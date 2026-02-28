"""
大炮 API - Seedream 5.0 图像生成节点
支持文生图、单图生图、多图融合、组图生成

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
import random
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 节点版本和作者信息
__version__ = "1.0.0"
__author__ = "@炮老师的小课堂"


# 日志函数
def _log_info(message):
    print(f"[dapaoAPI-Seedream5.0] 信息：{message}")

def _log_warning(message):
    print(f"[dapaoAPI-Seedream5.0] 警告：{message}")

def _log_error(message):
    print(f"[dapaoAPI-Seedream5.0] 错误：{message}")


# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CURRENT_DIR, 'config.json')


def get_config():
    """
    获取配置文件

    Time: 2026/2/27
    Author: HeGenAI
    """
    default_config = {
        "api_key": "",
        "base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "timeout": 180,
        "max_retries": 3
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
    if image.mode != 'RGB':
        image = image.convert('RGB')

    np_image = np.array(image).astype(np.float32) / 255.0
    tensor = torch.from_numpy(np_image)
    tensor = tensor.unsqueeze(0)

    return tensor


def tensor2pil(tensor: torch.Tensor) -> Image.Image:
    """将ComfyUI tensor转换为PIL图像"""
    if len(tensor.shape) == 4:
        tensor = tensor[0]

    np_image = tensor.cpu().numpy()
    np_image = np.clip(np_image, 0, 1)
    np_image = (np_image * 255).astype(np.uint8)

    return Image.fromarray(np_image)


def create_blank_tensor(width=512, height=512):
    """创建空白tensor"""
    blank_image = np.zeros((height, width, 3), dtype=np.float32)
    tensor = torch.from_numpy(blank_image).unsqueeze(0)
    return tensor


def image_to_base64_dataurl(image_tensor: torch.Tensor, max_size=2048) -> str:
    """
    将图像tensor转换为 data URL 格式的 base64 字符串（用于火山引擎 API）

    :param image_tensor: 输入的图像张量
    :param max_size: 最大尺寸，超过此尺寸会压缩
    :return: data URL 格式的 base64 字符串

    Time: 2026/2/27
    Author: HeGenAI
    """
    try:
        pil_image = tensor2pil(image_tensor)

        original_size = pil_image.size
        if max(original_size) > max_size:
            ratio = max_size / max(original_size)
            new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
            pil_image = pil_image.resize(new_size, Image.Resampling.LANCZOS)
            _log_info(f"图像压缩: {original_size} -> {new_size}")

        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        _log_error(f"图像转base64失败: {e}")
        return None




class Seedream50_ImageGeneration:
    """
    Seedream 5.0 图像生成节点 v1.0

    功能特性：
    - 文生图：根据文本提示词生成图像
    - 单图生图：基于单张参考图生成
    - 多图融合：支持2-14张参考图融合生成
    - 组图生成：自动生成一组内容关联的图片（最多15张）
    - 种子控制：固定、随机、递增三种模式
    - 灵活尺寸：支持2K/4K预设
    - 流式输出：支持流式输出模式

    作者：@炮老师的小课堂
    Time: 2026/2/27
    """

    @classmethod
    def INPUT_TYPES(cls):
        """
        定义节点输入参数

        Time: 2026/2/27
        Author: HeGenAI
        """
        config = get_config()

        return {
            "required": {
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "一只可爱的小猫，坐在窗台上，阳光洒在它身上，温暖的光线，高清摄影",
                    "placeholder": "请输入详细的图像描述..."
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件中的密钥"
                }),
                "🤖 模型ID": ("STRING", {
                    "default": "doubao-seedream-5-0-260128",
                    "placeholder": "模型ID或Endpoint ID"
                }),
                "📐 宽高比": ([
                    "1:1", "4:3", "3:4", "16:9", "9:16",
                    "3:2", "2:3", "21:9", "9:21"
                ], {
                    "default": "1:1"
                }),
                "📏 分辨率": (["2K", "4K"], {
                    "default": "2K"
                }),
                "📸 组图模式": (["关闭", "自动判断"], {
                    "default": "关闭",
                    "tooltip": "自动判断：模型根据提示词自主决定是否生成组图及数量"
                }),
                "📊 最大图片数": ("INT", {
                    "default": 15,
                    "min": 1,
                    "max": 15,
                    "step": 1,
                    "tooltip": "组图模式下，最多可生成的图片数量（输入参考图+生成图≤15）"
                }),
                "🎲 随机种子": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子，-1为随机"
                }),
                "🎯 种子控制": (["随机", "固定", "递增"], {
                    "default": "随机"
                }),
                "🌊 流式输出": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "启用后实时返回每张图片，组图场景下更快看到结果"
                }),
                "💧 添加水印": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "在图片右下角添加'AI生成'水印"
                }),
                "🔍 网络搜索": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "启用网络搜索功能，模型可以联网获取实时信息"
                }),
                "⏱️ 超时时间(秒)": ("INT", {
                    "default": 180,
                    "min": 30,
                    "max": 600,
                    "step": 10
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🖼️ 图像5": ("IMAGE",),
                "🖼️ 图像6": ("IMAGE",),
                "🖼️ 图像7": ("IMAGE",),
                "🖼️ 图像8": ("IMAGE",),
                "🖼️ 图像9": ("IMAGE",),
                "🖼️ 图像10": ("IMAGE",),
                "🖼️ 图像11": ("IMAGE",),
                "🖼️ 图像12": ("IMAGE",),
                "🖼️ 图像13": ("IMAGE",),
                "🖼️ 图像14": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("🖼️ 生成图像", "ℹ️ 生成信息")
    FUNCTION = "generate_image"
    CATEGORY = "🤖dapaoAPI/Seedream"
    DESCRIPTION = "Seedream 5.0 图像生成，支持文生图、多图融合、组图生成 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False

    def __init__(self):
        self.config = get_config()
        self.last_seed = -1

        # 官方 API size 参数格式：具体像素尺寸，如 "2048x2048"
        self.size_mapping = {
            "1:1":  {"2K": "2048x2048", "4K": "4096x4096"},
            "4:3":  {"2K": "2304x1728", "4K": "3456x2592"},
            "3:4":  {"2K": "1728x2304", "4K": "2592x3456"},
            "16:9": {"2K": "2560x1440", "4K": "3840x2160"},
            "9:16": {"2K": "1440x2560", "4K": "2160x3840"},
            "3:2":  {"2K": "2496x1664", "4K": "3744x2496"},
            "2:3":  {"2K": "1664x2496", "4K": "2496x3744"},
            "21:9": {"2K": "3008x1280", "4K": "4096x1792"},
            "9:21": {"2K": "1280x3008", "4K": "1792x4096"},
        }

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        seed_control = kwargs.get("🎯 种子控制", "随机")
        seed = kwargs.get("🎲 随机种子", -1)
        if seed_control in ["随机", "递增"]:
            return float("nan")
        return seed

    def generate_image(self, **kwargs):
        """
        调用 Seedream 5.0 API 生成图像

        Time: 2026/2/27
        Author: HeGenAI
        """
        # === 参数解析 ===
        prompt = kwargs.get("📝 提示词", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model = kwargs.get("🤖 模型ID", "doubao-seedream-5-0-260128")

        aspect_ratio = kwargs.get("📐 宽高比", "1:1")
        resolution = kwargs.get("📏 分辨率", "2K")

        group_mode = kwargs.get("📸 组图模式", "关闭")
        max_images = kwargs.get("📊 最大图片数", 15)

        seed = kwargs.get("🎲 随机种子", -1)
        seed_control = kwargs.get("🎯 种子控制", "随机")

        stream_enabled = kwargs.get("🌊 流式输出", False)
        watermark_enabled = kwargs.get("💧 添加水印", False)
        web_search_enabled = kwargs.get("🔍 网络搜索", False)
        timeout = kwargs.get("⏱️ 超时时间(秒)", 180)

        # === 收集参考图像 ===
        reference_images = []
        for i in range(1, 15):
            img_key = f"🖼️ 图像{i}"
            if img_key in kwargs and kwargs[img_key] is not None:
                reference_images.append(kwargs[img_key])

        status_info = []
        start_time = time.time()

        if not api_key:
            api_key = self.config.get("api_key", "")

        if not api_key:
            error_msg = "❌ 错误：未提供 API Key\n\n请在【🔑 API密钥】参数中输入或在 config.json 中配置"
            _log_error(error_msg)
            return (create_blank_tensor(), error_msg)

        try:
            # === 1. 计算图像尺寸 ===
            final_size = self.size_mapping.get(aspect_ratio, {}).get(resolution, "2048x2048")
            _log_info(f"使用尺寸: {final_size} (宽高比: {aspect_ratio}, 分辨率: {resolution})")
            status_info.append(f"📐 尺寸：{final_size} ({aspect_ratio}, {resolution})")

            # === 2. 处理参考图像 ===
            image_data_list = []
            if reference_images:
                _log_info(f"检测到 {len(reference_images)} 张参考图像")
                status_info.append(f"🖼️ 参考图：{len(reference_images)} 张")
                if len(reference_images) > 14:
                    _log_warning("参考图数量超过14张，仅使用前14张")
                    reference_images = reference_images[:14]
                for idx, img_tensor in enumerate(reference_images):
                    data_url = image_to_base64_dataurl(img_tensor)
                    if data_url:
                        image_data_list.append(data_url)
                        _log_info(f"成功转换参考图 {idx+1}")
                    else:
                        _log_warning(f"转换参考图 {idx+1} 失败")

            # === 3. 种子控制逻辑 ===
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

            self.last_seed = effective_seed
            _log_info(f"🎲 种子模式：{seed_control}，种子值：{effective_seed}")
            status_info.append(f"🎲 种子：{effective_seed}（{seed_control}）")

            # === 4. 构建 API 请求 ===
            base_url = self.config.get("base_url", "https://ark.cn-beijing.volces.com/api/v3")
            url = f"{base_url}/images/generations"

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "ComfyUI-dapaoAPI/1.0"
            }

            req_body = {
                "model": model,
                "prompt": prompt,
                "size": final_size,
                "response_format": "url",
                "watermark": watermark_enabled,
                "stream": stream_enabled
            }

            # 网络搜索：直接传给 Seedream 5.0 图像生成 API
            if web_search_enabled:
                req_body["web_search"] = {"enable": True}
                status_info.append("🔍 网络搜索：已启用（模型将联网搜索提示词相关信息）")
                _log_info("🔍 网络搜索已启用，web_search={\"enable\": True}")

            if image_data_list:
                req_body["image"] = image_data_list[0] if len(image_data_list) == 1 else image_data_list

            if group_mode == "自动判断":
                req_body["sequential_image_generation"] = "auto"
                req_body["sequential_image_generation_options"] = {"max_images": max_images}
                status_info.append(f"📸 组图模式：自动（最多{max_images}张）")
            else:
                req_body["sequential_image_generation"] = "disabled"
                status_info.append("📸 组图模式：关闭")

            _log_info(f"📤 发送请求到 Seedream 5.0 API...")
            _log_info(f"🤖 模型：{model}")
            _log_info(f"📋 请求体：{json.dumps(req_body, ensure_ascii=False, indent=2)}")
            status_info.append(f"🤖 模型：{model}")

            # === 5. 发送请求 ===
            response = requests.post(
                url,
                headers=headers,
                json=req_body,
                timeout=timeout,
                verify=False,
                stream=stream_enabled
            )

            if response.status_code != 200:
                error_msg = f"❌ 错误：API 请求失败\n\n状态码：{response.status_code}\n响应：{response.text[:500]}"
                _log_error(error_msg)
                return (create_blank_tensor(), error_msg)

            # === 6. 处理响应 ===
            all_generated_images = []

            if stream_enabled:
                _log_info("🌊 使用流式输出模式...")
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]
                            if data_str.strip() == '[DONE]':
                                break
                            try:
                                chunk_data = json.loads(data_str)
                                if "data" in chunk_data:
                                    for item in chunk_data["data"]:
                                        if "url" in item:
                                            image_url = item["url"]
                                            img_response = requests.get(image_url, timeout=60, verify=False)
                                            if img_response.status_code == 200:
                                                image = Image.open(io.BytesIO(img_response.content))
                                                all_generated_images.append(image)
                                                _log_info(f"✅ 成功下载图像 {len(all_generated_images)}：{image.size}")
                            except json.JSONDecodeError:
                                continue
            else:
                result = response.json()
                _log_info("📥 收到 API 响应")
                if "data" in result and result["data"]:
                    for idx, item in enumerate(result["data"]):
                        if "error" in item:
                            error_code = item["error"].get("code", "未知")
                            error_message = item["error"].get("message", "未知错误")
                            _log_warning(f"图像 {idx+1} 生成失败：{error_code} - {error_message}")
                            continue
                        image_url = item.get("url")
                        if image_url:
                            try:
                                _log_info(f"📥 下载图像 {idx+1}...")
                                img_response = requests.get(image_url, timeout=60, verify=False)
                                if img_response.status_code == 200:
                                    image = Image.open(io.BytesIO(img_response.content))
                                    all_generated_images.append(image)
                                    _log_info(f"✅ 成功下载图像 {idx+1}：{image.size}")
                            except Exception as e:
                                _log_warning(f"下载图像 {idx+1} 失败: {e}")

            # === 7. 检查结果 ===
            if not all_generated_images:
                error_msg = "❌ 错误：所有图像生成失败\n\n请检查：\n1. API Key 是否正确\n2. 网络连接是否正常\n3. 提示词是否合规\n4. 参考图是否符合要求"
                _log_error(error_msg)
                return (create_blank_tensor(), error_msg)

            # === 8. 转换为 tensor 并合并 ===
            image_tensors = [pil2tensor(img) for img in all_generated_images]
            final_tensor = image_tensors[0] if len(image_tensors) == 1 else torch.cat(image_tensors, dim=0)

            # === 9. 构建信息输出 ===
            end_time = time.time()
            elapsed_time = end_time - start_time
            status_info.append("=" * 40)
            status_info.append(f"✅ 成功生成 {len(all_generated_images)} 张图像")
            status_info.append("=" * 40)
            status_info.append(f"⏱️ 总耗时：{elapsed_time:.2f} 秒")
            if len(all_generated_images) > 1:
                status_info.append(f"⚡ 平均每张：{elapsed_time/len(all_generated_images):.2f} 秒")
            for idx, img in enumerate(all_generated_images):
                status_info.append(f"   图像 {idx+1}：{img.size[0]}x{img.size[1]}")

            info = "\n".join(status_info)
            _log_info(f"🎉 生成完成！成功生成 {len(all_generated_images)} 张图像")
            return (final_tensor, info)

        except Exception as e:
            error_msg = f"❌ 错误：图像生成失败\n\n错误详情：{str(e)}\n\n建议：\n1. 检查网络连接\n2. 检查 API Key 是否正确\n3. 查看终端完整日志"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return (create_blank_tensor(), error_msg)


# 节点映射
NODE_CLASS_MAPPINGS = {
    "Seedream50_ImageGeneration": Seedream50_ImageGeneration,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Seedream50_ImageGeneration": "🎨Seedream5.0图像生成@炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', '__version__', '__author__']

_log_info(f"Seedream 5.0 节点加载完成 v{__version__} by {__author__}")
_log_info(f"已注册 {len(NODE_CLASS_MAPPINGS)} 个节点")
