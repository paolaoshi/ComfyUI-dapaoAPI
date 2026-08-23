"""MiniMax Music 3 structured-caption compiler powered by dapaoAI LLM models.

This node is self-contained: it packages the local Music 3 style library and
uses only the small set of references relevant to the selected music brief.
It produces a generation-ready three-part caption, not audio.
"""

import asyncio
import json
import re
import sys
import time
import traceback
from pathlib import Path

import requests

from .network_error_utils import friendly_443_status, friendly_network_error
from .llm_model_options import LLM_MODEL_OPTIONS


API_BASE_URL = "https://api.dapaoai.com"
CHAT_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
NODE_NAME = "DapaoMusic3CaptionPromptNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮API常用工具🍬"
DISPLAY_NAME = "🎵Music3音乐提示词生成@炮老师的小课堂"
REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ"
RESOURCE_ROOT = Path(__file__).resolve().parent / "resources" / "music3_caption_rewriter"

MODEL_OPTIONS = list(LLM_MODEL_OPTIONS)

GENRE_FAMILIES = [
    "自动识别",
    "东亚现代流行｜C-pop/J-pop与电子、R&B、说唱融合",
    "东亚抒情与国风｜华语/日系抒情、原声或管弦",
    "现代R&B与Neo-Soul",
    "灵魂、蓝调与福音",
    "电影感流行抒情",
    "电影管弦与史诗配乐",
    "电子、合成器与氛围流行",
    "爵士、摇摆与大乐队",
    "传统声乐、音乐剧与舞台",
    "嘻哈、说唱、Trap与Drill",
    "金属与重型摇滚",
    "流行、另类与独立摇滚",
    "当代民谣与原声",
    "根源、传统与世界音乐",
    "通用流行与抒情",
    "舞曲流行、迪斯科与Funk",
    "俱乐部EDM、House与Trance",
    "乡村与Americana",
    "自定义",
]

FAMILY_FILE_BY_OPTION = {
    "东亚现代流行｜C-pop/J-pop与电子、R&B、说唱融合": "east-asian-modern",
    "东亚抒情与国风｜华语/日系抒情、原声或管弦": "east-asian-ballad-heritage",
    "现代R&B与Neo-Soul": "modern-rnb-neo-soul",
    "灵魂、蓝调与福音": "soul-blues-gospel",
    "电影感流行抒情": "cinematic-pop-ballad",
    "电影管弦与史诗配乐": "cinematic-orchestral-epic",
    "电子、合成器与氛围流行": "electronic-synth-ambient-pop",
    "爵士、摇摆与大乐队": "jazz-swing-big-band",
    "传统声乐、音乐剧与舞台": "traditional-vocal-stage",
    "嘻哈、说唱、Trap与Drill": "hip-hop-rap",
    "金属与重型摇滚": "metal-heavy-rock",
    "流行、另类与独立摇滚": "pop-alternative-rock",
    "当代民谣与原声": "contemporary-folk-acoustic",
    "根源、传统与世界音乐": "roots-traditional-global",
    "通用流行与抒情": "general-pop-ballad",
    "舞曲流行、迪斯科与Funk": "dance-pop-disco-funk",
    "俱乐部EDM、House与Trance": "club-edm-house-trance",
    "乡村与Americana": "country-americana",
}

AUTO_ROUTE_CUES = {
    "east-asian-modern": ("c-pop", "mandopop", "cantopop", "j-pop", "华语流行", "国语流行", "粤语流行", "日系流行", "国风流行"),
    "east-asian-ballad-heritage": ("华语抒情", "粤语抒情", "日系抒情", "国风抒情", "古风", "中国风", "东方抒情"),
    "modern-rnb-neo-soul": ("r&b", "rnb", "neo-soul", "neo soul", "节奏布鲁斯", "另类r&b", "氛围r&b"),
    "soul-blues-gospel": ("soul", "blues", "gospel", "worship", "灵魂乐", "蓝调", "福音", "敬拜"),
    "cinematic-pop-ballad": ("cinematic pop", "cinematic ballad", "orchestral pop", "电影感流行", "电影感抒情", "管弦流行"),
    "cinematic-orchestral-epic": ("film score", "soundtrack", "trailer", "orchestral", "symphonic", "电影配乐", "影视配乐", "预告片", "管弦", "交响", "史诗合唱"),
    "electronic-synth-ambient-pop": ("synth-pop", "synthpop", "electropop", "dream pop", "ambient pop", "darkwave", "retrowave", "合成器流行", "电子流行", "梦幻流行", "暗潮", "复古电子", "氛围流行"),
    "jazz-swing-big-band": ("jazz", "swing", "big band", "bossa nova", "爵士", "摇摆", "大乐队", "波萨诺瓦"),
    "traditional-vocal-stage": ("crooner", "doo-wop", "a cappella", "musical theatre", "show tune", "cabaret", "音乐剧", "舞台剧", "无伴奏", "歌舞剧", "卡巴莱"),
    "hip-hop-rap": ("hip-hop", "hip hop", "rap", "trap", "drill", "lo-fi hip-hop", "嘻哈", "说唱", "陷阱", "钻头"),
    "metal-heavy-rock": ("metal", "metalcore", "hard rock", "post-hardcore", "nu-metal", "金属", "金属核", "硬摇滚", "后硬核", "新金属"),
    "pop-alternative-rock": ("pop rock", "alternative rock", "indie rock", "arena rock", "j-rock", "punk", "流行摇滚", "另类摇滚", "独立摇滚", "朋克", "后摇"),
    "contemporary-folk-acoustic": ("indie folk", "folk pop", "singer-songwriter", "acoustic pop", "当代民谣", "独立民谣", "民谣流行", "唱作人", "原声流行"),
    "roots-traditional-global": ("traditional folk", "celtic", "reggae", "maritime", "world music", "传统民乐", "凯尔特", "雷鬼", "世界音乐", "民族融合"),
    "dance-pop-disco-funk": ("dance-pop", "dance pop", "nu-disco", "disco", "funk-pop", "funk", "舞曲流行", "迪斯科", "放克"),
    "club-edm-house-trance": ("edm", "house", "trance", "hardstyle", "dubstep", "techno", "club", "浩室", " trance", "硬派", "回响贝斯", "科技舞曲", "俱乐部"),
    "country-americana": ("country", "americana", "bluegrass", "rockabilly", "乡村", "美式根源", "蓝草", "乡村摇滚"),
    "general-pop-ballad": ("pop", "ballad", "流行", "抒情", "情歌"),
}

