"""
APImart Gemini 图像生成节点

使用 APImart /v1/images/generations 提交 Gemini 图像任务，并通过 /v1/tasks/{task_id} 轮询取图。
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


NODE_NAME = "DapaoGeminiImageAPImartNode"


class DapaoGeminiImageAPImartNode:
    _SIZE_CHOICES = [
        "1:1",
        "3:2",
        "2:3",
        "4:3",
        "3:4",
        "16:9",
        "9:16",
        "5:4",
        "4:5",
        "21:9",
        "1:4",
        "4:1",
        "1:8",
        "8:1",
    ]

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "填入 APImart Bearer Token",
                    "tooltip": "APImart 平台 API Key；自定义平台也使用对应 API Key。"
                }),
                "🤖 模型": (["gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview"], {
                    "default": "gemini-3.1-flash-image-preview",
                    "tooltip": "Gemini 3.1 Flash Image 或 Gemini 3 Pro Image。"
                }),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "赛博朋克风格的城市夜景，霓虹灯闪烁",
                    "placeholder": "请输入图像描述或图生图编辑要求..."
                }),
                "📐 画面比例": (cls._SIZE_CHOICES, {
                    "default": "1:1",
                    "tooltip": "按 APImart Gemini 文档保留支持比例。"
                }),
                "🧩 分辨率": (["0.5K", "1K", "2K", "4K"], {
                    "default": "1K",
                    "tooltip": "0.5K 预览，1K 标准，2K 高清，4K 更慢且费用更高。"
                }),
                "🖼️ 图片数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "step": 1,
                    "tooltip": "Gemini 图像生成支持 1-4 张。"
                }),
                "🎲 随机种": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": "randomize",
                    "tooltip": "只用于 ComfyUI 缓存控制；不会发送给 APImart。"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE", {"tooltip": "可选：接入后自动走图生图。"}),
                "🖼️ 图像2": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像3": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像4": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🔎 Google文字搜索": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "仅 Gemini Flash 文档明确支持，适合需要真实信息的图片。"
                }),
                "🖼️ Google图片搜索": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "需要配合 Google文字搜索；仅 Gemini Flash 文档明确支持。"
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
    DESCRIPTION = "APImart Gemini 图像生成：文生图、4图图生图 @炮老师的小课堂"
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
    def _get_base_url(custom_api_url):
        base_url = (custom_api_url or "").strip() or "https://api.apimart.ai"
        return base_url.rstrip("/")

    @staticmethod
    def _headers(api_key):
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/APImartGeminiImage",
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
            raise RuntimeError(f"Gemini 图像请求参数错误 400：请检查模型、比例、分辨率、提示词或参考图。接口返回：{message}")
        if status == 401:
            raise RuntimeError(f"Gemini 图像认证失败 401：API密钥无效或未填写正确。接口返回：{message}")
        if status == 402:
            raise RuntimeError(f"Gemini 图像余额不足 402：账户余额不足，请充值后再试。接口返回：{message}")
        if status == 403:
            raise RuntimeError(f"Gemini 图像权限不足 403：没有权限访问该模型或资源。接口返回：{message}")
        if status == 429:
            raise RuntimeError(f"Gemini 图像请求过频 429：请降低频率后重试。接口返回：{message}")
        if status >= 500:
            raise RuntimeError(f"Gemini 图像服务异常 {status}：服务器或上游暂时不可用。接口返回：{message}")
        raise RuntimeError(f"Gemini 图像请求失败 {status}：{message}")

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
                raise RuntimeError(f"Gemini 图像接口返回内容不是 JSON：{e}")
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

        for _ in range(1, max_poll_attempts + 1):
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
                    raise RuntimeError(f"Gemini 图像任务完成，但没有找到图片 URL。任务返回：{json.dumps(task_result, ensure_ascii=False)[:1000]}")
                if pbar:
                    pbar.update_absolute(100)
                return urls, task_result

            if status in ("failed", "FAILURE", "failure"):
                raise RuntimeError(f"Gemini 图像任务失败：{error or json.dumps(task_result, ensure_ascii=False)[:1000]}")

        raise RuntimeError(f"Gemini 图像轮询超过 {max_poll_attempts} 次仍未完成，请稍后用任务ID查询：{task_id}")

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
        model = kwargs.get("🤖 模型", "gemini-3.1-flash-image-preview")
        custom_model_id = kwargs.get("🤖 自定义模型ID", "").strip()
        final_model = custom_model_id or model
        prompt = kwargs.get("📝 提示词", "").strip()
        size = kwargs.get("📐 画面比例", "1:1")
        resolution = kwargs.get("🧩 分辨率", "1K")
        n = int(kwargs.get("🖼️ 图片数量", 1))
        cache_seed = int(kwargs.get("🎲 随机种", 0))
        google_search = bool(kwargs.get("🔎 Google文字搜索", False))
        google_image_search = bool(kwargs.get("🖼️ Google图片搜索", False))
        max_poll_attempts = int(kwargs.get("🔁 最大轮询次数", 60))
        poll_interval = int(kwargs.get("⏱️ 轮询间隔", 5))
        retry_count = int(kwargs.get("♻️ 最大重试次数", 2))
        timeout = int(kwargs.get("⌛ 初始超时", 180))
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        image_inputs = [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 5)]

        if not api_key:
            raise ValueError("请填写 🔑 API密钥。")
        if not prompt:
            raise ValueError("请填写 📝 提示词，不能为空。")
        if google_image_search and not google_search:
            raise ValueError("启用 🖼️ Google图片搜索 时，需要同时启用 🔎 Google文字搜索。")

        image_urls = []
        for image in image_inputs:
            if image is not None:
                image_urls.append(self._tensor_to_data_uri(image))

        mode_text = "🎨 文生图" if not image_urls else "🖼️ 图生图"
        payload = {
            "model": final_model,
            "prompt": prompt,
            "size": size,
            "resolution": resolution,
            "n": n,
        }
        if image_urls:
            payload["image_urls"] = image_urls
        if google_search:
            payload["google_search"] = True
        if google_image_search:
            payload["google_image_search"] = True

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
                raise RuntimeError("Gemini 图像任务完成，但没有得到图片。")
            combined = tensors[0] if len(tensors) == 1 else torch.cat(tensors, dim=0)
        except requests.exceptions.Timeout as e:
            raise RuntimeError(f"Gemini 图像请求超时：{timeout} 秒内没有响应，请增大超时时间或稍后重试。详情：{e}")
        except requests.exceptions.ConnectionError as e:
            raise RuntimeError(f"Gemini 图像网络连接失败：请检查网络、代理或防火墙。详情：{e}")
        except Exception:
            traceback.print_exc()
            raise

        elapsed_time = time.time() - start_time
        first_url = urls[0] if urls else ""
        info = [
            "✅ Gemini 图像生成任务完成",
            f"🔀 模式：{mode_text}",
            f"🔁 返回方式：{result_mode}",
            f"🤖 模型：{final_model}",
            f"📐 画面比例：{size}",
            f"🧩 分辨率：{resolution}",
            f"🖼️ 图片数量：{len(urls)}",
            f"🎲 随机种：{cache_seed}（仅用于 ComfyUI 缓存控制）",
            f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
        ]
        if task_id:
            info.append(f"🆔 任务ID：{task_id}")
        if image_urls:
            info.append(f"🧷 参考图数量：{len(image_urls)}")
        if google_search:
            info.append("🔎 已启用 Google文字搜索")
        if google_image_search:
            info.append("🖼️ 已启用 Google图片搜索")
        info.append("🔗 图片链接：")
        info.extend(urls)

        raw_json = json.dumps({"submit": submit_result, "task": task_result}, ensure_ascii=False, indent=2)
        return (combined, first_url, "\n".join(info) + "\n\n" + raw_json)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoGeminiImageAPImartNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🐥Gemini图像生成@炮老师的小课堂",
}
