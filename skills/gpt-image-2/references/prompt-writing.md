# JSON 提示词模板总规范

本文件是 `gpt-image-2` skill 的模板方法论总文档。后续所有具体模板文件都应尽量遵守这里的规则。

它不提供某个具体视觉场景的完整模板，而是定义：

- 模板应该如何组织
- 字段应该如何设计
- 参数如何区分为“必问 / 默认 / 随机”
- 缺失信息应该如何提问
- 如何从案例提炼出可复用的结构化 JSON 模板

---

# 一、何时使用 JSON 模板

当任务满足以下任一条件时，优先使用 JSON 模板，而不是直接写一整段自然语言提示词：

1. 画面元素很多
2. 画面包含多个功能区域
3. 需要 UI / 商品卡 / 评论区 / 图例 / 标注 / 页眉页脚等结构
4. 需要支持多个变体
5. 需要支持“用户指定 / 默认值 / 随机生成”三种模式
6. 后续很可能复用、扩写或调试

典型适用场景：

- 电商直播 UI 样机
- 产品爆炸视图海报
- 手绘城市地图
- 讲解型 Slides
- 高信息密度说明图

不必强行使用 JSON 模板的场景：

- 很简单的单主体图
- 没有复杂布局和多区域结构
- 用户只想快速试一个很轻量的视觉方向

---

# 二、references 的目录规则

`references/` 必须采用：

- 一级：分类目录
- 二级：单模板 Markdown 文件

例如：

```text
references/
  ui-mockups/
    live-commerce-ui.md
    social-interface-mockup.md
  product-visuals/
    exploded-view-poster.md
```

不要继续采用：

- 一个大类一个大文件
- 一个来源一个文件
- 一个案例一个没有分类的平铺文件

目录树的好处：

- 精准读取
- 易于扩展
- 模板互不污染
- 每个模板文件可以写得很完整

---

# 三、单模板文件的标准结构

每个具体模板文件建议遵循以下结构：

```markdown
# 模板名称

## 适用范围

## 何时使用

## 缺失信息优先提问顺序

## 主模板

📖 描述

📝 提示词
```json
{ ... }
```

### 参数策略

### 自动补全策略

### 变体方式

## 变体 1

## 变体 2

## 避免事项
```

说明：

- `主模板` 必须先有
- 变体模板建立在主模板之上
- 参数策略、自动补全策略、避免事项不能省略

---

# 四、JSON 模板的推荐骨架

大多数模板建议优先从以下骨架开始：

```json
{
  "type": "模板类型",
  "goal": "图像用途",
  "subject": {},
  "scene": {},
  "layout": {},
  "style": {},
  "details": {},
  "constraints": {}
}
```

## 字段职责

### `type`

模板类型名称，例如：

- 直播 UI 样机
- 产品爆炸视图海报
- 手绘地图信息图

### `goal`

说明这张图最终要干什么，例如：

- 电商直播截图样机
- 品牌主视觉海报
- 旅游攻略地图
- 高信息密度讲解图

### `subject`

主体内容，例如：

- 人物
- 商品
- 城市
- 角色
- 插画主角

### `scene`

场景、背景、环境、氛围。

### `layout`

画面区域组织方式，适用于：

- 海报
- UI
- 地图
- slides
- 多区域结构图

### `style`

风格、渲染、材质、色彩倾向、光线。

### `details`

用于装载局部细节，例如：

- 商品卖点
- callout labels
- 评论内容
- 图例元素
- 页脚文案

### `constraints`

用于明确：

- 必须出现什么
- 必须避免什么
- 最终结果更像什么、不像什么

---

# 五、场景特有字段建议

不同分类下可扩展不同结构。

## 5.1 UI Mockups

建议额外使用：

```json
{
  "ui_overlay": {
    "top_header": {},
    "chat_area": {},
    "gift_area": {},
    "product_card": {},
    "bottom_bar": {}
  }
}
```

## 5.2 Product Visuals

建议额外使用：

```json
{
  "header": {},
  "centerpiece": {},
  "callout_labels": {},
  "footer": {},
  "component_layers": []
}
```

## 5.3 Maps & Infographics

建议额外使用：

```json
{
  "title_section": {},
  "sections": [],
  "legend": {},
  "centerpiece": {},
  "extras": {}
}
```

## 5.4 Slides & Visual Docs

建议额外使用：

