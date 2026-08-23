# 旅行路线图模板

本文件用于生成“一条旅行路线 / 一份行程” 的可视化地图，常见用途：

- 自驾 / 骑行 / 徒步路线推荐图
- 多日行程攻略主图
- 跨城市旅行攻略
- 自媒体旅游内容封面
- 旅行品牌活动视觉

## 适用范围

- 多日行程图（D1-D7）
- 跨城市路线图
- 单日 city walk 路线图
- 户外徒步 / 骑行路线图
- 主题游路线（樱花、温泉、宝可梦取景地等）

## 何时使用

- 用户提到“路线图 / 行程图 / 攻略图 / 自驾路线”
- 用户希望视觉强调“顺序 + 时间”而不是“点位密度”

不要使用：

- 用户要美食地图（用 `food-map.md`）
- 用户要城市风貌地图（用 `illustrated-city-map.md`）

## 缺失信息优先提问顺序

1. 起点 / 终点 / 途经城市
2. 行程天数
3. 主题（美食、自然、文化、亲子、艺术）
4. 出行方式（自驾 / 高铁 / 飞机 / 徒步 / 骑行）
5. 风格：复古手绘 / 现代扁平 / Q 萌
6. 是否需要每日要点列表

## 主模板：多日行程旅行路线图

📖 描述

地图上以彩色实线 / 虚线连接多个城市或景点，按编号 D1-Dn 标注，每个站点配小插画。底部或侧栏列出每天行程要点。

📝 提示词

```json
{
  "type": "旅行路线图",
  "goal": "生成一张多日行程的可视化路线图，作为旅游攻略 / 节日 campaign 视觉首图",
  "style": "{argument name=\"art style\" default=\"复古手绘 + 水彩 + 米色羊皮纸底\"}",
  "title_section": {
    "title_text": "{argument name=\"title\" default=\"日本关西 7 日深度游\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"D1-D7 美食 + 文化 + 自然路线\"}"
  },
  "route": {
    "transport": "{argument name=\"transport\" default=\"高铁 + 步行\"}",
    "stops": [
      "{argument name=\"stop 1\" default=\"D1 大阪：道顿堀夜景\"}",
      "{argument name=\"stop 2\" default=\"D2 京都：清水寺 + 祇园\"}",
      "{argument name=\"stop 3\" default=\"D3 京都：岚山 + 竹林\"}",
      "{argument name=\"stop 4\" default=\"D4 奈良：东大寺 + 喂鹿\"}",
      "{argument name=\"stop 5\" default=\"D5 神户：北野异人馆\"}",
      "{argument name=\"stop 6\" default=\"D6 大阪：环球影城\"}",
      "{argument name=\"stop 7\" default=\"D7 大阪：返程购物\"}"
    ],
    "line_style": "{argument name=\"route line style\" default=\"红色虚线 + 圆点连接\"}"
  },
  "stop_illustrations": "每个站点配一个简洁手绘插画，比如鸟居、寺庙、鹿、温泉、塔",
  "side_panel": {
    "enabled": "{argument name=\"side panel enabled\" default=\"true\"}",
    "position": "{argument name=\"side panel position\" default=\"右侧或底部\"}",
    "content_type": "每日要点列表，包含 D1-Dn，每天 2-3 条 bullet"
  },
  "legend": {
    "items": [
      "红色虚线：高铁路线",
      "蓝色实线：步行路线",
      "金色星：必去景点",
      "粉色花：网红打卡点"
    ]
  },
  "extras": ["复古罗盘", "小段免责声明", "细微花纹边框"],
  "constraints": {
    "must_keep": [
      "路线顺序与编号一致",
      "每个站点都有插画 + 标签",
      "侧栏每日要点要简短，不超过 3 行"
    ],
    "avoid": [
      "城市位置出现明显错位（要符合大致地理方位）",
      "标签遮挡路线",
      "颜色过度饱和",
      "线型多于 2 种"
    ]
  }
}
```

### 参数策略

- 必问：起点、终点、天数、主题
- 可默认：风格、罗盘、图例
- 可随机：每日 bullet 中的次要细节

### 自动补全策略

- 用户只说目的地国家时：自动选 5-8 个经典城市
- 自动选风格匹配的吉祥物
- 自动安排合理路线顺序（不出现回头路）
- 行程天数默认 5-7 天

## 变体 1：单日 city walk 路线

📝 提示词

```json
{
  "type": "单日 city walk 路线图",
  "city": "{argument name=\"city\" default=\"上海\"}",
  "duration": "{argument name=\"duration\" default=\"半日\"}",
  "title_text": "{argument name=\"title\" default=\"上海周末 City Walk · 武康路一带\"}",
  "stops": [
    "{argument name=\"stop 1\" default=\"安福路\"}",
    "{argument name=\"stop 2\" default=\"武康路\"}",
    "{argument name=\"stop 3\" default=\"五原路\"}",
    "{argument name=\"stop 4\" default=\"乌鲁木齐中路\"}"
  ],
  "side_panel": {
    "enabled": true,
    "content_type": "每个点附 1 句推荐理由 + 推荐时段"
  },
  "constraints": {
    "must_feel": "悠闲、出片、生活感"
  }
}
```

## 变体 2：户外路线（徒步 / 骑行）

📝 提示词

```json
{
  "type": "户外徒步 / 骑行路线图",
  "title_text": "{argument name=\"title\" default=\"川西大环线 7 日骑行\"}",
  "transport": "{argument name=\"transport\" default=\"骑行\"}",
  "stops_count": "{argument name=\"stops count\" default=\"7\"}",
  "elevation_chart": {
    "enabled": "{argument name=\"elevation chart\" default=\"true\"}",
    "position": "底部"
  },
  "legend": {
    "items": [
      "实线：主路线",
      "虚线：备选路线",
      "三角：露营点",
      "心形：拍照点"
    ]
  },
  "constraints": {
    "must_feel": "硬核、户外感、专业"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "旅行路线图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户只说目的地与天数，自动安排经典路线、风格、侧栏要点",
  "constraints": {
    "must_feel": "可直接发布的攻略首图"
  }
}
```

## 避免事项

- 不要让路线长度超过画面边界，导致回绕重叠
- 不要让站点编号断裂（必须 D1 → Dn 连续）
- 不要让侧栏文字密度高过地图本身
- 不要混合多种交通线型（实线 + 虚线就够，不要 5 种）
- 不要画成真实精确比例尺，会让插画风塌掉
