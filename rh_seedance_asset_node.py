"""
RH Seedance2.0 asset nodes.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from fractions import Fraction
from io import BytesIO
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import time
import wave

import numpy as np
import requests
import torch
from PIL import Image


API_HOST = "https://www.runninghub.cn"
BASE_URL = f"{API_HOST}/openapi/v2"
UPLOAD_URL = f"{BASE_URL}/media/upload/binary"
ASSET_GROUP_ID = "group-20260327004931-dvjbj"
ASSET_NAME = "dapao_seedance_asset"
CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"

ASSET_READY_STATUSES = {"ACTIVE", "SUCCESS", "SUCCEEDED", "COMPLETED", "DONE", "READY", "AVAILABLE"}
ASSET_FAILED_STATUSES = {"FAILED", "ERROR", "CANCEL", "CANCELED"}

VIDEO_MIN_DURATION = 2.0
VIDEO_MAX_DURATION = 15.0
VIDEO_MIN_RATIO = 0.4
VIDEO_MAX_RATIO = 2.5
VIDEO_MIN_DIMENSION = 300
VIDEO_MAX_DIMENSION = 6000
VIDEO_MIN_PIXELS = 640 * 640
VIDEO_MAX_PIXELS = 834 * 1112
VIDEO_MIN_FPS = 24.0
VIDEO_MAX_FPS = 60.0
VIDEO_DEFAULT_FPS = 30.0
VIDEO_MAX_SIZE_BYTES = 50 * 1024 * 1024


def _log(message):
    print(f"[dapaoAPI-RH素材] {message}")


def _json(data):
    return json.dumps(data, ensure_ascii=False, indent=2)


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _connectable_string():
    return ("STRING", {"default": "", "forceInput": True})


def _api_key_input():
    return ("STRING", {
        "default": "",
        "placeholder": "填入 RunningHub API Key",
        "tooltip": "RunningHub API Key，仅用于本次请求，不会写入文件。",
    })


def _headers(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "ComfyUI-dapaoAPI/RHSeedanceAsset",
    }


def _response_error(response):
    text = response.text[:1000]
    try:
        data = response.json()
        if isinstance(data, dict):
            return data.get("msg") or data.get("message") or data.get("error") or text
    except Exception:
        pass
    return text


def _post_json(endpoint, api_key, payload, timeout=60, max_retries=2):
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            if attempt:
                time.sleep(min(2 ** attempt, 10))
            response = requests.post(url, headers=_headers(api_key), json=payload, timeout=timeout)
            if response.status_code >= 400:
                raise RuntimeError(f"HTTP {response.status_code}: {_response_error(response)}")
            data = response.json() if response.text else {}
            if not isinstance(data, dict):
                raise RuntimeError(f"接口返回内容不是 JSON：{response.text[:300]}")
            if data.get("code") not in (None, 0, "0"):
                raise RuntimeError(data.get("msg") or data.get("message") or str(data))
            return data
        except Exception as e:
            last_error = e
            if attempt >= max_retries:
                break
    raise RuntimeError(f"请求失败：{last_error}")


def _upload_file(api_key, content, filename, mime_type, timeout=120):
    response = requests.post(
        UPLOAD_URL,
        headers={"Authorization": f"Bearer {api_key}"},
        files={"file": (filename, content, mime_type)},
        timeout=max(timeout, 120),
    )
    if response.status_code >= 400:
        raise RuntimeError(f"媒体上传失败 {response.status_code}：{_response_error(response)}")
    data = response.json() if response.text else {}
    if data.get("code") not in (None, 0, "0"):
        raise RuntimeError(data.get("msg") or data.get("message") or str(data))
    url = (data.get("data") or {}).get("download_url")
    if not url:
        raise RuntimeError(f"媒体上传成功但没有返回 download_url：{_json(data)[:500]}")
    return url


def _tensor_to_pil_list(image_tensor):
    if image_tensor is None:
        return []
    value = image_tensor.detach().cpu() if hasattr(image_tensor, "detach") else image_tensor
    arr = value.numpy() if hasattr(value, "numpy") else np.asarray(value)
    if arr.ndim == 3:
        arr = arr[np.newaxis, ...]
    images = []
    for item in arr:
        item = np.nan_to_num(item)
        if item.max() <= 1.0:
            item = item * 255.0
        item = np.clip(item, 0, 255).astype(np.uint8)
        if item.ndim == 2:
            images.append(Image.fromarray(item, mode="L"))
        elif item.shape[-1] == 4:
            images.append(Image.fromarray(item, mode="RGBA"))
        else:
            images.append(Image.fromarray(item[..., :3], mode="RGB"))
    return images


def _prepare_image(image_tensor):
    images = _tensor_to_pil_list(image_tensor)
    if not images:
        raise ValueError("请接入有效的图片素材。")

    image = images[0]
    if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
        rgba = image.convert("RGBA")
        bg = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        image = Image.alpha_composite(bg, rgba).convert("RGB")
    elif image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    if width <= 0 or height <= 0:
        raise ValueError("图片尺寸无效。")

    ratio = width / height
    if ratio > 2.5:
        new_width = int(round(height * 2.5))
        left = max(0, (width - new_width) // 2)
        image = image.crop((left, 0, left + new_width, height))
    elif ratio < 0.4:
        new_height = int(round(width / 0.4))
        top = max(0, (height - new_height) // 2)
        image = image.crop((0, top, width, top + new_height))

    width, height = image.size
    min_dim, max_dim = min(width, height), max(width, height)
    scale = 1.0
    if min_dim < 300:
        scale = 300 / float(min_dim)
    elif max_dim > 6000:
        scale = 6000 / float(max_dim)
    if abs(scale - 1.0) > 1e-6:
        image = image.resize((max(300, int(width * scale)), max(300, int(height * scale))), Image.Resampling.LANCZOS)

    best = None
    working = image
    for _ in range(6):
        for quality in (95, 90, 85, 80, 75, 70, 65, 60):
            buf = BytesIO()
            working.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
            content = buf.getvalue()
            best = content if best is None or len(content) < len(best) else best
            if len(content) <= 10 * 1024 * 1024:
                return content, f"asset_{abs(hash(content)) % 10**10}.jpg", "image/jpeg"
        width, height = working.size
        if width <= 300 and height <= 300:
            break
        working = working.resize((max(300, int(width * 0.9)), max(300, int(height * 0.9))), Image.Resampling.LANCZOS)

    if not best:
        raise RuntimeError("图片编码失败。")
    if len(best) > 10 * 1024 * 1024:
        raise RuntimeError("图片处理后仍超过 10MB，请换用更小的素材。")
    return best, f"asset_{abs(hash(best)) % 10**10}.jpg", "image/jpeg"


def _normalize_audio(audio):
    if not isinstance(audio, dict) or "waveform" not in audio:
        raise ValueError("请接入有效的音频素材。")
    waveform = audio["waveform"]
    sample_rate = int(audio.get("sample_rate") or audio.get("sampler_rate") or 44100)
    if not isinstance(waveform, torch.Tensor):
        waveform = torch.as_tensor(waveform)
    waveform = waveform.detach().cpu().float()
    if waveform.dim() == 3:
        waveform = waveform.squeeze(0)
    if waveform.dim() == 1:
        waveform = waveform.unsqueeze(0)
    if waveform.dim() != 2:
        raise ValueError(f"音频 waveform 形状不支持：{tuple(waveform.shape)}")
    waveform = torch.nan_to_num(waveform, nan=0.0, posinf=1.0, neginf=-1.0).clamp(-1.0, 1.0)
    if waveform.shape[0] > 2:
        waveform = waveform.mean(dim=0, keepdim=True)
    max_rate = 48000
    if sample_rate > max_rate:
        target_samples = max(1, int(round(waveform.shape[-1] * max_rate / sample_rate)))
        waveform = torch.nn.functional.interpolate(
            waveform.unsqueeze(0),
            size=target_samples,
            mode="linear",
            align_corners=False,
        ).squeeze(0)
        sample_rate = max_rate
    min_samples = int(round(2.0 * sample_rate))
    max_samples = int(round(15.0 * sample_rate))
    if waveform.shape[-1] < min_samples:
        waveform = torch.nn.functional.pad(waveform, (0, min_samples - waveform.shape[-1]))
    elif waveform.shape[-1] > max_samples:
        waveform = waveform[:, :max_samples]
    return waveform.contiguous(), sample_rate


def _prepare_audio(audio):
    waveform, sample_rate = _normalize_audio(audio)
    pcm = (waveform.numpy().T * 32767.0).clip(-32768, 32767).astype(np.int16)
    buf = BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(int(pcm.shape[1]) if pcm.ndim == 2 else 1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())
    content = buf.getvalue()
    if len(content) > 15 * 1024 * 1024:
        raise RuntimeError("音频处理后仍超过 15MB，请缩短音频或降低采样率。")
    return content, f"asset_{abs(hash(content)) % 10**10}.wav", "audio/wav"


def _video_path(value):
    if value is None:
        return ""
    if hasattr(value, "get_stream_source"):
        source = value.get_stream_source()
        if isinstance(source, str) and os.path.isfile(source):
            return source
    for attr in ("path", "file_path", "filename"):
        path = getattr(value, attr, None)
        if isinstance(path, str) and os.path.isfile(path):
            return path
    if isinstance(value, dict):
        for key in ("file_path", "path", "filename", "file", "video_path"):
            path = value.get(key)
            if isinstance(path, str) and os.path.isfile(path):
                return path
    if isinstance(value, (list, tuple)) and value:
        return _video_path(value[0])
    if isinstance(value, str) and os.path.isfile(value):
        return value
    return ""


def _video_bytes(value):
    path = _video_path(value)
    if path:
        with open(path, "rb") as f:
            return f.read()
    if hasattr(value, "get_stream_source"):
        source = value.get_stream_source()
        if hasattr(source, "read"):
            return source.read()
    raise ValueError("请接入有效的视频素材。")


def _tool(name):
    env_name = f"RH_{name.upper()}_PATH"
    configured = os.environ.get(env_name)
    if configured and os.path.exists(configured):
        return configured
    return shutil.which(name)


def _run_command(command, timeout):
    result = subprocess.run(command, capture_output=True, timeout=timeout)
    stdout = (result.stdout or b"").decode("utf-8", errors="replace")
    stderr = (result.stderr or b"").decode("utf-8", errors="replace")
    return result.returncode, stdout, stderr


def _parse_rate(value):
    text = str(value or "").strip()
    if not text or text in {"0/0", "N/A"}:
        return 0.0
    try:
        if "/" in text:
            return float(Fraction(text))
        return float(text)
    except Exception:
        return 0.0


def _probe_video(path):
    ffprobe = _tool("ffprobe")
    if not ffprobe:
        raise RuntimeError("未找到 ffprobe，无法检查并规范化视频素材。请安装 ffmpeg/ffprobe，或设置 RH_FFPROBE_PATH。")

    command = [
        ffprobe,
        "-v", "error",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        path,
    ]
    code, stdout, stderr = _run_command(command, 60)
    if code != 0:
        raise RuntimeError(f"ffprobe 读取视频失败：{stderr[:500] or path}")

    try:
        data = json.loads(stdout or "{}")
    except Exception as e:
        raise RuntimeError(f"ffprobe 返回内容不是 JSON：{e}") from e

    streams = data.get("streams") or []
    fmt = data.get("format") or {}
    video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
    if not video_stream:
        raise RuntimeError("视频素材中没有可用视频轨。")

    width = int(video_stream.get("width") or 0)
    height = int(video_stream.get("height") or 0)
    rotation = 0
    tags = video_stream.get("tags") or {}
    if tags.get("rotate") not in (None, ""):
        try:
            rotation = int(float(tags.get("rotate")))
        except Exception:
            rotation = 0
    for side_data in video_stream.get("side_data_list") or []:
        if side_data.get("rotation") not in (None, ""):
            try:
                rotation = int(float(side_data.get("rotation")))
                break
            except Exception:
                pass
    if abs(rotation) % 180 == 90:
        width, height = height, width

    duration = 0.0
    for item in (fmt.get("duration"), video_stream.get("duration"), tags.get("DURATION")):
        try:
            if item not in (None, ""):
                duration = float(item)
                break
        except Exception:
            pass

    size_bytes = 0
    try:
        size_bytes = int(fmt.get("size") or 0)
    except Exception:
        size_bytes = 0
    if size_bytes <= 0 and os.path.isfile(path):
        size_bytes = os.path.getsize(path)

    fps = _parse_rate(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate"))
    return {
        "format_name": str(fmt.get("format_name") or ""),
        "width": width,
        "height": height,
        "duration": duration,
        "fps": fps,
        "size_bytes": size_bytes,
        "has_audio": any(item.get("codec_type") == "audio" for item in streams),
    }


def _even(value):
    value = max(2, int(round(value)))
    return value if value % 2 == 0 else value - 1


def _target_video_geometry(width, height):
    if width <= 0 or height <= 0:
        raise RuntimeError("视频尺寸无效。")

    crop_width = int(width)
    crop_height = int(height)
    ratio = crop_width / float(crop_height)
    if ratio > VIDEO_MAX_RATIO:
        crop_width = _even(crop_height * VIDEO_MAX_RATIO)
    elif ratio < VIDEO_MIN_RATIO:
        crop_height = _even(crop_width / VIDEO_MIN_RATIO)

    crop_x = max(0, _even((width - crop_width) / 2))
    crop_y = max(0, _even((height - crop_height) / 2))
    crop_width = min(crop_width, width - crop_x)
    crop_height = min(crop_height, height - crop_y)
    if crop_width % 2:
        crop_width -= 1
    if crop_height % 2:
        crop_height -= 1

    crop_ratio = crop_width / float(crop_height)
    target_area = min(max(crop_width * crop_height, VIDEO_MIN_PIXELS), VIDEO_MAX_PIXELS)
    target_width = _even(math.sqrt(target_area * crop_ratio))
    target_height = _even(target_width / crop_ratio)

    if min(target_width, target_height) < VIDEO_MIN_DIMENSION:
        scale = VIDEO_MIN_DIMENSION / float(min(target_width, target_height))
        target_width = _even(target_width * scale)
        target_height = _even(target_height * scale)

    if max(target_width, target_height) > VIDEO_MAX_DIMENSION:
        scale = VIDEO_MAX_DIMENSION / float(max(target_width, target_height))
        target_width = _even(target_width * scale)
        target_height = _even(target_height * scale)

    while target_width * target_height > VIDEO_MAX_PIXELS:
        target_width = _even(target_width * 0.98)
        target_height = _even(target_height * 0.98)

    return {
        "crop_width": int(crop_width),
        "crop_height": int(crop_height),
        "crop_x": int(crop_x),
        "crop_y": int(crop_y),
        "target_width": int(target_width),
        "target_height": int(target_height),
    }


def _validate_video_info(info):
    errors = []
    width = int(info.get("width") or 0)
    height = int(info.get("height") or 0)
    duration = float(info.get("duration") or 0.0)
    fps = float(info.get("fps") or 0.0)
    size_bytes = int(info.get("size_bytes") or 0)
    area = width * height
    ratio = width / float(height) if width > 0 and height > 0 else 0.0

    if duration < VIDEO_MIN_DURATION - 0.05 or duration > VIDEO_MAX_DURATION + 0.05:
        errors.append(f"duration={duration:.2f}s")
    if fps < VIDEO_MIN_FPS - 0.1 or fps > VIDEO_MAX_FPS + 0.1:
        errors.append(f"fps={fps:.2f}")
    if width < VIDEO_MIN_DIMENSION or height < VIDEO_MIN_DIMENSION:
        errors.append(f"resolution={width}x{height}")
    if ratio < VIDEO_MIN_RATIO - 0.01 or ratio > VIDEO_MAX_RATIO + 0.01:
        errors.append(f"ratio={ratio:.4f}")
    if area < VIDEO_MIN_PIXELS or area > VIDEO_MAX_PIXELS:
        errors.append(f"pixels={area}")
    if size_bytes > VIDEO_MAX_SIZE_BYTES:
        errors.append(f"size={size_bytes / (1024 * 1024):.2f}MB")
    if errors:
        raise RuntimeError("视频预处理后仍不符合素材要求：" + ", ".join(errors))


def _transcode_video(path, keep_audio=False):
    ffmpeg = _tool("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("未找到 ffmpeg，无法规范化视频素材。请安装 ffmpeg，或设置 RH_FFMPEG_PATH。")

    info = _probe_video(path)
    if info["duration"] <= 0:
        raise RuntimeError("无法读取视频时长。")

    duration = max(VIDEO_MIN_DURATION, min(VIDEO_MAX_DURATION, info["duration"]))
    fps = max(VIDEO_MIN_FPS, min(VIDEO_MAX_FPS, info["fps"] or VIDEO_DEFAULT_FPS))
    geometry = _target_video_geometry(info["width"], info["height"])

    _log(
        "视频预处理："
        f"原始 {info['width']}x{info['height']} / {info['duration']:.2f}s / {info['fps']:.2f}fps，"
        f"输出 {geometry['target_width']}x{geometry['target_height']} / {duration:.2f}s / {fps:.2f}fps"
    )

    output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    output.close()

    filters = []
    if (
        geometry["crop_width"] != info["width"]
        or geometry["crop_height"] != info["height"]
        or geometry["crop_x"] != 0
        or geometry["crop_y"] != 0
    ):
        filters.append(
            f"crop={geometry['crop_width']}:{geometry['crop_height']}:"
            f"{geometry['crop_x']}:{geometry['crop_y']}"
        )
    filters.append(f"scale={geometry['target_width']}:{geometry['target_height']}:flags=lanczos")
    filters.append(f"fps={fps:.3f}")
    if info["duration"] < VIDEO_MIN_DURATION:
        filters.append(f"tpad=stop_mode=clone:stop_duration={VIDEO_MIN_DURATION - info['duration']:.3f}")
    filters.append("format=yuv420p")

    command = [
        ffmpeg, "-y", "-i", path,
        "-map", "0:v:0",
        "-vf", ",".join(filters),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-movflags", "+faststart",
    ]
    if keep_audio and info["has_audio"]:
        command += ["-map", "0:a:0?", "-c:a", "aac", "-b:a", "128k", "-ar", "48000"]
    else:
        command += ["-an"]
    command.append(output.name)
    try:
        code, _stdout, stderr = _run_command(command, 300)
        if code != 0 or not os.path.exists(output.name) or os.path.getsize(output.name) <= 0:
            raise RuntimeError(f"ffmpeg 转码失败：{stderr[:800]}")

        output_path = output.name
        out_info = _probe_video(output_path)
        if out_info["size_bytes"] > VIDEO_MAX_SIZE_BYTES:
            constrained = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            constrained.close()
            try:
                bitrate_kbps = max(500, int((VIDEO_MAX_SIZE_BYTES * 8 * 0.92) / 1024 / max(duration, 1)) - 192)
                command2 = list(command)
                command2[command2.index("-crf")] = "-b:v"
                command2[command2.index("23")] = f"{bitrate_kbps}k"
                command2.insert(-1, "-maxrate")
                command2.insert(-1, f"{bitrate_kbps}k")
                command2.insert(-1, "-bufsize")
                command2.insert(-1, f"{bitrate_kbps * 2}k")
                command2[-1] = constrained.name
                code, _stdout, stderr = _run_command(command2, 300)
                if code != 0 or os.path.getsize(constrained.name) <= 0:
                    raise RuntimeError(f"ffmpeg 二次压缩失败：{stderr[:800]}")
                os.remove(output_path)
                output_path = constrained.name
                out_info = _probe_video(output_path)
            except Exception:
                try:
                    os.remove(constrained.name)
                except OSError:
                    pass
                raise

        _validate_video_info(out_info)
        return output_path, True
    except Exception:
        try:
            if os.path.exists(output.name):
                os.remove(output.name)
        except OSError:
            pass
        raise


def _prepare_video(video, keep_audio=False):
    path = _video_path(video)
    temp_input = ""
    temp_output = ""
    try:
        if not path:
            content = _video_bytes(video)
            temp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            temp.write(content)
            temp.close()
            temp_input = temp.name
            path = temp.name
        final_path, is_temp = _transcode_video(path, keep_audio=keep_audio)
        temp_output = final_path if is_temp else ""
        with open(final_path, "rb") as f:
            content = f.read()
        if len(content) > VIDEO_MAX_SIZE_BYTES:
            raise RuntimeError("视频素材超过 50MB，请压缩后再提交。")
        return content, f"asset_{abs(hash(content)) % 10**10}.mp4", "video/mp4"
    finally:
        for item in (temp_input, temp_output):
            try:
                if item and os.path.exists(item):
                    os.remove(item)
            except OSError:
                pass


def _media_inputs(image=None, video=None, audio=None):
    result = []
    if image is not None:
        result.append(("image", image))
    if video is not None:
        result.append(("video", video))
    if audio is not None:
        result.append(("audio", audio))
    return result


def _asset_type(media_type):
    return {"image": "Image", "video": "Video", "audio": "Audio"}[media_type]


def _prepare_media(media_type, value, keep_video_audio=False):
    if media_type == "image":
        return _prepare_image(value)
    if media_type == "video":
        return _prepare_video(value, keep_audio=keep_video_audio)
    if media_type == "audio":
        return _prepare_audio(value)
    raise ValueError(f"不支持的素材类型：{media_type}")


def _create_one_asset(api_key, media_type, value, timeout, keep_video_audio=False):
    content, filename, mime_type = _prepare_media(media_type, value, keep_video_audio=keep_video_audio)
    source_url = _upload_file(api_key, content, filename, mime_type, timeout)
    payload = {
        "groupId": ASSET_GROUP_ID,
        "url": source_url,
        "assetType": _asset_type(media_type),
        "name": ASSET_NAME,
    }
    response = _post_json("assets/create", api_key, payload, timeout)
    data = response.get("data") or {}
    asset_id = _clean(data.get("assetId"))
    if not asset_id:
        raise RuntimeError(f"创建成功但没有返回 assetId：{_json(response)[:500]}")
    ready_info = _wait_for_asset(api_key, asset_id, media_type, timeout)
    return {
        "media_type": media_type,
        "asset_id": asset_id,
        "status": _clean(ready_info.get("status")) or _clean(data.get("status")),
        "response": ready_info.get("response") or response,
    }


def _query_asset(api_key, asset_id, timeout):
    response = _post_json("assets/query", api_key, {"assetId": asset_id}, timeout, max_retries=1)
    data = response.get("data") or {}
    return {
        "asset_id": _clean(data.get("assetId")) or asset_id,
        "status": _clean(data.get("status")),
        "preview_url": _clean(data.get("previewUrl")),
        "response": response,
    }


def _wait_for_asset(api_key, asset_id, media_type, timeout):
    deadline = time.time() + {"image": 180, "video": 300, "audio": 180}.get(media_type, 180)
    last_status = ""
    while True:
        info = _query_asset(api_key, asset_id, timeout)
        status = _clean(info.get("status")).upper()
        if status != last_status:
            _log(f"素材 {asset_id} 状态：{status or 'UNKNOWN'}")
            last_status = status
        if status in ASSET_READY_STATUSES:
            return info
        if status in ASSET_FAILED_STATUSES:
            response_text = _json(info.get("response") or {})[:1500]
            raise RuntimeError(f"素材处理失败：{status}\nRH 查询返回：{response_text}")
        if time.time() >= deadline:
            response_text = _json(info.get("response") or {})[:1500]
            raise RuntimeError(f"等待素材可用超时，最后状态：{status or 'unknown'}\nRH 查询返回：{response_text}")
        time.sleep(2)


def _split_asset_ids(*values):
    result = []
    for value in values:
        text = _clean(value)
        if not text:
            continue
        for item in re.split(r"[\n,，]+", text):
            asset_id = _clean(item)
            if asset_id.startswith("asset://"):
                asset_id = asset_id[8:]
            if asset_id:
                result.append(asset_id)
    return result


class DapaoRHSeedanceAssetCreateNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": _api_key_input(),
            },
            "optional": {
                "image": ("IMAGE",),
                "video": ("VIDEO",),
                "audio": ("AUDIO",),
                "🎞️ 保留视频音频": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "默认关闭：上传视频素材前去掉音频，降低音乐/音轨触发版权审核的概率。",
                }),
                "skip_error": ("BOOLEAN", {"default": False}),
                "⌛ 请求超时": ("INT", {"default": 120, "min": 10, "max": 600, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("asset_id", "status", "response")
    FUNCTION = "create"
    CATEGORY = CATEGORY
    DESCRIPTION = "RunningHub Seedance2.0 素材创建"
    OUTPUT_NODE = False

    def _error_result(self, message):
        return ("", "", _json({"error": message}))

    def create(self, **kwargs):
        api_key = _clean(kwargs.get("🔑 API密钥"))
        skip_error = bool(kwargs.get("skip_error", False))
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        keep_video_audio = bool(kwargs.get("🎞️ 保留视频音频", False))
        try:
            if not api_key:
                raise ValueError("请填写 RunningHub API密钥。")
            media = _media_inputs(kwargs.get("image"), kwargs.get("video"), kwargs.get("audio"))
            if not media:
                raise ValueError("请接入 image、video 或 audio 中至少一种素材。")

            if len(media) == 1:
                item = _create_one_asset(
                    api_key,
                    media[0][0],
                    media[0][1],
                    timeout,
                    keep_video_audio=keep_video_audio,
                )
                return (item["asset_id"], item["status"], _json(item["response"]))

            created = [None] * len(media)
            with ThreadPoolExecutor(max_workers=min(3, len(media))) as executor:
                futures = {
                    executor.submit(
                        _create_one_asset,
                        api_key,
                        media_type,
                        value,
                        timeout,
                        keep_video_audio,
                    ): index
                    for index, (media_type, value) in enumerate(media)
                }
                for future in as_completed(futures):
                    created[futures[future]] = future.result()

            asset_ids = [item["asset_id"] for item in created if item and item.get("asset_id")]
            statuses = []
            for item in created:
                status = item.get("status") if item else ""
                if status and status not in statuses:
                    statuses.append(status)
            response = {
                "data": {
                    "assetId": ", ".join(asset_ids),
                    "assetIds": asset_ids,
                    "status": ", ".join(statuses),
                    "items": created,
                    "count": len(created),
                }
            }
            return (", ".join(asset_ids), ", ".join(statuses), _json(response))
        except Exception as e:
            if skip_error:
                return self._error_result(str(e))
            raise


class DapaoRHSeedanceAssetQueryNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": _api_key_input(),
                "asset_id": _connectable_string(),
            },
            "optional": {
                "skip_error": ("BOOLEAN", {"default": False}),
                "⌛ 请求超时": ("INT", {"default": 60, "min": 10, "max": 300, "step": 1}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("asset_id", "status", "preview_url", "response")
    FUNCTION = "query"
    CATEGORY = CATEGORY
    DESCRIPTION = "RunningHub Seedance2.0 素材查询"
    OUTPUT_NODE = False

    def _error_result(self, message):
        return ("", "", "", _json({"error": message}))

    def query(self, **kwargs):
        api_key = _clean(kwargs.get("🔑 API密钥"))
        asset_id = _clean(kwargs.get("asset_id"))
        skip_error = bool(kwargs.get("skip_error", False))
        timeout = int(kwargs.get("⌛ 请求超时", 60))
        try:
            if not api_key:
                raise ValueError("请填写 RunningHub API密钥。")
            if asset_id.startswith("asset://"):
                asset_id = asset_id[8:]
            if not asset_id:
                raise ValueError("asset_id 不能为空。")
            info = _query_asset(api_key, asset_id, timeout)
            return (info["asset_id"], info["status"], info["preview_url"], _json(info["response"]))
        except Exception as e:
            if skip_error:
                return self._error_result(str(e))
            raise


class DapaoRHSeedanceAssetIdsMergeNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "asset_id1": _connectable_string(),
            },
            "optional": {
                "asset_id2": _connectable_string(),
                "asset_id3": _connectable_string(),
                "asset_id4": _connectable_string(),
                "asset_id5": _connectable_string(),
                "asset_id6": _connectable_string(),
                "asset_id7": _connectable_string(),
                "asset_id8": _connectable_string(),
                "asset_id9": _connectable_string(),
                "asset_id10": _connectable_string(),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("asset_ids",)
    FUNCTION = "merge"
    CATEGORY = CATEGORY
    DESCRIPTION = "RunningHub Seedance2.0 素材ID合并"
    OUTPUT_NODE = False

    def merge(
        self,
        asset_id1,
        asset_id2="",
        asset_id3="",
        asset_id4="",
        asset_id5="",
        asset_id6="",
        asset_id7="",
        asset_id8="",
        asset_id9="",
        asset_id10="",
    ):
        asset_ids = _split_asset_ids(
            asset_id1,
            asset_id2,
            asset_id3,
            asset_id4,
            asset_id5,
            asset_id6,
            asset_id7,
            asset_id8,
            asset_id9,
            asset_id10,
        )
        if not asset_ids:
            raise ValueError("请至少填写一个 asset_id。")
        return (", ".join(asset_ids),)


NODE_CLASS_MAPPINGS = {
    "DapaoRHSeedanceAssetCreateNode": DapaoRHSeedanceAssetCreateNode,
    "DapaoRHSeedanceAssetQueryNode": DapaoRHSeedanceAssetQueryNode,
    "DapaoRHSeedanceAssetIdsMergeNode": DapaoRHSeedanceAssetIdsMergeNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoRHSeedanceAssetCreateNode": "RH Seedance2.0素材/创建",
    "DapaoRHSeedanceAssetQueryNode": "RH Seedance2.0素材/查询",
    "DapaoRHSeedanceAssetIdsMergeNode": "RH Seedance2.0素材ID/合并",
}