```json
{
  "page_type": "",
  "information_density": "",
  "headline_system": {},
  "visual_blocks": [],
  "annotation_style": {}
}
```

## 5.5 Storyboards & Sequences（电影分镜 / TVC / 流程板 / 漫画）

适用于「同一条叙事 / 同一个流程 / 同一组动作」按 N×M 网格输出多个 panel 的视觉。子类彼此之间字段差异大，按子类分别给字段建议：

### 5.5.1 电影 / 短片 cinematic 分镜（如 `cinematic-storyboard-grid.md`）

```json
{
  "subject": { "primary": "", "secondary": "", "mood": "", "style": "", "aspect_ratio_per_panel": "" },
  "vehicle_or_actor": { "design": "", "scale": "" },
  "layout": {
    "grid": { "rows": 0, "columns": 0, "count": 0 },
    "sheet_aspect_ratio": "",
    "panel_borders": "",
    "sections": [{ "position": "row x col y", "description": "" }],
    "continuity": "(必填) 显式声明 N 个 panel 是连续叙事 / 同一 hero / 同一 mood"
  },
  "lighting": { "primary": "", "secondary": "", "accents": "" },
  "environment": { "location": "", "weather": "", "threat": "" }
}
```

字段经验：

- `sections` 必须是数组，**严格按 row-major 顺序列出每镜**（不要让模型自由排列）
- `continuity` 是该子类的关键字段，**必填**
- 每镜描述要包含「景别 + 主体动作 + 光线 / 情绪」三要素
- 远 / 中 / 近 / POV 镜头要混搭，不要全特写或全远景

### 5.5.2 商业广告 TVC 分镜（如 `product-tvc-storyboard.md`）

```json
{
  "header": { "title": "", "subtitle_meta": "", "product_name_subtitle": "" },
  "layout": { "grid": { "rows": 0, "columns": 0, "panel_count": 0, "panel_aspect_ratio": "" } },
  "scenes": {
    "count": 0,
    "items": [{ "id": 1, "title_zh": "", "timestamp": "0-2s", "description": "" }]
  }
}
```

字段经验：

- 与电影分镜相比，必须有 `header.product_name_subtitle` + 每镜 `timestamp`（广告强约束）
- 每镜 `title_zh` 是面向客户的中文小标题（如「环境建立」「特写出镜」「人货同框」）
- `description` 必须**显式包含产品**，且产品在所有镜中外观一致

### 5.5.3 真人 / 角色 cinematic 流程板（如 `process-photo-board.md`）

```json
{
  "subject": {
    "character": { "gender": "", "age": "", "identity": "", "hair": "", "undersuit": "", "armor_or_outfit": "", "helmet_or_headpiece": "" },
    "environment": { "location": "", "background_elements": "" }
  },
  "layout": {
    "header": { "count": 2, "labels": ["title", "subtitle"], "design": "" },
    "sections": [{ "step_id": 1, "title": "", "position": "", "labels": [], "image": "" }],
    "footer": { "count": 1, "labels": ["slogan"], "design": "" },
    "grid": { "rows": 0, "columns": 0, "panel_count": 0, "panel_borders": "", "number_badges": "" }
  },
  "text_rendering": { "language": "", "font": "", "colors": "" }
}
```

字段经验：

- **角色一致性**靠把所有 fixed attributes（gender / hair / undersuit）独立成 `subject.character` 字段
- **状态递进**靠每 step 的 `image` 字段显式描述「此时已穿什么 / 正在做什么」
- 必须有 `number_badges` 字段（步骤号在视觉上一眼可识别）
- 标题语言（中 / 日 / 英）通过 `text_rendering.language` 显式声明

## 5.6 Catalog / Lineup / Character-Variant Poster（多卡片信息图海报）

适用于「同一基底（角色 / 产品 / 概念）多个变体在一张海报里并列展示」的视觉。子类：

### 5.6.1 同角色多版本海报（如 `character-catalog-poster.md`）

```json
{
  "subject_overview": "(必填) 全图主题，如 '十二星座女子图鉴'",
  "language": "",
  "format": "vertical poster",
  "style": { "overall": "", "rendering": "", "mood": "" },
  "layout": {
    "sections_count": 0,
    "sections": [{
      "title": "",
      "position": "",
      "theme_color": "(必填) 该 panel 的主题色，必须 panel 间各不相同",
      "symbol": "",
      "constellation": "",
      "labels": [],
      "character": { "pose": "", "outfit": "", "background": "" }
    }]
  }
}
```

