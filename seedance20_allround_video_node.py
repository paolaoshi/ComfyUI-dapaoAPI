"""Independent Seedance 2.0 video node for the dapaoAI relay.

The node submits stable dapaoAI mapping IDs. Resolution remains a separate
request parameter and is not encoded into the model name.
"""

try:
    from .node_error_utils import format_node_error
except ImportError:
    from node_error_utils import format_node_error


import asyncio
import io
import json
import os
import re
import hashlib
import threading
from urllib.parse import quote
import sys
import tempfile
import time
import traceback
import wave

import numpy as np
import requests
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error
from .image_input_utils import IMAGE_429_HINT, tensor_to_png_bytes
from .dreambrush_runtime import ensure_asset_references, queue_job_metadata, submit_json_task

try:
    import comfy.model_management
    import comfy.utils
    from comfy.comfy_types import IO
except Exception:
    comfy = None

    class IO:
        VIDEO = "VIDEO"


API_BASE_URL = "https://api.dapaoai.com"
NODE_NAME = "DapaoSeedance20AllroundVideoNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
DISPLAY_NAME = "🐠Seedance2.0全能视频@炮老师的小课堂"
MODEL_ID = "doubao-seedance-2.0"
STANDARD_UPSTREAM_MODEL = "seedance-2.0"
FAST_UPSTREAM_MODEL = STANDARD_UPSTREAM_MODEL
MODEL_OPTIONS = [MODEL_ID, STANDARD_UPSTREAM_MODEL]
UPSTREAM_REFERENCE_MODEL = MODEL_ID
MODE_OPTIONS = ["自动识别", "文生视频", "图生视频", "首尾帧生视频", "多模态参考"]
DURATION_OPTIONS = [str(value) for value in range(4, 16)]
ASPECT_RATIO_OPTIONS = ["16:9", "9:16", "4:3", "3:4", "1:1", "21:9", "adaptive"]
RESOLUTION_OPTIONS = ["720P", "480P", "1080P"]
MAX_IMAGE_REFERENCES = 9
MAX_VIDEO_REFERENCES = 3
MAX_AUDIO_REFERENCES = 3
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 20 * 1024 * 1024
MAX_AUDIO_BYTES = 15 * 1024 * 1024
_REGISTRATION_LOCKS = [threading.Lock() for _ in range(32)]


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        printable = str(message).encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(printable)


def _log_info(message):
    _safe_print(f"[dapaoAPI-Seedance2.0全能视频] 信息：{message}")


def _log_error(message):
    _safe_print(f"[dapaoAPI-Seedance2.0全能视频] 错误：{message}")


def _parse_extra_json(value):
    try:
        data = json.loads((value or "{}").strip() or "{}")
    except json.JSONDecodeError as error:
        raise ValueError(f"额外参数JSON格式错误：{error}") from error
    if not isinstance(data, dict):
        raise ValueError("额外参数JSON必须是 JSON 对象。")
    return data


def _response_error(response):
    text = response.text[:1200]
    try:
        data = response.json()
    except Exception:
        return text

    def decode_nested(value):
        # dapaoAI wraps some upstream errors as a JSON string inside
        # ``error.message``. Decode a few layers so quota/model failures are
        # reported with their real upstream code instead of a generic 502.
        for _ in range(3):
            if not isinstance(value, str):
                break
            stripped = value.strip()
            if not stripped or stripped[0] not in "[{":
                break
            try:
                value = json.loads(stripped)
            except Exception:
                break
        return value

    def walk(value):
        value = decode_nested(value)
        if isinstance(value, dict):
            code = value.get("code") or value.get("error_code") or value.get("type")
            for key in ("message", "msg", "detail", "error"):
                if key in value:
                    nested = walk(value[key])
                    if nested:
                        return f"{code}: {nested}" if code and str(code) not in nested else nested
            if code:
                return str(code)
        elif isinstance(value, list):
            for item in value:
                nested = walk(item)
                if nested:
                    return nested
        elif value is not None and str(value).strip():
            return str(value).strip()
        return ""

    message = walk(data.get("error", data) if isinstance(data, dict) else data)
    return message or text


