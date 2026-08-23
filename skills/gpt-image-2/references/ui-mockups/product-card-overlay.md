# 商品卡叠加样机模板

本文件用于生成“以人物 / 场景图为底，叠加商品卡 / 营销 UI 元素”的电商样机。

它跟 `live-commerce-ui.md` 的区别是：

- `live-commerce-ui.md`：仿真直播平台界面，强调聊天区 / 礼物区 / 平台 UI
- 本模板：偏向“商品 + 模特 / 商品 + 场景 + 卖点卡”的产品营销视觉，更接近落地页 hero 区或电商详情页主图

## 适用范围

- 电商详情页主图样机
- 落地页 hero section
- 朋友圈 / 公众号配图带商品卡
- 单图广告：人物 + 商品卡 + 卖点徽章
- 模特拿着商品 + 信息卡叠加

## 何时使用

- 用户要的是“一张图能讲清楚商品是什么 / 卖点是什么 / 价格是多少”
- 用户提到“详情页主图 / 投放图 / hero 图 / 落地页样机”
- 用户希望既有真实人物视觉，又有电商信息层

不要使用：

- 用户要的是真实直播间截图（用 `live-commerce-ui.md`）
- 用户要的是纯白底产品图（用 `product-visuals/white-background-product.md`）

## 缺失信息优先提问顺序

1. 商品是什么（名称 + 类目）
2. 主体来源：真人模特照片、模特描述、抽象“无人”场景
3. 是否要展示价格 / 卖点 / 徽章
4. 风格：日式简洁 / 极客科技 / 暖色生活方式 / 高级影棚 / 街头时尚
5. 配色主调
6. 文案语种：中文 / 英文 / 日文 / 双语

## 主模板：人物 + 商品卡 + 卖点叠加

📖 描述

生成一张电商落地页 hero 区视觉，结构稳定为：左侧文案 + 中间产品 + 右侧模特 / 场景。

📝 提示词

```json
{
  "type": "电商落地页 hero 商品卡叠加样机",
  "goal": "生成一张能直接当作电商详情页主视觉或营销落地页 hero 区使用的图，包含人物、产品、卖点、价格信息四要素",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"DERMA CALM\"}",
    "subtext": "{argument name=\"brand subtext\" default=\"敏感肌专研\"}"
  },
  "color_palette": {
    "base": "{argument name=\"base color\" default=\"白\"}",
    "primary": "{argument name=\"primary color\" default=\"深蓝\"}",
    "accent": "{argument name=\"accent color\" default=\"浅蓝\"}"
  },
  "layout": {
    "header": {
      "logo": "左侧品牌名 + 副标题",
      "navigation_links": "{argument name=\"nav links\" default=\"ABOUT, PRODUCT, FEATURE, INGREDIENT, VOICE, Q&A\"}",
      "cta_buttons": "{argument name=\"cta buttons\" default=\"我的页面, 立即购买\"}"
    },
    "hero": {
      "left_column": {
        "headline": "{argument name=\"main headline\" default=\"敏感肌也能每天安心使用的温和护理\"}",
        "subtext": "{argument name=\"sub headline\" default=\"低刺激 · 持久保湿 · 无香料 · 无酒精\"}",
        "buttons": ["立即购买", "了解详情"]
      },
      "center_column": {
        "product": "{argument name=\"product description\" default=\"白色按压瓶，瓶身印 'Moisture Barrier Serum'\"}",
        "props": [
          "白色乳液质感液滴特写",
          "圆形 '皮肤科医生监修' 徽章"
        ]
      },
      "right_column": {
        "subject": "{argument name=\"model description\" default=\"东亚年轻女性，皮肤通透，手指轻触脸颊\"}",
        "background": "{argument name=\"background\" default=\"虚化的实验室玻璃器皿背景，明亮干净\"}"
      }
    },
    "bottom_features_panel": {
      "left_cards": {
        "count": "{argument name=\"left feature count\" default=\"3\"}",
        "items": [
          "{argument name=\"feature 1\" default=\"95% 用户给出 5 星好评\"}",
          "{argument name=\"feature 2\" default=\"低刺激配方，盾牌图标\"}",
          "{argument name=\"feature 3\" default=\"水滴图标 + 屏障修护\"}"
        ]
      },
      "right_badges": {
        "count": 3,
        "items": ["无香料", "无酒精", "敏感肌测试通过"]
      },
      "footer": "底部小字免责声明"
    }
  },
  "style": {
    "rendering": "干净、临床感、商业级渲染，看起来像真实落地页截图",
    "consistency": "色板严格按照 base / primary / accent 三色"
  },
  "constraints": {
    "must_keep": [
      "三栏结构清晰",
      "产品作为视觉中心",
      "文案与产品一致",
      "徽章不能比 logo 还大"
    ],
    "avoid": [
      "排版极度拥挤",
      "模特动作显得违和",
      "色板出现额外鲜艳颜色"
    ]
  }
}
```

