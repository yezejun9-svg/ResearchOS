'use strict';
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const playwright = require(process.env.RESEARCHOS_PLAYWRIGHT_MODULE || 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/Lib/site-packages/playwright/driver/package');
const root = path.resolve(__dirname, '../../..');
const input = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = path.resolve(process.argv[3]), choice = process.argv[4];
const report = {schema:'researchos.electron-original-permission.v1',status:'EXECUTING',decision:choice,checks:[],screenshots:[],limitations:['Model responses and folder choice are explicit FIXTURE inputs; SDK/Host/HTTP/physical files are real.','No construction independent acceptance or LIVE provider qualification.']};
let app,page;
function check(id,okay,detail=null){report.checks.push({id,status:okay?'PASS':'FAIL',detail});if(!okay)throw new Error('failed assertion: '+id);}
async function capture(name){const file=path.join(out,name+'.png');await page.screenshot({path:file,fullPage:true});report.screenshots.push({file:name+'.png',sha256:createHash('sha256').update(fs.readFileSync(file)).digest('hex')});}
async function waitRun(statuses){
 const deadline=Date.now()+30000;
 while(Date.now()<deadline){
  const run=await page.evaluate(async({project,run})=>{const response=await fetch(`/v1/projects/${project}/runs/${run}`,{cache:'no-store'});return response.json();},{project:input.project_id,run:input.original_run_id});
  if(statuses.includes(run.status)){report.run_before_file_assertion=run;return;}
  await new Promise(resolve=>setTimeout(resolve,100));
 }
 throw new Error('Original run did not reach '+statuses.join('/'));
}
async function main(){
 const source=path.join(input.workspace_root,input.source_path),initial=fs.readFileSync(source);
 const relative=path.relative(path.join(root,'.local'),input.workspace_root);
 check('ISOLATED_ORIGINAL_ACTION',!relative.startsWith('..')&&!path.isAbsolute(relative)&&input.measurement_mode==='FIXTURE'&&input.external_provider_calls===0);
 check('ACTUAL_LOOPBACK_SDK_BEFORE_UI',input.loopback_model_calls_before_ui===2);
 const errors=[];
 app=await playwright._electron.launch({executablePath:path.join(root,'apps/desktop/node_modules/electron/dist/electron.exe'),args:[path.join(root,'apps/desktop')],cwd:root,env:process.env,timeout:40000});
 page=await app.firstWindow();page.on('pageerror',e=>errors.push(String(e)));
 await page.locator('#main h1').waitFor();
 await page.waitForFunction(()=>!document.querySelector('#main .loading-state'));
 await page.goto('ros-app://desktop/p/'+input.project_id,{waitUntil:'domcontentloaded'});
 await page.locator('.session-picker li button').first().click();
 const panel=page.locator('section.panel').filter({has:page.getByRole('heading',{name:'工具等待授权',exact:true})});
 await panel.waitFor();
 const allow=panel.getByRole('button',{name:'允许本次',exact:true});
 check('PERMISSION_VISIBLE_WITH_FROZEN_PATH',(await panel.textContent()).includes('source.txt'));
 check('ALLOW_DISABLED_UNTIL_EXACT_ARGUMENT_CONTENT',await allow.isDisabled());
 check('DENY_DOES_NOT_REQUIRE_ALLOW',await panel.getByRole('button',{name:'拒绝',exact:true}).isEnabled());
 await panel.getByRole('button',{name:'查看本次工具参数',exact:true}).click();
 check('ARTIFACT_METADATA_ALONE_NOT_APPROVAL',await allow.isDisabled());
 await panel.getByRole('button',{name:'受控预览',exact:true}).click();
 await panel.getByRole('link',{name:'下载已核对的内容',exact:true}).waitFor();
 await page.waitForFunction(()=>[...document.querySelectorAll('button')].some(b=>b.textContent==='允许本次'&&!b.disabled));
 const argumentsText=await panel.locator('.artifact-preview .preview-text').textContent();
 check('SEALED_ARGUMENT_PREVIEW_MATCHES_ACTION',JSON.parse(argumentsText).content===input.expected_written_text&&JSON.parse(argumentsText).expected_hash==='sha256:'+createHash('sha256').update(initial).digest('hex'));
 check('WAITING_HAS_NO_PHYSICAL_WRITE',fs.readFileSync(source).equals(initial));
 await capture('original-action-before-'+choice.toLowerCase());
 await panel.getByRole('button',{name:choice==='ALLOW_ONCE'?'允许本次':'拒绝',exact:true}).click();
 await panel.waitFor({state:'detached'});
 if(choice==='ALLOW_ONCE'){
  await waitRun(['SETTLED']);
  const actual=fs.readFileSync(source),expected=Buffer.from(input.expected_written_text);
  check('ALLOW_WRITES_EXACT_BYTES',actual.equals(expected),{actual_bytes:actual.toString('base64'),expected_bytes:expected.toString('base64')});
 }else{
  // Verify replay refusal only after the original Run has settled its cancellation.
  await waitRun(['CANCELLED','FAILED']);
  check('DENY_PRESERVES_PHYSICAL_BYTES',fs.readFileSync(source).equals(initial));
 }
 const observed=await page.evaluate(async({project,run,task})=>{
  const get=async p=>(await fetch(`/v1/projects/${project}/${p}`)).json();
  return {run:await get('runs/'+run),task:await get('tasks/'+task),session:await window.researchos.v2['session.get']({}),events:await window.researchos.v2['session.events']({after_sequence:0,limit:200})};
 },{project:input.project_id,run:input.original_run_id,task:input.original_task_id});
 report.observed=observed;
 check('SAME_ORIGINAL_RUN_AND_TASK',observed.run.id===input.original_run_id&&observed.task.id===input.original_task_id&&observed.task.active_run_id===input.original_run_id);
 check('PENDING_PERMISSION_CLOSED',observed.session.ok&&observed.session.result.pending_permissions.length===0);
 const events=observed.events.result?.events||[];
 check('ONE_REQUIRED_ONE_RESOLVED_EVENT',events.filter(e=>e.kind==='PERMISSION_REQUIRED').length===1&&events.filter(e=>e.kind==='PERMISSION_RESOLVED').length===1);
 const resolved=events.find(e=>e.kind==='PERMISSION_RESOLVED');
 check('DECISION_SEALED_AND_CONSUMED_ONCE',resolved.payload.decision===choice&&resolved.payload.consumed===(choice==='ALLOW_ONCE')&&resolved.payload.action_digest===input.prompt.action_digest&&resolved.payload.resolution_artifact_ref.entity_type==='Artifact');
 const repeat=await page.evaluate(prompt=>window.researchos.v2['permission.respond']({resource_request_id:prompt.request.id,resource_request_revision:prompt.request.revision,action_digest:prompt.action_digest,decision:'ALLOW_ONCE',reason:'Closed original action replay refusal probe'}),input.prompt);
 check('CLOSED_REQUEST_CANNOT_WRITE_AGAIN',!repeat.ok&&['STALE_REVISION','RESOURCE_BLOCKED'].includes(repeat.error_code||repeat.reason),repeat);
 check('REJECTION_PRESERVES_PHYSICAL_BYTES',fs.readFileSync(source).equals(choice==='ALLOW_ONCE'?Buffer.from(input.expected_written_text):initial));
 check('NO_RENDERER_ERRORS',errors.length===0,errors);
 await capture('original-action-after-'+choice.toLowerCase());report.status='PASS';
}
main().catch(async e=>{report.status='FAIL';report.error=String(e.stack||e);if(page&&!page.isClosed()){try{await capture('failure');}catch{}}}).finally(async()=>{if(app)await app.close();report.finished_at=new Date().toISOString();fs.writeFileSync(path.join(out,'permission.json'),JSON.stringify(report,null,2));process.stdout.write(JSON.stringify({status:report.status,checks:report.checks.length,error:report.error})+'\n');process.exitCode=report.status==='PASS'?0:1;});
