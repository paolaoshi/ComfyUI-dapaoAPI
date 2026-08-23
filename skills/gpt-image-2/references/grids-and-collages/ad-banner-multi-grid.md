# 跨行业混合广告 Banner 网格模板

本文件用于生成"一张图里 N 个独立广告 banner、彼此行业 / 主题 / 风格完全不同"的拼合视觉。

典型用途：

- 广告 / 设计 agency 能力 demo 板（一次秀 4 个不同业务方向的成品）
- 公众号 / 投流素材集合预览
- 「AI 能做哪些 banner」自我演示
- 海外日式 / 韩式 SNS banner 拼图（旅游 / 美妆 / 餐饮 / 教育混合）
- 模板库 / 素材集主图

特征（与现有 `banner-grid-2x2.md` 的区别）：

| 维度 | `banner-grid-2x2.md`（已有） | 本模板（新增） |
|---|---|---|
| 主题统一性 | 同品牌系列、风格统一 | **每格行业 / 主题 / 配色完全不同** |
| 视觉一致性 | 共享品牌色与 logo | 仅共享网格 + 留白节奏 |
| 用途 | 课程 / SNS 投放四件套 | agency demo / 拼图素材集 / 多场景示意 |

## 适用范围

- 4 / 6 / 9 格独立广告 banner 拼图
- 多行业演示板（旅游 / 美妆 / 餐饮 / 教育 / 金融 / 数码…）
- 多平台投流素材一图预览
- 设计师能力作品集主图

## 何时使用

- 用户提到"四种不同行业 banner / 多主题广告组 / 各做一张"
- 用户希望"一张图涵盖 N 个完全不同主题的 banner"
- 用户在做 agency 提案 / 模板示例图

不要使用：

- 同品牌 4 张延展 banner → 用 `grids-and-collages/banner-grid-2x2.md`
- 一张完整大 banner → 用 `poster-and-campaigns/banner-hero.md`
- 风格混合的同主体演绎 → 用 `grids-and-collages/mixed-style-multi-panel.md`
- 同一业务多日内容（lookbook / 时间表）→ 用 `grids-and-collages/lookbook-grid.md`

## 缺失信息优先提问顺序

1. 网格规格（2×2 / 2×3 / 3×3）
2. 每格分别什么主题 / 行业（用户给清单还是让你随机）
3. 语言（日 / 中 / 英 / 多语混合）
4. 是否需要可读的真实价格 / 折扣 / 文案
5. 是否需要每格出现"主体人物"或仅产品 / 文字
6. 主体来源：随机生成 / 模特库一致 / 用户给参考

如用户说"你随便写"：保留语言提问，其余主题自动生成 4 个差异度高的行业。

## 主模板：N×M 跨行业广告 banner 演示板

📖 描述

把画布等分为 N×M 格，每格独立构图、主题、字号 hierarchy 都完整，像把 4 张成品 banner 拼到一张图里。

📝 提示词

