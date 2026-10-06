"""Root-only exact-path registration after an actual independent scope review."""
from pathlib import Path
import argparse
import copy
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
V24 = ROOT / 'execution/v2.4'
def load(p): return json.loads(p.read_bytes())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p): return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)}
def save(p, v):
    with p.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(v, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
def replace(p, v): p.write_text(json.dumps(v, ensure_ascii=False, indent=2)+'\n', encoding='utf8')

parser = argparse.ArgumentParser()
parser.add_argument('--slice', required=True, choices=['goal', 'tools'])
parser.add_argument('--expected-revision', required=True, type=int)
parser.add_argument('--expected-path-revision', required=True, type=int)
parser.add_argument('--review-sha256', required=True)
args = parser.parse_args()
kind = args.slice
proposal_path = HERE / ('goal_source_scope_proposal_round2_codex.json' if kind == 'goal' else 'tool_source_scope_proposal_codex.json')
review_path = V24 / 'receipts/W05/W05-99/architecture_review_codex' / ('goal_scope_review_round2.json' if kind == 'goal' else 'tool_scope_review.json')
expected_proposal = {'goal': '7560059d5e7185dcc794f210809c41be8c8c2b4474a5712f3d4578f343fef151',
                     'tools': '885014328ca3571798e01585367d0047792e95662f0912ffe050163e0209e669'}[kind]
assert sha(proposal_path) == expected_proposal
assert sha(review_path) == args.review_sha256
proposal, review = load(proposal_path), load(review_path)
assert review['decision'] == 'APPROVED_FOR_ROOT_PATH_REGISTRATION'
assert review['reviewer'] == 'codex:/root/w1702_review'
assert review['approved_exact_paths'] == proposal['exact_paths']
worktree = ROOT / ('.local/worktrees/codex-w0599-goal' if kind == 'goal' else '.local/worktrees/codex-w0599-tools')
owner = 'codex:/root/w1101_map' if kind == 'goal' else 'codex:/root'
assert proposal['proposed_owner'] == owner
for item in proposal['existing_source_refs']:
    assert sha(ROOT / item['path']) == sha(worktree / item['path']) == item['sha256'], item['path']
for item in proposal['new_paths']:
    assert not (ROOT / item).exists() and not (worktree / item).exists(), item
cp_path, paths_path, state_path = (V24 / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json'])
cp, paths, state_raw = load(cp_path), load(paths_path), state_path.read_bytes()
old_cp = copy.deepcopy(cp)
assert cp['revision'] == args.expected_revision and paths['revision'] == args.expected_path_revision
assert cp['current_step_id'] == 'W05-99' and len(cp['failure_counters']) == 84
now = dt.datetime.now(dt.timezone.utc).isoformat()
scope_path = HERE / (kind + '_source_scope_codex.json')
record = copy.deepcopy(proposal)
record.update(schema='researchos.w05.root-additional-source-scope.v1', status='AUTHORIZED_EXACT_SOURCE_SLICE',
              registered_at=now, registered_by='codex:/root', owner=owner,
              worktree=worktree.relative_to(ROOT).as_posix(), proposal_ref=ref(proposal_path),
              independent_scope_review_ref=ref(review_path), checkpoint_before=args.expected_revision,
              main_current_formal_count=3, candidate_execution_is_not_formal_acceptance=True)
save(scope_path, record)
binding = paths['card_path_bindings']['W05-99']
key = 'goal_handler' if kind == 'goal' else 'durable_tool_projection'
assert key not in binding['subtasks']
other = set(binding['paths'])
for task in binding['subtasks'].values(): other.update(task['paths'])
assert not set(proposal['exact_paths']) & other
receipt_path = 'execution/v2.4/receipts/W05/W05-99/' + ('goal_executor_codex/**' if kind == 'goal' else 'tool_executor_codex/**')
binding['subtasks'][key] = {'owner': owner, 'worktree': record['worktree'],
    'branch': 'work/codex-w0599-' + kind, 'paths': [*proposal['exact_paths'], receipt_path],
    'scope_ref': ref(scope_path), 'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'reason': 'Independent current source scope for real Goal authority and provenance.' if kind == 'goal' else 'Canonical effect-derived durable events with exact recovery and unknown-cost boundaries; no execution authority in projection.'}
paths.update(revision=args.expected_path_revision+1, updated_at=now, updated_by='codex:/root', amended_at=now, amended_by='codex:/root')
replace(paths_path, paths)
cp.update(updated_at=now, updated_by='codex:/root',
    note='W05 precise additional source slice registered on an independent candidate. Main current3 W04 formal cases unchanged until candidate domain changes are integrated; then exact evidence revalidation is mandatory.')
cp['work_in_progress']['status'] = 'REGISTERED_CURRENT_CLI_GOAL_TOOL_SLICES'
cp['work_in_progress']['next_action'] = 'Implement only registered exact source scopes in separate candidates, retain meaningful raw tests and failures, independently review; no parent/formal acceptance or LIVE promotion.'
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'W05_'+kind.upper()+'_EXACT_SOURCE_SLICE_REGISTERED', 'evidence': ref(scope_path)})
cp['evidence_index'].append(scope_path.relative_to(ROOT).as_posix())
replace(cp_path, cp)
event_path = HERE / (kind + '_scope_value_round_codex.json')
save(event_path, {'schema': 'researchos.value-round.v1', 'round_id': 'W05-'+kind+'-exact-source-scope-20261006',
    'delta': 'INFRASTRUCTURE', 'summary': 'Independent precise source scope registered. Source tests and LIVE acceptance are not yet completed.',
    'evidence_refs': [ref(scope_path), ref(review_path)]})
spec = ROOT / '.local/worktrees/v24-continuation/spec/v2.4'
result = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(ROOT/'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(state_path), '--plan', str(spec/'contracts/execution.plan.json'),
    '--delivery', str(spec/'contracts/delivery.contract.json'), '--expected-revision', str(args.expected_revision),
    '--round-event', str(event_path), '--actor', 'codex:/root'], cwd=ROOT, capture_output=True)
for name, raw in [('stdout.json', result.stdout), ('stderr.txt', result.stderr)]:
    with (HERE / f'checkpoint{args.expected_revision+1}_{kind}.{name}').open('xb') as stream: stream.write(raw)
assert result.returncode == 0, result.stderr.decode('utf8','replace')
after = load(cp_path)
assert state_path.read_bytes() == state_raw and after['failure_counters'] == old_cp['failure_counters']
assert after['value_checkpoint']['history'][:len(old_cp['value_checkpoint']['history'])] == old_cp['value_checkpoint']['history']
assert after['value_checkpoint']['formal_gate']['formal_cases_accepted'] == 3
print(json.dumps({'status':'PASS_EXACT_ADDITIONAL_SLICE_REGISTERED','slice':kind,
    'checkpoint':after['revision'],'paths_revision':paths['revision'],'source_paths':len(proposal['exact_paths']), 'formal_cases_accepted':3}))
