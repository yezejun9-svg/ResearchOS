import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp516'
E = R / 'execution/v2.4/receipts/W05/W05-99'
I = E / 'owned_core_stop_anchor_revision02_independent_review_codex/20261015-current-chat'
Q = E / 'qualification_recovery_boundary_decision_codex/20261015-current-chat'
BASE = 'f5db4a9639f1a50380eb5929ee6295887baeb756'


def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))


def ref(p):
    data = p.read_bytes()
    return {'path': p.relative_to(R).as_posix(), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def new(p, obj):
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')


def replace(p, before, after):
    assert p.read_bytes() == before
    tmp = p.with_name(p.name + '.cp516.pending')
    with tmp.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(tmp, p)


assert ref(I / 'evidence-manifest.json')['sha256'] == '7ddd9b31b7233ec7ca36c34fdb9a4a862a403ae95e0d00cf6f72b514b40e1022'
assert ref(Q / 'FINAL-manifest.json')['sha256'] == 'd41b69fd63b752ec011206fdd581e2a7fd45a7dfbb26e565b188565ab091203f'
for directory, filename, field, count in ((I, 'evidence-manifest.json', 'files', 671), (Q, 'FINAL-manifest.json', 'refs', 51)):
    entries = read(directory / filename)[field]
    assert len(entries) == count
    for item in entries:
        p = directory / item['path']
        assert p.resolve().is_relative_to(directory.resolve())
        actual = ref(p)
        assert actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes']
for item in read(Q / 'FINAL-manifest.json')['external_refs']:
    p = Path(item['path'])
    assert p.resolve().is_relative_to(R.resolve())
    actual = ref(p)
    assert actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes']
review = read(I / 'review.json')
assert review['verdict'] == 'NEEDS_CHANGES' and review['candidate'] == BASE and len(review['findings']) == 3
assert len(review['minimal_fix_source_paths']) == 6 and len(review['coverage_gaps']) == 5
decision = read(Q / 'boundary-decision.json')
assert decision['proposed_class_status'] == 'NOT_IMPLEMENTED_NOT_ACCEPTED' and not decision['actual_authority'] and not decision['current_executable_alternative']
cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 515 and ow['revision'] == 301 and len(cp['failure_counters']) == 1716
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R)
assert len(subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=R, text=True).splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']
O.mkdir(exist_ok=False)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O / 'recovery-boundary-adopted-limits.json', {'at': now, 'report_ref': ref(Q / 'FINAL-manifest.json'), 'root_decision': 'CONDITIONAL_DESIGN_DIRECTION_ONLY_NO_NEW_CLASS_ACCEPTANCE', 'proposed_class': decision['proposed_class'], 'status': 'NOT_IMPLEMENTED_NOT_ACCEPTED', 'mandatory_conditions': ['real installed old/current entry and auto-restart persistent fence before arm', 'online pre-witness cannot claim product-root lease', 'same-machine/SID/root immutable pre/post evidence and supported complete Restart observation', 'post-restart real exclusive lease/current census/own-operation permit', 'narrow Host/effect/B evidence and UNKNOWN cost unchanged'], 'historical_successful_wait': 'UNAVAILABLE_UNCHANGED', 'source_C_or_boundary_authority': False, 'user_restart_requested': False, 'actual_authority': False, 'formal_increment': 0})
allowed = review['minimal_fix_source_paths'] + [review['optional_existing_test_path_for_durable_crash_matrix']]
scope = {
    'schema': 'researchos.owned-core-stop-proof-revision03-source-card.v1', 'at': now,
    'owner': 'codex:/root/owned_core_stop_builder', 'model': 'gpt-6-sol', 'reasoning_effort': 'high',
    'model_choice_reason': 'Bounded seven-path repair of independently reproduced required-field proof hole plus exact cancellation/native ancestry defects and missing safety cuts',
    'base_commit': BASE, 'base_tree': review['tree'], 'base_status': 'NEEDS_CHANGES_NOT_ACCEPTED',
    'worktree': str(R / '.local/worktrees/owned-core-stop-proof-r3-20261015'), 'branch': 'codex/owned-core-stop-proof-r3-20261015',
    'own_receipts': str(E / 'owned_core_stop_proof_revision03_source_codex/20261015-current-chat'),
    'own_temporary_root': str(R / '.local/owned-core-stop-proof-r3-20261015-tmp'),
    'source_allowlist': allowed,
    'inputs': [ref(I / 'evidence-manifest.json'), ref(I / 'review.md'), ref(I / 'review.json'), ref(I / 'classified-author-nonzero.json'), ref(I / 'diagnostic-audit.json'), ref(B / 'continuation-cp508/owned-stop-anchor-revision02-source-scope.json')],
    'copied_findings': review['findings'], 'copied_coverage_gaps': review['coverage_gaps'],
    'requirements': [
        'Own NEW isolated worktree/branch from exact f5, do not edit frozen f5/56e/author/reviewer evidence. You are not alone: B Source is active; Root alone shared checkpoint/ownership/handoff. Exactly six source/test fix paths plus journal_windows_test.go for durable matrix. No other Source, CLI entry/default grant/proof class additions, Main/spec/Source25/current product/private config changes. If a necessary source primitive cannot fit these files, report exact narrow extra path before edit; keep other cuts moving.',
        'F01 presence-aware required numeric native fields for EACH worker_native_exit and verifier_native_exit receipt. Missing/null rejected; native_wait_result must explicitly equal WAIT_OBJECT_0; native_exit_code explicitly present legal uint32 including0/nonzero. Reject negative/overflow/fractional; values in another proof class do not satisfy this one. Preserve all original strict proof classes and raw native capture requirements. No grandfathering omitted0, fallback synthetic class, caller bool or authority bypass.',
        'F02 propagate caller context cancellation AND earlier deadline to retained native boundary; effective deadline=min(grant monotonic deadline, caller deadline), never extended. Check ctx plus grant wall/monotonic before intent and immediately after native pre-wait before TerminateProcess. If canceled/expired after durable intent, signal0 and operation consumed forever, outcome UNKNOWN/zero-signal as justified. After one signal keep finite wait/completion and no retry. Do not replace actual numeric native Wait with context/error text.',
        'F03 open/check/retain Core and parent image ancestor native handles inside existing supervisor file, with non-reparse identity/ACL/owner boundary and deny write/delete semantics or proved equivalently strong primitive across check/open/action. Hash/ID from same final retained image handle; close ancestor handles in reverse only at ownedNativeProcess close. EvalSymlinks followed by path reopen alone is insufficient. Cover actual supervisor image paths, not only authority heldDocuments. No broad ACL permission relaxation, copied-image or hardlink fallback.',
        'Implement every required test listed in copied F01..03 and close copied COV01..05 with meaningful evidence. F01 worker/verifier missing/null/explicit0/nonzero and wait missing/null/nonzero/0, numeric malformed and cross-class tests. Re-run independent bad-receipt scenario with fresh true compiled grant CLI; earliest legitimate preflight rejection is correct and should stop the scenario, no fictitious second STOP grant after refused preflight. Normal fresh two-compiled-grant/nonempty SQLite positive still passes. Wrong parent/Host/Owner/SID bindings zero signal; distinguish wrong expected SID from genuinely foreign-user process if only former fixture available.',
        'F02 actual ctx already canceled/earlier deadline, cancellation after intent flush and after native pre-wait zero signal; permanent consumed intent denies reentry across independently invoked binaries; grant expiry after intent zero signal. F03 retained ancestor swap/reparse/write sharing/hardlink tests; use fresh task-owned junction fallback if symlink privilege unavailable, preserve initial skips/failures honestly. No current product/native process touched.',
        'COV01 permanent consumption requires real CLI reentry from all reachable claim/BEGIN/intent/post-call and torn/missing-required states, third-grant substitution, preflight reset and concurrent phases. Own fixture may seed explicit synthetic crash-state images if exact reachable grammar/hash/operation is preserved; label state injection as such, not an actually crashed process. Add actual killed grant-aware CLI coverage only when deterministic and warranted; never introduce a production approval or crash bypass just to make tests pass. Distinguish hardware/durability assumptions. COV04 full S209 dangerous-state inventory through true CLI Commit with valid predecessor and own fixture mutations; COV05 bounded malformed compiled-grant/CLI zero observable action matrix, with source/unit evidence for forbidden open/setup boundaries. Do not treat no-tests-to-run/skipped/unexecuted cuts as PASS.',
        'All own shell commands recipe/argv/cwd/relevantenv BEFORE execution, full raw stdout/stderr/native exit and failures/skips/gaps, explicit classification expected denial vs actual error. Use own new E copies of prior fixture/run_logger as needed, pin original/derived helper hashes and exact diffs; point worktree/cache/tmp/programs only to this task. Rebuild own fixture and real two grant binaries from revised Source, no old artifact overwrite, no actual model/Ollama/private signer/current DB/OS state probes. Source changes via explicit allowed paths; gofmt only allowed paths; local atomic explicit-path commit allowed with maintenance.auto=false/gc.auto=0.',
        'Freeze candidate clean commit/tree, source file hashes, full combined19path binarypatch from Main4f plus exact r3delta fromf5, claim-to-test map including all copied COV gaps, raw command/failure/capture-gap ledger and manifest. Preserve f5 rejection and 63 classified historical records(54expected/9errors), no duplicate3harness summaries or resets. Root independent astra review required before Source/Main/package/actual acceptance. Proposed boot recovery class is a separate NOT_IMPLEMENTED_NOT_ACCEPTED direction and is OUTSIDE this card. Formal0/42/all22open.',
    ], 'formal_increment': 0, 'actual_authority': False,
}
new(O / 'owned-core-stop-proof-revision03-source-scope.json', scope)
diag = read(I / 'diagnostic-audit.json')
old = list(cp['failure_counters'])
items = [('stop-review-native-record-' + str(i), 'INDEPENDENT_REVIEW_MIXED_NONZERO_RECORD_PRESERVED', item, ref(I / 'diagnostic-audit.json')) for i, item in enumerate(diag['own_nonzero'], 1)]
assert len(items) == 7
for i in range(4):
    items.append(('stop-review-gap-' + str(i + 1), 'INDEPENDENT_REVIEW_DIAGNOSTIC_PRESERVED', diag['own_gaps_and_corrections'][i], ref(I / 'diagnostic-audit.json')))
