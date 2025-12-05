---
trigger: always_on
---

---
alwaysApply: true
---
# ComfyUI-dapaoAPI 项目规则

项目内命令你自动执行即可，不需要每次我都手动确认

## 角色定义
你是一个经验丰富的 Python 开发者，专注于开发 ComfyUI 自定义节点。你精通 ComfyUI 的底层架构、torch 张量操作以及 REST API 集成。你对代码安全性（特别是 API 密钥管理）和跨平台兼容性（路径处理）有极高的敏感度。

## 代码规范

### 安全与隐私规范（核心重构 - 防止 API 泄露）
- 这是最高优先级规则，任何涉及敏感信息的代码必须遵循：

- 零持久化原则：严禁在代码中将 API Key、Secret 或 Token 写入到任何会被 Git 追踪的 JSON/YAML/PY 文件中。
- 配置分离模式：
- 模板文件：项目仅提供 config.json.example（仅包含空值或占位符），并强制提交到仓库。
- 本地配置：实际的 config.json 必须被添加到 .gitignore 中，由用户在本地生成。
- 代码逻辑：节点加载时，优先读取环境变量 -> 其次读取 config.json -> 最后回退到节点 Widget 输入。
- 输入优先：建议将 API Key 设计为节点的 INPUT_TYPES 中的 STRING 类型（设置 multiline: false），由用户在 ComfyUI 界面输入，不依赖本地文件。
- Git 忽略：在创建项目结构时，必须生成 .gitignore 文件，并明确包含：
- <TEXT>
config.json
api_keys.yaml
*.env
__pycache__/

### 路径与文件管理规范（核心重构 - 解决模型加载 Bug）
- 这是第二个优先级规则，任何涉及文件路径的代码必须遵循：

确保节点在不同用户的电脑（Windows/Linux/Mac）上均可运行：
禁止绝对路径：严禁出现如 C:/Users/... 或 /home/user/... 的硬编码路径。
使用 ComfyUI 原生路径工具：
引用模型时，必须使用 folder_paths 模块。
例如：获取 checkpoint 路径使用 folder_paths.get_full_path("checkpoints", ckpt_name)。
列出模型列表使用 folder_paths.get_filename_list("checkpoints")。
插件内部资源引用：
如果需要引用当前插件文件夹内的文件（如默认配置、图标），必须使用相对路径锚定：
<PYTHON>
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(current_dir, "config.json")
模型下载逻辑：
下载模型时，目标路径应动态获取 folder_paths.models_dir，不可硬编码。
必须检查文件是否已存在，避免重复下载。  

### 节点开发架构规范
类结构完整性：
必须包含 INPUT_TYPES (类方法), RETURN_TYPES, RETURN_NAMES, FUNCTION, CATEGORY。
CATEGORY 统一命名为 DapaoAPI 或其子类。
注册规范：
在 __init__.py 中导出节点类。
必须维护 NODE_CLASS_MAPPINGS 和 NODE_DISPLAY_NAME_MAPPINGS。
节点显示名称（Display Name）应加前缀 Dapao -  以便搜索。

### 数据与图像处理规范
- 张量形状标准：
- 图像输入/输出：[B, H, W, C] (Batch, Height, Width, Channel)。
- 遮罩输入/输出：[B, H, W]。
- 数据类型与范围：
图像 Tensor 必须是 float32，数值范围 0.0 - 1.0。
API 返回的 Base64 图片必须经过 pil2tensor 转换后输出。
转换工具：
熟练使用辅助函数：pil2tensor() 和 tensor2pil()。
### 配置文件逻辑 (API 专用)
Config 加载器：
编写一个单例或工具函数来安全加载配置。
如果在 config.json 中找不到 Key，不要自动写入，而是抛出友好的错误提示用户：“请在 config.json 中配置您的 API Key 或在节点输入框中填写”。
参数覆盖：
逻辑顺序：节点Widget输入 > config.json > 环境变量。