# 步骤 / 流程信息图模板

本文件用于生成"步骤 / 流程 / how-to / 教程"风信息图：

- 食谱 / 烘焙步骤图
- 操作教程 / app 使用流程
- 健身动作分解
- 化妆 / 护肤流程
- 旅行 / 报销 / 申请流程
- 育儿 / DIY 操作步骤

特征：

- 每一步有明显编号
- 每一步配一个简洁插画 / 图标
- 步骤之间有指引箭头 / 连接线
- 步骤数通常 3-7 步，最多 9 步
- 风格偏插画感、温暖、易懂（**与"工程精度流程图"明显不同**）

## 适用范围

- 食谱 / 操作 / 教程展示
- "X 步学会..." 类内容
- DIY / 手工 / 改造步骤
- 育儿 / 健身 / 美妆步骤
- 用户引导 / 入门指南

## 何时使用

- 用户提到 "步骤 / 流程 / how-to / 教程 / X 步 / 操作指南 / 食谱 / 化妆步骤"
- 用户希望"读者照着一步一步做"
- 用户希望视觉「插画感、温暖、易懂」（不是工程感）

不要使用：

- 用户要的是「工程精度的流程图」（菱形决策、Yes/No 分支） → 用 `technical-diagrams/flowchart-decision.md`
- 用户要的是「漫画分镜」 → 用 `storyboards-and-sequences/recipe-process-flowchart.md`
- 用户要的是「方法 pipeline 论文图」 → 用 `academic-figures/method-pipeline-overview.md`
- 用户要的是「便当格高密度信息」 → 用 `infographics/bento-grid-infographic.md`

## 缺失信息优先提问顺序

1. 主题 + 步骤数（如"3 步学会做意面 / 5 步配置开发环境 / 7 步完成日常护肤"）
2. 每一步的具体内容（标题 + 一两句说明）
3. 配色基调（暖系食物 / 清新护肤 / 卡通教程 / 黑板教学）
4. 排布方式（垂直瀑布 / 水平横排 / 蜿蜒路径 / 圆圈循环）
5. 是否带封面 / 完成图（开头一张「成品图」或结尾一张「成品展示」）
6. 比例（小红书 3:4 / 公众号 16:9 / 1:1）

## 主模板：步骤教程信息图

📖 描述

整张图按 3-7 个编号步骤排列，每一步包含：编号 badge + 步骤标题 + 步骤插画 + 简短文字说明，步骤之间用箭头 / 连线串联。

📝 提示词

```json
{
  "type": "步骤教程信息图",
  "goal": "生成一张让读者能照着一步步做的、插画感强、温暖易懂的教程图",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"3:4 portrait\"}",
    "background": "{argument name=\"background\" default=\"warm cream #FAF6EE 带轻微纸质感\"}"
  },
  "header": {
    "main_title": "{argument name=\"main_title\" default=\"5 步学会自制日式蛋包饭\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"零基础也能成功 · 20 分钟\"}",
    "optional_finished_image": "{argument name=\"finished_image\" default=\"右上角放一张'成品小图' + 装饰边框\"}"
  },
  "palette": {
    "primary": "{argument name=\"primary\" default=\"warm orange #E89F71\"}",
    "secondary": "{argument name=\"secondary\" default=\"sage green #9FB89E\"}",
    "neutral": "{argument name=\"neutral\" default=\"deep brown #4A3A2E\"}",
    "rule": "限制 3-4 主色，每步插画风格一致"
  },
  "layout": {
    "style": "{argument name=\"layout_style\" default=\"vertical-zigzag\"}",
    "options_explained": {
      "vertical-stack": "纯垂直瀑布，每步一行",
      "vertical-zigzag": "Z 字形蛇形，奇偶步左右交替",
      "horizontal-row": "横向 3-5 步并列",
      "circular": "圆环上分布步骤（适合循环型）",
      "winding-path": "蜿蜒小路，步骤沿路径分布（适合烹饪 / 旅行）"
    }
  },
  "steps": {
    "count": "{argument name=\"step_count\" default=\"5\"}",
    "structure_per_step": [
      "大编号 badge（圆形 / 圆角方块，统一色调，编号字体大且粗）",
      "步骤标题（4-8 字，加粗）",
      "插画图标 / 小场景（手绘感、单一物体或动作示意）",
      "1-2 行说明文字"
    ],
    "items_example": [
      "01 准备食材：鸡蛋 3 个、米饭一碗、洋葱 1/4、火腿丁",
      "02 洋葱炒香：黄油下锅，洋葱炒至透明",
      "03 拌入米饭：加入米饭和火腿，调味翻炒",
      "04 摊蛋皮：另起锅打散鸡蛋，做成半熟蛋皮",
      "05 包入装盘：把炒饭放上蛋皮，对折成船形，挤番茄酱"
    ]
  },
  "connectors": {
    "style": "{argument name=\"connector_style\" default=\"hand-drawn curved arrows\"}",
    "rule": "步骤之间必须有视觉指引：箭头 / 虚线 / 脚印 / 食材飞溅元素均可"
  },
  "footer": {
    "tip": "{argument name=\"tip\" default=\"💡 番茄酱可以换成韩式辣酱，味道更下饭\"}",
    "credit": "{argument name=\"credit\" default=\"@your_handle\"}"
  },
  "constraints": {
    "must_keep": [
      "每步插画风格一致（手绘 / 扁平 / 卡通 二选一，不混)",
      "编号 badge 设计完全一致（颜色、字号、形状）",
      "步骤之间视觉连接清晰",
      "文字不超过两行 / 步",
      "插画大小一致或按重要度梯度"
    ],
    "avoid": [
      "工程图风（直角、监工色板、菱形决策框）",
      "每步插画风格不同",
      "步骤数 < 3（太短不像教程）或 > 9（太长读不动）",
      "无编号 / 编号风格不一致",
      "步骤说明超过 3 行（变成长文）",
      "用 Helvetica 等冷感字体（建议手写感 / 圆体 / 友好字体）"
    ]
  }
}
```

