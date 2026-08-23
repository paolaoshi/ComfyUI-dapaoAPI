# 贴纸套装 / Sticker Set 模板

本文件用于"一张图包含 N 个独立可裁切贴纸"的视觉：

- 趣味动物贴纸
- 角色表情贴纸
- 主题节日贴纸
- 行业 / 兴趣主题贴纸
- iMessage / Telegram 风格贴纸包

特征：

- 一张图里多个独立小元素
- 每个元素有透明 / 白色 / 描边外圈
- 互相不连接
- 可整张图打印或单独裁切
- 风格高度统一

## 适用范围

- 贴纸套装（4-12 个）
- 表情包合集
- 节日礼盒贴纸
- 周边贴纸卡片

## 何时使用

- 用户提到"贴纸 / sticker set / 表情包套装"
- 用户希望一张图里多个独立小元素
- 用户希望每个元素都可独立使用

不要使用：

- 同一角色多表情九宫格（用 `character-grid-portrait.md`）
- 多版本头像（用 `themed-3d-icon.md`）
- 多 panel 故事拼贴（用 `grids-and-collages/mixed-style-multi-panel.md`）

## 缺失信息优先提问顺序

1. 主题（动物 / 食物 / 角色 / 节日 / 心情）
2. 贴纸数量（4 / 6 / 8 / 9 / 12）
3. 风格：手绘 / 3D Q 萌 / 拟物 / Anime
4. 是否带文字标签
5. 配色基调
6. 是否需要白色描边

## 主模板：趣味动物贴纸套装（9 张）

📖 描述

整体 1:1 或 4:3 大图，背景为浅米色，9 个独立贴纸排成 3×3，每个贴纸都有白色描边。

📝 提示词

```json
{
  "type": "贴纸套装 sticker set",
  "goal": "生成一张包含 N 个独立小贴纸的合集图，每个贴纸可单独裁切使用",
  "theme": "{argument name=\"theme\" default=\"趣味动物日常\"}",
  "style": {
    "rendering": "{argument name=\"art style\" default=\"3D Q 萌 + 软光\"}",
    "color_palette": "{argument name=\"color palette\" default=\"暖橙 + 米白 + 浅绿\"}"
  },
  "sticker_design": {
    "outline": "{argument name=\"outline\" default=\"3px 白色描边\"}",
    "shadow": "{argument name=\"shadow\" default=\"轻微底部投影\"}",
    "with_label": "{argument name=\"with label\" default=\"true\"}",
    "label_style": "{argument name=\"label style\" default=\"圆润手写体，深棕色\"}"
  },
  "layout": {
    "background": "{argument name=\"background\" default=\"浅米色 + 微纸纹\"}",
    "grid": "{argument name=\"grid\" default=\"3x3\"}",
    "spacing": "贴纸之间均匀间距",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"1:1\"}"
  },
  "stickers": {
    "count": "{argument name=\"sticker count\" default=\"9\"}",
    "items": [
      "{argument name=\"sticker 1\" default=\"喝咖啡的橘猫 + 标签 'morning'\"}",
      "{argument name=\"sticker 2\" default=\"举着气球的小柴犬 + 标签 'yay'\"}",
      "{argument name=\"sticker 3\" default=\"打哈欠的小熊 + 标签 'sleepy'\"}",
      "{argument name=\"sticker 4\" default=\"戴墨镜的兔子 + 标签 'cool'\"}",
      "{argument name=\"sticker 5\" default=\"抱着花的水豚 + 标签 'love'\"}",
      "{argument name=\"sticker 6\" default=\"跳起来的小狐狸 + 标签 'go'\"}",
      "{argument name=\"sticker 7\" default=\"读书的猫头鹰 + 标签 'study'\"}",
      "{argument name=\"sticker 8\" default=\"吃蛋糕的仓鼠 + 标签 'yum'\"}",
      "{argument name=\"sticker 9\" default=\"挥手的企鹅 + 标签 'hi'\"}"
    ]
  },
  "constraints": {
    "must_keep": [
      "每个贴纸独立、互不连接",
      "整体风格统一不漂移",
      "白色描边均匀",
      "标签字体一致"
    ],
    "avoid": [
      "贴纸大小差异过大",
      "风格混杂（写实 + 卡通）",
      "标签出现错字",
      "背景喧宾夺主"
    ]
  }
}
```

### 参数策略

- 必问：主题、数量
- 可默认：风格、描边、标签
- 可随机：每个贴纸具体造型

### 自动补全策略

- 默认 9 张（3×3）
- 默认带白色描边 + 短标签
- 风格按主题自动选（动物 = Q 萌 / 食物 = 3D 拟物 / 节日 = 节日色）

## 变体 1：节日贴纸套装

📝 提示词

```json
{
  "type": "节日贴纸套装",
  "theme": "{argument name=\"festival\" default=\"圣诞节\"}",
  "style": {
    "color_palette": "圣诞红 + 圣诞绿 + 金"
  },
  "stickers": {
    "count": 6,
    "items": [
      "圣诞树 + 'Merry'",
      "雪人 + 'Joy'",
      "礼盒 + 'Gift'",
      "圣诞老人头像 + 'Ho Ho Ho'",
      "驯鹿 + 'Rudolph'",
      "雪花 + 'Cool'"
    ]
  },
  "constraints": {
    "must_feel": "节日氛围、可分享、可印刷"
  }
}
```

## 变体 2：心情表情贴纸（无文字）

📝 提示词

```json
{
  "type": "心情表情贴纸（无文字）",
  "sticker_design": {
    "with_label": false
  },
  "stickers": {
    "count": 12,
    "items": ["开心", "生气", "委屈", "无语", "笑死", "震惊", "困了", "饿了", "心动", "酷", "尴尬", "拜拜"]
  },
  "constraints": {
    "must_feel": "可直接做表情包"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "贴纸套装自动补全",
  "mode": "auto-fill",
  "rule": "用户给主题，自动决定数量、风格、配色、标签内容",
  "constraints": {
    "must_feel": "可直接打印 / 上传 iMessage"
  }
}
```

## 避免事项

- 不要让贴纸数量超过 16（视觉过密）
- 不要让贴纸大小差异 > 2x
- 不要混合写实与 Q 萌风格
- 不要让标签字体超过 1 种
- 不要让背景出现可识别 logo
- 不要把贴纸彼此重叠（必须独立）
