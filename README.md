# 🤖 dapaoAPI - ComfyUI 多功能 API 节点集合

<div align="center">

**一套强大的 ComfyUI 自定义节点，集成多个主流 AI 服务 API**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom%20Nodes-orange)](https://github.com/comfyanonymous/ComfyUI)

</div>

---

## 📖 项目简介

dapaoAPI 是一套为 ComfyUI 设计的高质量自定义节点集合，整合了各种主流 AI 服务，提供从图像生成、图像分析到文本处理的完整工作流支持。

---
## 🎉 效果演示
### 🚀 2025-11-29 新增bannan2 贞贞专区 稳定IP 增加20图编辑 保证出图稳定 支持文生图 图像编辑
![alt text](效果图/20图编辑.png)
### 🚀 2025-11-25 增加视频/音频反推功能

![alt text](效果图/音频+视频反推.png)
### 🚀 2025-11-24 重大更新！通用 API 节点发布

**新增两大核心节点，支持任意第三方和官方 API 调用！**

#### ✨ 核心特性
- 🌐 **通用 API 调用节点**：支持任意 HTTP API（OpenAI、Claude、Gemini 等）
- 🎨 **通用图像编辑节点**：专为图像生成和编辑优化
- 🔄 **智能适配**：自动识别 Gemini 官方 API，优先使用 SDK
- 🛡️ **优雅降级**：SDK 失败自动回退到 REST API
- 🎯 **零破坏性**：完全兼容现有第三方 API

![alt text](<效果图/多模特对话 官方+第三方调用.png>)
*多模态对话 - 支持官方和第三方 API*

![alt text](<效果图/多图编辑大香蕉 官方+第三方调用.png>)
*多图编辑 - Nano Banana 2 官方+第三方调用*

![alt text](效果图/SORA2文生视频+图生视频（贞贞API.png)
*SORA2 视频生成 - 支持文生视频和图生视频*

### 🚀 2025-11-21 更新

**Nano Banana 2 节点发布！**
- 🍌 Google 多模态图像生成
- 🎨 文生图 + 多图编辑
- 🎭 13种专业模板
![alt text](效果图/gemini3对话.png)
![alt text](效果图/image.png)
🚀 豆包4.0多图组合
![alt text](效果图/01.png)
🚀 豆包4.0文生图
![alt text](效果图/02.png)
🚀 其他功能（提示词润色 反推 大语言润色等）
![alt text](效果图/005.png)

🚀 豆包4.0视频反推
![alt text](效果图/豆包视频反推.png)
🚀 全系功能演示在示意工作流里面，节点安装后在examples文件夹


## 🚀 快速开始

### 环境要求

- **ComfyUI**：已安装并能正常运行
- **Python**：3.8 或更高版本
- **依赖库**：requests、zhipuai（自动安装）

### 安装方法

#### 方法一：ComfyUI Manager（推荐）

1. 打开 ComfyUI Manager
2. 搜索 "dapaoAPI"
3. 点击安装
4. 重启 ComfyUI

#### 方法二：Git 克隆

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/paolaoshi/ComfyUI-dapaoAPI.git
cd ComfyUI-dapaoAPI
pip install -r requirements.txt
```

---

## 📦 节点列表

### 🆕 通用节点（v1.1.0 新增）

| 节点名称 | 功能描述 | 核心特性 | 适用场景 |
|---------|---------|---------|---------||
| **🌐 通用API调用（测试）** | 支持任意HTTP API调用 | • 自动适配官方/第三方API<br>• 支持多模态输入<br>• 智能SDK切换<br>• 完整错误处理 | • OpenAI API<br>• Claude API<br>• Gemini 官方API<br>• 任意第三方API |
| **🎨 通用图像编辑API** | 专为图像生成优化 | • 多图编辑支持<br>• 智能放大功能<br>• 官方SDK集成<br>• 多种端点适配 | • Gemini 图像生成<br>• Nano Banana 2<br>• 图像编辑API |
| **🎬 SORA2视频生成** | OpenAI SORA2视频生成 | • 文生视频+图生视频<br>• 多图输入（最多4张）<br>• 异步任务轮询<br>• 进度实时显示 | • 文本生成视频<br>• 图像转视频<br>• 创意视频制作 |

### 🎯 专用节点

| 节点名称 | 功能描述 | 核心特性 | 文档链接 |
|---------|---------|---------|---------|
| **Seedream 4.0 文生图** | 文本生成高质量图像 | 多风格预设、批量生成、种子控制 | [📖 使用说明](docs/1-Seedream文生图使用说明.md) |
| **Seedream 4.0 多图编辑** | 强大的多图编辑工具 | 8种编辑模式、最多8图输入、智能混合 | [📖 使用说明](docs/2-Seedream多图编辑使用说明.md) |
| **GLM 图像反推** | 图像内容智能分析 | 多图联合分析、多种输出格式 | [📖 使用说明](docs/3-GLM图像反推使用说明.md) |
| **GLM 提示词润色** | 提示词智能优化 | 3种预设方案、自定义指令 | [📖 使用说明](docs/4-GLM提示词润色使用说明.md) |
| **豆包 LLM 对话** | 字节跳动大语言模型 | 快速响应、通用对话 | [📖 使用说明](docs/5-豆包LLM对话使用说明.md) |
| **豆包图像反推** | 豆包 Vision 图像分析 | 多图联合分析、英文提示词生成 | [📖 使用说明](docs/7-豆包图像反推使用说明.md) |
| **智谱 LLM 对话** | 智谱 AI 大语言模型 | 深度中文理解、专业内容 | [📖 使用说明](docs/6-智谱LLM对话使用说明.md) |
| **豆包视频反推** | 豆包 Vision 视频内容分析 | VIDEO/图像批次双输入、4种模板、中英文切换 | [📖 使用说明](docs/8-豆包视频反推使用说明.md) |
| **🍌 Nano Banana 2** | Google 多模态图像生成 | 文生图+多图编辑、13种模板、专业控制 | [📖 使用说明](docs/banana2_usage.md) |
| **💎 Gemini 3 多功能** | Google Gemini 3 多模态 | LLM对话+图像反推+视频批次分析+音频分析、T8第三方API | [📖 使用说明](docs/gemini3_usage.md) |
| **🎬 Gemini 3 视频音频** | Gemini 3 视频音频分析 | 真实视频文件上传+音频文件上传+混合分析、File API | [📖 使用说明](docs/gemini3_video_audio_guide.md) |

## 🌐 通用 API 节点使用指南

### 🎯 节点特点

**🌐 通用API调用（测试）节点** 是一个强大的通用接口，可以调用任何符合标准的 HTTP API。

#### ✨ 核心优势

1. **智能适配**
   - 自动检测 Gemini 官方 API
   - 优先使用官方 SDK（更稳定、更快）
   - SDK 失败自动回退到 REST API

2. **多模态支持**
   - 📸 最多 4 张图像输入
   - 🎬 视频输入（自动采样关键帧）
   - 🎵 音频输入
   - 💬 文本对话

3. **灵活配置**
   - 自定义 API 地址
   - 自定义请求头和参数
   - 超时时间控制（默认 180 秒）
   - 响应数据提取

### 📝 配置示例

#### 示例 1：Gemini 官方 API

```
🎯 系统角色: 你是一个专业的图像分析师
💬 用户输入: 请分析这张图片的内容
🤖 模型名称: gemini-2.0-flash-exp
🌐 API地址: https://generativelanguage.googleapis.com
🔑 API密钥: 你的 Gemini API Key
📡 请求方法: POST
🔐 密钥位置: Header
📝 密钥字段名: x-goog-api-key
⏱️ 超时时间: 180
```

#### 示例 2：第三方 API（Nano Banana 2）

```
💬 用户输入: 让女正对镜头，人物一致性保持不变
🤖 模型名称: nano-banana-2
� API地址: https://api.gptbest.vip/v1/chat/completions
🔑 API密钥: 你的 API Key
📡 请求方法: POST
🔐 密钥位置: Header
📝 密钥字段名: Authorization
⏱️ 超时时间: 180
```

#### 示例 3：OpenAI API

```
🎯 系统角色: 你是一个有帮助的助手
💬 用户输入: 请分析这个内容
🤖 模型名称: gpt-4-vision-preview
🌐 API地址: https://api.openai.com/v1/chat/completions
🔑 API密钥: sk-xxx
📡 请求方法: POST
🔐 密钥位置: Header
📝 密钥字段名: Authorization
```

### 🎨 图像编辑节点使用

**🎨 通用图像编辑API** 节点专为图像生成和编辑优化：

#### 核心功能
- 🖼️ 多图输入（最多 4 张）
- 🎯 智能提示词构建
- 📐 宽高比控制
- 🎨 画质和风格预设
- 🔍 AI 智能放大
- 🌐 官方 API 自动适配

#### 配置示例

```
🎨 提示词: 让女正对镜头，保持人物特征
🤖 模型名称: gemini-3-pro-image-preview
🌐 API地址: https://generativelanguage.googleapis.com
🔑 API密钥: 你的 API Key
📝 密钥字段名: x-goog-api-key
📐 宽高比: 3:4
🎨 画质预设: hd
🎭 风格预设: natural
```

### 💡 使用技巧

1. **Gemini 官方 API**
   - API 地址只需填域名：`https://generativelanguage.googleapis.com`
   - 模型名称可以简写：`gemini-2.0-flash-exp`（自动转换为 `models/gemini-2.0-flash-exp`）
   - 密钥字段名：`x-goog-api-key`

2. **第三方 API**
   - 需要填写完整端点：`https://api.gptbest.vip/v1/chat/completions`
   - 密钥字段名通常是：`Authorization`
   - 会自动添加 `Bearer` 前缀

3. **超时设置**
   - 图像生成建议：180 秒
   - 文本对话建议：60 秒
   - 复杂任务建议：300 秒

---

## 🎬 SORA2 视频生成节点使用指南

### 🎯 节点特点

**🎬 SORA2视频生成（贞贞API）** 是基于 OpenAI SORA2 的视频生成节点，支持文生视频和图生视频。

#### ✨ 核心功能

1. **文生视频（T2V）**
   - 📝 纯文本描述生成视频
   - 🎨 支持详细的场景描述
   - ⏱️ 10/15/25 秒时长可选

2. **图生视频（I2V）**
   - 🖼️ 最多 4 张图像输入
   - 🎭 保持图像风格和内容
   - 🔄 图像序列转视频

3. **智能控制**
   - 🤖 sora-2 / sora-2-pro 模型选择
   - 📐 16:9 / 9:16 宽高比
   - 🎬 高清模式（仅 sora-2-pro）
   - 🎰 种子控制（可重现结果）
   - 🔐 隐私模式

### 📝 参数说明

#### 必填参数

| 参数 | 说明 | 选项 |
|------|------|------|
| 🎨 提示词 | 视频内容描述 | 多行文本 |
| 🤖 模型选择 | SORA2 模型 | sora-2 / sora-2-pro |
| 📐 宽高比 | 视频宽高比 | 16:9 / 9:16 |
| ⏱️ 视频时长 | 生成时长（秒） | 10 / 15 / 25 |
| 🎬 高清模式 | 是否启用高清 | true / false |
| 🔑 API密钥 | 贞贞API密钥 | 字符串 |

#### 可选参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| 🖼️ 图像1-4 | 输入图像（最多4张） | 无 |
| 🎰 随机种子 | 种子值（0为随机） | 0 |
| 🔒 生成后控制 | 种子控制方式 | randomize |
| 🔐 隐私模式 | 是否私密生成 | true |

### 🎯 使用示例

#### 示例 1：文生视频

```
🎨 提示词: 女人在天上飞，背景是蓝天白云，镜头缓慢推进
🤖 模型选择: sora-2
📐 宽高比: 16:9
⏱️ 视频时长: 15
🎬 高清模式: false
🔑 API密钥: sk-xxx
```

#### 示例 2：图生视频

```
🎨 提示词: 让图片中的人物动起来，保持人物特征不变
🤖 模型选择: sora-2-pro
📐 宽高比: 9:16
⏱️ 视频时长: 10
🎬 高清模式: false
🔑 API密钥: sk-xxx
🖼️ 图像1: [连接图像节点]
```

#### 示例 3：高清长视频

```
🎨 提示词: 城市夜景延时摄影，车流穿梭，霓虹闪烁
🤖 模型选择: sora-2-pro
📐 宽高比: 16:9
⏱️ 视频时长: 25
🎬 高清模式: false  # 注意：25秒和高清不能同时使用
🔑 API密钥: sk-xxx
```

### ⚠️ 重要提示

1. **模型限制**
   - `sora-2` 不支持 25 秒视频
   - `sora-2` 不支持高清模式
   - 25 秒和高清模式不能同时使用

2. **生成时间**
   - 10 秒视频：约 3-5 分钟
   - 15 秒视频：约 5-8 分钟
   - 25 秒视频：约 8-15 分钟

3. **输出说明**
   - 🎬 视频：VIDEO 类型，可连接保存节点
   - 🎥 视频URL：可直接下载或分享
   - 📋 响应信息：包含任务详情的 JSON

### 💡 提示词技巧

1. **描述要具体**
   ```
   ❌ 不好：一个女人
   ✅ 好：一位穿着白色连衣裙的年轻女性，在阳光下的草地上旋转
   ```

2. **包含镜头运动**
   ```
   - 镜头缓慢推进
   - 镜头环绕拍摄
   - 从上往下俯拍
   - 第一人称视角
   ```

3. **添加环境细节**
   ```
   - 背景是蓝天白云
   - 金色的夕阳光线
   - 柔和的室内灯光
   - 雨后湿润的街道
   ```

---

## 🔑 API 密钥获取

### Seedream 4.0（火山引擎）

1. 访问 [火山引擎控制台](https://console.volcengine.com/ark)
2. 创建 API Key
3. 创建推理端点并获取 Endpoint ID

**文档**：https://www.volcengine.com/docs/82379

### 智谱 AI

1. 访问 [智谱 AI 开放平台](https://open.bigmodel.cn/)
2. 注册并登录
3. 前往 [API Keys 页面](https://open.bigmodel.cn/usercenter/apikeys)
4. 创建并复制 API Key

**文档**：https://open.bigmodel.cn/dev/api

### 豆包（字节跳动）

1. 访问 [火山引擎豆包页面](https://console.volcengine.com/ark)
2. 开通豆包服务
3. 创建 API Key

**文档**：https://www.volcengine.com/docs/82379

### 🍌 Nano Banana 2（第三方API）

1. 联系第三方API服务提供商获取密钥
2. 配置 `banana2_config.json` 文件
3. 或在节点中直接输入API密钥

**支持镜像站**：
- comfly：https://api.gptbest.vip
- hk：https://hk-api.gptbest.vip
- us：https://api.gptbest.vip

**详细文档**：[📖 Nano Banana 2 使用说明](docs/banana2_usage.md)

### 🎬 SORA2 视频生成（贞贞API）

**贞贞 API**：
1. 联系第三方API服务提供商获取密钥
2. 配置 `sora2_config.json` 文件
3. 或在节点参数中直接输入API密钥

**API 地址**：https://ai.t8star.cn

**支持功能**：
- 📝 文生视频（T2V）
- 🖼️ 图生视频（I2V，最多4张图像）
- 🎬 高清模式（sora-2-pro）
- ⏱️ 多种时长（10/15/25秒）

**配置文件示例**：
```json
{
    "api_key": "sk-xxx",
    "base_url": "https://ai.t8star.cn",
    "timeout": 900
}
```

### 💎 Gemini 3 多功能（T8第三方）

**T8 第三方 API**：
1. 联系第三方API服务提供商获取密钥
2. 配置 `gemini3_config.json` 中对应镜像站的 `api_key`
3. 或在节点参数中直接输入API密钥

**支持的镜像站**：
- **comfly**：https://ai.comfly.chat/v1
- **hk**：https://hk-api.gptbest.vip/v1
- **us**：https://api.gptbest.vip/v1

**支持功能**：
- 💬 LLM 对话（纯文本）
- 🖼️ 图像反推（最多4张图像）
- 🎬 视频反推（视频帧分析）
- 🎵 音频分析（音频内容识别）

**支持模型**：
- gemini-3-pro-preview-T8
- gemini-3-flash-T8
- gemini-2.5-flash-T8
- gemini-2.5-pro-T8

**API文档**：https://gpt-best.apifox.cn/doc-6826301

**🆕 v1.0.9 新增特性**：
- ✅ **系统角色定义**：支持自定义 AI 角色和行为方式
- ✅ **用户输入分离**：系统角色和用户输入独立设置
- ✅ **纯 LLM 对话**：不输入媒体时可作为纯文本对话节点
- ✅ **多模态融合**：同时支持文本、图像、视频、音频分析
- ✅ **灵活切换**：一个节点实现对话和多模态分析双重功能

**典型使用场景**：
1. **纯文本对话**：只填写系统角色和用户输入，实现 LLM 对话
2. **图像分析**：添加图像输入，AI 根据系统角色进行专业分析
3. **视频理解**：输入视频，AI 提取关键信息并生成描述
4. **音频识别**：分析音频内容，生成文字描述或总结
5. **多模态混合**：同时输入多种媒体，进行综合分析


#### 模型选择

| 模型 | 特点 | 推荐场景 |
|------|------|----------|
| **GLM-4.5-Flash** ⭐ | 速度最快，性价比高 | 日常使用 |
| **GLM-4-Plus** | 能力最强，深度理解 | 专业需求 |
| **GLM-4-Air** | 平衡版本 | 通用场景 |
| **GLM-4-Flash** | 快速响应 | 实时对话 |

#### 典型应用
- 学术论文写作
- 深度问题解答
- 数据分析报告
- 教学辅导
- 专业内容生成

[📖 查看完整文档](docs/6-智谱LLM对话使用说明.md)

---

## 🎨 统一界面主题

所有节点采用统一的紫色主题，易于识别和使用：

- 🎨 **标题栏颜色**：紫色（#631E77）
- 🎨 **节点背景**：橙棕色（#773508）
- 📁 **节点分类**：🤖dapaoAPI
- 💡 **设计理念**：简洁、优雅、专业

---

## 📝 更新日志

### v1.1.0 (2025-11-24) 🎉
**🚀 通用 API 节点 + SORA2 视频生成重大更新**

#### 新增节点
- ✨ **🌐 通用API调用（测试）**：支持任意 HTTP API 调用
  - 自动适配 Gemini 官方 API
  - 支持多模态输入（图像、视频、音频）
  - 智能 SDK 切换和回退
  - 完整的错误处理和日志
  - 默认超时时间调整为 180 秒
  
- ✨ **🎨 通用图像编辑API**：专为图像生成优化
  - 多图编辑支持（最多 4 张）
  - 官方 Gemini SDK 集成
  - 智能放大功能
  - 完整的参数控制

- ✨ **🎬 SORA2视频生成（贞贞API）**：OpenAI SORA2 视频生成
  - 文生视频（T2V）和图生视频（I2V）
  - 多图输入支持（最多 4 张）
  - sora-2 / sora-2-pro 模型选择
  - 10/15/25 秒时长可选
  - 高清模式支持（仅 sora-2-pro）
  - 异步任务轮询，实时进度显示
  - VIDEO 类型输出，可直接连接保存节点

#### 核心特性
- 🔄 **智能适配**：自动识别并优化 Gemini 官方 API 调用
- 🛡️ **优雅降级**：SDK 失败自动回退到 REST API
- 🎯 **零破坏性**：完全兼容现有第三方 API
- 📝 **模型名称规范化**：自动转换为正确格式
- 🌐 **通用兼容**：支持 OpenAI、Claude、Gemini 等所有标准 API
- 🎬 **视频生成**：完整的 SORA2 视频生成工作流

#### 技术改进
- 优化 API 调用逻辑
- 增强错误处理机制
- 完善调试日志输出
- 新增 ComflyVideoAdapter 视频适配器
- 更新文档和示例

### v1.0.9 (2025-11-21)
**🆕 Gemini 3 多功能节点重大更新**
- ✨ 新增系统角色定义功能，支持自定义 AI 行为
- ✨ 用户输入与系统角色分离，更灵活的对话控制
- ✨ 支持纯 LLM 对话模式（无需媒体输入）
- ✨ 新增音频分析功能，支持音频内容识别
- ✨ 一个节点实现对话和多模态分析双重功能
- 🔧 优化 API 调用逻辑，提升稳定性
- 📚 完善文档和使用说明

### v1.0.8 (2025-11-20)
**🍌 Nano Banana 2 节点发布**
- ✨ 新增 Google Nano Banana 2 多模态图像生成节点
- ✨ 支持文生图和多图编辑功能
- ✨ 13种专业编辑模板
- ✨ 完整的中文界面和 emoji 图标
- 📚 详细的使用文档

### v1.0.7 及更早版本
- 豆包系列节点（文生图、多图编辑、LLM对话、图像反推、视频反推）
- GLM 系列节点（图像反推、提示词润色、LLM对话）
- 智谱 LLM 对话节点

---

## 🙏 致谢

感谢以下服务提供商：
- [火山引擎](https://www.volcengine.com/) - Seedream 4.0 & 豆包
- [智谱AI](https://open.bigmodel.cn/) - GLM-4 系列模型
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) - 优秀的节点化AI工作流框架

---

## 📞 联系方式

- **作者**：@炮老师的小课堂
- **版本**：v1.1.0
- **更新日期**：2025-11-24
- **作者微信**：paolaoshiAICG
- **GitHub**：https://github.com/paolaoshi/ComfyUI-dapaoAPI

![alt text](效果图/123.png)
---

## 🌟 支持项目

如果这个项目对您有帮助，请给个 ⭐ Star！

有任何问题或建议，欢迎提交 Issue 或 PR。

---

<div align="center">

**Happy Creating with dapaoAPI! 🎨✨**

</div>
