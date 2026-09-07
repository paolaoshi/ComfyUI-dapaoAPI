"""Wan 3.0 allround video node for the dapaoAI persistent queue."""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import traceback

from .dreambrush_runtime import ensure_asset_references, submit_json_task
from .media_preprocess_utils import MIB, prepare_audio, prepare_image_tensor, prepare_video
from .seedance20_allround_video_node import (
    API_BASE_URL, IO, DapaoSeedanceRelayClient, DapaoVideoAdapter,
    _extract_video_url, _safe_print, _sanitized_result, _task_id,
)


NODE_NAME = "DapaoWan30AllroundVideoNode"
DISPLAY_NAME = "🦭万相3.0全能视频@炮老师的小课堂"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
MODEL_OPTIONS = ["wan3.0", "wan3.0-fast", "wan3.0-video"]
VIDEO_REFERENCE_MODELS = {"wan3.0-video"}
MODE_OPTIONS = ["文生视频", "图生视频", "首尾帧生视频", "多模态参考"]
RESOLUTION_OPTIONS = ["720P", "1080P"]
ASPECT_RATIO_OPTIONS = ["自适应", "16:9", "9:16", "1:1"]
DURATION_OPTIONS = [str(value) for value in range(2, 31)]
MAX_IMAGES = 10
MAX_VIDEOS = 5
MAX_AUDIOS = 5
MAX_IMAGE_TOTAL = 20 * MIB
MAX_AUDIO_TOTAL = 15 * MIB


class DapaoWan30APIError(RuntimeError):
    def __init__(self, status_code, message):
        labels = {400: "请求参数或媒体素材不符合Wan 3.0要求", 401: "认证失败，请检查API密钥",
                  402: "余额不足，请充值后重试", 403: "没有模型或接口权限", 404: "接口、模型或任务不存在",
                  413: "素材或请求体过大，请减少素材；图片逐张应不超过2K，视频请裁剪后重试",
                  429: "请求过于频繁或排队中，请稍后重试；并检查每张图片是否超过2K",
                  500: "服务端处理异常，请稍后重试", 502: "Wan 3.0上游暂时不可用，请稍后重试或切换模型",
                  503: "Wan 3.0服务繁忙，请稍后重试或切换模型"}
        super().__init__(f"{labels.get(int(status_code), '中转站请求失败')} {status_code}：{message}")


class Wan30RelayClient(DapaoSeedanceRelayClient):
    def upload_many(self, blobs):
        if not blobs:
            return []
        return ensure_asset_references(self.api_key, blobs, base_url=self.base_url, timeout=self.timeout)

    def submit(self, payload, recovery_salt=None):
        return submit_json_task(
            api_key=self.api_key, base_url=self.base_url, endpoint="/v1/video/generations",
            payload=payload, timeout=self.timeout, user_agent="ComfyUI-dapaoAPI/Wan30Allround",
            error_factory=DapaoWan30APIError,
            max_poll_seconds=self.max_poll_seconds,
            recovery_salt=recovery_salt,
            reuse_succeeded=True,
        )


