"""Seedance 2.0 all-round director prompt compiler.

This node is intentionally independent from the H3 prompt node.  It uses the
same dapaoAI LLM surface and media widgets, but compiles Seedance prompts,
reference roles, clip contracts and explicit project state for one clip.
"""

import asyncio
import base64
import io
import json
import os
import sys
import tempfile
import time
import traceback
import wave

import numpy as np
import requests
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error
from .image_input_utils import IMAGE_429_HINT, tensor_to_png_data_uris
from .llm_model_options import LLM_MODEL_OPTIONS
from .dreambrush_runtime import submit_json_task


API_BASE_URL = "https://api.dapaoai.com"
CHAT_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
NODE_NAME = "DapaoSeedance20DirectorNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮API常用工具🍬"
DISPLAY_NAME = "😶‍🌫️Seedance2全能导演@炮老师的小课堂"

MODEL_OPTIONS = list(LLM_MODEL_OPTIONS)
MODE_OPTIONS = [
    "自动识别", "独立提示词", "T2V-文生视频", "I2V-图生视频", "V2V-视频参考",
    "R2V-全能参考", "FLF2V-首尾帧", "Edit-视频编辑", "Extend-视频续写",
    "Sequence-连续剧情", "Review-成片复盘", "Repair-失败修复",
]
STYLE_OPTIONS = [
    "通用导演", "极简产品广告", "品牌宣传短片", "真人电影叙事", "动作大片",
    "悬疑惊悚·真相反转", "误会喜剧·结尾反转", "一本正经·荒诞反差",
    "整蛊打脸·连环反转", "萌宠治愈日常", "萌宠拟人喜剧", "邵氏复古武侠",
    "魅惑美女氛围大片", "狗血穿越·逆袭短剧", "豪门霸总·身份反转",
    "国风仙侠奇幻", "赛博朋克科幻短片", "音乐MV", "美食料理·ASMR",
    "时尚美妆大片", "建筑空间漫游", "动漫热血动作", "3D动画短片",
    "黏土定格·微缩模型", "纸艺定格科普", "手绘实拍融合", "人物纪实·微纪录",
    "科技UI功能演示", "工业机械演示", "文旅城市宣传片",
]
ASPECT_RATIO_OPTIONS = ["21:9", "16:9", "4:3", "1:1", "3:4", "9:16"]
RESOLUTION_OPTIONS = ["自动", "480P", "720P", "1080P"]
MAX_IMAGES = 9
MAX_VIDEOS = 3
MAX_AUDIOS = 3
MAX_FILES = 12
# Seedance duration limits vary by the active API surface. Keep local checks
# permissive and let the selected provider enforce its own entitlement.
MIN_MEDIA_DURATION = 0.01
MAX_MEDIA_DURATION = 3600.0


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(str(message).encode(encoding, errors="replace").decode(encoding, errors="replace"))


def _log_info(message):
    _safe_print(f"[dapaoAPI-Seedance2导演] 信息：{message}")


def _log_error(message):
    _safe_print(f"[dapaoAPI-Seedance2导演] 错误：{message}")


def _tensor_to_data_uris(image_tensor, max_side=2048):
    return tensor_to_png_data_uris(image_tensor, max_edge=max_side)


def _pil_data_uri(image, max_side=1024, quality=84):
    image = image.convert("RGB")
    if max(image.size) > max_side:
        scale = max_side / max(image.size)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _temporary_video_path(video_input, index):
    if isinstance(video_input, str):
        if video_input.startswith(("http://", "https://")):
            response = requests.get(video_input, timeout=180)
            response.raise_for_status()
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            handle.write(response.content)
            handle.close()
            return handle.name, True
        if os.path.isfile(video_input):
            return video_input, False
    if isinstance(video_input, dict):
        for key in ("file_path", "path", "filename"):
            path = video_input.get(key)
            if isinstance(path, str) and os.path.isfile(path):
                return path, False
    if not hasattr(video_input, "save_to"):
        raise ValueError(f"无法读取参考视频{index}，请连接ComfyUI原生VIDEO输出。")
    handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    handle.close()
    saved = video_input.save_to(handle.name)
    if saved is False or not os.path.isfile(handle.name) or os.path.getsize(handle.name) <= 0:
        try:
            os.remove(handle.name)
        except OSError:
            pass
        raise ValueError(f"参考视频{index}保存失败。")
    return handle.name, True


