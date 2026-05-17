"""
GPT-image2 官方账号出图节点

使用 OpenAI 官方 /v1/images/generations 和 /v1/images/edits 接口调用 gpt-image-2 生成、编辑图片。
作者：@炮老师的小课堂
"""

import base64
import io
import json
import re
import time
import traceback

import numpy as np
import requests
import torch
from PIL import Image


NODE_NAME = "DapaoGPTImage2OfficialAccountNode"


class DapaoGPTImage2OfficialAccountNode:
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

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 OpenAI官方API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "填入 sk- 开头的 OpenAI 官方 API Key",
                    "tooltip": "只用于本次请求，不会写入文件。"
                }),
                "📝 生图提示词": ("STRING", {
                    "multiline": True,
                    "default": "一只可爱的小猫坐在窗边，温暖阳光，电影感摄影，高清细节",
                    "placeholder": "请描述你想生成的图片内容...",
                    "tooltip": "提示词不能为空，建议写清主体、风格、场景、光线和画幅。"
                }),
                "📐 图片尺寸": (cls._SIZE_CHOICES, {
                    "default": "1024x1024",
                    "tooltip": "gpt-image-2 支持 auto、1024、2K、4K 等尺寸；4K 可能更慢且费用更高。"
                }),
                "🎨 画质": (["auto", "low", "medium", "high"], {
                    "default": "auto",
                    "tooltip": "low 更快更省，high 更精细但更慢。"
                }),
                "🌈 背景": (["auto", "opaque"], {
                    "default": "auto",
                    "tooltip": "gpt-image-2 暂不支持 transparent 透明背景，所以这里只提供 auto/opaque。"
                }),
                "📦 输出格式": (["png", "jpeg", "webp"], {
                    "default": "png",
                    "tooltip": "png 质量稳定；jpeg/webp 可配合压缩质量。"
                }),
                "🛡️ 审核强度": (["auto", "low"], {
                    "default": "auto",
                    "tooltip": "auto 为标准审核；low 为较低审核强度。"
                }),
            },
            "optional": {
                "🗜️ 压缩质量": ("INT", {
                    "default": 100,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "仅 jpeg/webp 有效；png 会自动忽略。"
                }),
                "🌐 代理地址": ("STRING", {
                    "default": "",
                    "placeholder": "可选，如 http://127.0.0.1:7890",
                    "tooltip": "如果你的网络无法直连 OpenAI，可填写代理地址。"
                }),
                "⏱️ 超时时间": ("INT", {
                    "default": 180,
                    "min": 30,
                    "max": 600,
                    "step": 1,
                    "tooltip": "复杂图片可能需要较长时间，官方文档提示可能接近 2 分钟。"
                }),
                "♻️ 重试次数": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "tooltip": "仅网络错误、超时、429 或 5xx 会重试。"
                }),
                "🖼️ 图像": ("IMAGE", {
                    "tooltip": "可选：接入 ComfyUI 原生加载图像后，会自动切换为图像编辑模式。"
                }),
                "🎭 蒙版": ("MASK", {
                    "tooltip": "可选：需要同时接入图像；接入后会自动使用官方蒙版编辑。"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "ℹ️ 生成信息", "📄 原始JSON")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/🐦‍🔥GPT&gemini&即梦最新稳定🐦‍🔥"
    DESCRIPTION = "GPT-image2官方账号出图：使用 OpenAI 官方 API 调用 gpt-image-2 文生图、图像编辑和蒙版编辑 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _pil2tensor(image):
        if image.mode != "RGB":
            image = image.convert("RGB")
        np_image = np.array(image).astype(np.float32) / 255.0
        return torch.from_numpy(np_image).unsqueeze(0)

    @staticmethod
    def _parse_size_wh(size_str):
        match = re.match(r"^(\d+)x(\d+)$", size_str.strip())
        if not match:
            return None, None
        return int(match.group(1)), int(match.group(2))

    @classmethod
    def _validate_size(cls, size_str):
        if size_str == "auto":
            return
        width, height = cls._parse_size_wh(size_str)
        if width is None:
            raise ValueError("图片尺寸格式不正确，应为 宽x高，例如 1024x1024。")
        if max(width, height) > 3840:
            raise ValueError("图片尺寸不合法：长边必须小于或等于 3840px。")
        if width % 16 != 0 or height % 16 != 0:
            raise ValueError("图片尺寸不合法：宽和高都必须是 16 的倍数。")
        short_edge, long_edge = min(width, height), max(width, height)
        if long_edge / short_edge > 3.0 + 1e-9:
            raise ValueError("图片尺寸不合法：长边和短边比例不能超过 3:1。")
        pixels = width * height
        if pixels < 655360 or pixels > 8294400:
            raise ValueError("图片尺寸不合法：总像素必须在 655,360 到 8,294,400 之间。")

    @staticmethod
    def _raise_for_response(response):
        if response.status_code == 200:
            return

        message = response.text[:1000]
        try:
            data = response.json()
            error = data.get("error", {}) if isinstance(data, dict) else {}
            if isinstance(error, dict):
                message = error.get("message") or error.get("code") or message
        except Exception:
            pass

        status = response.status_code
        if status == 400:
            raise RuntimeError(f"OpenAI 参数错误 400：请检查提示词、尺寸、画质、背景或输出格式。接口返回：{message}")
        if status == 401:
            raise RuntimeError(f"OpenAI 认证失败 401：API Key 无效、过期或没有权限。接口返回：{message}")
        if status == 403:
            raise RuntimeError(f"OpenAI 权限不足 403：账号可能未完成组织验证，或没有 gpt-image-2 权限。接口返回：{message}")
        if status == 429:
            raise RuntimeError(f"OpenAI 请求过多 429：额度不足、限速或并发过高，请稍后再试。接口返回：{message}")
        if status >= 500:
            raise RuntimeError(f"OpenAI 服务异常 {status}：官方服务暂时不可用，请稍后重试。接口返回：{message}")
        raise RuntimeError(f"OpenAI 请求失败 {status}：{message}")

    @staticmethod
    def _should_retry(exc):
        if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return True
        response = getattr(exc, "response", None)
        if response is not None:
            return response.status_code == 429 or response.status_code >= 500
        text = str(exc)
        return "429" in text or "服务异常" in text

    def _post_with_retry(self, url, headers, payload, timeout, retry_count, proxies):
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout, proxies=proxies)
                self._raise_for_response(response)
                return response
            except Exception as e:
                last_error = e
                if attempt >= retry_count or not self._should_retry(e):
                    raise
                time.sleep(min(2 ** attempt, 8))
        raise last_error

    def _post_multipart_with_retry(self, url, headers, data, files, timeout, retry_count, proxies):
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                response = requests.post(url, headers=headers, data=data, files=files, timeout=timeout, proxies=proxies)
                self._raise_for_response(response)
                return response
            except Exception as e:
                last_error = e
                if attempt >= retry_count or not self._should_retry(e):
                    raise
                time.sleep(min(2 ** attempt, 8))
        raise last_error

    @staticmethod
    def _tensor_image_to_png_file(image):
        image_np = np.clip(image[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image_np).convert("RGB")
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @staticmethod
    def _mask_to_png_file(mask):
        mask_np = np.clip(mask[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        alpha_np = 255 - mask_np
        mask_image = Image.fromarray(mask_np, mode="L").convert("RGBA")
        mask_image.putalpha(Image.fromarray(alpha_np, mode="L"))
        buffer = io.BytesIO()
        mask_image.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    def _image_from_item(self, item, timeout, proxies):
        if not isinstance(item, dict):
            raise RuntimeError("接口返回的图片条目格式不正确。")

        b64_data = item.get("b64_json") or item.get("base64")
        if b64_data:
            if b64_data.strip().startswith("data:") and "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            try:
                image_bytes = base64.b64decode(b64_data)
                return Image.open(io.BytesIO(image_bytes)).convert("RGB")
            except Exception as e:
                raise RuntimeError(f"图片 base64 解码失败：{e}")

        image_url = item.get("url")
        if image_url:
            try:
                image_response = requests.get(image_url, timeout=timeout, proxies=proxies)
                if image_response.status_code != 200:
                    raise RuntimeError(f"图片下载失败，状态码：{image_response.status_code}")
                return Image.open(io.BytesIO(image_response.content)).convert("RGB")
            except Exception as e:
                raise RuntimeError(f"图片链接下载失败：{e}")

        raise RuntimeError("接口返回成功，但没有找到 b64_json 或 url 图片字段。")

    def generate(self, **kwargs):
        api_key = kwargs.get("🔑 OpenAI官方API密钥", "").strip()
        prompt = kwargs.get("📝 生图提示词", "").strip()
        size = kwargs.get("📐 图片尺寸", "1024x1024")
        quality = kwargs.get("🎨 画质", "auto")
        background = kwargs.get("🌈 背景", "auto")
        output_format = kwargs.get("📦 输出格式", "png")
        moderation = kwargs.get("🛡️ 审核强度", "auto")
        output_compression = int(kwargs.get("🗜️ 压缩质量", 100))
        proxy_url = kwargs.get("🌐 代理地址", "").strip()
        timeout = int(kwargs.get("⏱️ 超时时间", 180))
        retry_count = int(kwargs.get("♻️ 重试次数", 2))
        image_input = kwargs.get("🖼️ 图像")
        mask_input = kwargs.get("🎭 蒙版")

        if not api_key:
            raise ValueError("请填写 🔑 OpenAI官方API密钥。")
        if not prompt:
            raise ValueError("请填写 📝 生图提示词，不能为空。")
        if mask_input is not None and image_input is None:
            raise ValueError("使用 🎭 蒙版 时必须同时接入 🖼️ 图像，否则无法进行蒙版编辑。")
        if image_input is not None and mask_input is not None and image_input.shape[1:3] != mask_input.shape[1:3]:
            raise ValueError("🎭 蒙版尺寸必须和 🖼️ 图像尺寸一致。")
        self._validate_size(size)

        proxies = {"http": proxy_url, "https": proxy_url} if proxy_url else None
        start_time = time.time()
        mode_text = "🎨 文生图"

        try:
            if image_input is None:
                payload = {
                    "model": "gpt-image-2",
                    "prompt": prompt,
                    "quality": quality,
                    "background": background,
                    "output_format": output_format,
                    "moderation": moderation,
                }
                if size != "auto":
                    payload["size"] = size
                if output_format in ("jpeg", "webp") and output_compression != 100:
                    payload["output_compression"] = output_compression

                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "ComfyUI-dapaoAPI/GPTImage2OfficialAccount",
                }
                response = self._post_with_retry(
                    "https://api.openai.com/v1/images/generations",
                    headers,
                    payload,
                    timeout,
                    retry_count,
                    proxies,
                )
            else:
                mode_text = "🖼️ 图像编辑" if mask_input is None else "🎭 蒙版编辑"
                data = {
                    "model": "gpt-image-2",
                    "prompt": prompt,
                    "quality": quality,
                    "background": background,
                    "output_format": output_format,
                    "moderation": moderation,
                }
                if size != "auto":
                    data["size"] = size
                if output_format in ("jpeg", "webp") and output_compression != 100:
                    data["output_compression"] = str(output_compression)

                image_file = self._tensor_image_to_png_file(image_input)
                files = [("image", ("image.png", image_file, "image/png"))]
                if mask_input is not None:
                    mask_file = self._mask_to_png_file(mask_input)
                    files.append(("mask", ("mask.png", mask_file, "image/png")))

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "ComfyUI-dapaoAPI/GPTImage2OfficialAccount",
                }
                response = self._post_multipart_with_retry(
                    "https://api.openai.com/v1/images/edits",
                    headers,
                    data,
                    files,
                    timeout,
                    retry_count,
                    proxies,
                )

            result = response.json()
        except requests.exceptions.ProxyError as e:
            raise RuntimeError(f"代理连接失败：请检查 🌐 代理地址 是否正确。详情：{e}")
        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"请求超时：OpenAI 在 {timeout} 秒内没有返回，请增大超时时间或稍后重试。详情：{e}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"网络连接失败：请检查网络、代理或防火墙。详情：{e}")
        except json.JSONDecodeError:
            raise RuntimeError(f"OpenAI 返回内容不是 JSON：{response.text[:1000]}")
        except Exception:
            traceback.print_exc()
            raise

        data_items = result.get("data", [])
        if isinstance(data_items, dict):
            data_items = [data_items]
        if not data_items:
            raise RuntimeError(f"OpenAI 返回成功，但 data 为空，没有图片数据。原始返回：{json.dumps(result, ensure_ascii=False)[:1000]}")

        image = self._image_from_item(data_items[0], timeout, proxies)
        elapsed_time = time.time() - start_time
        raw_json = json.dumps(result, ensure_ascii=False, indent=2)
        revised_prompt = data_items[0].get("revised_prompt", "") if isinstance(data_items[0], dict) else ""

        info_lines = [
            "✅ GPT-image2 官方账号出图成功",
            f"🔀 模式：{mode_text}",
            "🤖 模型：gpt-image-2",
            f"📐 尺寸：{size}",
            f"🎨 画质：{quality}",
            f"🌈 背景：{background}",
            f"📦 输出格式：{output_format}",
            f"🛡️ 审核强度：{moderation}",
            f"⏱️ 耗时：{elapsed_time:.2f} 秒",
        ]
        if revised_prompt:
            info_lines.append(f"🪄 官方改写提示词：{revised_prompt}")
        if len(data_items) > 1:
            info_lines.append("⚠️ 接口返回了多张图，本节点仅使用第一张。")

        return (self._pil2tensor(image), "\n".join(info_lines), raw_json)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoGPTImage2OfficialAccountNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🦖GPT-image2官方账号出图",
}
