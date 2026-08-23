# 仿生 / 工业设计概念海报模板

本文件用于生成"自然原型 → 抽象 → 工业产品"的概念设计海报，把生物形态、演化推导、最终产品 hero 渲染、多视图技术图、品牌文案全部组合成一张概念展板。

典型用途：

- 仿生工业设计概念稿（飞行器 / 汽车 / 机器人 / 家电 / 鞋类）
- 设计师 / 学生作品集封面
- 创业公司 demo day "我们怎么从灵感走到产品"展示
- 学院派工业设计课程 deliverable
- 速度感 / 效率类品牌的视觉宣言海报
- 速速 sketch → 蓝图 → 渲染 全流程演示

特征（与现有 poster 模板的区别）：

| 模板 | 用途 |
|---|---|
| `brand-poster.md`（已有） | 品牌主海报（产品 / 人物 / 文字主张） |
| `campaign-kv.md`（已有） | Campaign KV + 衍生 layout 系统 |
| `banner-hero.md`（已有） | Web hero / 落地页横向构图 + CTA |
| `editorial-cover.md`（已有） | 杂志 / 期刊封面 |
| **本模板**（新增） | **工业设计概念海报：原型 → 演化 → hero → 多视图技术图** |

## 适用范围

- 仿生工业设计（manta / shark / falcon / leaf / honeycomb 启发）
- 概念产品介绍海报
- 学生 / 设计师作品集封面
- 「灵感 → 产品」的视觉叙事
- 高端制造 / 航空 / 汽车 / 户外品类

## 何时使用

- 用户提到"仿生 / 概念设计 / 工业设计 / 演化推导 / 灵感来源"
- 想做"从生物原型到最终产品"的视觉故事
- 需要 hero 渲染 + 多视图技术图 + 设计推导一图全包

不要使用：

- 单纯产品广告海报 → 用 `brand-poster.md` 或 `product-visuals/premium-studio-product.md`
- 学术论文 figure → 用 `academic-figures/method-pipeline-overview.md`
- 用户调研 / 需求分析海报 → 用 `slides-and-visual-docs/visual-report-page.md`

## 缺失信息优先提问顺序

1. 产品类型 + 名字（飞行器 SKYRAY / 鞋 SHARK SOLE / 椅 LEAF CHAIR）
2. 仿生原型（魟鱼 / 鲨鱼 / 树叶 / 蜂巢 / 龙虾…）
3. 风格基调（**black + cyan 高科技 / 米白 + 黑铁线稿 / 暖木色 + 自然 / 复古蓝图**）
4. 是否需要演化条（5 阶段灵感 → 产品）
5. 是否需要技术多视图（top / side / front / rear / underside / detail）
6. tagline / footer body text
7. 比例（默认竖版 3:4）

## 主模板：仿生概念产品海报

📖 描述

竖版海报 / 横版展板，分 5 个区：header（emblem + 名 + tagline）+ evolution strip（5 阶段推导）+ hero render（中央 3D）+ technical views grid（6 视图）+ footer body text。

📝 提示词

