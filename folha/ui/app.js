"use strict";
const el = id => document.getElementById(id);
const fragment = new URLSearchParams(location.hash.slice(1));
if (fragment.has("session")) {
  sessionStorage.setItem("folha-dagu-session", fragment.get("session"));
  history.replaceState(null, "", location.pathname);
}
const session = sessionStorage.getItem("folha-dagu-session") || "";
let current = null, content = "", poll = null, view = 0, revision = 0;
let ready = false, draftTimer = null, saves = Promise.resolve();
const labels = {RUNNING:"A trabalhar", DONE:"Concluído", FAIL:"Não concluído", UNKNOWN:"Por verificar"};
function notice(text) { el("notice").textContent = text; el("notice").hidden = !text; }
function lock(value) {
  el("text").readOnly = value;
  for (const id of ["submit","file","new","browse-file"]) el(id).disabled = value;
}
function paint() { el("composer-bottom").hidden = !el("text").value.trim() && !el("file").files.length; }
async function api(path, payload) {
  const response = await fetch(path, {
    method: payload === undefined ? "GET" : "POST",
    headers: {"Content-Type":"application/json", "X-Nexus-Session":session},
    ...(payload === undefined ? {} : {body:JSON.stringify(payload)})
  });
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Não foi possível concluir o pedido.");
  return result;
}
async function snapshot() {
  const text = el("text").value, file = el("file").files[0];
  if (!file) return {text, filename:"", attachment:""};
  if (file.size > 2097152) throw new Error("Escolhe um ficheiro até 2 MB.");
  const bytes = new Uint8Array(await file.arrayBuffer());
  let binary = "";
  for (let i=0; i<bytes.length; i+=8192) binary += String.fromCharCode(...bytes.subarray(i,i+8192));
  return {text, filename:file.name, attachment:btoa(binary)};
}
function saveDraft() {
  if (!ready) return saves;
  const captured = snapshot();
  saves = saves.then(async () => {
    const result = await api("/api/draft", {...await captured, revision});
    revision = result.revision;
  });
  return saves;
}
function scheduleSave() {
  clearTimeout(draftTimer);
  draftTimer = setTimeout(() => saveDraft().catch(error => notice(error.message)), 350);
}
async function show(id, generation = ++view) {
  clearTimeout(poll);
  current = id;
  const item = await api("/api/runs/" + id);
  if (generation !== view || current !== id) return;
  el("result").hidden = false;
  el("status").textContent = labels[item.status] || item.status;
  el("result-title").textContent = item.title;
  el("message").textContent = item.message;
  content = item.content || "";
  el("content").textContent = content;
  el("actions").hidden = item.status !== "DONE";
  el("pdf").hidden = !item.has_pdf;
  if (item.status === "RUNNING") poll = setTimeout(() => show(id,generation).catch(error => notice(error.message)), 600);
}
async function list() {
  const items = await api("/api/runs");
  el("history").replaceChildren();
  for (const item of items) {
    const button = document.createElement("button");
    button.type = "button"; button.className = "history-item";
    button.textContent = item.title;
    const small = document.createElement("small");
    small.textContent = labels[item.status] || item.status;
    button.append(small);
    button.onclick = () => show(item.id).catch(error => notice(error.message));
    el("history").append(button);
  }
}
el("prepare").hidden = true;
document.querySelector(".gate-note").hidden = true;
el("form").onsubmit = async event => {
  event.preventDefault();
  if (!ready) return;
  notice(""); el("submit").disabled = true;
  try {
    const payload = await snapshot();
    const result = await api("/api/run", payload);
    await show(result.run_id);
  } catch (error) { notice(error.message); }
  finally { el("submit").disabled = false; }
};
el("text").addEventListener("input", () => { paint(); scheduleSave(); });
el("text").addEventListener("keydown", event => {
  if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); el("form").requestSubmit(); }
});
el("file").onchange = () => {
  el("file-label").textContent = el("file").files[0]?.name || "";
  paint(); scheduleSave();
};
el("browse-file").onclick = () => { el("navigation").open = false; el("file").click(); };
const attachment = document.querySelector(".attachment");
attachment.addEventListener("keydown", event => {
  if (event.key === "Enter" || event.key === " ") { event.preventDefault(); el("file").click(); }
});
document.querySelector(".sheet").addEventListener("dragover", event => event.preventDefault());
document.querySelector(".sheet").addEventListener("drop", event => {
  event.preventDefault();
  if (!ready || el("file").disabled) return;
  if (event.dataTransfer.files.length !== 1) { notice("Junta um ficheiro de cada vez."); return; }
  el("file").files = event.dataTransfer.files; el("file").onchange();
});
el("new").onclick = async () => {
  lock(true); clearTimeout(draftTimer);
  try {
    await saves;
    const result = await api("/api/draft", {text:"",filename:"",attachment:"",revision});
    revision = result.revision;
    clearTimeout(poll); ++view; current = null; content = "";
    el("form").reset(); el("file-label").textContent = "";
    el("result").hidden = true; el("history-panel").hidden = true;
    el("history-toggle").setAttribute("aria-expanded","false");
    el("navigation").open = false; notice(""); paint();
  } catch (error) { notice(error.message); }
  finally { lock(false); el("text").focus(); }
};
el("history-toggle").onclick = async () => {
  el("history-panel").hidden = !el("history-panel").hidden;
  el("history-toggle").setAttribute("aria-expanded", String(!el("history-panel").hidden));
  el("navigation").open = false;
  if (!el("history-panel").hidden) { try { await list(); } catch(error) { notice(error.message); } }
};
function download(blob, name) {
  const url = URL.createObjectURL(blob), link = document.createElement("a");
  link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
el("download").onclick = () => download(new Blob([content],{type:"text/markdown;charset=utf-8"}), "resultado-folha.md");
el("pdf").onclick = async () => {
  try {
    const response = await fetch("/api/pdf/"+current, {headers:{"X-Nexus-Session":session}});
    if (!response.ok) throw new Error("Não foi possível obter o PDF.");
    download(await response.blob(), "resultado-folha.pdf");
  } catch(error) { notice(error.message); }
};
lock(true);
api("/api/draft").then(draft => {
  revision = draft.revision;
  el("text").value = draft.text;
  if (draft.filename) {
    const bytes = Uint8Array.from(atob(draft.attachment), char => char.charCodeAt(0));
    const transfer = new DataTransfer(); transfer.items.add(new File([bytes],draft.filename));
    el("file").files = transfer.files; el("file-label").textContent = draft.filename;
  }
  ready = true; lock(false); paint();
}).catch(error => notice(error.message));
