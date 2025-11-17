"""
大炮 API - Sora2 视频生成节点
提供文生视频和图生视频功能

作者：@炮老师的小课堂
版本：v1.0.0
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
from typing import Optional, Dict, Any, List
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 节点版本和作者信息
__version__ = "1.0.0"
__author__ = "@炮老师的小课堂"

# 统一节点颜色 (橙棕色)
NODE_COLOR = "#773508"  # RGB(119, 53, 8)

# 日志函数
def _log_info(message):
    print(f"[dapaoAPI] 信息：{message}")

def _log_warning(message):
    print(f"[dapaoAPI] 警告：{message}")

def _log_error(message):
    print(f"[dapaoAPI] 错误：{message}")


# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CURRENT_DIR, 'sora2_config.json')


def get_config():
    """获取配置文件"""
    default_config = {
        "api_key": "",
        "base_url": "https://api.example.com",  # 替换为实际的API地址
        "timeout": 300,
        "max_retries": 3
    }
    
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            # 创建默认配置文件
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            _log_info(f"已创建默认配置文件: {CONFIG_FILE}")
            return default_config
    except Exception as e:
        _log_error(f"读取配置文件失败: {e}")
        return default_config


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


def image_to_base64(image_tensor: torch.Tensor, max_size=2048) -> str:
    """
    将图像tensor转换为base64字符串
    
    Args:
        image_tensor: 输入的图像张量
        max_size: 最大尺寸，超过此尺寸会压缩
        
    Returns:
        base64 编码的字符串
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
        
        return image_base64
    except Exception as e:
        _log_error(f"图像转base64失败: {e}")
        return None


