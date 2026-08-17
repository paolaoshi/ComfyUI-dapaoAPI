"""Dedicated Seedream V5 Pro layer-decomposition node for dapaoAI."""

import asyncio
import base64
import io
import json
import sys
import time
import traceback

import numpy as np
import requests
import torch
import torch.nn.functional as torch_functional
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error

try:
    import comfy.model_management
    import comfy.utils
except Exception:
    comfy = None

API_BASE_URL = "https://api.dapaoai.com"
MODEL_ID = "seedream-v5-pro/layer-decomposition"
NODE_NAME = "DapaoSeedreamV5ProLayerDecompositionNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
DISPLAY_NAME = "🧩Seedream-v5-pro图层拆分@炮老师的小课堂"

SIZE_OPTIONS = ["自动", "1K", "1.5K", "2K"]
SIZE_VALUES = {"自动": "auto", "1K": "1K", "1.5K": "1.5K", "2K": "2K"}
OUTPUT_FORMATS = {"JPEG": "jpeg", "PNG": "png"}
PROMPT_OPTIMIZATION = {"标准模式": "standard", "快速模式": "fast"}


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        printable = str(message).encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(printable)


def _log_info(message):
    _safe_print(f"[dapaoAPI-Seedream图层拆分] 信息：{message}")


def _log_error(message):
    _safe_print(f"[dapaoAPI-Seedream图层拆分] 错误：{message}")


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


class DapaoSeedreamLayerAPIError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = int(status_code)
        self.api_message = str(message)
        labels = {
            400: "请求参数或待拆分图片不符合模型要求",
            401: "API 密钥无效或已过期",
            402: "账户余额不足，请充值后重试",
            403: "当前账户没有图层拆分模型权限",
            404: "中转站没有配置 seedream-v5-pro/layer-decomposition 模型",
            413: "待拆分图片超过接口大小限制",
            429: "请求过于频繁，图层拆分通道繁忙，请稍后再试",
            500: "图层拆分服务内部异常，本次任务未完成，请稍后重试",
            502: "中转站连接上游图层拆分服务失败，请稍后重试",
            503: "图层拆分模型通道暂时不可用，可能正在维护或排队繁忙",
        }
        label = labels.get(self.status_code, "中转站请求失败")
        super().__init__(f"{label} {self.status_code}：{self.api_message}")


def _response_layers(result):
    if not isinstance(result, dict):
        return []
    layers = []
    pending = [result]
    seen = set()
    while pending:
        layer = pending.pop(0)
        if id(layer) in seen:
            continue
        seen.add(id(layer))
        layers.append(layer)
        for key in ("data", "result", "output", "task", "prediction"):
            value = layer.get(key)
            if isinstance(value, dict):
                pending.append(value)
    return layers


def _task_id(result):
    for layer in _response_layers(result):
        value = layer.get("task_id") or layer.get("prediction_id") or layer.get("id")
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
    if any(status in {"submitted", "created", "processing", "pending", "queued", "running", "in_progress"} for status in statuses):
        return "processing", progress, message
    return (statuses[0] if statuses else ""), progress, message


def _value_record(metadata, value):
    if not isinstance(value, str) or not value:
        return None
    if value.startswith(("http://", "https://", "data:image/")):
        kind = "url"
    else:
        kind = "base64"
    metadata = metadata if isinstance(metadata, dict) else {}
    return {
        "kind": kind,
        "value": value,
        "z_index": metadata.get("z_index"),
        "name": metadata.get("name"),
        "description": metadata.get("description"),
        "bounding_box": metadata.get("bounding_box"),
    }


