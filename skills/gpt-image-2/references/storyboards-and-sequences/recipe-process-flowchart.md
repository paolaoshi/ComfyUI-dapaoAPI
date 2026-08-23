# 食谱 / 流程步骤图模板

本文件用于"按步骤图示展示一个流程"的视觉：

- 食谱 / 烹饪步骤图
- 产品使用步骤图
- DIY 教程步骤图
- 手工 / 化妆步骤图
- 工艺流程图

特征：

- 步骤分明（编号 + 描述 + 插图）
- 有明显流向（→ 或编号顺序）
- 强调"一图能跟着做"
- 通常含食材 / 工具列表
- 视觉清晰、信息密度适中

## 适用范围

- 食谱 / 烘焙步骤图
- 产品使用 / 安装教程图
- 手工 / DIY 教程图
- 化妆 / 护肤步骤图

## 何时使用

- 用户提到"步骤图 / 流程图 / 食谱图 / 教程图 / how-to"
- 用户希望"看图就能跟着做"

不要使用：

- 教学示意图（用 `slides-and-visual-docs/educational-diagram-slide.md`）
- 高密度信息图（用 `infographics/legend-heavy-infographic.md`）
- 角色关系图（用 `character-relationship-diagram.md`）

## 缺失信息优先提问顺序

1. 主题（什么食谱 / 什么教程）
2. 步骤数量（4-8 步）
3. 是否需要食材 / 工具列表
4. 风格：手绘水彩 / 拟物 3D / 扁平卡通 / 摄影实拍
5. 是否双语 / 含英文
6. 比例

## 主模板：食谱步骤图

📖 描述

整体一张图，顶部有菜名 + 食材列表，主体为 4-6 个编号步骤插图，底部有最终成品图。

📝 提示词

```json
{
  "type": "食谱步骤图",
  "goal": "生成一张可作为公众号 / 小红书 / 食谱书页的食谱步骤图",
  "recipe": {
    "name": "{argument name=\"recipe name\" default=\"番茄炒蛋\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"5 分钟家常版\"}",
    "servings": "{argument name=\"servings\" default=\"2 人份\"}",
    "time": "{argument name=\"time\" default=\"5 分钟\"}"
  },
  "ingredients": {
    "enabled": "{argument name=\"ingredients enabled\" default=\"true\"}",
    "position": "{argument name=\"ingredients position\" default=\"顶部右侧\"}",
    "items": [
      "{argument name=\"ing 1\" default=\"番茄 2 个\"}",
      "{argument name=\"ing 2\" default=\"鸡蛋 3 个\"}",
      "{argument name=\"ing 3\" default=\"葱花 适量\"}",
      "{argument name=\"ing 4\" default=\"盐 / 糖 / 油 适量\"}"
    ],
    "design": "每项配小图标"
  },
  "steps": {
    "count": "{argument name=\"step count\" default=\"5\"}",
    "items": [
      {"id": 1, "scene": "{argument name=\"step 1\" default=\"番茄切块，鸡蛋打散\"}"},
      {"id": 2, "scene": "{argument name=\"step 2\" default=\"热油下鸡蛋，炒到半熟盛出\"}"},
      {"id": 3, "scene": "{argument name=\"step 3\" default=\"加油下番茄，炒到出汁\"}"},
      {"id": 4, "scene": "{argument name=\"step 4\" default=\"倒回鸡蛋，加盐少许糖\"}"},
      {"id": 5, "scene": "{argument name=\"step 5\" default=\"翻炒均匀，撒葱花出锅\"}"}
    ],
    "step_block_style": "编号 + 插图 + 1 句说明"
  },
  "final_dish": {
    "enabled": "{argument name=\"final dish enabled\" default=\"true\"}",
    "position": "{argument name=\"final dish position\" default=\"底部居中大图\"}"
  },
  "style": {
    "art_style": "{argument name=\"art style\" default=\"手绘水彩 + 米色纸纹\"}",
    "color_palette": "{argument name=\"color palette\" default=\"番茄红 + 蛋黄 + 米白\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"3:4\"}",
  "constraints": {
    "must_keep": [
      "步骤编号连续清晰",
      "每个步骤插图与说明一致",
      "食材列表与步骤呼应",
      "成品图视觉抢眼"
    ],
    "avoid": [
      "步骤说明超过 15 字",
      "插图与文字脱节",
      "色板出现非食物自然色",
      "字体多种类"
    ]
  }
}
```

### 参数策略

- 必问：菜名、步骤数
- 可默认：风格、配色、食材呈现
- 可随机：背景纹理

### 自动补全策略

- 用户只给菜名时：自动列食材 + 自动展开 4-6 步
- 默认手绘水彩
- 步骤说明 ≤ 15 字 / 步

## 变体 1：产品使用 / 安装教程图

📝 提示词

```json
{
  "type": "产品使用 / 安装教程图",
  "recipe": {
    "name": "{argument name=\"product\" default=\"AURORA Pro 耳机配对\"}"
  },
  "ingredients": { "enabled": false },
  "steps": {
    "count": 4,
    "items": [
      {"id": 1, "scene": "打开充电盒"},
      {"id": 2, "scene": "手机蓝牙开启"},
      {"id": 3, "scene": "选择 'AURORA Pro'"},
      {"id": 4, "scene": "听到提示音即配对成功"}
    ]
  },
  "final_dish": { "enabled": false },
  "style": {
    "art_style": "扁平矢量 + 品牌色"
  },
  "constraints": {
    "must_feel": "说明书级清晰"
  }
}
```

## 变体 2：化妆 / 护肤步骤图

📝 提示词

```json
{
  "type": "化妆 / 护肤步骤图",
  "recipe": {
    "name": "{argument name=\"routine\" default=\"晨间护肤 5 步\"}"
  },
  "steps": {
    "count": 5,
    "items": [
      {"id": 1, "scene": "洁面"},
      {"id": 2, "scene": "化妆水"},
      {"id": 3, "scene": "精华"},
      {"id": 4, "scene": "面霜"},
      {"id": 5, "scene": "防晒"}
    ]
  },
  "style": {
    "art_style": "极简插画 + 柔粉色"
  },
  "constraints": {
    "must_feel": "干净、女性向、可分享"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "流程图自动补全",
  "mode": "auto-fill",
  "rule": "用户给主题，自动决定步骤数、食材 / 工具、风格、配色",
  "constraints": {
    "must_feel": "可直接发公众号 / 小红书"
  }
}
```

## 避免事项

- 不要让步骤数超过 8（注意力会断）
- 不要让单步说明超过 15 字
- 不要让插图与说明描述不一致
- 不要让色板与主题脱节（食物图不应出现荧光蓝）
- 不要漏掉编号 / 漏步
- 不要让食材列表喧宾夺主
