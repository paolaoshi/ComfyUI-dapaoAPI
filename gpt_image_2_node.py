import math
import torch
import requests
import json
import time
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import comfy.utils
from comfy.utils import common_upscale


def downscale_input(image):
    samples = image.movedim(-1, 1)
    total_pixels = int(1536 * 1024)
    scale_by = math.sqrt(total_pixels / (samples.shape[3] * samples.shape[2]))
    if scale_by >= 1:
        return image
    width = round(samples.shape[3] * scale_by)
    height = round(samples.shape[2] * scale_by)
    scaled = common_upscale(samples, width, height, "lanczos", "disabled")
    return scaled.movedim(1, -1)


def tensor2pil(image):
    return [Image.fromarray(np.clip(255.0 * img.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)) for img in image]


def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


class DapaoGPTImage2Node:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🌐 API线路": (["柏拉图", "zhenzhen", "hk", "us", "ip"], {
                    "default": "柏拉图",
                    "tooltip": "选择 API 线路：柏拉图 / zhenzhen / hk / us / ip(自定义地址)"
                }),
                "📝 模式": (["文生图", "图像编辑"], {"default": "文生图"}),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "输入你的提示词或改图要求..."
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入 API Key"
                }),
                "🤖 模型": (["gpt-image-2"], {"default": "gpt-image-2"}),
                "🎨 画质": (["auto", "high", "medium", "low"], {"default": "auto"}),
                "📐 尺寸": (["auto", "1024x1024", "1536x1024", "1024x1536"], {"default": "auto"}),
                "🌈 背景": (["auto", "transparent", "opaque"], {"default": "auto"}),
                "🧲 参考强度": (["auto", "high"], {"default": "high"}),
                "📦 输出格式": (["png", "jpeg", "webp"], {"default": "png"}),
                "🛡️ 审核强度": (["auto", "low"], {"default": "auto"}),
                "🖼️ 图片数量": ("INT", {"default": 1, "min": 1, "max": 4}),
                "🧾 返回格式": (["url", "b64_json"], {"default": "url"}),
                "🎲 种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "control_after_generate": "randomize"
                }),
                "⏱️ 图片下载超时": ("INT", {
                    "default": 600,
                    "min": 60,
                    "max": 1200,
                    "step": 10
                }),
            },
            "optional": {
                "🆔 任务ID": ("STRING", {"default": ""}),
                "🔗 自定义API地址": ("STRING", {
                    "default": "",
                    "placeholder": "当 API线路 选 ip 时填写完整地址"
                }),
                "🖼️ 参考图1": ("IMAGE",),
                "🖼️ 参考图2": ("IMAGE",),
                "🖼️ 参考图3": ("IMAGE",),
                "🖼️ 参考图4": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "🆔 任务ID", "📋 响应信息")
    FUNCTION = "process"
    CATEGORY = "🤖dapaoAPI/GPT"
    DESCRIPTION = "GPT Image 2 图像生成/编辑 @炮老师的小课堂 (v2026-s2a)"

    def __init__(self):
        self.timeout = 900
        self.image_download_timeout = 600

    def _get_base_url(self, api_source, custom_api_url):
        mapping = {
            "柏拉图": "https://api.bltcy.ai",
            "zhenzhen": "https://ai.t8star.cn",
            "hk": "https://hk-api.gptbest.vip",
            "us": "https://api.gptbest.vip",
            "ip": (custom_api_url or "").strip(),
        }
        url = mapping.get(api_source, "")
        if api_source == "ip" and not url:
            print("[dapaoAPI] ⚠️ 选择了 ip 线路但未填写自定义API地址，将默认使用柏拉图")
            return "https://api.bltcy.ai"
        return url

    def _get_headers(self, api_key, is_json=False):
        headers = {"Authorization": f"Bearer {api_key}"}
        if is_json:
            headers["Content-Type"] = "application/json"
        return headers

    def _download_image_bytes(self, url, timeout=None):
        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        }
        response = requests.get(url, headers=headers, timeout=timeout or self.image_download_timeout)
        response.raise_for_status()
        return response.content

    def _download_image_tensor(self, url, timeout=None):
        image_bytes = self._download_image_bytes(url, timeout)
        image = Image.open(BytesIO(image_bytes))
        if image.mode != "RGB":
            image = image.convert("RGB")
        return pil2tensor(image)

    def _prepare_image_file(self, image_tensor, index):
        scaled_image = downscale_input(image_tensor[0:1])
        pil_image = tensor2pil(scaled_image)[0]
        if pil_image.mode not in ["RGBA", "RGB"]:
            pil_image = pil_image.convert("RGBA")
        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        return ("image", (f"image_{index}.png", buffer, "image/png"))

    def _resolve_img2img_size(self, size, input_images):
        if size != "auto":
            return size
        first_image = next((img for img in input_images if img is not None), None)
        if first_image is None:
            return size
        pil_image = tensor2pil(first_image)[0]
        width, height = pil_image.size
        if height > width:
            return "1024x1536"
        if width > height:
            return "1536x1024"
        return "1024x1024"

    def _build_summary(self, api_source, mode, model, quality, size, background, input_fidelity, output_format, moderation, n, seed):
        return {
            "线路": api_source,
            "模式": mode,
            "模型": model,
            "画质": quality,
            "尺寸": size,
            "背景": background,
            "参考强度": input_fidelity if mode == "img2img" else "-",
            "输出格式": output_format,
            "审核强度": moderation,
            "图片数量": n,
            "种子": seed if seed > 0 else "auto",
        }

    def _blank_result(self, message, task_id=""):
        blank_image = Image.new("RGB", (1024, 1024), color="white")
        return (pil2tensor(blank_image), "", task_id, json.dumps(message, ensure_ascii=False))

    def _extract_status_and_data(self, result):
        status = result.get("status", "unknown") if isinstance(result, dict) else "unknown"
        final_data = result.get("data") if isinstance(result, dict) else None
        if isinstance(final_data, dict):
            status = final_data.get("status") or status
            if "data" in final_data:
                final_data = final_data.get("data")
        return status, final_data

    def _collect_image_items(self, data):
        items = []
        seen_urls = set()
        seen_b64 = set()

        def walk(node):
            if isinstance(node, dict):
                if node.get("b64_json"):
                    b64_value = node.get("b64_json")
                    if b64_value not in seen_b64:
                        seen_b64.add(b64_value)
                        items.append(node)
                    return
                if node.get("url"):
                    url_value = node.get("url")
                    if url_value not in seen_urls:
                        seen_urls.add(url_value)
                        items.append(node)
                    return
                for key in ["data", "images", "results", "output", "result"]:
                    if key in node:
                        walk(node.get(key))
                for value in node.values():
                    if isinstance(value, (dict, list)):
                        walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(data)
        return items

    def _process_image_items(self, items):
        generated_tensors = []
        image_urls = []
        data_items = self._collect_image_items(items)

        for item in data_items:
            try:
                if not isinstance(item, dict):
                    continue
                if item.get("b64_json"):
                    image_data = base64.b64decode(item["b64_json"])
                    image = Image.open(BytesIO(image_data))
                    if image.mode != "RGB":
                        image = image.convert("RGB")
                    generated_tensors.append(pil2tensor(image))
                elif item.get("url"):
                    image_url = item["url"]
                    image_urls.append(image_url)
                    generated_tensors.append(self._download_image_tensor(image_url))
            except Exception as e:
                print(f"[dapaoAPI] 处理返回图片失败: {e}")

        return generated_tensors, image_urls

    def _finalize_success(self, items, task_id, response_info, pbar):
        generated_tensors, image_urls = self._process_image_items(items)
        if not generated_tensors:
            return self._blank_result({
                "status": "failed",
                "task_id": task_id,
                "message": "接口返回成功，但未解析到图片数据",
                "raw_data": items,
                **response_info,
            }, task_id)

        combined_tensor = torch.cat(generated_tensors, dim=0)
        first_image_url = image_urls[0] if image_urls else ""
        pbar.update_absolute(100)
        return (
            combined_tensor,
            first_image_url,
            task_id,
            json.dumps({
                "status": "success",
                "task_id": task_id,
                "images_count": len(generated_tensors),
                "image_url": first_image_url,
                "all_urls": image_urls,
                **response_info,
            }, ensure_ascii=False),
        )

    def _query_task_status(self, base_url, api_key, task_id, response_info, pbar):
        try:
            response = requests.get(
                f"{base_url}/v1/images/tasks/{task_id}",
                headers=self._get_headers(api_key, is_json=True),
                timeout=self.timeout,
            )
            pbar.update_absolute(50)
            if response.status_code != 200:
                return self._blank_result({
                    "status": "query_failed",
                    "task_id": task_id,
                    "message": f"查询失败: {response.status_code} - {response.text[:1000]}",
                    **response_info,
                }, task_id)

            result = response.json()
            status, final_data = self._extract_status_and_data(result)
            print(f"[dapaoAPI] GPT Image 2 查询状态: {status}")

            if status in ["completed", "success", "done", "finished", "SUCCESS"]:
                return self._finalize_success(final_data, task_id, response_info, pbar)

            if status in ["processing", "pending", "in_progress", "NOT_START", "IN_PROGRESS"]:
                pbar.update_absolute(100)
                return self._blank_result({
                    "status": status,
                    "task_id": task_id,
                    "message": "任务仍在处理中，请稍后再次查询。",
                    **response_info,
                }, task_id)

            if status in ["failed", "error", "FAILURE"]:
                return self._blank_result({
                    "status": "failed",
                    "task_id": task_id,
                    "message": result.get("error") or result.get("message") or "任务失败",
                    **response_info,
                }, task_id)

            return self._blank_result({
                "status": status,
                "task_id": task_id,
                "message": "未识别的任务状态",
                "response": result,
                **response_info,
            }, task_id)
        except Exception as e:
            return self._blank_result({
                "status": "query_failed",
                "task_id": task_id,
                "message": f"查询任务异常: {str(e)}",
                **response_info,
            }, task_id)

    def _poll_task(self, base_url, api_key, task_id, response_info, pbar):
        max_attempts = 60
        for attempt in range(max_attempts):
            time.sleep(5)
            try:
                response = requests.get(
                    f"{base_url}/v1/images/tasks/{task_id}",
                    headers=self._get_headers(api_key, is_json=True),
                    timeout=self.timeout,
                )
                if response.status_code != 200:
                    continue

                result = response.json()
                status, final_data = self._extract_status_and_data(result)
                print(f"[dapaoAPI] GPT Image 2 轮询状态: {status}")
                pbar.update_absolute(min(90, 40 + (attempt + 1) * 50 // max_attempts))

                if status in ["completed", "success", "done", "finished", "SUCCESS"]:
                    return self._finalize_success(final_data, task_id, response_info, pbar)

                if status in ["failed", "error", "FAILURE"]:
                    return self._blank_result({
                        "status": "failed",
                        "task_id": task_id,
                        "message": result.get("error") or result.get("message") or "任务失败",
                        **response_info,
                    }, task_id)
            except Exception as e:
                print(f"[dapaoAPI] GPT Image 2 轮询异常: {e}")

        return self._blank_result({
            "status": "timeout",
            "task_id": task_id,
            "message": "任务轮询超时，请使用任务ID稍后再次查询。",
            **response_info,
        }, task_id)

    def process(self, **kwargs):
        api_source = kwargs.get("🌐 API线路", "柏拉图")
        mode_label = kwargs.get("📝 模式", "文生图")
        prompt = kwargs.get("📝 提示词", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model = kwargs.get("🤖 模型", "gpt-image-2")
        quality = kwargs.get("🎨 画质", "auto")
        size = kwargs.get("📐 尺寸", "auto")
        background = kwargs.get("🌈 背景", "auto")
        input_fidelity = kwargs.get("🧲 参考强度", "high")
        output_format = kwargs.get("📦 输出格式", "png")
        moderation = kwargs.get("🛡️ 审核强度", "auto")
        n = int(kwargs.get("🖼️ 图片数量", 1))
        response_format = kwargs.get("🧾 返回格式", "url")
        seed = kwargs.get("🎲 种子", 0)
        task_id = (kwargs.get("🆔 任务ID", "") or "").strip()
        self.image_download_timeout = int(kwargs.get("⏱️ 图片下载超时", 600))
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        input_images = [kwargs.get(f"🖼️ 参考图{i}") for i in range(1, 5)]

        if not api_key.strip():
            return self._blank_result({"status": "failed", "message": "API密钥为空，请填写后再试"})

        base_url = self._get_base_url(api_source, custom_api_url)
        has_input_images = any(img is not None for img in input_images)
        mode = "img2img" if mode_label == "图像编辑" else "text2img"
        if mode == "img2img" and not has_input_images:
            return self._blank_result({
                "status": "failed",
                "message": "当前选择的是图像编辑模式，请至少连接一张参考图",
                "线路": api_source,
                "模式": mode,
            })
        request_size = self._resolve_img2img_size(size, input_images) if mode == "img2img" else size
        response_info = self._build_summary(
            api_source, mode, model, quality, request_size, background, input_fidelity, output_format, moderation, n, seed
        )

        try:
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)

            if task_id:
                return self._query_task_status(base_url, api_key, task_id, response_info, pbar)

            if mode == "text2img":
                payload = {
                    "prompt": prompt,
                    "model": model,
                    "quality": quality,
                    "size": request_size,
                    "background": background,
                    "output_format": output_format,
                    "moderation": moderation,
                    "n": n,
                    "response_format": response_format,
                }
                if seed > 0:
                    payload["seed"] = seed

                response = requests.post(
                    f"{base_url}/v1/images/generations",
                    headers=self._get_headers(api_key, is_json=True),
                    params={"async": "true"},
                    json=payload,
                    timeout=self.timeout,
                )
            else:
                files = []
                for index, image in enumerate(input_images, start=1):
                    if image is not None:
                        files.append(self._prepare_image_file(image, index))

                data = {
                    "prompt": prompt,
                    "model": model,
                    "quality": quality,
                    "size": request_size,
                    "background": background,
                    "output_format": output_format,
                    "moderation": moderation,
                    "n": str(n),
                    "response_format": response_format,
                }
                if input_fidelity != "auto":
                    data["input_fidelity"] = input_fidelity
                if seed > 0:
                    data["seed"] = str(seed)

                print(f"[dapaoAPI] GPT Image 2 图生图提交: size={request_size}, images={len(files)}, input_fidelity={data.get('input_fidelity', 'auto')}")

                response = requests.post(
                    f"{base_url}/v1/images/edits",
                    headers=self._get_headers(api_key),
                    params={"async": "true"},
                    data=data,
                    files=files,
                    timeout=self.timeout,
                )

            pbar.update_absolute(30)

            if response.status_code != 200:
                return self._blank_result({
                    "status": "failed",
                    "message": f"API请求失败: {response.status_code} - {response.text[:1000]}",
                    **response_info,
                })

            result = response.json()
            print(f"[dapaoAPI] GPT Image 2 提交响应: {json.dumps(result, ensure_ascii=False)[:1000]}")

            if result.get("task_id"):
                returned_task_id = str(result["task_id"])
                pbar.update_absolute(40)
                return self._poll_task(base_url, api_key, returned_task_id, response_info, pbar)

            if result.get("data"):
                sync_task_id = result.get("id", "sync_result")
                return self._finalize_success(result.get("data"), str(sync_task_id), response_info, pbar)

            return self._blank_result({
                "status": "failed",
                "message": "未识别的返回格式",
                "response": result,
                **response_info,
            })
        except Exception as e:
            print(f"[dapaoAPI] GPT Image 2 执行异常: {e}")
            return self._blank_result({
                "status": "failed",
                "message": f"执行失败: {str(e)}",
                **response_info,
            })


NODE_CLASS_MAPPINGS = {
    "🙅GPT_image_2_异步@炮老师的小课堂": DapaoGPTImage2Node,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "🙅GPT_image_2_异步@炮老师的小课堂": "🙅GPT_image_2_异步@炮老师的小课堂",
}
