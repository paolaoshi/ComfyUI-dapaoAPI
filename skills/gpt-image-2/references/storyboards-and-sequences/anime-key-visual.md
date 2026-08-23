# 动漫 Key Visual 单图模板

本文件用于"一张图代表整部作品"的动漫主视觉：

- 动漫 KV / 主视觉
- 轻小说封面
- 同人志封面
- 动漫海报
- 游戏卡牌主图（不含 UI）

特征：

- 一张图聚集多个角色或一个角色 + 强氛围
- 戏剧性构图与灯光
- anime / 半写实风格
- 通常竖版 3:4 / 4:5
- 留 title 位

## 适用范围

- 动漫主视觉
- 轻小说 / 同人志封面
- IP 海报
- 游戏卡面

## 何时使用

- 用户提到"动漫 KV / anime 主视觉 / 轻小说封面 / IP 海报"
- 用户希望一张图就能讲完世界观
- 用户希望 anime 风格的高完成度大图

不要使用：

- 多分镜叙事（用 `manga-spread-page.md`）
- 4 格段子（用 `four-panel-comic.md`）
- 真实人物大片（用 `portraits-and-characters/founder-portrait.md`）
- 电影级概念大场景（用 `scenes-and-illustrations/concept-scene.md`）

## 缺失信息优先提问顺序

1. 作品 / 主题
2. 主角形象（数量 + 关系）
3. 世界观 / 时代 / 氛围
4. 风格：现代 anime / 90s anime / 半写实
5. 是否需要 title 位
6. 比例

## 主模板：动漫 Key Visual 单图

📖 描述

整体一张大图，包含主角 + 场景氛围 + 标题位，强叙事感。

📝 提示词

```json
{
  "type": "动漫 Key Visual",
  "goal": "生成一张可作为动漫 / 轻小说 / IP 主视觉的单图",
  "ip": {
    "title": "{argument name=\"ip title\" default=\"霜白幻想曲\"}",
    "tagline": "{argument name=\"tagline\" default=\"这场雪，下了一千年\"}"
  },
  "characters": {
    "count": "{argument name=\"character count\" default=\"3\"}",
    "items": [
      "{argument name=\"character 1\" default=\"少女主角，银白长发，蓝瞳，雪白连衣裙\"}",
      "{argument name=\"character 2\" default=\"剑士同伴，黑发，战甲\"}",
      "{argument name=\"character 3\" default=\"小动物伙伴，雪白狐狸\"}"
    ],
    "composition_relationship": "{argument name=\"composition\" default=\"主角居中，同伴左右护卫，动物在脚边\"}"
  },
  "world": {
    "scene": "{argument name=\"scene\" default=\"冰封城市，远景城堡，飘落雪花\"}",
    "lighting": "{argument name=\"lighting\" default=\"冷蓝主光 + 暖金边缘光\"}",
    "atmosphere": "{argument name=\"atmosphere\" default=\"史诗、孤独、坚定\"}"
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"现代 anime + 半写实 + 厚涂背景\"}",
    "color_palette": "{argument name=\"color palette\" default=\"冰蓝 + 月白 + 暖金\"}"
  },
  "title_block": {
    "enabled": "{argument name=\"title block enabled\" default=\"true\"}",
    "main_title": "{argument name=\"main title\" default=\"霜白幻想曲\"}",
    "sub_title": "{argument name=\"sub title\" default=\"FROZEN FANTASIA\"}",
    "position": "{argument name=\"title position\" default=\"画面顶部居中\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "主角作为绝对视觉中心",
      "灯光方向统一",
      "色板严格统一",
      "标题与主角不重叠"
    ],
    "avoid": [
      "角色塞太多导致脸部小到不可识别",
      "背景过亮淹没角色",
      "色板出现额外鲜艳色",
      "标题字体过多种类"
    ]
  }
}
```

### 参数策略

- 必问：作品名、主角、世界观
- 可默认：风格、配色、标题位
- 可随机：背景细节

### 自动补全策略

- 主角数默认 1-3
- 世界观 → 自动决定配色（冷世界 = 蓝白 / 末世 = 焦土棕 / 校园 = 暖橙）
- 默认竖版 3:4

## 变体 1：单角色 + 极强氛围 KV

📝 提示词

```json
{
  "type": "单角色 + 强氛围 KV",
  "characters": {
    "count": 1,
    "items": ["{argument name=\"character\" default=\"长发少女，逆光\"}"]
  },
  "world": {
    "atmosphere": "孤独 + 神秘"
  },
  "constraints": {
    "must_feel": "电影海报感"
  }
}
```

## 变体 2：群像 KV（5+ 角色）

📝 提示词

```json
{
  "type": "群像 KV",
  "characters": {
    "count": 6,
    "composition_relationship": "金字塔构图：主角顶 + 配角围绕"
  },
  "constraints": {
    "must_feel": "团队感、史诗、可作为动画首播主图"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "动漫 KV 自动补全",
  "mode": "auto-fill",
  "rule": "用户给一句作品概念，自动决定主角、构图、世界观、标题",
  "constraints": {
    "must_feel": "可直接首发"
  }
}
```

## 避免事项

- 不要让角色数量超过 7（脸部识别会崩）
- 不要让灯光方向不统一
- 不要让标题盖在主角脸上
- 不要使用 > 4 种主色
- 不要让背景细节超过角色细节量
