"""Shared user-facing diagnostics. Never submit, retry, or translate model output."""

import re

try:
    from .error_message_catalog import HTTP_ERROR_HINTS, BUSINESS_ERROR_HINTS
except ImportError:
    from error_message_catalog import HTTP_ERROR_HINTS, BUSINESS_ERROR_HINTS


_MARKER = "原始错误（敏感信息已遮盖）："


def redact_error(text):
    text = str(text)
    text = re.sub(r"(?i)\bBearer\s+[^\s\"',;}]+", "Bearer ***", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]+", "sk-***", text)
    text = re.sub(
        r"(?i)((?:api[_-]?key|authorization|access_token|token|secret|password)[\"']?\s*[:=]\s*[\"']?)([^\s\"',;&}]+)",
        r"\1***", text,
    )
    return text


def format_node_error(error, context="", status_code=None):
    """Explain known errors while keeping original text and existing node hints.

    Unknown errors are explicitly unknown; an English exception is not evidence
    of a network failure. Context is a module/node label, never a prompt.
    """
    raw = redact_error(str(error))
    if _MARKER in raw:
        if "服务端异常、繁忙或上游响应超时" in raw:
            if "banana" in context.lower() and "香蕉pro官方稳定版" not in raw:
                raw += "\n操作建议：在模型中选择“香蕉pro官方稳定版”或“香蕉2官方稳定版”。"
            elif any(word in context.lower() for word in ("image_2", "image2")) and "image-2官方稳定全分辨率" not in raw:
                raw += "\n操作建议：在模型中选择“image-2官方稳定全分辨率”。"
        return raw
    text = raw.lower() + (" " + type(error).__name__.lower() if isinstance(error, BaseException) else "")
    # Prefer structured status. Don't read a port, task ID or image size as HTTP.
    status = status_code or getattr(error, "status_code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    if status is None:
        match = re.search(
            r"(?:http(?:/\d(?:\.\d)?)?\s*|status(?:_code| code)?\s*[:=]?\s*|"
            r"状态码[：:]?\s*|请求失败\s*|请求错误\s*|错误\s*\(?|上传失败\s*)"
            r"([45][0-9]{2})\b", text)
        if not match:
            match = re.search(r"\b([45][0-9]{2})\s+(?:client error|server error|bad request|unauthorized|forbidden|not found|too many requests|internal server error|bad gateway|service unavailable|gateway timeout)", text)
        status = int(match.group(1)) if match else None
    try:
        status = int(status) if status is not None else None
    except (TypeError, ValueError):
        status = None

    business_hint = next((hint for _category, patterns, hint in BUSINESS_ERROR_HINTS
                          if any(pattern in text for pattern in patterns)), "")
    hint = ""
    if business_hint:
        hint = business_hint
    elif "may contain real person" in text:
        hint = "上游认为输入图片可能包含真人，拒绝本次生成。请让服务商确认当前渠道是否支持这类素材；若并非真人，请提供任务ID核查误判。"
    elif any(word in text for word in ("content_policy_violation", "content safety policy", "content_filter", "safety filter", "responsibleaipolicyviolation", "sensitive content", "nsfw")):
        hint = "上游内容审核未通过。请检查提示词和参考素材是否符合服务要求；若认为误判，请凭任务ID联系服务商核查。错误未指出具体内容时，无法确定触发原因。"
    elif "asset" in text and any(word in text for word in ("not found", "does not exist", "expired")):
        hint = "引用素材不存在或已失效。请让服务商核对素材ID、有效期及生成渠道是否一致，保留任务ID排查，避免重复创建素材或视频。"
    elif "seedance_asset_model_unsupported" in text:
        hint = "当前模型渠道不支持这条素材登记流程。请核对该模型应直传素材还是先登记素材，不能仅通过改模型ID解决。"
    elif any(word in text for word in ("context_length_exceeded", "maximum context length", "too many tokens")):
        hint = "输入或预留输出超过模型上下文长度。请减少提示词、历史消息和参考资料，分段处理，或选择支持更长上下文的模型。"
    elif any(word in text for word in ("model_not_supported", "unsupported model", "model is not supported")):
        hint = "当前接口或渠道不支持所选模型。请核对服务商提供的模型ID、接口协议和账号模型权限。"
    elif any(word in text for word in ("failed to download", "failed to fetch image", "invalid image url", "url is not accessible")):
        hint = "服务端无法读取参考素材。请检查素材链接是否可访问、是否过期，以及素材格式是否符合模型要求。"
    elif any(word in text for word in ("insufficient_quota", "insufficient balance", "quota exceeded", "insufficient credits")) or status == 402:
        hint = "账号余额或可用额度不足。请检查所用服务商账号余额、API密钥额度和模型配额。"
    elif any(word in text for word in ("invalid_api_key", "invalid api key", "incorrect api key", "authentication_error")) or status == 401:
        hint = "身份验证失败。请检查API密钥是否正确、是否过期，以及密钥与API地址是否属于同一服务商。"
    elif status == 429 or any(word in text for word in ("rate_limit", "rate limit", "too many requests")):
        hint = "请求受到限流或队列已满。请降低并发并稍后查询已有任务；提交结果不明时先查原任务，避免重复扣费。"
        if any(word in (text + context.lower()) for word in ("upload", "上传", "image", "图片", "图像")):
            hint += "若发生在图片上传阶段，请检查每张图片最长边是否超过2048px（2K），多图和批次也需逐张检查。"
    elif status in (500, 502, 503, 504) or any(word in text for word in ("internal server error", "bad gateway", "service unavailable", "gateway timeout")):
        hint = "服务端异常、繁忙或上游响应超时。请保留任务ID，先查询已有任务状态；没有任务ID时联系服务商确认提交结果，再决定是否重新提交。"
        if "banana" in context.lower():
            hint += "香蕉节点可在“模型”中选择“香蕉pro官方稳定版”或“香蕉2官方稳定版”。"
        elif any(word in context.lower() for word in ("image_2", "image2")):
            hint += "image-2节点可在“模型”中选择“image-2官方稳定全分辨率”。"
    elif status == 403 or "permission denied" in text:
        hint = "访问被拒绝。请检查账号、模型和素材的访问权限，并让服务商核查限制原因。"
    elif status == 404 or "model_not_found" in text:
        hint = "接口、模型或请求的资源不存在。请核对API地址、模型ID和任务ID是否属于当前渠道。"
    elif status in (413, 415) or "unsupported media" in text:
        hint = "素材大小或媒体格式不符合接口要求。请核对文件大小、编码和格式，按当前模型要求处理后再提交。"
    elif status in (400, 422) or any(word in text for word in ("invalid parameter", "invalid_request_error", "not valid", "unsupported resolution")):
        hint = "请求参数或素材不符合模型要求。请按下方原始错误中的字段，检查分辨率、时长、素材类型和数量。"
    elif status in (408, 504) or any(word in text for word in ("timed out", "timeout", "超时")):
        hint = "请求或等待任务超时，不能据此判断生成失败。若已取得任务ID，请继续查询原任务；否则先确认网络和服务状态，避免重复提交付费请求。"
    elif any(word in text for word in ("connectionerror", "connection refused", "connection reset", "proxyerror", "sslerror", "certificate verify failed", "name resolution", "getaddrinfo", "cannot connect to host", "max retries exceeded")):
        hint = "网络连接、代理、DNS或TLS证书异常。请检查运行ComfyUI电脑到当前API地址的网络连接及代理设置；不能仅凭此错误确定故障在本机还是服务端。"
    elif any(word in text for word in ("jsondecodeerror", "expecting value", "not json", "不是 json", "不是json")):
        hint = "返回内容不是有效JSON，可能是错误页面或接口格式不匹配。请检查API地址，并保留原始响应交服务商核查。"
    elif any(word in text for word in ("out of memory", "cuda error")):
        hint = "本地内存、显存或CUDA执行异常。请检查剩余内存和显存，减少本地批次或并发，并核对运行环境。"
    elif "no module named" in text or "filenotfounderror" in text:
        hint = "本地依赖或文件缺失。请按原始错误检查ComfyUI使用的Python环境、所需依赖和文件路径。"
    if not hint and status in HTTP_ERROR_HINTS:
        hint = HTTP_ERROR_HINTS[status]
    if not hint:
        hint = ("请按下方原始错误中的中文提示检查。若仍无法解决，请提供节点名称、模型ID和任务ID供排查。"
                if re.search(r"[\u4e00-\u9fff]", raw)
                else "执行失败，当前错误未匹配到已知原因，无法确定故障来源。请提供节点名称、模型ID、任务ID及下方原始错误供排查。")
    if status in HTTP_ERROR_HINTS and HTTP_ERROR_HINTS[status] != hint:
        hint += f"\nHTTP {status}说明：{HTTP_ERROR_HINTS[status]}"
    elif status is not None and status not in HTTP_ERROR_HINTS:
        hint += f"\nHTTP状态码：{status}。该状态码未收录专用说明，请结合原始错误核查。"
    return f"中文说明：{hint}\n{_MARKER}\n{raw}"
