"""dapaoAI API multi-turn chat with local Skill orchestration and DOM UI."""

from __future__ import annotations

import asyncio
import ast
import json
import re
import time

from .api_skill_runtime import (
    api_messages,
    build_skill_prompt,
    clean_reply,
    current_message_content,
    estimate_text_tokens,
    get_skill,
    list_skills,
    message_content,
    normalize_history,
    normalize_image_refs,
    normalize_state,
    parse_skill_reply,
    resolve_skill_id,
    select_material_mentions,
    set_model_display_names,
    skill_catalog,
    trim_history,
)
from .gpt_llm_chat_node import DapaoGPTLLMClient, _extract_text
from .llm_model_options import DEFAULT_LLM_MODEL, LLM_MODEL_CAPABILITIES, LLM_MODEL_OPTIONS


API_BASE_URL = "https://api.dapaoai.com"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮API常用工具🍬"


def _request_time(request_id) -> int:
    try:
        return int(str(request_id or "").split("-", 1)[0])
    except (TypeError, ValueError):
        return int(time.time() * 1000)


def _latest_assistant_reply(history: list[dict]) -> str:
    for item in reversed(history):
        if item.get("role") == "assistant" and isinstance(item.get("content"), str):
            return item["content"]
    return ""


def _usage(result: dict) -> dict:
    raw = result.get("usage") if isinstance(result, dict) else {}
    raw = raw if isinstance(raw, dict) else {}

    def number(*names):
        for name in names:
            try:
                return max(0, int(raw.get(name)))
            except (TypeError, ValueError):
                continue
        return 0

    prompt = number("prompt_tokens", "input_tokens")
    completion = number("completion_tokens", "output_tokens")
    total = number("total_tokens") or prompt + completion
    return {"prompt_tokens": prompt, "completion_tokens": completion, "total_tokens": total}


def _response_cost(result: dict) -> tuple[float | None, str]:
    """Read an explicit service-returned cost without inventing model prices."""
    if not isinstance(result, dict):
        return None, ""
    usage = result.get("usage") if isinstance(result.get("usage"), dict) else {}
    currency = str(
        usage.get("currency")
        or usage.get("cost_currency")
        or result.get("currency")
        or result.get("cost_currency")
        or ""
    ).strip().upper()[:12]
    for source in (usage, result):
        for name in ("cost", "total_cost", "consumeMoney", "consume_money", "thirdPartyConsumeMoney"):
            try:
                value = float(source.get(name))
            except (TypeError, ValueError):
                continue
            if value < 0:
                continue
            if not currency and name in {"consumeMoney", "consume_money", "thirdPartyConsumeMoney"}:
                currency = "CNY"
            return value, currency
    return None, currency


class DapaoAPIChatAdapter:
    """One-task adapter; it intentionally performs no paid POST retries."""

    def __init__(self, config: dict):
        self.api_key = str(config["api_key"])
        self.model = str(config["model"])
        self.timeout = int(config["timeout"])
        self.calls = 0
        self.billed_tokens = 0
        self.usage_totals = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        self.total_cost = 0.0
        self.has_cost = False
        self.cost_currency = ""
        self.cost_currency_ambiguous = False
        self.last_usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def complete(self, messages: list[dict], params: dict) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": int(params.get("max_tokens", 1024)),
            "temperature": float(params.get("temperature", 0.7)),
            "top_p": float(params.get("top_p", 0.9)),
            "stream": False,
        }
        for name in ("frequency_penalty", "presence_penalty"):
            value = float(params.get(name, 0.0))
            if value:
                payload[name] = value
        # These two are not uniformly supported by every OpenAI-compatible
        # mapping. Send them only after the user changes their neutral values.
        if int(params.get("top_k", 20)) != 20:
            payload["top_k"] = int(params["top_k"])
        if abs(float(params.get("repeat_penalty", 1.0)) - 1.0) > 1e-9:
            payload["repeat_penalty"] = float(params["repeat_penalty"])

        print(
            f"[dapaoAPI-Skill多轮对话] 提交LLM请求：model={self.model}，"
            f"messages={len(messages)}，max_tokens={payload['max_tokens']}"
        )
        result = DapaoGPTLLMClient(self.api_key, self.timeout).chat(payload)
        text = _extract_text(result)
        if not text:
            raise RuntimeError("LLM返回内容为空。")
        self.calls += 1
        self.last_usage = _usage(result)
        self.billed_tokens += self.last_usage["total_tokens"]
        for key in self.usage_totals:
            self.usage_totals[key] += self.last_usage[key]
        cost, currency = _response_cost(result)
        if cost is not None:
            self.has_cost = True
            self.total_cost += cost
            if not currency:
                self.cost_currency = ""
                self.cost_currency_ambiguous = True
            elif not self.cost_currency_ambiguous:
                if self.cost_currency and self.cost_currency != currency:
                    self.cost_currency = ""
                    self.cost_currency_ambiguous = True
                elif not self.cost_currency:
                    self.cost_currency = currency
        print(
            f"[dapaoAPI-Skill多轮对话] LLM响应完成：call={self.calls}，"
            f"tokens={self.last_usage['total_tokens'] or '未返回usage'}"
        )
        return text


