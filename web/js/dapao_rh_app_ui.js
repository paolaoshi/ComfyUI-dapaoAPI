import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_NAME = "DapaoRHAppNode";
const PARAMS_WIDGET = "🧩 应用参数JSON";
const CHANNEL_WIDGET = "🌐 API渠道";
const API_KEY_WIDGET = "🔑 API密钥";
const APP_ID_WIDGET = "🆔 应用ID";
const INSTANCE_WIDGET = "⚙️ 实例类型";
const EXTRA_PARAMS_WIDGET = "📋 额外节点参数JSON";
const SETUP_VERSION = 10;
const PERSISTED_WIDGETS = [
    CHANNEL_WIDGET,
    API_KEY_WIDGET,
    APP_ID_WIDGET,
    PARAMS_WIDGET,
    INSTANCE_WIDGET,
    EXTRA_PARAMS_WIDGET,
    "🔁 最大轮询秒数",
    "⏱️ 轮询间隔",
    "⌛ 请求超时",
    "🚫 出错时跳过",
];

const KNOWN_OPTIONS = {
    aspectRatio: ["1:1", "16:9", "9:16", "4:3", "3:4", "4:5", "5:4", "3:2", "2:3", "21:9", "9:21", "1:4", "4:1", "1:8", "8:1"],
    aspect_ratio: ["1:1", "16:9", "9:16", "4:3", "3:4", "4:5", "5:4", "3:2", "2:3", "21:9", "9:21"],
    ratio: ["1:1", "16:9", "9:16", "4:3", "3:4", "4:5", "5:4", "3:2", "2:3"],
    resolution: ["1k", "2k", "4k", "8k"],
    size: ["512", "768", "1024", "1280", "1536", "2048"],
    quality: ["low", "medium", "high", "best"],
    mode: ["text2img", "img2img"],
    instanceType: ["default", "plus", "pro"],
    instance_type: ["default", "plus", "pro"],
    precision: ["fp16", "fp32", "bf16"],
    scheduler: ["normal", "karras", "exponential", "sgm_uniform", "simple", "ddim_uniform"],
    sampler: ["euler", "euler_ancestral", "heun", "dpm_2", "dpm_2_ancestral", "lms", "dpmpp_2m", "dpmpp_sde", "ddim", "uni_pc"],
};

function getWidget(node, name) {
    return node?.widgets?.find((widget) => widget.name === name) || null;
}

function getGraphLink(linkId) {
    if (linkId === null || linkId === undefined) return null;
    const links = app.graph?.links;
    return links?.get?.(linkId) || links?.[linkId] || null;
}

function readableNodeValue(node, outputSlot) {
    const output = node?.outputs?.[outputSlot];
    const widgetNames = new Set(["value", "string", "text"]);
    const outputWidget = output?.widget;
    if (typeof outputWidget === "string") widgetNames.add(outputWidget);
    if (outputWidget?.name) widgetNames.add(outputWidget.name);
    if (output?.name) widgetNames.add(String(output.name).toLowerCase());

    const widgets = node?.widgets || [];
    const candidates = widgets.filter((widget) => widgetNames.has(String(widget.name || "").toLowerCase()));
    if (widgets.length === 1 && !candidates.includes(widgets[0])) candidates.push(widgets[0]);
    for (const widget of candidates) {
        if (["string", "number", "boolean"].includes(typeof widget.value) && String(widget.value).trim()) {
            return widget.value;
        }
    }

    for (const key of widgetNames) {
        const value = node?.properties?.[key];
        if (["string", "number", "boolean"].includes(typeof value) && String(value).trim()) return value;
    }
    return undefined;
}

function resolveLinkedValue(node, inputName, visited = new Set()) {
    const input = node?.inputs?.find((item) => item.name === inputName);
    const link = getGraphLink(input?.link);
    if (!link) return undefined;
    const originNode = app.graph?.getNodeById?.(link.origin_id);
    if (!originNode || visited.has(originNode.id)) return undefined;
    visited.add(originNode.id);

    const directValue = readableNodeValue(originNode, link.origin_slot);
    if (directValue !== undefined) return directValue;

    for (const originInput of originNode.inputs || []) {
        if (originInput.link === null || originInput.link === undefined) continue;
        const upstreamValue = resolveLinkedValue(originNode, originInput.name, visited);
        if (upstreamValue !== undefined) return upstreamValue;
    }
    return undefined;
}

