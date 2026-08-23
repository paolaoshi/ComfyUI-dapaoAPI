# 品牌识别系统板模板

本文件用于"一张图展示品牌完整识别系统"的视觉：

- 品牌 logo + 字体 + 配色 + 应用场景
- VI 摘要单页
- 品牌提案 board
- 品牌指南 cover
- 设计师 case study 单页

特征：

- 一张大图分多区块
- logo 应用 + 配色板 + 字体规范 + 实物 mockup
- 强调"系统感 + 专业感"
- 通常带 grid + label
- 偏冷静、不过度装饰

## 适用范围

- 品牌识别系统板（VI summary）
- 品牌提案 board
- 设计师作品集 single page

## 何时使用

- 用户提到"VI / 品牌识别 / 品牌系统 / brand board / brand guideline cover"
- 用户希望一张图展示品牌全套

不要使用：

- 吉祥物品牌套装（用 `mascot-brand-kit.md`）
- 单个海报（用 `poster-and-campaigns/brand-poster.md`）
- 包装 mockup 单图（用 `cosmetic-packaging.md`）

## 缺失信息优先提问顺序

1. 品牌名 + 一句定位
2. 行业 / 受众
3. logo 主形态（文字 / 图形 / 组合）
4. 主色 1-2 个
5. 字体偏好（衬线 / 无衬线 / 手写）
6. 是否需要包装 / 名片 / 海报 mockup

## 主模板：品牌识别系统板

📖 描述

整体一张大图，分 logo 区 + 配色区 + 字体区 + 应用 mockup 区。

📝 提示词

```json
{
  "type": "品牌识别系统板",
  "goal": "生成一张可作为 VI summary / brand board 的品牌识别系统单页",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"AURORA\"}",
    "tagline": "{argument name=\"tagline\" default=\"光，让生活柔软\"}",
    "industry": "{argument name=\"industry\" default=\"家居灯光\"}",
    "personality": "{argument name=\"personality\" default=\"温柔、现代、克制\"}"
  },
  "regions": {
    "logo": {
      "position": "{argument name=\"logo position\" default=\"左上大区\"}",
      "primary_logo": "{argument name=\"primary logo\" default=\"AURORA 字标 + 圆形光晕图形\"}",
      "secondary_logos": ["黑白单色版", "图形版（无文字）", "竖排版"],
      "background_test": "深底 / 浅底各展示一次"
    },
    "color_palette": {
      "position": "{argument name=\"color position\" default=\"右上\"}",
      "primary": [
        "{argument name=\"primary color 1\" default=\"#0F4C81 海军蓝\"}",
        "{argument name=\"primary color 2\" default=\"#FFD166 暖金\"}"
      ],
      "secondary": [
        "{argument name=\"secondary color 1\" default=\"#F4F1EA 米白\"}",
        "{argument name=\"secondary color 2\" default=\"#222 深灰\"}"
      ],
      "swatch_design": "色块 + HEX + 中文名"
    },
    "typography": {
      "position": "{argument name=\"type position\" default=\"左下\"}",
      "headline_font": "{argument name=\"headline font\" default=\"现代 serif（如 Playfair Display）\"}",
      "body_font": "{argument name=\"body font\" default=\"中文圆体 + 英文 sans\"}",
      "demo_block": "Aa Bb Cc 1234 + 一句中文 + 一句英文"
    },
    "applications": {
      "position": "{argument name=\"app position\" default=\"右下\"}",
      "mockups": [
        "{argument name=\"mockup 1\" default=\"名片正反面\"}",
        "{argument name=\"mockup 2\" default=\"产品包装盒\"}",
        "{argument name=\"mockup 3\" default=\"app icon + 闪屏\"}"
      ]
    }
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"现代极简 brand board，米色背景 + 微纸纹\"}",
    "grid": "细灰色辅助线"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "4 个区块边界清晰",
      "logo 区始终居首位",
      "配色板 ≤ 6 色 + HEX 可读",
      "应用 mockup 风格统一"
    ],
    "avoid": [
      "塞太多元素导致每区无呼吸感",
      "字体超过 2 种家族",
      "颜色超过 6 种",
      "缺少 HEX 编号"
    ]
  }
}
```

### 参数策略

- 必问：品牌名、行业、主色、定位
- 可默认：layout、字体推荐、应用 mockup
- 可随机：mockup 实物细节

### 自动补全策略

- 用户给品牌名 + 行业 + 一种性格关键词时：自动展开 logo + 配色 + 字体 + 3 个 mockup
- 默认"现代极简"风
- 默认竖版 3:4

## 变体 1：极致极简 brand board（仅 logo + 颜色）

📝 提示词

```json
{
  "type": "极简 brand board",
  "regions": {
    "logo": {"primary_logo": "字标 + 极简图形", "background_test": "白底 + 纯黑底"},
    "color_palette": {"primary": ["#000", "#FFF", "#FFD166"]},
    "typography": {"demo_block": "Aa Bb"},
    "applications": null
  },
  "constraints": {
    "must_feel": "瑞士平面 / Japanese minimal"
  }
}
```

## 变体 2：高密度 brand board（含语气、icon 系统）

📝 提示词

```json
{
  "type": "高密度 brand board",
  "regions": {
    "logo": {"primary_logo": "..."},
    "color_palette": {"primary": ["..."], "secondary": ["..."]},
    "typography": {"demo_block": "..."},
    "applications": {"mockups": ["名片", "包装", "海报", "app icon", "网站 hero"]}
  },
  "extras": {
    "icon_system": "12 个统一风格图标网格",
    "tone_of_voice": "3 句品牌语气示例"
  },
  "constraints": {
    "must_feel": "完整可印刷 brand book cover"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "Brand board 自动补全",
  "mode": "auto-fill",
  "rule": "用户给品牌名 + 行业 + 一句性格描述，自动决定 logo / 配色 / 字体 / 应用 mockup",
  "constraints": {
    "must_feel": "可作为客户提案首页"
  }
}
```

## 避免事项

- 不要让 logo 区被压缩到不显眼
- 不要让配色 > 6 种
- 不要让字体 > 2 个家族
- 不要让 mockup 过于花哨破坏专业感
- 不要漏掉 HEX 标注
- 不要让背景出现强烈纹理
