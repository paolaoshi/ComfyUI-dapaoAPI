# 手绘城市美食地图模板

本文件用于生成“某座城市 / 某个区域的吃货地图”视觉，常见用途：

- 旅行 / 美食攻略主视觉
- 自媒体引流图
- 餐饮品牌活动主视觉
- 教育 / 文化科普图
- 城市 IP 周边图

主要特征：

- 手绘水彩 / 复古插画风
- 编号点位 + 文字标签
- 图例与方向标
- 中心 IP（熊猫 / 城市吉祥物 / 美食吉祥物）
- 边角装饰

## 适用范围

- 城市美食地图
- 街区美食路线图
- 节日 / 主题活动美食地图
- 单一菜系 / 单一品类美食地图（火锅 / 茶饮 / 烘焙）

## 何时使用

- 用户提到“美食地图 / 吃货地图 / 城市美食 / 探店地图”
- 用户希望视觉手绘感强，适合社交分享
- 用户希望有“一张图能讲清楚去哪吃”的感觉

不要使用：

- 用户要的是“通用城市地图”（用 `illustrated-city-map.md`）
- 用户要的是“路线导航图”（用 `travel-route-map.md`）
- 用户要的是“门店分布图”（用 `store-distribution-map.md`）

## 缺失信息优先提问顺序

1. 城市 / 区域名
2. 主题：美食 / 网红店 / 小吃 / 饮品
3. 美食条目：用户指定 or 我帮你列
4. 是否需要包含地标（10 处以内）
5. 风格：复古羊皮纸 / 现代水彩 / Q 萌插画
6. 是否需要中心吉祥物（熊猫、辣椒、城市象征）
7. 语言：中文 / 双语

## 主模板：复古手绘城市美食地图

📖 描述

整体为一张复古纹理羊皮纸或米色背景，上面绘有道路、河流、公园等抽象底图；地标与美食以编号小插画形式分布在地图上，右下角图例，画面中心一个吉祥物，边角点缀植物。

📝 提示词

```json
{
  "type": "手绘地图信息图",
  "goal": "生成一张高完成度的城市美食地图，可作为旅游攻略 / 自媒体首图 / 城市文化主视觉",
  "style": "{argument name=\"art style\" default=\"复古羊皮纸上的水彩墨水手绘插画\"}",
  "title_section": {
    "city": "{argument name=\"city name\" default=\"成都\"}",
    "title_text": "{argument name=\"map title\" default=\"吃货暴走地图\"}",
    "mascot": "{argument name=\"title mascot\" default=\"戴着墨镜并竖起大拇指的卡通红辣椒\"}"
  },
  "border": "{argument name=\"border decoration\" default=\"绿叶与红辣椒藤蔓\"}",
  "layout": {
    "background": "{argument name=\"background description\" default=\"带有黄色道路、蓝色河流和绿色公园区域的纹理米色羊皮纸\"}",
    "sections": [
      {
        "title": "地标建筑",
        "count": "{argument name=\"landmark count\" default=\"6\"}",
        "illustrations": "{argument name=\"landmark illustrations\" default=\"传统凉亭、传统寺院、带攀爬熊猫的现代摩天大楼、电视塔、传统牌坊、工业建筑\"}",
        "labels": "{argument name=\"landmark labels\" default=\"人民公园、文殊院、IFS、339电视塔、宽窄巷子、东郊记忆\"}"
      },
      {
        "title": "美食地点",
        "count": "{argument name=\"food count\" default=\"12\"}",
        "illustrations": "{argument name=\"food illustrations\" default=\"麻婆豆腐、红油水饺、冷锅串串、三大炮、蛋烘糕、九宫格火锅、肥肠粉、钵钵鸡、冒菜、盖碗茶、冰粉、兔头\"}",
        "labels": "{argument name=\"food labels\" default=\"1 陈麻婆豆腐、2 钟水饺、3 春熙路、4 宽窄巷子·三大炮、5 建设路·叶婆婆蛋烘糕、6 玉林路·小龙坎火锅、7 香香巷·肥肠粉、8 武侯祠大街·钵钵鸡、9 东郊记忆·冒椒火辣、10 人民公园·鹤鸣茶社、11 锦里古街·冰粉、12 双流老妈兔头\"}"
      },
      {
        "title": "图例",
        "position": "右下角",
        "items": ["红点：美食地点", "绿色建筑：地标景点", "绿树：公园绿地", "蓝线：河流湖泊", "黄色双线：主要道路"]
      }
    ],
    "centerpiece": "{argument name=\"centerpiece\" default=\"坐着吃竹子的大熊猫\"}",
    "extras": [
      "{argument name=\"compass\" default=\"带有东南西北方向的复古罗盘\"}",
      "{argument name=\"disclaimer\" default=\"带有红辣椒图标的免责声明：温馨提示：吃辣需谨慎，肠胃要保护~\"}"
    ]
  },
  "constraints": {
    "must_keep": [
      "美食条目数量与编号必须一致",
      "标签文字清晰可读",
      "中心吉祥物视觉抢眼但不抢图例位置",
      "整体保持手绘水彩风"
    ],
    "avoid": [
      "出现真实地图比例（这是插画地图）",
      "美食条目过多导致拥挤",
      "标签字体多种风格混用",
      "图例缺失或与点位不对应"
    ]
  }
}
```

