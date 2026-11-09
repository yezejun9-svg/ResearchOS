import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os').resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
RECEIPTS = Path('execution/v2.4/receipts/W05/W05-99')
AUTHOR = ROOT / '.local/worktrees/codex-w0599-provider-binding'
HANDLER = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
HP = RECEIPTS / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
TLS = HP / 'tls-test-only-8ab013f049644525bc4f8ffee2901d45'
STOP = ROOT / RECEIPTS / 'provider_typed_route_independent_replay_codex/632e634c-2f7f-47c3-b63a-b7073a9e1ccb'
F08 = ROOT / RECEIPTS / 'cancel_finalization_udf_producer_supplement_codex/9d5612d4e27d43e09250867e88edcc9e'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]


def encode(o):
    return (json.dumps(o, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def save(n, o):
    with (OUT / n).open('xb') as f:
        f.write(encode(o))


def ref(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    p = p.resolve()
    assert p.is_relative_to(ROOT)
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if expected:
        assert h == expected, str(p)
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': h, 'bytes': len(b)}


def check(row):
    actual = ref(row['path'])
    assert actual['sha256'] == row['sha256'], row['path']
    if 'bytes' in row:
        assert actual['bytes'] == row['bytes'], row['path']


copies = []


def public_handler_copy(row):
    rel = Path(row['path'])
    assert not rel.is_absolute() and rel.is_relative_to(HP), str(rel)
    source = HANDLER / rel
    original = ref(source, row['sha256'])
    destination = ROOT / rel
    destination.parent.mkdir(parents=True, exist_ok=True)
    raw = source.read_bytes()
    if destination.exists():
        assert destination.read_bytes() == raw
    else:
        with destination.open('xb') as f:
            f.write(raw)
    result = ref(destination)
    copies.append({'original': original, 'copy': result})
    return result


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (290, 118, 255)
assert cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
manifest_ref = ref(STOP / 'manifest.json', '81a8dd9831385a71360e7c8848ae583ba11be83449189430184af29ab4fa0911')
for row in json.loads((ROOT / manifest_ref['path']).read_bytes())['files']:
    check(row)
review_ref = ref(STOP / 'review.json', '95d78e866a6f9ed1015877602b2c0ccd3712c2886804c315391c5b0f2b6c64e2')
failure_ref = ref(STOP / 'failure_origins.json', 'd6dd83ed9bbadfcbe0f78245b143553d2e26d6f895108a4eab42b64185fd23fa')
request_ref = ref(STOP / 'production-only-resource-request.json', '857ec278126328b08f35f1fb673b84fc7cedae367892d4e86e4db00f87c5337f')
review = json.loads((ROOT / review_ref['path']).read_bytes())
assert review['cases_executed'] == review['compile_invocations'] == 0 and review['not_run'] == 76
assert review['gofmt_exit'] == 0 and review['go_list_exit'] == 1 and not review['input_drift']
request = json.loads((ROOT / request_ref['path']).read_bytes())
check(request['basis'])
assert request['candidate'] == '6fb5263681c17f0e50920c354dc07ed440a23714'
assert request['exact_count'] == len(request['scope_requested']) == 10
assert request['existing_local_source_hash_matches'] == 361 and len(request['excluded_author_overcapture_test_paths']) == 11
assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=AUTHOR).decode().strip() == request['candidate']
assert not subprocess.check_output(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=AUTHOR).strip()
assets = []
checkout = ROOT / '.local/independent-provider-typed-route-r288-d4fd01da69224e05a135e0b01794826c'
for row in request['scope_requested']:
    assert row['path'].startswith('ops/supervisor/') and row['path'].endswith('_windows.go') and not row['path'].endswith('_test.go')
    source = AUTHOR / row['path']
    exact = ref(source, row['sha256'])
    assert exact['bytes'] == row['bytes']
    raw = subprocess.check_output(['git', 'show', request['candidate'] + ':' + row['path']], cwd=AUTHOR)
    blob = subprocess.check_output(['git', 'rev-parse', request['candidate'] + ':' + row['path']], cwd=AUTHOR).decode().strip()
    assert raw == source.read_bytes() and blob == row['git_blob']
    assert not re.search(rb'^\s*func\s+init\s*\(', raw, re.M) and b'//go:embed' not in raw
    assert not (checkout / row['path']).exists()
    assets.append({**copy.deepcopy(row), 'root_source_ref': exact, 'root_verified_immutable_git_bytes': True, 'destination': (checkout / row['path']).relative_to(ROOT).as_posix()})
provider_origin = json.loads((ROOT / failure_ref['path']).read_bytes())['origins'][0]
check(provider_origin['invocation'])
check(provider_origin['result'])
provider_result = json.loads((ROOT / ref(provider_origin['result']['path'])['path']).read_bytes())
assert provider_result['exit'] == provider_origin['actual_exit'] == provider_origin['driver_outer_exit'] == 1
check(provider_result['stdout'])
check(provider_result['stderr'])
assert provider_origin['product_case_failures'] == 0

tls_ref = public_handler_copy({'path': (TLS / 'proposal.json').as_posix(), 'sha256': '80da7bf92e256c8b241202a76e1c5888eca80485f99b3fc705e1a39bb0cc5b97'})
tls = json.loads((ROOT / tls_ref['path']).read_bytes())
assert tls['owned_source'] == 'internal/domain/runtime_configuration_binding_windows_test.go' and tls['production_source_changes'] == tls['tests_executed'] == 0
check(tls['pinned_go_authority'])
public_handler_copy(tls['supersedes_design_only'])
handler_fail_ref = public_handler_copy({'path': (HP / 'failure-origins-a743896e540f4e7ea03b7d5b71748cfb/failure_origins.json').as_posix(), 'sha256': '1e28da0fb96c0e3ae8c1faaefd8ae25af0bdcc6092222a34395c68516e47bb7c'})
handler_fail = json.loads((ROOT / handler_fail_ref['path']).read_bytes())
for row in handler_fail['actual_failed_invocations']:
    for key, value in row.items():
        if key.endswith('_ref') and isinstance(value, dict) and 'sha256' in value:
            public_handler_copy(value)
    result = json.loads((ROOT / row['result.json_ref']['path']).read_bytes())
    invocation = json.loads((ROOT / row['invocation_ref']['path']).read_bytes())
    assert row['actual_exit'] == result['exit'] == invocation['exit'] == 1
public_handler_copy(handler_fail['prior_diagnostic_ref'])
latest_pass_ref = public_handler_copy(handler_fail['latest_pass_ref'])
latest_pass = json.loads((ROOT / latest_pass_ref['path']).read_bytes())
assert latest_pass['exit'] == 0 and latest_pass['test_events'] == {'pass': 13, 'fail': 0, 'skip': 0}
supp_ref = public_handler_copy({'path': (TLS / 'failure_supplement.json').as_posix(), 'sha256': '1c83ed4199952811ec36051af8ca40b96048007d752789cb53781f95265f13a8'})
supp = json.loads((ROOT / supp_ref['path']).read_bytes())
for row in supp['origins']:
    for key in ['raw_ref', 'invocation_ref', 'result_ref']:
        public_handler_copy(row[key])
    invocation = json.loads((ROOT / row['invocation_ref']['path']).read_bytes())
    result = json.loads((ROOT / row['result_ref']['path']).read_bytes())
    assert row['actual_exit'] == invocation['exit'] == result['exit'] == 1
f08_error_ref = ref(F08 / 'read-errors-and-prior-outer-exit.json', '38952023df25ff7faf751d5c0566a4a8906821449b15c7c6193bb60228023413')
f08_copy_ref = ref(ROOT / RECEIPTS / 'integration_codex/f08-udf-copy-r290/copy_audit.json', '08fd76cee19c0a84b73cd15b9b0c3ea7e8eaf51ed3e8408e9c0b036e0ea8766f')
assert json.loads((ROOT / f08_copy_ref['path']).read_bytes())['count'] == 105
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
compile_scope = {
    'schema': 'researchos.root.provider-complete-public-compiler-resource-amendment.v1',
    'actor': 'codex:/root', 'executor': 'codex:/root/w05_merge_review', 'at': now,
    'original_scope_ref': cp['work_in_progress']['provider_typed_route_independent_execution_scope_ref'],
    'previous_amendment_ref': cp['work_in_progress']['provider_independent_resources_restore_overlay_amendment_ref'],
    'review_ref': review_ref, 'manifest_ref': manifest_ref, 'failure_origin_ref': failure_ref, 'request_ref': request_ref,
    'implementation_authorized': True, 'exact_public_compile_exports': assets,
    'source_policy': 'Export only ten candidate Git production files to original isolated checkout. Public functions named holdout or release are compiled only; no function/runner/private data/test/generator is executed. Original product9 and original7DB remain frozen.',
    'negative_scope': 'Do not export eleven imported-package TestGoFiles overcaptured by author. No new dataset, actual holdout, sandbox/release evidence, credential, Node, model, HTTP, worker or paid call.',
    'new_evidence_and_progress': 'Original sparse export did not include ops. Prior three sandbox assets now exact and gofmt0, then distinct supervisor omission stopped before compile. Independent inventory compared full author3690 compiler vector, verified361 present local bytes and found precisely10 production missing plus11 imported tests not needed. This is a deliberate complete known-input amendment, not an automatic same-input retry or failure reset.',
    'next_sequence': 'Exact10 export -> preserve already reviewed producer-bound overlay c300fb61dd2855bea5ba2f9bce329dcabc53662d4bb30169a59846d187105676 (copy to new immutable namespace if needed) -> actual gofmt/go-list -> full complete new compiled/source/tools/SDK/7DB freeze -> compile -> executable freeze -> same76 controls. Internal64 first R01/R02/R03 first, six public positives then six public backup refusals. No extra control or SQL mutation.',
    'stop_rule': 'First unexpected compilation/resource/control outcome stops dependent branch. No further automatic sparse-package export or hidden expectation correction. Retain every stopped result and report precise next producer/resource evidence for Root.',
    'previous_case_count': 0, 'maximum_controls': 76, 'preparation_failure_origins': 3,
    'original_history_failures': 5, 'original_P1_failures': 3, 'failure_reset': False,
    'source_acceptance': False, 'formal_increment': 0
}
save('compiler_resource_amendment.json', compile_scope)
compile_ref = ref(OUT / 'compiler_resource_amendment.json')
tls_scope = {
    'schema': 'researchos.root.same27-test-only-tls-fixture-amendment.v1',
    'actor': 'codex:/root', 'executor': 'codex:/root/sources_parent_impl', 'at': now,
    'original_scope_ref': cp['work_in_progress']['configuration_handler_scope_ref'],
    'proposal_ref': tls_ref, 'pinned_go_source_ref': ref(tls['pinned_go_authority']['path']),
    'implementation_authorized': True, 'source_paths_added': [], 'exact_source_count': 27,
    'only_owned_source': tls['owned_source'], 'production_TLS_source_changes': 0,
    'contract': copy.deepcopy(tls),
    'root_requirements': [
        'Append helper/positive and causally distinct negative tests only in owned new test file; do not modify protected muBrokerFixtureProgram, coordinatorFixtureProgram, qualifyNativeCoordinator, actual runtime_model source or old assertions.',
        'Independent exact-case offline process receives GODEBUG=x509usefallbackroots=1 before any TLS setup; preserve any other required GODEBUG options. Install fallback roots once via sync.Once, only exact own public fixture cert. No system/user truststore mutation, no InsecureSkipVerify, TLS key logger, arbitrary Doer, hostname bypass or production runtime port. Fixture key/public cert are solely local test assets.',
        'Root independently read pinned root.go72-122 in0246b2 actual0: this API explicitly supports Windows pureGo verification and forces process fallback roots only with exact environment. It is test process authority, never actual LIVE Windows host qualification.',
        'Required actual producer order: obtain actual existing contextFixture Owner/project -> own TLS SSE provider -> real Decode/Execute host.configure -> returned original config ref -> construct/seal profile once in own minimal helper using same fixture -> real RegisterRuntimeQualificationPlan/BeginRuntimeQualification -> actual immutable SDK bundle and native process -> original independent FIXTURE acceptance -> exact Session.create/NORMAL firstTask provenance. No retrofit of already sealed Artifact or current head as historical proof.',
        'Keep exact original model/config/provider/credential/profile/admission refs and full model effect/request history; secret is solely synthetic test data, never supplied key/Vault/DPAPI. Original production HTTPS requirement unchanged. Explicit FIXTURE mode with zero external requests/paid calls.',
        'Record complete source/tool/dependency/compiler/SDK/testexe/public cert/raw/closed SQLite proof before and after. Actual default certificate/hostname validation failures and unqualified modelref refusal must retain real stage outcomes; no fake model receipt or ready flag.',
        'Existing successful same-input cases may be reused. The f80 broad selector included protected migration ordinary and failed; preserve one actual origin with two failure events. No repeat of that migration or held generic1811/providerhistory5/Q10/L14. Only new TLS cases and changes affecting current source closure trigger new validation.'
    ],
    'source_acceptance': False, 'formal_increment': 0, 'failure_reset': False
}
save('test_tls_scope_amendment.json', tls_scope)
tls_scope_ref = ref(OUT / 'test_tls_scope_amendment.json')
save('handler-public-copy-audit.json', {'copies': copies, 'count': len(copies), 'product_source_writes': 0})
root_observation = {'actor': 'codex:/root', 'tool_chunk': 'd66caf', 'actual_outer_exit': 1,
    'cause': 'Last read-only rg selector found no HostConfiguration/ModelConfigRef/ProviderProfile text in new owned test file; preceding fixture and producer reads succeeded. No compilation/test/SQL was executed by this command.',
    'provenance': 'Original native exec_command result d66caf visible in chat; this file is transcript-derived bookkeeping, not reconstructed original process raw.', 'product_failure': False}
save('root-read-observation.json', root_observation)
root_read_ref = ref(OUT / 'root-read-observation.json')
old = copy.deepcopy(cp['failure_counters'])
new_origins = []


def append(key, status, evidence, detail):
    assert key not in {r.get('origin_key') for r in cp['failure_counters']}
    row = {'origin_key': key, 'attempts': 1, 'retries_used': 0, 'status': status,
        'evidence_ref': evidence, 'detail': detail, 'count_once': True, 'counter_reset': False, 'formal_increment': 0}
    cp['failure_counters'].append(row)
    new_origins.append(key)


append('W05-99/independent-provider-precompile/' + provider_origin['origin_id'], 'ACTUAL_GO_LIST_EXIT1_OUTER1_ONE_SUPERVISOR_OMISSION_NO_CASE', failure_ref, provider_origin)
for row in handler_fail['actual_failed_invocations']:
    append('W05-99/handler-validation/' + row['origin_id'], 'ACTUAL_FAILED_BATCH_SINGLE_BACKUP_FIXTURE_STAGE_CAUSE_PRESERVED', handler_fail_ref, row)
for row in handler_fail['tool_outer_nonzero']:
    assert row['outer_exit'] == 1
    append('W05-99/handler-read-tool/' + row['chunk'], 'REPORTED_ACTUAL_TOOL_OUTER1_TRANSCRIPT_LOCATOR_NO_PRODUCT_CASE', handler_fail_ref, row)
for row in supp['origins']:
    append('W05-99/handler-validation/' + row['id'], 'ACTUAL_BATCH_EXIT1_ONE_PROTECTED_MIGRATION_LEAF_PLUS_PARENT_NO_RETRY', supp_ref, row)
for row in supp['tool_outer']:
    assert row['exit'] == 1
    append('W05-99/handler-read-tool/' + row['chunk'], 'REPORTED_ACTUAL_READ_ONLY_TOOL_OUTER1_TRANSCRIPT_LOCATOR_NO_PRODUCT_CASE', supp_ref, row)
f08 = json.loads((ROOT / f08_error_ref['path']).read_bytes())
for row in f08['observations']:
    if row['outer_exec_exit_code'] != 0:
        assert row['outer_exec_exit_code'] == 1
        append('W05-99/F08-read-tool/' + row['tool_chunk'], 'REPORTED_ACTUAL_READ_ONLY_TOOL_OUTER1_TRANSCRIPT_LOCATOR_NO_SQL', f08_error_ref, row)
append('W05-99/Root/read-only-rg/d66caf', 'ACTUAL_ROOT_READ_ONLY_TOOL_OUTER1_NO_MATCH_NO_PRODUCT_CASE', root_read_ref, root_observation)
assert cp['failure_counters'][:255] == old and len(new_origins) == 15 and len(cp['failure_counters']) == 270
for p, raw in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(raw)
subs = ow['card_path_bindings']['W05-99']['subtasks']
subs['provider_typed_route_independent_replay'].update(state='COMPLETE_KNOWN10_PUBLIC_PRODUCTION_COMPILER_ASSETS_AMENDMENT_AUTHORIZED_CASES0_OF76',
    complete_compiler_resource_amendment_ref=compile_ref, stopped_review_ref=review_ref, preparation_failures=3)
subs['host_configuration_public_handlers'].update(test_tls_amendment_ref=tls_scope_ref)
subs['f08_whole_scope_readonly_review'] = {'owner': 'codex:/root/f08_whole_scope_review', 'source_author': 'codex:/root/command_queue_impl',
    'state': 'READONLY_FULL19_DESIGN_REVIEW_NO_IMPLEMENTATION',
    'receipt_namespace': (RECEIPTS / 'cancel_finalization_whole_scope_independent_review_codex').as_posix() + '/**',
    'production_source_writes': 0, 'SQL_or_test_execution': 0, 'formal_increment': 0}
cp['work_in_progress'].update(provider_independent_complete_compiler_resource_amendment_ref=compile_ref,
    provider_independent_stopped_review_ref=review_ref, configuration_handler_test_tls_scope_amendment_ref=tls_scope_ref,
    configuration_handler_failure_import_ref=handler_fail_ref, configuration_handler_failure_supplement_ref=supp_ref,
    configuration_handler_pending_and_backup_13pass_result_ref=latest_pass_ref,
    f08_udf_public_copy_ref=f08_copy_ref,
    f08_whole19_readonly_review='codex:/root/f08_whole_scope_review; new1MiB response cap not approved because frozen valid responses unbounded; closed witness/relationalDDL still review prerequisite.',
    next_action='Handler same27 test-only actual HTTPS SDK fixture while other same-input passes retained; independent provider complete known10 compiler export then actual compile/same76. F08 whole19 readonly, no SQL24 or scopehandoff before handler freeze and full revised closed-format review. Preserve all counts and raw; source/formal acceptance0.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'COMPLETE_KNOWN_PROVIDER_COMPILER_CLOSURE_AND_SAME27_TEST_TLS_AMENDMENTS_FAILURE_RECONCILIATION',
    'compile_scope_ref': compile_ref, 'tls_scope_ref': tls_scope_ref, 'new_unique_origins': new_origins,
    'failure_origins_before': 255, 'failure_origins_after': 270, 'formal_increment': 0})
cp.update(revision=291, expected_previous_revision=290, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=119, amended_at=now, amended_by='codex:/root')
for row in [compile_ref, tls_scope_ref, review_ref, failure_ref, request_ref, tls_ref, handler_fail_ref, supp_ref, f08_copy_ref, f08_error_ref, root_read_ref, latest_pass_ref]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
save('record.json', {'checkpoint': [290, 291], 'ownership': [118, 119], 'failure_origins': [255, 270],
    'unique_origins': new_origins, 'public_compile_resources': 10, 'handler_source_count': 27, 'production_TLS_change': 0,
    'provider_case_runs': 0, 'formal_increment': 0, 'unknown_da8654_f27297_unchanged': True})
assert all(p.read_bytes() == raw for p, raw in before.items())
for p, value in zip(CANON[:2], [cp, ow]):
    temp = p.with_name(p.name + '.root291.tmp')
    with temp.open('xb') as f:
        f.write(encode(value))
    assert p.read_bytes() == before[p]
    os.replace(temp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 291, 'ownership': 119, 'failure_origins': 270,
    'compiler_amendment_ref': compile_ref, 'tls_scope_amendment_ref': tls_scope_ref,
    'source_writes': 0, 'formal_increment': 0}, ensure_ascii=True))
