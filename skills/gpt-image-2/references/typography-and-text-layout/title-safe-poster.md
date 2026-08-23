# 大字主张 / Title-Safe 海报模板

本文件用于"以巨大文字本身作为主视觉"的海报：

- 大字主张（Hyper-Energetic Japanese Promo）
- 字面优先海报（type-first poster）
- 标语 / 主张型 banner
- 极致排版练习
- 文字电影海报感

特征：

- 字本身就是主体（字号超大占画面 50%+）
- 通常 3-7 个字 + 1-2 行小字
- 字体设计性强（手写 / 复古印刷 / 噪点 / 涂鸦）
- 背景克制
- 强调"信息一眼能读"

## 适用范围

- 标语 / 主张海报
- 活动 / 大促主视觉
- 字面优先 banner

## 何时使用

- 用户提到"大字 / 主张 / hero text / type-first / 文字海报"
- 用户希望"一句话就是主图"
- 用户希望日式 / 极致排版风

不要使用：

- 带产品的海报（用 `poster-and-campaigns/brand-poster.md`）
- editorial 杂志封面（用 `poster-and-campaigns/editorial-cover.md`）
- 复杂叙事（用 `scenes-and-illustrations/concept-scene.md`）

## 缺失信息优先提问顺序

1. 主标语（3-7 个字）
2. 副标 / tagline
3. 风格定位（日式昭和 / 现代极简 / 复古印刷 / 涂鸦 / 噪点）
4. 主色 1-2 个
5. 是否含小字标注 / logo
6. 比例

## 主模板：日式高能量大字海报

📖 描述

整体一张图，主体为大号标语字本身 + 副标 + 小字 + 极少的图形辅助。

📝 提示词

```json
{
  "type": "日式高能量大字海报",
  "goal": "生成一张以巨大文字本身为主视觉的高能量海报",
  "headline": {
    "text": "{argument name=\"headline\" default=\"全力疾走\"}",
    "language": "{argument name=\"language\" default=\"中文 / 日文混合\"}",
    "size": "占画面 60% 以上",
    "alignment": "{argument name=\"alignment\" default=\"居中\"}",
    "treatment": "{argument name=\"treatment\" default=\"叠加噪点 + 半色调网点 + 错位描边\"}"
  },
  "subheadline": {
    "text": "{argument name=\"subheadline\" default=\"GO ALL OUT 2026\"}",
    "size": "headline 1/4",
    "position": "{argument name=\"sub position\" default=\"headline 下方居中\"}"
  },
  "small_text": {
    "items": [
      "{argument name=\"small text 1\" default=\"4.24-5.24 SPECIAL CAMPAIGN\"}",
      "{argument name=\"small text 2\" default=\"X COLLECTIVE\"}"
    ],
    "position": "底部边角"
  },
  "design": {
    "primary_color": "{argument name=\"primary color\" default=\"#FF2C2C 朱红\"}",
    "background_color": "{argument name=\"background\" default=\"#F4EEDC 米黄\"}",
    "decoration": "{argument name=\"decoration\" default=\"4-5 个简单几何图形（圆 / 三角 / 短粗箭头），刻意留白\"}",
    "typography_family": "{argument name=\"font family\" default=\"现代日式 sans + 一个手写 accent\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "标语字必须能一眼读出",
      "字面占画面绝对主体",
      "颜色 ≤ 3",
      "字体 ≤ 2 家族"
    ],
    "avoid": [
      "标语字过小被装饰淹没",
      "装饰图形 > 6 个",
      "字体超过 3 种",
      "出现错别字"
    ]
  }
}
```

### 参数策略

- 必问：标语、副标、风格、主色
- 可默认：layout、装饰、字体
- 可随机：装饰具体形状

### 自动补全策略

- 用户给标语 + 风格关键词时：自动决定字处理 + 配色 + 装饰
- 默认日式高能量 = 噪点 + 半色调 + 错位
- 默认 3:4

## 变体 1：极简瑞士排版大字海报

📝 提示词

```json
{
  "type": "极简瑞士排版大字海报",
  "headline": {
    "treatment": "无装饰 + 无衬线 + 严格栅格"
  },
  "design": {
    "primary_color": "纯黑",
    "background_color": "纯白",
    "decoration": "无 / 仅一条细横线"
  },
  "constraints": {
    "must_feel": "瑞士平面 / Minimal"
  }
}
```

## 变体 2：复古印刷大字海报

📝 提示词

```json
{
  "type": "复古印刷大字海报",
  "headline": {
    "treatment": "套印偏移 + 油墨晕染 + 微微脏感"
  },
  "design": {
    "primary_color": "复古红",
    "background_color": "做旧米纸",
    "decoration": "复古印刷符号"
  },
  "constraints": {
    "must_feel": "1960s letterpress"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "大字海报自动补全",
  "mode": "auto-fill",
  "rule": "用户给一句标语，自动决定风格 + 配色 + 字处理 + 装饰",
  "constraints": {
    "must_feel": "可印刷 + 一眼能读"
  }
}
```

## 避免事项

- 不要让标语字小于画面 40%
- 不要让装饰多到喧宾夺主
- 不要让标语出现错别字（最严重）
- 不要让字体 > 2 家族
- 不要让背景饱和度 > 主标语
- 不要让小字塞超过 3 行
