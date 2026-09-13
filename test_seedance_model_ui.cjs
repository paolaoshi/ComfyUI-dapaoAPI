const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const source = fs.readFileSync('web/js/dapao_seedance20_allround_video_ui.js', 'utf8').replace(/^import .*;\r?\n/gm, '');
let extension;
const context = vm.createContext({
    app: { registerExtension(value) { extension = value; } },
    api: {}, console: { log() {} }, setTimeout() {}, window: {},
});
vm.runInContext(source + '\nthis.sync = syncModelControls;', context);
function node(type, model, resolution) {
    return { comfyClass: type, widgets: [
        { name: '🤖 模型', value: model },
        { name: '🧩 分辨率', value: resolution, options: {} },
        { name: '🔊 生成音频', value: false },
    ] };
}
const n = node('DapaoSeedance20AllroundVideoNode', 'doubao-seedance-2.0', '1080P');
context.sync(n);
assert.deepEqual(Array.from(n.widgets[1].options.values), ['720P', '480P', '1080P']);
assert.equal(n.widgets[1].value, '1080P');
n.widgets[0].value = 'seedance-2.0';
context.sync(n, '🤖 模型');
assert.deepEqual(Array.from(n.widgets[1].options.values), ['720P']);
assert.equal(n.widgets[1].value, '720P');
assert.equal(n.widgets[2].disabled, true);
n.widgets[0].value = 'doubao-seedance-2.0';
context.sync(n, '🤖 模型');
assert.deepEqual(Array.from(n.widgets[1].options.values), ['720P', '480P', '1080P']);
assert.equal(n.widgets[2].disabled, false);
const newer = node('DapaoSeedance25AllroundVideoNode', 'doubao-seedance-2-5', '480P');
context.sync(newer);
assert.equal(newer.widgets[1].value, '480P');

class OldNode { configure(info) { this.saved = info.widgets_values; } }
extension.beforeRegisterNodeDef(OldNode, { name: 'DapaoSeedance20AllroundVideoNode' });
const old = new OldNode();
old.configure({ widgets_values: ['key', 'SD2-face', '文生视频', 'prompt', '720P', true, '5', '16:9', false, 42, 'randomize', '{}', '{}', 1800, 5, 120] });
assert.equal(old.saved[1], 'doubao-seedance-2.0');
assert.equal(old.saved[5], '5');
assert.equal(old.saved[7], false);
assert.equal(old.saved[8], 42);
assert.equal(old.saved[12], 120);
assert.equal(old.saved[13], false);
console.log('PASS: SP resolution filtering, restoring standard resolutions, audio control, 2.5 and legacy widget migration.');

const previous = new OldNode();
previous.configure({ widgets_values: ['key', 'seedance-2.0', '自动识别', 'prompt', '720P', '5', '16:9', false, 42, 'randomize', '{}', '{}', 1800, 5, 120, false] });
assert.equal(previous.saved[10], 1800);
assert.equal(previous.saved[12], 120);
const current = new OldNode();
current.configure({ widgets_values: previous.saved });
assert.deepEqual(current.saved, previous.saved);
