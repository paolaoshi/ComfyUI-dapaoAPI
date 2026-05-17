"""
通用图像生成（文生图）节点

按 OpenAI 兼容的 /images/generations 接口调用文生图模型。
作者：@炮老师的小课堂
"""

import base64
import io
import json
import time
import traceback

import numpy as np
import requests
import torch
from PIL import Image


NODE_NAME = "DapaoUniversalTextToImageNode"


def _log_info(message):
    print(f"[dapaoAPI-通用文生图] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-通用文生图] 错误：{message}")


def pil2tensor(image: Image.Image) -> torch.Tensor:
    if image.mode != "RGB":
        image = image.convert("RGB")
    np_image = np.array(image).astype(np.float32) / 255.0
    return torch.from_numpy(np_image).unsqueeze(0)


def create_blank_tensor(width=1024, height=1024):
    blank_image = np.zeros((height, width, 3), dtype=np.float32)
    return torch.from_numpy(blank_image).unsqueeze(0)


class DapaoUniversalTextToImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "一只可爱的小猫，坐在窗台上，阳光洒在它身上，高清摄影",
                    "placeholder": "请输入要生成的图像描述..."
                }),
                "🌐 API地址": ("STRING", {
                    "default": "https://api.openai.com/v1/images/generations",
                    "placeholder": "请输入完整接口地址，如 https://xxx/v1/images/generations"
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "请输入 API Key"
                }),
                "🤖 模型ID": ("STRING", {
                    "default": "gpt-image-1",
                    "placeholder": "请输入模型 ID，如 gpt-image-1、dall-e-3 等"
                }),
                "📐 图片尺寸": ([
                    "1024x1024",
                    "1024x1536",
                    "1536x1024",
                    "512x512",
                    "768x768",
                    "自定义"
                ], {
                    "default": "1024x1024"
                }),
                "◀️ 自定义宽度": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 4096,
                    "step": 64,
                    "display": "number"
                }),
                "▲ 自定义高度": ("INT", {
                    "default": 1024,
                    "min": 64,
                    "max": 4096,
                    "step": 64,
                    "display": "number"
                }),
                "📸 出图数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "step": 1
                }),
                "📦 返回格式": (["url", "b64_json"], {
                    "default": "url"
                }),
            },
            "optional": {
                "📋 额外Body字段": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "JSON格式，如 {\"quality\": \"hd\", \"style\": \"vivid\"}"
                }),
                "⏱️ 超时时间": ("INT", {
                    "default": 180,
                    "min": 10,
                    "max": 600,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "ℹ️ 信息", "📄 原始JSON")
    FUNCTION = "generate_image"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "通用图像生成（文生图），兼容 OpenAI 风格 /images/generations 接口 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False

    def generate_image(self, **kwargs):
        prompt = kwargs.get("📝 提示词", "").strip()
        api_url = kwargs.get("🌐 API地址", "").strip()
        api_key = kwargs.get("🔑 API密钥", "").strip()
        model_id = kwargs.get("🤖 模型ID", "").strip()
        size = kwargs.get("📐 图片尺寸", "1024x1024")
        custom_width = kwargs.get("◀️ 自定义宽度", 1024)
        custom_height = kwargs.get("▲ 自定义高度", 1024)
        num_images = kwargs.get("📸 出图数量", 1)
        response_format = kwargs.get("📦 返回格式", "url")
        extra_body_str = kwargs.get("📋 额外Body字段", "{}")
        timeout = kwargs.get("⏱️ 超时时间", 180)

        if not prompt:
            error_msg = "❌ 错误：提示词不能为空"
            return (create_blank_tensor(), error_msg, "{}")

        if not api_url.startswith(("http://", "https://")):
            error_msg = "❌ 错误：请输入有效的 API 地址，需要以 http:// 或 https:// 开头"
            return (create_blank_tensor(), error_msg, "{}")

        if not api_key:
            error_msg = "❌ 错误：请输入 API 密钥"
            return (create_blank_tensor(), error_msg, "{}")

        if not model_id:
            error_msg = "❌ 错误：请输入模型 ID"
            return (create_blank_tensor(), error_msg, "{}")

        final_size = f"{custom_width}x{custom_height}" if size == "自定义" else size
        start_time = time.time()

        try:
            extra_body = json.loads(extra_body_str or "{}")
            if not isinstance(extra_body, dict):
                raise ValueError("额外Body字段必须是 JSON 对象")
        except Exception as e:
            error_msg = f"❌ 错误：额外Body字段不是有效 JSON 对象\n\n详情：{e}"
            return (create_blank_tensor(), error_msg, "{}")

        payload = {
            "model": model_id,
            "prompt": prompt,
            "size": final_size,
            "n": num_images,
            "response_format": response_format,
        }
        payload.update(extra_body)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "ComfyUI-dapaoAPI/UniversalTextToImage"
        }

        try:
            _log_info(f"开始请求：{api_url}")
            _log_info(f"模型：{model_id}，尺寸：{final_size}，数量：{num_images}，返回格式：{response_format}")

            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            raw_text = response.text

            if response.status_code != 200:
                error_msg = f"❌ 错误：API 请求失败\n\n状态码：{response.status_code}\n响应：{raw_text[:500]}"
                _log_error(error_msg)
                return (create_blank_tensor(), error_msg, raw_text or "{}")

            try:
                result = response.json()
                raw_json = json.dumps(result, ensure_ascii=False, indent=2)
            except Exception:
                error_msg = f"❌ 错误：API 返回内容不是 JSON\n\n响应：{raw_text[:500]}"
                return (create_blank_tensor(), error_msg, raw_text or "{}")

            image_tensors = []
            image_errors = []
            data_items = result.get("data", [])

            if isinstance(data_items, dict):
                data_items = [data_items]

            for index, item in enumerate(data_items, start=1):
                try:
                    image = self._image_from_item(item, timeout)
                    if image is None:
                        image_errors.append(f"第 {index} 张：未找到 url 或 b64_json")
                        continue
                    image_tensors.append(pil2tensor(image))
                    _log_info(f"第 {index} 张图片解析成功：{image.size}")
                except Exception as e:
                    image_errors.append(f"第 {index} 张：{e}")

            if not image_tensors:
                error_msg = "❌ 错误：API 请求成功，但没有解析到图片\n\n请确认接口返回 data[].url 或 data[].b64_json"
                if image_errors:
                    error_msg += "\n\n解析详情：\n" + "\n".join(image_errors)
                return (create_blank_tensor(), error_msg, raw_json)

            final_tensor = image_tensors[0] if len(image_tensors) == 1 else torch.cat(image_tensors, dim=0)
            elapsed_time = time.time() - start_time

            info_lines = [
                f"✅ 成功生成 {len(image_tensors)}/{num_images} 张图像",
                f"🤖 模型：{model_id}",
                f"📐 尺寸：{final_size}",
                f"📦 返回格式：{response_format}",
                f"⏱️ 耗时：{elapsed_time:.2f} 秒",
            ]
            if image_errors:
                info_lines.append("⚠️ 部分图片解析失败：")
                info_lines.extend(image_errors)

            return (final_tensor, "\n".join(info_lines), raw_json)

        except Exception as e:
            error_msg = f"❌ 错误：图像生成失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            return (create_blank_tensor(), error_msg, "{}")

    def _image_from_item(self, item, timeout):
        if not isinstance(item, dict):
            return None

        image_url = item.get("url")
        if image_url:
            image_response = requests.get(image_url, timeout=timeout)
            if image_response.status_code != 200:
                raise RuntimeError(f"图片下载失败，状态码：{image_response.status_code}")
            return Image.open(io.BytesIO(image_response.content)).convert("RGB")

        b64_data = item.get("b64_json") or item.get("base64")
        if b64_data:
            if "," in b64_data and b64_data.strip().startswith("data:"):
                b64_data = b64_data.split(",", 1)[1]
            image_bytes = base64.b64decode(b64_data)
            return Image.open(io.BytesIO(image_bytes)).convert("RGB")

        return None


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoUniversalTextToImageNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "通用图像生成(文生图)@炮老师的小课堂"
}
