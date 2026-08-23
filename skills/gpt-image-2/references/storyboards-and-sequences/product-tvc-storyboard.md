# 产品 TVC 商业广告分镜板模板

本文件用于生成"以单一产品为主角、跨 9-12 个商业广告镜头的真实摄影风分镜表"，每个 panel 都是一个真实拍摄镜头的视觉示意。

典型用途：

- 给广告 / TVC 公司做拍摄前 storyboard 提案
- 电商详情页"我们能做出这种品质视频"的预演稿
- 给 Seedance / Sora / Runway 等视频生成工具做镜头列表
- 客户审稿前的视频脚本可视化
- 电商「主图 → TVC」一图过的快速过审

特征（与现有 storyboards 模板的区别）：

| 模板 | 性质 | 风格 |
|---|---|---|
| `four-panel-comic.md`（已有） | 漫画 4 格 | 漫画 / 段子 / 反转 |
| `manga-spread-page.md`（已有） | 漫画跨页分镜 | 日漫 / 不规则格 |
| `recipe-process-flowchart.md`（已有） | 流程示意 | 食谱 / 教程插画 |
| **本模板**（新增） | **真实拍摄分镜** | **商业广告级摄影** |

**核心区别**：本模板每个 panel 都是「真实摄影 / 拟真渲染」的成片画面，不是漫画分镜也不是流程图，而是「这部 15 秒广告会拍成什么样」的视觉答案。

## 适用范围

- 商业 TVC 拍摄前 storyboard
- 电商详情页视频拍摄预演
- 客户审稿（"成片大概会长这样"）
- 给视频生成模型（Sora / Seedance / Runway）的镜头清单参考
- 4S 店 / 美妆 / 食品 / 数码品类的 15-30 秒广告分镜

## 何时使用

- 用户提到"TVC / 广告分镜 / storyboard / 视频脚本可视化"
- 用户已经有产品，想要"成片看起来怎样"的视觉提案
- 客户要看「9 / 12 个镜头分别拍什么」

不要使用：

- 漫画 / 故事 4 格 → 用 `four-panel-comic.md`
- 跨页不规则漫画 → 用 `manga-spread-page.md`
- 食谱 / 教程流程 → 用 `recipe-process-flowchart.md`
- 仅一张 hero 主图 → 用 `product-visuals/premium-studio-product.md`
- 详情页一图全销售看板 → 用 `product-visuals/ecommerce-marketing-board.md`

## 缺失信息优先提问顺序

1. 产品（必须有具体产品 / 包装 / 颜色 / 形状）
2. 视频时长（15s / 30s / 60s）+ 比例（9:16 竖屏 / 16:9 横屏 / 1:1）
3. 总镜头数（9 / 12 / 6）
4. 风格（**电影感 / 简约高级 / 暖色生活方式 / 冷色科技 / 复古怀旧**）
5. 是否需要"使用人手 / 演员"出现
6. 必须出现的卖点（决定哪个镜头要 close-up 哪个要 lifestyle）
7. 是否需要中英双语镜头标题 / 时间码

## 主模板：9-panel 产品 TVC 商业广告分镜板

📖 描述

3×3 = 9 格，每格是一个独立镜头的成片视觉示意，整体配 header（节目主标 + 时长 + 比例）+ 每格中文镜头标题 + 时间码 + 拍摄说明。

📝 提示词

