"""Miaobi Global SP: fixed 30-second text/image generation."""

import asyncio
import re
from urllib.parse import quote

from . import seedance20_allround_video_node as shared
from .node_error_utils import format_node_error

MODEL_ID = "seedance-2.5-sp"
NODE_NAME = "DapaoSeedance25GlobalSPVideoNode"
DISPLAY_NAME = "🐠Seedance2.5-SP视频（30秒）@炮老师的小课堂"


class GlobalSPClient(shared.DapaoSeedanceRelayClient):
    def submit(self, payload):
        return shared.submit_json_task(
            api_key=self.api_key, base_url=self.base_url, endpoint="/v1/videos",
            payload=payload, timeout=self.timeout,
            user_agent="ComfyUI-dapaoAPI/Seedance25GlobalSP",
            error_factory=shared.DapaoSeedanceAPIError,
            interrupt_callback=(shared.comfy.model_management.throw_exception_if_processing_interrupted if shared.comfy is not None else None),
            max_poll_seconds=self.max_poll_seconds,
            recovery_salt=getattr(self, "recovery_salt", 0), reuse_succeeded=True,
        )

    def _request_json(self, method, path, **kwargs):
        # Reuse task-state/error handling, with this model's documented endpoint.
        path = path.replace("/v1/video/generations/", "/v1/videos/", 1)
        return super()._request_json(method, path, **kwargs)


