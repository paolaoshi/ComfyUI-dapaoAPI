"""Offline request, image boundary and mapped concurrency contracts; never paid calls."""
import asyncio
import importlib
import inspect
import io
import sys
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from PIL import Image

PACKAGE = 'dapao_muse_tests'
package = types.ModuleType(PACKAGE)
package.__path__ = [str(Path(__file__).resolve().parent)]
sys.modules[PACKAGE] = package
module = importlib.import_module(PACKAGE + '.muse_video_node')


class Tensor:
    def __init__(self, array): self.array, self.shape = array, array.shape
    def __getitem__(self, index): return Tensor(self.array[index])
    def detach(self): return self
    def cpu(self): return self
    def numpy(self): return self.array


class Tests(unittest.TestCase):
    def setUp(self):
        self.patch = patch.object(importlib.import_module(PACKAGE + '.miaobi_reference_video_node'), 'GlobalSPClient')
        self.client_class = self.patch.start()
        self.addCleanup(self.patch.stop)
        self.client = self.client_class.return_value
        self.client.submit.return_value = {'id': 'task-muse-test', 'status': 'completed', 'metadata': {'url': 'https://example.com/video.mp4'}}
        self.client.upload_file.return_value = 'asset://file-muse-test'

    def run_node(self, **values):
        return asyncio.run(module.DapaoMuseVideoNode().generate(**{'🔑 API密钥': 'offline-key', '📝 提示词': 'lake', **values}))

    def test_schema_and_all_billable_durations(self):
        cls = module.DapaoMuseVideoNode
        self.assertTrue(inspect.iscoroutinefunction(cls.generate))
        self.assertFalse(getattr(cls, 'INPUT_IS_LIST', False))
        self.assertEqual(cls.MAX_IMAGE_REFERENCES, 1)
        self.assertNotIn('🎬 首帧图', cls.INPUT_TYPES()['optional'])
        for seconds in range(4, 31):
            result = self.run_node(**{'⏱️ 时长(秒)': str(seconds), '📐 视频比例': '9:16'})
            self.assertEqual(len(result), 4)
            self.assertEqual(result[0].get_dimensions(), (720, 1280))
            self.assertEqual(self.client.submit.call_args.args[0], dict(model='muse-video', prompt='lake', seconds=str(seconds), resolution='720p', size='9:16'))

    def test_single_image_preprocessed_at_actual_upload_boundary(self):
        image = Tensor(np.ones((1, 1200, 3000, 3), dtype=np.float32))
        self.run_node(**{'🖼️ 参考图1': image, '🎲 随机种': 42})
        content, name, mime, model = self.client.upload_file.call_args.args
        self.assertEqual(Image.open(io.BytesIO(content)).size, (2048, 819))
        self.assertEqual(mime, 'image/png')
        self.assertEqual(self.client.submit.call_args.args[0]['images'], ['asset://file-muse-test'])
        self.assertNotIn('seed', self.client.submit.call_args.args[0])
        self.assertEqual(self.client.recovery_salt, 42)

    def test_invalid_inputs_stop_before_upload_and_submit(self):
        for values in [{'⏱️ 时长(秒)': '3'}, {'⏱️ 时长(秒)': '31'}, {'🧩 分辨率': '1080P'}, {'📐 视频比例': '1:1'},
                       {'🎛️ 生成模式': '首尾帧生视频'}, {'🎛️ 生成模式': '图生视频'}, {'🔊 生成音频': True},
                       {'🖼️ 参考图1': Tensor(np.ones((2, 4, 4, 3)))}, {'🎞️ 参考视频1': 'video'}]:
            with self.assertRaises(RuntimeError): self.run_node(**values)
        self.client_class.assert_not_called()

    def test_paid_failure_preserves_reason_and_does_not_retry(self):
        self.client.submit.return_value = {'id':'task-failed','status':'failed','error':{'message':'provider unavailable'}}
        with self.assertRaises(RuntimeError) as caught: self.run_node()
        self.assertIn('task-failed', str(caught.exception))
        self.assertNotIn('offline-key', str(caught.exception))
        self.client.submit.assert_called_once()

    def test_mapped_calls_overlap_without_shared_client_state(self):
        barrier = threading.Barrier(2, timeout=5)
        def make_client(*args):
            client = types.SimpleNamespace()
            def submit(payload):
                barrier.wait()
                return {'id':'task-' + payload['prompt'], 'status':'completed', 'metadata':{'url':'https://example.com/video.mp4'}}
            client.submit = submit
            return client
        self.client_class.side_effect = make_client
        async def run():
            node=module.DapaoMuseVideoNode()
            return await asyncio.gather(*(node.generate(**{'🔑 API密钥':'offline-key','📝 提示词':value}) for value in ('one','two')))
        self.assertEqual([r[1] for r in asyncio.run(run())], ['task-one','task-two'])

    def test_omni_shared_execution_discrete_duration_and_three_references(self):
        omni=importlib.import_module(PACKAGE+'.gemini_omni_video_node').DapaoGeminiOmniVideoNode()
        self.assertEqual(omni.INPUT_TYPES()['required']['⏱️ 时长(秒)'][1]['default'],'8')
        for seconds in ['4','6','8','10']:
            asyncio.run(omni.generate(**{'🔑 API密钥':'offline-key','📝 提示词':'cameras','⏱️ 时长(秒)':seconds,'🖼️ 参考图1':Tensor(np.ones((3,16,16,3)))}))
            p=self.client.submit.call_args.args[0]
            self.assertEqual(p['model'],'gemini-omni-1.2-flash');self.assertEqual(p['seconds'],seconds);self.assertEqual(len(p['images']),3)
        for values in [{'⏱️ 时长(秒)':'5'},{'🖼️ 参考图1':Tensor(np.ones((4,16,16,3)))},{'🎵 参考音频1':'audio'}]:
            self.client.submit.reset_mock()
            with self.assertRaises(RuntimeError):asyncio.run(omni.generate(**{'🔑 API密钥':'offline-key','📝 提示词':'cameras',**values}))
            self.client.submit.assert_not_called()


if __name__ == '__main__': unittest.main()
