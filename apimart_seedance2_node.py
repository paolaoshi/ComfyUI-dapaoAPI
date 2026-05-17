import base64
import io
import json
import os
import re
import tempfile
import time
import traceback
import wave

import numpy as np
import requests
import torch
from PIL import Image

try:
    import comfy.utils
    from comfy.comfy_types import IO
except Exception:
    comfy = None

    class IO:
        VIDEO = "VIDEO"


NODE_CATEGORY = "🤖dapaoAPI/🐦‍🔥GPT&gemini&即梦最新稳定🐦‍🔥"


class APImartSeedanceVideoAdapter:
    def __init__(self, video_url):
        self.video_url = video_url or ""

    def get_dimensions(self):
        return 1280, 720

    def save_to(self, output_path, format="auto", codec="auto", metadata=None):
        response = requests.get(self.video_url, stream=True, timeout=300, allow_redirects=True)
        response.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)
        return True


def _blank_image_tensor():
    return torch.zeros((1, 1, 1, 3), dtype=torch.float32)


def _tensor_to_data_uri(image):
    image_np = np.clip(image[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
    pil_image = Image.fromarray(image_np).convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")


def _audio_tensor_to_wav_bytes(waveform, sample_rate):
    if hasattr(waveform, "cpu"):
        waveform = waveform.cpu().numpy()
    waveform = np.asarray(waveform)
    waveform = np.squeeze(waveform)
    if waveform.ndim == 1:
        waveform = waveform.reshape(-1, 1)
    elif waveform.ndim == 2 and waveform.shape[0] < waveform.shape[1]:
        waveform = waveform.T
    elif waveform.ndim > 2:
        waveform = waveform.reshape(-1, 1)

    if np.issubdtype(waveform.dtype, np.floating):
        waveform = np.clip(waveform, -1.0, 1.0)
        pcm = (waveform * 32767.0).astype(np.int16)
    else:
        pcm = waveform.astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(int(pcm.shape[1]))
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(pcm.tobytes())
    return buffer.getvalue()


def _audio_input_to_data_uri(audio_input):
    if not audio_input:
        return ""
    if isinstance(audio_input, str):
        return _asset_id_to_url(audio_input)
    if isinstance(audio_input, dict):
        waveform = audio_input.get("waveform")
        sample_rate = audio_input.get("sample_rate") or audio_input.get("sampler_rate") or 44100
        if waveform is None:
            return ""
        wav_bytes = _audio_tensor_to_wav_bytes(waveform, int(sample_rate))
        return "data:audio/wav;base64," + base64.b64encode(wav_bytes).decode("utf-8")
    return ""


def _video_input_to_data_uri(video_input):
    if not video_input:
        return ""
    if isinstance(video_input, str):
        return _asset_id_to_url(video_input)
    temp_path = os.path.join(tempfile.gettempdir(), f"dapao_apimart_seedance2_{int(time.time() * 1000)}.mp4")
    try:
        if hasattr(video_input, "save_to"):
            video_input.save_to(temp_path)
            with open(temp_path, "rb") as f:
                raw = f.read()
            return "data:video/mp4;base64," + base64.b64encode(raw).decode("utf-8")
        return ""
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


def _safe_json_loads(text):
    if not text or not str(text).strip():
        return {}
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _asset_id_to_url(value):
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://", "asset://", "data:")):
        return value
    return f"asset://{value}"


def _split_string_items(value):
    if not value:
        return []
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = str(value).replace("\n", ",").split(",")
    return [_asset_id_to_url(item) for item in raw_items if _asset_id_to_url(str(item))]


def _get_base_url(custom_api_url):
    base_url = (custom_api_url or "").strip() or "https://api.apimart.ai"
    return base_url.rstrip("/")


def _headers(api_key, user_agent="ComfyUI-dapaoAPI/APImartSeedance2"):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": user_agent,
    }


def _error_message(response):
    text = response.text[:1000]
    try:
        data = response.json()
        error = data.get("error", {}) if isinstance(data, dict) else {}
        if isinstance(error, dict):
            return error.get("message") or error.get("code") or error.get("type") or text
        if isinstance(data, dict):
            return data.get("message") or data.get("msg") or text
    except Exception:
        pass
    return text


def _raise_for_response(response, label="APImart 即梦2.0"):
    if response.status_code == 200:
        return
    message = _error_message(response)
    status = response.status_code
    lower_message = str(message).lower()
    if status == 400:
        if "data:" in lower_message or "base64" in lower_message or "url" in lower_message:
            raise RuntimeError(f"{label} 参数错误 400：平台可能不接受本地素材 data URI，请改用公网可访问素材 URL。接口返回：{message}")
        raise RuntimeError(f"{label} 参数错误 400：请检查模型、提示词、素材、比例、分辨率或时长。接口返回：{message}")
    if status == 401:
        raise RuntimeError(f"{label} 认证失败 401：API密钥无效或未填写正确。接口返回：{message}")
    if status == 402:
        raise RuntimeError(f"{label} 余额不足 402：账户余额不足，请充值后再试。接口返回：{message}")
    if status == 403:
        if "quota_not_enough" in lower_message or "insufficient balance" in lower_message:
            raise RuntimeError(f"{label} 余额不足 403：账户余额不足，请充值后再试。接口返回：{message}")
        raise RuntimeError(f"{label} 权限不足 403：没有权限访问该模型或资源。接口返回：{message}")
    if status == 413:
        raise RuntimeError(f"{label} 素材过大 413：本地素材转 base64 后过大，请改用公网可访问素材 URL。接口返回：{message}")
    if status == 429:
        raise RuntimeError(f"{label} 请求过频 429：请降低频率后重试。接口返回：{message}")
    if status >= 500:
        raise RuntimeError(f"{label} 服务异常 {status}：服务器或上游暂时不可用。接口返回：{message}")
    raise RuntimeError(f"{label} 请求失败 {status}：{message}")


def _raise_for_api_result(result, label="APImart 即梦2.0"):
    if not isinstance(result, dict):
        return
    code = result.get("code")
    if code in (None, 0, 200, "0", "200"):
        return
    error = result.get("error")
    if isinstance(error, dict):
        message = error.get("message") or error.get("code") or json.dumps(error, ensure_ascii=False)
    else:
        message = result.get("message") or result.get("msg") or json.dumps(result, ensure_ascii=False)[:1000]
    lower_message = str(message).lower()
    if code in (402, "402") or "quota_not_enough" in lower_message or "insufficient balance" in lower_message:
        raise RuntimeError(f"{label} 余额不足：账户余额不足，请充值后再试。接口返回：{message}")
    if code in (401, "401"):
        raise RuntimeError(f"{label} 认证失败：API密钥无效或未填写正确。接口返回：{message}")
    if code in (429, "429"):
        raise RuntimeError(f"{label} 请求过频：请降低频率后重试。接口返回：{message}")
    if "data:" in lower_message or "base64" in lower_message:
        raise RuntimeError(f"{label} 平台拒绝本地素材 data URI：请改用公网可访问素材 URL。接口返回：{message}")
    raise RuntimeError(f"{label} 接口返回错误 code={code}：{message}")


def _should_retry(exc):
    if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
        return True
    text = str(exc)
    return "429" in text or "服务异常" in text or "暂时不可用" in text


def _request_json_with_retry(method, url, headers, payload=None, timeout=180, retry_count=2, label="APImart 即梦2.0"):
    last_error = None
    for attempt in range(retry_count + 1):
        try:
            if method == "POST":
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            else:
                response = requests.get(url, headers=headers, timeout=timeout)
            _raise_for_response(response, label)
            result = response.json()
            _raise_for_api_result(result, label)
            return result
        except json.JSONDecodeError as e:
            raise RuntimeError(f"{label} 接口返回内容不是 JSON：{e}")
        except Exception as e:
            last_error = e
            if attempt >= retry_count or not _should_retry(e):
                raise
            time.sleep(min(2 ** attempt, 8))
    raise last_error


def _extract_task_id(result):
    if not isinstance(result, dict):
        return ""
    data = result.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return first.get("task_id") or first.get("id") or ""
    if isinstance(data, dict):
        return data.get("task_id") or data.get("id") or ""
    return result.get("task_id") or result.get("id") or ""


def _task_status(task_result):
    data = task_result.get("data", {}) if isinstance(task_result, dict) else {}
    if isinstance(data, dict):
        return data.get("status", ""), data.get("progress", 0), data.get("error") or data.get("message") or ""
    return "", 0, ""


def _poll_task(base_url, task_id, headers, timeout, retry_count, max_poll_attempts, poll_interval, label="APImart 即梦2.0", allow_failed_result=False):
    task_url = f"{base_url}/v1/tasks/{task_id}"
    pbar = comfy.utils.ProgressBar(100) if comfy is not None else None
    if pbar:
        pbar.update_absolute(5)

    last_result = None
    for _ in range(1, max_poll_attempts + 1):
        time.sleep(poll_interval)
        task_result = _request_json_with_retry("GET", task_url, headers, None, timeout, retry_count, label)
        last_result = task_result
        status, progress, error = _task_status(task_result)
        normalized_status = str(status).lower()
        if pbar:
            try:
                pbar.update_absolute(min(95, int(progress or 0)))
            except Exception:
                pass

        if normalized_status in ("completed", "success", "succeeded"):
            if pbar:
                pbar.update_absolute(100)
            return task_result
        if normalized_status in ("failed", "failure"):
            if allow_failed_result:
                if pbar:
                    pbar.update_absolute(100)
                return task_result
            raise RuntimeError(f"{label} 任务失败：{error or json.dumps(task_result, ensure_ascii=False)[:1000]}")

    raise RuntimeError(f"{label} 轮询超过 {max_poll_attempts} 次仍未完成，请稍后用任务ID查询：{task_id}。最后返回：{json.dumps(last_result, ensure_ascii=False)[:1000]}")


def _walk_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_values(item)
    else:
        yield value


def _extract_video_url(task_result):
    if not isinstance(task_result, dict):
        return ""
    candidates = []
    data = task_result.get("data", {})
    result = data.get("result", {}) if isinstance(data, dict) else {}
    for container in (result, data, task_result):
        if not isinstance(container, dict):
            continue
        for key in ("video_url", "videoUrl", "url"):
            value = container.get(key)
            if isinstance(value, str) and value:
                candidates.append(value)
        video_urls = container.get("video_urls") or container.get("videos")
        if isinstance(video_urls, list):
            for item in video_urls:
                if isinstance(item, str):
                    candidates.append(item)
                elif isinstance(item, dict):
                    value = item.get("url") or item.get("video_url")
                    if isinstance(value, str) and value:
                        candidates.append(value)
    for candidate in candidates:
        if candidate:
            return candidate

    raw = json.dumps(task_result, ensure_ascii=False)
    match = re.search(r"https?://[^\s<>\"']+\.mp4[^\s<>\"']*", raw)
    return match.group(0) if match else ""


def _extract_last_frame_url(task_result):
    if not isinstance(task_result, dict):
        return ""
    data = task_result.get("data", {})
    result = data.get("result", {}) if isinstance(data, dict) else {}
    for container in (result, data, task_result):
        if not isinstance(container, dict):
            continue
        for key in ("last_frame_url", "lastFrameUrl", "last_frame_image_url", "last_frame_image", "last_frame"):
            value = container.get(key)
            if isinstance(value, str) and value:
                return value
        images = container.get("images")
        if isinstance(images, list):
            for item in images:
                if isinstance(item, dict) and str(item.get("role", "")).lower() in ("last_frame", "lastframe"):
                    value = item.get("url") or item.get("image_url")
                    if isinstance(value, str) and value:
                        return value
    return ""


def _download_image_to_tensor(url, timeout):
    if not url:
        return _blank_image_tensor()
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    pil_image = Image.open(io.BytesIO(response.content)).convert("RGB")
    np_image = np.array(pil_image).astype(np.float32) / 255.0
    return torch.from_numpy(np_image).unsqueeze(0)


def _extract_usable_asset_urls(task_result):
    data = task_result.get("data", {}) if isinstance(task_result, dict) else {}
    result = data.get("result", {}) if isinstance(data, dict) else {}
    urls = []
    for key in ("usable_assets", "assets"):
        items = result.get(key)
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    asset_url = item.get("asset_url") or item.get("url")
                    status = str(item.get("status", "")).lower()
                    if asset_url and (key == "usable_assets" or status in ("active", "success", "completed", "")):
                        urls.append(asset_url)
    single = result.get("asset_url")
    if isinstance(single, str) and single:
        urls.append(single)
    return urls


class DapaoAPImartSeedance2AssetBundleNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧资源": ("STRING", {"default": "", "placeholder": "asset://xxx 或公网 URL"}),
            "🏁 尾帧资源": ("STRING", {"default": "", "placeholder": "asset://xxx 或公网 URL"}),
        }
        for i in range(1, 10):
            optional[f"🖼️ 参考图{i}"] = ("STRING", {"default": "", "placeholder": "asset://xxx 或公网 URL"})
        for i in range(1, 4):
            optional[f"🎞️ 参考视频{i}"] = ("STRING", {"default": "", "placeholder": "asset://xxx 或公网 URL"})
        for i in range(1, 4):
            optional[f"🎵 参考音频{i}"] = ("STRING", {"default": "", "placeholder": "asset://xxx 或公网 URL"})
        return {"required": {}, "optional": optional}

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("📦 资源包", "📋 响应信息")
    FUNCTION = "bundle"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "APImart 即梦2.0资源包：整理 asset:// 或公网 URL 给全能参考节点使用 @炮老师的小课堂"
    OUTPUT_NODE = False

    def bundle(self, **kwargs):
        first_frame = _asset_id_to_url(kwargs.get("🎬 首帧资源", ""))
        last_frame = _asset_id_to_url(kwargs.get("🏁 尾帧资源", ""))
        ref_images = [_asset_id_to_url(kwargs.get(f"🖼️ 参考图{i}", "")) for i in range(1, 10)]
        video_urls = [_asset_id_to_url(kwargs.get(f"🎞️ 参考视频{i}", "")) for i in range(1, 4)]
        audio_urls = [_asset_id_to_url(kwargs.get(f"🎵 参考音频{i}", "")) for i in range(1, 4)]
        payload = {
            "first_frame": first_frame,
            "last_frame": last_frame,
            "ref_images": [url for url in ref_images if url],
            "video_urls": [url for url in video_urls if url],
            "audio_urls": [url for url in audio_urls if url],
        }
        bundle_json = json.dumps(payload, ensure_ascii=False)
        info = [
            "✅ 即梦2.0资源包已生成",
            f"🎬 首帧：{'有' if first_frame else '无'}",
            f"🏁 尾帧：{'有' if last_frame else '无'}",
            f"🖼️ 参考图：{len(payload['ref_images'])}",
            f"🎞️ 参考视频：{len(payload['video_urls'])}",
            f"🎵 参考音频：{len(payload['audio_urls'])}",
        ]
        return (bundle_json, "\n".join(info))


