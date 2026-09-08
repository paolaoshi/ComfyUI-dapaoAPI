"""Three guided drama nodes, backed by eleven compatible advanced stages/tools."""
from __future__ import annotations

import asyncio
import json
import os
import re
import time

from .dreambrush_runtime import submit_json_task
from .gpt_llm_chat_node import DapaoGPTLLMAPIError, _extract_text
from .llm_model_options import DEFAULT_LLM_MODEL, LLM_MODEL_OPTIONS, LLM_MODEL_CAPABILITIES
from .short_drama_suite import (
    BUNDLE_TYPE, CATEGORY, CONTRACT, DEPENDENCIES, DIALECTS, DOC_NAMES, REQUIRED, SKILLS,
    check_document, clone_bundle, digest, extract_prompts, merge_bundles, new_bundle,
    put_doc, reference_options, skill_context, stale_docs, source_pieces,
    field, document_advisories, repair_video_reference_bindings, next_episode_bundle,
)


def safe_text(value, secret=""):
    text = str(value)
    if secret:
        text = text.replace(secret, "<密钥已隐藏>")
    text = re.sub(r"(?i)\bsk-[A-Za-z0-9_-]{8,}", "<密钥已隐藏>", text)
    return re.sub(r"(?i)\bBearer\s+[^\s\"',;]+", "Bearer <密钥已隐藏>", text)


class DapaoDramaProject:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "📛 项目名称": ("STRING", {"default": "我的漫剧"}),
            "📝 创作简报": ("STRING", {"default": "", "multiline": True}),
            "🎞️ 当前集号": ("INT", {"default": 1, "min": 1, "max": 9999}),
            "📚 计划集数": ("INT", {"default": 1, "min": 1, "max": 9999}),
            "⏱️ 单集目标秒数": ("INT", {"default": 60, "min": 5, "max": 3600}),
            "🎨 制作形态": (["二维动态漫剧", "三维动画", "静态漫剧", "水墨国漫", "Q版动画", "真人短剧"],),
            "🖌️ 视觉风格": ("STRING", {"default": "遵循创作要求", "multiline": True}),
            "📐 画幅比例": (["9:16", "16:9", "1:1", "4:3"],),
            "🌐 提示词语言": (["简体中文", "英文"],),
            "🎬 视频提示词方言": (list(DIALECTS),),
            "🖼️ 参考方式": (["挂图计划（自行出图）", "明确文生视频"],),
            "⏳ 单镜最短秒数": ("INT", {"default": 0, "min": 0, "max": 120, "tooltip": "0表示未指定模型限制；以你使用的模型实际能力填写。"}),
            "⌛ 单镜最长秒数": ("INT", {"default": 0, "min": 0, "max": 120}),
        }, "optional": {
            "📂 已有文档类型": (list(DOC_NAMES.values()), {"default": "剧本.md"}),
            "📄 已有文档": ("STRING", {"default": "", "multiline": True}),
        }}

    CATEGORY = CATEGORY
    FUNCTION = "build"
    RETURN_TYPES = (BUNDLE_TYPE, "STRING")
    RETURN_NAMES = ("📦 漫剧资料包", "🧭 流程说明")
    DESCRIPTION = "short-drama：本地设置集号、形态、风格和方言；可导入现成剧本/视觉设定/分镜直接进入对应阶段。无API调用。"

    def build(self, **kw):
        return self._build_sync(**kw)

    def _build_sync(self, **kw):
        cfg = {"title": kw.get("📛 项目名称", "我的漫剧"), "brief": kw.get("📝 创作简报", ""),
            "episode": f"EP{int(kw.get('🎞️ 当前集号', 1)):03d}", "episodes": int(kw.get("📚 计划集数", 1)),
            "seconds": int(kw.get("⏱️ 单集目标秒数", 60)), "form": kw.get("🎨 制作形态", "二维动态漫剧"),
            "style": kw.get("🖌️ 视觉风格", "遵循创作要求"), "ratio": kw.get("📐 画幅比例", "9:16"),
            "prompt_language": kw.get("🌐 提示词语言", "简体中文"), "dialect": kw.get("🎬 视频提示词方言", "通用"),
            "reference_mode": kw.get("🖼️ 参考方式", "挂图计划（自行出图）"),
            "shot_min": int(kw.get("⏳ 单镜最短秒数", 0)), "shot_max": int(kw.get("⌛ 单镜最长秒数", 0))}
        if cfg["shot_max"] and cfg["shot_min"] > cfg["shot_max"]:
            raise ValueError("单镜最短秒数不能大于最长秒数。")
        if int(kw.get("🎞️ 当前集号", 1)) > cfg["episodes"]:
            raise ValueError("当前集号不能超过计划集数。")
        bundle = new_bundle(cfg)
        imported = str(kw.get("📄 已有文档", "")).strip()
        if imported:
            key = next(k for k, v in DOC_NAMES.items() if v == kw.get("📂 已有文档类型", "剧本.md"))
            put_doc(bundle, key, imported)
        summary = (f"{cfg['title']} · {cfg['episode']} · {cfg['ratio']} · {cfg['form']}\n"
            "可选原著分析/系列开发 → 剧本 → 视觉设定\n"
            "视觉设定 → 资产图片提示词；剧本＋视觉设定 → 分镜关键帧 → 视频提示词\n"
            "两支资料合流 → 可选审查 → 提示词交付整理。静态漫剧可跳过视频。\n"
            "挂图计划仅说明将来如何使用图片；本套组不生成媒体。")
        return bundle, summary


