# 时序图模板

> ⚠️ **本模板生成的是位图（PNG）**，不是 PlantUML / mermaid 可编辑时序图。
> 需要可编辑请用 mermaid / PlantUML / draw.io。

本文件用于生成"工程感时序图"：

- API 调用时序（前端 → 后端 → DB）
- 鉴权 / OAuth / 多步握手时序
- 微服务间消息传递时序
- 分布式事务 / Saga / 2PC 时序
- 客户端 - 服务器 - 第三方 三方协议时序

特征：

- 顶部一排 actor 框（带名字 + 类型 icon）
- 每个 actor 下方一条垂直虚线（lifeline）
- 水平消息箭头连接 actors（实箭头同步、虚线箭头异步 / return）
- lifeline 上有"激活条"（细长矩形）表示该 actor 正在处理
- 消息可编号（1, 2, 3...）
- 暗色 grid 背景 + 等宽字体

## 适用范围

- API 调用时序
- 鉴权 / OAuth 流程
- 微服务消息时序
- 分布式事务 / Saga / 2PC
- 第三方协议 / SDK 调用流

## 何时使用

- 用户提到 "时序图 / sequence diagram / 调用时序 / API 流 / OAuth 流 / 分布式事务"
- 用户希望「actor + lifeline + 消息箭头」标准 UML 时序图样式
- 用户接受位图

不要使用：

- 用户要的是「业务流程 / 决策」 → 用 `technical-diagrams/flowchart-decision.md`
- 用户要的是「状态机」 → 用 `technical-diagrams/state-machine.md`
- 用户要的是「系统架构」 → 用 `technical-diagrams/system-architecture.md`

## 缺失信息优先提问顺序

1. 时序名称（"OAuth 2.0 授权码流程 / 下单时序 / Saga 事务"）
2. 参与的 actors（按从左到右顺序）
3. 消息序列（按时间顺序，标明 sender → receiver、消息内容、同步 / 异步）
4. 是否有失败 / 重试分支
5. 是否有 self-call（actor 调用自己内部方法）
6. 是否需要消息编号（论文 / 协议描述常需要）
7. 比例（默认 16:9 横版；actor 多时可用 4:3）

## 主模板：标准 UML 时序图

📖 描述

整张图顶部一排 actor 框，下方每个 actor 一条垂直虚线 lifeline，水平消息箭头连接 actors，激活条标在 lifeline 上，消息编号 + 标签清晰。

📝 提示词

