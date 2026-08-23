# 复古档案 / 编辑式信息图海报模板

本文件用于生成"以历史人物 / 科学概念 / 经典理论为主题，用 1940s Bell Labs 档案 / 老报纸 / 蓝图 / 博物馆出版物风格呈现"的复古信息图海报。

典型用途：

- 科学家 / 思想家致敬海报（Shannon / Turing / Curie / 鲁迅…）
- 经典理论可视化（信息论 / 量子力学 / 进化论）
- 课程 / 出版物 / 博物馆教育海报
- 知识科普向 SNS / 朋友圈分享图
- 复古风文创品 / 周边周边

特征（与现有 poster / infographics 模板的区别）：

| 模板 | 风格 |
|---|---|
| `editorial-cover.md`（已有） | 现代杂志封面 |
| `infographics/legend-heavy-infographic.md`（已有） | 高密度科普图（现代或自然） |
| `infographics/bento-grid-infographic.md`（已有） | 便当格模块化（现代） |
| **本模板**（新增） | **复古档案 / 蓝图 / 老报纸 / 博物馆教育海报** |

**关键词**：1940s 风格、aged paper、ink linework、engraved portrait、navy + charcoal、measurement ticks、formula、archival stamp。

## 适用范围

- 历史人物 + 思想 / 理论 致敬海报
- 复古蓝图 / 老报纸 / 博物馆出版物风教育图
- 科学概念可视化（带公式 / chart / 时间轴）
- 文创品 / 教育出版 / 学术致敬

## 何时使用

- 用户提到"复古信息图 / 致敬海报 / 老报纸风 / 蓝图风 / 博物馆海报"
- 海报主题是历史人物 / 经典理论
- 想要"高文字密度 + 复古质感"

不要使用：

- 现代扁平信息图 → 用 `infographics/legend-heavy-infographic.md`
- 现代便当格 → 用 `infographics/bento-grid-infographic.md`
- 单纯杂志封面 → 用 `editorial-cover.md`
- 道教 / 神秘主义图 → 走中式古典工笔（建议直接用自然语言，不强用本模板）

## 缺失信息优先提问顺序

1. 主题人物 / 概念（Claude Shannon / Turing / 鲁迅…）
2. 核心理论 / 公式 / 模型（决定中央图示）
3. 历史时期与档案风格（**1940s Bell Labs / 1900 老报纸 / 复古蓝图 / 博物馆出版物 / 学院手稿**）
4. 是否需要时间轴（影响理论的历史脉络）
5. 是否需要人物肖像（如不允许真人脸 → 用脸部遮挡块 / 雕版剪影）
6. 比例（**16:9 横版展板 / 3:4 竖版海报**）
7. 主语言（英 / 中 / 双语）

## 主模板：复古档案信息图海报（人物 + 模型 + 公式 + 时间轴）

📖 描述

宽幅海报，左侧档案 sidebar + 中央 hero 模型 + 右侧公式 box + 中下理论分区 + 底部时间轴，包含人物肖像 + 多种 chart + 复古纸张质感。

📝 提示词

