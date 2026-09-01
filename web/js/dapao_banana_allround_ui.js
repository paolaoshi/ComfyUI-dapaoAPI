import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoBananaAllroundNode";
const ASPECT_RATIOS = {
    "bananaPRO": ["模型默认", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
    "bannana-2": ["模型默认", "16:9", "4:3", "4:5", "3:2", "1:1", "2:3", "3:4", "5:4", "9:16", "21:9", "1:4", "4:1", "1:8", "8:1"],
    "香蕉pro官方稳定版": ["模型默认", "1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"],
    "香蕉2官方稳定版": ["模型默认", "16:9", "4:3", "4:5", "3:2", "1:1", "2:3", "3:4", "5:4", "9:16", "21:9", "1:4", "4:1", "1:8", "8:1"],
};
const RESOLUTIONS = {
    "bananaPRO": ["1K", "2K", "4K"],
    "bannana-2": ["1K", "2K", "4K"],
    "香蕉pro官方稳定版": ["1K", "2K", "4K"],
    "香蕉2官方稳定版": ["1K", "2K", "4K"],
};
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";

function nodeType(node) {
    return node?.comfyClass || node?.type || "";
}

function widget(node, name) {
    return node?.widgets?.find((item) => item.name === name) || null;
}

function value(node, name, fallback = "") {
    return widget(node, name)?.value ?? fallback;
}

function setComboValues(target, values, fallback) {
    if (!target || !Array.isArray(values) || values.length === 0) return;
    target.options ??= {};
    target.options.values = [...values];
    if (!values.includes(String(target.value))) {
        target.value = values.includes(fallback) ? fallback : values[0];
    }
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoBananaRegisterWidget) return;
    for (const legacyName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const legacyWidget = widget(node, legacyName);
        if (legacyWidget) {
            const legacyIndex = node.widgets.indexOf(legacyWidget);
            if (legacyIndex >= 0) node.widgets.splice(legacyIndex, 1);
        }
    }
    const registerWidget = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_BANANA_REGISTER_BUTTON",
        serialize: false,
        _hovered: false,
        _area: null,
        computeSize() {
            return [160, 38];
        },
        draw(ctx, nodeRef, width, y, height) {
            const widgetWidth = Math.max(160, Number(nodeRef?.size?.[0]) || Number(width) || 160);
            const margin = 8;
            const buttonY = y + 3;
            const buttonHeight = Math.max(30, height - 6);
            ctx.save();
            ctx.fillStyle = this._hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath();
            ctx.roundRect(margin, buttonY, widgetWidth - margin * 2, buttonHeight, 8);
            ctx.fill();
            ctx.strokeStyle = this._hovered ? "#ffd36a" : "#d49a42";
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.fillStyle = "#fff7df";
            ctx.font = "bold 13px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(REGISTER_WIDGET_NAME, widgetWidth / 2, buttonY + buttonHeight / 2);
            ctx.restore();
            this._area = { x: margin, y: buttonY, width: widgetWidth - margin * 2, height: buttonHeight };
        },
        mouse(event, pos, nodeRef) {
            const area = this._area;
            if (!area) return false;
            const inside = pos[0] >= area.x && pos[0] <= area.x + area.width &&
                pos[1] >= area.y && pos[1] <= area.y + area.height;
            if (event.type === "pointermove") {
                this._hovered = inside;
                nodeRef.setDirtyCanvas?.(true, true);
                return inside;
            }
            if (["pointerdown", "mousedown", "click"].includes(event.type) && inside) {
                const opened = window.open(REGISTER_URL, "_blank");
                if (opened) opened.opener = null;
                return true;
            }
            return false;
        },
    };
    node.addCustomWidget(registerWidget);
    node.__dapaoBananaRegisterWidget = registerWidget;
}

function refreshNode(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    // Gemini 原生图像协议没有 quality 参数；热更新时移除旧节点遗留控件，不保留占位。
    const legacyQualityWidget = widget(node, "🎨 画质");
    if (legacyQualityWidget) {
        const legacyIndex = node.widgets.indexOf(legacyQualityWidget);
        if (legacyIndex >= 0) node.widgets.splice(legacyIndex, 1);
    }
    const model = String(value(node, "🤖 模型", "bananaPRO"));
    setComboValues(widget(node, "📐 图片尺寸/比例"), ASPECT_RATIOS[model] || ASPECT_RATIOS.bananaPRO, "模型默认");
    setComboValues(widget(node, "🧩 清晰度"), RESOLUTIONS[model] || RESOLUTIONS.bananaPRO, "1K");
    ensureRegisterButton(node);
    if (node.computeSize) {
        const computed = node.computeSize();
        const currentWidth = Number(node.size?.[0]) || computed[0];
        node.setSize([Math.max(currentWidth, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapCallback(node, target) {
    if (!target || target.__dapaoBananaAllroundWrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refreshNode(node);
        return result;
    };
    target.__dapaoBananaAllroundWrapped = true;
}

function setup(node) {
    if (!node?.widgets || nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    node.widgets.forEach((target) => wrapCallback(node, target));
    refreshNode(node);
}

function refreshAllNodes() {
    app.graph?.findNodesByType(NODE_TYPE)?.forEach((node) => setup(node));
}

app.registerExtension({
    name: "Dapao.BananaAllround.UI",
    async setup() {
        api.addEventListener("hot_reload_update", () => {
            [50, 250, 1000].forEach((delay) => setTimeout(refreshAllNodes, delay));
        });
    },
    nodeCreated(node) {
        if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 20);
    },
    loadedGraphNode(node) {
        if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 50);
    },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        if (nodeData.name !== NODE_TYPE) return;

        const onNodeCreated = nodeTypeClass.prototype.onNodeCreated;
        nodeTypeClass.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            this.color = "#141416";
            this.bgcolor = "#19191c";
            setTimeout(() => setup(this), 20);
        };

        const onAdded = nodeTypeClass.prototype.onAdded;
        nodeTypeClass.prototype.onAdded = function () {
            onAdded?.apply(this, arguments);
            setTimeout(() => setup(this), 20);
        };

        const onConfigure = nodeTypeClass.prototype.onConfigure;
        nodeTypeClass.prototype.onConfigure = function () {
            const config = arguments[0];
            let values = Array.isArray(config?.widgets_values) ? [...config.widgets_values] : null;
            const qualityValues = ["低画质", "标准画质", "高画质"];
            if (values && qualityValues.includes(String(values[5]))) {
                values.splice(5, 1);
            }
            // 旧版在随机种后保存“额外参数JSON”；删除它，避免请求超时控件错位。
            if (values && typeof values[8] === "string" && String(values[8]).trim().startsWith("{")) {
                values.splice(8, 1);
            }
            if (values) {
                const args = Array.from(arguments);
                args[0] = { ...config, widgets_values: values };
                onConfigure?.apply(this, args);
            } else {
                onConfigure?.apply(this, arguments);
            }
            setTimeout(() => setup(this), 50);
        };

        const onWidgetChanged = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () {
            const result = onWidgetChanged?.apply(this, arguments);
            refreshNode(this);
            return result;
        };

        const onConnectionsChange = nodeTypeClass.prototype.onConnectionsChange;
        nodeTypeClass.prototype.onConnectionsChange = function () {
            const result = onConnectionsChange?.apply(this, arguments);
            setTimeout(() => refreshNode(this), 0);
            return result;
        };

    },
});

console.log("[Dapao Banana Allround UI] loaded");