### 参数策略

- 必问：商品名、品牌名、模特方向、主色
- 可默认：导航文案、按钮文案、徽章文案
- 可随机：底部小字免责声明、卖点措辞具体表述

### 自动补全策略

- 没有给品牌就生成一个简洁的英文品牌名 + 中文副标题
- 没有给模特方向，默认目标用户画像（护肤 -> 年轻女性 / 男士护肤 -> 年轻男性 / 数码 -> 都市年轻人）
- 卖点必须 3 条，互不重复，不空洞

## 变体 1：暗色科技产品落地页

📝 提示词

```json
{
  "type": "暗色科技品牌落地页 hero 样机",
  "theme": "{argument name=\"theme\" default=\"男士护肤 / 数码硬件\"}",
  "color_palette": ["深海军蓝", "白", "蓝色渐变"],
  "header": {
    "logo": "{argument name=\"brand name\" default=\"NEX SKIN\"}",
    "navigation": ["HOME", "PRODUCT", "ABOUT", "FEATURE", "FAQ"],
    "cta_button": "立即开始 >"
  },
  "hero": {
    "left_column": {
      "headline": "{argument name=\"main headline\" default=\"清爽感，从每日护理开始\"}",
      "sub_headline": "男士肌肤，更需要简单",
      "feature_highlights": [
        "去油控亮：调节皮脂",
        "保湿：长时间润泽",
        "一瓶搞定：化妆水 + 精华 + 乳液"
      ]
    },
    "center_image": {
      "subject": "{argument name=\"model\" default=\"清爽干练的亚洲年轻男性\"}",
      "pose": "手部托腮思考"
    },
    "right_column": {
      "product_shot": "{argument name=\"product\" default=\"高瘦的深蓝色瓶身，瓶身带水珠\"}"
    }
  },
  "bottom_stats_bar": {
    "items": [
      "累计销量 120 万瓶",
      "满意度 92.1%",
      "复购率 85.3%"
    ]
  },
  "constraints": {
    "must_feel": "硬朗、专业、可信赖"
  }
}
```

## 变体 2：四格人物 + 商品卡集合

适合一张图覆盖多个人群 / 场景。

📝 提示词

```json
{
  "type": "四格人物-商品卡集合样机",
  "layout": "2x2 网格，每格独立人物 + 独立商品卡",
  "quadrants": [
    {
      "position": "左上",
      "industry": "护肤",
      "subject": "亚洲女性轻触脸颊",
      "product": "白色按压瓶",
      "headline": "{argument name=\"q1 headline\" default=\"素肌觉醒\"}"
    },
    {
      "position": "右上",
      "industry": "餐饮",
      "subject": "意大利肉酱面特写",
      "product": "餐厅 logo + 限定上市标识",
      "headline": "{argument name=\"q2 headline\" default=\"这碗面，事件级\"}"
    },
    {
      "position": "左下",
      "industry": "旅行",
      "subject": "背包女性面对高山湖泊",
      "product": "旅行品牌 + 折扣 banner",
      "headline": "{argument name=\"q3 headline\" default=\"出发，让自己自由\"}"
    },
    {
      "position": "右下",
      "industry": "SaaS 应用",
      "subject": "手机展示任务管理 App 界面",
      "product": "应用品牌 + 7 天免费试用",
      "headline": "{argument name=\"q4 headline\" default=\"让任务管理更简单\"}"
    }
  ],
  "constraints": {
    "must_feel": "像同一品牌矩阵或同一广告 campaign 出品"
  }
}
```

## 变体 3：自动补全模式

适合用户只说“做一张电商落地页主图”。

📝 提示词

```json
{
  "type": "落地页商品卡叠加自动补全模板",
  "mode": "auto-fill",
  "rule": "在主模板基础上，自动补齐品牌名、文案、模特方向，但保持四要素：品牌、人物、商品、卖点都齐",
  "constraints": {
    "must_feel": "真实电商投放图",
    "avoid": "看起来像 PPT"
  }
}
```

## 避免事项

- 不要让人物表情过于夸张或假笑（会立刻破坏可信度）
- 卖点徽章 ≤ 3-4 个，多了会变成广告噪音
- 文案颜色不能与底图过于接近，否则不可读
- 商品在画面中必须有清晰主光，不能跟模特一起虚化
- 不要让中文 + 英文 + 日文同时占据同等大小，必须有主导语种
