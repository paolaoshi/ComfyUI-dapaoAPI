# 便当格 / 模块化信息图模板

本文件用于生成"便当格 / Bento grid / 高密度模块化"信息图：

- 小红书"高密度信息大图"（避坑指南 / 完全攻略 / 多维测评）
- 公众号 / Notion 式知识卡片
- 产品功能 overview 图
- 多维度测评 / 多 SKU 对比一图流
- 年终总结 / 季度回顾的仪表盘

特征：

- 由 6-9 个尺寸不一的矩形模块组成（像 Apple iOS widget 排布）
- 每个模块独立承载一个信息单元（一组数据 / 一个截图 / 一个要点）
- 大模块作视觉锚点，小模块补充细节
- 模块内圆角统一、留白节制、信息密度高
- 整体配色统一，用色块区分模块功能

## 适用范围

- 高密度知识 / 干货 / 攻略图
- 多模块产品介绍图
- 多维测评图
- 年度 / 季度 review 图
- Notion / 仪表盘式视觉

## 何时使用

- 用户提到 "bento / 便当格 / widget / 模块化 / 高密度信息大图 / 一图流 / 干货图 / Notion 风"
- 用户希望"一张图说清楚多个维度"
- 用户希望视觉像 Apple Newsroom / iOS widget / Notion dashboard

不要使用：

- 用户要的是单一主体的信息图（用 `infographics/legend-heavy-infographic.md`）
- 用户要的是手绘 / 笔记本风（用 `infographics/hand-drawn-infographic.md`）
- 用户要的是步骤流程（用 `infographics/step-by-step-infographic.md`）
- 用户要的是技术架构图（用 `technical-diagrams/system-architecture.md`）

## 缺失信息优先提问顺序

1. 主题（一句话能说清的，比如"2026 年最值得入手的 8 款国产相机"）
2. 模块数（6 / 8 / 9，建议 8）
3. 主标题 + 副标
4. 配色基调（极简黑白 / 莫兰迪 / Apple 浅灰 / 暗色科技 / 暖系）
5. 比例（小红书 3:4 / 公众号 16:9 / 1:1）
6. 是否需要"主推荐 / TOP 1"那个特别强调的大模块

## 主模板：便当格高密度信息图

📖 描述

一张图被划分为 6-9 个尺寸不一的圆角矩形模块，整体像 iOS widget 屏幕排布，每个模块承载一个独立信息单元。

📝 提示词

```json
{
  "type": "便当格 / Bento grid 高密度模块化信息图",
  "goal": "生成一张'像 Apple newsroom / iOS widget / Notion dashboard'的多模块信息图，一图说清多个维度",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"3:4 portrait\"}",
    "background": "{argument name=\"background\" default=\"warm off-white #F5F2EC\"}",
    "global_corner_radius": "{argument name=\"global_corner_radius\" default=\"24px\"}",
    "module_gap": "{argument name=\"module_gap\" default=\"16px\"}"
  },
  "header": {
    "main_title": "{argument name=\"main_title\" default=\"2026 年最值得入手的 8 款国产相机\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"全画幅 / APS-C / 视频向 / 复古相机一站式选\"}",
    "title_position": "top-left, large bold sans-serif"
  },
  "palette": {
    "primary": "{argument name=\"primary\" default=\"deep ink #1A1A1A\"}",
    "accent": "{argument name=\"accent\" default=\"vermilion #E94B3C\"}",
    "module_tints": [
      "soft sand #EBE3D5",
      "muted sage #C7D3C0",
      "dusty blue #B4C5D6",
      "warm peach #F2D4C4"
    ],
    "rule": "module backgrounds rotate among the tints; primary used for text; accent used at most twice"
  },
  "layout": {
    "style": "{argument name=\"layout_style\" default=\"asymmetric bento\"}",
    "module_count": "{argument name=\"module_count\" default=\"8\"}",
    "grid": "irregular: 1 hero module (large, 2x2 footprint) + 4-7 supporting modules of mixed 1x1 / 1x2 / 2x1 sizes",
    "alignment": "all modules share the same corner radius and gap; module edges align to an invisible grid"
  },
  "modules": [
    {
      "id": "M1-hero",
      "size": "large (2x2)",
      "role": "TOP 1 / 主推荐",
      "content": "封面级展示：大图 + 推荐理由 + ★★★★★ 评分 + 简要 spec"
    },
    {
      "id": "M2",
      "size": "medium (1x2)",
      "role": "对比维度 1",
      "content": "比如「重量对比」：bar chart + 数字标注 + 冠军那一项高亮"
    },
    {
      "id": "M3",
      "size": "small (1x1)",
      "role": "关键数字",
      "content": "一个超大数字 + 简短说明，比如「8 台」「¥4,999 起」"
    },
    {
      "id": "M4",
      "size": "small (1x1)",
      "role": "图标说明",
      "content": "一组 4-6 个简洁图标 + 极短标签（如「适用场景」）"
    },
    {
      "id": "M5",
      "size": "medium (2x1)",
      "role": "排行榜 / 列表",
      "content": "TOP 3 文字列表，前面带 1/2/3 大数字 badge"
    },
    {
      "id": "M6",
      "size": "small (1x1)",
      "role": "引用 / 卖点",
      "content": "一句金句 / kol 引用 + 引号装饰"
    },
    {
      "id": "M7",
      "size": "medium (1x2)",
      "role": "细节展示",
      "content": "产品特写局部 + 1-2 个 callout 标签"
    },
    {
      "id": "M8",
      "size": "small (1x1)",
      "role": "Footer / 提示",
      "content": "「滑到下一页 →」/ 二维码 / 来源标注"
    }
  ],
  "module_internal_style": {
    "padding": "16-24px inside each module",
    "typography": "sans-serif (Inter / Helvetica Neue / 思源黑); module title in bold, body smaller",
    "rule": "each module is self-contained and could stand alone",
    "imagery": "small product photos / icons / micro-charts; never let a module become pure text"
  },
  "constraints": {
    "must_keep": [
      "所有模块统一圆角",
      "模块间留固定 gap",
      "每个模块都有自己的 micro-title",
      "至少有 1 个模块包含视觉化数据（chart / 大数字）",
      "整图配色不超过 5 种主色"
    ],
    "avoid": [
      "所有模块尺寸一模一样（变成网格表）",
      "模块紧贴没有留白",
      "模块内信息密度过低（变成空 widget）",
      "模块边框使用粗描边 (>2px)",
      "用渐变 / 玻璃质感模糊 bento 的极简感"
    ]
  }
}
```

