# 主题系统

每个演示从头到尾跑**一个主题**。我们**不**在章节间翻转明暗 —— 那会
打断视频的视觉连贯性，录屏时看起来像很硬的剪辑。如果想要"暗一点的氛围"
段落，请在**同一调色板内**降对比、收聚光，而不是翻转表面色。

主题 = 一组 CSS 设计 token + 一个 `theme.json` 元数据。

**章节对 token 的消费分两层**：

1. **必须用 token 的**（换主题不破的底线）—— 颜色 + 字体家族
2. **章节自由发挥的**（按内容设计）—— 字号 / 间距 / 动画时长 / 缓动 /
   边框宽度 / 一般圆角 / 字距等都可硬编码

主题**不只管**颜色和字体，但其他维度（hero 数字、分割线、卡片、舞台
装饰）通过 **primitive class**（`.hero-num` / `.rule` / `.card` /
`.stage-frame`）自动接入，章节用 class 即可，不需要手动 `var()`。

主题管的维度：

| 维度                       | 主题怎么管                                                        |
| -------------------------- | ----------------------------------------------------------------- |
| **调色板**                 | shell / surface 阶梯、text 阶梯、accent + 透明度衍生              |
| **字型**                   | 中文 / 英文 / body / 等宽家族 + OpenType 特性集                     |
| **舞台 padding 密度**      | `--stage-pad-x/y` —— 精炼主题 140×100，密集主题 80×60              |
| **圆角性格**               | `--r-card` —— sharp (0) / refined (4) / soft (16) / keynote (32)  |
| **分割线性格**             | `--rule-w` + `--rule-style` —— 细/粗 × 实/虚                       |
| **hero 数字风格**          | `--hero-num-*` —— 编辑级斜体 / 终端等宽 / 粗黑 / 手写              |
| **舞台 / 卡片阴影**        | `--shadow-stage` / `--card-shadow` —— 纸浮 / 偏移实色 / 内阴影     |
| **装饰层**                 | `--surface-pattern*` / `--surface-vignette` / `--text-shadow`     |
| **动效基线**               | `theme.json` 的 `mood` —— 电影感慢 / 弹簧 / 利落 / 安静            |

> **`mood` 不写时长数值**。具体 ms / 缓动由 chapter agent 看 `mood`
> 自己拍板（慢主题别写 200ms 快动画，仅此而已）。

每个主题约 25~35 个 token。完整契约见下方。

---

## 内置主题

23 套主题，每个都有**独立的设计 DNA** —— 不是简单的换色版。挑一个
匹配你主题情绪的，或者作为你自己主题的起点。

### 深色主题

| id                | 性格                                                                                                                                                                                                            |
| ----------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `midnight-press`  | 电影感编辑级深色。暖色 espresso（不是纯黑）+ 火热橙。Instrument Serif italic 英文 vs Noto Serif SC 中文。hero 数字：斜体衬线。慢速电影感节奏（1.6s 揭示）。140×100 padding。只有 vignette，没有颗粒。            |
| `chalk-garden`    | 深石板黑板。Patrick Hand 全场手写，粉笔黄 accent。**2px 虚线 rule** 是签名。film grain（overlay）+ vignette。衬线带 chalk text-shadow。手绘节奏。                                                                |
| `terminal-green`  | 80 年代磷光终端。纯黑 + JetBrains Mono only + 0px 直角。**CRT 扫描线**贴在舞台上。文字带磷光 text-shadow。利落线性动效（180/400/650ms）。hero 数字：等宽带发光。                                                  |
| `blueprint`       | 工程蓝图。深海军蓝 + 绘图青 + IBM Plex Mono。**2px 虚线青色 rule + 60px 制图网格**是签名。hero 数字：等宽青色。等宽配对营造技术 / 蓝图感。                                                                       |
| `dark-botanical`  | 高级感编辑暗底 —— 时尚刊物 / 博物馆图录。近黑 + 暖陶 / 玫粉 / 鎏金叠层。Cormorant italic + IBM Plex Sans。**柔光晕染（blurred light pool）作为签名**。慢速电影感节奏（1.7s）。140×100 padding。              |
| `neon-cyber`      | 赛博朋克未来派。深海军底 + 电光青 + 玫红双霓虹。Clash Display + Satoshi。**青色发光网格 + 双色霓虹描边（cyan + magenta text-shadow）**是签名。snappy 节奏（380/650ms）。                                       |
| `bold-signal`     | hero pitch-deck 暗底。Archivo Black + Space Grotesk。大橙色焦点色卡 + 制表数编号。**对角线深色渐变 + 大字标语**是签名。punchy 节奏（420/680ms）。                                                                |
| `creative-voltage`| 复古朋克创意工作室。饱和电光蓝底 + 霓虹黄强调。Syne + Space Mono。**halftone 网点 + 偏移霓黄阴影**是签名。punchy + 能量节奏（450/720ms）。                                                                       |

