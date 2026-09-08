"""No paid/network requests: stage contracts, document joins and list concurrency."""
import asyncio
import copy
import importlib
import inspect
import json
from pathlib import Path
import sys
import threading
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parent
pkg = types.ModuleType("drama_suite_test")
pkg.__path__ = [str(ROOT)]
sys.modules[pkg.__name__] = pkg
m = importlib.import_module(pkg.__name__ + ".short_drama_nodes")
s = importlib.import_module(pkg.__name__ + ".short_drama_suite")

SCRIPT = "# EP001 门口\n\n## EP001-SC001 内 · 走廊 · 夜\n江辰抬起右手。江辰：有人吗？"
ASSETS = "# 视觉设定\n\n## 人物 · 江辰\n- 识别锚点：旧西装，窄长眼。\n\n## 地点 · 走廊\n- 识别锚点：左侧木门。"
IMAGE = "# 图片提示词\n\n## IMG-JIANGCHEN · 江辰角色板\n- 用途：身份\n### 可复制提示词\n> 窄长眼男子，旧西装，正面身份参考板。\n>\n> 白色背景，均匀柔光，无水印。"
PLAN = "PLAN-START（顺序：1）· SHOT-EP001-001《本镜冻结关键帧》（用途：起始帧；控制：站位；不得控制：终态）"
BOARD = f"""# 分镜
## SHOT-EP001-001 · 门前抬手
- 来源：EP001-SC001
- 时长：4s
- 起点：右手垂在身侧
- 唯一动作：抬起右手
- 终点：右手悬在木门前
- 视觉依据：《视觉设定.md》·人物「江辰」（控制：身份）；地点「走廊」（控制：空间）
- 图片提示词项：无
- 输入参考图：{PLAN}
### 冻结关键帧提示词
> 窄长眼男子穿旧西装，右手垂在身侧，站在走廊木门前。
"""
VIDEO = f"""# 视频提示词
## MOTION-EP001-001 · 门前抬手
- 分镜：SHOT-EP001-001
- 时长：4s
- 输入参考图：{PLAN}
- 生成方式：图生视频
### 可复制提示词
> 人物右手从身侧抬至木门前，镜头固定。
>
> 他说：“有人吗？”随后回到环境声；全镜不生成非画内字幕。
"""
FIXTURES = {"novel": "# 原著分析\n当前范围的冲突与人物候选。", "develop": "# 系列开发\nEP001以门后身份为悬念。",
            "write": SCRIPT, "assets": ASSETS, "image": IMAGE, "storyboard": BOARD, "video": VIDEO,
            "review": "# 审查\n- 结论：APPROVE_WITH_NOTES\n- 复核方式：LLM文本审查，未核验媒体。"}


def response(text):
    return {"choices": [{"finish_reason": "stop", "message": {"content": text}}], "usage": {"total_tokens": 10}}


def fake_submit(**kw):
    system = kw["payload"]["messages"][0]["content"]
    stage = next(k for k, name in m.SKILLS.items() if f"当前唯一阶段：{name} →" in system)
    return response(FIXTURES[stage])


