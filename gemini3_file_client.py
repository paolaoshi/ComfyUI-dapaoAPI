"""
Gemini 3 File API Client
用于上传视频和音频文件到 Gemini API
"""

import os
import json
import aiohttp
import mimetypes
import tempfile
import numpy as np
from typing import Optional
from io import BytesIO

# 配置文件路径
CONFIG_FILE_PATH = os.path.join(os.path.dirname(__file__), 'gemini3_config.json')


def save_audio_to_file(audio_data: dict) -> str:
    """
    将ComfyUI音频tensor保存为临时WAV文件
    
    参数:
        audio_data: 包含 'waveform' 和 'sample_rate' 的字典
    
    返回:
        临时文件路径
    """
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
    
    # 处理多维度：[batch, channels, samples] -> [samples] 或 [samples, channels]
    waveform = np.squeeze(waveform)
    
    # 如果是多声道，转置为 [samples, channels]
    if waveform.ndim == 2 and waveform.shape[0] < waveform.shape[1]:
        waveform = waveform.T
    
    # Normalize to 16-bit PCM
    if np.issubdtype(waveform.dtype, np.floating):
        waveform = np.clip(waveform, -1.0, 1.0)
        waveform = (waveform * 32767).astype(np.int16)
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    temp_path = temp_file.name
    temp_file.close()
    
    # 写入WAV文件
    scipy.io.wavfile.write(temp_path, sample_rate, waveform)
    
    print(f"[dapaoAPI-Gemini3-File] 音频已保存到: {temp_path}")
    print(f"[dapaoAPI-Gemini3-File] 采样率: {sample_rate}, 形状: {waveform.shape}")
    
    return temp_path


def save_video_to_file(video_path: str) -> str:
    """
    验证视频文件是否存在
    
    参数:
        video_path: 视频文件路径
    
    返回:
        视频文件路径
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    
    return video_path


class GeminiFileClient:
    """
    Gemini File API 客户端
    用于上传大文件（视频、音频等）
    """
    
    def __init__(self, api_key: str, api_provider: str):
        """
        初始化文件客户端
        
        参数:
            api_key: API密钥
            api_provider: API提供商（google/comfly/T8等）
        """
        self.api_key = api_key
        self.api_provider = api_provider
        self.base_url = "https://generativelanguage.googleapis.com"
        self.timeout = 300  # 5分钟超时（用于大文件上传）
        
        # 加载提供商配置
        config = {}
        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                print(f"[dapaoAPI-Gemini3-File] 警告：无法读取配置文件: {e}")
        
        if 'api_providers' in config and self.api_provider in config['api_providers']:
            provider_config = config['api_providers'][self.api_provider]
            self.base_url = provider_config.get('base_url', self.base_url)
    
    def _get_upload_url(self) -> str:
        """获取文件上传URL"""
        # 如果base_url已包含版本路径，不再添加
        if self.base_url.rstrip('/').endswith(('v1', 'v1beta', 'v1alpha')):
            return f"{self.base_url.rstrip('/')}/files"
        else:
            return f"{self.base_url.rstrip('/')}/v1beta/files"
    
    def _get_mime_type(self, file_path: str) -> str:
        """
        获取文件的MIME类型
        
        参数:
            file_path: 文件路径
        
        返回:
            MIME类型字符串
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            return mime_type
        
        # 手动映射常见格式
        ext = os.path.splitext(file_path)[1].lower()
        mime_map = {
            '.mp4': 'video/mp4',
            '.mov': 'video/quicktime',
            '.avi': 'video/x-msvideo',
            '.mkv': 'video/x-matroska',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.m4a': 'audio/mp4',
            '.ogg': 'audio/ogg',
            '.flac': 'audio/flac',
        }
        return mime_map.get(ext, 'application/octet-stream')
    
    async def upload_file(self, file_path: str) -> str:
        """
        上传文件到 Gemini File API
        
        参数:
            file_path: 本地文件路径
        
        返回:
            文件URI（用于后续API调用）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_size = os.path.getsize(file_path)
        mime_type = self._get_mime_type(file_path)
        file_name = os.path.basename(file_path)
        
        print(f"[dapaoAPI-Gemini3-File] 准备上传文件:")
        print(f"  - 文件名: {file_name}")
        print(f"  - 大小: {file_size / 1024 / 1024:.2f} MB")
        print(f"  - MIME类型: {mime_type}")
        
        url = self._get_upload_url()
        
        # 构建multipart/form-data
        async with aiohttp.ClientSession() as session:
            # 读取文件内容
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 创建multipart数据
            data = aiohttp.FormData()
            data.add_field('file',
                          file_content,
                          filename=file_name,
                          content_type=mime_type)
            
            # 添加元数据
            metadata = {
                "file": {
                    "display_name": file_name
                }
            }
            data.add_field('metadata',
                          json.dumps(metadata),
                          content_type='application/json')
            
            headers = {
                "x-goog-api-key": self.api_key
            }
            
            print(f"[dapaoAPI-Gemini3-File] 开始上传到: {url}")
            
            async with session.post(url, data=data, headers=headers, timeout=self.timeout) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"文件上传失败 {response.status}: {error_text}")
                
                result = await response.json()
                print(f"[dapaoAPI-Gemini3-File] 上传响应: {result}")
                
                # 提取文件URI
                if 'file' in result and 'uri' in result['file']:
                    file_uri = result['file']['uri']
                    print(f"[dapaoAPI-Gemini3-File] 文件URI: {file_uri}")
                    return file_uri
                elif 'uri' in result:
                    file_uri = result['uri']
                    print(f"[dapaoAPI-Gemini3-File] 文件URI: {file_uri}")
                    return file_uri
                else:
                    raise Exception(f"无法从响应中提取文件URI: {result}")
    
    async def delete_file(self, file_uri: str):
        """
        删除已上传的文件
        
        参数:
            file_uri: 文件URI
        """
        # 从URI提取文件ID
        file_id = file_uri.split('/')[-1]
        
        url = f"{self._get_upload_url()}/{file_id}"
        
        headers = {
            "x-goog-api-key": self.api_key
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, headers=headers) as response:
                if response.status != 200:
                    error_text = await response.text()
                    print(f"[dapaoAPI-Gemini3-File] 删除文件失败: {error_text}")
                else:
                    print(f"[dapaoAPI-Gemini3-File] 文件已删除: {file_uri}")
