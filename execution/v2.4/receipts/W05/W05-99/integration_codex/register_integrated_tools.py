from pathlib import Path
import copy, datetime, hashlib, importlib.util, json, subprocess, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
BASE = HERE.parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def ref(p): return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}
def create(p, value):
    with p.open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')

review_path = BASE/'architecture_review_codex/tool_projection_source_review.json'
assert sha(review_path) == 'cdd0524a14c554641bd0f35bb033b22eac3c5d59fec2ce78b15cea5e928de95c'
review = read(review_path)
assert review['decision'] == 'APPROVE_FROZEN_SOURCE_SLICE_FOR_ROOT_INTEGRATION'
assert review['actor'] != review['executor'] and not review['blocking_findings']
for source in review['scope']: assert sha(ROOT/source['path']) == source['sha256']
receipt_path = BASE/'tool_executor_codex/execution_receipt.json'
assert sha(receipt_path) == review['execution_receipt']['sha256']
cp_path, state_path = ROOT/'execution/v2.4/checkpoint.json', ROOT/'execution/v2.4/step_state.json'
cp = read(cp_path)
old = copy.deepcopy(cp)
state_bytes = state_path.read_bytes()
assert cp['revision'] == 224 and len(cp['failure_counters']) == 96
before = HERE/'checkpoint224_before_tools_integration.json'
with before.open('xb') as f: f.write(cp_path.read_bytes())

module_path = ROOT/'execution/v2.4/formal_case_index.py'
spec = importlib.util.spec_from_file_location('current_formal_drift', module_path)
formal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(formal)
frozen = ROOT/'.local/worktrees/v24-continuation/spec/v2.4'
derived = formal.derive_formal_cases(ROOT, state_path, frozen/'contracts/execution.plan.json')
assert derived['formal_cases_accepted'] == 0
w04 = next(x for x in derived['owners'] if x['task_id'] == 'W04')
assert w04['integrity'] == 'NEEDS_REVALIDATION'
drift_path = HERE/'tools_integrated_current_formal_drift.json'
create(drift_path, derived)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
integrated = HERE/'tool_slice_integrated_codex.json'
create(integrated, {
    'schema': 'researchos.w05.root-reviewed-tool-slice-integration.v1',
    'status': 'INTEGRATED_INDEPENDENTLY_REVIEWED_SOURCE_SLICE_NOT_PARENT_ACCEPTANCE',
    'integrated_at': now, 'integrator': 'codex:/root',
    'independent_reviewer': review['actor'], 'independent_review': ref(review_path),
    'candidate_head': review['candidate_head'], 'candidate_source_commit': review['source_commit'],
    'main_head_after_cherry_pick': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'main_source_commit': subprocess.check_output(['git','rev-parse','HEAD~1'],cwd=ROOT,text=True).strip(),
    'execution_receipt': ref(receipt_path), 'source_hashes_verified_after_integration': review['scope'],
    'retained_actual_test_evidence': review['evidence_integrity'],
    'source_validation_scope': 'Exact independently reviewed candidate bytes integrated; fixture and real Mu loopback results retained at their own tested snapshots. No new main run is claimed.',
    'formal_currentness': ref(drift_path),
    'historical_w04_registration_preserved': True,
    'w04_current_owned_cases': 0, 'w04_revalidation_required': True,
    'w05_status': 'IN_PROGRESS', 'full_live_completed': False,
    'parent_acceptance_issued': False, 'formal_acceptance_issued': False
})

origins = []
def failure(key, path, classification, detail):
    data = read(path)
    if 'exit_code' in data: assert data['exit_code'] != 0
    origins.append({'origin_key': key, 'attempts': 1, 'candidate_id': 'W05-99-S3',
        'input_hash': data.get('inputs_sha256', sha(path)),
        'status': 'RETAINED_ORIGINAL_FAILURE_RESOLVED_WITH_DISTINCT_CHANGED_INPUT',
        'classification': classification, 'evidence': ref(path),
        'product_failure_count_delta': 1 if classification == 'PRODUCT_SEALED_SESSION_SCAN_FAILURE' else 0,
        'detail': detail})
