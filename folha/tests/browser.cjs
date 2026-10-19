const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const path = require('node:path');

(async () => {
  const data = process.argv[2];
  const launch = (await fs.readFile(path.join(data,'launch-url.txt'),'utf8')).trim();
  const browser = await chromium.launch({channel:'msedge',headless:true});
  try {
    const page = await browser.newPage({viewport:{width:1280,height:900},acceptDownloads:true});
    const errors = [];
    page.on('pageerror',error => errors.push(error.message));
    await page.goto(launch);
    await page.waitForFunction(() => !document.getElementById('text').readOnly);
    await page.locator('#navigation summary').click();
    await page.locator('#new').click();
    await page.waitForFunction(() => !document.getElementById('text').readOnly && document.getElementById('text').value==='');
    assert.equal(await page.title(),'Folha Nexus');
    assert.equal(await page.locator('#page-title').textContent(),'Folha');
    const message = 'Crónica de teste: música, coração e memória.';
    await page.locator('#text').fill('guardar texto: '+message);
    const submitted = page.waitForResponse(r => r.url().endsWith('/api/run') && r.request().method()==='POST');
    await page.locator('#submit').click();
    assert.equal((await submitted).status(),202);
    await page.waitForFunction(expected => document.getElementById('status').textContent==='Concluído' && document.getElementById('content').textContent===expected,message,{timeout:30000});
    assert.equal(await page.locator('dialog[open]').count(),0);
    assert.equal(await page.locator('#prepare').isVisible(),false);
    console.log('PASS: existing Folha UI submits to Dagu and receives literal text, without approval dialogs.');

    await page.locator('#text').fill('pesquisa na biblioteca: coração memória');
    const searching = page.waitForResponse(r => r.url().endsWith('/api/run') && r.request().method()==='POST');
    await page.locator('#submit').click();
    assert.equal((await searching).status(),202);
    await page.waitForFunction(expected => document.getElementById('status').textContent==='Concluído' && document.getElementById('result-title').textContent==='Pesquisa na biblioteca' && document.getElementById('content').textContent.includes(expected),message,{timeout:30000});
    console.log('PASS: Folha retrieves full saved text through the library index and Dagu.');

    const rtf = Buffer.from('{\\rtf1\\ansi Teste visual da Folha com PDF.}','ascii');
    await page.locator('#text').fill('converter para pdf');
    await page.locator('#file').setInputFiles({name:'folha.rtf',mimeType:'application/rtf',buffer:rtf});
    const conversion = page.waitForResponse(r => r.url().endsWith('/api/run') && r.request().method()==='POST');
    await page.locator('#submit').click();
    assert.equal((await conversion).status(),202);
    await page.waitForFunction(() => document.getElementById('status').textContent==='Concluído' && document.getElementById('result-title').textContent==='Converter para PDF',null,{timeout:60000});
    const downloading = page.waitForEvent('download');
    await page.locator('#pdf').click();
    const download = await downloading;
    const pdf = await fs.readFile(await download.path());
    assert.equal(pdf.subarray(0,5).toString(),'%PDF-');
    assert.equal(await page.locator('dialog[open]').count(),0);
    console.log('PASS: attachment → PowerShell → YAML → Dagu → LibreOffice → PDF downloaded through Folha.');

    const draftSaved = page.waitForResponse(r => r.url().endsWith('/api/draft') && r.request().method()==='POST');
    await page.locator('#text').fill('Rascunho conservado: ação e memória.');
    assert.equal((await draftSaved).status(),200);
    await page.reload();
    await page.waitForFunction(() => !document.getElementById('text').readOnly);
    assert.equal(await page.locator('#text').inputValue(),'Rascunho conservado: ação e memória.');
    assert.equal(await page.locator('#file-label').textContent(),'folha.rtf');
    assert.deepEqual(errors,[]);
    await page.screenshot({path:path.join(data,'folha-browser.png'),fullPage:true});
    console.log('PASS: text and attachment restored after reload; no browser JavaScript errors.');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