class Sora2_VideoGeneration:
    """
    Sora2 视频生成节点（文生视频 + 图生视频）
    
    功能特性：
    - 🎬 文生视频：根据文字描述生成视频
    - 🖼️ 图生视频：基于输入图像生成视频
    - ⚙️ 灵活配置：支持多种分辨率、时长和质量选项
    - 🔄 异步任务：返回任务ID用于后续查询
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # === 基础设置 ===
                "📝 提示词": ("STRING", {
                    "multiline": True, 
                    "default": "一只可爱的小猫在草地上奔跑，阳光明媚，高清画质",
                    "placeholder": "请输入视频描述..."
                }),
                
                # === API 配置 ===
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件中的密钥"
                }),
                
                # === 视频设置 ===
                "📐 宽高比": ([
                    "16:9",   # 横屏
                    "9:16",   # 竖屏
                    "1:1",    # 方形
                    "21:9",   # 超宽屏
                    "4:3",    # 传统
                ], {
                    "default": "16:9"
                }),
                
                "⏱️ 时长(秒)": ([
                    "5",
                    "10",
                    "15",
                    "20",
                ], {
                    "default": "10"
                }),
                
                "🎨 高清模式": ("BOOLEAN", {
                    "default": True,
                    "label_on": "开启",
                    "label_off": "关闭"
                }),
                
                "💧 水印": ("BOOLEAN", {
                    "default": True,
                    "label_on": "显示",
                    "label_off": "隐藏"
                }),
                
                "🔒 私密模式": ("BOOLEAN", {
                    "default": True,
                    "label_on": "开启",
                    "label_off": "关闭"
                }),
            },
            "optional": {
                # === 图生视频选项（最多4张图片）===
                "🖼️ 输入图像1": ("IMAGE",),
                "🖼️ 输入图像2": ("IMAGE",),
                "🖼️ 输入图像3": ("IMAGE",),
                "🖼️ 输入图像4": ("IMAGE",),
                
                "🔔 回调地址": ("STRING", {
                    "default": "",
                    "placeholder": "可选：任务完成后的回调URL"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("任务ID", "视频URL", "详细信息")
    FUNCTION = "generate_video"
    CATEGORY = "dapaoAPI/Sora2"
    
    def __init__(self):
        self.config = get_config()
    
    def generate_video(
        self, 
        **kwargs
    ):
        """生成视频（文生视频或图生视频）"""
        try:
            # === 1. 提取参数 ===
            prompt = kwargs.get("📝 提示词", "")
            api_key = kwargs.get("🔑 API密钥", "").strip()
            aspect_ratio = kwargs.get("📐 宽高比", "16:9")
            duration = kwargs.get("⏱️ 时长(秒)", "10")
            hd_mode = kwargs.get("🎨 高清模式", True)
            watermark = kwargs.get("💧 水印", True)
            private_mode = kwargs.get("🔒 私密模式", True)
            
            # 收集所有输入的图像（最多4张）
            input_images = []
            for i in range(1, 5):
                img = kwargs.get(f"🖼️ 输入图像{i}", None)
                if img is not None:
                    input_images.append(img)
            
            notify_hook = kwargs.get("🔔 回调地址", "").strip()
            
            # === 2. 验证必填参数 ===
            if not prompt:
                error_msg = "❌ 错误：提示词不能为空"
                _log_error(error_msg)
                return ("", "", error_msg)
            
            # 使用配置文件中的 API Key（如果未提供）
            if not api_key:
                api_key = self.config.get("api_key", "")
            
            if not api_key:
                error_msg = "❌ 错误：API密钥未配置\n\n请在节点参数或配置文件中设置 API Key"
                _log_error(error_msg)
                return ("", "", error_msg)
            
            # === 3. 构建请求 ===
            start_time = time.time()
            status_info = []
            
            # 判断是文生视频还是图生视频
            is_image_to_video = len(input_images) > 0
            mode_name = "图生视频" if is_image_to_video else "文生视频"
            
            status_info.append("=" * 50)
            status_info.append(f"🎬 Sora2 {mode_name}")
            status_info.append("=" * 50)
            status_info.append("")
            status_info.append(f"📝 提示词：{prompt[:100]}{'...' if len(prompt) > 100 else ''}")
            status_info.append(f"📐 宽高比：{aspect_ratio}")
            status_info.append(f"⏱️ 时长：{duration}秒")
            status_info.append(f"🎨 高清模式：{'开启' if hd_mode else '关闭'}")
            status_info.append(f"💧 水印：{'显示' if watermark else '隐藏'}")
            status_info.append(f"🔒 私密模式：{'开启' if private_mode else '关闭'}")
            
            if is_image_to_video:
                status_info.append(f"🖼️ 输入图像：{len(input_images)} 张")
            
            status_info.append("")
            status_info.append("⏳ 正在提交任务...")
            
            _log_info(f"开始 Sora2 {mode_name}")
            _log_info(f"提示词: {prompt[:100]}...")
            
            # === 4. 准备 API 请求 ===
            base_url = self.config.get("base_url", "https://api.example.com")
            url = f"{base_url}/v2/videos/generations"
            timeout = self.config.get("timeout", 300)
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "ComfyUI-dapaoAPI/1.0"
            }
            
            # 构建请求体
            req_body = {
                "prompt": prompt,
                "model": "sora-2",
                "aspect_ratio": aspect_ratio,
                "hd": hd_mode,
                "duration": duration,
                "watermark": watermark,
                "private": private_mode
            }
            
            # 如果是图生视频，添加图像数据
            if is_image_to_video:
                _log_info(f"正在处理 {len(input_images)} 张输入图像...")
                images_base64 = []
                for idx, img in enumerate(input_images, 1):
                    image_base64 = image_to_base64(img)
                    if not image_base64:
                        error_msg = f"❌ 错误：第 {idx} 张图像处理失败"
                        _log_error(error_msg)
                        return ("", "", error_msg)
                    images_base64.append(image_base64)
                    _log_info(f"第 {idx} 张图像处理完成")
                
                req_body["images"] = images_base64
                _log_info(f"所有图像处理完成，共 {len(images_base64)} 张")
            
            # 添加回调地址（如果提供）
            if notify_hook:
                req_body["notify_hook"] = notify_hook
                status_info.append(f"🔔 回调地址：{notify_hook}")
            
            # === 5. 发送请求 ===
            _log_info(f"发送请求到: {url}")
            
            try:
                response = requests.post(
                    url,
                    headers=headers,
                    json=req_body,
                    timeout=timeout,
                    verify=False
                )
                
                _log_info(f"响应状态码: {response.status_code}")
                
                if response.status_code != 200:
                    error_msg = f"❌ API 请求失败\n\n状态码：{response.status_code}\n响应：{response.text}"
                    _log_error(error_msg)
                    return ("", "", error_msg)
                
                # 解析响应
                result = response.json()
                task_id = result.get("task_id", "")
                video_url = result.get("video_url", "")  # 获取视频URL（如果API直接返回）
                
                if not task_id:
                    error_msg = f"❌ 错误：未返回任务ID\n\n响应：{json.dumps(result, ensure_ascii=False, indent=2)}"
                    _log_error(error_msg)
                    return ("", "", error_msg)
                
                # === 6. 计算耗时 ===
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                # === 7. 构建成功信息 ===
                status_info.append("")
                status_info.append("=" * 50)
                status_info.append("✅ 任务提交成功！")
                status_info.append("=" * 50)
                status_info.append("")
                status_info.append(f"🆔 任务ID：{task_id}")
                if video_url:
                    status_info.append(f"🎬 视频URL：{video_url}")
                status_info.append(f"⏱️ 提交耗时：{elapsed_time:.2f} 秒")
                status_info.append("")
                status_info.append("💡 提示：")
                if video_url:
                    status_info.append("   1. 视频已生成，可直接使用视频URL")
                    status_info.append("   2. 视频URL输出端口可连接保存节点")
                else:
                    status_info.append("   1. 请使用任务ID查询视频生成状态")
                    status_info.append("   2. 视频生成通常需要几分钟时间")
                    status_info.append("   3. 可以使用查询节点获取视频下载链接")
                
                if notify_hook:
                    status_info.append("   4. 任务完成后会自动回调指定地址")
                
                info = "\n".join(status_info)
                _log_info(f"🎉 {mode_name}任务提交成功！任务ID: {task_id}")
                if video_url:
                    _log_info(f"视频URL: {video_url}")
                
                return (task_id, video_url, info)
                
            except requests.exceptions.Timeout:
                error_msg = f"❌ 错误：请求超时（{timeout}秒）\n\n建议：\n1. 检查网络连接\n2. 增加超时时间\n3. 稍后重试"
                _log_error(error_msg)
                return ("", "", error_msg)
            
            except requests.exceptions.RequestException as e:
                error_msg = f"❌ 错误：网络请求失败\n\n错误详情：{str(e)}\n\n建议：\n1. 检查网络连接\n2. 检查 API 地址是否正确\n3. 检查防火墙设置"
                _log_error(error_msg)
                return ("", "", error_msg)
            
        except Exception as e:
            error_msg = f"❌ 错误：视频生成失败\n\n错误详情：{str(e)}\n\n建议：\n1. 检查所有参数是否正确\n2. 查看控制台日志获取详细信息\n3. 联系技术支持"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return ("", "", error_msg)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "Sora2_VideoGeneration": Sora2_VideoGeneration,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Sora2_VideoGeneration": "🎬 Sora2 视频生成 @炮老师的小课堂",
}

# 添加节点版本信息
__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', '__version__', '__author__']

# 打印加载信息
_log_info(f"Sora2 节点加载完成 v{__version__} by {__author__}")
_log_info(f"已注册 {len(NODE_CLASS_MAPPINGS)} 个节点")
