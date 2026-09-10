import asyncio, importlib, inspect, sys, types, unittest, threading, io, base64
from pathlib import Path
from unittest.mock import patch
import torch
from PIL import Image
pkg=types.ModuleType('rh25tests');pkg.__path__=[str(Path(__file__).resolve().parent)];sys.modules[pkg.__name__]=pkg
m=importlib.import_module('rh25tests.rh_all_image_node')
class Tests(unittest.TestCase):
 def setUp(self):
  self.args={'🔑 API密钥':'offline','📝 提示词':'test image'}
  guard=patch.object(m.requests,'post',side_effect=AssertionError('Network forbidden'));guard.start();self.addCleanup(guard.stop)
 def test_routes(self):
  for model in m.IMAGE25_MODEL_CHOICES:
   for channel in m.CHANNEL_CHOICES:
    for mode in m.MODE_CHOICES:
     for api_channel in m.API_CHANNEL_CHOICES:
      calls=[]
      def submit(node,url,key,payload,timeout,*args,**kw):
       calls.append((url,payload,kw));return {'taskId':'offline','status':'SUCCESS','results':[{'url':'https://example.com/test.png'}]}
      args={**self.args,'🤖 模型':model,'🏷️ 渠道':channel,'🔀 模式':mode,'🌐 API渠道':api_channel,'🎨 画质':'max'}
      if mode=='图生图':args['🖼️ 图像1']=torch.zeros((1,16,16,3))
      with patch.object(m.DapaoRHAllImageNode,'_post_json',submit),patch.object(m.DapaoRHAllImageNode,'_download_image',return_value=Image.new('RGB',(8,8))):
       result=asyncio.run(m.DapaoRHAllImageNode().generate(**args))
      self.assertEqual(tuple(result[0].shape),(1,8,8,3));self.assertEqual(result[1],'https://example.com/test.png')
      variant=model.rsplit('-',1)[1];prefix='rhart-image-g-2.5'+('-official-token' if channel=='官方稳定版' else '')
      suffix='text-to-image' if mode=='文生图' else ('edit' if channel=='官方稳定版' else 'image-to-image')
      self.assertEqual(calls[0][0],m.API_BASE_URLS[api_channel]+'/'+prefix+'/'+variant+'/'+suffix)
      self.assertEqual(calls[0][2]['connection_retries'],0)
      self.assertEqual('quality' in calls[0][1],channel=='官方稳定版')
      self.assertEqual('imageUrls' in calls[0][1],mode=='图生图')
 def test_preprocessing_and_limits(self):
  node=m.DapaoRHAllImageNode();image=torch.zeros((1,64,4096,3))
  content=node._tensor_batch_to_png_bytes(image)[0];self.assertEqual(Image.open(io.BytesIO(content)).size,(2048,32))
  self.assertEqual(len(node._collect_image_urls({'🖼️ 图像16':torch.zeros((16,8,8,3))},'offline',30,16)),16)
  with self.assertRaisesRegex(ValueError,'最多接收10'):
   node._collect_image_urls({'🖼️ 图像1':torch.zeros((11,8,8,3))},'offline',30,10)
 def test_async_isolated_state_and_error_policy(self):
  self.assertTrue(inspect.iscoroutinefunction(m.DapaoRHAllImageNode.generate))
  barrier=threading.Barrier(2,timeout=3);workers=[]
  def work(node,**args):
   node._activate_api_channel(args['channel']);barrier.wait();workers.append(node);return node._current_api_channel()
  async def run():
   node=m.DapaoRHAllImageNode();return await asyncio.gather(node.generate(channel='国内版'),node.generate(channel='国外版'))
  with patch.object(m.DapaoRHAllImageNode,'_generate_sync',work):self.assertEqual(asyncio.run(run()),['国内版','国外版'])
  self.assertIsNot(workers[0],workers[1])
  with patch.object(m.requests,'post',side_effect=m.requests.Timeout('offline')) as request:
   result=asyncio.run(m.DapaoRHAllImageNode().generate(**self.args))
   self.assertIn('生成失败',result[2]);request.assert_called_once()
if __name__=='__main__':unittest.main()
