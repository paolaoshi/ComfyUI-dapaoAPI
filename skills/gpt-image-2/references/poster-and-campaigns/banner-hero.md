# Web Banner / Hero 模板

本文件用于生成“网页顶部 hero 区 / app banner / 投放素材”视觉：

- 网站首页 hero
- 落地页 banner
- App 顶部活动 banner
- 邮件 marketing banner
- 信息流广告素材

特征：

- 横向比例（16:9 / 21:9 / 3:1）
- 一句强 claim
- 留出 CTA 区域
- 安全留白（避免裁切关键元素）

## 适用范围

- Web hero
- 落地页 hero
- App banner
- 邮件 banner
- 投放素材

## 何时使用

- 用户提到“banner / hero / 落地页主图 / 顶部图”
- 用户需要横向构图 + CTA 区

不要使用：

- 竖图 / 方图主海报（用 `brand-poster.md`）
- 系列 KV（用 `campaign-kv.md`）
- 杂志封面（用 `editorial-cover.md`）

## 缺失信息优先提问顺序

1. 用途（web hero / app banner / 邮件）
2. 主题 / claim
3. 主视觉
4. CTA 文案 + 颜色
5. 品牌色
6. 比例

## 主模板：Web hero banner

📖 描述

整体横向构图，左侧为标题 + 副标题 + CTA，右侧为主视觉，底部安全留白。

📝 提示词

```json
{
  "type": "Web hero banner",
  "goal": "生成一张可直接作为产品官网 / 营销落地页 hero 区主图的横向 banner",
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"16:9\"}",
  "layout": {
    "left_column": {
      "headline": "{argument name=\"headline\" default=\"重新定义你的工作节奏\"}",
      "subhead": "{argument name=\"subhead\" default=\"AURORA Pro · 让 AI 替你处理 80% 的琐事\"}",
      "cta": {
        "text": "{argument name=\"cta text\" default=\"免费试用\"}",
        "color": "{argument name=\"cta color\" default=\"品牌主色\"}",
        "secondary": "{argument name=\"secondary cta\" default=\"了解更多\"}"
      }
    },
    "right_column": {
      "centerpiece": "{argument name=\"hero visual\" default=\"产品截图 + 微微 3D 透视 + 高光\"}",
      "scale": "{argument name=\"hero scale\" default=\"占右侧 80%\"}"
    }
  },
  "background": {
    "type": "{argument name=\"background type\" default=\"浅色渐变\"}",
    "decoration": "{argument name=\"decoration\" default=\"微噪点 + 极淡几何形\"}"
  },
  "brand": {
    "logo_position": "左上角",
    "navigation_hint": "{argument name=\"nav hint\" default=\"顶部导航条已存在，banner 不要画\"}"
  },
  "safe_area": {
    "rule": "底部 10% + 右侧 5% 留白，避免裁切",
    "mobile_consideration": "{argument name=\"mobile aware\" default=\"true\"}"
  },
  "constraints": {
    "must_keep": [
      "headline 字号最大",
      "CTA 必须可点击感（明确按钮形态）",
      "主视觉在右侧不超出安全区",
      "色板严格统一"
    ],
    "avoid": [
      "headline 与主视觉重叠",
      "CTA 颜色与背景对比过低",
      "信息密度过高",
      "主视觉横跨整个画面无 claim 空间"
    ]
  }
}
```

### 参数策略

- 必问：headline、CTA、主视觉、比例
- 可默认：背景、副标题、安全区
- 可随机：装饰几何形

### 自动补全策略

- 用户给产品名时：自动生成 1 句 headline + 1 句 sub + 1 个 CTA
- CTA 默认品牌主色按钮 + 灰色辅助按钮
- 主视觉按行业自动选（SaaS = 截图，消费 = 产品，服务 = 人物）

## 变体 1：纯图大背景 + 浮层文案

📝 提示词

```json
{
  "type": "全屏背景图 hero",
  "background": {
    "type": "全图背景",
    "description": "{argument name=\"background image\" default=\"清晨工作桌面，柔光\"}"
  },
  "layout": {
    "left_column": {
      "headline": "{argument name=\"headline\" default=\"AI 让早晨多出 30 分钟\"}",
      "cta": "立即体验"
    }
  },
  "constraints": {
    "must_feel": "氛围、生活、品牌精神"
  }
}
```

## 变体 2：长横条 banner（21:9 / 3:1）

📝 提示词

```json
{
  "type": "超宽横条 banner",
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"21:9\"}",
  "layout": {
    "left_column": { "headline": "限时 8 折 · 仅限 7 天" },
    "right_column": { "centerpiece": "倒计时数字 + 商品小图" }
  },
  "constraints": {
    "must_feel": "促销、紧迫感、CTA 强烈"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "Banner / hero 自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给产品 + 主题 + 比例，自动生成 headline / CTA / 主视觉 / 安全区",
  "constraints": {
    "must_feel": "可直接上 web / app"
  }
}
```

## 避免事项

- 不要让 headline 和主视觉互相遮挡
- 不要让 CTA 颜色与背景对比 < 4.5:1
- 不要在 banner 上塞 > 3 行正文
- 不要忽略安全留白（移动端裁切会出问题）
- 不要让 banner 横向构图变成纯图（必须有 claim）
