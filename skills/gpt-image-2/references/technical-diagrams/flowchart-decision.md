# 流程图 / 决策图模板

> ⚠️ **本模板生成的是位图（PNG）**，不是 mermaid / draw.io 可编辑流程图。
> 需要可编辑请用 mermaid / draw.io / excalidraw / Figma。

本文件用于生成"工程感的业务流程图 / 决策图"：

- 业务流程图（用户注册流程、支付流程、订单生命周期）
- 决策树式流程（含 Yes / No 分支）
- 算法 / 数据处理流程
- 内部审批 / 工单 / 申报流程
- 异常处理 / 错误恢复流程

特征：

- 标准 BPMN-like 形状语义：
  - 圆 / 圆角矩形 = 开始 / 结束
  - 矩形 = 过程步骤
  - 菱形 = 决策点（含 Yes / No 分支）
  - 平行四边形 = 输入 / 输出
- 自上而下 OR 从左到右
- 暗色 grid 背景 + 等宽字体（沿用 technical-diagrams 视觉系统）
- 决策分支颜色编码（Yes 绿、No 红 / 灰）

## 适用范围

- 业务流程图
- 决策树流程
- 算法 / 数据流程
- 错误处理 / 异常流程
- 文档 / blog 配图

## 何时使用

- 用户提到 "流程图 / flowchart / 决策图 / decision tree / 业务流程 / 算法流程"
- 用户希望「BPMN 标准形状语义、含 Yes/No 决策分支」
- 用户接受位图

不要使用：

- 用户要的是「步骤教程插画」（暖色、卡通感） → 用 `infographics/step-by-step-infographic.md`
- 用户要的是「时序图」（actor + 消息）→ 用 `technical-diagrams/sequence-diagram.md`
- 用户要的是「状态机」（state + transition）→ 用 `technical-diagrams/state-machine.md`
- 用户要的是「系统架构」（多组件部署）→ 用 `technical-diagrams/system-architecture.md`
- 用户要的是「漫画分镜流程」 → 用 `storyboards-and-sequences/recipe-process-flowchart.md`

## 缺失信息优先提问顺序

1. 流程名称（"用户注册流程 / 退款流程 / XX 算法流程"）
2. 起点 / 终点（什么触发？什么结束？）
3. 主要步骤（建议 5-12 个步骤，超过考虑分子流程）
4. 决策点（哪些地方需要分支？分支条件？）
5. 是否有异常分支 / 失败回路
6. 流向（top-down 自上而下 / left-right 从左到右）
7. 比例（top-down 用 3:4 或 9:16；left-right 用 16:9）

## 主模板：标准 BPMN 风流程图

📖 描述

整张图按"开始 → 过程 → 决策 → 结束"的 BPMN 形状语义流动，自上而下排布，决策点用菱形 + 双向分支，箭头标 Yes/No。整体在暗色 grid 背景上呈现工程感。

📝 提示词

