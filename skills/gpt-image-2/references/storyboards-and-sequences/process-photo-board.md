# 真人摄影流程图 / 装备穿戴 / 操作流程板模板

本文件用于生成"真人 / 角色级 cinematic 实拍质感的多步骤操作流程板"。常见场景：

- 装备穿戴 / 战甲组装 / 制服换装流程
- 工艺操作 / 化妆 / 实验 / 工坊步骤
- 训练 / 武术 / 健身一组动作分解
- 器械维修 / 装机 / 设备启动流程
- 角色 cosplay / 道具佩戴流程
- 任何「步骤 1 → 步骤 N，每步一张实拍 cinematic 图 + 编号 + 描述」的视觉手册

特征（与现有/新增模板的区别）：

| 模板 | 性质 |
|---|---|
| `recipe-process-flowchart.md`（已有） | 食谱流程（手绘 / illustration 风） |
| `pose-reference-sheet.md`（新增） | 姿势字典（同一角色 N 个孤立动作，无叙事顺序） |
| `cinematic-storyboard-grid.md`（新增） | 电影分镜（连续叙事，事件/情绪） |
| `product-tvc-storyboard.md`（新增） | 商业 TVC 分镜（产品中心） |
| **本模板**（新增） | **真人/角色实拍 cinematic 流程板**（步骤中心 + 顺序 + 装备状态变化） |

**核心区别**：本模板每张子图都是「同一角色不同步骤的真人/cinematic 实拍 still」，强调**装备状态 / 操作姿态从步骤 1 到 N 的变化**，并配步骤编号 + 步骤标题 + 步骤说明。

## 适用范围

- 装备穿戴流程（战甲 / 战术装备 / cosplay）
- 工艺操作流程（咖啡冲泡 / 化妆 / 实验）
- 训练分解（武术 / 健身 / 舞蹈技术分解）
- 设备启动 / 维修 / 装机流程
- 仪式 / 着装礼仪流程

## 何时使用

- 用户提到"装备 / 穿戴 / 流程图 / 步骤板 / 操作分解 / process board"
- 主体是**同一真人角色**或**同一物体**经历**有序的状态变化**
- 想要**实拍 / cinematic 写实质感**（不是手绘/线稿）
- 每步都需要图像 + 步骤编号 + 步骤说明文本

不要使用：

- 食谱 / 教程线稿流程 → 用 `recipe-process-flowchart.md`
- 姿势字典 / 动作字典（无顺序） → 用 `pose-reference-sheet.md`
- 电影叙事分镜（叙事重于步骤） → 用 `cinematic-storyboard-grid.md`
- 商业广告 TVC（产品中心） → 用 `product-tvc-storyboard.md`

## 缺失信息优先提问顺序

1. 流程主题（什么的流程？装备 / 化妆 / 操作 / 训练）
2. 角色描述（性别 / 年龄 / 发型 / 服装 / 关键识别特征）
3. 步骤数量（推荐 4 / 6 / 8 / 9）+ 网格（2×3 / 3×2 / 3×3 / 2×4）
4. 每步标题 + 简述（装备状态 / 动作描述）
5. 风格（**cinematic 实拍 / tokusatsu 特摄 / 时尚大片 / 工坊纪实 / 教程截图**）
6. 语言（标题 / 说明文字使用语言：日文 / 中文 / 英文）
7. 环境（工坊 / 化妆间 / 健身房 / 实验室 / 户外）
8. 比例（横版 16:9 看板 / 竖版 4:5 手册 / 1:1 社交媒体）

## 主模板：3×2 = 6 步真人 cinematic 装备穿戴流程板（特摄风案例）

📖 描述

横版 16:9 大图，2 行 3 列共 6 格。顶部标题横幅 + 6 格步骤图（每图带红色数字编号方块 + 步骤日文标题 + 步骤说明）+ 底部口号横幅。每格都是同一角色实拍 cinematic still，装备状态按步骤递进。

📝 提示词

