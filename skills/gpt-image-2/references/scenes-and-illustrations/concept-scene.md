# 概念 / 大场景插画模板

本文件用于生成“电影感大场景 / 概念美术 / 史诗插画”：

- 游戏概念图
- 电影 key art
- 小说 / IP 主视觉
- 预告海报场景
- 世界观介绍场景

特征：

- 大场景 / 大透视
- 强烈氛围
- 视觉信息量大
- 戏剧性灯光
- 适合作为大画幅展示

## 适用范围

- 游戏 / 动画 / 电影概念图
- 小说 / IP 主视觉
- 预告海报
- 世界观主图

## 何时使用

- 用户提到“概念图 / key art / 大场景 / 电影感 / 史诗”
- 用户希望一张图就能讲清楚一个世界

不要使用：

- 治愈日常（用 `healing-scene.md`）
- 童书风（用 `picture-book-scene.md`）
- 极简氛围（用 `minimalist-mood-scene.md`）

## 缺失信息优先提问顺序

1. 世界观主题（赛博朋克 / 东方奇幻 / 末世 / 太空 / 武侠）
2. 主体（人物 + 远景 / 巨型生物 / 城市）
3. 时间 / 天气 / 氛围
4. 配色 + 灯光基调
5. 比例（横版 21:9 / 16:9 / 竖版 9:16）
6. 是否有 title text 区

## 主模板：电影感概念大场景

📖 描述

整体宽幅画面，前景人物 + 中景叙事 + 远景大透视，戏剧性灯光，预留 title 区。

📝 提示词

```json
{
  "type": "电影感概念大场景",
  "goal": "生成一张可作为游戏 key art / 电影 key art / IP 世界观主视觉的概念大场景",
  "world": {
    "theme": "{argument name=\"world theme\" default=\"赛博朋克东方都市\"}",
    "tone": "{argument name=\"world tone\" default=\"霓虹 + 雨夜 + 高密度建筑\"}"
  },
  "composition": {
    "foreground": "{argument name=\"foreground\" default=\"撑伞的女主角背影\"}",
    "midground": "{argument name=\"midground\" default=\"湿漉漉的街道 + 霓虹招牌 + 反光\"}",
    "background": "{argument name=\"background\" default=\"高耸摩天楼 + 全息广告\"}",
    "perspective": "{argument name=\"perspective\" default=\"低机位仰视\"}"
  },
  "lighting": {
    "key_light": "{argument name=\"key light\" default=\"霓虹粉 + 霓虹蓝交错\"}",
    "fill_light": "{argument name=\"fill light\" default=\"湿地反光\"}",
    "atmosphere": "{argument name=\"atmosphere\" default=\"湿润空气 + 烟雨 + 微光颗粒\"}"
  },
  "color_palette": "{argument name=\"color palette\" default=\"霓虹粉 + 电光蓝 + 深黑\"}",
  "title_safe_area": "{argument name=\"title area\" default=\"画面顶部 1/4 留出 title 位\"}",
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"21:9\"}",
  "style": {
    "rendering": "电影级 concept art + 数字绘画 + 高细节"
  },
  "constraints": {
    "must_keep": [
      "前中后景层次清晰",
      "灯光方向统一",
      "色板严格统一",
      "前景人物剪影清晰"
    ],
    "avoid": [
      "前景与背景混在一起",
      "过度细节让画面塞满",
      "出现真实品牌 logo 招牌",
      "色调突然变化"
    ]
  }
}
```

### 参数策略

- 必问：世界观、构图层次、比例
- 可默认：灯光、配色、风格
- 可随机：远景细节

### 自动补全策略

- 主题自动选配色（赛博 = 霓虹 / 武侠 = 水墨 / 末世 = 焦土棕 / 太空 = 深紫）
- 默认 21:9 横屏
- 自动留 title 区

## 变体 1：竖版 IP 主视觉

📝 提示词

```json
{
  "type": "竖版 IP 主视觉",
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"9:16\"}",
  "composition": {
    "foreground": "主角全身居中",
    "midground": "光晕 + 队友剪影",
    "background": "代表世界观的核心建筑"
  },
  "constraints": {
    "must_feel": "海报感、英雄感、首发主图"
  }
}
```

## 变体 2：自然奇观大场景

📝 提示词

```json
{
  "type": "自然奇观大场景",
  "world": {
    "theme": "{argument name=\"natural theme\" default=\"极地浮冰 + 巨鲸\"}",
    "tone": "孤独、宏大、肃穆"
  },
  "composition": {
    "foreground": "渺小人影",
    "background": "巨型自然主体"
  },
  "constraints": {
    "must_feel": "渺小 vs 宏大"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "概念大场景自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给世界观一句话，自动决定构图、灯光、配色、比例",
  "constraints": {
    "must_feel": "可作为大屏 / 首发 KV"
  }
}
```

## 避免事项

- 不要让前景与背景同色融合
- 不要让灯光来源不统一
- 不要塞太多次要细节
- 不要让人物比建筑还大（破坏世界观尺度）
- 不要使用 > 4 种主色
