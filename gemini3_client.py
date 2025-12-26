"""
Gemini 3 API Client for dapaoAPI
基于 ComfyUI-Gemini-3 项目优化
"""

import os
import json
import base64
import aiohttp
import asyncio
from typing import Optional, List, Dict, Any
from io import BytesIO
from PIL import Image
import numpy as np

# 配置文件路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'gemini3_config.json')


def get_api_key(api_provider: str, api_key_override: str = "") -> Optional[str]:
    """
    获取API密钥，优先级：节点输入 > 配置文件 > 环境变量
    """
    # 1. 从节点输入
    if api_key_override and api_key_override.strip():
        return api_key_override.strip()
    
    # 2. 从配置文件
    config = {}
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            print(f"[dapaoAPI-Gemini3] 警告：无法读取配置文件: {e}")
    
    if 'api_providers' in config and api_provider in config['api_providers']:
        provider_config = config['api_providers'][api_provider]
        api_key_from_config = provider_config.get('api_key')
        if api_key_from_config and api_key_from_config.strip():
            return api_key_from_config.strip()
    
    # 3. 从环境变量
    env_var_map = {
        "google": "GEMINI_API_KEY",
        "comfly": "COMFLY_API_KEY",
        "T8": "T8_API_KEY"
    }
    env_var_name = env_var_map.get(api_provider)
    if env_var_name:
        api_key_from_env = os.environ.get(env_var_name)
        if api_key_from_env and api_key_from_env.strip():
            return api_key_from_env.strip()
    
    return None


def encode_image_tensor(image_tensor, max_size=1568) -> str:
    """将ComfyUI tensor转换为base64 JPEG"""
    # Convert tensor to numpy array
    if hasattr(image_tensor, 'cpu'):
        image_np = image_tensor.cpu().numpy()
    else:
        image_np = np.array(image_tensor)
    
    # Convert to 0-255 range
    if image_np.max() <= 1.0:
        image_np = (image_np * 255).astype(np.uint8)
    
    # Create PIL Image
    img = Image.fromarray(image_np)

    # Resize if too large (maintain aspect ratio)
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Encode to JPEG
    buffer = BytesIO()
    # Convert to RGB if needed (JPEG doesn't support alpha)
    if img.mode in ('RGBA', 'LA'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')
        
    img.save(buffer, format='JPEG', quality=90, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode('utf-8')


def encode_audio_tensor(audio_data: dict) -> str:
    """将ComfyUI音频tensor转换为base64 WAV"""
    try:
        import scipy.io.wavfile
    except ImportError:
        raise ImportError("需要安装 scipy: pip install scipy")
    
    waveform = audio_data.get('waveform')
    sample_rate = audio_data.get('sample_rate', 44100)
    
    if waveform is None:
        raise ValueError("音频数据必须包含 'waveform'")
    
    # Convert to numpy array
    if hasattr(waveform, 'cpu'):
        waveform = waveform.cpu().numpy()
    waveform = np.squeeze(waveform)  # Remove batch/channel dims
    
    # Normalize to 16-bit PCM
    if np.issubdtype(waveform.dtype, np.floating):
        waveform = (waveform * 32767).astype(np.int16)
    
    # Write to in-memory WAV file
    buffer = BytesIO()
    scipy.io.wavfile.write(buffer, sample_rate, waveform)
    buffer.seek(0)
    
    return base64.b64encode(buffer.read()).decode('utf-8')


class GeminiClient:
    """Gemini 3 异步客户端"""
    
    def __init__(self, api_key: str, api_provider: str):
        self.api_key = api_key
        self.api_provider = api_provider
        self.session: Optional[aiohttp.ClientSession] = None
        self.base_url = "https://generativelanguage.googleapis.com"
        self.timeout = 300
        
        # 加载提供商配置
        config = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"[dapaoAPI-Gemini3] 警告：无法读取配置文件: {e}")
        
        if 'api_providers' in config and self.api_provider in config['api_providers']:
            provider_config = config['api_providers'][self.api_provider]
            self.base_url = provider_config.get('base_url', self.base_url)
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _get_endpoint(self, model: str) -> str:
        """获取API端点URL"""
        # 如果base_url已包含版本路径，不再添加
        if self.base_url.rstrip('/').endswith(('v1', 'v1beta', 'v1alpha')):
            return f"{self.base_url.rstrip('/')}/models/{model}:generateContent"
        else:
            return f"{self.base_url.rstrip('/')}/v1beta/models/{model}:generateContent"
    
    async def generate_content(
        self,
        model: str,
        contents: List[Dict[str, Any]],
        temperature: float = 0.7,
        top_p: float = 0.9,
        max_tokens: int = 2048
    ) -> Dict[str, Any]:
        """生成内容"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = self._get_endpoint(model)
        
        # 构建请求payload
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "topP": top_p,
                "maxOutputTokens": max_tokens
            },
            "safetySettings": [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]
        }
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }
        
        async with self.session.post(url, json=payload, headers=headers, timeout=self.timeout) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"Gemini API错误 {response.status}: {error_text}")
            return await response.json()


def run_async(coro):
    """运行异步协程 - 兼容ComfyUI的事件循环"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果循环正在运行，使用nest_asyncio
            try:
                import nest_asyncio
                nest_asyncio.apply()
            except ImportError:
                print("[dapaoAPI-Gemini3] 警告：建议安装 nest_asyncio")
            return loop.run_until_complete(coro)
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(coro)
        finally:
            asyncio.set_event_loop(None)