class DramaStage:
    STAGE = "write"
    CATEGORY = CATEGORY
    FUNCTION = "generate"
    RETURN_TYPES = (BUNDLE_TYPE, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("📦 漫剧资料包", "📄 阶段文档", "🧩 提示词列表", "ℹ️ 处理信息")
    OUTPUT_IS_LIST = (False, False, True, False)

    @classmethod
    def INPUT_TYPES(cls):
        required = {
            "🔑 API密钥": ("STRING", {"default": "", "password": True,
                "tooltip": "留空可读取DAPAO_API_KEY环境变量；普通工作流可能保存明文输入，分享前请移除。"}),
            "🤖 LLM模型": (list(LLM_MODEL_OPTIONS), {"default": DEFAULT_LLM_MODEL}),
            "📝 本阶段要求": ("STRING", {"default": "", "multiline": True,
                "placeholder": "具体创作或修订要求；项目简报及已连接文档会自动继承。"}),
            "📚 专项参考": (reference_options(cls.STAGE),),
            "🌡️ 温度": ("FLOAT", {"default": 0.6, "min": 0, "max": 2, "step": 0.05}),
            "📝 最大输出令牌": ("INT", {"default": 16384, "min": 1024, "max": 65536, "step": 1024}),
            "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                "control_after_generate": "fixed", "tooltip": "固定种用于缓存与48小时内恢复同一LLM请求；修改种或内容才重新创作。"}),
            "⌛ 请求超时": ("INT", {"default": 600, "min": 30, "max": 1800}),
        }
        optional = {"📦 上游资料": (BUNDLE_TYPE,),
                    "📄 原文或现有稿": ("STRING", {"default": "", "multiline": True})}
        for stage in DEPENDENCIES[cls.STAGE]:
            optional[f"📄 {DOC_NAMES[stage]}"] = ("STRING", {"forceInput": True})
        if cls.STAGE in {"storyboard", "video"}:
            optional["📄 图片提示词.md"] = ("STRING", {"forceInput": True})
        if cls.STAGE == "novel":
            required.update({
                "🔍 分析方式": (["当前材料分析", "抽样快评", "全文分段分析"],),
                "🗂️ 原著分段依据": (["自动识别章节（无标题按字符）", "按字符分段"],),
                "📏 每段字符数": ("INT", {"default": 12000, "min": 2000, "max": 24000, "step": 1000}),
                "🧮 最大分析段数": ("INT", {"default": 16, "min": 1, "max": 128,
                    "tooltip": "抽样时为采样数；全文超过上限会在请求前停止。每段一次LLM，另加汇总；超长提取会逐级汇总，增加请求次数。"}),
            })
        return {"required": required, "optional": optional}

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kw):
        secret = str(kw.get("🔑 API密钥") or os.environ.get("DAPAO_API_KEY", "")).strip()
        try:
            return self._run(kw, secret)
        except Exception as error:
            raise RuntimeError(f"漫剧{DOC_NAMES[self.STAGE]}处理失败：{safe_text(error, secret)}\n未自动重试付费请求。") from None

    def _run(self, kw, secret):
        started = time.monotonic()
        model = kw.get("🤖 LLM模型", DEFAULT_LLM_MODEL)
        if not secret:
            raise ValueError("请填写API密钥，或设置DAPAO_API_KEY环境变量。")
        if model not in LLM_MODEL_OPTIONS:
            raise ValueError("LLM模型不在项目统一候选列表中。")
        bundle = clone_bundle(kw.get("📦 上游资料"))
        for key, label in DOC_NAMES.items():
            text = str(kw.get(f"📄 {label}", "")).strip()
            if text:
                put_doc(bundle, key, text)
        requirements = str(kw.get("📝 本阶段要求", "")).strip()
        raw = str(kw.get("📄 原文或现有稿", "")).strip()
        sources = [k for k in DEPENDENCIES[self.STAGE] if k in bundle["docs"]]
        if self.STAGE in {"storyboard", "video"} and "image" in bundle["docs"]:
            sources.append("image")
        for key in REQUIRED.get(self.STAGE, ()):
            if key not in bundle["docs"] or not bundle["docs"][key]["text"].strip():
                raise ValueError(f"缺少{DOC_NAMES[key]}；可连接上游资料包或直接接入该文档文本。")
        if self.STAGE != "review":
            stale = stale_docs(bundle) & set(sources)
            invalid = [k for k in sources if check_document(k, bundle["docs"][k]["text"], bundle)]
            if stale or invalid:
                raise ValueError("上游文档过期或结构检查未通过：" + "、".join(DOC_NAMES[k] for k in sorted(stale | set(invalid))))
        if not (requirements or raw or sources or bundle["config"].get("brief")):
            raise ValueError("请提供创作简报、原文、现有稿或上游资料。")
        if self.STAGE == "novel" and not raw:
            raise ValueError("原著分析需要实际正文，请填入原文或现有稿；不能只按书名推测。")
        system = CONTRACT + f"\n当前唯一阶段：{SKILLS[self.STAGE]} → {DOC_NAMES[self.STAGE]}\n"
        system += skill_context(self.STAGE, kw.get("📚 专项参考", "自动精选"), bundle["config"]["dialect"])
        context = {"项目设置": bundle["config"], "本阶段要求": requirements,
                   "上游文档": {DOC_NAMES[k]: bundle["docs"][k]["text"].split("\n\n# 原文分段提取（可追溯依据）\n")[0] if k == "novel" else bundle["docs"][k]["text"] for k in sources},
                   "现有本阶段文档": bundle["docs"].get(self.STAGE, {}).get("text", "")}
        if bundle.get("episode_history"):
            history = bundle["episode_history"]
            last = history[-1]
            context["跨集连续性"] = {
                "系列固定视觉基准": bundle.get("series_baseline", {}),
                "前集": last["episode"],
                "前集文档": {DOC_NAMES[k]: v["text"] for k, v in last["docs"].items()
                             if k in {"write", "assets", "image", "storyboard"}},
                "更早各集剧情": {e["episode"]: e["docs"]["write"]["text"] for e in history[:-1]},
                "更早各集视觉资产": {e["episode"]: {DOC_NAMES[k]: v["text"] for k,v in e["docs"].items() if k in {"assets", "image"}} for e in history[:-1]},
            }
            system += ("\n跨集模式：旧集文档是已发生事实，不得当作当前集重写。继承已确认身份、外貌、服装、场景布局、道具和知情状态。"
                "未揭晓的身份及伏笔不可无依据改成既定事实；有意变化须写明前态、后态、原因、来源集/场及生效范围。"
                "剧本末尾增加‘## 集间交接’，列出本集结束位置、人物知情/关系、可见状态、持物、未解伏笔与下一集进入条件。"
                "视觉设定增加‘## 跨集资产变化’，按复用/新增/有依据的变体列明人物、场景、道具；复用项保持原身份锚点，只有声音不出镜者不建外貌。"
                "已有IMG资产必须兼容原提示词：不得给它追加原提示词未包含的逐字连续性锁；新状态只约束本集镜头，图片提示词项写无，或为确有变化的资产另建本集变体编号。未确认的外貌细节不能声称已在前集确定。"
                "图片阶段保留复用资产的原IMG编号和原提示词，补充新资产/必要变体。分镜和视频必须承接前集末状态；审查时检查跨集矛盾并引用证据。")
        if self.STAGE in {"storyboard", "video"} and bundle.get("timing_plan"):
            context["手动分段时长（秒，优先于项目原目标时长）"] = bundle["timing_plan"]
            context["本轮总时长（秒）"] = sum(bundle["timing_plan"])
        if self.STAGE == "review":
            context["机械检查"] = {DOC_NAMES[k]: check_document(k, r["text"], bundle) for k, r in bundle["docs"].items()}
            context["过期文档"] = [DOC_NAMES[k] for k in sorted(stale_docs(bundle))]
        usage = []

        def payload_for(user, max_output=None):
            payload = {"model": model, "messages": [{"role": "system", "content": system},
                {"role": "user", "content": json.dumps(user, ensure_ascii=False)}],
                "temperature": float(kw.get("🌡️ 温度", 0.6)), "max_tokens": max_output or int(kw.get("📝 最大输出令牌", 16384))}
            # V4 defaults to thinking; its reasoning can consume the entire
            # output budget before any deliverable text. These document stages
            # use the documented non-thinking mode rather than hiding reasoning.
            if model in {"deepseek-v4-flash", "deepseek-v4-pro"}:
                payload["thinking"] = {"type": "disabled"}
            return payload

        def fits(user, max_output=None):
            payload = payload_for(user, max_output)
            return len(json.dumps(payload, ensure_ascii=False).encode()) + payload["max_tokens"] <= LLM_MODEL_CAPABILITIES[model]["context_limit"]

        def call(user, suffix="", max_output=None):
            payload = payload_for(user, max_output)
            # UTF-8 byte count is intentionally conservative; never truncate source silently.
            if not fits(user, max_output):
                raise ValueError("输入与技能参考超过当前模型的保守上下文预算。请减少专项参考、分集/分段处理，或选择更大上下文模型；内容未截断。")
            result = submit_json_task(api_key=secret, endpoint="/v1/chat/completions", payload=payload,
                timeout=int(kw.get("⌛ 请求超时", 600)), error_factory=DapaoGPTLLMAPIError,
                user_agent="ComfyUI-dapaoAPI/ShortDrama", reuse_succeeded=True,
                recovery_salt=f"drama:{self.STAGE}:{kw.get('🎲 随机种', 0)}:{suffix}")
            choices = result.get("choices") or []
            if choices and choices[0].get("finish_reason") == "length":
                if not str(choices[0].get("message", {}).get("content") or "").strip():
                    raise ValueError("模型耗尽输出预算但未返回正文（可能被内部思考占用）。请确认渠道支持该模型的非思考参数；不要将思考内容当作提示词交付。")
                raise ValueError("LLM输出被截断。请提高最大输出令牌或缩小本集范围；原响应已保存在本地恢复记录。")
            text = safe_text(_extract_text(result), secret).strip()
            if text.startswith("```") and text.endswith("```"):
                text = "\n".join(text.splitlines()[1:-1]).strip()
            if not text:
                raise ValueError("LLM未返回文档正文。")
            usage.append(result.get("usage") or {})
            return text

        if self.STAGE == "novel" and kw.get("🔍 分析方式", "当前材料分析") != "当前材料分析":
            size = int(kw.get("📏 每段字符数", 12000))
            limit = int(kw.get("🧮 最大分析段数", 16))
            if not 2000 <= size <= 24000 or not 1 <= limit <= 128:
                raise ValueError("原著分段参数无效。")
            pieces = source_pieces(raw, size, kw.get("🗂️ 原著分段依据") != "按字符分段")
            sampling = kw["🔍 分析方式"] == "抽样快评"
            if not sampling and len(pieces) > limit:
                raise ValueError(f"全文共有{len(pieces)}段，超过设定的{limit}段；请提高上限或明确分批范围。尚未请求LLM。")
            selected = list(range(len(pieces)))
            if sampling and len(selected) > limit:
                selected = sorted({round(i * (len(pieces) - 1) / (limit - 1)) for i in range(limit)}) if limit > 1 else [0]
            extracts = []
            for index in selected:
                offset, piece = pieces[index]
                extracts.append({"字符范围": [offset + 1, offset + len(piece)],
                    "提取": call({**context, "本次任务": "仅提取此片段功能、实体候选、冲突、进入/退出状态与证据；不要声称已分析全书。引用使用给定字符范围，跨段未完成事件标为未决。",
                                 "字符范围": [offset + 1, offset + len(piece)], "原文": piece}, f"part-{index}", min(4096, int(kw.get("📝 最大输出令牌", 16384))))})
            coverage = sum(len(pieces[i][1]) for i in selected) / len(raw)
            synthesis = {**context, "本次任务": "汇总已有提取为改编价值、剧情单元、节奏情绪、人物设定候选和分集建议；不编造未读范围，抽样不算全书分析。",
                         "覆盖率": coverage, "总段数": len(pieces), "已读段": selected}
            summaries = extracts
            level = 0
            while not fits({**synthesis, "片段提取": summaries}):
                level += 1
                if len(summaries) < 2 or level > 10:
                    raise ValueError("汇总上下文仍过长；请缩小材料范围。已完成片段的响应保存在恢复记录，同输入和种重跑会复用。")
                merged = []
                for offset in range(0, len(summaries), 2):
                    group = summaries[offset:offset+2]
                    summary = call({**synthesis, "本次任务": "压缩这组提取但保留所有来源字符范围、剧情因果、实体候选和未决缺口；不补原文未读内容。用紧凑Markdown，不超过1000汉字。", "片段提取": group}, f"reduce-{level}-{offset}", 4096)
                    merged.append({"提取": summary})
                summaries = merged
            document = call({**synthesis, "片段提取": summaries}, "synthesis")
            document = (f"<!-- 原文SHA256：{digest(raw)} -->\n"
                        f"- 本次实际覆盖：{len(selected)}/{len(pieces)}段，{coverage:.1%}字符；方式：{kw['🔍 分析方式']}\n\n" + document
                        + "\n\n# 原文分段提取（可追溯依据）\n" + "\n\n".join(
                            f"## 字符{e['字符范围'][0]}–{e['字符范围'][1]}\n{e['提取']}" for e in extracts))
        else:
            document = call({**context, "原文或现有稿": raw})
        repairs = []
        if self.STAGE == "video":
            document, repairs = repair_video_reference_bindings(document, bundle)
        issues = check_document(self.STAGE, document, bundle)
        put_doc(bundle, self.STAGE, document, sources, issues)
        if repairs:
            bundle["docs"][self.STAGE]["binding_repairs"] = repairs
        prompts = [p["prompt"] for p in extract_prompts(self.STAGE, document) if p["prompt"]]
        status = "结构检查通过（不代表成品质量）" if not issues else "需要修订；下游创作与交付会阻止使用：\n" + "\n".join(issues)
        if repairs:
            status += "\n本地参考图配置校正：\n" + "\n".join(repairs)
        advisories = document_advisories(self.STAGE, document, bundle)
        if advisories:
            status += "\n以下为人工复核提示，不阻断输出：\n" + "\n".join(advisories)
        info = f"{SKILLS[self.STAGE]} → {DOC_NAMES[self.STAGE]}\n{status}\nLLM响应次数：{len(usage)}；用量：{json.dumps(usage, ensure_ascii=False)}\n按平台LLM实际用量计费。耗时{time.monotonic()-started:.1f}秒；没有媒体生成请求。"
        return bundle, document, prompts, info


