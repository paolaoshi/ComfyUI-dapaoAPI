"""GPT Image 2 all-round image node for the dapaoAI relay.

This module is intentionally self-contained.  It does not import or inherit the
legacy low-price image node, so that node can be removed independently.
"""

import base64
import asyncio
import io
import json
import sys
import time
import traceback

import numpy as np
import requests
import torch
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error
from .image_input_utils import IMAGE_429_HINT, tensor_to_png_bytes
from .dreambrush_runtime import ensure_asset_references, queue_job_metadata, submit_json_task

try:
    import comfy.model_management
    import comfy.utils
except Exception:
    comfy = None


API_BASE_URL = "https://api.dapaoai.com"
NODE_NAME = "DapaoGPTImage2AllroundNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
DISPLAY_NAME = "🐠GPT-image-2全能图像@炮老师的小课堂"
MAX_REFERENCE_IMAGES = 9

MODEL_LABEL = "image-2"
OFFICIAL_STABLE_MODEL_LABEL = "image-2官方稳定全分辨率"
MODEL_OPTIONS = [MODEL_LABEL, OFFICIAL_STABLE_MODEL_LABEL]
MODEL_ID_BY_LABEL = {
    OFFICIAL_STABLE_MODEL_LABEL: "image-2-office",
}
MODEL_BY_RESOLUTION = {
    "1K": "image-2-1k",
    "2K": "image-2-2k",
    "4K": "image-2-4k",
}
RESOLUTION_API_VALUES = {"1K": "1k", "2K": "2k", "4K": "4k"}
PRICE_BY_RESOLUTION = {"1K": 0.06, "2K": 0.12, "4K": 0.18}
PRICE_BY_MODEL = {OFFICIAL_STABLE_MODEL_LABEL: 0.60}

SIZE_OPTIONS = [
    "模型默认",
    "1:1",
    "3:2",
    "2:3",
    "4:3",
    "3:4",
    "5:4",
    "4:5",
    "16:9",
    "9:16",
    "2:1",
    "1:2",
    "3:1",
    "1:3",
    "21:9",
    "9:21",
]
# `image-2-office` is currently backed by a stricter adapter than the public
# image-2 routes: it accepts `auto` or an explicit WIDTHxHEIGHT value.  Keep
# the UI in aspect-ratio terms, and translate only for that route.  Dimensions
# follow the relay's documented Image-2 reference sizes.
OFFICE_SIZE_BY_RESOLUTION = {
    "1K": {
        "1:1": "1024x1024", "3:2": "1536x1024", "2:3": "1024x1536",
        "4:3": "1024x768", "3:4": "768x1024", "5:4": "1280x1024",
        "4:5": "1024x1280", "16:9": "1536x864", "9:16": "864x1536",
        "2:1": "2048x1024", "1:2": "1024x2048", "3:1": "1881x836",
        "1:3": "887x1774", "21:9": "2016x864", "9:21": "864x2016",
    },
    "2K": {
        "1:1": "2048x2048", "3:2": "2048x1360", "2:3": "1360x2048",
        "4:3": "2048x1536", "3:4": "1536x2048", "5:4": "2560x2048",
        "4:5": "2048x2560", "16:9": "2048x1152", "9:16": "1152x2048",
        "2:1": "2688x1344", "1:2": "1344x2688", "3:1": "3072x1024",
        "1:3": "1024x3072", "21:9": "2688x1152", "9:21": "1152x2688",
    },
    "4K": {
        "1:1": "2880x2880", "3:2": "3520x2336", "2:3": "2336x3520",
        "4:3": "3312x2480", "3:4": "2480x3312", "5:4": "3216x2576",
        "4:5": "2576x3216", "16:9": "3840x2160", "9:16": "2160x3840",
        "2:1": "3840x1920", "1:2": "1920x3840", "3:1": "3840x1280",
        "1:3": "1280x3840", "21:9": "3840x1648", "9:21": "1648x3840",
    },
}
QUALITY_API_VALUES = {
    "低画质": "low",
    "标准画质": "medium",
    "高画质": "high",
}


def _safe_print(message):
    """Keep logging from masking the actual API error on GBK consoles."""
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        printable = str(message).encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(printable)


