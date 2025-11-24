"""
测试 OpenAI SDK 发送的实际请求格式
通过拦截 HTTP 请求来查看 multipart/form-data 的具体格式
"""

import io
import requests
from PIL import Image
import numpy as np

# 创建一个测试图像
print("创建测试图像...")
img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
pil_image = Image.fromarray(img_array)

# 保存为字节流
img_byte_arr = io.BytesIO()
pil_image.save(img_byte_arr, format='PNG')
img_byte_arr.seek(0)
img_bytes = img_byte_arr.read()

print(f"图像大小: {len(img_bytes)} 字节")

# 测试不同的 files 格式
print("\n" + "="*50)
print("测试1: 列表格式 - 使用字节数据")
print("="*50)

files1 = [
    ('image', ('image.png', img_bytes, 'image/png'))
]
data1 = {
    'prompt': '测试提示词',
    'model': 'gemini-3-pro-image-preview',
    'response_format': 'b64_json'
}

print(f"files 格式: {type(files1)}")
print(f"files 内容: {[(name, filename) for name, (filename, _, _) in files1]}")
print(f"data 内容: {data1}")

# 测试2: 使用 BytesIO 对象
print("\n" + "="*50)
print("测试2: 列表格式 - 使用 BytesIO 对象")
print("="*50)

img_byte_arr2 = io.BytesIO()
pil_image.save(img_byte_arr2, format='PNG')
img_byte_arr2.seek(0)

files2 = [
    ('image', ('image.png', img_byte_arr2, 'image/png'))
]
data2 = {
    'prompt': '测试提示词',
    'model': 'gemini-3-pro-image-preview',
    'response_format': 'b64_json'
}

print(f"files 格式: {type(files2)}")
print(f"files 内容: {[(name, filename) for name, (filename, _, _) in files2]}")
print(f"data 内容: {data2}")

# 测试3: 字典格式
print("\n" + "="*50)
print("测试3: 字典格式")
print("="*50)

img_byte_arr3 = io.BytesIO()
pil_image.save(img_byte_arr3, format='PNG')
img_byte_arr3.seek(0)

files3 = {
    'image': ('image.png', img_byte_arr3, 'image/png')
}
data3 = {
    'prompt': '测试提示词',
    'model': 'gemini-3-pro-image-preview',
    'response_format': 'b64_json'
}

print(f"files 格式: {type(files3)}")
print(f"files 内容: {list(files3.keys())}")
print(f"data 内容: {data3}")

print("\n" + "="*50)
print("测试完成")
print("="*50)
