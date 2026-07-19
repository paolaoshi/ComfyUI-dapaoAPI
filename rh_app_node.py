"""
RunningHub AI application node.

Loads an application's exposed parameters, uploads connected media to the
legacy AI-app API, submits an asynchronous task, and returns image/video URLs.
"""

import io
import json
import mimetypes
import os
import tempfile
import time
import traceback
from urllib.parse import urlparse

import requests
import torch
import torch.nn.functional as F
from PIL import Image

from .rh_all_image_node import API_CHANNEL_CHOICES, create_blank_tensor, pil2tensor
from .rh_all_video_seedance_node import DapaoRHAllVideoSeedanceNode, IO, RHSeedanceVideoAdapter


NODE_NAME = "DapaoRHAppNode"
CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"

APP_BASE_URLS = {
    "国内版": "https://www.runninghub.cn",
    "国外版": "https://www.runninghub.ai",
}

AUTH_ERROR_CODES = {"401", "403", "433"}
RUNNING_CODES = {"804", "813"}
FAILED_CODES = {"805"}

URL_KEYS = (
    "fileUrl",
    "file_url",
    "downloadUrl",
    "download_url",
    "resultUrl",
    "result_url",
    "outputUrl",
    "output_url",
    "signedUrl",
    "signed_url",
    "publicUrl",
    "public_url",
    "previewUrl",
    "preview_url",
    "url",
)


def _log_info(message):
    print(f"[dapaoAPI-RH应用] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH应用] 错误：{message}")


def _base_url(api_channel):
    base_url = APP_BASE_URLS.get(api_channel)
    if not base_url:
        raise ValueError(f"不支持的 API渠道：{api_channel}")
    return base_url


def _headers(api_key, api_channel, json_content=True):
    host = urlparse(_base_url(api_channel)).netloc
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Host": host,
        "User-Agent": "ComfyUI-dapaoAPI/RHApp",
    }
    if json_content:
        headers["Content-Type"] = "application/json"
    return headers


def _response_message(response):
    text = (response.text or "")[:1500]
    try:
        data = response.json()
        if isinstance(data, dict):
            return (
                data.get("msg")
                or data.get("message")
                or data.get("error")
                or (data.get("data") or {}).get("message")
                or text
            )
    except Exception:
        pass
    return text


def _authentication_error(api_channel, status, message):
    return RuntimeError(
        f"RunningHub 应用认证失败 {status}：当前选择的是“{api_channel}”。"
        f"国内版和国外版使用不同的 API 密钥，请确认 API渠道与密钥一致。接口返回：{message}"
    )


def _raise_api_error(code, message, api_channel):
    code_text = str(code or "未知")
    if code_text in AUTH_ERROR_CODES:
        raise _authentication_error(api_channel, code_text, message)
    if code_text == "434":
        raise RuntimeError(f"RunningHub 应用ID不存在、已下架或与“{api_channel}”不匹配：{message}")
    if code_text == "435":
        raise RuntimeError(f"RunningHub 账户余额不足 435：{message}")
    if code_text == "421":
        raise RuntimeError(f"RunningHub 应用参数错误 421：请刷新应用参数后重试。接口返回：{message}")
    if code_text == "803":
        raise RuntimeError(f"RunningHub 队列已满 803，请稍后重试：{message}")
    if code_text in FAILED_CODES:
        raise RuntimeError(f"RunningHub 应用任务失败 {code_text}：{message}")
    raise RuntimeError(f"RunningHub 应用接口错误 {code_text}：{message}")