```json
{
  "type": "product TVC storyboard board",
  "goal": "生成一张 9 格分镜图，每格都是该产品商业广告的一个真实拍摄镜头视觉示意，可作为拍摄前 storyboard / 客户审稿 / 视频生成参考",
  "input_mode": "{argument name=\"input mode\" default=\"text-only\"}",
  "reference_image_note": "如果用户提供产品参考图，必须保持产品外观完全一致（颜色 / 包装 / logo 不可漂移）",
  "header": {
    "title": "{argument name=\"header title\" default=\"产品TVC分镜脚本\"}",
    "subtitle_meta": "{argument name=\"video duration\" default=\"15秒\"} / {argument name=\"aspect ratio\" default=\"9:16竖屏\"} / 9宫格",
    "product_name_subtitle": "{argument name=\"product name\" default=\"青花瓷烟灰缸\"}"
  },
  "layout": {
    "format": "{argument name=\"board orientation\" default=\"vertical 3:4 storyboard sheet\"}",
    "background": "{argument name=\"board background\" default=\"dark elegant gradient with subtle paper texture\"}",
    "grid": {
      "rows": 3,
      "columns": 3,
      "panel_count": 9,
      "panel_aspect_ratio": "{argument name=\"panel ratio\" default=\"9:16 (vertical TVC)\"}",
      "panel_borders": "thin light divider, generous gutter",
      "panel_label_position": "top-left number badge + scene title in Chinese; small timestamp top-right; small Chinese description below the image"
    }
  },
  "scenes": {
    "count": 9,
    "items": [
      { "id": 1, "title_zh": "{argument name=\"scene 1 title\" default=\"环境建立\"}", "timestamp": "0-2s", "description": "environment-establishing wide shot with desk, books, window, and the product placed in context; soft morning light" },
      { "id": 2, "title_zh": "{argument name=\"scene 2 title\" default=\"主体亮相\"}", "timestamp": "2-3s", "description": "hero product medium shot on the table; warm rim light, shallow depth of field" },
      { "id": 3, "title_zh": "{argument name=\"scene 3 title\" default=\"工艺特写\"}", "timestamp": "3-5s", "description": "extreme close-up of the {argument name=\"signature detail\" default=\"blue floral craftsmanship pattern\"}" },
      { "id": 4, "title_zh": "{argument name=\"scene 4 title\" default=\"使用场景\"}", "timestamp": "5-7s", "description": "use case showing {argument name=\"use action\" default=\"a hand placing a cigarette into the ashtray with visible smoke\"}" },
      { "id": 5, "title_zh": "{argument name=\"scene 5 title\" default=\"功能展示\"}", "timestamp": "7-8s", "description": "{argument name=\"function shot\" default=\"top-down capacity display showing multiple cigarette butts inside\"}" },
      { "id": 6, "title_zh": "{argument name=\"scene 6 title\" default=\"清洁打理\"}", "timestamp": "8-10s", "description": "{argument name=\"care shot\" default=\"cleaning scene under running water in a sink with a hand holding the product\"}" },
      { "id": 7, "title_zh": "{argument name=\"scene 7 title\" default=\"细节品质\"}", "timestamp": "10-11s", "description": "{argument name=\"quality detail\" default=\"bottom-detail close-up showing the underside and anti-slip pads\"}" },
      { "id": 8, "title_zh": "{argument name=\"scene 8 title\" default=\"氛围生活\"}", "timestamp": "11-13s", "description": "{argument name=\"mood scene\" default=\"mood/lifestyle scene at night with the product on a desk, smoke rising, and ambient lamp light\"}" },
      { "id": 9, "title_zh": "{argument name=\"scene 9 title\" default=\"品牌收尾\"}", "timestamp": "13-15s", "description": "brand closing frame with the product as the hero plus Chinese marketing text '{argument name=\"closing tagline\" default=\"匠心传承,品味生活\"}'" }
    ]
  },
  "global_style": {
    "rendering": "premium realistic commercial photography across all 9 panels",
    "consistency": "the product (color / shape / packaging / logo) stays IDENTICAL across all 9 panels",
    "lighting": "{argument name=\"lighting style\" default=\"warm premium lighting, shallow depth of field, refined lifestyle desktop environment\"}",
    "color_grading": "{argument name=\"color grading\" default=\"warm cinematic\"}",
    "panel_treatment": "each panel feels like a real ad still, not a sketch or wireframe"
  },
  "constraints": {
    "must_keep": [
      "9 个镜头编号清晰、时间码递增不重叠（总和 = 视频时长）",
      "产品在 9 个镜头中外观完全一致",
      "每格的中文镜头标题 + 时间码 + 描述都必须存在",
      "整体看起来像专业广告 storyboard 板而不是 9 张随机图"
    ],
    "avoid": [
      "9 个镜头都是同一角度（必须有近景 / 中景 / 远景 / 俯拍 / 仰拍混合）",
      "镜头描述与产品类型不匹配（如给手机做'倒粉入杯'镜头）",
      "产品在不同镜头中改变颜色或外观",
      "时间码总和与 video duration 不一致",
      "没有 closing 镜头（最后一格必须是品牌收尾）"
    ]
  }
}
```

### 参数策略

