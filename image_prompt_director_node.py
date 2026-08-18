"""LLM-powered all-round image prompt compiler for ComfyUI.

The node is prompt-only: it never calls an image-generation endpoint.  It
adapts the Garden gpt-image-2 skill's structured template methodology into an
independent dapaoAI LLM node suitable for GPT Image 2 and other image models.
Template taxonomy adapted from ConardLi/garden-skills (MIT License, 2026).
"""

import asyncio
import base64
import io
import json
import sys
import time
import traceback

import numpy as np
import requests
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error
from .image_input_utils import IMAGE_429_HINT, resize_pil_for_input


API_BASE_URL = "https://api.dapaoai.com"
CHAT_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
NODE_NAME = "DapaoAllroundImagePromptNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮API常用工具🍬"
DISPLAY_NAME = "🪂全能image提示词生成@炮老师的小课堂"

MODEL_OPTIONS = [
    "gpt-5.5",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "gpt-5.6-sol",
    "claude-fable-5",
    "claude-opus-4-8",
    "claude-opus-5",
    "claude-sonnet-5",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
]

TASK_OPTIONS = [
    "自动识别",
    "新建图像提示词",
    "优化现有提示词",
    "参考图创作提示词",
    "图像编辑提示词",
    "蒙版局部编辑提示词",
    "提示词诊断与重写",
]

CATEGORY_LABELS = {
    "自动识别": "auto",
    "UI界面样机": "ui-mockups",
    "产品商业视觉": "product-visuals",
    "地图与路线": "maps",
    "幻灯片与视觉文档": "slides-and-visual-docs",
    "海报与Campaign": "poster-and-campaigns",
    "人物与角色设定": "portraits-and-characters",
    "场景与插画": "scenes-and-illustrations",
    "图像编辑工作流": "editing-workflows",
    "头像与个人形象": "avatars-and-profile",
    "分镜漫画与序列": "storyboards-and-sequences",
    "网格与拼贴": "grids-and-collages",
    "品牌与包装": "branding-and-packaging",
    "字体与文字版式": "typography-and-text-layout",
    "图标游戏与素材": "assets-and-props",
    "学术论文配图": "academic-figures",
    "信息图与数据看板": "infographics",
    "技术架构与工程图": "technical-diagrams",
}
CATEGORY_OPTIONS = list(CATEGORY_LABELS)

