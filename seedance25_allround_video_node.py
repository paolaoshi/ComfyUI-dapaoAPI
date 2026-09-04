"""Seedance 2.5 allround video node using the shared dapaoAI runtime."""

from .seedance20_allround_video_node import DapaoSeedance20AllroundVideoNode


NODE_NAME = "DapaoSeedance25AllroundVideoNode"
DISPLAY_NAME = "🐠Seedance2.5全能视频@炮老师的小课堂"
MODEL_ID = "SD2.5"


class DapaoSeedance25AllroundVideoNode(DapaoSeedance20AllroundVideoNode):
    """Seedance 2.5 route with expanded multimodal reference inputs."""

    MODEL_ID = MODEL_ID
    STANDARD_UPSTREAM_MODEL = MODEL_ID
    MODEL_OPTIONS = [MODEL_ID]
    MAX_IMAGE_REFERENCES = 30
    MAX_VIDEO_REFERENCES = 10
    MAX_AUDIO_REFERENCES = 10
    DURATION_OPTIONS = [str(value) for value in range(4, 31)]
    VERSION_LABEL = "Seedance2.5"
    HAS_FACE_MODE = False
    INCLUDE_BILLING_SECONDS = True
    DESCRIPTION = "Seedance2.5 文生视频、多图参考、首尾参考、多模态参考；支持30图、10视频、10音频素材接口"


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoSeedance25AllroundVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoSeedance25AllroundVideoNode",
    "MODEL_ID",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
