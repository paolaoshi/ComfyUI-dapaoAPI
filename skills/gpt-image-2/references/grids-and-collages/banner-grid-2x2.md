# 2×2 营销 Banner 网格模板

本文件用于"一张图里 4 个独立 banner，统一系列设计"的视觉：

- 在线教育课程系列 banner
- 培训 / 招生 banner
- 品牌活动多场景 banner
- SNS / 朋友圈广告四件套

特征：

- 2×2 等大网格
- 每格是一个独立 banner（带主标题 + 视觉 + CTA）
- 4 个 banner 风格统一但内容差异
- 每个 banner 可单独裁切发布

## 适用范围

- 教育 / 培训 banner 系列
- 品牌 SNS 套装
- 活动多场景广告
- A/B 测试候选稿

## 何时使用

- 用户提到"banner 系列 / 课程 banner / 4 张广告"
- 用户希望一次出 4 个一致风格的 banner
- 用户需要 SNS 投放素材

不要使用：

- 一张完整大 banner（用 `poster-and-campaigns/banner-hero.md`）
- 多面板叙事（用 `storyboards-and-sequences/four-panel-comic.md`）
- 头像网格（用 `avatars-and-profile/character-grid-portrait.md`）

## 缺失信息优先提问顺序

1. 主题 / 业务（教育 / 电商 / 品牌活动）
2. 4 个 banner 分别推什么
3. 每个 banner 的核心人物 / 道具
4. 品牌色 / 品牌字
5. 是否需要 logo / CTA
6. 比例（1:1 / 4:5 / 16:9 各 banner 内）

## 主模板：2×2 课程 / 教育 banner 套装

📖 描述

整体一张图，2×2 四个独立 banner，每个 banner 推一个课程，共享品牌色与 logo 区。

📝 提示词

```json
{
  "type": "2x2 课程 banner 套装",
  "goal": "生成一组 4 张统一风格的课程 banner，可单独裁切投放 SNS / 公众号顶部",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"星海学堂\"}",
    "logo_position": "{argument name=\"logo position\" default=\"每个 banner 左上角\"}",
    "primary_color": "{argument name=\"primary color\" default=\"#FF6B35\"}",
    "secondary_color": "{argument name=\"secondary color\" default=\"#0F4C81\"}"
  },
  "layout": {
    "format": "2x2 grid",
    "panel_count": 4,
    "gap": "16px 白色分隔",
    "panel_aspect_ratio": "{argument name=\"panel aspect\" default=\"4:5\"}",
    "overall_aspect_ratio": "1:1"
  },
  "panels": [
    {
      "position": "top-left",
      "course": "{argument name=\"course 1\" default=\"少儿编程\"}",
      "headline": "{argument name=\"headline 1\" default=\"6 岁就能学的 Scratch\"}",
      "visual": "{argument name=\"visual 1\" default=\"卡通男孩在屏幕前敲键盘\"}",
      "cta": "{argument name=\"cta 1\" default=\"立即试听\"}"
    },
    {
      "position": "top-right",
      "course": "{argument name=\"course 2\" default=\"少儿英语\"}",
      "headline": "{argument name=\"headline 2\" default=\"和外教自然对话\"}",
      "visual": "{argument name=\"visual 2\" default=\"卡通女孩戴耳机说英文\"}",
      "cta": "{argument name=\"cta 2\" default=\"领取试听课\"}"
    },
    {
      "position": "bottom-left",
      "course": "{argument name=\"course 3\" default=\"少儿数学\"}",
      "headline": "{argument name=\"headline 3\" default=\"思维训练 1v1\"}",
      "visual": "{argument name=\"visual 3\" default=\"卡通孩子在白板做题\"}",
      "cta": "{argument name=\"cta 3\" default=\"领取诊断\"}"
    },
    {
      "position": "bottom-right",
      "course": "{argument name=\"course 4\" default=\"少儿美术\"}",
      "headline": "{argument name=\"headline 4\" default=\"每周一幅作品\"}",
      "visual": "{argument name=\"visual 4\" default=\"卡通孩子在画画\"}",
      "cta": "{argument name=\"cta 4\" default=\"在线报名\"}"
    }
  ],
  "style": {
    "art_style": "{argument name=\"art style\" default=\"扁平卡通 + 圆润\"}",
    "typography": "中文圆体 + 英文 sans"
  },
  "constraints": {
    "must_keep": [
      "4 个 banner 共享同一品牌色与 logo 风格",
      "每个 banner 单独看也成立",
      "标题 ≤ 12 字 / 行",
      "CTA 按钮位置统一"
    ],
    "avoid": [
      "4 个 banner 风格漂移",
      "标题字号差异过大",
      "CTA 措辞不统一",
      "视觉元素塞太满"
    ]
  }
}
```

### 参数策略

- 必问：品牌名、4 个推广内容
- 可默认：品牌色、风格、layout
- 可随机：每个 visual 具体造型

### 自动补全策略

- 用户给品牌 + 4 个产品时：自动展开 4 个 headline + visual + CTA
- 默认 2×2 + 16px 白色分隔
- CTA 措辞自动按业务类型选

## 变体 1：电商商品 banner 套装

📝 提示词

```json
{
  "type": "电商商品 banner 套装",
  "panels": [
    {"course": "新品", "headline": "限时首发", "cta": "立即购买"},
    {"course": "热销", "headline": "TOP 1 爆款", "cta": "查看"},
    {"course": "回购", "headline": "老顾客好评", "cta": "回购优惠"},
    {"course": "组合", "headline": "买二送一", "cta": "立即下单"}
  ],
  "constraints": {
    "must_feel": "电商感 + 转化导向"
  }
}
```

## 变体 2：活动多场景 banner 套装

📝 提示词

```json
{
  "type": "活动多场景 banner 套装",
  "brand": {
    "name": "{argument name=\"event\" default=\"618 大促\"}"
  },
  "panels": [
    {"headline": "预热"},
    {"headline": "开抢"},
    {"headline": "爆款"},
    {"headline": "返场"}
  ],
  "constraints": {
    "must_feel": "活动统一视觉系统"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "2x2 banner 自动补全",
  "mode": "auto-fill",
  "rule": "用户给品牌 + 一句业务描述，自动决定 4 张 banner 主题 + 设计",
  "constraints": {
    "must_feel": "可直接投放"
  }
}
```

## 避免事项

- 不要让 4 个 banner 风格漂移
- 不要让标题字号 / 字体不统一
- 不要让 CTA 位置不一致
- 不要让 logo 出现在不同位置
- 不要让单个 banner 元素塞 > 5 个