class DapaoWan30AllroundVideoNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "图生或首尾帧模式必需；批次只取第1张。最长边自动压至2K。"}),
            "🏁 尾帧图": ("IMAGE", {"tooltip": "首尾帧模式必需；批次只取第1张。"}),
            "🔁 最大轮询秒数": ("INT", {"default": 3600, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30}),
            "⌛ 请求超时": ("INT", {"default": 180, "min": 30, "max": 600, "step": 10}),
            "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
        }
        for index in range(1, MAX_IMAGES + 1):
            optional[f"🖼️ 参考图{index}"] = ("IMAGE", {"tooltip": f"多模态参考图，最多{MAX_IMAGES}张，合计不超过20MB；提示词可按上传顺序写“图{index}”。"})
        for index in range(1, MAX_VIDEOS + 1):
            optional[f"🎞️ 参考视频{index}"] = (IO.VIDEO, {"tooltip": f"仅wan3.0-video，多段合计不超过15秒；自动转MP4/H.264/AAC、≤1080p/30fps；提示词写“视频{index}”。"})
        for index in range(1, MAX_AUDIOS + 1):
            optional[f"🎵 参考音频{index}"] = ("AUDIO", {"tooltip": f"参考音频最多5个、合计不超过15MB；自动转MP3；提示词写“音频{index}”。"})
        return {"required": {
            "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 dapaoAI API 密钥",
                "password": True,
                "tooltip": "建议留空并设置环境变量 DAPAO_API_KEY；直接填写的值可能随普通 ComfyUI 工作流保存。密钥只发送到 https://api.dapaoai.com。"}),
            "🤖 模型": (MODEL_OPTIONS, {"default": "wan3.0"}),
            "🎛️ 生成模式": (MODE_OPTIONS, {"default": "文生视频"}),
            "📝 提示词": ("STRING", {"multiline": True, "default": "电影感镜头，主体动作自然，画面稳定，光影与声音细节丰富"}),
            "🧩 分辨率": (RESOLUTION_OPTIONS, {"default": "720P"}),
            "📐 视频比例": (ASPECT_RATIO_OPTIONS, {"default": "自适应"}),
            "⏱️ 时长(秒)": (DURATION_OPTIONS, {"default": "5", "tooltip": "2–30秒；使用参考视频时最多15秒。"}),
            "🔊 生成音频": ("BOOLEAN", {"default": True}),
            "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                "control_after_generate": "randomize",
                "tooltip": "控制 ComfyUI 缓存和重新执行；生成后控制可选择固定、递增、递减或随机化。当前妙笔 Wan 3.0 接口不接收 seed。"}),
        }, "optional": optional}

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "Wan 3.0/fast/video 文生、图生、首尾帧和多模态参考；10图/5音频，video型号支持5段参考视频；本地预处理、asset复用和持久队列。"

    @staticmethod
    def _safe_response(value):
        media_keys = {"images", "videos", "audios", "image_urls", "video_urls", "audio_urls",
                      "input_reference", "first_frame_image", "last_frame_image",
                      "reference_images", "reference_videos", "reference_audios"}
        secret_keys = {"api_key", "apikey", "api-key", "authorization", "access_token", "access-token",
                       "token", "secret", "password", "credential", "密钥", "令牌", "密码"}
        if isinstance(value, dict):
            return {key: ("<敏感信息已隐藏>" if any(part in str(key).lower() for part in secret_keys) else
                          "<用户提示词已省略>" if str(key).lower() == "prompt" and item else
                          f"<用户素材已省略，共{len(item) if isinstance(item, list) else 1}项>"
                          if str(key).lower() in media_keys and item else DapaoWan30AllroundVideoNode._safe_response(item))
                    for key, item in value.items()}
        if isinstance(value, list):
            return [DapaoWan30AllroundVideoNode._safe_response(item) for item in value]
        if isinstance(value, str):
            value = re.sub(r"(?i)\bBearer\s+[^\s,;\"'}]+", "Bearer <敏感信息已隐藏>", value)
            value = re.sub(r"(?i)\bsk-[A-Za-z0-9_-]{8,}", "<敏感信息已隐藏>", value)
        return _sanitized_result(value)

    @staticmethod
    def _image_blobs(kwargs, names):
        blobs = []
        for name, prefix, single in names:
            value = kwargs.get(name)
            if value is None:
                continue
            prepared = prepare_image_tensor(value, prefix=prefix, max_count=1 if single else MAX_IMAGES)
            blobs.extend(prepared[:1] if single else prepared)
            if len(blobs) > MAX_IMAGES:
                raise ValueError(f"本地图片总数最多 {MAX_IMAGES} 张。")
        if sum(len(item[0]) for item in blobs) > MAX_IMAGE_TOTAL:
            raise ValueError("Wan 3.0 本地图片预处理后合计超过20MB，请减少图片或裁剪后重试。")
        return blobs

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        submitted, final, payload, stage = {}, {}, {}, "校验参数"
        model = str(kwargs.get("🤖 模型") or "wan3.0")
        try:
            api_key = str(kwargs.get("🔑 API密钥") or os.environ.get("DAPAO_API_KEY", "")).strip()
            prompt = str(kwargs.get("📝 提示词") or "").strip()
            mode = str(kwargs.get("🎛️ 生成模式") or "文生视频")
            resolution = str(kwargs.get("🧩 分辨率") or "720P")
            ratio = str(kwargs.get("📐 视频比例") or "自适应")
            duration = str(kwargs.get("⏱️ 时长(秒)") or "5")
            cache_seed = int(kwargs.get("🎲 随机种", 0))
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model not in MODEL_OPTIONS or mode not in MODE_OPTIONS:
                raise ValueError("模型或生成模式不受支持。")
            if not prompt:
                raise ValueError("提示词不能为空。")
            if resolution not in RESOLUTION_OPTIONS or ratio not in ASPECT_RATIO_OPTIONS or duration not in DURATION_OPTIONS:
                raise ValueError("分辨率、比例或时长选项无效。")
            frame_blobs, image_blobs, video_blobs, audio_blobs = [], [], [], []
            video_seconds = audio_seconds = 0.0
            stage = "预处理素材"
            if mode in {"图生视频", "首尾帧生视频"}:
                frame_names = [("🎬 首帧图", "wan30_first_frame", True)]
                if mode == "首尾帧生视频":
                    frame_names.append(("🏁 尾帧图", "wan30_last_frame", True))
                frame_blobs = self._image_blobs(kwargs, frame_names)
                required_frames = 2 if mode == "首尾帧生视频" else 1
                if len(frame_blobs) != required_frames:
                    raise ValueError("图生视频需要首帧；首尾帧生视频需要首帧和尾帧。")
            elif mode == "多模态参考":
                image_blobs = self._image_blobs(kwargs, [
                    (f"🖼️ 参考图{index}", f"wan30_reference_{index}", False) for index in range(1, MAX_IMAGES + 1)
                ])
                for index in range(1, MAX_AUDIOS + 1):
                    audio = kwargs.get(f"🎵 参考音频{index}")
                    if audio is not None:
                        blob = prepare_audio(audio, prefix=f"wan30_audio_{index}")
                        audio_seconds += blob[3]
                        audio_blobs.append(blob[:3])
                for index in range(1, MAX_VIDEOS + 1):
                    video = kwargs.get(f"🎞️ 参考视频{index}")
                    if video is not None:
                        if model not in VIDEO_REFERENCE_MODELS:
                            raise ValueError("参考视频仅支持 wan3.0-video，请切换模型或移除视频。")
                        blob = prepare_video(video, prefix=f"wan30_video_{index}", target_bytes=10 * MIB)
                        video_seconds += blob[3]
                        video_blobs.append(blob[:3])
                if video_seconds > 15.05:
                    raise ValueError(f"参考视频总时长不能超过15秒，当前约{video_seconds:.2f}秒。")
                if audio_seconds > 15.05:
                    raise ValueError(f"参考音频总时长不能超过15秒，当前约{audio_seconds:.2f}秒。")
                if sum(len(item[0]) for item in audio_blobs) > MAX_AUDIO_TOTAL:
                    raise ValueError("Wan 3.0参考音频预处理后合计超过15MB。")
                if video_blobs and int(duration) > 15:
                    raise ValueError("使用参考视频时，生成时长最多15秒。")
                if not any((image_blobs, video_blobs, audio_blobs)):
                    raise ValueError("多模态参考模式至少需要一种参考素材。")
            elif any(kwargs.get(f"🎞️ 参考视频{i}") is not None for i in range(1, MAX_VIDEOS + 1)):
                raise ValueError("参考视频只在多模态参考模式使用。")

            client = Wan30RelayClient(api_key, int(kwargs.get("⌛ 请求超时", 180)), int(kwargs.get("🔁 最大轮询秒数", 3600)))
            stage = "上传并复用素材"
            local_blobs = frame_blobs + image_blobs + video_blobs + audio_blobs
            uploaded = client.upload_many(local_blobs)
            cursor = 0
            local_frame_urls = uploaded[cursor:cursor + len(frame_blobs)]; cursor += len(frame_blobs)
            local_image_urls = uploaded[cursor:cursor + len(image_blobs)]; cursor += len(image_blobs)
            local_video_urls = uploaded[cursor:cursor + len(video_blobs)]; cursor += len(video_blobs)
            local_audio_urls = uploaded[cursor:cursor + len(audio_blobs)]
            image_urls = local_frame_urls if frame_blobs else local_image_urls
            video_urls = local_video_urls
            audio_urls = local_audio_urls
            if len(image_urls) > MAX_IMAGES or len(video_urls) > MAX_VIDEOS or len(audio_urls) > MAX_AUDIOS:
                raise ValueError("本地素材与公网素材合计超过模型数量上限。")

            payload = {"model": model, "prompt": prompt,
                       "aspect_ratio": "auto" if ratio == "自适应" else ratio,
                       "resolution": resolution.lower(),
                       "duration": int(duration), "seconds": duration,
                       "generate_audio": bool(kwargs.get("🔊 生成音频", True))}
            if mode == "图生视频":
                payload["input_reference"] = image_urls[0]
            elif mode == "首尾帧生视频":
                payload["first_frame_image"] = image_urls[0]
                payload["last_frame_image"] = image_urls[1]
            elif image_urls:
                payload["images"] = image_urls
            if video_urls:
                payload["videos"] = video_urls
            if audio_urls:
                payload["audios"] = audio_urls
            started = time.monotonic()
            stage = "提交并等待视频任务"
            submitted = client.submit(payload, recovery_salt=cache_seed)
            task_identifier = _task_id(submitted)
            submitted_url = _extract_video_url(submitted)
            if not task_identifier and not submitted_url:
                raise RuntimeError("提交成功但响应中没有任务ID或视频URL。")
            # The persistent queue only guarantees that the paid POST reached
            # the gateway. A queued upstream task still needs status polling.
            final = submitted if submitted_url else client.poll(
                task_identifier, int(kwargs.get("🔁 最大轮询秒数", 3600)), int(kwargs.get("⏱️ 轮询间隔", 5)))
            video_url = _extract_video_url(final)
            if not video_url:
                raise RuntimeError("视频任务完成，但响应中没有可识别的视频URL。")
            task_identifier = task_identifier or "同步返回"
            info = (f"✅ 万相3.0全能视频任务完成\n🌐 中转站：{API_BASE_URL}\n🤖 模型：{model}\n🎛️ 模式：{mode}\n"
                    f"⏱️ 时长：{duration}\n🧩 分辨率：{resolution}\n📐 比例：{ratio}\n🔊 生成音频：{payload['generate_audio']}\n"
                    f"🎲 随机种：{cache_seed}（仅用于ComfyUI缓存控制）\n"
                    f"🖼️ 图片：{len(image_urls)}张；🎞️ 视频：{len(video_urls)}段；🎵 音频：{len(audio_urls)}个\n"
                    f"💰 计费：按服务端最终输出秒数和模型价格结算\n🆔 任务ID：{task_identifier}\n🔗 视频URL：{video_url}\n"
                    f"⏱️ 耗时：{time.monotonic() - started:.2f}秒\n\n"
                    + json.dumps({"submit": self._safe_response(submitted), "final": self._safe_response(final)}, ensure_ascii=False, indent=2))
            dimensions = {"720P": 1280, "1080P": 1920}[resolution]
            if ratio == "9:16":
                width, height = round(dimensions * 9 / 16), dimensions
            elif ratio == "1:1":
                width = height = dimensions
            else:
                width, height = dimensions, round(dimensions * 9 / 16)
            return DapaoVideoAdapter(video_url, width, height), task_identifier, info, video_url
        except Exception as error:
            safe_error = self._safe_response(str(error))
            message = f"❌ 万相3.0全能视频生成失败：{safe_error}"
            _safe_print(message)
            _safe_print(self._safe_response(traceback.format_exc()))
            if kwargs.get("🚫 出错时跳过", False):
                return DapaoVideoAdapter(), "", message, ""
            detail = json.dumps({"stage": stage, "model": model, "payload": self._safe_response(payload),
                                 "submit": self._safe_response(submitted), "final": self._safe_response(final)},
                                ensure_ascii=False, indent=2)
            raise RuntimeError(f"{message}\n\n{detail}") from None


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoWan30AllroundVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}
