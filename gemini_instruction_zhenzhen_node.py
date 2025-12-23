"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💎 Google Gemini 3 指令节点 (T8专用版)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 专用于 T8 渠道的 Gemini 指令调用
   - 支持多模态输入（文本、图像）
   - 手动输入模型名称
   - 继承 GeminiClient 的基础能力

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v1.0.0
🎨 主题：紫色 (#8B4789)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
from .gemini3_client import (
    GeminiClient, get_api_key, encode_image_tensor, run_async
)

class DapaoGeminiInstructionZhenzhenNode:
    """
    💓Gemini指令贞贞@炮老师的小课堂
    
    专为 T8 渠道定制的 Gemini 元指令调用节点。
    支持手动输入模型名称，预设 gemini-3-flash-preview。
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 镜像站列表
        mirror_sites = ["T8", "comfly", "hk", "us"]
        
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
                
                "🤖 模型名称": ("STRING", {
                    "default": "gemini-3-flash-preview",
                    "multiline": False,
                    "placeholder": "手动输入模型名称 (如 gemini-3-flash-preview)"
                }),
                
                "🌐 镜像站": (mirror_sites, {
                    "default": "T8"
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
    CATEGORY = "🤖dapaoAPI/Gemini"
    DESCRIPTION = "Gemini 指令贞贞 (T8专用) | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def process(self, **kwargs):
        """同步处理入口"""
        # 提取参数
        kwargs_map = {
            "mirror_site": kwargs.get("🌐 镜像站"),
            "api_key": kwargs.get("🔑 API密钥"),
            "model": kwargs.get("🤖 模型名称", "gemini-3-flash-preview"),
            "system_role": kwargs.get("🎯 系统角色"),
            "user_input": kwargs.get("💬 用户输入"),
            "images": [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 5) if kwargs.get(f"🖼️ 图像{i}") is not None],
            "temperature": kwargs.get("🌡️ 温度"),
            "top_p": kwargs.get("🎲 top_p"),
            "max_tokens": kwargs.get("📝 最大令牌"),
            "language": kwargs.get("📊 输出语言")
        }
        
        return run_async(self.generate_async(**kwargs_map))
    
    async def generate_async(
        self,
        mirror_site: str,
        api_key: str,
        model: str,
        system_role: str,
        user_input: str,
        images: list,
        temperature: float,
        top_p: float,
        max_tokens: int,
        language: str
    ) -> str:
        """异步生成内容"""
        final_api_key = get_api_key(mirror_site, api_key_override=api_key or "")
        if not final_api_key:
            return (f"❌ 错误：未提供 {mirror_site} 的 API Key",)

        # 添加语言指令
        if language == "中文":
            language_instruction = "请用中文详细回答，提供尽可能完整和详细的描述。"
        else:
            language_instruction = "Please answer in English with detailed and comprehensive description."
        
        # 构建完整的系统角色
        full_system_role = f"{system_role}\n\n{language_instruction}"
        
        print(f"[dapaoAPI-Zhenzhen] 系统角色: {system_role[:50]}...")
        print(f"[dapaoAPI-Zhenzhen] 用户输入: {user_input[:100]}...")
        print(f"[dapaoAPI-Zhenzhen] 模型: {model}")
        print(f"[dapaoAPI-Zhenzhen] 镜像站: {mirror_site}")
        
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
        
        combined_text = user_input
        if full_system_role.strip():
            combined_text = f"{full_system_role}\n\n{user_input}"

        parts.append({"text": combined_text})

        contents = [{
            "role": "user",
            "parts": parts
        }]
        
        # 调用API
        try:
            async with GeminiClient(final_api_key, mirror_site) as client:
                result = await client.generate_content(
                    model=model,
                    contents=contents,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens
                )
            
            # 提取响应文本
            if 'candidates' in result and result['candidates']:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    response_parts = candidate['content']['parts']
                    response_text = ""
                    for part in response_parts:
                        if 'text' in part:
                            response_text += part['text']
                    return (response_text,)
            
            return (f"API返回了空内容: {result}",)
            
        except Exception as e:
            return (f"生成失败: {str(e)}",)


class DapaoGeminiInstructionOfficialNode:
    """
    💓Gemini指令官方@炮老师的小课堂
    """

    @classmethod
    def INPUT_TYPES(cls):
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
                "🤖 模型名称": ("STRING", {
                    "default": "gemini-3-flash-preview",
                    "multiline": False,
                    "placeholder": "手动输入模型名称 (如 gemini-3-flash-preview)"
                }),
                "🔑 Google API Key": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件或环境变量 GEMINI_API_KEY"
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
    CATEGORY = "🤖dapaoAPI/Gemini"
    DESCRIPTION = "Gemini 指令官方 (Google 官方) | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False

    def process(self, **kwargs):
        kwargs_map = {
            "api_key": kwargs.get("🔑 Google API Key"),
            "model": kwargs.get("🤖 模型名称", "gemini-3-flash-preview"),
            "system_role": kwargs.get("🎯 系统角色"),
            "user_input": kwargs.get("💬 用户输入"),
            "images": [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 5) if kwargs.get(f"🖼️ 图像{i}") is not None],
            "temperature": kwargs.get("🌡️ 温度"),
            "top_p": kwargs.get("🎲 top_p"),
            "max_tokens": kwargs.get("📝 最大令牌"),
            "language": kwargs.get("📊 输出语言")
        }

        return run_async(self.generate_async(**kwargs_map))

    async def generate_async(
        self,
        api_key: str,
        model: str,
        system_role: str,
        user_input: str,
        images: list,
        temperature: float,
        top_p: float,
        max_tokens: int,
        language: str
    ) -> str:
        final_api_key = get_api_key("google", api_key_override=api_key or "")
        if not final_api_key:
            return ("❌ 错误：未提供 Google 的 API Key",)

        if language == "中文":
            language_instruction = "请用中文详细回答，提供尽可能完整和详细的描述。"
        else:
            language_instruction = "Please answer in English with detailed and comprehensive description."

        full_system_role = f"{system_role}\n\n{language_instruction}"

        print(f"[dapaoAPI-Gemini-Official] 系统角色: {system_role[:50]}...")
        print(f"[dapaoAPI-Gemini-Official] 用户输入: {user_input[:100]}...")
        print(f"[dapaoAPI-Gemini-Official] 模型: {model}")

        parts = []

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

        combined_text = user_input
        if full_system_role.strip():
            combined_text = f"{full_system_role}\n\n{user_input}"

        parts.append({"text": combined_text})

        contents = [{
            "role": "user",
            "parts": parts
        }]

        try:
            async with GeminiClient(final_api_key, "google") as client:
                result = await client.generate_content(
                    model=model,
                    contents=contents,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens
                )

            if 'candidates' in result and result['candidates']:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    response_parts = candidate['content']['parts']
                    response_text = ""
                    for part in response_parts:
                        if 'text' in part:
                            response_text += part['text']
                    return (response_text,)

            return (f"API返回了空内容: {result}",)

        except Exception as e:
            return (f"生成失败: {str(e)}",)
