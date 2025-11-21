"""
大炮 API (dapaoAPI) 节点初始化

支持功能：
- Seedream 4.0 图像生成（文生图、多图编辑）
- 智谱 AI 图像反推（GLM-4V）
- 智谱 AI 提示词润色（GLM-4）
- 豆包 LLM对话（Seed-1.6）
- 智谱 LLM对话（GLM-4 系列）
- Google Nano Banana 2 多模态（图像+文本）
- 灵活的分辨率和宽高比控制
- 统一的紫色+橙棕色节点主题

作者：@炮老师的小课堂
版本：v3.2.0
"""

# 加载 Seedream 节点
from .seedream_nodes import (
    NODE_CLASS_MAPPINGS as SEEDREAM_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as SEEDREAM_DISPLAY_MAPPINGS
)

# 尝试加载 GLM 节点
try:
    from .glm_nodes import (
        NODE_CLASS_MAPPINGS as GLM_MAPPINGS,
        NODE_DISPLAY_NAME_MAPPINGS as GLM_DISPLAY_MAPPINGS
    )
    GLM_AVAILABLE = True
except ImportError as e:
    GLM_MAPPINGS = {}
    GLM_DISPLAY_MAPPINGS = {}
    GLM_AVAILABLE = False
    print(f"[dapaoAPI] 警告：GLM 节点加载失败: {e}")
    print("[dapaoAPI] 提示：请运行 pip install zhipuai 以启用 GLM 功能")

# 加载豆包LLM对话节点
from .doubao_chat_node import (
    NODE_CLASS_MAPPINGS as DOUBAO_CHAT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as DOUBAO_CHAT_DISPLAY_MAPPINGS
)

# 加载智谱LLM对话节点
from .zhipu_chat_node import (
    NODE_CLASS_MAPPINGS as ZHIPU_CHAT_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as ZHIPU_CHAT_DISPLAY_MAPPINGS
)

# 加载Nano Banana 2多模态节点
from .banana2_nodes import (
    NODE_CLASS_MAPPINGS as BANANA2_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as BANANA2_DISPLAY_MAPPINGS
)

# 加载Gemini 3多功能节点
from .gemini3_nodes import (
    NODE_CLASS_MAPPINGS as GEMINI3_MAPPINGS,
    NODE_DISPLAY_NAME_MAPPINGS as GEMINI3_DISPLAY_MAPPINGS
)

# 合并所有节点映射
NODE_CLASS_MAPPINGS = {
    **SEEDREAM_MAPPINGS,
    **GLM_MAPPINGS,
    **DOUBAO_CHAT_MAPPINGS,
    **ZHIPU_CHAT_MAPPINGS,
    **BANANA2_MAPPINGS,
    **GEMINI3_MAPPINGS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    **SEEDREAM_DISPLAY_MAPPINGS,
    **GLM_DISPLAY_MAPPINGS,
    **DOUBAO_CHAT_DISPLAY_MAPPINGS,
    **ZHIPU_CHAT_DISPLAY_MAPPINGS,
    **BANANA2_DISPLAY_MAPPINGS,
    **GEMINI3_DISPLAY_MAPPINGS,
}

# 声明 Web 目录，用于加载 JavaScript 扩展（节点颜色设置）
WEB_DIRECTORY = "./web"

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS', 'WEB_DIRECTORY']

# 启动信息
print("=" * 60)
print("  🎨 大炮 API (dapaoAPI) 节点加载完成!")
print("=" * 60)
print(f"  📦 Seedream 节点：{len(SEEDREAM_MAPPINGS)} 个")
if GLM_AVAILABLE:
    print(f"  🤖 GLM 智谱节点：{len(GLM_MAPPINGS)} 个")
else:
    print("  ⚠️  GLM 节点未启用（需要安装 zhipuai）")
print(f"  💬 豆包LLM对话：{len(DOUBAO_CHAT_MAPPINGS)} 个")
print(f"  💬 智谱LLM对话：{len(ZHIPU_CHAT_MAPPINGS)} 个")
print(f"  🍌 Nano Banana 2多模态：{len(BANANA2_MAPPINGS)} 个")
print(f"  💎 Gemini 3多功能：{len(GEMINI3_MAPPINGS)} 个")
print(f"  ✅ 总计：{len(NODE_CLASS_MAPPINGS)} 个节点")
print(f"  👨‍🏫 作者：@炮老师的小课堂")
print(f"  🎨 主题：紫色标题栏 + 橙棕色背景")
print("=" * 60)


