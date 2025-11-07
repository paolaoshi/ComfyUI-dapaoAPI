"""
大炮 API - 智谱 LLM 对话节点
纯文本大语言模型对话功能
使用智谱 GLM-4 系列模型

作者：@炮老师的小课堂
版本：v1.0.0
"""

import os
import json
import random

# 尝试导入智谱AI SDK
try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False
    print("[ZhipuLLM] 警告：未安装 zhipuai，请运行: pip install zhipuai")

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GLM_CONFIG_FILE = os.path.join(CURRENT_DIR, 'glm_config.json')

# 统一节点颜色 (橙棕色)
NODE_COLOR = "#773508"


# ==================== 辅助函数 ====================

def _log_info(message):
    """统一的日志输出函数"""
    print(f"[dapaoAPI-ZhipuLLM] 信息：{message}")


def _log_warning(message):
    """统一的警告输出函数"""
    print(f"[dapaoAPI-ZhipuLLM] 警告：{message}")


def _log_error(message):
    """统一的错误输出函数"""
    print(f"[dapaoAPI-ZhipuLLM] 错误：{message}")


def get_zhipu_config():
    """读取智谱配置文件"""
    default_config = {
        "ZHIPUAI_API_KEY": "",
        "default_model": "GLM-4.5-Flash"
    }
    
    try:
        if os.path.exists(GLM_CONFIG_FILE):
            with open(GLM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            return default_config
    except Exception as e:
        _log_error(f"读取配置文件失败: {e}")
        return default_config


# ==================== 节点类 ====================

class Zhipu_Chat:
    """
    智谱LLM对话节点
    
    使用智谱 GLM-4 系列模型进行纯文本对话
    支持多个GLM模型选择
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        models = [
            "GLM-4.5-Flash",
            "GLM-4-Plus",
            "GLM-4-Air",
            "GLM-4-Flash"
        ]
        
        return {
            "required": {
                "💬 用户消息": ("STRING", {
                    "multiline": True,
                    "default": "你好，请介绍一下你自己。",
                    "placeholder": "输入你想要发送的消息..."
                }),
                
                "🎯 系统提示词": ("STRING", {
                    "multiline": True,
                    "default": "你是一个专业、友好且乐于助人的AI助手。",
                    "placeholder": "定义AI的角色和行为方式..."
                }),
                
                "🤖 模型选择": (models, {
                    "default": "GLM-4.5-Flash",
                    "tooltip": "选择要使用的GLM模型"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则从配置文件读取"
                }),
                
                "🌡️ 温度": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "tooltip": "控制生成的随机性，越高越有创造性"
                }),
                
                "🎯 Top-P": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05,
                    "tooltip": "Top-p 核采样参数"
                }),
                
                "📏 最大长度": ("INT", {
                    "default": 2048,
                    "min": 256,
                    "max": 8192,
                    "step": 256,
                    "tooltip": "生成文本的最大token数量"
                }),
                
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "tooltip": "随机种子值（0表示不使用固定种子，范围：1-2147483647）"
                }),
                
                "🎛️ 种子控制": (["固定", "随机", "递增"], {
                    "default": "随机",
                    "tooltip": "固定: 使用上方种子值; 随机: 每次生成新种子; 递增: 种子值+1"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "📄 完整响应", "ℹ️ 处理信息")
    FUNCTION = "chat"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "智谱 GLM-4 大语言模型对话 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.color = NODE_COLOR
        self.bgcolor = NODE_COLOR
        self.config = get_zhipu_config()
        self.last_seed = 0
    
    def chat(self, **kwargs):
        """主函数：智谱对话"""
        
        # === 参数解析 ===
        user_message = kwargs.get("💬 用户消息", "")
        system_prompt = kwargs.get("🎯 系统提示词", "")
        model = kwargs.get("🤖 模型选择", "GLM-4.5-Flash")
        api_key = kwargs.get("🔑 API密钥", "")
        temperature = kwargs.get("🌡️ 温度", 0.7)
        top_p = kwargs.get("🎯 Top-P", 0.9)
        max_tokens = kwargs.get("📏 最大长度", 2048)
        seed = kwargs.get("🎲 随机种子", 0)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        
        # === 状态信息 ===
        status_info = []
        
        # === 检查 SDK ===
        if not ZHIPUAI_AVAILABLE:
            error_msg = "❌ 错误：智谱AI SDK未安装\n\n请运行：pip install zhipuai"
            _log_error(error_msg)
            return ("", "", error_msg)
        
        # === 检查消息 ===
        if not user_message.strip():
            error_msg = "❌ 错误：请输入用户消息"
            _log_error(error_msg)
            return ("", "", error_msg)
        
        # === 获取 API 密钥 ===
        if not api_key:
            api_key = self.config.get("ZHIPUAI_API_KEY", "")
        
        if not api_key:
            error_msg = "❌ 错误：请配置智谱 API Key\n\n请执行以下操作之一：\n1. 在节点参数中输入 API 密钥\n2. 编辑 glm_config.json 文件配置"
            _log_error(error_msg)
            return ("", "", error_msg)
        
        try:
            # === 种子处理（智谱API限制：1-2147483647）===
            if seed_control == "固定":
                effective_seed = max(1, min(seed, 2147483647)) if seed != 0 else 0
                seed_mode = "固定"
            elif seed_control == "随机":
                effective_seed = random.randint(1, 2147483647)
                seed_mode = "随机"
            elif seed_control == "递增":
                if self.last_seed == 0:
                    effective_seed = max(1, min(seed, 2147483647)) if seed != 0 else random.randint(1, 2147483647)
                else:
                    effective_seed = self.last_seed + 1
                    if effective_seed > 2147483647:
                        effective_seed = 1
                seed_mode = "递增"
            else:
                effective_seed = random.randint(1, 2147483647)
                seed_mode = "随机"
            
            self.last_seed = effective_seed
            random.seed(effective_seed)
            
            status_info.append(f"🤖 模型：{model} (智谱)")
            status_info.append(f"🎲 种子：{effective_seed} (模式: {seed_mode})")
            _log_info(f"使用模型：{model}")
            _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
            # === 调用 API ===
            _log_info("正在调用智谱 API 进行对话...")
            
            client = ZhipuAI(api_key=api_key)
            
            messages = []
            if system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_message})
            
            kwargs_api = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens
            }
            
            if effective_seed != 0:
                kwargs_api["seed"] = effective_seed
            
            response = client.chat.completions.create(**kwargs_api)
            
            if response.choices and len(response.choices) > 0:
                response_text = response.choices[0].message.content
                _log_info(f"API调用成功，生成长度: {len(response_text)} 字符")
            else:
                error_msg = "响应格式错误"
                _log_error(error_msg)
                return ("", "", f"❌ 响应格式错误：{error_msg}")
            
            # === 生成详细信息 ===
            info_lines = [
                "=" * 50,
                "🎉 智谱对话成功",
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
                "   - 智谱GLM-4系列模型中文能力强",
                "   - 种子值范围：1-2147483647",
                "",
                "=" * 50
            ]
            
            info = "\n".join(info_lines)
            
            _log_info("✅ 智谱对话完成！")
            return (response_text, response_text, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：对话失败\n\n{str(e)}"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return ("", str(e), error_msg)


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "Zhipu_Chat": Zhipu_Chat,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Zhipu_Chat": "💬 智谱LLM对话 @炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

