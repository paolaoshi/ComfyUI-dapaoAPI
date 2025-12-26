"""
大炮 API - 豆包 LLM 对话节点
纯文本大语言模型对话功能
使用豆包 Seed-1.6 模型

作者：@炮老师的小课堂
版本：v1.1.0
"""

import os
import json
import random
import time
import requests
import base64
import io
from PIL import Image
import numpy as np
import torch
import comfy.utils
from comfy.comfy_types import IO
try:
    import folder_paths
except Exception:
    folder_paths = None

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DOUBAO_CONFIG_FILE = os.path.join(CURRENT_DIR, 'doubao_config.json')

# 统一节点颜色 (橙棕色)



# ==================== 辅助函数 ====================

def _log_info(message):
    """统一的日志输出函数"""
    print(f"[dapaoAPI-DoubaoLLM] 信息：{message}")


def _log_warning(message):
    """统一的警告输出函数"""
    print(f"[dapaoAPI-DoubaoLLM] 警告：{message}")


def _log_error(message):
    """统一的错误输出函数"""
    print(f"[dapaoAPI-DoubaoLLM] 错误：{message}")


def get_doubao_config():
    """读取豆包配置文件"""
    default_config = {
        "doubao_api_key": "",
        "doubao_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "doubao_vision_endpoint": "doubao-seed-1-6-vision-250815",
        "timeout": 120
    }
    
    try:
        if os.path.exists(DOUBAO_CONFIG_FILE):
            with open(DOUBAO_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            return default_config
    except Exception as e:
        _log_error(f"读取配置文件失败: {e}")
        return default_config


def tensor_to_base64(image_tensor: torch.Tensor) -> str:
    """
    将 ComfyUI 图像张量转换为 base64 编码
    
    Args:
        image_tensor: ComfyUI 图像张量 [B, H, W, C], 值范围 [0, 1]
        
    Returns:
        str: base64 编码的图像数据（带 data URL 前缀）
    """
    try:
        # ComfyUI 的 IMAGE 是 PyTorch 张量，范围 [0,1]，形状 [B, H, W, C]
        # 转换为 PIL Image，范围 [0,255]
        i = 255. * image_tensor.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0])  # 取第一个 batch
        
        # 转换为 base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        _log_error(f"图像转 base64 失败: {e}")
        return None


# ==================== 节点类 ====================

class DoubaoVideoAdapter:
    """
    视频适配器：兼容 ComfyUI 的 VIDEO 类型输出
    
    说明：
    - 这里优先支持视频 URL（豆包视频生成接口一般返回 URL）
    - save_to 会把 URL 下载到 ComfyUI 指定的输出路径
    """
    def __init__(self, video_path_or_url: str):
        self.video_url = None
        self.video_path = None
        self.is_url = False
        
        if not video_path_or_url:
            return
        
        if isinstance(video_path_or_url, str) and video_path_or_url.startswith("http"):
            self.is_url = True
            self.video_url = video_path_or_url
        else:
            self.is_url = False
            self.video_path = video_path_or_url
    
    def get_dimensions(self):
        """
        获取视频尺寸
        
        说明：豆包任务结果通常是 URL，尺寸信息不一定能直接拿到，因此返回一个合理默认值。
        """
        return 1280, 720
    
    def save_to(self, output_path, format="auto", codec="auto", metadata=None):
        """
        保存视频到指定路径（ComfyUI SaveVideo/保存节点会调用）
        """
        if self.is_url:
            try:
                _log_info(f"开始下载视频到: {output_path}")
                response = requests.get(self.video_url, stream=True, timeout=300, allow_redirects=True, verify=False)
                response.raise_for_status()
                total_bytes = 0
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            f.write(chunk)
                            total_bytes += len(chunk)
                _log_info(f"视频下载完成，大小: {round(total_bytes / 1024 / 1024, 2)} MB")
                return True
            except Exception as e:
                _log_error(f"从 URL 下载视频失败: {e}")
                return False
        
        try:
            if not self.video_path or not os.path.exists(self.video_path):
                return False
            with open(self.video_path, "rb") as src, open(output_path, "wb") as dst:
                while True:
                    chunk = src.read(1024 * 1024)
                    if not chunk:
                        break
                    dst.write(chunk)
            return True
        except Exception as e:
            _log_error(f"保存本地视频失败: {e}")
            return False

