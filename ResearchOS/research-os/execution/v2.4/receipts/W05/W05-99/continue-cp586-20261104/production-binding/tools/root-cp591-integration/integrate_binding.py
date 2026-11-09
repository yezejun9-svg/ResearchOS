"""One-shot Root integration; reconcile its journal after uncertain outcomes."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/production-binding'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    temp = path.with_name(path.name + '.new')
    assert not temp.exists(), str(temp)
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


def git(cwd, *args):
    return subprocess.check_output([
        'git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
        '-c', 'user.name=Codex', '-c', 'user.email=codex@local.invalid',
        '--no-optional-locks', *args,
    ], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')


p = argparse.ArgumentParser()
p.add_argument('--review-file', required=True)
p.add_argument('--review-sha', required=True)
p.add_argument('--expected-revision', type=int, required=True)
p.add_argument('--expected-records', type=int, required=True)
a = p.parse_args()
review_file = OUT / a.review_file
assert review_file.resolve().is_relative_to((OUT / 'reviews').resolve())
assert sha(review_file) == a.review_sha
review = json.loads(review_file.read_bytes())
assert review['decision'] == 'APPROVE_FOUNDATION_ONLY_NOT_PRODUCT_ACCEPTANCE'
assert review['formal_increment'] == 0 and review['independent_vet']['exit_code'] == 0
scope = json.loads((OUT / 'scope.json').read_bytes())
frozen = json.loads((OUT / 'author/FROZEN.json').read_bytes())
assert sha(OUT / 'author/FROZEN.json') == 'b2bcc84dc8d7d35b075afe743f22c4cadc4a93db6cbc1f7d6caf2abe9d78e1cc'
files = {item['path']: item['sha256'] for item in frozen['sources']}
assert len(files) == 4 and set(files) == set(scope['source_paths'])
assert review['source_sha256'] == files
vet_file = Path(review['independent_vet']['ref'])
assert vet_file.resolve().is_relative_to((OUT / 'reviews').resolve())
assert sha(vet_file) == review['independent_vet']['sha256']
assert json.loads(vet_file.read_bytes())['exit_code'] == 0
assert frozen['final_author_attempt'] == 6 and frozen['test_fail'] == 0
attempt = OUT / 'author/attempt-06'
for name in ('gofmt', 'test', 'vet'):
    assert json.loads((attempt / (name + '.result.json')).read_bytes())['exit_code'] == 0
wt = Path(scope['worktree'])
cpfile = ROOT / 'execution/v2.4/checkpoint.json'
raw = cpfile.read_bytes()
cp = json.loads(raw)
assert cp['revision'] == a.expected_revision and len(cp['failure_counters']) == a.expected_records
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
assert git(ROOT, 'rev-parse', 'HEAD').strip() == scope['base_head']
assert git(wt, 'rev-parse', 'HEAD').strip() == scope['base_head']
assert not git(ROOT, 'diff', '--cached', '--name-only').strip()
assert not git(wt, 'diff', '--cached', '--name-only').strip()
assert not git(wt, 'diff', '--name-only').strip()
assert set(git(wt, 'ls-files', '--others', '--exclude-standard').splitlines()) == set(files)
journal = OUT / 'integration-journal.json'
assert not journal.exists(), 'Inspect uncertain outcome; never replay integration'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']


def check_protected():
    for path, digest in protected.items():
        assert (sha(ROOT / path) if (ROOT / path).is_file() else 'ABSENT_BEFORE') == digest, path


check_protected()
for path, digest in files.items():
    assert sha(wt / path) == digest and sha(attempt / 'source' / path) == digest, path
    assert not (ROOT / path).exists(), path
assert sha(wt / 'go.mod') == sha(ROOT / 'go.mod')
assert sha(wt / 'go.sum') == sha(ROOT / 'go.sum')
author = json.loads((OUT / 'author/diagnostics.json').read_bytes())
events = list(json.loads((HERE / 'diagnostics.json').read_bytes())['events'])
for entry in author['events']:
    if entry['id'] in ('no-progress-readback-path-diagnostics', 'attempt05-verification'):
        events.append({'origin_key': '20261104|production-binding|author|' + entry['id'], 'classification': 'AUTHOR_DIAGNOSTIC_PRESERVED', 'detail': entry})
for i, entry in enumerate(review.get('diagnostics', [])):
    key = entry.get('raw_chunk_id') or entry.get('tool_chunk') or ('final-' + str(i))
    events.append({'origin_key': '20261104|production-binding|review-preparation|' + key, 'classification': 'INDEPENDENT_REVIEW_DIAGNOSTIC_PRESERVED', 'detail': entry})
initial = list(cp['failure_counters'])
existing = {entry.get('origin_key') for entry in initial}
new_events = []
now = datetime.now(timezone.utc).isoformat()
for entry in events:
    if entry['origin_key'] not in existing:
        new_events.append(dict(at=now, attempts=1, counter_reset=False, **entry))
        existing.add(entry['origin_key'])
(OUT / ('checkpoint.cp' + str(a.expected_revision) + '.before-integration.json')).write_bytes(raw)
put(journal, {'status': 'VERIFIED_BEFORE_COMMIT', 'base_head': scope['base_head'], 'files': files, 'review_sha256': a.review_sha})
git(wt, 'add', '--', *files)
assert set(git(wt, 'diff', '--cached', '--name-only').splitlines()) == set(files)
git(wt, 'diff', '--cached', '--check')
commit = git(wt, 'commit', '-m', 'feat(domain): add private coding delivery binding integrity foundation')
head = git(wt, 'rev-parse', 'HEAD').strip()
put(journal, {'status': 'COMMITTED_AWAITING_MAIN_FF', 'candidate': head, 'commit_output': commit, 'files': files})
git(ROOT, 'merge', '--ff-only', head)
assert git(ROOT, 'rev-parse', 'HEAD').strip() == head
for path, digest in files.items():
    assert sha(ROOT / path) == digest, path
check_protected()
tree = git(ROOT, 'rev-parse', 'HEAD^{tree}').strip()
result = {
    'status': 'PRIVATE_BINDING_INTEGRITY_FOUNDATION_INTEGRATED_NO_REGISTERED_CALLER',
    'at': now, 'main_head': head, 'main_tree': tree, 'base_head': scope['base_head'],
    'files': files, 'review_ref': str(review_file.relative_to(ROOT)), 'review_sha256': a.review_sha,
    'author_checks_ref': str(attempt.relative_to(ROOT)), 'author_pass_events': 114,
    'protected_preserved': True, 'registry41_unchanged': True, 'step_state_unchanged': True,
    'old_DB_opened_or_migrated': False, 'numbered_migration_added': False,
    'ordinary_LIVE503_unchanged': True, 'SDK_sole_output_unchanged': True,
    'native_or_model_started_this_integration': False, 'formal_increment': 0,
    'limits': 'Integrity only; trusted Host producer/journal/private factory/source checker/Goal aggregation and production schema adoption+backup remain unimplemented.',
}
put(OUT / 'integration.json', result)
revision = a.expected_revision + 1
cp['failure_counters'].extend(new_events)
assert cp['failure_counters'][:a.expected_records] == initial
cp['revision'] = revision
cp['expected_previous_revision'] = a.expected_revision
cp['updated_at'] = now
cp['head'] = cp['current_Main_HEAD'] = head
cp['current_Main_tree'] = tree
cp['current_effective_formal_status']['current_head'] = head
cp['current_effective_formal_status']['needs_rederive_after_source_change'] = True
resume = dict(result, checkpoint_revision=revision, failure_records=len(cp['failure_counters']), counter_reset=False, formal_accepted=0, formal_required=42,
    next='Finish and independently review the owned-controller outer timeout before a separately recorded metadata-only run. Implement scoped W14 verified-native-peer/authenticated-command seams without granting writer takeover; durable native provenance/ACK/replay/settlement/CAS still required.')
put(OUT / 'RESUME.json', resume)
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {'status': result['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)), 'active_construction_owners': ['codex:/root/runtime_readiness controller outer timeout'], 'formal_increment': 0}
cp['workers'].append({'step_id': 'W05-99', 'slice_id': scope['scope_id'], 'owner': 'codex:/root integrated frozen source after independent QA', 'worktree': str(wt), 'state': result['status'], 'main_source_head': head, 'integration_ref': str((OUT / 'integration.json').relative_to(ROOT))})
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / ('handoff.cp' + str(a.expected_revision) + '.before.md')).write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp' + str(revision) + '.new')
assert not temp.exists()
temp.write_bytes(('# Current resume CP' + str(revision) + '\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. Final private binding foundation integrated after real catalog/NPR/checker fixes and independent fresh checks. No registered caller/schema adoption/old DB/API503/SDK output change. Formal0/42; all earlier failures and UNKNOWN evidence retained.\n\n').encode() + before)
os.replace(temp, handoff)
archive = OUT / 'tools/root-cp591-integration'
archive.mkdir()
for name in ('integrate_binding.py', 'diagnostics.json', 'selector.stdout.json', 'selector.stderr.txt', 'selector.command.json'):
    (archive / name).write_bytes((HERE / name).read_bytes())
put(journal, {'status': 'MAIN_CHECKPOINT_HANDOFF_SAVED', 'checkpoint_revision': revision, 'main_head': head, 'main_tree': tree, 'formal_increment': 0})
print(json.dumps({'checkpoint': revision, 'head': head, 'failure_records': len(cp['failure_counters']), 'formal_increment': 0}))
