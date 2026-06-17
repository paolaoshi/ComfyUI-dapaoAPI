"""
RH 批量 LLM 提示词节点

按 A 组图片作为主锚点，对齐 A/B/C/D 四组图片，逐条调用 RH LLM 生成提示词列表。
作者：@炮老师的小课堂
"""

import base64
import io
import json
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import torch
from PIL import Image

from .rh_llm_chat_node import (
    DEFAULT_MODEL,
    LLM_CHAT_URL,
    REASONING_CHOICES,
    DapaoRHLLMChatNode,
    _clean_think_tags,
    _default_model,
    _fetch_model_list,
)


NODE_NAME = "DapaoRHBatchLLMPromptNode"
VALID_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
GROUP_KEYS = ("A", "B", "C", "D")
MISSING_STRATEGIES = ["严格报错", "单图复用", "末张补齐", "忽略缺失组"]
TASK_FAILURE_STRATEGIES = ["失败占位继续", "跳过失败继续", "任一失败中断"]
IMAGE_INFERENCE_MODES = ["并发逐条请求", "单次批量请求"]
DEFAULT_GROUP_ROLES = {
    "A": "目标图",
    "B": "参考图",
    "C": "补充参考",
    "D": "风格参考",
}

DEFAULT_SYSTEM_ROLE = """你是一个专业的批量图像编辑提示词专家。你会严格根据每一组已对齐图片和用户元指令，为当前编号图片生成一个专属提示词。"""

DEFAULT_META_INSTRUCTION = """请根据当前组图片生成一个适合下游图像生成/图像编辑模型使用的最终提示词。
要求：
1. 只输出当前这一项的最终提示词文本。
2. 不输出编号、标题、Markdown、JSON、解释、寒暄或多余前后缀。
3. 必须保持与当前 A 图一一对应，不要描述其他编号图片。
4. 如果有 B/C/D 图，请按它们的角色说明理解并融合。"""

TEXT_ONLY_SYSTEM_HINT = """当用户没有提供图片时，你是一个批量提示词生成助手。你需要根据用户文字需求生成多条彼此不同、可直接用于下游文生图/图像生成模型的提示词。"""


def _log_info(message):
    print(f"[dapaoAPI-RH批量LLM提示词] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH批量LLM提示词] 错误：{message}")


def _natural_sort_key(path):
    text = path.name if isinstance(path, Path) else str(path)
    return [int(part) if part.isdigit() else part.lower() for part in re.split(r"(\d+)", text)]


def _normalize_name(name):
    stem = Path(name).stem if name else ""
    return re.sub(r"[\s_\-\.()\[\]{}]+", "", stem.lower())


def _number_key(name):
    stem = Path(name).stem if name else ""
    numbers = re.findall(r"\d+", stem)
    if not numbers:
        return ""
    return "-".join(str(int(number)) for number in numbers)


def _chinese_number_to_int(text):
    if not text:
        return None
    digits = {
        "零": 0,
        "一": 1,
        "二": 2,
        "两": 2,
        "三": 3,
        "四": 4,
        "五": 5,
        "六": 6,
        "七": 7,
        "八": 8,
        "九": 9,
    }
    text = text.strip()
    if text == "十":
        return 10
    if "十" in text:
        left, _, right = text.partition("十")
        tens = digits.get(left, 1) if left else 1
        ones = digits.get(right, 0) if right else 0
        return tens * 10 + ones
    return digits.get(text)


def _strip_list_prefix(text):
    return re.sub(r"^\s*(?:[-*•]+|\d+[\.\)、):：]|[一二三四五六七八九十]+[\.\)、):：])\s*", "", text).strip()


def _pil_to_data_uri(image, max_side=1024, jpeg_quality=85):
    if image.mode != "RGB":
        image = image.convert("RGB")
    original_size = image.size
    max_side = int(max_side or 0)
    if max_side > 0:
        width, height = image.size
        longest = max(width, height)
        if longest > max_side:
            scale = max_side / float(longest)
            image = image.resize((max(1, int(width * scale)), max(1, int(height * scale))), Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=int(jpeg_quality), optimize=True)
    raw = buffer.getvalue()
    encoded = base64.b64encode(raw).decode("ascii")
    meta = {
        "original_size": original_size,
        "encoded_size": image.size,
        "bytes": len(raw),
        "format": "JPEG",
        "quality": int(jpeg_quality),
        "max_side": max_side,
    }
    return f"data:image/jpeg;base64,{encoded}", meta


