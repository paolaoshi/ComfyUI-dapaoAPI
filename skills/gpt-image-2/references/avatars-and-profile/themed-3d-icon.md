# 主题 3D 图标头像模板

本文件用于"3D 卡通 / Q 萌图标级别"的头像视觉：

- Kawaii 3D 角色图标
- Minecraft 风皮肤渲染
- 拟物 3D 头像
- 应用图标式头像
- 周边贴纸 / 周边小角色

特征：

- 3D 渲染感
- Q 萌、可爱、强主题感
- 单图 / 单角色
- 圆角方形 / 圆形构图
- 适合社交平台头像 / 应用图标

## 适用范围

- 圆角方形 / 圆形头像
- 应用图标
- 周边小角色形象
- 卡通版本的"我"

## 何时使用

- 用户希望 3D 卡通版本的角色或自己
- 用户希望像 Pixar / Kawaii / Q 萌的角色头像
- 用户希望角色作为 IP 的图标级出场

不要使用：

- 写实风格自拍（用 `style-transfer-selfie.md`）
- 多版本网格（用 `character-grid-portrait.md`）
- 角色完整设定稿（用 `portraits-and-characters/character-sheet.md`）

## 缺失信息优先提问顺序

1. 主题（猫咪 / 角色 / 自己 / 兴趣爱好）
2. 风格基底（Kawaii Q 萌 / Pixar 写实卡通 / Minecraft 像素 3D / 拟物 3D）
3. 配色 / 主色
4. 配件 / 道具（眼镜 / 帽子 / 手中物）
5. 构图：胸像 / 全身 / 头像
6. 输出形态：圆形 / 圆角方形 / 透明背景

## 主模板：Kawaii 3D 角色图标

📖 描述

整体一张 1:1 头像图，主体为 Q 萌 3D 角色，圆角方形构图，背景纯色。

📝 提示词

```json
{
  "type": "Kawaii 3D 角色图标",
  "goal": "生成一张可作为社交平台头像 / 应用图标 / 周边小角色的 3D Q 萌角色图",
  "character": {
    "subject": "{argument name=\"character subject\" default=\"圆乎乎的橘色小柴犬\"}",
    "personality": "{argument name=\"personality\" default=\"开心、机灵\"}",
    "expression": "{argument name=\"expression\" default=\"微笑 + 张嘴吐舌头\"}",
    "pose": "{argument name=\"pose\" default=\"正面胸像，看向镜头\"}",
    "outfit_or_accessory": [
      "{argument name=\"item 1\" default=\"红色小领结\"}",
      "{argument name=\"item 2\" default=\"挂着小铃铛\"}"
    ]
  },
  "style": {
    "rendering": "{argument name=\"rendering\" default=\"3D Pixar 风 + 微微 toon shading\"}",
    "color_palette": "{argument name=\"color palette\" default=\"暖橙 + 奶油白\"}",
    "lighting": "{argument name=\"lighting\" default=\"柔光 + 微微背光\"}"
  },
  "background": {
    "type": "{argument name=\"background\" default=\"奶油黄纯色 + 极淡光晕\"}"
  },
  "format": {
    "shape": "{argument name=\"shape\" default=\"圆角方形\"}",
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"1:1\"}",
    "composition_safety": "主体留 10% 边距，避免被裁切"
  },
  "constraints": {
    "must_keep": [
      "整体 Q 萌可爱",
      "主体居中明确",
      "配色 ≤ 3 种",
      "细节克制（不要塞太多元素）"
    ],
    "avoid": [
      "写实风格混入",
      "颜色饱和到刺眼",
      "背景干扰主体",
      "配件遮挡角色脸部"
    ]
  }
}
```

### 参数策略

- 必问：角色主题、表情
- 可默认：风格、配色、背景、形态
- 可随机：配件具体造型

### 自动补全策略

- 用户给主体（柴犬 / 猫 / 自己 / 兴趣）时：自动选 Q 萌风格 + 暖色 + 圆角方形
- 配件默认 1-2 件
- 比例默认 1:1

## 变体 1：Minecraft 风皮肤渲染

📝 提示词

```json
{
  "type": "Minecraft 风个性化皮肤渲染",
  "character": {
    "subject": "{argument name=\"character\" default=\"基于参考图本人风格化的 minecraft 角色\"}",
    "outfit": "{argument name=\"outfit\" default=\"蓝色 T 恤 + 牛仔裤 + 红色背包\"}"
  },
  "style": {
    "rendering": "Minecraft 体素 3D 风，方块化身体，像素材质",
    "color_palette": "Minecraft 标准色 16 阶"
  },
  "background": {
    "type": "Minecraft 草地方块场景"
  },
  "constraints": {
    "must_feel": "可识别是 Minecraft 风且像 ta 自己"
  }
}
```

## 变体 2：拟物 3D 应用图标

📝 提示词

```json
{
  "type": "拟物 3D 应用图标式头像",
  "character": {
    "subject": "{argument name=\"theme\" default=\"摄影爱好者\"}",
    "metaphor_object": "{argument name=\"object\" default=\"3D 立体相机 + 微微反光\"}"
  },
  "style": {
    "rendering": "拟物 3D + 软光 + 厚阴影",
    "color_palette": "Apple Big Sur 风格"
  },
  "background": {
    "type": "圆角方形浅灰渐变"
  },
  "constraints": {
    "must_feel": "像一个真实可点击的 app 图标"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "3D 图标头像自动补全",
  "mode": "auto-fill",
  "rule": "用户给一个主题（兴趣 / 性格 / 喜好）即可，自动决定主体形象、风格、配色、形态",
  "constraints": {
    "must_feel": "可直接换头像"
  }
}
```

## 避免事项

- 不要让 3D 角色看起来"半真半假"（要么 Q 萌要么拟物，不要两者都不像）
- 不要让背景花哨到压主体
- 不要让头像里出现可读的英文标签 / 文字
- 不要让配件遮挡脸部
- 不要让单个图标里塞 > 2 个角色
