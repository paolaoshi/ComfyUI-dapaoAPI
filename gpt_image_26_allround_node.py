"""Miaobi GPT Image 2.6 static images; reuse existing image inputs, jobs and outputs."""
from .gpt_image_25_allround_node import DapaoGPTImage25AllroundNode
from .gpt_image_2_allround_node import DapaoImage2RelayClient

NODE_NAME = 'DapaoGPTImage26AllroundNode'
DISPLAY_NAME = '🦁GPT-image-2.6全能图像@炮老师的小课堂'
FLARE = 'Flare（普通丨低价丨全分辨率）'
SUNBURST = 'Sunburst（高精丨低价丨全分辨率）'


class DapaoImage26RelayClient(DapaoImage2RelayClient):
    def edit(self, payload, reference_images):
        data = {key: str(value) for key, value in payload.items() if key != 'async'}
        files = [('image[]', (f'image_{index}.png', content, 'image/png'))
                 for index, content in enumerate(reference_images, 1)]
        return self._request_json('POST', '/v1/images/edits', data=data, files=files)


class DapaoGPTImage26AllroundNode(DapaoGPTImage25AllroundNode):
    MAX_REFERENCE_IMAGES = 3
    MODEL_OPTIONS = [FLARE, SUNBURST]
    DEFAULT_MODEL = FLARE
    MODEL_ALIASES = {'gpt-image-2.6-flare': FLARE, 'gpt-image-2.6-sunburst': SUNBURST}
    MODEL_ID_BY_LABEL = {FLARE: 'gpt-image-2.6-flare', SUNBURST: 'gpt-image-2.6-sunburst'}
    TASK_LABEL = 'GPT-image-2.6'
    DESCRIPTION = ('GPT Image 2.6 Flare/Sunburst静态文生图、1–3张参考图编辑，1K/2K/4K。'
                   '输入逐张缩至最长边2048，返回标准IMAGE，可接保存图像节点。'
                   '价格以妙笔当前模型和账户分组实际结算；此IMAGE节点不输出GIF或SVG。')

    def _resolve_request_model(self, model_label, resolution_label):
        # 2.6 keeps the same public model ID at every resolution; no invented suffixes.
        return self.MODEL_ID_BY_LABEL[model_label]

    def _create_client(self, api_key, timeout, max_poll_seconds):
        return DapaoImage26RelayClient(api_key, timeout, max_poll_seconds)

    def _price_info(self, model_label, resolution_label, count):
        return '💰 价格：以妙笔当前模型和账户分组实际结算为准，旧文档价格可能已更新。\n'


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoGPTImage26AllroundNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}
