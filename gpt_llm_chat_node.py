"""Independent GPT LLM chat node for the dapaoAI relay."""

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


API_BASE_URL = "https://api.dapaoai.com"
CHAT_ENDPOINT = f"{API_BASE_URL}/v1/chat/completions"
NODE_NAME = "DapaoGPTLLMChatNode"
NODE_CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
DISPLAY_NAME = "🐠GPT-LLM智能对话@炮老师的小课堂"
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


def _safe_print(message):
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        printable = str(message).encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(printable)


def _log_info(message):
    _safe_print(f"[dapaoAPI-GPT-LLM智能对话] 信息：{message}")


def _log_error(message):
    _safe_print(f"[dapaoAPI-GPT-LLM智能对话] 错误：{message}")


def _parse_extra_json(value):
    try:
        data = json.loads((value or "{}").strip() or "{}")
    except json.JSONDecodeError as error:
        raise ValueError(f"额外参数JSON格式错误：{error}") from error
    if not isinstance(data, dict):
        raise ValueError("额外参数JSON必须是 JSON 对象。")
    return data


def _response_error(response):
    text = response.text[:1200]
    try:
        data = response.json()
    except Exception:
        return text
    if not isinstance(data, dict):
        return text
    error = data.get("error")
    if isinstance(error, dict):
        return str(error.get("message") or error.get("type") or error.get("code") or text)
    return str(data.get("message") or data.get("msg") or error or text)


class DapaoGPTLLMAPIError(RuntimeError):
    def __init__(self, status_code, message):
        self.status_code = int(status_code)
        self.api_message = str(message)
        labels = {
            400: "请求参数错误",
            401: "认证失败，请检查 API 密钥",
            402: "余额不足，请充值后重试",
            403: "没有模型或接口权限",
            404: "接口或映射模型不存在",
            429: "请求过频，请稍后重试",
        }
        label = labels.get(self.status_code, "中转站请求失败")
        super().__init__(f"{label} {self.status_code}：{self.api_message}")


def _tensor_to_data_uris(image_tensor):
    data_uris = []
    for index in range(image_tensor.shape[0]):
        array = np.clip(image_tensor[index].detach().cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        image = Image.fromarray(array).convert("RGB")
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        data_uris.append(f"data:image/png;base64,{encoded}")
    return data_uris


def _sanitized_result(value):
    if isinstance(value, dict):
        cleaned = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if normalized in {"data", "b64_json", "base64", "image_base64"} and isinstance(item, str) and len(item) > 200:
                cleaned[key] = f"<Base64已省略，共{len(item)}字符>"
            else:
                cleaned[key] = _sanitized_result(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitized_result(item) for item in value]
    if isinstance(value, str) and value.startswith("data:") and len(value) > 200:
        return f"<Data URI已省略，共{len(value)}字符>"
    return value


class DapaoGPTLLMClient:
    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, payload):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/GPTLLMChat",
        }
        try:
            response = requests.post(CHAT_ENDPOINT, headers=headers, json=payload, timeout=self.timeout)
        except (requests.ConnectionError, requests.Timeout) as error:
            raise RuntimeError(f"{friendly_network_error(error, '提交对话请求')} 对话请求不会自动重试，以免重复扣费。") from error
        if response.status_code >= 400:
            if response.status_code == 443:
                raise RuntimeError(friendly_443_status())
            raise DapaoGPTLLMAPIError(response.status_code, _response_error(response))
        try:
            return response.json()
        except json.JSONDecodeError as error:
            raise RuntimeError(f"中转站返回内容不是 JSON：{response.text[:500]}") from error


def _content_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    texts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text") or item.get("output_text")
        if isinstance(text, dict):
            text = text.get("value") or text.get("text")
        if text:
            texts.append(str(text))
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

    output_text = result.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text
    output = result.get("output")
    if isinstance(output, list):
        texts = []
        for item in output:
            if not isinstance(item, dict):
                continue
            text = _content_text(item.get("content"))
            if text:
                texts.append(text)
        if texts:
            return "\n".join(texts)
    return ""


def _extract_tool_calls(result):
    if not isinstance(result, dict):
        return None
    choices = result.get("choices")
    if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
        return None
    message = choices[0].get("message")
    return message.get("tool_calls") if isinstance(message, dict) else None


class DapaoGPTLLMChatNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {
            "📋 额外参数JSON": (
                "STRING",
                {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": '{"response_format":{"type":"json_object"}}',
                    "tooltip": "补充 OpenAI 兼容请求参数；不能覆盖模型、消息和节点核心采样参数。",
                },
            ),
            "🚫 出错时跳过": (
                "BOOLEAN",
                {
                    "default": False,
                    "tooltip": "开启后接口错误不会中断工作流，而是将错误信息作为文本输出。",
                },
            ),
        }
        for index in range(1, 9):
            optional[f"🖼️ 图像{index}"] = ("IMAGE", {"tooltip": "可选多模态参考图，最多8个输入接口。"})
        return {
            "required": {
                "🔑 API密钥": (
                    "STRING",
                    {
                        "default": "",
                        "placeholder": "填入 dapaoAI API 密钥",
                        "tooltip": "密钥只用于请求 https://api.dapaoai.com，不会写入配置文件。",
                    },
                ),
                "🤖 模型": (MODEL_OPTIONS, {"default": "gemini-3.7-flash"}),
                "🎯 系统角色": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "你是一个专业、友好、准确的 AI 助手。",
                        "placeholder": "定义 AI 的角色和行为方式……",
                    },
                ),
                "💬 用户输入": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "你好，请帮我分析这段内容。",
                        "placeholder": "输入你的问题或指令……",
                    },
                ),
                "🌡️ 温度": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.01}),
                "📝 最大输出令牌": ("INT", {"default": 2048, "min": 1, "max": 65536, "step": 1}),
                "🎲 Top_P": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01}),
                "🎲 随机种": (
                    "INT",
                    {
                        "default": 0,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": "randomize",
                        "tooltip": "仅控制 ComfyUI 缓存，不发送给接口。",
                    },
                ),
                "⌛ 请求超时": ("INT", {"default": 300, "min": 30, "max": 1200, "step": 10}),
            },
            "optional": optional,
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "📄 完整响应", "ℹ️ 处理信息")
    FUNCTION = "chat"
    CATEGORY = NODE_CATEGORY
    DESCRIPTION = "GPT-LLM 智能对话：支持文本与最多8路图像输入，通过 dapaoAI OpenAI 兼容接口调用"

    @staticmethod
    def _collect_images(kwargs):
        image_uris = []
        for index in range(1, 9):
            image = kwargs.get(f"🖼️ 图像{index}")
            if image is not None:
                image_uris.extend(_tensor_to_data_uris(image))
        return image_uris

    @staticmethod
    def _build_messages(system_role, user_input, image_uris):
        messages = []
        if system_role:
            messages.append({"role": "system", "content": system_role})
        if image_uris:
            content = [{"type": "text", "text": user_input}]
            content.extend({"type": "image_url", "image_url": {"url": uri}} for uri in image_uris)
            messages.append({"role": "user", "content": content})
        else:
            messages.append({"role": "user", "content": user_input})
        return messages

    async def chat(self, **kwargs):
        return await asyncio.to_thread(self._chat_sync, **kwargs)

    def _chat_sync(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model_id = kwargs.get("🤖 模型", "gemini-3.7-flash")
        system_role = (kwargs.get("🎯 系统角色") or "").strip()
        user_input = (kwargs.get("💬 用户输入") or "").strip()
        skip_error = bool(kwargs.get("🚫 出错时跳过", False))
        result = {}

        try:
            if not api_key:
                raise ValueError("请填写 dapaoAI API 密钥。")
            if model_id not in MODEL_OPTIONS:
                raise ValueError(f"不支持的映射模型：{model_id}")
            if not user_input:
                raise ValueError("用户输入不能为空。")

            image_uris = self._collect_images(kwargs)
            messages = self._build_messages(system_role, user_input, image_uris)
            payload = {
                "model": model_id,
                "messages": messages,
                "temperature": float(kwargs.get("🌡️ 温度", 0.7)),
                "max_tokens": int(kwargs.get("📝 最大输出令牌", 2048)),
                "top_p": float(kwargs.get("🎲 Top_P", 1.0)),
                "stream": False,
            }
            extra = _parse_extra_json(kwargs.get("📋 额外参数JSON", "{}"))
            protected = {"model", "messages", "temperature", "max_tokens", "top_p", "stream"}
            conflicts = sorted(set(extra).intersection(protected))
            if conflicts:
                raise ValueError(f"额外参数JSON不能覆盖节点核心参数：{', '.join(conflicts)}")
            payload.update(extra)

            _log_info(f"提交对话：relay={API_BASE_URL}，model={model_id}，参考图={len(image_uris)}张")
            started = time.time()
            result = DapaoGPTLLMClient(api_key, int(kwargs.get("⌛ 请求超时", 300))).chat(payload)
            text = _extract_text(result)
            if not text:
                tool_calls = _extract_tool_calls(result)
                text = json.dumps(tool_calls, ensure_ascii=False, indent=2) if tool_calls else ""
            if not text:
                raise RuntimeError("模型返回内容为空。")

            usage = result.get("usage", {}) if isinstance(result, dict) else {}
            input_tokens = usage.get("prompt_tokens", usage.get("input_tokens", "未知"))
            output_tokens = usage.get("completion_tokens", usage.get("output_tokens", "未知"))
            total_tokens = usage.get("total_tokens", "未知")
            info = (
                "✅ GPT-LLM 智能对话完成\n"
                f"🌐 中转站：{API_BASE_URL}\n"
                f"🤖 模型：{model_id}\n"
                f"🖼️ 图像：{len(image_uris)} 张\n"
                f"📥 输入令牌：{input_tokens}\n"
                f"📤 输出令牌：{output_tokens}\n"
                f"📊 总令牌：{total_tokens}\n"
                f"⏱️ 耗时：{time.time() - started:.2f} 秒"
            )
            return text, json.dumps(_sanitized_result(result), ensure_ascii=False, indent=2), info
        except Exception as error:
            message = f"❌ GPT-LLM 智能对话失败：{error}"
            _log_error(message)
            _log_error(traceback.format_exc())
            error_json = json.dumps({"error": str(error), "response": _sanitized_result(result)}, ensure_ascii=False, indent=2)
            if skip_error:
                return message, error_json, message
            raise RuntimeError(message) from error


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoGPTLLMChatNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}


__all__ = [
    "DapaoGPTLLMChatNode",
    "MODEL_OPTIONS",
    "NODE_CLASS_MAPPINGS",
    "NODE_DISPLAY_NAME_MAPPINGS",
]