class Doubao_Chat:
    """
    豆包LLM对话节点
    
    使用豆包 Seed-1.6 模型进行纯文本对话
    支持推理增强模式
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
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
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子值（0表示不使用固定种子）"
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
    CATEGORY = "🤖dapaoAPI/豆包"
    DESCRIPTION = "豆包 Seed-1.6 大语言模型对话 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_doubao_config()
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
        """主函数：豆包对话"""
        
        # === 参数解析 ===
        user_message = kwargs.get("💬 用户消息", "")
        system_prompt = kwargs.get("🎯 系统提示词", "")
        api_key = kwargs.get("🔑 API密钥", "")
        temperature = kwargs.get("🌡️ 温度", 0.7)
        top_p = kwargs.get("🎯 Top-P", 0.9)
        max_tokens = kwargs.get("📏 最大长度", 2048)
        seed = kwargs.get("🎲 随机种子", 0)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        
        # === 状态信息 ===
        status_info = []
        
        # === 检查消息 ===
        if not user_message.strip():
            error_msg = "❌ 错误：请输入用户消息"
            _log_error(error_msg)
            return ("", "", error_msg)
        
        # === 获取 API 密钥 ===
        if not api_key:
            api_key = self.config.get("doubao_api_key", "")
        
        if not api_key:
            error_msg = "❌ 错误：请配置豆包 API Key\n\n请执行以下操作之一：\n1. 在节点参数中输入 API 密钥\n2. 编辑 doubao_config.json 文件配置"
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
            
            status_info.append(f"🤖 模型：doubao-seed-1-6-251015 (豆包)")
            status_info.append(f"🎲 种子：{effective_seed} (模式: {seed_mode})")
            _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
            # === 调用 API ===
            _log_info("正在调用豆包 API 进行对话...")
            
            base_url = self.config.get("doubao_base_url", "https://ark.cn-beijing.volces.com/api/v3")
            url = f"{base_url}/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            messages = []
            if system_prompt.strip():
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_message})
            
            payload = {
                "model": "doubao-seed-1-6-251015",
                "messages": messages,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": False
            }
            
            if effective_seed != 0:
                payload["seed"] = effective_seed
            
            timeout = self.config.get("timeout", 120)
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
                "🎉 豆包对话成功",
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
                "   - 豆包Seed-1.6支持推理增强模式",
                "   - 种子值支持完整64位整数范围",
                "",
                "=" * 50
            ]
            
            info = "\n".join(info_lines)
            
            _log_info("✅ 豆包对话完成！")
            return (response_text, response_text, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：对话失败\n\n{str(e)}"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return ("", str(e), error_msg)


class Doubao_ImageToPrompt:
    """
    豆包 AI 图像反推节点 v1.0
    
    使用豆包 Seed-1.6 Vision 模型分析图像，生成详细的图像描述
    
    功能特性：
    - 🖼️ 多图支持：最多支持4张图片同时分析
    - 📝 自定义反推指令：灵活控制输出风格
    - 🎲 种子控制：支持固定、随机、递增三种模式
    
    适用场景：
    - 图生图前的提示词参考
    - 了解图像内容
    - 生成训练数据标注
    - 多图对比分析
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_doubao_config()
        
        return {
            "required": {
                # === 图像输入 ===
                "🖼️ 图像1": ("IMAGE", {
                    "tooltip": "必填：主要分析图像"
                }),
                
                # === 反推指令 ===
                "📝 反推指令": ("STRING", {
                    "multiline": True,
                    "default": """你是一个专业的图像分析专家，能够将图片内容转化为高质量的英文提示词。

请仔细观察图片，生成详细的英文描述，包括：
1. 主体：人物/物体的外观、特征、表情、动作
2. 场景：环境、背景、时间、天气、光线
3. 构图：视角、景别、空间关系
4. 风格：艺术风格、色彩、氛围、质感
5. 细节：纹理、材质、装饰、道具等

要求：
- 使用英文
- 详细具体
- 用逗号连接不同描述
- 末尾添加画质词：high quality, ultra detailed, masterpiece

只输出最终的英文提示词，不要包含解释。""",
                    "placeholder": "描述如何分析图像..."
                }),
                
                # === API 配置 ===
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则从配置文件读取"
                }),
                "🤖 视觉模型": ("STRING", {
                    "default": config.get("doubao_vision_endpoint", "doubao-seed-1-6-vision-250815"),
                    "placeholder": "如: doubao-seed-1-6-vision-250815"
                }),
                
                # === 高级设置 ===
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子值"
                }),
                
                "🎛️ 种子控制": (["固定", "随机", "递增"], {
                    "default": "随机",
                    "tooltip": "固定: 使用上方种子值; 随机: 每次生成新种子; 递增: 种子值+1"
                }),
            },
            "optional": {
                # === 可选图像输入 ===
                "🖼️ 图像2": ("IMAGE", {
                    "tooltip": "可选：额外的对比图像"
                }),
                "🖼️ 图像3": ("IMAGE", {
                    "tooltip": "可选：额外的对比图像"
                }),
                "🖼️ 图像4": ("IMAGE", {
                    "tooltip": "可选：额外的对比图像"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("🎨 图像描述", "ℹ️ 处理信息")
    FUNCTION = "analyze_image"
    CATEGORY = "🤖dapaoAPI/豆包"
    DESCRIPTION = "使用豆包 AI 分析图像，支持多图输入、生成详细的英文提示词 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_doubao_config()
        # 保存上一次使用的种子（用于递增模式）
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
    
    def analyze_image(self, **kwargs):
        """分析图像，生成提示词（支持多图）"""
        
        # 参数解析
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        prompt_text = kwargs.get("📝 反推指令", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model_name = kwargs.get("🤖 视觉模型", "doubao-seed-1-6-vision-250815")
        seed = kwargs.get("🎲 随机种子", 0)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        
        # 获取 API Key
        if not api_key:
            api_key = self.config.get("doubao_api_key", "")
        
        if not api_key:
            error_msg = "❌ 错误：未提供 API Key\n\n请执行以下操作之一：\n1. 在节点的【🔑 API密钥】参数中输入\n2. 编辑 doubao_config.json 文件配置"
            _log_error(error_msg)
            return ("", error_msg)
        
        # 检查图像输入（至少需要图像1）
        if image1 is None:
            error_msg = "❌ 错误：请提供至少一张图像\n\n请在【🖼️ 图像1】参数中上传图像"
            _log_error(error_msg)
            return ("", error_msg)
        
        try:
            # 收集所有有效的图像
            images = []
            if image1 is not None:
                images.append(("图像1", image1))
            if image2 is not None:
                images.append(("图像2", image2))
            if image3 is not None:
                images.append(("图像3", image3))
            if image4 is not None:
                images.append(("图像4", image4))
            
            _log_info(f"共接收到 {len(images)} 张图像")
            
            # 转换所有图像为 base64
            image_base64_list = []
            for img_name, img_tensor in images:
                _log_info(f"正在转换 {img_name}...")
                img_base64 = tensor_to_base64(img_tensor)
                if not img_base64:
                    _log_warning(f"{img_name} 转换失败，已跳过")
                    continue
                image_base64_list.append((img_name, img_base64))
            
            if not image_base64_list:
                error_msg = "❌ 错误：所有图像转换失败"
                _log_error(error_msg)
                return ("", error_msg)
            
            _log_info(f"成功转换 {len(image_base64_list)} 张图像")
            
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
            
            # 保存当前种子供下次使用
            self.last_seed = effective_seed
            random.seed(effective_seed)
            
            _log_info(f"调用豆包 Vision ({model_name}) 分析 {len(image_base64_list)} 张图像...")
            _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
            # 构建请求内容（先添加文本指令）
            content_parts = [{"type": "text", "text": prompt_text}]
            
            # 添加所有图像
            for img_name, img_base64 in image_base64_list:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": img_base64}
                })
            
            # 调用豆包 API
            base_url = self.config.get("doubao_base_url", "https://ark.cn-beijing.volces.com/api/v3")
            url = f"{base_url}/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": content_parts}],
                "stream": False
            }
            
            if effective_seed != 0:
                payload["seed"] = effective_seed
            
            timeout = self.config.get("timeout", 120)
            response = requests.post(url, headers=headers, json=payload, timeout=timeout, verify=False)
            
            if response.status_code != 200:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                _log_error(error_msg)
                return ("", f"❌ API 调用失败：{error_msg}")
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                result_text = result["choices"][0]["message"]["content"]
                _log_info("✅ 图像分析成功")
            else:
                error_msg = f"响应格式错误: {result}"
                _log_error(error_msg)
                return ("", f"❌ 响应格式错误：{error_msg}")
            
            # 构建详细的信息输出
            info_lines = [
                "🎉 豆包图像分析成功",
                "",
                "📊 分析信息：",
                f"   模型：{model_name}",
                f"   图像数量：{len(image_base64_list)} 张",
                f"   图像列表：{', '.join([name for name, _ in image_base64_list])}",
                "",
                "🎲 种子信息：",
                f"   种子值：{effective_seed}",
                f"   控制模式：{seed_mode}",
                "",
                "✅ 分析完成"
            ]
            
            info = "\n".join(info_lines)
            
            return (result_text, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：图像分析失败\n\n错误详情：{str(e)}\n\n建议：\n1. 检查网络连接\n2. 检查 API Key 是否正确\n3. 查看终端完整日志"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return ("", error_msg)


class Doubao_VideoToPrompt:
    """
    豆包 AI 视频反推节点 v2.0
    
    使用豆包 Seed-1.6 Vision 模型分析视频内容，生成详细的视频描述
    
    功能特性：
    - 🎬 VIDEO格式：支持 ComfyUI 原生 VIDEO 类型（LoadVideo节点输出）
    - 🖼️ 图像批次：支持 IMAGE 批次格式（多帧图像）
    - 📝 预设模板：提供多种分析模板，支持自定义
    - 🌐 中英文切换：支持输出中文或英文描述
    - 🎲 种子控制：支持固定、随机、递增三种模式
    - 🎯 帧采样：自动从视频中采样关键帧
    
    适用场景：
    - 视频内容理解和描述
    - 视频转文字提示词
    - 多帧图像序列分析
    - 动态场景描述生成
    
    作者：@炮老师的小课堂
    """
    
    PROMPT_TEMPLATES = {
        "详细英文提示词": """你是一个专业的视频分析专家，能够将视频内容转化为高质量的英文提示词。

请仔细观察视频中的所有帧，生成详细的英文描述，包括：
1. 主体：人物/物体的外观、动作、表情变化
2. 场景：环境、背景、光线、氛围
3. 动态：运动轨迹、动作序列、镜头运动
4. 风格：艺术风格、色彩、质感
5. 细节：纹理、材质、特效等

要求：
- 使用英文
- 详细具体，描述动态变化
- 用逗号连接不同描述
- 末尾添加画质词：high quality, ultra detailed, masterpiece

只输出最终的英文提示词，不要包含解释。""",
        
        "详细中文描述": """你是一个专业的视频分析专家，请详细描述视频内容。

请仔细观察视频中的所有帧，生成详细的中文描述，包括：
1. 主体：人物/物体的外观、动作、表情变化
2. 场景：环境、背景、光线、氛围
3. 动态：运动轨迹、动作序列、镜头运动
4. 风格：艺术风格、色彩、质感
5. 细节：纹理、材质、特效等

要求：
- 使用中文
- 详细具体，描述动态变化
- 语言流畅自然

只输出视频描述，不要包含其他解释。""",
        
        "简洁英文标签": """请用简洁的英文标签描述这个视频。

要求：
- 使用英文
- 用逗号分隔的关键词形式
- 包含：主体、动作、场景、风格
- 末尾添加：high quality, detailed

只输出标签，不要解释。""",
        
        "简洁中文总结": """请用一段话简洁总结这个视频的内容。

要求：
- 使用中文
- 100字以内
- 突出重点

只输出总结，不要其他内容。""",
    }
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_doubao_config()
        
        return {
            "required": {
                "📋 提示词模板": (list(cls.PROMPT_TEMPLATES.keys()), {
                    "default": "详细英文提示词",
                    "tooltip": "选择预设的分析模板"
                }),
                
                "✏️ 自定义提示词": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "留空则使用上方模板，填写则覆盖模板（优先级最高）"
                }),
                
                "🌐 输出语言": (["英文", "中文"], {
                    "default": "英文",
                    "tooltip": "选择最终输出的语言"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则从配置文件读取"
                }),
                "🤖 视觉模型": ("STRING", {
                    "default": config.get("doubao_vision_endpoint", "doubao-seed-1-6-vision-250815"),
                    "placeholder": "如: doubao-seed-1-6-vision-250815"
                }),
                
                "🎞️ 最大帧数": ("INT", {
                    "default": 8,
                    "min": 1,
                    "max": 16,
                    "step": 1,
                    "tooltip": "从视频中采样的最大帧数（API限制）"
                }),
                
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子值"
                }),
                
                "🎛️ 种子控制": (["固定", "随机", "递增"], {
                    "default": "随机",
                    "tooltip": "固定: 使用上方种子值; 随机: 每次生成新种子; 递增: 种子值+1"
                }),
            },
            "optional": {
                "🎬 上传视频(VIDEO格式)": ("VIDEO", {
                    "tooltip": "可选：ComfyUI VIDEO 格式（LoadVideo节点输出）"
                }),
                
                "🖼️ 上传视频(图像批次)": ("IMAGE", {
                    "tooltip": "可选：多帧图像批次"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("🎨 视频描述", "ℹ️ 处理信息")
    FUNCTION = "analyze_video"
    CATEGORY = "🤖dapaoAPI/豆包"
    DESCRIPTION = "使用豆包 AI 分析视频内容，支持 VIDEO 和图像批次两种输入格式 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_doubao_config()
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
    
    def analyze_video(self, **kwargs):
        """分析视频或图像批次，生成提示词"""
        
        video_input = kwargs.get("🎬 上传视频(VIDEO格式)")
        image_batch = kwargs.get("🖼️ 上传视频(图像批次)")
        template_name = kwargs.get("📋 提示词模板", "详细英文提示词")
        custom_prompt = kwargs.get("✏️ 自定义提示词", "")
        output_language = kwargs.get("🌐 输出语言", "英文")
        api_key = kwargs.get("🔑 API密钥", "")
        model_name = kwargs.get("🤖 视觉模型", "doubao-seed-1-6-vision-250815")
        max_frames = kwargs.get("🎞️ 最大帧数", 8)
        seed = kwargs.get("🎲 随机种子", 0)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        
        if not api_key:
            api_key = self.config.get("doubao_api_key", "")
        
        if not api_key:
            error_msg = "❌ 错误：未提供 API Key\n\n请执行以下操作之一：\n1. 在节点的【🔑 API密钥】参数中输入\n2. 编辑 doubao_config.json 文件配置"
            _log_error(error_msg)
            return ("", error_msg)
        
        if custom_prompt.strip():
            prompt_text = custom_prompt.strip()
            prompt_source = "自定义提示词"
            _log_info("使用自定义提示词")
        else:
            prompt_text = self.PROMPT_TEMPLATES.get(template_name, self.PROMPT_TEMPLATES["详细英文提示词"])
            prompt_source = f"模板: {template_name}"
            _log_info(f"使用预设模板: {template_name}")
        
        if output_language == "中文" and "英文" in prompt_text:
            prompt_text += "\n\n注意：请用中文输出最终结果。"
            _log_info("已添加中文输出要求")
        elif output_language == "英文" and "中文" in prompt_text:
            prompt_text += "\n\nNote: Please output the final result in English."
            _log_info("已添加英文输出要求")
        
        frames_tensor = None
        input_source = ""
        
        try:
            if video_input is not None:
                input_source = "VIDEO格式"
                _log_info("检测到 VIDEO 格式输入")
                
                try:
                    components = video_input.get_components()
                    frames_tensor = components.images  # 获取图像帧张量
                    _log_info(f"成功从 VIDEO 对象提取帧，形状: {frames_tensor.shape}")
                except Exception as e:
                    error_msg = f"❌ 错误：无法从 VIDEO 对象提取帧\n\n错误详情：{str(e)}"
                    _log_error(error_msg)
                    return ("", error_msg)
                    
            elif image_batch is not None:
                frames_tensor = image_batch
                input_source = "图像批次"
                _log_info("使用图像批次输入")
            else:
                error_msg = "❌ 错误：请提供视频或图像批次输入\n\n请在以下接口之一中提供数据：\n1. 🎬 上传视频(VIDEO格式)\n2. 🖼️ 上传视频(图像批次)"
                _log_error(error_msg)
                return ("", error_msg)
            
            total_frames = frames_tensor.shape[0]
            _log_info(f"输入源：{input_source}，总帧数：{total_frames}")
            
            if total_frames <= max_frames:
                sampled_indices = list(range(total_frames))
            else:
                step = total_frames / max_frames
                sampled_indices = [int(i * step) for i in range(max_frames)]
            
            _log_info(f"采样策略：从 {total_frames} 帧中采样 {len(sampled_indices)} 帧")
            _log_info(f"采样帧索引：{sampled_indices}")
            
            frame_base64_list = []
            for idx in sampled_indices:
                frame_tensor = frames_tensor[idx:idx+1]  # 保持批次维度
                _log_info(f"正在转换第 {idx+1}/{total_frames} 帧...")
                frame_base64 = tensor_to_base64(frame_tensor)
                if not frame_base64:
                    _log_warning(f"第 {idx+1} 帧转换失败，已跳过")
                    continue
                frame_base64_list.append((f"帧{idx+1}", frame_base64))
            
            if not frame_base64_list:
                error_msg = "❌ 错误：所有帧转换失败"
                _log_error(error_msg)
                return ("", error_msg)
            
            _log_info(f"成功转换 {len(frame_base64_list)} 帧")
            
            if seed_control == "固定":
                effective_seed = seed
                seed_mode = "固定"
            elif seed_control == "随机":
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            elif seed_control == "递增":
                if self.last_seed == 0:
                    effective_seed = seed if seed != 0 else random.randint(0, 0xffffffffffffffff)
                else:
                    effective_seed = self.last_seed + 1
                seed_mode = "递增"
            else:
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            
            self.last_seed = effective_seed
            random.seed(effective_seed)
            
            _log_info(f"调用豆包 Vision ({model_name}) 分析 {len(frame_base64_list)} 帧...")
            _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
            content_parts = [{"type": "text", "text": prompt_text}]
            
            for frame_name, frame_base64 in frame_base64_list:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": frame_base64}
                })
            
            base_url = self.config.get("doubao_base_url", "https://ark.cn-beijing.volces.com/api/v3")
            url = f"{base_url}/chat/completions"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
            
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": content_parts}],
                "stream": False
            }
            
            if effective_seed != 0:
                payload["seed"] = effective_seed
            
            timeout = self.config.get("timeout", 120)
            response = requests.post(url, headers=headers, json=payload, timeout=timeout, verify=False)
            
            if response.status_code != 200:
                error_msg = f"API调用失败: {response.status_code} - {response.text}"
                _log_error(error_msg)
                return ("", f"❌ API 调用失败：{error_msg}")
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                result_text = result["choices"][0]["message"]["content"]
                _log_info("✅ 视频分析成功")
            else:
                error_msg = f"响应格式错误: {result}"
                _log_error(error_msg)
                return ("", f"❌ 响应格式错误：{error_msg}")
            
            info_lines = [
                "🎉 豆包视频分析成功",
                "",
                "📊 分析信息：",
                f"   模型：{model_name}",
                f"   输入源：{input_source}",
                f"   总帧数：{total_frames} 帧",
                f"   采样帧数：{len(frame_base64_list)} 帧",
                f"   采样索引：{', '.join([str(i+1) for i in sampled_indices])}",
                "",
                "📝 提示词信息：",
                f"   来源：{prompt_source}",
                f"   输出语言：{output_language}",
                "",
                "🎲 种子信息：",
                f"   种子值：{effective_seed}",
                f"   控制模式：{seed_mode}",
                "",
                "✅ 分析完成"
            ]
            
            info = "\n".join(info_lines)
            
            return (result_text, info)
            
        except Exception as e:
            error_msg = f"""❌ 错误：视频分析失败

错误详情：{str(e)}

建议：
1. 检查网络连接
2. 检查 API Key 是否正确
3. 确认输入格式正确
4. 查看终端完整日志"""
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return ("", error_msg)


