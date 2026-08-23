# 白底电商主图模板

本文件用于生成最常见的“电商纯净白底产品图”：

- 单品白底
- 多角度白底
- 白底 + 浅阴影
- 白底 + 极简文案

适合：

- 平台主图（淘宝 / 京东 / 亚马逊 / 抖音电商首图）
- 商品 SKU 卡
- 详情页第一屏静态图
- App 图标式产品瞄点图

## 适用范围

- 单品产品图
- 多角度组合图
- 极简文案版主图
- 通用电商主图

## 何时使用

- 用户提到“白底图 / 主图 / 商品图 / 平台主图 / SKU 卡”
- 用户希望直接落到电商平台使用，不需要场景氛围
- 用户希望突出商品本身，不要任何装饰

不要使用：

- 用户希望产品出现在生活场景里（用 `lifestyle-product-scene.md`）
- 用户希望影棚级氛围质感（用 `premium-studio-product.md`）
- 用户希望展示包装外观（用 `packaging-showcase.md`）

## 缺失信息优先提问顺序

1. 商品具体是什么（名称 + 关键视觉特征）
2. 是单品还是多角度
3. 是否需要文字（品牌名 / 卖点 / 价格）
4. 是否需要徽章（新品 / 限定 / 折扣）
5. 是否需要轻微阴影和反射

## 主模板：极简白底单品

📖 描述

纯净白底，商品居中，柔和反射 / 落地阴影，可选择是否叠加品牌名与单卖点。

📝 提示词

```json
{
  "type": "白底电商主图",
  "goal": "生成可直接用于电商平台主图位的白底产品图，商品作为绝对视觉中心",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"白色按压式精华瓶\"}",
    "visual_description": "{argument name=\"product visual description\" default=\"圆肩瓶，磨砂白色瓶身，金属银色按压头，瓶身正面贴有简洁标签\"}",
    "label_text": "{argument name=\"label text\" default=\"DERMA CALM Moisture Serum 30ml\"}",
    "angle": "{argument name=\"shot angle\" default=\"正面 3/4 视角\"}",
    "scale": "{argument name=\"product scale\" default=\"占据画面 60%\"}"
  },
  "background": {
    "type": "{argument name=\"background type\" default=\"纯白\"}",
    "shadow": "{argument name=\"shadow\" default=\"轻微底部柔光阴影\"}",
    "reflection": "{argument name=\"reflection\" default=\"无\"}"
  },
  "lighting": {
    "key_light": "{argument name=\"key light\" default=\"正面柔光\"}",
    "fill_light": "{argument name=\"fill light\" default=\"两侧均匀柔光\"}"
  },
  "text_overlay": {
    "enabled": "{argument name=\"text overlay enabled\" default=\"false\"}",
    "brand": "{argument name=\"overlay brand\" default=\"\"}",
    "selling_point": "{argument name=\"overlay selling point\" default=\"\"}"
  },
  "style": {
    "rendering": "高分辨率商业摄影 + 干净后期，没有任何场景元素",
    "consistency": "颜色还原真实，质感还原真实"
  },
  "constraints": {
    "must_keep": [
      "纯净白底",
      "商品作为唯一视觉中心",
      "标签文字必须清晰可读"
    ],
    "avoid": [
      "出现任何装饰道具",
      "背景出现颜色斑块",
      "强反射干扰商品本身",
      "商品边缘有强烈描边"
    ]
  }
}
```

### 参数策略

- 必问：商品名、关键视觉特征、标签文字
- 可默认：拍摄角度、阴影方式、灯光方案
- 可随机：占画面比例（在合理范围内浮动）

### 自动补全策略

- 没有给具体角度时，护肤 / 饮料 / 数码默认正面 3/4，鞋默认 45° 侧视，箱包默认正面平视
- 没有给标签文字时不要编造品牌，直接留空
- 没有给徽章默认不要加

## 变体 1：多角度组合白底

📝 提示词

```json
{
  "type": "多角度白底组合图",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"无线耳机\"}",
    "angles_count": "{argument name=\"angle count\" default=\"3\"}",
    "angles": [
      "{argument name=\"angle 1\" default=\"正面充电盒闭合\"}",
      "{argument name=\"angle 2\" default=\"打开盒子+耳机露出\"}",
      "{argument name=\"angle 3\" default=\"单只耳机特写\"}"
    ],
    "arrangement": "{argument name=\"arrangement\" default=\"水平等距排列\"}"
  },
  "background": {
    "type": "纯白",
    "shadow": "微阴影"
  },
  "constraints": {
    "must_feel": "组合像同一组镜头拍摄，光线一致"
  }
}
```

## 变体 2：白底 + 极简营销叠层

适合需要在白底上叠加“品牌 + 单卖点 + 价格”的简版主图。

📝 提示词

```json
{
  "type": "白底极简营销主图",
  "subject": {
    "product_name": "{argument name=\"product name\" default=\"运动水壶\"}"
  },
  "background": "纯白",
  "text_overlay": {
    "enabled": true,
    "brand": "{argument name=\"brand\" default=\"AQUA GO\"}",
    "selling_point": "{argument name=\"selling point\" default=\"24 小时保温\"}",
    "price": "{argument name=\"price\" default=\"¥ 89\"}",
    "badge": "{argument name=\"badge\" default=\"新品上市\"}",
    "layout": "品牌左上、卖点右上、价格右下、徽章左下"
  },
  "constraints": {
    "must_feel": "像电商平台 SKU 主图",
    "avoid": "信息层级混乱"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "白底主图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户只给商品名，自动决定角度、阴影、画面占比，但严格保持纯白底",
  "constraints": {
    "must_feel": "电商平台可直接上架"
  }
}
```

## 避免事项

- 背景不能出现灰边、渐变或纹理
- 不要为了好看自动加入花卉、石头、布料等道具
- 不要让阴影方向与灯光方向矛盾
- 不要让商品占画面 < 40%，会显得稀薄
- 不要给标签编造一个不存在的品牌名（除非明确允许）
- 不要在白底图上加风格化文字字体（除非显式启用 `text_overlay`）
