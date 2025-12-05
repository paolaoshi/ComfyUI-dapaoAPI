"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🍌 Google Nano Banana 2 多模态节点
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 功能说明：
   - 支持文本生成图像（Text-to-Image）
   - 支持多图编辑（最多4张图像输入）
   - 丰富的风格和质量控制选项
   - 专业的相机、光照、模板预设

🔧 技术特性：
   - 使用第三方API调用 Nano Banana 2 模型
   - 支持多镜像站点（comfly/hk/us）
   - 流式响应处理
   - 智能提示词增强

📚 参考项目：ComfyUI_LLM_Banana

👨‍🏫 作者：@炮老师的小课堂
📦 版本：v3.0.0
🎨 主题：橙棕色 (#773508)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

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
import comfy.utils

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BANANA2_CONFIG_FILE = os.path.join(CURRENT_DIR, 'banana2_config.json')

# 统一节点颜色 (橙棕色)
NODE_COLOR = "#773508"


# ==================== 辅助函数 ====================

def _log_info(message):
    """统一的日志输出函数"""
    print(f"[dapaoAPI-Banana2] 信息：{message}")


def _log_warning(message):
    """统一的警告输出函数"""
    print(f"[dapaoAPI-Banana2] 警告：{message}")


def _log_error(message):
    """统一的错误输出函数"""
    print(f"[dapaoAPI-Banana2] 错误：{message}")


def get_banana2_config():
    """读取配置文件"""
    default_config = {
        "api_key": "",
        "base_url": "https://api.gptbest.vip",
        "timeout": 300
    }
    
    try:
        if os.path.exists(BANANA2_CONFIG_FILE):
            with open(BANANA2_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            return default_config
    except Exception as e:
        _log_error(f"读取配置文件失败: {e}")
        return default_config

def save_banana2_config(config):
    """保存配置文件 - 已禁用"""
    # try:
    #     with open(BANANA2_CONFIG_FILE, 'w', encoding='utf-8') as f:
    #         json.dump(config, f, indent=4, ensure_ascii=False)
    # except Exception as e:
    #     _log_error(f"保存配置文件失败: {e}")
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


# ==================== 节点类 ====================

class Nano_Banana_2:
    """
    Google Nano Banana 2 多模态节点
    
    支持第三方API，参考ComfyUI_LLM_Banana优化
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎨 提示词": ("STRING", {
                    "multiline": True,
                    "default": "让女正对镜头，人物一致性保持不变",
                    "placeholder": "输入你的提示词..."
                }),
                
                "🤖 模型选择": ([
                    "nano-banana-2-T8",
                    "nano-banana-hd-T8", 
                    "nano-banana-T8"
                ], {
                    "default": "nano-banana-2-T8"
                }),
                
                "🌐 镜像站": (["comfly", "hk", "us"], {
                    "default": "comfly",
                    "tooltip": "API镜像站选择"
                }),
                
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则使用配置文件"
                }),
                
                # 图像控制参数
                "📐 宽高比": (["1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "4:5", "5:4", "21:9"], {
                    "default": "3:4",
                    "tooltip": "图像宽高比"
                }),
                
                "📊 响应模式": (["文字+图像", "仅图像"], {
                    "default": "文字+图像",
                    "tooltip": "响应模式"
                }),
                
                "💎 质量": (["标准", "高清", "超高清"], {
                    "default": "高清",
                    "tooltip": "图像质量"
                }),
                
                "🎭 风格": (["自然", "鲜艳", "艺术", "电影", "摄影"], {
                    "default": "自然",
                    "tooltip": "图像风格"
                }),
                
                # 智能图像控制
                "🔍 细节级别": (["自动选择", "基础细节", "专业细节", "高级质量", "大师级"], {
                    "default": "专业细节"
                }),
                
                "📷 相机控制": (["自动选择", "广角镜头", "微距拍摄", "低角度", "高角度", "特写镜头", "中景镜头"], {
                    "default": "自动选择"
                }),
                
                "💡 光照控制": (["自动设置", "自然光", "影棚灯光", "戏剧阴影", "柔和光晕", "黄金时刻", "蓝调时刻"], {
                    "default": "自动设置"
                }),
                
                "🎬 模板选择": (["自动选择", "专业肖像", "电影风景", "产品摄影", "数字概念艺术", "动漫风格", "照片级渲染", "古典油画", "水彩画", "赛博朋克", "复古胶片", "建筑摄影", "美食摄影"], {
                    "default": "自动选择"
                }),
            },
            "optional": {
                "🖼️ 图像1": ("IMAGE",),
                "🖼️ 图像2": ("IMAGE",),
                "🖼️ 图像3": ("IMAGE",),
                "🖼️ 图像4": ("IMAGE",),
                
                "🌡️ 温度": ("FLOAT", {
                    "default": 1.0,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.05
                }),
                
                "🎲 top_p": ("FLOAT", {
                    "default": 0.95,
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.05
                }),
                
                "🎰 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 2147483647
                }),
                
                "📝 最大令牌": ("INT", {
                    "default": 32768,
                    "min": 1,
                    "max": 32768
                }),
                
                "🎯 种子控制": (["随机", "固定", "递增"], {
                    "default": "随机"
                }),
                
                # 安全设置
                "🛡️ 安全级别": (["默认", "严格", "中等", "宽松"], {
                    "default": "默认",
                    "tooltip": "内容安全过滤级别"
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "response", "image_url")
    FUNCTION = "process"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "Google Nano Banana 2 多模态 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        self.color = NODE_COLOR
        self.bgcolor = NODE_COLOR
        self.config = get_banana2_config()
        self.api_key = "" # 不再从配置文件加载API密钥
        self.timeout = 300
    
    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def image_to_base64(self, image_tensor):
        """将tensor转换为base64字符串"""
        if image_tensor is None:
            return None
        
        pil_image = tensor2pil(image_tensor)[0]
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        base64_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return base64_str
    
    def enhance_prompt(self, prompt, quality, style, detail_level, camera_control, lighting_control, template_selection):
        """增强提示词"""
        # 风格模板
        style_templates = {
            "natural": {
                "prefix": "Create a natural, realistic image of",
                "suffix": "Use natural colors and realistic lighting.",
                "quality_boost": "Achieve photorealistic quality with natural aesthetics."
            },
            "vivid": {
                "prefix": "Generate a vibrant, colorful image of",
                "suffix": "Use vivid colors and dynamic composition.",
                "quality_boost": "Achieve stunning visual impact with vivid colors."
            },
            "artistic": {
                "prefix": "Create an artistic interpretation of",
                "suffix": "Use creative composition and artistic style.",
                "quality_boost": "Achieve artistic excellence with creative vision."
            },
            "cinematic": {
                "prefix": "Generate a cinematic scene featuring",
                "suffix": "Use cinematic lighting and composition.",
                "quality_boost": "Achieve movie-quality cinematography."
            },
            "photographic": {
                "prefix": "Create a professional photograph of",
                "suffix": "Use professional photography techniques.",
                "quality_boost": "Achieve professional photography quality."
            }
        }
        
        style_config = style_templates.get(style, style_templates["natural"])
        
        enhanced_parts = [
            style_config["prefix"],
            prompt.strip(),
            style_config["suffix"]
        ]
        
        # 添加质量控制
        if quality == "hd":
            enhanced_parts.append("Generate in high definition with professional detail.")
        elif quality == "ultra_hd":
            enhanced_parts.append("Generate in ultra-high definition with exceptional detail.")
        
        # 添加细节级别
        if detail_level != "Auto Select":
            detail_instructions = {
                "Basic Detail": "Focus on essential details and clean composition.",
                "Professional Detail": "Include professional-level detail and refined elements.",
                "Premium Quality": "Achieve premium quality with exceptional attention to detail.",
                "Masterpiece Level": "Create a masterpiece with extraordinary detail."
            }
            enhanced_parts.append(detail_instructions.get(detail_level, ""))
        
        # 添加相机控制
        if camera_control != "Auto Select":
            camera_instructions = {
                "Wide-angle Lens": "Use wide-angle perspective.",
                "Macro Shot": "Focus on close-up details with macro techniques.",
                "Low-angle Perspective": "Use low-angle perspective for dramatic impact.",
                "High-angle Shot": "Use high-angle perspective.",
                "Close-up Shot": "Focus on intimate details.",
                "Medium Shot": "Use medium framing for balanced composition."
            }
            enhanced_parts.append(camera_instructions.get(camera_control, ""))
        
        # 添加光照控制
        if lighting_control != "Auto Settings":
            lighting_instructions = {
                "Natural Light": "Use natural lighting with soft illumination.",
                "Studio Lighting": "Use professional studio lighting.",
                "Dramatic Shadows": "Use dramatic lighting with strong contrast.",
                "Soft Glow": "Use soft, glowing lighting.",
                "Golden Hour": "Use golden hour lighting with warm tones.",
                "Blue Hour": "Use blue hour lighting with cool tones."
            }
            enhanced_parts.append(lighting_instructions.get(lighting_control, ""))
        
        # 添加模板选择
        if template_selection != "Auto Select":
            template_instructions = {
                "Professional Portrait": "Apply professional portrait techniques.",
                "Cinematic Landscape": "Use cinematic landscape composition.",
                "Product Photography": "Apply product photography techniques.",
                "Digital Concept Art": "Use digital concept art style.",
                "Anime Style Art": "Apply anime/manga art style.",
                "Photorealistic Render": "Create photorealistic 3D rendering.",
                "Classical Oil Painting": "Apply classical oil painting style.",
                "Watercolor Painting": "Use watercolor painting techniques.",
                "Cyberpunk Future": "Apply cyberpunk futuristic aesthetics.",
                "Vintage Film Photography": "Use vintage film photography style.",
                "Architectural Photography": "Apply architectural photography techniques.",
                "Gourmet Food Photography": "Use gourmet food photography techniques."
            }
            enhanced_parts.append(template_instructions.get(template_selection, ""))
        
        return " ".join(enhanced_parts)
    
    def send_request_streaming(self, payload, base_url):
        """发送流式请求到第三方API"""
        full_response = ""
        session = requests.Session()
        
        try:
            response = session.post(
                f"{base_url}/v1/chat/completions",
                headers=self.get_headers(),
                json=payload,
                stream=True,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line_text = line.decode('utf-8').strip()
                    if line_text.startswith('data: '):
                        data = line_text[6:]
                        if data == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data)
                            if 'choices' in chunk and chunk['choices']:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    full_response += content
                        except json.JSONDecodeError:
                            continue
            
            return full_response
        
        except requests.exceptions.Timeout:
            raise TimeoutError(f"API请求超时 ({self.timeout}秒)")
        except Exception as e:
            raise Exception(f"流式响应错误: {str(e)}")
    
    def process(self, **kwargs):
        # 提取参数（支持中文参数名）
        prompt = kwargs.get("🎨 提示词", "")
        model = kwargs.get("🤖 模型选择", "nano-banana-2-T8")
        mirror_site = kwargs.get("🌐 镜像站", "comfly")
        aspect_ratio = kwargs.get("📐 宽高比", "3:4")
        response_modality = kwargs.get("📊 响应模式", "文字+图像")
        quality = kwargs.get("💎 质量", "高清")
        style = kwargs.get("🎭 风格", "自然")
        detail_level = kwargs.get("🔍 细节级别", "专业细节")
        camera_control = kwargs.get("📷 相机控制", "自动选择")
        lighting_control = kwargs.get("💡 光照控制", "自动设置")
        template_selection = kwargs.get("🎬 模板选择", "自动选择")
        
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        
        temperature = kwargs.get("🌡️ 温度", 1.0)
        top_p = kwargs.get("🎲 top_p", 0.95)
        apikey = kwargs.get("🔑 API密钥", "")
        seed = kwargs.get("🎰 随机种子", 0)
        max_tokens = kwargs.get("📝 最大令牌", 32768)
        seed_control = kwargs.get("🎯 种子控制", "随机")
        safety_level = kwargs.get("🛡️ 安全级别", "默认")
        
        # 中文选项映射到英文
        response_modality_map = {"文字+图像": "TEXT_AND_IMAGE", "仅图像": "IMAGE_ONLY"}
        response_modality = response_modality_map.get(response_modality, "TEXT_AND_IMAGE")
        
        quality_map = {"标准": "standard", "高清": "hd", "超高清": "ultra_hd"}
        quality = quality_map.get(quality, "hd")
        
        style_map = {"自然": "natural", "鲜艳": "vivid", "艺术": "artistic", "电影": "cinematic", "摄影": "photographic"}
        style = style_map.get(style, "natural")
        
        detail_map = {"自动选择": "Auto Select", "基础细节": "Basic Detail", "专业细节": "Professional Detail", "高级质量": "Premium Quality", "大师级": "Masterpiece Level"}
        detail_level = detail_map.get(detail_level, "Professional Detail")
        
        camera_map = {"自动选择": "Auto Select", "广角镜头": "Wide-angle Lens", "微距拍摄": "Macro Shot", "低角度": "Low-angle Perspective", "高角度": "High-angle Shot", "特写镜头": "Close-up Shot", "中景镜头": "Medium Shot"}
        camera_control = camera_map.get(camera_control, "Auto Select")
        
        lighting_map = {"自动设置": "Auto Settings", "自然光": "Natural Light", "影棚灯光": "Studio Lighting", "戏剧阴影": "Dramatic Shadows", "柔和光晕": "Soft Glow", "黄金时刻": "Golden Hour", "蓝调时刻": "Blue Hour"}
        lighting_control = lighting_map.get(lighting_control, "Auto Settings")
        
        template_map = {"自动选择": "Auto Select", "专业肖像": "Professional Portrait", "电影风景": "Cinematic Landscape", "产品摄影": "Product Photography", "数字概念艺术": "Digital Concept Art", "动漫风格": "Anime Style Art", "照片级渲染": "Photorealistic Render", "古典油画": "Classical Oil Painting", "水彩画": "Watercolor Painting", "赛博朋克": "Cyberpunk Future", "复古胶片": "Vintage Film Photography", "建筑摄影": "Architectural Photography", "美食摄影": "Gourmet Food Photography"}
        template_selection = template_map.get(template_selection, "Auto Select")
        
        # 更新API密钥
        if apikey.strip():
            self.api_key = apikey
        
        if not self.api_key:
            error_msg = "❌ 错误：请配置API密钥"
            _log_error(error_msg)
            blank_image = Image.new('RGB', (512, 512), color='white')
            blank_tensor = pil2tensor(blank_image)
            return (blank_tensor, error_msg, "")
        
        # 根据mirror_site选择设置base_url
        mirror_mapping = {
            "comfly": "https://api.gptbest.vip",
            "hk": "https://hk-api.gptbest.vip",
            "us": "https://api.gptbest.vip"
        }
        base_url = mirror_mapping.get(mirror_site, "https://api.gptbest.vip").rstrip('/')
        
        # 移除模型名称中的-T8后缀
        actual_model = model.replace("-T8", "")
        
        # 准备默认图像
        default_image = None
        for img in [image1, image2, image3, image4]:
            if img is not None:
                default_image = img
                break
        
        if default_image is None:
            blank_image = Image.new('RGB', (512, 512), color='white')
            default_image = pil2tensor(blank_image)
        
        _log_info(f"使用第三方API - 模型: {actual_model}, 镜像站: {mirror_site}")
        
        # 增强提示词
        enhanced_prompt = self.enhance_prompt(prompt, quality, style, detail_level, 
                                              camera_control, lighting_control, template_selection)
        
        # 构建消息内容
        content = [{"type": "text", "text": enhanced_prompt}]
        
        # 添加图像
        images_added = 0
        for idx, img in enumerate([image1, image2, image3, image4], 1):
            if img is not None:
                batch_size = img.shape[0]
                _log_info(f"处理image{idx}，批次大小: {batch_size}")
                
                for i in range(batch_size):
                    single_image = img[i:i+1]
                    image_base64 = self.image_to_base64(single_image)
                    if image_base64:
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_base64}"}
                        })
                        images_added += 1
        
        _log_info(f"共添加 {images_added} 张图像到请求")
        
        # 构建消息
        messages = [{
            "role": "user",
            "content": content
        }]
        
        # 构建payload
        payload = {
            "model": actual_model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        if seed > 0:
            payload["seed"] = seed
        
        # 发送请求
        _log_info(f"发送请求到: {base_url}/v1/chat/completions")
        try:
            response_text = self.send_request_streaming(payload, base_url)
        except Exception as e:
            error_msg = f"❌ API错误: {str(e)}"
            _log_error(error_msg)
            return (default_image, error_msg, "")
        
        # 尝试从响应中提取base64图像
        base64_pattern = r'data:image\/[^;]+;base64,([A-Za-z0-9+/=]+)'
        base64_matches = re.findall(base64_pattern, response_text)
        
        if base64_matches:
            try:
                image_data = base64.b64decode(base64_matches[0])
                generated_image = Image.open(BytesIO(image_data))
                generated_tensor = pil2tensor(generated_image)
                _log_info(f"✅ 成功生成图像 ({generated_image.size[0]}x{generated_image.size[1]})")
                return (generated_tensor, response_text, f"data:image/png;base64,{base64_matches[0]}")
            except Exception as e:
                _log_error(f"处理base64图像数据错误: {str(e)}")
        
        # 尝试从响应中提取图像URL
        image_pattern = r'!\[.*?\]\((.*?)\)'
        matches = re.findall(image_pattern, response_text)
        
        if not matches:
            url_pattern = r'https?://\S+\.(?:jpg|jpeg|png|gif|webp)'
            matches = re.findall(url_pattern, response_text)
        
        if not matches:
            all_urls_pattern = r'https?://\S+'
            matches = re.findall(all_urls_pattern, response_text)
        
        if matches:
            image_url = matches[0]
            try:
                img_response = requests.get(image_url, timeout=self.timeout)
                img_response.raise_for_status()
                
                generated_image = Image.open(BytesIO(img_response.content))
                generated_tensor = pil2tensor(generated_image)
                _log_info(f"✅ 成功下载图像 ({generated_image.size[0]}x{generated_image.size[1]})")
                return (generated_tensor, response_text, image_url)
            except Exception as e:
                _log_error(f"下载图像错误: {str(e)}")
                return (default_image, f"{response_text}\n\n下载图像错误: {str(e)}", image_url)
        else:
            _log_info("✅ 返回文本响应（未找到图像）")
            return (default_image, response_text, "")


class Dapao_NanoBanana2:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "🎨 提示词": ("STRING", {
                    "multiline": True, 
                    "default": "",
                    "placeholder": "输入你的提示词..."
                }),
                "🤖 模式": (["图像编辑", "文生图"], {"default": "图像编辑"}),
                "🌐 API来源": (["comfly【默认】", "手动输入IP", "香港节点", "高速美国节点"], {"default": "comfly【默认】"}),
                "� 自定义IP": ("STRING", {
                    "default": "", 
                    "placeholder": "选择'手动输入IP'选项时输入 (例如 http://104.194.8.112:9088)"
                }),
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "请输入API Key"
                }),
                "🎭 模型": (["nano-banana-2"], {"default": "nano-banana-2"}),
                "📐 宽高比": (["auto", "16:9", "4:3", "4:5", "3:2", "1:1", "2:3", "3:4", "5:4", "9:16", "21:9"], {"default": "auto"}),
                "📏 图像尺寸": (["1K", "2K", "4K"], {"default": "2K"}),
            },
            "optional": {
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
                "📤 响应格式": (["url", "b64_json"], {"default": "url"}),
                "🎲 随机种子": ("INT", {"default": 0, "min": 0, "max": 2147483647})  
            }
        }
    
    RETURN_TYPES = ("IMAGE", "STRING", "STRING")
    RETURN_NAMES = ("image", "response", "image_url")
    FUNCTION = "generate_image_with_api_set"
    CATEGORY = "🤖dapaoAPI/Nano Banana 2"

    def __init__(self):
        self.config = get_banana2_config()
        self.api_key = self.config.get('api_key', '')
        self.timeout = 600

    def get_headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}"
        }
    
    def image_to_base64(self, image_tensor):
        """Convert tensor to base64 string"""
        if image_tensor is None:
            return None
            
        pil_image = tensor2pil(image_tensor)[0]
        buffered = BytesIO()
        pil_image.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')
    
    def generate_image_with_api_set(self, **kwargs):
        # 提取参数
        prompt = kwargs.get("🎨 提示词", "")
        api_base = kwargs.get("🌐 API来源", "comfly【默认】")
        apikey = kwargs.get("🔑 API密钥", "")
        mode_cn = kwargs.get("🤖 模式", "图像编辑")
        model = kwargs.get("🎭 模型", "nano-banana-2")
        aspect_ratio = kwargs.get("📐 宽高比", "auto")
        image_size = kwargs.get("📏 图像尺寸", "2K")
        custom_ip = kwargs.get("🔗 自定义IP", "")
        response_format = kwargs.get("📤 响应格式", "url")
        seed = kwargs.get("🎲 随机种子", 0)
        
        # 模式映射
        mode_map = {"文生图": "text2img", "图像编辑": "img2img"}
        mode = mode_map.get(mode_cn, "text2img")
        
        # 提取图像
        image_list = []
        for i in range(1, 21):
            key = f"🖼️ 图像{i}"
            if key in kwargs:
                image_list.append(kwargs[key])
            else:
                image_list.append(None)
        
        all_images = image_list

        baseurl = "https://ai.comfly.chat"
        base_url_mapping = {
            "comfly【默认】": "https://ai.comfly.chat",
            "手动输入IP": custom_ip,
            "香港节点": "https://hk-api.gptbest.vip",
            "高速美国节点": "https://api.gptbest.vip"
        }
        
        if api_base == "手动输入IP" and not custom_ip.strip():
            raise ValueError("选择'手动输入IP'选项时，必须在'自定义IP'字段中提供自定义IP地址")
        
        if api_base in base_url_mapping:
            baseurl = base_url_mapping[api_base]
            
        if apikey.strip():
            self.api_key = apikey
            # Update local config file
            config = get_banana2_config()
            config['api_key'] = apikey
            save_banana2_config(config)
            
        if not self.api_key:
            error_message = "API key not found in banana2_config.json"
            print(error_message)
            blank_image = Image.new('RGB', (1024, 1024), color='white')
            blank_tensor = pil2tensor(blank_image)
            return (blank_tensor, error_message, "")
            
        try:
            pbar = comfy.utils.ProgressBar(100)
            pbar.update_absolute(10)

            final_prompt = prompt
            
            if mode == "text2img":
                headers = self.get_headers()
                headers["Content-Type"] = "application/json"
                
                payload = {
                    "prompt": final_prompt,
                    "model": model,
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size
                }
                    
                if response_format:
                    payload["response_format"] = response_format

                if seed > 0:
                    payload["seed"] = seed
                           
                response = requests.post(
                    f"{baseurl}/v1/images/generations",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout
                )
            else:
                headers = self.get_headers()
                
                files = []
                image_count = 0
                for img in all_images:
                    if img is not None:
                        pil_img = tensor2pil(img)[0]
                        buffered = BytesIO()
                        pil_img.save(buffered, format="PNG")
                        buffered.seek(0)
                        files.append(('image', (f'image_{image_count}.png', buffered, 'image/png')))
                        image_count += 1
                
                print(f"处理 {image_count} 张输入图像")
                
                data = {
                    "prompt": final_prompt,
                    "model": model,
                    "aspect_ratio": aspect_ratio,
                    "image_size": image_size
                }
                
                if response_format:
                    data["response_format"] = response_format

                if seed > 0:
                    data["seed"] = str(seed)
               
                response = requests.post(
                    f"{baseurl}/v1/images/edits",
                    headers=headers,
                    data=data,
                    files=files,
                    timeout=self.timeout
                )
            
            pbar.update_absolute(50)
            
            if response.status_code != 200:
                error_message = f"API 错误: {response.status_code} - {response.text}"
                print(error_message)
                blank_image = Image.new('RGB', (1024, 1024), color='white')
                blank_tensor = pil2tensor(blank_image)
                return (blank_tensor, error_message, "")
                
            result = response.json()
            
            if "data" not in result or not result["data"]:
                error_message = "响应中无图像数据"
                print(error_message)
                blank_image = Image.new('RGB', (1024, 1024), color='white')
                blank_tensor = pil2tensor(blank_image)
                return (blank_tensor, error_message, "")
            
            generated_tensors = []
            image_urls = []
            response_info = f"使用 {model} 生成了 {len(result['data'])} 张图像\n"
            response_info += f"图像尺寸: {image_size}\n"
            response_info += f"宽高比: {aspect_ratio}\n"
            
            if mode == "img2img":
                response_info += f"输入图像数: {image_count}\n"

            if seed > 0:
                response_info += f"种子: {seed}\n"
            
            for i, item in enumerate(result["data"]):
                pbar.update_absolute(50 + (i+1) * 40 // len(result['data']))
                
                if "b64_json" in item:
                    image_data = base64.b64decode(item["b64_json"])
                    generated_image = Image.open(BytesIO(image_data))
                    generated_tensor = pil2tensor(generated_image)
                    generated_tensors.append(generated_tensor)
                    response_info += f"图像 {i+1}: Base64 数据\n"
                elif "url" in item:
                    image_url = item["url"]
                    image_urls.append(image_url)
                    response_info += f"图像 {i+1}: {image_url}\n"
                    try:
                        img_response = requests.get(image_url, timeout=self.timeout)
                        img_response.raise_for_status()
                        generated_image = Image.open(BytesIO(img_response.content))
                        generated_tensor = pil2tensor(generated_image)
                        generated_tensors.append(generated_tensor)
                    except Exception as e:
                        print(f"从 URL 下载图像错误: {str(e)}")
            
            pbar.update_absolute(100)
            
            if generated_tensors:
                combined_tensor = torch.cat(generated_tensors, dim=0)
                first_image_url = image_urls[0] if image_urls else ""
                return (combined_tensor, response_info, first_image_url)
            else:
                error_message = "处理图像失败"
                print(error_message)
                blank_image = Image.new('RGB', (1024, 1024), color='white')
                blank_tensor = pil2tensor(blank_image)
                return (blank_tensor, error_message, "")
            
        except Exception as e:
            error_message = f"图像生成错误: {str(e)}"
            print(error_message)
            import traceback
            traceback.print_exc()
            blank_image = Image.new('RGB', (1024, 1024), color='white')
            blank_tensor = pil2tensor(blank_image)
            return (blank_tensor, error_message, "")


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "Nano_Banana_2": Nano_Banana_2,
    "Dapao_NanoBanana2": Dapao_NanoBanana2,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Nano_Banana_2": "🍌 Nano Banana 2 @炮老师的小课堂",
    "Dapao_NanoBanana2": "🍌 Nano Banana 2 (Dapao) @炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']
