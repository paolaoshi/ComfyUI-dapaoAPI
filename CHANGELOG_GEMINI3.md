# Gemini 3 节点更新日志

## v1.1.0 (2024-11-25)

### 🎉 新功能

#### 🎬 新增 Gemini 3 视频音频节点
- **真实视频文件上传**：支持直接上传 mp4, mov, avi 等视频文件
- **音频文件上传**：支持 mp3, wav, m4a 等音频格式
- **混合分析**：可同时分析图像、视频和音频内容
- **File API 集成**：使用 Gemini File API 处理大文件

### 🐛 Bug 修复

#### 修复音频上传问题
- **问题**：原节点使用 `inline_data` 格式上传音频，导致 API 无法识别
- **解决**：改用 Gemini File API 上传音频文件
- **影响节点**：
  - ✅ 💎 Gemini 3 多功能节点（已修复）
  - ✅ 🎬 Gemini 3 视频音频节点（新节点，原生支持）

#### 视频分析改进
- **问题**：原节点将视频作为图像批次处理，丢失时序信息
- **解决**：新节点支持真实视频文件上传，保留完整视频信息
- **对比**：
  - 原节点：图像批次（IMAGE类型）→ 采样10帧 → 作为图像序列
  - 新节点：视频文件路径（STRING类型）→ 完整视频 → File API 上传

### 📝 技术细节

#### File API 实现
```python
# 音频处理流程
1. ComfyUI 音频 tensor → 临时 WAV 文件
2. 上传到 Gemini File API
3. 获取 file_uri
4. 在 API 请求中使用 file_data 格式
5. 自动清理临时文件

# 视频处理流程
1. 读取本地视频文件
2. 上传到 Gemini File API
3. 获取 file_uri
4. 在 API 请求中使用 file_data 格式
```

#### 数据格式对比
```python
# 旧格式（inline_data）- 不支持音频
{
    "inline_data": {
        "mime_type": "audio/wav",
        "data": "base64_encoded_data"
    }
}

# 新格式（file_data）- 支持音频和视频
{
    "file_data": {
        "mime_type": "audio/wav",
        "file_uri": "https://generativelanguage.googleapis.com/v1beta/files/..."
    }
}
```

### 🔄 兼容性

- ✅ 完全向后兼容
- ✅ 原有节点功能不受影响
- ✅ 新节点作为独立功能添加
- ✅ 可以同时使用两个节点

### 📚 文档更新

- ✅ 新增 `docs/gemini3_video_audio_guide.md` 使用指南
- ✅ 更新 `README.md` 节点列表
- ✅ 新增 `test_video_audio.py` 测试脚本

### 🔧 依赖更新

- ✅ scipy：音频处理（已在 requirements.txt 中）
- ✅ aiohttp：异步 HTTP 请求
- ✅ nest-asyncio：事件循环兼容

### 🎯 使用建议

#### 选择原节点（💎 Gemini 3 多功能）的场景：
- 需要对视频帧进行预处理
- 只分析视频的部分帧
- 与其他图像处理节点配合使用
- 不需要完整的视频时序信息

#### 选择新节点（🎬 Gemini 3 视频音频）的场景：
- 直接分析完整视频文件
- 分析音频文件
- 需要保留视频的时序信息
- 处理长视频
- 混合分析（图像+视频+音频）

### 🐛 已知问题

- 大文件（>100MB）上传可能较慢
- 某些镜像站可能不支持 File API
- 需要确保文件路径正确且文件存在

### 🔜 未来计划

- [ ] 支持更多视频格式
- [ ] 添加视频预处理选项
- [ ] 优化大文件上传速度
- [ ] 添加文件管理功能（查看、删除已上传文件）
- [ ] 支持视频 URL 直接输入

---

👨‍🏫 作者：@炮老师的小课堂
📦 项目：ComfyUI-dapaoAPI