```json
{
  "type": "biomimetic concept design poster",
  "goal": "生成一张「自然原型 → 推导 → hero → 多视图」的概念产品展板，可作为设计提案 / 作品集封面 / demo day 海报",
  "subject": {
    "vehicle_or_product": "{argument name=\"product type\" default=\"futuristic aircraft concept\"}",
    "name": "{argument name=\"product name\" default=\"SKYRAY\"}",
    "inspiration": "{argument name=\"animal inspiration\" default=\"stingray\"}",
    "design": "{argument name=\"design description\" default=\"blended-wing-body aircraft shaped like a manta ray, wide triangular planform, smooth organic curves, sharp pointed nose, slightly raised central spine, tapered wing tips curling subtly upward, dark graphite-black metallic skin with fine panel lines and faint blue illuminated accents along edges and seams\"}"
  },
  "style": {
    "mood": "{argument name=\"mood\" default=\"premium futuristic industrial design presentation\"}",
    "rendering": "{argument name=\"rendering\" default=\"hyper-detailed cinematic 3D concept art mixed with blueprint visualization\"}",
    "color_palette": "{argument name=\"color palette\" default=\"black, charcoal, gunmetal, silver, deep ocean blue, electric cyan highlights\"}",
    "lighting": "{argument name=\"lighting\" default=\"low-key dramatic studio lighting with glossy reflections, cool rim light, subtle underwater ambience in the top inspiration strip\"}"
  },
  "layout": {
    "background": "{argument name=\"background\" default=\"full black poster with faint technical grid lines and soft vignetting\"}",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4 portrait poster\"}",
    "sections": [
      {
        "title": "header",
        "position": "top",
        "count": 3,
        "labels": ["emblem mark", "{argument name=\"product name\" default=\"SKYRAY\"}", "{argument name=\"tagline\" default=\"INSPIRED BY THE SEA. ENGINEERED FOR THE SKY.\"}"]
      },
      {
        "title": "evolution strip",
        "position": "upper middle",
        "count": 5,
        "labels": [
          "{argument name=\"evo 1\" default=\"realistic stingray underwater at far left\"}",
          "{argument name=\"evo 2\" default=\"top-view biological stingray study\"}",
          "{argument name=\"evo 3\" default=\"abstract aerodynamic line sketch\"}",
          "{argument name=\"evo 4\" default=\"faceted aircraft blueprint transition drawing\"}",
          "{argument name=\"evo 5\" default=\"final sleek aircraft concept at far right\"}"
        ]
      },
      {
        "title": "hero render",
        "position": "center",
        "count": 1,
        "labels": ["large three-quarter view of the {argument name=\"product type\" default=\"aircraft\"}"]
      },
      {
        "title": "technical views grid",
        "position": "lower middle",
        "count": 6,
        "labels": ["TOP", "SIDE", "FRONT", "REAR", "UNDERSIDE", "DETAIL"]
      },
      {
        "title": "footer text",
        "position": "bottom",
        "count": 1,
        "labels": [
          "{argument name=\"body text\" default=\"A biomimetic high-speed aircraft concept shaped by the hydrodynamic elegance of the stingray. Its blended wing body, low-drag silhouette, and fluid control surfaces translate ocean-born efficiency into atmospheric performance.\"}"
        ]
      }
    ],
    "technical_views": {
      "TOP": "top orthographic view with measurement ticks",
      "SIDE": "thin side profile with long smooth belly curve",
      "FRONT": "front orthographic view emphasizing broad wingspan and central cockpit hump",
      "REAR": "rear orthographic view showing narrow tail end and wing sweep",
      "UNDERSIDE": "underside three-quarter view",
      "DETAIL": "close-up crop of metallic skin, seam lines, and glowing blue edge strip"
    }
  },
  "graphics": {
    "logo": "{argument name=\"logo description\" default=\"minimal four-point symmetrical emblem above title, resembling a stylized ray silhouette\"}",
    "arrows": "4 thin cyan arrows connecting the 5 stages in the evolution strip",
    "typography": "widely spaced modern sans-serif uppercase text, clean luxury-tech branding"
  },
  "camera": {
    "hero_render": "slightly elevated front-left three-quarter angle",
    "technical_views": "orthographic",
    "inspiration_image": "{argument name=\"inspiration camera\" default=\"underwater side angle with light rays from above\"}"
  },
  "quality": "ultra-clean, polished, high contrast, sharp, poster-ready, concept design board for {argument name=\"industry\" default=\"aerospace\"} branding or speculative industrial design",
  "constraints": {
    "must_keep": [
      "5 阶段演化条从左到右逻辑清晰（生物 → 抽象 → 产品）",
      "hero render 占据视觉中心 ≥ 35% 高度",
      "6 个 technical view 角度齐全且产品形态一致",
      "header / footer 排版对齐 hero 中轴线",
      "整体配色不超过 4 主色 + 1 accent"
    ],
    "avoid": [
      "演化条画成 5 张同一姿态的照片（应有从写实 → 抽象的递进）",
      "技术视图比例失调（top / front / rear 必须正交准确）",
      "hero 与技术视图中产品形态漂移",
      "footer body text 写得太长 → 应控制在 2-3 句",
      "把 emblem / logo 放成大图 → 应该是小型徽章",
      "用过多霓虹色破坏工业感"
    ]
  }
}
```