```json
{
  "type": "{argument name=\"grid spec\" default=\"2x2\"} grid of independent advertisement banners",
  "goal": "生成一张高密度广告 demo 板，每格都是一个独立可裁切的成品 banner，用于展示不同行业的视觉处理能力",
  "language": "{argument name=\"language\" default=\"Japanese\"}",
  "layout": {
    "structure": "{argument name=\"panel count\" default=\"4\"} equal quadrants",
    "gutter": "{argument name=\"gutter\" default=\"6px white divider\"}",
    "overall_aspect_ratio": "{argument name=\"overall ratio\" default=\"1:1\"}",
    "panel_aspect_ratio": "{argument name=\"panel ratio\" default=\"1:1\"}",
    "quadrants": [
      {
        "position": "top-left",
        "theme": "{argument name=\"theme 1\" default=\"Travel\"}",
        "subject": "{argument name=\"subject 1\" default=\"A couple holding hands on a white sand beach with turquoise ocean and bright blue sky\"}",
        "elements": ["{argument name=\"deco 1\" default=\"red hibiscus flower in bottom-left corner\"}"],
        "text_labels": [
          "{argument name=\"text 1a\" default=\"今年こそ、解き放て。\"}",
          "{argument name=\"text 1b\" default=\"沖縄旅行\"}",
          "{argument name=\"text 1c\" default=\"3日間の癒やし旅\"}",
          "{argument name=\"text 1d\" default=\"航空券+ホテル\"}",
          "{argument name=\"price 1\" default=\"39,800円〜\"}",
          "{argument name=\"text 1e\" default=\"絶景、グルメ、体験 ぜんぶ叶う!\"}"
        ],
        "icons": { "count": 3, "descriptions": ["airplane", "hotel building", "car"] },
        "color_palette": "{argument name=\"palette 1\" default=\"sky blue, turquoise, sand cream, accent red\"}"
      },
      {
        "position": "top-right",
        "theme": "{argument name=\"theme 2\" default=\"Skincare\"}",
        "subject": "{argument name=\"subject 2\" default=\"Close-up of a young woman with dewy glowing skin, eyes closed\"}",
        "elements": [
          "{argument name=\"deco 2a\" default=\"soft pink gradient background\"}",
          "{argument name=\"deco 2b\" default=\"dynamic water splash effects\"}",
          "{argument name=\"product 2\" default=\"pink cosmetic jar labeled 'LUMIÈRE Brightening Gel'\"}"
        ],
        "text_labels": [
          "毛穴・くすみ卒業!",
          "透明感あふれる",
          "水光肌へ",
          "新感覚スキンケア",
          "{argument name=\"discount 2\" default=\"初回限定 78%OFF\"}",
          "{argument name=\"price 2\" default=\"1,980円\"}"
        ],
        "badges": { "count": 3, "style": "gold circular", "labels": ["毛穴ケア", "高保湿", "ハリ・ツヤ"] },
        "color_palette": "blush pink, ivory, soft gold accent"
      },
      {
        "position": "bottom-left",
        "theme": "{argument name=\"theme 3\" default=\"Gourmet Food\"}",
        "subject": "{argument name=\"subject 3\" default=\"Thick medium-rare steak sizzling on a dark grill plate\"}",
        "elements": ["garlic chips", "rosemary sprig", "dark background with smoke and glowing embers"],
        "text_labels": [
          "とろける旨さ!",
          "{argument name=\"food 3\" default=\"黒毛和牛\"}",
          "贅沢ステーキ",
          "期間限定 / 特別価格",
          "{argument name=\"original price 3\" default=\"通常価格 8,980円\"}",
          "{argument name=\"sale price 3\" default=\"4,980円\"}"
        ],
        "badges": { "count": 1, "style": "red circular", "labels": ["A4 A5等級"] },
        "color_palette": "deep brown, charcoal black, amber, accent crimson"
      },
      {
        "position": "bottom-right",
        "theme": "{argument name=\"theme 4\" default=\"Online Education\"}",
        "subject": "{argument name=\"subject 4\" default=\"Young man in blue shirt studying at desk, writing in notebook beside open laptop\"}",
        "elements": ["bright indoor lighting", "minimal desk environment"],
        "text_labels": [
          "スキマ時間で",
          "{argument name=\"goal 4\" default=\"最短合格!\"}",
          "オンライン資格講座",
          "スマホで完結",
          "効率学習で差がつく!",
          "{argument name=\"discount 4\" default=\"今だけ! 受講料 20%OFF\"}"
        ],
        "badges": { "count": 1, "style": "blue circular", "labels": ["受講者数 10万人 突破!"] },
        "icons": { "count": 2, "descriptions": ["smartphone", "open book"] },
        "color_palette": "sky blue, white, energetic yellow accent"
      }
    ]
  },
  "global_style": {
    "rendering": "real ad-grade composition per panel; each panel must look like a finished standalone banner",
    "typography": "bold sans-serif headline + smaller subhead per panel; multi-weight hierarchy",
    "layering": "subject photo + clear text overlay + small badge / icon ornaments",
    "lighting": "panel-appropriate (sunny travel, dewy beauty, smoky food, bright office)"
  },
  "constraints": {
    "must_keep": [
      "每格都像独立一张可裁切的成品 banner（不是简单拼贴）",
      "字号 hierarchy 在每格内清晰（headline ≫ subhead ≫ price/CTA）",
      "格与格之间不要互相溢出"
    ],
    "avoid": [
      "所有格子复用同一种配色 / 同一个模特",
      "文字模糊不可读",
      "每格留白比例失衡",
      "把所有 logo / brand 强行写成同一品牌"
    ]
  }
}
```

