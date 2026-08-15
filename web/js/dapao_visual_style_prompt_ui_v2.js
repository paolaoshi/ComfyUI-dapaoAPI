import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoVisualStylePromptNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";
const CUSTOM_RULES = [
    ["🧩 创作任务", "✍️ 自定义创作任务"],
    ["🎨 视觉风格卡", "✍️ 自定义视觉风格"],
    ["🎯 使用场景", "✍️ 自定义使用场景"],
    ["🗂️ 视觉领域", "✍️ 自定义视觉领域"],
    ["🧭 构图与视角", "✍️ 自定义构图与视角"],
    ["📷 镜头与景深", "✍️ 自定义镜头与景深"],
    ["💡 光线", "✍️ 自定义光线"],
    ["🎨 配色", "✍️ 自定义配色"],
    ["🌫️ 画面氛围", "✍️ 自定义画面氛围"],
    ["🖼️ 参考图用途", "✍️ 自定义参考图用途"],
    ["🔤 画面文字策略", "✍️ 自定义画面文字策略"],
    ["🔒 核心保留策略", "✍️ 自定义核心保留策略"],
    ["🚫 避错策略", "✍️ 自定义避错策略"],
    ["🎚️ 风格改造强度", "✍️ 自定义风格改造强度"],
];
const ADVANCED_SELECTORS = new Set([
    "🗂️ 视觉领域", "🧭 构图与视角", "📷 镜头与景深", "💡 光线", "🎨 配色",
    "🌫️ 画面氛围", "🖼️ 参考图用途", "🔤 画面文字策略", "🔒 核心保留策略",
    "🚫 避错策略", "🎚️ 风格改造强度",
]);

function nodeType(node) { return node?.comfyClass || node?.type || ""; }
function widget(node, name) { return node?.widgets?.find((item) => item.name === name) || null; }
function boolValue(value, fallback = false) {
    if (value === undefined || value === null) return fallback;
    if (typeof value === "string") return ["1", "true", "yes", "on", "是", "开启"].includes(value.trim().toLowerCase());
    return Boolean(value);
}

function isCollapsedComputeSize(computeSize) {
    if (typeof computeSize !== "function") return false;
    try {
        const size = computeSize(480);
        return Array.isArray(size) && Number(size[1]) <= 0;
    } catch (_) {
        return false;
    }
}

function setWidgetHidden(node, name, hidden) {
    const target = widget(node, name);
    if (!target) return;
    if (!("__dapaoVisualStyleBaseComputeSize" in target)) {
        const legacy = target.__dapaoVisualStyleOriginalComputeSize;
        target.__dapaoVisualStyleBaseComputeSize = !isCollapsedComputeSize(legacy)
            ? legacy
            : (!isCollapsedComputeSize(target.computeSize) ? target.computeSize : undefined);
    }
    target.hidden = Boolean(hidden);
    target.computeSize = hidden
        ? (() => [0, -4])
        : target.__dapaoVisualStyleBaseComputeSize;
    const element = target.inputEl || target.element || target.domElement || target.inputElement;
    if (element?.style) element.style.display = hidden ? "none" : "";
}

function ensurePromptLayout(node) {
    const prompt = widget(node, "📝 原始视觉需求");
    if (!prompt) return;
    if (!("__dapaoVisualStylePromptBaseComputeSize" in prompt)) {
        prompt.__dapaoVisualStylePromptBaseComputeSize = prompt.computeSize;
        prompt.computeSize = function (width) {
            const base = typeof this.__dapaoVisualStylePromptBaseComputeSize === "function"
                ? this.__dapaoVisualStylePromptBaseComputeSize.call(this, width)
                : [width, 20];
            return [Math.max(Number(base?.[0]) || 0, Number(width) || 0), Math.max(126, Number(base?.[1]) || 0)];
        };
    }
    const element = prompt.inputEl || prompt.element || prompt.domElement || prompt.inputElement;
    if (element?.style) {
        element.style.minHeight = "104px";
        element.style.height = "104px";
        element.style.resize = "vertical";
    }
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoVisualStyleRegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const old = widget(node, oldName);
        if (!old) continue;
        const index = node.widgets.indexOf(old);
        if (index >= 0) node.widgets.splice(index, 1);
    }
    const button = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_VISUAL_STYLE_REGISTER_BUTTON",
        serialize: false,
        _hovered: false,
        _area: null,
        computeSize() { return [220, 40]; },
        draw(ctx, nodeRef, width, y, height) {
            const widgetWidth = Math.max(220, Number(nodeRef?.size?.[0]) || Number(width) || 220);
            const margin = 8;
            const buttonY = y + 3;
            const buttonHeight = Math.max(31, height - 6);
            ctx.save();
            const gradient = ctx.createLinearGradient(margin, buttonY, widgetWidth - margin, buttonY + buttonHeight);
            gradient.addColorStop(0, this._hovered ? "#dd8b21" : "#a96519");
            gradient.addColorStop(1, this._hovered ? "#b464db" : "#7d3ca3");
            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.roundRect(margin, buttonY, widgetWidth - margin * 2, buttonHeight, 9);
            ctx.fill();
            ctx.strokeStyle = this._hovered ? "#ffe48c" : "#d8a55f";
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.fillStyle = "#fff8df";
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
            const inside = pos[0] >= area.x && pos[0] <= area.x + area.width
                && pos[1] >= area.y && pos[1] <= area.y + area.height;
            if (event.type === "pointermove") {
                this._hovered = inside;
                nodeRef.setDirtyCanvas?.(true, true);
                return inside;
            }
            if (event.type === "pointerdown" && inside) {
                const opened = window.open(REGISTER_URL, "_blank");
                if (opened) opened.opener = null;
                return true;
            }
            return false;
        },
    };
    node.addCustomWidget(button);
    node.__dapaoVisualStyleRegisterWidget = button;
}

