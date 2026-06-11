"""
RH video enhancement node.
"""

import json
import time
import traceback

from .rh_all_image_node import BASE_URL
from .rh_all_video_seedance_node import (
    DapaoRHAllVideoSeedanceNode,
    IO,
    RHSeedanceVideoAdapter,
)


NODE_NAME = "DapaoRHVideoEnhanceNode"
CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"

UPSCALE_CHOICES = ["不启用", "720p", "1080p", "2k", "4k"]
FPS_CHOICES = ["不启用", "开启增强"]

UPSCALE_ENDPOINT = "rhart-video/video-upscaler"
FPS_ENDPOINT = "rhart-video/video-fps-increaser"
UPSCALE_PRICE = "¥0.14/秒"
FPS_PRICE = "¥0.07/秒"


def _log_info(message):
    print(f"[dapaoAPI-RH视频超清] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH视频超清] 错误：{message}")


class DapaoRHVideoEnhanceNode(DapaoRHAllVideoSeedanceNode):
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "填入 RunningHub API Key",
                    "tooltip": "RunningHub API Key，仅用于本次请求，不会写入文件。",
                }),
                "🧩 超分目标": (UPSCALE_CHOICES, {
                    "default": "1080p",
                    "tooltip": "选择目标分辨率；不启用时跳过视频超分。",
                }),
                "🎞️ 帧率增强": (FPS_CHOICES, {
                    "default": "不启用",
                    "tooltip": "开启后会在超分之后继续执行视频帧率增强。",
                }),
            },
            "optional": {
                "video": (IO.VIDEO, {"tooltip": "输入视频素材。"}),
                "🌐 视频公网URL": ("STRING", {
                    "default": "",
                    "placeholder": "可选：直接填写可访问的视频 URL，优先于 video 输入。",
                }),
                "📋 额外参数JSON": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "{\"webhookUrl\":\"https://example.com/webhook\"}",
                }),
                "🎲 随机种": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "control_after_generate": "randomize",
                    "tooltip": "仅用于 ComfyUI 缓存控制，不会传给 RH。",
                }),
                "⚠️ 跳过错误": ("BOOLEAN", {"default": False}),
                "🔁 最大轮询秒数": ("INT", {"default": 1800, "min": 60, "max": 7200, "step": 10}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
                "⌛ 请求超时": ("INT", {"default": 120, "min": 10, "max": 600, "step": 1}),
            },
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "enhance_video"
    CATEGORY = CATEGORY
    DESCRIPTION = "RunningHub RH 视频超分 + 视频帧率增强 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _blank_result(message=""):
        return (RHSeedanceVideoAdapter(""), "", message, "")

    @staticmethod
    def _price_text(upscale_target, fps_mode):
        prices = []
        if upscale_target != "不启用":
            prices.append(UPSCALE_PRICE)
        if fps_mode != "不启用":
            prices.append(FPS_PRICE)
        if len(prices) == 2:
            return "¥0.21/秒"
        return prices[0] if prices else "未启用"

    @staticmethod
    def _build_extra_params(extra_params_text):
        try:
            extra_params = json.loads(extra_params_text or "{}")
        except Exception as e:
            raise ValueError(f"额外参数JSON无效：{e}") from e
        if not isinstance(extra_params, dict):
            raise ValueError("额外参数JSON必须是 JSON 对象。")
        return extra_params

    def _source_video_url(self, kwargs, api_key, timeout):
        public_url = (kwargs.get("🌐 视频公网URL", "") or "").strip()
        if public_url:
            return public_url

        video = kwargs.get("video")
        if video is None:
            raise ValueError("请接入 video，或填写 🌐 视频公网URL。")

        direct_url = getattr(video, "video_url", "")
        if isinstance(direct_url, str) and direct_url.startswith(("http://", "https://")):
            return direct_url

        url = self._video_to_url(video, api_key, "rh_video_enhance_input", timeout)
        if not url:
            raise ValueError("视频素材读取或上传失败，请检查 video 输入。")
        return url

    def _run_stage(self, api_key, endpoint, payload, max_seconds, interval, timeout):
        submit_response = self._post_json(f"{BASE_URL}/{endpoint}", api_key, payload, timeout)
        if submit_response.get("errorCode") or submit_response.get("errorMessage"):
            raise RuntimeError(f"RunningHub 提交失败：[{submit_response.get('errorCode') or ''}] {submit_response.get('errorMessage') or submit_response}")

        task_id = self._extract_task_id(submit_response)
        if not task_id:
            raise RuntimeError(f"提交成功但响应中没有 taskId：{json.dumps(submit_response, ensure_ascii=False)[:1000]}")

        submit_data = self._payload_data(submit_response)
        if submit_data.get("status") == "SUCCESS" and submit_data.get("results"):
            final_response = submit_data
        else:
            final_response = self._poll_task_video(task_id, api_key, max_seconds, interval, timeout)

        result_urls = self._extract_result_urls(final_response)
        video_url = self._pick_video_url(result_urls)
        if not video_url:
            raise RuntimeError(f"任务完成但没有返回视频 URL：{json.dumps(final_response, ensure_ascii=False)[:1000]}")

        return {
            "task_id": task_id,
            "video_url": video_url,
            "submit": submit_response,
            "final": final_response,
            "payload": payload,
        }

    def enhance_video(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥", "") or "").strip()
        upscale_target = kwargs.get("🧩 超分目标", "1080p")
        fps_mode = kwargs.get("🎞️ 帧率增强", "不启用")
        skip_error = bool(kwargs.get("⚠️ 跳过错误", False))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1800))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        timeout = int(kwargs.get("⌛ 请求超时", 120))

        if not api_key:
            return self._blank_result("❌ 错误：请填写 RunningHub API密钥。")
        if upscale_target == "不启用" and fps_mode == "不启用":
            return self._blank_result("❌ 错误：请至少启用超分或帧率增强。")

        start_time = time.time()
        stages = []
        try:
            extra_params = self._build_extra_params(kwargs.get("📋 额外参数JSON", "{}"))
            current_url = self._source_video_url(kwargs, api_key, timeout)

            if upscale_target != "不启用":
                payload = {"videoUrl": current_url, "targetResolution": upscale_target}
                payload.update(extra_params)
                _log_info(f"开始视频超分：{upscale_target}")
                stage = self._run_stage(api_key, UPSCALE_ENDPOINT, payload, max_seconds, interval, timeout)
                stage["name"] = "视频超分"
                stage["endpoint"] = UPSCALE_ENDPOINT
                stage["price"] = UPSCALE_PRICE
                stage["setting"] = upscale_target
                stages.append(stage)
                current_url = stage["video_url"]

            if fps_mode != "不启用":
                payload = {"videoUrl": current_url}
                payload.update(extra_params)
                _log_info("开始视频帧率增强")
                stage = self._run_stage(api_key, FPS_ENDPOINT, payload, max_seconds, interval, timeout)
                stage["name"] = "视频帧率增强"
                stage["endpoint"] = FPS_ENDPOINT
                stage["price"] = FPS_PRICE
                stage["setting"] = fps_mode
                stages.append(stage)
                current_url = stage["video_url"]

            elapsed_time = time.time() - start_time
            task_ids = [stage["task_id"] for stage in stages]
            final_response = stages[-1]["final"] if stages else {}
            cost, duration = self._extract_usage(final_response)

            info_lines = [
                "✅ RH 视频超清任务完成",
                f"🧩 超分目标：{upscale_target}",
                f"🎞️ 帧率增强：{fps_mode}",
                f"💵 当前标价：{self._price_text(upscale_target, fps_mode)}",
                f"🧱 执行步骤：{' -> '.join(stage['name'] for stage in stages)}",
                f"🆔 任务ID：{', '.join(task_ids)}",
                f"🔗 视频URL：{current_url}",
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
                f"🎲 随机种：{int(kwargs.get('🎲 随机种', 0))}（仅用于 ComfyUI 缓存控制）",
            ]
            if cost is not None:
                info_lines.append(f"💰 实际消耗：¥{cost}")
            if duration is not None:
                info_lines.append(f"⏳ RH任务耗时：{duration}")

            raw_json = json.dumps({"stages": stages}, ensure_ascii=False, indent=2)
            return (
                RHSeedanceVideoAdapter(current_url),
                ", ".join(task_ids),
                "\n".join(info_lines) + "\n\n" + raw_json,
                current_url,
            )
        except Exception as e:
            error_msg = f"❌ 错误：RH 视频超清处理失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            raw_json = json.dumps({"stages": stages}, ensure_ascii=False, indent=2)
            if skip_error:
                return self._blank_result(error_msg + "\n\n" + raw_json)
            return self._blank_result(error_msg + "\n\n" + raw_json)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHVideoEnhanceNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🎉RH视频超清@炮老师的小课堂",
}
