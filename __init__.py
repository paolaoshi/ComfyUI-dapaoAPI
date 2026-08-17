"""
大炮 API (dapaoAPI) 节点初始化

当前维护分组：
- 大炮 AI 主力维护：GPT-image-2、Banana、Seedream 5.0 Pro、Seedream 图层拆分、GPT-LLM、Seedance2
- 大炮 API 常用工具：H3、Seedance 导演、Music3、视觉风格和详情页提示词
- API 通用工具：Gemini 多功能、通用 HTTP、通用图像生成与编辑
- RH 功能专区：RunningHub 图像、视频、LLM 与应用节点

作者：@炮老师的小课堂
版本：v1.7.4
"""

import asyncio
import aiohttp.web
import server
from pathlib import Path

# 首位菜单分组：大炮 AI 主力维护节点
from .gpt_image_2_allround_node import (
    NODE_CLASS_MAPPINGS as PRIMARY_MAINTENANCE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as PRIMARY_MAINTENANCE_DISPLAY_MAPPINGS
)

from .banana_allround_node import (
    NODE_CLASS_MAPPINGS as BANANA_ALLROUND_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as BANANA_ALLROUND_DISPLAY_MAPPINGS,
)

from .seedream_v5_pro_allround_node import (
    NODE_CLASS_MAPPINGS as SEEDREAM_V5_PRO_ALLROUND_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_V5_PRO_ALLROUND_DISPLAY_MAPPINGS,
)

from .seedream_v5_pro_layer_decomposition_node import (
    NODE_CLASS_MAPPINGS as SEEDREAM_V5_PRO_LAYER_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_V5_PRO_LAYER_DISPLAY_MAPPINGS,
)

from .gpt_llm_chat_node import (
    NODE_CLASS_MAPPINGS as GPT_LLM_CHAT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as GPT_LLM_CHAT_DISPLAY_MAPPINGS,
)

from .h3_video_prompt_node import (
    NODE_CLASS_MAPPINGS as H3_VIDEO_PROMPT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as H3_VIDEO_PROMPT_DISPLAY_MAPPINGS,
)

from .h3_prompt_box_node import (
    NODE_CLASS_MAPPINGS as H3_PROMPT_BOX_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as H3_PROMPT_BOX_DISPLAY_MAPPINGS,
)

from .seedance20_director_node import (
    NODE_CLASS_MAPPINGS as SEEDANCE20_DIRECTOR_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDANCE20_DIRECTOR_DISPLAY_MAPPINGS,
)

from .image_prompt_director_node import (
    NODE_CLASS_MAPPINGS as IMAGE_PROMPT_DIRECTOR_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as IMAGE_PROMPT_DIRECTOR_DISPLAY_MAPPINGS,
)

from .visual_style_prompt_node import (
    NODE_CLASS_MAPPINGS as VISUAL_STYLE_PROMPT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as VISUAL_STYLE_PROMPT_DISPLAY_MAPPINGS,
)

from .detail_flow_prompt_node import (
    NODE_CLASS_MAPPINGS as DETAIL_FLOW_PROMPT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as DETAIL_FLOW_PROMPT_DISPLAY_MAPPINGS,
)

from .music3_caption_prompt_node import (
    NODE_CLASS_MAPPINGS as MUSIC3_CAPTION_PROMPT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as MUSIC3_CAPTION_PROMPT_DISPLAY_MAPPINGS,
)

from .seedance20_allround_video_node import (
    NODE_CLASS_MAPPINGS as SEEDANCE20_ALLROUND_VIDEO_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDANCE20_ALLROUND_VIDEO_DISPLAY_MAPPINGS,
)

# 加载Gemini 3多功能节点
from .gemini3_nodes import (
    NODE_CLASS_MAPPINGS as GEMINI3_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as GEMINI3_DISPLAY_MAPPINGS
)

# 加载通用API调用节点
from .universal_api_node import (
    NODE_CLASS_MAPPINGS as UNIVERSAL_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as UNIVERSAL_DISPLAY_MAPPINGS
)