def _structured_values_from_text(text: str) -> list:
    value = str(text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", value, re.S | re.I)
    candidates = [fenced.group(1), value] if fenced else [value]
    decoder = json.JSONDecoder()
    values = []
    for candidate in candidates:
        variants = [candidate, candidate.translate(str.maketrans({"“": '"', "”": '"', "：": ":"}))]
        for variant in variants:
            for start in (match.start() for match in re.finditer(r"[\[{]", variant)):
                try:
                    parsed, _end = decoder.raw_decode(variant[start:])
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, (dict, list)) and parsed not in values:
                    values.append(parsed)
            try:
                parsed = ast.literal_eval(variant.strip())
            except (SyntaxError, ValueError):
                parsed = None
            if isinstance(parsed, (dict, list)) and parsed not in values:
                values.append(parsed)
    return values


def _json_object_from_text(text: str) -> dict:
    for parsed in _structured_values_from_text(text):
        if isinstance(parsed, dict):
            return parsed
    raise RuntimeError("模型没有返回有效的Skill名称JSON，请重试或手动修改。")


def _name_pairs_from_value(value) -> list[tuple[str, str]]:
    if isinstance(value, list):
        pairs = []
        for item in value:
            pairs.extend(_name_pairs_from_value(item))
        return pairs
    if not isinstance(value, dict):
        return []
    if "names" in value:
        return _name_pairs_from_value(value["names"])
    skill_id = value.get("id") or value.get("skill_id") or value.get("skill-id")
    display_name = value.get("display_name") or value.get("display-name") or value.get("title")
    if skill_id and not display_name and value.get("name") != skill_id:
        display_name = value.get("name")
    if isinstance(skill_id, str) and isinstance(display_name, str):
        return [(skill_id, display_name)]
    return [(str(key), item) for key, item in value.items() if isinstance(item, str)]


def _clean_model_name(value: str, skill_id: str) -> str:
    name = str(value or "").strip().strip("`|,，;；")
    name = re.sub(r"^\*\*(.*?)\*\*$", r"\1", name).strip()
    name = name.strip('"\'')
    name = re.sub(rf"\s*[\[（(]{re.escape(skill_id)}[\]）)]\s*$", "", name, flags=re.I).strip()
    if not re.search(r"[\u3400-\u9fff]", name) or not 1 <= len(name) <= 60:
        return ""
    if re.search(r"[\r\n]", name) or (skill_id and skill_id.lower() in name.lower()):
        return ""
    return name


def _skill_names_from_reply(text: str, skill_ids: list[str]) -> dict[str, str]:
    allowed = set(skill_ids)
    names: dict[str, str] = {}

    for value in _structured_values_from_text(text):
        for skill_id, raw_name in _name_pairs_from_value(value):
            skill_id = str(skill_id).strip()
            if skill_id in allowed:
                name = _clean_model_name(raw_name, skill_id)
                if name:
                    names[skill_id] = name

    unkeyed = []
    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("```") or re.fullmatch(r"[|:\-\s]+", line):
            continue
        matched = False
        for skill_id in sorted(allowed, key=len, reverse=True):
            if skill_id in names:
                continue
            position = line.find(skill_id)
            if position < 0:
                continue
            tail = line[position + len(skill_id):]
            tail = re.sub(r"^[\s\]）)'\"`|:=：—–-]+", "", tail)
            tail = re.sub(r"[|,，}\]]+\s*$", "", tail).strip()
            name = _clean_model_name(tail, skill_id)
            if name:
                names[skill_id] = name
                matched = True
                break
        if matched:
            continue
        candidate = re.sub(r"^\s*(?:[-*•]|\d+[.)、])\s*", "", line)
        candidate = _clean_model_name(candidate, "")
        if candidate and len(candidate) <= 32:
            unkeyed.append(candidate)

    unresolved = [skill_id for skill_id in skill_ids if skill_id not in names]
    if unresolved and len(unkeyed) == len(skill_ids):
        for skill_id, name in zip(skill_ids, unkeyed):
            names.setdefault(skill_id, name)
    return names


