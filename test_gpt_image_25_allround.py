"""Offline request contract and concurrency checks; no paid API calls."""
import asyncio
import base64
import importlib
import inspect
import io
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from PIL import Image

PACKAGE = "dapao_image25_testpkg"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).resolve().parent)]
sys.modules[PACKAGE] = package
base = importlib.import_module(f"{PACKAGE}.gpt_image_2_allround_node")
module = importlib.import_module(f"{PACKAGE}.gpt_image_25_allround_node")
Node = module.DapaoGPTImage25AllroundNode


def result():
    content = io.BytesIO()
    Image.new("RGB", (16, 16), "red").save(content, format="PNG")
    return {"data": [{"b64_json": base64.b64encode(content.getvalue()).decode()}]}


class Image25Tests(unittest.TestCase):
    def setUp(self):
        # Tripwire for every test: any accidental network access fails locally.
        for target in ("requests.request", "requests.sessions.Session.request"):
            guard = patch(target, side_effect=AssertionError("Network forbidden"))
            guard.start()
            self.addCleanup(guard.stop)
        for name in ("_log_info", "_log_error"):
            guard = patch.object(base, name)
            guard.start()
            self.addCleanup(guard.stop)
        self.args = {"🔑 API密钥": "offline", "📝 提示词": "测试图像"}

    def run_node(self, node=None, **kwargs):
        return asyncio.run((node or Node()).generate(**{**self.args, **kwargs}))

    def test_schema_and_registration(self):
        schema = Node.INPUT_TYPES()
        self.assertEqual(module.NODE_CLASS_MAPPINGS[module.NODE_NAME], Node)
        self.assertEqual(module.DISPLAY_NAME, "🦁GPT-image-2.5全能图像@炮老师的小课堂")
        self.assertEqual(Node.CATEGORY, "🤖dapaoAPI/🍬大炮AI主力维护🍬")
        self.assertTrue(inspect.iscoroutinefunction(getattr(Node, Node.FUNCTION)))
        self.assertFalse(getattr(Node, "INPUT_IS_LIST", False))
        self.assertEqual(schema["required"]["🤖 模型"][0], module.MODEL_OPTIONS)
        self.assertEqual(len(schema["required"]["🎨 画质"][0]), 5)
        self.assertEqual(sum(v[0] == "IMAGE" for v in schema["optional"].values()), 16)
        self.assertEqual(Node.RETURN_TYPES, ("IMAGE", "STRING", "STRING"))

    def test_all_qualities_and_resolutions_use_exact_model_and_native_n(self):
        for label, quality in module.QUALITY_API_VALUES.items():
            for resolution in ("1K", "2K", "4K"):
                with self.subTest(quality=quality, resolution=resolution), patch.object(base, "submit_json_task", return_value=result()) as submit:
                    output = self.run_node(**{"🎨 画质": label, "🧩 清晰度": resolution, "🖼️ 出图数量": 3, "📐 图片尺寸/比例": "16:9"})
                    submit.assert_called_once()
                    args = submit.call_args.kwargs
                    self.assertEqual(args["base_url"], "https://api.dapaoai.com")
                    self.assertEqual(args["endpoint"], "/v1/images/generations")
                    self.assertEqual(args["payload"], {"model": module.MODEL_LABEL, "prompt": "测试图像", "quality": quality, "resolution": resolution.lower(), "n": 3, "size": "16:9", "response_format": "url"})
                    self.assertEqual(tuple(output[0].shape), (1, 16, 16, 3))
                    self.assertEqual(output[1], "")
                    self.assertIn("妙笔工坊实际计费", output[2])

    def test_sunburst_generation_and_edit_use_exact_model(self):
        self.assertIn("gpt-image-2.5-sunburst", Node.INPUT_TYPES()["required"]["🤖 模型"][0])
        for quality in module.QUALITY_API_VALUES:
            args = {"🤖 模型": "gpt-image-2.5-sunburst", "🎨 画质": quality}
            with patch.object(base, "submit_json_task", return_value=result()) as submit:
                self.run_node(**args)
                self.assertEqual(submit.call_args.kwargs["payload"]["model"], "gpt-image-2.5-sunburst")
                self.assertEqual(submit.call_args.kwargs["payload"]["quality"], module.QUALITY_API_VALUES[quality])
            with patch.object(module.DapaoImage25RelayClient, "_request_json", return_value=result()) as request:
                self.run_node(**args, **{"🖼️ 图像1": torch.zeros((1, 16, 16, 3))})
                self.assertEqual(request.call_args.args, ("POST", "/v1/images/edits"))
                self.assertEqual(request.call_args.kwargs["data"]["model"], "gpt-image-2.5-sunburst")

    def test_invalid_quality_never_submits(self):
        with patch.object(base, "submit_json_task") as submit, patch.object(base, "ensure_asset_references") as upload:
            with self.assertRaisesRegex(RuntimeError, "不支持的画质"):
                self.run_node(**{"🎨 画质": "invalid"})
            submit.assert_not_called()
            upload.assert_not_called()

    def test_reference_batch_preprocessed_at_upload_boundary(self):
        images = torch.zeros((2, 64, 4096, 3))
        small = torch.zeros((1, 32, 48, 3))
        with patch.object(module.DapaoImage25RelayClient, "_request_json", return_value=result()) as upload:
            self.run_node(**{"🖼️ 图像1": images, "🖼️ 图像16": small})
            self.assertEqual(upload.call_args.args, ("POST", "/v1/images/edits"))
            blobs = [(part[1], part[0], part[2]) for _, part in upload.call_args.kwargs["files"]]
            self.assertEqual(len(blobs), 3)
            sizes = []
            for content, name, mime in blobs:
                image = Image.open(io.BytesIO(content))
                self.assertEqual(image.format, "PNG")
                sizes.append(image.size)
            self.assertEqual(sizes, [(2048, 32), (2048, 32), (48, 32)])
            self.assertNotIn("image_urls", upload.call_args.kwargs["data"])

    def test_sixteen_references_from_ports_or_batch_and_seventeen_rejected(self):
        single = torch.zeros((1, 16, 16, 3))
        cases = [
            {f"🖼️ 图像{i}": single for i in range(1, 17)},
            {"🖼️ 图像1": single.repeat(16, 1, 1, 1)},
        ]
        for inputs in cases:
            with patch.object(module.DapaoImage25RelayClient, "_request_json", return_value=result()) as upload:
                self.run_node(**inputs)
                self.assertEqual(len(upload.call_args.kwargs["files"]), 16)
                self.assertTrue(all(field == "image" for field, _ in upload.call_args.kwargs["files"]))
        with patch.object(base, "ensure_asset_references") as upload, patch.object(base, "submit_json_task") as submit:
            with self.assertRaisesRegex(RuntimeError, "最多接收16张参考图"):
                self.run_node(**{"🖼️ 图像1": single.repeat(16, 1, 1, 1), "🖼️ 图像16": single})
            upload.assert_not_called()
            submit.assert_not_called()
        old = base.DapaoGPTImage2AllroundNode
        self.assertEqual(sum(v[0] == "IMAGE" for v in old.INPUT_TYPES()["optional"].values()), 9)
        with self.assertRaisesRegex(ValueError, "最多接收9张参考图"):
            old._collect_reference_images({"🖼️ 图像1": single.repeat(10, 1, 1, 1)})

    def test_edit_http_boundary_and_no_retry(self):
        from unittest.mock import Mock
        response = Mock(status_code=200)
        response.json.return_value = result()
        with patch.object(base.requests, "request", return_value=response) as request:
            self.run_node(**{"🖼️ 图像1": torch.zeros((1, 16, 16, 3)), "⚡ 异步模式": True})
            request.assert_called_once()
            self.assertEqual(request.call_args.args, ("POST", "https://api.dapaoai.com/v1/images/edits"))
            args = request.call_args.kwargs
            self.assertNotIn("Content-Type", args["headers"])
            self.assertNotIn("Prefer", args["headers"])
            self.assertNotIn("async", args["data"])
            self.assertEqual(args["data"]["model"], "gpt-image-2.5-flare")
            self.assertEqual(args["files"][0][0], "image")
        with patch.object(base.requests, "request", side_effect=base.requests.Timeout("offline")) as request:
            with self.assertRaisesRegex(RuntimeError, "不会自动重试"):
                self.run_node(**{"🖼️ 图像1": torch.zeros((1, 16, 16, 3))})
            request.assert_called_once()

    def test_list_calls_overlap_with_distinct_clients(self):
        barrier = threading.Barrier(2, timeout=5)
        clients = []
        def generate(client, payload):
            clients.append(client)
            barrier.wait()
            return result()
        async def mapped():
            node = Node()
            return await asyncio.gather(*(node.generate(**{**self.args, "📝 提示词": str(i)}) for i in range(2)))
        with patch.object(base.DapaoImage2RelayClient, "generate", generate):
            outputs = asyncio.run(mapped())
        self.assertEqual(len(outputs), 2)
        self.assertIsNot(clients[0], clients[1])

    def test_errors_propagate_without_resubmission(self):
        for status in (429, 500, 502, 503):
            with self.subTest(status=status), patch.object(base, "submit_json_task", side_effect=base.DapaoImage2APIError(status, "offline failure")) as submit:
                with self.assertRaisesRegex(RuntimeError, str(status)) as error:
                    self.run_node()
                submit.assert_called_once()
                self.assertIsInstance(error.exception.__cause__, base.DapaoImage2APIError)
                if status == 429:
                    self.assertIn("2K", str(error.exception))

    def test_original_image2_routes_and_prices_unchanged(self):
        schema = base.DapaoGPTImage2AllroundNode.INPUT_TYPES()
        self.assertEqual(schema["required"]["🎨 画质"][0], ["低画质", "标准画质", "高画质"])
        for label, resolution, model, price, size in [
            ("image-2", "1K", "image-2-1k", "0.06", "16:9"),
            ("image-2", "2K", "image-2-2k", "0.12", "16:9"),
            ("image-2", "4K", "image-2-4k", "0.18", "16:9"),
            (base.OFFICIAL_STABLE_MODEL_LABEL, "4K", "image-2-office", "0.60", "3840x2160"),
        ]:
            with patch.object(base, "submit_json_task", return_value=result()) as submit:
                output = self.run_node(base.DapaoGPTImage2AllroundNode(), **{"🤖 模型": label, "🧩 清晰度": resolution, "📐 图片尺寸/比例": "16:9"})
                payload = submit.call_args.kwargs["payload"]
                self.assertEqual(payload["model"], model)
                self.assertEqual(payload["size"], size)
                self.assertEqual(payload["quality"], "medium")
                self.assertIn(f"¥{price}/张", output[2])

    def test_async_task_poll_and_url_output(self):
        with patch.object(base, "submit_json_task", return_value={"task_id": "task-test", "status": "processing"}) as submit, patch.object(base.DapaoImage2RelayClient, "poll", return_value={"data": [{"url": "https://example.com/a.png"}]}) as poll, patch.object(base.DapaoImage2RelayClient, "download", return_value=base64.b64decode(result()["data"][0]["b64_json"])):
            output = self.run_node(**{"⚡ 异步模式": True})
            self.assertTrue(submit.call_args.kwargs["payload"]["async"])
            poll.assert_called_once_with("task-test", 1200, 5, image_task=False)
            self.assertEqual(output[1], "https://example.com/a.png")


if __name__ == "__main__":
    unittest.main()
