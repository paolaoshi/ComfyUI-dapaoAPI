# 极简氛围插画模板

本文件用于生成“极简留白 / 强氛围” 插画：

- 极简海报
- 文学性氛围图
- 品牌情绪图
- 公众号文末图
- 桌面 / 手机壁纸

特征：

- 大留白
- 单一主体或极少元素
- 一种主导色
- 强情绪 / 强气质
- 文字（如有）极少

## 适用范围

- 文学性氛围图
- 极简海报
- 品牌情绪图
- 壁纸 / 文末图

## 何时使用

- 用户提到“极简 / 留白 / 氛围 / 一种心情 / 文学风”
- 用户希望视觉以“情绪为先”，不需要叙事

不要使用：

- 治愈日常（用 `healing-scene.md`）
- 概念大场景（用 `concept-scene.md`）
- 童书插画（用 `picture-book-scene.md`）

## 缺失信息优先提问顺序

1. 一种心情 / 一句话
2. 主体（一个人 / 一只鸟 / 一棵树 / 抽象图形）
3. 主导色
4. 是否需要文字
5. 比例

## 主模板：极简留白氛围图

📖 描述

整体大量留白，主体小且偏置，色调统一，文字（如有）只 1 句话。

📝 提示词

```json
{
  "type": "极简留白氛围图",
  "goal": "生成一张以情绪为主、留白极致的极简插画",
  "mood": {
    "feeling": "{argument name=\"feeling\" default=\"安静、独处、深秋\"}",
    "one_sentence": "{argument name=\"one sentence\" default=\"风停了，我也终于停了一下。\"}"
  },
  "subject": {
    "description": "{argument name=\"main subject\" default=\"远处一棵孤零零的小树\"}",
    "scale": "{argument name=\"subject scale\" default=\"占画面 10%\"}",
    "position": "{argument name=\"subject position\" default=\"画面右下\"}"
  },
  "background": {
    "type": "{argument name=\"background\" default=\"米白色雾气 + 微微纸纹\"}",
    "main_color": "{argument name=\"main color\" default=\"米白 + 一抹暖灰\"}"
  },
  "text_overlay": {
    "enabled": "{argument name=\"text enabled\" default=\"true\"}",
    "text": "{argument name=\"text\" default=\"风停了，我也终于停了一下。\"}",
    "position": "{argument name=\"text position\" default=\"画面左上\"}",
    "font_style": "{argument name=\"font style\" default=\"细衬线体\"}",
    "color": "深灰"
  },
  "style": {
    "rendering": "极简插画 + 微纸纹 + 柔和颗粒",
    "lighting": "整体柔光、几乎无戏剧光",
    "color_palette": "≤ 2 种主色"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "留白 ≥ 画面 70%",
      "主体小但不可缺",
      "色调严格统一",
      "情绪通过色 + 留白传达，不靠装饰"
    ],
    "avoid": [
      "次要元素堆叠",
      "颜色多于 2 种",
      "文字超过 1 句",
      "出现品牌 logo"
    ]
  }
}
```

### 参数策略

- 必问：心情、主体
- 可默认：背景、配色、字体
- 可随机：主体小细节

### 自动补全策略

- 心情 → 配色（独处 = 米白；夜晚 = 深蓝；秋 = 暖棕；春 = 樱粉）
- 主体根据心情选（孤独 = 一棵树 / 一只鸟；平静 = 一片海；思念 = 远去的背影）
- 文字 ≤ 18 字

## 变体 1：纯色极简海报

📝 提示词

```json
{
  "type": "纯色极简海报",
  "subject": {
    "description": "{argument name=\"subject\" default=\"一只飞鸟剪影\"}",
    "scale": "5%"
  },
  "background": {
    "type": "纯色",
    "main_color": "{argument name=\"main color\" default=\"深蓝\"}"
  },
  "text_overlay": {
    "text": "{argument name=\"text\" default=\"自由\"}",
    "font_style": "极粗黑体"
  },
  "constraints": {
    "must_feel": "强一句话、克制、概念"
  }
}
```

## 变体 2：抽象图形氛围

📝 提示词

```json
{
  "type": "抽象图形氛围图",
  "subject": {
    "description": "{argument name=\"abstract\" default=\"两个相切的圆\"}",
    "scale": "30%"
  },
  "constraints": {
    "must_feel": "概念、设计感、品牌资产"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "极简氛围图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给一句心情或一个词，自动决定主体、配色、文字、比例",
  "constraints": {
    "must_feel": "可做壁纸 / 文末图"
  }
}
```

## 避免事项

- 不要让画面塞满
- 不要使用 > 2 种主色
- 不要让文字超过 18 字
- 不要让主体居正中（极简通常偏置）
- 不要使用花哨字体
