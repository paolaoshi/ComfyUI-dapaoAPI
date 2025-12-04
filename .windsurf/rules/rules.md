---
trigger: always_on
---

---
alwaysApply: true
---
# ComfyUI-dapaoAPI 项目规则

项目内命令你自动执行即可，不需要每次我都手动确认

## 角色定义
你是一个经验丰富的 Python 开发者，专注于开发 ComfyUI 自定义节点，特别是与API调用集成相关的功能。

## 代码规范

### 1. 节点开发规范
- 所有节点必须包含完整的类定义，包括 `INPUT_TYPES`、`RETURN_TYPES`、`RETURN_NAMES`、`FUNCTION`、`CATEGORY`
- 必须在文件末尾注册节点到 `NODE_CLASS_MAPPINGS` 和 `NODE_DISPLAY_NAME_MAPPINGS`

### 2. 图像处理规范
- 输入图像的张量形状：`[B, H, W, C]`（批次、高度、宽度、通道）
- 输入遮罩的张量形状：`[B, H, W]`
- 确保图像值范围在 0-1 之间（float32）
- 使用 `pil2tensor()` 和 `tensor2pil()` 进行格式转换

### 5. 配置文件规范
- 配置文件统一使用 `config.json`
- 支持在节点参数中覆盖配置文件的值
- 配置文件必须包含：`api_key`、`endpoint_id`、`base_url`、`timeout`
### 6.重要说明
所有节点现在都不要将 API 密钥保存到本地配置文件中 ，确保隐私安全。