```json
{
  "type": "{argument name=\"theme type\" default=\"Japanese sci-fi armor dressing-process infographic\"}",
  "goal": "生成一张以同一角色为主角、按步骤递进展示装备/操作变化的 cinematic 实拍流程板",
  "style": "{argument name=\"overall style\" default=\"cinematic live-action tokusatsu-inspired promotional board, realistic industrial lighting, polished metal surfaces, sharp photographic detail\"}",
  "theme": "{argument name=\"process theme\" default=\"manual pre-battle suit-up sequence for a female hero in a red, silver, black, and blue protector suit\"}",
  "subject": {
    "character": {
      "gender": "{argument name=\"gender\" default=\"female\"}",
      "age": "{argument name=\"age\" default=\"young adult\"}",
      "identity": "{argument name=\"identity\" default=\"helmetless heroine during assembly, face intentionally obscured or anonymized in every unhelmeted panel\"}",
      "hair": "{argument name=\"hair\" default=\"dark brown to black hair tied in a high ponytail with bangs\"}",
      "undersuit": "{argument name=\"undersuit\" default=\"glossy black skintight inner suit with silver chest panel and white neck ring\"}",
      "armor_or_outfit": "{argument name=\"armor description\" default=\"retro-futuristic protector armor with red shoulder and arm plates, silver breastplate and torso plating, circular blue chest core, red waist unit, white gloves, red forearm guards with yellow stripe accents\"}",
      "helmet_or_headpiece": "{argument name=\"helmet description\" default=\"round red-and-silver helmet with black visor\"}"
    },
    "environment": {
      "location": "{argument name=\"location\" default=\"high-tech industrial hangar or armor bay\"}",
      "background_elements": "{argument name=\"background elements\" default=\"metal framework, robotic equipment, tool benches, armor racks, computer monitors, workshop lighting, bay corridor marked BAY-07 in final panel\"}"
    }
  },
  "layout": {
    "header": {
      "count": 2,
      "labels": [
        "{argument name=\"header title\" default=\"ソルジャンヌ・スーツ 手動装着プロセス\"}",
        "{argument name=\"header subtitle\" default=\"専用プロテクタースーツ『ソルジャンヌ』を、戦闘前に手動で装着する様子。各ユニットを確実に装着し、システムを起動する。\"}"
      ],
      "design": "wide black-to-red gradient banner across top, large bold white headline text, diagonal red accent stripe"
    },
    "sections": [
      {
        "step_id": 1,
        "title": "{argument name=\"step 1 title\" default=\"1 インナースーツの確認\"}",
        "position": "top-left",
        "labels": ["{argument name=\"step 1 caption\" default=\"各部のセンサーとコネクタをチェック。戦闘に備え、身体の状態を最終確認する。\"}"],
        "image": "{argument name=\"step 1 image\" default=\"three-quarter view of the heroine in only the black glossy inner suit, looking down while checking or tightening a wrist connector\"}"
      },
      {
        "step_id": 2,
        "title": "{argument name=\"step 2 title\" default=\"2 胸部・肩部アーマーの装着\"}",
        "position": "top-center",
        "labels": ["{argument name=\"step 2 caption\" default=\"胸部ユニットと肩部プロテクターを装着。コネクタを接続し、ロックを固定する。\"}"],
        "image": "{argument name=\"step 2 image\" default=\"mid shot with chest armor and red shoulder plates installed, heroine fastening the front torso area with both hands\"}"
      },
      {
        "step_id": 3,
        "title": "{argument name=\"step 3 title\" default=\"3 腰部ユニット・ベルトの固定\"}",
        "position": "top-right",
        "labels": ["{argument name=\"step 3 caption\" default=\"ウエストユニットを装着し、各部のロックを確認。可動部の動作チェックを行う。\"}"],
        "image": "{argument name=\"step 3 image\" default=\"mid shot with torso armor completed, heroine tightening or checking the waist belt and side locks\"}"
      },
      {
        "step_id": 4,
        "title": "{argument name=\"step 4 title\" default=\"4 ヘルメットの準備\"}",
        "position": "bottom-left",
        "labels": ["{argument name=\"step 4 caption\" default=\"ヘルメットのバイザーと内部システムをチェック。ヘッドセットとの同期を確認する。\"}"],
        "image": "{argument name=\"step 4 image\" default=\"heroine holding the red helmet in both hands at chest height, showing the glossy black visor\"}"
      },
      {
        "step_id": 5,
        "title": "{argument name=\"step 5 title\" default=\"5 ヘルメットの装着・システム起動\"}",
        "position": "bottom-center",
        "labels": ["{argument name=\"step 5 caption\" default=\"ヘルメットを装着し、直上のコネクタをロック。全身のシステムが起動し、胸部コアが発光する。\"}"],
        "image": "{argument name=\"step 5 image\" default=\"heroine placing the helmet onto her head with both hands; blue chest core glowing brightly\"}"
      },
      {
        "step_id": 6,
        "title": "{argument name=\"step 6 title\" default=\"6 装着完了\"}",
        "position": "bottom-right",
        "labels": ["{argument name=\"step 6 caption\" default=\"全システムの最終チェックを行い、戦闘モードへ。ソルジャンヌ、出撃準備完了!\"}"],
        "image": "{argument name=\"step 6 image\" default=\"full-body frontal hero pose in a futuristic corridor, fully suited with helmet on, arms relaxed at sides\"}"
      }
    ],
    "footer": {
      "count": 1,
      "labels": ["{argument name=\"footer slogan\" default=\"一つ一つの装着が、命を守り、力を引き出す。ソルジャンヌの戦いは、ここから始まる。\"}"],
      "design": "dark red cinematic footer strip with centered white slogan"
    },
    "grid": {
      "rows": 2,
      "columns": 3,
      "panel_count": 6,
      "panel_borders": "thin white dividers",
      "number_badges": "red square badges with white numerals 1-6 placed at the corner of each panel"
    }
  },
  "text_rendering": {
    "language": "{argument name=\"language\" default=\"Japanese\"}",
    "font": "{argument name=\"font style\" default=\"bold sans-serif headline with smaller sans-serif body text\"}",
    "colors": "{argument name=\"text color scheme\" default=\"white text on black, red, and white info bars; red numbered squares with white numerals\"}"
  },
  "composition": "{argument name=\"composition\" default=\"16:9 wide infographic board, six equal photo panels arranged in a 3-by-2 grid, each panel captioned below with a red numbered box from 1 to 6\"}",
  "lighting": "{argument name=\"lighting\" default=\"moody workshop lighting with metallic reflections and red accent lights, realistic shadows, cinematic sci-fi atmosphere\"}",
  "constraints": {
    "must_keep": [
      "同一角色（外貌 / 体型 / 内衬）在所有 panel 中一致",
      "装备状态在每一步显式递进（穿了什么 → 又穿了什么）",
      "每格带清晰编号 + 步骤标题 + 简要说明",
      "标题语言、字体、配色保持统一",
      "整体 16:9 看板布局工整对齐",
      "光线 / color grading / 环境质感统一"
    ],
    "avoid": [
      "角色长相 / 发型 / 体型在不同 panel 漂移",
      "装备状态非递进（步骤 4 比步骤 5 更全副武装）",
      "缺少编号 / 标题 / 说明",
      "把流程板做成姿势字典（每格无叙事联系）",
      "把流程板做成漫画 / 加对话气泡",
      "环境 / 灯光 / 滤镜在不同 panel 风格不一致"
    ]
  }
}
```

