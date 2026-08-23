# 4 格漫画模板

本文件用于"4 格漫画 / 讽刺漫画 / 段子漫画"视觉：

- 反转 4 格段子
- 讽刺产品广告漫画
- 短故事 4 格
- 自媒体 4 格漫画
- 食物 / 心情 4 格

特征：

- 4 个等大格子（2×2 或 1×4）
- 每格独立场景但故事连贯
- 起 / 承 / 转 / 合 节奏
- 通常带对话气泡 / 心声
- 风格统一

## 适用范围

- 自媒体 4 格漫画
- 讽刺广告 4 格
- 反转段子
- 心情日记漫画

## 何时使用

- 用户提到"4 格 / 四格漫画 / 段子漫画 / 讽刺漫画"
- 用户希望讲一个有节奏的小故事
- 用户希望有反转 / 笑点

不要使用：

- 多分镜跨页漫画（用 `manga-spread-page.md`）
- 无叙事的图标拼贴（用 `grids-and-collages/banner-grid-2x2.md`）
- 单图 KV（用 `anime-key-visual.md`）

## 缺失信息优先提问顺序

1. 主题 / 故事核心
2. 主角描述
3. 4 格分别讲什么（起承转合）
4. 风格（手绘日漫 / 极简线稿 / 美式卡通 / 国漫）
5. 是否有对话气泡
6. 比例（1:1 / 4:3 / 9:16）

## 主模板：2×2 反转 4 格漫画

📖 描述

整体一张图，分为 2×2 四格，按起 / 承 / 转 / 合讲一个有反转的小故事。

📝 提示词

```json
{
  "type": "2x2 反转 4 格漫画",
  "goal": "生成一张 2×2 四格漫画，讲一个有节奏与反转的小故事",
  "story": {
    "theme": "{argument name=\"theme\" default=\"减肥的人和半夜的炸鸡\"}",
    "structure": "起 / 承 / 转 / 合",
    "main_character": "{argument name=\"main character\" default=\"短发女孩，穿睡衣\"}"
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"日漫线稿 + 平涂淡色\"}",
    "consistency": "4 格中主角必须是同一人，画风统一",
    "color_palette": "{argument name=\"color palette\" default=\"米白 + 暖橙 + 灰\"}"
  },
  "panels": {
    "format": "2x2 grid",
    "items": [
      {
        "position": "top-left",
        "label": "起",
        "scene": "{argument name=\"panel 1\" default=\"主角站在体重秤上，皱着眉\"}",
        "dialogue": "{argument name=\"dialogue 1\" default=\"今晚开始减肥！\"}"
      },
      {
        "position": "top-right",
        "label": "承",
        "scene": "{argument name=\"panel 2\" default=\"主角坚定地喝了一杯水\"}",
        "dialogue": "{argument name=\"dialogue 2\" default=\"水也很饱嘛\"}"
      },
      {
        "position": "bottom-left",
        "label": "转",
        "scene": "{argument name=\"panel 3\" default=\"半夜里主角偷偷点开了外卖 app\"}",
        "dialogue": "{argument name=\"dialogue 3\" default=\"...就一份炸鸡\"}"
      },
      {
        "position": "bottom-right",
        "label": "合",
        "scene": "{argument name=\"panel 4\" default=\"主角抱着炸鸡桶，眼泪汪汪\"}",
        "dialogue": "{argument name=\"dialogue 4\" default=\"明天开始减\"}"
      }
    ]
  },
  "dialogue_design": {
    "balloon_style": "{argument name=\"balloon style\" default=\"白色圆角气泡，黑色描边\"}",
    "font_style": "{argument name=\"font style\" default=\"圆润手写体\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"1:1\"}",
  "constraints": {
    "must_keep": [
      "4 格主角是同一人",
      "故事节奏明显（起 / 承 / 转 / 合）",
      "对话气泡不挡脸",
      "画风统一不漂移"
    ],
    "avoid": [
      "故事走向平淡无反转",
      "对话超过 12 字",
      "分格大小不一致",
      "字体多种"
    ]
  }
}
```

### 参数策略

- 必问：主题、主角、4 格剧情
- 可默认：风格、配色、气泡样式
- 可随机：对话具体措辞

### 自动补全策略

- 用户只给主题时：自动展开起承转合 4 格剧情 + 4 句对话
- 主角默认按主题选适合的形象
- 默认 2×2

## 变体 1：讽刺产品广告 4 格

📝 提示词

```json
{
  "type": "讽刺产品广告 4 格",
  "story": {
    "theme": "{argument name=\"product satire theme\" default=\"科技公司 PPT vs 实际产品\"}"
  },
  "panels": {
    "format": "2x2 grid",
    "items": [
      {"label": "PPT 上的样子", "scene": "未来感产品 + 用户陶醉"},
      {"label": "发布会演示", "scene": "工程师手在抖"},
      {"label": "实际到货", "scene": "产品箱里只有一个充电器"},
      {"label": "客服回复", "scene": "'下个版本会有'"}
    ]
  },
  "constraints": {
    "must_feel": "讽刺 + 段子 + 一眼看懂"
  }
}
```

## 变体 2：1×4 横向 strip（适合 Twitter / X 长帖）

📝 提示词

```json
{
  "type": "1x4 横向 strip 漫画",
  "panels": {
    "format": "1x4 horizontal strip",
    "items": [
      {"label": "1", "scene": "..."},
      {"label": "2", "scene": "..."},
      {"label": "3", "scene": "..."},
      {"label": "4", "scene": "..."}
    ]
  },
  "aspect_ratio": "16:9",
  "constraints": {
    "must_feel": "横向阅读，4 格连成一段动作"
  }
}
```

## 变体 3：美食 / 心情日记 4 格

📝 提示词

```json
{
  "type": "心情 4 格日记漫画",
  "story": {
    "theme": "{argument name=\"daily theme\" default=\"周一早上的我\"}"
  },
  "style": {
    "art_style": "极简线稿 + 极少色块"
  },
  "constraints": {
    "must_feel": "亲切、生活、有共鸣"
  }
}
```

## 变体 4：自动补全模式

📝 提示词

```json
{
  "type": "4 格漫画自动补全",
  "mode": "auto-fill",
  "rule": "用户给主题，自动展开起承转合 4 格 + 主角形象 + 对话",
  "constraints": {
    "must_feel": "可直接发社媒"
  }
}
```

## 避免事项

- 不要让 4 格里没有反转 / 没有节奏
- 不要让对话超过 12 字 / 格
- 不要让画风每格漂移
- 不要让 4 格大小不等（除非刻意设计）
- 不要让气泡盖脸