```json
{
  "type": "vintage editorial infographic poster",
  "goal": "生成一张复古档案 / 1940s 出版物风格的科普海报，把人物 / 理论 / 公式 / 应用时间轴密集组合在一张图里",
  "subject": "{argument name=\"subject\" default=\"Claude Shannon and information theory\"}",
  "style": {
    "era": "{argument name=\"era\" default=\"1940s Bell Labs archival poster\"}",
    "look": "{argument name=\"paper look\" default=\"aged cream paper, blueprint drafting grid, thin ink linework, muted navy and charcoal printing, subtle stains and paper wear, technical illustration mixed with newspaper editorial design\"}",
    "rendering": "high-detail diagrammatic collage with engraved portrait, scientific charts, labeled panels, and hand-drawn signal graphics"
  },
  "poster": {
    "headline": "{argument name=\"headline\" default=\"Claude Shannon — The Architecture of Information\"}",
    "subheadline": "{argument name=\"subheadline\" default=\"How uncertainty became measurable, and communication became engineering.\"}",
    "topRightMeta": {
      "note": "{argument name=\"meta note\" default=\"NOTE TOSELF No. 6713–2\"}",
      "date": "{argument name=\"meta date\" default=\"MAY 1948\"}",
      "subject": "{argument name=\"meta subject\" default=\"A Mathematical Theory of Communication\"}"
    }
  },
  "layout": {
    "sections": [
      {
        "title": "left archival sidebar",
        "position": "far left vertical column",
        "count": 5,
        "labels": [
          "{argument name=\"sidebar 1\" default=\"BELL LABORATORIES MURRAY HILL, N.J.\"}",
          "{argument name=\"sidebar 2\" default=\"ENGINEERING THE INTANGIBLE\"}",
          "{argument name=\"sidebar 3\" default=\"CLAUDE E. SHANNON 1916–2001\"}",
          "{argument name=\"sidebar 4\" default=\"TOOLS OF THE INFORMATION AGE\"}",
          "{argument name=\"sidebar 5\" default=\"quote panel with hand-set type\"}"
        ]
      },
      {
        "title": "{argument name=\"model title\" default=\"THE COMMUNICATION MODEL\"}",
        "position": "upper middle wide panel",
        "count": 5,
        "labels": ["1 INFORMATION SOURCE", "2 ENCODER", "3 CHANNEL", "4 DECODER", "5 DESTINATION"]
      },
      {
        "title": "{argument name=\"formula title\" default=\"ENTROPY: THE MEASURE OF UNCERTAINTY\"}",
        "position": "upper right box",
        "count": 4,
        "labels": [
          "{argument name=\"formula\" default=\"H(X) = −Σ p(x) log2 p(x)\"}",
          "PROBABILITY DISTRIBUTION p(x)",
          "MORE EVEN → MORE MAXED UNCERTAINTY",
          "MORE LOPSIDED → LESS UNCERTAINTY"
        ]
      },
      {
        "title": "lower theory panels",
        "position": "middle to lower band",
        "count": 3,
        "labels": [
          "{argument name=\"theory A\" default=\"A ENTROPY — uncertainty before a message is known\"}",
          "{argument name=\"theory B\" default=\"B NOISE — randomness that corrupts transmission\"}",
          "{argument name=\"theory C\" default=\"C Redundancy & Error Correction — structure added so signals can survive failure\"}"
        ]
      },
      {
        "title": "{argument name=\"timeline title\" default=\"THEORY THAT TRANSFORMED CIVILIZATION\"}",
        "position": "bottom horizontal timeline",
        "count": 8,
        "labels": [
          "{argument name=\"era 1\" default=\"1840s TELEGRAPHY\"}",
          "{argument name=\"era 2\" default=\"1876+ TELEPHONE NETWORKS\"}",
          "{argument name=\"era 3\" default=\"1930s–40s DIGITAL COMPUTERS\"}",
          "{argument name=\"era 4\" default=\"1950s–60s SATELLITE COMMUNICATION\"}",
          "{argument name=\"era 5\" default=\"1970s INTERNET PROTOCOLS\"}",
          "{argument name=\"era 6\" default=\"1980s–90s DATA COMPRESSION\"}",
          "{argument name=\"era 7\" default=\"1990s–2000s CRYPTOGRAPHY\"}",
          "{argument name=\"era 8\" default=\"2010s+ AI & INFORMATION SYSTEMS\"}"
        ]
      }
    ],
    "centerpiece": "{argument name=\"centerpiece description\" default=\"a large abstract cloud of blue and gray signal noise, dots, lines, and waveforms behind the communication model, with arrows moving left to right through the five stages\"}"
  },
  "visualElements": {
    "portrait": {
      "subject": "{argument name=\"portrait subject\" default=\"Claude Shannon\"}",
      "placement": "left-center",
      "style": "{argument name=\"portrait style\" default=\"black-and-white archival seated portrait at a desk with the face intentionally obscured by a pale square censor block, wearing suit and tie, writing on paper\"}"
    },
    "objectsLeft": [
      "{argument name=\"object 1\" default=\"rotary telephone on desk\"}",
      "{argument name=\"object 2\" default=\"open notebook or papers\"}",
      "{argument name=\"object 3\" default=\"technical console with CRT screen and knobs behind portrait\"}",
      "{argument name=\"object 4\" default=\"small icon row of 4 tools: oscilloscope, signal meter, relay, punched tape\"}"
    ],
    "centerModel": [
      "book and symbols under source",
      "binary digits under encoder",
      "large noisy channel cloud with wave overlays",
      "binary digits and interpretation under decoder",
      "light bulb icon under destination"
    ],
    "chartsAndDiagrams": [
      "bar chart for entropy probabilities",
      "two low vs high entropy mini bar charts",
      "tree diagram and entropy notation",
      "signal distortion sketches labeled thermal noise / cross talk / distortion",
      "error-correction binary pipeline from original message to recovered message"
    ],
    "bottomDecor": ["small waveform legend with sine wave, digital signal, and noise", "archival stamp or footer on lower right"]
  },
  "color": {
    "background": "{argument name=\"paper color\" default=\"warm ivory paper\"}",
    "primaryInk": "{argument name=\"primary ink\" default=\"dark navy\"}",
    "secondaryInk": "{argument name=\"secondary ink\" default=\"charcoal gray\"}",
    "accent": "{argument name=\"accent ink\" default=\"faded steel blue\"}"
  },
  "composition": "symmetrical wide poster with dense boxed annotations, fine border lines, and a museum-quality educational infographic feel",
  "textDensity": "very high, with many small labels, formulas, captions, and historical notes in a carefully organized grid",
  "aspectRatio": "{argument name=\"aspect ratio\" default=\"16:9 landscape\"}",
  "constraints": {
    "must_keep": [
      "复古 1940s 印刷质感（aged paper / 网格 / 钢笔线 / 墨色）",
      "公式 / 模型 / 时间轴 / 肖像 4 大元素全部出现且清晰可读",
      "全图配色严格控制在 ivory + 1 主墨色 + 1 副墨色 + 1 accent",
      "若使用真实人物，脸部用 censor block / 雕版剪影 / 模糊处理"
    ],
    "avoid": [
      "用现代扁平 icon / 渐变 → 立刻破坏复古质感",
      "公式写错或丢失 (LaTeX 字符须由 prompt 描述清楚)",
      "时间轴超过 8 节点导致每节点不可读",
      "肖像区域过大压垮信息密度（应 ≤ 25% 总面积）",
      "使用霓虹 / 荧光色"
    ]
  }
}
```