def _request_json(method, url, api_key, api_channel, timeout=60, params=None, payload=None):
    last_error = None
    for attempt in range(3):
        try:
            response = requests.request(
                method,
                url,
                headers=_headers(api_key, api_channel),
                params=params,
                json=payload,
                timeout=timeout,
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            last_error = error
            if attempt >= 2:
                raise RuntimeError(
                    f"RunningHub 应用{api_channel}连接失败，已尝试 3 次：{error}\n"
                    "如果启用了代理软件，请检查代理是否稳定，或将当前 RunningHub 域名配置为直连。"
                ) from error
            time.sleep(attempt + 1)
            continue

        message = _response_message(response)
        if response.status_code in (401, 403):
            raise _authentication_error(api_channel, response.status_code, message)
        if response.status_code >= 500 and attempt < 2:
            last_error = RuntimeError(f"HTTP {response.status_code}: {message}")
            time.sleep(attempt + 1)
            continue
        if response.status_code >= 400:
            raise RuntimeError(f"RunningHub 应用请求失败 HTTP {response.status_code}：{message}")

        try:
            data = response.json() if response.text else {}
        except Exception as error:
            raise RuntimeError(f"RunningHub 应用返回内容不是 JSON：{error}，响应：{response.text[:500]}") from error
        if not isinstance(data, dict):
            raise RuntimeError(f"RunningHub 应用返回格式错误：{str(data)[:500]}")
        return data

    raise RuntimeError(f"RunningHub 应用请求失败：{last_error}")


def _extract_options(field):
    field_type = str(field.get("fieldType") or "").upper()
    select_types = {"LIST", "SELECT", "DROPDOWN", "COMBO", "ENUM"}
    for key in (
        "fieldData",
        "options",
        "list",
        "values",
        "enum",
        "choices",
        "items",
        "selectOptions",
        "dropdown",
    ):
        candidate = field.get(key)
        if key == "fieldData" and field_type not in select_types:
            continue
        if isinstance(candidate, str):
            try:
                candidate = json.loads(candidate)
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
        if not isinstance(candidate, list) or not candidate:
            continue
        options = []
        for item in candidate:
            if isinstance(item, (str, int, float)):
                options.append(item)
            elif isinstance(item, dict):
                value = item.get(
                    "value",
                    item.get("index", item.get("name", item.get("label"))),
                )
                if value is not None:
                    options.append(value)
        if options:
            return options

    field_value = field.get("fieldValue")
    if field_type in select_types and isinstance(field_value, list):
        return [item for item in field_value if isinstance(item, (str, int, float))]
    return []


def _infer_value_type(field_type):
    field_type = str(field_type or "").upper()
    if field_type == "IMAGE":
        return "image"
    if field_type == "VIDEO":
        return "video"
    if field_type == "AUDIO":
        return "audio"
    if field_type in {"NUMBER", "FLOAT", "DOUBLE", "INTEGER", "INT"}:
        return "number"
    if field_type in {"BOOLEAN", "BOOL"}:
        return "boolean"
    return "text"


def _default_value(field, options):
    value = field.get("fieldValue")
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict) or value is None:
        return options[0] if options else ""
    return value


def _normalize_schema(data, api_channel, webapp_id):
    app_data = data.get("data") if isinstance(data.get("data"), dict) else data
    raw_fields = app_data.get("nodeInfoList") or []
    counters = {"image": 0, "video": 0, "audio": 0, "text": 0, "number": 0, "boolean": 0}
    schema = []
    for field in raw_fields:
        if not isinstance(field, dict):
            continue
        node_id = str(field.get("nodeId") or "").strip()
        field_name = str(field.get("fieldName") or "").strip()
        if not node_id or not field_name:
            continue
        value_type = _infer_value_type(field.get("fieldType"))
        options = _extract_options(field)
        normalized = {
            "nodeId": node_id,
            "fieldName": field_name,
            "fieldType": str(field.get("fieldType") or "TEXT"),
            "valueType": value_type,
            "description": str(field.get("description") or field.get("fieldDesc") or ""),
            "defaultValue": _default_value(field, options),
            "options": options,
            "required": bool(field.get("required") or field.get("isRequired")),
        }
        normalized["inputIndex"] = counters[value_type]
        if value_type in {"image", "video", "audio"}:
            normalized["mediaIndex"] = counters[value_type]
        counters[value_type] += 1
        schema.append(normalized)

    covers = app_data.get("covers") if isinstance(app_data.get("covers"), list) else []
    cover_url = ""
    if covers and isinstance(covers[0], dict):
        cover_url = str(covers[0].get("url") or covers[0].get("thumbnailUri") or "")

    return {
        "version": 1,
        "apiChannel": api_channel,
        "webappId": webapp_id,
        "appName": str(
            app_data.get("webappName")
            or app_data.get("appName")
            or app_data.get("name")
            or f"RH应用 {webapp_id}"
        ),
        "coverUrl": str(app_data.get("coverUrl") or cover_url),
        "accessEncrypted": bool(app_data.get("accessEncrypted")),
        "schema": schema,
        "mediaCounts": {kind: counters[kind] for kind in ("image", "video", "audio")},
        "inputCounts": counters,
    }


