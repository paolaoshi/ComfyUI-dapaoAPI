# 人物关系图模板

本文件用于"基于一部作品 / 一个组织生成角色关系图"：

- 动漫 / 电影 / 小说人物关系图
- 公司 / 组织成员关系图
- 历史事件参与者关系图
- 团队 / 派系关系图

特征：

- 多个角色卡片（头像 + 名字 + 标签）
- 不同颜色 / 线型表示不同关系
- 视觉层级清晰（主角大、配角小）
- 强调"信息可视化 + 海报设计感"
- 整体克制不杂乱

## 适用范围

- IP 角色关系图
- 组织 / 团队结构图
- 历史事件人物关系图
- 自媒体科普图

## 何时使用

- 用户提到"关系图 / 关系网 / 角色 graph / 派系图"
- 用户希望一张图能讲清楚谁和谁是什么关系

不要使用：

- 单图 KV（用 `anime-key-visual.md`）
- 角色设定稿（用 `portraits-and-characters/character-sheet.md`）
- 一般信息图（用 `infographics/legend-heavy-infographic.md`）

## 缺失信息优先提问顺序

1. 主题（哪部作品 / 哪个组织）
2. 角色数量（建议 6-12）
3. 主角是谁（视觉权重最高）
4. 关系类型（血缘 / 友情 / 师徒 / 敌对 / 联盟 / 暗恋）
5. 风格：贴合原作画风 / 通用现代设计风
6. 比例

## 主模板：作品角色关系图海报

📖 描述

整体一张大图，多个角色卡片按关系网排布，连线区分不同关系类型，配图例与标题。

📝 提示词

```json
{
  "type": "作品角色关系图海报",
  "goal": "生成一张高完成度的角色关系图，可作为科普 / 同人 / 入坑指南海报",
  "ip": {
    "name": "{argument name=\"ip name\" default=\"鬼灭之刃\"}",
    "tone": "{argument name=\"ip tone\" default=\"贴合原作风格 + 海报设计感\"}"
  },
  "characters": {
    "count": "{argument name=\"character count\" default=\"9\"}",
    "auto_select": "{argument name=\"auto select\" default=\"true\"}",
    "rule": "若 auto_select 为 true，则按主题自动选 6-12 个最具代表性的角色",
    "user_list": "{argument name=\"user list\" default=\"\"}",
    "card_design": {
      "components": ["头像", "名字", "派系 / 身份标签"],
      "shape": "{argument name=\"card shape\" default=\"圆角方形\"}"
    }
  },
  "composition": {
    "structure": "{argument name=\"composition\" default=\"主角中心 + 同伴左右 + 敌对在远端\"}",
    "hierarchy": "主角卡片最大、重要配角中等、次要角色最小"
  },
  "relationships": {
    "types": [
      {"name": "血缘", "color": "深红", "line": "实线"},
      {"name": "友情 / 同伴", "color": "暖橙", "line": "实线"},
      {"name": "师徒", "color": "金色", "line": "双实线"},
      {"name": "敌对", "color": "深紫", "line": "锯齿线"},
      {"name": "暗恋", "color": "粉色", "line": "虚线"},
      {"name": "联盟", "color": "绿色", "line": "粗实线"}
    ],
    "annotation_rule": "在每条线中段标注关系简短文字"
  },
  "title_block": {
    "main_title": "{argument name=\"main title\" default=\"鬼灭之刃 · 人物关系图\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"一图入坑\"}",
    "position": "顶部"
  },
  "legend": {
    "enabled": "{argument name=\"legend enabled\" default=\"true\"}",
    "position": "{argument name=\"legend position\" default=\"右下角\"}"
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"贴合原作画风的角色头像 + 现代海报排版\"}",
    "color_palette": "{argument name=\"color palette\" default=\"参考原作主色\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "主角视觉最大",
      "关系线不交叉混乱",
      "每个角色名清晰可读",
      "图例与关系类型严格对应"
    ],
    "avoid": [
      "信息过载（>15 个角色）",
      "线型 > 6 种",
      "颜色超过 8 种",
      "出现廉价流程图感"
    ]
  }
}
```

### 参数策略

- 必问：主题、角色数量
- 可默认：关系类型、layout、图例、风格
- 可随机：背景纹理

### 自动补全策略

- 用户给主题时：自动选代表性角色 + 自动判断关系类型
- 默认主角中心构图
- 默认 6 种关系类型，按需要简化

## 变体 1：组织 / 团队结构图

📝 提示词

```json
{
  "type": "组织 / 团队结构图",
  "ip": {
    "name": "{argument name=\"organization\" default=\"某 AI 创业公司\"}",
    "tone": "现代企业海报"
  },
  "composition": {
    "structure": "金字塔型：CEO 顶 + 高管中 + 普通员工底"
  },
  "relationships": {
    "types": [
      {"name": "汇报", "color": "灰", "line": "实线"},
      {"name": "协作", "color": "蓝", "line": "虚线"}
    ]
  },
  "constraints": {
    "must_feel": "专业 + 可发布"
  }
}
```

## 变体 2：历史事件参与者图

📝 提示词

```json
{
  "type": "历史事件参与者关系图",
  "ip": {
    "name": "{argument name=\"event\" default=\"三国赤壁之战\"}",
    "tone": "历史插画 + 海报设计"
  },
  "composition": {
    "structure": "三派对峙：曹操方 / 孙权方 / 刘备方"
  },
  "constraints": {
    "must_feel": "教科书与海报兼具"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "角色关系图自动补全",
  "mode": "auto-fill",
  "rule": "用户给一个主题（作品 / 组织 / 事件），自动选角色 + 关系 + 风格 + 图例",
  "constraints": {
    "must_feel": "一图入坑级"
  }
}
```

## 避免事项

- 不要让角色超过 15 个
- 不要让线型超过 6 种
- 不要让所有线交叉成网（要有清晰阅读顺序）
- 不要简单复制官方海报排版
- 不要让标签字号比角色名小
- 不要忽略图例
