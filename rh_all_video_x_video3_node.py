"""
RH all-in-one video X-video3 node.
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


NODE_NAME = "DapaoRHAllVideoXVideo3Node"
CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"

MODEL_CHOICES = ["X-video3", "X-video3-v1.5"]
CHANNEL_CHOICES = ["官方稳定版", "低价渠道版"]
FUNCTION_CHOICES = ["文生视频", "图生视频", "视频编辑", "多图参考生视频", "视频续写"]
RESOLUTION_CHOICES = ["720p", "480p"]
DURATION_CHOICES = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "20", "25", "30"]
RATIO_CHOICES = ["16:9", "9:16", "1:1", "2:3", "3:2"]

DEFAULT_PROMPT = "电影级真实运镜，主体动作自然连贯，光影真实，细节丰富，高质量视频。"


ENDPOINT_CONFIGS = {
    ("X-video3-v1.5", "低价渠道版", "文生视频"): {
        "endpoint": "rhart-video-g/text-to-video",
        "price": "¥0.04/秒",
        "resolutions": ["720p", "480p"],
        "durations": [str(i) for i in range(6, 31)],
        "ratios": ["2:3", "3:2", "1:1", "16:9", "9:16"],
        "price_unit": 0.04,
    },
    ("X-video3-v1.5", "低价渠道版", "图生视频"): {
        "endpoint": "rhart-video-g/image-to-video",
        "price": "¥0.04/秒",
        "resolutions": ["720p", "480p"],
        "durations": [str(i) for i in range(6, 31)],
        "ratios": ["2:3", "3:2", "1:1", "16:9", "9:16"],
        "image_array_key": "imageUrls",
        "max_images": 7,
        "price_unit": 0.04,
    },
    ("X-video3", "官方稳定版", "文生视频"): {
        "endpoint": "rhart-video-g-official/text-to-video",
        "price": "6秒¥1.89 / 10秒¥3.15",
        "resolutions": ["720p", "480p"],
        "durations": ["6", "10"],
        "ratios": ["16:9", "9:16", "1:1"],
        "duration_prices": {"6": "¥1.89", "10": "¥3.15"},
    },
    ("X-video3", "官方稳定版", "图生视频"): {
        "endpoint": "rhart-video-g-official/image-to-video",
        "price": "6秒¥1.89 / 10秒¥3.15",
        "resolutions": ["720p", "480p"],
        "durations": ["6", "10"],
        "image_key": "imageUrl",
        "duration_prices": {"6": "¥1.89", "10": "¥3.15"},
        "no_ratio": True,
    },
    ("X-video3", "官方稳定版", "视频编辑"): {
        "endpoint": "rhart-video-g-official/edit-video",
        "price": "¥0.41/秒",
        "resolutions": ["720p", "480p"],
        "video_key": "videoUrl",
        "edit_price_unit": 0.41,
        "no_duration": True,
        "no_ratio": True,
    },
    ("X-video3", "官方稳定版", "多图参考生视频"): {
        "endpoint": "rhart-video-g-official/reference-to-video",
        "price": "6秒¥1.89 / 10秒¥3.15",
        "resolutions": ["720p", "480p"],
        "durations": ["6", "10"],
        "image_array_key": "imageUrls",
        "max_images": 7,
        "duration_prices": {"6": "¥1.89", "10": "¥3.15"},
        "no_ratio": True,
    },
    ("X-video3", "官方稳定版", "视频续写"): {
        "endpoint": "rhart-video-g-official/video-extend",
        "price": "6秒¥1.89 / 10秒¥3.15",
        "durations": ["6", "10"],
        "video_key": "videoUrl",
        "duration_prices": {"6": "¥1.89", "10": "¥3.15"},
        "no_resolution": True,
        "no_ratio": True,
    },
    ("X-video3-v1.5", "官方稳定版", "图生视频"): {
        "endpoint": "rhart-video-g-official/image-to-video-v1.5",
        "price": "480p¥0.56/秒 / 720p¥0.95/秒",
        "resolutions": ["480p", "720p"],
        "durations": [str(i) for i in range(1, 16)],
        "image_key": "imageUrl",
        "resolution_price_units": {"480p": 0.56, "720p": 0.95},
        "no_ratio": True,
    },
}


def _log_info(message):
    print(f"[dapaoAPI-RH全能视频X-video3] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH全能视频X-video3] 错误：{message}")


class DapaoRHAllVideoXVideo3Node(DapaoRHAllVideoSeedanceNode):
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🎬 首帧图": ("IMAGE", {"tooltip": "图生视频使用。"}),
            "🎞️ 输入视频": (IO.VIDEO, {"tooltip": "视频编辑/视频续写使用。"}),
        }
        for i in range(1, 8):
            optional[f"🖼️ 参考图{i}"] = ("IMAGE", {"tooltip": f"低价图生视频/多图参考生视频参考图{i}，最多7张。"})
        optional.update({
            "🌐 首帧公网URL": ("STRING", {"default": "", "placeholder": "可选：图生视频图片 URL"}),
            "🖼️ 参考图URL列表": ("STRING", {"multiline": True, "default": "", "placeholder": "可选：一行一个图片 URL，最多7个"}),
            "🌐 视频公网URL": ("STRING", {"default": "", "placeholder": "视频编辑/视频续写可选：输入视频 URL"}),
            "🎞️ 参考视频时长(秒)": ("INT", {"default": 6, "min": 1, "max": 8, "step": 1, "tooltip": "仅视频编辑用于价格估算：按参考视频时长计费，最短1秒，最长8秒。"}),
            "📋 额外参数JSON": ("STRING", {"multiline": True, "default": "{}", "placeholder": "{\"webhookUrl\":\"https://example.com/webhook\"}"}),
            "🔁 最大轮询秒数": ("INT", {"default": 1800, "min": 60, "max": 7200, "step": 10}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 60, "step": 1}),
            "⌛ 请求超时": ("INT", {"default": 120, "min": 10, "max": 600, "step": 1}),
        })
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 RunningHub API Key"}),
                "🤖 模型": (MODEL_CHOICES, {"default": "X-video3"}),
                "🏷️ 渠道": (CHANNEL_CHOICES, {"default": "官方稳定版"}),
                "🎛️ 功能": (FUNCTION_CHOICES, {"default": "文生视频"}),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_PROMPT,
                    "placeholder": "文生/图生/视频编辑/多图参考/视频续写均需填写提示词。",
                }),
                "📐 视频比例": (RATIO_CHOICES, {"default": "16:9"}),
                "🧩 分辨率": (RESOLUTION_CHOICES, {"default": "720p"}),
                "⏱️ 时长(秒)": (DURATION_CHOICES, {"default": "6"}),
                "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
                "🎲 随机种": ("INT", {"default": -1, "min": -1, "max": 2147483647, "control_after_generate": "randomize"}),
            },
            "optional": optional,
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "generate_video"
    CATEGORY = CATEGORY
    DESCRIPTION = "RunningHub 全能视频 X-video3：文生、图生、视频编辑、多图参考、视频续写 @炮老师的小课堂"
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

    def _collect_image_urls(self, kwargs, api_key, timeout, max_images=7):
        urls = []
        first_url = (kwargs.get("🌐 首帧公网URL", "") or "").strip()
        if first_url:
            urls.append(first_url)
        first_image = kwargs.get("🎬 首帧图")
        if first_image is not None and not first_url:
            urls.append(self._image_to_url(first_image, api_key, "rh_xvideo3_first", timeout))

        for i in range(1, 8):
            if len(urls) >= max_images:
                break
            image = kwargs.get(f"🖼️ 参考图{i}")
            if image is not None:
                urls.append(self._image_to_url(image, api_key, f"rh_xvideo3_ref_{i}", timeout))

        for item in self._split_lines(kwargs.get("🖼️ 参考图URL列表", "")):
            if len(urls) >= max_images:
                break
            urls.append(item)

        return [url for url in urls if url][:max_images]

    def _collect_single_image_url(self, kwargs, api_key, timeout):
        public_url = (kwargs.get("🌐 首帧公网URL", "") or "").strip()
        if public_url:
            return public_url
        image = kwargs.get("🎬 首帧图")
        if image is None:
            image = kwargs.get("🖼️ 参考图1")
        if image is not None:
            return self._image_to_url(image, api_key, "rh_xvideo3_image", timeout)
        return ""

    def _source_video_url(self, kwargs, api_key, timeout):
        public_url = (kwargs.get("🌐 视频公网URL", "") or "").strip()
        if public_url:
            return public_url
        video = kwargs.get("🎞️ 输入视频")
        if video is None:
            raise ValueError("当前功能必须接入 🎞️ 输入视频，或填写 🌐 视频公网URL。")
        direct_url = getattr(video, "video_url", "")
        if isinstance(direct_url, str) and direct_url.startswith(("http://", "https://")):
            return direct_url
        url = self._video_to_url(video, api_key, "rh_xvideo3_video", timeout)
        if not url:
            raise ValueError("视频素材读取或上传失败。")
        return url

    @staticmethod
    def _validate_choice(config, field, value, label):
        allowed = config.get(field) or []
        if allowed and value not in allowed:
            raise ValueError(f"当前组合不支持{label} {value}，可用：{', '.join(allowed)}。")

    @staticmethod
    def _price_text(config, payload, kwargs=None):
        kwargs = kwargs or {}
        if config.get("edit_price_unit") is not None:
            seconds = int(kwargs.get("🎞️ 参考视频时长(秒)", 6) or 6)
            seconds = max(1, min(8, seconds))
            return f"约¥{config['edit_price_unit'] * seconds:.2f}/{seconds}秒"
        duration = str(payload.get("duration", ""))
        resolution = str(payload.get("resolution", ""))
        if config.get("duration_prices"):
            return config["duration_prices"].get(duration, config["price"])
        if config.get("price_unit") is not None:
            seconds = int(duration or 0)
            return f"约¥{config['price_unit'] * seconds:.2f}/{seconds}秒" if seconds > 0 else config["price"]
        if config.get("resolution_price_units"):
            unit = config["resolution_price_units"].get(resolution)
            seconds = int(duration or 0)
            if unit is not None and seconds > 0:
                return f"约¥{unit * seconds:.2f}/{seconds}秒"
        return config["price"]

    def _build_payload(self, kwargs, config, api_key, timeout):
        function = kwargs.get("🎛️ 功能", "文生视频")
        prompt = (kwargs.get("📝 提示词", "") or "").strip()
        resolution = kwargs.get("🧩 分辨率", "720p")
        duration = str(kwargs.get("⏱️ 时长(秒)", "6"))
        ratio = kwargs.get("📐 视频比例", "16:9")
        seed = int(kwargs.get("🎲 随机种", -1))

        if not prompt:
            raise ValueError(f"{function}必须填写提示词。")
        if not config.get("no_resolution"):
            self._validate_choice(config, "resolutions", resolution, "分辨率")
        if not config.get("no_duration"):
            self._validate_choice(config, "durations", duration, "时长")
        if not config.get("no_ratio"):
            self._validate_choice(config, "ratios", ratio, "视频比例")

        payload = {"prompt": prompt}
        if not config.get("no_resolution"):
            payload["resolution"] = resolution
        if not config.get("no_duration"):
            payload["duration"] = duration
        if not config.get("no_ratio"):
            payload["aspectRatio"] = ratio
        if seed >= 0:
            payload["seed"] = seed

        if function == "图生视频":
            if config.get("image_array_key"):
                image_urls = self._collect_image_urls(kwargs, api_key, timeout, config.get("max_images", 7))
                if not image_urls:
                    raise ValueError("图生视频请至少接入一张图片，或填写图片URL。")
                payload[config["image_array_key"]] = image_urls
            else:
                image_url = self._collect_single_image_url(kwargs, api_key, timeout)
                if not image_url:
                    raise ValueError("图生视频必须接入 🎬 首帧图、🖼️ 参考图1，或填写 🌐 首帧公网URL。")
                payload[config.get("image_key", "imageUrl")] = image_url
        elif function == "多图参考生视频":
            image_urls = self._collect_image_urls(kwargs, api_key, timeout, config.get("max_images", 7))
            if not image_urls:
                raise ValueError("多图参考生视频请至少接入一张参考图，或填写图片URL。")
            payload[config.get("image_array_key", "imageUrls")] = image_urls
        elif function in ("视频编辑", "视频续写"):
            payload[config.get("video_key", "videoUrl")] = self._source_video_url(kwargs, api_key, timeout)

        payload.update(self._parse_extra_params(kwargs.get("📋 额外参数JSON", "{}")))
        return payload

    def generate_video(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥", "") or "").strip()
        model = kwargs.get("🤖 模型", "X-video3")
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
            _log_info(f"开始请求 RH 全能视频X-video3：{endpoint}")
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
                "✅ RH 全能视频 X-video3 任务完成",
                f"🤖 模型：{model}",
                f"🏷️ 渠道：{channel}",
                f"🎛️ 功能：{function}",
                f"📡 端点：{config['endpoint']}",
                f"💵 标价：{self._price_text(config, payload, kwargs)}",
                f"🧩 分辨率：{payload.get('resolution', '接口默认')}",
                f"⏱️ 时长：{payload.get('duration', '接口默认')}",
                f"📐 比例：{payload.get('aspectRatio', '接口默认')}",
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
            error_msg = f"❌ 错误：RH 全能视频 X-video3 生成失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            raw_json = json.dumps({"payload": payload, "submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return self._error_result(error_msg + "\n\n" + raw_json)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHAllVideoXVideo3Node,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🎉RH全能视频X-video3@炮老师的小课堂",
}