```json
{
  "type": "工程感时序图（UML sequence diagram）",
  "goal": "生成一张工程感时序图作为 README / blog / 协议文档配图",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"16:9\"}",
    "background": "deep slate #0F172A with subtle 1px grid #1E293B at 32px spacing",
    "outer_padding": "60px"
  },
  "title_strip": {
    "title": "{argument name=\"title\" default=\"OAuth 2.0 Authorization Code Flow\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"with PKCE\"}",
    "position": "top-left, JetBrains Mono / SF Mono, light gray"
  },
  "actors": {
    "count": "{argument name=\"actor_count\" default=\"4\"}",
    "items": [
      {
        "id": "A1",
        "name": "{argument name=\"actor1_name\" default=\"User\"}",
        "type": "{argument name=\"actor1_type\" default=\"user\"}",
        "icon_glyph": "stick figure outline"
      },
      {
        "id": "A2",
        "name": "{argument name=\"actor2_name\" default=\"Web App\"}",
        "type": "{argument name=\"actor2_type\" default=\"client\"}",
        "icon_glyph": "browser window outline"
      },
      {
        "id": "A3",
        "name": "{argument name=\"actor3_name\" default=\"Auth Server\"}",
        "type": "{argument name=\"actor3_type\" default=\"service\"}",
        "icon_glyph": "shield outline"
      },
      {
        "id": "A4",
        "name": "{argument name=\"actor4_name\" default=\"Resource Server\"}",
        "type": "{argument name=\"actor4_type\" default=\"service\"}",
        "icon_glyph": "database / server outline"
      }
    ],
    "header_box_style": {
      "shape": "rounded rectangle, corner radius 6px",
      "fill": "type-coded color × 12% opacity",
      "border": "1.5px solid type-coded color",
      "size": "160px wide × 64px tall, all headers identical size, evenly spaced",
      "label": "actor name in mono 11pt + small icon glyph above name"
    },
    "type_color_map": {
      "user": "cyan #22D3EE",
      "client": "blue #60A5FA",
      "service": "emerald #34D399",
      "database": "violet #A78BFA",
      "external": "slate #94A3B8"
    }
  },
  "lifelines": {
    "rule": "每个 actor header 下方画一条垂直虚线 (1px dashed slate #475569)，从 header 底部一直延伸到画布底部",
    "spacing": "lifelines 之间等距，间距 ≥ 200px"
  },
  "messages": {
    "count": "{argument name=\"message_count\" default=\"10\"}",
    "items": [
      { "id": "M1", "from": "A1", "to": "A2", "label": "1. Click 'Sign in'", "type": "sync" },
      { "id": "M2", "from": "A2", "to": "A3", "label": "2. GET /authorize?code_challenge=...", "type": "sync" },
      { "id": "M3", "from": "A3", "to": "A1", "label": "3. Show login page", "type": "return" },
      { "id": "M4", "from": "A1", "to": "A3", "label": "4. Submit credentials", "type": "sync" },
      { "id": "M5", "from": "A3", "to": "A2", "label": "5. Redirect with auth_code", "type": "return" },
      { "id": "M6", "from": "A2", "to": "A3", "label": "6. POST /token { code, code_verifier }", "type": "sync" },
      { "id": "M7", "from": "A3", "to": "A2", "label": "7. { access_token, refresh_token }", "type": "return" },
      { "id": "M8", "from": "A2", "to": "A4", "label": "8. GET /api/data (Bearer token)", "type": "sync" },
      { "id": "M9", "from": "A4", "to": "A4", "label": "9. validate token", "type": "self" },
      { "id": "M10", "from": "A4", "to": "A2", "label": "10. { data: ... }", "type": "return" }
    ],
    "message_style": {
      "sync": "solid line 1.5px slate #94A3B8, filled triangle arrowhead at target",
      "async": "solid line 1.5px slate #94A3B8, hollow triangle arrowhead",
      "return": "dashed line 1.5px slate #64748B, hollow triangle arrowhead",
      "self": "horizontal arrow that loops out to the right and back to the same lifeline (bracket shape)"
    },
    "label_format": "<编号>. <消息内容>，例如 '5. Redirect with auth_code'，mono 10pt，标在 arrow 上方居中"
  },
  "activation_bars": {
    "enabled": "{argument name=\"activation_bars_enabled\" default=\"true\"}",
    "rule": "在 actor lifeline 上画细长矩形（4-6px 宽）覆盖该 actor 处理消息的时间段；颜色用 actor 的 type color，半透明",
    "vertical_extent": "从该 actor 收到一个 message 开始，到它发出 return 结束"
  },
  "annotations": {
    "notes": {
      "enabled": "{argument name=\"notes_enabled\" default=\"false\"}",
      "rule": "可在某段时序旁画黄色便签（amber 半透明圆角矩形），加注释；如 'PKCE prevents code interception'"
    },
    "loops_alts": {
      "enabled": "{argument name=\"loops_alts_enabled\" default=\"false\"}",
      "rule": "可用 UML alt / loop 框：圆角矩形包围多条消息，左上角标 'alt' / 'loop' + 条件文本"
    }
  },
  "legend": {
    "enabled": true,
    "position": "bottom-right",
    "content": "actor type → color, message style → meaning (sync solid arrow / async hollow / return dashed / self bracket)",
    "style": "small panel, semi-transparent bg, mono 10pt"
  },
  "constraints": {
    "must_keep": [
      "actor headers 等大小、等间距、水平对齐",
      "lifelines 垂直、等间距",
      "messages 严格按时间从上到下排列",
      "每条 message 有编号 + 简洁标签",
      "sync / return / async 用不同箭头风格区分",
      "暗色 grid 背景 + 等宽字体",
      "legend 必画"
    ],
    "avoid": [
      "actor header 大小不一",
      "messages 不按时间顺序",
      "self-call 画成水平直线（必须 bracket / loop 形）",
      "return 用实线箭头（破坏语义）",
      "label 与 lifeline 重叠",
      "用 emoji 当 actor 图标",
      "actor > 6 个（拥挤；考虑拆分）",
      "messages > 15 条（视觉爆炸；考虑分子时序）",
      "声称这是可编辑 SVG"
    ]
  }
}
```