class DapaoDramaNovel(DramaStage):
    STAGE = "novel"
    DESCRIPTION = "short-drama-novel-analyze：快评、来源片段、剧情单元、人物归并与改编候选；长篇分段保留覆盖率。"


class DapaoDramaDevelop(DramaStage):
    STAGE = "develop"
    DESCRIPTION = "short-drama-develop：创作简报、改编边界、导演方向、故事引擎与分集地图；不改写剧本。"


class DapaoDramaWrite(DramaStage):
    STAGE = "write"
    DESCRIPTION = "short-drama-write：写作、定点修订、规范现成剧本；保留场次、对白、声音及集间状态。"


class DapaoDramaAssets(DramaStage):
    STAGE = "assets"
    DESCRIPTION = "short-drama-assets：拆人物、造型、地点、道具、变体、声音方向和连续性锁；不编写图片提示词。"


class DapaoDramaImage(DramaStage):
    STAGE = "image"
    RETURN_NAMES = ("📦 漫剧资料包", "📄 图片提示词文档", "🧩 资产图片提示词列表", "ℹ️ 处理信息")
    DESCRIPTION = "short-drama-image-prompts：角色板、三视图、地点板、道具板、状态图、风格帧与局部编辑提示词。"


class DapaoDramaStoryboard(DramaStage):
    STAGE = "storyboard"
    RETURN_NAMES = ("📦 漫剧资料包", "📄 分镜文档", "🧩 关键帧图片提示词列表", "ℹ️ 处理信息")
    DESCRIPTION = "short-drama-storyboard：逐镜职责、来源、起点动作终点、镜头时长、空间连续性、冻结关键帧与PLAN挂图计划。"


