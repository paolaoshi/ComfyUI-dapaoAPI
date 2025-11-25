"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌐 通用API调用节点（测试版）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 支持调用任何HTTP API
   - 灵活的请求方法(GET/POST/PUT/DELETE)
   - 自定义Headers和请求体
   - JSON格式的请求和响应
   - 支持 Gemini 官方 API（自动使用 SDK）

🔧 技术特性：
   - 基于 requests 库
   - 支持超时设置
   - 完整的错误处理
   - 响应数据提取
   - 智能适配第三方和官方API

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v2.1.0 (测试版)
🎨 主题：蓝色 (#4A90E2)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import requests
import base64
import io
import torch
import numpy as np
from PIL import Image
from typing import Tuple, Optional

from .gemini3_client import encode_image_tensor
from .gemini3_file_client import GeminiFileClient, save_audio_to_file

# 尝试导入 Google 官方 SDK（可选）
try:
    from google import genai
    from google.genai import types as genai_types
    GOOGLE_SDK_AVAILABLE = True
    print("[dapaoAPI-Universal] ✅ Google Genai SDK 可用")
except ImportError:
    GOOGLE_SDK_AVAILABLE = False
    print("[dapaoAPI-Universal] ⚠️ Google Genai SDK 未安装，将使用 REST API")

# 节点颜色 (蓝色)
NODE_COLOR = "#4A90E2"


class UniversalAPINode:
    """
    通用API调用节点
    
    支持调用任何HTTP API,用户可以自定义:
    - API地址
    - API密钥
    - 请求方法
    - 请求体
    - Headers
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "你是一个专业的AI助手",
                    "placeholder": "定义AI的角色和行为方式..."
                }),
                
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "请分析这个内容",
                    "placeholder": "输入你的问题或指令..."
                }),
                
                "🤖 模型名称": ("STRING", {
                    "default": "gpt-4-vision-preview",
                    "placeholder": "如: gpt-4-vision-preview, claude-3-opus"
                }),
                
                "🌐 API地址": ("STRING", {
                    "default": "https://api.openai.com/v1/chat/completions",
                    "placeholder": "输入完整的API URL（需包含完整路径）"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "输入你的API密钥"
                }),
                
                "📡 请求方法": (["POST", "GET", "PUT", "DELETE"], {
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
                "🎬 视频": ("IMAGE",),
                "🎵 音频": ("AUDIO",),
                
                "🎬 视频文件路径": ("STRING", {
                    "default": "",
                    "placeholder": "输入视频文件完整路径 (mp4/mov/avi等)"
                }),
                "🎵 音频文件路径": ("STRING", {
                    "default": "",
                    "placeholder": "输入音频文件完整路径 (mp3/wav/m4a等)"
                }),
                
                "🎯 响应提取路径": ("STRING", {
                    "default": "",
                    "placeholder": "如: data.result.text (留空返回完整响应)"
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
                
                "📦 额外Body字段": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "JSON格式的额外Body字段，如: {\"response_format\": \"b64_json\"}"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING", "IMAGE")
    RETURN_NAMES = ("AI回复", "response", "raw_json", "image")
    FUNCTION = "call_api"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "通用API调用节点 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.color = NODE_COLOR
        self.bgcolor = NODE_COLOR
    
    def call_api(
        self,
        **kwargs
    ) -> Tuple[str, str, str, Optional[torch.Tensor]]:
        """调用API"""
        # 提取参数
        system_role = kwargs.get("🎯 系统角色", "")
        user_input = kwargs.get("💬 用户输入", "")
        model_name = kwargs.get("🤖 模型名称", "gpt-4-vision-preview")
        api_url = kwargs.get("🌐 API地址", "")
        api_key = kwargs.get("🔑 API密钥", "")
        method = kwargs.get("📡 请求方法", "POST")
        key_location = kwargs.get("🔐 密钥位置", "Header")
        key_field = kwargs.get("📝 密钥字段名", "Authorization")
        extract_path = kwargs.get("🎯 响应提取路径", "")
        timeout = kwargs.get("⏱️ 超时时间", 180)
        extra_headers_str = kwargs.get("📋 额外Headers", "{}")
        extra_body_str = kwargs.get("📦 额外Body字段", "{}")
        
        # 多模态输入
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        video = kwargs.get("🎬 视频")
        audio = kwargs.get("🎵 音频")
        video_path = kwargs.get("🎬 视频文件路径", "").strip()
        audio_path = kwargs.get("🎵 音频文件路径", "").strip()
        
        print(f"[dapaoAPI-Universal] API地址: {api_url}")
        print(f"[dapaoAPI-Universal] 模型名称: {model_name}")
        print(f"[dapaoAPI-Universal] 请求方法: {method}")
        print(f"[dapaoAPI-Universal] 密钥位置: {key_location}")
        
        # 验证API地址
        if not api_url or not api_url.startswith(("http://", "https://")):
            error_msg = "❌ 错误：请输入有效的API地址"
            placeholder = self._create_placeholder_image()
            return (error_msg, error_msg, "{}", placeholder)
        
        # 收集所有图像
        images = [img for img in [image1, image2, image3, image4] if img is not None]
        
        # 🔍 检测 Gemini 官方 API
        is_gemini_official = "generativelanguage.googleapis.com" in api_url
        
        # 如果是 Gemini 官方且 SDK 可用，优先使用 SDK
        if is_gemini_official and GOOGLE_SDK_AVAILABLE:
            print(f"[dapaoAPI-Universal] 🚀 检测到 Gemini 官方 API，使用 SDK")
            try:
                return self._call_gemini_official_sdk(
                    api_key, model_name, system_role, user_input, images, video, audio
                )
            except Exception as e:
                print(f"[dapaoAPI-Universal] ❌ SDK 调用失败: {e}")
                print(f"[dapaoAPI-Universal] 🔄 回退到 REST API")
                # 继续使用 REST API
        
        # 根据 API 地址自动判断请求类型
        # 图像编辑端点（需要 multipart/form-data）
        is_image_edit_endpoint = "/images/edits" in api_url or "/images/edit" in api_url
        # 图像生成端点（JSON 格式）
        is_image_generation_endpoint = "/images/generations" in api_url or "/images/generation" in api_url
        # 对话端点（JSON 格式）
        is_chat_endpoint = "/chat/completions" in api_url or "/chat" in api_url or "/completions" in api_url
        
        print(f"[dapaoAPI-Universal] 端点类型检测:")
        print(f"  - API地址: {api_url}")
        print(f"  - 图像编辑: {is_image_edit_endpoint}")
        print(f"  - 图像生成: {is_image_generation_endpoint}")
        print(f"  - 对话: {is_chat_endpoint}")
        print(f"  - 图像数量: {len(images)}")
        
        # 根据端点类型构建请求体
        if is_image_edit_endpoint:
            # 图像编辑端点 - 使用 multipart/form-data
            print(f"[dapaoAPI-Universal] 使用图像编辑模式（multipart/form-data）")
            body_data = None
            use_multipart = True
            
        elif is_image_generation_endpoint:
            # 图像生成端点 - 使用 JSON
            print(f"[dapaoAPI-Universal] 使用图像生成模式（JSON）")
            body_data = {
                "prompt": user_input,
                "model": model_name,
                "response_format": "url",
                "n": 1
            }
            use_multipart = False
            
            # 添加可选参数（如果有图像输入，可能是图生图）
            if images:
                print(f"[dapaoAPI-Universal] 添加参考图像")
                first_image = images[0][0]  # [B, H, W, C] -> [H, W, C]
                image_base64 = encode_image_tensor(first_image)
                body_data["image"] = image_base64
                
        else:
            # 默认使用对话模式 - 使用 JSON
            print(f"[dapaoAPI-Universal] 使用对话模式（JSON）")
            use_multipart = False
            body_data = {
                "model": model_name,
                "messages": []
            }
            
            # 添加系统角色
            if system_role.strip():
                body_data["messages"].append({
                    "role": "system",
                    "content": system_role
                })
            
            # 构建用户消息内容
            user_content = []
            
            # 添加图像（base64编码）
            if images:
                print(f"[dapaoAPI-Universal] 处理 {len(images)} 个图像")
                for img_tensor in images:
                    batch_size = img_tensor.shape[0]
                    for i in range(batch_size):
                        single_image = img_tensor[i]
                        image_base64 = encode_image_tensor(single_image)
                        user_content.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        })
            
            # 添加视频（优先使用文件路径）
            if video_path and os.path.exists(video_path):
                print(f"[dapaoAPI-Universal] 读取视频文件: {video_path}")
                try:
                    import cv2
                    # 读取视频并采样关键帧
                    cap = cv2.VideoCapture(video_path)
                    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                    step = max(1, total_frames // 10)
                    
                    for i in range(0, total_frames, step):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                        ret, frame = cap.read()
                        if ret:
                            # 转换为 RGB
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            pil_image = Image.fromarray(frame_rgb)
                            
                            buffered = io.BytesIO()
                            pil_image.save(buffered, format="JPEG", quality=85)
                            base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                            
                            user_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_str}"
                                }
                            })
                    cap.release()
                    print(f"[dapaoAPI-Universal] 视频帧处理完成")
                except ImportError:
                    print(f"[dapaoAPI-Universal] 需要安装 opencv-python: pip install opencv-python")
                except Exception as e:
                    print(f"[dapaoAPI-Universal] 视频处理失败: {e}")
            elif video is not None:
                # 回退到视频帧处理
                print(f"[dapaoAPI-Universal] 处理视频帧")
                batch_size = video.shape[0]
                step = max(1, batch_size // 10)
                for i in range(0, batch_size, step):
                    frame = video[i]
                    image_base64 = encode_image_tensor(frame)
                    user_content.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_base64}"
                        }
                    })
            
            # 添加音频（优先使用文件路径）
            if audio_path and os.path.exists(audio_path):
                print(f"[dapaoAPI-Universal] 读取音频文件: {audio_path}")
                try:
                    # 直接读取文件并编码为 base64
                    with open(audio_path, 'rb') as f:
                        audio_data = f.read()
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    # 获取文件扩展名
                    ext = os.path.splitext(audio_path)[1].lower()
                    format_map = {
                        '.mp3': 'mp3',
                        '.wav': 'wav',
                        '.m4a': 'm4a',
                        '.ogg': 'ogg',
                        '.flac': 'flac'
                    }
                    audio_format = format_map.get(ext, 'mp3')
                    
                    user_content.append({
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_base64,
                            "format": audio_format
                        }
                    })
                    print(f"[dapaoAPI-Universal] 音频文件处理完成 ({audio_format})")
                except Exception as e:
                    print(f"[dapaoAPI-Universal] 音频文件读取失败: {e}")
            elif audio is not None:
                # 回退到 tensor 处理
                print(f"[dapaoAPI-Universal] 处理音频 tensor")
                try:
                    from .gemini3_client import encode_audio_tensor
                    audio_base64 = encode_audio_tensor(audio)
                    user_content.append({
                        "type": "input_audio",
                        "input_audio": {
                            "data": audio_base64,
                            "format": "wav"
                        }
                    })
                except Exception as e:
                    print(f"[dapaoAPI-Universal] 音频编码失败: {e}")
            
            # 添加文本
            user_content.append({
                "type": "text",
                "text": user_input
            })
            
            # 添加用户消息
            body_data["messages"].append({
                "role": "user",
                "content": user_content if len(user_content) > 1 else user_input
            })
        
        # 解析额外Headers
        try:
            extra_headers = json.loads(extra_headers_str) if extra_headers_str.strip() else {}
        except json.JSONDecodeError:
            extra_headers = {}
        
        # 构建Headers（multipart 模式不设置 Content-Type，让 requests 自动处理）
        if use_multipart:
            headers = {**extra_headers}
        else:
            headers = {
                "Content-Type": "application/json",
                **extra_headers
            }
        
        # 根据密钥位置添加API密钥
        params = {}
        if api_key:
            if key_location == "Header":
                # 处理Authorization特殊情况
                if key_field.lower() == "authorization" and not api_key.startswith(("Bearer ", "Basic ")):
                    headers[key_field] = f"Bearer {api_key}"
                else:
                    headers[key_field] = api_key
            elif key_location == "Query":
                params[key_field] = api_key
            elif key_location == "Body":
                # 如果不是 multipart 模式，添加到 body_data
                if not use_multipart and body_data is not None:
                    body_data[key_field] = api_key
        
        # 解析额外Body字段
        try:
            extra_body = json.loads(extra_body_str) if extra_body_str.strip() else {}
        except json.JSONDecodeError:
            print(f"[dapaoAPI-Universal] 额外Body字段解析失败，使用空字典")
            extra_body = {}
        
        # 准备 multipart/form-data 数据（如果需要）
        files = None
        data = None
        if use_multipart:
            print(f"[dapaoAPI-Universal] 准备 multipart/form-data 数据...")
            
            # 准备文本字段（基础字段）
            data = {
                "prompt": user_input,
            }
            
            # 添加模型名称（如果有）
            if model_name:
                data["model"] = model_name
            
            # 如果没有额外Body字段，且是图像编辑端点，添加默认的 response_format
            if not extra_body and is_image_edit_endpoint:
                extra_body = {"response_format": "b64_json"}
                print(f"[dapaoAPI-Universal] 自动添加 response_format: b64_json")
            
            # 合并额外Body字段（用户可以通过这个添加 response_format 等字段）
            data.update(extra_body)
            
            # 如果 API 密钥在 Body 中，添加到 data
            if api_key and key_location == "Body":
                data[key_field] = api_key
            
            # 准备图像文件（使用 BytesIO 对象，但不要 seek，让 requests 自己处理）
            files = []  # 改用列表格式，支持多个同名字段
            if images:
                print(f"[dapaoAPI-Universal] 添加 {len(images)} 个图像到 multipart")
                
                # 第一张图像 - 使用 'image' 字段（通用格式）
                img_tensor = images[0]
                single_image = img_tensor[0]  # [H, W, C]
                
                # 转换为 PIL Image
                img_np = (single_image.cpu().numpy() * 255).astype(np.uint8)
                pil_image = Image.fromarray(img_np)
                
                # 转换为字节流（保持 BytesIO 对象，模拟文件对象）
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                img_size = img_byte_arr.tell()  # 获取大小
                img_byte_arr.seek(0)  # 重置到开头
                
                # 添加到 files（使用 BytesIO 对象，模拟 open() 返回的文件对象）
                files.append(('image', ('image.png', img_byte_arr, 'image/png')))
                print(f"[dapaoAPI-Universal] 图像1大小: {img_size} 字节")
                
                # 第二张图像 - 使用 'mask' 字段（如果有）
                if len(images) > 1:
                    print(f"[dapaoAPI-Universal] 添加第二张图像作为 mask")
                    mask_tensor = images[1]
                    mask_image = mask_tensor[0]  # [H, W, C]
                    
                    # 转换为 PIL Image
                    mask_np = (mask_image.cpu().numpy() * 255).astype(np.uint8)
                    pil_mask = Image.fromarray(mask_np)
                    
                    # 转换为字节流
                    mask_byte_arr = io.BytesIO()
                    pil_mask.save(mask_byte_arr, format='PNG')
                    mask_size = mask_byte_arr.tell()
                    mask_byte_arr.seek(0)
                    
                    # 添加 mask 字段
                    files.append(('mask', ('mask.png', mask_byte_arr, 'image/png')))
                    print(f"[dapaoAPI-Universal] mask大小: {mask_size} 字节")
                
                # 第三、四张图像 - 使用 'image2', 'image3' 字段（某些平台可能支持多图）
                if len(images) > 2:
                    print(f"[dapaoAPI-Universal] 添加第三张图像")
                    img3_tensor = images[2]
                    img3 = img3_tensor[0]
                    img3_np = (img3.cpu().numpy() * 255).astype(np.uint8)
                    pil_img3 = Image.fromarray(img3_np)
                    img3_byte_arr = io.BytesIO()
                    pil_img3.save(img3_byte_arr, format='PNG')
                    img3_size = img3_byte_arr.tell()
                    img3_byte_arr.seek(0)
                    files.append(('image2', ('image2.png', img3_byte_arr, 'image/png')))
                    print(f"[dapaoAPI-Universal] 图像3大小: {img3_size} 字节")
                
                if len(images) > 3:
                    print(f"[dapaoAPI-Universal] 添加第四张图像")
                    img4_tensor = images[3]
                    img4 = img4_tensor[0]
                    img4_np = (img4.cpu().numpy() * 255).astype(np.uint8)
                    pil_img4 = Image.fromarray(img4_np)
                    img4_byte_arr = io.BytesIO()
                    pil_img4.save(img4_byte_arr, format='PNG')
                    img4_size = img4_byte_arr.tell()
                    img4_byte_arr.seek(0)
                    files.append(('image3', ('image3.png', img4_byte_arr, 'image/png')))
                    print(f"[dapaoAPI-Universal] 图像4大小: {img4_size} 字节")
            
            # 打印调试信息
            print(f"[dapaoAPI-Universal] multipart data 字段: {list(data.keys())}")
            print(f"[dapaoAPI-Universal] multipart files 数量: {len(files) if files else 0}")
            if files:
                print(f"[dapaoAPI-Universal] multipart files 字段名: {[f[0] for f in files]}")
        
        # 发送请求
        try:
            print(f"[dapaoAPI-Universal] 发送请求...")
            
            if method == "GET":
                response = requests.get(
                    api_url,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
            elif method == "POST":
                if use_multipart:
                    # multipart/form-data 请求
                    response = requests.post(
                        api_url,
                        data=data,
                        files=files,
                        params=params,
                        headers=headers,
                        timeout=timeout
                    )
                else:
                    # JSON 请求
                    response = requests.post(
                        api_url,
                        json=body_data,
                        params=params,
                        headers=headers,
                        timeout=timeout
                    )
            elif method == "PUT":
                if use_multipart:
                    response = requests.put(
                        api_url,
                        data=data,
                        files=files,
                        params=params,
                        headers=headers,
                        timeout=timeout
                    )
                else:
                    response = requests.put(
                        api_url,
                        json=body_data,
                        params=params,
                        headers=headers,
                        timeout=timeout
                    )
            elif method == "DELETE":
                response = requests.delete(
                    api_url,
                    params=params,
                    headers=headers,
                    timeout=timeout
                )
            else:
                error_msg = f"❌ 错误：不支持的请求方法 {method}"
                placeholder = self._create_placeholder_image()
                return (error_msg, "{}", "{}", placeholder)
            
            print(f"[dapaoAPI-Universal] 响应状态码: {response.status_code}")
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"❌ API错误 ({response.status_code}): {response.text}"
                print(f"[dapaoAPI-Universal] {error_msg}")
                print(f"[dapaoAPI-Universal] 请求详情:")
                print(f"  - URL: {api_url}")
                print(f"  - Method: {method}")
                print(f"  - Headers: {headers}")
                if use_multipart:
                    print(f"  - Multipart Data: {data}")
                    print(f"  - Multipart Files: {[f[0] for f in files] if files else 'None'}")
                else:
                    print(f"  - JSON Body: {body_data}")
                placeholder = self._create_placeholder_image()
                return (error_msg, response.text, response.text, placeholder)
            
            # 解析响应
            try:
                response_data = response.json()
                raw_json = json.dumps(response_data, ensure_ascii=False, indent=2)
                
                # 提取指定路径的数据
                if extract_path:
                    extracted_data = self._extract_from_path(response_data, extract_path)
                    if extracted_data is not None:
                        result = str(extracted_data)
                    else:
                        result = f"⚠️ 警告：未找到路径 '{extract_path}'\n\n完整响应:\n{raw_json}"
                else:
                    result = raw_json
                
                print(f"[dapaoAPI-Universal] 响应长度: {len(result)} 字符")
                
                # 提取AI回复内容
                ai_reply = self._extract_ai_reply(response_data)
                
                # 尝试提取图像
                image_tensor = self._extract_image_from_response(response_data)
                
                # 如果没有图像，创建空白占位图像
                if image_tensor is None:
                    image_tensor = self._create_placeholder_image()
                
                return (ai_reply, result, raw_json, image_tensor)
                
            except json.JSONDecodeError:
                # 如果响应不是JSON,直接返回文本
                placeholder = self._create_placeholder_image()
                return (response.text, response.text, response.text, placeholder)
        
        except requests.exceptions.Timeout:
            error_msg = f"❌ 错误：请求超时 ({timeout}秒)"
            print(f"[dapaoAPI-Universal] {error_msg}")
            placeholder = self._create_placeholder_image()
            return (error_msg, error_msg, "{}", placeholder)
        
        except requests.exceptions.ConnectionError as e:
            error_msg = f"❌ 错误：连接失败\n{str(e)}"
            print(f"[dapaoAPI-Universal] {error_msg}")
            placeholder = self._create_placeholder_image()
            return (error_msg, error_msg, "{}", placeholder)
        
        except Exception as e:
            error_msg = f"❌ 未知错误: {str(e)}"
            print(f"[dapaoAPI-Universal] {error_msg}")
            placeholder = self._create_placeholder_image()
            return (error_msg, error_msg, "{}", placeholder)
    
    def _extract_from_path(self, data, path: str):
        """从嵌套字典中提取数据
        
        例如: path = "data.result.text"
        会提取 data['data']['result']['text']
        """
        if not path:
            return data
        
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _extract_ai_reply(self, data) -> str:
        """从API响应中提取AI的实际回复内容
        
        支持多种常见的API响应格式:
        1. OpenAI格式: choices[0].message.content
        2. 简单格式: {"reply": "..."}
        3. 其他格式: {"result": "..."}
        """
        try:
            # OpenAI标准格式: choices[0].message.content
            if isinstance(data, dict) and "choices" in data:
                if isinstance(data["choices"], list) and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        content = choice["message"]["content"]
                        print(f"[dapaoAPI-Universal] 提取AI回复成功: {len(content)} 字符")
                        return content
            
            # 其他常见格式
            if isinstance(data, dict):
                # reply 字段
                if "reply" in data:
                    return str(data["reply"])
                # result 字段
                elif "result" in data:
                    return str(data["result"])
                # text 字段
                elif "text" in data:
                    return str(data["text"])
                # response 字段
                elif "response" in data:
                    return str(data["response"])
            
            # 如果无法提取，返回完整JSON
            print(f"[dapaoAPI-Universal] 无法提取AI回复，返回完整响应")
            return json.dumps(data, ensure_ascii=False, indent=2)
            
        except Exception as e:
            print(f"[dapaoAPI-Universal] AI回复提取失败: {e}")
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _extract_image_from_response(self, data) -> Optional[torch.Tensor]:
        """从响应中提取图像
        
        支持多种常见的API响应格式:
        1. {"data": [{"url": "http://..."}, {"b64_json": "..."}]}
        2. {"images": ["base64..."]}
        3. {"image": "base64..."}
        4. {"result": {"image": "base64..."}}
        5. Gemini: {"candidates": [{"content": {"parts": [{"inlineData": {"data": "..."}}]}}]}
        """
        try:
            print(f"[dapaoAPI-Universal] 开始提取图像...")
            print(f"[dapaoAPI-Universal] 响应数据类型: {type(data)}")
            
            # 尝试多种可能的路径
            image_data = None
            
            # Gemini 格式: candidates[0].content.parts[0].inlineData.data
            if isinstance(data, dict) and "candidates" in data:
                print(f"[dapaoAPI-Universal] 检测到 Gemini 'candidates' 字段")
                if isinstance(data["candidates"], list) and len(data["candidates"]) > 0:
                    candidate = data["candidates"][0]
                    if "content" in candidate and isinstance(candidate["content"], dict):
                        content = candidate["content"]
                        if "parts" in content and isinstance(content["parts"], list):
                            for part in content["parts"]:
                                if isinstance(part, dict) and "inlineData" in part:
                                    inline_data = part["inlineData"]
                                    if "data" in inline_data:
                                        image_data = inline_data["data"]
                                        print(f"[dapaoAPI-Universal] 找到 Gemini inlineData.data 字段")
                                        break
            
            # OpenAI DALL-E 格式: data[0].b64_json
            if not image_data and isinstance(data, dict) and "data" in data:
                print(f"[dapaoAPI-Universal] 检测到 'data' 字段")
                if isinstance(data["data"], list) and len(data["data"]) > 0:
                    first_item = data["data"][0]
                    print(f"[dapaoAPI-Universal] data[0] 字段: {list(first_item.keys()) if isinstance(first_item, dict) else type(first_item)}")
                    if "b64_json" in first_item:
                        image_data = first_item["b64_json"]
                        print(f"[dapaoAPI-Universal] 找到 b64_json 字段")
                    elif "url" in first_item:
                        image_url = first_item["url"]
                        print(f"[dapaoAPI-Universal] 检测到图像URL，开始下载: {image_url[:100]}...")
                        return self._download_image_from_url(image_url)
            
            # 其他常见格式
            if not image_data:
                print(f"[dapaoAPI-Universal] 尝试其他格式...")
                # images 数组
                if "images" in data and isinstance(data["images"], list) and len(data["images"]) > 0:
                    image_data = data["images"][0]
                    print(f"[dapaoAPI-Universal] 找到 images 数组")
                # image 字段
                elif "image" in data:
                    image_data = data["image"]
                    print(f"[dapaoAPI-Universal] 找到 image 字段")
                # result.image
                elif "result" in data and isinstance(data["result"], dict) and "image" in data["result"]:
                    image_data = data["result"]["image"]
                    print(f"[dapaoAPI-Universal] 找到 result.image 字段")
            
            if not image_data:
                print(f"[dapaoAPI-Universal] 未找到图像数据，响应字段: {list(data.keys()) if isinstance(data, dict) else 'not a dict'}")
                return None
            
            # 解码base64图像
            print(f"[dapaoAPI-Universal] 检测到图像数据，开始解码...")
            
            # 移除可能的data:image前缀
            if isinstance(image_data, str):
                if image_data.startswith("data:image"):
                    image_data = image_data.split(",", 1)[1]
                
                # 解码base64
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
                
                # 转换为RGB
                if image.mode != "RGB":
                    image = image.convert("RGB")
                
                # 转换为tensor [1, H, W, 3]
                image_np = np.array(image).astype(np.float32) / 255.0
                image_tensor = torch.from_numpy(image_np).unsqueeze(0)
                
                print(f"[dapaoAPI-Universal] 图像解码成功: {image_tensor.shape}")
                return image_tensor
            
            print(f"[dapaoAPI-Universal] 图像数据类型不支持: {type(image_data)}")
            return None
            
        except Exception as e:
            print(f"[dapaoAPI-Universal] 图像提取失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _call_gemini_official_sdk(self, api_key, model_name, system_role, user_input, images, video, audio):
        """使用 Google 官方 SDK 调用 Gemini API"""
        # 规范化模型名称（Gemini SDK 需要完整的模型 ID）
        if not model_name.startswith("models/"):
            # 移除空格和特殊字符，转换为小写
            normalized_name = model_name.lower().replace(" ", "-").replace("_", "-")
            # 如果是简短名称，添加 models/ 前缀
            model_name = f"models/{normalized_name}"
        
        print(f"[dapaoAPI-Universal] 使用模型: {model_name}")
        
        # 创建客户端
        client = genai.Client(api_key=api_key)
        
        # 构建 parts 数组
        parts = []
        
        # 添加图像
        if images:
            print(f"[dapaoAPI-Universal] 处理 {len(images)} 个图像")
            for img_tensor in images:
                single_image = img_tensor[0]
                img_np = (single_image.cpu().numpy() * 255).astype(np.uint8)
                pil_image = Image.fromarray(img_np)
                
                buffered = io.BytesIO()
                pil_image.save(buffered, format="JPEG", quality=85)
                base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_str
                    }
                })
        
        # 添加视频帧
        if video is not None:
            print(f"[dapaoAPI-Universal] 处理视频帧")
            batch_size = video.shape[0]
            step = max(1, batch_size // 10)
            for i in range(0, batch_size, step):
                frame = video[i]
                img_np = (frame.cpu().numpy() * 255).astype(np.uint8)
                pil_image = Image.fromarray(img_np)
                
                buffered = io.BytesIO()
                pil_image.save(buffered, format="JPEG", quality=85)
                base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": base64_str
                    }
                })
        
        # 添加音频（使用 File API）
        if audio is not None:
            print(f"[dapaoAPI-Universal] 处理音频")
            try:
                import asyncio
                # 保存音频为临时文件
                temp_audio_path = save_audio_to_file(audio)
                print(f"[dapaoAPI-Universal] 音频保存到: {temp_audio_path}")
                
                # 使用 File API 上传
                file_client = GeminiFileClient(api_key, "google")
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    file_uri = loop.run_until_complete(file_client.upload_file(temp_audio_path))
                    parts.append({
                        "file_data": {
                            "mime_type": "audio/wav",
                            "file_uri": file_uri
                        }
                    })
                    print(f"[dapaoAPI-Universal] 音频上传成功: {file_uri}")
                finally:
                    loop.close()
                
                # 清理临时文件
                try:
                    import os
                    os.remove(temp_audio_path)
                except:
                    pass
            except Exception as e:
                print(f"[dapaoAPI-Universal] 音频处理失败: {e}")
        
        # 添加文本
        parts.append({"text": user_input})
        
        # 构建配置
        config_params = {
            'temperature': 0.7,
            'top_p': 0.95,
            'top_k': 40,
            'max_output_tokens': 8192,
        }
        
        # 系统指令
        if system_role:
            config_params['system_instruction'] = system_role
        
        official_config = genai_types.GenerateContentConfig(**config_params)
        
        # 调用 API
        print(f"[dapaoAPI-Universal] 📡 调用官方 SDK...")
        response = client.models.generate_content(
            model=model_name,
            contents=[{"parts": parts}],
            config=official_config
        )
        
        # 提取响应
        ai_reply = ""
        image_tensor = None
        
        if hasattr(response, 'candidates') and response.candidates:
            for candidate in response.candidates:
                if hasattr(candidate, 'content') and candidate.content and hasattr(candidate.content, 'parts'):
                    for part in candidate.content.parts:
                        # 提取文本
                        if hasattr(part, 'text') and part.text:
                            ai_reply += part.text
                        # 提取图像
                        elif hasattr(part, 'inline_data') and part.inline_data:
                            try:
                                print(f"[dapaoAPI-Universal] 检测到 inline_data")
                                if hasattr(part.inline_data, 'data'):
                                    data = part.inline_data.data
                                    print(f"[dapaoAPI-Universal] inline_data.data 类型: {type(data)}")
                                    
                                    # 如果是 bytes 类型,直接使用
                                    if isinstance(data, bytes):
                                        image_bytes = data
                                    # 如果是 str 类型,需要 base64 解码
                                    elif isinstance(data, str):
                                        image_bytes = base64.b64decode(data)
                                    else:
                                        print(f"[dapaoAPI-Universal] 未知的 data 类型: {type(data)}")
                                        continue
                                    
                                    # 解码图像
                                    pil_image = Image.open(io.BytesIO(image_bytes))
                                    if pil_image.mode != "RGB":
                                        pil_image = pil_image.convert("RGB")
                                    image_np = np.array(pil_image).astype(np.float32) / 255.0
                                    image_tensor = torch.from_numpy(image_np).unsqueeze(0)
                                    print(f"[dapaoAPI-Universal] ✅ 成功提取图像: {image_tensor.shape}")
                            except Exception as e:
                                print(f"[dapaoAPI-Universal] 图像提取失败: {e}")
                                import traceback
                                traceback.print_exc()
        
        if image_tensor is None:
            image_tensor = self._create_placeholder_image()
        
        # 构建响应数据
        response_data = {
            "ai_reply": ai_reply,
            "success": True
        }
        raw_json = json.dumps(response_data, ensure_ascii=False, indent=2)
        
        return (ai_reply, ai_reply, raw_json, image_tensor)
    
    def _create_placeholder_image(self) -> torch.Tensor:
        """创建空白占位图像
        
        当API没有返回图像时，返回一个小的空白图像以避免错误
        """
        print(f"[dapaoAPI-Universal] 创建空白占位图像")
        # 创建一个 64x64 的灰色图像 [1, 64, 64, 3]
        placeholder = np.ones((64, 64, 3), dtype=np.float32) * 0.5  # 灰色
        return torch.from_numpy(placeholder).unsqueeze(0)
    
    def _download_image_from_url(self, url: str) -> Optional[torch.Tensor]:
        """从URL下载图像并转换为tensor
        
        Args:
            url: 图像URL地址
            
        Returns:
            图像tensor [1, H, W, 3] 或 None
        """
        try:
            print(f"[dapaoAPI-Universal] 正在下载图像...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            print(f"[dapaoAPI-Universal] 图像下载完成，大小: {len(response.content)} 字节")
            
            # 从响应内容创建图像
            image = Image.open(io.BytesIO(response.content))
            
            # 转换为RGB
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            # 转换为tensor [1, H, W, 3]
            image_np = np.array(image).astype(np.float32) / 255.0
            image_tensor = torch.from_numpy(image_np).unsqueeze(0)
            
            print(f"[dapaoAPI-Universal] 图像转换成功: {image_tensor.shape}")
            return image_tensor
            
        except Exception as e:
            print(f"[dapaoAPI-Universal] 图像下载失败: {e}")
            import traceback
            traceback.print_exc()
            return None


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "UniversalAPINode": UniversalAPINode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "UniversalAPINode": "🌐 通用API调用（测试） @炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
