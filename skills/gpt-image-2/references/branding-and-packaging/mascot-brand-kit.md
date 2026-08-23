# 吉祥物品牌套装模板

本文件用于"以吉祥物为核心的多面板品牌识别 / 周边视觉文档"：

- 吉祥物多角度 + 表情 + 应用场景
- 吉祥物周边商品 catalog
- 品牌 IP 完整介绍页
- 卡通人设品牌识别文档

特征：

- 一张大图，多区块
- 主区：吉祥物三视图 + 主形象
- 次区：表情 + 配色 + 周边
- 风格强调"亲切 + 可爱 + 一致"
- 通常含 IP 名 + 性格描述

## 适用范围

- 吉祥物品牌识别套装
- IP 周边商品 catalog
- 卡通人设介绍页
- 营销活动 IP 包

## 何时使用

- 用户提到"吉祥物 / mascot / IP 形象 / 卡通代言"
- 用户希望出"完整 IP 套装"而不是单图

不要使用：

- 单个角色设定稿（用 `portraits-and-characters/character-sheet.md`）
- 通用品牌识别（用 `brand-identity-board.md`）
- 单个动漫 KV（用 `storyboards-and-sequences/anime-key-visual.md`）

## 缺失信息优先提问顺序

1. 品牌 / IP 名 + 一句性格描述
2. 吉祥物主形态（动物 / 人 / 拟物 / 食物）
3. 配色 1-2 个
4. 是否需要表情包 / 周边 / 服装
5. 渲染风格（2D 卡通 / 3D Q 萌 / Pixar 写实卡通）
6. 比例

## 主模板：吉祥物品牌识别套装

📖 描述

整体一张大图，分主形象区 + 三视图区 + 表情区 + 应用区。

📝 提示词

```json
{
  "type": "吉祥物品牌识别套装",
  "goal": "生成一张可作为吉祥物 brand kit / 周边介绍页的多面板视觉文档",
  "ip": {
    "name": "{argument name=\"ip name\" default=\"AURORA 小光\"}",
    "tagline": "{argument name=\"tagline\" default=\"陪你度过每个夜晚\"}",
    "personality": "{argument name=\"personality\" default=\"温柔、好奇、爱发光\"}",
    "brand_owner": "{argument name=\"brand owner\" default=\"AURORA 家居灯光\"}"
  },
  "mascot": {
    "form": "{argument name=\"mascot form\" default=\"小型半透明灯泡精灵，圆乎乎，有发光的尾巴\"}",
    "color_palette": "{argument name=\"color palette\" default=\"暖金 + 米白 + 浅蓝\"}",
    "rendering": "{argument name=\"rendering\" default=\"3D Pixar 风 + Q 萌\"}"
  },
  "regions": {
    "hero": {
      "position": "{argument name=\"hero position\" default=\"左上大区\"}",
      "content": "吉祥物主形象 + 名字 + 一句性格描述",
      "background": "纯色 + 微光晕"
    },
    "three_view": {
      "position": "{argument name=\"three view position\" default=\"右上\"}",
      "content": "正面 / 侧面 / 背面三视图",
      "label": "FRONT / SIDE / BACK"
    },
    "expressions": {
      "position": "{argument name=\"expression position\" default=\"左下\"}",
      "count": "{argument name=\"expression count\" default=\"6\"}",
      "items": ["开心", "好奇", "困了", "惊讶", "害羞", "小生气"]
    },
    "applications": {
      "position": "{argument name=\"app position\" default=\"右下\"}",
      "items": [
        "{argument name=\"app 1\" default=\"产品包装盒角落\"}",
        "{argument name=\"app 2\" default=\"app 启动页\"}",
        "{argument name=\"app 3\" default=\"周边贴纸\"}",
        "{argument name=\"app 4\" default=\"短视频片头吉祥物动画静帧\"}"
      ]
    }
  },
  "style": {
    "background": "{argument name=\"background\" default=\"米色纸纹 + 细灰辅助线\"}",
    "typography": "圆润 sans + 一行手写体强调"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "吉祥物在所有区块外观一致",
      "三视图比例严格统一",
      "表情清晰可识别",
      "应用场景符合品牌"
    ],
    "avoid": [
      "吉祥物在不同区块画风漂移",
      "表情夸张到失真",
      "配色出现强烈对比破坏 IP 调性",
      "应用 mockup 风格冲突"
    ]
  }
}
```

### 参数策略

- 必问：IP 名、形态、性格、主色
- 可默认：layout、表情、应用场景
- 可随机：周边细节

### 自动补全策略

- 用户给一句"我想要一个 X 行业的可爱代言"时：自动决定形态 + 性格 + 配色 + 6 表情 + 4 应用
- 默认 3D Q 萌渲染
- 默认 4 区块布局

## 变体 1：吉祥物周边 catalog（重点是商品）

📝 提示词

```json
{
  "type": "吉祥物周边 catalog",
  "regions": {
    "hero": {"content": "吉祥物 + IP 名"},
    "three_view": null,
    "expressions": null,
    "applications": {
      "items": [
        "T 恤", "马克杯", "手机壳", "贴纸包", "钥匙扣", "毛绒玩偶", "帆布包", "手机支架"
      ]
    }
  },
  "constraints": {
    "must_feel": "电商商品 catalog 感"
  }
}
```

## 变体 2：极简吉祥物介绍页（仅主形象 + 性格）

📝 提示词

```json
{
  "type": "极简吉祥物介绍页",
  "regions": {
    "hero": {"content": "吉祥物 + 名 + 性格"},
    "three_view": null,
    "expressions": {"count": 4},
    "applications": null
  },
  "constraints": {
    "must_feel": "干净、易读"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "Mascot brand kit 自动补全",
  "mode": "auto-fill",
  "rule": "用户给品牌 + 行业 + 性格关键词，自动决定吉祥物形态 + 表情 + 应用",
  "constraints": {
    "must_feel": "可发布周边 / 公关图"
  }
}
```

## 避免事项

- 不要让吉祥物在不同区块比例不一致
- 不要让表情夸张到看起来另一个角色
- 不要在应用 mockup 上加太多其他设计元素
- 不要让配色超过 4 种主色
- 不要漏掉 IP 名 + 性格描述
