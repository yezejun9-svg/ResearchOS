// C-only read-only post-stop verifier. It cannot authorize Native execution or
// produce a product/formal acceptance claim. Run only against a separately
// reviewed exact scope after the ORIGINAL f13 Job has stopped.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const C_ROOT = 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task';
const FIXED_SOURCE = path.resolve(C_ROOT, 'product-v1-native-qualification-中文-root-01/S');
const FIXED_ROOT = path.dirname(FIXED_SOURCE);
const F13_ROOT = path.join(C_ROOT, 'product-v1-owned-verification-20261104/runs');
const RUNNER = path.join(C_ROOT,'product-v1-native-conditional-controller-prep-02/real-electron-flow.mjs');
const RUNNER_SHA256 = '746e1ff326a964904461902aa5980f9a9fdcfb619c5b1bef5ad65e52d9437587';
const SOURCE2_FINAL_MANIFEST = path.join(C_ROOT,'product-v1-native-prelaunch-intent-author-20261105-final/MANIFEST.json');
const SOURCE2_FINAL_MANIFEST_SHA256 = 'e842cc69ca0486b666392ec205ccb36d46b1ed95abe8a4a735bcdc98b26ec9e3';
const CASES = ['source_read','denied_read','source_write_open','working_write_open','source_create','working_create','loopback_connect'];
const SOURCE2 = Object.freeze({
  'adapters/runtime/codex_qualification_windows.go':'7af3347a194a66455f962d38fc1918b0752a30ca4138ef46734ebd2fdc20bd24',
  'adapters/runtime/codex_qualification_capture_windows.go':'a664f9c24feaf752ba784bb370d3a650d81232f8e449ccb45ca6138a16f9eb59',
  'internal/qualificationprobe/plan.go':'0005183086beade6418afb14c507cf39ea81f3003ef957188c92c8b9d2109aea',
});
const HELPER_HASH = 'sha256:4ac03d2af358ab0ecb4d2f06a12bbc0bcde043e7e3610ee114a64c0416f1b4ef';
const H64 = /^[a-f0-9]{64}$/;
const SHA = /^sha256:[a-f0-9]{64}$/;
const sha = data => crypto.createHash('sha256').update(data).digest('hex');
const shaPrefixed = data => 'sha256:' + sha(data);
const folded = file => path.resolve(file).toLowerCase();
const same = (a,b) => folded(a) === folded(b);
const exact = (test, code) => { if (!test) throw Object.assign(new Error(code),{code}); };
const bytesEqual = (a,b) => Buffer.compare(a,b) === 0;
export const emptyWireSlice = value => value === null || Array.isArray(value) && value.length === 0;
const pinReviewedRunner = () => readPinned(RUNNER,RUNNER_SHA256,100000);
const keys = (value, expected, code) => exact(value && typeof value === 'object' && !Array.isArray(value) &&
  Object.keys(value).sort().join('|') === [...expected].sort().join('|'), code);

