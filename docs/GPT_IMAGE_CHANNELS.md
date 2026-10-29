# GPT Image 渠道切换（2026-10-27）

依据冒个泡AI造物坊 packages/model-catalog/miaobi.json（2026-10-22.gpt-image-tiers）与 image-request.mjs。

| 界面渠道 | 1K实际ID | 2K实际ID | 4K实际ID |
|---|---|---|---|
| image-2 低价 | image-2-1k | image-2-1k | image-2-1k |
| image-2 原生 | image-2-1k | image-2-2k | image-2-4k |
| Flare 低价 | gpt-image-2.5-flare | gpt-image-2.5-flare | gpt-image-2.5-flare |
| Flare 原生 | gpt-image-2.5-flare | gpt-image-2.5-flare-2k | gpt-image-2.5-flare-4k |
| Sunburst 低价 | gpt-image-2.5-sunburst | gpt-image-2.5-sunburst | gpt-image-2.5-sunburst |
| Sunburst 原生 | gpt-image-2.5-sunburst | gpt-image-2.5-sunburst-2k | gpt-image-2.5-sunburst-4k |

两种渠道都允许1K/2K/4K；resolution继续传1k/2k/4k。原生渠道后台仍按参考项目映射不同ID，不能把界面ID如image-2-native直接当服务端模型ID发送。

保留原image-2官方稳定全分辨率独立入口（image-2-office），不把它改名成原生。新建节点默认低价；旧工作流中的image-2、gpt-image-2.5-flare、gpt-image-2.5-sunburst自动迁移到相应原生选项，保持既有分辨率路由。控件次序和端口不变。后端也兼容旧标签；旧API格式workflow仍可能被ComfyUI枚举校验拦截，建议在界面加载再保存新workflow。

2.5编辑仍为multipart /v1/images/edits，不自动重试。size参照冒个泡转换为像素；1K的3:1/1:3使用1536x512/512x1536，自动比例使用auto。文生仍发送比例和resolution。图片上限和逐张2K预处理、三路输出、列表异步映射均保持。

Image2低价/原生不再套用原来按分辨率的固定报价，显示以所选渠道和实际账单为准，避免低价4K被标成原生4K价格；官方稳定入口维持已有报价。

验证：27项离线测试通过，包括六种渠道×三种分辨率请求矩阵、2.5两种渠道编辑模型和像素尺寸、旧模型路由迁移、并发、原始错误、禁止重复提交。真实ComfyUI隔离实例成功启动；前端确认新默认低价、旧标签迁移原生、切换4K不改变渠道、保存重载保留值。未调用真实生图API或消耗余额。

使用：重启ComfyUI并刷新网页。在原两个节点的模型下拉中选择带低价/原生标识的选项，再选择清晰度。
