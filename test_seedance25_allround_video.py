"""Paid-API-free checks for the Seedance 2.5 node registration and payload."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PACKAGE = "dapao_seedance25_testpkg"
if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE] = package

network_utils = types.ModuleType(f"{PACKAGE}.network_error_utils")
network_utils.friendly_443_status = lambda: "443错误"
network_utils.friendly_network_error = lambda error, action: f"{action}失败：{error}"
sys.modules[f"{PACKAGE}.network_error_utils"] = network_utils

image_utils = types.ModuleType(f"{PACKAGE}.image_input_utils")
image_utils.IMAGE_429_HINT = "模拟图片提示"
image_utils.tensor_to_png_bytes = lambda value: list(value)
sys.modules[f"{PACKAGE}.image_input_utils"] = image_utils

runtime = types.ModuleType(f"{PACKAGE}.dreambrush_runtime")
runtime.ensure_asset_references = lambda **_kwargs: {}
runtime.queue_job_metadata = lambda result: {"status": result.get("status", "")}
runtime.submit_json_task = lambda **_kwargs: {}
sys.modules[f"{PACKAGE}.dreambrush_runtime"] = runtime

base_module = importlib.import_module(f"{PACKAGE}.seedance20_allround_video_node")
node_module = importlib.import_module(f"{PACKAGE}.seedance25_allround_video_node")


class _FakeClient:
    last_payload = None

    def __init__(self, *_args, **_kwargs):
        pass

    def submit(self, payload):
        type(self).last_payload = dict(payload)
        return {
            "id": "seedance25-test-task",
            "status": "succeeded",
            "video_url": "https://example.com/result.mp4",
        }

    def poll(self, *_args, **_kwargs):
        raise AssertionError("同步成功响应不应进入轮询")


class Seedance25AllroundVideoTests(unittest.TestCase):
    def test_existing_seedance20_contract_is_unchanged(self):
        inputs = base_module.DapaoSeedance20AllroundVideoNode.INPUT_TYPES()
        optional = inputs["optional"]
        required_names = list(inputs["required"])
        self.assertEqual(inputs["required"]["🤖 模型"][0], ["SD2-face", "SD2.0-mini", "SD2-fast"])
        self.assertEqual(inputs["required"]["⏱️ 时长(秒)"][0], [str(value) for value in range(4, 16)])
        self.assertLess(required_names.index("👤 真人模式"), required_names.index("⏱️ 时长(秒)"))
        self.assertEqual(len([key for key in optional if key.startswith("🖼️ 参考图")]), 9)
        self.assertEqual(len([key for key in optional if key.startswith("🎞️ 参考视频")]), 3)
        self.assertEqual(len([key for key in optional if key.startswith("🎵 参考音频")]), 3)
        self.assertTrue(base_module.DapaoSeedance20AllroundVideoNode.INCLUDE_BILLING_SECONDS)

    def test_registration_model_and_expanded_inputs(self):
        node_class = node_module.DapaoSeedance25AllroundVideoNode
        inputs = node_class.INPUT_TYPES()
        optional = inputs["optional"]

        self.assertEqual(node_module.DISPLAY_NAME, "🐠Seedance2.5全能视频@炮老师的小课堂")
        self.assertEqual(inputs["required"]["🤖 模型"][0], ["SD2.5"])
        self.assertEqual(inputs["required"]["⏱️ 时长(秒)"][0], [str(value) for value in range(4, 31)])
        self.assertNotIn("👤 真人模式", inputs["required"])
        self.assertEqual(len([key for key in optional if key.startswith("🖼️ 参考图")]), 30)
        self.assertEqual(len([key for key in optional if key.startswith("🎞️ 参考视频")]), 10)
        self.assertEqual(len([key for key in optional if key.startswith("🎵 参考音频")]), 10)
        self.assertTrue(inspect.iscoroutinefunction(node_class.generate))

        urls = [f"https://example.com/image-{index}.png" for index in range(30)]
        self.assertEqual(len(node_class._public_url_overrides(json.dumps({"images": urls}))["images"]), 30)
        with self.assertRaisesRegex(ValueError, "最多 30 个"):
            node_class._public_url_overrides(json.dumps({"images": urls + ["https://example.com/too-many.png"]}))

    def test_submit_payload_uses_sd25_without_real_request(self):
        original_client = base_module.DapaoSeedanceRelayClient
        base_module.DapaoSeedanceRelayClient = _FakeClient
        try:
            result = asyncio.run(node_module.DapaoSeedance25AllroundVideoNode().generate(
                **{
                    "🔑 API密钥": "test-key",
                    "🤖 模型": "SD2.5",
                    "🎛️ 生成模式": "文生视频",
                    "📝 提示词": "测试镜头",
                    "🧩 分辨率": "720P",
                    "⏱️ 时长(秒)": "5",
                    "📐 视频比例": "16:9",
                    "🔊 生成音频": True,
                    "🌐 公网素材URL(JSON)": "{}",
                    "📋 额外参数JSON": "{}",
                    "🔁 最大轮询秒数": 1800,
                    "⏱️ 轮询间隔": 5,
                    "⌛ 请求超时": 120,
                }
            ))
        finally:
            base_module.DapaoSeedanceRelayClient = original_client

        self.assertEqual(_FakeClient.last_payload["model"], "SD2.5")
        self.assertEqual(_FakeClient.last_payload["seconds"], "5")
        self.assertEqual(result[1], "seedance25-test-task")
        self.assertIn("Seedance2.5", result[2])

    def test_thirty_seconds_is_accepted_and_submitted(self):
        original_client = base_module.DapaoSeedanceRelayClient
        base_module.DapaoSeedanceRelayClient = _FakeClient
        try:
            node_module.DapaoSeedance25AllroundVideoNode()._generate_sync(**{
                "🔑 API密钥": "test-key",
                "🤖 模型": "SD2.5",
                "🎛️ 生成模式": "文生视频",
                "📝 提示词": "三十秒测试镜头",
                "🧩 分辨率": "720P",
                "⏱️ 时长(秒)": "30",
                "📐 视频比例": "16:9",
                "🔊 生成音频": True,
                "🌐 公网素材URL(JSON)": "{}",
                "📋 额外参数JSON": "{}",
                "🔁 最大轮询秒数": 1800,
                "⏱️ 轮询间隔": 5,
                "⌛ 请求超时": 120,
            })
        finally:
            base_module.DapaoSeedanceRelayClient = original_client

        self.assertEqual(_FakeClient.last_payload["duration"], 30)
        self.assertEqual(_FakeClient.last_payload["seconds"], "30")

    def test_sd25_payload_matches_sd20_protocol_except_model(self):
        original_client = base_module.DapaoSeedanceRelayClient
        base_module.DapaoSeedanceRelayClient = _FakeClient
        common = {
            "🔑 API密钥": "test-key",
            "🎛️ 生成模式": "文生视频",
            "📝 提示词": "协议一致性测试",
            "🧩 分辨率": "720P",
            "⏱️ 时长(秒)": "5",
            "📐 视频比例": "16:9",
            "🔊 生成音频": True,
            "🌐 公网素材URL(JSON)": "{}",
            "📋 额外参数JSON": "{}",
            "🔁 最大轮询秒数": 1800,
            "⏱️ 轮询间隔": 5,
            "⌛ 请求超时": 120,
        }
        try:
            base_module.DapaoSeedance20AllroundVideoNode()._generate_sync(
                **{**common, "🤖 模型": "SD2-face", "👤 真人模式": True}
            )
            sd20_payload = dict(_FakeClient.last_payload)
            node_module.DapaoSeedance25AllroundVideoNode()._generate_sync(
                **{**common, "🤖 模型": "SD2.5"}
            )
            sd25_payload = dict(_FakeClient.last_payload)
        finally:
            base_module.DapaoSeedanceRelayClient = original_client

        self.assertEqual(sd20_payload.pop("model"), "SD2-face")
        self.assertEqual(sd25_payload.pop("model"), "SD2.5")
        self.assertEqual(sd25_payload, sd20_payload)


if __name__ == "__main__":
    unittest.main()
