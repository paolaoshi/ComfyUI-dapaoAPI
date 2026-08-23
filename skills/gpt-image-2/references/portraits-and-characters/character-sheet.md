# 角色设定 / 三视图模板

本文件用于生成“一个角色的完整设定页 / 三视图 / 表情集 / 配饰集” 视觉：

- 动画 / 游戏角色设定
- IP 形象设定
- 漫画主角设定
- 同人角色设定
- 品牌吉祥物设定

特征：

- 一页内多个视角 / 多种姿势
- 标注配色 / 服装细节 / 关键尺寸
- 网格化排版
- 类似动画工作室设定稿

## 适用范围

- 角色三视图（前 / 侧 / 后）
- 表情九宫格
- 服装变体
- 配饰 / 武器集

## 何时使用

- 用户提到“角色设定 / 三视图 / 设定稿 / 表情集 / 角色 sheet”
- 用户希望一张图能展示一个角色的完整方案

不要使用：

- 单张人物肖像（用 `professional-portrait.md` / `founder-portrait.md`）
- 虚拟主播个人卡（用 `virtual-host.md`）

## 缺失信息优先提问顺序

1. 角色名 / 概念
2. 风格：anime / 3D 卡通 / 写实 / 像素
3. 性别 / 年龄 / 种族
4. 服装风格
5. sheet 类型：三视图 / 表情集 / 服装变体 / 综合
6. 是否包含标注与配色

## 主模板：角色综合设定 sheet

📖 描述

一张 4:3 或 3:4 大图，包含三视图（前 / 侧 / 后），表情九宫格，服装与配饰特写，配色板。

📝 提示词

```json
{
  "type": "角色综合设定 sheet",
  "goal": "生成一张可直接用于动画 / 游戏 / IP 立项的角色综合设定稿",
  "character": {
    "name": "{argument name=\"character name\" default=\"霜白·诺娜\"}",
    "concept": "{argument name=\"character concept\" default=\"冬日守望者，孤独但坚定\"}",
    "art_style": "{argument name=\"art style\" default=\"anime + 半写实\"}",
    "gender": "{argument name=\"gender\" default=\"少女\"}",
    "age_setting": "{argument name=\"age setting\" default=\"18 岁\"}"
  },
  "sections": {
    "three_view": {
      "enabled": "{argument name=\"three view enabled\" default=\"true\"}",
      "items": ["正面全身", "侧面全身", "背面全身"],
      "annotations": ["发色", "瞳色", "服装层次", "配饰"]
    },
    "expression_grid": {
      "enabled": "{argument name=\"expression grid enabled\" default=\"true\"}",
      "count": "{argument name=\"expression count\" default=\"9\"}",
      "items": ["微笑", "大笑", "害羞", "生气", "委屈", "惊讶", "认真", "迷茫", "睡颜"]
    },
    "outfit_variants": {
      "enabled": "{argument name=\"outfit variants enabled\" default=\"true\"}",
      "count": "{argument name=\"outfit count\" default=\"3\"}",
      "items": [
        "{argument name=\"outfit 1\" default=\"日常哥特连衣裙\"}",
        "{argument name=\"outfit 2\" default=\"战斗装：白银铠甲\"}",
        "{argument name=\"outfit 3\" default=\"便服：毛衣 + 长裙\"}"
      ]
    },
    "props_and_weapons": {
      "enabled": "{argument name=\"props enabled\" default=\"true\"}",
      "items": ["{argument name=\"prop 1\" default=\"冰晶法杖\"}", "{argument name=\"prop 2\" default=\"雪绒挂坠\"}"]
    },
    "color_palette": {
      "enabled": "{argument name=\"palette enabled\" default=\"true\"}",
      "main": "{argument name=\"palette main\" default=\"冰蓝 / 月白 / 银灰\"}",
      "accent": "{argument name=\"palette accent\" default=\"淡粉\"}"
    }
  },
  "layout": {
    "background": "{argument name=\"background\" default=\"米白色 grid 背景，干净像设定稿\"}",
    "grid": "整张 sheet 用细线分区，每区域有标题 + 标注"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"4:3\"}",
  "constraints": {
    "must_keep": [
      "三视图比例严格一致",
      "表情同一脸型，只换表情",
      "服装变体保留同一面相",
      "配色板与角色实际配色一致"
    ],
    "avoid": [
      "三视图角色像三个人",
      "表情九宫格里有重复",
      "标注线交叉",
      "背景喧宾夺主"
    ]
  }
}
```

### 参数策略

- 必问：角色名、风格、性别、概念
- 可默认：sheet 类型组合、背景、layout
- 可随机：表情类型、配饰造型

### 自动补全策略

- 风格自动按 IP 类型选（少女 anime / 男性写实 / 吉祥物 3D）
- 默认包含三视图 + 表情九宫格 + 配色板
- 无说明时不出现武器

## 变体 1：纯表情九宫格

📝 提示词

```json
{
  "type": "角色表情九宫格 sheet",
  "sections": {
    "three_view": { "enabled": false },
    "expression_grid": { "enabled": true, "count": 9 },
    "outfit_variants": { "enabled": false }
  },
  "constraints": {
    "must_feel": "可作为表情包 / 直播表情资源"
  }
}
```

## 变体 2：服装变体集

📝 提示词

```json
{
  "type": "角色服装变体集 sheet",
  "sections": {
    "three_view": { "enabled": false },
    "expression_grid": { "enabled": false },
    "outfit_variants": { "enabled": true, "count": 5 }
  },
  "constraints": {
    "must_feel": "可作为衣装企划稿"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "角色设定自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给一句概念，自动生成全套设定（视图、表情、服装、配色）",
  "constraints": {
    "must_feel": "可立项"
  }
}
```

## 避免事项

- 不要让三视图比例不一致（最常见错误）
- 不要让表情九宫格出现重复
- 不要在设定稿背景里加复杂场景
- 不要让标注遮住角色身体
- 不要使用真实版权角色作为参考