class DapaoDramaVideo(DramaStage):
    STAGE = "video"
    RETURN_NAMES = ("📦 漫剧资料包", "📄 视频提示词文档", "🧩 视频提示词列表", "ℹ️ 处理信息")
    DESCRIPTION = "short-drama-video-prompts：逐镜动作、运镜、表演和声音时间线；支持通用、Seedance和H3提示词方言，仅输出文字。"


class DapaoDramaReview(DramaStage):
    STAGE = "review"
    DESCRIPTION = "short-drama-review：按证据审原著、剧本、视觉连续性、分镜和提示词；仅输出问题、owner与修订要求，不自动重写。"


class DapaoDramaMerge:
    CATEGORY = CATEGORY
    FUNCTION = "merge"
    RETURN_TYPES = (BUNDLE_TYPE, "STRING")
    RETURN_NAMES = ("📦 合流资料包", "ℹ️ 合流信息")
    DESCRIPTION = "本地合并资产图片与分镜/视频两支；检查集号、设置和上游版本冲突，不调用LLM。"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"📦 支线A": (BUNDLE_TYPE,), "📦 支线B": (BUNDLE_TYPE,)}}

    def merge(self, **kw):
        bundle = merge_bundles(kw["📦 支线A"], kw["📦 支线B"])
        return bundle, "已合流：" + "、".join(DOC_NAMES[k] for k in bundle["docs"])


class DapaoDramaDeliver:
    CATEGORY = CATEGORY
    FUNCTION = "collect"
    RETURN_TYPES = ("STRING",) * 6
    RETURN_NAMES = ("🧩 资产图片提示词列表", "🧩 关键帧图片提示词列表", "🧩 视频提示词列表",
                    "📋 提示词清单JSON", "📚 五文档合订文本", "✅ 交付检查")
    OUTPUT_IS_LIST = (True, True, True, False, False, False)
    OUTPUT_NODE = True
    DESCRIPTION = "short-drama-produce的提示词交付适配：只读提取IMG/SHOT/MOTION正文与挂图顺序，不联网，不接入媒体模型。"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"📦 上游资料": (BUNDLE_TYPE,),
            "📦 交付范围": (["全部现有提示词", "资产图片", "分镜关键帧", "视频提示词"],)}}

    def collect(self, **kw):
        return self._collect_sync(**kw)

    def _collect_sync(self, **kw):
        bundle = clone_bundle(kw["📦 上游资料"])
        repairs = []
        video = bundle["docs"].get("video")
        if video and "video" not in stale_docs(bundle):
            repaired, repairs = repair_video_reference_bindings(video["text"], bundle)
            if repairs:
                video["text"] = repaired
                video["issues"] = check_document("video", repaired, bundle)
            repairs = repairs or video.get("binding_repairs", [])
        scope = kw.get("📦 交付范围", "全部现有提示词")
        stages = {"资产图片": ["image"], "分镜关键帧": ["storyboard"], "视频提示词": ["video"]}.get(scope, ["image", "storyboard", "video"])
        stale = stale_docs(bundle)
        manifest, outputs = [], {"image": [], "storyboard": [], "video": []}
        for stage in stages:
            record = bundle["docs"].get(stage)
            if not record:
                if scope != "全部现有提示词":
                    raise ValueError(f"资料包中没有{DOC_NAMES[stage]}。")
                continue
            issues = check_document(stage, record["text"], bundle)
            if stage in stale or issues:
                raise ValueError(f"{DOC_NAMES[stage]}过期或结构未通过，先在所属节点修订：" + "；".join(issues or record.get("issues", [])))
            for entry in extract_prompts(stage, record["text"]):
                manifest.append({"kind": stage, **entry, "media_generated": False})
                outputs[stage].append(entry["prompt"])
        if not manifest:
            raise ValueError("尚无可交付提示词，请先运行资产图片、分镜或视频提示词节点。")
        docs = "\n\n---\n\n".join(f"# {DOC_NAMES[k]}\n\n{bundle['docs'][k]['text']}" for k in ("write", "assets", "storyboard", "image", "video") if k in bundle["docs"])
        report = (f"资产图片{len(outputs['image'])}条；关键帧{len(outputs['storyboard'])}条；视频{len(outputs['video'])}条。\n"
                  "已检查可复制块与跨文档引用；PLAN是挂图计划，实际图片需自行准备。尚未生成或核验媒体。")
        if repairs:
            report += "\n本地参考图配置校正：\n" + "\n".join(repairs)
        advisories = [item for stage in stages if stage in bundle["docs"]
                      for item in document_advisories(stage, bundle["docs"][stage]["text"], bundle)]
        if advisories:
            report += "\n一致性需要人工复核（不阻断交付）：\n" + "\n".join(advisories)
        review = bundle["docs"].get("review")
        if review:
            verdict = field(review["text"], "结论") or "未给出标准结论，请查看审查文档"
            report += "\n文本审查：" + ("审查版本过期，请重新审查" if "review" in stale else verdict)
            docs += "\n\n---\n\n# 审查.md\n\n" + review["text"]
        manifest_json = json.dumps(manifest, ensure_ascii=False, indent=2)
        result = (outputs["image"], outputs["storyboard"], outputs["video"], manifest_json, docs, report)
        return {"ui": {"drama_preview": [report + "\n\n" + docs], "drama_manifest": [manifest_json]}, "result": result}


def select_prompt_entries(entries, selection=""):
    """Select whole prompts, never join them or inject display labels."""
    selection = str(selection).strip()
    if not selection or selection == "全部":
        return [entry["prompt"] for entry in entries]
    chosen = set()
    ids = {entry["id"]: index for index, entry in enumerate(entries)}
    for part in re.split(r"[,，、\s]+", selection):
        if part in ids:
            chosen.add(ids[part]); continue
        match = re.fullmatch(r"(\d+)(?:-(\d+))?", part)
        if not match:
            raise ValueError("提示词选择请填序号、范围或条目ID，例如1,3-5；留空为全部。")
        first, last = int(match[1]), int(match[2] or match[1])
        if first < 1 or last < first or last > len(entries):
            raise ValueError(f"提示词选择{part}超出当前{len(entries)}条的范围。")
        chosen.update(range(first - 1, last))
    return [entry["prompt"] for index, entry in enumerate(entries) if index in chosen]