### 参数策略

- **必问**：`main_title`、`module_count`
- **可默认**：`aspect_ratio`（3:4）、`palette`（warm off-white + vermilion 强调）、`global_corner_radius`、`module_gap`
- **可随机**：`module_tints` 的具体顺序、每个模块的具体内容（如果用户没指定，自动按主题推断）

### 自动补全策略

- 用户只给主题时：自动决定 8 个模块、推断模块角色（TOP 1 / 关键数字 / 图标 / 排行 / 卖点 / 细节 / footer）
- 用户说"小红书风" → palette 选 warm off-white + 暖强调色，aspect 3:4
- 用户说"科技 / 数码风" → palette 选深灰 + 霓虹强调，aspect 1:1 或 3:4
- 用户说"金融 / 严肃" → palette 选 mono + 单一深色强调，aspect 16:9

## 变体 1：iOS widget 屏风格

```json
{
  "modify": {
    "background": "iOS 系统壁纸渐变（深蓝紫 → 黑）",
    "module_backgrounds": "frosted glass + 浅描边",
    "module_corner_radius": "32px (更圆)",
    "typography": "SF Pro Display + SF Symbols 风格图标",
    "vibe": "像截了 iPhone 主屏然后所有 widget 都装满信息"
  }
}
```

适用：数码 / 应用推荐 / 产品介绍。

## 变体 2：Notion dashboard 风

```json
{
  "modify": {
    "background": "纯白 #FFFFFF",
    "module_backgrounds": "极淡灰 #F7F6F3 + 1px 浅灰边框",
    "module_corner_radius": "8px (方正)",
    "module_padding": "更大",
    "typography": "Inter / Söhne, 极细字重为主",
    "vibe": "极简、低调、像 Notion 页面截图"
  }
}
```

适用：知识管理、生产力、SaaS 工具介绍。

## 变体 3：高密度小红书"避坑指南"风

```json
{
  "modify": {
    "module_count": "9-12",
    "background": "warm cream + 颗粒纸质感",
    "module_tints": ["mint", "peach", "lavender", "lemon"],
    "accent": "tomato red 用作「⚠️ 避坑」标签",
    "typography": "稍微加点圆体 / 手写字增加亲切感",
    "vibe": "信息塞满、颜色更跳、有 emoji / 标签"
  }
}
```

适用：小红书避坑指南、新手攻略、必看清单。

## 避免事项

- 模块尺寸全部一样 → 变成 grid 表格，失去 bento 的"轻重缓急"
- 模块没有 micro-title → 失去"独立信息单元"语义
- 全图都是文字模块 → 失去视觉冲击
- 模块之间没有留白或留白不一致 → 视觉吵
- 配色超过 5 种主色 → 整体感崩
- 强行塞入 hero 模块当装饰但内容空 → 浪费视觉权重
- 模块边框 >2px → 像电子表格不像 bento
