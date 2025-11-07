# ✅ dapaoAPI 发布前检查清单

使用这个清单确保每次发布都万无一失！

---

## 📋 发布前检查（必做）

### 代码质量
- [ ] 所有节点功能测试通过
- [ ] 没有明显的 bug 或错误
- [ ] 代码注释完整清晰
- [ ] 删除了调试代码和 print 语句

### 文档完整性
- [ ] `README.md` 内容准确无误
- [ ] 版本号已更新到最新
- [ ] 更新日志已添加本次更新内容
- [ ] 所有节点都有使用说明文档

### 版本管理
- [ ] `pyproject.toml` 版本号已更新
- [ ] `__init__.py` 版本号已更新（如有）
- [ ] 版本号遵循语义化版本规范（x.y.z）

### 安全检查
- [ ] 确认 `.gitignore` 包含配置文件
- [ ] `config.json` 中没有真实 API 密钥
- [ ] `glm_config.json` 中没有真实 API 密钥
- [ ] `doubao_config.json` 中没有真实 API 密钥
- [ ] 示例配置文件（`.example.json`）已创建

### 依赖管理
- [ ] `requirements.txt` 包含所有必需依赖
- [ ] 依赖版本号指定清晰
- [ ] 没有未使用的依赖

### GitHub 配置
- [ ] `.github/workflows/publish.yml` 配置正确
- [ ] GitHub Secrets 中的 `REGISTRY_ACCESS_TOKEN` 有效
- [ ] 远程仓库地址正确

---

## 🚀 发布步骤

### 1. 更新版本号
```bash
# 编辑 pyproject.toml
version = "3.1.2"  # 修改为新版本
```

### 2. 提交更改
```bash
git add .
git commit -m "Release: v3.1.2 - 更新说明"
```

### 3. 打标签（推荐）
```bash
git tag -a v3.1.2 -m "Version 3.1.2"
```

### 4. 推送到 GitHub
```bash
git push origin master
git push origin v3.1.2
```

### 5. 验证发布
- [ ] 检查 GitHub Actions 运行状态
- [ ] 确认发布成功（绿色✅）
- [ ] 在 ComfyUI Manager 中搜索节点
- [ ] 测试安装流程

---

## 📊 版本号更新指南

| 更新类型 | 示例 | 说明 |
|---------|------|------|
| **Bug 修复** | 3.1.1 → 3.1.2 | 修复已知问题，不改变功能 |
| **新功能** | 3.1.2 → 3.2.0 | 添加新功能，向下兼容 |
| **破坏性更新** | 3.2.0 → 4.0.0 | API 变化，不向下兼容 |

---

## 🔍 发布后验证

### 1. GitHub 验证
- [ ] 仓库首页显示正确
- [ ] README 正常显示
- [ ] 标签已创建
- [ ] Actions 运行成功

### 2. ComfyUI Registry 验证
- [ ] 节点可以搜索到
- [ ] 版本号正确
- [ ] 描述信息完整
- [ ] 安装测试通过

### 3. 功能测试
- [ ] 全新安装测试
- [ ] 所有节点加载正常
- [ ] 基本功能运行正常
- [ ] API 调用成功

---

## ❌ 常见错误预防

### 错误 1：版本号忘记更新
- ✅ 解决：发布前双重检查 `pyproject.toml`

### 错误 2：配置文件被提交
- ✅ 解决：检查 `.gitignore` 和 `git status`

### 错误 3：文档链接失效
- ✅ 解决：逐个点击 README 中的链接

### 错误 4：依赖缺失
- ✅ 解决：在干净环境中测试 `pip install -r requirements.txt`

### 错误 5：Token 过期
- ✅ 解决：定期更新 GitHub Secrets 中的 Token

---

## 📞 紧急回滚

如果发布后发现严重问题，立即回滚：

```bash
# 1. 删除远程标签
git push origin :refs/tags/v3.1.2

# 2. 删除本地标签
git tag -d v3.1.2

# 3. 回滚提交
git revert HEAD
git push origin master

# 4. 修复问题后重新发布
```

---

## 📝 本次发布信息

**版本号**：v________

**发布日期**：20__年__月__日

**主要更新**：
- 
- 
- 

**测试人员**：________

**发布人员**：________

---

**作者**：@炮老师的小课堂  
**更新日期**：2024年

