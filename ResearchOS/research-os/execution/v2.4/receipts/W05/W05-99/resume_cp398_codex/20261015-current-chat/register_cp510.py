import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp510'
E = R / 'execution/v2.4/receipts/W05/W05-99'
A = E / 'qualification_projection_a_revision02_source_codex/20261015-current-chat'
I = E / 'qualification_projection_a_independent_review_codex/20261015-current-chat'
H = E / 'historical_qualification_public_provenance_codex/20261015-current-chat'
W = R / '.local/worktrees/qualification-projection-a-r2-20261015'
CANDIDATE = 'f48fca0e4013bda19913a34d91da0cd23157a08b'
BASE = '525a9c923a8761a9491070123de3c94aa5618d71'
MAIN = '4f4023c956f84d65743f39ce77d6c8899a21ada1'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    data = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def new(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def git(*args, cwd=R):
    return subprocess.check_output(['git', *args], cwd=cwd)


def replace(p, before, after):
    assert p.read_bytes() == before
    temporary = p.with_name(p.name + '.cp510.pending')
    with temporary.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(temporary, p)


assert ref(A / 'source-manifest.revision02.json')['sha256'] == '9acfbe0094a73d4a994f44bf0bcb9714470871fd200142960172a67309a8caa6'
manifest = read(A / 'source-manifest.revision02.json')
assert manifest['commit'] == CANDIDATE
assert git('rev-parse', 'HEAD', cwd=W).decode().strip() == CANDIDATE
assert git('rev-parse', CANDIDATE + '^{tree}', cwd=W).decode().strip() == '16e72ccf939c13142091495458ad04348a3ba660'
assert not git('status', '--porcelain=v1', '-uno', cwd=W)
paths = git('diff', '--name-only', BASE, CANDIDATE, cwd=W).decode().splitlines()
assert sorted(paths) == sorted(item['path'] for item in manifest['source_paths']) and len(paths) == 10
construction = read(B / 'continuation-cp503/qualification-projection-A-revision02-source-scope.json')
original_scope = read(B / 'continuation-cp497/qualification-projection-A-implementation-scope.json')
allowed = set(construction['allowed_existing_source'] + construction['allowed_new_source'] + construction['allowed_tests'])
assert set(paths) <= allowed
assert set(git('diff', '--name-only', MAIN, CANDIDATE, cwd=W).decode().splitlines()) <= allowed
for item in manifest['source_paths']:
    p = W / item['path']
    assert ref(p)['sha256'] == item['sha256'] and p.stat().st_size == item['bytes']
    assert git('show', CANDIDATE + ':' + item['path'], cwd=W) == p.read_bytes()
for name, base in [('r2-diff-from-525.binary.patch', BASE), ('r2-full-diff-from-4f.binary.patch', MAIN)]:
    p = A / name
    assert ref(p)['sha256'] == manifest['patches'][name]['sha256']
    assert p.stat().st_size == manifest['patches'][name]['bytes']
    assert git('diff', '--binary', base, CANDIDATE, '--', *sorted(paths), cwd=W) == p.read_bytes()
for command in manifest['recorded_commands']:
    for suffix, key in [('.stdout.raw', 'stdout'), ('.stderr.raw', 'stderr')]:
        p = A / (command['tag'] + suffix)
        assert ref(p)['sha256'] == command[key + '_sha256'] and p.stat().st_size == command[key + '_bytes']
    assert ref(A / (command['tag'] + '.command.json'))['sha256'] == command['command_sha256']
resource_manifests = []
for relative, expected in [('verifier-dependency-inputs01/COLLECTION-manifest.json', '99617d07ea92e2f5a0142ce09445394867074ba308e2b2800bf062a8be6b9c9e'), ('verifier-initializer-index01/COLLECTION-manifest.json', '717bacc93892081fcb1895f70c3cc5e8e8371faf17f264fbc5b710ecdcfca3c6')]:
    p = H / relative
    assert ref(p)['sha256'] == expected
    for item in read(p)['files']:
        member = Path(item['path'])
        assert hashlib.sha256(member.read_bytes()).hexdigest() == item['sha256'] and member.stat().st_size == item['bytes']
    resource_manifests.append(ref(p))

cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 509 and ow['revision'] == 295 and len(cp['failure_counters']) == 1607
assert git('rev-parse', 'HEAD').decode().strip() == MAIN and not git('diff', '--cached', '--name-only')
assert len(git('status', '--short', '--untracked-files=no').decode().splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
O.mkdir(exist_ok=False)
scope = {
    'schema': 'researchos.qualification-projection-A-revision02-independent-review.v1',
    'at': now,
    'owner': 'codex:/root/qualification_projection_review',
    'model': 'gpt-6-astra',
    'reasoning_effort': 'high',
    'model_choice_reason': 'Independent review of F01 native regression, F02 canonical number cloning, F03 true consumer mutation and positive controls across complete revised Source candidate',
    'mode': 'READONLY_SOURCE_REVIEW_ONLY',
    'candidate_commit': CANDIDATE,
    'candidate_tree': manifest['tree'],
    'base_commit': BASE,
    'main_base_commit': MAIN,
    'worktree': str(W),
    'source_manifest_ref': ref(A / 'source-manifest.revision02.json'),
    'prior_independent_review_ref': ref(I / 'evidence-manifest.revision02.json'),
    'construction_scope_ref': ref(B / 'continuation-cp503/qualification-projection-A-revision02-source-scope.json'),
    'original_scope_ref': ref(B / 'continuation-cp497/qualification-projection-A-implementation-scope.json'),
    'own_receipts': str(E / 'qualification_projection_a_revision02_independent_review_codex/20261015-current-chat'),
    'requirements': [
        'Verify frozen final source-manifest.revision02 SHA and exact candidate tree, patches from525 and4f restricted to10r2paths, all10 r2 paths within original16 and entire combined A production source. Root found author filename r2-full-diff-from-4f misleading: freeze helper restricts it to10r2paths and omits inherited A files; use full candidate Git4f diff for whole Source review, not that partial patch alone. Candidate immutable. No Source fixes, sharedstate, installed package, actual DB/OS/model/GUI/qualification/Core stop/oldRun operations. You are not alone: STOPanchor-r2 builder and C/F01 design reviewer; never revert or edit their work. Own receipts/new D temps only.',
        'Revisit F01 NativeOffline qualification before model config lookup and ordinary native behavior; targeted native regression must actually execute. F02 clone with UseNumber must preserve positive JSON representation then each single field mutation fails for intended reason; marker itself not mutated accidentally by invalid clone. F03 exact shared30 cases (21marker+9authority), genuine brokerEffect and completedLocalUnknownCost entries not only helper, positive unmodified same seed reaches actual provider/effect or succeeds cost predicate; each mutated manifest fully hash-consistent except intended bound discrepancy must reject before provider/launch/new effects or ledger changes.',
        'Audit fixture honesty: TEMP BEFORE INSERT RAISE IGNORE only fresh fixture suppresses auto-created runtime dispatch; first consistent dispatch is inserted once, no update immutable historical row. UNKNOWN cost test uses explicitly synthetic append-only fixture effects; do not call it historical/native/live proof. Intent-cause assertions must distinguish intended validation failure from unrelated setup/hash/parse error. Provider is local fixture only, no actual model call.',
        'Trace original full A stage/adapter/preprepare/pretransport/verifier/cost/manifest creation consistency, immutable effective1/tool0 projection vs original provider identity, no fallback on malformed marker, legacy/ordinary normal config retains8/tools4 through actual Host wire and legacy brokerEffect, persistent profile/config/vendor8df/frozen worker bundle unchanged. Actual frozen worker positive in original A remains hashverified evidence if unchanged; repeat only unresolved relevant cases.',
        'Independently run appropriate focused regressions and true consumer controls/matrices from revised source, verify 176 includes subtests and 3package PASS from raw; no requirement to repeat unrelated failing full Mu session. Historical full-session base/candidate failure stays explicitly not proven, separate from bounded 8/4 positive wire. Record all test errors/skips and new findings. No unbounded whole-package reruns or arbitrary scratch Source overlays.',
        'Audit recorded9 native failures and capture gap ledger9 unpredeclared read-only commands including1rg error plus1recipe-parser failure. Do not backfill missing historical raw or treat later successful capture as original. Verify original525 accidental22formatter restorations and supplement limitations remain preserved; no need repeat unchanged broad audit. Preserve Root9/20/index and source candidate guards, allow Root3 shared checkpoint paths to advance with before.raw.',
        'Capture every new command recipe before execution, exact argv/cwd/env/raw/native exit; D task-specific temp roots. Do not retry prior policy-denied cleanup files. Freeze review.md/json+manifest, separate ACCEPTED/LIMITED_SOURCE_ACCEPTED/NOT_ACCEPTED with precise limits. Source only, no Main/package/actual/formal acceptance. If no actionable new findings and tests satisfy original scope with explicit limits, do not block merely for historical gaps already retained.',
    ],
    'formal_increment': 0,
}
new(O / 'qualification-projection-A-r2-independent-review-scope.json', scope)
old = list(cp['failure_counters'])
imports = []
for command in manifest['recorded_commands']:
    if command['native_exit'] != 0:
        imports.append(('20261015|qualification-A-r2-command-' + command['tag'], command, ref(A / (command['tag'] + '.command.json'))))
gap = read(A / 'capture-gap-ledger.json')
for ordinal, item in enumerate(gap['items'], 1):
    imports.append(('20261015|qualification-A-r2-capture-gap-' + str(ordinal), item, ref(A / 'capture-gap-ledger.json')))
imports.append(('20261015|qualification-A-r2-read11-parser-gap', {'detail': gap['other_preexecution_failure'], 'raw_not_claimed': True}, ref(A / 'capture-gap-ledger.json')))
for item in read(H / 'verifier-dependency-inputs01/root-read-diagnostics.json')['items']:
    imports.append(('20261015|root-verifier-dependency-map-diagnostic-' + str(item['ordinal']), item, ref(H / 'verifier-dependency-inputs01/root-read-diagnostics.json')))
imports.append(('20261015|root-A-r2-full-patch-scope-correction', {'kind': 'SOURCE_ARTIFACT_SCOPE_LIMITATION', 'detail': 'Author artifact named full4f diff is restricted to10r2paths; Root explicitly records limit and requires full candidate Git diff for combined Source review. No artifact overwritten and no Source drift.'}, ref(A / 'freeze_source.py')))
for origin, detail, evidence in imports:
    assert not any(item.get('origin_key') == origin for item in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'SOURCE_REVISION_FAILURE_OR_CAPTURE_DIAGNOSTIC_PRESERVED', 'detail': detail, 'evidence_ref': evidence, 'counter_reset': False})
assert cp['failure_counters'][:1607] == old
count = len(cp['failure_counters'])
new(O / 'source-artifact-verification.json', {'candidate_commit': CANDIDATE, 'tree': manifest['tree'], 'r2_exact_paths': paths, 'full_A_paths': git('diff', '--name-only', MAIN, CANDIDATE, cwd=W).decode().splitlines(), 'patch_scope_limit': 'Author r2-full-diff-from-4f binary patch contains only the10 r2changed paths; inherited original A paths must be reviewed from full candidate Git diff. Filename is not a claim of15path completeness.', 'recorded_commands_verified': len(manifest['recorded_commands']), 'source_author_test_report': manifest['targeted_test'], 'independent_acceptance': 'PENDING', 'resource_map_refs': resource_manifests, 'raw_historical_gaps_preserved': gap, 'formal_increment': 0})
resume = read(B / 'continuation-cp509/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v88', at=now, checkpoint_revision=510, ownership_revision=296, failure_records_preserved=count, qualification_projection_A_r2_candidate_ref=ref(A / 'source-manifest.revision02.json'), qualification_projection_A_r2_independent_scope_ref=ref(O / 'qualification-projection-A-r2-independent-review-scope.json'), verifier_dependency_resource_refs=resource_manifests, active_source_cards=['CP508 STOPanchor-r2 original19paths real2compiledgrantCLI E2E+SA01-15/S2cuts'], next_command='Independently review whole A-r2 f48fca candidate with true consumer30matrices/native regression/8-4wire and honest capture gaps. STOPanchor-r2 Source continues. Clease/F01 independent design review in parallel. B Source waits accepted A-r2; verifier exact332link/2145source/initializer syntax maps ready for separately scoped semantic audit, not proof. No actual DB/backup/stop/model/replay/newrequest/package/migration. Main4f/old20/indexempty/f3consumedUNKNOWN preserved. Formal0/42/all22open.')
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=510, expected_previous_revision=509, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp510=rr, qualification_projection_A_r2_candidate_ref=ref(A / 'source-manifest.revision02.json'), qualification_projection_A_r2_independent_scope_ref=ref(O / 'qualification-projection-A-r2-independent-review-scope.json'), verifier_dependency_resource_refs=resource_manifests)
cp['evidence_index'].append({'kind': 'A_R2_CANDIDATE_AND_HISTORICAL_VERIFIER_INPUT_MAPS_FROZEN_INDEPENDENT_A_REVIEW_REGISTERED', 'ref': rr, 'formal_increment': 0})
ow.update(revision=296, expected_previous_revision=295, updated_at=now, updated_by='codex:/root')
ow['special_paths']['qualification_projection_A'].update(state='REVISION02_FROZEN_PENDING_INDEPENDENT_REVIEW', evidence_ref=ref(A / 'source-manifest.revision02.json'))
ow['special_paths']['qualification_projection_A_revision02_independent_review'] = {'owner': scope['owner'], 'mode': scope['mode'], 'state': 'REGISTERED_AWAITING_AGENT_SLOT', 'scope_ref': ref(O / 'qualification-projection-A-r2-independent-review-scope.json'), 'write_scope': [scope['own_receipts']]}
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, before in raw.items():
    assert p.read_bytes() == before
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP510\n\nRead `' + rr['path'] + '` first. A-r2 f48fca frozen for independent Source review; STOPanchor-r2 construction and Clease/F01 design review continue. Verifier exact dependency/syntax input maps available but not semantic proof. Main4f/f3 consumedUNKNOWN preserved. Formal0/42/all22open; preserved records' + str(count) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 510, 'ownership': 296, 'failure_records': count, 'diagnostics_imported': len(imports), 'resume': rr, 'scope': ref(O / 'qualification-projection-A-r2-independent-review-scope.json')}))
