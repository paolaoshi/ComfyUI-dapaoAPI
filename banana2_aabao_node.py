import torch
import requests
import json
import time
import base64
import re
from PIL import Image
from io import BytesIO
import numpy as np
import comfy.utils

# 辅助函数：Tensor 转 PIL
def tensor2pil(image):
    return [Image.fromarray(np.clip(255. * img.cpu().numpy().squeeze(), 0, 255).astype(np.uint8)) for img in image]

# 辅助函数：PIL 转 Tensor
def pil2tensor(image):
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)

# 辅助函数：Base64 转 PIL
def _b64_to_pil(b64_str):
    if not b64_str:
        return None
    try:
        image_data = base64.b64decode(b64_str)
        img = Image.open(BytesIO(image_data))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img
    except Exception as e:
        print(f"[dapaoAPI] Base64解码失败: {e}")
        return None

# 辅助函数：Tensor 转 Base64
def _tensor_to_b64(img_tensor, mime_type="image/png"):
    try:
        if img_tensor is None:
            return None
        pil_img = tensor2pil(img_tensor)[0]
        buffered = BytesIO()
        fmt = "PNG"
        if "jpeg" in mime_type: fmt = "JPEG"
        elif "webp" in mime_type: fmt = "WEBP"
        pil_img.save(buffered, format=fmt)
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        print(f"[dapaoAPI] 图片转Base64失败: {e}")
        return None