QUERY_ALIASES = {
    "女声": "female singer soprano mezzo",
    "男声": "male singer tenor baritone",
    "男女对唱": "male female duet",
    "合唱": "choir choral ensemble",
    "纯器乐": "instrumental no vocals",
    "说唱": "rap rhythmic vocal",
    "念白": "spoken word narration",
    "钢琴": "piano",
    "电钢琴": "rhodes electric piano",
    "木吉他": "acoustic guitar",
    "电吉他": "electric guitar",
    "弦乐": "strings orchestral",
    "管弦": "orchestral strings brass",
    "铜管": "brass",
    "贝斯": "bass",
    "鼓组": "drums percussion",
    "电子鼓": "electronic drums",
    "合成器": "synth synthesizer",
    "二胡": "erhu chinese bowed string",
    "琵琶": "pipa chinese traditional",
    "笛箫": "dizi flute chinese traditional",
    "班卓": "banjo",
    "曼陀林": "mandolin",
    "忧伤": "melancholic sorrowful",
    "温暖": "warm intimate",
    "明亮": "bright uplifting",
    "史诗": "epic majestic",
    "梦幻": "dreamy ethereal",
    "暗黑": "dark ominous",
    "热血": "energetic triumphant",
    "复古": "retro vintage",
    "亲密": "intimate close",
    "空灵": "ethereal ambient",
    "慢速": "slow",
    "中速": "midtempo",
    "快速": "fast uptempo",
}

MOOD_ARCS = [
    "自动识别",
    "克制铺陈 → 温暖释放 → 余韵收束",
    "脆弱低语 → 渐强 → 宣言式高潮",
    "平静神秘 → 紧张堆叠 → 史诗爆发",
    "忧伤回望 → 希望抬升 → 治愈落地",
    "明亮轻快 → 律动推进 → 庆祝式收尾",
    "暗涌压迫 → 强烈对抗 → 决绝收束",
    "浪漫亲密 → 宽阔抒情 → 温柔回落",
    "梦幻漂浮 → 迷离扩张 → 空灵淡出",
    "热血蓄力 → 高能副歌 → 胜利定格",
    "自定义",
]

