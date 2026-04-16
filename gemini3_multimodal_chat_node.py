"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💎 Google Gemini 3 多模态对话节点（官方+T8）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 支持 LLM 对话（纯文本）
   - 支持图像反推（多图输入）
   - 支持视频反推（VIDEO 输入）
   - 支持音频分析（AUDIO 输入）
   - 整合多种功能于一体

🔧 技术特性：
   - 支持 Google 官方 API 和 T8 第三方 API
   - 双 API Key 输入，稳定可靠
   - 异步架构，高性能
   - 灵活的配置系统

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v1.3.3
🎨 主题：紫色 (#8B4789)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import torch
import aiohttp
import asyncio
from typing import Tuple, Optional, List, Dict, Any

from .gemini3_client import encode_image_tensor, run_async
from .gemini3_file_client import GeminiFileClient, save_audio_to_file

# 配置文件路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'gemini3_config.json')

# 加载配置
API_PROVIDERS = ["Google官方", "T8", "柏拉图"]
DEFAULT_PROVIDER = "Google官方"
ALL_MODELS = ["gemini-3-pro-preview", "gemini-3-flash", "gemini-2.5-flash", "gemini-2.5-pro"]
PROVIDER_MODELS = {}

if os.path.exists(CONFIG_FILE_PATH):
    try:
        with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            if "api_providers" in config and isinstance(config["api_providers"], dict):
                # 获取所有提供商的模型列表
                all_models_set = set()
                for provider, details in config["api_providers"].items():
                    if "models" in details and isinstance(details["models"], list):
                        PROVIDER_MODELS[provider] = details["models"]
                        all_models_set.update(details["models"])
                if all_models_set:
                    ALL_MODELS = sorted(list(all_models_set))
            
            if "default_provider" in config:
                if config["default_provider"] == "google":
                    DEFAULT_PROVIDER = "Google官方"
                elif config["default_provider"] in ["comfly", "hk", "us", "T8"]:
                    DEFAULT_PROVIDER = "T8"
    except Exception as e:
        print(f"[Gemini3Chat] 警告：无法加载配置: {e}")


class Gemini3MultimodalChatNode:
    """
    Google Gemini 3 多模态对话节点
    
    支持多模态输入和对话
    支持 Google 官方 API 和 T8 第三方 API
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 获取模型列表
        t8_models = []
        google_models = []
        
        # T8 模型
        for provider in ["comfly", "hk", "us", "T8"]:
            if provider in PROVIDER_MODELS:
                for model in PROVIDER_MODELS[provider]:
                    if model not in t8_models:
                        t8_models.append(model)
        
        # Google 官方模型
        if "google" in PROVIDER_MODELS:
            google_models = PROVIDER_MODELS["google"]
        
        # 合并所有模型
        all_models = list(set(t8_models + google_models + ALL_MODELS))
        if not all_models:
            all_models = ["gemini-3-pro-preview", "gemini-3-flash"]
        
        # API 来源提供商（用于T8）
        api_sources = ["comfly", "hk", "us", "柏拉图"]
        
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
                
                "🌐 API来源": (API_PROVIDERS, {
                    "default": DEFAULT_PROVIDER
                }),
                
                "🤖 模型选择": (all_models, {
                    "default": all_models[0] if all_models else "gemini-3-pro-preview"
                }),
                
                "🔑 Google API Key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入你的 Google API Key (选择Google官方时使用)"
                }),
                
                "🔑 T8Star API Key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入你的 T8Star API Key (选择T8时使用)"
                }),

                "🔑 柏拉图 API Key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入你的 柏拉图 API Key (选择柏拉图时使用)"
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
                
                "🌐 镜像站": (api_sources, {
                    "default": "comfly",
                    "tooltip": "仅在选择T8时有效，选择柏拉图时可忽略"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "process"
    CATEGORY = "🤖dapaoAPI/Gemini"
    DESCRIPTION = "Gemini 3 多模态对话（多三方支持） | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.google_api_key = ''
        self.t8star_api_key = ''
        self.bltcy_api_key = ''

    def save_api_key(self, google_key=None, t8star_key=None, bltcy_key=None):
        """仅更新内存中的API密钥，不保存到文件"""
        if google_key and google_key.strip():
            self.google_api_key = google_key.strip()
        if t8star_key and t8star_key.strip():
            self.t8star_api_key = t8star_key.strip()
        if bltcy_key and bltcy_key.strip():
            self.bltcy_api_key = bltcy_key.strip()
    
    def get_api_config(self, api_source: str, mirror_site: str = "comfly"):
        """获取API配置"""
        if api_source == "Google官方":
            return {
                "base_url": "https://generativelanguage.googleapis.com",
                "provider": "google",
                "api_key": self.google_api_key
            }
        elif api_source == "柏拉图":
            return {
                "base_url": "https://api.bltcy.ai",
                "provider": "柏拉图",
                "api_key": self.bltcy_api_key
            }
        else:  # T8
            # 从配置文件获取镜像站URL
            config = {}
            if os.path.exists(CONFIG_FILE_PATH):
                try:
                    with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                except:
                    pass
            
            base_url = "https://ai.comfly.chat/v1"
            if 'api_providers' in config and mirror_site in config['api_providers']:
                base_url = config['api_providers'][mirror_site].get('base_url', base_url)
            
            return {
                "base_url": base_url,
                "provider": mirror_site,
                "api_key": self.t8star_api_key
            }
    
    async def generate_async(
        self,
        api_config: dict,
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
        
        print(f"[Gemini3Chat] API提供商: {api_config['provider']}")
        print(f"[Gemini3Chat] 模型: {model}")
        print(f"[Gemini3Chat] 系统角色: {system_role[:50]}...")
        print(f"[Gemini3Chat] 用户输入: {user_input[:100]}...")
        print(f"[Gemini3Chat] 图像数量: {len(images)}")
        print(f"[Gemini3Chat] 视频: {'是' if video is not None else '否'}")
        print(f"[Gemini3Chat] 音频: {'是' if audio is not None else '否'}")
        
        # 构建内容parts
        parts = []
        
        # 添加图像
        if images:
            for img_tensor in images:
                if img_tensor is not None:
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
                print(f"[Gemini3Chat] 开始处理音频...")
                temp_audio_path = save_audio_to_file(audio)
                print(f"[Gemini3Chat] 音频保存到: {temp_audio_path}")
                
                file_client = GeminiFileClient(api_config['api_key'], api_config['provider'])
                file_uri = await file_client.upload_file(temp_audio_path)
                
                parts.append({
                    "file_data": {
                        "mime_type": "audio/wav",
                        "file_uri": file_uri
                    }
                })
                print(f"[Gemini3Chat] 音频上传成功: {file_uri}")
                
                try:
                    os.remove(temp_audio_path)
                except:
                    pass
            except Exception as e:
                print(f"[Gemini3Chat] 音频处理失败: {e}")
        
        # 将系统角色和用户输入合并（Gemini 不支持 system 角色）
        combined_text = user_input
        if full_system_role.strip():
            combined_text = f"{full_system_role}\n\n{user_input}"
        
        # 添加用户输入文本
        parts.append({"text": combined_text})
        
        # 构建contents（Gemini API 只支持 user 和 model 两种角色）
        contents = [{
            "role": "user",
            "parts": parts
        }]
        
        # 调用API
        async with GeminiAPIClient(api_config) as client:
            result = await client.generate_content(
                model=model,
                contents=contents,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens
            )
        
        # 提取响应文本
        print(f"[Gemini3Chat] API响应: {str(result)[:200]}...")
        
        if 'candidates' in result and result['candidates']:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                response_parts = candidate['content']['parts']
                response_text = ""
                for part in response_parts:
                    if 'text' in part:
                        response_text += part['text']
                
                print(f"[Gemini3Chat] 响应长度: {len(response_text)} 字符")
                return response_text
        
        print(f"[Gemini3Chat] 完整响应: {result}")
        return "❌ 错误：API返回格式异常"
    
    def process(self, **kwargs):
        # 提取参数
        system_role = kwargs.get("🎯 系统角色", "")
        user_input = kwargs.get("💬 用户输入", "")
        api_source = kwargs.get("🌐 API来源", "Google官方")
        model = kwargs.get("🤖 模型选择", "gemini-3-pro-preview")
        google_api_key = kwargs.get("🔑 Google API Key", "")
        t8star_api_key = kwargs.get("🔑 T8Star API Key", "")
        bltcy_api_key = kwargs.get("🔑 柏拉图 API Key", "")
        language = kwargs.get("📊 输出语言", "中文")
        mirror_site = kwargs.get("🌐 镜像站", "comfly")
        
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        video = kwargs.get("🎬 视频")
        audio = kwargs.get("🎵 音频")
        
        temperature = kwargs.get("🌡️ 温度", 0.7)
        top_p = kwargs.get("🎲 top_p", 0.90)
        max_tokens = kwargs.get("📝 最大令牌", 2048)
        
        # 更新API密钥
        self.save_api_key(google_api_key, t8star_api_key, bltcy_api_key)
        
        # 获取API配置
        api_config = self.get_api_config(api_source, mirror_site)
        
        # 检查API密钥
        if not api_config['api_key']:
            return (f"❌ 错误：请提供 {api_source} 的API密钥",)
        
        # 收集所有图像
        images = [img for img in [image1, image2, image3, image4] if img is not None]
        
        # 运行异步任务
        try:
            response = run_async(
                self.generate_async(
                    api_config=api_config,
                    model=model,
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
            print(f"[Gemini3Chat] {error_msg}")
            return (error_msg,)


class GeminiAPIClient:
    """Gemini API 客户端"""
    
    def __init__(self, api_config: dict):
        self.api_key = api_config['api_key']
        self.base_url = api_config['base_url']
        self.provider = api_config['provider']
        self.session: Optional[aiohttp.ClientSession] = None
        self.timeout = 120
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_endpoint(self, model: str) -> str:
        """获取API端点URL"""
        if self.base_url.rstrip('/').endswith(('v1', 'v1beta', 'v1alpha')):
            return f"{self.base_url.rstrip('/')}/models/{model}:generateContent"
        else:
            return f"{self.base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
    
    async def generate_content(
        self,
        model: str,
        contents: List[Dict[str, Any]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """生成内容"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = self._get_endpoint(model)
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "topP": top_p,
                "maxOutputTokens": max_tokens
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        async with self.session.post(url, json=payload, headers=headers, timeout=self.timeout) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Gemini API错误 {response.status}: {error_text}")
            return await response.json()


# 节点注册
NODE_CLASS_MAPPINGS = {
    "Gemini3MultimodalChatNode": Gemini3MultimodalChatNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Gemini3MultimodalChatNode": "💎 Gemini 3 多模态对话（多三方支持）@炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
