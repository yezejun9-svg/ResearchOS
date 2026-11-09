import datetime
import hashlib
import json
import os
import subprocess
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
B = Path(__file__).parent
O = B / 'continuation-cp511'
E = R / 'execution/v2.4/receipts/W05/W05-99'
I = E / 'qualification_failure_revision03_independent_review_codex/20261015-current-chat'
A = E / 'qualification_failure_revision03_architecture_codex/20261015-current-chat'
H = E / 'historical_qualification_public_provenance_codex/20261015-current-chat'


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
    temporary = p.with_name(p.name + '.cp511.pending')
    with temporary.open('xb') as f:
        f.write(after)
    assert p.read_bytes() == before
    os.replace(temporary, p)


assert ref(I / 'FINAL-manifest.json')['sha256'] == 'c1f517f80da18e29a3b2f27c278ac65828372513552d35e3c7fc75ad5eb7b807'
for item in read(I / 'FINAL-manifest.json')['files']:
    p = I / item['path']
    assert p.parent == I and ref(p)['sha256'] == item['sha256'] and p.stat().st_size == item['bytes']
for relative, expected in [('verifier-dependency-inputs01/COLLECTION-manifest.json', '99617d07ea92e2f5a0142ce09445394867074ba308e2b2800bf062a8be6b9c9e'), ('verifier-initializer-index01/COLLECTION-manifest.json', '717bacc93892081fcb1895f70c3cc5e8e8371faf17f264fbc5b710ecdcfca3c6')]:
    p = H / relative
    assert ref(p)['sha256'] == expected
    for item in read(p)['files']:
        member = Path(item['path'])
        assert hashlib.sha256(member.read_bytes()).hexdigest() == item['sha256'] and member.stat().st_size == item['bytes']
