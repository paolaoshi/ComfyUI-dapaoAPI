# KPI 仪表盘式信息图模板

本文件用于生成"KPI / 仪表盘 / 数据回顾"信息图：

- 年度 / 季度 / 月度数据回顾图
- 产品关键指标 overview
- 个人年度复盘（读了多少书 / 跑了多少 km / 看了多少电影）
- 团队业绩看板
- 公司年报关键页
- "X 年我做了什么" 数据可视化总结

特征：

- 大量数字 + 进度条 + 迷你图表 + 图标
- 多个独立的"指标卡"组合
- 主指标用极大字号
- 视觉上像"信息可视化仪表盘"，有数据感

## 适用范围

- 年度 / 季度 / 月度回顾
- 个人复盘 / 数据总结
- 产品 / 业务 KPI 概览
- 公司年报关键页
- 用户 wrapped（Spotify Wrapped 风）

## 何时使用

- 用户提到 "KPI / dashboard / 仪表盘 / 年度回顾 / wrapped / 数据总结 / 复盘"
- 用户希望视觉「数据感强、像 SaaS 后台、像 Wrapped」
- 用户有真实的数字要展示

不要使用：

- 用户要的是「便当格内容多元」（用 `infographics/bento-grid-infographic.md`）
- 用户要的是「严肃出版级数据图表」（用 `academic-figures/publication-chart.md`）
- 用户要的是「商业报告 slide」（用 `slides-and-visual-docs/visual-report-page.md`）
- 用户要的是「品牌识别系统板」（用 `branding-and-packaging/brand-identity-board.md`）

## 缺失信息优先提问顺序

1. 主题 + 时间范围（如"2025 年阅读复盘 / Q3 业务概览 / 月度跑步数据"）
2. 主指标（1-3 个最大的数字，比如「读了 47 本书」「营收 ¥1,200 万」「跑了 612 km」）
3. 次级指标（4-8 个，如「最常读的类型」「最快单圈」「最忙的月份」）
4. 是否要趋势图 / 排行榜 / 占比图（哪些数据天然适合视觉化）
5. 配色（科技深色 / 暖系总结 / Spotify Wrapped 渐变 / 极简白底）
6. 比例（小红书 3:4 / 公众号 16:9 / 1:1）

## 主模板：KPI 仪表盘信息图

📖 描述

整张图被划分为多个指标卡，顶部是「主指标」（极大数字），下方排布次级指标卡（数字 + 进度环 / 迷你 chart / 排行榜 / 趋势线），整体像一份精心设计的数据快照。

📝 提示词

```json
{
  "type": "KPI 仪表盘信息图",
  "goal": "把一组数字以'数据可视化仪表盘'的形式呈现，让读者一眼感知数据规模和分布",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"3:4 portrait\"}",
    "background": "{argument name=\"background\" default=\"deep ink #0F172A 渐变到 #1E293B（暗色模式）\"}",
    "alt_background_light": "warm cream #F8F5EE（如果用户偏好亮色）"
  },
  "header": {
    "main_title": "{argument name=\"main_title\" default=\"2025 年阅读复盘\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"全年读完 / 在读 / 弃读 一览\"}",
    "period": "{argument name=\"period\" default=\"2025.01 - 2025.12\"}"
  },
  "palette": {
    "primary_text": "{argument name=\"primary_text\" default=\"#F1F5F9\"}",
    "accent_main": "{argument name=\"accent_main\" default=\"cyan #22D3EE\"}",
    "accent_secondary": "{argument name=\"accent_secondary\" default=\"violet #A78BFA\"}",
    "accent_alert": "{argument name=\"accent_alert\" default=\"rose #FB7185\"}",
    "rule": "限制 4 主色，accent 用于'高亮关键数字'"
  },
  "hero_metrics": {
    "count": "{argument name=\"hero_count\" default=\"3\"}",
    "rule": "顶部 1-3 个'主指标'卡，每个用超大数字 + 简短标签 + 同比变化箭头",
    "examples": [
      { "value": "47", "label": "本书读完", "delta": "↑ +12 vs 2024" },
      { "value": "23,140", "label": "总页数", "delta": "↑ +28%" },
      { "value": "8.2", "label": "平均评分", "delta": "↓ -0.1" }
    ]
  },
  "sub_metrics": {
    "count": "{argument name=\"sub_count\" default=\"6\"}",
    "card_types_to_use": [
      "progress_ring  — 圆环进度图，中央数字 + 标签（适合「目标完成度 78%」）",
      "bar_mini       — 迷你横向 bar，多 entity 排行（适合「TOP 5 读得最多的类型」）",
      "trend_line     — 迷你折线，沿时间趋势（适合「每月阅读数趋势」）",
      "donut_split    — 占比饼图，2-4 段（适合「电子书 vs 纸质书 比例」）",
      "big_number_card — 单个大数字 + 标签（适合「最快读完一本：3 天」）",
      "ranked_list    — 编号列表，3-5 项（适合「TOP 3 评分最高的书」）"
    ],
    "rule": "每张卡都有: 卡片标题（小） + 主视觉（chart） + 简短数据备注（≤1 行）",
    "examples": [
      { "type": "ranked_list", "title": "TOP 3 评分最高", "items": ["《...》 9.5", "《...》 9.3", "《...》 9.1"] },
      { "type": "donut_split", "title": "纸质 vs 电子", "values": "60% / 40%" },
      { "type": "trend_line", "title": "月度阅读量", "delta": "高峰：8 月 7 本" },
      { "type": "progress_ring", "title": "年度目标", "value": "94%（47/50）" },
      { "type": "bar_mini", "title": "TOP 5 类型", "items": "科普 / 小说 / 历史 / 经管 / 哲学" },
      { "type": "big_number_card", "title": "最快读完一本", "value": "3 天" }
    ]
  },
  "layout": {
    "structure": "顶部 hero_metrics 横排 → 中部 sub_metrics 网格（2 列 × 3 行 或 3 列 × 2 行） → 底部 footer 横条",
    "card_styling": "圆角 16-24px，半透明深色填充 + 1px 浅边框，内填充充足，文字层级清晰"
  },
  "footer": {
    "tagline": "{argument name=\"footer_tagline\" default=\"明年继续 📚\"}",
    "credit": "{argument name=\"credit\" default=\"@your_handle · made with gpt-image-2\"}"
  },
  "constraints": {
    "must_keep": [
      "数字必须真实可读（字号大、对比强）",
      "每张卡都有'数据视觉化'，不能纯文字",
      "颜色对应明确：accent_main 用于关键数字，alert 只用于负向 / 异常",
      "卡片之间留固定 gap，圆角统一",
      "至少有 1 张卡用 trend_line 或 progress_ring（带'变化'感）"
    ],
    "avoid": [
      "数字太小读不清",
      "卡片内只有文字（失去仪表盘感）",
      "颜色超过 5 种（不像 dashboard 像彩虹）",
      "图表精度伪装真实数据（如假冒精确坐标）→ 标明这是 illustrative",
      "把 dashboard 做成纯表格",
      "字体使用 Comic Sans / 手写体（数据感丢失）"
    ]
  }
}
```

