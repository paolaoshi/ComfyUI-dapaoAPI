"""Independent Seedance 2.0 video node for the dapaoAI relay.

The node submits stable dapaoAI mapping IDs. Resolution remains a separate
request parameter and is not encoded into the model name.
"""

import asyncio
import io
import json
import os
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
MODEL_ID = "SD2-face"
STANDARD_UPSTREAM_MODEL = "SD2.0-mini"
FAST_UPSTREAM_MODEL = "SD2-fast"
MODEL_OPTIONS = [MODEL_ID, STANDARD_UPSTREAM_MODEL, FAST_UPSTREAM_MODEL]
UPSTREAM_REFERENCE_MODEL = "seedance-2.0-face"
MODE_OPTIONS = ["文生视频", "图生视频", "首尾帧生视频", "多模态参考"]
DURATION_OPTIONS = [str(value) for value in range(4, 16)]
ASPECT_RATIO_OPTIONS = ["16:9", "9:16"]
RESOLUTION_OPTIONS = ["720P"]
MAX_IMAGE_REFERENCES = 9
MAX_VIDEO_REFERENCES = 3
MAX_AUDIO_REFERENCES = 3
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MAX_VIDEO_BYTES = 60 * 1024 * 1024
MAX_AUDIO_BYTES = 50 * 1024 * 1024


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
        }
        normalized = self.api_message.lower()
        if "insufficient_user_quota" in normalized or "insufficient quota" in normalized or "预扣费额度" in self.api_message:
            label = "上游余额不足"
            hint = "（土豆上游预扣费失败；请充值上游账户，或降低时长/切换可用渠道后重试）"
        elif "did not provide a seconds billing multiplier" in normalized:
            label = "中转站按秒计费适配器配置错误"
            hint = "（服务端任务适配器未返回 seconds 计费倍率；节点已提交 duration 和 seconds，需修复中转站适配器或计费配置）"
        elif "model name not specified" in self.api_message.lower() or "model name cannot be empty" in self.api_message.lower():
            label = "中转站模型映射为空"
            hint = "（节点已发送模型字段；请在 dapaoAI 的视频路由中检查 SD2-face、SD2.0-mini、SD2-fast 的目标模型是否为空或未绑定可用渠道）"
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
    if not value.startswith(("http://", "https://")):
        raise ValueError(f"{label}必须是公网 HTTP/HTTPS URL，不能使用本地路径、localhost 或 data URI。")
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
    for layer in _response_layers(result):
        value = layer.get("task_id") or layer.get("id")
        if isinstance(value, (str, int)) and str(value):
            return str(value)
    return ""


