# 中式电商一图全销售看板模板

本文件用于生成"一张超大竖图，把电商平台主图 + 详情页 + 卖点 + 使用步骤 + 场景 + 包装信息 + TVC 分镜全部塞进同一张图"的复合销售视觉。

典型用途：

- 淘宝 / 天猫 / 京东详情页主推位「上架前一图过审」
- 抖音 / 快手电商详情页竖屏单图
- 招商提案 / 客户审稿一图概览
- 卖家做新品全套素材的"母版"，后续切割成主图 / 详情页 / 视频脚本
- 跨境电商对内传达「一份完整产品营销策略」

特征（与现有 product-visuals 模板的区别）：

| 模板 | 信息密度 | 功能 |
|---|---|---|
| `white-background-product.md`（已有） | 低 | 单品多角度纯白底 |
| `premium-studio-product.md`（已有） | 中 | 高级影棚商业大片 |
| `lifestyle-product-scene.md`（已有） | 中 | 生活方式场景 |
| `packaging-showcase.md`（已有） | 中 | 礼盒 / 包装展示 |
| `exploded-view-poster.md`（已有） | 高 | 产品爆炸视图 + callout |
| **本模板**（新增） | **极高** | **5-7 个销售模块 + TVC 分镜表全在一张图** |

**关键区别**：本模板不是"产品视觉海报"，而是"详情页 + 主图 + 卖点 + 使用 + 场景 + 视频脚本的设计 master 看板"。

## 适用范围

- 中式电商详情页全套设计 master 看板
- 新品上线一图过审稿
- 卖家「招商 + 审稿 + 内传」全场景使用
- 食品 / 美妆 / 日用 / 健康类（信息密度高的品类）
- 「主图 + 详情页 + 视频脚本」一体化提案

## 何时使用

- 用户提到"详情页设计 / 电商主图 + 详情页一起 / 一图过审 / 全套销售看板"
- 用户希望出"包含使用步骤 + 场景 + TVC 分镜"的复合视觉
- 中式电商食品 / 美妆 / 母婴 / 日用品类（信息密度天然高）

不要使用：

- 单品白底主图 → 用 `white-background-product.md`
- 高级商业大片 → 用 `premium-studio-product.md`
- 仅 TVC 9 格分镜 → 用 `storyboards-and-sequences/product-tvc-storyboard.md`
- 海外 e-commerce 单图（信息密度低）→ 用 `product-card-overlay.md` 或 `banner-hero.md`

## 缺失信息优先提问顺序

1. 产品类目 + 品牌 + 产品名（必问，是看板的灵魂）
2. 包装外观（外盒颜色 / 字体 / logo / 内含物）
3. 配色基调（暗色奢华食品 / 浅色清爽美妆 / 暖色母婴 / 冷色科技）
4. 必须出现的核心卖点（4-6 条，决定中部 feature panel 内容）
5. 使用方式 / 冲泡步骤（决定 HOW TO MAKE 区域）
6. 应用场景（早餐 / 办公 / 健身 / 睡前 等 4 选）
7. 是否需要底部 TVC 分镜表（默认是）

## 主模板：5+1 模块电商一图全销售看板

📖 描述

竖版超长画布，分上 / 中 / 下 + 底部分镜表四大区，包含 5 个销售模块 + 1 个 TVC 分镜带。

📝 提示词

