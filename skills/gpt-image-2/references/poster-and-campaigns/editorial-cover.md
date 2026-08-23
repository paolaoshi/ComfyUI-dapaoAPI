# 杂志 / 编辑封面模板

本文件用于生成“杂志封面 / 编辑式视觉 / 出版物封面”：

- 时尚杂志封面
- 行业刊物封面
- 内部刊物 / 报告封面
- 自媒体特刊封面
- 编辑式专题主图

特征：

- 强烈的“出版物气质”
- 主视觉肖像 / 单一物品占主导
- 大字标题 + 小字栏目导引
- 比例多为竖版 3:4 / 4:5
- 留刊名 + 期号位置

## 适用范围

- 杂志 / 期刊封面
- 行业报告封面
- 自媒体特刊封面
- 出版物风视觉海报

## 何时使用

- 用户提到“杂志 / 封面 / 期刊 / cover / 出版风”
- 用户希望视觉极具“编辑感”，而不是广告海报感

不要使用：

- 通用品牌海报（用 `brand-poster.md`）
- Banner（用 `banner-hero.md`）
- Campaign KV（用 `campaign-kv.md`）

## 缺失信息优先提问顺序

1. 刊名 / 期号 / 出版方
2. 主标题（封面大字）
3. 主视觉（人 / 物 / 概念）
4. 子栏目 / 内页导引短句（3-5 条）
5. 风格：高级时装 / 文化 / 财经 / 科技 / 复古
6. 比例

## 主模板：杂志封面（人物肖像）

📖 描述

竖版封面，主视觉为人物肖像或单物，左上角刊名 + 期号，主标题大字横排或竖排，左右栏目导引小字。

📝 提示词

```json
{
  "type": "杂志封面",
  "goal": "生成一张可作为时尚 / 文化 / 行业杂志封面的视觉，编辑感强烈",
  "publication": {
    "name": "{argument name=\"publication name\" default=\"NEUE\"}",
    "tagline": "{argument name=\"tagline\" default=\"Culture · Design · Future\"}",
    "issue": "{argument name=\"issue\" default=\"Issue 042 / 2026 April\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "main_visual": {
    "type": "{argument name=\"main visual type\" default=\"人物肖像\"}",
    "description": "{argument name=\"main visual\" default=\"东亚年轻女性正面肖像，眼神平静，自然光\"}",
    "composition": "{argument name=\"composition\" default=\"占满画面，头部居中略偏右\"}"
  },
  "title_block": {
    "main_title": "{argument name=\"main title\" default=\"重启与重启之间\"}",
    "main_title_style": "{argument name=\"title style\" default=\"超大粗衬线，叠加在主视觉上\"}",
    "kicker": "{argument name=\"kicker\" default=\"专访\"}"
  },
  "side_teasers": {
    "count": "{argument name=\"teaser count\" default=\"4\"}",
    "items": [
      "{argument name=\"teaser 1\" default=\"AI 时代的写作 · 韩松落 vs ChatGPT\"}",
      "{argument name=\"teaser 2\" default=\"建筑师手记 · 在杭州慢慢盖一座房子\"}",
      "{argument name=\"teaser 3\" default=\"特别企划 · 30 位 30 岁\"}",
      "{argument name=\"teaser 4\" default=\"长读 · 一个失败的创业\"}"
    ],
    "position": "{argument name=\"teaser position\" default=\"画面下方 + 左侧 vertical\"}"
  },
  "color_palette": "{argument name=\"color palette\" default=\"米白 + 墨黑 + 一抹品牌橙\"}",
  "barcode": {
    "enabled": "{argument name=\"barcode enabled\" default=\"true\"}",
    "position": "右下角"
  },
  "constraints": {
    "must_keep": [
      "主视觉作为绝对锚点",
      "刊名清晰可读且不被遮挡",
      "主标题字号最大",
      "栏目导引不抢戏"
    ],
    "avoid": [
      "主视觉与文字争抢同一区域",
      "字体多于 3 种",
      "色板出现额外色",
      "出现广告 logo"
    ]
  }
}
```

### 参数策略

- 必问：刊名、期号、主标题、主视觉
- 可默认：色板、栏目导引、条码
- 可随机：装饰小元素

### 自动补全策略

- 风格根据刊型自动选（时尚 = 高对比 + 极简，财经 = 蓝灰 + 衬线，文化 = 暖米 + 衬线）
- 主标题默认 6-12 字
- 栏目默认 3-4 条

## 变体 1：单物封面（产品 / 物品）

📝 提示词

```json
{
  "type": "单物杂志封面",
  "main_visual": {
    "type": "object",
    "description": "{argument name=\"object\" default=\"一把保养良好的复古打字机\"}"
  },
  "title_block": {
    "main_title": "{argument name=\"title\" default=\"工具的灵魂\"}"
  },
  "constraints": {
    "must_feel": "静物、克制、文学感"
  }
}
```

## 变体 2：财经 / 科技刊封面

📝 提示词

```json
{
  "type": "财经科技刊封面",
  "main_visual": {
    "type": "concept",
    "description": "{argument name=\"concept\" default=\"信息流抽象图形 + 主体人物剪影\"}"
  },
  "color_palette": "深蓝 + 银 + 一抹荧光",
  "title_block": {
    "main_title": "{argument name=\"title\" default=\"AI 重写商业\"}"
  },
  "constraints": {
    "must_feel": "前沿、可信、行业旗舰"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "杂志封面自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给刊型 + 主题，自动生成刊名、期号、主标题、栏目导引、风格",
  "constraints": {
    "must_feel": "可放上书报亭"
  }
}
```

## 避免事项

- 不要让刊名被主视觉遮住
- 不要让主标题与主视觉色彩对比过低
- 不要让栏目导引超过 5 条
- 不要使用 > 3 种字体
- 不要让条码出现在主视觉中心
