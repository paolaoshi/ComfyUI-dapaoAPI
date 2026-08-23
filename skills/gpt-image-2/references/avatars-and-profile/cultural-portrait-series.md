# 文化 / 历史人物系列肖像模板

本文件用于"基于文化 / 历史 / 神话主题，批量生成系列肖像"：

- 朝代皇帝系列（明朝皇帝集 / 清朝皇帝集）
- 神话角色系列（希腊神话 / 北欧神话）
- 历史名人系列
- 经典文学角色系列
- 民族服饰系列

特征：

- 多个角色，每个角色一格
- 每格有名字 / 称号标签
- 风格统一（同一画师 / 同一时代风）
- 适合教育 / 文创 / 主题营销

## 适用范围

- 朝代皇帝 / 名人系列
- 神话 / 文学角色系列
- 民族 / 文化主题系列

## 何时使用

- 用户提到"系列 / 集合 / 朝代 / 神话 / 历史人物"
- 用户希望多个角色 + 标签

不要使用：

- 同一人多版本（用 `character-grid-portrait.md`）
- 单张人物风格转换（用 `style-transfer-selfie.md`）
- 角色 IP 设定稿（用 `portraits-and-characters/character-sheet.md`）

## 缺失信息优先提问顺序

1. 主题（朝代 / 神话 / 文学 / 文化）
2. 角色数量（建议 6-12）
3. 是否需要列名 / 称号 / 简短说明
4. 风格：水墨写实 / 油画 / 卡通 / 半写实
5. 是否参考某种风格（用户提供参考图 / 经典画师风）
6. 比例

## 主模板：朝代皇帝系列肖像

📖 描述

整体一张大图，包含若干个皇帝肖像，每个肖像下方有谥号 + 名讳。

📝 提示词

```json
{
  "type": "朝代皇帝系列肖像",
  "goal": "生成一张包含某朝代多位皇帝的系列肖像图，可作为教育 / 文创 / 自媒体科普图",
  "theme": {
    "dynasty": "{argument name=\"dynasty\" default=\"明朝\"}",
    "subject_count": "{argument name=\"subject count\" default=\"9\"}"
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"中式工笔写实人像 + 略带水墨感\"}",
    "consistency": "所有肖像必须由同一画师风格绘制",
    "color_palette": "{argument name=\"color palette\" default=\"低饱和金 + 朱红 + 黑\"}"
  },
  "layout": {
    "format": "{argument name=\"format\" default=\"3x3 grid\"}",
    "background": "{argument name=\"background\" default=\"米色绢布纹理\"}",
    "panel_design": {
      "portrait_shape": "圆角方形 / 椭圆",
      "label_position": "肖像下方居中",
      "label_content": "谥号 + 名讳，如 '太祖 朱元璋'"
    }
  },
  "subjects": {
    "auto_select": "{argument name=\"auto select\" default=\"true\"}",
    "rule": "若 auto_select 为 true，则按朝代顺序选取代表性皇帝；若用户指定列表，则按用户列表",
    "user_list": "{argument name=\"user list\" default=\"\"}"
  },
  "constraints": {
    "must_keep": [
      "所有肖像同一画师风格",
      "服饰、配饰严格符合所属朝代",
      "标签清晰可读且历史准确",
      "肖像之间均匀分布"
    ],
    "avoid": [
      "出现错朝代服饰",
      "肖像风格漂移（每个像不同画师）",
      "标签错字 / 错位",
      "背景过度装饰"
    ]
  }
}
```

### 参数策略

- 必问：主题、数量
- 可默认：风格、layout、配色、标签
- 可随机：背景纹理细节

### 自动补全策略

- 用户给朝代时：自动选代表性 9 位皇帝
- 风格默认中式工笔
- 标签默认"谥号 + 名讳"

## 变体 1：神话角色系列

📝 提示词

```json
{
  "type": "神话角色系列肖像",
  "theme": {
    "mythology": "{argument name=\"mythology\" default=\"希腊神话\"}",
    "subject_count": 12
  },
  "style": {
    "art_style": "古典油画 + 厚涂",
    "color_palette": "深蓝 + 金 + 暖棕"
  },
  "layout": {
    "format": "4x3 grid",
    "panel_design": {
      "label_content": "神祇名 + 司掌领域"
    }
  },
  "subjects": {
    "user_list": "宙斯 / 赫拉 / 波塞冬 / 哈迪斯 / 雅典娜 / 阿波罗 / 阿尔忒弥斯 / 阿瑞斯 / 阿芙洛狄忒 / 赫尔墨斯 / 赫菲斯托斯 / 狄俄尼索斯"
  },
  "constraints": {
    "must_feel": "古典油画馆藏感"
  }
}
```

## 变体 2：经典文学角色系列

📝 提示词

```json
{
  "type": "经典文学角色系列",
  "theme": {
    "literature": "{argument name=\"literature\" default=\"红楼梦十二金钗\"}",
    "subject_count": 12
  },
  "style": {
    "art_style": "工笔重彩 + 古风插画",
    "color_palette": "胭脂红 + 月白 + 翠绿"
  },
  "constraints": {
    "must_feel": "古典文学画册级"
  }
}
```

## 变体 3：民族服饰系列

📝 提示词

```json
{
  "type": "民族服饰系列肖像",
  "theme": {
    "subject_count": 9,
    "category": "{argument name=\"category\" default=\"中国 56 民族代表 9 选\"}"
  },
  "style": {
    "art_style": "高分辨率写实人像 + 棚拍",
    "color_palette": "保留各民族服饰原色"
  },
  "constraints": {
    "must_feel": "尊重文化、服饰准确"
  }
}
```

## 变体 4：自动补全模式

📝 提示词

```json
{
  "type": "文化人物系列自动补全",
  "mode": "auto-fill",
  "rule": "用户给一个文化主题，自动选角色列表、风格、layout、标签",
  "constraints": {
    "must_feel": "教科书级 / 文创可发布"
  }
}
```

## 避免事项

- 不要混淆朝代服饰（最常见错误）
- 不要让画风漂移（同一系列必须统一）
- 不要在文化敏感主题上使用戏谑表情
- 不要把神祇画成 cosplay 风
- 不要让标签错字 / 漏字
- 不要让单格人物超过 12 个，否则视觉破碎
