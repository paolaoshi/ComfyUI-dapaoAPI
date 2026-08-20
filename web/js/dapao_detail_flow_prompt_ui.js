import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoDetailFlowPromptNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";
const handledRegisterEvents = new WeakSet();

function nodeType(node) { return node?.comfyClass || node?.type || ""; }
function widget(node, name) { return node?.widgets?.find((item) => item.name === name) || null; }
function value(node, name, fallback = "") { return widget(node, name)?.value ?? fallback; }

function isPressEvent(event) {
    const type = String(event?.type || "");
    const pointerDown = globalThis.LiteGraph?.pointerevents_method
        ? `${globalThis.LiteGraph.pointerevents_method}down`
        : "";
    return type === "pointerdown" || type === "mousedown" || type === "click" || type === pointerDown;
}

function openRegisterPage(event) {
    if (event && typeof event === "object") {
        if (handledRegisterEvents.has(event)) return true;
        handledRegisterEvents.add(event);
    }

    // Keep the navigation in the original user gesture. Some browsers return
    // null from window.open in the ComfyUI canvas, so fall back to a real link.
    try {
        const opened = window.open(REGISTER_URL, "_blank", "noopener,noreferrer");
        if (opened) {
            opened.opener = null;
            return true;
        }
    } catch (_) {
        // Try the anchor fallback below.
    }
    try {
        const anchor = document.createElement("a");
        anchor.href = REGISTER_URL;
        anchor.target = "_blank";
        anchor.rel = "noopener noreferrer";
        anchor.style.display = "none";
        document.body?.appendChild(anchor);
        anchor.click();
        anchor.remove();
        return true;
    } catch (_) {
        return false;
    }
}

function pointInside(area, pos) {
    return Boolean(area && Array.isArray(pos) && pos.length >= 2
        && pos[0] >= area.x && pos[0] <= area.x + area.width
        && pos[1] >= area.y && pos[1] <= area.y + area.height);
}

function setWidgetHidden(node, name, hidden) {
    const target = widget(node, name);
    if (!target) return;
    if (!("__dapaoDetailFlowOriginalComputeSize" in target)) {
        target.__dapaoDetailFlowOriginalComputeSize = target.computeSize;
    }
    target.computeSize = hidden ? (() => [0, -4]) : target.__dapaoDetailFlowOriginalComputeSize;
    const element = target.inputEl || target.element || target.domElement || target.inputElement;
    if (element?.style) element.style.display = hidden ? "none" : "";
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoDetailFlowRegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const old = widget(node, oldName);
        if (!old) continue;
        const index = node.widgets.indexOf(old);
        if (index >= 0) node.widgets.splice(index, 1);
    }
    const button = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_DETAIL_FLOW_REGISTER_BUTTON",
        serialize: false,
        _hovered: false,
        _area: null,
        computeSize() { return [180, 38]; },
        draw(ctx, nodeRef, width, y, height) {
            const widgetWidth = Math.max(180, Number(nodeRef?.size?.[0]) || Number(width) || 180);
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
            // onMouseDown receives node-local coordinates, while widget.mouse
            // receives widget-local coordinates. Keep both hit regions current.
            this._nodeArea = { x: margin, y: buttonY, width: widgetWidth - margin * 2, height: buttonHeight };
        },
        mouse(event, pos, nodeRef) {
            const area = this._area;
            if (!area) return false;
            const inside = pointInside(area, pos);
            if (event.type === "pointermove") {
                this._hovered = inside;
                nodeRef.setDirtyCanvas?.(true, true);
                return inside;
            }
            if (isPressEvent(event) && inside) {
                openRegisterPage(event);
                return true;
            }
            return false;
        },
    };
    node.addCustomWidget(button);
    node.__dapaoDetailFlowRegisterWidget = button;
}

