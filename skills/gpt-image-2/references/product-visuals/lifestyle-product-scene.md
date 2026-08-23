# 生活方式产品场景图模板

本文件用于生成“商品出现在真实生活场景中”的视觉：

- 桌面工作场景中的笔记本电脑
- 海边度假桌上的饮料
- 咖啡馆桌上的拿铁
- 早晨梳妆台前的护肤品
- 宿舍床上的耳机
- 户外露营场景下的装备

强调：

- 商品在场景中“被使用 / 准备使用 / 刚被使用”
- 真实生活气息
- 自然光或柔和光为主
- 适度道具，但不喧宾夺主

它跟 `premium-studio-product.md` 的区别：

- 影棚图：纯氛围、纯产品、戏剧光、无场景
- 生活方式图：真实场景、自然光、可有人物局部（手、背影）

跟 `product-card-overlay.md` 的区别：

- product-card-overlay：电商详情页 hero，必须有 UI 卡 / 文案叠加
- 本模板：纯摄影场景图，不强求 UI

## 适用范围

- 品牌官网首屏
- 营销 banner 主视觉
- Instagram / 小红书 / 朋友圈封面图
- 内容化电商素材
- 节日促销场景图
- 杂志风格生活方式封面

## 何时使用

- 用户提到“场景图 / 生活方式 / lifestyle / 真实场景 / 杂志感”
- 用户希望商品看起来“有人在用”
- 用户希望视觉自然不商业化

不要使用：

- 用户要电商主图（用 `white-background-product.md`）
- 用户要爆炸视图（用 `exploded-view-poster.md`）
- 用户要包装展示（用 `packaging-showcase.md`）
- 用户要纯氛围广告级单品（用 `premium-studio-product.md`）

## 缺失信息优先提问顺序

1. 商品具体是什么
2. 场景：办公桌 / 咖啡馆 / 早晨梳妆台 / 海边 / 户外 / 厨房 / 卧室
3. 时间：清晨、午后、黄昏、夜晚
4. 气候 / 光照：自然光、暖光、阴天柔光、室内灯光
5. 是否包含人物（局部 / 全身 / 背影）
6. 是否需要轻量文案（slogan / hashtag）

## 主模板：单品 + 真实场景

📖 描述

商品摆放在真实生活场景中，自然光为主，可有人物局部（手 / 背影），少量道具增加生活感。

📝 提示词

```json
{
  "type": "生活方式产品场景图",
  "goal": "生成一张商品出现在真实生活场景中的视觉，氛围真实、克制、品质感强，可作为品牌主视觉或社媒封面使用",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"白色按压式精华瓶\"}",
    "visual_description": "{argument name=\"product visual\" default=\"圆肩瓶身，磨砂白瓶，瓶身印 'DERMA CALM'\"}",
    "position": "{argument name=\"product position\" default=\"画面中心略偏右下\"}"
  },
  "scene": {
    "location": "{argument name=\"scene location\" default=\"清晨阳光下的木质梳妆台\"}",
    "time_of_day": "{argument name=\"time of day\" default=\"清晨\"}",
    "weather_or_mood": "{argument name=\"mood\" default=\"清新、柔和、刚醒来的感觉\"}",
    "extra_props": [
      "{argument name=\"prop 1\" default=\"半透明杯里的清水\"}",
      "{argument name=\"prop 2\" default=\"散落的几片白色花瓣\"}",
      "{argument name=\"prop 3\" default=\"折叠的米白色毛巾\"}"
    ]
  },
  "lighting": {
    "type": "{argument name=\"light type\" default=\"自然光\"}",
    "direction": "{argument name=\"light direction\" default=\"侧光，从左侧窗户洒入\"}",
    "intensity": "{argument name=\"light intensity\" default=\"柔和\"}",
    "color_temp": "{argument name=\"color temperature\" default=\"略偏暖\"}"
  },
  "human_presence": {
    "enabled": "{argument name=\"include human\" default=\"true\"}",
    "form": "{argument name=\"human form\" default=\"局部，比如手指轻触瓶身\"}",
    "rule": "若包含人物，必须自然不刻意，不要有完整正脸"
  },
  "text_overlay": {
    "enabled": "{argument name=\"text enabled\" default=\"false\"}",
    "brand": "{argument name=\"brand name\" default=\"\"}",
    "headline": "{argument name=\"headline\" default=\"\"}"
  },
  "style": {
    "rendering": "真实摄影感 + 颗粒感 + 低饱和度，不像广告硬照",
    "depth": "浅景深，主体清晰",
    "consistency": "色调统一，没有突兀的高饱和元素"
  },
  "constraints": {
    "must_keep": [
      "商品是视觉焦点",
      "场景真实可信",
      "光线方向统一",
      "道具与商品同色系"
    ],
    "avoid": [
      "场景看起来是 3D 渲染",
      "人物正脸抢戏",
      "道具喧宾夺主",
      "出现明显的电商广告卡片"
    ]
  }
}
```

