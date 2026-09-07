"""Shared upload-boundary preprocessing for dapaoAI image/audio/video inputs."""

from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageCms

from .image_input_utils import tensor_to_pil_images


MIB = 1024 * 1024
IMAGE_TARGET_BYTES = 8 * MIB
IMAGE_MAX_BYTES = 10 * MIB
VIDEO_TARGET_BYTES = 18 * MIB
VIDEO_MAX_BYTES = 20 * MIB
AUDIO_MAX_BYTES = 15 * MIB


def _srgb(image: Image.Image) -> Image.Image:
    """Normalize orientation/color where Pillow exposes an embedded profile."""
    image = image.copy()
    profile = image.info.get("icc_profile")
    if profile:
        try:
            source = ImageCms.ImageCmsProfile(io.BytesIO(profile))
            target = ImageCms.createProfile("sRGB")
            output_mode = "RGBA" if image.mode == "RGBA" else "RGB"
            image = ImageCms.profileToProfile(image, source, target, outputMode=output_mode)
        except Exception:
            image = image.convert("RGBA" if image.mode == "RGBA" else "RGB")
    return image


def prepare_image_tensor(image_tensor, *, prefix="reference", max_count=10):
    """Return optimized image blobs, preserving meaningful alpha as PNG."""
    images = tensor_to_pil_images(image_tensor, max_edge=2048)
    if len(images) > max_count:
        raise ValueError(f"图片批次最多 {max_count} 张。")
    blobs = []
    for index, image in enumerate(images, 1):
        image = _srgb(image)
        has_alpha = image.mode == "RGBA" and image.getchannel("A").getextrema()[0] < 255
        if has_alpha:
            buffer = io.BytesIO()
            image.save(buffer, format="PNG", optimize=True, icc_profile=None)
            content, extension, mime = buffer.getvalue(), "png", "image/png"
        else:
            rgb = image.convert("RGB")
            content = b""
            for quality in (88, 84, 80, 76, 72):
                buffer = io.BytesIO()
                rgb.save(buffer, format="JPEG", quality=quality, optimize=False, progressive=False,
                         subsampling=0 if quality >= 84 else 2, exif=b"", icc_profile=None)
                content = buffer.getvalue()
                if len(content) <= IMAGE_TARGET_BYTES:
                    break
            extension, mime = "jpg", "image/jpeg"
        try:
            verified = Image.open(io.BytesIO(content))
            verified.verify()
        except Exception as error:
            raise ValueError(f"图片{index}预处理后无法解码。") from error
        if max(image.size) > 2048 or len(content) > IMAGE_MAX_BYTES:
            raise ValueError(f"图片{index}预处理后仍超过 2K/10MB，请裁剪或更换素材。")
        blobs.append((content, f"{prefix}_{index}.{extension}", mime))
    return blobs


def _ffmpeg_tool(name):
    configured = os.environ.get(f"DAPAO_{name.upper()}_PATH")
    if configured and Path(configured).is_file():
        return configured
    found = shutil.which(name)
    if found:
        return found
    if name == "ffmpeg":
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
    raise RuntimeError(f"未找到 {name}，无法自动优化素材。请安装 ffmpeg/ffprobe，或设置 DAPAO_{name.upper()}_PATH。")


def _run(command, timeout=300):
    result = subprocess.run(command, capture_output=True, timeout=timeout)
    if result.returncode:
        message = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace")
        raise RuntimeError(f"素材预处理失败：{message[-1000:]}")
    return result.stdout


def _probe(path):
    output = _run([_ffmpeg_tool("ffprobe"), "-v", "error", "-show_entries",
                   "format=duration,size,format_name:stream=codec_type,codec_name,width,height,avg_frame_rate",
                   "-of", "json", str(path)], 60)
    data = json.loads(output.decode("utf-8", errors="replace") or "{}")
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    try:
        duration = float(fmt.get("duration") or 0)
    except (TypeError, ValueError):
        duration = 0.0
    return {"duration": duration, "format": str(fmt.get("format_name") or ""), "streams": streams,
            "size": int(fmt.get("size") or Path(path).stat().st_size)}


def _video_path(video):
    if isinstance(video, (str, os.PathLike)) and Path(video).is_file():
        return str(Path(video)), False
    if isinstance(video, dict):
        for key in ("file_path", "path", "filename"):
            value = video.get(key)
            if isinstance(value, str) and Path(value).is_file():
                return value, False
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    handle.close()
    if not hasattr(video, "save_to") or video.save_to(handle.name) is False or not Path(handle.name).is_file():
        Path(handle.name).unlink(missing_ok=True)
        raise ValueError("无法读取 VIDEO 输入，请连接有效的 ComfyUI VIDEO。")
    return handle.name, True


