import base64
import io
import json
import time
import traceback

import numpy as np
import requests
from PIL import Image


NODE_NAME = "DapaoAPImartMultimodalChatNode"


def _tensor_to_data_uri(image):
    image_np = np.clip(image[0].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
    pil_image = Image.fromarray(image_np).convert("RGB")
    buffer = io.BytesIO()
    pil_image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")


class DapaoAPImartMultimodalChatNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "你是一个专业、友好、乐于助人的 AI 助手，能够结合用户提供的文字与图像进行准确分析和回答。",
                    "placeholder": "定义 AI 的角色和行为方式..."
                }),
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "请根据我提供的内容进行分析并给出详细回答。",
                    "placeholder": "输入你的问题或指令..."
                }),
                "🤖 模型ID": ("STRING", {
                    "default": "gpt-5.4-mini",
                    "multiline": False,
                    "placeholder": "手动输入模型 ID，如 gpt-5.4-mini"
                }),
                "🌐 API供应商": (["APImart", "自定义"], {
                    "default": "APImart",
                    "tooltip": "默认走 APImart Responses API；自定义用于兼容其他 OpenAI Responses 风格接口。"
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "请输入 API 密钥"
                }),
                "📊 输出语言": (["中文", "英文"], {
                    "default": "中文"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🔗 自定义API地址": ("STRING", {
                    "default": "",
                    "placeholder": "默认 https://api.apimart.ai/v1/responses；自定义时可填完整地址或基础域名"
                }),
                "🌡️ 温度": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01
                }),
                "🎲 Top_P": ("FLOAT", {
                    "default": 0.9,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "📝 最大输出令牌": ("INT", {
                    "default": 4096,
                    "min": 1,
                    "max": 65536
                }),
                "⏱️ 超时时间": ("INT", {
                    "default": 180,
                    "min": 30,
                    "max": 1200,
                    "step": 10
                }),
                "♻️ 最大重试次数": ("INT", {
                    "default": 2,
                    "min": 0,
                    "max": 5,
                    "step": 1
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "📄 完整响应", "ℹ️ 处理信息")
    FUNCTION = "chat"
    CATEGORY = "🤖dapaoAPI/🐦‍🔥GPT&gemini&即梦最新稳定🐦‍🔥"
    DESCRIPTION = "多模态智能对话：APImart Responses API，支持文本和 4 图分析 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _get_api_url(api_provider, custom_api_url):
        if api_provider == "APImart":
            return "https://api.apimart.ai/v1/responses"

        url = (custom_api_url or "").strip()
        if not url:
            raise ValueError("选择 自定义 API供应商 时，请填写 🔗 自定义API地址。")
        if not url.startswith(("http://", "https://")):
            raise ValueError("🔗 自定义API地址 需要以 http:// 或 https:// 开头。")
        url = url.rstrip("/")
        if url.endswith("/v1/responses") or url.endswith("/responses"):
            return url
        if url.endswith("/v1"):
            return f"{url}/responses"
        return f"{url}/v1/responses"

    @staticmethod
    def _headers(api_key):
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/APImartMultimodalChat",
        }

    @staticmethod
    def _response_error_message(response):
        text = response.text[:1000]
        try:
            data = response.json()
            error = data.get("error", {}) if isinstance(data, dict) else {}
            if isinstance(error, dict):
                return error.get("message") or error.get("code") or error.get("type") or text
            if isinstance(data, dict):
                return data.get("message") or text
        except Exception:
            pass
        return text

    def _raise_for_response(self, response):
        if response.status_code == 200:
            return
        message = self._response_error_message(response)
        status = response.status_code
        lower_message = str(message).lower()
        if status == 400:
            raise RuntimeError(f"多模态对话参数错误 400：请检查模型ID、提示词、图片或输出参数。接口返回：{message}")
        if status == 401:
            raise RuntimeError(f"多模态对话认证失败 401：API密钥无效或未填写正确。接口返回：{message}")
        if status == 402:
            raise RuntimeError(f"多模态对话余额不足 402：账户余额不足，请充值后再试。接口返回：{message}")
        if status == 403:
            if "quota_not_enough" in lower_message or "insufficient balance" in lower_message:
                raise RuntimeError(f"多模态对话余额不足 403：账户余额不足，请充值后再试。接口返回：{message}")
            raise RuntimeError(f"多模态对话权限不足 403：没有权限访问该模型或资源。接口返回：{message}")
        if status == 429:
            raise RuntimeError(f"多模态对话请求过频 429：请降低频率后重试。接口返回：{message}")
        if status >= 500:
            raise RuntimeError(f"多模态对话服务异常 {status}：服务器或上游暂时不可用。接口返回：{message}")
        raise RuntimeError(f"多模态对话请求失败 {status}：{message}")

    @staticmethod
    def _api_error_message(result):
        if not isinstance(result, dict):
            return "接口返回格式不正确。"
        error = result.get("error")
        if isinstance(error, dict):
            return error.get("message") or error.get("code") or error.get("type") or json.dumps(error, ensure_ascii=False)
        return result.get("message") or json.dumps(result, ensure_ascii=False)[:1000]

    def _raise_for_api_result(self, result):
        if not isinstance(result, dict):
            return
        code = result.get("code")
        if code in (None, 0, 200, "200"):
            return
        message = self._api_error_message(result)
        lower_message = str(message).lower()
        if code in (402, "402") or "quota_not_enough" in lower_message or "insufficient balance" in lower_message:
            raise RuntimeError(f"多模态对话余额不足：账户余额不足，请充值后再试。接口返回：{message}")
        if code in (401, "401"):
            raise RuntimeError(f"多模态对话认证失败：API密钥无效或未填写正确。接口返回：{message}")
        if code in (403, "403"):
            raise RuntimeError(f"多模态对话权限不足：没有权限访问该模型或资源。接口返回：{message}")
        if code in (429, "429"):
            raise RuntimeError(f"多模态对话请求过频：请降低频率后重试。接口返回：{message}")
        raise RuntimeError(f"多模态对话接口返回错误 code={code}：{message}")

    @staticmethod
    def _should_retry(exc):
        if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return True
        text = str(exc)
        return "429" in text or "服务异常" in text or "暂时不可用" in text

    def _request_json_with_retry(self, url, headers, payload, timeout, retry_count):
        last_error = None
        for attempt in range(retry_count + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=timeout)
                self._raise_for_response(response)
                result = response.json()
                self._raise_for_api_result(result)
                return result
            except json.JSONDecodeError as e:
                raise RuntimeError(f"多模态对话接口返回内容不是 JSON：{e}")
            except Exception as e:
                last_error = e
                if attempt >= retry_count or not self._should_retry(e):
                    raise
                time.sleep(min(2 ** attempt, 8))
        raise last_error

    @staticmethod
    def _content_text(content):
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                    if text:
                        texts.append(text)
            return "\n".join(texts)
        return "" if content is None else str(content)

    def _extract_text_from_container(self, container):
        if not isinstance(container, dict):
            return ""

        output_text = container.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text

        output = container.get("output")
        if isinstance(output, list):
            texts = []
            for item in output:
                if not isinstance(item, dict):
                    continue
                content = item.get("content", [])
                if isinstance(content, str):
                    texts.append(content)
                    continue
                for content_item in content or []:
                    if not isinstance(content_item, dict):
                        continue
                    text = content_item.get("text")
                    if text:
                        texts.append(text)
            if texts:
                return "\n".join(texts)

        choices = container.get("choices", [])
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message", {})
                if isinstance(message, dict):
                    text = self._content_text(message.get("content"))
                    if text:
                        return text
                text = first.get("text")
                if text:
                    return text

        for key in ("text", "response", "message"):
            value = container.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return ""

    def _extract_response_text(self, result):
        text = self._extract_text_from_container(result)
        if text:
            return text
        data = result.get("data") if isinstance(result, dict) else None
        if isinstance(data, dict):
            return self._extract_text_from_container(data)
        return ""

    @staticmethod
    def _build_usage_info(result):
        data = result.get("data", {}) if isinstance(result, dict) else {}
        usage = result.get("usage") if isinstance(result, dict) else None
        if not usage and isinstance(data, dict):
            usage = data.get("usage")
        if not isinstance(usage, dict):
            return []

        lines = []
        input_tokens = usage.get("input_tokens") or usage.get("prompt_tokens")
        output_tokens = usage.get("output_tokens") or usage.get("completion_tokens")
        total_tokens = usage.get("total_tokens")
        if input_tokens is not None:
            lines.append(f"📥 输入令牌：{input_tokens}")
        if output_tokens is not None:
            lines.append(f"📤 输出令牌：{output_tokens}")
        if total_tokens is not None:
            lines.append(f"📊 总令牌：{total_tokens}")
        return lines

    def _build_input(self, system_role, user_input, images, language):
        language_instruction = "请用中文回答。" if language == "中文" else "Please answer in English."
        system_text = (system_role or "").strip()
        if system_text:
            system_text = f"{system_text}\n\n{language_instruction}"
        else:
            system_text = language_instruction

        input_items = [{
            "role": "system",
            "content": [{"type": "input_text", "text": system_text}]
        }]

        user_content = []
        if (user_input or "").strip():
            user_content.append({"type": "input_text", "text": user_input.strip()})
        for image in images:
            user_content.append({
                "type": "input_image",
                "image_url": _tensor_to_data_uri(image)
            })

        input_items.append({
            "role": "user",
            "content": user_content
        })
        return input_items

    def chat(self, **kwargs):
        system_role = kwargs.get("🎯 系统角色", "")
        user_input = kwargs.get("💬 用户输入", "")
        model = kwargs.get("🤖 模型ID", "gpt-5.4-mini").strip()
        api_provider = kwargs.get("🌐 API供应商", "APImart")
        api_key = kwargs.get("🔑 API密钥", "").strip()
        language = kwargs.get("📊 输出语言", "中文")
        custom_api_url = kwargs.get("🔗 自定义API地址", "")
        temperature = float(kwargs.get("🌡️ 温度", 0.7))
        top_p = float(kwargs.get("🎲 Top_P", 0.9))
        max_output_tokens = int(kwargs.get("📝 最大输出令牌", 4096))
        timeout = int(kwargs.get("⏱️ 超时时间", 180))
        retry_count = int(kwargs.get("♻️ 最大重试次数", 2))
        images = [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 5) if kwargs.get(f"🖼️ 图像{i}") is not None]

        if not api_key:
            return ("", "{}", "❌ 错误：请填写 🔑 API密钥。")
        if not model:
            return ("", "{}", "❌ 错误：请填写 🤖 模型ID。")
        if not (user_input or "").strip() and not images:
            return ("", "{}", "❌ 错误：请填写 💬 用户输入，或至少接入一张图片。")

        start_time = time.time()
        try:
            api_url = self._get_api_url(api_provider, custom_api_url)
            payload = {
                "model": model,
                "input": self._build_input(system_role, user_input, images, language),
                "temperature": temperature,
                "top_p": top_p,
                "max_output_tokens": max_output_tokens,
            }
            result = self._request_json_with_retry(api_url, self._headers(api_key), payload, timeout, retry_count)
            response_text = self._extract_response_text(result)
            raw_json = json.dumps(result, ensure_ascii=False, indent=2)
            elapsed_time = time.time() - start_time

            info_lines = [
                "✅ 多模态智能对话完成",
                f"🤖 模型ID：{model}",
                f"🌐 API供应商：{api_provider}",
                f"🔗 请求地址：{api_url}",
                f"🖼️ 图像数量：{len(images)}",
                f"📊 输出语言：{language}",
                f"📝 最大输出令牌：{max_output_tokens}",
                f"♻️ 最大重试次数：{retry_count}",
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
            ]
            info_lines.extend(self._build_usage_info(result))
            if not response_text:
                info_lines.append("⚠️ 没有解析到文本回复，请查看完整响应。")
            return (response_text, raw_json, "\n".join(info_lines))
        except requests.exceptions.Timeout as e:
            return ("", "{}", f"❌ 错误：多模态对话请求超时：{timeout} 秒内没有响应，请增大超时时间或稍后重试。详情：{e}")
        except requests.exceptions.ConnectionError as e:
            return ("", "{}", f"❌ 错误：多模态对话网络连接失败：请检查网络、代理或防火墙。详情：{e}")
        except Exception as e:
            traceback.print_exc()
            return ("", "{}", f"❌ 错误：多模态智能对话失败\n\n详情：{e}")


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoAPImartMultimodalChatNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🐠多模态智能对话@炮老师的小课堂",
}
