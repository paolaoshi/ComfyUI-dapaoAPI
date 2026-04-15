"""
大炮 API - Grok 视频生成节点
调用 xAI Grok-Video-3 模型生成视频

Time: 2026/2/28 周六 10:40:00
Author: @炮老师的小课堂
"""

import os
import json
import time
import requests
import numpy as np
import torch
from PIL import Image
from io import BytesIO
import shutil

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

from comfy.comfy_types import IO

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GROK_CONFIG_FILE = os.path.join(CURRENT_DIR, 'grok_config.json')

BASE_URL_MAP = {
    "zhenzhen": "https://ai.t8star.cn",
    "hk": "https://hk-api.gptbest.vip",
    "us": "https://api.gptbest.vip",
}

print("[dapaoAPI] Grok 视频节点模块已加载")


def _log(msg):
    print(f"[dapaoAPI-GrokVideo] {msg}")


def _get_api_key(api_key_input: str) -> str:
    if api_key_input and api_key_input.strip():
        return api_key_input.strip()
    try:
        if os.path.exists(GROK_CONFIG_FILE):
            with open(GROK_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("api_key", "")
    except Exception:
        pass
    return ""


def _tensor2pil(tensor: torch.Tensor) -> Image.Image:
    if len(tensor.shape) == 4:
        tensor = tensor[0]
    return Image.fromarray((np.clip(tensor.cpu().numpy(), 0, 1) * 255).astype(np.uint8))


class GrokVideoAdapter:
    """
    视频适配器类，用于包装视频URL

    Time: 2026/2/28 周六 10:40:00
    Author: @炮老师的小课堂
    """
    def __init__(self, video_path_or_url):
        if not video_path_or_url:
            self.is_url = False
            self.is_empty = True
            self.video_path = None
            self.video_url = None
        elif video_path_or_url.startswith('http'):
            self.is_url = True
            self.is_empty = False
            self.video_url = video_path_or_url
            self.video_path = None
        else:
            self.is_url = False
            self.is_empty = False
            self.video_path = video_path_or_url
            self.video_url = None
        
    def get_dimensions(self):
        if self.is_empty:
            return 1280, 720
        if self.is_url:
            return 1280, 720
        else:
            try:
                import cv2
                cap = cv2.VideoCapture(self.video_path)
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                cap.release()
                return width, height
            except Exception as e:
                print(f"Error getting video dimensions: {str(e)}")
                return 1280, 720
            
    def save_to(self, output_path, format="auto", codec="auto", metadata=None):
        if self.is_empty:
            return False
        if self.is_url:
            try:
                response = requests.get(self.video_url, stream=True)
                response.raise_for_status()
                
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
            except Exception as e:
                print(f"Error downloading video from URL: {str(e)}")
                return False
        else:
            try:
                shutil.copyfile(self.video_path, output_path)
                return True
            except Exception as e:
                print(f"Error copying video file: {str(e)}")
                return False


class GrokVideoNode:
    """
    Grok 视频生成节点

    Time: 2026/2/28 周六 10:40:00
    Author: @炮老师的小课堂
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "一个女人在月球跳舞",
                }),
                "🤖 模型": (["grok-video-3"], {"default": "grok-video-3"}),
                "📐 视频比例": (["2:3", "3:2", "16:9", "9:16", "1:1"], {"default": "16:9"}),
                "⏱️ 时长(秒)": (["6", "10", "15"], {"default": "10"}),
                "🖥️ 分辨率": (["480P", "720P", "1080P"], {"default": "1080P"}),
                "🌐 API线路": (["zhenzhen", "ip", "hk", "us"], {"default": "zhenzhen"}),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用 grok_config.json 中的密钥"
                }),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
            },
            "optional": {
                "🖼️ 参考图1": ("IMAGE",),
                "🖼️ 参考图2": ("IMAGE",),
                "🖼️ 参考图3": ("IMAGE",),
                "🖼️ 参考图4": ("IMAGE",),
                "🖼️ 参考图5": ("IMAGE",),
                "🖼️ 参考图6": ("IMAGE",),
                "🖼️ 参考图7": ("IMAGE",),
                "🔗 自定义API地址": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "📋 任务ID", "📄 响应信息", "🔗 视频URL")
    FUNCTION = "generate_video"
    CATEGORY = "🤖dapaoAPI/Grok"
    DESCRIPTION = "调用 xAI Grok-Video-3 生成视频 | 作者: @炮老师的小课堂"

    def __init__(self):
        self.api_key = ""
        self.timeout = 300

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def upload_image(self, image_tensor, base_url):
        """Upload image to the file endpoint and return the URL"""
        try:
            pil_image = _tensor2pil(image_tensor)

            buffered = BytesIO()
            pil_image.save(buffered, format="PNG")
            file_content = buffered.getvalue()

            files = {'file': ('image.png', file_content, 'image/png')}

            response = requests.post(
                f"{base_url}/v1/files",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'url' in result:
                return result['url']
            else:
                print(f"Unexpected response from file upload API: {result}")
                return None
                
        except Exception as e:
            print(f"Error uploading image: {str(e)}")
            return None

    def generate_video(self, **kwargs):
        """
        执行视频生成

        Time: 2026/2/28 周六 10:40:00
        Author: @炮老师的小课堂
        """
        # 获取参数
        prompt = kwargs.get("📝 提示词", "")
        model = kwargs.get("🤖 模型", "grok-video-3")
        ratio = kwargs.get("📐 视频比例", "16:9")
        duration = kwargs.get("⏱️ 时长(秒)", "10")
        resolution = kwargs.get("🖥️ 分辨率", "1080P")
        api_route = kwargs.get("🌐 API线路", "zhenzhen")
        api_key_input = kwargs.get("🔑 API密钥", "")
        seed = kwargs.get("🎲 随机种子", 0)
        custom_url = kwargs.get("🔗 自定义API地址", "")
        
        # 获取参考图
        all_images = [
            kwargs.get("🖼️ 参考图1"),
            kwargs.get("🖼️ 参考图2"),
            kwargs.get("🖼️ 参考图3"),
            kwargs.get("🖼️ 参考图4"),
            kwargs.get("🖼️ 参考图5"),
            kwargs.get("🖼️ 参考图6"),
            kwargs.get("🖼️ 参考图7"),
        ]
        
        # 设置base_url
        if api_route == "ip" and custom_url.strip():
            base_url = custom_url.strip()
        else:
            base_url = BASE_URL_MAP.get(api_route, "https://ai.t8star.cn")
        
        # 设置API密钥
        if api_key_input.strip():
            self.api_key = api_key_input.strip()
        else:
            self.api_key = _get_api_key("")
            
        if not self.api_key:
            error_response = {"code": "error", "message": "API key not found"}
            return (GrokVideoAdapter(""), "", json.dumps(error_response), "")
            
        try:
            import comfy.utils
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)

            payload = {
                "prompt": prompt,
                "model": model,
                "ratio": ratio,
                "duration": int(duration),
                "resolution": resolution
            }

            if seed > 0:
                payload["seed"] = seed

            # Handle image inputs (up to 7 reference images)
            image_urls = []
            
            for i, img in enumerate(all_images):
                if img is not None:
                    pbar.update_absolute(15 + i * 2)
                    uploaded_url = self.upload_image(img, base_url)
                    if uploaded_url:
                        image_urls.append(uploaded_url)
                    else:
                        error_message = f"Failed to upload image {i+1}. Please check your image and try again."
                        print(error_message)
                        return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")
            
            if image_urls:
                payload["images"] = image_urls

            pbar.update_absolute(30)
            
            # Submit video generation request
            response = requests.post(
                f"{base_url}/v2/videos/generations",
                headers=self.get_headers(),
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                error_message = f"API error: {response.status_code} - {response.text}"
                print(error_message)
                return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")
                
            result = response.json()
            
            # Extract task_id from response
            task_id = result.get("task_id")
            if not task_id:
                error_message = "No task ID returned from API"
                print(error_message)
                return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")
            
            pbar.update_absolute(40)
            
            # Poll for video generation completion
            video_url = None
            attempts = 0
            max_attempts = 200
            start_time = time.time()
            max_wait_time = 600
        
            while attempts < max_attempts:
                current_time = time.time()
                elapsed_time = current_time - start_time

                if elapsed_time > max_wait_time:
                    error_message = f"Video generation timeout after {elapsed_time:.1f} seconds (max: {max_wait_time}s)"
                    print(error_message)
                    return (GrokVideoAdapter(""), task_id, json.dumps({"code": "error", "message": error_message}), "")
                
                time.sleep(5)
                attempts += 1
                
                try:
                    # Query task status
                    status_response = requests.get(
                        f"{base_url}/v2/videos/generations/{task_id}",
                        headers=self.get_headers(),
                        timeout=30
                    )
                    
                    if status_response.status_code != 200:
                        continue
                        
                    status_result = status_response.json()
                    
                    # Check task status
                    status = status_result.get("status", "UNKNOWN")
                    
                    # Update progress bar based on status
                    if status == "IN_PROGRESS":
                        progress = status_result.get("progress", "0%")
                        try:
                            if progress.endswith('%'):
                                progress_num = int(progress.rstrip('%'))
                                pbar_value = min(90, 40 + progress_num * 50 / 100)
                                pbar.update_absolute(pbar_value)
                        except (ValueError, AttributeError):
                            progress_value = min(80, 40 + (attempts * 40 // max_attempts))
                            pbar.update_absolute(progress_value)
                    
                    # Handle different statuses
                    if status == "SUCCESS":
                        # Extract video URL from successful response
                        data = status_result.get("data", {})
                        output = data.get("output", "")
                        if output:
                            video_url = output
                            break
                        else:
                            continue
                    
                    elif status == "FAILURE":
                        fail_reason = status_result.get("fail_reason", "Unknown error")
                        error_message = f"Video generation failed: {fail_reason}"
                        print(error_message)
                        return (GrokVideoAdapter(""), task_id, json.dumps({"code": "error", "message": error_message}), "")
                    
                    elif status in ["NOT_START", "IN_PROGRESS"]:
                        continue
                    else:
                        continue
                    
                except requests.exceptions.Timeout:
                    continue
                except Exception as e:
                    continue
            
            if not video_url:
                error_message = f"Video generation timeout or failed to retrieve video URL after {attempts} attempts, elapsed time: {elapsed_time:.1f}s"
                print(error_message)
                return (GrokVideoAdapter(""), task_id, json.dumps({"code": "error", "message": error_message}), "")

            if video_url:
                pbar.update_absolute(95)
                print(f"Video generation completed, URL: {video_url}")
                
                # Return video adapter
                video_adapter = GrokVideoAdapter(video_url)
                return (video_adapter, task_id, json.dumps({"code": "success", "url": video_url}), video_url)
            
        except Exception as e:
            error_message = f"Error generating video: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")


class GrokVideo30sNode:
    """
    Grok 30秒视频生成节点

    Time: 2026/4/15
    Author: @炮老师的小课堂
    """

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🖼️ 参考图1": ("IMAGE",),
                "🖼️ 参考图2": ("IMAGE",),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "图片1的女人和图片2的女人在月球跳舞",
                }),
                "🤖 模型": (["grok-video-3"], {"default": "grok-video-3"}),
                "📐 视频比例": (["2:3", "3:2", "16:9", "9:16", "1:1"], {"default": "16:9"}),
                "⏱️ 时长(秒)": ("INT", {"default": 30, "min": 6, "max": 30}),
                "🖥️ 分辨率": (["480P", "720P", "1080P"], {"default": "720P"}),
                "🌐 API线路": (["zhenzhen", "ip", "hk", "us"], {"default": "zhenzhen"}),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用 grok_config.json 中的密钥"
                }),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "🎬 生成后控制": (["randomize", "fixed"], {"default": "randomize"}),
            },
            "optional": {
                "🖼️ 参考图3": ("IMAGE",),
                "🖼️ 参考图4": ("IMAGE",),
                "🖼️ 参考图5": ("IMAGE",),
                "🖼️ 参考图6": ("IMAGE",),
                "🖼️ 参考图7": ("IMAGE",),
                "🔗 自定义API地址": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "📋 任务ID", "📄 响应信息", "🔗 视频URL")
    FUNCTION = "generate_video"
    CATEGORY = "🤖dapaoAPI/Grok"
    DESCRIPTION = "调用 xAI Grok-Video-3 生成30秒视频 | 作者: @炮老师的小课堂"

    def __init__(self):
        self.api_key = ""
        self.timeout = 300

    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def upload_image(self, image_tensor, base_url):
        """Upload image to the file endpoint and return the URL"""
        try:
            pil_image = _tensor2pil(image_tensor)

            buffered = BytesIO()
            pil_image.save(buffered, format="PNG")
            file_content = buffered.getvalue()

            files = {'file': ('image.png', file_content, 'image/png')}

            response = requests.post(
                f"{base_url}/v1/files",
                headers={"Authorization": f"Bearer {self.api_key}"},
                files=files,
                timeout=self.timeout
            )

            response.raise_for_status()
            result = response.json()

            if 'url' in result:
                return result['url']
            else:
                print(f"Unexpected response from file upload API: {result}")
                return None

        except Exception as e:
            print(f"Error uploading image: {str(e)}")
            return None

    def generate_video(self, **kwargs):
        """
        执行30秒视频生成

        Time: 2026/4/15
        Author: @炮老师的小课堂
        """
        # 获取参数
        prompt = kwargs.get("📝 提示词", "")
        model = kwargs.get("🤖 模型", "grok-video-3")
        ratio = kwargs.get("📐 视频比例", "16:9")
        duration = kwargs.get("⏱️ 时长(秒)", 30)
        resolution = kwargs.get("🖥️ 分辨率", "720P")
        api_route = kwargs.get("🌐 API线路", "zhenzhen")
        api_key_input = kwargs.get("🔑 API密钥", "")
        seed = kwargs.get("🎲 随机种子", 0)
        post_control = kwargs.get("🎬 生成后控制", "randomize")
        custom_url = kwargs.get("🔗 自定义API地址", "")

        # 获取参考图（1和2必需，3-7可选）
        all_images = [
            kwargs.get("🖼️ 参考图1"),
            kwargs.get("🖼️ 参考图2"),
            kwargs.get("🖼️ 参考图3"),
            kwargs.get("🖼️ 参考图4"),
            kwargs.get("🖼️ 参考图5"),
            kwargs.get("🖼️ 参考图6"),
            kwargs.get("🖼️ 参考图7"),
        ]

        # 设置base_url
        if api_route == "ip" and custom_url.strip():
            base_url = custom_url.strip()
        else:
            base_url = BASE_URL_MAP.get(api_route, "https://ai.t8star.cn")

        # 设置API密钥
        if api_key_input.strip():
            self.api_key = api_key_input.strip()
        else:
            self.api_key = _get_api_key("")

        if not self.api_key:
            error_response = {"code": "error", "message": "API key not found"}
            return (GrokVideoAdapter(""), "", json.dumps(error_response), "")

        try:
            import comfy.utils
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)

            payload = {
                "prompt": prompt,
                "model": model,
                "ratio": ratio,
                "duration": duration,
                "resolution": resolution
            }

            if seed > 0:
                payload["seed"] = seed

            # Handle image inputs (up to 7 reference images)
            image_urls = []

            for i, img in enumerate(all_images):
                if img is not None:
                    pbar.update_absolute(15 + i * 2)
                    uploaded_url = self.upload_image(img, base_url)
                    if uploaded_url:
                        image_urls.append(uploaded_url)
                    else:
                        error_message = f"Failed to upload image {i+1}. Please check your image and try again."
                        print(error_message)
                        return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")

            if image_urls:
                payload["images"] = image_urls

            pbar.update_absolute(30)

            # Submit video generation request
            response = requests.post(
                f"{base_url}/v2/videos/generations",
                headers=self.get_headers(),
                json=payload,
                timeout=self.timeout
            )

            if response.status_code != 200:
                error_message = f"API error: {response.status_code} - {response.text}"
                print(error_message)
                return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")

            result = response.json()

            # Extract task_id from response
            task_id = result.get("task_id")
            if not task_id:
                error_message = "No task ID returned from API"
                print(error_message)
                return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")

            pbar.update_absolute(40)

            # Poll for video generation completion
            video_url = None
            attempts = 0
            max_attempts = 200
            start_time = time.time()
            max_wait_time = 600

            while attempts < max_attempts:
                current_time = time.time()
                elapsed_time = current_time - start_time

                if elapsed_time > max_wait_time:
                    error_message = f"Video generation timeout after {elapsed_time:.1f} seconds (max: {max_wait_time}s)"
                    print(error_message)
                    return (GrokVideoAdapter(""), task_id, json.dumps({"code": "error", "message": error_message}), "")

                time.sleep(5)
                attempts += 1

                try:
                    # Query task status
                    status_response = requests.get(
                        f"{base_url}/v2/videos/generations/{task_id}",
                        headers=self.get_headers(),
                        timeout=30
                    )

                    if status_response.status_code != 200:
                        continue

                    status_result = status_response.json()

                    # Check task status
                    status = status_result.get("status", "UNKNOWN")

                    # Update progress bar based on status
                    if status == "IN_PROGRESS":
                        progress = status_result.get("progress", "0%")
                        try:
                            if progress.endswith('%'):
                                progress_num = int(progress.rstrip('%'))
                                pbar_value = min(90, 40 + progress_num * 50 / 100)
                                pbar.update_absolute(pbar_value)
                        except (ValueError, AttributeError):
                            progress_value = min(80, 40 + (attempts * 40 // max_attempts))
                            pbar.update_absolute(progress_value)

                    # Handle different statuses
                    if status == "SUCCESS":
                        # Extract video URL from successful response
                        data = status_result.get("data", {})
                        output = data.get("output", "")
                        if output:
                            video_url = output
                            break
                        else:
                            continue

                    elif status == "FAILURE":
                        fail_reason = status_result.get("fail_reason", "Unknown error")
                        error_message = f"Video generation failed: {fail_reason}"
                        print(error_message)
                        return (GrokVideoAdapter(""), task_id, json.dumps({"code": "error", "message": error_message}), "")

                    elif status in ["NOT_START", "IN_PROGRESS"]:
                        continue
                    else:
                        continue

                except requests.exceptions.Timeout:
                    continue
                except Exception as e:
                    continue

            if not video_url:
                error_message = f"Video generation timeout or failed to retrieve video URL after {attempts} attempts, elapsed time: {elapsed_time:.1f}s"
                print(error_message)
                return (GrokVideoAdapter(""), task_id, json.dumps({"code": "error", "message": error_message}), "")

            if video_url:
                pbar.update_absolute(95)
                print(f"Video generation completed, URL: {video_url}")

                # Return video adapter
                video_adapter = GrokVideoAdapter(video_url)
                return (video_adapter, task_id, json.dumps({"code": "success", "url": video_url}), video_url)

        except Exception as e:
            error_message = f"Error generating video: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            return (GrokVideoAdapter(""), "", json.dumps({"code": "error", "message": error_message}), "")


NODE_CLASS_MAPPINGS = {
    "DapaoGrokVideoNode": GrokVideoNode,
    "DapaoGrokVideo30sNode": GrokVideo30sNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoGrokVideoNode": "🤖 Grok视频生成 @炮老师的小课堂",
    "DapaoGrokVideo30sNode": "🤖 Grok视频生成30s @炮老师的小课堂"
}
