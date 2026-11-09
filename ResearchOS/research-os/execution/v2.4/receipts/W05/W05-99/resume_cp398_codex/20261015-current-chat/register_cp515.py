import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp515'
E = R / 'execution/v2.4/receipts/W05/W05-99'
A = E / 'historical_verifier_initialization_authority_audit_codex/20261015-current-chat'


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
    tmp = p.with_name(p.name + '.cp515.pending')
    with tmp.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(tmp, p)


assert ref(A / 'FINAL-manifest.json')['sha256'] == 'cd0f09b75b65d3446d7a0374ed838d3823dc5f7d501fdfc61964bc3575c450d7'
audit_manifest = read(A / 'FINAL-manifest.json')
assert audit_manifest['file_count'] == len(audit_manifest['files']) == 151
for item in audit_manifest['files']:
    p = A / item['path']
    assert p.resolve().is_relative_to(A.resolve())
    actual = ref(p)
    assert actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes']
audit = read(A / 'audit.json')
assert audit['decision'] == 'NOT_PROVABLE_NO_NEW_OPERATIONAL_CLASS' and audit['proposed_operational_class'] is None
assert audit['source_edits'] == audit['actual_database_opens'] == audit['current_os_process_probes'] == audit['model_calls'] == audit['product_executions'] == 0
cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 514 and ow['revision'] == 300 and len(cp['failure_counters']) == 1709
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R)
assert len(subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=R, text=True).splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']
O.mkdir(exist_ok=False)
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
new(O / 'audit-adopted-limits.json', {'at': now, 'audit_ref': ref(A / 'FINAL-manifest.json'), 'resource_refs_verified': 151, 'root_decision': 'ADOPT_NONOPERATIVE_NEGATIVE_FINDING_ONLY', 'effect': 'Current material cannot establish historical original verifier successful native closure; no new operational class and no actual STOP/C authority. Broad init search stops. Full semantic acceptance is not asserted.', 'preserved': ['original RunUNKNOWN and raw3/ACK2 facts', 'existing strict native proof classes', 'failure counters', 'all source and actual processes'], 'formal_increment': 0})
scope = {
    'schema': 'researchos.qualification-recovery-boundary-decision-scope.v1', 'at': now,
    'owner': 'codex:/root/verifier_revision_review', 'model': 'gpt-6-astra', 'reasoning_effort': 'high',
    'model_choice_reason': 'Bounded architecture decision on an explicit new recovery boundary after historical fact is known unavailable; reuses exact audit context without another transitive initializer audit',
    'own_receipts': str(E / 'qualification_recovery_boundary_decision_codex/20261015-current-chat'),
    'base_main': '4f4023c956f84d65743f39ce77d6c8899a21ada1',
    'inputs': [ref(A / 'FINAL-manifest.json'), ref(A / 'audit.md'), ref(A / 'residual-matrix.json'), ref(O / 'audit-adopted-limits.json'), ref(B / 'continuation-cp514/owned-core-stop-source-r2-independent-review-scope.json'), ref(E / 'qualification_failure_revision03_independent_review_codex/20261015-current-chat/FINAL-manifest.json'), ref(B / 'continuation-cp511/C-design-adopted-constraints.json')],
    'question': 'Historical original verifier successful Wait is unavailable. Does any explicit current recovery boundary safely satisfy the actual specification without claiming that historical Wait succeeded, or must a concrete user/resource decision remain? Give one finite recommendation or exact blocker.',
    'candidate_options': [
        'Separately scoped CORE-ONLY quiesce: exact owned Core identity, existing backup/census/exclusive SQLite barrier, durable one-shot intent, one native terminate and original-handle numeric wait, outcome explicitly maintenance-unproven. Only after Core is closed, a complete native current-process/image/descendant census under a defined no-new-launch fence may or may not establish current execution closure. Existing unknown verifier is not killed or reported historically waited. Assess census completeness, error paths, image/parent identity and race limits; do not assume sufficiency.',
        'A later observed OS boot boundary, if it can be strongly bound and is contract compatible, may establish current absence of all prior-boot execution while leaving old Wait unknown. Requires future concrete implementation/review and explicit user action; no reboot is authorized now. Assess what prior boot/creation facts are actually available, trusted platform/clock boundary, persistent effect limits and what this would or would not prove.',
        'Preserve/quarantine the original UNKNOWN product root and continue authorized formal work in a genuinely new normal product root only if actual specification permits it. Never reset/copy away old failures/counters/Task/budget or count a disposable fixture as formal normal acceptance. Determine if this is compatible at all rather than recommend hiding the original failed attempt.',
    ],
    'requirements': [
        'No Source writes or actual OS/process/DB/GUI/API/model/key/private-pipe operations. You are not alone: B Source and independent STOP19 source review run in parallel; Root alone shared checkpoint/ownership/handoff. Only own new E, evidence/analysis helper text and read-only public files/web primary documents are writable/readable as appropriate.',
        'The goal is an explicit recovery/scope decision, not a historical closure reconstruction. Keep original raw error/ACK/cost/RunUNKNOWN/history unchanged in every option. Never call present PID absence, reboot or future logger evidence of original Wait success. No broad NO_EFFECT, no silent weakening of existing accepted proof classes.',
        'Consult only the relevant immutable specification/contract clauses for FAILED/UNKNOWN, native isolation/current quiescence, maintenance/recovery and formal root acceptance, plus exact existing STOP/C implementation/design boundaries and official Windows API primary documentation needed for the three candidates. Tie every sufficiency assertion to a source; distinguish new contract proposal from current implemented behavior. External technical statements must rely only on official docs/research primary sources.',
        'Bound this assessment to at most12 grouped shell/source/web query steps after initial scope read, with recipes before commands and full raw/env/native exit/diagnostics. Do not re-enumerate initializer/callback graph, search all historical receipts again, probe current processes or read product DB. Existing historical gap remains irreversible through existing interfaces. If current inputs cannot justify an option, say so precisely rather than expand indefinitely.',
        'Output boundary-decision.md/json with a compact comparison, one recommended option if justified, exact mandatory conditions/evidence still needed, minimal prospective Source paths/test cuts or explicit user resource/decision. Mark all proposed classes NOT_IMPLEMENTED_NOT_ACCEPTED and actual_authority=false. If no option is supportable within the available scope, report exact irreducible decision and stop this architecture branch. Keep report focused, no full replacement51path architecture.',
        'This is not Source authorization and author cannot self-accept any new class. Any chosen new class requires a separately registered minimal Source card, meaningful Windows fixtures and independent acceptance before actual action. STOP-r2 existing review/cuts remain unchanged; no interruption or edits to its frozen candidate. Formal increment0/all22open. Freeze report/command/diagnostic ledger and FINAL-manifest, then stop.',
    ], 'source_write_authority': False, 'actual_authority': False, 'formal_increment': 0,
}
new(O / 'qualification-recovery-boundary-decision-scope.json', scope)
ledger = read(A / 'diagnostic-ledger.json')
old = list(cp['failure_counters'])
items = [('failure-' + str(i), v) for i, v in enumerate(ledger['failures'], 1)]
assert len(items) == 3 and len(ledger['tool_diagnostics']) == 1
for i in range(1, 3):
    items.append(('tool-recovery-' + str(i), {'tool_call_ordinal': i, 'detail': ledger['tool_diagnostics'][0], 'native_exit': None}))
