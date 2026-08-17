"""Plain-language network errors for dapaoAPI nodes."""

import re


def friendly_network_error(error, action="请求"):
    """Explain local HTTPS/proxy failures without blaming the relay prematurely."""
    text = str(error or "").strip()
    lowered = text.lower()
    is_https_443 = bool(
        re.search(r"(?:\b443\b|https://)", lowered)
        or "proxyerror" in lowered
        or "sslerror" in lowered
        or "cannot connect to host" in lowered
    )
    if is_https_443:
        return (
            f"ComfyUI本机网络连接异常：{action}无法通过 HTTPS 443 访问 dapaoAI。"
            "请先检查运行 ComfyUI 的电脑网络、VPN/代理、防火墙和 DNS，"
            "并确认浏览器可以打开 https://api.dapaoai.com 后再重试。"
        )
    return (
        f"ComfyUI本机网络连接或请求超时：{action}未能完成。"
        "请先检查运行 ComfyUI 的电脑网络、VPN/代理、防火墙和 DNS，"
        "确认网络正常后再重试。"
    )


def friendly_443_status():
    """Message for non-standard 443 responses often produced by local proxies."""
    return (
        "ComfyUI本机网络连接异常：收到非标准 HTTPS 443 响应。"
        "请先检查运行 ComfyUI 的电脑网络、VPN/代理、防火墙和 DNS，"
        "并确认浏览器可以打开 https://api.dapaoai.com 后再重试。"
    )
