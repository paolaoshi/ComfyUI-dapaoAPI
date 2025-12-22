"""
🤖 Dapao API Batch Reverse Tagging Node
功能：批量接收图片（文件夹或多图输入），调用视觉大模型 API 进行反推打标。
支持：单图/批次/列表输入，结果保存为TXT。
作者：@炮老师的小课堂
"""

import requests
import json
import torch
import numpy as np
from PIL import Image
import io
import base64
import server
import os
from pathlib import Path
import time

# 默认系统指令
DEFAULT_SYSTEM_PROMPT = """## 🧠 角色定位 
 你是一位富有艺术感的 **图像反推 助理**，具备对图像的深度理解能力，能够将视觉内容转化为丰富、生动、具体的文本提示词（prompt），以用于图像生成模型 FLUX 或 Stable Diffusion。 
 
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
   - 不添加“生成提示词”、“Prompt:”等前缀"""

DEFAULT_SYSTEM_PROMPT_EN = """## 🧠 Role Definition
You are an artistic **Image Reverse Prompting Assistant** with a deep understanding of images. You can translate visual content into rich, vivid, and specific text prompts for image generation models like FLUX or Stable Diffusion.

---

## 🎯 Core Task
I will provide an image or a brief theme description. Your task is to:

1. **Understand the Image/Theme**: Analyze the content, elements, emotions, and style in the image.
2. **Generate Prompt**: Based on the analysis, output a detailed **ENGLISH** prompt for high-quality image generation.

---

## 🖼️ Image Analysis Dimensions
Please describe the image content from the following perspectives, ensuring the prompt is rich, accurate, and concrete:

- **NSFW Content**: If the image involves nudity, sexual organs, or sexual poses, please describe them in detail.
- **Main Elements**: Core objects like characters, animals, objects, landscapes, etc.
- **Visual Details**: Colors, textures, lighting, clothing, poses, actions, expressions, environment composition, etc. (at least 5 specific details).
- **Atmosphere**: Warm, mysterious, fantasy, quiet, post-apocalyptic, etc.
- **Art Style**: Realism, cyberpunk, oil painting, watercolor, cartoon, pixel art, futurism, etc.
- **Composition**: e.g., "Top-down view", "Low angle", "Close-up", "Wide angle", etc.

---

## ✏️ Prompt Output Format Requirements

- **Language**: **ENGLISH ONLY**.
- **Tone**: Highly descriptive, clear imagery, avoid colloquialisms or vague wording.
- **Structure**: Coherent and natural, no bullet points, form a complete description paragraph.
- **Length**: Sufficiently detailed, recommended not less than 60 words.
- **Content Limits**:
  - Do not explain the prompt content.
  - Do not add prefixes like "Generate Prompt", "Prompt:", etc.
"""