### 浅色主题

| id                   | 性格                                                                                                                                                                                                            |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `paper-press`        | midnight-press 的白天孪生兄弟。暖奶油 + 纸纹（multiply blend）。火热橙。hero 数字：斜体编辑级衬线。慢速电影感节奏。140×100 padding。                                                                              |
| `warm-keynote`       | 现代 SaaS keynote。奶油 + 棕褐墨 + 青绿 + Inter。**大圆角（32px）glass slab** 配 backdrop blur。**粗黑 font-black hero 数字**。舞台上 40px 暖色网格。弹簧动效。                                                  |
| `newsroom`           | NYT 报刊。报纸奶油 + 墨黑衬线 + 旗红。Playfair Display + Noto Serif SC。**0 圆角**（报纸不会圆角）。hero 数字：超大斜体显示衬线。安静的印刷节奏。淡纸纹。                                                        |
| `bauhaus-bold`       | 现代主义宣言。米白 + 墨黑 + 原色蓝。Archivo Black + Inter。**0 圆角 + 4px 实色厚边 + 4px 黑色画框包住舞台 + 偏移实色阴影**。hero 数字：font-weight 900 巨字。利落快速动效。无装饰。                              |
| `sunset-zine`        | 独立 risograph zine。暖桃 + riso 洋红 + Fraunces。**虚线剪贴线 + 偏移桃色阴影**。hero 数字：斜体 Fraunces。粗 riso 纸纹。弹簧 overshoot 动效。                                                                  |
| `monochrome-print`   | 安静精炼的印刷杂志 —— Monocle / Wallpaper / MIT Press。米白 + 墨黑衬线 + 墨蓝 accent。Source Serif。**只有 1px 实线发丝、4px 精炼圆角**。hero 数字：斜体 tabular figures。**无装饰** —— 极简纯粹。极静节奏（1.7s 揭示）。 |
| `vintage-editorial`  | 俏皮编辑奶油底。Fraunces italic + Work Sans + 暖陶 accent。**细线几何叠层（圆 + 线 + 点）**是签名。有性格、会说话，像专栏作家。中速带轻微 overshoot。                                                            |
| `pastel-dream`       | 友好柔光。柔粉蓝灰底 + 奶油卡 + 鼠尾草绿。Plus Jakarta Sans。**大圆角（20px）+ 右侧多色 pill 色条**是签名。soft springy（520/820ms）。                                                                          |
| `split-canvas`       | 双拼画布 —— 蜜桃 + 薰衣草 50/50 硬切分。Outfit + 玫红 accent。**屏幕本身就是双色底**，章节自由在哪一侧落内容。playful 中速（480/780ms）。                                                                       |
| `electric-studio`    | 企业电光蓝。净白底 + 单一电光蓝 + Manrope。**贴底 4px 电蓝条**作为签名，B2B / 路演 / 财报场景的清晰自信。punchy 节奏（420/700ms）。                                                                              |
| `indigo-porcelain`   | 靛蓝瓷 —— **靛蓝当墨**（不是 accent，是字色本身）+ 瓷白纸。Playfair Display italic + Noto Serif SC + IBM Plex Sans 正文。学术 / 研究气质，像一本当代思想期刊。无装饰 —— 纯粹。慢速（1.55s）。                       |
| `forest-ink`         | 森林墨 —— **森林绿当墨** + 象牙暖纸。Source Serif 正文 + Playfair Display。旧版《国家地理》感，沉稳、文献感。faint warm grain。慢速（1.65s）。                                                                  |
| `kraft-paper`        | 牛皮纸 —— **深棕当墨** + 牛皮米。Fraunces + Source Serif + 紫铜 accent。老笔记本 / 老信封感。**粗暖纸纹**是签名。慢速 tactile（1.55s）。                                                                       |
| `dune`               | 沙丘 —— **炭褐当墨** + 沙底 + 几乎无 accent（muted clay）。Inter display + Source Serif 正文。**无装饰 + 极宽 padding（140×100）**是签名。建筑手册 / 画廊感。最慢节奏（1.75s）。                                |
| `swiss-ikb`          | 瑞士国际主义。**极细 200 weight Inter / Helvetica** + 净暖白底 + IKB 克莱因蓝 + **1px 发丝网格 (64px)**。`r-card: 0` 直角。Massimo Vignelli / Helvetica Forever 能量。punchy + linear（400/650ms）。           |


