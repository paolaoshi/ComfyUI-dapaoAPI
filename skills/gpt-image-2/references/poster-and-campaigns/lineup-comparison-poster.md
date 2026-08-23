# 系列产品 / 型号 Lineup 对比信息图海报模板

本文件用于生成"以单一品牌的全产品线 / 全型号 / 全 SKU 为主体，按等级 / 系列 / 类目分行排列，配 legend / icon key / 卖点 chart"的奢华 catalog 风信息图海报。

典型用途：

- 乐器品牌全 lineup 海报（PRS / Fender / Gibson / Boss…）
- 汽车品牌车型谱系海报（Porsche / Audi / Ford…）
- 钟表 / 镜头 / 笔 / 高端硬件品类系列对比
- 收藏家级海报 / 博物馆级品牌致敬图
- 年度 catalog 或 anniversary 海报
- 经销商门店墙面挂图

特征（与现有 poster / infographics 模板的区别）：

| 模板 | 用途 |
|---|---|
| `infographics/comparison-infographic.md`（已有） | A vs B / 套餐档位 / 误区对比（≤ 6 项） |
| `infographics/legend-heavy-infographic.md`（已有） | 高密度科普 / 因果链 / 演化（不强调产品 lineup） |
| **本模板**（新增） | **30+ 个 SKU 同时展示，按 tier × series 矩阵排列，含图例** |

**核心特征**：30-50 张产品 thumbnail 同时出现，靠 tier key + icon legend + tonal chart 让读者一眼看懂"我应该买哪一型"。

## 适用范围

- 单品牌 30+ SKU 的 lineup 致敬海报
- 经销商门店挂图 / 收藏家海报
- 年度 catalog 一图概览
- 周年 / anniversary 纪念海报
- B2B 招商「我们有多少 SKU」展示

## 何时使用

- 用户提到"全 lineup / 全产品谱系 / 全型号 / 收藏家海报 / catalog 一图"
- 单品牌产品数量 ≥ 20
- 用户想强调「品牌历史 / 产品线广 / 选择丰富」

不要使用：

- ≤ 6 个产品的对比 → 用 `infographics/comparison-infographic.md`
- 单产品多角度 → 用 `product-visuals/exploded-view-poster.md`
- 单产品高级影棚图 → 用 `product-visuals/premium-studio-product.md`
- 多品牌混合对比 → 不适用（本模板强调单品牌）

## 缺失信息优先提问顺序

1. 品牌名 + 类目（PRS 吉他 / 保时捷汽车 / 万宝龙钢笔…）
2. 总 SKU 数（20-50 较合适，超过 60 单格塌陷）
3. 分行依据（tier 等级 / series 系列 / 年代 / 价位…）
4. 是否需要 icon key / tonal key / spec key（影响顶部图例数）
5. 配色基调（**dark luxury / 白底 minimal / 复古沙金**）
6. 比例（默认 3:4 竖版）
7. 是否包含品牌签名 / 印章 / seal 装饰

## 主模板：奢华 lineup 对比信息图海报

📖 描述

竖版海报，header（主标 + 副标 + 签名 + 双印章）+ 顶部 3 个 legend key + 中部 6-8 行产品矩阵（按 tier 分行），每行左侧标 tier 名、右侧排 6-7 个产品卡。

📝 提示词

