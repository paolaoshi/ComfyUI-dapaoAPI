import { app } from "../../../scripts/app.js";
import { api } from "../../../scripts/api.js";
import { ComfyWidgets } from "../../../scripts/widgets.js";

const REGISTER = "👉点此注册API密钥👈";
const URL = "https://api.dapaoai.com/sign-up?aff=vcOZ";
const TYPES = new Set(["Prepare", "Visual", "Finish", "Project", "Novel", "Develop", "Write", "Assets", "Image", "Storyboard", "Video", "Review", "Deliver", "Merge"].map(x => `DapaoDrama${x}`));
const PREVIEW_TYPES = new Set(["DapaoDramaPrepare", "DapaoDramaVisual", "DapaoDramaFinish", "DapaoDramaDeliver"]);
const LOCAL = new Set(["DapaoDramaProject", "DapaoDramaDeliver", "DapaoDramaMerge"]);
const typeOf = node => node?.comfyClass || node?.type;

function fromDrama(node) {
    let link = node.inputs?.find(input => input.name === "anything")?.link;
    for (let depth = 0; link != null && depth < 10; depth++) {
        const edge = app.graph?.links?.[link];
        const source = app.graph?.getNodeById?.(edge?.origin_id);
        if (!source) return false;
        if (TYPES.has(typeOf(source))) return true;
        if (typeOf(source) !== "Reroute") return false;
        link = source.inputs?.[0]?.link;
    }
    return false;
}

function installListPreview(node) {
    if (typeOf(node) !== "easy showAnything" || node.__dramaListPreview) return;
    node.__dramaListPreview = true;
    const render = (values, resize = true) => {
        const old = node.widgets?.filter(w => w.__dramaPreviewItem || w.name === "text") || [];
        for (const widget of old) {
            widget.onRemove?.();
            node.widgets.splice(node.widgets.indexOf(widget), 1);
        }
        values.forEach((value, i) => {
            const widget = ComfyWidgets.STRING(node, `dapao_prompt_${i}`, ["STRING", { multiline: true }], app).widget;
            widget.__dramaPreviewItem = true;
            // Store one canonical copy below; native widgets_values is restored
            // by EasyUse before our hook, so it must not contain duplicate items.
            widget.serialize = false;
            widget.value = value;
            const element = widget.inputEl || widget.element;
            if (element) element.readOnly = true;
        });
        if (resize && node.computeSize && node.setSize) {
            const size = node.computeSize();
            node.setSize([Math.max(node.size?.[0] || 0, size[0]), size[1]]);
        }
        node.setDirtyCanvas?.(true, true);
    };
    const previous = node.onExecuted;
    node.onExecuted = function (message, ...args) {
        if (!fromDrama(this)) {
            if (this.properties) delete this.properties.dapaoDramaPreviewText;
            return previous?.call(this, message, ...args);
        }
        // A cache/status callback without text is not an empty result.
        if (!Array.isArray(message?.text)) return;
        this.properties ||= {};
        this.properties.dapaoDramaPreviewText = [...message.text];
        render(message.text);
    };
    const configured = node.onConfigure;
    node.onConfigure = function (...args) {
        const result = configured?.apply(this, args);
        const saved = this.properties?.dapaoDramaPreviewText;
        if (Array.isArray(saved)) render(saved, false);
        return result;
    };
    // Installation may occur after onConfigure, or after cached output replay.
    const saved = node.properties?.dapaoDramaPreviewText;
    if (Array.isArray(saved) && fromDrama(node)) render(saved, false);
}

function installMenuOrder() {
    const graph = globalThis.LiteGraph;
    if (!graph?.ContextMenu || graph.ContextMenu.__dapaoDramaOrder) return;
    const ranks = new Map([...TYPES].map((type, index) => [type, index]));
    // LiteGraph sorts titles (including emoji) before constructing each submenu.
    // Reorder only our entries at that final boundary; preserve all other menus.
    graph.ContextMenu = new Proxy(graph.ContextMenu, {
        construct(target, args, newTarget) {
            if (Array.isArray(args[0])) {
                const items = [...args[0]];
                const ordered = items.filter(item => ranks.has(item?.value))
                    .sort((a, b) => ranks.get(a.value) - ranks.get(b.value));
                let next = 0;
                for (let i = 0; i < items.length; i++) {
                    if (ranks.has(items[i]?.value)) items[i] = ordered[next++];
                }
                const drama = items.findIndex(item => item?.value === "🤖dapaoAPI/🐠漫剧一站式专用🐠/");
                const common = items.findIndex(item => item?.value === "🤖dapaoAPI/🍬大炮API常用工具🍬/");
                if (drama >= 0 && common >= 0) {
                    const [entry] = items.splice(drama, 1);
                    const after = items.findIndex(item => item?.value === "🤖dapaoAPI/🍬大炮API常用工具🍬/");
                    items.splice(after + 1, 0, entry);
                }
                args = [items, ...args.slice(1)];
            }
            return Reflect.construct(target, args, newTarget);
        },
    });
    graph.ContextMenu.__dapaoDramaOrder = true;
}

