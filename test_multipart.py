"""
测试 multipart/form-data 格式
查看 requests 库如何处理不同格式的文件数据
"""

import io
import requests
from PIL import Image
import numpy as np

# 创建一个测试图像
img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
pil_image = Image.fromarray(img_array)

# 方法1: 使用 BytesIO 对象
print("=" * 50)
print("方法1: BytesIO 对象")
img_byte_arr = io.BytesIO()
pil_image.save(img_byte_arr, format='PNG')
img_byte_arr.seek(0)

files1 = [
    ('image', ('image.png', img_byte_arr, 'image/png'))
]
data1 = {'prompt': 'test', 'model': 'test-model'}

print(f"files 类型: {type(files1)}")
print(f"files 内容: {[(name, filename, type_) for name, (filename, _, type_) in files1]}")

# 方法2: 使用字节数据
print("=" * 50)
print("方法2: 字节数据")
img_byte_arr2 = io.BytesIO()
pil_image.save(img_byte_arr2, format='PNG')
img_bytes = img_byte_arr2.getvalue()

files2 = [
    ('image', ('image.png', img_bytes, 'image/png'))
]
data2 = {'prompt': 'test', 'model': 'test-model'}

print(f"files 类型: {type(files2)}")
print(f"files 内容: {[(name, filename, type_) for name, (filename, _, type_) in files2]}")
print(f"字节数据大小: {len(img_bytes)}")

# 方法3: 使用字典格式
print("=" * 50)
print("方法3: 字典格式")
img_byte_arr3 = io.BytesIO()
pil_image.save(img_byte_arr3, format='PNG')
img_byte_arr3.seek(0)

files3 = {
    'image': ('image.png', img_byte_arr3, 'image/png')
}
data3 = {'prompt': 'test', 'model': 'test-model'}

print(f"files 类型: {type(files3)}")
print(f"files 内容: {list(files3.keys())}")

print("=" * 50)
print("测试完成")
