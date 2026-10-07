# 香蕉2.1接入与真实测试记录

验证日期：2026-10-07（北京时间）。中转站：`https://api.dapaoai.com`。

## 使用方法

重启 ComfyUI 并刷新页面，在现有“🐠香蕉-banana全能图像@炮老师的小课堂”节点中选择列表首位的“香蕉Pro 2.1全分辨率”（原显示名“香蕉2.1”，旧工作流加载时自动转换）。此名称仅为界面显示名，实际模型ID不变。

- 实际模型 ID：`gemini-nano-banana-2.1`。1K、2K、4K使用同一个模型ID。
- 思考等级：快速（minimal）、标准（medium，默认）、深入（high）。
- 联网搜索：默认关闭，打开后允许Google网页与图片搜索，是否调用由模型决定。
- 专属控件仅在选择香蕉2.1时显示；切换回旧模型后，后端也不会发送这些字段。
- 开启联网搜索后，可选择网页与图片、仅网页、仅图片。
- 展开“高级设置”可调整输出内容（图片与文字/仅图片）、返回思考摘要、输出Token上限（0为模型默认，最大32768）及系统指令。折叠仅隐藏控件，已设置的值仍生效。
- 响应信息增加可读的模型文字、模型返回的思考摘要、搜索词和来源链接；同时保留原响应JSON。模型不保证每次返回文字或摘要。
- 图像1至图像14：所有端口和每个IMAGE批次合计最多14张，超出时在请求前明确报错，避免静默丢图。
- 每张图片独立经过共享预处理，最长边不超过2048像素，Lanczos缩放、PNG上传。
- 随机种仅控制ComfyUI缓存，不向模型发送seed。出图数量仍表示独立请求次数；单条提示词并发最多4个，上游列表保留异步映射。
- 默认分组参考价约¥0.18/次，1K/2K/4K同价，以账户实际账单为准。

原有四个模型选项、默认模型、请求路由和输出端口保留。新增可选控件追加到旧控件之后，避免旧工作流的随机种和请求超时错位。

## 真实付费验证

用户明确授权后使用临时密钥，仅在进程内传入；未保存密钥。没有自动重试付费生成请求。

`GET /v1/models`、`GET /api/pricing`、`GET /api/usage/token/` 均返回HTTP 200。模型列表包含目标模型，支持Gemini和OpenAI类型端点。

测试沿用节点的共享图片预处理、Gemini请求体、持久队列提交/查询和结果解析。两批各3个并发任务，先文生图，再使用生成图及测试色卡做图生图。共有6次生成提交，6次成功；所有结果均下载、完整解码并记录SHA-256。

| 测试 | 参数 | 思考等级 | 参考图 | 实际输出像素 | 总耗时（含排队、下载） |
|---|---|---|---:|---|---:|
| 文生图 | 1K / 1:1 | minimal | 0 | 1024×1024 | 72.09秒 |
| 文生图 | 2K / 16:9 | medium | 0 | 2752×1536 | 54.43秒 |
| 文生图 | 4K / 3:4 | high | 0 | 3584×4800 | 110.08秒 |
| 图生图：茶壶改红色 | 1K / 4:3 | minimal | 1 | 1200×896 | 127.80秒 |
| 图生图：巴黎背景，联网搜索 | 2K / 9:16 | medium | 1 | 1536×2752 | 95.63秒 |
| 图生图：14张编号色卡 | 4K / 1:1 | high | 14 | 4096×4096 | 191.81秒 |

核验细节：

- 第一组任务同时开始，第二组任务也同时开始；妙笔实际返回queued/running/succeeded等状态，服务端仍可自行排队。
- 茶壶改色测试源图3072×3072，实际上传2048×2048，输出红色茶壶并保留蓝色标志和文字卡片。
- 搜索测试响应包含`groundingMetadata.searchEntryPoint`、`groundingChunks`、`webSearchQueries`，实际输出巴黎铁塔背景。
- 14图测试上传14张独立PNG，响应输入token数15734，输出包含编号1至14的两排色卡。未将这一小样本视为任意复杂场景的物体还原保证。
- 三档思考参数均被接受；medium/high响应含`thoughtsTokenCount`。这些样本不能用来严格比较三档速度或画质。
- 返回图片实际为JPEG；PNG是参考图上传编码，不能据此宣称生成结果为PNG。

### 任务ID