def _sample_video(video_input, index, sample_count):
    path, temporary = _temporary_video_path(video_input, index)
    try:
        try:
            import cv2
            capture = cv2.VideoCapture(path)
            if not capture.isOpened():
                raise RuntimeError("OpenCV无法打开视频")
            fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            if fps <= 0 or frame_count <= 0:
                raise ValueError(f"参考视频{index}缺少有效帧率或帧数信息。")
            duration = frame_count / fps
            if duration < MIN_MEDIA_DURATION:
                raise ValueError(f"参考视频{index}时长无效：{duration:.2f}秒。")
            last_time = max(0.0, duration - max(1.0 / fps, 0.04))
            frames = []
            for timestamp in np.linspace(0.0, last_time, max(2, int(sample_count))):
                capture.set(cv2.CAP_PROP_POS_MSEC, float(timestamp) * 1000.0)
                ok, frame = capture.read()
                if not ok or frame is None:
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append({"time": float(timestamp), "uri": _pil_data_uri(Image.fromarray(rgb))})
            capture.release()
            if len(frames) < 2:
                raise ValueError(f"参考视频{index}提取到的有效画面不足2帧。")
            return {"index": index, "duration": duration, "fps": fps, "width": width, "height": height, "frames": frames}
        except ImportError as error:
            raise RuntimeError("当前ComfyUI环境缺少opencv-python，无法采样参考视频。") from error
    finally:
        if temporary:
            try:
                os.remove(path)
            except OSError:
                pass


def _normalize_audio(audio_input, index):
    if not isinstance(audio_input, dict) or audio_input.get("waveform") is None:
        raise ValueError(f"参考音频{index}缺少waveform，请连接ComfyUI原生AUDIO输出。")
    waveform = audio_input["waveform"]
    sample_rate = int(audio_input.get("sample_rate") or audio_input.get("sampler_rate") or 44100)
    if hasattr(waveform, "detach"):
        waveform = waveform.detach().cpu().numpy()
    array = np.squeeze(np.asarray(waveform))
    if array.ndim == 1:
        array = array.reshape(1, -1)
    elif array.ndim == 2 and array.shape[0] > 8 and array.shape[1] <= 8:
        array = array.T
    if array.ndim != 2 or array.shape[0] > 8:
        raise ValueError(f"参考音频{index}声道格式无法识别。")
    array = np.nan_to_num(np.clip(array.astype(np.float32), -1.0, 1.0))
    duration = array.shape[1] / float(sample_rate)
    if duration < MIN_MEDIA_DURATION:
        raise ValueError(f"参考音频{index}时长无效：{duration:.2f}秒。")
    return array, sample_rate, duration


def _audio_to_wav_base64(channels, sample_rate):
    pcm = (np.clip(channels.T, -1.0, 1.0) * 32767).astype(np.int16)
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(int(pcm.shape[1]))
        output.setsampwidth(2)
        output.setframerate(int(sample_rate))
        output.writeframes(pcm.tobytes())
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def _audio_spectrogram_uri(channels, sample_rate):
    mono = channels.mean(axis=0)
    frame_size, hop = 2048, 512
    if mono.size < frame_size:
        mono = np.pad(mono, (0, frame_size - mono.size))
    windows = []
    for start in range(0, max(1, mono.size - frame_size + 1), hop):
        window = mono[start:start + frame_size] * np.hanning(frame_size)
        windows.append(np.abs(np.fft.rfft(window))[:512])
    spectrum = np.stack(windows or [np.zeros(512)], axis=1)
    db = 20 * np.log10(np.maximum(spectrum, 1e-6))
    db -= np.max(db)
    normalized = np.clip((db + 80) / 80, 0, 1)
    normalized = np.flipud(normalized)
    rgb = (np.stack([normalized * 1.8, np.clip((normalized - .15) * 1.35, 0, 1), .18 + normalized * .82], axis=-1) * 255).clip(0, 255).astype(np.uint8)
    return _pil_data_uri(Image.fromarray(rgb).resize((1024, 512), Image.Resampling.BICUBIC), quality=88)


