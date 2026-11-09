"""Seal an independent Source decision and exact current host records; grant nothing."""
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
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def load(path):
    return json.loads(Path(path).read_bytes())

def save(name, value):
    with (D / name).open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode())
    return pin(D / name)

def tail_rows(path, cap=64 * 1024 * 1024):
    size = path.stat().st_size
    with path.open('rb') as stream:
        header = stream.readline()
        stream.seek(max(len(header), size - cap))
        if stream.tell() != len(header):
            stream.readline()
        start = stream.tell()
        raw = stream.read(size - start)
    rows = []
    offset = start
    for line in raw.splitlines(keepends=True):
        try:
            row = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            offset += len(line)
            continue
        rows.append((offset, line, row))
        offset += len(line)
    return header, rows, size

def write_capture(name, header, call, result):
    path = D / name
    with path.open('xb') as stream:
        stream.write(header + call[1] + result[1])
    return pin(path)

def main():
    controls = load(D / 'independent-source-controls.json')
    assert controls['status'] == 'ACCEPTED_SOURCE_ONLY' and controls['new_failure_count'] == 0
    assert controls['all_Source_guards_closed'] is True and controls['retained_handles_count'] == 0
    choices = load(S / 'source.choice.json')
    contract = load(S / 'root-calling-contract.json')
    m = types.ModuleType('review_seal_runtime')
    m.__file__ = str(S / 'full_w09_runtime.source.py')
    exec(compile(Path(m.__file__).read_bytes(), m.__file__, 'exec'), m.__dict__)
    thread = os.environ['CODEX_THREAD_ID']
    matches = []
    for day in ('09', '10'):
        matches.extend(Path('C:/Users/yqyyds/.codex/sessions/2026/10/' + day).glob('rollout-*-' + thread + '.jsonl'))
    assert len(matches) == 1, 'EXACT_REVIEWER_SESSION_LOG'
    self_log = matches[0]
    header, rows, size = tail_rows(self_log)
    assert json.loads(header)['payload']['id'] == thread
    calls = {}
    control_pair = None
    for row in rows:
        payload = row[2].get('payload', {})
        kind, cid = payload.get('type'), payload.get('call_id')
        if kind in ('function_call', 'custom_tool_call') and cid:
            calls[cid] = row
        elif kind in ('function_call_output', 'custom_tool_call_output') and cid in calls:
            output = str(payload.get('output', ''))
            if '5e4da8' in output and 'Python_exit=0' in output:
                control_pair = (calls[cid], row)
    assert control_pair, 'ACTUAL_REVIEWER_CONTROL_TOOL_PAIR'
    call, result = control_pair
    raw_ref = write_capture('actual-reviewer-control-hostpair.raw.jsonl', header, call, result)
    binding = dict(schema='researchos.independent-source-review.actual-hostpair.v1', actor_id=ACTOR,
        reviewer_thread_id=thread, source_audit_path=str(self_log), source_prefix_size_observed=size,
        source_line_offsets=[0, call[0], result[0]], source_line_bytes=[len(header), len(call[1]), len(result[1])],
        original_line_sha256=[hashlib.sha256(row).hexdigest() for row in (header, call[1], result[1])],
        original_capture_ref=raw_ref, actual_call_id=call[2]['payload']['call_id'], actual_chunk_id='5e4da8',
        actual_outer_exit=0, actual_Python_exit=0, unobserved_Go_exit=None, unobserved_Native_exit=None,
        unobserved_SQL_exit=None, unobserved_dispatcher_exit=None, unobserved_model_exit=None,
        self_assigned_Root_ordinal=False)
    with self_log.open('rb') as stream:
        for offset, original in zip(binding['source_line_offsets'], (header, call[1], result[1])):
            stream.seek(offset)
            assert stream.read(len(original)) == original
    host_ref = save('actual-reviewer-control-hostpair.binding.json', binding)
    # Independently inspect the actual Source-author delivery already present in the real Root host log.
    root_log = Path(m.ROOT_AUDIT)
    root_header, root_rows, root_size = tail_rows(root_log)
    author_hash = pin(S / 'HDF.json')['sha256']
    peer_pair = None
    for previous, current in zip(root_rows, root_rows[1:]):
        before, after = previous[2], current[2]
        payload = after.get('payload', {})
        if (before.get('type') == 'inter_agent_communication_metadata' and after.get('type') == 'response_item'
            and payload.get('type') == 'agent_message' and payload.get('author') == m.AUTHOR
            and payload.get('recipient') == '/root' and author_hash in current[1].decode()):
            peer_pair = (previous, current)
    assert peer_pair, 'ACTUAL_SOURCE_AUTHOR_ROOT_DELIVERY'
    call, result = peer_pair
    peer_raw = write_capture('actual-Source-author-Root-peer.raw.jsonl', root_header, call, result)
    peer_ref = save('actual-Source-author-Root-peer.binding.json', dict(schema='researchos.w09-native-producer.actual-audit.v1',
        actor_id=m.AUTHOR, Root_thread_id=m.ROOT_THREAD_ID, source_audit_path=m.ROOT_AUDIT,
        source_line_offsets=[0, call[0], result[0]], original_line_sha256=[hashlib.sha256(row).hexdigest() for row in (root_header, call[1], result[1])],
        source_prefix_size_observed=root_size, original_capture_ref=peer_raw, binding_sha256=author_hash))
    assert m.actual_audit(peer_ref, m.AUTHOR, author_hash) == [peer_ref, peer_raw]
    # A hash change or author substitution cannot qualify this actual peer capture.
    rejection_rows = []
    original_read = m.read_ref
    peer = load(peer_ref['path'])
    for name, key, value in [('peer_wrong_actor', 'actor_id', ACTOR), ('peer_wrong_binding', 'binding_sha256', '0' * 64),
                             ('peer_false_offset', 'source_line_offsets', [0, call[0] + 1, result[0]])]:
        bad = dict(peer)
        bad[key] = value
        in_memory_ref = dict(path=str(D / ('IN_MEMORY_' + name)), sha256='0' * 64, bytes=0)
        m.read_ref = lambda ref, bad=bad, fake=in_memory_ref: json.dumps(bad).encode() if ref == fake else original_read(ref)
        try:
            m.actual_audit(in_memory_ref, m.AUTHOR, author_hash)
        except (ValueError, KeyError, TypeError) as exc:
            rejection_rows.append(dict(name=name, status='REJECTED_SOURCE_ONLY', exception_type=type(exc).__name__, error=str(exc)))
        else:
            raise AssertionError(name + '_ACCEPTED')
        finally:
            m.read_ref = original_read
    save('independent-actual-peer-controls.json', dict(actual_Source_author_peer_audit_ref=peer_ref,
        actual_original_bytes_verified=True, controls=rejection_rows, current_Root_execution_authority=False,
        reviewer_Root_delivery_must_be_captured_after_actual_sealed_delivery=True, actual_Go_runs=0, actual_Native_runs=0,
        execution_grant=False, formal_case_accepted_delta=0))
    # Final guard holds all reviewed Source inputs and this review's current evidence, excluding live Canon.
    gm = types.ModuleType('review_final_guard')
    gm.__file__ = choices['common']['guard_ref']['path']
    assert pin(gm.__file__) == choices['common']['guard_ref']
    exec(compile(Path(gm.__file__).read_bytes(), gm.__file__, 'exec'), gm.__dict__)
    refs = [pin(S / 'HDF.json'), pin(S / 'MF.json'), *load(S / 'MF.json')['members'], *choices['common']['source21'],
            *[pin(path) for path in sorted(D.iterdir()) if path.is_file()]]
    guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    try:
        guard.acquire(refs)
        assert all(pin(ref['path']) == ref for ref in refs), 'FINAL_SOURCE_REVIEW_INPUT_DRIFT'
    finally:
        cleanup = guard.close()
        final_guard_ref = save('independent-final-Source-guard.closed.json', cleanup)
    assert cleanup['closed'] is True and cleanup['retained_handles_count'] == 0 and not cleanup['errors']
    bound = {key: pin(S / name) for key, name in contract['source_file_bindings'].items()}
    decision = dict(schema=contract['review_schema'], decision=contract['review_decision'], status='ACCEPTED_SOURCE_ONLY',
        actor_id=ACTOR, actor_role='INDEPENDENT_NON_AUTHOR', reviewer_thread_id=thread,
        source_handoff_ref=pin(S / 'HDF.json'), source_manifest_ref=pin(S / 'MF.json'), calling_contract_ref=pin(S / 'root-calling-contract.json'),
        **bound, selectors=choices['selectors'], source21=choices['common']['source21'],
        actual_executed=False, formal_case_accepted_delta=0, formal_acceptance=False, parent_acceptance=False, execution_grant=False,
        independent_controls_ref=pin(D / 'independent-source-controls.json'), actual_peer_controls_ref=pin(D / 'independent-actual-peer-controls.json'),
        actual_reviewer_hostpair_ref=host_ref, source_author_actual_Root_peer_ref=peer_ref,
        final_guard_ref=final_guard_ref, next_stage_contract_ref=pin(D / 'Root-next-stage-required-fields.json'),
        author_controls_reproduced=69, independent_additional_controls=controls['independent_additional_controls'] + len(rejection_rows),
        source_compiler_pins_verified=3905, source_allowed_package_upper_bound=353, actual_compiler_package_count=None,
        findings=[], review_dimensions=['correctness', 'frozen_scope', 'actual_host_audit', 'Canon_owner_lease',
             'Windows_owned_Job_exit_cleanup', 'new_two_package_compiler_test_variant_qualification', 'maintainability'],
        strengths=['Original invocation failures remain primary; independent archive/close failures stay secondary.',
             'Owned Job closure requires typed PID and uint64 FILETIME and all mandatory cleanup flags.',
             'All three selectors bind the complete Main roster, six required package variants, unique fresh output/cache paths.'],
        limitations=['This decision accepts Source only. No actual Go/Native, SQL, dispatcher, provider or formal case was executed.',
             'Synthetic authority/compiler/cleanup counterexamples prove parser shape only; they provide no current Root authority or product PASS.',
             'MR2 qualifies prior C19 modes only and cannot supply retrieval test variants or a complete reusable two-package test program.',
             'Root must capture this sealed actual peer delivery, issue a fresh per-selector Scope/lease/current Canon vector, then request prepare/run.',
             'Actual Native, current evidence closure and independent ModeProof remain required before formal consumer acceptance.'],
        actual_Go_runs=0, actual_Native_runs=0, actual_SQL_runs=0, actual_dispatcher_runs=0, actual_model_provider_calls=0,
        Main_written=False, Canon_written=False, current_CanonicalPair_held=False, all_Source_guards_closed=True, retained_handles_count=0,
        original_failure_ordinals_preserved=[1026, 1029], new_failure_count=0, automatic_retry=False, self_assigned_Root_ordinal=False,
        unknown_individual_child_exit=None, sealed_stop=True)
    decision_ref = save('source-review-decision.json', decision)
    mf_ref = save('MF.json', dict(schema='researchos.w09-three-selector-independent-source-review-manifest.v1', actor_id=ACTOR,
        members=[pin(path) for path in sorted(D.iterdir()) if path.is_file()]))
    hdf_ref = save('HDF.json', dict(schema='researchos.w09-three-selector-independent-source-review-handoff.v1', actor_id=ACTOR,
        actor_role='INDEPENDENT_NON_AUTHOR', reviewer_thread_id=thread, status='ACCEPTED_SOURCE_ONLY', manifest_ref=mf_ref,
        source_decision_ref=decision_ref, source_handoff_ref=decision['source_handoff_ref'], source_manifest_ref=decision['source_manifest_ref'],
        calling_contract_ref=decision['calling_contract_ref'], actual_reviewer_hostpair_ref=host_ref,
        source_author_actual_Root_peer_ref=peer_ref, independent_controls_ref=decision['independent_controls_ref'],
        final_guard_ref=final_guard_ref, next_stage_contract_ref=decision['next_stage_contract_ref'],
        actual_executed=False, formal_case_accepted_delta=0, formal_acceptance=False, execution_grant=False,
        Main_written=False, Canon_written=False, all_Source_guards_closed=True, retained_handles_count=0, sealed_stop=True,
        next_gate='Root capture actual sealed reviewer delivery; Root-issued fresh per-selector Scope/request/vector/lease before prepare/run.'))
    hdf, members = m.pair(hdf_ref, mf_ref)
    assert decision_ref in members and hdf['source_decision_ref'] == decision_ref
    assert load(decision_ref['path'])['selectors'] == choices['selectors']
    print(json.dumps(dict(status='ACCEPTED_SOURCE_ONLY', HDF=hdf_ref, MF=mf_ref, decision=decision_ref,
        reviewer_thread_id=thread, source_author_actual_Root_peer_ref=peer_ref, actual_reviewer_hostpair_ref=host_ref,
        author_controls_reproduced=69, independent_checks=decision['independent_additional_controls'],
        all_Source_guards_closed=True, retained_handles_count=0, execution_grant=False, formal_case_accepted_delta=0,
        actual_Go_runs=0, actual_Native_runs=0, STOP=True), ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