def optimize_skill_display_names(
    config,
    scope: str = "issues",
    overwrite_manual: bool = False,
    skill_ids: list[str] | None = None,
) -> dict:
    """Use one paid LLM call to propose display aliases only; never edit Skill content."""
    api_config = _api_config(config)
    scope = scope if scope in {"all", "selected"} else "issues"
    selected_ids = {str(value).strip() for value in (skill_ids or []) if str(value).strip()}
    if scope == "selected" and len(selected_ids) != 1:
        raise ValueError("优化当前技能时必须提供一个有效的Skill ID。")
    all_skills = list(list_skills())
    candidates = []
    for item in all_skills:
        if item.get("display_source") == "manual" and not overwrite_manual:
            continue
        if scope == "selected" and item["id"] not in selected_ids:
            continue
        if scope == "issues" and not item.get("needs_optimization"):
            continue
        candidates.append({
            "id": item["id"],
            "source_name": item.get("source_name") or item["id"],
            "current_name": item.get("display_name") or item["id"],
            "function_description": str(item.get("description") or "")[:500],
        })
    if not candidates:
        return {"requested": 0, "updated": 0, "usage": {}, "catalog": skill_catalog()}

    system = (
        "你是Skill界面命名整理器。必须根据每项的function_description概括技能真实用途，而不是只翻译ID或原名称。"
        "只优化用户可见的简体中文显示名称，不修改Skill ID、功能、触发条件或描述。"
        "名称应准确、简洁、便于普通用户理解，建议4到16个中文字符；可保留GPT、H3、Music等必要品牌词。"
        "所有名称彼此不得重复；不要包含方括号、Skill ID、文件名、路径、冒号结尾、宣传口号或功能说明句。"
        "每行只返回：skill-id、一个制表符、中文显示名。不得输出标题、解释、编号、Markdown或代码块。"
    )
    user = "请整理以下Skill显示名称：\n" + json.dumps(candidates, ensure_ascii=False, separators=(",", ":"))
    adapter = DapaoAPIChatAdapter(api_config)
    reply = adapter.complete(
        [{"role": "system", "content": system}, {"role": "user", "content": user}],
        {"max_tokens": min(4096, max(512, len(candidates) * 64)), "temperature": 0.1, "top_p": 0.9},
    )
    candidate_ids = [item["id"] for item in candidates]
    proposed = _skill_names_from_reply(reply, candidate_ids)
    reserved = {item["display_name"] for item in all_skills if item["id"] not in candidate_ids}
    cleaned = {}
    for skill_id in candidate_ids:
        name = proposed.get(skill_id)
        if name and name not in reserved:
            cleaned[skill_id] = name
            reserved.add(name)
    if not cleaned:
        raise RuntimeError("模型返回内容无法匹配任何Skill ID或中文显示名称；本次不会自动重试。")
    catalog = set_model_display_names(cleaned, overwrite_manual=overwrite_manual)
    return {
        "requested": len(candidates),
        "updated": len(cleaned),
        "usage": adapter.last_usage,
        "catalog": catalog,
    }


def _api_config(value) -> dict:
    if not isinstance(value, dict):
        raise ValueError("请连接“大炮API模型配置”节点。")
    api_key = str(value.get("api_key") or "").strip()
    model = str(value.get("model") or DEFAULT_LLM_MODEL)
    if not api_key:
        raise ValueError("请在“大炮API模型配置”节点填写 dapaoAI API 密钥。")
    if model not in LLM_MODEL_OPTIONS:
        raise ValueError(f"不支持的LLM映射模型：{model}")
    capability = LLM_MODEL_CAPABILITIES[model]
    requested_context = int(value.get("context_limit") or 0)
    context_limit = requested_context if requested_context > 0 else capability["context_limit"]
    return {
        "version": 1,
        "api_key": api_key,
        "model": model,
        "timeout": min(1200, max(30, int(value.get("timeout") or 300))),
        "context_limit": max(2048, context_limit),
        "max_output": int(capability["max_output"]),
        "supports_images": bool(capability["supports_images"]),
        "supports_video": bool(capability.get("supports_video", False)),
        "supports_audio": bool(capability.get("supports_audio", False)),
    }


def _material_aliases(raw) -> dict[str, str]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        value = raw
    else:
        text = str(raw).strip()
        try:
            value = json.loads(text or "{}")
        except json.JSONDecodeError:
            value = {}
            for line in text.splitlines():
                if not line.strip():
                    continue
                key, separator, label = line.partition("=")
                if not separator:
                    raise ValueError("素材别名格式错误，请使用 JSON，或每行填写“图片1=产品正面”。")
                value[key.strip()] = label.strip()
    if not isinstance(value, dict):
        raise ValueError("素材别名必须是JSON对象。")
    result = {}
    for key, label in value.items():
        normalized_key = str(key or "").strip().lstrip("@")
        normalized_label = str(label or "").strip().lstrip("@")
        if not normalized_key or not normalized_label:
            continue
        result[normalized_key] = normalized_label[:80]
    if len(set(result.values())) != len(result):
        raise ValueError("素材别名不能重复，否则@菜单无法区分。")
    return result


