import requests
import json
import base64
import io
import torch
import numpy as np
from PIL import Image

# 图像转换工具函数
def tensor2pil(tensor):
    """将 tensor 转换为 PIL Image"""
    if tensor is None:
        return None
    
    # 确保 tensor 在 CPU 上
    tensor = tensor.cpu()
    
    # 处理不同的 tensor 形状
    if len(tensor.shape) == 3:  # [H, W, C]
        tensor = tensor.unsqueeze(0)
    
    batch_size = tensor.shape[0]
    images = []
    
    for i in range(batch_size):
        image = tensor[i].numpy()
        # 将值范围从 0-1 映射到 0-255
        image = (image * 255).astype(np.uint8)
        # 创建 PIL 图像
        images.append(Image.fromarray(image))
        
    return images

def pil_to_base64(image):
    """将 PIL Image 转换为 Base64 字符串"""
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

class DapaoEcommercePromptGenerator:
    """
    Dapao 详情页提示词生成器
    """
    
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "🌐 API地址": ("STRING", {
                    "default": "https://ai.t8star.cn/v1/chat/completions",
                    "multiline": False,
                    "tooltip": "OpenAI 兼容的 API 地址"
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "API Key (不会保存)"
                }),
                "🤖 模型名称": ("STRING", {
                    "default": "gemini-3-pro-preview",
                    "multiline": False,
                    "tooltip": "模型名称，需支持多模态"
                }),
                "⚡ 全自动随机优化": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "开启后，忽略手动填写的卖点和类型，由 AI 分析图片自动生成"
                }),
                "✨ 随机优化（增强文字排版）": ("BOOLEAN", {
                    "default": False,
                    "tooltip": "开启后，AI 将在提示词中增加关于排版布局、字体设计和文字视觉效果的创意指令"
                }),
                "🛍️ 产品类型": ("STRING", {
                    "default": "美妆粉底液",
                    "multiline": False,
                    "tooltip": "产品类型 (全自动模式下忽略)"
                }),
                "📝 核心卖点": ("STRING", {
                    "default": "遮瑕持久，水润服帖",
                    "multiline": True,
                    "tooltip": "核心卖点 (全自动模式下忽略)"
                }),
                "🎨 设计风格": ([
                    "简约 Ins 风", 
                    "高级奢华", 
                    "科技感", 
                    "清新自然",
                    "国潮风", 
                    "活泼撞色", 
                    "极简工业风", 
                    "梦幻唯美",
                    "亚马逊风格",
                    "赛博朋克",
                    "复古怀旧",
                    "日式和风",
                    "北欧极简",
                    "波普艺术",
                    "莫兰迪色系",
                    "暗黑哥特",
                    "未来主义",
                    "新中式",
                    "酸性设计",
                    "孟菲斯风格",
                    "Y2K千禧风"
                ], {"default": "简约 Ins 风"}),
                "🎬 场景偏好": ([
                    "混合（以使用场景为主）",
                    "生活方式交互",
                    "棚拍干净背景",
                    "户外自然光",
                    "室内温馨居家",
                    "商务办公环境",
                    "创意艺术布景",
                    "微距细节展示",
                    "动态运动抓拍",
                    "节日庆典氛围",
                    "极简纯色背景"
                ], {"default": "混合（以使用场景为主）"}),
                "🗣️ 输出语言": ([
                    "中文",
                    "英文",
                    "自动检测"
                ], {"default": "中文"}),
                "🎲 随机种子": ("INT", {
                    "default": 0, 
                    "min": 0, 
                    "max": 99999,
                    "tooltip": "随机种子"
                }),
                "🔢 生成数量": ("INT", {
                    "default": 10, 
                    "min": 1, 
                    "max": 20,
                    "tooltip": "生成的提示词数量"
                }),
            },
            "optional": {
                "🖼️ 参考图1": ("IMAGE",),
                "🖼️ 参考图2": ("IMAGE",),
                "🖼️ 参考图3": ("IMAGE",),
                "🖼️ 参考图4": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("📜 提示词列表", "🐞 调试信息")
    OUTPUT_IS_LIST = (True, False)
    FUNCTION = "generate_prompts"
    CATEGORY = "🤖dapaoAPI/其他工具搜集"

    def generate_prompts(self, **kwargs):
        # 映射中文参数名到变量
        api_url = kwargs.get("🌐 API地址", "").strip()
        api_key = kwargs.get("🔑 API密钥", "").strip()
        model_name = kwargs.get("🤖 模型名称", "").strip()
        auto_optimize = kwargs.get("⚡ 全自动随机优化", False)
        typography_optimize = kwargs.get("✨ 随机优化（增强文字排版）", False)
        product_type = kwargs.get("🛍️ 产品类型", "")
        selling_points = kwargs.get("📝 核心卖点", "")
        design_style = kwargs.get("🎨 设计风格", "")
        scene_preference = kwargs.get("🎬 场景偏好", "")
        output_language = kwargs.get("🗣️ 输出语言", "")
        seed = kwargs.get("🎲 随机种子", 0)
        prompt_count = kwargs.get("🔢 生成数量", 10)
        
        product_image = kwargs.get("🖼️ 参考图1")
        product_image_2 = kwargs.get("🖼️ 参考图2")
        product_image_3 = kwargs.get("🖼️ 参考图3")
        product_image_4 = kwargs.get("🖼️ 参考图4")
        
        # 1. 准备图像
        images = []
        for img in [product_image, product_image_2, product_image_3, product_image_4]:
            if img is not None:
                pil_imgs = tensor2pil(img)
                if pil_imgs:
                    images.append(pil_imgs[0]) # 取 batch 中的第一张
        
        # 2. 构建 Prompt
        system_prompt = """你是一个专业的电商视觉策划大师。你的任务是根据用户提供的产品信息和参考图，生成一系列用于AI绘画（如Midjourney/Stable Diffusion）的详细提示词，用于制作电商详情页。

请遵循以下规则：
1. **多图参考一致性**：如果提供了参考图，请仔细分析产品的主体特征（颜色、材质、形状），并在生成的提示词中保持主体一致性。
2. **场景构建**：根据`scene_preference`构建场景。
   - "生活方式交互"：侧重人物使用、生活场景。
   - "棚拍干净背景"：侧重纯色、简单几何背景、光影质感。
   - "混合"：结合以上两者，以展示产品优势为主。
3. **设计风格**：严格遵循`design_style`指定的视觉风格。
4. **输出格式（严格遵守）**：
   - 必须且仅输出一个纯 JSON 字符串列表 `["prompt 1", "prompt 2", ...]`。
   - **严禁**使用 Markdown 代码块标记（如 ```json 或 ```）。
   - **严禁**包含任何其他解释性文字、前缀或后缀。
   - 确保 JSON 格式合法，字符串内双引号需转义。
5. **语言**：根据`output_language`输出。如果选"自动检测"，则与卖点语言一致。
6. **数量**：必须生成 `prompt_count` 个提示词。

**输出示例**：
["提示词1内容...", "提示词2内容...", "提示词3内容..."]

**⚠️ 核心规则：卖点可视化（Visual Translation）**
用户提供的 `selling_points` 包含核心营销信息（如品牌名、Slogan、抽象卖点）。你**绝不能忽略**这些信息，必须将其转化为具体的视觉元素：
*   **品牌/文字信息**：如果卖点包含具体的品牌名或短语（如"大炮粉底"、"你最爱的粉底"），请尝试将其设计为画面中的 Logotype、包装文字、霓虹灯牌或杂志标题。
*   **抽象卖点转化**：将抽象形容词转化为物理特征。
    *   例如："水润" -> 画面出现水珠、液态飞溅、湿润的光泽感。
    *   例如："轻薄" -> 画面出现羽毛、漂浮感、透气织物。
    *   例如："遮瑕" -> 对比图构图、无瑕肌肤特写。
*   **请务必在 Prompt 中体现这些转化后的视觉细节。**
"""

        # 增加文字排版优化的指令
        typography_instruction = ""
        if typography_optimize:
            typography_instruction = f"""
**特别指令：增强文字排版优化**
请在生成的每个 Prompt 中，额外加入关于文字排版和视觉设计的创意描述。
你需要：
1. 设计具有视觉冲击力的标题排版（如：大胆的无衬线字体、优雅的衬线字体、手写体等，需符合设计风格）。
2. 描述文字与产品的空间关系（如：文字悬浮、环绕、穿插、留白）。
3. 强调版式设计感（如：杂志排版、海报风格、网格系统）。
4. 确保文字描述与`output_language`语言保持一致（如果是中文环境，描述中文排版美学）。
"""
        
        # 处理全自动模式
        if auto_optimize:
            user_text_base = f"""
请忽略用户提供的“产品类型”和“核心卖点”，改为完全根据提供的参考图进行智能分析。
你需要：
1. 自动识别图片中的产品类型、材质、颜色和特点。
2. 自动提炼出最吸引人的核心卖点（如质感、功能、适用场景）。
3. 结合用户指定的风格 `{design_style}` 和场景偏好 `{scene_preference}`。
4. 自动生成 `{prompt_count}` 个不同角度或场景的详情页提示词。
5. 保持输出语言为 `{output_language}`。

{typography_instruction}
"""
        else:
            user_text_base = f"""
产品类型：{product_type}
核心卖点：{selling_points}
设计风格：{design_style}
场景偏好：{scene_preference}
输出语言：{output_language}
生成数量：{prompt_count}

{typography_instruction}
"""

        user_content = []
        user_text = f"""
{user_text_base}

请生成 {prompt_count} 个详情页画面的提示词。
"""
        user_content.append({"type": "text", "text": user_text})

        # 添加图片到消息中
        for img in images:
            base64_img = pil_to_base64(img)
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_img}"
                }
            })

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        # 3. 调用 API
        if not api_url.endswith('/chat/completions'):
             # 简单的自动修正，如果用户只给了 host
            api_url = api_url.rstrip('/')
            if not api_url.endswith('/v1'):
                 # 有些用户可能直接给到 /v1，有些可能没有
                 pass 
            # 尝试智能拼接，但为了稳妥，这里假设用户填写的 api_url 是 base_url，如果不含 chat/completions 则补全
            # 但是标准 OpenAI SDK 传入的是 base_url，而 requests 往往需要完整 url
            # 按照常见习惯，如果结尾不是 chat/completions，尝试加上
            if 'chat/completions' not in api_url:
                if not api_url.endswith('/'):
                    api_url += '/'
                api_url += 'chat/completions'

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": model_name,
            "messages": messages,
            "temperature": 0.7,
            "seed": seed
        }

        try:
            response = requests.post(api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            
            content = result['choices'][0]['message']['content']
            
            # 4. 解析结果
            # 尝试提取 JSON 列表
            try:
                # 有时候模型会输出 markdown 代码块，需要去除
                clean_content = content.replace('```json', '').replace('```', '').strip()
                # 找到第一个 [ 和 最后一个 ]
                start = clean_content.find('[')
                end = clean_content.rfind(']')
                if start != -1 and end != -1:
                    json_str = clean_content[start:end+1]
                    prompts = json.loads(json_str)
                else:
                    # 如果找不到列表，尝试按行分割
                    prompts = [line for line in clean_content.split('\n') if line.strip()]
                    
                # 确保是列表
                if not isinstance(prompts, list):
                    prompts = [str(prompts)]
                
                # 确保数量（截断或填充）
                if len(prompts) > prompt_count:
                    prompts = prompts[:prompt_count]
                
                return (prompts, json.dumps(result, ensure_ascii=False, indent=2))

            except json.JSONDecodeError:
                # 解析失败，直接返回原始内容作为单条（或尝试分割）
                return ([content], f"JSON解析失败，原始返回:\n{content}")

        except Exception as e:
            error_msg = f"API调用出错: {str(e)}"
            if isinstance(e, requests.exceptions.HTTPError):
                if e.response.status_code == 401:
                    error_msg += "\n(401 Unauthorized: 请检查 API Key 是否正确，或者余额是否充足)"
                elif e.response.status_code == 404:
                    error_msg += "\n(404 Not Found: 请检查 API URL 是否正确)"
            
            debug_info = {
                "error": error_msg,
                "url": api_url,
                "headers": {k: v[:10] + "..." if k == "Authorization" else v for k, v in headers.items()},
                "payload_preview": str(payload)[:200] + "..."
            }
            return ([f"Error: {error_msg}"], json.dumps(debug_info, ensure_ascii=False, indent=2))

NODE_CLASS_MAPPINGS = {
    "DapaoEcommercePromptGenerator": DapaoEcommercePromptGenerator
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoEcommercePromptGenerator": "🦁详情页提示词@炮老师的小课堂"
}
