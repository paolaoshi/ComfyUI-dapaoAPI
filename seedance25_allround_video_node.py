"""Seedance 2.5 allround video node using the shared dapaoAI runtime."""

from .seedance20_allround_video_node import DapaoSeedance20AllroundVideoNode


NODE_NAME = "DapaoSeedance25AllroundVideoNode"
DISPLAY_NAME = "🐠Seedance2.5全能视频@炮老师的小课堂"
MODEL_ID = "doubao-seedance-2-5"


class DapaoSeedance25AllroundVideoNode(DapaoSeedance20AllroundVideoNode):
    """Seedance 2.5 route with expanded multimodal reference inputs."""

    MODEL_ID = MODEL_ID
    STANDARD_UPSTREAM_MODEL = MODEL_ID
    MODEL_OPTIONS = [MODEL_ID]
    MAX_IMAGE_REFERENCES = 9
    MAX_VIDEO_REFERENCES = 3
    MAX_AUDIO_REFERENCES = 3
    DURATION_OPTIONS = [str(value) for value in range(4, 16)]
    VERSION_LABEL = "Seedance2.5"
    HAS_FACE_MODE = False
    INCLUDE_BILLING_SECONDS = True
    DESCRIPTION = "Seedance2.5 文生视频、多图参考、首尾参考、多模态参考；素材自动上传登记，支持9图、3视频、3音频"

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        inputs["optional"].update({
            "🎚️ 码率模式": (["standard", "high"], {"default": "standard"}),
            "📦 输出格式": (["mp4", "mov"], {"default": "mp4"}),
            "🎞️ 参考任务": (["auto", "reference", "edit", "extend"], {"default": "auto", "tooltip": "仅多模态参考时提交；edit/extend需要参考视频。"}),
        })
        return inputs


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoSeedance25AllroundVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoSeedance25AllroundVideoNode",
    "MODEL_ID",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
