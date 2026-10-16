"""MiniMax H3 Miaobi: native assets, persistent acceptance queue, video task and local output."""
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import uuid
from urllib.parse import quote

import requests

from .dreambrush_runtime import ensure_asset_references, submit_json_task
from .image_input_utils import tensor_to_png_bytes
from .media_preprocess_utils import prepare_video, prepare_audio, _probe
from .node_error_utils import format_node_error
from .seedance20_allround_video_node import IO, DapaoVideoAdapter, _extract_video_url

MODEL = "minimax-h3-miaobi"
BASE = "https://api.dapaoai.com"
NODE_NAME = "DapaoMinimaxH3AllroundVideoNode"
DISPLAY_NAME = "🦁Minimax-H3全能视频@炮老师的小课堂"


def output_folder():
    import folder_paths
    folder = Path(folder_paths.get_output_directory()) / "dapao_h3"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def interrupted():
    try:
        import comfy.model_management as mm
    except ImportError:
        return
    mm.throw_exception_if_processing_interrupted()


class LocalH3Video(DapaoVideoAdapter):
    def __init__(self, path, width, height):
        super().__init__("", width, height)
        self.path = str(path)

    def save_to(self, output_path, **kwargs):
        if Path(output_path).resolve() != Path(self.path).resolve():
            shutil.copyfile(self.path, output_path)
        return True


class H3Client:
    def __init__(self, key, timeout=180, max_wait=3600, interval=5):
        self.key, self.timeout, self.max_wait, self.interval = key, timeout, max_wait, interval
        self.queue_id = ""
        self.task_id = ""
        self.retry_after = interval
        self.receipt = None
        self.record = {}

    def remember(self, **updates):
        import folder_paths
        if self.receipt is None:
            folder = Path(folder_paths.get_user_directory()) / "dapaoAPI" / "h3_tasks"
            folder.mkdir(parents=True, exist_ok=True)
            self.receipt = folder / (uuid.uuid4().hex + ".json")
        self.record.update(updates, queueJobId=self.queue_id, videoTaskId=self.task_id,
                           account_scope=hashlib.sha256((BASE + self.key).encode()).hexdigest())
        tmp = self.receipt.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.record, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, self.receipt)

    def get(self, path):
        r = requests.get(BASE + path, headers={"Authorization": "Bearer " + self.key},
                         timeout=self.timeout, allow_redirects=False)
        with r:
            try:
                self.retry_after = max(self.interval, min(600, int(r.headers.get("Retry-After", self.interval))))
            except (ValueError, TypeError):
                self.retry_after = self.interval
            if r.status_code >= 300:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:1800]}")
            return r.json()

    def pause(self, deadline):
        for _ in range(min(self.retry_after, max(0, int(deadline - time.monotonic())))):
            interrupted()
            time.sleep(1)

    def queue(self, identifier):
        self.queue_id = identifier
        self.remember(stage="恢复队列")
        path = "/v1/queue/jobs/" + quote(identifier, safe="")
        deadline = time.monotonic() + self.max_wait
        while time.monotonic() < deadline:
            interrupted()
            state = self.get(path)
            status = state.get("status")
            if status == "succeeded":
                return self.get(path + "/result")
            if status in {"failed", "canceled", "cancelled", "indeterminate"}:
                try:
                    detail = self.get(path + "/result")
                except Exception as e:
                    detail = str(e)
                raise RuntimeError(f"队列 {identifier} {status}：{detail}")
            if status not in {"queued", "running", "pending", "processing"}:
                raise RuntimeError(f"队列 {identifier} 状态待确认：{state}")
            self.pause(deadline)
        raise RuntimeError(f"队列 {identifier} 等待超时；请填写继续任务ID恢复查询，不要新建任务。")

    def submit(self, payload, seed):
        self.remember(stage="等待受理", request=payload, recovery_seed=seed)
        def status_changed(state, data):
            self.queue_id = str(data.get("id") or data.get("job_id") or self.queue_id)
            self.remember(stage=state)
        result = submit_json_task(api_key=self.key, base_url=BASE, endpoint="/v1/videos", payload=payload,
            timeout=self.timeout, max_poll_seconds=self.max_wait, recovery_salt=seed, reuse_succeeded=True,
            interrupt_callback=interrupted, status_callback=status_changed, user_agent="ComfyUI-dapaoAPI/MiniMaxH3")
        self.queue_id = result.get("_dapao_queue", {}).get("job_id", self.queue_id)
        self.task_id = str(result.get("id") or "")
        self.remember(stage="视频已受理")
        return result

    def poll(self, task_id):
        self.task_id = task_id
        self.remember(stage="查询视频")
        deadline = time.monotonic() + self.max_wait
        while time.monotonic() < deadline:
            interrupted()
            result = self.get("/v1/videos/" + quote(task_id, safe=""))
            status = result.get("status")
            if status == "completed":
                return result
            if status in {"failed", "canceled", "cancelled"}:
                raise RuntimeError(f"视频任务 {task_id} {status}：{json.dumps(result, ensure_ascii=False)}")
            if status not in {"queued", "in_progress", "pending", "processing"}:
                raise RuntimeError(f"视频任务 {task_id} 状态待确认：{json.dumps(result, ensure_ascii=False)}")
            self.pause(deadline)
        raise RuntimeError(f"视频任务 {task_id} 等待超时；请填写继续任务ID恢复查询，不要重新生成。")

    def download(self, task_id, result):
        folder = output_folder()
        target = folder / ("h3_" + uuid.uuid4().hex + ".mp4")
        url = _extract_video_url(result)
        # External URLs never receive the gateway key. Auth fallback uses a fixed origin.
        candidates = []
        if url.startswith(("https://", "http://")):
            candidates.append((url, {}, True))
        candidates.append((BASE + "/v1/videos/" + quote(task_id, safe="") + "/content",
                           {"Authorization": "Bearer " + self.key}, False))
        errors = []
        for address, headers, redirects in candidates:
            tmp = target.with_suffix(".part")
            try:
                with requests.get(address, headers=headers, stream=True, timeout=self.timeout,
                                  allow_redirects=redirects) as r:
                    if r.status_code >= 300:
                        raise RuntimeError(f"下载 HTTP {r.status_code}")
                    with tmp.open("wb") as f:
                        total = 0
                        for chunk in r.iter_content(1024 * 1024):
                            interrupted()
                            total += len(chunk)
                            if total > 1024 * 1024 * 1024:
                                raise RuntimeError("视频文件超过1GiB，本地保存已停止。")
                            f.write(chunk)
                probe = _probe(tmp)
                stream = next((s for s in probe["streams"] if s.get("codec_type") == "video"), None)
                if not stream or not tmp.stat().st_size:
                    raise RuntimeError("下载内容不是有效视频或文件为空。")
                os.replace(tmp, target)
                self.remember(stage="已保存", local_path=str(target))
                return LocalH3Video(target, stream["width"], stream["height"]), str(target)
            except Exception as e:
                tmp.unlink(missing_ok=True)
                errors.append(str(e))
                if type(e).__name__ == "InterruptProcessingException":
                    raise
        raise RuntimeError(f"视频已生成但保存失败，任务ID：{task_id}。填写继续任务ID重试保存；" + "；".join(errors))


