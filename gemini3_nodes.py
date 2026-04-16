"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💎 Google Gemini 多功能节点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 支持 LLM 对话（纯文本）
   - 支持图像反推（多图输入）
   - 支持视频反推（VIDEO 输入）
   - 整合三大功能于一体

🔧 技术特性：
   - 基于 ComfyUI-Gemini-3 项目优化
   - 异步架构，高性能
   - 多API提供商支持
   - 灵活的配置系统

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v2.0.0
🎨 主题：紫色 (#8B4789)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import torch
from typing import Tuple

from .gemini3_client import (
    GeminiClient, get_api_key, encode_image_tensor, run_async
)
from .gemini3_file_client import GeminiFileClient, save_audio_to_file

# 统一节点颜色 (紫色)


# 配置文件路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'gemini3_config.json')

# 加载配置
API_PROVIDERS = ["google", "comfly", "T8"]
DEFAULT_PROVIDER = "google"
ALL_MODELS = ["gemini-3-pro-preview"]
PROVIDER_MODELS = {}

if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if "api_providers" in config and isinstance(config["api_providers"], dict):
                API_PROVIDERS = list(config["api_providers"].keys())
                all_models_set = set()
                for provider, details in config["api_providers"].items():
                    if "models" in details and isinstance(details["models"], list):
                        PROVIDER_MODELS[provider] = details["models"]
                        all_models_set.update(details["models"])
                if all_models_set:
                    ALL_MODELS = sorted(list(all_models_set))
            
            if "default_provider" in config and config["default_provider"] in API_PROVIDERS:
                DEFAULT_PROVIDER = config["default_provider"]
    except Exception as e:
        print(f"[dapaoAPI-Gemini3] 警告：无法加载配置: {e}")


class Gemini3_Multimodal:
    """
    Google Gemini 多功能节点
    
    整合对话、图像反推、视频反推功能
    支持多API提供商
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 只显示T8相关的模型
        t8_models = []
        for provider in ["comfly", "hk", "us", "T8"]:
            if provider in PROVIDER_MODELS:
                for model in PROVIDER_MODELS[provider]:
                    model_display = f"{model}-T8"
                    if model_display not in t8_models:
                        t8_models.append(model_display)
        
        if not t8_models:
            t8_models = ["gemini-3-pro-preview-T8", "gemini-3-flash-T8"]
        
        # 镜像站列表
        mirror_sites = ["comfly", "hk", "us", "柏拉图"]
        
        return {
            "required": {
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "你是一个专业的AI助手，擅长分析图像、视频和音频内容，并提供详细的描述。",
                    "placeholder": "定义AI的角色和行为方式..."
                }),
                
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "请详细分析这个内容，包括所有细节",
                    "placeholder": "输入你的问题或指令..."
                }),
                
                "🤖 模型选择": ("STRING", {
                    "default": "gemini-3.1-flash-lite-preview",
                    "multiline": False,
                    "placeholder": "手动输入模型名称"
                }),
                
                "🌐 镜像站": (mirror_sites, {
                    "default": "柏拉图"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件"
                }),
                
                "📊 输出语言": (["中文", "英文"], {
                    "default": "中文"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🎬 视频": ("IMAGE",),
                "🎵 音频": ("AUDIO",),
                
                "🌡️ 温度": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01
                }),
                
                "🎲 top_p": ("FLOAT", {
                    "default": 0.90,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                
                "📝 最大令牌": ("INT", {
                    "default": 2048,
                    "min": 1,
                    "max": 32768
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "process"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "Google Gemini 多功能 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    async def generate_async(
        self,
        mirror_site: str,
        api_key: str,
        model: str,
        system_role: str,
        user_input: str,
        images: list,
        video,
        audio,
        temperature: float,
        top_p: float,
        max_tokens: int,
        language: str
    ) -> str:
        """异步生成内容"""
        # 添加语言指令
        if language == "中文":
            language_instruction = "请用中文详细回答，提供尽可能完整和详细的描述。"
        else:
            language_instruction = "Please answer in English with detailed and comprehensive description."
        
        # 构建完整的系统角色
        full_system_role = f"{system_role}\n\n{language_instruction}"
        
        print(f"[dapaoAPI-Gemini3] 系统角色: {system_role[:50]}...")
        print(f"[dapaoAPI-Gemini3] 用户输入: {user_input[:100]}...")
        print(f"[dapaoAPI-Gemini3] 模型: {model}")
        print(f"[dapaoAPI-Gemini3] 镜像站: {mirror_site}")
        print(f"[dapaoAPI-Gemini3] 最大令牌: {max_tokens}")
        print(f"[dapaoAPI-Gemini3] 图像数量: {len(images)}")
        print(f"[dapaoAPI-Gemini3] 视频: {'是' if video is not None else '否'}")
        print(f"[dapaoAPI-Gemini3] 音频: {'是' if audio is not None else '否'}")
        
        # 构建内容parts
        parts = []
        
        # 添加图像
        if images:
            for img_tensor in images:
                if img_tensor is not None:
                    # 处理批次
                    batch_size = img_tensor.shape[0]
                    for i in range(batch_size):
                        single_image = img_tensor[i]
                        image_base64 = encode_image_tensor(single_image)
                        parts.append({
                            "inline_data": {
                                "mime_type": "image/png",
                                "data": image_base64
                            }
                        })
        
        # 添加视频帧（采样最多10帧）
        if video is not None:
            batch_size = video.shape[0]
            step = max(1, batch_size // 10)
            for i in range(0, batch_size, step):
                frame = video[i]
                image_base64 = encode_image_tensor(frame)
                parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": image_base64
                    }
                })
        
        # 添加音频（使用 File API 上传）
        if audio is not None:
            try:
                print(f"[dapaoAPI-Gemini3] 开始处理音频...")
                # 保存音频到临时文件
                temp_audio_path = save_audio_to_file(audio)
                print(f"[dapaoAPI-Gemini3] 音频保存到: {temp_audio_path}")
                
                # 使用 File API 上传
                file_client = GeminiFileClient(api_key, mirror_site)
                file_uri = await file_client.upload_file(temp_audio_path)
                
                parts.append({
                    "file_data": {
                        "mime_type": "audio/wav",
                        "file_uri": file_uri
                    }
                })
                print(f"[dapaoAPI-Gemini3] 音频上传成功: {file_uri}")
                
                # 清理临时文件
                try:
                    import os
                    os.remove(temp_audio_path)
                except:
                    pass
            except Exception as e:
                print(f"[dapaoAPI-Gemini3] 音频处理失败: {e}")
        
        # 添加用户输入文本
        parts.append({"text": user_input})
        
        # 构建contents（包含系统角色）
        contents = []
        
        # 添加系统角色（如果有）
        if full_system_role.strip():
            contents.append({
                "role": "system",
                "parts": [{"text": full_system_role}]
            })
        
        # 添加用户消息
        contents.append({
            "role": "user",
            "parts": parts
        })
        
        # 调用API（使用镜像站作为provider）
        async with GeminiClient(api_key, mirror_site) as client:
            result = await client.generate_content(
                model=model,
                contents=contents,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
        
        # 提取响应文本
        print(f"[dapaoAPI-Gemini3] API响应: {str(result)[:200]}...")
        
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                response_parts = candidate['content']['parts']
                response_text = ""
                for part in response_parts:
                    if 'text' in part:
                        response_text += part['text']
                
                print(f"[dapaoAPI-Gemini3] 响应长度: {len(response_text)} 字符")
                return response_text
        
        print(f"[dapaoAPI-Gemini3] 完整响应: {result}")
        return "❌ 错误：API返回格式异常"
    
    def process(self, **kwargs):
        # 提取参数
        system_role = kwargs.get("🎯 系统角色", "")
        user_input = kwargs.get("💬 用户输入", "")
        model = kwargs.get("🤖 模型选择", "gemini-3.1-flash-lite-preview")
        mirror_site = kwargs.get("🌐 镜像站", "柏拉图")
        apikey = kwargs.get("🔑 API密钥", "")
        language = kwargs.get("📊 输出语言", "中文")
        
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        video = kwargs.get("🎬 视频")
        audio = kwargs.get("🎵 音频")
        
        temperature = kwargs.get("🌡️ 温度", 0.7)
        top_p = kwargs.get("🎲 top_p", 0.90)
        max_tokens = kwargs.get("📝 最大令牌", 2048)
        
        actual_model = model.strip() or "gemini-3.1-flash-lite-preview"
        
        # 获取API密钥
        api_key = get_api_key(mirror_site, apikey)
        if not api_key:
            return (f"❌ 错误：未配置 {mirror_site} 镜像站的API密钥\n\n请在配置文件或节点参数中设置",)
        
        # 收集所有图像
        images = [img for img in [image1, image2, image3, image4] if img is not None]
        
        # 运行异步任务
        try:
            response = run_async(
                self.generate_async(
                    mirror_site=mirror_site,
                    api_key=api_key,
                    model=actual_model,
                    system_role=system_role,
                    user_input=user_input,
                    images=images,
                    video=video,
                    audio=audio,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    language=language
                )
            )
            return (response,)
        except Exception as e:
            error_msg = f"❌ API错误: {str(e)}"
            print(f"[dapaoAPI-Gemini3] {error_msg}")
            return (error_msg,)


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "Gemini3_Multimodal": Gemini3_Multimodal,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Gemini3_Multimodal": "💎 Gemini 多功能 @炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
