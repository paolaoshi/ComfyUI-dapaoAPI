"""Shared DreamBrush asset reuse, persistent queue and concurrency runtime.

The public nodes keep their existing ComfyUI contracts.  This module owns the
cross-node network policy so mapped prompts share asset uploads, submit with
stable idempotency keys and poll the gateway queue without request spikes.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import mimetypes
import os
import random
import sqlite3
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

import requests


DEFAULT_BASE_URL = "https://api.dapaoai.com"
_PROCESS_SESSION = uuid.uuid4().hex
_HASH_GATE = threading.BoundedSemaphore(4)
_IMAGE_UPLOAD_GATE = threading.BoundedSemaphore(4)
_LARGE_UPLOAD_GATE = threading.BoundedSemaphore(2)
_SUBMIT_GATE = threading.BoundedSemaphore(4)
_POLL_GATE = threading.BoundedSemaphore(8)
_STORE_LOCK = threading.RLock()
_INFLIGHT_LOCK = threading.Lock()
_ACTIVE_JOB_LOCK = threading.Lock()
_INFLIGHT_ASSETS: dict[tuple[str, str], "_InflightAsset"] = {}
_ACTIVE_JOB_KEYS: set[str] = set()

_POLL_DELAYS = (2.0, 3.0, 5.0, 8.0, 10.0)
_ASSET_EXPIRY_MARGIN = 60
_JOB_RECOVERY_SECONDS = 48 * 60 * 60


class DreamBrushRuntimeError(RuntimeError):
    pass


class DreamBrushHTTPError(DreamBrushRuntimeError):
    def __init__(self, status_code: int, message: str):
        self.status_code = int(status_code)
        self.api_message = str(message)
        super().__init__(f"DreamBrush 请求失败 {self.status_code}：{self.api_message}")


class DreamBrushIndeterminateError(DreamBrushRuntimeError):
    pass


@dataclass(frozen=True)
class AssetBlob:
    content: bytes
    filename: str
    mime_type: str

    @property
    def sha256(self) -> str:
        with _HASH_GATE:
            return hashlib.sha256(self.content).hexdigest()


@dataclass(frozen=True)
class AssetRecord:
    sha256: str
    asset_id: str
    reference: str
    expires_at: int
    byte_count: int
    mime_type: str


@dataclass
class _InflightAsset:
    event: threading.Event
    record: AssetRecord | None = None
    error: BaseException | None = None


def _runtime_db_path() -> Path:
    override = os.environ.get("DAPAO_DREAMBRUSH_RUNTIME_DB", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    try:
        import folder_paths  # type: ignore

        root = Path(folder_paths.get_user_directory()) / "dapaoAPI"
    except Exception:
        root = Path(tempfile.gettempdir()) / "ComfyUI-dapaoAPI"
    return root / "dreambrush_runtime.sqlite3"


class RuntimeStore:
    def __init__(self, path: Path | None = None):
        self.path = Path(path or _runtime_db_path())
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(str(self.path), timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA busy_timeout=15000")
        connection.execute("PRAGMA journal_mode=WAL")
        return connection

    def _initialize(self) -> None:
        with _STORE_LOCK, closing(self._connect()) as connection, connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS assets (
                    scope TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    asset_id TEXT NOT NULL,
                    reference TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    byte_count INTEGER NOT NULL,
                    mime_type TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (scope, sha256)
                );
                CREATE TABLE IF NOT EXISTS jobs (
                    idempotency_key TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    request_hash TEXT NOT NULL,
                    job_id TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    error TEXT NOT NULL DEFAULT ''
                );
                CREATE INDEX IF NOT EXISTS jobs_recovery_idx
                    ON jobs(scope, endpoint, request_hash, updated_at);
                """
            )

    def asset(self, scope: str, sha256: str, now: int | None = None) -> AssetRecord | None:
        now = int(now or time.time())
        with _STORE_LOCK, closing(self._connect()) as connection, connection:
            row = connection.execute(
                "SELECT * FROM assets WHERE scope=? AND sha256=? AND expires_at>?",
                (scope, sha256, now + _ASSET_EXPIRY_MARGIN),
            ).fetchone()
        if row is None:
            return None
        return AssetRecord(
            sha256=row["sha256"], asset_id=row["asset_id"], reference=row["reference"],
            expires_at=int(row["expires_at"]), byte_count=int(row["byte_count"]),
            mime_type=row["mime_type"],
        )

    def save_asset(self, scope: str, record: AssetRecord) -> None:
        with _STORE_LOCK, closing(self._connect()) as connection, connection:
            connection.execute(
                """INSERT INTO assets
                   (scope, sha256, asset_id, reference, expires_at, byte_count, mime_type, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(scope, sha256) DO UPDATE SET
                     asset_id=excluded.asset_id, reference=excluded.reference,
                     expires_at=excluded.expires_at, byte_count=excluded.byte_count,
                     mime_type=excluded.mime_type, updated_at=excluded.updated_at""",
                (scope, record.sha256, record.asset_id, record.reference, record.expires_at,
                 record.byte_count, record.mime_type, time.time()),
            )

    def claim_job(self, scope: str, endpoint: str, request_hash: str) -> sqlite3.Row:
        cutoff = time.time() - _JOB_RECOVERY_SECONDS
        with _STORE_LOCK, closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """SELECT * FROM jobs
                   WHERE scope=? AND endpoint=? AND request_hash=? AND updated_at>?
                     AND status IN ('submitting','queued','running','indeterminate')
                   ORDER BY updated_at DESC""",
                (scope, endpoint, request_hash, cutoff),
            ).fetchall()
            for row in rows:
                with _ACTIVE_JOB_LOCK:
                    if row["idempotency_key"] in _ACTIVE_JOB_KEYS:
                        continue
                    _ACTIVE_JOB_KEYS.add(row["idempotency_key"])
                return row
            key = f"dapao-{uuid.uuid4()}"
            now = time.time()
            connection.execute(
                """INSERT INTO jobs
                   (idempotency_key, scope, endpoint, request_hash, status, session_id, created_at, updated_at)
                   VALUES (?, ?, ?, ?, 'submitting', ?, ?, ?)""",
                (key, scope, endpoint, request_hash, _PROCESS_SESSION, now, now),
            )
            with _ACTIVE_JOB_LOCK:
                _ACTIVE_JOB_KEYS.add(key)
            return connection.execute("SELECT * FROM jobs WHERE idempotency_key=?", (key,)).fetchone()

    def update_job(self, key: str, *, status: str, job_id: str | None = None, error: str = "") -> None:
        with _STORE_LOCK, closing(self._connect()) as connection, connection:
            if job_id is None:
                connection.execute(
                    "UPDATE jobs SET status=?, updated_at=?, error=? WHERE idempotency_key=?",
                    (status, time.time(), error[:1000], key),
                )
            else:
                connection.execute(
                    "UPDATE jobs SET status=?, job_id=?, updated_at=?, error=? WHERE idempotency_key=?",
                    (status, job_id, time.time(), error[:1000], key),
                )

    @staticmethod
    def release_job(key: str) -> None:
        with _ACTIVE_JOB_LOCK:
            _ACTIVE_JOB_KEYS.discard(key)


