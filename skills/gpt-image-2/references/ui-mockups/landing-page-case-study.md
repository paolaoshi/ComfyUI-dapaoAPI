# 长页面 Landing Page / Case Study UI 样机模板

本文件用于生成"完整的一整页 SaaS / 营销 / case study 落地页 UI 样机"——把多个 section（hero / strategy / performance / social proof / CTA）从上到下拼到一张超长图里。

典型用途：

- SaaS 产品官网首页 mockup
- 营销 case study 长页面（投后报告 / KPI 复盘）
- 增长 / agency 业务介绍页
- Y Combinator 风格 demo day 项目页
- 客户提案稿 / 投资人 deck 的网页化展示

特征（与现有 UI 模板的区别）：

| 模板 | 视觉范围 | 适用场景 |
|---|---|---|
| `chat-interface-scene.md` | 单屏聊天界面 | iMessage / 微信 / 群聊 |
| `social-interface-mockup.md` | 单屏社交动态详情 | Twitter / 小红书 / 微博 |
| `live-commerce-ui.md` | 单屏直播 UI 叠加 | 抖音 / 淘宝直播 |
| `product-card-overlay.md` | 单屏 hero / 详情主图 | 电商详情页主图 |
| **本模板** | **完整长页面**（5-7 个 section 纵向拼接） | **SaaS / 营销长页面 / case study** |

## 适用范围

- SaaS 落地页 / 产品官网首页
- 营销 case study 长页面
- 增长复盘报告 web 版
- 投资人 / 客户提案的网页样机
- Agency 业务介绍长页面

## 何时使用

- 用户提到"落地页 / landing page / case study / 一整页 / 长页面 / 网站 mockup"
- 用户希望出"从上到下完整 section 结构"而不是单屏截图
- 客户需要看到「hero → 数据 → 时间线 → 社交证明 → CTA」完整营销叙事

不要使用：

- 单屏 UI 截图 → 用 `chat-interface-scene` / `social-interface-mockup` / `live-commerce-ui`
- 仅 hero section → 用 `poster-and-campaigns/banner-hero.md`
- 真实可交互的 HTML 网页 → 应当生成 HTML 代码而非图片

## 缺失信息优先提问顺序

1. 业务类型（SaaS / agency / 课程 / case study / 投后报告）
2. 品牌 / 主标 + 一句话定位
3. 是「营销 case study」（要展示数据 + 客户 logo）还是「产品官网首页」（要展示功能 + 截图）
4. 配色基调（**深色 + 霓虹 / 纯白 + 强色 accent / 浅米色商务 / 玻璃拟态**）
5. 必须出现的核心数据（GMV / 播放量 / 客户数 / 增长率）
6. 是否要客户 logo 墙 / 推荐语 / CTA 表单
7. 比例（**3:4 / 9:16 长截图 / 整张 desktop 截图**）

## 主模板：营销 case study 长页面 mockup

📖 描述

一张超长截图，从上到下 6-7 个独立 section，整体用统一深色 + 霓虹 accent，每个 section 都长得像真实落地页里会出现的模块。

📝 提示词

