import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoAllroundImagePromptNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";
const CATEGORY_PREFIXES = {
    "自动识别": "auto",
    "UI界面样机": "UI界面样机",
    "产品商业视觉": "产品商业视觉",
    "地图与路线": "地图与路线",
    "幻灯片与视觉文档": "幻灯片与视觉文档",
    "海报与Campaign": "海报与Campaign",
    "人物与角色设定": "人物与角色设定",
    "场景与插画": "场景与插画",
    "图像编辑工作流": "图像编辑工作流",
    "头像与个人形象": "头像与个人形象",
    "分镜漫画与序列": "分镜漫画与序列",
    "网格与拼贴": "网格与拼贴",
    "品牌与包装": "品牌与包装",
    "字体与文字版式": "字体与文字版式",
    "图标游戏与素材": "图标游戏与素材",
    "学术论文配图": "学术论文配图",
    "信息图与数据看板": "信息图与数据看板",
    "技术架构与工程图": "技术架构与工程图",
};

function nodeType(node) { return node?.comfyClass || node?.type || ""; }
function widget(node, name) { return node?.widgets?.find((item) => item.name === name) || null; }
function value(node, name, fallback = "") { return widget(node, name)?.value ?? fallback; }
function setInputHidden(node, name, hidden) {
    const input = node?.inputs?.find((item) => item.name === name);
    if (input) input.hidden = Boolean(hidden);
}

function ensureRegisterButton(node) {
    if (!node?.addCustomWidget || node.__dapaoImagePromptRegisterWidget) return;
    for (const oldName of ["点击此处注册API密钥", REGISTER_WIDGET_NAME]) {
        const old = widget(node, oldName);
        if (!old) continue;
        const index = node.widgets.indexOf(old);
        if (index >= 0) node.widgets.splice(index, 1);
    }
    const button = {
        name: REGISTER_WIDGET_NAME,
        type: "DAPAO_IMAGE_PROMPT_REGISTER_BUTTON",
        serialize: false,
        _hovered: false,
        _area: null,
        computeSize(width) { return [Math.max(180, width), 38]; },
        draw(ctx, nodeRef, width, y, height) {
            const margin = 8, buttonY = y + 3, buttonHeight = Math.max(30, height - 6);
            ctx.save();
            ctx.fillStyle = this._hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath(); ctx.roundRect(margin, buttonY, width - margin * 2, buttonHeight, 8); ctx.fill();
            ctx.strokeStyle = this._hovered ? "#ffd36a" : "#d49a42"; ctx.lineWidth = 1.5; ctx.stroke();
            ctx.fillStyle = "#fff7df"; ctx.font = "bold 13px sans-serif"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
            ctx.fillText(REGISTER_WIDGET_NAME, width / 2, buttonY + buttonHeight / 2); ctx.restore();
            this._area = { x: margin, y: buttonY, width: width - margin * 2, height: buttonHeight };
        },
        mouse(event, pos, nodeRef) {
            const area = this._area;
            if (!area) return false;
            const inside = pos[0] >= area.x && pos[0] <= area.x + area.width && pos[1] >= area.y && pos[1] <= area.y + area.height;
            if (event.type === "pointermove") { this._hovered = inside; nodeRef.setDirtyCanvas?.(true, true); return inside; }
            if (event.type === "pointerdown" && inside) { const opened = window.open(REGISTER_URL, "_blank"); if (opened) opened.opener = null; return true; }
            return false;
        },
    };
    node.addCustomWidget(button);
    node.__dapaoImagePromptRegisterWidget = button;
}

function refreshTemplateChoices(node) {
    const target = widget(node, "🧩 具体模板");
    if (!target?.options) return;
    if (!target.__dapaoAllTemplateValues) target.__dapaoAllTemplateValues = [...(target.options.values || [])];
    const category = CATEGORY_PREFIXES[String(value(node, "🗂️ 设计分类", "自动识别"))] || "auto";
    const all = target.__dapaoAllTemplateValues;
    const filtered = category === "auto" ? all : ["自动选择模板", ...all.filter((item) => String(item).startsWith(`${category}｜`))];
    target.options.values = filtered;
    if (!filtered.includes(target.value)) target.value = "自动选择模板";
}

function refreshInputs(node) {
    const task = String(value(node, "🎛️ 任务模式", "自动识别"));
    const showImages = task !== "新建图像提示词" || task === "自动识别";
    const showMask = ["自动识别", "图像编辑提示词", "蒙版局部编辑提示词"].includes(task);
    for (let index = 1; index <= 9; index++) setInputHidden(node, `🖼️ 参考图${index}`, !showImages);
    setInputHidden(node, "🎭 蒙版", !showMask);
}

function refresh(node) {
    if (nodeType(node) !== NODE_TYPE) return;
    ensureRegisterButton(node); refreshTemplateChoices(node); refreshInputs(node);
    if (node.computeSize) { const computed = node.computeSize(); node.setSize([Math.max(Number(node.size?.[0]) || 0, computed[0]), computed[1]]); }
    node.setDirtyCanvas?.(true, true);
}
function wrap(node, target) {
    if (!target || target.__dapaoImagePromptWrapped) return;
    const original = target.callback;
    target.callback = function () { const result = original?.apply(this, arguments); refresh(node); return result; };
    target.__dapaoImagePromptWrapped = true;
}
function setup(node) { if (!node?.widgets || nodeType(node) !== NODE_TYPE) return; ensureRegisterButton(node); node.widgets.forEach((target) => wrap(node, target)); refresh(node); }
function refreshAll() { app.graph?.findNodesByType(NODE_TYPE)?.forEach((node) => setup(node)); }

app.registerExtension({
    name: "Dapao.AllroundImagePrompt.UI",
    async setup() { api.addEventListener("hot_reload_update", () => [50, 250, 1000].forEach((delay) => setTimeout(refreshAll, delay))); },
    nodeCreated(node) { if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 20); },
    loadedGraphNode(node) { if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 50); },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        if (nodeData.name !== NODE_TYPE) return;
        const created = nodeTypeClass.prototype.onNodeCreated;
        nodeTypeClass.prototype.onNodeCreated = function () { created?.apply(this, arguments); this.color = "#141416"; this.bgcolor = "#19191c"; setTimeout(() => setup(this), 20); };
        const added = nodeTypeClass.prototype.onAdded;
        nodeTypeClass.prototype.onAdded = function () { added?.apply(this, arguments); setTimeout(() => setup(this), 20); };
        const configured = nodeTypeClass.prototype.onConfigure;
        nodeTypeClass.prototype.onConfigure = function () { configured?.apply(this, arguments); setTimeout(() => setup(this), 50); };
        const changed = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () { const result = changed?.apply(this, arguments); refresh(this); return result; };
        const connected = nodeTypeClass.prototype.onConnectionsChange;
        nodeTypeClass.prototype.onConnectionsChange = function () { const result = connected?.apply(this, arguments); setTimeout(() => refresh(this), 0); return result; };
    },
});

console.log("[Dapao Allround Image Prompt UI] loaded");
