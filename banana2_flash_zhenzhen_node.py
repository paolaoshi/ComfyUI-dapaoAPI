import torch
import requests
import json
import time
import base64
from PIL import Image
from io import BytesIO
import numpy as np
import comfy.utils


def tensor2pil(image):
    return [Image.fromarray(np.clip(255. * img.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)) for img in image]


def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


class DapaoBanana2FlashZhenzhenNode:
    """
    🙈Banana2Flash贞贞@炮老师的小课堂

    使用 gemini-3.1-flash-image-preview 模型，支持文生图和图像编辑。
    API调用方式参考贞贞API（异步轮询）。

    Time: 2026/2/28 周六 08:41:57
    Author: HeGenAI
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🌐 API线路": (["zhenzhen", "ip", "hk", "us"], {"default": "zhenzhen"}),
                "🔑 API密钥": ("STRING", {"default": "", "multiline": False}),
                "📝 提示词": ("STRING", {"multiline": True, "default": ""}),
                "🎨 生成模式": (["文生图", "图像编辑"], {"default": "文生图"}),
                "🤖 模型版本": (["gemini-3.1-flash-image-preview"], {"default": "gemini-3.1-flash-image-preview"}),
                "📐 宽高比": (["auto", "16:9", "4:3", "4:5", "3:2", "1:1", "2:3", "3:4", "5:4", "9:16", "21:9", "1:4", "4:1", "1:8", "8:1"], {"default": "auto"}),
                "🖼️ 图片分辨率": (["1K", "2K", "4K"], {"default": "2K"}),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647, "control_after_generate": "randomize"}),
                "🖼️ 出图数量": ("INT", {"default": 1, "min": 1, "max": 999999}),
                "🌊 流式输出": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "🔗 自定义API地址": ("STRING", {"default": ""}),
                "🆔 任务ID": ("STRING", {"default": ""}),
                "📦 返回格式": (["url", "b64_json"], {"default": "url"}),
                "🖼️ 参考图1": ("IMAGE",),
                "🖼️ 参考图2": ("IMAGE",),
                "🖼️ 参考图3": ("IMAGE",),
                "🖼️ 参考图4": ("IMAGE",),
                "🖼️ 参考图5": ("IMAGE",),
                "🖼️ 参考图6": ("IMAGE",),
                "🖼️ 参考图7": ("IMAGE",),
                "🖼️ 参考图8": ("IMAGE",),
                "🖼️ 参考图9": ("IMAGE",),
                "🖼️ 参考图10": ("IMAGE",),
                "🖼️ 参考图11": ("IMAGE",),
                "🖼️ 参考图12": ("IMAGE",),
                "🖼️ 参考图13": ("IMAGE",),
                "🖼️ 参考图14": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "🆔 任务ID", "ℹ️ 响应信息")
    FUNCTION = "generate_image"
    CATEGORY = "🤖dapaoAPI/Nano Banana 2"

    def __init__(self):
        self.timeout = 600

    def _get_base_url(self, api_source, custom_api_url):
        mapping = {
            "zhenzhen": "https://ai.t8star.cn",
            "hk": "https://hk-api.gptbest.vip",
            "us": "https://api.gptbest.vip",
            "ip": custom_api_url.strip()
        }
        url = mapping.get(api_source, "")
        if api_source == "ip" and not url:
            return "https://ai.t8star.cn"
        return url

    def get_headers(self, api_key):
        return {"Authorization": f"Bearer {api_key}"}

    def generate_image(self, **kwargs):
        api_source = kwargs.get("🌐 API线路", "zhenzhen")
        api_key = kwargs.get("🔑 API密钥", "")
        prompt = kwargs.get("📝 提示词", "")
        mode = "text2img" if kwargs.get("🎨 生成模式", "文生图") == "文生图" else "img2img"
        model = kwargs.get("🤖 模型版本", "gemini-3.1-flash-image-preview")
        aspect_ratio = kwargs.get("📐 宽高比", "auto")
        image_size = kwargs.get("🖼️ 图片分辨率", "2K")
        seed = kwargs.get("🎲 随机种子", 0)
        n_images = max(1, int(kwargs.get("🖼️ 出图数量", 1)))
        stream_enabled = bool(kwargs.get("🌊 流式输出", False))
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        task_id = kwargs.get("🆔 任务ID", "")
        response_format = kwargs.get("📦 返回格式", "url")

        images = [kwargs.get(f"🖼️ 参考图{i}") for i in range(1, 15)]

        base_url = self._get_base_url(api_source, custom_api_url)

        if not api_key.strip():
            blank = pil2tensor(Image.new('RGB', (512, 512), color='black'))
            return (blank, "", "", json.dumps({"status": "failed", "message": "❌ API Key 为空"}))

        try:
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)

            if task_id.strip():
                return self._query_task_status(base_url, api_key, task_id, pbar)

            combined_tensors, all_urls, task_ids = [], [], []
            first_url, first_task_id = "", ""
            params = {"async": "true"}

            prepared_images = []
            if mode == "img2img":
                for idx, img in enumerate(images):
                    if img is None:
                        continue
                    buf = BytesIO()
                    tensor2pil(img)[0].save(buf, format="PNG")
                    prepared_images.append((f"image_{idx}.png", buf.getvalue()))

            for i in range(n_images):
                pbar.update_absolute(min(30, 10 + int((i / max(1, n_images)) * 20)))

                if mode == "text2img":
                    headers = self.get_headers(api_key)
                    headers["Content-Type"] = "application/json"
                    payload = {"prompt": prompt, "model": model, "aspect_ratio": aspect_ratio, "image_size": image_size, "n": 1}
                    if response_format:
                        payload["response_format"] = response_format
                    if seed > 0:
                        payload["seed"] = seed
                    response = requests.post(f"{base_url}/v1/images/generations", headers=headers, params=params, json=payload, timeout=self.timeout)
                else:
                    headers = self.get_headers(api_key)
                    files = [("image", (name, BytesIO(raw), "image/png")) for name, raw in prepared_images]
                    data = {"prompt": prompt, "model": model, "aspect_ratio": aspect_ratio, "image_size": image_size, "n": 1}
                    if response_format:
                        data["response_format"] = response_format
                    if seed > 0:
                        data["seed"] = str(seed)
                    response = requests.post(f"{base_url}/v1/images/edits", headers=headers, params=params, data=data, files=files, timeout=self.timeout)

                if response.status_code != 200:
                    blank = pil2tensor(Image.new("RGB", (512, 512), color="red"))
                    return (blank, "", "", json.dumps({"status": "failed", "message": f"API Error: {response.status_code} - {response.text}"}))

                result = response.json()

                if "task_id" in result:
                    returned_task_id = result["task_id"]
                    task_ids.append(str(returned_task_id))
                    if not first_task_id:
                        first_task_id = str(returned_task_id)
                    img_tensor, img_url, _, _ = self._poll_task(base_url, api_key, returned_task_id, pbar, final_update=not (stream_enabled and n_images > 1))
                    if isinstance(img_tensor, torch.Tensor) and img_tensor.dim() == 4:
                        combined_tensors.append(img_tensor)
                        if stream_enabled and n_images > 1:
                            pbar.update_absolute(min(99, 30 + int(((i + 1) / max(1, n_images)) * 69)), preview=("PNG", tensor2pil(img_tensor[0:1])[0], None))
                    if img_url:
                        if not first_url:
                            first_url = img_url
                        all_urls.append(img_url)
                elif "data" in result and result["data"]:
                    img_tensor, img_url, _, _ = self._process_success_data(result["data"], f"sync_{i}", pbar)
                    if isinstance(img_tensor, torch.Tensor) and img_tensor.dim() == 4:
                        combined_tensors.append(img_tensor)
                    if img_url:
                        if not first_url:
                            first_url = img_url
                        all_urls.append(img_url)
                else:
                    blank = pil2tensor(Image.new("RGB", (512, 512), color="gray"))
                    return (blank, "", "", json.dumps({"status": "failed", "message": f"未知响应格式: {result}"}))

            if combined_tensors:
                final_tensor = torch.cat(combined_tensors, dim=0)
                pbar.update_absolute(100)
                return (final_tensor, first_url, first_task_id, json.dumps({"status": "success", "images_count": int(final_tensor.shape[0]), "image_url": first_url, "all_urls": all_urls, "task_ids": task_ids}, ensure_ascii=False))

            blank = pil2tensor(Image.new("RGB", (512, 512), color="white"))
            return (blank, "", "", json.dumps({"status": "empty", "message": "No valid images found"}))

        except Exception as e:
            import traceback
            traceback.print_exc()
            blank = pil2tensor(Image.new('RGB', (512, 512), color='red'))
            return (blank, "", "", json.dumps({"status": "error", "message": str(e)}))

    def _poll_task(self, base_url, api_key, task_id, pbar, final_update=True):
        """轮询异步任务状态"""
        for attempt in range(60):
            time.sleep(5)
            try:
                headers = self.get_headers(api_key)
                headers["Content-Type"] = "application/json"
                response = requests.get(f"{base_url}/v1/images/tasks/{task_id}", headers=headers, timeout=self.timeout)
                if response.status_code != 200:
                    continue
                result = response.json()
                actual_status, actual_data = "unknown", None
                if "data" in result and isinstance(result["data"], dict):
                    actual_status = result["data"].get("status", "unknown")
                    actual_data = result["data"].get("data")
                print(f"[dapaoAPI] 轮询 ({attempt+1}/60) 状态: {actual_status}")
                if actual_status in ["completed", "success", "done", "finished", "SUCCESS"]:
                    if final_update:
                        pbar.update_absolute(100)
                    return self._process_success_data(actual_data, task_id, pbar)
                if actual_status in ["failed", "error", "FAILURE"]:
                    blank = pil2tensor(Image.new('RGB', (512, 512), color='red'))
                    return (blank, "", task_id, json.dumps({"status": "failed", "task_id": task_id}))
            except Exception as e:
                print(f"[dapaoAPI] 轮询异常: {e}")
        blank = pil2tensor(Image.new('RGB', (512, 512), color='yellow'))
        return (blank, "", task_id, json.dumps({"status": "timeout", "task_id": task_id}))

    def _query_task_status(self, base_url, api_key, task_id, pbar):
        """查询已有任务状态"""
        try:
            headers = self.get_headers(api_key)
            headers["Content-Type"] = "application/json"
            response = requests.get(f"{base_url}/v1/images/tasks/{task_id}", headers=headers, timeout=self.timeout)
            pbar.update_absolute(50)
            if response.status_code != 200:
                blank = pil2tensor(Image.new('RGB', (1024, 1024), color='white'))
                return (blank, "", task_id, json.dumps({"status": "query_failed", "message": f"{response.status_code} - {response.text}"}))
            result = response.json()
            actual_status, actual_data = "unknown", None
            if "data" in result and isinstance(result["data"], dict):
                actual_status = result["data"].get("status", "unknown")
                actual_data = result["data"].get("data")
            if actual_status in ["completed", "success", "done", "finished", "SUCCESS"]:
                return self._process_success_data(actual_data, task_id, pbar)
            blank = pil2tensor(Image.new('RGB', (512, 512), color='lightgray'))
            return (blank, "", task_id, json.dumps({"status": actual_status, "task_id": task_id}))
        except Exception as e:
            blank = pil2tensor(Image.new('RGB', (512, 512), color='white'))
            return (blank, "", task_id, json.dumps({"status": "error", "message": str(e)}))

    def _process_success_data(self, data, task_id, pbar):
        """处理成功返回的图片数据"""
        if not data:
            blank = pil2tensor(Image.new('RGB', (512, 512), color='white'))
            return (blank, "", task_id, json.dumps({"status": "failed", "message": "No data"}))

        items = data.get("data", []) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = [items]

        tensors, urls = [], []
        for item in items:
            try:
                if "b64_json" in item and item["b64_json"]:
                    buf = BytesIO(base64.b64decode(item["b64_json"]))
                    img = Image.open(buf)
                    buf.seek(0)
                    img = Image.open(buf)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    tensors.append(pil2tensor(img))
                elif "url" in item and item["url"]:
                    url = item["url"]
                    urls.append(url)
                    r = requests.get(url, timeout=self.timeout)
                    r.raise_for_status()
                    buf = BytesIO(r.content)
                    img = Image.open(buf)
                    buf.seek(0)
                    img = Image.open(buf)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    tensors.append(pil2tensor(img))
            except Exception as e:
                print(f"[dapaoAPI] 处理图片异常: {e}")

        if tensors:
            combined = torch.cat(tensors, dim=0)
            first_url = urls[0] if urls else ""
            pbar.update_absolute(100)
            return (combined, first_url, task_id, json.dumps({"status": "success", "task_id": task_id, "images_count": len(tensors), "image_url": first_url, "all_urls": urls}))

        blank = pil2tensor(Image.new('RGB', (512, 512), color='white'))
        return (blank, "", task_id, json.dumps({"status": "failed", "message": "No valid images"}))


NODE_CLASS_MAPPINGS = {
    "DapaoBanana2FlashZhenzhenNode": DapaoBanana2FlashZhenzhenNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoBanana2FlashZhenzhenNode": "🙈Banana2Flash贞贞@炮老师的小课堂"
}
