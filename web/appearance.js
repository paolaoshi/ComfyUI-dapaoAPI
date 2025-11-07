/**
 * dapaoAPI 节点外观设置
 * 
 * 设置所有 dapaoAPI 节点的统一颜色主题
 * 作者：@炮老师的小课堂
 */

import { app } from "../../scripts/app.js";

// 节点颜色配置
// 标题栏使用紫色，背景使用深橙棕色，形成层次感
const NODE_COLORS = {
    color: "#631E77",      // 标题栏颜色 (紫色 RGB: 99, 30, 119)
    bgcolor: "#773508"     // 背景颜色 (深橙棕色 RGB: 119, 53, 8)
};

// 注册 ComfyUI 扩展
app.registerExtension({
    name: "dapaoAPI.appearance",
    
    /**
     * 节点创建时的回调函数
     * 当任何节点被创建时，此函数会被调用
     */
    async nodeCreated(node) {
        // 检查节点是否属于 dapaoAPI
        // 包括以下节点类型：
        // - Seedream_Text2Image (Seedream 4.0 文生图)
        // - Seedream_MultiImage (Seedream 4.0 多图编辑)
        // - Doubao_ImageToPrompt (豆包图像反推)
        // - GLM_ImageToPrompt (GLM 图像反推)
        // - GLM_PromptPolish (GLM 提示词润色)
        // - Doubao_Chat (豆包LLM对话)
        // - Zhipu_Chat (智谱LLM对话)
        
        const dapaoAPINodeClasses = [
            "Seedream_Text2Image",
            "Seedream_MultiImage",
            "Doubao_ImageToPrompt",
            "GLM_ImageToPrompt",
            "GLM_PromptPolish",
            "Doubao_Chat",
            "Zhipu_Chat"
        ];
        
        // 如果是 dapaoAPI 的节点，应用颜色
        if (dapaoAPINodeClasses.includes(node.comfyClass)) {
            node.color = NODE_COLORS.color;
            node.bgcolor = NODE_COLORS.bgcolor;
            
            // 在控制台输出日志（可选）
            console.log(`[dapaoAPI] 已应用颜色主题到节点: ${node.comfyClass}`);
        }
    }
});

