"""Root-owned integration only; never executes a model or opens a product DB.

This is deliberately one-shot. Inspect the durable journal after any uncertain
result instead of replaying the script or resetting evidence/counters.
"""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
# The original draft targets CP590 and the rejected attempt04 source. It is
# retained as preparation evidence only. Rebase/review a new integration helper
# after the real NoProgress/checker repairs and independent final acceptance.
raise SystemExit('STALE_PREPARATION_ONLY: CP591 exists; old candidate rejected; do not integrate or replay')
CBASE = Path(__file__).resolve().parent
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    temporary = path.with_name(path.name + '.new')
    assert not temporary.exists(), str(temporary)
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def git(cwd, *args):
    return subprocess.check_output([
        'git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
        '-c', 'user.name=Codex', '-c', 'user.email=codex@local.invalid',
        '--no-optional-locks', *args,
    ], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')


parser = argparse.ArgumentParser()
parser.add_argument('--review', required=True)
parser.add_argument('--review-sha', required=True)
parser.add_argument('--attempt', required=True)
args = parser.parse_args()
review_file = OUT / args.review
assert review_file.resolve().is_relative_to((OUT / 'reviews').resolve())
assert sha(review_file) == args.review_sha
review = json.loads(review_file.read_bytes())
assert review['decision'] == 'APPROVE_FOUNDATION_ONLY_NOT_PRODUCT_ACCEPTANCE'
assert review['formal_increment'] == 0
attempt = OUT / 'author' / args.attempt
assert attempt.resolve().is_relative_to((OUT / 'author').resolve())
files = {item['path']: item['sha256'] for item in json.loads((attempt / 'source-manifest.json').read_bytes())}
scope = json.loads((OUT / 'scope.json').read_bytes())
assert set(files) == set(scope['source_paths']) and len(files) == 4
for name in ('gofmt', 'test'):
    assert json.loads((attempt / (name + '.result.json')).read_bytes())['exit_code'] == 0
assert review['independent_vet']['exit_code'] == 0
wt = Path(scope['worktree'])
cpfile = ROOT / 'execution/v2.4/checkpoint.json'
raw = cpfile.read_bytes()
cp = json.loads(raw)
assert cp['revision'] == 590 and len(cp['failure_counters']) == 2390
assert git(ROOT, 'rev-parse', 'HEAD').strip() == scope['base_head']
assert git(wt, 'rev-parse', 'HEAD').strip() == scope['base_head']
assert not git(ROOT, 'diff', '--cached', '--name-only').strip()
assert not git(wt, 'diff', '--cached', '--name-only').strip()
assert not git(wt, 'diff', '--name-only').strip()
assert set(git(wt, 'ls-files', '--others', '--exclude-standard').splitlines()) == set(files)
assert not (OUT / 'integration-journal.json').exists(), 'Uncertain prior outcome: inspect journal; no replay'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']


def check_protected():
    for path, digest in protected.items():
        actual = sha(ROOT / path) if (ROOT / path).is_file() else 'ABSENT_BEFORE'
        assert actual == digest, path


check_protected()
w14 = CBASE / 'w14-diagnosis'
w14_manifest = json.loads((w14 / 'HOST_IDENTITY_MANIFEST.json').read_bytes())
assert sha(w14 / 'HOST_IDENTITY_MANIFEST.json') == 'b52769c6f31b354c652e39b59d2c03d66d65e1b249db9ada0d4d21986387d3d8'
for entry in w14_manifest['files']:
    assert sha(w14 / entry['path']) == entry['sha256']
    assert (w14 / entry['path']).stat().st_size == entry['bytes']
assert (OUT / 'author/diagnostics.json').is_file()
for path, digest in files.items():
    assert sha(wt / path) == digest, path
    assert not (ROOT / path).exists(), path
assert sha(wt / 'go.mod') == sha(ROOT / 'go.mod')
assert sha(wt / 'go.sum') == sha(ROOT / 'go.sum')
(OUT / 'checkpoint.cp590.before-integration.json').write_bytes(raw)
put(OUT / 'integration-journal.json', {
    'status': 'VERIFIED_BEFORE_COMMIT', 'base_head': scope['base_head'],
    'files': files, 'review_sha256': args.review_sha,
})
git(wt, 'add', '--', *files)
assert set(git(wt, 'diff', '--cached', '--name-only').splitlines()) == set(files)
git(wt, 'diff', '--cached', '--check')
commit_output = git(wt, 'commit', '-m', 'feat(domain): add private coding delivery binding integrity foundation')
head = git(wt, 'rev-parse', 'HEAD').strip()
put(OUT / 'integration-journal.json', {
    'status': 'COMMITTED_AWAITING_MAIN_FAST_FORWARD', 'candidate': head,
    'files': files, 'commit_output': commit_output,
})
git(ROOT, 'merge', '--ff-only', head)
assert git(ROOT, 'rev-parse', 'HEAD').strip() == head
for path, digest in files.items():
    assert sha(ROOT / path) == digest, path
check_protected()
tree = git(ROOT, 'rev-parse', 'HEAD^{tree}').strip()
now = datetime.now(timezone.utc).isoformat()
result = {
    'status': 'PRIVATE_BINDING_INTEGRITY_FOUNDATION_INTEGRATED_NO_REGISTERED_CALLER',
    'at': now, 'base_head': scope['base_head'], 'main_head': head,
    'main_tree': tree, 'files': files,
    'review_ref': str(review_file.relative_to(ROOT)), 'review_sha256': args.review_sha,
    'author_attempt_ref': str(attempt.relative_to(ROOT)),
    'protected_preserved': True, 'numbered_migration_added': False,
    'existing_database_opened': False, 'auto_schema_installation_added': False,
    'ordinary_LIVE503_unchanged': True, 'SDK_sole_output_unchanged': True,
    'registry41_unchanged': True, 'step_state_unchanged': True,
    'native_or_model_started': False, 'formal_increment': 0,
    'limits': 'Integrity only. Trusted Host producer/journal/private creation/checker/Goal aggregation and production schema adoption/backup remain unimplemented.',
}
put(OUT / 'integration.json', result)
events = json.loads((CBASE / 'monitoring-diagnostics-20261104.json').read_bytes())['events']
trace = json.loads((CBASE / 'w14-diagnosis/HOST_IDENTITY_TRACE_DIAGNOSTICS.json').read_bytes())
events.append({'origin_key': '20261104|w14-native-provenance|source-read', 'classification': 'READONLY_SOURCE_QUERY_DIAGNOSTIC_NOT_PRODUCT_FAILURE', 'detail': trace['mixed_success_read']})
for index, event in enumerate(review.get('diagnostics', [])):
    events.append({'origin_key': f'20261104|production-binding|independent-review|{index}', 'classification': 'READONLY_REVIEW_DIAGNOSTIC_NOT_PRODUCT_FAILURE', 'detail': event})
author_diagnostics = OUT / 'author' / 'diagnostics.json'
if author_diagnostics.exists():
    for index, event in enumerate(json.loads(author_diagnostics.read_bytes()).get('events', [])):
        events.append({'origin_key': f'20261104|production-binding|author|{index}', 'classification': 'AUTHOR_DIAGNOSTIC_PRESERVED', 'detail': event})
assert author_diagnostics.exists(), 'Archive original author failure and uncertain transport before control integration'
initial = list(cp['failure_counters'])
existing = {entry.get('origin_key') for entry in initial}
for event in events:
    assert event['origin_key'] not in existing, event['origin_key']
    cp['failure_counters'].append(dict(at=now, attempts=1, counter_reset=False, **event))
    existing.add(event['origin_key'])
assert cp['failure_counters'][:2390] == initial
cp['revision'] = 591
cp['expected_previous_revision'] = 590
cp['updated_at'] = now
cp['head'] = cp['current_Main_HEAD'] = head
cp['current_Main_tree'] = tree
cp['current_effective_formal_status']['current_head'] = head
cp['current_effective_formal_status']['needs_rederive_after_source_change'] = True
resume = {
    'checkpoint_revision': 591, 'status': result['status'], 'main_head': head,
    'main_tree': tree, 'integration_ref': str((OUT / 'integration.json').relative_to(ROOT)),
    'formal_accepted': 0, 'formal_required': 42, 'formal_increment': 0,
    'failure_records': len(cp['failure_counters']), 'counter_reset': False,
    'next': 'Review repaired resource controller before separate metadata-only startup scope. W14 requires real client OS provenance and durable handoff, not a lease bypass. Private business binding remains unregistered until trusted producer, journal, dual contracts, checker and Goal aggregation are implemented.',
}
put(OUT / 'RESUME.json', resume)
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {
    'status': result['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)),
    'active_construction_owners': ['codex:/root/runtime_readiness resource-controller repair'],
    'formal_increment': 0,
}
cp['workers'].append({
    'step_id': 'W05-99', 'slice_id': scope['scope_id'], 'owner': 'codex:/root integrated after independent review',
    'worktree': str(wt), 'state': result['status'], 'main_source_head': head,
    'integration_ref': str((OUT / 'integration.json').relative_to(ROOT)),
})
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / 'handoff.cp590.before.md').write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp591.new')
assert not temp.exists()
temp.write_bytes((
    '# Current resume CP591\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) +
    '. Private Go/SQLite binding foundation integrated after real fresh-DB tests and independent review. No registered product caller, numbered migration, old DB, API/503 or SDK output change. Resource controller pending repaired-source review; W14 identity/handoff gap remains. Formal0/42; all earlier failures preserved.\n\n'
).encode('utf-8') + before)
os.replace(temp, handoff)
archive = OUT / 'tools' / 'root-integration'
archive.mkdir()
for name in ('integrate_production_binding.py', 'CURRENT_EXECUTION_STATE.json', 'monitoring-diagnostics-20261104.json'):
    (archive / name).write_bytes((CBASE / name).read_bytes())
w14_target = OUT.parent / 'w14-trusted-provenance-design'
assert not w14_target.exists()
w14_target.mkdir()
for entry in w14_manifest['files']:
    source = w14 / entry['path']
    assert sha(source) == entry['sha256'] and source.stat().st_size == entry['bytes']
    (w14_target / entry['path']).write_bytes(source.read_bytes())
(w14_target / 'HOST_IDENTITY_MANIFEST.json').write_bytes((w14 / 'HOST_IDENTITY_MANIFEST.json').read_bytes())
put(OUT / 'integration-journal.json', {'status': 'MAIN_AND_CP591_SAVED', 'main_head': head, 'main_tree': tree, 'formal_increment': 0})
print(json.dumps({'checkpoint': 591, 'head': head, 'source_files': 4, 'failure_records': len(cp['failure_counters']), 'formal_increment': 0}))