TEMPLATE_PATHS = [
    "academic-figures/graphical-abstract",
    "academic-figures/mechanism-diagram",
    "academic-figures/method-pipeline-overview",
    "academic-figures/multi-condition-comparison",
    "academic-figures/neural-network-architecture",
    "academic-figures/publication-chart",
    "academic-figures/qualitative-comparison-grid",
    "academic-figures/research-overview-poster",
    "academic-figures/scientific-schematic",
    "assets-and-props/game-screenshot-mockup",
    "assets-and-props/retro-skeuomorphic-icons",
    "avatars-and-profile/character-grid-portrait",
    "avatars-and-profile/cultural-portrait-series",
    "avatars-and-profile/sticker-set",
    "avatars-and-profile/style-transfer-selfie",
    "avatars-and-profile/themed-3d-icon",
    "branding-and-packaging/beverage-label-design",
    "branding-and-packaging/brand-identity-board",
    "branding-and-packaging/character-merch-board",
    "branding-and-packaging/cosmetic-packaging",
    "branding-and-packaging/full-mascot-brand-doc",
    "branding-and-packaging/mascot-brand-kit",
    "editing-workflows/background-replacement",
    "editing-workflows/local-object-replacement",
    "editing-workflows/object-removal",
    "editing-workflows/portrait-local-edit",
    "editing-workflows/product-retouching",
    "grids-and-collages/ad-banner-multi-grid",
    "grids-and-collages/anime-pitch-board",
    "grids-and-collages/banner-grid-2x2",
    "grids-and-collages/lookbook-grid",
    "grids-and-collages/mixed-style-multi-panel",
    "infographics/bento-grid-infographic",
    "infographics/comparison-infographic",
    "infographics/hand-drawn-infographic",
    "infographics/kpi-dashboard-infographic",
    "infographics/legend-heavy-infographic",
    "infographics/step-by-step-infographic",
    "maps/food-map",
    "maps/illustrated-city-map",
    "maps/itinerary-day-trip-map",
    "maps/store-distribution-map",
    "maps/travel-route-map",
    "portraits-and-characters/character-sheet",
    "portraits-and-characters/founder-portrait",
    "portraits-and-characters/pose-reference-sheet",
    "portraits-and-characters/professional-portrait",
    "portraits-and-characters/virtual-host",
    "poster-and-campaigns/banner-hero",
    "poster-and-campaigns/biomimetic-concept-poster",
    "poster-and-campaigns/brand-poster",
    "poster-and-campaigns/campaign-kv",
    "poster-and-campaigns/character-catalog-poster",
    "poster-and-campaigns/editorial-cover",
    "poster-and-campaigns/lineup-comparison-poster",
    "poster-and-campaigns/vintage-editorial-infographic",
    "product-visuals/ecommerce-marketing-board",
    "product-visuals/exploded-view-poster",
    "product-visuals/lifestyle-product-scene",
    "product-visuals/packaging-showcase",
    "product-visuals/premium-studio-product",
    "product-visuals/white-background-product",
    "scenes-and-illustrations/concept-scene",
    "scenes-and-illustrations/healing-scene",
    "scenes-and-illustrations/minimalist-mood-scene",
    "scenes-and-illustrations/picture-book-scene",
    "slides-and-visual-docs/dense-explainer-slides",
    "slides-and-visual-docs/educational-diagram-slide",
    "slides-and-visual-docs/policy-style-slide",
    "slides-and-visual-docs/visual-report-page",
    "storyboards-and-sequences/anime-key-visual",
    "storyboards-and-sequences/character-relationship-diagram",
    "storyboards-and-sequences/cinematic-storyboard-grid",
    "storyboards-and-sequences/four-panel-comic",
    "storyboards-and-sequences/manga-spread-page",
    "storyboards-and-sequences/process-photo-board",
    "storyboards-and-sequences/product-tvc-storyboard",
    "storyboards-and-sequences/recipe-process-flowchart",
    "technical-diagrams/er-diagram",
    "technical-diagrams/flowchart-decision",
    "technical-diagrams/mind-map-tech",
    "technical-diagrams/network-topology",
    "technical-diagrams/sequence-diagram",
    "technical-diagrams/state-machine",
    "technical-diagrams/system-architecture",
    "typography-and-text-layout/bilingual-layout-visual",
    "typography-and-text-layout/title-safe-poster",
    "ui-mockups/chat-interface-scene",
    "ui-mockups/landing-page-case-study",
    "ui-mockups/live-commerce-ui",
    "ui-mockups/product-card-overlay",
    "ui-mockups/short-video-cover-ui",
    "ui-mockups/social-interface-mockup",
]
TEMPLATE_LABEL_BY_PATH = {
    "academic-figures/graphical-abstract": "学术论文配图｜图形摘要",
    "academic-figures/mechanism-diagram": "学术论文配图｜机理示意图",
    "academic-figures/method-pipeline-overview": "学术论文配图｜方法流程总览图",
    "academic-figures/multi-condition-comparison": "学术论文配图｜多条件对比图",
    "academic-figures/neural-network-architecture": "学术论文配图｜神经网络架构图",
    "academic-figures/publication-chart": "学术论文配图｜论文数据图表",
    "academic-figures/qualitative-comparison-grid": "学术论文配图｜定性对比网格",
    "academic-figures/research-overview-poster": "学术论文配图｜研究总览海报",
    "academic-figures/scientific-schematic": "学术论文配图｜科学示意图",
    "assets-and-props/game-screenshot-mockup": "图标游戏与素材｜游戏截图样机",
    "assets-and-props/retro-skeuomorphic-icons": "图标游戏与素材｜复古拟物图标集",
    "avatars-and-profile/character-grid-portrait": "头像与个人形象｜角色网格肖像",
    "avatars-and-profile/cultural-portrait-series": "头像与个人形象｜文化肖像系列",
    "avatars-and-profile/sticker-set": "头像与个人形象｜贴纸与表情包套装",
    "avatars-and-profile/style-transfer-selfie": "头像与个人形象｜自拍风格转换",
    "avatars-and-profile/themed-3d-icon": "头像与个人形象｜主题3D图标",
    "branding-and-packaging/beverage-label-design": "品牌与包装｜饮料食品标签设计",
    "branding-and-packaging/brand-identity-board": "品牌与包装｜品牌识别系统板",
    "branding-and-packaging/character-merch-board": "品牌与包装｜角色周边展示板",
    "branding-and-packaging/cosmetic-packaging": "品牌与包装｜化妆品包装设计",
    "branding-and-packaging/full-mascot-brand-doc": "品牌与包装｜完整吉祥物品牌文档",
    "branding-and-packaging/mascot-brand-kit": "品牌与包装｜吉祥物品牌套装",
    "editing-workflows/background-replacement": "图像编辑工作流｜背景替换",
    "editing-workflows/local-object-replacement": "图像编辑工作流｜局部对象替换",
    "editing-workflows/object-removal": "图像编辑工作流｜物体移除",
    "editing-workflows/portrait-local-edit": "图像编辑工作流｜人像局部编辑",
    "editing-workflows/product-retouching": "图像编辑工作流｜产品精修",
    "grids-and-collages/ad-banner-multi-grid": "网格与拼贴｜多行业广告网格",
    "grids-and-collages/anime-pitch-board": "网格与拼贴｜动漫项目提案板",
    "grids-and-collages/banner-grid-2x2": "网格与拼贴｜2×2营销横幅网格",
    "grids-and-collages/lookbook-grid": "网格与拼贴｜造型图鉴网格",
    "grids-and-collages/mixed-style-multi-panel": "网格与拼贴｜多风格混合面板",
    "infographics/bento-grid-infographic": "信息图与数据看板｜便当格信息图",
    "infographics/comparison-infographic": "信息图与数据看板｜对比信息图",
    "infographics/hand-drawn-infographic": "信息图与数据看板｜手绘信息图",
    "infographics/kpi-dashboard-infographic": "信息图与数据看板｜KPI仪表盘信息图",
    "infographics/legend-heavy-infographic": "信息图与数据看板｜高图例密度信息图",
    "infographics/step-by-step-infographic": "信息图与数据看板｜分步骤教程信息图",
    "maps/food-map": "地图与路线｜城市美食地图",
    "maps/illustrated-city-map": "地图与路线｜城市风貌插画地图",
    "maps/itinerary-day-trip-map": "地图与路线｜一日游行程地图",
    "maps/store-distribution-map": "地图与路线｜门店分布地图",
    "maps/travel-route-map": "地图与路线｜旅行路线地图",
    "portraits-and-characters/character-sheet": "人物与角色设定｜角色设定稿",
    "portraits-and-characters/founder-portrait": "人物与角色设定｜创始人媒体肖像",
    "portraits-and-characters/pose-reference-sheet": "人物与角色设定｜姿势动作参考表",
    "portraits-and-characters/professional-portrait": "人物与角色设定｜职业商务肖像",
    "portraits-and-characters/virtual-host": "人物与角色设定｜虚拟主播形象",
    "poster-and-campaigns/banner-hero": "海报与Campaign｜网页主视觉横幅",
    "poster-and-campaigns/biomimetic-concept-poster": "海报与Campaign｜仿生概念海报",
    "poster-and-campaigns/brand-poster": "海报与Campaign｜品牌主海报",
    "poster-and-campaigns/campaign-kv": "海报与Campaign｜Campaign主视觉",
    "poster-and-campaigns/character-catalog-poster": "海报与Campaign｜角色图鉴海报",
    "poster-and-campaigns/editorial-cover": "海报与Campaign｜杂志编辑封面",
    "poster-and-campaigns/lineup-comparison-poster": "海报与Campaign｜系列产品对比海报",
    "poster-and-campaigns/vintage-editorial-infographic": "海报与Campaign｜复古编辑式信息海报",
    "product-visuals/ecommerce-marketing-board": "产品商业视觉｜电商营销综合看板",
    "product-visuals/exploded-view-poster": "产品商业视觉｜产品爆炸视图海报",
    "product-visuals/lifestyle-product-scene": "产品商业视觉｜生活方式产品场景",
    "product-visuals/packaging-showcase": "产品商业视觉｜包装礼盒展示",
    "product-visuals/premium-studio-product": "产品商业视觉｜高端影棚产品图",
    "product-visuals/white-background-product": "产品商业视觉｜电商白底产品图",
    "scenes-and-illustrations/concept-scene": "场景与插画｜电影感概念场景",
    "scenes-and-illustrations/healing-scene": "场景与插画｜治愈系日常场景",
    "scenes-and-illustrations/minimalist-mood-scene": "场景与插画｜极简留白氛围图",
    "scenes-and-illustrations/picture-book-scene": "场景与插画｜童书绘本场景",
    "slides-and-visual-docs/dense-explainer-slides": "幻灯片与视觉文档｜高密度讲解单页",
    "slides-and-visual-docs/educational-diagram-slide": "幻灯片与视觉文档｜教学示意图单页",
    "slides-and-visual-docs/policy-style-slide": "幻灯片与视觉文档｜政策解读风单页",
    "slides-and-visual-docs/visual-report-page": "幻灯片与视觉文档｜商业视觉报告页",
    "storyboards-and-sequences/anime-key-visual": "分镜漫画与序列｜动漫主视觉",
    "storyboards-and-sequences/character-relationship-diagram": "分镜漫画与序列｜角色关系图",
    "storyboards-and-sequences/cinematic-storyboard-grid": "分镜漫画与序列｜电影感分镜网格",
    "storyboards-and-sequences/four-panel-comic": "分镜漫画与序列｜四格漫画",
    "storyboards-and-sequences/manga-spread-page": "分镜漫画与序列｜漫画单页与跨页",
    "storyboards-and-sequences/process-photo-board": "分镜漫画与序列｜真人流程摄影板",
    "storyboards-and-sequences/product-tvc-storyboard": "分镜漫画与序列｜产品TVC广告分镜",
    "storyboards-and-sequences/recipe-process-flowchart": "分镜漫画与序列｜食谱步骤流程图",
    "technical-diagrams/er-diagram": "技术架构与工程图｜ER数据关系图",
    "technical-diagrams/flowchart-decision": "技术架构与工程图｜流程与决策图",
    "technical-diagrams/mind-map-tech": "技术架构与工程图｜技术思维导图",
    "technical-diagrams/network-topology": "技术架构与工程图｜网络拓扑图",
    "technical-diagrams/sequence-diagram": "技术架构与工程图｜系统时序图",
    "technical-diagrams/state-machine": "技术架构与工程图｜状态机图",
    "technical-diagrams/system-architecture": "技术架构与工程图｜系统架构图",
    "typography-and-text-layout/bilingual-layout-visual": "字体与文字版式｜双语版式视觉",
    "typography-and-text-layout/title-safe-poster": "字体与文字版式｜大字标题安全海报",
    "ui-mockups/chat-interface-scene": "UI界面样机｜聊天界面样机",
    "ui-mockups/landing-page-case-study": "UI界面样机｜长页面与案例页样机",
    "ui-mockups/live-commerce-ui": "UI界面样机｜直播电商界面",
    "ui-mockups/product-card-overlay": "UI界面样机｜产品卡片叠层界面",
    "ui-mockups/short-video-cover-ui": "UI界面样机｜短视频封面界面",
    "ui-mockups/social-interface-mockup": "UI界面样机｜社交平台界面样机",
}
TEMPLATE_PATH_BY_LABEL = {label: path for path, label in TEMPLATE_LABEL_BY_PATH.items()}
TEMPLATE_OPTIONS = ["自动选择模板"] + [TEMPLATE_LABEL_BY_PATH[path] for path in TEMPLATE_PATHS]

