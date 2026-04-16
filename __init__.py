"""
大炮 API (dapaoAPI) 节点初始化

支持功能：
- Seedream 4.0 图像生成（文生图、多图编辑）
- Seedream 4.5 图像生成（文生图、多图融合、组图生成）
- 豆包 LLM对话（Seed-1.6）
- xAI Grok LLM对话（Grok-beta）
- Google Nano Banana 2 多模态（图像+文本）
- Google Gemini 3 多模态对话（官方+T8）
- 通用 API 调用节点（支持任意 HTTP API）
- 通用图像编辑 API 节点
- 灵活的分辨率和宽高比控制
- 统一的紫色+橙棕色节点主题
- 大炮提示词模板管理
- 对比打标 (API)

作者：@炮老师的小课堂
版本：v1.7.4
"""

import aiohttp.web
import server
from pathlib import Path
import traceback

# 加载 Seedream 节点
from .seedream_nodes import (
    NODE_CLASS_MAPPINGS as SEEDREAM_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_DISPLAY_MAPPINGS
)

# 加载 Seedream 4.5 节点
from .seedream45_node import (
    NODE_CLASS_MAPPINGS as SEEDREAM45_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM45_DISPLAY_MAPPINGS
)

# 加载 Seedream 5.0 节点
from .seedream50_node import (
    NODE_CLASS_MAPPINGS as SEEDREAM50_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM50_DISPLAY_MAPPINGS
)

# 加载豆包LLM对话节点
from .doubao_chat_node import (
    NODE_CLASS_MAPPINGS as DOUBAO_CHAT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as DOUBAO_CHAT_DISPLAY_MAPPINGS
)

# 加载豆包视频生成节点
from .doubao_video_node import DoubaoVideoGeneration
from .doubao_seedance2_node import DoubaoSeedance2Node, DoubaoSeedance2AdvancedNode

DOUBAO_VIDEO_MAPPINGS = {
    "DapaoDoubaoVideoGeneration": DoubaoVideoGeneration,
    "DoubaoSeedance2Node": DoubaoSeedance2Node,
    "DoubaoSeedance2AdvancedNode": DoubaoSeedance2AdvancedNode
}
DOUBAO_VIDEO_DISPLAY_MAPPINGS = {
    "DapaoDoubaoVideoGeneration": "🎬Doubao视频生成 @炮老师的小课堂",
    "DoubaoSeedance2Node": "🥘seedance2.0视频基础@炮老师的小课堂",
    "DoubaoSeedance2AdvancedNode": "🥘seedance2.0视频高级@炮老师的小课堂"
}

# 加载 Grok LLM对话节点
from .grok_node import (
    NODE_CLASS_MAPPINGS as GROK_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as GROK_DISPLAY_MAPPINGS
)

# 加载 Grok 视频生成节点
from .grok_video_node import (
    NODE_CLASS_MAPPINGS as GROK_VIDEO_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as GROK_VIDEO_DISPLAY_MAPPINGS
)

