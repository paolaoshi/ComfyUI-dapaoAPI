import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";

const NODE_TYPES = new Set([
    "DapaoLowPriceUniversalImageNode",
    "DapaoLowPriceUniversalVideoNode",
    "DapaoLowPriceLLMChatNode",
    "DapaoLowPriceSubtitleRemovalNode",
]);

const IMAGE_PRICES = {
    "gpt-image-2": 0.035,
    "ph-gpt-image-2": 0.09,
    "ph-gpt-image-2k": 0.15,
    "ph-gpt-image-4k": 0.15,
    "banana2-S": 0.12,
    "banana2-S_copy": 0.15,
    "gr-banana-2": 0.18,
    "gr-banana-pro": 0.23,
    "gemini-3.1-flash-image-preview": 0.1216,
};

const PH_IMAGE_ALL_RATIOS = ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9", "9:21", "1:2", "2:1", "1:3", "3:1"];
const PH_IMAGE_4K_RATIOS = PH_IMAGE_ALL_RATIOS.filter((ratio) => !["1:3", "3:1"].includes(ratio));
const GPT_IMAGE_2_RATIOS = ["1:1", "16:9", "9:16", "3:2", "2:3"];
const GR_IMAGE_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "3:2", "2:3", "5:4", "4:5", "21:9"];
const GEMINI_IMAGE_RATIOS = ["1:1", "16:9", "9:16", "3:2", "2:3"];
const IMAGE_QUALITIES = ["模型默认", "低画质", "标准画质", "高画质"];
const PH_IMAGE_RESOLUTIONS = ["1K", "2K", "4K"];
const PH_IMAGE_MODEL_BY_RESOLUTION = { "1K": "ph-gpt-image-2", "2K": "ph-gpt-image-2k", "4K": "ph-gpt-image-4k" };
const GR_IMAGE_RESOLUTIONS = ["模型默认", "1K", "2K", "4K"];

const IMAGE_OPTIONS = {
    "gpt-image-2": { modes: ["文生图", "图生图"], sizes: GPT_IMAGE_2_RATIOS, qualities: IMAGE_QUALITIES, resolutions: [], maxImages: 9, maxCount: 10 },
    "ph-gpt-image-2": { modes: ["文生图", "图生图"], sizes: PH_IMAGE_ALL_RATIOS, qualities: IMAGE_QUALITIES, resolutions: PH_IMAGE_RESOLUTIONS, modelResolution: "1K", maxImages: 9, maxCount: 10 },
    "ph-gpt-image-2k": { modes: ["文生图", "图生图"], sizes: PH_IMAGE_ALL_RATIOS, qualities: IMAGE_QUALITIES, resolutions: PH_IMAGE_RESOLUTIONS, modelResolution: "2K", maxImages: 9, maxCount: 10 },
    "ph-gpt-image-4k": { modes: ["文生图", "图生图"], sizes: PH_IMAGE_4K_RATIOS, qualities: IMAGE_QUALITIES, resolutions: PH_IMAGE_RESOLUTIONS, modelResolution: "4K", maxImages: 9, maxCount: 10 },
    "banana2-S": { modes: ["文生图", "图生图"], sizes: ["16:9", "9:16", "1:1", "4:3", "3:4"], qualities: [], resolutions: [], maxImages: 9, maxCount: 10 },
    "banana2-S_copy": { modes: ["文生图", "图生图"], sizes: ["16:9", "9:16", "1:1", "4:3", "3:4"], qualities: [], resolutions: [], maxImages: 9, maxCount: 10 },
    "gr-banana-2": { modes: ["图生图"], sizes: GR_IMAGE_RATIOS, qualities: [], resolutions: GR_IMAGE_RESOLUTIONS, maxImages: 9, maxCount: 10 },
    "gr-banana-pro": { modes: ["图生图"], sizes: GR_IMAGE_RATIOS, qualities: [], resolutions: GR_IMAGE_RESOLUTIONS, maxImages: 9, maxCount: 10 },
    "gemini-3.1-flash-image-preview": { modes: ["文生图", "图生图"], sizes: GEMINI_IMAGE_RATIOS, qualities: [], resolutions: [], maxImages: 9, maxCount: 4, gemini: true },
};