class DramaCompact:
    """Compose the existing paid stages without changing their request protocol."""
    CATEGORY = CATEGORY
    FUNCTION = "generate"
    OUTPUT_NODE = True
    RETURN_TYPES = (BUNDLE_TYPE, "STRING", "STRING")
    RETURN_NAMES = ("📦 漫剧资料包", "📄 阶段文档", "ℹ️ 处理信息")

    @classmethod
    def common_inputs(cls):
        source = DramaStage.INPUT_TYPES()["required"]
        return {name: source[name] for name in (
            "🔑 API密钥", "🤖 LLM模型", "📝 本阶段要求", "🎲 随机种",
            "📝 最大输出令牌", "⌛ 请求超时")}

    async def generate(self, **kw):
        return await asyncio.to_thread(self._generate_sync, **kw)

    def _generate_sync(self, **kw):
        secret = str(kw.get("🔑 API密钥") or os.environ.get("DAPAO_API_KEY", "")).strip()
        try:
            result = self._run_compact(kw)
            if getattr(self, "BATCH_STAGE", None):
                bundle = result["result"][0]
                stage = self.BATCH_STAGE
                if stage == "selected":
                    stage = {"资产图片": "image", "分镜关键帧": "storyboard", "视频提示词": "video"}[kw.get("🧩 批量输出内容", "资产图片")]
                record = bundle["docs"].get(stage)
                valid = record and stage not in stale_docs(bundle) and not check_document(stage, record["text"], bundle)
                entries = extract_prompts(stage, record["text"]) if valid else []
                if stage == "image" and kw.get("♻️ 跨集资产输出") == "仅新增或变化资产" and bundle.get("episode_history"):
                    known = {e["id"]: e["prompt"] for old in bundle["episode_history"]
                             for e in extract_prompts("image", old["docs"].get("image", {}).get("text", ""))}
                    entries = [e for e in entries if known.get(e["id"]) != e["prompt"]]
                selected = select_prompt_entries(entries, kw.get("🔢 提示词选择", "")) if entries else []
                result["result"] += (selected,)
                if self.BATCH_STAGE == "selected":
                    # Derive durations from the same records/selection as prompts.
                    manifest = json.loads(result["result"][4])
                    videos = [e for e in manifest if e["kind"] == "video"]
                    def seconds(entry):
                        return float(re.fullmatch(r"(\d+(?:\.\d+)?)\s*(?:s|秒)?", entry["duration"])[1])
                    video_seconds = [seconds(e) for e in videos]
                    selected_seconds = []
                    if stage in {"storyboard", "video"} and entries:
                        selected_seconds = select_prompt_entries(
                            [{**e, "prompt": seconds(e)} for e in entries], kw.get("🔢 提示词选择", ""))
                    result["result"] += (video_seconds, selected_seconds)
            bundle_json = json.dumps(result["result"][0], ensure_ascii=False)
            result.setdefault("ui", {})["drama_bundle"] = [bundle_json]
            result["result"] += (bundle_json,)
            return result
        except Exception as error:
            raise RuntimeError(safe_text(error, secret)) from None

    def steps(self, bundle, kw, stages):
        infos = []
        for stage_class, overrides in stages:
            args = {**kw, "📦 上游资料": bundle, "📄 原文或现有稿": "", **overrides}
            stage = stage_class.STAGE
            reference = kw.get(f"📚 {DOC_NAMES[stage]}专项参考", "自动精选")
            args["📚 专项参考"] = reference if reference != "自动精选" else overrides.get("📚 专项参考", "自动精选")
            revision = str(kw.get(f"📄 {DOC_NAMES[stage]}修订稿", "")).strip()
            if revision:
                args["📄 原文或现有稿"] = revision
            bundle, _, _, info = stage_class()._generate_sync(**args)
            infos.append(info)
            if bundle["docs"][stage_class.STAGE].get("issues"):
                # Keep the actual draft visible for revision, but never spend on its descendants.
                return bundle, infos, False
        return bundle, infos, True

    def preview(self, bundle, infos, complete):
        docs = "\n\n---\n\n".join(f"# {DOC_NAMES[key]}\n\n{record['text']}"
                                      for key, record in bundle["docs"].items())
        status = ("本步骤完成。" if complete else "已停止后续调用：请按检查信息修订问题稿。") + "\n\n" + "\n\n".join(infos)
        return {"ui": {"drama_preview": [status + "\n\n" + docs]},
                "result": (bundle, docs, status)}

    @staticmethod
    def advanced_inputs(stages):
        fields = {"📂 导入文档类型": (list(DOC_NAMES.values()) + ["完整资料包JSON"],),
                  "📄 导入文档": ("STRING", {"default": "", "multiline": True})}
        for stage in stages:
            fields[f"📚 {DOC_NAMES[stage]}专项参考"] = (reference_options(stage),)
            fields[f"📄 {DOC_NAMES[stage]}修订稿"] = ("STRING", {"default": "", "multiline": True})
        return fields

    @staticmethod
    def input_bundle(kw):
        upstream = kw.get("📦 上游资料")
        if isinstance(upstream, str):
            try:
                upstream = json.loads(upstream)
            except (ValueError, TypeError):
                raise ValueError("上游资料不是有效的完整资料包JSON，请连接‘完整资料包JSON（续集用）’，不要连接提示词清单或剧本文本。") from None
            if not isinstance(upstream, dict) or upstream.get("schema") != "dapao.drama/1":
                raise ValueError("上游文本不是漫剧完整资料包，请连接‘完整资料包JSON（续集用）’输出。")
        bundle = clone_bundle(upstream)
        imported = str(kw.get("📄 导入文档", "")).strip()
        if imported:
            if kw.get("📂 导入文档类型") == "完整资料包JSON":
                bundle = clone_bundle(json.loads(imported))
            else:
                stage = next(k for k, name in DOC_NAMES.items() if name == kw.get("📂 导入文档类型", "剧本.md"))
                put_doc(bundle, stage, imported)
        video = bundle["docs"].get("video")
        if video and "video" not in stale_docs(bundle):
            repaired, changes = repair_video_reference_bindings(video["text"], bundle)
            if changes:
                video["text"] = repaired
                video["issues"] = check_document("video", repaired, bundle)
                video["binding_repairs"] = changes
        return bundle


