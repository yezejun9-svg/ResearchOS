import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
HERE = Path(__file__).resolve().parent
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    temp = path.with_name(path.name + '.new')
    assert not temp.exists()
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


def git(cwd, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '-c', 'user.name=Codex', '-c', 'user.email=codex@local.invalid', '--no-optional-locks', *args], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')


p = argparse.ArgumentParser()
p.add_argument('--review-sha', required=True)
p.add_argument('--expected-revision', required=True, type=int)
p.add_argument('--expected-records', required=True, type=int)
a = p.parse_args()
reviewfile = OUT / 'reviews/source-review.json'
assert sha(reviewfile) == a.review_sha
review = json.loads(reviewfile.read_bytes())
assert review['decision'] == 'APPROVE_PRECONDITION_SEAM_ONLY_NOT_HANDOFF_ACCEPTANCE'
assert review['formal_increment'] == 0 and review['independent_vet']['exit_code'] == 0
vet_file = Path(review['independent_vet']['ref'])
assert vet_file.resolve().is_relative_to((OUT / 'reviews').resolve())
assert sha(vet_file) == review['independent_vet']['sha256']
assert json.loads(vet_file.read_bytes())['exit_code'] == 0
manifestfile = OUT / 'author/source-manifest.json'
assert sha(manifestfile) == '2628e7d22108bc481d0efd1a1f40de5f7da82a3b4614cb67b3fef5b79390c6c7'
manifest = json.loads(manifestfile.read_bytes())
files = {item['path']: item['sha256'] for item in manifest['files']}
assert review['source_sha256'] == files
scope = json.loads((OUT / 'scope.json').read_bytes())
assert len(files) == 9 and set(files) == set(scope['production_paths'] + scope['test_paths'])
wt = Path(scope['worktree'])
assert git(ROOT, 'rev-parse', 'HEAD').strip() == scope['base_head']
assert git(wt, 'rev-parse', 'HEAD').strip() == scope['base_head']
assert not git(ROOT, 'diff', '--cached', '--name-only').strip()
assert not git(wt, 'diff', '--cached', '--name-only').strip()
assert set(git(wt, 'diff', '--name-only').splitlines()) == set(scope['production_paths'])
assert set(git(wt, 'ls-files', '--others', '--exclude-standard').splitlines()) == set(scope['test_paths'])
for path, digest in scope['base_source_sha256'].items():
    assert sha(ROOT / path) == digest
for path, digest in files.items():
    assert sha(wt / path) == digest
for path in scope['test_paths']:
    assert not (ROOT / path).exists()
for name in ('go.mod', 'go.sum'):
    assert sha(ROOT / name) == sha(wt / name)
cpfile = ROOT / 'execution/v2.4/checkpoint.json'
raw = cpfile.read_bytes()
cp = json.loads(raw)
assert cp['revision'] == a.expected_revision and len(cp['failure_counters']) == a.expected_records
assert not (OUT / 'integration-journal.json').exists(), 'Inspect uncertain integration; never replay'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']


def check_protected():
    for path, digest in protected.items():
        assert (sha(ROOT / path) if (ROOT / path).is_file() else 'ABSENT_BEFORE') == digest


check_protected()
author = json.loads((OUT / 'author/diagnostics.json').read_bytes())
events = [{'origin_key': '20261104|w14-seam|api-fixture-author', 'classification': 'AUTHOR_HTTP_FIXTURE_FAILURE_PRESERVED', 'detail': {'first_failure': author['first_test_failure'], 'directed_fix': author['directed_fix']}}]
for i, entry in enumerate(author['other_diagnostics']):
    events.append({'origin_key': '20261104|w14-seam|author-read-' + str(i), 'classification': 'AUTHOR_READ_OR_EDIT_CONTROLLER_DIAGNOSTIC_NOT_PRODUCT_FAILURE', 'detail': entry})
for i, entry in enumerate(review.get('diagnostics', [])):
    key = entry.get('raw_chunk_id') or entry.get('tool_chunk') or entry.get('chunk') or ('entry-' + str(i))
    events.append({'origin_key': '20261104|w14-seam|independent-' + key, 'classification': 'INDEPENDENT_REVIEW_DIAGNOSTIC_PRESERVED', 'detail': entry})
