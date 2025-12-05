import os
import json
import random
import requests
import base64
import re
from io import BytesIO
from PIL import Image
import torch
import numpy as np

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(CURRENT_DIR, 'banana2_config.json')

def get_config():
    """获取配置文件"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        return {}
    except Exception as e:
        print(f"[BananaIntegrated] 读取配置文件失败: {e}")
        return {}

def save_config(config):
    """保存配置文件 - 已禁用"""
    # print(f"[BananaIntegrated] 提示：配置文件保存功能已禁用，API密钥不会保存到本地")
    pass

def pil2tensor(image: Image.Image) -> torch.Tensor:
    """将PIL图像转换为ComfyUI tensor格式 [1, H, W, 3]"""
    if image.mode != 'RGB':
        image = image.convert('RGB')
    np_image = np.array(image).astype(np.float32) / 255.0
    tensor = torch.from_numpy(np_image)
    tensor = tensor.unsqueeze(0)
    return tensor

def tensor2pil(tensor: torch.Tensor) -> list:
    """将ComfyUI tensor转换为PIL图像列表"""
    if len(tensor.shape) == 4:
        return [Image.fromarray((t.cpu().numpy() * 255).astype(np.uint8)) for t in tensor]
    else:
        np_image = (tensor.cpu().numpy() * 255).astype(np.uint8)
        return [Image.fromarray(np_image)]

class BananaIntegratedNode:
    """
    🍌 banana官方/贞贞 整合版@炮老师的小课堂
    基于 TutuNanoBananaPro 修改，支持20张图片输入
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                # API提供商选择
                "🌐 API来源": (
                    ["Google官方", "T8Star"],
                    {"default": "Google官方"}
                ),
                
                # 提示词 - 从外部输入
                "🎨 提示词": ("STRING", {"forceInput": True, "multiline": True}),
                
                # 图像设置
                "📐 宽高比": (
                    ["1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
                    {"default": "1:1"}
                ),
                "📏 图像尺寸": (
                    ["1K", "2K", "4K"],
                    {"default": "2K"}
                ),
                
                # Google API密钥
                "🔑 Google API Key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入你的 Google API Key (选择Google官方时使用)"
                }),
                
                # T8Star API密钥
                "🔑 T8Star API Key": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "输入你的 T8Star API Key (选择T8Star时使用)"
                }),
                
                # 随机种子
                "🎲 随机种子": ("INT", {
                    "default": -1,
                    "min": -1,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子，-1为随机"
                }),
                
                # 种子控制
                "🎯 种子控制": (["随机", "固定", "递增"], {"default": "随机"}),
                
                # 超时设置
                "⏱️ 超时时间(秒)": ("INT", {
                    "default": 180,
                    "min": 10,
                    "max": 600,
                    "tooltip": "API请求超时时间，单位秒，默认180秒"
                }),
            },
            "optional": {
                # Google搜索增强 (仅Google官方支持)
                "🔍 启用Google搜索": ("BOOLEAN", {
                    "default": False,
                    "label_on": "启用搜索增强",
                    "label_off": "关闭搜索增强"
                }),
                # 20个图片输入端口
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                "🖼️ 图像5": ("IMAGE",),
                "🖼️ 图像6": ("IMAGE",),
                "🖼️ 图像7": ("IMAGE",),
                "🖼️ 图像8": ("IMAGE",),
                "🖼️ 图像9": ("IMAGE",),
                "🖼️ 图像10": ("IMAGE",),
                "🖼️ 图像11": ("IMAGE",),
                "🖼️ 图像12": ("IMAGE",),
                "🖼️ 图像13": ("IMAGE",),
                "🖼️ 图像14": ("IMAGE",),
                "🖼️ 图像15": ("IMAGE",),
                "🖼️ 图像16": ("IMAGE",),
                "🖼️ 图像17": ("IMAGE",),
                "🖼️ 图像18": ("IMAGE",),
                "🖼️ 图像19": ("IMAGE",),
                "🖼️ 图像20": ("IMAGE",),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("generated_image", "response")
    FUNCTION = "generate"
    CATEGORY = "🤖dapaoAPI/Nano Banana 2"
    
    def __init__(self):
        # 不再从配置文件加载API密钥，确保安全性
        self.google_api_key = ''
        self.t8star_api_key = ''
        self.last_seed = -1
    
    def get_api_config(self, api_provider):
        """获取API配置"""
        if api_provider == "Google官方":
            return {
                "endpoint": "https://generativelanguage.googleapis.com/v1beta/models/gemini-3-pro-image-preview:generateContent",
                "model": "gemini-3-pro-image-preview",
                "provider": "google"
            }
        else:  # T8Star
            return {
                "endpoint": "https://ai.t8star.cn/v1/images/generations",
                "model": "nano-banana-2",
                "provider": "t8star"
            }
    
    def save_api_key(self, google_key=None, t8star_key=None):
        """仅更新内存中的API密钥，不保存到文件"""
        if google_key and google_key.strip():
            self.google_api_key = google_key.strip()
        if t8star_key and t8star_key.strip():
            self.t8star_api_key = t8star_key.strip()
    
    def add_random_variation(self, prompt, seed=0):
        """
        在提示词末尾添加隐藏的随机标识
        用户每次运行都会得到不同结果（抽卡功能）
        结合种子使用，确保可控的随机性
        """
        # 如果seed为0或-1，使用当前时间作为随机源
        if seed <= 0:
            random_id = random.randint(10000, 99999)
        else:
            # 基于seed生成确定性的随机数
            rng = random.Random(seed)
            random_id = rng.randint(10000, 99999)
        
        return f"{prompt} [variation-{random_id}]"
    
    def build_request_payload(self, prompt, input_images, enable_google_search, aspect_ratio, image_size, seed, provider):
        """构建API请求 - 根据provider选择格式"""
        if provider == "google":
            return self.build_google_payload(prompt, input_images, enable_google_search, aspect_ratio, image_size, seed)
        else:  # t8star
            return self.build_t8star_payload(prompt, input_images, aspect_ratio, image_size, seed)
    
    def build_google_payload(self, prompt, input_images, enable_google_search, aspect_ratio, image_size, seed):
        """构建谷歌官方 Gemini API 格式的请求"""
        # 添加随机变化因子
        varied_prompt = self.add_random_variation(prompt, seed)
        
        # 构建端口号到数组索引的映射
        port_to_array_map = {}  # 端口号 -> 数组索引
        array_idx = 0
        for port_idx, img in enumerate(input_images, 1):
            if img is not None:
                array_idx += 1
                port_to_array_map[port_idx] = array_idx
        
        # 自动转换提示词中的图片引用（端口号 -> 数组索引）
        # original_prompt = varied_prompt # Unused
        for port_num, array_num in port_to_array_map.items():
            # 替换各种可能的引用格式
            patterns = [
                (rf'图{port_num}(?![0-9])', f'图{array_num}'),  # 图2 -> 图1
                (rf'图片{port_num}(?![0-9])', f'图片{array_num}'),  # 图片2 -> 图片1
                (rf'第{port_num}张图', f'第{array_num}张图'),  # 第2张图 -> 第1张图
                (rf'第{port_num}个图', f'第{array_num}个图'),  # 第2个图 -> 第1个图
            ]
            for pattern, replacement in patterns:
                varied_prompt = re.sub(pattern, replacement, varied_prompt)
        
        # 构建 contents 数组（Google官方格式）
        parts = []
        
        # 添加所有输入图片 - 保持原始索引位置
        array_position = 0  # 追踪在API数组中的实际位置
        for i in range(len(input_images)):
            img_tensor = input_images[i]
            if img_tensor is not None:
                # 转换为PIL图片
                pil_image = tensor2pil(img_tensor)[0]
                
                # 转换为base64
                buffered = BytesIO()
                pil_image.save(buffered, format="PNG", optimize=True, quality=95)
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # 添加图片到parts
                parts.append({
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": img_base64
                    }
                })
                
                # 输出时显示真实的图片编号（i+1 对应 🖼️ 图像1 到 🖼️ 图像20）
                array_position += 1
                print(f"[BananaIntegrated] 已添加输入端口 {i+1} 的图片, Base64大小: {len(img_base64)} 字符")
        
        # 添加文本提示词
        parts.append({
            "text": varied_prompt
        })
        
        # 构建完整的payload
        payload = {
            "contents": [{
                "parts": parts
            }],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "imageConfig": {
                    "aspectRatio": aspect_ratio,
                    "imageSize": image_size
                }
            }
        }
        
        # 如果启用搜索增强，添加tools
        if enable_google_search:
            payload["tools"] = [{"google_search": {}}]
            print(f"[BananaIntegrated] 已启用Google搜索增强")
        
        print(f"[BananaIntegrated] 图像配置: {aspect_ratio} @ {image_size}")
        print(f"[BananaIntegrated] 输入图片数: {len([img for img in input_images if img is not None])}")
        
        # 添加图片索引映射提示
        if array_position > 0:
            print(f"[BananaIntegrated] 🔍 自动映射转换（端口号 → API数组索引）:")
            for port_num, array_num in port_to_array_map.items():
                print(f"[BananaIntegrated]    - 图{port_num} → 图{array_num} (端口{port_num} → API第{array_num}张)")
        
        return payload
    
    def build_t8star_payload(self, prompt, input_images, aspect_ratio, image_size, seed):
        """构建T8Star API格式的请求 (OpenAI Dall-e 格式)"""
        # 添加随机变化因子
        varied_prompt = self.add_random_variation(prompt, seed)
        
        # 构建端口号到数组索引的映射
        port_to_array_map = {}  # 端口号 -> 数组索引
        array_idx = 0
        for port_idx, img in enumerate(input_images, 1):
            if img is not None:
                array_idx += 1
                port_to_array_map[port_idx] = array_idx
        
        # 自动转换提示词中的图片引用（端口号 -> 数组索引）
        # original_prompt = varied_prompt # Unused
        for port_num, array_num in port_to_array_map.items():
            # 替换各种可能的引用格式
            patterns = [
                (rf'图{port_num}(?![0-9])', f'图{array_num}'),  # 图2 -> 图1
                (rf'图片{port_num}(?![0-9])', f'图片{array_num}'),  # 图片2 -> 图片1
                (rf'第{port_num}张图', f'第{array_num}张图'),  # 第2张图 -> 第1张图
                (rf'第{port_num}个图', f'第{array_num}个图'),  # 第2个图 -> 第1个图
            ]
            for pattern, replacement in patterns:
                varied_prompt = re.sub(pattern, replacement, varied_prompt)
        
        # 构建payload - T8Star固定使用 nano-banana-2 (香蕉2/gemini-3-pro-image-preview)
        payload = {
            "model": "nano-banana-2",
            "prompt": varied_prompt,
            "aspect_ratio": aspect_ratio,
            "image_size": image_size,
            "response_format": "url"  # 使用URL格式返回
        }
        
        # 添加参考图片（如果有）
        image_array = []
        for i in range(len(input_images)):
            img_tensor = input_images[i]
            if img_tensor is not None:
                # 转换为PIL图片
                pil_image = tensor2pil(img_tensor)[0]
                
                # 转换为base64
                buffered = BytesIO()
                pil_image.save(buffered, format="PNG", optimize=True, quality=95)
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                # T8Star使用data URI格式
                data_uri = f"data:image/png;base64,{img_base64}"
                image_array.append(data_uri)
                
                print(f"[BananaIntegrated] 已添加输入端口 {i+1} 的图片, Base64大小: {len(img_base64)} 字符")
        
        if image_array:
            payload["image"] = image_array
        
        print(f"[BananaIntegrated] 图像配置: {aspect_ratio} @ {image_size}")
        print(f"[BananaIntegrated] 输入图片数: {len(image_array)}")
        
        # 添加图片索引映射提示
        if image_array:
            print(f"[BananaIntegrated] 🔍 自动映射转换（端口号 → API数组索引）:")
            for port_num, array_num in port_to_array_map.items():
                print(f"[BananaIntegrated]    - 图{port_num} → 图{array_num} (端口{port_num} → API第{array_num}张)")
        
        return payload
    
    def parse_response(self, response_json, provider):
        """解析API响应 - 根据provider选择格式"""
        if provider == "google":
            return self.parse_google_response(response_json)
        else:  # t8star
            return self.parse_t8star_response(response_json)
    
    def parse_google_response(self, response_json):
        """
        解析谷歌官方 Gemini API 响应
        """
        try:
            if "candidates" not in response_json or not response_json["candidates"]:
                raise Exception("响应中没有candidates数据")
            
            candidate = response_json["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                raise Exception("响应格式错误")
            
            parts = candidate["content"]["parts"]
            images = []
            text_parts = []
            
            for part in parts:
                # 跳过thought部分
                if part.get("thought", False):
                    continue
                    
                if "inlineData" in part:
                    # 图片数据
                    inline_data = part["inlineData"]
                    if "data" in inline_data:
                        # Base64格式
                        image_url = f"data:{inline_data.get('mimeType', 'image/png')};base64,{inline_data['data']}"
                        images.append(image_url)
                elif "text" in part:
                    # 文本数据
                    text_parts.append(part["text"])
            
            print(f"[BananaIntegrated] 解析到 {len(images)} 张图片, {len(text_parts)} 段文本")
            
            return {
                'images': images,
                'text': '\n'.join(text_parts),
                'success': len(images) > 0
            }
            
        except Exception as e:
            print(f"[BananaIntegrated] 响应解析错误: {str(e)}")
            print(f"[BananaIntegrated] 响应内容: {json.dumps(response_json, indent=2, ensure_ascii=False)[:500]}")
            raise Exception(f"响应解析失败: {str(e)}")
    
    def parse_t8star_response(self, response_json):
        """
        解析T8Star API响应 (OpenAI Dall-e 格式)
        """
        try:
            if "data" not in response_json:
                raise Exception("响应中没有data字段")
            
            images = []
            for item in response_json["data"]:
                if "url" in item:
                    images.append(item["url"])
                elif "b64_json" in item:
                    # 如果返回base64格式
                    image_url = f"data:image/png;base64,{item['b64_json']}"
                    images.append(image_url)
            
            print(f"[BananaIntegrated] 解析到 {len(images)} 张图片")
            
            return {
                'images': images,
                'text': '',  # T8Star不返回文本
                'success': len(images) > 0
            }
            
        except Exception as e:
            print(f"[BananaIntegrated] 响应解析错误: {str(e)}")
            print(f"[BananaIntegrated] 响应内容: {json.dumps(response_json, indent=2, ensure_ascii=False)[:500]}")
            raise Exception(f"响应解析失败: {str(e)}")
    
    def decode_image(self, image_url):
        """下载或解码图片"""
        try:
            if image_url.startswith('data:image/'):
                # Base64图片
                base64_data = image_url.split(',', 1)[1]
                image_data = base64.b64decode(base64_data)
                pil_image = Image.open(BytesIO(image_data))
            else:
                # HTTP URL图片 - 使用独立session避免代理连接复用问题
                session = requests.Session()
                session.trust_env = True
                try:
                    response = session.get(image_url, timeout=60)
                    response.raise_for_status()
                    pil_image = Image.open(BytesIO(response.content))
                finally:
                    session.close()
            
            # 转换为RGB模式
            if pil_image.mode != 'RGB':
                pil_image = pil_image.convert('RGB')
            
            print(f"[BananaIntegrated] 图片解码成功: {pil_image.size}")
            return pil2tensor(pil_image)
            
        except Exception as e:
            print(f"[BananaIntegrated] 图片解码失败: {str(e)}")
            raise
    
    def create_default_image(self, aspect_ratio, image_size):
        """创建默认占位图"""
        # 宽高比映射
        ratio_map = {
            "1:1": (1, 1), "2:3": (2, 3), "3:2": (3, 2),
            "3:4": (3, 4), "4:3": (4, 3), "4:5": (4, 5),
            "5:4": (5, 4), "9:16": (9, 16), "16:9": (16, 9),
            "21:9": (21, 9)
        }
        
        # 分辨率映射
        size_map = {"1K": 1024, "2K": 2048, "4K": 4096}
        
        w_ratio, h_ratio = ratio_map.get(aspect_ratio, (1, 1))
        base_size = size_map.get(image_size, 1024)
        
        # 计算实际尺寸
        if w_ratio >= h_ratio:
            width = base_size
            height = int(base_size * h_ratio / w_ratio)
        else:
            height = base_size
            width = int(base_size * w_ratio / h_ratio)
        
        # 创建白色图片
        img = Image.new('RGB', (width, height), color='white')
        return pil2tensor(img)
    
    def generate(self, **kwargs):
        """
        主处理函数 - 支持多种API提供商
        使用kwargs接收参数，兼容参数重命名
        """
        # 提取参数
        api_provider = kwargs.get("🌐 API来源", "Google官方")
        prompt = kwargs.get("🎨 提示词", "")
        aspect_ratio = kwargs.get("📐 宽高比", "1:1")
        image_size = kwargs.get("📏 图像尺寸", "2K")
        google_api_key = kwargs.get("🔑 Google API Key", "")
        t8star_api_key = kwargs.get("🔑 T8Star API Key", "")
        
        seed = kwargs.get("🎲 随机种子", -1)
        seed_control = kwargs.get("🎯 种子控制", "随机")
        timeout = kwargs.get("⏱️ 超时时间(秒)", 180)
        
        enable_google_search = kwargs.get("🔍 启用Google搜索", False)
        
        # 收集所有输入的图片
        input_images = []
        for i in range(1, 21):
            # 尝试获取两种可能的参数名（中文带表情 或 英文旧名称）
            img = kwargs.get(f"🖼️ 图像{i}")
            if img is None:
                img = kwargs.get(f"input_image_{i}")
            input_images.append(img)

        # 统计有效图片数量
        valid_image_count = len([img for img in input_images if img is not None])
        if valid_image_count > 0:
            print(f"[BananaIntegrated] 📸 检测到 {valid_image_count} 张输入图片，已自动切换为【图像编辑/多模态】模式")
        else:
            print(f"[BananaIntegrated] 📝 未检测到输入图片，使用【文生图】模式")
        
        # 处理种子逻辑
        if seed_control == "固定":
            effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
        elif seed_control == "随机":
            effective_seed = random.randint(0, 2147483647)
        elif seed_control == "递增":
            if self.last_seed == -1:
                effective_seed = seed if seed != -1 else random.randint(0, 2147483647)
            else:
                effective_seed = self.last_seed + 1
        else:
            effective_seed = random.randint(0, 2147483647)
        
        # 更新 last_seed
        self.last_seed = effective_seed
        print(f"[BananaIntegrated] 🎲 种子模式: {seed_control}, 使用种子: {effective_seed}")
        
        # 更新并保存API密钥
        self.save_api_key(google_api_key, t8star_api_key)
        
        # 获取API配置
        api_config = self.get_api_config(api_provider)
        
        # 检查API密钥
        if api_provider == "Google官方" and not self.google_api_key:
            return (self.create_default_image(aspect_ratio, image_size), "❌ 错误: 请提供 Google API Key")
        elif api_provider == "T8Star" and not self.t8star_api_key:
            return (self.create_default_image(aspect_ratio, image_size), "❌ 错误: 请提供 T8Star API Key")
        
        try:
            # 构建请求
            payload = self.build_request_payload(
                prompt, input_images, enable_google_search, aspect_ratio, image_size, effective_seed, api_config["provider"]
            )
            
            # 发送请求
            headers = {"Content-Type": "application/json"}
            if api_provider == "T8Star":
                headers["Authorization"] = f"Bearer {self.t8star_api_key}"
            
            url = api_config["endpoint"]
            if api_provider == "Google官方":
                url = f"{url}?key={self.google_api_key}"
            
            print(f"[BananaIntegrated] 正在发送请求到 {api_provider}...")
            # 使用用户设置的超时时间
            response = requests.post(url, headers=headers, json=payload, timeout=timeout)
            
            # 检查响应状态
            if response.status_code != 200:
                error_msg = f"API请求失败: {response.status_code} - {response.text}"
                print(f"[BananaIntegrated] {error_msg}")
                return (self.create_default_image(aspect_ratio, image_size), error_msg)
            
            # 解析响应
            result = self.parse_response(response.json(), api_config["provider"])
            
            if result['success']:
                # 解码第一张图片（如果有）
                output_image = self.decode_image(result['images'][0])
                return (output_image, result['text'] if result['text'] else "图片生成成功")
            else:
                return (self.create_default_image(aspect_ratio, image_size), "API未返回图片")
                
        except Exception as e:
            error_msg = f"处理过程中发生错误: {str(e)}"
            print(f"[BananaIntegrated] {error_msg}")
            return (self.create_default_image(aspect_ratio, image_size), error_msg)

# 节点映射
NODE_CLASS_MAPPINGS = {
    "BananaIntegratedNode": BananaIntegratedNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BananaIntegratedNode": "🍌 banana官方/贞贞 整合版@炮老师的小课堂"
}