TEMPO_OPTIONS = [
    "自动识别",
    "慢速｜60–78 BPM",
    "中慢｜79–96 BPM",
    "中速｜97–115 BPM",
    "中快｜116–132 BPM",
    "快速｜133–155 BPM",
    "高速｜156–180 BPM",
    "自定义",
]
METER_OPTIONS = ["自动识别", "4/4", "3/4", "6/8", "12/8", "自由节拍/无固定律动", "自定义"]
SCENARIO_OPTIONS = [
    "自动识别",
    "流媒体完整歌曲",
    "影视剧情/片尾曲",
    "电影或游戏配乐",
    "品牌广告/产品短片",
    "短视频背景音乐",
    "现场舞台/音乐节",
    "游戏战斗/关卡循环",
    "冥想、疗愈与睡眠",
    "儿童与亲子内容",
    "自定义",
]
DURATION_OPTIONS = ["自动识别", "30–60秒", "1–2分钟", "2–3分钟", "3–4分钟", "4–5分钟", "自定义"]
TONALITY_OPTIONS = [
    "自动识别/不指定",
    "明亮大调倾向",
    "忧郁小调倾向",
    "大小调转换",
    "五声音阶/国风调式",
    "布鲁斯调式",
    "爵士扩展和声",
    "模态/氛围化和声",
    "无明确调性",
    "自定义",
]
GROOVE_OPTIONS = [
    "自动识别",
    "平稳流行律动",
    "半拍/半速重心",
    "Swing摇摆律动",
    "Shuffle切分律动",
    "四拍踩底舞曲律动",
    "Trap切分与Hi-hat滚奏",
    "Funk切分与贝斯主导",
    "拉丁/波萨律动",
    "摇滚直拍与强反拍",
    "自由节奏/氛围脉冲",
    "自定义",
]
VOCAL_OPTIONS = [
    "自动识别",
    "纯器乐｜禁止人声与歌词",
    "单人女声",
    "单人男声",
    "中性/不限定性别单人声",
    "男女对唱",
    "双女声和声",
    "双男声和声",
    "混声主唱与合唱团",
    "说唱主唱",
    "念白/旁白与音乐",
    "无伴奏合唱",
    "自定义",
]
REGISTER_OPTIONS = [
    "自动识别",
    "低沉低音区",
    "温暖中低音区",
    "自然中音区",
    "明亮中高音区",
    "高音区与假声",
    "宽音域渐进",
    "说唱/近说话音域",
    "纯器乐主旋律",
    "自定义",
]
TIMBRE_OPTIONS = [
    "自动识别",
    "清澈明亮",
    "温暖柔和",
    "气声亲密",
    "醇厚磁性",
    "沙哑颗粒感",
    "高亢有力",
    "空灵通透",
    "复古爵士",
    "灵魂乐律动感",
    "激烈嘶吼/失真",
    "自定义",
]
DELIVERY_OPTIONS = [
    "自动识别",
    "叙述式、克制",
    "细腻气声、贴耳",
    "抒情渐强、宽阔副歌",
    "强力真声与高音爆发",
    "R&B转音与即兴Ad-lib",
    "节奏说唱、吐字清晰",
    "吟唱/颂唱",
    "戏剧化音乐剧演唱",
    "合唱式群体呼应",
    "纯器乐主旋律",
    "自定义",
]
HARMONY_OPTIONS = [
    "自动识别",
    "无伴唱、单主唱",
    "副歌轻量叠唱",
    "贴近三度/六度和声",
    "宽阔多轨和声墙",
    "领唱与群体呼应",
    "男女声对位",
    "福音式合唱抬升",
    "氛围哼唱与人声Pad",
    "自定义",
]
INSTRUMENT_OPTIONS = [
    "自动识别",
    "钢琴 + 弦乐 + 克制鼓组",
    "指弹木吉他 + 轻鼓 + 温暖贝斯",
    "Rhodes电钢琴 + 圆润贝斯 + R&B鼓组",
    "合成器Pad + 琶音 + 电子鼓",
    "失真电吉他 + 贝斯 + 现场鼓组",
    "管弦乐团 + 铜管 + 合唱",
    "808贝斯 + Trap鼓组 + 氛围采样",
    "House四拍 + 贝斯线 + 合成器Lead",
    "迪斯科吉他 + 铜管 + Funk贝斯",
    "爵士钢琴 + 立式贝斯 + 刷鼓",
    "国风弦乐/笛箫 + 现代节拍",
    "二胡/琵琶 + 管弦乐",
    "班卓琴/曼陀林 + 原声乐队",
    "手碟/民族打击 + 世界音乐纹理",
    "无伴奏人声层次",
    "自定义",
]
STRUCTURE_OPTIONS = [
    "自动识别",
    "Intro → Verse → Pre-Chorus → Chorus → Verse → Chorus → Bridge → Final Chorus → Outro",
    "Intro → Verse → Chorus → Verse → Chorus → Outro",
    "Intro → Verse → Pre-Chorus → Chorus → Post-Chorus → Bridge → Final Chorus → Outro",
    "Intro → Build → Drop → Breakdown → Final Drop → Outro",
    "Intro → Rap Verse → Hook → Rap Verse → Hook → Bridge → Final Hook → Outro",
    "Intro → A段 → B段 → A'段 → B'段 → Outro",
    "Intro → Verse → Chorus → Instrumental Solo → Chorus → Outro",
    "单段循环式氛围发展",
    "自定义",
]
PRODUCTION_OPTIONS = [
    "自动识别",
    "自然有机、动态呼吸",
    "现代流行、清晰宽阔",
    "温暖复古、磁带/黑胶质感",
    "电影化宽动态与空间层次",
    "俱乐部级紧实低频与冲击力",
    "Lo-fi柔化、颗粒与轻微失真",
    "极简干净、主体靠前",
    "密集墙式音色、强压缩",
    "空灵氛围、长尾混响",
    "现场乐队、真实房间感",
    "自定义",
]
SPACE_OPTIONS = [
    "自动识别",
    "亲密近场、主唱居中",
    "适度宽声场、清晰层次",
    "大空间厅堂混响",
    "电影化深景与环绕感",
    "俱乐部直接、有力且紧实",
    "朦胧梦幻、延迟与长尾",
    "干声靠前、少量空间效果",
    "自定义",
]
DENSITY_OPTIONS = [
    "自动识别",
    "极简留白",
    "由疏到密逐步堆叠",
    "中等密度、层次清晰",
    "副歌宽阔、主歌克制",
    "持续高能密集",
    "段落间强烈疏密对比",
    "自定义",
]
DETAIL_OPTIONS = ["精简｜180–250词", "标准｜250–450词", "详细｜450–650词", "自定义"]
OUTPUT_OPTIONS = ["结构化文本", "JSON", "JSONL"]
LANGUAGE_OPTIONS = ["英文（Music 3推荐）", "中文", "双语：英文为主、中文注释"]
EXCLUSION_OPTIONS = [
    "无",
    "禁止人声",
    "禁止说唱",
    "禁止电子鼓与808",
    "禁止失真吉他",
    "禁止合唱团",
    "禁止过度混响",
    "禁止过度压缩/响度战争",
    "禁止悲伤走向",
    "禁止史诗化堆叠",
    "自定义",
]


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(str(message).encode(encoding, errors="replace").decode(encoding, errors="replace"))


def _response_error(response):
    try:
        body = response.json()
    except Exception:
        return str(getattr(response, "text", "") or "")[:1000]
    if isinstance(body, dict):
        detail = body.get("error") or body.get("message") or body.get("detail") or body
        return json.dumps(detail, ensure_ascii=False) if isinstance(detail, (dict, list)) else str(detail)
    return str(body)


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
        text = _content_text(message.get("content"))
        if text:
            return text
        if first.get("text") is not None:
            return str(first["text"])
    return str(result.get("output_text") or result.get("text") or "")