initial = list(cp['failure_counters'])
existing = {entry.get('origin_key') for entry in initial}
now = datetime.now(timezone.utc).isoformat()
new_events = []
for event in events:
    if event['origin_key'] not in existing:
        new_events.append(dict(at=now, attempts=1, counter_reset=False, **event))
        existing.add(event['origin_key'])
(OUT / ('checkpoint.cp' + str(a.expected_revision) + '.before-integration.json')).write_bytes(raw)
put(OUT / 'integration-journal.json', {'status': 'VERIFIED_BEFORE_COMMIT', 'files': files, 'review_sha256': a.review_sha})
git(wt, 'add', '--', *files)
assert set(git(wt, 'diff', '--cached', '--name-only').splitlines()) == set(files)
git(wt, 'diff', '--cached', '--check')
commit = git(wt, 'commit', '-m', 'fix(auth): retain native peer provenance and bind command authentication to transaction')
head = git(wt, 'rev-parse', 'HEAD').strip()
put(OUT / 'integration-journal.json', {'status': 'COMMITTED_AWAITING_MAIN_FF', 'candidate': head, 'commit_output': commit})
git(ROOT, 'merge', '--ff-only', head)
for path, digest in files.items():
    assert sha(ROOT / path) == digest
check_protected()
tree = git(ROOT, 'rev-parse', 'HEAD^{tree}').strip()
result = {'status': 'W14_PEER_AUTH_PRECONDITION_SEAM_INTEGRATED_NO_HANDOFF', 'at': now, 'base_head': scope['base_head'], 'main_head': head, 'main_tree': tree, 'files': files, 'review_ref': str(reviewfile.relative_to(ROOT)), 'review_sha256': a.review_sha,
          'protected_preserved': True, 'public_wire_or_registry_changed': False, 'writer_grant_or_lease_or_ACK_changed': False, 'new_table_or_migration': False, 'old_DB_access': False, 'native_or_model_started_this_integration': False,
          'limits': 'Fresh native peer/boot generation and same-transaction credential observations only; ordinary bearer is not native proof. Durable client/writer provenance, exact-request attestation, ACK/replay/settlement/CAS and active pause remain unimplemented.', 'formal_increment': 0}
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
              next='Finish separately scoped Root-supervised metadata-only resource diagnostic after disk/cache/QA readback. Do not replay old UNKNOWN scopes. W14 full handoff remains a separate trusted-persistence/ACK/settlement/CAS implementation.')
put(OUT / 'RESUME.json', resume)
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {'status': result['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)), 'active_construction_owners': [], 'formal_increment': 0}
cp['workers'].append({'step_id': 'W14-01', 'slice_id': scope['scope_id'], 'owner': 'codex:/root integrated independently reviewed9source', 'worktree': str(wt), 'state': result['status'], 'main_source_head': head, 'integration_ref': str((OUT / 'integration.json').relative_to(ROOT))})
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / ('handoff.cp' + str(a.expected_revision) + '.before.md')).write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp' + str(revision) + '.new')
assert not temp.exists()
temp.write_bytes(('# Current resume CP' + str(revision) + '\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. W14 exact9-source peer/auth prerequisite integrated after independent no-native fresh checks; no writer takeover, new table, wire or lease bypass. Source-only, not W14 acceptance. Formal0/42; previous diagnostics/UNKNOWN preserved.\n\n').encode() + before)
os.replace(temp, handoff)
(OUT / 'tools/integrate_w14_seam.py').write_bytes(Path(__file__).read_bytes())
put(OUT / 'integration-journal.json', {'status': 'MAIN_CHECKPOINT_HANDOFF_SAVED', 'checkpoint_revision': revision, 'main_head': head, 'main_tree': tree, 'formal_increment': 0})
print(json.dumps({'checkpoint': revision, 'head': head, 'failure_records': len(cp['failure_counters']), 'source_files': 9, 'formal_increment': 0}))
