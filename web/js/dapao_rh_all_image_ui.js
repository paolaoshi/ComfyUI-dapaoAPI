import { app } from "../../../scripts/app.js";

const TAG = "[Dapao RH Price UI]";
const RH_NODE_TYPES = new Set(["DapaoRHAllImageNode", "DapaoRHAllImageConcurrentNode", "DapaoRHAllVideoSeedanceNode"]);

const PRICE_MAP = {
    "全能图片G-2|官方稳定版|文生图|1k|low": "¥0.06/次",
    "全能图片G-2|官方稳定版|文生图|2k|low": "¥0.13/次",
    "全能图片G-2|官方稳定版|文生图|4k|low": "¥0.19/次",
    "全能图片G-2|官方稳定版|文生图|1k|medium": "¥0.38/次",
    "全能图片G-2|官方稳定版|文生图|2k|medium": "¥0.76/次",
    "全能图片G-2|官方稳定版|文生图|4k|medium": "¥1.13/次",
    "全能图片G-2|官方稳定版|文生图|1k|high": "¥1.39/次",
    "全能图片G-2|官方稳定版|文生图|2k|high": "¥2.77/次",
    "全能图片G-2|官方稳定版|文生图|4k|high": "¥4.16/次",
    "全能图片G-2|官方稳定版|图生图|1k|low": "¥0.19/次",
    "全能图片G-2|官方稳定版|图生图|2k|low": "¥0.38/次",
    "全能图片G-2|官方稳定版|图生图|4k|low": "¥0.57/次",
    "全能图片G-2|官方稳定版|图生图|1k|medium": "¥0.38/次",
    "全能图片G-2|官方稳定版|图生图|2k|medium": "¥0.76/次",
    "全能图片G-2|官方稳定版|图生图|4k|medium": "¥1.13/次",
    "全能图片G-2|官方稳定版|图生图|1k|high": "¥1.39/次",
    "全能图片G-2|官方稳定版|图生图|2k|high": "¥2.77/次",
    "全能图片G-2|官方稳定版|图生图|4k|high": "¥4.16/次",
    "全能图片G-2|低价渠道版|文生图|1k|none": "¥0.10/次",
    "全能图片G-2|低价渠道版|文生图|2k|none": "¥0.10/次",
    "全能图片G-2|低价渠道版|文生图|4k|none": "¥0.10/次",
    "全能图片G-2|低价渠道版|图生图|1k|none": "¥0.10/次",
    "全能图片G-2|低价渠道版|图生图|2k|none": "¥0.10/次",
    "全能图片G-2|低价渠道版|图生图|4k|none": "¥0.10/次",
    "全能图片V2|官方稳定版|文生图|1k|none": "¥0.49/次",
    "全能图片V2|官方稳定版|文生图|2k|none": "¥0.74/次",
    "全能图片V2|官方稳定版|文生图|4k|none": "¥0.99/次",
    "全能图片V2|官方稳定版|图生图|1k|none": "¥0.49/次",
    "全能图片V2|官方稳定版|图生图|2k|none": "¥0.74/次",
    "全能图片V2|官方稳定版|图生图|4k|none": "¥0.99/次",
    "全能图片V2|低价渠道版|文生图|1k|none": "¥0.16/次",
    "全能图片V2|低价渠道版|文生图|2k|none": "¥0.16/次",
    "全能图片V2|低价渠道版|文生图|4k|none": "¥0.20/次",
    "全能图片V2|低价渠道版|图生图|1k|none": "¥0.16/次",
    "全能图片V2|低价渠道版|图生图|2k|none": "¥0.16/次",
    "全能图片V2|低价渠道版|图生图|4k|none": "¥0.20/次",
    "全能图片PRO|官方稳定版|文生图|1k|none": "¥0.80/次",
    "全能图片PRO|官方稳定版|文生图|2k|none": "¥1.00/次",
    "全能图片PRO|官方稳定版|文生图|4k|none": "¥1.50/次",
    "全能图片PRO|官方稳定版|图生图|1k|none": "¥0.80/次",
    "全能图片PRO|官方稳定版|图生图|2k|none": "¥1.00/次",
    "全能图片PRO|官方稳定版|图生图|4k|none": "¥1.50/次",
    "全能图片PRO|低价渠道版|文生图|1k|none": "¥0.40/次",
    "全能图片PRO|低价渠道版|文生图|2k|none": "¥0.40/次",
    "全能图片PRO|低价渠道版|文生图|4k|none": "¥0.50/次",
    "全能图片PRO|低价渠道版|图生图|1k|none": "¥0.40/次",
    "全能图片PRO|低价渠道版|图生图|2k|none": "¥0.40/次",
    "全能图片PRO|低价渠道版|图生图|4k|none": "¥0.50/次",
};

function getWidget(node, name) {
    if (!node?.widgets) return null;
    return node.widgets.find((w) => w.name === name) || null;
}

function getValue(node, name, fallback = "") {
    const widget = getWidget(node, name);
    return widget?.value ?? fallback;
}

function isInputLinked(node, name) {
    const input = node?.inputs?.find((item) => item.name === name);
    return input?.link != null;
}

