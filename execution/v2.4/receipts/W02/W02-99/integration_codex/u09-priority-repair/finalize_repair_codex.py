"""Register independently verified U09 tooling repair; do not accept a product card."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[6]
V24 = ROOT / 'execution/v2.4'
SPEC = ROOT / '.local/worktrees/v24-continuation/spec/v2.4'

def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def ref(path): return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}
def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')
def rewrite(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

review_path = HERE / 'independent_review_codex.json'
assert sha(review_path) == 'b08c4366ebea75b7f7a8cd0ad0329f1a0a52d6f32a714f805c23423fd3c7361d'
review = read(review_path)
assert review['verdict'] == 'PASS_IN_SCOPE' and not review['open_findings']
assert review['reviewer'] == 'codex:/root/w1702_review'
assert review['independent_of_executor'] is True
assert review['assertion_count'] == review['passed_assertions'] == 30
assert review['formal_case_count_delta'] == 0 and not review['parent_cards_accepted']
assert sha(ROOT / review['source_path']) == review['source_sha256']
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip() == review['source_revision']
manifest_path = Path(review['evidence_manifest']['path'])
assert sha(manifest_path) == review['evidence_manifest']['sha256']
for item in read(manifest_path)['artifacts']:
    path = Path(item['path']).resolve()
    assert path.is_relative_to(ROOT) and sha(path) == item['sha256'], str(path)
assertions = read(Path(review['assertion_results']['path']))
assert len(assertions) == 30 and len({row['id'] for row in assertions}) == 30
assert all(item['ok'] is True for item in assertions)
vector = read(Path(review['current_input_vector']['path']))
for path, digest in vector.items(): assert sha(Path(path)) == digest, path
cp_path, state_path = V24 / 'checkpoint.json', V24 / 'step_state.json'
state_raw = state_path.read_bytes()
cp = read(cp_path)
assert cp['revision'] == 205 and len(cp['failure_counters']) == 64
old_failures = copy.deepcopy(cp['failure_counters'])
old_value = copy.deepcopy(cp['value_checkpoint'])
failure = HERE / 'independent-review-codex/round1_failure.json'
assert read(failure)['actual_next_packet_calls_before_failure'] == 0
now = dt.datetime.now(dt.timezone.utc).isoformat()
record_path = HERE / 'integration_record_codex.json'
save(record_path, {'status': 'INDEPENDENTLY_VERIFIED_CONSTRUCTION_TOOL_REPAIR',
    'origin_problem_id': review['origin_problem_id'], 'integrator': 'codex:/root',
    'review': ref(review_path), 'manifest': ref(manifest_path),
    'source_revision': review['source_revision'], 'source_sha256': review['source_sha256'],
    'state_sha256_before': sha(state_path), 'checkpoint_before': 205,
    'parent_cards_accepted': [], 'formal_case_count_delta': 0,
    'authority': 'CONSTRUCTION_PRIORITY_ONLY_NOT_PRODUCT_ACCEPTANCE',
    'historical_failed_review_fixture': ref(failure)})
cp['failure_counters'].append({'origin_key': 'U09-independent-sparse-state-fixture',
    'attempts': 1, 'status': 'RESOLVED_CHANGED_IN_MEMORY_FIXTURE_INDEPENDENTLY_PASSED',
    'evidence': ref(failure), 'resolution_evidence': ref(review_path),
    'detail': 'Independent round1 omitted sparse W03 state row. Only synthetic in-memory fixture changed; no product call or source mutation before failure. Original failed script/evidence retained.'})
cp.update(updated_at=now, updated_by='codex:/root', current_step_id=None,
    next_step_id='W03-99', head=review['source_revision'],
    next_command='Use bootstrap/v24_checkpoint.py --next-packet with frozen plan/delivery and current state; selected required U02 prerequisite W03-99 is eligible.',
    work_in_progress={'origin_problem_id': review['origin_problem_id'],
        'status': 'INDEPENDENTLY_VERIFIED_TOOLING_REPAIR',
        'next_action': 'Register and execute the eligible W03-99 in a clean reused worktree; no product acceptance inferred.'},
    note='U09 prerequisite selector independently verified30/30. Parent3/22 formal0/42 unchanged,37 accepted rows unchanged.65 original failure origins preserved. Priority/history/pause retained; no frozen card dispatched yet.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'U09_REQUIRED_PREREQUISITE_SELECTOR_INDEPENDENTLY_VERIFIED',
    'evidence': ref(record_path), 'detail': 'Exact legal user-flow prerequisite frontier; preserve formal gates and failure history.'})
cp['evidence_index'].extend([record_path.relative_to(ROOT).as_posix(), review_path.relative_to(ROOT).as_posix()])
rewrite(cp_path, cp)
event = HERE / 'independent_pass_value_round_codex.json'
save(event, {'schema': 'researchos.value-round.v1',
    'round_id': 'U09-required-parent-frontier-independent-pass-20261006',
    'delta': 'INFRASTRUCTURE', 'summary': 'Independently verify required-parent frontier selection without claiming a user capability or accepting a card.',
    'evidence_refs': [ref(record_path), ref(review_path), ref(failure)]})
common = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(state_path),
    '--plan', str(SPEC / 'contracts/execution.plan.json'),
    '--delivery', str(SPEC / 'contracts/delivery.contract.json')]
argv = common + ['--expected-revision', '205', '--round-event', str(event), '--actor', 'codex:/root']
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(HERE / 'checkpoint206.stdout.txt').write_bytes(result.stdout)
(HERE / 'checkpoint206.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0
after = read(cp_path)
assert after['revision'] == 206 and after['failure_counters'][:64] == old_failures
assert len(after['failure_counters']) == 65 and state_path.read_bytes() == state_raw
value = after['value_checkpoint']
assert value['history'][:len(old_value['history'])] == old_value['history']
assert value['capabilities_observed'] == old_value['capabilities_observed']
assert value['pause_nonblocking_expansion'] is True
assert value['recommended_flow']['capability_id'] == 'U02'
assert value['recommended_flow']['scope'] == 'PREREQUISITE_FOR_USER_FLOW'
assert value['formal_gate']['accepted_parent_step_ids'] == ['W00-99', 'W01-99', 'W02-99']
result = subprocess.run(common + ['--next-packet'], cwd=ROOT, capture_output=True)
(HERE / 'checkpoint206_next_packet.json').write_bytes(result.stdout)
(HERE / 'checkpoint206_next_packet.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0
packet = json.loads(result.stdout)
assert packet['state_source'] == 'VALIDATED_FILE' and packet['eligible'] is True
assert packet['step']['id'] == 'W03-99'
selected = packet['value_checkpoint_policy']['selection']['candidates'][0]
assert selected['capability_id'] == 'U02' and selected['remaining_required_cards'] == 3
assert selected['scope'] == 'PREREQUISITE_FOR_USER_FLOW'
save(HERE / 'completion_record_codex.json', {'status': 'PASS_REPAIR_REGISTERED_WITH_ELIGIBLE_NEXT',
    'checkpoint_revision': 206, 'checkpoint_sha256': sha(cp_path),
    'state_sha256_unchanged': sha(state_path), 'failure_origins': 65,
    'selected_step': 'W03-99', 'next_packet': ref(HERE / 'checkpoint206_next_packet.json'),
    'parent_accepted': 3, 'formal_accepted': 0, 'card_dispatches': 0})
print(json.dumps({'status':'PASS_REPAIR_REGISTERED','checkpoint':206,
    'failure_origins':65,'selected_step':'W03-99','scope':selected['scope']}))
