# 18+ 模块吉祥物全流程品牌设计文档模板

本文件用于生成"一张超大画布、把吉祥物从 DNA 分析到落地应用的整套设计文档拍扁到一张图"的视觉。

典型用途：

- 设计公司给客户的 brand book / IP guideline 提案图
- 设计师作品集封面（一张图秀完整设计流程）
- IP 上线前的"design rationale"看板
- 教学示例：「一个吉祥物从概念到落地」全过程
- 投标 / 比稿用的能力展示图

特征（与现有 `mascot-brand-kit.md` 的区别）：

| 维度 | `mascot-brand-kit.md`（已有） | 本模板（新增） |
|---|---|---|
| 模块数 | 4-6 个区块 | **18-24 个模块** |
| 视角 | 主形象 + 三视图 + 表情 + 应用 | **DNA 分析 → moodboard → 探索草图 → 线稿 → 3D → 配色 → 材质 → 设计系统 → 数字应用 → 实物应用 → 终稿** |
| 用途 | IP 介绍页 / 周边 catalog | **完整 brand book / 设计提案 / 投标稿** |
| 渲染密度 | 中等 | 极高（接近 brand book PDF 的整页拼合） |

## 适用范围

- 18+ 模块吉祥物全流程设计文档
- 完整 brand book / IP guideline 一图概览
- 设计公司投标 / 提案 hero 图
- 「设计过程可视化」教学板

## 何时使用

- 用户提到"完整品牌设计流程 / brand guideline / IP design book"
- 用户希望出"包含设计推导过程"而不仅是结果
- 客户需要一张图涵盖「DNA → 草图 → 线稿 → 3D → 应用」全部环节

不要使用：

- 仅需 IP 形象集合 → 用 `branding-and-packaging/mascot-brand-kit.md`
- 仅需通用品牌识别（logo / 色 / 字 / 应用）→ 用 `branding-and-packaging/brand-identity-board.md`
- 单角色三视图 / 表情 → 用 `portraits-and-characters/character-sheet.md`
- IP 周边商品图 → 用 `branding-and-packaging/character-merch-board.md`

## 缺失信息优先提问顺序

1. 品牌 / IP 名 + 行业（茶饮 / 教育 / 数码 / 文创…）
2. 吉祥物主形态（动物 / 人形 / 拟物 / 食物 / 抽象）
3. 主色 + 副色（如不指定按行业默认）
4. 渲染风格（**3D Pixar 写实卡通 / 扁平 2D / Q 版 chibi / 拟人**）
5. 模块密度（18 / 24 / 自定义清单）
6. 必须出现的应用场景（plush 玩偶 / 包装 / app icon / 门店 / 等）

## 主模板：18 模块吉祥物全流程品牌设计文档

📖 描述

3 列 × 6 行 = 18 个等大模块，每个模块自成一段设计流程。整体像把一份 18 页 brand book PDF 的每页缩成一格拼到一张大图里。

📝 提示词