### 参数策略

- **必问**：product type + name、animal/biological inspiration、industry
- **可默认**：tagline、background、color palette
- **可随机**：evolution 5 阶段具体描述、technical views detail crop

### 自动补全策略

- 用户给出"产品 + 灵感"→ 自动按"生物 → 解剖 → 抽象 → 工业 → 成品"5 步推导
- 不指定 industry → 按产品类型自动归类（飞行器=aerospace；鞋=footwear；椅=furniture）
- 不指定颜色 → 按 industry 推荐（aerospace=black+cyan；footwear=white+orange；furniture=warm wood+cream）

## 变体 1：复古蓝图风（cream paper + ink）

📝 提示词

```json
{
  "type": "biomimetic concept poster vintage blueprint edition",
  "style_override": {
    "background": "aged cream blueprint paper with subtle stains and grid",
    "color_palette": "navy ink, dark sepia, faded brown, no neon",
    "rendering": "fine ink linework + stippled engraving + vintage drafting style",
    "mood": "Leonardo da Vinci notebook meets industrial blueprint"
  },
  "extra_elements": ["handwritten margin notes", "small wax seal stamp", "ruler tick marks along edges"]
}
```

### 何时选这个变体

- 强调「设计哲学 / 文艺复兴感」
- 教育 / 出版 / 文创品牌
- 反差点：用复古手感呈现未来产品

## 变体 2：自然色调（暖木 + 米白，适合家居 / 鞋 / 椅）

📝 提示词

```json
{
  "type": "biomimetic concept poster organic warm edition",
  "style_override": {
    "background": "warm off-white textured paper with subtle plant shadows",
    "color_palette": "cream, beige, warm wood, sage green, soft black",
    "rendering": "soft 3D render + photograph composite",
    "mood": "biophilic design, sustainability, calm premium"
  }
}
```

### 何时选这个变体

- 家居 / 椅 / 鞋 / 餐具 类
- 强调可持续 / 环保 / 自然亲和
- 不希望冷酷的"工业感"

## 变体 3：横版三联画（左灵感 / 中产品 / 右技术）

适合横屏展示 / agency 提案稿 hero 图。

📝 提示词

```json
{
  "type": "biomimetic concept poster horizontal triptych",
  "layout_override": {
    "format": "horizontal poster, 16:9 or 21:9",
    "structure": "3 vertical panels: left = biological inspiration column, center = hero product render, right = technical views stack",
    "evolution_strip": "vertical thin strip on the far left edge, 5 stages stacked top-to-bottom"
  },
  "use_case": "横屏 deck / agency 提案首页 / Behance project cover"
}
```

### 何时选这个变体

- 横屏展示渠道
- 设计师 case study 项目封面
- 演讲 / 提案稿首页

## 避免事项

- ❌ 演化条 5 阶段都是「最终产品的不同角度」→ 必须有「生物 → 抽象 → 产品」递进
- ❌ hero 与技术视图中产品的轮廓 / 比例不一致
- ❌ technical views 6 张全是渲染图 → 至少 4 张应该是正交线稿，1 张是材质 detail crop
- ❌ footer text 写成营销语 → 应该是设计哲学 / 工程描述
- ❌ 用动漫 / 卡通风格画工业产品（应使用 hyperreal 3D 或 blueprint）
- ❌ 把 emblem / logo 放成大字 → 应该是 ≤ headline 1/3 大小的小型徽章
- ❌ 全图使用 6 种以上颜色（应控制在 3-4 主色 + 1 accent）