class DapaoAPIChatMaterialLibraryNode:
    CATEGORY = NODE_CATEGORY
    RETURN_TYPES = ("DAPAO_API_CHAT_MATERIAL_LIBRARY",)
    RETURN_NAMES = ("📦多轮对话素材库",)
    FUNCTION = "build_library"
    DESCRIPTION = "登记最多20图、5视频、5音频；仅被聊天框本轮@引用的素材才会在请求边界处理和发送。"

    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for index in range(1, 21):
            optional[f"🖼️图片{index}"] = ("IMAGE", {"tooltip": f"待引用图片{index}；每个接口请连接单张IMAGE。"})
        for index in range(1, 6):
            optional[f"🎞️视频{index}"] = ("VIDEO", {"tooltip": f"待引用视频{index}；只有聊天本轮@视频{index}时才抽帧/发送。"})
            optional[f"🎵音频{index}"] = ("AUDIO", {"tooltip": f"待引用音频{index}；只有聊天本轮@音频{index}时才压缩并发送。"})
        return {
            "required": {
                "🏷️素材别名": (
                    "STRING",
                    {
                        "default": "{}",
                        "multiline": True,
                        "tooltip": "可选。JSON示例：{\"图片1\":\"产品正面\",\"视频1\":\"开场镜头\"}。固定编号仍是内部稳定ID。",
                    },
                ),
            },
            "optional": optional,
        }

    def build_library(self, **kwargs):
        aliases = _material_aliases(kwargs.get("🏷️素材别名"))
        items = []
        specs = (("image", "图片", "🖼️图片", 20), ("video", "视频", "🎞️视频", 5), ("audio", "音频", "🎵音频", 5))
        for kind, chinese, prefix, limit in specs:
            for slot in range(1, limit + 1):
                value = kwargs.get(f"{prefix}{slot}")
                if value is None:
                    continue
                token = f"@{chinese}{slot}"
                if kind == "image":
                    if not hasattr(value, "shape") or len(value.shape) != 4:
                        raise ValueError(f"{token}必须连接ComfyUI IMAGE。")
                    if int(value.shape[0]) != 1:
                        raise ValueError(f"{token}当前包含{int(value.shape[0])}张图片；请先拆分批次，每个素材接口只接一张。")
                key = f"{chinese}{slot}"
                label = aliases.get(key, token)
                items.append({"kind": kind, "slot": slot, "token": token, "label": label, "value": value})
        return ({"version": 1, "items": items},)


def _auto_select_skill(adapter: DapaoAPIChatAdapter, skills: list[dict], text: str) -> str:
    if not skills:
        raise ValueError("Skill加载器没有发现可用 Skill，请把 Skill 放入本插件的 skills 文件夹。")
    catalogue = "\n".join(
        f'- {item["id"]}: {item["name"]}；{str(item.get("description") or "")[:500]}'
        for item in skills
    )
    raw = adapter.complete(
        [
            {"role": "system", "content": "根据用户任务选择唯一最匹配的 Skill。只输出 Skill ID，不解释，不添加标点。"},
            {"role": "user", "content": f"可用 Skills：\n{catalogue}\n\n用户任务：\n{text}"},
        ],
        {"max_tokens": 80, "temperature": 0.0, "top_p": 1.0, "top_k": 20},
    )
    selected = clean_reply(raw).strip().strip("`'\".,，。 ")
    valid_ids = {str(item.get("id") or "") for item in skills}
    if selected in valid_ids:
        return selected
    for skill_id in valid_ids:
        if skill_id and skill_id in selected:
            return skill_id
    raise ValueError(f"自动选择 Skill 失败，模型返回：{selected[:120]}。请在 Skill加载器中手动选择后重试。")


def _pick_skill(adapter, config, text: str, previous_id: str = ""):
    if not isinstance(config, dict):
        return None
    skills = config.get("skills")
    if not isinstance(skills, list):
        skills = list(list_skills())
    selected = str(config.get("selected") or "") or previous_id
    if selected:
        skill = get_skill(selected)
        if not skill:
            raise ValueError(f"当前 Skill 不存在：{selected}。请刷新 Skill加载器后重试。")
        return skill
    return get_skill(_auto_select_skill(adapter, skills, text))