class DapaoDramaPrepare(DramaCompact):
    RETURN_TYPES = DramaCompact.RETURN_TYPES + ("STRING",)
    RETURN_NAMES = DramaCompact.RETURN_NAMES + ("💾 完整资料包JSON（续集用）",)
    OUTPUT_IS_LIST = (False, False, False, False)
    DESCRIPTION = "简化第一步：粘贴已有剧本、原创想法或小说正文；内部完成必要分析与剧本整理。小说会分段调用，成功请求可恢复。"

    @classmethod
    def INPUT_TYPES(cls):
        project = DapaoDramaProject.INPUT_TYPES()["required"]
        common = cls.common_inputs()
        required = {"🔑 API密钥": common.pop("🔑 API密钥"), "🤖 LLM模型": common.pop("🤖 LLM模型"),
            "📥 内容来源": (["已有剧本", "原创想法", "小说改编"],),
            "📄 剧本或故事内容": ("STRING", {"default": "", "multiline": True,
                "tooltip": "已有剧本/小说请粘贴正文；原创填写故事想法。当前按一集处理，不会自动生成全部集数。"})}
        for name in ("📛 项目名称", "⏱️ 单集目标秒数", "🎨 制作形态", "🖌️ 视觉风格", "📐 画幅比例",
                     "🎬 视频提示词方言", "🖼️ 参考方式"):
            required[name] = project[name]
        required["📚 系列规划"] = (["不需要（直接做本集）", "需要（先规划再写本集）"],)
        required.update(common)
        optional = {name: project[name] for name in ("🎞️ 当前集号", "📚 计划集数", "🌐 提示词语言", "⏳ 单镜最短秒数", "⌛ 单镜最长秒数")}
        novel = DapaoDramaNovel.INPUT_TYPES()["required"]
        optional["🧮 最大分析段数"] = novel["🧮 最大分析段数"]
        for name in ("🔍 分析方式", "🗂️ 原著分段依据", "📏 每段字符数"):
            optional[name] = novel[name]
        optional["🔍 分析方式"] = (novel["🔍 分析方式"][0], {"default": "全文分段分析"})
        optional["🎛️ 准备任务"] = (["自动完成剧本", "仅原著分析", "仅系列开发", "仅剧本创作或修订", "仅导入已有文档（不调用LLM）", "续写下一集（继承前集）"], {"tooltip": "续集自动按前集集号+1；继承前集项目与视觉风格，使用这里的单集目标秒数。内容框填写新一集方向，无须再粘贴旧剧本。"})
        optional["📦 上游资料"] = (f"{BUNDLE_TYPE},STRING", {"tooltip": "接受漫剧资料包或完整资料包JSON（续集用），JSON会自动解析，无需复制到导入框。"})
        optional.update(cls.advanced_inputs(("novel", "develop", "write")))
        return {"required": required, "optional": optional}

    def _run_compact(self, kw):
        raw = str(kw.get("📄 剧本或故事内容", "")).strip()
        task = kw.get("🎛️ 准备任务", "自动完成剧本")
        if not raw and task == "自动完成剧本" and not kw.get("📦 上游资料"):
            raise ValueError("请在“剧本或故事内容”中粘贴剧本、故事想法或小说正文。")
        mode = kw.get("📥 内容来源", "已有剧本")
        if mode not in self.INPUT_TYPES()["required"]["📥 内容来源"][0]:
            raise ValueError("请选择有效的内容来源。")
        request = str(kw.get("📝 本阶段要求", "")).strip()
        if task == "续写下一集（继承前集）":
            if not kw.get("📦 上游资料") and not (kw.get("📂 导入文档类型") == "完整资料包JSON" and kw.get("📄 导入文档")):
                raise ValueError("请接入前集节点2/3的漫剧资料包，或导入下载的完整资料包JSON。")
            direction = "\n".join(x for x in (raw, request) if x)
            previous = self.input_bundle(kw)
            bundle = next_episode_bundle(previous, direction, kw.get("⏱️ 单集目标秒数", previous["config"]["seconds"]))
            result = self.preview(*self.steps(bundle, kw, [(DapaoDramaWrite, {
                "📝 本阶段要求": "从前集结束状态续写下一集，不重复前集剧情。用户本集方向：\n" + direction})]))
            result["ui"]["drama_preview"][0] = f"已承接{previous['config']['episode']} → {bundle['config']['episode']}；继承系列风格、人物和场景基准。\n" + result["ui"]["drama_preview"][0]
            return result
        # Never keep the entire source novel in config (it would be sent to every later stage).
        brief = raw if mode == "原创想法" else request or f"根据用户提供的{mode}制作当前集；保持人物关系与剧情因果。"
        if kw.get("📦 上游资料"):
            bundle = self.input_bundle(kw)
        else:
            bundle, _ = DapaoDramaProject()._build_sync(**{**kw, "📝 创作简报": brief})
            bundle = self.input_bundle({**kw, "📦 上游资料": bundle})
        if task == "仅导入已有文档（不调用LLM）":
            return self.preview(bundle, ["已导入文档；未调用LLM。"], True)
        stages = []
        if task == "仅原著分析" or (task == "自动完成剧本" and mode == "小说改编"):
            stages.append((DapaoDramaNovel, {"📄 原文或现有稿": raw, "🔍 分析方式": kw.get("🔍 分析方式", "全文分段分析")}))
        if task == "仅系列开发" or (task == "自动完成剧本" and (mode == "小说改编" or kw.get("📚 系列规划") == "需要（先规划再写本集）")):
            stages.append((DapaoDramaDevelop, {"📄 原文或现有稿": raw if task == "仅系列开发" or mode == "已有剧本" else ""}))
        write_request = request
        if mode == "已有剧本":
            write_request = "规范化用户提供的剧本，保留原剧情、人物关系和关键对白。整理场次、动作、对白、声音及交接状态；指出矛盾和缺口，不擅自改写故事走向。\n" + request
        if task in {"自动完成剧本", "仅剧本创作或修订"}:
            stages.append((DapaoDramaWrite, {"📄 原文或现有稿": raw if mode != "小说改编" else "",
                                          "📝 本阶段要求": write_request}))
        return self.preview(*self.steps(bundle, kw, stages))


