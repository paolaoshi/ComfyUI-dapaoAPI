# 系统架构图模板

> ⚠️ **本模板生成的是位图（PNG），不是可编辑的 SVG / draw.io / mermaid 图**。
> 如果你需要可编辑、可对齐、可版本化的工程图，请用 mermaid / draw.io / excalidraw / Figma。
> 如果你需要的是「README 头图 / blog 配图 / 文档插图 / PPT 封面」级别的视觉呈现，本模板适合。

本文件用于生成"工程感系统架构图"：

- 整体系统架构（前端 + 后端 + DB + 缓存 + 队列 + 外部服务）
- 微服务架构概览
- 多区域 / 多 zone 部署架构
- AI 系统 / 数据管道架构
- 云原生架构图

特征：

- 暗色背景 (#0F172A slate-900) + 细 grid
- 节点 = 圆角矩形 + 半透明深色填充 + 1.5px 边框 + 等宽字体标签
- 配色按"角色"分类（用户层 / 业务层 / 数据层 / 基础设施 / 安全 / 中间件 / 外部）
- 有向数据流箭头：实箭头 = 同步，虚线 = 异步 / 回调
- 区域用虚线大框包围（VPC / 云区 / Trust boundary）
- 字体：JetBrains Mono / SF Mono 等宽

## 适用范围

- 系统总览架构图
- 微服务 / 分布式系统架构
- 多区域 / 多云部署架构
- 数据管道 / AI 系统架构
- 文档 / blog 配图 / README 头图

## 何时使用

- 用户提到 "系统架构 / 微服务 / 分布式 / 部署架构 / 数据管道 / AI 系统架构 / 云架构"
- 用户希望视觉「工程感、暗色、grid 网格、像 baoyu-diagram 那种」
- 用户接受这是位图（不要求可编辑）

不要使用：

- 用户要的是「业务流程图 / 决策图」 → 用 `technical-diagrams/flowchart-decision.md`
- 用户要的是「时序图 / API 调用流」 → 用 `technical-diagrams/sequence-diagram.md`
- 用户要的是「网络拓扑」（机房 / 路由器 / 设备）→ 用 `technical-diagrams/network-topology.md`
- 用户要的是「ER 图 / 数据模型」 → 用 `technical-diagrams/er-diagram.md`
- 用户要的是「论文方法 pipeline」 → 用 `academic-figures/method-pipeline-overview.md`
- 用户要的是「神经网络架构」 → 用 `academic-figures/neural-network-architecture.md`

## 缺失信息优先提问顺序

1. 系统名称 + 一句话定位（"我们要画 XX 平台的整体架构"）
2. 主要分层 / 区域（如"前端 / 网关 / 业务服务 / 数据层 / 基础设施"）
3. 每层有哪些节点（最多 8-15 个总节点，超过会拥挤）
4. 主要数据流方向（用户请求 → ... → 响应）
5. 是否有外部服务（第三方 API / SaaS）
6. 是否有"安全 / 鉴权 / 监控"相关组件需要单独标
7. 主题色偏好（默认 dark；是否要 light variant）
8. 比例（默认 16:9 横版；架构图很少竖版）

## 主模板：分层暗色系统架构图

📖 描述

整张图按层 / 按区域划分，每层是一组带相同色系的节点，节点之间用箭头连接表达数据流，整体在深色 grid 背景上呈现工程感。

📝 提示词

```json
{
  "type": "技术系统架构图（暗色工程感）",
  "goal": "生成一张用于 README / blog / 设计文档的工程感系统架构图",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"16:9\"}",
    "background": "{argument name=\"background\" default=\"deep slate #0F172A with subtle 1px grid lines #1E293B at 32px spacing\"}",
    "outer_padding": "60px"
  },
  "title_strip": {
    "title": "{argument name=\"title\" default=\"System Architecture Overview\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"v1.0 · 2026\"}",
    "position": "top-left, large mono font (JetBrains Mono / SF Mono), light gray text"
  },
  "color_semantics": {
    "rule": "颜色按'角色'编码，不按'技术'编码",
    "palette": [
      { "role": "User / Client / Edge", "color": "cyan #22D3EE", "use_for": "终端用户、Web、Mobile、CLI" },
      { "role": "Gateway / API / BFF", "color": "blue #60A5FA", "use_for": "API 网关、负载均衡、CDN、BFF" },
      { "role": "Business Services", "color": "emerald #34D399", "use_for": "微服务、应用层、业务逻辑" },
      { "role": "Data / Persistence", "color": "violet #A78BFA", "use_for": "数据库、缓存、对象存储、搜索" },
      { "role": "Middleware / Queue", "color": "orange #FB923C", "use_for": "MQ、Kafka、Redis Stream、Pub/Sub" },
      { "role": "Infra / Platform", "color": "amber #FBBF24", "use_for": "K8s、容器运行时、云平台" },
      { "role": "Security / Auth", "color": "rose #FB7185", "use_for": "鉴权、密钥、审计、防火墙" },
      { "role": "External / 3rd Party", "color": "slate #94A3B8", "use_for": "外部 SaaS、第三方 API" }
    ]
  },
  "regions": {
    "rule": "用大虚线框包围属于同一'部署单元'的节点，框上方有 region label",
    "items": [
      { "id": "R1", "label": "{argument name=\"region1_label\" default=\"Public Edge\"}", "color_border": "cyan dashed" },
      { "id": "R2", "label": "{argument name=\"region2_label\" default=\"VPC · ap-northeast-1\"}", "color_border": "amber dashed" },
      { "id": "R3", "label": "{argument name=\"region3_label\" default=\"Data Plane\"}", "color_border": "violet dashed" }
    ]
  },
  "nodes": {
    "count_total": "{argument name=\"node_count\" default=\"10\"}",
    "items": [
      { "id": "N1", "label": "Web App", "role": "User / Client", "region": "R1" },
      { "id": "N2", "label": "Mobile App", "role": "User / Client", "region": "R1" },
      { "id": "N3", "label": "CDN", "role": "Gateway / API", "region": "R1" },
      { "id": "N4", "label": "API Gateway", "role": "Gateway / API", "region": "R2" },
      { "id": "N5", "label": "Auth Service", "role": "Security / Auth", "region": "R2" },
      { "id": "N6", "label": "Order Service", "role": "Business Services", "region": "R2" },
      { "id": "N7", "label": "User Service", "role": "Business Services", "region": "R2" },
      { "id": "N8", "label": "Kafka", "role": "Middleware / Queue", "region": "R2" },
      { "id": "N9", "label": "PostgreSQL", "role": "Data / Persistence", "region": "R3" },
      { "id": "N10", "label": "Redis", "role": "Data / Persistence", "region": "R3" }
    ]
  },
  "node_style": {
    "shape": "rounded rectangle, corner radius 8px",
    "size": "auto-fit text + 24px horizontal padding, ~ 140px wide × 56px tall typical",
    "fill": "background color of role × 12% opacity (semi-transparent)",
    "border": "1.5px solid in role color (full opacity)",
    "label": "label text in JetBrains Mono / SF Mono 12pt, color = role color (lighter shade) for readability on dark bg",
    "icon": "small icon in top-left corner of node (optional, generic geometric glyph for the role — circle for service, cylinder for DB, hex for queue)"
  },
  "edges": {
    "sync_call": {
      "style": "solid line 1.5px in slate #64748B, with small filled triangle arrowhead at the target end",
      "use_for": "同步请求 / 调用"
    },
    "async_event": {
      "style": "dashed line 1.5px in slate #64748B, with hollow triangle arrowhead",
      "use_for": "异步事件 / 消息发布订阅 / 回调"
    },
    "data_flow_label": {
      "rule": "edges 上可选标小标签（如 'POST /orders' / 'order.created event'），用 mono 字体 9pt，背景与画布融合"
    },
    "rule_routing": "尽量正交（水平 / 垂直）走线；如果必须斜线，控制在 ≤ 30°；边不要穿过节点"
  },
  "legend": {
    "enabled": "{argument name=\"legend_enabled\" default=\"true\"}",
    "position": "bottom-right",
    "content": "color → role mapping (8 swatches), and edge style → meaning (sync solid vs async dashed)",
    "style": "small panel with semi-transparent background, mono font 10pt"
  },
  "constraints": {
    "must_keep": [
      "暗色背景 + 细 grid",
      "颜色按 role 编码，不要按技术品牌（如 PostgreSQL 用 violet 因它是 data，不是因为 PG 官方蓝）",
      "节点统一圆角和尺寸基线",
      "等宽字体（mono）贯穿全图",
      "edges 不穿过节点，标签不与边重叠",
      "区域虚线框颜色与区域含义匹配",
      "legend 必须画出（即使简化）"
    ],
    "avoid": [
      "彩虹色 / 高饱和霓虹色（除 cyan 之外其它色都要 muted）",
      "用 emoji 当节点图标（用极简几何 glyph）",
      "技术 logo 直接贴上去（除非是商标对照说明）",
      "3D 立方体 / 透视效果 / 玻璃质感",
      "同一种颜色既表'安全'又表'业务'",
      "节点超过 15 个（请拆分到多张子图）",
      "声称这张图可编辑 / 可导出 SVG（它是位图）",
      "用花哨字体 / 手写体（破坏工程感）"
    ]
  }
}
```

### 参数策略

- **必问**：`title`、节点列表（含每个节点的 role 归属）、主要 edges
- **可默认**：`background`（暗色 grid）、`color_semantics`（8 角色调色板）、`node_style`、`legend_enabled`（true）
- **可随机**：节点摆放位置（基于区域 / role 自动布局）、icon glyph 具体造型

### 自动补全策略

- 用户给 "Web + API + DB" 三层简化 → 自动用 3 个 region (Edge / Service / Data) + 5-7 个节点
- 用户没说 region → 默认按 role 自动聚类 + 加 region 框
- 用户没说要不要 light 变体 → 默认 dark；用户说要 light 时切换到变体 1
- 用户给具体技术（"用 PostgreSQL"）→ 节点 label 直接写技术名，但配色仍按 role 选

## 变体 1：浅色 / Light 模式系统架构图

```json
{
  "modify": {
    "background": "warm off-white #F8FAFC with very faint grid #E2E8F0",
    "node_fill": "role color × 8% opacity",
    "node_border": "1.5px solid role color (full opacity)",
    "label_color": "role color (full opacity, dark enough for white bg) — e.g. cyan label uses cyan-700 not cyan-300",
    "title_color": "deep slate #0F172A",
    "edges_color": "slate #475569",
    "vibe": "看起来像 light theme 文档配图（适合 Notion / GitHub / 白底文档）"
  }
}
```

适用：白底文档站、印刷版文档、对比 dark 版本提供的 light alternative。

## 变体 2：极简 monochrome 系统架构图

```json
{
  "modify": {
    "color_semantics": "all roles use slate #94A3B8 except 'highlight current focus' uses single accent (e.g. cyan #22D3EE)",
    "use_case": "强调结构本身，不强调角色分类（如教学讲解、概念示意）",
    "vibe": "克制、非分散注意力、像 The Verge / Stripe blog 的极简插图"
  }
}
```

适用：概念性示意（不需要强调角色）、blog hero 图、教学。

## 变体 3：Hero / Marketing 风系统架构图

```json
{
  "modify": {
    "background": "渐变深蓝紫 + 远景星点 + 主体节点带柔和发光",
    "node_style": "节点保留圆角和等宽字体，但加微妙发光（drop shadow + glow）",
    "title": "更大、加副标语",
    "use_case": "产品官网 hero / 投资人 deck / 发布会主图",
    "vibe": "Stripe / Linear / Vercel 官网风的视觉冲击力"
  }
}
```

适用：产品官网、技术品牌官网 hero、产品发布会主图。

## 避免事项

- 节点 > 15 个 → 视觉拥堵，建议拆分到多张图（"高层架构" + "细分模块图"）
- 用 PostgreSQL / Redis / Kafka 真实 logo → 容易侵权 + 破坏统一视觉
- 颜色按"技术"分（如 PG 用蓝、Redis 用红）→ 失去 role 语义
- 用 emoji 节点图标
- 3D 透视 / 玻璃质感 / 渐变填充节点
- 边穿过节点 / 标签碰撞 / 斜线乱飞
- 没有 legend → 读者不知道颜色含义
- 没有 region 框（即使逻辑上有分层）→ 失去"部署单元"信息
- 假装这是可导出可编辑的 SVG → 别误导用户
- 把神经网络结构 / 业务流程 / 时序 也塞到这张图（应该用对应模板）