items.append(('stop-review-draft-correction', 'INDEPENDENT_REVIEW_DIAGNOSTIC_PRESERVED', {'detail': diag['own_gaps_and_corrections'][4], 'native_abort_already_recorded': True, 'new_record_only_for_prior_draft_misdescription': True}, ref(I / 'diagnostic-audit.json')))
for item in review['findings']:
    items.append(('stop-review-finding-' + item['id'], 'INDEPENDENT_SOURCE_REVIEW_FINDING_PRESERVED', item, ref(I / 'review.json')))
qd = read(Q / 'diagnostic-ledger.json')['items']
q_by_id = {item['id']: item for item in qd}
for key in ['D01', 'D02', 'D05']:
    items.append(('boundary-decision-' + key, 'READONLY_ARCHITECTURE_DIAGNOSTIC_PRESERVED', q_by_id[key], ref(Q / 'diagnostic-ledger.json')))
for i in range(2):
    items.append(('boundary-web-capture-order-' + str(i + 1), 'READONLY_ARCHITECTURE_CAPTURE_ORDER_LIMIT', {'tool_call': ['Q3', 'Q5'][i], 'detail': q_by_id['D03']}, ref(Q / 'diagnostic-ledger.json')))
for i in range(2):
    items.append(('boundary-admin-reread-gap-' + str(i + 1), 'READONLY_ARCHITECTURE_CAPTURE_GAP', {'tool_chunk': ['7a0e0f', '4bc104'][i], 'detail': q_by_id['D07']}, ref(Q / 'diagnostic-ledger.json')))
