
import os
import json
import requests
import time
import base64
import io
import wave
import torch
import numpy as np
from PIL import Image
import folder_paths

try:
    import imageio
except ImportError:
    imageio = None

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CURRENT_DIR, 'config.json')

def get_config():
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

def tensor2pil(tensor: torch.Tensor) -> Image.Image:
    if len(tensor.shape) == 4:
        tensor = tensor[0]
    np_image = tensor.cpu().numpy()
    np_image = np.clip(np_image, 0, 1)
    np_image = (np_image * 255).astype(np.uint8)
    return Image.fromarray(np_image)

def image_to_base64(image_tensor: torch.Tensor, max_size=2048) -> str:
    try:
        pil_image = tensor2pil(image_tensor)
        if max(pil_image.size) > max_size:
            ratio = max_size / max(pil_image.size)
            new_size = (int(pil_image.size[0] * ratio), int(pil_image.size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        
        buffered = io.BytesIO()
        pil_image.save(buffered, format="JPEG", quality=90)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"[DoubaoSeedance2] 图像转base64失败: {e}")
        return None

def _safe_json_loads(text: str) -> dict:
    if not text or not text.strip():
        return {}
    try:
        value = json.loads(text)
        if isinstance(value, dict):
            return value
        return {}
    except Exception:
        return {}

def _guess_mime_type(file_path: str) -> str:
    ext = os.path.splitext(file_path or "")[1].lower().lstrip(".")
    if ext == "mp4":
        return "video/mp4"
    if ext == "mov":
        return "video/quicktime"
    if ext == "webm":
        return "video/webm"
    if ext == "mkv":
        return "video/x-matroska"
    if ext == "mp3":
        return "audio/mpeg"
    if ext == "wav":
        return "audio/wav"
    if ext == "m4a":
        return "audio/mp4"
    if ext == "flac":
        return "audio/flac"
    if ext == "ogg":
        return "audio/ogg"
    return "application/octet-stream"

def _file_to_data_url(file_path: str) -> str:
    if not file_path:
        return ""
    if not os.path.exists(file_path):
        return ""
    try:
        mime = _guess_mime_type(file_path)
        with open(file_path, "rb") as f:
            raw = f.read()
        b64 = base64.b64encode(raw).decode("utf-8")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return ""

def _normalize_url_or_data(value: str) -> str:
    if not value:
        return ""
    value = value.strip()
    if not value:
        return ""
    if value.startswith("http://") or value.startswith("https://"):
        return value
    return _file_to_data_url(value)

def _video_input_to_url_or_data(video_input) -> str:
    if not video_input:
        return ""
    if isinstance(video_input, str):
        return _normalize_url_or_data(video_input)

    temp_dir = ""
    try:
        temp_dir = folder_paths.get_temp_directory()
    except Exception:
        temp_dir = folder_paths.get_output_directory()

    temp_path = os.path.join(temp_dir, f"dapao_seedance_ref_video_{int(time.time() * 1000)}.mp4")
    try:
        if hasattr(video_input, "save_to"):
            video_input.save_to(temp_path)
            url_or_data = _normalize_url_or_data(temp_path)
            return url_or_data
        return ""
    finally:
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

def _audio_tensor_to_wav_bytes(waveform, sample_rate: int) -> bytes:
    if hasattr(waveform, "cpu"):
        waveform = waveform.cpu().numpy()

    waveform = np.asarray(waveform)
    waveform = np.squeeze(waveform)

    if waveform.ndim == 1:
        waveform = waveform.reshape(-1, 1)
    elif waveform.ndim == 2:
        if waveform.shape[0] < waveform.shape[1]:
            waveform = waveform.T
    else:
        waveform = waveform.reshape(-1, 1)

    if np.issubdtype(waveform.dtype, np.floating):
        waveform = np.clip(waveform, -1.0, 1.0)
        pcm = (waveform * 32767.0).astype(np.int16)
    else:
        pcm = waveform.astype(np.int16)

    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(int(pcm.shape[1]))
        wf.setsampwidth(2)
        wf.setframerate(int(sample_rate))
        wf.writeframes(pcm.tobytes())
    return buffer.getvalue()

def _audio_input_to_url_or_data(audio_input) -> str:
    if not audio_input:
        return ""
    if isinstance(audio_input, str):
        return _normalize_url_or_data(audio_input)
    if isinstance(audio_input, dict):
        waveform = audio_input.get("waveform")
        sample_rate = audio_input.get("sample_rate")
        if sample_rate is None:
            sample_rate = audio_input.get("sampler_rate")
        if sample_rate is None:
            sample_rate = 44100
        if waveform is None:
            return ""
        wav_bytes = _audio_tensor_to_wav_bytes(waveform, int(sample_rate))
        b64 = base64.b64encode(wav_bytes).decode("utf-8")
        return f"data:audio/wav;base64,{b64}"
    return ""

def _download_and_process_video(video_url: str, output_dir: str):
    res = requests.get(video_url, stream=True)
    if res.status_code != 200:
        raise Exception(f"下载失败: {res.status_code}")

    filename = f"seedance2_{int(time.time())}.mp4"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "wb") as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)

    frames_tensor = torch.zeros((1, 512, 512, 3))
    if imageio:
        try:
            reader = imageio.get_reader(filepath)
            frames = []
            for frame in reader:
                frames.append(frame)
                if len(frames) >= 8:
                    break
            if frames:
                frames_np = np.array(frames).astype(np.float32) / 255.0
                frames_tensor = torch.from_numpy(frames_np)
        except Exception as e:
            print(f"[DoubaoSeedance2] 读取视频帧失败: {e}")

    return (frames_tensor, filepath)

