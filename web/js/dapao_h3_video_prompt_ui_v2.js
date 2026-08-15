import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPE = "DapaoH3VideoPromptNode";
const H3_REFERENCE_NODE = "MiniMaxH3ReferenceToVideo";
const H3_IMAGE_NODE = "MiniMaxH3ImageToVideo";
const REGISTER_URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const REGISTER_WIDGET_NAME = "👉点此注册API密钥👈";
const PROMPT_WIDGET_NAME = "📝 原始视频需求";
const AUTO_MANIFEST_WIDGET_NAME = "🧩 H3自动素材清单";
const EXTERNAL_TEXT_INPUT_NAME = "🔗 外部文本输入";
const VIDEO_SAMPLE_COUNT_WIDGET_NAME = "🎞️ 每个视频采样帧数";
const DEFAULT_VIDEO_SAMPLE_COUNT = 5;
const MIN_VIDEO_SAMPLE_COUNT = 2;
const MAX_VIDEO_SAMPLE_COUNT = 8;
const TOKEN_PATTERN = /<(?:Picture|Video|Audio)\s+\d+>/g;

let activeReferenceMenu = null;

function nodeType(node) {
    return node?.comfyClass || node?.type || "";
}

function isNodeType(node, expected) {
    return [node?.comfyClass, node?.type, node?.constructor?.comfyClass, node?.constructor?.type]
        .some((item) => String(item || "") === expected || String(item || "").endsWith(expected));
}

function officialKind(node) {
    if (isNodeType(node, H3_REFERENCE_NODE) || String(node?.title || "") === "MiniMax H3 Reference to Video") return "reference";
    if (isNodeType(node, H3_IMAGE_NODE) || String(node?.title || "") === "MiniMax H3 Image to Video") return "image";
    return "";
}

function widget(node, name) {
    return node?.widgets?.find((item) => item.name === name) || null;
}

function value(node, name, fallback = "") {
    return widget(node, name)?.value ?? fallback;
}

function graphOf(node) {
    return node?.graph
        || app.canvas?.getCurrentGraph?.()
        || app.canvas?.graph
        || app.graph
        || null;
}

function graphLinks(graph) {
    const links = graph?.links;
    if (links instanceof Map || links instanceof Set) return [...links.values()].filter(Boolean);
    if (Array.isArray(links)) return links.filter(Boolean);
    if (links && typeof links[Symbol.iterator] === "function" && typeof links !== "string") {
        return [...links].filter(Boolean);
    }
    return links && typeof links === "object" ? Object.values(links).filter(Boolean) : [];
}

function graphLink(graph, reference) {
    if (reference == null) return null;
    if (typeof reference === "object") return reference;
    if (graph?.links instanceof Map) return graph.links.get(reference) || graph.links.get(String(reference)) || null;
    return graph?.links?.[reference]
        || graph?.links?.[String(reference)]
        || graphLinks(graph).find((link) => String(link?.id) === String(reference))
        || null;
}

function graphNode(graph, id) {
    if (id == null) return null;
    return graph?.getNodeById?.(id)
        || (graph?.nodes instanceof Map ? graph.nodes.get(id) || graph.nodes.get(String(id)) : null)
        || (graph?._nodes_by_id instanceof Map ? graph._nodes_by_id.get(id) || graph._nodes_by_id.get(String(id)) : null)
        || graph?._nodes_by_id?.[id]
        || graph?.nodes?.find?.((node) => String(node?.id) === String(id))
        || graph?._nodes?.find?.((node) => String(node?.id) === String(id))
        || null;
}

function graphNodes(graph) {
    if (Array.isArray(graph?._nodes)) return graph._nodes.filter(Boolean);
    if (Array.isArray(graph?.nodes)) return graph.nodes.filter(Boolean);
    if (graph?.nodes instanceof Map) return [...graph.nodes.values()].filter(Boolean);
    if (graph?._nodes_by_id instanceof Map) return [...graph._nodes_by_id.values()].filter(Boolean);
    if (graph?._nodes_by_id && typeof graph._nodes_by_id === "object") {
        return Object.values(graph._nodes_by_id).filter(Boolean);
    }
    return [];
}

function linkOriginId(link) {
    return link?.origin_id ?? link?.originId ?? link?.[1] ?? null;
}

function linkOriginSlot(link) {
    return Number(link?.origin_slot ?? link?.originSlot ?? link?.[2] ?? 0);
}