assert len(items) == 22
for suffix, status, detail, evidence_ref in items:
    origin = '20261015|cp516-' + suffix
    assert not any(v.get('origin_key') == origin for v in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': status, 'detail': detail, 'evidence_ref': evidence_ref, 'counter_reset': False})
assert cp['failure_counters'][:1716] == old and len(cp['failure_counters']) == 1738
new(O / 'author-nonzero-classification-adopted.json', {'classified_ref': ref(I / 'classified-author-nonzero.json'), 'raw_records_already_preserved_cp514': 63, 'expected_denial_or_blocked': 54, 'actual_error_records': 9, 'new_author_failure_counter_records': 0, 'old_records_unchanged': True, 'three_harness_summaries_additional_records': 0})
resume = read(B / 'continuation-cp515/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v94', at=now, checkpoint_revision=516, ownership_revision=302, failure_records_preserved=len(cp['failure_counters']), owned_stop_r2_independent_ref=ref(I / 'evidence-manifest.json'), owned_stop_r2_independent_status=review['verdict'], owned_stop_r3_source_scope_ref=ref(O / 'owned-core-stop-proof-revision03-source-scope.json'), recovery_boundary_decision_ref=ref(Q / 'FINAL-manifest.json'), recovery_boundary_adopted_limits_ref=ref(O / 'recovery-boundary-adopted-limits.json'), active_source_cards=['CP512 B exact9 ONLINE failure proof/transactions/tests', 'CP516 STOP-r3 exact7 F01requirednativefields/F02ctxdeadline/F03imageancestry+cuts'])
resume['next_command'] = 'Implement STOP-r3 newisolatedexact7 from rejectedf5; B Source/nativeB01passed authoronly/negative+rollbackmatrices running. Stopr2rejected3findings/5coveragegaps preserved,63authornonzero classified54expected9errors no recount. Bounded recovery decision conditionalfutureRestart+realinstalledentrypersistentfence only, NOT_IMPLEMENTED_NOT_ACCEPTED,noSourceC/boundary/actual authority,noUserRestartrequested. Main4f/protected9/dirty20/indexempty/originalRunUNKNOWN/rawACK/cost/processes unchanged. Formal0/42/all22open.'
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=516, expected_previous_revision=515, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp516=rr, owned_stop_r2_independent_ref=ref(I / 'evidence-manifest.json'), owned_stop_r3_source_scope_ref=ref(O / 'owned-core-stop-proof-revision03-source-scope.json'), recovery_boundary_decision_ref=ref(Q / 'FINAL-manifest.json'))
cp['evidence_index'].append({'kind': 'STOP_R2_REJECTED_R3_SOURCE_REGISTERED_CONDITIONAL_BOUNDARY_DIRECTION_ONLY', 'ref': rr, 'formal_increment': 0})
ow.update(revision=302, expected_previous_revision=301, updated_at=now, updated_by='codex:/root')
ow['special_paths']['owned_stop_r2_independent_review'].update(state='FROZEN_NEEDS_CHANGES', evidence_ref=ref(I / 'evidence-manifest.json'))
ow['special_paths']['owned_stop_r3_source'] = {'owner': scope['owner'], 'mode': 'SOURCE_IMPLEMENTATION_ISOLATED', 'state': 'REGISTERED', 'scope_ref': ref(O / 'owned-core-stop-proof-revision03-source-scope.json'), 'write_scope': [scope['worktree'], scope['own_receipts'], scope['own_temporary_root']], 'source_allowlist': allowed, 'actual_authority': False}
ow['special_paths']['qualification_recovery_boundary_decision'].update(state='FROZEN_CONDITIONAL_DESIGN_NOT_CLASS_ACCEPTANCE', evidence_ref=ref(Q / 'FINAL-manifest.json'))
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, data in raw.items():
    assert p.read_bytes() == data
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP516\n\nRead `' + rr['path'] + '` first. STOP-r2 rejected; STOP-r3 exact7 and B exact9 active Source cards. Conditional future Restart boundary only, no SourceC/boundary/actual authority or user Restart request. Formal0/42/all22open; preserved mixed records' + str(len(cp['failure_counters'])) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 516, 'ownership': 302, 'preserved_mixed_records': len(cp['failure_counters']), 'resume': rr, 'source_scope': ref(O / 'owned-core-stop-proof-revision03-source-scope.json'), 'stop_review_files': 671, 'boundary_local_refs': 51, 'boundary_external_refs': 17}))