def _sanitized_result(value):
    if isinstance(value, dict):
        return {key: _sanitized_result(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitized_result(item) for item in value]
    return value


def _strip_code_fence(text):
    value = str(text or "").strip()
    if value.startswith("```"):
        lines = value.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines.pop()
        value = "\n".join(lines).strip()
    return value


def _parse_json_object(text):
    cleaned = _strip_code_fence(text)
    try:
        parsed = json.loads(cleaned)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for position, character in enumerate(cleaned):
            if character != "{":
                continue
            try:
                parsed, _ = decoder.raw_decode(cleaned[position:])
            except json.JSONDecodeError:
                continue
            return parsed if isinstance(parsed, dict) else None
    return None


def _heading_section(text, heading, following=None):
    pattern = rf"(?ims)^###?\s*{re.escape(heading)}\s*$\s*(.*?)(?=^###?\s*(?:{re.escape(following) if following else 'Global Metadata|Vocal Details|Arrangement'})\s*$|\Z)"
    match = re.search(pattern, str(text or ""))
    return match.group(1).strip() if match else ""


def _make_caption(global_metadata, vocal_details, arrangement):
    return (
        "### Global Metadata\n\n"
        f"{str(global_metadata or '').strip()}\n\n"
        "### Vocal Details\n\n"
        f"{str(vocal_details or '').strip()}\n\n"
        "### Arrangement\n\n"
        f"{str(arrangement or '').strip()}"
    ).strip()


def _parse_compiler_output(text):
    parsed = _parse_json_object(text)
    if isinstance(parsed, dict):
        global_metadata = str(parsed.get("global_metadata") or parsed.get("Global Metadata") or "").strip()
        vocal_details = str(parsed.get("vocal_details") or parsed.get("Vocal Details") or "").strip()
        arrangement = str(parsed.get("arrangement") or parsed.get("Arrangement") or "").strip()
        if global_metadata and vocal_details and arrangement:
            return {
                "caption": _make_caption(global_metadata, vocal_details, arrangement),
                "global_metadata": global_metadata,
                "vocal_details": vocal_details,
                "arrangement": arrangement,
                "generated_lyrics": str(parsed.get("generated_lyrics") or "").strip(),
                "music_brief": str(parsed.get("music_brief") or "").strip(),
                "validation": str(parsed.get("validation") or "").strip(),
            }
    cleaned = _strip_code_fence(text)
    global_metadata = _heading_section(cleaned, "Global Metadata", "Vocal Details")
    vocal_details = _heading_section(cleaned, "Vocal Details", "Arrangement")
    arrangement = _heading_section(cleaned, "Arrangement")
    return {
        "caption": _make_caption(global_metadata, vocal_details, arrangement) if all((global_metadata, vocal_details, arrangement)) else cleaned,
        "global_metadata": global_metadata,
        "vocal_details": vocal_details,
        "arrangement": arrangement,
        "generated_lyrics": "",
        "music_brief": "",
        "validation": "",
    }


def _extract_lyric_tags(lyrics):
    tags = []
    for raw in re.findall(r"\[([^\]\r\n]{1,120})\]", str(lyrics or "")):
        tag = "[" + re.sub(r"\s+", " ", raw).strip() + "]"
        if tag not in tags:
            tags.append(tag)
    return tags


def _lyric_leakage(lyrics, caption):
    normalized_caption = re.sub(r"\s+", " ", str(caption or "").lower())
    leaks = []
    for line in str(lyrics or "").splitlines():
        line = re.sub(r"\[[^\]]+\]", "", line).strip()
        normalized = re.sub(r"\s+", " ", line.lower())
        if len(normalized) >= 20 and normalized in normalized_caption:
            leaks.append(line[:80])
    return leaks[:3]


def _is_instrumental_request(request, controls):
    vocal_mode = str(controls.get("人声配置") or "")
    exclusions = str(controls.get("排除项") or "")
    source = str(request or "").lower()
    explicit_phrases = (
        "纯器乐", "纯音乐", "无人声", "不要人声", "禁止人声", "无歌词",
        "instrumental only", "no vocals", "without vocals",
    )
    return (
        "纯器乐" in vocal_mode
        or "禁止人声" in exclusions
        or any(phrase in source for phrase in explicit_phrases)
    )


def _validate_generated_lyrics(lyrics):
    text = str(lyrics or "").strip()
    if not text:
        raise RuntimeError("LLM没有生成歌词。")
    if not _extract_lyric_tags(text):
        raise RuntimeError("LLM生成的歌词缺少[Verse]、[Chorus]等Music3段落标签。")
    lyric_body = re.sub(r"\[[^\]]+\]", "", text).strip()
    if len(lyric_body) < 12:
        raise RuntimeError("LLM生成的歌词正文过短。")
    return text


def _parse_index_cards(index_path):
    cards = []
    try:
        lines = index_path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return cards
    for line in lines:
        if not line.startswith("| `"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        template_match = re.search(r"`templates/([^`]+)`", cells[-1])
        identifier = cells[0].strip("`")
        if not template_match or not identifier:
            continue
        cards.append({
            "id": identifier,
            "style": cells[1],
            "secondary": cells[2],
            "tempo": cells[3],
            "mood": cells[4],
            "vocal": cells[5],
            "palette": cells[6],
            "template": template_match.group(1),
        })
    return cards


def _keyword_tokens(text):
    source = str(text or "").lower()
    expanded = [source]
    for cue, english in QUERY_ALIASES.items():
        if cue in source:
            expanded.append(english)
    return {
        token for token in re.findall(r"[a-z0-9+#&']{2,}", str(text or "").lower())
        if token not in {"the", "and", "with", "for", "from", "into", "auto"}
    } | {
        token for token in re.findall(r"[a-z0-9+#&']{2,}", " ".join(expanded))
        if token not in {"the", "and", "with", "for", "from", "into", "auto"}
    }


def _route_automatic_family(text, exclude=None):
    source = str(text or "").lower()
    scored = []
    for family, cues in AUTO_ROUTE_CUES.items():
        if family == exclude:
            continue
        score = 0
        for cue in cues:
            if re.fullmatch(r"[a-z0-9 &+.'/-]+", cue):
                matched = re.search(rf"(?<![a-z0-9]){re.escape(cue)}(?![a-z0-9])", source) is not None
            else:
                matched = cue in source
            if matched:
                score += 3 if len(cue) >= 5 else 2
        if family == "general-pop-ballad":
            score = min(score, 1)
        scored.append((score, family))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][1] if scored and scored[0][0] > 0 else "general-pop-ballad"


def _select_templates(families, query, maximum=3):
    tokens = _keyword_tokens(query)
    ranked_by_family = []
    seen = set()
    for family in families:
        if not family or family in seen:
            continue
        seen.add(family)
        cards = _parse_index_cards(RESOURCE_ROOT / "references" / f"index-{family}.md")
        scored = []
        for order, card in enumerate(cards):
            text = " ".join(card[key] for key in ("style", "secondary", "tempo", "mood", "vocal", "palette"))
            score = len(tokens & _keyword_tokens(text))
            scored.append((score, -order, card))
        if scored:
            scored.sort(reverse=True)
            ranked_by_family.append([item[2] for item in scored])
    selected = []
    if ranked_by_family:
        selected.append(ranked_by_family[0][0])
    if len(ranked_by_family) > 1 and ranked_by_family[1]:
        selected.append(ranked_by_family[1][0])
    for card in ranked_by_family[0][1:] if ranked_by_family else []:
        if card["id"] not in {item["id"] for item in selected}:
            selected.append(card)
        if len(selected) >= maximum:
            break
    references = []
    for card in selected[:maximum]:
        try:
            content = (RESOURCE_ROOT / "templates" / card["template"]).read_text(encoding="utf-8").strip()
        except OSError:
            content = ""
        if content:
            references.append({"card": card, "caption": content})
    return references


def _choice_with_custom(value, custom_value):
    value = str(value or "自动识别").strip()
    if value == "自定义":
        custom_value = str(custom_value or "").strip()
        if not custom_value:
            raise ValueError("已选择“自定义”，请填写对应的自定义内容。")
        return custom_value
    return value


SYSTEM_PROMPT = """You are the MiniMax Music 3 Structured Caption and lyrics compiler.

Turn a concise music request and optional lyrics into a fresh, generation-oriented Music 3 caption. Work privately: first form a Music Brief, resolve constraints, route to the supplied style family references, choose at most three references with Foundation / Modifier / Arrangement roles, then create a coherent timeline. Never reveal reference IDs, routing scores, template content, or chain of thought.

Hard rules, in priority order:
1. Preserve explicit user requirements and exclusions. Then preserve section-local bracketed lyric tags. Do not let a reference override them.
2. When source lyrics are supplied, they are immutable private analysis material: never quote, paraphrase, summarize, translate, or repeat them in the caption. Return an empty generated_lyrics field because the node preserves the original text itself. Only their bracketed tags may become section-level arrangement directives.
3. When source lyrics are absent and the request is vocal music, create a complete original lyric in generated_lyrics. Use Music3 bracketed section tags such as [Intro], [Verse 1], [Pre-Chorus], [Chorus], [Bridge], and [Outro], following the selected song structure. Match the language and subject implied by the user's request; for a primarily Chinese request with no stated lyric language, use Simplified Chinese. Do not put lyrics in any caption field.
4. When the request is instrumental or forbids vocals, generated_lyrics must be an empty string and Vocal Details must describe the lead melodic instrument or texture.
5. Do not reverse a specified vocal gender, tempo constraint, required instrument, or prohibition.
6. Do not fabricate exact BPM, key, scale, vocalist identity, or technical production claims. Use a range or qualitative description unless explicitly supplied or clearly justified by the controls.
7. References are inspiration only. Do not copy sentences, distinctive phrases, exact instrument lifecycles, or full structures. Synthesize a new result.
8. Make an audible section-by-section arrangement: explain entrances, exits, intensification, groove changes, transitions, and texture lifecycle. Do not return a static equipment list.

Return JSON only, without markdown fences, with exactly these keys:
{
  "global_metadata": "...",
  "vocal_details": "...",
  "arrangement": "...",
  "generated_lyrics": "complete tagged lyrics when source lyrics are absent and vocals are wanted; otherwise an empty string",
  "music_brief": "short non-sensitive summary of preserved user constraints only",
  "validation": "short confirmation of constraint, lyric-tag, and structure checks"
}

The three caption fields must render as exactly these headings when assembled: Global Metadata, Vocal Details, Arrangement. Do not place a song title, template ID, lyrics, or hidden reasoning in those caption fields."""


class Music3CaptionLLMClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/Music3CaptionCompiler",
        }
        try:
            response = requests.post(CHAT_ENDPOINT, headers=headers, json=payload, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RuntimeError(f"{friendly_network_error(error, '提交LLM请求')} LLM请求不会自动重试，以免重复扣费。") from error
        if response.status_code >= 400:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status())
            labels = {
                400: "请求参数错误",
                401: "API密钥无效或认证失败",
                402: "账户余额不足",
                403: "当前密钥没有该模型权限",
                404: "LLM模型映射不存在",
                429: "请求过于频繁，请稍后重试",
                500: "服务端处理异常，请稍后重试或切换LLM模型",
                502: "上游LLM暂时不可用，请稍后重试或切换LLM模型",
                503: "LLM服务暂时繁忙，请稍后重试或切换LLM模型",
            }
            raise RuntimeError(f"{labels.get(response.status_code, 'LLM请求失败')} {response.status_code}：{_response_error(response)}")
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站返回内容不是 JSON：{response.text[:500]}") from error