function effectiveWidgetValue(node, name, fallback = "") {
    if (hasLinkedInput(node, name)) {
        return resolveLinkedValue(node, name) ?? fallback;
    }
    const localValue = getWidget(node, name)?.value;
    if (localValue !== null && localValue !== undefined && String(localValue).trim()) return localValue;
    return fallback;
}

function hasLinkedInput(node, name) {
    const input = node?.inputs?.find((item) => item.name === name);
    return input?.link !== null && input?.link !== undefined;
}

function isTargetNode(node) {
    return (
        node?.comfyClass === NODE_NAME
        || node?.type === NODE_NAME
        || node?.constructor?.nodeData?.name === NODE_NAME
    );
}

function parseConfig(node) {
    const widget = getWidget(node, PARAMS_WIDGET);
    try {
        const parsed = JSON.parse(widget?.value || "{}");
        return parsed && typeof parsed === "object" ? parsed : {};
    } catch {
        return {};
    }
}

function saveConfig(node, config) {
    const widget = getWidget(node, PARAMS_WIDGET);
    if (widget) widget.value = JSON.stringify(config);
}

function parameterKey(field) {
    return `${field.nodeId}::${field.fieldName}`;
}

function fieldOptions(field) {
    if (Array.isArray(field.options) && field.options.length) return field.options;
    const direct = KNOWN_OPTIONS[field.fieldName];
    if (direct) return direct;
    const lower = String(field.fieldName || "").toLowerCase();
    const knownKey = Object.keys(KNOWN_OPTIONS).find((key) => key.toLowerCase() === lower);
    return knownKey ? KNOWN_OPTIONS[knownKey] : [];
}

function setStatus(node, text, state = "idle") {
    const widget = node._rhAppStatusWidget;
    if (!widget) return;
    widget.value = text;
    widget._rhAppState = state;
    node.setDirtyCanvas(true, true);
}

function moveBefore(node, widget, targetName) {
    const currentIndex = node.widgets?.indexOf(widget) ?? -1;
    const targetIndex = node.widgets?.findIndex((item) => item.name === targetName) ?? -1;
    if (currentIndex < 0 || targetIndex < 0 || currentIndex === targetIndex) return;
    node.widgets.splice(currentIndex, 1);
    const nextTargetIndex = node.widgets.findIndex((item) => item.name === targetName);
    node.widgets.splice(nextTargetIndex, 0, widget);
}

function resizeNode(node) {
    const computed = node.computeSize();
    node.setSize([Math.max(360, Number(node.size?.[0] || 0), Number(computed[0] || 0)), computed[1]]);
}

function refreshNodeLayout(node) {
    resizeNode(node);
    requestAnimationFrame(() => requestAnimationFrame(() => {
        resizeNode(node);
        node.onResize?.(node.size);
        node.setDirtyCanvas(true, true);
        app.canvas?.setDirty(true, true);
    }));
}

function removeDynamicWidgets(node) {
    for (const widget of node._rhAppDynamicWidgets || []) {
        try {
            widget.onRemove?.();
        } catch {
            // LiteGraph widgets generally do not define onRemove.
        }
        const index = node.widgets?.indexOf(widget) ?? -1;
        if (index >= 0) node.widgets.splice(index, 1);
    }
    node._rhAppDynamicWidgets = [];
    node._rhAppFieldValueWidgets = {};
    node._rhAppFieldInputWidgets = {};
}

const DYNAMIC_INPUT_CONFIG = {
    image: { limit: 8, prefix: "🖼️ 图像", type: "IMAGE" },
    video: { limit: 4, prefix: "🎞️ 视频", type: "VIDEO" },
    audio: { limit: 4, prefix: "🎵 音频", type: "AUDIO" },
    text: { limit: 16, prefix: "📝 文本", type: "STRING" },
    number: { limit: 8, prefix: "🔢 数字", type: "FLOAT" },
    boolean: { limit: 8, prefix: "🔘 布尔", type: "BOOLEAN" },
};

function captureDynamicConnections(node) {
    const connections = {};
    for (const config of Object.values(DYNAMIC_INPUT_CONFIG)) {
        for (let index = 1; index <= config.limit; index += 1) {
            const name = `${config.prefix}${index}`;
            const input = node.inputs?.find((item) => item.name === name);
            const link = getGraphLink(input?.link);
            if (!link) continue;
            connections[name] = {
                originId: link.origin_id,
                originSlot: link.origin_slot,
                type: config.type,
            };
        }
    }
    return connections;
}

