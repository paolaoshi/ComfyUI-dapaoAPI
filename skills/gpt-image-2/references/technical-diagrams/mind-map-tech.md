# 技术主题思维导图模板

> ⚠️ **本模板生成的是位图（PNG）**，不是 XMind / MindNode / mermaid mindmap 可编辑思维导图。
> 需要可编辑请用 XMind / MindNode / Excalidraw / mermaid mindmap。

本文件用于生成"工程感技术主题思维导图"：

- 技术栈梳理（前端 / 后端 / 数据 / DevOps 全景）
- 面试知识点脑图（八股文 / 系统设计 / 算法）
- 调研脑图（某领域调研后的总结）
- 学习路线图
- 主题词典 / 概念关系图

特征：

- 中央节点 = 主题（圆角矩形 / 椭圆，带强调色）
- 一级分支 = 主类别（4-8 个，放射状分布）
- 二级 / 三级分支 = 子主题（缩进式或嵌套）
- 不同分支用不同颜色（角色编码）
- 暗色 grid + 等宽字体（沿用视觉系统）

## 适用范围

- 技术栈全景图
- 面试准备脑图
- 调研 / 学习总结脑图
- 知识体系梳理
- 概念关系网

## 何时使用

- 用户提到 "思维导图 / mind map / 脑图 / 知识体系 / 学习路线 / 技术栈梳理"
- 用户希望「中央 + 放射」标准 mind map 结构
- 用户接受位图

不要使用：

- 用户要的是「工程系统架构」 → 用 `technical-diagrams/system-architecture.md`
- 用户要的是「ER 数据模型」 → 用 `technical-diagrams/er-diagram.md`
- 用户要的是「层级流程图 / step-by-step」 → 用 `infographics/step-by-step-infographic.md`
- 用户要的是「大纲 / 列表式 slide」 → 用 `slides-and-visual-docs/`

## 缺失信息优先提问顺序

1. 主题（中心节点的内容，"前端工程师技术栈 2026 / 系统设计面试要点"）
2. 一级分支数（建议 4-8 个）
3. 每个一级分支下的子节点（每个一级 3-7 个二级）
4. 是否需要三级 / 四级嵌套
5. 比例（默认 16:9 横版；分支多时可 3:4 竖版）
6. 是否高亮某些"重点 / 必会"节点

## 主模板：标准放射式技术思维导图

📖 描述

整张图中央是主题节点，四周放射出 4-8 条主分支，每条主分支再展开 3-7 个子节点，必要时再展开三级节点。每条主分支用一种颜色家族贯穿其所有子节点。

📝 提示词

```json
{
  "type": "工程感技术思维导图（放射式 mind map）",
  "goal": "生成一张放射式思维导图，作为知识梳理 / 面试准备 / 学习路线 / 技术栈全景的可视化",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"16:9\"}",
    "background": "deep slate #0F172A with subtle 1px grid #1E293B at 32px spacing",
    "outer_padding": "60px"
  },
  "title_strip": {
    "title": "{argument name=\"title\" default=\"Frontend Engineer Tech Stack\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"2026 edition\"}",
    "position": "top-left, JetBrains Mono / SF Mono, light gray"
  },
  "central_node": {
    "label": "{argument name=\"central_label\" default=\"Frontend\\nEngineer\"}",
    "shape": "rounded rectangle (corner radius 16px) or ellipse",
    "size": "260×120px",
    "fill": "amber #FBBF24 × 18% opacity",
    "border": "2px solid amber #FBBF24",
    "label_style": "mono bold 16pt, centered, light text",
    "position": "image center"
  },
  "primary_branches": {
    "count": "{argument name=\"primary_count\" default=\"6\"}",
    "items": [
      { "id": "B1", "label": "Languages", "color": "cyan #22D3EE", "angle_position": "top-left" },
      { "id": "B2", "label": "Frameworks", "color": "blue #60A5FA", "angle_position": "top-right" },
      { "id": "B3", "label": "State & Data", "color": "emerald #34D399", "angle_position": "right" },
      { "id": "B4", "label": "Build & Tooling", "color": "violet #A78BFA", "angle_position": "bottom-right" },
      { "id": "B5", "label": "Testing", "color": "rose #FB7185", "angle_position": "bottom-left" },
      { "id": "B6", "label": "Performance", "color": "orange #FB923C", "angle_position": "left" }
    ],
    "branch_node_style": {
      "shape": "rounded rectangle (corner radius 10px)",
      "size": "180×56px",
      "fill": "branch color × 14% opacity",
      "border": "1.5px solid branch color",
      "label": "mono bold 13pt, centered, light text",
      "position": "evenly distributed around central node, ~ radius 380-440px"
    },
    "connector_style": "thick branch-colored line 2px from central node to primary node, slight curve"
  },
  "secondary_nodes": {
    "rule": "每个 primary 下挂 3-7 个 secondary，沿主分支方向呈树枝状展开",
    "items_per_primary_example": {
      "B1_Languages": ["TypeScript", "JavaScript (ES2024+)", "WebAssembly", "CSS / Sass"],
      "B2_Frameworks": ["React 19", "Next.js 15", "Vue 3", "Svelte 5", "Solid"],
      "B3_State_Data": ["TanStack Query", "Zustand", "Jotai", "URQL / Apollo", "tRPC"],
      "B4_Build_Tooling": ["Vite", "Turbopack", "Bun", "pnpm + Turborepo", "Biome"],
      "B5_Testing": ["Vitest", "Playwright", "Storybook", "MSW"],
      "B6_Performance": ["Core Web Vitals", "RUM", "Bundle analysis", "Image / Font opt"]
    },
    "secondary_node_style": {
      "shape": "rounded rectangle (corner radius 8px)",
      "size": "auto-fit text + 12px padding, ~ 140×40px typical",
      "fill": "branch color × 8% opacity",
      "border": "1.2px solid branch color (slightly desaturated)",
      "label": "mono regular 11pt"
    },
    "connector_style": "thin branch-colored line 1.2px from primary to secondary, curved"
  },
  "tertiary_nodes": {
    "enabled": "{argument name=\"tertiary_enabled\" default=\"false\"}",
    "rule": "if true, secondary 可继续展开 2-3 个 tertiary（更小的圆角矩形 + 更细的连线），但要避免视觉爆炸；建议只在 1-2 个 secondary 下展开"
  },
  "highlights": {
    "must_know": {
      "enabled": "{argument name=\"must_know_enabled\" default=\"false\"}",
      "rule": "if true, 给重点 / 必会节点加'★'前缀 + 描边加粗到 2.5px",
      "examples": ["★ React 19", "★ TypeScript", "★ Vite"]
    }
  },
  "legend": {
    "enabled": true,
    "position": "bottom-right",
    "content": "branch color → category mapping，star → must-know",
    "style": "small panel, semi-transparent bg, mono 10pt"
  },
  "constraints": {
    "must_keep": [
      "central node 唯一且居中",
      "primary branches 围绕中央均匀分布（避免一边密一边空）",
      "每条分支颜色家族贯穿其所有子节点",
      "secondary 节点严格挂在对应 primary 的延伸方向",
      "暗色 grid 背景 + 等宽字体",
      "节点大小有 hierarchy（central > primary > secondary > tertiary）",
      "连线不交叉（除非不可避免）"
    ],
    "avoid": [
      "所有节点同尺寸 → 失去层级",
      "primary 集中在一侧 → 视觉失衡",
      "secondary 颜色与所属 primary 不一致",
      "连线大量交叉 → 可读性崩溃",
      "用 emoji 当节点图标（除非主题需要）",
      "primary > 8 个（拥挤；考虑分子图）",
      "三级以下嵌套全开 → 视觉爆炸",
      "用 3D / 渐变 / 玻璃质感",
      "声称这是可编辑 SVG"
    ]
  }
}
```