字段经验：

- 每 section 必须有自己的 `theme_color` + `symbol` + `motif`，否则会被模型画成同一张
- `character` 子字段保留同一基底（脸型 / 体型 / 发色），仅变化 outfit / pose / background
- `subject_overview` 是模型理解 "为什么这些 panel 要放在一起" 的关键提示

### 5.6.2 系列产品 lineup 对比海报（如 `lineup-comparison-poster.md`）

```json
{
  "subject": "(必填) 描述一句包含 'lineup chart / catalog board / comparison poster'",
  "branding": { "headline": "", "signature": "", "seals": [] },
  "palette": { "background": "", "highlights": [] },
  "layout": {
    "header": { "elements": [{ "type": "legend", "title": "", "labels": [] }] },
    "sections": [{ "title": "row N tier name", "labels": [] }]
  },
  "content_grid": "显式说明每行多少 SKU、每 SKU 是什么样的卡片",
  "visual_details": "材质 / 反光 / 印花 / 配件等让 SKU 之间彼此不同的细节"
}
```

字段经验：

- 必须有 `legend` 类元素（等级 key / 图标 key / 风格 key），否则海报"对比"意味就消失
- `content_grid` 字段必须显式给「每行 N 个 SKU + 行内排序逻辑（按价 / 按色 / 按年代）」
- SKU 数量通常 12 - 36，过少不像 lineup，过多每个会被画糊

## 5.7 Day-trip Itinerary Map（左行程卡 + 右画面地图 split 海报）

适用于"一日游 split 海报"（如 `itinerary-day-trip-map.md`）：

```json
{
  "destination": { "name": "", "duration": "1 day", "theme": "" },
  "headline": { "main": "", "tagline": "", "divider": "" },
  "style": { "overall": "", "left_panel_look": "", "right_panel_look": "", "color_palette": "", "atmosphere": "" },
  "layout": {
    "format": "vertical 2:3 poster, split into two equal vertical columns",
    "left_panel": { "type": "itinerary card", "header": [], "stop_count": 5, "stop_design": [], "border": "" },
    "right_panel": { "type": "painted map scene", "background": "", "path": "", "marker_design": "", "compass_rose": "", "stats_box": "" },
    "alignment_rule": "(必填) 左右编号 / 名称 / 顺序必须严格对齐"
  },
  "stops": {
    "count": 5,
    "items": [{ "number": 1, "name": "", "time": "", "description": "", "left_vignette": "", "right_scene": "" }]
  },
  "footer_box": { "compass_rose": "", "stats_box": { "design": "", "stats": [] } }
}
```

字段经验：

- `alignment_rule` **必填**，否则左右两栏极易错位
- 每 stop 同时给 `left_vignette`（卡片小插画）+ `right_scene`（地图大场景）双视觉
- `stops.count` 建议 5-7，过少不像行程，过多卡片塞不下
- `language` 默认与目的地官方语言一致（台湾 → 繁中，京都 → 日文）

## 5.8 Multi-Grid Ad Banner Set（多行业混合广告 banner 网格）

适用于"一图同时展示 N 个独立行业 / 主题 banner"（如 `ad-banner-multi-grid.md`）：

```json
{
  "language": "",
  "layout": {
    "structure": "2x2 / 3x3 grid of equal quadrants",
    "gutter": "",
    "overall_aspect_ratio": "",
    "panel_aspect_ratio": "",
    "quadrants": [{
      "position": "top-left",
      "theme": "(必填) 该格的行业 / 主题，如 'Travel' / 'Skincare'",
      "subject": "",
      "elements": [],
      "text_labels": [],
      "style": "(必填) 该格的视觉风格，与其它格不同"
    }]
  },
  "global_style": "把所有格统一的元素（如统一字体 / 统一边框）",
  "constraints": { "must_keep": ["每格内容彼此独立、无叙事关联"] }
}
```

字段经验：

- `quadrants` 数组**必填**，每格必须独立指定 `theme` + `style`
- `global_style` 用于"统一感"（如统一字体），但**不要**让所有格共享主体
- 与 `cinematic-storyboard-grid` 区别：本模板**强调 panel 间无叙事关联**，每格都是独立成品
- 与 `banner-grid-2x2`（已有）区别：本模板**多行业 / 多主题**，已有那个是同品牌多创意

