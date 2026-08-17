import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoMusic3CaptionPromptNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";

const CUSTOM_RULES = [
    ["🎼 主风格", "✍️ 自定义主风格"],
    ["🧬 融合风格", "✍️ 自定义融合风格"],
    ["🎯 使用场景", "✍️ 自定义使用场景"],
    ["⏳ 目标曲长", "✍️ 自定义目标曲长"],
    ["💫 情绪弧", "✍️ 自定义情绪弧"],
    ["⏱️ 速度", "✍️ 自定义速度"],
    ["🎹 调性倾向", "✍️ 自定义调性倾向"],
    ["🎚️ 拍号/律动", "✍️ 自定义拍号/律动"],
    ["🥁 核心律动", "✍️ 自定义核心律动"],
    ["🎙️ 人声配置", "✍️ 自定义人声配置"],
    ["📈 人声音域", "✍️ 自定义人声音域"],
    ["🗣️ 人声音色", "✍️ 自定义人声音色"],
    ["🎤 演唱方式", "✍️ 自定义演唱方式"],
    ["👥 和声/伴唱", "✍️ 自定义和声/伴唱"],
    ["🎻 核心乐器编制", "✍️ 自定义乐器编制"],
    ["🧱 歌曲结构", "✍️ 自定义歌曲结构"],
    ["🎛️ 制作质感", "✍️ 自定义制作质感"],
    ["🌌 空间与混响", "✍️ 自定义空间与混响"],
    ["🔥 编曲密度", "✍️ 自定义编曲密度"],
    ["🚫 排除项", "✍️ 自定义排除项"],
    ["📏 输出详略", "✍️ 自定义输出详略"],
];

function nodeType(node) { return node?.comfyClass || node?.type || ""; }
function widget(node, name) { return node?.widgets?.find((item) => item.name === name) || null; }

function setWidgetHidden(node, name, hidden) {
    const target = widget(node, name);
    if (!target) return;
    if (!("__dapaoMusic3OriginalComputeSize" in target)) {
        target.__dapaoMusic3OriginalComputeSize = target.computeSize;
    }
    target.computeSize = hidden ? (() => [0, -4]) : target.__dapaoMusic3OriginalComputeSize;
    target.hidden = Boolean(hidden);
    const element = target.inputEl || target.element || target.domElement || target.inputElement;
    if (element?.style) element.style.display = hidden ? "none" : "";
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoMusic3RegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const old = widget(node, oldName);
        if (!old) continue;
        const index = node.widgets.indexOf(old);
        if (index >= 0) node.widgets.splice(index, 1);
    }
    const button = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_MUSIC3_REGISTER_BUTTON",
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
            if (event.type === "pointerdown" && inside) {
                const opened = window.open(REGISTER_URL, "_blank", "noopener,noreferrer");
                if (opened) opened.opener = null;
                return true;
            }
            return false;
        },
    };
    node.addCustomWidget(button);
    node.__dapaoMusic3RegisterWidget = button;
}

function refresh(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    // Keep the serialized slot for old workflows, but the node now always
    // emits a direct Music3 caption + lyrics pair.
    setWidgetHidden(node, "📦 输出格式", true);
    for (const [selectorName, customName] of CUSTOM_RULES) {
        const selected = String(widget(node, selectorName)?.value || "");
        setWidgetHidden(node, customName, selected !== "自定义");
    }
    if (node.computeSize) {
        const computed = node.computeSize();
        node.setSize([Math.max(430, Number(node.size?.[0]) || 0, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapWidget(node, target) {
    if (!target || target.__dapaoMusic3Wrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refresh(node);
        return result;
    };
    target.__dapaoMusic3Wrapped = true;
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
    name: "Dapao.Music3CaptionPrompt.UI",
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

console.log("[Dapao Music3 Caption Prompt UI] loaded");
