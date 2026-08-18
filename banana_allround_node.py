"""Banana all-round image node for the dapaoAI relay.

The implementation is self-contained so it can survive removal of any legacy
Banana or GPT Image nodes.  The relay model IDs deliberately remain in the
Gemini-native URL; upstream provider names are documentation references only.
"""

import base64
import asyncio
import io
import json
import re
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import requests
import torch
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error
from .image_input_utils import IMAGE_429_HINT, tensor_to_png_inline_parts

try:
    import comfy.model_management
    import comfy.utils
except Exception:
    comfy = None


API_BASE_URL = "https://api.dapaoai.com"
NODE_NAME = "DapaoBananaAllroundNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
DISPLAY_NAME = "🐠香蕉-banana全能图像@炮老师的小课堂"

BANANA_PRO_OFFICIAL_LABEL = "香蕉pro官方稳定版"
BANANA_2_OFFICIAL_LABEL = "香蕉2官方稳定版"
MODEL_OPTIONS = ["bananaPRO", "bannana-2", BANANA_PRO_OFFICIAL_LABEL, BANANA_2_OFFICIAL_LABEL]
PRICE_BY_MODEL = {"bananaPRO": 0.20, "bannana-2": 0.15}
MODEL_ID_BY_RESOLUTION = {
    BANANA_PRO_OFFICIAL_LABEL: {
        "1K": "bananaPRO-official-1k",
        "2K": "bananaPRO-official-2k",
        "4K": "bananaPRO-official-4k",
    },
    BANANA_2_OFFICIAL_LABEL: {
        "1K": "banana2-official-1k",
        "2K": "banana2-official-2k",
        "4K": "banana2-official-4k",
    },
}
PRICE_BY_MODEL_RESOLUTION = {
    BANANA_PRO_OFFICIAL_LABEL: {"1K": 0.60, "2K": 0.60, "4K": 1.00},
    BANANA_2_OFFICIAL_LABEL: {"1K": 0.30, "2K": 0.30, "4K": 0.60},
}
BANANA_PRO_ASPECT_RATIOS = [
    "模型默认",
    "1:1",
    "2:3",
    "3:2",
    "3:4",
    "4:3",
    "4:5",
    "5:4",
    "9:16",
    "16:9",
    "21:9",
]
BANANA_2_ASPECT_RATIOS = [
    "模型默认",
    "16:9",
    "4:3",
    "4:5",
    "3:2",
    "1:1",
    "2:3",
    "3:4",
    "5:4",
    "9:16",
    "21:9",
    "1:4",
    "4:1",
    "1:8",
    "8:1",
]
ASPECT_RATIOS_BY_MODEL = {
    "bananaPRO": BANANA_PRO_ASPECT_RATIOS,
    "bannana-2": BANANA_2_ASPECT_RATIOS,
    BANANA_PRO_OFFICIAL_LABEL: BANANA_PRO_ASPECT_RATIOS,
    BANANA_2_OFFICIAL_LABEL: BANANA_2_ASPECT_RATIOS,
}
RESOLUTIONS_BY_MODEL = {
    "bananaPRO": ["1K", "2K", "4K"],
    "bannana-2": ["1K", "2K", "4K"],
    BANANA_PRO_OFFICIAL_LABEL: ["1K", "2K", "4K"],
    BANANA_2_OFFICIAL_LABEL: ["1K", "2K", "4K"],
}
# ComfyUI's server schema is static, so expose the union and let the frontend
# narrow each combo immediately after the model is selected.
ASPECT_RATIO_OPTIONS = list(dict.fromkeys(BANANA_PRO_ASPECT_RATIOS + BANANA_2_ASPECT_RATIOS))
RESOLUTION_OPTIONS = list(dict.fromkeys(value for values in RESOLUTIONS_BY_MODEL.values() for value in values))
_MARKDOWN_DATA_IMAGE_RE = re.compile(
    r"!\[[^\]]*\]\(data:(image/[^;\s)]+);base64,([^)]+)\)", re.IGNORECASE
)
_MARKDOWN_URL_IMAGE_RE = re.compile(r"!\[[^\]]*\]\((https?://[^)]+)\)", re.IGNORECASE)


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        printable = str(message).encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(printable)


def _log_info(message):
    _safe_print(f"[dapaoAPI-香蕉全能图像] 信息：{message}")


def _log_error(message):
    _safe_print(f"[dapaoAPI-香蕉全能图像] 错误：{message}")


