# 高图例密度信息图模板

本文件用于生成“图例多 / 标注多 / 信息密度高”的科普 / 教育 / 解释型信息图：

- 医学因果链信息图
- 工艺流程信息图
- 历史 / 文化讲解信息图
- 设备 / 物种解剖图
- 复杂系统结构图

特征：

- 中央有主体（人体 / 设备 / 概念图）
- 四周分布多区块编号
- 每个区块由“编号 + 标题 + 图标 + 子项目”组成
- 中英双语 / 多语并行
- 信息量极大但布局严谨

## 适用范围

- 医学科普图
- 时尚 / 设计流程图
- 演化 / 进化 / 历史时间轴图
- 设备解剖图
- 跨学科系统图

## 何时使用

- 用户提到“因果链 / 演化图 / 系统图 / 解剖图 / 工艺图 / 信息图”
- 用户希望一张图讲完一个体系
- 用户希望中英双语

不要使用：

- 用户要的是“讲解型 Slides”（用 `slides-and-visual-docs/dense-explainer-slides.md`）
- 用户要的是地图（用 maps 系列）
- 用户要的是演讲页（用 `policy-style-slide.md`）

## 缺失信息优先提问顺序

1. 主题（病症 / 工艺 / 概念）
2. 主标题 + 英文副标题
3. 章节数（建议 8-14 个）
4. 中央主视觉
5. 颜色系（医疗红蓝 / 自然绿 / 科技蓝 / 米色书卷）
6. 是否双语

## 主模板：高密度因果链信息图

📖 描述

中央一个透明 / 半剖面主体，四周环绕 8-14 个编号信息块，每块由小图标 + 标题 + 子项目构成，底部一行收束句。

📝 提示词

```json
{
  "type": "高密度因果链信息图海报",
  "goal": "生成一张高完成度的科普 / 教育 / 解释型信息图，可作为单页 PDF 主图、自媒体长图首图、医院 / 学校宣传图",
  "style": {
    "aesthetic": "{argument name=\"aesthetic\" default=\"高度精细的解剖 / 工程图风格 + 干净结构化排版 + 科学示意感\"}",
    "color_palette": "{argument name=\"color palette\" default=\"医疗红、医疗蓝、米色、解剖肉色\"}",
    "language": "{argument name=\"language\" default=\"双语中文 + 英文\"}"
  },
  "header": {
    "main_title_cn": "{argument name=\"main title cn\" default=\"糖尿病诞生的因果链\"}",
    "main_title_en": "{argument name=\"main title en\" default=\"THE CAUSAL CHAIN OF DIABETES\"}",
    "subtitle": "{argument name=\"subtitle\" default=\"从胰岛素失灵，到高血糖，到全身损伤\"}"
  },
  "centerpiece": {
    "description": "{argument name=\"centerpiece description\" default=\"透明人体，展示循环系统与内脏器官\"}",
    "highlight": "{argument name=\"highlight color\" default=\"红色高光路径\"}"
  },
  "sections": {
    "count": "{argument name=\"section count\" default=\"14\"}",
    "items": [
      "01 葡萄糖进入身体",
      "02 胰腺与胰岛素",
      "03 正常胰岛素作用",
      "04 胰岛素抵抗：2 型通路开始",
      "05 肝脏持续释放葡萄糖",
      "06 β 细胞衰竭：代偿到失败",
      "07 1 型糖尿病分支",
      "08 高血糖与血液化学",
      "09 高血糖导致组织损伤",
      "10 急性代谢后果",
      "11 微血管并发症",
      "12 大血管并发症",
      "13 器官系统长期代价",
      "14 调控系统失灵"
    ]
  },
  "section_block_style": {
    "components": ["编号", "中文标题", "英文标题", "1-3 个图标", "短描述 ≤ 2 行"],
    "alignment": "围绕中央主体放射状或两侧栏"
  },
  "footer": {
    "core_message": "{argument name=\"core message\" default=\"糖尿病不是一次发病，而是代谢失衡的长期累积\"}",
    "core_message_en": "{argument name=\"core message en\" default=\"Diabetes is not a single event — it is the accumulation of metabolic imbalance.\"}"
  },
  "constraints": {
    "must_keep": [
      "中央主体作为视觉锚点",
      "章节编号连续",
      "中英文同时出现，但不能字号一致",
      "图例 / 标注线不交叉"
    ],
    "avoid": [
      "信息块尺寸不统一",
      "图标过度装饰化",
      "中英文换行不一致",
      "整体过亮 / 过暗影响阅读"
    ]
  }
}
```

### 参数策略

- 必问：主题、主标题、章节数、中心主体
- 可默认：颜色系、英文标题、底部收束句
- 可随机：章节图标的具体造型

### 自动补全策略

- 用户只给主题时：自动决定 8-14 个章节，并自动给出英文标题
- 中央主体根据主题自动选（医学 → 人体；工艺 → 设备剖面；演化 → 时间轴；历史 → 主角剪影）
- 颜色系按主题选默认色

## 变体 1：东方手稿风信息图

📝 提示词

```json
{
  "type": "东方手稿风信息图",
  "header": {
    "main_title": "{argument name=\"main title\" default=\"儒释道·根本区别\"}"
  },
  "style": {
    "aesthetic": "古书手稿 + 水墨线条 + 低饱和数字水彩",
    "color_palette": "鼠尾草绿、淡金、米白",
    "background": "做旧米色羊皮纸 + 边角磨损"
  },
  "centerpiece": {
    "description": "中央一个垂直蛋形分层结构，从顶到底依次：佛、道、儒"
  },
  "sections": {
    "items": ["释 / 人与自我", "道 / 人与万物", "儒 / 人与人"]
  },
  "constraints": {
    "must_feel": "古典、克制、有研究感"
  }
}
```

## 变体 2：演化时间轴信息图

📝 提示词

```json
{
  "type": "演化时间轴信息图",
  "header": {
    "main_title": "{argument name=\"main title\" default=\"人类演化\"}"
  },
  "centerpiece": {
    "description": "蜿蜒石阶共 25 个编号台阶，每阶展示一个生物形态",
    "highlight": "末端为带问号的发光宇宙剪影"
  },
  "sections": {
    "items": [
      "L0 单细胞生命",
      "L1 多细胞生物",
      "L2 动物界",
      "L3 脊索动物",
      "L4 上陆革命",
      "L5 哺乳纲",
      "L6 人科演化",
      "L7 智人纪元"
    ]
  },
  "extras": ["右上'获得 / 失去功能'图例", "底部'演化关键里程碑'时间轴"],
  "constraints": {
    "must_feel": "知识感强、视觉震撼"
  }
}
```

## 变体 3：自动补全模式

📝 提示词

```json
{
  "type": "高密度信息图自动补全模板",
  "mode": "auto-fill",
  "rule": "用户给主题与领域，自动决定章节、中央主体、配色、英文翻译",
  "constraints": {
    "must_feel": "出版物级"
  }
}
```

## 避免事项

- 章节数 < 6 会显得稀薄，> 16 会过密
- 不要让中文标题和英文标题字号一样大
- 不要让所有章节都堆在一侧，必须围绕中心
- 不要让线条交叉造成阅读混乱
- 不要把信息图画成纯文字海报（必须有图标 + 主体）
- 不要让整体颜色超过 4 种主色
