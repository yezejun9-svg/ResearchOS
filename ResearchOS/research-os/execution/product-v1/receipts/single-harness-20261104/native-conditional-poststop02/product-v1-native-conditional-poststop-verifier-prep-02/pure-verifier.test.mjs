// Pure, source-derived validator cases. Root must run under a fresh supervised
// pure-test scope; this file does not open the real qualification receipts.
import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import crypto from 'node:crypto';
import { requireStoppedOriginalJob, requireOuterBinding, validatePlan, validateTranscript,
  verifyFiniteCases, compareImmutable, emptyWireSlice, requireQualificationCapture } from './verify-poststop.mjs';

const C='C:/Users/yqyyds/Documents/Codex/2026-11-04/task';
const S=path.resolve(C,'product-v1-native-qualification-中文-root-01/S');
const Q=path.dirname(S), runner=path.join(C,'product-v1-native-conditional-controller-prep-02/real-electron-flow.mjs');
const runnerHash='746e1ff326a964904461902aa5980f9a9fdcfb619c5b1bef5ad65e52d9437587';
const cases=['source_read','denied_read','source_write_open','working_write_open','source_create','working_create','loopback_connect'];
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const pref=x=>'sha256:'+sha(x);
const nonce='researchos-readonly-'+'a'.repeat(32);
const caseRows=()=>cases.map((name,i)=>({name,opened:i===0,errno:i===0?0:i===6?10013:5,
  digest:i===0?pref(Buffer.from('researchos-qualification-allow-v1\n')):'',bytes:i===0?Buffer.byteLength('researchos-qualification-allow-v1\n'):0}));