class DapaoAPImartSeedance2OmniReferenceNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE",),
            "🏁 尾帧图": ("IMAGE",),
        }
        for i in range(1, 10):
            optional[f"🖼️ 参考图{i}"] = ("IMAGE",)
        for i in range(1, 4):
            optional[f"🎞️ 参考视频{i}"] = ("VIDEO",)
        for i in range(1, 4):
            optional[f"🎵 参考音频{i}"] = ("AUDIO",)
        optional.update({
            "📦 资源包": ("STRING", {"default": "", "multiline": True, "placeholder": "接入 🐲即梦2.0资源包 输出"}),
            "🖼️ 返回尾帧": ("BOOLEAN", {"default": False}),
            "🔎 联网搜索": ("BOOLEAN", {"default": False}),
            "🤖 自定义模型ID": ("STRING", {"default": "", "placeholder": "留空使用模型下拉；填写后优先使用"}),
            "🔗 自定义API地址": ("STRING", {"default": "", "placeholder": "默认 https://api.apimart.ai；可填兼容地址"}),
            "➕ 额外参数JSON": ("STRING", {"default": "{}", "multiline": True, "placeholder": "可选：额外 payload 字段 JSON"}),
            "🔁 最大轮询次数": ("INT", {"default": 120, "min": 1, "max": 720, "step": 1}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
            "♻️ 最大重试次数": ("INT", {"default": 2, "min": 0, "max": 5, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 180, "min": 30, "max": 600, "step": 1}),
        })
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 APImart API Key"}),
                "🤖 模型": (["doubao-seedance-2.0", "doubao-seedance-2.0-fast", "doubao-seedance-2.0-face", "doubao-seedance-2.0-fast-face"], {"default": "doubao-seedance-2.0"}),
                "📝 提示词": ("STRING", {"multiline": True, "default": "小猫对着镜头打哈欠", "placeholder": "描述视频内容、动作、镜头和风格..."}),
                "📐 画面比例": (["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "adaptive"], {"default": "16:9"}),
                "🧩 分辨率": (["480p", "720p", "1080p"], {"default": "720p"}),
                "⏱️ 时长(秒)": ("INT", {"default": 5, "min": 4, "max": 15, "step": 1}),
                "🔊 生成音频": ("BOOLEAN", {"default": True}),
                "🎲 随机种": ("INT", {"default": -1, "min": -1, "max": 2147483647, "control_after_generate": "randomize"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL", "🏁 尾帧图")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "APImart 即梦2.0全能参考：文生视频、图生视频、首尾帧、视频/音频参考 @炮老师的小课堂"
    OUTPUT_NODE = False

    def _collect_resources(self, kwargs):
        bundle = _safe_json_loads(kwargs.get("📦 资源包", ""))
        image_with_roles = []
        image_urls = []
        video_urls = []
        audio_urls = []

        first_frame = kwargs.get("🎬 首帧图")
        last_frame = kwargs.get("🏁 尾帧图")
        if first_frame is not None:
            image_with_roles.append({"url": _tensor_to_data_uri(first_frame), "role": "first_frame"})
        elif _asset_id_to_url(bundle.get("first_frame", "")):
            image_with_roles.append({"url": _asset_id_to_url(bundle.get("first_frame", "")), "role": "first_frame"})

        if last_frame is not None:
            image_with_roles.append({"url": _tensor_to_data_uri(last_frame), "role": "last_frame"})
        elif _asset_id_to_url(bundle.get("last_frame", "")):
            image_with_roles.append({"url": _asset_id_to_url(bundle.get("last_frame", "")), "role": "last_frame"})

        for i in range(1, 10):
            image = kwargs.get(f"🖼️ 参考图{i}")
            if image is not None:
                image_urls.append(_tensor_to_data_uri(image))
        image_urls.extend(_split_string_items(bundle.get("ref_images")))

        for i in range(1, 4):
            video = kwargs.get(f"🎞️ 参考视频{i}")
            url = _video_input_to_data_uri(video)
            if url:
                video_urls.append(url)
        video_urls.extend(_split_string_items(bundle.get("video_urls")))
        video_urls.extend(_split_string_items(bundle.get("videos")))

        for i in range(1, 4):
            audio = kwargs.get(f"🎵 参考音频{i}")
            url = _audio_input_to_data_uri(audio)
            if url:
                audio_urls.append(url)
        audio_urls.extend(_split_string_items(bundle.get("audio_urls")))
        audio_urls.extend(_split_string_items(bundle.get("audios")))

        return image_with_roles, image_urls, video_urls, audio_urls

    def generate(self, **kwargs):
        api_key = kwargs.get("🔑 API密钥", "").strip()
        model = kwargs.get("🤖 模型", "doubao-seedance-2.0")
        custom_model_id = kwargs.get("🤖 自定义模型ID", "").strip()
        final_model = custom_model_id or model
        prompt = kwargs.get("📝 提示词", "").strip()
        size = kwargs.get("📐 画面比例", "16:9")
        resolution = kwargs.get("🧩 分辨率", "720p")
        duration = int(kwargs.get("⏱️ 时长(秒)", 5))
        generate_audio = bool(kwargs.get("🔊 生成音频", True))
        seed = int(kwargs.get("🎲 随机种", -1))
        return_last_frame = bool(kwargs.get("🖼️ 返回尾帧", False))
        web_search = bool(kwargs.get("🔎 联网搜索", False))
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        extra_params = _safe_json_loads(kwargs.get("➕ 额外参数JSON", "{}"))
        max_poll_attempts = int(kwargs.get("🔁 最大轮询次数", 120))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        retry_count = int(kwargs.get("♻️ 最大重试次数", 2))
        timeout = int(kwargs.get("⌛ 请求超时", 180))

        if not api_key:
            raise ValueError("请填写 🔑 API密钥。")
        if not final_model:
            raise ValueError("请填写 🤖 模型 或 🤖 自定义模型ID。")
        if not prompt:
            raise ValueError("请填写 📝 提示词。")

        image_with_roles, image_urls, video_urls, audio_urls = self._collect_resources(kwargs)
        if image_with_roles and image_urls:
            raise ValueError("APImart 文档限制：image_urls 和 image_with_roles 不能同时使用。使用首帧/尾帧时，请不要再接普通参考图。")
        if image_with_roles and (video_urls or audio_urls):
            raise ValueError("APImart 文档限制：使用首帧/尾帧图片时，不能同时使用参考视频或参考音频。")

        payload = {
            "model": final_model,
            "prompt": prompt,
            "resolution": resolution,
            "size": size,
            "duration": duration,
            "generate_audio": generate_audio,
        }
        if seed >= 0:
            payload["seed"] = seed
        if return_last_frame:
            payload["return_last_frame"] = True
        if web_search:
            payload["tools"] = [{"type": "web_search"}]
        if image_with_roles:
            payload["image_with_roles"] = image_with_roles
        if image_urls:
            payload["image_urls"] = image_urls
        if video_urls:
            payload["video_urls"] = video_urls
        if audio_urls:
            payload["audio_urls"] = audio_urls
        payload.update(extra_params)

        base_url = _get_base_url(custom_api_url)
        headers = _headers(api_key)
        start_time = time.time()
        try:
            submit_result = _request_json_with_retry("POST", f"{base_url}/v1/videos/generations", headers, payload, timeout, retry_count, "APImart 即梦2.0视频生成")
            task_id = _extract_task_id(submit_result)
            if not task_id:
                raise RuntimeError(f"视频任务提交成功，但没有找到 task_id。提交返回：{json.dumps(submit_result, ensure_ascii=False)[:1000]}")
            task_result = _poll_task(base_url, task_id, headers, timeout, retry_count, max_poll_attempts, poll_interval, "APImart 即梦2.0视频生成")
            video_url = _extract_video_url(task_result)
            if not video_url:
                raise RuntimeError(f"视频任务完成，但没有找到视频 URL。任务返回：{json.dumps(task_result, ensure_ascii=False)[:1000]}")
            last_frame_url = _extract_last_frame_url(task_result) if return_last_frame else ""
            last_frame_tensor = _download_image_to_tensor(last_frame_url, timeout) if last_frame_url else _blank_image_tensor()
        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"APImart 即梦2.0请求超时：{timeout} 秒内没有响应。详情：{e}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"APImart 即梦2.0网络连接失败：请检查网络、代理或防火墙。详情：{e}")
        except Exception:
            traceback.print_exc()
            raise

        elapsed_time = time.time() - start_time
        info = [
            "✅ APImart 即梦2.0视频生成完成",
            f"🤖 模型：{final_model}",
            f"📐 画面比例：{size}",
            f"🧩 分辨率：{resolution}",
            f"⏱️ 时长：{duration} 秒",
            f"🔊 生成音频：{generate_audio}",
            f"🎲 随机种：{seed}",
            f"🖼️ 普通参考图：{len(image_urls)}",
            f"🎬 首尾帧/角色图：{len(image_with_roles)}",
            f"🎞️ 参考视频：{len(video_urls)}",
            f"🎵 参考音频：{len(audio_urls)}",
            f"🆔 任务ID：{task_id}",
            f"🔗 视频URL：{video_url}",
            f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
        ]
        if last_frame_url:
            info.append(f"🏁 尾帧URL：{last_frame_url}")
        raw_json = json.dumps({"submit": submit_result, "task": task_result}, ensure_ascii=False, indent=2)
        return (APImartSeedanceVideoAdapter(video_url), task_id, "\n".join(info) + "\n\n" + raw_json, video_url, last_frame_tensor)


class DapaoAPImartSeedance2AssetUploadNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 APImart API Key"}),
                "🏷️ 资产名称": ("STRING", {"default": "dapao-seedance-asset", "placeholder": "素材名称"}),
                "📁 分组名称": ("STRING", {"default": "dapao-seedance-assets", "placeholder": "不填已有分组ID时会创建/复用该名称"}),
                "📝 项目名称": ("STRING", {"default": "default"}),
                "🎭 资产类型": (["Image", "Video", "Audio"], {"default": "Image"}),
            },
            "optional": {
                "📁 已有分组ID": ("STRING", {"default": "", "placeholder": "填写后优先使用 group_id，不创建新组"}),
                "🖼️ 图片素材": ("IMAGE",),
                "🎞️ 视频素材": ("VIDEO",),
                "🎵 音频素材": ("AUDIO",),
                "🌐 素材公网URL": ("STRING", {"default": "", "placeholder": "本地素材为空时使用；需公网可访问"}),
                "🔗 自定义API地址": ("STRING", {"default": "", "placeholder": "默认 https://api.apimart.ai；可填兼容地址"}),
                "🔁 最大轮询次数": ("INT", {"default": 120, "min": 1, "max": 720, "step": 1}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
                "♻️ 最大重试次数": ("INT", {"default": 2, "min": 0, "max": 5, "step": 1}),
                "⌛ 请求超时": ("INT", {"default": 180, "min": 30, "max": 600, "step": 1}),
                "跳过错误": ("BOOLEAN", {"default": False}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🆔 任务ID", "✅ 状态", "🔗 可用资产URL", "📋 响应信息")
    FUNCTION = "upload_asset"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "APImart 即梦2.0资产上传：虚拟素材审核，输出 asset:// 给视频生成使用 @炮老师的小课堂"
    OUTPUT_NODE = False

    def _media_to_url(self, image, video, audio, public_url, selected_asset_type):
        wired = []
        if image is not None:
            wired.append("图片")
        if video is not None:
            wired.append("视频")
        if audio is not None:
            wired.append("音频")
        if public_url:
            wired.append("公网URL")

        if image is not None:
            return _tensor_to_data_uri(image), "Image", wired
        if video is not None:
            return _video_input_to_data_uri(video), "Video", wired
        if audio is not None:
            return _audio_input_to_data_uri(audio), "Audio", wired
        if public_url:
            return _asset_id_to_url(public_url), selected_asset_type, wired
        return "", selected_asset_type, wired

    def upload_asset(self, **kwargs):
        api_key = kwargs.get("🔑 API密钥", "").strip()
        asset_name = kwargs.get("🏷️ 资产名称", "").strip() or f"dapao_asset_{int(time.time())}"
        group_name = kwargs.get("📁 分组名称", "").strip() or "dapao-seedance-assets"
        project_name = kwargs.get("📝 项目名称", "default").strip() or "default"
        selected_asset_type = kwargs.get("🎭 资产类型", "Image")
        group_id = kwargs.get("📁 已有分组ID", "").strip()
        image = kwargs.get("🖼️ 图片素材")
        video = kwargs.get("🎞️ 视频素材")
        audio = kwargs.get("🎵 音频素材")
        public_url = kwargs.get("🌐 素材公网URL", "").strip()
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        max_poll_attempts = int(kwargs.get("🔁 最大轮询次数", 120))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        retry_count = int(kwargs.get("♻️ 最大重试次数", 2))
        timeout = int(kwargs.get("⌛ 请求超时", 180))
        skip_error = bool(kwargs.get("跳过错误", False))

        try:
            if not api_key:
                raise ValueError("请填写 🔑 API密钥。")
            media_url, asset_type, wired = self._media_to_url(image, video, audio, public_url, selected_asset_type)
            if not media_url:
                raise ValueError("请接入 🖼️ 图片素材、🎞️ 视频素材、🎵 音频素材，或填写 🌐 素材公网URL。")

            payload = {
                "project_name": project_name,
                "asset_type": asset_type,
                "assets": [{"url": media_url, "name": asset_name}],
            }
            if group_id:
                payload["group_id"] = group_id
            else:
                payload["group"] = {
                    "name": group_name,
                    "description": "ComfyUI-dapaoAPI Seedance 2.0 assets",
                }

            base_url = _get_base_url(custom_api_url)
            headers = _headers(api_key, "ComfyUI-dapaoAPI/APImartSeedance2AssetUpload")
            submit_result = _request_json_with_retry("POST", f"{base_url}/v1/seedance2/private-avatar", headers, payload, timeout, retry_count, "APImart 即梦2.0资产上传")
            task_id = _extract_task_id(submit_result)
            if not task_id:
                raise RuntimeError(f"素材提交成功，但没有找到任务ID。提交返回：{json.dumps(submit_result, ensure_ascii=False)[:1000]}")
            task_result = _poll_task(base_url, task_id, headers, timeout, retry_count, max_poll_attempts, poll_interval, "APImart 即梦2.0资产上传", allow_failed_result=True)
            status, _, error = _task_status(task_result)
            usable_urls = _extract_usable_asset_urls(task_result)
            asset_url = usable_urls[0] if usable_urls else ""
            if not asset_url and str(status).lower() in ("failed", "failure"):
                raise RuntimeError(f"素材审核失败：{error or json.dumps(task_result, ensure_ascii=False)[:1000]}")

            info = [
                "✅ APImart 即梦2.0资产上传完成" if asset_url else "⚠️ APImart 即梦2.0资产任务完成但未返回可用资产",
                f"🆔 任务ID：{task_id}",
                f"✅ 状态：{status}",
                f"🎭 资产类型：{asset_type}",
                f"🏷️ 资产名称：{asset_name}",
                f"📁 分组：{group_id or group_name}",
                f"🔌 输入来源：{', '.join(wired)}",
            ]
            if media_url.startswith("data:"):
                info.append("ℹ️ 本地素材已按 data URI 提交；如果平台拒绝，请改用公网可访问素材 URL。")
            if usable_urls:
                info.append("🔗 可用资产URL：")
                info.extend(usable_urls)
            raw_json = json.dumps({"submit": submit_result, "task": task_result}, ensure_ascii=False, indent=2)
            return (task_id, str(status or ""), asset_url, "\n".join(info) + "\n\n" + raw_json)
        except Exception as e:
            traceback.print_exc()
            if not skip_error:
                raise
            return ("", "error", "", json.dumps({"error": str(e)}, ensure_ascii=False))


NODE_CLASS_MAPPINGS = {
    "DapaoAPImartSeedance2AssetBundleNode": DapaoAPImartSeedance2AssetBundleNode,
    "DapaoAPImartSeedance2OmniReferenceNode": DapaoAPImartSeedance2OmniReferenceNode,
    "DapaoAPImartSeedance2AssetUploadNode": DapaoAPImartSeedance2AssetUploadNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoAPImartSeedance2AssetBundleNode": "🐲即梦2.0资源包@炮老师的小课堂",
    "DapaoAPImartSeedance2OmniReferenceNode": "🐲即梦2.0全能参考@炮老师的小课堂",
    "DapaoAPImartSeedance2AssetUploadNode": "🐲即梦2.0资产上传@炮老师的小课堂",
}
