import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp509'
E = R / 'execution/v2.4/receipts/W05/W05-99'
A = E / 'qualification_failure_revision03_architecture_codex/20261015-current-chat'
I = E / 'qualification_failure_revision02_independent_review_codex/20261015-current-chat'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}


def new(p, value):
    with p.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.write('\n')


def replace(p, before, after):
    assert p.read_bytes() == before
    temporary = p.with_name(p.name + '.cp509.pending')
    with temporary.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(temporary, p)


assert len(sys.argv) == 2 and len(sys.argv[1]) == 64
assert ref(A / 'FINAL-manifest.json')['sha256'] == sys.argv[1]
manifest = read(A / 'FINAL-manifest.json')
for item in manifest['entries']:
    p = A / item['path']
    assert p.parent == A
    assert p.stat().st_size == item['bytes']
    assert hashlib.sha256(p.read_bytes()).hexdigest() == item['sha256']
assert manifest['actual_actions'] == 0 and manifest['source_writes'] == 0
pins = {
    'C-lease-addendum.md': 'a43287db0e89954baa1fc7b393adeaf41b730a97049d804b9d843d97facb76dd',
    'C-lease-exact-scope.json': 'ef69f8dcd63578f3692439b95f5ba21c155aeb75bc362bc9a52c65f4352f78b3',
    'C-lease-test-cuts.json': 'df37740b6057be0438adc14b56953d84ff46e9c9c7f5cd646fa55302cfc3223f',
}
for name, digest in pins.items():
    assert ref(A / name)['sha256'] == digest

cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 508 and ow['revision'] == 294
assert len(cp['failure_counters']) == 1595
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R)
assert len(subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=R, text=True).splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
O.mkdir(exist_ok=False)
scope = {
    'schema': 'researchos.C-lease-and-historical-claims-independent-review.v1',
    'at': now,
    'owner': 'codex:/root/qualification_failure_arch_review',
    'model': 'gpt-6-astra',
    'reasoning_effort': 'high',
    'model_choice_reason': 'Independent review of exact maintenance lease capability and historical FAILED-only proof classification before Source authority',
    'mode': 'READONLY_DESIGN_AND_PROOF_REVIEW_ONLY',
    'base_commit': '4f4023c956f84d65743f39ce77d6c8899a21ada1',
    'own_receipts': str(E / 'qualification_failure_revision03_independent_review_codex/20261015-current-chat'),
    'input_refs': [ref(A / 'FINAL-manifest.json'), ref(I / 'FINAL-manifest.json'), ref(I / 'C-minimal-addendum.json'), ref(I / 'STOP-alternative-proof-prerequisites.json'), ref(B / 'continuation-cp508/owned-stop-anchor-revision02-source-scope.json')],
    'requirements': [
        'Verify all frozen revision03 manifest members, C lease three files, F01 claims and proposed tests; read original revision02 C/private five-version transaction and independent findings. Review only the new C lease and F01 proof classes. STOP anchor direction already independently reviewed with mandatory SA-D01..05 copied into CP508 Source scope; do not redesign or re-review that unchanged anchor.',
        'No Source/shared state/current DB/OS/model/GUI/backups/process/private key/private pipe actions. You are not alone: A-r2 and STOP-anchor-r2 builders own isolated Source cards. Own new evidence directory only, each command recipe before execution with raw stdout/stderr/native exit; preserve every failure/capture gap honestly. Formal increment0, no actual or Source acceptance from design review.',
        'C: check one native lock owner, central acquisition of both journal namespaces, exact own-operation inspection permit and no cross-namespace exemption; private unforgeable generation-bound borrow, copying/release/concurrent borrow/Close behavior; domain dependency/import cycle and strict replacement grammar equivalence; direct public APIs fail closed and typed adapter rechecks journals itself. No callback, bool, JSON approval or raw handle as authority.',
        'Trace all five backup upgrade choices, prepared local/handoff nesting and source normalization identity, create/export, legacy release_host before Canary, disposable control bootstrap/resume and Core handoff, inherited recovery/migration token checks, fixture replay, normal startup, replacement and C early maintenance. Decide if exact allowlist covers every required entry and whether additional path is indispensable. New input parsing/validation must precede secret/protected/template/store work. Current C design is not Source authority and may proceed independently of blocked historical actual proof.',
        'F01: decide separately supported exact Host first-gate TOOL non-dispatch and unsupported universal OS NO_EFFECT. Verify claim provenance/source identity, raw three-frame/ACK2 classification, confirmed MODEL versus UNKNOWN monetary cost, actual B private drain ticket versus reconstructed historical quiescence. Raw queue_empty remains false; any derived FAILED-only classification must be separately justified, cannot weaken generic Finalize/Observation or write invented raw ACK/join.',
        'Review proposed HISTORICAL_NATIVE_JOB_ACCOUNTING_CLOSURE_V1 against exact recorded receipt plus pinned sandbox/bridge/coordinator source. Distinguish OS ActiveProcesses0 record/source inference/current future owner lock from raw WAIT result. Review Host Job/token-not-transferred narrow claim and preserve current NEVER_JOB_AUTHORIZED operational NOT_PROVABLE because complete init/background closure is absent. No original verifier native closure can be inferred from PID absence or defer cmd.Wait being called.',
        'Decide exact additional Source prerequisites or invariants needed to support FAILED-only without universal OS claim, preserving all old Task/request consumption/effects/ledger/budget/NoProgress/schema/qualification/raw history and exact five-version write set. Return minimal mandatory addendum or NOT_PROVABLE per branch. No new grant, old request replay, fake B receipt, execution/settlement/acceptance proof, or actual STOP authorization. B Source must be real and independently accepted before D; current actual STOP remains unavailable.',
        'Deliver immutable review.md/review.json with separate C lease/F01/worker/verifier verdicts, precise mandatory addenda and exact path changes if any, source refs/diagnostic ledger and evidence manifest. Do not expand this task into transitive verifier initializer audit or run fresh verifier/model. That missing proof can be a separately scoped read-only branch.',
    ],
    'formal_increment': 0,
}
new(O / 'C-lease-F01-independent-review-scope.json', scope)
old = list(cp['failure_counters'])
imports = []
for ordinal, line in enumerate((A / 'diagnostics.jsonl').read_text(encoding='utf8').splitlines(), 1):
    if not line.strip():
        continue
    origin = '20261015|qualification-failure-revision03-author-diagnostic-' + str(ordinal)
    assert not any(item.get('origin_key') == origin for item in old)
    detail = json.loads(line)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'DESIGN_OR_READ_DIAGNOSTIC_PRESERVED', 'detail': detail, 'evidence_ref': ref(A / 'diagnostics.jsonl'), 'counter_reset': False})
    imports.append(origin)
