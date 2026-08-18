"""Seedream 5.0 Pro all-round image node for the dapaoAI relay.

The node follows the official BytePlus Seedream 5.0 Pro image-generation
schema while using the relay model ID and base URL configured by dapaoAI.
"""

import asyncio
import base64
import io
import json
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import requests
import torch
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error
from .image_input_utils import IMAGE_429_HINT, tensor_to_pil_images

try:
    import comfy.model_management
    import comfy.utils
except Exception:
    comfy = None


API_BASE_URL = "https://api.dapaoai.com"
MODEL_ID = "seedream-v5-pro"
NODE_NAME = "DapaoSeedreamV5ProAllroundNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
DISPLAY_NAME = "🐠Seedream-v5-pro全能图像@炮老师的小课堂"
MAX_REFERENCE_IMAGES = 10
MAX_OUTPUT_REQUESTS = 10
MAX_CONCURRENT_REQUESTS = 4

ASPECT_RATIO_OPTIONS = ["模型智能选择", "1:1", "4:3", "3:4", "16:9", "9:16", "3:2", "2:3", "21:9"]
RESOLUTION_OPTIONS = ["1K", "1.5K", "2K"]
SIZE_BY_RESOLUTION = {
    "1K": {
        "1:1": "1024x1024", "4:3": "1152x864", "3:4": "864x1152",
        "16:9": "1424x800", "9:16": "800x1424", "3:2": "1248x832",
        "2:3": "832x1248", "21:9": "1568x672",
    },
    "1.5K": {
        "1:1": "1536x1536", "4:3": "1792x1344", "3:4": "1344x1792",
        "16:9": "2048x1152", "9:16": "1152x2048", "3:2": "1872x1248",
        "2:3": "1248x1872", "21:9": "2352x1008",
    },
    "2K": {
        "1:1": "2048x2048", "4:3": "2368x1776", "3:4": "1776x2368",
        "16:9": "2816x1584", "9:16": "1584x2816", "3:2": "2496x1664",
        "2:3": "1664x2496", "21:9": "3136x1344",
    },
}
PROMPT_OPTIMIZATION = {"关闭": None, "标准模式": "standard", "快速模式": "fast"}
OUTPUT_FORMATS = {"JPEG": "jpeg", "PNG": "png"}
RESPONSE_FORMATS = {"URL链接": "url", "Base64": "b64_json"}


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        printable = str(message).encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(printable)


def _log_info(message):
    _safe_print(f"[dapaoAPI-Seedream-v5-pro全能图像] 信息：{message}")


def _log_error(message):
    _safe_print(f"[dapaoAPI-Seedream-v5-pro全能图像] 错误：{message}")


def _response_error(response):
    text = response.text[:1600]
    try:
        data = response.json()
    except Exception:
        return text
    if not isinstance(data, dict):
        return text
    error = data.get("error")
    if isinstance(error, dict):
        detail = error.get("detail")
        if isinstance(detail, dict):
            nested = detail.get("error")
            if isinstance(nested, dict):
                return str(nested.get("message") or nested.get("code") or text)
        return str(error.get("message") or error.get("code") or detail or text)
    return str(data.get("message") or data.get("msg") or error or text)


class DapaoSeedreamV5ProAPIError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = int(status_code)
        self.api_message = str(message)
        labels = {
            400: "请求参数或参考图不符合 Seedream 5.0 Pro 要求",
            401: "API 密钥无效或已过期",
            402: "账户余额不足，请充值后重试",
            403: "当前账户没有该模型或接口权限",
            404: "中转站接口或 seedream-v5-pro 模型映射不存在",
            413: "参考图或请求内容过大",
            429: IMAGE_429_HINT,
            500: "服务内部出现异常，本次任务未完成，请稍后重试",
            502: "中转站连接上游 Seedream 服务失败，请稍后重试",
            503: "Seedream 模型通道暂时不可用，可能正在维护或排队繁忙",
        }
        label = labels.get(self.status_code, "中转站请求失败")
        super().__init__(f"{label} {self.status_code}：{self.api_message}")


