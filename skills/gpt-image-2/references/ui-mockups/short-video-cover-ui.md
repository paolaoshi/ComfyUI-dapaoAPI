# 短视频封面 / Stream 缩略图 UI 模板

本文件用于生成“短视频封面 + UI 元素”样机，例如：

- 抖音 / 快手 / B 站 / 小红书 视频封面
- YouTube / Twitch 缩略图
- VTuber / 主播 stream 封面
- 自媒体节目封面
- 社交平台短视频封面

特点：

- 主体大、文字大、信息层级高
- 必须有可视化“点击诱因”
- 文字与人物 / 主体画面强叠加

它跟 `live-commerce-ui.md` 的区别：

- 直播 UI：仿真整个直播间界面（聊天 / 礼物 / 商品）
- 本模板：只是封面图层，重点在抓眼球的标题 + 主视觉

## 适用范围

- 短视频平台封面图
- YouTube / Bilibili / Twitch 缩略图
- 节目主视觉
- 直播预告图
- 课程 / 知识类视频封面

## 何时使用

- 用户提到“封面 / 缩略图 / 短视频封面 / 视频首图”
- 用户希望生成一张点击率高的视觉
- 用户给出节目名 / 标题 / 主播 / 主题

不要使用：

- 用户要的是真实直播间截图（用 `live-commerce-ui.md`）
- 用户要的是社交动态详情页（用 `social-interface-mockup.md`）

## 缺失信息优先提问顺序

1. 平台：抖音 / 快手 / 小红书 / B 站 / YouTube / Twitch
2. 内容类型：知识科普 / 生活 vlog / 游戏 / 直播预告 / 商业广告 / 萌系内容
3. 主标题文案
4. 主体（真人 / 卡通 / 物品 / 抽象主视觉）
5. 风格：高对比醒目 / 软萌少女 / 冷静极简 / 暗黑神秘
6. 是否需要副标题、bullet、徽章

## 主模板：知识类高对比短视频封面

📖 描述

仿真“讲清楚一件事的科普 / 解读类视频封面”，主体偏右，左侧为大字标题，附副标题与点状要点。

📝 提示词

```json
{
  "type": "短视频科普类封面样机",
  "goal": "生成一张高点击率的视频封面图，包含主标题、副标题、主视觉、平台风格小标识",
  "platform": "{argument name=\"platform\" default=\"通用短视频封面\"}",
  "aspect_ratio": "{argument name=\"aspect ratio\" default=\"16:9\"}",
  "background": {
    "color_palette": "{argument name=\"color palette\" default=\"深蓝渐变 + 高亮黄\"}",
    "texture": "{argument name=\"texture\" default=\"细微噪点 + 柔光\"}"
  },
  "main_visual": {
    "subject": "{argument name=\"main subject\" default=\"一位看向镜头并指向左侧标题的中年男性\"}",
    "position": "{argument name=\"subject position\" default=\"画面右侧 1/3\"}",
    "expression": "{argument name=\"expression\" default=\"有信服感、略带惊讶\"}"
  },
  "title_block": {
    "main_title": "{argument name=\"main title\" default=\"99% 的人都不知道的 ChatGPT 用法\"}",
    "title_style": "{argument name=\"title style\" default=\"白底黑字粗黑体 + 局部高亮黄色描边\"}",
    "sub_title": "{argument name=\"sub title\" default=\"一招提升 10 倍效率\"}",
    "bullet_points": {
      "count": "{argument name=\"bullet count\" default=\"3\"}",
      "items": [
        "{argument name=\"bullet 1\" default=\"自动整理会议纪要\"}",
        "{argument name=\"bullet 2\" default=\"批量生成 PPT 大纲\"}",
        "{argument name=\"bullet 3\" default=\"一键写邮件模板\"}"
      ]
    }
  },
  "platform_marks": {
    "logo_or_handle": "{argument name=\"creator handle\" default=\"@效率怪人\"}",
    "duration_label": "{argument name=\"duration\" default=\"06:24\"}"
  },
  "style": {
    "rendering": "封面图必须像真实视频封面，而不是普通海报",
    "contrast": "标题必须在 1 米外都能看清",
    "consistency": "整体风格一致，不出现风格冲突"
  },
  "constraints": {
    "must_keep": [
      "主标题视觉权重最高",
      "主视觉与标题不相互遮挡",
      "颜色对比度足够高"
    ],
    "avoid": [
      "标题过长导致换行混乱",
      "主体表情夸张到掉档次",
      "边角小字过多"
    ]
  }
}
```