```json
{
  "type": "18-panel brand identity and character design document",
  "goal": "生成一张完整记录吉祥物从 DNA 分析到落地应用全流程的设计文档大图，可作为 brand book 一图概览或设计提案 hero 图",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"沐阳 MUYANG TEA\"}",
    "industry": "{argument name=\"industry\" default=\"tea shop\"}",
    "tagline": "{argument name=\"tagline\" default=\"温暖一杯,陪你慢慢喝\"}",
    "colors": [
      "{argument name=\"primary color\" default=\"yellow\"}",
      "{argument name=\"secondary color\" default=\"green\"}",
      "white",
      "brown",
      "dark green"
    ]
  },
  "character": {
    "description": "{argument name=\"character description\" default=\"3D rendered cute Shiba Inu mascot wearing a green apron, big sparkly eyes, plush soft body, friendly smile\"}",
    "rendering_style": "{argument name=\"render style\" default=\"Pixar-quality 3D, soft subsurface scattering, glossy plush texture\"}"
  },
  "layout": {
    "grid": "3 columns by 6 rows",
    "panel_count": 18,
    "panel_borders": "thin light-gray dividers, generous white margin between cells",
    "global_typography": "section titles in bilingual Chinese + English, small body text, panel numbers 01-18 prominently labeled",
    "background": "{argument name=\"page background\" default=\"clean off-white paper\"}"
  },
  "sections": [
    {
      "id": "01",
      "title": "01 品牌DNA分析 / BRAND DNA ANALYSIS",
      "elements": ["small logo lockup", "5 color swatches with HEX codes", "6 brand keyword icons", "small target audience donut chart"]
    },
    {
      "id": "02",
      "title": "02 概念构思 / CONCEPT MOODBOARD",
      "elements": ["5 inspiration photo references", "4 mood / vibe icons", "1 design equation diagram (e.g. 茶 + 狗 + 温暖 = MUYANG)"]
    },
    {
      "id": "03",
      "title": "03 形态研究 / FORM STUDY",
      "elements": ["4 logo anatomy icons", "4 evolution steps from primitive shape to refined silhouette", "4 final silhouette variants"]
    },
    {
      "id": "04",
      "title": "04 概念探索 / CONCEPT EXPLORATION",
      "elements": ["12 quick line-art character sketches with subtle pose / expression variation"]
    },
    {
      "id": "05",
      "title": "05 精细线稿 / REFINED LINE ART",
      "elements": ["3 rows showing front and side line-art with proportion guides, head-body ratio markers, and grid alignment"]
    },
    {
      "id": "06",
      "title": "06 细节精修 / DETAIL REFINEMENT",
      "elements": ["2 large full-body 3D renders with annotation labels", "4 circular close-up callouts (eyes, paw, apron stitch, tail)"]
    },
    {
      "id": "07",
      "title": "07 表情设定 / EXPRESSION SHEET",
      "elements": ["11 3D rendered head expressions: happy, sad, surprised, sleepy, angry, shy, proud, worried, laughing, wink, neutral"]
    },
    {
      "id": "08",
      "title": "08 姿势库 / POSE LIBRARY",
      "elements": ["9 full-body 3D rendered poses: waving, bowing, holding tea, jumping, sitting, sleeping, presenting, running, hugging cup"]
    },
    {
      "id": "09",
      "title": "09 转身视图 / TURNAROUND VIEW",
      "elements": ["5 full-body 3D renders at 0°/45°/90°/135°/180°", "5 matching line-art turnaround views below"]
    },
    {
      "id": "10",
      "title": "10 色彩开发 / COLOR DEVELOPMENT",
      "elements": ["5 rows of 5-color palettes (primary, accent, monochrome, seasonal, dark mode)", "short color psychology paragraph"]
    },
    {
      "id": "11",
      "title": "11 材质规格 / MATERIAL SPECIFICATION",
      "elements": ["5 texture swatches (plush, vinyl, ceramic, fabric, plastic)", "property sliders (softness / glossiness / transparency)", "4 manufacturing process icons"]
    },
    {
      "id": "12",
      "title": "12 色彩应用 / COLOR APPLICATION",
      "elements": ["4 mascot color variant renders", "2 light-mode and dark-mode renders", "4 contrast rating circles (AAA / AA / A / fail)"]
    },
    {
      "id": "13",
      "title": "13 构造指南 / CONSTRUCTION GUIDE",
      "elements": ["1 line-art geometry construction diagram (with circles / triangles / proportion lines)", "1 grid alignment diagram"]
    },
    {
      "id": "14",
      "title": "14 设计系统规则 / DESIGN SYSTEM RULES",
      "elements": ["minimum size icons (16px / 24px / 48px)", "clear-space diagram with X-height markers", "4 do/don't usage examples"]
    },
    {
      "id": "15",
      "title": "15 资产变体 / ASSET VARIANTS",
      "elements": ["3 size variants (S / M / L)", "3 line-art variants", "3 simplified flat icon-style heads"]
    },
    {
      "id": "16",
      "title": "16 数字应用 / DIGITAL APPLICATIONS",
      "elements": ["1 app icon mockup", "2 social avatar mockups", "small UI element row (button / loader / badge)", "3-step animation cycle thumbnails"]
    },
    {
      "id": "17",
      "title": "17 实物应用 / PHYSICAL APPLICATIONS",
      "elements": ["1 plush toy mockup", "1 product packaging mockup", "1 merchandise (tote / mug) mockup", "1 storefront / signage mockup"]
    },
    {
      "id": "18",
      "title": "18 最终主视觉 / FINAL RENDERING",
      "elements": ["1 large hero-size 3D render of mascot in signature pose holding brand product", "logo lockup", "file format / deliverable list"]
    }
  ],
  "global_style": {
    "rendering": "premium design agency presentation board, mixing 3D character renders, line art, photo mockups, charts, and infographic typography",
    "color_tone": "calm, professional, off-white background with brand colors as accents",
    "panel_density": "each panel completely filled but not cluttered; consistent label position (top-left) and small body text",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4 portrait poster (e.g. A2 print)\"}"
  },
  "constraints": {
    "must_keep": [
      "18 个模块编号清晰、双语标题",
      "吉祥物造型在所有 3D 模块中保持完全一致",
      "整体像 brand book 一页拼合，而不是 18 张独立海报",
      "每个模块的子元素数量精确（11 表情 / 9 姿势 / 5 转身 / 等）"
    ],
    "avoid": [
      "模块间风格漂移（一个模块 3D 写实、另一个忽然手绘）",
      "省略编号或双语标题",
      "把表情 / 姿势 / 转身画成同一姿势复制",
      "应用 mockup 不像真实物体（如 plush 看起来像截图）"
    ]
  }
}
```

