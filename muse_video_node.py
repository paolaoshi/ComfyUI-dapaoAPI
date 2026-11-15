"""Muse registration; execution is shared with Gemini Omni."""
from .miaobi_reference_video_node import MiaobiReferenceVideoNode

MODEL_ID = 'muse-video'
NODE_NAME = 'DapaoMuseVideoNode'

class DapaoMuseVideoNode(MiaobiReferenceVideoNode):
    MODEL_ID = MODEL_ID
    MODEL_OPTIONS = [MODEL_ID]
    MAX_IMAGE_REFERENCES = 1
    DURATION_OPTIONS = [str(value) for value in range(4, 31)]
    DEFAULT_DURATION = '5'
    VERSION_LABEL = 'Muse'
    BASE_PRICE = '0.3'
    DURATION_HINT = '按请求秒数计费；实际成片可能多1–2秒，不补收费用。'
    DESCRIPTION = 'Muse文生/单图生视频：720p，4–30秒，横屏或竖屏。' + DURATION_HINT + '不支持参考视频/音频、首尾帧或音轨开关。'

NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoMuseVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: '🐠Muse视频（文生/单图）@炮老师的小课堂'}