class DapaoSeedanceTaskError(RuntimeError):
    """Keep the failed read-only query available to the outer error report."""

    def __init__(self, task_id, result, message):
        self.result = result
        normalized = str(message).lower()
        hint = ""
        if "may contain real person" in normalized:
            hint = (
                "上游检测到输入图片可能包含真人，拒绝了本次生成。"
                "这不是素材登记失败；重新登记素材或增加真人模式开关不能解决该拒绝。"
                "请让妙笔维护者确认当前模型渠道是否支持这类真人素材；"
                "若图片并非真人，可提供任务ID请其核查误判。节点不会自动重试。\n"
            )
        elif "asset" in normalized and ("not found" in normalized or "does not exist" in normalized):
            hint = (
                "生成服务找不到引用的上游素材。请让妙笔维护者核对该任务的素材登记是否仍有效、"
                "素材登记与生成使用的渠道/上游凭据是否一致，以及file ID到上游asset ID的映射。"
                "这条错误不能说明是不支持真人，也不能靠切换真人模式解决。"
                "节点不会自动重新上传或重新提交视频。\n"
            )
        super().__init__(f"视频任务失败（任务ID：{task_id}）：{hint}{message}")


class DapaoSeedanceAPIError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = int(status_code)
        self.api_message = str(message)
        labels = {
            400: "请求参数或媒体素材错误",
            401: "认证失败，请检查 API 密钥",
            402: "余额不足，请充值后重试",
            403: "没有模型或接口权限",
            404: "接口或任务不存在",
            429: IMAGE_429_HINT,
            409: "素材尚未就绪或登记状态待核对，请保留原ID查询",
            410: "素材已过期，请重新准备源素材",
            500: "服务内部错误，请保留任务ID稍后查询",
            502: "上游响应异常，请保留任务ID稍后查询",
            503: "服务繁忙或队列不可用，请稍后查询原任务",
        }
        normalized = self.api_message.lower()
        if "insufficient_user_quota" in normalized or "insufficient quota" in normalized or "预扣费额度" in self.api_message:
            label = "上游余额不足"
            hint = "（请联系妙笔维护者核对渠道额度）"
        elif "did not provide a seconds billing multiplier" in normalized:
            label = "中转站按秒计费适配器配置错误"
            hint = "（服务端任务适配器未返回 seconds 计费倍率；节点已提交 seconds，需修复中转站适配器或计费配置）"
        elif "model name not specified" in self.api_message.lower() or "model name cannot be empty" in self.api_message.lower():
            label = "中转站模型映射为空"
            hint = "（节点已发送模型字段；请在 dapaoAI 的视频路由中检查该模型ID的目标模型是否为空或未绑定可用渠道）"
        else:
            label = labels.get(self.status_code, "中转站请求失败")
            hint = ""
        super().__init__(f"{label} {self.status_code}：{self.api_message}{hint}")


def _tensor_to_png_bytes(image_tensor):
    """Encode ComfyUI IMAGE batches to PNG bytes without creating data URIs."""
    return tensor_to_png_bytes(image_tensor)


def _audio_to_wav_bytes(audio_input):
    if not isinstance(audio_input, dict):
        raise ValueError("无法读取 AUDIO 输入。")
    waveform = audio_input.get("waveform")
    sample_rate = audio_input.get("sample_rate") or audio_input.get("sampler_rate") or 44100
    if waveform is None:
        raise ValueError("AUDIO 输入缺少 waveform。")
    if hasattr(waveform, "cpu"):
        waveform = waveform.cpu().numpy()
    waveform = np.squeeze(np.asarray(waveform))
    if waveform.ndim == 1:
        waveform = waveform.reshape(-1, 1)
    elif waveform.ndim == 2 and waveform.shape[0] < waveform.shape[1]:
        waveform = waveform.T
    if waveform.ndim != 2:
        raise ValueError("无法识别 AUDIO 输入的声道格式。")
    if np.issubdtype(waveform.dtype, np.floating):
        waveform = (np.clip(waveform, -1.0, 1.0) * 32767).astype(np.int16)
    else:
        waveform = waveform.astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(int(waveform.shape[1]))
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(waveform.tobytes())
    return buffer.getvalue()


def _video_to_bytes(video_input):
    if isinstance(video_input, str) and os.path.isfile(video_input):
        with open(video_input, "rb") as handle:
            return handle.read()
    if isinstance(video_input, dict):
        for key in ("file_path", "path", "filename"):
            path = video_input.get(key)
            if isinstance(path, str) and os.path.isfile(path):
                with open(path, "rb") as handle:
                    return handle.read()
    if not hasattr(video_input, "save_to"):
        raise ValueError("无法读取 VIDEO 输入，请使用可保存的 ComfyUI VIDEO。")
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    handle.close()
    try:
        saved = video_input.save_to(handle.name)
        if saved is False or not os.path.isfile(handle.name):
            raise ValueError("VIDEO 输入保存失败。")
        with open(handle.name, "rb") as file_handle:
            return file_handle.read()
    finally:
        try:
            os.remove(handle.name)
        except OSError:
            pass


