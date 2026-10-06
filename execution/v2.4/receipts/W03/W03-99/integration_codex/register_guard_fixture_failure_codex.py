"""Preserve the changed-input G02 fixture-role failure before its correction."""
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
SOURCE = ROOT / '.local/worktrees/codex-w0199/execution/v2.4/receipts/W03/W03-99/executor_codex/runs/W03-G02-go-539e02fb3dc4424190511d40d561ee72'

def load(path):
    return json.loads(path.read_bytes())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}

def save_new(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

cp_path = V24 / 'checkpoint.json'
cp = load(cp_path)
assert cp['revision'] == 210 and len(cp['failure_counters']) == 70
old_failures = copy.deepcopy(cp['failure_counters'])
old_accepted = copy.deepcopy(cp['accepted_steps'])
state_path = V24 / 'step_state.json'
state_raw = state_path.read_bytes()
original = load(SOURCE / 'receipt.json')
assert original['gate'] == 'W03-G02' and original['mode'] == 'FIXTURE'
assert original['status'] == 'FAIL' and original['exit_code'] == 1
assert sha(SOURCE / 'stdout.txt') == original['stdout_sha256'] == 'a4cb2e05dd4b6cd7b45c4058db72264cc2e46bc085bc2ce3c39eca44d6c46268'
assert sha(SOURCE / 'stderr.txt') == original['stderr_sha256']
events = [json.loads(line) for line in (SOURCE / 'stdout.txt').read_text(encoding='utf-8').splitlines() if line.strip()]
failed_tests = [event['Test'] for event in events if event.get('Action') == 'fail' and 'Test' in event]
assert failed_tests == ['TestW03CurrentEvaluationArtifactGuard']
assert any('role not authorized' in event.get('Output', '') for event in events)
mirror = HERE / 'observed-probe-failures' / SOURCE.name
mirror.mkdir(parents=True, exist_ok=False)
mirrors = []
for name in ['receipt.json', 'manifest.json', 'stdout.txt', 'stderr.txt']:
    with (mirror / name).open('xb') as stream:
        stream.write((SOURCE / name).read_bytes())
    assert sha(mirror / name) == sha(SOURCE / name)
    mirrors.append(ref(mirror / name))
now = dt.datetime.now(dt.timezone.utc).isoformat()
issue_path = HERE / 'guard_fixture_role_issue_codex.json'
save_new(issue_path, {'schema': 'researchos.actual-fixture-repair-issue.v1',
    'origin_problem_id': 'W03-CURRENT-EVALUATION-GUARD-FIXTURE-ROLE-001',
    'status': 'CONFIRMED_ONLY_REGISTERED_TEST_FIXTURE_CORRECTION', 'actor': 'codex:/root', 'at': now,
    'actual_failed_test': failed_tests[0], 'gate': 'W03-G02', 'mode': 'FIXTURE',
    'source_head': original['source_head'], 'input_digest': original['input_digest'], 'original_artifacts': mirrors,
    'observation': 'The OWNER test caller receives403 role not authorized before the TEST_RESULT guard. This run cannot prove the guard and is not a demonstrated production guard defect.',
    'allowed_correction': 'Only the already authorized internal/domain/w03_current_binding_test.go: use a project-granted EXECUTOR caller and matching produced_by. Production guard remains unchanged.',
    'changed_input_policy': 'Preserve original raw failure. After the test input changes, the broad enrolled source vector changes; revalidate newly frozen source instead of inheriting stale G01/G03 or repeating the old failed input.',
    'formal_case_count_delta': 0, 'parent_accepted': False})
cp['failure_counters'].append({'origin_key': 'W03-current-evaluation-guard-fixture-role', 'attempts': 1,
    'candidate_id': original['source_head'], 'input_hash': original['input_digest'],
    'status': 'OPEN_CONFIRMED_TEST_ROLE_CORRECTION', 'evidence': mirrors[0], 'issue': ref(issue_path),
    'detail': 'Actual G02 new regression fails on OWNER403 before guard. Preserve whole original Go output; authorized correction changes only test identity/grant/produced_by. No production guard relaxation or unchanged failure retry.'})
cp.update(updated_at=now, updated_by='codex:/root',
    note='W03 initial changed-source G01/G03 passed; G02 guard fixture OWNER role failed before intended boundary.71 original failure origins retained. Correct only authorized fixture and reverify changed frozen input; parent3/22 formal0/42 unchanged.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'W03_ACTUAL_G02_FIXTURE_ROLE_FAILURE_PRESERVED', 'evidence': ref(issue_path)})
cp['evidence_index'].append(issue_path.relative_to(ROOT).as_posix())
cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
event_path = HERE / 'guard_fixture_value_round_codex.json'
save_new(event_path, {'schema': 'researchos.value-round.v1',
    'round_id': 'W03-current-evaluation-guard-fixture-role-20261006', 'delta': 'INFRASTRUCTURE',
    'summary': 'Preserve the actual403 fixture failure and require new-input guard verification without changing production guards.',
    'evidence_refs': [ref(issue_path), mirrors[0]]})
argv = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(state_path),
    '--plan', str(SPEC / 'contracts/execution.plan.json'), '--delivery', str(SPEC / 'contracts/delivery.contract.json'),
    '--expected-revision', '210', '--round-event', str(event_path), '--actor', 'codex:/root']
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(HERE / 'checkpoint211.stdout.txt').write_bytes(result.stdout)
(HERE / 'checkpoint211.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
after = load(cp_path)
assert after['revision'] == 211 and len(after['failure_counters']) == 71
assert after['failure_counters'][:70] == old_failures and after['accepted_steps'] == old_accepted
assert state_path.read_bytes() == state_raw
print(json.dumps({'status': 'PASS_ACTUAL_G02_FIXTURE_FAILURE_PRESERVED',
    'checkpoint': 211, 'failure_origins': 71, 'production_guard_edits_authorized': False}))