def _analyze_audio(audio_input, index, include_raw):
    channels, sample_rate, duration = _normalize_audio(audio_input, index)
    mono = channels.mean(axis=0)
    peak = float(np.max(np.abs(mono)))
    rms = float(np.sqrt(np.mean(np.square(mono), dtype=np.float64)))
    return {
        "index": index, "duration": duration, "sample_rate": sample_rate,
        "channels": int(channels.shape[0]), "rms": rms, "peak": peak,
        "spectrogram_uri": _audio_spectrogram_uri(channels, sample_rate),
        **({"raw_wav_base64": _audio_to_wav_base64(channels, sample_rate)} if include_raw else {}),
    }


def _content_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(str(item.get("text") or item.get("output_text")) for item in content if isinstance(item, dict) and (item.get("text") or item.get("output_text")))


def _extract_text(result):
    if not isinstance(result, dict):
        return ""
    choices = result.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        return _content_text(message.get("content")) or str(first.get("text") or "")
    return str(result.get("output_text") or "")


def _sanitized(value):
    if isinstance(value, dict):
        return {k: _sanitized(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitized(v) for v in value]
    if isinstance(value, str) and (value.startswith("data:") or len(value) > 20000):
        return f"<内容已省略，共{len(value)}字符>"
    return value


def _parse_json(text):
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(cleaned):
            if char != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(cleaned[index:])
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                continue
    return {}


def _mode_from_inputs(selected, first, last, refs, videos, audios, state, observation):
    if selected != "自动识别":
        return selected
    if observation and state:
        return "Review-成片复盘"
    if state and not (first or last or refs or videos or audios):
        return "Sequence-连续剧情"
    if videos and (refs or audios):
        return "R2V-全能参考"
    if videos:
        return "V2V-视频参考"
    if first and last:
        return "FLF2V-首尾帧"
    if first:
        return "I2V-图生视频"
    if refs or audios or last:
        return "R2V-全能参考"
    return "T2V-文生视频"


STYLE_GUIDANCE = {
    "通用导演": "用一个可见主动作、一个有动机的主镜头运动和一个物理光源组织镜头。",
    "极简产品广告": "锁定产品身份、材质、Logo和结构，以亮相—卖点—英雄定格为节奏。",
    "品牌宣传短片": "只使用用户确认的品牌事实、文案和CTA，不虚构数据。",
    "真人电影叙事": "用可见表演、视线、道具和对白矛盾承载情绪，不使用空泛情绪词。",
    "动作大片": "明确动作起点、轨迹、碰撞结果和镜头终点，控制角色数量。",
    "悬疑惊悚·真相反转": "保留信息遮蔽，反转通过构图、道具或声音揭示，不靠无因果跳切。",
    "误会喜剧·结尾反转": "前段建立可误解的事实，结尾用一个可见行为完成反转。",
    "一本正经·荒诞反差": "用严肃执行方式承载荒诞事件，保持物理因果和明确收尾。",
    "整蛊打脸·连环反转": "每个反转必须有可见触发物，动作节奏逐步升级。",
    "萌宠治愈日常": "以动物真实动作、触感和安全互动为核心，避免拟人化失控。",
    "萌宠拟人喜剧": "拟人只通过服装、道具和动作表达，保留动物身体结构。",
    "邵氏复古武侠": "复古棚拍光、硬朗构图、明确兵器轨迹和一招一停的动作节拍。",
    "魅惑美女氛围大片": "以合法成年角色、服装、光线和镜头气质表达氛围，不写露骨内容。",
    "狗血穿越·逆袭短剧": "明确穿越触发、身份差异和一个可见逆袭动作，结尾停在新状态。",
    "豪门霸总·身份反转": "以道具、门禁、文件或视线完成身份信息揭示。",
    "国风仙侠奇幻": "锁定角色、法器和空间方向，特效有来源、路径、交互和消散。",
    "赛博朋克科幻短片": "使用可见霓虹来源、湿地反射、界面层级和清楚动作结果。",
    "音乐MV": "以音频节拍为时钟，明确可视节拍事件，歌词只使用用户提供文本。",
    "美食料理·ASMR": "强调真实材质、切割、蒸汽、油脂和逐项拟音。",
    "时尚美妆大片": "锁定妆容、服装、产品颜色和皮肤质感，镜头运动克制。",
    "建筑空间漫游": "先建立空间方向，再用单一运镜揭示尺度和材质。",
    "动漫热血动作": "保持角色轮廓、动作准备和冲击方向，避免连续高密度事件。",
    "3D动画短片": "锁定角色卡和场景卡，动作有准备—执行—回弹—反应。",
    "黏土定格·微缩模型": "表现黏土指纹、接缝和逐帧小步动作，拒绝光滑CG。",
    "纸艺定格科普": "纸张有厚度、切边、折痕和层间阴影，一个镜头只解释一个因果。",
    "手绘实拍融合": "真实空间和粗糙手绘层明确分工，接触必须成为变形原因。",
    "人物纪实·微纪录": "尊重观察事实，以自然光、真实空间声和克制镜头记录。",
    "科技UI功能演示": "只展示真实操作路径，文字稳定可读，避免假HUD。",
    "工业机械演示": "明确机械部件、受力方向、接触关系和安全的运动终点。",
    "文旅城市宣传片": "以地标、动线、时间和真实环境声建立空间记忆，不堆景点名词。",
}


SYSTEM_PROMPT = """你是 Seedance 2.0 的专业视频导演、提示词编译器和连续性监督。
你的任务不是生成视频，而是把用户创意编译成当前这一段可执行的 Seedance 提示词。

必须遵守：
1. 最终提示词使用自然语言，不输出内部字段名、JSON标签或抽象戏剧术语。
2. 先分配每个素材的唯一主职责，并写明哪些身份、Logo、场景和动作不能转移。
3. 最终提示词引用素材时必须使用原样标签 @Image1–@Image9、@Video1–@Video3、@Audio1–@Audio3；不能改成尖括号、方括号或重新编号。
4. 一个片段只承担一个主要可见动作、一个有动机的主镜头运动和一个明确结束状态。
5. 有项目状态时，observed_end_state 优先于 planned_end_state；不得重播已完成动作，也不得提前泄露 reserved_for_later。
6. 续写没有真实上一段结尾时，必须标记不确定，不得假设结尾。
7. 情绪必须通过可拍到的动作、视线、道具、光线、构图和声音表达，不能只写“更感人/更震撼”。
8. 处理真人、品牌、版权和声音素材时，只在用户明确授权和安全范围内工作。
9. 不要把平台特定的分辨率、时长、模型ID当成所有Seedance接口的通用保证。

只返回 JSON，字段固定为：
mode, prompt, director_analysis, reference_roles, clip_contract, project_state, production_notes。
其中 prompt 是最终交给视频生成节点的自然语言提示词；project_state 和 clip_contract 必须是可序列化对象。
"""


class SeedanceDirectorLLMClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, payload):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json", "User-Agent": "ComfyUI-dapaoAPI/Seedance2Director"}
        labels = {400: "请求参数错误", 401: "认证失败", 402: "余额不足", 403: "没有模型权限", 404: "映射模型不存在", 429: IMAGE_429_HINT, 500: "服务内部暂时异常", 502: "上游模型连接失败", 503: "模型服务繁忙或维护"}
        try:
            return submit_json_task(
                api_key=self.api_key, base_url=API_BASE_URL, endpoint="/v1/chat/completions",
                payload=payload, timeout=self.timeout, user_agent=headers["User-Agent"],
                error_factory=lambda status, message: RuntimeError(
                    f"{labels.get(status, '中转站请求失败')} {status}：{message}"
                ),
            )
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RuntimeError(f"{friendly_network_error(error, '提交LLM请求')} 已保存原幂等键供恢复。") from error


