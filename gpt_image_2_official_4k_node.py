import re
import io
import time
import math
import base64
import torch
import requests
import numpy as np
from PIL import Image
from io import BytesIO
import comfy.utils
from comfy.utils import common_upscale


def pil2tensor(image):
    if image.mode != "RGB":
        image = image.convert("RGB")
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def downscale_input(image):
    samples = image.movedim(-1, 1)
    total_pixels = int(1536 * 1024)
    scale_by = math.sqrt(total_pixels / (samples.shape[3] * samples.shape[2]))
    if scale_by >= 1:
        return image
    width = round(samples.shape[3] * scale_by)
    height = round(samples.shape[2] * scale_by)
    scaled = common_upscale(samples, width, height, "lanczos", "disabled")
    return scaled.movedim(1, -1)


class DapaoGPTImage2Official4KNode:
    _ASPECT_RATIO_CHOICES = [
        "1:1", "3:2", "2:3", "4:3", "3:4", "5:4", "4:5",
        "16:9", "9:16", "2:1", "1:2", "21:9", "9:21",
    ]
    _RESOLUTION_CHOICES = ["1k", "2k", "4k"]
    _SIZE_MAP = {
        ("1:1", "1k"): "1024x1024", ("1:1", "2k"): "2048x2048", ("1:1", "4k"): "2880x2880",
        ("16:9", "1k"): "1280x720", ("16:9", "2k"): "2560x1440", ("16:9", "4k"): "3840x2160",
        ("9:16", "1k"): "720x1280", ("9:16", "2k"): "1440x2560", ("9:16", "4k"): "2160x3840",
        ("4:3", "1k"): "1152x864", ("4:3", "2k"): "2304x1728", ("4:3", "4k"): "3264x2448",
        ("3:4", "1k"): "864x1152", ("3:4", "2k"): "1728x2304", ("3:4", "4k"): "2448x3264",
        ("3:2", "1k"): "1248x832", ("3:2", "2k"): "2496x1664", ("3:2", "4k"): "3504x2336",
        ("2:3", "1k"): "832x1248", ("2:3", "2k"): "1664x2496", ("2:3", "4k"): "2336x3504",
        ("5:4", "1k"): "1120x896", ("5:4", "2k"): "2240x1792", ("5:4", "4k"): "3200x2560",
        ("4:5", "1k"): "896x1120", ("4:5", "2k"): "1792x2240", ("4:5", "4k"): "2560x3200",
        ("21:9", "1k"): "1456x624", ("21:9", "2k"): "3024x1296", ("21:9", "4k"): "3696x1584",
        ("9:21", "1k"): "624x1456", ("9:21", "2k"): "1296x3024", ("9:21", "4k"): "1584x3696",
        ("2:1", "1k"): "2048x1024", ("2:1", "2k"): "2688x1344", ("2:1", "4k"): "3840x1920",
        ("1:2", "1k"): "1024x2048", ("1:2", "2k"): "1344x2688", ("1:2", "4k"): "1920x3840",
    }

    @staticmethod
    def _parse_size_wh(size_str):
        match = re.match(r"^(\d+)x(\d+)$", size_str.strip())
        if not match:
            return None, None
        return int(match.group(1)), int(match.group(2))

    @classmethod
    def _validate_size(cls, size_str):
        width, height = cls._parse_size_wh(size_str)
        if width is None:
            return False, "尺寸格式须为 宽x高，例如 1024x1024"
        if max(width, height) > 3840:
            return False, "长边须 <= 3840px"
        short_edge, long_edge = min(width, height), max(width, height)
        if long_edge / short_edge > 3.0 + 1e-9:
            return False, "长边:短边 不得超过 3:1"
        pixels = width * height
        if pixels < 655360 or pixels > 8294400:
            return False, "总像素须在 655,360～8,294,400 之间"
        return True, None

    @classmethod
    def _get_size_from_params(cls, aspect_ratio, resolution):
        size = cls._SIZE_MAP.get((aspect_ratio, resolution))
        if size is None:
            return None, f"不支持的组合: {aspect_ratio} × {resolution}"
        return size, None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🌐 API线路": (["柏拉图", "zhenzhen", "hk", "us", "ip"], {
                    "default": "柏拉图",
                    "tooltip": "选择 API 线路：柏拉图 / zhenzhen / hk / us / ip(自定义地址)"
                }),
                "📝 提示词": ("STRING", {"multiline": True, "default": ""}),
                "📐 画面比例": (cls._ASPECT_RATIO_CHOICES, {"default": "1:1"}),
                "🧩 分辨率": (cls._RESOLUTION_CHOICES, {"default": "1k"}),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",), "🖼️ 图像2": ("IMAGE",), "🖼️ 图像3": ("IMAGE",), "🖼️ 图像4": ("IMAGE",),
                "🖼️ 图像5": ("IMAGE",), "🖼️ 图像6": ("IMAGE",), "🖼️ 图像7": ("IMAGE",), "🖼️ 图像8": ("IMAGE",),
                "🖼️ 图像9": ("IMAGE",), "🖼️ 图像10": ("IMAGE",), "🖼️ 图像11": ("IMAGE",), "🖼️ 图像12": ("IMAGE",),
                "🖼️ 图像13": ("IMAGE",), "🖼️ 图像14": ("IMAGE",), "🖼️ 图像15": ("IMAGE",), "🖼️ 图像16": ("IMAGE",),
                "🎭 遮罩": ("MASK",),
                "🔑 API密钥": ("STRING", {"default": "", "multiline": False}),
                "🖼️ 图片数量": ("INT", {"default": 1, "min": 1, "max": 10}),
                "🎨 画质": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "🌈 背景": (["auto", "opaque"], {"default": "auto"}),
                "📦 输出格式": (["png", "jpeg", "webp"], {"default": "png"}),
                "🗜️ 压缩质量": ("INT", {"default": 100, "min": 0, "max": 100}),
                "🛡️ 审核强度": (["auto", "low"], {"default": "auto"}),
                "⚡ 异步模式": ("BOOLEAN", {"default": True}),
                "🔔 Webhook": ("STRING", {"default": ""}),
                "🔁 最大轮询次数": ("INT", {"default": 300, "min": 10, "max": 1000}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60}),
                "♻️ 最大重试次数": ("INT", {"default": 5, "min": 1, "max": 10}),
                "⌛ 初始超时": ("INT", {"default": 900, "min": 60, "max": 1200}),
                "🎲 种子": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": "randomize"}),
                "🔗 自定义API地址": ("STRING", {"default": "", "placeholder": "当 API线路 选 ip 时填写完整地址"}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/GPT"
    DESCRIPTION = "GPT-image2 官方 4K @炮老师的小课堂"

    def __init__(self):
        self.api_key = ""
        self.timeout = 300
        self.session = requests.Session()
        retry_strategy = requests.packages.urllib3.util.retry.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _get_base_url(self, api_source, custom_api_url):
        mapping = {
            "柏拉图": "https://api.bltcy.ai",
            "zhenzhen": "https://ai.t8star.cn",
            "hk": "https://hk-api.gptbest.vip",
            "us": "https://api.gptbest.vip",
            "ip": (custom_api_url or "").strip(),
        }
        url = mapping.get(api_source, "")
        if api_source == "ip" and not url:
            return "https://api.bltcy.ai"
        return url

    def _auth_headers(self):
        return {"Authorization": f"Bearer {self.api_key}"}

    def _blank_tensor(self):
        return pil2tensor(Image.new("RGB", (1024, 1024), color="white"))

    def _blank_input_file(self):
        buffer = io.BytesIO()
        Image.new("RGB", (1024, 1024), color="white").save(buffer, format="PNG")
        buffer.seek(0)
        return ("blank.png", buffer, "image/png")

    def _make_request_with_retry(self, url, data=None, files=None, max_retries=5, initial_timeout=300):
        for attempt in range(1, max_retries + 1):
            current_timeout = min(initial_timeout * (1.5 ** (attempt - 1)), 1200)
            try:
                response = self.session.post(url, headers=self._auth_headers(), data=data, files=files, timeout=current_timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code in (400, 401, 403):
                    raise
                if attempt == max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 60))
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                if attempt == max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 60))
            except Exception:
                if attempt == max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 60))

    def _build_multipart(self, prompt, images, mask, n, quality, size, background, output_format, output_compression, moderation, seed):
        if mask is not None and not images:
            raise Exception("使用遮罩时必须提供至少一张图像")

        image_files = []
        for image_tensor in images:
            batch_size = image_tensor.shape[0]
            for i in range(batch_size):
                single_image = image_tensor[i:i + 1]
                scaled_image = downscale_input(single_image).squeeze()
                image_np = (scaled_image.numpy() * 255).astype(np.uint8)
                pil_image = Image.fromarray(image_np)
                image_bytes = io.BytesIO()
                pil_image.save(image_bytes, format="PNG")
                image_bytes.seek(0)
                image_files.append((f"image_{len(image_files)}.png", image_bytes, "image/png"))

        if not image_files:
            image_files.append(self._blank_input_file())

        request_files = [("image", file_tuple) for file_tuple in image_files]

        if mask is not None:
            if len(image_files) != 1:
                raise Exception("遮罩仅支持单张输入图像")
            first_img = images[0]
            if mask.shape[1:] != first_img.shape[1:-1]:
                raise Exception("遮罩与图像尺寸必须一致")
            _batch, height, width = mask.shape
            rgba_mask = torch.zeros(height, width, 4, device="cpu")
            rgba_mask[:, :, 3] = 1 - mask.squeeze().cpu()
            scaled_mask = downscale_input(rgba_mask.unsqueeze(0)).squeeze()
            mask_np = (scaled_mask.numpy() * 255).astype(np.uint8)
            mask_img = Image.fromarray(mask_np)
            mask_bytes = io.BytesIO()
            mask_img.save(mask_bytes, format="PNG")
            mask_bytes.seek(0)
            request_files.append(("mask", ("mask.png", mask_bytes, "image/png")))

        data = {
            "prompt": prompt,
            "model": "gpt-image-2",
            "n": str(n),
            "quality": quality,
            "moderation": moderation,
            "size": size,
        }
        if background != "auto":
            data["background"] = background
        if output_compression != 100:
            data["output_compression"] = str(output_compression)
        if output_format != "png":
            data["output_format"] = output_format
        if seed > 0:
            data["seed"] = str(seed)
        return data, request_files

    def _decode_one(self, b64_json, image_url, max_retries, initial_timeout):
        if b64_json:
            b64_data = b64_json.split(",", 1)[-1] if b64_json.startswith("data:image") else b64_json
            return pil2tensor(Image.open(BytesIO(base64.b64decode(b64_data))))
        if image_url:
            for attempt in range(1, max_retries + 1):
                try:
                    response = requests.get(image_url, timeout=min(initial_timeout * (1.5 ** (attempt - 1)), 900))
                    response.raise_for_status()
                    return pil2tensor(Image.open(BytesIO(response.content)))
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    if attempt == max_retries:
                        return None
                    time.sleep(min(2 ** (attempt - 1), 60))
        return None

    def _items_to_tensors(self, data_array, max_retries, initial_timeout):
        tensors = []
        first_url = ""
        for item in data_array or []:
            image_url = item.get("url", "") or ""
            b64_json = item.get("b64_json", "") or ""
            if image_url and not first_url:
                first_url = image_url
            tensor = self._decode_one(b64_json, image_url, max_retries, initial_timeout)
            if tensor is not None:
                tensors.append(tensor)
        return tensors, first_url

    def _async_edits(self, base_url, data, request_files, pbar, max_poll_attempts, poll_interval, webhook, max_retries, initial_timeout):
        url = f"{base_url}/v1/images/edits?async=true"
        if webhook.strip():
            url += f"&webhook={webhook.strip()}"
        response = requests.post(url, headers=self._auth_headers(), data=data, files=request_files, timeout=self.timeout)
        if response.status_code != 200:
            raise RuntimeError(f"API请求失败: {response.status_code} - {response.text}")
        submit_result = response.json()
        task_id = submit_result.get("task_id") or submit_result.get("data")
        if not task_id:
            raise RuntimeError(f"返回中没有 task_id: {submit_result}")
        pbar.update_absolute(20)

        query_url = f"{base_url}/v1/images/tasks/{task_id}"
        for _ in range(1, max_poll_attempts + 1):
            time.sleep(poll_interval)
            status_response = requests.get(query_url, headers=self._auth_headers(), timeout=self.timeout)
            if status_response.status_code != 200:
                continue
            status_data = status_response.json()
            inner = status_data.get("data", {}) if isinstance(status_data, dict) else {}
            status = inner.get("status", "")
            progress_str = inner.get("progress", "0%")
            try:
                if isinstance(progress_str, str) and progress_str.endswith("%"):
                    pbar.update_absolute(min(95, 20 + int(int(progress_str[:-1]) * 0.75)))
            except Exception:
                pass
            if status == "SUCCESS":
                result_data = inner.get("data", {})
                data_array = result_data.get("data", []) if isinstance(result_data, dict) else []
                tensors, first_url = self._items_to_tensors(data_array, max_retries, initial_timeout)
                if not tensors:
                    raise RuntimeError("任务成功但未解析到图片")
                pbar.update_absolute(100)
                return torch.cat(tensors, dim=0), first_url, task_id, status_data
            if status == "FAILURE":
                raise RuntimeError(f"任务失败: {inner.get('fail_reason', 'Unknown error')}")
        raise RuntimeError(f"轮询超过 {max_poll_attempts} 次仍未完成")

    def _build_info(self, api_source, prompt, aspect_ratio, resolution, size, quality, input_count, output_format, output_compression, moderation, async_mode, image_url="", task_id=""):
        info = f"模式: {'异步官方4K编辑' if async_mode else '同步官方4K编辑'}\n"
        info += f"线路: {api_source}\n"
        info += "模型: gpt-image-2\n"
        info += f"提示词: {prompt}\n"
        info += f"画面比例: {aspect_ratio}\n"
        info += f"分辨率: {resolution}\n"
        info += f"实际尺寸: {size}\n"
        info += f"画质: {quality}\n"
        info += f"输入图像数: {input_count}\n"
        info += f"输出格式: {output_format}\n"
        info += f"压缩质量: {output_compression}\n"
        info += f"审核强度: {moderation}\n"
        if task_id:
            info += f"任务ID: {task_id}\n"
        if image_url:
            info += f"图片链接: {image_url}\n"
        return info.strip()

    def generate(self, **kwargs):
        api_source = kwargs.get("🌐 API线路", "柏拉图")
        prompt = kwargs.get("📝 提示词", "")
        aspect_ratio = kwargs.get("📐 画面比例", "1:1")
        resolution = kwargs.get("🧩 分辨率", "1k")
        mask = kwargs.get("🎭 遮罩")
        api_key = kwargs.get("🔑 API密钥", "")
        n = int(kwargs.get("🖼️ 图片数量", 1))
        quality = kwargs.get("🎨 画质", "auto")
        background = kwargs.get("🌈 背景", "auto")
        output_format = kwargs.get("📦 输出格式", "png")
        output_compression = int(kwargs.get("🗜️ 压缩质量", 100))
        moderation = kwargs.get("🛡️ 审核强度", "auto")
        async_mode = bool(kwargs.get("⚡ 异步模式", True))
        webhook = kwargs.get("🔔 Webhook", "")
        max_poll_attempts = int(kwargs.get("🔁 最大轮询次数", 300))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        max_retries = int(kwargs.get("♻️ 最大重试次数", 5))
        initial_timeout = int(kwargs.get("⌛ 初始超时", 900))
        seed = int(kwargs.get("🎲 种子", 0))
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        images = [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 17) if kwargs.get(f"🖼️ 图像{i}") is not None]

        if api_key.strip():
            self.api_key = api_key.strip()
        blank_tensor = self._blank_tensor()
        if not self.api_key:
            return (blank_tensor, "", "API密钥为空，请填写后再试")

        size, size_error = self._get_size_from_params(aspect_ratio, resolution)
        if size_error:
            return (blank_tensor, "", size_error)
        valid, error_message = self._validate_size(size)
        if not valid:
            return (blank_tensor, "", error_message)

        base_url = self._get_base_url(api_source, custom_api_url)
        pbar = comfy.utils.ProgressBar(100)
        pbar.update_absolute(5)

        try:
            data, request_files = self._build_multipart(
                prompt, images, mask, n, quality, size, background,
                output_format, output_compression, moderation, seed,
            )
            if async_mode:
                combined, image_url, task_id, _final_result = self._async_edits(
                    base_url, data, request_files, pbar, max_poll_attempts,
                    poll_interval, webhook, max_retries, initial_timeout,
                )
                info = self._build_info(
                    api_source, prompt, aspect_ratio, resolution, size, quality,
                    len(images), output_format, output_compression, moderation,
                    True, image_url, task_id,
                )
                return (combined, image_url, info)

            pbar.update_absolute(20)
            response = self._make_request_with_retry(
                f"{base_url}/v1/images/edits",
                data=data,
                files=request_files,
                max_retries=max_retries,
                initial_timeout=initial_timeout,
            )
            result = response.json()
            data_array = result.get("data", []) if isinstance(result, dict) else []
            tensors, first_url = self._items_to_tensors(data_array, max_retries, initial_timeout)
            if not tensors:
                return (blank_tensor, "", f"未能解析返回图片: {result}")
            pbar.update_absolute(100)
            info = self._build_info(
                api_source, prompt, aspect_ratio, resolution, size, quality,
                len(images), output_format, output_compression, moderation,
                False, first_url, "",
            )
            return (torch.cat(tensors, dim=0), first_url, info)
        except Exception as e:
            return (blank_tensor, "", f"执行失败: {str(e)}")


NODE_CLASS_MAPPINGS = {
    "🙅GPT-image2官方4K@炮老师的小课堂": DapaoGPTImage2Official4KNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "🙅GPT-image2官方4K@炮老师的小课堂": "🙅GPT-image2官方4K@炮老师的小课堂",
}