function refreshStyleChoices(node) {
    const domainWidget = widget(node, "🗂️ 视觉领域");
    const styleWidget = widget(node, "🎨 视觉风格卡");
    if (!domainWidget || !styleWidget?.options) return;
    if (!styleWidget.__dapaoVisualStyleAllValues) {
        styleWidget.__dapaoVisualStyleAllValues = [...(styleWidget.options.values || [])];
    }
    const domain = String(domainWidget.value || "自动识别");
    const all = styleWidget.__dapaoVisualStyleAllValues;
    const filtered = domain === "自动识别"
        ? all
        : ["自动选择", ...all.filter((item) => String(item).startsWith(`${domain}｜`) || String(item).startsWith("自定义（"))];
    styleWidget.options.values = filtered;
    if (!filtered.includes(styleWidget.value)) styleWidget.value = "自动选择";
}

function refresh(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    ensurePromptLayout(node);
    refreshStyleChoices(node);
    const retrieval = boolValue(widget(node, "🔎 真实提示词联网检索")?.value, false);
    setWidgetHidden(node, "🖼️ 联网参考数量", !retrieval);
    const advanced = boolValue(widget(node, "🎛️ 展开更多视觉控制")?.value, true);
    [
        "🗂️ 视觉领域",
        "🧭 构图与视角",
        "📷 镜头与景深",
        "💡 光线",
        "🎨 配色",
        "🌫️ 画面氛围",
        "🖼️ 参考图用途",
        "🔤 画面文字策略",
        "🔒 核心保留策略",
        "🚫 避错策略",
        "🎚️ 风格改造强度",
        "🧠 细节密度",
        "🎲 随机种",
        "🚫 出错时跳过",
    ].forEach((name) => setWidgetHidden(node, name, !advanced));
    for (const [selector, customField] of CUSTOM_RULES) {
        const selected = String(widget(node, selector)?.value || "");
        const show = selected.startsWith("自定义") && (!ADVANCED_SELECTORS.has(selector) || advanced);
        setWidgetHidden(node, customField, !show);
    }
    if (node.computeSize) {
        const computed = node.computeSize();
        node.setSize([Math.max(520, Number(node.size?.[0]) || 0, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrap(node, target) {
    if (!target || target.__dapaoVisualStyleWrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        setTimeout(() => refresh(node), 0);
        return result;
    };
    target.__dapaoVisualStyleWrapped = true;
}

function setup(node) {
    if (!node?.widgets || nodeType(node) !== NODE_TYPE) return;
    node.widgets.forEach((target) => wrap(node, target));
    refresh(node);
}

function refreshAll() {
    app.graph?.findNodesByType(NODE_TYPE)?.forEach((node) => setup(node));
}

app.registerExtension({
    name: "Dapao.VisualStylePrompt.UI",
    async setup() {
        api.addEventListener("hot_reload_update", () => [50, 250, 1000].forEach((delay) => setTimeout(refreshAll, delay)));
    },
    nodeCreated(node) {
        if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 20);
    },
    loadedGraphNode(node) {
        if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 50);
    },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        if (nodeData.name !== NODE_TYPE) return;
        const created = nodeTypeClass.prototype.onNodeCreated;
        nodeTypeClass.prototype.onNodeCreated = function () {
            created?.apply(this, arguments);
            this.color = "#261b2d";
            this.bgcolor = "#1c1721";
            setTimeout(() => setup(this), 20);
        };
        const added = nodeTypeClass.prototype.onAdded;
        nodeTypeClass.prototype.onAdded = function () {
            const result = added?.apply(this, arguments);
            setTimeout(() => setup(this), 20);
            return result;
        };
        const configured = nodeTypeClass.prototype.onConfigure;
        nodeTypeClass.prototype.onConfigure = function () {
            configured?.apply(this, arguments);
            setTimeout(() => setup(this), 50);
        };
        const changed = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () {
            const result = changed?.apply(this, arguments);
            setTimeout(() => refresh(this), 0);
            return result;
        };
    },
});

console.log("[Dapao Visual Style Prompt UI v2] loaded");