class DapaoSeedance20DirectorNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "I2V/FLF2V使用。"}),
            "🏁 尾帧图": ("IMAGE", {"tooltip": "FLF2V/全能参考使用。"}),
            "🎞️ 每个视频采样帧数": ("INT", {"default": 5, "min": 2, "max": 8, "step": 1}),
            "🎧 参考音频原声直传LLM": ("BOOLEAN", {"default": False, "tooltip": "同时发送音频频谱；原始WAV需要模型支持input_audio。"}),
            "📦 上一个项目状态JSON": ("STRING", {"multiline": True, "default": "{}", "tooltip": "连续剧情或续写时接入上一轮输出。"}),
            "🎬 上一段成片观察": ("STRING", {"multiline": True, "default": "", "tooltip": "复盘/续写时填写或描述上一段真实结尾。"}),
            "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
        }
        for index in range(1, MAX_IMAGES + 1):
            optional[f"🖼️ 参考图{index}"] = ("IMAGE", {"tooltip": f"Seedance源图片{index}，总数最多{MAX_IMAGES}张。"})
        for index in range(1, MAX_VIDEOS + 1):
            optional[f"🎞️ 参考视频{index}"] = ("VIDEO", {"tooltip": "Seedance源视频；具体时长限制按当前中转/上游平台校验。"})
            optional[f"🎵 参考音频{index}"] = ("AUDIO", {"tooltip": "Seedance源音频；具体时长限制按当前中转/上游平台校验。"})
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 dapaoAI API 密钥", "tooltip": "密钥只用于请求 https://api.dapaoai.com。"}),
                "🤖 LLM模型": (MODEL_OPTIONS, {"default": "gemini-3.7-flash"}),
                "🎛️ Seedance任务": (MODE_OPTIONS, {"default": "自动识别"}),
                "🎨 创作类型": (STYLE_OPTIONS, {"default": "通用导演"}),
                "🌐 输出中文提示词": ("BOOLEAN", {"default": False, "tooltip": "关闭时默认输出英文提示词；开启后输出简体中文。"}),
                "📝 原始视频需求": ("STRING", {"multiline": True, "default": "电影感镜头，主体动作自然，画面稳定，声音与动作同步。", "placeholder": "描述你想生成的视频、人物、动作、镜头和声音……"}),
                "⏱️ 目标时长(秒)": ("INT", {"default": 5, "min": 4, "max": 15, "step": 1}),
                "📐 视频比例": (ASPECT_RATIO_OPTIONS, {"default": "16:9"}),
                "🧩 目标分辨率": (RESOLUTION_OPTIONS, {"default": "自动"}),
                "🔊 原生音频": ("BOOLEAN", {"default": True}),
                "🌡️ 温度": ("FLOAT", {"default": 0.4, "min": 0.0, "max": 2.0, "step": 0.01}),
                "📝 最大输出令牌": ("INT", {"default": 4096, "min": 512, "max": 65536, "step": 1}),
                "🎲 Top_P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": "randomize", "tooltip": "仅控制ComfyUI缓存，不发送给接口。"}),
                "⌛ 请求超时": ("INT", {"default": 300, "min": 30, "max": 1200, "step": 10}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 Seedance最终提示词", "🎛️ 识别任务", "📑 导演与素材分析", "📦 项目状态JSON", "🧾 当前片段合同", "📄 LLM完整响应", "ℹ️ 处理信息")
    FUNCTION = "generate_prompt"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "Seedance 2.0全能导演：提示词编译、素材角色映射、连续剧情状态、复盘与失败修复。"

    @staticmethod
    def _collect_images(kwargs):
        ordered = []
        first, last = kwargs.get("🎬 首帧图"), kwargs.get("🏁 尾帧图")
        for label, image in (("首帧图", first), ("尾帧图", last)):
            if image is not None:
                if image.shape[0] != 1:
                    raise ValueError(f"{label}只能包含1张图。")
                ordered.append((label, _tensor_to_data_uris(image)[0]))
        for slot in range(1, MAX_IMAGES + 1):
            image = kwargs.get(f"🖼️ 参考图{slot}")
            if image is not None:
                for batch_index, uri in enumerate(_tensor_to_data_uris(image), 1):
                    ordered.append((f"参考图{slot}" + (f"-{batch_index}" if image.shape[0] > 1 else ""), uri))
        if len(ordered) > MAX_IMAGES:
            raise ValueError(f"Seedance最多接受{MAX_IMAGES}张图片（含首帧和尾帧），当前{len(ordered)}张。")
        return ordered

    @staticmethod
    def _collect_media(kwargs):
        sample_count = int(kwargs.get("🎞️ 每个视频采样帧数", 5))
        include_raw = bool(kwargs.get("🎧 参考音频原声直传LLM", False))
        videos, audios = [], []
        for slot in range(1, MAX_VIDEOS + 1):
            value = kwargs.get(f"🎞️ 参考视频{slot}")
            if value is not None:
                item = _sample_video(value, len(videos) + 1, sample_count)
                item["slot"] = slot
                videos.append(item)
            value = kwargs.get(f"🎵 参考音频{slot}")
            if value is not None:
                item = _analyze_audio(value, len(audios) + 1, include_raw)
                item["slot"] = slot
                audios.append(item)
        if len(videos) > MAX_VIDEOS or len(audios) > MAX_AUDIOS:
            raise ValueError("Seedance参考视频最多3个，参考音频最多3个。")
        return videos, audios

    @staticmethod
    def _build_content(kwargs, mode, style, images, videos, audios, state, observation):
        language = "Simplified Chinese" if kwargs.get("🌐 输出中文提示词", False) else "English"
        manifest = {
            "images": [f"@Image{i}={name}" for i, (name, _) in enumerate(images, 1)],
            "videos": [f"@Video{i}=slot {x['slot']}, {x['duration']:.2f}s, {x['width']}x{x['height']}" for i, x in enumerate(videos, 1)],
            "audios": [f"@Audio{i}=slot {x['slot']}, {x['duration']:.2f}s, {x['sample_rate']}Hz, {x['channels']}ch" for i, x in enumerate(audios, 1)],
        }
        prompt_text = (
            f"Task mode: {mode}\nCreative type: {style}\nCreative guidance: {STYLE_GUIDANCE.get(style, STYLE_GUIDANCE['通用导演'])}\n"
            f"Output language: {language}\nDuration: {kwargs.get('⏱️ 目标时长(秒)', 5)} seconds\n"
            f"Aspect ratio: {kwargs.get('📐 视频比例', '16:9')}\nResolution request: {kwargs.get('🧩 目标分辨率', '自动')}\n"
            f"Native audio: {str(bool(kwargs.get('🔊 原生音频', True))).lower()}\n"
            f"SOURCE MANIFEST: {json.dumps(manifest, ensure_ascii=False)}\n"
            f"PREVIOUS PROJECT STATE JSON:\n{state}\n\nOBSERVED PREVIOUS TAKE:\n{observation}\n\nUSER VIDEO BRIEF:\n{(kwargs.get('📝 原始视频需求') or '').strip()}"
        )
        if not (images or videos or audios):
            return prompt_text
        content = [{"type": "text", "text": prompt_text}]
        for i, (name, uri) in enumerate(images, 1):
            content.extend([{"type": "text", "text": f"Source @Image{i} ({name}) follows."}, {"type": "image_url", "image_url": {"url": uri}}])
        for item in videos:
            for frame in item["frames"]:
                content.extend([{"type": "text", "text": f"Sampled frame from @Video{item['index']} at {frame['time']:.3f}s."}, {"type": "image_url", "image_url": {"url": frame["uri"]}}])
        for item in audios:
            content.extend([{"type": "text", "text": f"Spectrogram for @Audio{item['index']}; use for rhythm and energy only."}, {"type": "image_url", "image_url": {"url": item["spectrogram_uri"]}}])
            if item.get("raw_wav_base64"):
                content.append({"type": "input_audio", "input_audio": {"data": item["raw_wav_base64"], "format": "wav"}})
        return content

    async def generate_prompt(self, **kwargs):
        return await asyncio.to_thread(self._generate_prompt_sync, **kwargs)

    def _generate_prompt_sync(self, **kwargs):
        result = {}
        resolved_mode = ""
        try:
            api_key = (kwargs.get("🔑 API密钥") or "").strip()
            model = kwargs.get("🤖 LLM模型", "gemini-3.7-flash")
            selected = kwargs.get("🎛️ Seedance任务", "自动识别")
            style = kwargs.get("🎨 创作类型", "通用导演")
            brief = (kwargs.get("📝 原始视频需求") or "").strip()
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model not in MODEL_OPTIONS:
                raise ValueError(f"不支持的LLM模型：{model}")
            if selected not in MODE_OPTIONS or style not in STYLE_OPTIONS:
                raise ValueError("Seedance任务或创作类型不受支持。")
            if not brief:
                raise ValueError("原始视频需求不能为空。")
            images = self._collect_images(kwargs)
            videos, audios = self._collect_media(kwargs)
            if len(images) + len(videos) + len(audios) > MAX_FILES:
                raise ValueError(f"图片、视频、音频合计最多{MAX_FILES}个文件。")
            state = (kwargs.get("📦 上一个项目状态JSON") or "{}").strip() or "{}"
            try:
                state_obj = json.loads(state)
                if not isinstance(state_obj, dict):
                    raise ValueError
            except Exception as error:
                raise ValueError("上一个项目状态JSON必须是对象。") from error
            observation = (kwargs.get("🎬 上一段成片观察") or "").strip()
            resolved_mode = _mode_from_inputs(selected, kwargs.get("🎬 首帧图") is not None, kwargs.get("🏁 尾帧图") is not None, bool(images), videos, audios, state_obj if state_obj != {} else None, observation)
            user_content = self._build_content(kwargs, resolved_mode, style, images, videos, audios, state, observation)
            messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}]
            payload = {"model": model, "messages": messages, "temperature": float(kwargs.get("🌡️ 温度", .4)), "max_tokens": int(kwargs.get("📝 最大输出令牌", 4096)), "top_p": float(kwargs.get("🎲 Top_P", 1.0)), "stream": False}
            started = time.time()
            result = SeedanceDirectorLLMClient(api_key, int(kwargs.get("⌛ 请求超时", 300))).chat(payload)
            raw = _extract_text(result)
            if not raw:
                raise RuntimeError("LLM返回内容为空。")
            parsed = _parse_json(raw)
            final_prompt = str(parsed.get("prompt") or raw).strip()
            analysis = str(parsed.get("director_analysis") or "").strip()
            roles = parsed.get("reference_roles") if isinstance(parsed.get("reference_roles"), (dict, list)) else {}
            contract = parsed.get("clip_contract") if isinstance(parsed.get("clip_contract"), dict) else {"mode": resolved_mode, "duration_sec": int(kwargs.get("⏱️ 目标时长(秒)", 5)), "status": "ready"}
            new_state = parsed.get("project_state") if isinstance(parsed.get("project_state"), dict) else state_obj
            if not isinstance(new_state, dict):
                new_state = state_obj
            if not analysis:
                analysis = json.dumps({"reference_roles": roles, "production_notes": parsed.get("production_notes", "")}, ensure_ascii=False, indent=2)
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            info = (f"✅ Seedance2全能导演编译完成\n🌐 中转站：{API_BASE_URL}\n🤖 LLM模型：{model}\n🎛️ 识别任务：{resolved_mode}\n🎨 创作类型：{style}\n⏱️ 时长：{kwargs.get('⏱️ 目标时长(秒)', 5)}秒\n📐 比例：{kwargs.get('📐 视频比例', '16:9')}\n🖼️ 图片：{len(images)}张\n🎞️ 视频：{len(videos)}个\n🎵 音频：{len(audios)}个\n📥 输入令牌：{usage.get('prompt_tokens', usage.get('input_tokens', '未知'))}\n📤 输出令牌：{usage.get('completion_tokens', usage.get('output_tokens', '未知'))}\n⏱️ 耗时：{time.time() - started:.2f}秒")
            return final_prompt, resolved_mode, analysis, json.dumps(new_state, ensure_ascii=False, indent=2), json.dumps(contract, ensure_ascii=False, indent=2), json.dumps(_sanitized(result), ensure_ascii=False, indent=2), info
        except Exception as error:
            message = f"❌ Seedance2全能导演生成失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            response = json.dumps({"error": str(error), "response": _sanitized(result)}, ensure_ascii=False, indent=2)
            if kwargs.get("🚫 出错时跳过", False):
                return message, resolved_mode or "未知", message, "{}", "{}", response, message
            raise RuntimeError(message) from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoSeedance20DirectorNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}

__all__ = ["DapaoSeedance20DirectorNode", "MODEL_OPTIONS", "MODE_OPTIONS", "STYLE_OPTIONS", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
