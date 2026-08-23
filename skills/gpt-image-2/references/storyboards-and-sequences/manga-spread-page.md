# 漫画跨页 / 多分镜页模板

本文件用于"一页内多个不规则分镜叙事"的漫画视觉：

- 单页 5-7 个分镜的漫画
- 跨页 spread（左右两页连贯）
- 心理 / 悬疑 / 战斗 / 日常多分镜
- 同人漫画 / 商业漫画
- 故事板 storyboard

特征：

- 不规则格子
- 大格 + 小格组合
- 有阅读顺序（通常右上 → 左下）
- 含对话框 + 心声 + 旁白
- 风格更"漫画书"而不是 4 格段子

## 适用范围

- 单页多分镜漫画
- 跨页 spread
- 故事板 / 分镜稿
- 同人 / 商业漫画

## 何时使用

- 用户提到"漫画分镜 / spread / 多格漫画 / 故事板"
- 用户希望叙事更复杂、节奏更动感
- 用户希望"漫画书"质感

不要使用：

- 4 格段子（用 `four-panel-comic.md`）
- 单图 KV（用 `anime-key-visual.md`）
- 角色设定稿（用 `portraits-and-characters/character-sheet.md`）

## 缺失信息优先提问顺序

1. 故事概要 / 这一页要讲什么
2. 分镜数量（5-9 格）
3. 主角描述
4. 风格：日漫 / 韩漫 / 美漫 / 同人
5. 阅读方向（日式右往左 / 美式左往右）
6. 是否含色彩或纯黑白

## 主模板：单页多分镜漫画

📖 描述

整体一页漫画，包含 5-7 个不规则分镜，按阅读顺序展开一段叙事。

📝 提示词

```json
{
  "type": "单页多分镜漫画",
  "goal": "生成一张完整的单页漫画，含多个分镜，叙事节奏紧凑",
  "story": {
    "summary": "{argument name=\"story summary\" default=\"主角接到神秘电话，决定独自前往\"}",
    "main_character": "{argument name=\"main character\" default=\"年轻女性侦探，短发，黑色风衣\"}",
    "supporting": "{argument name=\"supporting\" default=\"无\"}"
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"日式黑白漫画 + 网点 + 强阴影\"}",
    "tone": "{argument name=\"tone\" default=\"悬疑 + 紧张\"}",
    "color": "{argument name=\"color\" default=\"黑白 + 灰阶\"}"
  },
  "page_layout": {
    "panel_count": "{argument name=\"panel count\" default=\"6\"}",
    "reading_direction": "{argument name=\"reading direction\" default=\"日式：从右到左、从上到下\"}",
    "panels": [
      {
        "id": 1,
        "size": "大格 跨上半部分",
        "scene": "{argument name=\"panel 1\" default=\"主角侧脸特写，电话靠耳边\"}",
        "text": "{argument name=\"text 1\" default=\"旁白：那通电话，改变了一切\"}"
      },
      {
        "id": 2,
        "size": "中格 右下",
        "scene": "{argument name=\"panel 2\" default=\"特写电话听筒里的杂音\"}",
        "text": "{argument name=\"text 2\" default=\"对方：今晚十点，老地方\"}"
      },
      {
        "id": 3,
        "size": "小格 左下",
        "scene": "{argument name=\"panel 3\" default=\"主角眼神特写，瞳孔放大\"}",
        "text": "{argument name=\"text 3\" default=\"心声：又是他\"}"
      },
      {
        "id": 4,
        "size": "中格 右",
        "scene": "{argument name=\"panel 4\" default=\"主角穿上风衣的动作分镜\"}",
        "text": ""
      },
      {
        "id": 5,
        "size": "中格 中",
        "scene": "{argument name=\"panel 5\" default=\"主角推开门，雨夜街道\"}",
        "text": ""
      },
      {
        "id": 6,
        "size": "大格 跨下半部分",
        "scene": "{argument name=\"panel 6\" default=\"主角背影远去，路灯昏黄\"}",
        "text": "{argument name=\"text 6\" default=\"旁白：这是赴约，还是赴死\"}"
      }
    ]
  },
  "dialogue_design": {
    "balloon_style": "白底 + 黑描边 + 尖角指向",
    "narration_box": "矩形 + 灰底 + 黑边",
    "thought_balloon": "云形 + 虚线尾巴",
    "font_style": "无衬线漫画体"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "分镜大小有节奏（大 + 小 + 大）",
      "阅读顺序清晰",
      "主角在多格中保持一致",
      "对话框不挡关键人物动作"
    ],
    "avoid": [
      "分镜全部一样大（节奏单调）",
      "阅读顺序混乱",
      "主角形象漂移",
      "色调突变（黑白页里突然有彩色）"
    ]
  }
}
```

### 参数策略

- 必问：故事概要、分镜数、主角
- 可默认：风格、阅读方向、对话框样式
- 可随机：背景细节

### 自动补全策略

- 用户只给故事时：自动决定 5-7 格分镜节奏
- 默认日式黑白漫画 + 网点
- 默认日式阅读方向

## 变体 1：跨页 spread（左右两页）

📝 提示词

```json
{
  "type": "跨页 spread 漫画",
  "page_layout": {
    "panel_count": "8-12（左右两页加起来）",
    "format": "横向 spread，画面分左右两页"
  },
  "aspect_ratio": "16:11",
  "constraints": {
    "must_feel": "左右两页连贯，中央 gutter 不要切到关键元素"
  }
}
```

## 变体 2：彩色商业漫画页

📝 提示词

```json
{
  "type": "彩色商业漫画页",
  "style": {
    "color": "全彩 + 平涂 + 数字漫画质感",
    "art_style": "美漫 / 韩漫 风"
  },
  "constraints": {
    "must_feel": "可作为商业漫画连载页"
  }
}
```

## 变度 3：自动补全模式

📝 提示词

```json
{
  "type": "漫画跨页自动补全",
  "mode": "auto-fill",
  "rule": "用户给一段故事，自动切分镜、排版、对话",
  "constraints": {
    "must_feel": "出版社编辑可直接放入排版"
  }
}
```

## 避免事项

- 不要让分镜全部等大
- 不要让阅读顺序难以辨认
- 不要让对话框挡脸 / 挡动作
- 不要在黑白漫画页里突然出现强彩色
- 不要让主角形象在不同格里像不同人
- 跨页时不要让关键元素正好在中央装订线
