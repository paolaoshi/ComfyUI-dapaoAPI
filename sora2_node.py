"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 SORA2 视频生成节点（贞贞API）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 基于 OpenAI SORA2 的视频生成
   - 支持文生视频和图生视频
   - 支持多图输入（最多4张）
   - 支持种子控制和隐私设置

🔧 技术特性：
   - 异步任务轮询
   - 进度条显示
   - 完整的错误处理
   - 视频 URL 输出

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v1.0.0
🎨 主题：紫色 (#631E77)
🌐 API：贞贞 API (https://ai.t8star.cn)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import time
import base64
import requests
import torch
import cv2
import shutil
from io import BytesIO
from PIL import Image
from typing import Tuple, Optional
import comfy.utils
from comfy.comfy_types import IO

# 节点颜色（紫色主题）
NODE_COLOR = "#631E77"

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "sora2_config.json")


def _log_info(message):
    """统一的信息输出函数"""
    print(f"[dapaoAPI-SORA2] {message}")


def _log_error(message):
    """统一的错误输出函数"""
    print(f"[dapaoAPI-SORA2] ❌ 错误：{message}")


def get_sora2_config():
    """读取配置文件"""
    default_config = {
        "api_key": "",
        "base_url": "https://ai.t8star.cn",
        "timeout": 900
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


def save_sora2_config(config):
    """保存配置文件 - 已禁用"""
    # try:
    #     with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
    #         json.dump(config, f, indent=4, ensure_ascii=False)
    #     _log_info("配置已保存")
    # except Exception as e:
    #     _log_error(f"保存配置失败: {e}")
    pass


def tensor2pil(image_tensor):
    """将 Tensor 转换为 PIL Image"""
    # image_tensor shape: [B, H, W, C]
    if image_tensor.dim() == 4:
        image_tensor = image_tensor[0]  # 取第一张
    
    # 转换为 numpy
    image_np = (image_tensor.cpu().numpy() * 255).astype('uint8')
    
    # 转换为 PIL
    pil_image = Image.fromarray(image_np)
    return pil_image


class ComflyVideoAdapter:
    """视频适配器，兼容 ComfyUI 的 VIDEO 类型"""
    def __init__(self, video_path_or_url):
        if video_path_or_url.startswith('http'):
            self.is_url = True
            self.video_url = video_path_or_url
            self.video_path = None
        else:
            self.is_url = False
            self.video_path = video_path_or_url
            self.video_url = None
        
    def get_dimensions(self):
        """获取视频尺寸"""
        if self.is_url:
            return 1280, 720
        else:
            try: 
                cap = cv2.VideoCapture(self.video_path)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                return width, height
            except Exception as e:
                _log_error(f"获取视频尺寸失败: {e}")
                return 1280, 720
            
    def save_to(self, output_path, format="auto", codec="auto", metadata=None):
        """保存视频到指定路径"""
        if self.is_url:
            try:
                response = requests.get(self.video_url, stream=True)
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            except Exception as e:
                _log_error(f"从 URL 下载视频失败: {e}")
                return False
        else:
            try:
                shutil.copyfile(self.video_path, output_path)
                return True
            except Exception as e:
                _log_error(f"保存视频失败: {e}")
                return False


class Sora2VideoGenNode:
    """
    SORA2 视频生成节点
    
    支持文生视频和图生视频，可配置多种参数
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎨 提示词": ("STRING", {
                    "multiline": True,
                    "default": "女人在天上飞",
                    "placeholder": "描述你想要生成的视频内容..."
                }),
                
                "🤖 模型选择": (["sora-2", "sora-2-pro"], {
                    "default": "sora-2"
                }),
                
                "📐 宽高比": (["16:9", "9:16"], {
                    "default": "16:9"
                }),
                
                "⏱️ 视频时长": (["10", "15", "25"], {
                    "default": "15"
                }),
                
                "🎬 高清模式": ("BOOLEAN", {
                    "default": False
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件中的密钥"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                
                "🎰 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647,
                    "step": 1
                }),
                
                "🔒 生成后控制": (["randomize", "fixed"], {
                    "default": "randomize"
                }),
                
                "🔐 隐私模式": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🎥 视频URL", "📋 响应信息")
    FUNCTION = "generate_video"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "使用 SORA2 API 生成视频，支持文生视频和图生视频 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_sora2_config()
        self.api_key = "" # 不再从配置文件加载API密钥
        self.base_url = self.config.get("base_url", "https://ai.t8star.cn")
        self.timeout = self.config.get("timeout", 900)
        
        # 设置节点颜色
        self.color = NODE_COLOR
        self.bgcolor = NODE_COLOR
    
    def get_headers(self):
        """获取请求头"""
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def image_to_base64(self, image_tensor):
        """将图像 Tensor 转换为 Base64 字符串"""
        if image_tensor is None:
            return None
        
        try:
            pil_image = tensor2pil(image_tensor)
            buffered = BytesIO()
            pil_image.save(buffered, format="PNG")
            base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{base64_str}"
        except Exception as e:
            _log_error(f"图像转换失败: {e}")
            return None
    
    def generate_video(
        self,
        **kwargs
    ):
        """生成视频"""
        # 提取参数
        prompt = kwargs.get("🎨 提示词", "")
        model = kwargs.get("🤖 模型选择", "sora-2")
        aspect_ratio = kwargs.get("📐 宽高比", "16:9")
        duration = kwargs.get("⏱️ 视频时长", "15")
        hd = kwargs.get("🎬 高清模式", False)
        api_key = kwargs.get("🔑 API密钥", "")
        
        # 可选参数
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        seed = kwargs.get("🎰 随机种子", 0)
        seed_control = kwargs.get("🔒 生成后控制", "randomize")
        private = kwargs.get("🔐 隐私模式", True)
        
        # 更新 API 密钥
        if api_key.strip():
            self.api_key = api_key
            # config = get_sora2_config()
            # config['api_key'] = api_key
            # save_sora2_config(config)
        
        if not self.api_key:
            error_msg = "❌ 错误：请配置 API 密钥"
            _log_error(error_msg)
            return ("", "", json.dumps({"status": "error", "message": error_msg}))
        
        # 参数验证
        if duration == "25" and hd:
            error_msg = "25秒视频和高清模式不能同时使用，请只选择其中一个"
            _log_error(error_msg)
            return ("", "", json.dumps({"status": "error", "message": error_msg}))
        
        if model == "sora-2":
            if duration == "25":
                error_msg = "sora-2 模型不支持 25 秒视频，请使用 sora-2-pro"
                _log_error(error_msg)
                return ("", "", json.dumps({"status": "error", "message": error_msg}))
            if hd:
                error_msg = "sora-2 模型不支持高清模式，请使用 sora-2-pro 或关闭高清"
                _log_error(error_msg)
                return ("", "", json.dumps({"status": "error", "message": error_msg}))
        
        # 创建进度条
        pbar = comfy.utils.ProgressBar(100)
        pbar.update_absolute(10)
        
        try:
            # 处理图像输入
            has_image = any(img is not None for img in [image1, image2, image3, image4])
            
            if has_image:
                _log_info("处理输入图像...")
                images = []
                for idx, img in enumerate([image1, image2, image3, image4], 1):
                    if img is not None:
                        img_base64 = self.image_to_base64(img)
                        if img_base64:
                            images.append(img_base64)
                            _log_info(f"图像 {idx} 处理成功")
                
                if not images:
                    error_msg = "所有输入图像处理失败"
                    _log_error(error_msg)
                    return ("", "", json.dumps({"status": "error", "message": error_msg}))
                
                _log_info(f"共处理 {len(images)} 张图像")
            
            # 构建请求体
            payload = {
                "prompt": prompt,
                "model": model,
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                "hd": hd,
                "private": private
            }
            
            if has_image:
                payload["images"] = images
            
            if seed > 0:
                payload["seed"] = seed
            
            _log_info(f"开始生成视频...")
            _log_info(f"  - 模型: {model}")
            _log_info(f"  - 宽高比: {aspect_ratio}")
            _log_info(f"  - 时长: {duration}秒")
            _log_info(f"  - 高清: {'是' if hd else '否'}")
            _log_info(f"  - 图像输入: {'是' if has_image else '否'}")
            
            pbar.update_absolute(20)
            
            # 发送生成请求
            endpoint = f"{self.base_url}/v2/videos/generations"
            response = requests.post(
                endpoint,
                headers=self.get_headers(),
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_msg = f"API 错误: {response.status_code} - {response.text}"
                _log_error(error_msg)
                return ("", "", json.dumps({"status": "error", "message": error_msg}))
            
            result = response.json()
            
            if "task_id" not in result:
                error_msg = "API 响应中没有任务 ID"
                _log_error(error_msg)
                return ("", "", json.dumps({"status": "error", "message": error_msg}))
            
            task_id = result["task_id"]
            _log_info(f"✅ 任务创建成功，任务 ID: {task_id}")
            
            pbar.update_absolute(30)
            
            # 轮询任务状态
            max_attempts = 300  # 最多等待 50 分钟
            attempts = 0
            video_url = None
            
            _log_info("等待视频生成...")
            
            while attempts < max_attempts:
                time.sleep(10)  # 每 10 秒检查一次
                attempts += 1
                
                try:
                    status_response = requests.get(
                        f"{self.base_url}/v2/videos/generations/{task_id}",
                        headers=self.get_headers(),
                        timeout=self.timeout
                    )
                    
                    if status_response.status_code != 200:
                        continue
                    
                    status_data = status_response.json()
                    
                    # 更新进度条
                    progress_text = status_data.get("progress", "0%")
                    try:
                        if progress_text.endswith('%'):
                            progress_value = int(progress_text[:-1])
                            pbar_value = min(90, 30 + int(progress_value * 0.6))
                            pbar.update_absolute(pbar_value)
                            _log_info(f"生成进度: {progress_text}")
                    except (ValueError, AttributeError):
                        progress_value = min(80, 30 + (attempts * 50 // max_attempts))
                        pbar.update_absolute(progress_value)
                    
                    status = status_data.get("status", "")
                    
                    if status == "SUCCESS":
                        if "data" in status_data and "output" in status_data["data"]:
                            video_url = status_data["data"]["output"]
                            _log_info(f"✅ 视频生成成功！")
                            break
                    
                    elif status == "FAILURE":
                        fail_reason = status_data.get("fail_reason", "未知错误")
                        error_msg = f"视频生成失败: {fail_reason}"
                        _log_error(error_msg)
                        return ("", "", json.dumps({
                            "status": "error",
                            "message": error_msg,
                            "task_id": task_id
                        }))
                
                except Exception as e:
                    _log_error(f"检查任务状态时出错: {str(e)}")
            
            if not video_url:
                error_msg = f"等待超时：在 {max_attempts} 次尝试后仍未获取到视频 URL"
                _log_error(error_msg)
                return ("", "", json.dumps({
                    "status": "error",
                    "message": error_msg,
                    "task_id": task_id
                }))
            
            # 创建视频适配器
            video_adapter = ComflyVideoAdapter(video_url)
            
            pbar.update_absolute(100)
            
            # 构建响应数据
            response_data = {
                "status": "success",
                "task_id": task_id,
                "prompt": prompt,
                "model": model,
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                "hd": hd,
                "private": private,
                "video_url": video_url,
                "has_images": has_image
            }
            
            _log_info(f"✅ 视频生成完成")
            _log_info(f"视频 URL: {video_url}")
            
            return (
                video_adapter,
                video_url,
                json.dumps(response_data, ensure_ascii=False, indent=2)
            )
        
        except Exception as e:
            error_msg = f"视频生成过程中出错: {str(e)}"
            _log_error(error_msg)
            import traceback
            traceback.print_exc()
            return ("", "", json.dumps({"status": "error", "message": error_msg}))


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "Sora2VideoGenNode": Sora2VideoGenNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Sora2VideoGenNode": "🎨 SORA2视频生成（贞贞API） @炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