class DramaTests(unittest.TestCase):
    def setUp(self):
        self.network = patch.object(m, "submit_json_task", side_effect=fake_submit)
        self.submit = self.network.start()
        self.addCleanup(self.network.stop)
        # Any accidental requests bypassing the mocked submission fail immediately.
        guard = patch("requests.sessions.Session.request", side_effect=AssertionError("Network forbidden"))
        guard.start(); self.addCleanup(guard.stop)

    def run_stage(self, cls, bundle=None, **kwargs):
        return asyncio.run(cls().generate(**{"🔑 API密钥": "offline", "📦 上游资料": bundle, **kwargs}))

    def base(self):
        b = s.new_bundle()
        s.put_doc(b, "write", SCRIPT)
        s.put_doc(b, "assets", ASSETS, ["write"])
        return b

    def test_deepseek_document_requests_reserve_budget_for_content(self):
        for model in ('deepseek-v4-flash', 'deepseek-v4-pro'):
            self.run_stage(m.DapaoDramaImage, self.base(), **{'🤖 LLM模型': model})
            self.assertEqual(self.submit.call_args.kwargs['payload']['thinking'], {'type': 'disabled'})
        self.run_stage(m.DapaoDramaImage, self.base())
        self.assertNotIn('thinking', self.submit.call_args.kwargs['payload'])

    def test_next_episode_inherits_baseline_without_mutating_previous(self):
        first = self.base()
        s.put_doc(first, 'image', IMAGE, ['assets'])
        first['timing_plan'] = [4]
        original = copy.deepcopy(first)
        def sequel_submit(**kw):
            context = json.loads(kw['payload']['messages'][1]['content'])
            episode = context['项目设置']['episode']
            return response(SCRIPT.replace('EP001', episode) + '\n\n## 集间交接\n门外等待，包裹仍在手中，门内身份未解。')
        self.submit.side_effect = sequel_submit
        second = self.compact(m.DapaoDramaPrepare, first, **{'🎛️ 准备任务':'续写下一集（继承前集）', '📄 剧本或故事内容':'追问门内声音', '🎞️ 当前集号':1})['result'][0]
        self.assertEqual(first, original)
        self.assertEqual(second['config']['episode'], 'EP002')
        self.assertEqual(second['config']['episodes'], 2)
        self.assertEqual(second['series_baseline']['assets'], ASSETS)
        self.assertNotIn('timing_plan', second)
        self.assertNotIn('image', second['docs'])
        self.assertNotIn('assets', second['docs'])
        context = json.loads(self.submit.call_args.kwargs['payload']['messages'][1]['content'])
        self.assertEqual(context['跨集连续性']['前集文档']['剧本.md'], SCRIPT)
        s.put_doc(second, 'assets', ASSETS, ['write'])
        third = self.compact(m.DapaoDramaPrepare, second, **{'🎛️ 准备任务':'续写下一集（继承前集）'})
        self.assertEqual(third['result'][0]['config']['episode'], 'EP003')
        self.assertEqual(len(third['result'][0]['episode_history']), 2)
        self.assertEqual(json.loads(third['ui']['drama_bundle'][0]), third['result'][0])
        restored = self.compact(m.DapaoDramaPrepare, None, **{'🎛️ 准备任务':'续写下一集（继承前集）', '📂 导入文档类型':'完整资料包JSON', '📄 导入文档':json.dumps(second)})
        self.assertEqual(restored['result'][0]['config']['episode'], 'EP003')

    def test_sequel_requires_valid_previous_and_filters_reused_assets(self):
        with self.assertRaisesRegex(RuntimeError, '前集'):
            self.compact(m.DapaoDramaPrepare, None, **{'🎛️ 准备任务':'续写下一集（继承前集）'})
        first = self.base(); s.put_doc(first, 'image', IMAGE, ['assets'])
        second = s.next_episode_bundle(first, '继续', 60)
        s.put_doc(second, 'write', SCRIPT.replace('EP001','EP002'))
        s.put_doc(second, 'assets', ASSETS, ['write'])
        result = self.compact(m.DapaoDramaVisual, second, **{'🎨 处理内容':'仅资产图片提示词（复用已有设定）','♻️ 跨集资产输出':'仅新增或变化资产'})
        self.assertEqual(result['result'][3], [])
        self.assertIn('IMG-JIANGCHEN', result['result'][0]['docs']['image']['text'])

    def test_all_eleven_nodes_and_shared_catalogue(self):
        self.assertEqual(len(m.NODE_CLASS_MAPPINGS), 14)
        for cls in m.NODE_CLASS_MAPPINGS.values():
            self.assertTrue(cls.CATEGORY.startswith(s.CATEGORY))
            if issubclass(cls, m.DramaStage):
                self.assertTrue(inspect.iscoroutinefunction(cls.generate))
                self.assertEqual(cls.INPUT_TYPES()["required"]["🤖 LLM模型"][0], list(m.LLM_MODEL_OPTIONS))
                self.assertFalse(getattr(cls, "INPUT_IS_LIST", False))
                self.assertTrue(s.skill_context(cls.STAGE))

    def test_full_workflow_branch_join_and_delivery(self):
        b, _ = m.DapaoDramaProject().build(**{"📝 创作简报": "门后是谁"})
        b = self.run_stage(m.DapaoDramaDevelop, b)[0]
        b = self.run_stage(m.DapaoDramaWrite, b)[0]
        b = self.run_stage(m.DapaoDramaAssets, b)[0]
        original = copy.deepcopy(b)
        image = self.run_stage(m.DapaoDramaImage, b)
        board = self.run_stage(m.DapaoDramaStoryboard, b)
        self.assertEqual(b, original, "Sibling branches must not mutate upstream")
        joined = m.DapaoDramaMerge().merge(**{"📦 支线A": image[0], "📦 支线B": board[0]})[0]
        video = self.run_stage(m.DapaoDramaVideo, joined)
        reviewed = self.run_stage(m.DapaoDramaReview, video[0])
        delivery = m.DapaoDramaDeliver().collect(**{"📦 上游资料": reviewed[0]})
        self.assertIn("drama_preview", delivery["ui"])
        output = delivery["result"]
        self.assertEqual([len(x) for x in output[:3]], [1, 1, 1])
        self.assertIn("白色背景", output[0][0])
        self.assertIn("随后回到环境声", output[2][0])
        self.assertEqual(json.loads(output[3])[2]["references"], PLAN)
        self.assertNotIn("原著分析", output[4])
        self.assertIn("APPROVE_WITH_NOTES", output[5])
        self.assertEqual(self.submit.call_count, 7)
        for call in self.submit.call_args_list:
            self.assertEqual(call.kwargs["endpoint"], "/v1/chat/completions")
            self.assertTrue(call.kwargs["reuse_succeeded"])

    def compact(self, cls, bundle=None, **kw):
        return asyncio.run(cls().generate(**{"🔑 API密钥": "offline", "📦 上游资料": bundle, **kw}))

    def test_three_node_existing_script_pipeline(self):
        classes = [m.DapaoDramaPrepare, m.DapaoDramaVisual, m.DapaoDramaFinish]
        self.assertEqual([cls for cls in m.NODE_CLASS_MAPPINGS.values() if cls.CATEGORY == s.CATEGORY], classes)
        for cls in classes:
            self.assertTrue(inspect.iscoroutinefunction(cls.generate))
            self.assertTrue(cls.OUTPUT_NODE)
            self.assertEqual(cls.INPUT_TYPES()["required"]["🤖 LLM模型"][0], list(m.LLM_MODEL_OPTIONS))
            self.assertFalse(getattr(cls, "INPUT_IS_LIST", False))
        prepared = self.compact(classes[0], **{"📄 剧本或故事内容": SCRIPT})
        self.assertIn(SCRIPT, prepared["ui"]["drama_preview"][0])
        request = json.loads(self.submit.call_args.kwargs["payload"]["messages"][1]["content"])
        self.assertEqual(request["原文或现有稿"], SCRIPT)
        self.assertIn("保留原剧情", request["本阶段要求"])
        visual = self.compact(classes[1], prepared["result"][0])
        finish = self.compact(classes[2], visual["result"][0])
        for cls, output in zip(classes, (prepared, visual, finish)):
            self.assertEqual(len(output["result"]), len(cls.RETURN_TYPES))
            self.assertEqual(len(cls.OUTPUT_IS_LIST), len(cls.RETURN_TYPES))
            self.assertEqual(cls.RETURN_TYPES[-1], "STRING")
            self.assertFalse(cls.OUTPUT_IS_LIST[-1])
            self.assertEqual(json.loads(output["result"][-1]), output["result"][0])
            self.assertEqual(output["result"][-1], output["ui"]["drama_bundle"][0])
        self.assertEqual(self.submit.call_count, 5)
        self.assertEqual([len(x) for x in finish["result"][1:4]], [1, 1, 1])
        self.assertEqual(len(finish["result"]), len(classes[2].RETURN_TYPES))
        self.assertNotIn("offline", json.dumps(finish, ensure_ascii=False))
        self.assertIn("drama_manifest", finish["ui"])

    def test_compact_static_review_and_free_collect(self):
        prepared = self.compact(m.DapaoDramaPrepare, **{"📥 内容来源": "原创想法", "📄 剧本或故事内容": "门口悬疑", "🎨 制作形态": "静态漫剧"})
        visual = self.compact(m.DapaoDramaVisual, prepared["result"][0])
        finished = self.compact(m.DapaoDramaFinish, visual["result"][0], **{"🔍 文本审查": "开启（增加一次LLM调用）"})
        self.assertEqual(finished["result"][3], [])
        self.assertIn("APPROVE_WITH_NOTES", finished["result"][6])
        count = self.submit.call_count
        with patch.dict("os.environ", {}, clear=True):
            collected = self.compact(m.DapaoDramaFinish, finished["result"][0], **{"🔑 API密钥": "", "🎬 交付模式": "仅整理已有提示词（不调用LLM）", "🔍 文本审查": "开启（增加一次LLM调用）"})
        self.assertEqual(self.submit.call_count, count)
        self.assertEqual(collected["result"][1:6], finished["result"][1:6])

    def test_compact_novel_keeps_source_out_of_downstream_config(self):
        raw = "这是原著独有的正文" * 300
        prepared = self.compact(m.DapaoDramaPrepare, **{"📥 内容来源": "小说改编", "📄 剧本或故事内容": raw})
        self.assertEqual(self.submit.call_count, 4)  # extract, summarize, develop, write
        self.assertNotIn(raw, json.dumps(prepared["result"][0]["config"], ensure_ascii=False))
        self.assertNotIn(raw, self.submit.call_args.kwargs["payload"]["messages"][1]["content"])
        self.submit.reset_mock()
        with self.assertRaisesRegex(RuntimeError, "超过设定"):
            self.compact(m.DapaoDramaPrepare, **{"📥 内容来源": "小说改编", "📄 剧本或故事内容": "原文" * 13000, "🧮 最大分析段数": 1})
        self.submit.assert_not_called()

    def test_compact_bad_draft_stops_before_next_paid_stage(self):
        self.submit.side_effect = lambda **kw: response("格式错误的草稿")
        visual = self.compact(m.DapaoDramaVisual, self.base())
        self.assertEqual(self.submit.call_count, 1)
        self.assertIn("格式错误的草稿", visual["ui"]["drama_preview"][0])
        self.assertIn("已停止", visual["result"][2])
        with self.assertRaisesRegex(RuntimeError, "结构检查未通过"):
            self.compact(m.DapaoDramaFinish, visual["result"][0])
        self.assertEqual(self.submit.call_count, 1)
        failed = self.compact(m.DapaoDramaFinish, self.base())
        self.assertEqual(failed["result"][1:4], ([], [], []))
        self.assertEqual(failed["ui"]["drama_manifest"], ["[]"])
        self.assertEqual(self.submit.call_count, 2)

    def test_compact_list_overlap_and_error_redaction(self):
        barrier = threading.Barrier(2, timeout=5)
        def submit(**kw):
            barrier.wait()
            return response(SCRIPT)
        self.submit.side_effect = submit
        async def run():
            node = m.DapaoDramaPrepare()
            return await asyncio.gather(*(node.generate(**{"🔑 API密钥": "offline", "📄 剧本或故事内容": f"剧本{i}"}) for i in range(2)))
        results = asyncio.run(run())
        self.assertTrue(all(len(r["result"]) == 4 for r in results))
        self.submit.reset_mock()
        self.submit.side_effect = RuntimeError("Bearer secret-for-test")
        with self.assertRaises(RuntimeError) as caught:
            self.compact(m.DapaoDramaPrepare, **{"🔑 API密钥": "secret-for-test", "📄 剧本或故事内容": SCRIPT})
        self.assertNotIn("secret-for-test", str(caught.exception))
        self.assertEqual(self.submit.call_count, 1)

    def test_direct_entry_and_missing_sources_are_local_errors(self):
        self.run_stage(m.DapaoDramaImage, **{"📄 视觉设定.md": ASSETS})
        self.assertEqual(self.submit.call_count, 1)
        with self.assertRaisesRegex(RuntimeError, "缺少剧本"):
            self.run_stage(m.DapaoDramaAssets)
        self.assertEqual(self.submit.call_count, 1)

    def test_merge_conflicts_and_stale_descendants(self):
        b = self.base()
        a = self.run_stage(m.DapaoDramaImage, b)[0]
        changed = copy.deepcopy(b)
        s.put_doc(changed, "write", SCRIPT + "\n结尾改变。")
        with self.assertRaisesRegex(ValueError, "不同版本"):
            s.merge_bundles(a, changed)
        s.put_doc(a, "write", SCRIPT + "\n结尾改变。")
        self.assertIn("image", s.stale_docs(a))
        with self.assertRaises(ValueError):
            m.DapaoDramaDeliver().collect(**{"📦 上游资料": a})

    def test_malformed_paid_response_is_preserved_and_not_retried(self):
        self.submit.return_value = response("# 只有标题")
        self.submit.side_effect = None
        result = self.run_stage(m.DapaoDramaStoryboard, self.base())
        self.assertEqual(result[1], "# 只有标题")
        self.assertIn("需要修订", result[3])
        with self.assertRaises(RuntimeError):
            self.run_stage(m.DapaoDramaVideo, result[0])
        self.assertEqual(self.submit.call_count, 1)

    def test_scene_reference_duration_plan_and_locks(self):
        b = self.base()
        self.assertEqual(s.check_document("storyboard", BOARD, b), [])
        self.assertTrue(s.check_document("storyboard", BOARD.replace("EP001-SC001", "EP001-SC099"), b))
        b["config"]["shot_max"] = 3
        self.assertTrue(s.check_document("storyboard", BOARD, b))
        b["config"]["shot_max"] = 0
        s.put_doc(b, "storyboard", BOARD, ["write", "assets"])
        self.assertTrue(s.check_document("video", VIDEO.replace("4s", "5s"), b))
        self.assertTrue(s.check_document("video", VIDEO.replace("PLAN-START", "REF-START"), b))
        b["docs"]["assets"]["text"] += "\n- 连续性锁：LOCK-SUIT《西装》（镜头：全集）· 锁面：深灰羊毛西装"
        self.assertFalse(any("连续性锁" in x for x in s.check_document("storyboard", BOARD, b)))
        self.assertTrue(s.document_advisories("storyboard", BOARD, b))
        b["docs"]["assets"]["text"] = b["docs"]["assets"]["text"].replace("镜头：全集", "镜头：SHOT-EP001-001")
        self.assertTrue(any("连续性锁" in x for x in s.check_document("storyboard", BOARD, b)))

    def test_failed_board_preserves_valid_asset_prompt_outputs(self):
        bundle = self.run_stage(m.DapaoDramaImage, self.base())[0]
        self.submit.side_effect = lambda **kw: response("格式错误的草稿")
        output = self.compact(m.DapaoDramaFinish, bundle)
        self.assertEqual(len(output["result"][1]), 1)
        self.assertEqual(output["result"][2:4], ([], []))
        self.assertEqual(len(json.loads(output["result"][4])), 1)
        self.assertIn("部分交付", output["result"][6])

    def test_asset_strategy_and_duplicate_detection(self):
        self.compact(m.DapaoDramaVisual, self.base(), **{"👤 资产规划": "仅人物设定"})
        request = json.loads(self.submit.call_args.kwargs["payload"]["messages"][1]["content"])
        self.assertIn("不生成场景、建筑、门、道具", request["本阶段要求"])
        duplicate = IMAGE + "\n\n" + IMAGE.replace("IMG-JIANGCHEN", "IMG-DUPLICATE")
        self.assertTrue(any("资产提示词重复" in issue for issue in s.check_document("image", duplicate, self.base())))

    def test_reference_sentence_punctuation_is_not_binding_change(self):
        bundle = self.base()
        s.put_doc(bundle, 'storyboard', BOARD.replace(PLAN, PLAN + '。'), ['write', 'assets'])
        self.assertEqual(s.check_document('video', VIDEO, bundle), [])
        for changed in (VIDEO.replace('顺序：1', '顺序：2'), VIDEO.replace('控制：站位', '控制：服装'), VIDEO.replace('PLAN-START', 'PLAN-OTHER')):
            self.assertTrue(any('输入参考图与分镜不一致' in x for x in s.check_document('video', changed, bundle)))

    def test_manual_duration_plan_and_aligned_outputs(self):
        output = self.compact(m.DapaoDramaFinish, self.base(), **{'⏱️ 时长规划': '手动逐段时长', '📝 逐段时长（秒）': '4', '🧩 批量输出内容': '视频提示词'})['result']
        self.assertEqual(output[8], [4.0])
        self.assertEqual(output[9], [4.0])
        self.assertEqual(len(output[7]), len(output[9]))
        self.assertIn('总计4秒', output[6])
        context = json.loads(self.submit.call_args.kwargs['payload']['messages'][1]['content'])
        self.assertEqual(context['本轮总时长（秒）'], 4)
        self.submit.reset_mock()
        failed = self.compact(m.DapaoDramaFinish, self.base(), **{'⏱️ 时长规划': '手动逐段时长', '📝 逐段时长（秒）': '6,6,8,10'})['result']
        self.assertEqual(failed[3], [])
        self.assertIn('逐段时长未符合', failed[6])
        self.assertEqual(self.submit.call_count, 1)  # board mismatch, no video or retry
        for raw in ('', '0,5', '6,no', '121'):
            with self.assertRaisesRegex(RuntimeError, '尚未调用LLM'):
                self.compact(m.DapaoDramaFinish, self.base(), **{'⏱️ 时长规划': '手动逐段时长', '📝 逐段时长（秒）': raw})
        self.assertEqual(self.submit.call_count, 1)

    def test_segment_controls_reject_conflict_before_request(self):
        options = {'⏱️ 时长规划': '按段数逐段设置', '🔢 分段数量': 1, '⏱️ 第01段（秒）': 4}
        with self.assertRaisesRegex(RuntimeError, '01目标.*尚未调用LLM'):
            self.compact(m.DapaoDramaFinish, self.base(), **options)
        self.assertEqual(self.submit.call_count, 0)
        output = self.compact(m.DapaoDramaFinish, self.base(), **options, **{'⏳ 总时长规则': '以本节点分段合计为准'})['result']
        self.assertEqual(output[8], [4.0])

    def test_selected_duration_subset_keeps_prompt_order(self):
        bundle = self.base()
        board = BOARD + '\n' + BOARD.replace('SHOT-EP001-001', 'SHOT-EP001-002').replace('4s', '7s')
        video = VIDEO + '\n' + VIDEO.replace('MOTION-EP001-001', 'MOTION-EP001-002').replace('SHOT-EP001-001', 'SHOT-EP001-002').replace('4s', '7s')
        s.put_doc(bundle, 'storyboard', board, ['write', 'assets'])
        s.put_doc(bundle, 'video', video, ['storyboard'])
        output = self.compact(m.DapaoDramaFinish, bundle, **{'🎬 交付模式':'仅整理已有提示词（不调用LLM）', '🧩 批量输出内容':'视频提示词', '🔢 提示词选择':'2'})['result']
        self.assertEqual(output[8], [4,7])
        self.assertEqual(output[9], [7])
        self.assertEqual(output[7], [output[3][1]])
        self.submit.assert_not_called()

    def test_unused_extra_reference_repair_and_both_video_outputs(self):
        bundle = self.base()
        s.put_doc(bundle, 'storyboard', BOARD, ['write', 'assets'])
        extra = '；PLAN-EXTRA（顺序：2）· IMG-PROP《道具》（用途：尺度；控制：尺寸；不得控制：姿态）'
        draft = VIDEO.replace(PLAN, PLAN + extra)
        s.put_doc(bundle, 'video', draft, ['storyboard', 'assets', 'write'])
        output = self.compact(m.DapaoDramaFinish, bundle, **{'🎬 交付模式': '仅整理已有提示词（不调用LLM）', '🧩 批量输出内容': '视频提示词'})['result']
        self.assertEqual(output[3], output[7])
        self.assertEqual(len(output[3]), 1)
        self.assertEqual(output[3][0], s.extract_prompts('video', draft)[0]['prompt'])
        self.assertNotIn('PLAN-EXTRA', output[0]['docs']['video']['text'])
        self.assertIn('本地参考图配置校正', output[6])
        for unsafe in (draft.replace('人物右手', '参考图2的人物右手'), VIDEO.replace('控制：站位', '控制：服装')):
            repaired, changes = s.repair_video_reference_bindings(unsafe, bundle)
            self.assertEqual(repaired, unsafe)
            self.assertEqual(changes, [])
        imported = self.compact(m.DapaoDramaPrepare, **{'🎛️ 准备任务': '仅导入已有文档（不调用LLM）', '📂 导入文档类型': '完整资料包JSON', '📄 导入文档': json.dumps(output[0])})
        self.assertEqual(imported['result'][0], output[0])
        self.submit.assert_not_called()

    def test_compact_independent_tasks_and_references(self):
        reviewed = self.compact(m.DapaoDramaFinish, self.base(), **{"🎬 交付模式": "仅文本审查"})
        self.assertEqual(self.submit.call_count, 1)
        self.assertIn("APPROVE_WITH_NOTES", reviewed['result'][6])
        prepared = self.compact(m.DapaoDramaPrepare, **{"🎛️ 准备任务": "仅原著分析", "📄 剧本或故事内容": "片段原文", "🔍 分析方式": "当前材料分析"})
        self.assertEqual(set(prepared['result'][0]['docs']), {'novel'})
        image = self.compact(m.DapaoDramaVisual, self.base(), **{"🎨 处理内容": "仅资产图片提示词（复用已有设定）", "🖌️ 图片用途": "Lookdev风格比较"})
        self.assertEqual(self.submit.call_count, 3)
        self.assertIn("lookdev-frame.md", self.submit.call_args.kwargs['payload']['messages'][0]['content'])
        self.assertEqual(len(image['result'][3]), 1)
        before = self.submit.call_count
        imported = self.compact(m.DapaoDramaPrepare, **{"🎛️ 准备任务": "仅导入已有文档（不调用LLM）", "📂 导入文档类型": "剧本.md", "📄 导入文档": SCRIPT})
        self.assertEqual(imported['result'][0]['docs']['write']['text'], SCRIPT)
        self.assertEqual(before, self.submit.call_count)

    def test_batch_output_maps_to_independent_comfy_image_tasks(self):
        import ast
        import contextlib
        # Execute the installed ComfyUI mapper itself; no copied mapping algorithm.
        path = ROOT.parent.parent / 'execution.py'
        tree = ast.parse(path.read_text(encoding='utf-8'))
        names = {'_async_map_node_over_list', 'merge_result_data'}
        selected = ast.Module(body=[n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names], type_ignores=[])
        env = {'asyncio': asyncio, 'inspect': inspect, 'is_class': inspect.isclass,
               'ExecutionBlocker': type('ExecutionBlocker', (), {}), '_ComfyNodeInternal': type('V3', (), {}),
               'CurrentNodeContext': lambda *a: contextlib.nullcontext()}
        exec(compile(selected, str(path), 'exec'), env)
        bundle = self.base()
        text = IMAGE + '\n' + IMAGE.replace('IMG-JIANGCHEN', 'IMG-SCENE').replace('窄长眼男子', '木门走廊') + '\n' + IMAGE.replace('IMG-JIANGCHEN', 'IMG-PROP').replace('窄长眼男子', '旧包裹')
        s.put_doc(bundle, 'image', text, ['assets'])
        output = self.compact(m.DapaoDramaFinish, bundle, **{'🎬 交付模式': '仅整理已有提示词（不调用LLM）'})
        mapped = env['merge_result_data']([output['result']], m.DapaoDramaFinish())
        prompts = mapped[7]
        self.assertEqual(prompts, mapped[1])
        self.assertEqual(len(set(prompts)), 3)
        self.assertTrue(all(isinstance(p,str) and '共 3 条' not in p for p in prompts))
        class MockImage:
            def __init__(self): self.seen = []; self.ready = asyncio.Event()
            async def generate(self, prompt):
                self.seen.append(prompt)
                if len(self.seen) == 3: self.ready.set()
                await asyncio.wait_for(self.ready.wait(), 2)
                return (prompt,)
        async def run():
            node = MockImage()
            tasks = await env['_async_map_node_over_list']('offline', 'image', node, {'prompt': prompts}, 'generate')
            results = [await task if inspect.isawaitable(task) else task for task in tasks]
            return node.seen, results
        seen, results = asyncio.run(run())
        self.assertEqual(seen, prompts)
        self.assertEqual([r[0] for r in results], prompts)
        self.submit.assert_not_called()
        entries = s.extract_prompts('image', text)
        self.assertEqual(m.select_prompt_entries(entries, '1,3'), [prompts[0], prompts[2]])
        self.assertEqual(m.select_prompt_entries(entries, 'IMG-SCENE'), [prompts[1]])

    def test_global_lock_advisory_revalidates_cached_draft(self):
        bundle = self.base()
        bundle["docs"]["assets"]["text"] += "\n- 连续性锁：LOCK-SUIT《西装》（镜头：全集）· 锁面：深灰羊毛西装"
        s.put_doc(bundle, "storyboard", BOARD, ["write", "assets"], ["旧版检查：没有原样保留连续性锁"])
        result = m.DapaoDramaDeliver().collect(**{"📦 上游资料": bundle})["result"]
        self.assertEqual(len(result[1]), 1)
        self.assertIn("人工复核", result[-1])
        video = self.run_stage(m.DapaoDramaVideo, bundle)
        self.assertEqual(len(video[2]), 1)

    def test_list_mapping_overlaps(self):
        barrier = threading.Barrier(3, timeout=5)
        def submit(**kw):
            barrier.wait()
            return response(SCRIPT)
        self.submit.side_effect = submit
        async def run():
            return await asyncio.gather(*(m.DapaoDramaWrite().generate(**{"🔑 API密钥": "offline", "📝 本阶段要求": str(i)}) for i in range(3)))
        results = asyncio.run(run())
        self.assertEqual(len(results), 3)
        self.assertTrue(all(len(r) == 4 for r in results))

    def test_errors_are_redacted_and_not_retried(self):
        self.submit.side_effect = RuntimeError("Authorization Bearer local-secret-123")
        with self.assertRaises(RuntimeError) as caught:
            self.run_stage(m.DapaoDramaWrite, **{"🔑 API密钥": "local-secret-123", "📝 本阶段要求": "写剧本"})
        self.assertNotIn("local-secret-123", str(caught.exception))
        self.assertEqual(self.submit.call_count, 1)

    def test_novel_coverage_and_preflight_limits(self):
        raw = "原著正文" * 1100
        with self.assertRaisesRegex(RuntimeError, "超过设定"):
            self.run_stage(m.DapaoDramaNovel, **{"📄 原文或现有稿": raw, "🔍 分析方式": "全文分段分析", "📏 每段字符数": 2000, "🧮 最大分析段数": 1})
        self.assertEqual(self.submit.call_count, 0)
        result = self.run_stage(m.DapaoDramaNovel, **{"📄 原文或现有稿": raw, "🔍 分析方式": "抽样快评", "📏 每段字符数": 2000, "🧮 最大分析段数": 2})
        self.assertIn("2/3段", result[1])
        self.assertIn("字符1–2000", result[1])
        self.assertIn("字符4001–4400", result[1])
        self.assertEqual(self.submit.call_count, 3)

    def test_truncation_and_oversize_rejected(self):
        self.submit.side_effect = lambda **kw: {"choices": [{"finish_reason": "length", "message": {"content": "partial"}}]}
        with self.assertRaisesRegex(RuntimeError, "截断"):
            self.run_stage(m.DapaoDramaWrite, **{"📝 本阶段要求": "写剧本"})
        with self.assertRaisesRegex(RuntimeError, "上下文"):
            self.run_stage(m.DapaoDramaWrite, **{"🤖 LLM模型": "gpt-5.5", "📄 原文或现有稿": "长文本" * 100000})
        self.assertEqual(self.submit.call_count, 1)

    def test_static_delivery_does_not_require_video(self):
        b = self.run_stage(m.DapaoDramaStoryboard, self.base())[0]
        result = m.DapaoDramaDeliver().collect(**{"📦 上游资料": b, "📦 交付范围": "分镜关键帧"})["result"]
        self.assertEqual(result[2], [])
        self.assertEqual(len(result[1]), 1)

    def test_original_chapter_index_and_example_wiring(self):
        text = "第一章 门口\n" + "老人站在门口。" * 20 + "\n第二章 灯光\n" + "门内灯光亮起。" * 20
        pieces = s.source_pieces(text, 2000)
        self.assertEqual(len(pieces), 2)
        self.assertEqual("".join(p[1] for p in pieces), text)
        with self.assertRaisesRegex(ValueError, "章节索引"):
            s.source_pieces(text.replace("第二章", "第四章"), 2000)
        for file in (ROOT / "example_workflows").glob("漫剧_*.json"):
            workflow = json.loads(file.read_text(encoding="utf-8"))
            nodes = {n["id"]: n for n in workflow["nodes"]}
            for node in nodes.values():
                self.assertIn(node["type"], m.NODE_CLASS_MAPPINGS)
                self.assertNotIn("sk-", json.dumps(node["widgets_values"]))
            for link_id, src, output, dest, input_slot, typ in workflow["links"]:
                self.assertIn(link_id, nodes[src]["outputs"][output]["links"])
                self.assertEqual(nodes[dest]["inputs"][input_slot]["link"], link_id)
                self.assertEqual(typ, m.BUNDLE_TYPE)


if __name__ == "__main__":
    unittest.main()