const VIDEO_PRICES = {
    "bh2.0-fast-480p": [0.38, "second"], "bh2.0-fast-720p": [0.42, "second"],
    "bh2.0-480p": [0.48, "second"], "bh2.0-720p": [0.58, "second"], "bh2.0-1080p": [0.79, "second"],
    "bh2.0-mini-480p": [0.25, "second"], "bh2.0-mini-720p": [0.35, "second"],
    "SD2.0-480P": [0.40, "second"], "SD2.0-720P-fast": [0.39, "second"], "SD2.0-720P": [0.50, "second"], "SD2.0-1080P": [1.15, "second"],
    "sdvip4k": [2.20, "second"], "sdvip720p": [0.33, "second"], "sdvip1080p": [0.60, "second"],
    "gz-sd480p": [0.19, "second"], "gz-sd720p": [0.35, "second"], "gz-sd1080p": [0.70, "second"], "gz-sd4k": [1.60, "second"],
    "sdquan-2-miao": [0.275, "second"], "wanneng1.1": [0.18, "second"], "doubaofast": [0.258, "second"],
    "sd2-fast福利": [2.36, "request"], "sd2-福利": [2.98, "request"], "B-quannengship2.0": [3.45, "request"],
    "quanneng2.0": [5.25, "request"], "quanneng2.0-9tu": [1.58, "request"], "video2.0": [4.85, "request"],
    "sd2-vip720p": [3.55, "request"], "sd2-vip720p-fast": [3.75, "request"], "keling-3": [0.90, "request"],
    "xb-sora2": [0.78, "request"], "me-kuaile1.0": [1.85, "request"], "sora-2-z": [0.88, "request"], "veo-omni-flash": [0.88, "request"],
    "grok-video-3-pro": [0.65, "request"], "grok-video-3-max": [0.65, "request"],
    "grok-video-1.5-pro": [0.65, "request"], "grok-video-1.5-max": [0.65, "request"],
};

const ALL_VIDEO_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "2:3", "3:2", "21:9"];
const BH_VIDEO_RATIOS = ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9"];

function videoOptions(resolutions, durations, { images = 9, videos = 0, audios = 0, imageRequired = false, frames = true, ratios = ALL_VIDEO_RATIOS } = {}) {
    const modes = imageRequired ? ["图生视频"] : ["文生视频", "图生视频"];
    if (!imageRequired && frames) modes.push("首尾帧生视频");
    if (videos || audios) modes.push("多模态参考");
    return { resolutions, durations: durations.map(String), images, videos, audios, imageRequired, modes, ratios };
}

