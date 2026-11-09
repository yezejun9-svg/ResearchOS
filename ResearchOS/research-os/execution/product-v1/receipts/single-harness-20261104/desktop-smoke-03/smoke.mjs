// Prepared only. Run once under the separately scoped f13 owned Job supervisor.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';

const OWNER=path.dirname(fileURLToPath(import.meta.url));
const BUNDLE='D:/作品集/ResearchOS/research-os/.local/worktrees/product-v1-build-04-20261104/.local/desktop-v1-build-04';
const MANIFEST_SHA='e2b47e1ed96d13fc4552b123f3b1b702fdf919cf204850502c4029a4dac6083b';
const LAUNCH_SHA='63c0b49e5f237f8137baf50909af3269106f697f4a5b98d7307e7650dd4912af';
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const fail=code=>{throw Object.assign(Error(code),{code});};
const writeNew=(file,value)=>fs.writeFileSync(file,JSON.stringify(value,null,2)+'\n',{flag:'wx'});
const kind=e=>({name:e?.name||'Error',code:e?.code||null});
const inside=(root,value)=>{const rel=path.relative(root,value);return rel===''||(!rel.startsWith('..'+path.sep)&&rel!=='..'&&!path.isAbsolute(rel));};

export async function smoke(statePath){
  const launcher=path.join(BUNDLE,'launch-development.mjs');
  if(sha(path.join(BUNDLE,'development-manifest.json'))!==MANIFEST_SHA||sha(launcher)!==LAUNCH_SHA)fail('PINNED_BUNDLE_CHANGED');
  const {validateBundle,buildChildEnv,validateStatePath,validateSmokeReports}=await import(pathToFileURL(launcher).href);
  if([validateBundle,buildChildEnv,validateStatePath,validateSmokeReports].some(v=>typeof v!=='function'))fail('BUNDLE_EXPORTS_CHANGED');
  const checked=validateBundle(BUNDLE);
  const requested=path.resolve(statePath);
  if(path.parse(requested).root.toLowerCase()!=='c:\\'||!inside(OWNER,requested)||requested===OWNER)fail('NEW_C_STATE_REQUIRED');
  const state=validateStatePath(requested,checked.bundle); // nonexistent, no alias, outside bundle
  const capture=path.join(state,'home.png'),resultPath=path.join(state,'SMOKE-RESULT.json');
  const env=buildChildEnv({SystemRoot:'C:\\Windows',WINDIR:'C:\\Windows'},checked.bundle,state,true);
  // Explicit normal Windows profile paths permit normal Codex metadata lookup.
  // No ambient dictionary or auth/config file is read/copied. Electron's actual
  // userData, Host data and discovery remain the fresh state-specific paths.
  Object.assign(env,{
    USERPROFILE:'C:\\Users\\yqyyds',HOME:'C:\\Users\\yqyyds',
    APPDATA:'C:\\Users\\yqyyds\\AppData\\Roaming',LOCALAPPDATA:'C:\\Users\\yqyyds\\AppData\\Local',
    PATH:['C:\\nvm4w\\nodejs','C:\\Users\\yqyyds\\AppData\\Local\\nvm','C:\\Users\\yqyyds\\AppData\\Roaming\\npm',
      'C:\\Users\\yqyyds\\.local\\bin','C:\\Program Files\\Git\\cmd','C:\\Windows\\System32','C:\\Windows'].join(';'),
    ROS_DESKTOP_SMOKE:'1',ROS_DESKTOP_NATIVE_SMOKE:'1',ROS_DESKTOP_CAPTURE_PATH:capture,
  });
  const forbidden=/TOKEN|API.?KEY|PASSWORD|SECRET|PROXY|^NODE_OPTIONS$|^NODE_PATH$/i;
  if(Object.keys(env).some(k=>forbidden.test(k)))fail('ENVIRONMENT_REFUSED');
  fs.mkdirSync(state);
  for(const relative of ['data','electron-user-data','tmp'])fs.mkdirSync(path.join(state,relative),{recursive:true});
  writeNew(path.join(state,'WRAPPER-CONSUMED.json'),{
    status:'SMOKE_CONSUMED_OUTCOME_UNKNOWN',bundle_manifest_sha256:MANIFEST_SHA,launcher_sha256:LAUNCH_SHA,
    environment_keys_only:Object.keys(env).sort(),normal_windows_profile_explicit:true,
    directory_selection_actions:0,project_actions:0,model_submission_actions:0,
    requires_outer_job_stop_proved:true,automatic_retry:false,formal_increment:0,
  });
  let child,spawnError=null;
  const stdout=[],stderr=[],sizes={stdout:0,stderr:0};let overflow=false;
  const collect=(name,parts)=>part=>{
    const remaining=(1<<20)-sizes[name];sizes[name]+=part.length;
    if(remaining>0)parts.push(Buffer.from(part.subarray(0,remaining)));
    if(sizes[name]>1<<20)overflow=true; // Keep draining; never block Electron on a full pipe.
  };
  const base={bundle_manifest_sha256:MANIFEST_SHA,state,capture_path:capture,requires_outer_job_stop_proved:true,
    outer_job_stop_proved:false,automatic_retry:false,formal_increment:0,model_submission_actions:0};
  try{
    child=spawn(path.join(BUNDLE,'runtime/electron/electron.exe'),[path.join(BUNDLE,'apps/desktop')],
      {cwd:BUNDLE,env,shell:false,windowsHide:true,stdio:['ignore','pipe','pipe']});
    child.stdout.on('data',collect('stdout',stdout));child.stderr.on('data',collect('stderr',stderr));
    child.on('error',e=>{spawnError=kind(e);});
    // Original ChildProcess object is retained. No PID/name lookup or kill.
    // The outer reviewed Job owns the total deadline and every descendant.
    const close=await new Promise(resolve=>child.once('close',(code,signal)=>resolve({code,signal})));
    fs.writeFileSync(path.join(state,'electron.stdout.raw'),Buffer.concat(stdout),{flag:'wx'});
    fs.writeFileSync(path.join(state,'electron.stderr.raw'),Buffer.concat(stderr),{flag:'wx'});
    if(spawnError||close.signal||!Number.isInteger(close.code)||overflow)fail('CHILD_CLOSE_OR_STREAM_UNCONFIRMED');
    const text=new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(stdout));
    if(text&&!text.endsWith('\n'))fail('TRAILING_REPORT_FRAGMENT');
    const reports=[];
    for(const line of text.split('\n'))if(line.trim().startsWith('ROS_DESKTOP_REPORT ')){
      try{reports.push(JSON.parse(line.trim().slice('ROS_DESKTOP_REPORT '.length)));}
      catch{reports.push({event:'malformed_report'});}
    }
    const verdict=validateSmokeReports(reports,close.code);
    const ready=reports.find(r=>r.event==='ready_to_show');
    if(ready.pid!==child.pid||path.resolve(ready.capture_path||'')!==capture)fail('ORIGINAL_ELECTRON_OR_CAPTURE_MISMATCH');
    const image=fs.lstatSync(capture);
    if(!image.isFile()||image.isSymbolicLink()||fs.realpathSync.native(capture)!==capture||image.size<24)fail('CAPTURE_UNCONFIRMED');
    const png=fs.readFileSync(capture);
    if(!png.subarray(0,8).equals(Buffer.from([137,80,78,71,13,10,26,10])))fail('CAPTURE_NOT_PNG');
    const width=png.readUInt32BE(16),height=png.readUInt32BE(20);
    if(width<100||height<100)fail('CAPTURE_EMPTY');
    const result={...base,status:'NATIVE_REPORTS_AND_CAPTURE_OBSERVED_PENDING_OUTER_JOB_STOP',
      original_electron_pid:child.pid,child_close:close,native_report_verdict:verdict,reports,
      screenshot:{path:capture,sha256:sha(capture),bytes:image.size,width,height},
      runtime_or_model_qualification:false,business_acceptance:false};
    writeNew(resultPath,result);
    console.log(JSON.stringify({status:result.status,result_path:resultPath,screenshot:result.screenshot,
      requires_outer_job_stop_proved:true,formal_increment:0}));
    return result;
  }catch(error){
    writeNew(resultPath,{...base,status:'SMOKE_UNKNOWN_OR_FAILED',original_electron_pid:child?.pid||null,
      error:kind(error),spawn_error:spawnError,stdout_bytes:sizes.stdout,stderr_bytes:sizes.stderr,
      native_or_GUI_success:false});
    throw error;
  }
}

if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  if(process.argv.length!==4||process.argv[2]!=='--state')fail('ARGUMENTS_REQUIRE_NEW_STATE');
  try{await smoke(process.argv[3]);}
  catch(error){console.error(JSON.stringify({status:'SMOKE_UNKNOWN_OR_FAILED',error:kind(error),automatic_retry:false}));process.exitCode=2;}
}