class DapaoAPILLMConfigNode:
    CATEGORY = NODE_CATEGORY
    RETURN_TYPES = ("DAPAO_API_LLM_CONFIG",)
    RETURN_NAMES = ("🤖API模型",)
    FUNCTION = "build_config"
    DESCRIPTION = "配置 dapaoAI 多轮聊天使用的映射模型、密钥、超时与上下文预算。"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "🔑 API密钥": ("STRING", {
                "default": "",
                "placeholder": "填入 dapaoAI API 密钥",
                "tooltip": "仅发送到 https://api.dapaoai.com，不会写入聊天历史或 Skill。",
            }),
            "🤖 LLM模型": (list(LLM_MODEL_OPTIONS), {"default": DEFAULT_LLM_MODEL}),
            "📚 上下文上限": ("INT", {
                "default": 0,
                "min": 0,
                "max": 1_048_576,
                "step": 1024,
                "tooltip": "0=使用节点内置的保守模型能力值；仅用于本地裁剪与圆环显示。",
            }),
            "⌛ 请求超时": ("INT", {"default": 300, "min": 30, "max": 1200, "step": 10}),
        }}

    def build_config(self, **kwargs):
        model = str(kwargs.get("🤖 LLM模型") or DEFAULT_LLM_MODEL)
        if model not in LLM_MODEL_OPTIONS:
            raise ValueError(f"不支持的LLM映射模型：{model}")
        return ({
            "version": 1,
            "api_key": str(kwargs.get("🔑 API密钥") or "").strip(),
            "model": model,
            "context_limit": int(kwargs.get("📚 上下文上限") or 0),
            "timeout": int(kwargs.get("⌛ 请求超时") or 300),
        },)


class DapaoAPIChatSettingsNode:
    CATEGORY = NODE_CATEGORY
    RETURN_TYPES = ("DAPAO_API_CHAT_SETTINGS",)
    RETURN_NAMES = ("⚙️对话设置",)
    FUNCTION = "build_settings"
    DESCRIPTION = "多轮历史、生成参数、think显示与2K图片预处理设置。"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "📝 系统提示词": ("STRING", {"default": "", "multiline": True, "placeholder": "可选。连接 Skill 时由 Skill 负责系统规则。"}),
            "🔢 最大历史轮数": ("INT", {"default": 100, "min": 1, "max": 100, "step": 1}),
            "📤 最大生成token": ("INT", {"default": 4096, "min": 20, "max": 65536, "step": 1}),
            "🌡️ 温度": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01}),
            "🎯 top_p": ("FLOAT", {"default": 0.9, "min": 0.0, "max": 1.0, "step": 0.01}),
            "🔝 top_k": ("INT", {"default": 20, "min": 0, "max": 200, "step": 1, "tooltip": "默认20时不发送；修改后仅支持top_k的映射模型生效。"}),
            "🔁 重复惩罚": ("FLOAT", {"default": 1.0, "min": 0.5, "max": 2.0, "step": 0.01, "tooltip": "默认1.0时不发送；修改后仅支持repeat_penalty的映射模型生效。"}),
            "📈 频率惩罚": ("FLOAT", {"default": 0.0, "min": -2.0, "max": 2.0, "step": 0.01}),
            "📍 存在惩罚": ("FLOAT", {"default": 0.0, "min": -2.0, "max": 2.0, "step": 0.01}),
            "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF, "control_after_generate": True, "tooltip": "控制ComfyUI缓存，不发送给LLM。"}),
            "🧠 输出think块": ("BOOLEAN", {"default": False}),
            "📐 图片最大边长": ("INT", {"default": 2048, "min": 128, "max": 2048, "step": 64, "tooltip": "每张图片在真实API请求边界逐张Lanczos缩放并以PNG发送；默认2K。"}),
        }}

    def build_settings(self, **kwargs):
        return ({
            "系统提示词": str(kwargs.get("📝 系统提示词") or ""),
            "最大历史轮数": int(kwargs.get("🔢 最大历史轮数", 100)),
            "最大生成token": int(kwargs.get("📤 最大生成token", 4096)),
            "温度": float(kwargs.get("🌡️ 温度", 0.7)),
            "top_p": float(kwargs.get("🎯 top_p", 0.9)),
            "top_k": int(kwargs.get("🔝 top_k", 20)),
            "重复惩罚": float(kwargs.get("🔁 重复惩罚", 1.0)),
            "频率惩罚": float(kwargs.get("📈 频率惩罚", 0.0)),
            "存在惩罚": float(kwargs.get("📍 存在惩罚", 0.0)),
            "seed": int(kwargs.get("🎲 随机种", 0)),
            "输出think块": bool(kwargs.get("🧠 输出think块", False)),
            "最大边长": min(2048, max(128, int(kwargs.get("📐 图片最大边长", 2048)))),
        },)


