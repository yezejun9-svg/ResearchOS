"""Desktop authority adapter SOURCE PREPARATION ONLY. No process, SQLite, DLL, writes or registration implementation. Future Root/W05 binding required."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r'D:/作品集/ResearchOS/research-os')
CANONICAL = ['execution/v2.4/' + n + '.json' for n in
             ['checkpoint', 'path_ownership', 'step_state', 'commands']]
CASES = ['real-existing-open-readonly', 'real-existing-self-send']
CAPS = {'cases': 2, 'upstream_dispatch_per_case': 32, 'proxy_admission_per_case': 32,
        'qualifying_observed_HTTP_legs': 128, 'unobserved_client_outbound_hard_cap': None,
        'SDK_MODEL_Node_external_paid_private_calls': 0}
SOURCE = 'e2ee22a0e4d697bf98b46f10ebb58ae7e23159a7'
PARENT = 'a510dbef4a7e08fb5c428df44c39b133f3ffa856'



FIXED_CODE = {'controller_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_revision_preparation_codex\\736e757cdbc148a286c1d2426b8a7382\\desktop_controller.v3.proposed.py', 'sha256': 'd63a3cc10150fabbae327ea38962661074a3fe6590a04d6a393219fa2d3cc02c', 'bytes': 23124}, 'launcher_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_revision_preparation_codex\\736e757cdbc148a286c1d2426b8a7382\\desktop_launch.v2.proposed.py', 'sha256': 'a4b5d968cc1829971ada48f55743bb7f6cc790967f76c179ceca1cac978b2bf7', 'bytes': 6232}, 'debug_helper_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_revision_preparation_codex\\736e757cdbc148a286c1d2426b8a7382\\windows_debug_job_tree.future_images.deadline.proposed.py', 'sha256': '7f89cdd07a199a94848c7ecd5d5d474889c34ca34c343783b3d96338e0e0d3ee', 'bytes': 46898}, 'owned_helper_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W05\\W05-99\\integration_codex\\independent-cli-list-scopes-r308\\windows_owned_process.py', 'sha256': '6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad', 'bytes': 18901}, 'utility_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_cli2_controller_preparation_codex\\86d71652d03649879b13e03a974456d9\\runner.current58.proposed.py', 'sha256': 'c3abc7eedfb00c1dc52113bd27c49ae9c339626fa288c00765d0b14951f69904', 'bytes': 40577}, 'network_observer_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_controller_preparation_codex\\52998fc9c4d64166b10aa02e6eca11e4\\legacy_http_observer.proposed.cjs', 'sha256': '34ac15b03567af6475812bf66a331793746cea0c5aeadc2a2eb3a3f80e3df36a', 'bytes': 4442}, 'fixture_evaluator_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_revision_preparation_codex\\736e757cdbc148a286c1d2426b8a7382\\fixture_evaluator.v2.proposed.py', 'sha256': '717cd3a2056e4d93f4a603b26519e44b8f149277c544f0450b1d4b36984fa0b5', 'bytes': 9760}, 'roster_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\.local\\worktrees\\codex-w1303-desktop-http-r311\\execution\\v2.4\\receipts\\W13\\W13-03\\desktop_http_exact15_executor_codex\\revision-r317-a7f44ed9b4ae4225bd072adcf708e24b\\finite-roster.frozen.json', 'sha256': '6d97600d2adf812248fd7d2dcb1027e76d1066db9406fa114369f03930439899', 'bytes': 138614}, 'alias_roster_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_controller_preparation_codex\\52998fc9c4d64166b10aa02e6eca11e4\\negative-alias-roster.json', 'sha256': '6074704e76a9ced8b0162f78065431ff03ad6c474ae412addd99cdb771a3d33f', 'bytes': 5646}, 'alias_edits_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_controller_preparation_codex\\52998fc9c4d64166b10aa02e6eca11e4\\alias.edits.json', 'sha256': '2634a1199762ab77256208ebe6ac520a6484bd1e92393d1dd2a62a5aff35dd39', 'bytes': 1239}, 'instrumented_test_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\execution\\v2.4\\receipts\\W13\\W13-03\\fresh58_desktop169_go3_controller_preparation_codex\\52998fc9c4d64166b10aa02e6eca11e4\\http-wire-boundary.alias.instrumented.mjs.proposed.txt', 'sha256': 'd6f7b4a31edd1b7d242657b14af8b379b5f1563e790ef6890c0b79594c797629', 'bytes': 49460}, 'builder_source_ref': {'path': 'D:\\作品集\\ResearchOS\\research-os\\apps\\desktop\\build-validator.py', 'sha256': 'd7dbd66c5e98b26e1701ea00f918897092907d0afb1fc4912e59ecf05d569d46', 'bytes': 13612}}
CODE_KEYS = ['controller_ref', 'launcher_ref', 'debug_helper_ref', 'owned_helper_ref', 'utility_ref', 'network_observer_ref', 'fixture_evaluator_ref', 'roster_ref', 'alias_roster_ref', 'alias_edits_ref', 'instrumented_test_ref', 'builder_source_ref', 'authorization_verifier_ref', 'source_catalog_ref']

def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Non-finite JSON: ' + value)
    return json.loads(raw.decode('utf-8', errors='strict'), object_pairs_hook=pairs,
                      parse_constant=invalid)


def bounded_path(value, exists=True):
    p = Path(value)
    if not p.is_absolute():
        p = ROOT / p
    require('..' not in p.parts and p.is_absolute(), 'Invalid path')
    require(p.is_relative_to(ROOT) and p != ROOT, 'Path outside exact repository')
    require(p.resolve(strict=exists) == p.absolute(), 'Path alias: ' + str(p))
    cursor = p
    while cursor != ROOT.parent:
        if os.path.lexists(cursor):
            info = os.lstat(cursor)
            require(not cursor.is_symlink() and not (getattr(info, 'st_file_attributes', 0) & 0x400),
                    'Reparse/symlink path: ' + str(cursor))
        cursor = cursor.parent
    return p


class Reader:
    def __init__(self):
        self.raw = {}

    def read(self, p, external=False):
        p = Path(p) if external else bounded_path(p)
        require(p.is_absolute() and p.is_file(), 'Missing regular input: ' + str(p))
        key = str(p.absolute())
        raw = p.read_bytes()
        if key in self.raw:
            require(raw == self.raw[key], 'Input changed during authorization: ' + key)
        self.raw[key] = raw
        return raw

    def ref(self, p, external=False):
        p = Path(p) if external else bounded_path(p)
        raw = self.read(p, external)
        return {'path': str(p) if external else p.relative_to(ROOT).as_posix(),
                'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}

    def verify(self, item, external=False):
        require(isinstance(item, dict) and set(item) == {'path', 'sha256', 'bytes'}, 'Invalid ref')
        require(type(item['bytes']) is int and item['bytes'] >= 0, 'Invalid ref size')
        raw = self.read(item['path'], external)
        require(len(raw) == item['bytes'] and hashlib.sha256(raw).hexdigest() == item['sha256'],
                'Ref mismatch: ' + item['path'])
        return raw

    def doc(self, item, external=False):
        return strict_json(self.verify(item, external))


def registration_refs(reader, scope):
    base = ROOT / scope['registration_namespace']
    return {key: reader.ref(base/name) for key, name in {
        'manifest': 'manifest.json', 'audit': 'registration-audit.json',
        'invocation': 'invocation.json', 'intent': 'canonical-write.intent.json',
        'verified': 'canonical-write.verified.json'}.items()}


def validate_current58_source(reader, scope, authority, cp, ow):
    # Legacy current43 wire names are retained; this authority applies ONLY to SOURCE/current58.
    require(cp['head'] == SOURCE and authority['source_parent'] == PARENT and
            authority['unique_combined_source_paths'] == 58 and
            authority['source_acceptance'] is False and
            authority['fresh_compilation_or_cases_accepted'] is False,
            'Current58 source identity; no old qualification inheritance')
    closure_ref = authority['source_commit_closure_ref']
    require(bounded_path(closure_ref['path']) == ROOT/'execution/v2.4/receipts/W13/W13-03/desktop58_source_execution_independent_review_codex/a76cb528a87f45529adb3da26418eabb/review.json' and
            closure_ref['sha256'] == '7d82779e61ff50c3072e9d008531b2409e3ee288235ec7ad12a24f276f4de4b7' and
            closure_ref['bytes'] == 12270, 'Actual Desktop15 source closure pin')
    closure = reader.doc(closure_ref)
    require(closure['schema'] == 'researchos.desktop58-source-execution-independent-review.v1' and
            closure['reviewer'] == 'codex:/root/w05_merge_review' and
            closure['decision'] == 'SOURCE_COMMIT_EVIDENCE_CLOSED' and closure['requested_changes'] == [] and
            closure['actual_new_head'] == SOURCE and closure['actual_parent'] == PARENT and
            closure['unique_combined_paths'] == 58 and closure['source_path_count'] == 15 and
            closure['source_acceptance'] is False and closure['fresh58_qualified'] is False,
            'Closed source import is not current58 execution qualification')
    for key in ['completed_ref','manifest_ref','outer_manifest_ref','outer_invocation_ref',
                'source_intent_ref','root_tool_observations_ref','scope_ref','grant_ref']:
        reader.verify(closure[key])
    wip = cp['work_in_progress']
    require(wip['desktop_exact15_source_integration_state'] == 'CLOSED_PENDING_FRESH58_VALIDATION' and
            wip['desktop_exact15_actual58_head'] == SOURCE and
            wip['desktop_exact15_actual_combined_source_paths'] == 58,
            'Desktop source import forward registration absent')
    for key, value in [('desktop_exact15_source_integration_execution_review_ref',closure_ref),
                       ('desktop_exact15_source_integration_completed_ref',closure['completed_ref']),
                       ('desktop_exact15_source_integration_manifest_ref',closure['manifest_ref']),
                       ('desktop_exact15_source_integration_outer_manifest_ref',closure['outer_manifest_ref']),
                       ('desktop_exact15_source_integration_grant_ref',closure['grant_ref'])]:
        require(reader.verify(wip[key]) == reader.verify(value), 'Canonical current58 closure mismatch ' + key)
    lease = ow['card_path_bindings']['W13-03']['subtasks']['desktop_exact15_source_integration']
    require(lease['current_source_writer'] is None and lease['state'] == 'CLOSED_PENDING_FRESH58_VALIDATION',
            'Desktop source writer lease not closed')
    source_set = reader.doc(authority['combined_source_set_ref'])
    require(source_set['schema'] == 'researchos.current58-combined-source-set.v1' and
            source_set['source_commit'] == SOURCE and source_set['source_parent'] == PARENT and
            source_set['source_commit_closure_ref'] == closure_ref and len(source_set['files']) == 58,
            'Exact current58 source set missing')
    catalog = reader.doc(scope['catalog_ref'])
    require(catalog['commit'] == SOURCE and catalog['file_count'] == len(catalog['files']), 'Fresh current58 catalogue')
    cat = {x['path']: x for x in catalog['files']}
    require(len(cat) == len(catalog['files']), 'Duplicate catalogue source path')
    seen = set()
    for item in source_set['files']:
        p = bounded_path(item['path'])
        relative = p.relative_to(ROOT).as_posix()
        require(item['path'] == relative and relative not in seen and relative in cat,
                'Source set duplicate/alias/not in fresh catalogue')
        seen.add(relative)
        reader.verify(item)
        require(item['sha256'] == cat[relative]['sha256'] and item['bytes'] == cat[relative]['bytes'],
                'Current58 source set/catalogue differs')
    require(set(closure['source_paths']).issubset(seen), 'Desktop15 absent from actual58 source set')
    source_scope = reader.doc(closure['scope_ref'])
    require(len(source_scope['shared38_paths']) == 38 and len(source_scope['cli8_paths']) == 8 and
            len(closure['source_paths']) == 15, 'Original source-set cardinalities')
    expected_paths = set(source_scope['shared38_paths'] + source_scope['cli8_paths'] + closure['source_paths'])
    require(len(expected_paths) == 58 and seen == expected_paths, 'Exact original38 plus CLI8 plus Desktop15 union')
    forward_ref = authority['forward_head_audit_ref']
    mf_ref = authority['forward_head_manifest_ref']
    mf = reader.doc(mf_ref)
    require(len(mf['entries']) == mf['count'] and mf['self_excluded'] is True, 'Forward manifest shape')
    listed = {}
    base = bounded_path(mf_ref['path']).parent
    for item in mf['entries']:
        p = bounded_path(item['path'])
        require(p.parent == base and str(p) not in listed, 'Forward manifest foreign/duplicate member')
        reader.verify(item)
        listed[str(p)] = item
    def sealed(item):
        require(listed.get(str(bounded_path(item['path']))) == item, 'Unsealed forward fact')
        return reader.doc(item)
    audit = sealed(forward_ref)
    require(audit['schema'] == 'researchos.desktop58-forward-head-registration-audit.v1' and
            audit['actor'] == 'codex:/root' and audit['registered_head'] == SOURCE and
            audit['actual_registration_exit'] == 0 and audit['source_acceptance'] is False and
            audit['formal_increment'] == 0 and audit['grant_materialized'] is False and
            audit['compile_GUI_HTTP_models_authorized'] is False and
            reader.verify(audit['source_closure_review_ref']) == reader.verify(closure_ref),
            'Actual source-head forward seal missing')
    inv = sealed(audit['invocation_ref'])
    intent = sealed(audit['intent_ref'])
    verified = sealed(audit['verified_ref'])
    request = reader.doc(audit['request_ref'])
    require(inv['actual_exit'] == 0 and inv['wrapper_error'] is None and inv['automatic_retry'] is False,
            'Forward registration did not complete')
    before, after = audit['before'], audit['after']
    require(all(type(t) is list and len(t) == 3 and all(type(x) is int and x >= 0 for x in t)
                for t in [before, after, request['before_tuple'], request['after_tuple']]),
            'Forward tuples require exactly three actual integers')
    require(request['schema'] == 'researchos.desktop58-forward-head-request.v1' and
            request['actor'] == 'codex:/root' and request['before_tuple'] == before and request['after_tuple'] == after and
            request['head_before'] == PARENT and request['head_after'] == SOURCE and
            intent['actor'] == 'codex:/root' and intent['Main_head'] == SOURCE, 'Forward request/audit/intent origin pairing')
    transition = intent['transition']
    require(type(transition) is dict and set(transition) == {'checkpoint','ownership','failures'} and
            all(type(transition[k]) is list and len(transition[k]) == 2 and
                all(type(x) is int for x in transition[k]) and transition[k] == [before[i],after[i]]
                for i,k in enumerate(['checkpoint','ownership','failures'])), 'Forward intent exact tuple transition')
    copies, originals = request['original_copy_refs'], request['canonical_before']
    require(type(copies) is list and type(originals) is list and len(copies) == len(originals) == 4 and
            len(intent['metadata']) == 2 and len(intent['unchanged']) == 2, 'Forward original four layout')
    original_raw = []
    for i, canonical in enumerate(CANONICAL):
        require(bounded_path(originals[i]['path']) == ROOT/canonical and
                bounded_path(copies[i]['path']) not in [ROOT/x for x in CANONICAL], 'Forward original-copy order/path')
        raw_original = reader.verify(copies[i])
        require(hashlib.sha256(raw_original).hexdigest() == originals[i]['sha256'] and
                len(raw_original) == originals[i]['bytes'], 'Forward original copy digest/size')
        original_raw.append(raw_original)
        if i < 2:
            require(intent['metadata'][i]['path'] == canonical and
                    reader.verify(intent['metadata'][i]['original_ref']) == raw_original, 'Forward intent/request original metadata bytes')
        else:
            require(intent['unchanged'][i-2] == {'path':canonical,'sha256':originals[i]['sha256']},
                    'Forward unchanged ST/CM original binding')
    original_cp, original_ow = [strict_json(x) for x in original_raw[:2]]
    require([original_cp['revision'],original_ow['revision'],len(original_cp['failure_counters'])] == before and
            all(type(x) is int for x in [original_cp['revision'],original_ow['revision']]) and
            original_cp['head'] == PARENT, 'Forward original-copy tuple/head')
    current = [cp['revision'],ow['revision'],len(cp['failure_counters'])]
    require(all(type(x) is int for x in current) and all(after[i] <= current[i] for i in range(3)) and
            [verified['checkpoint'],verified['ownership'],verified['failure_origins']] == after and
            all(type(verified[k]) is int for k in ['checkpoint','ownership','failure_origins']) and
            verified['intent_ref'] == audit['intent_ref'],
            'Forward registered tuple does not precede current authorization')
    require(all(x in authority['sealed_integration_refs'] for x in [closure_ref,forward_ref,mf_ref]),
            'Current58 source closure/forward chain not bound by authority')


def exact_tuple(value, name):
    require(type(value) is list and len(value) == 3 and
            all(type(x) is int and x >= 0 for x in value), name)
    return value


def absolute_ref(reader, item):
    reader.verify(item, external=Path(item['path']).is_absolute() and not Path(item['path']).is_relative_to(ROOT))
    p = Path(item['path'])
    if not p.is_absolute():
        p = ROOT / p
    return {'path': str(p), 'sha256': item['sha256'], 'bytes': item['bytes']}


def same_ref(reader, a, b):
    require(absolute_ref(reader, a) == absolute_ref(reader, b), 'Exact ref identity differs')


def sealed_manifest(reader, item, field, excluded_key=None):
    doc = reader.doc(item)
    rows = doc[field]
    require(type(rows) is list and rows, 'Empty evidence manifest')
    if excluded_key:
        require(doc[excluded_key] is True and type(doc['count']) is int and doc['count'] == len(rows), 'Manifest count/self exclusion')
    base = bounded_path(item['path']).parent
    members = {}
    for row in rows:
        p = bounded_path(row['path'])
        require(p.is_relative_to(base) and p != bounded_path(item['path']) and str(p) not in members, 'Foreign/duplicate/self manifest member')
        reader.verify(row)
        members[str(p)] = row
    return members


def member(reader, members, item):
    key = str(bounded_path(item['path']))
    require(key in members, 'Required fact is not sealed')
    same_ref(reader, members[key], item)
    return reader.doc(item)


def binding(scope):
    # Full scope binding; the independent review path is predetermined, not its future digest.
    return scope


def validate_cli2(reader, scope):
    qref = scope['current58_CLI2_qualification_ref']
    rref = scope['current58_CLI2_review_ref']
    proof = sealed_manifest(reader, scope['current58_CLI2_manifest_ref'], 'entries', 'self_excluded')
    q = member(reader, proof, qref)
    review = member(reader, proof, rref)
    # These are the actual r331 wire schemas; their names do not grant old43 compatibility.
    require(q['schema'] == 'researchos.cli43-bounded-execution-qualification.v1' and
            review['schema'] == 'researchos.cli43-bounded-execution-independent-review.v1', 'Unknown CLI qualification wire schema: explicit adaptation required')
    require(q['source_commit'] == review['source_commit'] == SOURCE and
            q['reviewer'] == review['reviewer'] == 'codex:/root/w05_merge_review' and
            review['decision'] == 'CURRENT43_FRESH_HELD2_BOUNDED_QUALIFICATION_EVIDENCE_CLOSED' and
            review['requested_changes'] == [] and review['non_author'] is True and
            review['actual_readonly_evidence_audit'] is True, 'Same-head nonauthor CLI2 closure required')
    same_ref(reader, review['qualification_ref'], qref)
    require(q['current43_fresh_held2_qualified'] is True and review['current43_fresh_held2_qualified'] is True and
            q['qualified_case_count'] == 2 and q['qualified_case_ids'] == review['case_ids'] == CASES and
            q['native_calls'] == q['native_calls_exit0'] == 14 and q['test_leaf_PASS'] == 2 and
            q['test_leaf_FAIL'] == q['test_leaf_SKIP'] == 0 and q['CLI_exit_codes'] == [0, 3] and
            q['cases_NOT_RUN'] == [] and q['SDK_MODEL_Node_external_paid_private_calls'] == 0 and
            q['underlying_product_failure_count_this_cohort'] == 0, 'Incomplete fresh CLI2 result')
    for d in [q, review]:
        require(d['source_acceptance'] is False and d['formal_increment'] == 0 and
                d['desktop15_execution_authorized'] is False, 'CLI result cannot grant Desktop execution')
    require(q['whole43_test_suite_qualified'] is False and q['Main_integration_authorized'] is False, 'No whole-suite/integration inheritance')
    evidence = q['evidence_refs']
    for key in ['scope_ref', 'grant_ref', 'result_ref', 'executor_manifest_ref', 'launcher_completed_ref',
                'launcher_manifest_ref', 'root_completion_ref', 'root_closed_manifest_ref', 'audit_ref', 'supplement_ref', 'final_corrections_ref']:
        same_ref(reader, evidence[key], review[key])
    cli_scope = reader.doc(evidence['scope_ref'])
    require(cli_scope['source_commit'] == SOURCE and cli_scope['ordered_cases'] == CASES and
            cli_scope['run_uuid'] == q['run_uuid'], 'CLI result belongs to another source/scope/run')
    same_ref(reader, cli_scope['catalog_ref'], scope['source_catalog_ref'])
    cli_grant = reader.doc(evidence['grant_ref'])
    same_ref(reader, cli_grant['scope_ref'], evidence['scope_ref'])
    require(cli_grant['actual_registration_completed'] is True and cli_grant['binding']['source_commit'] == SOURCE and
            cli_grant['binding']['run_uuid'] == q['run_uuid'] and
            cli_grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED', 'CLI original grant mismatch')
    qualified_at = exact_tuple(q['current_canonical_tuple'], 'CLI qualifier tuple')
    require(all(qualified_at[i] <= scope['expected_registration'][i] for i in range(3)), 'CLI qualification is from a future tuple')
    ex = sealed_manifest(reader, evidence['executor_manifest_ref'], 'files', 'excluded_only_self')
    la = sealed_manifest(reader, evidence['launcher_manifest_ref'], 'files', 'excluded_only_self')
    rt = sealed_manifest(reader, evidence['root_closed_manifest_ref'], 'members')
    member(reader, rt, evidence['root_completion_ref'])
    result = member(reader, ex, evidence['result_ref'])
    completed = member(reader, la, evidence['launcher_completed_ref'])
    require(completed['program_reported_exit'] == completed['actual_inner_native_exit'] == 0 and
            completed['first_cause'] is None and completed['secondary'] == [], 'CLI launcher not closed')
    require(result['status'] == 'BOUNDED_DEVELOPMENT_EVIDENCE_REPORTED' and result['first_cause'] is None and
            result['secondary'] == [] and result['NOT_RUN'] == [] and result['native_calls'] == 14 and
            len(result['stages']) == 14 and len(result['case_roster']) == len(result['cases']) == 2,
            'CLI actual result incomplete')
    for stage in result['stages']:
        member(reader, ex, stage['result_ref'])
    require([x['case_id'] for x in q['case_facts']] == CASES, 'CLI fact order')
    for i, case in enumerate(CASES):
        fact, state, case_result = q['case_facts'][i], result['case_roster'][i], result['cases'][i]
        require(fact['state'] == state['state'] == 'QUALIFIED' and fact['native_test_exit'] == 0 and
                fact['CLI_exit'] == [0,3][i] and state['leaf'] == case_result['leaf'] == case and
                state['launch_attempted'] is True and state['resumed'] is True and state['actual_native_exit'] == 0 and
                state['test_leaf_started'] is True and state['fixture_observation'] == 'OBSERVED' and
                state['qualified'] is True and state['failure'] is None and case_result['status'] == 'PASS', 'CLI leaf not truly qualified')
        for key in ['invocation_ref','verified_ref','stdout_ref','stderr_ref']:
            require(str(bounded_path(fact[key]['path'])) in ex, 'CLI leaf unsealed raw fact')
            same_ref(reader, ex[str(bounded_path(fact[key]['path']))], fact[key])
        reader.verify(case_result['proof_ref'])
    return {'qualification_ref':qref, 'review_ref':rref, 'manifest_ref':scope['current58_CLI2_manifest_ref']}


def validate_resources(reader, scope):
    catalog = reader.doc(scope['source_catalog_ref'])
    require(catalog['commit'] == SOURCE and catalog['file_count'] == 639 and
            len(catalog['files']) == 639 and catalog['all_platform_Go_count'] == 559, 'Actual current639 catalogue absent')
    names = set()
    for row in catalog['files']:
        require(row['path'] not in names and row['kind'] == 'blob' and row['mode'] in ['100644','100755'], 'Catalogue member shape')
        names.add(row['path'])
        reader.verify({k:row[k] for k in ['path','sha256','bytes']})
    resource = reader.doc(scope['resource_catalog_ref'])
    require(resource['complete_public_roots_frozen'] is True, 'Public compiler/runtime closure is not frozen')
    # New resource producer contract: explicit provenance refs, never cardinality-only acceptance.
    same_ref(reader, resource['runtime_resources_ref'], scope['runtime_resources_ref'])
    same_ref(reader, resource['compiler_resources_ref'], scope['compiler_resources_ref'])
    files = resource['files']
    require(type(files) is list and files, 'Missing resource members')
    seen = {}
    for row in files:
        p = Path(row['path'])
        require(p.is_absolute() and str(p.resolve()) == str(p) and str(p) not in seen, 'Resource alias/duplicate')
        reader.verify(row, external=True)
        seen[str(p)] = row
    for refkey in ['runtime_resources_ref','compiler_resources_ref']:
        source = reader.doc(scope[refkey])
        require(type(source['files']) is list and source['files'], 'Missing explicit compiler/runtime input list')
        for row in source['files']:
            require(row['path'] in seen and row == seen[row['path']], 'Resource union omits pinned input')
    require(type(resource['images']) is list and 0 < len(resource['images']) <= 60, 'Static executable image allocation')
    for image in resource['images']:
        require(image['path'] in seen and image == seen[image['path']], 'Executable outside frozen public files')
    for key in ['python','go','node','electron','git']:
        tool = resource['tools'][key]
        require(tool['path'] in seen and tool == seen[tool['path']] and tool in resource['images'], 'Tool outside fixed compiler/image closure')
    require(str(Path(sys.executable).resolve()) == resource['tools']['python']['path'], 'Actual Python differs')
    for key in ['GOMODCACHE','web_modules']:
        p = Path(resource[key])
        require(p.is_absolute() and str(p.resolve()) == str(p) and p.is_dir(), 'Missing physical public resource root')
    return resource


def load_scope(reader, scope_path, scope_sha256):
    require(sys.flags.isolated and sys.flags.no_site, 'Python must use -I -S')
    sr = reader.ref(scope_path)
    require(sr['sha256'] == scope_sha256, 'Scope SHA')
    scope = reader.doc(sr)
    require(scope['schema'] == 'researchos.desktop58-169-go3-preparation-scope.v1' and scope['owner'] == 'codex:/root' and
            scope['source_commit'] == SOURCE and scope['source_parent'] == PARENT and
            scope['preparation_only'] is False and scope['execution_authorized'] is True, 'Unbound/preparation scope cannot execute')
    expected = exact_tuple(scope['expected_registration'], 'Root actual registration tuple')
    before = exact_tuple(scope['expected_before_registration'], 'Root original registration tuple')
    require(expected[0] == before[0]+1 and expected[1] == before[1]+1 and expected[2] >= before[2], 'Actual registration transition')
    require(type(scope['registration_namespace']) is str and scope['registration_namespace'].startswith(
        'execution/v2.4/receipts/W05/W05-99/integration_codex/'), 'Actual Root registration namespace')
    require(scope['registration_metadata_paths'] in [CANONICAL[:2], CANONICAL], 'Unknown actual intent layout')
    require(scope['python_flags'] == ['-I','-S','-X','utf8'] and scope['first_unexpected_stop'] is True and
            scope['automatic_retry'] is False and scope['counter_reset'] is False and
            scope['source_acceptance'] is False and scope['formal_increment'] == 0, 'Policy escalation')
    for key, value in [('node_cases',169),('Go_top_cases',3),('native_top_command_cap',176),('loopback_HTTP_max',390),
                       ('offscreen_Electron_controls',2),('installed_visible_GUI_calls',0),('SDK_model_external_paid_calls',0),
                       ('process_cap',2048),('active_job_processes',16),('image_cap',64),('cleanup_seconds',5)]:
        require(type(scope[key]) is int and scope[key] == value, 'Finite original limit changed: '+key)
    for key in ['inner_seconds','outer_seconds','builder_seconds','controller_evidence_reserve_seconds','launcher_evidence_reserve_seconds']:
        require(type(scope[key]) is int and scope[key] > 0, 'Root allocation not supplied: '+key)
    require(scope['inner_seconds'] > 30+scope['controller_evidence_reserve_seconds'] and
            scope['builder_seconds'] <= scope['inner_seconds']-30-scope['controller_evidence_reserve_seconds'] and
            scope['outer_seconds'] > scope['inner_seconds']+30+scope['launcher_evidence_reserve_seconds'], 'IO/finalization reserve missing')
    uid = scope['run_uuid']
    require(type(uid) is str and len(uid) == 32 and all(c in '0123456789abcdef' for c in uid), 'Root run UUID required')
    roots = [bounded_path(scope[k],False) for k in ['output_root','outer_output_root','export_root','new_authorization_root']]
    require(len(set(roots)) == 4 and all(uid in p.name for p in roots) and
            all(not a.is_relative_to(b) for a in roots for b in roots if a != b), 'Fresh disjoint exact roots')
    require(roots[2].is_relative_to(ROOT/'.local') and all(roots[i].is_relative_to(ROOT/'execution/v2.4/receipts/W13/W13-03') for i in [0,1,3]), 'Wrong output root class')
    # Launcher creates outer root before the inner validates the SAME grant. This gate is pure/read-only.
    require(not roots[0].exists() and not roots[2].exists(), 'Inner output/export must be new')
    require(scope['main_git']['head'] == SOURCE, 'Current58 Main HEAD required')
    bounded_path(scope['controller_review_path'], False)
    for key in CODE_KEYS:
        r = scope[key]
        require(Path(r['path']).is_absolute() and str(Path(r['path']).resolve()) == r['path'], 'Controller consumes absolute canonical refs')
        reader.verify(r)
    require(bounded_path(scope['authorization_verifier_ref']['path']) == Path(__file__).resolve(), 'Actual gate path')
    for key, original in FIXED_CODE.items():
        same_ref(reader, scope[key], original)
    roster = reader.doc(scope['roster_ref'])
    require(len(roster['leaves']) == 162 and len(roster['regressions']) == 7 and len(roster['go_units']) == 3, 'Exact original lanes')
    alias = reader.doc(scope['alias_roster_ref'])
    require(len(alias['rows']) == 20 and alias['executable_aliases'] == 15 and alias['prebuild_clones'] is False, 'Finite future aliases')
    declaration = scope['negative_alias_declarations']
    require(type(declaration) is list and len(declaration) == 20, 'Root must predeclare all exact alias paths')
    for row, actual in zip(alias['rows'],declaration):
        root = roots[2]/'.local/desktop-wire-negative'/(uid+'-'+str(row['allocation_ordinal']).zfill(2))
        want = {'case_name':row['name'],'allocation_ordinal':row['allocation_ordinal'],'path':str(root/'resources/client-wire/researchos-client-wire-validator.exe'),
                'max_creates':row['expected_image_creates'],'mode':row['mode']}
        require(actual == want and not root.exists(), 'Alias path/case/allocation changed or preexisting')
    require(type(scope['public_environment']) is dict and set(scope['public_environment']) <= {'SystemRoot','WINDIR','ComSpec','PATH','PATHEXT'}, 'Public environment only')
    validate_resources(reader, scope)
    return scope, sr


def validate_authority(reader, scope, scope_ref, canonical_copies, registration):
    require([x['canonical_path'] for x in canonical_copies] == CANONICAL, 'Canonical order')
    docs = [reader.doc(x['ref']) for x in canonical_copies]
    cp, ow = docs[:2]
    require([cp['revision'], ow['revision'], len(cp['failure_counters'])] == scope['expected_registration'], 'Canonical revision')
    require(cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb', 'Project identity')
    wip = cp['work_in_progress']
    require(wip['desktop58_finite_validation_scope_ref'] == scope_ref, 'Scope not registered')
    authority_ref = wip['desktop58_finite_validation_current_source_authority_ref']
    require(authority_ref == scope['current_source_authority_ref'], 'Current43 authority pin')
    authority = reader.doc(authority_ref)
    require(authority['schema']=='researchos.cli43.current-source-validation-authority.v1' and
            authority['actor']=='codex:/root' and authority['source_commit']==SOURCE and
            authority['current_canonical_head']==SOURCE and authority['source_integration_completed'] is True and
            authority['formal_increment']==0, 'Actual current43 source authority missing')
    for rr in authority['sealed_integration_refs']:
        reader.verify(rr)
    require(len(authority['sealed_integration_refs'])>=3, 'Actual Main38/CLI8 and head-forward refs missing')
    validate_current58_source(reader, {'catalog_ref':scope['source_catalog_ref']}, authority, cp, ow)
    require(wip['desktop58_finite_validation_CLI2_qualification_ref'] == scope['current58_CLI2_qualification_ref'] and
            wip['desktop58_finite_validation_state'] == 'REGISTERED_PENDING_ONCE_EXECUTION', 'Desktop prerequisite/lease state')
    lease = ow['card_path_bindings']['W13-03']['subtasks']['desktop58_finite_validation']
    require(lease['owner'] == 'codex:/root' and lease['current_source_writer'] is None and
            lease['state'] == 'REGISTERED_PENDING_ONCE_EXECUTION' and lease['scope_ref'] == scope_ref and
            lease['run_uuid'] == scope['run_uuid'] and lease['source_commit'] == SOURCE,
            'Actual Desktop finite execution lease absent')
    validate_cli2(reader, scope)
    same_ref(reader, scope['Root_forward_head_seal_ref'], authority['forward_head_manifest_ref'])
    forward_review = reader.doc(scope['Root_forward_head_review_ref'])
    require(scope['Root_forward_head_review_ref']['sha256'] == 'f14dcdf6cfa2676db6022e7a852abd38e2095bc45a0529566b10997001a03624' and
            scope['Root_forward_head_review_ref']['bytes'] == 7591 and
            forward_review['schema'] == 'researchos.desktop58-source-head-registration-closed-review.v1' and
            forward_review['reviewer'] == 'codex:/root/w05_merge_review' and
            forward_review['decision'] == 'SOURCE_HEAD_REGISTRATION_EVIDENCE_CLOSED' and
            forward_review['requested_changes'] == [] and forward_review['actual_registration_evidence_closed'] is True and
            forward_review['actual_head'] == SOURCE and forward_review['actual_parent'] == PARENT and
            forward_review['source_acceptance'] is False and forward_review['formal_increment'] == 0,
            'Historical source-head forward independent closure missing')
    same_ref(reader, forward_review['post_registration_audit_ref'], authority['forward_head_audit_ref'])
    same_ref(reader, forward_review['registration_manifest_ref'], authority['forward_head_manifest_ref'])
    runner_ref = wip['desktop58_finite_validation_controller_review_ref']
    require(bounded_path(runner_ref['path'])==bounded_path(scope['controller_review_path']), 'Controller review canonical path')
    review = reader.doc(runner_ref)
    require(review['schema'] == 'researchos.desktop58-controller-static-review.v1' and
            review['reviewer'] == 'codex:/root/w05_merge_review' and
            review['decision'] == 'READY_FOR_ROOT_CURRENT58_DESKTOP169_GO3_ONCE' and
            review['requested_changes'] == [], 'Controller independent review')
    for key, actual in [('controller_sha256', scope['controller_ref']['sha256']),
                        ('scope_sha256', scope_ref['sha256']),
                        ('launcher_sha256', scope['launcher_ref']['sha256']),
                        ('gate_sha256', scope['authorization_verifier_ref']['sha256'])]:
        require(review[key] == actual, 'Runner review mismatch ' + key)
    require(registration == registration_refs(reader, scope), 'Registration ref path/hash mismatch')
    manifest = reader.doc(registration['manifest'])
    entries = manifest['entries']
    require(len(entries) == manifest['count'], 'Registration manifest count')
    listed = {}
    for item in entries:
        path = bounded_path(item['path'])
        require(path.is_relative_to(ROOT/scope['registration_namespace']), 'Foreign registration manifest entry')
        require(str(path) not in listed, 'Duplicate registration manifest entry')
        reader.verify(item)
        listed[str(path)] = item
    def sealed(item):
        require(listed.get(str(bounded_path(item['path']))) == item, 'Registration input unsealed')
        return reader.doc(item)
    audit = sealed(registration['audit'])
    inv = sealed(registration['invocation'])
    intent = sealed(registration['intent'])
    verified = sealed(registration['verified'])
    require(audit['actor'] == 'codex:/root' and
            audit['status'] == 'ACTUAL_CANONICAL_REGISTRATION_CLOSED_NO_CASE_ACCEPTANCE' and
            audit['before'] == scope['expected_before_registration'] and audit['after'] == scope['expected_registration'] and
            audit['actual_registration_exit'] == 0, 'Registration audit not completed')
    require(inv['actor'] == 'codex:/root' and inv['actual_exit'] == 0 and
            inv['automatic_retry'] is False and inv['counter_reset'] is False, 'Registration invocation')
    require(audit['invocation_ref'] == registration['invocation'] and audit['intent_ref'] == registration['intent']
            and audit['verified_ref'] == registration['verified'] and audit['review_ref'] == inv['review_ref'], 'Audit links')
    reg_review = reader.doc(inv['review_ref'])
    require(reg_review['schema'] == 'researchos.root-registration-source-review.v1' and
            reg_review['reviewer'] == 'codex:/root/w05_merge_review' and
            reg_review['decision'] == 'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and
            reg_review['requested_changes'] == [] and reg_review['actual_registration_executed'] is False and
            reg_review['expected_before'] == scope['expected_before_registration'] and reg_review['expected_after'] == scope['expected_registration'], 'Registration independent review')
    for key, name in [('register_sha256','register.py'), ('wrapper_sha256','run.py'),
                      ('prepared_refs_sha256','prepared_refs.json'), ('audit_sha256','audit.json')]:
        rr = reader.ref(ROOT/scope['registration_namespace']/name)
        require(listed.get(str(bounded_path(rr['path']))) == rr and reg_review[key] == rr['sha256'], 'Registration script review')
    require(inv['runner_sha256'] == reg_review['register_sha256'] and
            inv['wrapper_sha256'] == reg_review['wrapper_sha256'], 'Registration actual scripts')
    for name in ['stdout', 'stderr']:
        rr = reader.ref(ROOT/scope['registration_namespace']/(name+'.raw'))
        require(listed.get(str(bounded_path(rr['path']))) == rr and inv[name+'_sha256'] == rr['sha256'], 'Registration raw')
    require([verified['checkpoint'],verified['ownership'],verified['failure_origins']] == scope['expected_registration']
            and verified['intent_ref'] == registration['intent'], 'Registration postverify')
    require(intent['actor'] == 'codex:/root' and intent['Main_head'] == scope['main_git']['head'] and
            intent['transition'] == {k:[scope['expected_before_registration'][i],scope['expected_registration'][i]] for i,k in enumerate(['checkpoint','ownership','failures'])}, 'Intent transition')
    changed=scope['registration_metadata_paths']
    require([x['path'] for x in intent['metadata']] == changed, 'Actual intent metadata differs from Root frozen layout')
    for idx, entry in enumerate(intent['metadata']):
        reader.verify(entry['original_ref'])
        desired = reader.verify(entry['desired_ref'])
        require(listed.get(str(bounded_path(entry['desired_ref']['path']))) == entry['desired_ref'], 'Desired unsealed')
        require(desired == reader.verify(canonical_copies[idx]['ref']), 'Actual canonical differs from desired')
        done_ref = reader.ref(ROOT/scope['registration_namespace']/('canonical-write.'+Path(entry['path']).stem+'.done.json'))
        done = sealed(done_ref)
        require(done['sha256'] == entry['desired_ref']['sha256'], 'Missing committed canonical')
    require([x['path'] for x in intent['unchanged']] == CANONICAL[len(changed):], 'Intent unchanged order')
    for idx, item in enumerate(intent['unchanged'],len(changed)):
        require(canonical_copies[idx]['ref']['sha256'] == item['sha256'], 'Unchanged canonical mismatch')
    original_failures = strict_json(reader.verify(intent['metadata'][0]['original_ref']))['failure_counters']
    require(len(original_failures) == scope['expected_before_registration'][2] and len(docs[0]['failure_counters']) == scope['expected_registration'][2] and
            docs[0]['failure_counters'][:len(original_failures)] == original_failures, 'Failure history prefix changed')
    return {'runner_review_ref':runner_ref, 'current43_authority_ref':authority_ref, 'registration_review_ref':inv['review_ref']}


def validate_grant(scope_path, scope_sha256, grant_path, grant_sha256):
    reader = Reader()
    scope, scope_ref = load_scope(reader, scope_path, scope_sha256)
    gr = reader.ref(grant_path)
    require(gr['sha256'] == grant_sha256, 'Grant SHA')
    root = bounded_path(scope['new_authorization_root'])
    require(bounded_path(grant_path) == root/'authorization.execute.json', 'Grant location')
    grant = reader.doc(gr)
    require(grant['schema'] == 'researchos.desktop58-finite-authorization.v1' and
            grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED' and
            grant['actual_registration_completed'] is True and grant['actor'] == 'codex:/root', 'Grant not executed registration')
    require(grant['scope_ref'] == scope_ref and grant['binding'] == binding(scope), 'Grant bound tuple')
    for entry in grant['canonical_copies']:
        require(bounded_path(entry['ref']['path']).parent == root, 'Canonical copy outside grant root')
    authority = validate_authority(reader,scope,scope_ref,grant['canonical_copies'],grant['registration_refs'])
    authority.update({'CLI2_qualification_ref':scope['current58_CLI2_qualification_ref'],
                      'CLI2_review_ref':scope['current58_CLI2_review_ref'],
                      'CLI2_manifest_ref':scope['current58_CLI2_manifest_ref']})
    require(grant['authority_review_refs'] == authority, 'Grant review links')
    require(grant['fresh_roots_observed_absent'] == [scope[k] for k in ['output_root','outer_output_root','export_root']] and
            grant['automatic_retry'] is False and grant['counter_reset'] is False,
            'Once/fresh allocation statement must be bound and independently reviewed')
    require(bounded_path(grant['prelaunch_evidence_ref']['path']).parent == root, 'Prelaunch evidence location')
    prelaunch = reader.doc(grant['prelaunch_evidence_ref'])
    require(prelaunch['runtime_resources_ref'] == scope['runtime_resources_ref'], 'Runtime manifest pin')
    require(bounded_path(prelaunch['toolchain_lock_ref']['path']) == ROOT/'execution/toolchains/locked.json', 'Toolchain lock path')
    tools = reader.doc(prelaunch['toolchain_lock_ref'])['tools']
    for key in ['python','git','go']:
        raw = reader.read(tools[key]['path'],external=True)
        require(hashlib.sha256(raw).hexdigest() == tools[key]['sha256'], 'Actual tool pin')
    require([x['kind'] for x in prelaunch['git']] == ['head','status','index'], 'Git preflight order')
    outputs = []
    for item, args in zip(prelaunch['git'], [['rev-parse','HEAD'],
                         ['status','--porcelain=v1','--untracked-files=no'],['diff','--cached','--name-only']]):
        require(item['argv'] == [tools['git']['path']] + args, 'Git preflight argv')
        result = item['result']
        cleanup = result['job_cleanup']
        require(result['actual_exit'] == 0 and result['error'] is None and result['timed_out'] is False
                and result['resumed'] is True and cleanup['errors'] == [] and
                all(cleanup.get(k) is True for k in ['kill_on_job_close_configured',
                    'assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']),
                'Git preflight process failure')
        outputs.append(reader.verify(item['stdout_ref']))
        reader.verify(item['stderr_ref'])
    require(outputs[0].decode('ascii').strip() == scope['main_git']['head'], 'Preflight HEAD')
    require(hashlib.sha256(outputs[1]).hexdigest() == scope['main_git']['status_sha256'] and
            len(outputs[1]) == scope['main_git']['status_bytes'], 'Preflight status')
    rows = outputs[1].splitlines()
    require(len(rows) == 13 and sum(x.startswith(b' D ') for x in rows) == 11 and
            outputs[2] == b'' and scope['main_git']['index_empty'] is True, 'Preflight index/13 rows')
    for item in grant['runtime_observation_refs']:
        require(bounded_path(item['path']).parent == root, 'Runtime observation location')
        observed = reader.doc(item)
        expected = {os.path.normcase(str(Path(x['path']).absolute())):x
                    for x in reader.doc(scope['runtime_resources_ref'])['files']}
        for key in ['launcher_ref','authorization_verifier_ref','owned_helper_ref','controller_ref','debug_helper_ref']:
            entry = scope[key]
            expected[os.path.normcase(str(bounded_path(entry['path'])))] = entry
        require(observed['all_observed_inputs_pre_pinned'] is True and observed['files'], 'Empty runtime observation')
        for entry in observed['files']:
            key = os.path.normcase(str(Path(entry['path']).absolute()))
            require(key in expected and entry['sha256'] == expected[key]['sha256'] and
                    entry['bytes'] == expected[key]['bytes'], 'Unpinned observed runtime')
            reader.verify(entry,external=True)
    # Return absolute refs: both existing consumers require canonical absolute paths.
    refs = []
    for path in sorted(reader.raw):
        raw = reader.read(path, external=not Path(path).is_relative_to(ROOT))
        refs.append({'path':path, 'sha256':hashlib.sha256(raw).hexdigest(), 'bytes':len(raw)})
    return {'authorization_paths':sorted(reader.raw), 'authorization_input_refs':refs,
            'scope':scope, 'grant':grant, 'source_commit':SOURCE,
            'fresh_current58_CLI2_qualified':True, 'original_CLI2_case_count':2,
            'registered_Root_scope_and_grant_verified':True}


