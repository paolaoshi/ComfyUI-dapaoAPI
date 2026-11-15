"""Gemini Omni uses the shared text/image-reference video execution path."""
from .miaobi_reference_video_node import MiaobiReferenceVideoNode

MODEL_ID = 'gemini-omni-1.2-flash'
NODE_NAME = 'DapaoGeminiOmniVideoNode'


class DapaoGeminiOmniVideoNode(MiaobiReferenceVideoNode):
    MODEL_ID = MODEL_ID
    MODEL_OPTIONS = [MODEL_ID]
    MAX_IMAGE_REFERENCES = 3
    DURATION_OPTIONS = ['4', '6', '8', '10']
    DEFAULT_DURATION = '8'
    VERSION_LABEL = 'Gemini Omni 1.2 Flash'
    BASE_PRICE = '0.08'
    DURATION_HINT = '仅4/6/8/10秒，按请求时长计费；默认8秒。'
    DESCRIPTION = ('Gemini Omni文生/1–3张参考图生视频，720p，16:9或9:16。'
                   '图片用于内容与风格参考，不是严格首尾帧。无参考视频/音频、延展或音轨开关。')


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoGeminiOmniVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: '🐠Gemini Omni视频（多图参考）@炮老师的小课堂'}
