import datetime, hashlib, json, sys, traceback
from pathlib import Path

R = Path('D:/作品集/ResearchOS/research-os')
Q = Path(__file__).resolve().parent
C = R / 'execution/v2.4/receipts/W05/W05-99/public22_to_main23_continuation_caller_source_codex/continue-20261010-01'
A = Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
ACTOR = 'codex:/root/backup_regression_resources'
THREAD = '01a11cee-bf59-7a01-be0e-9f799f9b1084'

def pin(path):
    raw = Path(path).read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def save(name, value):
    path = Q / name
    with path.open('xb') as f: f.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    return pin(path)

def walk(value):
    yield value
    if type(value) is dict:
        for child in value.values(): yield from walk(child)
    elif type(value) is list:
        for child in value: yield from walk(child)

def nested(value):
    for obj in walk(value):
        yield obj
        if type(obj) is str:
            decoder = json.JSONDecoder()
            for pos, char in enumerate(obj):
                if char not in '{[': continue
                try: child, end = decoder.raw_decode(obj, pos)
                except ValueError: continue
                if type(child) in (dict, list): yield from nested(child)

def actual_pairs(chunks):
    # Read only our own finite thread audit. Never open the Root audit named in Source.
    calls = {}; found = {}; seen = {}; offset = 0
    with A.open('rb') as f:
        prefix = A.stat().st_size
        header = f.readline(); offset = len(header)
        if json.loads(header)['payload']['id'] != THREAD: raise ValueError('OWN_AUDIT_THREAD')
        while offset < prefix:
            start = offset; line = f.readline(); offset += len(line)
            try: row = json.loads(line)
            except ValueError: continue
            payload = row.get('payload')
            if type(payload) is not dict: continue
            kind = payload.get('type')
            if kind in ('custom_tool_call', 'function_call'):
                calls[payload.get('call_id')] = (start, line, payload)
            if kind not in ('custom_tool_call_output', 'function_call_output'): continue
            call_id = payload.get('call_id')
            if call_id not in calls: continue
            if not any(chunk.encode('ascii') in line for chunk in chunks): continue
            candidates = {}
            for obj in nested(payload):
                if type(obj) is dict and obj.get('chunk_id') in chunks and 'exit_code' in obj and 'output' in obj:
                    candidates[obj['chunk_id']] = obj
            for chunk, actual in candidates.items():
                if chunk in found: raise ValueError('DUPLICATE_ACTUAL_HOST_OUTPUT_' + chunk)
                call_start, call_line, call = calls[call_id]
                raw_path = Q / ('actual-' + chunk + '.raw.jsonl')
                with raw_path.open('xb') as out: out.write(header + call_line + line)
                binding = dict(schema='researchos.independent-source-actual-tool-pair.v1', actor_id=ACTOR,
                    backend_actor='/root/backup_regression_resources', thread_id=THREAD,
                    source_audit_path=str(A), source_prefix_size_observed=prefix,
                    source_line_offsets=[0, call_start, start], call_id=call_id, tool_name=call.get('name'),
                    original_line_sha256=[hashlib.sha256(x).hexdigest() for x in (header, call_line, line)],
                    original_capture_ref=pin(raw_path), actual_host_chunk_id=chunk,
                    actual_outer_exit=actual['exit_code'], actual_python_exit=actual['exit_code'] if ('ROOT_PYTHON_EXIT='+str(actual['exit_code'])) in actual['output'].splitlines() else None,
                    Native=None, Go=None, SQL=None, model=None, TP=None, dispatcher=None)
                found[chunk] = save('actual-' + chunk + '.binding.json', binding)
    if set(found) != set(chunks): raise ValueError('MISSING_ACTUAL_TOOL_PAIR_' + ','.join(set(chunks)-set(found)))
    return found

def same(a, b):
    import ntpath
    return (ntpath.normcase(ntpath.normpath(a['path'])), a['sha256'], a['bytes']) == (ntpath.normcase(ntpath.normpath(b['path'])), b['sha256'], b['bytes'])