# 加载通用图像生成（文生图）节点
from .universal_text_to_image_node import (
    NODE_CLASS_MAPPINGS as UNIVERSAL_TEXT_TO_IMAGE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as UNIVERSAL_TEXT_TO_IMAGE_DISPLAY_MAPPINGS
)

# 加载通用图像生成（图像编辑）节点
from .universal_image_edit_node import (
    NODE_CLASS_MAPPINGS as UNIVERSAL_IMAGE_EDIT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as UNIVERSAL_IMAGE_EDIT_DISPLAY_MAPPINGS
)

# 加载图像编辑API节点
from .image_edit_api_node import (
    NODE_CLASS_MAPPINGS as IMAGE_EDIT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as IMAGE_EDIT_DISPLAY_MAPPINGS
)

# 加载 RH 全能图片节点
from .rh_all_image_node import (
    NODE_CLASS_MAPPINGS as RH_ALL_IMAGE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_ALL_IMAGE_DISPLAY_MAPPINGS
)

# 加载 RH 全能图片多并发节点
from .rh_all_image_concurrent_node import (
    NODE_CLASS_MAPPINGS as RH_ALL_IMAGE_CONCURRENT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_ALL_IMAGE_CONCURRENT_DISPLAY_MAPPINGS
)

# 加载 RH 全能视频 Seedance2.0 节点
from .rh_all_video_seedance_node import (
    NODE_CLASS_MAPPINGS as RH_ALL_VIDEO_SEEDANCE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_ALL_VIDEO_SEEDANCE_DISPLAY_MAPPINGS
)

# 加载 RH Seedance2.0 Mini 节点
from .rh_seedance20_mini_node import (
    NODE_CLASS_MAPPINGS as RH_SEEDANCE20_MINI_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_SEEDANCE20_MINI_DISPLAY_MAPPINGS
)

# 加载 RH 全能视频 V3.1 节点
from .rh_all_video_v31_node import (
    NODE_CLASS_MAPPINGS as RH_ALL_VIDEO_V31_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_ALL_VIDEO_V31_DISPLAY_MAPPINGS
)

# 加载 RH 全能视频 X-video3 节点
from .rh_all_video_x_video3_node import (
    NODE_CLASS_MAPPINGS as RH_ALL_VIDEO_XVIDEO3_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_ALL_VIDEO_XVIDEO3_DISPLAY_MAPPINGS
)

# 加载 RH Seedance2.0 素材节点
from .rh_seedance_asset_node import (
    NODE_CLASS_MAPPINGS as RH_SEEDANCE_ASSET_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_SEEDANCE_ASSET_DISPLAY_MAPPINGS
)

# 加载 RH 视频超清节点
from .rh_video_enhance_node import (
    NODE_CLASS_MAPPINGS as RH_VIDEO_ENHANCE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_VIDEO_ENHANCE_DISPLAY_MAPPINGS
)

# 加载 RH LLM 智能对话节点
from .rh_llm_chat_node import (
    NODE_CLASS_MAPPINGS as RH_LLM_CHAT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_LLM_CHAT_DISPLAY_MAPPINGS
)

# 加载 RH 批量 LLM 提示词节点
from .rh_batch_llm_prompt_node import (
    NODE_CLASS_MAPPINGS as RH_BATCH_LLM_PROMPT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_BATCH_LLM_PROMPT_DISPLAY_MAPPINGS
)

# 加载 RH 应用节点
from .rh_app_node import (
    NODE_CLASS_MAPPINGS as RH_APP_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as RH_APP_DISPLAY_MAPPINGS,
    fetch_rh_app_schema,
    upload_rh_app_file,
)

