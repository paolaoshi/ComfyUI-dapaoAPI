import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoGPTImage2AllroundNode";
const PRICES = { "1K": 0.06, "2K": 0.12, "4K": 0.18 };
const MODEL_PRICES = { "image-2官方稳定全分辨率": 0.60 };
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

function setWidgetHidden(node, name, hidden) {
    const target = widget(node, name);
    if (target) target.hidden = Boolean(hidden);
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoRegisterWidget) return;
    for (const legacyName of ["点击此处注册API密钥", "👉点此注册API密钥👈"]) {
        const legacyWidget = widget(node, legacyName);
        if (legacyWidget) {
            const legacyIndex = node.widgets.indexOf(legacyWidget);
            if (legacyIndex >= 0) node.widgets.splice(legacyIndex, 1);
        }
    }
    const registerWidget = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_REGISTER_BUTTON",
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
            const radius = 8;
            ctx.save();
            ctx.fillStyle = this._hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath();
            ctx.roundRect(margin, buttonY, widgetWidth - margin * 2, buttonHeight, radius);
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
    node.__dapaoRegisterWidget = registerWidget;
}

function refreshNode(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    const asyncMode = Boolean(value(node, "⚡ 异步模式", false));

    // 新版本已移除“模式”控件，模式只由实际图像连线自动决定。
    const legacyModeWidget = widget(node, "🔀 模式");
    if (legacyModeWidget) {
        const legacyIndex = node.widgets.indexOf(legacyModeWidget);
        if (legacyIndex >= 0) node.widgets.splice(legacyIndex, 1);
    }
    setWidgetHidden(node, "🔁 最大轮询秒数", !asyncMode);
    setWidgetHidden(node, "⏱️ 轮询间隔", !asyncMode);

    if (node.computeSize) {
        const computed = node.computeSize();
        const currentWidth = Number(node.size?.[0]) || computed[0];
        node.setSize([Math.max(currentWidth, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapCallback(node, target) {
    if (!target || target.__dapaoImage2AllroundWrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refreshNode(node);
        return result;
    };
    target.__dapaoImage2AllroundWrapped = true;
}

function setup(node) {
    if (!node?.widgets || nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    node.widgets.forEach((target) => wrapCallback(node, target));
    refreshNode(node);
}

function priceText(node) {
    const model = String(value(node, "🤖 模型", "image-2"));
    const resolution = String(value(node, "🧩 清晰度", "1K"));
    const count = Math.max(1, Number(value(node, "🖼️ 出图数量", 1)) || 1);
    const unitPrice = MODEL_PRICES[model] ?? PRICES[resolution];
    if (!unitPrice) return "价格待补";
    const total = (unitPrice * count).toFixed(2);
    return count === 1 ? `¥${total}/张` : `¥${total}/${count}张`;
}

function roundRect(ctx, x, y, width, height, radius) {
    const r = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + width - r, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + r);
    ctx.lineTo(x + width, y + height - r);
    ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
    ctx.lineTo(x + r, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
}

// 保持与截图参考节点相同的右上角价格标签绘制实现。
function drawBadge(node, ctx) {
    const text = priceText(node);
    ctx.save();
    ctx.font = "bold 14px Arial, sans-serif";
    const width = Math.max(82, ctx.measureText(text).width + 36);
    const height = 24;
    const x = Math.max(12, node.size[0] - width - 10);
    const y = -height + 4;
    ctx.fillStyle = text === "价格待补" ? "#5f5f66" : "#9c6a28";
    roundRect(ctx, x, y, width, height, 8);
    ctx.fill();
    ctx.fillStyle = text === "价格待补" ? "#d8d8dc" : "#ffbf35";
    ctx.beginPath();
    ctx.arc(x + 13, y + height / 2, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = text === "价格待补" ? "#5f5f66" : "#7b4616";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "bold 14px Arial, sans-serif";
    ctx.fillText(text === "价格待补" ? "?" : "¥", x + 13, y + height / 2 + 0.5);
    ctx.fillStyle = "#fff";
    ctx.textAlign = "left";
    ctx.fillText(text, x + 26, y + height / 2 + 0.5);
    ctx.restore();
}

function refreshAllNodes() {
    app.graph?.findNodesByType(NODE_TYPE)?.forEach((node) => setup(node));
}

app.registerExtension({
    name: "Dapao.GPTImage2Allround.UI",
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
            if (values && ["文生图", "图生图"].includes(String(values[2]))) {
                values.splice(2, 1);
            }
            // 旧版在随机种后保存“额外参数JSON”；删除它，避免轮询参数整体错位。
            if (values && typeof values[9] === "string" && String(values[9]).trim().startsWith("{")) {
                values.splice(9, 1);
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

        const onDrawForeground = nodeTypeClass.prototype.onDrawForeground;
        nodeTypeClass.prototype.onDrawForeground = function (ctx) {
            onDrawForeground?.apply(this, arguments);
            drawBadge(this, ctx);
        };
    },
});

console.log("[Dapao GPT Image 2 Allround UI] loaded");
