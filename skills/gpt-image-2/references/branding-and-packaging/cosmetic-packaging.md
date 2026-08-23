# 化妆品 / 护肤品包装模板

本文件用于"化妆品 / 护肤品瓶身、盒装、套装"包装设计视觉：

- 单瓶护肤品包装设计
- 化妆品系列套装包装
- 礼盒装包装
- 美妆电商主图（含包装）

特征：

- 强调瓶身形态 + 标签 + 材质
- 强调材质质感（玻璃 / 磨砂 / 金属盖）
- 通常含品牌名 + 产品名 + 容量
- 配色克制，高级感
- 单瓶或系列展示

## 适用范围

- 护肤品 / 化妆品包装设计
- 美妆礼盒
- 美妆电商主图

## 何时使用

- 用户提到"护肤品 / 化妆品 / 包装设计 / 瓶子"
- 用户希望产品包装的视觉

不要使用：

- 食品 / 饮料标签（用 `beverage-label-design.md`）
- 礼盒摄影（用 `product-visuals/packaging-showcase.md`）
- 单品白底图（用 `product-visuals/white-background-product.md`）

## 缺失信息优先提问顺序

1. 品牌名 + 风格定位（高奢 / 极简 / 文艺 / Y2K）
2. 产品类型（精华 / 面霜 / 洁面 / 香水）
3. 瓶身材质（玻璃 / 磨砂玻璃 / PETG / 陶瓷）
4. 主色 1-2 个
5. 单品 / 套装
6. 容量

## 主模板：单瓶护肤精华包装设计

📖 描述

整体一张图，主体为一支护肤精华瓶 + 外盒，背景为简洁场景。

📝 提示词

```json
{
  "type": "护肤精华单瓶包装设计",
  "goal": "生成一张可作为产品发布主图 / 包装提案 / 电商主图的化妆品包装视觉",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"LUMEN\"}",
    "positioning": "{argument name=\"positioning\" default=\"科学护肤 + 极简\"}"
  },
  "product": {
    "name": "{argument name=\"product name\" default=\"光子修护精华\"}",
    "subtitle": "{argument name=\"product subtitle\" default=\"PHOTON REPAIR SERUM\"}",
    "volume": "{argument name=\"volume\" default=\"30ml\"}",
    "form": "{argument name=\"bottle form\" default=\"圆柱形玻璃瓶 + 滴管\"}",
    "key_ingredient": "{argument name=\"ingredient\" default=\"5% 烟酰胺\"}"
  },
  "design": {
    "bottle_material": "{argument name=\"bottle material\" default=\"磨砂透明玻璃\"}",
    "label_material": "{argument name=\"label material\" default=\"哑光不干胶 + 烫银字\"}",
    "primary_color": "{argument name=\"primary color\" default=\"#0F4C81 深蓝\"}",
    "accent_color": "{argument name=\"accent color\" default=\"哑银\"}",
    "typography": "{argument name=\"typography\" default=\"现代 sans + 中文小字号\"}"
  },
  "outer_box": {
    "enabled": "{argument name=\"outer box\" default=\"true\"}",
    "shape": "{argument name=\"box shape\" default=\"立方体硬纸盒\"}",
    "finish": "{argument name=\"box finish\" default=\"哑光纸 + 烫银 logo\"}"
  },
  "scene": {
    "background": "{argument name=\"background\" default=\"米白色丝绸 + 柔光\"}",
    "props": "{argument name=\"props\" default=\"一片透明亚克力板 + 几滴水珠\"}",
    "lighting": "{argument name=\"lighting\" default=\"高级感软光 + 顶部主光\"}"
  },
  "format": {
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"4:5\"}",
    "composition": "瓶子主体居中偏右 + 外盒在后侧"
  },
  "constraints": {
    "must_keep": [
      "瓶身材质质感真实（玻璃应有反光与折射）",
      "标签字体清晰可读",
      "整体配色 ≤ 3 种",
      "高级感、克制"
    ],
    "avoid": [
      "标签字体 > 2 种",
      "背景过亮压过产品",
      "瓶身比例失真",
      "出现廉价塑料感（如果不是有意）"
    ]
  }
}
```

### 参数策略

- 必问：品牌名、产品类型、瓶身形态
- 可默认：材质、配色、外盒、场景
- 可随机：道具细节

### 自动补全策略

- 用户给品牌定位 + 产品类型时：自动展开瓶身 / 标签 / 配色 / 场景
- 高奢 = 黑金 / 极简 = 白蓝 / 文艺 = 米色木质 / Y2K = 高饱和
- 默认 4:5 竖版

## 变体 1：化妆品系列套装

📝 提示词

```json
{
  "type": "化妆品系列套装",
  "product": {
    "form": "5 件套（洁面 + 化妆水 + 精华 + 面霜 + 防晒）"
  },
  "design": {
    "consistency_rule": "5 件包装严格统一系统：相同瓶身比例 + 相同字体 + 相同配色"
  },
  "scene": {
    "composition": "5 件按高度排开 + 居中"
  },
  "constraints": {
    "must_feel": "套装级 + 系列识别度"
  }
}
```

## 变体 2：礼盒装

📝 提示词

```json
{
  "type": "化妆品礼盒装",
  "outer_box": {
    "enabled": true,
    "shape": "扁长方形礼盒（半开）",
    "finish": "丝绒包面 + 烫金 logo + 缎带"
  },
  "scene": {
    "background": "深色背景 + 聚光"
  },
  "constraints": {
    "must_feel": "节日 / 礼物级"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "化妆品包装自动补全",
  "mode": "auto-fill",
  "rule": "用户给品牌 + 产品类型 + 风格定位，自动决定瓶身 / 标签 / 外盒 / 场景",
  "constraints": {
    "must_feel": "可发产品发布会"
  }
}
```

## 避免事项

- 不要让产品名 + 容量字号差异过大
- 不要让标签字体超过 2 种
- 不要让瓶身比例失真
- 不要让背景过亮压过产品
- 不要让品牌 logo 出现在不显眼位置
- 不要让"高奢定位"的产品出现廉价材质
