# 饮料 / 食品标签设计模板

本文件用于"饮料瓶 / 食品罐 / 调料瓶等的标签 + 包装设计"视觉：

- 饮料瓶标签设计
- 食品罐头标签
- 调味品瓶标签
- 中式 / 日式 / 西式 各种风格
- 单品摄影 + 标签设计混合

特征：

- 强调标签信息（品牌名 + 品名 + 容量 + 营养标）
- 标签字体 / 排版讲究
- 通常含插画 / 图形元素
- 包装结合环境拍摄
- 强调产品调性（健康 / 高奢 / 复古 / 国潮）

## 适用范围

- 饮料 / 食品标签设计
- 调味品包装
- 国潮 / 复古风饮料

## 何时使用

- 用户提到"饮料 / 食品 / 标签设计 / 罐装 / 瓶装"
- 用户希望出"包装 + 标签"完整设计

不要使用：

- 化妆品包装（用 `cosmetic-packaging.md`）
- 礼盒摄影（用 `product-visuals/packaging-showcase.md`）
- 通用 brand board（用 `brand-identity-board.md`）

## 缺失信息优先提问顺序

1. 品牌名 + 品类（茶 / 咖啡 / 果汁 / 调味）
2. 风格调性（国潮 / 日式 / 西式现代 / 复古）
3. 瓶 / 罐形态
4. 主色 1-2 个
5. 是否需要插画 / 图形
6. 是否需要营养标 / 警示

## 主模板：国潮风饮料标签设计

📖 描述

整体一张图，主体为一瓶饮料 + 标签设计，背景为东方风场景。

📝 提示词

```json
{
  "type": "国潮风饮料瓶标签设计",
  "goal": "生成一张可作为产品发布 / 电商主图的饮料瓶 + 标签视觉",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"东风茶事\"}",
    "positioning": "{argument name=\"positioning\" default=\"国潮 + 现代\"}",
    "product_name": "{argument name=\"product name\" default=\"清晨乌龙\"}",
    "product_subtitle": "{argument name=\"product subtitle\" default=\"OOLONG MORNING\"}",
    "volume": "{argument name=\"volume\" default=\"330ml\"}"
  },
  "bottle": {
    "form": "{argument name=\"bottle form\" default=\"短粗玻璃瓶 + 金属盖\"}",
    "material": "{argument name=\"material\" default=\"透明玻璃 + 茶汤可见\"}"
  },
  "label_design": {
    "style": "{argument name=\"label style\" default=\"水墨 + 工笔 + 留白\"}",
    "primary_color": "{argument name=\"primary color\" default=\"墨绿 + 金\"}",
    "background_color": "{argument name=\"label bg\" default=\"米白\"}",
    "illustration": "{argument name=\"illustration\" default=\"工笔 茶山 + 远山\"}",
    "typography": "{argument name=\"typography\" default=\"标题宋体 + 英文 sans\"}",
    "info_strip_bottom": "营养成分 + 容量 + 配料表（小字）"
  },
  "scene": {
    "background": "{argument name=\"background\" default=\"竹席 + 茶碗 + 一片绿叶\"}",
    "lighting": "{argument name=\"lighting\" default=\"自然柔光\"}"
  },
  "format": {
    "aspect_ratio": "{argument name=\"aspect ratio\" default=\"4:5\"}",
    "composition": "瓶身居中 + 微微倾斜 + 标签清晰朝镜头"
  },
  "constraints": {
    "must_keep": [
      "标签风格统一（不混搭水墨 + 美漫）",
      "标签字体 ≤ 2 种",
      "营养标 / 配料表小字可读但不喧宾夺主",
      "瓶身材质真实"
    ],
    "avoid": [
      "标签设计过满",
      "插画风格与文字风格冲突",
      "底色过亮压过插画",
      "出现错别字"
    ]
  }
}
```

### 参数策略

- 必问：品牌名、品类、风格
- 可默认：瓶身、标签、场景
- 可随机：道具细节

### 自动补全策略

- 用户给"国潮 / 日式 / 西式现代 / 复古"风格时：自动决定标签插画 + 配色 + 字体
- 默认 4:5 竖版
- 默认含小字营养标

## 变体 1：日式工艺风调味料瓶

📝 提示词

```json
{
  "type": "日式工艺风调味料瓶",
  "brand": {
    "product_name": "{argument name=\"product\" default=\"丸大豆酱油\"}"
  },
  "bottle": {
    "form": "复古短瓶 + 木塞"
  },
  "label_design": {
    "style": "日式工艺 + 手工书法 + 米色和纸",
    "primary_color": "深棕 + 朱红印章"
  },
  "scene": {
    "background": "原木桌面 + 竹笸箩"
  },
  "constraints": {
    "must_feel": "传统工艺感"
  }
}
```

## 变体 2：西式现代果汁

📝 提示词

```json
{
  "type": "西式现代果汁瓶",
  "brand": {
    "product_name": "COLD-PRESS ORANGE",
    "volume": "350ml"
  },
  "bottle": {
    "form": "高瘦透明 PET 瓶"
  },
  "label_design": {
    "style": "现代 minimal + 大字色块 + 清晰营养标",
    "primary_color": "亮橙 + 白"
  },
  "scene": {
    "background": "白色亚克力台 + 切半橙子"
  },
  "constraints": {
    "must_feel": "健康 + 现代 + 商超友好"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "饮料 / 食品标签自动补全",
  "mode": "auto-fill",
  "rule": "用户给品牌 + 品类 + 风格，自动决定瓶身 / 标签 / 插画 / 场景",
  "constraints": {
    "must_feel": "可直接送印刷厂"
  }
}
```

## 避免事项

- 不要混搭风格（国潮 + 美漫 同框）
- 不要让标签字体 > 2 种
- 不要漏掉营养标 / 配料表（除非是 mockup）
- 不要让瓶身比例失真
- 不要让插画喧宾夺主到品牌名认不出
- 不要让背景颜色高饱和压过产品
