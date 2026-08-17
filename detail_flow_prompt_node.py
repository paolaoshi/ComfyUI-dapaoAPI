"""DetailFlow-inspired ecommerce detail-page prompt director.

This node is prompt-only: it never calls an image-generation endpoint.  It
turns product/reference images and confirmed product facts into a validated
page blueprint, a visual-master prompt, and one prompt per page slice.  The
implementation is self-contained so the source project is not required at
runtime.
"""

import asyncio
import base64
import io
import json
import re
import sys
import time
import traceback

import numpy as np
import requests
from PIL import Image

from .network_error_utils import friendly_443_status, friendly_network_error


API_BASE_URL = "https://api.dapaoai.com"
CHAT_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
NODE_NAME = "DapaoDetailFlowPromptNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮API常用工具🍬"
DISPLAY_NAME = "🛍️电商详情页提示词@炮老师的小课堂"

MODEL_OPTIONS = [
    "gpt-5.5", "gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol",
    "claude-fable-5", "claude-opus-4-8", "claude-opus-5", "claude-sonnet-5",
    "gemini-3.5-flash", "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
]
PAGE_TYPE_OPTIONS = ["实体商品详情页", "AI工具/模型产品页", "SaaS功能页", "开发者产品页", "自定义长页"]
PRODUCT_CATEGORY_OPTIONS = [
    "自动识别", "食品饮料", "美妆个护", "3C数码", "家居家电", "服饰箱包", "母婴用品",
    "宠物用品", "汽车用品", "运动户外", "珠宝饰品", "AI软件/模型", "SaaS服务", "开发者工具", "其他",
]
PLATFORM_OPTIONS = ["自动适配", "淘宝/天猫", "京东", "抖音小店", "拼多多", "小红书", "独立站", "通用长图"]
MAX_SCREEN_COUNT = 8
SCREEN_COUNT_OPTIONS = [str(index) for index in range(1, MAX_SCREEN_COUNT + 1)]
CONTINUITY_OPTIONS = ["严格连续详情页（推荐）", "统一视觉、分屏独立构图"]
TEXT_STRATEGY_OPTIONS = [
    "自动规划不同屏文字（推荐）", "精简中文标题与标签", "完整中文文案", "只使用用户提供的原文",
    "只预留文字区域", "完全不显示画面文字", "自定义（请填写下方补充）",
]
MASTER_OPTIONS = ["自动生成可选母版提示词（推荐）", "1:3长幅母版提示词", "1:4长幅母版提示词", "仅生成文字视觉规范"]
TARGET_MODEL_OPTIONS = [
    "通用图像模型（推荐）", "GPT Image 2（提示词适配）", "Banana 2（提示词适配）",
    "Banana Pro（提示词适配）", "FLUX/Stable Diffusion", "其他图像模型",
]
OUTPUT_LANGUAGE_OPTIONS = ["中文提示词", "英文提示词（画面文字仍保留中文）"]
DENSITY_OPTIONS = ["智能变化（推荐）", "整体简洁", "均衡信息密度", "专业高密度"]
CUSTOM_OPTION = "自定义（请填写下方补充）"
BUYER_OPTIONS = [
    "自动根据产品品类推荐（推荐）", "大众消费者", "年轻女性", "年轻男性", "职场/办公人群", "学生群体", "宝妈/家庭用户",
    "情侣/送礼人群", "中高端品质用户", "户外/运动人群", "数码科技爱好者", "专业从业者", CUSTOM_OPTION,
]
SELLING_POINT_OPTIONS = [
    "自动匹配品类核心卖点（推荐）", "自动生成互补卖点", "品质材质与做工", "核心功能与性能", "省时省力/效率提升", "口感与使用体验", "外观设计与审美",
    "便携收纳与易用", "安全可靠与耐用", "性价比与套装价值", "情绪价值与生活方式", "科技创新与专业能力",
    "自定义（请填写下方补充）", "不设置此卖点",
]
EVIDENCE_OPTIONS = [
    "自动选择最可信证据（推荐）", "规格尺寸与容量", "材质结构与工艺", "性能参数与测试", "成分配方与来源", "认证检测与品质保障",
    "续航电量与兼容性", "使用步骤与操作细节", "用户评价/口碑（仅限已提供）", "型号对比与套装清单", "暂无具体证据", CUSTOM_OPTION,
]
SCENE_OPTIONS = [
    "自动匹配购买人群（推荐）", "家庭日常", "办公/学习", "通勤出行", "旅行度假", "户外运动", "亲子陪伴", "情侣/朋友分享",
    "节日送礼", "直播/电商展示", "专业工作场景", "前后对比演示", CUSTOM_OPTION,
]
CTA_OPTIONS = [
    "自动匹配平台（推荐）", "立即购买", "加入购物车", "领券下单", "查看规格与套装", "咨询客服", "扫码了解详情", "预约体验",
    "申请试用", "关注店铺/收藏", "暂不设置CTA", CUSTOM_OPTION,
]
FACT_SAFETY_OPTIONS = [
    "智能推断并标记（推荐）", "严格只用已确认事实", "允许轻度营销修辞但不编造参数",
    "自定义（请填写下方补充）",
]
STYLE_OPTIONS = [
    "自动根据产品与参考图（推荐）", "高级极简商业摄影", "清新自然生活方式", "温暖居家生活感", "科技未来与UI信息图", "专业实验室/工程感",
    "潮流年轻电商视觉", "复古国风/东方美学", "3D卡通与品牌角色", "棚拍白底产品展示", "杂志编辑与高级时尚",
    CUSTOM_OPTION,
]

