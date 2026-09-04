// Canvas contract checks without a browser or live ComfyUI server.
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
let extension;
const navigations = [];
const context = vm.createContext({
    app: { registerExtension(value) { extension = value; } },
    api: { addEventListener() {} }, console,
    window: { open(url) { navigations.push(url); return {}; } },
    setTimeout(callback) { callback(); },
});
const source = fs.readFileSync("web/js/dapao_portrait_photography_prompt_ui.js", "utf8")
    .replace(/^import .*;\r?$/gm, "");
vm.runInContext(source, context);
const node = {
    comfyClass: "DapaoPortraitPhotographyPromptNode", size: [460, 700],
    widgets: [
        { name: "⚙️ 展开摄影参数", value: false },
        { name: "👤 人物年龄", value: "自动选择", computeSize() { return [220, 24]; } },
    ],
    addCustomWidget(value) { this.widgets.push(value); },
    computeSize() { return [430, 700]; },
    setSize(value) { this.size = value; }, setDirtyCanvas() {},
};
extension.nodeCreated(node);
const age = node.widgets.find(w => w.name === "👤 人物年龄");
assert.equal(age.hidden, true);
node.widgets[0].value = true;
node.widgets[0].callback();
assert.equal(age.hidden, false);
const button = node.widgets.find(w => w.name === "👉点此注册API密钥👈");
const canvas = new Proxy({}, { get(target, key) { return target[key] || (() => {}); } });
button.draw(canvas, node, 900, 100, 40);
assert.equal(button._area.width, 444); // live node size, not sidebar width
node.size[0] = 620;
button.draw(canvas, node, 900, 100, 40);
assert.equal(button._area.width, 604);
for (const type of ["pointerdown", "mousedown", "click"]) {
    assert.equal(button.mouse({ type }, [300, 120], node), true);
}
assert.equal(navigations.length, 3);
assert.ok(navigations.every(url => url === "https://api.dapaoai.com/sign-up?aff=vcOZ"));
extension.loadedGraphNode(node);
assert.equal(node.widgets.filter(w => w === button).length, 1);
assert.equal(node.widgets.filter(w => w.type === "DAPAO_PORTRAIT_PRICE_LABEL").length, 1);
assert.equal(button.serialize, false);
console.log("Portrait UI checks passed: collapse, live resize, registration events, restore, price label.");