_STORE: RuntimeStore | None = None


def runtime_store() -> RuntimeStore:
    global _STORE
    with _STORE_LOCK:
        path = _runtime_db_path()
        if _STORE is None or _STORE.path != path:
            _STORE = RuntimeStore(path)
        return _STORE


def account_scope(base_url: str, api_key: str) -> str:
    return hashlib.sha256(f"{base_url.rstrip('/')}\0{api_key}".encode("utf-8")).hexdigest()


def _response_message(response: requests.Response) -> str:
    text = str(getattr(response, "text", ""))[:1200]
    try:
        data = response.json()
    except Exception:
        return text or "中转站没有返回错误详情"
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            return str(error.get("message") or error.get("type") or error.get("code") or text)
        return str(data.get("message") or data.get("msg") or error or text)
    return text or str(data)[:1200]


def _friendly_asset_error(status: int, message: str, kind: str = "") -> str:
    labels = {
        400: "素材参数或格式不符合要求",
        401: "API 密钥无效，请检查认证信息",
        403: "当前 API 账号没有该素材的访问权限",
        413: "素材文件过大，请压缩、转码或减少素材",
        429: "素材上传或查询请求过多，已按中转站要求退避后仍未成功",
        500: "素材服务内部暂时异常",
        502: "素材服务连接上游存储失败",
        503: "素材服务繁忙或正在维护",
    }
    text = f"{labels.get(int(status), '素材接口请求失败')} {status}：{message}"
    if int(status) == 429 and kind == "image":
        text += "。请检查每张图片最长边是否超过 2048px（2K）；多图和批次输入也必须逐张控制在 2K 以内。"
    return text


