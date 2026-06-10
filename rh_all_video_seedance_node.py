"""
RH 全能视频 Seedance2.0 节点

按 RunningHub 标准模型 API 调用 Seedance2.0 / Seedance2.0 Fast 的文生视频、
图生视频和多模态视频接口。
作者：@炮老师的小课堂
"""

import io
import json
import os
import tempfile
import time
import traceback
import wave

import numpy as np
import requests
from PIL import Image

try:
    import comfy.utils
    from comfy.comfy_types import IO
except Exception:
    comfy = None

    class IO:
        VIDEO = "VIDEO"

from .rh_all_image_node import (
    BASE_URL,
    POLL_URL,
    UPLOAD_URL,
    DapaoRHAllImageNode,
    create_blank_tensor,
    pil2tensor,
)


NODE_NAME = "DapaoRHAllVideoSeedanceNode"

MODEL_CHOICES = ["SEEDANCE2.0", "SEEDANCE2.0-FAST"]
FUNCTION_CHOICES = ["文生视频", "图生视频", "多模态视频"]
RESOLUTION_CHOICES = ["480p", "720p", "native1080p", "1080p", "2k", "4k"]
DURATION_CHOICES = ["-1", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]
RATIO_CHOICES = ["adaptive", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"]
CONVERSION_SLOT_CHOICES = [
    "all",
    "firstFrameUrl",
    "lastFrameUrl",
    "image1",
    "image2",
    "image3",
    "image4",
    "image5",
    "image6",
    "image7",
    "image8",
    "image9",
    "video1",
    "video2",
    "video3",
]

ENDPOINT_CONFIGS = {
    ("SEEDANCE2.0", "文生视频"): {
        "endpoint": "rhart-video/sparkvideo-2.0/text-to-video",
        "display_name": "SEEDANCE2.0/文生视频",
        "price": "¥0.6/秒",
        "resolutions": ["480p", "720p", "native1080p", "1080p", "2k", "4k"],
        "conversion_slots": [],
    },
    ("SEEDANCE2.0-FAST", "文生视频"): {
        "endpoint": "rhart-video/sparkvideo-2.0-fast/text-to-video",
        "display_name": "SEEDANCE2.0-FAST/文生视频",
        "price": "¥0.5/秒",
        "resolutions": ["480p", "720p", "1080p", "2k", "4k"],
        "conversion_slots": [],
    },
    ("SEEDANCE2.0", "图生视频"): {
        "endpoint": "rhart-video/sparkvideo-2.0/image-to-video",
        "display_name": "SEEDANCE2.0/图生视频",
        "price": "¥0.6/秒",
        "resolutions": ["480p", "720p", "native1080p", "1080p", "2k", "4k"],
        "conversion_slots": ["all", "firstFrameUrl", "lastFrameUrl"],
    },
    ("SEEDANCE2.0-FAST", "图生视频"): {
        "endpoint": "rhart-video/sparkvideo-2.0-fast/image-to-video",
        "display_name": "SEEDANCE2.0-FAST/图生视频",
        "price": "¥0.5/秒",
        "resolutions": ["480p", "720p", "1080p", "2k", "4k"],
        "conversion_slots": ["all", "firstFrameUrl", "lastFrameUrl"],
    },
    ("SEEDANCE2.0", "多模态视频"): {
        "endpoint": "rhart-video/sparkvideo-2.0/multimodal-video",
        "display_name": "SEEDANCE2.0/多模态视频",
        "price": "¥0.6/秒",
        "resolutions": ["480p", "720p", "native1080p", "1080p", "2k", "4k"],
        "conversion_slots": ["all", "image1", "image2", "image3", "image4", "image5", "image6", "image7", "image8", "image9", "video1", "video2", "video3"],
    },
    ("SEEDANCE2.0-FAST", "多模态视频"): {
        "endpoint": "rhart-video/sparkvideo-2.0-fast/multimodal-video",
        "display_name": "SEEDANCE2.0-FAST/多模态视频",
        "price": "¥0.5/秒",
        "resolutions": ["480p", "720p", "1080p", "2k", "4k"],
        "conversion_slots": ["all", "image1", "image2", "image3", "image4", "image5", "image6", "image7", "image8", "image9", "video1", "video2", "video3"],
    },
}


def _log_info(message):
    print(f"[dapaoAPI-RH全能视频Seedance2.0] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH全能视频Seedance2.0] 错误：{message}")


class RHSeedanceVideoAdapter:
    def __init__(self, video_url):
        self.video_url = video_url or ""

    def get_dimensions(self):
        return 1280, 720

    def save_to(self, output_path, format="auto", codec="auto", metadata=None):
        if not self.video_url:
            return False
        try:
            response = requests.get(self.video_url, stream=True, timeout=300, allow_redirects=True)
            response.raise_for_status()
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            _log_error(f"视频保存失败：{e}")
            return False


class DapaoRHAllVideoSeedanceNode(DapaoRHAllImageNode):
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "图生视频必填；多模态视频可作为普通参考图。"}),
            "🏁 尾帧图": ("IMAGE", {"tooltip": "图生视频可选尾帧。"}),
        }
        for i in range(1, 10):
            optional[f"🖼️ 参考图{i}"] = ("IMAGE", {"tooltip": f"多模态视频参考图{i}，最多9张。"})
        for i in range(1, 4):
            optional[f"🎞️ 参考视频{i}"] = ("VIDEO", {"tooltip": f"多模态视频参考视频{i}，最多3个。"})
        for i in range(1, 4):
            optional[f"🎵 参考音频{i}"] = ("AUDIO", {"tooltip": f"多模态视频参考音频{i}，最多3个。"})
        optional.update({
            "🌐 首帧公网URL": ("STRING", {"default": "", "placeholder": "可选：不用图像输入时填写首帧图片 URL"}),
            "🌐 尾帧公网URL": ("STRING", {"default": "", "placeholder": "可选：不用图像输入时填写尾帧图片 URL"}),
            "🖼️ 参考图URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "多模态视频可选：一行一个图片 URL"}),
            "🎞️ 参考视频URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "多模态视频可选：一行一个视频 URL"}),
            "🎵 参考音频URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "多模态视频可选：一行一个音频 URL"}),
            "🔄 更多素材转换槽位": ("STRING", {"multiline": True, "default": "", "placeholder": "可选多选：一行一个槽位，例如 image1\\nvideo1；填 all 时优先使用 all"}),
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}", "placeholder": "{\"webhookUrl\":\"https://example.com/webhook\"}"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 10, "max": 600, "step": 1}),
        })
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 RunningHub API Key"}),
                "🤖 模型": (MODEL_CHOICES, {"default": "SEEDANCE2.0"}),
                "🎛️ 功能": (FUNCTION_CHOICES, {"default": "文生视频"}),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "镜头缓慢推进，阳光穿过窗户，画面电影感，高质量视频",
                    "placeholder": "文生视频必填；图生视频可选；多模态视频支持 @Image 1 / @Video 1 等引用。"
                }),
                "🧩 分辨率": (RESOLUTION_CHOICES, {"default": "720p"}),
                "⏱️ 时长(秒)": (DURATION_CHOICES, {"default": "5"}),
                "📐 视频比例": (RATIO_CHOICES, {"default": "adaptive"}),
                "🔊 生成音频": ("BOOLEAN", {"default": True}),
                "🧍 真人模式": ("BOOLEAN", {"default": True, "tooltip": "开启后 RH 会尝试把素材转为 asset:// 以增强人物一致性。"}),
                "🔄 素材转换槽位": (CONVERSION_SLOT_CHOICES, {"default": "all"}),
                "🖼️ 返回尾帧": ("BOOLEAN", {"default": False}),
                "🔎 联网搜索": ("BOOLEAN", {"default": False, "tooltip": "仅文生视频接口使用。"}),
                "🎲 随机种": ("INT", {"default": -1, "min": -1, "max": 2147483647, "control_after_generate": "randomize"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL", "🏁 尾帧图")
    FUNCTION = "generate_video"
    CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"
    DESCRIPTION = "RunningHub Seedance2.0 / FAST：文生视频、图生视频、多模态视频 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _split_lines(text):
        return [line.strip() for line in (text or "").splitlines() if line.strip()]

    @staticmethod
    def _split_slot_items(text):
        if not text:
            return []
        normalized = str(text).replace("，", ",").replace("、", ",").replace("\n", ",")
        return [item.strip() for item in normalized.split(",") if item.strip()]

    @staticmethod
    def _blank_last_frame():
        return create_blank_tensor(1, 1)

    @staticmethod
    def _tensor_to_png_bytes(image_tensor):
        image_np = np.clip(image_tensor[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        image = Image.fromarray(image_np).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()

    @staticmethod
    def _audio_to_wav_bytes(audio_input):
        waveform = audio_input.get("waveform") if isinstance(audio_input, dict) else None
        sample_rate = audio_input.get("sample_rate") if isinstance(audio_input, dict) else None
        if sample_rate is None and isinstance(audio_input, dict):
            sample_rate = audio_input.get("sampler_rate")
        if waveform is None:
            return None
        sample_rate = int(sample_rate or 44100)
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
            pcm = (np.clip(waveform, -1.0, 1.0) * 32767.0).astype(np.int16)
        else:
            pcm = waveform.astype(np.int16)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wf:
            wf.setnchannels(int(pcm.shape[1]))
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(pcm.tobytes())
        return buffer.getvalue()

    def _upload_bytes(self, api_key, content, filename, mime_type, timeout):
        files = {"file": (filename, content, mime_type)}
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(UPLOAD_URL, headers=headers, files=files, timeout=max(timeout, 120))
        if response.status_code >= 400:
            raise RuntimeError(f"媒体上传失败 {response.status_code}：{self._error_message(response)}")
        data = response.json()
        if data.get("code") == 0:
            url = data.get("data", {}).get("download_url")
            if url:
                return url
        raise RuntimeError(f"媒体上传失败：{data.get('msg') or data.get('message') or data}")

    def _image_to_url(self, image_tensor, api_key, name, timeout):
        if image_tensor is None:
            return ""
        content = self._tensor_to_png_bytes(image_tensor)
        return self._upload_bytes(api_key, content, f"{name}.png", "image/png", timeout)

    def _video_to_url(self, video_input, api_key, name, timeout):
        if not video_input:
            return ""
        if isinstance(video_input, str):
            value = video_input.strip()
            if value.startswith("http://") or value.startswith("https://"):
                return value
            if os.path.exists(value):
                with open(value, "rb") as f:
                    return self._upload_bytes(api_key, f.read(), f"{name}.mp4", "video/mp4", timeout)
            return ""
        temp_path = os.path.join(tempfile.gettempdir(), f"dapao_rh_seedance_{name}_{int(time.time() * 1000)}.mp4")
        try:
            if hasattr(video_input, "save_to"):
                video_input.save_to(temp_path)
                with open(temp_path, "rb") as f:
                    return self._upload_bytes(api_key, f.read(), f"{name}.mp4", "video/mp4", timeout)
        finally:
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
        return ""

    def _audio_to_url(self, audio_input, api_key, name, timeout):
        if not audio_input:
            return ""
        if isinstance(audio_input, str):
            value = audio_input.strip()
            if value.startswith("http://") or value.startswith("https://"):
                return value
            if os.path.exists(value):
                with open(value, "rb") as f:
                    return self._upload_bytes(api_key, f.read(), f"{name}.wav", "audio/wav", timeout)
            return ""
        content = self._audio_to_wav_bytes(audio_input)
        if content:
            return self._upload_bytes(api_key, content, f"{name}.wav", "audio/wav", timeout)
        return ""

    def _collect_reference_urls(self, kwargs, api_key, timeout):
        image_urls = []
        video_urls = []
        audio_urls = []

        first_url = (kwargs.get("🌐 首帧公网URL", "") or "").strip()
        if first_url:
            image_urls.append(first_url)
        first_image = kwargs.get("🎬 首帧图")
        if first_image is not None and not first_url:
            image_urls.append(self._image_to_url(first_image, api_key, "rh_seedance_multimodal_first", timeout))

        for i in range(1, 10):
            image = kwargs.get(f"🖼️ 参考图{i}")
            if image is not None:
                image_urls.append(self._image_to_url(image, api_key, f"rh_seedance_image_{i}", timeout))
        image_urls.extend(self._split_lines(kwargs.get("🖼️ 参考图URL列表", "")))
        image_urls = [url for url in image_urls if url][:9]

        for i in range(1, 4):
            video = kwargs.get(f"🎞️ 参考视频{i}")
            url = self._video_to_url(video, api_key, f"rh_seedance_video_{i}", timeout)
            if url:
                video_urls.append(url)
        video_urls.extend(self._split_lines(kwargs.get("🎞️ 参考视频URL列表", "")))
        video_urls = [url for url in video_urls if url][:3]

        for i in range(1, 4):
            audio = kwargs.get(f"🎵 参考音频{i}")
            url = self._audio_to_url(audio, api_key, f"rh_seedance_audio_{i}", timeout)
            if url:
                audio_urls.append(url)
        audio_urls.extend(self._split_lines(kwargs.get("🎵 参考音频URL列表", "")))
        audio_urls = [url for url in audio_urls if url][:3]

        return image_urls, video_urls, audio_urls

    def _build_conversion_slots(self, kwargs, config):
        allowed = config.get("conversion_slots") or []
        if not allowed:
            return []
        slots = []
        primary = kwargs.get("🔄 素材转换槽位", "all")
        if primary:
            slots.append(primary)
        slots.extend(self._split_slot_items(kwargs.get("🔄 更多素材转换槽位", "")))
        deduped = []
        for slot in slots:
            if slot == "all":
                return ["all"]
            if slot and slot not in deduped:
                deduped.append(slot)
        invalid = [slot for slot in deduped if slot not in allowed]
        if invalid:
            raise ValueError(f"当前功能不支持这些素材转换槽位：{', '.join(invalid)}。可用槽位：{', '.join(allowed)}")
        return deduped or ["all"]

    def _poll_task_video(self, task_id, api_key, max_seconds, interval, timeout):
        elapsed = 0
        consecutive_failures = 0
        pbar = comfy.utils.ProgressBar(100) if comfy is not None else None
        if pbar:
            pbar.update_absolute(5)

        while elapsed < max_seconds:
            time.sleep(interval)
            elapsed += interval
            try:
                result = self._post_json(POLL_URL, api_key, {"taskId": task_id}, timeout)
                consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1
                if consecutive_failures >= 5:
                    raise RuntimeError(f"连续多次轮询失败，任务状态未知。最后错误：{e}")
                continue

            result_data = self._payload_data(result)
            status = result_data.get("status") or result.get("status", "UNKNOWN")
            if pbar:
                pbar.update_absolute(min(95, max(5, int(elapsed / max_seconds * 95))))
            if status == "SUCCESS":
                if pbar:
                    pbar.update_absolute(100)
                return result_data or result
            if status == "FAILED":
                error_code = result_data.get("errorCode") or result.get("errorCode") or ""
                error_msg = result_data.get("errorMessage") or result.get("errorMessage") or result.get("msg") or "Unknown error"
                raise RuntimeError(f"任务失败：[{error_code}] {error_msg}")

        raise RuntimeError(f"任务超过 {max_seconds} 秒仍未完成，请稍后查询任务ID：{task_id}")

    @staticmethod
    def _extract_result_urls(final):
        data = DapaoRHAllImageNode._payload_data(final)
        results = data.get("results") or final.get("results") or []
        urls = []
        for item in results:
            if isinstance(item, dict):
                url = item.get("url") or item.get("outputUrl")
                output_type = (item.get("outputType") or "").lower()
                if url:
                    urls.append({"url": str(url), "type": output_type})
        return urls

    @staticmethod
    def _pick_video_url(result_urls):
        for item in result_urls:
            url = item["url"]
            if item["type"] in ("mp4", "mov", "webm") or ".mp4" in url.lower() or ".webm" in url.lower():
                return url
        return result_urls[0]["url"] if result_urls else ""

    @staticmethod
    def _pick_last_frame_url(result_urls, video_url):
        image_exts = (".png", ".jpg", ".jpeg", ".webp")
        for item in result_urls:
            url = item["url"]
            output_type = item["type"]
            if url == video_url:
                continue
            if output_type in ("png", "jpg", "jpeg", "webp") or any(ext in url.lower() for ext in image_exts):
                return url
        return ""

    def _download_last_frame(self, url, timeout):
        if not url:
            return self._blank_last_frame()
        return pil2tensor(self._download_image(url, timeout))

    def _build_payload(self, kwargs, config, api_key, timeout):
        function = kwargs.get("🎛️ 功能", "文生视频")
        prompt = (kwargs.get("📝 提示词", "") or "").strip()
        resolution = kwargs.get("🧩 分辨率", "720p")
        duration = str(kwargs.get("⏱️ 时长(秒)", "5"))
        ratio = kwargs.get("📐 视频比例", "adaptive")
        generate_audio = bool(kwargs.get("🔊 生成音频", True))
        real_person_mode = bool(kwargs.get("🧍 真人模式", True))
        return_last_frame = bool(kwargs.get("🖼️ 返回尾帧", False))
        web_search = bool(kwargs.get("🔎 联网搜索", False))
        seed = int(kwargs.get("🎲 随机种", -1))

        if resolution not in config.get("resolutions", []):
            raise ValueError(f"{config['display_name']} 不支持分辨率 {resolution}，可用分辨率：{', '.join(config['resolutions'])}")
        if function in ("文生视频", "多模态视频") and not prompt:
            raise ValueError(f"{function}必须填写提示词。")

        payload = {
            "prompt": prompt if prompt else None,
            "resolution": resolution,
            "duration": duration,
            "generateAudio": generate_audio,
            "ratio": ratio,
            "returnLastFrame": return_last_frame,
            "seed": seed,
        }

        if function == "文生视频":
            payload["webSearch"] = web_search
        elif function == "图生视频":
            first_url = (kwargs.get("🌐 首帧公网URL", "") or "").strip()
            last_url = (kwargs.get("🌐 尾帧公网URL", "") or "").strip()
            if not first_url:
                first_image = kwargs.get("🎬 首帧图")
                if first_image is None:
                    first_image = kwargs.get("🖼️ 参考图1")
                first_url = self._image_to_url(first_image, api_key, "rh_seedance_first_frame", timeout)
            if not last_url and kwargs.get("🏁 尾帧图") is not None:
                last_url = self._image_to_url(kwargs.get("🏁 尾帧图"), api_key, "rh_seedance_last_frame", timeout)
            if not first_url:
                raise ValueError("图生视频必须接入 🎬 首帧图、🖼️ 参考图1，或填写 🌐 首帧公网URL。")
            payload["firstFrameUrl"] = first_url
            if last_url:
                payload["lastFrameUrl"] = last_url
            payload["realPersonMode"] = real_person_mode
            payload["conversionSlots"] = self._build_conversion_slots(kwargs, config)
        elif function == "多模态视频":
            image_urls, video_urls, audio_urls = self._collect_reference_urls(kwargs, api_key, timeout)
            if image_urls:
                payload["imageUrls"] = image_urls
            if video_urls:
                payload["videoUrls"] = video_urls
            if audio_urls:
                payload["audioUrls"] = audio_urls
            if not image_urls and not video_urls and not audio_urls:
                raise ValueError("多模态视频请至少接入一张参考图、一个参考视频、一个参考音频，或填写 URL 列表。")
            payload["realPersonMode"] = real_person_mode
            payload["conversionSlots"] = self._build_conversion_slots(kwargs, config)
        else:
            raise ValueError(f"未知功能：{function}")

        extra_params = json.loads(kwargs.get("📋 额外参数JSON", "{}") or "{}")
        if not isinstance(extra_params, dict):
            raise ValueError("额外参数JSON必须是 JSON 对象。")
        payload.update(extra_params)
        return payload

    def generate_video(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥", "") or "").strip()
        model = kwargs.get("🤖 模型", "SEEDANCE2.0")
        function = kwargs.get("🎛️ 功能", "文生视频")
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1200))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))

        if not api_key:
            return (RHSeedanceVideoAdapter(""), "", "❌ 错误：请填写 RunningHub API密钥。", "", self._blank_last_frame())

        config = ENDPOINT_CONFIGS.get((model, function))
        if not config:
            return (RHSeedanceVideoAdapter(""), "", f"❌ 错误：当前组合没有可用接口：{model} / {function}", "", self._blank_last_frame())

        start_time = time.time()
        submit_response = {}
        final_response = {}
        try:
            payload = self._build_payload(kwargs, config, api_key, timeout)
            endpoint = config["endpoint"]
            _log_info(f"开始请求 RH Seedance2.0：{endpoint}")
            submit_response = self._post_json(f"{BASE_URL}/{endpoint}", api_key, payload, timeout)
            if submit_response.get("errorCode") or submit_response.get("errorMessage"):
                raise RuntimeError(f"RunningHub 提交失败：[{submit_response.get('errorCode') or ''}] {submit_response.get('errorMessage') or submit_response}")
            task_id = self._extract_task_id(submit_response)
            if not task_id:
                raise RuntimeError(f"提交成功但响应中没有 taskId：{json.dumps(submit_response, ensure_ascii=False)[:1000]}")

            submit_data = self._payload_data(submit_response)
            if submit_data.get("status") == "SUCCESS" and submit_data.get("results"):
                final_response = submit_data
            else:
                final_response = self._poll_task_video(task_id, api_key, max_seconds, interval, timeout)

            result_urls = self._extract_result_urls(final_response)
            video_url = self._pick_video_url(result_urls)
            if not video_url:
                raise RuntimeError(f"任务完成但没有返回视频 URL：{json.dumps(final_response, ensure_ascii=False)[:1000]}")
            last_frame_url = self._pick_last_frame_url(result_urls, video_url) if bool(kwargs.get("🖼️ 返回尾帧", False)) else ""
            last_frame = self._download_last_frame(last_frame_url, timeout) if last_frame_url else self._blank_last_frame()

            elapsed_time = time.time() - start_time
            cost, duration = self._extract_usage(final_response)
            info_lines = [
                "✅ RH 全能视频 Seedance2.0 任务完成",
                f"🤖 模型：{model}",
                f"🎛️ 功能：{function}",
                f"📡 端点：{endpoint}",
                f"💵 标价：{config['price']}",
                f"🧩 分辨率：{payload.get('resolution')}",
                f"⏱️ 时长：{payload.get('duration')} 秒",
                f"📐 比例：{payload.get('ratio')}",
                f"🔊 生成音频：{payload.get('generateAudio')}",
                f"🧍 真人模式：{payload.get('realPersonMode', '未使用')}",
                f"🔄 素材转换槽位：{payload.get('conversionSlots', '未使用')}",
                f"🖼️ 返回尾帧：{payload.get('returnLastFrame')}",
                f"🎲 随机种：{payload.get('seed')}",
                f"🆔 任务ID：{task_id}",
                f"🔗 视频URL：{video_url}",
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
            ]
            if cost is not None:
                info_lines.append(f"💰 实际消耗：¥{cost}")
            if duration is not None:
                info_lines.append(f"⏳ RH任务耗时：{duration}")
            if last_frame_url:
                info_lines.append(f"🏁 尾帧URL：{last_frame_url}")

            raw_json = json.dumps({"payload": payload, "submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return (RHSeedanceVideoAdapter(video_url), task_id, "\n".join(info_lines) + "\n\n" + raw_json, video_url, last_frame)
        except Exception as e:
            error_msg = f"❌ 错误：RH 全能视频 Seedance2.0 生成失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            raw_json = json.dumps({"submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return (RHSeedanceVideoAdapter(""), "", error_msg + "\n\n" + raw_json, "", self._blank_last_frame())


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHAllVideoSeedanceNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🎉RH全能视频Seedance2.0@炮老师的小课堂",
}