function resizeControls(node) {
    if (!node.computeSize || !node.setSize) return;
    const width = node.size?.[0] || 440;
    const size = node.computeSize();
    node.setSize([Math.max(440, width, size[0]), size[1]]);
    node.setDirtyCanvas?.(true, true);
}

function timingControls(node) {
    if (typeOf(node) !== "DapaoDramaFinish") return;
    const get = name => node.widgets?.find(w => w.name === name);
    const planning = get("⏱️ 时长规划");
    if (!planning) return;
    const manual = planning.value === "按段数逐段设置";
    const count = Math.max(1, Math.min(32, Number(get("🔢 分段数量")?.value) || 6));
    let total = 0;
    for (const widget of node.widgets) {
        const match = /^⏱️ 第(\d+)段（秒）$/.exec(widget.name);
        let visible;
        if (match) {
            visible = manual && Number(match[1]) <= count;
            if (visible) total += Number(widget.value) || 0;
        } else if (["🔢 分段数量", "⏳ 总时长规则"].includes(widget.name)) visible = manual;
        else if (widget.name === "📝 逐段时长（秒）") visible = planning.value === "手动逐段时长";
        if (visible !== undefined) {
            if (!("__dramaTimingSize" in widget)) widget.__dramaTimingSize = widget.computeSize;
            widget.hidden = !visible;
            widget.computeSize = visible ? widget.__dramaTimingSize : (() => [0, -4]);
            const el = widget.inputEl || widget.element;
            if (el?.style) el.style.display = visible ? "" : "none";
        }
        if ((visible !== undefined || widget === planning) && !widget.__dramaTimingCallback) {
            const previous = widget.callback;
            widget.callback = function (...args) {
                const result = previous?.apply(this, args);
                timingControls(node);
                resizeControls(node);
                return result;
            };
            widget.__dramaTimingCallback = true;
        }
    }
    if (!node.__dramaTimingSummary) {
        node.__dramaTimingSummary = node.addWidget("button", "", null, () => {});
        node.__dramaTimingSummary.serialize = false;
    }
    node.__dramaTimingSummary.name = manual
        ? `⏱️ 计划：${count}段，共${Number(total.toFixed(2))}秒 · ${get("⏳ 总时长规则")?.value || "必须与01目标一致"}`
        : "⏱️ 自动沿用项目目标；手动模式可控制分段预算";
}

