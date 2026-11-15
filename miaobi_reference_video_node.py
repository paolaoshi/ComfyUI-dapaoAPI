"""Text/image-reference video using the shared Miaobi queue, upload and VIDEO output."""
import asyncio
import re
from urllib.parse import quote

from . import seedance20_allround_video_node as shared
from .seedance25_global_sp_video_node import GlobalSPClient
from .node_error_utils import format_node_error

class MiaobiReferenceVideoNode(shared.DapaoSeedance20AllroundVideoNode):
    MAX_VIDEO_REFERENCES = 0
    MAX_AUDIO_REFERENCES = 0

    @classmethod
    def INPUT_TYPES(cls):
        inputs = super().INPUT_TYPES()
        required, optional = inputs['required'], inputs['optional']
        required['🎛️ 生成模式'] = (['自动识别', '文生视频', '图生视频'], {'default': '自动识别'})
        required['🧩 分辨率'] = (['720P'], {'default': '720P'})
        required['📐 视频比例'] = (['16:9', '9:16'], {'default': '16:9'})
        required['⏱️ 时长(秒)'][1].update(default=cls.DEFAULT_DURATION, tooltip=cls.DURATION_HINT)
        required.pop('🔊 生成音频')
        for name in ('🎬 首帧图', '🏁 尾帧图', '🎞️ 保留参考视频音轨'):
            optional.pop(name)
        for index in range(1, cls.MAX_IMAGE_REFERENCES + 1):
            optional[f'🖼️ 参考图{index}'] = ('IMAGE', {'tooltip': f'所有输入与图片批次合计最多{cls.MAX_IMAGE_REFERENCES}张；逐张等比缩小至最长边2048后上传。'})
        optional['⏱️ 轮询间隔'] = ('INT', {'default': 10, 'min': 5, 'max': 30, 'step': 1})
        return inputs

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        key = str(kwargs.get('🔑 API密钥') or '').strip()
        task_id, stage = '', 'validate'
        try:
            schema = self.INPUT_TYPES()
            unknown = set(kwargs) - set(schema['required']) - set(schema['optional'])
            if unknown:
                raise ValueError(self.VERSION_LABEL + '不支持这些输入：' + '、'.join(sorted(unknown)))
            if not key:
                raise ValueError('请填写妙笔API密钥。')
            for name in ('🤖 模型', '🎛️ 生成模式', '🧩 分辨率', '⏱️ 时长(秒)', '📐 视频比例'):
                options, config = schema['required'][name]
                if str(kwargs.get(name, config['default'])) not in options:
                    raise ValueError(f'{name}不支持：{kwargs.get(name)}')
            prompt = str(kwargs.get('📝 提示词') or '').strip()
            if not prompt or len(prompt) > 32000:
                raise ValueError('请填写视频提示词，最多32000字符。')
            seconds = str(kwargs.get('⏱️ 时长(秒)', self.DEFAULT_DURATION))
            ratio = kwargs.get('📐 视频比例', '16:9')
            mode = kwargs.get('🎛️ 生成模式', '自动识别')
            parts = self._collect_image_parts(kwargs)
            if mode == '文生视频' and parts:
                raise ValueError('文生视频不能接参考图，请选择自动识别或图生视频。')
            if mode == '图生视频' and not parts:
                raise ValueError('图生视频需要参考图片。')
            timeout, maximum, interval = (int(kwargs.get(name, default)) for name, default in
                [('⌛ 请求超时', 120), ('🔁 最大轮询秒数', 1800), ('⏱️ 轮询间隔', 10)])
            if not (30 <= timeout <= 600 and 60 <= maximum <= 7200 and 5 <= interval <= 30):
                raise ValueError('请求超时须30–600秒，最大轮询60–7200秒，轮询间隔5–30秒。')
            client = GlobalSPClient(key, timeout, maximum)
            client.recovery_salt = kwargs.get('🎲 随机种', 0)  # Local cache identity only; never a model seed.
            payload = dict(model=self.MODEL_ID, prompt=prompt, seconds=seconds, resolution='720p', size=ratio)
            stage = 'media_upload'
            if parts:
                payload['images'] = []
                for part in parts:
                    reference = client.upload_file(*part, self.MODEL_ID)
                    if not re.fullmatch(r'asset://file-[A-Za-z0-9_-]{1,59}', reference):
                        raise ValueError('妙笔上传未返回有效素材引用。')
                    payload['images'].append(reference)
            stage = 'video_submit'
            submitted = client.submit(payload)
            task_id = shared._task_id(submitted)
            if not task_id or not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', task_id) or submitted.get('object') == 'relay.job':
                raise RuntimeError('尚未取得视频任务ID，请保留队列记录查询，不要重复生成。')
            status, _, reason = shared._task_state(submitted)
            if status == 'failed':
                raise shared.DapaoSeedanceTaskError(task_id, submitted, reason)
            stage = 'video_poll'
            final = submitted if status == 'completed' else client.poll(task_id, maximum, interval)
            url = shared._extract_video_url(final) or shared.API_BASE_URL + '/v1/videos/' + quote(task_id, safe='') + '/content'
            width, height = self._expected_dimensions('720P', ratio)
            info = (f'✅ {self.VERSION_LABEL}视频完成\n模型：{self.MODEL_ID}\n模式：{"图生视频" if parts else "文生视频"}\n'
                    f'请求时长：{seconds}秒；{self.DURATION_HINT}\n720p · {ratio}\n'
                    f'任务ID：{task_id}\n基础价{self.BASE_PRICE}元/请求秒；实际以妙笔账户分组及账单为准。\n'
                    '保存失败请重试原视频保存；不要改变随机种后重新生成。')
            return shared.DapaoVideoAdapter(url, width, height, api_key=key, task_id=task_id), task_id, info, url
        except Exception as error:
            message = format_node_error(error, context=__name__)
            if key:
                message = message.replace(key, '***')
            raise RuntimeError(f'{message}\n模型：{self.MODEL_ID}；阶段：{stage}；任务ID：{task_id or "未取得"}') from None