```json
{
  "type": "UI/UX landing page mockup",
  "goal": "生成一张高仿真的营销 case study 长页面截图，可以作为提案稿、投后报告或作品集封面",
  "theme": "{argument name=\"theme\" default=\"dark mode, sleek modern aesthetic, glassmorphism, neon purple and blue glowing accents\"}",
  "viewport": {
    "width": "{argument name=\"viewport width\" default=\"desktop 1440px width\"}",
    "scroll_capture": "{argument name=\"capture style\" default=\"full-page screenshot, vertical scroll captured into one tall image\"}",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4 portrait long page\"}"
  },
  "header": {
    "logo": "{argument name=\"brand name\" default=\"goViralX\"}",
    "nav_items": ["Home", "Case Studies", "Pricing", "Contact"],
    "top_right_cta": "{argument name=\"top cta\" default=\"Login\"}",
    "top_right_tag": "{argument name=\"top right tag\" default=\"VIRAL CAMPAIGN CASE STUDY\"}"
  },
  "layout": {
    "section_count": 6,
    "section_separation": "subtle horizontal divider, 80-120px vertical breathing room",
    "sections": [
      {
        "name": "Hero",
        "position": "top",
        "headline": "{argument name=\"hero headline\" default=\"How We Created 10M+ Viral Impact\"}",
        "subheadline": "{argument name=\"hero subhead\" default=\"3 天引爆全网, 助力品牌实现指数级增长\"}",
        "stats_row": {
          "count": 4,
          "labels": ["{argument name=\"stat label 1\" default=\"总播放量\"}", "{argument name=\"stat label 2\" default=\"互动率\"}", "{argument name=\"stat label 3\" default=\"转化咨询\"}", "{argument name=\"stat label 4\" default=\"执行周期\"}"],
          "values": ["{argument name=\"stat value 1\" default=\"10,240,000+\"}", "{argument name=\"stat value 2\" default=\"18.7%\"}", "{argument name=\"stat value 3\" default=\"3,200+\"}", "{argument name=\"stat value 4\" default=\"72小时\"}"]
        },
        "visual": "{argument name=\"hero visual\" default=\"cinematic shot of a person in a hoodie looking at glowing digital screens and graphs, large play button overlay\"}"
      },
      {
        "name": "Strategy",
        "title": "{argument name=\"strategy title\" default=\"Our 3-Day Execution Strategy\"}",
        "layout_type": "vertical timeline",
        "steps_count": 3,
        "elements_per_step": ["timeline node circle", "step title", "3 bullet points", "video thumbnail with play button", "description box"],
        "step_titles": ["Day 1: Asset Production", "Day 2: Multi-Platform Launch", "Day 3: Amplification & PR"]
      },
      {
        "name": "Performance",
        "title": "{argument name=\"perf title\" default=\"Data-Driven Performance\"}",
        "left_column": {
          "stat_cards_count": 4,
          "values": ["10M+", "43%", "28,000+", "3,200+"],
          "labels": ["Total Views", "Engagement", "New Followers", "Leads"]
        },
        "right_column": {
          "charts_count": 2,
          "chart_1": "line graph showing 7-day growth peaking at Day 3, x-axis days 1-7, y-axis views, glowing line",
          "chart_2": "horizontal segmented bar chart showing platform distribution (TikTok 52%, Instagram 24%, X 15%, YouTube 9%)"
        }
      },
      {
        "name": "Keys to Success",
        "title": "{argument name=\"keys title\" default=\"The 3 Keys to Viral Success\"}",
        "cards_count": 3,
        "card_elements": ["glowing icon (fire / target / antenna)", "card title", "2-line description", "VIEW DETAIL link with arrow"]
      },
      {
        "name": "Social Proof",
        "title": "{argument name=\"sp title\" default=\"TRUSTED BY CREATORS & BRANDS\"}",
        "left_column": {
          "logos_count": 8,
          "grid": "2x4",
          "brands": ["{argument name=\"logo 1\" default=\"SHEIN\"}", "SHOPLINE", "Blueglass", "instacart", "lemon8", "mi", "CIDER", "bellroy"]
        },
        "right_column": {
          "testimonial_cards_count": 2,
          "elements": ["large quotation mark", "italic quote text", "author avatar circle", "author name + title (e.g. SaaS Founder, Growth Manager)"]
        }
      },
      {
        "name": "Call to Action",
        "title": "{argument name=\"cta title\" default=\"READY TO GO VIRAL?\"}",
        "interactive_elements": [
          "text input field with placeholder '{argument name=\"input placeholder\" default=\"Your work email\"}'",
          "glowing button with text '{argument name=\"call to action text\" default=\"获取专属增长方案 ->\"}'"
        ],
        "visual": "{argument name=\"cta visual\" default=\"3D render of a rocket ship taking off with purple and blue flames\"}"
      }
    ]
  },
  "footer": {
    "logo": "{argument name=\"brand name\" default=\"goViralX\"}",
    "columns": ["Product", "Company", "Resources", "Legal"],
    "social_icons": ["X", "LinkedIn", "YouTube", "Instagram"],
    "copyright": "© 2026 {argument name=\"brand name\" default=\"goViralX\"}. All rights reserved."
  },
  "global_style": {
    "rendering": "production-quality web UI mockup, sharp pixel-perfect typography, realistic component spacing, modern web design",
    "typography": "modern sans-serif (Inter / Space Grotesk feel), strong size hierarchy across sections",
    "color_tone": "{argument name=\"color tone\" default=\"dark navy / charcoal background, neon purple + electric blue accents, white-90% body text\"}",
    "components": "rounded corners 12-16px, soft glassmorphism cards, subtle shadows, accent gradient buttons",
    "browser_chrome": "{argument name=\"chrome\" default=\"none, just the page itself\"}"
  },
  "constraints": {
    "must_keep": [
      "6 个 section 从上到下顺序清晰、可独立识别",
      "每个 section 的内部组件都符合常规网页设计（卡片 / 网格 / 时间线 / chart）",
      "数据可读、字体清晰、对比度足够",
      "整体看起来像真实可滚动的网页截图，而不是 PPT 拼贴"
    ],
    "avoid": [
      "section 之间没有视觉分隔（容易混在一起）",
      "把 chart 画成示意图而非真实数据可视化",
      "logo 墙的品牌名变得不可读",
      "CTA 按钮颜色与全页配色冲突",
      "Hero 占据 80%+ 高度（导致下面 section 被压扁）"
    ]
  }
}
```

