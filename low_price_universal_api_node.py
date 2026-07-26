"""
炳火低价全能 API 节点。

覆盖图像生成、视频生成、LLM 对话和视频去字幕。
作者：@炮老师的小课堂
"""

import base64
import io
import json
import os
import re
import tempfile
import time
import traceback
import wave

import numpy as np
import requests
import torch
from PIL import Image

try:
    import comfy.model_management
    import comfy.utils
    from comfy.comfy_types import IO
except Exception:
    comfy = None

    class IO:
        VIDEO = "VIDEO"


API_BASE_URL = "https://api.7tai.cc/v1"
NODE_CATEGORY = "🤖dapaoAPI/低价全能API推荐"

IMAGE_NODE_NAME = "DapaoLowPriceUniversalImageNode"
VIDEO_NODE_NAME = "DapaoLowPriceUniversalVideoNode"
LLM_NODE_NAME = "DapaoLowPriceLLMChatNode"
SUBTITLE_NODE_NAME = "DapaoLowPriceSubtitleRemovalNode"


PH_IMAGE_2_RATIO_SIZES = {
    "1:1": "1024x1024", "16:9": "1280x720", "9:16": "720x1280",
    "4:3": "1152x864", "3:4": "864x1152", "3:2": "1536x1024",
    "2:3": "1024x1536", "5:4": "1120x896", "4:5": "896x1120",
    "21:9": "1456x624", "9:21": "624x1456", "1:2": "768x1536",
    "2:1": "1536x768", "1:3": "688x2048", "3:1": "2048x688",
}
PH_IMAGE_2K_RATIO_SIZES = {
    "1:1": "2048x2048", "16:9": "2048x1152", "9:16": "1152x2048",
    "4:3": "2304x1728", "3:4": "1728x2304", "3:2": "2048x1360",
    "2:3": "1360x2048", "5:4": "2240x1792", "4:5": "1792x2240",
    "21:9": "2912x1248", "9:21": "1248x2912", "1:2": "1536x3072",
    "2:1": "3072x1536", "1:3": "1280x3840", "3:1": "3840x1280",
}
PH_IMAGE_4K_RATIO_SIZES = {
    "1:1": "2880x2880", "16:9": "3840x2160", "9:16": "2160x3840",
    "4:3": "3264x2448", "3:4": "2448x3264", "3:2": "3504x2336",
    "2:3": "2336x3504", "5:4": "3200x2560", "4:5": "2560x3200",
    "21:9": "3840x1648", "9:21": "1648x3840", "1:2": "1920x3840",
    "2:1": "3840x1920",
}
GPT_IMAGE_2_RATIO_SIZES = {
    "1:1": "1024x1024",
    "3:2": "1536x1024",
    "2:3": "1024x1536",
}
GEMINI_IMAGE_RATIO_SIZES = {
    "1:1": "2048x2048",
    "16:9": "3840x2160",
    "9:16": "2160x3840",
    "3:2": "1536x1024",
    "2:3": "1024x1536",
}


IMAGE_MODELS = {
    "GPT Image 2｜gpt-image-2": {
        "id": "gpt-image-2", "price": 0.035, "max_images": 9, "max_n": 10,
        "modes": ["文生图", "图生图"],
        "reference_field": "image",
        "sizes": ["auto", "1024x1024", "1536x1024", "1024x1536", "16:9", "9:16"],
        "ratio_sizes": GPT_IMAGE_2_RATIO_SIZES,
        "qualities": ["low", "medium", "high"],
    },
    "GPT Image 2 增强｜ph-gpt-image-2": {
        "id": "ph-gpt-image-2", "price": 0.09, "max_images": 9, "max_n": 10,
        "modes": ["文生图", "图生图"],
        "reference_field": "image",
        "sizes": ["auto", "1024x1024", "1280x720", "720x1280", "1152x864", "864x1152", "1536x1024", "1024x1536", "1120x896", "896x1120", "1456x624", "624x1456", "768x1536", "1536x768", "688x2048", "2048x688"],
        "ratio_sizes": PH_IMAGE_2_RATIO_SIZES,
        "qualities": ["low", "medium", "high"],
    },
    "GPT Image 2K 高清｜ph-gpt-image-2k": {
        "id": "ph-gpt-image-2k", "price": 0.15, "max_images": 9, "max_n": 10,
        "modes": ["文生图", "图生图"],
        "reference_field": "image",
        "sizes": ["2048x2048", "2048x1152", "1152x2048", "2304x1728", "1728x2304", "2048x1360", "1360x2048", "2240x1792", "1792x2240", "2912x1248", "1248x2912", "1536x3072", "3072x1536", "1280x3840", "3840x1280"],
        "ratio_sizes": PH_IMAGE_2K_RATIO_SIZES,
        "qualities": ["low", "medium", "high"],
    },
    "GPT Image 4K 超清｜ph-gpt-image-4k": {
        "id": "ph-gpt-image-4k", "price": 0.15, "max_images": 9, "max_n": 10,
        "modes": ["文生图", "图生图"],
        "reference_field": "image",
        "sizes": ["2880x2880", "3840x2160", "2160x3840", "3264x2448", "2448x3264", "3504x2336", "2336x3504", "3200x2560", "2560x3200", "3840x1648", "1648x3840", "1920x3840", "3840x1920"],
        "ratio_sizes": PH_IMAGE_4K_RATIO_SIZES,
        "qualities": ["low", "medium", "high"],
    },
    "Nano Banana 标准版｜banana2-S": {
        "id": "banana2-S", "price": 0.12, "max_images": 9, "max_n": 10,
        "modes": ["文生图", "图生图"],
        "sizes": ["16:9", "9:16", "1:1", "4:3", "3:4"], "qualities": [],
    },
    "Nano Banana 增强版｜banana2-S_copy": {
        "id": "banana2-S_copy", "price": 0.15, "max_images": 9, "max_n": 10,
        "modes": ["文生图", "图生图"],
        "sizes": ["16:9", "9:16", "1:1", "4:3", "3:4"], "qualities": [],
    },
    "GR Banana 2｜gr-banana-2": {
        "id": "gr-banana-2", "price": 0.18, "max_images": 9, "min_images": 1, "max_n": 10,
        "modes": ["图生图"],
        "sizes": ["auto", "16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"],
        "qualities": [], "resolutions": ["1K", "2K", "4K"], "clarity_field": "quality",
    },
    "GR Banana Pro｜gr-banana-pro": {
        "id": "gr-banana-pro", "price": 0.23, "max_images": 9, "min_images": 1, "max_n": 10,
        "modes": ["图生图"],
        "sizes": ["auto", "16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"],
        "qualities": [], "resolutions": ["1K", "2K", "4K"], "clarity_field": "quality",
    },
    "Gemini 3.1 Flash 图像｜gemini-3.1-flash-image-preview": {
        "id": "gemini-3.1-flash-image-preview", "price": 0.1216, "max_images": 9, "max_n": 4,
        "modes": ["文生图", "图生图"],
        "sizes": ["auto", "1024x1024", "1536x1024", "1024x1536", "2048x2048", "2048x1152", "3840x2160", "2160x3840"],
        "ratio_sizes": GEMINI_IMAGE_RATIO_SIZES,
        "qualities": [], "gemini": True,
    },
}

