"""Record independently demonstrated W03 evidence-parser gaps, without product runs."""
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

findings_path = HERE.parent / 'independent_driver_findings_codex.json'
assert sha(findings_path) == '0957484bbf44cfe76960236996de01dd4a94552da0daec811a99025a3e5470ad'
findings = load(findings_path)
assert findings['independent_of_executor'] and findings['pure_memory']
assert findings['product_Go_GUI_provider_service_private_label_operations'] == 0
assert findings['case_count'] == 13 and len(findings['findings']) == 4
manifest_path = Path(findings['evidence_manifest']['path'])
assert sha(manifest_path) == findings['evidence_manifest']['sha256']
manifest = load(manifest_path)
assert manifest['product_or_atom_subprocesses'] == 0
for item in manifest['files']:
    path = (manifest_path.parent / item['path']).resolve()
    assert path.is_relative_to(manifest_path.parent.resolve())
    assert sha(path) == item['sha256'], item['path']
results_path = Path(findings['results']['path'])
assert sha(results_path) == findings['results']['sha256']
results = load(results_path)
assert len(results) == 13 and all(item['synthetic_only'] is True for item in results)
assert len({item['id'] for item in results}) == 13
for name, digest in findings['old_source_hashes'].items():
    assert sha(HERE.parent / 'executor_codex' / name) == digest
cp_path = V24 / 'checkpoint.json'
cp = load(cp_path)
assert cp['revision'] == 209 and len(cp['failure_counters']) == 69
old_failures = copy.deepcopy(cp['failure_counters'])
old_accepted = copy.deepcopy(cp['accepted_steps'])
state_path = V24 / 'step_state.json'
state_raw = state_path.read_bytes()
protected_paths = ['execution/v2.4/commands.json', 'execution/v2.4/path_ownership.json',
    'execution/commands.json', 'internal/domain/contracts/persistence-v24.schema.json']
protected = {name: sha(ROOT / name) for name in protected_paths}
now = dt.datetime.now(dt.timezone.utc).isoformat()
issue_path = HERE / 'driver_integrity_issue_codex.json'
save_new(issue_path, {'schema': 'researchos.demonstrated-evidence-integrity-issue.v1',
    'origin_problem_id': 'W03-DRIVER-EVIDENCE-INTEGRITY-001', 'status': 'CONFIRMED_REPAIR_IN_EXISTING_RECEIPT_SCOPE',
    'actor': 'codex:/root', 'at': now, 'independent_findings': ref(findings_path),
    'actual_pure_memory_results': ref(results_path), 'manifest': ref(manifest_path),
    'findings': findings['findings'], 'synthetic_scope_only': True,
    'accepted_invalid_parser_counterexamples': 7, 'legacy_transport_mismatches': 2,
    'positive_controls': 2, 'negative_controls': 2,
    'existing_authorized_worker_scope': 'execution/v2.4/receipts/W03/W03-99/executor_codex/**',
    'required_fix': 'Strict fixture corpus facts, package/test identity, exact old registry transport, finite JSON and integer non-bool exits. Enroll whole expected.json in the input manifest. Independently replay repaired counterexamples before acceptance.',
    'production_scope_expansion': False, 'new_product_executions': 0,
    'parent_accepted': False, 'formal_case_count_delta': 0})
cp['failure_counters'].append({'origin_key': 'W03-driver-evidence-integrity', 'attempts': 1,
    'candidate_id': 'work/codex-w0399@3e64c5f3',
    'input_hash': findings['evidence_manifest']['sha256'],
    'status': 'OPEN_CONFIRMED_SYNTHETIC_INTEGRITY_COUNTEREXAMPLES',
    'evidence': ref(findings_path), 'issue': ref(issue_path),
    'detail': '13 actual pure-memory controls/counterexamples independently demonstrate4 parser/transport gaps. No product/Go/LIVE probes and no raw atom fabrication or replacement. Repair remains within registered executor receipt paths.'})
cp.update(updated_at=now, updated_by='codex:/root',
    note='W03 current-domain production repair and independently demonstrated evidence integrity repair in progress.70 failure origins retained; parent3/22 formal0/42 unchanged. No product execution or resource retry in this registration.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root',
    'event': 'W03_INDEPENDENT_DRIVER_COUNTEREXAMPLES_PRESERVED_AND_REPAIR_REGISTERED', 'evidence': ref(issue_path)})
cp['evidence_index'].extend([findings_path.relative_to(ROOT).as_posix(), issue_path.relative_to(ROOT).as_posix()])
cp_path.write_text(json.dumps(cp, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
event_path = HERE / 'driver_findings_value_round_codex.json'
save_new(event_path, {'schema': 'researchos.value-round.v1',
    'round_id': 'W03-independent-driver-integrity-findings-20261006', 'delta': 'INFRASTRUCTURE',
    'summary': 'Preserve actual synthetic evidence-parser counterexamples and require strict repair before parent acceptance.',
    'evidence_refs': [ref(issue_path), ref(findings_path)]})
argv = [sys.executable, '-B', '-X', 'utf8', str(ROOT / 'bootstrap/v24_checkpoint.py'),
    '--checkpoint', str(cp_path), '--state', str(state_path),
    '--plan', str(SPEC / 'contracts/execution.plan.json'), '--delivery', str(SPEC / 'contracts/delivery.contract.json'),
    '--expected-revision', '209', '--round-event', str(event_path), '--actor', 'codex:/root']
result = subprocess.run(argv, cwd=ROOT, capture_output=True)
(HERE / 'checkpoint210.stdout.txt').write_bytes(result.stdout)
(HERE / 'checkpoint210.stderr.txt').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode('utf-8', errors='replace')
after = load(cp_path)
assert after['revision'] == 210 and len(after['failure_counters']) == 70
assert after['failure_counters'][:69] == old_failures and after['accepted_steps'] == old_accepted
assert state_path.read_bytes() == state_raw
assert all(sha(ROOT / name) == digest for name, digest in protected.items())
print(json.dumps({'status': 'PASS_DRIVER_FINDINGS_REGISTERED', 'checkpoint': 210,
    'failure_origins': 70, 'synthetic_examples': 13, 'new_product_executions': 0}))
