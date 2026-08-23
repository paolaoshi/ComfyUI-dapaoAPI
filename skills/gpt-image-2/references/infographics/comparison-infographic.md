# 对比信息图模板

本文件用于生成"二元 / 多元对比"信息图：

- A vs B 双栏对比（产品 / 概念 / 方法）
- 三方对比（如三种方案 / 三档套餐）
- 多维度评测对比（多产品 × 多维度）
- 优劣 / 利弊 / 正反对比
- "传统做法 vs 新做法"科普图
- 价格档位对比图

特征：

- 视觉上左右 / 多列分栏，对齐严格
- 每列有清晰的列首（角色 / 名称 / 大图）
- 每行是一个对比维度
- 用 ✓ ✗ 颜色 评分等手段做明显区分
- 一眼能看出"谁赢"

## 适用范围

- 产品 vs 产品对比图
- 方法 / 方案 / 流派对比图
- 套餐档位对比图
- 优劣 / 利弊对比图
- "误区 vs 正解"科普

## 何时使用

- 用户提到 "对比 / 比较 / vs / pk / 优劣 / 利弊 / 双栏 / 多列对比 / 套餐 / 档位"
- 用户希望"读者一眼分清谁更适合自己"
- 用户希望视觉上有"对决感 / 选择感"

不要使用：

- 用户要的是「步骤 / 流程」（用 `infographics/step-by-step-infographic.md`）
- 用户要的是「便当格高密度信息」（用 `infographics/bento-grid-infographic.md`）
- 用户要的是「Slide 单页讲解」（用 `slides-and-visual-docs/`）
- 用户要的是「真正的工程对比表 / 配置表」纯表格图（用 `academic-figures/qualitative-comparison-grid.md`）

## 缺失信息优先提问顺序

1. 对比对象数量（2 / 3 / 4）
2. 每个对象的名称
3. 对比维度数量（建议 4-7 个维度，比如：价格、性能、易用性、扩展性、生态、学习曲线）
4. 每个维度下每个对象的具体差异
5. 是否要明显「胜出标记」（皇冠 / TOP 1 标签）
6. 配色基调（中性 / 暖色 / 科技 / 黑白）
7. 比例（小红书 3:4 / 公众号 16:9 / 1:1）

## 主模板：双列对比信息图

📖 描述

整张图分为左右两列，列首是两个被对比的对象（带 logo / 头像 / 大图），下面 4-7 行对比维度，每行用图标 + 短文字 + 颜色 / ✓✗ 表达差异，底部一句话结论。

📝 提示词

```json
{
  "type": "双列对比信息图",
  "goal": "生成一张让读者一眼分清「谁更适合自己」的对比图",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"3:4 portrait\"}",
    "background": "{argument name=\"background\" default=\"warm off-white #F8F6F2\"}",
    "split_line": "{argument name=\"split_line\" default=\"中央一条细分割线 / 或一个交错的对决符号 'VS'\"}"
  },
  "header": {
    "main_title": "{argument name=\"main_title\" default=\"React vs Vue 选谁？2026 实战对比\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"7 个维度帮你拍板\"}"
  },
  "columns": [
    {
      "id": "left",
      "name": "{argument name=\"left_name\" default=\"React\"}",
      "color_theme": "{argument name=\"left_color\" default=\"cyan #61DAFB + 深灰\"}",
      "header_visual": "{argument name=\"left_visual\" default=\"React logo (大尺寸 + 浅色底卡片)\"}",
      "tagline": "{argument name=\"left_tagline\" default=\"灵活、生态强、社区大\"}"
    },
    {
      "id": "right",
      "name": "{argument name=\"right_name\" default=\"Vue\"}",
      "color_theme": "{argument name=\"right_color\" default=\"emerald #41B883 + 深灰\"}",
      "header_visual": "{argument name=\"right_visual\" default=\"Vue logo (大尺寸 + 浅色底卡片)\"}",
      "tagline": "{argument name=\"right_tagline\" default=\"上手快、文档好、约定多\"}"
    }
  ],
  "comparison_rows": {
    "count": "{argument name=\"row_count\" default=\"7\"}",
    "structure": "每一行：左侧维度图标 + 维度名（居中）→ 左列表现 + 右列表现，右侧用色块 / ✓✗ / 1-5 星标记",
    "items": [
      "学习曲线",
      "上手速度",
      "生态成熟度",
      "招聘市场",
      "性能表现",
      "TypeScript 体验",
      "适合的项目类型"
    ],
    "marker_style": "{argument name=\"marker_style\" default=\"5 星评分 + 颜色对比\"}",
    "highlight_winner_per_row": true
  },
  "footer": {
    "verdict": "{argument name=\"verdict\" default=\"看团队偏好：要快上手选 Vue，要长期生态选 React\"}",
    "winner_badge": {
      "enabled": "{argument name=\"winner_badge_enabled\" default=\"false\"}",
      "label": "{argument name=\"winner_badge_label\" default=\"Editor's Choice\"}",
      "position": "left | right"
    }
  },
  "constraints": {
    "must_keep": [
      "左右列宽度对称",
      "每行高度对齐",
      "维度名居中（属于"中柱"），左右各表现各的",
      "颜色不要让一边明显压另一边（除非显式 winner）",
      "字体一致",
      "数据 / 评分有视觉化标记，不要纯文字"
    ],
    "avoid": [
      "左右列尺寸不对称",
      "维度行没有图标",
      "颜色冲突让人分不清哪边是哪边",
      "对比维度只有 1-2 个（信息密度太低）",
      "对比维度 > 10 个（每行变得太挤）",
      "结论太主观（最好客观一句话总结）"
    ]
  }
}
```

