"""Shared Skill, conversation and context runtime for dapaoAI API chat."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import os
import re
import shutil
import tempfile
import threading
import wave
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from pathlib import PurePosixPath

from PIL import Image

from .image_input_utils import (
    MAX_INPUT_IMAGE_EDGE,
    resize_pil_for_input,
    tensor_to_png_data_uris,
)


STATE_TAG = re.compile(
    r"<dapao_local_skill_state>\s*(\{.*?\})\s*</dapao_local_skill_state>",
    re.S,
)
_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_STANDARD_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
_CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
_TEXT_EXTENSIONS = {".md", ".txt", ".yaml", ".yml", ".json"}
_MATERIAL_TOKEN_RE = re.compile(r"@(图片(?:20|1\d|[1-9])|视频[1-5]|音频[1-5])(?!\d)")
_MATERIAL_LIKE_RE = re.compile(r"@(图片|视频|音频)(\d+)")
PLUGIN_ROOT = Path(__file__).resolve().parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"
SKILL_ALIAS_PATH = PLUGIN_ROOT / "data" / "skill_display_names.json"
MAX_SKILL_UPLOAD_BYTES = 512 * 1024 * 1024
MAX_SKILL_ARCHIVE_BYTES = 128 * 1024 * 1024
MAX_SKILL_FILES = 5000
_ALIAS_LOCK = threading.Lock()
_INSTALL_LOCK = threading.Lock()
_IGNORED_PACKAGE_PARTS = {".git", "__MACOSX", "__pycache__", "node_modules"}


def _skill_roots() -> tuple[Path, ...]:
    """Prefer API-owned Skills and fall back to the sibling local plugin."""
    candidates = (
        SKILLS_ROOT,
        PLUGIN_ROOT.parent / "ComfyUI-llama_Dapao" / "skills",
    )
    unique: list[Path] = []
    for path in candidates:
        resolved = path.resolve()
        if resolved not in unique and resolved.is_dir():
            unique.append(resolved)
    SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
    if SKILLS_ROOT.resolve() not in unique:
        unique.insert(0, SKILLS_ROOT.resolve())
    return tuple(unique)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    values: dict[str, str] = {}
    lines = text[3:end].splitlines()
    index = 0
    while index < len(lines):
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*?)\s*$", lines[index])
        if not match:
            index += 1
            continue
        key, value = match.groups()
        if value in ("|", ">"):
            index += 1
            parts = []
            while index < len(lines) and (not lines[index].strip() or lines[index][:1].isspace()):
                parts.append(lines[index].strip())
                index += 1
            values[key] = " ".join(part for part in parts if part)
            continue
        values[key] = value.strip("\"'")
        index += 1
    return values


def _meta(skill_dir: Path, key: str) -> str:
    path = skill_dir / "meta.yaml"
    if not path.is_file():
        return ""
    for line in _read_text(path).splitlines():
        match = re.match(rf"^{re.escape(key)}:\s*(.*?)\s*$", line)
        if match:
            return match.group(1).strip("\"'")
    return ""


def _heading(text: str, chinese_only: bool = False) -> str:
    """Return only the document's first real H1, ignoring fenced code."""
    fenced = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = re.match(r"^\s*#\s+(.+?)\s*$", line)
        if not match:
            continue
        value = re.sub(r"[`*_]", "", match.group(1)).strip()
        if not value:
            return ""
        return value if not chinese_only or _CHINESE_RE.search(value) else ""
    return ""


def _agent_display_name(skill_dir: Path) -> str:
    path = skill_dir / "agents" / "openai.yaml"
    if not path.is_file():
        return ""
    in_interface = False
    for line in _read_text(path).splitlines():
        if re.match(r"^interface:\s*$", line):
            in_interface = True
            continue
        if in_interface and line and not line[:1].isspace():
            break
        if in_interface:
            match = re.match(r"^\s+display_name:\s*(.*?)\s*$", line)
            if match:
                return match.group(1).strip("\"'")
    return ""


def _skill_file(skill_dir: Path) -> str | None:
    return next(
        (name for name in ("SKILL.cn.md", "SKILL.md") if (skill_dir / name).is_file()),
        None,
    )


def _iter_skill_dirs(root: Path):
    """Yield direct Skills plus repository bundles shaped as repo/skills/<id>."""
    for entry in sorted(root.iterdir()):
        if not entry.is_dir():
            continue
        if _skill_file(entry):
            yield entry
            continue
        nested = entry / "skills"
        if not nested.is_dir():
            continue
        for skill_dir in sorted(nested.iterdir()):
            if skill_dir.is_dir() and _skill_file(skill_dir):
                yield skill_dir


def _read_alias_data() -> dict:
    if not SKILL_ALIAS_PATH.is_file():
        return {"version": 1, "aliases": {}}
    try:
        data = json.loads(_read_text(SKILL_ALIAS_PATH))
    except (OSError, json.JSONDecodeError):
        return {"version": 1, "aliases": {}}
    aliases = data.get("aliases") if isinstance(data, dict) else {}
    return {"version": 1, "aliases": aliases if isinstance(aliases, dict) else {}}


