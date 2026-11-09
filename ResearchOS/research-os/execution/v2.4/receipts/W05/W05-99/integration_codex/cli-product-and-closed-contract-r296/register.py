import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'execution/v2.4'
RP = Path('execution/v2.4/receipts/W05/W05-99')
HANDLER = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
QUEUE = ROOT / '.local/worktrees/codex-w0599-command-queue'
HP = RP / 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec'
CANON = [BASE / n for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')

def save(name, value):
    with (OUT / name).open('xb') as stream:
        stream.write(encode(value))

def ref(path, sha=None, size=None):
    path = Path(path)
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()
    assert path.is_relative_to(ROOT), str(path)
    raw = path.read_bytes()
    got = hashlib.sha256(raw).hexdigest()
    assert sha is None or got == sha, str(path)
    assert size is None or len(raw) == size, str(path)
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': got, 'bytes': len(raw)}

def verify(row):
    return ref(row['path'], row['sha256'], row.get('bytes'))

def load(row):
    verify(row)
    return json.loads((ROOT / row['path']).read_bytes())

copies = []
def copy_file(source, target, sha=None, size=None):
    src = ref(source, sha, size)
    raw = Path(source).read_bytes()
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        assert target.read_bytes() == raw, str(target)
    else:
        with target.open('xb') as stream:
            stream.write(raw)
    got = ref(target, src['sha256'], src['bytes'])
    copies.append({'source': src, 'copy': got})
    return got

def copy_namespace(worktree, namespace, expected_manifest, expected_handoff, expected_count):
    source = worktree / namespace
    manifest = json.loads((source / 'manifest.json').read_bytes())
    ref(source / 'manifest.json', expected_manifest)
    assert len(manifest['files']) == expected_count
    for row in manifest['files']:
        relative = Path(row['path'])
        assert not relative.is_absolute() and '..' not in relative.parts
        copy_file(source / relative, ROOT / namespace / relative, row['sha256'], row.get('bytes'))
    m = copy_file(source / 'manifest.json', ROOT / namespace / 'manifest.json', expected_manifest)
    h = copy_file(source / 'handoff.json', ROOT / namespace / 'handoff.json', expected_handoff)
    return m, h

def copy_handler_ref(row):
    relative = Path(row['path'])
    assert not relative.is_absolute() and relative.is_relative_to(HP)
    return copy_file(HANDLER / relative, ROOT / relative, row['sha256'], row.get('bytes'))

def copy_handler_nested(value):
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value and str(value['path']).startswith(HP.as_posix() + '/'):
            copy_handler_ref(value)
        else:
            for child in value.values():
                copy_handler_nested(child)
    elif isinstance(value, list):
        for child in value:
            copy_handler_nested(child)

before = {path: path.read_bytes() for path in CANON}
cp, ow = [json.loads(before[path]) for path in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (295, 123, 289)
assert hashlib.sha256(before[CANON[2]]).hexdigest() == 'fa58dad93d4ad94c27184d3c2dac318c7328eef7e748bd9525af75c8871c6149'
assert hashlib.sha256(before[CANON[3]]).hexdigest() == 'b357f60a9463b1a7504487bd8debf2b55f87f35938a26fe68a495aa834794129'
head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == cp['head'] == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
status = subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT)
assert len(status.splitlines()) == 13
assert len([row for row in status.splitlines() if row[:2] == b' D']) == 11
handler = ow['card_path_bindings']['W05-99']['subtasks']['host_configuration_public_handlers']
assert len(handler['paths']) == 33

review_ns = ROOT / RP / 'handler_cli_product_scope_independent_review_codex/e510a242-5d8f-484d-80f4-464580eed502'
cli_manifest = ref(review_ns / 'manifest.final.json', '5f9458c99c630b2c0fc5a9fcd54c140ce0a23017bce8248c50bb4b4f0806676a')
entries = load(cli_manifest)['entries']
assert len(entries) == 36
for entry in entries:
    verify(entry)
cli_review_ref = ref(review_ns / 'scope_review.json', '71aebabf60e2999a9ef1c94104e87cfdb50aa5d612980572aacb389ecf6613a4')
cli_review = load(cli_review_ref)
assert cli_review['decision'] == 'SOURCE_SCOPE_READY_WITH_MANDATORY_SAME_PATH_BOUNDS'
assert not cli_review['source_acceptance'] and len(cli_review['mandatory_same_path_bounds']) == 6
proposal_relative = HP / 'cli-product-scope-f31f46a2fa3d4432b52d02c4cd4b1921/proposal.json'
proposal_ref = copy_handler_ref({'path': proposal_relative.as_posix(), 'sha256': '71024bfbd1f9115354fb61c4efb3742f07b47eaf15d77f2a7ee15fcb65d2fd87'})
proposal = load(proposal_ref)
paths = [row['path'] for row in proposal['source_scope']]
assert len(paths) == len(set(paths)) == 5
assert not set(paths).intersection(handler['paths'])
for row in proposal['source_scope']:
    if row['exists']:
        ref(ROOT / row['path'], row['source_before_sha256'])
        ref(HANDLER / row['path'], row['source_before_sha256'])
    else:
        assert not (ROOT / row['path']).exists() and not (HANDLER / row['path']).exists()
save('cli_product_scope_amendment.json', {
    'schema': 'researchos.root.cli-product-source-scope.v1', 'owner': handler['owner'],
    'worktree': handler['worktree'], 'base_head': head, 'paths_before': 33, 'paths_after': 38,
    'proposal_ref': proposal_ref, 'independent_scope_review_ref': cli_review_ref, 'manifest_ref': cli_manifest,
    'additional_exact_source_paths': paths, 'source_scope': proposal['source_scope'],
    'mandatory_same_path_bounds': cli_review['mandatory_same_path_bounds'],
    'no_new_SQL_or_shared_schema': True, 'local_fixture_calls_only': True,
    'preserve_all_old_assertions_and_check_ids': True, 'source_acceptance': False,
    'final_freeze_and_full_actual_source_matrix_and_nonauthor_review_required': True,
    'no_auto_retry_or_external_model_or_private_vault_access': True, 'formal_increment': 0})
cli_scope_ref = ref(OUT / 'cli_product_scope_amendment.json')

# A separately sealed nonauthor boundary review is a required input, not inferred approval.
boundary_ns = ROOT / RP / 'handler_fixture_boundary_scope_review_codex/e11968dbe7734f819c1a4a1b1c158aad'
boundary_review_ref = ref(boundary_ns / 'scope_review.json', 'e736a3517e9dffd03174f9fe537222f8ad8e82dd24a212012038df0199e8d573')
boundary_review = load(boundary_review_ref)
assert boundary_review['verdict'] == 'SCOPE_READY_WITH_EXPLICIT_SCHEMA22_COMPATIBILITY_BOUNDARY'
assert not boundary_review['source_acceptance'] and boundary_review['additional_paths'] == 0
boundary_manifest_ref = ref(boundary_ns / 'manifest.json', '2186dacd0b1b08647d7686353c9d8ed3966913875370dfe2d0fbabd226b2c5d1')
boundary_manifest = load(boundary_manifest_ref)
assert len(boundary_manifest['files']) == 29
for row in boundary_manifest['files']:
    relative = Path(row['path'])
    verify(row if relative.is_absolute() or relative.parts[:1] == ('execution',) else dict(row, path=str(boundary_ns / relative)))
save('fixture_boundary_scope_amendment.json', {
    'schema': 'researchos.root.fixture-boundary-source-scope.v1', 'owner': handler['owner'],
    'paths_added': 0, 'scope_review_ref': boundary_review_ref, 'manifest_ref': boundary_manifest_ref,
    'bounds': [
        {'path': 'apps/cli/cli_sessions_test.go', 'span': 'Original TestW14CLICommandsUseRealSessionHTTP loop94-103',
         'only_change': 'c.commandID = domain.ID() before each genuinely NEW step v2Call; old104+assertions and exact replay tests unchanged.'},
        {'path': 'internal/domain/client_configuration_test.go', 'span': 'Original configurationReceipt111-117 only; signature and all9 calls unchanged',
         'only_change': 'CallerTx readonly sqlite_schema exact table existence. Missing identity table permits original headers {} only for actual original schema22; other version or SQL error fails. When table exists readonly principal/command identity presence: present uses pinned backupConfigurationSchema and writeClientCommandEnvelope(doc,env); absent actual legacy retains original headers {}. SQL errors never treated as absent. Preserve original ContentHash/body/status/response/time and negative semantic assertions; no production replay backfill.'}],
    'no_extra_source_file_or_caller_changes': True, 'foundation_independent_acceptance': False,
    'source_acceptance': False, 'formal_increment': 0})
fixture_scope_ref = ref(OUT / 'fixture_boundary_scope_amendment.json')

f08_ns = RP / 'cancel_finalization_closed_contract_revision_codex/e38a370a015346dfad46530b0fdd44f1'
f08_manifest, f08_handoff = copy_namespace(QUEUE, f08_ns,
    'a61ae5dc340f2f85f4e2b7cd9e95b99870e86bf32467cd7bb2437f41163c1d8e',
    'e328b09bd57b193d86a9ffaecea818c17f34dad0ea2bb19041156acf91a5b059', 111)
f08_proposal_ref = ref(ROOT / f08_ns / 'scope_proposal.json', 'a798158a34f413b135d1960a98233ddf5454bd92b80bc45357577803c43eb758')
f08_proposal = load(f08_proposal_ref)
assert f08_proposal['scope_count'] == 20 and len(f08_proposal['future_gates']) == 12
pre_ns = RP / 'handler_configuration_preliminary_independent_review_codex/195730b0764f4f008d74e0f148893185'
pre_manifest, pre_handoff = copy_namespace(QUEUE, pre_ns,
    '71f016c3b696efba0a4b8d1d6522a0351e794198a4fa2e44f49c5571468a8327',
    'c365f3ef3dc83b6c60e559719e13f1f0fa11aa12313c3fdfb0dd6ee99ca44962', 123)
pre_findings = ref(ROOT / pre_ns / 'findings.json', '43c9f39d64a4df256fd2fdbefed5dacab3be75a592e869082d9607fa312213fc')

failure_ref = copy_handler_ref({'path': (HP / 'failure-supplement-4799e19839904b2dab40249dbc44cbe0/failure_origins.json').as_posix(),
    'sha256': 'f7b962f6d2070dc6b32b6cd291766bd781aa87ad6c85dcd807863af23308e1f9'})
failures = load(failure_ref)
assert len(failures['new_batch_origins']) == 5 and failures['no_reset']
copy_handler_nested(failures)
new_rows = []
for row in failures['new_batch_origins']:
    assert row['result']['exit'] == load(row['invocation'])['exit'] == 1
    assert row['result']['input_count'] == 39069 and not row['result']['source_drift']
    assert row['source_before']['sha256'] == row['source_after']['sha256']
    new_rows.append({'origin_key': 'W05-99/handler-validation/' + row['origin_id'] + ':command',
        'evidence_ref': failure_ref, 'detail': {'actual_exit': 1, 'count_once_per_batch': True,
            'cause': row['cause'], 'result': row['result'], 'invocation': row['invocation'],
            'closed_snapshot_refs': row['closed_snapshot_refs'], 'binary_ref': row.get('binary_ref'), 'formal_increment': 0}})
new_rows.append({'origin_key': 'W05-99/handler-read-tool/b62571', 'evidence_ref': failure_ref, 'detail': failures['outer_tool_origin']})
f08_errors = ref(ROOT / f08_ns / 'read-errors.json', '7557e17c1b0570f9a43af01b52eaf62f55c751311c147916353950c50580d9fe')
for row in load(f08_errors)['entries']:
    if row.get('outer_exit_code') == 1:
        new_rows.append({'origin_key': 'W05-99/f08-closed-contract-read-tool/' + row['ref'], 'evidence_ref': f08_errors, 'detail': row})
    elif row.get('tool_failed'):
        cp['preserved_unindexed_tool_diagnostics'].append({'origin_key': 'W05-99/f08-closed-contract/' + row['ref'],
            'evidence_ref': f08_errors, 'actual_exit': None, 'tool_failed': True, 'detail': row,
            'no_native_exit_invented': True, 'formal_increment': 0})
new_rows.append({'origin_key': 'W05-99/root-read-tool/32c586-e41097', 'evidence_ref': None,
    'detail': {'actual_exit': 1, 'initial_chunk': '32c586', 'final_chunk': 'e41097',
        'cause': 'Broad rg used absent cwd integration_codex path, produced public metadata output truncated and native exit1. One continuous invocation, not two failures.',
        'raw_basis': 'Original native transcript only; no reconstructed stdout bytes.', 'product_tests': 0}})
boundary_errors_ref = ref(boundary_ns / 'read-errors.json')
for row in load(boundary_errors_ref)['events']:
    assert row['actual_outer_exit'] == 1
    new_rows.append({'origin_key': 'W05-99/fixture-boundary-read-tool/' + row['tool_result'], 'evidence_ref': boundary_errors_ref, 'detail': row})
old_failures = copy.deepcopy(cp['failure_counters'])
save('new_failure_origin_registration.json', {'origins': new_rows, 'actual_new_unique': len(new_rows),
    'unknown_exit_tool_failures_preserved_separately': 2, 'counter_reset': False})
origin_ref = ref(OUT / 'new_failure_origin_registration.json')
for row in new_rows:
    assert row['origin_key'] not in {old.get('origin_key') for old in cp['failure_counters']}
    if row['evidence_ref'] is None:
        row['evidence_ref'] = origin_ref
    cp['failure_counters'].append(dict(row, attempts=1, retries_used=0, status='ACTUAL_NONZERO_PRESERVED_SINGLE_CAUSE',
        count_once=True, counter_reset=False, formal_increment=0))
assert cp['failure_counters'][:289] == old_failures

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
for path, raw in before.items():
    with (OUT / (path.stem + '.original.json')).open('xb') as stream:
        stream.write(raw)
handler['paths'].extend(paths)
assert len(handler['paths']) == len(set(handler['paths'])) == 38
handler.update(state='EXACT38_HANDLER_CLI_CONFIGURATION_IMPLEMENTATION_AUTHORIZED_NOT_ACCEPTED',
    cli_product_amendment_ref=cli_scope_ref, fixture_boundary_amendment_ref=fixture_scope_ref,
    preliminary_handler_only_review_ref=pre_findings, final_source_ready=False)
f08 = ow['card_path_bindings']['W05-99']['subtasks']['f08_whole_scope_readonly_review']
f08.update(state='REVISED_WHOLE20_PENDING_FRESH_NONSELF_READONLY_REVIEW_NO_SOURCE_LEASE',
    revised20_proposal_ref=f08_proposal_ref, revised20_manifest_ref=f08_manifest,
    fresh_reviewer='codex:/root/w05_merge_review', SQL24_source_lease=False)
cp['work_in_progress'].update(configuration_handler_scope_state=handler['state'],
    configuration_cli_product_amendment_ref=cli_scope_ref, configuration_fixture_boundary_amendment_ref=fixture_scope_ref,
    configuration_handler_preliminary_review_ref=pre_findings, configuration_handler_failure_supplement_r296=failure_ref,
    f08_revised20_readonly_proposal_ref=f08_proposal_ref,
    pending_actual_failure_imports=['New author actual cohorts after sealed f7b supplement, if any; do not infer extra failures from nested events.'],
    next_action='Author completes exact38 CLI configuration plus owned P1 corrections, final full source freeze/actual matrix then nonauthor review. Fresh F08 whole20 readonly review runs in parallel; no SQL24 source lease yet. Provider whole9/source22 and Main23 final handler composition remain open.')
for row in cp['open_obligations_before_next_card']:
    if isinstance(row, dict) and row.get('kind') == 'CLI_CONFIGURATION_DEFAULT_AND_SCOPED_PUBLIC_CONTRACT':
        row.update(status='EXACT38_SOURCE_IMPLEMENTATION_AUTHORIZED_ACCEPTANCE_OPEN', resource_branch_only=False,
            scope_ref=cli_scope_ref, correction='Product scope gap, not a resource-only blocker. Original gap evidence retained.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'EXACT38_CLI_PRODUCT_AND_FIXTURE_BOUNDS_WITH_REVISED20_READONLY_INPUTS',
    'cli_scope_ref': cli_scope_ref, 'fixture_scope_ref': fixture_scope_ref,
    'failure_origins_before': 289, 'failure_origins_after': len(cp['failure_counters']),
    'Main_product_source_writes': 0, 'formal_increment': 0})
