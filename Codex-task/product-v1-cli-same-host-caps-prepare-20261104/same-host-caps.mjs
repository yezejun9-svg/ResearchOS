// Prepared only. Root must register a fresh exact f13 Job scope before execution.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {StringDecoder} from 'node:string_decoder';
import {pathToFileURL,fileURLToPath} from 'node:url';

const HERE=path.dirname(fileURLToPath(import.meta.url));
const TASK=path.dirname(HERE);
const BASE=path.join(TASK,'product-v1-real-electron-harness-prepare-revision-04');
const BASE_SHA='68458e0ff59d091d2481356f19bec7d557a3dc9924ee3f91cc8c47e77b1d450b';
const BUNDLE='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-05-20261104/.local/desktop-v1-build-05';
const CLI='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-03-20261104/.local/cli-v1-artifact-01/bin/researchos.exe';
const CLI_SHA='881e26a2784cab412c21e3f6b3e562d031d9f10479911953a83ef5888a7a4da7';
const MANIFEST_SHA='b630a2222faeed08c98259bfadd3c4d5196be9afec8508bd97ae4a9ec28ab1a9';
const LAUNCH_SHA='63c0b49e5f237f8137baf50909af3269106f697f4a5b98d7307e7650dd4912af';
const CONTROL_SHA='9874ea065e12822683e45e71350cd7c9874cfc87346c0625c826eda1094e0694';
const F13='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c';
const SHA=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const need=(ok,code)=>{if(!ok)throw Object.assign(Error(code),{code});};
const pin=(p,h)=>need(/^[a-f0-9]{64}$/.test(h||'')&&SHA(p)===h,'PIN_MISMATCH:'+path.basename(p));
const same=(a,b)=>path.resolve(a).toLowerCase()===path.resolve(b).toLowerCase();
const inside=(a,b)=>{const r=path.relative(a,b);return r&&!r.startsWith('..'+path.sep)&&r!=='..'&&!path.isAbsolute(r);};
const safe=s=>String(s).replace(/Bearer\s+[^\s"']+/gi,'Bearer [REDACTED]')
  .replace(/((?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|credential)(?:["'])?\s*[=:]\s*)(?:"(?:\\.|[^"\\\r\n])*"|'(?:\\.|[^'\\\r\n])*'|[^\s,;}]+)/gi,'$1"[REDACTED]"').slice(0,16384);
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function within(work,ms,label){let timer;try{return await Promise.race([work(),new Promise((_,reject)=>{timer=setTimeout(()=>reject(Object.assign(Error(label),{code:label})),ms);})]);}finally{clearTimeout(timer);}}
function validateSDK(sdk){
  pin(sdk.inventory_path,sdk.inventory_sha256);
  const inv=JSON.parse(fs.readFileSync(sdk.inventory_path,'utf8')),rows=[];
  need(inv.schema==='researchos.public-sdk-inventory/1'&&inv.version==='1.62.1'&&same(inv.root,sdk.root),'SDK_INVENTORY');
  function walk(dir){for(const e of fs.readdirSync(dir,{withFileTypes:true})){const p=path.join(dir,e.name);need(!fs.lstatSync(p).isSymbolicLink(),'SDK_ALIAS');if(e.isDirectory())walk(p);else{need(e.isFile(),'SDK_SPECIAL');rows.push({path:path.relative(sdk.root,p).replaceAll('\\','/'),sha256:SHA(p),bytes:fs.statSync(p).size});}}}
  walk(sdk.root);const order=a=>a.map(({path,sha256,bytes})=>({path,sha256,bytes})).sort((a,b)=>a.path.localeCompare(b.path));
  need(JSON.stringify(order(rows))===JSON.stringify(order(inv.files)),'SDK_DRIFT');
}
function publicDiscovery(file,core,env){
  const info=fs.lstatSync(file);need(info.isFile()&&!info.isSymbolicLink()&&info.size<=8192,'DISCOVERY_FILE');
  const d=JSON.parse(fs.readFileSync(file,'utf8'));
  need(Object.keys(d).every(k=>['url','pid','data_dir','host_instance_id','started_at'].includes(k)),'DISCOVERY_METADATA_ONLY');
  const u=new URL(d.url);need(u.protocol==='http:'&&['127.0.0.1','[::1]'].includes(u.hostname)&&!u.username&&!u.password,'NUMERIC_LOOPBACK_DISCOVERY');
  need(d.pid===core.pid&&d.host_instance_id===core.host_id&&same(d.data_dir,env.RESEARCHOS_DATA_DIR),'DISCOVERY_CORE_IDENTITY');
  return {url:d.url,pid:d.pid,data_dir:d.data_dir,host_instance_id:d.host_instance_id};
}

export async function run(scopeFile,expectedSHA){
  need(process.platform==='win32','WINDOWS_REQUIRED');pin(scopeFile,expectedSHA);
  const scope=JSON.parse(fs.readFileSync(scopeFile,'utf8'));
  need(scope.schema==='researchos.same-host-cli-caps/1'&&scope.status==='ROOT_APPROVED_SINGLE_CAPS','PREPARATION_ONLY');
  need(scope.root_supervision?.controller_sha256===F13&&scope.root_supervision?.required===true,'ROOT_F13_REQUIRED');
  need(scope.budget?.caps_invocations===1&&scope.budget?.task_submissions===0&&scope.budget?.model_requests===0&&scope.budget?.automatic_retries===0,'FIXED_CAPS_ONLY');
  need(scope.deadlines.flow_ms>0&&scope.deadlines.flow_ms<=90000&&scope.deadlines.cli_ms>0&&scope.deadlines.cli_ms<=30000&&scope.deadlines.close_ms>0&&scope.deadlines.close_ms<=30000&&scope.root_supervision.outer_deadline_ms>scope.deadlines.flow_ms+scope.deadlines.close_ms+10000,'BOUNDED_ROOT_SCOPE');
  need(/^[A-Za-z0-9._-]{24,128}$/.test(scope.scope_nonce||''),'SCOPE_NONCE');
  pin(process.execPath,scope.node.sha256);pin(path.join(HERE,'same-host-caps.mjs'),scope.runner_sha256);
  pin(path.join(BASE,'real-electron-flow.mjs'),BASE_SHA);pin(path.join(BUNDLE,'launch-development.mjs'),LAUNCH_SHA);
  pin(path.join(BUNDLE,'development-manifest.json'),MANIFEST_SHA);pin(CLI,CLI_SHA);
  const {makeEnvironment}=await import(pathToFileURL(path.join(BASE,'real-electron-flow.mjs')).href);
  const launcher=await import(pathToFileURL(path.join(BUNDLE,'launch-development.mjs')).href);
  const bundle=launcher.validateBundle(BUNDLE);
  need(path.isAbsolute(scope.run_root)&&inside(TASK,scope.run_root)&&path.parse(scope.run_root).root.toLowerCase()==='c:\\','FRESH_C_ROOT_REQUIRED');
  launcher.validateStatePath(scope.run_root,bundle.bundle);launcher.checkNativePath(scope.playwright.root);
  for(const k of ['normal_user_profile','normal_app_data','normal_local_app_data'])launcher.checkNativePath(scope.windows[k]);
  validateSDK(scope.playwright);
  need(scope.playwright.version==='1.62.1','SDK_VERSION');
  // Reuse the reviewed R04 explicit environment exactly, replacing only the new
  // run root and fixed build05 paths. No R04 run()/picker/project/submit is called.
  need(same(scope.bundle.root,BUNDLE),'FIXED_BUILD05');
  const env=Object.freeze(makeEnvironment(scope));
  need(same(env.RESEARCHOS_CLI_DISCOVERY,path.join(scope.run_root,'discovery.json'))&&env.RESEARCHOS_SHARED_HOST_LOCATOR_DISABLED==='1','EXPLICIT_SAME_HOST_DISCOVERY');
  need(!Object.keys(env).some(k=>/^(OPENAI_|ANTHROPIC_|AZURE_|CODEX_|NODE_|HTTP_PROXY$|HTTPS_PROXY$|ALL_PROXY$)/i.test(k)),'NO_AMBIENT_AUTH_OR_PROXY');
  fs.mkdirSync(scope.run_root);
  for(const d of ['receipts','tmp'])fs.mkdirSync(path.join(scope.run_root,d));
  const write=(n,v)=>fs.writeFileSync(path.join(scope.run_root,'receipts',n),JSON.stringify(v,null,2)+'\n',{flag:'wx'});
  write('CONSUMED.json',{scope_sha256:expectedSHA,scope_nonce:scope.scope_nonce,automatic_retry:false,caps_budget:1,task_budget:0,model_budget:0});
  const state={status:'RUNNING',scope_sha256:expectedSHA,bundle_manifest_sha256:MANIFEST_SHA,cli_sha256:CLI_SHA,
    caps_invocations:0,task_submissions:0,model_requests:0,formal_increment:0,main_reports:[],
    identity_basis:'APP_INTERNAL_DISCOVERY_AND_NATIVE_BOOTSTRAP_CHECKS_NOT_NETWORK_OR_PIPE_PID_INTERCEPTION',
    independent_native_server_pid_observed:false,root_job_stop_proved:'EXTERNAL_ROOT_F13_ONLY',
    close:{attempted:false,app_close_resolved:false}};
  const until=Date.now()+scope.deadlines.flow_ms;
  const guard=()=>need(Date.now()<until,'FLOW_DEADLINE');
  let app=null,cli=null,cliClosed=false;
  function observe(text){if(!text.startsWith('ROS_DESKTOP_REPORT '))return;try{const r=JSON.parse(text.slice(19));if(r.event==='ready_to_show'){
    const selected={event:r.event,pid:r.pid,host_health:r.host_health,host_url:r.host_url,management_state:r.management_state,
      owned_core_identity:r.owned_core_identity,renderer:{react_root:r.renderer?.react_root,bridge:r.renderer?.bridge},shared_host_locator:{status:r.shared_host_locator?.status}};
    if(!state.main_reports.some(x=>JSON.stringify(x)===JSON.stringify(selected)))state.main_reports.push(selected);
  }}catch{state.malformed_main_report=true;}}
  try{
    const {_electron}=await import(pathToFileURL(path.join(scope.playwright.root,'index.mjs')).href);
    guard();app=await _electron.launch({executablePath:path.join(BUNDLE,'runtime/electron/electron.exe'),args:[path.join(BUNDLE,'apps/desktop')],cwd:BUNDLE,env,timeout:Math.min(45000,until-Date.now())});
    app.on('console',m=>observe(m.text()));
    const desktop=app.process();state.playwright_launcher_pid=desktop?.pid||null;
    const decoder=new StringDecoder('utf8');let pending='';
    desktop?.stdout?.on('data',b=>{pending+=decoder.write(b);while(pending.includes('\n')){const i=pending.indexOf('\n');observe(pending.slice(0,i).replace(/\r$/,''));pending=pending.slice(i+1);}if(pending.length>65536){state.main_stream_overflow=true;pending='';}});
    desktop?.stderr?.on('data',()=>{});
    const page=await within(()=>app.firstWindow(),Math.min(30000,until-Date.now()),'FIRST_WINDOW_TIMEOUT');
    await page.locator('#root').waitFor({state:'visible',timeout:Math.min(15000,until-Date.now())});
    need(page.url().startsWith('ros-app://desktop/'),'ACTUAL_REACT_PAGE');
    while(!state.main_reports.length){guard();await pause(100);}
    need(state.main_reports.length===1&&!state.malformed_main_report&&!state.main_stream_overflow,'ONE_MAIN_IDENTITY');
    const ready=state.main_reports[0],core=ready.owned_core_identity;
    need(ready.management_state==='READY'&&ready.host_health==='UP'&&ready.renderer.react_root&&ready.renderer.bridge&&ready.shared_host_locator.status==='DISABLED','OWNED_CORE_READY');
    need(core&&Number.isSafeInteger(core.pid)&&core.pid>0&&/^\d+$/.test(core.created_ns)&&core.image_sha256===CONTROL_SHA&&/^host-[a-f0-9]{12}$/.test(core.host_id),'ORIGINAL_CORE_IDENTITY');
    state.owned_core_identity=core;
    const before=publicDiscovery(env.RESEARCHOS_CLI_DISCOVERY,core,env);need(before.url===ready.host_url,'READY_DISCOVERY_URL');
    write('owned-core-and-discovery.before.json',{core,discovery:before});
    guard();state.caps_invocations=1;
    const parts={stdout:[],stderr:[]},sizes={stdout:0,stderr:0};let overflow=false,spawnError=null;
    const collect=k=>b=>{const left=1048576-sizes[k];sizes[k]+=b.length;if(left>0)parts[k].push(Buffer.from(b.subarray(0,left)));if(sizes[k]>1048576)overflow=true;};
    cli=spawn(CLI,['harness','caps'],{cwd:scope.run_root,env,shell:false,windowsHide:true,stdio:['ignore','pipe','pipe']});
    state.original_cli_pid=cli.pid||null;cli.stdout.on('data',collect('stdout'));cli.stderr.on('data',collect('stderr'));cli.on('error',e=>{spawnError=e.code||e.name;});
    const closed=await within(()=>new Promise(resolve=>cli.once('close',(code,signal)=>{cliClosed=true;resolve({code,signal});})),Math.min(scope.deadlines.cli_ms,until-Date.now()),'CAPS_CLOSE_UNCONFIRMED');
    state.cli_close=closed;
    const stdout=Buffer.concat(parts.stdout),stderr=Buffer.concat(parts.stderr);
    write('cli-streams.json',{stdout_bytes:sizes.stdout,stdout_sha256:hash(stdout),stdout_text:safe(new TextDecoder('utf8',{fatal:true}).decode(stdout)),stderr_bytes:sizes.stderr,stderr_sha256:hash(stderr),stderr_text:safe(new TextDecoder('utf8',{fatal:true}).decode(stderr)),overflow,spawn_error:spawnError});
    need(!spawnError&&!overflow&&closed.code===0&&!closed.signal,'CAPS_EXIT_UNCONFIRMED');
    const report=JSON.parse(new TextDecoder('utf8',{fatal:true}).decode(stdout));
    need(report.command==='harness caps'&&report.status==='COMPLETED'&&report.completion_scope==='HOST_QUERY'&&report.exit_code===0,'CAPS_JSON_OUTCOME');
    need(report.response?.api_version==='harness.v1'&&report.response?.data?.harness_id==='codex'&&typeof report.response.data.can_submit==='boolean'&&Array.isArray(report.response.data.reason_codes),'CAPABILITIES_DATA');
    const hostRefs=[],nativePids=[];
    function refs(v){if(!v||typeof v!=='object')return;for(const [k,x]of Object.entries(v)){need(!/^(authorization|credential|credential_value|access_token|refresh_token|api_key|password)$/i.test(k),'CLI_SECRET_OUTPUT_REFUSED');if(['host_id','host_instance_id'].includes(k))hostRefs.push(x);if(['native_server_pid','host_pid'].includes(k))nativePids.push(x);refs(x);}}
    refs(report);need(hostRefs.every(x=>x===core.host_id)&&nativePids.every(x=>x===core.pid),'CLI_REPORTED_HOST_MISMATCH');
    state.cli_output_identity_fields={host_ids:hostRefs,native_or_host_pids:nativePids};
    state.capabilities={can_submit:report.response.data.can_submit,reason_codes:report.response.data.reason_codes};
    write('cli-caps.json',report);
    const after=publicDiscovery(env.RESEARCHOS_CLI_DISCOVERY,core,env);need(JSON.stringify(before)===JSON.stringify(after),'HOST_CHANGED_DURING_CAPS');
    write('owned-core-and-discovery.after.json',{core,discovery:after});
    state.status='SAME_HOST_CLI_CAPS_OBSERVED_PENDING_OUTER_JOB_STOP';
  }catch(e){state.status='BLOCKED_OR_FAILED_NO_RETRY';state.error={code:safe(e.code||e.name),message:safe(e.message)};}
  finally{
    state.cli_original_handle_close_observed=cliClosed;
    if(app){state.close.attempted=true;try{await within(()=>app.close(),scope.deadlines.close_ms,'APP_CLOSE_UNCONFIRMED_ROOT_JOB_REQUIRED');state.close.app_close_resolved=true;}catch(e){state.close.reason=safe(e.code||e.message);}}
    state.close.owned_core_exit='REQUIRES_ROOT_ORIGINAL_JOB_AND_PROCESS_ACCOUNTING';
    if(!state.close.app_close_resolved||!cliClosed)state.status='BLOCKED_OR_FAILED_NO_RETRY';
    write('result.json',state);console.log(JSON.stringify({status:state.status,result:path.join(scope.run_root,'receipts/result.json'),caps_invocations:state.caps_invocations,task_submissions:0,model_requests:0,formal_increment:0,requires_outer_job_stop_proof:true}));
  }
  return state;
}
if(process.argv[1]&&same(process.argv[1],fileURLToPath(import.meta.url))){
  const a=process.argv.slice(2);if(a.length!==4||a[0]!=='--scope'||a[2]!=='--scope-sha256'){console.error('PREPARATION_ONLY: Root exact f13 scope required');process.exitCode=2;}
  else{try{const r=await run(path.resolve(a[1]),a[3]);if(r.status!=='SAME_HOST_CLI_CAPS_OBSERVED_PENDING_OUTER_JOB_STOP')process.exitCode=2;}catch(e){console.error(safe(e.code||e.message));process.exitCode=2;}}
}
