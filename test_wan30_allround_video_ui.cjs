const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
let extension;
const opens = [];
const context = vm.createContext({
  app: { registerExtension(value) { extension = value; } },
  api: { addEventListener() {} }, console,
  window: { open(url) { opens.push(url); return {}; } },
  setTimeout(callback) { callback(); }, globalThis: {},
});
const source = fs.readFileSync("web/js/dapao_wan30_allround_video_ui.js", "utf8").replace(/^import .*;\r?$/gm, "");
vm.runInContext(source, context);
const widgetNames = ["🤖 模型", "🎛️ 生成模式"];
const node = {
  comfyClass: "DapaoWan30AllroundVideoNode", size: [480, 800],
  widgets: widgetNames.map(name => ({name, value: name === "🤖 模型" ? "wan3.0" : name === "🎛️ 生成模式" ? "文生视频" : "", computeSize(){return [220,24];}})),
  inputs: ["🎬 首帧图", "🏁 尾帧图", ...Array.from({length:10},(_,i)=>`🖼️ 参考图${i+1}`),
    ...Array.from({length:5},(_,i)=>`🎞️ 参考视频${i+1}`), ...Array.from({length:5},(_,i)=>`🎵 参考音频${i+1}`)].map(name=>({name})),
  addCustomWidget(value){this.widgets.push(value);}, computeSize(){return [430,700];},
  setSize(value){this.size=value;}, setDirtyCanvas(){},
};
extension.nodeCreated(node);
const input = name => node.inputs.find(x=>x.name===name);
const widget = name => node.widgets.find(x=>x.name===name);
assert.equal(input("🎬 首帧图").hidden, true);
widget("🎛️ 生成模式").value = "首尾帧生视频"; widget("🎛️ 生成模式").callback();
assert.equal(input("🎬 首帧图").hidden, false); assert.equal(input("🏁 尾帧图").hidden, false);
widget("🎛️ 生成模式").value = "多模态参考"; widget("🎛️ 生成模式").callback();
assert.equal(input("🖼️ 参考图10").hidden, false); assert.equal(input("🎵 参考音频5").hidden, false);
assert.equal(input("🎞️ 参考视频1").hidden, true);
widget("🤖 模型").value = "wan3.0-video"; widget("🤖 模型").callback();
assert.equal(input("🎞️ 参考视频5").hidden, false);
const button = widget("👉点此注册API密钥👈");
const canvas = new Proxy({}, {get(target,key){return target[key] || (()=>{});}});
button.draw(canvas,node,900,100,40); assert.equal(button._area.width,464);
node.size[0]=620; button.draw(canvas,node,900,100,40); assert.equal(button._area.width,604);
for (const type of ["pointerdown","mousedown","click"]) assert.equal(button.mouse({type},[300,120],node),true);
assert.equal(opens.length,3); assert.ok(opens.every(x=>x==="https://api.dapaoai.com/sign-up?aff=vcOZ"));
extension.loadedGraphNode(node);
assert.equal(node.widgets.filter(x=>x.type==="DAPAO_WAN30_REGISTER").length,1);
assert.equal(node.widgets.filter(x=>x.type==="DAPAO_WAN30_PRICE").length,1);
function NodeType() {}
NodeType.prototype.onConfigure = function(config) { this.configured = config; };
extension.beforeRegisterNodeDef(NodeType, {name: "DapaoWan30AllroundVideoNode"});
const restored = new NodeType();
restored.onConfigure({widgets_values: ["key", "wan3.0", "文生视频", "prompt", "720P", "自适应", "5", true,
  "{}", "{}", 3600, 5, 180, false]});
assert.equal(restored.configured.widgets_values[8], 0);
assert.equal(restored.configured.widgets_values[9], "randomize");
assert.equal(restored.configured.widgets_values[10], 3600);
console.log("Wan 3.0 UI checks passed.");
