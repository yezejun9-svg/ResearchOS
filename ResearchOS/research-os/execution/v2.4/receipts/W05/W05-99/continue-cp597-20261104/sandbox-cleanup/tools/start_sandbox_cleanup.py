"""Root-only next-slice allocation after an explicit construction release."""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
READY = HERE / 'cp598-sandbox-cleanup-readonly-20261104'
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/sandbox-cleanup'
PROD = ['ops/experiment_sandbox/sandbox_windows.go', 'ops/experiment_sandbox/async_windows.go']
TEST = ['ops/experiment_sandbox/lifecycle_windows_test.go']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def git(cwd, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', *args], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')
def put(p, v):
    t = p.with_name(p.name + '.new'); assert not t.exists()
    t.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'); os.replace(t, p)

p = argparse.ArgumentParser()
p.add_argument('--release', required=True)
p.add_argument('--release-sha', required=True)
p.add_argument('--expected-checkpoint', required=True, type=int)
p.add_argument('--expected-records', required=True, type=int)
p.add_argument('--expected-head', required=True)
p.add_argument('--remaining-owner', required=True, choices=['codex:/root/workbench_builder', 'codex:/root/delivery_binding_impl'])
a = p.parse_args()
releasefile = Path(a.release)
assert sha(releasefile) == a.release_sha
release = read(releasefile)
assert release['root_read_author_handoff'] and release['construction_frozen']
assert release['source_modification_permitted'] is False
assert release['owner'] != a.remaining_owner
assert sha(Path(release['manifest_path'])) == release['manifest_sha256']
assert sha(READY / 'MANIFEST.json') == 'd0c0011bac83276a1640cfbb842a9d511427a0f0631e869323e0957208affa49'
manifest = read(READY / 'MANIFEST.json')
for item in manifest['source_pins']:
    assert sha(ROOT / item['path']) == item['sha256'], item['path']
cpfile = ROOT / 'execution/v2.4/checkpoint.json'; cpraw = cpfile.read_bytes(); cp = json.loads(cpraw)
assert cp['revision'] == a.expected_checkpoint and len(cp['failure_counters']) == a.expected_records
assert git(ROOT, 'rev-parse', 'HEAD').strip() == a.expected_head
assert not set(git(ROOT, 'diff', '--name-only').splitlines()).intersection(PROD + TEST)
assert not (ROOT / TEST[0]).exists()
assert not OUT.exists(), 'Inspect any uncertain prior allocation; do not replay'
wt = ROOT / '.local/worktrees/sandbox-child-drain-20261104'; assert not wt.exists()
OUT.mkdir()
for d in ('readiness', 'author', 'reviews', 'tools'): (OUT / d).mkdir()
(OUT / ('checkpoint.cp' + str(cp['revision']) + '.before.json')).write_bytes(cpraw)
for f in READY.rglob('*'):
    assert not f.is_symlink() and not f.is_junction(), str(f)
    if f.is_file():
        dest = OUT / 'readiness' / f.relative_to(READY)
        dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(f.read_bytes())
