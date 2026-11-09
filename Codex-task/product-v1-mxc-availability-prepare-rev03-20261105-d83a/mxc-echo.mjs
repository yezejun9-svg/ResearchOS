// PREPARATION ONLY. Launch only as the child of the unchanged, pinned f13 CLI.
// This wrapper neither proves Job membership nor kills any process.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { BoundedCapture, durableJSON } from './bounded-capture.mjs';

const SELF = fileURLToPath(import.meta.url);
const PREP = path.dirname(SELF);
const OWNER = 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-owned-verification-20261104';
const SCOPE_ID = 'mxc_availability_20261105_d83a';
const RUN = path.join(OWNER, 'runs', SCOPE_ID, 'mxc');
const CODEX = 'C:/nvm4w/nodejs/node_modules/@openai/codex/node_modules/@openai/codex-win32-x64/vendor/x86_64-pc-windows-msvc/bin/codex.exe';
const NODE = 'C:/nvm4w/nodejs/node.exe';
const CMD = 'C:/Windows/System32/cmd.exe';
const FIXED = [
  [CODEX, '9d563ee4e0441ff9d59d612013e0460ddf8e5709735c2d9f6b98b7ef8ca4eb42'],
  [NODE, '5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'],
  [CMD, '15cd209c995b7d3009c91ca40892d5b8f1fb162f3e5f10716642ea278e8e0d7b'],
  [path.join(OWNER, 'owned_run.py'), 'f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'],
  [path.join(PREP, 'bounded-capture.mjs'), '5b1092acf0d4727bab5885cd8e7ce6c9d46420d8bcb63bedca65ce1198272740'],
];
const ARGV = ['-c', 'windows.sandbox=mxc', 'sandbox', '--include-managed-config',
  '--permission-profile', ':workspace', '--', CMD, '/d', '/c', 'echo', 'MXC_OK'];
