"""
APImart GPT image-2 图像生成节点

使用 APImart /v1/images/generations 提交任务，并通过 /v1/tasks/{task_id} 轮询取图。
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


NODE_NAME = "DapaoGPTImage2APImartNode"


class DapaoGPTImage2APImartNode:
    _SIZE_CHOICES = [
        "auto",
        "1:1",
        "3:2",
        "2:3",
        "4:3",
        "3:4",
        "5:4",
        "4:5",
        "16:9",
        "9:16",
        "2:1",
        "1:2",
        "3:1",
        "1:3",
        "21:9",
        "9:21",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "填入 APImart Bearer Token",
                    "tooltip": "APImart 平台 API Key，不会写入文件。"
                }),
                "🤖 模型": (["gpt-image-2-official", "gpt-image-2"], {
                    "default": "gpt-image-2-official",
                    "tooltip": "official 为官方渠道；gpt-image-2 为 APImart image-2 渠道。"
                }),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "一只橘猫坐在窗台上看夕阳，水彩画风格",
                    "placeholder": "请输入图像描述或编辑要求..."
                }),
                "📐 画面比例": (cls._SIZE_CHOICES, {
                    "default": "auto",
                    "tooltip": "保留 APImart 文档支持的 auto + 15 种比例，避免选到不支持的比例。"
                }),
                "🧩 分辨率": (["1k", "2k", "4k"], {
                    "default": "1k",
                    "tooltip": "1k 省钱，2k 高清，4k 更慢且费用更高。"
                }),
                "🖼️ 图片数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "step": 1,
                    "tooltip": "gpt-image-2-official 支持 1-4；gpt-image-2 按文档仅支持 1。"
                }),
                "🎨 画质": (["auto", "low", "medium", "high"], {"default": "auto"}),
                "🌈 背景": (["auto", "opaque", "transparent"], {
                    "default": "auto",
                    "tooltip": "gpt-image-2-official 不支持透明背景，平台可能自动降级。"
                }),
                "📦 输出格式": (["png", "jpeg", "webp"], {"default": "png"}),
                "🛡️ 审核强度": (["auto", "low"], {"default": "auto"}),
                "🎲 随机种": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": "randomize",
                    "tooltip": "只用于 ComfyUI 判断是否重新执行；不会发送给 APImart。固定不变会复用缓存，随机变化会重新请求。"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE", {"tooltip": "可选：接入后自动走图生图；蒙版只作用于图像1。"}),
                "🎭 蒙版": ("MASK", {"tooltip": "可选：必须搭配图像1，用于局部重绘。"}),
                "🖼️ 图像2": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像3": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像4": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🗜️ 压缩质量": ("INT", {
                    "default": 100,
                    "min": 0,
                    "max": 100,
                    "step": 1,
                    "tooltip": "仅 jpeg/webp 有效。"
                }),
                "🔁 最大轮询次数": ("INT", {"default": 60, "min": 1, "max": 300, "step": 1}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 3, "max": 30, "step": 1}),
                "♻️ 最大重试次数": ("INT", {"default": 2, "min": 0, "max": 5, "step": 1}),
                "⌛ 初始超时": ("INT", {"default": 180, "min": 30, "max": 600, "step": 1}),
                "🤖 自定义模型ID": ("STRING", {
                    "default": "",
                    "placeholder": "留空使用上方模型下拉；填写后优先使用这里的模型ID",
                    "tooltip": "用于兼容 APImart 协议的其他平台/模型，只覆盖 payload 里的 model 字段。"
                }),
                "🔗 自定义API地址": ("STRING", {
                    "default": "",
                    "placeholder": "默认 https://api.apimart.ai；可填写自定义 APImart 兼容地址"
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/🐦‍🔥GPT&gemini&即梦最新稳定🐦‍🔥"
    DESCRIPTION = "APImart GPT image-2：文生图、图生图、图像1蒙版局部重绘 @炮老师小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _pil2tensor(image):
        if image.mode != "RGB":
            image = image.convert("RGB")
        np_image = np.array(image).astype(np.float32) / 255.0
        return torch.from_numpy(np_image).unsqueeze(0)

    @staticmethod
    def _tensor_to_data_uri(image):
        image_np = np.clip(image[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image_np).convert("RGB")
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def _mask_to_data_uri(mask):
        mask_np = np.clip(mask[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        alpha_np = 255 - mask_np
        mask_image = Image.fromarray(mask_np, mode="L").convert("RGBA")
        mask_image.putalpha(Image.fromarray(alpha_np, mode="L"))
        buffer = io.BytesIO()
        mask_image.save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def _get_base_url(custom_api_url):
        base_url = (custom_api_url or "").strip() or "https://api.apimart.ai"
        return base_url.rstrip("/")

    @staticmethod
    def _headers(api_key):
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/APImartGPTImage2",
        }

    @staticmethod
    def _error_message(response):
        text = response.text[:1000]
        try:
            data = response.json()
            error = data.get("error", {}) if isinstance(data, dict) else {}
            if isinstance(error, dict):
                return error.get("message") or error.get("type") or text
            if isinstance(data, dict):
                return data.get("message") or text
        except Exception:
            pass
        return text

    def _raise_for_response(self, response):
        if response.status_code == 200:
            return
        message = self._error_message(response)
        status = response.status_code
        if status == 400:
            raise RuntimeError(f"APImart 参数错误 400：请检查模型、比例、分辨率、提示词或参考图。接口返回：{message}")
        if status == 401:
            raise RuntimeError(f"APImart 认证失败 401：API密钥无效或未填写正确。接口返回：{message}")
        if status == 402:
            raise RuntimeError(f"APImart 余额不足 402：账户余额不足，请充值后再试。接口返回：{message}")
        if status == 403:
            raise RuntimeError(f"APImart 权限不足 403：没有权限访问该模型或资源。接口返回：{message}")
        if status == 429:
            raise RuntimeError(f"APImart 请求过频 429：请降低频率后重试。接口返回：{message}")
        if status >= 500:
            raise RuntimeError(f"APImart 服务异常 {status}：服务器或上游暂时不可用。接口返回：{message}")
        raise RuntimeError(f"APImart 请求失败 {status}：{message}")

    @staticmethod
    def _should_retry(exc):
        if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return True
        text = str(exc)
        return "429" in text or "服务异常" in text or "暂时不可用" in text

    def _request_json_with_retry(self, method, url, headers, payload, timeout, retry_count):
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                if method == "POST":
                    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                else:
                    response = requests.get(url, headers=headers, timeout=timeout)
                self._raise_for_response(response)
                return response.json()
            except json.JSONDecodeError as e:
                raise RuntimeError(f"APImart 返回内容不是 JSON：{e}")
            except Exception as e:
                last_error = e
                if attempt >= retry_count or not self._should_retry(e):
                    raise
                time.sleep(min(2 ** attempt, 8))
        raise last_error

    @staticmethod
    def _extract_task_id(submit_result):
        data = submit_result.get("data") if isinstance(submit_result, dict) else None
        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first.get("task_id") or first.get("id")
        if isinstance(data, dict):
            return data.get("task_id") or data.get("id")
        return submit_result.get("task_id") if isinstance(submit_result, dict) else None

    @staticmethod
    def _extract_image_urls(task_result):
        data = task_result.get("data", {}) if isinstance(task_result, dict) else {}
        result = data.get("result", {}) if isinstance(data, dict) else {}
        images = result.get("images", []) if isinstance(result, dict) else []
        urls = []
        for item in images or []:
            if not isinstance(item, dict):
                continue
            item_url = item.get("url")
            if isinstance(item_url, list):
                urls.extend([url for url in item_url if url])
            elif isinstance(item_url, str) and item_url:
                urls.append(item_url)
        return urls

    @staticmethod
    def _extract_direct_items(result):
        data = result.get("data", []) if isinstance(result, dict) else []
        if isinstance(data, dict):
            data = [data]
        items = []
        for item in data or []:
            if not isinstance(item, dict):
                continue
            item_url = item.get("url")
            b64_data = item.get("b64_json") or item.get("base64")
            if item_url or b64_data:
                items.append(item)
        return items

    @staticmethod
    def _task_status(task_result):
        data = task_result.get("data", {}) if isinstance(task_result, dict) else {}
        if isinstance(data, dict):
            return data.get("status", ""), data.get("progress", 0), data.get("error") or data.get("message") or ""
        return "", 0, ""

    def _poll_task(self, base_url, task_id, headers, timeout, retry_count, max_poll_attempts, poll_interval):
        task_url = f"{base_url}/v1/tasks/{task_id}"
        pbar = comfy.utils.ProgressBar(100) if comfy is not None else None
        if pbar:
            pbar.update_absolute(5)

        for attempt in range(1, max_poll_attempts + 1):
            time.sleep(poll_interval)
            task_result = self._request_json_with_retry("GET", task_url, headers, None, timeout, retry_count)
            status, progress, error = self._task_status(task_result)
            if pbar:
                try:
                    pbar.update_absolute(min(95, int(progress or 0)))
                except Exception:
                    pass

            if status in ("completed", "SUCCESS", "success"):
                urls = self._extract_image_urls(task_result)
                if not urls:
                    raise RuntimeError(f"APImart 任务完成，但没有找到图片 URL。任务返回：{json.dumps(task_result, ensure_ascii=False)[:1000]}")
                if pbar:
                    pbar.update_absolute(100)
                return urls, task_result

            if status in ("failed", "FAILURE", "failure"):
                raise RuntimeError(f"APImart 任务失败：{error or json.dumps(task_result, ensure_ascii=False)[:1000]}")

        raise RuntimeError(f"APImart 轮询超过 {max_poll_attempts} 次仍未完成，请稍后用任务ID查询：{task_id}")

    @staticmethod
    def _download_image(url, timeout):
        response = requests.get(url, timeout=timeout)
        if response.status_code != 200:
            raise RuntimeError(f"图片下载失败，状态码：{response.status_code}，URL：{url}")
        return Image.open(io.BytesIO(response.content)).convert("RGB")

    def _image_from_direct_item(self, item, timeout):
        b64_data = item.get("b64_json") or item.get("base64")
        if b64_data:
            if b64_data.strip().startswith("data:") and "," in b64_data:
                b64_data = b64_data.split(",", 1)[1]
            return Image.open(io.BytesIO(base64.b64decode(b64_data))).convert("RGB")

        item_url = item.get("url")
        if isinstance(item_url, list):
            item_url = item_url[0] if item_url else ""
        if item_url:
            return self._download_image(item_url, timeout)
        raise RuntimeError("同步返回中没有可解析的 url 或 b64_json。")

    @staticmethod
    def _url_from_direct_item(item):
        item_url = item.get("url")
        if isinstance(item_url, list):
            return item_url[0] if item_url else ""
        return item_url or ""

    def generate(self, **kwargs):
        api_key = kwargs.get("🔑 API密钥", "").strip()
        model = kwargs.get("🤖 模型", "gpt-image-2-official")
        custom_model_id = kwargs.get("🤖 自定义模型ID", "").strip()
        final_model = custom_model_id or model
        prompt = kwargs.get("📝 提示词", "").strip()
        size = kwargs.get("📐 画面比例", "auto")
        resolution = kwargs.get("🧩 分辨率", "1k")
        n = int(kwargs.get("🖼️ 图片数量", 1))
        quality = kwargs.get("🎨 画质", "auto")
        background = kwargs.get("🌈 背景", "auto")
        output_format = kwargs.get("📦 输出格式", "png")
        moderation = kwargs.get("🛡️ 审核强度", "auto")
        cache_seed = int(kwargs.get("🎲 随机种", 0))
        output_compression = int(kwargs.get("🗜️ 压缩质量", 100))
        max_poll_attempts = int(kwargs.get("🔁 最大轮询次数", 60))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        retry_count = int(kwargs.get("♻️ 最大重试次数", 2))
        timeout = int(kwargs.get("⌛ 初始超时", 180))
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        image_inputs = [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 5)]
        mask = kwargs.get("🎭 蒙版")

        if not api_key:
            raise ValueError("请填写 🔑 API密钥。")
        if not prompt:
            raise ValueError("请填写 📝 提示词，不能为空。")
        if not custom_model_id and model == "gpt-image-2" and n != 1:
            raise ValueError("gpt-image-2 按 APImart 文档只支持 🖼️ 图片数量 = 1；如需 1-4 张，请选择 gpt-image-2-official。")
        if mask is not None and image_inputs[0] is None:
            raise ValueError("使用 🎭 蒙版 时必须接入 🖼️ 图像1。")
        if mask is not None and image_inputs[0].shape[1:3] != mask.shape[1:3]:
            raise ValueError("🎭 蒙版尺寸必须和 🖼️ 图像1 尺寸一致。")

        image_urls = []
        for image in image_inputs:
            if image is not None:
                image_urls.append(self._tensor_to_data_uri(image))

        mode_text = "🎨 文生图"
        if image_urls:
            mode_text = "🖼️ 图生图"
        if mask is not None:
            mode_text = "🎭 局部重绘"

        payload = {
            "model": final_model,
            "prompt": prompt,
            "size": size,
            "resolution": resolution,
            "quality": quality,
            "background": background,
            "output_format": output_format,
            "moderation": moderation,
            "n": n,
        }
        if output_format in ("jpeg", "webp"):
            payload["output_compression"] = output_compression
        if image_urls:
            payload["image_urls"] = image_urls
        if mask is not None:
            payload["mask_url"] = self._mask_to_data_uri(mask)

        base_url = self._get_base_url(custom_api_url)
        headers = self._headers(api_key)
        start_time = time.time()

        try:
            submit_result = self._request_json_with_retry(
                "POST",
                f"{base_url}/v1/images/generations",
                headers,
                payload,
                timeout,
                retry_count,
            )
            task_id = self._extract_task_id(submit_result)
            direct_items = []
            if task_id:
                urls, task_result = self._poll_task(base_url, task_id, headers, timeout, retry_count, max_poll_attempts, poll_interval)
                tensors = [self._pil2tensor(self._download_image(url, timeout)) for url in urls]
                result_mode = "异步任务"
            else:
                direct_items = self._extract_direct_items(submit_result)
                if not direct_items:
                    raise RuntimeError(f"提交成功但既没有返回 task_id，也没有返回图片 url/b64_json。提交返回：{json.dumps(submit_result, ensure_ascii=False)[:1000]}")
                urls = [self._url_from_direct_item(item) for item in direct_items]
                tensors = [self._pil2tensor(self._image_from_direct_item(item, timeout)) for item in direct_items]
                task_result = submit_result
                result_mode = "同步返回"
            if not tensors:
                raise RuntimeError("任务完成，但没有得到图片。")
            combined = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)
        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"APImart 请求超时：{timeout} 秒内没有响应，请增大超时时间或稍后重试。详情：{e}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"APImart 网络连接失败：请检查网络、代理或防火墙。详情：{e}")
        except Exception:
            traceback.print_exc()
            raise

        elapsed_time = time.time() - start_time
        first_url = urls[0] if urls else ""
        info = [
            "✅ APImart GPT image-2 任务完成",
            f"🔀 模式：{mode_text}",
            f"🤖 模型：{final_model}",
            f"🔁 返回方式：{result_mode}",
            f"📐 画面比例：{size}",
            f"🧩 分辨率：{resolution}",
            f"🖼️ 图片数量：{len(urls)}",
            f"🎲 随机种：{cache_seed}（仅用于 ComfyUI 缓存控制）",
            f"🎨 画质：{quality}",
            f"📦 输出格式：{output_format}",
            f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
        ]
        if task_id:
            info.append(f"🆔 任务ID：{task_id}")
        if image_urls:
            info.append(f"🧷 参考图数量：{len(image_urls)}")
        if mask is not None:
            info.append("🎭 已使用图像1蒙版")
        info.append("🔗 图片链接：")
        info.extend(urls)

        raw_json = json.dumps({"submit": submit_result, "task": task_result}, ensure_ascii=False, indent=2)
        return (combined, first_url, "\n".join(info) + "\n\n" + raw_json)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoGPTImage2APImartNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🐟GPT图像生成image-2@炮老师小课堂",
}
