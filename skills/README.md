# dapaoAI API Skill 目录与安装规范

API Skill 加载器优先扫描本目录，并兼容同级 `ComfyUI-llama_Dapao/skills/`；相同 Skill ID 以本目录版本为准。加载器支持手动上传文件夹或 ZIP，ZIP 会在校验后自动解压。已存在的同名 Skill 不会被覆盖。

## 标准单 Skill 结构

每个 Skill 使用独立英文 ID 文件夹，并至少包含 `SKILL.md`。本项目也兼容优先读取 `SKILL.cn.md`：

```text
skills/
└─ example-skill/
   ├─ SKILL.md
   ├─ SKILL.cn.md          # 可选；存在时优先读取
   ├─ meta.yaml            # 可选；项目中文显示信息
   ├─ agents/
   │  └─ openai.yaml       # 可选；标准UI显示信息
   ├─ references/          # 可选；按需载入的文字资料
   ├─ scripts/             # 可选；执行脚本
   └─ assets/              # 可选；模板、字体和媒体素材
```

`SKILL.md` 必须以 YAML frontmatter 开头：

```markdown
---
name: example-skill
description: 说明该Skill做什么，以及什么用户请求应触发它。
---

# Example Skill

这里写执行说明。
```

规则：

- `name` 必须使用小写字母、数字和连字符，最长64字符；目录名应与 `name` 一致。
- `description` 必须同时说明能力和适用场景。
- 不要把安装说明、更新日志等无关资料塞入 Skill；长资料放入 `references/`。
- `references/` 中的 `.md/.txt/.yaml/.yml/.json` 会被按需读取，不会在每轮全部加载。
- Skill内部效果由 `SKILL.md` 和资源决定；加载器显示别名不会修改这些文件。

## 中文显示名称

推荐在 `meta.yaml` 中提供：

```yaml
display-name-zh: 示例技能
name: example-skill
summary-cn: 用一句话说明该Skill的用途。
```

显示名解析顺序为：用户手动/AI别名 → `meta.yaml` 中文名 → `SKILL.md` 中文元数据 → `agents/openai.yaml` → 文档首个真实 H1 → `name` → 目录 ID。代码块中的 `# 注释` 不会被识别成标题。

手动名称优先于AI名称。别名保存在 `data/skill_display_names.json`，该文件不会提交到 Git；恢复默认只删除别名，不改 Skill。

## 完整仓库包

也支持保留完整仓库结构：

```text
skills/
└─ example-repository/
   ├─ scripts/
   ├─ data/
   └─ skills/
      ├─ skill-a/SKILL.md
      └─ skill-b/SKILL.md
```

加载器会识别 `仓库目录/skills/*`，上传时保留仓库根目录，避免 Skill 脚本或数据相对路径失效。

## 上传安全规则

- ZIP最大128MB；文件夹或解压后内容最大512MB、最多5000个文件。
- 禁止绝对路径、`..` 路径穿越、符号链接和重复路径。
- 自动忽略 `.git`、`node_modules`、`__pycache__`、`__MACOSX` 等非运行资料。
- 安装前统一验证所有 Skill；任一项失败则整批取消。
- 同名目录发生冲突时整批取消，不执行覆盖或合并。
- 上传和安装只复制文件，不执行包内脚本。