function setup(node) {
    if (!TYPES.has(typeOf(node)) || !node.addCustomWidget) return;
    if (["DapaoDramaPrepare", "DapaoDramaVisual", "DapaoDramaFinish"].includes(typeOf(node))) {
        const name = "💾 完整资料包JSON（续集用）";
        // Existing workflows restore their old output array during configure.
        // Append only; all pre-existing slot indices and links stay intact.
        if (node.addOutput && !node.outputs?.some(output => output.name === name))
            node.addOutput(name, "STRING");
    }
    // New ComfyUI DOM widgets use computeLayoutSize, not only computeSize.
    // Never let a textarea's percentage/CSS height become a minimum derived
    // from the node's saved height: arrange() would grow the node recursively.
    for (const widget of node.widgets || []) {
        const element = widget.inputEl || widget.element;
        const multiline = element?.tagName === "TEXTAREA" || widget.type === "customtext"
            || widget.options?.multiline || widget.name === "📚 文档预览";
        if (!multiline || widget.type?.startsWith("converted-widget")) continue;
        widget.__dramaStableTextLayout = true;
        widget.options ||= {};
        widget.options.getMinHeight = () => widget.hidden ? 0 : 64;
        widget.options.getMaxHeight = () => widget.hidden ? 0 : 64;
        // LiteGraph gives the legacy method precedence over computeLayoutSize.
        // Never use an allocated textarea height as the next layout minimum.
        const textSize = () => widget.hidden ? [0, -4] : [0, 64];
        widget.computeSize = textSize;
        if ("__dramaComputeSize" in widget) widget.__dramaComputeSize = textSize;
        if ("__dramaTimingSize" in widget) widget.__dramaTimingSize = textSize;
        widget.computeLayoutSize = () => widget.hidden
            ? { minHeight: 0, maxHeight: 0, minWidth: 0 }
            : { minHeight: 64, maxHeight: 64, minWidth: 0 };
    }
    if (["DapaoDramaPrepare", "DapaoDramaVisual", "DapaoDramaFinish"].includes(typeOf(node))) {
        const advanced = node.widgets?.filter(w => /专项参考$|修订稿$|导入文档|分析方式|分段依据|每段字符数|最大分析段数|审查范围|时间线音乐要求/.test(w.name)) || [];
        if (advanced.length && node.addWidget && !node.__dramaAdvanced) {
            const toggle = node.addWidget("button", "⚙️ 展开高级功能", null, () => {
                node.__dramaAdvancedOpen = !node.__dramaAdvancedOpen;
                toggle.name = node.__dramaAdvancedOpen ? "⚙️ 收起高级功能" : "⚙️ 展开高级功能";
                setup(node);
                resizeControls(node);
            });
            toggle.serialize = false;
            node.__dramaAdvanced = toggle;
        }
        for (const widget of advanced) {
            if (!("__dramaComputeSize" in widget)) widget.__dramaComputeSize = widget.computeSize;
            widget.hidden = !node.__dramaAdvancedOpen;
            widget.computeSize = widget.hidden ? (() => [0, -4]) : widget.__dramaComputeSize;
            const element = widget.inputEl || widget.element;
            if (element?.style) element.style.display = widget.hidden ? "none" : "";
        }
    }
    timingControls(node);
    node.color = "#14313a";
    node.bgcolor = "#191f24";
    if (!node.__dramaRegister) {
        const button = {
            name: REGISTER, type: "DAPAO_DRAMA_REGISTER", serialize: false,
            computeSize() { return [220, 40]; },
            draw(ctx, current, width, y, height) {
                const liveWidth = Number(current.size?.[0]) || width;
                this.area = { x: 8, y: y + 3, w: liveWidth - 16, h: Math.max(32, height - 6) };
                const a = this.area;
                ctx.save(); ctx.fillStyle = "#a96b1b"; ctx.strokeStyle = "#d49a42";
                ctx.beginPath(); ctx.roundRect(a.x, a.y, a.w, a.h, 7); ctx.fill(); ctx.stroke();
                ctx.fillStyle = "#fff7df"; ctx.font = "bold 13px sans-serif";
                ctx.textAlign = "center"; ctx.textBaseline = "middle";
                ctx.fillText(REGISTER, liveWidth / 2, a.y + a.h / 2); ctx.restore();
            },
            mouse(event, pos) {
                const a = this.area;
                if (!a || !["pointerdown", "mousedown", "click"].includes(event?.type)) return false;
                if (pos[0] < a.x || pos[0] > a.x + a.w || pos[1] < a.y || pos[1] > a.y + a.h) return false;
                // Some LiteGraph versions dispatch all three events for one press.
                const now = Date.now();
                if (!this.lastPress || now - this.lastPress > 400) {
                    window.open(URL, "_blank", "noopener,noreferrer"); this.lastPress = now;
                }
                return true;
            },
        };
        node.addCustomWidget(button); node.__dramaRegister = button;
        node.addCustomWidget({
            name: LOCAL.has(typeOf(node)) ? "🧩 本地整理 · 不调用API" : "💰 按阶段调用LLM计费 · 固定种可恢复请求",
            type: "DAPAO_DRAMA_PRICE", serialize: false,
            computeSize() { return [220, 24]; },
            draw(ctx, current, width, y) {
                ctx.save(); ctx.fillStyle = "#d8bd89"; ctx.font = "12px sans-serif"; ctx.textAlign = "center";
                ctx.fillText(this.name, (Number(current.size?.[0]) || width) / 2, y + 16); ctx.restore();
            },
        });
    }
    const key = node.widgets?.find(w => w.name === "🔑 API密钥");
    const input = key?.inputEl || key?.element;
    if (input?.tagName === "INPUT") input.type = "password";
    // DOM text widgets may derive computeSize from their current allocated
    // height. Recomputing on every configure/hot reload feeds that height back
    // into the layout and grows the node on each browser refresh.
    if (!node.__dramaLayoutInitialized && node.computeSize && node.setSize) {
        node.__dramaLayoutInitialized = true;
        const size = node.computeSize();
        node.setSize([Math.max(440, node.size?.[0] || 0, size[0]), size[1]]);
    }
    node.setDirtyCanvas?.(true, true);
}

