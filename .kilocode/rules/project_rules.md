# 🤖dapaoAPI 项目规则

## 1. 节点开发规范

- 所有节点必须包含完整的类定义：`INPUT_TYPES`、`RETURN_TYPES`、`RETURN_NAMES`、`FUNCTION`、`CATEGORY`
- 节点分类统一使用 `CATEGORY = "🤖dapaoAPI"`
- 必须在文件末尾注册节点到 `NODE_CLASS_MAPPINGS` 和 `NODE_DISPLAY_NAME_MAPPINGS`

## 2. 图像处理规范

- 输入图像张量形状：`[B, H, W, C]`（批次、高度、宽度、通道）
- 输入遮罩张量形状：`[B, H, W]`
- 图像值范围：0-1（float32）
- 格式转换：使用 `pil2tensor()` 和 `tensor2pil()`

## 3. 路径与文件管理规范

- 模型路径：严禁使用绝对路径，必须通过 ComfyUI 的 `folder_paths` 模块动态获取
- 资源引用：插件内文件（配置、图标）使用相对路径
- 下载逻辑：目标路径不可硬编码，下载前必须校验文件是否存在

## 4. 安全与隐私（最高优先级）

- 零持久化原则：严禁将 API Key/Token 写入任何 Git 追踪的文件
- 配置分离模式：
  - 仅提交 `config.example.json`（空值模板）
  - 实际 `config.json` 由用户本地生成，强制加入 `.gitignore`
- 读取优先级：环境变量 > 本地 Config > 节点 Widget 输入

## 5. Git 忽略清单

必须在 `.gitignore` 中包含：
```
config.json
api_keys.yaml
*.env
__pycache__/
```