class DapaoAPIBatchReverseNode:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "🌐 API地址": ("STRING", {
                    "default": "https://ai.t8star.cn/v1/chat/completions",
                    "multiline": False
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False
                }),
                "🤖 模型名称": ("STRING", {
                    "default": "gemini-3-pro-preview",
                    "multiline": False
                }),
                "🌐 输出语言": (["中文", "英文"], {"default": "中文"}),
                
                # --- 文件夹处理模式 ---
                "📂 输入文件夹": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "输入文件夹路径 - 为空则使用下方Image连接"
                }),
                "📍 输出位置": (["默认(输入文件夹)", "自定义输出文件夹"],),
                "📂 自定义输出文件夹": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "自定义输出文件夹路径 (仅当选择自定义时生效)"
                }),
                # ---------------------------

                "🧠 系统指令(System Prompt)": ("STRING", {
                    "default": DEFAULT_SYSTEM_PROMPT,
                    "multiline": True,
                    "dynamicPrompts": False
                }),
                "🗣️ 用户指令(User Prompt)": ("STRING", {
                    "default": "请详细分析这张图片。",
                    "multiline": True,
                    "dynamicPrompts": False
                }),
                "⏱️ 超时时间(秒)": ("INT", {
                    "default": 120, 
                    "min": 1, 
                    "max": 600
                }),
                "🎲 随机种子": ("INT", {"default": -1, "min": -1, "max": 0xffffffffffffffff}),
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
    RETURN_NAMES = ("📝 描述列表",)
    OUTPUT_IS_LIST = (True,) 
    FUNCTION = "batch_reverse"
    CATEGORY = "🤖dapaoAPI/其他工具搜集"

    def image_to_base64(self, img_input):
        """通用转Base64: 支持 Tensor 和 PIL.Image"""
        if isinstance(img_input, torch.Tensor):
            # [B, H, W, C] -> PIL
            if len(img_input.shape) == 4:
                img_input = img_input[0]
            elif len(img_input.shape) == 3:
                pass
            
            i = 255. * img_input.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        elif isinstance(img_input, Image.Image):
            img = img_input
            if img.mode != "RGB":
                img = img.convert("RGB")
        else:
            raise ValueError(f"Unsupported image type: {type(img_input)}")

        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{img_str}"

    def call_api(self, img_b64, api_url, api_key, model, system_prompt, user_prompt, timeout, seed):
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": img_b64}}
            ]}
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 4096,
        }

        if seed != -1:
            payload["seed"] = seed % 2147483647

        try:
            print(f"Generating description with model: {model}...")
            response = requests.post(api_url, headers=headers, json=payload, timeout=timeout)
            response.raise_for_status()
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return f"Error: Unexpected response format. Response: {json.dumps(result)}"
        except requests.exceptions.RequestException as e:
            error_msg = f"API Request Error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f"\nResponse: {e.response.text}"
            print(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected Error: {str(e)}"
            print(error_msg)
            return error_msg

    def get_valid_images(self, folder_path):
        """获取文件夹内所有图片文件"""
        valid_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        path = Path(folder_path)
        if not path.exists():
            return []
        
        images = []
        for p in path.iterdir():
            if p.is_file() and p.suffix.lower() in valid_exts:
                images.append(p)
        return sorted(images)

    def save_text_file(self, content, filename, base_folder, output_location, custom_output_folder):
        """保存文本到文件"""
        try:
            if output_location == "自定义输出文件夹":
                if not custom_output_folder:
                    print("⚠️ Custom output folder is empty, falling back to base folder.")
                    save_dir = Path(base_folder)
                else:
                    save_dir = Path(custom_output_folder)
            else:
                save_dir = Path(base_folder)
            
            save_dir.mkdir(parents=True, exist_ok=True)
            txt_path = save_dir / f"{Path(filename).stem}.txt"
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Saved text to: {txt_path}")
        except Exception as e:
            print(f"❌ Error saving text file: {e}")

    def batch_reverse(self, **kwargs):
        # 提取参数
        api_url = kwargs.get("🌐 API地址")
        api_key = kwargs.get("🔑 API密钥")
        model = kwargs.get("🤖 模型名称")
        input_folder = kwargs.get("📂 输入文件夹")
        output_location = kwargs.get("📍 输出位置")
        custom_output_folder = kwargs.get("📂 自定义输出文件夹")
        system_prompt = kwargs.get("🧠 系统指令(System Prompt)")
        user_prompt = kwargs.get("🗣️ 用户指令(User Prompt)")
        timeout = kwargs.get("⏱️ 超时时间(秒)")
        seed = kwargs.get("🎲 随机种子")

        language = kwargs.get("🌐 输出语言")

        # --- 处理语言切换 ---
        if language == "英文":
            # 1. 检测是否使用了默认中文提示词，如果是，直接替换为英文版
            if system_prompt.strip() == DEFAULT_SYSTEM_PROMPT.strip():
                print("ℹ️ Detected default Chinese prompt with English mode selected. Switching to English prompt.")
                # 尝试使用全局定义的英文提示词，如果没有则现场生成作为回退
                if 'DEFAULT_SYSTEM_PROMPT_EN' in globals():
                    system_prompt = DEFAULT_SYSTEM_PROMPT_EN
                else:
                    print("⚠️ DEFAULT_SYSTEM_PROMPT_EN not found in globals, using fallback generation.")
                    system_prompt = DEFAULT_SYSTEM_PROMPT.replace("仅使用中文生成 prompt", "Use English to generate the prompt") + "\n\n**IMPORTANT: Please output the final prompt in ENGLISH.**"
            else:
                # 2. 如果是自定义提示词，尝试替换关键字并追加强力指令
                print("ℹ️ Custom prompt detected. Injecting English instructions.")
                system_prompt = system_prompt.replace("仅使用中文生成 prompt", "Use English to generate the prompt")
                system_prompt += "\n\n**CRITICAL INSTRUCTION: The user has requested the output in ENGLISH. Regardless of previous instructions, please translate the final result into English.**"
        else:
            # 中文模式: 如果没有包含中文强制指令，且不是默认提示词（默认提示词已经包含了），则追加
            if "仅使用中文生成 prompt" not in system_prompt and system_prompt.strip() != DEFAULT_SYSTEM_PROMPT.strip():
                 system_prompt += "\n\n**重要提示：请务必使用中文输出最终结果。**"

        results = []
        
        # --- 模式 1: 文件夹处理模式 ---
        if input_folder:
            print(f"📂 Running in Folder Batch Mode: {input_folder}")
            images = self.get_valid_images(input_folder)
            
            if not images:
                print(f"⚠️ No images found in: {input_folder}")
            else:
                print(f"Found {len(images)} images to process.")
                for img_path in images:
                    try:
                        pil_img = Image.open(img_path)
                        b64_img = self.image_to_base64(pil_img)
                        content = self.call_api(b64_img, api_url, api_key, model, system_prompt, user_prompt, timeout, seed)
                        results.append(content)
                        self.save_text_file(content, img_path.name, input_folder, output_location, custom_output_folder)
                    except Exception as e:
                        print(f"❌ Error processing {img_path.name}: {e}")
                        results.append(f"Error: {e}")

        # --- 模式 2: 图像接口输入 (1-6) ---
        # 收集所有输入的图像，支持 Batch 和 List
        input_images = []
        for i in range(1, 7):
            key = f"🖼️ 图像{i}"
            if key in kwargs and kwargs[key] is not None:
                img_val = kwargs[key]
                # 检查是单个 Tensor [B,H,W,C] 还是 List
                if isinstance(img_val, list):
                    for item in img_val:
                        input_images.append(item)
                elif isinstance(img_val, torch.Tensor):
                    # 如果是 Batch [B, H, W, C]，拆分成单张
                    for b in range(img_val.shape[0]):
                        input_images.append(img_val[b]) # 取出单张 Tensor
                else:
                    # 其他情况暂不处理或视为单张
                    pass

        if input_images:
            print(f"🔌 Processing {len(input_images)} images from inputs...")
            for idx, img_tensor in enumerate(input_images):
                try:
                    b64_img = self.image_to_base64(img_tensor)
                    content = self.call_api(b64_img, api_url, api_key, model, system_prompt, user_prompt, timeout, seed)
                    results.append(content)
                    
                    # 连线模式下的保存逻辑
                    if output_location == "自定义输出文件夹" and custom_output_folder:
                        timestamp = int(time.time() * 1000)
                        filename = f"reverse_{idx}_{timestamp}.png" # 假名用于传递
                        self.save_text_file(content, filename, "", output_location, custom_output_folder)
                except Exception as e:
                    print(f"❌ Error processing input image {idx}: {e}")
                    results.append(f"Error: {e}")

        if not results:
             print("⚠️ No images processed. Please provide an input folder or connect images.")
             # 为避免下游节点报错，返回空字符串列表
             results.append("")

        return (results,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "DapaoAPIBatchReverseNode": DapaoAPIBatchReverseNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoAPIBatchReverseNode": "🍭大炮-API批量反推@炮老师的小课堂"
}
