"""Static review only. Never launch the controller, server, GPU or HTTP requests."""
from pathlib import Path
import datetime, hashlib, json
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reviews/source-review.json'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
expected={'SCOPE.json':'082f8b862d72fceb8534aa3759bf9e9eed11f046f8fed9f3281f97eb8401074f','PREPARED-MANIFEST.json':'59f7e04eb4b191df0f3483a5937d760bbef6e06d1ced5e8150d03116ec4bcbbb','main_windows.go':'873318865754eaf6cb209053d97e07b5b1cc01b500d01f0d473ee6180a43e9db','controller.exe':'78fbd65b1caa2380ea7d2e19f9e3fca87ac6655ed3ce538240ea665af19f084b'}
assert all(sha(ROOT/name)==digest for name,digest in expected.items())
manifest=json.loads((ROOT/'PREPARED-MANIFEST.json').read_bytes())
checks=[]
for item in manifest['files']:
    path=ROOT/item['relative']
    checks.append({'path':item['relative'],'sha256':sha(path),'bytes':path.stat().st_size})
    assert checks[-1]['sha256']==item['sha256'] and checks[-1]['bytes']==item['bytes']
report={
 'schema':'researchos.owned-model-stage-b-independent-source-review.v1',
 'reviewer':'/root/implementation_review',
 'job_static_reviewer':'/root/implementation_review/prompt_flow_review',
 'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'decision':'REQUIRES_CHANGES_DO_NOT_EXECUTE_CURRENT_FROZEN_CONTROLLER',
 'root_one_elevated_execution_admitted':False,
 'frozen_inputs_sha256':expected,
 'manifest_files_checked':checks,
 'run01_existed_at_readback':(ROOT/'run-01').exists(),
 'findings':[
  {
   'id':'STGB-P1-001','severity':'P1','blocking':True,
   'title':'Listener ownership is not bound to the actual HTTP connection',
   'source':'main_windows.go:570-595 (listenerPID/ownsPID then ordinary DialContext/client.Do)',
   'evidence':'metadataGET first snapshots the LISTENER table and checks a held live Job process, then constructs a plain net.Dialer transport. No ownership proof is coupled to the concrete TCP connection that carries the request.',
   'trigger':'The owned listener passes the check, then exits before Dial. An unrelated local service binds the now-free 43861 port. The ordinary transport can connect to that replacement and send GET /api/version or /api/tags. The fixed-port preflight and held old process handle do not prevent this sequence.',
   'impact':'Violates the declared no-foreign-GET boundary. A later metadata mismatch or cleanup failure cannot undo the request already sent.',
   'minimum_required_change':'Bind endpoint ownership to the concrete connected socket before writing any HTTP bytes. One feasible design is a custom DialContext that dials only the declared endpoint, obtains the actual client/server tuple, checks the corresponding server-side established TCP owner PID via a bounded passive OS lookup and verifies that PID against a held live owned-Job process, closing/failing on absent or ambiguous ownership. Keep the one-use request count, no proxy/redirect/retry policy, budget and exact endpoint. Review any added connection ownership query explicitly; do not scan alternative endpoints.',
   'required_static_or_pure_fixture_checks':['Owned LISTENER disappearing/replaced between precheck and dial cannot cause any HTTP Write.','Absent/foreign/ambiguous established tuple fails closed and closes its socket.','The check uses the actual socket tuple, not a second snapshot of only the listening port.']
  },
  {
   'id':'STGB-P1-002','severity':'P1','blocking':True,
   'title':'Unbounded monitor join can block the final Job fail-safe; watchdog is not synchronized before handle close',
   'source':'main_windows.go:478-486;655-678;747-757;759-838',
   'evidence':'The Job CloseHandle defer is registered before t.close, so t.close runs first. t.close waits indefinitely on t.done. The watcher may be in describe/hashFile io.Copy (326-344/112-122) or synchronous journal I/O (84-94). The 15-second cleanup deadline covers the main polling/drain logic but does not bound this join. watchdogDone is closed on return without waiting for the goroutine to acknowledge termination before the captured Job handle is later closed.',
   'trigger':'TerminateJobObject fails or the owned Job is not proved empty by the deadline. The main cleanup marks failure, but a blocked monitor join prevents reaching the last Job handle close that supplies KILL_ON_JOB_CLOSE. Separately, a late watchdog scheduling branch can retain a numeric Job handle across its owner closing that handle.',
   'impact':'The promised native cleanup deadline and final kill-on-close path are not guaranteed by this defer order; a late watchdog may use a closed/reused handle value.',
   'minimum_required_change':'Make Job termination/final fail-safe closure independent of unbounded monitor work. Apply the one absolute cleanup deadline to monitor completion as well, preserve an honest unproved-cleanup result, and ensure the Job handle has a single synchronized lifecycle: the watchdog must acknowledge stopping (or use an equivalent safe ownership mechanism) before the handle can be closed/reused. Do not introduce a second unbounded join before the only fail-safe, do not kill any pre-existing process, and do not turn missing child/event/stream evidence into success.',
   'required_static_or_pure_fixture_checks':['A deliberately stalled monitor cannot postpone the owned Job final-close path beyond the cleanup policy.','A deadline or interrupt racing normal return cannot cause TerminateJobObject on a closed/reused handle.','Tracking gaps, unsignaled handles or undrained streams continue to yield failure with no post-stop unchanged-assets claim.']
  }
 ],
 'verified_static_boundaries':[
  'Creation uses PROC_THREAD_ATTRIBUTE_JOB_LIST (0x0002000d) plus CREATE_SUSPENDED, then proves membership and writes exact creation FILETIME before ResumeThread. Job has KILL_ON_JOB_CLOSE and active process limit32, with no breakaway flag.',
  'HANDLE_LIST contains only NUL/stdout/stderr. Job and IOCP monitoring handles are not inherited. x/sys attribute container retains pointer backing storage. The exact returned primary handle is held independently from watcher duplicates.',
  'No adoption or name/PID/port-based killing of pre-existing processes. Normal termination targets the private Job; pre-resume unproved membership fallback uses only the exact returned new primary handle.',
  'Child environment is a new explicit UTF-16 whitelist: private profile/AppData/tmp, trusted runtime/System32 PATH and six named OLLAMA settings. Existing proxy/token/API-key/profile variables are not inherited. The controller never opens generated new profile keys.',
  'One fixed43861 preflight, conflict/access error stops before launch, no alternative port or endpoint scan. Passive listener table output is restricted to the declared port.',
  'Only GET /api/version and /api/tags are callable once each; attempts journal before transmission, no payload/credentials, proxy nil, redirects refused, fresh non-keepalive transport,5s and64KiB bounds. No inference/POST/pull/chat code path is present.',
  'Tracker records held handles, creation times and image hashes, checks owned membership and NEW_PROCESS roster against Job totals. Missing events/handles/PID reuse fail closed; no claim that IOCP can always capture a very short-lived child.',
  'Cleanup checks Job active0, all held handles signaled, all events accounted and true stream drain under one main deadline. It skips post-stop asset claim when cleanup is unproved; after proved shutdown it verifies all981 StageA asset hashes/roster and unused empty StageA profiles.',
  'Exclusive run-01 and O_EXCL evidence files prevent automatic replay or overwrite. Result retains resource_ready=false and formal_increment0. No success is declared by this static review.'
 ],
 'compile_evidence':{
  'BUILD-03.json':json.loads((ROOT/'BUILD-03.json').read_bytes()),
  'VET-01.json':json.loads((ROOT/'VET-01.json').read_bytes()),
  'qualification':'Author-recorded offline compile/vet exit0 for the pinned reviewed source; this review verifies their frozen bytes. No independent controller execution or native lifecycle test was performed.',
  'old_build01_failure_and_revision02_preserved':True
 },
 'next_step':'Preserve this frozen source/scope/binary and previous failures. Produce a new explicit revision and new pins for the two P1 fixes, then independently review before any Root execution. The present scope is not admitted for one elevated live metadata run.',
 'diagnostics':[],
 'review_operations':{'source_writes':0,'controller_runs':0,'server_or_gpu_starts':0,'HTTP_GETs':0,'inference':0,'old_database_connections':0,'D_writes':0,'counter_reset':False,'formal_increment':0},
 'evidence_chunks':['ae82aa','02273d','163956','ae3760','3dfec7','042234','616f72']
}
with OUT.open('x',encoding='utf-8',newline='\n') as stream:json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
print(json.dumps({'path':str(OUT),'sha256':sha(OUT),'decision':report['decision']},ensure_ascii=False))
