import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoPortraitPhotographyPromptNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";

const ADVANCED_WIDGETS = ["👤 人物年龄", "🧑 人物设定", "🌏 人物地域", "🎬 场景", "🏃 动作与事件", "📸 景别", "🧭 机位与裁切", "🌿 前景", "🎨 色彩关系", "💡 光线", "🔮 主光学效果", "✨ 辅助光学效果", "💫 情绪状态", "💇 发型", "👗 服装造型", "🏮 民俗文化风格", "🌡️ 温度", "📝 最大输出令牌", "⌛ 请求超时"];

function nodeType(node) { return node?.comfyClass || node?.type || ""; }
function widget(node, name) { return node?.widgets?.find((item) => item.name === name) || null; }

function setWidgetHidden(node, name, hidden) {
    const target = widget(node, name);
    if (!target) return;
    if (!("__dapaoPortraitOriginalComputeSize" in target)) {
        target.__dapaoPortraitOriginalComputeSize = target.computeSize;
    }
    target.computeSize = hidden ? (() => [0, -4]) : target.__dapaoPortraitOriginalComputeSize;
    target.hidden = Boolean(hidden);
    const element = target.inputEl || target.element || target.domElement || target.inputElement;
    if (element?.style) element.style.display = hidden ? "none" : "";
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoPortraitRegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const old = widget(node, oldName);
        if (!old) continue;
        const index = node.widgets.indexOf(old);
        if (index >= 0) node.widgets.splice(index, 1);
    }
    const button = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_PORTRAIT_REGISTER_BUTTON",
        serialize: false,
        _hovered: false,
        _area: null,
        computeSize() { return [220, 40]; },
        draw(ctx, nodeRef, width, y, height) {
            const widgetWidth = Math.max(220, Number(nodeRef?.size?.[0]) || Number(width) || 220);
            const margin = 8;
            const buttonY = y + 3;
            const buttonHeight = Math.max(32, height - 6);
            ctx.save();
            ctx.fillStyle = this._hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath();
            ctx.roundRect(margin, buttonY, Math.max(1, widgetWidth - margin * 2), buttonHeight, 7);
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
            this._area = { x: margin, y: buttonY, width: Math.max(1, widgetWidth - margin * 2), height: buttonHeight };
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
            if (["pointerdown", "mousedown", "click"].includes(event.type) && inside) {
                const opened = window.open(REGISTER_URL, "_blank", "noopener,noreferrer");
                if (opened) opened.opener = null;
                return true;
            }
            return false;
        },
    };
    node.addCustomWidget(button);
    node.__dapaoPortraitRegisterWidget = button;
}

function refresh(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    if (!widget(node, "💰 LLM实际用量计费｜以平台账单为准")) {
        node.addCustomWidget({
            name: "💰 LLM实际用量计费｜以平台账单为准",
            type: "DAPAO_PORTRAIT_PRICE_LABEL",
            serialize: false,
            computeSize() { return [220, 24]; },
            draw(ctx, nodeRef, width, y) {
                const currentWidth = Number(nodeRef?.size?.[0]) || Number(width) || 430;
                ctx.save();
                ctx.font = "12px sans-serif";
                ctx.textAlign = "center";
                ctx.fillStyle = "#d8bd89";
                ctx.fillText(this.name, currentWidth / 2, y + 16);
                ctx.restore();
            },
        });
    }
    const expanded = Boolean(widget(node, "⚙️ 展开摄影参数")?.value);
    for (const name of ADVANCED_WIDGETS) setWidgetHidden(node, name, !expanded);
    if (node.computeSize) {
        const computed = node.computeSize();
        node.setSize([Math.max(430, Number(node.size?.[0]) || 0, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapWidget(node, target) {
    if (!target || target.__dapaoPortraitWrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refresh(node);
        return result;
    };
    target.__dapaoPortraitWrapped = true;
}

function setup(node) {
    if (!node?.widgets || nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    node.widgets.forEach((target) => wrapWidget(node, target));
    refresh(node);
}

function refreshAll() {
    app.graph?.findNodesByType(NODE_TYPE)?.forEach((node) => setup(node));
}

app.registerExtension({
    name: "Dapao.PortraitPhotographyPrompt.UI",
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
            this.color = "#171515";
            this.bgcolor = "#1e1a1a";
            setTimeout(() => setup(this), 20);
        };
        const added = nodeTypeClass.prototype.onAdded;
        nodeTypeClass.prototype.onAdded = function () {
            added?.apply(this, arguments);
            setTimeout(() => setup(this), 20);
        };
        const configured = nodeTypeClass.prototype.onConfigure;
        nodeTypeClass.prototype.onConfigure = function () {
            configured?.apply(this, arguments);
            setTimeout(() => setup(this), 50);
        };
        const changed = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () {
            const result = changed?.apply(this, arguments);
            refresh(this);
            return result;
        };
    },
});

console.log("[Dapao Portrait Photography Prompt UI] loaded");

