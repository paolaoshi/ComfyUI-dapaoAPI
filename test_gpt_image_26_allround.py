"""Static IMAGE contract, exact routes, preprocessing and no duplicate paid retries."""
import asyncio
import base64
import importlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import torch
from PIL import Image

pkg=types.ModuleType('dapao_image26_tests');pkg.__path__=[str(Path(__file__).resolve().parent)];sys.modules[pkg.__name__]=pkg
base=importlib.import_module(pkg.__name__+'.gpt_image_2_allround_node')
module=importlib.import_module(pkg.__name__+'.gpt_image_26_allround_node')


class Tests(unittest.TestCase):
    def setUp(self):
        for target in ('requests.request','requests.sessions.Session.request'):
            guard=patch(target,side_effect=AssertionError('Network forbidden'));guard.start();self.addCleanup(guard.stop)
        for name in ('_log_info','_log_error'):
            guard=patch.object(base,name);guard.start();self.addCleanup(guard.stop)
        image=io.BytesIO();Image.new('RGB',(16,16),'blue').save(image,format='PNG')
        self.response={'data':[{'b64_json':base64.b64encode(image.getvalue()).decode()}]}

    def run_node(self,**kwargs):
        return asyncio.run(module.DapaoGPTImage26AllroundNode().generate(**{'🔑 API密钥':'offline','📝 提示词':'test',**kwargs}))

    def test_routes_and_static_output_keep_model_stable_for_all_resolutions(self):
        for model in ('gpt-image-2.6-flare','gpt-image-2.6-sunburst'):
            for resolution in ('1K','2K','4K'):
                with patch.object(base,'submit_json_task',return_value=self.response) as submit:
                    result=self.run_node(**{'🤖 模型':model,'🧩 清晰度':resolution,'📐 图片尺寸/比例':'16:9'})
                    p=submit.call_args.kwargs['payload']
                    self.assertEqual(p['model'],model);self.assertEqual(p['resolution'],resolution.lower());self.assertEqual(p['response_format'],'url')
                    self.assertEqual(tuple(result[0].shape),(1,16,16,3));self.assertIn('实际结算',result[2])

    def test_edit_uses_ordered_image_array_fields_and_bounded_references(self):
        with patch.object(module.DapaoImage26RelayClient,'_request_json',return_value=self.response) as request:
            self.run_node(**{'🖼️ 图像1':torch.zeros((1,3000,1200,3)), '🖼️ 图像2':torch.ones((2,16,16,3)), '📐 图片尺寸/比例':'9:16'})
            self.assertEqual(request.call_args.args,('POST','/v1/images/edits'))
            data=request.call_args.kwargs['data'];files=request.call_args.kwargs['files']
            self.assertEqual(data['size'],'9:16');self.assertEqual(data['resolution'],'1k');self.assertNotIn('async',data)
            self.assertEqual([x[0] for x in files],['image[]']*3)
            self.assertEqual(Image.open(io.BytesIO(files[0][1][1])).size,(819,2048))
        with patch.object(module.DapaoImage26RelayClient,'_request_json') as request:
            with self.assertRaises(RuntimeError):self.run_node(**{'🖼️ 图像1':torch.zeros((4,16,16,3))})
            request.assert_not_called()


if __name__=='__main__':unittest.main()
