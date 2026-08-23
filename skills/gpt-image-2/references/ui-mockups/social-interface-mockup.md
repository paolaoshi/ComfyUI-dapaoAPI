# 社交平台界面样机模板

本文件用于生成“社交媒体 App 界面 + 内容”的高度仿真样机，比如微博 / Twitter(X) / 小红书 / Threads / Instagram 等平台的发帖页、动态详情页、评论区。

不是用来做真实截图，而是用来做：

- 概念产品视觉
- 角色 / 历史人物 / 虚拟 IP 在社交平台的“假账号”
- 营销 demo
- 内容创意展示

## 适用范围

- 单条动态详情页（推文 / 帖子）
- 评论区样机
- 社交平台个人主页头部
- 暗黑 / 浅色模式 UI 模拟
- 多图九宫格 / 多图卡片样机

## 何时使用

- 用户提到“社交媒体样机 / 推文样机 / 微博样机 / Twitter 样机 / 朋友圈样机 / 小红书样机”
- 用户希望让一个名人 / 角色 / 虚拟身份“在某个平台发了一条 xx”
- 用户希望生成 UI + 内容融合的运营素材，而不是真实截屏

不要使用本模板的场景：

- 用户只想要一张人物头像
- 用户想要的是真实功能截图
- 用户要的是直播带货界面（去 `live-commerce-ui.md`）

## 缺失信息优先提问顺序

当用户只说“做一个社交平台样机”时，按以下顺序提问，能合并的合并：

1. 平台风格：Twitter/X、小红书、微博、Threads、Instagram、通用社交 App
2. 颜色模式：深色还是浅色
3. 账号主体：真人 / 名人 / 虚构人物 / 历史人物 / 品牌账号
4. 帖子内容：核心文案
5. 是否需要配图，配图主题是什么
6. 是否允许我自动补全互动数据（点赞、转发、评论文案）

如果用户说“你帮我补全”，则只问平台风格 + 主体身份 + 帖子主题，其余字段自动填充。

## 主模板：单条社交动态详情页

📖 描述

仿真“某社交平台动态详情页”的截图样机，包含：

- 顶部状态栏与导航
- 帖子作者信息（头像 / 昵称 / handle / 认证标）
- 帖子正文与可选 hashtags
- 多图卡片（可选）
- 互动统计与操作行
- 底部回复栏与底部 Tab Bar

📝 提示词

```json
{
  "type": "移动端社交平台动态详情页样机",
  "goal": "生成一张高仿真度的社交平台帖子详情页截图，用于做内容样机或概念演示",
  "platform": {
    "name": "{argument name=\"platform\" default=\"Twitter / X\"}",
    "color_mode": "{argument name=\"color mode\" default=\"dark\"}",
    "language": "{argument name=\"interface language\" default=\"中文\"}"
  },
  "header": {
    "status_bar": "顶部状态栏，显示时间 '{argument name=\"status time\" default=\"19:28\"}'，信号、Wi-Fi、电量图标",
    "navigation": "返回箭头 + 标题 '{argument name=\"page title\" default=\"帖子\"}'"
  },
  "post": {
    "author": {
      "avatar": "{argument name=\"avatar description\" default=\"身穿红袍头戴黑帽的中国古代帝王半身肖像\"}",
      "display_name": "{argument name=\"display name\" default=\"朱元璋\"}",
      "verified_badge": true,
      "handle": "{argument name=\"handle\" default=\"@Emperor_Ming\"}",
      "extra_badges": "{argument name=\"author extra badges\" default=\"皇室认证\"}"
    },
    "content": {
      "text": "{argument name=\"post text\" default=\"今日登基，开启洪武元年。愿与诸卿共建大明！\"}",
      "hashtags": "{argument name=\"hashtags\" default=\"#洪武元年 #登基大典 #大明王朝\"}",
      "media_grid": {
        "count": "{argument name=\"image count\" default=\"3\"}",
        "images": [
          "{argument name=\"image 1\" default=\"金色龙椅上的帝王正面照\"}",
          "{argument name=\"image 2\" default=\"宫殿庭院前万人朝拜的远景\"}",
          "{argument name=\"image 3\" default=\"帝王骑马率军前进的场景\"}"
        ]
      }
    },
    "metadata": {
      "timestamp": "{argument name=\"timestamp\" default=\"下午 1:36 · 1368 年 1 月 23 日\"}",
      "engagement": "{argument name=\"engagement stats\" default=\"5,432 转发 · 8,765 引用 · 2.01 万 点赞 · 10.23 万 浏览\"}"
    },
    "actions": "底部一行操作图标：回复、转发、点赞（红色心形带计数 '1'）、分享、上传"
  },
  "comments_preview": {
    "show": "{argument name=\"show top comment\" default=\"true\"}",
    "top_comment": {
      "avatar": "随机普通用户头像",
      "name": "{argument name=\"top commenter\" default=\"红巾军老张\"}",
      "text": "{argument name=\"top comment text\" default=\"陛下圣明！愿大明永昌！\"}"
    }
  },
  "footer": {
    "reply_bar": {
      "avatar": "当前登录用户的小头像",
      "placeholder": "{argument name=\"reply placeholder\" default=\"回复给 朱元璋...\"}"
    },
    "navigation_bar": "底部 Tab：首页、搜索、通知（带红点 '1'）、消息"
  },
  "style": {
    "rendering": "高保真移动端 UI 截图，1:2 左右纵向比例，看起来像真实手机截屏",
    "consistency": "整体配色严格遵循平台官方风格"
  },
  "constraints": {
    "must_keep": [
      "平台 UI 元素层级清晰",
      "头像、昵称、认证标、handle 都必须正确呈现",
      "正文文字必须清晰可读"
    ],
    "avoid": [
      "看起来像图片拼接而不是真实 UI",
      "比例错误导致像桌面网页",
      "头像与昵称配不上"
    ]
  }
}
```