def prepare_video(video, *, prefix="reference_video", target_bytes=10 * MIB, max_seconds=15.0):
    """Transcode to MP4/H.264/AAC, <=1080 edge, <=30 fps and bounded bytes."""
    source, remove_source = _video_path(video)
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output.close()
    try:
        info = _probe(source)
        duration = info["duration"]
        if duration < 0.95 or duration > max_seconds + 0.05:
            raise ValueError(f"参考视频时长需为 1–{int(max_seconds)} 秒，当前约 {duration:.2f} 秒。")
        audio_bps = 128_000
        total_bps = max(700_000, int(target_bytes * 8 * 0.92 / duration))
        video_kbps = max(500, (total_bps - audio_bps) // 1000)
        scale = "scale='if(gt(iw,ih),min(iw,1080),-2)':'if(gt(iw,ih),-2,min(ih,1080))':flags=lanczos,fps=30,format=yuv420p"
        _run([_ffmpeg_tool("ffmpeg"), "-y", "-i", source, "-map", "0:v:0", "-map", "0:a:0?",
              "-vf", scale, "-c:v", "libx264", "-preset", "medium", "-b:v", f"{video_kbps}k",
              "-maxrate", f"{video_kbps}k", "-bufsize", f"{video_kbps * 2}k", "-c:a", "aac",
              "-b:a", "128k", "-ar", "48000", "-movflags", "+faststart", "-map_metadata", "-1", output.name])
        final = _probe(output.name)
        video_stream = next((item for item in final["streams"] if item.get("codec_type") == "video"), {})
        if (final["size"] > min(target_bytes, VIDEO_MAX_BYTES) or video_stream.get("codec_name") != "h264"
                or max(int(video_stream.get("width") or 0), int(video_stream.get("height") or 0)) > 1080):
            raise ValueError("参考视频自动优化后仍超过体积、编码或 1080p 上限，请裁剪或更换素材。")
        return Path(output.name).read_bytes(), f"{prefix}.mp4", "video/mp4", duration
    finally:
        if remove_source:
            Path(source).unlink(missing_ok=True)
        Path(output.name).unlink(missing_ok=True)


def _audio_wav(audio):
    if not isinstance(audio, dict) or audio.get("waveform") is None:
        raise ValueError("无法读取 AUDIO 输入。")
    waveform = audio["waveform"]
    if hasattr(waveform, "detach"):
        waveform = waveform.detach()
    if hasattr(waveform, "cpu"):
        waveform = waveform.cpu().numpy()
    samples = np.squeeze(np.asarray(waveform))
    if samples.ndim == 1:
        samples = samples.reshape(-1, 1)
    elif samples.ndim == 2 and samples.shape[0] <= 8 and samples.shape[0] < samples.shape[1]:
        samples = samples.T
    if samples.ndim != 2:
        raise ValueError("无法识别 AUDIO 输入的声道格式。")
    samples = (np.clip(samples, -1, 1) * 32767).astype(np.int16) if np.issubdtype(samples.dtype, np.floating) else samples.astype(np.int16)
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    handle.close()
    with wave.open(handle.name, "wb") as target:
        target.setnchannels(samples.shape[1])
        target.setsampwidth(2)
        target.setframerate(int(audio.get("sample_rate") or audio.get("sampler_rate") or 44100))
        target.writeframes(samples.tobytes())
    return handle.name


def prepare_audio(audio, *, prefix="reference_audio", max_seconds=15.0):
    """Transcode reference audio to broadly supported MP3 with metadata removed."""
    source = _audio_wav(audio)
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
    output.close()
    try:
        duration = _probe(source)["duration"]
        if duration < 0.95 or duration > max_seconds + 0.05:
            raise ValueError(f"参考音频时长需为 1–{int(max_seconds)} 秒，当前约 {duration:.2f} 秒。")
        _run([_ffmpeg_tool("ffmpeg"), "-y", "-i", source, "-vn", "-c:a", "libmp3lame", "-b:a", "128k",
              "-ar", "44100", "-ac", "2", "-map_metadata", "-1", output.name])
        content = Path(output.name).read_bytes()
        if not content.startswith((b"ID3", b"\xff\xfb", b"\xff\xf3", b"\xff\xf2")) or len(content) > AUDIO_MAX_BYTES:
            raise ValueError("参考音频自动优化后格式或体积不符合要求，请裁剪或更换素材。")
        return content, f"{prefix}.mp3", "audio/mpeg", duration
    finally:
        Path(source).unlink(missing_ok=True)
        Path(output.name).unlink(missing_ok=True)


__all__ = ["MIB", "prepare_audio", "prepare_image_tensor", "prepare_video"]
