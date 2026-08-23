# 创始人 / 媒体大片肖像模板

本文件用于生成“创始人 / 高管 / 行业人物”级别的媒体大片肖像：

- 财经杂志专访配图
- 创业媒体封面
- 创始人主图（融资 / 上市新闻）
- 行业人物特写
- 个人品牌大片

特征：

- 戏剧性灯光
- 强烈的“人物气质”
- 高对比 / 高叙事感
- 通常竖版 3:4 / 4:5
- 留位置给标题或引言

## 适用范围

- 财经 / 创业杂志专访
- 公司官网创始人大片
- 行业人物特写
- 个人品牌主图

## 何时使用

- 用户提到“创始人大片 / 杂志专访 / 高管照 / 媒体大片 / 人物气质照”
- 用户希望视觉高叙事性、有“人物即故事”感

不要使用：

- 普通商务头像（用 `professional-portrait.md`）
- 虚拟主播（用 `virtual-host.md`）
- 角色设定（用 `character-sheet.md`）

## 缺失信息优先提问顺序

1. 人物身份 / 行业
2. 性别 / 年龄
3. 风格：黑白文学 / 工业感 / 创新派 / 古典财经
4. 构图：环境人像 / 特写 / 半身
5. 配色 / 灯光基调
6. 是否需要预留标题位

## 主模板：媒体大片创始人肖像

📖 描述

整体竖版肖像，主体为人物半身或环境人像，戏剧性侧光，强叙事，预留标题位。

📝 提示词

```json
{
  "type": "媒体大片级创始人肖像",
  "goal": "生成一张能直接作为财经杂志 / 创业媒体专访配图 / 公司官网创始人主图的媒体大片肖像",
  "subject": {
    "identity": "{argument name=\"identity\" default=\"AI 公司创始人 CEO\"}",
    "gender": "{argument name=\"gender\" default=\"东亚男性\"}",
    "age_range": "{argument name=\"age range\" default=\"35-45 岁\"}",
    "appearance": "{argument name=\"appearance\" default=\"头发整齐，神情沉稳\"}",
    "outfit": "{argument name=\"outfit\" default=\"深色高领针织 + 长款外套\"}"
  },
  "composition": {
    "shot": "{argument name=\"shot\" default=\"环境人像 + 半身\"}",
    "framing": "{argument name=\"framing\" default=\"人物在画面 1/3 处，背景留出 2/3 给环境\"}",
    "title_safe_area": "{argument name=\"title safe area\" default=\"画面右上预留标题位\"}"
  },
  "environment": {
    "location": "{argument name=\"location\" default=\"现代办公空间，落地窗 + 极简家具\"}",
    "depth": "{argument name=\"depth\" default=\"浅景深，背景虚化\"}"
  },
  "lighting": {
    "style": "{argument name=\"lighting style\" default=\"戏剧性侧光\"}",
    "key_light": "{argument name=\"key light\" default=\"窗户大面积自然光\"}",
    "fill_light": "{argument name=\"fill light\" default=\"暗部留细节\"}",
    "color_temp": "{argument name=\"color temp\" default=\"略冷\"}"
  },
  "expression": {
    "mood": "{argument name=\"mood\" default=\"沉静、有思考感\"}",
    "gaze": "{argument name=\"gaze\" default=\"略偏离镜头，望向远处\"}"
  },
  "style": {
    "rendering": "高分辨率人像摄影 + 杂志后期",
    "tone": "微微暗调 + 高对比 + 略颗粒",
    "color_palette": "{argument name=\"color palette\" default=\"冷灰 + 墨黑 + 暖肤色\"}"
  },
  "constraints": {
    "must_keep": [
      "人物表情有故事感",
      "灯光方向统一",
      "构图留出标题位",
      "整体克制不娱乐化"
    ],
    "avoid": [
      "出现 LOGO 与品牌元素",
      "夸张戏剧光",
      "饱和滤镜",
      "环境喧宾夺主"
    ]
  }
}
```

### 参数策略

- 必问：身份、性别、年龄、环境
- 可默认：色调、灯光、构图
- 可随机：环境家具细节

### 自动补全策略

- 行业自动选环境（金融 = 大理石大厅；科技 = 极简办公室；制造 = 工厂车间；创意 = 工作室）
- 灯光默认窗光 + 戏剧侧光
- 留标题位默认右上

## 变体 1：黑白文学风创始人肖像

📝 提示词

```json
{
  "type": "黑白文学风创始人肖像",
  "style": {
    "rendering": "高对比黑白 + 颗粒",
    "color_palette": "纯黑白"
  },
  "lighting": {
    "style": "硬光 + 强阴影"
  },
  "constraints": {
    "must_feel": "时间感、故事感、文学性"
  }
}
```

## 变体 2：工业 / 工厂背景创始人

📝 提示词

```json
{
  "type": "工业背景创始人肖像",
  "environment": {
    "location": "{argument name=\"factory\" default=\"产线背后，机械臂虚化\"}"
  },
  "lighting": {
    "style": "工业冷光 + 局部暖光"
  },
  "constraints": {
    "must_feel": "硬核、有制造感、可信赖"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "创始人大片自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给行业 + 人物名 / 性别，自动决定环境、风格、灯光",
  "constraints": {
    "must_feel": "可上财经杂志封面"
  }
}
```

## 避免事项

- 不要让人物正脸正中央（媒体大片不喜欢死板构图）
- 不要让背景出现真实品牌 logo
- 不要使用过度修图（皮肤要保留质感）
- 不要让灯光戏剧到“妆面感强”
- 不要忽略标题留白
