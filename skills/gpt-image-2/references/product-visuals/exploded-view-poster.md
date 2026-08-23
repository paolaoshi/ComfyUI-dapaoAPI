# 产品爆炸视图海报模板

本文件用于生成“将一个完整产品垂直堆叠展开成内部组件 + callout 标注 + 顶部宣传文案 + 底部品牌区”的高级产品海报。

代表案例：

- VR 头显爆炸视图
- 手机内部结构爆炸图
- 智能音箱拆解图
- 无线耳机爆炸图
- 高端家电拆解图
- 相机 / 镜头组件展开图
- 户外装备拆解图

## 适用范围

- 高端产品发布主视觉
- 详情页“技术亮点”单图
- 工程美学展示
- 内部结构教育图
- 媒体级技术海报

## 何时使用

- 用户提到“爆炸视图 / 拆解图 / 内部结构 / exploded view”
- 用户要展示产品工程结构 / 模块化设计 / 技术细节
- 用户希望视觉风格偏“硬核工程感 + 商业海报”

不要使用：

- 用户只要白底产品图（用 `white-background-product.md`）
- 用户只要场景化产品图（用 `lifestyle-product-scene.md`）
- 用户要的是包装展示（用 `packaging-showcase.md`）

## 缺失信息优先提问顺序

1. 产品是什么（具体型号或类目）
2. 你希望突出几个组件（典型 6-9 个）
3. 品牌名 / 主标语 / 副标语
4. 颜色基调（柔和渐变 / 纯黑 / 极光 / 深空）
5. 是否需要双语 callout（中文 + 英文）
6. 标注布局：左右两侧分布 / 顶部底部分布 / 单侧分布

## 主模板：垂直爆炸视图 + 双侧 callout

📖 描述

主体在画面中央垂直堆叠展开为多个层级，左右两侧分布 callout 标签，顶部为产品名 + 主标语，底部为收束文案 + 品牌 logo。

📝 提示词

```json
{
  "type": "产品爆炸视图海报",
  "goal": "生成一张高科技、工程美学风格的产品海报，主体为产品的垂直爆炸视图，左右辅以技术 callout，整体可作为发布会主视觉或详情页技术亮点图",
  "subject": "{argument name=\"product\" default=\"VR 头显\"}",
  "style": {
    "rendering": "{argument name=\"render style\" default=\"简洁的高科技 3D 渲染，摄影棚灯光，发光装饰\"}",
    "background_color": "{argument name=\"background color\" default=\"柔和的紫蓝色渐变\"}",
    "lighting": "{argument name=\"lighting\" default=\"摄影棚顶光 + 微弱边缘光，组件之间存在淡淡发光气氛\"}"
  },
  "header": {
    "logo": "{argument name=\"product brand mark\" default=\"∞ Meta Quest 3\"}",
    "subtitle": "{argument name=\"main catchphrase\" default=\"以全新的结构，重塑全新的现实。\"}"
  },
  "layout": {
    "centerpiece": "{argument name=\"centerpiece description\" default=\"VR 头显的垂直堆叠爆炸视图，从下到上展示 9 层不同内部组件：外壳、摄像头传感器、带芯片的主板、Pancake 透镜、内部框架、电池组、侧带、顶部头带和面部接口衬垫\"}",
    "callout_layout": "{argument name=\"callout layout\" default=\"左右两侧均匀分布\"}",
    "callout_labels": {
      "count": "{argument name=\"callout count\" default=\"8\"}",
      "left_side": [
        "{argument name=\"left callout 1\" default=\"Snapdragon® XR2 Gen 2\\n卓越的处理性能，带来实时沉浸体验。\"}",
        "{argument name=\"left callout 2\" default=\"可调节 IPD 机构\\n为广大用户提供舒适的佩戴感。\"}",
        "{argument name=\"left callout 3\" default=\"精密设计的头带\\n追求舒适与稳定的工程学设计。\"}"
      ],
      "right_side": [
        "{argument name=\"right callout 1\" default=\"前面板\\n精致的设计与优化的重量平衡。\"}",
        "{argument name=\"right callout 2\" default=\"追踪摄像头\\n实现高精度的位置追踪与环境感知。\"}",
        "{argument name=\"right callout 3\" default=\"Pancake 透镜\\n轻薄设计，提供广阔视野与清晰画质。\"}",
        "{argument name=\"right callout 4\" default=\"高性能电池\\n优化电源设计，支持长时间续航。\"}",
        "{argument name=\"right callout 5\" default=\"柔软的面部接口\\n确保长时间佩戴依然舒适。\"}"
      ]
    },
    "footer": {
      "left_text_block": {
        "headline": "{argument name=\"bottom headline\" default=\"体验，源于结构的进化。\"}",
        "body": "{argument name=\"bottom body\" default=\"每一个零件都蕴含着支撑沉浸式体验的前沿科技与匠心设计。Meta Quest 3 从内部构建未来，为您带来超乎想象的体验。\"}"
      },
      "right_logo": "{argument name=\"footer brand logo\" default=\"∞ Meta\"}"
    }
  },
  "constraints": {
    "must_keep": [
      "组件层级感清晰，层与层之间有适当距离",
      "callout 引线指向正确组件",
      "顶部 logo 和底部品牌区不能与组件重叠",
      "整体看起来像高端发布会海报"
    ],
    "avoid": [
      "组件展开过密导致看不清",
      "callout 文字过长换行混乱",
      "光线方向不统一",
      "组件之间出现穿模或穿插"
    ]
  }
}
```

