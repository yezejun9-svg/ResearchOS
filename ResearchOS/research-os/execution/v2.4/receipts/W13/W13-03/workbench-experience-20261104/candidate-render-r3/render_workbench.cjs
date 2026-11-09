'use strict';

// Isolated development rendering only: no product Core, credentials or IPC.
const { app, BrowserWindow } = require('electron');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const assert = require('node:assert/strict');
const { createHash } = require('node:crypto');

const [sourceRoot, outputRoot, runLabel = 'candidate'] = process.argv.slice(2);
assert(sourceRoot && outputRoot, 'source and output roots required');
const dist = path.join(sourceRoot, 'apps/web/dist');
assert(fs.existsSync(path.join(dist, 'index.html')), 'Build the candidate first');
const { installFixture, projectId } = require(path.join(sourceRoot, 'tests/ui/frontend-redesign-fixture.cjs'));
fs.mkdirSync(outputRoot, { recursive: true });
app.setPath('userData', fs.mkdtempSync(path.join(os.tmpdir(), 'researchos-ui-fixture-')));
app.disableHardwareAcceleration();
const report = { schema: 'researchos.workbench-render.v1', kind: 'ELECTRON_RENDER_FIXTURE_ONLY',
  sourceRoot, runLabel, electron: process.versions.electron, checks: [], screenshots: [], unexpected: [],
  limits: ['Disposable fixture API and Desktop bridge; no real model/Core, installation, NVDA, physical IME or formal acceptance.',
    'Screenshots show the production renderer with synthetic project/session/event inputs.'] };