(OUT / 'construction-release.json').write_bytes(releasefile.read_bytes())
git(ROOT, 'worktree', 'add', '--no-checkout', '-b', 'codex/sandbox-child-drain-20261104', str(wt), a.expected_head)
git(wt, 'sparse-checkout', 'set', '--no-cone', '/AGENTS.md', '/go.mod', '/go.sum', '/ops/experiment_sandbox/', '/internal/', '/adapters/', '/apps/', '/migrations/sqlite/', '/spec/v2.0/contracts/')
git(wt, 'checkout', 'HEAD')
evaluation = git(wt, 'ls-tree', '-r', '--name-only', 'HEAD', '--', 'evaluation/holdout/jev', 'evaluation/evolution', 'evaluation/skills').splitlines()
selected = ['/' + s for s in evaluation if s.endswith('.go') and not s.endswith('_test.go')]
if selected: git(wt, 'sparse-checkout', 'add', *selected)
assert not git(wt, 'status', '--porcelain=v1', '-uno').strip()
now = datetime.now(timezone.utc).isoformat()
scope = dict(scope_id='SANDBOX_POST_PRIMARY_CHILD_DRAIN_V1', owner='codex:/root/runtime_readiness', integrator='codex:/root',
    at=now, base_head=a.expected_head, worktree=str(wt), production_paths=PROD, test_paths=TEST,
    baseline_sha256={s: sha(ROOT / s) if (ROOT / s).is_file() else 'ABSENT_BEFORE' for s in PROD + TEST},
    purpose='Fix source-level post-primary held-child pipe deadlock before any new native qualification.',
    root_decisions=[
        'Private real lifecycle coordinator, production adapter uses original held handles. Single runSandbox owner; Cancel remains context notification, no raw Job handle export/reopen/concurrent termination.',
        'Keep primary live/interactive behavior and original command timeout. Preserve 500ms post-primary grace; remaining child requires forced termination and explicit error even when primary exit0, not expanded detached success.',
        'One 5s cleanup deadline covers termination confirmation and bounded stream-result wait. Original primary signal plus observed JobActive0 required; Terminate success or CloseJob alone never proves stopped.',
        'Close own Job KILL_ON_CLOSE fail-safe before any callback/diagnostic/stream join. Close once, no stale numeric handle or goroutine captures; on uncertainty keep receipt incomplete.',
        'Natural complete EOF with callback return needed for both StreamsDrained. Forced read close, missing result, callback stall or stream error never claims drained.',
        'Unconfirmed stop/drain means no output copy or staging/profile deletion race; retain owned resources for separately scoped recovery. Arbitrary Go callback cannot be forcibly stopped; no claim all kernel/FS/BeforeResume calls are bounded.',
        'Public Command/Receipt/Process API, caller WaitBackground, old native tests, recovery_windows.go and qualification journals unchanged.',
        'Only locked offline selected pure tests with fake original-handle ops and clock; no Start/Run/real AppContainer/Job/Native/model/probe/old DB/process scanning or killing.',
    ], formal_increment=0, counter_reset=False,
    forbidden=['No paths outside these3', 'No old qualification replay', 'No new native execution authorization', 'No failure reset or LIVE gate relaxation', 'No registry/step_state/path_ownership/schema changes'])
put(OUT / 'scope.json', scope)
revision = cp['revision'] + 1
owners = [a.remaining_owner, 'codex:/root/runtime_readiness']
resume = dict(checkpoint_revision=revision, status='CANDIDATE_CAPTURE_AND_SANDBOX_CLEANUP_IMPLEMENTING_OTHER_AUTHOR_FROZEN',
    main_head=a.expected_head, failure_records=len(cp['failure_counters']), formal_accepted=0, formal_required=42,
    active_construction_owners=owners, formal_increment=0, counter_reset=False, model_probe_replay_allowed=False,
    scope_ref=str((OUT / 'scope.json').relative_to(ROOT)),
    next='Continue the remaining Core/candidate author and three-path sandbox cleanup; independently review frozen source, then serially integrate approved slices only. No old native/model probe replay or activation of existing databases.')
put(OUT / 'RESUME.json', resume)
cp['revision'] = revision; cp['expected_previous_revision'] = revision - 1; cp['updated_at'] = now
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = dict(status=resume['status'], at=now, resume_ref=str((OUT / 'RESUME.json').relative_to(ROOT)), active_construction_owners=owners, formal_increment=0)
cp['workers'].append(dict(step_id='W14-01', slice_id=scope['scope_id'], owner=scope['owner'], worktree=str(wt), state='SCOPED_SOURCE_IMPLEMENTATION_ONLY', scope_ref=resume['scope_ref']))
assert cpfile.read_bytes() == cpraw; put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'; before = handoff.read_bytes()
(OUT / ('handoff.cp' + str(revision - 1) + '.before.md')).write_bytes(before)
t = handoff.with_name(handoff.name + '.cp' + str(revision) + '.new'); assert not t.exists()
t.write_bytes(('# Current resume CP' + str(revision) + '\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. Remaining source author plus sandbox cleanup are two construction owners; frozen source awaits independent QA. No native/model activation; historical failures and UNKNOWN retained, formal0/42.\n\n').encode('utf-8') + before)
os.replace(t, handoff)
(OUT / 'tools/start_sandbox_cleanup.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=revision, main_head=a.expected_head, worktree=str(wt), source_files=3, formal_increment=0)))