### 参数策略

- 必问：商品、场景、是否含人物
- 可默认：时间、灯光、道具
- 可随机：道具具体物件（在色板和场景内合理生成）

### 自动补全策略

- 护肤品默认：清晨梳妆台 + 自然侧光 + 毛巾、花瓣、玻璃杯
- 饮料默认：户外或桌面 + 自然光 + 冰块、柠檬片
- 数码默认：办公桌 + 室内自然光 + 笔记本、咖啡杯
- 户外装备默认：黄昏自然光 + 山野 / 海边 + 简单背景物

## 变体 1：饮品户外场景

📝 提示词

```json
{
  "type": "饮品户外生活方式场景图",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"金色气泡饮料铝罐\"}"
  },
  "scene": {
    "location": "海边木桌",
    "time_of_day": "晴朗午后",
    "extra_props": [
      "高脚杯 + 柠檬装饰",
      "近处水珠铝罐",
      "远处虚化海滩与天空"
    ]
  },
  "lighting": {
    "type": "自然光",
    "direction": "顶光 + 闪光焦外",
    "intensity": "明亮"
  },
  "human_presence": {
    "enabled": true,
    "form": "远处一名女性背影望向大海"
  },
  "text_overlay": {
    "enabled": true,
    "headline": "{argument name=\"headline\" default=\"夏天，就要这一口\"}"
  },
  "constraints": {
    "must_feel": "假期、清凉、自由"
  }
}
```

## 变体 2：办公桌数码场景

📝 提示词

```json
{
  "type": "桌面数码生活方式场景图",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"无线耳机充电盒\"}"
  },
  "scene": {
    "location": "极简北欧风桌面",
    "time_of_day": "上午",
    "extra_props": [
      "笔记本电脑半开",
      "咖啡杯",
      "小植物",
      "翻开的笔记本"
    ]
  },
  "lighting": {
    "type": "室内自然光 + 顶部柔光",
    "direction": "正面偏左",
    "intensity": "明亮均匀"
  },
  "human_presence": {
    "enabled": true,
    "form": "局部手指自然搭在桌上"
  },
  "constraints": {
    "must_feel": "专业、专注、利落"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "生活方式场景图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户只给商品名，自动决定最合适场景、时间、灯光与人物呈现方式，但必须维持商品视觉焦点",
  "constraints": {
    "must_feel": "杂志风、可信、不夸张"
  }
}
```

## 避免事项

- 不要让人物正脸成为主角
- 不要塞超过 4-5 个道具
- 不要让灯光出现“影棚顶光 + 室内自然光”混搭
- 不要让画面饱和度过高，会变成广告硬照
- 不要在生活方式图上叠加电商风的“价格 + 折扣”卡（那是 product-card-overlay 的活）
- 不要让背景出现明显品牌冲突（比如苹果电脑放在友商发布会场景）
