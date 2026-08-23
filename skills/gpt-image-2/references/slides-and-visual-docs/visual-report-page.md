# 商业视觉报告页模板

本文件用于生成“商业报告 / 投资分析 / 增长复盘 / OKR 概览” 风格的视觉单页：

- 商业咨询公司风格
- 投行 / 研究报告
- 公司年报概览
- 投资人简报
- OKR 季度总结

特征：

- 数据驱动
- 表格 + 图表 + 插图混合
- 排版严谨
- 一页能讲清楚一个商业判断

## 适用范围

- 单页 KPI 概览
- 投资人简报封面
- 报告执行摘要页
- 季度业务复盘页

## 何时使用

- 用户提到“报告 / 复盘 / 投资人简报 / KPI / OKR / executive summary”
- 用户需要数据可视化 + 商业判断风格

不要使用：

- 用户要的是政府公告（用 `policy-style-slide.md`）
- 用户要的是讲解课件（用 `dense-explainer-slides.md`）
- 用户要的是科普图（用 `educational-diagram-slide.md`）

## 缺失信息优先提问顺序

1. 报告主题（业务 / 季度 / 项目 / 公司）
2. 关键数据（3-5 个）
3. 关键判断（1 句话结论）
4. 是否需要时间线 / 趋势图
5. 配色：商业蓝 / 黑金 / 暖灰
6. 是否英文 / 中英双语

## 主模板：商业报告执行摘要页

📖 描述

顶部为标题 + 报告期 + logo；中间为关键数据卡 + 趋势小图 + 一句判断；底部为来源 / 备注。

📝 提示词

```json
{
  "type": "商业报告执行摘要页",
  "goal": "生成一张可作为投资人简报、季度报告封面、内部 OKR 复盘的执行摘要视觉单页",
  "style": {
    "color_palette": "{argument name=\"color palette\" default=\"商业蓝 + 灰 + 白\"}",
    "tone": "{argument name=\"visual tone\" default=\"理性、克制、可信赖\"}",
    "typography": "{argument name=\"typography\" default=\"无衬线现代字体 + 数字粗体\"}"
  },
  "header": {
    "company_or_team": "{argument name=\"team name\" default=\"NEX Inc.\"}",
    "report_period": "{argument name=\"period\" default=\"2026 Q1\"}",
    "main_title": "{argument name=\"main title\" default=\"季度业务复盘 · 执行摘要\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"3 项关键数据 + 1 句核心判断\"}"
  },
  "kpi_cards": {
    "count": "{argument name=\"kpi count\" default=\"4\"}",
    "items": [
      {
        "label": "{argument name=\"kpi 1 label\" default=\"营收\"}",
        "value": "{argument name=\"kpi 1 value\" default=\"¥ 12.4 亿\"}",
        "change": "{argument name=\"kpi 1 change\" default=\"+18% YoY\"}"
      },
      {
        "label": "{argument name=\"kpi 2 label\" default=\"活跃用户\"}",
        "value": "{argument name=\"kpi 2 value\" default=\"3,820 万\"}",
        "change": "{argument name=\"kpi 2 change\" default=\"+22% YoY\"}"
      },
      {
        "label": "{argument name=\"kpi 3 label\" default=\"毛利率\"}",
        "value": "{argument name=\"kpi 3 value\" default=\"62.1%\"}",
        "change": "{argument name=\"kpi 3 change\" default=\"+3.4 pp\"}"
      },
      {
        "label": "{argument name=\"kpi 4 label\" default=\"NPS\"}",
        "value": "{argument name=\"kpi 4 value\" default=\"62\"}",
        "change": "{argument name=\"kpi 4 change\" default=\"+8\"}"
      }
    ]
  },
  "trend_chart": {
    "enabled": "{argument name=\"trend chart enabled\" default=\"true\"}",
    "type": "{argument name=\"chart type\" default=\"折线 + 面积\"}",
    "metric": "{argument name=\"chart metric\" default=\"季度营收\"}",
    "x_axis": "Q1-Q4",
    "y_axis": "亿元"
  },
  "core_judgment": {
    "headline": "{argument name=\"core judgment\" default=\"核心增长来自 AI 产品线，需在 Q2 投入更多研发资源\"}"
  },
  "footer": {
    "source": "{argument name=\"source\" default=\"数据来源：内部财务系统\"}",
    "confidentiality": "{argument name=\"confidentiality\" default=\"内部资料 · 仅供讨论\"}"
  },
  "constraints": {
    "must_keep": [
      "数字必须最大、最显眼",
      "趋势图与 KPI 数据一致",
      "核心判断只有一句",
      "色板极简 ≤ 3 色"
    ],
    "avoid": [
      "数据过于堆叠",
      "出现装饰性插画",
      "字体多种类",
      "底色过亮影响数字识别"
    ]
  }
}
```

### 参数策略

- 必问：报告期、主题、关键数据
- 可默认：色板、字体、保密标识
- 可随机：装饰小元素

### 自动补全策略

- 用户只给主题时：自动生成 4 个常见 KPI（营收 / 用户 / 毛利率 / NPS）
- 默认色板商业蓝
- 默认 1 句核心判断使用“因 X，所以 Y”句式

## 变体 1：投资人 pitch 封面

📝 提示词

```json
{
  "type": "投资人 pitch 封面单页",
  "header": {
    "main_title": "{argument name=\"company\" default=\"NEX Inc.\"}",
    "subtitle": "{argument name=\"tagline\" default=\"重新定义 AI 工作流\"}"
  },
  "kpi_cards": {
    "items": [
      "ARR ¥ 1.2 亿",
      "增长 240% YoY",
      "客户 4500+"
    ]
  },
  "core_judgment": {
    "headline": "现在是融资的最佳窗口"
  },
  "constraints": {
    "must_feel": "锐利、自信、未来感"
  }
}
```

## 变体 2：年报概览页

📝 提示词

```json
{
  "type": "公司年报概览页",
  "header": {
    "main_title": "{argument name=\"year\" default=\"2025 年度报告\"}",
    "subtitle": "全年关键成就 + 来年展望"
  },
  "sections": {
    "items": ["全年 KPI", "重要里程碑", "团队成长", "来年规划"]
  },
  "constraints": {
    "must_feel": "克制、有沉淀感"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "商业报告页自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给业务方向 + 报告期，自动生成 KPI / 趋势 / 核心判断",
  "constraints": {
    "must_feel": "可发给投资人 / 高管"
  }
}
```

## 避免事项

- 不要在执行摘要页里塞 > 6 个 KPI
- 不要让趋势图与 KPI 矛盾
- 不要使用花哨字体
- 不要让核心判断超过 2 句
- 不要让背景色过深，会让数字读不清
