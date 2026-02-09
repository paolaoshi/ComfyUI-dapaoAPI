"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎨 SORA2 批量视频生成节点（T8Star API）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 基于 OpenAI SORA2 的批量视频生成
   - 支持并发生成（最高 10 并发）
   - 智能区分文生视频/图生视频（有图则图生视频，无图则文生视频）
   - 仅支持 T8Star API 供应商
   - 输出详细的视频流和文件名（参考 ComfyUI_Sora）

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v1.1.0
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
import concurrent.futures
import shutil
import re
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import comfy.utils
import folder_paths

# 配置文件路径
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "sora2_config.json")

def _log_info(message):
    print(f"[dapaoAPI-SORA2-Batch] {message}")

def _log_error(message):
    print(f"[dapaoAPI-SORA2-Batch] ❌ 错误：{message}")

def get_sora2_config():
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

def tensor2pil(image_tensor):
    if image_tensor.dim() == 4:
        image_tensor = image_tensor[0]
    image_np = (image_tensor.cpu().numpy() * 255).astype('uint8')
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

class EmptyVideoAdapter:
    """空视频适配器，用于错误处理或占位"""
    def __init__(self):
        self.is_empty = True
        
    def get_dimensions(self):
        return 1, 1  # 最小尺寸
    
    def save_to(self, output_path, format="auto", codec="auto", metadata=None):
        # 创建一个最小的黑色视频文件
        try:
            # 创建 1x1 黑色帧
            frame = np.zeros((1, 1, 3), dtype=np.uint8)
            # 使用 opencv 写入最小视频
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, 1.0, (1, 1))
            out.write(frame)
            out.release()
            return True
        except Exception as e:
            _log_error(f"创建空视频失败: {e}")
            return False

