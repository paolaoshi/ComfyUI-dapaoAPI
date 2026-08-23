# 高级影棚产品图模板

本文件用于生成“顶级影棚级商业产品图”：

- 杂志广告级质感
- 戏剧化灯光
- 颜色基调统一
- 道具克制
- 商品作为唯一叙事主角

适合：

- 香水 / 高端化妆品
- 高端腕表 / 珠宝
- 烈酒 / 葡萄酒
- 奢侈品配件
- 高端 3C / 影音设备
- 米其林餐饮主图

它跟 `white-background-product.md` 的区别：

- 白底图：电商平台主图，强调干净、还原
- 影棚图：广告级视觉，强调氛围、戏剧性、品牌格调

跟 `lifestyle-product-scene.md` 的区别：

- 影棚图：纯商品 + 纯氛围，没有人物、没有生活场景
- 生活方式图：商品出现在真实使用场景里

## 适用范围

- 高端品牌官网首屏图
- 杂志整版广告
- 平面投放主视觉
- 单品发布主图

## 何时使用

- 用户提到“影棚 / 商业广告 / 杂志 / 高级感 / 大片感 / cinematic / studio”
- 用户希望商品看起来“贵”
- 用户希望摆脱白底，但又不要日常场景

不要使用：

- 用户要电商平台主图（用 `white-background-product.md`）
- 用户希望商品出现在生活里（用 `lifestyle-product-scene.md`）
- 用户要展示包装结构 / 礼盒（用 `packaging-showcase.md`）

## 缺失信息优先提问顺序

1. 商品具体是什么 + 类目
2. 品牌定位（高端 / 极简 / 复古 / 暗黑 / 自然有机 / 未来感）
3. 颜色基调 + 主色 + 辅助色
4. 灯光氛围（柔和 / 戏剧 / 冷峻 / 暖光 / 顶光透射）
5. 是否需要少量道具（同色调）
6. 是否需要主标语 / 品牌 logo

## 主模板：单品高级影棚视觉

📖 描述

商品居于画面中心或黄金分割位，深色或同色基调背景，戏剧化主光，最少道具，可叠加品牌名 + 一句标语。

📝 提示词

```json
{
  "type": "高级影棚商业产品图",
  "goal": "生成一张可直接当作广告级单页主图的影棚视觉，商品作为唯一叙事中心，氛围统一，色调克制",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"高端香水玻璃瓶\"}",
    "visual_description": "{argument name=\"product visual\" default=\"琥珀色厚重玻璃瓶，金色金属盖，瓶身印有简约黑色品牌名\"}",
    "position": "{argument name=\"product position\" default=\"画面中心略偏右\"}",
    "scale": "{argument name=\"product scale\" default=\"占画面 45%\"}"
  },
  "background": {
    "type": "{argument name=\"background type\" default=\"深棕色丝绒布料 + 同色调环境\"}",
    "texture": "{argument name=\"background texture\" default=\"丝绒细微纹理\"}",
    "color_tone": "{argument name=\"color tone\" default=\"暖棕 + 金色\"}"
  },
  "lighting": {
    "key_light": "{argument name=\"key light\" default=\"顶部 45° 戏剧主光，造型清晰\"}",
    "fill_light": "{argument name=\"fill light\" default=\"右侧弱柔光\"}",
    "rim_light": "{argument name=\"rim light\" default=\"背后金色边缘光，勾勒瓶身轮廓\"}",
    "mood": "{argument name=\"lighting mood\" default=\"温暖、奢华、近黄昏感\"}"
  },
  "props": {
    "enabled": "{argument name=\"props enabled\" default=\"true\"}",
    "items": [
      "{argument name=\"prop 1\" default=\"几片散落的干玫瑰花瓣\"}",
      "{argument name=\"prop 2\" default=\"局部金色金属反射条\"}"
    ],
    "rule": "道具数量 ≤ 2，颜色必须与主色一致"
  },
  "text_overlay": {
    "enabled": "{argument name=\"text overlay enabled\" default=\"true\"}",
    "brand": "{argument name=\"brand name\" default=\"NUIT D'OR\"}",
    "headline": "{argument name=\"headline\" default=\"夜，是另一种光\"}",
    "position": "{argument name=\"text position\" default=\"画面左侧上半，留白足够\"}"
  },
  "style": {
    "rendering": "顶级商业摄影 + 高动态范围 + 微颗粒，看起来像杂志整版广告",
    "depth": "浅景深，背景轻微虚化",
    "consistency": "色板严格统一，不出现额外鲜艳色"
  },
  "constraints": {
    "must_keep": [
      "商品作为绝对主角",
      "光线方向统一",
      "色调统一不杂乱",
      "文案不要遮挡商品本身"
    ],
    "avoid": [
      "道具喧宾夺主",
      "出现 lifestyle 元素（手、餐具、模特）",
      "字体过多种类",
      "背景颜色与商品过于接近以至看不见轮廓"
    ]
  }
}
```

### 参数策略

- 必问：商品、品牌定位、主色调
- 可默认：道具、文案位置、灯光方向
- 可随机：道具具体物件（在主色范围内合理生成）

### 自动补全策略

- 香水 / 烈酒 默认深色调 + 顶光主光
- 化妆品 默认柔和奶油色调 + 正面柔光
- 珠宝 默认暗背景 + 边缘强光勾勒
- 数码 默认深空背景 + 蓝色冷光
- 文案默认一句 ≤ 8 字，不要长 slogan

## 变体 1：暗调奢侈品（珠宝 / 腕表）

📝 提示词

```json
{
  "type": "暗调奢侈品影棚视觉",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"金色机械腕表\"}",
    "visual_description": "{argument name=\"product visual\" default=\"圆形金壳、棕色鳄鱼皮表带、清晰表盘\"}"
  },
  "background": {
    "type": "深黑色平面 + 极弱反射",
    "color_tone": "近黑 + 局部金色"
  },
  "lighting": {
    "key_light": "顶部射灯",
    "rim_light": "金属边缘光，强调表壳轮廓"
  },
  "constraints": {
    "must_feel": "稀有、矜持、仪式感"
  }
}
```

## 变体 2：清冷数码 / 影音

📝 提示词

```json
{
  "type": "清冷调数码产品影棚视觉",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"无线智能音箱\"}",
    "visual_description": "{argument name=\"product visual\" default=\"圆柱形深空灰金属外壳，顶部触控环带蓝色光\"}"
  },
  "background": {
    "type": "深空灰渐变",
    "color_tone": "灰 + 冷蓝"
  },
  "lighting": {
    "key_light": "正面柔光",
    "rim_light": "蓝色背光，营造科技感"
  },
  "props": {
    "enabled": false
  },
  "constraints": {
    "must_feel": "高级、克制、未来感"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "高级影棚视觉自动补全模板",
  "mode": "auto-fill",
  "rule": "根据品类自动选择背景调性、灯光方向、文案长度，但保持商品唯一叙事中心",
  "constraints": {
    "must_feel": "杂志广告级"
  }
}
```

## 避免事项

- 不要塞入超过 2 个道具
- 不要出现人物或人物身体局部（手 / 嘴唇 / 指甲）
- 不要混合冷暖色调（除非品牌定位明确允许）
- 不要让商品反光过强以致看不清品牌字
- 不要把白底图风格搬过来（“无氛围”就不算高级）
- 不要让文字大于品牌应有的克制感（slogan 要少而短）
