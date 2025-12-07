"""
大炮 API - GPT 多模态对话节点
提供 GPT 系列模型（如 GPT-4o, o1 等）的多模态对话功能

作者：@炮老师的小课堂
版本：v1.0.1
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
from io import BytesIO

# 尝试导入 urllib3
try:
    import urllib3
    # 禁用 SSL 警告
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GPT_CONFIG_FILE = os.path.join(CURRENT_DIR, 'gpt_config.json')

print(f"[dapaoAPI] GPT 多模态节点模块已加载")

# ==================== 辅助函数 ====================

def _log_info(message):
    """统一的日志输出函数"""
    print(f"[dapaoAPI-GPT] 信息：{message}")


def _log_warning(message):
    """统一的警告输出函数"""
    print(f"[dapaoAPI-GPT] 警告：{message}")


def _log_error(message):
    """统一的错误输出函数"""
    print(f"[dapaoAPI-GPT] 错误：{message}")


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


def get_gpt_config():
    """读取 GPT 配置文件"""
    default_config = {
        "gpt_api_key": "",
        "gpt_base_url": "https://ai.t8star.cn/v1",
        "gpt_model": "gpt-5.1-thinking",
        "timeout": 120
    }
    
    try:
        if os.path.exists(GPT_CONFIG_FILE):
            with open(GPT_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            return default_config
    except Exception as e:
        _log_error(f"读取配置文件失败: {e}")
        return default_config


# ==================== 节点类 ====================

class GPT_Multimodal_Chat:
    """
    GPT 多模态对话节点
    
    支持 GPT-4o, o1 等模型的多模态输入（文本+图像）
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_gpt_config()
        # 常见 GPT 模型列表
        model_list = [
            "gpt-5.1-thinking",
            "gpt-5.1-thinking-all",
            "gpt-5.1",
            "gpt-5.1-all"
        ]
        
        return {
            "required": {
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "你是一个乐于助人的AI助手。",
                    "placeholder": "定义AI的角色和行为方式..."
                }),
                
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "请描述这张图片的内容。",
                    "placeholder": "输入你想要发送的消息..."
                }),
                
                "🤖 模型选择": (model_list, {
                    "default": config.get("gpt_model", "gpt-5.1-thinking")
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
                    "tooltip": "控制生成的随机性 (对于o1/推理模型可能无效)"
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
                    "max": 9223372036854775807,
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
    CATEGORY = "🤖dapaoAPI/GPT"
    DESCRIPTION = "GPT 多模态对话 (OpenAI/T8) | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_gpt_config()
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
        """主函数：GPT对话"""
        
        # === 参数解析 ===
        user_message = kwargs.get("💬 用户输入", "")
        system_prompt = kwargs.get("🎯 系统角色", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model_name = kwargs.get("🤖 模型选择", "gpt-5.1-thinking")
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
            api_key = self.config.get("gpt_api_key", "")
        
        if not api_key:
            error_msg = "❌ 错误：请配置 GPT API Key\n\n请执行以下操作之一：\n1. 在节点参数中输入 API 密钥\n2. 编辑 gpt_config.json 文件配置"
            _log_error(error_msg)
            return ("", "", error_msg)
        
        # === 种子处理 ===
        # 确保种子在 signed 64-bit 整数范围内 (API限制)
        MAX_SEED = 9223372036854775807
        
        if seed_control == "固定":
            effective_seed = seed
            seed_mode = "固定"
        elif seed_control == "随机":
            effective_seed = random.randint(0, MAX_SEED)
            seed_mode = "随机"
        elif seed_control == "递增":
            if self.last_seed == -1:
                effective_seed = seed if seed != -1 else random.randint(0, MAX_SEED)
            else:
                effective_seed = self.last_seed + 1
            seed_mode = "递增"
        else:
            effective_seed = random.randint(0, MAX_SEED)
            seed_mode = "随机"
        
        # 确保最终种子在有效范围内
        effective_seed = effective_seed % MAX_SEED
        
        self.last_seed = effective_seed
        random.seed(effective_seed)
            
        status_info.append(f"🤖 模型：{model_name}")
        status_info.append(f"🎲 种子：{effective_seed} (模式: {seed_mode})")
        if images:
            status_info.append(f"🖼️ 图像输入：{len(images)} 张")
        _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
        try:
            # === 调用 API ===
            _log_info("正在调用 GPT API 进行对话...")
            
            base_url = self.config.get("gpt_base_url", "https://ai.t8star.cn/v1")
            url = f"{base_url}/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
            
            # OpenAI o1 系列模型不支持 system role，需要转为 user role 或者 developer role
            # 但大部分 T8/OpenAI 兼容接口目前对 o1 的支持各异，通常建议把 system prompt 合并到 user prompt
            # 或者 T8 已经做了适配。为了安全起见，如果是 o1 模型，我们可以做个简单判断
            is_reasoning_model = "o1" in model_name.lower() or "reasoning" in model_name.lower()
            
            if is_reasoning_model:
                # 对于 o1 模型，有些接口不支持 system role，暂时先保留，如果报错再改
                # 或者直接将 system prompt 作为第一条 user 消息
                # 这里的处理方式：仍然保留 system，但如果报错 400 (unsupported role)，用户可能需要反馈
                # 不过 T8 既然兼容，可能已经处理了。
                # 按照 OpenAI 官方 o1-preview 文档，system message 是支持的，但是不建议用复杂的 system instruction
                # 还是照常发送 system message
                messages.append({"role": "system", "content": final_system_prompt})
            else:
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
            
            # 构造 messages
            if not images and len(user_content) == 1 and user_content[0]["type"] == "text":
                 messages.append({"role": "user", "content": user_message})
            else:
                 messages.append({"role": "user", "content": user_content})
            
            payload = {
                "model": model_name,
                "messages": messages,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            # 针对 reasoning (推理) 模型的特殊处理
            if not is_reasoning_model:
                payload["temperature"] = temperature
                payload["top_p"] = top_p
                # OpenAI 种子参数
                if effective_seed != 0:
                    payload["seed"] = effective_seed
            else:
                _log_info(f"检测到推理模型 ({model_name})，已自动移除 temperature, top_p, max_tokens 和 seed 参数以避免 422/400 错误")
                # 推理模型通常不接受 max_tokens (改用 max_completion_tokens) 或 seed
                if "max_tokens" in payload:
                    # OpenAI o1 使用 max_completion_tokens，这里先移除 max_tokens
                    # 如果需要支持 max_completion_tokens，可以添加
                    del payload["max_tokens"]
                    # payload["max_completion_tokens"] = max_tokens # 可选

            timeout = self.config.get("timeout", 120)
            
            # 打印最终 payload 用于调试
            _log_info(f"Request Payload Keys: {list(payload.keys())}")
            
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
                "🎉 GPT 对话成功",
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
                "=" * 50
            ]
            
            info = "\n".join(info_lines)
            
            _log_info("✅ GPT 对话完成！")
            return (response_text, response_text, info)
            
        except Exception as e:
            # 尝试获取更详细的响应信息
            error_details = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_json = e.response.json()
                    error_details = f"{e.response.status_code} - {json.dumps(error_json, ensure_ascii=False)}"
                except:
                    error_details = f"{e.response.status_code} - {e.response.text}"
            
            _log_error(f"API调用失败: {error_details}")
            
            return ("", f"Error: {error_details}", f"❌ API调用失败: {error_details}")


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "GPT_Multimodal_Chat": GPT_Multimodal_Chat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GPT_Multimodal_Chat": "🤖 GPT 多模态对话 (OpenAI/T8) @炮老师的小课堂",
}
