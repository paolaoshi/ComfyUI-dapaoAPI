"""Paid-API-free contract, preprocessing and concurrency checks for Wan 3.0."""

from __future__ import annotations

import asyncio
import importlib
import inspect
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np


ROOT = Path(__file__).resolve().parent
PACKAGE = "dapao_wan30_testpkg"
package = types.ModuleType(PACKAGE)
package.__path__ = [str(ROOT)]
sys.modules[PACKAGE] = package
node_module = importlib.import_module(f"{PACKAGE}.wan30_allround_video_node")
media_module = importlib.import_module(f"{PACKAGE}.media_preprocess_utils")
Node = node_module.DapaoWan30AllroundVideoNode


class Tensor:
    def __init__(self, value):
        self.value, self.shape = value, value.shape
    def __getitem__(self, index): return Tensor(self.value[index])
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return self.value


class FakeVideo:
    def __init__(self, path): self.path = path
    def save_to(self, path, **_kwargs):
        Path(path).write_bytes(Path(self.path).read_bytes())
        return True


class FakeClient:
    payloads = []
    instances = []
    barrier = None
    submit_result = None
    poll_result = None
    polled_ids = []
    def __init__(self, *_args, **_kwargs): type(self).instances.append(self)
    def upload_many(self, blobs): return [f"asset://test-{i}" for i in range(len(blobs))]
    def submit(self, payload, recovery_salt=None):
        type(self).payloads.append(dict(payload))
        self.recovery_salt = recovery_salt
        if type(self).barrier: type(self).barrier.wait()
        return type(self).submit_result or {
            "id": "wan-test", "status": "succeeded", "video_url": "https://example.com/result.mp4"
        }
    def poll(self, task_id, *_args):
        type(self).polled_ids.append(task_id)
        if type(self).poll_result is None:
            raise AssertionError("同步成功不应轮询")
        return type(self).poll_result


def defaults(**overrides):
    return {"🔑 API密钥": "offline", "🤖 模型": "wan3.0", "🎛️ 生成模式": "文生视频",
            "📝 提示词": "测试镜头", "🧩 分辨率": "720P", "📐 视频比例": "自适应",
            "⏱️ 时长(秒)": "5", "🔊 生成音频": True, "🎲 随机种": 7, **overrides}


