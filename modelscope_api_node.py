import base64
import io
import json
import os
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import numpy as np
import requests
import torch
from PIL import Image


def _pil2tensor(image: Image.Image) -> torch.Tensor:
    if image.mode != "RGB":
        image = image.convert("RGB")
    np_image = np.array(image).astype(np.float32) / 255.0
    tensor = torch.from_numpy(np_image).unsqueeze(0)
    return tensor


def _tensor2pil(tensor: torch.Tensor) -> Image.Image:
    if len(tensor.shape) == 4:
        tensor = tensor[0]
    np_image = tensor.detach().cpu().numpy()
    np_image = np.clip(np_image, 0, 1)
    np_image = (np_image * 255).astype(np.uint8)
    return Image.fromarray(np_image)


def _blank_image_tensor(color: str = "white", size: int = 512) -> torch.Tensor:
    return _pil2tensor(Image.new("RGB", (size, size), color=color))


def _load_local_config() -> Dict[str, Any]:
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        return {}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        return {}
    return {}


def _get_modelscope_token(token_override: str) -> Optional[str]:
    if token_override and token_override.strip():
        return token_override.strip()

    config = _load_local_config()
    for key in ["modelscope_token", "modelscope_api_key", "api_key", "token"]:
        val = config.get(key)
        if isinstance(val, str) and val.strip():
            return val.strip()

    for env_key in ["MODELSCOPE_SDK_TOKEN", "MODELSCOPE_TOKEN", "MODELSCOPE_API_KEY"]:
        val = os.environ.get(env_key)
        if val and val.strip():
            return val.strip()

    return None


def _normalize_base_url(base_url: str) -> str:
    base_url = (base_url or "").strip()
    if not base_url:
        return "https://api-inference.modelscope.cn/v1"
    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        return base_url
    if base_url.startswith("https://api-inference.modelscope.cn") or base_url.startswith("http://api-inference.modelscope.cn"):
        return f"{base_url}/v1"
    return base_url


def _encode_image_tensor_to_data_url(image_tensor: torch.Tensor) -> str:
    pil_img = _tensor2pil(image_tensor)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="PNG")
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def _encode_image_tensor_to_jpeg_data_url(image_tensor: torch.Tensor, quality: int = 85) -> str:
    pil_img = _tensor2pil(image_tensor)
    buffer = io.BytesIO()
    pil_img.save(buffer, format="JPEG", quality=int(quality))
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def _post_json(url: str, headers: Dict[str, str], payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
    raw_text = resp.text or ""
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code}: {raw_text[:2000]}")
    try:
        data = resp.json()
    except Exception:
        raise RuntimeError(f"HTTP {resp.status_code} 非JSON响应: {raw_text[:2000]}")
    if not isinstance(data, dict):
        raise RuntimeError("API 返回不是 JSON 对象")
    return data


def _get_json(url: str, headers: Dict[str, str], timeout: int) -> Any:
    resp = requests.get(url, headers=headers, timeout=timeout)
    raw_text = resp.text or ""
    if not resp.ok:
        raise RuntimeError(f"HTTP {resp.status_code}: {raw_text[:2000]}")
    try:
        return resp.json()
    except Exception:
        raise RuntimeError(f"HTTP {resp.status_code} 非JSON响应: {raw_text[:2000]}")


def _call_chat_completions(
    *,
    url: str,
    headers: Dict[str, str],
    payload: Dict[str, Any],
    timeout: int,
) -> Dict[str, Any]:
    try:
        return _post_json(url, headers=headers, payload=payload, timeout=timeout)
    except Exception as e:
        if "HTTP 400" not in str(e):
            raise

        minimal_payload = {"model": payload.get("model"), "messages": payload.get("messages")}
        return _post_json(url, headers=headers, payload=minimal_payload, timeout=timeout)