### 参数策略

- 必问：城市名、主题、美食列表（或允许我帮列）、风格
- 可默认：背景纹理、图例、罗盘
- 可随机：地标具体名称（在该城市内合理）

### 自动补全策略

- 用户只给城市名时：从该城市知名美食里挑 8-12 项 + 6 处经典地标
- 风格默认“复古水彩 + 米色羊皮纸”
- 中心吉祥物按城市选：成都熊猫、重庆熊猫拿火锅、广州烧鹅、北京龙、长沙臭豆腐
- slogan 不超过 12 字

## 变体 1：单品类美食地图（火锅 / 茶饮 / 甜品）

📝 提示词

```json
{
  "type": "单品类美食地图",
  "city": "{argument name=\"city\" default=\"重庆\"}",
  "category": "{argument name=\"category\" default=\"火锅\"}",
  "title_text": "{argument name=\"title\" default=\"火锅地图\"}",
  "mascot": "{argument name=\"mascot\" default=\"举着红汤勺的卡通熊猫\"}",
  "sections": [
    {
      "title": "推荐门店",
      "count": "{argument name=\"store count\" default=\"10\"}"
    },
    {
      "title": "图例",
      "items": ["红点：门店", "辣椒数：辣度等级", "金标：必吃"]
    }
  ],
  "constraints": {
    "must_feel": "门店主题鲜明，不要混入其它品类"
  }
}
```

## 变体 2：现代扁平风美食地图

📝 提示词

```json
{
  "type": "扁平插画风格美食地图",
  "city": "{argument name=\"city\" default=\"上海\"}",
  "style": "扁平矢量插画，柔和粉色 + 米色 + 灰蓝",
  "title_text": "{argument name=\"title\" default=\"周末探店地图\"}",
  "centerpiece": "卡通女孩拿地图",
  "constraints": {
    "must_feel": "适合小红书 / 朋友圈分享，干净不复古"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "美食地图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户只给城市，自动决定地标、美食列表、风格、吉祥物",
  "constraints": {
    "must_feel": "完整、可分享、不用户不需要再补任何信息"
  }
}
```

## 避免事项

- 不要把美食地图画成真实地理比例尺地图
- 不要让美食条目超过 15 个，太多会让标签彼此挤压
- 不要让图例位置与地标重叠
- 不要在一张地图里混 “美食 + 路线 + 门店分布”三种功能（拆开为不同模板）
- 不要让吉祥物比标题更显眼（吉祥物是辅助）