def _write_alias_data(data: dict) -> None:
    SKILL_ALIAS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    handle, temporary = tempfile.mkstemp(
        prefix="skill_display_names_", suffix=".tmp", dir=SKILL_ALIAS_PATH.parent
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, SKILL_ALIAS_PATH)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _clean_display_name(value: str, skill_id: str = "") -> str:
    name = re.sub(r"\s+", " ", str(value or "")).strip()
    if skill_id:
        name = re.sub(rf"\s*[\[（(]{re.escape(skill_id)}[\]）)]\s*$", "", name, flags=re.I).strip()
    if not name:
        raise ValueError("Skill显示名称不能为空。")
    if len(name) > 60:
        raise ValueError("Skill显示名称不能超过60个字符。")
    if any(ord(char) < 32 for char in name):
        raise ValueError("Skill显示名称不能包含换行或控制字符。")
    return name


def _source_display_name(value: str, skill_id: str) -> str:
    name = re.sub(r"\s+", " ", str(value or "")).strip()
    name = re.sub(rf"\s*[\[（(]{re.escape(skill_id)}[\]）)]\s*$", "", name, flags=re.I).strip()
    return (name or skill_id)[:100]


def _display_issues(name: str, skill_id: str) -> list[str]:
    value = str(name or "").strip()
    issues = []
    if not value or value == skill_id:
        issues.append("raw-id")
    if value and not _CHINESE_RE.search(value):
        issues.append("no-chinese-name")
    if len(value) > 32:
        issues.append("too-long")
    if re.search(r"\.(?:json|ya?ml|md)\b|[/\\]|：$", value, re.I):
        issues.append("looks-like-content")
    if skill_id and re.search(rf"[\[（(]?{re.escape(skill_id)}[\]）)]?", value, re.I):
        issues.append("contains-id")
    return issues


def _references(skill_dir: Path) -> list[str]:
    root = skill_dir / "references"
    if not root.is_dir():
        return []
    return sorted(
        path.relative_to(skill_dir).as_posix()
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in _TEXT_EXTENSIONS
    )


def _scan_skills(include_root: bool = False) -> tuple[dict, ...]:
    found: dict[str, dict] = {}
    alias_data = _read_alias_data().get("aliases", {})
    for root in _skill_roots():
        for skill_dir in _iter_skill_dirs(root):
            skill_id = skill_dir.name
            if skill_id in found or not _ID_RE.fullmatch(skill_id):
                continue
            skill_file = _skill_file(skill_dir)
            if not skill_file:
                continue
            body = _read_text(skill_dir / skill_file)
            metadata = _frontmatter(body)
            source_name = (
                _meta(skill_dir, "display-name-zh")
                or metadata.get("display-name-zh")
                or metadata.get("name-zh")
                or _agent_display_name(skill_dir)
                or _heading(body)
                or _meta(skill_dir, "name")
                or metadata.get("name")
                or skill_id
            )
            source_name = _source_display_name(str(source_name), skill_id)
            description = (
                _meta(skill_dir, "summary-cn")
                or metadata.get("summary-cn")
                or _meta(skill_dir, "description")
                or metadata.get("description")
                or ""
            )
            alias = alias_data.get(skill_id) if isinstance(alias_data, dict) else None
            alias = alias if isinstance(alias, dict) else {}
            display_name = str(alias.get("display_name") or source_name).strip() or skill_id
            display_source = str(alias.get("source") or "metadata") if alias.get("display_name") else "metadata"
            issues = _display_issues(str(source_name), skill_id)
            item = {
                "id": skill_id,
                "name": display_name[:100],
                "source_name": str(source_name)[:100],
                "display_name": display_name[:100],
                "display_source": display_source,
                "label": f"{display_name} [{skill_id}]" if display_name != skill_id else skill_id,
                "description": str(description)[:500],
                "skill_file": skill_file,
                "references": _references(skill_dir),
                "issues": issues,
                "needs_optimization": bool(issues) and not bool(alias.get("display_name")),
            }
            if include_root:
                item["_root"] = str(skill_dir.resolve())
            found[skill_id] = item
    counts: dict[str, int] = {}
    for item in found.values():
        counts[item["display_name"]] = counts.get(item["display_name"], 0) + 1
    for item in found.values():
        if counts.get(item["display_name"], 0) > 1 and "duplicate-name" not in item["issues"]:
            item["issues"].append("duplicate-name")
            if item.get("display_source") == "metadata":
                item["needs_optimization"] = True
    return tuple(found[key] for key in sorted(found))


def list_skills() -> tuple[dict, ...]:
    return _scan_skills(False)


def skill_catalog() -> dict:
    skills = list(list_skills())
    return {
        "version": 2,
        "skills": skills,
        "counts": {
            "total": len(skills),
            "issues": sum(bool(item.get("needs_optimization")) for item in skills),
            "manual": sum(item.get("display_source") == "manual" for item in skills),
            "model": sum(item.get("display_source") == "model" for item in skills),
        },
    }


def resolve_skill_id(value: str) -> str:
    selected = str(value or "").strip()
    if selected in ("", "自动选择", "自动匹配"):
        return ""
    if _ID_RE.fullmatch(selected) and get_skill(selected):
        return selected
    bracket = re.search(r"\[([A-Za-z0-9][A-Za-z0-9._-]{0,63})\]\s*$", selected)
    if bracket and get_skill(bracket.group(1)):
        return bracket.group(1)
    return next((item["id"] for item in list_skills() if item["label"] == selected), "")


