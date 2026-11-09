"""Safety checkpoint only: preserves source and pauses the superseded workflow."""
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
PREV = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104'
OUT = ROOT / 'execution/v2.4/receipts/product-shape-replan-20261104'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def git(cwd, *args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', *args], cwd=cwd, stderr=subprocess.STDOUT).decode('utf-8')
def put(p, value):
    t = p.with_name(p.name + '.new'); assert not t.exists()
    t.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8'); os.replace(t, p)

cpfile = ROOT / 'execution/v2.4/checkpoint.json'; oldraw = cpfile.read_bytes(); cp = json.loads(oldraw)
assert cp['revision'] == 601 and len(cp['failure_counters']) == 2448
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
head = git(ROOT, 'rev-parse', 'HEAD').strip()
assert head == 'b8e9efeee3c95dcb8577e5f3fee56ed0b812afc1'
assert not OUT.exists(), 'Inspect any uncertain prior pause checkpoint; do not repeat'
mainstatus = git(ROOT, 'status', '--porcelain=v1', '-uno')
assert len(mainstatus.splitlines()) == 20
protected = read(ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json')['protected_preserved']
for rel, digest in protected.items(): assert (sha(ROOT / rel) if (ROOT / rel).is_file() else 'ABSENT_BEFORE') == digest, rel
trees = {}
for name in ('clients', 'core', 'candidate-capture', 'sandbox-cleanup'):
    scope = read(PREV / name / 'scope.json'); wt = Path(scope['worktree'])
    paths = scope['production_paths'] + scope['test_paths']
    assert wt.resolve().is_relative_to((ROOT / '.local/worktrees').resolve())
    assert all((wt / rel).resolve().is_relative_to(wt.resolve()) for rel in paths)
    trees[name] = dict(worktree=str(wt), head=git(wt, 'rev-parse', 'HEAD').strip(),
        tracked_status=git(wt, 'status', '--porcelain=v1', '-uno'),
        scoped_untracked=git(wt, 'ls-files', '--others', '--exclude-standard', '--', *paths).splitlines(),
        source_sha256={rel: sha(wt / rel) if (wt / rel).is_file() else 'ABSENT_BEFORE' for rel in paths})
now = datetime.now(timezone.utc).isoformat()
pause = dict(checkpoint_revision=602, at=now, status='PAUSED_FOR_LANCER_INSPIRED_PRODUCT_V1_PLANNING',
    main_head=head, main_original_tracked_status=mainstatus, source_worktrees=trees,
    active_construction_owners=[], pending_operations=[], counter_reset=False,
    historical_aggregate_diagnostic_records=2448, legacy_formal_accepted=0, legacy_formal_required=42,
    legacy_acceptance_cards_paused=True, new_acceptance_status='TO_BE_DESIGNED_FROM_PRODUCT_V1_WORKFLOW',
    lancer_source='D:/开发工具/lancer-1.0.1/lancer-1.0.1',
    branch_states={
        'clients': 'exact8 integrated default-off; independent report e85f39 and reconnect addendum d6fe83 preserved',
        'core': '22author-frozen; independent already-started focused session12051 ended af99a4 exit0 run43/pass43. Attack overlay/vet NOT_RUN, rowid risk static/unconfirmed. No acceptance signed.',
        'candidate_capture': '6author-frozen94PASS; independent attempt01 exit1/vet0:116PASS10FAIL,7link/junction fixtureAccessDenied plus3parent failures; no elevated retry started, no acceptance signed.',
        'sandbox_cleanup': '3files installed+gofmt only,17fc8f exit0; never compiled/tested/frozen. Not enabled.',
    },
    pending_branch_diagnostic_aggregation='Author/reviewer raw failures and counters remain at their receipts; not erased or promoted by this pause. Aggregate2448 remains unchanged.',
    old_unknown_qualifications_preserved=True, consumed_model_probe_replay_allowed=False,
    implementation_resumption_allowed=False,
    next='Read-only inspect local Lancer, current ResearchOS and installed/downloaded AI CLI/Harness. Design product V1 screens, real workflow, adapter capabilities and new acceptance criteria before any further implementation. Do not continue old acceptance-card execution, install tools, call models or access credentials.')
OUT.mkdir()
(OUT / 'checkpoint.cp601.before.json').write_bytes(oldraw)
put(OUT / 'PAUSE.json', pause)
put(OUT / 'RESUME.json', pause)
cp['revision'] = 602; cp['expected_previous_revision'] = 601; cp['updated_at'] = now
cp['next_command'] = pause['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = dict(status=pause['status'], at=now, resume_ref=str((OUT / 'RESUME.json').relative_to(ROOT)), active_construction_owners=[], legacy_acceptance_cards_paused=True, formal_increment=0)
cp['product_direction'] = dict(status='READ_ONLY_V1_REPLAN', source='LATEST_EXPLICIT_USER_DIRECTION', reference= pause['lancer_source'], legacy_metrics_preserved=True, new_acceptance_status=pause['new_acceptance_status'])
assert len(cp['failure_counters']) == 2448 and cpfile.read_bytes() == oldraw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'; previous = handoff.read_bytes()
(OUT / 'handoff.cp601.before.md').write_bytes(previous)
t = handoff.with_name(handoff.name + '.cp602.new'); assert not t.exists()
t.write_bytes(('# Current resume CP602 — PRODUCT REPLAN, IMPLEMENTATION PAUSED\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. Latest user direction supersedes continued old-card construction. All source preserved; no pending commands, no active construction. Inspect Lancer and existing Harness read-only, then define product V1 flow and appropriate acceptance. Legacy0/42 and all failures/UNKNOWN retained as history, not silently reused as the new V1 standard.\n\n').encode('utf-8') + previous)
os.replace(t, handoff)
(OUT / 'pause_cp601_for_product_replan.py').write_bytes(Path(__file__).read_bytes())
assert git(ROOT, 'rev-parse', 'HEAD').strip() == head
assert git(ROOT, 'status', '--porcelain=v1', '-uno') == mainstatus
print(json.dumps(dict(checkpoint=602, main_head=head, tracked_statuses=20, protected_entries=len(protected), worktrees=len(trees), pending=0, active_construction=0, historical_records=2448, implementation_paused=True)))