| 测试 | 妙笔持久队列Job ID |
|---|---|
| 文生图1K | `job_5P3qcVmQ4xcWDIVoNnqhTq8SpbgTkgLs` |
| 文生图2K | `job_VqEwVdrvOwK8zRGs5iMJ98HjdP3MTfiQ` |
| 文生图4K | `job_EYykrqpmmQUeIcBxiOYTmCZzzJ6IIAkZ` |
| 图生图1K | `job_bIIwo8thQ5S4l4HjbkGGpjdVHvgDJbhj` |
| 图生图2K搜索 | `job_B54WJcDjtxxrPQmtciwuyuMpHtVk3M5S` |
| 图生图4K/14图 | `job_MiAKGU8Wccdry84o8I3D6BD1E0u4OFpv` |

### 扣费核对

价格接口：`quota_type=1`（按次），`model_price=0.024657534247`，默认分组倍率1；平台`usd_exchange_rate=7.3`、`quota_per_unit=500000`。

- 测试前累计消耗：10,982,136 quota。
- 测试后累计消耗：11,056,110 quota。
- 差值：73,974 quota。
- 6条目标模型消费日志，每条12,329 quota，总和73,974，与余额差值一致。
- 人民币换算：`73974 / 500000 × 7.3 = 1.0800204`，约¥1.08；每次约¥0.18。包含联网搜索的这次请求也扣同样数额，未来费用以平台账单为准。

## 代码与界面验收

新增`test_banana_allround_node.py`、`test_banana_model_ui.cjs`。

- 节点、`test_node_error_utils`、`test_node_execution_gate`：最新24项通过。
- JavaScript控件切换、值保留、画幅过滤及旧控件顺序检查通过；JavaScript语法检查、`git diff --check`通过。
- 离线拦截请求验证：所有旧模型请求体保持原样、2.1路由与专属字段正确、14个端口与批次逐图缩放、超过上限请求前拒绝、单条返回结构不变、列表任务重叠执行、同节点并发使用独立客户端、失败只提交一次且保留原始错误。
- 独立ComfyUI测试实例实际启动并注册节点，使用Playwright操作真实页面；没有在页面中保存临时密钥或点击付费运行。
- 修改前保存的旧工作流加载后，模型、提示词、画幅、清晰度、数量、随机种、超时及图像12连线保留，新增图像13/14可用。
- 实际点击思考等级和搜索开关，导出的执行输入包含对应值；切换旧模型时两个控件隐藏、节点高度收缩。
- 新工作流保存再加载后，high/搜索开启和图像14连线保留。

扩展运行`test_dreambrush_runtime`后，合计42项中41项通过。唯一失败为既有的节点数量固定断言：期望15个异步联网节点，仓库现有17个。使用Git HEAD中未修改的香蕉文件重复该项，仍为17 != 15；与本次新增模型无关，未调整该无关断言。

本次只真实测试2.1，未重新付费测试旧模型，也未穷举所有画幅、并发量或参考图组合。官方列出的极端画幅依据文档提供候选；本次实测覆盖上表5种常见画幅。

## 官方参数依据与本地产物

