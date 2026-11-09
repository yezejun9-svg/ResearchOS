"""Read public sources and write only a new C analysis packet. No execution."""
from datetime import datetime,timezone
import hashlib,json,shutil
from pathlib import Path
BASE=Path('D:/作品集/ResearchOS/research-os')
OUT=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-sandbox-cleanup-readonly-20261104')
REVIEW=Path('C:/Users/yqyyds/Documents/Codex/2026-11-04/task/cp598-coding-delivery-scope-review/sandbox-child-drain-review.md')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,value):
    with (OUT/name).open('x',encoding='utf-8',newline='\n') as stream:
        if isinstance(value,dict):json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')
        else:stream.write(value)
assert not OUT.exists(),'Existing packet: read back, never replay'
assert sha(REVIEW)=='b7b75c0fdaed4b88f9652a340e98ef9535c8c2528d001901569d7f37565c763e'
OUT.mkdir()
paths=['ops/experiment_sandbox/sandbox_windows.go','ops/experiment_sandbox/async_windows.go',
       'ops/experiment_sandbox/recovery_windows.go','ops/experiment_sandbox/async_windows_test.go',
       'ops/experiment_sandbox/sandbox_windows_test.go','ops/experiment_sandbox/native_go_windows_test.go',
       'adapters/runtime/bridge_windows.go','internal/host/runtime_check_windows.go']
pins=[]
for rel in paths:
    source=BASE/rel;raw=source.read_bytes();pin=hashlib.sha256(raw).hexdigest()
    dest=OUT/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    assert sha(source)==pin,'Source changed during readonly capture'
    pins.append({'path':rel,'sha256':pin,'bytes':len(raw)})
shutil.copyfile(REVIEW,OUT/'prior-child-drain-review.md')
put('SOURCE-MANIFEST.json',{'baseline_head':'001f7e5a4d95152c8f83874a60d9fbd3bbace538',
    'identity_check':'e85c4a exit0; Git sandbox-only status empty','source_pins':pins})
put('MINIMAL-SCOPE-PROPOSAL.json',{
    'status':'READONLY_PROPOSAL_NOT_AUTHORIZATION_TO_EDIT_OR_RUN',
    'native_activation_blocker':True,'construction_owner_registered':False,
    'proposed_production_paths':['ops/experiment_sandbox/sandbox_windows.go','ops/experiment_sandbox/async_windows.go'],
    'proposed_new_test_path':'ops/experiment_sandbox/lifecycle_windows_test.go',
    'new_test_path_reserved':False,'public_command_receipt_schema_change':False,
    'untouched':['recovery_windows.go','Native qualification journals','runtime/Host callers','public Process API','existing native tests'],
    'policy_recommendation':'Preserve primary lifetime and command deadline; preserve current500ms post-primary grace; if descendants remain, terminate owned Job and return explicit forced-descendant error even if primary exit0. No detached-child success expansion.',
    'must_be_explicit_in_root_scope':['500ms grace is a compatibility boundary, not permission for detached success',
       'One bounded cleanup deadline covers terminate/primary signal/Job-zero/drain; exact budget to be pinned before implementation, proposed5s',
       'No success until original primary signaled + observed JobActive0 + natural complete EOF for both streams; forced read close/callback timeout never equals drained',
       'KILL_ON_CLOSE final fallback executes before diagnostic/callback/pipe waits; stale raw handles and concurrent Cancel Terminate are forbidden',
       'Unconfirmed termination retains incomplete receipt and owned staging/profile for separately authorized recovery; no output copy or success cleanup claim']})
