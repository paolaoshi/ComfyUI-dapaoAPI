const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
let extension, opened = [];
const app = { registerExtension(x) { extension = x; }, graph: {
    links: { 1: { origin_id: 3 } }, getNodeById() { return { type: 'DapaoDramaFinish' }; }
} };
const LiteGraph = { ContextMenu: class ContextMenu {
    constructor(items, options) { this.items = items; this.options = options; }
} };
const code = fs.readFileSync('web/js/dapao_short_drama_ui.js', 'utf8').replace(/^import .*;\r?\n/gm, '');
vm.runInNewContext(code, {
    LiteGraph,
    app, api: { addEventListener() {} },
    window: { open(...args) { opened.push(args); } }, setTimeout(fn) { fn(); }, console,
    ComfyWidgets: { STRING(node, name) { const widget = { name, value: '', inputEl: {} }; node.widgets.push(widget); return { widget }; } },
});
extension.setup();
let displayed;
const show = { type: 'easy showAnything', widgets: [], inputs: [{ name: 'anything', link: 1 }], onExecuted(message) { displayed = message; } };
extension.nodeCreated(show); extension.loadedGraphNode(show);
const original = { text: ['人物林夏', '走廊', '包裹', '防盗门'] };
show.onExecuted(original);
assert.deepEqual(show.widgets.map(w => w.value), original.text);
assert.equal(new Set(show.widgets.map(w => w.name)).size, 4);
show.onExecuted(original);
assert.equal(show.widgets.length, 4);
assert.equal(original.text.length, 4);
show.inputs[0].link = null;
show.onExecuted(original);
assert.strictEqual(displayed, original);
const menuClass = LiteGraph.ContextMenu;
extension.setup();
assert.strictEqual(LiteGraph.ContextMenu, menuClass);
const types = ['Project', 'Novel', 'Develop', 'Write', 'Assets', 'Image', 'Storyboard', 'Video', 'Review', 'Deliver', 'Merge'].map(x => `DapaoDrama${x}`);
const unordered = [...types.slice(0, 5), ...types.slice(6), types[5]].map(value => ({ value }));
const options = { title: 'test' };
const menu = new LiteGraph.ContextMenu(unordered, options);
assert.deepEqual(Array.from(menu.items, x => x.value), types);
assert.strictEqual(menu.options, options);
assert.equal(unordered[10].value, types[5]);
const categories = ['🐠漫剧一站式专用🐠', '🍬大炮AI主力维护🍬', '🍬大炮API常用工具🍬', '🔮API通用工具🔮'].map(x => ({ value: `🤖dapaoAPI/${x}/` }));
assert.deepEqual(Array.from(new LiteGraph.ContextMenu(categories).items, x => x.value), [categories[1], categories[2], categories[0], categories[3]].map(x => x.value));
const unrelated = [null, { value: 'another-node', content: 'Other' }];
assert.deepEqual(Array.from(new LiteGraph.ContextMenu(unrelated).items), unrelated);
const compactTypes = ['DapaoDramaPrepare', 'DapaoDramaVisual', 'DapaoDramaFinish'];
assert.deepEqual(Array.from(new LiteGraph.ContextMenu([...compactTypes].reverse().map(value => ({ value }))).items, x => x.value), compactTypes);
for (const event of ['pointerdown', 'mousedown', 'click']) {
    const node = { type: 'DapaoDramaWrite', size: [500, 500], widgets: [], addCustomWidget(w) { this.widgets.push(w); },
        computeSize() { return this.size; }, setSize(x) { this.size = x; }, setDirtyCanvas() {} };
    extension.nodeCreated(node); extension.loadedGraphNode(node);
    assert.equal(node.widgets.filter(w => w.name === '👉点此注册API密钥👈').length, 1);
    const b = node.widgets[0];
    const ctx = new Proxy({}, { get: () => () => {}, set: () => true });
    b.draw(ctx, node, 9999, 10, 40);
    assert.equal(b.area.w, 484);
    node.size[0] = 700; b.draw(ctx, node, 123, 10, 40);
    assert.equal(b.area.w, 684);
    assert.equal(b.serialize, false);
    assert(b.mouse({ type: event }, [20, 20]));
}
assert.equal(opened.length, 3);
assert(opened.every(x => x[0] === 'https://api.dapaoai.com/sign-up?aff=vcOZ'));
class Deliver {
    constructor() { this.type = 'DapaoDramaDeliver'; this.size = [500, 500]; this.widgets = []; }
    addWidget(type, name, value, callback) { const w = { type, name, value, callback }; this.widgets.push(w); return w; }
    addCustomWidget(w) { this.widgets.push(w); }
    computeSize() { return this.size; }
    setSize(x) { this.size = x; }
}
extension.beforeRegisterNodeDef(Deliver, { name: 'DapaoDramaDeliver' });
const delivery = new Deliver();
delivery.onExecuted({ drama_preview: ['五文档'], drama_manifest: ['[]'] });
delivery.onExecuted({ drama_preview: ['新文档'], drama_manifest: ['[]'] });
assert.equal(delivery.__dramaPreview.value, '新文档');
assert.equal(delivery.__dramaPreview.inputEl.readOnly, true);
assert.equal(delivery.widgets.filter(w => w.name === '💾 下载提示词清单JSON').length, 1);
for (const type of compactTypes) {
    class Compact extends Deliver { constructor() { super(); this.type = type; } }
    extension.beforeRegisterNodeDef(Compact, { name: type });
    const node = new Compact();
    extension.nodeCreated(node);
    const message = { drama_preview: ['合并节点文档'] };
    if (type === 'DapaoDramaFinish') message.drama_manifest = ['[]'];
    node.onExecuted(message); node.onExecuted(message);
    assert.equal(node.__dramaPreview.value, '合并节点文档');
    assert.equal(node.widgets.filter(w => w.name === '👉点此注册API密钥👈').length, 1);
    assert.equal(node.widgets.filter(w => w.name === '📚 文档预览').length, 1);
    assert.equal(node.widgets.filter(w => w.name === '💾 下载提示词清单JSON').length, type === 'DapaoDramaFinish' ? 1 : 0);
}
console.log('Drama registration button resize/click checks passed.');
for (const type of compactTypes) {
    const node = new Deliver(); node.type = type; node.size = [900, 600];
    node.widgets = [{name: '导入文档', value: '原稿', inputEl: {style: {}}}];
    node.computeSize = () => [300, node.__dramaAdvancedOpen ? 1200 : 400];
    extension.nodeCreated(node);
    node.__dramaAdvanced.callback();
    assert.equal(node.size[0], 900);
    assert.equal(node.widgets[0].hidden, false);
    node.__dramaAdvanced.callback();
    assert.equal(node.size[0], 900);
    assert.equal(node.widgets[0].value, '原稿');
}
const timed = new Deliver(); timed.type = 'DapaoDramaFinish';
timed.widgets = [
    {name:'⏱️ 时长规划',value:'按段数逐段设置'},
    {name:'🔢 分段数量',value:4},
    {name:'⏳ 总时长规则',value:'必须与01目标一致'},
    ...[6,6,8,10,10].map((value,i)=>({name:`⏱️ 第${String(i+1).padStart(2,'0')}段（秒）`,value})),
];
extension.nodeCreated(timed);
assert(timed.__dramaTimingSummary.name.includes('4段，共30秒'));
assert.equal(timed.widgets[7].hidden,true);
timed.widgets[1].value=2; timed.widgets[1].callback();
assert(timed.__dramaTimingSummary.name.includes('2段，共12秒'));
assert.equal(timed.widgets[5].hidden,true);
console.log('Advanced width and per-segment controls passed.');
// A DOM widget's computed height can include the height allocated on the last
// load. Replaying configure/added/loaded hooks must not accumulate that height.
for (const type of compactTypes) {
    class Reloadable extends Deliver {
        constructor() { super(); this.type = type; }
        computeSize() { return [440, this.size[1] + 180]; }
        onConfigure(data) { this.size = [...data.size]; }
    }
    extension.beforeRegisterNodeDef(Reloadable, {name:type});
    let saved = [820, 1100];
    for (let refresh = 0; refresh < 5; refresh++) {
        const node = new Reloadable();
        node.onNodeCreated();
        node.onConfigure({size:saved});
        node.onAdded();
        extension.nodeCreated(node);
        extension.loadedGraphNode(node);
        node.onExecuted({drama_preview:['文档内容']});
        assert.deepEqual(node.size, saved, 'refresh must preserve saved dimensions');
        assert.equal(node.widgets.filter(w => w.name === '👉点此注册API密钥👈').length, 1);
        node.size = [850, 1150]; // User resize persists through the next refresh.
        saved = [...node.size];
    }
}
console.log('Repeated workflow reload preserves user dimensions.');
const domNode = new Deliver(); domNode.type = 'DapaoDramaFinish'; domNode.size = [820,1100];
domNode.widgets = [{name:'创作要求',type:'customtext',options:{},element:{tagName:'TEXTAREA',style:{}},computeLayoutSize(){return {minHeight:domNode.size[1],minWidth:0};}}];
extension.loadedGraphNode(domNode);
for(let i=0;i<5;i++) {
    const minimum = domNode.widgets[0].computeLayoutSize().minHeight;
    assert.equal(minimum,64);
    // Mirror LiteGraph arrange: expand only if widget minima exceed available room.
    domNode.setSize([820,Math.max(domNode.size[1],minimum+500)]);
    extension.loadedGraphNode(domNode);
    assert.equal(domNode.size[1],1100);
}
console.log('DOM layout minima no longer depend on saved node height.');
class EarlyResize extends Deliver {
    constructor(){super();this.type='DapaoDramaFinish';}
    configure(data){this.size=[...data.size];this.setSize([this.size[0],1870]);this.onConfigure(data);}
}
extension.beforeRegisterNodeDef(EarlyResize,{name:'DapaoDramaFinish'});
const early = new EarlyResize();
for(let i=0;i<5;i++) {early.configure({size:[540,900]});assert.deepEqual(early.size,[540,900]);}
console.log('Saved size wins over pre-onConfigure slot restoration resize.');
const bundleNode = new Deliver(); bundleNode.type='DapaoDramaPrepare';
const bundleMessage={drama_preview:['第二集'],drama_bundle:['{"schema":"dapao.drama/1"}']};
bundleNode.onExecuted(bundleMessage);bundleNode.onExecuted(bundleMessage);
assert.equal(bundleNode.widgets.filter(w=>w.name==='💾 保存完整资料包（续集用）').length,1);
assert.equal(bundleNode.__dramaBundle,bundleMessage.drama_bundle[0]);
assert.equal(bundleNode.__dramaBundleDownload.serialize,false);
// Legacy computeSize takes precedence in actual LiteGraph; test both paths.
const legacyText = new Deliver(); legacyText.type='DapaoDramaFinish';
legacyText.widgets=[{name:'正文',type:'customtext',computeSize(){return [0,legacyText.size[1]];}}];
extension.loadedGraphNode(legacyText);
assert.equal(legacyText.widgets[0].computeSize()[1],64);
legacyText.size[1]=5000;
assert.equal(legacyText.widgets[0].computeSize()[1],64);
const fresh = new Deliver();fresh.type='DapaoDramaFinish';fresh.size=[440,1870];
fresh.computeSize=()=>[440,666];
extension.nodeCreated(fresh);
assert.equal(fresh.size[1],666,'new nodes must discard hidden-control construction height');
class OldTall extends EarlyResize {computeSize(){return [440,700];}}
extension.beforeRegisterNodeDef(OldTall,{name:'DapaoDramaFinish'});
const oldTall=new OldTall();oldTall.configure({size:[540,2500],properties:{}});
assert.equal(oldTall.size[1],800);
oldTall.configure({size:[540,1500],properties:{dapaoDramaStableLayout:true}});
assert.equal(oldTall.size[1],1500,'after migration deliberate user height is preserved');
console.log('Legacy sizing, compact construction and old workflow migration passed.');
const oldPorts = new Deliver();oldPorts.type='DapaoDramaFinish';
oldPorts.outputs=Array.from({length:10},(_,i)=>({name:'old'+i,links:[i]}));
oldPorts.addOutput=function(name,type){this.outputs.push({name,type});};
extension.loadedGraphNode(oldPorts);extension.loadedGraphNode(oldPorts);
assert.equal(oldPorts.outputs.length,11);
assert.equal(oldPorts.outputs[10].name,'💾 完整资料包JSON（续集用）');
assert.deepEqual(oldPorts.outputs.slice(0,10).map(o=>o.links),Array.from({length:10},(_,i)=>[i]));
const persistedShow={type:'easy showAnything',widgets:[],inputs:[{name:'anything',link:1}],properties:{}};
extension.nodeCreated(persistedShow);
persistedShow.onExecuted({text:['镜头一','镜头二']});
persistedShow.onExecuted({});
assert.deepEqual(persistedShow.widgets.map(w=>w.value),['镜头一','镜头二']);
const restoredShow={type:'easy showAnything',widgets:[],inputs:[{name:'anything',link:1}],properties:JSON.parse(JSON.stringify(persistedShow.properties))};
extension.loadedGraphNode(restoredShow);
assert.deepEqual(restoredShow.widgets.map(w=>w.value),['镜头一','镜头二']);
restoredShow.onConfigure({});
assert.equal(restoredShow.widgets.length,2);
restoredShow.onExecuted({text:[]});
assert.equal(restoredShow.widgets.length,0);
assert.deepEqual(Array.from(restoredShow.properties.dapaoDramaPreviewText),[]);
console.log('Prompt display survives saved workflow reload and textless callbacks.');
