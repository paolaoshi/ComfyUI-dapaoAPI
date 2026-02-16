import { app } from "../../../scripts/app.js";

function getWidget(node, name) {
    return node?.widgets?.find((w) => w?.name === name) || null;
}

function getWidgetBySuffix(node, suffix) {
    return node?.widgets?.find((w) => typeof w?.name === "string" && w.name.endsWith(suffix)) || null;
}

function setHidden(node, widget, hidden) {
    if (!widget) return;
    if (hidden) {
        if (widget._dapaoOrigComputeSize === undefined) {
            widget._dapaoOrigComputeSize = widget.computeSize;
        }
        widget.hidden = true;
        widget.computeSize = () => [0, -4];
    } else {
        widget.hidden = false;
        if (widget._dapaoOrigComputeSize) {
            widget.computeSize = widget._dapaoOrigComputeSize;
        }
    }
    node.setDirtyCanvas(true, true);
}

function updateLoraWidgets(node) {
    const enableWidget = getWidget(node, "🧩 启用LoRA") || getWidgetBySuffix(node, "启用LoRA");
    const countWidget = getWidget(node, "🔢 LoRA数量") || getWidgetBySuffix(node, "LoRA数量");
    const enabled = !!enableWidget?.value;
    const count = Math.max(1, Math.min(5, parseInt(countWidget?.value ?? "1", 10) || 1));

    setHidden(node, countWidget, !enabled);

    for (let i = 1; i <= 5; i++) {
        const idWidget = getWidget(node, `🧩 LoRA${i} ID`) || getWidgetBySuffix(node, `LoRA${i} ID`);
        const wWidget = getWidget(node, `🎚️ LoRA${i} 强度`) || getWidgetBySuffix(node, `LoRA${i} 强度`);
        const show = enabled && i <= count;
        setHidden(node, idWidget, !show);
        setHidden(node, wWidget, !show);
    }
}

app.registerExtension({
    name: "Dapao.ModelScopeT2I.LoRAUI",
    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "DapaoModelScopeTextToImage") return;

        const onNodeCreated = nodeType.prototype.onNodeCreated;
        nodeType.prototype.onNodeCreated = function () {
            onNodeCreated?.apply(this, arguments);
            updateLoraWidgets(this);
        };

        const onAdded = nodeType.prototype.onAdded;
        nodeType.prototype.onAdded = function () {
            onAdded?.apply(this, arguments);
            updateLoraWidgets(this);

            const enableWidget = getWidget(this, "🧩 启用LoRA") || getWidgetBySuffix(this, "启用LoRA");
            const countWidget = getWidget(this, "🔢 LoRA数量") || getWidgetBySuffix(this, "LoRA数量");
            if (enableWidget) {
                const orig = enableWidget.callback;
                enableWidget.callback = (...args) => {
                    orig?.apply(enableWidget, args);
                    updateLoraWidgets(this);
                };
            }
            if (countWidget) {
                const orig = countWidget.callback;
                countWidget.callback = (...args) => {
                    orig?.apply(countWidget, args);
                    updateLoraWidgets(this);
                };
            }
        };

        const onConfigure = nodeType.prototype.onConfigure;
        nodeType.prototype.onConfigure = function () {
            onConfigure?.apply(this, arguments);
            updateLoraWidgets(this);
        };
    },
});
