# Theme Profile · freddie（Mailchimp 暖黄 / 友善）

> 这是给 **AI 写作时读** 的 authoring profile，不是 CSS。CSS token 由组件库
> 运行时主题持有（`data-theme="freddie"`）。本文件是"如何选择和使用这个主题"。
> 详尽版本见组件库 canonical md：`src/theme/themes/freddie/freddie.md`（写代码 /
> 公式 / 媒体 / Raw 前请读它）。

- **runtime theme id**：`freddie`（`<ThemeProvider theme="freddie">`）
- **气质**：温暖人文派（Mailchimp）。纯白纸、近黑 Peppercorn 墨、Cavendish 明黄
  只作**荧光笔 / 色块**（绝不作文字色）。俏皮柔和的衬线标题（Fraunces）压在干净
  grotesque 正文（Hanken）之上。机灵、亲切、有人味，但仍专业。完整继承结构纪律。

## 适合 / 不适合的文章类型

- **适合**：产品介绍、`tutorial` / 上手指南、changelog 叙事、功能 `explainer`、FAQ、
  亲和力强的营销味长文。面向普通用户、需要温度与幽默的内容。
- **不适合**：学术论文（`knuth`）；冷调系统规格（`vignelli`）；暗底工程现场（`shannon`）；
  极密集数据报告（`tufte`）；柔软治愈向（`andy`）；幻灯片。

## 排版气质

- 标题用 Fraunces（仿 Cooper / Means 的柔软俏皮），正文 / 标签用 Hanken Grotesk（仿 Graphik）。
- 正文 ~17px，行距 1.65；标题靠 `display: 600` + 柔轴，不靠超粗。强调不用斜体（协议级禁用）。
- **黄是荧光不是墨**：链接 = 黑字 + 黄 highlight（hover 填满）；章节号 = 黑字 + 黄贴纸（略旋转）。

## Raw 风格

像一页友好、带手作感的产品说明插图。

- 约束的是**气质**（黑 / 白 / 黄、适度圆角、舒展留白、一点人情味），不是**媒介**。
- 典型：步骤 / 流程图、对比示意、带黄色 highlight 的标注、友好小数据图、可点开 FAQ。
- 构图：留白舒展、黄只作强调、适度圆角；颜色只用 `--ra-*`（黄用 `--mc-yellow`）。
- 动效：允许短促、带一丝回弹的过渡；避免无限循环装饰。

## 媒体（图片 / 视频 / 音频）风格

- 适合：精修产品截图、温暖摄影、scruffy / 手绘风插画、流程示意、带人物的友好配图。
- 构图留白舒展、主体清楚、可有一点不规整的人味；caption 简洁；必须配 alt。
- 色彩贴近黑 / 白 / 黄，强调用黄色块承载，不引入紫粉冷渐变。

## 代码 / 公式风格

- `CodeBlock` 像友好的代码片段：暖浅 surface + 发丝线 + 适度圆角，不用暗色编辑器窗口。
- Prism token：标签 / 函数走墨色或暖红，关键字用 risk 红，字符串用绿；**黄不作语法色**。
- `Formula` 像正文里的友好标注：克制、对齐，可有极淡圆角 surface。

## 禁止项

- 把 Cavendish 黄当文字 / 链接 / 语法色（不可读，破坏识别）。
- 紫粉渐变、霓虹、Tailwind 默认味、把 emoji / 图标当装饰。
- 大圆角 + 大投影的卡片堆叠（那是 `andy` 的柔软领域）；用斜体强调。

## 不同信息密度下的表现建议（建议，非限制）

- `100% explainer / tutorial`：友好长文 + 步骤图 + 黄色 callout，正文为主体。
- `60-80% 产品介绍`：保留关键步骤 + 截图，黄色强调点睛。
- `40% briefing`：Raw 偏友好图解，文字更短，仍是亲切产品形态。