function reconnectDynamicInputs(node, connections) {
    for (const [name, connection] of Object.entries(connections || {})) {
        const targetSlot = node.inputs?.findIndex((item) => item.name === name) ?? -1;
        if (targetSlot < 0 || String(node.inputs[targetSlot].type) !== String(connection.type)) continue;
        const originNode = app.graph?.getNodeById?.(connection.originId);
        if (!originNode) continue;
        if (node.inputs[targetSlot].link !== null && node.inputs[targetSlot].link !== undefined) {
            node.disconnectInput(targetSlot);
        }
        originNode.connect(connection.originSlot, node, targetSlot);
    }
}

function bindDynamicInputsToWidgets(node, schema) {
    const counters = { image: 0, video: 0, audio: 0, text: 0, number: 0, boolean: 0 };
    for (const field of schema || []) {
        const config = DYNAMIC_INPUT_CONFIG[field.valueType];
        if (!config) continue;
        const fallbackIndex = counters[field.valueType] || 0;
        counters[field.valueType] = fallbackIndex + 1;
        const inputIndex = Number.isFinite(Number(field.inputIndex)) ? Number(field.inputIndex) : fallbackIndex;
        const inputName = `${config.prefix}${inputIndex + 1}`;
        const input = node.inputs?.find((item) => item.name === inputName);
        const anchorWidget = node._rhAppFieldInputWidgets?.[parameterKey(field)];
        if (!input || !anchorWidget) continue;
        input.widget = { name: anchorWidget.name };
        input.label = `${field.fieldName} · #${field.nodeId}`;
        input.localized_name = input.label;
    }
}

function setDynamicInputs(node, schema = []) {
    const connections = {
        ...(node._rhAppPendingConnections || {}),
        ...captureDynamicConnections(node),
    };
    for (const [kind, config] of Object.entries(DYNAMIC_INPUT_CONFIG)) {
        const fields = schema.filter((field) => field?.valueType === kind).slice(0, config.limit);
        const visibleCount = fields.length;

        for (let index = config.limit; index > visibleCount; index -= 1) {
            const name = `${config.prefix}${index}`;
            const inputIndex = node.inputs?.findIndex((item) => item.name === name) ?? -1;
            if (inputIndex >= 0) node.removeInput(inputIndex);
        }

        for (let index = 1; index <= visibleCount; index += 1) {
            const name = `${config.prefix}${index}`;
            if (!node.inputs?.some((item) => item.name === name)) {
                node.addInput(name, config.type);
            }
            const input = node.inputs?.find((item) => item.name === name);
            const field = fields[index - 1];
            if (input && field) {
                input.label = `${field.fieldName} · #${field.nodeId}`;
                input.localized_name = input.label;
            }
        }
    }

    if (!schema.length) {
        node._rhAppPendingConnections = connections;
        return;
    }
    node._rhAppPendingConnections = {};
    reconnectDynamicInputs(node, connections);
}

function syncDynamicValue(node, field, value) {
    const config = parseConfig(node);
    config.values = config.values && typeof config.values === "object" ? config.values : {};
    config.values[parameterKey(field)] = value;
    saveConfig(node, config);
}

function mediaLabel(field) {
    const labels = { image: "图像", video: "视频", audio: "音频" };
    const index = Number(field.mediaIndex || 0) + 1;
    return `${labels[field.valueType] || "媒体"}${index}优先，或填 URL/fileName`;
}

function chooseMediaFile(valueType) {
    const accepts = { image: "image/*", video: "video/*", audio: "audio/*" };
    return new Promise((resolve) => {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = accepts[valueType] || "*/*";
        input.style.display = "none";
        input.addEventListener("change", () => resolve(input.files?.[0] || null), { once: true });
        input.click();
    });
}

