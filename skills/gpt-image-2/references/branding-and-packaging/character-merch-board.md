# 角色 IP × 周边商品板模板

本文件用于生成"以单一动漫 / VTuber / 二次元角色为核心，叠加品牌 logo + 包装 + 周边 + SNS profile + 推广 banner"的复合视觉板。

典型用途：

- VTuber 出道 / 周年 / 新企划介绍图
- 同人 / 个人 IP 上线宣传图
- 二次元品牌（candy / bakery / cafe / 杂货店）店铺联动图
- 角色周边一图集合
- IP 房间生活方式商品 catalog
- 社交媒体宣传图（一图涵盖角色介绍 + 商品预告 + SNS handle）

特征（与其它 mascot / brand 模板的区别）：

| 模板 | 主体 | 重点 |
|---|---|---|
| `mascot-brand-kit.md`（已有） | 卡通吉祥物 | 三视图 + 表情 + 应用 |
| `full-mascot-brand-doc.md`（新增） | 卡通吉祥物 | 18 模块全流程设计文档 |
| `brand-identity-board.md`（已有） | 抽象品牌 | logo + 色 + 字 + 应用 mockup |
| **本模板**（新增） | **二次元角色 / VTuber / 个人 IP** | **角色形象 + 包装 + 周边 + SNS + lifestyle goods** |

## 适用范围

- VTuber 周边介绍板
- 个人 IP / VUP 出道宣传图
- 二次元品牌 × 实体商品联动图
- 角色生活方式 / 房间杂货商品集合
- 同人圈展会出本宣传图

## 何时使用

- 用户提到"角色周边 / VTuber 出道 / IP merch board / 个人企划图"
- 角色是动漫 / 二次元 / 萌系风格，而不是企业级吉祥物
- 需要"一张图秀完整 IP 商业生态"（角色 + 商品 + SNS + 包装）

不要使用：

- 企业 / 餐饮品牌吉祥物完整设计文档 → 用 `full-mascot-brand-doc.md`
- 仅角色三视图 / 表情 → 用 `portraits-and-characters/character-sheet.md`
- 单角色单海报 → 用 `portraits-and-characters/virtual-host.md`
- 单纯包装设计 → 用 `branding-and-packaging/cosmetic-packaging.md`

## 缺失信息优先提问顺序

1. 角色名 + 一句性格描述（必问，画面灵魂）
2. 主题色 + motif（樱花 / 海洋 / 星空 / 糖果 / 兔子…）
3. 风格基调（**柔粉萌系 / 哥特暗黑 / 赛博 / 和风 / 童话**）
4. 必须出现的商品类目（包装食品 / 文具 / 服饰 / 家居 / 数码周边）
5. SNS handle（可选，加上更像真实企划）
6. 是否包含店铺 / 活动信息（"4.26 NEW OPEN" 之类）

## 主模板 1：动漫角色品牌识别 + 周边商品板（Case 112 风格）

📖 描述

一张大图，包含 header banner + 包装 mockup + 推广海报 + web banner + SNS profile + 周边商品集合，全部围绕同一个角色展开。

📝 提示词