### 参数策略

- **必问**：brand name + 业务定位、core data values、配色基调
- **可默认**：nav items、footer columns、stat labels（按业务类型推荐）
- **可随机**：客户 logo 墙的具体品牌（按行业匹配真实存在的品牌名）、推荐语 quote 内容

### 自动补全策略

- 用户只说"营销 case study 落地页"→ 默认深色 + 霓虹方案 + 6 section 标准结构
- 用户给了核心数据（如「3 天 1000 万播放」）→ 自动反推 stat label / chart / strategy timeline
- 用户没说客户 logo → 按行业生成 8 个真实存在的品牌名（不要造假名）

## 变体 1：SaaS 产品官网首页（feature-driven）

📝 提示词

```json
{
  "type": "SaaS product homepage mockup",
  "section_count": 7,
  "sections": [
    "Hero (headline + subhead + CTA + dashboard screenshot)",
    "Logo Strip (8 customer logos)",
    "Feature Grid (3x2 = 6 features with icon + title + description)",
    "How It Works (3-step process)",
    "Product Screenshot Showcase (1 large dashboard image)",
    "Pricing (3 tiers comparison table)",
    "Testimonials + CTA"
  ],
  "theme": "{argument name=\"theme\" default=\"clean white + accent blue, modern startup\"}",
  "must_have": "1 prominent product UI screenshot embedded in Hero, 1 dashboard image in showcase section"
}
```

### 何时选这个变体

- 用户做的是 SaaS 产品官网而非 case study
- 需要展示「产品长什么样」（截图嵌套截图）
- 需要 pricing table

## 变体 2：投资人 / 客户 deck 网页化版

📝 提示词

```json
{
  "type": "investor / client pitch deck rendered as one long landing page",
  "section_count": 8,
  "sections": [
    "Hero (problem statement)",
    "Solution Overview",
    "Market Size (chart)",
    "Product Demo (screenshots)",
    "Traction (key metrics + growth chart)",
    "Team (4 avatars + roles)",
    "Roadmap (4 phases timeline)",
    "Ask + Contact"
  ],
  "theme": "professional, premium, slightly editorial, soft shadow + light grid background",
  "tone": "credible, ambitious, data-backed"
}
```

### 何时选这个变体

- 创业者要做 demo day 提案的网页化版
- 把 Keynote deck 转成可分享的网页样机
- 需要"传统 deck"的所有要素（market / team / ask）

## 变体 3：玻璃拟态 + 渐变（流行 2026 风格）

📝 提示词

```json
{
  "type": "glassmorphism landing page",
  "theme_override": {
    "background": "deep purple-to-pink gradient with floating blur orbs",
    "cards": "frosted glass effect (backdrop-blur 20px), 1px white border at 20% opacity",
    "accents": "neon green and hot pink glow",
    "typography": "ultra-bold sans-serif headlines, very thin weight body"
  },
  "section_count": 5,
  "sections": ["Hero", "Feature Cards 3x", "Stats", "Testimonials", "CTA"],
  "vibe": "Y2K x Apple Vision Pro x Linear.app"
}
```

### 何时选这个变体

- 设计驱动型品牌 / AI 工具 / 创意产品
- 需要在 SNS 引发设计师转发
- 客户希望做「视觉惊艳」而非「企业稳重」

## 避免事项

- ❌ section 之间分隔不清 → 必须有 80-120px 留白 + 颜色 / 背景微差
- ❌ 把图表画成纯装饰（必须看起来像真实数据曲线）
- ❌ logo 墙强行造假品牌名（用真实知名品牌或明确标注「示例」）
- ❌ CTA 按钮颜色和品牌色冲突 → 应该是品牌色的 accent 版本
- ❌ Hero 区域过大压扁后续 section（hero ≤ 35% 总高度）
- ❌ 全页只用一种字号 → 必须有 ≥ 4 级 hierarchy（H1 / H2 / Body / Caption）
- ❌ 把模板里的占位文字（"VIEW DETAIL"）原样保留 → 应根据业务替换成真实文案
- ❌ 输出比例选错（如 1:1 会装不下完整长页面，建议 3:4 / 9:16）