class DoubaoSeedance2Node:
    """
    豆包 Seedance 2.0 视频生成节点
    支持文生视频、图生视频、首尾帧视频
    """
    
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎛️ 生成模式": (["自动", "文生视频", "图生视频", "首尾帧"], {
                    "default": "自动"
                }),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "天空的云飘动着，路上的车辆行驶",
                    "placeholder": "请输入视频生成的提示词..."
                }),
                "🤖 模型名称": (["doubao-seedance-2-0-260128"], {
                    "default": "doubao-seedance-2-0-260128"
                }),
                "🖥️ 分辨率": (["720p", "1080p"], {
                    "default": "720p"
                }),
                "📐 视频比例": (["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"], {
                    "default": "16:9"
                }),
                "⏱️ 时长(秒)": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 20
                }),
                "🎥 镜头固定": ("BOOLEAN", {
                    "default": False,
                    "label_on": "true",
                    "label_off": "false"
                }),
                "➕ 额外参数": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "输入你的火山 Ark API Key（不会保存到本地）"
                }),
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "🌐 BaseURL": ("STRING", {
                    "default": "https://ark.cn-beijing.volces.com/api/v3",
                    "placeholder": "https://ark.cn-beijing.volces.com/api/v3"
                }),
                "⏳ 最大等待(秒)": ("INT", {
                    "default": 600,
                    "min": 10,
                    "max": 3600
                }),
                "🔁 查询间隔(秒)": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 60
                }),
            },
            "optional": {
                "🖼️ 参考图(用于图生)": ("IMAGE",),
                "🎬 首帧图": ("IMAGE",),
                "🏁 尾帧图": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "📂 视频URI", "🧾 响应信息")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/🐳即梦2.0视频生成"
    DESCRIPTION = "调用豆包 Seedance 2.0 模型生成视频，支持首尾帧控制 | 作者: @炮老师的小课堂"

    def generate(self, **kwargs):
        gen_mode = kwargs.get("🎛️ 生成模式", "自动")
        prompt = kwargs.get("📝 提示词", "")
        model = kwargs.get("🤖 模型名称", "doubao-seedance-2-0-260128")
        resolution = kwargs.get("🖥️ 分辨率", "720p")
        ratio = kwargs.get("📐 视频比例", "16:9")
        duration = int(kwargs.get("⏱️ 时长(秒)", 5))
        camera_fixed = bool(kwargs.get("🎥 镜头固定", False))
        extra_params_text = kwargs.get("➕ 额外参数", "")
        seed = int(kwargs.get("🎲 随机种子", 0))
        base_url = (kwargs.get("🌐 BaseURL", "") or "").strip() or "https://ark.cn-beijing.volces.com/api/v3"
        max_wait_seconds = int(kwargs.get("⏳ 最大等待(秒)", 600))
        poll_interval_seconds = int(kwargs.get("🔁 查询间隔(秒)", 2))

        first_frame = kwargs.get("🎬 首帧图")
        last_frame = kwargs.get("🏁 尾帧图")
        ref_image = kwargs.get("🖼️ 参考图(用于图生)")
        api_key = (kwargs.get("🔑 API密钥", "") or "").strip()

        if not api_key:
            config = get_config()
            api_key = (config.get("api_key", "") or "").strip()

        if not api_key:
            raise ValueError("未提供 API Key，请在节点里填写 🔑 API密钥")

        content = []
        
        if prompt:
            content.append({
                "type": "text",
                "text": prompt
            })

        auto_mode = "文生视频"
        if first_frame is not None and last_frame is not None:
            auto_mode = "首尾帧"
        elif first_frame is not None or ref_image is not None:
            auto_mode = "图生视频"

        final_mode = auto_mode if gen_mode == "自动" else gen_mode

        if final_mode == "首尾帧":
            if first_frame is None or last_frame is None:
                raise ValueError("生成模式为首尾帧时，必须同时提供 🎬 首帧图 与 🏁 尾帧图")
            b64_first = image_to_base64(first_frame)
            b64_last = image_to_base64(last_frame)
            if b64_first:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_first}"}
                })
            if b64_last:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64_last}"}
                })
        elif final_mode == "图生视频":
            img = first_frame if first_frame is not None else ref_image
            if img is None:
                raise ValueError("生成模式为图生视频时，必须提供 🖼️ 参考图(用于图生) 或 🎬 首帧图")
            b64 = image_to_base64(img)
            if b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
        elif final_mode != "文生视频":
            raise ValueError(f"未知生成模式: {final_mode}")

        tasks_url = f"{base_url.rstrip('/')}/content_generation/tasks"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        parameters = {
            "resolution": resolution,
            "aspect_ratio": ratio,
            "duration": duration,
            "camera_fixed": camera_fixed,
        }

        if seed > 0:
            parameters["seed"] = seed

        extra_params = _safe_json_loads(extra_params_text)
        if extra_params:
            parameters.update(extra_params)

        payload = {
            "model": model,
            "content": content,
            "parameters": parameters
        }

        try:
            response = requests.post(tasks_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code != 200:
                return (torch.zeros((1, 512, 512, 3)), "", response.text)
            
            res_json = response.json()
            if "id" not in res_json:
                return (torch.zeros((1, 512, 512, 3)), "", json.dumps(res_json, ensure_ascii=False))
            
            task_id = res_json["id"]

            video_url = None
            final_status = None
            start_time = time.time()
            
            while True:
                if time.time() - start_time > max_wait_seconds:
                    break

                time.sleep(poll_interval_seconds)
                check_url = f"{tasks_url}/{task_id}"
                check_res = requests.get(check_url, headers=headers, timeout=30)
                
                if check_res.status_code == 200:
                    task_status = check_res.json()
                    status = task_status.get("status")
                    final_status = task_status
                    
                    if status == "SUCCEEDED":
                        if "content" in task_status and "video_url" in task_status["content"]:
                            video_url = task_status["content"]["video_url"]
                        elif "result" in task_status and "video_url" in task_status["result"]:
                            video_url = task_status["result"]["video_url"]
                        
                        if not video_url:
                            import re
                            str_res = json.dumps(task_status)
                            urls = re.findall(r'https?://[^\s<>"]+\.mp4[^\s<>"]*', str_res)
                            if urls:
                                video_url = urls[0]
                        
                        break
                    elif status == "FAILED":
                        err_msg = task_status.get("error", {}).get("message", "未知错误")
                        response_info = json.dumps(task_status, ensure_ascii=False)
                        return (torch.zeros((1, 512, 512, 3)), "", response_info or f"任务失败: {err_msg}")

            if not video_url:
                response_info = json.dumps(final_status, ensure_ascii=False) if final_status else "任务超时或未获取到视频 URL"
                return (torch.zeros((1, 512, 512, 3)), "", response_info)

            frames_tensor, filepath = self.download_and_process_video(video_url)
            response_info = json.dumps(final_status, ensure_ascii=False) if final_status else ""
            return (frames_tensor, filepath, response_info)

        except Exception as e:
            return (torch.zeros((1, 512, 512, 3)), "", str(e))

    def download_and_process_video(self, video_url):
        return _download_and_process_video(video_url, self.output_dir)

class DoubaoSeedance2AdvancedNode:
    """
    豆包 Seedance 2.0 视频高级节点（组合参考）
    """

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "📝 提示词(支持@图像/@视频/@音频引用)": ("STRING", {
                    "multiline": True,
                    "default": "参考@视频1的人物动作和镜头运动，生成@图像1和@图像2的打斗场面，背景音乐参考@音频1的节奏，画面风格偏赛博朋克。",
                    "placeholder": "示例：参考@视频1的动作/镜头，融合@图像1/@图像2的角色或风格，必要时加入@音频1的节奏..."
                }),
                "🤖 模型名称": (["doubao-seedance-2-0-260128"], {
                    "default": "doubao-seedance-2-0-260128"
                }),
                "🖥️ 分辨率": (["720p", "1080p"], {
                    "default": "720p"
                }),
                "📐 视频比例": (["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"], {
                    "default": "16:9"
                }),
                "⏱️ 时长(秒)": ("INT", {
                    "default": 5,
                    "min": 1,
                    "max": 20
                }),
                "🎥 镜头固定": ("BOOLEAN", {
                    "default": False,
                    "label_on": "true",
                    "label_off": "false"
                }),
                "➕ 额外参数": ("STRING", {
                    "multiline": True,
                    "default": ""
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "输入你的火山 Ark API Key（不会保存到本地）"
                }),
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                "🌐 BaseURL": ("STRING", {
                    "default": "https://ark.cn-beijing.volces.com/api/v3",
                    "placeholder": "https://ark.cn-beijing.volces.com/api/v3"
                }),
                "⏳ 最大等待(秒)": ("INT", {
                    "default": 600,
                    "min": 10,
                    "max": 3600
                }),
                "🔁 查询间隔(秒)": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 60
                }),
            },
            "optional": {
                "🎞️ 参考视频1": ("VIDEO",),
                "🎞️ 参考视频2": ("VIDEO",),
                "🎞️ 参考视频3": ("VIDEO",),
                "🎞️ 参考视频4": ("VIDEO",),
                "🖼️ 图像参考1": ("IMAGE",),
                "🖼️ 图像参考2": ("IMAGE",),
                "🖼️ 图像参考3": ("IMAGE",),
                "🖼️ 图像参考4": ("IMAGE",),
                "🖼️ 图像参考5": ("IMAGE",),
                "🖼️ 图像参考6": ("IMAGE",),
                "🖼️ 图像参考7": ("IMAGE",),
                "🖼️ 图像参考8": ("IMAGE",),
                "🎵 参考音频1": ("AUDIO",),
                "🎵 参考音频2": ("AUDIO",),
                "🎵 参考音频3": ("AUDIO",),
                "🎵 参考音频4": ("AUDIO",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "📂 视频URI", "🧾 响应信息")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/🐳即梦2.0视频生成"
    DESCRIPTION = "Seedance 2.0 组合参考：多图+视频/音频引用提示词 | 作者: @炮老师的小课堂"

    def generate(self, **kwargs):
        prompt = kwargs.get("📝 提示词(支持@图像/@视频/@音频引用)", "")
        model = kwargs.get("🤖 模型名称", "doubao-seedance-2-0-260128")
        resolution = kwargs.get("🖥️ 分辨率", "720p")
        ratio = kwargs.get("📐 视频比例", "16:9")
        duration = int(kwargs.get("⏱️ 时长(秒)", 5))
        camera_fixed = bool(kwargs.get("🎥 镜头固定", False))
        extra_params_text = kwargs.get("➕ 额外参数", "")
        seed = int(kwargs.get("🎲 随机种子", 0))
        base_url = (kwargs.get("🌐 BaseURL", "") or "").strip() or "https://ark.cn-beijing.volces.com/api/v3"
        max_wait_seconds = int(kwargs.get("⏳ 最大等待(秒)", 600))
        poll_interval_seconds = int(kwargs.get("🔁 查询间隔(秒)", 2))

        api_key = (kwargs.get("🔑 API密钥", "") or "").strip()
        if not api_key:
            config = get_config()
            api_key = (config.get("api_key", "") or "").strip()
        if not api_key:
            raise ValueError("未提供 API Key，请在节点里填写 🔑 API密钥")

        video_inputs = [
            kwargs.get("🎞️ 参考视频1"),
            kwargs.get("🎞️ 参考视频2"),
            kwargs.get("🎞️ 参考视频3"),
            kwargs.get("🎞️ 参考视频4"),
        ]
        audio_inputs = [
            kwargs.get("🎵 参考音频1"),
            kwargs.get("🎵 参考音频2"),
            kwargs.get("🎵 参考音频3"),
            kwargs.get("🎵 参考音频4"),
        ]
        image_inputs = [
            kwargs.get("🖼️ 图像参考1"),
            kwargs.get("🖼️ 图像参考2"),
            kwargs.get("🖼️ 图像参考3"),
            kwargs.get("🖼️ 图像参考4"),
            kwargs.get("🖼️ 图像参考5"),
            kwargs.get("🖼️ 图像参考6"),
            kwargs.get("🖼️ 图像参考7"),
            kwargs.get("🖼️ 图像参考8"),
        ]

        content = []
        if prompt:
            content.append({"type": "text", "text": prompt})

        used_video_slots = []
        for idx, v in enumerate(video_inputs, start=1):
            url_or_data = _video_input_to_url_or_data(v)
            if url_or_data:
                used_video_slots.append(idx)
                content.append({"type": "video_url", "video_url": {"url": url_or_data}})

        used_image_slots = []
        for idx, img in enumerate(image_inputs, start=1):
            if img is None:
                continue
            b64 = image_to_base64(img)
            if b64:
                used_image_slots.append(idx)
                content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

        used_audio_slots = []
        for idx, a in enumerate(audio_inputs, start=1):
            url_or_data = _audio_input_to_url_or_data(a)
            if url_or_data:
                used_audio_slots.append(idx)
                content.append({"type": "audio_url", "audio_url": {"url": url_or_data}})

        tasks_url = f"{base_url.rstrip('/')}/content_generation/tasks"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}

        parameters = {
            "resolution": resolution,
            "aspect_ratio": ratio,
            "duration": duration,
            "camera_fixed": camera_fixed,
        }
        if seed > 0:
            parameters["seed"] = seed

        extra_params = _safe_json_loads(extra_params_text)
        if extra_params:
            parameters.update(extra_params)

        payload = {"model": model, "content": content, "parameters": parameters}

        response = requests.post(tasks_url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            return (torch.zeros((1, 512, 512, 3)), "", response.text)

        res_json = response.json()
        if "id" not in res_json:
            return (torch.zeros((1, 512, 512, 3)), "", json.dumps(res_json, ensure_ascii=False))

        task_id = res_json["id"]
        video_url = None
        final_status = None
        start_time = time.time()

        while True:
            if time.time() - start_time > max_wait_seconds:
                break

            time.sleep(poll_interval_seconds)
            check_url = f"{tasks_url}/{task_id}"
            check_res = requests.get(check_url, headers=headers, timeout=30)

            if check_res.status_code == 200:
                task_status = check_res.json()
                status = task_status.get("status")
                final_status = task_status

                if status == "SUCCEEDED":
                    if "content" in task_status and "video_url" in task_status["content"]:
                        video_url = task_status["content"]["video_url"]
                    elif "result" in task_status and "video_url" in task_status["result"]:
                        video_url = task_status["result"]["video_url"]

                    if not video_url:
                        import re
                        str_res = json.dumps(task_status)
                        urls = re.findall(r'https?://[^\s<>"]+\.mp4[^\s<>"]*', str_res)
                        if urls:
                            video_url = urls[0]

                    break

                if status == "FAILED":
                    response_info = json.dumps(task_status, ensure_ascii=False)
                    return (torch.zeros((1, 512, 512, 3)), "", response_info)

        if not video_url:
            response_info = json.dumps(final_status, ensure_ascii=False) if final_status else "任务超时或未获取到视频 URL"
            return (torch.zeros((1, 512, 512, 3)), "", response_info)

        frames_tensor, filepath = _download_and_process_video(video_url, self.output_dir)

        mapping_lines = []
        for i, slot in enumerate(used_video_slots, start=1):
            mapping_lines.append(f"@视频{i} = 🎞️ 参考视频{slot}")
        for i, slot in enumerate(used_image_slots, start=1):
            mapping_lines.append(f"@图像{i} = 🖼️ 图像参考{slot}")
        for i, slot in enumerate(used_audio_slots, start=1):
            mapping_lines.append(f"@音频{i} = 🎵 参考音频{slot}")

        response_info = json.dumps(final_status, ensure_ascii=False) if final_status else ""
        if mapping_lines:
            response_info = (response_info or "") + "\n\n" + "\n".join(mapping_lines)

        return (frames_tensor, filepath, response_info)