### 参数策略

- 必问：产品、组件数量、主标语
- 可默认：背景色、灯光、callout 模板文案
- 可随机：次级技术描述措辞、底部段落话术

### 自动补全策略

当用户只给出“产品名”时：

- 自动推测 6-9 个常见组件
- callout 文案使用“技术名称 + 一句价值描述”句式
- 主标语使用“以…重塑…”或“源于结构的进化”等收束感语句
- 底部品牌区默认与顶部 logo 一致

## 变体 1：手机 / 平板类爆炸图

📝 提示词

```json
{
  "type": "智能终端爆炸视图海报",
  "subject": "{argument name=\"product\" default=\"旗舰智能手机\"}",
  "style": {
    "rendering": "深空黑底 + 极简金属反光",
    "background_color": "{argument name=\"background color\" default=\"近黑色深空灰\"}"
  },
  "header": {
    "logo": "{argument name=\"product mark\" default=\"NEX Pro\"}",
    "subtitle": "{argument name=\"catchphrase\" default=\"看见每一层，理解每一处\"}"
  },
  "layout": {
    "centerpiece": "手机内部从底到顶垂直爆炸展开 8 层：金属中框、主板（含 SoC）、屏幕组件、摄像头模组、震动单元、电池、扬声器、玻璃后盖",
    "callout_labels": {
      "count": 8,
      "items_template": "组件名 + 技术亮点一句话"
    }
  },
  "constraints": {
    "must_feel": "工程美学 + 旗舰发布感"
  }
}
```

## 变体 2：可穿戴 / 音频类爆炸图

📝 提示词

```json
{
  "type": "可穿戴产品爆炸视图海报",
  "subject": "{argument name=\"product\" default=\"无线降噪耳机\"}",
  "style": {
    "rendering": "极简白色背景 + 柔和阴影 + 局部金属反光",
    "background_color": "{argument name=\"background color\" default=\"米白渐变\"}"
  },
  "header": {
    "logo": "{argument name=\"product mark\" default=\"AURA Pro\"}",
    "subtitle": "{argument name=\"catchphrase\" default=\"从内到外的安静\"}"
  },
  "layout": {
    "centerpiece": "耳罩侧面爆炸展开 6 层：外壳、麦克风阵列、降噪芯片板、驱动单元、声学海绵、记忆棉耳垫",
    "callout_labels": {
      "count": 6
    }
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "爆炸视图海报自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给出产品名后，自动决定层数（6-9 层）、callout 数量、主标语、底部段落与品牌 logo，但必须保持四要素：组件清晰、callout 与组件对位、顶部主语、底部品牌",
  "constraints": {
    "must_feel": "高端发布会主视觉"
  }
}
```

## 避免事项

- 不要让组件层数过多（超过 10 层就会显得拥挤）
- 不要让 callout 引线越过其他组件穿插
- 不要把 callout 文字写成营销口号，应该是“组件 + 技术 + 价值”三段式
- 不要让顶部 logo 和底部品牌 logo 不一致
- 不要在背景里加无关装饰元素（圆环、花纹、笔刷）
- 不要让灯光方向出现反向（顶光 + 反向阴影会立刻穿帮）
