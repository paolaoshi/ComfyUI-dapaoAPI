"""Offline contract checks: no real API calls or credentials."""
import asyncio
import base64
import importlib
import inspect
import io
import sys
import threading
import time
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from PIL import Image

ROOT = Path(__file__).parent
package = types.ModuleType("banana_contract")
package.__path__ = [str(ROOT)]
sys.modules[package.__name__] = package
banana = importlib.import_module("banana_contract.banana_allround_node")
Node = banana.DapaoBananaAllroundNode


def response():
    buffer = io.BytesIO()
    Image.new("RGB", (16, 12), "yellow").save(buffer, format="PNG")
    return {"candidates": [{"content": {"parts": [{"inlineData": {
        "mimeType": "image/png", "data": base64.b64encode(buffer.getvalue()).decode(),
    }}]}}]}


def inputs(**overrides):
    result = {"🔑 API密钥": "offline-test", "🤖 模型": banana.BANANA_21_LABEL,
              "📝 提示词": "teapot", "📐 图片尺寸/比例": "16:9", "🧩 清晰度": "2K"}
    result.update(overrides)
    return result


class BananaContracts(unittest.TestCase):
    def setUp(self):
        self.no_network = patch.object(banana.requests, "get", side_effect=AssertionError("offline test attempted GET"))
        self.no_network.start()
        self.no_submit = patch.object(banana, "submit_json_task", side_effect=AssertionError("offline test attempted submit"))
        self.no_submit.start()

    def tearDown(self):
        self.no_submit.stop()
        self.no_network.stop()

    def test_schema_and_optional_widget_order(self):
        schema = Node.INPUT_TYPES()
        self.assertTrue(inspect.iscoroutinefunction(Node.generate))
        self.assertFalse(getattr(Node, "INPUT_IS_LIST", False))
        self.assertEqual(len([n for n in schema['optional'] if n.startswith('🖼️ 图像')]), 14)
        self.assertEqual(list(schema['optional'])[0], '⌛ 请求超时')
        self.assertEqual(list(schema['optional'])[15:17], ['🧠 思考等级', '🔎 联网搜索'])

    def test_advanced_payload_validation_and_old_model_isolation(self):
        args = dict(search=True, search_scope='仅图片', output_mode='仅图片',
                    include_thoughts=True, max_tokens=32768, system_instruction=' 中文 ')
        p = Node._make_payload('p', [], '1:1', '1K', model_label=banana.BANANA_21_LABEL, **args)
        self.assertEqual(p['tools'], [{'googleSearch': {'searchTypes': {'imageSearch': {}}}}])
        self.assertEqual(p['generationConfig']['responseModalities'], ['IMAGE'])
        self.assertTrue(p['generationConfig']['thinkingConfig']['includeThoughts'])
        self.assertEqual(p['generationConfig']['maxOutputTokens'], 32768)
        self.assertEqual(p['systemInstruction'], {'parts': [{'text': '中文'}]})
        old = Node._make_payload('p', [], '1:1', '1K', model_label='bananaPRO', **args)
        self.assertNotIn('tools', old)
        self.assertNotIn('systemInstruction', old)
        self.assertNotIn('maxOutputTokens', old['generationConfig'])
        for bad in [-1, 32769, 1.5, True]:
            with self.assertRaises(ValueError):
                Node._make_payload('p', [], '1:1', '1K', model_label=banana.BANANA_21_LABEL, max_tokens=bad)
        with patch.object(banana, 'submit_json_task') as submit:
            for values in [{'📐 图片尺寸/比例': '9:21'}, {'📏 输出Token上限': -1},
                           {'🔎 联网搜索': True, '🧭 搜索范围': 'invalid'}]:
                with self.assertRaises(RuntimeError):
                    asyncio.run(Node().generate(**inputs(**values)))
            submit.assert_not_called()

    def test_response_text_sources_and_thought_images(self):
        r = response()
        parts = r['candidates'][0]['content']['parts']
        parts.insert(0, dict(parts[0], thought=True))
        parts.extend([{'text': '模型说明'}, {'text': '可用摘要', 'thought': True}])
        r['candidates'][0]['groundingMetadata'] = {'webSearchQueries': ['tower'],
            'groundingChunks': [{'web': {'title': '来源', 'uri': 'https://example.com'}}, {}]}
        self.assertEqual(len(banana._extract_image_items(r)), 1)
        text = banana._readable_response_details([r])
        self.assertIn('模型文字', text)
        self.assertIn('模型返回的思考摘要', text)
        self.assertIn('https://example.com', text)

    def test_old_models_keep_exact_payload_and_routes(self):
        expected = {'contents': [{'role': 'user', 'parts': [{'text': 'teapot'}]}],
                    'generationConfig': {'responseModalities': ['TEXT', 'IMAGE'],
                                         'imageConfig': {'imageSize': '2K', 'aspectRatio': '16:9'}}}
        for label, route in [('bananaPRO', 'bananaPRO'), ('bannana-2', 'bannana-2'),
                             ('香蕉pro官方稳定版', 'bananaPRO-official-2k'),
                             ('香蕉2官方稳定版', 'banana2-official-2k')]:
            with self.subTest(label=label), patch.object(banana, 'submit_json_task', return_value=response()) as submit:
                result = asyncio.run(Node().generate(**inputs(**{'🤖 模型': label, '🧠 思考等级': 'ignored', '🔎 联网搜索': True})))
                request = submit.call_args.kwargs
                self.assertEqual(request['payload'], expected)
                self.assertEqual(request['endpoint'], f'/v1beta/models/{route}:generateContent')
                self.assertEqual(len(result), 3)
                self.assertEqual(tuple(result[0].shape), (1, 12, 16, 3))

    def test_new_model_sizes_thinking_search_seed_and_price(self):
        for size in ['1K', '2K', '4K']:
            for thinking, level in banana.THINKING_LEVELS.items():
                with self.subTest(size=size, level=level), patch.object(banana, 'submit_json_task', return_value=response()) as submit:
                    result = asyncio.run(Node().generate(**inputs(**{
                        '🧩 清晰度': size, '🧠 思考等级': thinking, '🔎 联网搜索': True, '🎲 随机种': 333})))
                    request = submit.call_args.kwargs
                    self.assertEqual(request['endpoint'], '/v1beta/models/gemini-nano-banana-2.1:generateContent')
                    config = request['payload']['generationConfig']
                    self.assertEqual(config['imageConfig']['imageSize'], size)
                    self.assertEqual(config['thinkingConfig'], {'thinkingLevel': level})
                    self.assertEqual(request['payload']['tools'], [{'googleSearch': {'searchTypes': {'webSearch': {}, 'imageSearch': {}}}}])
                    self.assertFalse(set(config) & {'seed', 'temperature', 'topP', 'topK', 'candidateCount'})
                    self.assertIn('¥0.18/次', result[2])

    def test_default_thinking_and_search_disabled(self):
        p = Node._make_payload('p', [], '模型默认', '1K', model_label=banana.BANANA_21_LABEL)
        self.assertEqual(p['generationConfig']['thinkingConfig']['thinkingLevel'], 'medium')
        self.assertNotIn('tools', p)
        self.assertNotIn('aspectRatio', p['generationConfig']['imageConfig'])

    def test_all_14_ports_and_each_batch_image_preprocessed(self):
        kwargs = {f'🖼️ 图像{i}': torch.zeros((1, 10, 20, 3)) for i in range(1, 13)}
        kwargs['🖼️ 图像13'] = torch.zeros((1, 100, 3072, 3))
        kwargs['🖼️ 图像14'] = torch.ones((1, 3072, 100, 3))
        parts = Node._collect_reference_parts(kwargs)
        self.assertEqual(len(parts), 14)
        sizes = [Image.open(io.BytesIO(base64.b64decode(p['inlineData']['data']))).size for p in parts]
        self.assertEqual(sizes[-2:], [(2048, 67), (67, 2048)])
        self.assertTrue(all(max(s) <= 2048 for s in sizes))
        batch = Node._collect_reference_parts({'🖼️ 图像14': torch.zeros((2, 30, 50, 3))})
        self.assertEqual(len(batch), 2)

    def test_over_limit_is_rejected_before_paid_request(self):
        with patch.object(banana, 'submit_json_task') as submit:
            with self.assertRaisesRegex(RuntimeError, '15张.*14张'):
                asyncio.run(Node().generate(**inputs(**{'🖼️ 图像1': torch.zeros((15, 8, 8, 3))})))
            submit.assert_not_called()

    def test_invalid_thinking_is_rejected_before_paid_request(self):
        with patch.object(banana, 'submit_json_task') as submit:
            with self.assertRaisesRegex(RuntimeError, '不支持思考等级'):
                asyncio.run(Node().generate(**inputs(**{'🧠 思考等级': 'low'})))
            submit.assert_not_called()

    def test_list_mapping_really_overlaps_and_keeps_output_structure(self):
        barrier = threading.Barrier(2)
        starts, ends = [], []
        def fake(**kwargs):
            starts.append(time.monotonic())
            barrier.wait(timeout=5)
            ends.append(time.monotonic())
            return response()
        async def run():
            node = Node()
            return await asyncio.gather(*(node.generate(**inputs(**{'📝 提示词': str(i)})) for i in range(2)))
        with patch.object(banana, 'submit_json_task', side_effect=fake) as submit:
            results = asyncio.run(run())
            self.assertEqual(submit.call_count, 2)
        self.assertLess(max(starts), min(ends))
        self.assertTrue(all(len(r) == 3 and tuple(r[0].shape) == (1, 12, 16, 3) for r in results))

    def test_multiple_images_have_independent_clients_and_no_retry(self):
        barrier = threading.Barrier(2)
        clients = []
        def fake(client, model_id, payload):
            clients.append(client)
            barrier.wait(timeout=5)
            return response()
        with patch.object(banana.DapaoBananaRelayClient, 'generate_content', fake):
            result = asyncio.run(Node().generate(**inputs(**{'🖼️ 出图数量': 2, '⚡ 异步模式': True})))
        self.assertEqual(len({id(c) for c in clients}), 2)
        self.assertEqual(tuple(result[0].shape), (2, 12, 16, 3))
        with patch.object(banana, 'submit_json_task', side_effect=RuntimeError('HTTP 503 upstream unavailable')) as submit:
            with self.assertRaisesRegex(RuntimeError, '503.*upstream unavailable'):
                asyncio.run(Node().generate(**inputs()))
            self.assertEqual(submit.call_count, 1)


if __name__ == '__main__':
    unittest.main()