def _mask_for_index(mask_tensor, index, width, height):
    if mask_tensor is None:
        return None
    mask = mask_tensor[min(index, mask_tensor.shape[0] - 1)].detach().cpu().numpy()
    mask = np.clip(mask * 255.0, 0, 255).astype(np.uint8)
    image = Image.fromarray(mask, mode="L")
    if image.size != (width, height):
        image = image.resize((width, height), Image.Resampling.BILINEAR)
    return np.asarray(image).astype(np.float32) / 255.0


def _tensor_to_png_items(image_tensor, transparency_mask=None):
    items = []
    for index, source_image in enumerate(tensor_to_pil_images(image_tensor)):
        width, height = source_image.size
        has_alpha = source_image.mode == "RGBA"
        alpha = np.asarray(source_image.getchannel("A")) if has_alpha else None
        mask = _mask_for_index(transparency_mask, index, width, height)
        if mask is not None:
            # ComfyUI MASK uses white for transparency, so alpha is its inverse.
            alpha = np.clip((1.0 - mask) * 255.0, 0, 255).astype(np.uint8)
            has_alpha = True
        image = source_image.convert("RGB")
        if has_alpha:
            image.putalpha(Image.fromarray(alpha, mode="L"))
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        content = buffer.getvalue()
        items.append({
            "content": content,
            "data_uri": "data:image/png;base64," + base64.b64encode(content).decode("ascii"),
            "has_alpha": has_alpha,
        })
    return items


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


def _extract_image_records(result):
    records = []
    seen = set()

    def add(record, kind, value):
        if not isinstance(value, str) or not value:
            return
        marker = (kind, value)
        if marker in seen:
            return
        seen.add(marker)
        records.append({
            "kind": kind,
            "value": value,
            "z_index": record.get("z_index"),
            "name": record.get("name"),
            "description": record.get("description"),
            "bounding_box": record.get("bounding_box"),
            "size": record.get("size"),
            "output_format": record.get("output_format"),
        })

    def walk(value):
        if isinstance(value, dict):
            base64_value = value.get("b64_json") or value.get("image_base64")
            if isinstance(base64_value, str):
                add(value, "base64", base64_value)
            for key in ("url", "image_url", "result_url"):
                url = value.get(key)
                if isinstance(url, str) and url.startswith(("http://", "https://", "data:image/")):
                    add(value, "url", url)
            for item in value.values():
                if isinstance(item, (dict, list)):
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(result)
    if records and any(record.get("z_index") is not None for record in records):
        records.sort(key=lambda record: int(record.get("z_index") or 0))
    return records


def _sanitized_result(value):
    if isinstance(value, dict):
        return {key: _sanitized_result(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitized_result(item) for item in value]
    if isinstance(value, str):
        if value.startswith("data:image/") or len(value) > 4000:
            return f"<省略长内容，共{len(value)}字符>"
    return value


class DapaoSeedreamV5ProRelayClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = API_BASE_URL.rstrip("/")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/SeedreamV5ProAllround",
        }

    def _request_json(self, method, path, **kwargs):
        url = f"{self.base_url}/{path.lstrip('/')}"
        attempts = 3 if method.upper() == "GET" else 1
        for attempt in range(attempts):
            try:
                response = requests.request(
                    method,
                    url,
                    headers=self._headers(),
                    timeout=self.timeout,
                    **kwargs,
                )
            except (requests.ConnectionError, requests.Timeout) as error:
                if attempt < attempts - 1:
                    time.sleep(attempt + 1)
                    continue
                if method.upper() == "GET":
                    raise RuntimeError(f"{friendly_network_error(error, '查询任务')} 已尝试{attempts}次。") from error
                raise RuntimeError(f"{friendly_network_error(error, '提交图像任务')} 付费提交不会自动重试，以免重复扣费。") from error
            if response.status_code >= 400:
                if response.status_code == 443:
                    raise RuntimeError(friendly_443_status())
                raise DapaoSeedreamV5ProAPIError(response.status_code, _response_error(response))
            try:
                return response.json()
            except json.JSONDecodeError as error:
                raise RuntimeError(f"中转站返回内容不是 JSON：{response.text[:600]}") from error
        raise RuntimeError("中转站请求失败。")

    def generate(self, payload):
        return self._request_json("POST", "/v1/images/generations", json=payload)

    def poll(self, task_identifier, max_seconds, interval):
        started = time.monotonic()
        progress_bar = comfy.utils.ProgressBar(100) if comfy is not None else None
        task_path = f"/v1/images/tasks/{task_identifier}"
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
                raise RuntimeError(f"任务失败：{message or json.dumps(_sanitized_result(result), ensure_ascii=False)[:1200]}")
            if progress_bar:
                elapsed = time.monotonic() - started
                current = min(95, int(progress)) if progress is not None else min(95, int(elapsed / max_seconds * 95))
                progress_bar.update_absolute(current)
            time.sleep(interval)
        raise RuntimeError(f"任务超过{max_seconds}秒仍未完成。")

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


