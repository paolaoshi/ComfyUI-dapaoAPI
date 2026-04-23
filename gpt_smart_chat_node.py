import base64
import json
from io import BytesIO

import numpy as np
import requests
from PIL import Image


def tensor2base64(image_tensor):
    image = np.clip(255.0 * image_tensor.cpu().numpy(), 0, 255).astype(np.uint8)
    pil_image = Image.fromarray(image)
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class DapaoGPTSmartChatNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "你是一个专业、友好、乐于助人的 AI 助手，能够结合用户提供的文字与图像进行准确分析和回答。",
                    "placeholder": "定义 AI 的角色和行为方式..."
                }),
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "请根据我提供的内容进行分析并给出详细回答。",
                    "placeholder": "输入你的问题或指令..."
                }),
                "🤖 模型": ("STRING", {
                    "default": "gpt-5.4-mini",
                    "multiline": False,
                    "placeholder": "手动输入模型名称"
                }),
                "🌐 API线路": (["柏拉图", "zhenzhen", "hk", "us", "ip"], {
                    "default": "柏拉图",
                    "tooltip": "选择 API 线路：柏拉图 / zhenzhen / hk / us / ip(自定义地址)"
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "请输入 API 密钥"
                }),
                "📊 输出语言": (["中文", "英文"], {
                    "default": "中文"
                }),
            },
            "optional": {
                "🔗 自定义API地址": ("STRING", {
                    "default": "",
                    "placeholder": "当 API线路 选 ip 时填写完整地址"
                }),
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🌡️ 温度": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01
                }),
                "🎲 Top_P": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "📝 最大令牌": ("INT", {
                    "default": 4096,
                    "min": 1,
                    "max": 65536
                }),
                "⏱️ 超时时间": ("INT", {
                    "default": 180,
                    "min": 30,
                    "max": 1200,
                    "step": 10
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "📄 完整响应", "ℹ️ 处理信息")
    FUNCTION = "chat"
    CATEGORY = "🤖dapaoAPI/GPT"
    DESCRIPTION = "GPT 智能对话 @炮老师的小课堂"
    OUTPUT_NODE = False

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

    def _build_messages(self, system_role, user_input, images, language):
        language_instruction = "请用中文回答。" if language == "中文" else "Please answer in English."
        messages = []
        system_text = (system_role or "").strip()
        if system_text:
            messages.append({
                "role": "system",
                "content": f"{system_text}\n\n{language_instruction}"
            })

        content = [{"type": "text", "text": user_input or ""}]
        for image in images:
            if image is None:
                continue
            batch_size = image.shape[0]
            for index in range(batch_size):
                image_base64 = tensor2base64(image[index])
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                })

        messages.append({
            "role": "user",
            "content": content
        })
        return messages

    def _extract_text(self, result):
        choices = result.get("choices", [])
        if not choices:
            return ""
        message = choices[0].get("message", {})
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text" and item.get("text"):
                        texts.append(item["text"])
                    elif "text" in item and item["text"]:
                        texts.append(item["text"])
            return "\n".join(texts)
        return str(content)

    def chat(self, **kwargs):
        system_role = kwargs.get("🎯 系统角色", "")
        user_input = kwargs.get("💬 用户输入", "")
        model = kwargs.get("🤖 模型", "gpt-5.4-mini")
        api_source = kwargs.get("🌐 API线路", "柏拉图")
        api_key = kwargs.get("🔑 API密钥", "")
        language = kwargs.get("📊 输出语言", "中文")
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        temperature = kwargs.get("🌡️ 温度", 0.7)
        top_p = kwargs.get("🎲 Top_P", 0.9)
        max_tokens = kwargs.get("📝 最大令牌", 4096)
        timeout = int(kwargs.get("⏱️ 超时时间", 180))
        images = [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 5) if kwargs.get(f"🖼️ 图像{i}") is not None]

        if not api_key.strip():
            return ("", "", "API密钥为空，请填写后再试")

        base_url = self._get_base_url(api_source, custom_api_url)
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model,
            "messages": self._build_messages(system_role, user_input, images, language),
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
        }

        try:
            response = requests.post(
                f"{base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()
            result = response.json()
            response_text = self._extract_text(result)
            info = (
                f"模型: {model}\n"
                f"线路: {api_source}\n"
                f"图像数量: {len(images)}\n"
                f"输出语言: {language}\n"
                f"最大令牌: {max_tokens}"
            )
            return (response_text, json.dumps(result, ensure_ascii=False, indent=2), info)
        except Exception as e:
            return ("", "", f"执行失败: {str(e)}")


NODE_CLASS_MAPPINGS = {
    "🙅GPT智能对话@炮老师的小课堂": DapaoGPTSmartChatNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "🙅GPT智能对话@炮老师的小课堂": "🙅GPT智能对话@炮老师的小课堂",
}