class DapaoBanana2AabaoNode:
    """
    🙈Banana2aabao专用@炮老师的小课堂
    
    专为 Aabao 渠道定制的 Nano Banana 2 (Gemini-3-Pro) 生成节点。
    使用 Gemini 原生 API 协议 (generateContent)。
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # API 设置部分
                "🌐 API线路": (["aabao", "ip"], {"default": "aabao", "tooltip": "选择 API 线路：\naabao: Aabao 默认线路 (api.aabao.top)\nip: 自定义地址"}),
                "🔑 API密钥": ("STRING", {"default": "", "multiline": False, "tooltip": "请输入您的 API Key"}),
                
                # 生成参数部分
                "📝 提示词": ("STRING", {"multiline": True, "default": "", "tooltip": "提示词"}),
                "🎨 生成模式": (["文生图", "图像编辑"], {"default": "文生图", "tooltip": "模式：文生图 或 图像编辑"}),
                "🤖 模型版本": (["gemini-3-pro-image-preview"], {"default": "gemini-3-pro-image-preview", "tooltip": "选择模型版本"}),
                "📐 宽高比": (["auto", "16:9", "4:3", "4:5", "3:2", "1:1", "2:3", "3:4", "5:4", "9:16", "21:9"], {"default": "auto", "tooltip": "宽高比"}),
                "🖼️ 图片分辨率": (["1K", "2K", "4K"], {"default": "2K", "tooltip": "图片分辨率"}),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647, "tooltip": "随机种子"}),
            },
            "optional": {
                # 自定义 API 地址
                "🔗 自定义API地址": ("STRING", {"default": "https://api.aabao.top", "tooltip": "当 API线路 选择 'ip' 时，在此输入完整 API 地址"}),
                
                # 任务控制 (保留但不一定生效，Gemini通常同步)
                "🆔 任务ID": ("STRING", {"default": "", "tooltip": "Gemini 模式下通常无效"}),
                "📦 返回格式": (["url", "b64_json"], {"default": "url", "tooltip": "内部自动处理"}),
                
                # 多图输入 (支持最多4张图，Gemini 限制)
                "🖼️ 参考图1": ("IMAGE",),
                "🖼️ 参考图2": ("IMAGE",),
                "🖼️ 参考图3": ("IMAGE",),
                "🖼️ 参考图4": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "🆔 任务ID", "ℹ️ 响应信息")
    FUNCTION = "generate_image"
    CATEGORY = "🤖dapaoAPI/Nano Banana 2"

    def __init__(self):
        self.timeout = 300

    def _get_base_url(self, api_source, custom_api_url):
        """根据选择获取 API Base URL"""
        base_url_mapping = {
            "aabao": "https://api.aabao.top",
            "ip": custom_api_url.strip()
        }
        
        url = base_url_mapping.get(api_source, "")
        if api_source == "ip" and not url:
            print("[dapaoAPI] ⚠️ 警告：选择了 'ip' 模式但未填写 '自定义API地址'，将默认使用 aabao 线路")
            return "https://api.aabao.top"
            
        return url

    def generate_image(self, **kwargs):
        # 1. 提取参数
        api_source = kwargs.get("🌐 API线路", "aabao")
        api_key = kwargs.get("🔑 API密钥", "")
        prompt = kwargs.get("📝 提示词", "")
        mode_raw = kwargs.get("🎨 生成模式", "文生图")
        
        model = kwargs.get("🤖 模型版本", "gemini-3-pro-image-preview")
        aspect_ratio = kwargs.get("📐 宽高比", "auto")
        image_size = kwargs.get("🖼️ 图片分辨率", "2K")
        seed = kwargs.get("🎲 随机种子", 0)
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        
        # 2. 校验 API Key
        if not api_key.strip():
            error_message = "❌ API Key 为空，请在节点中填写 🔑 API密钥"
            print(error_message)
            blank_image = Image.new('RGB', (512, 512), color='black')
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "failed", "message": error_message}))

        # 3. 构建 URL (Gemini 协议)
        base_url = self._get_base_url(api_source, custom_api_url)
        base_url = base_url.rstrip('/')
        
        # 如果 URL 已经包含 /models/...，则直接使用
        if "/models/" in base_url and ":generateContent" in base_url:
            endpoint = base_url
        # 如果 URL 以 /v1beta 等结尾
        elif base_url.endswith("/v1beta") or base_url.endswith("/v1alpha") or base_url.endswith("/v1"):
            endpoint = f"{base_url}/models/{model}:generateContent"
        # 默认追加 /v1beta/models/...
        else:
            endpoint = f"{base_url}/v1beta/models/{model}:generateContent"
            
        print(f"[dapaoAPI] API Endpoint: {endpoint}")
        
        # 4. 构建 Payload
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 构建 parts
        parts = [{"text": prompt}]
        
        # 处理输入图片 (图生图)
        input_images = []
        for i in range(1, 5): # 最多4张
            img = kwargs.get(f"🖼️ 参考图{i}")
            if img is not None:
                b64 = _tensor_to_b64(img)
                if b64:
                    parts.append({
                        "inlineData": {
                            "mimeType": "image/png",
                            "data": b64
                        }
                    })

        # Gemini Payload 结构
        payload = {
            "contents": [{
                "role": "user",
                "parts": parts
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"], # 关键：请求图像
                "imageConfig": {}, # 宽高比和尺寸放在这里
                "temperature": 1.0,
                "topP": 0.95,
                "topK": 40,
                "maxOutputTokens": 8192
            }
        }
        
        # 设置宽高比和分辨率
        if aspect_ratio and aspect_ratio.lower() != "auto":
            payload["generationConfig"]["imageConfig"]["aspectRatio"] = aspect_ratio
        if image_size and image_size.lower() != "auto":
            payload["generationConfig"]["imageConfig"]["imageSize"] = image_size.upper() # 2K -> 2K
            
        if seed > 0:
            payload["generationConfig"]["seed"] = seed

        # 5. 发送请求
        try:
            print(f"[dapaoAPI] 发送请求中... (模式: {mode_raw})")
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)
            
            response = requests.post(endpoint, headers=headers, json=payload, timeout=self.timeout)
            pbar.update_absolute(80)
            
            if response.status_code != 200:
                error_message = f"API Error: {response.status_code} - {response.text}"
                print(error_message)
                blank_image = Image.new('RGB', (512, 512), color='red')
                return (pil2tensor(blank_image), "", "", json.dumps({"status": "failed", "message": error_message}))

            result = response.json()
            
            # 6. 解析结果 (提取图片)
            img_bytes = self._extract_image(result)
            
            if img_bytes:
                print("[dapaoAPI] ✅ 成功提取图像")
                pil_img = Image.open(BytesIO(img_bytes)).convert("RGB")
                pbar.update_absolute(100)
                return (pil2tensor(pil_img), "base64_image", "sync_task", json.dumps({"status": "success"}))
            else:
                print("[dapaoAPI] ❌ 未在响应中找到图像数据")
                # 尝试打印文本内容
                text_content = ""
                try:
                    text_content = result['candidates'][0]['content']['parts'][0]['text']
                    print(f"[dapaoAPI] 响应文本: {text_content}")
                except:
                    pass
                    
                blank_image = Image.new('RGB', (512, 512), color='gray')
                return (pil2tensor(blank_image), "", "", json.dumps({"status": "empty", "message": "No image found in response", "raw": result}))
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_message = f"请求异常: {str(e)}"
            print(error_message)
            blank_image = Image.new('RGB', (512, 512), color='red')
            return (pil2tensor(blank_image), "", "", json.dumps({"status": "error", "message": error_message}))

    def _extract_image(self, resp_json):
        """从 Gemini 响应中提取图片"""
        try:
            # 1. 尝试 inlineData (标准 Gemini)
            candidates = resp_json.get("candidates", [])
            for cand in candidates:
                parts = cand.get("content", {}).get("parts", [])
                for part in parts:
                    # 检查 inlineData
                    inline_data = part.get("inlineData") or part.get("inline_data")
                    if inline_data:
                        mime = inline_data.get("mimeType") or inline_data.get("mime_type")
                        if mime and mime.startswith("image/"):
                            b64 = inline_data.get("data")
                            if b64:
                                return base64.b64decode(b64)
                    
                    # 检查文本中的 Markdown 链接 (Fallback)
                    text = part.get("text", "")
                    if text:
                        # 匹配 ![...](url)
                        md_match = re.search(r'!\[.*?\]\((https?://[^\)]+)\)', text)
                        if md_match:
                            url = md_match.group(1)
                            print(f"[dapaoAPI] 发现图片链接: {url}")
                            return self._download_image(url)
                            
                        # 匹配纯 URL
                        url_match = re.search(r'(https?://[^\s\)]+\.(?:png|jpg|jpeg|gif|webp))', text, re.IGNORECASE)
                        if url_match:
                            url = url_match.group(1)
                            print(f"[dapaoAPI] 发现图片链接: {url}")
                            return self._download_image(url)

        except Exception as e:
            print(f"[dapaoAPI] 图片提取失败: {e}")
            
        return None

    def _download_image(self, url):
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                return r.content
        except Exception as e:
            print(f"[dapaoAPI] 下载图片失败: {e}")
        return None