def _extract_output_records(result):
    # Dedicated model responses commonly return parallel outputs[] and layers[] arrays.
    for container in _response_layers(result):
        outputs = container.get("outputs")
        if not isinstance(outputs, list) or not outputs:
            continue
        metadata_items = container.get("layers")
        if not isinstance(metadata_items, list):
            metadata_items = []
        records = []
        for index, output in enumerate(outputs):
            metadata = metadata_items[index] if index < len(metadata_items) else {}
            if isinstance(output, str):
                record = _value_record(metadata, output)
            elif isinstance(output, dict):
                merged = dict(metadata) if isinstance(metadata, dict) else {}
                merged.update(output)
                value = output.get("url") or output.get("image_url") or output.get("b64_json")
                record = _value_record(merged, value)
            else:
                record = None
            if record:
                records.append(record)
        if records:
            return records

    # OpenAI-style image responses carry one record per data[] item.
    records = []
    seen = set()

    def walk(value):
        if isinstance(value, dict):
            output = value.get("url") or value.get("image_url") or value.get("result_url")
            kind = "url"
            if not output:
                output = value.get("b64_json") or value.get("image_base64")
                kind = "base64"
            if isinstance(output, str) and output:
                marker = (kind, output)
                if marker not in seen:
                    seen.add(marker)
                    records.append({
                        "kind": kind,
                        "value": output,
                        "z_index": value.get("z_index"),
                        "name": value.get("name"),
                        "description": value.get("description"),
                        "bounding_box": value.get("bounding_box"),
                    })
            for item in value.values():
                if isinstance(item, (dict, list)):
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(result)
    return records


