# 双语 / 多语版式视觉模板

本文件用于"中英 / 中日 等双语并置的版式视觉"：

- 中英对照海报
- 中日对照科普图
- 双语展会 / 文化节物料
- 跨文化品牌主视觉
- 学术 / 文化机构出版物封面

特征：

- 两种语言并置（不是简单翻译，是设计语言）
- 通常一种语言为主、一种为辅 / 注解
- 字体严格分离（中文用中文字体 / 英文用英文字体）
- 字号层级清晰
- 重视留白与对齐

## 适用范围

- 中英 / 中日海报
- 跨文化品牌物料
- 学术 / 文化展览主视觉

## 何时使用

- 用户提到"中英 / 中日 / 双语 / bilingual"
- 用户希望文化 / 学术 / 高级感的双语视觉

不要使用：

- 单语大字海报（用 `title-safe-poster.md`）
- 纯产品海报（用 `poster-and-packaging/brand-poster.md`）
- 杂志封面（用 `poster-and-campaigns/editorial-cover.md`）

## 缺失信息优先提问顺序

1. 主语言 + 辅语言
2. 主标语 + 副标语（两种语言分别给）
3. 主题 / 行业
4. 字体风格（serif / sans / 衬线 / 圆体）
5. 主色 1-2 个
6. 比例

## 主模板：中英对照文化海报

📖 描述

整体一张图，中文为主、英文为辅，通过严格的版式系统建立层级。

📝 提示词

```json
{
  "type": "中英对照文化海报",
  "goal": "生成一张设计感强的中英双语海报，可作为文化活动 / 展览 / 品牌主视觉",
  "languages": {
    "primary": "{argument name=\"primary language\" default=\"中文\"}",
    "secondary": "{argument name=\"secondary language\" default=\"英文\"}"
  },
  "title_block": {
    "main_zh": "{argument name=\"main title zh\" default=\"东方不复\"}",
    "main_en": "{argument name=\"main title en\" default=\"THE ORIENT REIMAGINED\"}",
    "subtitle_zh": "{argument name=\"subtitle zh\" default=\"当代东方美学展\"}",
    "subtitle_en": "{argument name=\"subtitle en\" default=\"A Contemporary Eastern Aesthetic Exhibition\"}",
    "alignment": "{argument name=\"title alignment\" default=\"左上对齐\"}",
    "hierarchy_rule": "中文最大 → 英文中等 → 中文副标 → 英文副标"
  },
  "meta": {
    "date": "{argument name=\"date\" default=\"2026.5.1 - 2026.5.31\"}",
    "venue": "{argument name=\"venue\" default=\"X 美术馆 · 上海\"}",
    "presenter": "{argument name=\"presenter\" default=\"X CULTURAL FOUNDATION\"}"
  },
  "main_visual": {
    "description": "{argument name=\"main visual\" default=\"东方山水 + 现代几何切割\"}",
    "position": "{argument name=\"main visual position\" default=\"右下大区\"}"
  },
  "design": {
    "primary_color": "{argument name=\"primary color\" default=\"#A52A2A 朱砂红\"}",
    "background_color": "{argument name=\"background\" default=\"#F4EEDC 古纸米黄\"}",
    "zh_font": "{argument name=\"zh font\" default=\"宋体 / 楷体 / 现代衬线\"}",
    "en_font": "{argument name=\"en font\" default=\"现代 serif（Playfair / Cormorant）\"}",
    "grid": "{argument name=\"grid\" default=\"严格 12 栏栅格 + 细辅助线（最终输出隐藏）\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "中英文字体严格分离",
      "层级清晰：标题 > 副标 > 元信息",
      "留白充分",
      "色板 ≤ 3 色"
    ],
    "avoid": [
      "中英用同一字体（最常见错误）",
      "翻译错误（中英要等价不要错译）",
      "中英文字号差异过大或过小",
      "塞太多元素"
    ]
  }
}
```

### 参数策略

- 必问：主标语中英文、副标
- 可默认：layout、字体、配色、栅格
- 可随机：主视觉细节

### 自动补全策略

- 用户给中文主标语时：自动生成英文翻译 + 副标 + 元信息
- 字体默认中文衬线 + 英文 serif 配对
- 默认 3:4

## 变体 1：中日对照设计

📝 提示词

```json
{
  "type": "中日对照设计",
  "languages": {
    "primary": "日文",
    "secondary": "中文"
  },
  "title_block": {
    "main_zh": "{argument name=\"zh\" default=\"漫步京都\"}",
    "main_en": "{argument name=\"jp\" default=\"京を歩く\"}"
  },
  "design": {
    "zh_font": "黑体 / 思源宋体",
    "en_font": "ヒラギノ明朝 / 源ノ明朝（注：实际是日文字体）"
  },
  "constraints": {
    "must_feel": "日式杂志感"
  }
}
```

## 变体 2：科普 / 学术风双语

📝 提示词

```json
{
  "type": "科普 / 学术风双语海报",
  "title_block": {
    "main_zh": "{argument name=\"main zh\" default=\"光合作用\"}",
    "main_en": "{argument name=\"main en\" default=\"PHOTOSYNTHESIS\"}"
  },
  "main_visual": {
    "description": "示意图 + 标注线"
  },
  "design": {
    "primary_color": "学术墨绿",
    "background_color": "白色"
  },
  "constraints": {
    "must_feel": "教科书插页 + 现代设计"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "双语版式自动补全",
  "mode": "auto-fill",
  "rule": "用户给主标语（一种语言），自动生成另一种语言 + 副标 + 元信息 + 设计",
  "constraints": {
    "must_feel": "可发美术馆"
  }
}
```

## 避免事项

- 不要让中英用同一字体
- 不要让中英翻译错位 / 错译
- 不要让中英字号相同（应有主次层级）
- 不要让两种语言塞满画面（要留白）
- 不要混用 > 2 种字体家族（中文 1 + 英文 1 是上限）
- 不要让英文用宋体或日文字体（错配）
