# 角色 n×n 网格肖像模板

本文件用于"一张图里包含同一角色的多个版本（不同表情 / 不同职业 / 不同朝代 / 不同表情）"：

- 2×2 / 3×3 / 4×4 同一人物多职业 / 多场景
- 表情九宫格（喜怒哀乐 + 等等）
- 朝代 / 神话角色系列肖像
- 多种风格统一展示
- 多角色 group portrait grid

特征：

- 一张图分多格
- 每格是同一身份的不同呈现
- 网格线 / 透明分隔
- 强调"同一人 / 同一角色"的一致性

## 适用范围

- 一人多职业网格
- 表情九宫格
- 同一角色不同朝代 / 文化
- 同一角色不同造型集合

## 何时使用

- 用户希望一张图展示一个人的多个面
- 用户希望直接得到"网格图"而不是单图
- 用户希望同一身份的多版本对比

不要使用：

- 表情 / 服装设定稿（用 `portraits-and-characters/character-sheet.md`）
- 单张风格转换（用 `style-transfer-selfie.md`）
- 多个不同角色拼贴（用 `grids-and-collages/mixed-style-multi-panel.md`）

## 缺失信息优先提问顺序

1. 主体身份（参考图 / 文字描述）
2. 网格规格（2×2 / 3×3 / 4×4）
3. 每格的差异维度（职业 / 表情 / 朝代 / 风格）
4. 每格的具体内容（用户列 or 我帮列）
5. 风格基底（写实 / 3D 卡通 / anime）
6. 比例

## 主模板：2×2 同一人多职业网格

📖 描述

2×2 四格，主体为同一人，分别身处不同职业 / 场景。

📝 提示词

```json
{
  "type": "2x2 同一人物多职业网格",
  "goal": "生成一张 2×2 网格图，主体为同一人物，每格呈现不同职业身份与场景，可作为 LinkedIn / 自我介绍 / 创意头像使用",
  "subject": {
    "description": "{argument name=\"subject description\" default=\"东亚年轻男性，短黑发，自然微笑\"}",
    "consistency": "四格中脸型、肤色、五官比例必须严格一致"
  },
  "style": "{argument name=\"art style\" default=\"高分辨率写实人像摄影 + 自然光\"}",
  "layout": {
    "format": "2x2 grid",
    "panel_count": 4,
    "gap": "细白色分隔线",
    "panels": [
      {
        "position": "top-left",
        "scenario": "{argument name=\"panel 1\" default=\"职场商务：深蓝西装 + 白衬衫 + 蓝色领带，背景为灰色纹理\"}"
      },
      {
        "position": "top-right",
        "scenario": "{argument name=\"panel 2\" default=\"户外休闲：深蓝 T 恤，背景为虚化公园\"}"
      },
      {
        "position": "bottom-left",
        "scenario": "{argument name=\"panel 3\" default=\"建筑工人：黄色安全帽 + 橙色反光背心，背景为虚化车间\"}"
      },
      {
        "position": "bottom-right",
        "scenario": "{argument name=\"panel 4\" default=\"医务人员：白色实验服 + 浅蓝衬衫，背景为虚化实验室\"}"
      }
    ]
  },
  "constraints": {
    "must_keep": [
      "四格中是同一个人",
      "每格灯光自然且统一风格",
      "服装与场景高度匹配",
      "细分隔线清晰"
    ],
    "avoid": [
      "四格像四个不同人",
      "服装与场景明显错配",
      "网格线过粗破坏视觉",
      "每格风格漂移"
    ]
  }
}
```

### 参数策略

- 必问：主体描述、4 个差异维度
- 可默认：风格基底、网格分隔线
- 可随机：每格背景细节

### 自动补全策略

- 用户只给主体时：自动选 4 个反差大的职业 / 场景（商务 + 户外 + 蓝领 + 医疗 是经典组合）
- 默认 2×2 网格
- 默认写实摄影

## 变体 1：3×3 表情九宫格（同一角色）

📝 提示词

```json
{
  "type": "3x3 同一角色表情九宫格",
  "subject": {
    "description": "{argument name=\"character\" default=\"3D 动画风格，戴圆框眼镜，自然短发\"}",
    "common_theme": "{argument name=\"framing concept\" default=\"从撕开的白纸洞里探头\"}"
  },
  "style": "{argument name=\"art style\" default=\"3D Pixar 动画风\"}",
  "layout": {
    "format": "3x3 grid",
    "panel_count": 9,
    "panels": [
      {"expression": "眨眼", "action": "扶眼镜", "outfit": "绿色毛衣"},
      {"expression": "坏笑", "action": "拉低墨镜", "outfit": "红皮衣"},
      {"expression": "思考", "action": "手指点下巴", "outfit": "黄色卫衣"},
      {"expression": "大笑", "action": "趴在洞边", "outfit": "黑白条纹衫"},
      {"expression": "微笑", "action": "竖大拇指", "outfit": "橘色衬衫"},
      {"expression": "淡定", "action": "喝珍奶", "outfit": "蓝色毛衣"},
      {"expression": "开心", "action": "挥手", "outfit": "紫色马甲 + 白衬衫"},
      {"expression": "笑到闭眼", "action": "抱臂", "outfit": "粉色开衫"},
      {"expression": "搞怪", "action": "戳脸颊", "outfit": "蓝绿色毛衣"}
    ]
  },
  "constraints": {
    "must_feel": "九格是同一角色，仅表情 / 动作 / 服装变化"
  }
}
```

## 变体 2：3×3 历史朝代肖像系列

📝 提示词

```json
{
  "type": "3x3 朝代肖像系列",
  "subject": {
    "description": "{argument name=\"subject\" default=\"东亚男性，30 岁，气质沉稳\"}",
    "common_theme": "同一人物在不同朝代的形象"
  },
  "style": "高分辨率水墨写实",
  "layout": {
    "format": "3x3 grid",
    "panel_count": 9,
    "items": [
      "汉朝 / 唐朝 / 宋朝 / 元朝 / 明朝 / 清朝 / 民国 / 建国初 / 现代"
    ]
  },
  "constraints": {
    "must_feel": "九格是同一人，仅服饰、配饰、背景与时代相符"
  }
}
```

## 变体 3：4×4 同一角色风格集合

📝 提示词

```json
{
  "type": "4x4 同一角色风格集合",
  "subject": "{argument name=\"subject\" default=\"基于参考图的本人\"}",
  "layout": {
    "format": "4x4 grid",
    "panel_count": 16,
    "common_theme": "同一身份的 16 种不同风格（赛博朋克 / 街头 / 古风 / Y2K / 极简 / 油画 / 哥特 / ...）"
  },
  "constraints": {
    "must_feel": "16 格风格反差大但身份保持一致"
  }
}
```

## 变体 4：自动补全模式

📝 提示词

```json
{
  "type": "角色网格肖像自动补全",
  "mode": "auto-fill",
  "rule": "用户给主体 + 网格规格，自动决定每格内容、风格、构图",
  "constraints": {
    "must_feel": "可直接当头像合集 / 表情包 / 自我介绍图"
  }
}
```

## 避免事项

- 不要让不同格子里的人物像不同人（一致性是核心）
- 不要让网格分隔线过粗
- 不要让每格风格漂移（总体风格应统一）
- 不要超过 4×4（再多会让每格太小）
- 不要把网格题材分散到完全无关的主题（保留一致性维度）