### 参数策略

- **必问**：subject、headline、formula / 模型 / 时间轴的具体内容
- **可默认**：era、paper look、portrait style、centerpiece description
- **可随机**：sidebar 5 行小文案、bottom decor

### 自动补全策略

- 用户给了主题人物 → 自动反推核心模型 / 公式 / 时间轴
- 不指定肖像处理 → 默认 censor block 遮脸（避免真人脸生成失败）
- 不指定 paper / ink 色 → 用模板默认 ivory + navy + charcoal + steel blue

## 变体 1：中文学者 / 文人致敬版（鲁迅 / 钱学森 / 沈括…）

📝 提示词

```json
{
  "type": "vintage editorial infographic poster, Chinese scholar tribute edition",
  "subject": "{argument name=\"chinese subject\" default=\"鲁迅与现代白话文运动\"}",
  "style_override": {
    "era": "1920s 中国新文化运动时期出版物",
    "look": "aged 米黄宣纸 with 雕版印刷 effect, 红印泥 seal stamps, 竖排繁体或简化中文 mixed with 英译注释",
    "ink": "墨黑 + 朱红 + 灰青"
  },
  "language_override": "中文为主 + 英文小注释",
  "extra_elements": ["传统印章", "竖排标题", "毛笔签名", "线装书边框装饰"]
}
```

### 何时选这个变体

- 中国学者 / 文人 / 历史人物
- 教育 / 出版 / 文化致敬
- 想要「东方文人风」而非"西方档案风"

## 变体 2：3:4 竖版精装海报（适合印刷 / 文创售卖）

📝 提示词

```json
{
  "type": "vintage editorial infographic poster, vertical print edition",
  "aspectRatio_override": "3:4 portrait poster",
  "layout_override": {
    "structure": "top hero portrait + middle theory section + bottom timeline; sidebar moved to bottom strip",
    "headline_position": "very top, large serif"
  },
  "use_case": "可作为限量印刷海报 / 文创周边产品"
}
```

### 何时选这个变体

- 文创售卖品（A2 / A3 印刷海报）
- 教育机构教室张贴
- 想做"可挂墙"成品

## 变体 3：博物馆展板版（双语，更教育）

📝 提示词

```json
{
  "type": "museum exhibition panel infographic",
  "language": "bilingual (English + 主体语言)",
  "extra_sections": ["Acknowledgments / 致谢", "Further Reading / 延伸阅读", "QR code square (museum app)"],
  "must_keep": ["所有标注双语对照", "底部 acknowledgments / 资料来源 必须出现"]
}
```

### 何时选这个变体

- 真实博物馆 / 展览出版物
- 教育机构课程展板
- 学术致敬场景

## 避免事项

- ❌ 用渐变 / 霓虹 / 现代扁平 icon → 立即破坏复古感
- ❌ 把人物画得过大、占据 50%+ 面积 → 应该是模型 / 公式 / 时间轴占主，肖像辅助
- ❌ 公式写错或丢公式（核心理论必须可读）
- ❌ 时间轴节点 > 10 → 不可读，应控制在 6-8
- ❌ 让 GPT 生成真人脸 → 优先用 censor block / 雕版 / 模糊
- ❌ 只用一种字号 → 复古海报必须有 4-5 级 hierarchy
- ❌ 使用现代 web font（应描述为 serif / hand-set / engraved type）
- ❌ 把主题人物名字拼错（多次出现的名字必须在 prompt 中显式 spell-out）
