# 姿势 / 动作参考表 N×N 模板

本文件用于生成"同一个人物 / 角色，在 N×N 网格中以不同姿势 / 动作 / 战斗 / 舞蹈 pose 出现"的纯参考表 / 动作字典。

典型用途：

- 舞蹈 / hip-hop / 战斗 pose 编舞参考
- 角色动画师 / 漫画家 pose 速查表
- 健身 / 瑜伽 / 武术姿势字典
- 时尚拍照 pose 灵感库
- 游戏角色动作参考表
- AI 视频 / 后续生成的 pose 控制参考集

特征（与现有 portraits 模板的区别）：

| 模板 | 重点 |
|---|---|
| `character-sheet.md`（已有） | 一个角色的"完整设定"（三视图 + 表情 + 服装 + 配饰）|
| `avatars-and-profile/character-grid-portrait.md`（已有） | n×n 角色网格（多职业 / 多朝代肖像）|
| **本模板**（新增） | **同角色 N 个不同姿势 / 动作 / 舞蹈 pose 的纯动作字典** |

**核心区别**：本模板不变服装、不换角色、不换风格，只变姿势——每格的差异完全在 body language 上。

## 适用范围

- 4×4 / 4×5 / 5×5 姿势速查表
- 舞蹈 / 战斗 / 健身 / 时尚 pose 字典
- 动画师 / 漫画家 / 教练参考
- AI pose control 数据集源图

## 何时使用

- 用户提到"姿势参考 / pose sheet / 动作参考表 / 编舞 / 健身 / 战斗动作"
- 想要 N 个不同姿势的同一角色
- 用作教学 / 参考 / 后续生成的输入

不要使用：

- 角色完整设定（三视图 + 表情 + 服装）→ 用 `character-sheet.md`
- 多职业 / 多朝代肖像 → 用 `avatars-and-profile/character-grid-portrait.md`
- 漫画分镜 / 故事 → 用 `storyboards-and-sequences/four-panel-comic.md`
- 真实摄影分镜（带产品 / 商业广告）→ 用 `storyboards-and-sequences/product-tvc-storyboard.md`

## 缺失信息优先提问顺序

1. 姿势数量（默认 16，常见 9 / 12 / 16 / 20 / 25）
2. 角色性别 + 体型 + 发型 + 服装（**必须固定，所有 panel 共用**）
3. 渲染风格（**写实摄影 / 灰度 3D 雕塑 / 动漫线稿 / 极简扁平**）
4. 姿势主题（**hip-hop / 战斗 / 时尚 / 瑜伽 / 健身 / 通用动作**）
5. 是否需要每格编号 / 标注 / 方向箭头
6. 背景（默认 seamless 白）+ 灯光（默认柔和影棚）
7. 比例（默认 1:1 contact sheet / 16:9 横版）

## 主模板：4×4 = 16 格姿势参考表（写实摄影风）

📖 描述

清洁影棚 contact sheet，无背景，全身入框，每格姿势独立但角色 / 服装 / 镜头距离严格一致。

📝 提示词

