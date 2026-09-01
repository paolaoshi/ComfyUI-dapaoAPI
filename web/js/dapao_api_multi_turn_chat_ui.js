import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const CHAT_NODE = "DapaoAPIMultiTurnChatNode";
const CONFIG_NODE = "DapaoAPILLMConfigNode";
const SKILL_NODE = "DapaoAPISkillLoaderNode";
const MATERIAL_NODE = "DapaoAPIChatMaterialLibraryNode";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_LABEL = "👉点此注册API密钥👈";
const PREFIX = "dapao-api-chat";
const CHAT_PANEL_MIN_HEIGHT = 300;
const CHAT_NODE_CHROME_HEIGHT = 130;
const CHAT_NODE_DEFAULT_HEIGHT = 560;
const MATERIAL_PANEL_HEIGHT = 220;
const MATERIAL_NODE_DEFAULT_HEIGHT = 860;
const MATERIAL_NODE_MAX_HEIGHT = 1100;
const SKILL_PANEL_HEIGHT = 326;
const MATERIAL_TOKEN_PATTERN = /@(图片(?:20|1\d|[1-9])|视频[1-5]|音频[1-5])(?!\d)/g;
let activeMaterialMenu = null;
let materialPreviewEpoch = 0;

function injectStyles() {
    if (document.getElementById(`${PREFIX}-styles`)) return;
    const style = document.createElement("style");
    style.id = `${PREFIX}-styles`;
    style.textContent = `
        .${PREFIX} {
            box-sizing: border-box; container-type: inline-size; display: flex; flex-direction: column;
            width: 100%; max-width: 100%; min-width: 0; overflow: hidden;
            padding: 8px; gap: 7px; color: #e8e9ed; background: #242529;
            border: 1px solid #3c3e44; border-radius: 10px;
            font: 13px/1.45 Inter, "Microsoft YaHei", system-ui, sans-serif;
        }
        .${PREFIX} *, .${PREFIX} *::before, .${PREFIX} *::after { box-sizing: border-box; }
        .${PREFIX}__top {
            display: flex; align-items: center; gap: 7px; min-width: 0;
            padding: 1px 2px 6px; border-bottom: 1px solid #3a3c42;
        }
        .${PREFIX}__top-label { color: #aeb1ba; font-size: 12px; }
        .${PREFIX}__stage {
            max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            padding: 3px 8px; color: #ffd28b; background: #4d371a; border-radius: 5px; font-weight: 650;
        }
        .${PREFIX}__skill {
            min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            color: #c1c4cc;
        }
        .${PREFIX}__meter { margin-left: auto; display: flex; align-items: center; gap: 7px; flex: 0 0 auto; }
        .${PREFIX}__ring {
            display: grid; place-items: center; width: 38px; height: 38px; border-radius: 50%;
            background: conic-gradient(#55bd80 0deg, #464950 0deg); position: relative;
        }
        .${PREFIX}__ring::after { content: ""; position: absolute; inset: 4px; border-radius: 50%; background: #242529; }
        .${PREFIX}__percent { position: relative; z-index: 1; font-size: 10px; font-weight: 750; }
        .${PREFIX}__meter-copy { display: grid; font-size: 10px; color: #aeb1ba; line-height: 1.3; }
        .${PREFIX}__meter-copy strong { color: #e5e7eb; font-weight: 600; }
        .${PREFIX}__toolbar {
            display: flex; flex: 0 0 auto; align-items: center; flex-wrap: wrap; gap: 5px;
            min-width: 0; padding: 0 1px;
        }
        .${PREFIX}__toolbar button {
            min-height: 27px; padding: 4px 8px; color: #bfc3cc; background: #303238;
            border: 1px solid #454850; border-radius: 6px; cursor: pointer; font: inherit; font-size: 11px;
        }
        .${PREFIX}__toolbar button[data-tone="accent"] { color: #dcf6e8; border-color: #47745d; background: #294235; }
        .${PREFIX}__toolbar button[data-tone="danger"] { color: #ffd0d0; border-color: #6b4646; background: #422d2d; }
        .${PREFIX}__toolbar-spacer { flex: 1 1 auto; min-width: 6px; }
        .${PREFIX}__messages {
            flex: 1 1 auto; min-height: 0; overflow: auto; padding: 2px; scrollbar-width: thin; scrollbar-color: #565962 transparent;
            scroll-behavior: smooth;
        }
        .${PREFIX}__empty { display: grid; place-items: center; min-height: 100%; color: #8d919b; }
        .${PREFIX}__message {
            width: min(92%, 920px); margin: 0 0 8px; padding: 9px 10px;
            min-width: 0; border-radius: 9px; background: #1c1d20; border: 1px solid #33353a;
        }
        .${PREFIX}__message--user { margin-left: auto; background: #262c35; border-color: #3c4654; }
        .${PREFIX}__role { display: block; margin-bottom: 4px; color: #9da2ad; font-size: 11px; font-weight: 700; }
        .${PREFIX}__body { position: relative; overflow-wrap: anywhere; user-select: text; }
        .${PREFIX}__body[data-collapsed="true"] { max-height: 340px; overflow: hidden; }
        .${PREFIX}__body[data-collapsed="true"]::after {
            content: ""; position: absolute; inset: auto 0 0; height: 70px; pointer-events: none;
            background: linear-gradient(to bottom, transparent, #1c1d20 78%);
        }
        .${PREFIX}__message--user .${PREFIX}__body[data-collapsed="true"]::after { background: linear-gradient(to bottom, transparent, #262c35 78%); }
        .${PREFIX}__markdown { color: #e7e9ed; line-height: 1.62; }
        .${PREFIX}__markdown > :first-child { margin-top: 0; }
        .${PREFIX}__markdown > :last-child { margin-bottom: 0; }
        .${PREFIX}__markdown p { margin: 0 0 9px; white-space: pre-wrap; }
        .${PREFIX}__markdown h1, .${PREFIX}__markdown h2, .${PREFIX}__markdown h3,
        .${PREFIX}__markdown h4, .${PREFIX}__markdown h5, .${PREFIX}__markdown h6 {
            margin: 16px 0 7px; color: #f4f5f7; line-height: 1.28; overflow-wrap: anywhere;
        }
        .${PREFIX}__markdown h1 { font-size: 1.38em; }
        .${PREFIX}__markdown h2 { font-size: 1.24em; }
        .${PREFIX}__markdown h3 { font-size: 1.12em; }
        .${PREFIX}__markdown h4, .${PREFIX}__markdown h5, .${PREFIX}__markdown h6 { font-size: 1em; }
        .${PREFIX}__markdown ul, .${PREFIX}__markdown ol { margin: 4px 0 10px; padding-inline-start: 23px; }
        .${PREFIX}__markdown li { margin: 3px 0; }
        .${PREFIX}__markdown blockquote { margin: 8px 0; padding: 7px 10px; color: #c7cbd3; background: #27292e; border-inline-start: 1px solid #69717f; }
        .${PREFIX}__markdown hr { border: 0; border-top: 1px solid #3d4047; margin: 13px 0; }
        .${PREFIX}__markdown a { color: #81b5f6; text-underline-offset: 2px; }
        .${PREFIX}__markdown code { padding: 1px 4px; color: #f0d9aa; background: #292b30; border-radius: 4px; font-family: ui-monospace, Consolas, monospace; }
        .${PREFIX}__code { margin: 9px 0; overflow: hidden; background: #151619; border: 1px solid #34363c; border-radius: 8px; }
        .${PREFIX}__code-head { display: flex; align-items: center; gap: 8px; min-height: 28px; padding: 3px 7px; color: #8f949f; background: #25262b; font-size: 10px; }
        .${PREFIX}__code-head button { margin-inline-start: auto; min-height: 22px; padding: 2px 7px; color: #c9cdd5; background: #34363c; border: 0; border-radius: 4px; cursor: pointer; }
        .${PREFIX}__code pre { margin: 0; padding: 10px; overflow: auto; white-space: pre; tab-size: 4; }
        .${PREFIX}__code pre code { padding: 0; color: #e4e6eb; background: transparent; border-radius: 0; }
        .${PREFIX}__table-wrap { max-width: 100%; margin: 9px 0; overflow: auto; }
        .${PREFIX}__markdown table { width: 100%; border-collapse: collapse; font-size: 12px; }
        .${PREFIX}__markdown th, .${PREFIX}__markdown td { padding: 6px 8px; border: 1px solid #3d4047; text-align: start; vertical-align: top; }
        .${PREFIX}__markdown th { color: #f0f1f4; background: #292b30; }
        .${PREFIX}__meta { display: flex; align-items: center; flex-wrap: wrap; gap: 6px 8px; margin-top: 6px; color: #858a94; font-size: 10px; }
        .${PREFIX}__meta > span { min-width: 0; overflow-wrap: anywhere; }
        .${PREFIX}__meta button {
            margin-left: auto; min-width: 28px; min-height: 25px; border: 0; border-radius: 5px;
            color: #bfc3cc; background: #303238; cursor: pointer;
        }
        .${PREFIX}__meta button + button { margin-left: 0; }
        .${PREFIX}__options { display: flex; flex: 0 0 auto; flex-wrap: wrap; gap: 6px; min-height: 0; }
        .${PREFIX}__options:empty { display: none; }
        .${PREFIX}__option {
            flex: 0 0 auto; min-height: 30px; max-width: 260px; padding: 5px 10px;
            overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
            color: #dce8e1; background: #294034; border: 1px solid #3e6852; border-radius: 7px; cursor: pointer;
        }
        .${PREFIX}__compose {
            display: grid; grid-template-columns: minmax(0, 1fr) 112px; align-items: start;
            gap: 7px; min-width: 0; flex: 0 0 auto;
        }
        .${PREFIX}__input-wrap { display: flex; flex-direction: column; min-width: 0; gap: 5px; }
        .${PREFIX}__attachments { display: flex; flex-wrap: wrap; gap: 5px; }
        .${PREFIX}__attachments:empty { display: none; }
        .${PREFIX}__attachment { display: inline-flex; align-items: center; gap: 4px; padding: 3px 6px; color: #cad3df; background: #303843; border-radius: 5px; font-size: 11px; }
        .${PREFIX}__attachment button { border: 0; color: #f0b7b7; background: transparent; cursor: pointer; }
        .${PREFIX}__input {
            display: block; box-sizing: border-box; width: 100%; height: 154px; min-height: 84px; max-height: 320px;
            overflow-y: auto; padding: 8px 9px; color: #f0f1f4; background: #1b1c1f;
            border: 1px solid #454850; border-radius: 8px; outline: none; font: inherit;
            white-space: pre-wrap; overflow-wrap: anywhere; caret-color: #fff; resize: vertical;
        }
        .${PREFIX}__input:empty::before { content: attr(data-placeholder); color: #8d919b; pointer-events: none; }
        .${PREFIX}__input:focus { border-color: #66bd91; box-shadow: 0 2px 8px rgba(35, 85, 61, .22); }
        .${PREFIX}__reference-chip {
            display: inline-flex; align-items: center; gap: 5px; margin: 1px 3px; padding: 2px 7px;
            color: #f5f9ff; background: rgba(42, 88, 150, .72); border: 1px solid #5b9cff;
            border-radius: 7px; vertical-align: middle; white-space: nowrap; user-select: all;
        }
        .${PREFIX}__reference-chip img { width: 23px; height: 23px; border-radius: 4px; object-fit: cover; }
        .${PREFIX}__stale { color: #ff9090; text-decoration: underline wavy; }
        .${PREFIX}__actions { display: flex; flex-direction: column; align-items: stretch; gap: 6px; }
        .${PREFIX}__button {
            min-height: 34px; padding: 6px 9px; color: #e6e7eb; background: #3b3e45;
            border: 1px solid #555962; border-radius: 7px; cursor: pointer; font-weight: 600;
        }
        .${PREFIX}__button--send { color: #f2fff8; background: #347558; border-color: #4c9b76; }
        .${PREFIX}__button--context { color: #ffe6b4; background: #55401f; border-color: #806333; }
        .${PREFIX}__button--publish { color: #eef4ff; background: #355d91; border-color: #5682b9; }
        .${PREFIX} button:hover:not(:disabled) { filter: brightness(1.12); }
        .${PREFIX} button:focus-visible { outline: 2px solid #79c99d; outline-offset: 1px; }
        .${PREFIX} button:disabled, .${PREFIX}__input[data-disabled="true"] { cursor: not-allowed; opacity: .48; }
        .${PREFIX}__status { flex: 0 0 auto; min-height: 18px; padding-left: 1px; color: #9da2ad; font-size: 11px; }
        .${PREFIX}__status[data-state="busy"] { color: #e5bd73; }
        .${PREFIX}__status[data-state="error"] { color: #f08f8f; }
        @container (max-width: 420px) {
            .${PREFIX}__top { flex-wrap: wrap; }
            .${PREFIX}__meter { width: 100%; margin-left: 0; }
            .${PREFIX}__toolbar { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
            .${PREFIX}__toolbar-spacer { display: none; }
            .${PREFIX}__compose { grid-template-columns: 1fr; }
            .${PREFIX}__actions { display: grid; grid-template-columns: repeat(2, 1fr); }
        }
        @media (pointer: coarse) {
            .${PREFIX}__button, .${PREFIX}__option, .${PREFIX}__meta button { min-height: 44px; }
        }
        .${PREFIX}-menu {
            position: fixed; z-index: 100000; width: 350px; max-width: calc(100vw - 16px); max-height: 330px;
            overflow-y: auto; padding: 7px; color: #f4f4f4; background: rgba(28, 30, 33, .98);
            border: 1px solid rgba(255,255,255,.13); border-radius: 12px; box-shadow: 0 18px 48px rgba(0,0,0,.48);
        }
        .${PREFIX}-menu button { display: flex; align-items: center; gap: 10px; width: 100%; padding: 8px; border: 0; border-radius: 8px; color: inherit; background: transparent; cursor: pointer; text-align: left; }
        .${PREFIX}-menu__preview { width: 44px; height: 44px; flex: 0 0 44px; display: grid; place-items: center; overflow: hidden; border-radius: 7px; background: rgba(255,255,255,.1); font-size: 20px; }
        .${PREFIX}-menu__preview img { width: 100%; height: 100%; object-fit: cover; }
        .${PREFIX}-materials { box-sizing: border-box; display: flex; flex-direction: column; width: 100%; height: 100%; min-height: 170px; padding: 8px; gap: 7px; overflow: hidden; color: #e8e9ed; background: #242529; border: 1px solid #3c3e44; border-radius: 10px; font: 12px/1.4 Inter,"Microsoft YaHei",sans-serif; }
        .${PREFIX}-materials__status { color: #9fcfb6; }
        .${PREFIX}-materials__list { display: flex; flex-direction: column; gap: 5px; min-height: 0; overflow-y: auto; }
        .${PREFIX}-materials__row { display: grid; grid-template-columns: 35px 70px minmax(0,1fr); align-items: center; gap: 6px; padding: 5px; background: #1d1e22; border-radius: 7px; }
        .${PREFIX}-materials__preview { width: 35px; height: 35px; display: grid; place-items: center; overflow: hidden; background: #30343a; border-radius: 6px; font-size: 18px; }
        .${PREFIX}-materials__preview img { width: 100%; height: 100%; object-fit: cover; }
        .${PREFIX}-materials__row input { min-width: 0; width: 100%; padding: 5px 7px; color: #eef0f4; background: #292b30; border: 1px solid #484b53; border-radius: 5px; outline: none; }
        .${PREFIX}-materials__help { color: #90959f; }
        .${PREFIX}-skills {
            box-sizing: border-box; display: flex; flex-direction: column; width: 100%; height: 100%;
            min-height: ${SKILL_PANEL_HEIGHT}px; padding: 9px; gap: 8px; overflow: hidden;
            color: #e8e9ed; background: #242529; border: 1px solid #3c3e44; border-radius: 10px;
            font: 12px/1.4 Inter,"Microsoft YaHei",sans-serif;
        }
        .${PREFIX}-skills__header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
        .${PREFIX}-skills__header strong { color: #f0f2f5; font-size: 13px; }
        .${PREFIX}-skills__count { color: #9fcfb6; white-space: nowrap; }
        .${PREFIX}-skills__current { min-height: 34px; padding: 7px 8px; overflow: hidden; color: #b9bec8; background: #1d1e22; border-radius: 7px; text-overflow: ellipsis; white-space: nowrap; }
        .${PREFIX}-skills__name { width: 100%; min-width: 0; padding: 7px 8px; color: #eef0f4; background: #1b1c1f; border: 1px solid #484b53; border-radius: 6px; outline: none; }
        .${PREFIX}-skills__name:focus { border-color: #66bd91; }
        .${PREFIX}-skills__row { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 7px; }
        .${PREFIX}-skills button { min-width: 0; min-height: 32px; padding: 6px 7px; overflow: hidden; color: #e6e7eb; background: #3b3e45; border: 1px solid #555962; border-radius: 6px; cursor: pointer; text-overflow: ellipsis; white-space: nowrap; }
        .${PREFIX}-skills button:hover:not(:disabled) { filter: brightness(1.12); }
        .${PREFIX}-skills button:disabled, .${PREFIX}-skills input:disabled { cursor: not-allowed; opacity: .48; }
        .${PREFIX}-skills__ai { color: #fff6dc !important; background: #6e5421 !important; border-color: #a78031 !important; }
        .${PREFIX}-skills__upload { color: #e7f4ff !important; background: #31475d !important; border-color: #4d6b88 !important; }
        .${PREFIX}-skills__status { min-height: 34px; padding: 6px 7px; overflow-y: auto; color: #9da2ad; background: #202126; border-radius: 6px; }
        .${PREFIX}-skills__status[data-state="busy"] { color: #e5bd73; }
        .${PREFIX}-skills__status[data-state="error"] { color: #f08f8f; }
        .${PREFIX}-skills__help { color: #858a94; font-size: 10px; }
    `;
    document.head.appendChild(style);
}