test('distinct outer and inner scopes bind the original f13 argv and both input pins',()=>{
  const scope={scope_id:'fresh-one-shot',inner_scope_path:path.join(C,'inner.scope.json'),inner_scope_sha256:'b'.repeat(64)};
  const inner={node:{path:'C:/nvm4w/nodejs/node.exe',sha256:'c'.repeat(64)}};
  const outer={schema:'researchos.owned-windows-run/1',scope_id:scope.scope_id,purpose:'gui',authorization:'ROOT_REVIEWED_EXACT_COMMAND',
    cwd:path.dirname(runner),executable:inner.node.path,executable_sha256:inner.node.sha256,
    argv:[runner,'--execute','--scope',scope.inner_scope_path,'--scope-sha256',scope.inner_scope_sha256],
    inputs:[{path:scope.inner_scope_path,sha256:scope.inner_scope_sha256},{path:runner,sha256:runnerHash}]};
  assert.doesNotThrow(()=>requireOuterBinding(outer,scope,inner));
  for(const wrong of [
    {...outer,scope_id:'other'},
    {...outer,argv:[...outer.argv.slice(0,5),'d'.repeat(64)]},
    {...outer,argv:[runner,'--execute','--scope',path.join(C,'other.json'),'--scope-sha256',scope.inner_scope_sha256]},
    {...outer,inputs:outer.inputs.slice(1)},
    {...outer,inputs:[{path:scope.inner_scope_path,sha256:'e'.repeat(64)},outer.inputs[1]]}
  ]) assert.throws(()=>requireOuterBinding(wrong,scope,inner),/OUTER_F13_RUNNER_INNER_SCOPE_BINDING_MISSING/);
});
test('original f13 stopped Job proof gates a simulated receipt read',()=>{
  const scope={scope_id:'fresh-one-shot',outer_scope_sha256:'a'.repeat(64)};
  const root={status:'COMPLETED_OWNED_JOB_STOPPED',scope_id:scope.scope_id,scope_sha256:scope.outer_scope_sha256,
    job_assigned:true,resumed:true,stop_proved:true,job_active_zero:true,root_signaled:true,timed_out:false,
    input_drift:false,automatic_retry:false,terminate_job_attempts:0,terminate_original_root_attempts:0,
    root_exit_code:0,errors:[]};
  let receiptReads=0;const readAfterStop=value=>{requireStoppedOriginalJob(value,scope);receiptReads++};
  readAfterStop(root);
  for(const wrong of [{...root,job_active_zero:false},{...root,timed_out:true},{...root,stop_proved:false},
    {...root,terminate_job_attempts:1},{...root,scope_sha256:'b'.repeat(64)}])
    assert.throws(()=>readAfterStop(wrong),/ORIGINAL_F13_JOB_STOP_NOT_PROVED/);
  assert.equal(receiptReads,1);
});
test('actual lowercase plan wire keys, nonce, paths and canonical bytes are required',()=>{
  const plan={schema:'researchos.native-qualification-plan.v1',source:S,working:path.join(Q,'QW'),denied:path.join(Q,'D'),nonce,port:32123,cases};
  const encoded=Buffer.from(JSON.stringify(plan)).toString('base64url');
  const context={nonce,loopback_port:32123,plan_encoded:encoded,plan_hash:pref(Buffer.from(encoded))};
  assert.doesNotThrow(()=>validatePlan(context));
  for(const mutation of [{...plan,nonce:'researchos-readonly-'+'b'.repeat(32)},{...plan,port:3},
    {...plan,source:path.join(Q,'OTHER')},{Schema:plan.schema,...Object.fromEntries(Object.entries(plan).filter(([k])=>k!=='schema'))}]) {
    const e=Buffer.from(JSON.stringify(mutation)).toString('base64url');
    assert.throws(()=>validatePlan({...context,plan_encoded:e,plan_hash:pref(Buffer.from(e))}));
  }
});
test('lowercase ordered START/RESULT/COMPLETE transcript binds seven exact results',()=>{
  const rows=caseRows(), events=[];
  for(const row of rows) {
    events.push({schema:'researchos.native-qualification-event.v1',phase:'START',case:row.name,errno:0,opened:false,digest:'',bytes:0,bitmap:0});
    events.push({schema:'researchos.native-qualification-event.v1',phase:'RESULT',case:row.name,errno:row.errno,opened:row.opened,digest:row.digest,bytes:row.bytes,bitmap:0});
  }
  events.push({schema:'researchos.native-qualification-event.v1',phase:'COMPLETE',case:'',errno:0,opened:false,digest:'',bytes:0,bitmap:127});
  const raw=value=>Buffer.from(value.map(x=>JSON.stringify(x)).join('\n')+'\n');
  assert.doesNotThrow(()=>validateTranscript(raw(events),{case_results:rows}));
  for(const wrong of [events.slice(0,-1),[...events,{...events.at(-1)}],
    events.map((x,i)=>i===0?{Schema:x.schema,...Object.fromEntries(Object.entries(x).filter(([k])=>k!=='schema'))}:x),
    events.map((x,i)=>i===1?{...x,case:'wrong'}:x),events.map((x,i)=>i===14?{...x,bitmap:126}:x)])
    assert.throws(()=>validateTranscript(raw(wrong),{case_results:rows}));
});
test('nil empty slices are phase-specific and final seven finite cases remain strict',()=>{
  assert.equal(emptyWireSlice(null),true);assert.equal(emptyWireSlice([]),true);
  for(const value of [undefined,{},'empty',[1]])assert.equal(emptyWireSlice(value),false);
  const rows=caseRows(), final={observed_case_bitmap:127,post_controls_complete:true,finding_codes:null,case_results:rows};
  assert.doesNotThrow(()=>verifyFiniteCases(final));
  for(const wrong of [{...final,finding_codes:undefined},{...final,finding_codes:['VIOLATION']},
    {...final,case_results:null},{...final,case_results:rows.slice(1)},
    {...final,case_results:rows.map((x,i)=>i===6?{...x,errno:0}:x)}])
    assert.throws(()=>verifyFiniteCases(wrong));
  const initial={task_id:'task',case_results:null,finding_codes:null,observed_case_bitmap:0,post_controls_complete:false};
  assert.doesNotThrow(()=>compareImmutable(initial,{...initial,case_results:rows,observed_case_bitmap:127,post_controls_complete:true}));
  assert.throws(()=>compareImmutable(initial,{...initial,task_id:'other'}),/PRELAUNCH_FINAL_CONTEXT_DRIFT/);
});
test('qualification PID, configured Job, clean drain and raw hashes are jointly bound',()=>{
  const run_id='run-1',epoch='1',working=path.join(Q,'QW'),exe='C:/tools/codex.exe';
  const expected={run_id,epoch},job='researchos-codex-qualification-'+sha(run_id+'/'+epoch+'/'+nonce);
  const intent={context:{nonce},executable:exe,working_directory:working,job_name:job,job_limit_flags:8712,job_process_limit:16,job_memory_limit:2147483648};
  const files={stdout:path.join(Q,'receipts','fixed.json.stdout.partial'),stderr:path.join(Q,'receipts','fixed.json.stderr.partial')};
  const stdout=Buffer.from('bounded raw evidence\n'),stderr=Buffer.alloc(0),captureRaw=Buffer.from('{"created":1760000000000000000}');
  const capture={job,job_limit_flags:8712,job_process_limit:16,job_memory_limit:2147483648,job_limits_verified:true,
    pid:321,exited:true,job_zero:true,streams_drained:true,cleanup_complete:true,exit_code:0,timed_out:false,
    limit_exceeded:false,capture_error:'',stdout_error:'',stderr_error:'',reason:'',
    stdout_partial:files.stdout,stderr_partial:files.stderr,stdout_hash:pref(stdout),stderr_hash:pref(stderr),
    stdout_prefix:stdout.toString('base64'),stderr_prefix:null};
  assert.equal(requireQualificationCapture(capture,intent,expected,{codex:{executable:exe}},captureRaw,files,stdout,stderr),'1760000000000000000');
  for(const wrong of [{...capture,pid:0},{...capture,job_zero:false},{...capture,streams_drained:false},
    {...capture,job_limit_flags:0},{...capture,stdout_hash:pref(Buffer.from('changed'))},
    {...capture,stderr_error:'nonempty'}])
    assert.throws(()=>requireQualificationCapture(wrong,intent,expected,{codex:{executable:exe}},captureRaw,files,stdout,stderr));
  assert.throws(()=>requireQualificationCapture(capture,intent,expected,{codex:{executable:exe}},Buffer.from('{"created":0}'),files,stdout,stderr),/QUALIFICATION_PID_CREATION_EXACT_DECIMAL_REQUIRED/);
});