### 参数策略

- 必问：主标题、主体、平台、风格
- 可默认：副标题、徽章、小字标签
- 可随机：bullet points 的次序与具体措辞，但与主题强相关

### 自动补全策略

- 主标题为空时不要自动编造，必须问
- 副标题缺失可自动补一个“数字 + 动词”句式
- bullet points 必须 ≤ 4 条
- 主体表情默认“信服 + 略带惊讶”

## 变体 1：可爱风 VTuber / 主播预告封面

📝 提示词

```json
{
  "type": "VTuber / 主播预告封面",
  "style": "anime, 高对比可爱粉系，闪光、爱心、星星装饰",
  "character": {
    "description": "{argument name=\"character description\" default=\"棕发双丸子头动漫女孩，琥珀色眼眸，温柔微笑\"}",
    "outfit": "{argument name=\"outfit\" default=\"粉色和服 + 白色女仆围裙，樱花发饰\"}",
    "pose": "{argument name=\"pose\" default=\"手持装饰花朵的粉色麦克风\"}"
  },
  "layout": {
    "background": "{argument name=\"background\" default=\"粉色渐变 + 闪光 + 心形 + 蝴蝶结\"}",
    "text_sections": [
      {
        "type": "顶部丝带",
        "text": "{argument name=\"top ribbon\" default=\"今晚开播一起聊聊吧～\"}"
      },
      {
        "type": "主标题",
        "text": "{argument name=\"main title\" default=\"杂谈直播\"}",
        "decorations": "周围 3 个大桃子插画"
      },
      {
        "type": "中间丝带",
        "text": "{argument name=\"middle ribbon\" default=\"想和大家度过开心的时光♡\"}"
      },
      {
        "type": "底部要点",
        "items": [
          "新人友好",
          "礼物回收",
          "ROMO"
        ]
      },
      {
        "type": "底部说话框",
        "text": "评论大欢迎♪ 一起多聊聊吧"
      }
    ]
  },
  "constraints": {
    "must_feel": "像真实主播预告封面，不是同人插画"
  }
}
```

## 变体 2：开箱 / 评测视频封面

📝 提示词

```json
{
  "type": "开箱评测视频封面",
  "platform": "{argument name=\"platform\" default=\"YouTube\"}",
  "aspect_ratio": "16:9",
  "main_visual": {
    "subject": "{argument name=\"main product\" default=\"一台尚未拆封的科技产品包装盒\"}",
    "host": "{argument name=\"host description\" default=\"画面左侧主播半身，表情夸张惊喜\"}",
    "extras": ["盒子周围环绕的发光线条", "局部撕开包装的悬念感"]
  },
  "title_block": {
    "main_title": "{argument name=\"main title\" default=\"全网首发！我把它拆了\"}",
    "sub_title": "{argument name=\"sub title\" default=\"真的值这个价吗？\"}",
    "label_badge": "{argument name=\"badge\" default=\"独家\"}"
  },
  "constraints": {
    "must_feel": "强诱因 + 强好奇感"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "短视频封面自动补全模板",
  "mode": "auto-fill",
  "rule": "用户只给出主题时，自动补主标题、副标题、主体、风格、配色，但必须保持封面三要素：主标题、主视觉、强对比",
  "constraints": {
    "must_feel": "像真实视频平台上抓人封面"
  }
}
```

## 避免事项

- 不要让标题占满整个画面（必须留出主视觉）
- 不要让标题颜色与背景过于接近，必须高对比
- 不要在一张封面塞超过 2 行的副标题
- 不要让主体面部被标题文字大块遮挡
- 不要混合多个平台的 UI 元素（比如 YouTube 红色播放按钮 + 抖音水印）
- 不要在“知识科普”封面里出现 emoji 表情堆叠