def set_skill_display_name(skill_id: str, display_name: str | None, source: str = "manual") -> dict:
    skill_id = str(skill_id or "").strip()
    if not get_skill(skill_id):
        raise ValueError(f"当前 Skill 不存在：{skill_id}")
    with _ALIAS_LOCK:
        data = _read_alias_data()
        aliases = data.setdefault("aliases", {})
        if display_name is None or not str(display_name).strip():
            aliases.pop(skill_id, None)
        else:
            aliases[skill_id] = {
                "display_name": _clean_display_name(display_name, skill_id),
                "source": "model" if source == "model" else "manual",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        _write_alias_data(data)
    return skill_catalog()


def set_model_display_names(names: dict[str, str], overwrite_manual: bool = False) -> dict:
    current = {item["id"]: item for item in list_skills()}
    with _ALIAS_LOCK:
        data = _read_alias_data()
        aliases = data.setdefault("aliases", {})
        for skill_id, display_name in names.items():
            if skill_id not in current:
                continue
            existing = aliases.get(skill_id) if isinstance(aliases.get(skill_id), dict) else {}
            if existing.get("source") == "manual" and not overwrite_manual:
                continue
            aliases[skill_id] = {
                "display_name": _clean_display_name(display_name, skill_id),
                "source": "model",
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        _write_alias_data(data)
    return skill_catalog()


def get_skill(skill_id: str) -> dict | None:
    return next((item for item in _scan_skills(True) if item["id"] == skill_id), None)


def read_skill(skill: dict) -> str:
    return _read_text(Path(skill["_root"]) / skill["skill_file"])


def read_reference(skill: dict, relative_path: str) -> str:
    normalized = str(relative_path or "").replace("\\", "/").strip("/")
    if normalized not in skill.get("references", []):
        raise ValueError(f"Skill资料不存在：{normalized}")
    root = Path(skill["_root"]).resolve()
    path = (root / normalized).resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError("Skill资料路径无效。")
    return _read_text(path)


def _safe_upload_path(raw: str) -> Path:
    value = str(raw or "").replace("\\", "/")
    if not value or "\x00" in value or value.startswith("/") or re.match(r"^[A-Za-z]:", value):
        raise ValueError("上传包包含无效文件路径。")
    value = value.rstrip("/")
    pure = PurePosixPath(value)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ValueError(f"上传包包含不安全路径：{raw}")
    return Path(*pure.parts)


def _ignore_package_path(relative: Path) -> bool:
    return any(part in _IGNORED_PACKAGE_PARTS for part in relative.parts) or relative.name in {".DS_Store", "Thumbs.db"}


def _copy_uploaded_folder(files: list[tuple[str, Path]], destination: Path) -> None:
    if not files:
        raise ValueError("没有收到可安装的Skill文件。")
    if len(files) > MAX_SKILL_FILES:
        raise ValueError(f"Skill文件数量超过上限（最多{MAX_SKILL_FILES}个）。")
    total = 0
    seen = set()
    for relative_name, source in files:
        relative = _safe_upload_path(relative_name)
        if _ignore_package_path(relative):
            continue
        key = relative.as_posix().lower()
        if key in seen:
            raise ValueError(f"上传包包含重复路径：{relative.as_posix()}")
        seen.add(key)
        size = source.stat().st_size
        total += size
        if total > MAX_SKILL_UPLOAD_BYTES:
            raise ValueError("Skill文件夹总大小超过512MB上限。")
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def _extract_skill_archive(archive: Path, destination: Path) -> None:
    if archive.stat().st_size > MAX_SKILL_ARCHIVE_BYTES:
        raise ValueError("Skill压缩包超过128MB上限。")
    try:
        handle = zipfile.ZipFile(archive)
    except zipfile.BadZipFile as error:
        raise ValueError("上传文件不是有效的ZIP压缩包。") from error
    with handle:
        entries = handle.infolist()
        if len(entries) > MAX_SKILL_FILES:
            raise ValueError(f"ZIP内文件数量超过上限（最多{MAX_SKILL_FILES}个）。")
        total = 0
        seen = set()
        for info in entries:
            relative = _safe_upload_path(info.filename)
            if _ignore_package_path(relative) or info.is_dir():
                continue
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"ZIP不允许包含符号链接：{info.filename}")
            key = relative.as_posix().lower()
            if key in seen:
                raise ValueError(f"ZIP包含重复路径：{relative.as_posix()}")
            seen.add(key)
            total += max(0, int(info.file_size))
            if total > MAX_SKILL_UPLOAD_BYTES:
                raise ValueError("ZIP解压后总大小超过512MB上限。")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with handle.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)


def _candidate_skill_dirs(source: Path) -> list[Path]:
    candidates = []
    for path in source.rglob("*"):
        if not path.is_dir() or _ignore_package_path(path.relative_to(source)):
            continue
        if _skill_file(path):
            candidates.append(path)
    if _skill_file(source):
        candidates.append(source)
    selected = []
    for path in sorted(set(candidates), key=lambda item: (len(item.relative_to(source).parts), str(item))):
        if any(path == chosen or chosen in path.parents for chosen in selected):
            continue
        selected.append(path)
    return selected