### 参数策略

- **必问**：`left_name`、`right_name`、`row_count`（或具体维度列表）
- **可默认**：`background`、`marker_style`（5 星）、`color_theme`（基于品牌色 / 默认色）
- **可随机**：维度图标具体造型、`split_line` 是细线还是 VS 符号

### 自动补全策略

- 用户只给两个对象时（如"React vs Vue"）：自动推断 7 个常见对比维度
- 用户只给主题（如"对比 React 和 Vue"）：补全名称、tagline、色彩主题（用品牌色）
- 用户没说 winner：默认不放 winner badge，结论写中立
- 用户说"我要明显的对决感" → 加 VS 符号 + winner badge + 更对比的色彩

## 变体 1：三列对比（套餐档位 / 三方案）

```json
{
  "type": "三列档位对比信息图",
  "columns_count": 3,
  "column_examples": ["Free", "Pro", "Enterprise"],
  "rule": "中间列稍宽 + 底色稍亮 + 加 'Most Popular' 角标，行 = 功能维度 + ✓ ✗ 量化指标"
}
```

适用：SaaS 定价页、套餐对比、会员等级对比。

## 变体 2：误区 vs 正解（科普向）

```json
{
  "type": "误区 vs 正解 二栏对比",
  "left_column": {
    "label": "❌ 常见误区",
    "color": "muted red / gray",
    "items": "3-5 个常见错误说法"
  },
  "right_column": {
    "label": "✅ 正确做法",
    "color": "muted green / fresh",
    "items": "3-5 条正确说法 + 简单解释"
  },
  "vibe": "教育 / 科普 / 健康 / 育儿向"
}
```

适用：健康科普、育儿误区、消费避坑、健身误区。

## 变体 3：多产品 × 多维度评测矩阵（横向）

```json
{
  "type": "多列横向评测矩阵",
  "layout": "顶行 = 多个产品（4-6 个），左列 = 评测维度（5-8 行），格内 = 评分 / ✓✗ / 简短文字",
  "highlight_rule": "每一行最高分用颜色高亮 + 每列底部统计冠军次数",
  "vibe": "媒体测评图、消费报告"
}
```

适用：相机评测、笔记本评测、APP 横评、SUV 横评。

## 避免事项

- 双列宽度不对称（视觉偏向感 → 显失公允）
- 行高不一致 → 看不齐对比项
- 没有维度图标 → 行与行难以区分
- 颜色完全相同 → 失去左右区分
- 颜色对比过强（一边鲜红一边鲜绿）→ 像情绪化判决
- 评分只有 1 / 0 表达 → 没有梯度感（建议 1-5 星 / 圆点 / 进度条）
- 没有结论 footer → 读者不知道你想推哪个
- 把对比图做成纯文字表格 → 失去信息图的"一眼可读"