def _validate_public_url(value, label):
    value = str(value or "").strip()
    if not value.startswith(("http://", "https://", "asset://")):
        raise ValueError(f"{label}必须是公网 HTTP/HTTPS URL 或 asset:// 素材引用，不能使用本地路径、localhost 或 data URI。")
    return value


def _extract_public_url(result):
    """Find an HTTP(S) URL in varied /v1/files response envelopes."""
    preferred = {"url", "uri", "file_url", "download_url", "public_url", "source_url", "href"}

    def walk(value, key=""):
        if isinstance(value, dict):
            # Prefer fields conventionally used for uploaded-file URLs.
            for child_key, child in value.items():
                if str(child_key).lower() in preferred and isinstance(child, str):
                    candidate = child.strip()
                    if candidate.startswith(("http://", "https://")):
                        return candidate
            for child_key, child in value.items():
                found = walk(child, str(child_key).lower())
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = walk(child, key)
                if found:
                    return found
        elif isinstance(value, str) and value.startswith(("http://", "https://")):
            return value.strip()
        return ""

    return walk(result)


def _response_layers(result):
    if not isinstance(result, dict):
        return []
    layers = []
    pending = [result]
    seen = set()
    while pending:
        layer = pending.pop(0)
        if not isinstance(layer, dict) or id(layer) in seen:
            continue
        seen.add(id(layer))
        layers.append(layer)
        for key in ("data", "result", "output", "task"):
            nested = layer.get(key)
            if isinstance(nested, dict):
                pending.append(nested)
            elif isinstance(nested, list):
                pending.extend(item for item in nested if isinstance(item, dict))
    return layers


def _task_id(result):
    # The persistent queue job only represents delivery of the paid POST.
    # Prefer the upstream video task id returned by that POST for status polling.
    for layer in _response_layers(result):
        value = layer.get("task_id") or layer.get("id")
        if isinstance(value, (str, int)) and str(value):
            return str(value)
    queue_id = queue_job_metadata(result).get("job_id")
    if queue_id:
        return str(queue_id)
    return ""


def _task_state(result):
    statuses = []
    progress = None
    message = ""
    # The envelope's message may say "success" while data.status is FAILURE.
    # Prefer the actual task's failure reason over transport-level messages.
    layers = sorted(_response_layers(result), key=lambda layer: layer.get("status") is None)
    for layer in layers:
        if layer.get("status") is not None:
            statuses.append(str(layer["status"]).strip().lower())
        if progress is None and layer.get("progress") is not None:
            try:
                progress = float(str(layer["progress"]).strip().rstrip("%"))
            except (TypeError, ValueError):
                pass
        if not message:
            for key in ("fail_reason", "error_message", "error", "message", "msg", "detail"):
                value = layer.get(key)
                if isinstance(value, str) and value.strip():
                    message = value.strip()
                    break
                if isinstance(value, dict):
                    nested = value.get("message") or value.get("error") or value.get("detail")
                    if nested:
                        message = str(nested)
                        break
    if any(status in {"failed", "failure", "error", "cancelled", "canceled", "rejected", "expired"} for status in statuses):
        return "failed", progress, message
    if any(status in {"completed", "complete", "succeeded", "success", "done"} for status in statuses):
        return "completed", progress, message
    if any(status in {"not_start", "submitted", "processing", "pending", "queued", "running", "in_progress"} for status in statuses):
        return "processing", progress, message
    return (statuses[0] if statuses else ""), progress, message


def _extract_video_url(result):
    seen = set()

    def walk(value, key=""):
        if isinstance(value, dict):
            for child_key, child in value.items():
                found = walk(child, str(child_key).lower())
                if found:
                    return found
        elif isinstance(value, list):
            for child in value:
                found = walk(child, key)
                if found:
                    return found
        elif isinstance(value, str) and value.startswith(("http://", "https://")):
            if key in {"video_url", "url", "result_url", "video"} and value not in seen:
                seen.add(value)
                return value
        return ""

    return walk(result)


def _sanitized_result(value):
    if isinstance(value, dict):
        return {
            key: (f"<Data已省略，共{len(item)}字符>" if str(key).lower() in {"data", "base64", "b64_json"} and isinstance(item, str) and len(item) > 200 else _sanitized_result(item))
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_sanitized_result(item) for item in value]
    if isinstance(value, str) and value.startswith("data:") and len(value) > 200:
        return f"<Data URI已省略，共{len(value)}字符>"
    return value