TARGET_MODEL_OPTIONS = [
    "GPT Image 2 / OpenAI兼容",
    "通用Image模型",
    "Banana / Gemini Image",
    "Midjourney",
    "FLUX",
    "Stable Diffusion",
]
PROMPT_FORMAT_OPTIONS = ["自动", "结构化JSON", "结构化自然语言", "精简自然语言"]
DETAIL_OPTIONS = ["简洁", "标准", "专业高密度"]
ASPECT_RATIO_OPTIONS = ["自动", "1:1", "16:9", "9:16", "4:3", "3:4", "21:9", "2:3", "3:2"]
MAX_IMAGES = 9

CATEGORY_GUIDANCE = {
    "ui-mockups": "界面必须具有真实产品层级、组件间距、可读文字、状态反馈和可信导航；只生成视觉样机，不宣称是可交互网页。",
    "product-visuals": "产品身份、真实颜色、材质、比例、结构和Logo优先；构图围绕商品卖点，不虚构性能。",
    "maps": "路线、编号、地标、图例和顺序必须一致；无法核实的地理事实应标示为示意。",
    "slides-and-visual-docs": "用明确标题层级、模块、数据区和注释系统组织一页视觉文档，避免PPT装饰堆叠。",
    "poster-and-campaigns": "建立主视觉、标题安全区、品牌系统和衍生裁切逻辑；文案必须准确。",
    "portraits-and-characters": "锁定身份、年龄段、脸型、发型、服装和姿势；多视图保持角色一致。",
    "scenes-and-illustrations": "明确前中后景、视角、主体尺度、光源、色彩和情绪载体。",
    "editing-workflows": "原图为事实源，只修改用户指定区域；保持构图、身份、光线、透视和无关像素稳定。",
    "avatars-and-profile": "身份一致优先，风格变化不能改掉可识别特征；网格或贴纸需保持统一角色设计。",
    "storyboards-and-sequences": "按行优先顺序明确每格景别、动作和连续性；同一人物、产品和环境必须一致。",
    "grids-and-collages": "先定义网格、面板数量、每格职责和跨格统一规则，禁止随机重复。",
    "branding-and-packaging": "品牌名、Logo、配色、包装结构和应用场景形成一套系统；不捏造认证、奖项和合作。",
    "typography-and-text-layout": "准确文字是画面核心，明确语言、字重、层级、安全区和断行规则。",
    "assets-and-props": "成套素材必须统一透视、光线、材质、描边、尺寸和背景规范。",
    "academic-figures": "白底、几何精确、出版物级可读；严禁虚构数据、公式、实验结果和模型指标。",
    "infographics": "先建立信息层级、图例、编号和阅读路径；没有真实数据时使用示例占位而非伪造事实。",
    "technical-diagrams": "节点、连接线、方向、协议、状态和标签必须可读；输出是位图示意，不宣称可编辑SVG。",
}


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(str(message).encode(encoding, errors="replace").decode(encoding, errors="replace"))


