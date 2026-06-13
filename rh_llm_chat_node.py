"""
RH LLM 智能对话节点

调用 RunningHub LLM OpenAI 兼容接口，支持文本和多图对话。
作者：@炮老师的小课堂
"""

import base64
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import traceback

import numpy as np
import requests
from PIL import Image


NODE_NAME = "DapaoRHLLMChatNode"
LLM_CHAT_URL = "https://llm.runninghub.cn/v1/chat/completions"
LLM_MODELS_URL = "https://llm.runninghub.ai/v1/models"
DEFAULT_MODEL = "google/gemini-3.1-flash-lite-preview"
MODEL_CACHE_TTL_SECONDS = 3600
REASONING_CHOICES = ["none", "low", "medium", "high"]
MAX_VIDEO_BYTES = 10 * 1024 * 1024
MAX_VIDEO_DURATION = 15

_MODEL_CACHE = {"expires_at": 0.0, "models": None}

FALLBACK_MODELS = [
    "google/gemini-3.1-flash-lite-preview",
    "google/gemini-3.5-flash",
    "openai/gpt-5.5",
    "openai/gpt-5.5-pro",
    "anthropic/claude-fable-5",
    "openai/gpt-5.4-pro",
    "anthropic/claude-opus-4.8",
    "anthropic/claude-opus-4.7",
    "anthropic/claude-opus-4.6",
    "openai/gpt-5.4",
    "openai/gpt-5.3-codex",
    "glm-5.1",
    "glm-5-turbo",
    "anthropic/claude-sonnet-4.6",
    "glm-5",
    "qwen/qwen3.7-max",
    "glm-5v-turbo",
    "deepseek/deepseek-v4-pro",
    "xai/grok-4.3",
    "qwen/qwen3.6-plus",
    "google/gemini-3.1-pro-preview",
    "anthropic/claude-sonnet-4.5",
    "anthropic/claude-opus-4.5",
    "bytedance/doubao-seed-2.0-pro",
    "bytedance/doubao-seed-2.0-code",
    "deepseek/deepseek-v4-flash",
    "qwen/qwen3.6-flash",
    "openai/gpt-5.4-mini",
    "openai/gpt-5.4-nano",
    "google/gemini-3-flash-preview",
    "google/gemini-2.5-flash",
    "bytedance/doubao-seed-2.0-lite",
    "bytedance/doubao-seed-2.0-mini",
]


def _log_info(message):
    print(f"[dapaoAPI-RH LLM智能对话] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH LLM智能对话] 错误：{message}")


def _default_model(models):
    return DEFAULT_MODEL if DEFAULT_MODEL in models else models[0]


def _fetch_model_list(force=False):
    now = time.time()
    cached = _MODEL_CACHE.get("models")
    if not force and cached and now < float(_MODEL_CACHE.get("expires_at", 0)):
        return list(cached)

    try:
        response = requests.get(LLM_MODELS_URL, timeout=5)
        response.raise_for_status()
        data = response.json()
        models = []
        for item in data.get("data", []):
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("id", "")).strip()
            if model_id:
                models.append(model_id)
        if models:
            _MODEL_CACHE["models"] = models
            _MODEL_CACHE["expires_at"] = now + MODEL_CACHE_TTL_SECONDS
            return models
    except Exception as e:
        _log_info(f"获取模型列表失败，使用内置模型列表：{type(e).__name__}")

    return list(FALLBACK_MODELS)


def _clean_think_tags(text):
    if not isinstance(text, str) or not text:
        return text
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"</?think>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"<\|begin_of_box\|>|<\|end_of_box\|>", "", cleaned)
    return cleaned.strip()