class DapaoAPISkillLoaderNode:
    CATEGORY = NODE_CATEGORY
    RETURN_TYPES = ("DAPAO_API_SKILL_CONFIG",)
    RETURN_NAMES = ("🧩Skill配置",)
    FUNCTION = "load_skill"
    DESCRIPTION = "扫描、安装和管理API插件Skills；支持稳定ID选择、手动显示名和连接上游模型一键优化名称。"

    @classmethod
    def INPUT_TYPES(cls):
        skills = list_skills()
        choices = ["自动选择"] + [item["label"] for item in skills]
        return {
            "required": {"🧩 Skill选择": (choices, {
                "default": "自动选择",
                "tooltip": "自动选择会额外调用一次当前API模型进行确定性路由；手动选择可避免这次调用。Skill按需读取references时还可能进行一次明确的二阶段调用。",
            })},
            "optional": {
                "🤖API模型": ("DAPAO_API_LLM_CONFIG", {
                    "tooltip": "仅供“AI优化Skill显示名”按钮使用；不连接也可手动改名和上传Skill。",
                }),
            },
        }

    def load_skill(self, **kwargs):
        selected = str(kwargs.get("🧩 Skill选择") or "自动选择")
        selected_id = resolve_skill_id(selected)
        skills = list(list_skills())
        if selected not in ("自动选择", "自动匹配"):
            if not selected_id:
                raise ValueError("所选 Skill 不存在，请刷新节点后重试。")
        return ({"selected": selected_id, "skills": skills, "version": 1},)


