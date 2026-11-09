"""C evidence sealing only. Does not run child, build, GUI or model."""
from datetime import datetime,timezone
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name,v):
    with (ROOT/name).open('x',encoding='utf-8',newline='\n') as f:
        if isinstance(v,dict):json.dump(v,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
        else:f.write(v)
assert not (ROOT/'MANIFEST.json').exists(),'Frozen packet already exists; read back, no replay'
pin=sha(ROOT/'owned_run.py')
assert pin=='f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c'
actual=[]
for directory in sorted((ROOT/'runs').iterdir()):
    result=json.loads((directory/'RESULT.json').read_bytes())
    scope=ROOT/'scopes'/(directory.name+'.json')
    plan=json.loads(scope.read_bytes())
    assert plan['controller_sha256']==pin and result['scope_sha256']==sha(scope)
    assert result['stop_proved'] and result['root_signaled'] and result['job_active_zero'] and result['errors']==[]
    assert result['close_order'][0]=='job'
    for raw in result['raw']:assert sha(directory/raw['file'])==raw['sha256']
    actual.append({key:result[key] for key in ['scope_id','status','job_assigned','resumed','root_exit_code','creation_filetime',
        'root_signaled','job_active_zero','stop_proved','job_total_processes','terminate_job_attempts','elapsed_seconds']})
assert len(actual)==5
put('CHECKS.json',{'schema':'researchos.owned-run-author-checks.v1','status':'AUTHOR_CHECKED_PENDING_INDEPENDENT_REVIEW',
    'pure_initial':{'started':'dcac00','session':34596,'terminal':'97fc18','exit':0,'test_functions':2,'fault_subcases':6,'real_jobs':0},
    'final':{'started':'057eaf','session':64792,'terminal':'9e607e','exit':0,'py_compile_exit':0,'test_functions':7,
        'actual_fresh_owned_jobs':5,'pure_test_functions':2,'pure_fault_subcases':6,'elapsed_test_seconds':3.705},
    'post_run_readback':'c8d4ff exit0; no service/process scan','actual_results':actual,
    'job_accounting_note':'Observed per-Job totals3/3/3/2/2; not an assertion about executable roles. No outside PID/name scan or PID-based kill was performed.',
    'D_builds':0,'GUI_or_Electron_launches':0,'model_calls':0,'old_scope_replays':0,'external_network_calls':0,'formal_increment':0})
put('AUTHOR-DIAGNOSTICS.json',{'author_failed_batches':0,'uncertain_operations':[],
    'source':'New independent C controller, no old supervisor executable/authorization/process resources reused',
    'changes_before_actual_run':'Post-stop hashes skipped on unconfirmed cleanup; actual five scopes all bind final f13f630d controller',
    'outcomes':'All5 own jobs stopped and all original handles closed; all5 consumed scope directories retained; no automatic deletion/retry.',
    'failure_policy':'Any failed/uncertain future run preserves CONSUMED/raw/result. Missing RESULT is UNKNOWN, not permission to replay; a new name is not an implicit retry grant.',
    'old_project_failure_counters':'Untouched; no resets or re-indexing of earlier origins',
    'D_source_writes':0,'product_or_model_execution':0,'construction_frozen':True,'source_modification_permitted':False})
template={'schema':'researchos.owned-windows-run/1','scope_id':'REPLACE_WITH_NEW_ROOT_SCOPE','purpose':'build',
    'authorization':'TEMPLATE_NOT_AUTHORIZATION','controller_sha256':pin,
    'executable':'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe',
    'executable_sha256':'cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b',
    'argv':['-B','-X','utf8','<exact-reviewed-W>/apps/desktop/build-development.py','<all-exact-reviewed-build-flags>'],
    'cwd':'<exact-reviewed-W>','inputs':[{'path':'<exact-reviewed-W>/apps/desktop/build-development.py','sha256':'<FILL_EXACT_REVIEWED_SHA256>'}],
    'timeout_seconds':1200,'graceful':'none','grace_seconds':0,'cleanup_seconds':5,
    'process_limit':32,'memory_mib':4096,'max_raw_bytes':67108864,
    'env':{'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off'}}
put('BUILD-SCOPE-TEMPLATE.json',template)
gui={**template,'purpose':'gui','executable':'C:/nvm4w/nodejs/node.exe',
    'executable_sha256':'5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6',
    'argv':['<exact-sealed-bundle>/launch-development.mjs','--bundle','<exact-sealed-bundle>','--state','<never-existing-owned-state>','--launch','--smoke'],
    'cwd':'<exact-sealed-bundle>','inputs':[{'path':'<exact-sealed-bundle>/launch-development.mjs','sha256':'<FILL_SHA256>'},
        {'path':'<exact-sealed-bundle>/development-manifest.json','sha256':'<FILL_SHA256>'}],
    'timeout_seconds':120,'env':{}}
put('GUI-SCOPE-TEMPLATE.json',gui)
put('README.md','''# New owned Windows Job supervisor

Entry: owned_run.py with the fixed Python3.14 executable, -I -S -X utf8, --scope <new scopes/file.json> --scope-sha256 <exact-reviewed-file-hash>. It creates the derived runs/<scope_id> exclusively and fsyncs CONSUMED before any creation. Existing scope/output is never removed or retried. All five author fixture scopes are permanently consumed. Templates deliberately fail authorization and are not runnable until Root separately registers and pins an exact new build/GUI scope after independent review.

Actual code path is preallocated PROCESS_INFORMATION inside the same protected ownership region -> CreateProcessW(CREATE_SUSPENDED|CREATE_NO_WINDOW|EXTENDED_STARTUPINFO_PRESENT|CREATE_UNICODE_ENVIRONMENT) -> AssignProcessToJobObject -> actual IsProcessInJob -> ResumeThread. A private unnamed Job has KILL_ON_JOB_CLOSE, active-process and Job-memory limits, and no breakaway flags. STARTUPINFOEX only inherits stdin NUL, the two new regular raw files and an optional private event. Job handle is never inherited. Cancel/exception cannot rediscover or kill by PID/name; pre-Assign uncertainty uses the original newly-created suspended root handle as a fallback. Original process/thread handles remain held through stop observation and exit-code capture.

One owner polls the original root signal and that Job's accounting, using monotonic timeout. Primary exit alone never completes the run while descendants remain. At timeout it optionally signals only the predefined inherited manual-reset event, gives a bounded grace, then TerminateJobObject. Event mode requires a separately reviewed child harness to wait on OWNED_VERIFICATION_STOP_EVENT and perform its own graceful shutdown. Existing development launcher does not implement this event, so the GUI template correctly defaults to none; do not claim an event invokes management shutdown by itself. Normal Electron smoke already attempts its own management shutdown before exit.

Cleanup has one bounded budget; it requires original root signal plus observed JobActive0, then closes Job before all file/diagnostic operations. Close is a kernel fail-safe, not a substitute for observed zero. There is no output pipe, communicate(), stream-EOF join, PID/name scan or watchdog holding a stale numeric handle. Raw stdout/stderr go directly to new files; hashes are produced only after stop proof. Missing proof keeps raw unsealed and status UNKNOWN. File-size threshold is sampled, not a disk quota: one output burst may overshoot the configured value. Recheck available disk before build and scope a realistic cap.

Child environment is built from fixed public Windows/Git/Node paths plus fresh profile/APPDATA/TEMP, without copying ambient env. Only explicit offline Go keys are accepted; proxy/APIKEY/token/NODE_OPTIONS/PYTHONPATH/PATH overrides are refused. Do not put secrets in argv or a scope. Scope argv, executable SHA, controller SHA and input pins are reviewed public data. Job limits are lifecycle/resource containment, not filesystem/network/AppContainer isolation; these Python fixtures intentionally made no network calls. Reparse output parents are refused, and no previous user DB/profile/credentials are copied.

Author validation actually ran five new C jobs: normal root/grandchild, root+descendant timeout, root-exit0 with lingering descendant, predefined event grace and sampled output cap. Every run confirmed assignment/resume, original creation time and exit code, root signal, JobActive0, zero errors and Job-first close order. The root0/lingering-child case remained TIMED_OUT_STOPPED, never completed success. Seven tests plus py_compile passed9e607e; two pure tests cover six Create/Assign/Resume/Query/Terminate failure branches and secret-env rejection. Mock failure tests use no OS processes. Per-Job totals3/3/3/2/2 are actual accounting, not guessed process roles. All scope/CONSUMED/RESULT/raw files are retained and manifest-pinned. None of this is product build, installer, GUI, model readiness or business acceptance.

Minimal Root integration: copy the invalid BUILD-SCOPE-TEMPLATE to a new file under scopes/, replace all placeholders with the exact reviewed integrated V1 worktree/build recipe, bind every relevant script/manifest as inputs, select explicit timeout/process/memory/raw budgets, change authorization to ROOT_REVIEWED_EXACT_COMMAND only after review and record the scope digest. Invoke the controller once; read the derived RESULT and raw files. A COMPLETED_OWNED_JOB_STOPPED status only means the scoped process tree stopped with root exit0; validate the child's own source-bound build result and drift manifests separately. For GUI use a new scope/state and GUI template; verify actual ready/shutdown events, screenshots/user flows and artifacts separately. This controller never grants Native/model/paid authorization and no prior UNKNOWN/model scope can be reused.

Limits: process creation, kernel calls (including file-size metadata), filesystem operations, power loss, externally killed owner and repeated asynchronous interruption cannot be given an absolute in-process wall-clock guarantee. No Python file logging/read/hash/Sync occurs between Resume and bounded ownership polling. Journal writes and post-stop hashing may fail or block after kernel cleanup; a missing/incomplete RESULT is UNKNOWN and never replay permission. If a result or tool transport is uncertain, inspect the one consumed attempt first. No automatic retry or failure-counter reset exists.

Controller construction is now frozen for independent review. No D source/build, GUI/Electron, model, external network, old DB/credential read or old process/resource scope was used in this preparation. Do not rerun test_owned_run.py against its consumed fixture IDs. Independent tests require newly authorized fresh scopes; do not edit the frozen author packet.
''')
put('INVOKE-NOT-EXECUTED.txt','''After independent controller review and a separate Root exact build/GUI scope only:

& 'C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe' -I -S -X utf8 `
  'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-owned-verification-20261104/owned_run.py' `
  --scope 'C:/Users/yqyyds/Documents/Codex/2026-11-04/task/product-v1-owned-verification-20261104/scopes/<NEW-ROOT-SCOPE>.json' `
  --scope-sha256 '<EXACT-REVIEWED-SCOPE-SHA256>'

Read runs/<NEW-ROOT-SCOPE>/RESULT.json, CONSUMED.json, stdout.raw and stderr.raw. Do not invoke fixture01..05 or overwrite their journals.
''')
files=[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(ROOT.rglob('*'))
    if p.is_file() and '__pycache__' not in p.parts and p.name!='MANIFEST.json']
put('MANIFEST.json',{'schema':'researchos.product-v1-owned-supervisor.v1','status':'AUTHOR_NATIVE_C_FIXTURES_PASSED_PENDING_INDEPENDENT_REVIEW',
    'at':datetime.now(timezone.utc).isoformat(),'owner':'codex:/root/runtime_readiness','controller_sha256':pin,
    'tests_sha256':sha(ROOT/'test_owned_run.py'),'fixture_sha256':sha(ROOT/'fixtures/child.py'),
    'construction_frozen':True,'source_modification_permitted':False,'production_build_GUI_authorized':False,
    'actual_new_C_Job_tests':5,'py_compile_exit':0,'author_test_exit':0,'scope_consumptions':5,
    'D_source_writes':0,'D_builds':0,'GUI_launches':0,'model_calls':0,'old_qualification_replays':0,'formal_increment':0,
    'excluded':['__pycache__ (derived interpreter cache; no authority)'],'files':files})
print(json.dumps({'manifest_sha256':sha(ROOT/'MANIFEST.json'),'controller_sha256':pin,'files':len(files),
    'actual_owned_C_jobs':5,'D_builds':0,'GUI':0,'models':0,'construction_frozen':True}))
