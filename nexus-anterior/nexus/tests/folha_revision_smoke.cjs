// Standard Node test harness for the real browser script (no external packages).
// All HTTP calls are doubles; Windows CI separately tests the live Python Host.
"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const code=fs.readFileSync(require("node:path").join(__dirname,"..","ui","app.js"),"utf8");
const tick=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const fakeFile=()=>({name:"prova.txt",size:1,arrayBuffer:async()=>Uint8Array.from([97]).buffer});
async function scenario(mode){
  const els=new Map(),listeners=new Map();let resolveInterpret,resolvePrepare,opens=0,prepares=0,confirms=0;
  const node=id=>{
    if(!els.has(id))els.set(id,{value:"",files:[],hidden:false,disabled:false,open:false,checked:false,textContent:"",
      replaceChildren(){},append(){},focus(){},reset(){this.value="";},
      addEventListener(type,callback){listeners.set(id+":"+type,callback);},
      showModal(){this.open=true;opens++;},close(){this.open=false;}});
    return els.get(id);
  };
  const resolved={status:"RESOLVED",intent:"trabalhar",original:"Verifica a integridade deste ficheiro.",parser:"eliza-rules-v1",confirmation_required:false,execution:"NOT_AUTHORIZED"};
  const ctx={
    document:{getElementById:node},location:{hash:""},history:{replaceState(){}},
    sessionStorage:{getItem(){return "s";},setItem(){}},URLSearchParams,Uint8Array,
    btoa:v=>Buffer.from(v,"binary").toString("base64"),
    clearTimeout(){},setTimeout(){return 1;},
    fetch:async(path)=>{
      if(path==="/api/runs")return {ok:true,json:async()=>[]};
      if(path==="/api/interpret"){
        const make=()=>({ok:true,json:async()=>mode==="archive"?
          {...resolved,intent:"arquivo",original:"Guarda esta nota."}:resolved});
        if(mode==="race-interpret")return new Promise(r=>resolveInterpret=()=>r(make()));
        return make();
      }
      if(path==="/api/prepare-run"){
        prepares++;
        const make=()=>({ok:true,json:async()=>({ticket:"one",process:"verify",summary:"Verificar integridade",
          filename:"prova.txt",attachment_bytes:1,attachment_sha256:"a".repeat(64)})});
        if(mode==="race-prepare"||mode==="file-changed")
          return new Promise(r=>resolvePrepare=()=>r(make()));
        return make();
      }
      if(path==="/api/confirm-run"){confirms++;return {ok:true,json:async()=>({status:"CANCELLED"})};}
      throw Error("Unexpected path: "+path);
    }
  };
  vm.runInNewContext(code,ctx,{filename:"nexus/ui/app.js"});
  node("text").value=mode==="archive"?"Guarda esta nota.":resolved.original;
  if(mode!=="archive")node("file").files=[fakeFile()];
  const request=node("form").onsubmit({preventDefault(){}});
  for(let i=0;i<20 && !(resolveInterpret||resolvePrepare);i++)await tick();
  if(mode==="race-interpret"){
    assert.ok(resolveInterpret);
    const first=node("text").value;
    node("text").value="alterado";listeners.get("text:input")();
    node("text").value=first;listeners.get("text:input")();
    resolveInterpret();
  }
  if(mode==="race-prepare"||mode==="file-changed"){
    assert.ok(resolvePrepare);
    if(mode==="race-prepare"){
      const first=node("text").value;
      node("text").value="alterado";listeners.get("text:input")();
      node("text").value=first;listeners.get("text:input")();
    }else{
      node("file").files=[fakeFile()];node("file").onchange();
    }
    resolvePrepare();
  }
  await request;await tick();
  assert.equal(confirms,0,"must never execute while interpreting");
  assert.equal(opens,mode==="unchanged"?1:0,"stale or non-executable response opened an approval");
  assert.equal(prepares,mode==="archive"||mode==="race-interpret"?0:1);
  if(mode==="unchanged"){
    assert.equal(node("execution-confirmation").open,true);
    assert.equal(node("execution-approve").disabled,true);
  }else{
    assert.equal(node("execution-confirmation").open,false);
    assert.equal(node("submit").disabled,false);
  }
  if(mode==="archive"){
    assert.equal(node("result").hidden,false);
    assert.match(node("result-title").textContent,/Arquivo/);
    assert.equal(node("actions").hidden,true);
  }
}
(async()=>{
  for(const mode of ["race-interpret","race-prepare","file-changed","unchanged","archive"])
    await scenario(mode);
  console.log("PASS Folha: stale edit-return, file changed, valid verify, unexecutable archive preview");
})().catch(e=>{console.error(e);process.exitCode=1;});
