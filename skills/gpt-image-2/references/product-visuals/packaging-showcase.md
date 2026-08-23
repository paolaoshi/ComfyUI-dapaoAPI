# 包装展示图模板

本文件用于生成“产品包装本身”作为视觉主体的展示图：

- 礼盒包装 + 内容物
- 单品外盒 + 角度组合
- 系列产品包装合集
- 限量礼盒拆解视觉
- 套装内容物开盒摆放

它跟 `branding-and-packaging/` 下的“品牌包装系统”模板的区别：

- 本模板：单一产品 / 单一礼盒为视觉中心，重点是“开箱即用”的产品图
- branding-and-packaging：偏“品牌包装设计 system”视觉，可能包含多个 SKU、规范页

跟 `white-background-product.md` 的区别：

- 白底主图：单品本身
- 包装展示：盒子 + 拆开后内含的瓶 / 卡 / 说明书 / 周边

## 适用范围

- 礼盒展示
- 限量套装宣传图
- 节日促销主图
- 美妆套装 / 美食礼包 / 数码套装
- 内容物摆放图
- 节日礼盒主图

## 何时使用

- 用户提到“礼盒 / 套装 / 包装 / 开箱图 / 套盒主图”
- 用户希望同时展示外盒 + 内容物
- 用户希望突出包装设计本身

不要使用：

- 用户只要单品白底主图（用 `white-background-product.md`）
- 用户要场景化（用 `lifestyle-product-scene.md`）
- 用户要爆炸视图（用 `exploded-view-poster.md`）

## 缺失信息优先提问顺序

1. 包装类型：纸盒 / 铁盒 / 木盒 / 布袋 / 礼盒 / 简易盒
2. 内容物：几样、各是什么
3. 品牌名 / 系列名
4. 风格：高级简约 / 节日喜庆 / 轻奢复古 / 童趣可爱 / 国潮东方
5. 主色 + 辅色
6. 是否要展示打开状态

## 主模板：礼盒打开 + 内容物展示

📖 描述

主体是一个开盖的礼盒，内容物有序摆放在盒中或盒旁，背景为同色调干净表面。

📝 提示词

```json
{
  "type": "礼盒包装展示图",
  "goal": "生成一张兼具产品介绍与节日感的礼盒展示图，包含外盒 + 内容物 + 品牌信息层",
  "package": {
    "type": "{argument name=\"package type\" default=\"硬纸礼盒，开盖状态\"}",
    "shape": "{argument name=\"package shape\" default=\"长方形\"}",
    "exterior_color": "{argument name=\"exterior color\" default=\"墨绿色 + 烫金 logo\"}",
    "interior_color": "{argument name=\"interior color\" default=\"奶白色绒布内衬\"}",
    "logo": "{argument name=\"package logo\" default=\"金色品牌字标\"}",
    "ribbon": "{argument name=\"ribbon\" default=\"墨绿色丝带\"}"
  },
  "contents": {
    "count": "{argument name=\"content count\" default=\"4\"}",
    "items": [
      "{argument name=\"content item 1\" default=\"主产品玻璃瓶\"}",
      "{argument name=\"content item 2\" default=\"小袋装样品 x 2\"}",
      "{argument name=\"content item 3\" default=\"品牌卡片 + 使用说明\"}",
      "{argument name=\"content item 4\" default=\"金属勺 / 配件\"}"
    ],
    "arrangement": "{argument name=\"content arrangement\" default=\"内容物在盒内对称摆放，主产品略前置突出\"}"
  },
  "scene": {
    "background_surface": "{argument name=\"background surface\" default=\"奶白色亚光石面\"}",
    "background_color_tone": "{argument name=\"background tone\" default=\"米白 + 墨绿点缀\"}",
    "extra_decorations": [
      "{argument name=\"deco 1\" default=\"散落的小植物叶片\"}",
      "{argument name=\"deco 2\" default=\"无\"}"
    ]
  },
  "lighting": {
    "key_light": "{argument name=\"key light\" default=\"45° 顶光柔光\"}",
    "fill_light": "{argument name=\"fill light\" default=\"环境补光均匀\"}"
  },
  "text_overlay": {
    "enabled": "{argument name=\"text overlay enabled\" default=\"true\"}",
    "brand": "{argument name=\"brand name\" default=\"NORINE\"}",
    "headline": "{argument name=\"headline\" default=\"献给重要日子的礼物\"}",
    "subline": "{argument name=\"subline\" default=\"Limited Edition · 2026 Holiday\"}",
    "position": "画面左上或右上，简洁排版"
  },
  "style": {
    "rendering": "高分辨率商业产品摄影，内容物质感真实，包装材质清晰可识别",
    "consistency": "色板与材质一致，画面克制不杂乱"
  },
  "constraints": {
    "must_keep": [
      "外盒可识别 + logo 可读",
      "内容物清晰可数",
      "盒盖打开角度自然不别扭",
      "文字位置与主体不抢镜"
    ],
    "avoid": [
      "内容物挤在一起难分辨",
      "盒子形状不规整",
      "光线把烫金 logo 完全吃掉",
      "出现人物 / 模特 / 手"
    ]
  }
}
```