IMAGE_MODELS_BY_ID = {config["id"]: (label, config) for label, config in IMAGE_MODELS.items()}
PH_IMAGE_RESOLUTION_MODELS = {
    "1K": "ph-gpt-image-2",
    "2K": "ph-gpt-image-2k",
    "4K": "ph-gpt-image-4k",
}
PH_IMAGE_MODEL_IDS = set(PH_IMAGE_RESOLUTION_MODELS.values())


def _video_config(model_id, price, billing, resolution, durations, images=9, videos=0, audios=0, image_required=False, supports_frames=None, ratios=None):
    if supports_frames is None:
        supports_frames = model_id.startswith("bh2.0-") or model_id in {"sd2-vip720p", "sd2-vip720p-fast"}
    if image_required:
        modes = ["图生视频"]
        if videos or audios:
            modes.append("多模态参考")
    else:
        modes = ["文生视频", "图生视频"]
        if supports_frames:
            modes.append("首尾帧生视频")
        if videos or audios:
            modes.append("多模态参考")
    return {
        "id": model_id,
        "price": price,
        "billing": billing,
        "resolutions": resolution if isinstance(resolution, list) else [resolution],
        "durations": durations,
        "max_images": images,
        "max_videos": videos,
        "max_audios": audios,
        "image_required": image_required,
        "supports_frames": supports_frames,
        "modes": modes,
        "ratios": ratios or ["16:9", "9:16", "1:1", "4:3", "3:4", "2:3", "3:2", "21:9"],
    }


