import re
import io
import time
import json
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


def tensor2pil(image):
    return [Image.fromarray(np.clip(255.0 * img.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)) for img in image]


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


class DapaoGPTImage2OfficialStableNode:
    _SIZE_CHOICES = [
        "auto",
        "1024x1024",
        "1536x1024",
        "1024x1536",
        "2048x2048",
        "2048x1152",
        "3840x2160",
        "2160x3840",
    ]

    @staticmethod
    def _parse_size_wh(size_str):
        match = re.match(r"^(\d+)x(\d+)$", size_str.strip())
        if not match:
            return None, None
        return int(match.group(1)), int(match.group(2))

    @classmethod
    def _validate_size(cls, size_str):
        if size_str == "auto":
            return True, None
        width, height = cls._parse_size_wh(size_str)
        if width is None:
            return False, "尺寸格式须为 宽x高，例如 1024x1024"
        if max(width, height) > 3840:
            return False, "长边须 <= 3840px"
        if width % 16 != 0 or height % 16 != 0:
            return False, "宽、高均须为 16 的倍数"
        short_edge, long_edge = min(width, height), max(width, height)
        if long_edge / short_edge > 3.0 + 1e-9:
            return False, "长边:短边 不得超过 3:1"
        pixels = width * height
        if pixels < 655360 or pixels > 8294400:
            return False, "总像素须在 655,360～8,294,400 之间"
        return True, None

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🌐 API线路": (["柏拉图", "zhenzhen", "hk", "us", "ip"], {
                    "default": "柏拉图",
                    "tooltip": "选择 API 线路：柏拉图 / zhenzhen / hk / us / ip(自定义地址)"
                }),
                "📝 提示词": ("STRING", {"multiline": True, "default": ""}),
            },
            "optional": {
                "🖼️ 图像": ("IMAGE",),
                "🎭 遮罩": ("MASK",),
                "🔑 API密钥": ("STRING", {"default": ""}),
                "🖼️ 图片数量": ("INT", {"default": 1, "min": 1, "max": 10}),
                "🎨 画质": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "📐 尺寸": (cls._SIZE_CHOICES, {"default": "auto"}),
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
    DESCRIPTION = "GPT Image 2 官方稳定版 @炮老师的小课堂"

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

    def _json_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _blank_image(self):
        return Image.new("RGB", (1024, 1024), color="white")

    def _blank_tensor(self):
        return pil2tensor(self._blank_image())

    def _blank_input_file(self):
        buffer = io.BytesIO()
        self._blank_image().save(buffer, format="PNG")
        buffer.seek(0)
        return ("blank.png", buffer, "image/png")

    def _make_request_with_retry(self, url, data=None, files=None, max_retries=5, initial_timeout=300):
        for attempt in range(1, max_retries + 1):
            current_timeout = min(initial_timeout * (1.5 ** (attempt - 1)), 1200)
            try:
                if files is not None:
                    response = self.session.post(
                        url,
                        headers=self._auth_headers(),
                        data=data,
                        files=files,
                        timeout=current_timeout,
                    )
                else:
                    response = self.session.post(
                        url,
                        headers=self._json_headers(),
                        json=data,
                        timeout=current_timeout,
                    )
                response.raise_for_status()
                return response
            except requests.exceptions.Timeout:
                if attempt == max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 60))
            except requests.exceptions.ConnectionError:
                if attempt == max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 60))
            except requests.exceptions.HTTPError as exc:
                if exc.response is not None and exc.response.status_code in (400, 401, 403):
                    raise
                if attempt == max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 60))
            except Exception:
                if attempt == max_retries:
                    raise
                time.sleep(min(2 ** (attempt - 1), 60))

    def _build_edits_multipart(self, prompt, image, mask, n, quality, size, background, output_format, output_compression, moderation):
        if mask is not None and image is None:
            raise Exception("使用遮罩时必须提供图像")

        files = {}
        if image is None:
            files["image"] = self._blank_input_file()
            batch_size = 1
        else:
            batch_size = image.shape[0]
            for i in range(batch_size):
                single_image = image[i:i + 1]
                scaled_image = downscale_input(single_image).squeeze()
                image_np = (scaled_image.numpy() * 255).astype(np.uint8)
                pil_image = Image.fromarray(image_np)
                image_bytes = io.BytesIO()
                pil_image.save(image_bytes, format="PNG")
                image_bytes.seek(0)
                if batch_size == 1:
                    files["image"] = ("image.png", image_bytes, "image/png")
                else:
                    files.setdefault("image[]", []).append((f"image_{i}.png", image_bytes, "image/png"))

        if mask is not None:
            if batch_size != 1:
                raise Exception("遮罩仅支持单张输入图")
            if mask.shape[1:] != image.shape[1:-1]:
                raise Exception("遮罩与图像尺寸必须一致")
            _batch, height, width = mask.shape
            rgba_mask = torch.zeros(height, width, 4, device="cpu")
            rgba_mask[:, :, 3] = 1 - mask.squeeze().cpu()
            scaled_mask = downscale_input(rgba_mask.unsqueeze(0)).squeeze()
            mask_np = (scaled_mask.numpy() * 255).astype(np.uint8)
            mask_image = Image.fromarray(mask_np)
            mask_bytes = io.BytesIO()
            mask_image.save(mask_bytes, format="PNG")
            mask_bytes.seek(0)
            files["mask"] = ("mask.png", mask_bytes, "image/png")

        data = {
            "prompt": prompt,
            "model": "gpt-image-2",
            "n": str(n),
            "quality": quality,
            "moderation": moderation,
        }
        if size != "auto":
            data["size"] = size
        if background != "auto":
            data["background"] = background
        if output_compression != 100:
            data["output_compression"] = str(output_compression)
        if output_format != "png":
            data["output_format"] = output_format

        request_files = []
        if "image[]" in files:
            for file_tuple in files["image[]"]:
                request_files.append(("image", file_tuple))
        elif "image" in files:
            request_files.append(("image", files["image"]))
        if "mask" in files:
            request_files.append(("mask", files["mask"]))

        return data, request_files

    def _decode_one(self, b64_json, image_url, max_retries, initial_timeout):
        if b64_json:
            b64_data = b64_json
            if b64_data.startswith("data:image"):
                b64_data = b64_data.split(",", 1)[-1]
            image_data = base64.b64decode(b64_data)
            return pil2tensor(Image.open(BytesIO(image_data)))
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

    def _items_to_tensors(self, result, max_retries=5, initial_timeout=300):
        tensors = []
        for item in result.get("data", []) or []:
            if item.get("b64_json"):
                tensor = self._decode_one(item.get("b64_json"), "", max_retries, initial_timeout)
                if tensor is not None:
                    tensors.append(tensor)
            elif item.get("url"):
                tensor = self._decode_one("", item.get("url"), max_retries, initial_timeout)
                if tensor is not None:
                    tensors.append(tensor)
        return tensors

    def _async_edits(self, base_url, prompt, image, mask, pbar, max_poll_attempts, poll_interval, webhook, n, quality, size, background, output_format, output_compression, moderation, max_retries, initial_timeout):
        data, request_files = self._build_edits_multipart(
            prompt, image, mask, n, quality, size, background, output_format, output_compression, moderation,
        )
        url = f"{base_url}/v1/images/edits?async=true"
        if webhook.strip():
            url += f"&webhook={webhook.strip()}"

        pbar.update_absolute(10)
        response = requests.post(
            url,
            headers=self._auth_headers(),
            data=data,
            files=request_files,
            timeout=self.timeout,
        )
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
                    progress_value = int(progress_str[:-1])
                    pbar.update_absolute(min(95, 20 + int(progress_value * 0.75)))
            except Exception:
                pass

            if status == "SUCCESS":
                result_data = inner.get("data", {})
                data_array = result_data.get("data", []) if isinstance(result_data, dict) else []
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
                if not tensors:
                    raise RuntimeError("任务成功但未解析到图片")
                pbar.update_absolute(100)
                return torch.cat(tensors, dim=0), first_url, task_id, status_data

            if status == "FAILURE":
                fail_reason = inner.get("fail_reason", "Unknown error")
                raise RuntimeError(f"任务失败: {fail_reason}")

        raise RuntimeError(f"轮询超过 {max_poll_attempts} 次仍未完成")

    def _build_info(self, api_source, prompt, quality, size, background, output_format, output_compression, moderation, image_url="", task_id="", final_result=None, async_mode=True):
        mode_text = "异步官方编辑" if async_mode else "同步官方编辑"
        info = f"模式: {mode_text}\n"
        info += f"线路: {api_source}\n"
        info += "模型: gpt-image-2\n"
        info += f"提示词: {prompt}\n"
        info += f"画质: {quality}\n"
        if size != "auto":
            info += f"尺寸: {size}\n"
        if background != "auto":
            info += f"背景: {background}\n"
        info += f"输出格式: {output_format}\n"
        info += f"压缩质量: {output_compression}\n"
        info += f"审核强度: {moderation}\n"
        if task_id:
            info += f"任务ID: {task_id}\n"
        if image_url:
            info += f"图片链接: {image_url}\n"
        if final_result:
            inner = final_result.get("data", {}) if isinstance(final_result, dict) else {}
            inner_data = inner.get("data", {}) if isinstance(inner, dict) else {}
            if isinstance(inner_data, dict) and "usage" in inner_data:
                usage = inner_data["usage"]
                info += f"总Tokens: {usage.get('total_tokens', 'N/A')}\n"
        return info.strip()

    def generate(self, **kwargs):
        api_source = kwargs.get("🌐 API线路", "柏拉图")
        prompt = kwargs.get("📝 提示词", "")
        image = kwargs.get("🖼️ 图像")
        mask = kwargs.get("🎭 遮罩")
        api_key = kwargs.get("🔑 API密钥", "")
        n = int(kwargs.get("🖼️ 图片数量", 1))
        quality = kwargs.get("🎨 画质", "auto")
        size = kwargs.get("📐 尺寸", "auto")
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
        custom_api_url = kwargs.get("🔗 自定义API地址", "")

        if api_key.strip():
            self.api_key = api_key.strip()

        blank_tensor = self._blank_tensor()
        if not self.api_key:
            return (blank_tensor, "", "API密钥为空，请填写后再试")

        valid, error_message = self._validate_size(size)
        if not valid:
            return (blank_tensor, "", error_message)

        base_url = self._get_base_url(api_source, custom_api_url)
        pbar = comfy.utils.ProgressBar(100)
        pbar.update_absolute(5)

        try:
            if async_mode:
                combined, image_url, task_id, final_result = self._async_edits(
                    base_url,
                    prompt,
                    image,
                    mask,
                    pbar,
                    max_poll_attempts,
                    poll_interval,
                    webhook,
                    n,
                    quality,
                    size,
                    background,
                    output_format,
                    output_compression,
                    moderation,
                    max_retries,
                    initial_timeout,
                )
                info = self._build_info(
                    api_source, prompt, quality, size, background, output_format,
                    output_compression, moderation, image_url, task_id, final_result, True
                )
                return (combined, image_url, info)

            data, request_files = self._build_edits_multipart(
                prompt, image, mask, n, quality, size, background,
                output_format, output_compression, moderation,
            )
            response = self._make_request_with_retry(
                f"{base_url}/v1/images/edits",
                data=data,
                files=request_files,
                max_retries=max_retries,
                initial_timeout=initial_timeout,
            )
            result = response.json()
            if "data" not in result or not result["data"]:
                return (blank_tensor, "", f"返回中没有图片数据: {result}")
            tensors = self._items_to_tensors(result, max_retries, initial_timeout)
            if not tensors:
                return (blank_tensor, "", "未能解析返回图片")
            combined = torch.cat(tensors, dim=0)
            pbar.update_absolute(100)
            first_url = ""
            for item in result.get("data", []) or []:
                if item.get("url"):
                    first_url = item["url"]
                    break
            info = self._build_info(
                api_source, prompt, quality, size, background, output_format,
                output_compression, moderation, first_url, "", result, False
            )
            return (combined, first_url, info)
        except Exception as e:
            return (blank_tensor, "", f"执行失败: {str(e)}")


NODE_CLASS_MAPPINGS = {
    "🙅GPT_image_2_官方稳定@炮老师的小课堂": DapaoGPTImage2OfficialStableNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "🙅GPT_image_2_官方稳定@炮老师的小课堂": "🙅GPT_image_2_官方稳定@炮老师的小课堂",
}