async function uploadMediaField(node, field, buttonWidget) {
    const apiChannel = String(effectiveWidgetValue(node, CHANNEL_WIDGET, "国内版")).trim();
    const apiKey = String(effectiveWidgetValue(node, API_KEY_WIDGET)).trim();
    if (!apiKey) {
        setStatus(node, "请先填写或连接 API 密钥", "error");
        return;
    }

    const file = await chooseMediaFile(field.valueType);
    if (!file) return;
    buttonWidget.disabled = true;
    setStatus(node, `正在上传 ${field.fieldName}...`, "loading");
    try {
        const form = new FormData();
        form.append("api_channel", apiChannel);
        form.append("api_key", apiKey);
        form.append("media_type", field.valueType);
        form.append("file", file, file.name);
        const response = await api.fetchApi("/dapao/rh-app/upload", { method: "POST", body: form });
        const responseText = await response.text();
        let result;
        try {
            result = responseText ? JSON.parse(responseText) : {};
        } catch {
            const routeMissing = [404, 405].includes(response.status) || /^404\s*:/i.test(responseText.trim());
            throw new Error(routeMissing
                ? "RH应用上传后端尚未加载，请完全重启 ComfyUI"
                : `上传接口返回了非 JSON 内容（HTTP ${response.status}）`);
        }
        if (!response.ok || result.error || !result.fileName) {
            throw new Error(result.error || `上传失败 HTTP ${response.status}`);
        }

        syncDynamicValue(node, field, result.fileName);
        const valueWidget = node._rhAppFieldValueWidgets?.[parameterKey(field)];
        if (valueWidget) valueWidget.value = result.fileName;
        setStatus(node, `${field.fieldName} 上传成功 · ${file.name}`, "ready");
    } catch (error) {
        setStatus(node, `上传失败：${error?.message || error}`, "error");
    } finally {
        buttonWidget.disabled = false;
        node.setDirtyCanvas(true, true);
    }
}

function addMediaUploadWidget(node, field) {
    const widget = node.addWidget(
        "button",
        `⬆ 上传 ${field.fieldName} · #${field.nodeId}`,
        null,
        () => uploadMediaField(node, field, widget),
    );
    widget.serialize = false;
    widget._rhAppDynamic = true;
    node._rhAppFieldInputWidgets[parameterKey(field)] = widget;
    moveBefore(node, widget, INSTANCE_WIDGET);
    return widget;
}

function addParameterWidget(node, field, value) {
    const suffix = `#${field.nodeId}`;
    const baseLabel = `${field.fieldName} · ${suffix}`;
    const options = fieldOptions(field);
    let widget;

    if (["image", "video", "audio"].includes(field.valueType)) {
        widget = node.addWidget(
            "text",
            `${baseLabel} · ${mediaLabel(field)}`,
            String(value ?? ""),
            (next) => syncDynamicValue(node, field, next),
            { multiline: false },
        );
    } else if (options.length) {
        const normalizedOptions = options.map((item) => String(item));
        const normalizedValue = String(value ?? normalizedOptions[0] ?? "");
        if (normalizedValue && !normalizedOptions.includes(normalizedValue)) normalizedOptions.unshift(normalizedValue);
        widget = node.addWidget(
            "combo",
            baseLabel,
            normalizedValue,
            (next) => syncDynamicValue(node, field, next),
            { values: normalizedOptions },
        );
    } else if (field.valueType === "number") {
        const numberValue = Number(value);
        widget = node.addWidget(
            "number",
            baseLabel,
            Number.isFinite(numberValue) ? numberValue : 0,
            (next) => syncDynamicValue(node, field, next),
            { step: 0.1, precision: 4 },
        );
    } else if (field.valueType === "boolean") {
        const booleanValue = value === true || ["true", "1", "yes", "on"].includes(String(value).toLowerCase());
        widget = node.addWidget(
            "toggle",
            baseLabel,
            booleanValue,
            (next) => syncDynamicValue(node, field, Boolean(next)),
        );
    } else {
        widget = node.addWidget(
            "text",
            baseLabel,
            String(value ?? ""),
            (next) => syncDynamicValue(node, field, next),
            { multiline: true },
        );
    }

    widget.serialize = false;
    widget._rhAppDynamic = true;
    widget._rhAppDescription = field.description || "";
    node._rhAppFieldValueWidgets[parameterKey(field)] = widget;
    if (!["image", "video", "audio"].includes(field.valueType)) {
        node._rhAppFieldInputWidgets[parameterKey(field)] = widget;
    }
    moveBefore(node, widget, INSTANCE_WIDGET);
    return widget;
}