随时列出可用主题：

```bash
bash <path-to-web-video-presentation>/scripts/scaffold.sh --list-themes
```

---

## 脚手架时挑一个主题

```bash
# 默认（midnight-press）
bash scripts/scaffold.sh ./presentation

# 显式指定
bash scripts/scaffold.sh ./talk --theme=newsroom
```

脚手架会把所选主题的 `tokens.css` 拷到 `<project>/src/styles/tokens.css`，
并把主题 id 写到 `<project>/.theme`，方便以后看是从哪个主题开始的。

---

## 之后切换主题

切换 = 一次文件覆盖：

```bash
cp <path-to-web-video-presentation>/themes/newsroom/tokens.css \
   presentation/src/styles/tokens.css
```

刷新 dev server。完成。章节代码一行没动。

如果切换后某章节看起来有问题，那是该章节在某处硬编码了颜色 / 字体 /
尺寸，而不是用语义 token。去找出来 —— bug 在章节里，不在主题里。

---

## 完整 token 契约

`base.css` 给**性格 token 都准备了合理的默认值**。主题的 `tokens.css`
只需要覆盖**调色板 + 字体 + 性格旋钮 + 装饰**这四类。

> **base.css 里的字号 / 间距 / 时长尺度只供 primitive class 自己用**
> （`.label-mono` / `.kicker` / `.scene-pad` 等）。**不是**章节必须消费
> 的契约——章节这一层要不要 `var(--t-h1)` 还是直接写 `font-size: 96px`
> 完全自由。

### 必填（主题必须定义）

#### 表面色（4 个）

| token         | 作用                                                |
| ------------- | --------------------------------------------------- |
| `--shell`     | letterbox / 舞台外的页面背景                        |
| `--surface`   | 舞台主背景                                          |
| `--surface-2` | 凸起 —— 卡片、代码块、嵌入面板                      |
| `--surface-3` | 最里层 —— surface-2 里再嵌一层时用                  |

#### 文字（4 个）

| token          | 作用                                  |
| -------------- | ------------------------------------- |
| `--text`       | 主                                    |
| `--text-2`     | 次（副标题、正文）                    |
| `--text-mute`  | 静音 —— 标签 / 元数据                 |
| `--text-faint` | 三级 —— 提示 / 禁用                   |

#### 线条（1 个）

| token    | 作用              |
| -------- | ----------------- |
| `--rule` | 发丝分割线颜色    |

#### Accent（3 个）

| token           | 作用                                          |
| --------------- | --------------------------------------------- |
| `--accent`      | accent 本体（一个品牌强色）                   |
| `--accent-soft` | 低透明度叠层 —— pill 背景、悬浮光晕            |
| `--accent-glow` | 中透明度叠层 —— text shadow、圆点发光          |

#### 字型家族（4 个）

| token               | 作用                                       |
| ------------------- | ------------------------------------------ |
| `--font-display-cn` | 中文显示家族                               |
| `--font-display-en` | 拉丁显示家族（斜体强调声音）               |
| `--font-body`       | 正文 / 段落家族                            |
| `--font-mono`       | 等宽家族（终端、mono caps、badge）          |

### 可选的性格覆盖（主题应该定义来表达自己的性格）

这些有 base 默认值；主题重新定义来表达性格。

| token              | base 默认           | 作用                                                  |
| ------------------ | ------------------- | ----------------------------------------------------- |
| `--font-features`  | `"tnum","ss01"`     | body 上的 OpenType 特性栈                             |
| `--r-card`         | `--r-md`            | 默认卡片圆角（sharp / refined / keynote）              |
| `--r-stage`        | `0`                 | 直接加在舞台本身的圆角                                 |
| `--rule-w`         | `1px`               | rule 粗细（1=发丝，2=中等，4=厚重）                    |
| `--rule-style`     | `solid`             | rule 样式（`solid` / `dashed` / `dotted`）             |
| `--hero-num-font`  | `--font-display-en` | `.hero-num` 用什么字体（主题决定性格）                 |
| `--hero-num-style` | `italic`            | `italic` / `normal`                                   |
| `--hero-num-weight`| `400`               | 400（编辑级）/ 500（等宽）/ 900（粗黑）                |
| `--hero-num-track` | `--track-tight`     | hero 数字的字距                                       |
| `--stage-pad-x`    | `96px`              | 舞台横向内边距（密度旋钮）                            |
| `--stage-pad-y`    | `80px`              | 舞台纵向内边距                                        |
| `--card-shadow`    | none                | `.card` 的 box-shadow                                 |
| `--card-glass-bg`  | `rgba(255,255,255,0.06)` | `.card-glass` 的背景                            |
| `--card-glass-border` | `rgba(255,255,255,0.12)` | `.card-glass` 的边框                            |
| `--shadow-stage`   | dark drop           | 舞台的 box-shadow                                     |
| `--stage-border`   | `none`              | 舞台的可选边框（Bauhaus 用 `4px solid black`）         |