class DapaoSeedance25GlobalSPVideoNode(shared.DapaoSeedance20AllroundVideoNode):
    MODEL_ID = MODEL_ID
    MODEL_OPTIONS = [MODEL_ID]
    MAX_VIDEO_REFERENCES = 0
    MAX_AUDIO_REFERENCES = 0
    DURATION_OPTIONS = ["30"]
    VERSION_LABEL = "Seedance2.5 Global SP"
    USE_ASSET_LIBRARY = False
    DESCRIPTION = "固定30秒，文生视频或最多9张图片参考。图片自动上传妙笔，不登记素材库。分辨率按协议开放，尚未逐档真实生成验收。"

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        required, optional = inputs["required"], inputs["optional"]
        required["🎛️ 生成模式"] = (["自动识别", "文生视频", "图生视频"], {"default": "自动识别"})
        required["⏱️ 时长(秒)"] = (["30"], {"default": "30", "tooltip": "每次固定30秒。"})
        required["🧩 分辨率"] = (["720P", "480P", "1080P", "2K", "4K"], {"default": "720P", "tooltip": "协议允许，尚未逐档实测。"})
        required["📐 视频比例"] = (["16:9", "9:16", "1:1", "3:4", "4:3", "21:9"], {"default": "16:9"})
        required["📝 提示词"][1]["tooltip"] = "最多3000个字符。"
        required.pop("🔊 生成音频", None)
        for name in ("🎬 首帧图", "🏁 尾帧图", "🎞️ 保留参考视频音轨"):
            optional.pop(name, None)
        optional["⏱️ 轮询间隔"] = ("INT", {"default": 10, "min": 10, "max": 15, "step": 1})
        for index in range(1, 10):
            optional[f"🖼️ 参考图{index}"] = ("IMAGE", {"tooltip": "自动上传妙笔后直传图片引用，无需素材登记；所有输入合计最多9张。"})
        return inputs

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        task_id = ""
        stage = "validate"
        api_key = str(kwargs.get("🔑 API密钥") or "").strip()
        try:
            schema = self.INPUT_TYPES()
            unknown = set(kwargs) - set(schema["required"]) - set(schema["optional"])
            if unknown:
                raise ValueError("Global SP不支持这些输入：" + "、".join(sorted(unknown)))
            if not api_key:
                raise ValueError("请填写妙笔API密钥。")
            if kwargs.get("🤖 模型", MODEL_ID) not in (MODEL_ID, "seedance-2.5-global-sp"):
                raise ValueError("本节点仅支持seedance-2.5-sp。")
            prompt = str(kwargs.get("📝 提示词") or "").strip()
            if not prompt or len(prompt) > 3000:
                raise ValueError("提示词不能为空且不能超过3000个字符。")
            if str(kwargs.get("⏱️ 时长(秒)", "30")) != "30":
                raise ValueError("Global SP每次固定30秒。")
            mode = kwargs.get("🎛️ 生成模式", "自动识别")
            resolution = kwargs.get("🧩 分辨率", "720P")
            ratio = kwargs.get("📐 视频比例", "16:9")
            for name, value in (("🎛️ 生成模式", mode), ("🧩 分辨率", resolution), ("📐 视频比例", ratio)):
                if value not in schema["required"][name][0]:
                    raise ValueError(f"{name}不支持：{value}")
            parts = self._collect_image_parts(kwargs)
            if mode == "文生视频" and parts:
                raise ValueError("文生视频不能同时接入参考图，请选择图生视频或自动识别。")
            if mode == "图生视频" and not parts:
                raise ValueError("图生视频至少需要一张参考图。")
            mode = "图生视频" if parts else "文生视频"
            timeout = int(kwargs.get("⌛ 请求超时", 120))
            max_seconds = int(kwargs.get("🔁 最大轮询秒数", 1800))
            interval = int(kwargs.get("⏱️ 轮询间隔", 10))
            if not 10 <= interval <= 15:
                raise ValueError("Global SP轮询间隔必须在10至15秒之间。")
            client = GlobalSPClient(api_key, timeout, max_seconds)
            client.recovery_salt = kwargs.get("🎲 随机种", 0)
            payload = {"model": MODEL_ID, "prompt": prompt, "seconds": "30", "ratio": ratio, "resolution": resolution.lower()}
            stage = "media_upload"
            references = []
            for part in parts:
                if shared.comfy is not None:
                    shared.comfy.model_management.throw_exception_if_processing_interrupted()
                reference = client.upload_file(*part, MODEL_ID)
                if not re.fullmatch(r"asset://file-[A-Za-z0-9_-]{1,59}", reference):
                    raise ValueError("妙笔上传未返回有效文件引用，请核查上传响应。")
                references.append(reference)
            if references:
                payload["images"] = references
            stage = "video_submit"
            submitted = client.submit(payload)
            task_id = shared._task_id(submitted)
            if not task_id or not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", task_id) or submitted.get("object") == "relay.job":
                raise RuntimeError("未取得有效视频任务ID，请保留队列记录查询，不要重复提交。")
            state, _, reason = shared._task_state(submitted)
            if state == "failed":
                raise shared.DapaoSeedanceTaskError(task_id, submitted, reason)
            stage = "video_poll"
            final = submitted if state == "completed" else client.poll(task_id, max_seconds, interval)
            url = shared._extract_video_url(final) or shared.API_BASE_URL + "/v1/videos/" + quote(task_id, safe="") + "/content"
            width, height = self._expected_dimensions(resolution if resolution not in ("2K", "4K") else "1080P", ratio)
            if resolution in ("2K", "4K"):
                scale = (2560 if resolution == "2K" else 3840) / max(width, height)
                width, height = int(width * scale) // 2 * 2, int(height * scale) // 2 * 2
            info = (f"✅ Seedance2.5 Global SP完成\n模型：{MODEL_ID}\n模式：{mode}\n请求时长：30秒\n"
                    f"请求分辨率：{resolution}（实际以产物为准）\n比例：{ratio}\n参考图：{len(parts)}张\n"
                    f"任务ID：{task_id}\n价格：按妙笔当前模型及用户分组实际结算。")
            return shared.DapaoVideoAdapter(url, width, height, api_key=api_key, task_id=task_id), task_id, info, url
        except Exception as error:
            message = format_node_error(error, context=__name__)
            if api_key:
                message = message.replace(api_key, "***")
            raise RuntimeError(f"{message}\n模型：{MODEL_ID}；阶段：{stage}；任务ID：{task_id or '未取得'}") from None


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoSeedance25GlobalSPVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}
