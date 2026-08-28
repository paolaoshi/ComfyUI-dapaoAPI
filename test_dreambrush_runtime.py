import base64
import ast
import json
import os
import tempfile
import threading
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import dreambrush_runtime as runtime


class FakeResponse:
    def __init__(self, status_code=200, payload=None, headers=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.headers = headers or {}
        self.text = json.dumps(self._payload, ensure_ascii=False)

    def json(self):
        return self._payload


class DreamBrushRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temporary.name) / "runtime.sqlite3")
        self.environment = mock.patch.dict(os.environ, {"DAPAO_DREAMBRUSH_RUNTIME_DB": self.db_path})
        self.environment.start()
        runtime._STORE = None
        runtime._INFLIGHT_ASSETS.clear()
        runtime._ACTIVE_JOB_KEYS.clear()

    def tearDown(self):
        runtime._STORE = None
        self.environment.stop()
        self.temporary.cleanup()

    @staticmethod
    def asset_payload(content, asset_id="file-one"):
        return {
            "object": "asset",
            "id": asset_id,
            "reference": f"asset://{asset_id}",
            "sha256": runtime.hashlib.sha256(content).hexdigest(),
            "type": "image",
            "mime_type": "image/png",
            "bytes": len(content),
            "expires_at": int(time.time()) + 3600,
        }

    def test_data_uri_is_uploaded_once_and_persistently_reused(self):
        content = b"deterministic-png"
        uri = "data:image/png;base64," + base64.b64encode(content).decode("ascii")
        calls = []

        def request(method, url, **kwargs):
            calls.append((method, url))
            if url.endswith("/v1/assets/resolve"):
                return FakeResponse(200, {"object": "asset.resolve", "data": [], "missing": kwargs["json"]["hashes"]})
            if url.endswith("/v1/assets/uploads"):
                return FakeResponse(200, self.asset_payload(content))
            raise AssertionError(url)

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            first = runtime.externalize_payload_assets(
                {"messages": [{"content": [{"type": "image_url", "image_url": {"url": uri}}]}]},
                "key-one", "https://api.dapaoai.com", 30,
            )
            second = runtime.externalize_payload_assets(
                {"image": uri}, "key-one", "https://api.dapaoai.com", 30,
            )
        self.assertEqual(first["messages"][0]["content"][0]["image_url"]["url"], "asset://file-one")
        self.assertEqual(second["image"], "asset://file-one")
        self.assertEqual(sum(url.endswith("/v1/assets/uploads") for _, url in calls), 1)
        self.assertEqual(sum(url.endswith("/v1/assets/resolve") for _, url in calls), 1)

    def test_gemini_inline_data_becomes_file_data(self):
        content = b"gemini-image"
        payload = {"contents": [{"parts": [{"inlineData": {
            "mimeType": "image/png", "data": base64.b64encode(content).decode("ascii")
        }}, {"text": "keep"}]}]}

        def request(method, url, **kwargs):
            if url.endswith("/resolve"):
                return FakeResponse(200, {"data": [], "missing": kwargs["json"]["hashes"]})
            return FakeResponse(200, self.asset_payload(content, "file-gemini"))

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            transformed = runtime.externalize_payload_assets(payload, "key", runtime.DEFAULT_BASE_URL, 30)
        part = transformed["contents"][0]["parts"][0]
        self.assertNotIn("inlineData", part)
        self.assertEqual(part["fileData"], {"mimeType": "image/png", "fileUri": "asset://file-gemini"})

    def test_raw_input_audio_becomes_asset_reference(self):
        content = b"RIFF-mocked-wave"
        payload = {"type": "input_audio", "input_audio": {
            "data": base64.b64encode(content).decode("ascii"), "format": "wav"
        }}

        def request(method, url, **kwargs):
            if url.endswith("/resolve"):
                return FakeResponse(200, {"data": [], "missing": kwargs["json"]["hashes"]})
            item = self.asset_payload(content, "file-audio")
            item.update({"type": "audio", "mime_type": "audio/wav"})
            return FakeResponse(200, item)

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            transformed = runtime.externalize_payload_assets(payload, "key", runtime.DEFAULT_BASE_URL, 30)
        self.assertEqual(transformed["input_audio"]["data"], "asset://file-audio")

    def test_image_audio_video_share_upload_runtime_without_persisting_secrets_or_bytes(self):
        secret = "sk-never-persist-this-secret"
        blobs = [
            (b"unique-image-payload-9137", "reference.png", "image/png", "file-image"),
            (b"unique-audio-payload-6248", "reference.wav", "audio/wav", "file-audio"),
            (b"unique-video-payload-3571", "reference.mp4", "video/mp4", "file-video"),
        ]

        def request(method, url, **kwargs):
            if url.endswith("/resolve"):
                return FakeResponse(200, {"data": [], "missing": kwargs["json"]["hashes"]})
            content = kwargs["files"]["file"][1]
            mime_type = kwargs["files"]["file"][2]
            match = next(item for item in blobs if item[0] == content)
            item = self.asset_payload(content, match[3])
            item.update({"type": mime_type.split("/", 1)[0], "mime_type": mime_type})
            return FakeResponse(200, item)

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            references = runtime.ensure_asset_references(
                secret, [(content, filename, mime) for content, filename, mime, _asset_id in blobs]
            )
        self.assertEqual(references, ["asset://file-image", "asset://file-audio", "asset://file-video"])
        persisted = Path(self.db_path).read_bytes()
        self.assertNotIn(secret.encode("utf-8"), persisted)
        for content, _filename, _mime, _asset_id in blobs:
            self.assertNotIn(content, persisted)
            self.assertNotIn(base64.b64encode(content), persisted)

    def test_resolve_hit_skips_upload_and_partial_change_uploads_only_new_file(self):
        first = b"first"
        second = b"second"
        upload_hashes = []

        def record(content, asset_id):
            item = self.asset_payload(content, asset_id)
            return item

        resolve_round = 0

        def request(method, url, **kwargs):
            nonlocal resolve_round
            if url.endswith("/resolve"):
                resolve_round += 1
                hashes = kwargs["json"]["hashes"]
                if resolve_round == 1:
                    return FakeResponse(200, {"data": [record(first, "file-first")], "missing": []})
                return FakeResponse(200, {"data": [], "missing": hashes})
            uploaded = kwargs["files"]["file"][1]
            upload_hashes.append(runtime.hashlib.sha256(uploaded).hexdigest())
            return FakeResponse(200, record(uploaded, "file-second"))

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            refs1 = runtime.ensure_asset_references("key", [(first, "first.png", "image/png")])
            refs2 = runtime.ensure_asset_references("key", [
                (first, "first.png", "image/png"), (second, "second.png", "image/png")
            ])
        self.assertEqual(refs1, ["asset://file-first"])
        self.assertEqual(refs2, ["asset://file-first", "asset://file-second"])
        self.assertEqual(upload_hashes, [runtime.hashlib.sha256(second).hexdigest()])

    def test_expired_cache_entry_is_resolved_and_reuploaded(self):
        content = b"expired"
        client = runtime.AssetClient("key", timeout=30)
        digest = runtime.hashlib.sha256(content).hexdigest()
        client.store.save_asset(client.scope, runtime.AssetRecord(
            digest, "file-old", "asset://file-old", int(time.time()) + 10, len(content), "image/png"
        ))
        calls = []

        def request(method, url, **kwargs):
            calls.append(url)
            if url.endswith("/resolve"):
                return FakeResponse(200, {"data": [], "missing": [digest]})
            return FakeResponse(200, self.asset_payload(content, "file-new"))

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            reference = runtime.ensure_asset_references("key", [(content, "expired.png", "image/png")])[0]
        self.assertEqual(reference, "asset://file-new")
        self.assertTrue(any(url.endswith("/resolve") for url in calls))
        self.assertTrue(any(url.endswith("/uploads") for url in calls))

    def test_retry_after_is_honored_for_read_only_resolve(self):
        content = b"retry"
        calls = 0
        sleeps = []

        def request(method, url, **kwargs):
            nonlocal calls
            calls += 1
            if calls == 1:
                return FakeResponse(429, {"error": {"message": "busy"}}, {"Retry-After": "7"})
            if url.endswith("/resolve"):
                return FakeResponse(200, {"data": [self.asset_payload(content, "file-retry")], "missing": []})
            raise AssertionError(url)

        with mock.patch.object(runtime.requests, "request", side_effect=request), mock.patch.object(
            runtime.time, "sleep", side_effect=lambda value: sleeps.append(value)
        ):
            reference = runtime.ensure_asset_references("key", [(content, "retry.png", "image/png")])[0]
        self.assertEqual(reference, "asset://file-retry")
        self.assertEqual(sleeps, [7.0])

    def test_concurrent_asset_requests_use_one_upload(self):
        content = b"same-image-for-every-mapped-prompt"
        upload_count = 0
        upload_lock = threading.Lock()
        start = threading.Barrier(8)

        def request(method, url, **kwargs):
            nonlocal upload_count
            if url.endswith("/resolve"):
                return FakeResponse(200, {"data": [], "missing": kwargs["json"]["hashes"]})
            if url.endswith("/uploads"):
                with upload_lock:
                    upload_count += 1
                time.sleep(0.03)
                return FakeResponse(200, self.asset_payload(content))
            raise AssertionError(url)

        def worker(_index):
            start.wait()
            return runtime.ensure_asset_references("key", [(content, "same.png", "image/png")])[0]

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            with ThreadPoolExecutor(max_workers=8) as executor:
                results = list(executor.map(worker, range(8)))
        self.assertEqual(results, ["asset://file-one"] * 8)
        self.assertEqual(upload_count, 1)

    def test_queue_happy_path_and_backoff_states(self):
        statuses = iter(["queued", "running", "succeeded"])
        submitted_headers = []
        sleeps = []

        def request(method, url, **kwargs):
            if method == "POST" and url.endswith("/v1/images/generations"):
                submitted_headers.append(dict(kwargs["headers"]))
                self.assertNotIn("async", kwargs["json"])
                return FakeResponse(202, {"id": "job-happy", "status": "queued"})
            if url.endswith("/v1/queue/jobs/job-happy"):
                return FakeResponse(200, {"id": "job-happy", "status": next(statuses)})
            if url.endswith("/v1/queue/jobs/job-happy/result"):
                return FakeResponse(200, {"data": [{"url": "https://result/image.png"}]})
            raise AssertionError(url)

        with mock.patch.object(runtime.requests, "request", side_effect=request), mock.patch.object(
            runtime.time, "sleep", side_effect=lambda value: sleeps.append(value)
        ), mock.patch.object(runtime.random, "uniform", return_value=0.0):
            result = runtime.submit_json_task(
                api_key="key", endpoint="/v1/images/generations",
                payload={"model": "image", "prompt": "one", "async": True}, timeout=30,
            )
        self.assertEqual(result["_dapao_queue"]["job_id"], "job-happy")
        self.assertEqual([round(value) for value in sleeps], [2, 3])
        self.assertEqual(submitted_headers[0]["Prefer"], "respond-async")
        self.assertTrue(submitted_headers[0]["Idempotency-Key"].startswith("dapao-"))

    def test_network_recovery_reuses_original_idempotency_key(self):
        keys = []
        phase = {"fail": True}

        def request(method, url, **kwargs):
            if method == "POST":
                keys.append(kwargs["headers"]["Idempotency-Key"])
                if phase["fail"]:
                    raise runtime.requests.Timeout("lost response")
                return FakeResponse(200, {"choices": [{"message": {"content": "ok"}}]})
            raise AssertionError(url)

        with mock.patch.object(runtime.requests, "request", side_effect=request), mock.patch.object(runtime.time, "sleep"):
            with self.assertRaises(runtime.DreamBrushRuntimeError):
                runtime.submit_json_task(
                    api_key="key", endpoint="/v1/chat/completions",
                    payload={"model": "llm", "messages": [{"role": "user", "content": "same"}]}, timeout=30,
                )
            self.assertEqual(len(keys), 1, "付费提交断线后不得在同一次执行中自动重试")
            phase["fail"] = False
            result = runtime.submit_json_task(
                api_key="key", endpoint="/v1/chat/completions",
                payload={"model": "llm", "messages": [{"role": "user", "content": "same"}]}, timeout=30,
            )
        self.assertEqual(result["choices"][0]["message"]["content"], "ok")
        self.assertEqual(len(keys), 2)
        self.assertEqual(len(set(keys)), 1)

    def test_terminal_queue_states_are_not_resubmitted(self):
        for state in ("failed", "canceled", "expired", "indeterminate"):
            with self.subTest(state=state):
                runtime._STORE = None
                post_count = 0

                def request(method, url, **kwargs):
                    nonlocal post_count
                    if method == "POST":
                        post_count += 1
                        return FakeResponse(202, {"id": f"job-{state}", "status": "queued"})
                    return FakeResponse(200, {"id": f"job-{state}", "status": state, "message": "mock"})

                error_type = runtime.DreamBrushIndeterminateError if state == "indeterminate" else runtime.DreamBrushRuntimeError
                with mock.patch.object(runtime.requests, "request", side_effect=request):
                    with self.assertRaises(error_type):
                        runtime.submit_json_task(
                            api_key=f"key-{state}", endpoint="/v1/test",
                            payload={"model": "test", "prompt": state}, timeout=30,
                        )
                    if state == "indeterminate":
                        with self.assertRaises(runtime.DreamBrushIndeterminateError):
                            runtime.submit_json_task(
                                api_key=f"key-{state}", endpoint="/v1/test",
                                payload={"model": "test", "prompt": state}, timeout=30,
                            )
                        self.assertEqual(post_count, 1)

    def test_interruption_cancels_a_queued_job(self):
        deleted = []

        def request(method, url, **kwargs):
            return FakeResponse(202, {"id": "job-cancel", "status": "queued"})

        with mock.patch.object(runtime.requests, "request", side_effect=request), mock.patch.object(
            runtime.requests, "get", return_value=FakeResponse(200, {"id": "job-cancel", "status": "queued"})
        ), mock.patch.object(
            runtime.requests, "delete", side_effect=lambda url, **kwargs: deleted.append(url) or FakeResponse(200, {})
        ):
            with self.assertRaisesRegex(RuntimeError, "user stop"):
                runtime.submit_json_task(
                    api_key="key", endpoint="/v1/test", payload={"prompt": "cancel"}, timeout=30,
                    interrupt_callback=lambda: (_ for _ in ()).throw(RuntimeError("user stop")),
                )
        self.assertEqual(deleted, [f"{runtime.DEFAULT_BASE_URL}/v1/queue/jobs/job-cancel"])

    def test_submit_gate_caps_twelve_tasks_at_four(self):
        active = 0
        maximum = 0
        lock = threading.Lock()

        def request(method, url, **kwargs):
            nonlocal active, maximum
            with lock:
                active += 1
                maximum = max(maximum, active)
            time.sleep(0.025)
            with lock:
                active -= 1
            return FakeResponse(200, {"ok": kwargs["json"]["prompt"]})

        def worker(index):
            return runtime.submit_json_task(
                api_key="key", endpoint="/v1/test", payload={"prompt": f"task-{index}"}, timeout=30,
            )["ok"]

        with mock.patch.object(runtime.requests, "request", side_effect=request):
            with ThreadPoolExecutor(max_workers=12) as executor:
                results = list(executor.map(worker, range(12)))
        self.assertEqual(results, [f"task-{index}" for index in range(12)])
        self.assertLessEqual(maximum, 4)
        self.assertGreaterEqual(maximum, 2)

    def test_all_maintained_api_modules_use_the_shared_paid_submit_runtime(self):
        root = Path(__file__).resolve().parent
        direct_modules = [
            "banana_allround_node.py", "gpt_image_2_allround_node.py", "gpt_llm_chat_node.py",
            "seedream_v5_pro_allround_node.py", "seedream_v5_pro_layer_decomposition_node.py",
            "seedance20_allround_video_node.py", "detail_flow_prompt_node.py", "h3_video_prompt_node.py",
            "image_prompt_director_node.py", "music3_caption_prompt_node.py",
            "seedance20_director_node.py", "visual_style_prompt_node.py",
        ]
        for filename in direct_modules:
            source = (root / filename).read_text(encoding="utf-8")
            self.assertIn("submit_json_task", source, filename)
            self.assertNotIn("requests.post(", source, filename)
        multi_turn = (root / "api_multi_turn_chat_node.py").read_text(encoding="utf-8")
        self.assertIn("from .gpt_llm_chat_node import DapaoGPTLLMClient", multi_turn)

    def test_all_maintained_llm_nodes_share_the_deepseek_v4_catalogue(self):
        from llm_model_options import DEFAULT_LLM_MODEL, LLM_MODEL_OPTIONS

        expected = (
            "deepseek-v4-flash-vision-exp",
            "deepseek-v4-pro",
            "deepseek-v4-flash",
        )
        self.assertEqual(DEFAULT_LLM_MODEL, "gemini-3.7-flash")
        for model in expected:
            self.assertEqual(LLM_MODEL_OPTIONS.count(model), 1)

        root = Path(__file__).resolve().parent
        llm_nodes = (
            "gpt_llm_chat_node.py",
            "h3_video_prompt_node.py",
            "seedance20_director_node.py",
            "image_prompt_director_node.py",
            "visual_style_prompt_node.py",
            "detail_flow_prompt_node.py",
            "music3_caption_prompt_node.py",
            "api_multi_turn_chat_node.py",
        )
        for filename in llm_nodes:
            source = (root / filename).read_text(encoding="utf-8")
            self.assertIn(".llm_model_options import", source, filename)
            self.assertIn("LLM_MODEL_OPTIONS", source, filename)

    def test_all_maintained_network_execution_methods_are_coroutines(self):
        root = Path(__file__).resolve().parent
        target_categories = ("🍬大炮AI主力维护🍬", "🍬大炮API常用工具🍬")
        network_count = 0
        local_count = 0
        for path in root.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            constants = {}
            for node in tree.body:
                if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            constants[target.id] = node.value.value
            for node in (item for item in tree.body if isinstance(item, ast.ClassDef)):
                category = function = None
                methods = {}
                for member in node.body:
                    if isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods[member.name] = isinstance(member, ast.AsyncFunctionDef)
                    if not isinstance(member, ast.Assign):
                        continue
                    for target in member.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        if target.id == "CATEGORY":
                            category = (
                                member.value.value if isinstance(member.value, ast.Constant)
                                else constants.get(getattr(member.value, "id", ""))
                            )
                        elif target.id == "FUNCTION" and isinstance(member.value, ast.Constant):
                            function = member.value.value
                if not category or not any(value in category for value in target_categories):
                    continue
                if methods.get(function):
                    network_count += 1
                else:
                    local_count += 1
        self.assertEqual(network_count, 13)
        self.assertEqual(local_count, 5)


if __name__ == "__main__":
    unittest.main()
