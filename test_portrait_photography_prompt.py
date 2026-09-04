"""Offline request-boundary checks. Never submits a paid API request."""

import asyncio
import base64
import importlib
import inspect
import io
import json
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
PACKAGE = "dapao_portrait_testpkg"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = package
node_module = importlib.import_module(f"{PACKAGE}.portrait_photography_prompt_node")
Node = node_module.DapaoPortraitPhotographyPromptNode


class Tensor:
    """Small tensor interface exercising the real shared PNG resize code."""
    def __init__(self, array):
        self.array, self.shape = array, array.shape

    def __getitem__(self, index):
        return Tensor(self.array[index])

    def detach(self):
        return self

    def cpu(self):
        return self

    def numpy(self):
        return self.array


def response_for(payload):
    request = json.loads(payload["messages"][1]["content"][0]["text"])
    shots = []
    for index in range(request["shot_count"]):
        shots.append({
            "source_image_index": 0 if request["mode"] == "B" else index % request["source_image_count"] + 1,
            "title": f"画面{index}", "positive_prompt": f"独立完整人物提示词{index}",
            "negative_prompt": f"负面词{index}", "quality_check": "摄影与身份自检",
            "shooting_card": {**{key: f"{key}-{index}" for key in (
                "person", "event", "scene", "composition", "color", "light", "main_effect",
                "auxiliary_effect", "styling", "emotion", "identity_lock", "diversity")},
                "reference_changes": []},
        })
    plan = {"reference_analysis": "有图观察/无图说明", "style_plan": "风格方案",
            "quality_check": "尚未检查成品", "shots": shots}
    return {"choices": [{"message": {"content": json.dumps(plan, ensure_ascii=False)}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 200}}


class PortraitTests(unittest.TestCase):
    def setUp(self):
        # Block the actual runtime boundary for every test, including errors.
        self.boundary = patch.object(node_module, "submit_json_task", side_effect=lambda **kw: response_for(kw["payload"]))
        self.submit = self.boundary.start()
        self.addCleanup(self.boundary.stop)

    def run_node(self, **kwargs):
        return asyncio.run(Node().generate_prompt(**{"🔑 API密钥": "offline-test-key", **kwargs}))

    def test_single_output_and_model_catalogue(self):
        result = self.run_node()
        self.assertEqual(len(result), len(Node.RETURN_TYPES))
        self.assertEqual(result[0], result[2][0])
        self.assertEqual(result[1], result[3][0])
        self.assertEqual(Node.INPUT_TYPES()["required"]["🤖 LLM模型"][0], list(node_module.LLM_MODEL_OPTIONS))
        request = self.submit.call_args.kwargs
        self.assertEqual(request["base_url"], "https://api.dapaoai.com")
        self.assertEqual(request["endpoint"], "/v1/chat/completions")
        self.assertNotIn("seed", request["payload"])
        self.assertNotIn("offline-test-key", str(result))

    def test_every_mode_and_role_at_real_png_boundary(self):
        source = Tensor(np.zeros((2, 1024, 3072, 3), dtype=np.float32))
        style = Tensor(np.zeros((1, 2800, 700, 3), dtype=np.float32))
        for mode in (node_module.MODE_OPTIONS[0], node_module.MODE_OPTIONS[1], node_module.MODE_OPTIONS[2], node_module.MODE_OPTIONS[3]):
            result = self.run_node(**{"🎬 运行模式": mode, "🖼️ 原照片": source, "🎨 风格参考图": style})
            content = self.submit.call_args.kwargs["payload"]["messages"][1]["content"]
            request = json.loads(content[0]["text"])
            images = [part["image_url"]["url"] for part in content if part["type"] == "image_url"]
            self.assertEqual(len(images), 3)
            for index, uri in enumerate(images):
                image = Image.open(io.BytesIO(base64.b64decode(uri.split(",", 1)[1])))
                self.assertEqual(image.format, "PNG")
                self.assertEqual(image.size, (2048, 683) if index < 2 else (512, 2048))
            self.assertEqual(request["mode"], "A" if mode == node_module.MODE_OPTIONS[0] else mode[0])
            self.assertEqual(len(result[2]), 1 if request["mode"] == "B" else 2)

    def test_style_only_automatic_is_original(self):
        style = Tensor(np.zeros((1, 12, 8, 3), dtype=np.float32))
        self.run_node(**{"🎨 风格参考图": style})
        request = json.loads(self.submit.call_args.kwargs["payload"]["messages"][1]["content"][0]["text"])
        self.assertEqual(request["mode"], "B")

    def test_selected_batch_and_complete_skill(self):
        result = self.run_node(**{"🔢 方案数量": 5, "🎯 选中方案": 3, "🔗 外部人像需求": "五位不同年龄的人"})
        self.assertEqual(result[0], result[2][2])
        self.assertEqual(result[1], result[3][2])
        self.assertEqual(len(result[2]), 5)
        system = self.submit.call_args.kwargs["payload"]["messages"][0]["content"]
        self.assertIn(node_module.RESOURCE_PATH.read_text(encoding="utf-8"), system)
        self.assertIn("A/C身份锁定优先", system)

    def test_missing_original_and_bad_choices_never_submit(self):
        for kwargs in ({"🎬 运行模式": node_module.MODE_OPTIONS[1]},
                       {"🎬 运行模式": node_module.MODE_OPTIONS[3]},
                       {"🤖 LLM模型": "unknown"}, {"🎯 选中方案": 2}, {"🔢 方案数量": 13}):
            with self.assertRaises(RuntimeError):
                self.run_node(**kwargs)
        self.submit.assert_not_called()

    def test_list_tasks_overlap_and_have_independent_clients(self):
        self.assertTrue(inspect.iscoroutinefunction(getattr(Node, Node.FUNCTION)))
        self.assertFalse(getattr(Node, "INPUT_IS_LIST", False))
        barrier = threading.Barrier(3, timeout=5)
        clients = []
        def chat(client, payload):
            clients.append(client)
            barrier.wait()
            return response_for(payload)
        async def run_batch():
            node = Node()
            return await asyncio.gather(*(node.generate_prompt(**{"🔑 API密钥": "offline", "📝 人像需求": str(i)}) for i in range(3)))
        with patch.object(node_module.PortraitLLMClient, "chat", chat):
            result = asyncio.run(run_batch())
        self.assertEqual(len(result), 3)
        self.assertEqual(len({id(client) for client in clients}), 3)

    def test_errors_propagate_or_skip_without_paid_retry(self):
        self.submit.side_effect = RuntimeError("模拟429上传排队")
        with self.assertRaisesRegex(RuntimeError, "2048"):
            self.run_node()
        self.assertEqual(self.submit.call_count, 1)
        result = self.run_node(**{"🚫 出错时跳过": True})
        self.assertEqual(self.submit.call_count, 2)
        self.assertEqual(result[:4], ("", "", [], []))
        self.assertIn("2048", result[-1])
        for code in (400, 401, 402, 403, 404, 429, 443, 500, 502, 503):
            self.assertIsInstance(node_module._error(code, "模拟"), RuntimeError)

    def test_incomplete_or_wrong_image_response_rejected_without_retry(self):
        def invalid(**kw):
            result = response_for(kw["payload"])
            plan = json.loads(result["choices"][0]["message"]["content"])
            plan["shots"][0]["source_image_index"] = 99
            result["choices"][0]["message"]["content"] = json.dumps(plan)
            return result
        self.submit.side_effect = invalid
        with self.assertRaisesRegex(RuntimeError, "编号"):
            self.run_node()
        self.assertEqual(self.submit.call_count, 1)
        self.submit.side_effect = None
        self.submit.return_value = {"choices": [{"finish_reason": "length", "message": {"content": "{}"}}]}
        with self.assertRaisesRegex(RuntimeError, "截断"):
            self.run_node()
        self.assertEqual(self.submit.call_count, 2)


if __name__ == "__main__":
    unittest.main()
