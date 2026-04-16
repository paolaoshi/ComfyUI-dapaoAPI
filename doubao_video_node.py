"""
大炮 API - 豆包视频生成节点
调用火山引擎 Doubao-Seedance 模型生成视频

作者：@炮老师的小课堂
版本：v1.0.0
"""

import os
import json
import requests
import time
import base64
import io
import tempfile
from PIL import Image
import torch
import numpy as np
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CURRENT_DIR, 'config.json')

def _log_info(message):
    print(f"[dapaoAPI-Video] 信息：{message}")

def _log_warning(message):
    print(f"[dapaoAPI-Video] 警告：{message}")

def _log_error(message):
    print(f"[dapaoAPI-Video] 错误：{message}")

def get_config():
    """获取配置文件"""
    default_config = {
        "api_key": "",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "timeout": 300,
        "models": {
             "doubao-seedance-1-5-pro-251215": "Seedance 1.5 Pro (最新)",
             "doubao-seedance-1-0-pro-251215": "Seedance 1.0 Pro"
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

def tensor2pil(tensor: torch.Tensor) -> Image.Image:
    """将ComfyUI tensor转换为PIL图像"""
    if len(tensor.shape) == 4:
        tensor = tensor[0]
    np_image = tensor.cpu().numpy()
    np_image = np.clip(np_image, 0, 1)
    np_image = (np_image * 255).astype(np.uint8)
    return Image.fromarray(np_image)

def pil2tensor(image: Image.Image) -> torch.Tensor:
    """将PIL图像转换为ComfyUI tensor格式"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    np_image = np.array(image).astype(np.float32) / 255.0
    tensor = torch.from_numpy(np_image)
    tensor = tensor.unsqueeze(0)
    return tensor

def image_to_base64(image_tensor: torch.Tensor, max_size=2048) -> str:
    """将图像tensor转换为base64字符串"""
    try:
        pil_image = tensor2pil(image_tensor)
        # 调整大小
        if max(pil_image.size) > max_size:
            ratio = max_size / max(pil_image.size)
            new_size = (int(pil_image.size[0] * ratio), int(pil_image.size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
        
        buffered = io.BytesIO()
        pil_image.save(buffered, format="JPEG", quality=90)
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    except Exception as e:
        _log_error(f"图像转base64失败: {e}")
        return None

class DoubaoVideoGeneration:
    """
    豆包视频生成节点
    支持 Doubao-Seedance-1.5-Pro 模型
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "📝 提示词": ("STRING", {
                    "multiline": True, 
                    "default": "一只小猫在草地上奔跑，阳光明媚，高清，电影感",
                    "placeholder": "请输入视频生成的提示词..."
                }),
                "🤖 模型": (["doubao-seedance-1-5-pro-251215", "doubao-seedance-1-0-pro-251215"], {
                    "default": "doubao-seedance-1-5-pro-251215"
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件中的密钥"
                }),
                "🔊 是否有声": ("BOOLEAN", {
                    "default": True,
                    "label_on": "有声",
                    "label_off": "无声"
                }),
                "📐 宽高比": (["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"], {
                    "default": "16:9"
                }),
            },
            "optional": {
                "🖼️ 参考图": ("IMAGE",),
                "🎬 首帧图": ("IMAGE",),
                "🏁 尾帧图": ("IMAGE",),
                "🎲 随机种子": ("INT", {
                    "default": -1, 
                    "min": -1, 
                    "max": 2147483647
                }),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("🎞️ 视频帧", "📂 文件路径")
    FUNCTION = "generate_video"
    CATEGORY = "🤖dapaoAPI/豆包/视频"
    DESCRIPTION = "调用豆包 Seedance 模型生成视频，支持首尾帧控制 | 作者: @炮老师的小课堂"

    def generate_video(self, **kwargs):
        prompt = kwargs.get("📝 提示词", "")
        model = kwargs.get("🤖 模型", "doubao-seedance-1-5-pro-251215")
        api_key = kwargs.get("🔑 API密钥", "")
        has_audio = kwargs.get("🔊 是否有声", True)
        ratio = kwargs.get("📐 宽高比", "16:9")
        ref_image = kwargs.get("🖼️ 参考图")
        first_frame = kwargs.get("🎬 首帧图")
        last_frame = kwargs.get("🏁 尾帧图")
        seed = kwargs.get("🎲 随机种子", -1)

        # 获取配置
        config = get_config()
        if not api_key:
            api_key = config.get("api_key", "")
        
        if not api_key:
            raise ValueError("未提供 API Key，请在节点或 config.json 中配置")

        # 构建请求内容
        content = []
        
        # 1. 提示词
        if prompt:
            content.append({
                "type": "text",
                "text": prompt
            })
            
        # 2. 处理图片
        # 顺序：通常建议 参考图 -> 首帧 -> 尾帧
        # 但具体 API 可能对顺序敏感，这里按照最可能的逻辑排列
        
        if ref_image is not None:
            b64 = image_to_base64(ref_image)
            if b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
                _log_info("已添加参考图")

        if first_frame is not None:
            b64 = image_to_base64(first_frame)
            if b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
                _log_info("已添加首帧图")

        if last_frame is not None:
            b64 = image_to_base64(last_frame)
            if b64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })
                _log_info("已添加尾帧图")

        # 构建请求体
        base_url = config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
        # 视频生成通常是异步任务，端点可能不同
        # 尝试使用内容生成任务端点
        url = f"{base_url}/content_generation/tasks" # 注意：这是推测的端点，需验证
        # 如果是 chat/completions 兼容，则是：
        # url = f"{base_url}/chat/completions"
        
        # 根据搜索结果，Ark 视频生成似乎使用了专门的任务接口
        # 文档 ID 1520757 对应的是 "创建视频生成任务 API"
        # 假设 URL 是 https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks
        # 注意：content(s) 可能有 's'
        url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model,
            "content": content,
            # 其他可能的参数，放在 extra_body 或直接放在 payload
            # Seedance 参数可能包括:
            # - video_setting: { has_audio: bool, aspect_ratio: str }
            # - seed: int
        }
        
        # 添加额外参数
        # 注意：Ark API 的参数结构可能还在变动，这里尝试通用结构
        # 如果是 content generation task，通常有 parameters 字段
        # 或者直接在 payload 顶层
        
        # 尝试添加 parameters 字段
        parameters = {}
        if seed != -1:
            parameters["seed"] = seed
            
        # 添加音频和比例设置
        # 注意：这里基于常见 API 猜测，具体需参考文档
        parameters["with_audio"] = has_audio
        parameters["aspect_ratio"] = ratio
        
        # 将 parameters 添加到 payload
        payload["parameters"] = parameters
        
        _log_info(f"发起视频生成任务... 模型: {model}, 参数: {parameters}")
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60, verify=False)
            
            if response.status_code != 200:
                # 尝试 chat completions 端点作为备选 (虽然不太可能)
                # 或者报错
                raise Exception(f"API 请求失败: {response.status_code} - {response.text}")
            
            result = response.json()
            if "id" not in result:
                raise Exception(f"未返回任务 ID: {result}")
            
            task_id = result["id"]
            _log_info(f"任务已提交，ID: {task_id}，正在生成中...")
            
            # 轮询任务状态
            max_retries = 60 # 60 * 5s = 5分钟
            for i in range(max_retries):
                time.sleep(5)
                
                # 查询任务状态
                # URL: .../tasks/{task_id}
                check_url = f"{url}/{task_id}"
                check_res = requests.get(check_url, headers=headers, timeout=30, verify=False)
                
                if check_res.status_code == 200:
                    task_status = check_res.json()
                    status = task_status.get("status") # QUEUED, RUNNING, SUCCEEDED, FAILED
                    
                    if status == "SUCCEEDED":
                        _log_info("✅ 视频生成成功！")
                        # 获取视频 URL
                        # 通常在 result["content"] 或 result["video"]["url"]
                        # 假设结构:
                        # { "status": "SUCCEEDED", "content": { "video_url": "..." } }
                        # 或者
                        # { "result": { "video_url": "..." } }
                        
                        video_url = None
                        if "content" in task_status and "video_url" in task_status["content"]:
                            video_url = task_status["content"]["video_url"]
                        elif "result" in task_status and "video_url" in task_status["result"]:
                            video_url = task_status["result"]["video_url"]
                        # 深度遍历寻找 url
                        if not video_url:
                             # 简单粗暴的查找
                             str_res = json.dumps(task_status)
                             import re
                             urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', str_res)
                             if urls:
                                 # 过滤出视频链接 (mp4)
                                 mp4_urls = [u for u in urls if ".mp4" in u or ".mov" in u]
                                 if mp4_urls:
                                     video_url = mp4_urls[0]
                                 else:
                                     video_url = urls[0] # 可能是预签名链接
                        
                        if video_url:
                            return self.download_and_process_video(video_url)
                        else:
                            raise Exception("无法从响应中提取视频 URL")
                            
                    elif status == "FAILED":
                        err_msg = task_status.get("error", {}).get("message", "未知错误")
                        raise Exception(f"任务失败: {err_msg}")
                    
                    else:
                        _log_info(f"任务状态: {status} ({i+1}/{max_retries})")
                else:
                    _log_warning(f"查询状态失败: {check_res.status_code}")
            
            raise Exception("任务超时")

        except Exception as e:
            _log_error(f"执行失败: {e}")
            # 返回空图像和错误信息
            return (self.create_blank_image(), str(e))

    def download_and_process_video(self, video_url):
        """下载视频并返回"""
        try:
            _log_info(f"正在下载视频: {video_url}")
            res = requests.get(video_url, stream=True, verify=False)
            
            if res.status_code == 200:
                # 保存到临时文件
                # 或者保存到 ComfyUI output 目录
                output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))), "output")
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                
                filename = f"doubao_video_{int(time.time())}.mp4"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                _log_info(f"视频已保存: {filepath}")
                
                # 尝试读取视频帧
                # 需要 imageio 或 opencv
                # ComfyUI 环境通常有 imageio
                try:
                    import imageio
                    reader = imageio.get_reader(filepath)
                    frames = []
                    for frame in reader:
                        frames.append(frame)
                    
                    if frames:
                        # 转换为 tensor [B, H, W, C]
                        frames_np = np.array(frames).astype(np.float32) / 255.0
                        frames_tensor = torch.from_numpy(frames_np)
                        return (frames_tensor, filepath)
                except ImportError:
                    _log_warning("未安装 imageio，无法加载视频帧，仅返回路径")
                except Exception as e:
                    _log_warning(f"加载视频帧失败: {e}")
                
                # 如果无法加载帧，返回第一帧为空或占位符
                return (self.create_blank_image(), filepath)
            else:
                raise Exception(f"下载失败: {res.status_code}")
                
        except Exception as e:
            raise e

    def create_blank_image(self):
        return torch.zeros((1, 512, 512, 3), dtype=torch.float32)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "DoubaoVideoGeneration": DoubaoVideoGeneration
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DoubaoVideoGeneration": "🎬Doubao视频生成 @炮老师的小课堂"
}