function widget(node, name) {
    return node?.widgets?.find((item) => item.name === name) || null;
}

function first(value) {
    return Array.isArray(value) ? value[0] : value;
}

function parse(raw, fallback) {
    try {
        const value = JSON.parse(raw || "");
        return value ?? fallback;
    } catch (_) {
        return fallback;
    }
}

function historyValue(raw) {
    const value = parse(raw, []);
    return Array.isArray(value) ? value.filter((item) => item && ["user", "assistant"].includes(item.role) && typeof item.content === "string") : [];
}

function imageValue(raw) {
    const value = parse(raw, []);
    if (!Array.isArray(value)) return [];
    return value.filter((item) => item && (item.filename || item.name)).slice(0, 12).map((item) => ({
        filename: item.filename || item.name,
        subfolder: item.subfolder || "",
        type: "input",
    }));
}

function optionsValue(raw) {
    const value = parse(raw, []);
    return Array.isArray(value) ? value.filter((item) => typeof item === "string" && item.trim()).slice(0, 6) : [];
}

function element(tag, className, text = "") {
    const value = document.createElement(tag);
    value.className = className;
    if (text) value.textContent = text;
    return value;
}

function formatTokens(value) {
    const number = Math.max(0, Number(value) || 0);
    if (number < 1000) return String(Math.round(number));
    const scaled = number / 1000;
    return `${scaled >= 10 ? scaled.toFixed(0) : scaled.toFixed(1)}k`;
}