class DapaoDramaVisual(DramaCompact):
    BATCH_STAGE = "image"
    RETURN_TYPES = DramaCompact.RETURN_TYPES + ("STRING", "STRING")
    RETURN_NAMES = DramaCompact.RETURN_NAMES + ("🧩 所选资产批量提示词", "💾 完整资料包JSON（续集用）")
    OUTPUT_IS_LIST = (False, False, False, True, False)
    DESCRIPTION = "简化第二步：自动分析人物/场景/道具，再按选项生成资产图片提示词。资料包自动传递，无需分支合流。"

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"📦 上游资料": (BUNDLE_TYPE,),
            "🎨 处理内容": (["人物场景分析＋资产图片提示词", "仅人物场景分析", "仅资产图片提示词（复用已有设定）"],), **cls.common_inputs()},
            "optional": {"👤 资产规划": (["人物优先（角色设定＋必要场景）", "仅人物设定", "完整资产（人物＋场景＋关键道具）"],),
                "🖌️ 图片用途": (["自动规划", "人物身份板", "角色三视图", "造型与状态变体", "地点板", "关键道具板", "多对象组合板", "Lookdev风格比较", "局部编辑与修订"],),
                "🔢 提示词选择": ("STRING", {"default": "", "tooltip": "留空全部；例如1,3-5，或IMG条目ID。仅筛选批量出口，不修改原文档。"}),
                **cls.advanced_inputs(("assets", "image")),
                "♻️ 跨集资产输出": (["全部本集资产", "仅新增或变化资产"], {"tooltip": "仅影响所选资产批量出口；前集同编号同提示词的资产不重复输出。空列表表示没有新资产，继续使用已保存参考图。"})}}

    def _run_compact(self, kw):
        stages = [(DapaoDramaAssets, {})]
        mode = kw.get("🎨 处理内容", "人物场景分析＋资产图片提示词")
        if mode not in self.INPUT_TYPES()["required"]["🎨 处理内容"][0]:
            raise ValueError("请选择有效的处理内容。")
        if mode == "仅资产图片提示词（复用已有设定）":
            stages = []
        if mode != "仅人物场景分析":
            strategy = kw.get("👤 资产规划", "人物优先（角色设定＋必要场景）")
            directions = {
                "人物优先（角色设定＋必要场景）": "先生成本集主要人物的角色身份设定图（面部、发型、服装、体态；需要多视角时明确是一张组合板），人物条目排在最前。然后按必要性规划主要场景。门、门铃、墙面等环境构件并入场景，除非是跨镜头必须独立锁定的剧情核心物件，不单独占用资产图。不用无关道具凑数。",
                "仅人物设定": "只生成本集有视觉形象的人物角色设定图，不生成场景、建筑、门、道具。先主角后配角；明确区分身份、三视图、表情或剧情必需造型，不重复同一提示词凑数。不为只有声音且不出镜的角色臆造外貌。",
                "完整资产（人物＋场景＋关键道具）": "按主要人物、配角、主要场景、剧情关键道具顺序生成资产图提示词。人物设定排在最前。普通环境构件并入场景，仅为需要跨镜头保持一致的关键道具单独建图，避免重复和不必要的物件。",
            }
            if strategy not in directions:
                raise ValueError("请选择有效的资产规划方式。")
            purpose = kw.get("🖌️ 图片用途", "自动规划")
            direction = directions[strategy] if purpose == "自动规划" else f"本轮只生成{purpose}用途的图片提示词，保留身份锚点和未要求修改的部分。"
            recipe = {"人物身份板": "character-and-look.md", "角色三视图": "production-sheet-recipes.md",
                      "造型与状态变体": "look-and-state-variant.md", "地点板": "location-plate.md",
                      "关键道具板": "prop-plate.md", "多对象组合板": "production-sheet-recipes.md",
                      "Lookdev风格比较": "lookdev-frame.md", "局部编辑与修订": "edit-and-revision.md"}.get(purpose, "自动精选")
            stages.append((DapaoDramaImage, {"📚 专项参考": recipe,
                "📝 本阶段要求": str(kw.get("📝 本阶段要求", "")) + "\n资产规划：" + direction}))
        return self.preview(*self.steps(self.input_bundle(kw), kw, stages))