```json
{
  "type": "pose reference sheet",
  "goal": "生成一张同一角色 N 个不同姿势的纯动作参考表，可用于编舞 / 动画 / 健身 / AI pose 控制参考",
  "subject": {
    "theme": "{argument name=\"pose theme\" default=\"hip-hop dance and combat-ready movement chart\"}",
    "character": {
      "count": 1,
      "gender_presentation": "{argument name=\"gender\" default=\"female\"}",
      "age_appearance": "{argument name=\"age\" default=\"young adult\"}",
      "body_type": "{argument name=\"body type\" default=\"fit athletic dancer\"}",
      "skin_tone": "{argument name=\"skin tone\" default=\"light tan\"}",
      "hair": {
        "color": "{argument name=\"hair color\" default=\"black\"}",
        "style": "{argument name=\"hair style\" default=\"high ponytail with loose strands\"}"
      },
      "outfit": {
        "count": 5,
        "items": [
          "{argument name=\"outfit top\" default=\"white sports bra or cropped athletic top\"}",
          "{argument name=\"outfit bottom\" default=\"baggy purple jogger pants\"}",
          "{argument name=\"outfit shoes\" default=\"white chunky sneakers\"}",
          "{argument name=\"outfit accessory 1\" default=\"purple wristbands or forearm bands on both arms\"}",
          "{argument name=\"outfit accessory 2\" default=\"small hoop earrings\"}"
        ]
      }
    }
  },
  "style": {
    "image_type": "{argument name=\"render style\" default=\"photorealistic studio pose sheet\"}",
    "lighting": "{argument name=\"lighting\" default=\"clean even studio lighting\"}",
    "background": "{argument name=\"background\" default=\"plain light gray to white seamless backdrop\"}",
    "camera": "{argument name=\"camera\" default=\"full-body framing, straight-on view, consistent distance\"}",
    "rendering": "{argument name=\"rendering\" default=\"sharp realistic anatomy, dynamic motion, slight shadow under feet\"}",
    "face": "{argument name=\"face treatment\" default=\"intentionally blurred or obscured\"}"
  },
  "layout": {
    "grid": {
      "rows": "{argument name=\"rows\" default=\"4\"}",
      "columns": "{argument name=\"columns\" default=\"4\"}",
      "count": "{argument name=\"panel count\" default=\"16\"}"
    },
    "numbering": {
      "count": "{argument name=\"panel count\" default=\"16\"}",
      "labels": ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16"],
      "position": "top-left corner of each cell"
    },
    "cell_borders": "thin black divider lines between all panels",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"1:1\"}"
  },
  "poses": {
    "count": 16,
    "items": [
      { "label": "1", "description": "{argument name=\"pose 1\" default=\"wide low squat, knees bent outward, torso angled slightly left, both arms extended loosely in a defensive dance stance\"}" },
      { "label": "2", "description": "{argument name=\"pose 2\" default=\"deep side lunge to the left, left arm pointing straight left, right hand near the head, energetic directional pose\"}" },
      { "label": "3", "description": "{argument name=\"pose 3\" default=\"low crouch with one hand touching the floor, one knee bent under the body, opposite arm extended horizontally\"}" },
      { "label": "4", "description": "{argument name=\"pose 4\" default=\"upright one-leg balance, left knee lifted high, both arms spread outward for rhythm and balance\"}" },
      { "label": "5", "description": "{argument name=\"pose 5\" default=\"similar one-leg raised pose with the other leg supporting, arms stretched outward in a lighter dance variation\"}" },
      { "label": "6", "description": "{argument name=\"pose 6\" default=\"very wide grounded squat, torso pitched forward, one hand reaching toward the floor between the legs, other arm extended back\"}" },
      { "label": "7", "description": "{argument name=\"pose 7\" default=\"dramatic standing back arch, chest lifted upward, hips forward, both arms opened behind and to the sides\"}" },
      { "label": "8", "description": "{argument name=\"pose 8\" default=\"small jump or suspended squat, both feet off the floor, knees bent, arms spread wide symmetrically\"}" },
      { "label": "9", "description": "{argument name=\"pose 9\" default=\"floor-supported seated lean, one hand planted behind, one arm reaching diagonally upward, legs bent to one side\"}" },
      { "label": "10", "description": "{argument name=\"pose 10\" default=\"front-facing balance with one knee raised to hip height, one arm bent in guard position and the other extended sideways\"}" },
      { "label": "11", "description": "{argument name=\"pose 11\" default=\"deep lateral stance, feet far apart, knees bent, both hands raised open near shoulder level like a ready combat pose\"}" },
      { "label": "12", "description": "{argument name=\"pose 12\" default=\"low side lunge split, one hand planted on the floor, the other arm reaching vertically overhead, torso arched upward\"}" },
      { "label": "13", "description": "{argument name=\"pose 13\" default=\"standing backward lean with relaxed bent knees, chest up, arms hanging loosely behind in a groove pose\"}" },
      { "label": "14", "description": "{argument name=\"pose 14\" default=\"compact twisting crouch, weight low over bent legs, torso rotated, one arm pulled in and the other extended outward\"}" },
      { "label": "15", "description": "{argument name=\"pose 15\" default=\"very wide side lunge stretch, one hand to the floor near the front foot, opposite arm reaching diagonally overhead\"}" },
      { "label": "16", "description": "{argument name=\"pose 16\" default=\"one-leg lifted pose with knee high, one hand behind the head and the other arm extended forward, confident finishing stance\"}" }
    ]
  },
  "composition": "show the same person in all 16 panels with consistent outfit and scale, centered within each frame, designed like a movement library or choreography reference chart",
  "constraints": {
    "must_keep": [
      "16 panel 中的角色完全一致（脸 / 体型 / 发型 / 服装 / 鞋）",
      "每格全身入框，镜头距离一致",
      "每格姿势必须可识别且差异明显",
      "每格左上角编号 1-16 清晰",
      "身体比例正确（无肢体扭曲）"
    ],
    "avoid": [
      "16 个姿势都是站立 → 必须混合 squat / lunge / floor / jump / arabesque",
      "服装 / 配饰在不同 panel 改变",
      "全身入框被裁掉头或脚",
      "肢体扭曲 / 多手 / 多脚",
      "脸部表情过度抢戏（应该看姿势而不是表情）"
    ]
  }
}
```

