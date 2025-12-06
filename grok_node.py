"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🤖 Grok API 调用节点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 支持调用 xAI Grok 系列模型
   - 支持文生文、多模态识图 (Grok Vision)
   - 兼容 OpenAI 格式调用
   - 支持流式/非流式 (本节点使用非流式以获取完整结果)

🔧 技术特性：
   - 自动处理 Base64 图片编码
   - 完整的错误处理
   - 支持自定义系统提示词

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v1.0.0
🎨 主题：黑色 (#000000)
🌐 API文档：https://docs.x.ai/docs/overview

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import requests
import base64
import io
import torch
import numpy as np
import random
from PIL import Image
from typing import Tuple, Optional

# 节点颜色 (黑色/深灰，对应 xAI 风格)


def tensor2pil(image_tensor):
    """将 Tensor 转换为 PIL Image"""
    # image_tensor shape: [B, H, W, C]
    if image_tensor.dim() == 4:
        image_tensor = image_tensor[0]
    
    image_np = (image_tensor.cpu().numpy() * 255).astype('uint8')
    pil_image = Image.fromarray(image_np)
    return pil_image

def image_to_base64(pil_image):
    """将 PIL Image 转换为 Base64 字符串"""
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{img_str}"

class GrokChatNode:
    """
    xAI Grok 大模型调用节点
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "📝 系统提示词": ("STRING", {
                    "multiline": True,
                    "default": "You are a helpful assistant.",
                    "placeholder": "设置 AI 的角色..."
                }),
                
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "请解释一下量子纠缠。",
                    "placeholder": "输入你的问题..."
                }),
                
                "🤖 模型选择": (["grok-4-fast-reasoning", "grok-4-fast-non-reasoning", "grok-4", "grok-4-0709", "grok-2-vision-1212", "grok-2-1212", "grok-beta", "grok-vision-beta"], {
                    "default": "grok-4-fast-reasoning"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "输入贞贞 API Key (sk-...)",
                    "multiline": False
                }),
                
                "🎲 随机种子": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子，-1为随机"
                }),

                "🎯 种子控制": (["随机", "固定", "递增"], {"default": "随机"}),
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
                    "step": 0.1,
                    "tooltip": "数值越高，回答越随机；数值越低，回答越确定。"
                }),
                
                "🎲 Top P": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05
                }),
                
                "📏 最大Token": ("INT", {
                    "default": 4096,
                    "min": 128,
                    "max": 128000
                }),
                
                "⏱️ 超时时间": ("INT", {
                    "default": 60,
                    "min": 5,
                    "max": 300,
                    "tooltip": "API 请求超时时间(秒)"
                }),
                
                "🌐 自定义API地址": ("STRING", {
                    "default": "https://ai.t8star.cn/v1/chat/completions",
                    "placeholder": "默认使用贞贞 API 地址"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("AI回复", "完整响应JSON")
    FUNCTION = "chat"
    CATEGORY = "🤖dapaoAPI/Grok"
    DESCRIPTION = "调用 Grok 系列模型 (via 贞贞 API)，支持多模态识图"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎯 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        
        # 随机和递增模式下，强制更新 (返回 NaN)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        
        # 固定模式下，仅当种子值变化时更新
        return seed

    def __init__(self):
        self.last_seed = -1

    def chat(self, **kwargs):
        # 提取参数
        system_prompt = kwargs.get("📝 系统提示词", "")
        user_prompt = kwargs.get("💬 用户输入", "")
        model = kwargs.get("🤖 模型选择", "grok-4-fast-reasoning")
        api_key = kwargs.get("🔑 API密钥", "")
        
        # 图像处理
        images = [kwargs.get(f"🖼️ 图像1"), kwargs.get(f"🖼️ 图像2"), 
                 kwargs.get(f"🖼️ 图像3"), kwargs.get(f"🖼️ 图像4")]
        
        temperature = kwargs.get("🌡️ 温度", 0.7)
        top_p = kwargs.get("🎲 Top P", 1.0)
        max_tokens = kwargs.get("📏 最大Token", 4096)
        timeout = kwargs.get("⏱️ 超时时间", 60)
        api_url = kwargs.get("🌐 自定义API地址", "https://ai.t8star.cn/v1/chat/completions")
        
        seed = kwargs.get("🎲 随机种子", -1)
        seed_control = kwargs.get("🎯 种子控制", "随机")

        # 处理种子逻辑
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
        
        # 更新 last_seed
        self.last_seed = effective_seed
        print(f"[GrokAPI] 🎲 种子模式: {seed_control}, 使用种子: {effective_seed}")

        # 检查 API Key
        if not api_key:
            # 尝试从配置文件读取 (虽然现在默认不保存，但为了兼容性)
            # 这里为了安全，如果输入为空，直接报错，或者可以检查环境变量
            return ("❌ 错误：未提供 API Key，请在节点中输入。", "{}")

        # 构建消息体
        messages = []
        
        # 1. 系统提示词
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 2. 用户消息 (包含文本和图像)
        user_content = []
        
        # 添加文本
        if user_prompt:
            user_content.append({"type": "text", "text": user_prompt})
        
        # 添加图像
        has_images = False
        for img_tensor in images:
            if img_tensor is not None:
                has_images = True
                pil_img = tensor2pil(img_tensor)
                base64_img = image_to_base64(pil_img)
                user_content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": base64_img,
                        "detail": "auto"
                    }
                })
        
        # 如果没有图像，content 可以直接是字符串 (兼容性更好)，但 OpenAI 格式支持 array
        # Grok 文档建议 Vision 模型才传图片
        if not has_images:
            # 如果只有文本，简化结构
            messages.append({"role": "user", "content": user_prompt})
        else:
            messages.append({"role": "user", "content": user_content})

        # 准备请求头
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 准备请求体
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "seed": effective_seed,
            "stream": False
        }

        # 发送请求
        try:
            print(f"[GrokAPI] 发送请求到 {api_url} (Model: {model})")
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # 检查状态码
            if response.status_code != 200:
                error_msg = f"API Error {response.status_code}: {response.text}"
                print(f"[GrokAPI] ❌ {error_msg}")
                return (f"Error: {error_msg}", response.text)
            
            # 解析响应
            result = response.json()
            
            # 提取回复内容
            try:
                content = result["choices"][0]["message"]["content"]
                print(f"[GrokAPI] ✅ 请求成功，回复长度: {len(content)}")
                return (content, json.dumps(result, indent=2, ensure_ascii=False))
            except (KeyError, IndexError) as e:
                error_msg = f"解析响应失败: {e}"
                print(f"[GrokAPI] ❌ {error_msg}")
                return (f"Error: {error_msg}\nRaw: {json.dumps(result)}", json.dumps(result))

        except Exception as e:
            error_msg = f"请求异常: {str(e)}"
            print(f"[GrokAPI] ❌ {error_msg}")
            return (f"Error: {error_msg}", "{}")

# 节点映射
NODE_CLASS_MAPPINGS = {
    "GrokChatNode": GrokChatNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GrokChatNode": "🤖 Grok API 聊天 (xAI)"
}
