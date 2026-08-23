# 网络拓扑图模板

> ⚠️ **本模板生成的是位图（PNG）**，不是 NetBox / Cisco Packet Tracer / draw.io 可编辑网络拓扑。
> 需要可编辑请用 NetBox / Lucidchart / draw.io / Cisco Packet Tracer。

本文件用于生成"工程感网络拓扑图"：

- 公司 / 数据中心 网络拓扑
- 多区域 / 多 zone 部署拓扑
- 微服务 / 服务网格 拓扑
- VPC / 子网 / 路由表拓扑
- 边缘 / CDN / 多云互联拓扑

特征：

- 设备节点用类型化 glyph：路由器（菱形交叉）/ 交换机（矩形多端口）/ 服务器（带散热条小机箱）/ 防火墙（砖墙）/ 云（云朵）/ DB（圆柱）
- 物理连线用粗线，逻辑连线用虚线
- 大虚线框包围 zone / VLAN / VPC
- 带宽 / 协议标在线上（如 "10 Gbps" / "BGP" / "TLS 1.3"）
- 暗色 grid + 等宽字体（沿用视觉系统）

## 适用范围

- 数据中心 / 机房网络拓扑
- 云架构网络拓扑（VPC / subnet / NAT / IGW）
- 多区域 / 多云互联
- 服务网格拓扑（service mesh）
- 边缘 / CDN / 公网入口拓扑

## 何时使用

- 用户提到 "网络拓扑 / network topology / 部署拓扑 / VPC / 子网 / 数据中心 / 机房 / 服务网格"
- 用户希望「带网络设备 glyph + 区域分组 + 连线带宽标注」标准网络图
- 用户接受位图

不要使用：

- 用户要的是「应用层系统架构」 → 用 `technical-diagrams/system-architecture.md`
- 用户要的是「业务流程」 → 用 `technical-diagrams/flowchart-decision.md`
- 用户要的是「时序图」 → 用 `technical-diagrams/sequence-diagram.md`

## 缺失信息优先提问顺序

1. 拓扑名称（"AWS VPC 拓扑 / 公司机房拓扑 / 多区域部署"）
2. 主要 zones / subnets / VPCs（建议 2-5 个区域）
3. 每个区域内的设备 / 实例（路由器 / 交换机 / 服务器 / DB / 负载均衡）
4. 区域间的连接（VPN / Peering / IGW / Direct Connect）
5. 连线的协议 / 带宽（可选）
6. 是否标 IP 段 / CIDR
7. 比例（默认 16:9 横版）

## 主模板：标准云 / 数据中心 网络拓扑图

📖 描述

整张图按 zone / VPC 划分大虚线框区域，每个区域内放设备节点（带类型化 glyph），节点间用粗线连接（标带宽 / 协议），跨区域连接用专门的网关 / VPN 节点。整体在暗色 grid 背景上呈现工程感。

📝 提示词