function installRegisterMouseFallback(node) {
    if (!node || node.__dapaoDetailFlowRegisterMouseFallback) return;
    const original = node.onMouseDown;
    node.onMouseDown = function (event, pos) {
        const button = this.__dapaoDetailFlowRegisterWidget;
        if (isPressEvent(event) && pointInside(button?._nodeArea, pos)) {
            openRegisterPage(event);
            this.setDirtyCanvas?.(true, true);
            return true;
        }
        return original?.apply(this, arguments);
    };
    node.__dapaoDetailFlowRegisterMouseFallback = true;
}

function refreshInputs(node) {
    const customRules = [
        [["👥 目标购买人群"], "📝 自定义目标人群"],
        [["💡 主卖点方向"], "📝 自定义主卖点"],
        [["💡 第二卖点方向"], "📝 自定义第二卖点"],
        [["💡 第三卖点方向"], "📝 自定义第三卖点"],
        [["📏 主要证据类型"], "📝 自定义证据说明"],
        [["🎬 主要使用场景"], "📝 自定义使用场景"],
        [["🛒 CTA类型"], "📝 自定义CTA"],
        [["✍️ 画面文字方案"], "📝 自定义画面文字方案"],
        [["🚫 事实处理方式"], "📝 自定义事实限制"],
        [["🎨 视觉风格方向"], "📝 自定义视觉风格"],
    ];
    for (const [selectors, customName] of customRules) {
        const show = selectors.some((name) => String(value(node, name, "")).startsWith("自定义"));
        setWidgetHidden(node, customName, !show);
    }

    const showAdvanced = Boolean(value(node, "⚙️ 显示高级设置", false));
    for (const name of ["🌡️ 温度", "📝 最大输出令牌", "🎲 Top_P", "🔄 每次重新生成提示词", "⌛ 请求超时", "🚫 出错时跳过"]) {
        setWidgetHidden(node, name, !showAdvanced);
    }
}

function refresh(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    installRegisterMouseFallback(node);
    refreshInputs(node);
    if (node.computeSize) {
        const computed = node.computeSize();
        node.setSize([Math.max(Number(node.size?.[0]) || 0, computed[0], 560), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapWidget(node, target) {
    if (!target || target.__dapaoDetailFlowWrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refresh(node);
        return result;
    };
    target.__dapaoDetailFlowWrapped = true;
}

function setup(node) {
    if (!node?.widgets || nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node);
    node.widgets.forEach((target) => wrapWidget(node, target));
    refresh(node);
}

function refreshAll() {
    app.graph?.findNodesByType?.(NODE_TYPE)?.forEach((node) => setup(node));
}

app.registerExtension({
    name: "Dapao.DetailFlowPrompt.UI",
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
        if (nodeData?.name !== NODE_TYPE) return;
        const created = nodeTypeClass.prototype.onNodeCreated;
        nodeTypeClass.prototype.onNodeCreated = function () {
            const result = created?.apply(this, arguments);
            this.color = "#191412";
            this.bgcolor = "#211a17";
            installRegisterMouseFallback(this);
            setTimeout(() => setup(this), 20);
            return result;
        };
        const added = nodeTypeClass.prototype.onAdded;
        nodeTypeClass.prototype.onAdded = function () {
            const result = added?.apply(this, arguments);
            setTimeout(() => setup(this), 20);
            return result;
        };
        const configured = nodeTypeClass.prototype.onConfigure;
        nodeTypeClass.prototype.onConfigure = function () {
            const result = configured?.apply(this, arguments);
            setTimeout(() => setup(this), 50);
            return result;
        };
        const changed = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () {
            const result = changed?.apply(this, arguments);
            refresh(this);
            return result;
        };
        const connected = nodeTypeClass.prototype.onConnectionsChange;
        nodeTypeClass.prototype.onConnectionsChange = function () {
            const result = connected?.apply(this, arguments);
            setTimeout(() => refresh(this), 0);
            return result;
        };
    },
});

console.log("[Dapao DetailFlow Prompt UI] loaded");
