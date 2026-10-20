"use strict";
// Real Chrome over HTTP from the original Python app in the CI workspace.
// Temporary test Store; preparation must make zero API/tool/approval calls.
const {chromium}=require("playwright");
const fs=require("node:fs/promises"),path=require("node:path"),assert=require("node:assert/strict");
const os=require("node:os"),net=require("node:net"),{spawn}=require("node:child_process");
(async()=>{
  const reservation=net.createServer();
  await new Promise(resolve=>reservation.listen(0,"127.0.0.1",resolve));
  const port=reservation.address().port;
  await new Promise(resolve=>reservation.close(resolve));
  const data=await fs.mkdtemp(path.join(os.tmpdir(),"nexus-folha-browser-"));
  const backend=spawn(process.env.NEXUS_TEST_PYTHON || "python",
    ["-m","nexus.app","--data",path.join(data,"memory"),"--port",String(port),"--no-browser"],
    {cwd:path.resolve(__dirname,"../.."),stdio:["ignore","pipe","pipe"]});
  const diagnostics=[];
  backend.stderr.on("data",value=>diagnostics.push(value.toString()));
  backend.on("error",error=>diagnostics.push(error.message));
  const base="http://127.0.0.1:"+port;
  let browser;
  try {
    let ready=false;
    for(let attempt=0;attempt<100;attempt++) {
      if(backend.exitCode!==null)throw new Error("Python app failed: "+diagnostics.join(""));
      try { if((await fetch(base)).ok){ready=true;break;} }catch(_error){}
      await new Promise(resolve=>setTimeout(resolve,100));
    }
    assert.ok(ready,"Python Folha did not start: "+diagnostics.join(""));
    browser=await chromium.launch({channel:"chrome",headless:true});
    const page=await browser.newPage({viewport:{width:1280,height:960},locale:"pt-PT"});
    const errors=[],apiCalls=[];
    page.on("pageerror",e=>errors.push(e.message));
    page.on("request",r=>{if(new URL(r.url()).pathname.startsWith("/api/"))apiCalls.push(r.url());});
    const images=path.resolve("folha-browser-evidence");
    await fs.mkdir(images,{recursive:true});
    await page.goto(base);
    assert.equal(await page.locator("#text").inputValue(),"");
    assert.equal(await page.locator("#workspace").isVisible(),false);
    assert.equal(await page.locator("#history-panel").isVisible(),false);
    assert.equal(await page.locator("#composer-bottom").isVisible(),false);
    assert.equal(await page.locator("button:visible").count(),0);
    assert.equal(apiCalls.length,0);
    await page.screenshot({path:path.join(images,"folha-vazia.png"),fullPage:true});
    for(const [product,request] of [
      ["text","Faz-me um artigo sobre o turismo no Alentejo."],
      ["podcast","Quero um podcast sobre o Alentejo."],
      ["music","Cria uma música: Alma Lusitana."],
      ["short","Prepara uma curta sobre Lisboa."]
    ]) {
      await page.reload();
      await page.locator("#text").fill(request);await page.locator("#submit").click();
      assert.equal(await page.locator("#product").inputValue(),product);
      assert.equal(await page.locator("#stage-title").textContent(),"Ideia");
      assert.equal(await page.locator(".stages button").count(),6);
      assert.equal(apiCalls.length,0);
    }
    await page.locator("#brief-objective").fill("Contar uma história com sentido.");
    await page.locator("#brief-audience").fill("Público português.");
    await page.locator("#brief-format").fill("MP4, horizontal, legendado.");
    await page.locator("#stage-notes").fill("Ideia humana — conservar.");
    await page.locator("#submit").click();
    assert.equal(await page.locator("#brief-objective").inputValue(),"Contar uma história com sentido.");
    assert.equal(await page.locator("#stage-notes").inputValue(),"Ideia humana — conservar.");
    await page.screenshot({path:path.join(images,"folha-preparacao.png"),fullPage:true});
    await page.locator("#stage-reviewed").check();await page.locator("#stage-next").click();
    assert.equal(await page.locator("#stage-title").textContent(),"Pesquisa");
    for(let i=1;i<6;i++) {
      await page.locator("#stage-notes").fill("Material e decisões da etapa "+i+". Fontes a rever: livro e notas próprias.");
      await page.locator("#stage-reviewed").check();
      if(i<5)await page.locator("#stage-next").click();
    }
    assert.equal(await page.locator("#workspace-status").textContent(),"Preparação revista");
    await page.locator("#submit").click();
    assert.equal(await page.locator("#workspace-status").textContent(),"Preparação revista");
    const [download]=await Promise.all([page.waitForEvent("download"),page.locator("#save-preparation").click()]);
    const exported=JSON.parse(await fs.readFile(await download.path(),"utf8"));
    assert.equal(exported.product,"short");assert.equal(exported.produced,false);
    assert.ok(exported.stages.every(s=>s.reviewed));assert.equal(apiCalls.length,0);
    await page.locator("#navigation summary").click();await page.locator("#new").click();
    assert.equal(await page.locator("#text").inputValue(),"");
    assert.equal(await page.locator("#workspace").isVisible(),false);
    await page.locator("#navigation summary").click();await page.locator("#resume").click();
    assert.equal(await page.locator("#text").inputValue(),"Prepara uma curta sobre Lisboa.");
    assert.equal(await page.locator("#execution-confirmation").isVisible(),false);
    await page.setViewportSize({width:390,height:844});await page.reload();
    assert.equal(await page.locator("button:visible").count(),0);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    await page.locator("#text").fill("Cria uma música sobre a cidade.");await page.locator("#submit").click();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
    await page.screenshot({path:path.join(images,"folha-mobile.png"),fullPage:true});
    assert.deepEqual(errors,[]);
    console.log(JSON.stringify({result:"PASS",initialVisibleButtons:0,productBriefs:4,steps:6,
      desktopAndMobile:true,draftExport:true,restore:true,repeatedContinuePreservesWork:true,
      hostCallsDuringPreparation:apiCalls.length,pageErrors:errors.length}));
  } finally {
    if(browser)await browser.close();
    if(backend.pid && backend.exitCode===null){backend.kill();await new Promise(resolve=>backend.once("exit",resolve));}
    await fs.rm(data,{recursive:true,force:true});
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
