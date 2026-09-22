"""Miaobi Qwen Image 3.0 / Pro all-round image node."""
from __future__ import annotations
import asyncio, base64, io, json, time, traceback
import numpy as np
import torch
from PIL import Image
from . import gpt_image_2_allround_node as base
from .dreambrush_runtime import ensure_asset_references, submit_json_task
from .node_error_utils import format_node_error
from .image_input_utils import tensor_to_png_bytes

NODE_NAME = "DapaoQwenImage3AllroundNode"
DISPLAY_NAME = "🦁Qwen-image-3.0全能图像@炮老师的小课堂"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
MODEL_OPTIONS = ["qwen-image-3.0", "qwen-image-3.0-pro"]
RATIOS = ["模型默认", "1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "21:9"]
SIZES = {"1K": {"1:1":"1024x1024","16:9":"1280x720","9:16":"720x1280","4:3":"1152x864","3:4":"864x1152","3:2":"1248x832","2:3":"832x1248","21:9":"1512x648"}, "2K": {"1:1":"2048x2048","16:9":"2560x1440","9:16":"1440x2560","4:3":"2304x1728","3:4":"1728x2304","3:2":"2496x1664","2:3":"1664x2496","21:9":"3024x1296"}}
QWEN_SEED_MODULUS = 2147483648

def _normalize_seed(value):
    """Keep legacy workflow seeds inside Qwen's signed 32-bit range."""
    try:
        return int(value) % QWEN_SEED_MODULUS
    except (TypeError, ValueError, OverflowError):
        return 0

class QwenImage3Client(base.DapaoImage2RelayClient):
    def generate(self, payload):
        return submit_json_task(api_key=self.api_key, base_url=self.base_url, endpoint="/v1/images/generations", payload=payload, timeout=self.timeout, user_agent="ComfyUI-dapaoAPI/QwenImage3", error_factory=base.DapaoImage2APIError, max_poll_seconds=self.max_poll_seconds, reuse_succeeded=True)
    def edit(self, payload):
        return submit_json_task(api_key=self.api_key, base_url=self.base_url, endpoint="/v1/images/edits", payload=payload, timeout=self.timeout, user_agent="ComfyUI-dapaoAPI/QwenImage3", error_factory=base.DapaoImage2APIError, max_poll_seconds=self.max_poll_seconds, reuse_succeeded=True)

class DapaoQwenImage3AllroundNode:
    MAX_REFERENCE_IMAGES = 3
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "Qwen Image 3.0/Pro 文生图、1～3张参考图编辑和多图融合；图片自动预处理至2K。"
    @classmethod
    def INPUT_TYPES(cls):
        optional={"🔁 最大轮询秒数":("INT",{"default":1200,"min":60,"max":3600,"step":10}),"⏱️ 轮询间隔":("INT",{"default":5,"min":3,"max":30}),"⌛ 请求超时":("INT",{"default":900,"min":30,"max":1800,"step":10})}
        for i in range(1,4): optional[f"🖼️ 图像{i}"]=("IMAGE",{"tooltip":"Qwen Image 3.0参考图，最多3张。"})
        return {"required":{"🔑 API密钥":("STRING",{"default":"","password":True,"placeholder":"填入 dapaoAI API 密钥"}),"🤖 模型":(MODEL_OPTIONS,{"default":MODEL_OPTIONS[0]}),"📝 提示词":("STRING",{"multiline":True,"default":"一张高端商业摄影，光线自然，细节清晰"}),"🧩 清晰度":(["1K","2K"],{"default":"1K"}),"📐 图片比例":(RATIOS,{"default":"模型默认"}),"🖼️ 出图数量":("INT",{"default":1,"min":1,"max":6,"step":1}),"🪄 提示词改写":("BOOLEAN",{"default":False}),"🧠 启用思考":("BOOLEAN",{"default":False}),"💧 水印":("BOOLEAN",{"default":False}),"🎲 随机种":("INT",{"default":0,"min":0,"max":2147483647,"control_after_generate":"randomize"})},"optional":optional}
    @staticmethod
    def _collect(kwargs):
        blobs=[]
        for i in range(1,4):
            v=kwargs.get(f"🖼️ 图像{i}")
            if v is not None: blobs.extend(tensor_to_png_bytes(v))
        if len(blobs)>3: raise ValueError("Qwen Image 3.0最多接收3张参考图。")
        return blobs
    async def generate(self, **kwargs): return await asyncio.to_thread(self._generate_sync, **kwargs)
    def _generate_sync(self, **kwargs):
        submitted={}; final={}; model=str(kwargs.get("🤖 模型") or MODEL_OPTIONS[0]); api_key=str(kwargs.get("🔑 API密钥") or "").strip()
        try:
            prompt=str(kwargs.get("📝 提示词") or "").strip(); res=kwargs.get("🧩 清晰度","1K"); ratio=kwargs.get("📐 图片比例","模型默认"); n=int(kwargs.get("🖼️ 出图数量",1))
            if not api_key: raise ValueError("请填写妙笔API密钥。")
            if model not in MODEL_OPTIONS or res not in SIZES or ratio not in RATIOS: raise ValueError("模型、清晰度或图片比例无效。")
            if not prompt: raise ValueError("提示词不能为空。")
            if not 1<=n<=6: raise ValueError("出图数量必须为1至6。")
            blobs=self._collect(kwargs); seed=_normalize_seed(kwargs.get("🎲 随机种",0)); refs=ensure_asset_references(api_key, [(b,f"qwen_image_{i}.png","image/png") for i,b in enumerate(blobs,1)], base_url=base.API_BASE_URL, timeout=int(kwargs.get("⌛ 请求超时",900))) if blobs else []
            size=SIZES[res].get(ratio) if ratio!="模型默认" else "auto"
            payload={"model":model,"prompt":prompt,"size":size,"n":n,"response_format":"url","seed":seed,"prompt_extend":bool(kwargs.get("🪄 提示词改写",False)),"enable_thinking":bool(kwargs.get("🧠 启用思考",False)),"watermark":bool(kwargs.get("💧 水印",False))}
            if refs: payload["images"]=refs
            client=QwenImage3Client(api_key,int(kwargs.get("⌛ 请求超时",900)),int(kwargs.get("🔁 最大轮询秒数",1200)))
            submitted=client.edit(payload) if refs else client.generate(payload); final=submitted
            items=base._extract_image_items(final); task=base._task_id(final)
            if not items and task: final=client.poll(task,int(kwargs.get("🔁 最大轮询秒数",1200)),int(kwargs.get("⏱️ 轮询间隔",5)),image_task=False); items=base._extract_image_items(final)
            if not items: raise RuntimeError("任务完成但没有返回图片。")
            tensors=[base._pil_to_tensor(base._image_item_to_pil(client,k,v)) for k,v in items]; image=tensors[0] if len(tensors)==1 else torch.cat(tensors,0)
            urls="\n".join(v for k,v in items if k=="url"); info=f"✅ Qwen Image 3.0任务完成\n界面模型：{model}\n实际模型ID：{model}\n模式：{'图生图' if refs else '文生图'}\n清晰度：{res}\n尺寸：{size}\n随机种：{seed}\n参考图：{len(refs)}张\n返回：{len(tensors)}张\n任务ID：{task or '同步返回'}\n"+json.dumps({"submit":submitted,"final":final},ensure_ascii=False,indent=2)
            return image,urls,info
        except Exception as error:
            message=format_node_error(f"❌ Qwen Image 3.0全能图像生成失败：{error}",context=__name__)
            raise RuntimeError(message+"\n\n"+json.dumps({"submit":submitted,"final":final},ensure_ascii=False,indent=2)) from None

NODE_CLASS_MAPPINGS={NODE_NAME:DapaoQwenImage3AllroundNode}
NODE_DISPLAY_NAME_MAPPINGS={NODE_NAME:DISPLAY_NAME}
