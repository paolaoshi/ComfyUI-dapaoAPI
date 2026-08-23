# 主题选择

主题负责**审美气质、排版语言、图片风格、Raw 风格、代码 / 公式风格**。它不是 CSS 皮肤，
也不是信息密度规则。

> CSS 给浏览器读，theme profile 给 AI 读。

- **组件库拥有运行时主题**：CSS token、`ThemeProvider` 注册、实际渲染。
  注册的 runtime theme id 见 `src/theme/ThemeProvider.tsx`（当前：`tufte`、`press`）。
- **Skill 拥有主题 authoring profile**：`theme-profiles/index.json` + `<id>.md`，
  指导 AI 如何选择和使用主题。

## 选择流程

1. 读 `theme-profiles/index.json`，拿每个主题的 `bestFor` / `mood`。
2. 按 `source.md` 的内容类型 / 语气，从 `bestFor` 命中里挑 1-2 个推荐：
   - 技术 / 证据 / 数据型 → `tufte`。
   - 叙事 / 评论 / 出版 / 产品手记 → `press`。
3. 读选定主题的 `theme-profiles/<id>.md`（写作 / 配图 / Raw / 代码前的权威）。
4. 把选择 + 理由写进 `plan/plan.md` 的 **Theme** 段（见 `plan-template.md`）。

## Density 与 Theme 解耦

theme profile 里可以写"不同信息密度下的表现建议"，但**不能写成限制**。例：

- `tufte + 100% longform`：克制长文、数据证据、Raw 点亮关键概念。
- `tufte + 40% visual-essay`：仍成立，Raw 偏图解 / 证据、低装饰。
- `press + 100% longform`：可做深度出版文章。
- `press + 40% briefing`：更强编辑节奏与图文留白。

## 主题选择自检

- 主题是否匹配文章类型？
- 当前信息密度下，正文 / Raw / 图片比例该如何调整？
- Raw 是否能在该主题下自然发生？配图策略是否符合主题？
- 是否存在主题与源材料冲突？（冲突要在 `plan/plan.md` 的 Theme 段解释）
- runtime theme id 是否真实存在于组件库？Skill profile 是否存在？

## 新增主题的约束

新增主题必须**同时**满足：

1. 组件库有 runtime theme CSS 与 `ThemeProvider` 注册（`src/theme/themes/<id>/`）。
2. Skill 有对应 `theme-profiles/<id>.md`。
3. `theme-profiles/index.json` 绑定到正确 runtime theme id。

- 只有 Skill profile、没有组件库 runtime theme → 只能作候选，不能用于正式生成。
- 只有组件库 runtime theme、没有 Skill profile → Agent 不能主动推荐。
