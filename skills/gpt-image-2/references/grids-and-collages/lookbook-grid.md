# Lookbook / 9 宫格信息图模板

本文件用于"一张图里有 N 格主题清单"：

- 7 日穿搭 lookbook
- 9 宫格 self-care 清单
- 一周食谱 lookbook
- 月度计划 9 宫格
- 主题清单图（10 个 best、7 天习惯）

特征：

- 多格清单（7 / 9 / 12）
- 每格独立可读
- 通常带编号 / 日期 / 标签
- 无强叙事，重清单展示
- 顶部主标题 + 底部小总结

## 适用范围

- 穿搭 lookbook
- 食谱周历
- 习惯打卡卡片
- TOP N 清单视觉

## 何时使用

- 用户提到"7 日 / 9 宫格 / 月度 / lookbook / TOP N"
- 用户希望一张图能列完一个清单

不要使用：

- 营销 banner 套装（用 `banner-grid-2x2.md`）
- 关系图（用 `storyboards-and-sequences/character-relationship-diagram.md`）
- 表情九宫格（用 `avatars-and-profile/character-grid-portrait.md`）

## 缺失信息优先提问顺序

1. 主题（穿搭 / 食谱 / 习惯 / TOP）
2. 格子数（7 / 9 / 12）
3. 每格内容
4. 是否带编号 / 日期 / 标签
5. 风格：拍照实拍 / 插画 / 极简
6. 比例

## 主模板：7 日穿搭 lookbook

📖 描述

整体一张图，顶部有标题，主体为 7 格穿搭，每格是一个全身搭配，底部有简短风格总结。

📝 提示词

```json
{
  "type": "7 日穿搭 lookbook",
  "goal": "生成一张可发小红书 / Instagram 的 7 日穿搭信息图",
  "title_block": {
    "main_title": "{argument name=\"main title\" default=\"一周穿什么\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"7 days · 7 outfits\"}",
    "position": "顶部居中"
  },
  "subject": {
    "model": "{argument name=\"model description\" default=\"东亚年轻女性，自然微笑\"}",
    "consistency": "7 格里必须是同一人"
  },
  "layout": {
    "format": "{argument name=\"layout\" default=\"上 4 + 下 3 错位排版\"}",
    "panel_count": 7,
    "panel_design": {
      "label_top": "{argument name=\"label format\" default=\"DAY 1 / MON\"}",
      "outfit_caption": "1 句话风格描述"
    }
  },
  "outfits": [
    {"day": 1, "label": "MON", "style": "{argument name=\"day 1\" default=\"通勤白衬衫 + 米色西裤\"}"},
    {"day": 2, "label": "TUE", "style": "{argument name=\"day 2\" default=\"针织开衫 + 牛仔裤\"}"},
    {"day": 3, "label": "WED", "style": "{argument name=\"day 3\" default=\"连衣裙 + 平底鞋\"}"},
    {"day": 4, "label": "THU", "style": "{argument name=\"day 4\" default=\"运动卫衣 + 短裙\"}"},
    {"day": 5, "label": "FRI", "style": "{argument name=\"day 5\" default=\"皮衣 + 黑直筒裤\"}"},
    {"day": 6, "label": "SAT", "style": "{argument name=\"day 6\" default=\"棉麻衬衫 + 阔腿裤\"}"},
    {"day": 7, "label": "SUN", "style": "{argument name=\"day 7\" default=\"卫衣 + 运动短裤\"}"}
  ],
  "style": {
    "art_style": "{argument name=\"art style\" default=\"日杂时尚摄影 + 米色背景\"}",
    "color_palette": "{argument name=\"color palette\" default=\"米色 + 大地色 + 黑\"}"
  },
  "footer": {
    "summary": "{argument name=\"summary\" default=\"工作日通勤 + 周末松弛\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "7 格里是同一人",
      "穿搭风格符合一周节奏",
      "色板严格统一",
      "标签字体一致"
    ],
    "avoid": [
      "7 格里像不同人",
      "色板出现高饱和荧光色",
      "穿搭风格漂移到完全不搭",
      "字体超过 2 种"
    ]
  }
}
```

### 参数策略

- 必问：主题、模特描述、7 个穿搭
- 可默认：layout、风格、色板
- 可随机：背景细节

### 自动补全策略

- 用户给"风格关键词"（极简 / 复古 / 街头）时：自动展开 7 套穿搭
- 默认 7 格 + 错位排版
- 默认日杂摄影风

## 变体 1：9 宫格 self-care 清单

📝 提示词

```json
{
  "type": "9 宫格 self-care 清单",
  "title_block": {
    "main_title": "{argument name=\"main title\" default=\"每日自我关照 9 件事\"}"
  },
  "layout": {
    "format": "3x3 grid",
    "panel_count": 9
  },
  "outfits": [
    {"label": "1", "style": "8 杯水"},
    {"label": "2", "style": "10 分钟拉伸"},
    {"label": "3", "style": "晒 15 分钟太阳"},
    {"label": "4", "style": "深呼吸"},
    {"label": "5", "style": "记 3 件感谢"},
    {"label": "6", "style": "听一首喜欢的歌"},
    {"label": "7", "style": "和家人通话"},
    {"label": "8", "style": "10 页书"},
    {"label": "9", "style": "11 点睡觉"}
  ],
  "style": {
    "art_style": "极简插画 + 柔色"
  },
  "constraints": {
    "must_feel": "可作为打卡海报"
  }
}
```

## 变体 2：TOP 12 清单图

📝 提示词

```json
{
  "type": "TOP 12 清单图",
  "title_block": {
    "main_title": "{argument name=\"main title\" default=\"2026 年最值得读的 12 本书\"}"
  },
  "layout": {
    "format": "3x4 grid",
    "panel_count": 12
  },
  "constraints": {
    "must_feel": "推荐感 + 可分享"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "Lookbook / 清单自动补全",
  "mode": "auto-fill",
  "rule": "用户给主题，自动决定格数、内容、风格",
  "constraints": {
    "must_feel": "可发小红书"
  }
}
```

## 避免事项

- 不要让格数超过 16
- 不要让格子大小差异 > 2x（除非主图规则一致）
- 不要让背景配色与主题脱节
- 不要让标题字号 / 字体多种
- 不要让一个 lookbook 里出现多个不同模特（保持身份一致）