def _log_info(message):
    _safe_print(f"[dapaoAPI-GPT-image-2全能图像] 信息：{message}")


def _log_error(message):
    _safe_print(f"[dapaoAPI-GPT-image-2全能图像] 错误：{message}")


def _pil_to_tensor(image):
    image = image.convert("RGB")
    array = np.asarray(image).astype(np.float32) / 255.0
    return torch.from_numpy(array).unsqueeze(0)


def _tensor_to_png_bytes(image_tensor):
    return tensor_to_png_bytes(image_tensor)


def _png_data_uri(content):
    return "data:image/png;base64," + base64.b64encode(content).decode("ascii")


def _response_error(response):
    text = response.text[:1000]
    try:
        data = response.json()
    except Exception:
        return text
    if not isinstance(data, dict):
        return text
    error = data.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("code") or text)
    return str(data.get("message") or data.get("msg") or error or text)


class DapaoImage2APIError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = int(status_code)
        self.api_message = str(message)
        super().__init__(self._format_message())

    def _format_message(self):
        labels = {
            400: "请求参数错误",
            401: "认证失败，请检查 API 密钥",
            402: "余额不足，请充值后重试",
            403: "没有模型或接口权限",
            404: "接口不存在",
            429: IMAGE_429_HINT,
            500: (
                "服务内部出现异常，本次任务未完成，请稍后重试。\n"
                "如果当前使用 image-2，请在节点的‘模型’下拉框中切换到‘image-2官方稳定全分辨率’后再试"
            ),
            502: (
                "上游模型服务连接失败，当前模型暂时无法完成请求，请稍后重试。\n"
                "如果当前使用 image-2，建议在节点的‘模型’下拉框中切换到‘image-2官方稳定全分辨率’后再试"
            ),
            503: (
                "当前模型暂时没有可用服务通道，可能是通道繁忙或正在维护。\n"
                "如果当前使用 image-2，请在节点的‘模型’下拉框中切换到‘image-2官方稳定全分辨率’后再试"
            ),
        }
        label = labels.get(self.status_code, "中转站请求失败")
        return f"{label} {self.status_code}：{self.api_message}"


def _response_layers(result):
    if not isinstance(result, dict):
        return []
    layers = []
    pending = [result]
    seen = set()
    while pending:
        layer = pending.pop(0)
        layer_id = id(layer)
        if layer_id in seen:
            continue
        seen.add(layer_id)
        layers.append(layer)
        for key in ("data", "result", "output", "task"):
            value = layer.get(key)
            if isinstance(value, dict):
                pending.append(value)
            elif isinstance(value, list):
                pending.extend(item for item in value if isinstance(item, dict))
    return layers


def _task_id(result):
    queue_id = queue_job_metadata(result).get("job_id")
    if queue_id:
        return str(queue_id)
    for layer in _response_layers(result):
        value = layer.get("task_id") or layer.get("id")
        if isinstance(value, str) and value:
            return value
    return ""


def _task_state(result):
    statuses = []
    message = ""
    progress = None
    for layer in _response_layers(result):
        if layer.get("status") is not None:
            statuses.append(str(layer.get("status")).strip().lower())
        if progress is None and layer.get("progress") is not None:
            try:
                progress = float(str(layer.get("progress")).strip().rstrip("%"))
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
    if any(status in {"succeeded", "success", "completed", "complete"} for status in statuses):
        return "succeeded", progress, message
    if any(status in {"submitted", "processing", "pending", "queued", "running", "in_progress"} for status in statuses):
        return "processing", progress, message
    return (statuses[0] if statuses else ""), progress, message


def _extract_image_items(result):
    items = []
    seen = set()

    def add(kind, value):
        if not isinstance(value, str) or not value or value in seen:
            return
        seen.add(value)
        items.append((kind, value))

    def walk(value, parent_key=""):
        if isinstance(value, dict):
            for key, item in value.items():
                normalized_key = str(key).lower()
                if normalized_key in {"b64_json", "base64", "image_base64"}:
                    if isinstance(item, str):
                        add("base64", item)
                    else:
                        walk(item, normalized_key)
                elif normalized_key in {"url", "image_url", "result_url"}:
                    if isinstance(item, str) and item.startswith(("http://", "https://", "data:image/")):
                        add("url", item)
                    else:
                        walk(item, normalized_key)
                else:
                    walk(item, normalized_key)
        elif isinstance(value, list):
            for item in value:
                walk(item, parent_key)
        elif isinstance(value, str):
            if parent_key in {"url", "image_url", "result_url"} and value.startswith(("http://", "https://", "data:image/")):
                add("url", value)

    walk(result)
    return items


