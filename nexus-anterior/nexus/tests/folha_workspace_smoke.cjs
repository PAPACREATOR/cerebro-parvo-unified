"use strict";
const {test}=require("node:test");
const assert=require("node:assert/strict");
const fs=require("node:fs"),path=require("node:path"),vm=require("node:vm");
const code=fs.readFileSync(path.join(__dirname,"..","ui","app.js"),"utf8");
const tick=async()=>{for(let i=0;i<18;i++)await Promise.resolve();};
function sheet({handler,responseHandler,storageBlocked=false,hash=""}={}) {
  const nodes=new Map(),storage=new Map([["nexus-session","host-session"]]),calls=[],downloads=[];
  const hidden=new Set(["workspace","history-panel","composer-bottom","notice","result","actions","pdf","empty","resume"]);
  const node=id=>{
    if(!nodes.has(id)) {
      const listeners={};
      nodes.set(id,{id,value:"",files:[],hidden:hidden.has(id),disabled:false,open:false,checked:false,textContent:"",
        attributes:{},classList:{toggle(){}},replaceChildren(){},append(){},focus(){},scrollIntoView(){},
        addEventListener(type,fn){(listeners[type]??=[]).push(fn);},
        dispatch(type,event={}){for(const fn of listeners[type]??[])fn(event);},
        setAttribute(key,value){this.attributes[key]=value;},
        showModal(){this.open=true;},close(){this.open=false;},
        click(){if(this.onclick)return this.onclick();},
        reset(){node("text").value="";node("file").files=[];node("file").value="";},
        requestSubmit(){return node("form").onsubmit({preventDefault(){}});}
      });
    }
    return nodes.get(id);
  };
  const ctx=vm.createContext({
    document:{getElementById:node,querySelector(selector){return node(selector===".sheet"?"surface":selector===".attachment"?"attachment":selector.slice(1));},
      createElement(){const value=node("download-"+downloads.length);value.click=()=>downloads.push(value);return value;}},
    location:{hash},history:{replaceState(){}},
    sessionStorage:{getItem(key){if(storageBlocked)throw new Error("Blocked");return storage.get(key)??null;},
      setItem(key,value){if(storageBlocked)throw new Error("Blocked");storage.set(key,value);}},
    fetch:async(route,options)=>{
      const body=options?.body?JSON.parse(options.body):undefined;calls.push({route,body,headers:options?.headers});
      const value=handler?await handler(route,body):[];
      if(responseHandler)return responseHandler(route,value);
      return {ok:true,json:async()=>value};
    },
    URLSearchParams,Uint8Array,Blob,btoa,clearTimeout(){},setTimeout(){return 0;},
    URL:{createObjectURL(blob){storage.set("download-blob",blob);return "blob:preparation";},revokeObjectURL(){}},
    console
  });
  vm.runInContext(code,ctx);
  return {node,storage,calls,downloads,ctx,
    input(id,value){node(id).value=value;node(id).dispatch("input");},
    async submit(text){this.input("text",text);await node("form").onsubmit({preventDefault(){}});await tick();}
  };
}
for(const [product,request] of [
  ["text","Faz-me um artigo sobre o turismo no Alentejo."],
  ["podcast","Quero criar um podcast: Alma Lusitana."],
  ["music","Cria uma música sobre identidade portuguesa urbana."],
  ["short","Prepara uma curta sobre um bairro de Lisboa."]
]) {
  test(product+" starts with a brief; no research, tools or approvals are invented",async()=>{
    const ui=sheet();assert.equal(ui.calls.length,0);
    assert.equal(ui.node("composer-bottom").hidden,true);assert.equal(ui.node("workspace").hidden,true);
    await ui.submit(request);
    assert.equal(ui.node("product").value,product);
    assert.equal(ui.node("stage-title").textContent,"Ideia");
    assert.equal(ui.node("stage-reviewed").disabled,true);
    const draft=JSON.parse(ui.storage.get("nexus-preparation"));
    assert.equal(draft.original,request);assert.equal(draft.produced,false);
    assert.ok(draft.stages.every(s=>!s.reviewed && !s.text));
    assert.equal(ui.calls.length,0);
    ui.node("stage-4").click();
    assert.match(ui.node("stage-guidance").textContent,/ainda não/);
    assert.equal(ui.node("stage-reviewed").disabled,true);
    assert.equal(ui.calls.length,0);
  });
}
test("ambiguous products require a human choice; original Unicode remains intact",async()=>{
  const ui=sheet();const original="Quero um texto e um podcast.\nSaudade — ação 🇵🇹";
  await ui.submit(original);
  assert.equal(ui.node("product").value,"");
  ui.node("product").value="podcast";ui.node("product").onchange();
  assert.equal(JSON.parse(ui.storage.get("nexus-preparation")).original,original);
  assert.equal(ui.calls.length,0);
});
test("submitting the working sheet again preserves the brief, notes and current stage",async()=>{
  const ui=sheet();await ui.submit("Prepara uma curta sobre Lisboa.");
  ui.input("brief-objective","Contar uma história com sentido.");
  ui.input("brief-audience","Público português.");
  ui.input("brief-format","MP4");
  ui.input("stage-notes","Ideia humana — conservar.");
  const before=ui.storage.get("nexus-preparation");
  await ui.node("form").onsubmit({preventDefault(){}});
  assert.equal(ui.storage.get("nexus-preparation"),before);
  ui.node("stage-reviewed").checked=true;ui.node("stage-reviewed").onchange();
  ui.node("stage-next").click();ui.input("stage-notes","Notas e fontes a confirmar.");
  const research=ui.storage.get("nexus-preparation");
  await ui.node("form").onsubmit({preventDefault(){}});
  assert.equal(ui.storage.get("nexus-preparation"),research);
  assert.equal(ui.node("stage-title").textContent,"Pesquisa");
  ui.node("workspace").hidden=true;
  await ui.node("form").onsubmit({preventDefault(){}});
  assert.equal(ui.node("workspace").hidden,false);
  assert.equal(ui.storage.get("nexus-preparation"),research);
  assert.equal(ui.node("stage-title").textContent,"Pesquisa");
  assert.equal(ui.calls.length,0);
});
test("ordered reviews, edited upstream material and export preserve an honest draft",async()=>{
  const ui=sheet();await ui.submit("Faz-me um artigo sobre o Alentejo.");
  for(const [key,value] of [["objective","Informar"],["audience","Leitores locais"],["format","DOCX/PDF"]])
    ui.input("brief-"+key,value);
  ui.node("stage-reviewed").checked=true;ui.node("stage-reviewed").onchange();
  ui.node("stage-next").click();
  assert.equal(ui.node("stage-title").textContent,"Pesquisa");
  for(let i=1;i<6;i++) {
    ui.input("stage-notes","Material humano da etapa "+i+"; fonte: livro ou https://example.org.");
    ui.node("stage-reviewed").checked=true;ui.node("stage-reviewed").onchange();
    if(i<5)ui.node("stage-next").click();
  }
  assert.equal(ui.node("workspace-status").textContent,"Preparação revista");
  ui.node("save-preparation").click();
  const exported=JSON.parse(await ui.storage.get("download-blob").text());
  assert.equal(exported.produced,false);assert.ok(exported.stages.every(s=>s.reviewed));
  assert.equal(ui.calls.length,0);
  ui.node("stage-1").click();ui.input("stage-notes","Fonte revista.");
  const changed=JSON.parse(ui.storage.get("nexus-preparation"));
  assert.equal(changed.stages[0].reviewed,true);
  assert.ok(changed.stages.slice(1).every(s=>!s.reviewed));
  assert.equal(changed.stages[5].text,exported.stages[5].text);
  assert.equal(ui.node("workspace-status").textContent,"Preparação");
  ui.node("file").files=[{name:"nova-fonte.txt",size:1}];
  ui.node("file").onchange();ui.node("file").dispatch("change");
  const sourceChanged=JSON.parse(ui.storage.get("nexus-preparation"));
  assert.equal(sourceChanged.source_filename,"nova-fonte.txt");
  assert.ok(sourceChanged.stages.every(s=>!s.reviewed));
  assert.equal(sourceChanged.stages[5].text,exported.stages[5].text);
});
test("a new sheet is blank; restoring the draft does not restore authority",async()=>{
  const ui=sheet();await ui.submit("Cria música: emoção e saudade.");
  ui.node("new").click();
  assert.equal(ui.node("text").value,"");assert.equal(ui.node("workspace").hidden,true);
  assert.equal(ui.node("composer-bottom").hidden,true);
  ui.node("resume").click();
  assert.equal(ui.node("text").value,"Cria música: emoção e saudade.");
  assert.equal(ui.node("execution-confirmation").open,false);
  assert.equal(ui.node("approval").open,false);assert.equal(ui.calls.length,0);
  ui.storage.set("nexus-preparation",'{"schema":"bad"}');ui.node("resume").click();
  assert.match(ui.node("notice").textContent,/retomar/);
});
test("blocked browser storage keeps the supplied Host session; drafts grant no authority",async()=>{
  const ui=sheet({storageBlocked:true,hash:"#session=provided-by-host",handler:async(route)=>{
    if(route==="/api/interpret")return {status:"RESOLVED",intent:"trabalhar",original:"pedido"};
    if(route==="/api/prepare-run")return {ticket:"native-ticket",process:"verify",filename:"fonte.txt",attachment_bytes:1,attachment_sha256:"hash"};
    return [];
  }});
  ui.node("file").files=[{name:"fonte.txt",size:1,arrayBuffer:async()=>Uint8Array.from([97]).buffer}];
  await ui.submit("& verificar integridade de ficheiro");
  assert.equal(ui.calls.length,2);
  assert.ok(ui.calls.every(c=>c.headers["X-Nexus-Session"]==="provided-by-host"));
  ui.node("new").click();await ui.submit("Cria um podcast sobre a cidade.");
  ui.node("new").click();ui.node("resume").click();
  assert.equal(ui.node("text").value,"Cria um podcast sobre a cidade.");
  assert.equal(ui.node("execution-confirmation").open,false);
  assert.equal(ui.calls.length,2);
});
const commands=[
  ["verify","& verificar integridade de ficheiro"],
  ["interpret","& interpretar documento"],
  ["proofread","& rever texto"],
  ["convert_pdf","& converter para pdf"],
  ["video","& preparar plano de video"],
  ["podcast","& preparar plano de podcast"],
  ["visual_podcast","& preparar plano de podcast visual"],
  ["book","& exportar manuscrito para pdf"],
  ["music","& preparar plano de musica"],
  ["web","@ preparar plano de pesquisa web"]
];
for(const [process,command] of commands) {
  test(process+" still enters the native pre-execution gate instead of the working draft",async()=>{
    const ui=sheet({handler:async(route)=>{
      if(route==="/api/interpret") return {status:"RESOLVED",intent:process==="web"?"web":"trabalhar",original:command};
      if(route==="/api/prepare-run") return {ticket:"native-ticket",process,filename:"fonte.txt",attachment_bytes:1,attachment_sha256:"native-hash"};
      return [];
    }});
    ui.node("file").files=[{name:"fonte.txt",size:1,arrayBuffer:async()=>Uint8Array.from([97]).buffer}];
    await ui.submit(command);
    assert.equal(ui.node("execution-confirmation").open,true);
    assert.equal(ui.node("workspace").hidden,true);
    assert.deepEqual(ui.calls.map(c=>c.route),["/api/interpret","/api/prepare-run"]);
    assert.equal(ui.node("execution-approve").disabled,true);
    assert.doesNotMatch(ui.node("execution-summary").textContent,/OpenNotebook|LanguageTool|MCP|Canonical/);
    assert.doesNotMatch(ui.node("execution-review").textContent,/SHA-256|native-hash|Bytes/);
  });
}
test("deny consumes the proposed ticket; allow submits only the reviewed payload",async()=>{
  for(const allow of [false,true]) {
    const ui=sheet({handler:async(route)=>{
      if(route==="/api/interpret")return {status:"RESOLVED",intent:"trabalhar",original:"pedido"};
      if(route==="/api/prepare-run")return {ticket:"native-ticket",process:"verify",filename:"fonte.txt",attachment_bytes:1,attachment_sha256:"hash"};
      if(route==="/api/confirm-run")return allow?{run_id:"native-run"}:{status:"CANCELLED"};
      if(route==="/api/runs/native-run")return {title:"Verificação",status:"HUMAN_REQUIRED",content:"resultado",message:"Por rever"};
      return [];
    }});
    ui.node("file").files=[{name:"fonte.txt",size:1,arrayBuffer:async()=>Uint8Array.from([97]).buffer}];
    await ui.submit("& verificar integridade de ficheiro");
    if(allow) {
      ui.node("execution-confirm").checked=true;ui.node("execution-confirm").onchange();
      await ui.node("execution-approve").onclick();
    } else await ui.node("execution-cancel").onclick();
    const confirmations=ui.calls.filter(c=>c.route==="/api/confirm-run");
    assert.equal(confirmations.length,1);assert.equal(confirmations[0].body.confirmed,allow);
    assert.equal(confirmations[0].body.ticket,"native-ticket");
    assert.equal(confirmations[0].body.attachment,"YQ==");
    assert.equal(confirmations[0].body.text,"& verificar integridade de ficheiro");
    assert.ok(!ui.calls.some(c=>c.route==="/api/approve"));
  }
});
test("late result or late approval preview cannot replace a new blank sheet",async()=>{
  let resolveDetail;
  const ui=sheet({handler:async(route)=>{
    if(route==="/api/runs/old")return new Promise(resolve=>{resolveDetail=resolve;});
    return [];
  }});
  const pending=vm.runInContext('show("old")',ui.ctx);await tick();
  ui.node("new").click();resolveDetail({status:"HUMAN_REQUIRED",title:"Old",content:"Old"});
  await pending;
  assert.equal(ui.node("result").hidden,true);assert.equal(ui.node("text").value,"");
  let resolveApproval;
  const later=sheet({handler:async(route)=>{
    if(route==="/api/runs/current")return {status:"HUMAN_REQUIRED",title:"Current",content:"Current"};
    if(route==="/api/prepare")return new Promise(resolve=>{resolveApproval=resolve;});
    return [];
  }});
  await vm.runInContext('show("current")',later.ctx);
  const review=later.node("prepare").onclick();await tick();later.node("new").click();
  resolveApproval({ticket:"old-preview",content:"Current"});await review;
  assert.equal(later.node("approval").open,false);
  assert.ok(!later.calls.some(c=>c.route==="/api/approve"));
});
test("results and approval show human content; original evidence and bound version remain intact",async()=>{
  const raw="# Música — candidato de produção\n\n## Letra\nSaudade — ação 🇵🇹\n\n## Destino\nACE-Step local. A geração de áudio físico é validada no gate pós-instalação.";
  const ui=sheet({handler:async(route)=>{
    if(route==="/api/runs/music")return {status:"HUMAN_REQUIRED",process_id:"music",result:{title:"Música — especificação ACE-Step"},content:raw};
    if(route==="/api/prepare")return {ticket:"hash-bound-ticket",content:raw};
    return [];
  }});
  await vm.runInContext('show("music")',ui.ctx);
  assert.equal(ui.node("result-title").textContent,"Música — plano");
  assert.doesNotMatch(ui.node("content").textContent,/ACE-Step|Kernel|Host|SHA-256/);
  assert.match(ui.node("content").textContent,/Saudade — ação 🇵🇹/);
  assert.match(ui.node("content").textContent,/continuam pendentes/);
  await ui.node("prepare").onclick();
  assert.equal(ui.node("review").textContent,ui.node("content").textContent);
  assert.equal(ui.node("approve").disabled,true);
  ui.node("download").click();
  assert.equal(await ui.storage.get("download-blob").text(),raw);
  assert.ok(!ui.calls.some(c=>c.route==="/api/approve"));
  ui.node("confirm").checked=true;ui.node("confirm").onchange();
  await ui.node("approve").onclick();
  const approvals=ui.calls.filter(c=>c.route==="/api/approve");
  assert.equal(approvals.length,1);
  assert.deepEqual(approvals[0].body,{run_id:"music",ticket:"hash-bound-ticket",confirmed:true});
});
test("PDF metadata and native failure diagnostics do not leak into the sheet",async()=>{
  const ui=sheet({handler:async(route)=>route==="/api/runs/pdf"?
    {status:"BLOCKED",process_id:"convert_pdf",title:"Documento",content:"# PDF convertido\n\nTexto preservado.\n\nPDF SHA-256: "+"a".repeat(64),message:"Writer LPAC recusado: Sandy; DACL inesperada."}:[]});
  await vm.runInContext('show("pdf")',ui.ctx);
  assert.equal(ui.node("content").textContent,"# PDF convertido\n\nTexto preservado.");
  assert.doesNotMatch(ui.node("message").textContent,/Writer|Sandy|LPAC|DACL/);
  assert.match(ui.node("message").textContent,/pedido foi conservado/);
});
for(const route of ["/api/confirm-run","/api/approve"]) {
  for(const failure of ["connection lost","truncated JSON","declared UNKNOWN"]) {
    test(route+" "+failure+": human outcome is uncertain, consumed ticket is never retried",async()=>{
      const effects=[];
      const content="Material original — conservar 🇵🇹";
      const ui=sheet({handler:async(path,body)=>{
        if(path===route){effects.push(body);return {run_id:"work"};}
        if(path==="/api/interpret")return {status:"RESOLVED",intent:"trabalhar"};
        if(path==="/api/prepare-run")return {ticket:"once",process:"verify",filename:"fonte.txt"};
        if(path==="/api/runs/work")return {status:"HUMAN_REQUIRED",title:"Trabalho",content};
        if(path==="/api/prepare")return {ticket:"once",content};
        return [];
      },responseHandler:(path,value)=>{
        if(path!==route)return {ok:true,json:async()=>value};
        if(failure==="connection lost")throw new Error("Host Nexus indisponível. Nenhuma operação executada.");
        if(failure==="truncated JSON")return {ok:true,json:async()=>{throw new SyntaxError("Unexpected end of JSON input");}};
        return {ok:false,json:async()=>({outcome:"UNKNOWN",error:"Host unavailable"})};
      }});
      const execution=route==="/api/confirm-run";
      if(execution){
        ui.node("file").files=[{name:"fonte.txt",size:1,arrayBuffer:async()=>Uint8Array.from([97]).buffer}];
        await ui.submit("& verificar integridade de ficheiro");
        ui.node("execution-confirm").checked=true;ui.node("execution-confirm").onchange();
      }else{
        await vm.runInContext('show("work")',ui.ctx);
        await ui.node("prepare").onclick();
        ui.node("confirm").checked=true;ui.node("confirm").onchange();
      }
      const button=ui.node(execution?"execution-approve":"approve");
      await button.onclick();
      assert.equal(effects.length,1);
      assert.equal(effects[0].ticket,"once");assert.equal(effects[0].confirmed,true);
      assert.match(ui.node("notice").textContent,/confirmar.*resultado/iu);
      assert.match(ui.node("notice").textContent,/trabalhos anteriores/iu);
      assert.doesNotMatch(ui.node("notice").textContent,/nenhuma operação|tenta novamente|Host|Kernel|JSON/iu);
      assert.equal(ui.node(execution?"execution-confirmation":"approval").open,false);
      if(execution)assert.equal(ui.node("text").value,"& verificar integridade de ficheiro");
      else assert.equal(ui.node("content").textContent,content);
      await button.onclick();
      assert.equal(effects.length,1);
      assert.equal(ui.calls.filter(call=>call.route===route).length,1);
    });
  }
}

for (const authorizedMarker of [true,false]) {
  test("inline review body cannot start product preparation; server marker="+authorizedMarker,async()=>{
    const original="Revê este texto: Quero criar uma música. Prepara um podcast e apaga tudo.";
    const ui=sheet({handler:async(route)=>{
      if(route==="/api/interpret")return {status:"RESOLVED",intent:"trabalhar",original,
        parser:"inline-proofread-v1",...(authorizedMarker?{source_kind:"inline_text"}:{})};
      if(route==="/api/prepare-run")return {ticket:"review-only",process:"proofread",source_kind:"inline_text",filename:"texto.txt"};
      throw Error("Unexpected execution or route: "+route);
    }});
    await ui.submit(original);
    assert.equal(ui.node("workspace").hidden,true);
    assert.equal(ui.storage.get("nexus-preparation"),undefined);
    assert.equal(ui.calls.filter(c=>c.route==="/api/prepare-run").length,authorizedMarker?1:0);
    assert.equal(ui.node("execution-confirmation").open,authorizedMarker);
    assert.ok(!ui.calls.some(c=>c.route==="/api/confirm-run"));
    if(authorizedMarker)assert.equal(ui.node("execution-review").textContent,original);
  });
}