### 参数策略

- **必问**：grid spec、language、各 theme（或确认随机）
- **可默认**：text_labels（按 theme 自动套话术）、color_palette（按 theme 推荐）
- **可随机**：subject 描述、price 数字、badges 文案

### 自动补全策略

- 用户只说"做 4 张不同行业广告"→ 默认旅游 / 美妆 / 餐饮 / 教育组合（已被 Case 90 验证好用）
- 用户给行业清单但不给文案 → 根据行业语义自动写 headline / price / badge
- 用户指定语言 → 全部 panels 必须统一语言（除非显式说"混合语言"）

## 变体 1：3×3 九格行业全景演示板

📝 提示词

```json
{
  "type": "3x3 grid of advertisement banners across 9 industries",
  "language": "{argument name=\"language\" default=\"Japanese\"}",
  "layout": {
    "structure": "9 equal cells",
    "industries": [
      "Travel", "Skincare", "Gourmet Food",
      "Online Education", "Fashion", "Finance",
      "Mobile Game", "Real Estate", "Healthcare"
    ]
  },
  "per_cell_required_elements": [
    "industry-appropriate hero subject",
    "1 large headline",
    "1 sub-line",
    "1 price or CTA strip",
    "1 small badge or icon row"
  ],
  "global_style": {
    "rendering": "uniform crisp print quality across all 9 cells",
    "color_diversity": "must use 9 visibly different palettes so cells don't blend",
    "negative_space": "each cell ~12% padding"
  }
}
```

### 何时选这个变体

- 用户说"出 9 张完全不同行业 banner"
- 设计师在做万能模板演示页
- 想直接搬到 Behance / Dribbble 作品集封面

## 变体 2：手机端竖向 2×4 投流素材集

📝 提示词

```json
{
  "type": "2x4 vertical mobile ad placement preview",
  "panel_aspect_ratio": "9:16",
  "overall_aspect_ratio": "9:16 collage of 8 mini portrait banners",
  "use_case": "Pinterest / TikTok / Reels / 朋友圈 信息流广告效果预览",
  "per_cell_required_elements": [
    "vertical hero photo or illustration",
    "top-aligned headline",
    "bottom-aligned CTA pill",
    "small brand watermark"
  ],
  "constraints": {
    "must_keep": [
      "竖版构图安全区（顶部 / 底部各留 12% 给平台 UI）",
      "8 个 panel 行业差异明显"
    ]
  }
}
```

### 何时选这个变体

- 用户做投流素材 demo
- 做手机端广告效果预览图
- 给客户展示「同一活动多种行业切角」

## 避免事项

- ❌ 把 4 格强行画成同一个模特（变成 lookbook 而非多行业演示）
- ❌ 全部 panels 共享同一种配色 → 失去"跨行业"的视觉张力
- ❌ 文案过长导致 panel 内 hierarchy 崩塌（headline 应在画面 1/3-1/2 高度内可读）
- ❌ 把模板里的"argument"写到最终 prompt（要先做参数替换或保留 default）
- ❌ 多语混合时不指定哪个 panel 用哪种语言 → 模型会全部混乱
- ❌ panel 数量超过 9 个 → 单张图里每格细节会塌陷，不如分两张
