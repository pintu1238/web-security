/* Cross-tab freshness and persisted data checks using the installed Brave. */
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const {spawn, spawnSync} = require('node:child_process');
const root = path.resolve(__dirname, '..');
const temporary = fs.mkdtempSync(path.join(os.tmpdir(), 'nitishield-integrity-'));
const python = process.env.PYTHON || path.join(root,'.venv','Scripts','python.exe');
const base = `http://127.0.0.1:${process.env.TEST_PORT || 5057}`;
const server = spawn(python,[path.join(__dirname,'serve_test_app.py')],{cwd:root,windowsHide:true,
  env:{...process.env,NITISHIELD_TEST_DIR:temporary,TEST_PORT:process.env.TEST_PORT || '5057'},stdio:['ignore','pipe','pipe']});
let log='',browser;
server.stdout.on('data',d=>log+=d);server.stderr.on('data',d=>log+=d);
const checks=[];
async function check(name,run){try{await run();checks.push({name,passed:true});console.log('PASS '+name);}catch(error){checks.push({name,passed:false,error:error.message});console.log('FAIL '+name+': '+error.message);}}
async function main(){
  for(let i=0;i<100;i++){try{if((await fetch(base+'/api/health')).ok)break;}catch{}if(server.exitCode!==null)throw Error(log);await new Promise(r=>setTimeout(r,200));}
  browser=await chromium.launch({executablePath:process.env.BROWSER_EXECUTABLE || 'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe',headless:process.env.HEADLESS==='1'});
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  const page=await context.newPage();page.setDefaultTimeout(5000);
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const second=await browser.newContext();
  const api=second.request;
  await page.goto(base);await page.locator('.stat-card').first().waitFor();
  await check('Opening reminders during initial loading still renders the dashboard',async()=>{
    let firstReady,secondReady,releaseFirst,releaseSecond,count=0;
    const first=new Promise(r=>firstReady=r),second=new Promise(r=>secondReady=r);
    const firstGate=new Promise(r=>releaseFirst=r),secondGate=new Promise(r=>releaseSecond=r);
    await page.route('**/api/dashboard',async route=>{
      const index=++count;const response=await route.fetch();
      if(index===1){firstReady();await firstGate;}
      if(index===2){secondReady();await secondGate;}
      await route.fulfill({response});
    });
    try{
      await page.reload({waitUntil:'domcontentloaded'});await first;
      await page.getByRole('button',{name:'View notifications'}).click();await second;
      const firstResponse=page.waitForResponse(r=>r.url().endsWith('/api/dashboard'));
      releaseFirst();await firstResponse;
      await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
      releaseSecond();
      await page.getByRole('heading',{name:'Your workspace reminders'}).waitFor();
      await page.getByRole('button',{name:'Close dialog'}).click();
      await page.locator('.stat-card').first().waitFor();
    }finally{releaseFirst();releaseSecond();await page.unroute('**/api/dashboard');}
  });
  await page.goto(base);await page.locator('.stat-card').first().waitFor();
  await check('Navigation reads tasks saved by another session',async()=>{
    await api.post(base+'/api/tasks',{data:{title:'Cross-tab vendor review',category:'Security',priority:'high'}});
    await page.locator('#navigation').getByRole('link',{name:'Legal compliance'}).click();
    await page.getByText('Cross-tab vendor review',{exact:true}).waitFor();
  });
  await check('Notifications read current database records',async()=>{
    await api.post(base+'/api/tasks',{data:{title:'New notification task',category:'Operations',priority:'medium'}});
    await page.getByRole('button',{name:'View notifications'}).click();
    await page.locator('#modal').getByText('New notification task',{exact:true}).waitFor();
  });
  if(await page.locator('#modal').isVisible())await page.getByRole('button',{name:'Close dialog'}).click();
  const pdf=path.join(temporary,'Supplier handbook.pdf');
  const fixture=spawnSync(python,['-c','import pymupdf,sys; d=pymupdf.open(); p=d.new_page(); p.insert_text((72,72),"Suppliers must review access each month."); d.save(sys.argv[1]); d.close()',pdf],{windowsHide:true});
  assert.equal(fixture.status,0);
  const uploaded=await api.post(base+'/api/knowledge',{multipart:{file:{name:'Supplier handbook.pdf',mimeType:'application/pdf',buffer:fs.readFileSync(pdf)}}});assert.equal(uploaded.status(),201);
  await check('Global search finds an uploaded PDF and filters the library',async()=>{
    await page.getByRole('button',{name:'Search anything...'}).click();
    await page.getByRole('textbox',{name:'Search workspace'}).fill('Supplier handbook');
    await page.locator('.search-result').filter({hasText:'Supplier handbook'}).click();
    await page.locator('.knowledge-card').filter({hasText:'Supplier handbook'}).waitFor();
  });
  if(await page.locator('#modal').isVisible())await page.getByRole('button',{name:'Close dialog'}).click();
  await check('Global task search escapes a previously selected completed filter',async()=>{
    await page.goto(base+'/#compliance');await page.getByRole('button',{name:/^Completed/}).click();
    await page.getByRole('button',{name:'Search anything...'}).click();
    await page.getByRole('textbox',{name:'Search workspace'}).fill('Cross-tab vendor review');
    await page.locator('.search-result').filter({hasText:'Cross-tab vendor review'}).click();
    await page.getByRole('button',{name:'Complete Cross-tab vendor review',exact:true}).waitFor();
  });
  if(await page.locator('#modal').isVisible())await page.getByRole('button',{name:'Close dialog'}).click();
  await check('Persisted draft can be previewed again after reload',async()=>{
    await api.post(base+'/api/documents',{data:{type:'nda',business_name:'Persisted Company',owner:'Test Owner',address:'Test Address',effective_date:'2026-09-14'}});
    await page.goto(base+'/#documents');await page.reload();
    await page.getByRole('button',{name:'View draft',exact:true}).click();
    assert.ok((await page.locator('#document-preview').innerText()).includes('Persisted Company'));
  });
  if(await page.locator('#modal').isVisible())await page.getByRole('button',{name:'Close dialog'}).click();
  await check('Navigation reports backend failure and Retry reconnects',async()=>{
    await page.route('**/api/dashboard',route=>route.fulfill({status:503,contentType:'application/json',body:'{"error":"Database temporarily unavailable"}'}));
    await page.locator('#navigation').getByRole('link',{name:'Overview',exact:true}).click();
    await page.getByText('Database temporarily unavailable',{exact:true}).waitFor();
    await page.unroute('**/api/dashboard');
    await page.getByRole('button',{name:'Try again'}).click();
    await page.locator('.stat-card').first().waitFor();
  });
  await page.unroute('**/api/dashboard');
  await check('All seven pages render on mobile without page overflow',async()=>{
    await page.setViewportSize({width:390,height:844});
    for(const route of ['dashboard','scanner','compliance','documents','knowledge','settings','assistant']){
      await page.goto(base+'/#'+route);await page.locator('#main h1').waitFor();
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),route+' overflows');
    }
  });
  await check('No browser JavaScript errors',async()=>assert.deepEqual(errors,[]));
  fs.mkdirSync(path.join(root,'test-results'),{recursive:true});
  fs.writeFileSync(path.join(root,'test-results','browser-integrity.json'),JSON.stringify({browser:'Brave',checks},null,2));
  if(checks.some(c=>!c.passed))process.exitCode=1;
}
main().catch(e=>{console.error(e);process.exitCode=1;}).finally(async()=>{
  if(browser)await browser.close();server.kill();
  await new Promise(r=>server.exitCode!==null?r():server.once('exit',r));
  const resolved=path.resolve(temporary);
  if(resolved.startsWith(path.resolve(os.tmpdir())+path.sep)&&path.basename(resolved).startsWith('nitishield-integrity-'))fs.rmSync(resolved,{recursive:true,force:true});
});