def _pil_to_tensor(image):
    image = image.convert("RGB")
    array = np.asarray(image).astype(np.float32) / 255.0
    return torch.from_numpy(array).unsqueeze(0)


def _tensor_to_inline_parts(image_tensor):
    return tensor_to_png_inline_parts(image_tensor)


def _response_error(response):
    text = response.text[:1200]
    try:
        data = response.json()
    except Exception:
        return text
    if not isinstance(data, dict):
        return text
    error = data.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("status") or error.get("code") or text)
    return str(data.get("message") or data.get("msg") or error or text)


class DapaoBananaAPIError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = int(status_code)
        self.api_message = str(message)
        labels = {
            400: "请求参数错误",
            401: "认证失败，请检查 API 密钥",
            402: "余额不足，请充值后重试",
            403: "没有模型或接口权限",
            404: "接口或映射模型不存在",
            429: IMAGE_429_HINT,
            500: (
                "服务内部出现异常，本次任务未完成，请稍后重试。\n"
                "如果当前使用香蕉模型，请在节点的‘模型’下拉框中切换到‘香蕉pro官方稳定版’或‘香蕉2官方稳定版’后再试"
            ),
            502: (
                "上游模型服务连接失败，当前模型暂时无法完成请求，请稍后重试。\n"
                "如果当前使用香蕉模型，建议在节点的‘模型’下拉框中切换到‘香蕉pro官方稳定版’或‘香蕉2官方稳定版’后再试"
            ),
            503: (
                "当前模型暂时没有可用服务通道，可能是通道繁忙或正在维护。\n"
                "如果当前使用香蕉模型，请在节点的‘模型’下拉框中切换到‘香蕉pro官方稳定版’或‘香蕉2官方稳定版’后再试"
            ),
        }
        label = labels.get(self.status_code, "中转站请求失败")
        super().__init__(f"{label} {self.status_code}：{self.api_message}")


class DapaoBananaRelayClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = API_BASE_URL.rstrip("/")

    def generate_content(self, model_id, payload):
        url = f"{self.base_url}/v1beta/models/{model_id}:generateContent"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/BananaAllround",
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RuntimeError(f"{friendly_network_error(error, '提交图像任务')} 生成请求不会自动重试，以免重复扣费。") from error
        if response.status_code >= 400:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status())
            raise DapaoBananaAPIError(response.status_code, _response_error(response))
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站返回内容不是 JSON：{response.text[:500]}") from error

    def download(self, url):
        try:
            response = requests.get(
                url,
                headers={"User-Agent": "Mozilla/5.0", "Accept": "image/*,*/*;q=0.8"},
                timeout=max(self.timeout, 300),
                allow_redirects=True,
            )
            response.raise_for_status()
            return response.content
        except requests.RequestException as error:
            raise RuntimeError(friendly_network_error(error, "下载生成结果")) from error


def _extract_image_items(result):
    """Read both documented Gemini response forms plus common relay aliases."""
    items = []
    seen = set()

    def add(kind, value, mime_type="image/png"):
        if not isinstance(value, str) or not value.strip():
            return
        value = value.strip()
        key = (kind, value)
        if key in seen:
            return
        seen.add(key)
        items.append((kind, value, mime_type or "image/png"))

    candidates = result.get("candidates", []) if isinstance(result, dict) else []
    for candidate in candidates if isinstance(candidates, list) else []:
        if not isinstance(candidate, dict):
            continue
        content = candidate.get("content")
        parts = content.get("parts", []) if isinstance(content, dict) else []
        for part in parts if isinstance(parts, list) else []:
            if not isinstance(part, dict) or part.get("thought"):
                continue
            inline = part.get("inlineData") or part.get("inline_data")
            if isinstance(inline, dict) and inline.get("data"):
                add("base64", inline["data"], inline.get("mimeType") or inline.get("mime_type"))
            text = part.get("text")
            if isinstance(text, str):
                for match in _MARKDOWN_DATA_IMAGE_RE.finditer(text):
                    add("base64", match.group(2), match.group(1))
                for match in _MARKDOWN_URL_IMAGE_RE.finditer(text):
                    add("url", match.group(1))

    # Some relays normalize Gemini responses into OpenAI-style data items.
    data = result.get("data", []) if isinstance(result, dict) else []
    for item in data if isinstance(data, list) else []:
        if not isinstance(item, dict):
            continue
        encoded = item.get("b64_json") or item.get("base64") or item.get("image_base64")
        if encoded:
            add("base64", encoded)
        url = item.get("url") or item.get("image_url")
        if isinstance(url, str) and url.startswith(("http://", "https://")):
            add("url", url)

    return items