class DapaoAPIMultiTurnChatNode:
    CATEGORY = NODE_CATEGORY
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💬助手回复", "📚会话历史JSON", "🧩Skill最终结果")
    FUNCTION = "chat"
    OUTPUT_NODE = True
    DESCRIPTION = "dapaoAI多轮对话工作台：支持Skill、历史和@素材库；素材仅在本轮明确@时处理并发送。"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🤖API模型": ("DAPAO_API_LLM_CONFIG",),
                "💬本轮消息": ("STRING", {"default": "", "multiline": True}),
                "📚会话历史": ("STRING", {"default": "[]", "multiline": True}),
                "🖼️图片引用": ("STRING", {"default": "[]", "multiline": True}),
                "🧩流程状态": ("STRING", {"default": "{}", "multiline": True}),
                "🧩选项": ("STRING", {"default": "[]", "multiline": True}),
                "🆔请求标识": ("STRING", {"default": ""}),
                "🧭执行动作": ("STRING", {"default": "chat"}),
            },
            "optional": {
                "⚙️对话设置": ("DAPAO_API_CHAT_SETTINGS",),
                "🧩Skill配置": ("DAPAO_API_SKILL_CONFIG",),
                "📦素材库": ("DAPAO_API_CHAT_MATERIAL_LIBRARY",),
            },
            "hidden": {"unique_id": "UNIQUE_ID"},
        }

    async def chat(self, **kwargs):
        return await asyncio.to_thread(self._chat_sync, **kwargs)

    def _chat_sync(self, **kwargs):
        display_history = normalize_history(kwargs.get("📚会话历史", "[]"))
        user_text = str(kwargs.get("💬本轮消息") or "").strip()
        state = normalize_state(kwargs.get("🧩流程状态", "{}"))
        flow_before = {**state, "loaded_references": list(state["loaded_references"])}
        action = str(kwargs.get("🧭执行动作") or "chat").strip().lower()
        if action == "publish_final":
            reply = _latest_assistant_reply(display_history)
            raw_options = kwargs.get("🧩选项", "[]")
            try:
                raw_options = json.loads(raw_options) if isinstance(raw_options, str) else raw_options
            except json.JSONDecodeError:
                raw_options = []
            options = [str(item)[:240] for item in raw_options[:6] if str(item).strip()] if isinstance(raw_options, list) else []
            return self._result(display_history, reply, state, options, False, {})

        current_images = normalize_image_refs(kwargs.get("🖼️图片引用", "[]"))
        if not user_text and current_images:
            user_text = "请分析上传的图片，并根据当前对话或Skill继续处理。"
        if not user_text:
            return self._result(display_history, _latest_assistant_reply(display_history), state, [], False, {})

        config = _api_config(kwargs.get("🤖API模型"))
        settings = kwargs.get("⚙️对话设置") or {}
        settings = settings if isinstance(settings, dict) else {}
        max_rounds = min(100, max(1, int(settings.get("最大历史轮数", 100))))
        max_tokens = int(settings.get("最大生成token", 4096))
        max_edge = min(2048, max(128, int(settings.get("最大边长", 2048))))
        system_base = str(settings.get("系统提示词") or "")
        if current_images and not config["supports_images"]:
            raise RuntimeError(f"当前映射模型 {config['model']} 不支持图片输入，请切换多模态模型。")
        selected_materials = select_material_mentions(user_text, kwargs.get("📦素材库"))
        if any(item["kind"] == "image" for item in selected_materials) and not config["supports_images"]:
            raise RuntimeError(f"当前映射模型 {config['model']} 不支持图片输入，请切换多模态模型。")
        current_content, material_stats = current_message_content(
            user_text,
            current_images,
            selected_materials,
            max_edge,
            config,
        )
        media_image_equivalents = (
            int(material_stats["image_parts"])
            + int(material_stats["video_frames"])
            + (1 if material_stats["audio_seconds"] else 0)
        )

        adapter = DapaoAPIChatAdapter(config)
        skill_config = kwargs.get("🧩Skill配置")
        selected_skill = str(skill_config.get("selected") or "") if isinstance(skill_config, dict) else ""
        if selected_skill and state.get("skill") and selected_skill != state["skill"]:
            state = normalize_state({"context_cutoff": state.get("context_cutoff", 0)})
        skill = _pick_skill(adapter, skill_config, user_text, state.get("skill", ""))
        if skill:
            state["skill"], state["skill_name"] = skill["id"], skill["name"]
            system = build_skill_prompt(system_base, skill, state)
        else:
            system = system_base or "你是一个专业、友好、准确的AI助手。"

        cutoff = int(state.get("context_cutoff") or 0)
        context_history = [
            item for item in display_history
            if not cutoff or int(item.get("created_at", -1)) > cutoff
        ][-max_rounds * 2 :]
        context_history, budget, estimated_input, output_reserve, trimmed_messages = trim_history(
            context_history,
            system,
            user_text,
            max_tokens,
            config["context_limit"],
            config["max_output"],
            media_image_equivalents,
        )
        params = {
            "max_tokens": output_reserve,
            "temperature": float(settings.get("温度", 0.7)),
            "top_p": float(settings.get("top_p", 0.9)),
            "top_k": int(settings.get("top_k", 20)),
            "repeat_penalty": float(settings.get("重复惩罚", 1.0)),
            "frequency_penalty": float(settings.get("频率惩罚", 0.0)),
            "presence_penalty": float(settings.get("存在惩罚", 0.0)),
        }

        def make_messages():
            messages = ([{"role": "system", "content": system}] if system else []) + api_messages(context_history, max_edge)
            messages.append({"role": "user", "content": current_content})
            return messages

        reply = ""
        skill_state = {}
        options: list[str] = []
        for attempt in range(2):
            raw = adapter.complete(make_messages(), params)
            cleaned = raw if bool(settings.get("输出think块", False)) else clean_reply(raw)
            reply, skill_state = parse_skill_reply(cleaned.lstrip().removeprefix(": ").strip())
            if not skill:
                break
            requested = [
                path
                for path in skill_state.get("load_references", [])
                if isinstance(path, str)
                and path in skill["references"]
                and path not in state["loaded_references"]
            ]
            if requested and attempt == 0:
                state["loaded_references"].extend(requested)
                system = build_skill_prompt(system_base, skill, state)
                context_history, budget, estimated_input, output_reserve, trimmed_messages = trim_history(
                    context_history,
                    system,
                    user_text,
                    max_tokens,
                    config["context_limit"],
                    config["max_output"],
                    media_image_equivalents,
                )
                params["max_tokens"] = output_reserve
                continue
            state["stage"] = str(skill_state.get("stage") or "进行中")[:80]
            raw_options = skill_state.get("options")
            options = [str(item)[:240] for item in raw_options[:6] if str(item).strip()] if isinstance(raw_options, list) else []
            if skill_state.get("final"):
                state["final_result"] = reply
            break

        created_at = _request_time(kwargs.get("🆔请求标识"))
        user_tokens = estimate_text_tokens(user_text) + 8 + media_image_equivalents * 1536
        assistant_tokens = adapter.last_usage["completion_tokens"] or estimate_text_tokens(reply) + 8
        user_message = {
            "role": "user",
            "content": user_text,
            "token_count": user_tokens,
            "created_at": created_at,
            **({"images": current_images} if current_images else {}),
            **({
                "materials": [
                    {key: item[key] for key in ("kind", "slot", "token", "label")}
                    for item in selected_materials
                ]
            } if selected_materials else {}),
        }
        assistant_message = {
            "role": "assistant",
            "content": reply,
            "token_count": assistant_tokens,
            "created_at": int(time.time() * 1000),
            "flow_before": flow_before,
            "usage": {
                **adapter.usage_totals,
                "calls": adapter.calls,
                "source": "api" if adapter.usage_totals["total_tokens"] else "estimated",
                **({
                    "cost": round(adapter.total_cost, 8),
                    "currency": adapter.cost_currency,
                } if adapter.has_cost else {}),
            },
        }
        display_history.extend((user_message, assistant_message))
        actual_prompt = adapter.last_usage["prompt_tokens"] or estimated_input
        conversation_used = min(config["context_limit"], actual_prompt + assistant_tokens)
        context = {
            "used_tokens": conversation_used,
            "input_used_tokens": actual_prompt,
            "assistant_tokens": assistant_tokens,
            "prompt_budget": budget,
            "context_limit": config["context_limit"],
            "output_reserve": output_reserve,
            "requested_output": max_tokens,
            "output_auto_adjusted": output_reserve < max_tokens,
            "remaining_tokens": max(0, budget - actual_prompt),
            "input_remaining_tokens": max(0, budget - actual_prompt),
            "total_remaining_tokens": max(0, config["context_limit"] - conversation_used),
            "percent": round(conversation_used / max(1, config["context_limit"]) * 100, 1),
            "input_percent": round(actual_prompt / max(1, budget) * 100, 1),
            "current_rounds": sum(item["role"] == "user" for item in context_history) + 1,
            "max_rounds": max_rounds,
            "trimmed_messages": trimmed_messages,
            "usage_source": "api" if adapter.last_usage["prompt_tokens"] else "estimated",
            "api_calls": adapter.calls,
            "billed_tokens": adapter.billed_tokens,
            "round_prompt_tokens": adapter.usage_totals["prompt_tokens"],
            "round_completion_tokens": adapter.usage_totals["completion_tokens"],
            "round_total_tokens": adapter.usage_totals["total_tokens"],
            "round_cost": round(adapter.total_cost, 8) if adapter.has_cost else None,
            "cost_currency": adapter.cost_currency,
            "cost_source": "api" if adapter.has_cost else "unavailable",
            "model": config["model"],
            "material_count": len(selected_materials),
            "material_image_parts": int(material_stats["image_parts"]),
            "material_video_frames": int(material_stats["video_frames"]),
            "material_audio_seconds": round(float(material_stats["audio_seconds"]), 3),
        }
        return self._result(display_history, reply, state, options, True, context)

    @staticmethod
    def _result(history, reply, state, options, sent, context):
        history_json = json.dumps(history, ensure_ascii=False, separators=(",", ":"))
        final_result = str(state.get("final_result") or reply or "")
        return {
            "ui": {
                "📚会话历史": [history_json],
                "💬助手回复": [reply],
                "🧩流程状态": [json.dumps(state, ensure_ascii=False, separators=(",", ":"))],
                "🧩选项": [json.dumps(options, ensure_ascii=False)],
                "📊上下文": [json.dumps(context, ensure_ascii=False)],
                "✅已发送": [bool(sent)],
            },
            "result": (reply, history_json, final_result),
        }


