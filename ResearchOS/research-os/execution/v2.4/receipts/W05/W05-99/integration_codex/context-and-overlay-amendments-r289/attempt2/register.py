import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path('D:/作品集/ResearchOS/research-os').resolve()
OUT = Path(__file__).resolve().parent
BASE = 'execution/v2.4/receipts/W05/W05-99/'
HW = ROOT / '.local/worktrees/codex-w0599-host-configuration-handler'
HD = BASE + 'host_configuration_handler_executor_codex/implementation-3bdbe91d2e444b809535f6a0ebb123ec/pending-command-design-2faaea34633241868bac771cc70054f4/'
PR = BASE + 'provider_typed_route_independent_replay_codex/7dcde82f-d47d-4c69-989f-3a1c59f929ab/'
CANON = [ROOT / ('execution/v2.4/' + n) for n in ['checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json']]


def encode(o):
    return (json.dumps(o, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def save(n, o):
    with (OUT / n).open('xb') as f:
        f.write(encode(o))


def ref(p, expected=None):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    b = p.read_bytes()
    h = hashlib.sha256(b).hexdigest()
    if expected:
        assert h == expected, str(p)
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': h, 'bytes': len(b)}


def check(item):
    actual = ref(item['path'])
    assert actual['sha256'] == item['sha256'] and actual['bytes'] == item['bytes'], item['path']


before = {p: p.read_bytes() for p in CANON}
cp, ow = [json.loads(before[p]) for p in CANON[:2]]
assert (cp['revision'], ow['revision'], len(cp['failure_counters'])) == (288, 116, 251)
head = subprocess.check_output(['C:/Program Files/Git/cmd/git.exe', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
assert head == '2cdb0d43d5a600eef13c8f1735946a9adf52d079'
design_original = ref(HW / HD / 'supplement.json', '8032644d5e07d817155e55e2d8ff2cd0e8ff0b4c08048de0c4183f77dcc990e5')
design = json.loads((ROOT / design_original['path']).read_bytes())
assert not design['product_context_changes_applied'] and len(design['inputs']) == 6
copy_rows = []
for p in sorted((HW / HD).rglob('*')):
    if not p.is_file():
        continue
    source = p.resolve()
    assert source.is_relative_to((HW / HD).resolve())
    rel = source.relative_to(HW.resolve())
    target = ROOT / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    b = p.read_bytes()
    if target.exists():
        assert target.read_bytes() == b
    else:
        with target.open('xb') as f:
            f.write(b)
    copy_rows.append({'source': ref(source), 'copy': ref(target)})
for row in design['inputs']:
    expected_live = 'dfbd323d8b74a91a78d5ed2c1bcced6996534c379e64b23009eb3331dde0dad9' if row['path'] == 'internal/domain/runtime_sessions_windows.go' else row['sha256']
    assert ref(HW / row['path'])['sha256'] == expected_live
    assert ref(HW / row['snapshot'])['sha256'] == row['sha256']
    if row['path'] == 'internal/domain/client_protocol_goal.go':
        assert ref(row['path'])['sha256'] == row['sha256']
goal_lines = (ROOT / 'internal/domain/client_protocol_goal.go').read_text(encoding='utf-8').splitlines()
assert 'AdmitTurn' in goal_lines[98] and 'UPDATE client_sessions SET goal_id=?,task_id=?' in goal_lines[114]
review_ref = ref(PR + 'review.json', 'fb7a04ae98e3ed6b9b8453771fe43d45fcbb173bc30c83da9989fad636a1ee68')
manifest_ref = ref(PR + 'manifest.json', '03ad2ea3c339c0705e7a483aeec4334f2d3f8310526710d77cdc3f07bbe150cd')
for row in json.loads((ROOT / manifest_ref['path']).read_bytes())['files']:
    check(row)
repair_ref = ref(PR + 'overlay-repair-proposal.json', '842284286d4516b48d0c04acf58283e3a394443d50081a6467578dc73bfc35a2')
failure_ref = ref(PR + 'failure_origins.json', '0738bd3b7bc32c5f7f91fe5b840ab87b37274ac9f438b693ed990fcd270cb698')
failure = json.loads((ROOT / failure_ref['path']).read_bytes())
origin = failure['origins'][0]
for k in ['invocation', 'result', 'stderr']:
    check(origin[k])
result = json.loads((ROOT / origin['result']['path']).read_bytes())
assert result['exit'] == 2 and origin['actual_native_exit'] == 2 and origin['outer_driver_exit'] == 1
stopped = json.loads((ROOT / review_ref['path']).read_bytes())
assert stopped['actual_cases'] == 0 and stopped['not_run_controls'] == 76 and not stopped['compiler_executed']
repair = json.loads((ROOT / repair_ref['path']).read_bytes())
assert len(repair['bounds']) == 2 and not repair['executed_repairs']
check(repair['source'])
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
handler = {'schema': 'researchos.root.handler-pending-command-contract-amendment.v1', 'actor': 'codex:/root',
    'executor': 'codex:/root/sources_parent_impl', 'at': now,
    'original_scope_ref': cp['work_in_progress']['configuration_handler_scope_ref'],
    'author_design_original_ref': design_original, 'author_design_copy_ref': ref(HD + 'supplement.json'),
    'source_paths_added': [], 'exact_source_count': 27, 'implementation_authorized': True,
    'allowed_paths': ['internal/domain/client_protocol.go', 'internal/domain/client_protocol_configuration.go', 'internal/domain/runtime_sessions_windows.go'],
    'allowed_functions': 'Owned Execute/handleWrite admission boundary, new private context helpers in owned new configuration file, AdmitTurn/sessionTaskRoute validator. No protected client_protocol_goal.go changes or other caller edits.',
    'contract': copy.deepcopy(design),
    'live_input_supplement': {'path': 'internal/domain/runtime_sessions_windows.go', 'design_snapshot_sha256': '5a3fef6fc9f380bf3a39606f5d978ddce1c883fa289ef74782e33902b4cbb95d', 'current_sha256': 'dfbd323d8b74a91a78d5ed2c1bcced6996534c379e64b23009eb3331dde0dad9', 'root_read_tool_chunk': '2b7a4f', 'actual_difference': 'Three lines in owned matchStoredClientConfiguration strengthen rejection when original COMPLETED host.configure exists but original configuration row is absent. Other five design inputs remain identical; pending context not applied. Root independently read exact diff, approved within existing27.'},
    'root_corrections': [
        'Actual protected buildFiniteClientGoal invokes AdmitTurn at99 and publishes session.task_id at115. Original111 design locator is retained, superseded only by this exact current-source correction.',
        'Pending evidence is unexported, defensive original raw, original Envelope.ContentHash, authenticated principal, same callerTx pointer, actual reserved globalidentity and actual pre-dispatch project membership sets. It is not a durable journal or ready flag.',
        'Use immutable revision1 Goal/Task/Requirement and complete passedTask vs real stored body, actual producer objective/contract refs/candidate/template/acceptance/stop constraints and exact new-object membership. Do not prove current creation by ID prefix/timestamp/current model head.',
        'Existing bound Task always uses original durable Session/globalidentity/creation/scopedconfigure proof. Fresh NORMAL uses exact request SID and existing creator plus same dispatch newTask/newGoal. goal.start recomputes protected digest formula; null request SID requires exactly one actual newSession and actual workspace authority and resolved model bindings.',
        'Draft=true, missing/foreign context, changed hash/principal/identity, otherSession/sharedref, preexistingTask pretending new, missing true model qualification/provenance, extranewobjects, wrong writer/rev/epoch or missing existing creator cannot receive pending exception.',
        'Keep actual rejection semantics by stage: pre-dispatch typed rejection rolls business back and commits only legal identity+journal; protected AdmitTurn Fault produces COMPLETED with BLOCKED Task, not REJECTED. Test actual outcome/counts and no runtime effect instead of forcing different behavior.',
        'After original response insertion/commit, validate real successful snapshot-derived creation chain; later worker scans use durable original chain, not ephemeral context. No caller-supplied evidence field, credential access or new table/API.',
        'All old eleven core PASS/current39066 input proofs remain immutable prior stage. After context source changes, freeze complete new source/tool/compiler/exe/SDK vector before authoritative new cases; preserve earlier raw/counters.'
    ], 'required_controls': design['refusals'], 'formal_increment': 0, 'source_acceptance': False}
save('handler_pending_scope_amendment.json', handler)
handler_ref = ref(OUT / 'handler_pending_scope_amendment.json')
overlay = {'schema': 'researchos.root.independent-overlay-prepare-recovery.v1', 'actor': 'codex:/root',
    'executor': 'codex:/root/w05_merge_review', 'at': now,
    'original_scope_ref': cp['work_in_progress']['provider_typed_route_independent_execution_scope_ref'],
    'stopped_review_ref': review_ref, 'failure_ref': failure_ref, 'repair_proposal_ref': repair_ref,
    'original_overlay_ref': repair['source'], 'exact_changes': repair['bounds'],
    'implementation_authorized': True, 'product_source_writes': 0,
    'write_scope': 'Only new review-owned immutable overlay/driver/spec namespace and own isolated cache. Preserve original bad overlay/raw/checkout exports. Exactly one missing outer loop brace plus correct Num(spec,key) int64/error validation; normal gofmt of that file allowed, no unrelated test/control semantics changes.',
    'validation': 'One preparation sequence gofmt -> actual go-list closure -> compile/freeze -> same76 single-case controls as r288. Before first case new exact overlay/driver/spec/complete compiler+source+tools+exe+SDK/7DB freeze. First unexpected still stops; no extra cases, source or schema changes.',
    'preregistered_progress': ['actual gofmt exit0', 'actual go-list exit0 with full closure', 'actual compile exit0 before case execution'],
    'same_control_budget': 76, 'previous_cases_executed': 0, 'automatic_retries': False,
    'previous_overlay_preparation_failure_count': 1, 'old_model_history_failures': 5, 'old_P1_failures': 3,
    'model_HTTP_Node_worker_paid_private_calls': 0, 'source_acceptance': False, 'formal_increment': 0}
save('overlay_prepare_scope_amendment.json', overlay)
overlay_ref = ref(OUT / 'overlay_prepare_scope_amendment.json')
save('handler-design-public-copy-audit.json', {'files': copy_rows, 'count': len(copy_rows), 'source_writes': 0})
old = copy.deepcopy(cp['failure_counters'])
key = 'W05-99/independent-provider-overlay/' + origin['origin_id']
assert key not in {r.get('origin_key') for r in old}
cp['failure_counters'].append({'origin_key': key, 'attempts': 1, 'retries_used': 0,
    'status': 'ACTUAL_INDEPENDENT_GOFMT_EXIT2_OUTER1_ONE_TOOLING_ORIGIN_NO_PRODUCT_CASE',
    'evidence_ref': failure_ref, 'detail': origin, 'count_once': True, 'product_test_failure': False,
    'counter_reset': False, 'formal_increment': 0})
root_failure_ref = ref(OUT.parent / 'register.invocation.json')
assert json.loads((ROOT / root_failure_ref['path']).read_bytes())['actual_exit'] == 1
root_origin_key = 'W05-99/Root/pending-scope-live-snapshot/' + root_failure_ref['sha256']
assert root_origin_key not in {r.get('origin_key') for r in cp['failure_counters']}
cp['failure_counters'].append({'origin_key': root_origin_key, 'attempts': 1, 'retries_used': 0, 'status': 'ACTUAL_ROOT_PRECAS_EXIT1_OWNED_LIVE_STRENGTHENING_VS_DESIGN_SNAPSHOT', 'evidence_ref': root_failure_ref, 'cause': 'Registration assumed all six actively constructed live sources were unchanged; one authorized missing-original-config guard was strengthened. No canonical mutation before failure, old design/raw retained, exact delta independently read in chunk2b7a4f.', 'product_test_failure': False, 'counter_reset': False, 'formal_increment': 0})
assert cp['failure_counters'][:251] == old and len(cp['failure_counters']) == 253
for p, b in before.items():
    with (OUT / (p.stem + '.original.json')).open('xb') as f:
        f.write(b)
sub = ow['card_path_bindings']['W05-99']['subtasks']
sub['host_configuration_public_handlers'].update(pending_command_amendment_ref=handler_ref)
sub['provider_typed_route_independent_replay'].update(state='OVERLAY_ONLY_CAUSAL_PREPARE_REPAIR_ONCE_AUTHORIZED_CASES0_OF76',
    preparation_amendment_ref=overlay_ref, stopped_review_ref=review_ref, preparation_failures=1)
cp['work_in_progress'].update(configuration_handler_pending_command_amendment_ref=handler_ref,
    provider_independent_overlay_prepare_amendment_ref=overlay_ref,
    provider_independent_stopped_review_ref=review_ref,
    f08_design_proposal_ref=ref(BASE + 'cancel_finalization_design_revision_codex/246ac4e22a3c48fe8d86753b44a6cd78/scope_proposal.json', '70dbfcec98e10f6872982daf03588746d3aa1bc90d7096c28f9b1e30ee5d24a6'),
    next_action='Implement authorized same27 private pending-command proof and independent overlay-only two-fix prepare sequence; full new freeze and bounded validation. F08 pure-UDF/producer supplemental readonly, awaiting handler freeze and nonauthor scope. No held retries/reset/formal credit.')
cp['integrity_events'].append({'at': now, 'actor': 'codex:/root', 'event': 'HANDLER_PENDING_COMMAND_SAME27_AND_PROVIDER_OVERLAY_PREPARE_TWO_BOUNDED_AMENDMENTS',
    'handler_amendment_ref': handler_ref, 'overlay_amendment_ref': overlay_ref, 'failure_origins': [251, 253], 'formal_increment': 0})
cp.update(revision=289, expected_previous_revision=288, head=head, updated_at=now, updated_by='codex:/root')
ow.update(revision=117, amended_at=now, amended_by='codex:/root')
for item in [handler_ref, overlay_ref, review_ref, failure_ref, repair_ref, design_original]:
    if item['path'] not in cp['evidence_index']:
        cp['evidence_index'].append(item['path'])
save('record.json', {'checkpoint': [288, 289], 'ownership': [116, 117], 'failure_origins': [251, 253],
    'handler_source_count': 27, 'overlay_exact_changes': 2, 'provider_case_runs': 0, 'formal_increment': 0})
assert all(p.read_bytes() == b for p, b in before.items())
for p, value in zip(CANON[:2], [cp, ow]):
    tmp = p.with_name(p.name + '.root289.tmp')
    with tmp.open('xb') as f:
        f.write(encode(value))
    assert p.read_bytes() == before[p]
    os.replace(tmp, p)
assert all(p.read_bytes() == before[p] for p in CANON[2:])
print(json.dumps({'checkpoint': 289, 'ownership': 117, 'failure_origins': 253,
    'handler_amendment_ref': handler_ref, 'overlay_amendment_ref': overlay_ref, 'formal_increment': 0}, ensure_ascii=True))