def fetch_rh_app_schema(api_channel, api_key, webapp_id, timeout=30):
    api_channel = str(api_channel or "国内版").strip()
    api_key = str(api_key or "").strip()
    webapp_id = str(webapp_id or "").strip()
    if not api_key:
        raise ValueError("请填写 RunningHub API密钥后再刷新应用参数。")
    if not webapp_id:
        raise ValueError("请填写 RunningHub 应用ID。")

    data = _request_json(
        "GET",
        f"{_base_url(api_channel)}/api/webapp/apiCallDemo",
        api_key,
        api_channel,
        timeout=timeout,
        params={"apiKey": api_key, "webappId": webapp_id},
    )
    code = str(data.get("code", "0"))
    if code != "0":
        _raise_api_error(code, data.get("msg") or data.get("message") or data, api_channel)
    return _normalize_schema(data, api_channel, webapp_id)


def upload_rh_app_file(api_channel, api_key, content, filename, mime_type, timeout=120):
    api_channel = str(api_channel or "国内版").strip()
    api_key = str(api_key or "").strip()
    if not api_key:
        raise ValueError("请填写 RunningHub API密钥后再上传素材。")
    if not content:
        raise ValueError("上传素材内容为空。")

    url = f"{_base_url(api_channel)}/task/openapi/upload"
    response = None
    for attempt in range(3):
        try:
            response = requests.post(
                url,
                headers=_headers(api_key, api_channel, json_content=False),
                data={"apiKey": api_key, "fileType": "input"},
                files={"file": (filename, content, mime_type)},
                timeout=max(timeout, 120),
            )
            break
        except (requests.ConnectionError, requests.Timeout) as error:
            if attempt >= 2:
                raise RuntimeError(f"RunningHub 应用素材上传失败，已尝试 3 次：{error}") from error
            time.sleep(attempt + 1)

    message = _response_message(response)
    if response.status_code in (401, 403):
        raise _authentication_error(api_channel, response.status_code, message)
    if response.status_code >= 400:
        raise RuntimeError(f"RunningHub 应用素材上传失败 HTTP {response.status_code}：{message}")
    data = response.json() if response.text else {}
    code = str(data.get("code", "0"))
    if code != "0":
        _raise_api_error(code, data.get("msg") or data.get("message") or data, api_channel)
    file_name = str((data.get("data") or {}).get("fileName") or "").strip()
    if not file_name:
        raise RuntimeError(f"RunningHub 素材上传成功但没有返回 fileName：{json.dumps(data, ensure_ascii=False)[:500]}")
    return file_name


