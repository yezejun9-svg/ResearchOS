"""Register independent W02 construction acceptance, without formal case acceptance."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
V24 = ROOT / 'execution/v2.4'
SPEC = ROOT / '.local/worktrees/v24-continuation/spec/v2.4'
CARD = HERE.parent

def load(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def ref(path, base=V24): return {'path': path.relative_to(base).as_posix(), 'sha256': sha(path)}

review_path = CARD / 'independent_review_codex.json'
assert sha(review_path) == '5f5373c5ffb4d8db925b38f06b5387733485a1d509e9051e62acc06bdb7b7c4f'
review = load(review_path)
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert head == review['source_revision'] == '67ee53661f267c0b7a2441cfd58117fbd0b39b30'
assert review['step_id'] == 'W02-99' and review['verdict'] == 'ACCEPT_W02_PARENT_CONSTRUCTION'
assert review['independent_of_executor'] is True and review['open_findings'] == []
assert len(review['resolved_findings']) == 2
assert set(review['card_checks']) == {'W02-99-OUTPUT', 'W02-99-NEGATIVE', 'W02-99-EVIDENCE'}
assert set(review['card_checks'].values()) == {'PASS'}
assert len(review['development_checklist_mapping']) == 9
assert all(r['decision'] == 'ACCEPT_IN_W02_CONSTRUCTION_SCOPE' for r in review['development_checklist_mapping'])
assert review['owned_acceptance_ids'] == review['formal_cases_accepted'] == [] and review['formal_case_count_delta'] == 0
assert len(review['checks']) == 53 and all(r['ok'] is True for r in review['checks'])
for item in review['evidence_artifacts']:
    path = Path(item['path']).resolve()
    assert path.is_relative_to(ROOT.resolve()) and sha(path) == item['sha256'], item['path']
gate_refs = []
assert {r['check_id'] for r in review['gate_decisions']} == {'W02-G01', 'W02-G02', 'W02-G03'}
for gate in review['gate_decisions']:
    selector = gate['check_id']
    assert gate['decision'] == 'ACCEPT' and gate['assertion_ids'] == [selector] and gate['child_exit_code'] == 0
    original = ROOT / 'execution/invocations' / gate['invocation_id'] / 'receipt.json'
    mirror = Path(gate['dispatcher_receipt'])
    assert original.read_bytes() == mirror.read_bytes() and sha(mirror) == gate['dispatcher_receipt_sha256']
    dispatcher = load(mirror)
    assert dispatcher['code_revision'] == head and dispatcher['assertion_ids'] == [selector]
    for name in ('child', 'projection'):
        path = Path(gate[name + '_receipt']).resolve()
        assert path.is_relative_to(CARD.resolve()) and sha(path) == gate[name + '_receipt_sha256']
        assert sha(path.parent / 'manifest.json') == gate[name + '_manifest_sha256']
        manifest = load(path.parent / 'manifest.json')
        for rel, expected in manifest.items():
            raw = (path.parent / rel).resolve()
            assert raw.is_relative_to(path.parent) and sha(raw) == expected
        gate_refs.extend([ref(path), ref(path.parent / 'manifest.json')])
    gate_refs.append(ref(mirror))

state_path, cp_path = V24 / 'step_state.json', V24 / 'checkpoint.json'
state, cp = load(state_path), load(cp_path)
assert cp['revision'] == 203 and len(cp['failure_counters']) == 62
assert load(V24 / 'commands.json')['revision'] == review['commands_revision'] == 36
assert load(V24 / 'path_ownership.json')['revision'] == review['path_revision'] == 45
old_failures = copy.deepcopy(cp['failure_counters'])
old_other_steps = [r for r in copy.deepcopy(state['steps']) if r['id'] != 'W02-99']
row = next(r for r in state['steps'] if r['id'] == 'W02-99')
assert row['status'] == 'IN_PROGRESS' and row['executor_id'] != review['reviewer']
assert sum(r['status'] == 'ACCEPTED' for r in state['steps']) == 36
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
row.update(status='ACCEPTED', verifier_id=review['reviewer'], accepted_at=now,
    scope_note='W02 construction parent gates only. Final-owner cases empty; A03/A15 remain with W06/W20. Current exact registered gates, nine requirements and independent raw proof accepted.',
    execution_note='Original17/13/21 internal conditions remain distinct from three parent IDs and163 independent checks. All original failures retained; import AST and output projection repaired under new source.')
row['evidence'].extend(gate_refs + [ref(review_path), ref(HERE / 'exact_parent_dispatch_results.json')])
assert old_other_steps == [r for r in state['steps'] if r['id'] != 'W02-99']
write(state_path, state)
for failure in cp['failure_counters']:
    if failure['origin_key'] in ('W02-evidence-reuse-g02-import-AST-boundary', 'W02-parent-output-exact-ID-projection'):
        assert failure['attempts'] == 1 and failure['status'] == 'OPEN_MINIMAL_REPAIR_DISPATCHED'
        failure.update(status='RESOLVED_CHANGED_SOURCE_INDEPENDENTLY_REVIEWED', resolution=ref(review_path, ROOT))
failure_path = CARD / 'independent-review-codex/finalize_round1_failure.json'
cp['failure_counters'].append({'origin_key': 'W02-independent-historical-driver-current-hash-classification',
    'attempts': 1, 'status': 'RESOLVED_REVIEW_VALIDATOR_NO_PRODUCT_CHANGE',
    'evidence': ref(failure_path, ROOT),
    'detail': 'First final review incorrectly treated explicitly historical unarchived parent_driver hash as a current claim. Original failed script and error preserved. Correct classification then passed53 final checks; no product/helper/raw changed.'})
assert cp['failure_counters'][:60] == old_failures[:60]
for old, new in zip(old_failures[60:], cp['failure_counters'][60:62]):
    assert {k: v for k, v in new.items() if k not in ('status', 'resolution')} == {k: v for k, v in old.items() if k != 'status'}
cp.update(head=head, current_step_id=None, next_step_id='W03-99', work_in_progress=None,
    updated_at=now, updated_by='codex:/root',
    parent_tasks_accepted=['W00(gates only, via W00-99 independent acceptance)',
        'W01(gates only, via W01-99 independent acceptance)', 'W02(gates only, via W02-99 independent acceptance)'],
    note='37 materialized accepted including3 parents; parent3/22, formal0/42. W02 current exact construction gates independently accepted.63 failure origins preserved, including one resolved review-harness classification; budgets and all unrelated blockers unchanged.')
cp['accepted_steps'].append('W02-99')
cp['blocked_steps'] = [sid for sid in cp['blocked_steps'] if sid != 'W02-99']
for worker in cp['workers']:
    if worker['step_id'] == 'W02-99':
        worker.update(state='ACCEPTED_PARENT_CONSTRUCTION_NOT_FORMAL_CASES', independent_review=ref(review_path))
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'card': 'W02-99',
    'event': 'INDEPENDENT_PARENT_CONSTRUCTION_ACCEPTED', 'evidence': ref(review_path),
    'detail': 'Exact three gates and nine development rows independently accepted; parent3/22 formal0/42. Original findings/failure paths retained, two statuses resolved against independent closure. No unrelated resource replay.'})
for path in (review_path, HERE / 'exact_parent_dispatch_results.json', failure_path):
    rel = path.relative_to(ROOT).as_posix()
    if rel not in cp['evidence_index']: cp['evidence_index'].append(rel)
write(cp_path, cp)
event_path = HERE / 'acceptance_value_round_codex.json'
write(event_path, {'schema': 'researchos.value-round.v1', 'round_id': 'W02-parent-independent-acceptance-20261006',
    'delta': 'INFRASTRUCTURE', 'summary': 'Independent W02 construction acceptance: actual clean builds, dispatcher errors and current exact registration; repaired source/ID boundaries. No new formal case acceptance.',
    'evidence_refs': [ref(review_path, ROOT), ref(HERE / 'exact_parent_dispatch_results.json', ROOT)]})
base = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(state_path), '--plan', str(SPEC / 'contracts/execution.plan.json'),
    '--delivery', str(SPEC / 'contracts/delivery.contract.json')]
result = subprocess.run(base + ['--expected-revision', '203', '--round-event', str(event_path), '--actor', 'codex:/root'], cwd=ROOT, capture_output=True)
(HERE / 'checkpoint204.stdout.txt').write_bytes(result.stdout)
(HERE / 'checkpoint204.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
selected = subprocess.run(base + ['--next-packet'], cwd=ROOT, capture_output=True)
(HERE / 'checkpoint204_next_packet.json').write_bytes(selected.stdout)
(HERE / 'checkpoint204_next_packet.stderr.txt').write_bytes(selected.stderr)
assert selected.returncode == 0, selected.stderr.decode('utf-8', 'replace')
packet = json.loads(selected.stdout)
assert packet['state_source'] == 'VALIDATED_FILE' and packet['step']['id'] == 'W03-99'
after = load(cp_path)
assert after['revision'] == 204 and len(after['failure_counters']) == 63
assert after['value_checkpoint']['source_hashes']['step_state'] == sha(state_path)
assert after['value_checkpoint']['formal_gate']['accepted_parent_step_ids'] == ['W00-99', 'W01-99', 'W02-99']
write(HERE / 'acceptance_record_codex.json', {'recorded_at': now, 'status': 'INDEPENDENT_ACCEPTANCE_RECORDED',
    'step_id': 'W02-99', 'review_sha256': sha(review_path), 'checkpoint_revision': 204,
    'materialized_accepted': 37, 'parent_accepted': 3, 'parent_required': 22,
    'formal_accepted': 0, 'formal_required': 42, 'failure_origins_total': 63,
    'next_step': packet['step']['id'], 'state_sha256': sha(state_path)})
print(json.dumps({'status': 'PASS', 'checkpoint': 204, 'parent_accepted': 3,
                  'formal_accepted': 0, 'failure_origins': 63, 'next_step': packet['step']['id']}))
