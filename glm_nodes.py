"""
大炮 API - 智谱 AI (GLM) 节点集合
提供图像反推和提示词润色功能
基于智谱 API 实现

作者：@炮老师的小课堂
版本：v2.1.0
"""

import os
import json
import base64
import random
import io
from PIL import Image
import numpy as np
import torch

# 尝试导入智谱AI SDK
try:
    from zhipuai import ZhipuAI
    ZHIPUAI_AVAILABLE = True
except ImportError:
    ZHIPUAI_AVAILABLE = False
    print("[GLM_Nodes] 警告：未安装 zhipuai，请运行: pip install zhipuai")

# 获取当前目录
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
GLM_CONFIG_FILE = os.path.join(CURRENT_DIR, 'glm_config.json')
GLM_TEMPLATES_DIR = os.path.join(CURRENT_DIR, 'glm_optimization_templates')

# 统一节点颜色 (橙棕色)
NODE_COLOR = "#773508"  # RGB(119, 53, 8)


# ==================== 辅助函数 ====================

def _log_info(message):
    """统一的日志输出函数"""
    print(f"[dapaoAPI-GLM] 信息：{message}")


def _log_warning(message):
    """统一的警告输出函数"""
    print(f"[dapaoAPI-GLM] 警告：{message}")


def _log_error(message):
    """统一的错误输出函数"""
    print(f"[dapaoAPI-GLM] 错误：{message}")


def get_glm_config():
    """
    读取 GLM 配置文件
    
    Returns:
        dict: 配置字典
    """
    default_config = {
        "ZHIPUAI_API_KEY": "",
        "default_model": "GLM-4.5-Flash",
        "default_vision_model": "glm-4v-flash",
        "temperature": 0.9,
        "top_p": 0.7,
        "max_tokens": 2048
    }
    
    try:
        if os.path.exists(GLM_CONFIG_FILE):
            with open(GLM_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return {**default_config, **config}
        else:
            return default_config
    except Exception as e:
        _log_error(f"读取 GLM 配置文件失败: {e}")
        return default_config


def get_zhipuai_api_key():
    """
    获取智谱 API Key
    优先级：环境变量 > 配置文件
    
    Returns:
        str: API Key
    """
    # 1. 尝试从环境变量获取
    env_api_key = os.getenv("ZHIPUAI_API_KEY")
    if env_api_key:
        _log_info("使用环境变量 ZHIPUAI_API_KEY")
        return env_api_key
    
    # 2. 从配置文件获取
    config = get_glm_config()
    api_key = config.get("ZHIPUAI_API_KEY", "")
    if api_key and api_key != "YOUR_ZHIPUAI_API_KEY_HERE":
        _log_info("从配置文件读取 API Key")
        return api_key
    
    _log_warning("未找到 API Key，请在 glm_config.json 中配置")
    return ""


def tensor_to_base64(image_tensor: torch.Tensor) -> str:
    """
    将 ComfyUI 图像张量转换为 base64 编码
    
    Args:
        image_tensor: ComfyUI 图像张量 [B, H, W, C], 值范围 [0, 1]
        
    Returns:
        str: base64 编码的图像数据（带 data URL 前缀）
    """
    try:
        # ComfyUI 的 IMAGE 是 PyTorch 张量，范围 [0,1]，形状 [B, H, W, C]
        # 转换为 PIL Image，范围 [0,255]
        i = 255. * image_tensor.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8)[0])  # 取第一个 batch
        
        # 转换为 base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        return f"data:image/png;base64,{image_base64}"
    except Exception as e:
        _log_error(f"图像转 base64 失败: {e}")
        return None


def get_glm_optimization_templates():
    """
    获取 GLM 优化模板列表
    从 glm_optimization_templates 文件夹读取所有 .txt 文件
    
    Returns:
        list: 模板名称列表（不含扩展名）
    """
    templates = []  # 不再包含"自定义输入"选项
    
    try:
        if os.path.exists(GLM_TEMPLATES_DIR):
            # 读取所有 .txt 文件
            for filename in sorted(os.listdir(GLM_TEMPLATES_DIR)):
                if filename.endswith('.txt'):
                    # 去掉 .txt 扩展名
                    template_name = filename[:-4]
                    templates.append(template_name)
            
            if len(templates) > 0:
                _log_info(f"加载了 {len(templates)} 个 GLM 优化模板")
        else:
            _log_warning(f"GLM 模板文件夹不存在: {GLM_TEMPLATES_DIR}")
            templates.extend(["即梦文生图扩写", "即梦多图编辑", "wan2.2视频扩写"])
    except Exception as e:
        _log_error(f"读取 GLM 优化模板失败: {e}")
        templates.extend(["即梦文生图扩写", "即梦多图编辑", "wan2.2视频扩写"])
    
    # 确保默认模板在第一位
    if "即梦文生图扩写" in templates:
        templates.remove("即梦文生图扩写")
        templates.insert(0, "即梦文生图扩写")
    
    return templates if templates else ["即梦文生图扩写"]


