import { app } from "../../../scripts/app.js";

// 调试日志前缀
const TAG = "[Dapao LoRA UI]";

console.log(`${TAG} Loaded version 2.1 (ModelScope LoRA toggle parity)`);

// 帮助函数：安全获取 Widget
function getWidget(node, name) {
    if (!node?.widgets) return null;
    return node.widgets.find((w) => w.name === name) || null;
}

// 帮助函数：通过正则获取 Widget
function getWidgetByRegex(node, regex) {
    if (!node?.widgets) return null;
    return node.widgets.find((w) => regex.test(w.name)) || null;
}

// 获取各个关键 Widget
function getEnableWidget(node) {
    return getWidgetByRegex(node, /(启用|enable)\s*.*lora/i);
}

function getCountWidget(node) {
    return getWidgetByRegex(node, /(lora\s*数量|数量\s*lora)/i);
}

function getLoraIdWidget(node, i) {
    // 匹配 "LoRA1 ID", "LoRA 1 ID", "🧩 LoRA1 ID" 等
    return getWidgetByRegex(node, new RegExp(`LoRA\\s*${i}\\s*.*ID`, "i"));
}

function getLoraWeightWidget(node, i) {
    // 匹配 "LoRA1 强度", "LoRA 1 强度", "🎚️ LoRA1 强度" 等
    return getWidgetByRegex(node, new RegExp(`LoRA\\s*${i}\\s*.*强度`, "i"));
}

// 核心显示/隐藏逻辑
// 使用 LiteGraph 标准 hidden 属性，不 hack computeSize
function setHidden(node, widget, hidden) {
    if (!widget) return;
    
    // 如果状态没变，就不做操作，避免频繁刷新布局
    if (widget.hidden === hidden) return;
    
    widget.hidden = hidden;
    
    // 强制触发重新计算节点尺寸
    if (node.onResize) {
        node.onResize(node.size);
    }
    node.setDirtyCanvas(true, true);
}

// 主更新函数
function updateLoraWidgets(node) {
    if (!node.widgets) return;

    const enableWidget = getEnableWidget(node);
    const countWidget = getCountWidget(node);
    
    const enabled = enableWidget ? (enableWidget.value === true || enableWidget.value === "true" || enableWidget.value === 1 || enableWidget.value === "1") : false;
    
    // 获取数量：默认 1
    let count = 1;
    if (countWidget && countWidget.value) {
        // 尝试解析，支持字符串 "1" 或数字 1
        const val = parseInt(countWidget.value, 10);
        if (!isNaN(val)) {
            count = Math.max(1, Math.min(5, val));
        }
    }

    // 1. 设置数量控件的可见性
    setHidden(node, countWidget, !enabled);

    // 2. 遍历设置 LoRA 1~5 的可见性
    for (let i = 1; i <= 5; i++) {
        const idWidget = getLoraIdWidget(node, i);
        const wWidget = getLoraWeightWidget(node, i);
        
        const show = enabled && (i <= count);
        
        setHidden(node, idWidget, !show);
        setHidden(node, wWidget, !show);
    }
    
    // 记录状态，用于减少重复计算（可选）
    node._dapaoLoraUiState = { enabled, count };
    
    // 触发布局刷新
    node.setSize(node.computeSize());
}

app.registerExtension({
    name: "Dapao.ModelScopeT2I.LoRAUI",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "DapaoModelScopeTextToImage" && nodeData.name !== "DapaoModelScopeImageEdit") return;

        // 1. 节点创建时触发
        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            if (onNodeCreated) onNodeCreated.apply(this, arguments);
            console.log(`${TAG} Node created, initializing widgets...`);
            // 延时一下确保 widget 都初始化完了
            setTimeout(() => updateLoraWidgets(this), 10);
        };

        // 2. 节点添加到图表时触发
        const onAdded = nodeType.prototype.onAdded;
        nodeType.prototype.onAdded = function () {
            if (onAdded) onAdded.apply(this, arguments);
            console.log(`${TAG} Node added to graph`);
            updateLoraWidgets(this);
            
            // 监听值变化回调
            const enableWidget = getEnableWidget(this);
            const countWidget = getCountWidget(this);
            
            if (enableWidget) {
                const orig = enableWidget.callback;
                enableWidget.callback = (...args) => {
                    if (orig) orig.apply(enableWidget, args);
                    updateLoraWidgets(this);
                };
            } else {
                console.warn(`${TAG} Enable widget not found!`);
            }
            
            if (countWidget) {
                const orig = countWidget.callback;
                countWidget.callback = (...args) => {
                    if (orig) orig.apply(countWidget, args);
                    updateLoraWidgets(this);
                };
            } else {
                 console.warn(`${TAG} Count widget not found!`);
            }
        };

        // 3. 通用值变化监听
        const onWidgetChanged = nodeType.prototype.onWidgetChanged;
        nodeType.prototype.onWidgetChanged = function () {
            if (onWidgetChanged) onWidgetChanged.apply(this, arguments);
            updateLoraWidgets(this);
        };
        
        // 4. 反序列化配置后触发
        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            if (onConfigure) onConfigure.apply(this, arguments);
            setTimeout(() => updateLoraWidgets(this), 50);
        };
    },
});