failure('W05-S3-RECOVERY_ASSERTION_COST_BASIS', BASE/'tool_executor_codex/runs/20261006T001229Z-c21cc2e504/result.json',
    'TEST_ASSERTION_FAILURE_NOT_PRODUCT', '46 passes, one amended recovery assertion expected UNKNOWN although the actual native reservation has UPPER_BOUND/RESERVE. Corrected exact ledger-basis assertion while keeping unknown/null usage money, original Run and immutable receipt constraints; final targeted test passed.')
failure('W05-S3-SEALED_CURRENT_SESSION_SCAN', BASE/'tool_executor_codex/runs/20261006T001519Z-e9c4c28139/result.json',
    'PRODUCT_SEALED_SESSION_SCAN_FAILURE', 'Real negative case returned SESSION_SEALED from Scan. Independently reviewed source adds sealed_at IS NULL in both projection lookups; original immutable billing still ingests and final selected47 tests pass.')
failure('W05-S3-PROCESS_CREATION_WRONG_CWD', BASE/'tool_executor_codex/process_creation_failure.json',
    'LOCAL_PROCESS_CREATION_FAILURE_BEFORE_EXECUTION', 'Mistyped local working directory prevented tool process creation. Original error is retained as tool error, not process stderr or a test run; corrected actual directory was used for subsequent distinct invocations.')
assert not {x['origin_key'] for x in origins} & {x.get('origin_key') for x in cp['failure_counters']}
cp['failure_counters'].extend(origins)
cp.update(updated_at=now, updated_by='codex:/root',
    note='S1 CLI and S3 durable canonical tool/usage source independently reviewed and integrated. Actual domain change derives W04 NEEDS_REVALIDATION/current0, preserving historical accepted registration and all original failures. S2 Goal source awaits independent review; no W05/LIVE/formal acceptance.')
cp['work_in_progress'].update(status='CLI_S1_AND_TOOLS_S3_INTEGRATED_GOAL_S2_REVIEW_PENDING',
    next_action='Independently review frozen Goal S2; register approved S4 CLI goal follower scope and implement. Resolve remaining queue/nested cancellation and actual installed LIVE flows. Revalidate W04 with explicit immutable history protocol after this source wave; retain current0 until independently registered current proof.')
cp['evidence_index'].extend([integrated.relative_to(ROOT).as_posix(), drift_path.relative_to(ROOT).as_posix()])
cp['integrity_events'].append({'at': now,'actor':'codex:/root','event':'W05_S3_REVIEWED_SOURCE_INTEGRATED_W04_CURRENT_VECTOR_DRIFT','evidence':ref(integrated)})
cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
event_path = HERE/'checkpoint225_value_round_codex.json'
create(event_path, {'schema':'researchos.value-round.v1','round_id':'W05-S3-reviewed-integration-20261006',
    'delta':'FIXTURE','summary':'Actual canonical tool and usage journal projection integrated after independent source review; current W04 evidence invalidated by exact source drift. No installed LIVE/formal acceptance.',
    'evidence_refs':[ref(integrated),ref(drift_path)]})
args = [sys.executable,'-B','-X','utf8',str(ROOT/'bootstrap/v24_checkpoint.py'),
    '--checkpoint',str(cp_path),'--state',str(state_path),'--plan',str(frozen/'contracts/execution.plan.json'),
    '--delivery',str(frozen/'contracts/delivery.contract.json'),'--expected-revision','224',
    '--round-event',str(event_path),'--actor','codex:/root']
proc = subprocess.run(args,cwd=ROOT,capture_output=True)
for name,raw in [('stdout.json',proc.stdout),('stderr.txt',proc.stderr)]:
    with (HERE/f'checkpoint225.{name}').open('xb') as f:f.write(raw)
assert proc.returncode == 0, proc.stderr.decode('utf8','replace')
after = read(cp_path)
assert after['revision'] == 225 and len(after['failure_counters']) == 99
assert after['failure_counters'][:96] == old['failure_counters'] and state_path.read_bytes() == state_bytes
assert after['value_checkpoint']['formal_gate']['formal_cases_accepted'] == 0
print(json.dumps({'status':'PASS_REVIEWED_TOOLS_INTEGRATED_CURRENT_FORMAL_DRIFT_RECORDED', 'checkpoint':225, 'failure_origins':99, 'formal_current_count':0, 'historical_accepted_parent_rows':5}, ensure_ascii=True))
