"""Media preparation for the existing Seedance nodes; no node registrations."""
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import threading

import requests
from PIL import Image

from .image_input_utils import resize_pil_for_input, tensor_to_png_bytes

_IMAGES = threading.BoundedSemaphore(2)
_TRANSCODE = threading.BoundedSemaphore(1)


def _tool(name, args):
    executable = os.environ.get("DAPAO_" + name.upper() + "_PATH") or shutil.which(name)
    if not executable:
        raise ValueError(f"素材处理需要{name}，请安装FFmpeg或配置DAPAO_{name.upper()}_PATH。")
    options = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
    result = subprocess.run([executable, *args], capture_output=True, timeout=180, **options)
    if result.returncode:
        raise ValueError(f"{name}处理素材失败，请检查素材格式。")
    return result.stdout


def _probe(path):
    return json.loads(_tool("ffprobe", ["-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]))


def _download(url):
    # User-supplied media URLs never receive the gateway credential.
    with requests.get(url, stream=True, timeout=(10, 120)) as response:
        response.raise_for_status()
        chunks, total = [], 0
        for chunk in response.iter_content(1024 * 1024):
            total += len(chunk)
            if total > 200 * 1024 * 1024:
                raise ValueError("源素材超过200MiB，请先裁剪或压缩。")
            chunks.append(chunk)
        return b"".join(chunks)


def _image(content):
    with Image.open(io.BytesIO(content)) as source:
        image = resize_pil_for_input(source.convert("RGBA" if "A" in source.getbands() else "RGB"))
    width, height = image.size
    if min(width, height) <= 300 or not .4 < width / height < 2.5:
        raise ValueError("图片预处理后宽高须大于300像素、比例在0.4～2.5之间，请裁剪或更换。")
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    data = buffer.getvalue()
    if len(data) > 10 * 1024 * 1024:
        raise ValueError("图片预处理后超过10MiB，请裁剪或更换。")
    return data, "seedance.png", "image/png"


def _av(content, kind, keep_audio):
    with _TRANSCODE, tempfile.TemporaryDirectory(prefix="dapao-seedance-") as folder:
        source = Path(folder) / "input"
        source.write_bytes(content)
        info = _probe(source)
        duration = float(info.get("format", {}).get("duration", 0))
        if not 2 <= duration <= 15:
            raise ValueError("参考视频/音频须为2～15秒，请先裁剪；不会自动截断。")
        output = Path(folder) / ("output.mp4" if kind == "video" else "output.wav")
        args = ["-v", "error", "-y", "-i", str(source), "-map_metadata", "-1"]
        if kind == "video":
            rate = min(8_000_000, int(18 * 1024 * 1024 * 8 / duration) - 192_000)
            args += ["-map", "0:v:0", "-vf", "scale=w='min(1080,iw)':h='min(1080,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2,fps=30",
                     "-c:v", "libx264", "-threads", "2", "-pix_fmt", "yuv420p", "-b:v", str(rate), "-maxrate", str(rate), "-bufsize", str(rate * 2), "-movflags", "+faststart"]
            args += ["-map", "0:a:0?", "-c:a", "aac", "-ar", "48000", "-ac", "2"] if keep_audio else ["-an"]
        else:
            args += ["-map", "0:a:0", "-vn", "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le"]
        _tool("ffmpeg", [*args, str(output)])
        checked = _probe(output)
        if kind == "video":
            stream = next(s for s in checked["streams"] if s.get("codec_type") == "video")
            width, height = int(stream["width"]), int(stream["height"])
            if min(width, height) < 300 or not .4 <= width / height <= 2.5 or not 409600 <= width * height <= 2086876:
                raise ValueError("视频预处理后的尺寸不满足素材登记要求，请更换尺寸和比例合适的视频。")
        result_duration = float(checked["format"]["duration"])
        if not 2 <= result_duration <= 15:
            raise ValueError("转码后的素材时长须为2～15秒。")
        data = output.read_bytes()
        limit = 20 if kind == "video" else 15
        if len(data) > limit * 1024 * 1024:
            raise ValueError(f"素材转码后超过{limit}MiB，请裁剪或更换。")
        return (data, output.name, "video/mp4" if kind == "video" else "audio/wav"), result_duration


def prepare_inputs(node, kwargs, mode, overrides):
    """Preserve slot order, validate all media before any upload or paid POST."""
    from .seedance20_allround_video_node import _audio_to_wav_bytes, _video_to_bytes
    frames = [(name, kwargs.get(name)) for name in ("🎬 首帧图", "🏁 尾帧图") if kwargs.get(name) is not None]
    raw = {"image": [], "video": [], "audio": []}
    for kind, prefix, limit in (("image", "🖼️ 参考图", 9), ("video", "🎞️ 参考视频", 3), ("audio", "🎵 参考音频", 3)):
        # Detect now-unsupported saved 2.5 slots instead of silently dropping media.
        if any(value is not None and name.startswith(prefix) and name[len(prefix):].isdigit() and int(name[len(prefix):]) > limit for name, value in kwargs.items()):
            raise ValueError(f"{prefix}最多{limit}路，请移除超出的旧工作流输入。")
        values = [kwargs[f"{prefix}{i}"] for i in range(1, limit + 1) if kwargs.get(f"{prefix}{i}") is not None]
        urls = overrides[kind + "s" if kind != "image" else "images"]
        if values and urls:
            raise ValueError(f"{prefix}与同类公网URL请选择一种，避免素材被覆盖。")
        raw[kind] = [(v, False) for v in values] or [(v, True) for v in urls]
    if frames and any(raw.values()):
        raise ValueError("首尾帧与参考素材不能混用，请选择一种输入方式。")
    if frames:
        if kwargs.get("🎬 首帧图") is None:
            raise ValueError("尾帧必须搭配首帧。")
        raw["image"] = [(v, False) for _, v in frames]
    has_media = any(raw.values())
    if mode == "自动识别":
        mode = "首尾帧生视频" if frames else ("多模态参考" if has_media else "文生视频")
    if mode == "文生视频" and has_media:
        raise ValueError("已连接素材，请选择自动识别或对应素材模式。")
    if mode != "文生视频" and not has_media:
        raise ValueError("当前模式需要连接素材。")
    if mode in {"图生视频", "首尾帧生视频"} and (raw["video"] or raw["audio"]):
        raise ValueError("参考视频/音频请使用多模态参考模式。")
    if frames and mode not in {"首尾帧生视频", "图生视频"}:
        raise ValueError("首尾帧输入请使用自动识别或首尾帧模式。")
    if raw["audio"] and not raw["image"] and not raw["video"]:
        raise ValueError("参考音频不能单独输入。")
    media, image_bytes = [], 0
    for kind, values in raw.items():
        seconds, count = 0, 0
        for value, is_url in values:
            if is_url and value.startswith("asset://"):
                if not re.fullmatch(r"asset://file-[A-Za-z0-9_-]{1,59}", value):
                    raise ValueError("仅支持妙笔asset://file-...素材引用，不能填写RH或供应商素材ID。")
                parts = [value]
            elif kind == "image":
                with _IMAGES:
                    encoded = [_download(value)] if is_url else tensor_to_png_bytes(value)
                    if frames and len(encoded) != 1:
                        raise ValueError("首帧、尾帧插口各只能连接一张图片。")
                    parts = [_image(data) for data in encoded]
                    image_bytes += sum(len(p[0]) for p in parts)
            else:
                data = _download(value) if is_url else (_video_to_bytes(value) if kind == "video" else _audio_to_wav_bytes(value))
                part, duration = _av(data, kind, bool(kwargs.get("🎞️ 保留参考视频音轨", False)))
                seconds += duration
                parts = [part]
            count += len(parts)
            media.extend((kind, part, "reference_" + kind) for part in parts)
        if count > (9 if kind == "image" else 3) or seconds > 15:
            raise ValueError("最多9张图片、3段视频、3段音频；视频和音频各自合计不得超过15秒。")
    if image_bytes > 30 * 1024 * 1024:
        raise ValueError("参考图片合计超过30MiB，请减少素材。")
    if mode == "首尾帧生视频":
        if not 1 <= len(media) <= 2:
            raise ValueError("首尾帧模式需要1张首帧或2张首尾帧图片。")
        media = [(kind, source, "first_frame" if i == 0 else "last_frame") for i, (kind, source, _) in enumerate(media)]
    elif mode == "图生视频" and len(media) == 1:
        media = [(kind, source, "first_frame") for kind, source, _ in media]
    elif mode == "图生视频":
        mode = "多模态参考"
    return mode, media