function getEffectiveTaskCount(node) {
    const promptText = String(getValue(node, "📝 提示词", ""));
    const promptLines = promptText.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
    if (promptLines.length > 1) return Math.min(100, promptLines.length);
    if (isInputLinked(node, "📝 提示词")) return 1;
    return Number(getValue(node, "🔢 任务数量", 1)) || 1;
}

function normalizeResolution(value, node) {
    if (value && value !== "模型默认") return value;
    const model = getValue(node, "🤖 模型", "全能图片G-2");
    const channel = getValue(node, "🏷️ 渠道", "官方稳定版");
    if (model === "全能图片G-2" && channel === "官方稳定版") return "2k";
    return "1k";
}

function normalizeQuality(value, node) {
    const model = getValue(node, "🤖 模型", "全能图片G-2");
    const channel = getValue(node, "🏷️ 渠道", "官方稳定版");
    if (model === "全能图片G-2" && channel === "官方稳定版") {
        if (value && value !== "模型默认") return value;
        return "medium";
    }
    return "none";
}

function getPriceText(node) {
    const currentModel = getValue(node, "🤖 模型", "");
    if (node?.comfyClass === "DapaoRHAllVideoSeedanceNode" || node?.type === "DapaoRHAllVideoSeedanceNode" || currentModel.startsWith("SEEDANCE2.0")) {
        return getVideoPriceText(node);
    }
    const model = currentModel || "全能图片G-2";
    const channel = getValue(node, "🏷️ 渠道", "官方稳定版");
    const mode = getValue(node, "🔀 模式", "文生图");
    const resolution = normalizeResolution(getValue(node, "🧩 分辨率", "模型默认"), node);
    const quality = normalizeQuality(getValue(node, "🎨 画质", "模型默认"), node);
    const key = `${model}|${channel}|${mode}|${resolution}|${quality}`;
    const noQualityKey = `${model}|${channel}|${mode}|${resolution}|none`;
    const unitPrice = PRICE_MAP[key] || PRICE_MAP[noQualityKey];
    if (!unitPrice) return "价格待补";

    const taskCount = getEffectiveTaskCount(node);
    if (taskCount <= 1) return unitPrice;

    const match = unitPrice.match(/¥([0-9.]+)\/次/);
    if (!match) return `${unitPrice} x${taskCount}`;
    return `约¥${(Number(match[1]) * taskCount).toFixed(2)}/${taskCount}次`;
}

function getVideoPriceText(node) {
    const model = getValue(node, "🤖 模型", "SEEDANCE2.0");
    const duration = String(getValue(node, "⏱️ 时长(秒)", "5"));
    const unit = model === "SEEDANCE2.0-FAST" ? 0.5 : 0.6;
    if (duration === "-1") return `¥${unit.toFixed(1)}/秒`;
    const seconds = Number(duration);
    if (!Number.isFinite(seconds) || seconds <= 0) return `¥${unit.toFixed(1)}/秒`;
    return `约¥${(unit * seconds).toFixed(2)}/${seconds}秒`;
}

function wrapWidgetCallback(node, widget) {
    if (!widget || widget._dapaoRhPriceWrapped) return;
    const original = widget.callback;
    widget.callback = function (...args) {
        const result = original?.apply(this, args);
        node.setDirtyCanvas(true, true);
        return result;
    };
    widget._dapaoRhPriceWrapped = true;
}

function setupPriceBadge(node) {
    if (!node?.widgets) return;
    ["🤖 模型", "🏷️ 渠道", "🔀 模式", "🧩 分辨率", "🎨 画质", "📝 提示词", "🔢 任务数量", "⏱️ 时长(秒)"].forEach((name) => {
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
    const badgeHeight = 28;
    const paddingX = 12;
    const fontSize = text === "价格待补" ? 15 : 18;
    ctx.save();
    ctx.font = `bold ${fontSize}px Arial, sans-serif`;
    const textWidth = ctx.measureText(text).width;
    const badgeWidth = Math.max(88, textWidth + paddingX * 2 + 28);
    const x = Math.max(12, node.size[0] - badgeWidth - 10);
    const y = -badgeHeight + 4;

    ctx.fillStyle = text === "价格待补" ? "#5f5f66" : "#9c6a28";
    drawRoundRect(ctx, x, y, badgeWidth, badgeHeight, 9);
    ctx.fill();

    ctx.fillStyle = text === "价格待补" ? "#d8d8dc" : "#ffbf35";
    ctx.beginPath();
    ctx.arc(x + 18, y + badgeHeight / 2, 10, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = text === "价格待补" ? "#5f5f66" : "#7b4616";
    ctx.font = "bold 18px Arial, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(text === "价格待补" ? "?" : "¥", x + 18, y + badgeHeight / 2 + 1);

    ctx.fillStyle = "#ffffff";
    ctx.font = `bold ${fontSize}px Arial, sans-serif`;
    ctx.textAlign = "left";
    ctx.fillText(text, x + 34, y + badgeHeight / 2 + 1);
    ctx.restore();
}

app.registerExtension({
    name: "Dapao.RHAllImage.PriceBadge",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (!RH_NODE_TYPES.has(nodeData.name)) return;

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
            drawPriceBadge(this, ctx);
        };
    },
});

console.log(`${TAG} loaded`);
