# 门店分布图模板

本文件用于生成“品牌 / 餐饮 / 零售门店在某区域内分布”的可视化地图：

- 连锁品牌门店分布
- 加盟商招商地图
- 城市 / 商圈门店覆盖
- 节日活动可达门店标记
- 银行 / 充电桩 / 共享设施分布

## 适用范围

- 全国 / 全省 / 全市级别的门店分布
- 单一商圈门店分布
- 加盟招商展示图
- 区域服务覆盖图

## 何时使用

- 用户提到“门店分布 / 网点分布 / 覆盖图 / 门店地图 / 加盟招商”
- 用户希望一张图能讲清楚“在哪有门店”
- 用户希望突出门店密度与品牌覆盖

不要使用：

- 美食探店地图（用 `food-map.md`）
- 路线图（用 `travel-route-map.md`）
- 城市风貌图（用 `illustrated-city-map.md`）

## 缺失信息优先提问顺序

1. 区域：全国 / 全省 / 全市 / 商圈
2. 品牌名 + logo 描述
3. 门店类型：旗舰店 / 标准店 / 快闪店 / 加盟店
4. 门店数量与具体名称（或允许我列）
5. 是否需要图例区分门店类型
6. 风格：品牌色现代扁平 / 拟真地图 / 信息图风

## 主模板：现代扁平品牌门店分布图

📖 描述

底图为简化的区域轮廓，门店以品牌色图钉 / 图标点位标注，配品牌信息卡 + 图例。

📝 提示词

```json
{
  "type": "品牌门店分布图",
  "goal": "生成一张能直接用于品牌官网 / 招商手册 / 节日活动的门店分布可视化地图",
  "brand": {
    "name": "{argument name=\"brand name\" default=\"AURA Coffee\"}",
    "logo_description": "{argument name=\"brand logo\" default=\"金色咖啡豆 + 品牌字\"}",
    "brand_color": "{argument name=\"brand color\" default=\"暖棕 + 奶油白\"}"
  },
  "scope": {
    "region": "{argument name=\"region scope\" default=\"全国\"}",
    "base_map_style": "{argument name=\"base map style\" default=\"简化省份轮廓 + 浅色填色\"}"
  },
  "stores": {
    "total_count": "{argument name=\"total stores\" default=\"168\"}",
    "by_type": [
      "{argument name=\"flagship\" default=\"旗舰店 8 家\"}",
      "{argument name=\"standard\" default=\"标准店 120 家\"}",
      "{argument name=\"pop_up\" default=\"快闪店 12 家\"}",
      "{argument name=\"franchise\" default=\"加盟店 28 家\"}"
    ],
    "highlight_cities": "{argument name=\"highlight cities\" default=\"北京、上海、广州、深圳、成都、杭州\"}"
  },
  "marker_design": {
    "shapes": "圆形品牌色图钉 + 不同尺寸代表不同类型",
    "rule": "尺寸排序：旗舰 > 标准 > 快闪 > 加盟"
  },
  "info_panel": {
    "enabled": "{argument name=\"info panel enabled\" default=\"true\"}",
    "position": "{argument name=\"info panel position\" default=\"右侧\"}",
    "content": [
      "总门店数",
      "覆盖城市数",
      "近一年新开",
      "重点城市 Top 5"
    ]
  },
  "legend": {
    "items": [
      "大圆点：旗舰店",
      "中圆点：标准店",
      "三角：快闪店",
      "方块：加盟店"
    ]
  },
  "extras": ["品牌 logo 角标", "招商联系方式区"],
  "constraints": {
    "must_keep": [
      "门店密度真实合理（不要全国都是密点）",
      "品牌色严格统一",
      "图例与门店类型对应",
      "重点城市清晰可读"
    ],
    "avoid": [
      "底图细节过多盖过门店",
      "出现非品牌色",
      "标记过密导致看不清",
      "图例缺失"
    ]
  }
}
```

### 参数策略

- 必问：品牌、区域、门店数量、品牌色
- 可默认：图例样式、信息卡内容
- 可随机：城市排序、次要装饰

### 自动补全策略

- 用户只给品牌名时：自动设定 100-200 家门店级别，重点城市选 Top 5-10
- 品牌色未指定时根据行业常用色（咖啡棕、奶茶粉、零售蓝、医疗绿）
- 图例最少 2 项最多 5 项

## 变体 1：单商圈密度图

📝 提示词

```json
{
  "type": "商圈门店密度图",
  "scope": {
    "region": "{argument name=\"district\" default=\"上海·静安寺商圈\"}"
  },
  "stores": {
    "total_count": "{argument name=\"store count\" default=\"24\"}",
    "highlight_cities": "门店具体名称 + 编号"
  },
  "constraints": {
    "must_feel": "本地化、密度感、街区级"
  }
}
```

## 变体 2：服务覆盖图（充电桩 / 网点 / 服务点）

📝 提示词

```json
{
  "type": "服务覆盖分布图",
  "service": {
    "name": "{argument name=\"service name\" default=\"NEX 充电网络\"}",
    "color": "{argument name=\"service color\" default=\"科技蓝 + 高亮黄\"}"
  },
  "stations_count": "{argument name=\"station count\" default=\"800+\"}",
  "marker_design": {
    "shapes": "闪电图标 + 不同颜色代表充电速度等级"
  },
  "legend": {
    "items": ["黄色：超充", "蓝色：快充", "灰色：慢充"]
  },
  "constraints": {
    "must_feel": "科技、专业、可靠"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "门店分布图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给品牌 + 行业，自动估计门店规模、品牌色、图例",
  "constraints": {
    "must_feel": "招商手册级"
  }
}
```

## 避免事项

- 不要让点位密度脱离真实（小品牌不要画成全国满屏点）
- 不要让品牌 logo 淹没在地图细节里
- 不要把多个不同行业品牌混在一张图
- 不要让信息卡占据超过 1/3 画面
- 不要使用真实地图截图风（这是品牌图，不是 GIS 截图）
