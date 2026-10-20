// Browser-script component doubles only. Python/native acceptance is separate.
"use strict";
const assert=require("node:assert/strict"),fs=require("node:fs"),vm=require("node:vm");
const code=fs.readFileSync(require("node:path").join(__dirname,"..","ui","app.js"),"utf8");
const tick=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};

async function scenario(mode){
  const els=new Map(),listeners=new Map();let opens=0,confirms=0,resolvePrepare;
  const preparations=[];
  const node=id=>{
    if(!els.has(id))els.set(id,{value:"",files:[],hidden:false,disabled:false,open:false,checked:false,textContent:"",
      replaceChildren(){},append(){},focus(){},reset(){this.value="";},
      addEventListener(type,callback){listeners.set(id+":"+type,callback);},
      showModal(){this.open=true;opens++;},close(){this.open=false;}});
    return els.get(id);
  };
  const text="Corrige este texto: Eu vai para casa.";
  const resolved={status:"RESOLVED",intent:"trabalhar",original:text,
    parser:"inline-proofread-v1",execution:"NOT_AUTHORIZED",source_kind:"inline_text"};
  const ctx={
    document:{getElementById:node},location:{hash:""},history:{replaceState(){}},
    sessionStorage:{getItem(){return "s";},setItem(){}},URLSearchParams,Uint8Array,
    btoa:v=>Buffer.from(v,"binary").toString("base64"),clearTimeout(){},setTimeout(){return 1;},
    fetch:async(path,options)=>{
      if(path==="/api/runs")return {ok:true,json:async()=>[]};
      if(path==="/api/interpret"){
        const preview={...resolved};
        if(mode==="no-server-marker")delete preview.source_kind;
        return {ok:true,json:async()=>preview};
      }
      if(path==="/api/prepare-run"){
        preparations.push(JSON.parse(options.body));
        const response={ok:true,json:async()=>({ticket:"one",process:"proofread",summary:"Rever texto",
          source_kind:"inline_text",filename:"texto.txt",attachment_bytes:18,attachment_sha256:"a".repeat(64)})};
        if(mode==="edited")return new Promise(resolve=>resolvePrepare=()=>resolve(response));
        return response;
      }
      if(path==="/api/confirm-run"){confirms++;throw Error("No execution is permitted by this component test");}
      throw Error("Unexpected path: "+path);
    }
  };
  vm.runInNewContext(code,ctx,{filename:"nexus/ui/app.js"});
  node("text").value=text;
  const request=node("form").onsubmit({preventDefault(){}});
  if(mode==="edited"){
    for(let i=0;i<20&&!resolvePrepare;i++)await tick();
    assert.ok(resolvePrepare);
    node("text").value=text+" Mais texto.";listeners.get("text:input")();
    node("text").value=text;listeners.get("text:input")();
    resolvePrepare();
  }
  await request;await tick();
  assert.equal(confirms,0);
  assert.equal(opens,mode==="inline"?1:0);
  assert.equal(preparations.length,mode==="no-server-marker"?0:1);
  if(preparations.length)assert.deepEqual(preparations[0],{text,filename:"",attachment:""});
  if(mode==="inline"){
    assert.equal(node("execution-confirmation").open,true);
    assert.equal(node("execution-approve").disabled,true);
    assert.equal(node("execution-review").textContent,text);
  }else assert.equal(node("submit").disabled,false);
}

(async()=>{
  for(const mode of ["inline","no-server-marker","edited"])await scenario(mode);
  console.log("PASS Folha inline: server marker required, body retained on server, explicit confirmation, stale edit refused");
})().catch(error=>{console.error(error);process.exitCode=1;});
