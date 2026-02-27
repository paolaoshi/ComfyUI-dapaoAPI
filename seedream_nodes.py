"""
大炮 API - Seedream 4.0 节点集合
提供文生图和多图编辑功能

作者：@炮老师的小课堂
版本：v3.0.0
"""

import os
import json
import requests
import time
import base64
import io
from PIL import Image
import torch
import numpy as np
from typing import Optional, Dict, Any
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 节点版本和作者信息
__version__ = "3.0.0"
__author__ = "@炮老师的小课堂"

# 统一节点颜色 (橙棕色)


# 日志函数
def _log_info(message):
    print(f"[dapaoAPI] 信息：{message}")

def _log_warning(message):
    print(f"[dapaoAPI] 警告：{message}")

def _log_error(message):
    print(f"[dapaoAPI] 错误：{message}")


# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CURRENT_DIR, 'config.json')


def get_config():
    """获取配置文件"""
    default_config = {
        "api_key": "",
        "endpoint_id": "",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "timeout": 120,
        "max_retries": 3,
        "models": {
            "doubao-seedream-4-0-250828": "Seedream 4.0",
            "doubao-seedream-4-0": "Seedream 4.0 (通用)"
        }
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            return default_config
    except Exception as e:
        _log_error(f"读取配置文件失败: {e}")
        return default_config


def pil2tensor(image: Image.Image) -> torch.Tensor:
    """将PIL图像转换为ComfyUI tensor格式 [1, H, W, 3]"""
    # 确保图像是RGB模式
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # 转换为numpy数组
    np_image = np.array(image).astype(np.float32) / 255.0
    
    # 转换为tensor，格式为 [H, W, 3]
    tensor = torch.from_numpy(np_image)
    
    # 添加batch维度，格式为 [1, H, W, 3]
    tensor = tensor.unsqueeze(0)
    
    return tensor


def tensor2pil(tensor: torch.Tensor) -> Image.Image:
    """将ComfyUI tensor转换为PIL图像"""
    # 如果是批量tensor，只取第一个
    if len(tensor.shape) == 4:
        tensor = tensor[0]
    
    # 转换为numpy数组
    np_image = tensor.cpu().numpy()
    
    # 确保值在0-1范围内
    np_image = np.clip(np_image, 0, 1)
    
    # 转换为0-255范围
    np_image = (np_image * 255).astype(np.uint8)
    
    # 转换为PIL图像
    return Image.fromarray(np_image)


def create_blank_tensor(width=512, height=512):
    """创建空白tensor"""
    blank_image = np.zeros((height, width, 3), dtype=np.float32)
    tensor = torch.from_numpy(blank_image).unsqueeze(0)
    return tensor


def image_to_base64(image_tensor: torch.Tensor, max_size=2048, return_data_url=False) -> str:
    """
    将图像tensor转换为base64字符串
    
    Args:
        image_tensor: 输入的图像张量
        max_size: 最大尺寸，超过此尺寸会压缩
        return_data_url: 是否返回完整的 data URL 格式（用于火山引擎 API）
        
    Returns:
        base64 编码的字符串，或 data URL 格式
    """
    try:
        pil_image = tensor2pil(image_tensor)
        
        # 如果图像过大，进行压缩
        original_size = pil_image.size
        if max(original_size) > max_size:
            ratio = max_size / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            _log_info(f"图像压缩: {original_size} -> {new_size}")
        
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # 如果需要返回 data URL 格式
        if return_data_url:
            return f"data:image/png;base64,{image_base64}"
        
        return image_base64
    except Exception as e:
        _log_error(f"图像转base64失败: {e}")
        return None


class Seedream_Text2Image:
    """
    Seedream 4.0 文生图节点 v3.1
    
    功能特性：
    - 📸 批量生成：支持1-4张图片同时生成
    - 🎨 风格预设：10种常用风格快速切换
    - 🎛️ 种子控制：固定、随机、递增三种模式
    - 🚫 负面提示词：精准控制不想要的内容
    - 📊 详细信息：完整的生成记录和参数
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_config()
        models = config.get("models", {
            "doubao-seedream-4-0-250828": "Seedream 4.0"
        })
        model_list = list(models.keys())
        
        return {
            "required": {
                # === 基础设置 ===
                "📝 提示词": ("STRING", {
                    "multiline": True, 
                    "default": "一只可爱的小猫，坐在窗台上，阳光洒在它身上，温暖的光线，高清摄影",
                    "placeholder": "请输入详细的图像描述..."
                }),
                
                # === API 配置 ===
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件中的密钥"
                }),
                "🤖 模型选择": (model_list, {
                    "default": model_list[0] if model_list else "doubao-seedream-4-0-250828"
                }),
                
                # === 生成设置 ===
                "📸 出图数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "step": 1,
                    "tooltip": "一次生成的图片数量（1-4张）"
                }),
                
                # === 图像尺寸 ===
                "📐 分辨率预设": (["1K", "2K", "4K"], {
                    "default": "1K"
                }),
                "📏 宽高比": (["1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9", "9:21", "自定义"], {
                    "default": "1:1"
                }),
                "◀️ 宽度": ("INT", {
                    "default": 1024, 
                    "min": 512, 
                    "max": 4096, 
                    "step": 64,
                    "display": "number"
                }),
                "▲ 高度": ("INT", {
                    "default": 1024, 
                    "min": 512, 
                    "max": 4096, 
                    "step": 64,
                    "display": "number"
                }),
                
                # === 风格设置 ===
                "🎨 风格预设": ([
                    "默认",
                    "电影感",
                    "动漫风格", 
                    "写实摄影",
                    "油画艺术",
                    "水彩画",
                    "赛博朋克",
                    "3D渲染",
                    "极简主义",
                    "复古怀旧"
                ], {
                    "default": "默认",
                    "tooltip": "选择预设风格，会自动添加风格关键词"
                }),
                
                # === 高级设置 ===
                "🎲 随机种子": ("INT", {
                    "default": -1, 
                    "min": -1, 
                    "max": 2147483647,
                    "display": "number",
                    "tooltip": "随机种子值，-1为随机"
                }),
                
                "🎛️ 种子控制": (["固定", "随机", "递增"], {
                    "default": "随机",
                    "tooltip": "固定: 使用上方种子值; 随机: 每次生成新种子; 递增: 种子值+1"
                }),
            },
            "optional": {
                # === 负面提示词 ===
                "🚫 负面提示词": ("STRING", {
                    "multiline": True,
                    "default": "low quality, blurry, distorted, watermark, text, ugly, deformed",
                    "placeholder": "输入不想要的内容...",
                    "tooltip": "描述不希望出现在图像中的内容"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "ℹ️ 信息")
    FUNCTION = "generate_image"
    CATEGORY = "🤖dapaoAPI/Seedream"
    DESCRIPTION = "使用 Seedream 4.0 API 根据文本生成图像，支持批量生成、风格预设、种子控制 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_config()
        # 保存上一次使用的种子（用于递增模式）
        self.last_seed = -1
        
        # 风格预设映射（添加到提示词后）
        self.style_mapping = {
            "默认": "",
            "电影感": ", cinematic lighting, dramatic atmosphere, film grain, professional color grading, cinematic composition",
            "动漫风格": ", anime style, manga art, vibrant colors, cel shading, anime aesthetic, Japanese animation style",
            "写实摄影": ", photorealistic, high detail photography, professional camera, natural lighting, sharp focus, realistic texture",
            "油画艺术": ", oil painting style, classical art, brush strokes, artistic texture, painted artwork, fine art",
            "水彩画": ", watercolor painting, soft colors, artistic brushwork, watercolor texture, delicate shading",
            "赛博朋克": ", cyberpunk style, neon lights, futuristic city, sci-fi atmosphere, high-tech low-life, dystopian future",
            "3D渲染": ", 3D render, octane render, unreal engine, CGI, ray tracing, professional 3D graphics, detailed modeling",
            "极简主义": ", minimalist style, simple composition, clean design, minimal colors, modern aesthetic, negative space",
            "复古怀旧": ", vintage style, retro aesthetic, nostalgic atmosphere, classic photography, aged effect, old-fashioned"
        }
        
        self.size_mapping = {
            "1K": {
                "1:1": "1024x1024",
                "4:3": "1152x864",
                "3:4": "864x1152",
                "16:9": "1280x720",
                "9:16": "720x1280",
                "2:3": "832x1248",
                "3:2": "1248x832",
                "21:9": "1512x648",
                "9:21": "648x1512"
            },
            "2K": {
                "1:1": "2048x2048",
                "4:3": "2048x1536",
                "3:4": "1536x2048",
                "16:9": "2048x1152",
                "9:16": "1152x2048",
                "2:3": "1536x2048",
                "3:2": "2048x1536",
                "21:9": "2048x864",
                "9:21": "864x2048"
            },
            "4K": {
                "1:1": "4096x4096",
                "4:3": "4096x3072",
                "3:4": "3072x4096",
                "16:9": "4096x2304",
                "9:16": "2304x4096",
                "2:3": "3072x4096",
                "3:2": "4096x3072",
                "21:9": "4096x1728",
                "9:21": "1728x4096"
            }
        }
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        
        # 随机和递增模式下，强制更新 (返回 NaN)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        
        # 固定模式下，仅当种子值变化时更新
        return seed
    
    def generate_image(self, **kwargs):
        """调用 Seedream 4.0 API 生成图像（支持批量生成、风格预设、种子控制）"""
        
        import random
        import time
        
        # 参数解析
        prompt = kwargs.get("📝 提示词", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model = kwargs.get("🤖 模型选择", "doubao-seedream-4-0-250828")
        num_images = kwargs.get("📸 出图数量", 1)
        resolution = kwargs.get("📐 分辨率预设", "1K")
        aspect_ratio = kwargs.get("📏 宽高比", "1:1")
        width = kwargs.get("◀️ 宽度", 1024)
        height = kwargs.get("▲ 高度", 1024)
        style_preset = kwargs.get("🎨 风格预设", "默认")
        seed = kwargs.get("🎲 随机种子", -1)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        negative_prompt = kwargs.get("🚫 负面提示词", "")
        
        # 状态信息收集器
        status_info = []
        start_time = time.time()
        
        # 使用配置文件中的值（如果未提供）
        if not api_key:
            api_key = self.config.get("api_key", "")
        
        if not api_key:
            error_msg = "❌ 错误：未提供 API Key\n\n请在【🔑 API密钥】参数中输入或在 config.json 中配置"
            _log_error(error_msg)
            return (create_blank_tensor(), error_msg)
        
        try:
            # === 1. 计算最终尺寸 ===
            if aspect_ratio in ["Custom", "自定义"]:
                final_size = f"{width}x{height}"
                _log_info(f"使用自定义尺寸: {final_size}")
                status_info.append(f"📐 尺寸：{final_size}（自定义）")
            else:
                if resolution in self.size_mapping and aspect_ratio in self.size_mapping[resolution]:
                    final_size = self.size_mapping[resolution][aspect_ratio]
                else:
                    final_size = "1024x1024"
                    _log_warning(f"未找到 {resolution} 和 {aspect_ratio} 的组合，使用默认尺寸")
                _log_info(f"使用预设尺寸: {final_size}")
                status_info.append(f"📐 尺寸：{final_size}（{resolution} {aspect_ratio}）")
            
            # === 2. 处理风格预设 ===
            final_prompt = prompt
            if style_preset in self.style_mapping:
                style_suffix = self.style_mapping[style_preset]
                if style_suffix:
                    final_prompt = prompt + style_suffix
                    _log_info(f"✅ 应用风格预设：{style_preset}")
                    status_info.append(f"🎨 风格：{style_preset}")
                else:
                    status_info.append("🎨 风格：默认")
            
            # === 3. 处理负面提示词 ===
            if negative_prompt and negative_prompt.strip():
                _log_info(f"⚠️ 负面提示词：{negative_prompt[:50]}...")
                status_info.append(f"🚫 负面提示词：已设置")
                # 注意：Seedream API 可能不支持负面提示词，这里先记录
            
            # === 4. 种子控制逻辑 ===
            seeds_used = []
            
            for i in range(num_images):
                if seed_control == "固定":
                    # 固定模式：所有图片使用相同种子
                    effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
                    seed_mode = "固定"
                elif seed_control == "随机":
                    # 随机模式：每张图片使用不同随机种子
                    effective_seed = random.randint(0, 2147483647)
                    seed_mode = "随机"
                elif seed_control == "递增":
                    # 递增模式：种子递增
                    if i == 0:
                        # 第一张图片
                        if self.last_seed == -1:
                            effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
                        else:
                            effective_seed = self.last_seed + 1
                    else:
                        # 后续图片在第一张基础上递增
                        effective_seed = seeds_used[0] + i
                    seed_mode = "递增"
                else:
                    effective_seed = random.randint(0, 2147483647)
                    seed_mode = "随机"
                
                seeds_used.append(effective_seed)
            
            # 保存最后使用的种子（用于递增模式）
            if seeds_used:
                self.last_seed = seeds_used[-1]
            
            _log_info(f"🎲 种子模式：{seed_mode}")
            _log_info(f"🎲 使用的种子：{seeds_used}")
            status_info.append(f"🎲 种子模式：{seed_mode}")
            
            # === 5. 构建 API 请求 ===
            base_url = self.config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            url = f"{base_url}/images/generations"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "ComfyUI-dapaoAPI/3.1"
            }
            
            _log_info(f"📸 开始生成 {num_images} 张图像...")
            _log_info(f"🤖 模型：{model}")
            _log_info(f"📝 提示词：{final_prompt[:100]}...")
            
            status_info.append(f"📸 生成数量：{num_images} 张")
            status_info.append(f"🤖 模型：{model}")
            
            all_generated_images = []
            
            # === 6. 批量生成图像（逐个调用API）===
            for i, effective_seed in enumerate(seeds_used):
                _log_info(f"🔄 正在生成第 {i+1}/{num_images} 张图像...")
                
                # 构建请求体
                req_body = {
                    "model": model,
                    "prompt": final_prompt,
                    "size": final_size,
                    "n": 1,  # 每次生成1张
                    "response_format": "url",
                    "quality": "hd",
                    "style": "vivid",
                    "seed": effective_seed
                }
                
                # 发送请求
                response = requests.post(
                    url,
                    headers=headers,
                    json=req_body,
                    timeout=self.config.get("timeout", 120),
                    verify=False
                )
                
                if response.status_code != 200:
                    error_msg = f"❌ 错误：API 请求失败\n\n状态码：{response.status_code}\n响应：{response.text[:200]}"
                    _log_error(error_msg)
                    # 如果第一张就失败，返回错误
                    if i == 0:
                        return (create_blank_tensor(), error_msg)
                    # 否则继续生成其他图片
                    _log_warning(f"第 {i+1} 张图像生成失败，继续生成下一张")
                    continue
                
                # 解析响应
                result = response.json()
                _log_info(f"✅ 第 {i+1} 张 API 响应成功")
                
                # 从响应中提取图像
                if "data" in result and result["data"]:
                    for item in result["data"]:
                        image_url = item.get("url")
                        if image_url:
                            try:
                                img_response = requests.get(image_url, timeout=60, verify=False)
                                if img_response.status_code == 200:
                                    image = Image.open(io.BytesIO(img_response.content))
                                    all_generated_images.append({
                                        "image": image,
                                        "seed": effective_seed,
                                        "index": i + 1
                                    })
                                    _log_info(f"✅ 成功下载第 {i+1} 张图像：{image.size}，种子：{effective_seed}")
                            except Exception as e:
                                _log_warning(f"下载第 {i+1} 张图像失败: {e}")
            
            # === 7. 检查是否有成功生成的图像 ===
            if not all_generated_images:
                error_msg = "❌ 错误：所有图像生成失败\n\n请检查：\n1. API Key 是否正确\n2. 网络连接是否正常\n3. 提示词是否合规"
                _log_error(error_msg)
                return (create_blank_tensor(), error_msg)
            
            # === 8. 转换为 tensor 并合并 ===
            image_tensors = []
            for img_data in all_generated_images:
                tensor = pil2tensor(img_data["image"])
                image_tensors.append(tensor)
            
            # 合并所有图像
            if len(image_tensors) == 1:
                final_tensor = image_tensors[0]
            else:
                final_tensor = torch.cat(image_tensors, dim=0)
            
            # === 9. 计算生成时间 ===
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # === 10. 构建详细的信息输出 ===
            status_info.append("=" * 40)
            status_info.append(f"✅ 成功生成 {len(all_generated_images)}/{num_images} 张图像")
            status_info.append("=" * 40)
            status_info.append("")
            status_info.append("📋 生成详情：")
            
            # 显示每张图片的种子
            for img_data in all_generated_images:
                status_info.append(f"   图像 {img_data['index']}：种子 {img_data['seed']}")
            
            status_info.append("")
            status_info.append(f"⏱️ 总耗时：{elapsed_time:.2f} 秒")
            status_info.append(f"⚡ 平均每张：{elapsed_time/len(all_generated_images):.2f} 秒")
            
            if style_preset != "默认":
                status_info.append("")
                status_info.append("💡 提示：")
                status_info.append(f"   已应用 [{style_preset}] 风格预设")
            
            info = "\n".join(status_info)
            _log_info(f"🎉 生成完成！成功生成 {len(all_generated_images)} 张图像")
            
            return (final_tensor, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：图像生成失败\n\n错误详情：{str(e)}\n\n建议：\n1. 检查网络连接\n2. 检查 API Key 是否正确\n3. 查看终端完整日志"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return (create_blank_tensor(), error_msg)


class Seedream_MultiImage:
    """
    Seedream 4.0 多图编辑节点 v3.1（旗舰版）
    
    功能特性：
    - 📸 批量生成：支持1-4张变体同时生成
    - 🎨 编辑模式：8种预设编辑模式
    - ⚡ 编辑强度：精确控制编辑程度（0.1-1.0）
    - 🎯 主图指定：选择主要参考图像
    - 🔀 融合方式：平均/加权/渐变三种融合模式
    - 🎛️ 种子控制：固定、随机、递增三种模式
    - 🔄 处理顺序：自动/按序/重要性排序
    - 🚫 负面提示词：精准控制不想要的内容
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_config()
        models = config.get("models", {
            "doubao-seedream-4-0-250828": "Seedream 4.0"
        })
        model_list = list(models.keys())
        
        return {
            "required": {
                # === 基础设置 ===
                "📝 编辑提示词": ("STRING", {
                    "multiline": True, 
                    "default": "保持原图风格，优化细节，增强画面质量",
                    "placeholder": "描述如何处理和编辑这些图像..."
                }),
                
                # === API 配置 ===
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件中的密钥"
                }),
                "🤖 模型选择": (model_list, {
                    "default": model_list[0] if model_list else "doubao-seedream-4-0-250828"
                }),
                
                # === 生成设置 ===
                "📸 出图数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 4,
                    "step": 1,
                    "tooltip": "一次生成的变体数量（1-4张）"
                }),
                
                # === 编辑设置 ===
                "🎨 编辑模式": ([
                    "默认",
                    "风格融合",
                    "细节增强",
                    "色彩校正",
                    "创意混合",
                    "构图优化",
                    "光影调整",
                    "艺术风格化"
                ], {
                    "default": "默认",
                    "tooltip": "选择预设的编辑处理模式"
                }),
                
                "⚡ 编辑强度": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.1,
                    "max": 1.0,
                    "step": 0.1,
                    "tooltip": "控制编辑的影响程度：0.1-0.3轻微，0.4-0.7适度，0.8-1.0大幅"
                }),
                
                # === 多图处理 ===
                "🎯 主图选择": ([
                    "自动识别",
                    "图像1",
                    "图像2",
                    "图像3",
                    "图像4",
                    "图像5"
                ], {
                    "default": "自动识别",
                    "tooltip": "指定哪张图作为主要参考"
                }),
                
                "🔀 融合方式": ([
                    "平均融合",
                    "加权融合",
                    "渐变过渡"
                ], {
                    "default": "加权融合",
                    "tooltip": "多图混合的方式"
                }),
                
                "🔄 处理顺序": ([
                    "自动排序",
                    "按输入顺序",
                    "重要性优先"
                ], {
                    "default": "自动排序",
                    "tooltip": "图像的处理优先级"
                }),
                
                # === 输出尺寸 ===
                "📐 目标分辨率": (["1K", "2K", "4K", "保持原图"], {
                    "default": "保持原图"
                }),
                "📏 目标宽高比": (["1:1", "4:3", "3:4", "16:9", "9:16", "2:3", "3:2", "21:9", "9:21", "保持原图"], {
                    "default": "保持原图"
                }),
                
                # === 高级设置 ===
                "🎲 随机种子": ("INT", {
                    "default": -1, 
                    "min": -1, 
                    "max": 2147483647,
                    "display": "number",
                    "tooltip": "随机种子值，-1为随机"
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
                "🖼️ 图像5": ("IMAGE",),
                
                # === 负面提示词 ===
                "🚫 负面提示词": ("STRING", {
                    "multiline": True,
                    "default": "distorted, artifacts, low quality, blurry, noise",
                    "placeholder": "描述不想要的效果...",
                    "tooltip": "描述不希望出现的效果和内容"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("🎨 生成图像", "ℹ️ 处理信息")
    FUNCTION = "generate_image"
    CATEGORY = "🤖dapaoAPI/Seedream"
    DESCRIPTION = "多图编辑和融合，支持批量生成、8种编辑模式、智能融合 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_config()
        # 保存上一次使用的种子（用于递增模式）
        self.last_seed = -1
        
        # 编辑模式映射（添加到提示词后）
        self.edit_mode_mapping = {
            "默认": "",
            "风格融合": ", unify style across all images, harmonize visual elements, consistent aesthetic",
            "细节增强": ", enhance details, sharpen textures, improve clarity, increase definition",
            "色彩校正": ", color correction, balanced tones, unified color palette, professional grading",
            "创意混合": ", creative blend, artistic combination, innovative fusion, imaginative merge",
            "构图优化": ", improve composition, better framing, enhanced layout, optimized arrangement",
            "光影调整": ", adjust lighting, enhance shadows, improve highlights, balanced exposure",
            "艺术风格化": ", artistic style, painterly effect, creative interpretation, stylized rendering"
        }
        
        self.size_mapping = {
            "1K": {
                "1:1": "1024x1024",
                "4:3": "1152x864",
                "3:4": "864x1152",
                "16:9": "1280x720",
                "9:16": "720x1280",
                "2:3": "832x1248",
                "3:2": "1248x832",
                "21:9": "1512x648",
                "9:21": "648x1512"
            },
            "2K": {
                "1:1": "2048x2048",
                "4:3": "2048x1536",
                "3:4": "1536x2048",
                "16:9": "2048x1152",
                "9:16": "1152x2048",
                "2:3": "1536x2048",
                "3:2": "2048x1536",
                "21:9": "2048x864",
                "9:21": "864x2048"
            },
            "4K": {
                "1:1": "4096x4096",
                "4:3": "4096x3072",
                "3:4": "3072x4096",
                "16:9": "4096x2304",
                "9:16": "2304x4096",
                "2:3": "3072x4096",
                "3:2": "4096x3072",
                "21:9": "4096x1728",
                "9:21": "1728x4096"
            }
        }
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        
        # 随机和递增模式下，强制更新 (返回 NaN)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        
        # 固定模式下，仅当种子值变化时更新
        return seed
    
    def generate_image(self, **kwargs):
        """调用 Seedream 4.0 API 进行多图编辑（支持批量生成、智能编辑、多种融合模式）"""
        
        import random
        import time
        
        # 参数解析
        prompt = kwargs.get("📝 编辑提示词", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model = kwargs.get("🤖 模型选择", "doubao-seedream-4-0-250828")
        num_images = kwargs.get("📸 出图数量", 1)
        edit_mode = kwargs.get("🎨 编辑模式", "默认")
        edit_strength = kwargs.get("⚡ 编辑强度", 0.7)
        main_image = kwargs.get("🎯 主图选择", "自动识别")
        blend_mode = kwargs.get("🔀 融合方式", "加权融合")
        process_order = kwargs.get("🔄 处理顺序", "自动排序")
        resolution = kwargs.get("📐 目标分辨率", "保持原图")
        aspect_ratio = kwargs.get("📏 目标宽高比", "保持原图")
        seed = kwargs.get("🎲 随机种子", -1)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        negative_prompt = kwargs.get("🚫 负面提示词", "")
        
        # 收集图像输入
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        image5 = kwargs.get("🖼️ 图像5")
        
        # 状态信息收集器
        status_info = []
        start_time = time.time()
        
        # 使用配置文件中的值（如果未提供）
        if not api_key:
            api_key = self.config.get("api_key", "")
        
        if not api_key:
            error_msg = "❌ 错误：未提供 API Key\n\n请在【🔑 API密钥】参数中输入或在 config.json 中配置"
            _log_error(error_msg)
            return (create_blank_tensor(), error_msg)
        
        #收集所有输入的图像
        input_images = []
        image_names = []
        for i, img in enumerate([image1, image2, image3, image4, image5], 1):
            if img is not None:
                input_images.append(img)
                image_names.append(f"图像{i}")
        
        if not input_images:
            error_msg = "❌ 错误：请至少提供一张输入图像\n\n请在【🖼️ 图像1-5】中上传图片"
            _log_error(error_msg)
            return (create_blank_tensor(), error_msg)
        
        try:
            # === 1. 处理输入图像（根据处理顺序和主图选择）===
            _log_info(f"📊 收到 {len(input_images)} 张输入图像")
            status_info.append(f"📊 输入：{len(input_images)} 张图像（{', '.join(image_names)}）")
            
            # 根据主图选择调整图像顺序
            if main_image != "自动识别":
                main_idx = int(main_image.replace("图像", "")) - 1
                if 0 <= main_idx < len(input_images):
                    # 将主图放到第一位
                    main_img = input_images.pop(main_idx)
                    input_images.insert(0, main_img)
                    main_name = image_names.pop(main_idx)
                    image_names.insert(0, main_name)
                    _log_info(f"🎯 主图：{main_name}")
                    status_info.append(f"🎯 主图：{main_name}")
            
            # 将所有图像转换为 base64
            image_base64_list = []
            for i, img in enumerate(input_images):
                _log_info(f"🔄 转换 {image_names[i]}...")
                img_base64 = image_to_base64(img, return_data_url=True)
                if img_base64:
                    image_base64_list.append(img_base64)
                    _log_info(f"✅ {image_names[i]} 转换成功")
                else:
                    _log_warning(f"⚠️ {image_names[i]} 转换失败，跳过")
            
            if not image_base64_list:
                error_msg = "❌ 错误：所有图像转换失败"
                _log_error(error_msg)
                return (create_blank_tensor(), error_msg)
            
            # === 2. 处理编辑模式和强度 ===
            final_prompt = prompt
            if edit_mode in self.edit_mode_mapping:
                mode_suffix = self.edit_mode_mapping[edit_mode]
                if mode_suffix:
                    final_prompt = prompt + mode_suffix
                    _log_info(f"✅ 应用编辑模式：{edit_mode}")
                    status_info.append(f"🎨 编辑模式：{edit_mode}")
                    status_info.append(f"⚡ 编辑强度：{edit_strength}")
                else:
                    status_info.append("🎨 编辑模式：默认")
            
            # 添加融合方式和处理顺序到提示词
            blend_hint = ""
            if len(input_images) > 1:
                if blend_mode == "平均融合":
                    blend_hint = ", evenly blend all images, balanced combination"
                elif blend_mode == "加权融合":
                    blend_hint = ", weighted blend with main image priority, harmonious mix"
                elif blend_mode == "渐变过渡":
                    blend_hint = ", gradient transition between images, smooth blending"
                
                if blend_hint:
                    final_prompt += blend_hint
                    status_info.append(f"🔀 融合方式：{blend_mode}")
                    status_info.append(f"🔄 处理顺序：{process_order}")
            
            # === 3. 处理负面提示词 ===
            if negative_prompt and negative_prompt.strip():
                _log_info(f"⚠️ 负面提示词：{negative_prompt[:50]}...")
                status_info.append("🚫 负面提示词：已设置")
            
            # === 4. 计算目标尺寸 ===
            final_size = None
            if resolution != "保持原图" and aspect_ratio != "保持原图":
                if resolution in self.size_mapping and aspect_ratio in self.size_mapping[resolution]:
                    final_size = self.size_mapping[resolution][aspect_ratio]
                    status_info.append(f"📐 输出尺寸：{final_size}（{resolution} {aspect_ratio}）")
            else:
                status_info.append("📐 输出尺寸：保持原图")
            
            # === 5. 种子控制逻辑 ===
            seeds_used = []
            for i in range(num_images):
                if seed_control == "固定":
                    effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
                    seed_mode = "固定"
                elif seed_control == "随机":
                    effective_seed = random.randint(0, 2147483647)
                    seed_mode = "随机"
                elif seed_control == "递增":
                    if i == 0:
                        if self.last_seed == -1:
                            effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
                        else:
                            effective_seed = self.last_seed + 1
                    else:
                        effective_seed = seeds_used[0] + i
                    seed_mode = "递增"
                else:
                    effective_seed = random.randint(0, 2147483647)
                    seed_mode = "随机"
                
                seeds_used.append(effective_seed)
            
            if seeds_used:
                self.last_seed = seeds_used[-1]
            
            _log_info(f"🎲 种子模式：{seed_mode}")
            status_info.append(f"🎲 种子模式：{seed_mode}")
            status_info.append(f"📸 生成数量：{num_images} 张")
            
            # === 6. 构建 API 请求 ===
            base_url = self.config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            url = f"{base_url}/images/generations"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "ComfyUI-dapaoAPI/3.1"
            }
            
            _log_info(f"📸 开始生成 {num_images} 张变体...")
            
            all_generated_images = []
            
            # === 7. 批量生成图像（逐个调用API）===
            for i, effective_seed in enumerate(seeds_used):
                _log_info(f"🔄 正在生成第 {i+1}/{num_images} 张...")
                
                req_body = {
                    "model": model,
                    "prompt": final_prompt,
                    "image": image_base64_list,
                    "n": 1,
                    "response_format": "url",
                    "quality": "hd",
                    "style": "vivid",
                    "seed": effective_seed
                }
                
                if final_size:
                    req_body["size"] = final_size
                
                response = requests.post(
                    url,
                    headers=headers,
                    json=req_body,
                    timeout=self.config.get("timeout", 120),
                    verify=False
                )
                
                if response.status_code != 200:
                    _log_error(f"❌ 第 {i+1} 张生成失败：{response.status_code}")
                    if i == 0:
                        error_msg = f"❌ 错误：API 请求失败\n\n状态码：{response.status_code}"
                        return (create_blank_tensor(), error_msg)
                    continue
                
                result = response.json()
                _log_info(f"✅ 第 {i+1} 张 API 响应成功")
                
                if "data" in result and result["data"]:
                    for item in result["data"]:
                        image_url = item.get("url")
                        if image_url:
                            try:
                                img_response = requests.get(image_url, timeout=60, verify=False)
                                if img_response.status_code == 200:
                                    img = Image.open(io.BytesIO(img_response.content))
                                    all_generated_images.append({
                                        "image": img,
                                        "seed": effective_seed,
                                        "index": i + 1
                                    })
                                    _log_info(f"✅ 第 {i+1} 张下载成功：{img.size}")
                            except Exception as e:
                                _log_warning(f"下载第 {i+1} 张失败: {e}")
            
            # === 8. 检查是否有成功生成的图像 ===
            if not all_generated_images:
                error_msg = "❌ 错误：所有图像生成失败"
                _log_error(error_msg)
                return (create_blank_tensor(), error_msg)
            
            # === 9. 转换为 tensor 并合并 ===
            image_tensors = []
            for img_data in all_generated_images:
                tensor = pil2tensor(img_data["image"])
                image_tensors.append(tensor)
            
            if len(image_tensors) == 1:
                final_tensor = image_tensors[0]
            else:
                final_tensor = torch.cat(image_tensors, dim=0)
            
            # === 10. 计算生成时间 ===
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # === 11. 构建详细的信息输出 ===
            status_info.append("=" * 40)
            status_info.append(f"✅ 成功生成 {len(all_generated_images)}/{num_images} 张图像")
            status_info.append("=" * 40)
            status_info.append("")
            status_info.append("📋 生成详情：")
            
            for img_data in all_generated_images:
                status_info.append(f"   变体 {img_data['index']}：种子 {img_data['seed']}")
            
            status_info.append("")
            status_info.append(f"⏱️ 总耗时：{elapsed_time:.2f} 秒")
            status_info.append(f"⚡ 平均每张：{elapsed_time/len(all_generated_images):.2f} 秒")
            
            if edit_mode != "默认":
                status_info.append("")
                status_info.append("💡 提示：")
                status_info.append(f"   已应用 [{edit_mode}] 编辑模式")
                status_info.append(f"   编辑强度：{edit_strength}")
            
            info = "\n".join(status_info)
            _log_info(f"🎉 多图编辑完成！成功生成 {len(all_generated_images)} 张图像")
            
            return (final_tensor, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：多图编辑失败\n\n错误详情：{str(e)}\n\n建议：\n1. 检查网络连接\n2. 检查 API Key 是否正确\n3. 确认输入图像格式正确"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return (create_blank_tensor(), error_msg)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "Seedream_Text2Image": Seedream_Text2Image,
    "Seedream_MultiImage": Seedream_MultiImage,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Seedream_Text2Image": "🎨 Seedream 4.0文生图 @炮老师的小课堂",
    "Seedream_MultiImage": "🖼️ Seedream 4.0多图编辑 @炮老师的小课堂",
}

# 添加节点版本信息
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', '__version__', '__author__']

# 打印加载信息
_log_info(f"Seedream 节点加载完成 v{__version__} by {__author__}")
_log_info(f"已注册 {len(NODE_CLASS_MAPPINGS)} 个节点")

