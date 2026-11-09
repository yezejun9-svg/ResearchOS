"""Pure read-only authorization verifier. No process, SQLite, or DLL calls."""
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(r'D:/作品集/ResearchOS/research-os')
REGISTRATION = 'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-root-r319'
CANONICAL = ['execution/v2.4/' + n + '.json' for n in
             ['checkpoint', 'path_ownership', 'step_state', 'commands']]
CASES = ['NullContext', 'OwnedContext', 'ContextNotResultFilter', 'ExactReplayAfterCommit',
         'ChangedPayloadConflict', 'ChangedSIDConflict', 'CrossProjectContext',
         'ForeignPrincipalContext', 'ForeignPrincipalNullList', 'UnknownContext',
         'ProjectGrantDenied', 'CrossProjectCursor', 'CrossPrincipalCursor', 'MalformedRequest']
CAPS = {'cases': 14, 'per_case_HTTP_maximum': 16, 'total_HTTP_maximum': 224,
        'SDK_MODEL_Node_external_paid_private_calls': 0}
SOURCE = 'a5d6d16ffaf129de0361470c3a1570228bd259a2'
PARENT = '534857db99fa5e694987f877af74c322eaa2a0b3'
SOURCE_HASHES = {
    'internal/api/v2_sessions_test.go': '9556e94e5a3dabf298494edcd160382b40474dc153f1138cf3157c677acb76ae',
    'internal/domain/client_protocol_sessions.go': '7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3'}


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
    keys = ['owner', 'run_uuid', 'new_output_root', 'new_export_root', 'new_authorization_root',
            'source_commit', 'actual_candidate_parent_expected', 'source_paths_sha256',
            'ordered_cases', 'limits', 'registration_namespace', 'expected_registration',
            'runner_ref', 'launcher_ref', 'authorization_gate_ref', 'owned_process_helper_ref',
            'author14_review_ref', 'author14_handoff_ref', 'author14_manifest_ref',
            'runtime_resources_ref', 'main_git', 'launch_limits', 'python_flags']
    return {key: scope[key] for key in keys}


def load_scope(reader, scope_path, scope_sha256):
    require(sys.flags.no_site, 'Python site startup must be disabled')
    sr = reader.ref(scope_path)
    require(sr['sha256'] == scope_sha256, 'Scope SHA')
    scope = reader.doc(sr)
    require(scope['owner'] == 'codex:/root' and scope['source_commit'] == SOURCE and
            scope['actual_candidate_parent_expected'] == PARENT and
            scope['source_paths_sha256'] == SOURCE_HASHES, 'Candidate/owner mismatch')
    require(scope['ordered_cases'] == CASES and scope['limits'] == CAPS, 'Roster/caps mismatch')
    require(scope['registration_namespace'] == REGISTRATION and
            scope['expected_registration'] == [319, 147, 413], 'Registration identity')
    require(scope['python_flags'] == ['-I', '-S', '-X', 'utf8'], 'Python isolation flags')
    require(scope['first_unexpected_stop'] is True and scope['same_input_automatic_retry'] is False
            and scope['counter_reset'] is False, 'Stop/retry policy')
    require(scope['source_acceptance'] is False and scope['Main_integration_authorized'] is False
            and scope['formal_increment'] == 0, 'Acceptance escalation')
    uid = scope['run_uuid']
    require(isinstance(uid, str) and len(uid) == 32 and all(c in '0123456789abcdef' for c in uid), 'Run UUID')
    if 'uuid' in scope:
        require(scope['uuid'] == uid, 'UUID alias mismatch')
    roots = [bounded_path(scope[k], False) for k in ['new_output_root', 'new_export_root', 'new_authorization_root']]
    require(all(uid in p.name for p in roots) and len(set(roots)) == 3, 'Nonunique run roots')
    require(all(not a.is_relative_to(b) for a in roots for b in roots if a != b), 'Overlapping roots')
    require(roots[0].is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99') and
            roots[1].is_relative_to(ROOT/'.local') and
            roots[2].is_relative_to(ROOT/'execution/v2.4/receipts/W05/W05-99'), 'Run root classes')
    for key in ['runner_ref', 'launcher_ref', 'authorization_gate_ref', 'owned_process_helper_ref']:
        reader.verify(scope[key])
    for key in ['author14_handoff_ref', 'author14_manifest_ref']:
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
    return scope, sr


def registration_refs(reader):
    base = ROOT / REGISTRATION
    return {key: reader.ref(base/name) for key, name in {
        'manifest': 'manifest.json', 'audit': 'registration-audit.json',
        'invocation': 'invocation.json', 'intent': 'canonical-write.intent.json',
        'verified': 'canonical-write.verified.json'}.items()}


