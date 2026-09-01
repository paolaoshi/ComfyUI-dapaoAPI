import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoSeedreamV5ProLayerDecompositionNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";

function nodeType(node) {
    return node?.comfyClass || node?.type || "";
}

function widget(node, name) {
    return node?.widgets?.find((item) => item.name === name) || null;
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoSeedreamLayerRegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const oldWidget = widget(node, oldName);
        if (!oldWidget) continue;
        const index = node.widgets.indexOf(oldWidget);
        if (index >= 0) node.widgets.splice(index, 1);
    }
    const registerWidget = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_SEEDREAM_LAYER_REGISTER_BUTTON",
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
    node.__dapaoSeedreamLayerRegisterWidget = registerWidget;
}

function setup(node) {
    if (!node?.widgets || nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    if (node.computeSize) {
        const computed = node.computeSize();
        const currentWidth = Number(node.size?.[0]) || computed[0];
        node.setSize([Math.max(380, currentWidth, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function refreshAllNodes() {
    app.graph?.findNodesByType(NODE_TYPE)?.forEach((node) => setup(node));
}

app.registerExtension({
    name: "Dapao.SeedreamV5ProLayerDecomposition.UI",
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

    },
});

console.log("[Dapao Seedream V5 Pro Layer Decomposition UI] loaded");