VIDEO_MODELS = {
    "Seedance 2.0 Fast 480P｜bh2.0-fast-480p": _video_config("bh2.0-fast-480p", 0.38, "second", "480P", range(4, 16), videos=3, audios=3, ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]),
    "Seedance 2.0 Fast 720P｜bh2.0-fast-720p": _video_config("bh2.0-fast-720p", 0.42, "second", "720P", range(4, 16), videos=3, audios=3, ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]),
    "Seedance 2.0 标准 480P｜bh2.0-480p": _video_config("bh2.0-480p", 0.48, "second", "480P", range(4, 16), videos=3, audios=3, ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]),
    "Seedance 2.0 标准 720P｜bh2.0-720p": _video_config("bh2.0-720p", 0.58, "second", "720P", range(4, 16), videos=3, audios=3, ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]),
    "Seedance 2.0 标准 1080P｜bh2.0-1080p": _video_config("bh2.0-1080p", 0.79, "second", "1080P", range(4, 16), videos=3, audios=3, ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]),
    "Seedance 2.0 Mini 480P｜bh2.0-mini-480p": _video_config("bh2.0-mini-480p", 0.25, "second", "480P", range(4, 16), videos=3, audios=3, ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]),
    "Seedance 2.0 Mini 720P｜bh2.0-mini-720p": _video_config("bh2.0-mini-720p", 0.35, "second", "720P", range(4, 16), videos=3, audios=3, ratios=["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"]),
    "Seedance 2.0 480P｜SD2.0-480P": _video_config("SD2.0-480P", 0.40, "second", "480P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 720P Fast｜SD2.0-720P-fast": _video_config("SD2.0-720P-fast", 0.39, "second", "720P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 720P｜SD2.0-720P": _video_config("SD2.0-720P", 0.50, "second", "720P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 1080P｜SD2.0-1080P": _video_config("SD2.0-1080P", 1.15, "second", "1080P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 4K｜sdvip4k": _video_config("sdvip4k", 2.20, "second", "4K", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 720P 优惠｜sdvip720p": _video_config("sdvip720p", 0.33, "second", "720P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 1080P 优惠｜sdvip1080p": _video_config("sdvip1080p", 0.60, "second", "1080P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 480P 高性价比｜gz-sd480p": _video_config("gz-sd480p", 0.19, "second", "480P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 720P 高性价比｜gz-sd720p": _video_config("gz-sd720p", 0.35, "second", "720P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 1080P 高性价比｜gz-sd1080p": _video_config("gz-sd1080p", 0.70, "second", "1080P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 4K 高性价比｜gz-sd4k": _video_config("gz-sd4k", 1.60, "second", "4K", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 不卡脸｜sdquan-2-miao": _video_config("sdquan-2-miao", 0.275, "second", "720P", [5, 10, 15]),
    "全能视频 1.1｜wanneng1.1": _video_config("wanneng1.1", 0.18, "second", "720P", range(4, 16)),
    "豆包 Fast｜doubaofast": _video_config("doubaofast", 0.258, "second", "720P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 Fast 福利｜sd2-fast福利": _video_config("sd2-fast福利", 2.36, "request", "720P", range(4, 16), images=4, videos=3, audios=3),
    "Seedance 2.0 福利｜sd2-福利": _video_config("sd2-福利", 2.98, "request", "720P", range(4, 16), images=4, videos=3, audios=3),
    "全能视频 2.0 B线｜B-quannengship2.0": _video_config("B-quannengship2.0", 3.45, "request", "720P", [5, 10, 15]),
    "全能视频 2.0｜quanneng2.0": _video_config("quanneng2.0", 5.25, "request", "720P", [15], audios=3),
    "全能视频 2.0 九图特惠｜quanneng2.0-9tu": _video_config("quanneng2.0-9tu", 1.58, "request", "720P", [15]),
    "全能视频 2.0 多模态｜video2.0": _video_config("video2.0", 4.85, "request", "720P", range(4, 16), videos=3, audios=3),
    "Seedance 2.0 VIP 720P｜sd2-vip720p": _video_config("sd2-vip720p", 3.55, "request", "720P", [15]),
    "Seedance 2.0 Fast VIP 720P｜sd2-vip720p-fast": _video_config("sd2-vip720p-fast", 3.75, "request", "720P", range(4, 16), videos=3, audios=3),
    "可灵 3｜keling-3": _video_config("keling-3", 0.90, "request", "720P", [15], images=2, audios=3),
    "Sora 2 图生视频｜xb-sora2": _video_config("xb-sora2", 0.78, "request", "720P", [8, 12], images=1, audios=3, image_required=True, supports_frames=False),
    "快乐 1.0｜me-kuaile1.0": _video_config("me-kuaile1.0", 1.85, "request", ["720P", "1080P"], [5, 10, 15], images=5, audios=3),
    "Sora 2 Z｜sora-2-z": _video_config("sora-2-z", 0.88, "request", "720P", [12], images=1, audios=3),
    "Veo Omni Flash｜veo-omni-flash": _video_config("veo-omni-flash", 0.88, "request", "720P", [10], images=5, audios=3, image_required=True, supports_frames=False),
    "Grok 视频 3 Pro｜grok-video-3-pro": _video_config("grok-video-3-pro", 0.65, "request", ["480P", "540P", "720P", "1080P"], [10]),
    "Grok 视频 3 Max｜grok-video-3-max": _video_config("grok-video-3-max", 0.65, "request", ["480P", "540P", "720P", "1080P"], [15]),
    "Grok 视频 1.5 Pro｜grok-video-1.5-pro": _video_config("grok-video-1.5-pro", 0.65, "request", ["480P", "720P"], [10], images=1, image_required=True, supports_frames=False),
    "Grok 视频 1.5 Max｜grok-video-1.5-max": _video_config("grok-video-1.5-max", 0.65, "request", ["480P", "720P"], [15], images=1, image_required=True, supports_frames=False),
}


LLM_MODELS = {
    "GPT-4o（多模态）｜gpt-4o": {"id": "gpt-4o", "input": 1.75, "output": 7, "vision": True},
    "GPT-4o Mini（多模态）｜gpt-4o-mini": {"id": "gpt-4o-mini", "input": 0.105, "output": 0.42, "vision": True},
    "GPT-5 对话版｜gpt-5-chat-latest": {"id": "gpt-5-chat-latest", "input": 0.875, "output": 7},
    "GPT-5 Mini｜gpt-5-mini": {"id": "gpt-5-mini", "input": 0.175, "output": 1.4},
    "OpenAI o3 推理｜o3": {"id": "o3", "input": 1.4, "output": 5.6, "reasoning": True},
    "OpenAI o4-mini 推理｜o4-mini": {"id": "o4-mini", "input": 0.77, "output": 3.08, "reasoning": True},
    "Claude Opus 4.8｜claude-opus-4-8": {"id": "claude-opus-4-8", "input": 10.5, "output": 52.5},
    "Claude Sonnet 4.5｜claude-sonnet-4-5": {"id": "claude-sonnet-4-5", "input": 2.1, "output": 10.5},
    "Claude Haiku 4.5｜claude-haiku-4-5": {"id": "claude-haiku-4-5", "input": 0.7, "output": 3.5},
    "Gemini 2.5 Pro（多模态）｜gemini-2.5-pro": {"id": "gemini-2.5-pro", "input": 0.875, "output": 7, "vision": True},
    "Gemini 2.5 Flash｜gemini-2.5-flash": {"id": "gemini-2.5-flash", "input": 0.21, "output": 1.75},
    "DeepSeek V3 对话｜deepseek-chat": {"id": "deepseek-chat", "input": 0.196, "output": 0.294},
    "DeepSeek R1 推理｜deepseek-reasoner": {"id": "deepseek-reasoner", "input": 0.385, "output": 1.54},
    "MiniMax M2｜minimax-m2": {"id": "minimax-m2", "input": 0.21, "output": 0.84},
}


ALL_IMAGE_SIZES = list(dict.fromkeys(
    ["模型默认"]
    + [ratio for config in IMAGE_MODELS.values() for ratio in config.get("ratio_sizes", {})]
    + [size for config in IMAGE_MODELS.values() for size in config["sizes"]]
))
IMAGE_QUALITY_MAP = {"模型默认": None, "低画质": "low", "标准画质": "medium", "高画质": "high"}
IMAGE_RESOLUTION_MAP = {"模型默认": None, "1K": "1K", "2K": "2K", "4K": "4K"}
VIDEO_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "2:3", "3:2", "21:9"]
VIDEO_RESOLUTIONS = ["模型默认", "480P", "540P", "720P", "1080P", "4K"]


def _log_info(message):
    print(f"[dapaoAPI-低价全能API] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-低价全能API] 错误：{message}")


def _normalize_image_size(config, requested_size):
    if requested_size == "模型默认" or requested_size in config["sizes"]:
        return requested_size
    mapped_size = config.get("ratio_sizes", {}).get(str(requested_size))
    if mapped_size:
        return mapped_size
    raise ValueError(f"{config['id']} 不支持图片尺寸/比例 {requested_size}，请重新选择。")


def _merge_extra_parameters(payload, extra, protected_fields):
    conflicts = sorted(set(extra).intersection(protected_fields))
    if conflicts:
        raise ValueError(f"额外参数JSON不能覆盖节点核心参数：{', '.join(conflicts)}")
    payload.update(extra)


def _blank_image(width=1024, height=1024):
    return torch.zeros((1, height, width, 3), dtype=torch.float32)


def _pil_to_tensor(image):
    image = image.convert("RGB")
    return torch.from_numpy(np.asarray(image).astype(np.float32) / 255.0).unsqueeze(0)


def _tensor_to_png_items(image_tensor):
    items = []
    for index in range(image_tensor.shape[0]):
        array = np.clip(image_tensor[index].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        image = Image.fromarray(array).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        items.append(buffer.getvalue())
    return items


def _tensor_to_data_uri(image_tensor):
    return "data:image/png;base64," + base64.b64encode(_tensor_to_png_items(image_tensor)[0]).decode("ascii")


def _audio_to_wav_bytes(audio_input):
    if not isinstance(audio_input, dict):
        return None
    waveform = audio_input.get("waveform")
    sample_rate = audio_input.get("sample_rate") or audio_input.get("sampler_rate") or 44100
    if waveform is None:
        return None
    if hasattr(waveform, "cpu"):
        waveform = waveform.cpu().numpy()
    waveform = np.squeeze(np.asarray(waveform))
    if waveform.ndim == 1:
        waveform = waveform.reshape(-1, 1)
    elif waveform.ndim == 2 and waveform.shape[0] < waveform.shape[1]:
        waveform = waveform.T
    if np.issubdtype(waveform.dtype, np.floating):
        waveform = (np.clip(waveform, -1.0, 1.0) * 32767).astype(np.int16)
    else:
        waveform = waveform.astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(int(waveform.shape[1]))
        handle.setsampwidth(2)
        handle.setframerate(int(sample_rate))
        handle.writeframes(waveform.tobytes())
    return buffer.getvalue()


def _parse_extra_json(value):
    try:
        data = json.loads((value or "{}").strip() or "{}")
    except json.JSONDecodeError as error:
        raise ValueError(f"额外参数JSON格式错误：{error}") from error
    if not isinstance(data, dict):
        raise ValueError("额外参数JSON必须是 JSON 对象。")
    return data


def _response_error(response):
    text = response.text[:1000]
    try:
        data = response.json()
        if isinstance(data, dict):
            error = data.get("error")
            if isinstance(error, dict):
                return error.get("message") or error.get("code") or text
            return data.get("message") or data.get("msg") or error or text
    except Exception:
        pass
    return text


def _task_response_layers(result):
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


def _task_state(result):
    layers = _task_response_layers(result)
    statuses = [str(layer.get("status", "")).strip().lower() for layer in layers if layer.get("status") is not None]
    failed = {"failed", "failure", "error", "cancelled", "canceled", "rejected"}
    succeeded = {"succeeded", "success", "completed", "complete"}
    processing = {"processing", "pending", "queued", "running", "in_progress", "not_start"}
    if any(status in failed for status in statuses):
        status = "failed"
    elif any(status in succeeded for status in statuses):
        status = "succeeded"
    elif any(status in processing for status in statuses):
        status = "processing"
    else:
        status = statuses[0] if statuses else ""

    message = ""
    for layer in reversed(layers):
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
        if message:
            break

    progress = None
    for layer in layers:
        value = layer.get("progress")
        if isinstance(value, str):
            value = value.strip().rstrip("%")
        try:
            progress = float(value)
            break
        except (TypeError, ValueError):
            continue
    return status, progress, message


class BinghuoClient:
    def __init__(self, api_key, timeout, base_url=API_BASE_URL):
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = (base_url or API_BASE_URL).rstrip("/")

    def _headers(self, json_body=False):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "ComfyUI-dapaoAPI/LowPriceUniversal",
        }
        if json_body:
            headers["Content-Type"] = "application/json"
        return headers

    def request_json(self, method, path, **kwargs):
        url = path if path.startswith(("http://", "https://")) else f"{self.base_url}/{path.lstrip('/')}"
        headers = kwargs.pop("headers", self._headers(json_body="json" in kwargs))
        last_error = None
        attempts = 3 if method.upper() == "GET" else 1
        for attempt in range(attempts):
            try:
                response = requests.request(method, url, headers=headers, timeout=self.timeout, **kwargs)
                if response.status_code >= 400:
                    message = _response_error(response)
                    if response.status_code == 401:
                        raise RuntimeError(f"认证失败 401：请检查 API 密钥。接口返回：{message}")
                    if response.status_code == 402:
                        raise RuntimeError(f"余额不足 402：请充值后再试。接口返回：{message}")
                    if response.status_code == 429:
                        raise RuntimeError(f"请求过频 429：请稍后重试。接口返回：{message}")
                    raise RuntimeError(f"API 请求失败 {response.status_code}：{message}")
                try:
                    return response.json()
                except json.JSONDecodeError as error:
                    raise RuntimeError(f"API 返回内容不是 JSON：{response.text[:500]}") from error
            except (requests.ConnectionError, requests.Timeout) as error:
                last_error = error
                if attempt < attempts - 1:
                    time.sleep(attempt + 1)
                    continue
                if attempts == 1:
                    raise RuntimeError(f"API 连接失败：{error}。提交类请求不会自动重试，以免重复扣费。") from error
                raise RuntimeError(f"API 连接失败，已尝试 {attempts} 次：{error}") from error
        raise last_error

    def upload(self, content, filename, mime_type):
        limits = {
            "image": (10 * 1024 * 1024, "图片", "10MB"),
            "audio": (50 * 1024 * 1024, "音频", "50MB"),
            "video": (60 * 1024 * 1024, "视频", "60MB"),
        }
        media_kind = mime_type.split("/", 1)[0]
        if media_kind in limits and len(content) > limits[media_kind][0]:
            raise ValueError(f"{limits[media_kind][1]}素材超过上传上限 {limits[media_kind][2]}，请压缩或裁剪后重试。")
        result = self.request_json(
            "POST",
            "/assets/uploads",
            headers=self._headers(),
            files={"file": (filename, content, mime_type)},
        )
        url = result.get("url") if isinstance(result, dict) else None
        if not url:
            raise RuntimeError(f"素材上传成功但没有返回 URL：{json.dumps(result, ensure_ascii=False)[:800]}")
        return str(url)

    def poll(self, path, max_seconds, interval):
        started = time.monotonic()
        pbar = comfy.utils.ProgressBar(100) if comfy is not None else None
        while time.monotonic() - started < max_seconds:
            if comfy is not None:
                comfy.model_management.throw_exception_if_processing_interrupted()
            result = self.request_json("GET", path)
            status, progress, message = _task_state(result)
            if status == "succeeded":
                if pbar:
                    pbar.update_absolute(100)
                return result
            if status == "failed":
                raise RuntimeError(f"任务失败：{message or json.dumps(result, ensure_ascii=False)[:1000]}")
            if pbar:
                elapsed = time.monotonic() - started
                pbar.update_absolute(min(100, int(progress)) if progress is not None else min(95, int(elapsed / max_seconds * 95)))
            time.sleep(interval)
            if comfy is not None:
                comfy.model_management.throw_exception_if_processing_interrupted()
        raise RuntimeError(f"任务超过 {max_seconds} 秒仍未完成。")

    def download(self, url):
        response = requests.get(url, timeout=max(self.timeout, 300), allow_redirects=True)
        response.raise_for_status()
        return response.content


class BinghuoVideoAdapter:
    def __init__(self, video_url):
        self.video_url = video_url or ""

    def get_dimensions(self):
        return 1280, 720

    def save_to(self, output_path, format="auto", codec="auto", metadata=None):
        if not self.video_url:
            return False
        response = requests.get(self.video_url, stream=True, timeout=300, allow_redirects=True)
        response.raise_for_status()
        with open(output_path, "wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    handle.write(chunk)
        return True


def _extract_task_id(result):
    if not isinstance(result, dict):
        return ""
    return str(result.get("task_id") or result.get("id") or "")


def _extract_video_url(result):
    if not isinstance(result, dict):
        return ""
    for key in ("result_url", "url", "video_url"):
        value = result.get(key)
        if isinstance(value, str) and value.startswith(("http://", "https://")):
            return value
    for key in ("data", "result", "output"):
        value = result.get(key)
        if isinstance(value, dict):
            url = _extract_video_url(value)
            if url:
                return url
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    url = _extract_video_url(item)
                    if url:
                        return url
    return ""


def _extract_image_items(result):
    if isinstance(result, dict) and isinstance(result.get("data"), list):
        documented_items = []
        for item in result["data"]:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("b64_json"), str) and item["b64_json"]:
                documented_items.append(("base64", item["b64_json"]))
                continue
            for key in ("url", "result_url", "image_url"):
                value = item.get(key)
                if isinstance(value, str) and value.startswith(("http://", "https://", "data:image/")):
                    documented_items.append(("url", value))
                    break
        if documented_items:
            return documented_items

    items = []
    seen = set()

    def add(kind, value):
        if not isinstance(value, str) or not value or value in seen:
            return
        seen.add(value)
        items.append((kind, value))

    def walk(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key in {"b64_json", "base64", "image_base64"}:
                    add("base64", item)
                elif key in {"url", "image_url", "result_url"}:
                    if isinstance(item, dict):
                        walk(item)
                    elif isinstance(item, str) and item.startswith(("http://", "https://", "data:image/")):
                        add("url", item)
                else:
                    walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(result)
    return items


def _image_item_to_pil(client, kind, value):
    if kind == "base64":
        content = base64.b64decode(value)
    elif value.startswith("data:image/"):
        content = base64.b64decode(value.split(",", 1)[1])
    else:
        content = client.download(value)
    return Image.open(io.BytesIO(content)).convert("RGB")


def _video_input_to_bytes(video_input):
    if isinstance(video_input, str) and os.path.isfile(video_input):
        with open(video_input, "rb") as handle:
            return handle.read()
    if not hasattr(video_input, "save_to"):
        raise ValueError("无法读取 VIDEO 输入，请改用视频公网 URL。")
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    handle.close()
    try:
        if not video_input.save_to(handle.name):
            raise ValueError("VIDEO 输入保存失败。")
        with open(handle.name, "rb") as file_handle:
            return file_handle.read()
    finally:
        try:
            os.remove(handle.name)
        except OSError:
            pass


class DapaoLowPriceUniversalImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}", "tooltip": "补充文档中的高级参数；不能覆盖模型、尺寸等节点核心参数。"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 3600, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 900, "min": 30, "max": 1800, "step": 10}),
        }
        for index in range(1, 10):
            optional[f"🖼️ 图像{index}"] = ("IMAGE", {"tooltip": f"图生图参考图{index}，最多9张。"})
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入炳火 API 令牌", "tooltip": "仅用于请求，不会写入配置文件。"}),
                "🤖 模型": (list(IMAGE_MODELS), {"default": next(iter(IMAGE_MODELS))}),
                "🔀 模式": (["文生图", "图生图"], {"default": "文生图"}),
                "📝 提示词": ("STRING", {"multiline": True, "default": "一张高端商业摄影海报，干净的自然光，细节清晰，质感高级"}),
                "📐 图片尺寸/比例": (ALL_IMAGE_SIZES, {"default": "模型默认"}),
                "🧩 清晰度": (list(IMAGE_RESOLUTION_MAP), {"default": "模型默认"}),
                "🎨 画质": (list(IMAGE_QUALITY_MAP), {"default": "模型默认"}),
                "🖼️ 出图数量": ("INT", {"default": 1, "min": 1, "max": 10, "step": 1}),
                "⚡ 异步模式": ("BOOLEAN", {"default": False, "tooltip": "多图长任务可开启；提交后自动轮询。"}),
                "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": "randomize", "tooltip": "仅控制 ComfyUI 缓存，不发送给接口。"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "炳火低价全能图像：GPT Image、Nano Banana、GR Banana、Gemini 图像生成与编辑 @炮老师的小课堂"

    def _collect_reference_urls(self, kwargs, client, limit):
        urls = []
        for input_index in range(1, 10):
            image_tensor = kwargs.get(f"🖼️ 图像{input_index}")
            if image_tensor is None:
                continue
            for batch_index, content in enumerate(_tensor_to_png_items(image_tensor), start=1):
                if len(urls) >= limit:
                    return urls
                urls.append(client.upload(content, f"image_{input_index}_{batch_index}.png", "image/png"))
        return urls

    @staticmethod
    def _gemini_payload(model_id, prompt, image_urls, size):
        content = [{"type": "text", "text": prompt}]
        for url in image_urls:
            content.append({"type": "image_url", "image_url": {"url": url}})
        payload = {"model": model_id, "messages": [{"role": "user", "content": content}]}
        if size != "模型默认":
            payload["size"] = size
        return payload

    def generate(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_label = kwargs.get("🤖 模型", next(iter(IMAGE_MODELS)))
        config = IMAGE_MODELS[model_label]
        requested_model_id = config["id"]
        mode = kwargs.get("🔀 模式", "文生图")
        prompt = (kwargs.get("📝 提示词") or "").strip()
        requested_size = kwargs.get("📐 图片尺寸/比例", "模型默认")
        size = requested_size
        legacy_control = kwargs.get("🎨 画质/清晰度", "模型默认")
        quality_label = kwargs.get("🎨 画质", "模型默认")
        resolution_label = kwargs.get("🧩 清晰度", "模型默认")
        if quality_label in IMAGE_RESOLUTION_MAP and resolution_label == "模型默认":
            resolution_label = quality_label
            quality_label = "模型默认"
        if quality_label == "模型默认" and legacy_control in IMAGE_QUALITY_MAP:
            quality_label = legacy_control
        if resolution_label == "模型默认" and legacy_control in IMAGE_RESOLUTION_MAP:
            resolution_label = legacy_control
        quality = IMAGE_QUALITY_MAP.get(quality_label)
        resolution = IMAGE_RESOLUTION_MAP.get(resolution_label)
        count = int(kwargs.get("🖼️ 出图数量", 1))
        async_mode = bool(kwargs.get("⚡ 异步模式", False))
        timeout = int(kwargs.get("⌛ 请求超时", 900))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1200))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        submitted = {}
        final = {}
        try:
            if config["id"] in PH_IMAGE_MODEL_IDS and resolution in PH_IMAGE_RESOLUTION_MODELS:
                config = IMAGE_MODELS_BY_ID[PH_IMAGE_RESOLUTION_MODELS[resolution]][1]
                resolution = None
            if mode not in config["modes"]:
                raise ValueError(f"{config['id']} 不支持模式“{mode}”，可选：{'、'.join(config['modes'])}。")
            size = _normalize_image_size(config, size)
            if quality is not None and quality not in config["qualities"]:
                quality = None
            allowed_resolutions = config.get("resolutions", [])
            if resolution and resolution not in allowed_resolutions:
                resolution = None
            count = min(max(count, 1), config["max_n"])
            if config.get("gemini") and mode == "图生图":
                count = 1
                async_mode = False
            if not api_key:
                raise ValueError("请填写炳火 API 密钥。")
            if not prompt:
                raise ValueError("提示词不能为空。")

            client = BinghuoClient(api_key, timeout)
            image_urls = self._collect_reference_urls(kwargs, client, config["max_images"]) if mode == "图生图" else []
            if len(image_urls) < config.get("min_images", 0):
                raise ValueError(f"{config['id']} 必须接入至少 {config['min_images']} 张参考图。")
            if mode == "图生图" and not image_urls:
                raise ValueError("选择图生图时，请至少接入一张参考图。")

            extra = _parse_extra_json(kwargs.get("📋 额外参数JSON", "{}"))
            started = time.time()
            if config.get("gemini") and image_urls:
                if count != 1:
                    raise ValueError("Gemini 图生图通过对话端点调用，出图数量请设为 1。")
                payload = self._gemini_payload(config["id"], prompt, image_urls, size)
                _merge_extra_parameters(payload, extra, {"model", "messages", "size", "n", "async"})
                submitted = client.request_json("POST", "/chat/completions", json=payload)
                final = submitted
            else:
                payload = {"model": config["id"], "prompt": prompt, "n": count}
                if size != "模型默认":
                    payload["size"] = size
                if quality:
                    payload["quality"] = quality
                if resolution:
                    payload[config["clarity_field"]] = resolution
                if image_urls:
                    reference_field = config.get("reference_field", "image_urls")
                    payload[reference_field] = image_urls[0] if reference_field == "image" and len(image_urls) == 1 else image_urls
                if async_mode:
                    payload["async"] = True
                _merge_extra_parameters(
                    payload,
                    extra,
                    {"model", "prompt", "n", "size", "quality", "image", "image_urls", "images", "async"},
                )
                _log_info(
                    f"提交图片任务：model={payload.get('model')}，size={payload.get('size', '模型默认')}，"
                    f"quality={payload.get('quality', '模型默认')}，n={payload.get('n')}，参考图={len(image_urls)}张"
                )
                submitted = client.request_json("POST", "/images/generations", json=payload)
                task_id = _extract_task_id(submitted)
                final = client.poll(f"/images/generations/{task_id}", max_seconds, interval) if task_id and str(submitted.get("status", "")).lower() == "processing" else submitted

            image_items = _extract_image_items(final)
            if not image_items:
                raise RuntimeError(f"任务完成但没有返回图片：{json.dumps(final, ensure_ascii=False)[:1000]}")
            tensors = [_pil_to_tensor(_image_item_to_pil(client, kind, value)) for kind, value in image_items]
            images = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)
            output_width = int(images.shape[2])
            output_height = int(images.shape[1])
            expected_match = re.fullmatch(r"(\d+)x(\d+)", str(size))
            size_warning = ""
            if expected_match:
                expected_width, expected_height = map(int, expected_match.groups())
                if (output_width, output_height) != (expected_width, expected_height):
                    size_warning = (
                        f"⚠️ 上游返回尺寸不符：请求 {expected_width}×{expected_height}，"
                        f"实际 {output_width}×{output_height}。节点未缩放图片。\n"
                    )
                    _log_error(size_warning.strip())
            first_url = next((value for kind, value in image_items if kind == "url" and value.startswith("http")), "")
            elapsed = time.time() - started
            completion_title = "⚠️ 图像任务完成，但上游返回尺寸不符" if size_warning else "✅ 低价全能图像任务完成"
            info = (
                f"{completion_title}\n"
                f"🤖 界面模型：{requested_model_id}\n📤 实际提交模型：{config['id']}\n🔀 模式：{mode}\n"
                f"📐 界面选择：{requested_size}\n📤 实际提交尺寸：{size}\n"
                f"🎨 画质：{quality or '模型默认'}\n🧩 清晰度：{resolution_label if resolution_label != '模型默认' else '由模型决定'}\n"
                f"🖼️ 参考图：{len(image_urls)} 张\n"
                f"🧭 图生图字段：{config.get('reference_field', 'image_urls') if image_urls else '未提交'}\n"
                f"{size_warning}"
                f"🖼️ 结果：{len(tensors)} 张，实际尺寸：{output_width}×{output_height}\n⏱️ 耗时：{elapsed:.2f} 秒\n\n"
                + json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2)
            )
            return images, first_url, info
        except Exception as error:
            message = f"❌ 低价全能图像生成失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            return _blank_image(), "", message + "\n\n" + json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2)


class DapaoLowPriceUniversalVideoNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "首尾帧模式的首帧。"}),
            "🏁 尾帧图": ("IMAGE", {"tooltip": "首尾帧模式的尾帧。"}),
            "🌐 首帧公网URL": ("STRING", {"default": ""}),
            "🌐 尾帧公网URL": ("STRING", {"default": ""}),
            "🎞️ 参考视频URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "每行一个公网视频 URL，最多3个"}),
            "🎵 参考音频URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "每行一个公网音频 URL，最多3个"}),
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1800, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 30, "max": 600, "step": 10}),
        }
        for index in range(1, 10):
            optional[f"🖼️ 参考图{index}"] = ("IMAGE",)
        for index in range(1, 4):
            optional[f"🎞️ 参考视频{index}"] = (IO.VIDEO,)
            optional[f"🎵 参考音频{index}"] = ("AUDIO",)
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入炳火 API 令牌"}),
                "🤖 模型": (list(VIDEO_MODELS), {"default": "Seedance 2.0 Mini 480P｜bh2.0-mini-480p"}),
                "🎛️ 生成模式": (["文生视频", "图生视频", "首尾帧生视频", "多模态参考"], {"default": "文生视频"}),
                "📝 提示词": ("STRING", {"multiline": True, "default": "电影感镜头缓慢推进，主体动作自然，光影细腻，画面稳定且细节丰富"}),
                "🧩 分辨率": (VIDEO_RESOLUTIONS, {"default": "模型默认"}),
                "⏱️ 时长(秒)": ([str(value) for value in range(4, 16)], {"default": "5"}),
                "📐 视频比例": (VIDEO_RATIOS, {"default": "16:9"}),
                "🔊 生成音频": ("BOOLEAN", {"default": True}),
                "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": "randomize", "tooltip": "仅控制 ComfyUI 缓存。"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "炳火低价全能视频：Seedance、全能视频、可灵、Sora、Veo、Grok 视频 @炮老师的小课堂"

    @staticmethod
    def _split_urls(value):
        return [item.strip() for item in str(value or "").replace("，", ",").replace("\n", ",").split(",") if item.strip()]

    def _collect_images(self, kwargs, client, limit):
        urls = []
        for index in range(1, 10):
            image = kwargs.get(f"🖼️ 参考图{index}")
            if image is None:
                continue
            for batch_index, content in enumerate(_tensor_to_png_items(image), start=1):
                if len(urls) >= limit:
                    return urls
                urls.append(client.upload(content, f"video_ref_{index}_{batch_index}.png", "image/png"))
        return urls

    def _collect_videos(self, kwargs, client, limit):
        urls = self._split_urls(kwargs.get("🎞️ 参考视频URL列表"))
        for index in range(1, 4):
            video = kwargs.get(f"🎞️ 参考视频{index}")
            if video is not None and len(urls) < limit:
                urls.append(client.upload(_video_input_to_bytes(video), f"reference_{index}.mp4", "video/mp4"))
        return urls[:limit]

    def _collect_audios(self, kwargs, client, limit):
        urls = self._split_urls(kwargs.get("🎵 参考音频URL列表"))
        for index in range(1, 4):
            audio = kwargs.get(f"🎵 参考音频{index}")
            if audio is not None and len(urls) < limit:
                content = _audio_to_wav_bytes(audio)
                if content:
                    urls.append(client.upload(content, f"reference_{index}.wav", "audio/wav"))
        return urls[:limit]

    @staticmethod
    def _frame_url(kwargs, client, input_name, url_name, filename):
        url = (kwargs.get(url_name) or "").strip()
        image = kwargs.get(input_name)
        if url and image is not None:
            raise ValueError(f"{input_name} 与 {url_name} 只能使用一个。")
        if url:
            return url
        if image is not None:
            return client.upload(_tensor_to_png_items(image)[0], filename, "image/png")
        return ""

    def generate(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_label = kwargs.get("🤖 模型", "Seedance 2.0 Mini 480P｜bh2.0-mini-480p")
        config = VIDEO_MODELS[model_label]
        mode = kwargs.get("🎛️ 生成模式", "文生视频")
        prompt = (kwargs.get("📝 提示词") or "").strip()
        resolution = kwargs.get("🧩 分辨率", "模型默认")
        duration = int(kwargs.get("⏱️ 时长(秒)", 5))
        ratio = kwargs.get("📐 视频比例", "16:9")
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1800))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        submitted = {}
        final = {}
        try:
            if mode not in config["modes"]:
                raise ValueError(f"{config['id']} 不支持模式“{mode}”。")
            if duration not in config["durations"]:
                raise ValueError(f"{config['id']} 不支持时长 {duration} 秒，可选：{'、'.join(map(str, config['durations']))}。")
            final_resolution = config["resolutions"][0] if resolution == "模型默认" else resolution
            if final_resolution not in config["resolutions"]:
                raise ValueError(f"{config['id']} 不支持分辨率 {resolution}，可选：{'、'.join(config['resolutions'])}。")
            if ratio not in config["ratios"]:
                raise ValueError(f"{config['id']} 不支持比例 {ratio}，可选：{'、'.join(config['ratios'])}。")
            if not api_key:
                raise ValueError("请填写炳火 API 密钥。")
            if not prompt:
                raise ValueError("提示词不能为空。")

            client = BinghuoClient(api_key, timeout)
            image_urls = []
            video_urls = []
            audio_urls = []
            payload = {
                "model": config["id"], "prompt": prompt, "duration": duration,
                "ratio": ratio,
            }
            generate_audio = bool(kwargs.get("🔊 生成音频", True))
            if not generate_audio:
                payload["generate_audio"] = False
            if len(config["resolutions"]) > 1:
                payload["resolution"] = final_resolution

            if mode == "图生视频":
                image_urls = self._collect_images(kwargs, client, config["max_images"])
            elif mode == "首尾帧生视频":
                start_url = self._frame_url(kwargs, client, "🎬 首帧图", "🌐 首帧公网URL", "start_frame.png")
                end_url = self._frame_url(kwargs, client, "🏁 尾帧图", "🌐 尾帧公网URL", "end_frame.png")
                if not start_url:
                    raise ValueError("首尾帧生视频必须接入首帧图或填写首帧公网 URL。")
                payload["start_frame"] = [start_url]
                if end_url:
                    payload["end_frame"] = [end_url]
            elif mode == "多模态参考":
                image_urls = self._collect_images(kwargs, client, config["max_images"])
                if config["max_videos"]:
                    video_urls = self._collect_videos(kwargs, client, config["max_videos"])
                elif self._split_urls(kwargs.get("🎞️ 参考视频URL列表")) or any(kwargs.get(f"🎞️ 参考视频{i}") is not None for i in range(1, 4)):
                    raise ValueError(f"{config['id']} 不支持参考视频。")
                if config["max_audios"]:
                    audio_urls = self._collect_audios(kwargs, client, config["max_audios"])
                elif self._split_urls(kwargs.get("🎵 参考音频URL列表")) or any(kwargs.get(f"🎵 参考音频{i}") is not None for i in range(1, 4)):
                    raise ValueError(f"{config['id']} 不支持参考音频。")

            if config["image_required"] and not image_urls and "start_frame" not in payload:
                raise ValueError(f"{config['id']} 是图生视频模型，必须至少接入一张参考图。")
            if mode == "图生视频" and not image_urls:
                raise ValueError("选择图生视频时，请至少接入一张参考图。")
            if image_urls:
                payload["images"] = image_urls
            if video_urls:
                payload["reference_videos"] = video_urls
            if audio_urls:
                payload["reference_audios"] = audio_urls
            if audio_urls and config["id"].startswith("bh2.0-") and not image_urls and not video_urls:
                raise ValueError("bh2.0 系列使用参考音频时，必须同时提供至少一张参考图或一个参考视频。")
            if audio_urls and config["id"].startswith("gz-sd") and not image_urls:
                raise ValueError("gz-sd 系列使用参考音频时，必须同时提供至少一张参考图。")
            _merge_extra_parameters(
                payload,
                _parse_extra_json(kwargs.get("📋 额外参数JSON", "{}")),
                {
                    "model", "prompt", "duration", "resolution", "ratio", "aspect_ratio", "size",
                    "images", "reference_images", "start_frame", "end_frame", "reference_videos",
                    "reference_audios", "generate_audio", "n",
                },
            )

            started = time.time()
            _log_info(
                f"提交视频任务：model={config['id']}，mode={mode}，duration={duration}，"
                f"resolution={final_resolution}，ratio={ratio}，audio={'默认开启' if generate_audio else '关闭'}，"
                f"参考图={len(image_urls)}张，参考视频={len(video_urls)}个，参考音频={len(audio_urls)}个"
            )
            submitted = client.request_json("POST", "/video/generations", json=payload)
            task_id = _extract_task_id(submitted)
            if not task_id:
                raise RuntimeError(f"提交成功但没有返回任务 ID：{json.dumps(submitted, ensure_ascii=False)[:1000]}")
            final = client.poll(f"/video/generations/{task_id}", max_seconds, interval)
            video_url = _extract_video_url(final)
            if not video_url:
                raise RuntimeError(f"任务完成但没有返回视频 URL：{json.dumps(final, ensure_ascii=False)[:1000]}")
            elapsed = time.time() - started
            price = config["price"] * duration if config["billing"] == "second" else config["price"]
            if video_urls:
                if config["id"].startswith("bh2.0-"):
                    price *= 1.8
                elif config["id"] in {"SD2.0-720P-fast", "SD2.0-720P", "SD2.0-1080P", "sdvip4k", "gz-sd480p", "gz-sd720p", "gz-sd1080p", "gz-sd4k"}:
                    price *= 2
            info = (
                "✅ 低价全能视频任务完成\n"
                f"🤖 模型：{config['id']}\n🎛️ 模式：{mode}\n🧩 分辨率：{final_resolution}\n⏱️ 时长：{duration} 秒\n"
                f"📐 比例：{ratio}\n🖼️ 参考图：{len(image_urls)}\n🎞️ 参考视频：{len(video_urls)}\n🎵 参考音频：{len(audio_urls)}\n"
                f"💰 预估价格：¥{price:.3f}\n🆔 任务ID：{task_id}\n🔗 视频URL：{video_url}\n⏱️ 耗时：{elapsed:.2f} 秒\n\n"
                + json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2)
            )
            return BinghuoVideoAdapter(video_url), task_id, info, video_url
        except Exception as error:
            message = f"❌ 低价全能视频生成失败：{error}"
            if "fail_to_fetch_task" in str(error):
                message += "\n⚠️ 上游视频服务未能取得生成任务（fail_to_fetch_task）。请求未返回任务ID，节点不会自动重提，以免重复扣费；请稍后手动重试或更换模型。"
            _log_error(message)
            _log_error(traceback.format_exc())
            return BinghuoVideoAdapter(""), "", message + "\n\n" + json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2), ""


class DapaoLowPriceLLMChatNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}", "placeholder": "{\"response_format\":{\"type\":\"json_object\"}}"}),
            "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
        }
        for index in range(1, 9):
            optional[f"🖼️ 图像{index}"] = ("IMAGE", {"tooltip": "仅识图模型使用。"})
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入炳火 API 令牌"}),
                "🤖 模型": (list(LLM_MODELS), {"default": "GPT-4o Mini（多模态）｜gpt-4o-mini"}),
                "🎯 系统角色": ("STRING", {"multiline": True, "default": "你是一个专业、友好、准确的 AI 助手。"}),
                "💬 用户输入": ("STRING", {"multiline": True, "default": "你好，请帮我分析这段内容。"}),
                "🌡️ 温度": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01}),
                "📝 最大输出令牌": ("INT", {"default": 2048, "min": 1, "max": 65536, "step": 1}),
                "🎲 Top_P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff, "control_after_generate": "randomize", "tooltip": "仅控制 ComfyUI 缓存。"}),
                "⌛ 请求超时": ("INT", {"default": 300, "min": 30, "max": 1200, "step": 10}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "📄 完整响应", "ℹ️ 处理信息")
    FUNCTION = "chat"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "炳火低价 LLM 智能对话：GPT、Claude、Gemini、DeepSeek、MiniMax，支持多图识别 @炮老师的小课堂"

    @staticmethod
    def _extract_text(result):
        choices = result.get("choices", []) if isinstance(result, dict) else []
        if not choices:
            return ""
        message = choices[0].get("message", {}) if isinstance(choices[0], dict) else {}
        content = message.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(str(item.get("text", "")) for item in content if isinstance(item, dict) and item.get("text"))
        return ""

    def chat(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_label = kwargs.get("🤖 模型", "GPT-4o Mini（多模态）｜gpt-4o-mini")
        config = LLM_MODELS[model_label]
        skip_error = bool(kwargs.get("🚫 出错时跳过", False))
        try:
            if not api_key:
                raise ValueError("请填写炳火 API 密钥。")
            user_input = (kwargs.get("💬 用户输入") or "").strip()
            if not user_input:
                raise ValueError("用户输入不能为空。")
            messages = []
            system_role = (kwargs.get("🎯 系统角色") or "").strip()
            if system_role:
                messages.append({"role": "system", "content": system_role})
            image_uris = []
            if config.get("vision"):
                for index in range(1, 9):
                    image = kwargs.get(f"🖼️ 图像{index}")
                    if image is not None:
                        for batch in range(image.shape[0]):
                            image_uris.append(_tensor_to_data_uri(image[batch:batch + 1]))
            if image_uris:
                content = [{"type": "text", "text": user_input}]
                content.extend({"type": "image_url", "image_url": {"url": uri}} for uri in image_uris)
                messages.append({"role": "user", "content": content})
            else:
                messages.append({"role": "user", "content": user_input})
            payload = {
                "model": config["id"], "messages": messages,
                "max_tokens": int(kwargs.get("📝 最大输出令牌", 2048)),
                "stream": False,
            }
            if not config.get("reasoning"):
                payload["temperature"] = float(kwargs.get("🌡️ 温度", 0.7))
                payload["top_p"] = float(kwargs.get("🎲 Top_P", 1.0))
            _merge_extra_parameters(
                payload,
                _parse_extra_json(kwargs.get("📋 额外参数JSON", "{}")),
                {"model", "messages", "stream", "temperature", "max_tokens", "top_p"},
            )
            started = time.time()
            result = BinghuoClient(api_key, int(kwargs.get("⌛ 请求超时", 300))).request_json("POST", "/chat/completions", json=payload)
            text = self._extract_text(result)
            if not text:
                tool_calls = ((result.get("choices") or [{}])[0].get("message") or {}).get("tool_calls") if isinstance(result, dict) else None
                text = json.dumps(tool_calls, ensure_ascii=False, indent=2) if tool_calls else ""
            if not text:
                raise RuntimeError("模型返回内容为空。")
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            elapsed = time.time() - started
            info = (
                "✅ 低价 LLM 智能对话完成\n"
                f"🤖 模型：{config['id']}\n🖼️ 图像：{len(image_uris)} 张\n"
                f"📥 输入令牌：{usage.get('prompt_tokens', '未知')}\n📤 输出令牌：{usage.get('completion_tokens', '未知')}\n"
                f"⏱️ 耗时：{elapsed:.2f} 秒"
            )
            return text, json.dumps(result, ensure_ascii=False, indent=2), info
        except Exception as error:
            message = f"❌ 低价 LLM 智能对话失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            if skip_error:
                return message, json.dumps({"error": str(error)}, ensure_ascii=False, indent=2), message
            raise


class DapaoLowPriceSubtitleRemovalNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入炳火 API 令牌"}),
                "🔗 视频公网URL": ("STRING", {"default": "", "placeholder": "有本地 VIDEO 输入时可留空"}),
                "⏱️ 视频时长(秒)": ("INT", {"default": 10, "min": 1, "max": 600, "step": 1, "tooltip": "务必填写真实时长，用于计费。"}),
                "📐 视频分辨率": (["720x1280", "1280x720", "1080x1920", "1920x1080", "自定义"], {"default": "720x1280"}),
                "✏️ 自定义分辨率": ("STRING", {"default": "720x1280", "placeholder": "宽x高，例如 1080x1920"}),
                "🔁 最大轮询秒数": ("INT", {"default": 1800, "min": 60, "max": 7200, "step": 10}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30, "step": 1}),
                "⌛ 请求超时": ("INT", {"default": 120, "min": 30, "max": 600, "step": 10}),
            },
            "optional": {
                "🎞️ 输入视频": (IO.VIDEO, {"tooltip": "本地视频会先上传；与公网 URL 二选一。"}),
            },
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 无字幕视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "remove_subtitles"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "炳火低价视频去字幕：自动去除画面中的硬字幕 @炮老师的小课堂"

    def remove_subtitles(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        submitted = {}
        final = {}
        try:
            if not api_key:
                raise ValueError("请填写炳火 API 密钥。")
            client = BinghuoClient(api_key, timeout)
            video_url = (kwargs.get("🔗 视频公网URL") or "").strip()
            video_input = kwargs.get("🎞️ 输入视频")
            if video_url and video_input is not None:
                raise ValueError("输入视频与视频公网 URL 只能使用一个。")
            if not video_url and video_input is not None:
                video_url = client.upload(_video_input_to_bytes(video_input), "subtitle_input.mp4", "video/mp4")
            if not video_url.startswith(("http://", "https://")):
                raise ValueError("请接入本地视频，或填写公网可直接下载的视频 URL。")
            duration = int(kwargs.get("⏱️ 视频时长(秒)", 10))
            resolution = kwargs.get("📐 视频分辨率", "720x1280")
            if resolution == "自定义":
                resolution = (kwargs.get("✏️ 自定义分辨率") or "").strip()
            if not re.fullmatch(r"[1-9]\d*x[1-9]\d*", str(resolution)):
                raise ValueError("视频分辨率格式错误，请填写“宽x高”，例如 1080x1920。")
            payload = {"model": "去字幕", "video_url": video_url, "duration": duration, "resolution": resolution}
            started = time.time()
            submitted = client.request_json("POST", "/video/generations", json=payload)
            task_id = _extract_task_id(submitted)
            if not task_id:
                raise RuntimeError(f"提交成功但没有返回任务 ID：{json.dumps(submitted, ensure_ascii=False)[:1000]}")
            final = client.poll(
                f"/video/generations/{task_id}",
                int(kwargs.get("🔁 最大轮询秒数", 1800)),
                int(kwargs.get("⏱️ 轮询间隔", 5)),
            )
            result_url = _extract_video_url(final)
            if not result_url:
                raise RuntimeError(f"任务完成但没有返回视频 URL：{json.dumps(final, ensure_ascii=False)[:1000]}")
            info = (
                "✅ 视频去字幕完成\n"
                f"⏱️ 视频时长：{duration} 秒\n📐 分辨率：{resolution}\n💰 预估价格：¥{duration * 0.009:.3f}\n"
                f"🆔 任务ID：{task_id}\n🔗 视频URL：{result_url}\n⏱️ 耗时：{time.time() - started:.2f} 秒\n\n"
                + json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2)
            )
            return BinghuoVideoAdapter(result_url), task_id, info, result_url
        except Exception as error:
            message = f"❌ 视频去字幕失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            return BinghuoVideoAdapter(""), "", message + "\n\n" + json.dumps({"submit": submitted, "final": final}, ensure_ascii=False, indent=2), ""


NODE_CLASS_MAPPINGS = {
    IMAGE_NODE_NAME: DapaoLowPriceUniversalImageNode,
    VIDEO_NODE_NAME: DapaoLowPriceUniversalVideoNode,
    LLM_NODE_NAME: DapaoLowPriceLLMChatNode,
    SUBTITLE_NODE_NAME: DapaoLowPriceSubtitleRemovalNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    IMAGE_NODE_NAME: "🐠低价全能图像@炮老师的小课堂",
    VIDEO_NODE_NAME: "🐠低价全能视频@炮老师的小课堂",
    LLM_NODE_NAME: "🐠低价LLM智能对话@炮老师的小课堂",
    SUBTITLE_NODE_NAME: "🐠低价视频去字幕@炮老师的小课堂",
}
