import { app } from "../../../scripts/app.js";
const TYPE = "DapaoMinimaxH3AllroundVideoNode";
const REGISTER = "👉点此注册API密钥👈";
let prices = null;
// Only accept the documented price-expression shape; never execute server expressions.
async function loadPrices() {
    try {
        const data = await fetch("/dapao/minimax-h3/pricing").then(r => r.json());
        prices = data.rates?.["720P"] > 0 && data.rates?.["1080P"] > 0 ? data.rates : null;
    } catch { prices = null; }
    app.graph?._nodes?.filter(n => n.comfyClass === TYPE).forEach(refresh);
}
function refresh(node) {
    if (!node.widgets) return;
    const get = name => node.widgets.find(w => w.name === name)?.value;
    const counts = ["🖼️ 参考图", "🎞️ 参考视频", "🎵 参考音频"].map(prefix =>
        node.inputs?.filter(i => i.name.startsWith(prefix) && i.link != null).length || 0);
    const resume = Boolean(String(get("🆔 继续任务ID") || "").trim());
    node.__h3Status = resume ? "继续原任务：仅查询/保存，不提交新生成" : `已接入 ${counts[0]} 图 / ${counts[1]} 视频 / ${counts[2]} 音频（批次逐张计数，上限12项）`;
    const rate = prices?.[get("🧩 分辨率")];
    node.__h3Price = resume ? "💰 不发起新生成，原任务费用以账单为准" : rate > 0
        ? `💰 标准分组 ¥${rate.toFixed(3)}/秒 · 预计 ¥${(rate * Number(get("⏱️ 时长(秒)") || 4)).toFixed(2)}（实际账单为准）`
        : "💰 费用以账单为准（暂未取得有效实时价格）";
    if (node.computeSize) {const size=node.computeSize();node.setSize([Math.max(480,node.size?.[0]||0,size[0]),size[1]]);}
    node.setDirtyCanvas?.(true,true);
}
function setup(node) {
    if (!node.widgets || node.__h3Setup) {refresh(node);return;}
    node.__h3Setup = true;
    for (const name of ["__h3Status","__h3Price"]) node.addCustomWidget({name, type:"H3_LABEL",serialize:false,
        computeSize(){return [460,24];}, draw(ctx,n,width,y){ctx.save();ctx.fillStyle="#d8bd89";ctx.font="12px sans-serif";ctx.textAlign="center";ctx.fillText(n[name]||"",n.size[0]/2,y+16);ctx.restore();}});
    node.addCustomWidget({name:REGISTER,type:"H3_REGISTER",serialize:false,computeSize(){return [220,38];},
        draw(ctx,n,width,y,height){const w=n.size[0];this.area=[8,y+3,w-16,32];ctx.save();ctx.fillStyle="#a96b1b";ctx.beginPath();ctx.roundRect(8,y+3,w-16,32,8);ctx.fill();ctx.fillStyle="#fff7df";ctx.font="bold 13px sans-serif";ctx.textAlign="center";ctx.fillText(REGISTER,w/2,y+24);ctx.restore();},
        mouse(e,pos){const a=this.area;if(a&&["pointerdown","mousedown","click"].includes(e.type)&&pos[0]>=a[0]&&pos[0]<=a[0]+a[2]&&pos[1]>=a[1]&&pos[1]<=a[1]+a[3]){window.open("https://api.dapaoai.com/sign-up?aff=vcOZ","_blank","noopener,noreferrer");return true;}return false;}});
    for(const w of node.widgets){const original=w.callback;w.callback=function(){const r=original?.apply(this,arguments);refresh(node);return r;};}
    refresh(node);
}
app.registerExtension({name:"Dapao.MinimaxH3.UI",setup:loadPrices,
    nodeCreated(n){if(n.comfyClass===TYPE)setTimeout(()=>setup(n),20);},
    loadedGraphNode(n){if(n.comfyClass===TYPE)setTimeout(()=>setup(n),20);},
    async beforeRegisterNodeDef(cls,data){if(data.name!==TYPE)return;
        for(const key of ["onConfigure","onConnectionsChange"]){const orig=cls.prototype[key];cls.prototype[key]=function(){const r=orig?.apply(this,arguments);setTimeout(()=>setup(this),20);return r;};}
    }
});