function formatTime(value) {
    const date = new Date(Number(value));
    if (!Number.isFinite(date.getTime()) || date.getTime() <= 0) return "";
    const pad = (part) => String(part).padStart(2, "0");
    return `${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

function hideBackendWidget(target) {
    if (!target) return;
    target.type = `converted-widget:${PREFIX}-${target.name}`;
    target.hidden = true;
    target.options ||= {};
    target.options.hidden = true;
    target.options.hideInPanel = true;
    target.computeSize = () => [0, -4];
    target.serializeValue = async () => target.value;
    if (target.inputEl) target.inputEl.style.display = "none";
    if (target.element) target.element.style.display = "none";
}

function setWidgetValue(node, target, value) {
    if (!target) return;
    target.value = value;
    target.callback?.(value);
    const index = node?.widgets?.indexOf(target) ?? -1;
    if (index >= 0) {
        node.widgets_values ??= [];
        node.widgets_values[index] = value;
    }
    node?.setDirtyCanvas?.(true, true);
    node?.graph?.setDirtyCanvas?.(true, true);
}

function nodeClass(node) {
    return String(node?.comfyClass || node?.type || node?.constructor?.comfyClass || "");
}

function graphOf(node) {
    return node?.graph || app.canvas?.getCurrentGraph?.() || app.canvas?.graph || app.graph || null;
}

function graphLinks(graph) {
    const links = graph?.links;
    if (links instanceof Map || links instanceof Set) return [...links.values()].filter(Boolean);
    if (Array.isArray(links)) return links.filter(Boolean);
    return links && typeof links === "object" ? Object.values(links).filter(Boolean) : [];
}

function graphLink(graph, id) {
    if (id == null) return null;
    if (typeof id === "object") return id;
    if (graph?.links instanceof Map) return graph.links.get(id) || graph.links.get(String(id)) || null;
    return graph?.links?.[id] || graph?.links?.[String(id)] || graphLinks(graph).find((link) => String(link?.id) === String(id)) || null;
}

function graphNode(graph, id) {
    if (id == null) return null;
    return graph?.getNodeById?.(id)
        || (graph?.nodes instanceof Map ? graph.nodes.get(id) || graph.nodes.get(String(id)) : null)
        || graph?._nodes_by_id?.[id]
        || graph?._nodes?.find((item) => String(item?.id) === String(id))
        || null;
}

function inputOrigin(node, inputName) {
    const graph = graphOf(node);
    const input = node?.inputs?.find((item) => item?.name === inputName || String(item?.name || "").split(".").pop() === inputName);
    if (!input) return null;
    let link = graphLink(graph, input.link ?? input.links?.[0]);
    if (!link) {
        const index = node.inputs.indexOf(input);
        link = graphLinks(graph).find((candidate) => {
            const target = candidate?.target_id ?? candidate?.targetId ?? candidate?.[3];
            const slot = candidate?.target_slot ?? candidate?.targetSlot ?? candidate?.[4];
            return String(target) === String(node.id) && (Number(slot) === index || String(slot) === String(input.name));
        });
    }
    const origin = link?.origin_id ?? link?.originId ?? link?.[1];
    return graphNode(graph, origin);
}

function viewUrl(path) {
    if (typeof api.apiURL === "function") return api.apiURL(path);
    if (typeof api.apiURL === "string" && api.apiURL) return `${api.apiURL.replace(/\/$/, "")}${path}`;
    return path;
}

async function responseJson(response, fallback = "请求失败") {
    let data = {};
    try { data = await response.json(); } catch (_) { /* response may be empty */ }
    if (!response?.ok) {
        const status = response?.status || "unknown";
        const localMethodError = Number(status) === 405
            ? "当前ComfyUI后台未接受此操作，请完整重启ComfyUI后再试。"
            : "";
        throw new Error(data?.error || localMethodError || `${fallback} (${status})`);
    }
    return data;
}

function upstreamByType(node, inputName, expectedType) {
    let source = inputOrigin(node, inputName);
    const visited = new Set();
    while (source && !visited.has(String(source.id))) {
        visited.add(String(source.id));
        if (nodeClass(source) === expectedType) return source;
        if (!/reroute/i.test(nodeClass(source)) || !source.inputs?.length) return null;
        source = inputOrigin(source, source.inputs[0].name);
    }
    return null;
}

function scalarOutputValue(source, visited = new Set()) {
    if (!source || visited.has(source)) return undefined;
    visited.add(source);

    if (/reroute/i.test(nodeClass(source)) && source.inputs?.[0]) {
        return scalarOutputValue(inputOrigin(source, source.inputs[0].name), visited);
    }

    const isScalar = (value) => ["string", "number", "boolean"].includes(typeof value);
    const preferredNames = new Set(["value", "text", "string", "字符串", "文本", "内容"]);
    const preferred = source.widgets?.find((item) => preferredNames.has(String(item?.name || "").toLowerCase()) && isScalar(item?.value));
    if (preferred) return preferred.value;

    const scalarWidget = source.widgets?.find((item) => isScalar(item?.value));
    if (scalarWidget) return scalarWidget.value;

    const stored = source.widgets_values?.[0];
    return isScalar(stored) ? stored : undefined;
}

function connectedWidgetValue(node, inputName, fallback) {
    const connected = scalarOutputValue(inputOrigin(node, inputName));
    if (connected !== undefined) return connected;
    const local = widget(node, inputName)?.value;
    return local !== undefined && local !== null ? local : fallback;
}

function skillOptimizerConfig(node) {
    const source = upstreamByType(node, "🤖API模型", CONFIG_NODE);
    if (!source) throw new Error("请先把“大炮API模型配置”连接到Skill加载器的“🤖API模型”接口。手动改名和上传无需连接模型。");
    const apiKey = String(connectedWidgetValue(source, "🔑 API密钥", "") || "").trim();
    if (!apiKey) throw new Error("请先在上游API模型配置中填写API密钥。");
    return {
        api_key: apiKey,
        model: String(connectedWidgetValue(source, "🤖 LLM模型", "") || ""),
        timeout: Number(connectedWidgetValue(source, "⌛ 请求超时", 300) || 300),
        context_limit: Number(connectedWidgetValue(source, "📚 上下文上限", 0) || 0),
    };
}

function skillIdFromLabel(value) {
    const text = String(value || "").trim();
    if (["", "自动选择", "自动匹配"].includes(text)) return "";
    return text.match(/\[([A-Za-z0-9][A-Za-z0-9._-]{0,63})\]\s*$/)?.[1] || text;
}

function previewDescriptor(node, visited = new Set()) {
    if (!node || visited.has(String(node.id))) return { src: "", key: "" };
    visited.add(String(node.id));
    if (/reroute/i.test(nodeClass(node)) && node.inputs?.[0]) return previewDescriptor(inputOrigin(node, node.inputs[0].name), visited);

    // LoadImage may still have an old entry in app.nodeOutputs after the user
    // selects a new file. Its current widget is the authoritative live value.
    const imageWidget = node.widgets?.find((item) => item?.name === "image") || node.widgets?.[0];
    const filename = String(imageWidget?.value || node.widgets_values?.[0] || "").trim();
    if (filename && nodeClass(node) === "LoadImage") {
        const params = new URLSearchParams({ filename, type: "input", v: String(materialPreviewEpoch) });
        return { src: `${viewUrl("/view")}?${params.toString()}`, key: `load:${node.id}:${filename}:${materialPreviewEpoch}` };
    }

    const output = app.nodeOutputs?.[String(node.id)]?.images;
    const file = Array.isArray(output) && output.length ? output[0] : null;
    if (file?.filename) {
        const params = new URLSearchParams({ filename: file.filename, type: file.type || "output", v: String(materialPreviewEpoch) });
        if (file.subfolder) params.set("subfolder", file.subfolder);
        const key = `output:${node.id}:${file.filename}:${file.subfolder || ""}:${file.type || "output"}:${materialPreviewEpoch}`;
        return { src: `${viewUrl("/view")}?${params.toString()}`, key };
    }
    const image = node.imgs?.[0] || node.images?.[0];
    const src = typeof image === "string" ? image : image?.currentSrc || image?.src || "";
    return { src, key: `image:${node.id}:${src}` };
}

function firstPreview(node, visited = new Set()) {
    return previewDescriptor(node, visited).src;
}

function aliasValue(node) {
    const raw = widget(node, "🏷️素材别名")?.value;
    const parsed = parse(raw, {});
    return parsed && typeof parsed === "object" && !Array.isArray(parsed) ? parsed : {};
}

function libraryManifest(source) {
    if (!source || nodeClass(source) !== MATERIAL_NODE) return { source: null, items: [] };
    const aliases = aliasValue(source);
    const specs = [["image", "图片", "🖼️图片", 20], ["video", "视频", "🎞️视频", 5], ["audio", "音频", "🎵音频", 5]];
    const items = [];
    specs.forEach(([kind, chinese, prefix, limit]) => {
        for (let slot = 1; slot <= limit; slot += 1) {
            const origin = inputOrigin(source, `${prefix}${slot}`);
            if (!origin) continue;
            const token = `@${chinese}${slot}`;
            const preview = previewDescriptor(origin);
            items.push({
                kind,
                slot,
                token,
                label: String(aliases[`${chinese}${slot}`] || token),
                src: preview.src,
                preview_key: preview.key,
            });
        }
    });
    return { source, items };
}

function materialSourceSignature(manifest) {
    return JSON.stringify((manifest?.items || []).map(({ kind, slot, preview_key }) => ({ kind, slot, preview_key })));
}

function materialManifest(chatNode) {
    return libraryManifest(inputOrigin(chatNode, "📦素材库"));
}

function mediaEmoji(kind) {
    return kind === "image" ? "🖼️" : kind === "video" ? "🎞️" : "🎵";
}

function textFromEditor(editor) {
    let result = "";
    const walk = (current) => {
        if (current.nodeType === Node.TEXT_NODE) return void (result += current.nodeValue || "");
        if (current.nodeType !== Node.ELEMENT_NODE) return;
        if (current.classList?.contains(`${PREFIX}__reference-chip`)) return void (result += current.dataset.token || "");
        if (current.tagName === "BR") return void (result += "\n");
        [...current.childNodes].forEach(walk);
        if (["DIV", "P"].includes(current.tagName) && current !== editor) result += "\n";
    };
    walk(editor);
    return result.replace(/\n+$/, "");
}

function createReferenceChip(item) {
    const chip = element("span", `${PREFIX}__reference-chip`);
    chip.dataset.token = item.token;
    chip.contentEditable = "false";
    if (item.src) {
        const image = document.createElement("img");
        image.src = item.src;
        chip.append(image);
    } else chip.append(document.createTextNode(mediaEmoji(item.kind)));
    chip.append(document.createTextNode(item.label.startsWith("@") ? item.label : `@${item.label}`));
    return chip;
}

function renderEditor(editor, value, manifest) {
    const byToken = new Map(manifest.items.map((item) => [item.token, item]));
    editor.replaceChildren();
    const text = String(value || "");
    let offset = 0;
    for (const match of text.matchAll(MATERIAL_TOKEN_PATTERN)) {
        if (match.index > offset) editor.append(document.createTextNode(text.slice(offset, match.index)));
        const item = byToken.get(match[0]);
        if (item) editor.append(createReferenceChip(item));
        else {
            const stale = element("span", `${PREFIX}__stale`, match[0]);
            stale.title = "该素材当前未连接到素材库";
            editor.append(stale);
        }
        offset = match.index + match[0].length;
    }
    if (offset < text.length) editor.append(document.createTextNode(text.slice(offset)));
    if (!editor.childNodes.length) editor.append(document.createElement("br"));
}

function mentionRange(editor) {
    const selection = window.getSelection();
    if (!selection?.rangeCount || !editor.contains(selection.anchorNode) || selection.anchorNode?.nodeType !== Node.TEXT_NODE) return null;
    const before = (selection.anchorNode.nodeValue || "").slice(0, selection.anchorOffset);
    const match = before.match(/@([^\s@]*)$/u);
    if (!match) return null;
    const range = document.createRange();
    range.setStart(selection.anchorNode, selection.anchorOffset - match[0].length);
    range.setEnd(selection.anchorNode, selection.anchorOffset);
    return { range, query: match[1].toLowerCase() };
}

function closeMaterialMenu() {
    activeMaterialMenu?.element?.remove();
    activeMaterialMenu = null;
}

function selectMaterialRow(index) {
    if (!activeMaterialMenu?.items.length) return;
    activeMaterialMenu.index = (index + activeMaterialMenu.items.length) % activeMaterialMenu.items.length;
    activeMaterialMenu.rows.forEach((row, rowIndex) => { row.style.background = rowIndex === activeMaterialMenu.index ? "rgba(46,181,112,.24)" : "transparent"; });
    activeMaterialMenu.rows[activeMaterialMenu.index]?.scrollIntoView?.({ block: "nearest" });
}

function isLink(value, output) {
    return Array.isArray(value) && value.length === 2 && Number.isFinite(Number(value[0])) && Number.isFinite(Number(value[1])) && Boolean(output?.[String(value[0])]);
}

function collectLinks(value, output, found = new Set()) {
    if (isLink(value, output)) {
        found.add(String(value[0]));
    } else if (Array.isArray(value)) {
        value.forEach((item) => collectLinks(item, output, found));
    } else if (value && typeof value === "object") {
        Object.values(value).forEach((item) => collectLinks(item, output, found));
    }
    return found;
}

async function chatOnlyPrompt(node, overrides = {}) {
    const prompt = await app.graphToPrompt();
    const output = prompt?.output;
    const targetId = String(node.id);
    if (!output?.[targetId]) throw new Error("当前聊天节点不在可执行提示中，请检查API模型连接。");
    output[targetId].inputs ||= {};
    Object.assign(output[targetId].inputs, overrides);
    const keep = new Set();
    const visit = (id) => {
        const key = String(id);
        if (keep.has(key) || !output[key]) return;
        keep.add(key);
        collectLinks(output[key].inputs || {}, output).forEach(visit);
    };
    visit(targetId);
    prompt.output = Object.fromEntries(Object.entries(output).filter(([id]) => keep.has(String(id))));
    return prompt;
}

async function chatAndDownstreamPrompt(node, overrides = {}) {
    const prompt = await app.graphToPrompt();
    const output = prompt?.output;
    const targetId = String(node.id);
    if (!output?.[targetId]) throw new Error("当前聊天节点不在可执行提示中，请检查API模型连接。");
    output[targetId].inputs ||= {};
    Object.assign(output[targetId].inputs, overrides);

    const dependencies = new Map();
    const dependents = new Map();
    Object.entries(output).forEach(([id, item]) => {
        const upstream = collectLinks(item?.inputs || {}, output);
        dependencies.set(String(id), upstream);
        upstream.forEach((sourceId) => {
            if (!dependents.has(sourceId)) dependents.set(sourceId, new Set());
            dependents.get(sourceId).add(String(id));
        });
    });

    const descendants = new Set([targetId]);
    const queue = [targetId];
    while (queue.length) {
        const current = queue.shift();
        for (const next of dependents.get(current) || []) {
            if (descendants.has(next)) continue;
            descendants.add(next);
            queue.push(next);
        }
    }
    const downstreamCount = descendants.size - 1;
    if (!downstreamCount) return { prompt, downstreamCount: 0 };

    const keep = new Set(descendants);
    const addDependencies = (id) => {
        for (const sourceId of dependencies.get(String(id)) || []) {
            if (keep.has(sourceId)) continue;
            keep.add(sourceId);
            addDependencies(sourceId);
        }
    };
    descendants.forEach(addDependencies);
    prompt.output = Object.fromEntries(Object.entries(output).filter(([id]) => keep.has(String(id))));
    return { prompt, downstreamCount };
}

async function copyText(text) {
    if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(String(text || ""));
    const area = document.createElement("textarea");
    area.value = String(text || "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.append(area);
    area.select();
    document.execCommand("copy");
    area.remove();
}

function downloadText(filename, text, type = "text/plain;charset=utf-8") {
    const url = URL.createObjectURL(new Blob([String(text || "")], { type }));
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
}

function safeLink(raw) {
    try {
        const url = new URL(String(raw || ""), window.location.href);
        return ["http:", "https:", "mailto:"].includes(url.protocol) ? url.href : "";
    } catch (_) {
        return "";
    }
}

function appendInlineMarkdown(parent, raw) {
    const text = String(raw || "");
    const pattern = /(`[^`\n]+`|\*\*[^*\n]+\*\*|~~[^~\n]+~~|\[[^\]\n]+\]\([^\s)]+(?:\s+"[^"]*")?\)|\*[^*\n]+\*)/g;
    let offset = 0;
    for (const match of text.matchAll(pattern)) {
        if (match.index > offset) parent.append(document.createTextNode(text.slice(offset, match.index)));
        const token = match[0];
        if (token.startsWith("`")) {
            const code = document.createElement("code");
            code.textContent = token.slice(1, -1);
            parent.append(code);
        } else if (token.startsWith("**")) {
            const strong = document.createElement("strong");
            strong.textContent = token.slice(2, -2);
            parent.append(strong);
        } else if (token.startsWith("~~")) {
            const strike = document.createElement("s");
            strike.textContent = token.slice(2, -2);
            parent.append(strike);
        } else if (token.startsWith("[")) {
            const parsed = token.match(/^\[([^\]]+)\]\(([^\s)]+)(?:\s+"([^"]*)")?\)$/);
            const href = safeLink(parsed?.[2]);
            if (parsed && href) {
                const link = document.createElement("a");
                link.textContent = parsed[1];
                link.href = href;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                if (parsed[3]) link.title = parsed[3];
                parent.append(link);
            } else parent.append(document.createTextNode(token));
        } else {
            const emphasis = document.createElement("em");
            emphasis.textContent = token.slice(1, -1);
            parent.append(emphasis);
        }
        offset = match.index + token.length;
    }
    if (offset < text.length) parent.append(document.createTextNode(text.slice(offset)));
}

function tableCells(line) {
    return String(line || "").trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((cell) => cell.trim());
}

function isTableDivider(line) {
    return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(String(line || ""));
}