def _validate_skill_candidate(skill_dir: Path) -> dict:
    skill_file = _skill_file(skill_dir)
    if not skill_file:
        raise ValueError(f"{skill_dir.name} 缺少 SKILL.md 或 SKILL.cn.md。")
    body = _read_text(skill_dir / skill_file)
    metadata = _frontmatter(body)
    skill_id = str(metadata.get("name") or "").strip()
    description = str(metadata.get("description") or "").strip()
    if not skill_id or not description:
        raise ValueError(f"{skill_dir.name}/{skill_file} 必须在YAML头中提供 name 和 description。")
    if not _STANDARD_ID_RE.fullmatch(skill_id):
        raise ValueError(f"Skill name“{skill_id}”不规范：只能使用小写字母、数字和连字符，最长64字符。")
    warnings = []
    if skill_dir.name != skill_id:
        warnings.append(f"目录名 {skill_dir.name} 与 name {skill_id} 不一致，安装时按 name 归一化。")
    return {"id": skill_id, "path": skill_dir, "skill_file": skill_file, "warnings": warnings}


def _package_root(source: Path) -> Path:
    visible = [path for path in source.iterdir() if not _ignore_package_path(path.relative_to(source))]
    return visible[0] if len(visible) == 1 and visible[0].is_dir() else source