function linkTargetId(link) {
    return link?.target_id ?? link?.targetId ?? link?.[3] ?? null;
}

function linkTargetSlot(link) {
    return link?.target_slot ?? link?.targetSlot ?? link?.[4] ?? null;
}

function inputLeafName(input) {
    return String(input?.name || "").split(".").pop();
}

function findInput(node, name) {
    return (node?.inputs || []).find((input) => input?.name === name || inputLeafName(input) === name) || null;
}

function firstInputLink(input) {
    if (!input) return null;
    if (input.link != null) return input.link;
    if (Array.isArray(input.links)) return input.links[0] ?? null;
    if (input.links instanceof Set || input.links instanceof Map) return input.links.values().next().value ?? null;
    if (typeof input.links?.[Symbol.iterator] === "function" && typeof input.links !== "string") {
        return input.links[Symbol.iterator]().next().value ?? null;
    }
    return input.links ?? null;
}

function originNode(node, inputName) {
    const input = typeof inputName === "string" ? findInput(node, inputName) : inputName;
    const graph = graphOf(node);
    let link = graphLink(graph, firstInputLink(input));
    if (!link && graph && node && input) {
        const inputIndex = node.inputs?.indexOf(input);
        link = graphLinks(graph).find((candidate) => {
            if (String(linkTargetId(candidate)) !== String(node.id)) return false;
            const targetSlot = linkTargetSlot(candidate);
            return Number(targetSlot) === inputIndex
                || String(targetSlot) === String(input.name)
                || String(targetSlot) === String(inputLeafName(input));
        }) || null;
    }
    return link ? graphNode(graphOf(node), linkOriginId(link)) : null;
}

function outputTargets(node, slot = 0) {
    const graph = graphOf(node);
    if (!graph) return [];
    const outputLinks = node?.outputs?.[slot]?.links;
    const references = outputLinks instanceof Map || outputLinks instanceof Set ? [...outputLinks.values()]
        : Array.isArray(outputLinks) ? outputLinks
            : outputLinks && typeof outputLinks[Symbol.iterator] === "function" && typeof outputLinks !== "string"
                ? [...outputLinks]
                : outputLinks == null ? [] : [outputLinks];
    const links = references.map((reference) => graphLink(graph, reference)).filter(Boolean);
    links.push(...graphLinks(graph).filter((link) => (
        String(linkOriginId(link)) === String(node?.id) && linkOriginSlot(link) === slot
    )));
    return [...new Map(links.map((link) => [
        String(link?.id ?? `${linkTargetId(link)}:${linkTargetSlot(link)}`),
        link,
    ])).values()]
        .map((link) => graphNode(graph, linkTargetId(link)))
        .filter(Boolean);
}

function downstreamPromptTargets(node) {
    if (isNodeType(node, NODE_TYPE)) return outputTargets(node, 0);
    const result = [];
    (node?.outputs || []).forEach((output, slot) => {
        const type = String(output?.type || "");
        const name = String(output?.name || "");
        if (!type || type === "*" || type === "STRING" || /text|prompt|提示词/i.test(name)) {
            result.push(...outputTargets(node, slot));
        }
    });
    return result;
}

function findOfficialTarget(start) {
    const queue = outputTargets(start, 0).map((node) => ({ node, depth: 1 }));
    const seen = new Set();
    while (queue.length) {
        const current = queue.shift();
        const key = String(current?.node?.id || "");
        if (!current?.node || seen.has(key) || current.depth > 6) continue;
        seen.add(key);
        if (officialKind(current.node)) return current.node;
        downstreamPromptTargets(current.node).forEach((node) => queue.push({ node, depth: current.depth + 1 }));
    }

    // 新旧 ComfyUI 对 output.links 的维护方式不同；必要时从官方节点反向追踪实际输入连线。
    const graph = graphOf(start);
    const reachesStart = (node, visited = new Set()) => {
        if (!node || visited.has(String(node.id))) return false;
        if (node === start || String(node.id) === String(start?.id)) return true;
        visited.add(String(node.id));
        return (node.inputs || []).some((input) => reachesStart(originNode(node, input), visited));
    };
    return graphNodes(graph).find((node) => officialKind(node) && reachesStart(node)) || null;
}