function applySchema(node, incoming, preserveValues = true) {
    const previous = parseConfig(node);
    const sameApplication = (
        previous.webappId === incoming.webappId
        && previous.apiChannel === incoming.apiChannel
    );
    const previousValues = preserveValues && sameApplication && previous.values && typeof previous.values === "object"
        ? previous.values
        : {};
    const values = {};

    for (const field of incoming.schema || []) {
        const key = parameterKey(field);
        values[key] = Object.prototype.hasOwnProperty.call(previousValues, key)
            ? previousValues[key]
            : field.defaultValue ?? "";
    }

    const config = { ...incoming, values };
    saveConfig(node, config);
    removeDynamicWidgets(node);
    node._rhAppFieldValueWidgets = {};
    node._rhAppFieldInputWidgets = {};
    node._rhAppDynamicWidgets = [];
    for (const field of incoming.schema || []) {
        if (["image", "video", "audio"].includes(field.valueType)) {
            node._rhAppDynamicWidgets.push(addMediaUploadWidget(node, field));
        }
        node._rhAppDynamicWidgets.push(addParameterWidget(node, field, values[parameterKey(field)]));
    }
    setDynamicInputs(node, incoming.schema || []);
    bindDynamicInputsToWidgets(node, incoming.schema || []);
    setStatus(
        node,
        `${incoming.appName || "RH应用"} · ID ${incoming.webappId || "-"} · ${incoming.schema?.length || 0} 个参数`,
        "ready",
    );
    refreshNodeLayout(node);
    node.setDirtyCanvas(true, true);
}

async function refreshSchema(node, manual = false) {
    const apiChannel = String(effectiveWidgetValue(node, CHANNEL_WIDGET, "国内版")).trim();
    const apiKey = String(effectiveWidgetValue(node, API_KEY_WIDGET)).trim();
    const webappId = String(effectiveWidgetValue(node, APP_ID_WIDGET)).trim();
    if (!apiKey || !webappId) {
        if (manual) {
            const message = !apiKey && hasLinkedInput(node, API_KEY_WIDGET)
                ? "执行前无法读取上游 API 密钥，请使用普通字符串节点"
                : (!apiKey ? "请先填写 API 密钥" : "请先填写应用ID");
            setStatus(node, message, "error");
        }
        return;
    }

    const saved = parseConfig(node);
    const applicationChanged = (
        Array.isArray(saved.schema)
        && saved.schema.length > 0
        && (
            String(saved.webappId || "") !== webappId
            || String(saved.apiChannel || "国内版") !== apiChannel
        )
    );
    if (applicationChanged) {
        node._rhAppRequestId = (node._rhAppRequestId || 0) + 1;
        removeDynamicWidgets(node);
        setDynamicInputs(node, []);
        saveConfig(node, {});
        resizeNode(node);
    }

    const requestId = (node._rhAppRequestId || 0) + 1;
    node._rhAppRequestId = requestId;
    setStatus(node, "正在读取应用参数...", "loading");
    if (node._rhAppRefreshWidget) node._rhAppRefreshWidget.disabled = true;
    try {
        const response = await api.fetchApi("/dapao/rh-app/schema", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ api_channel: apiChannel, api_key: apiKey, webapp_id: webappId }),
        });
        const responseText = await response.text();
        let result;
        try {
            result = responseText ? JSON.parse(responseText) : {};
        } catch {
            const routeMissing = [404, 405].includes(response.status) || /^404\s*:/i.test(responseText.trim());
            throw new Error(routeMissing
                ? "RH应用后端尚未加载，请完全关闭并重新启动 ComfyUI"
                : `本地接口返回了非 JSON 内容（HTTP ${response.status}）`);
        }
        if (!response.ok || result.error) throw new Error(result.error || `HTTP ${response.status}`);
        if (node._rhAppRequestId !== requestId) return;
        applySchema(node, result, true);
    } catch (error) {
        if (node._rhAppRequestId !== requestId) return;
        setStatus(node, `刷新失败：${error?.message || error}`, "error");
    } finally {
        if (node._rhAppRequestId === requestId && node._rhAppRefreshWidget) {
            node._rhAppRefreshWidget.disabled = false;
        }
    }
}

function markNeedsManualRefresh(node) {
    clearTimeout(node._rhAppRefreshTimer);
    clearInterval(node._rhAppSourceTimer);
    node._rhAppRefreshTimer = null;
    node._rhAppSourceTimer = null;
    node._rhAppRequestId = (node._rhAppRequestId || 0) + 1;
    setStatus(node, "输入已变更，请点击刷新应用参数", "idle");
}

function wrapRefreshCallback(node, widget) {
    if (!widget || widget._rhAppWrappedVersion === SETUP_VERSION) return;
    const original = widget._rhAppWrapped ? null : widget.callback;
    widget.callback = function (...args) {
        const result = original?.apply(this, args);
        markNeedsManualRefresh(node);
        return result;
    };
    widget._rhAppWrapped = true;
    widget._rhAppWrappedVersion = SETUP_VERSION;
}

