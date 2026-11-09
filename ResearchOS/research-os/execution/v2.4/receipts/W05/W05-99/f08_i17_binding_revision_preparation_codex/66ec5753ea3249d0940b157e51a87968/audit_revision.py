"""Author's static byte/data evidence only, never independent acceptance."""
from pathlib import Path
import ast
import base64
import copy
from datetime import datetime
import hashlib
import json
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_io import OUT, PRIOR, REVIEW, ACTOR, ref, checked, load, compact, dump, apply_unified, functions, byte_body_record, source_rules, shape

def main():
    group = load(OUT/'source-group.json')
    prior_group = load(PRIOR/'source-group.json')
    original_raw = checked(group['producer_tests']['before'])
    new_raw = checked(group['producer_tests']['after'])
    prior_raw = checked(prior_group['producer_tests']['after'])
    assert b'\r' not in original_raw and b'\r' not in new_raw
    assert new_raw == prior_raw.replace(b'\r\n', b'\n')
    original_functions, new_functions = functions(original_raw), functions(new_raw)
    old_tests = sorted(n for n in original_functions if n.startswith('Test'))
    assert len(old_tests) == 28
    raw_bodies = [byte_body_record(original_functions, new_functions, n) for n in old_tests]
    for name in ['f08FullJournalDataFixture','f08TestDataSetup','step','put','graph','materialize','f08FixtureClone']:
        body = new_functions[name]['raw']
        assert b'evaluate(' not in body and b'f08BuildCallbacks(' not in body, name
    assert b'bytes.Clone(raw)' in new_functions['step']['raw']
    assert b'frames=append' in new_functions['step']['raw']
    replay = new_functions['f08FullJournalFixture']['raw']
    assert replay.index(b'f08FullJournalDataFixture') < replay.index(b'.evaluate(')
    assert b'f08Strict(' not in new_functions['f08FixtureClone']['raw']

    driver_before_raw = checked(group['driver_test_contract']['before'])
    driver_after_raw = checked(group['driver_test_contract']['after'])
    assert group['driver_test_contract'] == prior_group['driver_test_contract']
    assert driver_after_raw == checked(prior_group['driver_test_contract']['after'])
    driver_before, driver_after = functions(driver_before_raw), functions(driver_after_raw)
    driver_names = ['TestDriverI%02d' % n for n in range(1,19) if n != 17]
    driver_bodies = [byte_body_record(driver_before, driver_after, n) for n in driver_names]
    assert len(driver_bodies) == 17
    # I18 entire raw function body, including the full negative disclosure/assertions.
    i18 = next(r for r in driver_bodies if r['name'] == 'TestDriverI18')
    assert b'direct!=nil||directErr==nil||directErr.Error()!=v.FixedCallbackError' in driver_after['TestDriverI17']['raw']
    assert b'var driver18F08Bindings func()' in driver_after_raw
    assert group['driver_test_contract']['original_controller'] == 'UNCHANGED'
    assert group['driver_test_contract']['I17_original_adapter'] == 'still nil FATAL_OPEN'

    source_raw = checked(group['production_callback']['after'])
    assert source_raw == checked(prior_group['production_callback']['after'])
    assert group['production_callback']['before'] == group['production_callback']['after']
    assert group['driver_source'] == prior_group['driver_source']
    checked(group['driver_source']['after'])
    assert group['original_DDL34'] == prior_group['original_DDL34']
    checked(group['original_DDL34'])
    assert group['domain_harness'] == prior_group['domain_harness']
    harness = checked(group['domain_harness']['after'])
    functions(harness)
    assert harness.startswith(b'package domain\n')
    for literal in [b'f08BuildCallbacks(backupConfigurationProtocol,backupConfigurationDomain)',
        b'direct!=nil||e==nil||e.Error()!=v.FixedCallbackError', b'native.Code()&255',
        b'after!=count', b'PRAGMA trusted_schema=OFF', b'flags!=2099200', b'FATAL_OPEN']:
        assert literal in harness, literal
    assert b'RegisterFunction(' not in harness and b'os/exec' not in harness
    assert not re.search(rb'\bfunc\s+F08\w*', harness)
    source_functions = functions(source_raw)
    assert b'case 5:e=v.journal(s,action,old,row)' in source_functions['evaluate']['raw']
    assert b'if e!=nil{return nil,e};return int64(1),nil' in source_functions['evaluate']['raw']
    assert b'if err != nil { return nil, err }' in source_functions['f08Boundary']['raw']
    assert b'c[2]!=settling' in source_functions['f08Pending']['raw']
    lines = source_raw.decode('utf-8').splitlines()
    for line_no, text in [(785,'len(rows)!=len(g.members)'),(788,'len(pins)!=len(g.pins)'),
        (1435,'q!=row[4]'),(1499,'f08RetainedColumns(old,row,6)'),(1522,'c[8]!="CONFIRMED"')]:
        assert text in lines[line_no-1] and 'f08Binding' in lines[line_no-1]

    changes = load(OUT/'changes.json')
    assert len(changes) == 8
    for change in changes:
        a, b = checked(change['before']), checked(change['after'])
        assert apply_unified(a, checked(change['forward'])) == b
        assert apply_unified(b, checked(change['inverse'])) == a
    metadata_changes = load(OUT/'metadata-script-fix.json')['changes']
    assert len(metadata_changes) == 3
    for change in metadata_changes:
        a, b = checked(change['before']), checked(change['after'])
        assert apply_unified(a, checked(change['forward'])) == b
        assert apply_unified(b, checked(change['inverse'])) == a

    prior_vector_raw = checked(prior_group['raw_vectors'])
    vectors_raw = checked(group['raw_vectors'])
    suffix = b'\n  ],\n  "formal_acceptance": false,'
    prior_at, after_at = prior_vector_raw.index(suffix), vectors_raw.index(suffix)
    assert vectors_raw[:prior_at] == prior_vector_raw[:prior_at]
    assert vectors_raw[after_at:] == prior_vector_raw[prior_at:]
    prior_manifest, manifest = json.loads(prior_vector_raw), json.loads(vectors_raw)
    assert manifest['vectors'][:109] == prior_manifest['vectors']
    assert len(manifest['vectors']) == 114
    assert manifest['schema'] == 'researchos.f08.i17.vector-manifest.v1'
    assert manifest['producer_ref'] == prior_manifest['producer_ref']
    assert manifest['formal_acceptance'] is False and manifest['SQL24_complete'] is False
    assert manifest['all_expected_results'] == 'SOURCE_INFERENCE_NOT_RUN'
    all_ids = set()
    function_counts = {name: 0 for name in manifest['names']}
    blob_refs = 0
    for v in manifest['vectors']:
        assert v['id'] not in all_ids
        all_ids.add(v['id']); function_counts[v['function']] += 1
        assert v['corrupt_kind'] == 'CALLBACK_ERROR' and v['expected_sqlite_primary_code'] == 1
        assert v['sqlite_code_evidence'] == 'SOURCE_INFERENCE_NOT_NATIVE_RUN'
        assert v['status'] == 'SOURCE_DERIVED_NOT_RUN'
        assert v['valid_expected'] == {'driver_type': 'int64', 'value': 1}
        assert v['provenance']['predicate_executions'] == 0
        for arg in v['valid'] + v['corrupt']:
            if arg['kind'] == 'BLOB':
                checked(arg['ref']); blob_refs += 1
            else:
                assert arg['kind'] in ['INTEGER','NULL','TEXT']
    assert list(function_counts.values()) == [4,5,105]
    prior_BLOB_arg_occurrences = sum(a['kind']=='BLOB' for v in prior_manifest['vectors'] for a in v['valid']+v['corrupt'])
    assert blob_refs == prior_BLOB_arg_occurrences + 2*len(manifest['vectors'][109:])
    dispatch_controls = [v for v in manifest['vectors'][:109] if v['function'].endswith('proof_v1')]
    assert len(dispatch_controls) == 100
    for v in dispatch_controls:
        good, bad = json.loads(checked(v['valid'][1]['ref'])), json.loads(checked(v['corrupt'][1]['ref']))
        assert bad['action'] == 'unbound.action' and v['fixed_callback_error'] == 'F08_MODE'
        bad['action'] = good['action']
        assert bad == good

    # New mutations are independently read back; reversing exactly one fact must
    # reproduce the baseline's full raw bytes. No actual evaluator is called.
    plan = load(REVIEW/'minimum-source-fact-plan.json')
    cases = load(OUT/'source-fact-cases.json')['cases']
    new = manifest['vectors'][109:]
    assert [v['id'] for v in new] == [c['id'] for c in plan['cases']]
    assert len(cases) == 5
    rules = source_rules(source_raw)
    static_results = []
    for v, c, p in zip(new, cases, plan['cases']):
        assert v['valid'][0] == v['corrupt'][0] == {'kind':'INTEGER','integer':5}
        assert v['valid'][1]['kind'] == v['corrupt'][1]['kind'] == 'BLOB'
        assert v['valid'][1]['ref'] == p['baseline']
        good_raw, bad_raw = checked(v['valid'][1]['ref']), checked(v['corrupt'][1]['ref'])
        good, bad = json.loads(good_raw), json.loads(bad_raw)
        assert good_raw == compact(good) and bad_raw == compact(bad)
        shape(good, rules); shape(bad, rules)
        assert good['action'] == bad['action'] == p['action']
        assert set(good) == set(bad) == {'action','row','old','sources'}
        assert good['old'] == bad['old']
        restored = copy.deepcopy(bad)
        mutation = v['mutation']
        cause = {'id': v['id'], 'single_changed_fact': mutation['path'], 'mode_action_unchanged': True,
            'shape_type_unique_keys_preserved': True, 'expected_fixed_error': 'F08_ORIGINAL_BINDING',
            'expected_good': 'int64(1),nil error', 'expected_bad': 'nil,F08_ORIGINAL_BINDING',
            'source_expected_ONLY': True, 'actual_callback_run': None}
        locator = good['row'][:4] if good['action']=='commit.insert' else [good['row'][0],good['row'][1],good['row'][3],good['row'][4]]
        parents = {cat: [r for cat2,r in good['sources'] if cat2==cat and r[:4]==locator] for cat in ['admitted','final']}
        assert len(parents['admitted']) == len(parents['final']) == 1
        admitted, final = parents['admitted'][0], parents['final'][0]
        admitted_doc, final_doc = json.loads(bytes.fromhex(admitted[8])), json.loads(bytes.fromhex(final[7]))
        members = [r for cat,r in good['sources'] if cat=='final_members' and r[:4]==locator]
        admitted_pins = [r for cat,r in good['sources'] if cat=='pins' and r[:4]==locator and r[4]=='ADMITTED']
        final_pins = [r for cat,r in good['sources'] if cat=='pins' and r[:4]==locator and r[4]=='FINALIZED']
        assert len(members) == len(final_doc['members']) == 1
        assert len(admitted_pins) == len(admitted_doc['pins']) == 6
        assert len(final_pins) == len(final_doc['pins']) == 9
        assert final_doc['root']['member_count'] == len(final_doc['members'])
        controls = [r for cat,r in good['sources'] if cat=='controls' and [r[0],r[1],r[2],r[5]]==locator]
        assert len(controls)==1 and controls[0][8]=='CONFIRMED'
        cause['baseline_structural_counts'] = {'final_members':1,'admitted_pins':6,'final_pins':9,'control_state':'CONFIRMED'}
        if mutation['operation'] == 'remove_one_tuple':
            assert good['row'] == bad['row']
            index = int(mutation['path'].split('/')[-1])
            assert len(good['sources']) == len(bad['sources']) + 1
            assert good['sources'][index] == mutation['before']
            restored['sources'].insert(index, copy.deepcopy(mutation['before']))
            if v['id'] == 'proof-commit-missing-admitted-pin':
                bad_count = sum(cat=='pins' and r[:4]==locator and r[4]=='ADMITTED' for cat,r in bad['sources'])
                assert bad_count == 5 and len(admitted_doc['pins']) == 6
                cause.update({'baseline_count':6,'bad_count':5,'document_expected_count':6,
                    'genuine_fault': 'finalGroup:1368 -> completeMaterializations:788'})
            else:
                bad_count = sum(cat=='final_members' and r[:4]==locator for cat,r in bad['sources'])
                assert bad_count == 0 and len(final_doc['members']) == 1
                cause.update({'baseline_count':1,'bad_count':0,'document_expected_count':1,
                    'genuine_fault': 'completedJournal:1521 -> completeMaterializations:785'})
        elif v['id'] == 'proof-commit-control-not-confirmed':
            index = int(mutation['path'].split('/')[2])
            assert good['row'] == bad['row'] and bad['sources'][index][1][8]=='RECONCILING'
            assert good['sources'][index][1][2]==locator[2]
            restored['sources'][index][1][8] = 'CONFIRMED'
            cause.update({'original_and_final_response_cells_retained': True,
                'settling_control_skipped_by_f08Pending': True,
                'genuine_fault': 'completedJournal:1522 CONFIRMED predicate'})
        elif v['id'] == 'proof-journal-retained-original-header-field':
            assert good['sources'] == bad['sources']
            header0, header1 = json.loads(bytes.fromhex(good['row'][7])), json.loads(bytes.fromhex(bad['row'][7]))
            for header, row in [(header0,good['row']),(header1,bad['row'])]:
                assert list(header) == ['schema','encoding','raw_envelope_base64']
                assert header['schema']=='researchos.private-command-envelope.v1' and header['encoding']=='base64'
                assert compact(header,False)==bytes.fromhex(row[7])
                raw = base64.b64decode(header['raw_envelope_base64'],validate=True)
                assert base64.b64encode(raw).decode('ascii') == header['raw_envelope_base64']
                assert len(raw) <= 1048576 and len(header['raw_envelope_base64']) <= 1398104 and len(bytes.fromhex(row[7])) <= 1398200
            env0 = json.loads(checked(mutation['original_envelope_ref']))
            env1 = json.loads(checked(mutation['changed_envelope_ref']))
            assert list(env0) == list(env1) == ['protocol_version','command_id','client_id','project_id','session_id','expected_revision','writer_epoch','method','payload']
            delta = [key for key in env0 if env0[key] != env1[key]]
            assert delta == ['expected_revision'] and env0['expected_revision']==7 and env1['expected_revision']==8
            schema = load(Path(manifest['source_ref']['path']).parent/'27-015-client.protocol.schema.json')
            revision_branch = schema['$defs']['CommandEnvelope']['properties']['expected_revision']['anyOf'][0]
            assert revision_branch == {'type':'integer','minimum':1}
            assert type(env1['expected_revision']) is int and env1['expected_revision'] >= revision_branch['minimum']
            assert env1['protocol_version']=='researchos-client/2' and env1['method']=='session.control'
            assert env1['project_id']==bad['row'][1] and env1['command_id']==bad['row'][3]
            assert env1['payload']==env0['payload'] and env1['session_id']==env0['session_id']
            q0 = 'sha256:' + hashlib.sha256(compact(env0)).hexdigest()
            q1 = 'sha256:' + hashlib.sha256(compact(env1)).hexdigest()
            assert q0==good['row'][4]==bad['row'][4] and q1!=q0
            assert good['row'][7]==good['old'][7]==admitted[5]
            restored['row'][7] = good['row'][7]
            cause.update({'original_request_hash':q0,'mutated_envelope_ContentHash_source_reconstruction':q1,
                'request_hash_retained':True,'legal_revision_schema_branch':revision_branch,
                'schema_validation_runtime':None,'private_header_order_and_padded_base64_valid':True,
                'other_envelope_fields_byte_order_and_values_retained':True,
                'genuine_fault': 'journalEnvelope:1435 decoded.ContentHash mismatch'})
        elif v['id'] == 'proof-journal-retained-timestamp':
            assert good['sources'] == bad['sources']
            for timestamp in [good['row'][8],bad['row'][8],good['old'][8]]:
                assert datetime.fromisoformat(timestamp.replace('Z','+00:00')).isoformat().endswith('+00:00')
            assert good['row'][8]==good['old'][8] and bad['row'][8]!=good['old'][8]
            # journal.update retains the original source row exactly, and only
            # response body column6 is the existing allowed transition delta.
            original_source = [r for cat,r in good['sources'] if cat=='idempotency' and r[:4]==good['old'][:4]]
            assert original_source == [good['old']]
            assert [i for i,(a,b) in enumerate(zip(good['old'],good['row'])) if a!=b] == [6]
            assert [i for i,(a,b) in enumerate(zip(bad['old'],bad['row'])) if a!=b] == [6,8]
            restored['row'][8] = good['row'][8]
            cause.update({'OLD_and_source_ACK_timestamp_retained':True,
                'allowed_existing_body_change_column':6,'one_new_retained_column_change':8,
                'genuine_fault':'journal:1499 f08RetainedColumns(old,row,6)'})
        else:
            raise AssertionError(v['id'])
        assert restored == good and compact(restored) == good_raw
        assert c['expected_direct_bad'] == {'value':None,'error':'F08_ORIGINAL_BINDING'}
        assert v['fixed_callback_error']=='F08_ORIGINAL_BINDING'
        assert c['actual_callback_result'] is None and c['actual_native_run'] is None
        for item in c['source_lines']:
            assert item['text'] == lines[item['line']-1]
        cause['single_fact_inverse_reproduces_full_baseline_raw_bytes'] = True
        static_results.append(cause)

    sequences = load(PRIOR/'raw-sequences.json')
    assert group['raw_sequences'] == prior_group['raw_sequences']
    sequence_counts = [len(s['frames']) for s in sequences['sequences']]
    assert sequence_counts == [24,24,26,26]
    for s in sequences['sequences']:
        assert not s['actual_sql_native_capture']
        for frame in s['frames']:
            checked(frame['go_producer_raw'])
            assert not frame['sql_native_bytes_proven'] and not frame['storage_types_before_cast_runtime_proven']
    inputs_before, inputs_after = load(OUT/'inputs.before.json'), load(OUT/'inputs.after.json')
    assert inputs_before == inputs_after
    for r in inputs_before:
        checked(r)
    scope = load(OUT/'scope-and-open.json')
    assert scope['remaining_FATAL_OPEN'] == load(PRIOR/'scope-and-open.json')['remaining_FATAL_OPEN']
    assert scope['non_author_remaining_FATAL_OPEN_verbatim'] == load(REVIEW/'source-review.json')['remaining_FATAL_OPEN']
    assert not scope['source_acceptance'] and not scope['formal_acceptance'] and not scope['three_callbacks_complete']
    assert scope['formal_increment']==0 and scope['candidate_execution_count']==0
    parsed_python = []
    for path in sorted(OUT.glob('*.py')):
        ast.parse(path.read_bytes().decode('utf-8'), filename=path.name)
        parsed_python.append(ref(path))

    dump('static-byte-audit.json', {'schema':'researchos.f08.i17.R01-R02.static-byte-audit.v1',
        'actor':ACTOR,'status':'STATIC_PREPARATION_CHECKED_NOT_ACCEPTED','self_acceptance':False,
        'R01':{'original_test_CRLF':0,'prior_v4_CRLF':609,'new_v5_CRLF':0,
            'old_Test_raw_byte_bodies_equal_without_normalization':28,'raw_body_records':raw_bodies,
            'all_helper_semantics_and_data_freeze_candidates_retained':True},
        'driver_other17_raw_byte_bodies_equal':driver_bodies,'I18_entire_raw_body':i18,
        'full_corrected_driver_test_whole_bytes_reused':True,'original_partial17_controller_unmodified':True,
        'R02':{'five_planned_source_fact_pairs':static_results,'old109_entry_raw_prefix_bytes_unchanged':True,
            'old100_dispatch_controls_unchanged':True,'same_accepted_mode_action_shape':True,
            'all_good_and_bad_expectations':'SOURCE_INFERENCE_NOT_RUN','actual_target_results':None},
        'vector_count':114,'function_vector_counts':function_counts,'BLOB_arg_ref_occurrences_rehashed':blob_refs,
        'prior_BLOB_arg_ref_occurrences':prior_BLOB_arg_occurrences,
        'new_source_fact_pair_BLOB_arg_occurrence_delta':10,
        'whole_forward_inverse_bytes_exact':True,'diff_pair_count':8,
        'receipt_metadata_fix_byte_inverse_pairs':3,
        'four_pretransition_sequence_counts':sequence_counts,'pretransition_frames':100,
        'production_v3_driver_DDL34_harness_whole_bytes_reused':True,
        'original_input46_preserved':True,'selected_input_ref_count':len(inputs_before),'input_drift':0,
        'Python_AST_parse_only_refs':parsed_python,
        'Go_AST_Go_compile_gofmt_SQL_driver_helper_HTTP_SDK_model_calls':0,
        'remaining_FATAL_OPEN':scope['remaining_FATAL_OPEN'],
        'source_acceptance':False,'SQL24_adoption_allowed':False,'formal_increment':0,
        'full_I17':'FATAL_OPEN','source_writer_stops_after_seal':True})
    print(json.dumps({'status':'STATIC_PREPARATION_CHECKED_NOT_ACCEPTED','old_Test_raw_bodies':28,
        'other_driver_raw_bodies':17,'I18_full_body_exact':True,'new_source_fact_pairs':5,
        'vectors':114,'inverse_exact':True,'inputs':len(inputs_before),'target_runs':0},ensure_ascii=False))

if __name__=='__main__':
    main()
