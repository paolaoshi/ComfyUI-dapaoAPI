"""H3 contracts: all remote I/O intercepted, no paid calls."""
import asyncio
import importlib
import inspect
import io
import sys
import tempfile
import threading
import types
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import torch
from PIL import Image

pkg=types.ModuleType('h3_test');pkg.__path__=[str(Path(__file__).parent)];sys.modules[pkg.__name__]=pkg
m=importlib.import_module('h3_test.minimax_h3_allround_video_node')
Node=m.DapaoMinimaxH3AllroundVideoNode

def args(**kw):return {'🔑 API密钥':'offline-test','📝 提示词':'镜头推进',**kw}

class H3Tests(unittest.TestCase):
    def setUp(self):
        self.net=patch.object(m.requests,'get',side_effect=AssertionError('Unexpected network'));self.net.start();self.addCleanup(self.net.stop)
        self.submit=patch.object(m,'submit_json_task',side_effect=AssertionError('Unexpected submission'));self.submit.start();self.addCleanup(self.submit.stop)
        self.assets=patch.object(m,'ensure_asset_references',side_effect=AssertionError('Unexpected upload'));self.assets.start();self.addCleanup(self.assets.stop)
        self.rem=patch.object(m.H3Client,'remember');self.rem.start();self.addCleanup(self.rem.stop)
    def test_schema(self):
        self.assertTrue(inspect.iscoroutinefunction(Node.generate))
        self.assertFalse(getattr(Node,'INPUT_IS_LIST',False))
        s=Node.INPUT_TYPES();self.assertEqual(s['required']['🧩 分辨率'][0],['720P','1080P'])
        self.assertEqual(len([x for x in s['optional'] if x.startswith('🖼️ 参考图')]),9)
    def test_price_expression_is_data_not_code(self):
        r=MagicMock();r.__enter__.return_value=r
        r.json.side_effect=[{'data':[{'model_name':m.MODEL,'billing_expr':'video_second_price(lower(trim(param("resolution") ?? "720p")) == "1080p" ? 0.135 / 7.3 : 0.075 / 7.3)'}]}, {'data':{'usd_exchange_rate':7.3}}]
        with patch.object(m.requests,'get',return_value=r):self.assertEqual(m.public_prices(),{'1080P':0.135,'720P':0.075})
    def test_receipt_contains_ids_but_no_key(self):
        self.rem.stop()
        with tempfile.TemporaryDirectory() as root,patch.dict(sys.modules,{'folder_paths':types.SimpleNamespace(get_user_directory=lambda:root)}):
            c=m.H3Client('private-key');c.queue_id='job_one';c.task_id='video_one';c.remember(stage='生成中')
            text=c.receipt.read_text(encoding='utf-8');self.assertIn('video_one',text);self.assertIn('job_one',text);self.assertNotIn('private-key',text)
    def test_exact_request_and_two_stages(self):
        with patch.object(m,'submit_json_task',return_value={'id':'video_x','_dapao_queue':{'job_id':'job_x'}}) as post, patch.object(m.H3Client,'poll',return_value={'status':'completed','metadata':{'url':'https://example.com/a.mp4'}}) as poll, patch.object(m.H3Client,'download',return_value=(m.LocalH3Video('local.mp4',1280,768),'local.mp4')):
            out=asyncio.run(Node().generate(**args()))
            self.assertEqual(len(out),4);self.assertEqual(out[1],'video_x');poll.assert_called_once_with('video_x')
            self.assertEqual(post.call_args.kwargs['endpoint'],'/v1/videos')
            self.assertEqual(post.call_args.kwargs['payload'],dict(model=m.MODEL,prompt='镜头推进',duration=4,resolution='720p',aspect_ratio='16:9',generate_audio=True))
            self.assertTrue(post.call_args.kwargs['reuse_succeeded']);self.assertEqual(post.call_count,1)
    def test_preflight_limits(self):
        for kw in [{'⏱️ 时长(秒)':2},{'⏱️ 时长(秒)':4.5},{'🧩 分辨率':'2K'}, {'🎵 参考音频1':{}},{'🖼️ 参考图1':torch.zeros(10,8,8,3)}, {'🎞️ 参考视频4':object()},
                   {'🖼️ 参考图1':torch.zeros(9,8,8,3),**{f'🎞️ 参考视频{i}':object() for i in range(1,4)},'🎵 参考音频1':{}}]:
            with self.subTest(kw=list(kw)), self.assertRaises(RuntimeError):asyncio.run(Node().generate(**args(**kw)))
    def test_png_resize_order_and_mixed_twelve(self):
        image=torch.zeros(6,20,3072,3)
        kw={'🖼️ 参考图1':image,**{f'🎞️ 参考视频{i}':object() for i in range(1,4)},**{f'🎵 参考音频{i}':{} for i in range(1,4)}}
        with patch.object(m,'prepare_video',return_value=(b'v','v.mp4','video/mp4',4)),patch.object(m,'prepare_audio',return_value=(b'a','a.mp3','audio/mpeg',4)):
            blobs,counts=Node.media(kw)
        self.assertEqual(counts,[6,3,3]);self.assertEqual(len(blobs[0]),6)
        im=Image.open(io.BytesIO(blobs[0][0][0]));self.assertEqual(max(im.size),2048);self.assertEqual(im.format,'PNG')
    def test_resume_never_uploads_or_submits(self):
        with patch.object(m.H3Client,'queue',return_value={'id':'video_old'}) as queue,patch.object(m.H3Client,'poll',return_value={}),patch.object(m.H3Client,'download',return_value=(m.LocalH3Video('old.mp4',100,100),'old.mp4')):
            out=asyncio.run(Node().generate(**args(**{'🆔 继续任务ID':'job_old'})))
            queue.assert_called_once_with('job_old');self.assertEqual(out[1],'video_old')
    def test_parallel_tasks_overlap(self):
        barrier=threading.Barrier(2,timeout=4)
        def submit(client,payload,seed):barrier.wait();return {'id':'video_x'}
        with patch.object(m.H3Client,'submit',submit),patch.object(m.H3Client,'poll',return_value={}),patch.object(m.H3Client,'download',return_value=(m.LocalH3Video('x',20,20),'x')):
            async def run():return await asyncio.gather(Node().generate(**args()),Node().generate(**args()))
            self.assertEqual(len(asyncio.run(run())),2)
    def test_failure_no_retry(self):
        with patch.object(m,'submit_json_task',side_effect=RuntimeError('HTTP 503 upstream')) as post:
            with self.assertRaisesRegex(RuntimeError,'HTTP 503'):asyncio.run(Node().generate(**args()))
            self.assertEqual(post.call_count,1)
    def test_auth_fallback_and_atomic_video_save(self):
        responses=[]
        def get(url,**kw):
            responses.append((url,kw));r=MagicMock();r.__enter__.return_value=r
            r.status_code=403 if len(responses)==1 else 200;r.iter_content.return_value=[b'video-data'];return r
        with tempfile.TemporaryDirectory() as root,patch.object(m,'output_folder',return_value=Path(root)),patch.object(m.requests,'get',side_effect=get),patch.object(m,'_probe',return_value={'streams':[{'codec_type':'video','width':1920,'height':1080}]}):
            video,path=m.H3Client('secret').download('video_1',{'metadata':{'url':'https://external.invalid/file'}})
            self.assertEqual(Path(path).read_bytes(),b'video-data');self.assertEqual(video.get_dimensions(),(1920,1080))
            target=Path(root)/'save.mp4';video.save_to(target);self.assertEqual(target.read_bytes(),b'video-data')
        self.assertEqual(responses[0][1]['headers'],{})
        self.assertEqual(responses[1][0],m.BASE+'/v1/videos/video_1/content')
        self.assertFalse(responses[1][1]['allow_redirects'])
    def test_queue_success_is_only_acceptance(self):
        c=m.H3Client('test');c.pause=lambda _:None
        with patch.object(c,'get',side_effect=[{'status':'running'},{'status':'succeeded'},{'id':'video_9'}]) as get:
            self.assertEqual(c.queue('job_9')['id'],'video_9');self.assertEqual(get.call_count,3)
        with patch.object(c,'get',side_effect=[{'status':'in_progress'},{'status':'completed'}]) as get:
            self.assertEqual(c.poll('video_9')['status'],'completed');self.assertEqual(get.call_args.args[0],'/v1/videos/video_9')

if __name__=='__main__':unittest.main()