### 参数策略

- **必问**：`title`、`central_label`、primary 分支列表（含名称）、每条 primary 下的 secondary 列表
- **可默认**：`background`（暗色 grid）、`primary_branches.color`（默认 6 色组合）、`tertiary_enabled`（false）、`must_know_enabled`（false）
- **可随机**：每条 primary 的 angle_position（基于数量自动等距分布）、节点轻微微调避免重叠

### 自动补全策略

- 用户给"主题 + 4-6 个分支" → 自动用 default secondary 数量（每分支 4 个）
- 用户给"我要前端技术栈脑图" → 用 default 6 分支（Languages / Frameworks / State&Data / Build / Testing / Performance）
- 用户没指定颜色 → 自动按角色顺序分配 6 色组合
- 用户说"加重点标记" → 启用 `must_know_enabled`
- 用户说要 light 模式 → 用变体 1

## 变体 1：浅色 Light 思维导图

```json
{
  "modify": {
    "background": "warm off-white #F8FAFC + faint grid #E2E8F0",
    "node_fill": "branch color × 6% opacity",
    "node_border": "1.5px solid (deeper shade for white bg)",
    "label_color": "deep slate #0F172A",
    "connector_color": "branch color (deeper shade)",
    "vibe": "白底文档站 / 印刷友好"
  }
}
```

## 变体 2：层级树形图（左到右）

```json
{
  "modify": {
    "layout": "替换放射式为'左到右树形'：central node 在最左，primary 垂直排列在右侧第二列，secondary 在第三列，以此类推",
    "use_case": "更适合'学习路线 / 知识层级' (而不是'全景概览')",
    "vibe": "更像 XMind 的 logical chart 视图"
  }
}
```

适用：学习路线、知识层级、决策树形知识。

## 变体 3：组织 / 团队结构脑图

```json
{
  "modify": {
    "central_label": "team / company / org name",
    "primary_branches": "部门 / 职能 (Engineering / Design / Product / Ops / Marketing)",
    "secondary_nodes": "具体角色 / 团队成员 (用 'Name · Title' 格式)",
    "highlights_extra": "team lead 用 ★ 标记 + 边框加粗",
    "use_case": "团队介绍 deck、组织架构图"
  }
}
```

适用：团队 / 组织架构展示、新人 onboarding 文档。

## 避免事项

- primary 分支集中在画布一侧 → 视觉失衡
- 节点全部同尺寸 → 失去层级
- 连线大量交叉 → 不可读
- secondary 颜色与所属 primary 不一致 → 视觉混乱
- 三级以下全展开 → 视觉爆炸
- 用 emoji 当节点 icon（除非主题相关，如"美食脑图"）
- primary > 8 个 → 拥挤，考虑拆分主题
- 用 3D / 渐变 / 玻璃质感
- 中央节点不在中心 / 不唯一
- 把"系统架构 / ER 图"做成 mind map（语义错位）
- 字号过小 / mono 字体丢失（破坏工程感）