def _log_error(message):
    _safe_print(f"[dapaoAPI-全能image提示词] 错误：{message}")


def _image_data_uris(image_tensor, max_side=2048):
    result = []
    for item in image_tensor:
        array = np.clip(item.detach().cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        image = resize_pil_for_input(Image.fromarray(array).convert("RGB"), max_side)
        if max(image.size) > max_side:
            scale = max_side / max(image.size)
            image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        result.append("data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii"))
    return result


def _mask_data_uri(mask_tensor):
    array = mask_tensor.detach().cpu().numpy()
    if array.ndim == 3:
        array = array[0]
    array = np.clip(array * 255.0, 0, 255).astype(np.uint8)
    image = Image.fromarray(array, mode="L")
    if max(image.size) > 1536:
        scale = 1536 / max(image.size)
        image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.NEAREST)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")


def _content_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    texts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        value = item.get("text") or item.get("output_text")
        if isinstance(value, dict):
            value = value.get("value") or value.get("text")
        if value:
            texts.append(str(value))
    return "\n".join(texts)


def _extract_text(result):
    if not isinstance(result, dict):
        return ""
    choices = result.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        return _content_text(message.get("content")) or str(first.get("text") or "")
    return str(result.get("output_text") or "")


def _parse_json(text):
    cleaned = str(text or "").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for index, char in enumerate(cleaned):
            if char != "{":
                continue
            try:
                value, _ = decoder.raw_decode(cleaned[index:])
                if isinstance(value, dict):
                    return value
            except json.JSONDecodeError:
                continue
    return {}


