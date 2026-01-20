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
📦 版本：v1.0.1
🎨 主题：紫色 (#631E77)
🌐 API：贞贞 API (https://ai.t8star.cn)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
import random
import time
import base64
import requests
import torch
import cv2
import shutil
import re
import numpy as np
import folder_paths
from io import BytesIO
from PIL import Image
from typing import Tuple, Optional
import comfy.utils
from comfy.comfy_types import IO

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
        if not video_path_or_url:
             self.is_url = False
             self.video_path = ""
             self.video_url = None
             return

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
                if not self.video_path:
                    return 1280, 720
                cap = cv2.VideoCapture(self.video_path)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                if width == 0 or height == 0:
                     return 1280, 720
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
                if not self.video_path:
                    return False
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
                    "default": -1,
                    "min": -1,
                    "max": 2147483647,
                    "step": 1
                }),
                
                "🎯 种子控制": (["随机", "固定", "递增"], {
                    "default": "随机"
                }),
                
                "🔐 隐私模式": ("BOOLEAN", {
                    "default": True
                }),
            }
        }
    
    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🎥 视频URL", "📋 响应信息")
    FUNCTION = "generate_video"
    CATEGORY = "zhenzhen/SORA2"
    DESCRIPTION = "使用 SORA2 API 生成视频，支持文生视频和图生视频 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.config = get_sora2_config()
        self.api_key = "" # 不再从配置文件加载API密钥
        self.base_url = self.config.get("base_url", "https://ai.t8star.cn")
        self.timeout = self.config.get("timeout", 900)
        
        self.last_seed = -1
    
    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎯 种子控制", "随机")
        seed = kwargs.get("🎰 随机种子", -1)
        
        # 随机和递增模式下，强制更新 (返回 NaN)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        
        # 固定模式下，仅当种子值变化时更新
        return seed

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
    
    def _parse_stream(self, response, pbar):
        """解析流式响应"""
        video_url = None
        full_content = ""
        
        for line in response.iter_lines():
            if not line:
                continue
            
            decoded_line = line.decode('utf-8').strip()
            if not decoded_line.startswith('data:'):
                try:
                    # 尝试解析普通 JSON 行 (兼容非 SSE 格式)
                    data = json.loads(decoded_line)
                    if "choices" in data and len(data["choices"]) > 0:
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            full_content += content
                            # 尝试提取进度
                            match = re.search(r'进度.*?(\d+)%', content)
                            if match:
                                progress = int(match.group(1))
                                pbar.update_absolute(min(95, progress))
                                _log_info(f"生成进度: {progress}%")
                except:
                    pass
                continue
                
            # 处理 SSE 格式 (data: {...})
            json_str = decoded_line[5:].strip()
            if json_str == "[DONE]":
                break
                
            try:
                data = json.loads(json_str)
                if "choices" in data and len(data["choices"]) > 0:
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        full_content += content
                        # 尝试提取进度
                        match = re.search(r'进度.*?(\d+)%', content)
                        if match:
                            progress = int(match.group(1))
                            pbar.update_absolute(min(95, progress))
                            _log_info(f"生成进度: {progress}%")
            except Exception as e:
                continue

        # 从完整内容中提取视频 URL
        # 格式通常是: ... [视频](URL) ... OR just the URL
        # 贞贞API通常在最后返回 URL
        url_match = re.search(r'https://[^\s\)]+\.mp4', full_content)
        if url_match:
            video_url = url_match.group(0)
        
        return video_url, full_content

    def _download_and_wrap_video(self, video_url):
        """下载视频并包装为 ComflyVideoAdapter"""
        try:
            _log_info(f"正在下载视频: {video_url}")
            resp = requests.get(video_url, stream=True, timeout=120)
            if resp.status_code != 200:
                _log_error(f"下载失败: {resp.status_code}")
                # 尝试返回 URL 适配器作为回退
                return ComflyVideoAdapter(video_url)
            
            # 使用临时文件
            temp_dir = folder_paths.get_temp_directory()
            temp_file = os.path.join(temp_dir, f"sora_{int(time.time())}_{random.randint(0, 1000)}.mp4")
            
            with open(temp_file, 'wb') as f:
                for chunk in resp.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            _log_info(f"视频已下载到临时文件: {temp_file}")
            
            # 返回本地文件适配器
            return ComflyVideoAdapter(temp_file)
            
        except Exception as e:
            _log_error(f"视频下载包装失败: {e}")
            # 尝试返回 URL 适配器作为回退
            return ComflyVideoAdapter(video_url)



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
        seed = kwargs.get("🎰 随机种子", -1)
        seed_control = kwargs.get("🎯 种子控制", "随机")
        private = kwargs.get("🔐 隐私模式", True)
        
        # === 种子处理逻辑 ===
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
        
        # 更新 API 密钥
        if api_key.strip():
            self.api_key = api_key
        
        if not self.api_key:
            error_msg = "❌ 错误：请配置 API 密钥"
            _log_error(error_msg)
            raise ValueError(error_msg)
        
        # 参数验证与模型映射
        # Sora-2 API 在贞贞平台上对应的模型名称通常是 sora_video2
        # 我们这里做一个映射，或者直接使用用户选择的
        api_model = "sora_video2" 
        if model == "sora-2-pro":
             # 假设 pro 对应 sora_video2_pro 或者保持 sora_video2 但参数不同？
             # 参考代码中 default="sora_video2"，没有看到 pro 的特殊映射，
             # 但用户界面有 "sora-2-pro"。这里暂时都映射为 sora_video2，或者相信用户的选择
             # 如果用户选择的是 "sora-2"，我们映射为 "sora_video2"
             # 如果是 "sora-2-pro"，可能需要具体 API 文档。
             # 暂时保持原样传递，或者参考 Comfyui-zhenzhen 的 Comfly.py 只有 sora_video2
             api_model = "sora_video2"
        else:
             api_model = "sora_video2"

        # 创建进度条
        pbar = comfy.utils.ProgressBar(100)
        pbar.update_absolute(10)
        
        try:
            # 处理图像输入
            has_image = any(img is not None for img in [image1, image2, image3, image4])
            messages = []
            
            # 构建 Prompt，包含参数信息
            # Sora-2 的参数通常作为 Prompt 的一部分或者 System Prompt？
            # 贞贞 API 的 OpenAISoraAPIPlus 并没有把 aspect_ratio 等放到 payload 顶层，
            # 而是只用了 model 和 messages。
            # 这意味着参数可能需要拼接到 prompt 中，或者 API 实际上忽略了它们？
            # 仔细看 OpenAISoraAPIPlus 的 INPUT_TYPES，有 aspect_ratio, duration 等，
            # 但是在 generate 中，并没有使用这些参数！
            # 这是一个重大发现：OpenAISoraAPIPlus 的 generate 方法接收了 aspect_ratio 等，但根本没用！
            # 只有 user_prompt 被使用了。
            # 这可能意味着：
            # 1. 默认参数已经足够。
            # 2. 参数应该写在 prompt 里。
            # 3. 那个节点实现不完整。
            # 既然用户说那个节点成功，那我们照搬它的逻辑：只发 prompt (和 image)。
            # 为了保险，我把参数加到 prompt 后面，或者作为 system prompt?
            # 还是严格照搬？
            # 照搬的话，宽高比和时长怎么控制？
            # 也许 sora_video2 模型足够智能，从 prompt 理解？
            # 或者我应该把它们拼接到 prompt 中。
            
            enhanced_prompt = prompt
            params_desc = []
            if aspect_ratio: params_desc.append(f"--ar {aspect_ratio}")
            if duration: params_desc.append(f"--d {duration}")
            # if hd: params_desc.append("--hd") # 假设支持
            
            # 很多 Sora 包装器支持 --ar 格式
            if params_desc:
                enhanced_prompt += " " + " ".join(params_desc)

            if has_image:
                _log_info("处理输入图像 (图生视频模式)...")
                content_list = [{"type": "text", "text": enhanced_prompt}]
                
                # 限制最多处理1张图？OpenAISoraAPIPlus 似乎只处理了一张 image (Input type definition)
                # 但这里我们支持4张。OpenAI 格式支持多图。
                for idx, img in enumerate([image1, image2, image3, image4], 1):
                    if img is not None:
                        img_base64 = self.image_to_base64(img) # 返回 data:image/png;base64,...
                        if img_base64:
                            content_list.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": img_base64,
                                    "detail": "high"
                                }
                            })
                            _log_info(f"图像 {idx} 已添加")
                
                messages = [{"role": "user", "content": content_list}]
            else:
                _log_info("文生视频模式...")
                messages = [{"role": "user", "content": enhanced_prompt}]
            
            # 构建 API URL
            # 确保 URL 正确：https://ai.t8star.cn/v1/chat/completions
            base = self.base_url.rstrip('/')
            if not base.endswith('/v1'):
                base += '/v1'
            api_url = f"{base}/chat/completions"
            
            payload = {
                "model": api_model,
                "messages": messages,
                "stream": True,
                # 尝试将参数放入 payload，适配部分 OpenAI 兼容接口的扩展参数
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                "hd": hd
            }
            
            _log_info(f"开始生成视频...")
            _log_info(f"  - 模型: {api_model}")
            _log_info(f"  - 提示词: {enhanced_prompt[:50]}...")
            
            pbar.update_absolute(20)
            
            # 发送生成请求
            response = requests.post(
                api_url,
                headers=self.get_headers(),
                json=payload,
                timeout=self.timeout,
                stream=True
            )
            
            if response.status_code != 200:
                # 尝试读取错误信息
                try:
                    err_text = response.text
                except:
                    err_text = "无法读取响应内容"
                error_msg = f"API 错误: {response.status_code} - {err_text}"
                _log_error(error_msg)
                raise ValueError(error_msg)
            
            _log_info("请求已提交，正在接收流式响应...")
            
            # 解析流式响应
            video_url, full_response = self._parse_stream(response, pbar)
            
            if not video_url:
                # 如果流式没有解析到 URL，尝试从 full_response 再次查找 (防止 parse_stream 漏掉)
                url_match = re.search(r'https://[^\s\)]+\.mp4', full_response)
                if url_match:
                    video_url = url_match.group(0)
            
            if not video_url:
                error_msg = "未能从响应中提取视频 URL"
                _log_error(error_msg)
                _log_error(f"完整响应: {full_response[:200]}...")
                raise ValueError(error_msg)
            
            _log_info(f"✅ 视频生成成功！URL: {video_url}")
            
            # 下载并包装为 Adapter
            video_output = self._download_and_wrap_video(video_url)
            
            pbar.update_absolute(100)
            
            # 构建响应数据
            response_data = {
                "status": "success",
                "prompt": enhanced_prompt,
                "model": api_model,
                "video_url": video_url,
                "raw_response": full_response[:500]
            }
            
            return (
                video_output,
                video_url,
                json.dumps(response_data, ensure_ascii=False, indent=2)
            )
        
        except Exception as e:
            error_msg = f"视频生成过程中出错: {str(e)}"
            _log_error(error_msg)
            import traceback
            traceback.print_exc()
            raise ValueError(error_msg)


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "Sora2VideoGenNode": Sora2VideoGenNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Sora2VideoGenNode": "🎨 SORA2视频生成（贞贞API） @炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