```json
{
  "type": "luxury vintage lineup comparison infographic poster",
  "goal": "生成一张奢华 catalog 风的品牌全产品线对比海报，30+ SKU 同时呈现，配等级 / 图标 / 风格图例",
  "subject": "{argument name=\"subject description\" default=\"a highly detailed, vertically oriented PRS electric guitar lineup chart designed like a premium museum poster or collector's reference board\"}",
  "style": {
    "overall": "{argument name=\"overall style\" default=\"ornate, dark, glossy, high-contrast, gold-foil typography, elegant wood-and-metal textures, symmetrical grid layout, premium catalog aesthetic, subtle vintage patina, ultra sharp graphic design\"}"
  },
  "branding": {
    "main_headline": "{argument name=\"main headline\" default=\"THE LEGENDARY LINEAGE OF PRS GUITARS\"}",
    "subheadline": "{argument name=\"subheadline\" default=\"EVERY ICON. EVERY LINE. ONE HERITAGE.\"}",
    "signature": "{argument name=\"signature\" default=\"Paul Reed Smith\"}",
    "left_seal": "{argument name=\"left seal\" default=\"PAUL REED SMITH GUITARS\"}",
    "right_seal": "{argument name=\"right seal\" default=\"MADE IN MARYLAND U.S.A.\"}"
  },
  "palette": {
    "background": "{argument name=\"background palette\" default=\"black and deep charcoal with dark figured wood accents\"}",
    "primary": "{argument name=\"primary color\" default=\"antique gold\"}",
    "secondary": "{argument name=\"secondary color\" default=\"cream\"}",
    "accent_colors": ["deep green", "teal", "royal blue", "purple", "gold", "burgundy"]
  },
  "layout": {
    "format": "{argument name=\"format\" default=\"single-page vertical poster\"}",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4 portrait\"}",
    "header": {
      "position": "top",
      "elements": [
        "large central title",
        "small tagline below",
        "script signature",
        "2 circular emblems in upper left and upper right",
        "{argument name=\"legend count\" default=\"3\"} horizontal legend boxes under the title"
      ]
    },
    "sections": [
      {
        "title": "{argument name=\"key 1 title\" default=\"PRESTIGE TIER KEY\"}",
        "position": "upper left below title",
        "count": 6,
        "labels": ["{argument name=\"tier 1\" default=\"SE\"}", "{argument name=\"tier 2\" default=\"S2\"}", "{argument name=\"tier 3\" default=\"CE\"}", "{argument name=\"tier 4\" default=\"CORE\"}", "{argument name=\"tier 5\" default=\"WOOD LIBRARY\"}", "{argument name=\"tier 6\" default=\"PRIVATE STOCK\"}"]
      },
      {
        "title": "{argument name=\"key 2 title\" default=\"PICKUP ICON KEY\"}",
        "position": "upper center-right below title",
        "count": 7,
        "labels": ["HH", "HSH", "P-90", "SOAP", "58/15", "TCI", "Bass"]
      },
      {
        "title": "{argument name=\"key 3 title\" default=\"TONAL CHARACTER KEY\"}",
        "position": "upper right below title",
        "count": 7,
        "labels": ["Warm / Vintage", "Balanced / All-around", "Bright / Articulate", "High Gain / Modern", "Blues / Classic Rock", "Metal / Progressive", "Funk / Soul / Clean"]
      },
      {
        "title": "{argument name=\"row 1 label\" default=\"CORE\"}",
        "position": "first main row left label",
        "count": 7,
        "labels": ["{argument name=\"row 1 model 1\" default=\"Custom 24\"}", "McCarty 594", "DGT (David Grissom)", "Custom 22", "Hollowbody II", "SC 594", "row category panel"]
      },
      {
        "title": "{argument name=\"row 2 label\" default=\"S2\"}",
        "position": "second main row left label",
        "count": 6,
        "labels": ["S2 Custom 24", "S2 McCarty 594", "S2 Standard 24", "S2 Vela", "S2 Singlecut", "S2 Mira"]
      },
      {
        "title": "{argument name=\"row 3 label\" default=\"SE\"}",
        "position": "third main row left label",
        "count": 6,
        "labels": ["SE Custom 24", "SE Standard 24", "SE Paul's Guitar", "SE Santana", "SE Hollowbody II", "SE Mark Holcomb"]
      },
      {
        "title": "{argument name=\"row 4 label\" default=\"CE\"}",
        "position": "fourth main row left label",
        "count": 6,
        "labels": ["CE 24", "CE 22", "CE 24 Semi-Hollow", "CE 24 Floyd", "CE 24 Satin", "CE Bass"]
      },
      {
        "title": "{argument name=\"row 5 label\" default=\"BOLT-ON SERIES\"}",
        "position": "fifth main row left label",
        "count": 6,
        "labels": ["NF 53", "Silver Sky", "NF 3", "NF 53 Satin", "DGT Bolt-On", "Studio"]
      },
      {
        "title": "{argument name=\"row 6 label\" default=\"PRIVATE STOCK\"}",
        "position": "sixth main row left label",
        "count": 6,
        "labels": ["Dragon I", "Frostbite", "#4004", "The Tree of Life", "#8731", "PS DGT"]
      }
    ],
    "footer": {
      "position": "bottom",
      "elements": ["small badge at lower left", "centered company line", "right-side script signature"]
    }
  },
  "content_grid": {
    "total_models_shown": "{argument name=\"total model count\" default=\"37\"}",
    "card_design": "{argument name=\"card design\" default=\"each product card contains a guitar render, model name, year, small pickup icons, a short descriptive blurb, and origin/wood specs at the bottom\"}",
    "row_side_panels": 6
  },
  "visual_details": {
    "products": "{argument name=\"product description\" default=\"front-facing electric guitars with varied body shapes and highly polished figured maple tops, metallic and transparent finishes, some solid colors, some natural wood\"}",
    "typography": "all caps serif headlines, small serif body text, script signature accents",
    "borders": "thin decorative gold rules around every panel and the full poster",
    "lighting": "studio-lit products against dark panel backgrounds",
    "render_quality": "clean infographic precision with realistic product renders"
  },
  "camera": "straight-on flat poster view, no perspective distortion, centered composition",
  "quality": "ultra detailed, print-ready, high-resolution editorial infographic, luxury brand poster",
  "constraints": {
    "must_keep": [
      "30+ 个产品 thumbnail 必须可读且方向统一（同一视角）",
      "tier 行左侧 label 清晰",
      "顶部 3 key（tier / pickup / tonal）必须可对应到产品卡上的小 icon",
      "签名 / 印章 / 主标 / 副标都必须出现",
      "整体一致深色 + 金 / 沙白配色"
    ],
    "avoid": [
      "产品方向不统一（一个正面一个 45° 一个仰拍）",
      "label 不对齐导致行不像 catalog",
      "30+ 产品挤在 1:1 方图里 → 必须竖版 3:4 或更长",
      "色彩超过 4 主色 + 6 accent",
      "产品名拼写错误（lineup 海报核心是产品名，必须正确）"
    ]
  }
}
```