function escapeRegExp(value) {
    return String(value || "").replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function connectedByPrefix(node, prefix) {
    const pattern = new RegExp(`^${escapeRegExp(prefix)}(\\d+)$`);
    return (node?.inputs || [])
        .map((input) => {
            const match = inputLeafName(input).match(pattern);
            const origin = match ? originNode(node, input) : null;
            return origin ? { input, origin, slot: Number(match[1]) } : null;
        })
        .filter(Boolean)
        .sort((a, b) => a.slot - b.slot);
}

function connectedInput(node, name) {
    return Boolean(originNode(node, name));
}

function setInputHidden(node, name, hidden) {
    const target = node?.inputs?.find((item) => item.name === name);
    if (target) target.hidden = Boolean(hidden);
}

function setWidgetValue(node, target, nextValue) {
    if (!target) return;
    const changed = String(target.value ?? "") !== String(nextValue);
    if (changed) {
        target.value = nextValue;
        target.callback?.(nextValue);
    }
    const index = node.widgets?.indexOf(target) ?? -1;
    if (index >= 0) {
        node.widgets_values ??= [];
        node.widgets_values[index] = nextValue;
    }
}

/**
 * 兼容旧工作流的 widgets_values 顺序。
 *
 * H3 节点曾新增过隐藏控件，旧工作流恢复时，后续的数字可能发生位置错配，
 * 导致视频采样帧数被恢复为随机种的 0。ComfyUI 会在调用 Python 前先校验
 * INT 范围，所以必须在节点恢复和序列化阶段把非法值修正，并同步持久化数组。
 */
function normalizeVideoSampleCount(node) {
    const target = widget(node, VIDEO_SAMPLE_COUNT_WIDGET_NAME);
    if (!target) return DEFAULT_VIDEO_SAMPLE_COUNT;
    const numeric = Number(target.value);
    const valid = Number.isInteger(numeric)
        && numeric >= MIN_VIDEO_SAMPLE_COUNT
        && numeric <= MAX_VIDEO_SAMPLE_COUNT;
    const normalized = valid ? numeric : DEFAULT_VIDEO_SAMPLE_COUNT;
    setWidgetValue(node, target, normalized);
    return normalized;
}

function hideWidget(target) {
    if (!target || target.__dapaoH3GeneratorHidden) return;
    target.__dapaoH3GeneratorHidden = true;
    target.computeSize = () => [0, -4];
    const element = target.inputEl || target.element || target.domElement || target.inputElement;
    if (element?.style) element.style.display = "none";
}

function viewUrl(path) {
    if (typeof api.apiURL === "function") return api.apiURL(path);
    if (typeof api.apiURL === "string" && api.apiURL) return `${api.apiURL.replace(/\/$/, "")}${path}`;
    return path;
}

function previewSource(node, seen = new Set()) {
    if (!node || seen.has(String(node.id))) return node;
    seen.add(String(node.id));
    if (Array.isArray(node.imgs) && node.imgs.length) return node;
    if (/reroute/i.test(nodeType(node)) && node.inputs?.[0]) return previewSource(originNode(node, node.inputs[0]), seen);
    return node;
}

function firstPreview(node) {
    const source = previewSource(node);
    const output = app.nodeOutputs?.[String(source?.id)]?.images;
    const file = Array.isArray(output) && output.length ? output[0] : null;
    if (file?.filename) {
        const params = new URLSearchParams({ filename: file.filename, type: file.type || "output", rand: String(Date.now()) });
        if (file.subfolder) params.set("subfolder", file.subfolder);
        return `${viewUrl("/view")}?${params.toString()}`;
    }
    const imageWidget = source?.widgets?.find((item) => item?.name === "image") || source?.widgets?.[0];
    const filename = String(imageWidget?.value || source?.widgets_values?.[0] || "").trim();
    if (filename && isNodeType(source, "LoadImage")) {
        const params = new URLSearchParams({ filename, type: "input", rand: String(Date.now()) });
        return `${viewUrl("/view")}?${params.toString()}`;
    }
    const image = source?.imgs?.[0] || source?.images?.[0];
    if (typeof image === "string") return image;
    return image?.src || image?.currentSrc || "";
}

function referenceManifest(target) {
    if (!target) return { version: 1, target: "", mode: "T2VA", items: [] };
    const items = [];
    if (officialKind(target) === "image") {
        const first = originNode(target, "first_frame");
        const last = originNode(target, "last_frame");
        if (first) items.push({ kind: "Picture", index: 1, token: "<Picture 1>", label: "首帧", source_input: "first_frame", src: firstPreview(first) });
        if (last) {
            const index = first ? 2 : 1;
            items.push({ kind: "Picture", index, token: `<Picture ${index}>`, label: "尾帧", source_input: "last_frame", src: firstPreview(last) });
        }
        return {
            version: 1,
            target: nodeType(target),
            mode: first && last ? "FL2VA" : first ? "I2VA" : last ? "L2VA" : "T2VA",
            items,
        };
    }

    connectedByPrefix(target, "ref_image_").forEach((entry, offset) => {
        const index = offset + 1;
        items.push({ kind: "Picture", index, token: `<Picture ${index}>`, label: `参考图${index}`, source_input: entry.input.name, src: firstPreview(entry.origin) });
    });

    let audioIndex = 0;
    const videos = connectedByPrefix(target, "ref_video_");
    videos.forEach((entry, offset) => {
        const videoIndex = offset + 1;
        const soundtrackInput = `ref_video_audio_${entry.slot}`;
        if (connectedInput(target, soundtrackInput)) {
            audioIndex += 1;
            items.push({ kind: "Audio", index: audioIndex, token: `<Audio ${audioIndex}>`, label: `参考视频${videoIndex}音轨`, source_input: soundtrackInput, src: "" });
        }
        items.push({ kind: "Video", index: videoIndex, token: `<Video ${videoIndex}>`, label: `参考视频${videoIndex}`, source_input: entry.input.name, src: "" });
    });
    connectedByPrefix(target, "ref_audio_").forEach((entry) => {
        audioIndex += 1;
        items.push({ kind: "Audio", index: audioIndex, token: `<Audio ${audioIndex}>`, label: `参考音频${audioIndex}`, source_input: entry.input.name, src: "" });
    });
    return { version: 1, target: nodeType(target), mode: "Ref2VA", items };
}

function serializedManifest(manifest) {
    return JSON.stringify({
        version: 1,
        target: manifest.target,
        mode: manifest.mode,
        items: manifest.items.map(({ src, ...item }) => item),
    });
}

function lockedInputNames(target) {
    const result = new Set();
    if (!target) return result;
    if (officialKind(target) === "image") {
        if (connectedInput(target, "first_frame")) result.add("🎬 首帧图");
        if (connectedInput(target, "last_frame")) result.add("🏁 尾帧图");
        return result;
    }
    const manifest = referenceManifest(target);
    manifest.items.forEach((item) => {
        if (item.kind === "Picture" && item.index <= 9) result.add(`🖼️ 参考图${item.index}`);
        if (item.kind === "Video" && item.index <= 3) result.add(`🎞️ 参考视频${item.index}`);
        if (item.kind === "Audio" && item.index <= 3) result.add(`🎵 参考音频${item.index}`);
    });
    return result;
}

function setInputLocked(input, locked) {
    if (!input) return;
    if (!input.__dapaoH3LockStyle) {
        input.__dapaoH3LockStyle = {
            label: input.label,
            colorOn: input.color_on,
            colorOff: input.color_off,
            tooltip: input.tooltip,
        };
    }
    const original = input.__dapaoH3LockStyle;
    input.__dapaoH3OfficialLocked = Boolean(locked);
    input.disabled = Boolean(locked);
    if (locked) {
        input.label = `${input.name}（官方已接入）`;
        input.color_on = "#7f8792";
        input.color_off = "#555b64";
        input.tooltip = "素材已连接到下游官方MiniMax H3节点，此处已锁定以避免重复接入。";
    } else {
        input.label = original.label;
        input.color_on = original.colorOn;
        input.color_off = original.colorOff;
        input.tooltip = original.tooltip;
    }
}

function refreshInputLocks(node, target) {
    const locked = lockedInputNames(target);
    (node.inputs || []).forEach((input) => setInputLocked(input, locked.has(input.name)));
}

function mediaEmoji(kind) {
    return kind === "Picture" ? "🖼️" : kind === "Video" ? "🎞️" : "🎵";
}

function textFromEditor(editor) {
    let result = "";
    function walk(element) {
        if (element.nodeType === Node.TEXT_NODE) {
            result += element.nodeValue || "";
            return;
        }
        if (element.nodeType !== Node.ELEMENT_NODE) return;
        if (element.classList?.contains("dapao-h3-generator-chip")) {
            result += element.dataset.token || element.textContent || "";
            return;
        }
        if (element.tagName === "BR") {
            result += "\n";
            return;
        }
        [...element.childNodes].forEach(walk);
        if (["DIV", "P"].includes(element.tagName) && element !== editor) result += "\n";
    }
    walk(editor);
    return result.replace(/\n+$/, "");
}

function mentionRange(editor) {
    const selection = window.getSelection();
    if (!editor || !selection?.rangeCount || !editor.contains(selection.anchorNode)
        || selection.anchorNode?.nodeType !== Node.TEXT_NODE) return null;
    const text = (selection.anchorNode.nodeValue || "").slice(0, selection.anchorOffset);
    const match = text.match(/@([^\s@]*)$/u);
    if (!match) return null;
    const range = document.createRange();
    range.setStart(selection.anchorNode, selection.anchorOffset - match[0].length);
    range.setEnd(selection.anchorNode, selection.anchorOffset);
    return { range, query: match[1].toLowerCase() };
}

function createReferenceChip(item) {
    const chip = document.createElement("span");
    chip.className = "dapao-h3-generator-chip";
    chip.dataset.token = item.token;
    chip.contentEditable = "false";
    Object.assign(chip.style, {
        display: "inline-flex", alignItems: "center", gap: "6px", margin: "1px 4px", padding: "3px 9px 3px 5px",
        borderRadius: "9px", border: "1px solid #5b9cff", background: "rgba(42, 88, 150, .62)", color: "#f5f9ff",
        verticalAlign: "middle", whiteSpace: "nowrap", userSelect: "all",
    });
    if (item.src) {
        const image = document.createElement("img");
        image.src = item.src;
        Object.assign(image.style, { width: "28px", height: "28px", borderRadius: "6px", objectFit: "cover" });
        chip.appendChild(image);
    } else {
        const icon = document.createElement("span");
        icon.textContent = mediaEmoji(item.kind);
        chip.appendChild(icon);
    }
    const token = document.createElement("span");
    token.textContent = item.token;
    chip.appendChild(token);
    return chip;
}

function renderPromptEditor(state, valueText) {
    const text = String(valueText || "");
    state.editor.replaceChildren();
    if (!state.manifest.items.length) {
        state.editor.textContent = text;
        if (!text) state.editor.appendChild(document.createElement("br"));
        return;
    }
    const byToken = new Map(state.manifest.items.map((item) => [item.token, item]));
    let offset = 0;
    for (const match of text.matchAll(TOKEN_PATTERN)) {
        if (match.index > offset) state.editor.appendChild(document.createTextNode(text.slice(offset, match.index)));
        const item = byToken.get(match[0]);
        if (item) state.editor.appendChild(createReferenceChip(item));
        else {
            const stale = document.createElement("span");
            stale.textContent = match[0];
            Object.assign(stale.style, { color: "#ff8c8c", textDecoration: "underline wavy" });
            state.editor.appendChild(stale);
        }
        offset = match.index + match[0].length;
    }
    if (offset < text.length) state.editor.appendChild(document.createTextNode(text.slice(offset)));
    if (!state.editor.childNodes.length) state.editor.appendChild(document.createElement("br"));
}

function promptEditorNeedsChipHydration(state, text) {
    const validTokens = new Set(state.manifest.items.map((item) => item.token));
    const expected = (String(text || "").match(TOKEN_PATTERN) || []).filter((token) => validTokens.has(token));
    const actual = [...state.editor.querySelectorAll(".dapao-h3-generator-chip")]
        .map((chip) => chip.dataset.token || chip.textContent || "");
    return expected.length !== actual.length || expected.some((token, index) => token !== actual[index]);
}

function syncPromptEditor(node) {
    const state = node.__dapaoH3PromptEditor;
    if (!state) return;
    setWidgetValue(node, state.promptWidget, textFromEditor(state.editor));
    node.setDirtyCanvas?.(true, true);
}

function closeReferenceMenu() {
    activeReferenceMenu?.element?.remove();
    activeReferenceMenu = null;
}

function selectReferenceMenuRow(index) {
    if (!activeReferenceMenu) return;
    activeReferenceMenu.index = (index + activeReferenceMenu.items.length) % activeReferenceMenu.items.length;
    activeReferenceMenu.rows.forEach((row, rowIndex) => {
        row.style.background = rowIndex === activeReferenceMenu.index ? "rgba(46, 181, 112, .24)" : "transparent";
    });
    activeReferenceMenu.rows[activeReferenceMenu.index]?.scrollIntoView?.({ block: "nearest" });
}

function insertReferenceIntoPrompt(node, item) {
    const state = node.__dapaoH3PromptEditor;
    const mention = mentionRange(state?.editor);
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
    syncPromptEditor(node);
    closeReferenceMenu();
    state.editor.focus();
}

function showReferenceMenu(node) {
    const state = node.__dapaoH3PromptEditor;
    const mention = mentionRange(state?.editor);
    if (!state || !state.manifest.items.length || !mention) {
        closeReferenceMenu();
        return;
    }
    const items = state.manifest.items.filter((item) => {
        const haystack = `${item.label} ${item.token} ${item.kind}`.toLowerCase();
        return !mention.query || haystack.includes(mention.query);
    });
    closeReferenceMenu();
    if (!items.length) return;
    const element = document.createElement("div");
    Object.assign(element.style, {
        position: "fixed", width: "360px", maxWidth: "calc(100vw - 16px)", maxHeight: "360px", overflowY: "auto",
        padding: "8px", borderRadius: "14px", background: "rgba(28, 30, 33, .98)", color: "#f4f4f4",
        boxShadow: "0 18px 48px rgba(0, 0, 0, .48)", border: "1px solid rgba(255, 255, 255, .12)", zIndex: "100000",
    });
    const rows = items.map((item, index) => {
        const row = document.createElement("button");
        row.type = "button";
        Object.assign(row.style, {
            display: "flex", alignItems: "center", gap: "12px", width: "100%", border: "0", borderRadius: "10px",
            padding: "9px", color: "inherit", background: "transparent", cursor: "pointer", textAlign: "left", fontSize: "14px",
        });
        const preview = document.createElement("div");
        Object.assign(preview.style, {
            width: "54px", height: "54px", flex: "0 0 54px", display: "grid", placeItems: "center", overflow: "hidden",
            borderRadius: "8px", background: "rgba(255, 255, 255, .1)", fontSize: "23px",
        });
        if (item.src) {
            const image = document.createElement("img");
            image.src = item.src;
            Object.assign(image.style, { width: "100%", height: "100%", objectFit: "cover" });
            preview.appendChild(image);
        } else preview.textContent = mediaEmoji(item.kind);
        const label = document.createElement("span");
        label.textContent = `${item.label}  →  ${item.token}`;
        row.append(preview, label);
        row.addEventListener("pointerenter", () => selectReferenceMenuRow(index));
        row.addEventListener("pointerdown", (event) => {
            event.preventDefault();
            event.stopPropagation();
            insertReferenceIntoPrompt(node, item);
        });
        element.appendChild(row);
        return row;
    });
    document.body.appendChild(element);
    const caret = mention.range.getBoundingClientRect();
    const rect = element.getBoundingClientRect();
    element.style.left = `${Math.max(8, Math.min(window.innerWidth - rect.width - 8, caret.left))}px`;
    let top = caret.bottom + 8;
    if (top + rect.height > window.innerHeight - 8) top = Math.max(8, caret.top - rect.height - 8);
    element.style.top = `${top}px`;
    activeReferenceMenu = { element, rows, items, index: 0, node };
    selectReferenceMenuRow(0);
}

function setupPromptEditor(node) {
    if (!node?.addDOMWidget || node.__dapaoH3PromptEditor) return;
    const promptWidget = widget(node, PROMPT_WIDGET_NAME);
    const autoManifestWidget = widget(node, AUTO_MANIFEST_WIDGET_NAME);
    if (!promptWidget || !autoManifestWidget) return;
    hideWidget(promptWidget);
    hideWidget(autoManifestWidget);

    const container = document.createElement("div");
    Object.assign(container.style, { width: "100%", height: "100%", minHeight: "270px", boxSizing: "border-box", padding: "8px" });
    const panel = document.createElement("div");
    Object.assign(panel.style, {
        display: "grid", gridTemplateRows: "auto 1fr auto", width: "100%", height: "100%", minHeight: "250px",
        border: "1px solid rgba(255, 255, 255, .18)", borderRadius: "11px", background: "rgba(15, 16, 18, .72)", overflow: "hidden",
    });
    const status = document.createElement("div");
    Object.assign(status.style, { padding: "9px 12px", font: "12px/1.4 sans-serif", color: "#a9d7ff", borderBottom: "1px solid rgba(255,255,255,.08)" });
    const editor = document.createElement("div");
    editor.contentEditable = "true";
    editor.spellcheck = false;
    Object.assign(editor.style, {
        minHeight: "205px", padding: "14px", outline: "none", overflowY: "auto", whiteSpace: "pre-wrap", wordBreak: "break-word",
        color: "#f1f1f1", font: "14px/1.65 sans-serif", caretColor: "#ffffff",
    });
    const warning = document.createElement("div");
    Object.assign(warning.style, { padding: "8px 12px", font: "12px/1.4 sans-serif", borderTop: "1px solid rgba(255,255,255,.08)" });
    panel.append(status, editor, warning);
    container.appendChild(panel);
    const domWidget = node.addDOMWidget("dapao_h3_generator_prompt_editor", "H3_GENERATOR_PROMPT_EDITOR", container, {
        serialize: false,
        hideOnZoom: false,
        getValue: () => textFromEditor(editor),
        setValue: (valueText) => {
            const state = node.__dapaoH3PromptEditor;
            if (state) renderPromptEditor(state, valueText);
        },
        getMinHeight: () => 270,
    });
    node.__dapaoH3PromptEditor = {
        promptWidget, autoManifestWidget, container, editor, status, warning, domWidget,
        manifest: { version: 1, target: "", mode: "T2VA", items: [] },
        renderedManifestKey: "",
    };
    renderPromptEditor(node.__dapaoH3PromptEditor, promptWidget.value || "");
    editor.addEventListener("input", () => { syncPromptEditor(node); showReferenceMenu(node); });
    editor.addEventListener("click", () => showReferenceMenu(node));
    editor.addEventListener("keydown", (event) => {
        if ((event.ctrlKey || event.metaKey) && ["c", "v", "x", "a"].includes(event.key.toLowerCase())) event.stopPropagation();
        if (!activeReferenceMenu || activeReferenceMenu.node !== node) return;
        if (event.key === "ArrowDown") { event.preventDefault(); selectReferenceMenuRow(activeReferenceMenu.index + 1); }
        else if (event.key === "ArrowUp") { event.preventDefault(); selectReferenceMenuRow(activeReferenceMenu.index - 1); }
        else if (event.key === "Enter") { event.preventDefault(); insertReferenceIntoPrompt(node, activeReferenceMenu.items[activeReferenceMenu.index]); }
        else if (event.key === "Escape") { event.preventDefault(); closeReferenceMenu(); }
    });
    editor.addEventListener("paste", (event) => {
        event.preventDefault();
        event.stopPropagation();
        document.execCommand("insertText", false, event.clipboardData?.getData("text/plain") || "");
    });
    ["pointerdown", "pointermove", "dblclick", "wheel"].forEach((name) => container.addEventListener(name, (event) => event.stopPropagation()));
    node.setSize?.([Math.max(Number(node.size?.[0]) || 0, 620), Math.max(Number(node.size?.[1]) || 0, 560)]);
}

function refreshPromptEditor(node, target) {
    const state = node.__dapaoH3PromptEditor;
    if (!state) return;
    const manifest = referenceManifest(target);
    // 未连接官方节点时必须保持为空，避免后端把普通文本误判为T2VA素材清单模式。
    const nextSerialized = target ? serializedManifest(manifest) : "";
    let currentText = textFromEditor(state.editor);
    const storedText = String(state.promptWidget.value || "");
    const sourceText = storedText !== currentText ? storedText : currentText;
    const externalTextConnected = Boolean(originNode(node, EXTERNAL_TEXT_INPUT_NAME));
    state.manifest = manifest;
    state.externalTextConnected = externalTextConnected;
    state.editor.contentEditable = externalTextConnected ? "false" : "true";
    state.editor.style.opacity = externalTextConnected ? "0.62" : "1";
    setWidgetValue(node, state.autoManifestWidget, nextSerialized);
    refreshInputLocks(node, target);
    const manifestChanged = nextSerialized !== String(state.renderedManifestKey || "");
    if (manifestChanged || sourceText !== currentText || promptEditorNeedsChipHydration(state, sourceText)) {
        renderPromptEditor(state, sourceText);
        currentText = textFromEditor(state.editor);
    }
    state.renderedManifestKey = nextSerialized;
    const counts = { Picture: 0, Video: 0, Audio: 0 };
    manifest.items.forEach((item) => { counts[item.kind] += 1; });
    if (externalTextConnected) state.status.textContent = target
        ? "已接入外部文本｜执行时使用外部文本；官方素材 @ 引用请在上游提示词节点完成"
        : "已接入外部文本｜执行时优先使用外部文本，本框内容作为备用";
    else if (!target) state.status.textContent = "普通文本模式｜将最终提示词连接到官方 MiniMax H3 节点后，可使用 @ 引用素材";
    else if (!manifest.items.length) state.status.textContent = "已连接官方H3节点｜当前没有可引用素材";
    else state.status.textContent = `已同步官方素材｜图片 ${counts.Picture}｜视频 ${counts.Video}｜音频 ${counts.Audio}`;
    const stale = target
        ? [...new Set((currentText.match(TOKEN_PATTERN) || []).filter((token) => !manifest.items.some((item) => item.token === token)))]
        : [];
    state.warning.textContent = stale.length
        ? `⚠️ 已失效素材标记：${stale.join("、")}`
        : externalTextConnected
            ? "🔗 外部文本已连接；如需编辑，请先断开外部文本接口"
            : (manifest.items.length ? "输入 @ 选择官方H3节点已连接的素材" : "未连接官方H3时，按普通文本输入");
    state.warning.style.color = stale.length ? "#ff9d8f" : "#8f9aa8";
    node.setDirtyCanvas?.(true, true);
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
        computeSize() {
            return [180, 38];
        },
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
    normalizeVideoSampleCount(node);
    refreshImageInputs(node);
    setupPromptEditor(node);
    refreshPromptEditor(node, findOfficialTarget(node));
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
    normalizeVideoSampleCount(node);
    setupPromptEditor(node);
    ensureRegisterButton(node);
    node.widgets.forEach((target) => wrapCallback(node, target));
    refreshNode(node);
}

function refreshAllNodes() {
    const graph = graphOf(null);
    graph?.findNodesByType?.(NODE_TYPE)?.forEach((node) => setup(node));
}

document.addEventListener("pointerdown", (event) => {
    if (activeReferenceMenu && !activeReferenceMenu.element.contains(event.target)) closeReferenceMenu();
}, true);

app.registerExtension({
    name: "Dapao.H3VideoPrompt.UI",
    async setup() {
        api.addEventListener("hot_reload_update", () => {
            [50, 250, 1000].forEach((delay) => setTimeout(refreshAllNodes, delay));
        });
        api.addEventListener("executed", () => setTimeout(refreshAllNodes, 50));
    },
    nodeCreated(node) {
        if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 20);
    },
    loadedGraphNode(node) {
        if (nodeType(node) === NODE_TYPE) setTimeout(() => setup(node), 50);
    },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        const type = String(nodeData?.name || "");
        if (![NODE_TYPE, H3_REFERENCE_NODE, H3_IMAGE_NODE].includes(type)) return;

        const onConnectionsChange = nodeTypeClass.prototype.onConnectionsChange;
        nodeTypeClass.prototype.onConnectionsChange = function () {
            const result = onConnectionsChange?.apply(this, arguments);
            setTimeout(() => refreshAllNodes(), 0);
            return result;
        };

        const onConfigureOfficial = nodeTypeClass.prototype.onConfigure;
        nodeTypeClass.prototype.onConfigure = function () {
            const result = onConfigureOfficial?.apply(this, arguments);
            setTimeout(() => refreshAllNodes(), 50);
            return result;
        };

        if (type !== NODE_TYPE) return;

        const onConnectInput = nodeTypeClass.prototype.onConnectInput;
        nodeTypeClass.prototype.onConnectInput = function () {
            const slot = arguments[0];
            if (this.inputs?.[slot]?.__dapaoH3OfficialLocked) return false;
            return onConnectInput?.apply(this, arguments);
        };

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
            const result = onConfigure?.apply(this, arguments);
            normalizeVideoSampleCount(this);
            setTimeout(() => setup(this), 50);
            return result;
        };

        const onSerialize = nodeTypeClass.prototype.onSerialize;
        nodeTypeClass.prototype.onSerialize = function () {
            normalizeVideoSampleCount(this);
            const state = this.__dapaoH3PromptEditor;
            if (state) syncPromptEditor(this);
            return onSerialize?.apply(this, arguments);
        };

        const onWidgetChanged = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () {
            const result = onWidgetChanged?.apply(this, arguments);
            normalizeVideoSampleCount(this);
            refreshNode(this);
            return result;
        };

        const onConnectionsChangeNode = nodeTypeClass.prototype.onConnectionsChange;
        nodeTypeClass.prototype.onConnectionsChange = function () {
            const result = onConnectionsChangeNode?.apply(this, arguments);
            setTimeout(() => refreshNode(this), 0);
            return result;
        };
    },
});

console.log("[Dapao H3 Video Prompt UI v2] loaded");
