/* Optional: Brave -> Flask -> real Ollama/public HTTP -> disposable SQLite. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const {spawn,spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'..');
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'nitishield-live-'));
const python=process.env.PYTHON || path.join(root,'.venv','Scripts','python.exe');
const port=process.env.TEST_PORT || '5058';
const base=`http://127.0.0.1:${port}`;
const output=path.join(root,'test-results');fs.mkdirSync(output,{recursive:true});
const server=spawn(python,[path.join(__dirname,'serve_test_app.py')],{cwd:root,windowsHide:true,
  env:{...process.env,NITISHIELD_TEST_DIR:temporary,TEST_PORT:port,NITISHIELD_LIVE_AI:'1'},stdio:['ignore','pipe','pipe']});
let log='',browser;server.stdout.on('data',d=>log+=d);server.stderr.on('data',d=>log+=d);
const report={browser:'Brave',model:'real Ollama',checks:[]};
async function main(){
  for(let i=0;i<100;i++){try{if((await fetch(base+'/api/health')).ok)break;}catch{}if(server.exitCode!==null)throw Error(log);await new Promise(r=>setTimeout(r,200));}
  browser=await chromium.launch({executablePath:process.env.BROWSER_EXECUTABLE || 'C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe',headless:process.env.HEADLESS==='1'});
  const page=await browser.newPage({viewport:{width:1440,height:1000},acceptDownloads:true});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  const pdf=path.join(temporary,'Leave policy.pdf');
  const fixture=spawnSync(python,['-c','import pymupdf,sys; d=pymupdf.open(); p=d.new_page(); p.insert_textbox((72,72,500,500),"Employees receive 18 days of paid annual leave per year. Submit leave requests to a manager at least 7 days in advance. Up to 5 unused days may be carried into the next year."); d.save(sys.argv[1]); d.close()',pdf],{windowsHide:true});
  assert.equal(fixture.status,0);
  await page.goto(base+'/#knowledge');await page.locator('#pdf-upload').setInputFiles(pdf);
  await page.getByText('PDF added to your knowledge base.',{exact:true}).waitFor();
  await page.getByRole('button',{name:'Ask about it'}).click();await page.locator('#chat-question').waitFor();
  assert.ok(await page.locator('#chat-document').inputValue());
  for(const question of ['How many paid leave days do employees get per year?','Explain that simply.']){
    console.log('Checking real AI: '+question);
    const started=Date.now();
    await page.locator('#chat-question').fill(question);
    const responseEvent=page.waitForResponse(r=>r.url().endsWith('/api/search')&&r.request().method()==='POST',{timeout:200000});
    await page.getByRole('button',{name:'Send question'}).click();
    const response=await responseEvent;
    const body=await response.json();
    report.checks.push({name:question,status:response.status(),seconds:Math.round((Date.now()-started)/1000),mode:body.mode,answer:body.answer,sources:body.results?.length});
    assert.equal(response.status(),200);assert.equal(body.mode,'generated',body.answer);
    assert.match(body.answer,/18|eighteen/i);assert.ok(body.results.length);assert.match(body.answer,/\[\d+\]/);
    await page.waitForFunction(()=>document.querySelector('#chat-question')?.disabled===false);
    console.log('PASS real AI generated and saved answer in '+Math.round((Date.now()-started)/1000)+' seconds');
  }
  await page.reload();await page.locator('.message.user').last().waitFor();
  assert.equal(await page.locator('.message.user').count(),2);
  await page.screenshot({path:path.join(output,'brave-real-ai.png'),fullPage:true,animations:'disabled'});
  report.checks.push({name:'Real generated conversation survives browser reload',passed:true});
  await page.goto(base+'/#scanner');await page.getByLabel('Website URL').fill('https://example.com');
  await page.getByLabel('I own this website or have permission to assess it.').check();
  const scanEvent=page.waitForResponse(r=>r.url().endsWith('/api/scans')&&r.request().method()==='POST',{timeout:60000});
  await page.getByRole('button',{name:'Run assessment',exact:true}).click();
  const response=await scanEvent;const scan=await response.json();
  report.checks.push({name:'Real public HTTP assessment',status:response.status(),scan});
  assert.equal(response.status(),201,JSON.stringify(scan));
  await page.getByRole('heading',{name:'Your security assessment',exact:true}).waitFor();
  await page.screenshot({path:path.join(output,'brave-real-scan.png'),fullPage:true,animations:'disabled'});
  console.log('PASS real public HTTP assessment saved score '+scan.score);
  assert.deepEqual(errors,[]);
}
main().catch(e=>{report.error=e.message;console.error(e);process.exitCode=1;}).finally(async()=>{
  fs.writeFileSync(path.join(output,'browser-live-services.json'),JSON.stringify(report,null,2));
  if(browser)await browser.close();server.kill();
  await new Promise(r=>server.exitCode!==null?r():server.once('exit',r));
  const resolved=path.resolve(temporary);
  if(resolved.startsWith(path.resolve(os.tmpdir())+path.sep)&&path.basename(resolved).startsWith('nitishield-live-'))fs.rmSync(resolved,{recursive:true,force:true});
});
