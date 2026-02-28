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

try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass

from comfy.comfy_types import IO
from comfy_api.input_impl import VideoFromFile

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


def _image_to_base64(image_tensor: torch.Tensor) -> str:
    pil = _tensor2pil(image_tensor)
    buf = BytesIO()
    pil.save(buf, format="JPEG", quality=90)
    import base64
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode('utf-8')


def _download_video(video_url: str) -> str:
    output_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(CURRENT_DIR))), "output"
    )
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, f"grok_video_{int(time.time())}.mp4")
    res = requests.get(video_url, stream=True, timeout=120)
    res.raise_for_status()
    with open(filepath, 'wb') as f:
        for chunk in res.iter_content(chunk_size=8192):
            f.write(chunk)
    return filepath


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
                "⏱️ 时长(秒)": ([6, 10, 15], {"default": 10}),
                "🖥️ 分辨率": (["480P", "720P", "1080P"], {"default": "1080P"}),
                "🌐 API线路": (["zhenzhen", "ip", "hk", "us"], {"default": "zhenzhen"}),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用 grok_config.json 中的密钥"
                }),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647}),
                "⏳ 最大等待(秒)": ("INT", {"default": 600, "min": 60, "max": 1800}),
                "🔄 查询间隔(秒)": ("INT", {"default": 5, "min": 3, "max": 30}),
            },
            "optional": {
                "🖼️ 参考图(图生视频)": ("IMAGE",),
                "🔗 自定义API地址": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🔗 视频URL", "📋 任务ID", "📄 响应信息")
    FUNCTION = "generate_video"
    CATEGORY = "🤖dapaoAPI/Grok"
    DESCRIPTION = "调用 xAI Grok-Video-3 生成视频 | 作者: @炮老师的小课堂"

    def generate_video(self, **kwargs):
        """
        执行视频生成

        Time: 2026/2/28 周六 10:40:00
        Author: @炮老师的小课堂
        """
        prompt = kwargs.get("📝 提示词", "")
        model = kwargs.get("🤖 模型", "grok-video-3")
        ratio = kwargs.get("📐 视频比例", "16:9")
        duration = kwargs.get("⏱️ 时长(秒)", 10)
        resolution = kwargs.get("🖥️ 分辨率", "1080P")
        api_route = kwargs.get("🌐 API线路", "zhenzhen")
        api_key_input = kwargs.get("🔑 API密钥", "")
        seed = kwargs.get("🎲 随机种子", 0)
        max_wait = kwargs.get("⏳ 最大等待(秒)", 600)
        poll_interval = kwargs.get("🔄 查询间隔(秒)", 5)
        image = kwargs.get("🖼️ 参考图(图生视频)")
        custom_url = kwargs.get("🔗 自定义API地址", "")

        if api_route == "ip":
            base_url = custom_url.strip() if custom_url.strip() else "https://ai.t8star.cn"
        else:
            base_url = BASE_URL_MAP.get(api_route, "https://ai.t8star.cn")

        api_key = _get_api_key(api_key_input)
        if not api_key:
            raise ValueError("未提供 API Key，请在节点或 grok_config.json 中配置")

        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        payload = {
            "prompt": prompt, "model": model,
            "ratio": ratio, "duration": duration, "resolution": resolution
        }
        if seed > 0:
            payload["seed"] = seed

        # 图生视频：转base64
        if image is not None:
            _log("正在处理参考图...")
            payload["images"] = [_image_to_base64(image)]
            _log("参考图处理完成")

        # 提交生成任务
        _log(f"提交任务... 模型:{model} 比例:{ratio} 时长:{duration}s")
        resp = requests.post(
            f"{base_url}/v2/videos/generations",
            headers=headers, json=payload, timeout=60
        )
        if resp.status_code != 200:
            raise RuntimeError(f"API错误: {resp.status_code} - {resp.text}")
        result = resp.json()
        task_id = result.get("task_id")
        if not task_id:
            raise RuntimeError(f"未返回任务ID: {result}")
        _log(f"任务已提交，ID: {task_id}")

        # 轮询任务状态
        start_time = time.time()
        while True:
            elapsed = time.time() - start_time
            if elapsed > max_wait:
                raise TimeoutError(f"视频生成超时（{elapsed:.0f}s）")

            time.sleep(poll_interval)
            try:
                sr = requests.get(
                    f"{base_url}/v2/videos/generations/{task_id}",
                    headers=headers, timeout=30
                )
                if sr.status_code != 200:
                    continue
                sr_data = sr.json()
                status = sr_data.get("status", "UNKNOWN")
                _log(f"状态: {status}（已等待 {elapsed:.0f}s）")

                if status == "SUCCESS":
                    video_url = sr_data.get("data", {}).get("output")
                    if not video_url:
                        continue
                    _log(f"生成成功，下载视频: {video_url}")
                    filepath = _download_video(video_url)
                    _log(f"视频已保存: {filepath}")
                    return (
                        VideoFromFile(open(filepath, 'rb')),
                        video_url,
                        task_id,
                        json.dumps({"code": "success", "url": video_url, "file": filepath}, ensure_ascii=False)
                    )
                elif status == "FAILURE":
                    fail_reason = sr_data.get("fail_reason", "未知错误")
                    raise RuntimeError(f"视频生成失败: {fail_reason}")
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                continue


NODE_CLASS_MAPPINGS = {
    "DapaoGrokVideoNode": GrokVideoNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoGrokVideoNode": "🤖 Grok视频生成 @炮老师的小课堂"
}