class Sora2BatchVideoGenerator:
    """
    SORA2 批量视频生成节点
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 构建 10 组输入
        inputs = {
            "required": {
                "🌐 API供应商": (["t8 (贞贞API)"], {"default": "t8 (贞贞API)"}),
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "T8Star API Key (留空使用配置文件)"}),
                "🤖 模型选择": (["sora-2", "sora-2-pro"], {"default": "sora-2"}),
                
                "🚀 最大并发数": ("INT", {"default": 3, "min": 1, "max": 10}),
                "📐 宽高比": (["16:9", "9:16"], {"default": "16:9"}),
                "⏱️ 视频时长": (["10", "15", "25"], {"default": "15"}),
                "🎬 高清模式": ("BOOLEAN", {"default": False}),
                "🎲 随机种子": ("INT", {"default": -1, "min": -1, "max": 2147483647}),
                "🎯 种子控制": (["随机", "固定", "递增"], {"default": "随机"}),
                "📂 输出目录": ("STRING", {"default": "sora_batch_output"}),
            },
            "optional": {}
        }
        
        # 动态添加 10 组 prompt 和 image
        for i in range(1, 11):
            inputs["optional"][f"🖼️ 图像 {i}"] = ("IMAGE",)
            inputs["optional"][f"📝 提示词 {i}"] = ("STRING", {"multiline": True, "default": "", "placeholder": f"第 {i} 个视频的提示词 (留空则跳过)"})
            
        return inputs

    # Outputs: merged_video, merged_filename, video_1, filename_1 ... video_10, filename_10, report
    RETURN_TYPES = ("VIDEO", "STRING") + tuple(["VIDEO", "STRING"] * 10) + ("STRING",)
    RETURN_NAMES = ("🎬 合并视频", "📄 合并文件名") + tuple([n for i in range(1, 11) for n in (f"🎬 视频 {i}", f"📄 文件名 {i}")]) + ("📋 执行报告",)
    
    FUNCTION = "generate_batch"
    CATEGORY = "🤖dapaoAPI/SORA2"
    DESCRIPTION = "批量并发生成 SORA2 视频，智能区分文生视频/图生视频 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = True

    def __init__(self):
        self.config = get_sora2_config()
        self.base_url = self.config.get("base_url", "https://ai.t8star.cn")
        self.timeout = self.config.get("timeout", 900)
        self.last_seed = -1

    def image_to_base64(self, image_tensor):
        if image_tensor is None: return None
        try:
            pil_image = tensor2pil(image_tensor)
            buffered = BytesIO()
            pil_image.save(buffered, format="PNG")
            base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            return f"data:image/png;base64,{base64_str}"
        except Exception as e:
            _log_error(f"图像转换失败: {e}")
            return None

    def _download_video(self, url, output_dir, filename):
        """下载视频到本地"""
        try:
            base_output_dir = folder_paths.get_output_directory()
            target_dir = os.path.join(base_output_dir, output_dir)
            os.makedirs(target_dir, exist_ok=True)
            
            file_path = os.path.join(target_dir, filename)
            
            response = requests.get(url, stream=True, timeout=60)
            if response.status_code == 200:
                with open(file_path, 'wb') as f:
                    response.raw.decode_content = True
                    shutil.copyfileobj(response.raw, f)
                return file_path
            else:
                _log_error(f"下载失败: {response.status_code} - {url}")
                return None
        except Exception as e:
            _log_error(f"下载异常: {e}")
            return None

    def _generate_single_video(self, params, index, pbar):
        """生成单个视频的任务函数"""
        prompt = params["prompt"]
        image = params.get("image")
        model = params["model"]
        aspect_ratio = params["aspect_ratio"]
        duration = params["duration"]
        hd = params["hd"]
        seed = params["seed"]
        api_key = params["api_key"]
        
        task_name = f"任务-{index}"
        _log_info(f"[{task_name}] 开始处理: {prompt[:20]}...")

        # 模型映射
        api_model = "sora_video2" 

        # 构建 Prompt
        enhanced_prompt = prompt
        params_desc = []
        if aspect_ratio: params_desc.append(f"--ar {aspect_ratio}")
        if duration: params_desc.append(f"--d {duration}")
        
        if params_desc:
            enhanced_prompt += " " + " ".join(params_desc)

        messages = []
        if image is not None:
            img_b64 = self.image_to_base64(image)
            if img_b64:
                messages = [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": enhanced_prompt},
                        {"type": "image_url", "image_url": {"url": img_b64, "detail": "high"}}
                    ]
                }]
                _log_info(f"[{task_name}] 模式: 图生视频")
            else:
                _log_info(f"[{task_name}] 图像转换失败，降级为文生视频")
                messages = [{"role": "user", "content": enhanced_prompt}]
        else:
            _log_info(f"[{task_name}] 模式: 文生视频")
            messages = [{"role": "user", "content": enhanced_prompt}]

        # 构建 API URL
        base = self.base_url.rstrip('/')
        if not base.endswith('/v1'):
            base += '/v1'
        api_url = f"{base}/chat/completions"

        payload = {
            "model": api_model,
            "messages": messages,
            "stream": True,
            # 尝试将参数放入 payload
            "aspect_ratio": aspect_ratio,
            "duration": duration,
            "hd": hd
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        try:
            # 发送请求
            resp = requests.post(api_url, headers=headers, json=payload, timeout=600, stream=True)
            
            if resp.status_code != 200:
                try:
                    err = resp.text
                except:
                    err = str(resp.status_code)
                return {"index": index, "status": "failed", "error": f"API请求失败: {err}"}
            
            # 解析流
            video_url = None
            full_content = ""
            
            for line in resp.iter_lines():
                if not line: continue
                decoded_line = line.decode('utf-8').strip()
                if not decoded_line.startswith('data:'):
                    continue
                    
                json_str = decoded_line[5:].strip()
                if json_str == "[DONE]": break
                
                try:
                    data = json.loads(json_str)
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            full_content += content
                except:
                    pass
            
            # 提取 URL
            url_match = re.search(r'https://[^\s\)]+\.mp4', full_content)
            if url_match:
                video_url = url_match.group(0)
                
            if video_url:
                _log_info(f"[{task_name}] ✅ 生成成功")
                
                filename = f"sora_batch_{index}_{int(time.time())}.mp4"
                return {"index": index, "status": "success", "url": video_url, "filename": filename}
            else:
                return {"index": index, "status": "failed", "error": "未能从响应中提取视频URL"}

        except Exception as e:
            return {"index": index, "status": "error", "error": str(e)}

    def generate_batch(self, **kwargs):
        # 1. 解析参数 (使用中文键名)
        api_key = kwargs.get("🔑 API密钥", "").strip()
        if not api_key:
            api_key = self.config.get("api_key", "")
        if not api_key:
            raise ValueError("❌ 错误：未配置 API 密钥")
            
        model = kwargs.get("🤖 模型选择")
        max_concurrent = kwargs.get("🚀 最大并发数", 3)
        aspect_ratio = kwargs.get("📐 宽高比")
        duration = kwargs.get("⏱️ 视频时长")
        hd = kwargs.get("🎬 高清模式")
        base_seed = kwargs.get("🎲 随机种子", -1)
        seed_control = kwargs.get("🎯 种子控制", "随机")
        output_dir = kwargs.get("📂 输出目录", "sora_batch_output")
        
        # 2. 收集任务
        tasks = []
        for i in range(1, 11):
            prompt = kwargs.get(f"📝 提示词 {i}", "").strip()
            image = kwargs.get(f"🖼️ 图像 {i}")
            
            # 如果没有 prompt 且没有 image，则跳过
            if not prompt and image is None:
                continue
                
            if not prompt and image is not None:
                prompt = "Animate this image" # 默认提示词
            
            # 计算种子
            if seed_control == "固定":
                current_seed = base_seed
            elif seed_control == "递增":
                current_seed = base_seed + i if base_seed != -1 else -1
            else: # 随机
                current_seed = -1 # API 会处理随机
                
            tasks.append({
                "index": i,
                "prompt": prompt,
                "image": image,
                "model": model,
                "aspect_ratio": aspect_ratio,
                "duration": duration,
                "hd": hd,
                "seed": current_seed,
                "api_key": api_key
            })
            
        if not tasks:
            # 返回全空
            empty_adapter = EmptyVideoAdapter()
            empty_outputs = [empty_adapter, ""] * 11 + ["未找到有效任务"]
            return tuple(empty_outputs)
            
        _log_info(f"收集到 {len(tasks)} 个生成任务，最大并发: {max_concurrent}")
        
        # 3. 并发执行
        results_map = {} # index -> result
        pbar = comfy.utils.ProgressBar(len(tasks))
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            future_to_task = {executor.submit(self._generate_single_video, task, task["index"], pbar): task for task in tasks}
            
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                idx = task["index"]
                try:
                    res = future.result()
                    
                    # 如果成功，下载视频
                    if res["status"] == "success":
                        local_path = self._download_video(res["url"], output_dir, res["filename"])
                        if local_path:
                            res["local_path"] = local_path
                            # 包装为 Adapter
                            res["video_adapter"] = ComflyVideoAdapter(local_path)
                        else:
                            res["status"] = "download_failed"
                            res["error"] = "下载失败"
                            
                    results_map[idx] = res
                    pbar.update(1)
                except Exception as exc:
                    _log_error(f"任务 {idx} 异常: {exc}")
                    results_map[idx] = {"index": idx, "status": "error", "error": str(exc)}

        # 4. 构建输出
        # 输出顺序: 合并视频, 合并文件名, 视频 1, 文件名 1 ... 视频 10, 文件名 10, 报告
        
        # 合并视频暂时留空
        # 使用 EmptyVideoAdapter 而不是 None
        empty_adapter = EmptyVideoAdapter()
        final_outputs = [empty_adapter, ""]
        
        report_lines = []
        
        for i in range(1, 11):
            if i in results_map:
                res = results_map[i]
                if res["status"] == "success" and "local_path" in res:
                    # 返回 Adapter
                    final_outputs.append(res.get("video_adapter"))
                    final_outputs.append(res["filename"])
                    report_lines.append(f"任务 {i}: ✅ 成功 - {res['filename']}")
                else:
                    final_outputs.append(empty_adapter)
                    final_outputs.append("")
                    report_lines.append(f"任务 {i}: ❌ 失败 - {res.get('error', '未知错误')}")
            else:
                final_outputs.append(empty_adapter)
                final_outputs.append("")
        
        final_outputs.append("\n".join(report_lines))
        
        return tuple(final_outputs)