function renderMarkdown(raw) {
    const root = element("div", `${PREFIX}__markdown`);
    const lines = String(raw || "").replace(/\r\n?/g, "\n").split("\n");
    const isBlockStart = (index) => {
        const line = lines[index] || "";
        return /^\s*```/.test(line)
            || /^\s{0,3}#{1,6}\s+/.test(line)
            || /^\s*>\s?/.test(line)
            || /^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)
            || /^\s*[-+*]\s+/.test(line)
            || /^\s*\d+[.)]\s+/.test(line)
            || (index + 1 < lines.length && line.includes("|") && isTableDivider(lines[index + 1]));
    };
    let index = 0;
    while (index < lines.length) {
        const line = lines[index];
        if (!line.trim()) { index += 1; continue; }
        const fence = line.match(/^\s*```\s*([^\s`]*)\s*$/);
        if (fence) {
            const codeLines = [];
            index += 1;
            while (index < lines.length && !/^\s*```\s*$/.test(lines[index])) codeLines.push(lines[index++]);
            if (index < lines.length) index += 1;
            const codeText = codeLines.join("\n");
            const block = element("div", `${PREFIX}__code`);
            const head = element("div", `${PREFIX}__code-head`);
            head.append(element("span", "", fence[1] || "代码"));
            const copy = element("button", "", "复制代码");
            copy.type = "button";
            copy.addEventListener("click", async () => {
                await copyText(codeText);
                copy.textContent = "已复制";
                setTimeout(() => { copy.textContent = "复制代码"; }, 1200);
            });
            head.append(copy);
            const pre = document.createElement("pre");
            const code = document.createElement("code");
            code.textContent = codeText;
            pre.append(code);
            block.append(head, pre);
            root.append(block);
            continue;
        }
        const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+)$/);
        if (heading) {
            const value = document.createElement(`h${heading[1].length}`);
            appendInlineMarkdown(value, heading[2]);
            root.append(value);
            index += 1;
            continue;
        }
        if (/^\s*([-*_])(?:\s*\1){2,}\s*$/.test(line)) {
            root.append(document.createElement("hr"));
            index += 1;
            continue;
        }
        if (/^\s*>\s?/.test(line)) {
            const quoteLines = [];
            while (index < lines.length && /^\s*>\s?/.test(lines[index])) quoteLines.push(lines[index++].replace(/^\s*>\s?/, ""));
            const quote = document.createElement("blockquote");
            appendInlineMarkdown(quote, quoteLines.join("\n"));
            root.append(quote);
            continue;
        }
        const listMatch = line.match(/^\s*([-+*]|\d+[.)])\s+(.+)$/);
        if (listMatch) {
            const ordered = /^\d/.test(listMatch[1]);
            const list = document.createElement(ordered ? "ol" : "ul");
            while (index < lines.length) {
                const itemMatch = lines[index].match(/^\s*([-+*]|\d+[.)])\s+(.+)$/);
                if (!itemMatch || /^\d/.test(itemMatch[1]) !== ordered) break;
                const item = document.createElement("li");
                appendInlineMarkdown(item, itemMatch[2]);
                list.append(item);
                index += 1;
            }
            root.append(list);
            continue;
        }
        if (index + 1 < lines.length && line.includes("|") && isTableDivider(lines[index + 1])) {
            const headers = tableCells(line);
            index += 2;
            const rows = [];
            while (index < lines.length && lines[index].trim() && lines[index].includes("|") && !isBlockStart(index)) rows.push(tableCells(lines[index++]));
            const wrap = element("div", `${PREFIX}__table-wrap`);
            const table = document.createElement("table");
            const thead = document.createElement("thead");
            const headRow = document.createElement("tr");
            headers.forEach((value) => { const cell = document.createElement("th"); appendInlineMarkdown(cell, value); headRow.append(cell); });
            thead.append(headRow);
            const tbody = document.createElement("tbody");
            rows.forEach((values) => {
                const row = document.createElement("tr");
                headers.forEach((_, cellIndex) => { const cell = document.createElement("td"); appendInlineMarkdown(cell, values[cellIndex] || ""); row.append(cell); });
                tbody.append(row);
            });
            table.append(thead, tbody);
            wrap.append(table);
            root.append(wrap);
            continue;
        }
        const paragraphLines = [line];
        index += 1;
        while (index < lines.length && lines[index].trim() && !isBlockStart(index)) paragraphLines.push(lines[index++]);
        const paragraph = document.createElement("p");
        appendInlineMarkdown(paragraph, paragraphLines.join("\n"));
        root.append(paragraph);
    }
    return root;
}

function usageSummary(history) {
    const total = { prompt_tokens: 0, completion_tokens: 0, total_tokens: 0, calls: 0, cost: 0, has_cost: false, currency: "", currency_ambiguous: false };
    history.forEach((item) => {
        if (item?.role !== "assistant" || !item.usage || typeof item.usage !== "object") return;
        for (const key of ["prompt_tokens", "completion_tokens", "total_tokens", "calls"]) total[key] += Math.max(0, Number(item.usage[key]) || 0);
        const cost = Number(item.usage.cost);
        if (Number.isFinite(cost) && cost >= 0) {
            total.has_cost = true;
            total.cost += cost;
            const currency = String(item.usage.currency || "").toUpperCase();
            if (!currency) {
                total.currency = "";
                total.currency_ambiguous = true;
            } else if (!total.currency_ambiguous && (!total.currency || total.currency === currency)) total.currency = currency;
            else if (!total.currency_ambiguous && total.currency !== currency) {
                total.currency = "";
                total.currency_ambiguous = true;
            }
        }
    });
    return total;
}

function formatCost(value, currency = "") {
    const amount = Number(value);
    if (!Number.isFinite(amount) || amount < 0) return "后台账单为准";
    const code = String(currency || "").toUpperCase();
    const shown = amount < 0.01 ? amount.toFixed(6) : amount.toFixed(4);
    if (code === "CNY" || code === "RMB") return `¥${shown}`;
    if (code === "USD") return `$${shown}`;
    return `${shown}${code ? ` ${code}` : "（API返回）"}`;
}

function sessionFilename(extension) {
    const stamp = new Date().toISOString().replace(/[:.]/g, "-");
    return `dapao-api-chat-${stamp}.${extension}`;
}

function insertMaterialReference(node, item) {
    const state = node.__dapaoAPIChatState;
    const mention = mentionRange(state?.input);
    if (!state || !mention) return;
    mention.range.deleteContents();
    const chip = createReferenceChip(item);
    const space = document.createTextNode(" ");
    mention.range.insertNode(space);
    mention.range.insertNode(chip);
    const selection = window.getSelection();
    const caret = document.createRange();
    caret.setStartAfter(space);
    caret.collapse(true);
    selection.removeAllRanges();
    selection.addRange(caret);
    state.syncDraft();
    closeMaterialMenu();
    state.input.focus();
}

function showMaterialMenu(node) {
    const state = node.__dapaoAPIChatState;
    const mention = mentionRange(state?.input);
    if (!state || !mention) return closeMaterialMenu();
    state.manifest = materialManifest(node);
    const items = state.manifest.items.filter((item) => `${item.label} ${item.token} ${item.kind}`.toLowerCase().includes(mention.query));
    closeMaterialMenu();
    if (!items.length) return;
    const menu = element("div", `${PREFIX}-menu`);
    const rows = items.map((item, index) => {
        const row = document.createElement("button");
        row.type = "button";
        const preview = element("span", `${PREFIX}-menu__preview`);
        if (item.src) {
            const image = document.createElement("img");
            image.src = item.src;
            preview.append(image);
        } else preview.textContent = mediaEmoji(item.kind);
        const shown = item.label.startsWith("@") ? item.label : `@${item.label}`;
        row.append(preview, document.createTextNode(`${shown}  →  ${item.token}`));
        row.addEventListener("pointerenter", () => selectMaterialRow(index));
        row.addEventListener("pointerdown", (event) => {
            event.preventDefault();
            event.stopPropagation();
            insertMaterialReference(node, item);
        });
        menu.append(row);
        return row;
    });
    document.body.append(menu);
    const caret = mention.range.getBoundingClientRect();
    const rect = menu.getBoundingClientRect();
    menu.style.left = `${Math.max(8, Math.min(window.innerWidth - rect.width - 8, caret.left))}px`;
    let top = caret.bottom + 7;
    if (top + rect.height > window.innerHeight - 8) top = Math.max(8, caret.top - rect.height - 7);
    menu.style.top = `${top}px`;
    activeMaterialMenu = { element: menu, rows, items, index: 0, node };
    selectMaterialRow(0);
}

