"""
RH 全能图片节点

按 RH_CLI 的 RunningHub 标准模型 API 调用全能图片系列模型。
作者：@炮老师的小课堂
"""

import base64
import io
import json
import time
import traceback

import numpy as np
import requests
import torch
from PIL import Image

try:
    import comfy.utils
except Exception:
    comfy = None


NODE_NAME = "DapaoRHAllImageNode"
API_HOST = "https://www.runninghub.cn"
BASE_URL = f"{API_HOST}/openapi/v2"
UPLOAD_URL = f"{BASE_URL}/media/upload/binary"
POLL_URL = f"{BASE_URL}/query"
INLINE_LIMIT_BYTES = 5 * 1024 * 1024

MODEL_CHOICES = ["全能图片G-2", "全能图片V2", "全能图片PRO"]
CHANNEL_CHOICES = ["官方稳定版", "低价渠道版"]
MODE_CHOICES = ["文生图", "图生图"]

ENDPOINT_CONFIGS = {
    ("全能图片G-2", "官方稳定版", "文生图"): {
        "endpoint": "rhart-image-g-2-official/text-to-image",
        "display_name": "RH 全能图片G-2-文生图-官方稳定版",
        "ratios": ["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "21:9", "9:21", "16:9"],
        "resolutions": ["1k", "2k", "4k"],
        "qualities": ["low", "medium", "high"],
        "default_ratio": "16:9",
        "default_resolution": "2k",
        "default_quality": "medium",
        "max_images": 0,
    },
    ("全能图片G-2", "官方稳定版", "图生图"): {
        "endpoint": "rhart-image-g-2-official/image-to-image",
        "display_name": "RH 全能图片G-2-图生图-官方稳定版",
        "ratios": ["1:1", "1:2", "2:1", "1:3", "3:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "21:9", "9:21", "16:9"],
        "resolutions": ["1k", "2k", "4k"],
        "qualities": ["low", "medium", "high"],
        "default_ratio": "16:9",
        "default_resolution": "2k",
        "default_quality": "medium",
        "max_images": 10,
    },
    ("全能图片G-2", "低价渠道版", "文生图"): {
        "endpoint": "rhart-image-g-2/text-to-image",
        "display_name": "RH 全能图片G-2-文生图-低价渠道版",
        "ratios": ["empty", "3:2", "1:1", "2:3", "5:4", "4:5", "16:9", "9:16", "21:9", "3:4", "4:3"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "empty",
        "default_resolution": "1k",
        "max_images": 0,
    },
    ("全能图片G-2", "低价渠道版", "图生图"): {
        "endpoint": "rhart-image-g-2/image-to-image",
        "display_name": "RH 全能图片G-2-图生图-低价渠道版",
        "ratios": ["empty", "3:2", "1:1", "2:3", "5:4", "4:5", "16:9", "9:16", "21:9", "3:4", "4:3"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "empty",
        "default_resolution": "1k",
        "max_images": 10,
    },
    ("全能图片V2", "官方稳定版", "文生图"): {
        "endpoint": "rhart-image-n-g31-flash-official/text-to-image",
        "display_name": "RH 全能图片V2-文生图-官方稳定版",
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "21:9",
        "default_resolution": "1k",
        "max_images": 0,
    },
    ("全能图片V2", "官方稳定版", "图生图"): {
        "endpoint": "rhart-image-n-g31-flash-official/image-to-image",
        "display_name": "RH 全能图片V2-图生图-官方稳定版",
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "9:16",
        "default_resolution": "1k",
        "max_images": 14,
    },
    ("全能图片V2", "低价渠道版", "文生图"): {
        "endpoint": "rhart-image-n-g31-flash/text-to-image",
        "display_name": "RH 全能图片V2-文生图-低价渠道版",
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "9:16",
        "default_resolution": "1k",
        "max_images": 0,
    },
    ("全能图片V2", "低价渠道版", "图生图"): {
        "endpoint": "rhart-image-n-g31-flash/image-to-image",
        "display_name": "RH 全能图片V2-图生图-低价渠道版",
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "1:4", "4:1", "1:8", "8:1"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "9:16",
        "default_resolution": "1k",
        "max_images": 10,
    },
    ("全能图片PRO", "官方稳定版", "文生图"): {
        "endpoint": "rhart-image-n-pro-official/text-to-image",
        "display_name": "RH 全能图片PRO-文生图-官方稳定版",
        "ratios": ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "3:4",
        "default_resolution": "1k",
        "max_images": 0,
    },
    ("全能图片PRO", "官方稳定版", "图生图"): {
        "endpoint": "rhart-image-n-pro-official/edit",
        "display_name": "RH 全能图片PRO-图生图-官方稳定版",
        "ratios": ["1:1", "3:2", "2:3", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "3:4",
        "default_resolution": "1k",
        "max_images": 10,
    },
    ("全能图片PRO", "低价渠道版", "文生图"): {
        "endpoint": "rhart-image-n-pro/text-to-image",
        "display_name": "RH 全能图片PRO-文生图-低价渠道版",
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "9:16",
        "default_resolution": "1k",
        "max_images": 0,
    },
    ("全能图片PRO", "低价渠道版", "图生图"): {
        "endpoint": "rhart-image-n-pro/edit",
        "display_name": "RH 全能图片PRO-图生图-低价渠道版",
        "ratios": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"],
        "resolutions": ["1k", "2k", "4k"],
        "default_ratio": "3:4",
        "default_resolution": "1k",
        "max_images": 10,
    },
}

ALL_RATIOS = [
    "模型默认",
    "empty",
    "1:1",
    "16:9",
    "9:16",
    "4:3",
    "3:4",
    "3:2",
    "2:3",
    "5:4",
    "4:5",
    "21:9",
    "1:2",
    "2:1",
    "1:3",
    "3:1",
    "9:21",
    "1:4",
    "4:1",
    "1:8",
    "8:1",
]


def _log_info(message):
    print(f"[dapaoAPI-RH全能图片] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH全能图片] 错误：{message}")


def pil2tensor(image):
    if image.mode != "RGB":
        image = image.convert("RGB")
    np_image = np.array(image).astype(np.float32) / 255.0
    return torch.from_numpy(np_image).unsqueeze(0)


def create_blank_tensor(width=1024, height=1024):
    blank_image = np.zeros((height, width, 3), dtype=np.float32)
    return torch.from_numpy(blank_image).unsqueeze(0)


class DapaoRHAllImageNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "填入 RunningHub API Key",
                    "tooltip": "RunningHub API Key，仅用于本次请求，不会写入文件。"
                }),
                "🤖 模型": (MODEL_CHOICES, {
                    "default": "全能图片G-2",
                    "tooltip": "只保留 G-2、V2、PRO 三个模型，具体端点由渠道和模式共同决定。"
                }),
                "🏷️ 渠道": (CHANNEL_CHOICES, {
                    "default": "官方稳定版",
                    "tooltip": "官方稳定版质量更稳；低价渠道版通常费用更低。"
                }),
                "🔀 模式": (MODE_CHOICES, {
                    "default": "文生图",
                    "tooltip": "文生图不需要参考图；图生图必须至少接入一张图像。"
                }),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "一张高端商业摄影海报，干净的自然光，细节清晰，质感高级",
                    "placeholder": "请输入图像生成或编辑要求..."
                }),
                "📐 画面比例": (ALL_RATIOS, {
                    "default": "模型默认",
                    "tooltip": "选择模型默认时自动使用当前端点默认比例。G-2 低价渠道的 empty 表示不指定比例。"
                }),
                "🧩 分辨率": (["模型默认", "1k", "2k", "4k"], {
                    "default": "模型默认",
                    "tooltip": "选择模型默认时自动使用当前端点默认分辨率。"
                }),
                "🎨 画质": (["模型默认", "low", "medium", "high"], {
                    "default": "模型默认",
                    "tooltip": "当前只在 G-2 官方稳定版端点中生效；其他端点会自动忽略。"
                }),
                "🎲 随机种": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": "randomize",
                    "tooltip": "只用于 ComfyUI 判断是否重新执行；不会发送给 RunningHub。"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE", {"tooltip": "图生图参考图。"}),
                "🖼️ 图像2": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像3": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像4": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像5": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像6": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像7": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像8": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像9": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像10": ("IMAGE", {"tooltip": "可选参考图。"}),
                "📋 额外参数JSON": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "{\"aspectRatio\":\"1:1\"}",
                    "tooltip": "JSON对象，会合并到 RH 请求体；同名字段会覆盖节点控件生成的参数。"
                }),
                "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 3600, "step": 10}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30, "step": 1}),
                "⌛ 请求超时": ("INT", {"default": 60, "min": 10, "max": 300, "step": 1}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/RH全能图片"
    DESCRIPTION = "RunningHub RH 全能图片系列：文生图、图生图、多参考图生成 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _headers(api_key):
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/RHAllImage",
        }

    @staticmethod
    def _error_message(response):
        text = response.text[:1000]
        try:
            data = response.json()
            if isinstance(data, dict):
                return data.get("msg") or data.get("message") or data.get("error") or text
        except Exception:
            pass
        return text

    def _post_json(self, url, api_key, payload, timeout):
        response = requests.post(url, headers=self._headers(api_key), json=payload, timeout=timeout)
        if response.status_code >= 400:
            raise RuntimeError(f"RunningHub 请求失败 {response.status_code}：{self._error_message(response)}")
        try:
            data = response.json()
        except Exception as e:
            raise RuntimeError(f"RunningHub 返回内容不是 JSON：{e}，响应：{response.text[:500]}")
        code = data.get("code") if isinstance(data, dict) else None
        if code not in (None, 0, "0"):
            raise RuntimeError(f"RunningHub API 返回错误：{data.get('msg') or data.get('message') or data}")
        return data

    @staticmethod
    def _payload_data(response):
        if isinstance(response, dict) and isinstance(response.get("data"), dict):
            return response["data"]
        return response if isinstance(response, dict) else {}

    @staticmethod
    def _extract_task_id(response):
        if not isinstance(response, dict):
            return None
        task_id = response.get("taskId") or response.get("task_id")
        data = response.get("data")
        if not task_id and isinstance(data, dict):
            task_id = data.get("taskId") or data.get("task_id")
        return str(task_id) if task_id else None

    @staticmethod
    def _extract_usage(final):
        data = DapaoRHAllImageNode._payload_data(final)
        usage = data.get("usage") or {}
        cost = usage.get("consumeMoney") or usage.get("thirdPartyConsumeMoney")
        duration = usage.get("taskCostTime")
        return cost, duration

    @staticmethod
    def _extract_urls(final):
        data = DapaoRHAllImageNode._payload_data(final)
        results = data.get("results") or []
        urls = []
        for item in results:
            if not isinstance(item, dict):
                continue
            item_url = item.get("url") or item.get("outputUrl")
            if isinstance(item_url, list):
                urls.extend([url for url in item_url if url])
            elif item_url:
                urls.append(str(item_url))
        return urls

    def _poll_task(self, task_id, api_key, max_seconds, interval, timeout):
        elapsed = 0
        consecutive_failures = 0
        pbar = comfy.utils.ProgressBar(100) if comfy is not None else None
        if pbar:
            pbar.update_absolute(5)

        while elapsed < max_seconds:
            time.sleep(interval)
            elapsed += interval
            try:
                result = self._post_json(POLL_URL, api_key, {"taskId": task_id}, timeout)
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
                error_msg = result_data.get("errorMessage") or result.get("msg") or "Unknown error"
                error_code = result_data.get("errorCode") or result.get("errorCode") or ""
                raise RuntimeError(f"任务失败：[{error_code}] {error_msg}")

        raise RuntimeError(f"任务超过 {max_seconds} 秒仍未完成，请稍后查询任务ID：{task_id}")

    @staticmethod
    def _tensor_batch_to_png_bytes(image_tensor):
        image_bytes = []
        for index in range(image_tensor.shape[0]):
            image_np = np.clip(image_tensor[index].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
            image = Image.fromarray(image_np).convert("RGB")
            buffer = io.BytesIO()
            image.save(buffer, format="PNG")
            image_bytes.append(buffer.getvalue())
        return image_bytes

    def _upload_image_bytes(self, api_key, content, filename, timeout):
        files = {"file": (filename, content, "image/png")}
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.post(UPLOAD_URL, headers=headers, files=files, timeout=max(timeout, 120))
        if response.status_code >= 400:
            raise RuntimeError(f"图片上传失败 {response.status_code}：{self._error_message(response)}")
        data = response.json()
        if data.get("code") == 0:
            download_url = data.get("data", {}).get("download_url")
            if download_url:
                return download_url
        raise RuntimeError(f"图片上传失败：{data.get('msg') or data}")

    def _image_bytes_to_input_url(self, api_key, content, filename, timeout):
        if len(content) > INLINE_LIMIT_BYTES:
            return self._upload_image_bytes(api_key, content, filename, timeout)
        encoded = base64.b64encode(content).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    def _collect_image_urls(self, kwargs, api_key, timeout, max_images):
        image_urls = []
        for input_index in range(1, 11):
            image_tensor = kwargs.get(f"🖼️ 图像{input_index}")
            if image_tensor is None:
                continue
            for batch_index, content in enumerate(self._tensor_batch_to_png_bytes(image_tensor), start=1):
                if len(image_urls) >= max_images:
                    return image_urls
                filename = f"comfyui_ref_{input_index}_{batch_index}.png"
                image_urls.append(self._image_bytes_to_input_url(api_key, content, filename, timeout))
        return image_urls

    @staticmethod
    def _download_image(url, timeout):
        response = requests.get(url, timeout=max(timeout, 120))
        if response.status_code >= 400:
            raise RuntimeError(f"图片下载失败，状态码：{response.status_code}，URL：{url}")
        return Image.open(io.BytesIO(response.content)).convert("RGB")

    def _build_payload(self, config, prompt, ratio, resolution, quality, image_urls, extra_params):
        payload = {"prompt": prompt}

        final_ratio = config["default_ratio"] if ratio == "模型默认" else ratio
        if final_ratio not in config["ratios"]:
            raise ValueError(f"当前端点不支持画面比例 {final_ratio}，可选：{', '.join(config['ratios'])}")
        if final_ratio != "empty":
            payload["aspectRatio"] = final_ratio

        final_resolution = config["default_resolution"] if resolution == "模型默认" else resolution
        if final_resolution not in config["resolutions"]:
            raise ValueError(f"当前端点不支持分辨率 {final_resolution}，可选：{', '.join(config['resolutions'])}")
        payload["resolution"] = final_resolution

        if image_urls:
            payload["imageUrls"] = image_urls

        if "qualities" in config:
            final_quality = config.get("default_quality", "medium") if quality == "模型默认" else quality
            if final_quality not in config["qualities"]:
                raise ValueError(f"当前端点不支持画质 {final_quality}，可选：{', '.join(config['qualities'])}")
            payload["quality"] = final_quality
        else:
            final_quality = "未使用"

        payload.update(extra_params)
        return payload, final_ratio, final_resolution, final_quality

    def generate(self, **kwargs):
        api_key = kwargs.get("🔑 API密钥", "").strip()
        model = kwargs.get("🤖 模型", "全能图片G-2")
        channel = kwargs.get("🏷️ 渠道", "官方稳定版")
        mode = kwargs.get("🔀 模式", "文生图")
        prompt = kwargs.get("📝 提示词", "").strip()
        ratio = kwargs.get("📐 画面比例", "模型默认")
        resolution = kwargs.get("🧩 分辨率", "模型默认")
        quality = kwargs.get("🎨 画质", "模型默认")
        cache_seed = int(kwargs.get("🎲 随机种", 0))
        extra_params_str = kwargs.get("📋 额外参数JSON", "{}")
        max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1200))
        interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        timeout = int(kwargs.get("⌛ 请求超时", 60))

        if not api_key:
            return (create_blank_tensor(), "", "❌ 错误：请填写 RunningHub API密钥。")
        if not prompt:
            return (create_blank_tensor(), "", "❌ 错误：提示词不能为空。")

        config = ENDPOINT_CONFIGS.get((model, channel, mode))
        if not config:
            return (create_blank_tensor(), "", f"❌ 错误：当前组合没有可用端点：{model} / {channel} / {mode}")

        try:
            extra_params = json.loads(extra_params_str or "{}")
            if not isinstance(extra_params, dict):
                raise ValueError("额外参数JSON必须是 JSON 对象")
        except Exception as e:
            return (create_blank_tensor(), "", f"❌ 错误：额外参数JSON无效：{e}")

        start_time = time.time()
        submit_response = {}
        final_response = {}

        try:
            image_urls = []
            if mode == "图生图":
                image_urls = self._collect_image_urls(kwargs, api_key, timeout, config["max_images"])
                if not image_urls:
                    raise ValueError("选择图生图时，请至少接入一张参考图。")

            payload, final_ratio, final_resolution, final_quality = self._build_payload(
                config,
                prompt,
                ratio,
                resolution,
                quality,
                image_urls,
                extra_params,
            )

            endpoint = config["endpoint"]
            _log_info(f"开始请求 RH：{endpoint}")
            _log_info(f"端点：{config['display_name']}，参考图：{len(image_urls)}，比例：{final_ratio}，分辨率：{final_resolution}")

            submit_response = self._post_json(f"{BASE_URL}/{endpoint}", api_key, payload, timeout)
            task_id = self._extract_task_id(submit_response)
            if not task_id:
                raise RuntimeError(f"提交成功但响应中没有 taskId：{json.dumps(submit_response, ensure_ascii=False)[:1000]}")

            submit_data = self._payload_data(submit_response)
            if submit_data.get("status") == "SUCCESS" and submit_data.get("results"):
                final_response = submit_data
            else:
                final_response = self._poll_task(task_id, api_key, max_seconds, interval, timeout)

            urls = self._extract_urls(final_response)
            if not urls:
                raise RuntimeError(f"任务完成但没有返回图片 URL：{json.dumps(final_response, ensure_ascii=False)[:1000]}")

            tensors = [pil2tensor(self._download_image(url, timeout)) for url in urls]
            final_tensor = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)

            elapsed_time = time.time() - start_time
            cost, duration = self._extract_usage(final_response)
            first_url = urls[0] if urls else ""

            info_lines = [
                "✅ RH 全能图片任务完成",
                f"🤖 模型：{model}",
                f"🏷️ 渠道：{channel}",
                f"🔀 模式：{mode}",
                f"📡 端点：{endpoint}",
                f"📐 画面比例：{final_ratio}",
                f"🧩 分辨率：{final_resolution}",
                f"🎨 画质：{final_quality}",
                f"🖼️ 结果数量：{len(urls)}",
                f"🧷 参考图数量：{len(image_urls)}",
                f"🎲 随机种：{cache_seed}（仅用于 ComfyUI 缓存控制）",
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
                f"🆔 任务ID：{task_id}",
            ]
            if cost is not None:
                info_lines.append(f"💰 实际消耗：¥{cost}")
            if duration is not None:
                info_lines.append(f"⏳ RH任务耗时：{duration}")
            info_lines.append("🔗 图片链接：")
            info_lines.extend(urls)

            raw_json = json.dumps({"submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return (final_tensor, first_url, "\n".join(info_lines) + "\n\n" + raw_json)

        except Exception as e:
            error_msg = f"❌ 错误：RH 全能图片生成失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            raw_json = json.dumps({"submit": submit_response, "final": final_response}, ensure_ascii=False, indent=2)
            return (create_blank_tensor(), "", error_msg + "\n\n" + raw_json)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHAllImageNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🌈RH全能图片@炮老师的小课堂",
}