def _task_state(result):
    statuses = []
    progress = None
    message = ""
    for layer in _response_layers(result):
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
    if any(status in {"failed", "failure", "error", "cancelled", "canceled", "rejected"} for status in statuses):
        return "failed", progress, message
    if any(status in {"completed", "complete", "succeeded", "success", "done"} for status in statuses):
        return "completed", progress, message
    if any(status in {"submitted", "processing", "pending", "queued", "running", "in_progress"} for status in statuses):
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

    def __init__(self, video_url="", width=1280, height=720):
        self.video_url = video_url or ""
        self.width = max(1, int(width))
        self.height = max(1, int(height))

    def get_dimensions(self):
        return self.width, self.height

    def save_to(self, output_path, format="auto", codec="auto", metadata=None, **kwargs):
        # ComfyUI 不同版本的保存节点可能额外传入 crf、fps、bitrate 等参数；
        # 远端视频已经编码完成，这些参数只需兼容接收，不应改变下载内容。
        if not self.video_url:
            return False
        response = requests.get(self.video_url, stream=True, timeout=300, allow_redirects=True)
        response.raise_for_status()
        with open(output_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return True


class DapaoSeedanceRelayClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout
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
            response = requests.request(method, url, headers=self._headers(), timeout=self.timeout, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as error:
            if method.upper() == "POST":
                raise RuntimeError(f"{friendly_network_error(error, '提交视频任务')} 视频提交不会自动重试，以免重复扣费。") from error
            raise RuntimeError(friendly_network_error(error, '查询视频任务')) from error
        if response.status_code >= 400:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status())
            raise DapaoSeedanceAPIError(response.status_code, _response_error(response))
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站返回内容不是 JSON：{response.text[:500]}") from error

    def upload_file(self, content, filename, mime_type, model_name):
        """Upload a reference and require a public URL for Seedance to fetch.

        Seedance's upstream worker runs outside the user's ComfyUI machine, so
        local paths and data URIs cannot be used as references.  dapaoAI
        deployments using the asset upload route return a public URL in the
        response envelope; deployments returning only a
        private file id are rejected with an actionable message.
        """
        if not isinstance(content, (bytes, bytearray)) or not content:
            raise ValueError(f"{filename}内容为空，无法上传。")
        media_limit = {
            "image": (MAX_IMAGE_BYTES, "图片"),
            "video": (MAX_VIDEO_BYTES, "视频"),
            "audio": (MAX_AUDIO_BYTES, "音频"),
        }.get(str(mime_type).split("/", 1)[0])
        if media_limit and len(content) > media_limit[0]:
            raise ValueError(f"{media_limit[1]}素材超过上传上限 {media_limit[0] // 1024 // 1024}MB，请压缩后重试。")
        model_name = str(model_name or "").strip()
        if not model_name:
            raise ValueError("素材上传缺少模型ID，无法选择上传通道。")
        # dapaoAI's file relay needs a model to select the backing channel.
        # Multipart parsers differ across relay versions, so provide the same
        # model in both the query string and form body.
        url = f"{self.base_url}/v1/files"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "ComfyUI-dapaoAPI/Seedance20Allround",
        }
        try:
            response = requests.post(
                url,
                headers=headers,
                params={"model": model_name},
                files={"file": (filename, bytes(content), mime_type)},
                data={"model": model_name, "purpose": "user_data"},
                timeout=max(self.timeout, 120),
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RuntimeError(friendly_network_error(error, "上传视频参考素材")) from error
        if response.status_code >= 400:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status())
            raise RuntimeError(
                f"中转站素材上传接口 /v1/files（model={model_name}）失败 {response.status_code}：{_response_error(response)}。"
                "此错误发生在视频提交前，不代表 SD2-face、SD2.0-mini、SD2-fast 模型映射失败。"
            )
        try:
            result = response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站素材上传返回内容不是 JSON：{response.text[:500]}") from error
        public_url = _extract_public_url(result)
        if not public_url:
            raise RuntimeError(
                "中转站素材上传接口未返回公网 URL。Seedance 上游不能读取私有 file_id；"
                "请在节点的“🌐 公网素材URL(JSON)”中填写可公网访问的 http(s) 地址，"
                "或让 dapaoAI 的素材上传接口返回可公网访问的 url。"
            )
        return public_url

    def submit(self, payload):
        # dapaoAI 视频接口使用单数 video 路由；上游土豆文档的 videos 路由不能直接照搬。
        return self._request_json("POST", "/v1/video/generations", json=payload)

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
                raise RuntimeError(f"视频任务失败：{message or json.dumps(_sanitized_result(result), ensure_ascii=False)[:1000]}")
            if progress_bar:
                elapsed = time.monotonic() - started
                current = min(95, int(progress)) if progress is not None else min(95, int(elapsed / max_seconds * 95))
                progress_bar.update_absolute(current)
            time.sleep(interval)
        raise RuntimeError(f"视频任务超过 {max_seconds} 秒仍未完成。")