def _sanitized_result(value):
    if isinstance(value, dict):
        return {key: _sanitized_result(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitized_result(item) for item in value]
    if isinstance(value, str) and (value.startswith("data:image/") or len(value) > 4000):
        return f"<省略长内容，共{len(value)}字符>"
    return value


class DapaoSeedreamLayerClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = API_BASE_URL.rstrip("/")

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/SeedreamV5ProLayerDecomposition",
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
                raise RuntimeError(f"{friendly_network_error(error, '提交图层拆分任务')} 付费提交不会自动重试，以免重复扣费。") from error
            if response.status_code >= 400:
                if response.status_code == 443:
                    raise RuntimeError(friendly_443_status())
                raise DapaoSeedreamLayerAPIError(response.status_code, _response_error(response))
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
        while time.monotonic() - started < max_seconds:
            if comfy is not None:
                comfy.model_management.throw_exception_if_processing_interrupted()
            result = self._request_json("GET", f"/v1/images/tasks/{task_identifier}")
            status, progress, message = _task_state(result)
            records = _extract_output_records(result)
            if status == "succeeded" or records:
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
        raise RuntimeError(f"图层拆分任务超过{max_seconds}秒仍未完成。")

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
            raise RuntimeError(friendly_network_error(error, "下载图层拆分结果")) from error


def _tensor_to_png_data_uri(image_tensor):
    if not isinstance(image_tensor, torch.Tensor) or image_tensor.ndim != 4:
        raise ValueError("待拆分图像必须是 ComfyUI IMAGE。")
    if image_tensor.shape[0] != 1:
        raise ValueError("专用拆层模型一次只能处理1张图像，请先从图像批次中取出单张。")
    image_array = image_tensor[0].detach().cpu().numpy()
    if image_array.ndim != 3 or image_array.shape[2] < 3:
        raise ValueError("待拆分图像必须是 RGB 图像。")
    height, width = image_array.shape[:2]
    if width < 512 or height < 512 or width > 6000 or height > 6000:
        raise ValueError(f"图片尺寸需在512到6000像素之间，当前为{width}x{height}。")
    ratio = width / height
    if ratio < 1 / 16 or ratio > 16:
        raise ValueError(f"图片宽高比需在1:16到16:1之间，当前为{width}:{height}。")
    rgb = np.clip(image_array[:, :, :3] * 255.0, 0, 255).astype(np.uint8)
    image = Image.fromarray(rgb, mode="RGB")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    content = buffer.getvalue()
    if len(content) > 30 * 1024 * 1024:
        raise ValueError(f"待拆分图片编码后为{len(content) / 1024 / 1024:.1f}MB，超过30MB限制。")
    return "data:image/png;base64," + base64.b64encode(content).decode("ascii"), width, height


def _tensor_to_rgb_image(image_tensor):
    image_array = image_tensor[0].detach().cpu().numpy()
    rgb = np.clip(image_array[:, :, :3] * 255.0, 0, 255).astype(np.uint8)
    return Image.fromarray(rgb, mode="RGB")


def _record_to_rgba(client, record):
    value = record["value"]
    if record["kind"] == "base64":
        encoded = value.split(",", 1)[1] if value.startswith("data:") and "," in value else value
        content = base64.b64decode(encoded)
    elif value.startswith("data:image/"):
        content = base64.b64decode(value.split(",", 1)[1])
    else:
        content = client.download(value)
    return Image.open(io.BytesIO(content)).convert("RGBA")


def _resize_rgba(image, size):
    if image.size == size:
        return image
    rgba = torch.from_numpy(np.asarray(image).astype(np.float32) / 255.0)
    rgba = rgba.clone()
    rgba[..., :3] *= rgba[..., 3:4]
    resized = torch_functional.interpolate(
        rgba.permute(2, 0, 1).unsqueeze(0),
        size=(size[1], size[0]),
        mode="bilinear",
        align_corners=False,
        antialias=True,
    ).squeeze(0).permute(1, 2, 0)
    alpha = resized[..., 3:4]
    straight = torch.cat([resized[..., :3] / alpha.clamp(min=1e-6), alpha], dim=-1).clamp(0, 1)
    return Image.fromarray((straight.numpy() * 255.0).round().astype(np.uint8), mode="RGBA")


def _fit_rgba_inside(image, max_size):
    """Resize an RGBA layer proportionally so it fits inside max_size."""
    max_width, max_height = max_size
    if image.width <= max_width and image.height <= max_height:
        return image
    scale = min(max_width / image.width, max_height / image.height)
    target = (
        max(1, int(round(image.width * scale))),
        max(1, int(round(image.height * scale))),
    )
    return _resize_rgba(image, target)


def _bounding_box(record, canvas_size):
    box = record.get("bounding_box")
    if not isinstance(box, dict):
        return None
    values = box.get("absolute")
    if not isinstance(values, (list, tuple)) or len(values) != 4:
        values = box.get("normalized")
        if not isinstance(values, (list, tuple)) or len(values) != 4:
            return None
        width, height = canvas_size
        values = [
            float(values[0]) / 1000 * width,
            float(values[1]) / 1000 * height,
            float(values[2]) / 1000 * width,
            float(values[3]) / 1000 * height,
        ]
    try:
        left, top, right, bottom = (int(round(float(value))) for value in values)
    except (TypeError, ValueError):
        return None
    width, height = canvas_size
    left = max(0, min(width - 1, left))
    top = max(0, min(height - 1, top))
    right = max(left + 1, min(width, right))
    bottom = max(top + 1, min(height, bottom))
    return left, top, right, bottom


def _full_canvas_layer(image, record, canvas_size):
    placement = _bounding_box(record, canvas_size)
    if placement is None:
        # Some relays return only layer URLs and drop bounding_box metadata. Keep
        # the returned cutout's proportions in that case; pad it instead of
        # stretching the subject to the base canvas.
        image = _fit_rgba_inside(image, canvas_size)
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
        left = max(0, (canvas_size[0] - image.width) // 2)
        top = max(0, (canvas_size[1] - image.height) // 2)
        canvas.alpha_composite(image, (left, top))
        return canvas, [left, top, left + image.width, top + image.height], "缺少坐标，按原始比例居中补边"
    left, top, right, bottom = placement
    box_size = (right - left, bottom - top)
    image = _fit_rgba_inside(image, box_size)
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    paste_left = left + max(0, (box_size[0] - image.width) // 2)
    paste_top = top + max(0, (box_size[1] - image.height) // 2)
    canvas.alpha_composite(image, (paste_left, paste_top))
    return canvas, [paste_left, paste_top, paste_left + image.width, paste_top + image.height], ""


def _alpha_crop(image):
    rgba = image.convert("RGBA")
    alpha = np.asarray(rgba.getchannel("A"), dtype=np.uint8)
    ys, xs = np.where(alpha > 4)
    if not len(xs):
        return None
    return rgba.crop((int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))


def _match_layer_to_reference(image, record, reference):
    """Place a cropped RGBA layer back onto its source-image canvas."""
    canvas_size = reference.size
    cropped = _alpha_crop(image)
    if cropped is None:
        return Image.new("RGBA", canvas_size, (0, 0, 0, 0)), [0, 0, 0, 0], None, "透明图层为空"

    try:
        import cv2
    except ImportError:
        fallback, placement, warning = _full_canvas_layer(image, record, canvas_size)
        return fallback, placement, None, f"缺少 OpenCV，PSD使用普通定位；{warning}".rstrip("；")

    source_rgb = np.asarray(reference.convert("RGB"), dtype=np.uint8)
    layer_rgb = np.asarray(cropped.convert("RGB"), dtype=np.uint8)
    layer_alpha = np.asarray(cropped.getchannel("A"), dtype=np.uint8)
    source_height, source_width = source_rgb.shape[:2]
    layer_height, layer_width = layer_rgb.shape[:2]
    max_scale = min(source_width / layer_width, source_height / layer_height)
    if max_scale <= 0:
        fallback, placement, warning = _full_canvas_layer(image, record, canvas_size)
        return fallback, placement, None, f"PSD定位尺寸无效；{warning}".rstrip("；")

    search_factor = min(1.0, 640.0 / max(source_width, source_height))
    search_size = (
        max(1, int(round(source_width * search_factor))),
        max(1, int(round(source_height * search_factor))),
    )
    source_lab = cv2.cvtColor(source_rgb, cv2.COLOR_RGB2LAB)
    layer_lab = cv2.cvtColor(layer_rgb, cv2.COLOR_RGB2LAB)
    source_search = cv2.resize(source_lab, search_size, interpolation=cv2.INTER_AREA)
    min_scale = min(max_scale, max(0.08, 48.0 / max(layer_width, layer_height)))
    if max_scale / max(min_scale, 1e-6) < 1.01:
        coarse_scales = np.array([max_scale], dtype=np.float64)
    else:
        coarse_scales = np.geomspace(min_scale, max_scale, num=48)
    if min_scale <= 1.0 <= max_scale:
        coarse_scales = np.unique(np.append(coarse_scales, 1.0))

    best_score = -1.0
    best_scale = None
    for scale in coarse_scales:
        width = max(4, int(round(layer_width * float(scale) * search_factor)))
        height = max(4, int(round(layer_height * float(scale) * search_factor)))
        if width > source_search.shape[1] or height > source_search.shape[0]:
            continue
        template = cv2.resize(
            layer_lab,
            (width, height),
            interpolation=cv2.INTER_AREA,
        )
        mask = cv2.resize(layer_alpha, (width, height), interpolation=cv2.INTER_AREA)
        mask = np.where(mask > 24, 255, 0).astype(np.uint8)
        if int(np.count_nonzero(mask)) < 32:
            continue
        result = cv2.matchTemplate(source_search, template, cv2.TM_CCOEFF_NORMED, mask=mask)
        _, score, _, _ = cv2.minMaxLoc(result)
        if np.isfinite(score) and score > best_score:
            best_score = float(score)
            best_scale = float(scale)

    if best_scale is None or best_score < 0.25:
        fallback, placement, warning = _full_canvas_layer(image, record, canvas_size)
        score_text = "无有效结果" if best_scale is None else f"匹配分数{best_score:.3f}过低"
        return fallback, placement, best_score if best_scale is not None else None, f"PSD自动定位{score_text}；{warning}".rstrip("；")

    refine_low = max(min_scale, best_scale * 0.94)
    refine_high = min(max_scale, best_scale * 1.06)
    refine_scales = np.linspace(refine_low, refine_high, num=13)
    for scale in refine_scales:
        width = max(4, int(round(layer_width * float(scale) * search_factor)))
        height = max(4, int(round(layer_height * float(scale) * search_factor)))
        if width > source_search.shape[1] or height > source_search.shape[0]:
            continue
        template = cv2.resize(
            layer_lab,
            (width, height),
            interpolation=cv2.INTER_AREA,
        )
        mask = cv2.resize(layer_alpha, (width, height), interpolation=cv2.INTER_AREA)
        mask = np.where(mask > 24, 255, 0).astype(np.uint8)
        result = cv2.matchTemplate(source_search, template, cv2.TM_CCOEFF_NORMED, mask=mask)
        _, score, _, _ = cv2.minMaxLoc(result)
        if np.isfinite(score) and score > best_score:
            best_score = float(score)
            best_scale = float(scale)

    target_size = (
        min(source_width, max(1, int(round(layer_width * best_scale)))),
        min(source_height, max(1, int(round(layer_height * best_scale)))),
    )
    target_layer = _resize_rgba(cropped, target_size)
    template_lab = cv2.cvtColor(np.asarray(target_layer.convert("RGB"), dtype=np.uint8), cv2.COLOR_RGB2LAB)
    template_alpha = np.asarray(target_layer.getchannel("A"), dtype=np.uint8)
    full_mask = np.where(template_alpha > 24, 255, 0).astype(np.uint8)
    result = cv2.matchTemplate(source_lab, template_lab, cv2.TM_CCOEFF_NORMED, mask=full_mask)
    _, full_score, _, location = cv2.minMaxLoc(result)
    if np.isfinite(full_score):
        best_score = float(full_score)
    left, top = int(location[0]), int(location[1])
    canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    canvas.alpha_composite(target_layer, (left, top))
    placement = [left, top, left + target_layer.width, top + target_layer.height]
    return canvas, placement, best_score, ""


def _pil_to_image_and_mask(image):
    rgba = np.asarray(image).astype(np.float32) / 255.0
    image_tensor = torch.from_numpy(rgba[:, :, :3]).unsqueeze(0)
    mask_tensor = torch.from_numpy(1.0 - rgba[:, :, 3]).unsqueeze(0)
    return image_tensor, mask_tensor


def _pil_to_rgba_tensor(image):
    rgba = np.asarray(image.convert("RGBA"), dtype=np.uint8)
    return torch.from_numpy(rgba.astype(np.float32) / 255.0).unsqueeze(0)


def _z_index(record, fallback):
    value = record.get("z_index")
    if isinstance(value, bool):
        return fallback
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


class DapaoSeedreamV5ProLayerDecompositionNode:
    @classmethod
    def INPUT_TYPES(cls):
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
                "🖼️ 待拆分图像": (
                    "IMAGE",
                    {"tooltip": "必须接入且只能接入1张图像；支持512到6000像素、最大30MB。"},
                ),
                "📝 拆分要求": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "placeholder": "留空自动拆分主要元素，也可以指定需要拆出的对象",
                        "tooltip": "可用自然语言指定对象，也支持 <bbox>x1 y1 x2 y2</bbox>，坐标范围0到1000。",
                    },
                ),
                "🧩 清晰度": (SIZE_OPTIONS, {"default": "自动"}),
                "🧠 拆分优化": (list(PROMPT_OPTIMIZATION), {"default": "标准模式"}),
                "📦 基础图格式": (list(OUTPUT_FORMATS), {"default": "JPEG", "tooltip": "透明图层始终返回PNG。"}),
                "🎲 随机种": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": "randomize",
                        "tooltip": "专用拆层接口没有 seed 参数；此值只控制 ComfyUI 缓存和重新执行。",
                    },
                ),
            },
            "optional": {
                "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 3600, "step": 10}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 3, "max": 30, "step": 1}),
                "⌛ 请求超时": ("INT", {"default": 900, "min": 30, "max": 1800, "step": 10}),
            },
        }

    RETURN_TYPES = ("IMAGE", "IMAGE", "MASK", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = (
        "🖼️ 基础背景图",
        "🧩 透明图层批次",
        "🎭 图层蒙版批次",
        "🔗 结果链接",
        "📋 图层信息",
        "🗂️ PSD透明图层批次",
    )
    FUNCTION = "decompose"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "使用 seedream-v5-pro/layer-decomposition 将单张图像拆成背景与最多16个透明图层 @炮老师的小课堂"

    async def decompose(self, **kwargs):
        return await asyncio.to_thread(self._decompose_sync, **kwargs)

    def _decompose_sync(self, **kwargs):
        api_key = str(kwargs.get("🔑 API密钥") or "").strip()
        model_id = str(kwargs.get("🤖 模型") or MODEL_ID)
        image_tensor = kwargs.get("🖼️ 待拆分图像")
        prompt = str(kwargs.get("📝 拆分要求") or "").strip()
        effective_prompt = prompt or "自动识别并拆分图像中的所有主要元素，分别输出独立透明图层。"
        size_label = str(kwargs.get("🧩 清晰度") or "自动")
        optimization_label = str(kwargs.get("🧠 拆分优化") or "标准模式")
        format_label = str(kwargs.get("📦 基础图格式") or "JPEG")
        timeout = int(kwargs.get("⌛ 请求超时", 900))
        max_poll_seconds = int(kwargs.get("🔁 最大轮询秒数", 1200))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        submitted = {}
        final = {}
        started = time.time()

        try:
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_id != MODEL_ID:
                raise ValueError(f"不支持的模型：{model_id}")
            if size_label not in SIZE_VALUES:
                raise ValueError(f"不支持的清晰度：{size_label}")
            if optimization_label not in PROMPT_OPTIMIZATION:
                raise ValueError(f"不支持的拆分优化模式：{optimization_label}")
            if format_label not in OUTPUT_FORMATS:
                raise ValueError(f"不支持的基础图格式：{format_label}")

            image_data, input_width, input_height = _tensor_to_png_data_uri(image_tensor)
            input_reference = _tensor_to_rgb_image(image_tensor)
            payload = {
                "model": MODEL_ID,
                "prompt": effective_prompt,
                "image": image_data,
                "size": SIZE_VALUES[size_label],
                "output_format": OUTPUT_FORMATS[format_label],
                "optimize_prompt_options": {"mode": PROMPT_OPTIMIZATION[optimization_label]},
            }

            _log_info(
                f"提交拆层任务：relay={API_BASE_URL}，model={MODEL_ID}，"
                f"input={input_width}x{input_height}，size={payload['size']}"
            )
            client = DapaoSeedreamLayerClient(api_key, timeout)
            submitted = client.generate(payload)
            final = submitted
            records = _extract_output_records(final)
            task_identifier = _task_id(submitted)
            state, _, _ = _task_state(submitted)
            if not records and task_identifier and state in {"", "processing"}:
                final = client.poll(task_identifier, max_poll_seconds, poll_interval)
                records = _extract_output_records(final)
            if not records:
                raise RuntimeError(
                    "任务完成但没有找到基础图和透明图层："
                    + json.dumps(_sanitized_result(final), ensure_ascii=False)[:1600]
                )

            indexed_records = list(enumerate(records))
            indexed_records.sort(key=lambda item: _z_index(item[1], item[0]))
            records = [record for _, record in indexed_records]
            base_record = records[0]
            layer_records = records[1:]
            if not layer_records:
                raise RuntimeError("模型只返回了基础图，没有返回可拆分图层；请调整图片或拆分要求后重试。")

            base_rgba = _record_to_rgba(client, base_record)
            base_image, _ = _pil_to_image_and_mask(base_rgba)
            canvas_size = base_rgba.size
            layer_images = []
            layer_masks = []
            layer_details = []
            psd_layer_items = []
            for index, record in enumerate(layer_records, start=1):
                native_rgba = _record_to_rgba(client, record)
                canvas_rgba, placement, warning = _full_canvas_layer(native_rgba, record, canvas_size)
                psd_canvas_rgba, psd_placement, psd_match_score, psd_warning = _match_layer_to_reference(
                    native_rgba,
                    record,
                    input_reference,
                )
                image, mask = _pil_to_image_and_mask(canvas_rgba)
                layer_images.append(image)
                layer_masks.append(mask)
                psd_layer_items.append({"record": record, "image": psd_canvas_rgba})
                layer_details.append({
                    "batch_index": index - 1,
                    "z_index": _z_index(record, index),
                    "name": record.get("name") or f"图层{index}",
                    "description": record.get("description") or "",
                    "bounding_box": record.get("bounding_box"),
                    "placed_absolute": placement,
                    "native_size": f"{native_rgba.width}x{native_rgba.height}",
                    "warning": warning,
                    "psd_placed_absolute": psd_placement,
                    "psd_match_score": round(psd_match_score, 4) if psd_match_score is not None else None,
                    "psd_warning": psd_warning,
                    "url": record["value"] if record["kind"] == "url" and record["value"].startswith(("http://", "https://")) else "",
                })

            layers_tensor = torch.cat(layer_images, dim=0)
            masks_tensor = torch.cat(layer_masks, dim=0)
            psd_rgba_layers = [
                _pil_to_rgba_tensor(item["image"])
                for item in reversed(psd_layer_items)
            ]
            psd_base_rgba = _resize_rgba(base_rgba, input_reference.size)
            psd_rgba_layers.append(_pil_to_rgba_tensor(psd_base_rgba))
            psd_layers_tensor = torch.cat(psd_rgba_layers, dim=0)
            urls = [
                record["value"] for record in records
                if record["kind"] == "url" and record["value"].startswith(("http://", "https://"))
            ]
            elapsed = time.time() - started
            info = (
                "✅ Seedream-v5-pro 专用图层拆分完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 实际模型ID：{MODEL_ID}\n"
                f"🖼️ 输入尺寸：{input_width}x{input_height}\n"
                f"📐 基础图尺寸：{canvas_size[0]}x{canvas_size[1]}\n"
                f"🧩 清晰度：{size_label}，实际size：{payload['size']}\n"
                f"🧠 拆分优化：{optimization_label}\n"
                f"📝 拆分要求：{'用户指定' if prompt else '自动识别全部主要元素'}\n"
                f"📦 基础图格式：{format_label}，透明图层：PNG\n"
                f"🗂️ 返回结果：1张基础图 + {len(layer_records)}个透明图层\n"
                f"📄 PSD画布：{input_reference.width}x{input_reference.height}，图层已按输入原图自动定位\n"
                "🔌 PSD输出：请将“PSD透明图层批次”连接到“🐋保存为PSD”节点\n"
                f"⏱️ 耗时：{elapsed:.2f}秒\n\n"
                + json.dumps(
                    {
                        "layers": layer_details,
                        "request": {key: value for key, value in payload.items() if key != "image"},
                        "submit": _sanitized_result(submitted),
                        "final": _sanitized_result(final),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return base_image, layers_tensor, masks_tensor, "\n".join(urls), info, psd_layers_tensor
        except Exception as error:
            message = f"❌ Seedream-v5-pro 图层拆分失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            details = json.dumps(
                {
                    "request_model": MODEL_ID,
                    "submit": _sanitized_result(submitted),
                    "final": _sanitized_result(final),
                },
                ensure_ascii=False,
                indent=2,
            )
            raise RuntimeError(f"{message}\n\n{details}") from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoSeedreamV5ProLayerDecompositionNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoSeedreamV5ProLayerDecompositionNode",
    "MODEL_ID",
    "SIZE_OPTIONS",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
