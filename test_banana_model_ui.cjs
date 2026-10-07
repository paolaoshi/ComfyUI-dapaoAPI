const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('web/js/dapao_banana_allround_ui.js', 'utf8').replace(/^import .*;\r?\n/gm, '');
let extension;
const context = vm.createContext({app: {registerExtension(e) {extension = e;}}, api: {},
    console: {log() {}}, setTimeout() {}, window: {}});
vm.runInContext(source + '\nthis.refresh = refreshNode;', context);
const names = ['🤖 模型', '📐 图片尺寸/比例', '🧩 清晰度', '🧠 思考等级', '🔎 联网搜索'];
const n = {comfyClass: 'DapaoBananaAllroundNode',
    widgets: names.map((name, i) => ({name, value: ['bananaPRO','1:8','2K','深入（high）',true][i]})),
    inputs: names.slice(-2).map(name => ({name})), setDirtyCanvas() {}};
context.refresh(n);
assert.equal(n.widgets[1].value, '模型默认');
assert.equal(n.widgets[3].hidden, true);
assert.equal(n.widgets[4].hidden, true);
n.widgets[0].value = '香蕉Pro 2.1全分辨率';
context.refresh(n);
assert.equal(n.widgets[3].hidden, false);
assert.equal(n.widgets[4].hidden, false);
assert.equal(n.inputs[0].hidden, false);
assert(n.widgets[1].options.values.includes('8:1'));
assert.deepEqual(Array.from(n.widgets[2].options.values), ['1K','2K','4K']);
n.widgets[0].value = '香蕉2官方稳定版';
context.refresh(n);
assert.equal(n.widgets[3].hidden, true);
assert.equal(n.widgets[3].value, '深入（high）');
assert.equal(n.widgets[4].value, true);
class TestNode {onConfigure(config) {this.saved = config.widgets_values;}}
extension.beforeRegisterNodeDef(TestNode, {name: 'DapaoBananaAllroundNode'});
const oldValues = ['', '香蕉2官方稳定版', 'prompt', '16:9','2K',2,true,12345,'randomize',700];
const old = new TestNode(); old.onConfigure({widgets_values: oldValues});
assert.deepEqual(Array.from(old.saved), oldValues);
for (const [name, value] of [['🧭 搜索范围','仅网页'], ['⚙️ 高级设置',false],
    ['🖼️ 输出内容','仅图片'], ['💭 返回思考摘要',true], ['📏 输出Token上限',32768], ['🧾 系统指令','中文']]) {
    n.widgets.push({name,value});
}
n.widgets[0].value = '香蕉Pro 2.1全分辨率';
context.refresh(n);
const byName = name => n.widgets.find(w => w.name === name);
assert.equal(byName('🧭 搜索范围').hidden, false);
assert.equal(byName('🧾 系统指令').hidden, true);
byName('⚙️ 高级设置').value = true;
context.refresh(n);
assert.equal(byName('🧾 系统指令').hidden, false);
byName('🔎 联网搜索').value = false;
context.refresh(n);
assert.equal(byName('🧭 搜索范围').hidden, true);
assert.equal(byName('🧭 搜索范围').value, '仅网页');
assert(!byName('📐 图片尺寸/比例').options.values.includes('9:21'));
n.widgets[0].value = 'bananaPRO';
context.refresh(n);
assert.equal(byName('🧾 系统指令').hidden, true);
assert.equal(byName('⚙️ 高级设置').hidden, true);
console.log('PASS: model isolation, search scope, advanced folding, values preserved, old workflow order.');