assert cp['failure_counters'][:1595] == old
count = len(cp['failure_counters'])
resume = read(B / 'continuation-cp508/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v87', at=now, checkpoint_revision=509, ownership_revision=295, failure_records_preserved=count, qualification_failure_revision03_design_ref=ref(A / 'FINAL-manifest.json'), C_lease_F01_independent_review_scope_ref=ref(O / 'C-lease-F01-independent-review-scope.json'), next_command='Continue isolated A-r2 and STOPanchor-r2 Source cards; register and run bounded independent C single-lease and F01 narrow historical proof classification review. Actual STOP unavailable and full historical NO_EFFECT/verifier operational substitute NOT_PROVABLE. No actual DB/backup/stop/model/replay/newrequest/package/migration. Main4f/protected9/old20/indexempty/f3consumedUNKNOWN preserved. Formal0/42/all22open.')
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=509, expected_previous_revision=508, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp509=rr, qualification_failure_revision03_design_ref=ref(A / 'FINAL-manifest.json'), C_lease_F01_independent_review_scope_ref=ref(O / 'C-lease-F01-independent-review-scope.json'))
cp['evidence_index'].append({'kind': 'C_SINGLE_NATIVE_LEASE_AND_F01_NARROW_CLAIMS_FROZEN_INDEPENDENT_REVIEW_REGISTERED', 'ref': rr, 'formal_increment': 0})
ow.update(revision=295, expected_previous_revision=294, updated_at=now, updated_by='codex:/root')
ow['special_paths']['qualification_failure_revision03_design'].update(state='FROZEN_DESIGN_AND_READONLY_ANALYSIS', evidence_ref=ref(A / 'FINAL-manifest.json'))
ow['special_paths']['C_lease_F01_independent_review'] = {'owner': scope['owner'], 'mode': scope['mode'], 'state': 'REGISTERED_AWAITING_AGENT_SLOT', 'scope_ref': ref(O / 'C-lease-F01-independent-review-scope.json'), 'write_scope': [scope['own_receipts']]}
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, before in raw.items():
    assert p.read_bytes() == before
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP509\n\nRead `' + rr['path'] + '` first. C lease and narrow historical claims frozen for independent review; actual STOP unavailable/verifier operational substitute NOT_PROVABLE. Two isolated Source cards continue. Main4f/f3 consumedUNKNOWN preserved. Formal0/42/all22open; preserved records' + str(count) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 509, 'ownership': 295, 'failure_records': count, 'diagnostics_imported': len(imports), 'resume': rr, 'scope': ref(O / 'C-lease-F01-independent-review-scope.json')}))