class DapaoModelScopeListModels:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 SDK Token": ("STRING", {"default": "", "multiline": False}),
                "🌐 Base URL": ("STRING", {"default": "https://api-inference.modelscope.cn/v1", "multiline": False}),
                "⏱️ 超时时间": ("INT", {"default": 60, "min": 1, "max": 300}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("📃 模型列表", "raw_json")
    FUNCTION = "list_models"
    CATEGORY = "🤖dapaoAPI/魔塔API"

    def list_models(self, **kwargs) -> Tuple[str, str]:
        token = _get_modelscope_token(kwargs.get("🔑 SDK Token", ""))
        if not token:
            return ("❌ 缺少 SDK Token：请在节点输入或本地 config.json / 环境变量中配置", json.dumps({"error": "missing_token"}, ensure_ascii=False))

        base_url = _normalize_base_url(kwargs.get("🌐 Base URL", ""))
        timeout = int(kwargs.get("⏱️ 超时时间", 60))
        url = f"{base_url}/models"
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        try:
            data = _get_json(url, headers=headers, timeout=timeout)
            model_ids: List[str] = []

            if isinstance(data, dict):
                items = data.get("data")
                if isinstance(items, list):
                    for it in items:
                        if isinstance(it, dict):
                            mid = it.get("id")
                            if isinstance(mid, str) and mid.strip():
                                model_ids.append(mid.strip())
                elif isinstance(items, dict):
                    mid = items.get("id")
                    if isinstance(mid, str) and mid.strip():
                        model_ids.append(mid.strip())
            elif isinstance(data, list):
                for it in data:
                    if isinstance(it, dict):
                        mid = it.get("id")
                        if isinstance(mid, str) and mid.strip():
                            model_ids.append(mid.strip())
                    elif isinstance(it, str) and it.strip():
                        model_ids.append(it.strip())

            model_ids = sorted(list(dict.fromkeys(model_ids)))
            text = "\n".join(model_ids) if model_ids else json.dumps(data, ensure_ascii=False)
            return (text, json.dumps(data, ensure_ascii=False))
        except Exception as e:
            err = {"error": str(e), "url": url}
            return (f"❌ 获取模型列表失败：{e}", json.dumps(err, ensure_ascii=False))


class DapaoModelScopeChat:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 魔塔Token": ("STRING", {"default": "", "multiline": False}),
                "🌐 Base URL": ("STRING", {"default": "https://api-inference.modelscope.cn/v1", "multiline": False}),
                "🧠 模型ID": ("STRING", {"default": "Qwen/Qwen3-VL-8B-Instruct", "multiline": False}),
                "💬 用户消息": ("STRING", {"default": "你好", "multiline": True}),
                "🎯 系统提示词": ("STRING", {"default": "你是一个专业、友好且乐于助人的AI助手。", "multiline": True}),
                "🌡️ 温度": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01}),
                "🎲 Top-P": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
                "📏 最大长度": ("INT", {"default": 2048, "min": 1, "max": 32768}),
                "⏱️ 超时时间": ("INT", {"default": 180, "min": 1, "max": 600}),
                "🎲 随机种子": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
                "🎯 种子控制": (["随机", "固定", "递增"], {"default": "随机"}),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🧾 历史消息JSON": ("STRING", {"default": "[]", "multiline": True}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "raw_json")
    FUNCTION = "chat"
    CATEGORY = "🤖dapaoAPI/魔塔API"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎯 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        return seed

    def chat(self, **kwargs) -> Tuple[str, str]:
        token = _get_modelscope_token(kwargs.get("🔑 魔塔Token", ""))
        if not token:
            return ("❌ 缺少 SDK Token：请在节点输入或本地 config.json / 环境变量中配置", json.dumps({"error": "missing_token"}, ensure_ascii=False))

        base_url = _normalize_base_url(kwargs.get("🌐 Base URL", ""))
        url = f"{base_url}/chat/completions"

        model_id = (kwargs.get("🧠 模型ID", "") or "").strip()
        user_message = kwargs.get("💬 用户消息", "") or ""
        system_prompt = kwargs.get("🎯 系统提示词", "") or ""
        temperature = float(kwargs.get("🌡️ 温度", 0.7))
        top_p = float(kwargs.get("🎲 Top-P", 0.9))
        max_tokens = int(kwargs.get("📏 最大长度", 2048))
        timeout = int(kwargs.get("⏱️ 超时时间", 180))

        seed = int(kwargs.get("🎲 随机种子", -1))
        seed_control = kwargs.get("🎯 种子控制", "随机")

        history_json = kwargs.get("🧾 历史消息JSON", "[]") or "[]"
        messages: List[Dict[str, Any]] = []
        try:
            history = json.loads(history_json) if history_json.strip() else []
            if isinstance(history, list):
                for item in history:
                    if isinstance(item, dict) and "role" in item and "content" in item:
                        messages.append({"role": str(item["role"]), "content": item["content"]})
        except Exception:
            messages = []

        if system_prompt.strip():
            messages.insert(0, {"role": "system", "content": system_prompt})

        images: List[Optional[torch.Tensor]] = [
            kwargs.get("🖼️ 图像1"),
            kwargs.get("🖼️ 图像2"),
            kwargs.get("🖼️ 图像3"),
            kwargs.get("🖼️ 图像4"),
        ]
        has_any_image = any(img is not None for img in images)
        if has_any_image:
            parts: List[Dict[str, Any]] = []
            if user_message.strip():
                parts.append({"type": "text", "text": user_message})
            for img in images:
                if img is None:
                    continue
                single = img[0] if len(img.shape) == 4 else img
                parts.append({"type": "image_url", "image_url": {"url": _encode_image_tensor_to_data_url(single)}})
            messages.append({"role": "user", "content": parts})
        else:
            messages.append({"role": "user", "content": user_message})

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        effective_seed = self._effective_seed(seed, seed_control)
        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": False,
            "seed": effective_seed,
        }

        try:
            data = _call_chat_completions(url=url, headers=headers, payload=payload, timeout=timeout)
            text = ""
            choices = data.get("choices")
            if isinstance(choices, list) and choices:
                msg = choices[0].get("message") if isinstance(choices[0], dict) else None
                if isinstance(msg, dict):
                    text = msg.get("content") or ""
            if not text:
                text = json.dumps(data, ensure_ascii=False)
            return (text, json.dumps(data, ensure_ascii=False))
        except Exception as e:
            err_text = str(e)
            hint = ""
            if "has no provider supported" in err_text:
                hint = "（该模型可能未在 API-Inference 开通。先用「📃 魔塔模型列表」节点查可用模型ID，再填到本节点）"
            err = {"error": err_text, "url": url}
            return (f"❌ API 调用失败：{e} {hint}".strip(), json.dumps(err, ensure_ascii=False))

    def __init__(self):
        self.last_seed = -1

    def _effective_seed(self, seed: int, seed_control: str) -> int:
        import random

        if seed_control == "固定":
            effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
        elif seed_control == "随机":
            effective_seed = random.randint(0, 2147483647)
        elif seed_control == "递增":
            if self.last_seed == -1:
                effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
            else:
                effective_seed = self.last_seed + 1
        else:
            effective_seed = random.randint(0, 2147483647)

        self.last_seed = effective_seed
        return effective_seed


