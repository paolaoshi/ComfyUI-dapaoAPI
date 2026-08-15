"""Dedicated MiniMax H3 prompt editor with stable reference metadata."""

import json
import re


NODE_NAME = "DapaoH3PromptBoxNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮API常用工具🍬"
DISPLAY_NAME = "🧙‍♂️H3专用提示词框@炮老师的小课堂"
REFERENCE_TYPE = "DAPAO_H3_REFERENCES"

_TOKEN_PATTERN = re.compile(r"<(Picture|Video|Audio)\s+(\d+)>")
_REFERENCE_LIKE_PATTERN = re.compile(r"<\s*(?:Picture|Video|Audio)[^>]*>", re.IGNORECASE)
_LIMITS = {"Picture": 9, "Video": 3, "Audio": 6}


def _parse_manifest(value):
    if not value:
        return {"version": 1, "mode": "T2VA", "target": "", "items": []}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError("H3素材清单格式无效，请重新连接或刷新官方H3节点。") from error
    if not isinstance(value, dict) or not isinstance(value.get("items"), list):
        raise ValueError("H3素材清单缺少有效items字段。")

    items = []
    expected_index = {"Picture": 1, "Video": 1, "Audio": 1}
    for raw in value["items"]:
        if not isinstance(raw, dict):
            raise ValueError("H3素材清单包含无效项目。")
        kind = str(raw.get("kind") or "")
        index = raw.get("index")
        if kind not in _LIMITS or not isinstance(index, int):
            raise ValueError("H3素材清单包含未知素材类型或编号。")
        if index != expected_index[kind] or index > _LIMITS[kind]:
            raise ValueError(f"H3素材清单中的{kind}编号不连续或超出官方上限。")
        expected_index[kind] += 1
        token = f"<{kind} {index}>"
        if raw.get("token") not in (None, token):
            raise ValueError(f"H3素材标记必须使用官方格式：{token}")
        items.append({
            "kind": kind,
            "index": index,
            "token": token,
            "label": str(raw.get("label") or token),
            "source_input": str(raw.get("source_input") or ""),
        })

    mode = str(value.get("mode") or "T2VA")
    if mode not in {"T2VA", "I2VA", "FL2VA", "L2VA", "Ref2VA"}:
        raise ValueError(f"未知H3模式：{mode}")
    return {
        "version": 1,
        "mode": mode,
        "target": str(value.get("target") or ""),
        "items": items,
    }


class DapaoH3PromptBoxNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "📝 H3提示词": (
                    "STRING",
                    {
                        "multiline": True,
                        "dynamicPrompts": True,
                        "default": "",
                        "placeholder": "输入提示词；键入 @ 选择官方H3节点已连接的素材……",
                    },
                ),
                "🧩 H3素材清单": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "由节点界面根据下游官方MiniMax H3节点自动维护。",
                    },
                ),
            }
        }

    RETURN_TYPES = ("STRING", REFERENCE_TYPE)
    RETURN_NAMES = ("📝 H3提示词", "🧩 H3素材标记")
    FUNCTION = "build_prompt"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "为MiniMax H3编写带官方<Picture/Video/Audio N>素材标记的提示词。"

    def build_prompt(self, **kwargs):
        text = str(kwargs.get("📝 H3提示词") or "").strip()
        manifest = _parse_manifest(kwargs.get("🧩 H3素材清单"))
        allowed = {item["token"] for item in manifest["items"]}
        used = {match.group(0) for match in _TOKEN_PATTERN.finditer(text)}
        malformed = sorted(set(_REFERENCE_LIKE_PATTERN.findall(text)) - used)
        if malformed:
            raise ValueError(
                "H3素材标记格式不正确，请使用<Picture 1>、<Video 1>、<Audio 1>格式："
                + "、".join(malformed)
            )
        unknown = sorted(used - allowed)
        if unknown:
            raise ValueError("提示词引用了当前官方H3节点未连接的素材：" + "、".join(unknown))
        return text, manifest


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoH3PromptBoxNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoH3PromptBoxNode",
    "REFERENCE_TYPE",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
