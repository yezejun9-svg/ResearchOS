"""Pure read-only authorization verifier. No process, SQLite, or DLL calls."""
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


def binding(scope):
    keys = ['owner','run_uuid','new_output_root','new_export_root','new_authorization_root','new_wrapper_root',
            'source_commit','actual_candidate_parent_expected','ordered_cases','limits',
            'registration_namespace','expected_registration','expected_before_registration','registration_metadata_paths',
            'runner_ref','launcher_ref','authorization_gate_ref','owned_process_helper_ref',
            'debug_tree_helper_ref','runtime_resources_ref','compiler_resources_ref','main_git',
            'launch_limits','python_flags','catalog_ref','instrumentation_ref','instrumented_source_ref',
            'instrumentation_helper_ref','current43_authority_ref','controller_review_path']
    return {key: scope[key] for key in keys}


def load_scope(reader, scope_path, scope_sha256):
    require(sys.flags.no_site, 'Python site startup must be disabled')
    sr = reader.ref(scope_path)
    require(sr['sha256'] == scope_sha256, 'Scope SHA')
    scope = reader.doc(sr)
    require(scope['owner'] == 'codex:/root' and scope['source_commit'] == SOURCE and
            scope['actual_candidate_parent_expected'] == PARENT , 'Candidate/owner mismatch')
    require(scope['ordered_cases'] == CASES and scope['limits'] == CAPS, 'Roster/caps mismatch')
    require(scope.get('preparation_only') is False and scope.get('execution_authorized') is True, 'Preparation cannot run')
    require(isinstance(scope['expected_registration'],list) and len(scope['expected_registration'])==3 and all(type(x) is int for x in scope['expected_registration']) and scope['expected_registration'][0]>323, 'Explicit future registration missing')
    require(isinstance(scope['expected_before_registration'],list) and len(scope['expected_before_registration'])==3, 'Explicit previous registration missing')
    require(isinstance(scope['registration_namespace'],str) and scope['registration_namespace'].startswith('execution/v2.4/receipts/W05/W05-99/integration_codex/'), 'Registration namespace missing')
    require(scope['registration_metadata_paths'] in [CANONICAL[:2],CANONICAL],
            'Root must explicitly bind actual two- or four-file intent layout')
    require(scope['python_flags'] == ['-I', '-S', '-X', 'utf8'], 'Python isolation flags')
    require(scope['first_unexpected_stop'] is True and scope['same_input_automatic_retry'] is False
            and scope['counter_reset'] is False, 'Stop/retry policy')
    require(scope['source_acceptance'] is False and scope['Main_integration_authorized'] is False
            and scope['formal_increment'] == 0, 'Acceptance escalation')
    uid = scope['run_uuid']
    require(isinstance(uid, str) and len(uid) == 32 and all(c in '0123456789abcdef' for c in uid), 'Run UUID')
    if 'uuid' in scope:
        require(scope['uuid'] == uid, 'UUID alias mismatch')
    roots = [bounded_path(scope[k], False) for k in ['new_output_root', 'new_export_root', 'new_authorization_root','new_wrapper_root']]
    require(all(uid in p.name for p in roots) and len(set(roots)) == 4, 'Nonunique run roots')
    require(all(not a.is_relative_to(b) for a in roots for b in roots if a != b), 'Overlapping roots')
    require(roots[0].is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99') and
            roots[1].is_relative_to(ROOT/'.local') and
            roots[2].is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99') and
            roots[3].is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99'), 'Run root classes')
    for key in ['runner_ref', 'launcher_ref', 'authorization_gate_ref', 'owned_process_helper_ref']:
        reader.verify(scope[key])
    for key in ['current43_authority_ref','debug_tree_helper_ref','compiler_resources_ref','catalog_ref','instrumentation_ref','instrumented_source_ref','instrumentation_helper_ref']:
        reader.verify(scope[key])
    require(bounded_path(scope['authorization_gate_ref']['path']) == Path(__file__).resolve(), 'Gate path')
    runtime = reader.doc(scope['runtime_resources_ref'])
    require(isinstance(runtime.get('files'), list) and runtime['files'], 'Runtime inventory absent')
    seen = set()
    for item in runtime['files']:
        p = str(Path(item['path']).absolute())
        require(p not in seen, 'Duplicate runtime resource')
        seen.add(p)
        reader.verify(item, external=True)
    bounded_path(scope['controller_review_path'], False)
    require(scope['main_git']['head']==SOURCE, 'Current Main43 HEAD required')
    require(Path(sys.executable).resolve()==Path(reader.doc(reader.ref(ROOT/'execution/toolchains/locked.json'))['tools']['python']['path']).resolve(),'Pinned actual Python required')
    return scope, sr


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


def validate_authority(reader, scope, scope_ref, canonical_copies, registration):
    require([x['canonical_path'] for x in canonical_copies] == CANONICAL, 'Canonical order')
    docs = [reader.doc(x['ref']) for x in canonical_copies]
    cp, ow = docs[:2]
    require([cp['revision'], ow['revision'], len(cp['failure_counters'])] == scope['expected_registration'], 'Canonical revision')
    require(cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb', 'Project identity')
    wip = cp['work_in_progress']
    require(wip['cli43_fresh_compiler_held2_scope_ref'] == scope_ref, 'Scope not registered')
    authority_ref = wip['cli43_fresh_compiler_current_source_authority_ref']
    require(authority_ref == scope['current43_authority_ref'], 'Current43 authority pin')
    authority = reader.doc(authority_ref)
    require(authority['schema']=='researchos.cli43.current-source-validation-authority.v1' and
            authority['actor']=='codex:/root' and authority['source_commit']==SOURCE and
            authority['current_canonical_head']==SOURCE and authority['source_integration_completed'] is True and
            authority['formal_increment']==0, 'Actual current43 source authority missing')
    for rr in authority['sealed_integration_refs']:
        reader.verify(rr)
    require(len(authority['sealed_integration_refs'])>=3, 'Actual Main38/CLI8 and head-forward refs missing')
    validate_current58_source(reader, scope, authority, cp, ow)
    runner_ref = wip['cli43_fresh_compiler_controller_review_ref']
    require(bounded_path(runner_ref['path'])==bounded_path(scope['controller_review_path']), 'Controller review canonical path')
    review = reader.doc(runner_ref)
    require(review['schema'] == 'researchos.cli43-compiler-controller-static-review.v1' and
            review['reviewer'] == 'codex:/root/w05_merge_review' and
            review['decision'] == 'READY_FOR_ROOT_CURRENT43_HELD2_ONCE' and
            review['requested_changes'] == [], 'Controller independent review')
    for key, actual in [('runner_sha256', scope['runner_ref']['sha256']),
                        ('scope_sha256', scope_ref['sha256']),
                        ('launcher_sha256', scope['launcher_ref']['sha256']),
                        ('gate_sha256', scope['authorization_gate_ref']['sha256'])]:
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
    require(grant['schema'] == 'researchos.cli43-compiler-authorization.v1' and
            grant['status'] == 'ROOT_REGISTERED_EXECUTION_AUTHORIZED' and
            grant['actual_registration_completed'] is True and grant['actor'] == 'codex:/root', 'Grant not executed registration')
    require(grant['scope_ref'] == scope_ref and grant['binding'] == binding(scope), 'Grant bound tuple')
    for entry in grant['canonical_copies']:
        require(bounded_path(entry['ref']['path']).parent == root, 'Canonical copy outside grant root')
    authority = validate_authority(reader,scope,scope_ref,grant['canonical_copies'],grant['registration_refs'])
    require(grant['authority_review_refs'] == authority, 'Grant review links')
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
        for key in ['launcher_ref','authorization_gate_ref','owned_process_helper_ref','runner_ref','debug_tree_helper_ref']:
            entry = scope[key]
            expected[os.path.normcase(str(bounded_path(entry['path'])))] = entry
        require(observed['all_observed_inputs_pre_pinned'] is True and observed['files'], 'Empty runtime observation')
        for entry in observed['files']:
            key = os.path.normcase(str(Path(entry['path']).absolute()))
            require(key in expected and entry['sha256'] == expected[key]['sha256'] and
                    entry['bytes'] == expected[key]['bytes'], 'Unpinned observed runtime')
            reader.verify(entry,external=True)
    return {'authorization_paths': sorted(reader.raw), 'scope':scope, 'grant':grant,
            'authorization_input_refs':[reader.ref(p, external=not Path(p).is_relative_to(ROOT)) for p in sorted(reader.raw)]}
