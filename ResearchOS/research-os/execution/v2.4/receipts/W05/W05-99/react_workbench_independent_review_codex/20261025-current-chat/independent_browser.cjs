'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE);
const [url,wt,out]=process.argv.slice(2);
const {installFixture,projectId}=require(path.join(wt,'tests/ui/frontend-redesign-fixture.cjs'));
fs.mkdirSync(out,{recursive:false});
const report={kind:'INDEPENDENT_BROWSER_NATIVE_SHAPED_FIXTURE',checks:[],screenshots:[],limitations:['No native Desktop or provider launched; isolated intercept-only bridge shape.']};
function check(name,value,detail){report.checks.push({name,status:value?'PASS':'FAIL',detail});assert.ok(value,name);}
async function shot(page,name){const file=path.join(out,name+'.png');await page.screenshot({path:file,fullPage:true});report.screenshots.push({path:file,sha256:crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex')});}
async function main(){const browser=await chromium.launch({headless:true});try{
 for(const width of [320,1440]){
 const context=await browser.newContext({viewport:{width,height:900}}),page=await context.newPage(),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 const fixture=await installFixture(page,{native:true,qualificationState:'AWAITING_CONFIRMATION'});
 await page.goto(url+'/p/'+projectId,{waitUntil:'domcontentloaded'});
 await page.getByRole('heading',{name:'河流污染证据核对',exact:true}).waitFor();
 await page.getByText('当前可写',{exact:true}).waitFor();
 check(width+'-writer-is-status',await page.getByRole('button',{name:'当前可写',exact:true}).count()===0);
 check(width+'-overflow',await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
 const opener=width===320?page.getByRole('button',{name:'打开导航',exact:true}):page.getByRole('button',{name:'打开阶段进度',exact:true});
 await opener.click();
 const region=page.locator(width===320?'.sidebar.drawer-open':'.progress-rail.drawer-open');
 check(width+'-drawer-focus',await region.evaluate(el=>el.contains(document.activeElement)));
 await page.keyboard.press('Shift+Tab');
 check(width+'-focus-trap-reverse',await region.evaluate(el=>el.contains(document.activeElement)));
 await page.keyboard.press('Tab');
 check(width+'-focus-trap-forward',await region.evaluate(el=>el.contains(document.activeElement)));
 await page.keyboard.press('Escape');
 check(width+'-escape-restores-opener',await opener.evaluate(el=>el===document.activeElement));
 if(width===320)await page.getByRole('button',{name:'打开导航'}).click();
 await page.getByRole('link',{name:'研究周期',exact:true}).click();
 await page.getByRole('heading',{name:'选择研究周期',exact:true,level:1}).waitFor();
 check(width+'-cycle-route',new URL(page.url()).pathname.endsWith('/cycles'));
 await page.goBack();await page.getByRole('heading',{name:'河流污染证据核对',exact:true}).waitFor();
 check(width+'-history-back',new URL(page.url()).pathname==='/p/'+projectId);
 await page.getByRole('button',{name:'切换为深色主题'}).click();
 await page.waitForFunction(()=>document.documentElement.dataset.theme==='dark');
 check(width+'-dark-theme',await page.locator('html').getAttribute('data-theme')==='dark');
 await shot(page,'native-'+width+'-dark');
 await page.getByRole('button',{name:'切换为浅色主题'}).click();
 await page.waitForFunction(()=>document.documentElement.dataset.theme==='light');
 if(width===1440){
 const confirm=page.getByRole('button',{name:'明确确认一次调用',exact:true});
 await confirm.waitFor();check('confirmation-visible',await confirm.isEnabled());
 await page.evaluate(()=>{window.__reviewConfirmCalls=0;window.researchos.desktop.qualificationConfirm=async()=>{window.__reviewConfirmCalls++;return {ok:false,reason:'INDEPENDENT_EXPECTED_REFUSAL'}}});
 page.once('dialog',d=>d.dismiss());await confirm.click();
 check('dismiss-no-bridge-dispatch',await page.evaluate(()=>window.__reviewConfirmCalls===0));
 page.once('dialog',d=>d.accept());await confirm.click();
 await page.getByRole('alert').filter({hasText:'INDEPENDENT_EXPECTED_REFUSAL'}).waitFor();
 check('explicit-confirm-dispatch-once',await page.evaluate(()=>window.__reviewConfirmCalls===1));
 check('refusal-visible-not-success',await page.getByText('当前模型已完成一次有界资格调用').count()===0);
 const composer=page.getByRole('textbox',{name:'会话消息'});
 await page.evaluate(()=>{window.__reviewSend=window.researchos.v2['session.send'];window.researchos.v2['session.send']=async()=>({ok:true,completed:false,protocol_status:'UNKNOWN'})});
 await composer.fill('保留此未知结果草稿');await page.getByRole('button',{name:'发送',exact:true}).click();
 await page.getByRole('alert').filter({hasText:'UNKNOWN'}).waitFor();
 check('unknown-keeps-draft',await composer.inputValue()==='保留此未知结果草稿');
 await page.evaluate(()=>window.researchos.v2['session.send']=window.__reviewSend);
 await composer.fill('独立复核的待处理消息');await page.getByRole('button',{name:'发送',exact:true}).click();
 await page.getByText('1 条命令等待处理。',{exact:true}).waitFor();
 check('pending-visible',await composer.inputValue()==='');
 await shot(page,'native-pending-confirmation');
 await page.evaluate(()=>{const old=window.researchos.desktop.openSession;window.researchos.desktop.openSession=async id=>{const reply=await old(id);reply.result.writer={client_id:'other-client',expires_at:'2000-01-01T00:00:00Z'};return reply}});
 await page.locator('.session-picker button').first().click();
 await page.getByRole('button',{name:'在此继续',exact:true}).waitFor();
 await composer.fill('只读不可发送');check('expired-writer-disables-send',await page.getByRole('button',{name:'发送',exact:true}).isDisabled());
 check('expired-writer-no-current-write-status',await page.getByText('当前可写',{exact:true}).count()===0);
 }
 check(width+'-no-page-errors',errors.length===0,errors);check(width+'-no-network-fallthrough',fixture.unexpected.length===0,fixture.unexpected);
 await shot(page,'native-'+width+'-light');await context.close();
 }
 const ctx=await browser.newContext({viewport:{width:1440,height:900}}),page=await ctx.newPage();
 const fixture=await installFixture(page);
 await page.goto(url+'/p/'+projectId);await page.getByLabel('访问令牌').fill('independent-disposable-fixture');await page.getByRole('button',{name:'打开工作台'}).click();
 await page.getByRole('heading',{name:'城市河流研究',exact:true,level:1}).waitFor();
 check('browser-native-controls-absent',await page.getByRole('textbox',{name:'会话消息'}).count()===0);
 check('browser-goals-tasks-acceptance-distinct',await page.getByRole('heading',{name:'当前目标',exact:true}).count()===1 && await page.getByRole('heading',{name:'当前推进',exact:true}).count()===1 && await page.getByText('执行结果不等于业务验收。',{exact:true}).count()===1);
 await page.getByRole('link',{name:'研究周期',exact:true}).click();await page.getByRole('heading',{name:'选择研究周期',exact:true,level:1}).waitFor();await page.goBack();await page.getByRole('heading',{name:'城市河流研究',exact:true,level:1}).waitFor();
 await page.locator('.project-switch').click();await page.getByRole('heading',{name:'项目入口',exact:true,level:1}).waitFor();
 check('browser-project-switch',new URL(page.url()).pathname==='/');
 check('browser-no-fallthrough',fixture.unexpected.length===0,fixture.unexpected);await ctx.close();
 const errctx=await browser.newContext(),ep=await errctx.newPage();const ef=await installFixture(ep,{native:true,profileError:true});await ep.goto(url+'/p/'+projectId);await ep.getByRole('alert').filter({hasText:'部分项目资料尚未读取'}).waitFor();check('partial-error-retry-accessible',await ep.getByRole('button',{name:'重新读取',exact:true}).count()>0);await shot(ep,'partial-profile-error');check('partial-error-no-fallthrough',ef.unexpected.length===0,ef.unexpected);await errctx.close();
 const pairctx=await browser.newContext(),pair=await pairctx.newPage();await pair.goto(url+'/pair');await pair.getByRole('heading',{name:'连接研究电脑',exact:true}).waitFor();check('pair-gate-preserved',await pair.getByText('请从电脑复制新的配对链接，再在此浏览器打开。',{exact:true}).count()===1);await pairctx.close();
 report.status='PASS';
 }finally{await browser.close()}}
main().catch(error=>{report.status='FAIL';report.error=error.stack;process.exitCode=1}).finally(()=>{fs.writeFileSync(path.join(out,'report.json'),JSON.stringify(report,null,2));console.log(JSON.stringify({status:report.status,checks:report.checks.length,error:report.error}));});
