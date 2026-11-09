"""Independent Source-only review. No Root grants, products, TP or live Canon."""
import ast
import copy
from datetime import datetime, timezone
import hashlib
import json
import ntpath
from pathlib import Path
import re
import types

R = Path('D:/作品集/ResearchOS/research-os')
B = R / 'execution/v2.4/receipts/W05/W05-99'
Q = B / 'schema21_root_caller_registration_source_codex/s21root-20261010-01'
N = B / 'schema21_root_caller_registration_independent_source_review_codex/review-s21root-20261010-01'
ROOT_LOG = Path('C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl')
G = B / 'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
AUTHOR = 'codex:/root/full_w09_source_review'
ROOT_THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
checks = []
findings = []
closure = None

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=path.as_posix(), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def normalized(ref):
    return dict(path=str(Path(ref['path'])), sha256=ref['sha256'], bytes=ref['bytes'])

def load_json(path):
    return json.loads(Path(path).read_bytes())

def save(name, value):
    path = N / name
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return pin(path)

def note(name, passed, **detail):
    checks.append(dict(name=name, passed=bool(passed), **detail))

def expect_reject(name, action, expected):
    try:
        action()
    except (ValueError, TypeError, KeyError) as exc:
        note(name, expected in str(exc), rejection=str(exc), expected=expected)
    else:
        note(name, False, rejection=None, expected=expected)

def import_inert(path, name):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(Path(path).read_bytes(), str(path), 'exec'), module.__dict__)
    return module

def capture_existing_builder_final():
    """Capture real Root reception, never issue a Root binding/witness."""
    size = ROOT_LOG.stat().st_size
    lower = max(0, size - 64 * 1024 * 1024)
    found = None
    with ROOT_LOG.open('rb') as stream:
        header = stream.readline()
        stream.seek(lower)
        if lower:
            stream.readline()
        previous = None
        while stream.tell() < size:
            offset = stream.tell()
            line = stream.readline()
            if offset + len(line) > size:
                break
            row = json.loads(line)
            payload = row.get('payload')
            if type(payload) is dict and row.get('type') == 'response_item' and payload.get('type') == 'agent_message' and payload.get('author') == AUTHOR.removeprefix('codex:') and payload.get('recipient') == '/root':
                content = payload.get('content')
                if type(content) is list and len(content) == 1 and type(content[0]) is dict:
                    body = content[0].get('text')
                    envelope = 'Message Type: FINAL_ANSWER\nTask name: /root\nSender: ' + AUTHOR.removeprefix('codex:') + '\nPayload:\n'
                    if type(body) is str and body.startswith(envelope):
                        try:
                            delivery = json.loads(body[len(envelope):])
                        except (ValueError, TypeError):
                            delivery = None
                        if type(delivery) is dict and delivery.get('component') == 'OLD21_PROGRAMME_BUILDER_SOURCE':
                            if previous and previous[2].get('type') == 'inter_agent_communication_metadata':
                                found = (header, previous, (offset, line, row), delivery)
            previous = (offset, line, row)
    if found is None:
        raise ValueError('EXISTING_TASK68_ROOT_FINAL_NOT_FOUND')
    header, first, last, delivery = found
    offsets = [0, first[0], last[0]]
    lines = [header, first[1], last[1]]
    with ROOT_LOG.open('rb') as stream:
        for offset, line in zip(offsets, lines):
            stream.seek(offset)
            if stream.readline() != line:
                raise ValueError('ORIGINAL_ROOT_FINAL_OFFSET_DRIFT')
    raw_path = N / 'actual-Task68-Root-received-Final.raw.jsonl'
    with raw_path.open('xb') as stream:
        stream.write(b''.join(lines))
    binding = dict(schema='researchos.independent-actual-peer-observation.v1', observed_by=AUTHOR,
        root_thread_id=ROOT_THREAD, source_audit_path=ROOT_LOG.as_posix(),
        source_prefix_size_observed=size, source_line_offsets=offsets,
        source_line_bytes=[len(x) for x in lines], original_line_sha256=[hashlib.sha256(x).hexdigest() for x in lines],
        original_capture_ref=pin(raw_path), peer_actor=AUTHOR, message_id=last[2]['payload']['id'],
        received_at=last[2]['timestamp'], original_metadata_ordinal=first[2]['ordinal'],
        original_delivery_ordinal=last[2]['ordinal'], issued_by_Root=False,
        Root_witness=False, Root_authorization=False, formal_acceptance=False, execution_grant=False)
    binding_ref = save('actual-Task68-Root-received-Final.observation.json', binding)
    return binding, binding_ref, first[2], last[2], delivery