```json
{
  "type": "工程感网络拓扑图",
  "goal": "生成一张工程感网络拓扑图作为部署文档 / 网络架构 review / 培训材料",
  "canvas": {
    "aspect_ratio": "{argument name=\"aspect_ratio\" default=\"16:9\"}",
    "background": "deep slate #0F172A with subtle 1px grid #1E293B at 32px spacing",
    "outer_padding": "60px"
  },
  "title_strip": {
    "title": "{argument name=\"title\" default=\"AWS Multi-AZ VPC Topology\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"production · ap-northeast-1\"}",
    "position": "top-left, JetBrains Mono / SF Mono, light gray"
  },
  "device_glyphs": {
    "rule": "每种设备使用统一的极简几何 glyph，避免使用真实厂商图标",
    "types": [
      { "type": "router", "glyph": "diamond shape with X cross inside", "color": "amber #FBBF24" },
      { "type": "switch", "glyph": "rectangle with multiple port dots along the bottom edge", "color": "amber #FBBF24" },
      { "type": "firewall", "glyph": "stylized brick wall pattern (small rectangles in 2-3 rows)", "color": "rose #FB7185" },
      { "type": "load_balancer", "glyph": "trapezoid funnel with 3 lines coming in, 1 going out", "color": "blue #60A5FA" },
      { "type": "server", "glyph": "small rack rectangle with 3-4 horizontal slots", "color": "emerald #34D399" },
      { "type": "container", "glyph": "rounded square with sail / shipping container symbol", "color": "emerald #34D399" },
      { "type": "database", "glyph": "cylinder (3D-suggested)", "color": "violet #A78BFA" },
      { "type": "cloud_service", "glyph": "cloud outline with abbreviation inside (e.g. 'S3', 'CDN')", "color": "cyan #22D3EE" },
      { "type": "user", "glyph": "stick figure", "color": "cyan #22D3EE" },
      { "type": "internet", "glyph": "globe with latitude / longitude lines", "color": "slate #94A3B8" },
      { "type": "nat_gateway", "glyph": "small rectangle labeled 'NAT'", "color": "amber #FBBF24" },
      { "type": "vpn_gateway", "glyph": "small rectangle with key icon, labeled 'VPN'", "color": "rose #FB7185" }
    ]
  },
  "zones": {
    "count": "{argument name=\"zone_count\" default=\"4\"}",
    "items": [
      { "id": "Z1", "label": "Public Internet", "color_border": "slate #94A3B8 dashed", "cidr": "0.0.0.0/0" },
      { "id": "Z2", "label": "VPC · ap-northeast-1\\n10.0.0.0/16", "color_border": "amber #FBBF24 dashed", "cidr": "10.0.0.0/16" },
      { "id": "Z3", "label": "Public Subnet · 10.0.1.0/24 (AZ-a)", "color_border": "blue #60A5FA dashed", "parent": "Z2" },
      { "id": "Z4", "label": "Private Subnet · 10.0.2.0/24 (AZ-a)", "color_border": "emerald #34D399 dashed", "parent": "Z2" }
    ],
    "zone_label_position": "top-left of each zone box, mono 11pt with CIDR on second line"
  },
  "nodes": {
    "items": [
      { "id": "N1", "type": "user", "label": "End Users", "zone": "Z1" },
      { "id": "N2", "type": "internet", "label": "Internet", "zone": "Z1" },
      { "id": "N3", "type": "cloud_service", "label": "CloudFront\\n(CDN)", "zone": "Z1" },
      { "id": "N4", "type": "load_balancer", "label": "ALB", "zone": "Z3" },
      { "id": "N5", "type": "nat_gateway", "label": "NAT GW", "zone": "Z3" },
      { "id": "N6", "type": "container", "label": "ECS Tasks\\n(2 instances)", "zone": "Z4" },
      { "id": "N7", "type": "database", "label": "RDS PostgreSQL\\n(Multi-AZ)", "zone": "Z4" },
      { "id": "N8", "type": "cloud_service", "label": "S3\\n(static assets)", "zone": "Z1" }
    ],
    "node_label_format": "device name + optional second line with detail (count / class / role)，mono 10pt 标在 glyph 下方"
  },
  "connections": {
    "items": [
      { "from": "N1", "to": "N2", "type": "physical", "label": "" },
      { "from": "N2", "to": "N3", "type": "physical", "label": "HTTPS / TLS 1.3" },
      { "from": "N3", "to": "N4", "type": "physical", "label": "Origin pull" },
      { "from": "N4", "to": "N6", "type": "physical", "label": "HTTP" },
      { "from": "N6", "to": "N7", "type": "physical", "label": "TCP 5432" },
      { "from": "N6", "to": "N5", "type": "physical", "label": "egress" },
      { "from": "N5", "to": "N2", "type": "physical", "label": "" },
      { "from": "N3", "to": "N8", "type": "physical", "label": "Origin pull" }
    ],
    "line_style": {
      "physical": "solid line 2px slate #94A3B8 (carries actual traffic)",
      "logical": "dashed line 1.5px slate #64748B (logical relation, e.g. 'IAM allows access')",
      "redundant": "double-line in violet #A78BFA (HA pair, redundant link)",
      "encrypted": "solid line 2px emerald #34D399 with small lock glyph in middle"
    },
    "label_format": "protocol + optional bandwidth, e.g. 'HTTPS / 443' / '10 Gbps' / 'BGP' / 'TLS 1.3'，mono 9pt 标在线中央",
    "rule_routing": "正交走线为主；跨 zone 时穿过 zone 边界画"
  },
  "annotations": {
    "ip_cidr_labels": {
      "enabled": "{argument name=\"ip_labels_enabled\" default=\"true\"}",
      "rule": "每个 zone 标 CIDR；关键节点标 IP 或 hostname"
    },
    "az_labels": {
      "enabled": "{argument name=\"az_labels_enabled\" default=\"true\"}",
      "rule": "云环境下标可用区 (AZ-a / AZ-b)"
    }
  },
  "legend": {
    "enabled": true,
    "position": "bottom-right",
    "content": "device glyph → device type，line style → connection type (physical / logical / redundant / encrypted)，zone color → zone type",
    "style": "small panel, semi-transparent bg, mono 10pt"
  },
  "constraints": {
    "must_keep": [
      "每种设备 glyph 一致，不混用",
      "zone 用大虚线框清晰包围",
      "zone 标签含 CIDR / AZ（云环境）或 VLAN ID（数据中心）",
      "连线粗细 / 颜色编码反映连接类型",
      "暗色 grid 背景 + 等宽字体",
      "legend 必画"
    ],
    "avoid": [
      "用真实厂商 logo (Cisco / AWS / Azure 真实图标) → 容易侵权 + 破坏统一视觉",
      "设备 glyph 不一致 (一个用方框一个用真实图标)",
      "用 emoji 当设备图标",
      "zone 不用虚线框 → 失去区域感",
      "连线无 protocol 标 → 失去工程价值",
      "节点 > 15 个 → 拥挤，考虑分子图",
      "用 3D / 渐变 / 玻璃质感",
      "声称这是可编辑 SVG"
    ]
  }
}
```

