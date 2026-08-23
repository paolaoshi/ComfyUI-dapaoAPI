# 高密度讲解型 Slides 模板

本文件用于生成“一页能讲清楚一个主题”的高密度 Slides 视觉，灵感来源于：

- 日本霞关风格政府 Slides
- Irasutoya 简约温馨插画
- 商业咨询公司一页纸总结
- 学术海报一页式排版

特征：

- 信息密度极高
- 有标题区 + 多个段落 + 多块图示
- 色板克制（≤ 3 色）
- 文字 + 图标 + 小插画混合

## 适用范围

- 单页讲解 Slides
- 公开课 / 培训 / 演讲单页讲义
- 自媒体长图首页
- 公司一页纸方案概述

## 何时使用

- 用户提到“讲解 Slides / 高密度页 / 一页讲清楚 / 政策风 / Irasutoya 风”
- 用户希望大量文字与插画共存
- 用户希望一张图就能传播信息

不要使用：

- 用户要的是政策公告风（用 `policy-style-slide.md`）
- 用户要的是商业报告（用 `visual-report-page.md`）
- 用户要的是教学示意图（用 `educational-diagram-slide.md`）

## 缺失信息优先提问顺序

1. 主题
2. 风格倾向：温馨插画风 / 政府严谨风 / 学术风 / 咨询风
3. 信息密度（中等 / 高 / 极高）
4. 章节数（3-6 段）
5. 是否需要英文 / 日文 / 双语
6. 是否需要中央主图

## 主模板：Irasutoya × 霞关风混合 Slides

📖 描述

整体一页 Slide，包含主标题 + 副标题 + 多个段落 + 简洁插画 + 必要图示。

📝 提示词

```json
{
  "type": "高密度讲解型 Slide",
  "goal": "生成一张可作为讲解课件 / 公众号长图首页 / 培训单页的高密度 Slide",
  "style": {
    "format": "{argument name=\"format\" default=\"ponchi-e diagram\"}",
    "blend": "Irasutoya 柔和温馨插画 + 霞关风格 Slides 高信息密度",
    "color_palette": "{argument name=\"color palette\" default=\"米白底 + 朱红 + 深灰\"}"
  },
  "title_section": {
    "main_title": "{argument name=\"main title\" default=\"桃太郎物语全图解\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"用一张图理解这个故事\"}",
    "language": "{argument name=\"language\" default=\"日文\"}"
  },
  "centerpiece": {
    "enabled": "{argument name=\"centerpiece enabled\" default=\"true\"}",
    "description": "{argument name=\"centerpiece description\" default=\"画面中央偏上，桃太郎站在桃子上，狗、猴、雉鸡围绕\"}"
  },
  "sections": {
    "count": "{argument name=\"section count\" default=\"5\"}",
    "items": [
      "{argument name=\"section 1\" default=\"出生：从桃子里诞生\"}",
      "{argument name=\"section 2\" default=\"成长：勇敢善良的少年\"}",
      "{argument name=\"section 3\" default=\"出发：前往鬼之岛\"}",
      "{argument name=\"section 4\" default=\"伙伴：狗 / 猴 / 雉鸡\"}",
      "{argument name=\"section 5\" default=\"胜利：击败鬼并归乡\"}"
    ],
    "section_block_style": "每节由小插画 + 标题 + 2-3 句解释构成"
  },
  "annotations": {
    "style": "细线引线 + 小标签",
    "rule": "标注线不能与中央主体交叉"
  },
  "footer": {
    "summary": "{argument name=\"summary\" default=\"善良 + 勇气 + 伙伴，是这个故事的内核\"}"
  },
  "constraints": {
    "must_keep": [
      "信息密度高，但有清晰阅读顺序",
      "中央主体作为视觉锚点",
      "插画风与文字风一致",
      "色板严格 ≤ 3 色"
    ],
    "avoid": [
      "段落字号大小不一",
      "插画过度精致破坏统一感",
      "文字铺满到边缘没有留白",
      "出现奇怪的英文混排"
    ]
  }
}
```

### 参数策略

- 必问：主题、章节数
- 可默认：色板、副标题、底部总结句
- 可随机：每节插画的具体造型

### 自动补全策略

- 用户给主题时：自动决定章节切分（建议 4-6 节）
- 风格默认 Irasutoya × 霞关混合
- 中央主体根据主题自动选

## 变体 1：商业咨询公司一页纸

📝 提示词

```json
{
  "type": "商业咨询一页纸 Slide",
  "style": {
    "color_palette": "深蓝 + 灰 + 白",
    "blend": "现代咨询公司风格 + 极简图标"
  },
  "title_section": {
    "main_title": "{argument name=\"main title\" default=\"AI 时代的产品策略\"}",
    "subtitle": "一页讲清楚战略思考"
  },
  "sections": {
    "count": 4,
    "items": [
      "现状诊断",
      "核心机会",
      "策略路径",
      "关键里程碑"
    ]
  },
  "constraints": {
    "must_feel": "理性、克制、可信赖"
  }
}
```

## 变体 2：学术海报一页式

📝 提示词

```json
{
  "type": "学术海报一页式 Slide",
  "style": {
    "color_palette": "学术蓝 + 米色 + 黑",
    "blend": "学术海报 + 论文式排版"
  },
  "title_section": {
    "main_title": "{argument name=\"paper title\" default=\"基于多模态信号的图像质量评估方法\"}",
    "subtitle": "一页摘要图"
  },
  "sections": {
    "items": ["研究问题", "方法概述", "实验结果", "结论与未来工作"]
  },
  "constraints": {
    "must_feel": "学术、严谨、可投稿级"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "高密度讲解 Slide 自动补全模板",
  "mode": "auto-fill",
  "rule": "用户只给主题，自动选风格、章节、色板、中央主体",
  "constraints": {
    "must_feel": "出版物级"
  }
}
```

## 避免事项

- 不要让正文字号 > 标题
- 不要让单页章节超过 6 个
- 不要把中央主体放得太大盖过其他段落
- 不要混入与主风格不同的插画来源
- 不要在一页里中文 + 英文 + 日文都出现