def _record_to_image(client, record):
    value = record["value"]
    if record["kind"] == "base64":
        encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
        content = base64.b64decode(encoded)
    elif value.startswith("data:image/"):
        content = base64.b64decode(value.split(",", 1)[1])
    else:
        content = client.download(value)
    return Image.open(io.BytesIO(content)).convert("RGBA")


def _images_and_masks(client, records):
    pil_images = [_record_to_image(client, record) for record in records]
    target_size = pil_images[0].size
    normalized = []
    for image in pil_images:
        if image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)
        normalized.append(image)

    image_tensors = []
    mask_tensors = []
    for image in normalized:
        rgba = np.asarray(image).astype(np.float32) / 255.0
        image_tensors.append(torch.from_numpy(rgba[:, :, :3]).unsqueeze(0))
        mask_tensors.append(torch.from_numpy(1.0 - rgba[:, :, 3]).unsqueeze(0))
    return torch.cat(image_tensors, dim=0), torch.cat(mask_tensors, dim=0)


class DapaoSeedreamV5ProAllroundNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎭 图像1透明蒙版": (
                "MASK",
                {"tooltip": "仅透明背景模式需要；请连接与图像1配套的 ComfyUI 透明蒙版。"},
            ),
            "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 3600, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 3, "max": 30, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 900, "min": 30, "max": 1800, "step": 10}),
        }
        for index in range(1, MAX_REFERENCE_IMAGES + 1):
            optional[f"🖼️ 图像{index}"] = (
                "IMAGE",
                {"tooltip": f"接入任意参考图后自动切换为图生图，官方最多支持{MAX_REFERENCE_IMAGES}张。"},
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
                "🤖 模型": ([MODEL_ID], {"default": MODEL_ID}),
                "📝 提示词": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "一张信息清晰、文字准确、构图专业的中文商业视觉海报",
                        "tooltip": "描述需要生成或编辑的图像内容。",
                    },
                ),
                "📐 图片比例": (ASPECT_RATIO_OPTIONS, {"default": "1:1"}),
                "🧩 清晰度": (RESOLUTION_OPTIONS, {"default": "2K"}),
                "🧠 提示词优化": (list(PROMPT_OPTIMIZATION), {"default": "标准模式"}),
                "📦 输出格式": (list(OUTPUT_FORMATS), {"default": "JPEG"}),
                "📨 返回方式": (list(RESPONSE_FORMATS), {"default": "URL链接"}),
                "🏷️ 添加水印": ("BOOLEAN", {"default": False}),
                "🫧 透明背景": (
                    "BOOLEAN",
                    {"default": False, "tooltip": "官方仅支持单张带透明通道的参考图，启用后输出固定为 PNG。"},
                ),
                "🖼️ 出图数量": (
                    "INT",
                    {"default": 1, "min": 1, "max": MAX_OUTPUT_REQUESTS, "step": 1, "tooltip": "官方单次只生成1张；大于1时节点发起多个独立请求。"},
                ),
                "⚡ 多图并发": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "多张输出使用最多4路并发；每路都是独立付费请求。"},
                ),
                "🎲 随机种": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": "randomize",
                        "tooltip": "Seedream 5.0 Pro 官方没有 seed 参数；此值只控制 ComfyUI 缓存。",
                    },
                ),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("IMAGE", "MASK", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像/图层", "🎭 透明蒙版", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "Seedream 5.0 Pro 文生图、多图编辑与透明背景；列表输入自动并发 @炮老师的小课堂"

    @staticmethod
    def _collect_reference_images(kwargs):
        items = []
        transparency_mask = kwargs.get("🎭 图像1透明蒙版")
        for input_index in range(1, MAX_REFERENCE_IMAGES + 1):
            image_tensor = kwargs.get(f"🖼️ 图像{input_index}")
            if image_tensor is None:
                continue
            paired_mask = transparency_mask if input_index == 1 else None
            items.extend(_tensor_to_png_items(image_tensor, paired_mask))
        if len(items) > MAX_REFERENCE_IMAGES:
            raise ValueError(
                f"Seedream 5.0 Pro 最多接收{MAX_REFERENCE_IMAGES}张参考图，"
                f"当前输入接口和图像批次合计{len(items)}张。"
            )
        return items

    @staticmethod
    def _submit_one(api_key, timeout, payload, max_poll_seconds, poll_interval):
        client = DapaoSeedreamV5ProRelayClient(api_key, timeout)
        submitted = client.generate(payload)
        final = submitted
        records = _extract_image_records(final)
        task_identifier = _task_id(submitted)
        state, _, _ = _task_state(submitted)
        if not records and task_identifier and state in {"", "processing"}:
            final = client.poll(task_identifier, max_poll_seconds, poll_interval)
            records = _extract_image_records(final)
        if not records:
            raise RuntimeError(
                "任务完成但没有找到图片："
                + json.dumps(_sanitized_result(final), ensure_ascii=False)[:1600]
            )
        return submitted, final, records

    @classmethod
    def _submit_many(cls, api_key, timeout, payload, count, concurrent, max_poll_seconds, poll_interval):
        arguments = (api_key, timeout, payload, max_poll_seconds, poll_interval)
        if count == 1 or not concurrent:
            return [cls._submit_one(*arguments) for _ in range(count)]
        results = [None] * count
        with ThreadPoolExecutor(
            max_workers=min(count, MAX_CONCURRENT_REQUESTS),
            thread_name_prefix="dapao-seedream-v5-pro",
        ) as executor:
            futures = {executor.submit(cls._submit_one, *arguments): index for index in range(count)}
            for future in as_completed(futures):
                results[futures[future]] = future.result()
        return results

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        api_key = str(kwargs.get("🔑 API密钥") or "").strip()
        model_id = str(kwargs.get("🤖 模型") or MODEL_ID)
        prompt = str(kwargs.get("📝 提示词") or "").strip()
        aspect_ratio = str(kwargs.get("📐 图片比例") or "1:1")
        resolution = str(kwargs.get("🧩 清晰度") or "2K")
        optimization_label = str(kwargs.get("🧠 提示词优化") or "标准模式")
        output_label = str(kwargs.get("📦 输出格式") or "JPEG")
        response_label = str(kwargs.get("📨 返回方式") or "URL链接")
        watermark = bool(kwargs.get("🏷️ 添加水印", False))
        transparent = bool(kwargs.get("🫧 透明背景", False))
        count = min(max(int(kwargs.get("🖼️ 出图数量", 1)), 1), MAX_OUTPUT_REQUESTS)
        concurrent = bool(kwargs.get("⚡ 多图并发", True))
        timeout = int(kwargs.get("⌛ 请求超时", 900))
        max_poll_seconds = int(kwargs.get("🔁 最大轮询秒数", 1200))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        responses = []
        started = time.time()

        try:
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_id != MODEL_ID:
                raise ValueError(f"不支持的模型：{model_id}")
            if aspect_ratio not in ASPECT_RATIO_OPTIONS:
                raise ValueError(f"不支持的图片比例：{aspect_ratio}")
            if resolution not in RESOLUTION_OPTIONS:
                raise ValueError(f"不支持的清晰度：{resolution}")
            if optimization_label not in PROMPT_OPTIMIZATION:
                raise ValueError(f"不支持的提示词优化模式：{optimization_label}")
            if output_label not in OUTPUT_FORMATS:
                raise ValueError(f"不支持的输出格式：{output_label}")
            if response_label not in RESPONSE_FORMATS:
                raise ValueError(f"不支持的返回方式：{response_label}")

            references = self._collect_reference_images(kwargs)
            mode = "图生图" if references else "文生图"
            if not prompt:
                raise ValueError("文生图或图生图模式下提示词不能为空。")
            if transparent:
                if len(references) != 1:
                    raise ValueError("透明背景模式必须且只能接入1张参考图。")
                if not references[0]["has_alpha"]:
                    raise ValueError("透明背景模式需要图像1自带透明通道，或连接‘图像1透明蒙版’。")
                output_label = "PNG"

            if aspect_ratio == "模型智能选择":
                size = resolution
            else:
                size = SIZE_BY_RESOLUTION[resolution][aspect_ratio]

            payload = {
                "model": MODEL_ID,
                "prompt": prompt,
                "size": size,
                "output_format": OUTPUT_FORMATS[output_label],
                "response_format": RESPONSE_FORMATS[response_label],
                "watermark": watermark,
            }
            if transparent:
                payload["background"] = "transparent"
            optimization = PROMPT_OPTIMIZATION[optimization_label]
            if optimization:
                payload["optimize_prompt_options"] = {"mode": optimization}
            if references:
                payload["image"] = [item["data_uri"] for item in references]

            _log_info(
                f"提交任务：relay={API_BASE_URL}，model={MODEL_ID}，mode={mode}，"
                f"size={size}，count={count}，并发={concurrent and count > 1}，"
                f"参考图={len(references)}张"
            )
            responses = self._submit_many(
                api_key,
                timeout,
                payload,
                count,
                concurrent,
                max_poll_seconds,
                poll_interval,
            )

            client = DapaoSeedreamV5ProRelayClient(api_key, timeout)
            all_records = []
            for _, _, records in responses:
                all_records.extend(records)
            images, masks = _images_and_masks(client, all_records)
            urls = [
                record["value"] for record in all_records
                if record["kind"] == "url" and record["value"].startswith(("http://", "https://"))
            ]
            elapsed = time.time() - started
            info = (
                "✅ Seedream-v5-pro 全能图像任务完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 实际模型ID：{MODEL_ID}\n"
                f"🔀 自动模式：{mode}\n"
                f"📐 图片比例：{aspect_ratio}\n"
                f"🧩 清晰度：{resolution}，实际size：{size}\n"
                f"🧠 提示词优化：{optimization_label}\n"
                f"📦 输出格式：{output_label}，返回方式：{response_label}\n"
                f"🫧 透明背景：{'开启' if transparent else '关闭'}\n"
                f"🖼️ 参考图：{len(references)}张，请求：{count}次，返回图像：{len(all_records)}张\n"
                f"⚡ 提交方式：{'并发' if concurrent and count > 1 else '单次/顺序'}\n"
                f"💰 价格：待配置\n"
                f"⏱️ 耗时：{elapsed:.2f}秒\n"
                + "\n"
                + json.dumps(
                    {
                        "request": {key: value for key, value in payload.items() if key != "image"},
                        "responses": [
                            {"submit": _sanitized_result(submit), "final": _sanitized_result(final)}
                            for submit, final, _ in responses
                        ],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return images, masks, "\n".join(urls), info
        except Exception as error:
            message = f"❌ Seedream-v5-pro 全能图像生成失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            details = json.dumps(
                {
                    "responses": [
                        {
                            "submit": _sanitized_result(item[0]),
                            "final": _sanitized_result(item[1]),
                        }
                        for item in responses if item
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
            raise RuntimeError(f"{message}\n\n{details}") from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoSeedreamV5ProAllroundNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoSeedreamV5ProAllroundNode",
    "MODEL_ID",
    "ASPECT_RATIO_OPTIONS",
    "RESOLUTION_OPTIONS",
    "SIZE_BY_RESOLUTION",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