def _image_item_to_pil(client, kind, value):
    if kind == "base64":
        encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
        try:
            content = base64.b64decode(encoded)
        except Exception as error:
            raise RuntimeError(f"返回图片 Base64 解码失败：{error}") from error
    else:
        content = client.download(value)
    try:
        return Image.open(io.BytesIO(content)).convert("RGB")
    except Exception as error:
        raise RuntimeError(f"中转站返回的数据不是有效图片：{error}") from error


def _sanitized_result(value):
    """Prevent multi-megabyte base64 strings from flooding the response widget."""
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in {"data", "b64_json", "base64", "image_base64"} and isinstance(item, str) and len(item) > 200:
                cleaned[key] = f"<图片Base64已省略，共{len(item)}字符>"
            else:
                cleaned[key] = _sanitized_result(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitized_result(item) for item in value]
    if isinstance(value, str) and value.startswith("data:image/") and len(value) > 200:
        return f"<图片Data URI已省略，共{len(value)}字符>"
    return value


class DapaoBananaAllroundNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "⌛ 请求超时": ("INT", {"default": 900, "min": 30, "max": 1800, "step": 10}),
        }
        for index in range(1, 13):
            optional[f"🖼️ 图像{index}"] = ("IMAGE", {"tooltip": "接入任意参考图后自动切换为图生图，最多12张。"})
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
                "🤖 模型": (MODEL_OPTIONS, {"default": "bananaPRO"}),
                "📝 提示词": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "一张高端商业摄影海报，干净的自然光，细节清晰，质感高级",
                    },
                ),
                "📐 图片尺寸/比例": (ASPECT_RATIO_OPTIONS, {"default": "1:1"}),
                "🧩 清晰度": (RESOLUTION_OPTIONS, {"default": "1K"}),
                "🖼️ 出图数量": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "⚡ 异步模式": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "只控制同一条提示词的出图数量大于1时是否并发；上游提示词列表会由ComfyUI自动并发。每张均按一次接口调用计价。",
                    },
                ),
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

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "Banana 文生图/多图编辑；接收提示词列表时由ComfyUI并发执行各条任务"

    @staticmethod
    def _collect_reference_parts(kwargs):
        parts = []
        for input_index in range(1, 13):
            image_tensor = kwargs.get(f"🖼️ 图像{input_index}")
            if image_tensor is None:
                continue
            for part in _tensor_to_inline_parts(image_tensor):
                if len(parts) >= 12:
                    return parts
                parts.append(part)
        return parts

    @staticmethod
    def _make_payload(prompt, reference_parts, aspect_ratio, resolution):
        parts = list(reference_parts)
        parts.append({"text": prompt})
        image_config = {"imageSize": resolution}
        if aspect_ratio != "模型默认":
            image_config["aspectRatio"] = aspect_ratio
        payload = {
            "contents": [{"role": "user", "parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": image_config,
            },
        }
        return payload

    @staticmethod
    def _submit_many(client, model_id, payload, count, concurrent):
        if not concurrent or count == 1:
            return [client.generate_content(model_id, payload) for _ in range(count)]
        results = [None] * count
        with ThreadPoolExecutor(max_workers=min(count, 4), thread_name_prefix="dapao-banana") as executor:
            futures = {executor.submit(client.generate_content, model_id, payload): index for index in range(count)}
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        return results

    async def generate(self, **kwargs):
        # Each mapped prompt becomes an independent coroutine in ComfyUI.
        # Move requests/PIL work to worker threads so list tasks run in
        # parallel without changing the proven single-prompt implementation.
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_label = kwargs.get("🤖 模型", "bananaPRO")
        prompt = (kwargs.get("📝 提示词") or "").strip()
        aspect_ratio = kwargs.get("📐 图片尺寸/比例", "1:1")
        resolution = kwargs.get("🧩 清晰度", "1K")
        count = min(max(int(kwargs.get("🖼️ 出图数量", 1)), 1), 10)
        concurrent = bool(kwargs.get("⚡ 异步模式", False))
        timeout = int(kwargs.get("⌛ 请求超时", 900))
        responses = []
        started = time.time()

        try:
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_label not in MODEL_OPTIONS:
                raise ValueError(f"不支持的映射模型：{model_label}")
            if not prompt:
                raise ValueError("提示词不能为空。")
            supported_aspect_ratios = ASPECT_RATIOS_BY_MODEL[model_label]
            supported_resolutions = RESOLUTIONS_BY_MODEL[model_label]
            if aspect_ratio not in supported_aspect_ratios:
                raise ValueError(f"模型 {model_label} 不支持图片比例：{aspect_ratio}")
            if resolution not in supported_resolutions:
                raise ValueError(f"模型 {model_label} 不支持清晰度：{resolution}")
            model_id = MODEL_ID_BY_RESOLUTION.get(model_label, {}).get(resolution, model_label)
            reference_parts = self._collect_reference_parts(kwargs)
            mode = "图生图" if reference_parts else "文生图"
            payload = self._make_payload(prompt, reference_parts, aspect_ratio, resolution)
            client = DapaoBananaRelayClient(api_key, timeout)

            _log_info(
                f"提交任务：relay={API_BASE_URL}，model={model_id}，mode={mode}，"
                f"aspectRatio={aspect_ratio}，imageSize={resolution}，count={count}，"
                f"并发={concurrent}，参考图={len(reference_parts)}张"
            )
            responses = self._submit_many(client, model_id, payload, count, concurrent)

            image_items = []
            for response in responses:
                items = _extract_image_items(response)
                if not items:
                    raise RuntimeError(
                        "任务完成但没有找到图片："
                        + json.dumps(_sanitized_result(response), ensure_ascii=False)[:1600]
                    )
                image_items.extend(items)

            pil_images = [_image_item_to_pil(client, kind, value) for kind, value, _ in image_items]
            # Gemini 映射在同一批次偶尔返回不同像素尺寸（尤其是超宽比例）。
            # ComfyUI IMAGE batch 要求 H/W 完全一致，因此统一到首张图尺寸后再拼接。
            target_size = pil_images[0].size
            resized_count = 0
            normalized_images = []
            for image in pil_images:
                if image.size != target_size:
                    image = image.resize(target_size, Image.Resampling.LANCZOS)
                    resized_count += 1
                normalized_images.append(image)
            tensors = [_pil_to_tensor(image) for image in normalized_images]
            images = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)
            urls = [value for kind, value, _ in image_items if kind == "url"]
            elapsed = time.time() - started
            unit_price = PRICE_BY_MODEL_RESOLUTION.get(model_label, {}).get(
                resolution,
                PRICE_BY_MODEL.get(model_label),
            )
            if unit_price is None:
                raise RuntimeError(f"模型 {model_label} 的价格尚未配置。")
            estimated_price = unit_price * count
            info = (
                "✅ 香蕉-banana 全能图像任务完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 界面模型：{model_label}\n"
                f"📤 实际模型ID：{model_id}\n"
                f"🔀 模式：{mode}\n"
                f"📐 图片比例：{aspect_ratio}\n"
                f"🧩 清晰度：{resolution}\n"
                f"🖼️ 参考图：{len(reference_parts)} 张\n"
                f"🖼️ 请求数量：{count} 次，实际返回：{len(tensors)} 张\n"
                f"📏 尺寸统一：{'已统一到首张图片' if resized_count else '无需处理'}\n"
                f"⚡ 提交方式：{'并发' if concurrent and count > 1 else '顺序'}\n"
                f"💰 单价：¥{unit_price:.2f}/张，预计价格：¥{estimated_price:.2f}\n"
                f"⏱️ 耗时：{elapsed:.2f} 秒\n\n"
                + json.dumps({"responses": _sanitized_result(responses)}, ensure_ascii=False, indent=2)
            )
            return images, "\n".join(urls), info
        except Exception as error:
            message = f"❌ 香蕉-banana 全能图像生成失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            details = json.dumps({"responses": _sanitized_result(responses)}, ensure_ascii=False, indent=2)
            # Fail loudly so downstream Save Image nodes never save a fake black placeholder.
            raise RuntimeError(f"{message}\n\n{details}") from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoBananaAllroundNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoBananaAllroundNode",
    "MODEL_OPTIONS",
    "MODEL_ID_BY_RESOLUTION",
    "PRICE_BY_MODEL",
    "PRICE_BY_MODEL_RESOLUTION",
    "ASPECT_RATIOS_BY_MODEL",
    "RESOLUTIONS_BY_MODEL",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
