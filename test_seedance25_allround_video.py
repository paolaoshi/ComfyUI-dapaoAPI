"""Offline regression checks for the two existing Miaobi Seedance nodes."""
import asyncio
import importlib
import inspect
import io
import json
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
from PIL import Image

PACKAGE = "dapao_seedance_miaobi_tests"
pkg = types.ModuleType(PACKAGE)
pkg.__path__ = [str(Path(__file__).resolve().parent)]
sys.modules[PACKAGE] = pkg
runtime = types.ModuleType(PACKAGE + ".dreambrush_runtime")
runtime.ensure_asset_references = Mock()
runtime.submit_json_task = Mock()
runtime.queue_job_metadata = lambda result: result.get("_dapao_queue", {})
sys.modules[runtime.__name__] = runtime
base = importlib.import_module(PACKAGE + ".seedance20_allround_video_node")
v25 = importlib.import_module(PACKAGE + ".seedance25_allround_video_node")
media = importlib.import_module(PACKAGE + ".seedance_relay_media")

class Tensor:
    def __init__(self, array): self.array = array; self.shape = array.shape
    def __getitem__(self, index): return Tensor(self.array[index])
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return self.array

class Tests(unittest.TestCase):
    def setUp(self):
        self.counter = 0
        self.uploads = []
        self.requests = []
        runtime.ensure_asset_references.reset_mock(side_effect=True)
        runtime.submit_json_task.reset_mock(side_effect=True)
        runtime.ensure_asset_references.side_effect = self.upload
        runtime.submit_json_task.side_effect = lambda **kw: {"id": "task-test", "status": "completed", "metadata": {"url": "https://example.com/video.mp4"}}
        self.network = patch.object(base.requests, "request", side_effect=self.request)
        self.network.start()
        self.no_get = patch.object(base.requests, "get", side_effect=AssertionError("unexpected external GET"))
        self.no_get.start()
        self.addCleanup(self.network.stop)
        self.addCleanup(self.no_get.stop)
        self.addCleanup(patch.stopall)
        patch.object(base, "_safe_print", lambda *_: None).start()

    def upload(self, key, blobs, **kw):
        refs = []
        for blob in blobs:
            self.uploads.append(blob)
            self.counter += 1
            refs.append(f"asset://file-{self.counter}")
        return refs

    def request(self, method, url, **kw):
        self.requests.append((method, url, kw))
        self.assertTrue(url.startswith("https://api.dapaoai.com/v1/seedance/assets"))
        data = {"id": kw.get("json", {}).get("file_id", "file-1"), "status": "ready", "registration_id": "sa-test"}
        response = Mock(status_code=200, headers={})
        response.json.return_value = data
        return response

    def args(self, model="doubao-seedance-2.0", **extra):
        return {"🔑 API密钥": "offline-key", "🤖 模型": model, "📝 提示词": "测试", "🎛️ 生成模式": "自动识别", **extra}

    def run_node(self, model="doubao-seedance-2.0", **extra):
        cls = v25.DapaoSeedance25AllroundVideoNode if model == "doubao-seedance-2-5" else base.DapaoSeedance20AllroundVideoNode
        result = asyncio.run(cls().generate(**self.args(model, **extra)))
        self.assertEqual(len(result), 4)
        self.assertEqual(result[1], "task-test")
        return runtime.submit_json_task.call_args.kwargs["payload"]

    def test_models_and_existing_node_names(self):
        for cls, models in [(base.DapaoSeedance20AllroundVideoNode, ["doubao-seedance-2.0", "seedance-2.0"]), (v25.DapaoSeedance25AllroundVideoNode, ["doubao-seedance-2-5"])]:
            inputs = cls.INPUT_TYPES()
            self.assertEqual(inputs["required"]["🤖 模型"][0], models)
            self.assertNotIn("👤 真人模式", inputs["required"])
            self.assertTrue(inspect.iscoroutinefunction(getattr(cls, cls.FUNCTION)))
            self.assertFalse(getattr(cls, "INPUT_IS_LIST", False))
            self.assertEqual(len([k for k in inputs["optional"] if k.startswith("🖼️ 参考图")]), 9)

    def test_text_payloads_all_models(self):
        for model in ["doubao-seedance-2.0", "seedance-2.0", "doubao-seedance-2-5"]:
            payload = self.run_node(model, **{"🔊 生成音频": False})
            self.assertEqual(set(payload), {"model", "prompt", "seconds", "metadata"})
            self.assertEqual(payload["model"], model)
            self.assertNotIn("content", payload["metadata"])
            if model == "seedance-2.0": self.assertNotIn("generate_audio", payload["metadata"])
            else: self.assertIs(payload["metadata"]["generate_audio"], False)
            if model == "doubao-seedance-2-5": self.assertEqual(payload["metadata"]["output_format"], "mp4")
            else: self.assertNotIn("output_format", payload["metadata"])
        self.assertFalse(self.requests)

    def test_direct_frames_are_resized_registered_and_ordered(self):
        frame = Tensor(np.zeros((1, 1200, 2400, 3), dtype=np.float32))
        payload = self.run_node(**{"🎬 首帧图": frame, "🏁 尾帧图": frame})
        self.assertEqual([c["role"] for c in payload["metadata"]["content"]], ["first_frame", "last_frame"])
        self.assertEqual(len(self.requests), 2)
        for data, _, mime in self.uploads:
            with Image.open(io.BytesIO(data)) as image: self.assertEqual(image.size, (2048, 1024))
            self.assertEqual(mime, "image/png")
        self.assertTrue(payload["metadata"]["seedance_asset_library"])
        self.assertTrue(all(r[2]["json"]["model"] == "doubao-seedance-2.0" for r in self.requests))

    def test_sp_accepts_material_but_rejects_other_resolution(self):
        payload = self.run_node("seedance-2.0", **{"🌐 公网素材URL(JSON)": json.dumps({"images": ["asset://file-test"]})})
        self.assertFalse(self.requests)
        self.assertNotIn("seedance_asset_library", payload["metadata"])
        self.assertEqual(payload["metadata"]["content"][0]["image_url"]["url"], "asset://file-test")
        runtime.submit_json_task.reset_mock()
        with self.assertRaisesRegex(RuntimeError, "分辨率"):
            self.run_node("seedance-2.0", **{"🧩 分辨率": "1080P"})
        runtime.submit_json_task.assert_not_called()

    def test_25_direct_image_upload_skips_registration(self):
        frame = Tensor(np.zeros((1, 1200, 2400, 3), dtype=np.float32))
        with patch.object(base.DapaoSeedanceRelayClient, "prepare_asset", side_effect=AssertionError("2.5 must not register")):
            payload = self.run_node("doubao-seedance-2-5", **{"🖼️ 参考图1": frame, "🔊 生成音频": False})
        self.assertFalse(self.requests)
        self.assertEqual(len(self.uploads), 1)
        with Image.open(io.BytesIO(self.uploads[0][0])) as image:
            self.assertEqual(image.size, (2048, 1024))
        self.assertNotIn("seedance_asset_library", payload["metadata"])
        self.assertEqual(payload["metadata"]["content"][0]["image_url"]["url"], "asset://file-1")
        self.assertEqual(payload["metadata"]["content"][0]["role"], "reference_image")
        self.assertIs(payload["metadata"]["generate_audio"], False)
        self.assertEqual(runtime.submit_json_task.call_count, 1)

    def test_25_frames_keep_roles_without_registration(self):
        frame = Tensor(np.zeros((1, 512, 512, 3)))
        payload = self.run_node("doubao-seedance-2-5", **{"🎬 首帧图": frame, "🏁 尾帧图": frame})
        self.assertEqual([c["role"] for c in payload["metadata"]["content"]], ["first_frame", "last_frame"])
        self.assertNotIn("seedance_asset_library", payload["metadata"])
        self.assertFalse(self.requests)

    def test_wrapped_video_states_and_failure_reason(self):
        client = base.DapaoSeedanceRelayClient("offline", 60)
        for status in ["NOT_START", "SUBMITTED", "QUEUED", "IN_PROGRESS"]:
            self.assertEqual(base._task_state({"code": 0, "message": "success", "data": {"status": status}})[0], "processing")
        for status in ["SUCCESS", "FAILURE"]:
            response = {"code": 0, "message": "success", "data": {"status": status, "fail_reason": "specific failure" if status == "FAILURE" else ""}}
            with patch.object(client, "_request_json", return_value=response) as request:
                if status == "SUCCESS":
                    self.assertEqual(client.poll("task-test", 60, 5), response)
                else:
                    with self.assertRaisesRegex(base.DapaoSeedanceTaskError, "specific failure"):
                        client.poll("task-test", 60, 5)
                self.assertEqual(request.call_count, 1)

    def test_real_person_rejection_keeps_details_without_retry(self):
        client = base.DapaoSeedanceRelayClient("offline", 60)
        message = "The request failed because the input image 'content[1]' may contain real person."
        response = {"code": "success", "data": {"status": "FAILURE", "fail_reason": message}}
        with patch.object(client, "_request_json", return_value=response) as request:
            with self.assertRaises(base.DapaoSeedanceTaskError) as caught:
                client.poll("task-test", 60, 5)
        self.assertIn("可能包含真人", str(caught.exception))
        self.assertIn(message, str(caught.exception))
        self.assertIs(caught.exception.result, response)
        self.assertEqual(request.call_count, 1)

    def test_25_extend_and_false(self):
        payload = self.run_node("doubao-seedance-2-5", **{"🎞️ 参考任务": "extend", "📦 输出格式": "mov", "🎚️ 码率模式": "high", "🔊 生成音频": False, "🌐 公网素材URL(JSON)": json.dumps({"videos": ["asset://file-video"]})})
        self.assertNotIn("seedance_asset_library", payload["metadata"])
        self.assertFalse(self.requests)
        self.assertEqual(payload["metadata"]["omni_reference_task_type"], "extend")
        self.assertEqual(payload["metadata"]["output_format"], "mov")
        self.assertIs(payload["metadata"]["generate_audio"], False)

    def test_invalid_combinations_never_submit(self):
        frame = Tensor(np.zeros((1, 512, 512, 3)))
        for extra in [{"🎬 首帧图": frame, "🖼️ 参考图1": frame}, {"🏁 尾帧图": frame}, {"🌐 公网素材URL(JSON)": json.dumps({"audios": ["asset://file-audio"]})}, {"⏱️ 時长(秒)": "5", "⏱️ 时长(秒)": "30"}]:
            with self.assertRaises(RuntimeError): self.run_node(**extra)
        runtime.submit_json_task.assert_not_called()
        self.assertFalse(self.uploads)

    def test_registration_failure_does_not_generate_or_retry(self):
        with patch.object(base.DapaoSeedanceRelayClient, "_request_json", return_value={"status": "indeterminate", "registration_id": "sa-test"}) as request:
            with self.assertRaisesRegex(RuntimeError, "indeterminate"):
                self.run_node(**{"🌐 公网素材URL(JSON)": json.dumps({"images": ["asset://file-test"]})})
            self.assertEqual(request.call_count, 1)
        runtime.submit_json_task.assert_not_called()

    def test_registration_poll_uses_registration_id(self):
        client = base.DapaoSeedanceRelayClient("offline", 60)
        with patch.object(client, "_request_json", side_effect=[{"status": "processing", "registration_id": "sa-specific"}, {"status": "ready"}]) as request, patch.object(base.time, "sleep"):
            client.prepare_asset("asset://file-test", "doubao-seedance-2.0")
        self.assertIn("registration_id=sa-specific", request.call_args.args[1])

    def test_list_tasks_overlap_and_exception_propagates(self):
        barrier = threading.Barrier(2, timeout=3)
        def submit(**kw):
            barrier.wait()
            return {"id": "task-test", "status": "completed", "metadata": {"url": "https://example.com/video.mp4"}}
        runtime.submit_json_task.side_effect = submit
        async def run():
            node = base.DapaoSeedance20AllroundVideoNode()
            return await asyncio.gather(node.generate(**self.args()), node.generate(**self.args()))
        self.assertEqual(len(asyncio.run(run())), 2)
        runtime.submit_json_task.side_effect = RuntimeError("offline failure")
        with self.assertRaisesRegex(RuntimeError, "offline failure"): self.run_node()

    def test_real_ffmpeg_preprocessing_and_duration_limits(self):
        import tempfile
        import shutil
        if not shutil.which("ffmpeg") or not shutil.which("ffprobe"):
            self.skipTest("FFmpeg unavailable")
        with tempfile.TemporaryDirectory() as folder:
            video = Path(folder) / "input.mp4"
            media._tool("ffmpeg", ["-v", "error", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720:r=30:d=2", "-c:v", "libx264", "-threads", "2", str(video)])
            part, duration = media._av(video.read_bytes(), "video", False)
            self.assertEqual(part[2], "video/mp4")
            self.assertAlmostEqual(duration, 2, places=1)
            audio = base._audio_to_wav_bytes({"waveform": np.zeros((1, 88200), dtype=np.float32), "sample_rate": 44100})
            part, duration = media._av(audio, "audio", False)
            import wave
            with wave.open(io.BytesIO(part[0])) as wav:
                self.assertEqual(wav.getframerate(), 48000)
                self.assertEqual(wav.getnchannels(), 2)
            self.assertAlmostEqual(duration, 2, places=1)

    def test_gateway_download_never_sends_key_to_signed_url(self):
        redirect = Mock(is_redirect=True, headers={"Location": "https://media.example.com/video.mp4"})
        response = Mock(is_redirect=False)
        response.iter_content.return_value = [b"video-bytes"]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        import tempfile
        with tempfile.TemporaryDirectory() as folder, patch.object(base.requests, "get", side_effect=[redirect, response]) as get:
            adapter = base.DapaoVideoAdapter("https://untrusted.example/video", api_key="offline", task_id="task-test")
            adapter.save_to(str(Path(folder) / "video.mp4"))
            self.assertTrue(get.call_args_list[0].args[0].startswith("https://api.dapaoai.com/v1/videos/"))
            self.assertNotIn("headers", get.call_args_list[1].kwargs)

    def test_missing_upstream_asset_preserves_failure_without_resubmit(self):
        runtime.submit_json_task.side_effect = lambda **kw: {"id": "task-test", "status": "queued"}
        failed = {"id": "task-test", "status": "failed", "error": {"message": "The specified asset asset-test is not found."}}
        original_request = self.request
        def request(method, url, **kw):
            if "/video/generations/" in url:
                response = Mock(status_code=200, headers={})
                response.json.return_value = failed
                return response
            return original_request(method, url, **kw)
        with patch.object(base.requests, "request", side_effect=request):
            with self.assertRaises(RuntimeError) as raised:
                self.run_node(**{"🌐 公网素材URL(JSON)": json.dumps({"images": ["asset://file-test"]})})
        message = str(raised.exception)
        self.assertIn("生成服务找不到引用的上游素材", message)
        self.assertIn('"stage": "video_poll"', message)
        self.assertIn('"registration_id": "sa-test"', message)
        self.assertIn('"status": "failed"', message)
        self.assertIn("asset://file-test", message)
        self.assertEqual(runtime.submit_json_task.call_count, 1)
        self.assertEqual(len(self.requests), 1)
        self.assertFalse(self.uploads)

    def test_seed_is_recovery_salt_not_request_field(self):
        self.run_node(**{"🎲 随机种": 123})
        call = runtime.submit_json_task.call_args.kwargs
        self.assertEqual(call["recovery_salt"], 123)
        self.assertNotIn("seed", call["payload"])
        self.assertTrue(call["reuse_succeeded"])

if __name__ == "__main__": unittest.main()