```json
{
  "type": "brand identity and merchandise design board",
  "goal": "生成一张以单一动漫角色为核心的完整品牌发布板，可作为角色出道、周年企划、IP 上线宣传图",
  "theme": {
    "color_palette": "{argument name=\"theme color\" default=\"pastel pink\"} and white",
    "motif": "{argument name=\"motif\" default=\"cherry blossoms\"} and pink hearts",
    "vibe": "{argument name=\"vibe\" default=\"sweet, soft, dreamy, idol-debut energy\"}"
  },
  "character": {
    "name": "{argument name=\"character name\" default=\"癒音ちー\"}",
    "subname": "{argument name=\"character subtext\" default=\"ゆおんちー\"}",
    "description": "{argument name=\"character description\" default=\"anime girl with short brown bob hair, pink eyes, wearing a white hoodie, gentle smile\"}",
    "personality": "{argument name=\"personality\" default=\"治愈系，温柔，喜欢甜食\"}"
  },
  "branding": {
    "main_logo": "{argument name=\"main logo text\" default=\"癒音ちー\"}",
    "sub_logo": "{argument name=\"sub logo text\" default=\"ゆおんちー\"}",
    "social_handle": "{argument name=\"social handle\" default=\"@yuonchii\"}"
  },
  "layout": {
    "format": "single large composite board, vertical poster orientation",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4 portrait\"}",
    "background": "{argument name=\"background\" default=\"clean white with soft pink gradient corners and tiny doodles\"}",
    "sections": [
      {
        "type": "header banner",
        "position": "top",
        "elements": ["large main logo", "small sub logo beneath", "cherry blossom decorative graphics", "character portrait on the right"]
      },
      {
        "type": "product packaging",
        "position": "middle left",
        "elements": [
          "1 square box with heart-shaped transparent window showing {argument name=\"packaging filling\" default=\"pink heart candies\"} inside",
          "character illustration printed on the box front",
          "2 individual candy / product wrappers placed beside the box",
          "5 scattered {argument name=\"scattered item\" default=\"heart candies\"} around the packaging"
        ]
      },
      {
        "type": "promotional poster",
        "position": "middle right",
        "elements": [
          "character portrait centered",
          "{argument name=\"poster prop\" default=\"heart-shaped candy bowl\"}",
          "main logo at the top",
          "{argument name=\"event tag\" default=\"4.26 NEW OPEN\"} text",
          "social handle text"
        ]
      },
      {
        "type": "horizontal web banner",
        "position": "lower middle",
        "elements": ["main logo on the left", "{argument name=\"motif\" default=\"cherry blossoms\"} graphics filling the middle", "character portrait on the right", "thin tagline below"]
      },
      {
        "type": "social media profile mockup",
        "position": "bottom left",
        "elements": [
          "header / cover image with logo and motif",
          "1 circular profile picture (character close-up)",
          "handle text '{argument name=\"social handle\" default=\"@yuonchii\"}'",
          "1 follow button (filled accent color)",
          "mock bio: 2-3 lines of character introduction"
        ]
      },
      {
        "type": "merchandise collection",
        "position": "bottom right",
        "count": 9,
        "items": [
          "{argument name=\"merch 1\" default=\"1 white t-shirt with logo\"}",
          "{argument name=\"merch 2\" default=\"1 white mug with character\"}",
          "{argument name=\"merch 3\" default=\"4 round pin badges\"}",
          "{argument name=\"merch 4\" default=\"1 acrylic keychain\"}",
          "{argument name=\"merch 5\" default=\"2 candy packets\"}"
        ]
      }
    ]
  },
  "global_style": {
    "rendering": "polished anime-illustration style for the character + photorealistic product mockups for packaging / merchandise + clean editorial layout for SNS / banner",
    "typography": "main logo in cute display font; SNS / body in clean sans-serif; small handwritten accents",
    "consistency": "the same character appearance used in EVERY section without drift",
    "panel_density": "moderate; each section breathes with consistent margin"
  },
  "constraints": {
    "must_keep": [
      "角色形象在所有 section 中完全一致（发型 / 配色 / 表情 base）",
      "logo / SNS handle 拼写统一",
      "每个 section 有清晰边界，不要互相溢出",
      "包装 / 周边看起来像真实物体而非贴图拼贴"
    ],
    "avoid": [
      "在不同 section 中改变角色发色 / 服装 base color",
      "周边商品看起来是同一物件复制（应有材质差异：陶瓷 / 棉布 / 亚克力 / 纸）",
      "把 SNS profile 区做得不像真实社交平台 UI",
      "header logo 字号被周围装饰挤压到难读"
    ]
  }
}
```

### 参数策略

