# 🚀 ComfyUI-dapaoAPI 发布指南

本文档介绍如何将 dapaoAPI 节点发布到 GitHub 和 ComfyUI Registry。

---

## 📋 发布前准备

### 1. 检查文件清单

确保以下文件存在且内容正确：

- ✅ `pyproject.toml` - 项目元数据配置
- ✅ `README.md` - 项目说明文档
- ✅ `LICENSE` - MIT 开源协议
- ✅ `requirements.txt` - Python 依赖
- ✅ `.gitignore` - Git 忽略规则
- ✅ `.github/workflows/publish.yml` - 自动发布配置

### 2. 更新版本号

发布新版本前，需要在 `pyproject.toml` 中更新版本号：

```toml
[project]
version = "3.1.1"  # 修改为新版本号
```

版本号规则（语义化版本）：
- **主版本号（Major）**：不兼容的 API 修改
- **次版本号（Minor）**：向下兼容的功能新增
- **修订号（Patch）**：向下兼容的问题修复

示例：
- `3.1.1` → `3.1.2`（bug修复）
- `3.1.1` → `3.2.0`（新功能）
- `3.1.1` → `4.0.0`（破坏性更新）

### 3. 配置文件安全检查

⚠️ **重要**：确保不要提交真实的 API 密钥！

检查以下配置文件：
- `config.json`
- `glm_config.json`
- `doubao_config.json`

这些文件已在 `.gitignore` 中设置为忽略。

---

## 📦 发布到 GitHub

### 方法一：使用 Git 命令行

#### 1. 初始化 Git 仓库（首次）

```bash
cd E:\Debug\ComfyUI\custom_nodes\ComfyUI-dapaoAPI
git init
git add .
git commit -m "Initial commit: dapaoAPI v3.1.1"
```

#### 2. 关联远程仓库

```bash
# 替换为您的 GitHub 仓库地址
git remote add origin https://github.com/paolaoshi/ComfyUI-dapaoAPI.git
```

#### 3. 推送到 GitHub

```bash
# 首次推送
git branch -M master
git push -u origin master

# 后续推送
git add .
git commit -m "Update: 描述您的更新内容"
git push
```

### 方法二：使用 GitHub Desktop

1. 打开 GitHub Desktop
2. 选择 `File` → `Add Local Repository`
3. 选择项目目录：`E:\Debug\ComfyUI\custom_nodes\ComfyUI-dapaoAPI`
4. 填写提交信息，点击 `Commit to master`
5. 点击 `Publish repository` 或 `Push origin`

---

## 🎯 发布到 ComfyUI Registry

### 前置条件

1. **获取 Registry Access Token**
   - 访问 ComfyUI Registry 网站
   - 登录您的账号
   - 生成 Personal Access Token

2. **配置 GitHub Secrets**
   - 进入 GitHub 仓库页面
   - 点击 `Settings` → `Secrets and variables` → `Actions`
   - 点击 `New repository secret`
   - Name: `REGISTRY_ACCESS_TOKEN`
   - Value: 粘贴您的 Token
   - 点击 `Add secret`

### 发布方式

#### 方式一：自动发布（推荐）

当您修改 `pyproject.toml` 并推送到 GitHub 时，会自动触发发布：

```bash
# 1. 修改版本号
# 编辑 pyproject.toml，更新 version = "3.1.2"

# 2. 提交并推送
git add pyproject.toml
git commit -m "Release: v3.1.2"
git push

# 3. GitHub Actions 会自动发布到 ComfyUI Registry
```

#### 方式二：手动触发

1. 进入 GitHub 仓库页面
2. 点击 `Actions` 标签
3. 选择 `Publish dapaoAPI to Comfy Registry`
4. 点击 `Run workflow`
5. 选择分支（通常是 `master`）
6. 点击 `Run workflow` 按钮

### 查看发布状态

1. 进入 GitHub 仓库的 `Actions` 页面
2. 查看最新的工作流运行记录
3. 绿色✅表示发布成功，红色❌表示发布失败
4. 点击查看详细日志

---

## 📝 发布流程示例

### 完整发布新版本

```bash
# 1. 确保代码最新
git pull

# 2. 修改 pyproject.toml 中的版本号
# version = "3.1.1" → version = "3.1.2"

# 3. 更新 README.md 中的版本号（如有需要）

# 4. 更新 __init__.py 中的版本号（如有需要）

# 5. 提交更改
git add .
git commit -m "Release: v3.1.2 - 修复种子控制问题"

# 6. 打标签（可选但推荐）
git tag -a v3.1.2 -m "Version 3.1.2"

# 7. 推送到 GitHub
git push origin master
git push origin v3.1.2

# 8. GitHub Actions 自动发布到 ComfyUI Registry
# 9. 等待几分钟，检查 Actions 页面确认发布成功
```

---

## ⚠️ 常见问题

### 1. 发布失败：Token 无效

**解决方法**：
- 检查 GitHub Secrets 中的 `REGISTRY_ACCESS_TOKEN` 是否正确
- Token 可能已过期，需要重新生成

### 2. 发布失败：版本冲突

**解决方法**：
- 不能发布相同版本号
- 确保 `pyproject.toml` 中的版本号是新的

### 3. 配置文件被提交

**解决方法**：
```bash
# 从 Git 中移除但保留本地文件
git rm --cached config.json
git rm --cached glm_config.json
git rm --cached doubao_config.json
git commit -m "Remove config files from git"
git push
```

### 4. 推送被拒绝

**解决方法**：
```bash
# 先拉取远程更新
git pull --rebase origin master
# 解决冲突（如有）
# 再推送
git push origin master
```

---

## 📚 相关文档

- [GitHub Actions 文档](https://docs.github.com/en/actions)
- [ComfyUI Registry 文档](https://registry.comfy.org/)
- [语义化版本规范](https://semver.org/lang/zh-CN/)

---

## 🎉 发布成功后

发布成功后，用户可以通过以下方式安装您的节点：

### 通过 ComfyUI Manager 安装
1. 打开 ComfyUI Manager
2. 搜索 "dapaoAPI"
3. 点击安装
4. 重启 ComfyUI

### 通过 Git 克隆安装
```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/paolaoshi/ComfyUI-dapaoAPI.git
cd ComfyUI-dapaoAPI
pip install -r requirements.txt
```

---

**作者**：@炮老师的小课堂  
**版本**：v3.1.1  
**更新日期**：2024年

