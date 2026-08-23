# 游戏内截图 Mockup 模板

本文件用于"伪造一张游戏内截图"的视觉：

- 开放世界游戏截图
- RPG 战斗截图
- 像素 / 体素游戏截图
- 视觉小说截图
- 游戏 UI mockup

特征：

- 整体看起来"像真实游戏内画面"
- 含游戏 UI（HUD / 任务面板 / 血条 / 小地图）
- 有视角语言（第一人称 / 第三人称 / 俯视 / 等距）
- 强调游戏感而非纯插画
- 通常带文字气泡 / 任务提示

## 适用范围

- 游戏内截图 mockup
- 游戏宣传图（伪截图）
- 游戏立项 demo 视觉
- 直播缩略图（伪游戏画面）

## 何时使用

- 用户提到"游戏截图 / game screenshot / mockup / HUD / UI"
- 用户希望"看起来像游戏画面"而不是插画

不要使用：

- 动漫 KV（用 `storyboards-and-sequences/anime-key-visual.md`）
- 游戏立项 pitch（用 `grids-and-collages/anime-pitch-board.md`）
- 角色设定（用 `portraits-and-characters/character-sheet.md`）

## 缺失信息优先提问顺序

1. 游戏类型（开放世界 / RPG / 像素 / 视觉小说 / 模拟）
2. 视角（第一人称 / 第三人称 / 俯视 / 等距）
3. 场景（户外 / 室内 / 城市 / 战斗）
4. 主角描述（如有）
5. UI 元素（HUD / 血条 / 任务 / 小地图）
6. 比例

## 主模板：开放世界游戏截图

📖 描述

整体一张图，模拟真实游戏内截图，含 HUD UI。

📝 提示词

```json
{
  "type": "开放世界游戏截图",
  "goal": "生成一张看起来像真实游戏内截图的视觉",
  "game_meta": {
    "game_name": "{argument name=\"game name\" default=\"FROZEN FANTASIA\"}",
    "engine_feel": "{argument name=\"engine feel\" default=\"现代 3A 引擎（接近 Unreal 5 渲染）\"}",
    "perspective": "{argument name=\"perspective\" default=\"第三人称越肩\"}"
  },
  "scene": {
    "environment": "{argument name=\"environment\" default=\"雪原 + 远景城堡 + 极光\"}",
    "time_of_day": "{argument name=\"time\" default=\"黄昏\"}",
    "weather": "{argument name=\"weather\" default=\"细雪\"}",
    "lighting": "{argument name=\"lighting\" default=\"冷蓝主光 + 暖金边缘光\"}"
  },
  "character": {
    "description": "{argument name=\"character\" default=\"少女主角，银白长发，背身，正在拔剑\"}",
    "position": "画面下三分之一，背身朝远景"
  },
  "ui_elements": {
    "hud": {
      "enabled": "{argument name=\"hud enabled\" default=\"true\"}",
      "items": [
        "{argument name=\"hud item 1\" default=\"左下：血条 + 蓝条 + 角色头像\"}",
        "{argument name=\"hud item 2\" default=\"右下：技能槽 4 格 + 物品栏\"}",
        "{argument name=\"hud item 3\" default=\"左上：小地图（圆形）+ 当前坐标\"}",
        "{argument name=\"hud item 4\" default=\"右上：任务追踪 - '寻找春之源'\"}"
      ]
    },
    "subtitle": {
      "enabled": "{argument name=\"subtitle enabled\" default=\"true\"}",
      "speaker": "{argument name=\"speaker\" default=\"狐狸伙伴\"}",
      "text": "{argument name=\"subtitle text\" default=\"前面就是冰封峡谷了，要小心\"}"
    },
    "interaction_prompt": {
      "enabled": "{argument name=\"prompt enabled\" default=\"true\"}",
      "text": "{argument name=\"prompt\" default=\"按 [E] 调查\"}"
    }
  },
  "style": {
    "rendering": "{argument name=\"rendering\" default=\"PBR 渲染 + 高动态范围 + 微微胶片噪点\"}",
    "color_palette": "{argument name=\"color palette\" default=\"冰蓝 + 月白 + 暖金\"}"
  },
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"16:9\"}",
  "constraints": {
    "must_keep": [
      "看起来像游戏内截图（有真实 HUD）",
      "HUD 与场景颜色不冲突",
      "字幕字体与 HUD 字体统一",
      "主角与场景比例正确"
    ],
    "avoid": [
      "看起来像静态插画（无 HUD）",
      "HUD 元素塞 > 8 个",
      "UI 风格混杂（像素 + 现代 同框）",
      "字幕过长 / 错字"
    ]
  }
}
```

### 参数策略

- 必问：游戏类型、视角、场景
- 可默认：UI 元素、字幕、配色
- 可随机：环境细节

### 自动补全策略

- 用户给游戏概念时：自动决定视角 / HUD / 字幕
- 默认 16:9
- 默认现代 3A 渲染

## 变体 1：像素游戏截图

📝 提示词

```json
{
  "type": "像素游戏截图",
  "game_meta": {
    "engine_feel": "16-bit JRPG 风（如圣剑传说 3）",
    "perspective": "俯视 / 等距"
  },
  "style": {
    "rendering": "像素艺术 + 16 色调色板",
    "color_palette": "16 色复古 RPG 调色"
  },
  "ui_elements": {
    "hud": {
      "items": ["底部对话框 + 角色立绘"]
    }
  },
  "constraints": {
    "must_feel": "FC / SNES JRPG"
  }
}
```

## 变体 2：视觉小说截图

📝 提示词

```json
{
  "type": "视觉小说截图",
  "game_meta": {
    "engine_feel": "Galgame / Visual Novel",
    "perspective": "第一人称（看角色）"
  },
  "ui_elements": {
    "hud": null,
    "subtitle": {
      "enabled": true,
      "speaker": "{argument name=\"speaker\" default=\"女主角\"}",
      "text": "..."
    }
  },
  "style": {
    "rendering": "anime 半厚涂 + 柔光"
  },
  "constraints": {
    "must_feel": "VN 标准对话场景"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "游戏截图自动补全",
  "mode": "auto-fill",
  "rule": "用户给一句游戏概念，自动决定视角 / 场景 / HUD / 主角",
  "constraints": {
    "must_feel": "可作为 Steam 商店截图"
  }
}
```

## 避免事项

- 不要让 HUD 元素超过 8 个
- 不要让 UI 风格与游戏类型脱节（像素游戏不应有现代毛玻璃 HUD）
- 不要让字幕超过 2 行
- 不要让主角占画面过大压过 HUD
- 不要让"截图"看起来像静态插画（HUD 是关键标识）
- 不要让任务面板出现明显错字 / 乱码