try:
    assert pin(G)['sha256'] == 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'
    assert pin(G)['bytes'] == 11404
    g = import_inert(G, 'independent_source_guard')
    closure = g.SourceReadGuard(per_file_cap=512 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    hdf_ref = pin(Q / 'HDF.json'); mf_ref = pin(Q / 'MF.json')
    assert hdf_ref['sha256'] == '82b5f5af96d0fe62d4fa968181e061423595a670f9bcec63230effbcfe9c0b58' and hdf_ref['bytes'] == 9999
    assert mf_ref['sha256'] == 'c5cf3440f97f0b9daa909c6287cec73c6fc2f7d85e33f38d568e8a49d9251a63' and mf_ref['bytes'] == 45184
    source = load_json(Q / 'HDF.json'); mf = load_json(Q / 'MF.json')
    inputs = load_json(source['source_inputs_ref']['path'])
    ref_inputs = [hdf_ref, mf_ref, pin(G)] + mf['members'] + inputs['references']
    builder_review_refs = source['known_builder_Source_review_refs']
    ref_inputs += list(builder_review_refs.values())
    observed_binding, observed_binding_ref, first, last, delivery = capture_existing_builder_final()
    ref_inputs += [observed_binding_ref, observed_binding['original_capture_ref']]
    refs = {}
    live_paths = {ntpath.normcase(ntpath.normpath(str(R / x))) for x in ('execution/v2.4/checkpoint.json', 'execution/v2.4/path_ownership.json')}
    for ref in ref_inputs:
        ref = normalized(ref)
        key = ntpath.normcase(ntpath.normpath(ref['path']))
        if key in live_paths:
            raise ValueError('LIVE_CANON_REF_FORBIDDEN_IN_SOURCE_REVIEW')
        if key in refs and refs[key] != ref:
            raise ValueError('SOURCE_REFERENCE_PIN_CONFLICT')
        refs[key] = ref
    closure.acquire(list(refs.values()))
    note('complete new Caller MF members and explicit Source input refs held', True,
        members=len(mf['members']), distinct_held_refs=len(refs), live_Canon_held=0)
    m = import_inert(Q / 'old21_root.source.py', 'old21_independent_Source_only')
    caller_ref = pin(Q / 'old21_root.source.py'); contract = load_json(Q / 'root-calling-contract.source.json')
    note('exact Caller and contract final refs', caller_ref['sha256'] == '2d63900e47dbb27dee7a06a98884ca11c8d4dcc167d867c993ccd7d745ac0249' and caller_ref['bytes'] == 63407 and pin(Q / 'root-calling-contract.source.json')['sha256'] == 'f0ba2fe3bee58f0f90ed4be81c4967bbdb1ba965af8aad878deeda0adea42732')
    br = {k: load_json(ref['path']) for k, ref in builder_review_refs.items()}
    bs = load_json(source['builder_source_hdf_ref']['path']); bmf = load_json(source['builder_source_mf_ref']['path']); bc = load_json(bs['contract_ref']['path'])
    def builder_check(decision=br['decision'], review=br['hdf'], review_mf=br['mf'], source_doc=bs, source_mf=bmf, builder_contract=bc, review_refs=builder_review_refs):
        return m.validate_builder_chain(review_refs, review, review_mf, decision, source_doc, source_mf, builder_contract)
    builder_check()
    note('actual sealed Task68 HDF/MF/decision + fixed Native builder chain', True, builder853_reexecuted=False)
    for actor in (m.ROOT, m.CALLER_AUTHOR, m.BUILDER_AUTHOR, 'anonymous'):
        d = copy.deepcopy(br['decision']); h = copy.deepcopy(br['hdf'])
        d['review_author'] = h['review_author'] = actor
        expect_reject('non-author builder review rejects ' + actor, lambda d=d, h=h: builder_check(decision=d, review=h), 'BUILDER_NONAUTHOR_REQUIRED')
    bad_contract = copy.deepcopy(bc); bad_contract['schema_version'] = 23
    expect_reject('schema23 cannot qualify old21', lambda: builder_check(builder_contract=bad_contract), 'BUILDER_CONTRACT_CHAIN')
    d = copy.deepcopy(br['decision']); d['execution_grant'] = True
    expect_reject('builder Source review grants forbidden', lambda: builder_check(decision=d), 'SOURCE_REVIEW_NOT_PROGRAMME_QUALIFICATION')
    for text, code in (('{"a":1,"a":2}', 'DUPLICATE_JSON_KEY'), ('{"a":NaN}', 'NONFINITE_NUMBER'), ('{"a":1} trailing', 'Extra data')):
        expect_reject('strict JSON rejects ' + code, lambda text=text: m.strict(text), code)
    expect_reject('public22 authority cannot authorize old21', lambda: m.public371_evidence(), 'PUBLIC22_SCOPE_CANNOT_AUTHORIZE_OLD21')
    tree = ast.parse((Q / 'old21_root.source.py').read_bytes())
    functions = {x.name: x for x in tree.body if isinstance(x, ast.FunctionDef)}
    base_tree = ast.parse(Path(source['base_caller_ref']['path']).read_bytes())
    base_functions = {x.name: x for x in base_tree.body if isinstance(x, ast.FunctionDef)}
    for name in ('strict', 'structured_documents', 'original_capture_rows', 'failure_rows'):
        note(name + ' exact inherited M4 AST', ast.dump(functions[name], include_attributes=False) == ast.dump(base_functions[name], include_attributes=False), legacy_source=True)
    decode = copy.deepcopy(functions['validate_peer_delivery'])
    decode.name = 'source_only_peer_interface'
    start = next(i for i, node in enumerate(decode.body) if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'payload' for t in node.targets))
    decode.body = decode.body[start:]
    decode.args = ast.arguments(posonlyargs=[], args=[ast.arg(arg=x) for x in ('binding', 'first', 'last', 'expected_refs', 'peer_actor', 'operation')], kwonlyargs=[], kw_defaults=[], defaults=[])
    module = ast.fix_missing_locations(ast.Module(body=[decode], type_ignores=[]))
    namespace = dict(m.__dict__)
    exec(compile(module, '<Source-only exact peer interface AST; no Root binding issuance>', 'exec'), namespace)
    peer = namespace['source_only_peer_interface']
    expected = list(builder_review_refs.values())
    actual_delivery_refs = delivery.get('review_refs')
    note('real Root received Task68 full refs exact; backend identity+metadata', m.exact_ref_set(actual_delivery_refs) == m.exact_ref_set(expected) and first['ordinal'] + 1 == last['ordinal'] and first['timestamp'] == last['timestamp'] and last['metadata']['client_authored'] is False,
        observation_ref=observed_binding_ref, peer_schema=delivery['schema'], peer_operation=delivery['operation'])
    expect_reject('existing genuine Task68 Final is rejected by new Caller', lambda: peer(observed_binding, first, last, expected, AUTHOR, 'BUILDER_SOURCE_REVIEW_WITNESS'), 'PEER_TYPED_DELIVERY_REQUIRED')
    findings.append(dict(id='OLD21_BUILDER_LEGACY_TYPED_DELIVERY_INCOMPATIBLE', severity='BLOCKER', lines=[179, 282, 286],
        actual_schema=delivery['schema'], actual_operation=delivery['operation'], actual_component=delivery.get('component'),
        required_schema='researchos.old21-peer-review-delivery.v2', required_operation='BUILDER_SOURCE_REVIEW_WITNESS',
        observation_ref=observed_binding_ref, diagnostic='Actual existing Builder review full references are correct but strict new peer schema refuses its already sealed normal Final.',
        minimum_fix='Add a role-specific exact legacy Builder delivery branch, restricted to the actual component, reviewer, Root thread and fixed accepted three refs; preserve anchored whole JSON, original bytes/offsets, sender/recipient/message-id/metadata and Root capture causality. Fresh Caller/runtime deliveries retain their own strict schema. Do not reseal the 853 Builder checks.'))
    # Explicit in-memory Source controls only, never a real peer delivery or Root witness.
    fixture_delivery = copy.deepcopy(delivery)
    fixture_delivery.update(schema='researchos.old21-peer-review-delivery.v2', operation='BUILDER_SOURCE_REVIEW_WITNESS')
    fixture_last = copy.deepcopy(last)
    envelope = 'Message Type: FINAL_ANSWER\nTask name: /root\nSender: ' + AUTHOR.removeprefix('codex:') + '\nPayload:\n'
    fixture_last['payload']['content'][0]['text'] = envelope + json.dumps(fixture_delivery, ensure_ascii=False, indent=2)
    peer(observed_binding, first, fixture_last, expected, AUTHOR, 'BUILDER_SOURCE_REVIEW_WITNESS')
    note('Source-only modern peer body conditional interface positive', True, synthetic_control_only=True, Root_delivery_grant=False)
    for key, val in (('author', '/root/anonymous'), ('recipient', '/root/other'), ('type', 'message')):
        changed = copy.deepcopy(fixture_last); changed['payload'][key] = val
        expect_reject('Source-only peer wrong ' + key, lambda changed=changed: peer(observed_binding, first, changed, expected, AUTHOR, 'BUILDER_SOURCE_REVIEW_WITNESS'), 'ACTUAL_PEER_DELIVERY_REQUIRED')
    for label, suffix in (('trailing', ' trailing'), ('duplicate', ',"schema":"duplicated"}')):
        changed = copy.deepcopy(fixture_last)
        if label == 'trailing':
            changed['payload']['content'][0]['text'] += suffix
        else:
            changed['payload']['content'][0]['text'] = changed['payload']['content'][0]['text'].rstrip()[:-1] + suffix
        expect_reject('Source-only peer ' + label + ' JSON', lambda changed=changed: peer(observed_binding, first, changed, expected, AUTHOR, 'BUILDER_SOURCE_REVIEW_WITNESS'), 'PEER_TYPED_DELIVERY_REQUIRED')
    archives = {x['key']: load_json(x['snapshot_ref']['path']) for x in source['current_before_archive_refs']}
    cp, ow = archives['checkpoint'], archives['path_ownership']
    current_counter = cp['work_in_progress']['root_next_failure_ordinal_live']
    pending = dict(issued_by=m.ROOT, counter_reset=False, pending=[], next_original_failure_ordinal=current_counter-1, Source_only_in_memory_fixture=True)
    original_doc = m.doc
    m.doc = lambda ref: copy.deepcopy(pending)
    try:
        returned, pending_refs = m.failure_rows(hdf_ref, cp)
    finally:
        m.doc = original_doc
    scope_ref = hdf_ref
    owner = dict(scope_ref=scope_ref, selected_worker_id=m.ROOT, Source_only_in_memory_fixture=True)
    worker = dict(scope_ref=scope_ref, selected_owner_ref=mf_ref, worker_id=m.ROOT, Source_only_in_memory_fixture=True)
    after_cp, after_ow = m.projection(cp, ow, scope_ref, mf_ref, caller_ref, hdf_ref, owner, worker, returned, datetime.now(timezone.utc).isoformat())
    note('pure empty-pending counter rollback reproduced with actual archived start', after_cp['work_in_progress']['root_next_failure_ordinal_live'] == current_counter-1,
        before_counter=current_counter, supplied_next=current_counter-1, after_counter=after_cp['work_in_progress']['root_next_failure_ordinal_live'],
        synthetic_in_memory_only=True, live_Canon_read_or_write=False, actual_TP_called=False)
    note('rollback fixture leaves every preexisting failure row unchanged', m.encoded(cp['failure_counters']) == m.encoded(after_cp['failure_counters']))
    findings.append(dict(id='OLD21_EMPTY_PENDING_COUNTER_ROLLBACK', severity='BLOCKER', inherited_M4=True, lines=[469, 496],
        before_counter=current_counter, supplied_next=current_counter-1, accepted_after_counter=current_counter-1,
        contract_line=336, diagnostic='pending=[] equals an empty decreasing range and is accepted; pure projection then overwrites the actual counter with a smaller value.',
        minimum_fix='Require type(next_original_failure_ordinal) is int and next >= start before constructing range, reject bool; require pending ordinals to be exact ints. Add the same monotonic precondition to projection because it is a pure public callback. Preserve NULL exits and SHA+selector once-only append; reject negative/decreasing/boolean next for empty pending, allow same next only for truly empty pending.'))
    # M4 true-time condition extracted verbatim; no runtime qualification is created.
    time_need = next(node for node in functions['runtime_review_chain'].body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call) and any(isinstance(arg, ast.Constant) and arg.value == 'RUNTIME_ORIGINAL_REVIEW_ISSUANCE_TIME_ORDER' for arg in node.value.args))
    condition = compile(ast.Expression(time_need.value.args[0]), '<exact inherited causal time condition>', 'eval')
    stamps = ['2026-10-09T00:00:0' + str(i) + '+00:00' for i in range(7)]
    time_env = dict(m.__dict__, scope={'created_utc':stamps[0]}, review={'reviewed_utc':stamps[1]}, received=m.when(stamps[2]), qualification={'payload_created_utc':stamps[3],'created_utc':stamps[6]}, root_binding={'tool_call_timestamp':stamps[4],'tool_result_timestamp':stamps[5]})
    note('payload/Root observation/wrapper strict causal condition executable', eval(condition, time_env), synthetic_condition_only=True)
    wrong = copy.deepcopy(time_env['qualification']); wrong['created_utc'] = '2999-01-01T00:00:00+00:00'
    note('future wrapper time rejected', not eval(condition, dict(time_env, qualification=wrong)), synthetic_condition_only=True)
    wrong = copy.deepcopy(time_env['qualification']); wrong['payload_created_utc'] = stamps[5]
    note('payload after Root call rejected', not eval(condition, dict(time_env, qualification=wrong)), synthetic_condition_only=True)
    note('Source old failed guard UNKNOWN preserved', source['Source_old_failed_guard_status'] == 'UNKNOWN_NOT_SERIALIZED', original_failures=source['old_original_failures'], historical_guards_not_retroactively_closed=True)
    own_operation = [x.value for x in ast.walk(functions['own_review']) if isinstance(x, ast.Constant) and x.value == 'SOURCE_REVIEW_WITNESS']
    note('Root Task70 operation correction agrees with actual Caller contract', len(own_operation) == 1 and 'SOURCE_REVIEW_WITNESS' in m.CAPTURE_OPERATIONS, rejected_task_operation_was_Root_instruction_error=True, not_a_Source_blocker=True)
    result = dict(schema='researchos.old21-independent-caller-finite-Source-review.v1', review_author=AUTHOR,
        source_hdf_ref=hdf_ref, source_mf_ref=mf_ref, caller_ref=caller_ref, calling_contract_ref=pin(Q/'root-calling-contract.source.json'),
        checks=checks, check_count=len(checks), unexpected_check_failures=sum(not x['passed'] for x in checks),
        blocking_findings=findings, verdict='CHANGES_REQUIRED', independent_non_author=True,
        actual_Task68_peer_observation_ref=observed_binding_ref,
        reused_builder_review_refs=builder_review_refs, builder853_controls_reexecuted=False,
        Source_only=True, in_memory_controls_are_not_Root_grants=True,
        actual_Go_Native_SQL_model_dispatcher_TP_calls=0, live_Canon_held=0,
        execution_grant=False, formal_acceptance=False, programme_qualification_ref=None)
    result_ref = save('finite-Source-review.json', result)
finally:
    if closure is not None:
        closed = closure.close()
        guard_ref = save('independent-Source-guard.closed.json', closed)
        if not closed['closed'] or closed['retained_handles_count'] or closed['errors']:
            raise ValueError('INDEPENDENT_SOURCE_GUARD_NOT_CLOSED')
if any(not x['passed'] for x in checks):
    raise ValueError('UNEXPECTED_REVIEW_CONDITION_FAILED')
print(json.dumps(dict(result_ref=result_ref, guard_ref=guard_ref, checks=len(checks), blockers=len(findings), verdict='CHANGES_REQUIRED', Source_only=True, closed0=True), ensure_ascii=False))