def _tensor_to_data_uris(image_tensor):
    data_uris = []
    for index in range(image_tensor.shape[0]):
        image_np = np.clip(image_tensor[index].cpu().numpy() * 255.0, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(image_np).convert("RGB")
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        data_uris.append(f"data:image/png;base64,{encoded}")
    return data_uris


def _copy_file_like_to_temp(file_obj):
    if not hasattr(file_obj, "read"):
        return None
    try:
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        with handle:
            handle.write(file_obj.read())
        return handle.name
    except Exception:
        return None


def _extract_video_path(video):
    cleanup_paths = []
    if isinstance(video, str) and os.path.exists(video):
        return video, cleanup_paths
    if isinstance(video, dict):
        for key in ("file_path", "path", "filename"):
            value = video.get(key)
            if isinstance(value, str) and os.path.exists(value):
                return value, cleanup_paths

    file_obj = getattr(video, "_VideoFromFile__file", None)
    if isinstance(file_obj, str) and os.path.exists(file_obj):
        return file_obj, cleanup_paths
    copied = _copy_file_like_to_temp(file_obj)
    if copied:
        cleanup_paths.append(copied)
        return copied, cleanup_paths

    for attr in ("path", "file"):
        value = getattr(video, attr, None)
        if isinstance(value, str) and os.path.exists(value):
            return value, cleanup_paths

    if hasattr(video, "get_stream_source"):
        try:
            value = video.get_stream_source()
            if isinstance(value, str) and os.path.exists(value):
                return value, cleanup_paths
        except Exception:
            pass

    if hasattr(video, "save_to"):
        try:
            handle = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            handle.close()
            video.save_to(handle.name)
            if os.path.exists(handle.name):
                cleanup_paths.append(handle.name)
                return handle.name, cleanup_paths
        except Exception:
            pass

    return None, cleanup_paths


def _compress_video(input_path):
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return None

    output_path = os.path.join(
        tempfile.gettempdir(),
        f"dapao_rh_llm_video_{int(time.time() * 1000)}.mp4",
    )
    command = [
        ffmpeg,
        "-y",
        "-i",
        input_path,
        "-t",
        str(MAX_VIDEO_DURATION),
        "-fs",
        str(MAX_VIDEO_BYTES),
        "-vcodec",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "28",
        "-acodec",
        "aac",
        output_path,
    ]
    try:
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except Exception as e:
        _log_info(f"视频压缩失败，无法自动缩小视频：{type(e).__name__}")
        return None

    if os.path.exists(output_path) and os.path.getsize(output_path) <= MAX_VIDEO_BYTES:
        return output_path
    return None


def _video_to_data_uri(video):
    path, cleanup_paths = _extract_video_path(video)
    if not path:
        raise RuntimeError("无法从 VIDEO 输入解析到本地视频文件路径。")

    try:
        use_path = path
        if os.path.getsize(use_path) > MAX_VIDEO_BYTES:
            compressed = _compress_video(use_path)
            if not compressed:
                raise RuntimeError("视频超过 10MB，且未找到 ffmpeg 或压缩失败，无法发送给 RH LLM。")
            cleanup_paths.append(compressed)
            use_path = compressed

        if os.path.getsize(use_path) > MAX_VIDEO_BYTES:
            raise RuntimeError("视频处理后仍超过 10MB，无法发送给 RH LLM。")

        with open(use_path, "rb") as handle:
            encoded = base64.b64encode(handle.read()).decode("ascii")
        return f"data:video/mp4;base64,{encoded}"
    finally:
        for cleanup_path in cleanup_paths:
            try:
                os.remove(cleanup_path)
            except Exception:
                pass


class DapaoRHLLMChatNode:
    @classmethod
    def INPUT_TYPES(cls):
        models = _fetch_model_list()
        return {
            "required": {
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "填入 RunningHub LLM API Key",
                    "tooltip": "仅用于本次请求，不会写入文件。"
                }),
                "🤖 模型ID": (models, {
                    "default": _default_model(models),
                    "tooltip": "启动节点时会从 RH 获取模型列表；如果获取失败，会使用内置备用列表。"
                }),
                "🎯 系统角色": ("STRING", {
                    "multiline": True,
                    "default": "你是一个专业、友好、乐于助人的 AI 助手，能够结合用户提供的文字与图像进行准确分析和回答。",
                    "placeholder": "定义 AI 的角色和行为方式..."
                }),
                "💬 用户输入": ("STRING", {
                    "multiline": True,
                    "default": "你好，请帮我分析这段内容。",
                    "placeholder": "输入你的问题或指令..."
                }),
                "🌡️ 温度": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01,
                    "tooltip": "数值越高，回答越发散；数值越低，回答越稳定。"
                }),
                "📝 最大输出令牌": ("INT", {
                    "default": 2048,
                    "min": 1,
                    "max": 65536,
                    "step": 1
                }),
                "🎲 Top_P": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                "🧠 推理强度": (REASONING_CHOICES, {
                    "default": "none",
                    "tooltip": "与 RH LLM reasoning_effort 参数对应，普通对话建议 none。"
                }),
                "🎲 随机种": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": "randomize",
                    "tooltip": "只用于 ComfyUI 判断是否重新执行；不会发送给 RunningHub。"
                }),
                "⏱️ 超时时间": ("INT", {
                    "default": 180,
                    "min": 30,
                    "max": 1200,
                    "step": 10
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🖼️ 图像5": ("IMAGE",),
                "🖼️ 图像6": ("IMAGE",),
                "🖼️ 图像7": ("IMAGE",),
                "🖼️ 图像8": ("IMAGE",),
                "🎬 视频": ("VIDEO",),
                "➕ 额外参数JSON": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "{\"presence_penalty\":0,\"frequency_penalty\":0}",
                    "tooltip": "JSON对象，会合并到 RH 请求体；同名字段会覆盖节点控件生成的参数。"
                }),
                "🚫 出错时跳过": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "开启后接口报错不会中断工作流，而是把错误信息作为文本输出。"
                }),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("💭 AI回复", "📄 完整响应", "ℹ️ 处理信息")
    FUNCTION = "chat"
    CATEGORY = "🤖dapaoAPI/🦄RH功能专区🦄"
    DESCRIPTION = "RH LLM 智能对话：RunningHub OpenAI 兼容接口，支持文本、多图和视频分析 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _headers(api_key):
        return {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "ComfyUI-dapaoAPI/RHLLMChat",
        }

    @staticmethod
    def _response_error_message(response):
        text = response.text[:1000]
        try:
            data = response.json()
            if isinstance(data, dict):
                error = data.get("error")
                if isinstance(error, dict):
                    return error.get("message") or error.get("code") or error.get("type") or text
                return data.get("message") or data.get("msg") or data.get("error") or text
        except Exception:
            pass
        return text

    def _raise_for_response(self, response):
        if response.status_code == 200:
            return
        message = self._response_error_message(response)
        status = response.status_code
        if status == 400:
            raise RuntimeError(f"RH LLM 参数错误 400：请检查模型ID、提示词、图片或输出参数。接口返回：{message}")
        if status == 401:
            raise RuntimeError(f"RH LLM 认证失败 401：API密钥无效或未填写正确。接口返回：{message}")
        if status == 402:
            raise RuntimeError(f"RH LLM 余额不足 402：账户余额不足，请充值后再试。接口返回：{message}")
        if status == 403:
            raise RuntimeError(f"RH LLM 权限不足 403：没有权限访问该模型或资源。接口返回：{message}")
        if status == 429:
            raise RuntimeError(f"RH LLM 请求过频 429：请降低频率后重试。接口返回：{message}")
        if status >= 500:
            raise RuntimeError(f"RH LLM 服务异常 {status}：服务器或上游暂时不可用。接口返回：{message}")
        raise RuntimeError(f"RH LLM 请求失败 {status}：{message}")

    @staticmethod
    def _should_retry(exc):
        if isinstance(exc, (requests.exceptions.Timeout, requests.exceptions.ConnectionError)):
            return True
        text = str(exc)
        return "429" in text or "服务异常" in text or "暂时不可用" in text

    def _post_json_with_retry(self, payload, api_key, timeout):
        last_error = None
        for attempt in range(3):
            try:
                response = requests.post(
                    LLM_CHAT_URL,
                    headers=self._headers(api_key),
                    json=payload,
                    timeout=timeout,
                )
                self._raise_for_response(response)
                return response.json()
            except json.JSONDecodeError as e:
                raise RuntimeError(f"RH LLM 返回内容不是 JSON：{e}")
            except Exception as e:
                last_error = e
                if attempt >= 2 or not self._should_retry(e):
                    raise
                time.sleep(min(2 ** attempt, 5))
        raise last_error

    @staticmethod
    def _build_messages(system_role, user_input, image_urls, video_url=None):
        messages = []
        if (system_role or "").strip():
            messages.append({"role": "system", "content": system_role.strip()})

        if image_urls:
            content = [{"type": "text", "text": user_input or ""}]
            for url in image_urls:
                content.append({"type": "image_url", "image_url": {"url": url}})
            messages.append({"role": "user", "content": content})
        elif video_url:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": user_input or ""},
                    {"type": "video_url", "video_url": {"url": video_url}},
                ],
            })
        else:
            messages.append({"role": "user", "content": user_input or ""})
        return messages

    @staticmethod
    def _extract_text(result):
        if not isinstance(result, dict):
            return ""
        choices = result.get("choices", [])
        if not isinstance(choices, list) or not choices:
            return ""
        first = choices[0] if isinstance(choices[0], dict) else {}
        message = first.get("message") if isinstance(first.get("message"), dict) else {}
        content = message.get("content")
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
        text = first.get("text")
        return "" if text is None else str(text)

    def _collect_images(self, kwargs):
        image_urls = []
        for index in range(1, 9):
            image_tensor = kwargs.get(f"🖼️ 图像{index}")
            if image_tensor is None:
                continue
            image_urls.extend(_tensor_to_data_uris(image_tensor))
        return image_urls

    def _collect_video(self, kwargs, has_images):
        video = kwargs.get("🎬 视频")
        if video is None:
            return None
        if has_images:
            _log_info("同时输入了图像和视频：按参考节点逻辑优先使用图像，忽略视频。")
            return None
        return _video_to_data_uri(video)

    @staticmethod
    def _load_extra_params(extra_json):
        text = (extra_json or "{}").strip()
        if not text:
            return {}
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"➕ 额外参数JSON 格式错误：{e}")
        if not isinstance(data, dict):
            raise ValueError("➕ 额外参数JSON 必须是 JSON 对象，例如 {\"presence_penalty\":0}")
        return data

    def chat(self, **kwargs):
        api_key = (kwargs.get("🔑 API密钥") or "").strip()
        model = (kwargs.get("🤖 模型ID") or DEFAULT_MODEL).strip()
        system_role = kwargs.get("🎯 系统角色", "")
        user_input = kwargs.get("💬 用户输入", "")
        temperature = kwargs.get("🌡️ 温度", 1.0)
        max_tokens = kwargs.get("📝 最大输出令牌", 2048)
        top_p = kwargs.get("🎲 Top_P", 1.0)
        reasoning_effort = kwargs.get("🧠 推理强度", "none")
        cache_seed = kwargs.get("🎲 随机种", 0)
        timeout = int(kwargs.get("⏱️ 超时时间", 180))
        extra_json = kwargs.get("➕ 额外参数JSON", "{}")
        skip_error = kwargs.get("🚫 出错时跳过", False)

        try:
            if not api_key:
                raise ValueError("API密钥为空，请填写 RunningHub LLM API Key 后再试。")
            if not model:
                raise ValueError("模型ID为空，请填写有效模型ID。")

            start_time = time.time()
            image_urls = self._collect_images(kwargs)
            video_url = self._collect_video(kwargs, bool(image_urls))
            payload = {
                "model": model,
                "messages": self._build_messages(system_role, user_input, image_urls, video_url),
                "max_tokens": int(max_tokens),
                "temperature": float(temperature),
                "top_p": float(top_p),
                "presence_penalty": 0,
                "frequency_penalty": 0,
                "reasoning_effort": reasoning_effort or "none",
            }
            payload.update(self._load_extra_params(extra_json))

            _log_info(f"开始请求模型：{model}，图像数量：{len(image_urls)}，视频：{'是' if video_url else '否'}")
            result = self._post_json_with_retry(payload, api_key, timeout)
            response_text = _clean_think_tags(self._extract_text(result))
            if not response_text:
                raise RuntimeError("RH LLM 返回内容为空。")

            elapsed_time = time.time() - start_time
            info = (
                "✅ RH LLM 智能对话完成\n"
                f"🤖 模型ID：{model}\n"
                f"🖼️ 图像数量：{len(image_urls)}\n"
                f"🎬 视频输入：{'是' if video_url else '否'}\n"
                f"🌡️ 温度：{temperature}\n"
                f"📝 最大输出令牌：{max_tokens}\n"
                f"🎲 Top_P：{top_p}\n"
                f"🧠 推理强度：{reasoning_effort}\n"
                f"🎲 随机种：{cache_seed}（仅用于 ComfyUI 缓存控制）\n"
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒"
            )
            return (response_text, json.dumps(result, ensure_ascii=False, indent=2), info)

        except Exception as e:
            error_msg = f"❌ RH LLM 智能对话失败：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            if skip_error:
                return (error_msg, json.dumps({"error": str(e)}, ensure_ascii=False, indent=2), error_msg)
            raise


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHLLMChatNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🐟RH LLM智能对话@炮老师的小课堂",
}