# 加载魔塔 API 节点
from .modelscope_api_node import (
    NODE_CLASS_MAPPINGS as MODELSCOPE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as MODELSCOPE_DISPLAY_MAPPINGS
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

# 加载图像编辑API节点
from .image_edit_api_node import (
    NODE_CLASS_MAPPINGS as IMAGE_EDIT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as IMAGE_EDIT_DISPLAY_MAPPINGS
)

# 加载 Banana 整合版节点
from .banana_integrated_node import (
    NODE_CLASS_MAPPINGS as BANANA_INTEGRATED_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as BANANA_INTEGRATED_DISPLAY_MAPPINGS
)

# 加载 Gemini 3 多模态对话节点
from .gemini3_multimodal_chat_node import (
    NODE_CLASS_MAPPINGS as GEMINI3_CHAT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as GEMINI3_CHAT_DISPLAY_MAPPINGS
)

# 加载大炮提示词模板节点
from .dapao_template_node import (
    NODE_CLASS_MAPPINGS as PROMPT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as PROMPT_DISPLAY_MAPPINGS
)

# 加载 Dapao 详情页提示词节点
from .dapao_ecommerce_node import (
    NODE_CLASS_MAPPINGS as DAPAO_ECOMMERCE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as DAPAO_ECOMMERCE_DISPLAY_MAPPINGS
)

# 加载 Banana2 贞贞节点 / 官方节点 / 定制节点
from .banana2_zhenzhen_node import DapaoBanana2ZhenzhenNode, DapaoBanana2OfficialNode
from .banana2_flash_zhenzhen_node import DapaoBanana2FlashZhenzhenNode

BANANA2_ZHENZHEN_MAPPINGS = {
    "DapaoBanana2ZhenzhenNode": DapaoBanana2ZhenzhenNode,
    "DapaoBanana2FlashZhenzhenNode": DapaoBanana2FlashZhenzhenNode,
}

BANANA2_ZHENZHEN_DISPLAY_MAPPINGS = {
    "DapaoBanana2ZhenzhenNode": "🙈Banana2贞贞/柏拉图@炮老师的小课堂",
    "DapaoBanana2FlashZhenzhenNode": "🙈Banana2Flash贞贞/柏拉图@炮老师的小课堂",
}

BANANA2_OFFICIAL_MAPPINGS = {
    "DapaoBanana2OfficialNode": DapaoBanana2OfficialNode
}

BANANA2_OFFICIAL_DISPLAY_MAPPINGS = {
    "DapaoBanana2OfficialNode": "🙈Banana2官方@炮老师的小课堂"
}

# 加载对比打标节点
from .dapao_compare_tagging_node import (
    NODE_CLASS_MAPPINGS as COMPARE_TAGGING_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as COMPARE_TAGGING_DISPLAY_MAPPINGS
)

# 加载批量反推节点
from .dapao_api_batch_reverse_node import (
    NODE_CLASS_MAPPINGS as BATCH_REVERSE_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as BATCH_REVERSE_DISPLAY_MAPPINGS
)

# 加载 Gemini 指令节点（贞贞 / 官方）
try:
    from .gemini_instruction_zhenzhen_node import (
        DapaoGeminiInstructionZhenzhenNode,
        DapaoGeminiInstructionOfficialNode,
    )
    # 加载 Gemini 图像反推节点
    from .gemini_image_reverse_node import GeminiImageReverseNode
    
    GEMINI_ZHENZHEN_MAPPINGS = {
        "DapaoGeminiInstructionZhenzhenNode": DapaoGeminiInstructionZhenzhenNode
    }
    GEMINI_ZHENZHEN_DISPLAY_MAPPINGS = {
        "DapaoGeminiInstructionZhenzhenNode": "🦉Gemini指令贞贞/柏拉图@炮老师的小课堂"
    }
    GEMINI_OFFICIAL_MAPPINGS = {
        "DapaoGeminiInstructionOfficialNode": DapaoGeminiInstructionOfficialNode
    }
    GEMINI_OFFICIAL_DISPLAY_MAPPINGS = {
        "DapaoGeminiInstructionOfficialNode": "💓Gemini指令官方@炮老师的小课堂"
    }
    
    GEMINI_REVERSE_MAPPINGS = {
        "DapaoGeminiImageReverse": GeminiImageReverseNode
    }
    GEMINI_REVERSE_DISPLAY_MAPPINGS = {
        "DapaoGeminiImageReverse": "💐Gemini图像反推 @炮老师的小课堂"
    }
    
except Exception as e:
    print(f"[dapaoAPI] ❌ 警告：Gemini 指令贞贞节点加载失败: {e}")
    import traceback
    traceback.print_exc()
    GEMINI_ZHENZHEN_MAPPINGS = {}
    GEMINI_ZHENZHEN_DISPLAY_MAPPINGS = {}
    GEMINI_OFFICIAL_MAPPINGS = {}
    GEMINI_OFFICIAL_DISPLAY_MAPPINGS = {}
    GEMINI_REVERSE_MAPPINGS = {}
    GEMINI_REVERSE_DISPLAY_MAPPINGS = {}

from .dapao_template_adapter import DapaoPromptTemplateAdapter
from .dapao_user_templates_manager import DapaoUserTemplatesManager

# 合并所有节点映射
NODE_CLASS_MAPPINGS = {
    **SEEDREAM_MAPPINGS,
    **SEEDREAM45_MAPPINGS,
    **SEEDREAM50_MAPPINGS,
    **DOUBAO_CHAT_MAPPINGS,
    **DOUBAO_VIDEO_MAPPINGS,
    **GROK_MAPPINGS,
    **GROK_VIDEO_MAPPINGS,
    **MODELSCOPE_MAPPINGS,

    **GEMINI3_MAPPINGS,
    **UNIVERSAL_MAPPINGS,
    **IMAGE_EDIT_MAPPINGS,
    **BANANA_INTEGRATED_MAPPINGS,
    **BANANA2_ZHENZHEN_MAPPINGS,
    **BANANA2_OFFICIAL_MAPPINGS,
    **GEMINI3_CHAT_MAPPINGS,
    **PROMPT_MAPPINGS,
    **DAPAO_ECOMMERCE_MAPPINGS,
    **COMPARE_TAGGING_MAPPINGS,
    **BATCH_REVERSE_MAPPINGS,
    **GEMINI_ZHENZHEN_MAPPINGS,
    **GEMINI_OFFICIAL_MAPPINGS,
    **GEMINI_REVERSE_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **SEEDREAM_DISPLAY_MAPPINGS,
    **SEEDREAM45_DISPLAY_MAPPINGS,
    **SEEDREAM50_DISPLAY_MAPPINGS,
    **DOUBAO_CHAT_DISPLAY_MAPPINGS,
    **DOUBAO_VIDEO_DISPLAY_MAPPINGS,
    **GROK_DISPLAY_MAPPINGS,
    **GROK_VIDEO_DISPLAY_MAPPINGS,
    **MODELSCOPE_DISPLAY_MAPPINGS,

    **GEMINI3_DISPLAY_MAPPINGS,
    **UNIVERSAL_DISPLAY_MAPPINGS,
    **IMAGE_EDIT_DISPLAY_MAPPINGS,
    **BANANA_INTEGRATED_DISPLAY_MAPPINGS,
    **BANANA2_ZHENZHEN_DISPLAY_MAPPINGS,
    **BANANA2_OFFICIAL_DISPLAY_MAPPINGS,
    **GEMINI3_CHAT_DISPLAY_MAPPINGS,
    **PROMPT_DISPLAY_MAPPINGS,
    **DAPAO_ECOMMERCE_DISPLAY_MAPPINGS,
    **COMPARE_TAGGING_DISPLAY_MAPPINGS,
    **BATCH_REVERSE_DISPLAY_MAPPINGS,
    **GEMINI_ZHENZHEN_DISPLAY_MAPPINGS,
    **GEMINI_OFFICIAL_DISPLAY_MAPPINGS,
    **GEMINI_REVERSE_DISPLAY_MAPPINGS,
}

# 声明 Web 目录，用于加载 JavaScript 扩展
WEB_DIRECTORY = "./web"

# --- Dapao API ---
# Initialize adapter once
ADAPTER_INSTANCE = DapaoPromptTemplateAdapter()
USER_TEMPLATES_MANAGER = DapaoUserTemplatesManager()

# Base directory for this extension
EXTENSION_DIR = Path(__file__).parent

@server.PromptServer.instance.routes.get("/dapao/categories")
async def get_dapao_categories(request: aiohttp.web.Request):
    """
    API endpoint to get all template categories.
    Query params:
    - lang: 'zh' or 'en' (default: 'zh')
    """
    try:
        lang = request.query.get("lang", "zh")
        categories = ADAPTER_INSTANCE.get_all_categories(lang)
        return aiohttp.web.json_response(categories)
    except Exception as e:
        print(f"Error in /dapao/categories: {e}")
        traceback.print_exc()
        return aiohttp.web.json_response({"error": str(e)}, status=500)


@server.PromptServer.instance.routes.get("/dapao/templates")
async def get_dapao_templates(request: aiohttp.web.Request):
    """
    API endpoint to get templates by category.
    ?category=<category_id>
    """
    category_id = request.query.get("category", None)
    
    if not category_id:
        return aiohttp.web.json_response(
            {"error": "Category ID is required"}, status=400
        )
    
    try:
        # The frontend doesn't need language-specific templates from this endpoint,
        # it gets both and switches locally.
        templates = ADAPTER_INSTANCE.get_templates_by_category(category_id)
        return aiohttp.web.json_response(templates)
    except Exception as e:
        print(f"Error in /dapao/templates: {e}")
        traceback.print_exc()
        return aiohttp.web.json_response(
            {"error": str(e)}, status=500
        )


@server.PromptServer.instance.routes.get("/dapao/images/{image_path:.*}")
async def get_dapao_image(request: aiohttp.web.Request):
    """
    Serve image files from the gpt4o-image-prompts-master directory
    and external user directory
    Example: /dapao/images/333.jpeg
    """
    try:
        image_path = request.match_info['image_path']
        
        # 1. Try Internal Path
        internal_path = EXTENSION_DIR / "bananapro-image-prompts-master" / "gpt4o-image-prompts-master" / "images" / image_path
        if internal_path.exists() and internal_path.is_relative_to(EXTENSION_DIR):
             return aiohttp.web.FileResponse(internal_path)

        return aiohttp.web.Response(status=404, text="Not Found")
        
    except Exception as e:
        print(f"Error serving image {image_path}: {e}")
        return aiohttp.web.Response(status=500, text=str(e))


# ===== User Templates API =====

@server.PromptServer.instance.routes.get("/dapao/user-assets/{image_path:.*}")
async def get_user_asset(request: aiohttp.web.Request):
    """Serve user uploaded assets"""
    try:
        image_path = request.match_info['image_path']
        asset_path = EXTENSION_DIR / "user_assets" / image_path
        
        if asset_path.exists() and asset_path.is_relative_to(EXTENSION_DIR):
            return aiohttp.web.FileResponse(asset_path)
            
        return aiohttp.web.Response(status=404, text="Not Found")
    except Exception as e:
        return aiohttp.web.Response(status=500, text=str(e))

@server.PromptServer.instance.routes.post("/dapao/upload-image")
async def upload_user_image(request: aiohttp.web.Request):
    """
    Upload an image or use a ComfyUI generated image.
    Compresses to < 100KB.
    """
    import io
    from PIL import Image
    import folder_paths
    import time
    import shutil

    try:
        reader = await request.multipart()
        
        # Check if it's a file upload or a comfy image reference
        field = await reader.next()
        
        img = None
        filename_prefix = "upload"
        
        if field.name == 'image':
            # File Upload
            filename = field.filename
            file_content = await field.read()
            img = Image.open(io.BytesIO(file_content))
            filename_prefix = Path(filename).stem
            
        elif field.name == 'comfy_image':
            # ComfyUI Generated Image
            data = await field.json()
            filename = data.get('filename')
            subfolder = data.get('subfolder', '')
            image_type = data.get('type', 'output')
            
            # Resolve path
            if image_type == 'output':
                base_dir = folder_paths.get_output_directory()
            elif image_type == 'temp':
                base_dir = folder_paths.get_temp_directory()
            else:
                base_dir = folder_paths.get_input_directory()
                
            image_path = Path(base_dir) / subfolder / filename
            if not image_path.exists():
                return aiohttp.web.json_response({"error": "Source image not found"}, status=404)
                
            img = Image.open(image_path)
            filename_prefix = Path(filename).stem
            
        else:
             return aiohttp.web.json_response({"error": "No image provided"}, status=400)
             
        # Process Image (Compress < 100KB)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
            
        # Resize if too large (max 1024px)
        max_dim = 1024
        if max(img.size) > max_dim:
            ratio = max_dim / max(img.size)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            
        # Compress loop
        output_io = io.BytesIO()
        quality = 90
        while quality >= 10:
            output_io.seek(0)
            output_io.truncate()
            img.save(output_io, format='JPEG', quality=quality, optimize=True)
            size_kb = output_io.tell() / 1024
            if size_kb < 100:
                break
            quality -= 5
            
        # Save to user_assets/images
        timestamp = int(time.time())
        save_filename = f"{filename_prefix}_{timestamp}.jpeg"
        save_dir = EXTENSION_DIR / "user_assets" / "images"
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / save_filename
        
        with open(save_path, "wb") as f:
            f.write(output_io.getvalue())
            
        # Return relative URL
        url = f"/dapao/user-assets/images/{save_filename}"
        return aiohttp.web.json_response({"url": url, "size_kb": round(size_kb, 2)})

    except Exception as e:
        print(f"Error uploading image: {e}")
        traceback.print_exc()
        return aiohttp.web.json_response({"error": str(e)}, status=500)

@server.PromptServer.instance.routes.get("/dapao/user-templates")
async def get_user_templates(request: aiohttp.web.Request):
    """Get all user-created templates"""
    try:
        templates = USER_TEMPLATES_MANAGER.get_all_templates()
        return aiohttp.web.json_response(templates)
    except Exception as e:
        print(f"Error in /dapao/user-templates: {e}")
        traceback.print_exc()
        return aiohttp.web.json_response({"error": str(e)}, status=500)


@server.PromptServer.instance.routes.post("/dapao/user-templates")
async def create_user_template(request: aiohttp.web.Request):
    """Create a new user template"""
    try:
        data = await request.json()
        result = USER_TEMPLATES_MANAGER.create_template(data)
        
        if result.get("success"):
            return aiohttp.web.json_response(result, status=201)
        else:
            return aiohttp.web.json_response(result, status=400)
    
    except Exception as e:
        print(f"Error creating user template: {e}")
        traceback.print_exc()
        return aiohttp.web.json_response({"error": str(e)}, status=500)


@server.PromptServer.instance.routes.put("/dapao/user-templates/{template_id}")
async def update_user_template(request: aiohttp.web.Request):
    """Update a user template"""
    try:
        template_id = request.match_info['template_id']
        data = await request.json()
        result = USER_TEMPLATES_MANAGER.update_template(template_id, data)
        
        if result.get("success"):
            return aiohttp.web.json_response(result)
        else:
            return aiohttp.web.json_response(result, status=404 if "not found" in result.get("error", "") else 400)
    
    except Exception as e:
        print(f"Error updating user template: {e}")
        traceback.print_exc()
        return aiohttp.web.json_response({"error": str(e)}, status=500)


@server.PromptServer.instance.routes.delete("/dapao/user-templates/{template_id}")
async def delete_user_template(request: aiohttp.web.Request):
    """Delete a user template"""
    try:
        template_id = request.match_info['template_id']
        result = USER_TEMPLATES_MANAGER.delete_template(template_id)
        
        if result.get("success"):
            return aiohttp.web.json_response(result)
        else:
            return aiohttp.web.json_response(result, status=404 if "not found" in result.get("error", "") else 400)
    
    except Exception as e:
        print(f"Error deleting user template: {e}")
        traceback.print_exc()
        return aiohttp.web.json_response({"error": str(e)}, status=500)

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# 启动信息
print("=" * 60)
print("  🎨 大炮 API (dapaoAPI) 节点加载完成!")
print("=" * 60)
print(f"  📦 Seedream 4.0 节点：{len(SEEDREAM_MAPPINGS)} 个")
print(f"  🌟 Seedream 4.5 节点：{len(SEEDREAM45_MAPPINGS)} 个")
print(f"  💬 豆包LLM对话：{len(DOUBAO_CHAT_MAPPINGS)} 个")
print(f"  🎬 豆包视频生成：{len(DOUBAO_VIDEO_MAPPINGS)} 个")
print(f"  💬 Grok LLM对话：{len(GROK_MAPPINGS)} 个")
print(f"  💎 Gemini 3多功能：{len(GEMINI3_MAPPINGS)} 个")
print(f"  💎 Gemini 3对话（官方+T8）：{len(GEMINI3_CHAT_MAPPINGS)} 个")
print(f"  🌐 通用API调用：{len(UNIVERSAL_MAPPINGS)} 个")
print(f"  🎨 图像编辑API：{len(IMAGE_EDIT_MAPPINGS)} 个")
print(f"  🍌 Banana整合版：{len(BANANA_INTEGRATED_MAPPINGS) + len(BANANA2_ZHENZHEN_MAPPINGS)} 个")
print(f"  🎨 大炮提示词模板：{len(PROMPT_MAPPINGS)} 个")
print(f"  🔍 对比打标节点：{len(COMPARE_TAGGING_MAPPINGS)} 个")
print(f"  🍭 批量反推节点：{len(BATCH_REVERSE_MAPPINGS)} 个")
print(f"  💓 Gemini 指令贞贞：{len(GEMINI_ZHENZHEN_MAPPINGS)} 个")
print(f"  💓 Gemini 指令官方：{len(GEMINI_OFFICIAL_MAPPINGS)} 个")
print(f"  💐 Gemini 图像反推：{len(GEMINI_REVERSE_MAPPINGS)} 个")
print(f"  ✅ 总计：{len(NODE_CLASS_MAPPINGS)} 个节点")
print(f"  👨‍🏫 作者：@炮老师的小课堂")
print(f"  🎨 主题：紫色标题栏 + 橙棕色背景")
print("=" * 60)
