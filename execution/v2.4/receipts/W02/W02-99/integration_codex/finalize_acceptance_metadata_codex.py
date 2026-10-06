"""Finalize completed W02 registration while preserving the U09 direction stop."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
V24 = ROOT / 'execution/v2.4'

def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')

state, cp = read(V24 / 'step_state.json'), read(V24 / 'checkpoint.json')
review = HERE.parent / 'independent_review_codex.json'
assert sha(review) == '5f5373c5ffb4d8db925b38f06b5387733485a1d509e9051e62acc06bdb7b7c4f'
row = next(r for r in state['steps'] if r['id'] == 'W02-99')
assert row['status'] == 'ACCEPTED' and row['verifier_id'] == 'codex:/root/w1702_review'
assert cp['revision'] == 204 and len(cp['failure_counters']) == 63
assert sum(r['status'] == 'ACCEPTED' for r in state['steps']) == 37
assert cp['value_checkpoint']['source_hashes']['step_state'] == sha(V24 / 'step_state.json')
assert cp['value_checkpoint']['formal_gate']['accepted_parent_step_ids'] == ['W00-99', 'W01-99', 'W02-99']
packet = read(HERE / 'checkpoint204_next_packet.json')
assert packet['state_source'] == 'VALIDATED_FILE'
assert packet['status'] == 'NO_READY_USER_FLOW' and packet['step'] is None
assert packet['value_checkpoint_policy']['priority_consumed'] is True
assert packet['value_checkpoint_policy']['default_step_id'] == 'W03-99'
assert packet['value_checkpoint_policy']['selected_step_id'] is None
assert cp['value_checkpoint']['pause_nonblocking_expansion'] is True
save(HERE / 'acceptance_postcondition_erratum_codex.json', {
    'original_script': 'accept_parent_codex.py', 'original_failure_line': 119,
    'cause': 'Root incorrectly required zero exit and W03 next selection after successful acceptance; actual next selector correctly returned code3 NO_READY_USER_FLOW under the current U09 implementation.',
    'state_registration_completed': True, 'checkpoint204_completed': True,
    'review_sha256': sha(review), 'original_next_packet_sha256': sha(HERE / 'checkpoint204_next_packet.json'),
    'resolution': 'Read-only finalizer confirms all acceptance/state/checkpoint postconditions and preserves the direction stop. U09 candidate reachability is independently under review; no selector bypass/counter reset/user-flow claim.',
    'product_or_verification_replay': False, 'new_permission_or_resource_actions': False,
})
save(HERE / 'acceptance_record_codex.json', {
    'status': 'INDEPENDENT_ACCEPTANCE_RECORDED_WITH_DIRECTION_REPLAN_PENDING',
    'step_id': 'W02-99', 'review_sha256': sha(review), 'checkpoint_revision': 204,
    'materialized_accepted': 37, 'parent_accepted': 3, 'parent_required': 22,
    'formal_accepted': 0, 'formal_required': 42, 'failure_origins_total': 63,
    'state_sha256': sha(V24 / 'step_state.json'), 'next_selected_step': None,
    'frozen_default_ready_step': 'W03-99', 'next_policy': 'NO_READY_USER_FLOW',
    'next_action': 'Resolve the shortest user-flow prerequisite selection under unchanged U09 thresholds.',
})
print(json.dumps({'status': 'PASS_ACCEPTANCE_METADATA_ONLY', 'checkpoint': 204,
                  'parent_accepted': 3, 'formal_accepted': 0, 'next_selected_step': None}))
