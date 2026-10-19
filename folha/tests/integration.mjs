import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';

const data = process.argv[2];
if (!data) throw new Error('Pass the isolated test data directory.');
const launch = new URL((await fs.readFile(path.join(data,'launch-url.txt'),'utf8')).trim());
const base = launch.origin;
const session = new URLSearchParams(launch.hash.slice(1)).get('session');
async function request(route, payload, headers={}) {
  return fetch(base+route, {
    method: payload === undefined ? 'GET' : 'POST',
    headers: {'Content-Type':'application/json','X-Nexus-Session':session,...headers},
    ...(payload === undefined ? {} : {body:JSON.stringify(payload)})
  });
}
async function run(payload) {
  const response = await request('/api/run',payload);
  const result = await response.json();
  assert.equal(response.status,202,JSON.stringify(result));
  const end = Date.now()+60000;
  while (Date.now()<end) {
    const response = await request('/api/runs/'+result.run_id);
    const state = await response.json();
    if (state.status !== 'RUNNING') {
      assert.equal(state.status,'DONE',JSON.stringify(state));
      return state;
    }
    await new Promise(resolve=>setTimeout(resolve,300));
  }
  throw new Error('Workflow did not finish within 60 seconds.');
}
assert.equal((await request('/health')).status,200);
assert.equal((await request('/api/runs',undefined,{'X-Nexus-Session':'wrong'})).status,403);
assert.equal((await request('/api/run',{text:'guardar texto: nope',filename:'',attachment:''},{Origin:'https://example.com'})).status,403);
assert.equal((await request('/api/run',{text:'não converter para pdf',filename:'x.txt',attachment:'eA=='})).status,400);
assert.equal((await request('/api/run',{text:'converter para pdf',filename:'',attachment:''})).status,400);
console.log('PASS: local session, origin and deterministic routing checks.');

const literal = 'Crónica: ação, música e coração.\n${env.HOME}\n$(throw "do not execute")\nname: injected\nsteps: [bad]';
const saved = await run({text:'guardar texto: '+literal,filename:'',attachment:''});
assert.equal(saved.content,literal);
assert.equal(await fs.readFile(path.join(data,'runs',saved.id,'texto.md'),'utf8'),literal);
console.log('PASS: UTF-8 text saved literally; YAML and shell-looking text stay data.');
assert.equal(await fs.readFile(path.join(data,'biblioteca','wikis',saved.id+'.md'),'utf8'),literal);
const retrieved = await run({text:'procurar na biblioteca: coração',filename:'',attachment:''});
assert.ok(retrieved.content.includes(literal),retrieved.content);
assert.equal((await fs.readdir(path.join(data,'biblioteca','wikis'))).includes(retrieved.id+'.md'),false);
console.log('PASS: saved text is archived and found through SQLite FTS5 and Dagu, with full text preserved.');

const libraryFile = path.join(data,'biblioteca','fontes','teste-indexacao.txt');
const marker = 'catalogoteste'+Date.now();
await fs.writeFile(libraryFile,marker+' música d\'água\n.exit\nDROP TABLE biblioteca_fts;\n$(not-code)\n','utf8');
const fresh = await run({text:'pesquisa na biblioteca: '+marker+' musica',filename:'',attachment:''});
assert.ok(fresh.content.includes("música d'água\n.exit\nDROP TABLE biblioteca_fts;"),fresh.content);
await fs.writeFile(libraryFile,marker+' versão revista orquestra','utf8');
const changed = await run({text:'pesquisa na biblioteca: '+marker+' orquestra',filename:'',attachment:''});
assert.ok(changed.content.includes('versão revista orquestra'),changed.content);
assert.ok(!changed.content.includes('DROP TABLE'),changed.content);
await fs.unlink(libraryFile);
const removed = await run({text:'pesquisa na biblioteca: '+marker,filename:'',attachment:''});
assert.ok(removed.content.includes('Documentos encontrados: 0'),removed.content);
console.log('PASS: both-folder indexing reconciles added, edited and removed files; SQL-like input stays data.');

const input = Buffer.from('Documento original: coração.\n','utf8');
const originalHash = createHash('sha256').update(input).digest('hex');
const verified = await run({text:'verificar integridade de ficheiro',filename:'original.txt',attachment:input.toString('base64')});
assert.ok(verified.content.includes(originalHash),verified.content);
assert.deepEqual(await fs.readFile(path.join(data,'runs',verified.id,'entrada.txt')),input);
console.log('PASS: file hash agrees with independent SHA256; original bytes preserved.');

const rtf = Buffer.from('{\\rtf1\\ansi Teste Folha Dagu. Documento convertido pelo LibreOffice.}','ascii');
const converted = await run({text:'Quero converter este documento para PDF',filename:'documento.rtf',attachment:rtf.toString('base64')});
const pdfResponse = await request('/api/pdf/'+converted.id);
assert.equal(pdfResponse.status,200);
const pdf = Buffer.from(await pdfResponse.arrayBuffer());
assert.equal(pdf.subarray(0,5).toString(),'%PDF-');
assert.ok(converted.content.includes(createHash('sha256').update(pdf).digest('hex')));
assert.deepEqual(await fs.readFile(path.join(data,'runs',converted.id,'entrada.rtf')),rtf);
console.log('PASS: real LibreOffice conversion, PDF download, checksum and original preservation.');
console.log(JSON.stringify({verified:verified.id,converted:converted.id,pdfBytes:pdf.length}));
