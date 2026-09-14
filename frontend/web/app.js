/* NitiShield's browser workspace. All business state is stored by the Flask API. */
'use strict';

const paths = {
  'shield-check':'<path d="M12 3 3.5 6.5V12c0 5.3 8.5 9 8.5 9s8.5-3.7 8.5-9V6.5L12 3Z"/><path d="m8 12 2.5 2.5L16 9"/>',
  shield:'<path d="M12 3 3.5 6.5V12c0 5.3 8.5 9 8.5 9s8.5-3.7 8.5-9V6.5L12 3Z"/><path d="M12 8v4m0 4h.01"/>',
  grid:'<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/><rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>',
  scan:'<path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m13-5v3a2 2 0 0 1-2 2h-3M2 12h20"/><rect x="7" y="7" width="10" height="10" rx="2"/>',
  checklist:'<rect x="5" y="4" width="14" height="17" rx="2"/><path d="M9 4V2h6v2M9 10l1 1 2-2m2 2h2M9 16l1 1 2-2m2 2h2"/>',
  sparkles:'<path d="m12 3 2.3 6.7L21 12l-6.7 2.3L12 21l-2.3-6.7L3 12l6.7-2.3L12 3Zm7-1v4m-2-2h4M4 18v4m-2-2h4"/>',
  document:'<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6Z"/><path d="M14 2v6h6M8 13h8m-8 4h5"/>',
  book:'<path d="M12 5v16M3 3l9 2 9-2v16l-9 2-9-2V3Z"/><path d="m6 7 3 .7m-3 3.3 3 .7m6-4 3-.7m-3 4.7 3-.7"/>',
  settings:'<path d="m9 3-1 3-3 1-2 4 2 2v3l3 3h3l2 2 4-2 1-3 3-1v-5l-3-1-1-3h-3L12 3H9Z"/><circle cx="12" cy="12" r="3"/>',
  home:'<path d="m3 10 9-7 9 7v10H3V10Z"/><path d="M9 20v-7h6v7"/>',
  search:'<circle cx="10.5" cy="10.5" r="6.5"/><path d="m16 16 5 5"/>',
  bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Zm-8 12h4"/>',
  'arrow-up-right':'<path d="M6 18 18 6M6 6h12v12"/>',
  'arrow-right':'<path d="M4 12h16m-6-6 6 6-6 6"/>',
  download:'<path d="M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5"/>',
  upload:'<path d="M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5"/>',
  plus:'<path d="M12 5v14M5 12h14"/>',
  check:'<path d="m5 12 4 4L19 6"/>',
  'check-circle':'<circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/>',
  alert:'<path d="M10.3 3.8a2 2 0 0 1 3.4 0L22 18a2 2 0 0 1-1.7 3H3.7A2 2 0 0 1 2 18l8.3-14.2Z"/><path d="M12 9v4m0 4h.01"/>',
  clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18m-13 5h2m4 0h2"/>',
  globe:'<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
  lock:'<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V6a4 4 0 0 1 8 0v4m-4 5v2"/>',
  mail:'<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 5 9 8 9-8"/>',
  user:'<circle cx="12" cy="8" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
  building:'<path d="M4 21V3h12v18M16 9h4v12M2 21h20M8 7h4m-4 4h4m-4 4h4m-3 6v-3h2v3"/>',
  chevrons:'<path d="m9 8 3-3 3 3m-6 8 3 3 3-3"/>',
  menu:'<path d="M4 6h16M4 12h16M4 18h16"/>',
  close:'<path d="m6 6 12 12M6 18 18 6"/>',
  send:'<path d="m22 2-7 20-4-9-9-4 20-7ZM22 2 11 13"/>',
  trash:'<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
  copy:'<rect x="8" y="8" width="13" height="13" rx="2"/><path d="M16 8V3H3v13h5"/>',
  leaf:'<path d="M20 3C9 2 3 5 4 12s10 10 14 2c2-4 2-8 2-11ZM4 21 15 10"/>',
  info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10h.01"/>',
  refresh:'<path d="M20 7v5h-5M4 17v-5h5M6 6a8 8 0 0 1 14 6M4 12a8 8 0 0 0 14 6"/>',
  history:'<path d="M3 3v6h6M3 9a9 9 0 1 1 0 7m9-10v6l4 2"/>',
  'help-circle':'<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 2-2.5 2-2.5 4m0 4h.01"/>',
};
const icon = (name, cls='') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.document}</svg>`;
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const pages = [
  {id:'dashboard',title:'Overview',icon:'grid'},
  {id:'scanner',title:'Security scanner',icon:'scan'},
  {id:'compliance',title:'Legal compliance',icon:'checklist'},
  {id:'assistant',title:'Legal assistant',icon:'sparkles',tag:'AI'},
  {id:'documents',title:'Document studio',icon:'document'},
  {id:'knowledge',title:'Knowledge base',icon:'book'},
];
const templates = [
  {id:'privacy_policy',title:'Privacy policy',icon:'lock',category:'DATA & PRIVACY',description:'Explain how your business collects, uses, and protects personal information.'},
  {id:'employment_agreement',title:'Employment agreement',icon:'user',category:'PEOPLE & WORK',description:'Start an agreement with clear responsibilities, working arrangements, and expectations.'},
  {id:'nda',title:'Non-disclosure agreement',icon:'shield-check',category:'BUSINESS',description:'Set out how confidential business information should be shared and protected.'},
  {id:'incident_response',title:'Incident response plan',icon:'scan',category:'CYBERSECURITY',description:'Give your team a practical starting point for responding to a security incident.'},
];
const state = {page:'dashboard',data:null,taskFilter:'all',taskQuery:'',knowledgeQuery:'',knowledge:[],documents:[],conversations:[],chatDocument:'',chatLanguage:'',assistantStatus:null,renderVersion:0,dataVersion:0,historyVersion:0,busyChat:false,busyScan:false};
const main = document.getElementById('main');
const modal = document.getElementById('modal');
let modalReturnFocus = null;
let latestDataRefresh = null;

function hydrateIcons(root=document){ root.querySelectorAll('[data-icon]').forEach(el => { el.innerHTML=icon(el.dataset.icon); el.removeAttribute('data-icon'); }); }
async function api(path, options={}) {
  const controller = new AbortController();
  const timeout = setTimeout(()=>controller.abort(),path==='/search'?195000:60000);
  try {
    const response = await fetch(`/api${path}`, {cache:'no-store',...options, headers:{...(options.body instanceof FormData ? {} : {'Content-Type':'application/json'}),...options.headers}, signal:controller.signal});
    const payload = await response.json().catch(()=>({error:'The server returned an unreadable response. Please try again.'}));
    if(!response.ok) throw new Error(payload.error || `The request failed (${response.status}).`);
    return payload;
  } catch(error) {
    if(error.name==='AbortError') throw new Error('This request took too long. Check your connection and try again.');
    if(error instanceof TypeError) throw new Error('Cannot reach the backend. Make sure the NitiShield server is running, then retry.');
    throw error;
  } finally { clearTimeout(timeout); }
}
const json = body => JSON.stringify(body);
function toast(message,error=false) {
  const el=document.createElement('div');el.className=`toast${error?' error':''}`;
  el.innerHTML=`${icon(error?'alert':'check-circle')}<span>${esc(message)}</span>`;
  document.getElementById('toast-region').append(el);
  setTimeout(()=>el.remove(),error?8500:4500);
}
async function copyText(text){
  if(navigator.clipboard&&window.isSecureContext){
    try{await navigator.clipboard.writeText(text);return;}catch{/* Try the browser's selection-based copy when permission is unavailable. */}
  }
  const previousFocus=document.activeElement;
  const selection=document.createElement('textarea');
  selection.value=text;
  selection.setAttribute('readonly','');
  selection.setAttribute('aria-label','Text to copy');
  selection.style.cssText='position:fixed;left:0;top:0;width:1px;height:1px;opacity:0;pointer-events:none';
  (modal.open?modal:document.body).append(selection);
  try{
    selection.focus();selection.select();selection.setSelectionRange(0,text.length);
    if(!document.execCommand('copy'))throw new Error('Your browser blocked copying. Select the draft text and press Ctrl+C, or download the draft.');
  }finally{selection.remove();if(previousFocus?.isConnected)previousFocus.focus();}
}
function formatDate(value,options={}) {
  if(!value)return 'No date set';
  const date=new Date(/^\d{4}-\d{2}-\d{2}$/.test(value)?`${value}T12:00:00`:value);
  return Number.isNaN(date.getTime())?'Date unavailable':date.toLocaleDateString('en-GB',{day:'numeric',month:'short',...options});
}
function when(value) {
  if(!value)return '';
  const date=new Date(value);if(Number.isNaN(date.getTime()))return '';
  const diff=Math.max(0,Date.now()-date.getTime());
  if(diff<60000)return 'Just now';if(diff<3600000)return `${Math.floor(diff/60000)} min ago`;
  if(diff<86400000)return `${Math.floor(diff/3600000)} hr ago`;return formatDate(value);
}
const today = () => {const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;};
const initials = name => String(name||'My business').split(/\s+/).filter(Boolean).slice(0,2).map(w=>w[0]).join('').toUpperCase();
const badge = (text,style=text) => `<span class="badge ${esc(style)}">${esc(text)}</span>`;
function empty(title,description,action='') { return `<div class="empty-state">${icon('leaf')}<h3>${esc(title)}</h3><p>${esc(description)}</p>${action}</div>`; }
function heading(title,subtitle,actions='',eyebrow='YOUR BUSINESS, IN FOCUS') {
  return `<div class="page-heading"><div><div class="eyebrow">${esc(eyebrow)}</div><h1>${esc(title)}</h1><p>${esc(subtitle)}</p></div>${actions?`<div class="button-row">${actions}</div>`:''}</div>`;
}
function button(label,action,ico='plus',style='primary',attrs=''){return `<button class="btn btn-${style}" data-action="${action}" ${attrs}>${icon(ico)}${label}</button>`;}
function link(label,page,ico='arrow-right',cls='text-button'){return `<a class="${cls}" href="#${page}">${label}${icon(ico)}</a>`;}
function ring(score,label='out of 100') {return `<div class="score-ring" style="--value:${Math.max(0,Math.min(100,Number(score)||0))}"><svg viewBox="0 0 120 120" aria-hidden="true"><circle cx="60" cy="60" r="50"/><circle cx="60" cy="60" r="50"/></svg><strong>${score==null?'—':esc(score)}</strong><small>${esc(label)}</small></div>`;}
function errorView(error){return `<div class="error-panel"><h2>Let’s reconnect your workspace</h2><p>${esc(error.message)}</p>${button('Try again','retry','refresh')}</div>`;}
function setConnection(ok){document.getElementById('connection-dot').className=`status-dot ${ok?'online':'error'}`;document.getElementById('connection-status').textContent=ok?'Workspace connected':'Connection unavailable';}
function refreshData(){
  const version=++state.dataVersion;
  latestDataRefresh=api('/dashboard').then(data=>{
    // A render waiting on an older response must also wait for its replacement.
    if(version!==state.dataVersion)return latestDataRefresh;
    state.data=data;state.knowledge=data.knowledge||[];state.documents=data.documents||[];setConnection(true);updateProfile();
    return data;
  }).catch(error=>{
    if(version!==state.dataVersion)return latestDataRefresh;
    setConnection(false);throw error;
  });
  return latestDataRefresh;
}
function updateProfile(){
  const p=state.data?.profile||{};const name=p.business_name||'My business';
  document.getElementById('workspace-name').textContent=name;
  document.getElementById('profile-name').textContent=p.owner||name;
  document.getElementById('profile-initials').textContent=initials(p.owner||name);
  document.getElementById('top-avatar').textContent=initials(p.owner||name);
  document.getElementById('notification-dot').hidden=p.notifications===false||!(state.data?.tasks||[]).some(t=>t.status!=='completed');
}
function closeSidebar(){document.getElementById('sidebar').classList.remove('open');document.getElementById('sidebar-backdrop').classList.remove('open');}
function navigate(page){if(location.hash===`#${page}`)renderPage();else location.hash=page;closeSidebar();}
async function renderPage(){
  const requested=location.hash.slice(1).split('/')[0]||'dashboard';
  state.page=[...pages.map(p=>p.id),'settings'].includes(requested)?requested:'dashboard';
  const version=++state.renderVersion;
  const page=state.page;
  document.title=`${pages.find(p=>p.id===state.page)?.title||'Settings'} · NitiShield AI`;
  document.getElementById('breadcrumb-title').textContent=pages.find(p=>p.id===state.page)?.title||'Settings';
  document.querySelectorAll('.nav-item').forEach(a=>{a.classList.toggle('active',a.getAttribute('href')===`#${state.page}`);if(a.classList.contains('active'))a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  closeSidebar();
  try {
    main.innerHTML='<div class="initial-loading"><span class="spinner"></span><p>Loading your workspace...</p></div>';
    await refreshData();
    if(version!==state.renderVersion)return;
    if(page==='assistant'){
      main.innerHTML='<div class="initial-loading"><span class="spinner"></span><p>Loading your workspace...</p></div>';
      const [result,status]=await Promise.all([api('/conversations'),api('/assistant/status')]);
      if(version!==state.renderVersion)return;
      state.conversations=result;state.assistantStatus=status;
      if(state.chatDocument&&!state.knowledge.some(d=>d.id===state.chatDocument))state.chatDocument='';
    }
    if(version!==state.renderVersion)return;
    const renderers={dashboard:dashboardView,scanner:scannerView,compliance:complianceView,assistant:assistantView,documents:documentsView,knowledge:knowledgeView,settings:settingsView};
    main.innerHTML=`<div class="page-enter">${renderers[state.page]()}</div>`;
    if(state.page==='assistant')scrollChat();
  }catch(error){if(version===state.renderVersion){main.innerHTML=errorView(error);setConnection(false);}}
}

function dashboardView(){
  const {profile={},tasks=[],scans=[],documents=[],activity=[],stats={}}=state.data;
  const completed=tasks.filter(t=>t.status==='completed').length;
  const percent=tasks.length?Math.round(completed/tasks.length*100):0;
  const latest=scans[0];const score=latest?.score??stats.security_score??null;
  const findings=(latest?.findings||[]).filter(f=>!['pass','passed'].includes(f.status));
  const pending=tasks.filter(t=>t.status!=='completed');
  const greeting=new Date().getHours()<12?'Good morning':new Date().getHours()<17?'Good afternoon':'Good evening';
  const name=profile.owner?`, ${profile.owner.split(' ')[0]}`:'';
  return heading(`${greeting}${name} 👋`,'Here’s where your business stands. Let’s make it a little stronger.',
    `<a class="btn btn-secondary" href="/api/export">${icon('download')}<span class="optional-label">Export </span>report</a>${button('Run assessment','navigate','scan','primary','data-page="scanner"')}`,
    new Date().toLocaleDateString('en-GB',{weekday:'long',day:'numeric',month:'long',year:'numeric'}).toUpperCase())+
    `<section class="welcome-banner"><div class="banner-icon">${icon('shield-check')}</div><div><h2>A stronger business starts with peace of mind.</h2><p>Understand your risks, stay on top of compliance, and take your next step with confidence.</p>${link('Explore your action plan','compliance')}</div><div class="banner-art">${icon('shield-check')}</div></section>
    <section class="stat-grid" aria-label="Workspace metrics">
      ${statCard('Security score',score==null?'—':score,'/ 100','shield-check','',score==null?'Not assessed':score>=80?'Looking good':'Needs attention',score==null?'Run your first assessment':'Latest website assessment',score==null?'blue':'')}
      ${statCard('Compliance readiness',percent,'%','checklist','blue',`${completed} of ${tasks.length} complete`,'Your starter checklist','blue')}
      ${statCard('Open findings',latest?findings.length:'—','','alert','amber',latest?'Assessment findings':'No assessment yet',latest?'Review recommended actions':'Your results will appear here','amber')}
      ${statCard('Documents created',documents.length||stats.documents_count||0,'','document','purple','Your document library','Ready when you need them','blue')}
    </section>
    <div class="dashboard-columns"><div class="column-stack">
      <section class="card"><div class="card-header"><div><h2>Security overview</h2><p>A clearer picture of your website’s protection.</p></div><span class="pill">${icon('globe')} Website</span></div><div class="card-body"><div class="security-summary">${ring(score)}<div>${badge(score==null?'GET YOUR BASELINE':score>=80?'LOOKING GOOD':'ACTION RECOMMENDED',score==null?'low':score>=80?'completed':'high')}<h3>${score==null?'Your next step: an assessment':score>=80?'Good foundations. Keep building.':'A few improvements can go a long way.'}</h3><p>${score==null?'Check your public website’s HTTPS and security headers to see where you stand.':`${latest.checks_passed??0} of ${latest.checks_total??6} checks passed. Review each finding for practical next steps.`}</p></div></div><div class="severity-row">${['high','medium','low'].map((s,i)=>`<div class="severity-item"><i class="color-dot ${['red','amber','blue'][i]}"></i>${s[0].toUpperCase()+s.slice(1)}<b>${latest?findings.filter(f=>f.severity===s).length:'—'}</b></div>`).join('')}<div class="severity-item" style="margin-left:auto"><i class="color-dot green"></i>Passed<b>${latest?.checks_passed??'—'}</b></div></div></div><div class="card-foot"><span>${icon('clock')}${latest?`Last assessed ${esc(when(latest.created_at))}`:'Your first assessment is a click away'}</span>${link('View assessment','scanner')}</div></section>
      <section class="card"><div class="card-header"><div><h2>Your next steps <span class="pill" style="margin-left:6px">${pending.length}</span></h2><p>Small actions. Meaningful progress.</p></div>${link('View all','compliance')}</div><div class="task-list">${pending.length?pending.slice(0,4).map(taskRow).join(''):empty('You’re all caught up','Add a task to plan your next improvement.',button('Add a task','add-task'))}</div><div class="card-foot"><span>Starter recommendations for your business</span>${button('Add task','add-task','plus','secondary')}</div></section>
      <section><div class="section-title" style="margin-top:0"><h2>A shortcut to what’s next</h2></div><div class="quick-grid">${quickAction('Ask a legal question','Answers from your sources','assistant','sparkles')}${quickAction('Create a document','A head start on paperwork','documents','document')}${quickAction('Browse your library','Keep knowledge close','knowledge','book')}</div></section>
    </div><div class="column-stack right-column">
      <section class="card"><div class="card-header"><div><h2>Compliance at a glance</h2><p>Your progress, one step at a time.</p></div>${icon('checklist')}</div><div class="card-body"><div class="compliance-number"><strong>${percent}%</strong><span>of your checklist complete</span></div><div class="compliance-bar"><span style="width:${percent}%"></span></div>${['Legal','Security','Operations'].map((cat,i)=>{const ct=tasks.filter(t=>t.category===cat);return `<div class="compliance-detail"><span><i class="color-dot ${['green','blue','amber'][i]}"></i>${cat==='Legal'?'Legal & business':cat==='Security'?'Data & security':'People & operations'}</span><strong>${ct.filter(t=>t.status==='completed').length} / ${ct.length}</strong></div>`;}).join('')}</div><div class="card-foot"><span>Your checklist, your pace.</span>${link('View checklist','compliance')}</div></section>
      <section class="card"><div class="card-header"><div><h2>Recent activity</h2><p>What’s happening in your workspace.</p></div>${icon('history')}</div><div class="card-body">${activity.length?activity.slice(0,4).map(activityItem).join(''):`<div class="empty-activity"><span class="activity-icon">${icon('leaf')}</span><div><h3 style="font-size:11px;margin-bottom:5px">A fresh start for your business</h3><p>Your completed tasks, assessments, and documents will appear here.</p></div></div>`}</div></section>
      <section class="insight-card"><div class="insight-label">${icon('sparkles')} A LITTLE BUSINESS WISDOM</div><h3>Security grows with your everyday habits.</h3><p>Start with a simple checklist. Make one improvement today, and build from there.</p>${link('Find your next step','compliance')}</section>
    </div></div>`;
}
function statCard(title,value,suffix,ico,color,label,note,badgeColor){return `<article class="stat-card"><div class="stat-top"><span>${title}</span><span class="stat-icon ${color}">${icon(ico)}</span></div><div class="stat-value">${esc(value)}<small>${suffix}</small></div><div class="stat-bottom"><span class="mini-badge ${badgeColor}">${esc(label)}</span><span>${note}</span></div></article>`;}
function taskRow(t){return `<div class="task-row"><button class="task-check ${t.status==='completed'?'completed':''}" aria-label="${t.status==='completed'?'Reopen':'Complete'} ${esc(t.title)}" aria-pressed="${t.status==='completed'}" data-action="toggle-task" data-id="${esc(t.id)}">${t.status==='completed'?icon('check'):''}</button><div class="task-text ${t.status==='completed'?'done':''}"><strong>${esc(t.title)}</strong><small>${esc(t.category)}${t.due_date?` · Due ${formatDate(t.due_date)}`:' · Starter recommendation'}</small></div>${badge(t.priority,t.priority)}</div>`;}
function quickAction(title,desc,page,ico){return `<a class="quick-action" href="#${page}">${icon(ico)}${icon('arrow-up-right','corner-arrow')}<strong>${title}</strong><p>${desc}</p></a>`;}
function activityItem(a){return `<div class="activity-item"><span class="activity-icon">${icon(({scan:'shield-check',task:'check',document:'document',settings:'settings',search:'sparkles',upload:'book'})[a.type]||'check-circle')}</span><div><strong>${esc(a.title)}</strong><p>${esc(a.detail||'')}</p><time datetime="${esc(a.created_at)}">${esc(when(a.created_at))}</time></div></div>`;}

function complianceView(){
  const tasks=state.data.tasks||[];const completed=tasks.filter(t=>t.status==='completed').length;
  return heading('A little progress, every day.','Keep your business essentials organised in one practical checklist.',button('Add task','add-task'),'LEGAL COMPLIANCE')+
  `<div class="notice">${icon('info')}<span>This is a starter checklist for your own review. Completion reflects your recorded progress and does not certify legal compliance.</span></div><div class="toolbar"><div class="tabs" aria-label="Task filter">${['all','pending','completed'].map(filter=>`<button class="tab ${state.taskFilter===filter?'active':''}" data-action="task-filter" data-filter="${filter}">${filter[0].toUpperCase()+filter.slice(1)} <span class="muted">${filter==='all'?tasks.length:filter==='completed'?completed:tasks.length-completed}</span></button>`).join('')}</div><input class="search-field" id="task-search" placeholder="Search your checklist..." aria-label="Search tasks" value="${esc(state.taskQuery)}"></div><section class="card"><div class="table-wrap"><table><thead><tr><th>TASK</th><th>CATEGORY</th><th>PRIORITY</th><th>DUE DATE</th><th>STATUS</th><th><span class="small">ACTIONS</span></th></tr></thead><tbody id="task-table-body">${taskTableRows()}</tbody></table></div></section>`;
}
function taskTableRows(){
  const tasks=(state.data.tasks||[]).filter(t=>(state.taskFilter==='all'||t.status===state.taskFilter)&&`${t.title} ${t.category}`.toLowerCase().includes(state.taskQuery.toLowerCase()));
  return tasks.length?tasks.map(t=>`<tr><td><button class="task-check ${t.status==='completed'?'completed':''}" aria-label="${t.status==='completed'?'Reopen':'Complete'} ${esc(t.title)}" aria-pressed="${t.status==='completed'}" data-action="toggle-task" data-id="${esc(t.id)}">${t.status==='completed'?icon('check'):''}</button><span class="table-title">${esc(t.title)}</span>${t.description?`<span class="table-subtitle">${esc(t.description)}</span>`:''}</td><td>${esc(t.category)}</td><td>${badge(t.priority)}</td><td class="muted">${formatDate(t.due_date)}</td><td>${badge(t.status)}</td><td><button class="icon-button" data-action="delete-task" data-id="${esc(t.id)}" aria-label="Delete ${esc(t.title)}">${icon('trash')}</button></td></tr>`).join(''):`<tr><td colspan="6">${empty('Nothing here just yet','Try another filter or add a task to your checklist.')}</td></tr>`;
}
function scannerView(){
  const scans=state.data.scans||[];
  return heading('Clarity starts with a check.','Assess your public website and get practical steps to improve its protection.',button('How it works','scan-help','help-circle','secondary'),'SECURITY SCANNER')+
    `<div class="two-columns"><section class="card"><div class="card-header"><div><h2>Assess your website</h2><p>A passive check of HTTPS and important response headers.</p></div><span class="stat-icon">${icon('globe')}</span></div><div class="card-body"><form id="scan-form"><div class="field"><label for="scan-url">Website URL</label><input id="scan-url" name="url" type="url" required placeholder="https://yourbusiness.com" value="${esc(state.data.profile?.website||'')}" maxlength="2048"><small>Use the full public URL, including https://.</small></div><div class="notice">${icon('shield-check')}<span>We check public page responses. This assessment does not log in, exploit vulnerabilities, or certify your website is secure.</span></div><label class="check-label"><input type="checkbox" name="authorized" required><span>I own this website or have permission to assess it.</span></label><div class="form-actions"><button class="btn btn-primary" type="submit" ${state.busyScan?'disabled':''}>${state.busyScan?'<span class="spinner"></span>':icon('scan')}${state.busyScan?'Assessment in progress...':'Run assessment'}</button></div><div id="scan-feedback" role="status"></div></form></div></section><section class="card"><div class="card-header"><h2>What we look at</h2></div><div class="card-body">${[['lock','HTTPS connection'],['shield','Content Security Policy'],['globe','Strict Transport Security'],['document','Content type protection'],['grid','Frame protection'],['user','Referrer policy']].map(([i,t])=>`<div class="compliance-detail"><span>${icon(i)} ${t}</span><span class="muted small">Public response</span></div>`).join('')}</div></section></div><section class="card scan-history"><div class="card-header"><div><h2>Assessment history</h2><p>Real results, saved for your next review.</p></div><span class="pill">${scans.length} assessment${scans.length===1?'':'s'}</span></div>${scans.length?`<div class="table-wrap"><table><thead><tr><th>WEBSITE</th><th>SCORE</th><th>CHECKS PASSED</th><th>ASSESSED</th><th>REPORT</th></tr></thead><tbody>${scans.map(s=>`<tr><td class="table-title">${esc(s.url)}</td><td>${badge(`${s.score} / 100`,s.score>=80?'completed':'medium')}</td><td>${esc(s.checks_passed)} / ${esc(s.checks_total)}</td><td class="muted">${formatDate(s.created_at)}</td><td><button class="text-button" data-action="scan-detail" data-id="${esc(s.id)}">View findings ${icon('arrow-right')}</button></td></tr>`).join('')}</tbody></table></div>`:empty('Your first assessment is waiting','Add your website above to create a security baseline.')}</section>`;
}
function scanDetail(scan){
  showModal('Your security assessment',`<div class="scan-result-header">${ring(scan.score)}<div><h2>${scan.score>=80?'A solid starting point':'Room to strengthen your website'}</h2><p>${esc(scan.url)}</p><p>${esc(scan.checks_passed)} of ${esc(scan.checks_total)} checks passed · ${formatDate(scan.created_at)}</p></div></div>${(scan.findings||[]).map(f=>{const pass=['pass','passed'].includes(f.status);return `<div class="finding"><div class="finding-icon ${pass?'pass':''}">${icon(pass?'check':'alert')}</div><div><div class="finding-title"><h3>${esc(f.title)}</h3>${badge(pass?'Passed':f.severity,pass?'pass':f.severity)}</div><p>${esc(f.description)}</p>${!pass&&f.recommendation?`<p><strong>Next step:</strong> ${esc(f.recommendation)}</p>`:''}</div></div>`;}).join('')}<div class="notice warning">${icon('info')}<span>This is a snapshot of response headers, not a comprehensive security audit.</span></div><div class="form-actions"><a class="btn btn-primary" href="/api/scans/${encodeURIComponent(scan.id)}/report">${icon('download')}Download report</a></div>`);
}

function documentsView(){return heading('Good paperwork. Less work.','Create useful first drafts, tailored to your business details.',`<span class="pill">${icon('document')} ${state.documents.length} saved drafts</span>`,'DOCUMENT STUDIO')+
  `<div class="template-grid">${templates.map(t=>`<article class="card template-card"><div class="template-icon">${icon(t.icon)}</div><span class="badge">${t.category}</span><h3>${t.title}</h3><p>${t.description}</p>${button('Create draft','create-document','plus','secondary',`data-template="${t.id}"`)}</article>`).join('')}</div><div class="notice warning">${icon('info')}<span>Documents are editable starting templates. Review the content and complete any remaining details with a qualified professional before using them.</span></div><section class="card"><div class="card-header"><div><h2>Your document library</h2><p>Prepared drafts, ready to download and make your own.</p></div></div>${state.documents.length?`<div class="table-wrap"><table><thead><tr><th>DOCUMENT</th><th>BUSINESS</th><th>CREATED</th><th>DOWNLOAD</th></tr></thead><tbody>${state.documents.map(d=>`<tr><td>${icon('document')} <span class="table-title">${esc(d.title)}</span></td><td>${esc(d.business_name)}</td><td>${formatDate(d.created_at)}</td><td><div class="button-row"><button class="text-button" data-action="view-document" data-id="${esc(d.id)}">View draft ${icon('document')}</button><a class="text-button" href="/api/documents/${encodeURIComponent(d.id)}/download">Download ${icon('download')}</a></div></td></tr>`).join('')}</tbody></table></div>`:empty('Your library starts here','Choose a template above to create your first business document.')}</section>`;}
function knowledgeView(){return heading('Your knowledge, within reach.','A shared home for the documents behind your legal research.',button('Upload PDF','upload','upload'),'KNOWLEDGE BASE')+
  `<input type="file" id="pdf-upload" accept="application/pdf,.pdf" hidden><div class="upload-area" id="drop-zone" role="button" tabindex="0" aria-label="Choose a PDF to upload" data-action="upload">${icon('upload')}<strong>Bring your documents together</strong><p>Drop a PDF here, or click to browse · Text-based PDFs, up to 10 MB</p></div><div class="toolbar"><h2>${state.knowledge.length} source document${state.knowledge.length===1?'':'s'}</h2><input class="search-field" id="knowledge-search" aria-label="Search documents" placeholder="Search your library..." value="${esc(state.knowledgeQuery)}"></div><div class="knowledge-grid" id="knowledge-results">${knowledgeCards(state.knowledgeQuery)}</div><div class="notice">${icon('info')}<span>The legal assistant uses these documents to explain answers in plain language. A document’s presence in the library does not verify its authority or currency.</span></div>`;}
function knowledgeCards(query){const docs=state.knowledge.filter(d=>`${d.title} ${d.file_name}`.toLowerCase().includes(query.toLowerCase()));return docs.length?docs.map(d=>`<article class="card knowledge-card"><div class="template-icon">${icon('document')}</div><div><h3>${esc(d.title)}</h3><p>PDF document · ${esc(d.pages)} page${d.pages===1?'':'s'} · ${Math.max(1,Math.round(d.size/1024))} KB</p><div class="button-row"><a class="text-button" href="/api/knowledge/${encodeURIComponent(d.id)}/download">Open source ${icon('arrow-up-right')}</a><button class="text-button" style="margin-left:8px" data-action="ask-document" data-title="${esc(d.title)}" data-id="${esc(d.id)}">Ask about it ${icon('sparkles')}</button></div></div></article>`).join(''):`<div class="card full-width">${empty('No matching documents','Upload a PDF or try a different search.')}</div>`;}

const suggestions=['How can you help me?','Tell me about this website','Can a business use a digital signature?','नेपालीमा जवाफ दिनुहोस्: तपाईंले कसरी सहयोग गर्न सक्नुहुन्छ?'];
function assistantView(){return heading('A clearer way to find answers.','Ask everyday questions, get help with NitiShield, or explore your PDFs.','','LEGAL ASSISTANT')+
  `<div class="chat-layout"><section class="card chat-panel"><div class="chat-header"><div class="chat-heading"><span class="chat-avatar">${icon('sparkles')}</span><div><strong>NitiShield assistant</strong><small>Everyday answers · PDF explanations</small></div></div>${button('Clear history','clear-chat','trash','secondary',state.busyChat?'disabled':'')}</div>${chatScope()}<div class="chat-messages" id="chat-messages" aria-live="polite">${state.conversations.length?state.conversations.map(conversationMarkup).join(''):chatWelcome()}</div><form class="chat-form" id="chat-form"><div class="chat-input-wrap"><textarea id="chat-question" name="question" rows="2" required maxlength="2000" placeholder="Ask anything, or choose a PDF to discuss..." aria-label="Your question" ${state.busyChat?'disabled':''}></textarea><button type="submit" aria-label="Send question" ${state.busyChat?'disabled':''}>${icon('send')}</button></div><p class="chat-disclaimer">AI can make mistakes. Check the cited pages for important legal decisions.</p></form></section><aside class="chat-sidebar"><div class="card"><h3>Ask naturally</h3><p>Everyday questions work without a PDF. Choose a document when you want an answer based on that PDF, with page references you can check. Follow up with “explain that simply.”</p><div style="margin-top:16px">${link('Browse knowledge base','knowledge')}</div></div><div class="card"><h3>English or नेपाली</h3><p>Auto follows your question’s language. Choose नेपाली to request Nepali answers even when you type in English. Searchable Nepali PDFs are supported; scanned images need OCR first.</p></div></aside></div>`;}
function chatScope(){return `<div class="chat-scope"><label for="chat-document">Answer from</label><select id="chat-document" aria-label="Document to ask about" ${state.busyChat?'disabled':''}><option value="">Auto · general chat + library</option>${state.knowledge.map(d=>`<option value="${esc(d.id)}" ${state.chatDocument===d.id?'selected':''}>${esc(d.title)}</option>`).join('')}</select><label for="chat-language">Reply in</label><select id="chat-language" aria-label="Response language" ${state.busyChat?'disabled':''}>${[['','Auto · question language'],['English','English'],['नेपाली','नेपाली'],['Hindi','हिन्दी']].map(([value,label])=>`<option value="${value}" ${state.chatLanguage===value?'selected':''}>${label}</option>`).join('')}</select><span class="small muted" role="status">${esc(state.assistantStatus?.message||'Checking local AI...')}</span></div>`;}
document.addEventListener('change',event=>{if(event.target.id==='chat-document')state.chatDocument=event.target.value;if(event.target.id==='chat-language')state.chatLanguage=event.target.value;});
function chatWelcome(){return `<div class="chat-welcome"><span class="chat-avatar">${icon('sparkles')}</span><h2>Let’s find a little clarity.</h2><p>Ask a normal question, get to know this website, or talk through a PDF in simple words.</p><div class="suggestions">${suggestions.map(q=>`<button class="suggestion" data-action="suggestion" data-question="${esc(q)}">${esc(q)} ${icon('arrow-up-right')}</button>`).join('')}</div></div>`;}
function sourceUrl(result){const url=result.metadata?.url;if(!url)return null;try{const parsed=new URL(url,location.origin);if(!['http:','https:'].includes(parsed.protocol))return null;return parsed.href;}catch{return null;}}
function answerMarkup(answer){return String(answer).split(/\n\s*\n/).filter(Boolean).map(part=>`<p>${esc(part).replace(/\*\*([^*\n]+)\*\*/g,'<strong>$1</strong>').replace(/\n/g,'<br>')}</p>`).join('');}
function conversationMarkup(c){return `<div class="message user">${esc(c.question)}</div><div class="message assistant"><span class="chat-avatar">${icon('sparkles')}</span><div class="message-body">${answerMarkup(c.answer||'I couldn’t finish that answer. Please try again.')}${(c.results||[]).slice(0,5).map((r,i)=>{const url=sourceUrl(r);return `<details class="source-card"><summary>[${i+1}] ${esc(r.metadata?.law_name||r.metadata?.file_name||'Source document')}${r.metadata?.page_number?` · Page ${esc(r.metadata.page_number)}`:''}</summary><p>${esc(r.text)}</p>${url?`<a class="text-button" href="${esc(url)}" target="_blank" rel="noopener noreferrer">Open source ${icon('arrow-up-right')}</a>`:''}</details>`;}).join('')}</div></div>`;}
function scrollChat(){const el=document.getElementById('chat-messages');if(el)el.scrollTop=el.scrollHeight;}

function settingsView(){const p=state.data.profile||{};return heading('Make this space yours.','Keep your business details ready for every document and assessment.','','WORKSPACE SETTINGS')+
  `<div class="settings-layout"><nav class="settings-menu" aria-label="Settings sections"><a class="active" href="#settings" data-action="focus-settings" data-target="business-name">${icon('building')}Business profile</a><a href="#settings" data-action="focus-settings" data-target="notifications">${icon('bell')}Workspace preferences</a><a href="#settings" data-action="focus-settings" data-target="export-settings">${icon('download')}Your data</a><p>These details belong to this local workspace and are saved on your backend.</p></nav><section class="card"><div class="card-header"><div><h2>Business profile</h2><p>The details that make your workspace personal.</p></div><span class="profile-avatar" style="width:44px;height:44px">${esc(initials(p.business_name))}</span></div><div class="card-body"><form id="settings-form"><div class="form-grid"><div class="field"><label for="business-name">Business name</label><input id="business-name" name="business_name" value="${esc(p.business_name||'')}" required maxlength="150"></div><div class="field"><label for="owner-name">Owner / representative</label><input id="owner-name" name="owner" value="${esc(p.owner||'')}" placeholder="Your name" maxlength="150"></div><div class="field"><label for="business-email">Business email</label><input id="business-email" name="email" type="email" value="${esc(p.email||'')}" placeholder="hello@yourbusiness.com" maxlength="254"></div><div class="field"><label for="business-type">Business type</label><select id="business-type" name="business_type">${['IT / Software','E-Commerce','Retail','Service','Education','Other'].map(t=>`<option ${p.business_type===t?'selected':''}>${t}</option>`).join('')}</select></div><div class="field full-width"><label for="business-website">Website</label><input id="business-website" name="website" type="url" value="${esc(p.website||'')}" placeholder="https://yourbusiness.com" maxlength="2048"></div><div class="field full-width"><label for="business-address">Business address</label><textarea id="business-address" name="address" rows="3" maxlength="1000" placeholder="Street, city, province">${esc(p.address||'')}</textarea></div></div><div class="section-title"><h2>Workspace preferences</h2></div><label class="check-label"><input id="notifications" type="checkbox" name="notifications" ${p.notifications!==false?'checked':''}><span>Show open-task reminders in the notification panel.<br><span class="muted small">This setting controls in-app reminders in your workspace.</span></span></label><div class="form-actions"><button class="btn btn-primary" type="submit">${icon('check')}Save changes</button></div></form><div class="export-box" id="export-settings" tabindex="-1"><div><h3>Your data, always within reach.</h3><p>Download a JSON copy of your workspace records.</p></div><a class="btn btn-secondary" href="/api/export">${icon('download')}Export data</a></div></div></section></div>`;}

function showModal(title,body){modalReturnFocus=document.activeElement;document.getElementById('modal-content').innerHTML=`<div class="modal-heading"><h2 id="modal-title">${esc(title)}</h2><button class="icon-button" aria-label="Close dialog" data-action="close-modal">${icon('close')}</button></div><div class="modal-body">${body}</div>`;if(!modal.open)modal.showModal();const first=modal.querySelector('input,textarea');if(first)first.focus();}
function taskModal(){showModal('One small step forward',`<form id="task-form"><div class="form-grid"><div class="field full-width"><label for="task-title">What needs doing?</label><input id="task-title" name="title" placeholder="e.g. Review access to business accounts" required maxlength="200"></div><div class="field"><label for="task-category">Category</label><select id="task-category" name="category"><option>Legal</option><option>Security</option><option>Operations</option></select></div><div class="field"><label for="task-priority">Priority</label><select id="task-priority" name="priority"><option value="medium">Medium</option><option value="high">High</option><option value="low">Low</option></select></div><div class="field full-width"><label for="task-date">Due date <span class="muted">(optional)</span></label><input id="task-date" type="date" name="due_date"></div></div><div class="form-actions">${button('Cancel','close-modal','close','secondary','type="button"')}<button class="btn btn-primary" type="submit">${icon('plus')}Add task</button></div></form>`);}
function documentModal(type){const t=templates.find(t=>t.id===type);if(!t)return;const p=state.data.profile||{};showModal(`Create a ${t.title.toLowerCase()}`,`<form id="document-form"><input type="hidden" name="type" value="${type}"><div class="form-grid"><div class="field full-width"><label for="draft-business">Business name</label><input id="draft-business" name="business_name" required maxlength="150" value="${esc(p.business_name||'')}"></div><div class="field full-width"><label for="draft-owner">Owner / representative</label><input id="draft-owner" name="owner" required maxlength="150" value="${esc(p.owner||'')}" placeholder="Full name"></div><div class="field full-width"><label for="draft-address">Business address</label><textarea id="draft-address" name="address" required maxlength="1000" placeholder="Your business address">${esc(p.address||'')}</textarea></div><div class="field full-width"><label for="draft-date">Effective date</label><input id="draft-date" name="effective_date" type="date" required value="${today()}"></div></div><div class="notice warning">${icon('info')}<span>This creates a draft template for review, not a certified legal document.</span></div><div class="form-actions"><button type="submit" class="btn btn-primary">${icon('document')}Create draft</button></div></form>`);}
function documentPreview(doc){showModal(`${doc.title} · Draft`, `<p style="margin-bottom:15px">Your draft is ready. Read through it and adapt the details before use.</p><pre id="document-preview">${esc(doc.content)}</pre><div class="form-actions">${button('Copy text','copy-document','copy','secondary')}<a class="btn btn-primary" href="/api/documents/${encodeURIComponent(doc.id)}/download">${icon('download')}Download draft</a></div>`);}
async function globalSearch(){await refreshData();showModal('Find your next step',`<input class="search-field" id="global-search-input" placeholder="Search pages, tasks, or documents..." aria-label="Search workspace"><div class="modal-search-results" id="global-search-results"></div>`);updateSearch('');}
function updateSearch(query){
  const candidates=[...pages.map(p=>({title:p.title,type:'Page',page:p.id})),{title:'Business settings',type:'Page',page:'settings'},...(state.data?.tasks||[]).map(t=>({title:t.title,type:'Task',page:'compliance'})),...(state.data?.documents||[]).map(d=>({title:d.title,type:'Document',page:'documents'})),...(state.knowledge||[]).map(d=>({title:d.title,type:'PDF',page:'knowledge'}))];
  const results=candidates.filter(x=>x.title.toLowerCase().includes(query.toLowerCase())).slice(0,12);
  document.getElementById('global-search-results').innerHTML=results.length?results.map(r=>`<button class="search-result" data-action="search-navigate" data-page="${r.page}" data-query="${r.type==='Task'||r.type==='PDF'?esc(r.title):''}"><span>${esc(r.title)}</span><small>${r.type} ${icon('arrow-up-right')}</small></button>`).join(''):'<p class="muted small" style="padding:15px">No matches. Try a different search.</p>';
}
function notifications(){const enabled=state.data?.profile?.notifications!==false;const tasks=(state.data?.tasks||[]).filter(t=>t.status!=='completed');showModal('Your workspace reminders',!enabled?empty('Reminders are turned off','You can enable in-app reminders in your workspace settings.',link('Open settings','settings','arrow-right','btn btn-secondary')):tasks.length?`<p style="margin-bottom:17px">${tasks.length} open tasks are ready whenever you are.</p>${tasks.map(t=>`<div class="task-row"><span class="activity-icon">${icon('checklist')}</span><div class="task-text"><strong>${esc(t.title)}</strong><small>${esc(t.category)}${t.due_date?` · Due ${formatDate(t.due_date)}`:''}</small></div>${badge(t.priority)}</div>`).join('')}<div class="form-actions">${button('Open checklist','search-navigate','arrow-right','primary','data-page="compliance"')}</div>`:empty('You’re all caught up','There are no open tasks on your checklist.'));}
async function mutateTask(id,changes){await api(`/tasks/${encodeURIComponent(id)}`,{method:'PATCH',body:json(changes)});await refreshData();await renderPage();}
async function handleAction(el,event){
  const a=el.dataset.action;
  if(el.tagName==='A')event.preventDefault();
  switch(a){
    case 'navigate':navigate(el.dataset.page);break;
    case 'menu':document.getElementById('sidebar').classList.toggle('open');document.getElementById('sidebar-backdrop').classList.toggle('open');break;
    case 'close-modal':modal.close();break;
    case 'global-search':await globalSearch();break;
    case 'notifications':await refreshData();notifications();break;
    case 'search-navigate':{
      if(el.dataset.page==='compliance'){state.taskFilter='all';state.taskQuery=el.dataset.query||'';}
      if(el.dataset.page==='knowledge')state.knowledgeQuery=el.dataset.query||'';
      modal.close();navigate(el.dataset.page);break;
    }
    case 'retry':state.data=null;await renderPage();break;
    case 'add-task':taskModal();break;
    case 'task-filter':state.taskFilter=el.dataset.filter;await renderPage();break;
    case 'toggle-task':{const task=state.data.tasks.find(t=>String(t.id)===el.dataset.id);if(!task)return;el.disabled=true;try{await mutateTask(task.id,{status:task.status==='completed'?'pending':'completed'});toast(task.status==='completed'?'Task reopened.':'One more step complete. Nicely done.');}finally{el.disabled=false;}break;}
    case 'delete-task':{const t=state.data.tasks.find(t=>String(t.id)===el.dataset.id);if(!t)return;showModal('Remove this task?',`<p>Remove “${esc(t.title)}” from your checklist? You can add a new task whenever you need one.</p><div class="form-actions">${button('Keep task','close-modal','close','secondary')}${button('Remove task','confirm-delete-task','trash','danger',`data-id="${esc(t.id)}"`)}</div>`);break;}
    case 'confirm-delete-task':el.disabled=true;try{await api(`/tasks/${encodeURIComponent(el.dataset.id)}`,{method:'DELETE'});modal.close();await refreshData();await renderPage();toast('Task removed.');}finally{el.disabled=false;}break;
    case 'scan-help':showModal('A focused website health check',`<p>NitiShield requests your public website and checks the response for HTTPS and protective HTTP headers. Each passed check contributes to the score.</p><div class="notice">${icon('shield-check')}<span>Only assess websites you own or are authorised to review. Private network addresses are not supported.</span></div><p>Results reflect a single point in time. They do not test application logic, credentials, malware, or every possible vulnerability. A missing header is a configuration finding, not proof of an exploitable issue.</p>`);break;
    case 'scan-detail':{const scan=state.data.scans.find(s=>String(s.id)===el.dataset.id);if(scan)scanDetail(scan);break;}
    case 'create-document':documentModal(el.dataset.template);break;
    case 'view-document':el.disabled=true;try{documentPreview(await api(`/documents/${encodeURIComponent(el.dataset.id)}`));}finally{el.disabled=false;}break;
    case 'copy-document':{const text=document.getElementById('document-preview')?.textContent;if(text){await copyText(text);toast('Draft copied to clipboard.');}break;}
    case 'upload':document.getElementById('pdf-upload')?.click();break;
    case 'ask-document':{state.chatDocument=el.dataset.id;navigate('assistant');await waitForView('chat-question');const input=document.getElementById('chat-question');if(input){input.value='Summarize this PDF in simple language.';input.focus();}break;}
    case 'suggestion':{const input=document.getElementById('chat-question');input.value=el.dataset.question;document.getElementById('chat-form').requestSubmit();break;}
    case 'clear-chat':if(state.busyChat)return;showModal('Clear your conversation history?',`<p>This removes saved questions and answers from this workspace. Your source documents stay in the knowledge base.</p><div class="form-actions">${button('Keep history','close-modal','close','secondary')}${button('Clear history','confirm-clear-chat','trash','danger')}</div>`);break;
    case 'confirm-clear-chat':if(state.busyChat)return;el.disabled=true;try{await api('/conversations',{method:'DELETE'});state.historyVersion++;state.conversations=[];modal.close();await renderPage();toast('Conversation history cleared.');}finally{el.disabled=false;}break;
    case 'focus-settings':{const target=document.getElementById(el.dataset.target);if(target){target.scrollIntoView({behavior:'smooth',block:'center'});target.focus();}break;}
  }
}
async function waitForView(id){for(let i=0;i<50;i++){if(document.getElementById(id))return;await new Promise(r=>setTimeout(r,100));}}

async function handleForm(form){
  const submit=form.querySelector('[type="submit"]');const original=submit?.innerHTML;
  if(submit?.disabled)return;
  const values=Object.fromEntries(new FormData(form));
  if(submit){submit.disabled=true;submit.innerHTML='<span class="spinner"></span> Working...';}
  try{
    switch(form.id){
      case 'task-form':await api('/tasks',{method:'POST',body:json({...values,due_date:values.due_date||null})});modal.close();await refreshData();await renderPage();toast('Your next step is on the list.');break;
      case 'settings-form':{const profile=await api('/settings',{method:'PUT',body:json({...values,notifications:form.elements.notifications.checked})});state.data.profile=profile;await refreshData();await renderPage();toast('Business profile saved.');break;}
      case 'document-form':{const doc=await api('/documents',{method:'POST',body:json(values)});await refreshData();await renderPage();documentPreview(doc);toast('Your document draft is ready.');break;}
      case 'scan-form':{
        if(state.busyScan)return;state.busyScan=true;
        submit.innerHTML='<span class="spinner"></span> Assessing website...';
        const feedback=document.getElementById('scan-feedback');if(feedback)feedback.innerHTML='<div class="notice">Checking the public response. This may take a few moments.</div>';
        try{const scan=await api('/scans',{method:'POST',body:json({url:values.url,authorized:form.elements.authorized.checked})});await refreshData();state.busyScan=false;await renderPage();scanDetail(scan);toast('Assessment complete. Your findings are ready.');}
        finally{state.busyScan=false;if(feedback)feedback.innerHTML='';const active=document.querySelector('#scan-form [type="submit"]');if(active){active.disabled=false;active.innerHTML=`${icon('scan')}Run assessment`;}}
        break;
      }
      case 'chat-form':await sendQuestion(values.question,form);break;
    }
  }finally{if(submit?.isConnected){submit.disabled=false;submit.innerHTML=original;}}
}
async function sendQuestion(question,form){
  question=question.trim();if(!question)return;
  if(state.busyChat)return;state.busyChat=true;
  const historyVersion=state.historyVersion;
  const clearButton=document.querySelector('[data-action="clear-chat"]');if(clearButton)clearButton.disabled=true;
  const input=form.elements.question;input.disabled=true;
  const messages=document.getElementById('chat-messages');
  if(!state.conversations.length)messages.innerHTML='';
  document.querySelectorAll('#chat-document,#chat-language').forEach(selector=>selector.disabled=true);
  const pending=document.createElement('div');pending.className='pending-conversation';pending.innerHTML=`<div class="message user">${esc(question)}</div><div class="message assistant"><span class="chat-avatar">${icon('sparkles')}</span><span class="spinner"></span><span class="small muted">Writing an answer...</span></div>`;messages.append(pending);scrollChat();
  let answered=false;
  try{
    const answer=await api('/search',{method:'POST',body:json({question,...(state.chatDocument?{document_id:state.chatDocument}:{}),...(state.chatLanguage?{language:state.chatLanguage}:{})})});answered=true;
    if(historyVersion!==state.historyVersion)return;
    pending.outerHTML=conversationMarkup({...answer,question});input.value='';
    const conversations=await api('/conversations');
    if(historyVersion===state.historyVersion)state.conversations=conversations;
    await refreshData();
  }
  catch(error){pending.remove();if(messages.isConnected&&!messages.children.length)messages.innerHTML=chatWelcome();throw error;}
  finally{
    state.busyChat=false;
    input.disabled=false;
    if(state.page==='assistant'&&document.getElementById('chat-form')){
      main.innerHTML=`<div class="page-enter">${assistantView()}</div>`;
      const currentInput=document.getElementById('chat-question');
      if(!answered&&historyVersion===state.historyVersion)currentInput.value=question;
      scrollChat();currentInput.focus();
    }
  }
}
async function uploadFile(file){
  if(!file)return;
  if(!file.name.toLowerCase().endsWith('.pdf'))throw new Error('Choose a PDF document to upload.');
  if(file.size>10*1024*1024)throw new Error('That PDF is larger than 10 MB. Please choose a smaller file.');
  const area=document.getElementById('drop-zone');if(area?.dataset.busy==='true')return;
  if(area){area.dataset.busy='true';area.innerHTML='<span class="spinner"></span><strong>Reading and adding your PDF...</strong><p>We’re preparing it for your knowledge base.</p>';}
  try{const data=new FormData();data.append('file',file);await api('/knowledge',{method:'POST',body:data});await refreshData();await renderPage();toast('PDF added to your knowledge base.');}
  catch(error){await renderPage();throw error;}
}

document.getElementById('navigation').innerHTML=pages.map(p=>`<a class="nav-item" href="#${p.id}">${icon(p.icon)}<span>${p.title}</span>${p.tag?`<span class="nav-tag">${p.tag}</span>`:''}</a>`).join('');
hydrateIcons();
document.addEventListener('click',event=>{const el=event.target.closest('[data-action]');if(el&&!el.disabled){if(el.tagName==='BUTTON'&&el.type==='submit'&&el.closest('form'))return;handleAction(el,event).catch(error=>toast(error.message,true));}});
document.addEventListener('submit',event=>{if(event.target.tagName==='FORM'){event.preventDefault();handleForm(event.target).catch(error=>toast(error.message,true));}});
document.addEventListener('input',event=>{
  if(event.target.id==='task-search'){state.taskQuery=event.target.value;document.getElementById('task-table-body').innerHTML=taskTableRows();}
  if(event.target.id==='knowledge-search'){state.knowledgeQuery=event.target.value;document.getElementById('knowledge-results').innerHTML=knowledgeCards(state.knowledgeQuery);}
  if(event.target.id==='global-search-input')updateSearch(event.target.value);
});
document.addEventListener('change',event=>{if(event.target.id==='pdf-upload')uploadFile(event.target.files[0]).catch(error=>toast(error.message,true));});
document.addEventListener('keydown',event=>{
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'){event.preventDefault();globalSearch().catch(error=>toast(error.message,true));}
  if(event.key==='Escape')closeSidebar();
  if(event.target.id==='drop-zone'&&['Enter',' '].includes(event.key)){event.preventDefault();document.getElementById('pdf-upload').click();}
  if(event.target.id==='chat-question'&&event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();if(!state.busyChat)document.getElementById('chat-form').requestSubmit();}
});
document.addEventListener('dragover',event=>{const zone=event.target.closest('#drop-zone');if(zone){event.preventDefault();zone.classList.add('dragging');}});
document.addEventListener('dragleave',event=>{const zone=event.target.closest('#drop-zone');if(zone)zone.classList.remove('dragging');});
document.addEventListener('drop',event=>{const zone=event.target.closest('#drop-zone');if(zone){event.preventDefault();zone.classList.remove('dragging');uploadFile(event.dataTransfer.files[0]).catch(error=>toast(error.message,true));}});
modal.addEventListener('close',()=>{if(modalReturnFocus?.isConnected)modalReturnFocus.focus();});
modal.addEventListener('click',event=>{if(event.target===modal){const r=modal.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)modal.close();}});
modal.addEventListener('click',event=>{if(event.target.closest('a[href^="#"]'))modal.close();});
document.getElementById('sidebar-backdrop').addEventListener('click',closeSidebar);
window.addEventListener('hashchange',renderPage);
renderPage();
