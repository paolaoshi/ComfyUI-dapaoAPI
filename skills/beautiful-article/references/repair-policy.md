# 修复政策（最小切片）

按最小单位修复。**有修复才写** `review/repair-log.md`（一次过 / 无修复则不写）。

## 禁止

- 用户只反馈一处问题就**重写整篇**。
- 为了修视觉而改动**已确认的文章结构**。
- 为了压缩信息而删除用户**指定必须保留**的内容。

## 最小切片对照

| 问题 | 最小修复单位 |
|---|---|
| 信息缺失 | 对应 Section / Table / CodeBlock |
| 信息太密 | 对应 Section 的段落和局部 Raw |
| 主题不对 | `plan/plan.md` 的 Theme 段 + 局部 token / Raw |
| 图片不对 | 对应图片和 `plan/plan.md` 的 Assets 段 |
| 首屏不对 | Hero / Lead / Summary |
| Raw 跑偏 | 单个 Raw block |
| 移动端问题 | 对应 CSS / 组件布局 |
| 构建错误 | 具体文件和行 |

## repair-log.md 格式

```markdown
## <日期> <谁反馈 / 哪个 Reviewer>
- 问题：<一句话>
- 定位层：<节奏 / 视觉 / 内容 / 构建>
- 最小修复单位：<Section 03 / raw-blocks/02 / main.tsx 主题 ...>
- 改动：<改了什么>
- 验证：<dev 预览 / npm run html 通过 / 控制台无错>
```

先定位是哪一层（内容 / 结构 / 视觉 / 构建），再改最小切片，**不要重做整篇**。