### 参数策略

- **必问**：`title`、zones 列表（含 CIDR / 名称）、nodes 列表（含 type + zone）、connections（含 from/to）
- **可默认**：`background`（暗色 grid）、`device_glyphs`（默认全套）、`ip_labels_enabled`（true）、`az_labels_enabled`（true）
- **可随机**：节点摆放位置（在 zone 内自动布局）

### 自动补全策略

- 用户给"AWS 单 AZ VPC + ALB + ECS + RDS" → 用 default 拓扑
- 用户没给 CIDR → 反问（不能瞎编 IP 段）
- 用户说"加多 AZ HA" → 复制 private subnet 到 AZ-b，标 redundant 连线
- 用户说"加 WAF / Shield" → 在 ALB 前加 firewall glyph
- 用户说要 light 模式 → 用变体 1

## 变体 1：浅色 Light 网络拓扑

```json
{
  "modify": {
    "background": "warm off-white #F8FAFC + faint grid #E2E8F0",
    "node_glyph_fill": "device color × 8% opacity",
    "node_glyph_border": "1.5px solid (deeper shade for white bg)",
    "label_color": "deep slate #0F172A",
    "zone_border_color": "deeper shade",
    "vibe": "白底文档 / 印刷版"
  }
}
```

## 变体 2：服务网格 (Service Mesh) 拓扑

```json
{
  "modify": {
    "title_format": "Service Mesh Topology",
    "node_emphasis": "每个 service node 旁边贴一个小 sidecar (proxy) glyph，表达 sidecar 模式",
    "connections_emphasis": "service-to-service 连线全部经过 sidecar；标 mTLS 加密",
    "extras": "可加 control plane node (Istio / Linkerd) 在右上角，连线用虚线表示控制流",
    "use_case": "Istio / Linkerd / Consul / Cilium service mesh 文档"
  }
}
```

适用：服务网格架构、零信任网络、SRE 培训材料。

## 变体 3：多云互联拓扑（hybrid cloud）

```json
{
  "modify": {
    "zones": "横向并排画多个云的大框：'AWS Region' + 'GCP Region' + 'On-Prem DC'",
    "interconnect": "云间用 'Direct Connect' / 'Cloud Interconnect' / 'VPN' 粗连线连接，标带宽 / SLA",
    "extras": "可加 transit gateway / 中央 routing hub 在画布中央",
    "use_case": "混合云 / 多云架构、灾备拓扑、迁移规划"
  }
}
```

适用：混合云架构、多云部署、灾备 / DR 拓扑。

## 避免事项

- 用真实厂商图标（容易侵权）
- 设备 glyph 不一致（同一种设备用不同形状）
- 用 emoji 当设备图标
- zone 没有虚线框 → 失去区域感
- 连线无 protocol / 带宽标 → 失去工程价值
- 节点 > 15 → 视觉爆炸
- 用 3D / 渐变 / 玻璃质感（破坏工程感）
- 中央 hub-and-spoke 但中心节点没标"作什么"
- 把"应用层"组件塞进网络拓扑（应该用 system-architecture）
- 假装这是可导出可编辑的 SVG
- IP / CIDR 信息缺失（云环境网络图核心信息）
