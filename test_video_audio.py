"""
测试 Gemini 3 视频音频节点
用于验证文件上传和API调用功能
"""

import asyncio
import os
import sys

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

from gemini3_file_client import GeminiFileClient, save_audio_to_file
from gemini3_client import get_api_key
import numpy as np


async def test_audio_upload():
    """测试音频上传"""
    print("\n" + "="*60)
    print("测试音频上传功能")
    print("="*60)
    
    # 获取API密钥
    api_key = get_api_key("comfly", "")
    if not api_key:
        print("❌ 错误：未配置API密钥")
        return
    
    # 创建测试音频数据（1秒的440Hz正弦波）
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    waveform = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    
    audio_data = {
        'waveform': waveform,
        'sample_rate': sample_rate
    }
    
    try:
        # 保存音频到临时文件
        print("\n1. 保存音频到临时文件...")
        temp_path = save_audio_to_file(audio_data)
        print(f"✅ 音频已保存: {temp_path}")
        print(f"   文件大小: {os.path.getsize(temp_path) / 1024:.2f} KB")
        
        # 上传到 Gemini File API
        print("\n2. 上传到 Gemini File API...")
        client = GeminiFileClient(api_key, "comfly")
        file_uri = await client.upload_file(temp_path)
        print(f"✅ 上传成功!")
        print(f"   文件URI: {file_uri}")
        
        # 清理临时文件
        os.remove(temp_path)
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_video_upload(video_path: str):
    """测试视频上传"""
    print("\n" + "="*60)
    print("测试视频上传功能")
    print("="*60)
    
    if not os.path.exists(video_path):
        print(f"❌ 错误：视频文件不存在: {video_path}")
        return
    
    # 获取API密钥
    api_key = get_api_key("comfly", "")
    if not api_key:
        print("❌ 错误：未配置API密钥")
        return
    
    try:
        print(f"\n视频文件: {video_path}")
        print(f"文件大小: {os.path.getsize(video_path) / 1024 / 1024:.2f} MB")
        
        # 上传到 Gemini File API
        print("\n上传到 Gemini File API...")
        client = GeminiFileClient(api_key, "comfly")
        file_uri = await client.upload_file(video_path)
        print(f"✅ 上传成功!")
        print(f"   文件URI: {file_uri}")
        
        print("\n✅ 测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


def main():
    """主函数"""
    print("="*60)
    print("Gemini 3 视频音频节点测试工具")
    print("="*60)
    
    # 测试音频上传
    print("\n[测试1] 音频上传")
    asyncio.run(test_audio_upload())
    
    # 测试视频上传（如果提供了视频路径）
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        print("\n[测试2] 视频上传")
        asyncio.run(test_video_upload(video_path))
    else:
        print("\n[提示] 要测试视频上传，请提供视频文件路径:")
        print("  python test_video_audio.py E:\\Videos\\sample.mp4")


if __name__ == "__main__":
    main()
