# Campaign Key Visual 模板

本文件用于生成“一组 campaign 主视觉”，强调“可延展、可复用、可成系列”：

- 季度 campaign 主视觉
- 节日 campaign 主图
- 跨平台投放统一视觉
- 联名 campaign 主图

特征：

- 主视觉强调“可拓展”到 banner / story / 短视频封面
- 由 1 个 anchor visual + 1 套 layout system 组成
- 强调 campaign claim
- 色板严格统一

## 适用范围

- 全新 campaign 主视觉系统
- 节日 / 双 11 / 大促 campaign
- 联名 campaign

## 何时使用

- 用户提到“campaign / 大促 / 季度活动 / KV / 系列主视觉”
- 用户希望视觉能延展为 banner / story / 海报

不要使用：

- 单张品牌海报（用 `brand-poster.md`）
- Web hero（用 `banner-hero.md`）

## 缺失信息优先提问顺序

1. Campaign 主题
2. Campaign 时间窗口
3. Campaign claim（slogan / 主张句）
4. 品牌色 + campaign 专属色
5. 主视觉中心（人物 / 产品 / 概念图形）
6. 是否需要展示衍生 layout

## 主模板：Campaign Key Visual + 衍生

📖 描述

主图为 anchor visual，画面中央有 campaign claim，下方展示衍生 layout（1:1、9:16、16:9）小预览。

📝 提示词

```json
{
  "type": "Campaign Key Visual 主视觉系统",
  "goal": "生成一张能作为 campaign 主图，并展示其衍生版本的视觉系统图",
  "campaign": {
    "name": "{argument name=\"campaign name\" default=\"AURORA Spring Drop 2026\"}",
    "claim": "{argument name=\"campaign claim\" default=\"春日新声，听见每一刻心动\"}",
    "duration": "{argument name=\"duration\" default=\"2026.4.20 - 2026.5.15\"}"
  },
  "visual_system": {
    "color_palette": "{argument name=\"color palette\" default=\"樱粉 + 雾蓝 + 米白\"}",
    "anchor_visual": {
      "description": "{argument name=\"anchor visual\" default=\"少女戴着新款无线耳机，背景为樱花花瓣飘落\"}",
      "composition": "人物在画面 1/3 偏左，留白足够给 claim"
    },
    "graphic_motif": "{argument name=\"motif\" default=\"重复出现的小樱花标志 + 圆点节奏点\"}"
  },
  "claim_typography": {
    "font_style": "{argument name=\"font style\" default=\"现代衬线 + 圆滑细节\"}",
    "color": "深灰 + 樱粉点缀"
  },
  "derivative_layouts": {
    "enabled": "{argument name=\"derivatives enabled\" default=\"true\"}",
    "items": [
      "1:1 社交首图",
      "9:16 短视频封面",
      "16:9 banner"
    ],
    "rule": "三个衍生 layout 在主图下方排成一行展示"
  },
  "logo_placement": {
    "position": "右下角"
  },
  "constraints": {
    "must_keep": [
      "anchor visual 与衍生 layout 保持视觉一致",
      "claim 文字在所有比例下都可读",
      "色板严格统一",
      "品牌 logo 在所有版本都出现"
    ],
    "avoid": [
      "衍生 layout 风格漂移",
      "claim 在小尺寸下不可读",
      "色板出现额外色",
      "anchor visual 主体超出画面"
    ]
  }
}
```

### 参数策略

- 必问：campaign 名、claim、色板、anchor visual
- 可默认：衍生 layout 列表、logo 位置、字体
- 可随机：motif 装饰具体形式

### 自动补全策略

- 用户给主题 + 节点（春 / 夏 / 双 11 / 圣诞），自动选色板与 motif
- claim 默认 12-18 字
- 衍生 layout 默认 3 种比例

## 变体 1：联名 campaign

📝 提示词

```json
{
  "type": "联名 campaign 主视觉",
  "campaign": {
    "name": "{argument name=\"co-brand campaign\" default=\"AURORA × MUJI Limited\"}",
    "claim": "{argument name=\"claim\" default=\"日常之声，安静的力量\"}"
  },
  "visual_system": {
    "color_palette": "灰白 + 暖米 + 一丝品牌色",
    "anchor_visual": {
      "description": "两品牌产品并置 + 日常场景"
    }
  },
  "constraints": {
    "must_feel": "克制、有共同语境、不互相压倒"
  }
}
```

## 变体 2：纯图形 campaign

📝 提示词

```json
{
  "type": "纯图形 campaign 主视觉",
  "visual_system": {
    "anchor_visual": {
      "description": "{argument name=\"motif\" default=\"由品牌字标演化的几何图形\"}"
    },
    "graphic_motif": "{argument name=\"pattern\" default=\"重复 grid + 节奏点\"}"
  },
  "constraints": {
    "must_feel": "概念感强、抽象、属于品牌资产"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "Campaign KV 自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给 campaign 主题 + 时间，自动决定 claim、色板、anchor、衍生",
  "constraints": {
    "must_feel": "可直接进入投放系统"
  }
}
```

## 避免事项

- 不要让衍生 layout 与主图风格分裂
- 不要让 claim 跨越主体（必须留白）
- 不要在一张 KV 系统里出现 > 2 套字体
- 不要把所有比例都画成同一构图（必须真实重新构图）
- 不要让 motif 喧宾夺主
