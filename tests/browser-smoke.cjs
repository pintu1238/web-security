/* Run with Node and Playwright installed; all mutations use a disposable database. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn, spawnSync } = require('node:child_process');

const root = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'nitishield-browser-'));
const output = path.join(root, 'test-results');
const port = process.env.TEST_PORT || '5056';
const base = `http://127.0.0.1:${port}`;
const python = process.env.PYTHON || path.join(root, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
fs.mkdirSync(path.join(temporary, 'legal_documents'));
fs.mkdirSync(output, {recursive:true});
for (const file of fs.readdirSync(path.join(root,'Backend','legal_documents')).filter(f=>f.endsWith('.pdf'))) {
  fs.copyFileSync(path.join(root,'Backend','legal_documents',file),path.join(temporary,'legal_documents',file));
}
const server = spawn(python, [path.join(__dirname,'serve_test_app.py')], {cwd:root, env:{...process.env,NITISHIELD_TEST_DIR:temporary,TEST_PORT:port}, windowsHide:true, stdio:['ignore','pipe','pipe']});
let serverLog='';
server.stdout.on('data',d=>serverLog+=d);server.stderr.on('data',d=>serverLog+=d);
let browser;
const checks=[];
function done(name){checks.push(name);process.stdout.write(`PASS ${name}\n`);}
async function download(page,link,expected){
  const event=page.waitForEvent('download');await link.click();const file=await event;
  const filePath=await file.path();const body=fs.readFileSync(filePath);
  if(expected)assert.ok(body.toString().includes(expected));
  return body;
}
async function main(){
  let ready=false;
  for(let n=0;n<100;n++){
    if(server.exitCode!==null)throw new Error(`Test server exited: ${serverLog}`);
    try{const response=await fetch(`${base}/api/health`);if(response.ok){ready=true;break;}}catch{}
    await new Promise(resolve=>setTimeout(resolve,200));
  }
  assert.ok(ready,`Test server did not start: ${serverLog}`);
  const executable=process.env.BROWSER_EXECUTABLE || (process.platform==='win32' ? 'C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe' : undefined);
  browser=await chromium.launch({headless:process.env.HEADLESS==='1',...(executable?{executablePath:executable}:{})});
  const context=await browser.newContext({viewport:{width:1440,height:1120},acceptDownloads:true});
  const page=await context.newPage();
  const jsErrors=[];page.on('pageerror',e=>jsErrors.push(e.message));
  page.on('dialog',async d=>{jsErrors.push(`Unexpected dialog: ${d.message()}`);await d.dismiss();});
  await page.goto(base);
  await page.getByRole('heading',{name:'Overview',exact:true}).waitFor();
  assert.equal(await page.locator('#connection-dot').count(),0);
  assert.equal(await page.getByText('Workspace connected',{exact:true}).count(),0);
  await page.getByRole('heading',{name:'Overview',exact:true}).waitFor();
  assert.equal(await page.locator('.stat-card').count(),4);
  await page.screenshot({path:path.join(output,'dashboard-desktop.png'),fullPage:true,animations:'disabled'});
  done('Dashboard loads from real backend with an unassessed baseline');

  await page.getByRole('button',{name:'Search anything...'}).click();
  await page.getByRole('textbox',{name:'Search workspace'}).fill('compliance');
  await page.locator('.search-result').filter({hasText:'Legal compliance'}).click();
  await page.getByRole('heading',{name:'A little progress, every day.'}).waitFor();
  done('Global search and page navigation');

  const title='Review vendor access <b>today</b>';
  await page.getByRole('button',{name:'Add task',exact:true}).click();
  await page.getByLabel('What needs doing?').fill(title);
  await page.getByLabel('Category',{exact:true}).selectOption('Security');
  await page.getByLabel('Priority',{exact:true}).selectOption('high');
  await page.getByLabel('Due date (optional)').fill('2030-09-14');
  await page.locator('#task-form').getByRole('button',{name:'Add task'}).click();
  await page.getByText(title,{exact:true}).waitFor();
  await page.reload();await page.getByText(title,{exact:true}).waitFor();
  assert.equal(await page.locator('td b').filter({hasText:'today'}).count(),0);
  await page.getByRole('button',{name:`Complete ${title}`,exact:true}).click();
  await page.getByRole('button',{name:`Reopen ${title}`,exact:true}).waitFor();
  await page.getByRole('button',{name:`Reopen ${title}`,exact:true}).click();
  await page.getByRole('button',{name:`Complete ${title}`,exact:true}).waitFor();
  await page.locator('#task-search').fill('no task matches this');
  await page.getByRole('heading',{name:'Nothing here just yet'}).waitFor();
  await page.locator('#task-search').fill('');
  await page.getByRole('button',{name:`Delete ${title}`,exact:true}).click();
  await page.getByRole('button',{name:'Remove task',exact:true}).click();
  await page.getByText(title,{exact:true}).waitFor({state:'hidden'});
  done('Task creation, persistence, escaping, completion, reopening, filtering and deletion');

  await page.goto(`${base}/#settings`);await page.getByLabel('Business name',{exact:true}).waitFor();
  await page.getByLabel('Business name',{exact:true}).fill('Himalayan Digital');
  await page.getByLabel('Owner / representative',{exact:true}).fill('Asha Sharma');
  await page.getByLabel('Business email',{exact:true}).fill('asha@example.com');
  await page.getByLabel('Website',{exact:true}).fill('https://example.com');
  await page.getByLabel('Business address',{exact:true}).fill('Lalitpur, Bagmati, Nepal');
  await page.locator('#notifications').uncheck();
  await page.getByRole('button',{name:'Save changes',exact:true}).click();
  await page.getByText('Business profile saved.',{exact:true}).waitFor();
  await page.reload();await page.getByLabel('Business name',{exact:true}).waitFor();
  assert.equal(await page.getByLabel('Business name',{exact:true}).inputValue(),'Himalayan Digital');
  assert.equal(await page.getByLabel('Business email',{exact:true}).inputValue(),'asha@example.com');
  assert.equal(await page.locator('#notifications').isChecked(),false);
  assert.equal(await page.locator('#notification-dot').isVisible(),false);
  await page.getByRole('button',{name:'View notifications'}).click();
  await page.getByRole('heading',{name:'Reminders are turned off'}).waitFor();
  await page.getByRole('button',{name:'Close dialog'}).click();
  const exportBody=await download(page,page.getByRole('link',{name:'Export data'}),'Himalayan Digital');
  assert.ok(JSON.parse(exportBody).tasks.length>=1);
  done('Settings persist, notification preference works, workspace export downloads');

  await page.goto(`${base}/#documents`);
  for(const type of ['privacy_policy','employment_agreement','nda','incident_response']){
    await page.locator(`[data-template="${type}"]`).click();
    await page.locator('#document-form').getByRole('button',{name:'Create draft',exact:true}).click();
    await page.locator('#document-preview').waitFor();
    assert.ok((await page.locator('#document-preview').innerText()).includes('Himalayan Digital'));
    if(type==='privacy_policy'){
      // Plain-HTTP network addresses do not expose the modern clipboard API.
      await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{value:undefined,configurable:true}));
      await page.getByRole('button',{name:'Copy text',exact:true}).click();
      await page.getByText('Draft copied to clipboard.',{exact:true}).waitFor();
    }
    const contents=await download(page,page.getByRole('link',{name:'Download draft'}),'Himalayan Digital');
    assert.ok(contents.length>300);
    await page.getByRole('button',{name:'Close dialog'}).click();
  }
  assert.equal(await page.locator('tbody tr').count(),4);
  const firstDocumentRow=page.locator('tbody tr').first();
  await firstDocumentRow.getByRole('button',{name:/Delete/}).click();
  await page.locator('#modal').getByRole('button',{name:'Delete draft',exact:true}).click();
  await page.getByText('Draft deleted.',{exact:true}).waitFor();
  assert.equal(await page.locator('tbody tr').count(),3);
  done('All four document templates generate, persist and download; saved drafts can be deleted after confirmation');

  await page.goto(`${base}/#knowledge`);await page.locator('.knowledge-card').first().waitFor();
  const source=await download(page,page.locator('.knowledge-card').first().getByRole('link',{name:'Open source'}));
  assert.equal(source.subarray(0,4).toString(),'%PDF');
  await page.locator('#knowledge-search').fill('not in the library');
  await page.getByRole('heading',{name:'No matching documents'}).waitFor();
  await page.locator('#knowledge-search').fill('');
  const fixturePath=path.join(temporary,'browser-upload.pdf');
  const fixture=spawn(python,['-c','import pymupdf,sys; d=pymupdf.open(); p=d.new_page(); p.insert_text((72,72),"Vendor security checklist. Review vendor access every month and revoke inactive accounts."); d.save(sys.argv[1]); d.close()',fixturePath],{windowsHide:true});
  await new Promise((resolve,reject)=>{fixture.on('error',reject);fixture.on('close',code=>code===0?resolve():reject(new Error('PDF fixture failed')));});
  await page.locator('#pdf-upload').setInputFiles(fixturePath);
  await page.getByText('PDF added to your knowledge base.',{exact:true}).waitFor();
  assert.ok(await page.locator('.knowledge-card').count()>=2);
  done('Source PDF download, library search and real PDF upload');

  await page.goto(`${base}/#assistant`);await page.locator('#chat-question').waitFor();
  await page.locator('#chat-question').fill('electronic records');
  await page.getByRole('button',{name:'Send question',exact:true}).click();
  await page.locator('.source-card').first().waitFor({timeout:30000});
  await page.locator('.source-card summary').first().click();
  assert.ok(await page.locator('.source-card').first().getByRole('link',{name:'Open source'}).getAttribute('href'));
  await page.reload();await page.locator('.source-card').first().waitFor();
  await page.getByRole('button',{name:'Clear history'}).click();
  await page.locator('#modal').getByRole('button',{name:'Clear history'}).click();
  await page.getByRole('heading',{name:'Let’s find a little clarity.'}).waitFor();
  done('Legal search returns actual citations, persists and clears history');

  await page.goto(`${base}/#knowledge`);await page.locator('.knowledge-card').first().waitFor();
  await page.locator('.knowledge-card').filter({hasText:'browser-upload'}).getByRole('button',{name:'Ask about it'}).click();
  await page.locator('#chat-document').waitFor();
  const selectedDocument=await page.locator('#chat-document').inputValue();
  assert.ok(selectedDocument);
  await page.waitForFunction(()=>document.querySelector('#chat-question')?.value==='Summarize this PDF in simple language.');
  const selectedRequest=page.waitForRequest(r=>r.url().endsWith('/api/search')&&r.method()==='POST');
  await page.getByRole('button',{name:'Send question',exact:true}).click();
  assert.equal((await selectedRequest).postDataJSON().document_id,selectedDocument);
  await page.locator('.source-card').first().waitFor({timeout:30000});
  assert.equal(await page.locator('.source-card').count(),1);
  assert.ok((await page.locator('.source-card').first().textContent()).includes('Review vendor access every month'));
  await page.getByRole('button',{name:'Clear history'}).click();
  await page.locator('#modal').getByRole('button',{name:'Clear history'}).click();
  await page.getByRole('heading',{name:'Let’s find a little clarity.'}).waitFor();
  await page.locator('#chat-document').selectOption('');
  done('Ask about an uploaded PDF selects it and scopes summary evidence to that PDF');

  for(const question of ['tell me about this website','how can you help me?']){
    await page.locator('#chat-question').fill(question);
    await page.getByRole('button',{name:'Send question',exact:true}).click();
    await page.waitForFunction(()=>document.querySelector('#chat-question')?.disabled===false);
    const answer=await page.locator('.message.assistant .message-body').last().textContent();
    assert.ok(answer.includes('NitiShield'));
    assert.ok(!answer.includes('could not find'));
  }
  assert.equal(await page.locator('.source-card').count(),0);
  done('Ordinary website and help questions answer without PDF sources');
  await page.getByLabel('Response language').selectOption('नेपाली');
  await page.locator('#chat-question').fill('How can you help me?');
  const languageRequest=page.waitForRequest(r=>r.url().endsWith('/api/search')&&r.method()==='POST');
  await page.getByRole('button',{name:'Send question',exact:true}).click();
  assert.equal((await languageRequest).postDataJSON().language,'नेपाली');
  await page.waitForFunction(()=>document.querySelector('#chat-question')?.disabled===false);
  assert.ok((await page.locator('.message.assistant .message-body').last().textContent()).includes('सहयोग'));
  await page.locator('#navigation').getByRole('link',{name:'Overview'}).click();
  await page.locator('#navigation').getByRole('link',{name:'Legal assistant'}).click();
  await page.getByLabel('Response language').waitFor();
  assert.equal(await page.getByLabel('Response language').inputValue(),'नेपाली');
  await page.getByLabel('Response language').selectOption('');
  done('Nepali selector reaches backend, returns Nepali help and survives page navigation');

  let releaseAnswer;
  let requestArrived;
  const answerGate=new Promise(resolve=>releaseAnswer=resolve);
  const requestGate=new Promise(resolve=>requestArrived=resolve);
  await page.route('**/api/search',async route=>{
    const response=await route.fetch();
    requestArrived();
    await answerGate;
    await route.fulfill({response});
  });
  await page.locator('#chat-question').fill('digital signatures');
  await page.getByRole('button',{name:'Send question'}).click();
  await requestGate;
  assert.equal(await page.getByRole('button',{name:'Clear history',exact:true}).isDisabled(),true);
  await page.locator('#navigation').getByRole('link',{name:'Overview'}).click();
  await page.locator('#navigation').getByRole('link',{name:'Legal assistant'}).click();
  await page.locator('#chat-question').waitFor();
  assert.equal(await page.locator('#chat-question').isDisabled(),true);
  releaseAnswer();
  await page.waitForFunction(()=>document.querySelector('#chat-question')?.disabled===false,{},{timeout:5000});
  assert.equal(await page.getByRole('button',{name:'Send question'}).isDisabled(),false);
  await page.unroute('**/api/search');
  done('Returning during a pending answer recovers active chat controls');

  await page.goto(`${base}/#scanner`);await page.getByLabel('Website URL').waitFor();
  await page.getByRole('button',{name:'How it works'}).click();
  await page.getByRole('heading',{name:'A focused website health check'}).waitFor();
  await page.getByRole('button',{name:'Close dialog'}).click();
  await page.getByLabel('Website URL').fill('http://127.0.0.1:5000');
  await page.getByLabel('I own this website or have permission to assess it.').check();
  await page.getByRole('button',{name:'Run assessment',exact:true}).click();
  await page.locator('.toast.error').filter({hasText:/public|internal/i}).waitFor();
  await page.getByRole('heading',{name:'Your first assessment is waiting'}).waitFor();
  done('Assessment validation surfaces backend rejection without fake results');

  await page.getByLabel('Website URL').fill('https://browser-fixture.example');
  await page.getByRole('button',{name:'Run assessment',exact:true}).click();
  await page.getByRole('heading',{name:'Your security assessment'}).waitFor({timeout:30000});
  assert.equal(await page.locator('#modal .finding').count(),4);
  assert.equal(await page.locator('#modal .score-ring strong').innerText(),'33');
  await download(page,page.getByRole('link',{name:'Download report'}),'Security');
  await page.getByRole('button',{name:'Close dialog'}).click();
  await page.reload();await page.getByRole('button',{name:'View findings'}).waitFor();
  done('Assessment scoring, saved findings and report download with a controlled network fixture');

  await page.goto(`${base}/#dashboard`);await page.locator('.stat-card').first().waitFor();
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  await page.screenshot({path:path.join(output,'dashboard-mobile.png'),fullPage:true,animations:'disabled'});
  assert.ok(await page.locator('.right-column .card').first().evaluate(el=>el.getBoundingClientRect().width>345));
  await page.getByRole('button',{name:'Open navigation'}).click();
  await page.locator('#navigation').getByRole('link',{name:'Document studio'}).click();
  await page.getByRole('heading',{name:'Good paperwork. Less work.'}).waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
  done('Mobile dashboard, navigation and document layout have no page overflow');
  assert.deepEqual(jsErrors,[]);
  done('No browser JavaScript errors or injected dialogs');
  const persisted=spawnSync(python,['-c','import sqlite3,json,sys; c=sqlite3.connect(sys.argv[1]); print(json.dumps({t:c.execute("SELECT COUNT(*) FROM "+t).fetchone()[0] for t in ("tasks","scans","findings","generated_documents","conversations","knowledge_documents","activity")})); c.close()',path.join(temporary,'workspace.db')],{windowsHide:true,encoding:'utf8'});
  assert.equal(persisted.status,0,persisted.stderr);
  const database=JSON.parse(persisted.stdout);
  assert.equal(database.generated_documents,4);assert.equal(database.scans,1);assert.equal(database.findings,4);
  assert.ok(database.conversations>=1);assert.ok(database.knowledge_documents>=2);assert.ok(database.activity>=1);
  done('Browser actions independently verified in SQLite tables');
  fs.writeFileSync(path.join(output,'browser-smoke.json'),JSON.stringify({browser:executable,model:process.env.NITISHIELD_LIVE_AI==='1'?'live Ollama':'HTTP inference fixture',checks,passed:checks.length,database},null,2));
  process.stdout.write(`\n${checks.length} browser checks passed.\n`);
}
main().catch(error=>{process.stderr.write(`${error.stack}\n`);process.exitCode=1;}).finally(async()=>{
  if(browser)await browser.close();server.kill();
  await new Promise(resolve=>server.exitCode!==null?resolve():server.once('exit',resolve));
  const resolved=path.resolve(temporary);const tempBase=path.resolve(os.tmpdir())+path.sep;
  if(resolved.startsWith(tempBase)&&path.basename(resolved).startsWith('nitishield-browser-'))fs.rmSync(resolved,{recursive:true,force:true});
});