### 参数策略

- **必问**：`hero_metrics`（至少 1 个主指标的具体数字 + 标签）、`sub_metrics` 数量、配色偏好（暗 / 亮）
- **可默认**：`aspect_ratio`（3:4）、`palette`（cyan + violet 暗色）、卡片圆角 / 间距
- **可随机**：每张 sub 卡选哪种 chart 类型（如果用户没指定）

### 自动补全策略

- 用户只给主题和几个数字 → 自动补全合理的卡片类型组合，确保至少 1 个 trend、1 个 ranked_list、1 个 progress_ring
- 用户说"Spotify Wrapped 风" → 切换到 vivid 渐变背景（粉紫橙），字体更大胆
- 用户说"年报严肃版" → 切换到亮色背景 + mono palette，字体改 Inter，去掉 emoji
- 用户说"个人复盘" → 加 footer credit，用暖色 accent，可加可爱 emoji

## 变体 1：Spotify Wrapped 风

```json
{
  "type": "Wrapped 风 KPI 仪表盘",
  "modify": {
    "background": "vivid 渐变（紫红 → 蓝紫 → 橙）",
    "typography": "extreme bold display font, slogan-style",
    "hero_metrics": "数字超大占满屏宽，每页只放 1 个主指标",
    "vibe": "像音乐播放器年度总结，有节奏感、强情绪"
  }
}
```

适用：年度个人总结、品牌 wrapped 活动、社交平台年终图。

## 变体 2：商业 / 业务 dashboard 严肃版

```json
{
  "type": "商业业务 KPI dashboard 信息图",
  "modify": {
    "background": "纯白 #FFFFFF 或极浅灰 #F8FAFC",
    "palette": "primary text 深灰 #0F172A，accent 单一深蓝 #1E40AF",
    "typography": "Inter / Söhne, 极克制",
    "vibe": "投资人 deck / 年报 / 季报"
  }
}
```

适用：公司年报、季度业务回顾、投资人简报。

## 变体 3：复古 / Newspaper 风数据回顾

```json
{
  "type": "复古报纸风 KPI 信息图",
  "modify": {
    "background": "warm aged paper",
    "palette": "黑 + 红 + 米色 三色",
    "typography": "serif title (Playfair / Bodoni) + monospace 数字",
    "vibe": "像 The Economist / Wall Street Journal 数据特辑页"
  }
}
```

适用：媒体年度数据特辑、复古风格内容、严肃读者向。

## 避免事项

- 数据全是文字 → 失去 dashboard 视觉化的意义
- 卡片之间没有 gap → 看不出独立性
- 颜色超过 5 种主色 → 像彩虹板不像 dashboard
- 用 Comic Sans 等手写感字体 → 数据可信度直接归零
- 假装精确（虚构 X 轴 Y 轴标尺真值）→ 误导
- 卡片内信息空荡（一个大数字+一个标签就完了）→ 留白过度
- 没有 hero metric（每个卡同等大小）→ 失去视觉重心