const refreshAll = () => app.graph?._nodes?.filter(n => TYPES.has(typeOf(n))).forEach(setup);
app.registerExtension({
    name: "Dapao.ShortDrama.UI",
    setup() {
        installMenuOrder();
        api.addEventListener("hot_reload_update", () => [100, 500, 1200].forEach(ms => setTimeout(refreshAll, ms)));
    },
    nodeCreated(node) { setTimeout(() => installListPreview(node), 30); if (TYPES.has(typeOf(node))) setTimeout(() => setup(node), 20); },
    loadedGraphNode(node) {
        setTimeout(() => installListPreview(node), 50);
        if (TYPES.has(typeOf(node))) {
            node.__dramaLayoutInitialized = true;
            setTimeout(() => setup(node), 50);
        }
    },
    beforeRegisterNodeDef(cls, data) {
        if (!TYPES.has(data.name)) return;
        const configure = cls.prototype.configure;
        if (configure) cls.prototype.configure = function (config, ...args) {
            const savedSize = config?.size?.length === 2 ? Array.from(config.size) : null;
            this.__dramaLayoutInitialized = true;
            setup(this);
            const result = configure.call(this, config, ...args);
            setup(this);
            // Slot restoration and other extensions can resize before onConfigure.
            // The saved dimensions must win after that entire synchronous phase.
            if (savedSize?.every(v => Number.isFinite(v) && v > 0)) {
                const minimum = this.computeSize()[1];
                // One-time repair for workflows saved with the old all-controls
                // height. Subsequent loads keep the user's chosen dimensions.
                if (!config.properties?.dapaoDramaStableLayout && savedSize[1] > minimum + 600)
                    savedSize[1] = minimum + 100;
                this.setSize(savedSize);
            }
            this.properties ||= {};
            this.properties.dapaoDramaStableLayout = true;
            return result;
        };
        for (const event of ["onNodeCreated", "onConfigure", "onAdded"]) {
            const previous = cls.prototype[event];
            cls.prototype[event] = function (...args) {
                // Saved workflow dimensions belong to the user. Configure runs
                // before our deferred setup callbacks, including on initial load.
                if (event === "onConfigure") this.__dramaLayoutInitialized = true;
                const result = previous?.apply(this, args);
                // Configure must hide optional widgets before the first arrange,
                // rather than letting all 32 segment controls inflate saved size.
                if (event === "onConfigure" || event === "onNodeCreated") setup(this);
                setTimeout(() => setup(this), 30);
                return result;
            };
        }
        if (PREVIEW_TYPES.has(data.name)) {
            const executed = cls.prototype.onExecuted;
            cls.prototype.onExecuted = function (message) {
                const result = executed?.apply(this, arguments);
                const text = message?.drama_preview?.join("\n") || "";
                this.__dramaManifest = message?.drama_manifest?.[0] || "[]";
                if (message?.drama_bundle?.[0]) {
                    this.__dramaBundle = message.drama_bundle[0];
                    if (!this.__dramaBundleDownload) {
                        this.__dramaBundleDownload = this.addWidget("button", "💾 保存完整资料包（续集用）", null, () => {
                            const href = window.URL.createObjectURL(new Blob([this.__dramaBundle], {type:"application/json;charset=utf-8"}));
                            const a = document.createElement("a");
                            a.href = href; a.download = "漫剧完整资料包.json"; a.click();
                            setTimeout(() => window.URL.revokeObjectURL(href), 1000);
                        });
                        this.__dramaBundleDownload.serialize = false;
                    }
                }
                if (!this.__dramaPreview) {
                    const preview = ComfyWidgets.STRING(this, "📚 文档预览", ["STRING", { multiline: true }], app).widget;
                    preview.serialize = false;
                    if (preview.inputEl) preview.inputEl.readOnly = true;
                    this.__dramaPreview = preview;
                }
                if (message?.drama_manifest && !this.__dramaDownload) {
                    const download = this.addWidget("button", "💾 下载提示词清单JSON", null, () => {
                        const href = window.URL.createObjectURL(new Blob([this.__dramaManifest], { type: "application/json;charset=utf-8" }));
                        const anchor = document.createElement("a");
                        anchor.href = href; anchor.download = "漫剧提示词清单.json";
                        anchor.click(); setTimeout(() => window.URL.revokeObjectURL(href), 1000);
                    });
                    download.serialize = false;
                    this.__dramaDownload = download;
                }
                this.__dramaPreview.value = text;
                setup(this);
                return result;
            };
        }
    },
});