### 参数策略

- **必问**：pose count、character description（性别 + 体型 + 发型 + 服装）、render style
- **可默认**：pose 1-16 具体描述（按 theme 自动生成多样化姿势）
- **可随机**：face treatment、shadow direction

### 自动补全策略

- 用户只说"舞蹈 pose 16 格" → 用模板默认 16 姿势组合（已混合 squat / lunge / floor / balance / jump / backbend）
- 用户给出 theme（hip-hop / 战斗 / 时尚） → 自动调整 pose 描述风格
- 用户给参考人物 → 把 character 字段全部用参考图细节填充

## 变体 1：4×4 灰度 3D 雕塑风（带方向箭头）

适合 Korean 舞蹈编舞 / 战斗动作教学，源自 Case 130 风格。

📝 提示词

```text
[STYLE]
monochromatic grayscale illustration, 3D rendered character, clean instructional reference sheet,
white background, comic-style cell grid layout, technical diagram aesthetic

[LAYOUT]
4x4 grid layout, 16 panels total, each panel separated by thin black border lines,
numbered cells from 1 to 16, consistent panel size

[CHARACTER]
{argument name="character" default="young female dancer, athletic build, ponytail hairstyle, crop top and baggy pants, sneakers"}, same character in all panels

[PANEL STRUCTURE - per cell]
top-left: bold number badge + {argument name="title" default="Korean title text"}
center: full-body character pose illustration
bottom-left: {argument name="description" default="Korean description text (3-4 lines)"}
overlay: directional arrows indicating movement direction

[ARROWS / MOTION INDICATORS]
curved arrows, straight arrows, circular rotation indicators,
placed around the character to show movement flow and direction

[RENDERING STYLE]
high detail 3D sculpt style, soft studio lighting, subtle shadows,
no color, grayscale shading, clean linework, game concept art quality

[NEGATIVE]
no background scenery, no color tones, no extra characters,
no cluttered backgrounds
```

### 何时选这个变体

- 想要"教学手册感"
- 需要明确的方向箭头
- 灰度 3D 雕塑感（不是写实摄影）

## 变体 2：5×5 = 25 格大型动作字典

📝 提示词

```json
{
  "type": "expanded pose reference sheet 25-panel",
  "layout": { "rows": 5, "columns": 5, "count": 25 },
  "must_keep": ["每格的细节会变小，但姿势仍可识别", "适合 contact sheet / 16:10 横屏"],
  "use_case": "动画师 / 编舞 / pose AI 数据集"
}
```

### 何时选这个变体

- 需要更多 pose 样本
- 接受单格细节降低
- 适合作为 dataset / library

## 变体 3：3×3 = 9 格精修 hero pose 集（每格细节更高）

📝 提示词

```json
{
  "type": "hero pose collection 9-panel",
  "layout": { "rows": 3, "columns": 3, "count": 9 },
  "rendering_quality_per_panel": "increase detail since fewer panels",
  "use_case": "时尚拍照 pose 灵感 / 模特参考 / 海报 hero pose 库"
}
```

### 何时选这个变体

- 用作时尚 / 模特拍摄 pose 灵感
- 每格需要更高完成度
- 不追求姿势数量

## 避免事项

- ❌ 16 panel 中角色服装漂移 → 致命错误
- ❌ 16 个姿势全是站立或全是 squat → 缺乏动作多样性
- ❌ 编号丢失或乱序
- ❌ 全身入框被裁（头 / 脚）
- ❌ 多手 / 多脚 / 关节扭曲
- ❌ 给写实姿势加抽象背景（应保持 seamless 纯色）
- ❌ 脸部表情过度抢戏（应使用 blurred face / neutral 处理）
- ❌ 把模板里默认的"hip-hop"姿势组合直接用在"瑜伽"主题（应替换 pose 1-16 描述）
- ❌ 让模型自由生成 N 个 pose（必须显式列出每格姿势描述）