def _retry_delay(response: requests.Response | None, attempt: int) -> float:
    if response is not None:
        raw = response.headers.get("Retry-After", "")
        try:
            return min(30.0, max(0.2, float(raw)))
        except (TypeError, ValueError):
            pass
    return min(10.0, (2 ** attempt) + random.uniform(0.1, 0.8))


def _request_with_retry(
    method: str,
    url: str,
    *,
    attempts: int = 3,
    gate: threading.BoundedSemaphore | None = None,
    **kwargs,
) -> requests.Response:
    last_error: BaseException | None = None
    for attempt in range(attempts):
        response = None
        try:
            if gate is None:
                response = requests.request(method, url, **kwargs)
            else:
                with gate:
                    response = requests.request(method, url, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as error:
            last_error = error
            if attempt + 1 >= attempts:
                raise
            time.sleep(_retry_delay(None, attempt))
            continue
        if response.status_code == 429 or response.status_code >= 500:
            if attempt + 1 < attempts:
                time.sleep(_retry_delay(response, attempt))
                continue
        return response
    if last_error:
        raise last_error
    raise DreamBrushRuntimeError("DreamBrush 请求重试结束但没有响应。")


class AssetClient:
    def __init__(self, api_key: str, base_url: str = DEFAULT_BASE_URL, timeout: int = 300):
        self.api_key = str(api_key)
        self.base_url = str(base_url).rstrip("/")
        self.timeout = int(timeout)
        self.scope = account_scope(self.base_url, self.api_key)
        self.store = runtime_store()

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "User-Agent": "ComfyUI-dapaoAPI/AssetClient"}

    def _resolve(self, hashes: list[str]) -> dict[str, AssetRecord]:
        if not hashes:
            return {}
        response = _request_with_retry(
            "POST", f"{self.base_url}/v1/assets/resolve", headers={**self.headers, "Content-Type": "application/json"},
            json={"hashes": hashes}, timeout=self.timeout, attempts=3, gate=_POLL_GATE,
        )
        if response.status_code >= 400:
            raise DreamBrushHTTPError(
                response.status_code,
                _friendly_asset_error(response.status_code, _response_message(response)),
            )
        try:
            payload = response.json()
        except Exception as error:
            raise DreamBrushRuntimeError("素材 resolve 返回内容不是 JSON。") from error
        records: dict[str, AssetRecord] = {}
        for item in payload.get("data", []) if isinstance(payload, dict) else []:
            if not isinstance(item, dict):
                continue
            record = self._record(item)
            records[record.sha256] = record
            self.store.save_asset(self.scope, record)
        return records

    @staticmethod
    def _validate_size(blob: AssetBlob) -> None:
        kind = blob.mime_type.split("/", 1)[0].lower()
        limit = {"image": 10, "audio": 50, "video": 60}.get(kind)
        if limit and len(blob.content) > limit * 1024 * 1024:
            raise ValueError(f"{kind}素材 {blob.filename} 为 {len(blob.content)/1024/1024:.1f}MB，超过 {limit}MB 限制。")

    def _upload(self, blob: AssetBlob, expected_hash: str) -> AssetRecord:
        self._validate_size(blob)
        gate = _IMAGE_UPLOAD_GATE if blob.mime_type.lower().startswith("image/") else _LARGE_UPLOAD_GATE
        response = _request_with_retry(
            "POST", f"{self.base_url}/v1/assets/uploads", headers=self.headers,
            files={"file": (blob.filename, blob.content, blob.mime_type)}, data={"purpose": "model-input"},
            timeout=max(self.timeout, 120), attempts=3, gate=gate,
        )
        if response.status_code >= 400:
            kind = blob.mime_type.split("/", 1)[0].lower()
            raise DreamBrushHTTPError(
                response.status_code,
                _friendly_asset_error(response.status_code, _response_message(response), kind),
            )
        try:
            item = response.json()
        except Exception as error:
            raise DreamBrushRuntimeError("素材上传返回内容不是 JSON。") from error
        record = self._record(item, fallback_hash=expected_hash, blob=blob)
        if record.sha256 != expected_hash:
            raise DreamBrushRuntimeError("中转站返回的素材 SHA-256 与实际上传字节不一致。")
        self.store.save_asset(self.scope, record)
        return record

    @staticmethod
    def _record(item: dict, fallback_hash: str = "", blob: AssetBlob | None = None) -> AssetRecord:
        asset_id = str(item.get("id") or item.get("asset_id") or "").strip()
        reference = str(item.get("reference") or (f"asset://{asset_id}" if asset_id else "")).strip()
        sha256 = str(item.get("sha256") or fallback_hash).strip().lower()
        expires_at = int(item.get("expires_at") or 0)
        if not asset_id or not reference.startswith("asset://") or len(sha256) != 64 or expires_at <= int(time.time()):
            raise DreamBrushRuntimeError("中转站返回的素材记录缺少 id/reference/sha256/expires_at。")
        return AssetRecord(
            sha256=sha256, asset_id=asset_id, reference=reference, expires_at=expires_at,
            byte_count=int(item.get("bytes") or (len(blob.content) if blob else 0)),
            mime_type=str(item.get("mime_type") or (blob.mime_type if blob else "application/octet-stream")),
        )

    def ensure(self, blobs: Iterable[AssetBlob]) -> list[AssetRecord]:
        ordered = list(blobs)
        hashes = [blob.sha256 for blob in ordered]
        unique: dict[str, AssetBlob] = {}
        for digest, blob in zip(hashes, ordered):
            unique.setdefault(digest, blob)
        results: dict[str, AssetRecord] = {}
        owners: dict[str, _InflightAsset] = {}
        waiters: dict[str, _InflightAsset] = {}

        for digest in unique:
            cached = self.store.asset(self.scope, digest)
            if cached:
                results[digest] = cached
                continue
            key = (self.scope, digest)
            with _INFLIGHT_LOCK:
                state = _INFLIGHT_ASSETS.get(key)
                if state is None:
                    state = _InflightAsset(threading.Event())
                    _INFLIGHT_ASSETS[key] = state
                    owners[digest] = state
                else:
                    waiters[digest] = state

        try:
            if owners:
                resolved: dict[str, AssetRecord] = {}
                owner_hashes = list(owners)
                for start in range(0, len(owner_hashes), 100):
                    resolved.update(self._resolve(owner_hashes[start:start + 100]))
                results.update(resolved)
                missing = [digest for digest in owner_hashes if digest not in resolved]
                uploaded: dict[str, AssetRecord] = {}
                if missing:
                    with ThreadPoolExecutor(max_workers=min(4, len(missing)), thread_name_prefix="dapao-assets") as executor:
                        futures = {executor.submit(self._upload, unique[digest], digest): digest for digest in missing}
                        for future in as_completed(futures):
                            uploaded[futures[future]] = future.result()
                    results.update(uploaded)
                for digest, state in owners.items():
                    state.record = results[digest]
                    state.event.set()
            for digest, state in waiters.items():
                state.event.wait(timeout=max(self.timeout, 300))
                if state.error:
                    raise state.error
                if state.record is None:
                    raise DreamBrushRuntimeError("等待并发素材上传超时。")
                results[digest] = state.record
            return [results[digest] for digest in hashes]
        except BaseException as error:
            for state in owners.values():
                state.error = error
                state.event.set()
            raise
        finally:
            with _INFLIGHT_LOCK:
                for digest in owners:
                    _INFLIGHT_ASSETS.pop((self.scope, digest), None)


