"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const code = fs.readFileSync(path.join(__dirname, "..", "ui", "app.js"), "utf8");
const nodes = new Map();
const apiCalls = [];
function node(id) {
  if (!nodes.has(id)) nodes.set(id, {
    value: "", files: [], textContent: "", hidden: false, disabled: false,
    checked: false, open: false, style: {},
    addEventListener(name, callback) { this["on" + name] = callback; },
    append() {}, replaceChildren() {}, reset() {}, focus() {}, close() {this.open=false;},
    showModal() {this.open=true;}
  });
  return nodes.get(id);
}
const ctx = {
  document: { getElementById: node, querySelector() {return null;} },
  location: { hash: "" },
  history: { replaceState() {} },
  sessionStorage: { getItem() {return "python-token";}, setItem() {} },
  URLSearchParams,
  Uint8Array, btoa: x => Buffer.from(x, "binary").toString("base64"),
  clearTimeout() {}, setTimeout() {return 1;},
  fetch: async (path, options) => {
    const request = {path, method: options?.method, body:options?.body?JSON.parse(options.body):null};
    apiCalls.push(request);
    if (path === "/api/runs") return {ok:true,json:async()=>[]};
    if (path === "/api/search") return {ok:true,json:async()=>({
      scope:request.body.include_creative ? "canonical+creative" : "canonical",
      results:[{run_id:"a".repeat(32),authority:request.body.include_creative?"creative":"canonical",
                process_id:"verify",snippet:"teste FTS5 local"}],
    })};
    if (path === "/api/interpret") return {ok:true,json:async()=>({
      status:"RESOLVED", intent:"perguntar",original:request.body.text,
      execution:"NOT_AUTHORIZED",
    })};
    throw new Error("Unexpected request: "+path);
  }
};
vm.runInNewContext(code,ctx,{filename:"app.js"});

async function submit(message) {
  node("text").value=message;
  if (node("text").oninput) node("text").oninput();
  await node("form").onsubmit({preventDefault() {}});
}
(async()=>{
  await submit("?? pesquisar nexo");
  assert.equal(apiCalls.filter(x=>x.path==="/api/search").length,1);
  assert.equal(apiCalls.at(-1).body.include_creative,false);
  assert.equal(apiCalls.at(-1).body.query,"nexo");
  assert.match(node("content").textContent,/teste FTS5 local/);
  assert.equal(node("actions").hidden,true);
  await submit("?? pesquisar rascunhos evidência");
  assert.equal(apiCalls.at(-1).body.include_creative,true);
  assert.equal(apiCalls.at(-1).body.query,"evidência");
  assert.equal(node("result-title").textContent,"Trabalhos aprovados e rascunhos");
  assert.doesNotMatch(node("content").textContent,/canonical|creative|verify|[a-f0-9]{32}/);
  assert.match(node("content").textContent,/Rascunho · por rever/);
  await submit("?? perguntar algo geral");
  assert.equal(apiCalls.at(-1).path,"/api/interpret");
  assert.equal(apiCalls.some(x=>/prepare-run|confirm-run|\/api\/approve/.test(x.path)),false);
  assert.equal(apiCalls.every(x=>x.path!=="/api/search"||x.method==="POST"),true);
  console.log("PASS Folha FTS5 read-only command, canonical default, explicit Creative");
})().catch(e=>{console.error(e);process.exitCode=1;});