items.append(('initial-bootstrap-capture-gap', ledger['transcript_only_bootstrap_reads'][0]))
items.append(('display-truncation', ledger['display_truncation']))
for suffix, item in items:
    origin = '20261015|verifier-init-audit-' + suffix
    assert not any(v.get('origin_key') == origin for v in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'READONLY_AUDIT_DIAGNOSTIC_PRESERVED', 'detail': item, 'evidence_ref': ref(A / 'diagnostic-ledger.json'), 'counter_reset': False})
assert cp['failure_counters'][:1709] == old and len(cp['failure_counters']) == 1716
resume = read(B / 'continuation-cp514/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v93', at=now, checkpoint_revision=515, ownership_revision=301, failure_records_preserved=len(cp['failure_counters']), verifier_initialization_audit_ref=ref(A / 'FINAL-manifest.json'), verifier_initialization_audit_decision=audit['decision'], recovery_boundary_decision_scope_ref=ref(O / 'qualification-recovery-boundary-decision-scope.json'))
resume['next_command'] = 'B Source active; STOP-r2f5 exact19 independent review finds potential handle-ancestry/cancel/native-exit-field gaps, wait final. Init audit151refs verified NOT_PROVABLE,noactual/nativeclass; historical original verifier Wait cannot be retrofilled. New bounded12step recovery-boundary architecture decision registered, noSource/noactual. No broadinitrerun, originalRun/rawACK/effects/cost/counters unchanged. Main4f/protected9/dirty20/indexempty/processes retained. Formal0/42/all22open.'
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=515, expected_previous_revision=514, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp515=rr, verifier_initialization_audit_ref=ref(A / 'FINAL-manifest.json'), recovery_boundary_decision_scope_ref=ref(O / 'qualification-recovery-boundary-decision-scope.json'))
cp['evidence_index'].append({'kind': 'VERIFIER_AUDIT_NEGATIVE_LIMIT_ADOPTED_BOUNDED_RECOVERY_DECISION', 'ref': rr, 'formal_increment': 0})
ow.update(revision=301, expected_previous_revision=300, updated_at=now, updated_by='codex:/root')
ow['special_paths']['qualification_recovery_boundary_decision'] = {'owner': scope['owner'], 'mode': 'READ_ONLY_BOUNDED_ARCHITECTURE_DECISION', 'state': 'REGISTERED', 'scope_ref': ref(O / 'qualification-recovery-boundary-decision-scope.json'), 'write_scope': [scope['own_receipts']], 'source_write_authority': False, 'actual_authority': False}
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, data in raw.items():
    assert p.read_bytes() == data
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP515\n\nRead `' + rr['path'] + '` first. B Source/STOP independent review continue; verifier audit NOT_PROVABLE frozen. Bounded recovery-boundary decision only, no Source/actual grant. Formal0/42/all22open; preserved mixed records' + str(len(cp['failure_counters'])) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 515, 'ownership': 301, 'preserved_mixed_records': len(cp['failure_counters']), 'resume': rr, 'scope': ref(O / 'qualification-recovery-boundary-decision-scope.json'), 'audit_files_verified': 151}))
