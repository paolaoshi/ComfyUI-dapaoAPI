# HTML 输出与构建

工作区是一个 Vite + React + TS 项目，从 npm 消费 `reacticle`（最新发布版）。文章源在
`article/Article.tsx`（由 `article/main.tsx` 挂载，主题在此固定）。

## 命令（在工作区根目录）

| 命令 | 作用 |
|---|---|
| `npm run dev` | 启动预览（Phase 4 / 5 边写边看）。 |
| `npm run build` | `tsc --noEmit` 类型检查 **+** 构建自包含单页 HTML 到 `dist/index.html`（CSS + JS 内联）。TS 报错会让构建失败，避免错误漏进交付物。 |
| `npm run html` | 复用 `npm run build`（含类型检查），再把单页 HTML 复制到 `article/article.html`（**交付物**）。 |
| `npm run typecheck` | 仅类型检查。 |

单文件由 `vite-plugin-singlefile` 产出：CSS + JS 全部内联，**断网可打开、可分享**。

## 切换主题

主题在 `article/main.tsx` 的 `<ThemeProvider theme="...">` 改一个字即可（必须是组件库
已注册的 runtime theme id：`tufte` / `press`）。

## PDF（可选 · 由 Checkpoint 3 触发）

详见 `references/pdf-output.md`。一句话用法：

```bash
npm run html                                                   # 先有 article/article.html
bash <path-to-beautiful-article>/scripts/html-to-pdf.sh        # → article/article.pdf
```

脚本会自动探测系统的 chromium-family 浏览器，在 HTML 头部注入 `@media print` 覆盖（把
TOC 从左右栅格塌成上下排布，TOC 独占首页），再 headless 打印为 PDF。无 npm 依赖、无 Node。

> Raw 交互在 PDF 里只能渲染为初始态。`interactive-explainer` 类型 PDF 价值有限，用户可在
> Checkpoint 3 自行决定要不要导。

如需"复制为提示词 / 行动项"按钮，可在文章里挂 `ExportBar`（与 PDF 无关）。

## 交付自检

- `npm run html` 成功，`article/article.html` 能在浏览器离线打开。
- 控制台无报错；桌面与移动端都可读，无文字溢出 / 遮挡 / 空白异常。
