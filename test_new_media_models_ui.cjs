const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function load(file){let extension;const context=vm.createContext({app:{registerExtension(e){extension=e;}},api:{addEventListener(){}},window:{open(){return {}}},console,setTimeout(fn){fn();},globalThis:{}});vm.runInContext(fs.readFileSync(file,'utf8').replace(/^import .*;\r?$/gm,''),context);return extension;}
function node(type,model,count){return {comfyClass:type,size:[480,600],widgets:[['🤖 模型',model],['🎛️ 生成模式','自动识别'],['🧩 分辨率','720P'],['⚡ 异步模式',false]].map(([name,value])=>({name,value})),inputs:Array.from({length:count},(_,i)=>({name:`🖼️ 参考图${i+1}`})),addWidget(type,name,value){const w={type,name,value};this.widgets.push(w);return w;},addCustomWidget(w){this.widgets.push(w)},computeSize(){return [430,500]},setSize(v){this.size=v},setDirtyCanvas(){}};}
const video=load('web/js/dapao_seedance20_allround_video_ui.js');
for(const [type,model,count,price] of [['DapaoMuseVideoNode','muse-video',1,'0.3'],['DapaoGeminiOmniVideoNode','gemini-omni-1.2-flash',3,'0.08']]){
 const n=node(type,model,count);video.nodeCreated(n);
 assert(n.inputs.every(i=>!i.hidden));assert(n.widgets.find(w=>w.name==='💰 计费说明').value.includes(price));
 const mode=n.widgets.find(w=>w.name==='🎛️ 生成模式');mode.value='文生视频';mode.callback();assert(n.inputs.every(i=>i.hidden));
 mode.value='图生视频';mode.callback();assert(n.inputs.every(i=>!i.hidden));
 assert.equal(n.widgets.filter(w=>w.name==='👉点此注册API密钥👈').length,1);
 function Type(){}Type.prototype.configure=function(info){this.saved=info.widgets_values;};video.beforeRegisterNodeDef(Type,{name:type});
 const instance=new Type(),values=['key',model,'自动识别','prompt','720P','5','16:9',0,'fixed',1800,'10','120'];instance.configure({widgets_values:values});assert.deepEqual(instance.saved,values);
}
const image=load('web/js/dapao_gpt_image_2_allround_ui.js');
for(const [type,model] of [['DapaoGPTImage25AllroundNode','gpt-image-2.5-flare'],['DapaoGPTImage26AllroundNode','gpt-image-2.6-flare']]){
 const n=node(type,model,0);image.nodeCreated(n);assert(n.widgets.find(w=>w.name==='🤖 模型').value.startsWith('Flare'));assert.equal(n.widgets.filter(w=>w.name==='👉点此注册API密钥👈').length,1);
 if(type.includes('26'))assert(n.widgets.find(w=>w.name==='🤖 模型').tooltip.includes('最多3张'));
}
console.log('PASS Muse/Omni reference visibility, billing labels, saved widget compatibility and GPT 2.5/2.6 registration UI');
