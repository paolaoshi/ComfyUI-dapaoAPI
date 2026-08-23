"""Paid-API-free regression checks for dapaoAI Skill multi-turn chat."""

from __future__ import annotations

import asyncio
import base64
import importlib
import importlib.util
import inspect
import io
import json
import sys
import tempfile
import threading
import time
import types
import unittest
import zipfile
from pathlib import Path

try:
    from PIL import Image
except ModuleNotFoundError:
    Image = None
try:
    import numpy as _numpy
except ModuleNotFoundError:
    _numpy = None


ROOT = Path(__file__).resolve().parent
PACKAGE = "dapao_api_testpkg"
if PACKAGE not in sys.modules:
    package = types.ModuleType(PACKAGE)
    package.__path__ = [str(ROOT)]
    sys.modules[PACKAGE] = package

# The lean WSL Python used by CI may not carry ComfyUI's Pillow/numpy/requests
# stack. Stub only import-time surfaces; the real portable-Python run exercises
# the actual modules, while paid HTTP is always replaced below.
if Image is None:
    pil_module = types.ModuleType("PIL")
    pil_module.Image = types.SimpleNamespace(Image=object)
    sys.modules.setdefault("PIL", pil_module)
if Image is None or _numpy is None:
    image_utils = types.ModuleType(f"{PACKAGE}.image_input_utils")
    image_utils.MAX_INPUT_IMAGE_EDGE = 2048
    image_utils.resize_pil_for_input = lambda image, max_edge=2048: image
    image_utils.tensor_to_png_data_uris = lambda image, max_edge=2048: ["data:image/png;base64,ZmFrZQ=="]
    sys.modules[f"{PACKAGE}.image_input_utils"] = image_utils

fake_gpt_module = types.ModuleType(f"{PACKAGE}.gpt_llm_chat_node")
fake_gpt_module.DapaoGPTLLMClient = object
fake_gpt_module._extract_text = lambda result: result.get("choices", [{}])[0].get("message", {}).get("content", "")
sys.modules[f"{PACKAGE}.gpt_llm_chat_node"] = fake_gpt_module

chat_module = importlib.import_module(f"{PACKAGE}.api_multi_turn_chat_node")
runtime_module = importlib.import_module(f"{PACKAGE}.api_skill_runtime")


class FakeClient:
    active = 0
    max_active = 0
    lock = threading.Lock()
    fail = False
    payloads = []

    def __init__(self, api_key, timeout):
        self.api_key = api_key
        self.timeout = timeout

    def chat(self, payload):
        type(self).payloads.append(payload)
        with self.lock:
            type(self).active += 1
            type(self).max_active = max(type(self).max_active, type(self).active)
        try:
            time.sleep(0.12)
            if type(self).fail:
                raise RuntimeError("模拟接口错误")
            user = payload["messages"][-1]["content"]
            if isinstance(user, list):
                user = user[0]["text"]
            text = f"模拟回复：{user}"
            return {
                "choices": [{"message": {"content": text}}],
                "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
            }
        finally:
            with self.lock:
                type(self).active -= 1


