import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoSeedance20DirectorNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";

function nodeType(node) { return node?.comfyClass || node?.type || ""; }
function widget(node, name) { return node?.widgets?.find((item) => item.name === name) || null; }
function value(node, name, fallback = "") { return widget(node, name)?.value ?? fallback; }
function setInputHidden(node, name, hidden) {
    const input = node?.inputs?.find((item) => item.name === name);
    if (input) input.hidden = Boolean(hidden);
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoSeedance20RegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const old = widget(node, oldName);
        if (old) {
            const index = node.widgets.indexOf(old);
            if (index >= 0) node.widgets.splice(index, 1);
        }
    }
    const button = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_SEEDANCE20_REGISTER_BUTTON",
        serialize: false,
        _hovered: false,
        _area: null,
        computeSize() { return [180, 38]; },
        draw(ctx, nodeRef, width, y, height) {
            const widgetWidth = Math.max(180, Number(nodeRef?.size?.[0]) || Number(width) || 180);
            const margin = 8, buttonY = y + 3, buttonHeight = Math.max(30, height - 6);
            ctx.save();
            ctx.fillStyle = this._hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath(); ctx.roundRect(margin, buttonY, widgetWidth - margin * 2, buttonHeight, 8); ctx.fill();
            ctx.strokeStyle = this._hovered ? "#ffd36a" : "#d49a42"; ctx.lineWidth = 1.5; ctx.stroke();
            ctx.fillStyle = "#fff7df"; ctx.font = "bold 13px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillText(REGISTER_WIDGET_NAME, widgetWidth / 2, buttonY + buttonHeight / 2); ctx.restore();
            this._area = { x: margin, y: buttonY, width: widgetWidth - margin * 2, height: buttonHeight };
        },
        mouse(event, pos, nodeRef) {
            const area = this._area;
            if (!area) return false;
            const inside = pos[0] >= area.x && pos[0] <= area.x + area.width && pos[1] >= area.y && pos[1] <= area.y + area.height;
            if (event.type === "pointermove") { this._hovered = inside; nodeRef.setDirtyCanvas?.(true, true); return inside; }
            if (["pointerdown", "mousedown", "click"].includes(event.type) && inside) { const opened = window.open(REGISTER_URL, "_blank"); if (opened) opened.opener = null; return true; }
            return false;
        },
    };
    node.addCustomWidget(button);
    node.__dapaoSeedance20RegisterWidget = button;
}

function refreshInputs(node) {
    const mode = String(value(node, "🎛️ Seedance任务", "自动识别"));
    const automatic = mode === "自动识别";
    const usesFirst = automatic || mode === "I2V-图生视频" || mode === "FLF2V-首尾帧" || mode === "R2V-全能参考";
    const usesLast = automatic || mode === "FLF2V-首尾帧" || mode === "R2V-全能参考";
    const usesRefs = automatic || ["V2V-视频参考", "R2V-全能参考", "Sequence-连续剧情", "Review-成片复盘", "Repair-失败修复"].includes(mode);
    const usesVideoAudio = automatic || ["V2V-视频参考", "R2V-全能参考", "Sequence-连续剧情", "Review-成片复盘", "Repair-失败修复"].includes(mode);
    setInputHidden(node, "🎬 首帧图", !usesFirst);
    setInputHidden(node, "🏁 尾帧图", !usesLast);
    for (let i = 1; i <= 9; i++) setInputHidden(node, `🖼️ 参考图${i}`, !usesRefs);
    for (let i = 1; i <= 3; i++) {
        setInputHidden(node, `🎞️ 参考视频${i}`, !usesVideoAudio);
        setInputHidden(node, `🎵 参考音频${i}`, !usesVideoAudio);
    }
    const stateVisible = ["自动识别", "Extend-视频续写", "Sequence-连续剧情", "Review-成片复盘", "Repair-失败修复"].includes(mode);
    setInputHidden(node, "📦 上一个项目状态JSON", !stateVisible);
    setInputHidden(node, "🎬 上一段成片观察", !stateVisible);
}

function refresh(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node); refreshInputs(node);
    if (node.computeSize) { const computed = node.computeSize(); node.setSize([Math.max(Number(node.size?.[0]) || 0, computed[0]), computed[1]]); }
    node.setDirtyCanvas?.(true, true);
}
function wrap(node, target) {
    if (!target || target.__dapaoSeedance20Wrapped) return;
    const original = target.callback;
    target.callback = function () { const result = original?.apply(this, arguments); refresh(node); return result; };
    target.__dapaoSeedance20Wrapped = true;
}
function setup(node) { if (!node?.widgets || nodeType(node) !== NODE_TYPE) return; ensureRegisterButton(node); node.widgets.forEach((target) => wrap(node, target)); refresh(node); }
function refreshAll() { app.graph?.findNodesByType(NODE_TYPE)?.forEach((node) => setup(node)); }

app.registerExtension({
    name: "Dapao.Seedance20Director.UI",
    async setup() { api.addEventListener("hot_reload_update", () => [50, 250, 1000].forEach((delay) => setTimeout(refreshAll, delay))); },
    nodeCreated(node) { if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 20); },
    loadedGraphNode(node) { if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 50); },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        if (nodeData.name !== NODE_TYPE) return;
        const originalCreated = nodeTypeClass.prototype.onNodeCreated;
        nodeTypeClass.prototype.onNodeCreated = function () { originalCreated?.apply(this, arguments); this.color = "#141416"; this.bgcolor = "#19191c"; setTimeout(() => setup(this), 20); };
        const originalAdded = nodeTypeClass.prototype.onAdded;
        nodeTypeClass.prototype.onAdded = function () { originalAdded?.apply(this, arguments); setTimeout(() => setup(this), 20); };
        const originalConfigure = nodeTypeClass.prototype.onConfigure;
        nodeTypeClass.prototype.onConfigure = function () { originalConfigure?.apply(this, arguments); setTimeout(() => setup(this), 50); };
        const originalChanged = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () { const result = originalChanged?.apply(this, arguments); refresh(this); return result; };
        const originalConnections = nodeTypeClass.prototype.onConnectionsChange;
        nodeTypeClass.prototype.onConnectionsChange = function () { const result = originalConnections?.apply(this, arguments); setTimeout(() => refresh(this), 0); return result; };
    },
});

console.log("[Dapao Seedance2 Director UI] loaded");