### 可选的装饰层（主题可选用，给质感加签名）

这些默认是 no-op；主题选择性启用。装饰画**在舞台上**（pattern 用
`stage-frame::after`，vignette 用 `stage-frame::before`），所以会被屏幕
录制器捕捉到。

| token                        | 作用                                                                                                       |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------- |
| `--surface-pattern`          | 叠在舞台上的 `background-image`。SVG 噪声 / 网格 / 扫描线。                                                |
| `--surface-pattern-size`     | 配套的 `background-size`。可平铺渐变必填。                                                                  |
| `--surface-pattern-blend`    | pattern 层的 `mix-blend-mode`（`normal` / `multiply` / `overlay`）。                                       |
| `--surface-pattern-opacity`  | pattern 层的整体透明度乘子。                                                                                |
| `--surface-vignette`         | vignette 叠层的 `background`（黑板 / 电影感边角的径向渐变）。                                              |
| `--text-shadow`              | 应用在 `.serif-cn` / `.serif-it` / `.display-en` 上。如粉笔晕 / 磷光辉。                                    |

如果你需要的装饰找不到对应槽位，那就跨过"主题契约"边界进入"章节自定义
CSS"领域 —— 在那里解决，别扩主题契约。

---

## 创作新主题

### 1. 复制一个最接近的作为起点

挑一个**最接近**你目标气质的：

| 目标情绪                                | 起点                  |
| --------------------------------------- | --------------------- |
| 阴郁、电影感、编辑级                    | `midnight-press`      |
| 编辑级 - 浅色                           | `paper-press`         |
| 现代 keynote / SaaS                     | `warm-keynote`        |
| 教室 / 解说                             | `chalk-garden`        |
| 终端 / 黑客 / 复古 CRT                  | `terminal-green`      |
| 纪录片 / 严肃 / 新闻                    | `newsroom`            |
| 工程 / 蓝图 / 技术                      | `blueprint`           |
| 现代主义 / 布鲁塔利斯特 / 宣言          | `bauhaus-bold`        |
| 独立 / 玩味 / zine                      | `sunset-zine`         |
| 精炼 / 安静 / 印刷                      | `monochrome-print`    |
| 高级感暗底 / 时尚 / 博物馆图录          | `dark-botanical`      |
| 赛博朋克 / 未来感 / AI / web3           | `neon-cyber`          |
| 俏皮编辑 / 有声音的博主 / 文化随笔      | `vintage-editorial`   |
| 柔粉 / 友好 / onboarding / 女性向       | `pastel-dream`        |
| 双色分屏 / 对照 / 辩论                  | `split-canvas`        |
| pitch deck / 大字宣言 / 焦点色卡         | `bold-signal`         |
| B2B / 企业 / 投资人路演                 | `electric-studio`     |
| 复古朋克 / 创意工作室 / 设计周          | `creative-voltage`    |
| 学术 / 研究 / 中国当代文化              | `indigo-porcelain`    |
| 自然 / 可持续 / 户外 / 纪录             | `forest-ink`          |
| 文学 / 怀旧 / 书评 / 手工艺             | `kraft-paper`         |
| 建筑 / 艺术展览 / 高端画廊              | `dune`                |
| 瑞士国际主义 / Helvetica / 信息驱动设计 | `swiss-ikb`           |

```bash
cd <path-to-web-video-presentation>/themes
cp -r monochrome-print my-theme
```

### 2. 改 `my-theme/tokens.css`

按契约自上而下走一遍：调色板 → 字体 → 性格旋钮（`--r-card` /
`--rule-*` / `--hero-num-*` / `--stage-pad-*`）→ 阴影 → 装饰。
**不要**碰字号 / 间距 / 时长尺度 —— 那些是 base.css 给 primitive class
用的内部默认值，不是主题契约的一部分。