### 参数策略

- **必问**：theme（什么流程）、character（角色描述）、6 个 step title + caption + image（按顺序递进）、language
- **可默认**：style、environment、composition、lighting、grid
- **可随机**：footer slogan、background detail（除非用户指定）

### 自动补全策略

- 用户给一句"想要 6 步装备穿戴流程" → 按「内层 → 上身 → 下身 → 头部准备 → 头部装上 → 全身完成」自动拆 6 步
- 用户给一句"咖啡冲泡 6 步" → 按「研磨 → 称重 → 烧水 → 闷蒸 → 注水 → 出杯」自动拆
- 用户给"化妆 6 步" → 按「打底 → 遮瑕 → 眼妆 → 腮红 → 唇妆 → 定妆」自动拆
- 不指定语言 → 默认与用户对话语言一致

## 变体 1：3×3 = 9 步竖版手册（4:5 / 9:16）

📝 提示词

```json
{
  "type": "9-step process manual board, vertical poster",
  "layout": { "rows": 3, "columns": 3, "panel_count": 9, "aspect_ratio": "4:5 or 9:16 vertical" },
  "use_case": "更细致的步骤手册 / 小红书 / 公众号竖版图文 / 教程封面"
}
```

### 何时选这个变体

- 步骤多于 6（例如详细 9 步教程）
- 需要竖版（社交媒体 / 手机端阅读）
- 教程类内容

## 变体 2：2×4 = 8 步横版（适合训练分解 / 武术拆招）

📝 提示词

```json
{
  "type": "8-step technical breakdown board, horizontal banner",
  "layout": { "rows": 2, "columns": 4, "panel_count": 8, "aspect_ratio": "16:9 ultra-wide" },
  "use_case": "武术拆招 / 健身动作分解 / 舞蹈技术 / 体操"
}
```

### 何时选这个变体

- 横向叙事更自然（左 → 右一招一式）
- 步骤数量为 8
- 需要更大显示宽度

## 变体 3：4 步极简流程（适合简单装备 / 入门教程）

📝 提示词

```json
{
  "type": "4-step minimal process board",
  "layout": { "rows": 2, "columns": 2, "panel_count": 4, "aspect_ratio": "1:1" },
  "use_case": "极简入门教程 / 简单装备 / 4 步完成的简短流程"
}
```

### 何时选这个变体

- 流程只有 4 步
- 1:1 适合 Instagram / 小红书封面
- 想要简洁干净

## 变体 4：摄影时尚大片质感（非特摄风）

📝 提示词

```json
{
  "type": "fashion editorial multi-step lookbook board",
  "style_override": {
    "rendering": "high-end fashion photography, soft beauty light, magazine editorial spread",
    "lighting": "softbox key light + rim light, clean shadow",
    "background": "seamless studio backdrop or minimal location"
  },
  "use_case": "服装搭配步骤 / 化妆教程 / 时尚 lookbook"
}
```

### 何时选这个变体

- 需要时尚大片美感
- 主题是服装 / 化妆 / 美容
- 不需要 sci-fi / 工业感

## 避免事项

- ❌ 角色外观在不同 panel 漂移（**必须强调 character consistency**）
- ❌ 装备状态非递进（必须按步骤显式叠加）
- ❌ 缺少编号 / 标题 / 说明
- ❌ 把流程板做成姿势字典（用 `pose-reference-sheet.md`）
- ❌ 把流程板做成漫画 / 加对话气泡
- ❌ 环境 / 灯光 / 滤镜在不同 panel 风格不一致
- ❌ 让模型自由生成步骤（必须显式列出每步标题 + 说明 + 镜头描述）
- ❌ 在面部不打码 / 不模糊的情况下生成真人 lookalike 照片（**遵守身份隐私约束**）