### 参数策略

- 必问：包装类型、内容物组成、品牌名、主色
- 可默认：丝带、内衬颜色、装饰
- 可随机：装饰小物（在色板内）

### 自动补全策略

- 美妆礼盒默认：奶白内衬 + 金色 logo + 玻璃瓶为主产品
- 节日食品礼盒默认：木盒或牛皮纸 + 红色丝带 + 多种小袋装内容
- 数码礼盒默认：黑色硬盒 + 灰色泡棉内衬 + 主机 + 配件
- slogan 默认 “Limited Edition / Holiday / Anniversary” 系收束语

## 变体 1：节日喜庆礼盒

📝 提示词

```json
{
  "type": "节日喜庆礼盒展示图",
  "package": {
    "type": "硬纸礼盒，开盖状态",
    "exterior_color": "{argument name=\"exterior color\" default=\"中国红 + 烫金\"}",
    "interior_color": "金色绒布内衬",
    "ribbon": "金色蝴蝶结"
  },
  "contents": {
    "items": [
      "{argument name=\"content 1\" default=\"红色礼袋 x 2\"}",
      "{argument name=\"content 2\" default=\"主礼品（食品 / 茶叶 / 工艺品）\"}",
      "{argument name=\"content 3\" default=\"祝福贺卡\"}"
    ]
  },
  "scene": {
    "background_surface": "金色亮面或深红绒布",
    "extra_decorations": ["散落小金粒", "梅花枝点缀"]
  },
  "constraints": {
    "must_feel": "节日庄重感、东方喜庆"
  }
}
```

## 变体 2：极简轻奢礼盒

📝 提示词

```json
{
  "type": "极简轻奢礼盒展示图",
  "package": {
    "type": "亚光硬纸礼盒",
    "exterior_color": "奶白 + 灰色细线",
    "interior_color": "深灰绒布",
    "logo": "压凹品牌字 + 极小金箔"
  },
  "contents": {
    "items": [
      "{argument name=\"content 1\" default=\"主玻璃瓶\"}",
      "{argument name=\"content 2\" default=\"配件 / 说明卡\"}"
    ]
  },
  "scene": {
    "background_surface": "暖灰色亚光石板",
    "extra_decorations": []
  },
  "constraints": {
    "must_feel": "克制、有体面感"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "包装展示图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给品类与品牌即可。自动决定包装类型、内容物组合、配色与装饰，但必须维持包装为视觉中心",
  "constraints": {
    "must_feel": "可以直接用作品牌官网或电商页 hero"
  }
}
```

## 避免事项

- 内容物超过 6 件就开始杂乱，建议 3-5 件
- 不要把内容物全部塞回盒里，至少 1 件半露或前置
- 不要用强反光金属面做背景（会让金箔 logo 看不清）
- 不要在画面里塞品牌之外的其他 logo
- 不要让礼盒呈现“快递箱拆开”那种廉价感
- 不要使用过于饱和的彩色背景，让盒子的颜色失真