MAX_PRODUCT_IMAGES = 6
MAX_STYLE_IMAGES = 3
MAX_LLM_IMAGES = 9
BLUEPRINT_FIELDS = {
    "slice_id", "buyer_question", "claim_seed", "screen_job", "evidence_type", "content_density",
    "copy_structure_pattern", "primary_module", "secondary_modules", "text_exact", "composition_shift",
    "top_edge_anchor", "bottom_edge_anchor", "visual_composition", "risk_unknowns",
}


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(str(message).encode(encoding, errors="replace").decode(encoding, errors="replace"))


def _log_error(message):
    _safe_print(f"[dapaoAPI-电商详情页提示词] 错误：{message}")


def _image_data_uris(image_tensor, max_side=1536):
    result = []
    for item in image_tensor:
        array = np.clip(item.detach().cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        image = Image.fromarray(array).convert("RGB")
        if max(image.size) > max_side:
            scale = max_side / max(image.size)
            image = image.resize((max(1, int(image.width * scale)), max(1, int(image.height * scale))), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90)
        result.append("data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode("ascii"))
    return result


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


def _selected_value(kwargs, select_name, custom_name):
    selected = str(kwargs.get(select_name) or "").strip()
    custom = str(kwargs.get(custom_name) or "").strip()
    if selected.startswith("自定义"):
        return custom or "（用户选择自定义，但未填写补充说明）"
    return selected


def _compact_text(value):
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _merged_brief(kwargs):
    internal = str(kwargs.get("📝 原始电商需求") or "").strip()
    external = str(kwargs.get("🔗 外部原始需求") or "").strip()
    if external and internal:
        return f"上游传入需求：\n{external}\n\n节点内补充需求：\n{internal}"
    return external or internal


def _complete_screen_prompt(screen_prompt, visual_master, screen_index=None, screen_count=None):
    """Build a self-contained downstream prompt without another LLM request."""
    shared = []
    master_spec = _compact_text(visual_master.get("visual_master_spec"))
    identity = _compact_text(visual_master.get("product_identity_lock"))
    style = _compact_text(visual_master.get("visual_style_dna"))
    continuity = _compact_text(visual_master.get("continuity_rules"))
    ratio = _compact_text(visual_master.get("recommended_slice_ratio"))
    if master_spec:
        shared.append(f"视觉系统：{master_spec}")
    if identity:
        shared.append(f"产品身份锁：{identity}")
    if style:
        shared.append(f"风格锁：{style}")
    if continuity:
        shared.append(f"连续性规则：{continuity}")
    if ratio:
        shared.append(f"建议画幅：{ratio}（最终尺寸仍以所连接图像节点的参数为准）")
    boundary = ""
    if screen_index == 1 and screen_count == 1:
        boundary = "本屏是完整详情页的唯一画面：同时完成产品开场、卖点证明、价值总结和CTA自然收尾；上下边缘均不得暗示还有其他分屏。"
    elif screen_index == 1:
        boundary = "本屏是整套详情页的正式开场：顶部自然起始，底部为第02屏留下明确但不悬空的视觉衔接。"
    elif screen_index == screen_count:
        boundary = "本屏是整套详情页的最终收尾：承接上一屏，完成价值总结、信任收束和CTA；底部自然闭合，不得暗示还有下一屏。"
    elif screen_index and screen_count:
        boundary = "本屏位于完整详情页中段：顶部承接上一屏，底部为下一屏提供成对视觉锚点，不得形成独立海报式断层。"
    body = str(screen_prompt or "").strip()
    if boundary:
        body = "【页面位置与闭环要求】\n" + boundary + "\n\n" + body
    if not shared:
        return body
    return "【全局一致性锁】\n" + "\n".join(shared) + "\n\n【当前分屏生成要求】\n" + body


def _screen_number(value):
    """Accept 1, 01, 第1屏, screen_01 and similar LLM numbering variants."""
    text = str(value or "").strip()
    match = re.search(r"(?<!\d)(\d{1,2})(?!\d)", text)
    return int(match.group(1)) if match else None


def _prompt_rows(prompts):
    """Serialize one complete prompt per physical line for CR Prompt List."""
    rows = []
    for prompt in prompts:
        row = re.sub(r"\s+", " ", str(prompt or "")).strip()
        if row:
            rows.append(row)
    return "\n".join(rows)


class DetailFlowLLMClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/DetailFlowPrompt",
        }
        try:
            response = requests.post(CHAT_ENDPOINT, headers=headers, json=payload, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RuntimeError(f"{friendly_network_error(error, '提交LLM请求')} LLM请求不会自动重试，以免重复扣费。") from error
        if response.status_code >= 400:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status())
            labels = {400: "请求参数错误", 401: "认证失败", 402: "余额不足", 403: "没有模型权限", 404: "映射模型不存在", 429: "请求过频"}
            try:
                detail = response.json()
            except Exception:
                detail = response.text[:1000]
            raise RuntimeError(f"{labels.get(response.status_code, '中转站请求失败')} {response.status_code}：{detail}")
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站返回内容不是JSON：{response.text[:500]}") from error


SYSTEM_PROMPT = r"""
你是电商详情页内容导演、产品视觉策划和图像提示词工程师。你只生成提示词与结构化规划，不调用任何图像生成接口，也不能声称已经出图。

你必须把一个产品组织成一套有购买逻辑的连续详情页，而不是多张互不相关的海报。先区分：图片可见事实、用户确认事实、合理但未确认的推断、不能出现的未知信息。严禁编造精确参数、认证、奖项、医疗/功效结论、折扣、销量、合作方和品牌事实。

严格执行以下规则：
1. 首屏先确定2至4个具体卖点种子；后续每个分屏必须展开、证明、可视化、比较或情境化其中至少一个种子，不得突然加入无铺垫的新卖点。
2. 每个分屏只承担一个不同的购买问题和页面任务。相邻分屏不能使用相同的文案语法、同样的主视觉和同样的标签堆叠。
3. 首屏可以使用强标题；后续优先使用问答、细节标注、三点拆解、场景字幕、步骤、信任清单、对比条目或安静收尾，不要让所有分屏重复“标题+副标题+产品主视觉”。
4. 每个分屏都必须写明primary_module、secondary_modules、content_density、composition_shift、top_edge_anchor和bottom_edge_anchor。上下边缘只承担视觉衔接，不放核心标题和关键证明。
5. 视觉母版是连续空间和风格锚点，不是最终分屏，也不是裁切源。分屏提示词必须继承产品身份、色彩、灯光、材质、字体、间距、连续性元素和边缘衔接，同时改变信息密度和构图。
6. 产品参考图是身份事实源；风格参考图只提取抽象风格DNA，不复制原品牌、人物、文字或产品。
7. 画面文字必须严格服从用户提供的准确文案。图像模型容易产生错字时，按用户的文字策略减少文字数量或预留排版区域，并在风险中说明。
8. 即使资料不足也必须一次完成用户指定数量的提示词。“智能推断并标记”可以进行品类级合理推断，但必须把推断列入inferred_points和risk_notes；“严格只用已确认事实”不得补造参数、认证或具体功效。
9. 在返回前自行检查事实安全、卖点连续性、相邻屏文案结构差异和产品身份锁，并把发现的风险写入audit_report；本节点不接收或审核已经生成的成图。
10. 目标图像模型只用于调整提示词写法，不得声称已经设置下游图像节点的真实分辨率或比例。通用模式不绑定具体比例；其他模式仅给出保守建议，最终尺寸以用户连接的图像节点参数为准。
11. 用户选择“自动”选项时，必须根据产品品类、产品图、平台和目标人群生成具体结论；最终提示词中不能出现“自动匹配”“自动推荐”等占位词。多个自动卖点必须彼此互补，不能重复。

工作方式只有一种：一次完成产品诊断、卖点种子、用户指定数量的详情页蓝图、文字视觉母版和全部分屏提示词。必须严格服从SCREEN COUNT，不得多生成或少生成。屏数少于8时，合并叙事阶段并保留“开场—证明—转化”的完整购买逻辑。不要等待确认，也不要要求用户回接中间结果。

用户选择的屏数就是一套完整详情页的全部屏数，不是8屏模板的前N屏截断：
- 第01屏必须承担产品身份、核心购买理由和整页开场；top_edge_anchor应明确为自然起始，不得假设前面还有页面。
- 最后一屏必须完成价值总结、信任收束和CTA；bottom_edge_anchor应明确为自然收尾，不得留下“下一屏继续”、未展开卖点或悬空视觉线索。
- 中间屏负责展开卖点、可视化证据和使用场景；相邻屏的底部与顶部视觉锚点必须成对衔接。
- 屏数较少时合并任务，屏数较多时拆分证据，但无论选择1至8中的哪个数量，都必须形成从开场到收尾闭环的完整详情页。

页面类型的默认叙事：
- 实体商品：产品身份与核心购买理由→痛点/欲望→核心利益→结构材质工艺→使用场景→证据与信任→对比/价值构成→CTA收尾。
- AI工具/模型：产品身份→输出/工作流证据→能力地图→具体用例→控制参数与限制→API/集成→版本或替代方案对比→试用/文档CTA。
- SaaS功能：功能承诺→使用前后流程→关键界面/自动化→团队角色权限→集成与数据流→指标审计可靠性→采用CTA；分屏较多时拆分证据而不是编造新功能。
- 开发者产品：可构建内容→请求响应示例→平台/SDK/格式→认证/限流/安全→真实集成示例→文档与沙箱CTA；分屏较多时拆分技术证据。
- 自定义长页：服从用户需求，但仍必须保持卖点种子、差异化结构和事实安全。

必须只返回一个紧凑JSON对象，不要Markdown围栏，不要解释内部规则。JSON字段固定为：
product_analysis、claim_seeds、blueprint、visual_master、screen_prompts、audit_report、exact_copy_master、production_notes。

blueprint项数必须严格等于SCREEN COUNT。每项只需包含：slice_id、buyer_question、claim_seed、screen_job、evidence_type、content_density、copy_structure_pattern、primary_module、secondary_modules、text_exact、composition_shift、top_edge_anchor、bottom_edge_anchor、visual_composition、risk_unknowns。字段内容保持紧凑，避免重复描述。
visual_master必须包含：visual_master_spec、master_reference_prompt、visual_style_dna、product_identity_lock、continuity_rules、recommended_master_ratio、recommended_slice_ratio。
screen_prompts必须是对象，键从01开始连续编号，数量严格等于SCREEN COUNT。共享的产品身份、风格和连续性规则写入visual_master，不要在各分屏提示词中机械重复；每个分屏提示词重点写当前屏任务、准确文字、画面构图、上下边缘衔接和禁止事项。每屏控制在信息完整但不重复的长度内，中文通常300至600字。节点会自动把visual_master共享规则合并到每一屏，形成可直接交给图像模型的完整提示词。
audit_report必须包含observed_problems、severity、unsupported_claims、continuity_findings和next_action。
"""

LANGUAGE_POLICY = {
    "中文提示词": "所有说明和分屏提示词使用简体中文；用户要求逐字保留的品牌名、产品名和画面文案原样保留。",
    "英文提示词（画面文字仍保留中文）": "说明文字和图像提示词使用专业英文；用户要求逐字保留的中文品牌名、产品名和画面文案必须原样保留。",
}


class DapaoDetailFlowPromptNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "🔗 外部原始需求": ("STRING", {"forceInput": True, "default": "", "tooltip": "可连接任意STRING文本节点；连接后会与节点内需求合并。"}),
            "🛍️ 产品名称": ("STRING", {"default": "", "multiline": False, "placeholder": "可选：品牌、产品名、型号"}),
            "📝 真实参数与产品事实": ("STRING", {"default": "", "multiline": True, "placeholder": "可选：尺寸、材质、容量、成分、型号、续航、认证、套装清单、售后等真实资料"}),
            "👥 目标购买人群": (BUYER_OPTIONS, {"default": "自动根据产品品类推荐（推荐）"}),
            "📝 自定义目标人群": ("STRING", {"default": "", "multiline": True}),
            "💡 主卖点方向": (SELLING_POINT_OPTIONS, {"default": "自动匹配品类核心卖点（推荐）"}),
            "💡 第二卖点方向": (SELLING_POINT_OPTIONS, {"default": "自动生成互补卖点"}),
            "💡 第三卖点方向": (SELLING_POINT_OPTIONS, {"default": "不设置此卖点"}),
            "📝 自定义主卖点": ("STRING", {"default": "", "multiline": True}),
            "📝 自定义第二卖点": ("STRING", {"default": "", "multiline": True}),
            "📝 自定义第三卖点": ("STRING", {"default": "", "multiline": True}),
            "📏 主要证据类型": (EVIDENCE_OPTIONS, {"default": "自动选择最可信证据（推荐）"}),
            "📝 自定义证据说明": ("STRING", {"default": "", "multiline": True}),
            "🎬 主要使用场景": (SCENE_OPTIONS, {"default": "自动匹配购买人群（推荐）"}),
            "📝 自定义使用场景": ("STRING", {"default": "", "multiline": True}),
            "🛒 CTA类型": (CTA_OPTIONS, {"default": "自动匹配平台（推荐）"}),
            "📝 自定义CTA": ("STRING", {"default": "", "multiline": True}),
            "📝 自定义画面文字方案": ("STRING", {"default": "", "multiline": True}),
            "🔤 必须逐字保留的画面文字": ("STRING", {"default": "", "multiline": True, "placeholder": "可选：品牌名、价格、型号、宣传语、参数"}),
            "🚫 事实处理方式": (FACT_SAFETY_OPTIONS, {"default": "智能推断并标记（推荐）"}),
            "📝 自定义事实限制": ("STRING", {"default": "", "multiline": True}),
            "🎨 视觉风格方向": (STYLE_OPTIONS, {"default": "自动根据产品与参考图（推荐）"}),
            "📝 自定义视觉风格": ("STRING", {"default": "", "multiline": True}),
            "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
        }
        for index in range(1, MAX_PRODUCT_IMAGES + 1):
            optional[f"📦 产品图{index}"] = ("IMAGE", {"tooltip": f"产品身份事实参考图{index}。"})
        for index in range(1, MAX_STYLE_IMAGES + 1):
            optional[f"🎨 风格参考图{index}"] = ("IMAGE", {"tooltip": f"只提取抽象风格DNA的参考图{index}。"})
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 dapaoAI API 密钥", "tooltip": "密钥只用于请求 https://api.dapaoai.com。"}),
                "🤖 LLM模型": (MODEL_OPTIONS, {"default": "gemini-3.7-flash"}),
                "🧭 页面类型": (PAGE_TYPE_OPTIONS, {"default": "实体商品详情页"}),
                "🗂️ 产品品类": (PRODUCT_CATEGORY_OPTIONS, {"default": "自动识别"}),
                "🛒 适配平台": (PLATFORM_OPTIONS, {"default": "自动适配"}),
                "🔢 分屏数量": (SCREEN_COUNT_OPTIONS, {"default": "8", "tooltip": "选择1至8屏；无论数量多少，都会从首屏开场到末屏CTA完整收尾。"}),
                "🔗 页面连续方式": (CONTINUITY_OPTIONS, {"default": "严格连续详情页（推荐）"}),
                "✍️ 画面文字方案": (TEXT_STRATEGY_OPTIONS, {"default": "自动规划不同屏文字（推荐）"}),
                "🧱 视觉母版方式": (MASTER_OPTIONS, {"default": "自动生成可选母版提示词（推荐）", "tooltip": "母版输出是可选增强项；不连接它也不影响所选分屏提示词。"}),
                "🎯 提示词适配目标": (TARGET_MODEL_OPTIONS, {"default": "通用图像模型（推荐）", "tooltip": "只调整提示词写法，不会自动修改下游图像节点的分辨率。"}),
                "📚 内容密度": (DENSITY_OPTIONS, {"default": "智能变化（推荐）"}),
                "🌐 提示词语言": (OUTPUT_LANGUAGE_OPTIONS, {"default": "中文提示词"}),
                "📝 原始电商需求": ("STRING", {"multiline": True, "default": "为这个产品制作一套连续的电商详情页，突出真实卖点和购买理由。", "placeholder": "描述产品、页面目标、希望强调的内容……"}),
                "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": "randomize", "tooltip": "只用于ComfyUI缓存控制，不发送给LLM；测试生图时可让上游提示词重新执行。"}),
                "⚙️ 显示高级设置": ("BOOLEAN", {"default": False}),
                "🌡️ 温度": ("FLOAT", {"default": 0.3, "min": 0.0, "max": 2.0, "step": 0.01}),
                "📝 最大输出令牌": ("INT", {"default": 12000, "min": 2048, "max": 65536, "step": 1}),
                "🎲 Top_P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🔄 每次重新生成提示词": ("BOOLEAN", {"default": False, "tooltip": "关闭时复用ComfyUI缓存；开启后每次Queue都会重新请求LLM。"}),
                "⌛ 请求超时": ("INT", {"default": 600, "min": 30, "max": 1800, "step": 10}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "🧭 可选视觉母版提示词", "🖼️ 第01屏提示词", "🖼️ 第02屏提示词", "🖼️ 第03屏提示词", "🖼️ 第04屏提示词",
        "🖼️ 第05屏提示词", "🖼️ 第06屏提示词", "🖼️ 第07屏提示词", "🖼️ 第08屏提示词", "📋 详情页完整蓝图JSON",
        "📝 全部准确画面文案", "⚠️ 事实与连续性提醒", "📄 LLM完整响应", "ℹ️ 处理信息", "📚 所选分屏多行提示词", "🧩 所选分屏批量提示词",
    )
    OUTPUT_IS_LIST = (False,) * 15 + (True,)
    FUNCTION = "generate_prompt"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "一次生成1至8屏完整连续电商详情页提示词；提供独立分屏、CR多行文本和ComfyUI批量列表三种连接方式。"

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan") if kwargs.get("🔄 每次重新生成提示词", False) else False

    @staticmethod
    def _collect_images(kwargs, prefix, limit, max_side):
        images = []
        for slot in range(1, limit + 1):
            tensor = kwargs.get(f"{prefix}{slot}")
            if tensor is None:
                continue
            for batch_index, uri in enumerate(_image_data_uris(tensor, max_side=max_side), 1):
                if len(images) >= limit:
                    return images
                label = f"{prefix}{slot}" + (f"-批次{batch_index}" if getattr(tensor, "shape", [1])[0] > 1 else "")
                images.append((label, uri))
        return images

    @staticmethod
    def _build_user_content(kwargs, product_images, style_images, screen_count):
        brief = _merged_brief(kwargs)
        buyer = _selected_value(kwargs, "👥 目标购买人群", "📝 自定义目标人群")
        selling_points = [
            _selected_value(kwargs, "💡 主卖点方向", "📝 自定义主卖点"),
            _selected_value(kwargs, "💡 第二卖点方向", "📝 自定义第二卖点"),
            _selected_value(kwargs, "💡 第三卖点方向", "📝 自定义第三卖点"),
        ]
        selling_points = [item for item in selling_points if item and item != "不设置此卖点"]
        evidence = _selected_value(kwargs, "📏 主要证据类型", "📝 自定义证据说明")
        scene = _selected_value(kwargs, "🎬 主要使用场景", "📝 自定义使用场景")
        cta = _selected_value(kwargs, "🛒 CTA类型", "📝 自定义CTA")
        text_plan = _selected_value(kwargs, "✍️ 画面文字方案", "📝 自定义画面文字方案")
        fact_safety = _selected_value(kwargs, "🚫 事实处理方式", "📝 自定义事实限制")
        visual_style = _selected_value(kwargs, "🎨 视觉风格方向", "📝 自定义视觉风格")
        text = f"""
WORK MODE: ONE-SHOT DIRECT PROMPT PACKAGE
PAGE TYPE: {kwargs.get('🧭 页面类型', '实体商品详情页')}
PRODUCT CATEGORY: {kwargs.get('🗂️ 产品品类', '自动识别')}
PLATFORM: {kwargs.get('🛒 适配平台', '自动适配')}
SCREEN COUNT: {screen_count} (this is the complete page from opening through final CTA, not a truncated prefix)
CONTINUITY: {kwargs.get('🔗 页面连续方式', '严格连续详情页（推荐）')}
TEXT AND COPY PLAN: {text_plan}
MASTER STRATEGY: {kwargs.get('🧱 视觉母版方式', '自动生成可选母版提示词（推荐）')}
PROMPT ADAPTATION TARGET: {kwargs.get('🎯 提示词适配目标', '通用图像模型（推荐）')}
CONTENT DENSITY: {kwargs.get('📚 内容密度', '智能变化（推荐）')}
OUTPUT LANGUAGE: {kwargs.get('🌐 提示词语言', '中文提示词')}

PRODUCT NAME:
{(kwargs.get('🛍️ 产品名称') or '').strip()}
CONFIRMED PRODUCT FACTS AND PARAMETERS:
{(kwargs.get('📝 真实参数与产品事实') or '').strip()}
TARGET BUYERS:
{buyer}
SELLING POINT DIRECTIONS:
{json.dumps(selling_points, ensure_ascii=False)}
PRIMARY EVIDENCE TYPE:
{evidence}
PRIMARY USAGE SCENE:
{scene}
CTA / PURCHASE ACTION:
{cta}
EXACT ON-IMAGE COPY:
{(kwargs.get('🔤 必须逐字保留的画面文字') or '').strip()}
FACT SAFETY RULE:
{fact_safety}
STYLE DIRECTION:
{visual_style}
USER BRIEF:
{brief}

REFERENCE COUNTS: product={len(product_images)}, style={len(style_images)}
"""
        if not product_images and not style_images:
            return text
        content = [{"type": "text", "text": text}]
        for index, (label, uri) in enumerate(product_images, 1):
            content.extend([{"type": "text", "text": f"PRODUCT_REFERENCE_{index} ({label}) follows. Treat it as product identity evidence."}, {"type": "image_url", "image_url": {"url": uri}}])
        for index, (label, uri) in enumerate(style_images, 1):
            content.extend([{"type": "text", "text": f"STYLE_REFERENCE_{index} ({label}) follows. Extract abstract style DNA only."}, {"type": "image_url", "image_url": {"url": uri}}])
        return content

    @staticmethod
    def _normalize_blueprint(blueprint, screen_count):
        """Normalize common LLM screen-id spellings without rejecting valid content."""
        if not isinstance(blueprint, list):
            return blueprint
        indexed = {}
        for item in blueprint:
            if not isinstance(item, dict):
                continue
            number = _screen_number(item.get("slice_id"))
            if number is not None and 1 <= number <= screen_count and number not in indexed:
                indexed[number] = item
        if len(indexed) == screen_count:
            ordered = [indexed[index] for index in range(1, screen_count + 1)]
        else:
            ordered = [item for item in blueprint if isinstance(item, dict)][:screen_count]
        for index, item in enumerate(ordered, 1):
            item["slice_id"] = f"{index:02d}"
        return ordered

    @staticmethod
    def _normalize_screen_prompts(prompts, screen_count):
        if not isinstance(prompts, dict):
            return prompts
        indexed = {}
        for key, value in prompts.items():
            number = _screen_number(key)
            if number is not None and 1 <= number <= screen_count and number not in indexed:
                indexed[number] = value
        return {f"{index:02d}": indexed.get(index, "") for index in range(1, screen_count + 1)}

    @staticmethod
    def _validate_output(parsed, screen_count):
        if not parsed:
            raise ValueError("LLM没有返回可解析的JSON对象。")
        blueprint = parsed.get("blueprint")
        if not isinstance(blueprint, list) or not blueprint:
            raise ValueError("LLM返回缺少blueprint数组，无法保证详情页结构。")
        if isinstance(blueprint, list) and blueprint:
            expected = int(screen_count)
            if len(blueprint) < expected:
                raise ValueError(f"LLM只返回了{len(blueprint)}屏蓝图，期望{expected}屏。")
            for index, item in enumerate(blueprint[:expected], 1):
                if not isinstance(item, dict):
                    raise ValueError(f"第{index}屏蓝图不是对象。")
        prompts = parsed.get("screen_prompts")
        if not isinstance(prompts, dict):
            raise ValueError("LLM返回缺少screen_prompts对象，无法直接连接图像节点。")
        missing = [f"{index:02d}" for index in range(1, int(screen_count) + 1) if not str(prompts.get(f"{index:02d}") or "").strip()]
        if missing:
            raise ValueError("LLM缺少分屏提示词：" + ", ".join(missing))
    @staticmethod
    def _local_structure_audit(blueprint, screen_count, claim_seeds):
        issues = []
        if not blueprint:
            return issues
        if not 2 <= len(claim_seeds or []) <= 4:
            issues.append("首屏卖点种子数量应为2至4个。")
        for index, item in enumerate(blueprint[:screen_count], 1):
            if not isinstance(item, dict):
                continue
            missing = sorted(BLUEPRINT_FIELDS - set(item))
            if missing:
                issues.append(f"第{index:02d}屏缺少规划字段：{', '.join(missing)}。")
            if not item.get("claim_seed"):
                issues.append(f"第{index:02d}屏没有绑定首屏卖点种子。")
            if index > 1:
                previous = blueprint[index - 2] if isinstance(blueprint[index - 2], dict) else {}
                if item.get("buyer_question") and item.get("buyer_question") == previous.get("buyer_question"):
                    issues.append(f"第{index - 1:02d}屏与第{index:02d}屏重复同一购买问题。")
                if item.get("copy_structure_pattern") and item.get("copy_structure_pattern") == previous.get("copy_structure_pattern"):
                    issues.append(f"第{index - 1:02d}屏与第{index:02d}屏文案结构相同。")
                if item.get("composition_shift") and item.get("composition_shift") == previous.get("composition_shift"):
                    issues.append(f"第{index - 1:02d}屏与第{index:02d}屏构图变化策略重复。")
        return issues

    async def generate_prompt(self, **kwargs):
        return await asyncio.to_thread(self._generate_prompt_sync, **kwargs)

    def _generate_prompt_sync(self, **kwargs):
        result = {}
        started = time.time()
        try:
            api_key = (kwargs.get("🔑 API密钥") or "").strip()
            model = kwargs.get("🤖 LLM模型", "gemini-3.7-flash")
            screen_count = int(kwargs.get("🔢 分屏数量", "8"))
            brief = _merged_brief(kwargs)
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model not in MODEL_OPTIONS:
                raise ValueError(f"不支持的LLM模型：{model}")
            if screen_count < 1 or screen_count > MAX_SCREEN_COUNT:
                raise ValueError(f"分屏数量只能选择1至{MAX_SCREEN_COUNT}。")
            if not brief:
                raise ValueError("原始电商需求不能为空。")
            product_images = self._collect_images(kwargs, "📦 产品图", MAX_PRODUCT_IMAGES, 1536)
            style_images = self._collect_images(kwargs, "🎨 风格参考图", MAX_STYLE_IMAGES, 1024)
            total_images = len(product_images) + len(style_images)
            if total_images > MAX_LLM_IMAGES:
                raise ValueError(f"本次LLM最多接收{MAX_LLM_IMAGES}张图像，目前接入{total_images}张。")
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + LANGUAGE_POLICY.get(kwargs.get("🌐 提示词语言", "中文提示词"), LANGUAGE_POLICY["中文提示词"])},
                    {"role": "user", "content": self._build_user_content(kwargs, product_images, style_images, screen_count)},
                ],
                "temperature": float(kwargs.get("🌡️ 温度", 0.3)),
                "max_tokens": int(kwargs.get("📝 最大输出令牌", 12000)),
                "top_p": float(kwargs.get("🎲 Top_P", 1.0)),
                "stream": False,
            }
            result = DetailFlowLLMClient(api_key, int(kwargs.get("⌛ 请求超时", 600))).chat(payload)
            raw_text = _extract_text(result)
            parsed = _parse_json(raw_text)
            if isinstance(parsed, dict):
                parsed["blueprint"] = self._normalize_blueprint(parsed.get("blueprint"), screen_count)
                parsed["screen_prompts"] = self._normalize_screen_prompts(parsed.get("screen_prompts"), screen_count)
            self._validate_output(parsed, screen_count)
            blueprint = parsed.get("blueprint")[:screen_count] if isinstance(parsed.get("blueprint"), list) else []
            prompts = parsed.get("screen_prompts") if isinstance(parsed.get("screen_prompts"), dict) else {}
            master = parsed.get("visual_master") if isinstance(parsed.get("visual_master"), dict) else {}
            selected_prompts = [
                _complete_screen_prompt(prompts.get(f"{index:02d}"), master, index, screen_count)
                for index in range(1, screen_count + 1)
            ]
            page_prompts = selected_prompts + [""] * (MAX_SCREEN_COUNT - screen_count)
            exact_copy = parsed.get("exact_copy_master", "")
            audit = parsed.get("audit_report") if isinstance(parsed.get("audit_report"), dict) else {}
            local_audit = self._local_structure_audit(
                blueprint, screen_count, parsed.get("claim_seeds") if isinstance(parsed.get("claim_seeds"), list) else []
            )
            analysis = {
                "product_analysis": parsed.get("product_analysis", {}),
                "claim_seeds": parsed.get("claim_seeds", []),
                "audit_report": audit,
                "production_notes": parsed.get("production_notes", []),
                "local_structure_audit": local_audit,
            }
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            info = (
                "✅ 电商详情页提示词生成完成\n"
                f"🌐 中转站：{API_BASE_URL}\n🤖 LLM模型：{model}\n🎛️ 模式：一键直出提示词包\n"
                f"🧭 页面类型：{kwargs.get('🧭 页面类型', '实体商品详情页')}\n🔢 分屏：{screen_count}屏完整详情页\n"
                f"📦 产品图：{len(product_images)}张｜🎨 风格图：{len(style_images)}张\n"
                f"🔎 本地结构提醒：{len(local_audit)}项\n"
                f"🌐 输出语言：{kwargs.get('🌐 提示词语言', '中文提示词')}\n"
                f"📥 输入令牌：{usage.get('prompt_tokens', usage.get('input_tokens', '未知'))}\n📤 输出令牌：{usage.get('completion_tokens', usage.get('output_tokens', '未知'))}\n"
                f"⏱️ 耗时：{time.time() - started:.2f}秒\nℹ️ 本节点只生成提示词，不调用图像生成接口。"
            )
            return (
                str(master.get("master_reference_prompt") or master.get("visual_master_spec") or "").strip(),
                *page_prompts,
                json.dumps(blueprint, ensure_ascii=False, indent=2),
                json.dumps(exact_copy, ensure_ascii=False, indent=2) if not isinstance(exact_copy, str) else exact_copy,
                json.dumps(analysis, ensure_ascii=False, indent=2),
                json.dumps(_sanitized(result), ensure_ascii=False, indent=2),
                info,
                _prompt_rows(selected_prompts),
                selected_prompts,
            )
        except Exception as error:
            message = f"❌ 电商详情页提示词生成失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            response = json.dumps({"error": str(error), "response": _sanitized(result)}, ensure_ascii=False, indent=2)
            if kwargs.get("🚫 出错时跳过", False):
                return ("", "", "", "", "", "", "", "", "", "", "", message, response, message, "", [])
            raise RuntimeError(message) from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoDetailFlowPromptNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}

__all__ = ["DapaoDetailFlowPromptNode", "NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
