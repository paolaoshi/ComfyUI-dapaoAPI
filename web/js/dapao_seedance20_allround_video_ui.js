import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoSeedance20AllroundVideoNode";
const FACE_MODEL = "SD2-face";
const DEFAULT_NON_FACE_MODEL = "SD2.0-mini";
const SUPPORTED_MODELS = new Set([FACE_MODEL, DEFAULT_NON_FACE_MODEL, "SD2-fast"]);
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
    if (!node?.addCustomWidget || node.__dapaoSeedance20RegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const oldWidget = widget(node, oldName);
        if (oldWidget) {
            const index = node.widgets.indexOf(oldWidget);
            if (index >= 0) node.widgets.splice(index, 1);
        }
    }
    const registerWidget = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_SEEDANCE20_REGISTER_BUTTON",
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
    node.__dapaoSeedance20RegisterWidget = registerWidget;
}

function syncModelControls(node, sourceName = "") {
    if (node.__dapaoSeedance20Syncing) return;
    node.__dapaoSeedance20Syncing = true;
    try {
        const resolutionWidget = widget(node, "🧩 分辨率");
        const faceModeWidget = widget(node, "👤 真人模式");
        const modelWidget = widget(node, "🤖 模型");
        if (!resolutionWidget || !faceModeWidget || !modelWidget) return;

        let model = String(modelWidget.value || FACE_MODEL);
        const faceMode = Boolean(faceModeWidget.value);
        resolutionWidget.value = "720P";

        if (sourceName === "🤖 模型") {
            if (!SUPPORTED_MODELS.has(model)) {
                model = faceMode ? FACE_MODEL : DEFAULT_NON_FACE_MODEL;
                modelWidget.value = model;
            }
            faceModeWidget.value = model === FACE_MODEL;
        } else if (sourceName === "👤 真人模式") {
            if (faceMode) {
                modelWidget.value = FACE_MODEL;
            } else if (model === FACE_MODEL || !SUPPORTED_MODELS.has(model)) {
                modelWidget.value = DEFAULT_NON_FACE_MODEL;
            }
        } else {
            if (!SUPPORTED_MODELS.has(model)) {
                model = faceMode ? FACE_MODEL : DEFAULT_NON_FACE_MODEL;
                modelWidget.value = model;
            }
            faceModeWidget.value = model === FACE_MODEL;
        }
    } finally {
        node.__dapaoSeedance20Syncing = false;
    }
}

function refreshNode(node, sourceName = "") {
    if (nodeType(node) !== NODE_TYPE) return;
    syncModelControls(node, sourceName);
    const mode = String(value(node, "🎛️ 生成模式", "文生视频"));
    const imageMode = mode === "图生视频" || mode === "多模态参考";
    const frameMode = mode === "首尾帧生视频";
    const multimodalMode = mode === "多模态参考";
    setInputHidden(node, "🎬 首帧图", !frameMode);
    setInputHidden(node, "🏁 尾帧图", !frameMode);
    for (let index = 1; index <= 9; index++) {
        setInputHidden(node, `🖼️ 参考图${index}`, !imageMode);
    }
    for (let index = 1; index <= 3; index++) {
        setInputHidden(node, `🎞️ 参考视频${index}`, !multimodalMode);
        setInputHidden(node, `🎵 参考音频${index}`, !multimodalMode);
    }
    ensureRegisterButton(node);
    if (node.computeSize) {
        const computed = node.computeSize();
        const currentWidth = Number(node.size?.[0]) || computed[0];
        node.setSize([Math.max(currentWidth, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapCallback(node, target) {
    if (!target || target.__dapaoSeedance20Wrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refreshNode(node, target.name);
        return result;
    };
    target.__dapaoSeedance20Wrapped = true;
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
    name: "Dapao.Seedance20AllroundVideo.UI",
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
            refreshNode(this, typeof arguments[0] === "string" ? arguments[0] : "");
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

console.log("[Dapao Seedance2.0 Allround Video UI] loaded without price badge");
