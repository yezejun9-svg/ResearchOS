"""Root-only, one-shot serial integration of an independently reviewed frozen slice.

This script is deliberately inert without a separately prepared pinned plan.
Any existing journal requires manual outcome reconciliation, never a retry.
"""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observed(path):
    return sha(path) if path.is_file() else 'ABSENT_BEFORE'


def read(path):
    return json.loads(path.read_bytes())


def git(cwd, *args):
    return subprocess.check_output([
        'git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false',
        '-c', 'user.name=Codex', '-c', 'user.email=codex@local.invalid',
        '--no-optional-locks', *args,
    ], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')


def put(path, value):
    temp = path.with_name(path.name + '.new')
    assert not temp.exists(), str(temp)
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temp, path)


parser = argparse.ArgumentParser()
parser.add_argument('--plan', required=True)
parser.add_argument('--plan-sha', required=True)
args = parser.parse_args()
planfile = Path(args.plan)
assert sha(planfile) == args.plan_sha
plan = read(planfile)
assert plan['root_only'] is True and plan['formal_increment'] == 0
scopefile = ROOT / plan['scope_ref']
assert sha(scopefile) == plan['scope_sha256']
scope = read(scopefile)
wt = Path(scope['worktree'])
out = ROOT / plan['receipt_ref']
assert out.resolve().is_relative_to((ROOT / 'execution/v2.4/receipts').resolve())
assert out.is_dir()
journal = out / 'root-integration-journal.json'
assert not journal.exists(), 'Inspect existing journal and reconcile uncertain effects; do not replay'
reviewfile = ROOT / plan['review_ref']
assert sha(reviewfile) == plan['review_sha256']
review = read(reviewfile)
assert review['decision'] == plan['approved_decision']
assert review['formal_increment'] == 0
assert not review.get('pending_blockers', [])
files = plan['source_sha256']
assert files and set(files).issubset(set(scope['production_paths'] + scope['test_paths']))
assert files == review['source_sha256']
for ref, digest in plan['evidence_pins'].items():
    assert sha(ROOT / ref) == digest, ref
for rel, digest in scope['baseline_sha256'].items():
    assert observed(ROOT / rel) == digest, ('Main path no longer at reviewed baseline', rel)
    if rel not in files:
        assert observed(wt / rel) == digest, ('Unreviewed author change', rel)
for rel, digest in files.items():
    assert sha(wt / rel) == digest, ('Author freeze drift', rel)
assert git(ROOT, 'rev-parse', 'HEAD').strip() == plan['expected_main_head']
assert git(wt, 'rev-parse', 'HEAD').strip() == scope['base_head']
assert not git(ROOT, 'diff', '--cached', '--name-only').strip()
assert not git(wt, 'diff', '--cached', '--name-only').strip()
tracked = set(git(wt, 'diff', '--name-only').splitlines())
untracked = set(git(wt, 'ls-files', '--others', '--exclude-standard').splitlines())
assert tracked | untracked == set(files), (tracked, untracked)
for name in ('go.mod', 'go.sum'):
    assert sha(ROOT / name) == sha(wt / name)