const VIDEO_OPTIONS = {
    "bh2.0-fast-480p": videoOptions(["480P"], range(4, 15), { videos: 3, audios: 3, ratios: BH_VIDEO_RATIOS }),
    "bh2.0-fast-720p": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, ratios: BH_VIDEO_RATIOS }),
    "bh2.0-480p": videoOptions(["480P"], range(4, 15), { videos: 3, audios: 3, ratios: BH_VIDEO_RATIOS }),
    "bh2.0-720p": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, ratios: BH_VIDEO_RATIOS }),
    "bh2.0-1080p": videoOptions(["1080P"], range(4, 15), { videos: 3, audios: 3, ratios: BH_VIDEO_RATIOS }),
    "bh2.0-mini-480p": videoOptions(["480P"], range(4, 15), { videos: 3, audios: 3, ratios: BH_VIDEO_RATIOS }),
    "bh2.0-mini-720p": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, ratios: BH_VIDEO_RATIOS }),
    "SD2.0-480P": videoOptions(["480P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "SD2.0-720P-fast": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "SD2.0-720P": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "SD2.0-1080P": videoOptions(["1080P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "sdvip4k": videoOptions(["4K"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "sdvip720p": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "sdvip1080p": videoOptions(["1080P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "gz-sd480p": videoOptions(["480P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "gz-sd720p": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "gz-sd1080p": videoOptions(["1080P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "gz-sd4k": videoOptions(["4K"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "sdquan-2-miao": videoOptions(["720P"], [5, 10, 15], { frames: false }),
    "wanneng1.1": videoOptions(["720P"], range(4, 15), { frames: false }),
    "doubaofast": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "sd2-fast福利": videoOptions(["720P"], range(4, 15), { images: 4, videos: 3, audios: 3, frames: false }),
    "sd2-福利": videoOptions(["720P"], range(4, 15), { images: 4, videos: 3, audios: 3, frames: false }),
    "B-quannengship2.0": videoOptions(["720P"], [5, 10, 15], { frames: false }),
    "quanneng2.0": videoOptions(["720P"], [15], { audios: 3, frames: false }),
    "quanneng2.0-9tu": videoOptions(["720P"], [15], { frames: false }),
    "video2.0": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3, frames: false }),
    "sd2-vip720p": videoOptions(["720P"], [15], { frames: true }),
    "sd2-vip720p-fast": videoOptions(["720P"], range(4, 15), { videos: 3, audios: 3 }),
    "keling-3": videoOptions(["720P"], [15], { images: 2, audios: 3, frames: false }),
    "xb-sora2": videoOptions(["720P"], [8, 12], { images: 1, audios: 3, imageRequired: true, frames: false }),
    "me-kuaile1.0": videoOptions(["720P", "1080P"], [5, 10, 15], { images: 5, audios: 3, frames: false }),
    "sora-2-z": videoOptions(["720P"], [12], { images: 1, audios: 3, frames: false }),
    "veo-omni-flash": videoOptions(["720P"], [10], { images: 5, audios: 3, imageRequired: true, frames: false }),
    "grok-video-3-pro": videoOptions(["480P", "540P", "720P", "1080P"], [10], { frames: false }),
    "grok-video-3-max": videoOptions(["480P", "540P", "720P", "1080P"], [15], { frames: false }),
    "grok-video-1.5-pro": videoOptions(["480P", "720P"], [10], { images: 1, imageRequired: true, frames: false }),
    "grok-video-1.5-max": videoOptions(["480P", "720P"], [15], { images: 1, imageRequired: true, frames: false }),
};

const LLM_PRICES = {
    "gpt-4o": [1.75, 7], "gpt-4o-mini": [0.105, 0.42], "gpt-5-chat-latest": [0.875, 7], "gpt-5-mini": [0.175, 1.4],
    "o3": [1.4, 5.6], "o4-mini": [0.77, 3.08], "claude-opus-4-8": [10.5, 52.5], "claude-sonnet-4-5": [2.1, 10.5],
    "claude-haiku-4-5": [0.7, 3.5], "gemini-2.5-pro": [0.875, 7], "gemini-2.5-flash": [0.21, 1.75],
    "deepseek-chat": [0.196, 0.294], "deepseek-reasoner": [0.385, 1.54], "minimax-m2": [0.21, 0.84],
};

const VISION_MODELS = new Set(["gpt-4o", "gpt-4o-mini", "gemini-2.5-pro"]);
const OPENAI_REASONING_MODELS = new Set(["o3", "o4-mini"]);
const IMAGE_QUALITY_VALUES = new Set(["模型默认", "低画质", "标准画质", "高画质"]);
const IMAGE_RESOLUTION_VALUES = new Set(["模型默认", "1K", "2K", "4K"]);

function range(start, end) {
    return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

function nodeType(node) {
    return node?.comfyClass || node?.type || "";
}

function widget(node, name) {
    return node?.widgets?.find((item) => item.name === name) || null;
}

function value(node, name, fallback = "") {
    return widget(node, name)?.value ?? fallback;
}

function modelId(node) {
    const label = String(value(node, "🤖 模型", ""));
    return label.includes("｜") ? label.split("｜").pop().trim() : label.trim();
}

function modelLabelById(node, id) {
    const modelWidget = widget(node, "🤖 模型");
    const values = modelWidget?.options?.values || [];
    return values.find((label) => String(label).split("｜").pop().trim() === id) || null;
}

function inputLinked(node, name) {
    return node?.inputs?.some((input) => input.name === name && input.link != null) || false;
}

function setComboValues(target, values, fallback = values[0]) {
    if (!target || !values?.length) return;
    const normalized = values.map(String);
    target.options ??= {};
    target.options.values = normalized;
    if (!normalized.includes(String(target.value))) target.value = String(fallback);
}

function setWidgetHidden(node, name, hidden) {
    const target = widget(node, name);
    if (target) target.hidden = Boolean(hidden);
}

function setInputHidden(node, name, hidden) {
    const target = node?.inputs?.find((item) => item.name === name);
    if (target) target.hidden = Boolean(hidden);
}

function refreshImageNode(node) {
    let id = modelId(node);
    let config = IMAGE_OPTIONS[id];
    if (!config) return;
    const modelWidget = widget(node, "🤖 模型");
    const resolutionWidget = widget(node, "🧩 清晰度");
    const modelChanged = node.__dapaoLastImageModelId !== id;
    if (config.modelResolution && modelChanged && resolutionWidget) {
        resolutionWidget.value = config.modelResolution;
    }
    if (config.resolutions.length) {
        setComboValues(resolutionWidget, config.resolutions, config.modelResolution || config.resolutions[0]);
    }
    const resolutionModelId = PH_IMAGE_MODEL_BY_RESOLUTION[String(resolutionWidget?.value)];
    if (config.modelResolution && resolutionModelId && resolutionModelId !== id) {
        const targetLabel = modelLabelById(node, resolutionModelId);
        if (targetLabel && modelWidget) {
            modelWidget.value = targetLabel;
            id = resolutionModelId;
            config = IMAGE_OPTIONS[id];
        }
    }
    node.__dapaoLastImageModelId = id;
    setComboValues(widget(node, "🔀 模式"), config.modes);
    setComboValues(widget(node, "📐 图片尺寸/比例"), ["模型默认", ...config.sizes], "模型默认");
    const qualityWidget = widget(node, "🎨 画质");
    if (qualityWidget && resolutionWidget && resolutionWidget.value === "模型默认" && config.resolutions.includes(String(qualityWidget.value))) {
        resolutionWidget.value = qualityWidget.value;
    }
    if (config.qualities.length) setComboValues(qualityWidget, config.qualities);
    if (config.resolutions.length) setComboValues(resolutionWidget, config.resolutions, config.modelResolution || config.resolutions[0]);
    setWidgetHidden(node, "🎨 画质", !config.qualities.length);
    setWidgetHidden(node, "🧩 清晰度", !config.resolutions.length);

    const mode = String(value(node, "🔀 模式", config.modes[0]));
    const geminiEdit = Boolean(config.gemini && mode === "图生图");
    const countWidget = widget(node, "🖼️ 出图数量");
    if (countWidget) {
        countWidget.options ??= {};
        countWidget.options.min = 1;
        countWidget.options.max = geminiEdit ? 1 : config.maxCount;
        const current = Number(countWidget.value) || 1;
        countWidget.value = geminiEdit ? 1 : Math.min(Math.max(current, 1), config.maxCount);
    }
    setWidgetHidden(node, "🖼️ 出图数量", geminiEdit);

    const asyncWidget = widget(node, "⚡ 异步模式");
    if (geminiEdit && asyncWidget) asyncWidget.value = false;
    setWidgetHidden(node, "⚡ 异步模式", geminiEdit);
    const asyncEnabled = !geminiEdit && Boolean(value(node, "⚡ 异步模式", false));
    setWidgetHidden(node, "🔁 最大轮询秒数", !asyncEnabled);
    setWidgetHidden(node, "⏱️ 轮询间隔", !asyncEnabled);

    const showImages = mode === "图生图";
    for (let index = 1; index <= 9; index++) {
        setInputHidden(node, `🖼️ 图像${index}`, !showImages || index > config.maxImages);
    }
}

function refreshVideoNode(node) {
    const config = VIDEO_OPTIONS[modelId(node)];
    if (!config) return;
    setComboValues(widget(node, "🎛️ 生成模式"), config.modes);
    setComboValues(widget(node, "🧩 分辨率"), config.resolutions);
    setComboValues(widget(node, "⏱️ 时长(秒)"), config.durations);
    setComboValues(widget(node, "📐 视频比例"), config.ratios);
    setWidgetHidden(node, "🧩 分辨率", config.resolutions.length === 1);
    setWidgetHidden(node, "⏱️ 时长(秒)", config.durations.length === 1);

    const mode = String(value(node, "🎛️ 生成模式", config.modes[0]));
    const imageMode = mode === "图生视频" || mode === "多模态参考";
    const frameMode = mode === "首尾帧生视频";
    const multimodalMode = mode === "多模态参考";

    setWidgetHidden(node, "🌐 首帧公网URL", !frameMode);
    setWidgetHidden(node, "🌐 尾帧公网URL", !frameMode);
    setInputHidden(node, "🎬 首帧图", !frameMode);
    setInputHidden(node, "🏁 尾帧图", !frameMode);

    for (let index = 1; index <= 9; index++) {
        setInputHidden(node, `🖼️ 参考图${index}`, !imageMode || index > config.images);
    }
    setWidgetHidden(node, "🎞️ 参考视频URL列表", !multimodalMode || !config.videos);
    setWidgetHidden(node, "🎵 参考音频URL列表", !multimodalMode || !config.audios);
    for (let index = 1; index <= 3; index++) {
        setInputHidden(node, `🎞️ 参考视频${index}`, !multimodalMode || index > config.videos);
        setInputHidden(node, `🎵 参考音频${index}`, !multimodalMode || index > config.audios);
    }
}

function refreshLlmNode(node) {
    const id = modelId(node);
    const vision = VISION_MODELS.has(id);
    const reasoning = OPENAI_REASONING_MODELS.has(id);
    for (let index = 1; index <= 8; index++) {
        setInputHidden(node, `🖼️ 图像${index}`, !vision);
    }
    setWidgetHidden(node, "🌡️ 温度", reasoning);
    setWidgetHidden(node, "🎲 Top_P", reasoning);
}

function refreshSubtitleNode(node) {
    setWidgetHidden(node, "✏️ 自定义分辨率", value(node, "📐 视频分辨率", "720x1280") !== "自定义");
}

function refreshNode(node) {
    if (!NODE_TYPES.has(nodeType(node))) return;
    const type = nodeType(node);
    if (type === "DapaoLowPriceUniversalImageNode") refreshImageNode(node);
    else if (type === "DapaoLowPriceUniversalVideoNode") refreshVideoNode(node);
    else if (type === "DapaoLowPriceLLMChatNode") refreshLlmNode(node);
    else if (type === "DapaoLowPriceSubtitleRemovalNode") refreshSubtitleNode(node);
    if (node.computeSize) {
        const computed = node.computeSize();
        const currentWidth = Number(node.size?.[0]) || computed[0];
        node.setSize([Math.max(currentWidth, computed[0]), computed[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

function wrapCallback(node, target) {
    if (!target || target.__dapaoLowPriceWrapped) return;
    const original = target.callback;
    target.callback = function () {
        const result = original?.apply(this, arguments);
        refreshNode(node);
        return result;
    };
    target.__dapaoLowPriceWrapped = true;
}

function setup(node) {
    if (!node?.widgets || !NODE_TYPES.has(nodeType(node))) return;
    node.widgets.forEach((target) => wrapCallback(node, target));
    refreshNode(node);
}

function migrateImageWidgetOrder(node, serializedValues) {
    if (nodeType(node) !== "DapaoLowPriceUniversalImageNode" || !Array.isArray(serializedValues)) return;
    if (typeof serializedValues[6] !== "number" || typeof serializedValues[7] !== "boolean") return;

    const oldCombined = String(serializedValues[5] ?? "模型默认");
    const savedQuality = [serializedValues[13], oldCombined].map(String).find((item) => IMAGE_QUALITY_VALUES.has(item)) || "模型默认";
    const savedResolution = [serializedValues[14], serializedValues[13], oldCombined].map(String).find((item) => IMAGE_RESOLUTION_VALUES.has(item) && item !== "模型默认") || "模型默认";
    const restored = {
        "🧩 清晰度": savedResolution,
        "🎨 画质": savedQuality,
        "🖼️ 出图数量": serializedValues[6],
        "⚡ 异步模式": serializedValues[7],
        "🎲 随机种": serializedValues[8],
        "📋 额外参数JSON": serializedValues[9],
        "🔁 最大轮询秒数": serializedValues[10],
        "⏱️ 轮询间隔": serializedValues[11],
        "⌛ 请求超时": serializedValues[12],
    };
    for (const [name, savedValue] of Object.entries(restored)) {
        const target = widget(node, name);
        if (target && savedValue !== undefined) target.value = savedValue;
    }
}

function hasReferenceVideo(node) {
    if (value(node, "🎛️ 生成模式", "文生视频") !== "多模态参考") return false;
    if (String(value(node, "🎞️ 参考视频URL列表", "")).trim()) return true;
    return [1, 2, 3].some((index) => inputLinked(node, `🎞️ 参考视频${index}`));
}

function priceText(node) {
    const id = modelId(node);
    const type = nodeType(node);
    if (type === "DapaoLowPriceUniversalImageNode") {
        const price = IMAGE_PRICES[id];
        const count = Number(value(node, "🖼️ 出图数量", 1)) || 1;
        if (!price) return "价格待补";
        const total = (price * count).toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
        return count === 1 ? `¥${total}/张` : `¥${total}/${count}张`;
    }
    if (type === "DapaoLowPriceUniversalVideoNode") {
        const config = VIDEO_PRICES[id];
        if (!config) return "价格待补";
        const duration = Number(value(node, "⏱️ 时长(秒)", 5)) || 5;
        let price = config[1] === "second" ? config[0] * duration : config[0];
        if (hasReferenceVideo(node)) {
            if (id.startsWith("bh2.0-")) price *= 1.8;
            else if (["SD2.0-720P-fast", "SD2.0-720P", "SD2.0-1080P", "sdvip4k", "gz-sd480p", "gz-sd720p", "gz-sd1080p", "gz-sd4k"].includes(id)) price *= 2;
        }
        const amount = price.toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
        return config[1] === "request" ? `¥${amount}/次` : `¥${amount}/${duration}秒`;
    }
    if (type === "DapaoLowPriceLLMChatNode") {
        const price = LLM_PRICES[id];
        return price ? `入${price[0]}/出${price[1]}` : "价格待补";
    }
    if (type === "DapaoLowPriceSubtitleRemovalNode") {
        const duration = Number(value(node, "⏱️ 视频时长(秒)", 10)) || 10;
        const amount = (duration * 0.009).toFixed(3).replace(/0+$/, "").replace(/\.$/, "");
        return `¥${amount}/${duration}秒`;
    }
    return "价格待补";
}

function roundRect(ctx, x, y, width, height, radius) {
    const r = Math.min(radius, width / 2, height / 2);
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + width - r, y);
    ctx.quadraticCurveTo(x + width, y, x + width, y + r);
    ctx.lineTo(x + width, y + height - r);
    ctx.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
    ctx.lineTo(x + r, y + height);
    ctx.quadraticCurveTo(x, y + height, x, y + height - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
    ctx.closePath();
}

function drawBadge(node, ctx) {
    const text = priceText(node);
    ctx.save();
    ctx.font = "bold 14px Arial, sans-serif";
    const width = Math.max(82, ctx.measureText(text).width + 36);
    const height = 24;
    const x = Math.max(12, node.size[0] - width - 10);
    const y = -height + 4;
    ctx.fillStyle = text === "价格待补" ? "#5f5f66" : "#9c6a28";
    roundRect(ctx, x, y, width, height, 8);
    ctx.fill();
    ctx.fillStyle = text === "价格待补" ? "#d8d8dc" : "#ffbf35";
    ctx.beginPath();
    ctx.arc(x + 13, y + height / 2, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = text === "价格待补" ? "#5f5f66" : "#7b4616";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.font = "bold 14px Arial, sans-serif";
    ctx.fillText(text === "价格待补" ? "?" : "¥", x + 13, y + height / 2 + 0.5);
    ctx.fillStyle = "#fff";
    ctx.textAlign = "left";
    ctx.font = "bold 14px Arial, sans-serif";
    ctx.fillText(text, x + 26, y + height / 2 + 0.5);
    ctx.restore();
}

function refreshAllNodes() {
    for (const type of NODE_TYPES) {
        app.graph?.findNodesByType(type)?.forEach((node) => setup(node));
    }
}

app.registerExtension({
    name: "Dapao.LowPriceUniversalAPI.UI",
    async setup() {
        api.addEventListener("hot_reload_update", () => {
            [50, 250, 1000, 3000].forEach((delay) => setTimeout(refreshAllNodes, delay));
        });
    },
    nodeCreated(node) {
        if (NODE_TYPES.has(nodeType(node))) setTimeout(() => setup(node), 20);
    },
    loadedGraphNode(node) {
        if (NODE_TYPES.has(nodeType(node))) setTimeout(() => setup(node), 50);
    },
    async beforeRegisterNodeDef(nodeTypeClass, nodeData) {
        if (!NODE_TYPES.has(nodeData.name)) return;

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
            migrateImageWidgetOrder(this, arguments[0]?.widgets_values);
            setTimeout(() => setup(this), 50);
        };

        const onWidgetChanged = nodeTypeClass.prototype.onWidgetChanged;
        nodeTypeClass.prototype.onWidgetChanged = function () {
            const result = onWidgetChanged?.apply(this, arguments);
            refreshNode(this);
            return result;
        };

        const onDrawForeground = nodeTypeClass.prototype.onDrawForeground;
        nodeTypeClass.prototype.onDrawForeground = function (ctx) {
            onDrawForeground?.apply(this, arguments);
            drawBadge(this, ctx);
        };
    },
});

console.log("[Dapao Low Price Universal API UI] loaded with adaptive model capabilities");