class DapaoMinimaxH3AllroundVideoNode:
    @classmethod
    def INPUT_TYPES(cls):
        optional = {}
        for label, count, kind in [("🖼️ 参考图", 9, "IMAGE"), ("🎞️ 参考视频", 3, IO.VIDEO), ("🎵 参考音频", 3, "AUDIO")]:
            for i in range(1, count + 1):
                optional[label + str(i)] = (kind, {"tooltip": "按编号顺序提交，全部素材合计最多12项。图片批次逐张计数，最长边压至2048px；音视频建议每段2–15秒、每类合计不超过15秒。"})
        optional.update({
            "🆔 继续任务ID": ("STRING", {"default": "", "tooltip": "填写原job_队列ID或视频任务ID，仅查询并保存，不发起新生成。无需重新连接素材。"}),
            "🔁 最大轮询秒数": ("INT", {"default": 3600, "min": 60, "max": 7200}),
            "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30}),
            "⌛ 请求超时": ("INT", {"default": 180, "min": 30, "max": 600}),
        })
        return {"required": {
            "🔑 API密钥": ("STRING", {"default": "", "password": True, "tooltip": "可留空使用DAPAO_API_KEY环境变量。填写的密钥可能随ComfyUI工作流保存。"}),
            "🤖 模型": ([MODEL],),
            "📝 提示词": ("STRING", {"default": "镜头缓慢推进，主体动作自然，画面稳定，无字幕", "multiline": True}),
            "🧩 分辨率": (["720P", "1080P"], {"default": "720P"}),
            "📐 视频比例": (["16:9", "9:16"], {"default": "16:9"}),
            "⏱️ 时长(秒)": ("INT", {"default": 4, "min": 3, "max": 15}),
            "🔊 生成音频": ("BOOLEAN", {"default": True}),
            "🎲 随机种": ("INT", {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
                "control_after_generate": "fixed", "tooltip": "仅用于缓存和任务恢复，不发送给H3。生成新视频请改变此值；恢复任务优先填写继续任务ID。"}),
        }, "optional": optional}

    RETURN_TYPES = (IO.VIDEO, "STRING", "STRING", "STRING")
    RETURN_NAMES = ("🎬 视频", "🆔 任务ID", "📋 响应信息", "🔗 视频URL")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/🍬大炮AI主力维护🍬"
    DESCRIPTION = "H3妙笔文生/图生/混合参考自动识别，9图+3视频+3音频且总数≤12；成片先保存本地，原任务可继续查询。"

    @staticmethod
    def media(kwargs):
        for prefix, maximum in [("🖼️ 参考图", 9), ("🎞️ 参考视频", 3), ("🎵 参考音频", 3)]:
            if any(v is not None and k.startswith(prefix) and k[len(prefix):].isdigit() and int(k[len(prefix):]) > maximum for k, v in kwargs.items()):
                raise ValueError(f"{prefix}最多{maximum}项，不能静默忽略额外素材。")
        counts = [sum(int(v.shape[0]) for i in range(1, 10) if (v := kwargs.get(f"🖼️ 参考图{i}")) is not None),
                  sum(kwargs.get(f"🎞️ 参考视频{i}") is not None for i in range(1, 4)),
                  sum(kwargs.get(f"🎵 参考音频{i}") is not None for i in range(1, 4))]
        if counts[0] > 9 or sum(counts) > 12:
            raise ValueError(f"参考素材为{counts[0]}图/{counts[1]}视频/{counts[2]}音频，共{sum(counts)}项；最多9图/3视频/3音频且合计不超过12项。")
        if counts[2] and not (counts[0] or counts[1]):
            raise ValueError("参考音频必须同时搭配至少一张图片或一段视频。")
        blobs = [[], [], []]
        for i in range(1, 10):
            image = kwargs.get(f"🖼️ 参考图{i}")
            if image is not None:
                blobs[0].extend((data, f"h3_image_{i}_{j}.png", "image/png") for j, data in enumerate(tensor_to_png_bytes(image)))
        if any(len(b[0]) > 10 * 1024 * 1024 for b in blobs[0]):
            raise ValueError("图片压至2K后仍超过10MiB，请裁剪或更换图片。")
        for slot, label, prepare in [(1, "🎞️ 参考视频", prepare_video), (2, "🎵 参考音频", prepare_audio)]:
            total = 0
            for i in range(1, 4):
                value = kwargs.get(label + str(i))
                if value is not None:
                    blob = prepare(value, prefix=f"h3_{slot}_{i}")
                    total += blob[3]
                    if blob[3] < 1.95:
                        raise ValueError(f"{label}{i}请提供至少2秒的素材。")
                    blobs[slot].append(blob[:3])
            if total > 15.05:
                raise ValueError(f"{label}合计约{total:.2f}秒，本节点按接入建议限制为15秒，请裁剪后再连接。")
        return blobs, counts

    async def generate(self, **kwargs):
        return await asyncio.to_thread(self._generate_sync, **kwargs)

    def _generate_sync(self, **kwargs):
        client = None
        stage = "校验参数"
        try:
            key = (kwargs.get("🔑 API密钥") or os.environ.get("DAPAO_API_KEY", "")).strip()
            if not key:
                raise ValueError("请填写妙笔API密钥或配置DAPAO_API_KEY。")
            client = H3Client(key, int(kwargs.get("⌛ 请求超时", 180)), int(kwargs.get("🔁 最大轮询秒数", 3600)), int(kwargs.get("⏱️ 轮询间隔", 5)))
            resume = str(kwargs.get("🆔 继续任务ID", "")).strip()
            counts = [0, 0, 0]
            if resume:
                if not re.fullmatch(r"[A-Za-z0-9_-]{1,200}", resume):
                    raise ValueError("继续任务ID格式无效，请填写队列或视频任务ID。")
                stage = "恢复原任务"
                submitted = client.queue(resume) if resume.startswith("job_") else {"id": resume}
            else:
                prompt = str(kwargs.get("📝 提示词", "")).strip()
                resolution = kwargs.get("🧩 分辨率", "720P")
                ratio = kwargs.get("📐 视频比例", "16:9")
                duration = kwargs.get("⏱️ 时长(秒)", 4)
                if kwargs.get("🤖 模型", MODEL) != MODEL or resolution not in ["720P", "1080P"] or ratio not in ["16:9", "9:16"]:
                    raise ValueError("模型、分辨率或比例不受支持；H3妙笔暂不开放2K。")
                if not prompt or type(duration) is not int or not 3 <= duration <= 15:
                    raise ValueError("提示词不能为空，生成时长必须是3–15秒的整数。")
                stage = "预处理素材"
                blobs, counts = self.media(kwargs)
                stage = "上传并复用素材"
                refs = ensure_asset_references(key, [b for group in blobs for b in group], base_url=BASE, timeout=client.timeout) if sum(counts) else []
                payload = dict(model=MODEL, prompt=prompt, duration=duration, resolution=resolution.lower(), aspect_ratio=ratio,
                               generate_audio=bool(kwargs.get("🔊 生成音频", True)))
                offset = 0
                for name, count in zip(["images", "videos", "audios"], counts):
                    if count:
                        payload[name] = refs[offset:offset + count]
                    offset += count
                if len(refs) != sum(counts):
                    raise RuntimeError("素材上传结果数量不符，未提交生成。")
                stage = "等待异步受理"
                submitted = client.submit(payload, kwargs.get("🎲 随机种", 0))
            task = str(submitted.get("id") or "")
            if not task or task.startswith("job_"):
                raise RuntimeError("受理结果缺少视频任务ID；队列成功不代表视频完成。")
            client.task_id = task
            stage = "生成中"
            result = client.poll(task)
            stage = "正在保存"
            video, path = client.download(task, result)
            info = (f"✅ H3视频已保存\n模型：{MODEL}\n队列ID：{client.queue_id}\n视频任务ID：{task}\n"
                    f"素材：{counts[0]}图/{counts[1]}视频/{counts[2]}音频（恢复任务不重新上传）\n"
                    f"本地文件：{path}\n实际尺寸：{video.width}×{video.height}\n费用以妙笔账单为准，按请求输出时长计费。")
            return video, task, info, _extract_video_url(result)
        except Exception as e:
            ids = f"队列ID：{client.queue_id}；视频任务ID：{client.task_id}" if client else ""
            message = format_node_error(f"H3视频处理失败，阶段：{stage}；{ids}；{e}", context=__name__)
            raise RuntimeError(message) from None