protected = read(ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json')['protected_preserved']


def check_protected():
    for rel, digest in protected.items():
        assert observed(ROOT / rel) == digest, ('Protected old result drift', rel)


check_protected()
status_before = git(ROOT, 'status', '--porcelain=v1', '-uno')
cpfile = ROOT / 'execution/v2.4/checkpoint.json'
cpraw = cpfile.read_bytes()
cp = json.loads(cpraw)
assert cp['revision'] == plan['expected_checkpoint']
assert len(cp['failure_counters']) == plan['expected_failure_records']
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
original_records = list(cp['failure_counters'])
new_records = []
known = {entry.get('origin_key') for entry in original_records}
now = datetime.now(timezone.utc).isoformat()
for event in plan.get('diagnostic_events', []):
    assert event['origin_key'] and event['classification']
    if event['origin_key'] not in known:
        new_records.append(dict(at=now, attempts=1, counter_reset=False, **event))
        known.add(event['origin_key'])
(out / ('checkpoint.cp' + str(cp['revision']) + '.before-integration.json')).write_bytes(cpraw)
put(journal, {'status': 'VERIFIED_BEFORE_SOURCE_COPY', 'plan_sha256': args.plan_sha,
              'base_main': plan['expected_main_head'], 'source_sha256': files})
for rel, digest in files.items():
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((wt / rel).read_bytes())
    assert sha(target) == digest
git(ROOT, 'add', '--', *files)
assert set(git(ROOT, 'diff', '--cached', '--name-only').splitlines()) == set(files)
git(ROOT, 'diff', '--cached', '--check')
put(journal, {'status': 'EXACT_PATHS_STAGED_AWAITING_COMMIT', 'source_sha256': files})
commit_output = git(ROOT, 'commit', '-m', plan['commit_message'])
head = git(ROOT, 'rev-parse', 'HEAD').strip()
tree = git(ROOT, 'rev-parse', 'HEAD^{tree}').strip()
put(journal, {'status': 'MAIN_COMMITTED_AWAITING_CHECKPOINT', 'main_head': head,
              'main_tree': tree, 'commit_output': commit_output})
for rel, digest in files.items():
    assert sha(ROOT / rel) == digest
check_protected()
assert git(ROOT, 'status', '--porcelain=v1', '-uno') == status_before
revision = cp['revision'] + 1
result = {'status': plan['result_status'], 'at': now, 'checkpoint_revision': revision,
          'base_main_head': plan['expected_main_head'], 'main_head': head, 'main_tree': tree,
          'source_sha256': files, 'review_ref': plan['review_ref'],
          'review_sha256': plan['review_sha256'], 'protected_preserved': True,
          'original_tracked_statuses_preserved': True, 'formal_increment': 0,
          'old_database_access': False, 'native_or_model_started': False,
          'limits': plan['limits']}
put(out / 'integration.json', result)
cp['failure_counters'].extend(new_records)
assert cp['failure_counters'][:len(original_records)] == original_records
cp['revision'] = revision
cp['expected_previous_revision'] = revision - 1
cp['updated_at'] = now
cp['head'] = cp['current_Main_HEAD'] = head
cp['current_Main_tree'] = tree
cp['current_effective_formal_status']['current_head'] = head
cp['current_effective_formal_status']['needs_rederive_after_source_change'] = True
resume = dict(result, failure_records=len(cp['failure_counters']), counter_reset=False,
              formal_accepted=0, formal_required=42, next=plan['next'],
              active_construction_owners=plan['active_construction_owners'],
              model_probe_replay_allowed=False)
resume_ref = str((out / 'RESUME.json').relative_to(ROOT))
put(out / 'RESUME.json', resume)
cp['next_command'] = plan['next'] + ' Read ' + resume_ref
cp['current_implementation'] = {'status': result['status'], 'at': now,
    'resume_ref': resume_ref, 'active_construction_owners': plan['active_construction_owners'],
    'formal_increment': 0}
cp['workers'].append({'step_id': 'W14-01', 'slice_id': scope['scope_id'],
    'owner': 'codex:/root integrated independently reviewed source', 'worktree': str(wt),
    'state': result['status'], 'main_source_head': head, 'integration_ref': str((out / 'integration.json').relative_to(ROOT))})
assert cpfile.read_bytes() == cpraw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
oldhandoff = handoff.read_bytes()
(out / ('handoff.cp' + str(revision - 1) + '.before.md')).write_bytes(oldhandoff)
temporary = handoff.with_name(handoff.name + '.cp' + str(revision) + '.new')
assert not temporary.exists()
temporary.write_bytes(('# Current resume CP' + str(revision) + '\n\nRead ' + resume_ref +
    '. ' + plan['handoff_sentence'] + ' Formal0/42; historical diagnostics/UNKNOWN and consumed model scope retained.\n\n').encode('utf-8') + oldhandoff)
os.replace(temporary, handoff)
(out / 'root-integration-plan.json').write_bytes(planfile.read_bytes())
(out / 'integrate_cp598_slice.py').write_bytes(Path(__file__).read_bytes())
put(journal, {'status': 'MAIN_CHECKPOINT_HANDOFF_SAVED', 'checkpoint_revision': revision,
              'main_head': head, 'main_tree': tree, 'formal_increment': 0})
print(json.dumps({'checkpoint': revision, 'main_head': head, 'source_files': len(files),
    'failure_records': len(cp['failure_counters']), 'formal_increment': 0}))