_DATA_URI_PREFIX = "data:"


def _decode_data_uri(value: str, index: int) -> AssetBlob | None:
    if not value.startswith(_DATA_URI_PREFIX) or ";base64," not in value:
        return None
    header, encoded = value.split(",", 1)
    mime_type = header[5:].split(";", 1)[0].strip().lower()
    if not mime_type.startswith(("image/", "audio/", "video/")):
        return None
    try:
        content = base64.b64decode(encoded, validate=True)
    except Exception as error:
        raise ValueError("请求素材中的 Data URI Base64 无法解码。") from error
    extension = mimetypes.guess_extension(mime_type) or ".bin"
    return AssetBlob(content, f"payload_asset_{index}{extension}", mime_type)


def externalize_payload_assets(payload: dict, api_key: str, base_url: str, timeout: int) -> dict:
    """Replace embedded media with reusable asset:// references.

    OpenAI-style data URI fields are replaced in-place.  Gemini inlineData
    parts are converted to the standard fileData/fileUri representation.
    """
    prepared = copy.deepcopy(payload)
    blobs: list[AssetBlob] = []

    def collect(value: Any) -> None:
        if isinstance(value, str):
            blob = _decode_data_uri(value, len(blobs) + 1)
            if blob:
                blobs.append(blob)
            return
        if isinstance(value, dict):
            inline = value.get("inlineData") or value.get("inline_data")
            if isinstance(inline, dict) and isinstance(inline.get("data"), str):
                mime = str(inline.get("mimeType") or inline.get("mime_type") or "image/png")
                try:
                    content = base64.b64decode(inline["data"], validate=True)
                except Exception as error:
                    raise ValueError("Gemini inlineData Base64 无法解码。") from error
                extension = mimetypes.guess_extension(mime) or ".bin"
                blobs.append(AssetBlob(content, f"gemini_asset_{len(blobs)+1}{extension}", mime))
                return
            input_audio = value.get("input_audio")
            if isinstance(input_audio, dict) and isinstance(input_audio.get("data"), str):
                encoded = input_audio["data"]
                if not encoded.startswith(("asset://", "data:")):
                    audio_format = str(input_audio.get("format") or "wav").lower().lstrip(".")
                    mime = {"wav": "audio/wav", "mp3": "audio/mpeg", "m4a": "audio/mp4"}.get(
                        audio_format, f"audio/{audio_format}"
                    )
                    try:
                        content = base64.b64decode(encoded, validate=True)
                    except Exception as error:
                        raise ValueError("input_audio Base64 无法解码。") from error
                    blobs.append(AssetBlob(content, f"input_audio_{len(blobs)+1}.{audio_format}", mime))
                    return
            for item in value.values():
                collect(item)
            return
        if isinstance(value, list):
            for item in value:
                collect(item)

    collect(prepared)
    if not blobs:
        return prepared
    records = AssetClient(api_key, base_url, timeout).ensure(blobs)
    iterator = iter(records)

    def rewrite(value: Any) -> Any:
        if isinstance(value, str):
            if _decode_data_uri(value, 0):
                return next(iterator).reference
            return value
        if isinstance(value, dict):
            inline_key = "inlineData" if "inlineData" in value else "inline_data" if "inline_data" in value else ""
            inline = value.get(inline_key) if inline_key else None
            if isinstance(inline, dict) and isinstance(inline.get("data"), str):
                record = next(iterator)
                result = {key: rewrite(item) for key, item in value.items() if key != inline_key}
                result["fileData"] = {
                    "mimeType": str(inline.get("mimeType") or inline.get("mime_type") or "application/octet-stream"),
                    "fileUri": record.reference,
                }
                return result
            input_audio = value.get("input_audio")
            if isinstance(input_audio, dict) and isinstance(input_audio.get("data"), str):
                encoded = input_audio["data"]
                if not encoded.startswith(("asset://", "data:")):
                    result = {key: rewrite(item) for key, item in value.items() if key != "input_audio"}
                    result["input_audio"] = dict(input_audio)
                    result["input_audio"]["data"] = next(iterator).reference
                    return result
            return {key: rewrite(item) for key, item in value.items()}
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        return value

    return rewrite(prepared)