put('LIFECYCLE-SEAM.json',{
    'visibility':'package-private only; production creates adapter from original held handles; no public fake Native injection',
    'placement':'Small coordinator/types in sandbox_windows.go, stream result/wakeup plumbing in async_windows.go; no additional scheduler/backend',
    'single_owner':'runSandbox coordinator owns Job/process handle close, terminate and accounting; Process.Cancel continues context notification, never stores/reopens raw Job handle',
    'injected_ops':['clock.Now','bounded primary wait/signal','Job accounting(total,active)','TerminateJob on original handle','CloseJob once','primary exit query','stream-result notifications','owned pipe close after fail-safe'],
    'states':['RUNNING','PRIMARY_EXITED_GRACE','STOPPING_JOB','DRAINING_STREAMS','DONE_OR_INCOMPLETE'],
    'order':['While RUNNING retain existing interactive input and original command timeout.',
       'On primary signal cache exitcode; continue context/deadline/stream-fault checks during <=500ms grace. JobActive0 permits natural drain.',
       'Cancel/deadline/stream error or active descendants after grace sends at most one owned termination request; preserve original reason and classification.',
       'Within one cleanup deadline observe original primary signaled and JobActive0. If query/terminate/wait fails, never invent stopped.',
       'Close original Job as final kernel fallback before any potentially unbounded stream/callback/diagnostic join. No goroutine captures its raw numeric handle.',
       'Only then wait on buffered stream results with remaining deadline. Force-close read ends on missing EOF; return incomplete, never StreamsDrained=true.',
       'Copy output/delete staging/profile only under the explicitly supported stop/drain conditions; aggregate real errors without promoting flags.'],
    'callback_limit':'A blocked arbitrary OnStream Go callback cannot be forcibly stopped. Cleanup must not wait for it before Job termination/close. Missing callback completion is incomplete; late writes/goroutine ownership require explicit quarantine/retention, not a claimed drain proof.',
    'blocking_OS_limit':'No in-process Go design proves bounded return if kernel calls never return. Filesystem copy/remove, profile calls and BeforeResume callbacks also need truthful separate bounds; no claim they became bounded merely by this coordinator.',
    'no_claim':'No mock establishes actual AppContainer/Job stop or Native qualification.'})
matrix=[
 ('parent0-active-child-held-pipes','grace expires -> terminate once -> observe primary signal+active0 -> closeJob -> EOF/drain; forced descendant error prevents success'),
 ('normal-single-process','primary0+active0+two natural EOFs preserves successful receipt'),
 ('child-finishes-within-grace','active child exits <=500ms; no forced terminate, successful natural drain'),
 ('child-longer-than-grace','explicit forced cleanup error; do not silently support detached success until original command deadline'),
 ('interactive-primary-alive','no premature termination on open input/temporarily idle streams; original max5min/15min opt-in unchanged'),
 ('cancel-each-phase','RUNNING/grace/stopping/draining observes cancellation and never depends on future parent polling'),
 ('command-timeout','legacy TimedOut/124 classification retained; cleanup budget is separate and cannot reset command deadline'),
 ('queued-write-caller-cancel','waiting writeGate40ms cancellation does not cancel active writer/Job; existing contract preserved'),
 ('active-write-timeout','p.cancel notification remains actionable after parent signal and releases owned input only through owned stop'),
 ('job-query-terminate-primary-wait-error','no stopped/drained flags without observations; close fallback happens once before stream waits'),
 ('missing-stream-or-held-callback','owner can terminate/close Job before bounded stream completion; never unbounded channel receive/join'),
 ('stream-overflow-callback-error','cancel survives parent exit; no truncated stream promoted to drained'),
 ('cleanup-order-and-stale-handle','fake operations assert terminate/query/close order; no operations after Job close or handles reused'),
 ('pre-resume-veto-create-error','startup failure cleans owned resources without waiting nonexistent EOFs; BeforeResume progress is separate bounded-trusted contract'),
 ('copy-delete-profile-errors','do not equate staging RemoveAll success with all handle/profile cleanup; truthful incomplete/error')]
put('PURE-TEST-MATRIX.json',{'status':'DESIGN_ONLY_NOT_EXECUTED','entry_proposal':'go test ./ops/experiment_sandbox -run ^TestSandboxLifecycle -count=1',
    'execution_requires_new_root_scope':True,'real_ops_forbidden':['Run','Start','Windows.CreateProcess','AppContainer/profile creation','os.Pipe real handles','Native qualification','model/provider'],
    'fixtures':'Call actual private coordinator with fake operations/clock/channels; never tests that only restate constants or infer native behavior from labels.',
    'cases':[{'id':name,'expected':expected} for name,expected in matrix]})
put('DIAGNOSTICS.json',{'source_reads':['5faf49','12f891','d6df30','2d9357','e85c4a'],
    'default_git_read':'d5177f exit1 Permission denied; no mutation; elevated readonlye85c4a exit0 supplied identity/status',
    'child_readonly_diagnostic':'ac5763 PowerShell pipeline syntax error; corrected e0ba33 exit0; no product/Native attempt. Child finalized and released slot.',
    'existing_prior_review_sha256':sha(REVIEW),'tests_run':0,'native_starts':0,'model_calls':0,'probe_replays':0,'D_writes':0,
    'process_scans_or_kills':0,'credential_reads':0,'failure_counter_reset':False,'construction':False})