### 参数策略

- **必问**：`title`、actors 列表、messages 序列（含 from/to/label/type）
- **可默认**：`activation_bars_enabled`（true）、`type_color_map`、`notes_enabled`（false）、`loops_alts_enabled`（false）
- **可随机**：actor icon glyph 具体造型、消息标签字号微调

### 自动补全策略

- 用户给"我要画 OAuth 流程" → 默认 4 actor + 10 消息（用户 → web → auth → resource）
- 用户没说 sync / async → 默认 sync；明显的回调 / 通知场景默认 async
- 用户说"含失败重试" → 启用 `loops_alts_enabled` + alt block 包围
- 用户说"加注释解释" → 启用 `notes_enabled`
- 用户说要 light 模式 → 用变体 1

## 变体 1：浅色 Light 时序图

```json
{
  "modify": {
    "background": "warm off-white #F8FAFC + faint grid #E2E8F0",
    "actor_header_fill": "type color × 8% opacity",
    "actor_header_border": "1.5px solid (deeper shade for white bg)",
    "label_color": "deep slate #0F172A",
    "lifeline_color": "slate #94A3B8 dashed",
    "vibe": "白底文档 / 印刷版友好"
  }
}
```

## 变体 2：协议握手 / OAuth / 鉴权专用风

```json
{
  "modify": {
    "messages_emphasis": "为安全 / token 类消息加 🔒 等价 glyph 或 'TLS' / 'signed' 小标签",
    "extras": "在 message 上额外标 HTTP method（GET/POST/PUT），加微小 mono 标签",
    "annotation": "加 PKCE / nonce / state 解释 note，notes_enabled = true",
    "use_case": "OAuth 2.0 / OIDC / SAML / mTLS 等协议"
  }
}
```

适用：协议教学、鉴权流程文档。

## 变体 3：分布式事务 / Saga / 2PC 风

```json
{
  "modify": {
    "actor_types": "通常 4-5 个 service actor + 1 个 coordinator + 1 个 message broker",
    "messages_emphasis": "明确标 prepare / commit / rollback / compensate 阶段，用不同颜色 (commit 绿、rollback 红、prepare 蓝)",
    "loops_alts_enabled": true,
    "alt_blocks": "alt 'commit phase' / 'rollback phase' 包围相应消息",
    "use_case": "Saga / 2PC / TCC / outbox pattern 教学和文档"
  }
}
```

适用：分布式事务模式教学、架构 review、failure mode 分析。

## 避免事项

- 时序图但 messages 不按时间从上到下 → 失去时序性
- 用菱形 / 圆形当 actor（必须矩形 header）
- self-call 画成直线（必须 bracket）
- return 用实线（与 sync 混淆）
- actor > 6 → 视觉拥挤，考虑拆分
- messages > 15 → 视觉爆炸
- 用 emoji 当 actor 图标
- 把 actor 头像做成卡通人物 → 失去工程感
- 没有 activation 条 → 看不出谁在处理
- 没有 message 编号（教学场景必须有）
- 把"流程图"画成时序图（节点应该是动作而非 actor）
