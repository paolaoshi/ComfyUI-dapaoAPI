"""Offline error contract: explain failures, preserve evidence, never retry."""
import ast
import asyncio
from pathlib import Path
import unittest

from node_error_utils import format_node_error
from network_error_utils import friendly_network_error
from node_execution_gate import serialize_registered_nodes
from error_message_catalog import HTTP_ERROR_HINTS, BUSINESS_ERROR_HINTS


class ErrorContractTests(unittest.TestCase):
    def test_document_contains_every_shared_catalog_entry(self):
        guide = (Path(__file__).parent / "ERROR_HANDLING.md").read_text(encoding="utf-8")
        for code, hint in HTTP_ERROR_HINTS.items():
            self.assertIn(f"| {code} | {hint} |", guide)
        for category, patterns, hint in BUSINESS_ERROR_HINTS:
            self.assertIn(f"`{category}`", guide)
            self.assertIn(hint, guide)

    def test_every_http_catalog_entry_in_all_feature_contexts(self):
        for code, hint in HTTP_ERROR_HINTS.items():
            for context in ("gpt_image_2_allround_node", "banana_allround_node", "gpt_llm_chat_node", "seedance20_allround_video_node", "rh_app_node", "素材上传", "下载结果"):
                with self.subTest(code=code, context=context):
                    raw = f"HTTP {code}: synthetic error"
                    text = format_node_error(raw, context=context)
                    self.assertIn(hint, text)
                    self.assertIn(raw, text)
                    self.assertIn(hint, format_node_error("synthetic error", status_code=code))

    def test_business_catalog_and_http_coexist(self):
        for category, patterns, hint in BUSINESS_ERROR_HINTS:
            for pattern in patterns:
                with self.subTest(category=category, pattern=pattern):
                    raw = f"HTTP 429: {pattern}"
                    text = format_node_error(raw)
                    self.assertIn(hint, text)
                    self.assertIn(raw, text)
        self.assertIn("功能", format_node_error("HTTP 501: Not Implemented"))
        self.assertIn("上游", format_node_error("HTTP 502: Bad Gateway"))
        self.assertIn("未收录", format_node_error("custom failure", status_code=599))

    def test_known_errors_have_specific_chinese_and_original(self):
        cases = [
            ("Invalid API key", "身份验证失败"),
            ("HTTP 402: payment required", "额度不足"),
            ("HTTP 403: forbidden", "访问被拒绝"),
            ("HTTP 404: not found", "资源不存在"),
            ("HTTP 429: too many requests", "限流"),
            ("HTTP 500: internal server error", "服务端异常"),
            ("HTTP 502: bad gateway", "服务端异常"),
            ("HTTP 503: service unavailable", "服务端异常"),
            ("HTTP 504: gateway timeout", "上游响应超时"),
            ("content_policy_violation", "内容审核未通过"),
            ("image may contain real person", "可能包含真人"),
            ("asset demo not found", "引用素材不存在"),
            ("seedance_asset_model_unsupported", "素材登记流程"),
            ("HTTP 422: invalid parameter duration", "请求参数或素材"),
            ("HTTP 413: payload too large", "素材大小"),
            ("Read timed out", "等待任务超时"),
            ("ProxyError: connection refused", "代理"),
            ("JSONDecodeError: Expecting value", "有效JSON"),
            ("CUDA out of memory", "显存"),
            ("No module named demo", "依赖或文件缺失"),
        ]
        for raw, expected in cases:
            with self.subTest(raw=raw):
                result = format_node_error(raw)
                self.assertIn(expected, result)
                self.assertIn(raw, result)
                self.assertIn("原始错误", result)

    def test_unknown_is_not_guessed_from_url_port_or_task_id(self):
        for raw in ["unrecognized upstream failure https://example.com:443", "task-500 picture 403x429"]:
            self.assertIn("未匹配到已知原因", format_node_error(raw))
        self.assertIn("unrecognized", friendly_network_error(Exception("unrecognized")))

    def test_network_original_and_secrets(self):
        result = friendly_network_error(Exception("ProxyError: cannot connect; Bearer abcdef; api_key=xyz; sk-demo123"))
        self.assertIn("ProxyError: cannot connect", result)
        for secret in ["abcdef", "xyz", "sk-demo123"]:
            self.assertNotIn(secret, result)

    def test_nested_idempotence_and_model_advice(self):
        result = format_node_error("HTTP 503: unavailable")
        for module, expected in [("banana_allround_node", "香蕉pro官方稳定版"), ("gpt_image_2_allround_node", "image-2官方稳定全分辨率")]:
            final = format_node_error(result, context=module)
            self.assertIn(expected, final)
            self.assertEqual(format_node_error(final, context=module), final)
            self.assertEqual(final.count("原始错误（"), 1)
        self.assertIn("2048", format_node_error("HTTP 429", context="图片上传"))

    def test_registered_fallback_preserves_exception_and_success(self):
        class Probe:
            FUNCTION = "run"
            calls = 0
            async def run(self, fail=False):
                self.calls += 1
                if fail:
                    error = ValueError("HTTP 400: invalid parameter duration")
                    error.task_id = "task-demo"
                    raise error
                return ("A prompt about an HTTP 500 error", {"error": "a story"})
        serialize_registered_nodes({"probe": Probe})
        probe = Probe()
        with self.assertRaises(ValueError) as caught:
            asyncio.run(probe.run(True))
        self.assertEqual(caught.exception.task_id, "task-demo")
        self.assertIn("请求参数", str(caught.exception))
        self.assertEqual(probe.calls, 1)
        self.assertEqual(asyncio.run(probe.run()), ("A prompt about an HTTP 500 error", {"error": "a story"}))

    def test_registration_and_explicit_error_messages_have_shared_formatter(self):
        root = Path(__file__).parent
        init = (root / "__init__.py").read_text(encoding="utf-8-sig")
        self.assertIn("serialize_registered_nodes(NODE_CLASS_MAPPINGS)", init)
        checked = 0
        for path in root.glob("*node*.py"):
            if path.name.startswith("test_"):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8-sig"))
            parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
            for node in ast.walk(tree):
                if not isinstance(node, ast.JoinedStr) or not node.values:
                    continue
                first = node.values[0]
                if not isinstance(first, ast.Constant) or not str(first.value).startswith("❌"):
                    continue
                if str(first.value).startswith("❌ 失败任务："):
                    continue  # Batch summary count, not an error description.
                parent = parents.get(node)
                checked += 1
                self.assertTrue(isinstance(parent, ast.Call) and isinstance(parent.func, ast.Name) and parent.func.id == "format_node_error", f"{path.name}:{node.lineno}")
        self.assertGreater(checked, 30)


if __name__ == "__main__":
    unittest.main()
