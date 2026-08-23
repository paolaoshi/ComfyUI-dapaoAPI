# 风格化自拍 / 人设转换模板

本文件用于"基于一张参考图（用户自拍 / 公开照），把人物转化成某种特定风格" 的人设视觉：

- Cosplay 自拍风
- 哥特 / 复古胶片 / 街头 / 涂鸦 风格人设
- 偶像写真 / 拍立得风
- 户外活动情境照（漫展、篮球场、咖啡店）
- 名人 / 角色风格转换

特征：

- 必须基于参考图（REFERENCE_0）保留五官身份
- 仅修改风格 / 妆 / 服装 / 场景气氛
- 单图输出（不是网格 / 不是 sheet）
- 输出更像"你的另一个版本"

## 适用范围

- 把自拍转为某种角色 / 风格
- 一键 cosplay 任意角色
- 改妆容 + 服装 + 场景气氛同步切换

## 何时使用

- 用户提供一张自拍，希望转风格
- 用户描述自己 + 想要的风格，让我们生成
- 用户希望"我的样子但是 X 风格"

不要使用：

- 多版本网格（用 `character-grid-portrait.md`）
- 标准职业头像（用 `portraits-and-characters/professional-portrait.md`）
- 创始人大片（用 `portraits-and-characters/founder-portrait.md`）
- VTuber / 二次元角色（用 `portraits-and-characters/virtual-host.md`）

## 缺失信息优先提问顺序

1. 是否提供参考图（REFERENCE_0）？没有的话需要文字描述本人
2. 想要的风格主题（cosplay / 哥特 / 胶片 / 街头 / 偶像 / 名人风）
3. 服装 / 妆容 / 发型变化范围
4. 场景背景（保留原图 / 新场景）
5. 比例

## 主模板：风格转换自拍（基于 REFERENCE_0）

📖 描述

保留参考图人物身份与基本姿势，将整体风格切换到指定主题。

📝 提示词

```text
基于 REFERENCE_0 中的人物，保留其脸型、五官比例、肤色与基本姿势，将整体风格转换为 {argument name="target style" default="trad goth 哥特风"}：
- 头发：{argument name="hair description" default="黑色短发 + 厚重齐刘海"}
- 妆容：{argument name="makeup description" default="深色烟熏眼妆 + 黑色哑光唇"}
- 服装：{argument name="outfit description" default="黑色皮质上衣 + 银色十字项链 + 多层叠戴"}
- 配饰：{argument name="accessories" default="鼻环、耳钉 2 个、银戒指"}
- 场景：{argument name="scene description" default="保留原图背景"}
- 灯光：{argument name="lighting" default="戏剧性侧光，对比度高"}

输出风格：{argument name="rendering" default="高分辨率写实摄影"}，单张人像图。

约束：
- 不要修改人物身份（脸型、五官比例必须可识别）
- 不要修改性别、年龄段、种族
- 妆容浓但不假，肌肤保留质感
- 服装风格统一不混搭
```

### 参数策略

- 必问：参考图、目标风格
- 可默认：发型、妆容、服装、配饰
- 可随机：背景细节、配饰具体造型

### 自动补全策略

- 用户只给一个风格关键词时：自动展开发型 + 妆 + 服装 + 配饰四件套
- 没有参考图时，要求用户先提供，或退化为纯文本描述
- 默认保留原图背景，除非风格强烈要求换景

## 变体 1：Cosplay 自拍（漫展 / 角色扮演）

📝 提示词

```text
基于 REFERENCE_0 中的人物（如无参考图，则按 {argument name="subject self description" default="东亚年轻女性，自然微笑"} 描述），将其转换为 {argument name="character" default="原神 雷电将军"} 的 cosplay 自拍照，
拍摄场景：{argument name="event location" default="上海漫展现场"}；
保留人物本人五官特征，让人能看出"是 ta 在 cos 这个角色"；
渲染为手机自拍照风格 + 现场氛围 + 自然光。
```

## 变体 2：复古胶片 / Vintage 35mm 闪光人像

📝 提示词

```text
基于 REFERENCE_0 中的人物，将其重新拍摄为 vintage 35mm 闪光胶片人像：
- 闪光灯直射造成的硬阴影
- 颗粒感胶片质感
- 颜色偏 1990s 暖黄
- 场景：{argument name="vintage scene" default="街边台球室"}
- 人物表情自然，不刻意摆拍
保留原图人物身份。
```

## 变体 3：偶像写真 / 拍立得集合（单张拍立得形态）

📝 提示词

```text
基于 REFERENCE_0 中的人物，生成一张拍立得照片：
- 拍立得边框（白色厚边、底部留白手写标签）
- 人物在画面居中
- 风格：{argument name="polaroid mood" default="日系偶像清纯"}
- 拍立得底部手写一句话：'{argument name="caption" default="2026.4.24 weekend"}'
- 整体颗粒感 + 微微过曝
```

## 变体 4：自动补全模式

📝 提示词

```text
基于 REFERENCE_0 中的人物，将其转换为最适合的某种"高级风格化人设"自动决定：
- 自动判断该人物气质适合的风格主题
- 自动展开发型 / 妆容 / 服装 / 场景 / 灯光
- 不修改人物身份特征
- 输出单张图
```

## 避免事项

- 不要修改五官比例（最常见失败：换脸）
- 不要修改性别 / 种族特征
- 不要让妆容浓到变成"滤镜假皮肤"
- 不要把背景换得脱离主题
- 不要在没有参考图时假装是基于参考图（退化为文本描述模式即可）
- 不要使用真实存在的版权角色名直接 cosplay（建议描述特征而非点名）