def _tensor_to_data_uri(image_tensor, max_side=1024, jpeg_quality=85):
    if image_tensor.dim() == 4:
        image_tensor = image_tensor[0]
    image_np = np.clip(image_tensor.cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
    return _pil_to_data_uri(Image.fromarray(image_np), max_side=max_side, jpeg_quality=jpeg_quality)


@dataclass
class BatchImageItem:
    group: str
    index: int
    name: str
    source: str
    path: str = ""
    tensor: object = None
    norm_key: str = field(init=False)
    num_key: str = field(init=False)
    data_uri: str = field(default="", init=False)
    encode_meta: dict = field(default_factory=dict, init=False)

    def __post_init__(self):
        self.norm_key = _normalize_name(self.name)
        self.num_key = _number_key(self.name)

    def to_public_dict(self):
        return {
            "group": self.group,
            "index": self.index + 1,
            "name": self.name,
            "source": self.source,
            "path": self.path,
            "normalized_key": self.norm_key,
            "number_key": self.num_key,
        }

    def to_data_uri(self, max_side=1024, jpeg_quality=85):
        if self.data_uri:
            return self.data_uri
        if self.tensor is not None:
            self.data_uri, self.encode_meta = _tensor_to_data_uri(self.tensor, max_side=max_side, jpeg_quality=jpeg_quality)
            return self.data_uri
        if self.path:
            with Image.open(self.path) as image:
                self.data_uri, self.encode_meta = _pil_to_data_uri(image, max_side=max_side, jpeg_quality=jpeg_quality)
            return self.data_uri
        raise ValueError(f"{self.group}组第 {self.index + 1} 张图片没有可用数据。")


class DapaoRHBatchLLMPromptNode(DapaoRHLLMChatNode):
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(cls):
        models = _fetch_model_list()
        return {
            "required": {
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "填入 RunningHub LLM API Key",
                }),
                "🤖 模型ID": (models, {
                    "default": _default_model(models),
                    "tooltip": "复用 RH LLM 模型列表。"
                }),
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_SYSTEM_ROLE,
                }),
                "🧾 元指令": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_META_INSTRUCTION,
                    "placeholder": "描述你希望 LLM 如何根据每组图片生成提示词...",
                }),
                "📂 A组文件夹": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "A组图片文件夹；A组 IMAGE 未连接时生效",
                }),
                "📂 B组文件夹": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "B组图片文件夹；B组 IMAGE 未连接时生效",
                }),
                "📂 C组文件夹": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "C组图片文件夹；C组 IMAGE 未连接时生效",
                }),
                "📂 D组文件夹": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "D组图片文件夹；D组 IMAGE 未连接时生效",
                }),
                "🧩 缺失处理策略": (MISSING_STRATEGIES, {
                    "default": "严格报错",
                    "tooltip": "智能对齐找不到对应图片时的处理方式。默认严格报错，防止错位。"
                }),
                "🔢 无图默认数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "完全没有接入图片/文件夹时使用。若指令里写了 10组/10个/十组，会优先自动识别文本数量。"
                }),
                "🛡️ 多图模式最大提示词数量": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 10000,
                    "step": 1,
                    "tooltip": "只限制有图/文件夹模式。0 表示不限制；例如填 50 时最多处理 A组前 50 项，避免误传大文件夹消耗大量 token。"
                }),
                "🚦 多图推理模式": (IMAGE_INFERENCE_MODES, {
                    "default": "并发逐条请求",
                    "tooltip": "并发逐条请求每个任务只发当前配对图，通常更接近单独节点速度；单次批量请求会把所有图片塞进一次请求，图片多时可能很慢。"
                }),
                "🚀 并发数": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 20,
                    "step": 1,
                    "tooltip": "有图/文件夹模式下同时请求 RH LLM 的任务数量。过高可能触发限流，建议 2-6。"
                }),
                "🛟 失败重试次数": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "tooltip": "单个图片配对任务失败后的额外重试次数。"
                }),
                "🧪 推理失败策略": (TASK_FAILURE_STRATEGIES, {
                    "default": "失败占位继续",
                    "tooltip": "失败占位继续会保留列表位置；跳过失败继续会减少输出数量；任一失败中断会直接报错。"
                }),
                "🖼️ 发送图片最长边": ("INT", {
                    "default": 1024,
                    "min": 256,
                    "max": 4096,
                    "step": 64,
                    "tooltip": "发送给 LLM 前会等比缩放图片，默认最长边 1024。调小更快更省 token；调大细节更多但更慢。"
                }),
                "🗜️ 发送图片JPEG质量": ("INT", {
                    "default": 85,
                    "min": 40,
                    "max": 100,
                    "step": 1,
                    "tooltip": "发送给 LLM 的 JPEG 压缩质量。默认 85，通常足够做提示词/编辑指令分析。"
                }),
                "🌡️ 温度": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01}),
                "📝 最大输出令牌": ("INT", {"default": 2048, "min": 1, "max": 65536, "step": 1}),
                "🎲 Top_P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🧠 推理强度": (REASONING_CHOICES, {"default": "none"}),
                "🎲 随机种": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": "randomize",
                    "tooltip": "只用于 ComfyUI 缓存控制；不会发送给 RH LLM。"
                }),
                "⏱️ 超时时间": ("INT", {"default": 180, "min": 30, "max": 1200, "step": 10}),
            },
            "optional": {
                "🖼️ A组图像": ("IMAGE",),
                "🖼️ B组图像": ("IMAGE",),
                "🖼️ C组图像": ("IMAGE",),
                "🖼️ D组图像": ("IMAGE",),
                "➕ 额外参数JSON": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "{\"presence_penalty\":0,\"frequency_penalty\":0}",
                    "tooltip": "JSON对象，会合并到 RH 请求体；同名字段会覆盖节点控件生成的参数。"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("📝 提示词列表", "📄 完整响应", "ℹ️ 处理信息")
    OUTPUT_IS_LIST = (True, False, False)
    FUNCTION = "generate_batch_prompts"
    CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"
    DESCRIPTION = "RH 批量 LLM 提示词：A/B/C/D 多组图片智能对齐，逐条生成下游提示词 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _first_input_value(value, default=None):
        if isinstance(value, (list, tuple)):
            if not value:
                return default
            return value[0]
        return value if value is not None else default

    @classmethod
    def _text_input_value(cls, kwargs, name, default=""):
        value = cls._first_input_value(kwargs.get(name), default)
        return default if value is None else str(value)

    @classmethod
    def _int_input_value(cls, kwargs, name, default):
        value = cls._first_input_value(kwargs.get(name), default)
        try:
            return int(value)
        except Exception:
            return int(default)

    @classmethod
    def _float_input_value(cls, kwargs, name, default):
        value = cls._first_input_value(kwargs.get(name), default)
        try:
            return float(value)
        except Exception:
            return float(default)

    @staticmethod
    def _expand_image_input(value, group):
        if value is None:
            return []
        values = value if isinstance(value, (list, tuple)) else [value]
        items = []
        for raw in values:
            if raw is None:
                continue
            if isinstance(raw, torch.Tensor):
                if raw.dim() == 4:
                    for index in range(raw.shape[0]):
                        items.append(BatchImageItem(group, len(items), f"{group}_{len(items) + 1:03d}.png", "IMAGE", tensor=raw[index:index + 1]))
                elif raw.dim() == 3:
                    items.append(BatchImageItem(group, len(items), f"{group}_{len(items) + 1:03d}.png", "IMAGE", tensor=raw.unsqueeze(0)))
                continue
            if isinstance(raw, Image.Image):
                items.append(BatchImageItem(group, len(items), f"{group}_{len(items) + 1:03d}.png", "PIL", tensor=None))
                items[-1].data_uri, items[-1].encode_meta = _pil_to_data_uri(raw)
        return items

    @staticmethod
    def _folder_images(folder_path, group):
        folder_text = (folder_path or "").strip().strip('"')
        if not folder_text:
            return []
        folder = Path(folder_text)
        if not folder.exists() or not folder.is_dir():
            raise ValueError(f"{group}组文件夹不存在或不是文件夹：{folder_text}")
        paths = sorted(
            [path for path in folder.iterdir() if path.is_file() and path.suffix.lower() in VALID_IMAGE_EXTS],
            key=_natural_sort_key,
        )
        return [
            BatchImageItem(group, index, path.name, "folder", path=str(path))
            for index, path in enumerate(paths)
        ]

    def _collect_group_items(self, kwargs, group):
        image_key = f"🖼️ {group}组图像"
        folder_key = f"📂 {group}组文件夹"
        image_items = self._expand_image_input(kwargs.get(image_key), group)
        if image_items:
            return image_items, {
                "group": group,
                "source": "IMAGE",
                "count": len(image_items),
                "folder_ignored": bool(self._text_input_value(kwargs, folder_key, "").strip()),
            }
        folder_items = self._folder_images(self._text_input_value(kwargs, folder_key, ""), group)
        return folder_items, {"group": group, "source": "folder" if folder_items else "empty", "count": len(folder_items)}

    @staticmethod
    def _unique_map(items, attr):
        result = {}
        duplicate_keys = set()
        for item in items:
            key = getattr(item, attr)
            if not key:
                continue
            if key in result:
                duplicate_keys.add(key)
                result[key] = None
            elif key not in duplicate_keys:
                result[key] = item
        return {key: item for key, item in result.items() if item is not None}

    @classmethod
    def _fallback_item(cls, items, strategy):
        if not items or strategy == "忽略缺失组":
            return None, "ignored_missing"
        if strategy == "单图复用" and len(items) == 1:
            return items[0], "single_reuse"
        if strategy == "末张补齐":
            return items[-1], "last_fill"
        return None, "missing"

    @classmethod
    def _match_item(cls, anchor, items, strategy):
        if not items:
            return None, "empty_group"

        if strategy == "单图复用" and len(items) == 1:
            return items[0], "single_reuse"

        norm_map = cls._unique_map(items, "norm_key")
        num_map = cls._unique_map(items, "num_key")
        target_has_numbers = any(item.num_key for item in items)

        if anchor.norm_key and anchor.norm_key in norm_map:
            return norm_map[anchor.norm_key], "filename_exact"
        if anchor.num_key and anchor.num_key in num_map:
            return num_map[anchor.num_key], "number_key"

        should_sequence = anchor.index < len(items) and not (anchor.num_key and target_has_numbers)
        if should_sequence:
            return items[anchor.index], "sequence"

        fallback, method = cls._fallback_item(items, strategy)
        return fallback, method

    @classmethod
    def _build_alignment(cls, groups, roles, strategy, max_prompt_count=0):
        anchors = groups["A"]
        if not anchors:
            raise ValueError("检测到 B/C/D 组有图片，但 A组没有图片。图像对齐模式必须连接 A组图像或填写 A组文件夹；完全无图时会自动进入文本批量模式。")
        original_anchor_count = len(anchors)
        limit = max(0, int(max_prompt_count or 0))
        if limit > 0:
            anchors = anchors[:limit]

        rows = []
        errors = []
        for anchor in anchors:
            selected = {"A": anchor}
            row_groups = {
                "A": {
                    "role": roles["A"],
                    "match_method": "anchor",
                    "image": anchor.to_public_dict(),
                }
            }
            for group in ("B", "C", "D"):
                items = groups.get(group) or []
                match, method = cls._match_item(anchor, items, strategy)
                selected[group] = match
                row_groups[group] = {
                    "role": roles[group],
                    "match_method": method,
                    "image": match.to_public_dict() if match else None,
                }
                if items and method == "missing" and strategy == "严格报错":
                    errors.append(f"第 {anchor.index + 1} 项：{group}组找不到与 A={anchor.name} 对齐的图片。")

            rows.append({
                "index": anchor.index + 1,
                "selected": selected,
                "groups": row_groups,
            })

        if errors:
            preview = "\n".join(errors[:10])
            extra = f"\n... 还有 {len(errors) - 10} 个错误" if len(errors) > 10 else ""
            raise ValueError(f"图片智能对齐失败，已按严格策略中止，避免提示词错位：\n{preview}{extra}")

        return rows, original_anchor_count, limit

    @staticmethod
    def _build_row_user_text(meta_instruction, row, total_count, roles):
        lines = [
            (meta_instruction or "").strip(),
            "",
            "【批量配对信息】",
            f"当前处理第 {row['index']}/{total_count} 项。",
        ]
        for group in GROUP_KEYS:
            image = row["groups"][group]["image"]
            role = roles[group]
            if image:
                lines.append(f"{group}组（{role}）：{image['name']}，匹配方式：{row['groups'][group]['match_method']}")
            else:
                lines.append(f"{group}组（{role}）：未提供或已忽略")
        lines.extend([
            "",
            "请只输出当前这一项的最终提示词文本，不要输出编号、标题、Markdown、JSON或解释。",
        ])
        return "\n".join(line for line in lines if line is not None)

    @staticmethod
    @staticmethod
    def _row_image_stats(row):
        metas = []
        for group in GROUP_KEYS:
            item = row["selected"].get(group)
            if item is not None and item.encode_meta:
                metas.append({"group": group, "name": item.name, **item.encode_meta})
        return {
            "image_count": len(metas),
            "total_bytes": sum(int(meta.get("bytes", 0)) for meta in metas),
            "images": metas,
        }

    @staticmethod
    def _build_row_messages(system_role, user_text, row, roles, image_max_side=1024, image_jpeg_quality=85):
        messages = []
        if (system_role or "").strip():
            messages.append({"role": "system", "content": system_role.strip()})

        content = [{"type": "text", "text": user_text}]
        for group in GROUP_KEYS:
            item = row["selected"].get(group)
            if item is None:
                continue
            content.append({"type": "text", "text": f"{group}组（{roles[group]}）：{item.name}"})
            content.append({"type": "image_url", "image_url": {"url": item.to_data_uri(image_max_side, image_jpeg_quality)}})
        messages.append({"role": "user", "content": content})
        return messages

    @staticmethod
    def _build_batch_user_text(meta_instruction, rows, roles):
        lines = [
            (meta_instruction or "").strip(),
            "",
            "【批量配对信息】",
            f"本次共有 {len(rows)} 个任务。请为每个任务各生成 1 条专属提示词。",
        ]
        for row in rows:
            lines.append(f"任务 {row['index']}：")
            for group in GROUP_KEYS:
                image = row["groups"][group]["image"]
                role = roles[group]
                if image:
                    lines.append(f"- {group}组（{role}）：{image['name']}，匹配方式：{row['groups'][group]['match_method']}")
                else:
                    lines.append(f"- {group}组（{role}）：未提供或已忽略")
        lines.extend([
            "",
            "【强制输出格式】",
            "必须只输出一个 JSON 字符串数组。",
            f"数组长度必须严格等于 {len(rows)}。",
            "数组第 1 个元素对应任务 1，第 2 个元素对应任务 2，依此类推。",
            "不要输出 Markdown、编号、解释或 JSON 对象。",
        ])
        return "\n".join(line for line in lines if line is not None)

    @classmethod
    def _build_batch_messages(cls, system_role, user_text, rows, roles, image_max_side=1024, image_jpeg_quality=85):
        messages = []
        if (system_role or "").strip():
            messages.append({"role": "system", "content": system_role.strip()})

        content = [{"type": "text", "text": user_text}]
        for row in rows:
            content.append({"type": "text", "text": f"任务 {row['index']} 开始"})
            for group in GROUP_KEYS:
                item = row["selected"].get(group)
                if item is None:
                    continue
                content.append({"type": "text", "text": f"任务 {row['index']} - {group}组（{roles[group]}）：{item.name}"})
                content.append({"type": "image_url", "image_url": {"url": item.to_data_uri(image_max_side, image_jpeg_quality)}})
            content.append({"type": "text", "text": f"任务 {row['index']} 结束"})
        messages.append({"role": "user", "content": content})
        return messages

    @staticmethod
    def _clean_prompt(text):
        cleaned = _clean_think_tags(text or "")
        cleaned = re.sub(r"^```(?:json|text)?\s*", "", cleaned.strip(), flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned.strip())
        cleaned = re.sub(r"^(?:提示词|Prompt|prompt)\s*[:：]\s*", "", cleaned.strip())
        return cleaned.strip()

    @staticmethod
    def _detect_text_prompt_count(*texts, default_count=1):
        joined = "\n".join(str(text or "") for text in texts)
        patterns = [
            r"(\d{1,3})\s*(?:组|个|条|套|份|段)\s*(?:提示词|prompt|Prompt)?",
            r"(?:生成|输出|写|给我|帮我)\s*(\d{1,3})\s*(?:组|个|条|套|份|段)",
            r"(\d{1,3})\s*(?:prompts?|Prompts?)",
        ]
        for pattern in patterns:
            match = re.search(pattern, joined)
            if match:
                return max(1, min(100, int(match.group(1))))

        chinese_match = re.search(r"([一二两三四五六七八九十]{1,3})\s*(?:组|个|条|套|份|段)", joined)
        if chinese_match:
            value = _chinese_number_to_int(chinese_match.group(1))
            if value:
                return max(1, min(100, value))

        return max(1, min(100, int(default_count or 1)))

    @classmethod
    def _extract_prompt_list(cls, response_text, expected_count):
        cleaned = _clean_think_tags(response_text or "").strip()
        candidates = [cleaned]

        fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.IGNORECASE | re.DOTALL)
        if fence_match:
            candidates.insert(0, fence_match.group(1).strip())

        array_match = re.search(r"\[[\s\S]*\]", cleaned)
        if array_match:
            candidates.insert(0, array_match.group(0))

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
            except Exception:
                continue
            if isinstance(parsed, dict):
                for key in ("prompts", "提示词", "list", "items", "data"):
                    value = parsed.get(key)
                    if isinstance(value, list):
                        parsed = value
                        break
            if isinstance(parsed, list):
                prompts = [cls._clean_prompt(str(item)) for item in parsed if str(item).strip()]
                if prompts:
                    return prompts[:expected_count]

        lines = []
        for line in re.split(r"\r?\n+", cleaned):
            line = _strip_list_prefix(line)
            if not line:
                continue
            if line in ("[", "]", "{", "}"):
                continue
            line = line.rstrip(",")
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            lines.append(cls._clean_prompt(line))
        return [line for line in lines if line][:expected_count]

    def _call_llm_for_row(self, api_key, model, system_role, user_text, row, roles, params):
        started_encode = time.time()
        messages = self._build_row_messages(
            system_role,
            user_text,
            row,
            roles,
            params.get("image_max_side", 1024),
            params.get("image_jpeg_quality", 85),
        )
        encode_elapsed = time.time() - started_encode
        image_stats = self._row_image_stats(row)
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": int(params["max_tokens"]),
            "temperature": float(params["temperature"]),
            "top_p": float(params["top_p"]),
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "reasoning_effort": params["reasoning_effort"] or "none",
        }
        payload.update(params["extra_params"])

        started_request = time.time()
        result = self._post_json_with_retry(payload, api_key, int(params["timeout"]))
        request_elapsed = time.time() - started_request
        response_text = self._clean_prompt(self._extract_text(result))
        if not response_text:
            raise RuntimeError("RH LLM 返回内容为空。")
        timing = {
            "encode_seconds": round(encode_elapsed, 3),
            "request_seconds": round(request_elapsed, 3),
            "image_stats": image_stats,
        }
        return response_text, result, timing

    def _call_llm_for_image_batch(self, api_key, model, system_role, meta_instruction, rows, roles, params):
        user_text = self._build_batch_user_text(meta_instruction, rows, roles)
        started_encode = time.time()
        messages = self._build_batch_messages(
            system_role,
            user_text,
            rows,
            roles,
            params.get("image_max_side", 1024),
            params.get("image_jpeg_quality", 85),
        )
        encode_elapsed = time.time() - started_encode
        image_stats = [self._row_image_stats(row) for row in rows]
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": int(params["max_tokens"]),
            "temperature": float(params["temperature"]),
            "top_p": float(params["top_p"]),
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "reasoning_effort": params["reasoning_effort"] or "none",
        }
        payload.update(params["extra_params"])

        start_time = time.time()
        result = self._post_json_with_retry(payload, api_key, int(params["timeout"]))
        elapsed_time = time.time() - start_time
        response_text = _clean_think_tags(self._extract_text(result))
        prompts = self._extract_prompt_list(response_text, len(rows))
        if len(prompts) != len(rows):
            raise RuntimeError(
                f"单次批量请求要求返回 {len(rows)} 条提示词，但只解析到 {len(prompts)} 条。"
                "可以改用“并发逐条请求”，或提高最大输出令牌。"
            )
        timing = {
            "encode_seconds": round(encode_elapsed, 3),
            "request_seconds": round(elapsed_time, 3),
            "image_count": sum(item["image_count"] for item in image_stats),
            "total_bytes": sum(item["total_bytes"] for item in image_stats),
            "rows": image_stats,
        }
        return prompts, result, response_text, elapsed_time, timing

    def _run_image_row_task(self, row, total_count, api_key, model, system_role, meta_instruction, roles, params, retry_count):
        last_error = None
        last_traceback = ""
        user_text = self._build_row_user_text(meta_instruction, row, total_count, roles)
        started_at = time.time()
        for attempt in range(retry_count + 1):
            try:
                prompt, raw, timing = self._call_llm_for_row(api_key, model, system_role, user_text, row, roles, params)
                elapsed_time = time.time() - started_at
                return {
                    "index": row["index"],
                    "ok": True,
                    "prompt": prompt,
                    "response": raw,
                    "attempts": attempt + 1,
                    "elapsed_seconds": round(elapsed_time, 3),
                    "timing": timing,
                    "error": "",
                }
            except Exception as e:
                last_error = e
                last_traceback = traceback.format_exc()
                if attempt < retry_count:
                    _log_info(f"第 {row['index']} 项第 {attempt + 1} 次失败，准备重试：{e}")
                    time.sleep(min(8, 1 + attempt * 2))

        return {
            "index": row["index"],
            "ok": False,
            "prompt": "",
            "response": None,
            "attempts": retry_count + 1,
            "elapsed_seconds": round(time.time() - started_at, 3),
            "timing": {},
            "error": str(last_error),
            "traceback": last_traceback,
        }

    def _generate_text_only_prompts(self, api_key, model, system_role, meta_instruction, params, default_count, cache_seed):
        prompt_count = self._detect_text_prompt_count(system_role, meta_instruction, default_count=default_count)
        user_text = "\n".join([
            (meta_instruction or "").strip(),
            "",
            "【输出要求】",
            f"请生成 {prompt_count} 条彼此不同的提示词。",
            "必须只输出一个 JSON 字符串数组，格式为：[\"提示词1\", \"提示词2\", ...]。",
            f"数组长度必须严格等于 {prompt_count}。",
            "每个数组元素是一条可以直接给下游图像生成模型使用的完整提示词。",
            "不要输出 Markdown、编号、解释或 JSON 对象。",
        ]).strip()
        final_system_role = "\n\n".join(part for part in [system_role.strip(), TEXT_ONLY_SYSTEM_HINT] if part)
        payload = {
            "model": model,
            "messages": self._build_messages(final_system_role, user_text, [], None),
            "max_tokens": int(params["max_tokens"]),
            "temperature": float(params["temperature"]),
            "top_p": float(params["top_p"]),
            "presence_penalty": 0,
            "frequency_penalty": 0,
            "reasoning_effort": params["reasoning_effort"] or "none",
        }
        payload.update(params["extra_params"])

        start_time = time.time()
        result = self._post_json_with_retry(payload, api_key, int(params["timeout"]))
        response_text = _clean_think_tags(self._extract_text(result))
        prompts = self._extract_prompt_list(response_text, prompt_count)
        if len(prompts) != prompt_count:
            raise RuntimeError(
                f"无图文本模式要求输出 {prompt_count} 条提示词，但只解析到 {len(prompts)} 条。"
                "请在元指令中要求输出 JSON 字符串数组，或提高最大输出令牌。"
            )

        elapsed_time = time.time() - start_time
        full_response = {
            "mode": "text_only",
            "prompts": prompts,
            "raw_response": result,
            "parsed_text": response_text,
            "prompt_count": prompt_count,
            "count_source": "text_auto_or_default",
        }
        info = "\n".join([
            "✅ RH 批量 LLM 提示词完成",
            "🧭 模式：无图文本批量生成",
            f"🤖 模型ID：{model}",
            f"📝 提示词数量：{prompt_count}",
            "🖼️ 图像输入数量：A=0，B=0，C=0，D=0",
            f"🌡️ 温度：{params['temperature']}",
            f"📝 最大输出令牌：{params['max_tokens']}",
            f"🎲 Top_P：{params['top_p']}",
            f"🧠 推理强度：{params['reasoning_effort']}",
            f"🎲 随机种：{cache_seed}（仅用于 ComfyUI 缓存控制）",
            f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
        ])
        return prompts, json.dumps(full_response, ensure_ascii=False, indent=2), info

    def generate_batch_prompts(self, **kwargs):
        api_key = self._text_input_value(kwargs, "🔑 API密钥", "").strip()
        model = self._text_input_value(kwargs, "🤖 模型ID", DEFAULT_MODEL).strip()
        system_role = self._text_input_value(kwargs, "🎯 系统角色", "")
        meta_instruction = self._text_input_value(kwargs, "🧾 元指令", "")
        strategy = self._text_input_value(kwargs, "🧩 缺失处理策略", "严格报错")
        cache_seed = self._int_input_value(kwargs, "🎲 随机种", 0)
        text_only_default_count = self._int_input_value(kwargs, "🔢 无图默认数量", 1)
        image_mode_max_prompts = self._int_input_value(kwargs, "🛡️ 多图模式最大提示词数量", 0)
        image_inference_mode = self._text_input_value(kwargs, "🚦 多图推理模式", "并发逐条请求")
        concurrency = max(1, min(20, self._int_input_value(kwargs, "🚀 并发数", 4)))
        retry_count = max(0, min(5, self._int_input_value(kwargs, "🛟 失败重试次数", 1)))
        task_failure_strategy = self._text_input_value(kwargs, "🧪 推理失败策略", "失败占位继续")
        image_max_side = max(256, min(4096, self._int_input_value(kwargs, "🖼️ 发送图片最长边", 1024)))
        image_jpeg_quality = max(40, min(100, self._int_input_value(kwargs, "🗜️ 发送图片JPEG质量", 85)))

        if not api_key:
            raise ValueError("API密钥为空，请填写 RunningHub LLM API Key 后再试。")
        if not model:
            raise ValueError("模型ID为空，请填写有效模型ID。")
        if strategy not in MISSING_STRATEGIES:
            strategy = "严格报错"
        if task_failure_strategy not in TASK_FAILURE_STRATEGIES:
            task_failure_strategy = "失败占位继续"
        if image_inference_mode not in IMAGE_INFERENCE_MODES:
            image_inference_mode = "并发逐条请求"

        roles = dict(DEFAULT_GROUP_ROLES)
        params = {
            "temperature": self._float_input_value(kwargs, "🌡️ 温度", 0.7),
            "max_tokens": self._int_input_value(kwargs, "📝 最大输出令牌", 2048),
            "top_p": self._float_input_value(kwargs, "🎲 Top_P", 1.0),
            "reasoning_effort": self._text_input_value(kwargs, "🧠 推理强度", "none"),
            "timeout": self._int_input_value(kwargs, "⏱️ 超时时间", 180),
            "extra_params": self._load_extra_params(self._text_input_value(kwargs, "➕ 额外参数JSON", "{}")),
            "image_max_side": image_max_side,
            "image_jpeg_quality": image_jpeg_quality,
        }

        start_time = time.time()
        groups = {}
        source_report = {}
        for group in GROUP_KEYS:
            groups[group], source_report[group] = self._collect_group_items(kwargs, group)

        has_any_images = any(groups[group] for group in GROUP_KEYS)
        if not has_any_images:
            return self._generate_text_only_prompts(
                api_key,
                model,
                system_role,
                meta_instruction,
                params,
                text_only_default_count,
                cache_seed,
            )

        rows, original_anchor_count, image_mode_limit = self._build_alignment(groups, roles, strategy, image_mode_max_prompts)
        total_count = len(rows)
        prompts = [""] * total_count
        raw_responses = [None] * total_count
        task_results = [None] * total_count

        if image_inference_mode == "单次批量请求":
            _log_info(f"开始单次批量请求生成提示词：模型 {model}，任务 {total_count} 条，缺失策略 {strategy}")
            batch_prompts, raw, parsed_text, request_elapsed, batch_timing = self._call_llm_for_image_batch(
                api_key,
                model,
                system_role,
                meta_instruction,
                rows,
                roles,
                params,
            )
            prompts = batch_prompts
            raw_responses = [{"index": "batch", "response": raw, "parsed_text": parsed_text, "timing": batch_timing}]
            for index, row in enumerate(rows):
                row["prompt"] = prompts[index]
                row["error"] = ""
                row["attempts"] = 1
                row["elapsed_seconds"] = round(request_elapsed, 3)
                row["timing"] = batch_timing.get("rows", [{}])[index] if index < len(batch_timing.get("rows", [])) else {}
                task_results[index] = {
                    "index": row["index"],
                    "ok": True,
                    "prompt": prompts[index],
                    "attempts": 1,
                    "elapsed_seconds": round(request_elapsed, 3),
                    "timing": row["timing"],
                    "error": "",
                }
            concurrency = 1
            success_count = total_count
            failed_count = 0
        else:
            concurrency = min(concurrency, total_count)
            _log_info(f"开始并发逐条生成提示词：模型 {model}，任务 {total_count} 条，并发 {concurrency}，缺失策略 {strategy}")
            abort_error = None
            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                future_map = {
                    executor.submit(
                        self._run_image_row_task,
                        row,
                        total_count,
                        api_key,
                        model,
                        system_role,
                        meta_instruction,
                        roles,
                        params,
                        retry_count,
                    ): row
                    for row in rows
                }

                for future in as_completed(future_map):
                    row = future_map[future]
                    index = row["index"] - 1
                    try:
                        result = future.result()
                    except Exception as e:
                        result = {
                            "index": row["index"],
                            "ok": False,
                            "prompt": "",
                            "response": None,
                            "attempts": retry_count + 1,
                            "elapsed_seconds": None,
                            "timing": {},
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        }
                    task_results[index] = result
                    row["prompt"] = result.get("prompt", "")
                    row["error"] = result.get("error", "")
                    row["attempts"] = result.get("attempts", 1)
                    row["elapsed_seconds"] = result.get("elapsed_seconds")
                    row["timing"] = result.get("timing", {})

                    if result.get("ok"):
                        prompts[index] = result["prompt"]
                        raw_responses[index] = {"index": row["index"], "response": result.get("response")}
                        _log_info(f"第 {row['index']}/{total_count} 项完成，提示词长度 {len(result['prompt'])}，尝试 {result.get('attempts')} 次，耗时 {result.get('elapsed_seconds')} 秒")
                    else:
                        _log_error(f"第 {row['index']} 项失败：{result.get('error')}")
                        if result.get("traceback"):
                            _log_error(result["traceback"])
                        if task_failure_strategy == "任一失败中断":
                            abort_error = result
                            for pending in future_map:
                                pending.cancel()
                            break
                        if task_failure_strategy == "失败占位继续":
                            prompts[index] = f"ERROR: 第 {row['index']} 项提示词生成失败：{result.get('error')}"

            if abort_error:
                raise RuntimeError(f"第 {abort_error['index']}/{total_count} 项 LLM 提示词生成失败，已按策略中断：{abort_error.get('error')}")

            if task_failure_strategy == "跳过失败继续":
                prompts = [
                    result.get("prompt", "")
                    for result in task_results
                    if result and result.get("ok") and result.get("prompt")
                ]

            raw_responses = [item for item in raw_responses if item is not None]
            success_count = sum(1 for result in task_results if result and result.get("ok"))
            failed_count = sum(1 for result in task_results if result and not result.get("ok"))

        elapsed_time = time.time() - start_time
        alignment_report = {
            "status": "success",
            "node": NODE_NAME,
            "model": model,
            "prompt_count": len(prompts),
            "task_count": total_count,
            "success_count": success_count,
            "failed_count": failed_count,
            "image_inference_mode": image_inference_mode,
            "concurrency": concurrency,
            "retry_count": retry_count,
            "task_failure_strategy": task_failure_strategy,
            "image_max_side": image_max_side,
            "image_jpeg_quality": image_jpeg_quality,
            "original_anchor_count": original_anchor_count,
            "image_mode_max_prompt_count": image_mode_limit,
            "truncated_by_limit": bool(image_mode_limit > 0 and original_anchor_count > len(prompts)),
            "anchor_group": "A",
            "missing_strategy": strategy,
            "roles": roles,
            "sources": source_report,
            "cache_seed": cache_seed,
            "elapsed_seconds": round(elapsed_time, 3),
            "rows": [
                {
                    "index": row["index"],
                    "groups": row["groups"],
                    "prompt": row.get("prompt", ""),
                    "prompt_length": len(row.get("prompt", "")),
                    "attempts": row.get("attempts", 1),
                    "elapsed_seconds": row.get("elapsed_seconds"),
                    "timing": row.get("timing", {}),
                    "error": row.get("error", ""),
                }
                for row in rows
            ],
        }
        full_response = {
            "prompts": prompts,
            "alignment_report": alignment_report,
            "raw_responses": raw_responses,
            "task_results": [
                {key: value for key, value in (result or {}).items() if key != "response"}
                for result in task_results
            ],
        }
        info_lines = [
            "✅ RH 批量 LLM 提示词完成",
            f"🤖 模型ID：{model}",
            f"📝 提示词数量：{len(prompts)}",
            f"🔢 实际任务数量：{total_count}",
            f"🚦 多图推理模式：{image_inference_mode}",
            f"🚀 并发数：{concurrency}",
            f"🛟 失败重试次数：{retry_count}",
            f"🧪 推理失败策略：{task_failure_strategy}",
            f"✅ 成功任务：{success_count}",
            f"❌ 失败任务：{failed_count}",
            f"🖼️ 发送图片最长边：{image_max_side}",
            f"🗜️ 发送图片JPEG质量：{image_jpeg_quality}",
            f"🛡️ 多图模式最大提示词数量：{image_mode_limit if image_mode_limit > 0 else '不限制'}",
            f"⚓ A组原始数量：{original_anchor_count}",
            f"⚓ 锚点组：A组",
            f"🧩 缺失处理策略：{strategy}",
            f"🖼️ 图像输入数量：A={source_report['A']['count']}，B={source_report['B']['count']}，C={source_report['C']['count']}，D={source_report['D']['count']}",
            f"🌡️ 温度：{params['temperature']}",
            f"📝 最大输出令牌：{params['max_tokens']}",
            f"🎲 Top_P：{params['top_p']}",
            f"🧠 推理强度：{params['reasoning_effort']}",
            f"🎲 随机种：{cache_seed}（仅用于 ComfyUI 缓存控制）",
            f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
        ]
        info_lines.append("📋 对齐明细：")
        for row in rows:
            parts = []
            for group in GROUP_KEYS:
                image = row["groups"][group]["image"]
                method = row["groups"][group]["match_method"]
                parts.append(f"{group}={image['name'] if image else '空'}({method})")
            timing = row.get("timing") or {}
            timing_text = ""
            if "image_stats" in timing:
                stats = timing.get("image_stats") or {}
                size_kb = int(stats.get("total_bytes", 0)) / 1024
                timing_text = f"，图片 {stats.get('image_count', 0)} 张/{size_kb:.1f}KB，请求 {timing.get('request_seconds', '未知')}秒"
            elif "total_bytes" in timing:
                size_kb = int(timing.get("total_bytes", 0)) / 1024
                timing_text = f"，图片 {timing.get('image_count', 0)} 张/{size_kb:.1f}KB"
            info_lines.append(f"#{row['index']} " + "，".join(parts) + timing_text)

        return (
            prompts,
            json.dumps(full_response, ensure_ascii=False, indent=2),
            "\n".join(info_lines),
        )


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHBatchLLMPromptNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🐠RH批量LLM提示词@炮老师的小课堂",
}