## 5.9 Full Brand / Mascot Doc（18+ 模块大型品牌识别全流程文档）

适用于"一图概览整个品牌 / 吉祥物从 DNA 到落地的全流程"（如 `full-mascot-brand-doc.md`）：

```json
{
  "brand": { "name": "", "industry": "", "primary_colors": [], "voice": "" },
  "character": { "description": "", "rendering_style": "" },
  "layout": {
    "grid": "3 columns by 6 rows",
    "panel_count": 18,
    "sections": [
      { "id": "01", "title": "01 BRAND DNA ANALYSIS", "elements": [] },
      { "id": "02", "title": "02 CONCEPT MOODBOARD", "elements": [] }
    ]
  }
}
```

字段经验：

- `sections` 数组**显式列出 18 个模块**，每模块有自己的 `id` + `title` + `elements`
- 模块 `id` 双数字编号（01-18），方便视觉上形成「目录感」
- 每模块 `elements` 必须显式列出「这一格画什么」（草图 / 3D / 配色板 / 应用场景）
- 与 `mascot-brand-kit`（已有）区别：本模板是**全流程文档**（18-24 格），已有那个是**简化套装**（6-9 格）

---

# 六、参数设计规则

每个模板字段都尽量判断属于以下哪一类。

## 6.1 核心参数（优先提问）

缺失会显著影响结果，优先问用户。

常见例子：

- 主体是谁
- 商品名称是什么
- 城市名是什么
- 主题是什么
- 是真人照片还是文字描述
- 平台风格是什么

## 6.2 可默认参数

缺失后可以先用默认值，不影响模板正常工作。

常见例子：

- 背景色
- 次级按钮文案
- 普通装饰元素
- 一般性灯光词
- 常规色彩倾向

## 6.3 可随机参数

允许自动补全，但必须在风格范围内合理生成。

常见例子：

- 路人昵称
- 次级聊天消息
- 礼物提示
- 小装饰元素
- 次级背景内容

---

# 七、参数写法规范

变量统一使用如下格式：

```text
{argument name="host name" default="Elon Musk"}
```

建议规则：

- `name`：简洁明确
- `default`：给出一个可直接工作的默认值
- 如果一个字段后续经常需要随机化，也应先给出合理默认值

不要使用：

- 含糊不清的参数名
- 没有默认值但又不是必问字段

---

# 八、缺失信息提问策略

## 8.1 总原则

提问必须：

- 精准
- 少量
- 只围绕模板关键字段
- 不要泛泛而问

## 8.2 通用优先级

建议按下面顺序判断是否需要提问：

1. 主体来源是什么
2. 图像用途是什么
3. 核心对象/商品/主题是什么
4. 是否允许自动补全缺失信息
5. 是否有必须保留或必须避免的元素

## 8.3 直播 UI 类示例

不要问：

- “你想做成什么感觉？”

优先问：

- 主播是谁？
- 用真人照片、名人名字、人物描述，还是随机生成？
- 商品名称是什么？
- 商品价格是否指定？
- 是否允许我自动补全评论和礼物内容？

## 8.4 电影 / TVC 分镜类示例

不要问：

- "你想要什么故事？"

优先问：

- 一句话故事：谁 + 在哪 + 发生什么 + 结局是什么？
- 题材是什么？（sci-fi / 灾难 / 战斗 / 浪漫 / 悬疑 / 黑色电影）
- 镜头数量？（9 / 12 / 16）+ 网格（3×3 / 3×4 / 4×4）
- 情绪曲线：起 → 升 → 高潮 → 落 / 一直紧张 / 平静爆发？
- 风格：photoreal / 油画 / 动漫 cinematic / 黑白 / 复古胶片？
- (TVC 专用)产品是什么？品牌名 / 卖点 / 时长 / 比例？

## 8.5 流程板 / 装备穿戴 / 教程板示例

不要问：

- "你想做几张图？"

优先问：

- 流程主题是什么？（装备 / 化妆 / 操作 / 训练 / 维修）
- 主角是谁？（性别 / 年龄 / 关键识别特征 / 是否需要面部隐私保护）
- 步骤数量？（4 / 6 / 8 / 9）+ 网格
- 每一步「标题 + 简述 + 此时装备状态 / 操作动作」
- 风格：cinematic 实拍 / 时尚大片 / tokusatsu 特摄 / 工坊纪实？
- 文字语言（标题 / 说明字段使用语言）？

