"""GPT Image 2.5 with queued generation and explicit multipart editing.

Official quality reference:
https://developers.openai.com/api/docs/models/gpt-image-2.5-flare
Relay-specific resolution and response_format fields follow image-2.
Reference images go to /v1/images/edits, never image_urls on generations.
"""

from .gpt_image_2_allround_node import DapaoGPTImage2AllroundNode, DapaoImage2RelayClient

NODE_NAME = "DapaoGPTImage25AllroundNode"
DISPLAY_NAME = "🦁GPT-image-2.5全能图像@炮老师的小课堂"
MODEL_LABEL = "gpt-image-2.5-flare"
SUNBURST_LABEL = "gpt-image-2.5-sunburst"
MODEL_OPTIONS = [MODEL_LABEL, SUNBURST_LABEL]
QUALITY_API_VALUES = {
    "low(低质量)": "low",
    "medium(中质量)": "medium",
    "high(高质量)": "high",
    "xhigh(超高)": "xhigh",
    "max(最高)": "max",
}


class DapaoImage25RelayClient(DapaoImage2RelayClient):
    def edit(self, payload, reference_images):
        # Explicit editing endpoint: generations may silently ignore image_urls.
        # Keep this synchronous; do not request the JSON-only persistent queue.
        data = {key: str(value) for key, value in payload.items() if key != "async"}
        files = [
            ("image", (f"image_{index}.png", content, "image/png"))
            for index, content in enumerate(reference_images, 1)
        ]
        return self._request_json("POST", "/v1/images/edits", data=data, files=files)


class DapaoGPTImage25AllroundNode(DapaoGPTImage2AllroundNode):
    # Official Images edit API: up to 16 input image references.
    # https://developers.openai.com/api/reference/resources/images/methods/edit
    MAX_REFERENCE_IMAGES = 16
    MODEL_OPTIONS = MODEL_OPTIONS
    DEFAULT_MODEL = MODEL_LABEL
    MODEL_ID_BY_LABEL = {MODEL_LABEL: MODEL_LABEL, SUNBURST_LABEL: SUNBURST_LABEL}
    QUALITY_API_VALUES = QUALITY_API_VALUES
    DEFAULT_QUALITY = "medium(中质量)"
    TASK_LABEL = "GPT-image-2.5"
    DESCRIPTION = (
        "妙笔工坊 GPT-image-2.5 文生图/多图编辑，支持五档画质；"
        "最多16张参考图（含批次），逐张压缩至最长边2K，提示词列表由ComfyUI并发执行。"
        "Flare / Sunburst均可选择；价格以妙笔工坊实际计费为准。@炮老师的小课堂"
    )

    def _create_client(self, api_key, timeout, max_poll_seconds):
        return DapaoImage25RelayClient(api_key, timeout, max_poll_seconds)

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        inputs["required"]["⚡ 异步模式"][1]["tooltip"] = (
            "文生图沿用妙笔工坊队列；接入参考图后自动使用图生图编辑接口同步等待，"
            "不向编辑接口发送异步参数。提示词列表仍支持并发。"
        )
        return inputs

    def _price_info(self, model_label, resolution_label, count):
        # No confirmed relay tariff: never reuse image-2's per-image prices.
        return "💰 价格：以妙笔工坊实际计费为准（暂未配置2.5价格）\n"


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoGPTImage25AllroundNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}
