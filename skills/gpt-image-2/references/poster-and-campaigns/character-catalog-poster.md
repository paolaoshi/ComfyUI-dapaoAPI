# 角色清单 / 系列卡片信息图海报模板

本文件用于生成"同一基础角色 / 同一系列基础物，分裂出 N 个变体（星座 / 元素 / 朝代 / 性格 / 季节），每个变体配独立 panel + 个性化文案 + 装饰主题"的信息图海报。

典型用途：

- 12 星座系列卡片海报（每次 3 个，共 4 个元素海报）
- MBTI 16 人格视觉海报
- 朝代 / 神话 / 民族 系列肖像
- 「同模特不同造型」的系列写真宣传图
- 节气 / 月份 / 季节 系列海报
- 角色多视角性格档案

特征：

- **同一基础角色**在所有 panel 中复用（外貌特征统一）
- **N 个 panel** 共享统一边框 / 排版 / 字体系统
- **每个 panel** 有独立 theme color、装饰 motif、文案 6-8 条
- 整体像「角色 / 概念字典的一页」

与其它模板的区别：

| 模板 | 重点 |
|---|---|
| `portraits-and-characters/character-sheet.md`（已有） | 单角色三视图 + 表情 + 服装 |
| `avatars-and-profile/cultural-portrait-series.md`（已有） | 朝代 / 民族 / 文学系列肖像（侧重肖像本身） |
| `avatars-and-profile/character-grid-portrait.md`（已有） | n×n 网格肖像（多职业 / 表情 / 朝代） |
| **本模板**（新增） | **同角色多版本卡片，每卡有独立 theme + 6-8 条性格文案 + 装饰 motif** |

## 适用范围

- 12 星座 / 4 元素 / MBTI / 节气 / 朝代 / 神话 系列海报
- 「同模特不同造型 + 性格档案」的 SNS 分享图
- IP 角色分支档案
- 心理测试 / 性格分类 视觉化海报

## 何时使用

- 用户提到"星座 / MBTI / 节气 / 朝代 / 性格分类 海报"
- 同一角色要拆成 N 个版本展示
- 每个版本需要独立文案 + 装饰主题
- 输出像「图鉴的一页」/「档案册的一章」

不要使用：

- 单角色多表情 → 用 `portraits-and-characters/character-sheet.md`
- 朝代 / 神话肖像但不带性格档案 → 用 `avatars-and-profile/cultural-portrait-series.md`
- n×n 拼图肖像（不带文案）→ 用 `avatars-and-profile/character-grid-portrait.md`

## 缺失信息优先提问顺序

1. 系列主题（12 星座 / MBTI / 朝代 / 季节 / 自定义）
2. 本张要画几个 panel（3 / 4 / 9 / 12 / 16）
3. 主体角色描述（**真人风 / anime 风 / 写实 / 偶像风**）+ 是否同一个人物
4. 主语言（中 / 英 / 日 / 双语）
5. 整体审美（**柔粉萌系 / 复古档案 / 极简朋克 / 古典工笔 / pastel editorial**）
6. 是否需要每 panel 独立 theme color
7. 比例（默认 3:4 竖版）

## 主模板：3-panel 同角色变体卡片海报（适合 12 星座按元素拆 / MBTI 4 维度拆）

📖 描述

竖版海报，header（主标 + 副标）+ 3 个上下堆叠的 panel，每 panel 内部分左角色 / 右文案，含独立 theme color、symbol、constellation / motif。

📝 提示词