NODE_CLASS_MAPPINGS = {NODE_NAME: DapaoMinimaxH3AllroundVideoNode}
NODE_DISPLAY_NAME_MAPPINGS = {NODE_NAME: DISPLAY_NAME}

# Public pricing only: fixed upstream URLs, no user credentials and no expression execution.
def public_prices():
    with requests.get(BASE + '/api/pricing', timeout=10) as r:
        r.raise_for_status()
        row = next((x for x in r.json().get('data', []) if x.get('model_name') == MODEL), {})
    with requests.get(BASE + '/api/status', timeout=10) as r:
        r.raise_for_status()
        exchange = float(r.json().get('data', {}).get('usd_exchange_rate') or 0)
    pattern = r'video_second_price\(lower\(trim\(param\("resolution"\) \?\? "720p"\)\) == "1080p" \? ([\d.]+) / ([\d.]+) : ([\d.]+) / ([\d.]+)\)'
    match = re.fullmatch(pattern, row.get('billing_expr', ''))
    if not match or exchange <= 0:
        return {}
    a, b, c, d = map(float, match.groups())
    if min(a, b, c, d) <= 0:
        return {}
    return {'1080P': a / b * exchange, '720P': c / d * exchange}


try:
    from server import PromptServer
    from aiohttp import web
    if getattr(PromptServer, 'instance', None) is not None:
        @PromptServer.instance.routes.get('/dapao/minimax-h3/pricing')
        async def h3_public_pricing(request):
            try:
                rates = await asyncio.to_thread(public_prices)
            except Exception:
                rates = {}
            return web.json_response({'rates': rates, 'group': 'default'})
except ImportError:
    pass