# 合并所有节点映射
NODE_CLASS_MAPPINGS = {
    **PRIMARY_MAINTENANCE_MAPPINGS,
    **BANANA_ALLROUND_MAPPINGS,
    **SEEDREAM_V5_PRO_ALLROUND_MAPPINGS,
    **SEEDREAM_V5_PRO_LAYER_MAPPINGS,
    **GPT_LLM_CHAT_MAPPINGS,
    **SEEDANCE20_ALLROUND_VIDEO_MAPPINGS,
    **H3_VIDEO_PROMPT_MAPPINGS,
    **H3_PROMPT_BOX_MAPPINGS,
    **SEEDANCE20_DIRECTOR_MAPPINGS,
    **VISUAL_STYLE_PROMPT_MAPPINGS,
    **DETAIL_FLOW_PROMPT_MAPPINGS,
    **MUSIC3_CAPTION_PROMPT_MAPPINGS,
    **IMAGE_PROMPT_DIRECTOR_MAPPINGS,
    **GEMINI3_MAPPINGS,
    **UNIVERSAL_MAPPINGS,
    **UNIVERSAL_TEXT_TO_IMAGE_MAPPINGS,
    **UNIVERSAL_IMAGE_EDIT_MAPPINGS,
    **IMAGE_EDIT_MAPPINGS,
    **RH_ALL_IMAGE_MAPPINGS,
    **RH_ALL_IMAGE_CONCURRENT_MAPPINGS,
    **RH_ALL_VIDEO_SEEDANCE_MAPPINGS,
    **RH_SEEDANCE20_MINI_MAPPINGS,
    **RH_ALL_VIDEO_V31_MAPPINGS,
    **RH_ALL_VIDEO_XVIDEO3_MAPPINGS,
    **RH_SEEDANCE_ASSET_MAPPINGS,
    **RH_VIDEO_ENHANCE_MAPPINGS,
    **RH_LLM_CHAT_MAPPINGS,
    **RH_BATCH_LLM_PROMPT_MAPPINGS,
    **RH_APP_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **PRIMARY_MAINTENANCE_DISPLAY_MAPPINGS,
    **BANANA_ALLROUND_DISPLAY_MAPPINGS,
    **SEEDREAM_V5_PRO_ALLROUND_DISPLAY_MAPPINGS,
    **SEEDREAM_V5_PRO_LAYER_DISPLAY_MAPPINGS,
    **GPT_LLM_CHAT_DISPLAY_MAPPINGS,
    **SEEDANCE20_ALLROUND_VIDEO_DISPLAY_MAPPINGS,
    **H3_VIDEO_PROMPT_DISPLAY_MAPPINGS,
    **H3_PROMPT_BOX_DISPLAY_MAPPINGS,
    **SEEDANCE20_DIRECTOR_DISPLAY_MAPPINGS,
    **VISUAL_STYLE_PROMPT_DISPLAY_MAPPINGS,
    **DETAIL_FLOW_PROMPT_DISPLAY_MAPPINGS,
    **MUSIC3_CAPTION_PROMPT_DISPLAY_MAPPINGS,
    **IMAGE_PROMPT_DIRECTOR_DISPLAY_MAPPINGS,
    **GEMINI3_DISPLAY_MAPPINGS,
    **UNIVERSAL_DISPLAY_MAPPINGS,
    **UNIVERSAL_TEXT_TO_IMAGE_DISPLAY_MAPPINGS,
    **UNIVERSAL_IMAGE_EDIT_DISPLAY_MAPPINGS,
    **IMAGE_EDIT_DISPLAY_MAPPINGS,
    **RH_ALL_IMAGE_DISPLAY_MAPPINGS,
    **RH_ALL_IMAGE_CONCURRENT_DISPLAY_MAPPINGS,
    **RH_ALL_VIDEO_SEEDANCE_DISPLAY_MAPPINGS,
    **RH_SEEDANCE20_MINI_DISPLAY_MAPPINGS,
    **RH_ALL_VIDEO_V31_DISPLAY_MAPPINGS,
    **RH_ALL_VIDEO_XVIDEO3_DISPLAY_MAPPINGS,
    **RH_SEEDANCE_ASSET_DISPLAY_MAPPINGS,
    **RH_VIDEO_ENHANCE_DISPLAY_MAPPINGS,
    **RH_LLM_CHAT_DISPLAY_MAPPINGS,
    **RH_BATCH_LLM_PROMPT_DISPLAY_MAPPINGS,
    **RH_APP_DISPLAY_MAPPINGS,
}