put('REPORT.md','''# Sandbox cleanup activation blocker — readonly scope preparation

Current Main001f7e5a and empty sandbox-only Git status were read at e85c4a. The eight public source snapshots are pinned. Existing independent child-drain review b7b75c0f is included, not reinterpreted as native evidence. No implementation or test was run; no D file was written.

The verified path is sandbox_windows.go343: primary signal breaks the only context/timeout loop (checks346), then Job accounting is polled for at most500ms (368-374). Line376 receives both streams without a bound. A live child retaining stdout/stderr keeps the reader open, preventing return and the KILL_ON_JOB_CLOSE defer212. Cancel async_windows.go162 only cancels context and closes input, so after the earlier loop has ended it cannot reach TerminateJob. collectStream180-212 calls OnStream inline; a blocked callback is a second reason its result never arrives. These are source-level control-flow findings; no native reproduction was attempted.

Minimum recommended future scope: sandbox_windows.go, async_windows.go, plus new lifecycle_windows_test.go. Keep Command/Receipt wire and public Process API. Extract a private real lifecycle coordinator with injected clock/accounting/terminate/signal/stream-result operations. The production adapter uses only original held handles, single-owner termination and close, and buffered result notifications. Cancel must be observed in every phase; putting a raw Job handle in Process.Cancel would introduce a stale-handle race and is unnecessary.

Preserve the existing500ms child grace rather than silently expanding detached-child success. Primary remains live: original interactive semantics and command timeout apply. Primary exits: child completion within grace can finish normally; remaining descendants must be terminated and confirmed stopped before bounded drain, with an explicit forced-descendant error even if primary exit0. This changes their running duration, but the old code already sampled Stopped=false beyond500ms and callers could not accept those receipts. Waiting the whole Job until the command deadline and newly accepting such child success would be a separate explicit semantic expansion.

On every stop path, first terminate this owned Job and confirm the original primary signal plus JobActive0 under one cleanup deadline, proposed5s to be finalized in Root scope. Job fail-safe close cannot depend on callback, logging, channel join, pipe EOF or file cleanup. If confirmation fails, close the Job as the final kernel fallback but keep stopped/drained false and retain an unusable/UNKNOWN outcome; no inference from Terminate success alone. Only after kernel stop/close should a bounded stream-result wait occur. Forced pipe close, missing EOF, blocked callback and stream errors never equal StreamsDrained. No output copy/delete should race unconfirmed processes or late callback activity.

An arbitrary blocked Go callback cannot be forcibly stopped. Returning boundedly while such a callback remains requires explicit quarantine/retention and honest incomplete status; otherwise a late callback may write after receipt or staging cleanup. Do not claim this small lifecycle fix bounds arbitrary BeforeResume work, filesystem calls, nonreturning Windows calls or all cleanup. Current CleanupComplete only records staging RemoveAll (154-157); profile deletion and handle close errors are currently ignored. They are not certified complete by the existing flag.

Actual callers need this ownership: Run84-89 and Bridge519 use Wait(background), not Wait(cancelledctx). Bridge319 uses Interactive;531 requires stopped+drained+outputcopied+cleanup. runtime_check_windows.go551-556 also refuses incomplete receipts. Replacing Wait(background) with Wait(ctx) would return an empty receipt while the child can still run and allow caller cleanup to race live work. Recovery CleanupAbandoned verifies only recorded primary PID/creation; it is not Job-zero evidence or permission to scan/kill old processes. No abandoned cleanup was invoked.

Fifteen proposed pure fake cases exercise the actual coordinator, including the primary-exit/held-child counterexample, each-phase cancellation, EOF/callback stalls, error order, interactive completion and queued Write cancellation. Existing Windows native tests do not cover this orphan-held-pipe case and must not be replayed as qualification recovery. Later actual child/pipe validation needs an entirely new explicit scope and isolated owned resources; previous Native/UNKNOWN approvals and failures remain consumed and unchanged. This packet is a prerequisite design branch, not authorization to edit or enable Native execution.
''')
inventory=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
put('MANIFEST.json',{'schema':'researchos.sandbox-cleanup-readonly-preparation.v1','status':'READONLY_BLOCKER_PREPARED_NOT_IMPLEMENTED',
    'at':datetime.now(timezone.utc).isoformat(),'owner':'codex:/root/runtime_readiness','baseline_head':'001f7e5a4d95152c8f83874a60d9fbd3bbace538',
    'native_activation_blocked':True,'source_modification_permitted':False,'tests_executed':0,'native_executions':0,'model_calls':0,'D_writes':0,
    'failure_counter_reset':False,'formal_increment':0,'source_pins':pins,'files':inventory})
print(json.dumps({'status':'READONLY_BLOCKER_PREPARED_NOT_IMPLEMENTED','path':str(OUT),
    'manifest_sha256':sha(OUT/'MANIFEST.json'),'file_count':len(inventory),'source_count':len(pins),
    'native':0,'model':0,'tests_run':0,'D_writes':0}))