**几条不那么显而易见的规则：**

- 深色主题里 `--shell` **比 `--surface` 更深 / 更饱和**；浅色主题里
  `--shell` **比 `--surface` 略灰一点** —— 这样舞台读起来是"主体"，
  外围会退后。
- 维持 `--text` 与 `--surface` **至少 4.5:1 对比度**。96px+ 的标题
  可以放宽到 3:1，body / cue 必须 ≥ 4.5:1。
- `--accent` 是**唯一的**饱和色。第二个饱和色会跟第一个打架。
- `--accent-glow` 和 `--accent-soft` 是 `--accent` **同色相的透明度
  叠层**，永远不要用别的色相。
- `--text-faint` 在 `--surface` 上 13px 大写时**仍然要可读**。
- 挑**一个设计签名**重重发力：虚线 rule、粗黑边、扫描线、纸纹、glass
  slab。别同时叠三个。

### 3. 改 `my-theme/theme.json`

```json
{
  "id": "my-theme",
  "name": "My Theme",
  "nameZh": "我的主题",
  "description": "一句英文描述它的气质。",
  "descriptionZh": "一句中文描述它的气质。",
  "mood": ["dark", "moody", "futuristic"],
  "bestFor": ["<匹配场景 1>", "<匹配场景 2>"],
  "preview": {
    "shell": "#080808",
    "surface": "#101010",
    "text": "#f0f0f0",
    "accent": "#ffd54a"
  }
}
```

`id` 必须等于目录名。

### 主题元数据字段说明

| 字段 | 必填 | 取值 | 决定什么 |
|---|---|---|---|
| `id` / `name` / `nameZh` | ✓ | 字符串 | 主题标识 |
| `description` / `descriptionZh` | ✓ | 一句话 | Checkpoint Plan 列清单时的简介 |
| `mood` | ✓ | 标签数组 | 模糊匹配用 |
| `bestFor` | ✓ | 场景数组 | Checkpoint Plan 智能推荐时的命中点 |
| `preview` | ✓ | 4 色对象 | Checkpoint Plan 列清单时的视觉预览 |

> **主题不再约束动画选型 / 时长 / 字号 / emoji**。视觉风格由 `tokens.css`
> 的颜色 / 字体 / 字号 token 决定，动画 / 节奏 / 视觉演示完全交给 chapter
> agent 在每章实现时按内容自由发挥，避免主题字段过早限制创造力。
>
> 风格审美约束（不要紫粉渐变、不要 emoji 装饰、不要假数据等）由
> [`CHAPTER-CRAFT.md`](CHAPTER-CRAFT.md) 统一规定，与具体主题无关。

### 4. 用所有 demo 章节测试一遍

```bash
bash scripts/scaffold.sh /tmp/test-theme --theme=my-theme
cd /tmp/test-theme
npm run dev
```

把 demo 每一步点完。检查：

- 标题衬线在舞台上很清晰。
- accent 圆点在发光但不爆。
- 斜体强调有可读的背景。
- 进度条（悬浮底边）能看到，是 accent 色。
- masthead 行（`.masthead`）读起来像编辑 chrome，不像 navbar。
- hero 数字（`.hero-num`）感觉**和整体字型同源**，不像贴上去的。
- 卡片（`.card`）感觉是合适的材质（纸 / 玻璃 / cell）。
- 装饰**被注意到一次然后被忘掉** —— 永远不打扰。

哪里不对就改 `tokens.css`，刷新即可。无需重新构建。

### 5. 加到文档里

在本文件顶部"内置主题"表里追加一行。

---

## 反模式

- **章节 CSS 硬编码 hex 颜色 / 字体名** —— 缺哪个色彩 / 字体语义就在
  契约里补一个，给所有主题加上（注意：**字号 / 间距 / 时长**硬编码不算
  反模式，章节按内容自由设计）
- **演示中途切换主题** —— 选一个，一以贯之
- **第二个 accent 色** —— 只能有一个。用尺度 + 字重做层级
- **在组件层 override 主题 token**（颜色 / 字体 / 性格签名）—— 只在
  `:root` 里覆盖。一次性的颜色需求 = 提一个派生 token，让所有主题都
  提供自己的值
- **依赖主题的 TSX 条件分支** —— 章节必须主题无关。布局依赖明 vs 暗
  = 布局脆弱，修布局
- **一个主题叠三个设计签名** —— 选 ONE 个（虚线 rule / 扫描线 /
  glass slab / 纸纹 / 粗边），三个会自己打架