def ensure_asset_references(
    api_key: str,
    blobs: Iterable[tuple[bytes, str, str] | AssetBlob],
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 300,
) -> list[str]:
    normalized = [item if isinstance(item, AssetBlob) else AssetBlob(item[0], item[1], item[2]) for item in blobs]
    return [record.reference for record in AssetClient(api_key, base_url, timeout).ensure(normalized)]


def _canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _json_response(response: requests.Response, label: str) -> dict:
    try:
        result = response.json()
    except Exception as error:
        raise DreamBrushRuntimeError(f"{label}返回内容不是 JSON：{str(getattr(response, 'text', ''))[:500]}") from error
    if not isinstance(result, dict):
        raise DreamBrushRuntimeError(f"{label}返回的 JSON 不是对象。")
    return result


def _job_layer(payload: dict) -> dict:
    current = payload
    for _ in range(3):
        if not isinstance(current, dict):
            break
        if current.get("status") or current.get("id") or current.get("job_id"):
            return current
        nested = current.get("data") or current.get("result")
        if not isinstance(nested, dict):
            break
        current = nested
    return payload


def queue_job_metadata(payload: dict) -> dict:
    value = payload.get("_dapao_queue") if isinstance(payload, dict) else None
    return value if isinstance(value, dict) else {}


