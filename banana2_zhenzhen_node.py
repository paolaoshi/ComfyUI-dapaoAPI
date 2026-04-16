import torch
import requests
import json
import time
import base64
from PIL import Image
from io import BytesIO
import numpy as np
import comfy.utils
import math

# 辅助函数：Tensor 转 PIL
def tensor2pil(image):
    return [Image.fromarray(np.clip(255. * img.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)) for img in image]

# 辅助函数：PIL 转 Tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

class DapaoBanana2ZhenzhenNode:
    """
    🙈Banana2贞贞@炮老师的小课堂
    
    整合了 Nano Banana 2 生成能力与多线路 API 切换功能。
    支持文本生图、图生图（多图编辑）以及异步任务查询。
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # API 设置部分
                "🌐 API线路": (["zhenzhen", "柏拉图", "ip", "hk", "us"], {"default": "zhenzhen", "tooltip": "选择 API 线路：\nzhenzhen: 国内线路\n柏拉图: 柏拉图镜像站\nhk: 香港线路\nus: 美国线路\nip: 自定义地址"}),
                "🔑 API密钥": ("STRING", {"default": "", "multiline": False, "tooltip": "请输入您的 API Key"}),
                
                # 生成参数部分
                "📝 提示词": ("STRING", {"multiline": True, "default": "", "tooltip": "提示词"}),
                "🎨 生成模式": (["文生图", "图像编辑"], {"default": "文生图", "tooltip": "模式：文生图 或 图像编辑"}),
                "🤖 模型版本": (["nano-banana-2", "nano-banana-2-2k", "nano-banana-2-4k"], {"default": "nano-banana-2", "tooltip": "选择模型版本"}),
                "📐 宽高比": (["auto", "16:9", "4:3", "4:5", "3:2", "1:1", "2:3", "3:4", "5:4", "9:16", "21:9"], {"default": "auto", "tooltip": "宽高比"}),
                "🖼️ 图片分辨率": (["1K", "2K", "4K"], {"default": "2K", "tooltip": "图片分辨率"}),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647, "control_after_generate": "randomize", "tooltip": "随机种子"}),
                "🖼️ 出图数量": ("INT", {"default": 1, "min": 1, "max": 999999, "tooltip": "一次请求生成图片数量"}),
                "🌊 流式输出": ("BOOLEAN", {"default": False, "tooltip": "启用后逐张显示生成结果（多张出图时更快看到第一张）"}),
            },
            "optional": {
                # 自定义 API 地址
                "🔗 自定义API地址": ("STRING", {"default": "", "tooltip": "当 API线路 选择 'ip' 时，在此输入完整 API 地址 (如 http://1.2.3.4:8080)"}),
                
                # 任务控制
                "🆔 任务ID": ("STRING", {"default": "", "tooltip": "填入任务 ID 可查询历史任务状态（留空则创建新任务）"}),
                "📦 返回格式": (["url", "b64_json"], {"default": "url", "tooltip": "返回格式：URL链接 或 Base64编码"}),
                
                # 多图输入 (支持最多14张图)
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

    def get_headers(self, api_key):
        return {
            "Authorization": f"Bearer {api_key}"
        }

    def _get_base_url(self, api_source, custom_api_url):
        """根据选择获取 API Base URL"""
        base_url_mapping = {
            "zhenzhen": "https://ai.t8star.cn",
            "柏拉图": "https://api.bltcy.ai",
            "hk": "https://hk-api.gptbest.vip",
            "us": "https://api.gptbest.vip",
            "ip": custom_api_url.strip()
        }
        
        url = base_url_mapping.get(api_source, "")
        if api_source == "ip" and not url:
            print("[dapaoAPI] ⚠️ 警告：选择了 'ip' 模式但未填写 '自定义API地址'，将默认使用 zhenzhen 线路")
            return "https://ai.t8star.cn"
            
        return url

    def generate_image(self, **kwargs):
        # 1. 参数映射（中文 -> 内部变量名）
        api_source = kwargs.get("🌐 API线路", "zhenzhen")
        api_key = kwargs.get("🔑 API密钥", "")
        prompt = kwargs.get("📝 提示词", "")
        mode_raw = kwargs.get("🎨 生成模式", "文生图")
        
        # 映射模式到 API 值
        mode_map = {
            "文生图": "text2img",
            "图像编辑": "img2img"
        }
        mode = mode_map.get(mode_raw, "text2img")
        
        model = kwargs.get("🤖 模型版本", "nano-banana-2")
        aspect_ratio = kwargs.get("📐 宽高比", "auto")
        image_size = kwargs.get("🖼️ 图片分辨率", "2K")
        seed = kwargs.get("🎲 随机种子", 0)
        n_images_raw = kwargs.get("🖼️ 出图数量", None)
        if n_images_raw is None:
            n_images_raw = kwargs.get("出图数量", None)
        if n_images_raw is None:
            n_images_raw = 1
        n_images = max(1, int(n_images_raw))
        stream_enabled = bool(kwargs.get("🌊 流式输出", False))
        
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        task_id = kwargs.get("🆔 任务ID", "")
        response_format = kwargs.get("📦 返回格式", "url")
        
        # 提取图片
        image1 = kwargs.get("🖼️ 参考图1")
        image2 = kwargs.get("🖼️ 参考图2")
        image3 = kwargs.get("🖼️ 参考图3")
        image4 = kwargs.get("🖼️ 参考图4")
        image5 = kwargs.get("🖼️ 参考图5")
        image6 = kwargs.get("🖼️ 参考图6")
        image7 = kwargs.get("🖼️ 参考图7")
        image8 = kwargs.get("🖼️ 参考图8")
        image9 = kwargs.get("🖼️ 参考图9")
        image10 = kwargs.get("🖼️ 参考图10")
        image11 = kwargs.get("🖼️ 参考图11")
        image12 = kwargs.get("🖼️ 参考图12")
        image13 = kwargs.get("🖼️ 参考图13")
        image14 = kwargs.get("🖼️ 参考图14")

        # 2. 确定 API 地址
        base_url = self._get_base_url(api_source, custom_api_url)
        print(f"[dapaoAPI] 使用 API 线路: {api_source} -> {base_url}")
        
        # 3. 校验 API Key
        if not api_key.strip():
            error_message = "❌ API Key 为空，请在节点中填写 🔑 API密钥"
            print(error_message)
            blank_image = Image.new('RGB', (512, 512), color='black')
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "failed", "message": error_message}))

        try:
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)

            # 4. 如果提供了 task_id，直接查询状态
            if task_id.strip():
                print(f"[dapaoAPI] 查询任务状态 task_id: {task_id}")
                return self._query_task_status(base_url, api_key, task_id, pbar)
            
            # 5. 创建新任务
            print(f"[dapaoAPI] 创建新任务，模式: {mode}")

            combined_tensors = []
            all_urls = []
            task_ids = []
            first_url = ""
            first_task_id = ""
            params = {"async": "true"}

            prepared_images = []
            if mode == "img2img":
                all_images = [image1, image2, image3, image4, image5, image6, image7,
                              image8, image9, image10, image11, image12, image13, image14]
                for idx, img in enumerate(all_images):
                    if img is None:
                        continue
                    pil_img = tensor2pil(img)[0]
                    buffered = BytesIO()
                    pil_img.save(buffered, format="PNG")
                    prepared_images.append((f"image_{idx}.png", buffered.getvalue()))
                print(f"[dapaoAPI] 处理 {len(prepared_images)} 张输入图片")

            for i in range(n_images):
                pbar.update_absolute(min(30, 10 + int((i / max(1, n_images)) * 20)))

                if mode == "text2img":
                    headers = self.get_headers(api_key)
                    headers["Content-Type"] = "application/json"

                    payload = {
                        "prompt": prompt,
                        "model": model,
                        "aspect_ratio": aspect_ratio,
                        "n": 1,
                    }

                    if model == "nano-banana-2":
                        payload["image_size"] = image_size

                    if response_format:
                        payload["response_format"] = response_format

                    if seed > 0:
                        payload["seed"] = seed

                    print(f"[dapaoAPI] 发送文生图请求: {payload}")
                    response = requests.post(
                        f"{base_url}/v1/images/generations",
                        headers=headers,
                        params=params,
                        json=payload,
                        timeout=self.timeout,
                    )
                else:
                    headers = self.get_headers(api_key)

                    files = []
                    for j, (name, raw) in enumerate(prepared_images):
                        bio = BytesIO(raw)
                        bio.seek(0)
                        files.append(("image", (name, bio, "image/png")))

                    data = {
                        "prompt": prompt,
                        "model": model,
                        "aspect_ratio": aspect_ratio,
                        "n": 1,
                    }

                    if model == "nano-banana-2":
                        data["image_size"] = image_size

                    if response_format:
                        data["response_format"] = response_format

                    if seed > 0:
                        data["seed"] = str(seed)

                    print(f"[dapaoAPI] 发送图生图请求...")
                    response = requests.post(
                        f"{base_url}/v1/images/edits",
                        headers=headers,
                        params=params,
                        data=data,
                        files=files,
                        timeout=self.timeout,
                    )

                if response.status_code != 200:
                    error_message = f"API Error: {response.status_code} - {response.text}"
                    print(error_message)
                    blank_image = Image.new("RGB", (512, 512), color="red")
                    return (pil2tensor(blank_image), "", "", json.dumps({"status": "failed", "message": error_message}))

                result = response.json()

                if "task_id" in result:
                    returned_task_id = result["task_id"]
                    task_ids.append(str(returned_task_id))
                    if not first_task_id:
                        first_task_id = str(returned_task_id)
                    img_tensor, img_url, tid, info = self._poll_task(
                        base_url,
                        api_key,
                        returned_task_id,
                        pbar,
                        final_update=not (stream_enabled and n_images > 1),
                    )
                    if isinstance(img_tensor, torch.Tensor) and img_tensor.dim() == 4:
                        combined_tensors.append(img_tensor)
                        if stream_enabled and n_images > 1:
                            preview_tensor = img_tensor[0:1]
                            preview_image = ("PNG", tensor2pil(preview_tensor)[0], None)
                            pbar.update_absolute(
                                min(99, 30 + int(((i + 1) / max(1, n_images)) * 69)),
                                preview=preview_image,
                            )
                    if img_url:
                        if not first_url:
                            first_url = img_url
                        all_urls.append(img_url)
                elif "data" in result and result["data"]:
                    img_tensor, img_url, tid, info = self._process_success_data(result["data"], f"sync_{i}", pbar)
                    if isinstance(img_tensor, torch.Tensor) and img_tensor.dim() == 4:
                        combined_tensors.append(img_tensor)
                        if stream_enabled and n_images > 1:
                            preview_tensor = img_tensor[0:1]
                            preview_image = ("PNG", tensor2pil(preview_tensor)[0], None)
                            pbar.update_absolute(
                                min(99, 30 + int(((i + 1) / max(1, n_images)) * 69)),
                                preview=preview_image,
                            )
                    if img_url:
                        if not first_url:
                            first_url = img_url
                        all_urls.append(img_url)
                else:
                    error_message = f"未知的响应格式: {result}"
                    print(error_message)
                    blank_image = Image.new("RGB", (512, 512), color="gray")
                    return (pil2tensor(blank_image), "", "", json.dumps({"status": "failed", "message": error_message}))

            if combined_tensors:
                final_tensor = torch.cat(combined_tensors, dim=0)
                pbar.update_absolute(100)
                return (
                    final_tensor,
                    first_url,
                    first_task_id,
                    json.dumps(
                        {
                            "status": "success",
                            "images_count": int(final_tensor.shape[0]) if isinstance(final_tensor, torch.Tensor) else 0,
                            "image_url": first_url,
                            "all_urls": all_urls,
                            "task_ids": task_ids,
                        },
                        ensure_ascii=False,
                    ),
                )

            blank_image = Image.new("RGB", (512, 512), color="white")
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "empty", "message": "No valid images found"}, ensure_ascii=False))
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_message = f"生成过程异常: {str(e)}"
            print(error_message)
            blank_image = Image.new('RGB', (512, 512), color='red')
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "error", "message": error_message}))

    def _poll_task(self, base_url, api_key, task_id, pbar, final_update=True):
        """轮询任务状态"""
        print(f"[dapaoAPI] 开始轮询任务: {task_id}")
        max_attempts = 60  # 最多等待10分钟
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(5)  # 每5秒查询一次
            attempt += 1
            
            try:
                headers = self.get_headers(api_key)
                headers["Content-Type"] = "application/json"
                
                query_url = f"{base_url}/v1/images/tasks/{task_id}"
                response = requests.get(query_url, headers=headers, timeout=self.timeout)
                
                if response.status_code != 200:
                    print(f"[dapaoAPI] 查询失败 ({attempt}): {response.status_code}")
                    continue
                
                result = response.json()
                
                # 解析状态
                actual_status = "unknown"
                actual_data = None
                
                if "data" in result and isinstance(result["data"], dict):
                    actual_status = result["data"].get("status", "unknown")
                    actual_data = result["data"].get("data")
                
                print(f"[dapaoAPI] 轮询 ({attempt}/{max_attempts}) 状态: {actual_status}")
                
                # 成功
                if actual_status in ["completed", "success", "done", "finished", "SUCCESS"]:
                    if final_update:
                        pbar.update_absolute(100)
                    return self._process_success_data(actual_data, task_id, pbar)
                
                # 失败
                if actual_status in ["failed", "error", "FAILURE"]:
                    error_msg = result.get("data", {}).get("error", "Unknown error")
                    print(f"[dapaoAPI] 任务失败: {error_msg}")
                    blank_image = Image.new('RGB', (512, 512), color='red')
                    return (pil2tensor(blank_image), "", task_id, json.dumps({"status": "failed", "message": error_msg}))
                
                # 进行中
                pbar.update_absolute(50 + (attempt % 40))
                
            except Exception as e:
                print(f"[dapaoAPI] 轮询异常: {e}")
        
        print("[dapaoAPI] 轮询超时")
        blank_image = Image.new('RGB', (512, 512), color='yellow')
        return (pil2tensor(blank_image), "", task_id, json.dumps({"status": "timeout", "message": "Task polling timed out"}))

    def _query_task_status(self, base_url, api_key, task_id, pbar):
        """单次查询任务状态"""
        return self._poll_task(base_url, api_key, task_id, pbar)

    def _process_success_data(self, data, task_id, pbar):
        """处理成功的返回数据"""
        generated_tensors = []
        image_urls = []
        
        # 兼容列表或单项
        data_items = data.get("data", []) if isinstance(data, dict) else data
        if not isinstance(data_items, list):
            data_items = [data_items]
            
        for i, item in enumerate(data_items):
            try:
                img_tensor = None
                img_url = ""
                
                if "b64_json" in item and item["b64_json"]:
                    # Base64
                    image_data = base64.b64decode(item["b64_json"])
                    img = Image.open(BytesIO(image_data))
                    if img.mode != 'RGB': img = img.convert('RGB')
                    img_tensor = pil2tensor(img)
                    img_url = "base64_image"
                    
                elif "url" in item and item["url"]:
                    # URL
                    img_url = item["url"]
                    image_urls.append(img_url)
                    # 下载图片
                    print(f"[dapaoAPI] 下载图片: {img_url}")
                    resp = requests.get(img_url, timeout=self.timeout)
                    resp.raise_for_status()
                    img = Image.open(BytesIO(resp.content))
                    if img.mode != 'RGB': img = img.convert('RGB')
                    img_tensor = pil2tensor(img)
                
                if img_tensor is not None:
                    generated_tensors.append(img_tensor)
                    
            except Exception as e:
                print(f"[dapaoAPI] 处理图片失败: {e}")
                continue
        
        if generated_tensors:
            combined_tensor = torch.cat(generated_tensors, dim=0)
            first_url = image_urls[0] if image_urls else ""
            
            result_info = {
                "status": "success",
                "task_id": task_id,
                "images_count": len(generated_tensors),
                "image_url": first_url,
                "all_urls": image_urls
            }
            return (combined_tensor, first_url, task_id, json.dumps(result_info))
        else:
            print("[dapaoAPI] 未找到有效图片数据")
            blank_image = Image.new('RGB', (512, 512), color='white')
            return (pil2tensor(blank_image), "", task_id, json.dumps({"status": "empty", "message": "No valid images found"}))


class DapaoBanana2OfficialNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 Google API Key": ("STRING", {"default": "", "multiline": False, "tooltip": "请输入 Google API Key"}),
                "📝 提示词": ("STRING", {"multiline": True, "default": "", "tooltip": "提示词"}),
                "🎨 生成模式": (["文生图", "图像编辑"], {"default": "文生图", "tooltip": "模式：文生图 或 图像编辑"}),
                "🤖 模型版本": ("STRING", {"default": "gemini-3-pro-image-preview", "multiline": False, "tooltip": "模型名称可手动输入，方便后续升级/更名"}),
                "📐 宽高比": (["auto", "16:9", "4:3", "4:5", "3:2", "1:1", "2:3", "3:4", "5:4", "9:16", "21:9"], {"default": "auto", "tooltip": "宽高比"}),
                "🖼️ 图片分辨率": (["1K", "2K", "4K"], {"default": "2K", "tooltip": "图片分辨率"}),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647, "control_after_generate": "randomize", "tooltip": "随机种子"}),
                "🖼️ 出图数量": ("INT", {"default": 1, "min": 1, "max": 999999, "tooltip": "一次请求生成图片数量"}),
                "🌊 流式输出": ("BOOLEAN", {"default": False, "tooltip": "启用后逐张显示生成结果（多张出图时更快看到第一张）"}),
            },
            "optional": {
                "🔍 启用Google搜索": ("BOOLEAN", {"default": False, "label_on": "启用搜索增强", "label_off": "关闭搜索增强"}),
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
            },
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "🆔 任务ID", "ℹ️ 响应信息")
    FUNCTION = "generate_image"
    CATEGORY = "🤖dapaoAPI/Nano Banana 2"

    def __init__(self):
        self.timeout = 600

    def _tensor_to_b64(self, img_tensor):
        try:
            pil_img = tensor2pil(img_tensor)[0]
            buffered = BytesIO()
            pil_img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
        except Exception:
            return ""

    def _extract_image_bytes(self, resp_json):
        try:
            candidates = resp_json.get("candidates", [])
            for cand in candidates:
                parts = cand.get("content", {}).get("parts", [])
                for part in parts:
                    if part.get("thought", False):
                        continue
                    inline_data = part.get("inlineData") or part.get("inline_data")
                    if not inline_data:
                        continue
                    mime = inline_data.get("mimeType") or inline_data.get("mime_type")
                    if not mime or not str(mime).startswith("image/"):
                        continue
                    b64 = inline_data.get("data")
                    if b64:
                        return base64.b64decode(b64)
        except Exception:
            return None
        return None

    def generate_image(self, **kwargs):
        api_key = kwargs.get("🔑 Google API Key", "")
        prompt = kwargs.get("📝 提示词", "")
        mode_raw = kwargs.get("🎨 生成模式", "文生图")
        model = kwargs.get("🤖 模型版本", "gemini-3-pro-image-preview")
        aspect_ratio = kwargs.get("📐 宽高比", "auto")
        image_size = kwargs.get("🖼️ 图片分辨率", "2K")
        seed = kwargs.get("🎲 随机种子", 0)
        n_images = max(1, int(kwargs.get("🖼️ 出图数量", 1) or 1))
        stream_enabled = bool(kwargs.get("🌊 流式输出", False))
        enable_google_search = bool(kwargs.get("🔍 启用Google搜索", False))

        mode_map = {"文生图": "text2img", "图像编辑": "img2img"}
        mode = mode_map.get(mode_raw, "text2img")

        if not str(api_key or "").strip():
            error_message = "❌ Google API Key 为空，请在节点中填写 🔑 Google API Key"
            blank_image = Image.new("RGB", (512, 512), color="black")
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "failed", "message": error_message}, ensure_ascii=False))

        input_images = []
        if mode == "img2img":
            for i in range(1, 15):
                img = kwargs.get(f"🖼️ 参考图{i}")
                if img is not None:
                    input_images.append(img)

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}

        combined_tensors = []
        pbar = comfy.utils.ProgressBar(100)
        pbar.update_absolute(10)

        try:
            for i in range(n_images):
                pbar.update_absolute(min(30, 10 + int((i / max(1, n_images)) * 20)))

                parts = []
                for img_tensor in input_images:
                    b64 = self._tensor_to_b64(img_tensor)
                    if b64:
                        parts.append({"inlineData": {"mimeType": "image/png", "data": b64}})
                parts.append({"text": prompt})

                payload = {
                    "contents": [{"role": "user", "parts": parts}],
                    "generationConfig": {"responseModalities": ["TEXT", "IMAGE"], "imageConfig": {}},
                }
                if aspect_ratio and str(aspect_ratio).lower() != "auto":
                    payload["generationConfig"]["imageConfig"]["aspectRatio"] = aspect_ratio
                if image_size and str(image_size).lower() != "auto":
                    payload["generationConfig"]["imageConfig"]["imageSize"] = str(image_size).upper()
                if seed and int(seed) > 0:
                    payload["generationConfig"]["seed"] = int(seed)
                if enable_google_search:
                    payload["tools"] = [{"google_search": {}}]

                response = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code != 200:
                    error_message = f"API Error: {response.status_code} - {response.text}"
                    blank_image = Image.new("RGB", (512, 512), color="red")
                    return (pil2tensor(blank_image), "", "", json.dumps({"status": "failed", "message": error_message}, ensure_ascii=False))

                result = response.json()
                img_bytes = self._extract_image_bytes(result)
                if not img_bytes:
                    blank_image = Image.new("RGB", (512, 512), color="gray")
                    return (pil2tensor(blank_image), "", "", json.dumps({"status": "empty", "message": "No image found in response"}, ensure_ascii=False))

                pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
                img_tensor = pil2tensor(pil_img)
                combined_tensors.append(img_tensor)

                if stream_enabled and n_images > 1:
                    preview_image = ("PNG", pil_img, None)
                    pbar.update_absolute(
                        min(99, 30 + int(((i + 1) / max(1, n_images)) * 69)),
                        preview=preview_image,
                    )

            if combined_tensors:
                final_tensor = torch.cat(combined_tensors, dim=0)
                pbar.update_absolute(100)
                return (
                    final_tensor,
                    "base64_image",
                    "",
                    json.dumps({"status": "success", "images_count": int(final_tensor.shape[0])}, ensure_ascii=False),
                )

            blank_image = Image.new("RGB", (512, 512), color="white")
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "empty", "message": "No valid images found"}, ensure_ascii=False))

        except Exception as e:
            import traceback
            traceback.print_exc()
            error_message = f"生成过程异常: {str(e)}"
            blank_image = Image.new("RGB", (512, 512), color="red")
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "error", "message": error_message}, ensure_ascii=False))