report.harness_sha256=createHash('sha256').update(fs.readFileSync(__filename)).digest('hex');
fs.copyFileSync(__filename,path.join(outputRoot,'render_workbench.cjs'));
report.dist_files=fs.readdirSync(path.join(dist,'assets')).map(name=>({name,sha256:createHash('sha256').update(fs.readFileSync(path.join(dist,'assets',name))).digest('hex')}));
report.source_manifest=['apps/web/src/main.jsx','apps/web/src/workbench.jsx','apps/web/src/components/workbench-layout.jsx','apps/web/src/activity.js','apps/web/src/components/activity-rail.jsx','apps/web/src/workbench.css','tests/ui/desktop/activity-projection.test.mjs'].filter(name=>fs.existsSync(path.join(sourceRoot,name))).map(name=>({path:name,sha256:createHash('sha256').update(fs.readFileSync(path.join(sourceRoot,name))).digest('hex')}));
let window, server;
function check(name, actual, detail) {
  report.checks.push({ name, status: actual ? 'PASS' : 'FAIL', detail });
  assert(actual, name + ': ' + JSON.stringify(detail));
}
async function evalInPage(code) {
  try {return await window.webContents.executeJavaScript(code, true)}
  catch(error) {report.failedEvaluation=code;throw error}
}
async function until(code) {
  const started = Date.now();
  while (Date.now() - started < 12000) {
    if (await evalInPage(code)) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error('Timed out waiting for ' + code);
}
async function shot(name) {
  const file = path.join(outputRoot, name + '.png');
  fs.writeFileSync(file, (await window.webContents.capturePage()).toPNG());
  report.screenshots.push({ name, path: file, sha256: createHash('sha256').update(fs.readFileSync(file)).digest('hex') });
}
function response(res, status, body, contentType = 'application/json') {
  res.writeHead(status, { 'content-type': contentType, 'cache-control': 'no-store' });
  res.end(body);
}
const override = `
  localStorage.setItem('researchos.theme', new URLSearchParams(location.search).get('theme') || 'light');
  window.__workbenchScenario = { mode: 'active' };
  const fixtureEvent = (sequence, kind, payload) => ({event_id:'fixture-e'+sequence, session_id:'session-one', sequence, kind, payload});
  const fixtureEvents = [
    fixtureEvent(1, 'RUN_STATE', { status:'RUNNING' }),
    fixtureEvent(2, 'TOOL_STARTED', {tool_call_id:'call-read', tool_name:'read_file', input_summary:'apps/web/src/workbench.jsx'}),
    fixtureEvent(3, 'TOOL_RESULT', {tool_call_id:'call-read', outcome:'SUCCEEDED', summary:'已读取工作台实现，保留原有权限与会话边界'}),
    fixtureEvent(4, 'TOOL_STARTED', {tool_call_id:'call-test', tool_name:'run_tests', input_summary:'工作台交互与事件投影检查'}),
    fixtureEvent(5, 'USAGE', {cost_known:false, money:null})
  ];
  const oldGet = window.researchos.v2['session.get'];
  window.researchos.v2['session.get'] = async body => {
    const reply = await oldGet(body), s = reply.result;
    if (!s.__workbenchSetup) {
      s.__workbenchSetup = true; s.title='把 ResearchOS 做成智能工作台';
      s.run_status='RUNNING'; s.active_run_id='fixture-run'; s.event_sequence=5;
      s.messages[0].parts=[{text:'让 ResearchOS 的迭代过程看得见。以对话为中心，保留工具调用、变更和验收证据。'}];
      s.messages[1].parts=[{text:'已核对项目与检查点。正在整理工作台：对话在中间，执行轨迹和成果在右侧。\\n\\n本轮保留现有接口和权限检查，完成后分别验证双主题、键盘输入与窄屏布局。'}];
    }
    return reply;
  };
  window.researchos.v2['session.events'] = async body => ({ok:true,completed:true,protocol_status:'COMPLETED',result:{
    events:fixtureEvents.filter(e => BigInt(e.sequence)>BigInt(body.after_sequence || 0)), next_sequence:5}});
  window.researchos.v2['session.list'] = async () => ({ok:true,completed:true,protocol_status:'COMPLETED',result:{items:[
    {session_id:'session-one',title:'把 ResearchOS 做成智能工作台',run_status:'RUNNING'},
    {session_id:'session-old',title:'来源核验与复用记录',run_status:'SETTLED'}],next_cursor:null}});
  const originalSend = window.researchos.v2['session.send'];
  window.researchos.v2['session.send'] = async body => {
    if (window.__workbenchScenario.rejectSend) return {ok:false,protocol_status:'REJECTED',reason:'FIXTURE_SEND_REJECTED'};
    return originalSend(body);
  };
  addEventListener('DOMContentLoaded', () => {
    const badge = document.createElement('div'); badge.textContent='开发界面夹具 · 非真实运行回执';
    badge.style.cssText='position:fixed;bottom:0;right:0;z-index:9999;background:#183c30;color:white;padding:3px 9px;font:11px Segoe UI,sans-serif;pointer-events:none';
    document.body.append(badge);
  });
`;

async function main() {
  let handler;
  const scripts = [];
  const fixture = await installFixture({ route: async (_pattern, cb) => { handler = cb; },
    addInitScript: async (fn, arg) => scripts.push('(' + fn.toString() + ')(' + JSON.stringify(arg) + ');') }, { native: true });
  const javascript = scripts.join('\n') + override;
  server = http.createServer(async (req, res) => {
    const url = new URL(req.url, 'http://127.0.0.1:' + server.address().port);
    if (url.pathname === '/__fixture.js') return response(res, 200, javascript, 'text/javascript');
    if(url.pathname.endsWith('/events/stream')) {
      res.writeHead(200,{'content-type':'text/event-stream','cache-control':'no-cache'});res.write(': fixture heartbeat\n\n');
      const heartbeat=setInterval(()=>res.write(': fixture heartbeat\n\n'),5000);
      res.on('close',()=>clearInterval(heartbeat));return;
    }
    if (url.pathname.endsWith('/profile')) return response(res, 200, JSON.stringify({project_id:projectId,name:'ResearchOS',revision:7}));
    if (url.pathname.endsWith('/progress')) return response(res, 200, JSON.stringify({project_id:projectId,plan_revision:7,as_of_event_sequence:5,
      stages:[{stage:'discovery',accepted:2,planned:2,active:0,pending_review:0,blocked:0},
        {stage:'verification',accepted:1,planned:2,active:1,pending_review:0,blocked:0},
        {stage:'experiment',accepted:0,planned:1,active:0,pending_review:1,blocked:0},
        {stage:'review',accepted:0,planned:1,active:0,pending_review:0,blocked:0}]}));
    const serveAsset = () => {
      const relative = url.pathname.startsWith('/assets/') ? url.pathname.slice(1) : 'index.html';
      const file = path.resolve(dist, relative);
      if (!file.startsWith(path.resolve(dist) + path.sep) || !fs.existsSync(file)) return response(res,404,'');
      if (relative === 'index.html') return response(res,200,fs.readFileSync(file,'utf8').replace('<head>','<head><script src="/__fixture.js"></script>'),'text/html');
      response(res,200,fs.readFileSync(file),file.endsWith('.css')?'text/css':file.endsWith('.js')?'text/javascript':'application/octet-stream');
    };
    try {
      await handler({ request:() => ({url:() => url.href,method:() => req.method}),
        fulfill:async ({status=200,body='',contentType='application/json'}) => response(res,status,body,contentType),
        continue:async () => serveAsset(), abort:async () => response(res,403,'fixture blocked') });
    } catch (error) { response(res,500,JSON.stringify({error:String(error)})); }
  });
  await new Promise(resolve => server.listen(0,'127.0.0.1',resolve));
  const origin='http://127.0.0.1:'+server.address().port;
  window=new BrowserWindow({width:1440,height:1000,show:false,useContentSize:true,
    webPreferences:{offscreen:true,contextIsolation:true,nodeIntegration:false,sandbox:true,partition:'workbench-fixture-'+Date.now()}});
  window.webContents.session.webRequest.onBeforeRequest((details,callback) => {
    const allowed=details.url.startsWith(origin+'/');
    if (!allowed) report.unexpected.push(details.url);
    callback({cancel:!allowed});
  });
  const pageErrors=[];
  window.webContents.on('console-message',(event) => {if(event.level==='error')pageErrors.push(event.message)});
  report.pageErrors=pageErrors;
  for(const width of (runLabel==='baseline'?[1440]:[1440,1024,768,390,320])) for(const theme of (runLabel==='baseline'?['light']:['light','dark'])) {
    window.setContentSize(width,1000);
    await window.loadURL(origin+'/p/'+projectId+'?theme='+theme);
    await until("document.querySelector('.conversation-transcript') && document.body.innerText.includes('让 ResearchOS 的迭代过程看得见')");
    await new Promise(resolve => setTimeout(resolve,1600));
    const metrics=await evalInPage(`({width:document.documentElement.clientWidth,viewport:innerWidth,scroll:document.documentElement.scrollWidth,theme:document.documentElement.dataset.theme,
      center:Math.round(document.querySelector('.workbench-conversation-pane')?.getBoundingClientRect().width || 0),
      input:!!document.querySelector('textarea[aria-label="会话消息"]')})`);
    check(width+'-'+theme+'-no-overflow',metrics.scroll<=metrics.width,metrics);
    check(width+'-'+theme+'-input',metrics.input,metrics);
    check(width+'-'+theme+'-theme',metrics.theme===theme,metrics);
    const header=await evalInPage(`([...document.querySelectorAll('.topbar button')].filter(el=>el.getClientRects().length).map(el=>({left:el.getBoundingClientRect().left,right:el.getBoundingClientRect().right,width:el.getBoundingClientRect().width})))`);
    check(width+'-'+theme+'-header-in-viewport',header.every(box=>box.left>=0&&box.right<=metrics.width+1),header);
    if(width===1440&&runLabel!=='baseline') check(theme+'-conversation-width',metrics.center>=560,metrics);
    await shot(runLabel+'-'+width+'-'+theme);
  }
  if(runLabel==='baseline') {report.status='PASS';return}
  window.setContentSize(1440,1000);
  await window.loadURL(origin+'/p/'+projectId+'?theme=dark');
  await until("!!document.querySelector('textarea[aria-label=\"会话消息\"]')");
  await new Promise(resolve => setTimeout(resolve,1600));
  const beforeCalls=await evalInPage('window.__frontendFixtureCalls.length');
  await evalInPage(`(() => {const t=document.querySelector('textarea[aria-label="会话消息"]');const set=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set;set.call(t,'检查这次界面更新的工具调用与测试结果。');t.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await new Promise(resolve=>setTimeout(resolve,150));
  await evalInPage(`document.querySelector('textarea[aria-label="会话消息"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,isComposing:true}))`);
  await new Promise(resolve=>setTimeout(resolve,100));
  check('IME-enter-does-not-send',await evalInPage("!window.__frontendFixtureCalls.some(c=>c.name==='session.send')"));
  await evalInPage(`document.querySelector('textarea[aria-label="会话消息"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,shiftKey:true}))`);
  await new Promise(resolve=>setTimeout(resolve,100));
  check('shift-enter-does-not-send',await evalInPage("!window.__frontendFixtureCalls.some(c=>c.name==='session.send')"));
  await evalInPage(`document.querySelector('textarea[aria-label="会话消息"]').dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',bubbles:true,ctrlKey:true}))`);
  await until("window.__frontendFixtureCalls.some(c=>c.name==='session.send')");
  check('send-retains-real-session-api',await evalInPage("window.__frontendFixtureCalls.some(c=>c.name==='session.send' && c.body.text.includes('这次界面更新'))"),beforeCalls);
  await evalInPage(`(()=>{window.__workbenchScenario.rejectSend=true;const t=document.querySelector('textarea[aria-label="会话消息"]');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(t,'发送失败时保留这份草稿');t.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await new Promise(resolve=>setTimeout(resolve,150));
  await evalInPage(`document.querySelector('.session-composer').requestSubmit()`);
  await until("document.body.innerText.includes('FIXTURE_SEND_REJECTED')");
  check('failed-send-preserves-draft',await evalInPage("document.querySelector('textarea[aria-label=\"会话消息\"]').value==='发送失败时保留这份草稿'"));
  await shot(runLabel+'-failure-draft');
  await evalInPage(`document.querySelector('.workbench-sessions-disclosure').open=true;document.querySelector('.workbench-session-pane .panel details').open=true`);
  await new Promise(resolve=>setTimeout(resolve,150));
  await evalInPage(`Array.from(document.querySelectorAll('.workbench-session-pane button')).find(el=>el.textContent==='创建会话').click()`);
  await until("!!document.querySelector('.conversation-welcome')");
  await evalInPage(`(()=>{const t=document.querySelector('textarea[aria-label="会话消息"]');Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value').set.call(t,'保留我的目标与约束');t.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  await new Promise(resolve=>setTimeout(resolve,150));
  await evalInPage("document.querySelector('.conversation-starters button').click()");
  await new Promise(resolve=>setTimeout(resolve,100));
  check('suggestion-preserves-existing-draft',await evalInPage("document.querySelector('textarea[aria-label=\"会话消息\"]').value.startsWith('保留我的目标与约束') && document.querySelector('textarea[aria-label=\"会话消息\"]').value.includes('梳理项目现状')"));
  check('old-session-events-not-visible',await evalInPage("!document.querySelector('.activity-timeline')"));
  await shot(runLabel+'-new-session');
  const preservedDraft=await evalInPage("document.querySelector('textarea[aria-label=\"会话消息\"]').value");
  await evalInPage(`Object.defineProperty(navigator,'onLine',{configurable:true,get:()=>false});dispatchEvent(new Event('offline'))`);
  await until("document.querySelector('.session-composer button[type=submit]').disabled");
  check('offline-disables-send',await evalInPage("document.querySelector('.session-composer button[type=submit]').disabled"));
  check('offline-retains-draft',await evalInPage("document.querySelector('textarea[aria-label=\"会话消息\"]').value")===preservedDraft);
  await shot(runLabel+'-offline');
  window.webContents.setZoomFactor(2);
  await new Promise(resolve=>setTimeout(resolve,250));
  const zoom=await evalInPage('({width:document.documentElement.clientWidth,viewport:innerWidth,scroll:document.documentElement.scrollWidth})');
  check('200-percent-zoom-no-overflow',zoom.scroll<=zoom.width,zoom);
  await shot(runLabel+'-zoom-200');
  window.webContents.setZoomFactor(1);
  check('no-unexpected-api',fixture.unexpected.length===0,fixture.unexpected);
  check('no-external-network',report.unexpected.length===0,report.unexpected);
  check('no-renderer-console-errors',pageErrors.length===0,pageErrors);
  report.status='PASS';
}
app.whenReady().then(main).catch(async error=>{report.status='FAIL';report.error=error.stack||String(error);if(window&&!window.isDestroyed())try{await shot(runLabel+'-failure-state')}catch{}}).finally(()=>{
  fs.writeFileSync(path.join(outputRoot,'report.json'),JSON.stringify(report,null,2));
  process.stdout.write(JSON.stringify({status:report.status,checks:report.checks.length,screenshots:report.screenshots.length,error:report.error||null})+'\n');
  if(window&&!window.isDestroyed()) window.destroy();
  if(server) server.close();
  app.exit(report.status==='PASS'?0:1);
});
