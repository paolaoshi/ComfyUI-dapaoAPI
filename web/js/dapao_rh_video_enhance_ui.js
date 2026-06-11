import { app } from "../../../scripts/app.js";

const TAG = "[Dapao RH Video Enhance Price UI]";
const NODE_TYPE = "DapaoRHVideoEnhanceNode";

function getWidget(node, name) {
    if (!node?.widgets) return null;
    return node.widgets.find((w) => w.name === name) || null;
}

function getValue(node, name, fallback = "") {
    const widget = getWidget(node, name);
    return widget?.value ?? fallback;
}

function isTargetNode(node) {
    const typeName = node?.comfyClass || node?.type || node?.constructor?.nodeData?.name || "";
    return typeName === NODE_TYPE;
}

function getPriceText(node) {
    const upscaleTarget = getValue(node, "🧩 超分目标", "1080p");
    const fpsMode = getValue(node, "🎞️ 帧率增强", "不启用");
    const unit = (upscaleTarget !== "不启用" ? 0.14 : 0) + (fpsMode !== "不启用" ? 0.07 : 0);
    if (unit <= 0) return "请选择增强";
    return `¥${unit.toFixed(2)}/秒`;
}

function wrapWidgetCallback(node, widget) {
    if (!widget || widget._dapaoRhVideoEnhancePriceWrapped) return;
    const original = widget.callback;
    widget.callback = function (...args) {
        const result = original?.apply(this, args);
        node.setDirtyCanvas(true, true);
        return result;
    };
    widget._dapaoRhVideoEnhancePriceWrapped = true;
}

function setupPriceBadge(node) {
    if (!isTargetNode(node)) return;
    ["🧩 超分目标", "🎞️ 帧率增强"].forEach((name) => {
        wrapWidgetCallback(node, getWidget(node, name));
    });
    node.setDirtyCanvas(true, true);
}

function drawRoundRect(ctx, x, y, width, height, radius) {
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

function drawPriceBadge(node, ctx) {
    const text = getPriceText(node);
    const muted = text === "请选择增强";
    const badgeHeight = 28;
    const paddingX = 12;
    const fontSize = muted ? 15 : 18;

    ctx.save();
    ctx.font = `bold ${fontSize}px Arial, sans-serif`;
    const textWidth = ctx.measureText(text).width;
    const badgeWidth = Math.max(92, textWidth + paddingX * 2 + 28);
    const x = Math.max(12, node.size[0] - badgeWidth - 10);
    const y = -badgeHeight + 4;

    ctx.fillStyle = muted ? "#5f5f66" : "#9c6a28";
    drawRoundRect(ctx, x, y, badgeWidth, badgeHeight, 9);
    ctx.fill();

    ctx.fillStyle = muted ? "#d8d8dc" : "#ffbf35";
    ctx.beginPath();
    ctx.arc(x + 18, y + badgeHeight / 2, 10, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = muted ? "#5f5f66" : "#7b4616";
    ctx.font = "bold 18px Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(muted ? "?" : "¥", x + 18, y + badgeHeight / 2 + 1);

    ctx.fillStyle = "#ffffff";
    ctx.font = `bold ${fontSize}px Arial, sans-serif`;
    ctx.textAlign = "left";
    ctx.fillText(text, x + 34, y + badgeHeight / 2 + 1);
    ctx.restore();
}

function patchNodeInstance(node) {
    if (!isTargetNode(node) || node._dapaoRhPriceInstancePatched) return;
    const onDrawForeground = node.onDrawForeground;
    node.onDrawForeground = function (ctx) {
        onDrawForeground?.apply(this, arguments);
        drawPriceBadge(this, ctx);
    };
    node._dapaoRhPriceInstancePatched = true;
    setupPriceBadge(node);
}

app.registerExtension({
    name: "Dapao.RHVideoEnhance.PriceBadge",
    setup() {
        setTimeout(() => {
            app.graph?._nodes?.forEach((node) => patchNodeInstance(node));
            app.canvas?.setDirty(true, true);
        }, 100);
    },
    nodeCreated(node) {
        patchNodeInstance(node);
    },
    loadedGraphNode(node) {
        patchNodeInstance(node);
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_TYPE) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            setTimeout(() => setupPriceBadge(this), 10);
        };

        const onAdded = nodeType.prototype.onAdded;
        nodeType.prototype.onAdded = function () {
            onAdded?.apply(this, arguments);
            setupPriceBadge(this);
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            onConfigure?.apply(this, arguments);
            setTimeout(() => setupPriceBadge(this), 50);
        };

        const onDrawForeground = nodeType.prototype.onDrawForeground;
        nodeType.prototype.onDrawForeground = function (ctx) {
            onDrawForeground?.apply(this, arguments);
            if (!this._dapaoRhPriceInstancePatched) {
                drawPriceBadge(this, ctx);
            }
        };
    },
});

console.log(`${TAG} loaded`);
