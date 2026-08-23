# 脚手架

脚手架在 Phase 4 创建文章工作区，**不把工程代码塞进 SKILL.md**。工程模板是 Skill
assets（`assets/scaffold-template/`），由 `scripts/scaffold.sh` 复制并接线。

## 用法

```bash
bash <path-to-beautiful-article>/scripts/scaffold.sh ./my-article --theme=tufte
bash <path-to-beautiful-article>/scripts/scaffold.sh ./brief --theme=press --no-cover
bash <path-to-beautiful-article>/scripts/scaffold.sh --list-themes
```

`--theme` 必须是 `theme-profiles/index.json` 里的 id（当前 `tufte` / `press` / …）。工作区可建在
**任意目录**，不需要在 reacticle 仓库内。

`--no-cover` 禁用书封式文章封面（默认开 · 屏幕 3:4 / PDF 独占首页）。Checkpoint 1 用户
选了"封面 · 关"时传这个。详见 `references/cover.md`。

## 脚手架做什么

- 创建工作区目录 + 复制 Vite / React / TS 模板。
- **从 npm 安装最新发布版的 `reacticle`**：`package.json` 里 `reacticle: "latest"`，脚手架
  装完依赖后再 `npm install reacticle@latest` 强制刷新到当下最新，并打印实际版本。
- 在 `article/main.tsx` 写入所选 runtime theme id，并 `import "reacticle/styles.css"`。
- 创建默认 `article/Article.tsx` + `article/sections/`、`article/raw-blocks/`、
  `article/assets/`。`Article.tsx` 末尾自带 **colophon Raw 块**（`Made with
  [beautiful-article](github 仓库) · <主题> theme`），样式低对比小字、走 `--ra-*` token，
  **不可删除**（见 SKILL.md「默认策略」）。
- 默认创建 **`article/Cover.tsx`**（书封式封面外壳 + 占位：屏幕 3:4 / PDF 独占首页）并在
  `main.tsx` 里渲染 `<Cover />` 在 `<ArticleDoc />` 之上。`--no-cover` 时跳过这一步：
  不复制 Cover.tsx，并从 `main.tsx` 剥掉 `__COVER_IMPORT_*__` / `__COVER_RENDER_*__`
  标记包裹的两段。封面设计见 `references/cover.md`。
- 创建工作记忆目录 `source/`、`plan/`、`review/`。
- `katex` / `prismjs` 作为 `reacticle` 的依赖会被自动带下来，无需在工作区单独声明。

## 升级组件库

工作区随时可升级到最新组件库：

```bash
npm install reacticle@latest
```

## 工作区结构

```text
my-article/
  package.json  vite.config.ts  tsconfig.json  tsconfig.node.json  index.html
  source/   plan/   review/
  article/
    main.tsx        # 入口：<ThemeProvider theme="..."> + <Cover/> + <ArticleDoc/>
    Cover.tsx       # 书封式文章封面：屏幕 3:4 / PDF 独占首页（默认；--no-cover 时不生成）
    Article.tsx     # assembler（主 Agent 拥有）：import + 排序各 Section，不写 Section 正文
    sections/       # 一节一文件（铁律）：NN-*.tsx，每个导出一个 Section 组件
      01-opening.tsx
    raw-blocks/     # 大型 Raw 隔离：NN-*.tsx
    assets/         # 配图素材
  .theme            # 记录起步主题
```

> **一个 Section = 一个文件**（`sections/NN-*.tsx`），坚决不允许把多个 Section 写进
> `Article.tsx`。`Article.tsx` 只做组装。这是多 Agent 并行（开发模式由 Checkpoint 2 选定）
> 的前提，详见 `references/section-build.md`。

## 切主题

改两处（脚手架默认会把主题名注入到这两个位置）：

1. `article/main.tsx` 里 `<ThemeProvider theme="...">`（控制运行时主题）。
2. `article/Article.tsx` 末尾的 colophon `· <主题> theme`（控制印记里显示的主题名）。

两处保持一致。详见 `html-output.md`。

## 构建 / 预览

见 `references/html-output.md`（`npm run dev` / `build` / `html`）。
