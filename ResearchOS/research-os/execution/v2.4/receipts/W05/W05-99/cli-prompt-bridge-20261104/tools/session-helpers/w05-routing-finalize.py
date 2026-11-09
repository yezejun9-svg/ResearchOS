"""Finalize author metadata only; frozen source and global state stay read-only."""
import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w05-runtime-routing-20261104')
MAIN=Path('D:/作品集/ResearchOS/research-os')
OUT=MAIN/'execution/v2.4/receipts/W05/W05-99/continue-cp579-20261104/routing-author'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest_json(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def put(name,value):
    path=OUT/name
    if path.exists():raise RuntimeError('refuse existing author metadata: '+str(path))
    temp=path.with_name(path.name+'.new')
    if temp.exists():raise RuntimeError('uncertain previous metadata write: '+str(temp))
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temp.replace(path)

input2=load(OUT/'checks-02/inputs.json')
frozen=input2['source_sha256']
actual={name:sha(ROOT/name) for name in frozen}
if actual!=frozen:raise RuntimeError('frozen source changed; stop metadata finalization')
results=load(OUT/'checks-02/results.json')
if not all(row['matched_expected_exit'] for row in results):raise RuntimeError('checks02 not complete/expected')
first=load(OUT/'checks-01/results.json')
if not any(row['name']=='go-unit' and row['exit_code']==1 for row in first):raise RuntimeError('first compilation failure evidence missing')

registry_path=MAIN/'execution/v2.4/commands.json'
registry=load(registry_path)
container=registry.get('commands')
if not isinstance(container,dict) or 'test.runtime' not in container:
    raise RuntimeError('unexpected registry structure; no proposal generated')
before=container['test.runtime']
after=json.loads(json.dumps(before))
for check in ['W05-H08','W05-P01','W05-U02']:
    if check not in after['selectors']['check_id']:after['selectors']['check_id'].append(check)
after.setdefault('tool_env',{})['RESEARCHOS_PYTHON']='python'
after.setdefault('fixed_env',{})['RESEARCHOS_V24_SPEC_ROOT']='D:/作品集/ResearchOS/ResearchOS_Implementation_Package_v2.4'
for name in ['ops/ci/runtime_v24.py','tests/runtime/check/routing_test.go','tests/runtime/runtime_v24_test.py']:
    if name not in after['expected_artifacts']:after['expected_artifacts'].append(name)
after['note']='Exact selector routing: W05/W05-01 and W05/W05-02 keep their original Go development suites. Only W05/W05-G01 and W12/case C11 forward to ops/ci/runtime.py --mode fixture. W05/W05-G02,H08,P01,U02 and W05/case A04 route to the spec-pinned ops/ci/runtime_v24.py --mode live gap preflight; this preflight does not execute native/provider work and returns nonzero BLOCKED/IMPLEMENTATION_GAP with no passed assertion IDs until a current Mu formal driver is implemented. Mixed, unknown, incomplete, and cross-task selector tuples are rejected. Every Python launch resolves an absolute path from execution/toolchains/locked.json and verifies its SHA256 without PATH fallback. The registry-bound v2.4 specification root is machine-specific path debt; missing/drifted resources fail closed with no v2.0 fallback. No RESEARCHOS_RUNTIME_LIVE opt-in is fixed or implied. Existing GOPATH/GOCACHE absolute machine-path debt remains. Development routing checks do not constitute independent or formal product acceptance.'
proposal={
    'status':'PROPOSAL_ONLY_NOT_APPLIED','target':'execution/v2.4/commands.json','key':'test.runtime',
    'observed_registry_revision':registry.get('revision'),'requested_baseline_revision':40,
    'observed_registry_sha256':sha(registry_path),'before_entry_canonical_sha256':digest_json(before),
    'after_entry_canonical_sha256':digest_json(after),
    'apply_policy':'Root alone serially verifies current revision/hash and applies via the registry owner/CAS flow. Rebase this proposal if the observed registry changes; never overwrite unrelated dirty entries.',
    'changed_fields':['selectors.check_id','tool_env.RESEARCHOS_PYTHON','fixed_env.RESEARCHOS_V24_SPEC_ROOT','expected_artifacts','note'],
    'unchanged_fields':['executable_tool','argv','cwd','platforms','required_env','allowed_env','timeout_seconds','assertion_field','owner_card','owner'],
    'do_not_add':{'RESEARCHOS_RUNTIME_LIVE':'1'},
    'before_entry':before,'proposed_entry':after,
    'machine_path_debt':['RESEARCHOS_V24_SPEC_ROOT uses the user-authorized absolute Windows package root. Another host must explicitly rebind a v2.4 root with identical frozen hashes. Existing absolute GOPATH/GOCACHE debt is preserved.'],
}
put('registry-proposal.json',proposal)
diagnostics={
    'status':'AUTHOR_DIAGNOSTICS_ONLY_NO_LEDGER_MUTATION',
    'records':[
        {'kind':'read_diagnostic','action':'default-sandbox Git status on isolated D: worktree','observed':'fatal: this operation must be run in a work tree','resolution':'Elevated Git status subsequently returned clean and is-inside-work-tree true; no Git configuration changed.'},
        {'kind':'read_diagnostic','action':'default-sandbox explicit git-dir/work-tree status','observed':'fatal: this operation must be run in a work tree','resolution':'Use authorized require_escalated for D: worktree; no core.worktree/bare modification.'},
        {'kind':'author_compilation_failure','failure_origin':'w05-routing-author-go-unused-import-20261104','attempt_index':1,'evidence':'checks-01/go-unit','exit_code':1,'observed':'tests/runtime/check/w0501.go:14:2: "os/exec" imported and not used','repair':'Removed unused import left after replacing the old Python exec.Command. Original checks-01 artifacts remain intact.'},
        {'kind':'directed_retry','failure_origin':'w05-routing-author-go-unused-import-20261104','attempt_index':2,'evidence':'checks-02/go-unit','exit_code':0,'observed':'Pure route and locked-tool development tests passed. No reset of failure history.'},
        {'kind':'transport_diagnostic','action':'Post-test elevated read-only Git diff/check and report read','observed':'Failed to create unified exec process: exec-server transport disconnected','execution_state':'CreateProcess failed; no source or metadata write attempted by this read-only command. All test controllers already had terminal exit results.','resolution':'Stopped writes/compiles; resumed metadata-only finalization after parent reported successful elevated Git/CP reads (23ebec).'},
    ],
    'global_failure_counter':'Not read-modify-written by this author. Parent owns cumulative origin accounting; preserve all prior records.',
    'pending_processes':False,'no_native_or_provider_execution':True,
}
put('diagnostics.json',diagnostics)

summary={
    'status':'SOURCE_FROZEN_DEVELOPMENT_CHECKS_PASSED_FORMAL_DRIVER_MISSING',
    'generated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'worktree':str(ROOT),'base_head':'3cd8e4ceba16ba6c4890fe2fd5a35324682b44f5','committed':False,
    'source_frozen':True,'source_sha256':actual,
    'deliverables':[
        {'path':'tests/runtime/check/legacy.go','purpose':'Strict exact selector routes, locked absolute Python SHA verification, nonzero invalid/toolchain reports.'},
        {'path':'tests/runtime/check/w0501.go','purpose':'Replace only the old Codex LIVE-gate probe with locked non-executing v2.4 preflight; remove now-unused import. Preserve served suite.'},
        {'path':'tests/runtime/check/w0502.go','purpose':'Use the corrected shared route truth table; preserve served suite.'},
        {'path':'tests/runtime/check/routing_test.go','purpose':'Pure independently specified selector and locked-interpreter tests; no main/boot/provider/old cleanup.'},
        {'path':'ops/ci/runtime_v24.py','purpose':'Validate four frozen spec hashes and exact binding/mode; explicit non-executing LIVE implementation gap report.'},
        {'path':'tests/runtime/runtime_v24_test.py','purpose':'Eight negative/roster/mode/resource/CLI report tests without native/provider execution.'},
    ],
    'checks':results,
    'first_failure_preserved':'checks-01/go-unit; failure origin w05-routing-author-go-unused-import-20261104 attempt 1, corrected on attempt 2.',
    'interpretation':'Python 8 tests and Go pure selector/tool-lock tests pass. A04 LIVE exit 1 and fixture exit 2 are expected non-success preflight results, never product acceptance.',
    'formal_driver_status':'IMPLEMENTATION_GAP: no current Mu v2.4 formal LIVE driver. No native/provider operation or formal assertion executed.',
    'formal_passed_assertion_ids':[],
    'a04_roster':['A04-01','A04-02','A04-03','A04-04','A04-05','A04-06'],
    'measurement_mode':'NOT_RUN','independent_acceptance':'NOT_REQUESTED',
    'not_run':['Old W05-01/02 suites with existing scratch RemoveAll','Legacy Codex LIVE harness','Model/provider/native/installer/product processes','Formal A04 acceptance'],
    'registry_proposal':str(OUT/'registry-proposal.json'),'registry_changed':False,'main_changed':False,
    'diagnostics':str(OUT/'diagnostics.json'),'test_input_manifest':str(OUT/'checks-02/inputs.json'),
    'limitations':['Root must independently review and serially integrate the six frozen source files and registry proposal.','The formal driver is still absent; this change repairs callable routing and truthful gaps only.','Machine-specific specification root must be rebound explicitly on another host with the same frozen hashes.'],
    'process_state':'All author test controller sessions reached terminal results; no pending author process.',
}
put('author-summary.json',summary)
evidence={str(path.relative_to(OUT)).replace('\\','/'):sha(path) for folder in ['checks-01','checks-02'] for path in sorted((OUT/folder).rglob('*')) if path.is_file()}
for name in ['author-summary.json','registry-proposal.json','diagnostics.json']:evidence[name]=sha(OUT/name)
put('diagnostics-manifest.json',{'source_sha256':actual,'evidence_sha256':evidence,'checks01_preserved':True,'checks02_complete':True,'source_unchanged_since_checks02_inputs':True})
copy=OUT/'w05-routing-finalize.py'
if copy.exists():raise RuntimeError('finalize script copy already exists')
shutil.copyfile(Path(__file__),copy)
print(json.dumps({'status':summary['status'],'files':{name:sha(OUT/name) for name in ['author-summary.json','registry-proposal.json','diagnostics.json','diagnostics-manifest.json']},'source_sha256':actual,'observed_registry_revision':registry.get('revision')},ensure_ascii=False))