### 参数策略

- 必问：平台、颜色模式、账号主体、帖子文案
- 可默认：状态栏时间、底部 Tab Bar 文案、操作行图标
- 可随机：互动统计数字、热门评论文案、hashtags 中的次要标签

### 自动补全策略

当用户说“你帮我补全”时：

- 时间默认下午时段
- 浏览数与点赞数按帖子内容热度估算（小众内容用 K，热点用 W）
- 评论用真实社区口吻，不要生成空洞模板话
- hashtags 与帖子主题保持一致，不要塞入无关流量词

## 变体 1：明亮模式 + 中文小红书风

📝 提示词

```json
{
  "type": "小红书风格图文动态详情页样机",
  "platform": {
    "name": "小红书",
    "color_mode": "light",
    "language": "中文"
  },
  "header": "顶部为搜索栏 + 头像 + 关注按钮",
  "post": {
    "author": {
      "display_name": "{argument name=\"display name\" default=\"小满 Maya\"}",
      "tag": "{argument name=\"author tag\" default=\"穿搭 | 探店\"}"
    },
    "title": "{argument name=\"post title\" default=\"上海周末 City Walk 路线分享\"}",
    "cover_image": "{argument name=\"cover image\" default=\"街头年轻女生侧身行走\"}",
    "swipeable_images_count": 4,
    "body_text": "{argument name=\"body text\" default=\"安福路 → 武康路 → 五原路，全程 3 公里...\"}",
    "tags": ["#周末出片", "#City Walk", "#上海周末去哪儿"]
  },
  "interaction_bar": "点赞、收藏、评论、分享，全部带数字",
  "comments_preview": {
    "count": 3,
    "messages": [
      "想要详细攻略！",
      "这条路线我也走过，超出片",
      "求穿搭链接 🔗"
    ]
  },
  "constraints": {
    "must_feel": "像真实小红书图文笔记，而不是海报"
  }
}
```

## 变体 2：品牌账号官方公告

适合品牌、应用、企业账号风格。

📝 提示词

```json
{
  "type": "品牌官方账号公告样机",
  "platform": {
    "name": "{argument name=\"platform\" default=\"Twitter / X\"}",
    "color_mode": "{argument name=\"color mode\" default=\"light\"}"
  },
  "post": {
    "author": {
      "display_name": "{argument name=\"brand name\" default=\"Anthropic\"}",
      "verified_badge": "official-gold",
      "handle": "{argument name=\"handle\" default=\"@AnthropicAI\"}"
    },
    "content": {
      "text": "{argument name=\"announcement text\" default=\"Today we're introducing Claude Opus 4.7 — our most capable model yet for coding and complex reasoning.\"}",
      "media_grid": {
        "count": 1,
        "images": ["产品发布主视觉，带 '{argument name=\"product name\" default=\"Claude Opus 4.7\"}' 大字"]
      }
    },
    "metadata": {
      "engagement": "高互动量级，例如 '12K 转发 / 36K 引用 / 158K 点赞 / 2.3M 浏览'"
    }
  },
  "constraints": {
    "must_feel": "像官方账号正式发布",
    "avoid": "出现明显的私人化、口语化措辞"
  }
}
```

## 变体 3：自动补全模式

适合用户只说“给我做一个社交平台样机”。

📝 提示词

```json
{
  "type": "社交动态样机自动补全模板",
  "mode": "auto-fill",
  "platform_generation": "若用户没说，默认 Twitter / X，深色模式，中文界面",
  "author_generation": "随机生成一个看起来真实但不冒犯的账号主体",
  "content_generation": "围绕一个具体且具体感强的话题展开，不要泛而空",
  "media_generation": "默认 1-3 张配图，与正文紧密相关",
  "constraints": {
    "must_feel": "真实、有人味、可信"
  }
}
```

## 避免事项

- 不要让 UI 元素只是纯文字堆叠，必须有头像、按钮、图标三要素
- 不要把社交平台风格混搭到分不清是哪个平台
- 不要让正文超过截图所能正常显示的长度，否则会出现严重截断
- 不要在“品牌官方账号”里生成太私人化或太情绪化的话术
- 不要生成与平台官方颜色明显冲突的主色（比如 X 出现纯小红书红）
