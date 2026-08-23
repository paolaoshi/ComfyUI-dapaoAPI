# 电影感叙事分镜 contact sheet 模板

本文件用于生成"以一段连续叙事 / 情绪 / 事件序列为主线，按 N×M 网格输出 9-15 个 cinematic still"的电影分镜板。

典型用途：

- 短片 / 概念片 / pitch trailer 的视觉提案
- AI 视频生成（Sora / Runway / Pika）的镜头列表参考
- 漫画 / 动画 / 游戏 cinematic cut scene 提案
- 影视投资 deck 的概念视觉
- 「这段故事拍出来会长什么样」一图答案
- sci-fi / 战斗 / 灾难 / 浪漫 / 悬疑 任意题材

特征（与现有 storyboards 模板的区别）：

| 模板 | 性质 |
|---|---|
| `four-panel-comic.md`（已有） | 漫画 4 格 / 段子 / 反转 |
| `manga-spread-page.md`（已有） | 漫画跨页（不规则格） |
| `recipe-process-flowchart.md`（已有） | 流程示意（食谱 / 教程） |
| `product-tvc-storyboard.md`（新增） | **商业广告 TVC 分镜（产品中心）** |
| **本模板**（新增） | **电影 / 短片 / 概念片 叙事分镜**（事件 / 情绪 / 故事中心） |

**核心区别**：本模板每个 panel 都是「电影级 cinematic still」，不强调产品 / 商业，而强调「这一秒发生了什么 + 镜头如何拍 + 情绪是什么」。

## 适用范围

- 电影 / 短片 / 动画 cinematic 分镜板
- AI 视频镜头列表
- pitch trailer 视觉提案
- 概念片 storyboard（sci-fi / 战斗 / 灾难 / 浪漫 / 悬疑）

## 何时使用

- 用户提到"电影分镜 / cinematic storyboard / 短片镜头表 / 概念片镜头列表"
- 主体是事件 / 情绪 / 故事，不是产品 / 商业广告
- 想要「电影感」而非「漫画感」/「广告感」

不要使用：

- 商业广告 TVC 分镜（带产品） → 用 `product-tvc-storyboard.md`
- 漫画分镜（带对话气泡 / 心声） → 用 `four-panel-comic.md` / `manga-spread-page.md`
- 食谱 / 教程流程 → 用 `recipe-process-flowchart.md`
- 真人摄影流程图 / 装备穿戴 → 用 `process-photo-board.md`

## 缺失信息优先提问顺序

1. 故事 / 主线（一段话描述：谁 + 在哪 + 发生什么 + 结局）
2. 题材（**sci-fi / 灾难 / 战斗 / 浪漫 / 悬疑 / 西部 / 黑色电影**）
3. 镜头数量（9 / 12 / 15）+ 网格（3×3 / 3×4 / 3×5 / 4×4）
4. 情绪曲线（**起 → 升 → 高潮 → 落 / 一直紧张 / 一直平静爆发**）
5. 风格（**photoreal / 油画质感 / 动漫电影感 / 黑白电影 / 复古 70s**）
6. 配色基调（决定整组镜头的 color grading）
7. 比例（每格 16:9 / 21:9 电影宽屏；整图 1:1 contact sheet 或 4:5 / 16:9）

## 主模板：3×4 = 12 镜电影感分镜 contact sheet（sci-fi 案例）

📖 描述

12 个独立 cinematic still，连续叙事一个事件（如飞船降落气巨星），每格自成一幅 cinematic 概念图，整体保持 mood / 灯光 / 配色一致。

📝 提示词