cp.update(revision=296, expected_previous_revision=295, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=124, amended_at=now, amended_by='codex:/root')
for row in [cli_scope_ref, fixture_scope_ref, cli_review_ref, boundary_review_ref, f08_manifest,
            f08_handoff, f08_proposal_ref, pre_manifest, pre_handoff, pre_findings, failure_ref, f08_errors, origin_ref]:
    if row['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(row['path'])
save('public_copy_audit.json', {'copies': copies, 'count': len(copies), 'Main_product_source_writes': 0,
    'CLI_review_manifest_entries_verified': 36, 'F08_namespace_files': 112, 'preliminary_namespace_files': 124})
save('record.json', {'checkpoint': [295, 296], 'ownership': [123, 124], 'failure_origins': [289, len(cp['failure_counters'])],
    'exact_source_paths': 38, 'CLI_scope': cli_scope_ref, 'fixture_scope': fixture_scope_ref,
    'F08_SQL24_source_lease': False, 'Main_source_writes': 0, 'formal_increment': 0})
assert all(path.read_bytes() == raw for path, raw in before.items())
assert subprocess.check_output(['git', 'status', '--porcelain=v1', '--untracked-files=no'], cwd=ROOT) == status
for path, value in zip(CANON[:2], [cp, ow]):
    temporary = path.with_name(path.name + '.root296.tmp')
    with temporary.open('xb') as stream:
        stream.write(encode(value))
    assert path.read_bytes() == before[path]
    os.replace(temporary, path)
assert all(path.read_bytes() == before[path] for path in CANON[2:])
print(json.dumps({'checkpoint': 296, 'ownership': 124, 'failure_origins': len(cp['failure_counters']),
    'CLI_scope_ref': cli_scope_ref, 'fixture_scope_ref': fixture_scope_ref,
    'Main_product_source_writes': 0, 'formal_increment': 0}, ensure_ascii=True))
