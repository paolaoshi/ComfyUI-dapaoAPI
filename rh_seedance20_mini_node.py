"""
RH Seedance2.0 Mini node

One compact node for the RunningHub sparkvideo-2.0-mini text-to-video and
multimodal-video APIs.
作者：@炮老师的小课堂
"""

import json
import time
import traceback

import requests

from .rh_all_image_node import BASE_URL
from .rh_all_video_seedance_node import (
    DapaoRHAllVideoSeedanceNode,
    RHSeedanceVideoAdapter,
)


NODE_NAME = "DapaoRHSeedance20MiniNode"
CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"

FUNCTION_CHOICES = ["文生视频", "多模态视频"]
RESOLUTION_CHOICES = ["480p", "720p", "1080p", "2k", "4k"]
DURATION_CHOICES = ["-1", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15"]
RATIO_CHOICES = ["adaptive", "16:9", "4:3", "1:1", "3:4", "9:16", "21:9"]
CONVERSION_SLOT_CHOICES = [
    "all",
    "image1",
    "image2",
    "image3",
    "image4",
    "image5",
    "image6",
    "image7",
    "image8",
    "image9",
    "video1",
    "video2",
    "video3",
]

MINI_ENDPOINT_CONFIGS = {
    "文生视频": {
        "endpoint": "rhart-video/sparkvideo-2.0-mini/text-to-video",
        "display_name": "seedance2.0-Mini/文生视频",
        "price": "480p¥0.3/秒，720p¥0.6/秒，1080p¥0.88/秒，2k¥1.02/秒，4k¥1.23/秒",
        "resolutions": RESOLUTION_CHOICES,
        "conversion_slots": [],
    },
    "多模态视频": {
        "endpoint": "rhart-video/sparkvideo-2.0-mini/multimodal-video",
        "display_name": "seedance2.0-Mini/多模态视频",
        "price": "无参考视频按分辨率计费；有参考视频按基础时长与分辨率附加计费",
        "resolutions": RESOLUTION_CHOICES,
        "conversion_slots": CONVERSION_SLOT_CHOICES,
    },
}

NO_REFERENCE_PRICE_UNITS = {
    "480p": 0.30,
    "720p": 0.60,
    "1080p": 0.88,
    "2k": 1.02,
    "4k": 1.23,
}

REFERENCE_PRICE_UNITS = {
    "480p": {"base": 0.20, "extra": 0.0},
    "720p": {"base": 0.40, "extra": 0.0},
    "1080p": {"base": 0.40, "extra": 0.28},
    "2k": {"base": 0.40, "extra": 0.42},
    "4k": {"base": 0.40, "extra": 0.63},
}

MIN_BILLING_SECONDS = {
    "4": 7,
    "5": 9,
    "6": 10,
    "7": 12,
    "8": 14,
    "9": 15,
    "10": 17,
    "11": 19,
    "12": 20,
    "13": 22,
    "14": 24,
    "15": 25,
}


def _log_info(message):
    print(f"[dapaoAPI-RH Seedance2.0 Mini] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH Seedance2.0 Mini] 错误：{message}")


class DapaoRHSeedance20MiniNode(DapaoRHAllVideoSeedanceNode):
    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for i in range(1, 10):
            optional[f"🖼️ 参考图{i}"] = ("IMAGE", {"tooltip": f"多模态视频参考图{i}，最多9张。"})
        for i in range(1, 4):
            optional[f"🎞️ 参考视频{i}"] = ("VIDEO", {"tooltip": f"多模态视频参考视频{i}，最多3个。"})
        for i in range(1, 4):
            optional[f"🎵 参考音频{i}"] = ("AUDIO", {"tooltip": f"多模态视频参考音频{i}，最多3个。"})
        optional.update({
            "asset_ids": ("STRING", {
                "default": "",
                "forceInput": True,
                "tooltip": "素材库 asset_id，可接 RH Seedance2.0素材ID/合并 输出；支持逗号或换行分隔。多模态视频会自动按素材类型分流。",
            }),
            "🖼️ 参考图URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "多模态视频可选：一行一个图片 URL"}),
            "🎞️ 参考视频URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "多模态视频可选：一行一个视频 URL"}),
            "🎵 参考音频URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "多模态视频可选：一行一个音频 URL"}),
            "🔄 更多素材转换槽位": ("STRING", {"multiline": True, "default": "", "placeholder": "可选多选：一行一个槽位，例如 image1\\nvideo1；填 all 时优先使用 all"}),
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}", "placeholder": "{\"webhookUrl\":\"https://example.com/webhook\"}"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 10, "max": 600, "step": 1}),
        })
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 RunningHub API Key"}),
                "🎛️ 功能": (FUNCTION_CHOICES, {"default": "文生视频"}),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "镜头缓慢推进，阳光穿过窗户，画面电影感，高质量视频",
                    "placeholder": "文生视频必填；多模态视频支持 @Image 1 / @Video 1 等引用。"
                }),
                "🧩 分辨率": (RESOLUTION_CHOICES, {"default": "720p"}),
                "⏱️ 时长(秒)": (DURATION_CHOICES, {"default": "5"}),
                "🔊 生成音频": ("BOOLEAN", {"default": True}),
                "📐 视频比例": (RATIO_CHOICES, {"default": "adaptive"}),
                "🧍 真人模式": ("BOOLEAN", {"default": True, "tooltip": "开启后 RH 会尝试把素材转为 asset:// 以增强人物一致性。"}),
                "🔄 素材转换槽位": (CONVERSION_SLOT_CHOICES, {"default": "all"}),
                "🎞️ 参考视频总时长(秒)": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 45.0, "step": 0.1}),
                "🖼️ 返回尾帧": ("BOOLEAN", {"default": False}),
                "🔎 联网搜索": ("BOOLEAN", {"default": False, "tooltip": "仅文生视频接口使用。"}),
                "🎲 随机种": ("INT", {"default": -1, "min": -1, "max": 2147483647, "control_after_generate": "randomize"}),
                "skip_error": ("BOOLEAN", {"default": False}),
            },
            "optional": optional,
        }

    CATEGORY = CATEGORY
    DESCRIPTION = "RunningHub seedance2.0-Mini：文生视频、多模态视频 @炮老师的小课堂"

    @staticmethod
    def _has_reference_video(kwargs):
        if DapaoRHAllVideoSeedanceNode._split_lines(kwargs.get("🎞️ 参考视频URL列表", "")):
            return True
        return any(kwargs.get(f"🎞️ 参考视频{i}") is not None for i in range(1, 4))

    @staticmethod
    def _price_text(function, resolution, duration, reference_video_seconds=0.0, has_reference_video=False):
        duration = str(duration)
        unit = NO_REFERENCE_PRICE_UNITS.get(resolution)
        seconds = float(duration) if duration != "-1" else 0.0
        if function != "多模态视频" or not has_reference_video:
            if unit is None:
                return "价格待补"
            if seconds <= 0:
                return f"¥{unit:g}/秒"
            return f"约¥{unit * seconds:.2f}/{seconds:g}秒"

        ref_config = REFERENCE_PRICE_UNITS.get(resolution)
        if not ref_config:
            return "价格待补"
        if seconds <= 0:
            if ref_config["extra"]:
                return f"基础¥{ref_config['base']:g}/秒 + 附加¥{ref_config['extra']:g}/秒"
            return f"¥{ref_config['base']:g}/秒"

        min_seconds = MIN_BILLING_SECONDS.get(duration, seconds)
        base_seconds = max(float(reference_video_seconds or 0.0) + seconds, float(min_seconds))
        total = base_seconds * ref_config["base"] + seconds * ref_config["extra"]
        return f"约¥{total:.2f}/{seconds:g}秒"

    def _upload_bytes(self, api_key, content, filename, mime_type, timeout):
        upload_url = f"{getattr(self, '_active_base_url', BASE_URL).rstrip('/')}/media/upload/binary"
        files = {"file": (filename, content, mime_type)}
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(upload_url, headers=headers, files=files, timeout=max(timeout, 120))
        if response.status_code >= 400:
            raise RuntimeError(f"媒体上传失败 {response.status_code}：{self._error_message(response)}")
        data = response.json()
        if data.get("code") == 0:
            url = data.get("data", {}).get("download_url")
            if url:
                return url
        raise RuntimeError(f"媒体上传失败：{data.get('msg') or data.get('message') or data}")

    def _query_asset_type(self, api_key, asset_id, timeout):
        response = self._post_json(
            f"{getattr(self, '_active_base_url', BASE_URL).rstrip('/')}/assets/query",
            api_key,
            {"assetId": asset_id},
            timeout,
        )
        data = response.get("data") or {}
        asset_type = str(data.get("assetType") or "").strip().lower()
        if not asset_type:
            raise ValueError(f"素材 {asset_id} 没有返回 assetType，无法判断应接入图片、视频还是音频槽位。")
        return asset_type

    def _poll_task_video(self, task_id, api_key, max_seconds, interval, timeout):
        poll_url = f"{getattr(self, '_active_base_url', BASE_URL).rstrip('/')}/query"
        elapsed = 0
        consecutive_failures = 0
        try:
            import comfy.utils
            pbar = comfy.utils.ProgressBar(100)
        except Exception:
            pbar = None
        if pbar:
            pbar.update_absolute(5)

        while elapsed < max_seconds:
            time.sleep(interval)
            elapsed += interval
            try:
                result = self._post_json(poll_url, api_key, {"taskId": task_id}, timeout)
                consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1
                if consecutive_failures >= 5:
                    raise RuntimeError(f"连续多次轮询失败，任务状态未知。最后错误：{e}")
                continue

            result_data = self._payload_data(result)
            status = result_data.get("status") or result.get("status", "UNKNOWN")
            if pbar:
                pbar.update_absolute(min(95, max(5, int(elapsed / max_seconds * 95))))
            if status == "SUCCESS":
                if pbar:
                    pbar.update_absolute(100)
                return result_data or result
            if status == "FAILED":
                error_code = result_data.get("errorCode") or result.get("errorCode") or ""
                error_msg = result_data.get("errorMessage") or result.get("errorMessage") or result.get("msg") or "Unknown error"
                raise RuntimeError(f"任务失败：[{error_code}] {error_msg}")

        raise RuntimeError(f"任务超过 {max_seconds} 秒仍未完成，请稍后查询任务ID：{task_id}")

    def generate_video(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥", "") or "").strip()
        self._active_base_url = BASE_URL

        function = kwargs.get("🎛️ 功能", "文生视频")
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1200))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        skip_error = bool(kwargs.get("skip_error", False))

        if not api_key:
            return (RHSeedanceVideoAdapter(""), "", "❌ 错误：请填写 RunningHub API密钥。", "", self._blank_last_frame())

        config = MINI_ENDPOINT_CONFIGS.get(function)
        if not config:
            return (RHSeedanceVideoAdapter(""), "", f"❌ 错误：当前功能没有可用接口：{function}", "", self._blank_last_frame())

        start_time = time.time()
        submit_response = {}
        final_response = {}
        try:
            payload = self._build_payload(kwargs, config, api_key, timeout)
            endpoint = config["endpoint"]
            _log_info(f"开始请求 RH Seedance2.0 Mini：{endpoint}")
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
            last_frame_url = self._pick_last_frame_url(result_urls, video_url) if bool(kwargs.get("🖼️ 返回尾帧", False)) else ""
            last_frame = self._download_last_frame(last_frame_url, timeout) if last_frame_url else self._blank_last_frame()

            elapsed_time = time.time() - start_time
            cost, duration_cost = self._extract_usage(final_response)
            price_text = self._price_text(
                function,
                payload.get("resolution"),
                payload.get("duration"),
                kwargs.get("🎞️ 参考视频总时长(秒)", 0.0),
                self._has_reference_video(kwargs),
            )
            info_lines = [
                "✅ RH Seedance2.0 Mini 任务完成",
                f"🎛️ 功能：{function}",
                f"📡 端点：{endpoint}",
                f"💵 标价：{price_text}",
                f"🧩 分辨率：{payload.get('resolution')}",
                f"⏱️ 时长：{payload.get('duration')} 秒",
                f"📐 比例：{payload.get('ratio')}",
                f"🔊 生成音频：{payload.get('generateAudio')}",
                f"🧍 真人模式：{payload.get('realPersonMode', '未使用')}",
                f"🔄 素材转换槽位：{payload.get('conversionSlots', '未使用')}",
                f"🖼️ 返回尾帧：{payload.get('returnLastFrame')}",
                f"🎲 随机种：{payload.get('seed')}",
                f"🆔 任务ID：{task_id}",
                f"🔗 视频URL：{video_url}",
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
            ]
            if cost is not None:
                info_lines.append(f"💰 实际消耗：¥{cost}")
            if duration_cost is not None:
                info_lines.append(f"⏳ RH任务耗时：{duration_cost}")
            if last_frame_url:
                info_lines.append(f"🏁 尾帧URL：{last_frame_url}")

            raw_json = json.dumps({"payload": payload, "submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return (RHSeedanceVideoAdapter(video_url), task_id, "\n".join(info_lines) + "\n\n" + raw_json, video_url, last_frame)
        except Exception as e:
            error_msg = f"❌ 错误：RH Seedance2.0 Mini 生成失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            raw_json = json.dumps({"submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            if skip_error:
                return (RHSeedanceVideoAdapter(""), "", error_msg + "\n\n" + raw_json, "", self._blank_last_frame())
            return (RHSeedanceVideoAdapter(""), "", error_msg + "\n\n" + raw_json, "", self._blank_last_frame())


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHSeedance20MiniNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🎉RH seedance2.0-Mini@炮老师的小课堂",
}
