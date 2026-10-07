"""Register the observed W03 contract repair before changing production inputs."""
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

def read(path):
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
paths_path = V24 / 'path_ownership.json'
cp = read(cp_path)
paths = read(paths_path)
assert cp['revision'] == 208 and paths['revision'] == 46
assert len(cp['failure_counters']) == 68
assert cp['current_step_id'] == 'W03-99'
state_path = V24 / 'step_state.json'
state_raw = state_path.read_bytes()
state = read(state_path)
assert next(row for row in state['steps'] if row['id'] == 'W03-99')['status'] == 'IN_PROGRESS'
old_failures = copy.deepcopy(cp['failure_counters'])
old_accepted = copy.deepcopy(cp['accepted_steps'])
old_blocked = copy.deepcopy(cp['blocked_steps'])
old_value_history = copy.deepcopy(cp['value_checkpoint']['history'])
old_pause = cp['value_checkpoint']['pause_nonblocking_expansion']

existing_paths = [
    'internal/domain/contracts.go', 'internal/domain/store.go',
    'internal/domain/operations.go', 'adapters/evaluation/evaluation.go',
    'apps/control/main.go', 'apps/control/replay_command.go', 'internal/host/host.go',
]
new_worker_paths = [
    'internal/domain/contracts_persistence_v24.go',
    'internal/domain/w03_current_binding_test.go',
    'adapters/evaluation/w03_current_summary_test.go',
    'internal/host/w03_current_contracts_test.go',
]
root_projection_path = 'internal/domain/contracts/persistence-v24.schema.json'
for name in existing_paths:
    assert (ROOT / name).is_file(), name
for name in new_worker_paths + [root_projection_path]:
    assert not (ROOT / name).exists(), name