```json
{
  "type": "工程感流程图 / 决策图",
  "goal": "生成一张用 BPMN 标准形状语义画的业务流程图，可作 README / blog / 文档配图",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"3:4 portrait\"}",
    "background": "deep slate #0F172A with subtle 1px grid #1E293B at 32px spacing",
    "outer_padding": "60px"
  },
  "title_strip": {
    "title": "{argument name=\"title\" default=\"User Registration Flow\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"with email verification\"}",
    "position": "top-left, JetBrains Mono / SF Mono, light gray"
  },
  "flow_direction": "{argument name=\"flow_direction\" default=\"top-to-bottom\"}",
  "shape_legend": {
    "start_end": {
      "shape": "filled solid circle (start) and target / bullseye circle (end), or fully rounded pill rectangle with label 'Start' / 'End'",
      "color": "cyan #22D3EE for start, rose #FB7185 for end"
    },
    "process": {
      "shape": "rectangle with corner radius 8px",
      "color": "emerald #34D399 border + 12% fill"
    },
    "decision": {
      "shape": "diamond (rotated square)",
      "color": "amber #FBBF24 border + 12% fill",
      "labels": "Yes / No on outgoing arrows; arrow color: emerald for Yes, slate for No"
    },
    "io": {
      "shape": "parallelogram (skewed rectangle)",
      "color": "violet #A78BFA border + 12% fill",
      "use_for": "用户输入、数据写入、外部 API 输入输出"
    },
    "subprocess": {
      "shape": "rectangle with corner radius 8px and a smaller secondary rectangle inside (BPMN sub-process notation)",
      "color": "blue #60A5FA border + 12% fill",
      "use_for": "封装子流程，避免主图过大"
    }
  },
  "nodes": {
    "count": "{argument name=\"node_count\" default=\"9\"}",
    "items": [
      { "id": "S", "type": "start_end", "label": "Start" },
      { "id": "N1", "type": "io", "label": "User submits email + password" },
      { "id": "N2", "type": "process", "label": "Validate input format" },
      { "id": "N3", "type": "decision", "label": "Email already exists?" },
      { "id": "N4a", "type": "process", "label": "Show error: account exists" },
      { "id": "N4b", "type": "process", "label": "Create user record" },
      { "id": "N5", "type": "process", "label": "Send verification email" },
      { "id": "N6", "type": "decision", "label": "User clicks link within 24h?" },
      { "id": "N7a", "type": "process", "label": "Mark account verified" },
      { "id": "N7b", "type": "process", "label": "Soft-delete record" },
      { "id": "E", "type": "start_end", "label": "End" }
    ]
  },
  "edges": {
    "rule": "edges 沿主轴正交走线（自上而下时主轴 vertical），决策分支水平展开",
    "items": [
      { "from": "S", "to": "N1" },
      { "from": "N1", "to": "N2" },
      { "from": "N2", "to": "N3" },
      { "from": "N3", "to": "N4a", "label": "Yes" },
      { "from": "N3", "to": "N4b", "label": "No" },
      { "from": "N4a", "to": "E" },
      { "from": "N4b", "to": "N5" },
      { "from": "N5", "to": "N6" },
      { "from": "N6", "to": "N7a", "label": "Yes" },
      { "from": "N6", "to": "N7b", "label": "No" },
      { "from": "N7a", "to": "E" },
      { "from": "N7b", "to": "E" }
    ],
    "edge_style": {
      "default": "solid line 1.5px slate #64748B with filled triangle arrowhead",
      "yes_branch": "thin solid line in emerald #34D399 + label 'Yes' near origin in mono 9pt",
      "no_branch": "thin solid line in slate #64748B + label 'No'",
      "exception_branch": {
        "enabled": "{argument name=\"exception_branch_enabled\" default=\"false\"}",
        "style": "dashed rose #FB7185 line, label 'Exception' / 'Error'"
      }
    }
  },
  "swim_lanes": {
    "enabled": "{argument name=\"swim_lanes_enabled\" default=\"false\"}",
    "rule": "if true, divide canvas into vertical / horizontal lanes labeled by actor (e.g. 'User', 'Frontend', 'Backend', 'Email Service'); place each node in its actor's lane"
  },
  "legend": {
    "enabled": true,
    "position": "bottom-right",
    "content": "shape → role mapping (start/end, process, decision, io, subprocess) and edge → meaning",
    "style": "small panel, semi-transparent bg, mono 10pt"
  },
  "constraints": {
    "must_keep": [
      "BPMN 形状语义严格对应",
      "决策节点必有 ≥ 2 条分支",
      "每条决策分支必标 'Yes' / 'No' 或具体条件",
      "edges 正交走线，标签不与边重叠",
      "暗色背景 + 等宽字体",
      "至少有 1 个 start 和 1 个 end",
      "legend 必画"
    ],
    "avoid": [
      "用 emoji 节点",
      "把决策点画成圆 / 方（必须菱形）",
      "把过程画成菱形（混淆语义）",
      "斜线乱飞 / 边穿过节点",
      "节点 > 15 个（拆分子流程）",
      "决策分支没有标签",
      "用花哨字体 / 渐变填充",
      "把流程图画成插画感（步骤教程请用 step-by-step-infographic）",
      "声称这是可编辑 SVG（它是位图）"
    ]
  }
}
```

### 参数策略

- **必问**：`title`、起点 + 终点、节点列表（含 type）、决策点的分支条件
- **可默认**：`flow_direction`（top-to-bottom）、`background`（暗色 grid）、`shape_legend`、`legend_enabled`（true）
- **可随机**：节点位置（基于 flow_direction 自动布局）

### 自动补全策略

- 用户给 5-7 个步骤但没说决策 → 默认无决策（纯线性流程）
- 用户说"含异常处理" → 启用 `exception_branch_enabled` + 加 dashed rose 线
- 用户说"多角色 / 跨部门 / 跨服务" → 启用 `swim_lanes_enabled`
- 用户说"流程很长，超过 12 步" → 反问是否拆分为多个子流程
- 用户说要 light 模式 → 用变体 1

## 变体 1：浅色 Light 流程图

```json
{
  "modify": {
    "background": "warm off-white #F8FAFC + faint grid #E2E8F0",
    "node_fill": "shape role color × 8% opacity",
    "node_border": "1.5px solid full opacity (use deeper shade for white bg)",
    "label_color": "deep slate #0F172A",
    "edge_color": "slate #475569",
    "vibe": "适合白底文档站 / 印刷版"
  }
}
```

## 变体 2：Swim Lanes 跨角色泳道流程图

```json
{
  "modify": {
    "swim_lanes_enabled": true,
    "lane_layout": "vertical lanes (each actor a vertical column)",
    "lane_labels": ["User", "Frontend", "Backend API", "Database", "Email Service"],
    "rule": "每个 node 放进对应 actor 的 lane；edges 跨 lane 时用粗箭头",
    "use_case": "跨部门审批、跨服务交互、用户与系统多次互动"
  }
}
```

适用：跨部门审批流程、跨服务交互流程、需要明确"谁干什么"的流程。

## 变体 3：算法伪代码可视化流程

```json
{
  "modify": {
    "title": "Algorithm: <name>",
    "node_label_format": "节点 label 用伪代码片段而非自然语言",
    "rule_extra": "保留循环节点（向回的弧形箭头表示 loop），变量赋值用 ← 符号",
    "vibe": "适合论文 algorithm box 的可视化版本"
  }
}
```

适用：算法可视化、论文 algorithm 章节的视觉版、教学讲义。

## 避免事项

- 决策菱形画成方块或圆（语义混淆）
- 决策分支没有 Yes / No 标签
- 节点 > 15 个（视觉爆炸，建议拆分）
- 用 emoji 节点图标
- 边斜飞 / 穿过节点 / 标签碰撞
- 用插画感卡通图（请用 `step-by-step-infographic.md`）
- 用 3D / 渐变 / 玻璃质感
- 多个起点或多个终点未标记清楚
- swim lane 时把跨 lane 的箭头画得不显眼
- 把"系统架构"塞进流程图（节点是组件而非动作）
