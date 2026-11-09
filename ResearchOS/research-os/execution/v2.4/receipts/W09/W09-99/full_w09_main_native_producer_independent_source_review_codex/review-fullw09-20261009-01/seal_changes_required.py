"""Seal the real peer-identity rejection and preserve the original failed invocation."""
import hashlib
import json
import os
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
R = Path('D:/作品集/ResearchOS/research-os')
S = R / 'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261009-01'
D = Path(__file__).resolve().parent
ACTOR = 'codex:/root/full_w09_source_review'

def pin(path):
    raw = Path(path).read_bytes()
    return dict(path=str(Path(path)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def load(path):
    return json.loads(Path(path).read_bytes())

def save(name, value):
    with (D / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
    return pin(D / name)

def tail_rows(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.readline()
        stream.seek(max(len(header), size - 64 * 1024 * 1024))
        if stream.tell() != len(header):
            stream.readline()
        offset = stream.tell()
        raw = stream.read(size - offset)
    rows = []
    for line in raw.splitlines(keepends=True):
        try:
            item = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            offset += len(line)
            continue
        rows.append((offset, line, item))
        offset += len(line)
    return header, rows, size

def capture_tool(header, pair, path, size, chunk, name, python_exit):
    call, result = pair
    target = D / (name + '.raw.jsonl')
    with target.open('xb') as stream:
        stream.write(header + call[1] + result[1])
    binding = dict(schema='researchos.independent-source-review.actual-hostpair.v1', actor_id=ACTOR,
        reviewer_thread_id=os.environ['CODEX_THREAD_ID'], source_audit_path=str(path), source_prefix_size_observed=size,
        source_line_offsets=[0, call[0], result[0]], source_line_bytes=[len(header), len(call[1]), len(result[1])],
        original_line_sha256=[hashlib.sha256(row).hexdigest() for row in (header, call[1], result[1])],
        original_capture_ref=pin(target), actual_call_id=call[2]['payload']['call_id'], actual_chunk_id=chunk,
        actual_outer_exit=python_exit, actual_Python_exit=python_exit,
        unobserved_Go_exit=None, unobserved_Native_exit=None, unobserved_SQL_exit=None,
        unobserved_dispatcher_exit=None, unobserved_model_exit=None, self_assigned_Root_ordinal=False)
    with path.open('rb') as stream:
        for offset, line in zip(binding['source_line_offsets'], (header, call[1], result[1])):
            stream.seek(offset)
            assert stream.read(len(line)) == line
    return save(name + '.binding.json', binding)

def main():
    choices = load(S / 'source.choice.json')
    contract = load(S / 'root-calling-contract.json')
    m = types.ModuleType('independent_rejection_runtime')
    m.__file__ = str(S / 'full_w09_runtime.source.py')
    exec(compile(Path(m.__file__).read_bytes(), m.__file__, 'exec'), m.__dict__)
    thread = os.environ['CODEX_THREAD_ID']
    matches = []
    for day in ('09', '10'):
        matches.extend(Path('C:/Users/yqyyds/.codex/sessions/2026/10/' + day).glob('rollout-*-' + thread + '.jsonl'))
    assert len(matches) == 1
    self_log = matches[0]
    header, rows, size = tail_rows(self_log)
    calls, pairs = {}, {}
    for row in rows:
        payload = row[2].get('payload', {})
        kind, cid = payload.get('type'), payload.get('call_id')
        if kind in ('function_call', 'custom_tool_call') and cid:
            calls[cid] = row
        elif kind in ('function_call_output', 'custom_tool_call_output') and cid in calls:
            for chunk in ('4dd2da', 'c33474'):
                if chunk in str(payload.get('output', '')):
                    pairs[chunk] = (calls[cid], row)
    assert set(pairs) == {'4dd2da', 'c33474'}
    failure_host_ref = capture_tool(header, pairs['4dd2da'], self_log, size, '4dd2da', 'actual-first-seal-failure-hostpair', 1)
    probe_host_ref = capture_tool(header, pairs['c33474'], self_log, size, 'c33474', 'actual-peer-identity-probe-hostpair', 0)
    failure_ref = save('original-new-failure-preserved.json', dict(
        schema='researchos.independent-source-review.original-failure.v1', actual_invocation_count=1, chunk_id='4dd2da',
        argv=['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe', '-I', '-S', '-B', '-X', 'utf8',
              str(D / 'seal_independent_source_review.py')], cwd='D:/作品集/ResearchOS', Python_exit=1, actual_outer_exit=1,
        exception_type='AssertionError', error='ACTUAL_SOURCE_AUTHOR_ROOT_DELIVERY', source_line=111,
        raw_actual_call_and_result_ref=failure_host_ref, automatic_retry=False, failure_reset=False,
        Root_failure_ordinal=1042, Root_failure_ordinal_assigned_by='codex:/root',
        Go_exit=None, Native_exit=None, SQL_exit=None, dispatcher_exit=None, model_exit=None,
        semantic_effect='Reviewer sealing failed before HDF/MF/decision; real peer inspection identified a Source contract bug.',
        same_invocation_not_retried=True))
    root_log = Path(m.ROOT_AUDIT)
    root_header, root_rows, root_size = tail_rows(root_log)
    digest = pin(S / 'HDF.json')['sha256']
    peer_pair = None
    for before, after in zip(root_rows, root_rows[1:]):
        payload = after[2].get('payload', {})
        if (before[2].get('type') == 'inter_agent_communication_metadata' and after[2].get('type') == 'response_item'
            and payload.get('type') == 'agent_message' and payload.get('author') == '/root/native_temp_independent_review'
            and payload.get('recipient') == '/root' and digest in after[1].decode()):
            peer_pair = (before, after)
    assert peer_pair
    call, result = peer_pair
    assert result[2]['ordinal'] == call[2]['ordinal'] + 1 and call[2]['timestamp'] == result[2]['timestamp']
    assert result[2]['metadata']['client_authored'] is False
    assert len(result[2]['payload']['content']) == 1 and result[2]['payload']['content'][0]['type'] == 'input_text'
    raw_path = D / 'actual-Source-author-real-Root-peer.raw.jsonl'
    with raw_path.open('xb') as stream:
        stream.write(root_header + call[1] + result[1])
    peer_ref = save('actual-Source-author-real-Root-peer.binding.json', dict(schema='researchos.w09-native-producer.actual-audit.v1',
        actor_id=m.AUTHOR, Root_thread_id=m.ROOT_THREAD_ID, source_audit_path=m.ROOT_AUDIT,
        source_line_offsets=[0, call[0], result[0]], original_line_sha256=[hashlib.sha256(row).hexdigest() for row in (root_header, call[1], result[1])],
        source_prefix_size_observed=root_size, original_capture_ref=pin(raw_path), binding_sha256=digest))
    with root_log.open('rb') as stream:
        for offset, line in zip([0, call[0], result[0]], (root_header, call[1], result[1])):
            stream.seek(offset)
            assert stream.read(len(line)) == line
    rejection = None
    try:
        m.actual_audit(peer_ref, m.AUTHOR, digest)
    except ValueError as exc:
        assert str(exc) == 'ACTUAL_PEER_DELIVERY'
        rejection = dict(exception_type=type(exc).__name__, error=str(exc))
    else:
        raise AssertionError('REAL_PEER_IDENTITY_BUG_NOT_REPRODUCED')
    finding = dict(id='SOURCE-BLOCKER-01', priority='BLOCKER', category='correctness',
        source_ref=pin(S / 'full_w09_runtime.source.py'), line=520,
        title='Canonical actor ID is compared directly with the real host task author',
        actual_actor_id=m.AUTHOR, actual_host_payload_author=result[2]['payload']['author'],
        actual_Source_delivery_ref=peer_ref, exact_Source_delivered_hash=digest,
        actual_host_observed_ordinal=result[2]['ordinal'], actual_host_observed_offset=result[0],
        reproduced_production_rejection=rejection,
        impact='Every actual Source-author audit in validate_authority fails before prepare/run; reviewer peer captures fail by the same rule.',
        suggested_change='Explicitly bind each canonical codex actor to its exact host task path for author/reviewer peer records. Validate canonical actor, actual host author, metadata/session/offset bytes, and artifact digest together.',
        required_control='Use this real author peer capture as a positive Source control; reject foreign task authors and wrong canonical actor mappings. Keep actual Root tool-pair validation separate.',
        author_control_gap='The 69 controls verify actual Root tool pairs; authority shape controls replace actual_audit with an in-memory mock. No actual peer-delivery positive control was exercised.')
    finding_ref = save('independent-real-peer-blocker.json', dict(status='CHANGES_REQUIRED', finding=finding,
        byte_exact_source_log_verified=True, actual_Go_runs=0, actual_Native_runs=0, execution_grant=False, formal_case_accepted_delta=0))
    gm = types.ModuleType('changes_required_final_guard')
    gm.__file__ = choices['common']['guard_ref']['path']
    assert pin(gm.__file__) == choices['common']['guard_ref']
    exec(compile(Path(gm.__file__).read_bytes(), gm.__file__, 'exec'), gm.__dict__)
    refs = [pin(S / 'HDF.json'), pin(S / 'MF.json'), *load(S / 'MF.json')['members'], *choices['common']['source21'],
            *[pin(path) for path in sorted(D.iterdir()) if path.is_file()]]
    guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    try:
        guard.acquire(refs)
        assert all(pin(ref['path']) == ref for ref in refs)
    finally:
        cleanup = guard.close()
        guard_ref = save('changes-required-final-Source-guard.closed.json', cleanup)
    assert cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count'] == 0
    bound = {key: pin(S / name) for key, name in contract['source_file_bindings'].items()}
    decision = dict(schema=contract['review_schema'], decision='CHANGES_REQUIRED', status='CHANGES_REQUIRED',
        actor_id=ACTOR, actor_role='INDEPENDENT_NON_AUTHOR', reviewer_thread_id=thread,
        source_handoff_ref=pin(S / 'HDF.json'), source_manifest_ref=pin(S / 'MF.json'), calling_contract_ref=pin(S / 'root-calling-contract.json'),
        **bound, selectors=choices['selectors'], source21=choices['common']['source21'], findings=[finding],
        independent_controls_ref=pin(D / 'independent-source-controls.json'), real_peer_blocker_ref=finding_ref,
        actual_reviewer_hostpair_ref=pin(D / 'actual-reviewer-control-hostpair.binding.json'),
        failure_hostpair_ref=failure_host_ref, identity_probe_hostpair_ref=probe_host_ref,
        actual_Source_author_peer_ref=peer_ref, original_new_failure_ref=failure_ref,
        final_guard_ref=guard_ref, next_stage_contract_ref=pin(D / 'Root-next-stage-required-fields.json'),
        author_controls_reproduced=69, independent_shape_checks_passed=112, actual_peer_audit_rejections=1,
        initial_shape_check_status='PASSED_BUT_SUPERSEDED_BY_REAL_PEER_BLOCKER',
        source_compiler_pins_verified=3905, source_allowed_package_upper_bound=353, actual_compiler_package_count=None,
        actual_executed=False, actual_Go_runs=0, actual_Native_runs=0, actual_SQL_runs=0, actual_dispatcher_runs=0, actual_model_provider_calls=0,
        execution_grant=False, formal_case_accepted_delta=0, formal_acceptance=False, parent_acceptance=False,
        Main_written=False, Canon_read=False, Canon_written=False, current_CanonicalPair_held=False,
        all_Source_guards_closed=True, retained_handles_count=0, automatic_retry=False,
        Source_original_failure_ordinals_preserved=[1026, 1029], new_real_invocation_failure_count=1,
        self_assigned_Root_ordinal=False, Root_assigned_original_failure_ordinal=1042, unknown_individual_child_exit=None,
        next_gate='Source author issues a new immutable Source revision and real peer positive/negative controls; independent review before Root Scope/request.',
        actualprepare_request_allowed=False, actualrun_request_allowed=False, sealed_stop=True)
    decision_ref = save('source-review-decision.json', decision)
    mf_ref = save('MF.json', dict(schema='researchos.w09-three-selector-independent-source-review-manifest.v1', actor_id=ACTOR,
        members=[pin(path) for path in sorted(D.iterdir()) if path.is_file()]))
    hdf_ref = save('HDF.json', dict(schema='researchos.w09-three-selector-independent-source-review-handoff.v1',
        actor_id=ACTOR, actor_role='INDEPENDENT_NON_AUTHOR', reviewer_thread_id=thread, status='CHANGES_REQUIRED',
        manifest_ref=mf_ref, source_decision_ref=decision_ref, source_handoff_ref=decision['source_handoff_ref'],
        source_manifest_ref=decision['source_manifest_ref'], calling_contract_ref=decision['calling_contract_ref'],
        real_peer_blocker_ref=finding_ref, original_new_failure_ref=failure_ref, final_guard_ref=guard_ref,
        actual_executed=False, execution_grant=False, formal_case_accepted_delta=0, formal_acceptance=False,
        Main_written=False, Canon_written=False, all_Source_guards_closed=True, retained_handles_count=0, sealed_stop=True,
        next_gate=decision['next_gate']))
    review, refs = m.pair(hdf_ref, mf_ref)
    assert decision_ref in refs and review['source_decision_ref'] == decision_ref
    print(json.dumps(dict(status='CHANGES_REQUIRED', HDF=hdf_ref, MF=mf_ref, decision=decision_ref,
        blocker_ref=finding_ref, original_new_failure_ref=failure_ref, source_author_actual_peer_ref=peer_ref,
        all_Source_guards_closed=True, retained_handles_count=0, actual_Go_runs=0, actual_Native_runs=0,
        formal_case_accepted_delta=0, execution_grant=False, STOP=True), ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
