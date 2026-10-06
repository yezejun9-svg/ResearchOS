"""Register a root-authorized constructor routing repair under unchanged frozen U09."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
V24 = ROOT / 'execution/v2.4'
SPEC = ROOT / '.local/worktrees/v24-continuation/spec/v2.4'
OUT = HERE / 'u09-priority-repair'
OUT.mkdir(exist_ok=False)

def read(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, data): path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def ref(path, base=ROOT): return {'path': path.relative_to(base).as_posix(), 'sha256': sha(path)}

cp_path = V24 / 'checkpoint.json'
cp = read(cp_path)
assert cp['revision'] == 204 and len(cp['failure_counters']) == 63
old = json.loads(json.dumps(cp['failure_counters']))
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
scope = {'origin_problem_id': 'U09-REQUIRED-PARENT-FRONTIER-001',
    'status': 'AUTHORIZED_ROOT_CONSTRUCTION_TOOLING_REPAIR', 'registered_at': now,
    'integrator': 'codex:/root', 'executor': 'codex:/root/w1102_impl',
    'worktree': '.local/worktrees/codex-w0299', 'branch': 'work/codex-u09-priority',
    'source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'allowed_files': ['bootstrap/v24_checkpoint.py', OUT.relative_to(ROOT).as_posix() + '/**'],
    'root_only_files': ['execution/v2.4/step_state.json', 'execution/v2.4/checkpoint.json', 'execution/v2.4/path_ownership.json'],
    'authorization_basis': 'Explicit ongoing full v2.4 implementation goal and current root shared integrator; repair only the project constructor selector to honor frozen17 section6, not a new product-agent coding demonstration or a new acceptance card.',
    'baseline_inputs': [ref(ROOT / 'bootstrap/v24_checkpoint.py'), ref(V24 / 'step_state.json'),
        ref(cp_path), ref(SPEC / 'contracts/execution.plan.json'), ref(SPEC / 'contracts/delivery.contract.json'),
        ref(SPEC / '17_USER_JOURNEYS_AND_VALUE.md'), ref(HERE / 'checkpoint204_next_packet.json')],
    'observed_problem': 'No direct ready capability implementation slice; existing selector excludes all parent gates and cross-parent prerequisites. It returns NO_READY_USER_FLOW despite the only ready W03-99 belonging to the shortest complete remaining U02 closure W03-99/W04-99/W05-99.',
    'frozen_expectation': 'Prefer direct ready user slices first. Only when absent, select a dependency-ready legal card in an unclosed U01-U08 owner parent dependency closure. Prioritize closures with no registered blockers, then total unaccepted closure length. Keep priority true and count prerequisite work as infrastructure/fixture rather than USER_FLOW.',
    'negative_requirements': ['No arbitrary default fallback or U09-as-user-flow.',
        'Never select BLOCKED/FAILED/CANCELLED/EXECUTION_REPORTED or a card with unaccepted direct dependencies.',
        'No frozen threshold/schema/22-parent/42-case/accepted-state/budget changes.',
        'No service/provider/GUI/old audit/NVDA/resource retries or independent-signed receipt writes.'],
    'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'model_reason': 'Frozen DAG/constructor priority semantics are an architecture decision; reuse existing Astra agent without repeating capacity failures.',
    'formal_case_count_delta': 0}
scope_path = OUT / 'issue_scope_codex.json'
write(scope_path, scope)
erratum = HERE / 'acceptance_postcondition_erratum_codex.json'
cp['failure_counters'].append({'origin_key': 'W02-root-U09-next-selection-postcondition', 'attempts': 1,
    'status': 'RESOLVED_ACCEPTANCE_METADATA_PRIORITY_REPAIR_SEPARATE', 'evidence': ref(erratum),
    'detail': 'Root acceptance was committed to state/CP204; postcondition wrongly expected next selector code0. Actual code3 preserved frozen U09 stop. Read-only finalizer confirmed completed independent acceptance; separate original priority gap now frozen for narrow repair.'})
assert cp['failure_counters'][:63] == old
cp.update(updated_at=now, updated_by='codex:/root', current_step_id=None, next_step_id=None,
    work_in_progress={'origin_problem_id': scope['origin_problem_id'], 'status': 'CONSTRUCTION_SELECTOR_REPAIR_IN_PROGRESS',
        'worktree': scope['worktree'], 'next_action': 'Repair legal required-user-flow parent frontier and independently verify, preserving U09 priority/history. No frozen card dispatched yet.'},
    note='37 materialized accepted, parent3/22 formal0/42. W02 independent acceptance finalized.64 original failure origins preserved. U09 direction stop remains active; narrow necessary-prerequisite selector repair registered before edits, no new user-flow claim or resource replay.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'U09_REQUIRED_PREREQUISITE_REPAIR_REGISTERED',
    'evidence': ref(scope_path), 'detail': 'Frozen17 section6 requires shortest user-flow gap work. Record precise root construction-only source scope and independent review; no threshold/counter/acceptance reset.'})
cp['evidence_index'].extend([scope_path.relative_to(ROOT).as_posix(), erratum.relative_to(ROOT).as_posix()])
write(cp_path, cp)
event = OUT / 'registration_value_round_codex.json'
write(event, {'schema': 'researchos.value-round.v1', 'round_id': 'U09-required-parent-frontier-repair-start-20261006',
    'delta': 'INFRASTRUCTURE', 'summary': 'Freeze constructor priority defect: required parent frontier omitted. Register narrow repair while retaining direction-stop history and formal gates.', 'evidence_refs': [ref(scope_path), ref(erratum)]})
argv = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(V24 / 'step_state.json'), '--plan', str(SPEC / 'contracts/execution.plan.json'),
    '--delivery', str(SPEC / 'contracts/delivery.contract.json'), '--expected-revision', '204', '--round-event', str(event), '--actor', 'codex:/root']
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(OUT / 'checkpoint205.stdout.txt').write_bytes(result.stdout)
(OUT / 'checkpoint205.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0
after = read(cp_path)
assert after['revision'] == 205 and len(after['failure_counters']) == 64
assert after['failure_counters'][:63] == old and after['value_checkpoint']['pause_nonblocking_expansion'] is True
print(json.dumps({'status': 'PASS_REPAIR_SCOPE_REGISTERED', 'checkpoint': 205,
                  'failure_origins': 64, 'card_dispatches': 0}))
