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
    USE_ASSET_LIBRARY = False
    DESCRIPTION = "Seedance2.5：素材上传妙笔后直接引用，无需素材登记。支持9图、3视频、3音频输入；高级参数组合以实际渠道支持为准。"

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        inputs["optional"]["🎬 首帧图"] = ("IMAGE", {"tooltip": "图片上传妙笔后作为first_frame提交，无需素材登记。"})
        inputs["optional"]["🏁 尾帧图"] = ("IMAGE", {"tooltip": "图片上传妙笔后作为last_frame提交，无需素材登记。"})
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