const digest = data => crypto.createHash('sha256').update(data).digest('hex');
const fileSHA = file => {
  const fd = fs.openSync(file, 'r'), hash = crypto.createHash('sha256');
  try { const buf = Buffer.alloc(1048576); let n; while ((n = fs.readSync(fd, buf, 0, buf.length, null))) hash.update(buf.subarray(0, n)); }
  finally { fs.closeSync(fd); }
  return hash.digest('hex');
};
const fold = p => path.resolve(p).toLowerCase();
const requireThat = (test, code) => { if (!test) throw Object.assign(new Error(code), { code }); };
function ordinary(p, directory = false) {
  requireThat(path.isAbsolute(p), 'ABSOLUTE_PATH_REQUIRED');
  let cursor = path.resolve(p);
  for (;;) {
    const stat = fs.lstatSync(cursor);
    requireThat(!stat.isSymbolicLink() && fold(fs.realpathSync.native(cursor)) === fold(cursor), 'PATH_ALIAS_REFUSED');
    const parent = path.dirname(cursor); if (parent === cursor) break; cursor = parent;
  }
  requireThat(directory ? fs.statSync(p).isDirectory() : fs.statSync(p).isFile(), 'PATH_KIND_INVALID');
}
function writeNew(name, value) {
  const fd = fs.openSync(path.join(RUN, name), 'wx');
  try { fs.writeFileSync(fd, JSON.stringify(value, null, 2) + '\n'); fs.fsyncSync(fd); }
  finally { fs.closeSync(fd); }
}
export function makeEnvironment(scope) {
  // Adapted only from pinned Native05 necessary OS/native-profile fields.
  const root = scope.windows.system_root, profile = scope.windows.normal_user_profile;
  const drive = path.parse(root).root.replace(/[\\/]+$/, '');
  requireThat(/^[A-Za-z]:$/.test(drive), 'WINDOWS_SYSTEMROOT_DRIVE_REQUIRED');
  return {
    SystemRoot: root, WINDIR: root, SystemDrive: drive.toUpperCase(), OS: 'Windows_NT',
    COMSPEC: CMD, PATHEXT: '.COM;.EXE;.BAT;.CMD',
    PATH: [path.dirname(CODEX), path.dirname(NODE), path.join(root, 'System32'), root].join(path.delimiter),
    USERPROFILE: profile, HOME: profile,
    APPDATA: scope.windows.normal_app_data, LOCALAPPDATA: scope.windows.normal_local_app_data,
    TEMP: path.join(RUN, 'tmp'), TMP: path.join(RUN, 'tmp'),
  };
}
async function main() {
  requireThat(process.platform === 'win32' && fold(process.execPath) === fold(NODE), 'PINNED_WINDOWS_NODE_REQUIRED');
  requireThat(process.argv.length === 4, 'EXACT_ARGUMENT_COUNT_REQUIRED');
  const scopePath = process.argv[2], scopeHash = process.argv[3];
  requireThat(fold(scopePath) === fold(path.join(PREP, 'mxc.scope.json')) && /^[a-f0-9]{64}$/.test(scopeHash), 'FIXED_SCOPE_REQUIRED');
  ordinary(scopePath); const raw = fs.readFileSync(scopePath);
  requireThat(raw.length < 32768 && digest(raw) === scopeHash, 'SCOPE_PIN_MISMATCH');
  const s = JSON.parse(raw);
  requireThat(s.schema === 'researchos.mxc-availability.v1' && s.state === 'ROOT_REVIEWED_EXACT_COMMAND', 'ROOT_REVIEW_REQUIRED');
  requireThat(s.scope_id === SCOPE_ID && s.root_job_required === true && s.root_membership_proof === 'EXTERNAL_F13_ONLY', 'ROOT_JOB_REQUIRED');
  requireThat(s.controller_sha256 === FIXED[3][1] && s.wrapper_sha256 === fileSHA(SELF), 'CONTROLLER_PIN_MISMATCH');
  requireThat(JSON.stringify(s.argv) === JSON.stringify(ARGV) && fold(s.executable) === fold(CODEX) && fold(s.run_root) === fold(RUN), 'EXACT_COMMAND_REQUIRED');
  requireThat(s.model_tasks === 0 && s.native_invocations === 1 && s.automatic_retries === 0, 'ZERO_MODEL_ONE_NATIVE_BUDGET_REQUIRED');
  requireThat(s.timeout_ms === 35000 && s.stream_limit_bytes === 1048576 && s.retained_prefix_bytes === 65536, 'FIXED_BOUNDS_REQUIRED');
  requireThat(JSON.stringify(s.windows) === JSON.stringify({
    system_root:'C:/Windows', normal_user_profile:'C:/Users/yqyyds',
    normal_app_data:'C:/Users/yqyyds/AppData/Roaming', normal_local_app_data:'C:/Users/yqyyds/AppData/Local'
  }), 'FIXED_NATIVE_ENVIRONMENT_REQUIRED');
  for (const [p, pin] of FIXED) { ordinary(p); requireThat(fileSHA(p) === pin, 'INPUT_PIN_MISMATCH'); }
  ordinary(PREP, true); ordinary(path.dirname(RUN), true);
  fs.mkdirSync(RUN); // Exclusive one-use budget; retained on every failure.
  writeNew('CONSUMED.json', {scope_sha256:scopeHash, invocation_budget_consumed:1, model_tasks:0, automatic_retry:false, status:'PRELAUNCH'});
  fs.mkdirSync(path.join(RUN, 'cwd')); fs.mkdirSync(path.join(RUN, 'tmp'));
  const cwd = path.join(RUN, 'cwd'); ordinary(cwd, true);
  requireThat(fs.readdirSync(cwd).length === 0, 'FRESH_EMPTY_CWD_REQUIRED');
  let timedOut = false, spawnError = null, exitCode = null, exitSignal = null;
  const observationErrors = [];
  const streams = [];
  const failCapture = code => {
    if(!observationErrors.includes(code)) observationErrors.push(code);
    for(const stream of streams) stream.pause();
    if(observationErrors.length === 1) process.stderr.write('MXC_CAPTURE_FAILURE_AWAITING_ROOT_JOB\n');
  };
  for(const name of ['stdout','stderr']) streams.push(new BoundedCapture({directory:RUN,name,
    limit:s.stream_limit_bytes,prefixLimit:s.retained_prefix_bytes,onFailure:failCapture}));
  const liveSnapshot = status => {
    try { durableJSON(path.join(RUN,'live-state.json'),{status,spawn_error:spawnError,timed_out:timedOut,
      observation_errors:observationErrors,streams:streams.map(v=>v.state()),child_close_observed:false,
      resource_ready:false,automatic_retry:false}); }
    catch { failCapture('LIVE_STATE_PERSISTENCE_FAILED'); }
  };
  const env = makeEnvironment(s);
  writeNew('launch-plan.json', {executable:CODEX, argv:ARGV, cwd, env_keys_only:Object.keys(env).sort(), scope_sha256:scopeHash, root_job_proof:'EXTERNAL_F13_ONLY'});
  let child;
  try { child = spawn(CODEX, ARGV, {cwd, env, shell:false, windowsHide:true, detached:false, stdio:['ignore','pipe','pipe']}); }
  catch(error) {
    const message=String(error.message||'');
    spawnError={code:String(error.code||'SPAWN_THROW'),message_prefix:message.slice(0,2048),message_sha256:digest(message),message_truncated:message.length>2048};
    liveSnapshot('UNKNOWN_SYNCHRONOUS_SPAWN_ERROR_NO_RETRY');
    throw error;
  }
  // No child.kill/process.exit/PID-name operations; f13 owns all hard termination.
  const timer = setTimeout(() => {
    timedOut = true;
    for(const stream of streams) stream.markTimeout();
    liveSnapshot('UNKNOWN_SOFT_TIMEOUT_AWAITING_ROOT_JOB');
    process.stderr.write('MXC_WRAPPER_TIMEOUT_AWAITING_ROOT_JOB\n');
  }, s.timeout_ms);
  for (const stream of streams) {
    stream.attach(child[stream.name]);
    child[stream.name].on('data', chunk => {
      stream.accept(chunk);
      if(stream.limitReached||stream.persistenceFailed) liveSnapshot('UNKNOWN_LIMIT_OR_IO_FAILURE_AWAITING_ROOT_JOB');
    });
    child[stream.name].on('error', error => {stream.recordError(error);liveSnapshot('UNKNOWN_STREAM_ERROR_AWAITING_ROOT_JOB');});
    child[stream.name].on('end', () => stream.markEnd());
  }
  child.on('error', error => {
    const message=String(error.message||'');
    spawnError = {code:String(error.code || 'SPAWN_ERROR'), errno:error.errno ?? null, syscall:String(error.syscall || ''),
      message_prefix:message.slice(0,2048),message_sha256:digest(message),message_truncated:message.length>2048};
    liveSnapshot('UNKNOWN_SPAWN_ERROR_AWAITING_CHILD_CLOSE');
  });
  await new Promise(resolve => child.once('close', (code, signal) => {exitCode=code;exitSignal=signal;resolve();}));
  clearTimeout(timer);
  const evidence = streams.map(stream => stream.finish());
  const stdout = fs.readFileSync(streams[0].prefixPath);
  const exactEcho = streams[0].ingested === stdout.length && (stdout.equals(Buffer.from('MXC_OK\r\n')) || stdout.equals(Buffer.from('MXC_OK\n')));
  const drift = FIXED.some(([p,pin]) => fileSHA(p) !== pin) || fileSHA(SELF) !== s.wrapper_sha256 || fileSHA(scopePath) !== scopeHash;
  const observed = exitCode === 0 && !spawnError && !timedOut && evidence.every(v=>v.stream_complete) && exactEcho && !drift && observationErrors.length === 0;
  const result = {status:observed?'MXC_ECHO_CHILD_CLOSED_REQUIRES_ROOT_STOP_PROOF':'FAILED_OR_UNKNOWN_NO_RETRY',
    exit_code:exitCode,exit_signal:exitSignal,spawn_error:spawnError,timed_out:timedOut,input_drift:drift,observation_errors:observationErrors,
    exact_echo:exactEcho,streams:evidence,child_close_observed:true,root_job_stop_proof:'EXTERNAL_F13_ONLY',
    resource_ready:false,product_can_submit:false,formal_increment:0,product_increment:0,model_tasks:0,automatic_retry:false};
  writeNew('RESULT.json', result);
  process.stdout.write(JSON.stringify({status:result.status,resource_ready:false,model_tasks:0})+'\n');
  process.exitCode = observed ? 0 : 1;
}
main().catch(error => {
  // No raw diagnostic or path/credential-bearing exception dump.
  process.stderr.write(JSON.stringify({status:'BLOCKED_OR_UNKNOWN_ROOT_READBACK_REQUIRED',code:error.code || 'WRAPPER_ERROR',automatic_retry:false})+'\n');
  process.exitCode = 2;
});