- [Google generateContent图像生成指南](https://ai.google.dev/gemini-api/docs/generate-content/image-generation)
- [Google官方模型页](https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1)

本次原图、脱敏请求/响应、逐项结果、扣费日志、摘要及界面截图保存在：

`C:\Users\upboy\.codex\visualizations\2026\10\07\01a114ea-8bfb-7de3-ac92-ff9bd01a8006\banana21-validation`

该路径仅为本机验收产物位置，没有写入节点运行配置。`summary.json`包含图片尺寸、SHA-256、任务ID及耗时；`ui-banana21.png`和`ui-old-model.png`记录专属控件显示/隐藏。

## 官方能力复核及补充验证

### 比例：以当前线路实际拒绝信息校正文档冲突

Google Cloud模型页列出9:21，但Gemini generateContent的ImageConfig参考列表未包含9:21。2026-10-07向当前妙笔模型路由真实提交后，上游返回HTTP400：

> aspectRatio 9:21 is not supported by 'gemini-nano-banana-2.1'. Supported: 1:1, 4:3, 3:4, 4:5, 5:4, 2:3, 3:2, 9:16, 16:9, 21:9, 1:4, 4:1, 1:8, 8:1, auto.

因此保留14种固定比例和“模型默认”（不发送aspectRatio），不添加无效的9:21。支持横向21:9不能推导出支持纵向9:21。本地校验会在付费请求之前拒绝无效值；比例控件已补充提示。此结论针对当前中转线路，不代表所有Google平台永远不支持9:21。

### 能力核对表

| 能力 | 当前节点处理与验证边界 |
|---|---|
| 文生图/图生图、多参考图 | 已接入；真实覆盖14张输入。官方人物/物体一致性指标不应解释为任意14张人像都能精确保留 |
| 1K/2K/4K | 已接入且三档实测；不从通用ImageConfig枚举推导2.1支持512 |
| 14种固定比例、自动比例 | 已提供；常见5种画幅实测，未逐一付费穷举全部极端比例 |
| minimal/medium/high思考 | 已提供，三档实测 |
| Google网页和图片搜索 | 已提供三个范围；组合、仅网页、仅图片均有成功实测和groundingMetadata |
| IMAGE或TEXT+IMAGE输出 | 已提供；IMAGE-only按官方协议及模拟请求验证，未获得独立成功的付费样本（与9:21同次提交被拒绝） |
| 系统指令 | 已提供，可选文本；真实请求接受此字段，不能据单个样本保证任何指令严格遵循 |
| includeThoughts | 已提供；两次追加成功响应均返回thought文本，单独呈现为模型返回摘要；thought图片不会混入最终图像输出 |
| maxOutputTokens | 已提供0=省略或1至32768；32768请求成功，其余边界离线验证，过低可能造成截断 |
| 模型文本、搜索来源、用量、签名 | 文本和可用网页来源可读展示；原始响应JSON保留用量、grounding和签名，图片base64省略；不执行来源HTML |
| seed/temperature/topP/topK/logprobs | 2.1不提供这些采样参数；随机种只控制ComfyUI缓存 |
| 原生多图数量n/candidateCount | 不虚构支持；界面出图数量为独立请求次数，模型单次实际返回张数仍可能不同 |
| 输出格式/压缩质量 | 当前generateContent ImageConfig未列这些字段；不混入其他API的PNG/JPEG/quality参数 |
| 多轮对话、thoughtSignature回传 | 属于需要保存完整历史的独立工作流能力；当前节点每次独立生成，未实现会话输入输出。不能把脱敏响应JSON当作完整会话重放 |
| 视频/PDF作为输入 | 官方模型支持更广的输入；现有节点合同是TEXT+IMAGE，不含视频/PDF输入或上传流程。本次未扩大为文件理解节点，也未验证中转兼容性 |
| Batch、缓存、平台配额 | 平台能力，未冒充单次图像生成参数；当前节点并发与服务商Batch API不是一回事 |
| 函数调用、代码执行、URL Context、Maps、结构化输出 | 不为当前模型添加未支持工具开关 |
| 安全过滤 | 沿用服务端默认；未提供绕过开关；服务拒绝仍通过共享错误处理保留原始原因 |

这份核对表覆盖本次查阅的主要能力及不适用于当前节点的边界，不宣称视频/PDF、多轮会话等功能已经实现。

### 追加3次并发提交与最终账单

| 测试 | 任务ID | 结果 |
|---|---|---|
| 9:21 / 1K / IMAGE-only | `job_yQx6jdwpQOt9a9TKgBdFU5DZvz53HgrR` | 41.59秒后HTTP400，比例不支持 |
| 仅网页搜索 / 1K / 1:1 | `job_e36xJZ3Gawso8AqSUtQYcRh7yt9RIKXu` | 成功，1024×1024 JPEG，39.32秒 |
| 仅图片搜索 / 1K / 1:1 | `job_dkTkhKqOAGal6o5O7OyNywDMQ2p6n2y8` | 成功，1024×1024 JPEG，53.28秒 |

追加测试前累计消耗11,056,110；结算完成后11,080,768，差24,658 quota。两条消费日志各12,329，失败日志quota为0。换算约¥0.3600068。最初完成瞬间的快照只更新了一条累计消耗，后来只读复查账单已对齐；以`billing-reconciled.json`为最终依据，不以最早`summary.json`的瞬时差值为最终费用。连同前6次测试合计约¥1.44。所有提交均无自动重试。

新增参数已经通过24项Python测试和前端模拟检查；真实ComfyUI页面导出执行输入包含对应参数，鼠标点击高级设置后节点从828缩至702高度且值保留。新工作流序列化再加载也已检查。原节点三路输出和旧模型参数隔离保持不变。

追加产物目录：`C:\Users\upboy\.codex\visualizations\2026\10\07\01a114ea-8bfb-7de3-ac92-ff9bd01a8006\banana21-capability-audit`，包括请求、响应、原图、账单以及`ui-advanced.png`。

补充官方来源（2026-10-07查阅）：

- [generateContent API与ImageConfig字段](https://ai.google.dev/api/generate-content)
- [Google Cloud Nano Banana 2.1模型页](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/nano-banana-2-1)
- [图像生成与搜索、思考、输出模式](https://ai.google.dev/gemini-api/docs/generate-content/image-generation)