class DapaoRHAppNode(DapaoRHAllVideoSeedanceNode):
    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for index in range(1, 9):
            optional[f"🖼️ 图像{index}"] = ("IMAGE", {"tooltip": f"自动对应应用暴露的第 {index} 个 IMAGE 参数。"})
        for index in range(1, 5):
            optional[f"🎞️ 视频{index}"] = (IO.VIDEO, {"tooltip": f"自动对应应用暴露的第 {index} 个 VIDEO 参数。"})
        for index in range(1, 5):
            optional[f"🎵 音频{index}"] = ("AUDIO", {"tooltip": f"自动对应应用暴露的第 {index} 个 AUDIO 参数。"})
        for index in range(1, 17):
            optional[f"📝 文本{index}"] = ("STRING", {
                "forceInput": True,
                "tooltip": f"自动对应应用暴露的第 {index} 个文本或下拉参数，上游输入优先。",
            })
        for index in range(1, 9):
            optional[f"🔢 数字{index}"] = ("FLOAT", {
                "forceInput": True,
                "tooltip": f"自动对应应用暴露的第 {index} 个数字参数，上游输入优先。",
            })
        for index in range(1, 9):
            optional[f"🔘 布尔{index}"] = ("BOOLEAN", {
                "forceInput": True,
                "tooltip": f"自动对应应用暴露的第 {index} 个布尔参数，上游输入优先。",
            })
        optional.update({
            "📋 额外节点参数JSON": ("STRING", {
                "multiline": True,
                "default": "[]",
                "placeholder": '[{"nodeId":"3","fieldName":"prompt","fieldValue":"一只猫"}]',
                "tooltip": "可选高级覆盖；相同 nodeId + fieldName 会覆盖动态表单值。",
            }),
            "🔁 最大轮询秒数": ("INT", {"default": 2400, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 10, "max": 600, "step": 1}),
            "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
        })
        return {
            "required": {
                "🌐 API渠道": (API_CHANNEL_CHOICES, {
                    "default": "国内版",
                    "tooltip": "国内版与国外版使用不同的应用ID和 API 密钥。",
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "填入 RunningHub 应用 API Key",
                    "tooltip": "国内版和国外版密钥不通用。",
                }),
                "🆔 应用ID": ("STRING", {
                    "default": "",
                    "placeholder": "输入 RunningHub Webapp ID",
                    "tooltip": "填写或修改后，点击“刷新应用参数”加载该应用暴露的参数。",
                }),
                "🧩 应用参数JSON": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "tooltip": "由动态参数面板自动维护。",
                }),
                "⚙️ 实例类型": (["默认", "plus", "pro"], {"default": "默认"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("IMAGE", IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🎬 视频", "🆔 任务ID", "🔗 输出URL", "📋 响应信息")
    FUNCTION = "run_app"
    CATEGORY = CATEGORY
    DESCRIPTION = "通过应用ID加载智能参数并运行 RunningHub AI 应用 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _blank_result(message=""):
        return (create_blank_tensor(), RHSeedanceVideoAdapter(""), "", "", message)

    @staticmethod
    def _parameter_key(node_id, field_name):
        return f"{node_id}::{field_name}"

    @staticmethod
    def _load_json(value, fallback):
        try:
            data = json.loads(value or json.dumps(fallback))
        except Exception as error:
            raise ValueError(f"JSON 格式错误：{error}") from error
        return data

    @staticmethod
    def _tensor_to_png_bytes(image_tensor):
        image = image_tensor[0]
        image_np = (image.cpu().numpy().clip(0, 1) * 255).astype("uint8")
        buffer = io.BytesIO()
        Image.fromarray(image_np).convert("RGB").save(buffer, format="PNG")
        return buffer.getvalue()

    def _upload_app_bytes(self, api_channel, api_key, content, filename, mime_type, timeout):
        return upload_rh_app_file(api_channel, api_key, content, filename, mime_type, timeout)

    def _video_bytes(self, video_input):
        if isinstance(video_input, str) and os.path.isfile(video_input):
            with open(video_input, "rb") as file:
                return file.read()
        temp_path = os.path.join(tempfile.gettempdir(), f"dapao_rh_app_{int(time.time() * 1000)}.mp4")
        try:
            if hasattr(video_input, "save_to"):
                video_input.save_to(temp_path)
                with open(temp_path, "rb") as file:
                    return file.read()
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
        raise ValueError("无法读取 VIDEO 输入，请确认上游节点输出有效视频。")

    def _connected_media_file(self, entry, kwargs, api_channel, api_key, timeout):
        value_type = entry.get("valueType")
        media_index = int(entry.get("mediaIndex", 0)) + 1
        if value_type == "image":
            media = kwargs.get(f"🖼️ 图像{media_index}")
            if media is None:
                return ""
            return self._upload_app_bytes(
                api_channel,
                api_key,
                self._tensor_to_png_bytes(media),
                f"rh_app_image_{media_index}.png",
                "image/png",
                timeout,
            )
        if value_type == "video":
            media = kwargs.get(f"🎞️ 视频{media_index}")
            if media is None:
                return ""
            return self._upload_app_bytes(
                api_channel,
                api_key,
                self._video_bytes(media),
                f"rh_app_video_{media_index}.mp4",
                "video/mp4",
                timeout,
            )
        if value_type == "audio":
            media = kwargs.get(f"🎵 音频{media_index}")
            if media is None:
                return ""
            content = self._audio_to_wav_bytes(media)
            if not content:
                raise ValueError(f"无法读取音频输入 {media_index}。")
            return self._upload_app_bytes(
                api_channel,
                api_key,
                content,
                f"rh_app_audio_{media_index}.wav",
                "audio/wav",
                timeout,
            )
        return ""

    @staticmethod
    def _connected_scalar_value(entry, kwargs):
        prefixes = {"text": "📝 文本", "number": "🔢 数字", "boolean": "🔘 布尔"}
        value_type = entry.get("valueType") or "text"
        prefix = prefixes.get(value_type)
        if not prefix:
            return False, None
        input_index = int(entry.get("inputIndex", 0)) + 1
        input_name = f"{prefix}{input_index}"
        return (input_name in kwargs), kwargs.get(input_name)

    def _remote_media_file(self, value, api_channel, api_key, timeout, value_type):
        value = str(value or "").strip().splitlines()[0] if str(value or "").strip() else ""
        if not value:
            return ""
        if not value.startswith(("http://", "https://")) and not os.path.isfile(value):
            return value

        if os.path.isfile(value):
            filename = os.path.basename(value)
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            with open(value, "rb") as file:
                content = file.read()
        else:
            response = requests.get(value, timeout=max(timeout, 120))
            response.raise_for_status()
            filename = os.path.basename(urlparse(value).path) or f"rh_app_{value_type}"
            mime_type = response.headers.get("Content-Type") or mimetypes.guess_type(filename)[0] or "application/octet-stream"
            content = response.content
        return self._upload_app_bytes(api_channel, api_key, content, filename, mime_type, timeout)

    def _build_node_info(self, config, kwargs, api_channel, api_key, timeout, extra_text):
        schema = config.get("schema") if isinstance(config.get("schema"), list) else []
        values = config.get("values") if isinstance(config.get("values"), dict) else {}
        node_info = []
        input_counters = {"image": 0, "video": 0, "audio": 0, "text": 0, "number": 0, "boolean": 0}
        for entry in schema:
            if not isinstance(entry, dict):
                continue
            node_id = str(entry.get("nodeId") or "").strip()
            field_name = str(entry.get("fieldName") or "").strip()
            if not node_id or not field_name:
                continue
            key = self._parameter_key(node_id, field_name)
            value = values.get(key, entry.get("defaultValue", ""))
            value_type = entry.get("valueType") or "text"
            fallback_index = input_counters.get(value_type, 0)
            input_counters[value_type] = fallback_index + 1
            if "inputIndex" not in entry:
                entry = {**entry, "inputIndex": fallback_index}
            if value_type in {"image", "video", "audio"}:
                connected = self._connected_media_file(entry, kwargs, api_channel, api_key, timeout)
                value = connected or self._remote_media_file(value, api_channel, api_key, timeout, value_type)
                if not value:
                    continue
            else:
                connected, connected_value = self._connected_scalar_value(entry, kwargs)
                if connected:
                    value = connected_value
                if value_type == "number" and value not in (None, ""):
                    numeric = float(value)
                    value = int(numeric) if numeric.is_integer() else numeric
                elif value_type == "boolean":
                    value = value is True or str(value).lower() in {"1", "true", "yes", "on"}
                elif value in (None, ""):
                    continue
            node_info.append({"nodeId": node_id, "fieldName": field_name, "fieldValue": value})

        extra = self._load_json(extra_text, [])
        if isinstance(extra, dict):
            extra = extra.get("nodeInfoList") or []
        if not isinstance(extra, list):
            raise ValueError("额外节点参数JSON必须是数组，或包含 nodeInfoList 数组的对象。")

        merged = {(item["nodeId"], item["fieldName"]): item for item in node_info}
        for item in extra:
            if not isinstance(item, dict):
                continue
            node_id = str(item.get("nodeId") or "").strip()
            field_name = str(item.get("fieldName") or "").strip()
            if node_id and field_name:
                merged[(node_id, field_name)] = {
                    "nodeId": node_id,
                    "fieldName": field_name,
                    "fieldValue": item.get("fieldValue", ""),
                }
        return list(merged.values())

    @staticmethod
    def _extract_task_id(data):
        payload = data.get("data")
        if isinstance(payload, dict):
            task_id = payload.get("taskId") or payload.get("task_id")
        else:
            task_id = payload
        return str(task_id or data.get("taskId") or "").strip()

    @staticmethod
    def _failed_reason(data):
        payload = data.get("data")
        if isinstance(payload, dict):
            reason = payload.get("failedReason") or payload.get("failReason") or payload.get("message")
            if isinstance(reason, dict):
                return reason.get("exception_message") or reason.get("message") or json.dumps(reason, ensure_ascii=False)
            if reason:
                return str(reason)
        return str(data.get("msg") or data.get("message") or "Unknown error")

    @classmethod
    def _collect_output_items(cls, value):
        items = []

        def walk(current, inherited_type=""):
            if isinstance(current, list):
                for item in current:
                    walk(item, inherited_type)
                return
            if not isinstance(current, dict):
                return
            output_type = str(current.get("fileType") or current.get("outputType") or current.get("type") or inherited_type).lower()
            for key in URL_KEYS:
                url = current.get(key)
                if isinstance(url, str) and url.startswith(("http://", "https://")):
                    items.append({"url": url, "type": output_type})
                    break
            for key, nested in current.items():
                if key not in URL_KEYS:
                    walk(nested, output_type)

        walk(value)
        deduped = []
        seen = set()
        for item in items:
            if item["url"] not in seen:
                seen.add(item["url"])
                deduped.append(item)
        return deduped

    @staticmethod
    def _media_kind(item):
        output_type = str(item.get("type") or "").lower()
        path = urlparse(item.get("url") or "").path.lower()
        if "video" in output_type or path.endswith((".mp4", ".webm", ".mov", ".m4v")):
            return "video"
        if "audio" in output_type or path.endswith((".mp3", ".wav", ".ogg", ".m4a", ".flac")):
            return "audio"
        if "image" in output_type or path.endswith((".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp")):
            return "image"
        return "unknown"

    @staticmethod
    def _download_image(url, timeout):
        response = requests.get(url, timeout=max(timeout, 120))
        response.raise_for_status()
        return Image.open(io.BytesIO(response.content)).convert("RGB")

    @staticmethod
    def _combine_image_tensors(image_tensors):
        if not image_tensors:
            return create_blank_tensor()
        target_height = int(image_tensors[0].shape[1])
        target_width = int(image_tensors[0].shape[2])
        normalized = []
        for tensor in image_tensors:
            height = int(tensor.shape[1])
            width = int(tensor.shape[2])
            if height == target_height and width == target_width:
                normalized.append(tensor)
                continue

            scale = min(target_width / width, target_height / height)
            resized_height = max(1, min(target_height, round(height * scale)))
            resized_width = max(1, min(target_width, round(width * scale)))
            resized = F.interpolate(
                tensor.permute(0, 3, 1, 2),
                size=(resized_height, resized_width),
                mode="bicubic",
                align_corners=False,
            ).permute(0, 2, 3, 1).clamp(0, 1)
            canvas = torch.zeros(
                (resized.shape[0], target_height, target_width, resized.shape[3]),
                dtype=resized.dtype,
                device=resized.device,
            )
            top = (target_height - resized_height) // 2
            left = (target_width - resized_width) // 2
            canvas[:, top:top + resized_height, left:left + resized_width, :] = resized
            normalized.append(canvas)
        return torch.cat(normalized, dim=0)

    def _poll_outputs(self, api_channel, api_key, task_id, max_seconds, interval, timeout):
        started = time.time()
        while time.time() - started < max_seconds:
            time.sleep(interval)
            data = _request_json(
                "POST",
                f"{_base_url(api_channel)}/task/openapi/outputs",
                api_key,
                api_channel,
                timeout=timeout,
                payload={"apiKey": api_key, "taskId": task_id},
            )
            code = str(data.get("code", ""))
            if code == "0":
                return data
            if code in RUNNING_CODES:
                continue
            if code in FAILED_CODES:
                raise RuntimeError(f"RunningHub 应用任务失败 805：{self._failed_reason(data)}")
            _raise_api_error(code, data.get("msg") or data.get("message") or data, api_channel)
        raise RuntimeError(f"RunningHub 应用任务超过 {max_seconds} 秒仍未完成，任务ID：{task_id}")

    def run_app(self, **kwargs):
        api_channel = str(kwargs.get("🌐 API渠道", "国内版") or "国内版").strip()
        api_key = str(kwargs.get("🔑 API密钥", "") or "").strip()
        webapp_id = str(kwargs.get("🆔 应用ID", "") or "").strip()
        instance_type = str(kwargs.get("⚙️ 实例类型", "默认") or "默认")
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 2400))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        skip_error = bool(kwargs.get("🚫 出错时跳过", False))
        submit_response = {}
        final_response = {}

        try:
            if not api_key:
                raise ValueError("请填写 RunningHub API密钥。")
            if not webapp_id:
                raise ValueError("请填写 RunningHub 应用ID。")

            config = self._load_json(kwargs.get("🧩 应用参数JSON", "{}"), {})
            if (
                not isinstance(config, dict)
                or str(config.get("webappId") or "") != webapp_id
                or str(config.get("apiChannel") or "") != api_channel
                or not isinstance(config.get("schema"), list)
            ):
                schema = fetch_rh_app_schema(api_channel, api_key, webapp_id, timeout=min(timeout, 60))
                config = {**schema, "values": {}}

            node_info = self._build_node_info(
                config,
                kwargs,
                api_channel,
                api_key,
                timeout,
                kwargs.get("📋 额外节点参数JSON", "[]"),
            )
            payload = {
                "apiKey": api_key,
                "webappId": webapp_id,
                "nodeInfoList": node_info,
                "taskType": "ASYNC",
            }
            if instance_type != "默认":
                payload["instanceType"] = instance_type

            _log_info(f"开始运行：{api_channel} / {config.get('appName') or webapp_id} / 参数 {len(node_info)} 个")
            submit_response = _request_json(
                "POST",
                f"{_base_url(api_channel)}/task/openapi/ai-app/run",
                api_key,
                api_channel,
                timeout=timeout,
                payload=payload,
            )
            submit_code = str(submit_response.get("code", "0"))
            if submit_code != "0":
                _raise_api_error(
                    submit_code,
                    submit_response.get("msg") or submit_response.get("message") or submit_response,
                    api_channel,
                )
            task_id = self._extract_task_id(submit_response)
            if not task_id:
                raise RuntimeError(f"RunningHub 应用提交成功但没有返回 taskId：{json.dumps(submit_response, ensure_ascii=False)[:800]}")

            final_response = self._poll_outputs(
                api_channel,
                api_key,
                task_id,
                max_seconds,
                interval,
                timeout,
            )
            output_items = self._collect_output_items(final_response.get("data"))
            if not output_items:
                raise RuntimeError(f"RunningHub 应用任务完成但没有返回输出 URL：{json.dumps(final_response, ensure_ascii=False)[:1200]}")

            image_tensors = []
            video_url = ""
            for item in output_items:
                kind = self._media_kind(item)
                if kind == "image":
                    try:
                        image_tensors.append(pil2tensor(self._download_image(item["url"], timeout)))
                    except Exception as error:
                        _log_error(f"图片下载失败，保留 URL 输出：{error}")
                elif kind == "video" and not video_url:
                    video_url = item["url"]

            images = self._combine_image_tensors(image_tensors)
            urls = [item["url"] for item in output_items]
            info_lines = [
                "✅ RH 应用任务完成",
                f"🌐 API渠道：{api_channel}",
                f"🪲 应用：{config.get('appName') or webapp_id}",
                f"🆔 应用ID：{webapp_id}",
                f"⚙️ 实例类型：{instance_type}",
                f"🧩 提交参数：{len(node_info)} 个",
                f"🆔 任务ID：{task_id}",
                f"📦 输出数量：{len(urls)}",
            ]
            raw = json.dumps(
                {
                    "nodeInfoList": node_info,
                    "submit": submit_response,
                    "final": final_response,
                },
                ensure_ascii=False,
                indent=2,
            )
            return (images, RHSeedanceVideoAdapter(video_url), task_id, "\n".join(urls), "\n".join(info_lines) + "\n\n" + raw)
        except Exception as error:
            message = f"❌ 错误：RH 应用运行失败\n\n详情：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            if skip_error:
                return self._blank_result(message)
            return self._blank_result(message)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHAppNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🪲RH应用@炮老师的小课堂",
}