## 8.6 角色多版本目录海报示例（catalog character poster）

不要问：

- "你想画什么角色？"

优先问：

- 全图主题是什么？（十二星座 / 五行 / 朝代 / 人格类型 / 节气）
- 一共几个版本？（3 / 5 / 6 / 12）
- 每个版本的「名称 + 主题色 + 装束 / 道具 / 背景」
- 同一角色基底（脸型 / 体型 / 发色）保持哪些不变？
- 风格：anime / 国风 gongbi / Q 版 / 写实？

## 8.7 系列产品 lineup 对比海报示例

不要问：

- "你想做什么海报？"

优先问：

- 品牌 / 产品线 名称是什么？
- 一共几个 SKU？（建议 12-36）
- 按什么维度排序？（等级 tier / 系列 series / 年代 / 价格）
- 是否需要 legend（等级 key / 图标 key / 风格 key）？
- 背景调性：奢华深色 / 复古牛皮纸 / 工业极简？

## 8.8 一日游 split 海报示例

不要问：

- "你想去哪？"

优先问：

- 目的地（景区 / 城市 / 国家公园 名称）？
- 标题文案 + 文字语言（中 / 日 / 英）？
- 站点数量（5-7）+ 每站「名称 + 时间 + 一句描述 + 小插画 + 大场景」？
- 整体路线主题（自然 / 历史 / 美食 / 摄影 / 朝圣）？
- 风格：复古插画 / 国家公园海报 / 水彩日式 / Art Nouveau？
- 底部 stats（总距离 / 步数 / 预计时间）？

---

# 九、自动补全策略

当用户明确表示：

- “你来补全”
- “你随机生成”
- “先给我一个 demo”

则允许：

1. 只问最关键的 1-2 个问题
2. 其余字段使用默认值
3. 或在可随机字段中合理生成

自动补全时必须满足：

- 不破坏主体一致性
- 不与用户已指定信息冲突
- 不制造过于离谱的次要元素

---

# 十、主模板与变体模板的关系

每个模板文件至少要有：

1. 一套主模板
2. 若干变体模板（可选但推荐）

## 主模板

应满足：

- 最通用
- 最容易复用
- 可覆盖大多数使用场景

## 变体模板

常见变体：

- 用户给参考照片版
- 用户给名人名字版
- 用户给文本描述版
- 自动补全版
- 平台风格版
- 商业化加强版

变体不应完全脱离主模板，而应在主模板结构上调整少量字段。

---

# 十一、从参考案例提炼模板的步骤

参考案例来源目前主要是：

- `skills/gpt-image-2/100+GPT-Image2提示词.md`

后续提炼模板时，严格按以下步骤：

## Step 1：先判断分类

把案例归入正确的一级目录（与 `SKILL.md` 模板索引一致）：

- ui-mockups
- product-visuals
- maps（不再叫 maps-and-infographics）
- slides-and-visual-docs
- poster-and-campaigns
- portraits-and-characters
- scenes-and-illustrations
- editing-workflows
- avatars-and-profile
- storyboards-and-sequences
- grids-and-collages
- branding-and-packaging
- typography-and-text-layout
- assets-and-props
- academic-figures
- infographics
- technical-diagrams

## Step 2：判断是新原型还是旧原型变体

例如：

- VR 头显爆炸图 -> 新原型
- 手机爆炸图 -> 旧原型变体

## Step 3：拆字段

把案例拆成：

- 主体
- 场景
- 布局
- 风格
- 文案
- 约束

## Step 4：标记参数类型

为每个字段标记：

- 必问
- 可默认
- 可随机

## Step 5：先写主模板

不要一开始就写 4 个版本。先把最通用的一套主模板写出来。

## Step 6：再补变体

例如：

- 参考照片版
- 人名版
- 描述版
- 自动补全版

## Step 7：补提问顺序

说明在真实对话里优先要问哪些字段。

## Step 8：补避免事项

总结这个模板最容易失败的地方。

---

# 十二、模板文件命名规则

模板文件名应满足：

- 小写字母
- 数字或连字符
- 尽量精确表达主题
- 不要用来源命名
- 不要用序号命名

正确示例：

- `live-commerce-ui.md`
- `exploded-view-poster.md`
- `food-map.md`

错误示例：

- `template-01.md`
- `youmind-case-1.md`
- `twitter-prompt-4.md`

---

