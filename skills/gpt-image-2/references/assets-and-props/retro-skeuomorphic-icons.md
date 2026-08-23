# 拟物 / 复古图标集模板

本文件用于"成套图标 / 拟物 / Y2K / 复古"图标视觉：

- 拟物风应用图标集（Skeuomorphic）
- Y2K 风格水晶图标
- 像素 / 复古游戏图标
- 主题图标包（生活 / 工作 / 旅行）
- UI 图标系统

特征：

- 多个图标，统一风格
- 通常 6 / 8 / 12 / 16 个
- 每个图标圆角方形 / 圆形
- 强调材质质感（玻璃 / 金属 / 拟物）
- 适合作为 app 图标包 / icon set

## 适用范围

- 应用图标集
- 主题图标包
- UI 图标系统
- 周边贴纸 / 卡片

## 何时使用

- 用户提到"图标 / icon set / 拟物 / skeuomorphic / Y2K / 像素图标"
- 用户希望成套图标

不要使用：

- 单个 3D 图标头像（用 `avatars-and-profile/themed-3d-icon.md`）
- 贴纸套装（用 `avatars-and-profile/sticker-set.md`）
- 通用品牌识别（用 `branding-and-packaging/brand-identity-board.md`）

## 缺失信息优先提问顺序

1. 风格（拟物 / Y2K / 像素 / Flat / Glass / Clay）
2. 图标主题（应用 / 工作 / 生活 / 旅行）
3. 图标数量（6 / 8 / 12 / 16）
4. 主色 1-2 个
5. 形状基底（圆角方形 / 圆形 / 自由形）
6. 是否带文字标签

## 主模板：拟物风应用图标集

📖 描述

整体一张图，包含 N 个统一风格的拟物图标，以网格排布。

📝 提示词

```json
{
  "type": "拟物风应用图标集",
  "goal": "生成一组成套统一风格的图标，可作为 icon pack / 主题包",
  "theme": "{argument name=\"theme\" default=\"经典办公应用\"}",
  "style": {
    "rendering": "{argument name=\"rendering\" default=\"拟物 3D + 软光 + 柔和阴影\"}",
    "material": "{argument name=\"material\" default=\"玻璃质感 + 微微反光\"}",
    "color_palette": "{argument name=\"color palette\" default=\"米白 + 暖橙 + 浅蓝 + 灰\"}",
    "shape_base": "{argument name=\"shape base\" default=\"圆角方形（24% 圆角）\"}"
  },
  "layout": {
    "grid": "{argument name=\"grid\" default=\"4x3\"}",
    "icon_count": "{argument name=\"icon count\" default=\"12\"}",
    "spacing": "16px",
    "background": "{argument name=\"background\" default=\"米色纸纹\"}",
    "label_below": "{argument name=\"label below\" default=\"true\"}",
    "label_style": "细灰色无衬线小字"
  },
  "icons": [
    {"id": 1, "concept": "{argument name=\"icon 1\" default=\"邮件 - 信封 + 发光指示\"}", "label": "Mail"},
    {"id": 2, "concept": "{argument name=\"icon 2\" default=\"日历 - 翻开页面 + 红色今日标记\"}", "label": "Calendar"},
    {"id": 3, "concept": "{argument name=\"icon 3\" default=\"备忘录 - 黄色便签 + 红色书签\"}", "label": "Notes"},
    {"id": 4, "concept": "{argument name=\"icon 4\" default=\"相机 - 复古胶片机\"}", "label": "Camera"},
    {"id": 5, "concept": "{argument name=\"icon 5\" default=\"音乐 - 黑胶唱片\"}", "label": "Music"},
    {"id": 6, "concept": "{argument name=\"icon 6\" default=\"地图 - 折叠地图 + 红针\"}", "label": "Maps"},
    {"id": 7, "concept": "{argument name=\"icon 7\" default=\"天气 - 太阳 + 云\"}", "label": "Weather"},
    {"id": 8, "concept": "{argument name=\"icon 8\" default=\"计算器 - 数字按键\"}", "label": "Calc"},
    {"id": 9, "concept": "{argument name=\"icon 9\" default=\"时钟 - 圆形表盘\"}", "label": "Clock"},
    {"id": 10, "concept": "{argument name=\"icon 10\" default=\"设置 - 齿轮\"}", "label": "Settings"},
    {"id": 11, "concept": "{argument name=\"icon 11\" default=\"健康 - 心形脉搏线\"}", "label": "Health"},
    {"id": 12, "concept": "{argument name=\"icon 12\" default=\"钱包 - 棕色皮夹\"}", "label": "Wallet"}
  ],
  "constraints": {
    "must_keep": [
      "12 个图标风格严格统一（同样光源、同样圆角、同样厚度）",
      "色板 ≤ 6 色",
      "label 字体一致",
      "每个图标可单独识别"
    ],
    "avoid": [
      "图标风格漂移（有些拟物有些扁平）",
      "颜色超过 6 种",
      "图标内部细节过密",
      "label 错字"
    ]
  }
}
```

### 参数策略

- 必问：主题、数量、风格
- 可默认：layout、配色、形状基底
- 可随机：每个图标具体设计

### 自动补全策略

- 用户给主题 + 数量时：自动展开每个图标具体形象
- 默认 4×3 = 12 个
- 默认拟物 3D + 玻璃质感

## 变体 1：Y2K 水晶图标包

📝 提示词

```json
{
  "type": "Y2K 水晶图标包",
  "style": {
    "material": "透明水晶 + 折射光",
    "color_palette": "高饱和粉 + 蓝紫 + 银"
  },
  "constraints": {
    "must_feel": "Y2K Aero 风"
  }
}
```

## 变体 2：像素复古游戏图标

📝 提示词

```json
{
  "type": "像素复古游戏图标",
  "style": {
    "rendering": "16-bit 像素 + 锐利边缘",
    "color_palette": "16 色复古游戏调色板"
  },
  "constraints": {
    "must_feel": "FC / SNES 时代"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "图标包自动补全",
  "mode": "auto-fill",
  "rule": "用户给主题，自动决定图标数量、风格、配色、layout",
  "constraints": {
    "must_feel": "可作为 icon pack 上架"
  }
}
```

## 避免事项

- 不要让图标风格漂移
- 不要让色板 > 6
- 不要让 label 字体超过 1 种
- 不要让单个图标内部塞 > 3 元素
- 不要让网格大小不一致
- 不要让 icon 与 background 对比度不够
