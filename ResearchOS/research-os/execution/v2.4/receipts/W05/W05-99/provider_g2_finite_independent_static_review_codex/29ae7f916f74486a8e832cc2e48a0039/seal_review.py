from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = Path(__file__).resolve().parent
WT = ROOT / '.local/worktrees/codex-w0599-provider-g2-finite-r307'
SOURCE_NS = WT / 'execution/v2.4/receipts/W05/W05-99/provider_g2_finite_executor_codex/3fc125bf95424cb298a87a9527515d09'
FINAL = SOURCE_NS / 'final-audit-97b53059b7284a5294781a90f7ab64a1'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def ref(path):
    raw = path.read_bytes()
    return {'path': path.as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

def save(name, value):
    with (OUT / name).open('x', encoding='utf-8', newline='\n') as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write('\n')

at = datetime.now(timezone.utc).isoformat()
handoff = read(FINAL / 'handoff.json')
scope = read(SOURCE_NS / 'scope.original.json')
audit = read(OUT / 'current-hash-audit.json')
raw_cases = read(OUT / 'actual-case-raw-audit.json')
protected = read(OUT / 'protected-functions.independent.json')
if audit['manifest_bad'] or audit['inputs_bad'] or audit['archives_bad']:
    raise RuntimeError('actual input mismatch; cannot seal positive static scope finding')
if not all(x['equal'] for x in audit['generated'] + audit['extras']):
    raise RuntimeError('compiler artifact mismatch')
if not raw_cases['ordered_selectors_match'] or not raw_cases['all_outcomes_match']:
    raise RuntimeError('actual roster mismatch')
if not all(x['byte_equal'] for x in protected['rows']):
    raise RuntimeError('protected function mismatch')

inputs = [FINAL / 'handoff.json', FINAL / 'manifest.json', SOURCE_NS / 'scope.original.json']
for value in handoff.values():
    if isinstance(value, dict) and isinstance(value.get('path'), str):
        p = Path(value['path'])
        inputs.append(p if p.is_absolute() else WT / p)
inputs.extend(SOURCE_NS / n for n in ['build_g2.py', 'run_finite.py', 'seal_audit.py'])
snapdir = OUT / 'source_receipt_snapshots'
snapdir.mkdir()
snapshots = []
for p in dict.fromkeys(inputs):
    r = ref(p)
    # Large vectors/raw/binary remain in their immutable referenced public namespace.
    if r['bytes'] <= 260000 and p.suffix in {'.json', '.py'}:
        dst = snapdir / (hashlib.sha256(p.as_posix().encode()).hexdigest()[:12] + '-' + p.name)
        dst.write_bytes(p.read_bytes())
        r['copy'] = ref(dst)
    snapshots.append(r)
save('input_refs.json', snapshots)

source_rows = []
for name in ['runtime_provider_binding_windows_test.go', 'runtime_coordinator_windows_test.go']:
    old = ref(OUT / ('candidate-' + name))
    current = ref(WT / 'internal/domain' / name)
    source_rows.append({'path': 'internal/domain/' + name, 'git_blob_snapshot': old,
                        'current_after_read': current, 'same_bytes': old['sha256'] == current['sha256']})
if not all(x['same_bytes'] for x in source_rows):
    raise RuntimeError('test source changed after Git snapshot')
save('source_before_after.json', {'candidate': handoff['source_commit'], 'base': handoff['base_commit'], 'rows': source_rows,
     'full_original_build_before_after_and_current': ref(OUT / 'current-hash-audit.json'),
     'timing_limit': 'Current hash observation is a sequential read, not a filesystem atomic snapshot. Original author before/after vectors are separately retained; no canonical stability claim.'})

findings = [
 {'id':'S01','kind':'SCOPE_CONFORMING_STATIC','detail':'Git source commit has only the two authorized test paths and exact parent 6fb5263. Thirty-five protected complete function bodies are byte-identical. Original wrappers retain signatures and nil callback behavior; protected held history/archived/qualification bodies remain unchanged.', 'evidence':ref(OUT/'protected-functions.independent.json')},
 {'id':'S02','kind':'CAUSE_ASSERTIONS_PRESENT','detail':'Actual same Goal ACTIVATE precedes the optional cap update and fresh GET; callback asserts no Task/Run then restores original token. Preflight retains HTTP/effect guards and now exact Fault Status/Code/Message. Native collection binds original Run epoch/dispatch, manifest, bridge MODEL frame and PREPARED transport before matching the UNKNOWN chain. Synthetic matcher records only test the predicate, not runtime success.', 'locators':['internal/domain/runtime_coordinator_windows_test.go:122','internal/domain/runtime_provider_binding_windows_test.go:567','internal/domain/runtime_provider_binding_windows_test.go:677','internal/domain/runtime_provider_binding_windows_test.go:1001']},
 {'id':'S03','kind':'REAL_COMPONENT_WITH_LIMIT','detail':'Two rollback leaves call original dispatchGate/taskContextForRun, providerRoute/runtime request gate/providerTransport and prepareEffectTx inside a real caller transaction, observe PREPARED plus RESERVE or exact budget refusal, then explicitly rollback. Captured schema/columns and JSON-encoded all-table row multisets match. This projection is not an independent proof of SQLite typeof/implicit rowid/physical byte equality; no claim is made that it is.', 'locators':['internal/domain/runtime_provider_binding_windows_test.go:817','internal/domain/runtime_provider_binding_windows_test.go:871']},
 {'id':'S04','kind':'QUARANTINE_LAYERS_AND_COST_BOUNDARY','detail':'Four original payloads retain their bytes and eight evaluator controls follow complete SSE -> Feed -> Finish -> policy. Four native cases retain exact PREPARED/STARTED/UNKNOWN MODEL key/hash/reservation and RESERVE ledger, null actual_cost, no invented COMMIT/RECONCILE/RELEASE or successful MODEL ACK. These are nonstream qualification_bootstrap fixtures with QueueRequired=false, not ordinary session streaming or same-Run tool positives.', 'locators':['internal/domain/runtime_provider_binding_windows_test.go:612','internal/domain/runtime_provider_binding_windows_test.go:952','internal/domain/runtime_provider_binding_windows_test.go:1001']},
 {'id':'E01','kind':'ORIGINAL_EXECUTION_EVIDENCE_CHECKED_NOT_REPLAYED','detail':'Read all 29 original invocation/stdout results: ordered 18 component and 11 native leaves, same newly built f888 executable, native exit 0 and exact leaf PASS, zero skips/failures/timeouts. Original MODEL loopback total 4, preflight MODEL 0. API setup/readiness counted separately; protected contextFixture bootstrap remains NOT_INSTRUMENTED, not zero.', 'evidence':ref(OUT/'actual-case-raw-audit.json')},
 {'id':'E02','kind':'SNAPSHOT_LIMIT','detail':'Thirteen preserved database files are VACUUM INTO snapshots created while their original fixtures existed. The protected snapshot function is byte-identical. Original t.TempDir database files are not separately retained by this cohort; do not claim raw original DB bytes or byte equality with snapshots. This review hashes snapshot files and reads the existing schema/row reports; it never opens SQLite and does not independently certify those SQL checks.'},
 {'id':'R01','kind':'REPLAY_RUNNER_PREPARATION_REQUIRED','detail':'Do not execute the old author runner unchanged for independent replay: it allows start_index omission of earlier rows, uses Python assert guards, and on timeout uses PID taskkill without an owned Job/creation binding. All sealed original cases completed without timeout; this static future-runner issue does not rewrite their native exits. Independent runner must start at row 0, reject optimized guard disabling, use explicit checks and owned Job lifecycle, retain exact failed outputs and stop without retry.'}
]

review = {'schema':'researchos.provider-g2-independent-static-review.v1','at':at,
 'reviewer':'codex:/root/command_queue_impl','candidate_author':'codex:/root/sources_parent_impl',
 'identity_boundary':'Reviewer did not author these exact2 G2 test changes, but authored earlier provider production and some finite design. This review does not independently accept provider production or qualify it.',
 'decision':'STATIC_EXACT2_WITHIN_REGISTERED_SCOPE_PENDING_INDEPENDENT_FINITE29',
 'source_ready':False,'formal_acceptance_delta':0,'Main_provider_acceptance':False,
 'candidate_source_commit':handoff['source_commit'],'base_commit':handoff['base_commit'],
 'receipt_commit':'9a34aacbaeb775566e524f5af3518ea86a5d41b9',
 'scope':ref(SOURCE_NS/'scope.original.json'),'author_handoff':ref(FINAL/'handoff.json'),
 'hash_verification':{'manifest':755,'compiled_inputs':37513,'archives':349,'generated_original_and_copy':8,'exe_match':True,'mismatches':0,'audit':ref(OUT/'current-hash-audit.json')},
 'findings':findings,'concrete_test_source_blockers_identified':[],
 'replay_required_before_any_independent_execution_verdict':True,
 'this_review_executions':{'Go':0,'Node':0,'SQL':0,'SDK':0,'HTTP':0,'MODEL':0,'paid':0,'product_tests':0},
 'new_failure_origins':[ref(OUT/'failure_origin.json')],
 'failure_count_note':'One read-only locator failure 47bf7d from Root-supplied wrong receipt root. Original source tool origins 339800/798239/62f172 and all earlier history/P12/G1 failures remain unchanged. No test failures newly observed by execution.'}
save('review.json', review)

future = {'schema':'researchos.provider-g2-finite-independent-replay-proposal.v1','status':'NOT_RUN_REQUIRES_ROOT_REGISTERED_SCOPE_AND_RUNNER_REVIEW','at':at,
 'executor':'Future Root-registered nonauthor executor; no implicit execution grant here',
 'source_readonly_commit':handoff['source_commit'],'author_WT_writes':False,
 'new_paths_proposed':['.local/independent-provider-g2-<registered-UUID>/source',' .local/independent-provider-g2-<registered-UUID>/cache'.strip(),'.local/independent-provider-g2-<registered-UUID>/gotmp','execution/v2.4/receipts/W05/W05-99/provider_g2_independent_replay_codex/<registered-UUID>/'],
 'receipt_tool_paths_proposed':['prepare_replay.py','run_replay.py','execution_spec.json','input_closure.json'],
 'source_edits':[],'overlay_edits':[],
 'preparation_owner_duties':[
  'Export exact public Git commit into a new absent directory, verify every source path against that commit and preserve original author WT. No branch-head substitution, checkout/reset/cherry-pick or edits to Main.',
  'Prepare new immutable spec and runner bound to source commit, all 29 selectors, role, parent authority, resource hashes and unique output directory; independent runner source review before any run. Existing author build_g2/run_finite are references only.',
  'Fresh GOCACHE/GOTMPDIR/TEMP and own receipt output; shared GOPATH is readonly. GOTOOLCHAIN=local GOENV=off GOPROXY=off GOSUMDB=off and actual GOROOT. No dependency installation, new vendor, SDK rebuild or schema edits. gofmt must be read-only -l, never -w.',
  'Use locked Go list -deps -test -json then test -c -work -x. Preserve raw WORK assignment and actual compile/link invocations, all dependency source/tests/embeds, schema numbered+additive SQL, Go module/stdlib/compiler files, actual linked archives, generated _testmain/importcfg/importcfg.link, buildinfo and fresh binary. All real included inputs are enumerated; historical counts are comparisons, not hardcoded completeness.',
  'Freeze actual readonly SDK/dist/package exports, Node, builder/worker/bundle provenance, Python/helper/DLL/input resources and every external runner input before build and before first case. Rehash after components, native batch, final/failure. No Main canonical JSONs or other agents mutable caches in protected input closure.',
  'Use owned-process helper only after explicit hash binding/review; assign Job before resume, retain PID plus creation_time and actual exit/timeout/cleanup. No naked taskkill, no PID reuse assumptions. Helper errors stop the dependent lane; unknown exit stays null.',
  'Reject existing execution phase markers and optimized Python guard disabling. Exactly 29 sequential invocations from index0, no start_index/resume/autoretry; preserve first failure and remaining NOT_RUN.'
 ],
 'locked_resources':{'tools':scope['mandatory_runner_proposal']['locked_tools'], 'bundle':scope['readonly_bundle_original_ref'],
  'bundle_source_root':ROOT.as_posix(),'bundle_alternative_forbidden':'Main 2a8e bundle and old G1 test executable cannot replace provider 497e bundle/new G2 binary',
  'job_helper':{'path':(ROOT/'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py').as_posix(),'sha256':'6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad','must_revalidate_actual_resources':True}},
 'compiler_argv':scope['mandatory_runner_proposal']['compiler_plan'],
 'ordered_cases':[{'index':i,'lane':'component' if i<18 else 'native','selector':v,'status':'NOT_RUN'} for i,v in enumerate(scope['ordered_cases'])],
 'argv_template':['<new-exe>','-test.v','-test.count=1','-test.timeout=150s','-test.failfast','-test.run=<one exact selector>'],
 'test_timeout_seconds':150,'outer_seconds':180,'bounded_owned_job_cleanup_seconds':5,
 'network':{'MODEL_loopback_max':4,'preflight_MODEL_max':0,'component_MODEL_max':0,'external':0,'paid':0,'real_credentials':0,'setup_readiness':'Separately counted from MODEL. Preserve protected bootstrap NOT_INSTRUMENTED instead of claiming total HTTP4 or bootstrap0.'},
 'per_case_requirements':[
  'Original argv/cwd/explicit environment/start/end/actual exit/timeout/Job lifecycle/raw stdout/stderr and exact PASS leaf. Child parent PASS is separate, no skip or implicit case omission.',
  'Exact typed Fault, expected real stage trace, original epoch/dispatch/manifest/MODEL frame/transport and complete UNKNOWN reservation ledger for native cases; exact cause mismatch must stop even if native process exits0.',
  'Cap mutation after real Goal ACTIVATE and before Task/context/Run; retain before-task evidence. Actual legal PREPARED+RESERVE or budget Fault only inside rollback Tx, projected rows unchanged after rollback.',
  'Retain all 13 new fixture snapshots under disclosed VACUUM method and hash after all children join. Read-only validation may audit new public snapshots with schema/all-table row multisets; distinguish that from original t.TempDir bytes and from SQL storage-class/rowid evidence.',
  'A stronger original DB-file retention or typed-row pre/post guarantee needs a separately specified test/overlay delta; current no-edit replay cannot retroactively provide it. Do not rewrite old originals or label regenerated snapshots as originals.'
 ],
 'no_repeat':['held two historical positives','old broad64+12','Go3/JS3','qualification success','sameRun TOOL success','provider whole9 acceptance'],
 'stop_on':['nonzero or timeout or cleanup failure','unexpected typed cause/stage/frame/key/count','source/resource/input drift','missing evidence or wrong expected leaf','MODEL request budget exceeded'],
 'on_stop':'Save actual raw/origin/current input vector and available own public closed facts, mark remaining rows NOT_RUN, no automatic repair or retry. New UUID preserves the existing failure chain.',
 'completion':'Only a separately authorized finite run plus nonauthor adjudication can issue replay evidence. This proposal and author native29 cannot establish provider whole-source acceptance/Main integration/G3-G6/LIVE/parent formal gates.'}
save('future_replay_scope.json', future)
save('tool_observations.json', {'kind':'Tool-return observation index, not reconstructed raw shell streams',
 'successful_tool_refs':['337a1a','48b0ea','4a1f10','235f70','a5ec2e','910e85','7ca804','e3f65e','4f5c62','113887','6821c1','2fb8f0','ea446c','13c026','e1ef09'],
 'hash_process':{'start_tool_ref':'9504ab','session_id':16263,'completion_tool_ref':'69f2d3','actual_exit':0,'summary':{'manifest':755,'input':37513,'archives':349,'mismatches':0}},
 'failure':ref(OUT/'failure_origin.json'),'new_nonzero_count':1,'original_raw_when_unavailable':None})
save('handoff.json', {'schema':'researchos.provider-g2-static-review-handoff.v1','at':at,
 'review':ref(OUT/'review.json'),'future_scope':ref(OUT/'future_replay_scope.json'),
 'input_refs':ref(OUT/'input_refs.json'),'current_hash_audit':ref(OUT/'current-hash-audit.json'),
 'source_guard':ref(OUT/'source_before_after.json'),'failure_refs':[ref(OUT/'failure_origin.json')],
 'source_ready':False,'actual_replay_executed':False,'formal_increment':0,
 'manifest_note':'manifest.json follows and lists this handoff without self-reference; deliver its hash separately.'})
files = sorted((p for p in OUT.rglob('*') if p.is_file()), key=lambda p:p.as_posix())
save('manifest.json', {'schema':'researchos.immutable-receipt-manifest.v1','entries':[ref(p) for p in files], 'listed_files':len(files), 'self_excluded':True})
print(json.dumps({n:ref(OUT/n) for n in ['review.json','future_replay_scope.json','handoff.json','manifest.json']},ensure_ascii=True))