### 参数策略

- **必问**：brand name + industry、character description、render style、primary/secondary colors
- **可默认**：tagline、page background、aspect ratio
- **可随机**：表情库 / 姿势库的具体 11 / 9 项内容（按 IP 性格自动）

### 自动补全策略

- 用户只说"吉祥物"+ 行业 → 自动按行业语义生成形象（茶饮 → 柴犬 / 兔子；科技 → 机器人 / 像素小怪；母婴 → 萌兽 / 云朵小人）
- 不指定 11 表情 / 9 姿势具体内容 → 用模板里的标准集
- 不指定材质 / 应用场景 → 按行业默认（餐饮强调包装 / 玩偶；科技强调 app icon / UI）

## 变体 1：24 模块完整 IP guideline（适合大客户提案）

把上面 18 模块基础上再加 6 个模块，覆盖 IP 商业化更深维度。

📝 提示词

```json
{
  "type": "24-panel mascot IP commercialization guideline",
  "extra_sections_after_18": [
    {
      "id": "19",
      "title": "19 联名场景 / CO-BRANDING SCENARIOS",
      "elements": ["4 联名 mockup（与不同行业品牌跨界）"]
    },
    {
      "id": "20",
      "title": "20 节庆主题包 / SEASONAL VARIATIONS",
      "elements": ["4 节庆变体（春节 / 中秋 / 圣诞 / 万圣节）"]
    },
    {
      "id": "21",
      "title": "21 表情包 / STICKER PACK",
      "elements": ["16 chibi 表情贴纸网格"]
    },
    {
      "id": "22",
      "title": "22 周边商品矩阵 / MERCH MATRIX",
      "elements": ["6 周边类目（公仔 / 文具 / 服饰 / 家居 / 数码 / 食品）"]
    },
    {
      "id": "23",
      "title": "23 内容平台应用 / SOCIAL CONTENT KIT",
      "elements": ["1 公众号头图 + 1 视频封面 + 1 朋友圈九宫格 + 1 直播间背景"]
    },
    {
      "id": "24",
      "title": "24 商业化路径 / COMMERCIALIZATION ROADMAP",
      "elements": ["timeline with 4 phases: 上线 / 周边 / 联名 / IP 授权"]
    }
  ]
}
```

### 何时选这个变体

- 大客户 IP 比稿
- 提案需要展示「不仅会设计，还懂商业化」
- 想一图秀完整 IP 商业蓝图

## 变体 2：极简 9 模块快速 brand kit

适合中小客户预算、不需要全流程，但要比单图丰富。

📝 提示词

```json
{
  "type": "9-panel quick mascot brand kit",
  "layout": { "grid": "3 columns by 3 rows", "panel_count": 9 },
  "sections": [
    "01 LOGO + COLOR",
    "02 主形象 3D HERO",
    "03 表情 6 个",
    "04 姿势 4 个",
    "05 三视图",
    "06 配色调色板",
    "07 字体规范",
    "08 应用 mockup（包装 + app icon）",
    "09 终稿主视觉"
  ]
}
```

### 何时选这个变体

- 客户预算有限 / 时间紧
- 一图 = 一份 mini 设计文档（朋友圈级别可读）
- 试稿阶段先出这版，确认方向再升级 18 / 24 模块

## 变体 3：纯设计推导版（无 3D，全是草图 + 线稿）

适合学院派 / 文创 / 手作品牌，强调「设计思考过程」。

📝 提示词

```json
{
  "type": "18-panel mascot design rationale (sketch-first edition)",
  "rendering_override": "ALL panels in pencil sketch + ink line + watercolor wash; NO 3D renders even in 06/08/09; final panel 18 may upgrade to ink-color illustration",
  "vibe": "designer's working notebook scanned and laid out as a document",
  "extra_visual_elements": ["coffee stain", "tape strips", "handwritten margin notes"]
}
```

### 何时选这个变体

- 文创 / 出版 / 手作 / 学院派品牌
- 想强调「人手设计、有温度」
- 对接独立设计师 / 插画师作品集

## 避免事项

- ❌ 模块编号缺失或顺序错乱（18 个模块的编号是模板的灵魂）
- ❌ 让吉祥物造型在不同模块漂移（必须严格保持同一形态）
- ❌ 表情 / 姿势 / 转身的数量不精确（11 / 9 / 5 是经过验证的视觉密度）
- ❌ 把 mockup 区画成贴图拼贴而非真实材质渲染
- ❌ 全图 18 模块共用一种字号 → hierarchy 崩塌；section 标题必须比 body 大 ≥ 1.6×
- ❌ 整体像 18 张独立海报拼贴 → 应该有共享背景 + 一致 margin + 一致标题样式
- ❌ 在画质有限时硬上 24 模块 → 单格细节会塌陷，建议 18 模块为上限
