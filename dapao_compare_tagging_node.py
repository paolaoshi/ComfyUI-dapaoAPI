"""
🤖 Dapao Compare Tagging Node
功能：对比两张图片（原图 vs 结果图），调用视觉大模型 API 生成高质量描述。
支持：单图/批次张量输入，或直接读取文件夹进行批量处理并保存为TXT。
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

# 默认系统指令
DEFAULT_SYSTEM_PROMPT = """角色设定： 
 你是一位拥有像素级观察力的“计算机视觉数据标注专家”。你擅长分析成对的图像数据（Source Image vs Target Image），并能用极其精炼、准确的自然语言描述从“原图”到“结果图”的视觉转化过程及结果图中的所有细节元素。 
 
 核心任务目标： 
 对比输入的【图1（原图）】和【图2（AI生成图）】，生成一段高质量的图像描述（Prompt/Caption）。描述必须涵盖：风格转换类型、主体人物变化、以及图2中新增的所有视觉元素（如表情集、服装分解、物品陈列等）。 
 
 行为约束与规则： 
 
 零废话原则： 严禁输出任何开场白（如“好的，分析如下”、“这两张图的变化是”）、结束语或解释性文字。直接输出描述内容。 
 结构化描述： 描述逻辑应遵循：主转换动作（风格+主体） -> 详细布局分解（表情、服装、物品） -> 微观细节（材质、特写）。 
 精准动词： 使用“将...转换为...”、“详细分解...”、“展示...”、“拆解...”、“列出...”、“特写...”等强导向性动词。 
 视觉锚定： 只描述图2中实际存在的元素。如果图2把图1的某个模糊部分画清楚了（如包里的东西），必须详细列出。 
 分隔符： 不同的描述维度之间用分号（；）隔开，保持句子紧凑。 
 输入处理逻辑： 
 
 输入： [图片1], [图片2] 
 分析： 
 识别图1的主体（真人/照片）。 
 识别图2的风格（卡通/插画/3D等）。 
 扫描图2的布局，识别是否有“表情列表”、“服装拆解图”、“物品平铺”等特殊区域。 
 提取图2中的文字标签（如果有）或视觉物体名称。 
 输出格式要求： 
 纯文本段落。无Markdown标题，无列表符号。 
 
 语气和风格： 
 客观、描述性、高密度、指令化。"""

class DapaoCompareTaggingNode:
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
                
                # --- 新增：文件夹处理模式 ---
                "📂 A文件夹(原始图)": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "A文件夹(原始图) 路径 - 为空则使用下方Image连接"
                }),
                "📂 B文件夹(结果图)": ("STRING", {
                    "default": "", 
                    "multiline": False, 
                    "placeholder": "B文件夹(结果图) 路径 - 为空则使用下方Image连接"
                }),
                "📍 输出位置": (["默认(B文件夹)", "自定义输出文件夹"],),
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
                    "default": "请分析这两张图片，生成对比描述。",
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
                # 改为 Optional，支持纯文件夹模式
                "🖼️ 图像1(原始图)": ("IMAGE",),
                "🖼️ 图像2(结果图)": ("IMAGE",),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("📝 描述内容",)
    OUTPUT_IS_LIST = (True,) 
    FUNCTION = "compare_images"
    CATEGORY = "🤖dapaoAPI/其他工具搜集"

    def image_to_base64(self, img_input):
        """通用转Base64: 支持 Tensor 和 PIL.Image"""
        
        # 1. 如果是 Tensor [B, H, W, C] -> 转 PIL
        if isinstance(img_input, torch.Tensor):
            # 处理 Batch，只取第一张 [B, H, W, C] -> [H, W, C]
            if len(img_input.shape) == 4:
                img_input = img_input[0]
            elif len(img_input.shape) == 3:
                pass
            
            i = 255. * img_input.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        
        # 2. 如果已经是 PIL Image
        elif isinstance(img_input, Image.Image):
            img = img_input
            # 确保转为 RGB
            if img.mode != "RGB":
                img = img.convert("RGB")
        else:
            raise ValueError(f"Unsupported image type: {type(img_input)}")

        # 3. 转 Base64
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{img_str}"

    def call_api(self, img1_b64, img2_b64, api_url, api_key, model, system_prompt, user_prompt, timeout, seed):
        # 构造请求 Headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        # 构造请求 Payload
        messages = [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": user_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img1_b64
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": img2_b64
                        }
                    }
                ]
            }
        ]

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 4096,
        }

        if seed != -1:
            # 确保 seed 不超过 32 位整数上限
            payload["seed"] = seed % 2147483647

        # 发送请求
        try:
            print(f"Generating description with model: {model}...")
            response = requests.post(
                api_url, 
                headers=headers, 
                json=payload, 
                timeout=timeout
            )
            
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

    def save_text_file(self, content, filename, folder_b_path, output_location, custom_output_folder):
        """保存文本到文件"""
        try:
            # 确定保存目录
            if output_location == "自定义输出文件夹":
                if not custom_output_folder:
                    print("⚠️ Custom output folder is empty, falling back to Folder B.")
                    save_dir = Path(folder_b_path)
                else:
                    save_dir = Path(custom_output_folder)
            else:
                save_dir = Path(folder_b_path)
            
            # 创建目录
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # 确定文件名 (与原图同名，后缀改为.txt)
            txt_path = save_dir / f"{Path(filename).stem}.txt"
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(content)
                
            print(f"✅ Saved text to: {txt_path}")
            
        except Exception as e:
            print(f"❌ Error saving text file: {e}")

    def compare_images(self, **kwargs):
        # 提取参数 (兼容中文 Key)
        api_url = kwargs.get("🌐 API地址")
        api_key = kwargs.get("🔑 API密钥")
        model = kwargs.get("🤖 模型名称")
        folder_path_a = kwargs.get("📂 A文件夹(原始图)")
        folder_path_b = kwargs.get("📂 B文件夹(结果图)")
        output_location = kwargs.get("📍 输出位置")
        custom_output_folder = kwargs.get("📂 自定义输出文件夹")
        system_prompt = kwargs.get("🧠 系统指令(System Prompt)")
        user_prompt = kwargs.get("🗣️ 用户指令(User Prompt)")
        timeout = kwargs.get("⏱️ 超时时间(秒)")
        seed = kwargs.get("🎲 随机种子")
        image_1 = kwargs.get("🖼️ 图像1(原始图)")
        image_2 = kwargs.get("🖼️ 图像2(结果图)")

        results = []
        
        # --- 模式 1: 文件夹批处理模式 ---
        if folder_path_a and folder_path_b:
            print(f"📂 Running in Folder Batch Mode...")
            
            imgs_a = self.get_valid_images(folder_path_a)
            imgs_b = self.get_valid_images(folder_path_b)
            
            if not imgs_a:
                raise ValueError(f"No images found in Folder A: {folder_path_a}")
            
            # 建立文件名索引
            map_a = {p.stem: p for p in imgs_a}
            map_b = {p.stem: p for p in imgs_b}
            
            # 找出交集 (按文件名匹配)
            common_names = sorted(list(set(map_a.keys()) & set(map_b.keys())))
            
            # 如果没有找到匹配的文件名，尝试按顺序配对 (降级策略)
            if not common_names:
                print("⚠️ Warning: No matching filenames found! Falling back to sequential pairing (using Folder B names for output).")
                
                count = min(len(imgs_a), len(imgs_b))
                if count == 0:
                     raise ValueError("One of the folders is empty!")
                     
                print(f"🔄 Sequential Mode: Processing {count} pairs...")
                
                for i in range(count):
                    path_a = imgs_a[i]
                    path_b = imgs_b[i]
                    
                    try:
                        # 加载图片
                        pil_a = Image.open(path_a)
                        pil_b = Image.open(path_b)
                        
                        # 转 Base64
                        b64_a = self.image_to_base64(pil_a)
                        b64_b = self.image_to_base64(pil_b)
                        
                        # 调用 API
                        content = self.call_api(
                            b64_a, b64_b, api_url, api_key, model,
                            system_prompt, user_prompt, timeout, seed
                        )
                        
                        results.append(content)
                        
                        # 保存文件 (使用 B 文件夹的文件名)
                        self.save_text_file(content, path_b.name, folder_path_b, output_location, custom_output_folder)
                        
                    except Exception as e:
                        print(f"❌ Error processing sequential pair {i}: {e}")
                        results.append(f"Error: {e}")
                
                return (results,)

            print(f"Found {len(common_names)} matched image pairs.")
            
            for name in common_names:
                path_a = map_a[name]
                path_b = map_b[name]
                
                try:
                    # 加载图片
                    pil_a = Image.open(path_a)
                    pil_b = Image.open(path_b)
                    
                    # 转 Base64
                    b64_a = self.image_to_base64(pil_a)
                    b64_b = self.image_to_base64(pil_b)
                    
                    # 调用 API
                    content = self.call_api(
                        b64_a, b64_b, api_url, api_key, model,
                        system_prompt, user_prompt, timeout, seed
                    )
                    
                    results.append(content)
                    
                    # 保存文件
                    self.save_text_file(content, path_b.name, folder_path_b, output_location, custom_output_folder)
                    
                except Exception as e:
                    print(f"❌ Error processing pair {name}: {e}")
                    results.append(f"Error: {e}")

        # --- 模式 2: 传统连线模式 ---
        elif image_1 is not None and image_2 is not None:
            print(f"🔌 Running in Tensor Connection Mode...")
            
            # 确保输入是 Batch 格式 [B, H, W, C]
            if len(image_1.shape) == 3:
                image_1 = image_1.unsqueeze(0)
            if len(image_2.shape) == 3:
                image_2 = image_2.unsqueeze(0)
                
            batch_size_1 = image_1.shape[0]
            batch_size_2 = image_2.shape[0]
            
            if batch_size_1 == batch_size_2:
                count = batch_size_1
            elif batch_size_1 == 1:
                count = batch_size_2
            elif batch_size_2 == 1:
                count = batch_size_1
            else:
                error_msg = f"Batch Size Mismatch Error: Image1 has {batch_size_1}, Image2 has {batch_size_2}."
                raise ValueError(error_msg)

            for i in range(count):
                img1 = image_1[i if batch_size_1 > 1 else 0]
                img2 = image_2[i if batch_size_2 > 1 else 0]
                
                b64_a = self.image_to_base64(img1)
                b64_b = self.image_to_base64(img2)
                
                content = self.call_api(
                    b64_a, b64_b, api_url, api_key, model, 
                    system_prompt, user_prompt, timeout, seed
                )
                results.append(content)
                
                # 连线模式下，是否需要保存？
                # 如果用户指定了 Custom Output Folder，我们尝试保存，但没有文件名...
                # 这里暂时只保存到内存，因为没有文件名。如果用户需要保存，建议使用 Save Text 节点。
                if output_location == "自定义输出文件夹" and custom_output_folder:
                     # 生成一个时间戳文件名
                     import time
                     timestamp = int(time.time() * 1000)
                     filename = f"batch_{i}_{timestamp}.png" # 假名用于传递
                     self.save_text_file(content, filename, "", output_location, custom_output_folder)

        else:
            raise ValueError("Invalid Input: Please provide either (Folder A + Folder B) OR connect (Image 1 + Image 2).")
            
        return (results,)

# 注册节点
NODE_CLASS_MAPPINGS = {
    "DapaoCompareTaggingNode": DapaoCompareTaggingNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoCompareTaggingNode": "🍭大炮-API对比打标@炮老师的小课堂"
}
