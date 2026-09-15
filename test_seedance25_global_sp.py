"""Offline contract and concurrency tests for Global SP."""
import asyncio
import importlib
import inspect
import io
import time
import unittest
from unittest.mock import patch
from PIL import Image
import numpy as np
import test_seedance25_allround_video as fixture

mod = importlib.import_module(fixture.PACKAGE + ".seedance25_global_sp_video_node")

class GlobalSPTests(unittest.TestCase):
    setUp = fixture.Tests.setUp
    upload = fixture.Tests.upload
    request = fixture.Tests.request

    def args(self, **extra):
        return {"🔑 API密钥": "offline-key", "📝 提示词": "测试", **extra}

    def run_node(self, **extra):
        return asyncio.run(mod.DapaoSeedance25GlobalSPVideoNode().generate(**self.args(**extra)))

    def test_text_contract(self):
        result = self.run_node(**{"🤖 模型": "seedance-2.5-sp"})
        self.assertEqual(mod.MODEL_ID, "seedance-2.5-sp")
        call = fixture.runtime.submit_json_task.call_args.kwargs
        self.assertEqual(call["endpoint"], "/v1/videos")
        self.assertEqual(call["payload"], {"model": mod.MODEL_ID, "prompt": "测试", "seconds": "30", "ratio": "16:9", "resolution": "720p"})
        self.assertEqual(len(result), 4)
        self.assertFalse(self.uploads)
        self.assertFalse(self.requests)

    def test_image_preprocessing_without_registration(self):
        frame = fixture.Tensor(np.zeros((2, 1200, 2400, 3), dtype=np.float32))
        with patch.object(mod.GlobalSPClient, "prepare_asset", side_effect=AssertionError("must not register")):
            self.run_node(**{"🖼️ 参考图1": frame, "🎛️ 生成模式": "图生视频", "🧩 分辨率": "4K"})
        payload = fixture.runtime.submit_json_task.call_args.kwargs["payload"]
        self.assertEqual(payload["images"], ["asset://file-1", "asset://file-2"])
        self.assertNotIn("metadata", payload)
        self.assertEqual(payload["resolution"], "4k")
        for blob in self.uploads:
            self.assertEqual(Image.open(io.BytesIO(blob[0])).size, (2048, 1024))

    def test_invalid_inputs_never_submit(self):
        for extra in [{"⏱️ 时长(秒)": "5"}, {"🎛️ 生成模式": "图生视频"}, {"📐 视频比例": "adaptive"}, {"🔊 生成音频": True}, {"🎛️ 生成模式": "首尾帧生视频"}, {"📝 提示词": "a"*3001}, {"🤖 模型": "unsupported-model"}]:
            with self.assertRaises(RuntimeError): self.run_node(**extra)
        fixture.runtime.submit_json_task.assert_not_called()

    def test_old_model_option_routes_to_relay_id(self):
        self.run_node(**{"🤖 模型": "seedance-2.5-global-sp"})
        self.assertEqual(fixture.runtime.submit_json_task.call_args.kwargs["payload"]["model"], "seedance-2.5-sp")
        self.assertEqual(mod.DapaoSeedance25GlobalSPVideoNode.INPUT_TYPES()["required"]["🤖 模型"][0], ["seedance-2.5-sp"])

    def test_image_count_and_text_mode(self):
        frame = fixture.Tensor(np.zeros((10, 2, 2, 3), dtype=np.float32))
        with self.assertRaisesRegex(RuntimeError, "超过9"):
            self.run_node(**{"🖼️ 参考图1": frame})
        with self.assertRaisesRegex(RuntimeError, "文生视频不能"):
            self.run_node(**{"🖼️ 参考图1": frame[:1], "🎛️ 生成模式": "文生视频"})
        self.assertFalse(self.uploads)
        fixture.runtime.submit_json_task.assert_not_called()

    def test_poll_endpoint_and_failure_no_resubmit(self):
        client = mod.GlobalSPClient("offline-key", 60)
        result = {"status": "completed", "metadata": {"url": "https://example.com/result.mp4"}}
        with patch.object(fixture.base.DapaoSeedanceRelayClient, "_request_json", return_value=result) as request:
            self.assertEqual(client.poll("task-test", 60, 10), result)
            self.assertEqual(request.call_args.args, ("GET", "/v1/videos/task-test"))
        fixture.runtime.submit_json_task.side_effect = RuntimeError("HTTP 501: Not Implemented")
        with self.assertRaisesRegex(RuntimeError, "未实现"):
            self.run_node()
        self.assertEqual(fixture.runtime.submit_json_task.call_count, 1)

    def test_async_mapping_overlap(self):
        starts=[]
        def submit(**kwargs):
            starts.append(time.monotonic())
            time.sleep(0.1)
            return {"id": "task-test", "status": "completed"}
        fixture.runtime.submit_json_task.side_effect=submit
        node=mod.DapaoSeedance25GlobalSPVideoNode()
        async def run():
            return await asyncio.gather(*(node.generate(**self.args()) for _ in range(2)))
        results=asyncio.run(run())
        self.assertLess(abs(starts[1]-starts[0]), .08)
        self.assertTrue(all(len(r)==4 for r in results))
        self.assertTrue(inspect.iscoroutinefunction(node.generate))
        schema=node.INPUT_TYPES()
        self.assertEqual(schema["required"]["⏱️ 时长(秒)"][0], ["30"])
        self.assertNotIn("🏁 尾帧图",schema["optional"])

if __name__ == "__main__": unittest.main()