class DapaoModelScopeImageEdit:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 魔塔Token": ("STRING", {"default": "", "multiline": False}),
                "🌐 Base URL": ("STRING", {"default": "https://api-inference.modelscope.cn/v1", "multiline": False}),
                "🧠 模型ID": ("STRING", {"default": "damo/cv_stable-diffusion_image-to-image", "multiline": False}),
                "📝 提示词": ("STRING", {"default": "", "multiline": True}),
                "📐 图像宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64, "display": "number"}),
                "📏 图像高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64, "display": "number"}),
                "🔢 张数": ("INT", {"default": 1, "min": 1, "max": 4}),
                "⏱️ 超时时间": ("INT", {"default": 300, "min": 1, "max": 900}),
                "🎲 随机种子": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
                "🎯 种子控制": (["随机", "固定", "递增"], {"default": "随机"}),
                "🧩 启用LoRA": ("BOOLEAN", {"default": False}),
                "🔢 LoRA数量": (["1", "2", "3", "4", "5"], {"default": "1"}),
                "🧩 LoRA1 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA1 强度": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA2 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA2 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA3 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA3 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA4 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA4 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA5 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA5 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🖼️ 图像5": ("IMAGE",),
                "🖼️ 图像6": ("IMAGE",),
            }
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎯 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        return seed

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "raw_json")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/魔塔API"

    def __init__(self):
        self.last_seed = -1

    def _effective_seed(self, seed: int, seed_control: str) -> int:
        import random

        if seed_control == "固定":
            effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
        elif seed_control == "随机":
            effective_seed = random.randint(0, 2147483647)
        elif seed_control == "递增":
            if self.last_seed == -1:
                effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
            else:
                effective_seed = self.last_seed + 1
        else:
            effective_seed = random.randint(0, 2147483647)
        self.last_seed = effective_seed
        return effective_seed

    def generate(self, **kwargs) -> Tuple[torch.Tensor, str, str]:
        token = _get_modelscope_token(kwargs.get("🔑 魔塔Token", ""))
        if not token:
            return (
                _blank_image_tensor("red"),
                "❌ 缺少Token",
                json.dumps({"error": "missing_token"}, ensure_ascii=False),
            )

        base_url = _normalize_base_url(kwargs.get("🌐 Base URL", ""))
        model_id = (kwargs.get("🧠 模型ID", "") or "").strip()
        if not model_id:
            return (
                _blank_image_tensor("gray"),
                "❌ 缺少模型ID",
                json.dumps({"error": "missing_model_id"}, ensure_ascii=False),
            )
        url = f"{base_url}/images/generations"

        prompt = kwargs.get("📝 提示词", "") or ""
        width = int(kwargs.get("📐 图像宽度", 1024))
        height = int(kwargs.get("📏 图像高度", 1024))
        n_images = int(kwargs.get("🔢 张数", 1))
        timeout = int(kwargs.get("⏱️ 超时时间", 300))

        seed = int(kwargs.get("🎲 随机种子", -1))
        seed_control = kwargs.get("🎯 种子控制", "随机")
        effective_seed = self._effective_seed(seed, seed_control)

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        headers_submit = {**headers, "X-ModelScope-Async-Mode": "true"}

        # LoRA 处理
        enable_lora = bool(kwargs.get("🧩 启用LoRA", False))
        lora_count_raw = kwargs.get("🔢 LoRA数量", "1")
        try:
            lora_count = int(lora_count_raw)
        except Exception:
            lora_count = 1
        lora_count = max(1, min(5, lora_count))

        lora_items: List[Tuple[str, float]] = []
        if enable_lora:
            for idx in range(1, lora_count + 1):
                lora_id = (kwargs.get(f"🧩 LoRA{idx} ID", "") or "").strip()
                if not lora_id:
                    continue
                w = float(kwargs.get(f"🎚️ LoRA{idx} 强度", 0.0))
                if w <= 0:
                    continue
                lora_items.append((lora_id, w))

        lora_dict: Dict[str, float] = {}
        if lora_items:
            for lid, w in lora_items:
                lora_dict[lid] = float(w)

        # 收集图像
        input_images = []
        for i in range(1, 7):
            img = kwargs.get(f"🖼️ 图像{i}")
            if img is not None:
                # 转换为 base64
                single = img[0] if len(img.shape) == 4 else img
                input_images.append(_encode_image_tensor_to_jpeg_data_url(single))
        if not input_images:
            return (
                _blank_image_tensor("gray"),
                "❌ 图像编辑需要至少 1 张输入图像",
                json.dumps({"error": "missing_input_image"}, ensure_ascii=False),
            )

        payload: Dict[str, Any] = {
            "model": model_id,
            "prompt": prompt,
            "seed": effective_seed,
            "n": n_images,
            "size": f"{width}x{height}",
        }
        if len(input_images) == 1:
            payload["image"] = input_images[0]
        else:
            payload["images"] = input_images
        if lora_dict:
            payload["loras"] = lora_dict
            first_lora_id = next(iter(lora_dict.keys()))
            first_lora_w = next(iter(lora_dict.values()))
            payload["lora"] = first_lora_id
            payload["lora_weight"] = first_lora_w

        headers_submit = {
            **headers_submit,
            "X-ModelScope-Task-Type": "image-to-image-generation",
            "X-ModelScope-Request-Params": json.dumps({"loras": lora_dict} if lora_dict else {}, ensure_ascii=False),
        }

        # 尝试调用
        try:
            try:
                data = _post_json(url, headers=headers_submit, payload=payload, timeout=timeout)
            except Exception as e:
                if "HTTP 400" not in str(e):
                    raise
                payload_no_size = {k: v for k, v in payload.items() if k != "size"}
                data = _post_json(url, headers=headers_submit, payload=payload_no_size, timeout=timeout)

            task_id = data.get("task_id") if isinstance(data, dict) else None
            final_data: Any = data
            urls: List[str] = []

            # 异步任务轮询
            if isinstance(task_id, str) and task_id.strip():
                task_url = f"{base_url}/tasks/{task_id.strip()}"
                # 注意：通用推理任务的任务查询 URL 可能不同，这里假设与 TextToImage 相同
                # 如果 base_url 是 /v1，则 /tasks/{id} 是合理的
                task_headers = {**headers, "X-ModelScope-Task-Type": "image_generation"}
                start = time.time()
                while True:
                    if time.time() - start > timeout:
                        raise RuntimeError(f"task_timeout: {task_id}")
                    task_data = _get_json(task_url, headers=task_headers, timeout=min(timeout, 60))
                    final_data = {"submit": data, "task": task_data}
                    if isinstance(task_data, dict):
                        status = (task_data.get("task_status") or task_data.get("status") or "").upper()
                        if status in ["SUCCEED", "SUCCESS", "SUCCEEDED"]:
                            out_imgs = task_data.get("output_images")
                            # 通用推理结果可能在 output 字段
                            if not out_imgs:
                                out_imgs = task_data.get("output", {}).get("images")
                            
                            if isinstance(out_imgs, list):
                                for u in out_imgs:
                                    if isinstance(u, str) and u.strip():
                                        urls.append(u.strip())
                            break
                        if status in ["FAILED", "FAIL"]:
                            raise RuntimeError(f"task_failed: {json.dumps(task_data, ensure_ascii=False)[:2000]}")
                    time.sleep(2)
            else:
                # 同步返回处理
                # 通用推理结果通常在 data.output.choices (chat) 或 data.output.results
                # 文生图/图生图通常直接返回 output_images 或 output: { output_imgs: ... }
                
                # 1. 尝试直接获取 images
                images = data.get("images")
                if isinstance(images, list):
                    for item in images:
                        if isinstance(item, dict):
                            u = item.get("url")
                            if isinstance(u, str) and u.strip():
                                urls.append(u.strip())
                        elif isinstance(item, str) and item.strip():
                            urls.append(item.strip())
                
                # 2. 尝试 output_images
                if not urls:
                    out_imgs = data.get("output_images")
                    if isinstance(out_imgs, list):
                        for u in out_imgs:
                            urls.append(u)
                            
                # 3. 尝试 output.images (常见于通用推理)
                if not urls and isinstance(data.get("output"), dict):
                    out_imgs = data.get("output", {}).get("images")
                    if isinstance(out_imgs, list):
                        for u in out_imgs:
                            urls.append(u)

                # 4. 尝试 output.img_url
                if not urls and isinstance(data.get("output"), dict):
                     u = data.get("output", {}).get("img_url")
                     if u: urls.append(u)

            if not urls:
                return (_blank_image_tensor("gray"), "⚠️ 未返回图片URL", json.dumps(final_data, ensure_ascii=False))

            tensors: List[torch.Tensor] = []
            download_errors: List[Dict[str, Any]] = []
            for u in urls:
                try:
                    if u.startswith("http"):
                        r = requests.get(u, timeout=timeout)
                        if r.status_code in (401, 403):
                            r = requests.get(u, timeout=timeout, headers={"Authorization": f"Bearer {token}"})
                        r.raise_for_status()
                        img = Image.open(io.BytesIO(r.content))
                    elif u.startswith("data:image") or ";base64," in u:
                        import base64
                        b64_part = u.split(",", 1)[1] if "," in u else u
                        img = Image.open(io.BytesIO(base64.b64decode(b64_part)))
                    else:
                        download_errors.append({"url": u, "error": "unsupported_url"})
                        continue

                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    tensors.append(_pil2tensor(img))
                except Exception as e:
                    download_errors.append({"url": u, "error": str(e)})
                    continue

            if not tensors:
                if isinstance(final_data, dict):
                    final_data = {**final_data, "download_errors": download_errors}
                else:
                    final_data = {"data": final_data, "download_errors": download_errors}
                first_url = urls[0] if urls else ""
                return (_blank_image_tensor("gray"), first_url or "⚠️ 未能下载图片", json.dumps(final_data, ensure_ascii=False))

            out = torch.cat(tensors, dim=0)
            return (out, urls[0] if urls else "", json.dumps(final_data, ensure_ascii=False))
        except Exception as e:
            err = {"error": str(e), "url": url}
            return (_blank_image_tensor("red"), f"❌ {e}", json.dumps(err, ensure_ascii=False))