class DapaoSeedance20AllroundVideoNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "首尾帧模式的首图，将作为 images[0] 提交。"}),
            "🏁 尾帧图": ("IMAGE", {"tooltip": "首尾帧模式的尾图，将排在首图之后作为多图参考提交。"}),
            "🌐 公网素材URL(JSON)": (
                "STRING",
                {
                    "multiline": True,
                    "default": "{}",
                    "tooltip": "可选：填写公网素材地址，格式 {\"images\":[],\"videos\":[],\"audios\":[]}。上游只接受 http(s)，不能填本地路径或 data URI。",
                },
            ),
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1800, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 30, "max": 600, "step": 10}),
        }
        for index in range(1, MAX_IMAGE_REFERENCES + 1):
            optional[f"🖼️ 参考图{index}"] = ("IMAGE", {"tooltip": f"多图参考，第{index}路，最多{MAX_IMAGE_REFERENCES}张。"})
        for index in range(1, MAX_VIDEO_REFERENCES + 1):
            optional[f"🎞️ 参考视频{index}"] = (IO.VIDEO, {"tooltip": "多模态参考视频。"})
        for index in range(1, MAX_AUDIO_REFERENCES + 1):
            optional[f"🎵 参考音频{index}"] = ("AUDIO", {"tooltip": "多模态参考音频，不能单独使用。"})
        return {
            "required": {
                "🔑 API密钥": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "填入 dapaoAI API 密钥",
                        "tooltip": "密钥只用于请求 https://api.dapaoai.com，不会写入配置文件。",
                    },
                ),
                "🤖 模型": (MODEL_OPTIONS, {"default": MODEL_ID}),
                "🎛️ 生成模式": (MODE_OPTIONS, {"default": "文生视频"}),
                "📝 提示词": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "电影感镜头缓慢推进，主体动作自然，光影细腻，画面稳定且细节丰富",
                    },
                ),
                "🧩 分辨率": (
                    RESOLUTION_OPTIONS,
                    {"default": "720P", "tooltip": "当前暂时只开放 720P。"},
                ),
                "👤 真人模式": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "开启时切换到 SD2-face；关闭时默认切换到 SD2.0-mini。直接选择 SD2.0-mini 或 SD2-fast 时会自动关闭。"},
                ),
                "⏱️ 时长(秒)": (DURATION_OPTIONS, {"default": "5"}),
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
            },
            "optional": optional,
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "Seedance2.0 文生视频、多图参考、首尾参考、多模态参考；参考素材统一使用公网 HTTP/HTTPS URL"

    @staticmethod
    def _collect_image_parts(kwargs, limit=MAX_IMAGE_REFERENCES):
        image_parts = []
        for index in range(1, MAX_IMAGE_REFERENCES + 1):
            image = kwargs.get(f"🖼️ 参考图{index}")
            if image is None:
                continue
            for content in _tensor_to_png_bytes(image):
                if len(image_parts) >= limit:
                    return image_parts
                image_parts.append((content, f"seedance_reference_{index}_{len(image_parts) + 1}.png", "image/png"))
        return image_parts

    @staticmethod
    def _collect_video_parts(kwargs):
        parts = []
        for index in range(1, MAX_VIDEO_REFERENCES + 1):
            video = kwargs.get(f"🎞️ 参考视频{index}")
            if video is not None:
                content = _video_to_bytes(video)
                if len(content) > MAX_VIDEO_BYTES:
                    raise ValueError(f"参考视频{index}超过本节点 {MAX_VIDEO_BYTES // 1024 // 1024}MB 的安全上限，请先压缩。")
                parts.append((content, f"seedance_reference_video_{index}.mp4", "video/mp4"))
        return parts

    @staticmethod
    def _collect_audio_parts(kwargs):
        parts = []
        for index in range(1, MAX_AUDIO_REFERENCES + 1):
            audio = kwargs.get(f"🎵 参考音频{index}")
            if audio is not None:
                content = _audio_to_wav_bytes(audio)
                if len(content) > MAX_AUDIO_BYTES:
                    raise ValueError(f"参考音频{index}超过本节点 {MAX_AUDIO_BYTES // 1024 // 1024}MB 的安全上限，请先压缩。")
                parts.append((content, f"seedance_reference_audio_{index}.wav", "audio/wav"))
        return parts

    @staticmethod
    def _frame_parts(kwargs):
        first = kwargs.get("🎬 首帧图")
        last = kwargs.get("🏁 尾帧图")
        result = []
        if first is not None:
            result.extend((content, "seedance_first_frame.png", "image/png") for content in _tensor_to_png_bytes(first))
        if last is not None:
            result.extend((content, "seedance_last_frame.png", "image/png") for content in _tensor_to_png_bytes(last))
        return result[:MAX_IMAGE_REFERENCES]

    @staticmethod
    def _public_url_overrides(value):
        data = _parse_extra_json(value)
        result = {}
        for key in ("images", "videos", "audios"):
            raw = data.get(key, [])
            if isinstance(raw, str):
                raw = [raw] if raw.strip() else []
            if not isinstance(raw, list):
                raise ValueError(f"公网素材URL JSON 的 {key} 必须是 URL 数组。")
            limit = {"images": MAX_IMAGE_REFERENCES, "videos": MAX_VIDEO_REFERENCES, "audios": MAX_AUDIO_REFERENCES}[key]
            if len(raw) > limit:
                raise ValueError(f"公网素材URL.{key}最多 {limit} 个。")
            result[key] = [_validate_public_url(item, f"公网素材URL.{key}") for item in raw]
        return result

    @staticmethod
    def _select_request_model(model_id):
        """Return the exact dapaoAI mapping selected by the user."""
        if model_id not in MODEL_OPTIONS:
            raise ValueError(f"未知界面模型：{model_id}")
        return model_id

    @staticmethod
    def _expected_dimensions(resolution_label, aspect_ratio):
        """Return the expected encoded dimensions for downstream VIDEO nodes."""
        long_side = 1280
        if aspect_ratio == "9:16":
            return round(long_side * 9 / 16), long_side
        return long_side, round(long_side * 9 / 16)

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_id = str(kwargs.get("🤖 模型") or "").strip()
        mode = kwargs.get("🎛️ 生成模式", "文生视频")
        prompt = (kwargs.get("📝 提示词") or "").strip()
        resolution_label = kwargs.get("🧩 分辨率", "720P")
        face_mode = bool(kwargs.get("👤 真人模式", True))
        # Older saved workflows can deserialize a newly added combo widget as
        # an empty string. Resolve that state locally before validation.
        if not model_id:
            model_id = MODEL_ID if face_mode else STANDARD_UPSTREAM_MODEL
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

        try:
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_id not in MODEL_OPTIONS:
                raise ValueError(f"未知界面模型：{model_id}")
            if mode not in MODE_OPTIONS:
                raise ValueError(f"不支持的生成模式：{mode}")
            if not prompt:
                raise ValueError("提示词不能为空。")
            if resolution_label not in RESOLUTION_OPTIONS:
                raise ValueError("当前分辨率仅支持 720P。")
            # The model selector is authoritative; face mode is a convenience
            # control and status indicator for the dedicated face mapping.
            face_mode = model_id == MODEL_ID
            request_model = self._select_request_model(model_id)
            if duration not in range(4, 16):
                raise ValueError("时长仅支持 4–15 秒。")
            if aspect_ratio not in ASPECT_RATIO_OPTIONS:
                raise ValueError("视频比例仅支持 16:9 或 9:16。")
            overrides = self._public_url_overrides(kwargs.get("🌐 公网素材URL(JSON)", "{}"))

            image_parts = []
            video_parts = []
            audio_parts = []
            if mode == "图生视频":
                image_parts = self._collect_image_parts(kwargs)
                if not image_parts and not overrides["images"]:
                    raise ValueError("图生视频至少需要接入一张参考图。")
            elif mode == "首尾帧生视频":
                image_parts = self._frame_parts(kwargs)
                if not image_parts and not overrides["images"]:
                    raise ValueError("首尾帧生视频至少需要接入首帧图。")
            elif mode == "多模态参考":
                image_parts = self._collect_image_parts(kwargs)
                video_parts = self._collect_video_parts(kwargs)
                audio_parts = self._collect_audio_parts(kwargs)
                if not image_parts and not video_parts and not overrides["images"] and not overrides["videos"]:
                    raise ValueError("多模态参考至少需要一张参考图或一个参考视频。")
                if audio_parts and not image_parts and not video_parts and not overrides["images"] and not overrides["videos"]:
                    raise ValueError("参考音频不能单独使用，需同时接入参考图或参考视频。")

            client = DapaoSeedanceRelayClient(api_key, timeout)
            stage = "media_upload"
            # Explicit public URLs are useful when a deployment does not expose
            # /v1/assets/uploads, and always take precedence over local tensors.
            image_uris = list(overrides["images"])
            video_uris = list(overrides["videos"])
            audio_uris = list(overrides["audios"])
            if not image_uris and image_parts:
                image_uris = [client.upload_file(content, filename, mime_type, request_model) for content, filename, mime_type in image_parts]
            if not video_uris and video_parts:
                video_uris = [client.upload_file(content, filename, mime_type, request_model) for content, filename, mime_type in video_parts]
            if not audio_uris and audio_parts:
                audio_uris = [client.upload_file(content, filename, mime_type, request_model) for content, filename, mime_type in audio_parts]
            if mode == "图生视频" and not image_uris:
                raise ValueError("图生视频至少需要一张公网参考图。")
            if mode == "首尾帧生视频" and not image_uris:
                raise ValueError("首尾帧生视频至少需要一张公网首帧图。")
            if mode == "多模态参考" and not image_uris and not video_uris:
                raise ValueError("多模态参考至少需要一张公网参考图或一个公网参考视频。")
            for ref_key, refs in (("images", image_uris), ("videos", video_uris), ("audios", audio_uris)):
                for ref in refs:
                    _validate_public_url(ref, f"{ref_key} 参考素材")

            payload = {
                # Submit one of the two real upstream model IDs. Resolution
                # remains a separate request parameter. dapaoAI's per-second
                # billing layer reads ``seconds`` while the Tudou upstream
                # protocol reads integer ``duration``, so provide both with
                # the same bounded value.
                "model": request_model,
                "prompt": prompt,
                "duration": duration,
                "seconds": str(duration),
                "aspect_ratio": aspect_ratio,
                "resolution": resolution_label.lower(),
                "generate_audio": bool(kwargs.get("🔊 生成音频", True)),
            }
            if image_uris:
                payload["images"] = image_uris
            if video_uris:
                payload["videos"] = video_uris
            if audio_uris:
                payload["audios"] = audio_uris
            extra = _parse_extra_json(kwargs.get("📋 额外参数JSON", "{}"))
            protected = {
                "model", "prompt", "duration", "seconds", "aspect_ratio", "resolution",
                "images", "videos", "audios", "generate_audio",
            }
            conflicts = sorted(set(extra).intersection(protected))
            if conflicts:
                raise ValueError(f"额外参数JSON不能覆盖节点核心参数：{', '.join(conflicts)}")
            payload.update(extra)

            _log_info(
                f"提交任务：relay={API_BASE_URL}，model={model_id}，实际model={request_model}，"
                f"mode={mode}，真人模式={face_mode}，duration={duration}，aspect_ratio={aspect_ratio}，"
                f"resolution={resolution_label.lower()}，billing_seconds={payload['seconds']}，"
                f"audio={payload['generate_audio']}，图={len(image_uris)}，视频={len(video_uris)}，音频={len(audio_uris)}"
            )
            started = time.time()
            stage = "video_submit"
            submitted = client.submit(payload)
            task_identifier = _task_id(submitted)
            if not task_identifier:
                raise RuntimeError(f"提交成功但没有返回任务ID：{json.dumps(_sanitized_result(submitted), ensure_ascii=False)[:1200]}")
            final = client.poll(task_identifier, max_seconds, interval)
            video_url = _extract_video_url(final)
            if not video_url:
                raise RuntimeError(f"任务完成但没有找到视频URL：{json.dumps(_sanitized_result(final), ensure_ascii=False)[:1600]}")
            if face_mode:
                parameter_profile = "SD2-face（720P真人版）"
            else:
                parameter_profile = f"{request_model}（720P）"
            info = (
                "✅ Seedance2.0 全能视频任务完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 模型ID：{model_id}\n"
                f"🔎 实际请求模型：{request_model}\n"
                f"🔎 参数档位：{parameter_profile}\n"
                f"🎛️ 模式：{mode}\n"
                f"⏱️ 时长：{duration} 秒\n"
                f"📐 比例：{aspect_ratio}\n"
                f"🧩 分辨率：{resolution_label}\n"
                f"👤 真人模式：{face_mode}\n"
                f"🔊 生成音频：{payload['generate_audio']}\n"
                f"💰 预计价格：¥{duration * 0.48:.2f}\n"
                f"🖼️ 参考图：{len(image_uris)} 张\n"
                f"🎞️ 参考视频：{len(video_uris)} 个\n"
                f"🎵 参考音频：{len(audio_uris)} 个\n"
                f"🆔 任务ID：{task_identifier}\n"
                f"🔗 视频URL：{video_url}\n"
                f"⏱️ 耗时：{time.time() - started:.2f} 秒\n\n"
                + json.dumps({"submit": _sanitized_result(submitted), "final": _sanitized_result(final)}, ensure_ascii=False, indent=2)
            )
            width, height = self._expected_dimensions(resolution_label, aspect_ratio)
            return DapaoVideoAdapter(video_url, width, height), task_identifier, info, video_url
        except Exception as error:
            message = f"❌ Seedance2.0 全能视频生成失败：{error}"
            if request_model:
                message += f"\n（节点实际发送 model={request_model}）"
            _log_error(message)
            _log_error(traceback.format_exc())
            details = json.dumps(
                {
                    "request_model": request_model,
                    "payload_model": payload.get("model") if isinstance(payload, dict) else "",
                    "stage": stage,
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
