import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoH3VideoPromptNode";
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

function setInputHidden(node, name, hidden) {
    const target = node?.inputs?.find((item) => item.name === name);
    if (target) target.hidden = Boolean(hidden);
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoH3RegisterWidget) return;

    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const oldWidget = widget(node, oldName);
        if (!oldWidget) continue;
        const index = node.widgets.indexOf(oldWidget);
        if (index >= 0) node.widgets.splice(index, 1);
    }

    const registerWidget = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_H3_REGISTER_BUTTON",
        serialize: false,
        _hovered: false,
        _area: null,
        computeSize(width) {
            return [Math.max(180, width), 38];
        },
        draw(ctx, nodeRef, width, y, height) {
            const margin = 8;
            const buttonY = y + 3;
            const buttonHeight = Math.max(30, height - 6);
            ctx.save();
            ctx.fillStyle = this._hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath();
            ctx.roundRect(margin, buttonY, width - margin * 2, buttonHeight, 8);
            ctx.fill();
            ctx.strokeStyle = this._hovered ? "#ffd36a" : "#d49a42";
            ctx.lineWidth = 1.5;
            ctx.stroke();
            ctx.fillStyle = "#fff7df";
            ctx.font = "bold 13px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(REGISTER_WIDGET_NAME, width / 2, buttonY + buttonHeight / 2);
            ctx.restore();
            this._area = { x: margin, y: buttonY, width: width - margin * 2, height: buttonHeight };
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

    node.addCustomWidget(registerWidget);
    node.__dapaoH3RegisterWidget = registerWidget;
}

function refreshImageInputs(node) {
    const mode = String(value(node, "🎛️ H3生成模式", "自动识别"));
    const autoMode = mode === "自动识别";
    const refMode = mode === "Ref2VA-全能参考";
    const showFirst = autoMode || mode === "I2VA-首帧生视频" || mode === "FL2VA-首尾帧生视频";
    const showLast = autoMode || mode === "L2VA-尾帧生视频" || mode === "FL2VA-首尾帧生视频";
    const showReferences = autoMode || refMode;
    const showVideoAudio = autoMode || refMode;

    setInputHidden(node, "🎬 首帧图", !showFirst);
    setInputHidden(node, "🏁 尾帧图", !showLast);
    for (let index = 1; index <= 9; index++) {
        setInputHidden(node, `🖼️ 参考图${index}`, !showReferences);
    }
    for (let index = 1; index <= 3; index++) {
        setInputHidden(node, `🎞️ 参考视频${index}`, !showVideoAudio);
        setInputHidden(node, `🎵 参考音频${index}`, !showVideoAudio);
    }
}

function refreshNode(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    refreshImageInputs(node);
    ensureRegisterButton(node);
    if (node.computeSize) {
        const computed = node.computeSize();
        const currentWidth = Number(node.size?.[0]) || computed[0];
        node.setSize([Math.max(currentWidth, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapCallback(node, target) {
    if (!target || target.__dapaoH3Wrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refreshNode(node);
        return result;
    };
    target.__dapaoH3Wrapped = true;
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
    name: "Dapao.H3VideoPrompt.UI",
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
            onConfigure?.apply(this, arguments);
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

console.log("[Dapao H3 Video Prompt UI] loaded");
