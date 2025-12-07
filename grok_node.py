"""
大炮 API - Grok (xAI) 对话节点
提供 xAI Grok 大语言模型对话功能

作者：@炮老师的小课堂
版本：v1.0.0
"""

import os
import json
import random
import requests
import base64
import io
from PIL import Image
import numpy as np
import torch
import urllib3
from io import BytesIO

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GROK_CONFIG_FILE = os.path.join(CURRENT_DIR, 'grok_config.json')

# ==================== 辅助函数 ====================

def _log_info(message):
    """统一的日志输出函数"""
    print(f"[dapaoAPI-Grok] 信息：{message}")


def _log_warning(message):
    """统一的警告输出函数"""
    print(f"[dapaoAPI-Grok] 警告：{message}")


def _log_error(message):
    """统一的错误输出函数"""
    print(f"[dapaoAPI-Grok] 错误：{message}")


def encode_image_tensor(image_tensor) -> str:
    """将ComfyUI tensor转换为base64 PNG"""
    # Convert tensor to numpy array
    if hasattr(image_tensor, 'cpu'):
        image_np = image_tensor.cpu().numpy()
    else:
        image_np = np.array(image_tensor)
    
    # Convert to 0-255 range
    if image_np.max() <= 1.0:
        image_np = (image_np * 255).astype(np.uint8)
    
    # Handle batch dimension if present (take first image)
    if len(image_np.shape) == 4:
        image_np = image_np[0]
        
    # Create PIL Image
    img = Image.fromarray(image_np)
    
    # Encode to PNG
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def get_grok_config():
    """读取 Grok 配置文件"""
    default_config = {
        "grok_api_key": "",
        "grok_base_url": "https://api.t8star.cn/v1",
        "grok_model": "grok-4-fast-reasoning",
        "timeout": 120
    }
    
    try:
        if os.path.exists(GROK_CONFIG_FILE):
            with open(GROK_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            return default_config
    except Exception as e:
        _log_error(f"读取配置文件失败: {e}")
        return default_config


# ==================== 节点类 ====================

class Grok_Chat:
    """
    Grok (xAI) LLM对话节点
    
    使用 xAI Grok 模型进行纯文本对话
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_grok_config()
        return {
            "required": {
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "你是一个幽默、机智且直率的AI助手，深受《银河系漫游指南》的启发。",
                    "placeholder": "定义AI的角色和行为方式..."
                }),
                
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "你好，请介绍一下你自己。",
                    "placeholder": "输入你想要发送的消息..."
                }),
                
                "🤖 模型选择": (["grok-beta", "grok-vision-beta", "grok-4-fast-reasoning"], {
                    "default": config.get("grok_model", "grok-4-fast-reasoning")
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则从配置文件读取"
                }),
                
                "📊 输出语言": (["中文", "英文"], {
                    "default": "中文"
                }),
                
                "🌡️ 温度": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "控制生成的随机性，越高越有创造性"
                }),
                
                "🎲 top_p": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "Top-p 核采样参数"
                }),
                
                "📝 最大令牌": ("INT", {
                    "default": 4096,
                    "min": 256,
                    "max": 128000,
                    "step": 256,
                    "tooltip": "生成文本的最大token数量"
                }),
                
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子值（0表示不使用固定种子）"
                }),
                
                "🎛️ 种子控制": (["固定", "随机", "递增"], {
                    "default": "随机",
                    "tooltip": "固定: 使用上方种子值; 随机: 每次生成新种子; 递增: 种子值+1"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "📄 完整响应", "ℹ️ 处理信息")
    FUNCTION = "chat"
    CATEGORY = "🤖dapaoAPI/Grok"
    DESCRIPTION = "xAI Grok 大语言模型对话 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_grok_config()
        self.last_seed = -1

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        
        # 随机和递增模式下，强制更新 (返回 NaN)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        
        # 固定模式下，仅当种子值变化时更新
        return seed
    
    def chat(self, **kwargs):
        """主函数：Grok对话"""
        
        # === 参数解析 ===
        user_message = kwargs.get("💬 用户输入", "")
        system_prompt = kwargs.get("🎯 系统角色", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model_name = kwargs.get("🤖 模型选择", "grok-4-fast-reasoning")
        output_lang = kwargs.get("📊 输出语言", "中文")
        temperature = kwargs.get("🌡️ 温度", 0.7)
        top_p = kwargs.get("🎲 top_p", 0.9)
        max_tokens = kwargs.get("📝 最大令牌", 4096)
        seed = kwargs.get("🎲 随机种子", 0)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        
        # 图像输入
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        
        # 收集所有图像
        images = [img for img in [image1, image2, image3, image4] if img is not None]
        
        # === 状态信息 ===
        status_info = []
        
        # === 检查消息 ===
        if not user_message.strip():
            error_msg = "❌ 错误：请输入用户消息"
            _log_error(error_msg)
            return ("", "", error_msg)
        
        # === 获取 API 密钥 ===
        if not api_key:
            api_key = self.config.get("grok_api_key", "")
        
        if not api_key:
            error_msg = "❌ 错误：请配置 Grok API Key\n\n请执行以下操作之一：\n1. 在节点参数中输入 API 密钥\n2. 编辑 grok_config.json 文件配置"
            _log_error(error_msg)
            return ("", "", error_msg)
        
        try:
            # === 种子处理 ===
            if seed_control == "固定":
                effective_seed = seed
                seed_mode = "固定"
            elif seed_control == "随机":
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            elif seed_control == "递增":
                if self.last_seed == -1:
                    effective_seed = seed if seed != -1 else random.randint(0, 0xffffffffffffffff)
                else:
                    effective_seed = self.last_seed + 1
                seed_mode = "递增"
            else:
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            
            self.last_seed = effective_seed
            random.seed(effective_seed)
            
            status_info.append(f"🤖 模型：{model_name} (xAI)")
            status_info.append(f"🎲 种子：{effective_seed} (模式: {seed_mode})")
            if images:
                status_info.append(f"🖼️ 图像输入：{len(images)} 张")
            _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
            # === 调用 API ===
            _log_info("正在调用 Grok API 进行对话...")
            
            base_url = self.config.get("grok_base_url", "https://api.x.ai/v1")
            url = f"{base_url}/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            messages = []
            
            # 处理系统提示词和语言设置
            final_system_prompt = system_prompt
            if output_lang == "中文":
                lang_instruction = "请用中文详细回答，提供尽可能完整和详细的描述。"
            else:
                lang_instruction = "Please answer in English with detailed and comprehensive description."
            
            if final_system_prompt.strip():
                final_system_prompt = f"{final_system_prompt}\n\n{lang_instruction}"
            else:
                final_system_prompt = lang_instruction
                
            messages.append({"role": "system", "content": final_system_prompt})
            
            # 构建用户消息内容
            user_content = []
            
            # 1. 添加文本
            if user_message.strip():
                user_content.append({"type": "text", "text": user_message})
            
            # 2. 添加图像
            if images:
                for img_tensor in images:
                    try:
                        # 处理批次中的每一张图片
                        batch_size = img_tensor.shape[0]
                        for i in range(batch_size):
                            single_image = img_tensor[i]
                            base64_image = encode_image_tensor(single_image)
                            user_content.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            })
                    except Exception as e:
                        _log_error(f"处理图像失败: {e}")
            
            # 如果没有图像，可以使用简化的文本格式（虽然OpenAI格式也支持content为字符串，但列表更通用）
            # 但为了兼容性，如果只有文本且没有图像，有些API可能更喜欢纯字符串
            if not images and len(user_content) == 1 and user_content[0]["type"] == "text":
                 messages.append({"role": "user", "content": user_message})
            else:
                 messages.append({"role": "user", "content": user_content})
            
            payload = {
                "model": model_name,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # Grok API (OpenAI兼容) 种子参数为 seed
            if effective_seed != 0:
                payload["seed"] = effective_seed
            
            timeout = self.config.get("timeout", 120)
            
            # 发送请求
            response = requests.post(url, headers=headers, json=payload, timeout=timeout, verify=False)
            
            if response.status_code != 200:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                _log_error(error_msg)
                return ("", str(response.text), f"❌ API 调用失败：{error_msg}")
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                response_text = result["choices"][0]["message"]["content"]
                _log_info(f"API调用成功，生成长度: {len(response_text)} 字符")
            else:
                error_msg = f"响应格式错误: {result}"
                _log_error(error_msg)
                return ("", str(result), f"❌ 响应格式错误：{error_msg}")
            
            # === 生成详细信息 ===
            info_lines = [
                "=" * 50,
                "🎉 Grok 对话成功",
                "=" * 50,
                "",
                "📊 对话统计：",
                *[f"   {info}" for info in status_info],
                f"   📝 回复长度：{len(response_text)} 字符",
                f"   💬 用户消息长度：{len(user_message)} 字符",
                "",
                "🤖 API 参数：",
                f"   🌡️ 温度：{temperature}",
                f"   🎯 Top-P：{top_p}",
                f"   📏 最大长度：{max_tokens}",
                "",
                "💡 使用提示：",
                "   - AI回复可直接使用或继续处理",
                "   - Grok 模型通常具有幽默感和实时信息访问能力",
                "",
                "=" * 50
            ]
            
            info = "\n".join(info_lines)
            
            _log_info("✅ Grok 对话完成！")
            return (response_text, response_text, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：对话失败\n\n{str(e)}"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return ("", str(e), error_msg)


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "Grok_Chat": Grok_Chat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Grok_Chat": "🤖 Grok LLM对话 (xAI) @炮老师的小课堂",
}