function wrapConnectionCallback(node) {
    if (node._rhAppConnectionWrappedVersion === SETUP_VERSION) return;
    const original = node._rhAppConnectionWrapped ? null : node.onConnectionsChange;
    node.onConnectionsChange = function (...args) {
        const result = original?.apply(this, args);
        const slot = Number(args[1]);
        const inputName = this.inputs?.[slot]?.name;
        if ([CHANNEL_WIDGET, API_KEY_WIDGET, APP_ID_WIDGET].includes(inputName)) markNeedsManualRefresh(this);
        return result;
    };
    node._rhAppConnectionWrapped = true;
    node._rhAppConnectionWrappedVersion = SETUP_VERSION;
}

function setupNode(node, forceSchemaSync = false) {
    if (!isTargetNode(node) || !node?.widgets) return;
    const firstSetup = node._rhAppSetupVersion !== SETUP_VERSION;
    if (!firstSetup && !forceSchemaSync) return;
    clearTimeout(node._rhAppRefreshTimer);
    clearInterval(node._rhAppSourceTimer);
    node._rhAppRefreshTimer = null;
    node._rhAppSourceTimer = null;
    node._rhAppSetup = true;
    node._rhAppSetupVersion = SETUP_VERSION;

    if (firstSetup) {
        for (const name of [PARAMS_WIDGET, EXTRA_PARAMS_WIDGET]) {
            const widget = getWidget(node, name);
            if (!widget) continue;
            widget.type = "hidden";
            widget.hidden = true;
            if (widget.element) widget.element.style.display = "none";
        }

        node._rhAppStatusWidget = getWidget(node, "📡 应用状态")
            || node.addWidget("text", "📡 应用状态", "等待应用ID", () => {}, { multiline: false });
        node._rhAppStatusWidget.serialize = false;
        moveBefore(node, node._rhAppStatusWidget, INSTANCE_WIDGET);

        node._rhAppRefreshWidget = getWidget(node, "↻ 刷新应用参数")
            || node.addWidget("button", "↻ 刷新应用参数", null, () => refreshSchema(node, true));
        node._rhAppRefreshWidget.callback = () => refreshSchema(node, true);
        node._rhAppRefreshWidget.serialize = false;
        moveBefore(node, node._rhAppRefreshWidget, INSTANCE_WIDGET);

        wrapRefreshCallback(node, getWidget(node, CHANNEL_WIDGET), true);
        wrapRefreshCallback(node, getWidget(node, API_KEY_WIDGET), false);
        wrapRefreshCallback(node, getWidget(node, APP_ID_WIDGET), true);
        wrapConnectionCallback(node);
    }

    const saved = parseConfig(node);
    if (Array.isArray(saved.schema) && saved.schema.length) {
        applySchema(node, saved, true);
    } else {
        removeDynamicWidgets(node);
        setDynamicInputs(node, []);
        setStatus(node, "请点击刷新应用参数", "idle");
    }
    resizeNode(node);
}

app.registerExtension({
    name: "Dapao.RHApp.DynamicParameters.v10",
    setup() {
        setTimeout(() => {
            app.graph?._nodes?.forEach((node) => setupNode(node, true));
            app.canvas?.setDirty(true, true);
        }, 100);
    },
    nodeCreated(node) {
        setupNode(node);
    },
    loadedGraphNode(node) {
        setupNode(node, true);
    },
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== NODE_NAME) return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            setTimeout(() => setupNode(this), 20);
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            onConfigure?.apply(this, arguments);
            setTimeout(() => setupNode(this, true), 30);
        };

        const onRemoved = nodeType.prototype.onRemoved;
        nodeType.prototype.onRemoved = function () {
            clearTimeout(this._rhAppRefreshTimer);
            clearInterval(this._rhAppSourceTimer);
            this._rhAppRequestId = (this._rhAppRequestId || 0) + 1;
            onRemoved?.apply(this, arguments);
        };

        const onSerialize = nodeType.prototype.onSerialize;
        nodeType.prototype.onSerialize = function (data) {
            onSerialize?.call(this, data);
            data.widgets_values = PERSISTED_WIDGETS.map((name) => getWidget(this, name)?.value ?? null);
        };
    },
});
