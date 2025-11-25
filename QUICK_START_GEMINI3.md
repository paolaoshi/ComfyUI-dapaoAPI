# 🚀 Gemini 3 视频音频节点快速启动指南

## 📦 安装完成

✅ 所有文件已创建
✅ scipy 依赖已安装
✅ 节点已注册

## 🔄 重启 ComfyUI

**重要**：必须重启 ComfyUI 才能加载新节点

```bash
# 关闭当前 ComfyUI
# 然后重新启动
```

## 🎯 找到新节点

重启后，在节点菜单中搜索：

1. **🎬 Gemini 3 视频音频** - 新节点（支持视频/音频文件）
2. **💎 Gemini 3 多功能** - 原节点（已修复音频问题）

位置：`🤖dapaoAPI` 分类下

## 🧪 快速测试

### 测试1：音频分析（使用音频文件）

```
节点：🎬 Gemini 3 视频音频

参数设置：
🎯 系统角色: 你是一个专业的音频分析师
💬 用户输入: 请识别这段音频的内容
🤖 模型选择: gemini-3-pro-preview-T8
🌐 镜像站: comfly
🔑 API密钥: [你的API密钥]
🎵 音频文件路径: E:\Audio\sample.mp3

点击运行 ▶️
```

### 测试2：视频分析（使用视频文件）

```
节点：🎬 Gemini 3 视频音频

参数设置：
🎯 系统角色: 你是一个专业的视频分析师
💬 用户输入: 请详细描述这个视频的内容
🤖 模型选择: gemini-3-pro-preview-T8
🌐 镜像站: comfly
🔑 API密钥: [你的API密钥]
🎬 视频文件路径: E:\Videos\sample.mp4

点击运行 ▶️
```

### 测试3：图像分析（使用原节点）

```
节点：💎 Gemini 3 多功能

参数设置：
🎯 系统角色: 你是一个专业的图像分析师
💬 用户输入: 请分析这张图片
🤖 模型选择: gemini-3-pro-preview-T8
🌐 镜像站: comfly
🔑 API密钥: [你的API密钥]
🖼️ 图像1: [连接图像加载节点]

点击运行 ▶️
```

## 🔑 配置 API 密钥

### 方法1：配置文件（推荐）

编辑 `gemini3_config.json`：

```json
{
  "api_providers": {
    "comfly": {
      "api_key": "你的API密钥",
      "base_url": "https://api.comfly.ai",
      "models": ["gemini-3-pro-preview", "gemini-3-flash"]
    }
  },
  "default_provider": "comfly"
}
```

### 方法2：节点参数

在节点的"🔑 API密钥"参数中直接输入

## 📝 文件路径格式

### Windows
```
E:\Videos\sample.mp4
E:\Audio\music.mp3
C:\Users\用户名\Documents\video.mov
```

### Linux/Mac
```
/home/user/videos/sample.mp4
/Users/username/audio/music.mp3
```

**注意**：
- 必须是完整的绝对路径
- 确保文件存在且可访问
- 路径中的中文需要系统支持

## 🎨 支持的格式

### 视频格式
- ✅ MP4 (.mp4)
- ✅ MOV (.mov)
- ✅ AVI (.avi)
- ✅ MKV (.mkv)
- ✅ WebM (.webm)

### 音频格式
- ✅ MP3 (.mp3)
- ✅ WAV (.wav)
- ✅ M4A (.m4a)
- ✅ OGG (.ogg)
- ✅ FLAC (.flac)

## 🐛 常见问题

### Q1: 找不到新节点？
**A**: 确保已重启 ComfyUI，并在 `🤖dapaoAPI` 分类下查找

### Q2: 提示找不到 scipy？
**A**: 运行 `pip install scipy`

### Q3: 音频/视频上传失败？
**A**: 检查：
- 文件路径是否正确
- 文件是否存在
- API密钥是否配置
- 网络连接是否正常

### Q4: API 返回错误？
**A**: 查看 ComfyUI 控制台日志，会有详细的错误信息

### Q5: 上传速度慢？
**A**: 
- 尝试切换镜像站（comfly/hk/us）
- 使用较小的文件测试
- 检查网络连接

## 📊 查看日志

在 ComfyUI 控制台中查找：

```
[dapaoAPI-Gemini3-Video] 开始上传视频文件...
[dapaoAPI-Gemini3-Video] 视频上传成功: https://...
[dapaoAPI-Gemini3-Video] API响应: ...
```

## 🎯 最佳实践

### 1. 选择合适的节点

| 场景 | 推荐节点 |
|------|---------|
| 分析完整视频文件 | 🎬 Gemini 3 视频音频 |
| 分析音频文件 | 🎬 Gemini 3 视频音频 |
| 分析视频帧序列 | 💎 Gemini 3 多功能 |
| 纯图像分析 | 💎 Gemini 3 多功能 |
| 混合分析（图+视频+音频） | 🎬 Gemini 3 视频音频 |

### 2. 优化提示词

```
好的提示词：
"请详细分析这个视频，包括场景、人物、动作、对话内容和背景音乐"

不好的提示词：
"分析视频"
```

### 3. 控制文件大小

- 视频：建议 < 100MB
- 音频：建议 < 50MB
- 如需分析大文件，考虑先压缩或剪辑

## 📚 更多文档

- 📖 [详细使用指南](docs/gemini3_video_audio_guide.md)
- 📝 [更新日志](CHANGELOG_GEMINI3.md)
- 📋 [完整更新总结](UPDATE_SUMMARY.md)

## 🎉 开始使用

1. ✅ 重启 ComfyUI
2. ✅ 配置 API 密钥
3. ✅ 准备测试文件
4. ✅ 创建工作流
5. ✅ 运行测试

---

👨‍🏫 作者：@炮老师的小课堂
📦 项目：ComfyUI-dapaoAPI
💬 如有问题，请查看详细文档或提交 Issue