# 声明 Web 目录，用于加载 JavaScript 扩展
WEB_DIRECTORY = "./web"

@server.PromptServer.instance.routes.post("/dapao/rh-app/schema")
async def get_rh_app_schema(request: aiohttp.web.Request):
    body = {}
    try:
        body = await request.json()
        result = await asyncio.to_thread(
            fetch_rh_app_schema,
            body.get("api_channel", "国内版"),
            body.get("api_key", ""),
            body.get("webapp_id", ""),
            30,
        )
        return aiohttp.web.json_response(result)
    except Exception as error:
        message = str(error)
        api_key = str(body.get("api_key", "") or "")
        if api_key:
            message = message.replace(api_key, "***")
        return aiohttp.web.json_response({"error": message}, status=400)


@server.PromptServer.instance.routes.post("/dapao/rh-app/upload")
async def upload_rh_app_media(request: aiohttp.web.Request):
    values = {}
    file_content = b""
    filename = "upload.bin"
    mime_type = "application/octet-stream"
    try:
        reader = await request.multipart()
        while True:
            field = await reader.next()
            if field is None:
                break
            if field.name == "file":
                file_content = await field.read(decode=False)
                filename = Path(field.filename or filename).name
                mime_type = field.headers.get("Content-Type") or mime_type
            else:
                values[field.name] = await field.text()

        file_name = await asyncio.to_thread(
            upload_rh_app_file,
            values.get("api_channel", "国内版"),
            values.get("api_key", ""),
            file_content,
            filename,
            mime_type,
            180,
        )
        return aiohttp.web.json_response({"fileName": file_name, "originalName": filename})
    except Exception as error:
        message = str(error)
        api_key = str(values.get("api_key", "") or "")
        if api_key:
            message = message.replace(api_key, "***")
        return aiohttp.web.json_response({"error": message}, status=400)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# 启动信息
print("=" * 60)
print("  🎨 大炮 API (dapaoAPI) 节点加载完成!")
print("=" * 60)
print(f"  💎 Gemini 3多功能：{len(GEMINI3_MAPPINGS)} 个")
print(f"  🌐 通用API调用：{len(UNIVERSAL_MAPPINGS)} 个")
print(f"  🎨 图像编辑API：{len(IMAGE_EDIT_MAPPINGS)} 个")
print(f"  🌈 RH 全能图片：{len(RH_ALL_IMAGE_MAPPINGS)} 个")
print(f"  🌈 RH 全能图片多并发：{len(RH_ALL_IMAGE_CONCURRENT_MAPPINGS)} 个")
print(f"  🎉 RH 全能视频 Seedance2.0：{len(RH_ALL_VIDEO_SEEDANCE_MAPPINGS)} 个")
print(f"  🎉 RH Seedance2.0 Mini：{len(RH_SEEDANCE20_MINI_MAPPINGS)} 个")
print(f"  🎉 RH 全能视频 V3.1：{len(RH_ALL_VIDEO_V31_MAPPINGS)} 个")
print(f"  🎉 RH 全能视频 X-video3：{len(RH_ALL_VIDEO_XVIDEO3_MAPPINGS)} 个")
print(f"  📦 RH Seedance2.0素材：{len(RH_SEEDANCE_ASSET_MAPPINGS)} 个")
print(f"  🎉 RH 视频超清：{len(RH_VIDEO_ENHANCE_MAPPINGS)} 个")
print(f"  🪲 RH 应用：{len(RH_APP_MAPPINGS)} 个")
print(f"  ✅ 总计：{len(NODE_CLASS_MAPPINGS)} 个节点")
print(f"  👨‍🏫 作者：@炮老师的小课堂")
print(f"  🎨 主题：紫色标题栏 + 橙棕色背景")
print("=" * 60)
