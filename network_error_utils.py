"""Plain-language network errors for dapaoAPI nodes."""

try:
    from .node_error_utils import format_node_error
except ImportError:
    from node_error_utils import format_node_error


def friendly_network_error(error, action="请求"):
    """Keep the original exception; a HTTPS URL alone proves no network cause."""
    return format_node_error(error, context=action)



def friendly_443_status(original="HTTP 443"):
    """Message for non-standard 443 responses often produced by local proxies."""
    return format_node_error(
        "收到非标准HTTP 443状态码，不能仅凭状态码判断原因。"
        "请检查代理和API地址，并让服务商核查响应。\n" + str(original)
    )