class DapaoDramaFinish(DramaCompact):
    BATCH_STAGE = "selected"
    DESCRIPTION = "简化第三步：生成分镜和视频提示词，可选文本审查，直接预览/下载交付清单。静态模式跳过视频，仅整理模式不调用LLM。"
    OUTPUT_NODE = True
    RETURN_TYPES = (BUNDLE_TYPE,) + DapaoDramaDeliver.RETURN_TYPES + ("STRING", "FLOAT", "FLOAT", "STRING")
    RETURN_NAMES = ("📦 漫剧资料包",) + DapaoDramaDeliver.RETURN_NAMES + ("🧩 所选批量提示词", "⏱️ 全部视频时长列表", "⏱️ 所选批量时长列表", "💾 完整资料包JSON（续集用）")
    OUTPUT_IS_LIST = (False,) + DapaoDramaDeliver.OUTPUT_IS_LIST + (True, True, True, False)

    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"📦 上游资料": (BUNDLE_TYPE,),
            "🎬 交付模式": (["自动（按制作形态）", "动态漫剧（图片＋视频提示词）", "静态漫剧（仅图片提示词）", "仅整理已有提示词（不调用LLM）", "仅分镜关键帧", "仅视频提示词（复用已有分镜）", "仅文本审查"],),
            "🔍 文本审查": (["关闭", "开启（增加一次LLM调用）"],), **cls.common_inputs()},
            "optional": {"🧩 批量输出内容": (["资产图片", "分镜关键帧", "视频提示词"],),
                "🔢 提示词选择": ("STRING", {"default": "", "tooltip": "留空全部；例如1,3-5，或完整IMG/SHOT/MOTION条目ID。"}),
                "🔎 审查范围": (["全部现有文档", "原著分析", "故事与剧本", "资产与连续性", "图片提示词", "分镜与关键帧", "视频提示词", "交付隐私", "反模板与AI味"],),
                "🎵 时间线音乐要求": ("STRING", {"default": "", "multiline": True,
                    "tooltip": "选填。仅写视频提示词时生效，音乐区间/剧情功能/进入退出/动态曲线写入视频文档；不调用音乐模型。"}),
                **cls.advanced_inputs(("storyboard", "video", "review")),
                "⏱️ 时长规划": (["自动分镜", "按段数逐段设置", "手动逐段时长"],),
                "📝 逐段时长（秒）": ("STRING", {"default": "", "tooltip": "旧工作流兼容：例如6,6,8,10代表4段共30秒，合计覆盖原目标。推荐改用按段数逐段设置。"}),
                "🔢 分段数量": ("INT", {"default": 6, "min": 1, "max": 32}),
                "⏳ 总时长规则": (["必须与01目标一致", "以本节点分段合计为准"], {"tooltip": "默认合计必须等于01目标，否则在调用LLM前停止。明确选择覆盖时，按新预算重新组织分镜，01剧本文档保持原稿。"}),
                **{f"⏱️ 第{i:02d}段（秒）": ("FLOAT", {"default": 10.0, "min": 0.5, "max": 120.0, "step": 0.5}) for i in range(1, 33)}}}

    def _run_compact(self, kw):
        bundle = self.input_bundle(kw)
        mode = kw.get("🎬 交付模式", "自动（按制作形态）")
        if mode not in self.INPUT_TYPES()["required"]["🎬 交付模式"][0]:
            raise ValueError("请选择有效的交付模式。")
        timing = None
        planning = kw.get("⏱️ 时长规划", "自动分镜")
        if planning in {"手动逐段时长", "按段数逐段设置"} and mode not in {"仅整理已有提示词（不调用LLM）", "仅文本审查"}:
            raw = str(kw.get("📝 逐段时长（秒）", "")).strip()
            values = re.split(r"[,，、;；\s]+", raw)
            if planning == "按段数逐段设置":
                count = int(kw.get("🔢 分段数量", 6))
                if not 1 <= count <= 32:
                    raise ValueError("分段数量应为1至32；尚未调用LLM。")
                values = [str(kw.get(f"⏱️ 第{i:02d}段（秒）", 10.0)) for i in range(1, count + 1)]
                raw = ",".join(values)
            if not raw or any(not re.fullmatch(r"\d+(?:\.\d+)?", v) for v in values):
                raise ValueError("逐段时长请填写秒数，例如6,6,8,10；尚未调用LLM。")
            timing = [float(v) for v in values]
            cfg = bundle["config"]
            if len(timing) > 200 or any(v <= 0 or v > 120 or (cfg["shot_min"] and v < cfg["shot_min"]) or (cfg["shot_max"] and v > cfg["shot_max"]) for v in timing):
                raise ValueError("逐段时长须为0至120秒之间的正数、最多200段，并符合01设定的单镜时长范围；尚未调用LLM。")
            if planning == "按段数逐段设置" and kw.get("⏳ 总时长规则", "必须与01目标一致") != "以本节点分段合计为准" and abs(sum(timing) - float(cfg["seconds"])) > 0.001:
                raise ValueError(f"分段合计{sum(timing):g}秒，01目标为{cfg['seconds']}秒。请调整各段时长，或明确选择“以本节点分段合计为准”；尚未调用LLM。")
            bundle["timing_plan"] = timing
            if mode == "仅视频提示词（复用已有分镜）":
                board = bundle["docs"].get("storyboard", {}).get("text", "")
                if check_document("storyboard", board, bundle):
                    raise ValueError("已有分镜不符合手动时长，请选择动态漫剧或仅分镜关键帧重新规划；尚未调用LLM。")
        stages = []
        review_args = {"📝 本阶段要求": str(kw.get("📝 本阶段要求", "")) +
                       "\n仅审查指定范围：" + kw.get("🔎 审查范围", "全部现有文档") + "。按证据指出问题及负责修订的阶段，不自动改稿。"}
        if mode == "仅文本审查":
            bundle, infos, complete = self.steps(bundle, kw, [(DapaoDramaReview, review_args)])
            preview = self.preview(bundle, infos, complete)
            _, docs, status = preview["result"]
            status += "\n审查结论：" + (field(bundle["docs"]["review"]["text"], "结论") or "请查看审查文档")
            return {"ui": preview["ui"], "result": (bundle, [], [], [], "[]", docs, status)}
        if mode != "仅整理已有提示词（不调用LLM）":
            if mode != "仅视频提示词（复用已有分镜）":
                args = {}
                if timing:
                    args["📝 本阶段要求"] = str(kw.get("📝 本阶段要求", "")) + f"\n严格生成{len(timing)}个分镜，依次为{timing}秒，总计{sum(timing)}秒，优先于原项目目标时长。按预算重新组织剧情、动作和对白，不事后截断，不只修改时长字段。"
                stages.append((DapaoDramaStoryboard, args))
            dynamic = mode in {"动态漫剧（图片＋视频提示词）", "仅视频提示词（复用已有分镜）"} or (mode == "自动（按制作形态）" and bundle["config"]["form"] != "静态漫剧")
            if dynamic:
                video_args = {}
                if str(kw.get("🎵 时间线音乐要求", "")).strip():
                    video_args["📝 本阶段要求"] = str(kw.get("📝 本阶段要求", "")) + "\n在视频文档另设时间线音乐章节，写明区间、剧情功能、进入退出、动态曲线及边界，不编造歌词：\n" + kw["🎵 时间线音乐要求"]
                stages.append((DapaoDramaVideo, video_args))
            else:
                # Exclude old dynamic results when explicitly switching to static delivery.
                bundle["docs"].pop("video", None)
                bundle["docs"].pop("review", None)
            if kw.get("🔍 文本审查") == "开启（增加一次LLM调用）":
                stages.append((DapaoDramaReview, review_args))
        bundle, infos, complete = self.steps(bundle, kw, stages)
        if not complete:
            preview = self.preview(bundle, infos, False)
            _, docs, status = preview["result"]
            valid = clone_bundle(bundle)
            for stage in ("image", "storyboard", "video"):
                record = valid["docs"].get(stage)
                if record and (stage in stale_docs(valid) or check_document(stage, record["text"], valid)):
                    valid["docs"].pop(stage)
            if any(stage in valid["docs"] for stage in ("image", "storyboard", "video")):
                partial = DapaoDramaDeliver()._collect_sync(**{"📦 上游资料": valid})["result"]
                lists, manifest = partial[:3], partial[3]
            else:
                lists, manifest = ([], [], []), "[]"
            status = "部分交付：保留已通过检查的提示词；失败或尚未生成的阶段为空。\n" + status
            preview["ui"] = {"drama_preview": [status + "\n\n" + docs], "drama_manifest": [manifest]}
            preview["result"] = (bundle, *lists, manifest, docs, status)
            return preview
        delivered = DapaoDramaDeliver()._collect_sync(**{"📦 上游资料": bundle})
        result = delivered["result"]
        report = result[-1] + "\n\n" + "\n\n".join(infos)
        if bundle.get("timing_plan"):
            plan = bundle["timing_plan"]
            report = f"手动计划：{len(plan)}段；逐段{plan}秒；总计{sum(plan):g}秒。\n" + report
        delivered["result"] = (bundle, *result[:-1], report)
        delivered["ui"]["drama_preview"] = [report + "\n\n" + result[-2]]
        return delivered


_ADVANCED_NODES = [
    (DapaoDramaProject, "🐠01漫剧项目与流程"), (DapaoDramaNovel, "📖02漫剧原著分析"),
    (DapaoDramaDevelop, "🧠03漫剧系列开发"), (DapaoDramaWrite, "✍️04漫剧剧本创作"),
    (DapaoDramaAssets, "🎭05漫剧视觉资产"), (DapaoDramaImage, "🖼️06漫剧资产图片提示词"),
    (DapaoDramaStoryboard, "🎬07漫剧分镜与关键帧"), (DapaoDramaVideo, "🎞️08漫剧视频提示词"),
    (DapaoDramaReview, "🔍09漫剧审查"), (DapaoDramaDeliver, "📦10漫剧提示词交付"),
    (DapaoDramaMerge, "🔀11漫剧资料合流"),
]
for _class, _ in _ADVANCED_NODES:
    _class.CATEGORY = CATEGORY + "/🧰高级分步（原11节点）"
_NODES = [
    (DapaoDramaPrepare, "🐠01漫剧剧本准备"),
    (DapaoDramaVisual, "🎭02漫剧人物与画面"),
    (DapaoDramaFinish, "🎬03漫剧分镜与交付"),
] + _ADVANCED_NODES
NODE_CLASS_MAPPINGS = {cls.__name__: cls for cls, _ in _NODES}
NODE_DISPLAY_NAME_MAPPINGS = {cls.__name__: name + "@炮老师的小课堂" for cls, name in _NODES}
