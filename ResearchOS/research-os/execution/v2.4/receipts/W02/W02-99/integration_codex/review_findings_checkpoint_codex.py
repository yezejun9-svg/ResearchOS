"""Persist W02 review findings and original failures without accepting the parent."""
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

def load(path): return json.loads(path.read_bytes())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
def ref(path, base=V24): return {'path': path.relative_to(base).as_posix(), 'sha256': sha(path)}

cp_path, state_path = V24 / 'checkpoint.json', V24 / 'step_state.json'
cp, state = load(cp_path), load(state_path)
assert cp['revision'] == 202
old_failures = json.loads(json.dumps(cp['failure_counters']))
assert len(old_failures) == 58
row = next(r for r in state['steps'] if r['id'] == 'W02-99')
assert row['status'] == 'IN_PROGRESS'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
now = dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat()
issues = [
    ('W02-parent-G01-isolated-source-and-Mu-manifest',
     HERE.parent / 'run-20261005T204244Z-bef88e7b3cde/receipt.json',
     'RESOLVED_CHANGED_SOURCE_MATERIALIZATION_AND_MANIFEST_READER',
     'Original clean-build harness omitted15 public Go source files and misread Mu manifest files count as a map. Five successful raw subchecks retained; corrected actual builds passed17 internal checks. Original aggregate FAIL was not promoted.'),
    ('W02-parent-G02-pending-classification-and-token-path',
     HERE.parent / 'run-20261005T204259Z-bb25f6d59445/receipt.json',
     'RESOLVED_CHANGED_CLASSIFIER_AND_ROOT_PATH_OVERLAY',
     'Original harness incorrectly reported PENDING_INTEGRATION with both missing binding and stale token mapping. Root path44 and strict only-binding classification repaired the concrete causes; immutable original receipt retained.'),
    ('W02-evidence-reuse-g02-import-AST-boundary',
     HERE.parent / 'independent-review-codex/ast_boundary_probe.json',
     'OPEN_MINIMAL_REPAIR_DISPATCHED',
     'Independent AST-only counterexample showed an unbounded g02 default expression was allowed, despite executing at Python function definition. Mutant was never imported. Body-only exemption and related AST integrity negatives are required before acceptance.'),
    ('W02-parent-output-exact-ID-projection',
     HERE / 'exact_dispatch_results.json',
     'OPEN_MINIMAL_REPAIR_DISPATCHED',
     'Current registered outputs passed their internal assertions but emitted suffix/internal IDs instead of frozen exact W02-G01/G02/G03 parent IDs. Preserve all original17/13/21 checks and root invocation bytes; add a strict parent-report projection before accepting exact gates.'),
]
for key, evidence, status, detail in issues:
    assert not any(r['origin_key'] == key for r in cp['failure_counters'])
    cp['failure_counters'].append({'origin_key': key, 'attempts': 1, 'status': status,
        'evidence': ref(evidence, ROOT), 'detail': detail})
assert cp['failure_counters'][:len(old_failures)] == old_failures
for path in (HERE / 'exact_dispatch_results.json', HERE.parent / 'reuse_handoff_codex.json',
             HERE.parent / 'independent-review-codex/ast_boundary_probe.json'):
    evidence = ref(path)
    if evidence not in row['evidence']: row['evidence'].append(evidence)
    rel = path.relative_to(ROOT).as_posix()
    if rel not in cp['evidence_index']: cp['evidence_index'].append(rel)
row['execution_note'] = ('Actual current registration/mapping and archived product/error raw reviewed; '
    'independent review found import-time AST and exact-parent-ID projection gaps. '
    'Narrow changed-input fixes dispatched, old raw preserved; no parent/formal acceptance.')
write(state_path, state)
cp.update(head=head, updated_at=now, updated_by='codex:/root', current_step_id='W02-99',
    next_step_id='W02-99', work_in_progress={'step_id': 'W02-99',
    'worktree': '.local/worktrees/codex-w0299', 'status': 'IN_PROGRESS',
    'next_action': 'Close independent AST default/decorator boundary and exact parent-ID projection; rerun only changed registered entry validation, then independent acceptance.'},
    note='36 materialized accepted; parent2/22, formal0/42. W02 remains the sole active engineering card. Three root invocations pass internal checks but exact parent projection and AST boundary must be repaired.62 original failure origins preserved, no counter/budget reset.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'card': 'W02-99',
    'event': 'REGISTERED_INTERNAL_RESULTS_AND_INDEPENDENT_FINDINGS_PRESERVED',
    'evidence': ref(HERE / 'exact_dispatch_results.json'),
    'detail': 'Preserve actual3 current registered invocations; no exact-parent-ID, whole-card or formal-case acceptance. Two new independent findings dispatched for narrow fixes.'})
write(cp_path, cp)
event = HERE / 'review_findings_value_round_codex.json'
write(event, {'schema': 'researchos.value-round.v1', 'round_id': 'W02-current-registration-review-findings-20261006',
    'delta': 'INFRASTRUCTURE', 'summary': 'Current root registration and mapping physically executed; independent review exposed exact-ID projection and AST import boundary. Original failures retained and narrow fixes pending; no new parent acceptance.',
    'evidence_refs': [ref(HERE / 'exact_dispatch_results.json', ROOT),
                      ref(HERE.parent / 'independent-review-codex/ast_boundary_probe.json', ROOT)]})
argv = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(state_path), '--plan', str(SPEC / 'contracts/execution.plan.json'),
    '--delivery', str(SPEC / 'contracts/delivery.contract.json'), '--expected-revision', '202',
    '--round-event', str(event), '--actor', 'codex:/root']
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(HERE / 'checkpoint203.stdout.txt').write_bytes(result.stdout)
(HERE / 'checkpoint203.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', 'replace')
after = load(cp_path)
assert after['revision'] == 203 and len(after['failure_counters']) == 62
assert after['failure_counters'][:len(old_failures)] == old_failures
assert after['value_checkpoint']['source_hashes']['step_state'] == sha(state_path)
print(json.dumps({'status': 'PASS_PENDING_REVIEW_FIXES', 'checkpoint': 203,
                  'parent_accepted': 2, 'formal_accepted': 0, 'failure_origins': 62}))