class DapaoMusic3CaptionPromptNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🔑 API密钥": ("STRING", {"default": "", "placeholder": "填入 dapaoAI API 密钥", "tooltip": "密钥仅用于 https://api.dapaoai.com，不写入配置文件。"}),
                "🤖 LLM模型": (MODEL_OPTIONS, {"default": "gemini-3.7-flash"}),
                "📝 原始音乐需求": ("STRING", {"multiline": True, "default": "温暖的原声流行歌曲，亲密女声，副歌逐步扩张并在结尾温柔收束。", "placeholder": "描述音乐风格、情绪、场景或你希望保留的核心元素……"}),
                "🎼 主风格": (GENRE_FAMILIES, {"default": "自动识别"}),
                "🧬 融合风格": (["无"] + GENRE_FAMILIES, {"default": "无"}),
                "🎯 使用场景": (SCENARIO_OPTIONS, {"default": "自动识别"}),
                "⏳ 目标曲长": (DURATION_OPTIONS, {"default": "自动识别"}),
                "💫 情绪弧": (MOOD_ARCS, {"default": "自动识别"}),
                "⏱️ 速度": (TEMPO_OPTIONS, {"default": "自动识别"}),
                "🎹 调性倾向": (TONALITY_OPTIONS, {"default": "自动识别/不指定"}),
                "🎚️ 拍号/律动": (METER_OPTIONS, {"default": "自动识别"}),
                "🥁 核心律动": (GROOVE_OPTIONS, {"default": "自动识别"}),
                "🎙️ 人声配置": (VOCAL_OPTIONS, {"default": "自动识别"}),
                "📈 人声音域": (REGISTER_OPTIONS, {"default": "自动识别"}),
                "🗣️ 人声音色": (TIMBRE_OPTIONS, {"default": "自动识别"}),
                "🎤 演唱方式": (DELIVERY_OPTIONS, {"default": "自动识别"}),
                "👥 和声/伴唱": (HARMONY_OPTIONS, {"default": "自动识别"}),
                "🎻 核心乐器编制": (INSTRUMENT_OPTIONS, {"default": "自动识别"}),
                "🧱 歌曲结构": (STRUCTURE_OPTIONS, {"default": "自动识别"}),
                "🎛️ 制作质感": (PRODUCTION_OPTIONS, {"default": "自动识别"}),
                "🌌 空间与混响": (SPACE_OPTIONS, {"default": "自动识别"}),
                "🔥 编曲密度": (DENSITY_OPTIONS, {"default": "自动识别"}),
                "🚫 排除项": (EXCLUSION_OPTIONS, {"default": "无"}),
                "🌐 输出语言": (LANGUAGE_OPTIONS, {"default": "英文（Music 3推荐）"}),
                "📏 输出详略": (DETAIL_OPTIONS, {"default": "标准｜250–450词"}),
                "📦 输出格式": (OUTPUT_OPTIONS, {"default": "结构化文本", "tooltip": "旧工作流兼容控件；当前始终输出可直连Music3的音乐描述与原始歌词。"}),
                "🌡️ 温度": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 2.0, "step": 0.01}),
                "📝 最大输出令牌": ("INT", {"default": 4096, "min": 512, "max": 16384, "step": 1}),
                "🎲 Top_P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": "randomize", "tooltip": "只控制ComfyUI缓存，不发送给LLM。"}),
                "⌛ 请求超时": ("INT", {"default": 300, "min": 30, "max": 1200, "step": 10}),
            },
            "optional": {
                "🔗 外部音乐需求": ("STRING", {"forceInput": True, "default": "", "tooltip": "连接任意STRING节点；存在时与本节点的原始音乐需求合并。"}),
                "📝 歌词": ("STRING", {"multiline": True, "default": "", "placeholder": "可选。留空时自动生成完整歌词；填写后原样输出，可含 [Verse]、[Chorus]、[Bridge] 等段落标签。"}),
                "🔗 外部歌词": ("STRING", {"forceInput": True, "default": "", "tooltip": "可连接歌词文本；存在时与本节点歌词合并并原样输出。没有任何歌词输入时由LLM自动生成。"}),
                "➕ 补充约束": ("STRING", {"multiline": True, "default": "", "placeholder": "可选：指定BPM、调性、必须保留的乐器、时长、用途或额外禁用项。"}),
                "✍️ 自定义主风格": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义融合风格": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义使用场景": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义目标曲长": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义情绪弧": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义速度": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义调性倾向": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义拍号/律动": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义核心律动": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义人声配置": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义人声音域": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义人声音色": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义演唱方式": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义和声/伴唱": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义乐器编制": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义歌曲结构": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义制作质感": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义空间与混响": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义编曲密度": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义排除项": ("STRING", {"multiline": True, "default": ""}),
                "✍️ 自定义输出详略": ("STRING", {"multiline": True, "default": "", "placeholder": "例如：320–400 English words"}),
                "🚫 出错时跳过": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING", "STRING")
    RETURN_NAMES = (
        "🎼 音乐描述",
        "📝 歌词",
        "🌐 全局音乐信息",
        "🎙️ 人声细节",
        "🧱 编曲结构",
        "📑 音乐结构分析",
        "📄 语言模型完整响应",
        "ℹ️ 处理信息",
    )
    FUNCTION = "generate_prompt"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "生成MiniMax Music 3结构化音乐描述和完整歌词；无歌词时自动创作，有歌词时原样保留，前两个输出可直连官方Music3 Text Encode。"

    @staticmethod
    def _compose_controls(kwargs):
        fields = [
            ("主风格", "🎼 主风格", "✍️ 自定义主风格"),
            ("融合风格", "🧬 融合风格", "✍️ 自定义融合风格"),
            ("使用场景", "🎯 使用场景", "✍️ 自定义使用场景"),
            ("目标曲长", "⏳ 目标曲长", "✍️ 自定义目标曲长"),
            ("情绪弧", "💫 情绪弧", "✍️ 自定义情绪弧"),
            ("速度", "⏱️ 速度", "✍️ 自定义速度"),
            ("调性倾向", "🎹 调性倾向", "✍️ 自定义调性倾向"),
            ("拍号/律动", "🎚️ 拍号/律动", "✍️ 自定义拍号/律动"),
            ("核心律动", "🥁 核心律动", "✍️ 自定义核心律动"),
            ("人声配置", "🎙️ 人声配置", "✍️ 自定义人声配置"),
            ("人声音域", "📈 人声音域", "✍️ 自定义人声音域"),
            ("人声音色", "🗣️ 人声音色", "✍️ 自定义人声音色"),
            ("演唱方式", "🎤 演唱方式", "✍️ 自定义演唱方式"),
            ("和声/伴唱", "👥 和声/伴唱", "✍️ 自定义和声/伴唱"),
            ("核心乐器编制", "🎻 核心乐器编制", "✍️ 自定义乐器编制"),
            ("歌曲结构", "🧱 歌曲结构", "✍️ 自定义歌曲结构"),
            ("制作质感", "🎛️ 制作质感", "✍️ 自定义制作质感"),
            ("空间与混响", "🌌 空间与混响", "✍️ 自定义空间与混响"),
            ("编曲密度", "🔥 编曲密度", "✍️ 自定义编曲密度"),
            ("排除项", "🚫 排除项", "✍️ 自定义排除项"),
            ("输出详略", "📏 输出详略", "✍️ 自定义输出详略"),
        ]
        controls = {}
        for label, field, custom_field in fields:
            value = kwargs.get(field, "自动识别")
            if label == "融合风格" and value == "无":
                controls[label] = "无"
            elif label == "排除项" and value == "无":
                controls[label] = "无"
            else:
                controls[label] = _choice_with_custom(value, kwargs.get(custom_field, ""))
        return controls

    @staticmethod
    def _reference_families(kwargs):
        main = kwargs.get("🎼 主风格", "自动识别")
        fusion = kwargs.get("🧬 融合风格", "无")
        routing_text = "\n".join(
            str(kwargs.get(name) or "")
            for name in ("📝 原始音乐需求", "🔗 外部音乐需求", "➕ 补充约束")
        )
        primary = FAMILY_FILE_BY_OPTION.get(main)
        if main == "自动识别":
            primary = _route_automatic_family(routing_text)
        families = [primary]
        if fusion == "自动识别" and re.search(r"(?:融合|混合|结合|with|influence|/|\+)", routing_text, re.I):
            families.append(_route_automatic_family(routing_text, exclude=primary))
        elif fusion != "无":
            families.append(FAMILY_FILE_BY_OPTION.get(fusion))
        return [family for family in families if family]

    @staticmethod
    def _build_user_content(request, lyrics, controls, output_language, references):
        tags = _extract_lyric_tags(lyrics)
        reference_blocks = []
        for number, reference in enumerate(references, 1):
            card = reference["card"]
            reference_blocks.append(
                f"REFERENCE {number} (internal inspiration only, do not copy):\n"
                f"Role candidate: style={card['style']}; tempo/key={card['tempo']}; mood={card['mood']}; "
                f"vocal={card['vocal']}; palette={card['palette']}\n"
                f"Complete reference caption:\n{reference['caption']}"
            )
        language_instruction = {
            "英文（Music 3推荐）": "Write all caption content in English.",
            "中文": "Write all caption content in Simplified Chinese. Keep the three final heading names in English when the caller assembles them.",
            "双语：英文为主、中文注释": "Write the main caption content in English, then add concise Simplified Chinese explanations in parentheses only where useful.",
        }.get(output_language, "Write all caption content in English.")
        instrumental = _is_instrumental_request(request, controls)
        if lyrics.strip():
            lyrics_mode = "SOURCE LYRICS PROVIDED: preserve them externally; generated_lyrics must be empty."
        elif instrumental:
            lyrics_mode = "INSTRUMENTAL REQUEST: generated_lyrics must be empty."
        else:
            lyrics_mode = "NO SOURCE LYRICS: generate a complete original, section-tagged lyric in generated_lyrics."
        return (
            "USER MUSIC REQUEST:\n"
            f"{request}\n\n"
            "EXPLICIT CONTROL PANEL:\n"
            f"{json.dumps(controls, ensure_ascii=False, indent=2)}\n\n"
            f"LYRIC SECTION TAGS ONLY (must be honored as local arrangement directives): {', '.join(tags) if tags else 'none'}\n"
            f"LYRICS MODE: {lyrics_mode}\n"
            "SOURCE LYRICS FOR PRIVATE HIGH-LEVEL MOOD ANALYSIS ONLY. Never quote, paraphrase, summarize, translate, or repeat them in the caption:\n"
            f"{lyrics if lyrics.strip() else '[no lyrics supplied]'}\n\n"
            f"OUTPUT LANGUAGE: {language_instruction}\n"
            "Always return the required JSON object; the node will assemble the Music 3 caption and choose source or generated lyrics separately.\n\n"
            "SELECTED LOCAL STYLE REFERENCES:\n"
            f"{'\n\n'.join(reference_blocks) if reference_blocks else 'No precise family was selected. Use conservative general-pop routing from the explicit controls.'}"
        )

    async def generate_prompt(self, **kwargs):
        return await asyncio.to_thread(self._generate_prompt_sync, **kwargs)

    def _generate_prompt_sync(self, **kwargs):
        result = {}
        try:
            api_key = str(kwargs.get("🔑 API密钥") or "").strip()
            model_id = str(kwargs.get("🤖 LLM模型") or "gemini-3.7-flash")
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_id not in MODEL_OPTIONS:
                raise ValueError(f"不支持的LLM映射模型：{model_id}")
            request_parts = [str(kwargs.get("📝 原始音乐需求") or "").strip(), str(kwargs.get("🔗 外部音乐需求") or "").strip()]
            request = "\n\n".join(part for part in request_parts if part)
            if not request:
                raise ValueError("原始音乐需求不能为空。")
            lyric_parts = [str(kwargs.get("📝 歌词") or "").strip(), str(kwargs.get("🔗 外部歌词") or "").strip()]
            lyrics = "\n".join(part for part in lyric_parts if part)
            supplement = str(kwargs.get("➕ 补充约束") or "").strip()
            if supplement:
                request = f"{request}\n\nAdditional explicit constraints:\n{supplement}"
            controls = self._compose_controls(kwargs)
            output_language = kwargs.get("🌐 输出语言", "英文（Music 3推荐）")
            if output_language not in LANGUAGE_OPTIONS:
                raise ValueError("输出语言不受支持。")
            reference_families = self._reference_families(kwargs)
            reference_query = " ".join([request, *controls.values()])
            references = _select_templates(reference_families, reference_query)
            user_content = self._build_user_content(request, lyrics, controls, output_language, references)
            payload = {
                "model": model_id,
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user_content}],
                "temperature": float(kwargs.get("🌡️ 温度", 0.35)),
                "max_tokens": int(kwargs.get("📝 最大输出令牌", 4096)),
                "top_p": float(kwargs.get("🎲 Top_P", 1.0)),
                "stream": False,
            }
            _safe_print(f"[Music3Caption] 提交编译：model={model_id}，参考族={reference_families or ['自动路由']}，模板={len(references)}")
            started = time.time()
            result = Music3CaptionLLMClient(api_key, int(kwargs.get("⌛ 请求超时", 300))).chat(payload)
            raw_text = _extract_text(result)
            if not raw_text:
                raise RuntimeError("LLM返回内容为空。")
            compiled = _parse_compiler_output(raw_text)
            if not all((compiled["global_metadata"], compiled["vocal_details"], compiled["arrangement"])):
                raise RuntimeError("LLM未按Music 3规范返回完整的Global Metadata、Vocal Details和Arrangement。")
            caption = compiled["caption"]
            leakage = _lyric_leakage(lyrics, caption)
            if leakage:
                raise RuntimeError("LLM错误复述了歌词正文，为避免把歌词写入Music Caption已停止输出。")
            instrumental_requested = _is_instrumental_request(request, controls)
            instrumental_text = compiled["vocal_details"]
            affirmative_vocals = re.search(r"\b(?:singer|vocalist|lead vocals?|backing vocals?|singing|sung)\b", instrumental_text, re.I)
            negated_vocals = re.search(r"\b(?:no|without|absent|contains no)\s+(?:lead |backing )?vocals?\b|纯器乐|无人声|不含人声", instrumental_text, re.I)
            if instrumental_requested and affirmative_vocals and not negated_vocals:
                raise RuntimeError("LLM未遵守“纯器乐”要求，Vocal Details中仍出现人声内容。")
            if lyrics:
                output_lyrics = lyrics
                lyrics_mode = "保留用户输入歌词"
            elif instrumental_requested:
                output_lyrics = ""
                lyrics_mode = "纯器乐（无需歌词）"
            else:
                output_lyrics = _validate_generated_lyrics(compiled["generated_lyrics"])
                lyrics_mode = "LLM自动生成完整歌词"
            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            analysis = (
                "✅ Music 3结构化Caption已生成\n"
                f"主风格：{controls['主风格']}\n"
                f"融合风格：{controls['融合风格']}\n"
                f"本地参考：{len(references)}条（仅用于内部风格与编曲参考）\n"
                f"歌词段落标签：{', '.join(_extract_lyric_tags(output_lyrics)) if output_lyrics else '纯器乐，无歌词'}\n"
                f"歌词处理：{lyrics_mode}\n"
                f"约束校验：{compiled['validation'] or '已检查三段结构、显式控制与歌词正文隔离。'}"
            )
            info = (
                "✅ Music3音乐提示词生成完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 LLM模型：{model_id}\n"
                f"🎼 主风格：{controls['主风格']}\n"
                f"🧬 融合风格：{controls['融合风格']}\n"
                f"📚 本地参考模板：{len(references)}条\n"
                "📦 输出内容：Music3结构化音乐描述 + 完整歌词\n"
                f"📝 歌词处理：{lyrics_mode}\n"
                f"📥 输入令牌：{usage.get('prompt_tokens', usage.get('input_tokens', '未知'))}\n"
                f"📤 输出令牌：{usage.get('completion_tokens', usage.get('output_tokens', '未知'))}\n"
                f"⏱️ 耗时：{time.time() - started:.2f}秒"
            )
            return (
                caption,
                output_lyrics,
                compiled["global_metadata"],
                compiled["vocal_details"],
                compiled["arrangement"],
                analysis,
                json.dumps(_sanitized_result(result), ensure_ascii=False, indent=2),
                info,
            )
        except Exception as error:
            message = f"❌ Music3音乐提示词生成失败：{error}"
            _safe_print(message)
            _safe_print(traceback.format_exc())
            response_text = json.dumps({"error": str(error), "response": _sanitized_result(result)}, ensure_ascii=False, indent=2)
            if kwargs.get("🚫 出错时跳过", False):
                return message, str(kwargs.get("🔗 外部歌词") or kwargs.get("📝 歌词") or ""), message, message, message, message, response_text, message
            raise RuntimeError(message) from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoMusic3CaptionPromptNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoMusic3CaptionPromptNode",
    "MODEL_OPTIONS",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
