"""
RH 全能图片多并发节点

复用 RH 全能图片节点的模型配置与请求逻辑，在节点内部并发提交多个 RunningHub 任务。
作者：@炮老师的小课堂
"""

import json
import re
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

import torch

try:
    import comfy.utils
except Exception:
    comfy = None

from .rh_all_image_node import (
    ALL_RATIOS,
    BASE_URL,
    CHANNEL_CHOICES,
    ENDPOINT_CONFIGS,
    MODE_CHOICES,
    MODEL_CHOICES,
    POLL_URL,
    DapaoRHAllImageNode,
    create_blank_tensor,
    pil2tensor,
)


NODE_NAME = "DapaoRHAllImageConcurrentNode"
FAILURE_CHOICES = ["跳过失败继续", "失败返回占位", "任一失败中断"]


def _log_info(message):
    print(f"[dapaoAPI-RH全能图片多并发] 信息：{message}")


def _log_error(message):
    print(f"[dapaoAPI-RH全能图片多并发] 错误：{message}")


class DapaoRHAllImageConcurrentNode(DapaoRHAllImageNode):
    INPUT_IS_LIST = True

    @classmethod
    def INPUT_TYPES(cls):
        result = {
            "required": {
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "填入 RunningHub API Key",
                    "tooltip": "RunningHub API Key，仅用于本次请求，不会写入文件。"
                }),
                "🤖 模型": (MODEL_CHOICES, {
                    "default": "全能图片G-2",
                    "tooltip": "只保留 G-2、V2、PRO 三个模型，具体端点由渠道和模式共同决定。"
                }),
                "🏷️ 渠道": (CHANNEL_CHOICES, {
                    "default": "官方稳定版",
                    "tooltip": "官方稳定版质量更稳；低价渠道版通常费用更低。"
                }),
                "🔀 模式": (MODE_CHOICES, {
                    "default": "文生图",
                    "tooltip": "文生图不需要参考图；图生图会把接入的参考图复用于每一个并发任务。"
                }),
                "📝 提示词": ("STRING", {
                    "multiline": True,
                    "default": "一张高端商业摄影海报，干净的自然光，细节清晰，质感高级",
                    "placeholder": "多行优先：一行一个任务；只有一行时，才按任务数量重复生成。"
                }),
                "🔢 任务数量": ("INT", {
                    "default": 1,
                    "min": 1,
                    "max": 100,
                    "step": 1,
                    "tooltip": "只在手动输入单行提示词且没有连接上游时生效；多行提示词或上游连接输入会优先决定实际任务数量。"
                }),
                "🚀 并发数": ("INT", {
                    "default": 4,
                    "min": 1,
                    "max": 20,
                    "step": 1,
                    "tooltip": "同时运行的 RH 任务上限；不会增加总任务数量，多行提示词时不会超过有效行数。"
                }),
                "🧪 失败策略": (FAILURE_CHOICES, {
                    "default": "跳过失败继续",
                    "tooltip": "跳过失败继续会只返回成功图；失败返回占位会用黑图保持任务顺序；任一失败中断会返回错误。"
                }),
                "🛟 失败重试次数": ("INT", {
                    "default": 1,
                    "min": 0,
                    "max": 5,
                    "step": 1,
                    "tooltip": "单个任务失败后的额外重试次数。"
                }),
                "🌊 流式接收": ("BOOLEAN", {
                    "default": True,
                    "tooltip": "开启后每个 RH 任务完成就立即接收图片并更新预览；最终输出仍按 ComfyUI 规则在节点结束后统一传递。"
                }),
                "📐 画面比例": (ALL_RATIOS, {
                    "default": "模型默认",
                    "tooltip": "选择模型默认时自动使用当前端点默认比例。G-2 低价渠道的 empty 表示不指定比例。"
                }),
                "🧩 分辨率": (["模型默认", "1k", "2k", "4k"], {
                    "default": "模型默认",
                    "tooltip": "选择模型默认时自动使用当前端点默认分辨率。"
                }),
                "🎨 画质": (["模型默认", "low", "medium", "high"], {
                    "default": "模型默认",
                    "tooltip": "当前只在 G-2 官方稳定版端点中生效；其他端点会自动忽略。"
                }),
                "🎲 随机种": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "control_after_generate": "randomize",
                    "tooltip": "只用于 ComfyUI 判断是否重新执行；不会发送给 RunningHub。"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE", {"tooltip": "图生图参考图，会复用于每一个并发任务。"}),
                "🖼️ 图像2": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像3": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像4": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像5": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像6": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像7": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像8": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像9": ("IMAGE", {"tooltip": "可选参考图。"}),
                "🖼️ 图像10": ("IMAGE", {"tooltip": "可选参考图。"}),
                "📋 额外参数JSON": ("STRING", {
                    "multiline": True,
                    "default": "{}",
                    "placeholder": "{\"aspectRatio\":\"1:1\"}",
                    "tooltip": "JSON对象，会合并到每个 RH 请求体；同名字段会覆盖节点控件生成的参数。"
                }),
                "🔁 最大轮询秒数": ("INT", {"default": 1200, "min": 60, "max": 3600, "step": 10}),
                "⏱️ 轮询间隔": ("INT", {"default": 5, "min": 2, "max": 30, "step": 1}),
                "⌛ 请求超时": ("INT", {"default": 60, "min": 10, "max": 300, "step": 1}),
            }
        }
        result["hidden"] = {
            "prompt": "PROMPT",
            "unique_id": "UNIQUE_ID",
        }
        return result

    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("🖼️ 图像批次", "🔗 图片链接", "📋 响应信息")
    FUNCTION = "generate_concurrent"
    CATEGORY = "🤖dapaoAPI/RH全能图片"
    DESCRIPTION = "RunningHub RH 全能图片系列多并发批量生成 @炮老师的小课堂"
    OUTPUT_NODE = False

    @staticmethod
    def _split_prompt_lines(prompt_text):
        def collect(value):
            if value is None:
                return []
            if isinstance(value, (list, tuple)):
                lines = []
                for item in value:
                    lines.extend(collect(item))
                return lines
            if isinstance(value, dict):
                for key in ("prompt", "prompts", "text", "texts", "body_text", "value"):
                    if key in value:
                        return collect(value[key])
                lines = []
                for item in value.values():
                    lines.extend(collect(item))
                return lines

            text = str(value).strip()
            if not text:
                return []

            if text[:1] in ("[", "{"):
                try:
                    parsed = json.loads(text)
                    if parsed is not value:
                        parsed_lines = collect(parsed)
                        if parsed_lines:
                            return parsed_lines
                except Exception:
                    pass

            parts = re.split(r"\r?\n+", text)
            return [line.strip() for line in parts if line.strip()]

        return collect(prompt_text)

    @classmethod
    def _build_prompt_list(cls, prompt_text, task_count, max_tasks=100):
        lines = cls._split_prompt_lines(prompt_text)
        if not lines:
            return []
        if len(lines) > 1:
            return lines[:max_tasks]
        return [lines[0]] * task_count

    @staticmethod
    def _fit_prompt_count(prompts, task_count):
        if not prompts:
            return []
        if len(prompts) >= task_count:
            return prompts[:task_count]
        return prompts + [prompts[-1]] * (task_count - len(prompts))

    @staticmethod
    def _is_prompt_input_connected(kwargs):
        workflow_prompt = DapaoRHAllImageConcurrentNode._first_input_value(kwargs.get("prompt"))
        unique_id = DapaoRHAllImageConcurrentNode._first_input_value(kwargs.get("unique_id"))
        if not isinstance(workflow_prompt, dict) or unique_id is None:
            return False

        node_data = workflow_prompt.get(str(unique_id)) or workflow_prompt.get(unique_id)
        if not isinstance(node_data, dict):
            return False

        inputs = node_data.get("inputs")
        if not isinstance(inputs, dict):
            return False

        value = inputs.get("📝 提示词")
        return isinstance(value, list) and len(value) >= 2

    @staticmethod
    def _first_input_value(value, default=None):
        if isinstance(value, (list, tuple)):
            if not value:
                return default
            return value[0]
        return value if value is not None else default

    @classmethod
    def _text_input_value(cls, kwargs, name, default=""):
        return cls._first_input_value(kwargs.get(name), default)

    @classmethod
    def _int_input_value(cls, kwargs, name, default):
        value = cls._first_input_value(kwargs.get(name), default)
        try:
            return int(value)
        except Exception:
            return int(default)

    @classmethod
    def _bool_input_value(cls, kwargs, name, default):
        value = cls._first_input_value(kwargs.get(name), default)
        if isinstance(value, str):
            return value.strip().lower() not in ("", "0", "false", "no", "off", "关闭")
        return bool(value)

    @staticmethod
    def _expand_image_input(value):
        if value is None:
            return []
        values = list(value) if isinstance(value, (list, tuple)) else [value]
        images = []
        for item in values:
            if item is None:
                continue
            if isinstance(item, torch.Tensor):
                if item.dim() == 4:
                    images.extend(item[index:index + 1] for index in range(item.shape[0]))
                elif item.dim() == 3:
                    images.append(item.unsqueeze(0))
                continue
            images.append(item)
        return images

    @classmethod
    def _select_task_image(cls, value, task_index):
        images = cls._expand_image_input(value)
        if not images:
            return None
        if task_index < len(images):
            return images[task_index]
        if len(images) == 1:
            return images[0]
        return images[-1]

    @classmethod
    def _image_input_counts(cls, kwargs):
        counts = []
        for input_index in range(1, 11):
            key = f"🖼️ 图像{input_index}"
            count = len(cls._expand_image_input(kwargs.get(key)))
            if count:
                counts.append((key, count))
        return counts

    def _collect_task_image_urls(self, image_inputs, task_index, api_key, timeout, max_images):
        image_urls = []
        for input_index in range(1, 11):
            key = f"🖼️ 图像{input_index}"
            image_tensor = self._select_task_image(image_inputs.get(key), task_index)
            if image_tensor is None:
                continue
            for batch_index, content in enumerate(self._tensor_batch_to_png_bytes(image_tensor), start=1):
                if len(image_urls) >= max_images:
                    return image_urls
                filename = f"comfyui_ref_task{task_index + 1}_{input_index}_{batch_index}.png"
                image_urls.append(self._image_bytes_to_input_url(api_key, content, filename, timeout))
        return image_urls

    def _poll_task_no_progress(self, task_id, api_key, max_seconds, interval, timeout):
        elapsed = 0
        consecutive_failures = 0

        while elapsed < max_seconds:
            time.sleep(interval)
            elapsed += interval
            try:
                result = self._post_json(POLL_URL, api_key, {"taskId": task_id}, timeout)
                consecutive_failures = 0
            except Exception as e:
                consecutive_failures += 1
                if consecutive_failures >= 5:
                    raise RuntimeError(f"连续多次轮询失败，任务状态未知。最后错误：{e}")
                continue

            result_data = self._payload_data(result)
            status = result_data.get("status") or result.get("status", "UNKNOWN")
            if status == "SUCCESS":
                return result_data or result
            if status == "FAILED":
                error_msg = result_data.get("errorMessage") or result.get("msg") or "Unknown error"
                error_code = result_data.get("errorCode") or result.get("errorCode") or ""
                raise RuntimeError(f"任务失败：[{error_code}] {error_msg}")

        raise RuntimeError(f"任务超过 {max_seconds} 秒仍未完成，请稍后查询任务ID：{task_id}")

    def _run_one_task(
        self,
        task_index,
        prompt,
        api_key,
        config,
        ratio,
        resolution,
        quality,
        image_inputs,
        extra_params,
        max_seconds,
        interval,
        timeout,
        retry_count,
    ):
        last_error = None
        last_traceback = ""
        for attempt in range(retry_count + 1):
            submit_response = {}
            final_response = {}
            try:
                image_urls = []
                if image_inputs is not None:
                    image_urls = self._collect_task_image_urls(
                        image_inputs,
                        task_index,
                        api_key,
                        timeout,
                        config["max_images"],
                    )
                    if not image_urls:
                        raise ValueError("选择图生图时，请至少接入一张参考图。")

                payload, final_ratio, final_resolution, final_quality = self._build_payload(
                    config,
                    prompt,
                    ratio,
                    resolution,
                    quality,
                    image_urls,
                    dict(extra_params),
                )
                endpoint = config["endpoint"]
                submit_response = self._post_json(f"{BASE_URL}/{endpoint}", api_key, payload, timeout)
                if submit_response.get("errorCode") or submit_response.get("errorMessage"):
                    raise RuntimeError(
                        f"RunningHub 提交失败：[{submit_response.get('errorCode') or ''}] "
                        f"{submit_response.get('errorMessage') or submit_response}"
                    )
                task_id = self._extract_task_id(submit_response)
                if not task_id:
                    raise RuntimeError(f"提交成功但响应中没有 taskId：{json.dumps(submit_response, ensure_ascii=False)[:1000]}")

                submit_data = self._payload_data(submit_response)
                if submit_data.get("status") == "SUCCESS" and submit_data.get("results"):
                    final_response = submit_data
                else:
                    final_response = self._poll_task_no_progress(task_id, api_key, max_seconds, interval, timeout)

                urls = self._extract_urls(final_response)
                if not urls:
                    raise RuntimeError(f"任务完成但没有返回图片 URL：{json.dumps(final_response, ensure_ascii=False)[:1000]}")

                images = [self._download_image(url, timeout) for url in urls]
                cost, duration = self._extract_usage(final_response)
                return {
                    "index": task_index,
                    "ok": True,
                    "prompt": prompt,
                    "task_id": task_id,
                    "urls": urls,
                    "images": images,
                    "cost": cost,
                    "duration": duration,
                    "attempts": attempt + 1,
                    "reference_images": len(image_urls),
                    "ratio": final_ratio,
                    "resolution": final_resolution,
                    "quality": final_quality,
                    "submit": submit_response,
                    "final": final_response,
                }
            except Exception as e:
                last_error = e
                last_traceback = traceback.format_exc()
                if attempt < retry_count:
                    _log_info(f"任务 {task_index + 1} 第 {attempt + 1} 次失败，准备重试：{e}")
                    time.sleep(min(10, 2 + attempt * 2))

        return {
            "index": task_index,
            "ok": False,
            "prompt": prompt,
            "error": str(last_error),
            "traceback": last_traceback,
        }

    @staticmethod
    def _results_to_tensor(results, failure_strategy):
        ok_images = []
        for result in results:
            if result.get("ok"):
                ok_images.extend(result.get("images") or [])

        if not ok_images:
            return create_blank_tensor()

        base_size = ok_images[0].size if ok_images else (1024, 1024)
        tensors = []
        for result in results:
            if result.get("ok"):
                for image in result.get("images") or []:
                    if image.size != base_size:
                        image = image.resize(base_size)
                    tensors.append(pil2tensor(image))
            elif failure_strategy == "失败返回占位":
                tensors.append(create_blank_tensor(*base_size))

        return torch.cat(tensors, dim=0) if tensors else create_blank_tensor()

    def generate_concurrent(self, **kwargs):
        api_key = str(self._text_input_value(kwargs, "🔑 API密钥", "")).strip()
        model = self._text_input_value(kwargs, "🤖 模型", "全能图片G-2")
        channel = self._text_input_value(kwargs, "🏷️ 渠道", "官方稳定版")
        mode = self._text_input_value(kwargs, "🔀 模式", "文生图")
        prompt_text = kwargs.get("📝 提示词", "")
        if not self._split_prompt_lines(prompt_text):
            legacy_main_prompt = kwargs.get("📝 主提示词", "")
            legacy_batch_prompts = kwargs.get("🧾 批量提示词", "")
            prompt_text = legacy_batch_prompts if self._split_prompt_lines(legacy_batch_prompts) else legacy_main_prompt
        task_count = self._int_input_value(kwargs, "🔢 任务数量", 1)
        concurrency = self._int_input_value(kwargs, "🚀 并发数", 4)
        failure_strategy = self._text_input_value(kwargs, "🧪 失败策略", "跳过失败继续")
        retry_count = self._int_input_value(kwargs, "🛟 失败重试次数", 1)
        stream_receive = self._bool_input_value(kwargs, "🌊 流式接收", True)
        ratio = self._text_input_value(kwargs, "📐 画面比例", "模型默认")
        resolution = self._text_input_value(kwargs, "🧩 分辨率", "模型默认")
        quality = self._text_input_value(kwargs, "🎨 画质", "模型默认")
        cache_seed = self._int_input_value(kwargs, "🎲 随机种", 0)
        extra_params_str = self._text_input_value(kwargs, "📋 额外参数JSON", "{}")
        max_seconds = self._int_input_value(kwargs, "🔁 最大轮询秒数", 1200)
        interval = self._int_input_value(kwargs, "⏱️ 轮询间隔", 5)
        timeout = self._int_input_value(kwargs, "⌛ 请求超时", 60)

        prompt_lines = self._split_prompt_lines(prompt_text)
        prompt_line_count = len(prompt_lines)

        if not api_key:
            return (create_blank_tensor(), "", "❌ 错误：请填写 RunningHub API密钥。")
        if not prompt_lines:
            return (create_blank_tensor(), "", "❌ 错误：提示词不能为空。")

        config = ENDPOINT_CONFIGS.get((model, channel, mode))
        if not config:
            return (create_blank_tensor(), "", f"❌ 错误：当前组合没有可用端点：{model} / {channel} / {mode}")

        try:
            extra_params = json.loads(extra_params_str or "{}")
            if not isinstance(extra_params, dict):
                raise ValueError("额外参数JSON必须是 JSON 对象")
        except Exception as e:
            return (create_blank_tensor(), "", f"❌ 错误：额外参数JSON无效：{e}")

        task_count = max(1, min(100, task_count))
        multi_line_priority = prompt_line_count > 1
        prompt_input_connected = self._is_prompt_input_connected(kwargs)
        if multi_line_priority:
            prompts = prompt_lines[:100]
            quantity_source = "批量提示词列表/多行提示词优先"
        elif prompt_input_connected:
            prompts = [prompt_lines[0]]
            quantity_source = "上游连接输入单条执行"
        else:
            prompts = [prompt_lines[0]] * task_count
            quantity_source = "手动单行提示词按任务数量重复"

        image_inputs = None
        image_counts = []
        image_batch_count = 0
        if mode == "图生图":
            image_inputs = kwargs
            image_counts = self._image_input_counts(image_inputs)
            if not image_counts:
                return (create_blank_tensor(), "", "❌ 错误：选择图生图时，请至少接入一张参考图。")
            image_batch_count = max(count for _, count in image_counts)
            if image_batch_count > len(prompts):
                prompts = self._fit_prompt_count(prompts, min(100, image_batch_count))
                quantity_source = f"{quantity_source}；参考图批次补齐任务"

        task_count = len(prompts)
        concurrency = max(1, min(task_count, min(20, concurrency)))
        retry_count = max(0, min(5, retry_count))

        start_time = time.time()
        try:
            _log_info(f"开始多并发请求 RH：任务数量 {task_count}，并发数 {concurrency}，端点 {config['endpoint']}")

            results = [None] * task_count
            pbar = comfy.utils.ProgressBar(task_count) if comfy is not None else None
            completed = 0
            abort_error = None

            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                future_map = {
                    executor.submit(
                        self._run_one_task,
                        index,
                        prompts[index],
                        api_key,
                        config,
                        ratio,
                        resolution,
                        quality,
                        image_inputs,
                        extra_params,
                        max_seconds,
                        interval,
                        timeout,
                        retry_count,
                    ): index
                    for index in range(task_count)
                }

                for future in as_completed(future_map):
                    index = future_map[future]
                    try:
                        result = future.result()
                    except Exception as e:
                        result = {
                            "index": index,
                            "ok": False,
                            "prompt": prompts[index],
                            "error": str(e),
                            "traceback": traceback.format_exc(),
                        }
                    results[index] = result
                    completed += 1
                    if pbar:
                        if stream_receive and result.get("ok") and result.get("images"):
                            pbar.update_absolute(completed, preview=("PNG", result["images"][0], None))
                        else:
                            pbar.update_absolute(completed)
                    if not result.get("ok") and failure_strategy == "任一失败中断":
                        abort_error = result
                        for pending in future_map:
                            pending.cancel()
                        break

            results = [result for result in results if result is not None]
            if abort_error:
                message = f"❌ 错误：第 {abort_error['index'] + 1} 个 RH 并发任务失败，已按策略中断。\n\n详情：{abort_error.get('error')}"
                return (create_blank_tensor(), "", message)

            success_count = sum(1 for result in results if result.get("ok"))
            failed_count = len(results) - success_count
            final_tensor = self._results_to_tensor(results, failure_strategy)
            all_urls = []
            for result in results:
                if result.get("ok"):
                    all_urls.extend(result.get("urls") or [])

            elapsed_time = time.time() - start_time
            total_cost = 0.0
            has_cost = False
            for result in results:
                cost = result.get("cost")
                if cost is not None:
                    try:
                        total_cost += float(cost)
                        has_cost = True
                    except Exception:
                        pass

            info_lines = [
                "✅ RH 全能图片多并发任务完成",
                f"🤖 模型：{model}",
                f"🏷️ 渠道：{channel}",
                f"🔀 模式：{mode}",
                f"📡 端点：{config['endpoint']}",
                f"📝 提示词有效行数：{prompt_line_count}",
                f"🔢 实际任务数量：{task_count}",
                f"📌 数量来源：{quantity_source}",
                f"🚀 并发数：{concurrency}",
                f"🌊 流式接收：{'开启' if stream_receive else '关闭'}",
                f"🛟 失败重试次数：{retry_count}",
                f"🧪 失败策略：{failure_strategy}",
                f"✅ 成功任务：{success_count}",
                f"❌ 失败任务：{failed_count}",
                f"🖼️ 输出图片数：{final_tensor.shape[0]}",
                f"🧷 参考图批次数：{image_batch_count if mode == '图生图' else 0}",
                f"🎲 随机种：{cache_seed}（仅用于 ComfyUI 缓存控制）",
                f"⏱️ 总耗时：{elapsed_time:.2f} 秒",
            ]
            if image_counts:
                info_lines.append("🧷 图像输入数量：" + "，".join(f"{key}={count}" for key, count in image_counts))
            if has_cost:
                info_lines.append(f"💰 已返回任务总消耗：¥{total_cost:.4f}")

            info_lines.append("📋 任务明细：")
            for result in results:
                label = f"#{result['index'] + 1}"
                if result.get("ok"):
                    cost_text = f"，消耗 ¥{result.get('cost')}" if result.get("cost") is not None else ""
                    ref_text = f"，参考图 {result.get('reference_images', 0)} 张" if mode == "图生图" else ""
                    info_lines.append(f"{label} ✅ taskId={result.get('task_id')}，图片 {len(result.get('urls') or [])} 张{ref_text}，尝试 {result.get('attempts')} 次{cost_text}")
                else:
                    info_lines.append(f"{label} ❌ {result.get('error')}")

            info_lines.append("🔗 图片链接：")
            info_lines.extend(all_urls)

            raw_json = json.dumps(
                {
                    "results": [
                        {key: value for key, value in result.items() if key not in ("images",)}
                        for result in results
                    ]
                },
                ensure_ascii=False,
                indent=2,
            )
            return (final_tensor, "\n".join(all_urls), "\n".join(info_lines) + "\n\n" + raw_json)

        except Exception as e:
            error_msg = f"❌ 错误：RH 全能图片多并发生成失败\n\n详情：{e}"
            _log_error(error_msg)
            _log_error(traceback.format_exc())
            return (create_blank_tensor(), "", error_msg)


NODE_CLASS_MAPPINGS = {
    NODE_NAME: DapaoRHAllImageConcurrentNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    NODE_NAME: "🌈RH全能图片(多并发)@炮老师的小课堂",
}
