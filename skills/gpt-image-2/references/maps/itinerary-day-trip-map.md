# 一日游 / 单日行程图模板（左侧 stops + 右侧画面地图）

本文件用于生成"竖版 2:3 一日游攻略海报，左半是行程卡片（5 站编号 + 时间 + 描述），右半是奇幻写实风的山水地图（同样 5 个标号匹配）"。

典型用途：

- 景区 / 国家公园 / 古镇 一日游推荐海报
- 旅游局 / 文旅 campaign 主视觉
- 公众号 / 小红书 长图文封面
- 旅游品牌 / 民宿 / OTA 一日 itinerary 物料
- 节假日打卡路线分享图
- 游记封面 / 行程纪念海报

特征（与已有 maps 模板的区别）：

| 模板 | 性质 |
|---|---|
| `travel-route-map.md`（已有） | **多日行程**（D1-D7）跨城市路线图，强调顺序 + 时间 |
| `food-map.md`（已有） | **美食地图**（多店铺密度） |
| `illustrated-city-map.md`（已有） | **城市风貌地图**（地标插画） |
| `store-distribution-map.md`（已有） | **门店分布图** |
| **本模板**（新增） | **单日行程 split 海报**：左行程卡 + 右奇幻写实地图，5-7 站点严格对齐 |

**核心区别**：本模板是"单日行程 + 复古旅行海报美学 + 双栏严格对齐"的视觉范式，最适合景区一日游、国家公园 itinerary、城市 city walk 单日方案。

## 适用范围

- 单日 itinerary（5-7 站点）
- 景区 / 国家公园 / 山岳 / 古镇 一日游
- 城市 city walk 单日方案
- 文旅局 / 旅游品牌 campaign
- 复古插画风 / 国家公园海报美学

## 何时使用

- 用户明确说"一日游 / 一天行程 / 单日 itinerary / 一日打卡"
- 想要复古插画 + parchment + 双栏 split 设计
- 站点数量适中（建议 5-7）
- 需要每站时间 + 描述 + 图标

不要使用：

- 多日行程（D1-D7） → 用 `travel-route-map.md`
- 美食地图（密度高、无强顺序） → 用 `food-map.md`
- 城市地标插画（不强调路线） → 用 `illustrated-city-map.md`
- 门店分布（商业化） → 用 `store-distribution-map.md`

## 缺失信息优先提问顺序

1. 目的地（景区 / 城市 / 国家公园 名称）
2. 标题文案（中文 / 日文 / 英文 …）
3. 站点数量（推荐 5；上限 7）
4. 每站「名称 + 时间 + 一句中文描述 + 小插画主体」
5. 整体路线主题（自然 / 历史 / 美食 / 朝圣 / 摄影）
6. 风格调性（复古插画 / 国家公园海报 / 水彩 / Art Nouveau / parchment）
7. 配色基调（暖 sepia + gold / 翠绿 + 金 / 蓝白雪山）
8. 底部 stats（总距离 / 步数 / 海拔 / 预计时间）
9. 是否需要罗盘玫瑰 / 装饰边框 / 复古印章

## 主模板：5 站点竖版 split 一日游海报（5-stop vertical split itinerary poster）

📖 描述

竖版 2:3 海报，左半是 parchment 行程卡（标题 + 5 个编号 station，每站带圆形编号徽章 + 小插画 + 名称 + 时间括号 + 中文描述），右半是奇幻写实风山水大画面（金色蜿蜒路径串联 5 个 marker，每 marker 与左侧编号 + 名称严格匹配）。底部右下角带罗盘玫瑰 + stats info box。整体 sepia + gold + jade 复古旅行海报美学。

📝 提示词

