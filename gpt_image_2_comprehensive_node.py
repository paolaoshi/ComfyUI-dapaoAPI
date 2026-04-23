import math
import time
import json
import base64
import re
import torch
import requests
import numpy as np
from io import BytesIO
from PIL import Image
import comfy.utils
from comfy.utils import common_upscale


def tensor2pil(image):
    return [Image.fromarray(np.clip(255.0 * img.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)) for img in image]


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


class DapaoGPTImage2ComprehensiveNode:
    _last_generated_image_urls = ""
    _conversation_history = []

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🌐 API线路": (["柏拉图", "zhenzhen", "hk", "us", "ip"], {
                    "default": "柏拉图",
                    "tooltip": "选择 API 线路：柏拉图 / zhenzhen / hk / us / ip(自定义地址)"
                }),
                "📝 提示词": ("STRING", {"multiline": True, "default": ""}),
                "🔑 API密钥": ("STRING", {"default": "", "multiline": False}),
                "🤖 模型": (["gpt-image-2"], {"default": "gpt-image-2"}),
                "🎨 画质": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "📐 尺寸": (["auto", "1024x1024", "1536x1024", "1024x1536"], {"default": "auto"}),
                "🌈 背景": (["auto", "transparent", "opaque"], {"default": "auto"}),
                "📦 输出格式": (["png", "jpeg", "webp"], {"default": "png"}),
                "🛡️ 审核强度": (["auto", "low"], {"default": "auto"}),
                "🎲 种子": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": "randomize"}),
                "🧹 清空对话": ("BOOLEAN", {"default": True}),
                "⏱️ 图片下载超时": ("INT", {"default": 600, "min": 60, "max": 1200, "step": 10}),
            },
            "optional": {
                "🔗 自定义API地址": ("STRING", {"default": "", "placeholder": "当 API线路 选 ip 时填写完整地址"}),
                "🖼️ 参考图1": ("IMAGE",),
                "🖼️ 参考图2": ("IMAGE",),
                "🖼️ 参考图3": ("IMAGE",),
                "🖼️ 参考图4": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "📋 响应信息", "🔗 图片链接", "💬 对话记录")
    FUNCTION = "process"
    CATEGORY = "🤖dapaoAPI/GPT"
    DESCRIPTION = "GPT Image 2 综合版 @炮老师的小课堂"

    def __init__(self):
        self.timeout = 900
        self.image_download_timeout = 600

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

    def _get_headers(self, api_key):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def _image_to_base64(self, pil_image):
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def _download_image(self, url, timeout=30):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            }
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))
            return pil2tensor(image)
        except Exception as e:
            print(f"[dapaoAPI] 下载图片失败 {url}: {e}")
            return None

    def _extract_image_urls(self, response_text):
        image_pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(image_pattern, response_text)
        if not matches:
            url_pattern = r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)'
            matches = re.findall(url_pattern, response_text)
        if not matches:
            all_urls_pattern = r'https?://\S+'
            matches = re.findall(all_urls_pattern, response_text)
        seen = set()
        result = []
        for item in matches:
            if item not in seen:
                seen.add(item)
                result.append(item)
        return result

    def _format_conversation_history(self):
        if not DapaoGPTImage2ComprehensiveNode._conversation_history:
            return ""
        formatted = []
        for entry in DapaoGPTImage2ComprehensiveNode._conversation_history:
            formatted.append(f"**用户**: {entry['user']}")
            formatted.append(f"**系统**: {entry['ai']}")
            formatted.append("---")
        return "\n\n".join(formatted).strip()

    def _send_request(self, api_key, base_url, payload):
        full_response = ""
        payload["stream"] = True
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            headers=self._get_headers(api_key),
            json=payload,
            stream=True,
            timeout=self.timeout,
        )
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            line_text = line.decode("utf-8").strip()
            if not line_text.startswith("data: "):
                continue
            data = line_text[6:]
            if data == "[DONE]":
                break
            try:
                chunk = json.loads(data)
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        full_response += delta["content"]
            except json.JSONDecodeError:
                continue
        return full_response

    def process(self, **kwargs):
        api_source = kwargs.get("🌐 API线路", "柏拉图")
        prompt = kwargs.get("📝 提示词", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model = kwargs.get("🤖 模型", "gpt-image-2")
        quality = kwargs.get("🎨 画质", "auto")
        size = kwargs.get("📐 尺寸", "auto")
        background = kwargs.get("🌈 背景", "auto")
        output_format = kwargs.get("📦 输出格式", "png")
        moderation = kwargs.get("🛡️ 审核强度", "auto")
        seed = kwargs.get("🎲 种子", 0)
        clear_chats = bool(kwargs.get("🧹 清空对话", True))
        self.image_download_timeout = int(kwargs.get("⏱️ 图片下载超时", 600))
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        input_images = [kwargs.get(f"🖼️ 参考图{i}") for i in range(1, 5)]

        blank_img = Image.new("RGB", (1024, 1024), color="white")
        blank_tensor = pil2tensor(blank_img)

        if clear_chats:
            DapaoGPTImage2ComprehensiveNode._conversation_history = []

        if not api_key.strip():
            return (blank_tensor, "API密钥为空，请填写后再试", "", self._format_conversation_history())

        try:
            base_url = self._get_base_url(api_source, custom_api_url)
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

            content = [{"type": "text", "text": prompt}]

            if not clear_chats and DapaoGPTImage2ComprehensiveNode._last_generated_image_urls:
                prev_image_url = DapaoGPTImage2ComprehensiveNode._last_generated_image_urls.split("\n")[0].strip()
                if prev_image_url:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": prev_image_url}
                    })
            else:
                for img in input_images:
                    if img is not None:
                        scaled = downscale_input(img[0:1])
                        pil_image = tensor2pil(scaled)[0]
                        image_base64 = self._image_to_base64(pil_image)
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        })

            messages = [{"role": "user", "content": content}]
            payload = {
                "model": model,
                "messages": messages,
            }
            if seed > 0:
                payload["seed"] = seed

            pbar.update_absolute(20)
            response_text = self._send_request(api_key, base_url, payload)
            pbar.update_absolute(50)

            DapaoGPTImage2ComprehensiveNode._conversation_history.append({
                "user": prompt,
                "ai": response_text,
            })

            response_info = (
                f"模型: {model}\n"
                f"线路: {api_source}\n"
                f"画质: {quality}\n"
                f"尺寸: {size}\n"
                f"背景: {background}\n"
                f"输出格式: {output_format}\n"
                f"审核强度: {moderation}\n"
                f"种子: {seed if seed > 0 else 'auto'}\n"
                f"时间: {timestamp}"
            )

            image_urls = self._extract_image_urls(response_text)
            image_urls_string = "\n".join(image_urls) if image_urls else ""
            if image_urls_string:
                DapaoGPTImage2ComprehensiveNode._last_generated_image_urls = image_urls_string

            chat_history = self._format_conversation_history()

            if image_urls:
                tensors = []
                for index, url in enumerate(image_urls):
                    pbar.update_absolute(min(90, 50 + (index + 1) * 40 // len(image_urls)))
                    tensor = self._download_image(url, self.image_download_timeout)
                    if tensor is not None:
                        tensors.append(tensor)
                if tensors:
                    combined_tensor = torch.cat(tensors, dim=0)
                    pbar.update_absolute(100)
                    return (combined_tensor, response_info, image_urls_string, chat_history)

            first_image = next((img for img in input_images if img is not None), None)
            if first_image is not None:
                pbar.update_absolute(100)
                return (first_image, response_info, image_urls_string, chat_history)

            pbar.update_absolute(100)
            return (blank_tensor, response_info, image_urls_string, chat_history)
        except Exception as e:
            error_message = f"执行失败: {str(e)}"
            print(f"[dapaoAPI] {error_message}")
            DapaoGPTImage2ComprehensiveNode._conversation_history.append({"user": prompt, "ai": error_message})
            first_image = next((img for img in input_images if img is not None), None)
            if first_image is not None:
                return (first_image, error_message, "", self._format_conversation_history())
            return (blank_tensor, error_message, "", self._format_conversation_history())


NODE_CLASS_MAPPINGS = {
    "🙅GPT_image_2_综合@炮老师的小课堂": DapaoGPTImage2ComprehensiveNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "🙅GPT_image_2_综合@炮老师的小课堂": "🙅GPT_image_2_综合@炮老师的小课堂",
}