def load_glm_template_content(template_name: str) -> str:
    """
    加载指定 GLM 优化模板的内容
    
    Args:
        template_name: 模板名称（不含扩展名）
        
    Returns:
        str: 模板内容
    """
    template_file = os.path.join(GLM_TEMPLATES_DIR, f"{template_name}.txt")
    
    try:
        if not os.path.exists(template_file):
            _log_warning(f"模板文件不存在: {template_file}")
            return ""
        
        with open(template_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找分隔线
        marker = "==================== 优化方案内容 ===================="
        if marker in content:
            # 提取分隔线后的内容
            parts = content.split(marker)
            if len(parts) >= 2:
                template_content = parts[1].strip()
                return template_content
        
        # 如果没有分隔线，过滤掉注释行
        lines = []
        for line in content.split('\n'):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                lines.append(line)
        
        return '\n'.join(lines)
    
    except Exception as e:
        _log_error(f"读取模板文件失败: {e}")
        return ""


# ==================== 节点类 ====================

class GLM_ImageToPrompt:
    """
    智谱 AI 图像反推节点 v3.1
    
    使用 GLM-4V 视觉模型分析图像，生成详细的图像描述
    
    功能特性：
    - 🖼️ 多图支持：最多支持4张图片同时分析
    - 📝 自定义反推指令：灵活控制输出风格
    - 🎲 种子控制：支持固定、随机、递增三种模式
    
    适用场景：
    - 图生图前的提示词参考
    - 了解图像内容
    - 生成训练数据标注
    - 多图对比分析
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_glm_config()
        
        return {
            "required": {
                # === 图像输入 ===
                "🖼️ 图像1": ("IMAGE", {
                    "tooltip": "必填：主要分析图像"
                }),
                
                # === 反推指令 ===
                "📝 反推指令": ("STRING", {
                    "multiline": True,
                    "default": """你是一个专业的图像分析专家，能够将图片内容转化为高质量的英文提示词。

请仔细观察图片，生成详细的英文描述，包括：
1. 主体：人物/物体的外观、特征、表情、动作
2. 场景：环境、背景、时间、天气、光线
3. 构图：视角、景别、空间关系
4. 风格：艺术风格、色彩、氛围、质感
5. 细节：纹理、材质、装饰、道具等

要求：
- 使用英文
- 详细具体
- 用逗号连接不同描述
- 末尾添加画质词：high quality, ultra detailed, masterpiece

只输出最终的英文提示词，不要包含解释。""",
                    "placeholder": "描述如何分析图像..."
                }),
                
                # === API 配置 ===
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "placeholder": "留空则从配置文件读取"
                }),
                "🤖 视觉模型": ("STRING", {
                    "default": config.get("default_vision_model", "glm-4v-flash"),
                    "placeholder": "如: glm-4v-flash, glm-4v-plus"
                }),
                
                # === 高级设置 ===
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子值"
                }),
                
                "🎛️ 种子控制": (["固定", "随机", "递增"], {
                    "default": "随机",
                    "tooltip": "固定: 使用上方种子值; 随机: 每次生成新种子; 递增: 种子值+1"
                }),
            },
            "optional": {
                # === 可选图像输入 ===
                "🖼️ 图像2": ("IMAGE", {
                    "tooltip": "可选：额外的对比图像"
                }),
                "🖼️ 图像3": ("IMAGE", {
                    "tooltip": "可选：额外的对比图像"
                }),
                "🖼️ 图像4": ("IMAGE", {
                    "tooltip": "可选：额外的对比图像"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("🎨 图像描述", "ℹ️ 处理信息")
    FUNCTION = "analyze_image"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "使用智谱 AI 分析图像，支持多图输入、生成详细的英文提示词 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        # 设置节点颜色
        self.color = NODE_COLOR
        self.bgcolor = NODE_COLOR
        # 保存上一次使用的种子（用于递增模式）
        self.last_seed = 0
    
    def analyze_image(self, **kwargs):
        """分析图像，生成提示词（支持多图）"""
        
        # 检查 SDK 是否可用
        if not ZHIPUAI_AVAILABLE:
            error_msg = "❌ 错误：未安装 zhipuai SDK\n\n请运行以下命令安装：\npip install zhipuai\n\n安装后重启 ComfyUI"
            _log_error(error_msg)
            return ("", error_msg)
        
        # 参数解析
        image1 = kwargs.get("🖼️ 图像1")
        image2 = kwargs.get("🖼️ 图像2")
        image3 = kwargs.get("🖼️ 图像3")
        image4 = kwargs.get("🖼️ 图像4")
        prompt_text = kwargs.get("📝 反推指令", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model_name = kwargs.get("🤖 视觉模型", "glm-4v-flash")
        seed = kwargs.get("🎲 随机种子", 0)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        
        # 获取 API Key
        final_api_key = api_key.strip() or get_zhipuai_api_key()
        if not final_api_key:
            error_msg = "❌ 错误：未提供 API Key\n\n请执行以下操作之一：\n1. 在节点的【🔑 API密钥】参数中输入\n2. 编辑 glm_config.json 文件配置\n3. 设置环境变量 ZHIPUAI_API_KEY"
            _log_error(error_msg)
            return ("", error_msg)
        
        # 检查图像输入（至少需要图像1）
        if image1 is None:
            error_msg = "❌ 错误：请提供至少一张图像\n\n请在【🖼️ 图像1】参数中上传图像"
            _log_error(error_msg)
            return ("", error_msg)
        
        try:
            # 收集所有有效的图像
            images = []
            if image1 is not None:
                images.append(("图像1", image1))
            if image2 is not None:
                images.append(("图像2", image2))
            if image3 is not None:
                images.append(("图像3", image3))
            if image4 is not None:
                images.append(("图像4", image4))
            
            _log_info(f"共接收到 {len(images)} 张图像")
            
            # 转换所有图像为 base64
            image_base64_list = []
            for img_name, img_tensor in images:
                _log_info(f"正在转换 {img_name}...")
                img_base64 = tensor_to_base64(img_tensor)
                if not img_base64:
                    _log_warning(f"{img_name} 转换失败，已跳过")
                    continue
                image_base64_list.append((img_name, img_base64))
            
            if not image_base64_list:
                error_msg = "❌ 错误：所有图像转换失败"
                _log_error(error_msg)
                return ("", error_msg)
            
            _log_info(f"成功转换 {len(image_base64_list)} 张图像")
            
            # 初始化客户端
            _log_info("初始化智谱 AI 客户端...")
            client = ZhipuAI(api_key=final_api_key)
            
            # 构建请求内容（先添加文本指令）
            content_parts = [{"type": "text", "text": prompt_text}]
            
            # 添加所有图像
            for img_name, img_base64 in image_base64_list:
                content_parts.append({
                    "type": "image_url",
                    "image_url": {"url": img_base64}
                })
            
            # === 种子处理 ===
            import random
            
            # 根据种子控制模式决定最终种子值
            if seed_control == "固定":
                effective_seed = seed
                seed_mode = "固定"
            elif seed_control == "随机":
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            elif seed_control == "递增":
                if self.last_seed == 0:
                    effective_seed = seed if seed != 0 else random.randint(0, 0xffffffffffffffff)
                else:
                    effective_seed = self.last_seed + 1
                seed_mode = "递增"
            else:
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            
            # 保存当前种子供下次使用
            self.last_seed = effective_seed
            random.seed(effective_seed)
            
            _log_info(f"调用 GLM-4V ({model_name}) 分析 {len(image_base64_list)} 张图像...")
            _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
            # 智谱API的种子值范围限制：必须在 2147483647 以内
            # 将大种子值映射到智谱API支持的范围内 (1 - 2147483647)
            zhipu_seed = (effective_seed % 2147483647) + 1 if effective_seed > 2147483647 else effective_seed
            if zhipu_seed != effective_seed:
                _log_info(f"种子值转换: {effective_seed} -> {zhipu_seed} (智谱API限制)")
            
            # 调用 API
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": content_parts}],
                seed=zhipu_seed if zhipu_seed != 0 else None
            )
            
            result_text = str(response.choices[0].message.content)
            _log_info("✅ 图像分析成功")
            
            # 构建详细的信息输出
            info_lines = [
                "🎉 GLM 图像分析成功",
                "",
                "📊 分析信息：",
                f"   模型：{model_name}",
                f"   图像数量：{len(image_base64_list)} 张",
                f"   图像列表：{', '.join([name for name, _ in image_base64_list])}",
                "",
                "🎲 种子信息：",
                f"   种子值：{effective_seed}",
                f"   控制模式：{seed_mode}",
                "",
                "✅ 分析完成"
            ]
            
            info = "\n".join(info_lines)
            
            return (result_text, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：图像分析失败\n\n错误详情：{str(e)}\n\n建议：\n1. 检查网络连接\n2. 检查 API Key 是否正确\n3. 查看终端完整日志"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            return ("", error_msg)


class GLM_PromptPolish:
    """
    智谱 AI 提示词润色节点 v3.1
    
    使用 GLM-4 大语言模型优化、扩写、润色提示词
    
    功能特性：
    - 📝 内置提示词输入：直接在节点内输入原始提示词
    - ✨ 预设优化方案：wan2.2视频扩写、即梦文生图扩写、即梦多图编辑
    - 🎯 系统提示词优先级：自定义输入 > 预设方案（默认"即梦文生图扩写"）
    - 📏 智能长度控制：自动优化到指定 token 长度
    - 💡 详细错误提示：清晰的状态和错误引导
    - 🎨 美化布局：参考 Seedream 多图编辑节点风格
    
    作者：@炮老师的小课堂
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        config = get_glm_config()
        templates = get_glm_optimization_templates()
        
        return {
            "required": {
                # === 输入提示词 ===
                "📝 原始提示词": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "输入需要优化的提示词..."
                }),
                
                # === 优化方案选择 ===
                "✨ 优化方案": (templates, {
                    "default": templates[0] if templates else "即梦文生图扩写",
                    "tooltip": "选择预设的优化方案（留空系统提示词则使用此预设）"
                }),
                
                # === 系统提示词（最高优先级）===
                "🎯 系统提示词": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "（可选）自定义系统提示词，留空则使用上方预设\n支持 {prompt} 占位符"
                }),
                
                # === API 配置 ===
                "🔑 API密钥": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "placeholder": "留空则从配置文件读取"
                }),
                
                "🤖 模型名称": ("STRING", {
                    "default": config.get("default_model", "GLM-4.5-Flash"),
                    "multiline": False,
                    "placeholder": "如: GLM-4.5-Flash, GLM-4-Plus"
                }),
                
                # === 高级参数 ===
                "🌡️ 温度": ("FLOAT", {
                    "default": config.get("temperature", 0.9),
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "温度参数，越高越有创造性"
                }),
                
                "🎲 Top-P": ("FLOAT", {
                    "default": config.get("top_p", 0.7),
                    "min": 0.0,
                    "max": 1.0,
                    "step": 0.01,
                    "tooltip": "Top-P 采样参数"
                }),
                
                "📏 最大长度": ("INT", {
                    "default": config.get("max_tokens", 2048),
                    "min": 256,
                    "max": 4096,
                    "step": 256,
                    "tooltip": "最大生成 token 数量"
                }),
                
                "🎲 随机种子": ("INT", {
                    "default": 0,
                    "min": 0,
                    "max": 0xffffffffffffffff,
                    "tooltip": "随机种子值"
                }),
                
                "🎛️ 种子控制": (["固定", "随机", "递增"], {
                    "default": "随机",
                    "tooltip": "固定: 使用上方种子值; 随机: 每次生成新种子; 递增: 种子值+1"
                }),
            }
        }
    
    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("✨ 优化后提示词", "📝 原始提示词", "ℹ️ 处理信息")
    FUNCTION = "polish_prompt"
    CATEGORY = "🤖dapaoAPI"
    DESCRIPTION = "使用智谱 AI 优化和润色提示词，支持模板选择、智能长度控制、3种种子模式、详细错误提示 | 作者: @炮老师的小课堂"
    OUTPUT_NODE = False
    
    def __init__(self):
        # 设置节点颜色
        self.color = NODE_COLOR
        self.bgcolor = NODE_COLOR
        # 保存上一次使用的种子（用于递增模式）
        self.last_seed = 0
    
    def polish_prompt(self, **kwargs):
        """润色提示词"""
        
        # 参数解析
        original_prompt = kwargs.get("📝 原始提示词", "")
        optimization_preset = kwargs.get("✨ 优化方案", "即梦文生图扩写")
        custom_system_prompt = kwargs.get("🎯 系统提示词", "")
        api_key = kwargs.get("🔑 API密钥", "")
        model_name = kwargs.get("🤖 模型名称", "GLM-4.5-Flash")
        temperature = kwargs.get("🌡️ 温度", 0.9)
        top_p = kwargs.get("🎲 Top-P", 0.7)
        max_tokens = kwargs.get("📏 最大长度", 2048)
        seed = kwargs.get("🎲 随机种子", 0)
        seed_control = kwargs.get("🎛️ 种子控制", "随机")
        
        # 状态信息收集器
        status_info = []
        
        # 检查 SDK 是否可用
        if not ZHIPUAI_AVAILABLE:
            error_msg = "❌ 错误：未安装 zhipuai SDK\n\n请运行以下命令安装：\npip install zhipuai\n\n安装后重启 ComfyUI"
            _log_error(error_msg)
            status_info.append("❌ SDK 未安装")
            return ("", "", error_msg)
        
        # 获取 API Key
        final_api_key = api_key.strip() or get_zhipuai_api_key()
        if not final_api_key:
            error_msg = "❌ 错误：未提供 API Key\n\n请执行以下操作之一：\n1. 在节点的【api_key】参数中输入\n2. 编辑 glm_config.json 文件配置\n3. 设置环境变量 ZHIPUAI_API_KEY"
            _log_error(error_msg)
            status_info.append("❌ API Key 缺失")
            return ("", original_prompt, error_msg)
        
        status_info.append("✅ API Key 已配置")
        
        # 检查输入
        if not original_prompt or not original_prompt.strip():
            error_msg = "❌ 错误：请输入需要优化的提示词\n\n请在【📝 原始提示词】参数中输入内容"
            _log_warning(error_msg)
            status_info.append("❌ 输入为空")
            return ("", "", error_msg)
        
        try:
            # === 优先级控制：自定义系统提示词 > 预设方案 ===
            final_optimization_prompt = ""
            used_method = ""
            
            if custom_system_prompt and custom_system_prompt.strip():
                # 最高优先级：用户手动输入系统提示词
                final_optimization_prompt = custom_system_prompt.strip()
                used_method = "自定义系统提示词"
                _log_info("✅ 使用自定义系统提示词")
                status_info.append("📝 使用：自定义系统提示词")
            else:
                # 使用预设方案（默认"即梦文生图扩写"）
                template_content = load_glm_template_content(optimization_preset)
                if template_content:
                    final_optimization_prompt = template_content
                    used_method = f"预设：{optimization_preset}"
                    _log_info(f"✅ 使用预设模板: {optimization_preset}")
                    status_info.append(f"📝 使用：{optimization_preset}")
                else:
                    _log_warning(f"预设 '{optimization_preset}' 加载失败，使用默认")
                    final_optimization_prompt = "请将以下内容优化为详细的提示词：{prompt}"
                    used_method = "默认方案（预设加载失败）"
                    status_info.append("⚠️ 预设加载失败，使用默认")
            
            # 替换占位符
            final_optimization_prompt = final_optimization_prompt.replace("{prompt}", original_prompt)
            
            # 初始化客户端
            _log_info("初始化智谱 AI 客户端...")
            status_info.append("🔄 正在连接智谱 API...")
            
            try:
                client = ZhipuAI(api_key=final_api_key)
                status_info.append("✅ API 连接成功")
            except Exception as init_error:
                error_msg = f"❌ 错误：API 初始化失败\n\n错误详情：{str(init_error)}\n\n可能原因：\n1. API Key 无效\n2. 网络连接问题\n3. SDK 版本问题\n\n建议：检查 API Key 是否正确"
                _log_error(error_msg)
                status_info.append("❌ API 连接失败")
                return ("", original_prompt, "\n".join(status_info) + "\n\n" + error_msg)
            
            # === 种子处理 ===
            import random
            
            # 根据种子控制模式决定最终种子值
            if seed_control == "固定":
                # 固定模式：使用用户指定的种子值
                effective_seed = seed
                seed_mode = "固定"
            elif seed_control == "随机":
                # 随机模式：每次生成新的随机种子
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            elif seed_control == "递增":
                # 递增模式：在上一次种子基础上+1
                if self.last_seed == 0:
                    effective_seed = seed if seed != 0 else random.randint(0, 0xffffffffffffffff)
                else:
                    effective_seed = self.last_seed + 1
                seed_mode = "递增"
            else:
                # 默认：随机
                effective_seed = random.randint(0, 0xffffffffffffffff)
                seed_mode = "随机"
            
            # 保存当前种子供下次使用
            self.last_seed = effective_seed
            
            random.seed(effective_seed)
            seed_info = f"🎲 种子：{effective_seed} (模式: {seed_mode})"
            status_info.append(seed_info)
            _log_info(f"使用种子：{effective_seed}，模式：{seed_mode}")
            
            # 智谱API的种子值范围限制：必须在 2147483647 以内
            # 将大种子值映射到智谱API支持的范围内 (1 - 2147483647)
            zhipu_seed = (effective_seed % 2147483647) + 1 if effective_seed > 2147483647 else effective_seed
            if zhipu_seed != effective_seed:
                _log_info(f"种子值转换: {effective_seed} -> {zhipu_seed} (智谱API限制)")
            
            _log_info(f"调用 GLM-4 ({model_name}) 优化提示词...")
            _log_info(f"原始提示词: {original_prompt[:50]}...")
            _log_info(f"最大生成长度: {max_tokens} tokens")
            
            status_info.append(f"🤖 模型：{model_name}")
            status_info.append(f"📏 最大长度：{max_tokens} tokens")
            status_info.append("🔄 正在优化提示词...")
            
            # === 调用 API 生成优化后的提示词 ===
            messages = [
                {"role": "system", "content": "你是一个专业的提示词优化专家。"},
                {"role": "user", "content": final_optimization_prompt}
            ]
            
            try:
                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    seed=zhipu_seed if zhipu_seed != 0 else None,
                )
            except Exception as api_error:
                error_msg = f"❌ 错误：API 调用失败\n\n错误详情：{str(api_error)}\n\n可能原因：\n1. API Key 已失效或额度不足\n2. 网络连接中断\n3. 模型名称错误\n4. 请求超时\n\n建议：\n1. 检查智谱 AI 控制台余额\n2. 检查网络连接\n3. 尝试重新运行"
                _log_error(error_msg)
                status_info.append("❌ API 调用失败")
                return ("", original_prompt, "\n".join(status_info) + "\n\n" + error_msg)
            
            optimized_prompt = response.choices[0].message.content
            status_info.append("✅ 优化完成")
            
            _log_info("提示词优化成功")
            _log_info(f"优化后提示词: {optimized_prompt[:100]}...")
            
            # 长度统计
            final_word_count = len(optimized_prompt.split())
            final_estimated_tokens = int(final_word_count * 1.3)
            
            status_info.append("=" * 40)
            status_info.append("✅ 优化成功完成")
            status_info.append("=" * 40)
            
            # 构建详细的信息输出
            info_lines = [
                "🎉 GLM 提示词优化成功",
                "",
                "📋 使用方案：",
                f"   {used_method}",
                "",
                "🤖 API 信息：",
                f"   模型：{model_name}",
                f"   温度：{temperature}",
                f"   Top-P：{top_p}",
                "",
                "📊 长度信息：",
                f"   实际：~{final_estimated_tokens} tokens ({final_word_count} 词)",
                "",
                "🎲 种子：",
                f"   {effective_seed}",
                "",
                "💡 提示：",
                "   - 优化后的提示词可以直接用于图像生成",
                "   - 可连接到其他节点继续处理",
            ]
            
            info = "\n".join(info_lines)
            
            return (optimized_prompt, original_prompt, info)
            
        except Exception as e:
            error_msg = f"❌ 错误：提示词优化失败\n\n错误详情：{str(e)}\n\n可能原因：\n1. 网络连接问题\n2. API 请求超时\n3. 系统错误\n\n建议：\n1. 检查网络连接\n2. 稍后重试\n3. 如果问题持续，请查看终端完整日志"
            _log_error(error_msg)
            import traceback
            _log_error(traceback.format_exc())
            
            # 添加状态信息
            if status_info:
                error_msg = "\n".join(status_info) + "\n\n" + error_msg
            
            return ("", original_prompt, error_msg)


# ==================== 节点注册 ====================

NODE_CLASS_MAPPINGS = {
    "GLM_ImageToPrompt": GLM_ImageToPrompt,
    "GLM_PromptPolish": GLM_PromptPolish,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GLM_ImageToPrompt": "🔍 GLM图像反推 @炮老师的小课堂",
    "GLM_PromptPolish": "✨ GLM提示词润色 @炮老师的小课堂",
}

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

