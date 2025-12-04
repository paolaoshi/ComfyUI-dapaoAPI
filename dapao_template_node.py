"""
Dapao Prompt Master
Template Manager for Dapao Image Prompts
"""

import os
import sys

try:
    from .dapao_template_adapter import DapaoPromptTemplateAdapter
except ImportError:
    from dapao_template_adapter import DapaoPromptTemplateAdapter


class DapaoPromptNode:
    """
    Dapao Prompt Node - Browse and use prompt templates
    """
    
    def __init__(self):
        """Initialize with template adapter"""
        try:
            self.adapter = DapaoPromptTemplateAdapter()
            self.initialized = True
        except Exception as e:
            print(f"[Dapao] ERROR: Failed to initialize adapter: {e}")
            self.adapter = None
            self.initialized = False
    
    @classmethod
    def INPUT_TYPES(cls):
        """Define node inputs"""
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "在此输入您的提示词...\n\n点击下方的「浏览模板」按钮加载模板。",
                    "dynamicPrompts": False
                })
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("final_prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = "🤖dapaoAPI/Nano Banana 2"
    OUTPUT_NODE = False
    
    def generate_prompt(self, prompt=""):
        """
        Generate final prompt
        """
        return (prompt,)


# ======================== Node Registration ========================

NODE_CLASS_MAPPINGS = {
    "DapaoPromptNode": DapaoPromptNode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DapaoPromptNode": "🎨 大炮bannan文生图提示词"
}