def submit_json_task(
    *,
    api_key: str,
    endpoint: str,
    payload: dict,
    timeout: int,
    base_url: str = DEFAULT_BASE_URL,
    user_agent: str = "ComfyUI-dapaoAPI",
    error_factory: Callable[[int, str], BaseException] | None = None,
    interrupt_callback: Callable[[], None] | None = None,
    status_callback: Callable[[str, dict], None] | None = None,
    max_poll_seconds: int | None = None,
) -> dict:
    """Submit one paid JSON request through DreamBrush's persistent queue.

    Gateways that have not enabled ``respond-async`` may return HTTP 200; that
    synchronous response remains supported without a second paid submission.
    """
    base_url = base_url.rstrip("/")
    transformed = externalize_payload_assets(payload, api_key, base_url, timeout)
    # ``Prefer: respond-async`` is the single queue contract.  Do not pass a
    # legacy body-level async switch to the worker, otherwise some old model
    # adapters would enqueue a second upstream task instead of returning the
    # final model response to the persistent queue.
    transformed.pop("async", None)
    scope = account_scope(base_url, api_key)
    request_hash = _canonical_hash(transformed)
    store = runtime_store()
    row = store.claim_job(scope, endpoint, request_hash)
    key = str(row["idempotency_key"])
    job_id = str(row["job_id"] or "")
    existing_status = str(row["status"])
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Prefer": "respond-async",
        "Idempotency-Key": key,
        "User-Agent": user_agent,
    }
    deadline = time.monotonic() + int(max_poll_seconds or max(timeout, 1200))
    poll_attempt = 0
    last_reported_state = ""

    def raise_http(response: requests.Response) -> None:
        message = _response_message(response)
        if error_factory:
            raise error_factory(response.status_code, message)
        raise DreamBrushHTTPError(response.status_code, message)

    try:
        if existing_status == "indeterminate":
            raise DreamBrushIndeterminateError(
                "该逻辑任务此前进入 indeterminate 状态，禁止自动重新提交，以免重复生成或重复扣费。"
            )
        if not job_id:
            try:
                response = _request_with_retry(
                    "POST", f"{base_url}/{endpoint.lstrip('/')}", headers=headers, json=transformed,
                    # A paid submit is never retried in-process. If its response is
                    # lost, the outbox keeps this key for a later explicit recovery.
                    timeout=timeout, attempts=1, gate=_SUBMIT_GATE,
                )
            except (requests.ConnectionError, requests.Timeout) as error:
                store.update_job(key, status="submitting", error=str(error))
                raise DreamBrushRuntimeError(
                    "付费任务提交回包中断；已保存原幂等键，下次执行会复用同一键恢复，不会生成新键。"
                ) from error
            if response.status_code >= 400:
                store.update_job(key, status="failed", error=f"HTTP {response.status_code}")
                raise_http(response)
            submitted = _json_response(response, "任务提交")
            if response.status_code != 202:
                store.update_job(key, status="succeeded")
                submitted.setdefault("_dapao_queue", {"mode": "synchronous"})
                return submitted
            layer = _job_layer(submitted)
            job_id = str(layer.get("id") or layer.get("job_id") or "").strip()
            if not job_id:
                store.update_job(key, status="indeterminate", error="HTTP 202 missing job id")
                raise DreamBrushIndeterminateError("中转站返回 HTTP 202 但没有 Job ID，已停止自动操作。")
            state = str(layer.get("status") or "queued").lower()
            store.update_job(key, status=state, job_id=job_id)
        while time.monotonic() < deadline:
            if interrupt_callback:
                try:
                    interrupt_callback()
                except BaseException:
                    try:
                        with _POLL_GATE:
                            status_response = requests.get(
                                f"{base_url}/v1/queue/jobs/{job_id}", headers={"Authorization": f"Bearer {api_key}"},
                                timeout=min(timeout, 30),
                            )
                        status_payload = status_response.json() if status_response.status_code < 400 else {}
                        state = str(_job_layer(status_payload).get("status") or "").lower()
                        if state == "queued":
                            requests.delete(
                                f"{base_url}/v1/queue/jobs/{job_id}", headers={"Authorization": f"Bearer {api_key}"},
                                timeout=min(timeout, 30),
                            )
                            store.update_job(key, status="canceled", job_id=job_id)
                    finally:
                        raise
            status_response = _request_with_retry(
                "GET", f"{base_url}/v1/queue/jobs/{job_id}",
                headers={"Authorization": f"Bearer {api_key}", "User-Agent": user_agent},
                timeout=min(timeout, 60), attempts=3, gate=_POLL_GATE,
            )
            if status_response.status_code >= 400:
                raise_http(status_response)
            status_payload = _json_response(status_response, "队列状态查询")
            layer = _job_layer(status_payload)
            state = str(layer.get("status") or "").lower()
            if state and state != last_reported_state:
                print(f"[dapaoAPI持久队列] Job {job_id}：{state}")
                last_reported_state = state
            if status_callback:
                status_callback(state, layer)
            if state in {"queued", "running"}:
                store.update_job(key, status=state, job_id=job_id)
                delay_index = min(poll_attempt, len(_POLL_DELAYS) - 1)
                base_delay = _POLL_DELAYS[delay_index]
                if state == "running" and delay_index == 0:
                    base_delay = 3.0
                poll_attempt += 1
                time.sleep(base_delay + random.uniform(0.0, min(2.5, base_delay * 0.3)))
                continue
            if state == "succeeded":
                result_response = _request_with_retry(
                    "GET", f"{base_url}/v1/queue/jobs/{job_id}/result",
                    headers={"Authorization": f"Bearer {api_key}", "User-Agent": user_agent},
                    timeout=timeout, attempts=3, gate=_POLL_GATE,
                )
                if result_response.status_code >= 400:
                    raise_http(result_response)
                result = _json_response(result_response, "队列任务结果")
                result.setdefault("_dapao_queue", {"mode": "persistent", "job_id": job_id, "status": state})
                store.update_job(key, status="succeeded", job_id=job_id)
                return result
            if state in {"failed", "canceled", "expired", "indeterminate"}:
                message = str(layer.get("error") or layer.get("message") or json.dumps(layer, ensure_ascii=False)[:1000])
                # Failed queue jobs may keep the real upstream response only on
                # the result endpoint. This is a read-only diagnostic request;
                # it never resubmits the paid generation.
                if state == "failed":
                    try:
                        failed_result_response = _request_with_retry(
                            "GET", f"{base_url}/v1/queue/jobs/{job_id}/result",
                            headers={"Authorization": f"Bearer {api_key}", "User-Agent": user_agent},
                            timeout=min(timeout, 60), attempts=3, gate=_POLL_GATE,
                        )
                        if failed_result_response.status_code < 400:
                            failed_result = _json_response(failed_result_response, "失败任务详情")
                            failed_detail = str(
                                failed_result.get("error")
                                or failed_result.get("message")
                                or failed_result.get("msg")
                                or json.dumps(failed_result, ensure_ascii=False)[:1600]
                            )
                        else:
                            failed_detail = _response_message(failed_result_response)
                        if failed_detail and failed_detail not in message:
                            message = f"{message}；上游详情：{failed_detail}"
                    except Exception:
                        # Preserve the original terminal error when an older
                        # gateway does not expose failed results.
                        pass
                store.update_job(key, status=state, job_id=job_id, error=state)
                if state == "indeterminate":
                    raise DreamBrushIndeterminateError(f"任务 {job_id} 状态无法确认：{message}；禁止自动重提。")
                raise DreamBrushRuntimeError(f"任务 {job_id} 已{state}：{message}")
            raise DreamBrushRuntimeError(f"任务 {job_id} 返回未知状态：{state or '空'}")
        store.update_job(key, status="running", job_id=job_id, error="local poll timeout")
        raise DreamBrushRuntimeError(f"任务 {job_id} 超过本地等待时间；Job ID 已保存，下次执行将恢复查询。")
    finally:
        store.release_job(key)


__all__ = [
    "AssetBlob", "AssetClient", "AssetRecord", "DreamBrushHTTPError",
    "DreamBrushIndeterminateError", "DreamBrushRuntimeError", "RuntimeStore",
    "account_scope", "ensure_asset_references", "externalize_payload_assets",
    "queue_job_metadata", "runtime_store", "submit_json_task",
]
