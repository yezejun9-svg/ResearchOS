"""Minimal R01/R02 author preparation: pure IO/JSON/lexical/static source only."""
from pathlib import Path
import ast
import base64
import copy
import hashlib
import json
import re
import sys

# -I -S means script-directory imports are explicit and owned by this receipt.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from packet_io import OUT, PRIOR, REVIEW, MAPPING, ACTOR, ref, checked, load, compact, dump, write, diff_pair, source_rules, shape
import packet_io

def main():
    # Previous metadata exception preserved its already-written candidate data.
    # A corrected script reuses only exact identical bytes and never overwrites
    # those files; original failed scripts and native logs are distinct inputs.
    assert (OUT / 'origin.metadata-vector-newline.json').exists()
    packet_io.ALLOW_IDENTICAL_PREPARED_REUSE = True
    review_handoff = load(REVIEW / 'handoff.json')
    assert ref(REVIEW / 'handoff.json')['sha256'] == '7d6a671d4e3ac374ea302c881e7c21b991e4c4fa943756a83358fe8b7d252ae9'
    assert ref(REVIEW / 'handoff.json')['bytes'] == 8501
    assert ref(PRIOR / 'handoff.json')['sha256'] == '66e6d86beb597b245339df1f6133126bcfbf0e65fe9ce9008801f12f32ee22df'
    assert ref(PRIOR / 'manifest.json')['sha256'] == '07e4fe92947f004393a376b387b344725622ff5949d53f2ca7ad059fb5d537a4'
    for key in ['source_review_ref', 'readable_review_ref', 'minimum_source_fact_plan_ref']:
        checked(review_handoff[key])
    review = json.loads(checked(review_handoff['source_review_ref']))
    assert review['verdict'] == 'REQUEST_CHANGES'
    assert [f['id'] for f in review['findings']] == ['I17-R01', 'I17-R02']
    plan = json.loads(checked(review_handoff['minimum_source_fact_plan_ref']))
    assert plan['minimum_new_pairs'] == 5 and len(plan['cases']) == 5
    group = load(PRIOR / 'source-group.json')
    source_ref = group['production_callback']['after']
    source_raw = checked(source_ref)
    rules = source_rules(source_raw)
    source_lines = source_raw.decode('utf-8').splitlines()
    original_test = group['producer_tests']['before']
    prior_test = group['producer_tests']['after']
    original_raw, prior_raw = checked(original_test), checked(prior_test)
    assert b'\r' not in original_raw and prior_raw.count(b'\r\n') == 609

    # Hash every prior packet member and every non-author review packet member.
    # Refs are reused without changing/copying their sealed bytes.
    selected = {}
    whole_records = []
    def add(r):
        checked(r)
        if r['path'] in selected:
            assert selected[r['path']] == r
        selected[r['path']] = r
    for root in [PRIOR, REVIEW]:
        manifest = load(root / 'manifest.json')
        expected_schema = 'researchos.whole-namespace-manifest.v1' if root == PRIOR else 'researchos.source-review.manifest.v1'
        expected_exclusion = 'manifest.json' if root == PRIOR else True
        assert manifest['schema'] == expected_schema and manifest['self_excluded'] == expected_exclusion
        paths = {m['path'] for m in manifest['members']}
        actual = {p.as_posix() for p in root.rglob('*') if p.is_file() and p != root / 'manifest.json'}
        assert paths == actual
        assert manifest['file_count'] == len(manifest['members'])
        assert manifest['total_bytes'] == sum(m['bytes'] for m in manifest['members'])
        for member in manifest['members']:
            add(member)
        add(ref(root / 'manifest.json'))
        whole_records.append({'root': root.as_posix(), 'manifest_ref': ref(root / 'manifest.json'),
            'members': manifest['file_count'], 'member_bytes': manifest['total_bytes'],
            'member_plus_manifest_refs_rehashed': manifest['file_count'] + 1, 'drift': 0})
    original_input_refs = load(PRIOR / 'inputs.before.json')
    assert original_input_refs == load(PRIOR / 'inputs.after.json')
    for r in original_input_refs:
        add(r)
    # These two actual source files were located/read before this operation.
    protocol_source = MAPPING / 'source-snapshots/09-client_protocol.go'
    protocol_schema = MAPPING / 'source-snapshots/27-015-client.protocol.schema.json'
    add(ref(protocol_source)); add(ref(protocol_schema)); add(source_ref); add(original_test)
    for case in plan['cases']:
        add(case['baseline'])
    inputs_before = [selected[k] for k in sorted(selected)]
    dump('inputs.before.json', inputs_before)
    dump('whole-prior-packets.before.json', whole_records)
    dump('owner-and-scope.json', {'schema': 'researchos.receipt-owner.v1', 'actor': ACTOR,
        'owned_namespace': OUT.as_posix(), 'parent': '/root', 'source_writer': True,
        'other_writers': 'Root and separate W05/F08 branches; preserve their changes',
        'model_selection': 'Inherited current Codex model; no override or new user chat',
        'scope': 'New receipt-only minimal R01/R02 source and raw proposals; no adoption',
        'Main_canonical_cache_module_old_receipt_writes': 0, 'target_helper_Go_SQL_SDK_HTTP_model_calls': 0})

    # R01 correction restores only LF to the prior helper-refactored candidate.
    # Raw old Test slices are checked later without any newline normalization.
    new_test_raw = prior_raw.replace(b'\r\n', b'\n')
    assert b'\r' not in new_test_raw
    new_test_ref = write('client_cancel_finalization_test.v5.go.proposed.txt', new_test_raw)
    changes = [diff_pair('R01-prior-v4-to-v5-LF', prior_test, new_test_ref),
        diff_pair('R01-original-v3-to-v5-helpers', original_test, new_test_ref)]

    new_cases, case_evidence = [], []
    for case in plan['cases']:
        case_id = case['id']
        before_raw = checked(case['baseline'])
        before = json.loads(before_raw)
        assert before_raw == compact(before), 'Existing raw baseline not byte-reconstructible'
        assert case['mode'] == 5 and before['action'] == case['action']
        bad = copy.deepcopy(before)
        mutation = {'single_fact': case['single_fact']}
        locator = before['row'][:4] if before['action'] == 'commit.insert' else [before['row'][0], before['row'][1], before['row'][3], before['row'][4]]
        if case_id == 'proof-commit-missing-admitted-pin':
            candidates = [i for i, (category, row) in enumerate(before['sources'])
                if category == 'pins' and row[:4] == locator and row[4] == 'ADMITTED']
            assert len(candidates) == 6
            index = candidates[0]
            removed = bad['sources'].pop(index)
            mutation.update({'path': '/sources/' + str(index), 'operation': 'remove_one_tuple',
                'category': 'pins', 'phase': 'ADMITTED', 'before': removed, 'after': 'ABSENT'})
            branch_lines = [1490, 1491, 1492, 1493, 1520, 1521, 1366, 1367, 1368, 783, 784, 785, 786, 787, 788]
        elif case_id == 'proof-commit-missing-final-member':
            candidates = [i for i, (category, row) in enumerate(before['sources'])
                if category == 'final_members' and row[:4] == locator]
            assert len(candidates) == 1
            index = candidates[0]
            removed = bad['sources'].pop(index)
            mutation.update({'path': '/sources/' + str(index), 'operation': 'remove_one_tuple',
                'category': 'final_members', 'before': removed, 'after': 'ABSENT'})
            branch_lines = [1490, 1491, 1492, 1493, 1520, 1521, 783, 784, 785]
        elif case_id == 'proof-commit-control-not-confirmed':
            candidates = [i for i, (category, row) in enumerate(before['sources'])
                if category == 'controls' and [row[0], row[1], row[2], row[5]] == locator]
            assert len(candidates) == 1
            index = candidates[0]
            assert bad['sources'][index][1][8] == 'CONFIRMED'
            bad['sources'][index][1][8] = 'RECONCILING'
            mutation.update({'path': '/sources/' + str(index) + '/1/8', 'operation': 'replace_one_scalar',
                'before': 'CONFIRMED', 'after': 'RECONCILING'})
            branch_lines = [1490, 1491, 1492, 1493, 1520, 1521, 1371, 1372, 1373, 1388, 1522]
        elif case_id == 'proof-journal-retained-original-header-field':
            old_header_raw = bytes.fromhex(before['row'][7])
            header = json.loads(old_header_raw)
            assert list(header) == ['schema', 'encoding', 'raw_envelope_base64']
            assert compact(header, False) == old_header_raw
            original_env_raw = base64.b64decode(header['raw_envelope_base64'], validate=True)
            env = json.loads(original_env_raw)
            assert compact(env, False) == original_env_raw
            assert env['expected_revision'] == 7
            changed_env = copy.deepcopy(env)
            changed_env['expected_revision'] = 8
            changed_env_raw = compact(changed_env, False)
            changed_header = copy.deepcopy(header)
            changed_header['raw_envelope_base64'] = base64.b64encode(changed_env_raw).decode('ascii')
            changed_header_raw = compact(changed_header, False)
            bad['row'][7] = changed_header_raw.hex().upper()
            mutation.update({'path': '/row/7', 'operation': 'replace_one_header_scalar',
                'decoded_envelope_path': '/expected_revision', 'before': 7, 'after': 8,
                'original_envelope_ref': write('header/original-envelope.json', original_env_raw),
                'changed_envelope_ref': write('header/changed-envelope.json', changed_env_raw),
                'original_header_ref': write('header/original-private-header.json', old_header_raw),
                'changed_header_ref': write('header/changed-private-header.json', changed_header_raw)})
            branch_lines = [1495, 1496, 1425, 1426, 1427, 1428, 1429, 1430, 1431, 1432, 1433, 1434, 1435]
        elif case_id == 'proof-journal-retained-timestamp':
            assert bad['row'][8] == '2026-01-01T00:00:00Z'
            bad['row'][8] = '2026-01-02T00:00:00Z'
            mutation.update({'path': '/row/8', 'operation': 'replace_one_scalar',
                'before': '2026-01-01T00:00:00Z', 'after': '2026-01-02T00:00:00Z'})
            branch_lines = [1495, 1496, 1497, 1498, 1499, 1007, 1008, 1009, 1010, 1011]
        else:
            raise AssertionError(case_id)
        good_shape, bad_shape = shape(before, rules), shape(bad, rules)
        assert bad['action'] == before['action'] and bad['old'] == before['old']
        bad_ref = write('raw/' + case_id + '.bad.json', compact(bad))
        changes.append(diff_pair('R02-' + case_id, case['baseline'], bad_ref))
        vector = {'id': case_id, 'function': 'researchos_f08_proof_v1',
            'valid': [{'kind': 'INTEGER', 'integer': 5}, {'kind': 'BLOB', 'ref': case['baseline']}],
            'corrupt': [{'kind': 'INTEGER', 'integer': 5}, {'kind': 'BLOB', 'ref': bad_ref}],
            'corrupt_kind': 'CALLBACK_ERROR', 'fixed_callback_error': case['expected_fixed_error'],
            'expected_sqlite_primary_code': 1, 'sqlite_code_evidence': 'SOURCE_INFERENCE_NOT_NATIVE_RUN',
            'mutation': mutation, 'provenance': {'producer_ref': original_test,
                'corrected_data_producer_tests_ref': new_test_ref, 'baseline_ref': case['baseline'],
                'non_author_minimum_plan_ref': review_handoff['minimum_source_fact_plan_ref'],
                'data_builder': 'Independent copy of sealed pretransition data, only the planned fact changed',
                'sequence': 'ack_true_text', 'transition_index': 25 if case['action'] == 'commit.insert' else 24,
                'predicate_executions': 0, 'ddl_native_capture': False},
            'status': 'SOURCE_DERIVED_NOT_RUN', 'valid_expected': {'driver_type': 'int64', 'value': 1}}
        new_cases.append(vector)
        case_evidence.append({'id': case_id, 'baseline_ref': case['baseline'], 'bad_ref': bad_ref,
            'mode': 5, 'action_before': before['action'], 'action_after': bad['action'],
            'shape_before': good_shape, 'shape_after': bad_shape, 'mutation': mutation,
            'source_ref': source_ref, 'source_branch': case['source_fail_branch'],
            'source_lines': [{'line': n, 'text': source_lines[n-1]} for n in branch_lines],
            'expected_direct_good': {'type': 'int64', 'value': 1, 'error': None},
            'expected_direct_bad': {'value': None, 'error': 'F08_ORIGINAL_BINDING'},
            'expected_SQL_bad': {'actual_type_required': 'sqlite.Error', 'primary_code': 1,
                'fixed_callback_error': 'F08_ORIGINAL_BINDING'},
            'expected_failed_INSERT_count_change': 0, 'expectation_authority': 'SOURCE_INFERENCE_NOT_RUN',
            'actual_callback_result': None, 'actual_SQLite_error': None,
            'actual_failed_INSERT_count_change': None, 'actual_native_run': None,
            'full_production_DDL': 'FATAL_OPEN'})

    prior_vector_ref = group['raw_vectors']
    prior_vector_raw = checked(prior_vector_ref)
    prior_vectors = json.loads(prior_vector_raw)
    assert len(prior_vectors['vectors']) == 109
    suffix = b'\n  ],\n  "formal_acceptance": false,'
    assert prior_vector_raw.count(suffix) == 1
    insertion = prior_vector_raw.index(suffix)
    # Preserve original 109 entry bytes and all surrounding fields verbatim.
    added = b',\n'.join(b'\n'.join(b'    ' + line for line in json.dumps(v, ensure_ascii=False, indent=2).encode('utf-8').splitlines()) for v in new_cases)
    new_vector_raw = prior_vector_raw[:insertion] + b',\n' + added + prior_vector_raw[insertion:]
    new_vectors = json.loads(new_vector_raw)
    assert new_vectors['vectors'][:109] == prior_vectors['vectors']
    assert new_vectors['vectors'][109:] == new_cases
    assert {k: v for k, v in new_vectors.items() if k != 'vectors'} == {k: v for k, v in prior_vectors.items() if k != 'vectors'}
    new_vector_ref = write('vector-manifest.json', new_vector_raw)
    changes.append(diff_pair('R02-vector-manifest-append-only', prior_vector_ref, new_vector_ref))
    dump('source-fact-cases.json', {'schema': 'researchos.f08.i17.source-fact-revision.v1',
        'actor': ACTOR, 'status': 'PROPOSED_NOT_RUN', 'non_author_request_ref': ref(REVIEW/'source-review.json'),
        'minimum_plan_ref': ref(REVIEW/'minimum-source-fact-plan.json'), 'cases': case_evidence,
        'original_dispatch_controls': 100, 'new_source_fact_pairs': 5,
        'actual_native_result': None, 'predicate_execution_count': 0})
    dump('source34-rules.exact.json', {'source_ref': source_ref, 'rules': rules,
        'rule_count': 34, 'authority': 'SOURCE_TEXT_EXTRACTION_NO_SQL_EXECUTION'})
    dump('changes.json', changes)
    next_group = copy.deepcopy(group)
    next_group['producer_tests']['after'] = new_test_ref
    next_group['raw_vectors'] = new_vector_ref
    next_group['prior_group_ref'] = ref(PRIOR/'source-group.json')
    next_group['non_author_request_ref'] = ref(REVIEW/'source-review.json')
    next_group['raw_source_fact_cases'] = ref(OUT/'source-fact-cases.json')
    next_group['minimal_delta'] = 'R01 LF restoration and R02 exactly five appended genuine source-fact pairs'
    # Keep unchanged real private harness, corrected driver test and full inputs.
    dump('source-group.json', next_group)
    scope = load(PRIOR/'scope-and-open.json')
    scope.update({'actor': ACTOR, 'prior_scope_ref': ref(PRIOR/'scope-and-open.json'),
        'non_author_remaining_FATAL_OPEN_verbatim': review['remaining_FATAL_OPEN'],
        'R01_preparation': 'LF restored; all 28 old raw byte bodies require audit without normalization',
        'R02_preparation': 'Exactly five planned source-fact raw pairs, accepted mode/action/shape; NOT_RUN',
        'new_failure_origins': [ref(OUT/'origin.rg-absent-specs.json'), ref(OUT/'origin.metadata-membership.json'), ref(OUT/'origin.metadata-vector-newline.json')],
        'original_failure_facts': {'prior_author_handoff': ref(PRIOR/'handoff.json'),
            'non_author_review_handoff': ref(REVIEW/'handoff.json'),
            'preserved_with_no_retry_no_recount_no_reset': True},
        'actual_native_observations': [], 'original_tool_observations': [ref(OUT/'original-tool-observations.json')]})
    dump('scope-and-open.json', scope)
    dump('metadata-script-fix.json', {'changes': [
        diff_pair('metadata-root-manifest-exclusion-fix', ref(OUT/'metadata-failure/revise_prepare.original-failed.py'), ref(OUT/'revise_prepare.py')),
        diff_pair('metadata-vector-LF-append-fix', ref(OUT/'metadata-failure/revise_prepare.second-failed.py'), ref(OUT/'revise_prepare.py')),
        diff_pair('metadata-identical-prepared-byte-reuse', ref(OUT/'metadata-failure/packet_io.before-resume.py'), ref(OUT/'packet_io.py'))],
        'original_failed_inputs_reexecuted': False, 'unchanged_prepared_file_overwrites': 0})
    inputs_after = [ref(r['path']) for r in inputs_before]
    assert inputs_after == inputs_before
    dump('inputs.after.json', inputs_after)
    dump('preparation-result.json', {'schema': 'researchos.f08.i17.minimal-revision-preparation.v1',
        'status': 'SOURCE_PREPARATION_ONLY_AWAITING_NON_AUTHOR_REVIEW', 'actor': ACTOR,
        'old_vector_count': 109, 'new_source_fact_pairs': 5, 'vector_count': 114,
        'prior_test_CRLF': 609, 'new_test_CRLF': 0, 'new_test_ref': new_test_ref,
        'new_vectors_ref': new_vector_ref, 'original_inputs_rehashed': len(original_input_refs),
        'total_pinned_input_refs_rehashed': len(inputs_before), 'input_drift': 0,
        'source_group_ref': ref(OUT/'source-group.json'), 'changes_ref': ref(OUT/'changes.json'),
        'source_acceptance': False, 'formal_increment': 0, 'all_target_tests_NOT_RUN': True})
    print(json.dumps({'status': 'SOURCE_PREPARATION_ONLY', 'new_pairs': 5, 'vectors': 114,
        'new_test_CRLF': 0, 'input_refs': len(inputs_before), 'input_drift': 0,
        'target_runs': 0}, ensure_ascii=False))

if __name__ == '__main__':
    try:
        main()
    except BaseException as error:
        # This metadata preparation exception is neither a candidate failure nor
        # a simulated target execution. Real traceback/exit are kept by runner.
        raise