# 十三、单文件实施清单（后续每次新增模板都要遵守）

以后每新增一个模板文件，都按这份清单执行：

1. 确定一级分类目录
2. 确定文件名是否足够精确
3. 判断它是新原型还是已有原型变体
4. 写 `适用范围`
5. 写 `何时使用`
6. 写 `缺失信息优先提问顺序`
7. 写主模板 JSON
8. 写参数策略
9. 写自动补全策略
10. 写变体方式
11. 写避免事项
12. 若属于新增模板主题，则同步更新 `SKILL.md` 索引

---

# 十四、Phase 1：references 目录树重构

## 目标

把 `references/` 从平铺结构升级为目录树。

## 任务拆解

### 1. 建立一级分类目录

创建空目录：

- `references/ui-mockups/`
- `references/product-visuals/`
- `references/maps-and-infographics/`
- `references/slides-and-visual-docs/`
- `references/poster-and-campaigns/`
- `references/portraits-and-characters/`
- `references/scenes-and-illustrations/`
- `references/editing-workflows/`
- `references/branding-and-packaging/`
- `references/typography-and-text-layout/`
- `references/storyboards-and-sequences/`
- `references/assets-and-props/`

### 2. 迁移现有直播模板

把现有直播模板迁移到：

- `references/ui-mockups/live-commerce-ui.md`

### 3. 更新 `SKILL.md`

把原来的平铺索引改成：

- 一级分类
- 二级具体模板文件

### 4. 清理旧路径引用

删除旧的平铺 references 文件路径引用。

## 阶段完成标准

- references 目录树创建完成
- 现有直播模板已迁移到 `ui-mockups/`
- `SKILL.md` 索引已同步

---

# 十五、Phase 2：模板方法论升级

## 目标

把 `prompt-writing.md` 升级成后续所有模板的总规范。

## 任务拆解

### 1. 补全目录规则

明确 references 必须是目录树。

### 2. 补全单模板文件规范

明确一个模板文件内部必须有哪些章节。

### 3. 补全 JSON 字段设计标准

包括：

- 通用字段
- 分类特有字段
- 字段职责

### 4. 补全参数分类规则

包括：

- 核心参数
- 可默认参数
- 可随机参数

### 5. 补全提问与自动补全策略

包括：

- 问题优先级
- 自动补全何时允许
- 如何避免无谓提问

### 6. 补全案例提炼流程

从参考案例到 JSON 模板的完整步骤。

## 阶段完成标准

- `prompt-writing.md` 可以单独作为“模板设计总规范”使用

---

# 十六、后续阶段预告（只列主任务）

## Phase 3：建设 `ui-mockups/`

优先文件：

- `live-commerce-ui.md`
- `social-interface-mockup.md`
- `product-card-overlay.md`

## Phase 4：建设 `product-visuals/`

优先文件：

- `exploded-view-poster.md`
- `white-background-product.md`
- `premium-studio-product.md`

## Phase 5：建设 `maps-and-infographics/`

优先文件：

- `food-map.md`
- `travel-route-map.md`
- `illustrated-city-map.md`

## Phase 6：建设 `slides-and-visual-docs/`

优先文件：

- `dense-explainer-slides.md`
- `policy-style-slide.md`
- `visual-report-page.md`

## Phase 7：扩展常用视觉分类

- poster-and-campaigns
- portraits-and-characters
- scenes-and-illustrations
- editing-workflows

## Phase 8：扩展高级分类

- branding-and-packaging
- typography-and-text-layout
- storyboards-and-sequences
- assets-and-props

---

# 十七、近期执行顺序建议

按当前情况，建议后续严格按下面顺序推进：

1. 完成 Phase 1：重构 references 为目录树
2. 完成 Phase 2：升级 `prompt-writing.md`
3. 完成 Phase 3：建设 `ui-mockups/`
4. 完成 Phase 4：建设 `product-visuals/`
5. 完成 Phase 5：建设 `maps-and-infographics/`
6. 完成 Phase 6：建设 `slides-and-visual-docs/`
7. 再进入其他分类扩展

---

# 十八、结论

后续这个 skill 不能按“不断加案例”的方式增长，而要按：

- 先定目录树
- 再定模板规范
- 再做单模板文件
- 再补参数与提问策略
- 最后再持续扩展案例

这样你后面才能真正依据一份稳定的路线图持续指导我完善这个 skill，而不会每次都重新决定结构。