function readPinned(file, digest, cap) {
  exact(path.isAbsolute(file) && H64.test(digest || ''), 'PINNED_ABSOLUTE_FILE_REQUIRED');
  const stat = fs.lstatSync(file);
  exact(stat.isFile() && !stat.isSymbolicLink() && stat.size > 0 && stat.size <= cap, 'PINNED_FILE_TYPE_OR_SIZE');
  exact(same(fs.realpathSync.native(file),file), 'PINNED_FILE_REPARSE_OR_ALIAS');
  const raw = fs.readFileSync(file);
  exact(raw.length === stat.size && sha(raw) === digest, 'PINNED_FILE_BYTES_CHANGED');
  return raw;
}
function parseJSON(raw, code) {
  let value; try { value = JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(raw)); } catch { exact(false,code); }
  exact(value && typeof value === 'object' && !Array.isArray(value),code);
  return value;
}
function readExactOwned(file, cap) {
  exact(path.isAbsolute(file), 'EXACT_OWNED_FILE_PATH_REQUIRED');
  const stat = fs.lstatSync(file);
  exact(stat.isFile() && !stat.isSymbolicLink() && stat.size > 0 && stat.size <= cap, 'OWNED_FILE_TYPE_OR_SIZE');
  exact(same(fs.realpathSync.native(file),file), 'OWNED_FILE_REPARSE_OR_ALIAS');
  const raw = fs.readFileSync(file);
  exact(raw.length === stat.size, 'OWNED_FILE_READ_SHORT');
  return raw;
}
function expectedPaths(runId,epoch) {
  exact(/^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$/.test(runId || '') &&
    /^[1-9][0-9]{0,18}$/.test(epoch || '') && BigInt(epoch) <= 9223372036854775807n,
    'AUTHORITATIVE_RUN_REF_REQUIRED');
  const base = path.join(FIXED_ROOT,'receipts',sha(runId+'/'+epoch)+'.json');
  return {capture:base,intent:base+'.prelaunch.json',stdout:base+'.stdout.partial',stderr:base+'.stderr.partial'};
}
function contextBase(value, expected, kind) {
  exact(value?.task_id === expected.task_id && value.run_id === expected.run_id && value.epoch === expected.epoch &&
    value.host_boot === expected.host_boot && value.source_binding_hash === expected.source_binding_hash &&
    same(value.source, FIXED_SOURCE) && same(value.working,path.join(FIXED_ROOT,'QW')) &&
    same(value.denied,path.join(FIXED_ROOT,'D')) && value.native_hash === expected.native_hash &&
    value.helper_hash === HELPER_HASH && value.host_build_hash === expected.host_build_hash &&
    value.template_hash === expected.template_hash && value.environment_hash === expected.environment_hash &&
    same(value.normal_home,expected.normal_home) &&
    Array.isArray(value.expected_cases) && JSON.stringify(value.expected_cases) === JSON.stringify(CASES) &&
    value.pre_controls_complete === true, 'CURRENT_'+kind+'_CONTEXT_MISMATCH');
  exact(/^researchos-readonly-[a-f0-9]{32}$/.test(value.nonce || '') &&
    Number.isInteger(value.loopback_port) && value.loopback_port >= 1 && value.loopback_port <= 65535 &&
    SHA.test(value.plan_hash || '') && SHA.test(value.rendered_argv_hash || '') &&
    Array.isArray(value.rendered_argv) && value.rendered_argv.length >= 9 &&
    value.rendered_argv_hash === shaPrefixed(Buffer.from(JSON.stringify(value.rendered_argv))) &&
    JSON.stringify(value.rendered_argv) === JSON.stringify(expected.rendered_argv),
    'CURRENT_'+kind+'_PLAN_OR_ARGV_INVALID');
}
export function validatePlan(context) {
  exact(typeof context.plan_encoded === 'string' && /^[A-Za-z0-9_-]{1,5500}$/.test(context.plan_encoded), 'PLAN_ENCODING_INVALID');
  const raw = Buffer.from(context.plan_encoded,'base64url');
  exact(raw.length > 0 && raw.length <= 4096 && raw.toString('base64url') === context.plan_encoded &&
    context.plan_hash === shaPrefixed(Buffer.from(context.plan_encoded)), 'PLAN_ENCODING_OR_HASH_CHANGED');
  const plan = parseJSON(raw,'PLAN_JSON_INVALID');
  keys(plan,['schema','source','working','denied','nonce','port','cases'],'PLAN_FIELDS_CHANGED');
  exact(plan.schema === 'researchos.native-qualification-plan.v1' && same(plan.source,FIXED_SOURCE) &&
    same(plan.working,path.join(FIXED_ROOT,'QW')) && same(plan.denied,path.join(FIXED_ROOT,'D')) &&
    plan.nonce === context.nonce && plan.port === context.loopback_port &&
    JSON.stringify(plan.cases) === JSON.stringify(CASES) &&
    JSON.stringify(plan) === raw.toString('utf8'), 'PLAN_CONTEXT_OR_CANONICAL_BYTES_MISMATCH');
}
export function compareImmutable(intent, final) {
  const mutated = new Set(['case_results','finding_codes','observed_case_bitmap','post_controls_complete']);
  for (const [name,value] of Object.entries(intent)) {
    if (!mutated.has(name)) exact(JSON.stringify(value) === JSON.stringify(final[name]), 'PRELAUNCH_FINAL_CONTEXT_DRIFT:'+name);
  }
  exact(Object.keys(intent).sort().join('|') === Object.keys(final).sort().join('|'), 'PRELAUNCH_FINAL_CONTEXT_FIELDS_CHANGED');
}
export function validateTranscript(raw, context) {
  exact(raw.length > 0 && raw.length <= 65536 && raw.at(-1) === 10, 'STDOUT_TRANSCRIPT_BOUNDARY');
  const lines = new TextDecoder('utf-8',{fatal:true}).decode(raw.subarray(0,-1)).split('\n');
  exact(lines.length === CASES.length*2+1, 'STDOUT_TRANSCRIPT_CASE_COUNT');
  for (let i=0;i<CASES.length;i++) {
    for (let j=0;j<2;j++) {
      const line=lines[i*2+j], event=parseJSON(Buffer.from(line),'STDOUT_EVENT_JSON_INVALID');
      keys(event,['schema','phase','case','errno','opened','digest','bytes','bitmap'],'STDOUT_EVENT_FIELDS_CHANGED');
      exact(JSON.stringify(event)===line && event.schema==='researchos.native-qualification-event.v1' &&
        event.phase===(j?'RESULT':'START') && event.case===CASES[i] && event.bitmap===0,
        'STDOUT_EVENT_ORDER_OR_BYTES_CHANGED');
      if (!j) exact(event.errno===0 && event.opened===false && event.digest==='' && event.bytes===0,'STDOUT_START_NOT_EMPTY');
      else {
        const row=context.case_results[i];
        exact(row.name===CASES[i] && row.opened===event.opened && row.errno===event.errno &&
          row.digest===event.digest && row.bytes===event.bytes,'STDOUT_RECEIPT_CASE_DRIFT');
      }
    }
  }
  const last=lines.at(-1), end=parseJSON(Buffer.from(last),'STDOUT_COMPLETE_JSON_INVALID');
  keys(end,['schema','phase','case','errno','opened','digest','bytes','bitmap'],'STDOUT_COMPLETE_FIELDS_CHANGED');
  exact(JSON.stringify(end)===last && end.schema==='researchos.native-qualification-event.v1' &&
    end.phase==='COMPLETE' && end.case==='' && end.bitmap===127 && end.errno===0 &&
    end.opened===false && end.digest==='' && end.bytes===0, 'STDOUT_COMPLETE_INVALID');
}
export function verifyFiniteCases(context) {
  exact(context.observed_case_bitmap===127 && context.post_controls_complete===true &&
    Object.hasOwn(context,'finding_codes') && emptyWireSlice(context.finding_codes) &&
    Array.isArray(context.case_results) && context.case_results.length===7, 'SEVEN_CASES_OR_HOST_CONTROLS_INCOMPLETE');
  const allow=Buffer.from('researchos-qualification-allow-v1\n');
  for(let i=0;i<CASES.length;i++) {
    const row=context.case_results[i];
    keys(row,['name','opened','errno','digest','bytes'],'CASE_RESULT_FIELDS_CHANGED');
    exact(row.name===CASES[i], 'CASE_RESULT_ORDER_CHANGED');
    if (i===0) exact(row.opened===true && row.errno===0 && row.digest===shaPrefixed(allow) && row.bytes===allow.length,'POSITIVE_SOURCE_READ_NOT_OBSERVED');
    else exact(row.opened===false && row.errno===(i===6?10013:5) && row.digest==='' && row.bytes===0,
      'FINITE_DENIAL_NOT_OBSERVED:'+row.name);
  }
}
export function requireStoppedOriginalJob(root,scope) {
  exact(root.status==='COMPLETED_OWNED_JOB_STOPPED' && root.scope_id===scope.scope_id &&
    root.scope_sha256===scope.outer_scope_sha256 && root.job_assigned===true && root.resumed===true &&
    root.stop_proved===true && root.job_active_zero===true && root.root_signaled===true &&
    root.timed_out===false && root.input_drift===false && root.automatic_retry===false &&
    root.terminate_job_attempts===0 && root.terminate_original_root_attempts===0 &&
    root.root_exit_code===0 && Array.isArray(root.errors) && root.errors.length===0,
    'ORIGINAL_F13_JOB_STOP_NOT_PROVED');
}
export function requireOuterBinding(outer,scope,runScope) {
  exact(outer.schema==='researchos.owned-windows-run/1' && outer.scope_id===scope.scope_id &&
    outer.purpose==='gui' && outer.authorization==='ROOT_REVIEWED_EXACT_COMMAND' &&
    same(outer.cwd,path.dirname(RUNNER)) && Array.isArray(outer.argv) && outer.argv.length===6 &&
    same(outer.argv[0],RUNNER) && outer.argv[1]==='--execute' && outer.argv[2]==='--scope' &&
    same(outer.argv[3],scope.inner_scope_path) && outer.argv[4]==='--scope-sha256' &&
    outer.argv[5]===scope.inner_scope_sha256 && Array.isArray(outer.inputs) &&
    outer.inputs.filter(row=>same(row.path,scope.inner_scope_path)&&row.sha256===scope.inner_scope_sha256).length===1 &&
    outer.inputs.filter(row=>same(row.path,RUNNER)&&row.sha256===RUNNER_SHA256).length===1 &&
    same(outer.executable,runScope.node.path) && outer.executable_sha256===runScope.node.sha256,
    'OUTER_F13_RUNNER_INNER_SCOPE_BINDING_MISSING');
}
export function requireQualificationCapture(capture,intent,expected,runScope,captureRaw,files,stdout,stderr) {
  const job='researchos-codex-qualification-'+sha(expected.run_id+'/'+expected.epoch+'/'+intent.context.nonce);
  exact(same(intent.executable,runScope.codex.executable) && same(intent.working_directory,path.join(FIXED_ROOT,'QW')) &&
    intent.job_name===job && capture.job===job && intent.job_limit_flags===8712 &&
    intent.job_process_limit===16 && intent.job_memory_limit===2147483648 &&
    capture.job_limit_flags===intent.job_limit_flags && capture.job_process_limit===16 &&
    capture.job_memory_limit===2147483648 && capture.job_limits_verified===true,
    'QUALIFICATION_JOB_IDENTITY_OR_LIMITS_CHANGED');
  exact(Number.isInteger(capture.pid)&&capture.pid>0&&capture.pid<=4294967295&&
    capture.exited===true&&capture.job_zero===true&&capture.streams_drained===true&&
    capture.cleanup_complete===true&&capture.exit_code===0&&capture.timed_out===false&&
    capture.limit_exceeded===false&&capture.capture_error===''&&capture.stdout_error===''&&
    capture.stderr_error===''&&capture.reason==='', 'QUALIFICATION_CHILD_OR_STREAM_NOT_CLEAN');
  const createdText=captureRaw.toString('utf8').match(/"created":([1-9][0-9]*)/g)||[];
  exact(createdText.length===1, 'QUALIFICATION_PID_CREATION_EXACT_DECIMAL_REQUIRED');
  exact(same(capture.stdout_partial,files.stdout)&&same(capture.stderr_partial,files.stderr)&&
    SHA.test(capture.stdout_hash||'')&&SHA.test(capture.stderr_hash||''),
    'EXACT_RAW_STREAM_PATHS_AND_HASHES_REQUIRED');
  exact(capture.stdout_hash===shaPrefixed(stdout)&&capture.stderr_hash===shaPrefixed(stderr)&&
    typeof capture.stdout_prefix==='string'&&bytesEqual(Buffer.from(capture.stdout_prefix,'base64'),stdout)&&
    (capture.stderr_prefix===null||capture.stderr_prefix===''||
      typeof capture.stderr_prefix==='string'&&bytesEqual(Buffer.from(capture.stderr_prefix,'base64'),stderr)),
    'RAW_STREAM_DIGEST_OR_PREFIX_CHANGED');
  return createdText[0].split(':')[1];
}
function verify(scopeFile,scopeSHA) {
  exact(process.platform==='win32', 'WINDOWS_PATH_SEMANTICS_REQUIRED');
  const scope=parseJSON(readPinned(scopeFile,scopeSHA,65536),'SCOPE_JSON_INVALID');
  const source2Final=parseJSON(readPinned(SOURCE2_FINAL_MANIFEST,SOURCE2_FINAL_MANIFEST_SHA256,65536),'FROZEN_SOURCE2_FINAL_MANIFEST_INVALID');
  exact(source2Final.schema==='researchos.native-prelaunch-intent-final-author.v1' &&
    source2Final.source_hashes?.['adapters/runtime/codex_qualification_windows.go']===SOURCE2['adapters/runtime/codex_qualification_windows.go'] &&
    source2Final.source_hashes?.['adapters/runtime/codex_qualification_capture_windows.go']===SOURCE2['adapters/runtime/codex_qualification_capture_windows.go'],
    'FROZEN_SOURCE2_FINAL_PRODUCTION_CHANGED');
  exact(scope.schema==='researchos.native-conditional-poststop-scope/1' && scope.status==='ROOT_REVIEWED_POSTSTOP_SCOPE' &&
    same(scope.qualification_root,FIXED_ROOT) && same(scope.synthetic_source,FIXED_SOURCE), 'POSTSTOP_SCOPE_NOT_AUTHORIZED');
  exact(H64.test(scope.outer_scope_sha256||'') && H64.test(scope.inner_scope_sha256||'') &&
    H64.test(scope.root_job_result_sha256||'') &&
    H64.test(scope.runner_result_sha256||'') && H64.test(scope.expected_capture_sha256||'') &&
    H64.test(scope.expected_prelaunch_sha256||'') && /^[a-f0-9]{32}$/.test(scope.current_host_boot||'') &&
    scope.host_boot_provenance==='ROOT_INDEPENDENT_CURRENT_HOST_BOOT_REVIEW',
    'POSTSTOP_INDEPENDENT_PINS_REQUIRED');
  exact(/^[a-z0-9][a-z0-9-]{1,127}$/.test(scope.scope_id||'') &&
    same(scope.root_job_result_path,path.join(F13_ROOT,scope.scope_id,'RESULT.json')),
    'ORIGINAL_F13_RESULT_PATH_REQUIRED');
  // This proof is checked BEFORE any Native qualification receipt is opened.
  const root=parseJSON(readPinned(scope.root_job_result_path,scope.root_job_result_sha256,65536),'ORIGINAL_F13_RESULT_INVALID');
  requireStoppedOriginalJob(root,scope);
  pinReviewedRunner();
  const outer=parseJSON(readPinned(scope.outer_scope_path,scope.outer_scope_sha256,65536),'ORIGINAL_OUTER_SCOPE_INVALID');
  const runScope=parseJSON(readPinned(scope.inner_scope_path,scope.inner_scope_sha256,65536),'ORIGINAL_INNER_SCOPE_INVALID');
  requireOuterBinding(outer,scope,runScope);
  exact(runScope.status==='ROOT_APPROVED_REAL_RUN' && same(runScope.qualification.root,FIXED_ROOT) &&
    same(runScope.qualification.synthetic_source,FIXED_SOURCE) &&
    runScope.bundle.manifest_sha256===scope.bundle_manifest_sha256 &&
    runScope.source.head===scope.source_head &&
    runScope.source.pins?.length>=48, 'ORIGINAL_RUN_SCOPE_BINDING_CHANGED');
  for(const [name,hash] of Object.entries(SOURCE2)) exact(runScope.source.pins.some(row=>row.path===name&&row.sha256===hash),
    'FROZEN_SOURCE2_OR_PLAN_PIN_MISSING:'+name);
  const runRoot=runScope.run_root;
  exact(path.isAbsolute(runRoot) && same(scope.runner_result_path,path.join(runRoot,'receipts','result.json')),
    'EXACT_ORIGINAL_RUNNER_RESULT_PATH_REQUIRED');
  const runner=parseJSON(readPinned(scope.runner_result_path,scope.runner_result_sha256,2<<20),'ORIGINAL_RUNNER_RESULT_INVALID');
  const task=runner.task;
  exact(runner.scope_sha256===scope.inner_scope_sha256 && runner.close?.app_close_resolved===true &&
    task?.task_ref?.project_id===runner.project_id && task.task_ref.task_id &&
    task.run?.run_id===runner.run_ref?.run_id && task.run?.epoch===runner.run_ref?.epoch &&
    task.terminal===true && runner.actual_dom_submit_attempts===1 && runner.formal_increment===0 &&
    runner.product_increment===0, 'AUTHORITATIVE_ONE_TASK_RUNNER_EVIDENCE_REQUIRED');
  const expected={task_id:task.task_ref.task_id,run_id:task.run.run_id,epoch:task.run.epoch,
    host_boot:scope.current_host_boot,source_binding_hash:scope.source_binding_hash,
    native_hash:'sha256:'+runScope.codex.sha256,host_build_hash:scope.host_build_hash,
    template_hash:scope.template_hash,environment_hash:scope.environment_hash,
    normal_home:runScope.windows.normal_user_profile,rendered_argv:scope.expected_rendered_argv};
  exact([expected.source_binding_hash,expected.native_hash,expected.host_build_hash,expected.template_hash,expected.environment_hash].every(x=>SHA.test(x||'')) &&
    Array.isArray(expected.rendered_argv) && expected.rendered_argv.length>=9, 'REVIEWED_FRESH_PROVENANCE_PINS_REQUIRED');
  const files=expectedPaths(expected.run_id,expected.epoch);
  // No directory walk or alternative path is permitted; all paths are derived
  // from the real bound Run and the one Root-approved qualification root.
  const captureRaw=readPinned(files.capture,scope.expected_capture_sha256,200000);
  const capture=parseJSON(captureRaw,'FINAL_CAPTURE_JSON_INVALID');
  exact(capture.schema==='researchos.native-qualification-capture.v1' && capture.reason==='' &&
    same(capture.prelaunch_intent_path,files.intent) && capture.prelaunch_intent_sha256==='sha256:'+scope.expected_prelaunch_sha256,
    'FINAL_CAPTURE_INTENT_LINK_INVALID');
  const intentRaw=readPinned(files.intent,scope.expected_prelaunch_sha256,32768);
  exact(intentRaw.at(-1)===10, 'PRELAUNCH_INTENT_FINAL_NEWLINE_REQUIRED');
  const intent=parseJSON(intentRaw,'PRELAUNCH_INTENT_JSON_INVALID');
  exact(intent.schema==='researchos.native-qualification-prelaunch.v1' && intent.phase==='PREPARED_INTENT_ONLY',
    'PRELAUNCH_PHASE_NOT_PREPARED');
  contextBase(intent.context,expected,'PRELAUNCH');
  contextBase(capture.context,expected,'FINAL');
  compareImmutable(intent.context,capture.context);
  validatePlan(intent.context);
  exact(intent.context.post_controls_complete===false && intent.context.observed_case_bitmap===0 &&
    Object.hasOwn(intent.context,'case_results') && emptyWireSlice(intent.context.case_results) &&
    Object.hasOwn(intent.context,'finding_codes') && emptyWireSlice(intent.context.finding_codes),
    'PRELAUNCH_CONTEXT_CONTAINS_POSTHOC_RESULT');
  const stdout=readExactOwned(files.stdout,65536);
  const stderrStat=fs.lstatSync(files.stderr);
  exact(stderrStat.isFile()&&!stderrStat.isSymbolicLink()&&stderrStat.size===0&&
    same(fs.realpathSync.native(files.stderr),files.stderr),'STDERR_PARTIAL_NOT_EXACT_EMPTY_FILE');
  const stderr=fs.readFileSync(files.stderr);
  const createdText=requireQualificationCapture(capture,intent,expected,runScope,captureRaw,files,stdout,stderr);
  verifyFiniteCases(capture.context);
  validateTranscript(stdout,capture.context);
  return {status:'FINITE_SEVEN_CASES_OBSERVED_POSTSTOP_NOT_PRODUCT_ACCEPTED',formal_increment:0,product_increment:0,
    original_job_stop_proved:true,qualification_job_zero:true,streams_drained:true,
    task_ref:task.task_ref,run_ref:runner.run_ref,qualification_pid:capture.pid,
    qualification_created_decimal:createdText,capture_sha256:scope.expected_capture_sha256,
    prelaunch_intent_sha256:scope.expected_prelaunch_sha256,
    case_names:CASES,claim_limit:'Only seven fixed operations with the bound process, time, paths and controls; no full permission graph, model billing or product acceptance.'};
}

if(process.argv[1] && same(process.argv[1],fileURLToPath(import.meta.url))) {
  const args=process.argv.slice(2);
  if(args.length!==4||args[0]!=='--scope'||args[2]!=='--scope-sha256') {
    console.log(JSON.stringify({status:'PREPARATION_ONLY_EXACT_ROOT_POSTSTOP_SCOPE_REQUIRED',formal_increment:0,product_increment:0}));
    process.exitCode=2;
  } else {
    try { console.log(JSON.stringify(verify(path.resolve(args[1]),args[3]))); }
    catch(error) { console.log(JSON.stringify({status:'BLOCKED_POSTSTOP_EVIDENCE_NOT_ESTABLISHED',reason:error.code||'UNEXPECTED_VALIDATION_ERROR',formal_increment:0,product_increment:0}));process.exitCode=2; }
  }
}
