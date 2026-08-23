# 品牌主海报模板

本文件用于生成“一张能代表品牌某一阶段表达的主海报”：

- 新品发布主海报
- 季度 campaign 主图
- 品牌升级主图
- 节日活动主海报
- 公司一周年主图

特征：

- 一句强 slogan
- 视觉中心明确
- 品牌色严格统一
- 适合横屏 / 竖屏 / 方屏多版本

## 适用范围

- 单张品牌主海报
- 大型 campaign 主视觉
- 节日 / 周年 / 重要节点主图

## 何时使用

- 用户提到“品牌海报 / 主视觉 / KV / 活动主图 / slogan 海报”
- 用户希望一张图能代表品牌

不要使用：

- 系列主视觉（用 `campaign-kv.md`）
- Web banner（用 `banner-hero.md`）
- 杂志封面（用 `editorial-cover.md`）

## 缺失信息优先提问顺序

1. 品牌名 + 行业
2. 主题 / slogan
3. 视觉调性：未来感 / 复古 / 极简 / 国潮 / 街头
4. 是否有人物 / 产品 / 场景
5. 比例：竖屏 / 横屏 / 方形
6. 色板

## 主模板：单张品牌主海报

📖 描述

整体一张海报，主视觉居中或大占比，slogan 清晰，品牌 logo 在角落，适合作为单图传播主图。

📝 提示词

```json
{
  "type": "品牌主海报",
  "goal": "生成一张能直接作为发布会主图、活动主视觉、社交首图的品牌主海报",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"AURORA\"}",
    "industry": "{argument name=\"industry\" default=\"消费电子\"}"
  },
  "visual_tone": {
    "aesthetic": "{argument name=\"aesthetic\" default=\"极简未来感\"}",
    "color_palette": "{argument name=\"color palette\" default=\"深蓝 + 银白 + 紫罗兰高光\"}",
    "lighting": "{argument name=\"lighting\" default=\"边缘冷光 + 中央柔光\"}"
  },
  "centerpiece": {
    "type": "{argument name=\"centerpiece type\" default=\"产品\"}",
    "description": "{argument name=\"centerpiece description\" default=\"全新一代旗舰耳机，悬浮在画面中央，1/3 处有微微辉光\"}",
    "scale": "{argument name=\"scale\" default=\"占画面 50%\"}"
  },
  "slogan": {
    "main": "{argument name=\"main slogan\" default=\"听见，未被听见的一切\"}",
    "sub": "{argument name=\"sub slogan\" default=\"AURORA Pro · 全新一代主动降噪\"}"
  },
  "logo_placement": {
    "position": "{argument name=\"logo position\" default=\"右下角\"}",
    "size": "适中，不抢主视觉"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4 竖版\"}",
  "constraints": {
    "must_keep": [
      "主视觉作为视觉锚点",
      "slogan 不超过 12 字",
      "品牌 logo 必须出现且可读",
      "色板严格一致"
    ],
    "avoid": [
      "信息密度过高",
      "出现额外品牌元素",
      "字体多于 2 种",
      "背景颜色与主视觉融为一体"
    ]
  }
}
```

### 参数策略

- 必问：品牌、slogan、主视觉类型、比例
- 可默认：色板、灯光、logo 位置
- 可随机：背景纹理细节

### 自动补全策略

- 用户给品牌 + 行业，自动选调性（消费电子 = 未来感，国潮 = 暖色，零售 = 暖灰）
- slogan 默认 8-12 字
- logo 默认右下角

## 变体 1：人物 + 产品双主体

📝 提示词

```json
{
  "type": "人物 + 产品双主体海报",
  "centerpiece": {
    "type": "human + product",
    "human": "{argument name=\"human\" default=\"东亚年轻女性，自然微笑\"}",
    "product": "{argument name=\"product\" default=\"白色精华瓶\"}",
    "composition": "人物在右、产品在左 1/3 处"
  },
  "constraints": {
    "must_feel": "信任、品质、品牌人设清晰"
  }
}
```

## 变体 2：纯文字主海报

📝 提示词

```json
{
  "type": "纯文字品牌主海报",
  "slogan": {
    "main": "{argument name=\"slogan\" default=\"我们要赢，但更要把伙伴一起带上\"}"
  },
  "visual_tone": {
    "aesthetic": "极简、留白大、字体即视觉"
  },
  "constraints": {
    "must_feel": "态度、价值观、信仰感"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "品牌主海报自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给品牌与节点，自动选调性、色板、slogan、主视觉",
  "constraints": {
    "must_feel": "可上线传播"
  }
}
```

## 避免事项

- 不要让 slogan 超过 12 字
- 不要让 logo 抢主视觉
- 不要在一张海报里放多个产品
- 不要使用 3 种以上字体
- 不要让背景出现可识别第三方品牌