class APIMultiTurnChatTests(unittest.TestCase):
    def setUp(self):
        self.original_client = chat_module.DapaoGPTLLMClient
        chat_module.DapaoGPTLLMClient = FakeClient
        FakeClient.active = 0
        FakeClient.max_active = 0
        FakeClient.fail = False
        FakeClient.payloads = []

    def tearDown(self):
        chat_module.DapaoGPTLLMClient = self.original_client

    @staticmethod
    def kwargs(message="你好"):
        return {
            "🤖API模型": {
                "api_key": "test-key",
                "model": "gemini-3.7-flash",
                "timeout": 30,
                "context_limit": 8192,
            },
            "💬本轮消息": message,
            "📚会话历史": "[]",
            "🖼️图片引用": "[]",
            "🧩流程状态": "{}",
            "🧩选项": "[]",
            "🆔请求标识": "1787390000000-test",
        }

    def test_public_method_is_coroutine_and_single_output_contract_is_stable(self):
        self.assertTrue(inspect.iscoroutinefunction(chat_module.DapaoAPIMultiTurnChatNode.chat))
        self.assertFalse(hasattr(chat_module.DapaoAPIMultiTurnChatNode, "INPUT_IS_LIST"))
        self.assertEqual(chat_module.DapaoAPIMultiTurnChatNode.CATEGORY, "🤖dapaoAPI/🍬大炮API常用工具🍬")
        result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**self.kwargs()))
        self.assertEqual(len(result["result"]), 3)
        self.assertEqual(result["result"][0], "模拟回复：你好")
        self.assertEqual(json.loads(result["result"][1]), json.loads(result["ui"]["📚会话历史"][0]))
        self.assertEqual(result["result"][2], "模拟回复：你好")
        self.assertEqual(chat_module.DapaoAPIMultiTurnChatNode.RETURN_TYPES, ("STRING", "STRING", "STRING"))
        self.assertEqual(
            chat_module.DapaoAPIMultiTurnChatNode.RETURN_NAMES,
            ("💬助手回复", "📚会话历史JSON", "🧩Skill最终结果"),
        )
        final = chat_module.DapaoAPIMultiTurnChatNode._result([], "阶段回复", {"final_result": "最终成品"}, [], True, {})
        self.assertEqual(final["result"], ("阶段回复", "[]", "最终成品"))
        self.assertEqual(
            set(result["ui"]),
            {"📚会话历史", "💬助手回复", "🧩流程状态", "🧩选项", "📊上下文", "✅已发送"},
        )
        history = json.loads(result["ui"]["📚会话历史"][0])
        self.assertEqual([item["role"] for item in history], ["user", "assistant"])
        context = json.loads(result["ui"]["📊上下文"][0])
        self.assertEqual(context["usage_source"], "api")
        self.assertEqual(context["api_calls"], 1)

    def test_empty_global_run_replays_latest_outputs_without_an_api_call(self):
        class ForbiddenClient:
            def __init__(self, *args, **kwargs):
                raise AssertionError("空草稿回填输出时不得创建API客户端")

        history = [
            {"role": "user", "content": "上一轮问题", "token_count": 6, "created_at": 1},
            {"role": "assistant", "content": "上一轮助手回复", "token_count": 8, "created_at": 2},
        ]
        values = self.kwargs("")
        values["📚会话历史"] = json.dumps(history, ensure_ascii=False)
        chat_module.DapaoGPTLLMClient = ForbiddenClient
        result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))
        self.assertEqual(result["result"][0], "上一轮助手回复")
        self.assertEqual(json.loads(result["result"][1]), history)
        self.assertEqual(result["result"][2], "上一轮助手回复")
        self.assertFalse(result["ui"]["✅已发送"][0])

        values["🧩流程状态"] = json.dumps({"final_result": "Skill完整最终成品"}, ensure_ascii=False)
        final_result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))
        self.assertEqual(final_result["result"][0], "上一轮助手回复")
        self.assertEqual(final_result["result"][2], "Skill完整最终成品")

    def test_context_cutoff_preserves_display_history_but_excludes_old_api_context(self):
        history = [
            {"role": "user", "content": "旧问题", "created_at": 10},
            {"role": "assistant", "content": "旧回答", "created_at": 20},
            {"role": "user", "content": "新问题", "created_at": 200},
            {"role": "assistant", "content": "新回答", "created_at": 210},
        ]
        values = self.kwargs("继续处理")
        values["📚会话历史"] = json.dumps(history, ensure_ascii=False)
        values["🧩流程状态"] = json.dumps({"context_cutoff": 100}, ensure_ascii=False)
        result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))

        sent_text = json.dumps(FakeClient.payloads[-1]["messages"], ensure_ascii=False)
        self.assertNotIn("旧问题", sent_text)
        self.assertNotIn("旧回答", sent_text)
        self.assertIn("新问题", sent_text)
        self.assertIn("新回答", sent_text)
        returned = json.loads(result["result"][1])
        self.assertEqual([item["content"] for item in returned[:4]], ["旧问题", "旧回答", "新问题", "新回答"])
        self.assertEqual(json.loads(result["ui"]["🧩流程状态"][0])["context_cutoff"], 100)

    def test_publish_final_never_constructs_api_client_and_prefers_skill_result(self):
        class ForbiddenClient:
            def __init__(self, *args, **kwargs):
                raise AssertionError("发送最终状态不得创建API客户端")

        values = self.kwargs("")
        values["🤖API模型"] = None
        values["🧭执行动作"] = "publish_final"
        values["📚会话历史"] = json.dumps([
            {"role": "assistant", "content": "最近阶段回复", "created_at": 20},
        ], ensure_ascii=False)
        values["🧩流程状态"] = json.dumps({"final_result": "Skill最终成品", "context_cutoff": 10}, ensure_ascii=False)
        values["🧩选项"] = json.dumps(["继续", "修改"], ensure_ascii=False)
        chat_module.DapaoGPTLLMClient = ForbiddenClient
        result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))
        self.assertEqual(result["result"], ("最近阶段回复", result["result"][1], "Skill最终成品"))
        self.assertEqual(json.loads(result["ui"]["🧩选项"][0]), ["继续", "修改"])
        self.assertFalse(result["ui"]["✅已发送"][0])

    def test_publish_final_falls_back_to_latest_assistant_reply(self):
        values = self.kwargs("")
        values["🧭执行动作"] = "publish_final"
        values["📚会话历史"] = json.dumps([
            {"role": "assistant", "content": "可发布的最近回复", "created_at": 20},
        ], ensure_ascii=False)
        result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))
        self.assertEqual(result["result"][0], "可发布的最近回复")
        self.assertEqual(result["result"][2], "可发布的最近回复")
        self.assertEqual(FakeClient.payloads, [])

    def test_all_five_nodes_have_complete_comfy_contracts(self):
        for node_class in (
            chat_module.DapaoAPIChatMaterialLibraryNode,
            chat_module.DapaoAPILLMConfigNode,
            chat_module.DapaoAPIChatSettingsNode,
            chat_module.DapaoAPISkillLoaderNode,
            chat_module.DapaoAPIMultiTurnChatNode,
        ):
            self.assertTrue(callable(node_class.INPUT_TYPES))
            self.assertTrue(hasattr(node_class, "RETURN_TYPES"))
            self.assertTrue(hasattr(node_class, "RETURN_NAMES"))
            self.assertTrue(hasattr(node_class, "FUNCTION"))
            self.assertTrue(hasattr(node_class, "CATEGORY"))

    def test_chat_panel_height_tracks_user_resizing_without_an_upper_cap(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        self.assertIn("getMaxHeight: () => undefined", source)
        self.assertIn("nodeHeight - CHAT_NODE_CHROME_HEIGHT", source)
        self.assertIn("updateLayout(size || this.size)", source)
        self.assertNotIn("CHAT_NODE_MAX_HEIGHT", source)
        self.assertNotIn("getHeight: () => CHAT_PANEL_HEIGHT", source)

    def test_chat_composer_uses_material_library_instead_of_direct_image_upload(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        self.assertIn("输入消息；键入 @ 选择素材", source)
        self.assertIn("actions.append(sendButton, clearButton, clearContextButton, publishButton)", source)
        self.assertIn("grid-template-columns: repeat(2, 1fr)", source)
        self.assertNotIn('"插入图片"', source)
        self.assertNotIn('api.fetchApi("/upload/image"', source)
        self.assertNotIn("function uploadImage", source)

    def test_context_clear_and_on_demand_publish_frontend_contract(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        for label in ("清除上下文", "发送最终状态", "撤销清除上下文"):
            self.assertIn(label, source)
        self.assertIn('"🧭执行动作": "chat"', source)
        self.assertIn('"🧭执行动作": "publish_final"', source)
        self.assertIn("async function chatAndDownstreamPrompt", source)
        self.assertIn("const dependents = new Map()", source)
        self.assertIn("const descendants = new Set([targetId])", source)
        self.assertIn("descendants.forEach(addDependencies)", source)
        self.assertIn("filter(([id]) => keep.has(String(id)))", source)
        self.assertIn("if (!scoped.downstreamCount)", source)
        self.assertIn("context_cutoff: cutoff", source)
        self.assertIn('skill: ""', source)
        self.assertIn('loaded_references: []', source)
        self.assertIn('final_result: ""', source)
        self.assertIn('rememberUndo(snapshot, "撤销清除上下文")', source)

    def test_skill_state_v3_normalizes_context_cutoff_safely(self):
        state = runtime_module.normalize_state({
            "skill": "demo",
            "loaded_references": ["references/a.md"],
            "context_cutoff": "123",
        })
        self.assertEqual(state["version"], 3)
        self.assertEqual(state["context_cutoff"], 123)
        self.assertEqual(runtime_module.normalize_state({"context_cutoff": "bad"})["context_cutoff"], 0)

    def test_chat_frontend_exposes_safe_markdown_session_branch_and_usage_tools(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        self.assertIn("function renderMarkdown(raw)", source)
        self.assertIn("code.textContent = codeText", source)
        self.assertIn('link.rel = "noopener noreferrer"', source)
        self.assertNotIn("innerHTML", source)
        for label in ("导出MD", "导出JSON", "导入会话", "撤销清空", "回到底部", "编辑重发", "从此删除"):
            self.assertIn(label, source)
        self.assertIn("resize: vertical", source)
        self.assertIn("const sessionSnapshot = () =>", source)
        self.assertIn("const beginBranchEdit = (index) =>", source)
        self.assertIn("const deleteFrom = (index, button) =>", source)
        self.assertIn("pendingBranchRollback", source)
        self.assertIn("function usageSummary(history)", source)
        self.assertIn("费用以后台为准", source)
        self.assertIn("if (sent || Object.keys(parsedContext).length)", source)

    def test_explicit_service_cost_and_usage_are_preserved_without_invented_prices(self):
        self.assertEqual(
            chat_module._response_cost({"usage": {"cost": "0.125", "currency": "CNY"}}),
            (0.125, "CNY"),
        )
        self.assertEqual(chat_module._response_cost({"usage": {"total_tokens": 10}}), (None, ""))

        class CostClient:
            def __init__(self, api_key, timeout):
                self.api_key = api_key
                self.timeout = timeout

            def chat(self, payload):
                return {
                    "choices": [{"message": {"content": "带费用回复"}}],
                    "usage": {
                        "prompt_tokens": 80,
                        "completion_tokens": 20,
                        "total_tokens": 100,
                        "cost": 0.015,
                        "currency": "CNY",
                    },
                }

        chat_module.DapaoGPTLLMClient = CostClient
        result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**self.kwargs("费用测试")))
        history = json.loads(result["ui"]["📚会话历史"][0])
        usage = history[-1]["usage"]
        self.assertEqual(usage["prompt_tokens"], 80)
        self.assertEqual(usage["completion_tokens"], 20)
        self.assertEqual(usage["total_tokens"], 100)
        self.assertEqual(usage["cost"], 0.015)
        self.assertEqual(usage["currency"], "CNY")
        context = json.loads(result["ui"]["📊上下文"][0])
        self.assertEqual(context["round_cost"], 0.015)
        self.assertEqual(context["cost_source"], "api")

        restored = runtime_module.normalize_history(json.dumps(history, ensure_ascii=False))
        self.assertEqual(restored[-1]["usage"], usage)

    def test_material_previews_follow_live_upstream_image_changes(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        load_image = source.index('if (filename && nodeClass(node) === "LoadImage")')
        cached_output = source.index("const output = app.nodeOutputs")
        self.assertLess(load_image, cached_output, "LoadImage当前选择必须优先于旧执行缓存")
        self.assertIn("function materialSourceSignature(manifest)", source)
        self.assertIn("window.setInterval(() => {", source)
        self.assertIn("materialSourceSignature(manifest) !== lastSourceSignature", source)
        self.assertIn("window.clearInterval(liveRefreshTimer)", source)
        self.assertIn("preview_key }) => ({ kind, slot, token, label, preview_key })", source)
        self.assertIn("materialPreviewEpoch += 1", source)
        self.assertIn("refreshMaterialLibraries(); refreshChatMaterialManifests();", source)

    def test_skill_optimizer_reads_values_from_connected_primitive_nodes(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        self.assertIn("function scalarOutputValue(source, visited = new Set())", source)
        self.assertIn("return scalarOutputValue(inputOrigin(source, source.inputs[0].name), visited);", source)
        self.assertIn("function connectedWidgetValue(node, inputName, fallback)", source)
        self.assertIn('connectedWidgetValue(source, "🔑 API密钥", "")', source)
        self.assertIn("const local = widget(node, inputName)?.value;", source)

    def test_skill_optimizer_runs_directly_as_one_explicit_post(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        handler = source[source.index("const optimize = async (scope)"):source.index("const upload = async")]
        self.assertNotIn("window.confirm", handler)
        self.assertIn('fetch(viewUrl(path), {', source)
        self.assertIn('method: "POST"', source)
        self.assertEqual(handler.count('request("/dapao/api-skills/optimize-display-names"'), 1)
        self.assertIn('optimizeCurrentButton.addEventListener("click", () => optimize("selected"))', handler)
        self.assertIn('optimizeAllButton.addEventListener("click", () => optimize("all"))', handler)
        self.assertIn("Number(catalog.version || 0) >= 2", source)
        self.assertIn("AI优化按钮已禁用", source)
        backend = (ROOT / "__init__.py").read_text(encoding="utf-8")
        self.assertIn('routes.post("/dapao/api-skills/optimize-display-names")', backend)

    def test_framework_style_list_tasks_overlap(self):
        async def run_tasks():
            node = chat_module.DapaoAPIMultiTurnChatNode()
            return await asyncio.gather(
                node.chat(**self.kwargs("任务A")),
                node.chat(**self.kwargs("任务B")),
                node.chat(**self.kwargs("任务C")),
            )

        results = asyncio.run(run_tasks())
        self.assertEqual(len(results), 3)
        self.assertGreaterEqual(FakeClient.max_active, 2)

    def test_image_only_message_gets_a_default_instruction(self):
        values = self.kwargs("")
        values["🖼️图片引用"] = json.dumps([
            {"filename": "reference.png", "subfolder": "dapao_api_chat", "type": "input"}
        ])
        original = chat_module.current_message_content
        chat_module.current_message_content = lambda text, images, materials, max_edge, config: (
            text,
            {"image_parts": len(images), "video_frames": 0, "audio_seconds": 0.0},
        )
        try:
            result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))
        finally:
            chat_module.current_message_content = original
        history = json.loads(result["ui"]["📚会话历史"][0])
        self.assertEqual(history[0]["content"], "请分析上传的图片，并根据当前对话或Skill继续处理。")
        self.assertEqual(history[0]["images"][0]["filename"], "reference.png")

    def test_material_library_is_passive_and_keeps_runtime_objects(self):
        image = types.SimpleNamespace(shape=(1, 64, 64, 3))
        video = object()
        library = chat_module.DapaoAPIChatMaterialLibraryNode().build_library(**{
            "🏷️素材别名": '{"图片1":"产品正面"}',
            "🖼️图片1": image,
            "🎞️视频2": video,
        })[0]
        self.assertEqual([item["token"] for item in library["items"]], ["@图片1", "@视频2"])
        self.assertEqual(library["items"][0]["label"], "产品正面")
        self.assertIs(library["items"][0]["value"], image)
        self.assertIs(library["items"][1]["value"], video)

    def test_only_current_turn_mentions_are_prepared(self):
        first, second = object(), object()
        library = {"version": 1, "items": [
            {"kind": "image", "slot": 1, "token": "@图片1", "label": "正面", "value": first},
            {"kind": "image", "slot": 2, "token": "@图片2", "label": "背面", "value": second},
        ]}
        captured = []
        original = chat_module.current_message_content

        def fake_content(text, images, materials, max_edge, config):
            captured.extend(materials)
            return text, {"image_parts": len(materials), "video_frames": 0, "audio_seconds": 0.0}

        chat_module.current_message_content = fake_content
        values = self.kwargs("只分析 @图片2")
        values["📦素材库"] = library
        try:
            result = asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))
        finally:
            chat_module.current_message_content = original
        self.assertEqual([item["token"] for item in captured], ["@图片2"])
        history = json.loads(result["ui"]["📚会话历史"][0])
        self.assertEqual([item["token"] for item in history[0]["materials"]], ["@图片2"])

    def test_unknown_or_disconnected_material_token_is_rejected_before_api(self):
        values = self.kwargs("分析 @视频1")
        values["📦素材库"] = {"version": 1, "items": []}
        with self.assertRaisesRegex(ValueError, "未连接|失效"):
            asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**values))

    def test_two_digit_image_token_is_resolved_as_one_stable_reference(self):
        marker = object()
        library = {"version": 1, "items": [
            {"kind": "image", "slot": 10, "token": "@图片10", "label": "第十张", "value": marker},
        ]}
        selected = runtime_module.select_material_mentions("比较 @图片10 的构图", library)
        self.assertEqual(len(selected), 1)
        self.assertIs(selected[0]["value"], marker)

    def test_historical_media_metadata_is_not_resent(self):
        history = [{"role": "user", "content": "看图", "images": [{"filename": "old.png", "subfolder": ""}]}]
        self.assertEqual(runtime_module.api_messages(history, 2048), [{"role": "user", "content": "看图"}])

    def test_api_exception_still_propagates(self):
        FakeClient.fail = True
        with self.assertRaisesRegex(RuntimeError, "模拟接口错误"):
            asyncio.run(chat_module.DapaoAPIMultiTurnChatNode().chat(**self.kwargs()))

    def test_skill_scan_and_state_protocol(self):
        skills = runtime_module.list_skills()
        self.assertTrue(skills, "应从API目录或同级本地插件扫描到至少一个Skill")
        body, state = runtime_module.parse_skill_reply(
            '正文<dapao_local_skill_state>{"stage":"确认","options":["继续"],"final":false}</dapao_local_skill_state>'
        )
        self.assertEqual(body, "正文")
        self.assertEqual(state["stage"], "确认")

    def test_skill_heading_parser_ignores_shell_comments_inside_fences(self):
        body = "---\nname: demo\ndescription: demo\n---\n# Real Title\n```bash\n# 这不是显示名称：\n```\n# 后续标题"
        self.assertEqual(runtime_module._heading(body), "Real Title")
        self.assertEqual(runtime_module._heading(body, chinese_only=True), "")

    def test_nested_repository_skills_are_discovered_and_old_labels_resolve_by_id(self):
        ids = {item["id"] for item in runtime_module.list_skills()}
        self.assertIn("img-gen-taste", ids)
        self.assertIn("img-gen-prompts", ids)
        self.assertEqual(runtime_module.resolve_skill_id("任何旧名字 [gpt-image-2]"), "gpt-image-2")

    def test_manual_skill_display_name_is_independent_and_resettable(self):
        original_root = runtime_module.SKILLS_ROOT
        original_alias = runtime_module.SKILL_ALIAS_PATH
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            skill = root / "display-demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: display-demo\ndescription: Display test.\n---\n# Display Demo\n",
                encoding="utf-8",
            )
            runtime_module.SKILLS_ROOT = root
            runtime_module.SKILL_ALIAS_PATH = Path(temporary) / "aliases.json"
            try:
                catalog = runtime_module.set_skill_display_name("display-demo", "显示名称测试")
                item = next(value for value in catalog["skills"] if value["id"] == "display-demo")
                self.assertEqual(item["display_name"], "显示名称测试")
                self.assertEqual(item["display_source"], "manual")
                self.assertEqual((skill / "SKILL.md").read_text(encoding="utf-8").splitlines()[1], "name: display-demo")
                catalog = runtime_module.set_skill_display_name("display-demo", None)
                item = next(value for value in catalog["skills"] if value["id"] == "display-demo")
                self.assertEqual(item["display_name"], "Display Demo")
            finally:
                runtime_module.SKILLS_ROOT = original_root
                runtime_module.SKILL_ALIAS_PATH = original_alias

    def test_zip_skill_install_is_validated_and_extracted_without_execution(self):
        original_root = runtime_module.SKILLS_ROOT
        original_alias = runtime_module.SKILL_ALIAS_PATH
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            archive = Path(temporary) / "safe.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("safe-skill/SKILL.md", "---\nname: safe-skill\ndescription: Safe upload.\n---\n# Safe\n")
                handle.writestr("safe-skill/scripts/tool.py", "raise RuntimeError('must not execute')\n")
            runtime_module.SKILLS_ROOT = root
            runtime_module.SKILL_ALIAS_PATH = Path(temporary) / "aliases.json"
            try:
                result = runtime_module.install_uploaded_skills([(archive.name, archive)], "zip")
                self.assertEqual(result["installed_ids"], ["safe-skill"])
                self.assertTrue((root / "safe-skill" / "SKILL.md").is_file())
                self.assertTrue((root / "safe-skill" / "scripts" / "tool.py").is_file())
            finally:
                runtime_module.SKILLS_ROOT = original_root
                runtime_module.SKILL_ALIAS_PATH = original_alias

    def test_folder_skill_upload_preserves_relative_resources(self):
        original_root = runtime_module.SKILLS_ROOT
        original_alias = runtime_module.SKILL_ALIAS_PATH
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            root = temporary_root / "skills"
            skill_file = temporary_root / "skill.md"
            reference_file = temporary_root / "guide.md"
            skill_file.write_text("---\nname: folder-skill\ndescription: Folder upload.\n---\n# Folder Skill\n", encoding="utf-8")
            reference_file.write_text("reference", encoding="utf-8")
            runtime_module.SKILLS_ROOT = root
            runtime_module.SKILL_ALIAS_PATH = temporary_root / "aliases.json"
            try:
                result = runtime_module.install_uploaded_skills([
                    ("folder-skill/SKILL.md", skill_file),
                    ("folder-skill/references/guide.md", reference_file),
                ], "folder")
                self.assertEqual(result["installed_ids"], ["folder-skill"])
                self.assertEqual((root / "folder-skill" / "references" / "guide.md").read_text(encoding="utf-8"), "reference")
            finally:
                runtime_module.SKILLS_ROOT = original_root
                runtime_module.SKILL_ALIAS_PATH = original_alias

    def test_skill_loader_frontend_exposes_alias_ai_zip_and_folder_controls(self):
        source = (ROOT / "web" / "js" / "dapao_api_multi_turn_chat_ui.js").read_text(encoding="utf-8")
        for marker in ("保存显示名", "优化当前技能", "优化全部技能", "上传ZIP", "上传文件夹", "webkitdirectory"):
            self.assertIn(marker, source)
        self.assertIn("/dapao/api-skills/install", source)
        self.assertIn("/dapao/api-skills/optimize-display-names", source)

    def test_zip_path_traversal_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("../escape.txt", "blocked")
            with self.assertRaisesRegex(ValueError, "不安全路径"):
                runtime_module.install_uploaded_skills([(archive.name, archive)], "zip")
            absolute = Path(temporary) / "absolute.zip"
            with zipfile.ZipFile(absolute, "w") as handle:
                handle.writestr("/absolute.txt", "blocked")
            with self.assertRaisesRegex(ValueError, "无效文件路径"):
                runtime_module.install_uploaded_skills([(absolute.name, absolute)], "zip")

    def test_repository_bundle_is_preserved_and_conflicts_do_not_overwrite(self):
        original_root = runtime_module.SKILLS_ROOT
        original_alias = runtime_module.SKILL_ALIAS_PATH
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "skills"
            archive = Path(temporary) / "bundle.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("sample-repo/skills/bundle-skill/SKILL.md", "---\nname: bundle-skill\ndescription: Bundle test.\n---\n# Bundle\n")
                handle.writestr("sample-repo/scripts/shared.py", "VALUE = 1\n")
            runtime_module.SKILLS_ROOT = root
            runtime_module.SKILL_ALIAS_PATH = Path(temporary) / "aliases.json"
            try:
                result = runtime_module.install_uploaded_skills([(archive.name, archive)], "zip")
                self.assertTrue(result["bundle"])
                self.assertTrue((root / "sample-repo" / "scripts" / "shared.py").is_file())
                marker = root / "sample-repo" / "keep.txt"
                marker.write_text("original", encoding="utf-8")
                with self.assertRaises(FileExistsError):
                    runtime_module.install_uploaded_skills([(archive.name, archive)], "zip")
                self.assertEqual(marker.read_text(encoding="utf-8"), "original")
            finally:
                runtime_module.SKILLS_ROOT = original_root
                runtime_module.SKILL_ALIAS_PATH = original_alias

    def test_model_display_optimization_uses_one_mocked_call_and_never_edits_skill(self):
        class FakeNamingAdapter:
            calls = 0

            def __init__(self, _config):
                self.last_usage = {"total_tokens": 33}

            def complete(self, _messages, _params):
                type(self).calls += 1
                return '{"names":{"gpt-image-2":"GPT Image 2图像助手"}}'

        original_adapter = chat_module.DapaoAPIChatAdapter
        original_alias = runtime_module.SKILL_ALIAS_PATH
        with tempfile.TemporaryDirectory() as temporary:
            runtime_module.SKILL_ALIAS_PATH = Path(temporary) / "aliases.json"
            chat_module.DapaoAPIChatAdapter = FakeNamingAdapter
            source = ROOT / "skills" / "gpt-image-2" / "SKILL.md"
            before = source.read_bytes()
            try:
                result = chat_module.optimize_skill_display_names({
                    "api_key": "mock-key", "model": "gemini-3.7-flash", "timeout": 30,
                }, scope="all")
                self.assertEqual(FakeNamingAdapter.calls, 1)
                self.assertEqual(result["updated"], 1)
                item = next(value for value in result["catalog"]["skills"] if value["id"] == "gpt-image-2")
                self.assertEqual(item["display_name"], "GPT Image 2图像助手")
                self.assertFalse(item["needs_optimization"])
                self.assertEqual(source.read_bytes(), before)
            finally:
                chat_module.DapaoAPIChatAdapter = original_adapter
                runtime_module.SKILL_ALIAS_PATH = original_alias

    def test_skill_name_json_parser_accepts_nested_fences_and_model_commentary(self):
        fenced = '```json\n{"names":{"img-gen-prompts":"图像提示词助手","img-gen-taste":"图像审美助手"}}\n```'
        self.assertEqual(
            chat_module._json_object_from_text(fenced)["names"]["img-gen-prompts"],
            "图像提示词助手",
        )
        commentary = '整理结果如下：\n{"names":{"gpt-image-2":"GPT Image 2图像助手"}}\n请查收。'
        self.assertEqual(
            chat_module._json_object_from_text(commentary)["names"]["gpt-image-2"],
            "GPT Image 2图像助手",
        )

    def test_skill_name_reply_parser_accepts_common_model_formats(self):
        ids = ["img-gen-prompts", "img-gen-taste"]
        variants = (
            '{"names":[{"id":"img-gen-prompts","name":"图像提示词助手"},{"id":"img-gen-taste","display_name":"图像审美助手"}]}',
            "img-gen-prompts\t图像提示词助手\nimg-gen-taste\t图像审美助手",
            "| img-gen-prompts | 图像提示词助手 |\n| img-gen-taste | 图像审美助手 |",
            "1. img-gen-prompts - 图像提示词助手\n2. img-gen-taste：图像审美助手",
            "1. 图像提示词助手\n2. 图像审美助手",
        )
        for reply in variants:
            with self.subTest(reply=reply):
                self.assertEqual(
                    chat_module._skill_names_from_reply(reply, ids),
                    {"img-gen-prompts": "图像提示词助手", "img-gen-taste": "图像审美助手"},
                )

    def test_current_skill_scope_sends_only_selected_skill_in_one_mocked_call(self):
        class SelectedAdapter:
            calls = 0
            prompt = ""

            def __init__(self, _config):
                self.last_usage = {"total_tokens": 12}

            def complete(self, messages, _params):
                type(self).calls += 1
                type(self).prompt = messages[-1]["content"]
                return "img-gen-prompts\t图像提示词生成助手"

        original_adapter = chat_module.DapaoAPIChatAdapter
        original_alias = runtime_module.SKILL_ALIAS_PATH
        with tempfile.TemporaryDirectory() as temporary:
            runtime_module.SKILL_ALIAS_PATH = Path(temporary) / "aliases.json"
            chat_module.DapaoAPIChatAdapter = SelectedAdapter
            try:
                result = chat_module.optimize_skill_display_names(
                    {"api_key": "mock-key", "model": "gemini-3.7-flash", "timeout": 30},
                    scope="selected",
                    skill_ids=["img-gen-prompts"],
                )
                self.assertEqual(SelectedAdapter.calls, 1)
                self.assertEqual(result["requested"], 1)
                self.assertEqual(result["updated"], 1)
                self.assertIn('"id":"img-gen-prompts"', SelectedAdapter.prompt)
                self.assertNotIn('"id":"img-gen-taste"', SelectedAdapter.prompt)
                self.assertIn("function_description", SelectedAdapter.prompt)
            finally:
                chat_module.DapaoAPIChatAdapter = original_adapter
                runtime_module.SKILL_ALIAS_PATH = original_alias

    def test_all_skill_scope_uses_descriptions_and_saves_every_mocked_name_in_one_call(self):
        class AllSkillsAdapter:
            calls = 0
            candidate_count = 0
            descriptions_ok = False

            def __init__(self, _config):
                self.last_usage = {"total_tokens": 88}

            def complete(self, messages, _params):
                type(self).calls += 1
                payload = json.loads(messages[-1]["content"].split("：\n", 1)[1])
                type(self).candidate_count = len(payload)
                type(self).descriptions_ok = all(bool(item.get("function_description")) for item in payload)
                return "\n".join(
                    f"{item['id']}\t功能命名{index + 1}号"
                    for index, item in enumerate(payload)
                )

        original_adapter = chat_module.DapaoAPIChatAdapter
        original_alias = runtime_module.SKILL_ALIAS_PATH
        with tempfile.TemporaryDirectory() as temporary:
            runtime_module.SKILL_ALIAS_PATH = Path(temporary) / "aliases.json"
            chat_module.DapaoAPIChatAdapter = AllSkillsAdapter
            try:
                result = chat_module.optimize_skill_display_names(
                    {"api_key": "mock-key", "model": "gemini-3.7-flash", "timeout": 30},
                    scope="all",
                )
                self.assertEqual(AllSkillsAdapter.calls, 1)
                self.assertGreater(AllSkillsAdapter.candidate_count, 1)
                self.assertTrue(AllSkillsAdapter.descriptions_ok)
                self.assertEqual(result["requested"], AllSkillsAdapter.candidate_count)
                self.assertEqual(result["updated"], result["requested"])
            finally:
                chat_module.DapaoAPIChatAdapter = original_adapter
                runtime_module.SKILL_ALIAS_PATH = original_alias

    def test_shared_lanczos_resize_contract_caps_long_edge_at_2k(self):
        class FakeImage:
            def __init__(self, width, height):
                self.width = width
                self.height = height
                self.size = (width, height)

            def copy(self):
                return FakeImage(self.width, self.height)

            def resize(self, size, resampling):
                self.assert_resampling = resampling
                return FakeImage(*size)

        old_numpy = sys.modules.get("numpy")
        old_pil = sys.modules.get("PIL")
        numpy_stub = types.ModuleType("numpy")
        pil_stub = types.ModuleType("PIL")
        pil_stub.Image = types.SimpleNamespace(
            Image=FakeImage,
            Resampling=types.SimpleNamespace(LANCZOS="LANCZOS"),
        )
        sys.modules["numpy"] = numpy_stub
        sys.modules["PIL"] = pil_stub
        try:
            spec = importlib.util.spec_from_file_location("dapao_image_utils_contract", ROOT / "image_input_utils.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            resized = module.resize_pil_for_input(FakeImage(4096, 1024))
        finally:
            if old_numpy is None:
                sys.modules.pop("numpy", None)
            else:
                sys.modules["numpy"] = old_numpy
            if old_pil is None:
                sys.modules.pop("PIL", None)
            else:
                sys.modules["PIL"] = old_pil
        self.assertEqual(resized.size, (2048, 512))

    def test_uploaded_image_is_reencoded_as_png_with_2k_limit(self):
        calls = {}

        class FakeImage:
            mode = "RGB"

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def convert(self, mode):
                calls["convert"] = mode
                return self

            def save(self, buffer, format, optimize):
                calls["save"] = (format, optimize)
                buffer.write(b"fake-png-content")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "large.jpg").touch()
            folder_paths = types.ModuleType("folder_paths")
            folder_paths.get_input_directory = lambda: str(root)
            old = sys.modules.get("folder_paths")
            old_image = runtime_module.Image
            old_resize = runtime_module.resize_pil_for_input
            sys.modules["folder_paths"] = folder_paths
            runtime_module.Image = types.SimpleNamespace(open=lambda path: FakeImage())
            runtime_module.resize_pil_for_input = lambda image, max_edge: calls.setdefault("max_edge", max_edge) and image
            try:
                uri = runtime_module.image_data_uri({"filename": "large.jpg", "subfolder": ""})
            finally:
                runtime_module.Image = old_image
                runtime_module.resize_pil_for_input = old_resize
                if old is None:
                    sys.modules.pop("folder_paths", None)
                else:
                    sys.modules["folder_paths"] = old
            self.assertTrue(uri.startswith("data:image/png;base64,"))
            self.assertEqual(base64.b64decode(uri.split(",", 1)[1]), b"fake-png-content")
            self.assertEqual(calls["max_edge"], 2048)
            self.assertEqual(calls["save"], ("PNG", True))


if __name__ == "__main__":
    unittest.main()