- **必问**：product name、video duration + aspect ratio、产品参考图（如有）
- **可默认**：board background、closing tagline、lighting style
- **可随机**：scene 1-9 具体描述（按产品类目套用模板）

### 自动补全策略

- 用户只说"做我这个产品的 9 格 TVC 分镜"+ 给参考图 → 按产品类目自动套 9 镜头模板
- 不指定具体镜头内容 → 用「环境建立 → 亮相 → 工艺 → 使用 → 功能 → 清洁/打理 → 细节 → 氛围 → 收尾」标准结构
- 不指定时长 → 默认 15s 9 格

## 变体 1：12 panel 30 秒长版

📝 提示词

```json
{
  "type": "12-panel 30s product TVC storyboard",
  "header": {
    "subtitle_meta": "30秒 / {argument name=\"aspect ratio\" default=\"16:9横屏\"} / 12宫格"
  },
  "layout": { "rows": 3, "columns": 4, "panel_count": 12 },
  "scenes_extension": [
    "10) 用户证言/使用见证镜头",
    "11) 数据/对比/认证镜头",
    "12) 第二次品牌收尾 + CTA"
  ],
  "use_case": "30s TVC / 详情页长视频 / 完整产品故事"
}
```

### 何时选这个变体

- 视频时长 ≥ 30s
- 需要「用户见证 + 数据对比 + CTA」更完整销售环节
- 横屏播放渠道（YouTube / B 站 / 详情页 banner 视频）

## 变体 2：6 panel 极简短视频版（适合抖音 15s）

📝 提示词

```json
{
  "type": "6-panel 15s vertical short video storyboard",
  "header": {
    "subtitle_meta": "15秒 / 9:16竖屏 / 6宫格"
  },
  "layout": { "rows": 2, "columns": 3, "panel_count": 6 },
  "scenes": [
    "1 钩子/痛点开场",
    "2 产品出现",
    "3 一个核心卖点 close-up",
    "4 使用瞬间",
    "5 效果/对比",
    "6 品牌 + CTA"
  ],
  "use_case": "抖音 / 快手 / TikTok / Reels 15s 短视频"
}
```

### 何时选这个变体

- 平台限制 15s 内
- 主要走「钩子 + 卖点 + 转化」的快节奏短视频
- 6 镜头 = 每镜头平均 2.5s，够直接好懂

## 变体 3：电影感叙事 TVC（高端品类）

📝 提示词

```json
{
  "type": "cinematic-narrative TVC storyboard",
  "header": {
    "subtitle_meta": "{argument name=\"video duration\" default=\"60秒\"} / 16:9宽屏 / 9宫格"
  },
  "scenes_replacement": [
    "1 主角登场 / 情境引入",
    "2 矛盾 / 困境",
    "3 转折 / 产品出现",
    "4 互动 / 体验",
    "5 高光时刻",
    "6 情绪释放",
    "7 群像 / 共鸣",
    "8 品牌哲学陈述",
    "9 logo + slogan 静帧"
  ],
  "style_override": {
    "lighting": "电影级灯光，强对比，氛围浓郁",
    "color_grading": "复古 / 蒂芙尼 / 沙漠橙 / 黑白特定色调",
    "talent": "真人演员 + 情绪面部表情"
  }
}
```

### 何时选这个变体

- 汽车 / 奢侈品 / 高端家电 / 全球品牌
- 走「故事 + 情绪 + 哲学」而非「卖点 + 数据」
- 60s+ 长版品牌片

## 避免事项

- ❌ 9 个镜头都是产品 close-up → 必须有镜头节奏（远 / 中 / 近 / 极近 / 俯 / 仰）
- ❌ 产品在不同镜头中变色 / 变形 → 致命错误，必须强调"identical product"
- ❌ 镜头描述与产品类目不符（如给口红做"水龙头清洗"镜头）
- ❌ 时间码总和不等于视频总时长 → 客户立刻看出来不专业
- ❌ 漏掉品牌收尾镜头（最后一格必须是 logo + slogan / CTA）
- ❌ 把 9 格画成漫画 / 插画风 → 应该是真实摄影感
- ❌ 板面没有 header（标题 + 时长 + 比例）→ 看起来像随机的 9 张图
- ❌ 把模板里的"argument"占位符原样写到最终 prompt