- **必问**：character name、character description、theme color、motif
- **可默认**：merch 1-5（按 vibe 自动推荐周边类目）、aspect ratio
- **可随机**：scattered item / poster prop（按 motif 自动）、bio 文案

### 自动补全策略

- 用户只说"VTuber 出道宣传图"+ 角色形象 → 自动配套粉色樱花 / 蓝色海洋 / 紫色星空 motif
- 用户没指定周边 → 默认 9 件套（T 恤 / 马克杯 / 4 徽章 / 钥匙扣 / 2 包装）
- 用户没说店铺信息 → SNS profile 区不强调"NEW OPEN"，改为"PROFILE"

## 主模板 2：角色房间杂货 lifestyle 商品集合（Case 167 风格）

📖 描述

不强调出道 / 品牌发布，而是"这个角色喜欢什么样的房间生活"，把 6 件家居生活物品 + 角色 + 概念说明拼在一张图。

📝 提示词

```json
{
  "type": "pastel lifestyle poster / character room-goods feature sheet",
  "goal": "生成一张以角色为代言人、展示其喜爱房间生活物品的杂志风 catalog 图，适合 SNS 分享 / 商品预告 / 个人企划",
  "theme": "{argument name=\"theme\" default=\"soft dreamy lavender jellyfish aesthetic\"}",
  "style": "{argument name=\"style\" default=\"Japanese cute editorial graphic, airy white background, pastel lilac palette, delicate handwritten notes, sparkles and tiny doodles, soft product photography mixed with magazine layout\"}",
  "subject": {
    "character": {
      "name": "{argument name=\"character name\" default=\"くらげちゃん\"}",
      "appearance": "{argument name=\"character appearance\" default=\"young woman with a short platinum-blonde bob haircut, wearing a fluffy pale-lavender zip hoodie over a white inner top, shown from chest up on the lower right, face intentionally obscured with a plain beige rectangle\"}"
    }
  },
  "layout": {
    "orientation": "vertical poster",
    "background": "clean white with faint pastel doodles of stars, bubbles, tiny jellyfish, and musical notes",
    "sections": [
      { "title": "header", "position": "top", "elements": ["speech bubble intro", "main title", "small subtitle GOODS", "horizontal lavender ribbon tagline", "round badge on the top right"] },
      { "title": "featured goods grid", "position": "upper and middle left", "count": 6, "labels": ["{argument name=\"goods 1\" default=\"ゆらゆらくらげランプ\"}", "{argument name=\"goods 2\" default=\"くらげと夢見るベッドリネン\"}", "{argument name=\"goods 3\" default=\"くらげシェルミラー\"}", "{argument name=\"goods 4\" default=\"くらげグラデマグ\"}", "{argument name=\"goods 5\" default=\"くらげのときめき収納ボックス\"}", "{argument name=\"goods 6\" default=\"くらげふわもこマット\"}"] },
      { "title": "side handwritten note", "position": "upper right", "labels": ["{argument name=\"side note\" default=\"みんなも くらげちゃんRoomで いっしょに まったりしよー♡♡\"}"] },
      { "title": "room concept box", "position": "lower left", "labels": ["{argument name=\"concept title\" default=\"くらげちゃんの お部屋作りのこだわり\"}"] },
      { "title": "pick up circle", "position": "lower center-left", "labels": ["Pick up!"] }
    ]
  },
  "product_images": {
    "count": 6,
    "items": [
      { "name": "{argument name=\"goods 1\" default=\"ゆらゆらくらげランプ\"}", "description": "small translucent jellyfish-shaped lamp on a white base, glowing softly in pale blue-lavender" },
      { "name": "{argument name=\"goods 2\" default=\"くらげと夢見るベッドリネン\"}", "description": "plush pastel-lavender bed with fluffy comforter and pillows, dreamy cozy bedroom styling" },
      { "name": "{argument name=\"goods 3\" default=\"くらげシェルミラー\"}", "description": "small tabletop mirror with a puffy shell-like pastel-lilac frame and rounded base" },
      { "name": "{argument name=\"goods 4\" default=\"くらげグラデマグ\"}", "description": "ceramic mug with lavender-to-pink gradient and a simple jellyfish illustration" },
      { "name": "{argument name=\"goods 5\" default=\"くらげのときめき収納ボックス\"}", "description": "pastel storage box holding cosmetics and small bottles, decorated with a jellyfish emblem" },
      { "name": "{argument name=\"goods 6\" default=\"くらげふわもこマット\"}", "description": "small fluffy cloud-like or jellyfish-like mat in pale lavender and white" }
    ]
  },
  "text_elements": {
    "main_title": "{argument name=\"headline text\" default=\"くらげちゃんの お部屋アイテム\"}",
    "tagline": "{argument name=\"tagline\" default=\"ふわふわで甘くて、ちょっぴり夢みたいな私のお部屋へようこそ♡\"}",
    "concept_points": {
      "count": 3,
      "items": [
        "{argument name=\"concept 1\" default=\"色は白とラベンダーで統一!\"}",
        "{argument name=\"concept 2\" default=\"光が集まるふわっとした空間に\"}",
        "{argument name=\"concept 3\" default=\"お友達入りのアイテムに囲まれて 自分らしくいられる空間を大切にしてるよ♪\"}"
      ]
    },
    "product_blurbs": "each product has a short handwritten Japanese description in a cute casual font beside or below the image"
  },
  "composition": "the poster is left-heavy with product cards and text, while the character portrait occupies the lower right third, slightly overlapping the layout",
  "color_palette": ["white", "pastel lavender", "soft lilac", "pale gray-violet", "touches of pastel blue-pink gradient"],
  "constraints": {
    "must_keep": [
      "6 件商品风格统一（同色系 + 同质感倾向）",
      "角色出现在固定位置不抢主体",
      "整体像 SNS 可分享的精致 catalog"
    ],
    "avoid": [
      "商品堆叠杂乱无 grid",
      "字体太多种类（建议日文手写 + 一种主标题字体即可）",
      "把角色画太大反客为主"
    ]
  }
}
```

