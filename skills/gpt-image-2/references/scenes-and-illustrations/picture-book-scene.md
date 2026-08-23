# 童书 / 绘本场景插画模板

本文件用于生成“童书 / 绘本 / 儿童内容” 风格插画：

- 童书内页 / 封面
- 儿童内容公众号头图
- 绘本风周边
- 教育内容插图
- 节日卡片

特征：

- 柔和水彩 / 蜡笔 / 拼贴风
- 角色 Q 萌
- 颜色温暖
- 信息清晰、易理解
- 留有故事感

## 适用范围

- 童书内页 / 封面
- 教育内容插图
- 儿童节日卡片
- 童趣品牌插图

## 何时使用

- 用户提到“绘本 / 童书 / 儿童 / 蜡笔风 / 水彩童书风”
- 用户希望温暖、童趣、故事感

不要使用：

- 治愈日常（用 `healing-scene.md`）
- 概念大片（用 `concept-scene.md`）
- 极简氛围（用 `minimalist-mood-scene.md`）

## 缺失信息优先提问顺序

1. 故事 / 主题
2. 主角（孩子 / 动物）
3. 场景
4. 风格：水彩 / 蜡笔 / 拼贴 / Anime 童趣
5. 是否包含文字
6. 比例

## 主模板：童书内页插画

📖 描述

整体一页童书插画，主角 Q 萌可爱，场景柔光，可包含 1 句故事文本。

📝 提示词

```json
{
  "type": "童书内页插画",
  "goal": "生成一张可直接作为童书内页的温暖插画",
  "story": {
    "theme": "{argument name=\"story theme\" default=\"小熊第一次去森林冒险\"}",
    "scene": "{argument name=\"scene\" default=\"晨雾中的森林小径\"}",
    "moment": "{argument name=\"story moment\" default=\"小熊抬头看到第一缕阳光透过树叶\"}"
  },
  "main_character": {
    "description": "{argument name=\"main character\" default=\"圆乎乎的小熊，背着小布包\"}",
    "expression": "{argument name=\"expression\" default=\"好奇 + 微笑\"}",
    "pose": "{argument name=\"pose\" default=\"抬头仰望\"}"
  },
  "secondary_characters": {
    "items": [
      "{argument name=\"secondary 1\" default=\"飞过的小鸟\"}",
      "{argument name=\"secondary 2\" default=\"探出头的兔子\"}"
    ]
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"水彩绘本风 + 柔和勾线\"}",
    "color_palette": "{argument name=\"color palette\" default=\"暖橙 + 柔绿 + 米白\"}",
    "rendering": "颗粒感纸纹 + 柔和水彩 + 简单线条"
  },
  "text_overlay": {
    "enabled": "{argument name=\"text enabled\" default=\"true\"}",
    "text": "{argument name=\"text\" default=\"小熊抬起头，世界忽然变得很大。\"}",
    "position": "{argument name=\"text position\" default=\"画面下方居中\"}",
    "font_style": "圆润手写体"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"4:3\"}",
  "constraints": {
    "must_keep": [
      "主角作为视觉中心",
      "整体配色温暖治愈",
      "文字与画面留白合理",
      "次要角色不抢主角"
    ],
    "avoid": [
      "出现成年人复杂表情",
      "色调过冷",
      "场景过于写实",
      "出现品牌 logo"
    ]
  }
}
```

### 参数策略

- 必问：主角、场景、文字
- 可默认：风格、配色、字体
- 可随机：次要角色

### 自动补全策略

- 主角 Q 萌优先（动物 > 孩子）
- 风格默认水彩绘本
- 文字 ≤ 25 字
- 比例默认 4:3 或 3:4

## 变体 1：节日卡片

📝 提示词

```json
{
  "type": "节日童趣卡片",
  "story": {
    "theme": "{argument name=\"festival\" default=\"圣诞节\"}",
    "scene": "雪夜小屋"
  },
  "main_character": {
    "description": "戴红帽的小狐狸"
  },
  "text_overlay": {
    "text": "Merry Christmas",
    "position": "顶部"
  },
  "constraints": {
    "must_feel": "节日氛围、温暖、可分享"
  }
}
```

## 变体 2：教育插图

📝 提示词

```json
{
  "type": "儿童教育插图",
  "story": {
    "theme": "{argument name=\"concept\" default=\"刷牙的正确顺序\"}",
    "scene": "浴室"
  },
  "main_character": {
    "description": "拿牙刷的小孩"
  },
  "text_overlay": {
    "enabled": true,
    "text": "1. 漱口 → 2. 上牙 → 3. 下牙 → 4. 漱口"
  },
  "constraints": {
    "must_feel": "易懂、可教学、亲切"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "童书插画自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给主题，自动决定主角、场景、风格、文字",
  "constraints": {
    "must_feel": "可印成绘本"
  }
}
```

## 避免事项

- 不要让人物五官写实
- 不要让场景过暗
- 不要让文字超过 25 字
- 不要使用 > 3 种字体
- 不要出现成年人才理解的概念