NODE_CLASS_MAPPINGS = {
    "DapaoAPIChatMaterialLibraryNode": DapaoAPIChatMaterialLibraryNode,
    "DapaoAPILLMConfigNode": DapaoAPILLMConfigNode,
    "DapaoAPIChatSettingsNode": DapaoAPIChatSettingsNode,
    "DapaoAPISkillLoaderNode": DapaoAPISkillLoaderNode,
    "DapaoAPIMultiTurnChatNode": DapaoAPIMultiTurnChatNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoAPIChatMaterialLibraryNode": "📦大炮API多轮对话素材库@炮老师的小课堂",
    "DapaoAPILLMConfigNode": "🤖大炮API模型配置@炮老师的小课堂",
    "DapaoAPIChatSettingsNode": "⚙️API对话增强设置@炮老师的小课堂",
    "DapaoAPISkillLoaderNode": "🧩大炮API Skill加载器@炮老师的小课堂",
    "DapaoAPIMultiTurnChatNode": "💬大炮API多轮对话@炮老师的小课堂",
}


__all__ = [
    "DapaoAPIChatAdapter",
    "DapaoAPIChatMaterialLibraryNode",
    "DapaoAPIChatSettingsNode",
    "DapaoAPILLMConfigNode",
    "DapaoAPIMultiTurnChatNode",
    "DapaoAPISkillLoaderNode",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
