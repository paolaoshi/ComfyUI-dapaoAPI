import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoWan30AllroundVideoNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_NAME = "👉点此注册API密钥👈";
const VIDEO_MODEL = "wan3.0-video";

function nodeType(node) { return node?.comfyClass || node?.type || ""; }
function widget(node, name) { return node?.widgets?.find(item => item.name === name) || null; }
function value(node, name, fallback = "") { return widget(node, name)?.value ?? fallback; }
function setInputHidden(node, name, hidden) {
    const target = node?.inputs?.find(item => item.name === name);
    if (target) target.hidden = Boolean(hidden);
}
function isPress(event) {
    const type = String(event?.type || "");
    const liteDown = globalThis.LiteGraph?.pointerevents_method
        ? `${globalThis.LiteGraph.pointerevents_method}down` : "";
    return ["pointerdown", "mousedown", "click", liteDown].includes(type);
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__wan30Register) return;
    for (const name of ["点击此处注册API密钥", REGISTER_NAME]) {
        const old = widget(node, name);
        const index = old ? node.widgets.indexOf(old) : -1;
        if (index >= 0) node.widgets.splice(index, 1);
    }
    const button = {
        name: REGISTER_NAME, type: "DAPAO_WAN30_REGISTER", serialize: false,
        _area: null, _hovered: false,
        computeSize() { return [220, 38]; },
        draw(ctx, nodeRef, width, y, height) {
            const liveWidth = Math.max(220, Number(nodeRef?.size?.[0]) || Number(width) || 220);
            const x = 8, top = y + 3, buttonHeight = Math.max(30, height - 6), buttonWidth = liveWidth - 16;
            ctx.save();
            ctx.fillStyle = this._hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath(); ctx.roundRect(x, top, buttonWidth, buttonHeight, 8); ctx.fill();
            ctx.strokeStyle = this._hovered ? "#ffd36a" : "#d49a42"; ctx.lineWidth = 1.5; ctx.stroke();
            ctx.fillStyle = "#fff7df"; ctx.font = "bold 13px sans-serif";
            ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillText(REGISTER_NAME, liveWidth / 2, top + buttonHeight / 2); ctx.restore();
            this._area = { x, y: top, width: buttonWidth, height: buttonHeight };
        },
        mouse(event, pos, nodeRef) {
            const a = this._area;
            if (!a) return false;
            const inside = pos[0] >= a.x && pos[0] <= a.x + a.width && pos[1] >= a.y && pos[1] <= a.y + a.height;
            if (event?.type === "pointermove") {
                this._hovered = inside; nodeRef.setDirtyCanvas?.(true, true); return inside;
            }
            if (inside && isPress(event)) {
                const opened = window.open(REGISTER_URL, "_blank", "noopener,noreferrer");
                if (opened) opened.opener = null;
                return true;
            }
            return false;
        },
    };
    node.addCustomWidget(button);
    node.__wan30Register = button;
}

function ensurePriceLabel(node) {
    if (!node?.addCustomWidget || node.__wan30Price) return;
    const label = {
        name: "💰 按服务端最终输出秒数和模型价格结算", type: "DAPAO_WAN30_PRICE", serialize: false,
        computeSize() { return [220, 24]; },
        draw(ctx, nodeRef, width, y) {
            const liveWidth = Number(nodeRef?.size?.[0]) || Number(width) || 420;
            ctx.save(); ctx.fillStyle = "#d8bd89"; ctx.font = "12px sans-serif";
            ctx.textAlign = "center"; ctx.fillText(this.name, liveWidth / 2, y + 16); ctx.restore();
        },
    };
    node.addCustomWidget(label); node.__wan30Price = label;
}

function refresh(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node); ensurePriceLabel(node);
    const mode = String(value(node, "🎛️ 生成模式", "文生视频"));
    const model = String(value(node, "🤖 模型", "wan3.0"));
    const imageMode = mode === "图生视频";
    const frameMode = mode === "首尾帧生视频";
    const referenceMode = mode === "多模态参考";
    setInputHidden(node, "🎬 首帧图", !(imageMode || frameMode));
    setInputHidden(node, "🏁 尾帧图", !frameMode);
    for (let i = 1; i <= 10; i++) setInputHidden(node, `🖼️ 参考图${i}`, !referenceMode);
    for (let i = 1; i <= 5; i++) {
        setInputHidden(node, `🎵 参考音频${i}`, !referenceMode);
        setInputHidden(node, `🎞️ 参考视频${i}`, !(referenceMode && model === VIDEO_MODEL));
    }
    if (node.computeSize) {
        const size = node.computeSize();
        node.setSize([Math.max(430, Number(node.size?.[0]) || 0, size[0]), size[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function setup(node) {
    if (!node?.widgets || nodeType(node) !== NODE_TYPE) return;
    for (const target of node.widgets) {
        if (target.__wan30Wrapped) continue;
        const original = target.callback;
        target.callback = function () {
            const result = original?.apply(this, arguments); refresh(node); return result;
        };
        target.__wan30Wrapped = true;
    }
    refresh(node);
}

function migrateWidgetValues(config) {
    const values = Array.isArray(config?.widgets_values) ? [...config.widgets_values] : null;
    if (!values) return config;
    const isJsonBox = item => typeof item === "string" && String(item).trim().startsWith("{");
    if (isJsonBox(values[8]) && isJsonBox(values[9])) {
        values.splice(8, 2, 0, "randomize");
        return { ...config, widgets_values: values };
    }
    return config;
}

function refreshAll() { app.graph?.findNodesByType(NODE_TYPE)?.forEach(setup); }

app.registerExtension({
    name: "Dapao.Wan30AllroundVideo.UI",
    async setup() { api.addEventListener("hot_reload_update", () => [50, 250, 1000].forEach(ms => setTimeout(refreshAll, ms))); },
    nodeCreated(node) { if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 20); },
    loadedGraphNode(node) { if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 50); },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        if (nodeData.name !== NODE_TYPE) return;
        for (const name of ["onNodeCreated", "onAdded", "onConfigure"]) {
            const original = nodeTypeClass.prototype[name];
            nodeTypeClass.prototype[name] = function () {
                const args = Array.from(arguments);
                if (name === "onConfigure" && args[0]) args[0] = migrateWidgetValues(args[0]);
                const result = original?.apply(this, args);
                this.color = "#141416"; this.bgcolor = "#19191c";
                setTimeout(() => setup(this), name === "onConfigure" ? 50 : 20); return result;
            };
        }
        const changed = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () {
            const result = changed?.apply(this, arguments); refresh(this); return result;
        };
        const connections = nodeTypeClass.prototype.onConnectionsChange;
        nodeTypeClass.prototype.onConnectionsChange = function () {
            const result = connections?.apply(this, arguments); setTimeout(() => refresh(this), 0); return result;
        };
    },
});

console.log("[Dapao Wan 3.0 Allround Video UI] loaded");