class DapaoImage2RelayClient:
    def __init__(self, api_key, timeout, max_poll_seconds=1200):
        self.api_key = api_key
        self.timeout = timeout
        self.max_poll_seconds = int(max_poll_seconds)
        self.base_url = API_BASE_URL.rstrip("/")

    def _headers(self, json_body=False):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "ComfyUI-dapaoAPI/GPTImage2Allround",
        }
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    def _request_json(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = kwargs.pop("headers", self._headers(json_body="json" in kwargs))
        attempts = 3 if method.upper() == "GET" else 1
        for attempt in range(attempts):
            try:
                response = requests.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as error:
                if attempt < attempts - 1:
                    time.sleep(attempt + 1)
                    continue
                if method.upper() == "GET":
                    raise RuntimeError(f"{friendly_network_error(error, '查询任务')} 已尝试 {attempts} 次。") from error
                raise RuntimeError(f"{friendly_network_error(error, '提交图像任务')} 提交请求不会自动重试，以免重复扣费。") from error
            if response.status_code >= 400:
                if response.status_code == 443:
                    raise RuntimeError(friendly_443_status())
                raise DapaoImage2APIError(response.status_code, _response_error(response))
            try:
                return response.json()
            except json.JSONDecodeError as error:
                raise RuntimeError(f"中转站返回内容不是 JSON：{response.text[:500]}") from error
        raise RuntimeError("中转站请求失败。")

    def generate(self, payload):
        return submit_json_task(
            api_key=self.api_key, base_url=self.base_url, endpoint="/v1/images/generations",
            payload=payload, timeout=self.timeout, user_agent="ComfyUI-dapaoAPI/GPTImage2Allround",
            error_factory=DapaoImage2APIError,
            interrupt_callback=(comfy.model_management.throw_exception_if_processing_interrupted if comfy is not None else None),
            max_poll_seconds=self.max_poll_seconds,
        )

    def edit(self, payload, reference_images):
        """Use reusable asset IDs; the gateway adapts them to upstream multipart."""
        references = ensure_asset_references(
            self.api_key,
            [(content, f"image_{index}.png", "image/png") for index, content in enumerate(reference_images, start=1)],
            base_url=self.base_url,
            timeout=self.timeout,
        )
        request_payload = {key: value for key, value in payload.items() if key != "async"}
        request_payload["image_urls"] = references
        return submit_json_task(
            api_key=self.api_key, base_url=self.base_url, endpoint="/v1/images/generations",
            payload=request_payload, timeout=self.timeout, user_agent="ComfyUI-dapaoAPI/GPTImage2Allround",
            error_factory=DapaoImage2APIError,
            interrupt_callback=(comfy.model_management.throw_exception_if_processing_interrupted if comfy is not None else None),
            max_poll_seconds=self.max_poll_seconds,
        )

    def poll(self, task_id, max_seconds, interval, image_task=False):
        started = time.monotonic()
        progress_bar = comfy.utils.ProgressBar(100) if comfy is not None else None
        task_path = f"/v1/images/tasks/{task_id}" if image_task else f"/v1/tasks/{task_id}"
        while time.monotonic() - started < max_seconds:
            if comfy is not None:
                comfy.model_management.throw_exception_if_processing_interrupted()
            result = self._request_json("GET", task_path)
            status, progress, message = _task_state(result)
            if status == "succeeded":
                if progress_bar:
                    progress_bar.update_absolute(100)
                return result
            if status == "failed":
                raise RuntimeError(f"任务失败：{message or json.dumps(result, ensure_ascii=False)[:1000]}")
            if progress_bar:
                elapsed = time.monotonic() - started
                current = min(95, int(progress)) if progress is not None else min(95, int(elapsed / max_seconds * 95))
                progress_bar.update_absolute(current)
            time.sleep(interval)
        raise RuntimeError(f"任务超过 {max_seconds} 秒仍未完成。")

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


def _image_item_to_pil(client, kind, value):
    if kind == "base64":
        encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
        content = base64.b64decode(encoded)
    elif value.startswith("data:image/"):
        content = base64.b64decode(value.split(",", 1)[1])
    else:
        content = client.download(value)
    return Image.open(io.BytesIO(content)).convert("RGB")


class DapaoGPTImage2AllroundNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 3600, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 3, "max": 30, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 900, "min": 30, "max": 1800, "step": 10}),
        }
        for index in range(1, MAX_REFERENCE_IMAGES + 1):
            optional[f"🖼️ 图像{index}"] = (
                "IMAGE",
                {"tooltip": f"接入任意参考图后自动切换为图生图，最多{MAX_REFERENCE_IMAGES}张。"},
            )
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
                "🤖 模型": (MODEL_OPTIONS, {"default": MODEL_LABEL}),
                "📝 提示词": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "一张高端商业摄影海报，干净的自然光，细节清晰，质感高级",
                    },
                ),
                "📐 图片尺寸/比例": (SIZE_OPTIONS, {"default": "模型默认"}),
                "🧩 清晰度": (list(MODEL_BY_RESOLUTION), {"default": "1K"}),
                "🎨 画质": (list(QUALITY_API_VALUES), {"default": "标准画质"}),
                "🖼️ 出图数量": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "⚡ 异步模式": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "兼容旧工作流的保留开关；DreamBrush持久队列与幂等保护现在始终启用。"},
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
    DESCRIPTION = "GPT-image-2 文生图/多图编辑；接收提示词列表时由ComfyUI并发执行各条任务 @炮老师的小课堂"

    @staticmethod
    def _collect_reference_images(kwargs):
        contents = []
        for input_index in range(1, MAX_REFERENCE_IMAGES + 1):
            image_tensor = kwargs.get(f"🖼️ 图像{input_index}")
            if image_tensor is None:
                continue
            for content in _tensor_to_png_bytes(image_tensor):
                contents.append(content)
        if len(contents) > MAX_REFERENCE_IMAGES:
            raise ValueError(
                f"image-2图生图最多接收{MAX_REFERENCE_IMAGES}张参考图，"
                f"当前输入接口及图像批次合计{len(contents)}张。"
            )
        return contents

    async def generate(self, **kwargs):
        # ComfyUI maps list outputs into one coroutine per prompt.  Running the
        # blocking requests work in worker threads lets those mapped prompts
        # progress concurrently while preserving the single-prompt code path.
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_label = kwargs.get("🤖 模型", MODEL_LABEL)
        prompt = (kwargs.get("📝 提示词") or "").strip()
        size = kwargs.get("📐 图片尺寸/比例", "模型默认")
        resolution_label = kwargs.get("🧩 清晰度", "1K")
        quality_label = kwargs.get("🎨 画质", "标准画质")
        count = min(max(int(kwargs.get("🖼️ 出图数量", 1)), 1), 10)
        async_mode = bool(kwargs.get("⚡ 异步模式", False))
        timeout = int(kwargs.get("⌛ 请求超时", 900))
        max_poll_seconds = int(kwargs.get("🔁 最大轮询秒数", 1200))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))

        submitted = {}
        final = {}
        started = time.time()
        try:
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_label not in MODEL_OPTIONS:
                raise ValueError(f"未知界面模型：{model_label}")
            if not prompt:
                raise ValueError("提示词不能为空。")
            if resolution_label not in MODEL_BY_RESOLUTION:
                raise ValueError(f"不支持的清晰度：{resolution_label}")
            if quality_label not in QUALITY_API_VALUES:
                raise ValueError(f"不支持的画质：{quality_label}")

            model_id = MODEL_ID_BY_LABEL.get(model_label, MODEL_BY_RESOLUTION[resolution_label])
            resolution = RESOLUTION_API_VALUES[resolution_label]
            quality = QUALITY_API_VALUES[quality_label]
            # 后端以实际收到的 IMAGE 输入为准，避免前端连线状态与工作流参数不同步。
            reference_images = self._collect_reference_images(kwargs)
            mode = "图生图" if reference_images else "文生图"

            core_payload = {
                "model": model_id,
                "prompt": prompt,
                "resolution": resolution,
                "quality": quality,
                "n": count,
                "response_format": "url",
            }
            # The public image-2 routes accept aspect-ratio strings.  The
            # official stable route currently validates `size` as `auto` or
            # explicit pixels, so translate the same UI choice for that route.
            submitted_size = size
            if model_label == OFFICIAL_STABLE_MODEL_LABEL:
                if size == "模型默认":
                    submitted_size = "auto"
                else:
                    submitted_size = OFFICE_SIZE_BY_RESOLUTION.get(resolution_label, {}).get(size)
                    if not submitted_size:
                        # Defensive fallback: an unknown/legacy ratio should
                        # still produce an image instead of sending an invalid
                        # ratio string to the strict adapter.
                        submitted_size = "auto"
                core_payload["size"] = submitted_size
            elif size != "模型默认":
                core_payload["size"] = size
            if async_mode:
                core_payload["async"] = True

            client = DapaoImage2RelayClient(api_key, timeout, max_poll_seconds)

            _log_info(
                f"提交任务：relay={API_BASE_URL}，model={model_id}，mode={mode}，"
                f"size={core_payload.get('size', '模型默认')}，quality={quality}，"
                f"n={count}，参考图={len(reference_images)}张"
            )
            if mode == "文生图":
                submitted = client.generate(core_payload)
            else:
                # 图生图必须走 edits multipart；重复的 image 文件字段对应多张参考图。
                submitted = client.edit(core_payload, reference_images)

            final = submitted
            image_items = _extract_image_items(final)
            task_identifier = _task_id(submitted)
            state, _, _ = _task_state(submitted)
            if not image_items and task_identifier and (async_mode or state == "processing"):
                final = client.poll(
                    task_identifier,
                    max_poll_seconds,
                    poll_interval,
                    image_task=(mode == "图生图"),
                )
                image_items = _extract_image_items(final)

            if not image_items:
                raise RuntimeError(f"任务完成但没有找到图片：{json.dumps(final, ensure_ascii=False)[:1200]}")

            tensors = [_pil_to_tensor(_image_item_to_pil(client, kind, value)) for kind, value in image_items]
            first_shape = tensors[0].shape
            if any(tensor.shape[1:] != first_shape[1:] for tensor in tensors[1:]):
                raise RuntimeError("中转站返回的多张图片尺寸不一致，无法组成 ComfyUI IMAGE 批次。")
            images = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)
            urls = [value for kind, value in image_items if kind == "url" and value.startswith(("http://", "https://"))]
            elapsed = time.time() - started
            unit_price = PRICE_BY_MODEL.get(model_label, PRICE_BY_RESOLUTION[resolution_label])
            estimated_price = unit_price * count
            info = (
                "✅ GPT-image-2 全能图像任务完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 界面模型：{model_label}\n"
                f"📤 实际模型ID：{model_id}\n"
                f"🔀 模式：{mode}\n"
                f"📐 图片比例：{size}\n"
                f"📏 实际尺寸参数：{submitted_size if model_label == OFFICIAL_STABLE_MODEL_LABEL else size}\n"
                f"🧩 清晰度：{resolution_label}\n"
                f"🎨 画质：{quality_label} ({quality})\n"
                f"🖼️ 参考图：{len(reference_images)} 张\n"
                f"🖼️ 请求数量：{count} 张，实际返回：{len(tensors)} 张\n"
                f"💰 单价：¥{unit_price:.2f}/张，预计价格：¥{estimated_price:.2f}\n"
                f"🆔 任务ID：{task_identifier or '同步返回'}\n"
                f"⏱️ 耗时：{elapsed:.2f} 秒\n\n"
                + json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2)
            )
            return images, "\n".join(urls), info
        except Exception as error:
            message = f"❌ GPT-image-2 全能图像生成失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            details = json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2)
            # 不再返回黑色占位图，避免下游保存节点把请求失败误当成有效结果。
            raise RuntimeError(f"{message}\n\n{details}") from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoGPTImage2AllroundNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoGPTImage2AllroundNode",
    "MODEL_OPTIONS",
    "MODEL_ID_BY_LABEL",
    "MODEL_BY_RESOLUTION",
    "PRICE_BY_RESOLUTION",
    "PRICE_BY_MODEL",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