function setupChat(node) {
    if (node.__dapaoAPIChatReady || typeof node.addDOMWidget !== "function") return;
    injectStyles();
    node.properties ||= {};

    const userWidget = widget(node, "💬本轮消息");
    const historyWidget = widget(node, "📚会话历史");
    const imageWidget = widget(node, "🖼️图片引用");
    const flowWidget = widget(node, "🧩流程状态");
    const optionsWidget = widget(node, "🧩选项");
    const requestWidget = widget(node, "🆔请求标识");
    const actionWidget = widget(node, "🧭执行动作");
    if (![userWidget, historyWidget, imageWidget, flowWidget, optionsWidget, requestWidget, actionWidget].every(Boolean)) return;
    node.__dapaoAPIChatReady = true;
    [userWidget, historyWidget, imageWidget, flowWidget, optionsWidget, requestWidget, actionWidget].forEach(hideBackendWidget);

    const root = element("div", PREFIX);
    const top = element("div", `${PREFIX}__top`);
    const stage = element("span", `${PREFIX}__stage`, "未开始");
    const skill = element("span", `${PREFIX}__skill`, "普通对话");
    const meter = element("div", `${PREFIX}__meter`);
    const ring = element("div", `${PREFIX}__ring`);
    const percent = element("span", `${PREFIX}__percent`, "--");
    const meterCopy = element("div", `${PREFIX}__meter-copy`);
    const tokenLine = element("strong", "", "已用约 --");
    const roundLine = element("span", "", "轮数 --/--");
    const costLine = element("span", "", "费用 --");
    const toolbar = element("div", `${PREFIX}__toolbar`);
    const exportMarkdownButton = element("button", "", "导出MD");
    const exportJsonButton = element("button", "", "导出JSON");
    const importButton = element("button", "", "导入会话");
    const undoButton = element("button", "", "撤销清空");
    const cancelEditButton = element("button", "", "取消编辑");
    const toolbarSpacer = element("span", `${PREFIX}__toolbar-spacer`);
    const bottomButton = element("button", "", "回到底部");
    const importInput = document.createElement("input");
    const messages = element("div", `${PREFIX}__messages`);
    const options = element("div", `${PREFIX}__options`);
    const compose = element("div", `${PREFIX}__compose`);
    const inputWrap = element("div", `${PREFIX}__input-wrap`);
    const attachments = element("div", `${PREFIX}__attachments`);
    const input = element("div", `${PREFIX}__input`);
    const actions = element("div", `${PREFIX}__actions`);
    const sendButton = element("button", `${PREFIX}__button ${PREFIX}__button--send`, "发送");
    const clearButton = element("button", `${PREFIX}__button`, "清空");
    const clearContextButton = element("button", `${PREFIX}__button ${PREFIX}__button--context`, "清除上下文");
    const publishButton = element("button", `${PREFIX}__button ${PREFIX}__button--publish`, "发送最终状态");
    const status = element("div", `${PREFIX}__status`, "准备就绪");
    input.contentEditable = "true";
    input.spellcheck = false;
    input.dataset.placeholder = "输入消息；键入 @ 选择素材；Enter 发送，Shift+Enter 换行";
    importInput.type = "file";
    importInput.accept = ".json,application/json";
    importInput.hidden = true;
    undoButton.hidden = true;
    cancelEditButton.hidden = true;
    undoButton.dataset.tone = "accent";
    cancelEditButton.dataset.tone = "danger";
    messages.setAttribute("role", "log");
    messages.setAttribute("aria-live", "polite");
    status.setAttribute("aria-live", "polite");
    clearContextButton.title = "保留聊天记录，但下次发送不再把旧记录交给模型";
    publishButton.title = "不调用模型，把Skill最终结果或最近助手回复发送给已连接的下游";
    [sendButton, clearButton, clearContextButton, publishButton, exportMarkdownButton, exportJsonButton, importButton, undoButton, cancelEditButton, bottomButton].forEach((button) => { button.type = "button"; });
    ring.append(percent);
    meterCopy.append(tokenLine, roundLine, costLine);
    meter.append(ring, meterCopy);
    top.append(element("span", `${PREFIX}__top-label`, "流程"), stage, skill, meter);
    toolbar.append(exportMarkdownButton, exportJsonButton, importButton, undoButton, cancelEditButton, toolbarSpacer, bottomButton);
    inputWrap.append(attachments, input);
    actions.append(sendButton, clearButton, clearContextButton, publishButton);
    compose.append(inputWrap, actions);
    root.append(top, toolbar, messages, options, compose, status, importInput);
    ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "wheel"].forEach((name) => root.addEventListener(name, (event) => event.stopPropagation()));
    let manifest = materialManifest(node);
    renderEditor(input, String(userWidget.value || ""), manifest);

    const renderMessages = (scrollToBottom = true) => {
        const history = historyValue(historyWidget.value);
        messages.replaceChildren();
        if (!history.length) {
            messages.append(element("div", `${PREFIX}__empty`, "开始一段对话，或连接 Skill 进入分阶段工作流"));
            return;
        }
        history.forEach((item, index) => {
            const block = element("article", `${PREFIX}__message ${PREFIX}__message--${item.role}`);
            const imageCount = Array.isArray(item.images) ? item.images.length : 0;
            const materialCount = Array.isArray(item.materials) ? item.materials.length : 0;
            const suffix = [imageCount ? `直传图片${imageCount}` : "", materialCount ? `@素材${materialCount}` : ""].filter(Boolean).join(" · ");
            block.append(element("span", `${PREFIX}__role`, item.role === "user" ? `用户${suffix ? ` · ${suffix}` : ""}` : "助手"));
            const body = element("div", `${PREFIX}__body`);
            body.append(renderMarkdown(item.content));
            const longMessage = item.content.length > 2400 || item.content.split("\n").length > 32;
            const messageKey = `${item.created_at || 0}-${index}-${item.content.length}`;
            node.properties.dapaoAPIExpandedMessages ||= {};
            const expanded = Boolean(node.properties.dapaoAPIExpandedMessages[messageKey]);
            if (longMessage && !expanded) body.dataset.collapsed = "true";
            block.append(body);
            const meta = element("div", `${PREFIX}__meta`);
            const usage = item.role === "assistant" && item.usage && typeof item.usage === "object" ? item.usage : null;
            const details = usage && Number(usage.total_tokens) > 0
                ? [
                    `输入 ${formatTokens(usage.prompt_tokens)}`,
                    `输出 ${formatTokens(usage.completion_tokens)}`,
                    `${formatTokens(usage.total_tokens)} tokens`,
                    Number(usage.calls) > 1 ? `${Number(usage.calls)}次调用` : "",
                    Object.prototype.hasOwnProperty.call(usage, "cost") ? formatCost(usage.cost, usage.currency) : "费用以后台为准",
                    formatTime(item.created_at),
                ].filter(Boolean)
                : [
                    Number.isFinite(Number(item.token_count)) ? `约 ${Math.round(Number(item.token_count))} tokens` : "",
                    item.role === "assistant" ? "费用以后台为准" : "",
                    formatTime(item.created_at),
                ].filter(Boolean);
            meta.append(element("span", "", details.join(" · ")));
            const copyButton = element("button", "", "复制");
            copyButton.type = "button";
            copyButton.title = "复制这条消息";
            copyButton.addEventListener("click", () => copyText(item.content));
            meta.append(copyButton);
            if (longMessage) {
                const expandButton = element("button", "", expanded ? "收起" : "展开");
                expandButton.type = "button";
                expandButton.addEventListener("click", () => {
                    const next = body.dataset.collapsed === "true";
                    body.dataset.collapsed = String(!next);
                    expandButton.textContent = next ? "收起" : "展开";
                    if (next) node.properties.dapaoAPIExpandedMessages[messageKey] = true;
                    else delete node.properties.dapaoAPIExpandedMessages[messageKey];
                    node.graph?.setDirtyCanvas?.(true, true);
                });
                meta.append(expandButton);
            }
            if (item.role === "user") {
                const editButton = element("button", "", "编辑重发");
                editButton.type = "button";
                editButton.title = "从这条用户消息开始创建新分支";
                editButton.addEventListener("click", () => beginBranchEdit(index));
                const deleteButton = element("button", "", "从此删除");
                deleteButton.type = "button";
                deleteButton.title = "删除本轮及其后的消息；再次点击确认";
                deleteButton.addEventListener("click", () => deleteFrom(index, deleteButton));
                meta.append(editButton, deleteButton);
            }
            if (item.role === "assistant" && index === history.length - 1) {
                const retry = element("button", "", "重生");
                retry.type = "button";
                retry.title = "重新生成最后一条回复";
                retry.addEventListener("click", () => regenerate());
                meta.append(retry);
            }
            block.append(meta);
            messages.append(block);
        });
        if (scrollToBottom) messages.scrollTop = messages.scrollHeight;
    };

    const renderFlow = () => {
        const state = parse(flowWidget.value, {});
        stage.textContent = String(state.stage || "未开始");
        stage.title = stage.textContent;
        skill.textContent = state.skill_name || state.skill || "普通对话";
        skill.title = skill.textContent;
        options.replaceChildren();
        optionsValue(optionsWidget.value).forEach((value) => {
            const button = element("button", `${PREFIX}__option`, value);
            button.type = "button";
            button.title = value;
            button.addEventListener("click", () => {
                if (node.__dapaoAPIChatBusy) return;
                renderEditor(input, value, manifest);
                send();
            });
            options.append(button);
        });
    };

    const renderContext = () => {
        const state = node.properties.dapaoAPIContextState || {};
        const history = historyValue(historyWidget.value);
        const cutoff = Math.max(0, Number(parse(flowWidget.value, {}).context_cutoff) || 0);
        const activeHistory = cutoff
            ? history.filter((item) => Number.isFinite(Number(item.created_at)) && Number(item.created_at) > cutoff)
            : history;
        const totals = usageSummary(activeHistory);
        const hasHistory = activeHistory.length > 0;
        const used = Math.max(0, Number(state.used_tokens) || 0);
        const limit = Math.max(0, Number(state.context_limit) || 0);
        if (!hasHistory || !limit) {
            percent.textContent = "--";
            tokenLine.textContent = "已用约 --";
            roundLine.textContent = "轮数 --/--";
            costLine.textContent = "费用 --";
            ring.style.background = "conic-gradient(#55bd80 0deg, #464950 0deg)";
            meter.title = "完成一次回复后显示上下文占用";
            return;
        }
        const rawPercent = used / limit * 100;
        const color = rawPercent >= 90 ? "#df7777" : rawPercent >= 75 ? "#d7a84f" : "#55bd80";
        percent.textContent = `${Math.round(rawPercent)}%`;
        tokenLine.textContent = `上下文 ${formatTokens(used)}/${formatTokens(limit)}`;
        roundLine.textContent = `本轮 ${formatTokens(state.round_total_tokens || state.billed_tokens)} · ${state.current_rounds || 0}/${state.max_rounds || "--"}轮`;
        costLine.textContent = `费用 ${totals.has_cost ? formatCost(totals.cost, totals.currency) : "后台结算"}`;
        ring.style.background = `conic-gradient(${color} ${Math.min(100, rawPercent) * 3.6}deg, #464950 0deg)`;
        meter.title = [
            `模型：${state.model || "--"}`,
            `上下文已使用约 ${Math.round(used)} tokens`,
            `总上下文剩余约 ${Math.round(Number(state.total_remaining_tokens) || 0)} tokens`,
            `本轮输入预算 ${Math.round(Number(state.prompt_budget) || 0)} tokens`,
            `预留输出 ${Math.round(Number(state.output_reserve) || 0)} tokens`,
            `统计来源：${state.usage_source === "api" ? "API usage" : "本地估算"}`,
            `本轮API调用 ${Number(state.api_calls) || 0} 次，输入 ${Number(state.round_prompt_tokens) || 0}，输出 ${Number(state.round_completion_tokens) || 0}，合计 ${Number(state.round_total_tokens || state.billed_tokens) || 0} tokens`,
            `当前保留会话API用量 ${totals.total_tokens || 0} tokens，共 ${totals.calls || 0} 次调用`,
            `当前保留会话费用：${totals.has_cost ? formatCost(totals.cost, totals.currency) : "接口未返回金额，以dapaoAI后台账单为准"}`,
            Number(state.trimmed_messages) > 0 ? `已裁剪 ${state.trimmed_messages} 条旧消息` : "本轮未裁剪历史",
        ].join("\n");
    };

    const renderAttachments = () => {
        const images = imageValue(imageWidget.value);
        attachments.replaceChildren();
        images.forEach((image, index) => {
            const chip = element("span", `${PREFIX}__attachment`, `图片${index + 1}`);
            chip.title = image.filename;
            const remove = element("button", "", "移除");
            remove.type = "button";
            remove.addEventListener("click", () => {
                const next = imageValue(imageWidget.value);
                next.splice(index, 1);
                setWidgetValue(node, imageWidget, JSON.stringify(next));
                renderAttachments();
            });
            chip.append(remove);
            attachments.append(chip);
        });
    };

    let undoState = null;
    let undoTimer = 0;
    let branchEdit = null;
    let pendingBranchRollback = null;

    const sessionSnapshot = () => ({
        format: "dapao-api-chat-session",
        version: 1,
        exported_at: new Date().toISOString(),
        history: branchEdit?.history || historyValue(historyWidget.value),
        flow: branchEdit?.flow || parse(flowWidget.value, {}),
        options: branchEdit?.options || optionsValue(optionsWidget.value),
        context: branchEdit?.context || node.properties.dapaoAPIContextState || {},
        draft: textFromEditor(input),
        legacy_images: imageValue(imageWidget.value),
    });

    const clearUndo = () => {
        if (undoTimer) window.clearTimeout(undoTimer);
        undoTimer = 0;
        undoState = null;
        undoButton.hidden = true;
    };

    const rememberUndo = (snapshot, label) => {
        clearUndo();
        undoState = snapshot;
        undoButton.textContent = label;
        undoButton.hidden = false;
        undoTimer = window.setTimeout(clearUndo, 60000);
    };

    const estimatedContext = (history, current = {}) => {
        const limit = Math.max(0, Number(current.context_limit) || 0);
        const used = history.reduce((total, item) => total + Math.max(0, Number(item.token_count) || 0), 0);
        const lastUsage = [...history].reverse().find((item) => item.role === "assistant" && item.usage)?.usage || {};
        return {
            ...current,
            used_tokens: limit ? Math.min(limit, used) : used,
            total_remaining_tokens: limit ? Math.max(0, limit - used) : 0,
            current_rounds: history.filter((item) => item.role === "user").length,
            usage_source: "estimated",
            round_prompt_tokens: Number(lastUsage.prompt_tokens) || 0,
            round_completion_tokens: Number(lastUsage.completion_tokens) || 0,
            round_total_tokens: Number(lastUsage.total_tokens) || 0,
            api_calls: Number(lastUsage.calls) || 0,
            billed_tokens: Number(lastUsage.total_tokens) || 0,
        };
    };

    const applySession = (raw, message = "会话已恢复") => {
        const source = Array.isArray(raw) ? { history: raw } : raw;
        if (!source || typeof source !== "object") throw new Error("会话文件必须是JSON对象或历史数组");
        const encodedHistory = JSON.stringify(source.history || []);
        if (encodedHistory.length > 4_000_000) throw new Error("会话历史超过4MB上限");
        const history = historyValue(encodedHistory).slice(-200);
        if ((source.history || []).length && !history.length) throw new Error("没有找到有效的用户或助手消息");
        if (history.some((item) => item.content.length > 500000)) throw new Error("单条消息超过50万字符上限");
        const flow = source.flow && typeof source.flow === "object" ? source.flow : {};
        const sessionOptions = Array.isArray(source.options) ? source.options.filter((item) => typeof item === "string").slice(0, 6) : [];
        const context = source.context && typeof source.context === "object" ? source.context : estimatedContext(history, {});
        const draft = typeof source.draft === "string" ? source.draft.slice(0, 200000) : "";
        const legacyImages = imageValue(JSON.stringify(source.legacy_images || []));
        branchEdit = null;
        cancelEditButton.hidden = true;
        setWidgetValue(node, historyWidget, JSON.stringify(history));
        setWidgetValue(node, flowWidget, JSON.stringify(flow));
        setWidgetValue(node, optionsWidget, JSON.stringify(sessionOptions));
        setWidgetValue(node, userWidget, draft);
        setWidgetValue(node, imageWidget, JSON.stringify(legacyImages));
        setWidgetValue(node, requestWidget, `${Date.now()}-session`);
        node.properties.dapaoAPIContextState = context;
        renderEditor(input, draft, manifest);
        renderMessages(); renderFlow(); renderContext(); renderAttachments();
        status.textContent = message;
        status.dataset.state = "idle";
        node.graph?.setDirtyCanvas?.(true, true);
    };

    const exportMarkdown = () => {
        const snapshot = sessionSnapshot();
        const lines = ["# dapaoAI 多轮对话记录", "", `导出时间：${snapshot.exported_at}`, ""];
        snapshot.history.forEach((item) => {
            const role = item.role === "user" ? "用户" : "助手";
            const time = formatTime(item.created_at);
            lines.push(`## ${role}${time ? ` · ${time}` : ""}`, "", item.content, "");
            if (item.role === "assistant" && item.usage) {
                const usage = item.usage;
                lines.push(`> 输入 ${usage.prompt_tokens || 0} · 输出 ${usage.completion_tokens || 0} · 总计 ${usage.total_tokens || 0} tokens · ${Object.prototype.hasOwnProperty.call(usage, "cost") ? formatCost(usage.cost, usage.currency) : "费用以后台账单为准"}`, "");
            }
        });
        downloadText(sessionFilename("md"), lines.join("\n"), "text/markdown;charset=utf-8");
        status.textContent = `已导出 ${snapshot.history.length} 条消息为Markdown`;
    };

    const beginBranchEdit = (index) => {
        if (node.__dapaoAPIChatBusy) return;
        if (branchEdit) cancelBranchEdit();
        const history = historyValue(historyWidget.value);
        const item = history[index];
        if (!item || item.role !== "user") return;
        const followingAssistant = history[index + 1]?.role === "assistant" ? history[index + 1] : null;
        const baseFlow = followingAssistant?.flow_before || parse(flowWidget.value, {});
        branchEdit = {
            index,
            history,
            baseFlow,
            flow: parse(flowWidget.value, {}),
            options: optionsValue(optionsWidget.value),
            context: node.properties.dapaoAPIContextState || {},
            draft: textFromEditor(input),
            images: imageValue(imageWidget.value),
        };
        setWidgetValue(node, flowWidget, JSON.stringify(baseFlow));
        setWidgetValue(node, optionsWidget, "[]");
        setWidgetValue(node, imageWidget, JSON.stringify(item.images || []));
        renderEditor(input, item.content, manifest);
        syncDraft();
        renderFlow(); renderAttachments();
        cancelEditButton.hidden = false;
        status.textContent = `正在编辑第 ${history.slice(0, index + 1).filter((entry) => entry.role === "user").length} 轮；发送后将替换此处及后续消息`;
        status.dataset.state = "busy";
        input.focus();
    };

    const cancelBranchEdit = () => {
        if (!branchEdit || node.__dapaoAPIChatBusy) return;
        setWidgetValue(node, flowWidget, JSON.stringify(branchEdit.flow));
        setWidgetValue(node, optionsWidget, JSON.stringify(branchEdit.options));
        setWidgetValue(node, imageWidget, JSON.stringify(branchEdit.images));
        node.properties.dapaoAPIContextState = branchEdit.context;
        renderEditor(input, branchEdit.draft, manifest);
        syncDraft();
        branchEdit = null;
        cancelEditButton.hidden = true;
        renderFlow(); renderContext(); renderAttachments();
        status.textContent = "已取消编辑，原会话未改变";
        status.dataset.state = "idle";
    };

    const deleteFrom = (index, button) => {
        if (node.__dapaoAPIChatBusy) return;
        if (branchEdit) { cancelBranchEdit(); return; }
        if (button.dataset.armed !== "true") {
            button.dataset.armed = "true";
            button.textContent = "确认删除";
            status.textContent = "再次点击“确认删除”，将删除本轮及其后的消息";
            status.dataset.state = "error";
            window.setTimeout(() => {
                if (!button.isConnected) return;
                button.dataset.armed = "false";
                button.textContent = "从此删除";
            }, 3500);
            return;
        }
        const snapshot = sessionSnapshot();
        const history = historyValue(historyWidget.value);
        const followingAssistant = history[index + 1]?.role === "assistant" ? history[index + 1] : null;
        const nextHistory = history.slice(0, index);
        setWidgetValue(node, historyWidget, JSON.stringify(nextHistory));
        setWidgetValue(node, flowWidget, JSON.stringify(followingAssistant?.flow_before || {}));
        setWidgetValue(node, optionsWidget, "[]");
        setWidgetValue(node, requestWidget, `${Date.now()}-delete`);
        node.properties.dapaoAPIContextState = estimatedContext(nextHistory, node.properties.dapaoAPIContextState || {});
        branchEdit = null;
        cancelEditButton.hidden = true;
        rememberUndo(snapshot, "撤销删除");
        renderMessages(); renderFlow(); renderContext();
        status.textContent = "已删除本轮及其后的消息，可在60秒内撤销";
        status.dataset.state = "idle";
    };

    const setBusy = (busy, message = busy ? "正在请求 dapaoAI..." : "准备就绪", state = busy ? "busy" : "idle") => {
        node.__dapaoAPIChatBusy = busy;
        [sendButton, clearButton, clearContextButton, publishButton].forEach((target) => { target.disabled = busy; });
        [importButton, undoButton, cancelEditButton].forEach((target) => { target.disabled = busy; });
        input.contentEditable = busy ? "false" : "true";
        input.dataset.disabled = String(busy);
        options.querySelectorAll("button").forEach((target) => { target.disabled = busy; });
        status.textContent = message;
        status.dataset.state = state;
    };

    const syncDraft = () => {
        const value = textFromEditor(input);
        setWidgetValue(node, userWidget, value);
        setWidgetValue(node, requestWidget, `${Date.now()}-draft`);
        return value;
    };

    const refreshManifest = () => {
        const next = materialManifest(node);
        const currentText = textFromEditor(input);
        const compact = (value) => JSON.stringify(value.items.map(({ kind, slot, token, label, preview_key }) => ({ kind, slot, token, label, preview_key })));
        const changed = compact(manifest) !== compact(next);
        manifest = next;
        if (changed) renderEditor(input, currentText, manifest);
        if (node.__dapaoAPIChatState) node.__dapaoAPIChatState.manifest = manifest;
        return manifest;
    };

    node.__dapaoAPIChatState = { input, syncDraft, refreshManifest, manifest };

    const send = async () => {
        refreshManifest();
        const text = textFromEditor(input).trim();
        const hasImages = imageValue(imageWidget.value).length > 0;
        if ((!text && !hasImages) || node.__dapaoAPIChatBusy) return;
        const stale = [...new Set((text.match(MATERIAL_TOKEN_PATTERN) || []).filter((token) => !manifest.items.some((item) => item.token === token)))];
        if (stale.length) return setBusy(false, `素材已失效或未连接：${stale.join("、")}`, "error");
        const requestId = `${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const activeBranch = branchEdit;
        const originalHistoryValue = String(historyWidget.value || "[]");
        const requestHistory = activeBranch ? activeBranch.history.slice(0, activeBranch.index) : historyValue(historyWidget.value);
        if (activeBranch) {
            setWidgetValue(node, historyWidget, JSON.stringify(requestHistory));
            node.properties.dapaoAPIContextState = estimatedContext(requestHistory, node.properties.dapaoAPIContextState || {});
        }
        setWidgetValue(node, userWidget, text);
        setWidgetValue(node, requestWidget, requestId);
        setBusy(true);
        try {
            const prompt = await chatOnlyPrompt(node, {
                "💬本轮消息": text,
                "📚会话历史": JSON.stringify(requestHistory),
                "🖼️图片引用": String(imageWidget.value || "[]"),
                "🧩流程状态": String(flowWidget.value || "{}"),
                "🧩选项": String(optionsWidget.value || "[]"),
                "🆔请求标识": requestId,
                "🧭执行动作": "chat",
            });
            const queued = await api.queuePrompt(-1, prompt);
            if (queued?.error) throw new Error(queued.error?.message || queued.error);
            node.__dapaoAPIChatPromptId = queued?.prompt_id || queued?.promptId || "";
            pendingBranchRollback = activeBranch;
            branchEdit = null;
            cancelEditButton.hidden = true;
            clearUndo();
            status.textContent = node.__dapaoAPIChatPromptId ? "已发送，等待模型回复..." : "已提交队列，等待模型回复...";
        } catch (error) {
            pendingBranchRollback = null;
            if (activeBranch) {
                setWidgetValue(node, historyWidget, originalHistoryValue);
                branchEdit = activeBranch;
                cancelEditButton.hidden = false;
                renderMessages(false); renderContext();
            }
            setBusy(false, `加入队列失败：${error?.message || error}`, "error");
        }
    };

    const publishFinal = async () => {
        if (node.__dapaoAPIChatBusy) return;
        const history = historyValue(historyWidget.value);
        const flow = parse(flowWidget.value, {});
        const latestReply = [...history].reverse().find((item) => item.role === "assistant")?.content || "";
        const finalValue = String(flow.final_result || latestReply || "").trim();
        if (!finalValue) return setBusy(false, "没有可发送的最终状态，请先完成一轮对话", "error");
        const requestId = `${Date.now()}-publish`;
        setBusy(true, "正在准备最终状态下游任务...");
        try {
            const scoped = await chatAndDownstreamPrompt(node, {
                "💬本轮消息": "",
                "📚会话历史": String(historyWidget.value || "[]"),
                "🖼️图片引用": "[]",
                "🧩流程状态": String(flowWidget.value || "{}"),
                "🧩选项": String(optionsWidget.value || "[]"),
                "🆔请求标识": requestId,
                "🧭执行动作": "publish_final",
            });
            if (!scoped.downstreamCount) return setBusy(false, "没有检测到下游节点，最终状态未发送", "error");
            node.__dapaoAPIChatPublishPending = true;
            const queued = await api.queuePrompt(-1, scoped.prompt);
            if (queued?.error) throw new Error(queued.error?.message || queued.error);
            node.__dapaoAPIChatPromptId = queued?.prompt_id || queued?.promptId || "";
            status.textContent = `最终状态已提交，正在执行 ${scoped.downstreamCount} 个下游节点...`;
        } catch (error) {
            node.__dapaoAPIChatPublishPending = false;
            setBusy(false, `最终状态发送失败：${error?.message || error}`, "error");
        }
    };

    const regenerate = () => {
        if (node.__dapaoAPIChatBusy) return;
        const history = historyValue(historyWidget.value);
        if (history.length < 2 || history.at(-1)?.role !== "assistant" || history.at(-2)?.role !== "user") return;
        beginBranchEdit(history.length - 2);
        send();
    };

    sendButton.addEventListener("click", send);
    publishButton.addEventListener("click", publishFinal);
    exportMarkdownButton.addEventListener("click", exportMarkdown);
    exportJsonButton.addEventListener("click", () => {
        const snapshot = sessionSnapshot();
        downloadText(sessionFilename("json"), JSON.stringify(snapshot, null, 2), "application/json;charset=utf-8");
        status.textContent = `已导出 ${snapshot.history.length} 条消息为JSON`;
        status.dataset.state = "idle";
    });
    importButton.addEventListener("click", () => importInput.click());
    importInput.addEventListener("change", async () => {
        const file = importInput.files?.[0];
        importInput.value = "";
        if (!file || node.__dapaoAPIChatBusy) return;
        if (file.size > 4_000_000) {
            status.textContent = "导入失败：会话JSON不能超过4MB";
            status.dataset.state = "error";
            return;
        }
        try {
            const parsedSession = JSON.parse(await file.text());
            const previous = sessionSnapshot();
            applySession(parsedSession, "会话导入成功；原会话可在60秒内撤销");
            rememberUndo(previous, "撤销导入");
        } catch (error) {
            status.textContent = `导入失败：${error?.message || error}`;
            status.dataset.state = "error";
        }
    });
    undoButton.addEventListener("click", () => {
        if (!undoState || node.__dapaoAPIChatBusy) return;
        const snapshot = undoState;
        clearUndo();
        applySession(snapshot, "已撤销最近一次会话修改");
    });
    cancelEditButton.addEventListener("click", cancelBranchEdit);
    bottomButton.addEventListener("click", () => { messages.scrollTop = messages.scrollHeight; });
    input.addEventListener("input", () => {
        syncDraft();
        showMaterialMenu(node);
    });
    input.addEventListener("keydown", (event) => {
        if (activeMaterialMenu?.node === node) {
            if (event.key === "ArrowDown") { event.preventDefault(); return selectMaterialRow(activeMaterialMenu.index + 1); }
            if (event.key === "ArrowUp") { event.preventDefault(); return selectMaterialRow(activeMaterialMenu.index - 1); }
            if (event.key === "Escape") { event.preventDefault(); return closeMaterialMenu(); }
            if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); return insertMaterialReference(node, activeMaterialMenu.items[activeMaterialMenu.index]); }
        }
        if (event.key === "Enter" && !event.shiftKey && !event.isComposing) { event.preventDefault(); send(); }
    });
    input.addEventListener("click", () => showMaterialMenu(node));
    input.addEventListener("paste", (event) => {
        event.preventDefault();
        event.stopPropagation();
        document.execCommand("insertText", false, event.clipboardData?.getData("text/plain") || "");
    });
    clearButton.addEventListener("click", () => {
        if (node.__dapaoAPIChatBusy) return;
        const snapshot = sessionSnapshot();
        setWidgetValue(node, historyWidget, "[]");
        setWidgetValue(node, userWidget, "");
        setWidgetValue(node, imageWidget, "[]");
        setWidgetValue(node, flowWidget, "{}");
        setWidgetValue(node, optionsWidget, "[]");
        setWidgetValue(node, requestWidget, `${Date.now()}-clear`);
        node.properties.dapaoAPIContextState = {};
        branchEdit = null;
        cancelEditButton.hidden = true;
        renderEditor(input, "", manifest);
        renderMessages(); renderFlow(); renderContext(); renderAttachments();
        rememberUndo(snapshot, "撤销清空");
        setBusy(false, "会话已清空，可在60秒内撤销");
        node.graph?.setDirtyCanvas?.(true, true);
    });
    clearContextButton.addEventListener("click", () => {
        if (node.__dapaoAPIChatBusy) return;
        const snapshot = sessionSnapshot();
        const history = historyValue(historyWidget.value);
        const cutoff = Date.now();
        setWidgetValue(node, flowWidget, JSON.stringify({
            version: 3,
            skill: "",
            skill_name: "",
            stage: "未开始",
            loaded_references: [],
            final_result: "",
            context_cutoff: cutoff,
        }));
        setWidgetValue(node, optionsWidget, "[]");
        setWidgetValue(node, requestWidget, `${cutoff}-clear-context`);
        node.properties.dapaoAPIContextState = {};
        branchEdit = null;
        cancelEditButton.hidden = true;
        rememberUndo(snapshot, "撤销清除上下文");
        renderMessages(false); renderFlow(); renderContext();
        setBusy(false, `已清除模型上下文，保留 ${history.length} 条聊天记录；下次发送从新会话开始`);
        node.graph?.setDirtyCanvas?.(true, true);
    });

    const chatPanelHeight = (size = node.size) => {
        const nodeHeight = Number(size?.[1] ?? node.size?.[1] ?? CHAT_NODE_DEFAULT_HEIGHT);
        return Math.max(CHAT_PANEL_MIN_HEIGHT, nodeHeight - CHAT_NODE_CHROME_HEIGHT);
    };
    const domWidget = node.addDOMWidget("dapao_api_chat", "dapao_api_chat", root, {
        getMinHeight: () => CHAT_PANEL_MIN_HEIGHT,
        getMaxHeight: () => undefined,
        getHeight: () => chatPanelHeight(),
        hideOnZoom: false,
        hideInPanel: true,
        serialize: false,
    });
    domWidget.options.hideInPanel = true;
    domWidget.computeSize = (width) => [
        Math.max(360, width || node.size?.[0] || 440),
        chatPanelHeight(),
    ];
    const updateLayout = (size = node.size) => {
        root.style.height = `${chatPanelHeight(size)}px`;
        root.style.minHeight = `${CHAT_PANEL_MIN_HEIGHT}px`;
        node.graph?.setDirtyCanvas?.(true, true);
    };
    domWidget.afterResize = () => updateLayout();
    const originalResize = node.onResize;
    node.onResize = function (size) {
        const result = originalResize?.apply(this, arguments);
        updateLayout(size || this.size);
        return result;
    };
    const originalExecuted = node.onExecuted;
    node.onExecuted = function (output) {
        originalExecuted?.apply(this, arguments);
        const nextHistory = first(output?.["📚会话历史"]);
        const nextFlow = first(output?.["🧩流程状态"]);
        const nextOptions = first(output?.["🧩选项"]);
        const nextContext = first(output?.["📊上下文"]);
        const sent = Boolean(first(output?.["✅已发送"]));
        const published = Boolean(node.__dapaoAPIChatPublishPending);
        if (typeof nextHistory === "string") setWidgetValue(node, historyWidget, nextHistory);
        if (typeof nextFlow === "string") setWidgetValue(node, flowWidget, nextFlow);
        if (typeof nextOptions === "string") setWidgetValue(node, optionsWidget, nextOptions);
        if (typeof nextContext === "string") {
            const parsedContext = parse(nextContext, {});
            if (sent || Object.keys(parsedContext).length) node.properties.dapaoAPIContextState = parsedContext;
        }
        if (sent) {
            pendingBranchRollback = null;
            setWidgetValue(node, userWidget, "");
            setWidgetValue(node, imageWidget, "[]");
            renderEditor(input, "", manifest);
        }
        node.__dapaoAPIChatPublishPending = false;
        renderMessages(); renderFlow(); renderContext(); renderAttachments();
        setBusy(false, published ? "最终状态已发送到下游" : "准备就绪");
    };
    const originalConfigure = node.onConfigure;
    node.onConfigure = function () {
        const result = originalConfigure?.apply(this, arguments);
        setTimeout(() => {
            refreshManifest();
            renderEditor(input, String(userWidget.value || ""), manifest);
            renderMessages(); renderFlow(); renderContext(); renderAttachments(); updateLayout();
        }, 0);
        return result;
    };
    const fail = () => {
        if (!node.__dapaoAPIChatBusy) return;
        const publishing = Boolean(node.__dapaoAPIChatPublishPending);
        node.__dapaoAPIChatPublishPending = false;
        let restored = false;
        if (pendingBranchRollback) {
            branchEdit = pendingBranchRollback;
            pendingBranchRollback = null;
            setWidgetValue(node, historyWidget, JSON.stringify(branchEdit.history));
            setWidgetValue(node, flowWidget, JSON.stringify(branchEdit.baseFlow));
            setWidgetValue(node, optionsWidget, "[]");
            node.properties.dapaoAPIContextState = branchEdit.context;
            cancelEditButton.hidden = false;
            renderMessages(false); renderFlow(); renderContext();
            restored = true;
        }
        setBusy(false, publishing
            ? "最终状态下游执行失败，请查看ComfyUI日志中的中文错误"
            : restored ? "生成失败，原历史已恢复；可修改后重试" : "生成失败，请查看ComfyUI日志中的中文错误", "error");
    };
    api.addEventListener("execution_error", fail);
    api.addEventListener("execution_interrupted", fail);
    const originalRemoved = node.onRemoved;
    node.onRemoved = function () {
        api.removeEventListener("execution_error", fail);
        api.removeEventListener("execution_interrupted", fail);
        if (undoTimer) window.clearTimeout(undoTimer);
        closeMaterialMenu();
        return originalRemoved?.apply(this, arguments);
    };
    const currentChatHeight = Number(node.size?.[1]) || 0;
    const safeChatHeight = Math.max(currentChatHeight, CHAT_NODE_DEFAULT_HEIGHT);
    node.setSize([Math.max(node.size?.[0] || 0, 440), safeChatHeight]);
    setTimeout(() => { renderMessages(); renderFlow(); renderContext(); renderAttachments(); updateLayout(); }, 0);
}

function addConfigWidgets(node) {
    if (node.__dapaoAPIConfigWidgets || !node.addCustomWidget) return;
    node.__dapaoAPIConfigWidgets = true;
    const register = {
        name: REGISTER_LABEL,
        type: "DAPAO_API_REGISTER_BUTTON",
        serialize: false,
        hovered: false,
        area: null,
        computeSize: () => [180, 38],
        draw(ctx, nodeRef, width, y, height) {
            const actualWidth = Math.max(180, Number(nodeRef?.size?.[0]) || Number(width) || 180);
            const margin = 8;
            const buttonHeight = Math.max(30, height - 6);
            ctx.save();
            ctx.fillStyle = this.hovered ? "#d99524" : "#a96b1b";
            ctx.beginPath();
            ctx.roundRect(margin, y + 3, actualWidth - margin * 2, buttonHeight, 8);
            ctx.fill();
            ctx.fillStyle = "#fff7df";
            ctx.font = "bold 13px sans-serif";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(REGISTER_LABEL, actualWidth / 2, y + 3 + buttonHeight / 2);
            ctx.restore();
            this.area = { x: margin, y: y + 3, width: actualWidth - margin * 2, height: buttonHeight };
        },
        mouse(event, pos, nodeRef) {
            if (!this.area) return false;
            const inside = pos[0] >= this.area.x && pos[0] <= this.area.x + this.area.width && pos[1] >= this.area.y && pos[1] <= this.area.y + this.area.height;
            if (event.type === "pointermove") { this.hovered = inside; nodeRef.setDirtyCanvas?.(true, true); return inside; }
            if (["pointerdown", "mousedown", "click"].includes(event.type) && inside) {
                const opened = window.open(REGISTER_URL, "_blank");
                if (opened) opened.opener = null;
                return true;
            }
            return false;
        },
    };
    node.addCustomWidget(register);
    node.setSize([Math.max(node.size?.[0] || 0, 340), node.computeSize?.()[1] || node.size?.[1] || 220]);
}

function skillLoaderNodes() {
    const graph = graphOf(null);
    const nodes = graph?._nodes || (graph?.nodes instanceof Map ? [...graph.nodes.values()] : graph?.nodes) || [];
    return nodes.filter((node) => nodeClass(node) === SKILL_NODE);
}

function refreshAllSkillLoaders(catalog = null) {
    skillLoaderNodes().forEach((node) => {
        if (catalog) node.__dapaoSkillManager?.applyCatalog?.(catalog);
        else node.__dapaoSkillManager?.refresh?.();
    });
}

function setupSkillLoader(node) {
    if (node.__dapaoSkillManagerReady || typeof node.addDOMWidget !== "function") return;
    injectStyles();
    const selector = widget(node, "🧩 Skill选择");
    if (!selector) return;
    node.__dapaoSkillManagerReady = true;

    const root = element("div", `${PREFIX}-skills`);
    const header = element("div", `${PREFIX}-skills__header`);
    const count = element("span", `${PREFIX}-skills__count`, "正在读取…");
    const current = element("div", `${PREFIX}-skills__current`, "当前：自动选择");
    const nameInput = document.createElement("input");
    nameInput.className = `${PREFIX}-skills__name`;
    nameInput.type = "text";
    nameInput.maxLength = 60;
    nameInput.placeholder = "选择Skill后可手动修改显示名称";
    const nameRow = element("div", `${PREFIX}-skills__row`);
    const saveButton = element("button", "", "保存显示名");
    const resetButton = element("button", "", "恢复默认名");
    const optimizeRow = element("div", `${PREFIX}-skills__row`);
    const optimizeCurrentButton = element("button", `${PREFIX}-skills__ai`, "✨优化当前技能");
    const optimizeAllButton = element("button", `${PREFIX}-skills__ai`, "✨优化全部技能");
    const uploadRow = element("div", `${PREFIX}-skills__row`);
    const zipButton = element("button", `${PREFIX}-skills__upload`, "上传ZIP");
    const folderButton = element("button", `${PREFIX}-skills__upload`, "上传文件夹");
    const refreshButton = element("button", "", "刷新列表");
    const status = element("div", `${PREFIX}-skills__status`, "显示名独立保存，不修改Skill内容。上传同名Skill不会覆盖。 ");
    const help = element("div", `${PREFIX}-skills__help`, "每次AI优化只调用上游模型一次并按Skill功能描述命名；全部优化不会覆盖手动名称。支持标准Skill目录及repo/skills/*仓库包。");
    const zipInput = document.createElement("input");
    const folderInput = document.createElement("input");
    zipInput.type = folderInput.type = "file";
    zipInput.accept = ".zip,application/zip";
    folderInput.multiple = true;
    folderInput.webkitdirectory = true;
    folderInput.setAttribute("webkitdirectory", "");
    zipInput.hidden = folderInput.hidden = true;
    [saveButton, resetButton, optimizeCurrentButton, optimizeAllButton, zipButton, folderButton, refreshButton].forEach((button) => { button.type = "button"; });
    header.append(element("strong", "", "Skill显示与安装"), count);
    nameRow.append(saveButton, resetButton);
    optimizeRow.append(optimizeCurrentButton, optimizeAllButton);
    uploadRow.style.gridTemplateColumns = "repeat(3, minmax(0, 1fr))";
    uploadRow.append(zipButton, folderButton, refreshButton);
    root.append(header, current, nameInput, nameRow, optimizeRow, uploadRow, status, help, zipInput, folderInput);
    ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "wheel"].forEach((name) => root.addEventListener(name, (event) => event.stopPropagation()));

    let catalog = { skills: [], counts: {} };
    let busy = false;
    const buttons = [saveButton, resetButton, optimizeCurrentButton, optimizeAllButton, zipButton, folderButton, refreshButton];
    const setStatus = (message, state = "idle") => {
        status.textContent = message;
        status.dataset.state = state;
    };
    const setBusy = (value, message = "正在处理…") => {
        busy = value;
        buttons.forEach((button) => { button.disabled = value; });
        nameInput.disabled = value || !skillIdFromLabel(selector.value);
        if (value) setStatus(message, "busy");
    };
    const selectedItem = () => {
        const id = skillIdFromLabel(selector.value);
        return catalog.skills?.find((item) => item.id === id) || null;
    };
    const render = () => {
        const item = selectedItem();
        const counts = catalog.counts || {};
        const optimizerReady = Number(catalog.version || 0) >= 2;
        count.textContent = `${counts.total ?? catalog.skills?.length ?? 0}个｜异常${counts.issues ?? 0}`;
        optimizeAllButton.disabled = busy || !optimizerReady;
        optimizeCurrentButton.disabled = busy || !optimizerReady || !item || item.display_source === "manual";
        if (!item) {
            current.textContent = "当前：自动选择（由对话模型按需求路由）";
            current.title = current.textContent;
            nameInput.value = "";
            nameInput.disabled = true;
            saveButton.disabled = resetButton.disabled = true;
            return;
        }
        const source = item.display_source === "manual" ? "手动" : item.display_source === "model" ? "AI" : "原始资料";
        const issues = Array.isArray(item.issues) && item.issues.length ? `｜原始名称异常：${item.issues.join(", ")}` : "";
        current.textContent = `原始：${item.source_name || item.id}｜当前来源：${source}${issues}`;
        current.title = current.textContent;
        nameInput.value = item.display_name || item.name || item.id;
        nameInput.disabled = busy;
        saveButton.disabled = resetButton.disabled = busy;
    };
    const applyCatalog = (next, desiredId = skillIdFromLabel(selector.value)) => {
        if (!next || !Array.isArray(next.skills)) return;
        catalog = next;
        const values = ["自动选择", ...next.skills.map((item) => item.label)];
        selector.options ||= {};
        selector.options.values = values;
        const matched = desiredId && next.skills.find((item) => item.id === desiredId);
        selector.value = matched?.label || (desiredId ? "自动选择" : (values.includes(selector.value) ? selector.value : "自动选择"));
        node.graph?.setDirtyCanvas?.(true, true);
        render();
        if (Number(next.version || 0) < 2) {
            setStatus("当前仍在运行旧版Skill优化后端。请完整关闭并重新启动ComfyUI；为避免浪费token，AI优化按钮已禁用。", "error");
        }
    };
    const fetchCatalog = async () => {
        const response = await fetch(viewUrl(`/dapao/api-skills/catalog?_=${Date.now()}`), {
            method: "GET",
            cache: "no-store",
            credentials: "same-origin",
        });
        return responseJson(response, "读取Skill列表失败");
    };
    const refresh = async (desiredId = skillIdFromLabel(selector.value), announce = false) => {
        try {
            const next = await fetchCatalog();
            applyCatalog(next, desiredId);
            if (announce) setStatus(`Skill列表已刷新：共 ${next.counts?.total ?? next.skills.length} 个。`);
            return next;
        } catch (error) {
            setStatus(`读取失败：${error?.message || error}`, "error");
            return null;
        }
    };
    const request = async (path, body, message) => {
        // Some ComfyUI frontend builds have dropped the method option while
        // forwarding custom-route requests. Native same-origin fetch keeps
        // this paid action an explicit, single POST with no automatic retry.
        const response = await fetch(viewUrl(path), {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(body),
        });
        return responseJson(response, message);
    };
    const originalCallback = selector.callback;
    selector.callback = function () {
        const result = originalCallback?.apply(this, arguments);
        setTimeout(render, 0);
        return result;
    };
    saveButton.addEventListener("click", async () => {
        const item = selectedItem();
        if (!item || busy) return;
        setBusy(true, "正在保存显示名称…");
        try {
            const next = await request("/dapao/api-skills/display-name", { skill_id: item.id, display_name: nameInput.value }, "保存失败");
            applyCatalog(next, item.id); refreshAllSkillLoaders(next);
            setStatus("显示名称已保存；Skill内容和稳定ID未修改。 ");
        } catch (error) { setStatus(`保存失败：${error?.message || error}`, "error"); }
        finally { setBusy(false); render(); }
    });
    resetButton.addEventListener("click", async () => {
        const item = selectedItem();
        if (!item || busy) return;
        setBusy(true, "正在恢复原始名称…");
        try {
            const next = await request("/dapao/api-skills/display-name", { skill_id: item.id, reset: true }, "恢复失败");
            applyCatalog(next, item.id); refreshAllSkillLoaders(next);
            setStatus("已恢复资料中的默认显示名称。 ");
        } catch (error) { setStatus(`恢复失败：${error?.message || error}`, "error"); }
        finally { setBusy(false); render(); }
    });
    const optimize = async (scope) => {
        if (busy) return;
        try {
            const item = selectedItem();
            if (scope === "selected" && !item) return setStatus("请先在Skill选择中选中要优化的技能。", "error");
            if (scope === "selected" && item.display_source === "manual") {
                return setStatus("当前技能使用手动显示名；请先恢复默认名，再使用AI优化。", "error");
            }
            const config = skillOptimizerConfig(node);
            const targetCount = scope === "selected" ? 1 : (catalog.skills || []).filter((value) => value.display_source !== "manual").length;
            if (!targetCount) return setStatus("没有可由AI优化的技能；手动显示名不会被覆盖。 ");
            setBusy(true, `正在使用 ${config.model || "上游API模型"} ${scope === "selected" ? "优化当前技能" : `统一优化${targetCount}个技能`}…`);
            const result = await request("/dapao/api-skills/optimize-display-names", {
                config,
                scope,
                skill_ids: scope === "selected" ? [item.id] : [],
                overwrite_manual: false,
            }, "AI优化失败");
            applyCatalog(result.catalog); refreshAllSkillLoaders(result.catalog);
            const tokens = Number(result.usage?.total_tokens || 0);
            setStatus(`AI已根据技能功能优化 ${result.updated || 0}/${result.requested || targetCount} 个显示名称${tokens ? `｜本次${tokens} tokens` : ""}。手动名称未覆盖。`);
        } catch (error) { setStatus(`AI优化失败：${error?.message || error}`, "error"); }
        finally { setBusy(false); render(); }
    };
    optimizeCurrentButton.addEventListener("click", () => optimize("selected"));
    optimizeAllButton.addEventListener("click", () => optimize("all"));

    const upload = async (fileList, mode) => {
        const files = [...(fileList || [])];
        if (!files.length || busy) return;
        setBusy(true, mode === "zip" ? "正在安全检查并解压Skill ZIP…" : `正在上传并校验 ${files.length} 个文件…`);
        try {
            const paths = files.map((file) => file.webkitRelativePath || file.name);
            const body = new FormData();
            body.append("mode", mode);
            body.append("paths", JSON.stringify(paths));
            body.append("package_hint", paths[0]?.split(/[\\/]/)[0] || files[0]?.name || "uploaded-skill");
            files.forEach((file, index) => body.append("files", file, `skill-upload-${index}-${file.name}`));
            // Keep multipart boundaries under the browser's control. Some
            // ComfyUI api.fetchApi versions rewrite or drop multipart options.
            const response = await fetch(viewUrl("/dapao/api-skills/install"), {
                method: "POST",
                body,
                cache: "no-store",
                credentials: "same-origin",
            });
            const result = await responseJson(response, "Skill安装失败");
            const installedIds = Array.isArray(result.installed_ids) ? result.installed_ids : [];
            const freshCatalog = await fetchCatalog();
            const installedId = installedIds.find((id) => freshCatalog?.skills?.some((item) => item.id === id));
            if (!installedId) throw new Error("Skill文件已上传，但安装结果没有出现在目录中，请查看后台日志。");
            applyCatalog(freshCatalog, installedId);
            refreshAllSkillLoaders(freshCatalog);
            const warning = result.warnings?.length ? `｜提示：${result.warnings.join("；")}` : "";
            const installedPaths = Array.isArray(result.installed_paths) ? result.installed_paths : [];
            const pathMessage = installedPaths.length ? `｜保存到 skills/${installedPaths.join("、skills/")}` : "";
            const action = result.reused ? "相同内容已存在，已直接选中" : "安装成功并已选中";
            setStatus(`${action}：${installedIds.join("、")}${result.bundle ? "（仓库包）" : ""}${pathMessage}${warning}`);
        } catch (error) {
            await refresh();
            setStatus(`安装失败：${error?.message || error}`, "error");
        }
        finally { setBusy(false); zipInput.value = ""; folderInput.value = ""; render(); }
    };
    zipButton.addEventListener("click", () => zipInput.click());
    folderButton.addEventListener("click", () => folderInput.click());
    refreshButton.addEventListener("click", () => refresh(skillIdFromLabel(selector.value), true));
    zipInput.addEventListener("change", () => upload(zipInput.files, "zip"));
    folderInput.addEventListener("change", () => upload(folderInput.files, "folder"));

    const domWidget = node.addDOMWidget("dapao_api_skill_manager", "dapao_api_skill_manager", root, {
        getMinHeight: () => SKILL_PANEL_HEIGHT,
        getMaxHeight: () => SKILL_PANEL_HEIGHT,
        getHeight: () => SKILL_PANEL_HEIGHT,
        hideOnZoom: false,
        hideInPanel: true,
        serialize: false,
    });
    domWidget.options.hideInPanel = true;
    domWidget.computeSize = (width) => [Math.max(420, width || node.size?.[0] || 480), SKILL_PANEL_HEIGHT];
    root.style.height = `${SKILL_PANEL_HEIGHT}px`;
    node.__dapaoSkillManager = { applyCatalog, refresh, render };
    node.setSize([Math.max(node.size?.[0] || 0, 480), Math.max(node.size?.[1] || 0, node.computeSize?.()[1] || 390)]);
    setTimeout(refresh, 0);
}

function refreshChatMaterialManifests() {
    const graph = graphOf(null);
    const nodes = graph?._nodes || (graph?.nodes instanceof Map ? [...graph.nodes.values()] : graph?.nodes) || [];
    nodes.filter((node) => nodeClass(node) === CHAT_NODE).forEach((node) => node.__dapaoAPIChatState?.refreshManifest?.());
}

function refreshMaterialLibraries() {
    const graph = graphOf(null);
    const nodes = graph?._nodes || (graph?.nodes instanceof Map ? [...graph.nodes.values()] : graph?.nodes) || [];
    nodes.filter((node) => nodeClass(node) === MATERIAL_NODE).forEach((node) => node.__dapaoMaterialLibraryRender?.());
}

function setupMaterialLibrary(node) {
    if (node.__dapaoMaterialLibraryReady || typeof node.addDOMWidget !== "function") return;
    injectStyles();
    const aliasWidget = widget(node, "🏷️素材别名");
    if (!aliasWidget) return;
    node.__dapaoMaterialLibraryReady = true;
    hideBackendWidget(aliasWidget);
    const root = element("div", `${PREFIX}-materials`);
    const status = element("div", `${PREFIX}-materials__status`);
    const list = element("div", `${PREFIX}-materials__list`);
    const help = element("div", `${PREFIX}-materials__help`, "这里只准备素材；只有聊天框本轮明确 @ 后，素材才会压缩并进入API请求。别名不改变固定内部编号。");
    root.append(status, list, help);
    ["pointerdown", "mousedown", "mouseup", "click", "dblclick", "wheel"].forEach((name) => root.addEventListener(name, (event) => event.stopPropagation()));

    let lastSourceSignature = "";
    const render = (preparedManifest = null) => {
        const manifest = preparedManifest || libraryManifest(node);
        lastSourceSignature = materialSourceSignature(manifest);
        const aliases = aliasValue(node);
        list.replaceChildren();
        manifest.items.forEach((item) => {
            const row = element("div", `${PREFIX}-materials__row`);
            const preview = element("span", `${PREFIX}-materials__preview`);
            if (item.src) {
                const image = document.createElement("img");
                image.src = item.src;
                preview.append(image);
            } else preview.textContent = mediaEmoji(item.kind);
            const token = element("span", "", item.token);
            const alias = document.createElement("input");
            alias.type = "text";
            alias.maxLength = 80;
            alias.placeholder = "可选中文别名";
            const key = item.token.slice(1);
            alias.value = String(aliases[key] || "");
            alias.addEventListener("input", () => {
                const next = aliasValue(node);
                const value = alias.value.trim().replace(/^@/, "");
                if (value) next[key] = value;
                else delete next[key];
                setWidgetValue(node, aliasWidget, JSON.stringify(next));
                refreshChatMaterialManifests();
            });
            row.append(preview, token, alias);
            list.append(row);
        });
        const counts = { image: 0, video: 0, audio: 0 };
        manifest.items.forEach((item) => { counts[item.kind] += 1; });
        status.textContent = manifest.items.length
            ? `已准备：图片 ${counts.image}/20｜视频 ${counts.video}/5｜音频 ${counts.audio}/5`
            : "尚未连接素材（支持20图、5视频、5音频）";
        refreshChatMaterialManifests();
    };
    node.__dapaoMaterialLibraryRender = render;
    const liveRefreshTimer = window.setInterval(() => {
        if (!node.graph) return;
        const manifest = libraryManifest(node);
        if (materialSourceSignature(manifest) !== lastSourceSignature) render(manifest);
    }, 300);
    const domWidget = node.addDOMWidget("dapao_api_material_library", "dapao_api_material_library", root, {
        getMinHeight: () => MATERIAL_PANEL_HEIGHT,
        getMaxHeight: () => MATERIAL_PANEL_HEIGHT,
        getHeight: () => MATERIAL_PANEL_HEIGHT,
        hideOnZoom: false,
        hideInPanel: true,
        serialize: false,
    });
    domWidget.options.hideInPanel = true;
    domWidget.computeSize = (width) => [Math.max(400, width || node.size?.[0] || 460), MATERIAL_PANEL_HEIGHT];
    root.style.height = `${MATERIAL_PANEL_HEIGHT}px`;
    const currentMaterialHeight = Number(node.size?.[1]) || 0;
    const safeMaterialHeight = Math.min(
        MATERIAL_NODE_MAX_HEIGHT,
        Math.max(currentMaterialHeight, MATERIAL_NODE_DEFAULT_HEIGHT),
    );
    node.setSize([Math.max(node.size?.[0] || 0, 460), safeMaterialHeight]);
    const originalRemoved = node.onRemoved;
    node.onRemoved = function () {
        window.clearInterval(liveRefreshTimer);
        return originalRemoved?.apply(this, arguments);
    };
    setTimeout(render, 0);
}

function wrapConnectionRefresh(nodeTypeClass, type) {
    const prototype = nodeTypeClass.prototype;
    if (prototype.__dapaoAPIChatConnectionRefresh) return;
    prototype.__dapaoAPIChatConnectionRefresh = true;
    const original = prototype.onConnectionsChange;
    prototype.onConnectionsChange = function () {
        const result = original?.apply(this, arguments);
        setTimeout(() => {
            if (type === MATERIAL_NODE) this.__dapaoMaterialLibraryRender?.();
            if (type === SKILL_NODE) this.__dapaoSkillManager?.render?.();
            refreshChatMaterialManifests();
        }, 0);
        return result;
    };
}

document.addEventListener("pointerdown", (event) => {
    if (activeMaterialMenu && !activeMaterialMenu.element.contains(event.target)) closeMaterialMenu();
}, true);

app.registerExtension({
    name: "Dapao.API.MultiTurnChat",
    nodeCreated(node) {
        const type = nodeClass(node);
        if (type === CHAT_NODE) setupChat(node);
        if (type === MATERIAL_NODE) setupMaterialLibrary(node);
        if (type === SKILL_NODE) setupSkillLoader(node);
        if (type === CONFIG_NODE) setTimeout(() => addConfigWidgets(node), 20);
    },
    loadedGraphNode(node) {
        const type = nodeClass(node);
        if (type === CHAT_NODE) setupChat(node);
        if (type === MATERIAL_NODE) setupMaterialLibrary(node);
        if (type === SKILL_NODE) setupSkillLoader(node);
        if (type === CONFIG_NODE) setTimeout(() => addConfigWidgets(node), 50);
    },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        const type = String(nodeData?.name || "");
        if ([CHAT_NODE, MATERIAL_NODE, SKILL_NODE].includes(type)) wrapConnectionRefresh(nodeTypeClass, type);
    },
    async setup() {
        api.addEventListener("executed", () => {
            materialPreviewEpoch += 1;
            setTimeout(() => { refreshMaterialLibraries(); refreshChatMaterialManifests(); }, 50);
        });
        api.addEventListener("hot_reload_update", () => setTimeout(refreshChatMaterialManifests, 100));
    },
});

console.log("[Dapao API Skill Multi-turn Chat UI] loaded");