```json
{
  "type": "cinematic storyboard contact sheet",
  "goal": "生成一张 12 镜分镜板，每镜都是一幅完整的电影 cinematic still，整组讲述一个连续叙事",
  "subject": {
    "primary": "{argument name=\"primary subject\" default=\"a small futuristic spacecraft descending into a massive gas giant storm system\"}",
    "secondary": "{argument name=\"secondary subject\" default=\"an enormous leviathan-like silhouette hidden within the clouds\"}",
    "mood": "{argument name=\"mood\" default=\"oppressive, catastrophic, awe-struck, high tension, cosmic dread\"}",
    "style": "{argument name=\"cinematic style\" default=\"photorealistic cinematic concept art with dark sci-fi realism, volumetric storm clouds, strong contrast, amber and black palette with occasional cold blue lightning\"}",
    "aspect_ratio_per_panel": "{argument name=\"per-panel ratio\" default=\"16:9\"}"
  },
  "vehicle_or_actor": {
    "design": "{argument name=\"hero design\" default=\"compact armored deep-atmosphere ship with 3 bright rear engines, angular industrial hull, worn metallic panels\"}",
    "scale": "{argument name=\"scale relation\" default=\"tiny compared to the planet and creature\"}"
  },
  "layout": {
    "grid": {
      "rows": "{argument name=\"rows\" default=\"3\"}",
      "columns": "{argument name=\"columns\" default=\"4\"}",
      "count": "{argument name=\"panel count\" default=\"12\"}"
    },
    "sheet_aspect_ratio": "{argument name=\"sheet ratio\" default=\"16:9 contact sheet\"}",
    "panel_borders": "thin white dividers, generous gutter",
    "sections": [
      { "position": "row 1 col 1", "description": "{argument name=\"shot 1\" default=\"wide exterior shot of the ship entering the upper atmosphere of a colossal gas giant at extreme speed, glowing clouds streaked with fire and friction around the vessel, curved planetary horizon visible\"}" },
      { "position": "row 1 col 2", "description": "{argument name=\"shot 2\" default=\"cockpit POV, dark interior filled with red and cyan holographic instruments, forward visibility collapsing into turbulent storm layers and electrical haze\"}" },
      { "position": "row 1 col 3", "description": "{argument name=\"shot 3\" default=\"exterior mid-wide shot of the ship diving into a gigantic rotating cloud funnel, surrounded by violent spiraling storm structure\"}" },
      { "position": "row 1 col 4", "description": "{argument name=\"shot 4\" default=\"extreme close exterior of the ship hull as bright lightning strikes dangerously close, white electric energy crawling across the metal surface\"}" },
      { "position": "row 2 col 1", "description": "{argument name=\"shot 5\" default=\"dashboard warning screen in red, showing a critical systems failure interface with 4 warning lines and 1 large percentage readout: WARNING / ENGINES COMPROMISED / THRUST FLUCTUATION / GRAVITY SPIKE DETECTED / DESCENT RATE -453%\"}" },
      { "position": "row 2 col 2", "description": "{argument name=\"shot 6\" default=\"rear three-quarter exterior of the ship fighting turbulence inside dense storm clouds, engines burning hard while the craft barely holds course\"}" },
      { "position": "row 2 col 3", "description": "{argument name=\"shot 7\" default=\"massive circular disturbance forming in the clouds like an eye or maw, entire storm systems displaced by something huge moving beneath\"}" },
      { "position": "row 2 col 4", "description": "{argument name=\"shot 8\" default=\"second cockpit view with radar-like navigation display and red alert text, pilot making a blind evasive maneuver through lightning-filled darkness\"}" },
      { "position": "row 3 col 1", "description": "{argument name=\"shot 9\" default=\"first reveal of the colossal creature shape rising near the ship, black organic surface and immense curved anatomy emerging from darkness, ship tiny at lower left\"}" },
      { "position": "row 3 col 2", "description": "{argument name=\"shot 10\" default=\"spiral descent shot, ship caught inside a vortex tunnel of clouds, spinning downward with engines flaring as it struggles to recover\"}" },
      { "position": "row 3 col 3", "description": "{argument name=\"shot 11\" default=\"sudden breakthrough into a calm void, minimal composition, ship flying in eerie silence through dark open space with soft mist and no visible storm around it\"}" },
      { "position": "row 3 col 4", "description": "{argument name=\"shot 12\" default=\"final reveal, gigantic leviathan fully emerging behind or beside the ship in cleared space, backlit by a pale circular storm opening, enormous open maw-like silhouette dwarfing the craft\"}" }
    ],
    "continuity": "all 12 panels depict one continuous narrative sequence with consistent hero design, color grading, and mood arc"
  },
  "lighting": {
    "primary": "{argument name=\"primary light\" default=\"glowing amber storm light\"}",
    "secondary": "{argument name=\"secondary light\" default=\"red cockpit interface glow\"}",
    "accents": "{argument name=\"accent light\" default=\"blue-white lightning and engine exhaust\"}"
  },
  "environment": {
    "location": "{argument name=\"location\" default=\"inside the upper and middle storm layers of a gigantic gas giant\"}",
    "weather": "{argument name=\"weather\" default=\"violent turbulence, electrical storms, vortex funnels, cloud walls, pressure chaos\"}",
    "threat": "{argument name=\"threat / tension\" default=\"no safe zone, repeated near-failure, unknown colossal presence driving the storm\"}"
  },
  "constraints": {
    "must_keep": [
      "12 panel 必须呈现一段连续叙事（不是 12 张随机图）",
      "hero（飞船 / 角色）外观在所有 panel 中一致",
      "整体 color grading / mood 统一",
      "镜头节奏混合（远景 / 中景 / 特写 / POV / 仰拍 / 俯拍）",
      "至少 1 个 reveal / climax 镜头（如最后一格）"
    ],
    "avoid": [
      "12 panel 全是同一类型镜头（如全特写）",
      "hero 外观漂移",
      "整体 color grading 不一致（一格暖光一格冷光毫无理由）",
      "镜头描述与故事主线脱节",
      "把分镜画成漫画 / 加对话气泡（这是电影 still 不是漫画）"
    ]
  }
}
```