```json
{
  "type": "Chinese e-commerce product marketing board",
  "goal": "生成一张同时包含主图 / 详情页 / 卖点 / 使用步骤 / 场景 / 携带便利 / TVC 分镜的复合销售看板，可作为详情页 master / 招商稿 / 卖家内传素材",
  "product": {
    "category": "{argument name=\"product category\" default=\"instant grain powder drink\"}",
    "brand": "{argument name=\"brand\" default=\"五谷磨房\"}",
    "name": "{argument name=\"product name\" default=\"核桃芝麻黑豆粉\"}",
    "packaging": "{argument name=\"packaging description\" default=\"matte black retail box with gold Chinese typography and a large swirling bowl graphic on the front, plus individual black sachets inside\"}",
    "net_weight": "{argument name=\"net weight\" default=\"320g (32g×10袋)\"}"
  },
  "style": {
    "overall": "{argument name=\"overall style\" default=\"premium dark food advertising layout\"}",
    "color_palette": ["black", "deep brown", "warm gold", "beige", "walnut brown"],
    "lighting": "dramatic studio lighting with glossy highlights and warm rim light",
    "mood": "{argument name=\"mood\" default=\"luxurious, nourishing, healthy, appetizing\"}"
  },
  "layout": {
    "format": "single tall composite board divided into 5 major sections plus a bottom storyboard table",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"portrait, approximately 9:16\"}",
    "grid": "top area split into left main image and right detail page; middle area split into preparation guide and feature panel; lower area split into lifestyle scenarios and sachet carry section; bottom is a full-width tabular storyboard",
    "sections": [
      {
        "title": "主图 / Main image",
        "position": "top-left",
        "count": 8,
        "labels": [
          "{argument name=\"brand\" default=\"五谷磨房\"}",
          "{argument name=\"product name\" default=\"核桃芝麻黑豆粉\"}",
          "32g×10袋 独立包装",
          "{argument name=\"main keyword 1\" default=\"五黑谷物\"}",
          "{argument name=\"main keyword 2\" default=\"香浓醇厚\"}",
          "{argument name=\"main keyword 3\" default=\"独立小袋\"}",
          "{argument name=\"main keyword 4\" default=\"即冲即饮\"}",
          "product box and drink cup hero composition"
        ]
      },
      {
        "title": "详情页 / Details page",
        "position": "top-right",
        "count": 5,
        "labels": ["{argument name=\"ingredient 1\" default=\"黑芝麻\"}", "{argument name=\"ingredient 2\" default=\"黑豆\"}", "{argument name=\"ingredient 3\" default=\"黑米\"}", "{argument name=\"ingredient 4\" default=\"核桃\"}", "{argument name=\"ingredient 5\" default=\"谷物粉\"}"]
      },
      {
        "title": "{argument name=\"feature title\" default=\"香浓细腻 顺滑好喝\"}",
        "position": "mid-right",
        "count": 4,
        "labels": [
          "{argument name=\"feature 1\" default=\"一冲即饮 营养美味\"}",
          "{argument name=\"feature 2\" default=\"粉质细腻 Fine powder\"}",
          "{argument name=\"feature 3\" default=\"浓香醇厚 Rich & Smooth\"}",
          "{argument name=\"feature 4\" default=\"营养代餐 Nutritious\"}"
        ]
      },
      {
        "title": "{argument name=\"how to title\" default=\"冲泡方式 HOW TO MAKE\"}",
        "position": "mid-left lower",
        "count": 3,
        "labels": [
          "{argument name=\"step 1\" default=\"1 倒入一袋粉(32g)\"}",
          "{argument name=\"step 2\" default=\"2 加入200ml 热水或牛奶\"}",
          "{argument name=\"step 3\" default=\"3 搅拌均匀 即可享用\"}"
        ]
      },
      {
        "title": "{argument name=\"scenario title\" default=\"一杯好谷物 轻松好生活\"}",
        "position": "lower-left",
        "count": 4,
        "labels": [
          "{argument name=\"scenario 1\" default=\"元气早餐\"}",
          "{argument name=\"scenario 2\" default=\"办公室下午茶\"}",
          "{argument name=\"scenario 3\" default=\"健身代餐\"}",
          "{argument name=\"scenario 4\" default=\"睡前暖饮\"}"
        ]
      },
      {
        "title": "{argument name=\"convenience title\" default=\"独立小袋 随身携带\"}",
        "position": "lower-right",
        "count": 3,
        "labels": ["独立小袋 便携卫生", "锁住新鲜 防潮防氧化", "1袋1杯 精准份量"]
      },
      {
        "title": "视频推广广告 / TVC 视频提示词 + 分镜头脚本",
        "position": "bottom full width",
        "count": 7,
        "labels": [
          "镜头1 开场-产品展示",
          "镜头2 食材特写",
          "镜头3 倒粉入杯",
          "镜头4 冲泡搅拌",
          "镜头5 饮用场景",
          "镜头6 产品卖点",
          "镜头7 结尾口号"
        ]
      }
    ]
  },
  "scene_elements": {
    "ingredients": [
      { "name": "{argument name=\"ingredient 1\" default=\"black sesame\"}", "form": "small black seeds in a round bowl" },
      { "name": "{argument name=\"ingredient 2\" default=\"black beans\"}", "form": "glossy whole beans in a round bowl" },
      { "name": "{argument name=\"ingredient 3\" default=\"black rice\"}", "form": "dark long grains in a round bowl" },
      { "name": "{argument name=\"ingredient 4\" default=\"walnuts\"}", "form": "walnut halves in a round bowl" },
      { "name": "{argument name=\"ingredient 5\" default=\"grain powder\"}", "form": "light beige powder in a round bowl" }
    ],
    "serving": {
      "drink": "{argument name=\"drink description\" default=\"thick gray-brown sesame walnut bean beverage with smooth surface swirl\"}",
      "cup": "transparent glass cup with handle",
      "utensil": "metal spoon stirring or resting inside drink"
    },
    "supporting_props": ["walnuts on table", "scattered black beans", "grain stalks or wheat stems", "dark tabletop", "ingredient bowls", "open package showing 5 visible sachets"]
  },
  "text_treatment": {
    "headline_font": "bold elegant Chinese display type in metallic gold",
    "body_font": "clean sans serif Chinese with occasional English subtitles",
    "accent": "thin gold divider lines and circular ingredient frames"
  },
  "camera_and_composition": {
    "product_shots": "front-facing hero box, angled sachet display box, close-up beverage macro",
    "food_photography": "high-detail commercial food styling, shallow depth of field, crisp texture emphasis"
  },
  "quality": "ultra-detailed commercial design mockup, polished e-commerce key visual plus details page plus ad storyboard, 4K",
  "constraints": {
    "must_keep": [
      "5 个销售模块 + 1 个 TVC 分镜带都必须出现且可识别",
      "每个模块有自己的小标题 + 编号或图标",
      "包装 / 商品在不同模块中保持一致外观",
      "中文文案在主标 / 副标 / 卖点 hierarchy 清晰"
    ],
    "avoid": [
      "把详情页区画成纯文字（必须有原料图 / icon）",
      "5 个模块之间没有视觉边界",
      "TVC 分镜带画成文字列表而非缩略图 + 标注",
      "把所有文案叠到主图区导致主图不像主图",
      "原料 / 商品在不同区域改变包装颜色"
    ]
  }
}
```