def _safe_bundle_id(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")[:64]
    if not normalized or not _STANDARD_ID_RE.fullmatch(normalized):
        normalized = f"skill-bundle-{int(datetime.now(timezone.utc).timestamp())}"
    return normalized


def _copytree_ignore(_directory, names):
    return [name for name in names if name in _IGNORED_PACKAGE_PARTS or name in {".DS_Store", "Thumbs.db"}]


def _directory_manifest(root: Path) -> dict[str, tuple[int, str]]:
    manifest = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(root)
        if _ignore_package_path(relative):
            continue
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(1024 * 1024)
                if not chunk:
                    break
                digest.update(chunk)
        manifest[relative.as_posix()] = (path.stat().st_size, digest.hexdigest())
    return manifest


def _install_prepared_source(source: Path, package_hint: str) -> dict:
    root = _package_root(source)
    candidates = _candidate_skill_dirs(root)
    if not candidates:
        raise ValueError("没有找到可安装的Skill：需要 SKILL.md 或 SKILL.cn.md。")
    validated = [_validate_skill_candidate(path) for path in candidates]
    ids = [item["id"] for item in validated]
    if len(ids) != len(set(ids)):
        raise ValueError("上传包内存在重复的Skill name，已取消安装。")

    nested_root = root / "skills"
    bundle_mode = nested_root.is_dir() and any(nested_root == item["path"].parent or nested_root in item["path"].parents for item in validated)
    installs = []
    if bundle_mode:
        bundle_id = _safe_bundle_id(root.name if root != source else Path(package_hint).stem)
        installs.append({"destination": SKILLS_ROOT / bundle_id, "source": root, "bundle": True, "ids": ids})
    else:
        installs.extend({
            "destination": SKILLS_ROOT / item["id"],
            "source": item["path"],
            "bundle": False,
            "ids": [item["id"]],
        } for item in validated)

    reused = []
    conflicts = []
    for item in installs:
        destination = item["destination"]
        if not destination.exists():
            continue
        if destination.is_dir() and _directory_manifest(item["source"]) == _directory_manifest(destination):
            reused.append(item)
        else:
            conflicts.append(str(destination))
    if conflicts:
        raise FileExistsError(
            "以下Skill或仓库目录已存在且内容不同，未执行覆盖：" + ", ".join(conflicts)
        )

    SKILLS_ROOT.mkdir(parents=True, exist_ok=True)
    transaction = Path(tempfile.mkdtemp(prefix=".skill-install-", dir=SKILLS_ROOT))
    completed = []
    try:
        staged = []
        pending_installs = [item for item in installs if item not in reused]
        for index, item in enumerate(pending_installs):
            target = transaction / f"{index}-{item['destination'].name}"
            shutil.copytree(item["source"], target, ignore=_copytree_ignore)
            staged.append((target, item))
        for target, item in staged:
            target.replace(item["destination"])
            completed.append(item["destination"])
    except Exception:
        for path in completed:
            if path.is_dir():
                shutil.rmtree(path)
        raise
    finally:
        shutil.rmtree(transaction, ignore_errors=True)

    warnings = [warning for item in validated for warning in item["warnings"]]
    if reused:
        warnings.append(
            "检测到相同Skill内容已存在，已直接复用："
            + ", ".join(item["destination"].name for item in reused)
        )
    catalog = skill_catalog()
    catalog_ids = {item["id"] for item in catalog.get("skills", [])}
    missing_ids = [skill_id for skill_id in ids if skill_id not in catalog_ids]
    if missing_ids:
        for path in completed:
            if path.is_dir():
                shutil.rmtree(path)
        raise RuntimeError(
            "Skill已复制但目录扫描未发现，安装已回滚：" + ", ".join(missing_ids)
        )
    return {
        "installed_ids": ids,
        "installed_paths": [item["destination"].name for item in installs],
        "reused_paths": [item["destination"].name for item in reused],
        "reused": bool(reused),
        "bundle": bundle_mode,
        "warnings": warnings,
        "catalog": catalog,
    }


def install_uploaded_skills(files: list[tuple[str, Path]], mode: str, package_hint: str = "uploaded-skill") -> dict:
    mode = str(mode or "").lower()
    if mode not in {"zip", "folder"}:
        raise ValueError("上传模式必须是 zip 或 folder。")
    with _INSTALL_LOCK, tempfile.TemporaryDirectory(prefix="dapao-skill-upload-") as temporary:
        workspace = Path(temporary)
        source = workspace / "source"
        source.mkdir()
        if mode == "zip":
            if len(files) != 1:
                raise ValueError("每次只能上传一个ZIP压缩包。")
            package_hint = files[0][0]
            _extract_skill_archive(files[0][1], source)
        else:
            _copy_uploaded_folder(files, source)
            if files:
                package_hint = PurePosixPath(str(files[0][0]).replace("\\", "/")).parts[0]
        return _install_prepared_source(source, package_hint)


def json_value(raw, fallback):
    try:
        return json.loads(raw or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def normalize_history(raw) -> list[dict]:
    value = json_value(raw, [])
    if not isinstance(value, list):
        return []
    result = []
    for item in value:
        if not isinstance(item, dict) or item.get("role") not in ("user", "assistant"):
            continue
        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            continue
        message = {"role": item["role"], "content": content.strip()}
        images = normalize_image_refs(item.get("images", [])) if item["role"] == "user" else []
        if images:
            message["images"] = images
        if item["role"] == "user" and isinstance(item.get("materials"), list):
            materials = []
            for material in item["materials"][:30]:
                if not isinstance(material, dict):
                    continue
                kind = str(material.get("kind") or "")
                try:
                    slot = int(material.get("slot"))
                except (TypeError, ValueError):
                    continue
                if kind not in {"image", "video", "audio"}:
                    continue
                materials.append({
                    "kind": kind,
                    "slot": slot,
                    "token": str(material.get("token") or "")[:20],
                    "label": str(material.get("label") or "")[:80],
                })
            if materials:
                message["materials"] = materials
        for key in ("token_count", "created_at"):
            try:
                number = int(item.get(key))
            except (TypeError, ValueError):
                continue
            if number >= 0:
                message[key] = number
        if item["role"] == "assistant" and isinstance(item.get("flow_before"), dict):
            message["flow_before"] = normalize_state(item["flow_before"])
        if item["role"] == "assistant" and isinstance(item.get("usage"), dict):
            raw_usage = item["usage"]
            usage = {}
            for key in ("prompt_tokens", "completion_tokens", "total_tokens", "calls"):
                try:
                    number = max(0, int(raw_usage.get(key) or 0))
                except (TypeError, ValueError):
                    number = 0
                usage[key] = number
            try:
                cost = float(raw_usage.get("cost"))
            except (TypeError, ValueError):
                cost = None
            if cost is not None and cost >= 0:
                usage["cost"] = round(cost, 8)
                usage["currency"] = str(raw_usage.get("currency") or "")[:12].upper()
            usage["source"] = str(raw_usage.get("source") or "estimated")[:20]
            if any(usage.get(key) for key in ("prompt_tokens", "completion_tokens", "total_tokens", "calls")) or cost is not None:
                message["usage"] = usage
        result.append(message)
    return result


def normalize_image_refs(raw) -> list[dict]:
    value = json_value(raw, raw if isinstance(raw, list) else [])
    if not isinstance(value, list):
        return []
    result = []
    for ref in value[:12]:
        if not isinstance(ref, dict):
            continue
        filename = os.path.basename(str(ref.get("filename") or ref.get("name") or "").strip())
        subfolder = str(ref.get("subfolder") or "").replace("\\", "/").strip("/")
        if filename and (not subfolder or all(part not in ("", ".", "..") for part in subfolder.split("/"))):
            result.append({"filename": filename, "subfolder": subfolder, "type": "input"})
    return result


def normalize_material_library(value) -> dict:
    """Validate the lightweight runtime object produced by the material node."""
    if value in (None, ""):
        return {"version": 1, "items": []}
    if not isinstance(value, dict) or not isinstance(value.get("items"), list):
        raise ValueError("多轮对话素材库格式无效，请重新连接素材库节点。")
    limits = {"image": 20, "video": 5, "audio": 5}
    names = {"image": "图片", "video": "视频", "audio": "音频"}
    seen = set()
    counts = {key: 0 for key in limits}
    items = []
    for raw in value["items"]:
        if not isinstance(raw, dict):
            raise ValueError("多轮对话素材库包含无效素材项目。")
        kind = str(raw.get("kind") or "")
        try:
            slot = int(raw.get("slot"))
        except (TypeError, ValueError) as error:
            raise ValueError("多轮对话素材库包含无效素材编号。") from error
        if kind not in limits or not 1 <= slot <= limits[kind]:
            raise ValueError("多轮对话素材库包含未知类型或超出上限的素材。")
        token = f"@{names[kind]}{slot}"
        if raw.get("token") not in (None, token) or token in seen:
            raise ValueError(f"素材标记重复或格式错误：{token}")
        if raw.get("value") is None:
            raise ValueError(f"素材 {token} 没有有效的ComfyUI输入对象。")
        seen.add(token)
        counts[kind] += 1
        label = str(raw.get("label") or token).strip()[:80] or token
        items.append({"kind": kind, "slot": slot, "token": token, "label": label, "value": raw["value"]})
    for kind, count in counts.items():
        if count > limits[kind]:
            raise ValueError(f"{names[kind]}素材最多{limits[kind]}个，当前为{count}个。")
    return {"version": 1, "items": items}


def select_material_mentions(text: str, library) -> list[dict]:
    """Resolve only stable @ tokens from the current turn, preserving order."""
    normalized = normalize_material_library(library)
    by_token = {item["token"]: item for item in normalized["items"]}
    mentioned = [match.group(0) for match in _MATERIAL_TOKEN_RE.finditer(str(text or ""))]
    malformed = []
    for match in _MATERIAL_LIKE_RE.finditer(str(text or "")):
        token = match.group(0)
        if token not in mentioned:
            malformed.append(token)
    if malformed:
        raise ValueError("素材标记编号超出允许范围：" + "、".join(dict.fromkeys(malformed)))
    unknown = [token for token in mentioned if token not in by_token]
    if unknown:
        raise ValueError("本轮引用了当前素材库中未连接或已失效的素材：" + "、".join(dict.fromkeys(unknown)))
    selected = []
    seen = set()
    for token in mentioned:
        if token not in seen:
            selected.append(by_token[token])
            seen.add(token)
    return selected


def _pil_png_data_uri(image: Image.Image, max_edge: int) -> str:
    image = resize_pil_for_input(image.convert("RGBA" if image.mode == "RGBA" else "RGB"), max_edge)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _temporary_video_path(video_input, slot: int):
    if isinstance(video_input, str):
        value = video_input.strip()
        if os.path.isfile(value):
            return value, False
        if value.startswith(("http://", "https://")):
            import requests

            handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            handle.close()
            try:
                response = requests.get(value, stream=True, timeout=180, allow_redirects=True)
                response.raise_for_status()
                total = 0
                with open(handle.name, "wb") as output:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if not chunk:
                            continue
                        total += len(chunk)
                        if total > 512 * 1024 * 1024:
                            raise ValueError(f"@视频{slot}超过512MB，请先压缩或裁剪后再连接。")
                        output.write(chunk)
                return handle.name, True
            except Exception:
                try:
                    os.remove(handle.name)
                except OSError:
                    pass
                raise
        raise ValueError(f"@视频{slot}路径不存在或不是HTTP/HTTPS地址。")
    if isinstance(video_input, dict):
        for key in ("file_path", "path", "filename"):
            path = video_input.get(key)
            if isinstance(path, str) and os.path.isfile(path):
                return path, False
    if not hasattr(video_input, "save_to"):
        raise ValueError(f"无法读取@视频{slot}，请连接ComfyUI原生VIDEO输出。")
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    handle.close()
    try:
        saved = video_input.save_to(handle.name)
        if saved is False or not os.path.isfile(handle.name) or os.path.getsize(handle.name) <= 0:
            raise ValueError(f"@视频{slot}保存失败。")
        return handle.name, True
    except Exception:
        try:
            os.remove(handle.name)
        except OSError:
            pass
        raise


def _video_frame_parts(video_input, slot: int, max_edge: int, sample_count: int = 6) -> list[dict]:
    import numpy as np

    path, temporary = _temporary_video_path(video_input, slot)
    capture = None
    try:
        try:
            import cv2
        except ImportError as error:
            raise RuntimeError("当前ComfyUI Python缺少opencv-python，无法为通用LLM抽取视频帧。") from error
        capture = cv2.VideoCapture(path)
        if not capture.isOpened():
            raise ValueError(f"@视频{slot}无法解码，请先转为常见MP4格式。")
        fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if fps <= 0 or frame_count <= 0:
            raise ValueError(f"@视频{slot}缺少有效帧率或帧数信息。")
        duration = frame_count / fps
        last_time = max(0.0, duration - max(1.0 / fps, 0.04))
        timestamps = np.linspace(0.0, last_time, max(2, min(8, int(sample_count))))
        parts = [{
            "type": "text",
            "text": f"{f'@视频{slot}'}：模型不支持原生视频输入，下面是均匀抽取的{len(timestamps)}个代表帧，按时间顺序分析。",
        }]
        extracted = 0
        for timestamp in timestamps:
            capture.set(cv2.CAP_PROP_POS_MSEC, float(timestamp) * 1000.0)
            ok, frame = capture.read()
            if not ok or frame is None:
                continue
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            parts.append({"type": "text", "text": f"@视频{slot} 抽帧时间 {float(timestamp):.3f}s"})
            parts.append({"type": "image_url", "image_url": {"url": _pil_png_data_uri(Image.fromarray(rgb), max_edge)}})
            extracted += 1
        if extracted < 2:
            raise ValueError(f"@视频{slot}提取到的有效画面不足2帧。")
        return parts
    finally:
        if capture is not None:
            capture.release()
        if temporary:
            try:
                os.remove(path)
            except OSError:
                pass


def _audio_input_part(audio_input, slot: int) -> tuple[dict, float]:
    import numpy as np

    if not isinstance(audio_input, dict) or audio_input.get("waveform") is None:
        raise ValueError(f"无法读取@音频{slot}，请连接ComfyUI原生AUDIO输出。")
    sample_rate = int(audio_input.get("sample_rate") or audio_input.get("sampler_rate") or 44100)
    if sample_rate <= 0:
        raise ValueError(f"@音频{slot}采样率无效。")
    waveform = audio_input["waveform"]
    if hasattr(waveform, "detach"):
        waveform = waveform.detach().cpu().numpy()
    array = np.asarray(waveform)
    if array.ndim == 3:
        if array.shape[0] != 1:
            raise ValueError(f"@音频{slot}包含多个批次，请先拆分为单条音频。")
        array = array[0]
    array = np.squeeze(array)
    if array.ndim == 1:
        array = array.reshape(1, -1)
    elif array.ndim == 2 and array.shape[0] > 8 and array.shape[1] <= 8:
        array = array.T
    if array.ndim != 2 or not 1 <= array.shape[0] <= 8:
        raise ValueError(f"@音频{slot}声道格式无法识别。")
    if np.issubdtype(array.dtype, np.integer):
        maximum = max(abs(np.iinfo(array.dtype).min), np.iinfo(array.dtype).max)
        array = array.astype(np.float32) / float(maximum)
    else:
        array = array.astype(np.float32)
    mono = np.nan_to_num(np.clip(array, -1.0, 1.0)).mean(axis=0)
    duration = mono.size / float(sample_rate)
    target_rate = 16_000
    if sample_rate != target_rate and mono.size:
        target_size = max(1, round(mono.size * target_rate / sample_rate))
        mono = np.interp(
            np.linspace(0.0, mono.size - 1, target_size),
            np.arange(mono.size),
            mono,
        ).astype(np.float32)
    pcm = (np.clip(mono, -1.0, 1.0) * 32767.0).astype(np.int16)
    if pcm.nbytes > 25 * 1024 * 1024:
        raise ValueError(f"@音频{slot}压缩为16kHz单声道后仍超过25MB，请先裁剪音频。")
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(target_rate)
        output.writeframes(pcm.tobytes())
    return {
        "type": "input_audio",
        "input_audio": {"data": base64.b64encode(buffer.getvalue()).decode("ascii"), "format": "wav"},
    }, duration


def current_message_content(
    text: str,
    uploaded_images: list[dict],
    selected_materials: list[dict],
    max_edge: int,
    capabilities: dict,
) -> tuple[str | list[dict], dict]:
    """Build only the current turn's media parts at the actual request boundary."""
    if not uploaded_images and not selected_materials:
        return text, {"image_parts": 0, "video_frames": 0, "audio_seconds": 0.0}
    parts = [{"type": "text", "text": text}]
    stats = {"image_parts": 0, "video_frames": 0, "audio_seconds": 0.0}
    for ref in uploaded_images:
        parts.append({"type": "image_url", "image_url": {"url": image_data_uri(ref, max_edge)}})
        stats["image_parts"] += 1
    for item in selected_materials:
        token, label = item["token"], item["label"]
        parts.append({"type": "text", "text": f"当前轮引用素材：{token}（{label}）"})
        if item["kind"] == "image":
            uris = tensor_to_png_data_uris(item["value"], max_edge)
            if len(uris) != 1:
                raise ValueError(f"{token}必须是单张IMAGE，请在素材库前拆分批次。")
            parts.append({"type": "image_url", "image_url": {"url": uris[0]}})
            stats["image_parts"] += 1
        elif item["kind"] == "video":
            if not capabilities.get("supports_images"):
                raise RuntimeError("当前模型既不支持原生视频，也不支持视频抽帧所需的图片输入，请切换多模态模型。")
            frame_parts = _video_frame_parts(item["value"], item["slot"], max_edge)
            parts.extend(frame_parts)
            stats["video_frames"] += sum(part.get("type") == "image_url" for part in frame_parts)
        else:
            if not capabilities.get("supports_audio"):
                raise RuntimeError("当前模型不支持音频输入，请切换 Gemini 多模态映射模型后重试。")
            audio_part, duration = _audio_input_part(item["value"], item["slot"])
            parts.append(audio_part)
            stats["audio_seconds"] += duration
    return parts, stats


def normalize_state(raw) -> dict:
    value = raw if isinstance(raw, dict) else json_value(raw, {})
    if not isinstance(value, dict):
        value = {}
    try:
        context_cutoff = max(0, int(value.get("context_cutoff") or 0))
    except (TypeError, ValueError):
        context_cutoff = 0
    return {
        "version": 3,
        "skill": str(value.get("skill") or ""),
        "skill_name": str(value.get("skill_name") or "")[:100],
        "stage": str(value.get("stage") or "未开始")[:80],
        "loaded_references": [
            str(item)
            for item in value.get("loaded_references", value.get("loaded", []))
            if isinstance(item, str)
        ][:100],
        "final_result": str(value.get("final_result", value.get("final", "")) or ""),
        "context_cutoff": context_cutoff,
    }


def build_skill_prompt(base: str, skill: dict, state: dict) -> str:
    loaded = [
        f"\n--- 已载入资料：{path} ---\n{read_reference(skill, path)}"
        for path in state["loaded_references"]
        if path in skill["references"]
    ]
    catalogue = "\n".join(f"- {path}" for path in skill["references"]) or "- 无"
    loaded_names = "、".join(state["loaded_references"]) or "无"
    protocol = (
        "你正在通过 ComfyUI 的 dapaoAI Skill 执行器工作。只完成当前对话中能完成的内容，"
        "不得声称已调用联网、画布、媒体生成或其他未连接工具。信息不足或到达确认门时先提问，"
        "每次只推进当前阶段。回复正文之后必须追加且最后只能出现一个状态标记："
        '<dapao_local_skill_state>{"stage":"当前阶段","options":[],'
        '"load_references":[],"final":false}</dapao_local_skill_state>。'
        "options 最多6个；load_references 只能填写可用资料中的相对路径；"
        "只有交付完整最终产物时 final 才能为 true。使用简体中文交流。"
    )
    return "\n\n".join(
        item
        for item in (
            base.strip(),
            f"当前工作 Skill：{skill['name']} ({skill['id']})\n当前阶段：{state['stage']}"
            f"\n可用资料：\n{catalogue}\n已加载资料：{loaded_names}",
            read_skill(skill),
            *loaded,
            protocol,
        )
        if item
    )


def parse_skill_reply(raw: str) -> tuple[str, dict]:
    matches = list(STATE_TAG.finditer(raw or ""))
    if not matches:
        return str(raw or "").strip(), {}
    last = matches[-1]
    state = json_value(last.group(1), {})
    text = (raw[: last.start()] + raw[last.end() :]).strip()
    return text, state if isinstance(state, dict) else {}


def clean_reply(text: str) -> str:
    value = str(text or "").strip()
    match = re.search(r"<think>.*?</think>(.*)", value, re.S)
    return match.group(1).strip() if match else value


def estimate_text_tokens(text: str) -> int:
    value = str(text or "")
    cjk = sum(1 for char in value if "\u3400" <= char <= "\u9fff")
    return max(1, cjk + math.ceil((len(value) - cjk) / 4))


def estimate_history_tokens(system: str, history: list[dict], user_text: str, image_count: int) -> int:
    total = estimate_text_tokens(system) + 12
    for item in history:
        total += estimate_text_tokens(item.get("content", "")) + 8
        total += len(item.get("images", [])) * 1536
    return total + estimate_text_tokens(user_text) + 8 + image_count * 1536


def trim_history(history, system, user_text, max_tokens, context_limit, max_output, image_count):
    context_limit = max(2048, int(context_limit))
    requested_output = min(max(32, int(max_tokens)), max(32, int(max_output)), context_limit - 512)
    output_reserve = requested_output
    safety_margin = 128
    current = list(history)
    trimmed_count = 0
    budget = max(256, context_limit - output_reserve - safety_margin)
    used = estimate_history_tokens(system, current, user_text, image_count)
    while current and used > budget:
        current.pop(0)
        trimmed_count += 1
        if current and current[0].get("role") == "assistant":
            current.pop(0)
            trimmed_count += 1
        used = estimate_history_tokens(system, current, user_text, image_count)
    if used > budget:
        output_reserve = min(requested_output, max(32, context_limit - used - safety_margin))
        budget = max(256, context_limit - output_reserve - safety_margin)
    if used > budget:
        recommended = math.ceil((used + safety_margin + 32) / 1024) * 1024
        raise ValueError(
            f"系统提示词、Skill、图片与本轮消息约需 {used} tokens，超过当前 {context_limit} 上下文。"
            f"已清理历史并压缩输出仍无法容纳；请缩短内容、减少图片，或把上下文上限提高到至少 {recommended}。"
        )
    return current, budget, used, output_reserve, trimmed_count


def image_data_uri(ref: dict, max_edge: int = MAX_INPUT_IMAGE_EDGE) -> str:
    import folder_paths

    root = Path(folder_paths.get_input_directory()).resolve()
    path = (root / ref.get("subfolder", "") / ref["filename"]).resolve()
    if root not in path.parents or not path.is_file():
        raise ValueError(f"找不到对话图片：{ref.get('filename', '')}")
    with Image.open(path) as source:
        image = resize_pil_for_input(source.convert("RGBA" if source.mode == "RGBA" else "RGB"), max_edge)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def message_content(text: str, images: list[dict], max_edge: int):
    if not images:
        return text
    parts = [{"type": "text", "text": text}]
    parts.extend(
        {"type": "image_url", "image_url": {"url": image_data_uri(ref, max_edge)}}
        for ref in images
    )
    return parts


def api_messages(history: list[dict], max_edge: int) -> list[dict]:
    # Media is deliberately current-turn-only.  Historical user records keep
    # attachment metadata for the UI/regenerate action, but subsequent API
    # calls carry the prior text/analysis only.  Re-reference a library item
    # with @ when the model must inspect it again.
    return [
        {
            "role": item["role"],
            "content": item["content"],
        }
        for item in history
    ]


__all__ = [
    "SKILLS_ROOT",
    "api_messages",
    "build_skill_prompt",
    "clean_reply",
    "current_message_content",
    "estimate_text_tokens",
    "get_skill",
    "list_skills",
    "message_content",
    "normalize_history",
    "normalize_image_refs",
    "normalize_material_library",
    "normalize_state",
    "parse_skill_reply",
    "read_reference",
    "read_skill",
    "select_material_mentions",
    "trim_history",
]
