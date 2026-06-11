"""
RH all-in-one video V3.1 node.
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


NODE_NAME = "DapaoRHAllVideoV31Node"
CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"

MODEL_CHOICES = ["V3.1-FAST", "V3.1-PRO", "V3.1-LITE"]
CHANNEL_CHOICES = ["官方稳定版", "低价渠道版"]
FUNCTION_CHOICES = ["文生视频", "图生视频", "首尾帧生视频", "参考生视频", "视频扩展"]
RESOLUTION_CHOICES = ["720p", "1080p", "4k"]
DURATION_CHOICES = ["4", "6", "8"]
RATIO_CHOICES = ["16:9", "9:16"]

DEFAULT_PROMPT = "电影级写实质感，镜头缓慢推进，主体动作自然连贯，光影真实，高质量视频。"


ENDPOINT_CONFIGS = {
    ("V3.1-FAST", "低价渠道版", "文生视频"): {
        "endpoint": "rhart-video-v3.1-fast/text-to-video",
        "price": "¥1.5",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
    },
    ("V3.1-FAST", "低价渠道版", "图生视频"): {
        "endpoint": "rhart-video-v3.1-fast/image-to-video",
        "price": "¥1.5",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
        "image_array_key": "imageUrls",
        "max_images": 3,
    },
    ("V3.1-FAST", "低价渠道版", "首尾帧生视频"): {
        "endpoint": "rhart-video-v3.1-fast/start-end-to-video",
        "price": "¥1.5",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
        "first_key": "firstFrameUrl",
        "last_key": "lastFrameUrl",
        "last_required": False,
    },
    ("V3.1-PRO", "低价渠道版", "文生视频"): {
        "endpoint": "rhart-video-v3.1-pro/text-to-video",
        "price": "¥0.9",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
    },
    ("V3.1-PRO", "低价渠道版", "图生视频"): {
        "endpoint": "rhart-video-v3.1-pro/image-to-video",
        "price": "¥0.8",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
        "image_key": "imageUrl",
    },
    ("V3.1-PRO", "低价渠道版", "首尾帧生视频"): {
        "endpoint": "rhart-video-v3.1-pro/start-end-to-video",
        "price": "¥0.9",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
        "first_key": "firstFrameUrl",
        "last_key": "lastFrameUrl",
        "last_required": False,
    },
    ("V3.1-LITE", "低价渠道版", "文生视频"): {
        "endpoint": "rhart-video-v3.1-lite/text-to-video",
        "price": "价格待补",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
    },
    ("V3.1-LITE", "低价渠道版", "图生视频"): {
        "endpoint": "rhart-video-v3.1-lite/image-to-video",
        "price": "价格待补",
        "resolutions": ["720p", "4k"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
        "image_array_key": "imageUrls",
        "max_images": 3,
    },
    ("V3.1-FAST", "官方稳定版", "文生视频"): {
        "endpoint": "rhart-video-v3.1-fast-official/text-to-video",
        "price": "¥2.35",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["4", "6", "8"],
        "ratios": ["16:9", "9:16"],
        "supports_audio": True,
    },
    ("V3.1-FAST", "官方稳定版", "图生视频"): {
        "endpoint": "rhart-video-v3.1-fast-official/image-to-video",
        "price": "¥2.35",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["4", "6", "8"],
        "ratios": ["16:9", "9:16"],
        "image_key": "imageUrl",
        "last_key": "lastImageUrl",
        "supports_audio": True,
    },
    ("V3.1-FAST", "官方稳定版", "参考生视频"): {
        "endpoint": "rhart-video-v3.1-fast-official/reference-to-video",
        "price": "¥4.03",
        "resolutions": ["720p", "1080p"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
        "image_array_key": "imageUrls",
        "max_images": 3,
        "supports_audio": True,
        "no_duration": True,
    },
    ("V3.1-FAST", "官方稳定版", "视频扩展"): {
        "endpoint": "rhart-video-v3.1-fast-official/video-extend",
        "price": "¥6.56",
        "resolutions": ["720p", "1080p"],
        "durations": ["8"],
        "video_key": "video",
        "no_prompt_required": True,
        "no_duration": True,
        "no_ratio": True,
    },
    ("V3.1-PRO", "官方稳定版", "文生视频"): {
        "endpoint": "rhart-video-v3.1-pro-official/text-to-video",
        "price": "¥4.7",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["4", "6", "8"],
        "ratios": ["16:9", "9:16"],
        "supports_audio": True,
    },
    ("V3.1-PRO", "官方稳定版", "图生视频"): {
        "endpoint": "rhart-video-v3.1-pro-official/image-to-video",
        "price": "¥4.7",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["4", "6", "8"],
        "ratios": ["16:9", "9:16"],
        "image_key": "imageUrl",
        "last_key": "lastImageUrl",
        "supports_audio": True,
    },
    ("V3.1-PRO", "官方稳定版", "参考生视频"): {
        "endpoint": "rhart-video-v3.1-pro-official/reference-to-video",
        "price": "¥9.4",
        "resolutions": ["720p", "1080p", "4k"],
        "durations": ["8"],
        "image_array_key": "imageUrls",
        "max_images": 3,
        "supports_audio": True,
        "no_duration": True,
        "no_ratio": True,
    },
    ("V3.1-PRO", "官方稳定版", "视频扩展"): {
        "endpoint": "rhart-video-v3.1-pro-official/video-extend",
        "price": "¥17.4",
        "resolutions": ["720p", "1080p"],
        "durations": ["8"],
        "video_key": "video",
        "no_prompt_required": True,
        "no_duration": True,
        "no_ratio": True,
    },
    ("V3.1-LITE", "官方稳定版", "文生视频"): {
        "endpoint": "rhart-video-v3.1-lite-official/text-to-video",
        "price": "¥0.32/秒",
        "resolutions": ["720p", "1080p"],
        "durations": ["4", "6", "8"],
        "ratios": ["16:9", "9:16"],
    },
    ("V3.1-LITE", "官方稳定版", "图生视频"): {
        "endpoint": "rhart-video-v3.1-lite-official/image-to-video",
        "price": "¥0.32/秒",
        "resolutions": ["720p", "1080p"],
        "durations": ["4", "6", "8"],
        "ratios": ["16:9", "9:16"],
        "image_key": "imageUrl",
    },
    ("V3.1-LITE", "官方稳定版", "首尾帧生视频"): {
        "endpoint": "rhart-video-v3.1-lite-official/start-end-to-video",
        "price": "¥2.52",
        "resolutions": ["720p", "1080p"],
        "durations": ["8"],
        "ratios": ["16:9", "9:16"],
        "first_key": "firstImageUrl",
        "last_key": "lastImageUrl",
        "last_required": True,
        "no_duration": True,
    },
}


def _log_info(message):
    print(f"[dapaoAPI-RH全能视频V3.1] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH全能视频V3.1] 错误：{message}")


class DapaoRHAllVideoV31Node(DapaoRHAllVideoSeedanceNode):
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "图生视频/首尾帧生视频使用。"}),
            "🏁 尾帧图": ("IMAGE", {"tooltip": "图生视频可选，首尾帧生视频按接口要求使用。"}),
            "🎞️ 输入视频": (IO.VIDEO, {"tooltip": "视频扩展使用。"}),
        }
        for i in range(1, 4):
            optional[f"🖼️ 参考图{i}"] = ("IMAGE", {"tooltip": f"图生视频/参考生视频参考图{i}，最多3张。"})
        optional.update({
            "🌐 首帧公网URL": ("STRING", {"default": "", "placeholder": "可选：首帧/主图图片 URL"}),
            "🌐 尾帧公网URL": ("STRING", {"default": "", "placeholder": "可选：尾帧图片 URL"}),
            "🖼️ 参考图URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "可选：一行一个图片 URL，最多3个"}),
            "🌐 视频公网URL": ("STRING", {"default": "", "placeholder": "视频扩展可选：输入视频 URL"}),
            "🚫 反向提示词": ("STRING", {"multiline": True, "default": "", "placeholder": "可选：不希望出现的元素"}),
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}", "placeholder": "{\"webhookUrl\":\"https://example.com/webhook\"}"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1800, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 10, "max": 600, "step": 1}),
        })
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 RunningHub API Key"}),
                "🤖 模型": (MODEL_CHOICES, {"default": "V3.1-FAST"}),
                "🏷️ 渠道": (CHANNEL_CHOICES, {"default": "官方稳定版"}),
                "🎛️ 功能": (FUNCTION_CHOICES, {"default": "文生视频"}),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_PROMPT,
                    "placeholder": "文生/图生/首尾帧/参考生视频必填；视频扩展可选。",
                }),
                "🧩 分辨率": (RESOLUTION_CHOICES, {"default": "720p"}),
                "⏱️ 时长(秒)": (DURATION_CHOICES, {"default": "8"}),
                "📐 视频比例": (RATIO_CHOICES, {"default": "16:9"}),
                "🔊 生成音频": ("BOOLEAN", {"default": False}),
                "🎲 随机种": ("INT", {"default": -1, "min": -1, "max": 2147483647, "control_after_generate": "randomize"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "generate_video"
    CATEGORY = CATEGORY
    DESCRIPTION = "RunningHub 全能视频 V3.1：文生、图生、首尾帧、参考生视频、视频扩展 @炮老师的小课堂"
    OUTPUT_NODE = False

    def _error_result(self, message):
        return (RHSeedanceVideoAdapter(""), "", message, "")

    @staticmethod
    def _parse_extra_params(text):
        try:
            data = json.loads(text or "{}")
        except Exception as e:
            raise ValueError(f"额外参数JSON无效：{e}") from e
        if not isinstance(data, dict):
            raise ValueError("额外参数JSON必须是 JSON 对象。")
        return data

    def _collect_image_urls(self, kwargs, api_key, timeout, max_images=3):
        urls = []
        first_url = (kwargs.get("🌐 首帧公网URL", "") or "").strip()
        if first_url:
            urls.append(first_url)
        first_image = kwargs.get("🎬 首帧图")
        if first_image is not None and not first_url:
            urls.append(self._image_to_url(first_image, api_key, "rh_v31_first", timeout))

        for i in range(1, 4):
            if len(urls) >= max_images:
                break
            image = kwargs.get(f"🖼️ 参考图{i}")
            if image is not None:
                urls.append(self._image_to_url(image, api_key, f"rh_v31_ref_{i}", timeout))

        for item in self._split_lines(kwargs.get("🖼️ 参考图URL列表", "")):
            if len(urls) >= max_images:
                break
            urls.append(item)

        return [url for url in urls if url][:max_images]

    def _collect_first_last_urls(self, kwargs, config, api_key, timeout):
        first_url = (kwargs.get("🌐 首帧公网URL", "") or "").strip()
        last_url = (kwargs.get("🌐 尾帧公网URL", "") or "").strip()

        if not first_url and kwargs.get("🎬 首帧图") is not None:
            first_url = self._image_to_url(kwargs.get("🎬 首帧图"), api_key, "rh_v31_first", timeout)
        if not last_url and kwargs.get("🏁 尾帧图") is not None:
            last_url = self._image_to_url(kwargs.get("🏁 尾帧图"), api_key, "rh_v31_last", timeout)

        if not first_url:
            raise ValueError("当前功能必须接入 🎬 首帧图，或填写 🌐 首帧公网URL。")
        if config.get("last_required") and not last_url:
            raise ValueError("当前功能必须接入 🏁 尾帧图，或填写 🌐 尾帧公网URL。")
        return first_url, last_url

    def _source_video_url(self, kwargs, api_key, timeout):
        public_url = (kwargs.get("🌐 视频公网URL", "") or "").strip()
        if public_url:
            return public_url
        video = kwargs.get("🎞️ 输入视频")
        if video is None:
            raise ValueError("视频扩展必须接入 🎞️ 输入视频，或填写 🌐 视频公网URL。")
        direct_url = getattr(video, "video_url", "")
        if isinstance(direct_url, str) and direct_url.startswith(("http://", "https://")):
            return direct_url
        url = self._video_to_url(video, api_key, "rh_v31_extend", timeout)
        if not url:
            raise ValueError("视频素材读取或上传失败。")
        return url

    def _validate_choice(self, config, field, value, label):
        allowed = config.get(field) or []
        if allowed and value not in allowed:
            raise ValueError(f"当前组合不支持{label} {value}，可用：{', '.join(allowed)}。")

    def _build_payload(self, kwargs, config, api_key, timeout):
        function = kwargs.get("🎛️ 功能", "文生视频")
        prompt = (kwargs.get("📝 提示词", "") or "").strip()
        resolution = kwargs.get("🧩 分辨率", "720p")
        duration = str(kwargs.get("⏱️ 时长(秒)", "8"))
        ratio = kwargs.get("📐 视频比例", "16:9")
        negative_prompt = (kwargs.get("🚫 反向提示词", "") or "").strip()
        seed = int(kwargs.get("🎲 随机种", -1))
        generate_audio = bool(kwargs.get("🔊 生成音频", False))

        self._validate_choice(config, "resolutions", resolution, "分辨率")
        if not config.get("no_duration"):
            self._validate_choice(config, "durations", duration, "时长")
        if not config.get("no_ratio"):
            self._validate_choice(config, "ratios", ratio, "视频比例")
        if not config.get("no_prompt_required") and not prompt:
            raise ValueError(f"{function}必须填写提示词。")

        payload = {}
        if prompt:
            payload["prompt"] = prompt
        if negative_prompt:
            payload["negativePrompt"] = negative_prompt
        if not config.get("no_ratio"):
            payload["aspectRatio"] = ratio
        if not config.get("no_duration"):
            payload["duration"] = duration
        payload["resolution"] = resolution
        if seed >= 0:
            payload["seed"] = seed
        if config.get("supports_audio"):
            payload["generateAudio"] = generate_audio

        if function == "图生视频":
            if config.get("image_array_key"):
                image_urls = self._collect_image_urls(kwargs, api_key, timeout, config.get("max_images", 3))
                if not image_urls:
                    raise ValueError("图生视频请至少接入一张图片，或填写图片URL。")
                payload[config["image_array_key"]] = image_urls
            else:
                first_url, last_url = self._collect_first_last_urls(kwargs, config, api_key, timeout)
                payload[config.get("image_key", "imageUrl")] = first_url
                if config.get("last_key") and last_url:
                    payload[config["last_key"]] = last_url
        elif function == "首尾帧生视频":
            first_url, last_url = self._collect_first_last_urls(kwargs, config, api_key, timeout)
            payload[config.get("first_key", "firstFrameUrl")] = first_url
            if last_url:
                payload[config.get("last_key", "lastFrameUrl")] = last_url
        elif function == "参考生视频":
            image_urls = self._collect_image_urls(kwargs, api_key, timeout, config.get("max_images", 3))
            if not image_urls:
                raise ValueError("参考生视频请至少接入一张参考图，或填写图片URL。")
            payload[config.get("image_array_key", "imageUrls")] = image_urls
        elif function == "视频扩展":
            payload[config.get("video_key", "video")] = self._source_video_url(kwargs, api_key, timeout)

        payload.update(self._parse_extra_params(kwargs.get("📋 额外参数JSON", "{}")))
        return payload

    def generate_video(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥", "") or "").strip()
        model = kwargs.get("🤖 模型", "V3.1-FAST")
        channel = kwargs.get("🏷️ 渠道", "官方稳定版")
        function = kwargs.get("🎛️ 功能", "文生视频")
        timeout = int(kwargs.get("⌛ 请求超时", 120))
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1800))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))

        if not api_key:
            return self._error_result("❌ 错误：请填写 RunningHub API密钥。")

        config = ENDPOINT_CONFIGS.get((model, channel, function))
        if not config:
            return self._error_result(f"❌ 错误：当前组合没有可用接口：{model} / {channel} / {function}")

        start_time = time.time()
        submit_response = {}
        final_response = {}
        payload = {}
        try:
            payload = self._build_payload(kwargs, config, api_key, timeout)
            endpoint = config["endpoint"]
            _log_info(f"开始请求 RH 全能视频V3.1：{endpoint}")
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

            elapsed_time = time.time() - start_time
            cost, duration_cost = self._extract_usage(final_response)
            info_lines = [
                "✅ RH 全能视频 V3.1 任务完成",
                f"🤖 模型：{model}",
                f"🏷️ 渠道：{channel}",
                f"🎛️ 功能：{function}",
                f"📡 端点：{config['endpoint']}",
                f"💵 标价：{config['price']}",
                f"🧩 分辨率：{payload.get('resolution')}",
                f"⏱️ 时长：{payload.get('duration', '接口默认')}",
                f"📐 比例：{payload.get('aspectRatio', '接口默认')}",
                f"🔊 生成音频：{payload.get('generateAudio', '未使用')}",
                f"🎲 随机种：{payload.get('seed', '未使用')}",
                f"🆔 任务ID：{task_id}",
                f"🔗 视频URL：{video_url}",
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
            ]
            if cost is not None:
                info_lines.append(f"💰 实际消耗：¥{cost}")
            if duration_cost is not None:
                info_lines.append(f"⏳ RH任务耗时：{duration_cost}")

            raw_json = json.dumps({"payload": payload, "submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return (RHSeedanceVideoAdapter(video_url), task_id, "\n".join(info_lines) + "\n\n" + raw_json, video_url)
        except Exception as e:
            error_msg = f"❌ 错误：RH 全能视频 V3.1 生成失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            raw_json = json.dumps({"payload": payload, "submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return self._error_result(error_msg + "\n\n" + raw_json)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHAllVideoV31Node,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🎉RH全能视频V3.1@炮老师的小课堂",
}