addenda = read(I / 'mandatory-addenda.json')
lease_scope = read(A / 'C-lease-exact-scope.json')
allowed = set(lease_scope['production_existing'] + lease_scope['production_new'] + lease_scope['tests_allowed'])
assert len(addenda['C']) == 3 and all(set(item['paths']) <= allowed for item in addenda['C'])
cp_p = R / 'execution/v2.4/checkpoint.json'
ow_p = R / 'execution/v2.4/path_ownership.json'
hp = R / 'execution/v2.4/HANDOFF_RESUME_PACK.md'
sp = R / 'execution/v2.4/step_state.json'
raw = {p: p.read_bytes() for p in (cp_p, ow_p, hp, sp)}
cp, ow = read(cp_p), read(ow_p)
assert cp['revision'] == 510 and ow['revision'] == 296 and len(cp['failure_counters']) == 1629
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=R, text=True).strip() == '4f4023c956f84d65743f39ce77d6c8899a21ada1'
assert not subprocess.check_output(['git', 'diff', '--cached', '--name-only'], cwd=R)
assert len(subprocess.check_output(['git', 'status', '--short', '--untracked-files=no'], cwd=R, text=True).splitlines()) == 20
for item in read(E / 'current_chat_integration_preflight_codex/20261012-current-chat/preflight-v2.json')['protected_source']:
    assert ref(R / item['path'])['sha256'] == item['sha256']

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
O.mkdir(exist_ok=False)
adoption = {'schema': 'researchos.C-lease-and-narrow-classification-design-adoption.v1', 'at': now, 'status': 'DESIGN_CONSTRAINTS_ADOPTED_NOT_SOURCE_OR_ACTUAL_AUTHORITY', 'independent_review_ref': ref(I / 'FINAL-manifest.json'), 'lease_scope_ref': ref(A / 'C-lease-exact-scope.json'), 'mandatory_addendum': addenda, 'classification_decisions': read(I / 'classification-decisions.json'), 'scope_expansion': [], 'actual_STOP_C_enabled': False, 'formal_increment': 0}
new(O / 'C-design-adopted-constraints.json', adoption)
scope = {
    'schema': 'researchos.original-verifier-startup-authority-semantic-audit.v1',
    'at': now,
    'owner': 'codex:/root/verifier_revision_review',
    'model': 'gpt-6-astra',
    'reasoning_effort': 'high',
    'model_choice_reason': 'Security and architecture proof analysis of historical exact verifier selected-source initialization and pre-Job capability, independently constrained by accepted review',
    'mode': 'READONLY_SEMANTIC_PROOF_ANALYSIS_NO_SOURCE_OR_ACTUAL',
    'own_receipts': str(E / 'historical_verifier_initialization_authority_audit_codex/20261015-current-chat'),
    'binary_sha256': 'f255f4d49c5b217462bb38a8ec2292e9d62889d8506488569ff3638237708a43',
    'source_commit': '4f4023c956f84d65743f39ce77d6c8899a21ada1',
    'input_refs': [ref(I / 'FINAL-manifest.json'), ref(I / 'classification-decisions.json'), ref(A / 'FINAL-manifest.json'), ref(H / 'verifier-dependency-inputs01/COLLECTION-manifest.json'), ref(H / 'verifier-initializer-index01/COLLECTION-manifest.json'), ref(H / 'verifier-authority-inputs01/COLLECTION-manifest.json'), ref(H / 'attempt02/COLLECTION-manifest.json')],
    'requirements': [
        'Read scope and verify frozen input files. You are not alone: STOPanchor-r2 Source builder and A-r2 independent Source reviewer; B Source may start after A acceptance. No Source/shared checkpoint edits/current DB/OS-process observation/model/GUI/backups/private key or private pipe actions. Do not execute any verifier or product binary. Own new E only and explicit D analysis temp if necessary; log exact recipe before each command, full raw/env/native exit and all gaps/failures.',
        'Previous broad claims remain NOT_PROVABLE until actual complete premises are established; no self acceptance or actual authority. Goal is a concrete supported/missing startup capability proof matrix from exact selected sources, not a generic discussion or complete unrelated repository audit. Inputs now provide original exact332 link packages, current333 list extraunsafe,2145 selected files/2138 recorded-vector matches. All selected Go files match historical vector;7 unmatched HFiles are explicit toolchain header provenance limitation, not silently captured historical data. Current selection is reconstruction, original binary nm602 initializer symbols are actual exact binary data.',
        'Audit complete init/variable-initializer and background path BEFORE verifier receives Job, across selected project/third-party dependencies and relevant standard runtime boundaries. AST index parses2052 Go files,4696 initializer syntax entries/30085 functions, nonstandard82 init functions+1503 package values with call syntax. Syntax index includes deferred function literal bodies, type conversions and pure table registrations; distinguish them from actually executed initializer calls. Resolve actual reachable calls/dynamic registrations/callbacks/unsafe/native/assembly/OS DLL loader boundaries with source and symbol evidence; group purely static literal/table cases with explicit rule and enumerate residuals rather than claiming a grep proves closure.',
        'Trace actual main Challenge/Hello/ReadJob gate, all child entry points, imports/init code, reachable DB/store/protectedstore/provider/HTTP/client/exec/goroutine/timer/config/path scans before Job. Original argv empty, explicit child environment only SystemRoot/WINDIR/TEMP/TMP; Host owner/scheduler/short verifier token and Job not transferred on exact historical protocol-error branch is already supported narrow reconstruction. Prove or reject absence of independent product DB/network/external-effect work before Job; report any concrete startup side effects truthfully. No claim that ordinary sameSID process is OS sandboxed or has no ambient OS permissions.',
        'Include provenance and bounds for DLL lazy resolution, modernc libc/sqlite init registration/mutex/allocations, jsonschema embedded meta-schema compiler versus potential URL loaders, pdfcpu/font configuration, and Go runtime background/standard library initialization. Reachability must use exact selected files and original binary linkage, not README or all-version assumptions. Any unresolved dynamic/native/init path remains a named residual; no unsupported positive conclusion merely because direct os.Open/Dial strings absent.',
        'Assess narrowly proposed NEVER_JOB_AUTHORIZED_V1 operational substitute only if full startup/pre-Job premises support it; distinguish Host-no-Job control flow from process native closure. Do not invent original verifier PID/creation/native Wait/exit0/Close result or treat current absence/defer cmd.Wait call as captured success. You may separately assess whether a specifically bound source-derived synchronous-close completion class is supportable from existing public post-return evidence plus exact Go exec/os Windows wait implementation; mere DB reason written before defer is insufficient evidence of return, and missing response path remains missing. No new native process probe to fill history.',
        'If a finite operational class becomes supportable, freeze exact subject/binary/source/build/branch/authority/environment/pipe invariants, consumer checks, forbidden substitutions and tamper tests; identify smallest possible future STOP proof/scope amendment within existing19 but DO NOT edit Source or authorize current stop. Must receive separate independent semantic review before Root can register any class Source change or actual action. If still NOT_PROVABLE, deliver exact missing premise and bounded next resource request, not endless exploration. Do not re-open C lease/STOP anchor accepted designs or universal worker OS NO_EFFECT.',
        'Deliver immutable audit.md/audit.json, full selected-init coverage/residual matrix, relevant source hashes/line refs, proposed proof class and tests only if justified, command/diagnostic ledger and FINAL-manifest. Keep source inference/historical raw/current reconstruction distinct. No model calls/tests of actual product/formal increment and no self-signed acceptance.',
    ],
    'formal_increment': 0,
}
new(O / 'verifier-initialization-semantic-audit-scope.json', scope)
roots = [
    {'ordinal': 1, 'tool_chunk': 'cc7502', 'native_exit': 0, 'kind': 'ROOT_OVERSIZED_INITIALIZER_DISPLAY', 'detail': 'AST initializer call-list display was truncated; original complete pinned AST JSON exists. Only bounded follow-up summaries used, no full raw display asserted.'},
    {'ordinal': 2, 'tool_chunk': '110d55', 'native_exit': 1, 'kind': 'ROOT_GUESSED_DOMAIN_SOURCE_PATHS', 'detail': 'artifact.go and runtime_observation.go absent; exact C architecture search returned relevant planned uploaded_content row and rg --files recovered existing source list. No absence inference or Source mutation.'},
    {'ordinal': 3, 'kind': 'ROOT_COMMAND_COUNT_DESCRIPTION_CORRECTION', 'detail': 'Root messages and private continuation text said43 A-r2 recorded commands; frozen manifest actually58. CP510 registrar used len and verified all58 with exactly9 nonzero; source-artifact-verification is authoritative. No author manifest overwritten.'},
]
new(O / 'root-read-and-description-diagnostics.json', {'items': roots})
old = list(cp['failure_counters'])
imports = []
for line in (I / 'diagnostics.jsonl').read_text(encoding='utf8').splitlines():
    if not line.strip():
        continue
    item = json.loads(line)
    if item.get('capture_status') == 'GAP' or item.get('native_exit', item.get('exit_code', 0)) != 0 or item.get('result') in ['HASH_VERIFICATION_FAILED', 'PATH_LOOKUP_MISS', 'NONBLOCKING_WARNING']:
        imports.append(('20261015|Clease-F01-independent-diagnostic-' + str(item['ordinal']), item, ref(I / 'diagnostics.jsonl')))