### 参数策略

- **必问**：primary subject、mood、cinematic style、12 个 shot 简述
- **可默认**：lighting、environment、aspect ratio
- **可随机**：每镜的具体角度（按主线自动生成 wide/POV/CU 混搭）

### 自动补全策略

- 用户给一句故事大纲 → 自动拆 12 镜（按 「entry → mid → escalation → climax → reveal」结构）
- 不指定 mood → 按题材自动（sci-fi=oppressive；浪漫=warm；战斗=tense；悬疑=cold）
- 不指定每镜镜头类型 → 自动混搭 4 wide / 4 medium / 2 CU / 2 POV

## 变体 1：3×3 = 9 镜短片节奏（适合 1-2 分钟短片）

📝 提示词

```json
{
  "type": "9-shot short film storyboard",
  "layout": { "rows": 3, "columns": 3, "count": 9 },
  "narrative_arc": ["1 establish", "2-3 inciting", "4-5 escalation", "6 turn", "7-8 climax", "9 resolve / cliffhanger"],
  "use_case": "1-2 分钟短片 / 概念片 / TikTok 长视频"
}
```

### 何时选这个变体

- 故事更短 / 节奏更紧凑
- 不需要 12 镜
- 适合短片 / 短视频提案

## 变体 2：4×4 = 16 镜大型场面（适合战斗 / 灾难 / 长 sequence）

📝 提示词

```json
{
  "type": "16-shot epic sequence storyboard",
  "layout": { "rows": 4, "columns": 4, "count": 16 },
  "narrative_arc_extended": [
    "1-2 setup",
    "3-5 build",
    "6-8 first wave",
    "9 mid-climax",
    "10-12 second wave",
    "13-14 final climax",
    "15-16 aftermath"
  ],
  "use_case": "战斗大场面 / 灾难片 / 史诗 sequence"
}
```

### 何时选这个变体

- 需要更多镜头表现复杂叙事
- 史诗 / 战斗 / 灾难题材
- 接受单格细节降低

## 变体 3：黑白电影 / 复古胶片质感

📝 提示词

```json
{
  "type": "black-and-white noir storyboard contact sheet",
  "style_override": {
    "rendering": "high-contrast black and white film still, deep shadows, grain texture, 1940s noir cinematography",
    "lighting": "venetian blind shadows, hard side light, smoke",
    "framing": "tight closeups, dutch angles, low POV"
  },
  "use_case": "悬疑 / 黑色电影 / 复古犯罪题材"
}
```

### 何时选这个变体

- 黑白 / noir 题材
- 想要复古胶片质感
- 强调光影 / 几何构图

## 避免事项

- ❌ 12 panel 之间故事断裂（必须连续叙事）
- ❌ hero 外观漂移
- ❌ color grading 不一致（一格暖光一格冷光）
- ❌ 全是同类型镜头（必须混合远 / 中 / 近 / POV / 俯仰）
- ❌ 把分镜画成漫画 / 加对话气泡
- ❌ 把广告产品塞进电影分镜（应使用 `product-tvc-storyboard.md`）
- ❌ 最后一格不是 reveal / climax / cliffhanger（电影分镜需要明确的尾镜）
- ❌ 让模型自由生成 12 镜（必须显式列出每镜描述以保证叙事连贯）