class Doubao_VideoGenerate:
    """
    🫐 豆包视频生成节点
    
    功能：
    - 调用火山方舟 Ark 的视频生成异步接口创建任务
    - 轮询任务状态，成功后输出视频 URL，并提供 VIDEO 类型输出以便连接保存节点
    
    说明：
    - 文本提示词会被拼接为：提示词 + 参数（如分辨率/时长/镜头固定等）
    - 可选输入首帧图，走图生视频（I2V）流程
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎬 生成模式": (["文生视频", "图生视频", "首尾帧视频"], {
                    "default": "文生视频"
                }),
                "🎨 提示词": ("STRING", {
                    "multiline": True,
                    "default": "天空的云飘动着，路上的车辆行驶",
                    "placeholder": "描述你想要生成的视频内容..."
                }),
                
                "🤖 模型名称": ("STRING", {
                    "default": "doubao-seedance-1-5-pro-251215",
                    "placeholder": "在火山方舟控制台查看对应的 Model ID"
                }),
                
                "🖥️ 分辨率": (["480p", "720p", "1080p"], {
                    "default": "720p"
                }),
                
                "📐 视频比例": (["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"], {
                    "default": "16:9"
                }),
                
                "⏱️ 时长(秒)": ("INT", {
                    "default": 5,
                    "min": 2,
                    "max": 12,
                    "step": 1
                }),
                
                "📷 镜头固定": ("BOOLEAN", {
                    "default": False
                }),
                
                "➕ 额外参数": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "可选：直接填写 Seedance 参数（例如：--cameramove 1），会原样拼接到提示词末尾"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则从 doubao_config.json 读取"
                }),
                
                "⏳ 最大等待(秒)": ("INT", {
                    "default": 600,
                    "min": 30,
                    "max": 3600,
                    "step": 10
                }),
                
                "🔁 查询间隔(秒)": ("INT", {
                    "default": 2,
                    "min": 1,
                    "max": 30,
                    "step": 1
                }),
            },
            "optional": {
                "🖼️ 首帧图": ("IMAGE",),
                "🖼️ 尾帧图": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🎥 视频URL", "📋 响应信息")
    FUNCTION = "generate_video"
    CATEGORY = "🤖dapaoAPI/豆包"
    DESCRIPTION = "调用豆包 Seedance 模型生成视频（异步任务轮询）| 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_doubao_config()
    
    def _build_prompt_text(self, prompt: str, resolution: str, ratio: str, duration: int, camera_fixed: bool, extra_args: str) -> str:
        prompt = (prompt or "").strip()
        extra_args = (extra_args or "").strip()
        camera_fixed_text = "true" if camera_fixed else "false"
        
        parts = [
            prompt,
            f"--resolution {resolution}",
            f"--ratio {ratio}",
            f"--duration {duration}",
            f"--camerafixed {camera_fixed_text}",
        ]
        if extra_args:
            parts.append(extra_args)
        return " ".join([p for p in parts if p])
    
    def _extract_task_id(self, create_result: dict) -> str:
        if not isinstance(create_result, dict):
            return ""
        if create_result.get("id"):
            return str(create_result["id"])
        data = create_result.get("data")
        if isinstance(data, dict) and data.get("id"):
            return str(data["id"])
        return ""
    
    def _extract_video_url(self, task_result: dict) -> str:
        if not isinstance(task_result, dict):
            return ""
        
        direct_candidates = [
            task_result.get("video_url"),
            task_result.get("url"),
        ]
        for c in direct_candidates:
            if isinstance(c, str) and c.startswith("http"):
                return c
        
        content = task_result.get("content")
        if isinstance(content, dict):
            for key in ("video_url", "url"):
                url = content.get(key)
                if isinstance(url, str) and url.startswith("http"):
                    return url
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") in ("video_url", "video"):
                    for key in ("video_url", "video"):
                        value = item.get(key)
                        if isinstance(value, dict):
                            url = value.get("url")
                            if isinstance(url, str) and url.startswith("http"):
                                return url
                        if isinstance(value, str) and value.startswith("http"):
                            return value
                for key in ("url", "video_url"):
                    url = item.get(key)
                    if isinstance(url, str) and url.startswith("http"):
                        return url
        
        result = task_result.get("result")
        if isinstance(result, dict):
            for key in ("video_url", "url"):
                url = result.get(key)
                if isinstance(url, str) and url.startswith("http"):
                    return url
            result_content = result.get("content")
            if isinstance(result_content, list):
                for item in result_content:
                    if not isinstance(item, dict):
                        continue
                    url = item.get("url")
                    if isinstance(url, str) and url.startswith("http"):
                        return url
        
        return ""
    
    def _extract_status(self, task_result: dict) -> str:
        if not isinstance(task_result, dict):
            return "unknown"
        
        for key in ("status", "state"):
            v = task_result.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()
        
        data = task_result.get("data")
        if isinstance(data, dict):
            v = data.get("status") or data.get("state")
            if isinstance(v, str) and v.strip():
                return v.strip()
        
        return "unknown"
    
    def _download_video_to_output(self, video_url: str, task_id: str) -> tuple[str, str]:
        if not video_url or not isinstance(video_url, str) or not video_url.startswith("http"):
            return "", "video_url 为空或不合法"
        
        if folder_paths is None:
            return "", "folder_paths 不可用，无法确定输出目录"
        
        try:
            output_root = folder_paths.get_output_directory()
            target_dir = os.path.join(output_root, "video", "dapaoAPI")
            os.makedirs(target_dir, exist_ok=True)
            
            safe_task_id = (task_id or "task").replace("/", "_").replace("\\", "_")
            target_path = os.path.join(target_dir, f"doubao_{safe_task_id}.mp4")
            
            _log_info(f"开始预下载视频到输出目录: {target_path}")
            r = requests.get(video_url, stream=True, timeout=300, allow_redirects=True, verify=False)
            r.raise_for_status()
            
            total_bytes = 0
            with open(target_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        f.write(chunk)
                        total_bytes += len(chunk)
            
            _log_info(f"预下载完成，大小: {round(total_bytes / 1024 / 1024, 2)} MB")
            return target_path, ""
        except Exception as e:
            return "", str(e)
    
    def generate_video(self, **kwargs):
        mode = kwargs.get("🎬 生成模式", "文生视频")
        prompt = kwargs.get("🎨 提示词", "")
        model_name = kwargs.get("🤖 模型名称", "doubao-seedance-1-5-pro-251215")
        resolution = kwargs.get("🖥️ 分辨率", "720p")
        ratio = kwargs.get("📐 视频比例", "16:9")
        duration = int(kwargs.get("⏱️ 时长(秒)", 5))
        camera_fixed = bool(kwargs.get("📷 镜头固定", False))
        extra_args = kwargs.get("➕ 额外参数", "")
        api_key = kwargs.get("🔑 API密钥", "")
        max_wait_seconds = int(kwargs.get("⏳ 最大等待(秒)", 600))
        poll_interval = int(kwargs.get("🔁 查询间隔(秒)", 2))
        first_frame = kwargs.get("🖼️ 首帧图")
        last_frame = kwargs.get("🖼️ 尾帧图")
        
        if not (prompt or "").strip():
            raise ValueError("❌ 错误：请输入提示词")
        
        if not api_key:
            api_key = self.config.get("doubao_api_key", "")
        if not api_key:
            raise ValueError("❌ 错误：请配置豆包 API Key（节点参数或 doubao_config.json）")
        
        base_url = self.config.get("doubao_base_url", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")
        create_url = f"{base_url}/contents/generations/tasks"
        
        prompt_text = self._build_prompt_text(prompt, resolution, ratio, duration, camera_fixed, extra_args)
        _log_info(f"开始创建视频生成任务，模型：{model_name}")
        
        content = [{"type": "text", "text": prompt_text}]
        
        if mode == "文生视频":
            if first_frame is not None or last_frame is not None:
                raise ValueError("❌ 错误：文生视频模式不需要首帧图/尾帧图，请清空后重试")
        elif mode == "图生视频":
            if first_frame is None:
                raise ValueError("❌ 错误：图生视频模式必须提供首帧图")
            if last_frame is not None:
                raise ValueError("❌ 错误：图生视频模式不支持尾帧图，请切换为首尾帧视频")
        elif mode == "首尾帧视频":
            if first_frame is None or last_frame is None:
                raise ValueError("❌ 错误：首尾帧视频模式必须同时提供首帧图和尾帧图")
        else:
            raise ValueError(f"❌ 错误：未知生成模式: {mode}")
        
        if first_frame is not None:
            first_frame_base64 = tensor_to_base64(first_frame)
            if not first_frame_base64:
                raise ValueError("❌ 错误：首帧图转换失败，请检查输入图像")
            content.append({"type": "image_url", "image_url": {"url": first_frame_base64}})
        
        if last_frame is not None:
            last_frame_base64 = tensor_to_base64(last_frame)
            if not last_frame_base64:
                raise ValueError("❌ 错误：尾帧图转换失败，请检查输入图像")
            content.append({"type": "image_url", "image_url": {"url": last_frame_base64}})
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }
        payload = {
            "model": model_name,
            "content": content,
        }
        
        timeout = int(self.config.get("timeout", 120))
        pbar = comfy.utils.ProgressBar(100)
        pbar.update_absolute(5)
        
        response = requests.post(create_url, headers=headers, json=payload, timeout=timeout, verify=False)
        if response.status_code != 200:
            raise ValueError(f"❌ 创建任务失败: {response.status_code} - {response.text}")
        
        create_result = response.json()
        task_id = self._extract_task_id(create_result)
        if not task_id:
            raise ValueError(f"❌ 创建任务返回缺少 task_id: {create_result}")
        
        _log_info(f"任务创建成功，task_id: {task_id}")
        pbar.update_absolute(15)
        
        get_url = f"{base_url}/contents/generations/tasks/{task_id}"
        start_time = time.time()
        attempts = 0
        last_status = "unknown"
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait_seconds:
                raise TimeoutError(f"❌ 等待超时：{max_wait_seconds} 秒内未生成完成（最后状态：{last_status}）")
            
            attempts += 1
            try:
                r = requests.get(get_url, headers=headers, timeout=timeout, verify=False)
                if r.status_code != 200:
                    time.sleep(poll_interval)
                    continue
                
                task_result = r.json()
                status = self._extract_status(task_result).lower()
                last_status = status
                
                if status in ("succeeded", "success", "completed", "done"):
                    video_url = self._extract_video_url(task_result)
                    if not video_url:
                        raise ValueError(f"❌ 任务已完成但未解析到视频 URL: {task_result}")
                    
                    local_video_path, download_error = self._download_video_to_output(video_url, task_id)
                    adapter = DoubaoVideoAdapter(local_video_path if local_video_path else video_url)
                    pbar.update_absolute(100)
                    
                    info = {
                        "model": model_name,
                        "task_id": task_id,
                        "status": status,
                        "prompt": prompt,
                        "prompt_with_args": prompt_text,
                        "resolution": resolution,
                        "ratio": ratio,
                        "duration": duration,
                        "camera_fixed": camera_fixed,
                        "mode": mode,
                        "has_first_frame": first_frame is not None,
                        "has_last_frame": last_frame is not None,
                        "video_url": video_url,
                        "local_video_path": local_video_path,
                        "local_download_error": download_error,
                        "attempts": attempts,
                        "elapsed_seconds": round(elapsed, 2),
                        "raw_response": task_result,
                    }
                    
                    _log_info("✅ 视频生成完成")
                    return (adapter, video_url, json.dumps(info, ensure_ascii=False, indent=2))
                
                if status in ("failed", "error"):
                    raise ValueError(f"❌ 任务失败: {task_result}")
                
                progress = 15 + min(80, int((elapsed / max_wait_seconds) * 80))
                pbar.update_absolute(progress)
            
            except Exception as e:
                _log_warning(f"轮询异常（第 {attempts} 次）: {e}")
            
            time.sleep(poll_interval)

# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "Doubao_Chat": Doubao_Chat,
    "Doubao_ImageToPrompt": Doubao_ImageToPrompt,
    "Doubao_VideoToPrompt": Doubao_VideoToPrompt,
    "Doubao_VideoGenerate": Doubao_VideoGenerate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Doubao_Chat": "💬 豆包LLM对话 @炮老师的小课堂",
    "Doubao_ImageToPrompt": "🔍 豆包图像反推 @炮老师的小课堂",
    "Doubao_VideoToPrompt": "🎬 豆包视频反推 @炮老师的小课堂",
    "Doubao_VideoGenerate": "🫐豆包视频生成@炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