### 参数策略

- **必问**：product brand + name、packaging description、5 个原料 / 成分 / 卖点关键词
- **可默认**：style overall（按品类自动）、scenario / step / feature 文案（按品类自动套话术）
- **可随机**：supporting props 细节、TVC 7 镜头具体文案

### 自动补全策略

- 用户只说"做一个 XX 的电商详情页一图全套"→ 默认按食品 / 美妆 / 母婴自动选 dark / light / warm 色系
- 没指定原料 5 项 → 按产品品类自动列（如奶粉 → 5 种奶源；护肤 → 5 种成分；健身代餐 → 5 种谷物）
- 没指定 TVC 镜头 → 用模板里的 7 镜头标准结构

## 变体 1：浅色清爽美妆 / 护肤板（替换风格）

📝 提示词

```json
{
  "type": "Chinese e-commerce skincare product marketing board",
  "style_override": {
    "overall": "clean light premium beauty layout",
    "color_palette": ["off-white", "soft beige", "rose gold", "pastel pink", "champagne"],
    "lighting": "bright airy soft daylight with subtle highlights",
    "mood": "fresh, clean, hydrating, premium"
  },
  "section_replacements": {
    "ingredients_section": "5 active ingredient icons (玻尿酸 / 烟酰胺 / 神经酰胺 / 视黄醇 / VC)",
    "feature_section": "4 efficacy claims (保湿 / 美白 / 抗皱 / 修护)",
    "scenario_section": "4 use moments (晨间 / 通勤 / 妆前 / 夜间修护)",
    "how_to_section": "3-step routine (洁面 → 涂抹 → 按摩)"
  }
}
```

### 何时选这个变体

- 美妆 / 护肤 / 个护品类
- 客户要"日系清爽 / 韩系治愈"风
- 不需要食品类的"暗色 + 金"奢华感

## 变体 2：母婴 / 儿童 / 暖色系

📝 提示词

```json
{
  "type": "Chinese e-commerce baby/child product marketing board",
  "style_override": {
    "overall": "warm friendly child-safe layout with rounded corners and soft illustrations",
    "color_palette": ["cream", "soft yellow", "baby blue", "pastel pink", "wood brown"],
    "lighting": "warm natural daylight, gentle shadows",
    "mood": "safe, gentle, healthy, trustworthy"
  },
  "extra_section": {
    "title": "妈妈放心 / 安全认证",
    "elements": ["欧盟认证", "无添加", "0 防腐剂", "宝宝可用"]
  }
}
```

### 何时选这个变体

- 母婴 / 儿童 / 孕产品类
- 必须强调「安全 / 认证 / 无添加」
- 暖色 + 圆润视觉

## 变体 3：3C / 数码 / 工具品类（少文字 + 多技术参数）

📝 提示词

```json
{
  "type": "Chinese e-commerce 3C / digital product marketing board",
  "style_override": {
    "overall": "tech minimal dark layout with neon accents",
    "color_palette": ["matte black", "graphite", "cyan", "white"],
    "mood": "high-tech, precise, professional"
  },
  "section_replacements": {
    "ingredients_section": "spec table (CPU / RAM / Battery / Connectivity / Weight)",
    "feature_section": "4 tech feature pills with icons",
    "scenario_section": "4 user scenarios (办公 / 出差 / 创作 / 游戏)",
    "how_to_section": "skip; replace with 6 product angle close-ups"
  }
}
```

### 何时选这个变体

- 数码 / 工具 / 电子产品
- 客户希望"少抒情 + 多参数 + 强科技感"

## 避免事项

- ❌ 把所有 5+1 模块挤在 1:1 方图里 → 必须用 9:16 / 3:4 长图才装得下
- ❌ 主图区写满文字 → 主图就是主图，文字应在卖点区
- ❌ 模块之间没有视觉边界（线 / 色块 / 留白）→ 整图变成糊一团
- ❌ TVC 分镜带画成纯文本列表 → 必须有 7 张 thumbnail 缩略图 + 编号 + 标题
- ❌ 包装 / 商品在不同模块改变颜色 / 字体 → 一致性是这类看板的命脉
- ❌ 配色 ≥ 6 主色 → 必须控制在 3-4 主色 + 1 accent
- ❌ 全图字体 ≥ 4 种 → 标题 + 正文 + 1 个手写 accent 即可
- ❌ 让模型"自己想 5 个原料" 而你的产品确实有特定成分 → 必须在 prompt 中明确列出