def validate_authority(reader, scope, scope_ref, canonical_copies, registration):
    require([x['canonical_path'] for x in canonical_copies] == CANONICAL, 'Canonical order')
    docs = [reader.doc(x['ref']) for x in canonical_copies]
    cp, ow = docs[:2]
    require([cp['revision'], ow['revision'], len(cp['failure_counters'])] == [319, 147, 413], 'Canonical revision')
    require(cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb', 'Project identity')
    wip = cp['work_in_progress']
    require(wip['session_list_closedcopy_root_finite14_scope_ref'] == scope_ref, 'Scope not registered')
    author_ref = wip['session_list_closedcopy_root_author14_review_ref']
    require(author_ref == scope['author14_review_ref'], 'Author evidence review pin')
    author = reader.doc(author_ref)
    require(author['actor'] == 'codex:/root/sources_parent_impl' and
            author['status'] == 'READY_FOR_ROOT_INDEPENDENT_FINITE14' and
            author['source_commit'] == SOURCE and author['failed_checks'] == [] and
            author['source_acceptance'] is False, 'Author evidence not independently ready')
    runner_ref = wip['session_list_closedcopy_root_runner_review_ref']
    review = reader.doc(runner_ref)
    require(review['schema'] == 'researchos.session-list-root-runner-static-review.v1' and
            review['reviewer'] == 'codex:/root/w05_merge_review' and
            review['decision'] == 'READY_FOR_CANONICAL_ROOT_FINITE14_ONCE' and
            review['requested_changes'] == [], 'Runner independent review')
    for key, actual in [('runner_sha256', scope['runner_ref']['sha256']),
                        ('scope_sha256', scope_ref['sha256']),
                        ('launcher_sha256', scope['launcher_ref']['sha256']),
                        ('gate_sha256', scope['authorization_gate_ref']['sha256'])]:
        require(review[key] == actual, 'Runner review mismatch ' + key)
    require(registration == registration_refs(reader), 'Registration ref path/hash mismatch')
    manifest = reader.doc(registration['manifest'])
    entries = manifest['entries']
    require(len(entries) == manifest['count'], 'Registration manifest count')
    listed = {}
    for item in entries:
        path = bounded_path(item['path'])
        require(path.is_relative_to(ROOT/REGISTRATION), 'Foreign registration manifest entry')
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
            audit['before'] == [318, 146, 410] and audit['after'] == [319, 147, 413] and
            audit['actual_registration_exit'] == 0, 'Registration audit not completed')
    require(inv['actor'] == 'codex:/root' and inv['actual_exit'] == 0 and
            inv['automatic_retry'] is False and inv['counter_reset'] is False, 'Registration invocation')
    require(audit['invocation_ref'] == registration['invocation'] and audit['intent_ref'] == registration['intent']
            and audit['verified_ref'] == registration['verified'] and audit['review_ref'] == inv['review_ref'], 'Audit links')
    reg_review = reader.doc(inv['review_ref'])
    require(reg_review['schema'] == 'researchos.root-registration-source-review.v1' and
            reg_review['reviewer'] != 'codex:/root' and
            reg_review['decision'] == 'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' and
            reg_review['requested_changes'] == [] and reg_review['actual_registration_executed'] is False and
            reg_review['expected_before'] == [318,146,410] and reg_review['expected_after'] == [319,147,413], 'Registration independent review')
    for key, name in [('register_sha256','register.py'), ('wrapper_sha256','run.py'),
                      ('prepared_refs_sha256','prepared_refs.json'), ('audit_sha256','audit.json')]:
        rr = reader.ref(ROOT/REGISTRATION/name)
        require(listed.get(str(bounded_path(rr['path']))) == rr and reg_review[key] == rr['sha256'], 'Registration script review')
    require(inv['runner_sha256'] == reg_review['register_sha256'] and
            inv['wrapper_sha256'] == reg_review['wrapper_sha256'], 'Registration actual scripts')
    for name in ['stdout', 'stderr']:
        rr = reader.ref(ROOT/REGISTRATION/(name+'.raw'))
        require(listed.get(str(bounded_path(rr['path']))) == rr and inv[name+'_sha256'] == rr['sha256'], 'Registration raw')
    require([verified['checkpoint'],verified['ownership'],verified['failure_origins']] == [319,147,413]
            and verified['intent_ref'] == registration['intent'], 'Registration postverify')
    require(intent['actor'] == 'codex:/root' and intent['Main_head'] == scope['main_git']['head'] and
            intent['transition'] == {'checkpoint':[318,319], 'ownership':[146,147], 'failures':[410,413]}, 'Intent transition')
    require([x['path'] for x in intent['metadata']] == CANONICAL[:2], 'Intent metadata shape')
    for idx, entry in enumerate(intent['metadata']):
        reader.verify(entry['original_ref'])
        desired = reader.verify(entry['desired_ref'])
        require(listed.get(str(bounded_path(entry['desired_ref']['path']))) == entry['desired_ref'], 'Desired unsealed')
        require(desired == reader.verify(canonical_copies[idx]['ref']), 'Actual canonical differs from desired')
        done_ref = reader.ref(ROOT/REGISTRATION/('canonical-write.'+Path(entry['path']).stem+'.done.json'))
        done = sealed(done_ref)
        require(done['sha256'] == entry['desired_ref']['sha256'], 'Missing committed canonical')
    require([x['path'] for x in intent['unchanged']] == CANONICAL[2:], 'Intent unchanged order')
    for idx, item in enumerate(intent['unchanged'],2):
        require(canonical_copies[idx]['ref']['sha256'] == item['sha256'], 'Unchanged canonical mismatch')
    original_failures = strict_json(reader.verify(intent['metadata'][0]['original_ref']))['failure_counters']
    require(len(original_failures) == 410 and len(docs[0]['failure_counters']) == 413 and
            docs[0]['failure_counters'][:410] == original_failures, 'Failure history prefix changed')
    return {'runner_review_ref':runner_ref, 'author14_review_ref':author_ref, 'registration_review_ref':inv['review_ref']}


def validate_grant(scope_path, scope_sha256, grant_path, grant_sha256):
    reader = Reader()
    scope, scope_ref = load_scope(reader, scope_path, scope_sha256)
    gr = reader.ref(grant_path)
    require(gr['sha256'] == grant_sha256, 'Grant SHA')
    root = bounded_path(scope['new_authorization_root'])
    require(bounded_path(grant_path) == root/'authorization.execute.json', 'Grant location')
    grant = reader.doc(gr)
    require(grant['schema'] == 'researchos.root-finite14-authorization.v2' and
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
    for key in ['python','git']:
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
        for key in ['launcher_ref','authorization_gate_ref','owned_process_helper_ref']:
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