```json
{
  "type": "vintage illustrated travel itinerary poster, vertical split layout",
  "goal": "生成一张左行程卡 / 右奇幻写实地图、5 站编号严格对齐的一日游攻略海报，可作为景区 / 国家公园 / 城市单日游主视觉",
  "language": "{argument name=\"language\" default=\"Traditional Chinese\"}",
  "destination": {
    "name": "{argument name=\"destination name\" default=\"阿里山國家風景區\"}",
    "duration": "{argument name=\"duration\" default=\"1 day\"}",
    "theme": "{argument name=\"trip theme\" default=\"mountain forest railway and sunset cloud sea\"}"
  },
  "headline": {
    "main": "{argument name=\"headline text\" default=\"阿里山國家風景區一日遊\"}",
    "tagline": "{argument name=\"tagline\" default=\"一座高山，五個經典景點。難忘的奇幻旅程。\"}",
    "divider": "small decorative mountain divider beneath the tagline"
  },
  "style": {
    "overall": "{argument name=\"art style\" default=\"premium tourism poster, painterly digital illustration, nostalgic national-park brochure aesthetic\"}",
    "left_panel_look": "{argument name=\"left look\" default=\"parchment-textured itinerary card in warm beige with ornate gold Art Nouveau borders and dark brown typography\"}",
    "right_panel_look": "{argument name=\"right look\" default=\"dramatic painted fantasy-realism map scene of a mountain journey at sunrise and sunset tones\"}",
    "color_palette": "{argument name=\"color palette\" default=\"warm sepia, gold, jade green, deep brown, cream, soft sunset orange\"}",
    "atmosphere": "layered mountain ranges, mist-filled valleys, evergreen forests, golden-hour light, luminous cloud seas, romantic painterly atmosphere"
  },
  "layout": {
    "format": "vertical 2:3 poster, split into two equal vertical columns",
    "left_panel": {
      "type": "itinerary card",
      "header": ["headline title centered top", "tagline beneath", "decorative mountain divider"],
      "stop_count": 5,
      "stop_design": [
        "circular black-and-gold number badge",
        "small vignette illustration",
        "bold location name in headline font",
        "time in parentheses beside name",
        "1-2 sentence Chinese description"
      ],
      "border": "ornate gold Art Nouveau frame with corner flourishes"
    },
    "right_panel": {
      "type": "painted map scene",
      "background": "continuous mountain landscape at sunrise to sunset gradient",
      "path": "glowing golden winding path connecting all numbered markers in order",
      "marker_design": "black-and-gold marker plaques with number + same location name as left panel",
      "compass_rose": "decorative compass rose labeled N E S W at bottom-right",
      "stats_box": "dark green and gold information box at bottom-right corner"
    },
    "alignment_rule": "the 5 numbered stops on the left must match the 5 numbered markers on the right exactly in order, label, and visual identity"
  },
  "stops": {
    "count": 5,
    "items": [
      {
        "number": 1,
        "name": "{argument name=\"stop 1 name\" default=\"阿里山車站\"}",
        "time": "{argument name=\"stop 1 time\" default=\"8:00 AM\"}",
        "description": "{argument name=\"stop 1 desc\" default=\"開啟探索神木與森林的旅程。\"}",
        "left_vignette": "{argument name=\"stop 1 left vignette\" default=\"wooden mountain railway station\"}",
        "right_scene": "{argument name=\"stop 1 right scene\" default=\"a rustic alpine wooden station perched on a cliff among pine forests\"}"
      },
      {
        "number": 2,
        "name": "{argument name=\"stop 2 name\" default=\"阿里山森林鐵路\"}",
        "time": "{argument name=\"stop 2 time\" default=\"9:30 AM\"}",
        "description": "{argument name=\"stop 2 desc\" default=\"穿越森林，體驗百年林鐵風情。\"}",
        "left_vignette": "{argument name=\"stop 2 left vignette\" default=\"red-and-black steam train\"}",
        "right_scene": "{argument name=\"stop 2 right scene\" default=\"a small steam locomotive traveling on a curved mountain railway with smoke drifting upward\"}"
      },
      {
        "number": 3,
        "name": "{argument name=\"stop 3 name\" default=\"神木區棧道\"}",
        "time": "{argument name=\"stop 3 time\" default=\"11:30 AM\"}",
        "description": "{argument name=\"stop 3 desc\" default=\"漫步千年巨木下，感受森林靈氣。\"}",
        "left_vignette": "{argument name=\"stop 3 left vignette\" default=\"giant cedar trees and elevated wooden boardwalk\"}",
        "right_scene": "{argument name=\"stop 3 right scene\" default=\"towering ancient red cypress trees with a spiral and zigzag wooden walkway around the trunks\"}"
      },
      {
        "number": 4,
        "name": "{argument name=\"stop 4 name\" default=\"姊妹潭\"}",
        "time": "{argument name=\"stop 4 time\" default=\"1:30 PM\"}",
        "description": "{argument name=\"stop 4 desc\" default=\"欣賞靜謐湖光，聆聽自然樂章。\"}",
        "left_vignette": "{argument name=\"stop 4 left vignette\" default=\"tranquil forest lake and pavilion\"}",
        "right_scene": "{argument name=\"stop 4 right scene\" default=\"an emerald lake surrounded by dense forest with a small pavilion and arched bridge\"}"
      },
      {
        "number": 5,
        "name": "{argument name=\"stop 5 name\" default=\"小笠原山展望台\"}",
        "time": "{argument name=\"stop 5 time\" default=\"4:00 PM\"}",
        "description": "{argument name=\"stop 5 desc\" default=\"觀賞壯闊山景與雲海，欣賞日落。\"}",
        "left_vignette": "{argument name=\"stop 5 left vignette\" default=\"wooden observation deck above clouds at sunset\"}",
        "right_scene": "{argument name=\"stop 5 right scene\" default=\"a lookout deck on a peak above a sea of clouds, facing a glowing sunset\"}"
      }
    ]
  },
  "footer_box": {
    "compass_rose": "decorative compass labeled N / E / S / W at bottom-right of map panel",
    "stats_box": {
      "design": "dark green and gold information box",
      "stats": [
        "{argument name=\"stat 1\" default=\"總距離 ~9公里 / 5.6英里\"}",
        "{argument name=\"stat 2\" default=\"預計時間 全天 - 14,500步\"}"
      ]
    }
  },
  "constraints": {
    "must_keep": [
      "5 个 stop 严格对齐：左侧编号 / 名称 / 顺序 = 右侧 marker",
      "竖版 2:3 split 布局，左右等宽",
      "左侧 parchment + 金色 Art Nouveau 边框 + 编号徽章",
      "右侧蜿蜒金色路径连接所有 marker（按编号顺序）",
      "底部右下角带罗盘 + stats box",
      "整体复古旅行海报美学（sepia + gold）",
      "标题语言、字体、配色保持统一",
      "每站名称在左右两栏完全一致"
    ],
    "avoid": [
      "左右编号不对齐 / 名称漂移",
      "右侧路径不串联所有 marker",
      "marker 数量与左侧 stop 数量不一致",
      "破坏 2:3 split 布局（左右不等宽 / 错位）",
      "在 parchment 卡上使用现代极简风（破坏复古调性）",
      "把行程图做成简单地图（必须有完整的山水写实场景）",
      "缺少时间 / 描述文字",
      "把多日行程塞进一张图（应使用 travel-route-map.md）"
    ]
  }
}
```

