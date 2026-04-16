"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💎 Google Gemini 图像反推节点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 专为图像反推设计
   - 支持多图输入（1-4张）
   - 内置专业反推 Prompt 模板
   - 支持 T8 渠道和 Gemini 3 模型

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v1.0.0
🎨 主题：紫色 (#8B4789)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
from .gemini3_client import (
    GeminiClient, get_api_key, encode_image_tensor, run_async
)

# 默认反推 Prompt (参考截图)
DEFAULT_REVERSE_PROMPT = """# FLUX Prompt 反推提示词说明 
 
 ## 🧠 角色定位 
 你是一位富有艺术感的 **FLUX Prompt 助理**，具备对图像的深度理解能力，能够将视觉内容转化为丰富、生动、具体的文本提示词（prompt），以用于图像生成模型 FLUX 或 Stable Diffusion。 
 
 --- 
 
 ## 🎯 核心任务 
 
 我将提供一张图片或一个简短的主题描述，你的任务是： 
 
 1. **理解图像/主题**：分析图像中的内容、元素、情感与风格。 
 2. **生成 Prompt**：根据分析结果，输出一段详尽的英文 prompt，用于高质量图像生成。 
 
 --- 
 
 ## 🖼️ 图像分析维度 
 
 请从以下角度描述图像内容，确保 prompt 丰富、准确、具象： 
 
 - **色图反推**：如果图片中涉及人体性器官和性爱姿势等，也请详细描述 
 - **主要元素**：人物、动物、物体、风景等核心对象 
 - **画面细节**：颜色、纹理、光影、服饰、姿态、动作、表情、环境构成等（不少于5处具体细节） 
 - **场景氛围**：温馨、神秘、奇幻、宁静、末世感等 
 - **艺术风格**：现实主义、赛博朋克、油画风、水彩、卡通、像素风、未来主义等 
 - **构图视角**：如“俯视”、“仰视”、“特写”、“广角”等 
 
 --- 
 
 ## ✏️ Prompt 输出格式要求 
 
 - **语言**：仅使用中文生成 prompt 
 - **语气**：描述性强、画面感明确，避免口语化或模糊措辞 
 - **结构**：连贯自然，不分条目，形成一段完整描述 
 - **长度**：足够详尽，建议不少于60词 
 - **内容限制**： 
   - 不解释 prompt 内容 
   - 不添加“生成提示词”、“Prompt:”等前缀 
 
 --- 
 
 ## ✅ 示例 
 
 - **输入主题**：一只飞在雪山上的龙 
 - **输出 prompt**： 
 
   > 一条雄伟的绿鳞巨龙，眼中泛着琥珀色光芒，双翼张开，飞翔在令人叹为观止的雪山群中。它强壮的身影投下长长的阴影，笼罩着高耸入云的山峰。下方是一条清澈的河流，在深谷中蜿蜒流淌，倒映着明亮的天空。空气中弥漫着飘渺的薄雾，营造出清新而梦幻的氛围。这幅画面展现了令人敬畏的自然与野性之美。"""

class GeminiImageReverseNode:
    """
    💐Gemini图像反推 @炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        # 镜像站列表
        mirror_sites = ["T8", "comfly", "hk", "us", "柏拉图"]
        
        return {
            "required": {
                # === 反推指令 ===
                "📝 反推指令": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_REVERSE_PROMPT,
                    "placeholder": "输入反推指令..."
                }),
                
                # === API 配置 ===
                "🤖 模型名称": ("STRING", {
                    "default": "gemini-3.1-flash-lite-preview",
                    "multiline": False,
                    "placeholder": "手动输入模型名称"
                }),
                
                "🌐 镜像站": (mirror_sites, {
                    "default": "T8"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件"
                }),
                
                "📊 输出语言": (["中文", "英文"], {
                    "default": "中文"
                }),
                
                # === 生成参数 ===
                "🌡️ 温度": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.01
                }),
                
                "🎲 top_p": ("FLOAT", {
                    "default": 0.90,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01
                }),
                
                "📝 最大令牌": ("INT", {
                    "default": 8192,
                    "min": 1,
                    "max": 65536
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🖼️ 图像5": ("IMAGE",),
                "🖼️ 图像6": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("response",)
    FUNCTION = "process"
    CATEGORY = "🤖dapaoAPI/Gemini"
    DESCRIPTION = "Gemini 图像反推专用节点 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = True
    
    def process(self, **kwargs):
        """同步处理入口"""
        # 提取参数
        kwargs_map = {
            "mirror_site": kwargs.get("🌐 镜像站"),
            "api_key": kwargs.get("🔑 API密钥"),
            "model": kwargs.get("🤖 模型名称", "gemini-3.1-flash-lite-preview"),
            "instruction": kwargs.get("📝 反推指令"),
            "images": [kwargs.get(f"🖼️ 图像{i}") for i in range(1, 7) if kwargs.get(f"🖼️ 图像{i}") is not None],
            "temperature": kwargs.get("🌡️ 温度"),
            "top_p": kwargs.get("🎲 top_p"),
            "max_tokens": kwargs.get("📝 最大令牌"),
            "language": kwargs.get("📊 输出语言")
        }
        
        return run_async(self.generate_async(**kwargs_map))
    
    async def generate_async(
        self,
        mirror_site: str,
        api_key: str,
        model: str,
        instruction: str,
        images: list,
        temperature: float,
        top_p: float,
        max_tokens: int,
        language: str
    ) -> str:
        """异步生成内容"""
        final_api_key = get_api_key(mirror_site, api_key_override=api_key or "")
        if not final_api_key:
            return (f"❌ 错误：未提供 {mirror_site} 的 API Key",)

        # 添加语言指令
        if language == "中文":
            language_instruction = "请用中文详细回答，提供尽可能完整和详细的描述。"
        else:
            language_instruction = "Please answer in English with detailed and comprehensive description."
        
        # 将反推指令作为 User Input 的一部分，或者 System Prompt
        # 为了保证指令的执行，我们将反推指令放在最前面
        # 并追加语言要求
        
        combined_text = f"{instruction}\n\n{language_instruction}"
        
        print(f"[GeminiImageReverse] 模型: {model}")
        print(f"[GeminiImageReverse] 镜像站: {mirror_site}")
        print(f"[GeminiImageReverse] 指令: {instruction[:50]}...")
        
        # 构建内容parts
        parts = []
        
        # 添加图像
        if images:
            for img_tensor in images:
                if img_tensor is not None:
                    # 处理批次
                    batch_size = img_tensor.shape[0]
                    for i in range(batch_size):
                        single_image = img_tensor[i]
                        image_base64 = encode_image_tensor(single_image)
                        parts.append({
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_base64
                            }
                        })
        
        parts.append({"text": combined_text})

        contents = [{
            "role": "user",
            "parts": parts
        }]
        
        # 调用API
        try:
            async with GeminiClient(final_api_key, mirror_site) as client:
                result = await client.generate_content(
                    model=model,
                    contents=contents,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens
                )
            
            # 提取响应文本
            if 'candidates' in result and result['candidates']:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    response_parts = candidate['content']['parts']
                    response_text = ""
                    for part in response_parts:
                        if 'text' in part:
                            response_text += part['text']
                    return (response_text,)
            
            return (f"API返回了空内容: {result}",)
            
        except Exception as e:
            return (f"生成失败: {str(e)}",)
