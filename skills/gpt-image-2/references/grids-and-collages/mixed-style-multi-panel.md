# 多风格混合多面板拼贴模板

本文件用于"一张图里多个 panel，每个 panel 风格不同但主题统一"：

- 5 格 / 6 格 mixed style 拼贴
- 跨风格 IP 视觉海报
- "同一主体的不同时空"拼贴
- "一句话演化史"拼贴
- 自媒体趣味海报

特征：

- 多个不同风格 panel 共存
- 每个 panel 风格完全不同（写实 + anime + 像素 + 油画）
- 主题或主体保持一致
- 视觉冲击强、有趣味
- 通常带 panel 内的小标签

## 适用范围

- 跨风格艺术拼贴
- 一个角色 / 主题的多种风格演绎
- 病毒传播海报
- IP 历史 / 时间线拼贴

## 何时使用

- 用户提到"多风格 / 跨风格 / 风格混合 / 多种画风"
- 用户希望视觉冲击 + 有趣
- 用户希望同一主题不同风格演绎

不要使用：

- 风格统一的 banner 套装（用 `banner-grid-2x2.md`）
- 风格统一的 lookbook（用 `lookbook-grid.md`）
- 风格统一的 4 格漫画（用 `storyboards-and-sequences/four-panel-comic.md`）

## 缺失信息优先提问顺序

1. 主题 / 主体（一定要明确，因为它是各风格的锚点）
2. 格子数（4 / 5 / 6）
3. 每格风格（写实 / anime / 油画 / 像素 / 3D / 蜡笔 / ...）
4. 是否带风格标签
5. 比例

## 主模板：5 格混合风格拼贴（同一主体不同风格）

📖 描述

整体一张图，5 格不同形状，每格风格完全不同，但主体一致，每格底部有小风格标签。

📝 提示词

```json
{
  "type": "5 格混合风格拼贴",
  "goal": "生成一张多风格拼贴图，主体一致，5 格分别用不同画风演绎",
  "subject": {
    "description": "{argument name=\"subject description\" default=\"一只戴墨镜的橘猫\"}",
    "consistency_rule": "5 格中是同一主体，仅画风变化"
  },
  "layout": {
    "format": "{argument name=\"layout\" default=\"中央大格 + 四角小格\"}",
    "panel_count": 5,
    "label_position": "每格底部",
    "label_design": "黑色细字 + 白底"
  },
  "panels": [
    {
      "position": "center",
      "style": "{argument name=\"panel 1 style\" default=\"高分辨率写实摄影\"}",
      "label": "{argument name=\"panel 1 label\" default=\"PHOTO\"}"
    },
    {
      "position": "top-left",
      "style": "{argument name=\"panel 2 style\" default=\"日式 anime 厚涂\"}",
      "label": "{argument name=\"panel 2 label\" default=\"ANIME\"}"
    },
    {
      "position": "top-right",
      "style": "{argument name=\"panel 3 style\" default=\"古典油画 + 金色画框感\"}",
      "label": "{argument name=\"panel 3 label\" default=\"OIL\"}"
    },
    {
      "position": "bottom-left",
      "style": "{argument name=\"panel 4 style\" default=\"16-bit 像素\"}",
      "label": "{argument name=\"panel 4 label\" default=\"PIXEL\"}"
    },
    {
      "position": "bottom-right",
      "style": "{argument name=\"panel 5 style\" default=\"Q 萌 3D Pixar 风\"}",
      "label": "{argument name=\"panel 5 label\" default=\"3D\"}"
    }
  ],
  "global_constraints": {
    "background": "{argument name=\"background\" default=\"米色纸纹\"}",
    "spacing": "12px 白色分隔"
  },
  "constraints": {
    "must_keep": [
      "5 格主体高度一致（一眼能看出是同一只 / 同一人）",
      "每格风格差异明显",
      "标签字体统一",
      "整体 layout 平衡"
    ],
    "avoid": [
      "主体在不同格里像不同物种 / 不同人",
      "标签遮挡主体",
      "背景不同导致拼贴破碎",
      "格子大小毫无规律"
    ]
  }
}
```

### 参数策略

- 必问：主体、5 个风格
- 可默认：layout、标签、背景
- 可随机：每格细节

### 自动补全策略

- 用户给主体时：自动选 5 个反差大的风格（写实 + anime + 油画 + 像素 + 3D 是经典组合）
- 默认中央大格 + 四角小格
- 默认每格底部小标签

## 变体 1：6 格"演化史"拼贴

📝 提示词

```json
{
  "type": "6 格演化史拼贴",
  "subject": {
    "description": "{argument name=\"subject\" default=\"一辆汽车\"}",
    "common_theme": "同一主题的 6 个时代演化"
  },
  "panels": [
    {"label": "1900s", "style": "复古黑白胶片"},
    {"label": "1950s", "style": "复古彩色海报"},
    {"label": "1980s", "style": "新蒸汽波"},
    {"label": "2000s", "style": "数字摄影"},
    {"label": "2020s", "style": "现代写实"},
    {"label": "2050s", "style": "赛博朋克概念图"}
  ],
  "constraints": {
    "must_feel": "时间感 + 演化感"
  }
}
```

## 变体 2：4 格"如果他生在不同国家"

📝 提示词

```json
{
  "type": "4 格异国想象拼贴",
  "subject": {
    "description": "{argument name=\"subject\" default=\"一个咖啡店老板\"}",
    "common_theme": "同一身份在不同国家文化里的视觉表达"
  },
  "panels": [
    {"label": "JAPAN", "style": "日式喫茶店 + 木质温馨"},
    {"label": "ITALY", "style": "意式街角咖啡 + 拼花地板"},
    {"label": "ETHIOPIA", "style": "传统咖啡仪式 + 红色织物"},
    {"label": "USA", "style": "工业风咖啡店 + 黑金属"}
  ],
  "constraints": {
    "must_feel": "文化感 + 同一身份"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "混合风格拼贴自动补全",
  "mode": "auto-fill",
  "rule": "用户给主体 + 拼贴主轴（风格 / 时代 / 文化），自动决定 5 个 panel",
  "constraints": {
    "must_feel": "病毒级有趣"
  }
}
```

## 避免事项

- 不要让 panel > 6（视觉破碎）
- 不要让主体在不同格里失去识别度
- 不要让风格反差不明显（看起来像同一格重复）
- 不要让背景颜色冲突（统一一个底色锚点）
- 不要塞 > 1 行标签