### 参数策略

- **必问**：destination name、headline、5 个 stop（name + time + desc + left vignette + right scene）
- **可默认**：style overall、left/right look、color palette、stats、tagline、language
- **可随机**：tagline 文案、stats 数字（除非用户给出实际数据）

### 自动补全策略

- 用户给"想要 XX 一日游" → 按热门景点推断 5 站点（早 → 晚时间链）
- 用户没给时间 → 自动按 8:00 / 9:30 / 11:30 / 1:30 PM / 4:00 PM 自然推进
- 不指定语言 → 默认与 destination 所在地的官方语言一致（台湾 → 繁中，京都 → 日文，巴黎 → 法文，纽约 → 英文）
- 不指定 stats → 给合理估计（5km-15km / 8000-15000 步）

## 变体 1：7 站点 city walk 版（步行 + 美食 / 文化）

📝 提示词

```json
{
  "type": "city walk one-day itinerary poster, vertical split layout",
  "stops_count": 7,
  "transport": "walking only",
  "stop_design": ["each stop adds estimated walking minutes between previous and current"],
  "right_scene_override": "vintage illustrated city map with streets, buildings, parks, and golden walking path threading through 7 markers",
  "use_case": "京都 city walk / 巴黎左岸 / 东京下町 一日散步路线"
}
```

### 何时选这个变体

- 城市内步行路线
- 站点偏多（6-7）
- 强调街道 / 巷弄 / 美食 / 咖啡 文化

## 变体 2：横版 16:9 双栏（适合官网 banner / PPT 主图）

📝 提示词

```json
{
  "type": "horizontal split itinerary banner, 16:9",
  "layout_override": {
    "format": "horizontal 16:9 wide",
    "split": "left 40% itinerary card, right 60% map scene",
    "stops_arrangement": "left card lists 5 stops in 1 vertical column"
  },
  "use_case": "景区官网首图 / PPT 推介 / 视频开场图"
}
```

### 何时选这个变体

- 横版承载（官网 banner / 演讲首页）
- 不需要竖版社交分享

## 变体 3：水彩日式风（樱花 / 温泉 / 神社）

📝 提示词

```json
{
  "type": "Japanese watercolor one-day itinerary poster",
  "style_override": {
    "art_style": "delicate Japanese watercolor with soft sumi-e ink lines, sakura pastel palette",
    "color_palette": "soft pink, mint, indigo, cream, gold accents",
    "left_panel_look": "washi paper card with cherry blossom decorations and elegant kanji typography",
    "right_panel_look": "hazy mountain shrine and onsen valley painted in watercolor with cherry blossom drifting"
  },
  "use_case": "京都樱花一日游 / 箱根温泉一日游 / 镰仓寺庙巡礼"
}
```

### 何时选这个变体

- 日本主题 / 樱花 / 温泉 / 神社
- 想要更柔美的水彩日式美学
- 不要复古西方 Art Nouveau 调性

## 避免事项

- ❌ 左右编号不对齐 / 名称漂移
- ❌ 右侧路径不串联所有 marker（必须按顺序串成一条金色路径）
- ❌ 破坏 2:3 split 布局（左右必须等宽）
- ❌ 把多日行程塞进一张图（**用 `travel-route-map.md`**）
- ❌ 把美食地图塞进来（**用 `food-map.md`**）
- ❌ 缺少时间 / 描述 / stats
- ❌ 在 parchment 卡上用现代极简风
- ❌ 把右侧画成简单线条地图（必须是完整的山水写实场景画）
- ❌ 让模型自由生成 stop（必须显式列出每站 name + time + desc + 左 vignette + 右 scene）
- ❌ 站点数量超过 7（视觉密度过高）
