import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('D:/作品集/ResearchOS/research-os')
CBASE = Path(__file__).resolve().parent
OUT = ROOT / 'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/checkpoint-cp591'
HEAD = 'b84b065739d64a61407ca815651880b6c06ae36a'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(path, value):
    temporary = path.with_name(path.name + '.new')
    assert not temporary.exists(), str(temporary)
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


cpfile = ROOT / 'execution/v2.4/checkpoint.json'
raw = cpfile.read_bytes()
cp = json.loads(raw)
assert cp['revision'] == 590 and len(cp['failure_counters']) == 2390
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
git_head = subprocess.check_output(['git', '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', '--no-optional-locks', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert git_head == HEAD and cp['current_Main_HEAD'] == HEAD
assert not OUT.exists(), 'Inspect uncertain checkpoint write; do not replay'
protected = json.loads((ROOT / 'execution/v2.4/receipts/W05/W05-99/cli-prompt-bridge-20261104/integration.json').read_bytes())['protected_preserved']
for path, digest in protected.items():
    assert (sha(ROOT / path) if (ROOT / path).is_file() else 'ABSENT_BEFORE') == digest, path
author = json.loads((CBASE / 'production-binding-author-state/diagnostics.json').read_bytes())
prep = json.loads((CBASE / 'production-binding-review/PREPARATION.json').read_bytes())
w14 = json.loads((CBASE / 'w14-diagnosis/HOST_IDENTITY_MANIFEST.json').read_bytes())
r4dir = CBASE / 'owned-model-resource-stage-b/revision-04'
assert sha(r4dir / 'PREPARED-MANIFEST.json') == '5e084c996e0d18fef59411473198739d278ce0e34074c24bb7d1673d3b779270'
r4 = json.loads((r4dir / 'PREPARED-MANIFEST.json').read_bytes())
for item in r4['files']:
    assert sha(r4dir / item['relative']) == item['sha256']
    assert (r4dir / item['relative']).stat().st_size == item['bytes']
assert sha(CBASE / 'w14-diagnosis/HOST_IDENTITY_MANIFEST.json') == 'b52769c6f31b354c652e39b59d2c03d66d65e1b249db9ada0d4d21986387d3d8'
selected = [
    'save_cp591_progress.py', 'CURRENT_EXECUTION_STATE.json', 'monitoring-diagnostics-20261104.json',
    'production-binding-review/PREPARATION.json',
    *['production-binding-author-state/' + name for name in (
        'FROZEN_PINS.json', 'PENDING_HANDOFF.md', 'diagnostics.json',
        'attempt04-invocation01.ps1.txt', 'attempt04-invocation02.ps1.txt', 'INVOCATION_RECORDS.md',
    )],
    'w14-diagnosis/HOST_IDENTITY_MANIFEST.json',
    *['w14-diagnosis/' + item['path'] for item in w14['files']],
    'owned-model-resource-stage-b/revision-04/PREPARED-MANIFEST.json',
    *['owned-model-resource-stage-b/revision-04/' + item['relative'] for item in r4['files'] if item['relative'] != 'controller.exe'],
    'owned-model-resource-stage-b/reviews/source-review.json',
]
for item in w14['files']:
    path = CBASE / 'w14-diagnosis' / item['path']
    assert sha(path) == item['sha256'] and path.stat().st_size == item['bytes']
assert all((CBASE / path).is_file() for path in selected)
OUT.mkdir()
(OUT / 'checkpoint.cp590.before.json').write_bytes(raw)
archive = OUT / 'saved-evidence'
manifest = []
for path in selected:
    source = CBASE / path
    target = archive / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    assert sha(target) == sha(source)
    manifest.append({'path': path, 'sha256': sha(target), 'bytes': target.stat().st_size})
put(OUT / 'saved-evidence-manifest.json', manifest)
now = datetime.now(timezone.utc).isoformat()
events = json.loads((CBASE / 'monitoring-diagnostics-20261104.json').read_bytes())['events']
trace = json.loads((CBASE / 'w14-diagnosis/HOST_IDENTITY_TRACE_DIAGNOSTICS.json').read_bytes())
events.append({'origin_key': '20261104|w14-native-provenance|source-read', 'classification': 'READONLY_SOURCE_QUERY_DIAGNOSTIC_NOT_PRODUCT_FAILURE', 'detail': trace['mixed_success_read']})
selected_ids = {
    'scope-read-relative-path', 'typed-utf8-readback', 'windows-rg-glob', 'checkspec-shape-readback',
    'sql-original-hash-nul', 'attempt03-verification', 'attempt04-invocation01', 'reconnect-cim',
    'attempt04-invocation02', 'attempt04-vet-unknown', 'readonly-helper-limit', 'c-handoff-patch-record',
}
for event in author['events']:
    if event['id'] in selected_ids:
        events.append({'origin_key': '20261104|production-binding|author|' + event['id'], 'classification': 'AUTHOR_DIAGNOSTIC_NOT_FORMAL_ACCEPTANCE', 'detail': event})
for event in prep['diagnostics']:
    events.append({'origin_key': '20261104|production-binding|review-preparation|' + event['raw_chunk_id'], 'classification': 'READONLY_REVIEW_LOCATOR_DIAGNOSTIC', 'detail': event})
events.append({
    'origin_key': '20261104|production-binding|review-canonical-noprogress',
    'classification': 'INDEPENDENT_FOUNDATION_RELATION_DEFECT_SOURCE_NOT_INTEGRATED',
    'detail': 'Reviewer88c516 confirmed public Task lacks origin_problem_id/candidate_id; createTask removes them and stores canonical NoProgressRecord linked by task.no_progress_record_id. Current handmade test positive was insufficient. Author repairing only the four new source files; independent review and fresh tests required again. No old schema/data/test/API changed.',
})
events.append({
    'origin_key': '20261104|production-binding|review-checker-command-key',
    'classification': 'INDEPENDENT_FOUNDATION_CHECKER_IDENTITY_DEFECT_SOURCE_NOT_INTEGRATED',
    'detail': 'Required checker identity was incorrectly matched on check_id display label instead of exact command_key. A schema-valid differently routed checker could be misrecognized after rehashing. Independent reviewer requires exact required command_key or frozen versioned(id,key) identity, ambiguity refusal and actual schema-valid controls. Author repairing same four-file scope.',
})
events.append({
    'origin_key': '20261104|resource-controller|r4-transport',
    'classification': 'UNCERTAIN_EXECUTION_TRANSPORT_RECONCILED_WITH_OFFLINE_TERMINAL',
    'detail': json.loads((r4dir / 'AUTHOR-DIAGNOSTICS.json').read_bytes())['r4_transport'],
})
initial = list(cp['failure_counters'])
existing = {event.get('origin_key') for event in initial}
for event in events:
    assert event['origin_key'] not in existing, event['origin_key']
    cp['failure_counters'].append(dict(at=now, attempts=1, counter_reset=False, **event))
    existing.add(event['origin_key'])
assert cp['failure_counters'][:2390] == initial
resume = {
    'checkpoint_revision': 591, 'status': 'RECONNECTED_SOURCE_REVIEW_IN_PROGRESS_NO_NEW_MAIN_COMMIT',
    'main_head': HEAD, 'failure_records': len(cp['failure_counters']),
    'counter_reset': False, 'formal_accepted': 0, 'formal_required': 42, 'formal_increment': 0,
    'binding': 'Four-file unregistered foundation in isolated worktree. Historical attempt04 source had95PASS, authorvetUNKNOWN. Independent review found actual Task-to-NoProgressRecord relationship and checker command_key identity errors; author repair pending new freeze and peer checks. Do not integrate old pins.',
    'w14': 'Read-only trace/design frozen with21 source hashes. Native peer OS facts discarded before v2; no trusted two-client provenance. No production fix or W14 PASS.',
    'resource': 'R4 final scope/source/controller pins verified and metadata/source/fixture log archived. Author offline build7top5subpurefixtures/vet80d257 exit0; independent review in progress. No real controller/backend/model/GPU/HTTP startup or inference.',
    'transport': 'Root95ff16 elevated read succeeded. A CreateProcess error later corresponded to completed attempt04 files: always reconcile uncertain outcomes, never infer nonexecution from that message.',
    'saved_evidence_ref': str((OUT / 'saved-evidence-manifest.json').relative_to(ROOT)),
    'next': 'Finish real NoProgressRecord relation and checker command_key repair within existing four-file scope and independently reverify final pins. Independently review R4 before separately recorded metadata-only startup. Preserve ordinary LIVE503/SDK output and all historical approvals/UNKNOWN scopes.',
}
put(OUT / 'RESUME.json', resume)
put(OUT / 'save-journal.json', {'status': 'EVIDENCE_ARCHIVED_BEFORE_CHECKPOINT', 'main_head': HEAD, 'failure_records': len(cp['failure_counters'])})
cp['revision'] = 591
cp['expected_previous_revision'] = 590
cp['updated_at'] = now
cp['next_command'] = resume['next'] + ' Read ' + str((OUT / 'RESUME.json').relative_to(ROOT))
cp['current_implementation'] = {
    'status': resume['status'], 'at': now, 'resume_ref': str((OUT / 'RESUME.json').relative_to(ROOT)),
    'active_construction_owners': ['codex:/root/delivery_binding_impl four-file relation/checker repair'],
    'formal_increment': 0,
}
assert cpfile.read_bytes() == raw
put(cpfile, cp)
handoff = ROOT / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
before = handoff.read_bytes()
(OUT / 'handoff.cp590.before.md').write_bytes(before)
temporary = handoff.with_name(handoff.name + '.cp591.new')
assert not temporary.exists()
temporary.write_bytes(('# Current resume CP591\n\nRead ' + str((OUT / 'RESUME.json').relative_to(ROOT)) + '. Main remains b84b0657. Binding independent review requires real NoProgressRecord relation repair; old successful handmade positives do not close it. W14 provenance design frozen, not implemented. Resource R4 author offline checks passed but no native/model startup. Original2390 diagnostic prefix preserved and new failures/uncertainties appended. Formal0/42.\n\n').encode('utf-8') + before)
os.replace(temporary, handoff)
put(OUT / 'save-journal.json', {'status': 'CP591_AND_HANDOFF_SAVED', 'main_head': HEAD, 'failure_records': len(cp['failure_counters']), 'formal_increment': 0})
print(json.dumps({'checkpoint': 591, 'main_head': HEAD, 'failure_records': len(cp['failure_counters']), 'archived_files': len(manifest), 'formal_increment': 0}))