### 何时选这个变体

- 用户做的是「我房间里有什么」「IP 同款杂货」类企划
- 强调氛围 / 生活方式 > 商业 / 出道
- 适合 SNS 分享、不需要 logo 系统 / 包装 mockup

## 主模板 3：极简版（角色 + 4-6 件周边 + logo）

适合资源有限、只想做单一 IP 上新公告的场景。

📝 提示词

```json
{
  "type": "minimal character merch announcement",
  "sections": [
    "top: large main logo + character close-up",
    "middle: 4-6 merchandise items in a grid",
    "bottom: SNS handle + release date + 1 line tagline"
  ],
  "vibe": "{argument name=\"vibe\" default=\"clean, premium, focus on products\"}",
  "merch_count": 6,
  "must_keep": ["商品摄影质感统一", "logo 与 SNS handle 拼写一致"]
}
```

### 何时选这个变体

- 没有时间做 6-8 个 section
- 只想强调"角色 + 周边 + 上新时间"
- 想做"洁净简约"风而非"信息量爆炸"风

## 避免事项

- ❌ 在不同 section 中改变角色的发型 / 配色 / 服装 base → 视觉立刻不像「同一 IP」
- ❌ 把 6 件商品画成同一样东西复制 → 必须有材质 / 形状 / 用途差异
- ❌ logo 在 header 与 web banner 中字体不一致
- ❌ SNS profile 区的 follow 按钮和角色 IP 主色冲突
- ❌ 周边商品 mockup 出现透视错误（如 mug 椭圆变扁、T 恤褶皱不自然）
- ❌ 包装 mockup 的"透明窗"画成纯贴图而非真实折射
- ❌ 全图配色 ≥ 5 个主色调 → 失去 IP 一致性，应控制在 2-3 主色 + 1-2 accent