### 参数策略

- **必问**：`step_count`、每一步的标题（即 `items_example` 实际内容）
- **可默认**：`background`、`palette`（按主题选——食物用暖橙、护肤用 macaron、技术教程用 mint）、`layout_style`（默认 vertical-zigzag）、`connector_style`
- **可随机**：每步插画的具体造型、connector 是箭头还是虚线、装饰物（飞溅 / 星点 / 小标签）

### 自动补全策略

- 用户只给主题（如"5 步学会做意面"）：自动补全 5 步具体内容、自动选暖色食物 palette、自动加成品小图
- 用户说"小红书风" → 加手绘装饰 + macaron 配色
- 用户说"美妆 / 护肤" → palette 切换到 dusty pink + cream
- 用户说"健身" → palette 切换到 mint + coral，插画用人物动作示意
- 用户说"DIY / 手工" → 加工具 emoji / 材料 list
- 用户说"技术教程" → palette 切换 mint + slate，插画用截图框

## 变体 1：横向 3-5 步流程

```json
{
  "type": "横向步骤教程信息图",
  "modify": {
    "aspect_ratio": "16:9 landscape",
    "layout_style": "horizontal-row",
    "step_count": "3-5",
    "rule": "每步等宽并列，步骤之间用粗箭头连接，每步上方编号下方说明"
  }
}
```

适用：网页 hero、PPT 单页、产品 onboarding 页面。

## 变体 2：蜿蜒小路 / Winding path 流程

```json
{
  "type": "蜿蜒小路步骤教程信息图",
  "modify": {
    "layout_style": "winding-path",
    "background": "插画感地图底（草地 / 厨房 / 城市路面）",
    "rule": "步骤沿一条蜿蜒小路分布，路上画脚印 / 食材 / 工具，每步在路边的小卡片上",
    "vibe": "旅行游记、烹饪冒险、儿童教程"
  }
}
```

适用：儿童教程、旅行规划、有故事感的步骤展示。

## 变体 3：圆环循环步骤

```json
{
  "type": "圆环循环步骤信息图",
  "modify": {
    "layout_style": "circular",
    "step_count": "4-8",
    "rule": "步骤排列在一个大圆环上，按顺时针，箭头沿圆环走，中央放主题字 + 总结",
    "vibe": "PDCA / 季节循环 / 生命周期 / 月度 routine"
  }
}
```

适用：PDCA 循环、月度计划循环、健身 routine、季节循环。

## 避免事项

- 步骤数太多（>9）或太少（<3）
- 步骤插画风格混杂（一步手绘一步扁平）
- 编号 badge 设计每步都不一样
- 没有视觉连接（步骤像散落的卡片）
- 用工程图的菱形决策 / 直角箭头 → 失去插画温度感
- 用 Helvetica / Arial 冷感字体
- 步骤说明超过 3 行 → 变长文，失去信息图特性
- 把"流程图"做成这个模板（流程图请用 `technical-diagrams/flowchart-decision.md`）
