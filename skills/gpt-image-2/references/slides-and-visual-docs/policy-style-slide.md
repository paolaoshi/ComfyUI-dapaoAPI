# 政策 / 政府风说明 Slide 模板

本文件用于生成“政府公告 / 政策解读 / 公共宣传”风格的视觉页：

- 政府政策解读
- 行业白皮书一页摘要
- 公共服务说明
- 法规变更说明
- 通知 / 公告主视觉

特征：

- 严谨克制
- 主标题大、官方感
- 信息分块清晰
- 配色稳重（深蓝 / 深红 / 深绿 + 米色）
- 适当装饰但不喧闹

## 适用范围

- 政策解读图
- 政府公告主图
- 行业白皮书摘要图
- 法规变更说明图
- 公共宣传海报式 Slide

## 何时使用

- 用户提到“政策解读 / 政府公告 / 白皮书 / 公共宣传 / 严谨说明”
- 用户希望视觉看起来“权威、严肃、不娱乐化”

不要使用：

- 用户要的是讲解课件（用 `dense-explainer-slides.md`）
- 用户要的是商业报告（用 `visual-report-page.md`）
- 用户要的是科普教学（用 `educational-diagram-slide.md`）

## 缺失信息优先提问顺序

1. 主题（政策名 / 公告名 / 法规名）
2. 颁布单位 / 发布机构
3. 核心内容章节（3-5 节）
4. 关键数字或日期
5. 配色：政红 / 政蓝 / 政绿 / 中性灰
6. 是否需要二维码 / 联系方式

## 主模板：政策解读单页 Slide

📖 描述

整体页面：顶部官方 logo / 机构名 + 主标题 + 副标题；中间多个分块说明 + 数据高亮；底部出处 / 二维码 / 发布时间。

📝 提示词

```json
{
  "type": "政策解读单页 Slide",
  "goal": "生成一张严谨、权威、可作为政府公告 / 政策解读用途的视觉页",
  "style": {
    "color_palette": "{argument name=\"color palette\" default=\"政红 + 米白 + 深灰\"}",
    "tone": "{argument name=\"visual tone\" default=\"严谨、克制、官方\"}",
    "typography": "{argument name=\"typography\" default=\"思源宋体大标题 + 思源黑体正文\"}"
  },
  "header": {
    "agency_name": "{argument name=\"agency name\" default=\"国家某某局\"}",
    "agency_logo": "{argument name=\"agency logo\" default=\"国徽 / 机构徽\"}",
    "main_title": "{argument name=\"main title\" default=\"关于推进某行业高质量发展的指导意见\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"政策核心要点解读\"}",
    "release_date": "{argument name=\"release date\" default=\"2026 年 4 月 24 日\"}"
  },
  "sections": {
    "count": "{argument name=\"section count\" default=\"5\"}",
    "items": [
      "{argument name=\"section 1\" default=\"政策背景\"}",
      "{argument name=\"section 2\" default=\"主要目标\"}",
      "{argument name=\"section 3\" default=\"重点任务\"}",
      "{argument name=\"section 4\" default=\"保障措施\"}",
      "{argument name=\"section 5\" default=\"实施时间表\"}"
    ],
    "section_block_style": "编号 + 标题 + 2-3 行说明，可附小图标"
  },
  "highlight_numbers": {
    "enabled": "{argument name=\"highlight numbers enabled\" default=\"true\"}",
    "items": [
      "{argument name=\"key number 1\" default=\"5 大重点任务\"}",
      "{argument name=\"key number 2\" default=\"3 年实施周期\"}",
      "{argument name=\"key number 3\" default=\"覆盖 28 个领域\"}"
    ]
  },
  "footer": {
    "source": "{argument name=\"source\" default=\"来源：官方文件全文链接\"}",
    "qr_code": "{argument name=\"qr code\" default=\"右下角二维码：查看政策原文\"}"
  },
  "constraints": {
    "must_keep": [
      "主标题字号最大",
      "机构 logo 与名称必须出现且可读",
      "色板克制 ≤ 3 色",
      "数据高亮区视觉突出但不浮夸"
    ],
    "avoid": [
      "出现娱乐化字体",
      "插图过度卡通化",
      "出现品牌广告元素",
      "颜色过度饱和"
    ]
  }
}
```

### 参数策略

- 必问：政策名、机构、章节
- 可默认：色板、字体方案、底部信息
- 可随机：装饰小图标

### 自动补全策略

- 默认章节按“背景 / 目标 / 任务 / 保障 / 时间表”五段
- 默认色板政红 + 米白 + 深灰
- 默认机构样式留白通用化，避免冒充真实机构

## 变体 1：公共宣传海报式 Slide

📝 提示词

```json
{
  "type": "公共宣传海报式 Slide",
  "header": {
    "main_title": "{argument name=\"main title\" default=\"全民垃圾分类·从我做起\"}",
    "subtitle": "权威指引 + 行动指南"
  },
  "centerpiece": {
    "description": "{argument name=\"centerpiece\" default=\"四种垃圾桶 + 简洁分类图标\"}"
  },
  "sections": {
    "items": [
      "可回收物",
      "厨余垃圾",
      "有害垃圾",
      "其他垃圾"
    ]
  },
  "constraints": {
    "must_feel": "公益、清晰、易懂"
  }
}
```

## 变体 2：白皮书摘要 Slide

📝 提示词

```json
{
  "type": "行业白皮书摘要 Slide",
  "header": {
    "main_title": "{argument name=\"report name\" default=\"2026 年某行业发展白皮书\"}"
  },
  "sections": {
    "items": ["市场概况", "趋势洞察", "关键数据", "未来展望"]
  },
  "highlight_numbers": {
    "enabled": true,
    "items": ["市场规模 1.2 万亿", "复合增长 18%", "活跃企业 4500+"]
  },
  "constraints": {
    "must_feel": "专业、可作为公开发布材料"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "政策风 Slide 自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给主题，自动选机构样式、章节切分、色板",
  "constraints": {
    "must_feel": "权威、克制、可分发"
  }
}
```

## 避免事项

- 不要冒充任何真实机构 logo
- 不要使用娱乐化字体（毛笔体、卡通体除特殊场合）
- 不要让插图分散注意力
- 不要让颜色超过 3 种主色
- 不要让正文行距过密以至无法阅读
- 不要在政策风 Slide 上加过多营销卡片