schema_path = SPEC / 'contracts/domain.schema.json'
assert sha(schema_path) == 'b53d9e6eddfeed89d27ee65c378d8067ae8b0c46de2ba2a098856a7557df1c54'
diagnostic = V24 / 'receipts/W03/W03-99/executor_codex/runs/nested-producer-1c2d84bead794859b96a5f1fe1a319cd/receipt.json'
assert sha(diagnostic) == '3e907f7d666690099605dc91a82809a02ff62e10f2f5f7c4c7b8f7d13ec2a3b6'
protected_paths = [
    'execution/v2.4/commands.json', 'execution/commands.json',
    'execution/toolchains/locked.json', 'internal/domain/contracts/evaluation-v24.schema.json',
    'internal/domain/contracts_evaluation_v24.go', 'spec/v2.0/contracts/domain.schema.json',
    'spec/v2.0/contracts/api.openapi.yaml', 'bootstrap/v24_checkpoint.py',
]
protected = {name: sha(ROOT / name) for name in protected_paths}
now = dt.datetime.now(dt.timezone.utc).isoformat()
scope_path = HERE / 'source_repair_scope_codex.json'
scope = {
    'schema': 'researchos.confirmed-source-repair-scope.v1',
    'origin_problem_id': 'W03-RUNTIME-DOMAIN-V24-PROJECTION-001',
    'status': 'REGISTERED_BEFORE_PRODUCTION_EDITS',
    'registered_at': now, 'step_id': 'W03-99',
    'integrator': 'codex:/root', 'executor': 'codex:/root/w0199_impl',
    'main_source_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'candidate_source_head': '3e64c5f38ad36fc53ad1d9a006861c53931721f8',
    'candidate_worktree': '.local/worktrees/codex-w0199', 'candidate_branch': 'work/codex-w0399',
    'original_issue': ref(HERE / 'runtime_domain_contract_issue_codex.json'),
    'actual_nested_producer_evidence': ref(diagnostic),
    'existing_allowed_paths': {name: sha(ROOT / name) for name in existing_paths},
    'new_allowed_worker_paths': new_worker_paths,
    'root_owned_projection_path': root_projection_path,
    'projection_source': {'path': str(schema_path), 'sha256': sha(schema_path),
        'roots': ['ProjectBinding', 'ProjectState', 'Goal', 'Task', 'EvaluationSummary'],
        'derivation': 'Exact unchanged local transitive $defs closure; root creates and commits this projection before executor edits.'},
    'architecture': [
        'Keep legacy LoadContracts and domain.New behavior; current overlays do not replace old contracts globally.',
        'ProjectBinding has no schema_version. Choose strict current schema only for recognized current binding.route, including ProjectState/Goal/Task nested bindings; recognized legacy routes retain strict legacy schema. Missing or unknown routes fail closed.',
        'GoalPage and TaskPage preserve original outer constraints and validate each item against strict legacy/current oneOf, permitting legitimate mixed pages without stripping fields or weakening item contracts.',
        'Expose only a trusted fixed current Mu constructor, not caller-provided route/version. New project uses MU_FORK; new Goal inherits persisted project binding and new Task inherits persisted Goal binding. Updates retain original bindings.',
        'Both actual control domain services (REST and native Host) use the trusted current constructor; replay uses the same route. Legacy default constructors remain available for old objects and existing fixtures.',
        'EvaluationSummary inherits an already validated report schema_version; 2.0 stays 2.0 and 2.4 stays 2.4. Do not force Normalize NATIVE/PROMPTFOO to 2.4 or silently downgrade invalid/missing versions.',
        'The existing TEST_RESULT artifact guard recognizes 2.4 summary/report versions as well as 2.0, preserving project checks and the existing sealed experiment-output boundary.',
    ],
    'required_changed_input_validation': [
        'Production HTTP and SQLite current Mu ProjectState/Goal/Task creation, binding inheritance, single and mixed strict list response validation.',
        'Legacy stored project continuation and child inheritance preserve binding; malformed routes/refs/versions and client route injection are rejected.',
        'Real normalized validated 2.4 report to 2.4 summary and legacy 2.0 preservation; current TEST_RESULT cannot bypass existing experiment sealing guards.',
        'Source/current projection exact provenance, existing domain/host/evaluation tests appropriate to changed code, then all three registered parent gates.',
    ],
    'forbidden': [
        'Frozen spec edits, migrations, new business authority, client/env route controls, threshold relaxation.',
        'Shared metadata/command registry edits by executor, independent self-acceptance, formal case ownership changes.',
        'Provider/GUI/protected-service/NVDA/resource retries or repeating the blocked W13 workspace audit.',
        'Overwriting original failed receipts or unchanged failed input retries.',
    ],
    'protected_sha256': protected,
    'owned_acceptance_ids': [], 'formal_case_count_delta': 0,
    'parent_accepted': False,
}
save_new(scope_path, scope)
old_binding = copy.deepcopy(paths['card_path_bindings']['W03-99'])
new_binding = copy.deepcopy(old_binding)
new_binding['paths'] = ['execution/v2.4/receipts/W03/W03-99/executor_codex/**'] + existing_paths + new_worker_paths
new_binding['root_only_paths'] += [root_projection_path, 'execution/v2.4/receipts/W03/W03-99/integration_codex/**']
new_binding['source_repair_scope'] = ref(scope_path)
new_binding['source_head'] = scope['candidate_source_head']
new_binding['rationale'] = 'Confirmed actual frozen/current runtime contract gap; precise current-producer and compatibility repair registered before source edits. Original receipt-only scope retained in immutable path_binding_codex.json.'
new_binding['limits'][0] = 'Only exact source_repair_scope_codex.json paths may be edited; root projection and shared registries remain root-owned.'
paths['card_path_bindings']['W03-99'] = new_binding
paths.update(revision=47, amended_at=now, amended_by='codex:/root')
paths_path.write_text(json.dumps(paths, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
save_new(HERE / 'source_path_amendment_codex.json', {
    'schema': 'researchos.path-scope-amendment.v1', 'at': now, 'actor': 'codex:/root',
    'previous_revision': 46, 'revision': 47, 'old_binding': old_binding,
    'new_binding': new_binding, 'scope': ref(scope_path), 'ownership': ref(paths_path),
})
cp.update(updated_at=now, updated_by='codex:/root',
    work_in_progress={'step_id': 'W03-99', 'status': 'REGISTERED_CURRENT_DOMAIN_REPAIR',
        'origin_problem_id': scope['origin_problem_id'], 'worktree': scope['candidate_worktree'],
        'next_action': 'Root generates exact frozen projection, executor implements only registered producer/validation paths, then root runs exact three gates and independent reviewer verifies.'},
    note='W03 confirmed source repair registered before edits. Preserve68 failure origins, all original evidence, parent3/22 and formal0/42; U09 shortest U02 prerequisite remains active.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'W03_CONFIRMED_PRODUCTION_REPAIR_SCOPE_REGISTERED', 'evidence': ref(scope_path)})
cp['evidence_index'].append(scope_path.relative_to(ROOT).as_posix())
cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
event_path = HERE / 'source_scope_value_round_codex.json'
save_new(event_path, {'schema': 'researchos.value-round.v1',
    'round_id': 'W03-confirmed-current-domain-source-scope-20261006', 'delta': 'INFRASTRUCTURE',
    'summary': 'Bound the actual production contract repair and preserve compatibility; no user-flow or formal acceptance inferred.',
    'evidence_refs': [ref(scope_path), ref(HERE / 'source_path_amendment_codex.json')]})
argv = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(state_path),
    '--plan', str(SPEC / 'contracts/execution.plan.json'), '--delivery', str(SPEC / 'contracts/delivery.contract.json'),
    '--expected-revision', '208', '--round-event', str(event_path), '--actor', 'codex:/root']
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(HERE / 'checkpoint209.stdout.txt').write_bytes(result.stdout)
(HERE / 'checkpoint209.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
after = read(cp_path)
assert after['revision'] == 209 and paths['revision'] == 47
assert after['failure_counters'] == old_failures and after['accepted_steps'] == old_accepted
assert after['blocked_steps'] == old_blocked and state_path.read_bytes() == state_raw
assert after['value_checkpoint']['pause_nonblocking_expansion'] == old_pause
assert after['value_checkpoint']['history'][:len(old_value_history)] == old_value_history
assert all(sha(ROOT / name) == digest for name, digest in protected.items())
assert all(sha(ROOT / name) == digest for name, digest in scope['existing_allowed_paths'].items())
print(json.dumps({'status': 'PASS_SCOPE_REGISTERED_BEFORE_EDITS', 'checkpoint': 209,
    'path_revision': 47, 'failure_origins': 68, 'source_edits': 0,
    'parent_accepted': False, 'formal_case_count_delta': 0}))
