"""Allocate the next source slice only after the client author explicitly freezes.

The required release file is written by Root after reading the author's frozen
handoff. It is not elapsed-time approval and never authorizes native/model work.
"""
import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/candidate-capture'
READY = HERE / 'cp598-coding-delivery-next-scope'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def put(p, value):
    t = p.with_name(p.name + '.new')
    assert not t.exists()
    t.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(t, p)
def git(cwd, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', *args], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')

p = argparse.ArgumentParser()
p.add_argument('--release', required=True)
p.add_argument('--release-sha', required=True)
p.add_argument('--expected-checkpoint', required=True, type=int)
p.add_argument('--expected-records', required=True, type=int)
p.add_argument('--expected-head', required=True)
a = p.parse_args()
releasefile = Path(a.release)
assert sha(releasefile) == a.release_sha
release = read(releasefile)
assert release['root_read_author_handoff'] and release['client_construction_frozen']
assert release['source_modification_permitted'] is False
assert sha(Path(release['manifest_path'])) == release['manifest_sha256']
assert sha(READY / 'MANIFEST.final.json') == 'd0f46a83b9a1ce5300e67d145e0b833b8d75bd0c5e58a345f9817965b42fe583'
proposal = read(READY / 'NEXT_SLICE.json')
paths = [entry['path'] for entry in proposal['exact_paths']]
assert len(paths) == 6
prod = [p for p in paths if not p.endswith('_test.go')]
tests = [p for p in paths if p.endswith('_test.go')]
assert len(prod) == 4 and len(tests) == 2
cpfile = ROOT / 'execution/v2.4/checkpoint.json'
cpraw = cpfile.read_bytes(); cp = json.loads(cpraw)
assert cp['revision'] == a.expected_checkpoint and len(cp['failure_counters']) == a.expected_records
assert git(ROOT, 'rev-parse', 'HEAD').strip() == a.expected_head
assert not set(git(ROOT, 'diff', '--name-only').splitlines()).intersection(paths)
assert not OUT.exists(), 'Reconcile an uncertain prior scope allocation before retry'
protected = read(ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json')['protected_preserved']
for rel, digest in protected.items():
    actual = sha(ROOT / rel) if (ROOT / rel).is_file() else 'ABSENT_BEFORE'
    assert actual == digest, rel
now = datetime.now(timezone.utc).isoformat()
OUT.mkdir()
for child in ('readiness', 'author', 'reviews', 'tools'): (OUT / child).mkdir()
(OUT / ('checkpoint.cp' + str(cp['revision']) + '.before.json')).write_bytes(cpraw)
for f in READY.iterdir():
    assert f.is_file() and not f.is_symlink()
    (OUT / 'readiness' / f.name).write_bytes(f.read_bytes())
(OUT / 'client-author-release.json').write_bytes(releasefile.read_bytes())
wt = ROOT / '.local/worktrees/host-candidate-capture-20261104'
assert not wt.exists()
git(ROOT, 'worktree', 'add', '--no-checkout', '-b', 'codex/host-candidate-capture-20261104', str(wt), a.expected_head)
git(wt, 'sparse-checkout', 'set', '--no-cone', '/AGENTS.md', '/go.mod', '/go.sum', '/internal/', '/adapters/', '/apps/', '/tests/runtime/', '/migrations/sqlite/', '/spec/v2.0/contracts/', '/ops/')
git(wt, 'checkout', 'HEAD')
evaluation = git(wt, 'ls-tree', '-r', '--name-only', 'HEAD', '--', 'evaluation/holdout/jev', 'evaluation/evolution', 'evaluation/skills').splitlines()
selected = ['/' + p for p in evaluation if p.endswith('.go') and not p.endswith('_test.go')]
if selected: git(wt, 'sparse-checkout', 'add', *selected)
assert not git(wt, 'status', '--porcelain=v1', '-uno').strip()
scope = dict(scope_id=proposal['scope_id'], at=now, owner='codex:/root/delivery_binding_impl', integrator='codex:/root',
    base_head=a.expected_head, worktree=str(wt), production_paths=prod, test_paths=tests,
    baseline_sha256={p: sha(ROOT / p) if (ROOT / p).is_file() else 'ABSENT_BEFORE' for p in paths},
    purpose='Candidate-only same-byte final-private-copy witness; no business checker/factory or production activation.',
    root_decisions=[
        'Private unexported context has no JSON input or exported producer; nil follows old sandbox.Run unchanged; unknown nonnil fails closed.',
        'Prepare freezes roster/fixed files/suite/identity, not editable candidate content. This check-time Host staging manifest after the last authorized write is the final-copy baseline.',
        'BeforeResume uses actual final private staging copy and native identity; candidate bytes are bounded and captured once. Fixed go.mod/test bytes are hashed, never retained in candidate evidence.',
        'Only candidate bytes plus structural-only deliverygate witness can enter host_evidence. SDK len1, model response and business Goal503 unchanged.',
        'Match immutable capture/native callback/complete receipt identity. A nonzero or timeout must not become business PASS. No final reread from workspace.',
        'New Start+BeforeResume branch preserves existing Run semantics by Wait(context.Background()); do not return early through Wait(ctx) then delete staging while cleanup is active. No new sandbox cancellation policy.',
        'os.Root alone is not no-reparse or exact-spelling proof. Explicit Windows attributes and bounded exact inventory checks are required; final toolchain/vendor and same-OS-user exclusion are not claimed.',
        'Use pure fresh directory fixtures only; no sandbox/process/native/model/probe/old DB/provider/real frozen issue execution.',
    ],
    forbidden=['No paths outside six scoped files', 'No trusted factory invention', 'No schema/migration/registry/step_state/path_ownership changes', 'No LIVE gate relaxation', 'No old failed/UNKNOWN probe replay', 'No failure reset'],
    formal_increment=0, counter_reset=False)
put(OUT / 'scope.json', scope)
review = read(ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients/reviews/freeze-01/source-review.json')
old_records = list(cp['failure_counters']); known = {x.get('origin_key') for x in old_records}
for i, event in enumerate(review['diagnostics']):
    origin_key = '20261104|cp598-clients-v1-independent|' + event['tool_chunk'] + '|' + str(i)
    if origin_key not in known:
        cp['failure_counters'].append(dict(at=now, attempts=1, origin_key=origin_key, counter_reset=False, classification=event['category'], detail=event))
        known.add(origin_key)
assert cp['failure_counters'][:len(old_records)] == old_records
revision = cp['revision'] + 1
owners = ['codex:/root/workbench_builder', 'codex:/root/delivery_binding_impl']
resume = dict(checkpoint_revision=revision, status='CORE_AND_PRIVATE_CANDIDATE_CAPTURE_IMPLEMENTING_CLIENTS_FROZEN_FOR_REVIEW',
    main_head=a.expected_head, formal_accepted=0, formal_required=42, formal_increment=0,
    failure_records=len(cp['failure_counters']), counter_reset=False, active_construction_owners=owners,
    scope_ref=str((OUT / 'scope.json').relative_to(ROOT)), model_probe_replay_allowed=False,
    next='Continue Core and six-path candidate capture implementation with offline checks and independent review. Independently review repaired frozen client02, then integrate exact approved slices serially. Do not replay consumed model diagnostics or activate old databases.')
put(OUT / 'RESUME.json', resume)
cp['revision'] = revision; cp['expected_previous_revision'] = revision - 1; cp['updated_at'] = now
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = dict(status=resume['status'], at=now, resume_ref=str((OUT / 'RESUME.json').relative_to(ROOT)), active_construction_owners=owners, formal_increment=0)
cp['workers'].append(dict(step_id='W14-01', slice_id=scope['scope_id'], owner=scope['owner'], worktree=str(wt), state='SCOPED_SOURCE_IMPLEMENTATION_ONLY', scope_ref=resume['scope_ref']))
assert cpfile.read_bytes() == cpraw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes(); (OUT / ('handoff.cp' + str(revision - 1) + '.before.md')).write_bytes(before)
temp = handoff.with_name(handoff.name + '.cp' + str(revision) + '.new'); assert not temp.exists()
temp.write_bytes(('# Current resume CP' + str(revision) + '\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. Client v1 real Go/Node failures retained; repaired client frozen for review. Core and private candidate capture are the two construction owners. Prepared fixtures only; formal0/42, consumed model scope unchanged.\n\n').encode('utf-8') + before)
os.replace(temp, handoff)
(OUT / 'tools/start_cp598_capture.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps(dict(checkpoint=revision, main_head=a.expected_head, failure_records=len(cp['failure_counters']), worktree=str(wt), source_files=6, formal_increment=0)))