```json
{
  "type": "{argument name=\"theme type\" default=\"Chinese zodiac-style character infographic poster\"}",
  "subject_overview": "{argument name=\"subject overview\" default=\"twelve zodiac character list, water signs edition\"}",
  "language": "{argument name=\"language\" default=\"Traditional Chinese\"}",
  "format": "vertical poster",
  "style": {
    "overall": "{argument name=\"style overall\" default=\"elegant anime-inspired character catalog with editorial infographic layout\"}",
    "rendering": "{argument name=\"rendering\" default=\"soft polished digital illustration, pastel gradients, delicate sparkles, ornamental border design\"}",
    "mood": "{argument name=\"mood\" default=\"dreamy, celestial, refined, feminine, aquatic\"}"
  },
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"2:3\"}",
    "background": "{argument name=\"background\" default=\"very light pearl white with pale blue-lavender tint, subtle texture, thin decorative frame with filigree corners and tiny stars\"}"
  },
  "header": {
    "title": "{argument name=\"headline text\" default=\"十二星座角色清單|水象星座\"}",
    "subtitle": "{argument name=\"subtitle text\" default=\"感受・直覺・共鳴\"}",
    "icons": ["small stars", "{argument name=\"top right motif\" default=\"water droplet emblem in top right\"}", "curled cloud-like line art in top left"]
  },
  "layout": {
    "sections_count": 3,
    "sections": [
      {
        "title": "{argument name=\"section 1 title\" default=\"巨蟹座 Cancer\"}",
        "position": "top panel",
        "theme_color": "{argument name=\"section 1 color\" default=\"powder blue\"}",
        "symbol": "{argument name=\"section 1 symbol\" default=\"Cancer glyph inside circle at left\"}",
        "constellation": "{argument name=\"section 1 constellation\" default=\"Cancer constellation at upper right\"}",
        "count": 6,
        "labels": [
          "{argument name=\"section 1 line 1\" default=\"元素:水\"}",
          "{argument name=\"section 1 line 2\" default=\"概念:情感守護者,把人放在心上\"}",
          "{argument name=\"section 1 line 3\" default=\"性格:溫柔、敏感、顧家\"}",
          "{argument name=\"section 1 line 4\" default=\"行動原則:先確認感受,再保護重要的人\"}",
          "{argument name=\"section 1 line 5\" default=\"戀愛傾向:慢慢靠近,越熟越黏\"}",
          "{argument name=\"section 1 line 6\" default=\"人際怪癖:嘴上說沒事,實際會記很久\"}"
        ],
        "character": {
          "identity": "{argument name=\"base character\" default=\"young woman model reimagined as zodiac character\"}",
          "pose": "{argument name=\"section 1 pose\" default=\"half-body portrait, facing forward, arms gently wrapped around a large seashell pillow\"}",
          "outfit": "{argument name=\"section 1 outfit\" default=\"light blue celestial slip dress with lace trim and sheer cardigan embroidered with stars and moons\"}",
          "background": "{argument name=\"section 1 bg\" default=\"soft blue night sky with crescent moon, seashell, sparkling stars, stylized ocean wave and tiny water droplets\"}"
        }
      },
      {
        "title": "{argument name=\"section 2 title\" default=\"天蠍座 Scorpio\"}",
        "position": "middle panel",
        "theme_color": "{argument name=\"section 2 color\" default=\"deep violet\"}",
        "symbol": "Scorpio glyph inside circle at left",
        "constellation": "Scorpio constellation at upper right",
        "count": 6,
        "labels": [
          "元素:水",
          "{argument name=\"section 2 line 2\" default=\"概念:深海偵察者,情緒有深度\"}",
          "{argument name=\"section 2 line 3\" default=\"性格:專注、神秘、意志強\"}",
          "{argument name=\"section 2 line 4\" default=\"行動原則:先觀察,再一擊到位\"}",
          "{argument name=\"section 2 line 5\" default=\"戀愛傾向:愛得深,重忠誠與獨占感\"}",
          "{argument name=\"section 2 line 6\" default=\"人際怪癖:越在乎越不說,會偷偷試探\"}"
        ],
        "character": {
          "identity": "{argument name=\"base character\" default=\"young woman model reimagined as zodiac character\"}",
          "pose": "half-body portrait, one hand near chin in a composed enigmatic gesture",
          "outfit": "black semi-sheer dress with gothic details and a dark plum off-shoulder shawl",
          "background": "dark purple celestial sea scene with crescent moon, bubbles, stars, and curling misty water shapes"
        }
      },
      {
        "title": "{argument name=\"section 3 title\" default=\"雙魚座 Pisces\"}",
        "position": "bottom panel",
        "theme_color": "{argument name=\"section 3 color\" default=\"lavender\"}",
        "symbol": "Pisces glyph inside circle at left",
        "constellation": "Pisces constellation at upper right",
        "count": 6,
        "labels": [
          "元素:水",
          "{argument name=\"section 3 line 2\" default=\"概念:夢境共感者,靠直覺導航\"}",
          "{argument name=\"section 3 line 3\" default=\"性格:浪漫、柔軟、有想像力\"}",
          "{argument name=\"section 3 line 4\" default=\"行動原則:先感受,再順流找答案\"}",
          "{argument name=\"section 3 line 5\" default=\"戀愛傾向:容易心動,渴望靈魂陪伴\"}",
          "{argument name=\"section 3 line 6\" default=\"人際怪癖:常把別人的情緒也一起感受\"}"
        ],
        "character": {
          "identity": "{argument name=\"base character\" default=\"young woman model reimagined as zodiac character\"}",
          "pose": "half-body portrait, one hand lifted as if balancing floating bubbles, other hand resting at chest",
          "outfit": "translucent lavender fantasy dress with soft draped sleeves and shimmering fabric",
          "background": "pale lilac underwater-celestial blend with bubbles, sparkles, and flowing translucent wave forms"
        }
      }
    ],
    "dividers": "three horizontal framed panels with thin ornamental borders"
  },
  "footer": {
    "center_icon": "{argument name=\"footer icon\" default=\"small blue seashell emblem\"}",
    "decorations": ["tiny stars", "fine scrollwork"]
  },
  "constraints": {
    "must_keep": [
      "3 个 panel 必须使用同一个 base character（脸 / 体型 / 发型 base 一致）",
      "每 panel 通过服装 / 道具 / 背景 motif 区分",
      "文字内容清晰且对齐（每 panel 6 行性格档案）",
      "整体色彩主题统一（如水象都用蓝紫系）",
      "分隔 panel 的边框样式一致"
    ],
    "avoid": [
      "把基础角色画成 3 个完全不同的人",
      "panel 间装饰 motif 风格漂移（一个写实一个卡通）",
      "性格档案文字超过 panel 一半面积",
      "将其它 9 个星座 / 不在主题内的内容也画进来",
      "使用过多字体（建议主标 + 性格列表 + 英文星座 三种字体即可）"
    ]
  }
}
```

