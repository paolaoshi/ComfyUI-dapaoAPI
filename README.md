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
## 效果演示
🚀 2025-11-21更新！增加Nano Banana 2的支持！
增加gemini3智能对话以及多模态反推等新功能
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
| **💎 Gemini 3 多功能** | Google Gemini 3 多模态 | LLM对话+图像反推+视频反推+音频分析、T8第三方API | 🆕 新增 |

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
- **版本**：v1.0.9
- **更新日期**：2025-11-21
- **作者微信**：paolaoshiAICG

![alt text](效果图/123.png)
---

## 🌟 支持项目

如果这个项目对您有帮助，请给个 ⭐ Star！

有任何问题或建议，欢迎提交 Issue 或 PR。

---

<div align="center">

**Happy Creating with dapaoAPI! 🎨✨**

</div>