def main():
    h = json.loads((C / 'HDF.json').read_bytes())
    i = json.loads(Path(h['source_inputs_ref']['path']).read_bytes())
    delta = json.loads((Q / 'delta-review-result.json').read_bytes())
    resources = json.loads((Q / 'complete-resource-closure.json').read_bytes())
    cleanup = resources['guard_cleanup']
    if not (cleanup['closed'] is True and cleanup['retained_handles_count'] == 0 and cleanup['errors'] == []
            and all(e['verified'] and e['closed'] for e in cleanup['entries'])):
        raise ValueError('ACTUAL_RESOURCE_CLOSURE_REQUIRED')
    if not (delta['finding']['id'] == 'P22C-OBSERVATION-CLOSE-001' and len(delta['controls']) == 3
            and all(c['passed'] for c in delta['controls']) and delta['guard_cleanup']['closed'] is True):
        raise ValueError('THREE_NEW_SOURCE_COUNTEREXAMPLE_CONTROLS_REQUIRED')
    witness = json.loads(Path(resources['author_witness_ref']['path']).read_bytes())
    if witness['actor_id'] != h['source_author'] or witness['Root_thread_id'] != '01a11007-5233-7ca1-b71f-9e9e5ce84c98' or witness['binding_sha256'] != h['calling_contract_ref']['sha256']:
        raise ValueError('REAL_AUTHOR_WITNESS_BINDING')
    raw = Path(witness['original_capture_ref']['path']).read_bytes()
    lines = [json.loads(x) for x in raw.splitlines()]
    metadata, final = lines[1], lines[2]
    if not (final['payload']['author'] == '/root/attach_restore_independent_review' and final['payload']['recipient'] == '/root'
            and final['metadata']['client_authored'] is False and metadata['timestamp'] == final['timestamp']):
        raise ValueError('TRUE_ADJACENT_SOURCE_BACKEND_IDENTITY')
    content = final['payload']['content']
    text = '\n'.join(c['text'] for c in content if c.get('type') == 'input_text')
    expected = 'Message Type: FINAL_ANSWER\nTask name: /root\nSender: /root/attach_restore_independent_review\nPayload:\n'
    payload_text = text[len(expected):] if text.startswith(expected) else text
    published = json.loads(payload_text)
    for ref in (pin(C/'HDF.json'), pin(C/'MF.json'), h['calling_contract_ref']):
        if not any(type(v) is dict and set(v) == {'path','sha256','bytes'} and same(v, ref) for v in walk(published)):
            raise ValueError('PUBLISHED_SOURCE_STRUCTURED_REF_BINDING')
    pairs = actual_pairs({'3047d2', '924cd3', '18f298', '9e5fbb'})
    reviewed = datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')
    decision = dict(schema='researchos.public22-continuation-root-independent-source-decision.v1',
        actor_id=ACTOR, actor_role='INDEPENDENT_NON_AUTHOR', source_author=h['source_author'],
        decision='SOURCE_CHANGES_REQUIRED', execution_grant=False, formal_acceptance=False,
        original1025_result='FAILED_RETAINED', continuation_only=True, runtime_closure_reviewed=False,
        source_hdf_ref=pin(C/'HDF.json'), source_mf_ref=pin(C/'MF.json'), caller_ref=h['caller_ref'],
        source_inputs_ref=h['source_inputs_ref'], calling_contract_ref=h['calling_contract_ref'],
        runtime_resources_ref=i['runtime_resources_ref'], main23_bound_ref=i['main23_bound_ref'],
        existing22_decision_ref=i['existing22_decision_ref'], reviewed_utc=reviewed,
        findings=[delta['finding']], new_source_controls_ref=pin(Q/'delta-review-result.json'),
        declared_public_resource_closure_ref=pin(Q/'complete-resource-closure.json'),
        actual_source_guard_cleanup_refs=[pin(Q/'delta-sourceguard.closed.json'), pin(Q/'complete-resource-sourceguard.closed.json')],
        actual_source_tool_pairs=pairs, original_tool_io_ref=pin(Q/'original-tool-io.reencoded.json'),
        real_source_author_capture_ref=resources['author_witness_ref'], real_source_author_raw_ref=resources['author_raw_ref'],
        protected_original_results=dict(original1025='FAILED_RETAINED', old_four_native_children_replayed=False,
            original_counter_reset=False, full20to24='OPEN', formal_case_delta=0),
        verified_scope=dict(phases=['upgrade22to23','backup23','verify23'], phase_timeout_seconds=90,
            original_db_backup_and_key_paths_not_replaced=True, new_working22_is_byte_identical_guarded_copy=True,
            new_candidate23_and_backup23_and_verify23_paths_are_one_shot=True, current4_runtime_CAS_required=True,
            Root_finite_scope_lease_owner_and_worker_required=True, preentry_complete_Root_capture_required=True,
            Main23_bound_programme_reuse_only_when_source_programme_and_review_exact_pins_still_match=True,
            no_private_owner_key_content_access_by_reviewer=True, no_SQL_connections=True, no_product_execution=True),
        resource_review_limits=dict(declared_unique_public_resource_pins_verified=len(cleanup['entries']),
            declared_runtime_manifest_resource_count=149, Source_resource_count=620,
            passive_current_process_module_inventory_only=True, future_Root_CLI_loaded_resource_gate_NOT_EXECUTED=True,
            reviewer_instrumentation_imports_produced_extra_loaded_files=resources['loaded_resources_missing_from_runtime_manifest'],
            extra_imports_are_not_claimed_as_Source_runtime_regression=True,
            resource_qualification_not_execution_authorization=True),
        minimum_revision='Move fact persistence inside output context immediately after returned run_owned observation, before either context __exit__; retain output close/hash errors independently and never replace observed actual_exit/OwnedJob cleanup with NULL.',
        required_after_revision='New immutable Source, exact inverse, only necessary close-fault delta controls, real non-author Source review and future Root finite Scope/resource rebinding before three new children.',
        forbidden_here=['Root stage calls','Go','Native','SQL','model','TP','Main or Canon mutation','private Owner/key byte access'],
        source_branch_only=True,
        reviewer_original_failures=[dict(original_ordinal=1181, actual_host_chunk_id='9e5fbb', actual_outer_exit=1, actual_python_exit=1,
            original_host_pair_ref=pairs['9e5fbb'], original_io_ref=pin(Q/'original9e5fbb.fullIO.reencoded.json'),
            failed_script_ref=pin(Q/'seal_review.py'), inverse_ref=pin(Q/'sealer-revision-inverse.json'),
            explanation='Reviewer sealer over-required direct caller_ref publication. The actual FINAL correctly published HDF/MF/contract and HDF transitively binds caller. Source finding and original failure counters remain unchanged.')])
    decision_ref = save('decision.json', decision)
    members = [pin(p) for p in sorted(Q.iterdir(), key=lambda p:p.name) if p.is_file() and p.name not in ('MF.json','HDF.json')]
    mf_ref = save('MF.json', dict(schema='researchos.independent-source-review-manifest.v1', actor_id=ACTOR, members=members))
    hdf_ref = save('HDF.json', dict(schema='researchos.public22-continuation-independent-source-HDF.v1', actor_id=ACTOR,
        reviewed_utc=reviewed, source_decision_ref=decision_ref, manifest_ref=mf_ref,
        source_hdf_ref=decision['source_hdf_ref'], source_mf_ref=decision['source_mf_ref'],
        caller_ref=h['caller_ref'], source_inputs_ref=h['source_inputs_ref'], calling_contract_ref=h['calling_contract_ref'],
        actual_source_tool_pairs=pairs, all_acquired_source_guards_closed=True, retained_handles_count=0,
        SourceAuthor_and_reviewer_distinct=True, Root_runtime_execution_grant=False, formal_acceptance=False))
    print(json.dumps(dict(schema='researchos.independent-source-review-FINAL.v1', actor_id=ACTOR,
        decision='SOURCE_CHANGES_REQUIRED', HDF_ref=hdf_ref, MF_ref=mf_ref, decision_ref=decision_ref,
        caller_ref=h['caller_ref'], calling_contract_ref=h['calling_contract_ref'], new_controls=3,
        verified_public_resources=len(cleanup['entries']), all_guards_closed=True, execution_grant=False, formal_acceptance=False), ensure_ascii=False))
    return 0

if __name__ == '__main__':
    rc = 1
    try: rc = main()
    except BaseException: traceback.print_exc()
    print('ROOT_PYTHON_EXIT=' + str(rc))
    sys.exit(rc)
