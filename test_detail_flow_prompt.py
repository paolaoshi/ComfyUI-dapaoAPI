"""Paid-API-free regression checks for the DetailFlow prompt node."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import re
import sys
import threading
import time
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = "dapao_detail_flow_testpkg"
if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE] = package

network_utils = types.ModuleType(f"{PACKAGE}.network_error_utils")
network_utils.friendly_443_status = lambda: "443错误"
network_utils.friendly_network_error = lambda error, action: f"{action}失败：{error}"
sys.modules[f"{PACKAGE}.network_error_utils"] = network_utils

image_utils = types.ModuleType(f"{PACKAGE}.image_input_utils")
image_utils.IMAGE_429_HINT = "模拟429图片提示"
image_utils.tensor_to_png_data_uris = lambda value, max_edge=2048: list(value)
sys.modules[f"{PACKAGE}.image_input_utils"] = image_utils

model_options = types.ModuleType(f"{PACKAGE}.llm_model_options")
model_options.LLM_MODEL_OPTIONS = ("gemini-3.7-flash", "gpt-5.6-sol")
sys.modules[f"{PACKAGE}.llm_model_options"] = model_options

detail_module = importlib.import_module(f"{PACKAGE}.detail_flow_prompt_node")


def fake_package(screen_count):
    blueprint = []
    prompts = {}
    for index in range(1, screen_count + 1):
        blueprint.append({
            "slice_id": f"screen_{index:02d}",
            "chapter_id": f"C{((index - 1) // 8) + 1}",
            "chapter_role": f"章节任务{((index - 1) // 8) + 1}",
            "buyer_question": f"购买问题{index}",
            "claim_seed": f"卖点{((index - 1) % 6) + 1}",
            "screen_job": f"页面任务{index}",
            "evidence_type": f"证据{index}",
            "content_density": "均衡",
            "copy_structure_pattern": f"结构{index}",
            "primary_module": f"主模块{index}",
            "secondary_modules": [f"次模块{index}"],
            "text_exact": [f"准确文案{index}"],
            "composition_shift": f"构图变化{index}",
            "top_edge_anchor": "承接上屏" if index > 1 else "自然起始",
            "bottom_edge_anchor": "承接下屏" if index < screen_count else "自然收尾",
            "visual_composition": f"画面构图{index}",
            "risk_unknowns": [],
        })
        prompts[f"第{index:02d}屏"] = f"第{index:02d}屏完整生成要求"
    min_seeds, _ = detail_module._claim_seed_bounds(screen_count)
    return {
        "product_analysis": {"category": "测试产品"},
        "claim_seeds": [f"卖点{index}" for index in range(1, min_seeds + 1)],
        "blueprint": blueprint,
        "visual_master": {
            "visual_master_spec": "统一视觉母版",
            "master_reference_prompt": "母版提示词",
            "visual_style_dna": "统一风格",
            "product_identity_lock": "产品身份不变",
            "continuity_rules": "相邻屏连续",
            "recommended_master_ratio": "1:4",
            "recommended_slice_ratio": "3:4",
        },
        "screen_prompts": prompts,
        "audit_report": {
            "observed_problems": [],
            "severity": "low",
            "unsupported_claims": [],
            "continuity_findings": [],
            "next_action": "生成",
        },
        "exact_copy_master": ["准确文案"],
        "production_notes": [],
    }


class FakeClient:
    active = 0
    max_active = 0
    payloads = []
    fail = False
    lock = threading.Lock()

    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, payload):
        type(self).payloads.append(payload)
        with self.lock:
            type(self).active += 1
            type(self).max_active = max(type(self).max_active, type(self).active)
        try:
            time.sleep(0.08)
            if type(self).fail:
                raise RuntimeError("模拟接口失败")
            user_content = payload["messages"][-1]["content"]
            if isinstance(user_content, list):
                user_content = user_content[0]["text"]
            match = re.search(r"SCREEN COUNT:\s*(\d+)", user_content)
            screen_count = int(match.group(1))
            return {
                "choices": [{"message": {"content": json.dumps(fake_package(screen_count), ensure_ascii=False)}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 200},
            }
        finally:
            with self.lock:
                type(self).active -= 1


class DetailFlowPromptTests(unittest.TestCase):
    def setUp(self):
        self.original_client = detail_module.DetailFlowLLMClient
        detail_module.DetailFlowLLMClient = FakeClient
        FakeClient.active = 0
        FakeClient.max_active = 0
        FakeClient.payloads = []
        FakeClient.fail = False

    def tearDown(self):
        detail_module.DetailFlowLLMClient = self.original_client

    @staticmethod
    def kwargs(screen_count=8, **extra):
        values = {
            "🔑 API密钥": "test-key",
            "🤖 LLM模型": "gemini-3.7-flash",
            "🔢 分屏数量": str(screen_count),
            "📝 原始电商需求": "测试完整详情页",
            "📝 最大输出令牌": 32768,
            "⌛ 请求超时": 30,
        }
        values.update(extra)
        return values

    def test_schema_supports_24_dynamic_screens_and_expanded_images(self):
        input_types = detail_module.DapaoDetailFlowPromptNode.INPUT_TYPES()
        optional = input_types["optional"]
        self.assertEqual(detail_module.MAX_SCREEN_COUNT, 24)
        self.assertEqual(input_types["required"]["🔢 分屏数量"][0][-1], "24")
        self.assertEqual(len([name for name in optional if name.startswith("📦 产品图")]), 12)
        self.assertEqual(len([name for name in optional if name.startswith("🎨 风格参考图")]), 6)
        self.assertEqual(len(detail_module.DapaoDetailFlowPromptNode.RETURN_TYPES), 32)
        self.assertEqual(len(detail_module.DapaoDetailFlowPromptNode.RETURN_NAMES), 32)
        self.assertTrue(detail_module.DapaoDetailFlowPromptNode.OUTPUT_IS_LIST[7])
        self.assertFalse(any(detail_module.DapaoDetailFlowPromptNode.OUTPUT_IS_LIST[8:]))

    def test_24_screen_output_contract(self):
        node = detail_module.DapaoDetailFlowPromptNode()
        result = asyncio.run(node.generate_prompt(**self.kwargs(24)))
        self.assertEqual(len(result), 32)
        self.assertEqual(len(json.loads(result[1])), 24)
        self.assertEqual(len(result[7]), 24)
        self.assertIn("第01屏完整生成要求", result[8])
        self.assertIn("第24屏完整生成要求", result[31])
        self.assertIn("3个连续章节", result[5])
        self.assertEqual(FakeClient.payloads[-1]["max_tokens"], 32768)

    def test_selected_count_fills_only_matching_screen_outputs(self):
        result = asyncio.run(detail_module.DapaoDetailFlowPromptNode().generate_prompt(**self.kwargs(3)))
        self.assertEqual(len(result[7]), 3)
        self.assertTrue(all(result[index] for index in range(8, 11)))
        self.assertTrue(all(result[index] == "" for index in range(11, 32)))

    def test_public_method_is_async_and_list_tasks_overlap(self):
        self.assertTrue(inspect.iscoroutinefunction(detail_module.DapaoDetailFlowPromptNode.generate_prompt))

        async def run_two():
            first = detail_module.DapaoDetailFlowPromptNode().generate_prompt(**self.kwargs(2))
            second = detail_module.DapaoDetailFlowPromptNode().generate_prompt(**self.kwargs(4))
            return await asyncio.gather(first, second)

        results = asyncio.run(run_two())
        self.assertEqual([len(result[7]) for result in results], [2, 4])
        self.assertGreaterEqual(FakeClient.max_active, 2)

    def test_skip_error_keeps_full_output_shape_without_retry(self):
        FakeClient.fail = True
        result = asyncio.run(detail_module.DapaoDetailFlowPromptNode().generate_prompt(**self.kwargs(24, **{"🚫 出错时跳过": True})))
        self.assertEqual(len(result), 32)
        self.assertEqual(result[7], [])
        self.assertTrue(all(value == "" for value in result[8:]))
        self.assertEqual(len(FakeClient.payloads), 1)

    def test_shared_png_preprocessor_is_used_at_2k(self):
        seen = {}
        original = detail_module.tensor_to_png_data_uris

        def fake_png(value, max_edge=0):
            seen["value"] = value
            seen["max_edge"] = max_edge
            return ["data:image/png;base64,ZmFrZQ=="]

        detail_module.tensor_to_png_data_uris = fake_png
        try:
            value = object()
            self.assertEqual(detail_module._image_data_uris(value), ["data:image/png;base64,ZmFrZQ=="])
        finally:
            detail_module.tensor_to_png_data_uris = original
        self.assertEqual(seen, {"value": value, "max_edge": 2048})


if __name__ == "__main__":
    unittest.main()