class DapaoModelScopeTextToImage:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 魔塔Token": ("STRING", {"default": "", "multiline": False}),
                "🌐 Base URL": ("STRING", {"default": "https://api-inference.modelscope.cn/v1", "multiline": False}),
                "🧠 模型ID": ("STRING", {"default": "Tongyi-MAI/Z-Image-Turbo", "multiline": False}),
                "📝 提示词": ("STRING", {"default": "a cute girl in festive chinese new year clothing", "multiline": True}),
                "📐 图像宽度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64, "display": "number"}),
                "📏 图像高度": ("INT", {"default": 1024, "min": 64, "max": 8192, "step": 64, "display": "number"}),
                "🔢 张数": ("INT", {"default": 1, "min": 1, "max": 4}),
                "⏱️ 超时时间": ("INT", {"default": 300, "min": 1, "max": 900}),
                "🎲 随机种子": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
                "🎯 种子控制": (["随机", "固定", "递增"], {"default": "随机"}),
                "🧩 启用LoRA": ("BOOLEAN", {"default": False}),
                "🔢 LoRA数量": (["1", "2", "3", "4", "5"], {"default": "1"}),
                "🧩 LoRA1 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA1 强度": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA2 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA2 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA3 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA3 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA4 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA4 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧩 LoRA5 ID": ("STRING", {"default": "", "multiline": False}),
                "🎚️ LoRA5 强度": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 1.0, "step": 0.01}),
            },
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎯 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        return seed

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "raw_json")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/魔塔API"

    def __init__(self):
        self.last_seed = -1

    def _effective_seed(self, seed: int, seed_control: str) -> int:
        import random

        if seed_control == "固定":
            effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
        elif seed_control == "随机":
            effective_seed = random.randint(0, 2147483647)
        elif seed_control == "递增":
            if self.last_seed == -1:
                effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
            else:
                effective_seed = self.last_seed + 1
        else:
            effective_seed = random.randint(0, 2147483647)
        self.last_seed = effective_seed
        return effective_seed

    def generate(self, **kwargs):
        token = _get_modelscope_token(kwargs.get("🔑 魔塔Token", ""))
        if not token:
            return (
                _blank_image_tensor("red"),
                "❌ 缺少Token",
                json.dumps({"error": "missing_token"}, ensure_ascii=False),
            )

        base_url = _normalize_base_url(kwargs.get("🌐 Base URL", ""))
        url = f"{base_url}/images/generations"

        model_id = (kwargs.get("🧠 模型ID", "") or "").strip()
        prompt = kwargs.get("📝 提示词", "") or ""
        width = int(kwargs.get("📐 图像宽度", 1024))
        height = int(kwargs.get("📏 图像高度", 1024))
        n_images = int(kwargs.get("🔢 张数", 1))
        timeout = int(kwargs.get("⏱️ 超时时间", 300))

        seed = int(kwargs.get("🎲 随机种子", -1))
        seed_control = kwargs.get("🎯 种子控制", "随机")
        effective_seed = self._effective_seed(seed, seed_control)

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        headers_submit = {**headers, "X-ModelScope-Async-Mode": "true"}

        enable_lora = bool(kwargs.get("🧩 启用LoRA", False))
        lora_count_raw = kwargs.get("🔢 LoRA数量", "1")
        try:
            lora_count = int(lora_count_raw)
        except Exception:
            lora_count = 1
        lora_count = max(1, min(5, lora_count))

        lora_items: List[Tuple[str, float]] = []
        if enable_lora:
            for idx in range(1, lora_count + 1):
                lora_id = (kwargs.get(f"🧩 LoRA{idx} ID", "") or "").strip()
                if not lora_id:
                    continue
                w = float(kwargs.get(f"🎚️ LoRA{idx} 强度", 0.0))
                if w <= 0:
                    continue
                lora_items.append((lora_id, w))

        loras_payload: Any = None
        loras_meta: Dict[str, Any] = {}
        if len(lora_items) == 1 and abs(lora_items[0][1] - 1.0) < 1e-6:
            loras_payload = lora_items[0][0]
        elif len(lora_items) >= 1:
            total = sum(w for _, w in lora_items)
            if total <= 0:
                loras_payload = None
            else:
                loras_payload = {lid: (w / total) for lid, w in lora_items}
                loras_meta = {"loras_original": {lid: w for lid, w in lora_items}, "loras_normalized": True}

        payload: Dict[str, Any] = {"model": model_id, "prompt": prompt, "seed": effective_seed, "size": f"{width}x{height}"}
        if n_images != 1:
            payload["n"] = n_images
        if loras_payload is not None:
            payload["loras"] = loras_payload

        try:
            try:
                data = _post_json(url, headers=headers_submit, payload=payload, timeout=timeout)
            except Exception as e:
                if "HTTP 400" not in str(e):
                    raise
                minimal_payload: Dict[str, Any] = {"model": model_id, "prompt": prompt, "seed": effective_seed}
                if n_images != 1:
                    minimal_payload["n"] = n_images
                if loras_payload is not None:
                    minimal_payload["loras"] = loras_payload
                data = _post_json(url, headers=headers_submit, payload=minimal_payload, timeout=timeout)

            task_id = data.get("task_id") if isinstance(data, dict) else None
            final_data: Any = data
            urls: List[str] = []

            if isinstance(task_id, str) and task_id.strip():
                task_url = f"{base_url}/tasks/{task_id.strip()}"
                task_headers = {**headers, "X-ModelScope-Task-Type": "image_generation"}
                start = time.time()
                while True:
                    if time.time() - start > timeout:
                        raise RuntimeError(f"task_timeout: {task_id}")
                    task_data = _get_json(task_url, headers=task_headers, timeout=min(timeout, 60))
                    final_data = {"submit": data, "task": task_data, **loras_meta}
                    if isinstance(task_data, dict):
                        status = (task_data.get("task_status") or task_data.get("status") or "").upper()
                        if status in ["SUCCEED", "SUCCESS", "SUCCEEDED"]:
                            out_imgs = task_data.get("output_images")
                            if isinstance(out_imgs, list):
                                for u in out_imgs:
                                    if isinstance(u, str) and u.strip():
                                        urls.append(u.strip())
                            break
                        if status in ["FAILED", "FAIL"]:
                            raise RuntimeError(f"task_failed: {json.dumps(task_data, ensure_ascii=False)[:2000]}")
                    time.sleep(2)
            else:
                images = data.get("images") if isinstance(data, dict) else None
                if isinstance(images, list):
                    for item in images:
                        if isinstance(item, dict):
                            u = item.get("url")
                            if isinstance(u, str) and u.strip():
                                urls.append(u.strip())
                        elif isinstance(item, str) and item.strip():
                            urls.append(item.strip())
                elif isinstance(data, dict):
                    out_imgs = data.get("output_images")
                    if isinstance(out_imgs, list):
                        for u in out_imgs:
                            if isinstance(u, str) and u.strip():
                                urls.append(u.strip())
                if loras_meta and isinstance(final_data, dict):
                    final_data = {**final_data, **loras_meta}

            if not urls:
                return (_blank_image_tensor("gray"), "⚠️ 未返回图片URL", json.dumps(final_data, ensure_ascii=False))

            tensors: List[torch.Tensor] = []
            download_errors: List[Dict[str, Any]] = []
            for u in urls:
                try:
                    r = requests.get(u, timeout=timeout)
                    if r.status_code in (401, 403):
                        r = requests.get(u, timeout=timeout, headers={"Authorization": f"Bearer {token}"})
                    r.raise_for_status()
                    img = Image.open(io.BytesIO(r.content))
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    tensors.append(_pil2tensor(img))
                except Exception as e:
                    download_errors.append({"url": u, "error": str(e)})
                    continue

            if not tensors:
                if isinstance(final_data, dict):
                    final_data = {**final_data, "download_errors": download_errors}
                else:
                    final_data = {"data": final_data, "download_errors": download_errors}
                first_url = urls[0] if urls else ""
                return (_blank_image_tensor("gray"), first_url or "⚠️ 未能下载图片", json.dumps(final_data, ensure_ascii=False))

            out = torch.cat(tensors, dim=0)
            return (out, urls[0], json.dumps(final_data, ensure_ascii=False))
        except Exception as e:
            err = {"error": str(e), "url": url}
            return (_blank_image_tensor("red"), f"❌ {e}", json.dumps(err, ensure_ascii=False))


NODE_CLASS_MAPPINGS = {
    "DapaoModelScopeListModels": DapaoModelScopeListModels,
    "DapaoModelScopeChat": DapaoModelScopeChat,
    "DapaoModelScopeTextToImage": DapaoModelScopeTextToImage,
    "DapaoModelScopeImageEdit": DapaoModelScopeImageEdit,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoModelScopeListModels": "📃 魔塔模型列表 @炮老师的小课堂",
    "DapaoModelScopeChat": "💬 魔塔LLM对话 @炮老师的小课堂",
    "DapaoModelScopeTextToImage": "🎨 魔塔文生图 @炮老师的小课堂",
    "DapaoModelScopeImageEdit": "魔塔图像编辑@炮老师的小课堂",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