class DapaoVideoAdapter:
    """A lightweight VIDEO output accepted by common ComfyUI save nodes."""

    def __init__(self, video_url="", width=1280, height=720, *, api_key="", task_id=""):
        self.video_url = video_url or ""
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self._api_key = api_key
        self._task_id = task_id

    def get_dimensions(self):
        return self.width, self.height

    def save_to(self, output_path, format="auto", codec="auto", metadata=None, **kwargs):
        # ComfyUI 不同版本的保存节点可能额外传入 crf、fps、bitrate 等参数；
        # 远端视频已经编码完成，这些参数只需兼容接收，不应改变下载内容。
        if not self.video_url:
            return False
        if self._task_id:
            url = API_BASE_URL + "/v1/videos/" + quote(self._task_id, safe="") + "/content"
            response = requests.get(url, headers={"Authorization": "Bearer " + self._api_key}, stream=True, timeout=300, allow_redirects=False)
            if response.is_redirect:
                location = response.headers.get("Location", "")
                response.close()
                if not location.startswith("https://"):
                    raise RuntimeError("妙笔视频下载返回无效重定向，请查询原任务。")
                # Follow the signed download URL without the gateway key.
                response = requests.get(location, stream=True, timeout=300, allow_redirects=True)
        else:
            response = requests.get(self.video_url, stream=True, timeout=300, allow_redirects=True)
        response.raise_for_status()
        with response, open(output_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return True


class DapaoSeedanceRelayClient:
    def __init__(self, api_key, timeout, max_poll_seconds=1200):
        self.api_key = api_key
        self.timeout = timeout
        self.max_poll_seconds = int(max_poll_seconds)
        self.base_url = API_BASE_URL.rstrip("/")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/Seedance20Allround",
        }

    def _request_json(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = requests.request(method, url, headers=self._headers(), timeout=self.timeout, allow_redirects=False, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as error:
            if method.upper() == "POST":
                raise RuntimeError(f"{friendly_network_error(error, '提交视频任务')} 视频提交不会自动重试，以免重复扣费。") from error
            raise RuntimeError(friendly_network_error(error, '查询视频任务')) from error
        try:
            self.retry_after = max(10, min(600, int(response.headers.get("Retry-After", "10"))))
        except (TypeError, ValueError):
            self.retry_after = 10
        if response.status_code >= 300:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status(response.text))
            raise DapaoSeedanceAPIError(response.status_code, _response_error(response))
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站返回内容不是 JSON：{response.text[:500]}") from error

    def upload_file(self, content, filename, mime_type, model_name):
        """Resolve or upload one reusable gateway asset."""
        if not isinstance(content, (bytes, bytearray)) or not content:
            raise ValueError(f"{filename}内容为空，无法上传。")
        media_limit = {
            "image": (MAX_IMAGE_BYTES, "图片"),
            "video": (MAX_VIDEO_BYTES, "视频"),
            "audio": (MAX_AUDIO_BYTES, "音频"),
        }.get(str(mime_type).split("/", 1)[0])
        if media_limit and len(content) > media_limit[0]:
            raise ValueError(f"{media_limit[1]}素材超过上传上限 {media_limit[0] // 1024 // 1024}MB，请压缩后重试。")
        return ensure_asset_references(
            self.api_key, [(bytes(content), filename, mime_type)],
            base_url=self.base_url, timeout=self.timeout,
        )[0]

    def prepare_asset(self, reference, model_name):
        if not re.fullmatch(r"asset://file-[A-Za-z0-9_-]{1,59}", reference):
            raise ValueError("妙笔上传未返回有效的asset://file-...引用。")
        identifier = reference.removeprefix("asset://")
        digest = hashlib.sha256((self.base_url + self.api_key + model_name + identifier).encode()).digest()
        with _REGISTRATION_LOCKS[int.from_bytes(digest[:2], "big") % len(_REGISTRATION_LOCKS)]:
            try:
                state = self._request_json("POST", "/v1/seedance/assets", json={"model": model_name, "file_id": identifier})
            except Exception as error:
                raise RuntimeError(f"素材{identifier}登记未完成：{error}。请保留ID查询，不自动重复创建。") from error
            registration = state.get("registration_id")
            if state.get("status") != "ready" and not registration:
                raise RuntimeError(f"素材登记未返回登记ID，请保留素材{identifier}交妙笔核对，不自动重建。")
            deadline = time.monotonic() + 600
            while state.get("status") != "ready":
                if state.get("status") not in {"creating", "processing"}:
                    raise RuntimeError(f"素材{identifier}登记状态：{state.get('status')}，请查询原记录，不自动重建。")
                if time.monotonic() >= deadline:
                    raise RuntimeError(f"素材{identifier}登记等待超时，登记ID：{registration}，请继续查询原记录。")
                for _ in range(min(getattr(self, "retry_after", 10), max(1, int(deadline - time.monotonic())))):
                    if comfy is not None:
                        comfy.model_management.throw_exception_if_processing_interrupted()
                    time.sleep(1)
                try:
                    state = self._request_json("GET", f"/v1/seedance/assets/{identifier}?registration_id={quote(str(registration), safe='')}")
                except Exception as error:
                    raise RuntimeError(f"素材查询中断，素材ID：{identifier}，登记ID：{registration}。{error}") from error
            return {**state, "registration_id": registration or state.get("registration_id")}

    def submit(self, payload):
        return submit_json_task(
            api_key=self.api_key, base_url=self.base_url, endpoint="/v1/video/generations",
            payload=payload, timeout=self.timeout, user_agent="ComfyUI-dapaoAPI/Seedance20Allround",
            error_factory=DapaoSeedanceAPIError,
            interrupt_callback=(comfy.model_management.throw_exception_if_processing_interrupted if comfy is not None else None),
            max_poll_seconds=self.max_poll_seconds,
            recovery_salt=getattr(self, "recovery_salt", 0), reuse_succeeded=True,
        )

    def poll(self, task_id, max_seconds, interval):
        started = time.monotonic()
        progress_bar = comfy.utils.ProgressBar(100) if comfy is not None else None
        while time.monotonic() - started < max_seconds:
            if comfy is not None:
                comfy.model_management.throw_exception_if_processing_interrupted()
            result = self._request_json("GET", f"/v1/video/generations/{task_id}")
            status, progress, message = _task_state(result)
            if status == "completed":
                if progress_bar:
                    progress_bar.update_absolute(100)
                return result
            if status == "failed":
                raise DapaoSeedanceTaskError(task_id, result, message or "生成服务返回失败状态")
            if progress_bar:
                elapsed = time.monotonic() - started
                current = min(95, int(progress)) if progress is not None else min(95, int(elapsed / max_seconds * 95))
                progress_bar.update_absolute(current)
            time.sleep(interval)
        raise RuntimeError(f"视频任务 {task_id} 超过 {max_seconds} 秒仍未完成，请保留任务ID继续查询，不要重复提交。")


class DapaoSeedance20AllroundVideoNode:
    MODEL_ID = MODEL_ID
    STANDARD_UPSTREAM_MODEL = STANDARD_UPSTREAM_MODEL
    MODEL_OPTIONS = MODEL_OPTIONS
    MAX_IMAGE_REFERENCES = MAX_IMAGE_REFERENCES
    MAX_VIDEO_REFERENCES = MAX_VIDEO_REFERENCES
    MAX_AUDIO_REFERENCES = MAX_AUDIO_REFERENCES
    DURATION_OPTIONS = DURATION_OPTIONS
    VERSION_LABEL = "Seedance2.0"
    HAS_FACE_MODE = False
    INCLUDE_BILLING_SECONDS = True
    USE_ASSET_LIBRARY = True

    def _log_info(self, message):
        _safe_print(f"[dapaoAPI-{self.VERSION_LABEL}全能视频] 信息：{message}")

    def _log_error(self, message):
        _safe_print(f"[dapaoAPI-{self.VERSION_LABEL}全能视频] 错误：{message}")

    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "首尾帧模式的首图，将自动登记并作为first_frame提交。"}),
            "🏁 尾帧图": ("IMAGE", {"tooltip": "首尾帧模式的尾图，将自动登记并作为last_frame提交。"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1800, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 30, "max": 600, "step": 10}),
        }
        for index in range(1, cls.MAX_IMAGE_REFERENCES + 1):
            optional[f"🖼️ 参考图{index}"] = ("IMAGE", {"tooltip": f"多图参考，第{index}路，最多{cls.MAX_IMAGE_REFERENCES}张。"})
        for index in range(1, cls.MAX_VIDEO_REFERENCES + 1):
            optional[f"🎞️ 参考视频{index}"] = (IO.VIDEO, {"tooltip": "多模态参考视频。"})
        for index in range(1, cls.MAX_AUDIO_REFERENCES + 1):
            optional[f"🎵 参考音频{index}"] = ("AUDIO", {"tooltip": "多模态参考音频，不能单独使用。"})
        optional["🎞️ 保留参考视频音轨"] = ("BOOLEAN", {"default": False})
        required = {
                "🔑 API密钥": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "填入 dapaoAI API 密钥",
                        "tooltip": "密钥只用于请求 https://api.dapaoai.com，不会写入配置文件。",
                    },
                ),
                "🤖 模型": (cls.MODEL_OPTIONS, {"default": cls.MODEL_ID}),
                "🎛️ 生成模式": (MODE_OPTIONS, {"default": "自动识别"}),
                "📝 提示词": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "电影感镜头缓慢推进，主体动作自然，光影细腻，画面稳定且细节丰富",
                    },
                ),
                "🧩 分辨率": (
                    RESOLUTION_OPTIONS,
                    {"default": "720P", "tooltip": "标准版支持480P/720P/1080P；SP仅720P。"},
                ),
                "⏱️ 时长(秒)": (cls.DURATION_OPTIONS, {"default": "5"}),
                "📐 视频比例": (ASPECT_RATIO_OPTIONS, {"default": "16:9"}),
                "🔊 生成音频": ("BOOLEAN", {"default": True}),
                "🎲 随机种": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": "randomize",
                        "tooltip": "仅控制 ComfyUI 缓存，不发送给接口。",
                    },
                ),
        }
        return {
            "required": required,
            "optional": optional,
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "Seedance2.0 文生视频、多图参考、首尾参考、多模态参考；本地素材自动复用 asset://，并使用持久队列"

    @classmethod
    def _collect_image_parts(cls, kwargs, limit=None):
        limit = cls.MAX_IMAGE_REFERENCES if limit is None else limit
        image_parts = []
        for index in range(1, cls.MAX_IMAGE_REFERENCES + 1):
            image = kwargs.get(f"🖼️ 参考图{index}")
            if image is None:
                continue
            for content in _tensor_to_png_bytes(image):
                if len(image_parts) >= limit:
                    raise ValueError(f"参考图片超过{limit}张，请减少输入。")
                image_parts.append((content, f"seedance_reference_{index}_{len(image_parts) + 1}.png", "image/png"))
        return image_parts

    @classmethod
    def _collect_video_parts(cls, kwargs):
        parts = []
        for index in range(1, cls.MAX_VIDEO_REFERENCES + 1):
            video = kwargs.get(f"🎞️ 参考视频{index}")
            if video is not None:
                content = _video_to_bytes(video)
                if len(content) > MAX_VIDEO_BYTES:
                    raise ValueError(f"参考视频{index}超过本节点 {MAX_VIDEO_BYTES // 1024 // 1024}MB 的安全上限，请先压缩。")
                parts.append((content, f"seedance_reference_video_{index}.mp4", "video/mp4"))
        return parts

    @classmethod
    def _collect_audio_parts(cls, kwargs):
        parts = []
        for index in range(1, cls.MAX_AUDIO_REFERENCES + 1):
            audio = kwargs.get(f"🎵 参考音频{index}")
            if audio is not None:
                content = _audio_to_wav_bytes(audio)
                if len(content) > MAX_AUDIO_BYTES:
                    raise ValueError(f"参考音频{index}超过本节点 {MAX_AUDIO_BYTES // 1024 // 1024}MB 的安全上限，请先压缩。")
                parts.append((content, f"seedance_reference_audio_{index}.wav", "audio/wav"))
        return parts

    @classmethod
    def _frame_parts(cls, kwargs):
        first = kwargs.get("🎬 首帧图")
        last = kwargs.get("🏁 尾帧图")
        result = []
        if first is not None:
            result.extend((content, "seedance_first_frame.png", "image/png") for content in _tensor_to_png_bytes(first))
        if last is not None:
            result.extend((content, "seedance_last_frame.png", "image/png") for content in _tensor_to_png_bytes(last))
        return result

    @classmethod
    def _public_url_overrides(cls, value):
        data = _parse_extra_json(value)
        result = {}
        for key in ("images", "videos", "audios"):
            raw = data.get(key, [])
            if isinstance(raw, str):
                raw = [raw] if raw.strip() else []
            if not isinstance(raw, list):
                raise ValueError(f"公网素材URL JSON 的 {key} 必须是 URL 数组。")
            limit = {"images": cls.MAX_IMAGE_REFERENCES, "videos": cls.MAX_VIDEO_REFERENCES, "audios": cls.MAX_AUDIO_REFERENCES}[key]
            if len(raw) > limit:
                raise ValueError(f"公网素材URL.{key}最多 {limit} 个。")
            result[key] = [_validate_public_url(item, f"公网素材URL.{key}") for item in raw]
        return result

    @classmethod
    def _select_request_model(cls, model_id):
        """Return the exact dapaoAI mapping selected by the user."""
        if model_id not in cls.MODEL_OPTIONS:
            raise ValueError(f"未知界面模型：{model_id}")
        return model_id

    @staticmethod
    def _expected_dimensions(resolution_label, aspect_ratio):
        """Return the expected encoded dimensions for downstream VIDEO nodes."""
        sizes = {
            "480P": [(864, 496), (496, 864), (752, 560), (560, 752), (640, 640), (992, 432)],
            "720P": [(1280, 720), (720, 1280), (1112, 834), (834, 1112), (960, 960), (1470, 630)],
            "1080P": [(1920, 1080), (1080, 1920), (1664, 1248), (1248, 1664), (1440, 1440), (2206, 946)],
        }
        index = ASPECT_RATIO_OPTIONS.index(aspect_ratio) if aspect_ratio != "adaptive" else 0
        return sizes[resolution_label][index]

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_id = str(kwargs.get("🤖 模型") or "").strip()
        mode = kwargs.get("🎛️ 生成模式", "自动识别")
        prompt = (kwargs.get("📝 提示词") or "").strip()
        resolution_label = kwargs.get("🧩 分辨率", "720P")
        # Older saved workflows can deserialize a newly added combo widget as
        # an empty string. Resolve that state locally before validation.
        if not model_id:
            model_id = self.MODEL_ID
        duration = int(kwargs.get("⏱️ 时长(秒)", 5))
        aspect_ratio = kwargs.get("📐 视频比例", "16:9")
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1800))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        submitted = {}
        final = {}
        request_model = ""
        payload = {}
        stage = "validate"
        asset_records = []

        try:
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_id not in self.MODEL_OPTIONS:
                raise ValueError(f"未知界面模型：{model_id}")
            if mode not in MODE_OPTIONS:
                raise ValueError(f"不支持的生成模式：{mode}")
            if not prompt:
                raise ValueError("提示词不能为空。")
            allowed_resolutions = ["720P"] if model_id == "seedance-2.0" else RESOLUTION_OPTIONS
            if resolution_label not in allowed_resolutions:
                raise ValueError(f"{model_id}支持的分辨率：{'/'.join(allowed_resolutions)}。")
            request_model = self._select_request_model(model_id)
            if str(duration) not in self.DURATION_OPTIONS:
                raise ValueError(f"时长仅支持 {self.DURATION_OPTIONS[0]}–{self.DURATION_OPTIONS[-1]} 秒。")
            if aspect_ratio not in ASPECT_RATIO_OPTIONS:
                raise ValueError("视频比例无效，请从候选列表选择。")
            overrides = self._public_url_overrides(kwargs.get("🌐 公网素材URL(JSON)", "{}"))

            from .seedance_relay_media import prepare_inputs
            stage = "media_prepare"
            mode, media = prepare_inputs(self, kwargs, mode, overrides)
            metadata = {"resolution": resolution_label.lower(), "ratio": aspect_ratio}
            if model_id != "seedance-2.0":
                metadata["generate_audio"] = bool(kwargs.get("🔊 生成音频", True))
            if model_id == "doubao-seedance-2-5":
                bitrate = kwargs.get("🎚️ 码率模式", "standard")
                container = kwargs.get("📦 输出格式", "mp4")
                task_type = kwargs.get("🎞️ 参考任务", "auto")
                if bitrate not in {"standard", "high"} or container not in {"mp4", "mov"}:
                    raise ValueError("2.5码率或输出格式无效。")
                metadata.update(bitrate_mode=bitrate, output_format=container)
                if mode == "多模态参考":
                    if task_type not in {"auto", "reference", "edit", "extend"}:
                        raise ValueError("2.5参考任务类型无效。")
                    if task_type in {"edit", "extend"} and not any(m[0] == "video" for m in media):
                        raise ValueError("编辑/延长任务需要参考视频。")
                    metadata["omni_reference_task_type"] = task_type
            extra = _parse_extra_json(kwargs.get("📋 额外参数JSON", "{}"))
            if extra:
                raise ValueError("新妙笔协议请使用节点参数控件，额外参数JSON暂仅接受{}，避免旧协议字段误传。")
            client = DapaoSeedanceRelayClient(api_key, timeout, max_seconds)
            client.recovery_salt = kwargs.get("🎲 随机种", 0)
            use_asset_library = self.USE_ASSET_LIBRARY and request_model != "seedance-2.0"
            stage = "media_upload"
            image_uris, video_uris, audio_uris = [], [], []
            content = []
            for kind, source, role in media:
                if comfy is not None:
                    comfy.model_management.throw_exception_if_processing_interrupted()
                stage = "media_upload"
                reference = source if isinstance(source, str) else client.upload_file(*source, request_model)
                record = {"reference": reference, "model": request_model, "kind": kind, "role": role}
                asset_records.append(record)
                if not re.fullmatch(r"asset://file-[A-Za-z0-9_-]{1,59}", reference):
                    raise ValueError("请使用妙笔上传返回的asset://file-...引用，不能使用供应商素材ID。")
                if use_asset_library:
                    stage = "asset_registration"
                    registered = client.prepare_asset(reference, request_model)
                    record.update({key: registered.get(key) for key in ("registration_id", "status", "expires_at")})
                    if registered.get("kind") and registered["kind"] != kind:
                        raise ValueError(f"素材{reference}实际类型与{kind}输入不匹配，请检查连接。")
                {"image": image_uris, "video": video_uris, "audio": audio_uris}[kind].append(reference)
                content.append({"type": kind + "_url", kind + "_url": {"url": reference}, "role": role})
            if content:
                metadata["content"] = content
                if use_asset_library:
                    metadata["seedance_asset_library"] = True
            payload = {"model": request_model, "prompt": prompt, "seconds": str(duration), "metadata": metadata}

            self._log_info(
                f"提交任务：relay={API_BASE_URL}，model={model_id}，实际model={request_model}，"
                f"mode={mode}，duration={duration}，aspect_ratio={aspect_ratio}，"
                f"resolution={resolution_label.lower()}，billing_seconds={payload.get('seconds', '按次计费不发送')}，"
                f"audio={metadata.get('generate_audio', '由SP模型决定')}，图={len(image_uris)}，视频={len(video_uris)}，音频={len(audio_uris)}"
            )
            started = time.time()
            stage = "video_submit"
            submitted = client.submit(payload)
            task_identifier = _task_id(submitted)
            if not task_identifier or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", task_identifier) or submitted.get("object") == "relay.job":
                raise RuntimeError("未取得有效视频任务ID，请保留妙笔队列记录查询，不要重复提交。")
            # A succeeded _dapao_queue means the POST was delivered and its
            # upstream response was captured. It does not mean video rendering
            # has finished. Only a completed video task may skip polling.
            submitted_status, _, _ = _task_state(submitted)
            if submitted_status == "failed":
                raise DapaoSeedanceTaskError(task_identifier, submitted, _task_state(submitted)[2])
            stage = "video_poll"
            final = submitted if submitted_status == "completed" else client.poll(task_identifier, max_seconds, interval)
            video_url = _extract_video_url(final)
            if not video_url:
                video_url = API_BASE_URL + "/v1/videos/" + quote(task_identifier, safe="") + "/content"
            parameter_profile = f"{request_model}（{resolution_label}）"
            info = (
                f"✅ {self.VERSION_LABEL} 全能视频任务完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 模型ID：{model_id}\n"
                f"🔎 实际请求模型：{request_model}\n"
                f"🔎 参数档位：{parameter_profile}\n"
                f"🎛️ 模式：{mode}\n"
                f"⏱️ 时长：{duration} 秒\n"
                f"📐 比例：{aspect_ratio}\n"
                f"🧩 分辨率：{resolution_label}\n"
                f"🔊 生成音频：{metadata.get('generate_audio', '由SP模型决定')}\n"
                f"💰 价格：按妙笔实际结算（SP按秒；标准版按计费用量）\n"
                f"🖼️ 参考图：{len(image_uris)} 张\n"
                f"🎞️ 参考视频：{len(video_uris)} 个\n"
                f"🎵 参考音频：{len(audio_uris)} 个\n"
                f"🆔 任务ID：{task_identifier}\n"
                f"🔗 视频URL：{video_url}\n"
                f"⏱️ 耗时：{time.time() - started:.2f} 秒\n\n"
                + json.dumps({"submit": _sanitized_result(submitted), "final": _sanitized_result(final)}, ensure_ascii=False, indent=2)
            )
            width, height = self._expected_dimensions(resolution_label, aspect_ratio)
            return DapaoVideoAdapter(video_url, width, height, api_key=api_key, task_id=task_identifier), task_identifier, info, video_url
        except Exception as error:
            if isinstance(error, DapaoSeedanceTaskError):
                final = error.result
            message = format_node_error(f"❌ {self.VERSION_LABEL} 全能视频生成失败：{error}", context=__name__)
            if request_model:
                message += f"\n（节点实际发送 model={request_model}）"
            self._log_error(message)
            self._log_error(traceback.format_exc())
            details = json.dumps(
                {
                    "request_model": request_model,
                    "payload_model": payload.get("model") if isinstance(payload, dict) else "",
                    "stage": stage,
                    "assets": asset_records,
                    "submit": _sanitized_result(submitted),
                    "final": _sanitized_result(final),
                },
                ensure_ascii=False,
                indent=2,
            )
            raise RuntimeError(f"{message}\n\n{details}") from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoSeedance20AllroundVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoSeedance20AllroundVideoNode",
    "MODEL_ID",
    "STANDARD_UPSTREAM_MODEL",
    "FAST_UPSTREAM_MODEL",
    "UPSTREAM_REFERENCE_MODEL",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