def _sanitized(value):
    if isinstance(value, dict):
        return {key: _sanitized(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitized(item) for item in value]
    if isinstance(value, str) and (value.startswith("data:") or len(value) > 20000):
        return f"<内容已省略，共{len(value)}字符>"
    return value


def _category_catalog_text():
    grouped = {}
    for path in TEMPLATE_PATHS:
        category, template = path.split("/", 1)
        grouped.setdefault(category, []).append(template)
    return "\n".join(f"- {category}: {', '.join(items)}" for category, items in grouped.items())


SYSTEM_PROMPT = f"""你是一个专业的图像创意总监、结构化提示词工程师和图像编辑监督。
你只负责生成或优化提示词，不调用图像生成接口，不宣称已经出图。

工作方法来自 GPT Image 2 结构化视觉模板体系：
1. 先识别任务类别和最匹配的具体模板，只使用一个主模板；必要时借用一个辅助模板的局部规则。
2. 简单单主体任务可用自然语言；多区域UI、产品看板、信息图、学术图、技术图、分镜和品牌系统优先使用结构化JSON。
3. 最终提示词必须明确：用途、主体、场景、布局、风格、关键细节、准确文字、必须保留和必须避免。
4. 用户已经提供的信息优先；无关细节可合理默认；品牌、价格、文案、论文数据、公式、产品参数等事实不能擅自编造。
5. 编辑任务以参考图为事实源，只改用户指定内容；有蒙版时只在蒙版区域修改，并匹配原图光线、阴影、材质、透视和噪点。
6. 优化现有提示词时保留原意，只修复歧义、冲突、缺失布局、身份漂移和文字不准确等问题。
7. 对长页面、复杂图表和高密度文字，要主动控制信息量，并说明位图模型无法保证像素级排版和可编辑矢量输出。
8. 不输出关于本系统、Skill文件或内部路由的解释。

类别专用规则：
{json.dumps(CATEGORY_GUIDANCE, ensure_ascii=False, indent=2)}

可选模板目录：
{_category_catalog_text()}

只返回JSON对象，字段固定为：
task, category, template, final_prompt, prompt_format, parameter_analysis, missing_critical_information, recommended_generation_parameters, production_notes。
final_prompt必须是可以直接交给图像模型的完整提示词。
"""

LANGUAGE_POLICY_CHINESE = """
【最高优先级语言规则】
用户已开启“输出中文提示词”。返回JSON中的 final_prompt 必须完整使用简体中文；如果 final_prompt 是结构化JSON，其字段名和字段值也必须使用简体中文。除用户要求逐字保留的原文、品牌名、模型名、产品名、代码、公式和通用技术缩写外，不得输出英文句子。parameter_analysis、missing_critical_information、recommended_generation_parameters 和 production_notes 的说明文字也使用简体中文。先在内部完成翻译再返回，不能解释语言规则。
"""

LANGUAGE_POLICY_ENGLISH = """
【输出语言规则】
用户未开启中文提示词。final_prompt 默认使用自然、专业的英文；用户要求逐字保留的中文画面文字必须原样保留。
"""


def _as_bool(value):
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "是", "开启"}
    return bool(value)


def _has_sufficient_chinese(text):
    """Require Chinese to be the prompt's main prose language.

    A few Chinese words inside an otherwise English prompt must not pass the
    check. Latin text is still allowed for brands, model names and common
    technical terms.
    """
    value = str(text or "")
    chinese_count = sum(1 for char in value if "\u4e00" <= char <= "\u9fff")
    latin_count = sum(1 for char in value if char.isascii() and char.isalpha())
    return chinese_count >= 8 and chinese_count >= latin_count * 0.45


class ImagePromptLLMClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/AllroundImagePrompt",
        }
        try:
            response = requests.post(CHAT_ENDPOINT, headers=headers, json=payload, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RuntimeError(f"{friendly_network_error(error, '提交LLM请求')} LLM请求不会自动重试，以免重复扣费。") from error
        if response.status_code >= 400:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status())
            labels = {400: "请求参数错误", 401: "认证失败", 402: "余额不足", 403: "没有模型权限", 404: "映射模型不存在", 429: IMAGE_429_HINT}
            try:
                detail = response.json()
            except Exception:
                detail = response.text[:1000]
            raise RuntimeError(f"{labels.get(response.status_code, '中转站请求失败')} {response.status_code}：{detail}")
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站返回内容不是JSON：{response.text[:500]}") from error


class DapaoAllroundImagePromptNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "📝 需要优化的现有提示词": ("STRING", {"multiline": True, "default": "", "tooltip": "优化、诊断或改写任务使用。"}),
            "🔤 画面准确文字与数据": ("STRING", {"multiline": True, "default": "", "tooltip": "填写必须逐字保留的标题、价格、数据、标签或公式。"}),
            "🔒 必须保留": ("STRING", {"multiline": True, "default": "", "tooltip": "参考图身份、产品结构、Logo、构图、背景等不可改变内容。"}),
            "🚫 禁止出现": ("STRING", {"multiline": True, "default": "", "tooltip": "不希望出现的对象、风格、文字或错误。"}),
            "📎 参考素材用途说明": ("STRING", {"multiline": True, "default": "", "tooltip": "说明每张参考图控制身份、产品、风格、构图、姿势或背景中的哪一项。"}),
            "🎭 蒙版": ("MASK", {"tooltip": "局部编辑提示词使用；白色区域表示允许修改。"}),
            "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
        }
        for index in range(1, MAX_IMAGES + 1):
            optional[f"🖼️ 参考图{index}"] = ("IMAGE", {"tooltip": f"给LLM分析的参考图{index}，最多{MAX_IMAGES}张。"})
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 dapaoAI API 密钥", "tooltip": "密钥只用于请求 https://api.dapaoai.com。"}),
                "🤖 LLM模型": (MODEL_OPTIONS, {"default": "gemini-3.7-flash"}),
                "🎛️ 任务模式": (TASK_OPTIONS, {"default": "自动识别"}),
                "🗂️ 设计分类": (CATEGORY_OPTIONS, {"default": "自动识别"}),
                "🧩 具体模板": (TEMPLATE_OPTIONS, {"default": "自动选择模板"}),
                "🎯 目标图像模型": (TARGET_MODEL_OPTIONS, {"default": "GPT Image 2 / OpenAI兼容"}),
                "🌐 输出中文提示词": ("BOOLEAN", {"default": False, "tooltip": "关闭时默认输出英文提示词，开启后输出简体中文。"}),
                "📝 原始图像需求": ("STRING", {"multiline": True, "default": "设计一张构图清晰、信息层级明确、细节专业的商业视觉图片。", "placeholder": "描述要生成或编辑的图片……"}),
                "📐 图片比例": (ASPECT_RATIO_OPTIONS, {"default": "自动"}),
                "📚 提示词格式": (PROMPT_FORMAT_OPTIONS, {"default": "自动"}),
                "🧠 细节密度": (DETAIL_OPTIONS, {"default": "标准"}),
                "🌡️ 温度": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 2.0, "step": 0.01}),
                "📝 最大输出令牌": ("INT", {"default": 6144, "min": 512, "max": 65536, "step": 1}),
                "🎲 Top_P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": "randomize", "tooltip": "仅控制ComfyUI缓存，不发送给接口。"}),
                "⌛ 请求超时": ("INT", {"default": 300, "min": 30, "max": 1200, "step": 10}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🪂 最终图像提示词", "🗂️ 识别分类", "🧩 使用模板", "📑 参数与优化分析", "📄 LLM完整响应", "ℹ️ 处理信息")
    FUNCTION = "generate_prompt"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "调用dapaoAI LLM，根据GPT Image 2结构化设计模板生成、优化和诊断图像提示词；本节点不出图。"

    @staticmethod
    def _collect_images(kwargs):
        images = []
        for slot in range(1, MAX_IMAGES + 1):
            tensor = kwargs.get(f"🖼️ 参考图{slot}")
            if tensor is None:
                continue
            for batch_index, uri in enumerate(_image_data_uris(tensor), 1):
                if len(images) >= MAX_IMAGES:
                    return images
                label = f"参考图{slot}" + (f"-{batch_index}" if tensor.shape[0] > 1 else "")
                images.append((label, uri))
        return images

    @staticmethod
    def _build_user_content(kwargs, images):
        selected_category = CATEGORY_LABELS.get(kwargs.get("🗂️ 设计分类", "自动识别"), "auto")
        selected_template_label = kwargs.get("🧩 具体模板", "自动选择模板")
        selected_template_path = TEMPLATE_PATH_BY_LABEL.get(selected_template_label, selected_template_label)
        if selected_template_label != "自动选择模板":
            if selected_template_path not in TEMPLATE_PATHS:
                raise ValueError(f"未知具体模板：{selected_template_label}")
            template_category = selected_template_path.split("/", 1)[0]
            if selected_category != "auto" and selected_category != template_category:
                raise ValueError(f"设计分类 {selected_category} 与具体模板 {selected_template_label} 不一致。")
        output_chinese = _as_bool(kwargs.get("🌐 输出中文提示词", False))
        output_language = "Simplified Chinese" if output_chinese else "English"
        text = (
            f"Requested task: {kwargs.get('🎛️ 任务模式', '自动识别')}\n"
            f"Selected category: {selected_category}\nSelected template ID: {selected_template_path}\n"
            f"Selected template label: {selected_template_label}\n"
            f"Target image model: {kwargs.get('🎯 目标图像模型', 'GPT Image 2 / OpenAI兼容')}\n"
            f"Output language: {output_language}\nAspect ratio: {kwargs.get('📐 图片比例', '自动')}\n"
            f"Prompt format: {kwargs.get('📚 提示词格式', '自动')}\nDetail density: {kwargs.get('🧠 细节密度', '标准')}\n"
            f"Reference images: {len(images)}/{MAX_IMAGES}\n"
            f"Has edit mask: {str(kwargs.get('🎭 蒙版') is not None).lower()}\n\n"
            f"USER REQUEST:\n{(kwargs.get('📝 原始图像需求') or '').strip()}\n\n"
            f"EXISTING PROMPT TO OPTIMIZE:\n{(kwargs.get('📝 需要优化的现有提示词') or '').strip()}\n\n"
            f"EXACT TEXT AND DATA — preserve verbatim, do not invent missing facts:\n{(kwargs.get('🔤 画面准确文字与数据') or '').strip()}\n\n"
            f"MUST PRESERVE:\n{(kwargs.get('🔒 必须保留') or '').strip()}\n\n"
            f"MUST AVOID:\n{(kwargs.get('🚫 禁止出现') or '').strip()}\n\n"
            f"REFERENCE ROLE NOTES:\n{(kwargs.get('📎 参考素材用途说明') or '').strip()}\n\n"
            + (
                "MANDATORY OUTPUT LANGUAGE: Simplified Chinese. final_prompt and all explanatory values "
                "must use Simplified Chinese; do not draft them in English."
                if output_chinese
                else "MANDATORY OUTPUT LANGUAGE: English, except exact user-provided on-image text."
            )
        )
        if not images and kwargs.get("🎭 蒙版") is None:
            return text
        content = [{"type": "text", "text": text}]
        for index, (label, uri) in enumerate(images, 1):
            content.extend([
                {"type": "text", "text": f"REFERENCE_{index - 1} ({label}) follows. Describe only visible evidence and follow the user's role notes."},
                {"type": "image_url", "image_url": {"url": uri}},
            ])
        mask = kwargs.get("🎭 蒙版")
        if mask is not None:
            content.extend([
                {"type": "text", "text": "EDIT_MASK follows. White pixels are editable; black pixels must be preserved."},
                {"type": "image_url", "image_url": {"url": _mask_data_uri(mask)}},
            ])
        return content

    async def generate_prompt(self, **kwargs):
        return await asyncio.to_thread(self._generate_prompt_sync, **kwargs)

    def _generate_prompt_sync(self, **kwargs):
        result = {}
        try:
            api_key = (kwargs.get("🔑 API密钥") or "").strip()
            model = kwargs.get("🤖 LLM模型", "gemini-3.7-flash")
            request = (kwargs.get("📝 原始图像需求") or "").strip()
            existing_prompt = (kwargs.get("📝 需要优化的现有提示词") or "").strip()
            task = kwargs.get("🎛️ 任务模式", "自动识别")
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model not in MODEL_OPTIONS:
                raise ValueError(f"不支持的LLM模型：{model}")
            if task not in TASK_OPTIONS:
                raise ValueError(f"不支持的任务模式：{task}")
            if not request and not existing_prompt:
                raise ValueError("原始图像需求和现有提示词不能同时为空。")
            if task in {"优化现有提示词", "提示词诊断与重写"} and not existing_prompt:
                raise ValueError(f"{task}需要填写需要优化的现有提示词。")
            if task == "蒙版局部编辑提示词" and kwargs.get("🎭 蒙版") is None:
                raise ValueError("蒙版局部编辑提示词必须接入MASK蒙版。")

            images = self._collect_images(kwargs)
            output_chinese = _as_bool(kwargs.get("🌐 输出中文提示词", False))
            language_policy = LANGUAGE_POLICY_CHINESE if output_chinese else LANGUAGE_POLICY_ENGLISH
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + language_policy},
                {"role": "user", "content": self._build_user_content(kwargs, images)},
            ]
            payload = {
                "model": model,
                "messages": messages,
                "temperature": float(kwargs.get("🌡️ 温度", 0.35)),
                "max_tokens": int(kwargs.get("📝 最大输出令牌", 6144)),
                "top_p": float(kwargs.get("🎲 Top_P", 1.0)),
                "stream": False,
            }
            started = time.time()
            result = ImagePromptLLMClient(api_key, int(kwargs.get("⌛ 请求超时", 300))).chat(payload)
            raw_text = _extract_text(result)
            if not raw_text:
                raise RuntimeError("LLM返回内容为空。")
            parsed = _parse_json(raw_text)
            final_prompt = str(parsed.get("final_prompt") or raw_text).strip()
            language_corrected = False
            correction_result = {}
            if output_chinese and not _has_sufficient_chinese(final_prompt):
                correction_payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "你是严格的简体中文本地化校对器。输入是一个图像提示词JSON结果。"
                                "保持原JSON结构、事实、布局、参考图编号、专有名词、公式和逐字画面文案不变，"
                                "将final_prompt及所有说明性字段完整翻译为简体中文。只返回JSON对象，不要解释。"
                            ),
                        },
                        {"role": "user", "content": raw_text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": int(kwargs.get("📝 最大输出令牌", 6144)),
                    "top_p": 1.0,
                    "stream": False,
                }
                correction_result = ImagePromptLLMClient(
                    api_key, int(kwargs.get("⌛ 请求超时", 300))
                ).chat(correction_payload)
                corrected_text = _extract_text(correction_result)
                corrected_parsed = _parse_json(corrected_text)
                corrected_prompt = str(corrected_parsed.get("final_prompt") or "").strip()
                if not corrected_prompt or not _has_sufficient_chinese(corrected_prompt):
                    raise RuntimeError("已开启中文提示词，但所选LLM连续两次没有返回有效简体中文提示词。")
                parsed = corrected_parsed
                final_prompt = corrected_prompt
                language_corrected = True
            category = str(parsed.get("category") or CATEGORY_LABELS.get(kwargs.get("🗂️ 设计分类", "自动识别"), "auto")).strip()
            raw_template = str(parsed.get("template") or kwargs.get("🧩 具体模板", "自动选择模板")).strip()
            template = TEMPLATE_LABEL_BY_PATH.get(raw_template, raw_template)
            analysis_data = {
                "task": parsed.get("task", task),
                "prompt_format": parsed.get("prompt_format", kwargs.get("📚 提示词格式", "自动")),
                "parameter_analysis": parsed.get("parameter_analysis", ""),
                "missing_critical_information": parsed.get("missing_critical_information", []),
                "recommended_generation_parameters": parsed.get("recommended_generation_parameters", {}),
                "production_notes": parsed.get("production_notes", ""),
            }
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            info = (
                "✅ 全能image提示词生成完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 LLM模型：{model}\n"
                f"🎛️ 任务：{task}\n"
                f"🗂️ 分类：{category}\n"
                f"🧩 模板：{template}\n"
                f"🎯 目标模型：{kwargs.get('🎯 目标图像模型', 'GPT Image 2 / OpenAI兼容')}\n"
                f"🌐 提示词语言：{'简体中文' if output_chinese else '英文'}"
                f"{'（已自动纠正模型语言）' if language_corrected else ''}\n"
                f"🖼️ 参考图：{len(images)}张\n"
                f"🎭 蒙版：{'已接入' if kwargs.get('🎭 蒙版') is not None else '未接入'}\n"
                f"📥 输入令牌：{usage.get('prompt_tokens', usage.get('input_tokens', '未知'))}\n"
                f"📤 输出令牌：{usage.get('completion_tokens', usage.get('output_tokens', '未知'))}\n"
                f"⏱️ 耗时：{time.time() - started:.2f}秒\n"
                "ℹ️ 本节点只生成提示词，不会调用图像生成接口。"
            )
            return (
                final_prompt,
                category,
                template,
                json.dumps(analysis_data, ensure_ascii=False, indent=2),
                json.dumps(
                    _sanitized({"initial": result, "language_correction": correction_result}),
                    ensure_ascii=False,
                    indent=2,
                ),
                info,
            )
        except Exception as error:
            message = f"❌ 全能image提示词生成失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            response_text = json.dumps({"error": str(error), "response": _sanitized(result)}, ensure_ascii=False, indent=2)
            if kwargs.get("🚫 出错时跳过", False):
                return message, "未知", "未知", message, response_text, message
            raise RuntimeError(message) from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoAllroundImagePromptNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}

__all__ = [
    "DapaoAllroundImagePromptNode",
    "MODEL_OPTIONS",
    "TASK_OPTIONS",
    "CATEGORY_OPTIONS",
    "TEMPLATE_OPTIONS",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