for item in roots:
    imports.append(('20261015|root-cp511-diagnostic-' + str(item['ordinal']), item, ref(O / 'root-read-and-description-diagnostics.json')))
assert len(imports) == 10
for origin, detail, evidence in imports:
    assert not any(item.get('origin_key') == origin for item in old)
    cp['failure_counters'].append({'origin_key': origin, 'attempts': 1, 'status': 'INDEPENDENT_DESIGN_OR_READ_DIAGNOSTIC_PRESERVED', 'detail': detail, 'evidence_ref': evidence, 'counter_reset': False})
assert cp['failure_counters'][:1629] == old
count = len(cp['failure_counters'])
resume = read(B / 'continuation-cp510/RESUME.current.json')
resume.update(schema='researchos.current-chat-resume.v89', at=now, checkpoint_revision=511, ownership_revision=297, failure_records_preserved=count, C_lease_F01_independent_ref=ref(I / 'FINAL-manifest.json'), C_design_adopted_constraints_ref=ref(O / 'C-design-adopted-constraints.json'), verifier_initialization_semantic_audit_scope_ref=ref(O / 'verifier-initialization-semantic-audit-scope.json'), next_command='A-r2 independent Source review freezing limited verdict; B Source only after accepted exact A. STOPanchor-r2 continues real two compiledgrantCLI fixtures. C design accepted conditionally with all copied C-LD01..03/F01-D01..03/W-D01 but no Source/actual C authority. Separate exact-verifier initialization semantic audit registered; verifier operational substitute still NOT_PROVABLE until independently supported. No actual DB/backup/stop/model/replay/newrequest/package/migration. Main4f/old20/indexempty/f3consumedUNKNOWN preserved. Formal0/42/all22open.')
new(O / 'RESUME.current.json', resume)
rr = ref(O / 'RESUME.current.json')
cp.update(revision=511, expected_previous_revision=510, updated_at=now, updated_by='codex:/root', next_command=resume['next_command'])
cp['work_in_progress'].update(current_chat_continuation_cp511=rr, C_lease_F01_independent_ref=ref(I / 'FINAL-manifest.json'), C_design_adopted_constraints_ref=ref(O / 'C-design-adopted-constraints.json'), verifier_initialization_semantic_audit_scope_ref=ref(O / 'verifier-initialization-semantic-audit-scope.json'))
cp['evidence_index'].append({'kind': 'C_LEASE_AND_NARROW_HISTORICAL_CLASSIFICATION_CONDITIONAL_DESIGN_ADOPTED_VERIFIER_INIT_AUDIT_REGISTERED', 'ref': rr, 'formal_increment': 0})
ow.update(revision=297, expected_previous_revision=296, updated_at=now, updated_by='codex:/root')
ow['special_paths']['C_lease_F01_independent_review'].update(state='FROZEN_CONDITIONAL_DESIGN_ACCEPTED_NOT_ACTUAL', evidence_ref=ref(I / 'FINAL-manifest.json'))
ow['special_paths']['verifier_initialization_semantic_audit'] = {'owner': scope['owner'], 'mode': scope['mode'], 'state': 'REGISTERED', 'scope_ref': ref(O / 'verifier-initialization-semantic-audit-scope.json'), 'write_scope': [scope['own_receipts']]}
for p, name in ((cp_p, 'checkpoint.before.raw.json'), (ow_p, 'ownership.before.raw.json'), (hp, 'handoff.before.raw.md')):
    (O / name).write_bytes(raw[p])
for p, before in raw.items():
    assert p.read_bytes() == before
replace(ow_p, raw[ow_p], (json.dumps(ow, ensure_ascii=False, indent=2) + '\n').encode())
replace(cp_p, raw[cp_p], (json.dumps(cp, ensure_ascii=False, indent=2) + '\n').encode())
replace(hp, raw[hp], ('# Current verified continuation CP511\n\nRead `' + rr['path'] + '` first. C lease design adopted with copied mandatory constraints; current actual STOP/C remains unavailable. Exact verifier initialization audit registered; A independent Source review and STOPanchor-r2 continue. Main4f/f3 consumedUNKNOWN preserved. Formal0/42/all22open; preserved records' + str(count) + '.\n\n').encode() + raw[hp])
assert sp.read_bytes() == raw[sp]
print(json.dumps({'checkpoint': 511, 'ownership': 297, 'failure_records': count, 'diagnostics_imported': len(imports), 'resume': rr, 'scope': ref(O / 'verifier-initialization-semantic-audit-scope.json')}))