### 参数策略

- **必问**：theme type（系列主题）、3 个 section title、base character description
- **可默认**：language（按 theme 推荐）、aspect ratio、装饰 motif
- **可随机**：性格档案 6 行的具体文案（按角色性格自动生成）

### 自动补全策略

- 用户给出"水象星座" → 自动 fill 巨蟹 / 天蠍 / 雙魚 + 蓝紫色调 + 海洋 motif
- 用户给出"火象" → 自动 fill 牡羊 / 獅子 / 射手 + 红橙金色 + 火焰 motif
- 用户给出"MBTI 分析家组" → 自动 fill INTJ / INTP / ENTJ / ENTP + 紫色 + 几何 motif

## 变体 1：4 panel 横版便当格（适合 16 panel 一组拆 4 张）

📝 提示词

```json
{
  "type": "4-panel character catalog poster, horizontal bento layout",
  "format_override": "horizontal poster, 16:9 or 4:3",
  "layout_override": {
    "structure": "2x2 grid, 4 equal panels",
    "use_case": "MBTI 4 维度（NT / NF / SJ / SP）一张图各 1 个代表角色"
  },
  "section_count": 4,
  "must_keep": ["4 panel 共享同一个 base character", "对角线/网格平衡"]
}
```

### 何时选这个变体

- 想做 MBTI 16 类拆 4 维度
- 12 星座拆 4 元素，每张 3 个 → 不如 1 张 4 元素代表
- 横屏分享渠道（Twitter / 朋友圈）

## 变体 2：12 panel 全集（不推荐单图，但若必须）

📝 提示词

```json
{
  "type": "12-panel full series character catalog poster",
  "section_count": 12,
  "layout_override": {
    "format": "very tall vertical poster, 1:2 or longer",
    "structure": "3 columns x 4 rows OR 4 columns x 3 rows",
    "panel_internal_layout": "much smaller per-panel: 1 character thumb + 3 short labels (not 6)"
  },
  "warning": "panel 越多每格细节越塌；建议拆成 4 张元素海报而不是 1 张 12 panel"
}
```

### 何时选这个变体

- 必须出 1 张 = 全 12 星座 / 12 节气
- 客户接受牺牲单 panel 细节
- 用作系列总览图（不是细读图）

## 变体 3：朝代 / 神话 系列肖像（无星座符号，加文化 motif）

📝 提示词

```json
{
  "type": "dynastic / mythological character catalog poster",
  "section_count": 3,
  "section_examples": ["唐 / 宋 / 明 / 清 / 民国"],
  "style_override": {
    "overall": "elegant editorial portrait series with classical Chinese motifs",
    "palette": "warm beige, antique gold, ink black, vermilion red",
    "decoration_per_panel": "对应朝代的纹样 / 服饰 / 建筑 / 器皿"
  },
  "labels_per_panel_count": 5,
  "labels_examples": ["年代", "服饰特色", "代表器物", "性格 keyword", "印章 / 落款"]
}
```

### 何时选这个变体

- 文创 / 出版 / 教育历史类
- 想做「同一模特穿不同朝代」的写真系列
- 不需要星座 / MBTI 这种现代分类

## 避免事项

- ❌ 把 base character 画成多个不同的人 → 致命，立即破坏「同一角色多版本」核心
- ❌ panel 间装饰 motif 风格漂移（一个写实一个 chibi）
- ❌ 在 3-panel 海报中硬塞 12 个星座 → 不可读
- ❌ 性格档案文字遮住人物脸 / 占据 > 50% 面积
- ❌ panel 边框 / 字体不统一 → 看起来像 3 张不同海报拼贴
- ❌ 在主题外硬塞额外元素（"水象星座" 海报里出现火焰）
- ❌ 配色 ≥ 5 主色 → 失去系列感
- ❌ 一个 panel 6 行文字、另一个 8 行 / 另一个 4 行 → 必须等量
