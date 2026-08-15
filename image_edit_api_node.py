"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 图像编辑API调用节点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 专门用于图像编辑的API调用
   - 支持多个图像输入(最多4个)
   - 灵活的API配置
   - 支持 Nano Banana 2 / Gemini 3 高级特性 (1K/2K/4K, 风格, 质量)
   - 集成智能AI放大 (Gigapixel/RealESRGAN)

🔧 技术特性：
   - 基于通用API调用逻辑
   - 支持图像base64编码
   - 支持图像URL下载
   - 完整的错误处理
   - 智能提示词处理

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v2.0.0 (Nano Banana Enhanced)
🎨 主题：紫色 (#9B59B6)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import requests
import base64
import io
import torch
import numpy as np
from PIL import Image
from typing import Tuple, Optional, Dict, Any, List
import re
import random
import time
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 尝试导入 Google 官方 SDK（可选）
try:
    from google import genai
    from google.genai import types as genai_types
    GOOGLE_SDK_AVAILABLE = True
    print("[dapaoAPI] ✅ Google Genai SDK 可用")
except ImportError:
    GOOGLE_SDK_AVAILABLE = False
    print("[dapaoAPI] ⚠️ Google Genai SDK 未安装，将使用 REST API")

# 尝试导入智能放大模块
try:
    from .ComfyUI_LLM_Banana.banana_upscale import smart_upscale
except ImportError:
    try:
        from ComfyUI_LLM_Banana.banana_upscale import smart_upscale
    except ImportError:
        smart_upscale = None
        print("⚠️ 未找到 ComfyUI_LLM_Banana.banana_upscale 模块，智能放大功能将不可用")

# 节点颜色 (紫色)


class ImageEditAPINode:
    """
    图像编辑API调用节点 (增强版)
    
    集成 Nano Banana 2 / Gemini 3 高级特性
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 定义预设选项
        aspect_ratios = ["Auto", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"]
        response_modalities = ["TEXT_AND_IMAGE", "IMAGE_ONLY"]
        output_resolutions = ["Auto (Model Default)", "1K", "2K", "4K"]
        quality_presets = ["standard", "hd", "ultra_hd", "ai_enhanced", "ai_ultra"]
        style_presets = ["vivid", "natural", "artistic", "cinematic", "photographic"]
        upscale_factors = ["1x (不放大)", "2x", "4x", "6x"]
        gigapixel_models = ["High Fidelity", "Standard", "Art & CG", "Lines", "Very Compressed", "Low Resolution", "Text & Shapes", "Redefine", "Recover"]
        
        return {
            "required": {
                "💬 提示词": ("STRING", {
                    "multiline": True,
                    "default": "请根据这些图片进行专业的图像编辑",
                    "placeholder": "输入你的编辑指令..."
                }),
                
                "🌐 API地址": ("STRING", {
                    "default": "https://api.tu-zi.com/v1/chat/completions",
                    "placeholder": "输入完整的API URL (Gemini模型用/chat/completions, DALL-E用/images/edits)"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "输入你的API密钥"
                }),
                
                "🤖 模型名称": ("STRING", {
                    "default": "gemini-3-pro-image-preview",
                    "placeholder": "输入模型名称，如: gemini-3-pro-image-preview, dall-e-3"
                }),
                
                "📡 请求方法": (["POST", "GET", "PUT"], {
                    "default": "POST"
                }),
                
                "🔐 密钥位置": (["Header", "Query", "Body"], {
                    "default": "Header"
                }),
                
                "📝 密钥字段名": ("STRING", {
                    "default": "Authorization",
                    "placeholder": "如: Authorization, api_key, X-API-Key"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                
                # Gemini/Nano Banana 高级参数
                "📐 宽高比": (aspect_ratios, {"default": "Auto"}),
                "📊 响应模式": (response_modalities, {"default": "TEXT_AND_IMAGE"}),
                "🖥️ 输出分辨率": (output_resolutions, {"default": "Auto (Model Default)", "tooltip": "仅支持 Nano Banana 2 (Gemini 3) 模型"}),
                "🎨 画质预设": (quality_presets, {"default": "hd"}),
                "🎭 风格预设": (style_presets, {"default": "natural"}),
                
                # 放大设置
                "🔍 放大倍数": (upscale_factors, {"default": "1x (不放大)"}),
                "🧩 放大模型": (gigapixel_models, {"default": "High Fidelity"}),

                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "可选：定义AI的角色和行为方式..."
                }),
                
                "🎯 响应提取路径": ("STRING", {
                    "default": "",
                    "placeholder": "如: data.0.url (留空自动智能提取)"
                }),
                
                "⏱️ 超时时间": ("INT", {
                    "default": 180,
                    "min": 1,
                    "max": 300,
                    "step": 1
                }),
                
                "📋 额外Headers": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "JSON格式的额外Headers"
                }),
                
                "📦 额外Body参数": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "JSON格式的额外Body参数"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("image", "response", "image_url", "raw_json")
    FUNCTION = "call_api"
    CATEGORY = "🤖dapaoAPI/🔮API通用工具🔮"
    DESCRIPTION = "🎨通用图像编辑API (测试版) @炮老师的小课堂 | 支持多模态图像编辑、智能提示词处理、AI放大"
    OUTPUT_NODE = False
    
    def __init__(self):
        pass
    
    def call_api(
        self,
        **kwargs
    ) -> Tuple[torch.Tensor, str, str, str]:
        """调用图像编辑API"""
        # 提取基础参数
        prompt = kwargs.get("💬 提示词", "")
        api_url = kwargs.get("🌐 API地址", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model_name = kwargs.get("🤖 模型名称", "Auto (Latest Gemini 3 Pro) 🤖")
        method = kwargs.get("📡 请求方法", "POST")
        key_location = kwargs.get("🔐 密钥位置", "Header")
        key_field = kwargs.get("📝 密钥字段名", "Authorization")
        
        # 提取高级参数
        aspect_ratio = kwargs.get("📐 宽高比", "Auto")
        response_modality = kwargs.get("📊 响应模式", "TEXT_AND_IMAGE")
        output_resolution = kwargs.get("🖥️ 输出分辨率", "Auto (Model Default)")
        quality = kwargs.get("🎨 画质预设", "hd")
        style = kwargs.get("🎭 风格预设", "natural")
        upscale_factor = kwargs.get("🔍 放大倍数", "1x (不放大)")
        gigapixel_model = kwargs.get("🧩 放大模型", "High Fidelity")
        
        # 其他参数
        system_role = kwargs.get("🎯 系统角色", "")
        extract_path = kwargs.get("🎯 响应提取路径", "")
        timeout = kwargs.get("⏱️ 超时时间", 60)
        extra_headers_str = kwargs.get("📋 额外Headers", "{}")
        extra_body_str = kwargs.get("📦 额外Body参数", "{}")
        
        # 图像输入
        images = [img for img in [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 5)] if img is not None]
        
        print(f"[dapaoAPI] API地址: {api_url}")
        print(f"[dapaoAPI] 模型: {model_name}")
        print(f"[dapaoAPI] 图像数量: {len(images)}")
        
        # 1. 检测模型类型
        is_nb2 = "gemini-3" in model_name.lower() or "pro-image" in model_name.lower()
        
        # 2. 智能提示词处理 (多图引用替换)
        converted_prompt = prompt
        if len(images) >= 1: converted_prompt = converted_prompt.replace("图1", "第一张图片")
        if len(images) >= 2: converted_prompt = converted_prompt.replace("图2", "第二张图片")
        if len(images) >= 3: converted_prompt = converted_prompt.replace("图3", "第三张图片")
        if len(images) >= 4: converted_prompt = converted_prompt.replace("图4", "第四张图片")
        
        # 构建完整提示词
        if len(images) > 1:
            # 多图编辑：强调所有图片的使用
            image_list = "、".join([f"第{i+1}张图片" for i in range(len(images))])
            full_prompt = f"""【多图编辑任务】
我上传了 {len(images)} 张图片（{image_list}），请务必综合参考所有图片进行编辑。

用户指令：
{converted_prompt}

重要要求：
1. 必须同时参考所有 {len(images)} 张图片的内容
2. 风格: {style}, 画质: {quality}
3. 仔细分析每张图片的特征，并按照用户指令进行精确组合
4. 确保生成的图片融合了所有输入图片的关键元素
5. 保持自然真实的视觉效果
"""
        elif len(images) == 1:
            # 单图编辑
            full_prompt = f"""请根据以下要求编辑图片：
{converted_prompt}

要求：风格 {style}, 画质 {quality}
"""
        else:
            full_prompt = prompt

        # 3. 构建API请求
        # 🔍 智能检测 Gemini 官方 API 并构建完整 URL
        is_gemini_official = "generativelanguage.googleapis.com" in api_url
        
        if is_gemini_official:
            # Gemini 官方 API：自动构建完整端点
            if ":generateContent" not in api_url:
                # 移除末尾的斜杠
                base_url = api_url.rstrip('/')
                # 构建完整端点
                api_url = f"{base_url}/v1beta/models/{model_name}:generateContent"
                print(f"[dapaoAPI] 🔗 Gemini 官方 API 完整端点: {api_url}")
        
        # 🔍 优先检测是否是 /images/edits 端点 (需要使用 multipart/form-data)
        is_images_edit_endpoint = "/images/edits" in api_url or "/images/edit" in api_url
        
        if is_images_edit_endpoint:
            # 使用 multipart/form-data 格式调用 /images/edits 端点
            return self._handle_images_edit_endpoint(
                api_url, api_key, full_prompt, images, model_name,  # 使用 full_prompt 而不是 prompt
                key_location, key_field, timeout, extra_headers_str, extra_body_str,
                aspect_ratio, output_resolution, response_modality, quality, style,
                upscale_factor, gigapixel_model
            )
        
        # 判断是否为 Gemini/Nano Banana 系列调用 (通过模型名或URL判断)
        is_gemini_api = "gemini" in model_name.lower() or "banana" in model_name.lower() or "google" in api_url.lower()
        
        if is_gemini_api:
            # 🔍 区分 Gemini 官方 API 和代理 API
            if is_gemini_official and GOOGLE_SDK_AVAILABLE:
                # 优先使用官方 SDK
                print(f"[dapaoAPI] 🚀 使用 Google 官方 SDK 调用")
                try:
                    return self._call_with_official_sdk(
                        api_key, model_name, full_prompt, images,
                        aspect_ratio, output_resolution, response_modality,
                        quality, style, system_role, upscale_factor, gigapixel_model, is_nb2
                    )
                except Exception as e:
                    print(f"[dapaoAPI] ❌ 官方 SDK 调用失败: {e}")
                    print(f"[dapaoAPI] 🔄 回退到 REST API")
                    # 继续使用 REST API
            
            if is_gemini_official:
                # Gemini 官方原生格式：使用 contents 和 parts
                print(f"[dapaoAPI] 使用 Gemini 官方原生格式")
                
                # 构建 parts 数组：文本 + 图片
                parts = [{"text": full_prompt}]
                
                for img_tensor in images:
                    # Tensor -> PIL -> Base64
                    single_image = img_tensor[0]
                    img_np = (single_image.cpu().numpy() * 255).astype(np.uint8)
                    pil_image = Image.fromarray(img_np)
                    pil_image = self._resize_image_if_needed(pil_image)
                    
                    buffered = io.BytesIO()
                    pil_image.save(buffered, format="JPEG", quality=85)
                    base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    
                    parts.append({
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64_str
                        }
                    })
                
                # Gemini 原生请求格式
                body_data = {
                    "contents": [{
                        "parts": parts
                    }]
                }
                
                # 添加 generationConfig
                generation_config = {}
                
                if response_modality == "IMAGE_ONLY":
                    generation_config["responseModalities"] = ["Image"]
                else:
                    generation_config["responseModalities"] = ["Text", "Image"]
                
                # 图像配置
                image_config = {}
                if aspect_ratio != "Auto":
                    image_config["aspectRatio"] = aspect_ratio
                if is_nb2 and output_resolution != "Auto (Model Default)":
                    image_config["imageSize"] = output_resolution
                if image_config:
                    generation_config["imageConfig"] = image_config
                
                if generation_config:
                    body_data["generationConfig"] = generation_config
                
                # 系统指令
                if system_role:
                    body_data["system_instruction"] = {
                        "parts": [{"text": system_role}]
                    }
                    
            else:
                # 代理 API：使用 OpenAI 兼容格式
                print(f"[dapaoAPI] 使用 OpenAI 兼容格式（代理）")
                
                messages = []
                if system_role:
                    messages.append({"role": "system", "content": system_role})
                
                # User Content (Text + Images)
                content_parts = [{"type": "text", "text": full_prompt}]
                
                for img_tensor in images:
                    single_image = img_tensor[0]
                    img_np = (single_image.cpu().numpy() * 255).astype(np.uint8)
                    pil_image = Image.fromarray(img_np)
                    pil_image = self._resize_image_if_needed(pil_image)
                    
                    buffered = io.BytesIO()
                    pil_image.save(buffered, format="PNG")
                    base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                    
                    content_parts.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_str}"}
                    })
                
                messages.append({"role": "user", "content": content_parts})
                
                body_data = {
                    "model": model_name,
                    "messages": messages,
                    "stream": False
                }
                
                # Gemini 特有参数
                generation_config = {}
                if response_modality == "IMAGE_ONLY":
                    generation_config["responseModalities"] = ["Image"]
                else:
                    generation_config["responseModalities"] = ["Text", "Image"]
                
                image_config = {}
                if aspect_ratio != "Auto":
                    image_config["aspectRatio"] = aspect_ratio
                if is_nb2 and output_resolution != "Auto (Model Default)":
                    image_config["imageSize"] = output_resolution
                if image_config:
                    generation_config["imageConfig"] = image_config
                    
                body_data["generationConfig"] = generation_config

        else:
            # 普通 OpenAI Edit 接口或 DALL-E
            # ... (保持原有逻辑或简化)
            # 为简单起见，这里统一使用 Chat 接口格式 (GPT-4V 风格)，因为现代多模态编辑大多支持此格式
            # 如果是旧版 DALL-E 2 Edit，需要 Multipart，这里保留旧逻辑的简化版
            
            is_dalle_edit = "dall-e-2" in model_name and ("edits" in api_url)
            
            if is_dalle_edit:
                # DALL-E Edit Logic (Multipart)
                return self._handle_dalle_edit(
                    api_url, api_key, prompt, images, model_name, 
                    key_location, key_field, timeout, extra_headers_str, extra_body_str
                )
            
            # 默认回退到 Chat 逻辑
            messages = [{"role": "user", "content": full_prompt}]
            # ... (同上，只是没有 Gemini 特有参数)
            # 重新构建简单的 Chat Body
            body_data = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": system_role or "You are a helpful assistant."},
                    {"role": "user", "content": []}
                ]
            }
            
            content_list = [{"type": "text", "text": full_prompt}]
            for img_tensor in images:
                single_image = img_tensor[0]
                img_np = (single_image.cpu().numpy() * 255).astype(np.uint8)
                pil_image = Image.fromarray(img_np)
                buffered = io.BytesIO()
                pil_image.save(buffered, format="PNG")
                base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                content_list.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{base64_str}"}
                })
            body_data["messages"][1]["content"] = content_list

        # 合并额外参数
        try:
            extra_body = json.loads(extra_body_str) if extra_body_str.strip() else {}
            body_data.update(extra_body)
        except:
            pass
            
        # Headers
        try:
            extra_headers = json.loads(extra_headers_str) if extra_headers_str.strip() else {}
        except:
            extra_headers = {}
            
        headers = {
            "Content-Type": "application/json",
            **extra_headers
        }
        
        # API Key
        if api_key:
            if key_location == "Header":
                if key_field.lower() == "authorization" and not api_key.startswith(("Bearer ", "Basic ")):
                    headers[key_field] = f"Bearer {api_key}"
                else:
                    headers[key_field] = api_key
            elif key_location == "Body":
                body_data[key_field] = api_key
        
        # 发送请求
        try:
            print(f"[dapaoAPI] 发送请求中...")
            response = requests.post(api_url, json=body_data, headers=headers, timeout=timeout)
            
            if response.status_code != 200:
                return (self._create_placeholder_image(), f"❌ API错误 ({response.status_code}): {response.text}", "", response.text)
                
            response_data = response.json()
            raw_json = json.dumps(response_data, ensure_ascii=False, indent=2)
            
            # 🔍 调试：打印响应结构
            print(f"[dapaoAPI] 响应状态码: {response.status_code}")
            print(f"[dapaoAPI] 响应长度: {len(response.text)} 字符")
            print(f"[dapaoAPI] 响应结构预览: {list(response_data.keys())}")
            
            # 如果有 choices，打印 content 的前 200 字符
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0].get("message", {}).get("content", "")
                print(f"[dapaoAPI] Content 预览: {content[:200]}...")
            
            # 提取结果
            print(f"[dapaoAPI] 开始提取图像...")
            image_tensor = self._extract_image_from_response(response_data)
            image_url = self._extract_image_url(response_data)
            
            # 提取文本响应 (作为辅助信息)
            response_text = self._extract_text_from_response(response_data)
            if not response_text:
                response_text = raw_json
                
            if image_tensor is None:
                return (self._create_placeholder_image(), f"⚠️ 未找到图像\n{response_text}", image_url, raw_json)
            
            # 4. 智能放大 (Post-Processing)
            if upscale_factor != "1x (不放大)" and smart_upscale:
                scale = int(upscale_factor.replace("x", "").split()[0])
                if scale > 1:
                    print(f"[dapaoAPI] 开始 {scale}x 智能放大...")
                    # Tensor -> PIL
                    curr_img_np = (image_tensor[0].cpu().numpy() * 255).astype(np.uint8)
                    curr_pil = Image.fromarray(curr_img_np)
                    
                    target_w = curr_pil.width * scale
                    target_h = curr_pil.height * scale
                    
                    upscaled_pil = smart_upscale(curr_pil, target_w, target_h, gigapixel_model)
                    
                    if upscaled_pil:
                        # PIL -> Tensor
                        image_np = np.array(upscaled_pil).astype(np.float32) / 255.0
                        image_tensor = torch.from_numpy(image_np).unsqueeze(0)
                        print(f"[dapaoAPI] 放大完成: {image_tensor.shape}")
                        response_text += f"\n\n✅ 已完成 {scale}x 智能放大 ({gigapixel_model})"
            
            return (image_tensor, response_text, image_url, raw_json)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return (self._create_placeholder_image(), f"❌ 执行错误: {str(e)}", "", "{}")

    def _handle_dalle_edit(self, url, key, prompt, images, model, key_loc, key_field, timeout, ex_h, ex_b):
        # 简化的 DALL-E 2 Edit 实现 (Multipart)
        # (仅作为兼容性保留，实际逻辑参考原文件)
        # 由于用户主要关注 Gemini/Nano Banana，这里暂不展开 DALL-E 具体逻辑
        return (self._create_placeholder_image(), "DALL-E Edit Legacy Mode Not Fully Implemented in V2", "", "{}")

    def _resize_image_if_needed(self, pil_image, max_pixels=1048576):
        width, height = pil_image.size
        current_pixels = width * height
        if current_pixels > max_pixels:
            ratio = (max_pixels / current_pixels) ** 0.5
            new_width = int(width * ratio)
            new_height = int(height * ratio)
            return pil_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        return pil_image

    def _call_with_official_sdk(self, api_key, model_name, prompt, images,
                                 aspect_ratio, output_resolution, response_modality,
                                 quality, style, system_role, upscale_factor, gigapixel_model, is_nb2):
        """使用 Google 官方 SDK 调用 API"""
        # 规范化模型名称（Gemini SDK 需要完整的模型 ID）
        if not model_name.startswith("models/"):
            # 移除空格和特殊字符，转换为小写
            normalized_name = model_name.lower().replace(" ", "-").replace("_", "-")
            # 如果是简短名称，添加 models/ 前缀
            model_name = f"models/{normalized_name}"
        
        print(f"[dapaoAPI] 使用模型: {model_name}")
        
        # 创建客户端
        client = genai.Client(api_key=api_key)
        
        # 构建 parts 数组
        parts = [{"text": prompt}]
        
        for img_tensor in images:
            single_image = img_tensor[0]
            img_np = (single_image.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            pil_image = self._resize_image_if_needed(pil_image)
            
            buffered = io.BytesIO()
            pil_image.save(buffered, format="JPEG", quality=85)
            base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": base64_str
                }
            })
        
        # 构建配置
        config_params = {
            'temperature': 0.7,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8192,
        }
        
        # 响应模式
        if response_modality == "IMAGE_ONLY":
            config_params['response_modalities'] = ['Image']
        else:
            config_params['response_modalities'] = ['Text', 'Image']
        
        # 图像配置
        image_config_params = {}
        if aspect_ratio != "Auto":
            image_config_params['aspect_ratio'] = aspect_ratio
        if is_nb2 and output_resolution != "Auto (Model Default)":
            image_config_params['image_size'] = output_resolution
        if image_config_params:
            config_params['image_config'] = genai_types.ImageConfig(**image_config_params)
        
        # 系统指令
        if system_role:
            config_params['system_instruction'] = system_role
        
        official_config = genai_types.GenerateContentConfig(**config_params)
        
        # 调用 API
        print(f"[dapaoAPI] 📡 调用官方 SDK...")
        response = client.models.generate_content(
            model=model_name,
            contents=[{"parts": parts}],
            config=official_config
        )
        
        # 提取图像
        image_tensor = None
        response_text = ""
        
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        # 提取文本
                        if hasattr(part, 'text') and part.text:
                            response_text += part.text
                        # 提取图像
                        elif hasattr(part, 'inline_data') and part.inline_data:
                            if hasattr(part.inline_data, 'data'):
                                data = part.inline_data.data
                                if hasattr(data, 'decode'):
                                    data = base64.b64encode(data).decode('utf-8')
                                image_tensor = self._decode_base64_to_tensor(data)
                                print(f"[dapaoAPI] ✅ 成功提取图像")
        
        # 智能放大
        if image_tensor is not None and upscale_factor and upscale_factor != "1x (不放大)" and smart_upscale:
            try:
                scale = int(upscale_factor.replace("x", "").strip().split()[0])
                if scale > 1:
                    print(f"[dapaoAPI] 🔍 开始 {scale}x 智能放大")
                    img_np = (image_tensor[0].cpu().numpy() * 255).astype(np.uint8)
                    pil_img = Image.fromarray(img_np)
                    target_w = pil_img.width * scale
                    target_h = pil_img.height * scale
                    upscaled = smart_upscale(pil_img, target_w, target_h, gigapixel_model)
                    if upscaled:
                        image_tensor = torch.from_numpy(np.array(upscaled).astype(np.float32) / 255.0).unsqueeze(0)
                        print(f"[dapaoAPI] ✅ 智能放大完成")
            except Exception as e:
                print(f"[dapaoAPI] ⚠️ 智能放大失败: {e}")
        
        if image_tensor is None:
            image_tensor = self._create_placeholder_image()
            response_text = "⚠️ 未找到图像数据"
        
        return (image_tensor, response_text, "", "")
    
    def _create_placeholder_image(self) -> torch.Tensor:
        return torch.from_numpy(np.ones((64, 64, 3), dtype=np.float32) * 0.5).unsqueeze(0)
    
    def _handle_images_edit_endpoint(self, api_url, api_key, prompt, images, model_name,
                                     key_location, key_field, timeout, extra_headers_str, extra_body_str,
                                     aspect_ratio, output_resolution, response_modality, quality, style,
                                     upscale_factor, gigapixel_model):
        """
        处理 /images/edits 端点 (使用 multipart/form-data 格式)
        参考：https://wiki.tu-zi.com/s/8c61a536-7a59-4410-a5e2-8dab3d041958/doc/2gemini-3-pro-image-preview-wCmFtI3Tm5
        """
        print(f"[dapaoAPI] 检测到 /images/edits 端点，使用 multipart/form-data 格式")
        
        # 准备 Headers
        try:
            extra_headers = json.loads(extra_headers_str) if extra_headers_str.strip() else {}
        except:
            extra_headers = {}
        
        headers = {**extra_headers}
        
        # API Key
        if api_key:
            if key_location == "Header":
                if key_field.lower() == "authorization" and not api_key.startswith(("Bearer ", "Basic ")):
                    headers[key_field] = f"Bearer {api_key}"
                else:
                    headers[key_field] = api_key
        
        # 准备 form data
        data = {
            "model": model_name,
            "prompt": prompt,
        }
        
        # 添加额外参数
        try:
            extra_body = json.loads(extra_body_str) if extra_body_str.strip() else {}
            data.update(extra_body)
        except:
            pass
        
        # 准备图片文件 (multipart/form-data)
        files = []
        for idx, img_tensor in enumerate(images):
            single_image = img_tensor[0]
            img_np = (single_image.cpu().numpy() * 255).astype(np.uint8)
            pil_image = Image.fromarray(img_np)
            
            # 将图片保存到 BytesIO
            buffered = io.BytesIO()
            pil_image.save(buffered, format="PNG")
            buffered.seek(0)
            
            # 添加到 files (第一张图片用 'image'，后续用 'image2', 'image3' 等)
            field_name = "image" if idx == 0 else f"image{idx + 1}"
            files.append((field_name, (f"image{idx + 1}.png", buffered, "image/png")))
            print(f"[dapaoAPI] 添加图片 {idx + 1}: {pil_image.size}")
        
        # 发送请求
        try:
            print(f"[dapaoAPI] 发送 multipart/form-data 请求到: {api_url}")
            print(f"[dapaoAPI] 模型: {model_name}")
            print(f"[dapaoAPI] 图片数量: {len(images)}")
            print(f"[dapaoAPI] 完整提示词:\n{prompt}")
            
            response = requests.post(
                api_url,
                headers=headers,
                data=data,
                files=files,
                timeout=timeout,
                verify=False
            )
            
            print(f"[dapaoAPI] 响应状态码: {response.status_code}")
            print(f"[dapaoAPI] 响应长度: {len(response.text)} 字符")
            
            if response.status_code != 200:
                return (self._create_placeholder_image(), f"❌ API错误 ({response.status_code}): {response.text}", "", response.text)
            
            response_data = response.json()
            raw_json = json.dumps(response_data, ensure_ascii=False, indent=2)
            
            print(f"[dapaoAPI] 响应结构: {list(response_data.keys())}")
            
            # 如果有 choices，打印 content
            if "choices" in response_data and len(response_data["choices"]) > 0:
                content = response_data["choices"][0].get("message", {}).get("content", "")
                print(f"[dapaoAPI] Content 预览: {content[:200]}...")
            
            # 提取结果
            print(f"[dapaoAPI] 开始提取图像...")
            image_tensor = self._extract_image_from_response(response_data)
            image_url = self._extract_image_url(response_data)
            response_text = self._extract_text_from_response(response_data)
            
            if not response_text:
                response_text = raw_json
            
            if image_tensor is None:
                return (self._create_placeholder_image(), f"⚠️ 未找到图像数据\n{response_text}", image_url, raw_json)
            
            # 智能放大 (如果需要)
            if upscale_factor and upscale_factor != "1x (不放大)" and smart_upscale:
                try:
                    scale = int(upscale_factor.replace("x", "").strip().split()[0])
                    if scale > 1:
                        print(f"[dapaoAPI] 开始 {scale}x 智能放大，模型: {gigapixel_model}")
                        # 转换为 PIL
                        img_np = (image_tensor[0].cpu().numpy() * 255).astype(np.uint8)
                        pil_img = Image.fromarray(img_np)
                        target_w = pil_img.width * scale
                        target_h = pil_img.height * scale
                        upscaled = smart_upscale(pil_img, target_w, target_h, gigapixel_model)
                        if upscaled:
                            image_tensor = torch.from_numpy(np.array(upscaled).astype(np.float32) / 255.0).unsqueeze(0)
                            print(f"[dapaoAPI] ✅ 智能放大完成: {upscaled.size}")
                except Exception as e:
                    print(f"[dapaoAPI] ⚠️ 智能放大失败: {e}")
            
            return (image_tensor, response_text, image_url, raw_json)
            
        except requests.exceptions.Timeout:
            return (self._create_placeholder_image(), f"⏱️ 请求超时 ({timeout}秒)", "", "")
        except Exception as e:
            import traceback
            error_msg = f"❌ 请求失败: {e}\n{traceback.format_exc()}"
            print(f"[dapaoAPI] {error_msg}")
            return (self._create_placeholder_image(), error_msg, "", "")

    def _extract_image_from_response(self, data) -> Optional[torch.Tensor]:
        # 增强的图像提取逻辑
        try:
            print(f"[dapaoAPI] 🔍 开始图像提取，响应键: {list(data.keys())}")
            
            # 1. Google Gemini 格式 (candidates.content.parts)
            if "candidates" in data:
                print(f"[dapaoAPI] ✓ 检测到 candidates 字段")
                for candidate in data["candidates"]:
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            # Inline Data
                            if "inline_data" in part:
                                b64_data = part["inline_data"].get("data", "")
                                if b64_data:
                                    print(f"[dapaoAPI] ✓ 找到 inline_data，长度: {len(b64_data)}")
                                    return self._decode_base64_to_tensor(b64_data)
                            # Image URL (rare but possible in some proxies)
                            if "image_url" in part:
                                print(f"[dapaoAPI] ✓ 找到 image_url")
                                return self._download_image_from_url(part["image_url"]["url"])
            
            # 2. OpenAI / Generic 格式
            if "data" in data and isinstance(data["data"], list):
                print(f"[dapaoAPI] ✓ 检测到 data 数组")
                item = data["data"][0]
                if "b64_json" in item:
                    print(f"[dapaoAPI] ✓ 找到 b64_json")
                    return self._decode_base64_to_tensor(item["b64_json"])
                if "url" in item:
                    print(f"[dapaoAPI] ✓ 找到 url")
                    return self._download_image_from_url(item["url"])
            
            # 3. 直接 URL 或 Base64
            if "image" in data:
                print(f"[dapaoAPI] ✓ 找到 image 字段")
                return self._decode_or_download(data["image"])
            if "images" in data and len(data["images"]) > 0:
                print(f"[dapaoAPI] ✓ 找到 images 数组")
                return self._decode_or_download(data["images"][0])
            if "url" in data:
                print(f"[dapaoAPI] ✓ 找到 url 字段")
                return self._download_image_from_url(data["url"])
            
            # 4. OpenAI Chat Completion 格式 (从 content 中提取 Markdown 图片链接)
            # 很多代理商会将 Gemini 生成的图片以 Markdown 链接形式放在 content 中
            if "choices" in data and len(data["choices"]) > 0:
                print(f"[dapaoAPI] ✓ 检测到 choices 字段")
                content = data["choices"][0].get("message", {}).get("content", "")
                print(f"[dapaoAPI] Content 长度: {len(content)}")
                if content:
                    # 匹配 Markdown 图片语法 ![alt](url)
                    import re
                    print(f"[dapaoAPI] 尝试匹配 Markdown 图片...")
                    # 优先匹配 markdown 图片链接
                    match = re.search(r'!\[.*?\]\((.*?)\)', content)
                    if match:
                        image_url = match.group(1)
                        print(f"[dapaoAPI] ✓ 从Markdown中提取到图片URL: {image_url[:80]}...")
                        result = self._download_image_from_url(image_url)
                        if result is not None:
                            print(f"[dapaoAPI] ✓ 图片下载成功")
                            return result
                        else:
                            print(f"[dapaoAPI] ✗ 图片下载失败")
                    else:
                        print(f"[dapaoAPI] ✗ 未匹配到 Markdown 格式")
                    
                    # 其次匹配任意 https:// URL (支持各种图床域名)
                    print(f"[dapaoAPI] 尝试匹配通用 URL...")
                    if "https://" in content or "http://" in content:
                        # 更宽松的匹配，支持各种图床域名
                        # 匹配 http(s)://... 直到遇到空格、右括号、引号等
                        url_match = re.search(r'(https?://[^\s\)\]\"\'\<\>]+)', content)
                        if url_match:
                            image_url = url_match.group(1)
                            # 清理可能跟随的标点符号
                            image_url = image_url.rstrip(').,;:!?\"\']')
                            print(f"[dapaoAPI] ✓ 提取到图片URL: {image_url}")
                            result = self._download_image_from_url(image_url)
                            if result is not None:
                                print(f"[dapaoAPI] ✓ 图片下载成功")
                                return result
                            else:
                                print(f"[dapaoAPI] ✗ 图片下载失败")
                        else:
                            print(f"[dapaoAPI] ✗ 未匹配到 URL")
                    else:
                        print(f"[dapaoAPI] ✗ Content 中不包含 http(s) 链接")

            print(f"[dapaoAPI] ✗ 所有提取方法均失败")
            return None
        except Exception as e:
            print(f"[dapaoAPI] ❌ 图像提取异常: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_text_from_response(self, data) -> str:
        try:
            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0].get("message", {}).get("content", "")
            if "candidates" in data and len(data["candidates"]) > 0:
                parts = data["candidates"][0].get("content", {}).get("parts", [])
                text_parts = [p.get("text", "") for p in parts if "text" in p]
                return "\n".join(text_parts)
            return ""
        except:
            return ""

    def _extract_image_url(self, data) -> str:
        # 简化版URL提取
        try:
            if "data" in data and isinstance(data["data"], list):
                return data["data"][0].get("url", "")
            
            # 尝试从 Markdown 内容中提取
            if "choices" in data and len(data["choices"]) > 0:
                content = data["choices"][0].get("message", {}).get("content", "")
                if content:
                    import re
                    match = re.search(r'!\[.*?\]\((.*?)\)', content)
                    if match:
                        return match.group(1)
            
            return data.get("url", "") or data.get("image_url", "")
        except:
            return ""

    def _decode_base64_to_tensor(self, b64_str) -> torch.Tensor:
        if "," in b64_str: b64_str = b64_str.split(",")[1]
        img_bytes = base64.b64decode(b64_str)
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        return torch.from_numpy(np.array(img).astype(np.float32) / 255.0).unsqueeze(0)

    def _download_image_from_url(self, url) -> torch.Tensor:
        try:
            print(f"[dapaoAPI] 🌐 开始下载图片: {url}")
            resp = requests.get(url, timeout=60, verify=False)  # 有些代理可能有SSL问题
            print(f"[dapaoAPI] 📥 下载状态码: {resp.status_code}, 大小: {len(resp.content)} bytes")
            
            if resp.status_code != 200:
                print(f"[dapaoAPI] ❌ 下载失败，状态码: {resp.status_code}")
                return None
                
            img = Image.open(io.BytesIO(resp.content)).convert("RGB")
            print(f"[dapaoAPI] ✅ 图片解析成功: {img.size}")
            tensor = torch.from_numpy(np.array(img).astype(np.float32) / 255.0).unsqueeze(0)
            print(f"[dapaoAPI] ✅ 转换为Tensor成功: {tensor.shape}")
            return tensor
        except Exception as e:
            print(f"[dapaoAPI] ❌ 图片下载/解析失败: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def _decode_or_download(self, data) -> torch.Tensor:
        if data.startswith("http"): return self._download_image_from_url(data)
        return self._decode_base64_to_tensor(data)

# 节点注册
NODE_CLASS_MAPPINGS = {
    "ImageEditAPINode": ImageEditAPINode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ImageEditAPINode": "🎨通用图像编辑API (测试版) @炮老师的小课堂",
}
