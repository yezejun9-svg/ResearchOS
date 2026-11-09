import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp512'
E = R / 'execution/v2.4/receipts/W05/W05-99'
I = E / 'qualification_projection_a_revision02_independent_review_codex/20261015-current-chat'
A = E / 'qualification_failure_revision02_architecture_codex/20261015-current-chat'
N = E / 'qualification_failure_revision03_independent_review_codex/20261015-current-chat'
BASE = 'f48fca0e4013bda19913a34d91da0cd23157a08b'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    data = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def new(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def replace(p, before, after):
    assert p.read_bytes() == before
    temporary = p.with_name(p.name + '.cp512.pending')
    with temporary.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(temporary, p)


assert ref(I / 'evidence-manifest.json')['sha256'] == '319c2c8a86585ea5daa587fbdbb7df75ba321c367f8b172fc32f49cb3944f1fe'
for item in read(I / 'evidence-manifest.json')['files']:
    p = I / item['path']
    assert p.parent == I and ref(p)['sha256'] == item['sha256'] and p.stat().st_size == item['bytes']
review = read(I / 'review.json')
assert review['verdict'] == 'LIMITED_SOURCE_ACCEPTED' and review['candidate_commit'] == BASE and not review['actionable_findings']
pins = {'B-ARCHITECTURE.md': 'db4d9bc604429b8e326a724f5d51a719332fa16359b1eda3b4313868b79f9324', 'B-exact-scope.json': '45fdb7a350cdc620fc7520c969092484438fe7ab0a53782563655c18b379547b', 'B-test-cuts.json': '0a6edc0873e6f5fac8cebbf73e2c79a9b4461f628625e5d35abf74ec536f48b0'}
for name, digest in pins.items():
    assert ref(A / name)['sha256'] == digest
design_scope = read(A / 'B-exact-scope.json')
cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 511 and ow['revision'] == 297 and len(cp['failure_counters']) == 1639
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R)
assert len(subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=R, text=True).splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']
assert subprocess.check_output(['git', 'rev-parse', BASE + '^{tree}'], cwd=R, text=True).strip() == '16e72ccf939c13142091495458ad04348a3ba660'

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
O.mkdir(exist_ok=False)
scope = {
    'schema': 'researchos.qualification-failure-B-source-card.v1',
    'at': now,
    'owner': 'codex:/root/qualification_projection_builder',
    'model': 'gpt-6-sol',
    'reasoning_effort': 'high',
    'model_choice_reason': 'Bounded9path implementation of independently reviewed online first-gate failure proof and private drain/transaction consumer, reusing accepted A binding knowledge',
    'base_commit': BASE,
    'base_tree': review['candidate_tree'],
    'worktree': str(R / '.local/worktrees/qualification-failure-b-20261015'),
    'branch': 'codex/qualification-failure-b-20261015',
    'own_receipts': str(E / 'qualification_failure_b_source_codex/20261015-current-chat'),
    'accepted_A_ref': ref(I / 'evidence-manifest.json'),
    'design_refs': [ref(A / name) for name in pins],
    'independent_design_ref': ref(E / 'qualification_failure_revision02_independent_review_codex/20261015-current-chat/FINAL-manifest.json'),
    'C_write_shape_ref': ref(A / 'C-ARCHITECTURE.md'),
    'current_classification_review_ref': ref(N / 'FINAL-manifest.json'),
    'allowed_existing_source': design_scope['production_existing'],
    'allowed_new_source': design_scope['production_new'],
    'allowed_tests': design_scope['tests_allowed'],
    'requirements': [
        'Own NEW isolated worktree/branch from exact accepted A-r2 f48, no edit original525/f48 candidate or Main. You are not alone: STOPanchor-r2 author and readonly verifier startup semantic audit in parallel; Root alone edits shared checkpoint/ownership/handoff. Exactly4existing+2newproduction+3tests, no other Source. New E task receipts and new unique D temp/cache permitted. No original actual data/DB/Core54076/Desktop69996/Ollama/profile/config/package/GUI/model/old target two files/Source25/spec changes. Git writes explicitpaths only with maintenance.auto=false/gc.auto=0.',
        'Implement complete frozen B architecture/testcuts with real production wiring. Typed ONLINE_FIRST_GATE_TOOL_DENIAL constructor ONLY first brokerEffect dispatchGate transaction before providerRoute/prepareEffectTx, exact actual qualification Task/plan/admission/marker/profile/technical/route/credential bounds/frame3 TOOL/key/raw/payload hashes, zero history across all rejected-key effect/ledger stages. Known model route used in forbidden TOOL differs from unknown route. Any malformed request or second gate remains generic UNKNOWN; no conversion by error text or caller bool. Hold resourceWriteLock serialization, create-new strict private immutable receipt flush before propagating typed error; persistence failures remain UNKNOWN.',
        'Per-dispatch admission+completion registry with one mutex and private broker drain ticket. On typed denial close admission, cancel dedicated broker context and bridge, consume/join every admitted broker exactly once; retain first cause and disqualify extra suffix/frame/unknown duplicate completion. All broker goroutines must use owned cancel context. Bounded timeout never yields closed ticket; worker exit alone insufficient. Generic paths cancel/join where possible and keep UNKNOWN on unresolved work. Cancel heartbeat and await completion before terminal CAS. No new ACK after rejection, no invented ACK3 or historical goroutine join.',
        'Runtime adapter provides bounded source-bound facts only, generic Bridge.Finalize/Journal.Observation ACK equality unchanged. Domain private verifier accepts native stopped/drained/cleanup/output facts plus exact raw3/ACK2/rejected1 census, confirmed sole MODEL receipt/effect binding, no other effect/queue/control/checkpoint, UNKNOWN monetary ledger preserved under current accounting policy. Failure type concerns Host broker non-dispatch; do not claim universal OS NO_EFFECT. Derived FAILED-only classification is separate from raw queue_empty=false and cannot change raw protocol, ACKs, artifacts, exit124/timedout/cancel facts or native ended time.',
        'Implement real private validatedQualificationFailureTx and private variant/types in B new domain file; B initially supports ONLINE_FIRST_GATE_TOOL_DENIAL only, no fake historical C constructor or D production stub. Validated consumer loads terminalRun/qualification marker/plan/idempotency/uploaded sealed bytes/artifact version/observation; recomputes subject/hash/author/currentOwner-root bindings and rejects zero value/callerJSON/ref forgery/revocation. D later calls this actual implementation, but do not implement D now.',
        'FAILED-only apply transaction uses deterministic planned facts and stable host:qualification-failure-closure run/epoch/denialdigest key. Reuse C revision02 exact ordinary schema24 shape: Run and ProjectState versions + new GENERATED/LIVE/PROJECT MANIFEST run_idnull/ImpactLink/EventEnvelope, one uploaded_content sealed row and exact enumerated ancillary refs/observation/idempotency; runtime_uploads/artifact_uses/artifact_use_proofs0. Produced_by actual authenticated Host scheduler principal with scoped project grant/currentOwner-root, not old executor. Current online path may allocate its plan once then freeze it before transaction. Validate actual immutable schemas and s.put invariants, atomic rollback/CAS/replay0delta. Never reportRun/projectSessionRun/accept/settle or change Task/active_run_id/request consumption/effects/ledger/budget/NoProgress/lease/qualification/schema/native outputs.',
        'B01-B12 all concrete positive/negative cuts required, especially real first-gate known-route denial after MODEL, actual native closed worker and host drain, blocked/late broker completion and heartbeat race, malformed/unknown/secondgate/persistence failures, every transactional write rollback, completed marker replay, ordinary coding/tool generic behavior, and forged/private helper consumer. Fixtures can synthesize fresh isolated input/domain states with honest provenance but cannot supply production approval bool/test registry or fabricate native observations as real OS proof. If native B01 cannot use a valid fixture under accepted A marker, report exact missing resource/scope before editing outside9; keep other cuts progressing. No missing/zero assertions counted PASS.',
        'Every command recipe/argv/cwd/relevantenv must be written BEFORE execution; full raw stdout/stderr/native exit/fails/skips and any capture gap honest. Gofmt only explicit allowed paths. Run meaningful focused Windows regression/build with local fixture provider, no actual model/Ollama. Avoid unrelated known fullMu historical failures and broad package reruns unless new concern. Current worker bundle2a8/profile/vendorSDK8df persistent binding bytes unchanged. Preserve all original failed attempts; no reusing prior denied cleanup path or deletion workaround.',
        'Freeze exact commit/tree/cleanworktree, whole Bdiff binarypatch fromf48 including allchangedpaths, per-source hash, test-cut mapping, command/failure/gap ledger/guards and manifest. Do not label path-restricted patch as full combined patch. Local atomic explicit-path commit permitted. Source only author report, independent astra review required before acceptance/Main/package/actual. Formal increment0/all22open.',
    ],
    'formal_increment': 0,
}
new(O / 'qualification-failure-B-source-scope.json', scope)
old = list(cp['failure_counters'])
items = read(I / 'diagnostic-audit.json')['reviewer_new_diagnostics']
for ordinal, item in enumerate(items, 1):
    origin = '20261015|qualification-A-r2-independent-diagnostic-' + str(ordinal)
    assert not any(entry.get('origin_key') == origin for entry in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'INDEPENDENT_SOURCE_REVIEW_DIAGNOSTIC_PRESERVED', 'detail': item, 'evidence_ref': ref(I / 'diagnostic-audit.json'), 'counter_reset': False})