class Wan30Tests(unittest.TestCase):
    def setUp(self):
        FakeClient.payloads, FakeClient.instances, FakeClient.barrier = [], [], None
        FakeClient.submit_result, FakeClient.poll_result, FakeClient.polled_ids = None, None, []
        self.client_patch = patch.object(node_module, "Wan30RelayClient", FakeClient)
        self.client_patch.start(); self.addCleanup(self.client_patch.stop)

    def test_registration_capabilities_and_async_contract(self):
        inputs = Node.INPUT_TYPES()
        self.assertEqual(node_module.DISPLAY_NAME, "🦭万相3.0全能视频@炮老师的小课堂")
        self.assertEqual(Node.CATEGORY, "🤖dapaoAPI/🍬大炮AI主力维护🍬")
        self.assertEqual(inputs["required"]["🤖 模型"][0], ["wan3.0", "wan3.0-fast", "wan3.0-video"])
        self.assertEqual(inputs["required"]["🧩 分辨率"][0], ["720P", "1080P"])
        self.assertEqual(inputs["required"]["📐 视频比例"][0], ["自适应", "16:9", "9:16", "1:1"])
        self.assertEqual(inputs["required"]["⏱️ 时长(秒)"][0], list(map(str, range(2, 31))))
        self.assertEqual(inputs["required"]["🎲 随机种"][1]["control_after_generate"], "randomize")
        self.assertTrue(inputs["required"]["🔑 API密钥"][1]["password"])
        self.assertNotIn("🌐 公网素材URL(JSON)", inputs["optional"])
        self.assertNotIn("📋 额外参数JSON", inputs["optional"])
        self.assertEqual(len([x for x in inputs["optional"] if x.startswith("🖼️ 参考图")]), 10)
        self.assertEqual(len([x for x in inputs["optional"] if x.startswith("🎞️ 参考视频")]), 5)
        self.assertEqual(len([x for x in inputs["optional"] if x.startswith("🎵 参考音频")]), 5)
        self.assertTrue(inspect.iscoroutinefunction(Node.generate))
        self.assertFalse(getattr(Node, "INPUT_IS_LIST", False))

    def test_text_payload_for_every_model(self):
        for model in node_module.MODEL_OPTIONS:
            result = asyncio.run(Node().generate(**defaults(**{"🤖 模型": model})))
            payload = FakeClient.payloads[-1]
            self.assertEqual(payload["model"], model)
            self.assertEqual(payload["aspect_ratio"], "auto")
            self.assertEqual(payload["duration"], 5)
            self.assertEqual(payload["seconds"], "5")
            self.assertFalse({"mode", "prompt_extend", "watermark", "seed", "file_url", "link_url"}.intersection(payload))
            self.assertEqual(FakeClient.instances[-1].recovery_salt, 7)
            self.assertIn("随机种：7（仅用于ComfyUI缓存控制）", result[2])
            self.assertEqual(result[3], "https://example.com/result.mp4")

    def test_persistent_queue_success_still_polls_upstream_video_task(self):
        FakeClient.submit_result = {
            "id": "task-upstream-123", "task_id": "task-upstream-123", "status": "queued",
            "_dapao_queue": {"mode": "persistent", "job_id": "job-delivery-456", "status": "succeeded"},
        }
        FakeClient.poll_result = {
            "id": "task-upstream-123", "status": "succeeded",
            "video_url": "https://example.com/polled-result.mp4",
        }
        result = asyncio.run(Node().generate(**defaults()))
        self.assertEqual(FakeClient.polled_ids, ["task-upstream-123"])
        self.assertEqual(result[1], "task-upstream-123")
        self.assertEqual(result[3], "https://example.com/polled-result.mp4")

    def test_first_last_and_multimodal_payloads(self):
        image = Tensor(np.zeros((1, 400, 800, 3), dtype=np.float32))
        asyncio.run(Node().generate(**defaults(**{"🎛️ 生成模式": "首尾帧生视频", "🎬 首帧图": image, "🏁 尾帧图": image})))
        self.assertEqual(FakeClient.payloads[-1]["first_frame_image"], "asset://test-0")
        self.assertEqual(FakeClient.payloads[-1]["last_frame_image"], "asset://test-1")
        with patch.object(node_module, "prepare_audio", return_value=(b"mp3", "a.mp3", "audio/mpeg", 5.0)), \
             patch.object(node_module, "prepare_video", return_value=(b"mp4", "v.mp4", "video/mp4", 5.0)):
            asyncio.run(Node().generate(**defaults(**{"🤖 模型": "wan3.0-video", "🎛️ 生成模式": "多模态参考",
                "🖼️ 参考图1": image, "🎵 参考音频1": {"waveform": object()}, "🎞️ 参考视频1": object()})))
        payload = FakeClient.payloads[-1]
        self.assertEqual((len(payload["images"]), len(payload["videos"]), len(payload["audios"])), (1, 1, 1))

        asyncio.run(Node().generate(**defaults(**{"🎛️ 生成模式": "图生视频", "🎬 首帧图": image})))
        self.assertEqual(FakeClient.payloads[-1]["input_reference"], "asset://test-0")

    def test_video_capability_and_core_validation_before_submit(self):
        bad = [
            defaults(**{"🤖 模型": "wan3.0", "🎛️ 生成模式": "多模态参考", "🎞️ 参考视频1": object()}),
            defaults(**{"🎛️ 生成模式": "图生视频"}),
            defaults(**{"🎛️ 生成模式": "首尾帧生视频", "🎬 首帧图": Tensor(np.zeros((1, 8, 8, 3), dtype=np.float32))}),
            defaults(**{"🎛️ 生成模式": "多模态参考"}),
        ]
        for values in bad:
            with self.assertRaises(RuntimeError): asyncio.run(Node().generate(**values))
        self.assertFalse(FakeClient.payloads)

    def test_skip_error_never_leaks_error_as_video_url(self):
        result = asyncio.run(Node().generate(**defaults(**{"🎛️ 生成模式": "图生视频", "🚫 出错时跳过": True})))
        self.assertEqual(result[0].video_url, "")
        self.assertEqual(result[1], "")
        self.assertIn("失败", result[2])
        self.assertEqual(result[3], "")

    def test_friendly_errors_and_media_redaction(self):
        for status in (400, 401, 402, 403, 404, 413, 429, 500, 502, 503):
            self.assertIsInstance(node_module.DapaoWan30APIError(status, "模拟"), RuntimeError)
        safe = Node._safe_response({"prompt": "secret prompt", "images": ["asset://secret"],
                                    "first_frame_image": "https://signed.example/file",
                                    "video_url": "https://example.com/output.mp4"})
        self.assertNotIn("secret", str(safe))
        self.assertNotIn("signed.example", str(safe))
        self.assertEqual(safe["video_url"], "https://example.com/output.mp4")
        safe = Node._safe_response({"api_key": "sk-super-secret-123456", "nested": {
            "Authorization": "Bearer sk-super-secret-123456",
            "message": "request rejected for sk-super-secret-123456",
        }})
        self.assertNotIn("super-secret", str(safe))

    def test_list_mapped_tasks_overlap_with_independent_clients(self):
        FakeClient.barrier = threading.Barrier(3, timeout=5)
        async def run():
            return await asyncio.gather(*(Node().generate(**defaults(**{"📝 提示词": str(i)})) for i in range(3)))
        results = asyncio.run(run())
        self.assertEqual(len(results), 3)
        self.assertEqual(len({id(client) for client in FakeClient.instances}), 3)

    def test_real_image_audio_video_preprocessing(self):
        noisy = Tensor(np.random.default_rng(4).random((1, 1200, 2600, 3), dtype=np.float32))
        image_blob = media_module.prepare_image_tensor(noisy)[0]
        self.assertLessEqual(len(image_blob[0]), media_module.IMAGE_MAX_BYTES)
        from PIL import Image
        import io
        decoded = Image.open(io.BytesIO(image_blob[0]))
        self.assertLessEqual(max(decoded.size), 2048)

        samples = np.zeros((1, 1, 44100 * 2), dtype=np.float32)
        audio_blob = media_module.prepare_audio({"waveform": Tensor(samples), "sample_rate": 44100})
        self.assertEqual(audio_blob[2], "audio/mpeg")
        self.assertGreater(audio_blob[3], 1.9)

        source = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); source.close()
        try:
            subprocess.run([media_module._ffmpeg_tool("ffmpeg"), "-y", "-f", "lavfi", "-i", "color=c=blue:s=1280x720:r=60",
                            "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "2", "-c:v", "libx264",
                            "-c:a", "aac", source.name], check=True, capture_output=True)
            video_blob = media_module.prepare_video(FakeVideo(source.name))
            self.assertEqual(video_blob[2], "video/mp4")
            self.assertLessEqual(len(video_blob[0]), 10 * media_module.MIB)
            target = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4"); target.write(video_blob[0]); target.close()
            try:
                info = media_module._probe(target.name)
                stream = next(x for x in info["streams"] if x["codec_type"] == "video")
                self.assertEqual(stream["codec_name"], "h264")
                self.assertLessEqual(max(stream["width"], stream["height"]), 1080)
            finally: Path(target.name).unlink(missing_ok=True)
        finally: Path(source.name).unlink(missing_ok=True)


if __name__ == "__main__": unittest.main()