### 参数策略

- **必问**：brand name、product category、6 个 tier 名 + 每行的产品名清单
- **可默认**：style overall（按品类自动）、palette、aspect ratio
- **可随机**：description blurb（按产品自动）、card 上的 spec 文字

### 自动补全策略

- 用户给"PRS 吉他全 lineup" → 用模板默认 6 行 × 6-7 SKU 结构
- 用户给"汽车品牌"+ 几个车型 → 自动按"轿车 / SUV / 跑车 / EV"分行
- 不指定 legend 数 → 默认 3 个（tier / 核心 spec / 性格）

## 变体 1：浅色极简 minimal（适合科技 / 设计品牌）

📝 提示词

```json
{
  "type": "minimal lineup comparison poster, light edition",
  "style_override": {
    "overall": "clean white / light gray background, thin sans-serif typography, no gold foil, no ornate borders, only thin hairlines",
    "palette": "off-white background, soft gray dividers, single accent color from brand (e.g. orange / blue / green)"
  },
  "use_case": "Apple / Tesla / Bose / 设计驱动品牌"
}
```

### 何时选这个变体

- 科技 / 设计品牌（不适合奢华金箔）
- 想要极简 / 现代感
- 单一 accent 强对比

## 变体 2：横版 timeline 谱系版（按年代分行）

📝 提示词

```json
{
  "type": "horizontal lineup chronology poster",
  "format_override": "horizontal poster, 16:9 or 21:9",
  "row_grouping_by": "decade (1950s / 60s / 70s / 80s / 90s / 2000s / 2010s / 2020s)",
  "use_case": "品牌 anniversary 海报 / 演变史"
}
```

### 何时选这个变体

- 品牌周年 / 历史海报
- 想强调「时间轴 + 演变」而非「等级 + 选择」
- 横屏展示（展览 / 门店墙）

## 变体 3：3 系列对比表（适合 SKU 较少 / 入门-旗舰对比）

📝 提示词

```json
{
  "type": "3-tier lineup comparison table poster",
  "row_count": 3,
  "rows": ["BASIC / 入门", "PRO / 进阶", "ULTRA / 旗舰"],
  "columns_per_row": 4,
  "extra_columns": ["spec table per tier with checkmarks / dashes"],
  "use_case": "新品发布 / 价位段对比 / B2C 选购指南"
}
```

### 何时选这个变体

- SKU 数 ≤ 12
- 用户更需要「性能对比」而非「lineup 全景」
- 适合官网 / 落地页 / 销售物料

## 避免事项

- ❌ 30+ SKU 挤在 1:1 方图 → 必须竖版长图或横版宽图
- ❌ 产品方向 / 视角不统一 → catalog 感立即崩塌
- ❌ tier label 用与正文相同字号 → 行无法快速识别
- ❌ legend key 与产品 thumb 上的 icon 对不上（图例失效）
- ❌ 产品 thumb 之间间距不均匀 → 视觉杂乱
- ❌ 产品名拼写错误（catalog 类海报核心信息）
- ❌ 配色 ≥ 6 主色（应控制在 1 主背景 + 1 主字色 + 1 accent + 至多 6 行 accent）
- ❌ 把模板里的"PRS Guitars"原样保留而你的品牌不是 PRS → 必须替换 brand name 与所有产品名