root_diag = {'tool_chunk': '3040b5', 'native_exit': 0, 'kind': 'ROOT_OVERSIZED_A_REVIEW_DIAGNOSTIC_DISPLAY', 'detail': 'Read diagnostic-audit plus entire successful-command ledger caused display truncation. Required three reviewer diagnostics are in fully preserved frozen diagnostic-audit.json; no original full ledger display capture claimed.'}
new(O / 'root-read-diagnostic.json', root_diag)
cp['failure_counters'].append({'origin_key': '20261015|root-cp512-oversized-diagnostic-display', 'attempts': 1, 'status': 'READ_DIAGNOSTIC_PRESERVED', 'detail': root_diag, 'evidence_ref': ref(O / 'root-read-diagnostic.json'), 'counter_reset': False})
assert cp['failure_counters'][:1639] == old and len(items) == 3
count = len(cp['failure_counters'])
resume = read(B / 'continuation-cp511/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v90', at=now, checkpoint_revision=512, ownership_revision=298, failure_records_preserved=count, qualification_projection_A_r2_independent_ref=ref(I / 'evidence-manifest.json'), qualification_projection_A_r2_independent_status=review['verdict'], qualification_failure_B_source_scope_ref=ref(O / 'qualification-failure-B-source-scope.json'), active_source_cards=['CP508 STOPanchor-r2 real2compiledgrantCLI E2E+SA01-15/S2cuts', 'CP512 B onlinefirstgate/drain/FAILEDprivateconsumer exact9 paths fromacceptedA-r2f48'], next_command='Implement exact9 B Source from accepted A-r2f48, true firstgate/drain/native FAILED-only privateproof/consumer with B01-12; STOPanchor-r2 realpositiveCLI done authoronly, remainingnegatives/freeze/independentreview pending. Readonly exactverifier init semantics audit parallel. Cdesignmandatoryaddenda adopted, actualSTOP/C still unavailable and noactual authority. Main4f/old20/indexempty/f3consumedUNKNOWN unchanged; noactual DB/backup/stop/model/replay/newrequest/package/migration. Formal0/42/all22open.')
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=512, expected_previous_revision=511, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp512=rr, qualification_projection_A_r2_independent_ref=ref(I / 'evidence-manifest.json'), qualification_failure_B_source_scope_ref=ref(O / 'qualification-failure-B-source-scope.json'))
cp['evidence_index'].append({'kind': 'A_R2_LIMITED_SOURCE_ACCEPTED_B_ONLINE_FAILURE_SOURCE_REGISTERED', 'ref': rr, 'formal_increment': 0})
ow.update(revision=298, expected_previous_revision=297, updated_at=now, updated_by='codex:/root')
ow['special_paths']['qualification_projection_A'].update(state='REVISION02_LIMITED_SOURCE_ACCEPTED_NOT_MAIN', evidence_ref=ref(I / 'evidence-manifest.json'))
ow['special_paths']['qualification_projection_A_revision02_independent_review'].update(state='FROZEN_LIMITED_SOURCE_ACCEPTED', evidence_ref=ref(I / 'evidence-manifest.json'))
ow['special_paths']['qualification_failure_B_source'] = {'owner': scope['owner'], 'mode': 'SOURCE_IMPLEMENTATION_ISOLATED', 'state': 'REGISTERED', 'scope_ref': ref(O / 'qualification-failure-B-source-scope.json'), 'write_scope': [scope['worktree'], scope['own_receipts']], 'source_allowlist': scope['allowed_existing_source'] + scope['allowed_new_source'] + scope['allowed_tests']}
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, before in raw.items():
    assert p.read_bytes() == before
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP512\n\nRead `' + rr['path'] + '` first. A-r2 independently LIMITED_SOURCE_ACCEPTED; exact9 B Source registered fromf48. STOPanchor-r2 plusB are two activeSource cards. Verifier init semantic audit readonly. Current actual STOP/C unavailable; Main4f/f3 consumedUNKNOWN preserved. Formal0/42/all22open; preserved records' + str(count) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 512, 'ownership': 298, 'failure_records': count, 'diagnostics_imported': len(items) + 1, 'resume': rr, 'scope': ref(O / 'qualification-failure-B-source-scope.json')}))
