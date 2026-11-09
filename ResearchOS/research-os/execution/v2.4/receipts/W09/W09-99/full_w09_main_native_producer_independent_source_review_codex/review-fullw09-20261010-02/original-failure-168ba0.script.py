"""Non-author delta and complete authority-shape review; no product invocation."""
import ast
import copy
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import types

sys.dont_write_bytecode = True
R = Path('D:/作品集/ResearchOS/research-os')
W = R / 'execution/v2.4/receipts/W09/W09-99'
S = W / 'full_w09_main_native_producer_source_codex/fullw09-20261010-02'
OLD = W / 'full_w09_main_native_producer_source_codex/fullw09-20261009-01'
PRIOR = W / 'full_w09_main_native_producer_independent_source_review_codex/review-fullw09-20261009-01'
D = Path(__file__).resolve().parent
ACTOR = 'codex:/root/full_w09_source_review'

def pin(path):
    path = Path(path)
    raw = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def load(path):
    return json.loads(Path(path).read_bytes())

def save(name, obj):
    with (D / name).open('xb') as stream:
        stream.write((json.dumps(obj, ensure_ascii=False, indent=2) + '\n').encode())
    return pin(D / name)

def inert(path, name):
    m = types.ModuleType(name)
    m.__file__ = str(path)
    exec(compile(Path(path).read_bytes(), str(path), 'exec'), m.__dict__)
    return m

def tail(path):
    size = path.stat().st_size
    with path.open('rb') as stream:
        head = stream.readline()
        stream.seek(max(len(head), size - 64 * 1024 * 1024))
        if stream.tell() != len(head): stream.readline()
        offset = stream.tell()
        raw = stream.read(size - offset)
    rows = []
    for line in raw.splitlines(keepends=True):
        try: item = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            offset += len(line); continue
        rows.append((offset, line, item))
        offset += len(line)
    return head, rows, size

def main():
    checks, findings = [], []
    def check(name, ok, detail=None):
        if not ok: raise AssertionError(name)
        checks.append(dict(name=name, status='PASS_SOURCE_ONLY', detail=detail))
    def reject(name, fn, code):
        try: fn()
        except (ValueError, KeyError, TypeError, FileNotFoundError) as exc:
            check(name, code in str(exc), dict(exception_type=type(exc).__name__, error=str(exc)))
            return
        raise AssertionError(name + '_ACCEPTED')
    expected = {'HDF.json': ('f5bbc877a80892fc25b944d35462ff49a230ae180a0c3fd1e87c9971fda34260', 8106),
                'MF.json': ('348787ca166129839be1e71c4128597c20e840590c02a1d2d263b2668ffb2715', 9888),
                'peer-audit-controls.json': ('006e8cd7737426e14ce8b4bfd201992cfecd419f5584e7969fe0e3eba8136c45', 4002),
                'inverse-and-pins.json': ('ce00d8bfdb4176360f159ad396b8a77a083e9e431316e341a74209086f3fea90', 10003)}
    for name, (digest, size) in expected.items():
        check('Root_input_' + name, pin(S / name) == dict(path=str(S / name), sha256=digest, bytes=size))
    h, mf, c, contract = [load(S / name) for name in ('HDF.json', 'MF.json', 'source.choice.json', 'root-calling-contract.json')]
    m = inert(S / 'full_w09_runtime.source.py', 'v2_independent_authority_runtime')
    check('reviewer_non_author', m.AUTHOR == h['actor_id'] == 'codex:/root/w09_formal_profile_source_impl'
          and ACTOR != m.AUTHOR and h['source_thread_id'] != os.environ['CODEX_THREAD_ID'])
    refs = [pin(S / 'HDF.json'), pin(S / 'MF.json'), *mf['members'], *c['common']['source21'],
            h['prior_source_hdf_ref'], h['prior_source_mf_ref'], h['prior_independent_decision_ref'],
            pin(PRIOR / 'independent-source-controls.json'), pin(PRIOR / 'original-new-failure-preserved.json')]
    refs.extend(pin(OLD / name) for name in contract['source_file_bindings'].values())
    for value in c['common'].values():
        if type(value) is dict and set(value) == {'path', 'sha256', 'bytes'}: refs.append(value)
    refs.extend(c['common']['tool_refs'].values())
    uniq = {}
    for ref in refs:
        key = ref['path'].casefold()
        check('same_pin_' + str(len(uniq)), key not in uniq or uniq[key] == ref)
        uniq[key] = ref
    refs = list(uniq.values())
    check('Source_guard_excludes_current_Canon', not set(str(path).casefold() for path in m.CANON).intersection(uniq))
    gm = inert(c['common']['guard_ref']['path'], 'v2_independent_guard')
    guard = gm.SourceReadGuard(per_file_cap=256 * 1024 * 1024, total_cap=2 * 1024 * 1024 * 1024)
    try:
        guard.acquire(refs)
        check('all_current_frozen_delta_pins', all(pin(ref['path']) == ref for ref in refs), len(refs))
        href, mref = pin(S / 'HDF.json'), pin(S / 'MF.json')
        pair_h, pair_refs = m.pair(href, mref)
        check('v2_pair_complete_31_members', pair_h == h and len(mf['members']) == 31 and len(pair_refs) == 33)
        package_error = None
        try: m.package_refs()
        except ValueError as exc:
            package_error = str(exc)
        check('actual_package_entry_rejects_sealed_v2', package_error == 'SOURCE_PACKAGE')
        status_node = next(node for node in ast.parse((S / 'full_w09_runtime.source.py').read_bytes()).body
                           if isinstance(node, ast.FunctionDef) and node.name == 'package_refs')
        actual_status = h['status']
        expected_status = 'SOURCE_READY_PENDING_INDEPENDENT_REVIEW'
        finding = dict(id='V2-SOURCE-BLOCKER-01', priority='BLOCKER', category='correctness',
            source_ref=pin(S / 'full_w09_runtime.source.py'), line=status_node.lineno + 2,
            title='The sealed v2 handoff status cannot pass package_refs',
            handoff_ref=href, actual_handoff_status=actual_status, runtime_required_status=expected_status,
            production_interface='package_refs()', actual_rejection='ValueError: SOURCE_PACKAGE',
            impact='validate_authority always stops at package_refs before the three actor audits and canonical registration; actual prepare/run cannot use this immutable v2 package.',
            suggested_change='Issue a new immutable revision whose Source HDF status matches the precise Source-only state required by package_refs, or update package_refs to validate the exact intended v2 schema/status. Keep fresh independent review, real actor audits, Scope, current Canon vector and lease as separate execution gates.',
            required_positive='Call real package_refs against the final sealed HDF/MF and then exercise the complete in-memory authority shape; a package marker grants no execution.',
            required_negatives=['wrong Source author', 'foreign HDF schema/status', 'old Source bindings', 'missing independent review', 'wrong real actor audit', 'expired lease', 'missing canonical owner/worker'])
        findings.append(finding)
        check('compiler_blueprint_unchanged', (S / 'compiler-source-blueprint.json').read_bytes() == (OLD / 'compiler-source-blueprint.json').read_bytes())
        old_c, old_contract = load(OLD / 'source.choice.json'), load(OLD / 'root-calling-contract.json')
        check('same_current_Main_Source21', c['common']['source21'] == old_c['common']['source21'])
        check('Scope_exact_fields_unchanged', contract['scope_required_fields'] == old_contract['scope_required_fields']
              and contract['request_exact_fields'] == old_contract['request_exact_fields'])
        bound = {key: pin(S / name) for key, name in contract['source_file_bindings'].items()}
        check('all_new_source_self_bindings', bound == contract['bound_source_refs'])
        for key, row in c['selectors'].items():
            old = old_c['selectors'][key]
            check(key + '_full_roster_and_route_unchanged', all(row[field] == old[field] for field in
                  ('selector', 'mode', 'native_scope', 'packages', 'selected_tests', 'expected_native_ids', 'go_test_argv_suffix',
                   'list_argv_suffix', 'assertion_owner', 'required_independent_modes')))
            check(key + '_fresh_current_paths', row['run_id'] != old['run_id'] and all(not Path(row[field]).exists()
                  for field in ('receipt_root', 'scratch_root', 'output_root'))
            check(key + '_new_namespace_run_path', Path(row['receipt_root']).parent == S
                  and row['receipt_root'] == str(S / ('actual-' + key + '-' + row['run_id'])))
        check('three_new_UUIDs_unique', len({row['run_id'] for row in c['selectors'].values()}) == 3)
        inv = load(S / 'inverse-and-pins.json')
        for row in inv['inverse_files']:
            check('exact_inverse_' + row['name'], Path(row['prior_ref']['path']).read_bytes() == Path(row['inverse_saved_ref']['path']).read_bytes()
                  and pin(row['new_ref']['path']) == row['new_ref'])
        source_hosts = load(S / 'actual-hostpairs.binding.json')
        for item in source_hosts['captures']:
            raw = Path(item['actual_capture_ref']['path']).read_bytes()
            check('source_host_pin_' + item['target'], pin(item['actual_capture_ref']['path']) == item['actual_capture_ref'])
            lines = raw.splitlines(keepends=True)
            check('source_host_three_rows_' + item['target'], len(lines) == 3)
            with Path(source_hosts['source_log']).open('rb') as stream:
                for offset, digest, line in zip(item['source_line_offsets'], item['original_line_sha256'], lines):
                    stream.seek(offset)
                    check('actual_source_host_byte_' + item['target'] + '_' + str(offset), stream.read(len(line)) == line and hashlib.sha256(line).hexdigest() == digest)
            head, call, result = map(json.loads, lines)
            check('actual_source_host_identity_' + item['target'], head['payload']['id'] == h['source_thread_id']
                  and call['payload']['call_id'] == result['payload']['call_id'] == item['call_id'])
        # Reproduce only the new author peer delta controls; no old 69/112 checks or product are rerun.
        text = (S / 'peer_audit_controls.py').read_text()
        old = 'path = N / "peer-audit-controls.json"'
        assert text.count(old) == 1
        text = text.replace(old, 'path = review_destination / "reproduced-peer-audit-controls.json"')
        control = types.ModuleType('v2_author_delta_reproduction')
        control.__file__ = str(S / 'peer_audit_controls.py')
        control.review_destination = D
        capture = io.StringIO()
        with redirect_stdout(capture): exec(compile(text, control.__file__, 'exec'), control.__dict__)
        reproduced, original = load(D / 'reproduced-peer-audit-controls.json'), load(S / 'peer-audit-controls.json')
        check('new_20_peer_delta_controls_reproduced', reproduced['controls'] == original['controls'] and reproduced['pass'] == 20)
        save('reproduced-peer-control.stdout.json', dict(stdout=capture.getvalue(), old_69_and_112_not_rerun=True))
        # Capture the actual NEW author's delivered v2 HDF from the fixed Root log.
        root_header, root_rows, root_size = tail(Path(m.ROOT_AUDIT))
        real_peer = None
        for before, after in zip(root_rows, root_rows[1:]):
            payload = after[2].get('payload', {})
            if (before[2].get('type') == 'inter_agent_communication_metadata' and payload.get('type') == 'agent_message'
                and payload.get('author') == '/root/w09_formal_profile_source_impl' and payload.get('recipient') == '/root'
                and href['sha256'] in after[1].decode()): real_peer = (before, after)
        check('actual_new_author_delivery_found', real_peer is not None)
        call, result = real_peer
        p = D / 'actual-v2-author-Root-peer.raw.jsonl'
        with p.open('xb') as stream: stream.write(root_header + call[1] + result[1])
        author_audit = save('actual-v2-author-Root-peer.binding.json', dict(schema='researchos.w09-native-producer.actual-audit.v1',
            actor_id=m.AUTHOR, Root_thread_id=m.ROOT_THREAD_ID, source_audit_path=m.ROOT_AUDIT,
            source_line_offsets=[0, call[0], result[0]], original_line_sha256=[hashlib.sha256(line).hexdigest() for line in (root_header, call[1], result[1])],
            source_prefix_size_observed=root_size, original_capture_ref=pin(p), binding_sha256=href['sha256']))
        check('actual_new_author_mapping_positive', m.actual_audit(author_audit, m.AUTHOR, href['sha256']) == [author_audit, pin(p)])
        for bad_actor in ('/root/w09_formal_profile_source_impl', 'codex:/root/../w09_formal_profile_source_impl', 'codex:/root/NAME',
                          'codex:/root/name/', 'codex:/root/name//child', True, None):
            reject('legal_actor_mapping_' + repr(bad_actor), lambda bad_actor=bad_actor: m.exact_host_peer_author(bad_actor), 'CANONICAL_PEER_ACTOR')
        old_peer_ref = pin(PRIOR / 'actual-Source-author-real-Root-peer.binding.json')
        reject('old_author_cannot_authorize_v2', lambda: m.actual_audit(old_peer_ref, m.AUTHOR, href['sha256']), 'AUDIT_FIXED_ROOT_ACTOR_BINDING')
        # Construct the WHOLE exact authority chain in memory. This does not create Scope, Canon, requests or execution rights.
        originals = m.read_ref, m.package_refs, m.actual_audit
        memory = {}
        def fixture(name, obj):
            raw = (json.dumps(obj, ensure_ascii=False) + '\n').encode()
            ref = dict(path=str(S / ('IN_MEMORY_' + name)), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            memory[ref['path']] = raw
            return ref
        def memory_read(ref):
            if ref['path'] in memory:
                raw = memory[ref['path']]
                m.require(m.raw_pin(Path(ref['path']), raw) == ref, 'IN_MEMORY_PIN')
                return raw
            return originals[0](ref)
        selector = m.choice('W09-G01')
        reviewer = 'codex:/root/in_memory_independent_peer'
        dr = fixture('review-decision', dict(schema=contract['review_schema'], decision=contract['review_decision'], actor_role='INDEPENDENT_NON_AUTHOR',
             actor_id=reviewer, source_handoff_ref=href, source_manifest_ref=mref, calling_contract_ref=pin(S / 'root-calling-contract.json'),
             **bound, selectors=c['selectors'], source21=c['common']['source21'], actual_executed=False, formal_case_accepted_delta=0))
        rm = fixture('review-MF', dict(members=[dr]))
        rh = fixture('review-HDF', dict(actor_id=reviewer, manifest_ref=rm, source_decision_ref=dr))
        review_audit, root_audit = fixture('mock-review-audit', {}), fixture('mock-Root-scope-audit', {})
        now = datetime.now(timezone.utc)
        scope = dict(schema=contract['scope_schema'], status='ROOT_AUTHORIZED_SINGLE_SELECTOR_NATIVE', issued_by=m.ROOT_ACTOR, executor=m.ROOT_ACTOR,
            source_handoff_ref=href, source_manifest_ref=mref, **bound, source_review_handoff_ref=rh, source_review_manifest_ref=rm, source_review_decision_ref=dr,
            source_author_audit_ref=author_audit, source_review_audit_ref=review_audit, lease_id='a' * 32,
            lease_issued_at=(now-timedelta(minutes=1)).isoformat(), lease_expires_at=(now+timedelta(minutes=5)).isoformat(),
            maximum_go_test_runs=1, maximum_go_list_runs=1,
            **{key: selector[key] for key in ('selector_key', 'selector', 'mode', 'native_scope', 'packages', 'source_root', 'run_id', 'receipt_root',
                'scratch_root', 'output_root', 'selected_tests', 'expected_native_ids', 'source21', 'list_timeout_seconds', 'producer_timeout_seconds', 'inner_Go_timeout_seconds')},
            **{key: False for key in m.BOOL_FALSE}, **{key: 0 for key in m.ZERO})
        sr = fixture('Scope', scope)
        owner = dict(owner=m.ROOT_ACTOR, current_source_writer=None, state='ROOT_REGISTERED_PENDING_SELECTOR_NATIVE', scope_ref=sr,
            source_handoff_ref=href, source_manifest_ref=mref, source_review_handoff_ref=rh, source_review_manifest_ref=rm,
            source_root=str(R), selector=selector['selector_key'], run_id=selector['run_id'], receipt_root=selector['receipt_root'],
            scratch_root=selector['scratch_root'], output_root=selector['output_root'], lease_id=scope['lease_id'],
            lease_issued_at=scope['lease_issued_at'], lease_expires_at=scope['lease_expires_at'], formal_case_accepted_delta=0, parent_acceptance=False)
        worker = dict(step_id='W09-99', slice_id=m.SLICE+'_'+selector['selector_key'], owner=m.ROOT_ACTOR, state=owner['state'], scope_ref=sr,
            source_handoff_ref=href, source_review_handoff_ref=rh, run_id=selector['run_id'], lease_id=scope['lease_id'])
        docs = [dict(revision=372, project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb', head=selector['expected_git_head'], workers=[worker],
                    work_in_progress=dict(w09_native_producer_scopes={selector['selector_key']: sr})),
                dict(revision=176, active_integrator=dict(id=m.ROOT_ACTOR), shared_integrator='qoder-desktop:/root/platform_owner',
                    card_path_bindings={'W09-99': dict(owner=m.ROOT_ACTOR, subtasks={m.OWNER_KEY+'_'+selector['selector_key']: owner})}), {}, {}]
        canon = []
        for path, doc in zip(m.CANON, docs):
            raw = json.dumps(doc).encode()
            ref = dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
            memory[str(path)] = raw
            canon.append(ref)
        vr = fixture('vector', dict(schema='researchos.w09-three-selector-native-canonical-vector.v1', checkpoint_revision=372, ownership_revision=176, refs=canon))
        q = dict(schema=contract['request_schema'], issued_by=m.ROOT_ACTOR, selector=selector['selector_key'], scope_ref=sr,
                 canonical_vector_ref=vr, calling_contract_ref=pin(S / 'root-calling-contract.json'), scope_audit_ref=root_audit)
        qr = fixture('request', q)
        m.read_ref = memory_read
        reject('real_complete_authority_chain_stops_at_sealed_package', lambda: m.validate_authority(qr, selector), 'SOURCE_PACKAGE')
        audit_calls = []
        def isolated_audits(ref, actor, binding):
            if ref == author_audit:
                return originals[2](ref, actor, binding)
            m.require((ref, actor, binding) == (review_audit, reviewer, dr['sha256'])
                      or (ref == root_audit and actor == m.ROOT_ACTOR and type(binding) is str and len(binding) == 64), 'SYNTHETIC_AUDIT_BINDING')
            audit_calls.append(actor)
            return [ref]
        # Bypass only the already-proven package status blocker to check remaining exact shape gates.
        m.package_refs = lambda: (href, mref, pair_refs)
        m.actual_audit = isolated_audits
        try:
            check('post_package_full_authority_shape_NO_EXECUTION_GRANT', m.validate_authority(qr, selector)[1] == scope
                  and audit_calls == [reviewer, m.ROOT_ACTOR])
            # Earlier exact Scope gates do not need synthetic audit rebinding.
            for key in contract['scope_required_fields']:
                bad = dict(scope)
                bad.pop(key)
                br = fixture('missing-Scope-'+key, bad)
                bqr = fixture('request-missing-'+key, dict(q, scope_ref=br))
                reject('required_Scope_field_'+key, lambda bqr=bqr: m.validate_authority(bqr, selector), 'SCOPE_FIELDS')
            for name, key, value, code in [
                ('extra-key', 'unlisted', True, 'SCOPE_FIELDS'), ('non-Root', 'executor', m.AUTHOR, 'ROOT_SCOPE'),
                ('formal-enabled', 'formal_acceptance', True, 'SCOPE_BOUNDARY'), ('bool-zero', 'formal_case_accepted_delta', False, 'SCOPE_BOUNDARY'),
                ('extra-Go-run', 'maximum_go_test_runs', 2, 'FINITE_EXECUTION_BUDGET'), ('wrong-runtime', 'runtime_ref', pin(OLD/'full_w09_runtime.source.py'), 'EXACT_SOURCE_CALLERS'),
                ('wrong-HDF', 'source_handoff_ref', pin(OLD/'HDF.json'), 'EXACT_SOURCE_PAIR'), ('old-run', 'run_id', old_c['selectors']['W09-G01']['run_id'], 'EXACT_SCOPE_run_id'),
                ('partial-tests', 'selected_tests', selector['selected_tests'][:-1], 'EXACT_SCOPE_selected_tests'),
                ('wrong-package', 'packages', ['./internal/domain'], 'EXACT_SCOPE_packages'),
                ('old-author-audit', 'source_author_audit_ref', old_peer_ref, 'SYNTHETIC_AUDIT_BINDING'),
                ('expired-lease', 'lease_expires_at', (now-timedelta(seconds=1)).isoformat(), 'CURRENT_FINITE_LEASE'),
                ('future-lease', 'lease_issued_at', (now+timedelta(minutes=1)).isoformat(), 'CURRENT_FINITE_LEASE'),
                ('unbounded-lease', 'lease_expires_at', (now+timedelta(hours=3)).isoformat(), 'CURRENT_FINITE_LEASE'),
                ('invalid-lease-id', 'lease_id', 'A'*32, 'CURRENT_FINITE_LEASE')]:
                bad = dict(scope)
                bad[key] = value
                br = fixture('bad-Scope-'+name, bad)
                bqr = fixture('bad-request-'+name, dict(q, scope_ref=br))
                reject('whole_authority_'+name, lambda bqr=bqr: m.validate_authority(bqr, selector), code)
            for key in contract['request_exact_fields']:
                bad = dict(q)
                bad.pop(key)
                br = fixture('missing-request-'+key, bad)
                reject('required_request_field_'+key, lambda br=br: m.validate_authority(br, selector), 'REQUEST_FIELDS')
            for name, index, mutate, code in [
                ('wrong-Root-role', 1, lambda doc: doc['active_integrator'].__setitem__('id', m.AUTHOR), 'ROOT_CURRENT_ROLE'),
                ('scope-not-registered', 0, lambda doc: doc['work_in_progress']['w09_native_producer_scopes'].__setitem__('W09-G01', pin(OLD/'HDF.json')), 'CANONICAL_SCOPE_REGISTRATION'),
                ('foreign-owner', 1, lambda doc: doc['card_path_bindings']['W09-99']['subtasks'][m.OWNER_KEY+'_W09-G01'].__setitem__('owner', m.AUTHOR), 'EXACT_REGISTERED_OWNER'),
                ('missing-worker', 0, lambda doc: doc.__setitem__('workers', []), 'UNIQUE_REGISTERED_WORKER'),
                ('duplicate-worker', 0, lambda doc: doc['workers'].append(copy.deepcopy(doc['workers'][0])), 'UNIQUE_REGISTERED_WORKER')]:
                doc = copy.deepcopy(docs[index])
                mutate(doc)
                before = memory[canon[index]['path']]
                raw = json.dumps(doc).encode()
                changed = dict(canon[index], sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
                vector_refs = list(canon)
                vector_refs[index] = changed
                memory[changed['path']] = raw
                bad_vr = fixture('bad-Canon-vector-'+name, dict(schema='researchos.w09-three-selector-native-canonical-vector.v1',
                    checkpoint_revision=372, ownership_revision=176, refs=vector_refs))
                bad_q = fixture('bad-Canon-request-'+name, dict(q, canonical_vector_ref=bad_vr))
                try: reject('registered_authority_'+name, lambda bad_q=bad_q: m.validate_authority(bad_q, selector), code)
                finally: memory[canon[index]['path']] = before
            # Preserve fixed request/scope refs while changing downstream documents in memory only.
            def replace_memory(ref, obj):
                raw = (json.dumps(obj, ensure_ascii=False) + '\n').encode()
                return dict(path=ref['path'], sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)), raw
            for name, key, value, code in [('bad-status', 'decision', 'CHANGES_REQUIRED', 'INDEPENDENT_SOURCE_DECISION'),
                ('author-self-review', 'actor_id', m.AUTHOR, 'SOURCE_DECISION_MEMBER'),
                ('wrong-source', 'source_handoff_ref', pin(OLD/'HDF.json'), 'REVIEW_BINDING_source_handoff_ref'),
                ('actual-claim', 'actual_executed', True, 'SOURCE_REVIEW_BOUNDARY'),
                ('formal-delta', 'formal_case_accepted_delta', 1, 'SOURCE_REVIEW_BOUNDARY')]:
                bad = json.loads(memory[dr['path']])
                bad[key] = value
                bad_dr = fixture('bad-review-'+name, bad)
                bad_rm = fixture('bad-review-MF-'+name, dict(members=[bad_dr]))
                bad_rh = fixture('bad-review-HDF-'+name, dict(actor_id=reviewer, manifest_ref=bad_rm, source_decision_ref=bad_dr))
                bad_scope = dict(scope, source_review_handoff_ref=bad_rh, source_review_manifest_ref=bad_rm, source_review_decision_ref=bad_dr)
                bad_sr = fixture('bad-review-Scope-'+name, bad_scope)
                bad_q = fixture('bad-review-request-'+name, dict(q, scope_ref=bad_sr))
                reject('independent_review_gate_'+name, lambda bad_q=bad_q: m.validate_authority(bad_q, selector), code)
        finally:
            m.read_ref, m.package_refs, m.actual_audit = originals
        check('all_delta_inputs_preserved', all(pin(ref['path']) == ref for ref in refs))
        check('all_future_directories_still_absent', all(not Path(row[key]).exists() for row in c['selectors'].values()
              for key in ('receipt_root', 'scratch_root', 'output_root')))
    finally:
        cleanup = guard.close()
        guard_ref = save('delta-Source-guard.closed.json', cleanup)
    check('all_Source_guards_closed_zero', cleanup['closed'] is True and cleanup['retained_handles_count'] == 0 and not cleanup['errors'])
    observation = dict(schema='researchos.fullw09-v2-independent-delta-and-authority-review.v1', status='CHANGES_REQUIRED',
        actor_id=ACTOR, reviewer_thread_id=os.environ['CODEX_THREAD_ID'], findings=findings, checks=checks,
        actual_Source_package_entry_called=True, actual_new_author_peer_audit_verified=True,
        author_new_controls_reproduced=20, prior_69_and_112_reused_not_reexecuted=True,
        complete_authority_shape_scope_fields_checked=len(contract['scope_required_fields']), request_fields_checked=len(contract['request_exact_fields']),
        authority_fixture='IN_MEMORY_ONLY; package gate bypassed solely for later shape checks; reviewer and Scope audits synthetic; new author audit REAL',
        real_current_Canon_read=False, real_Scope_issued=False, real_request_issued=False, actual_prepare_run=False,
        actual_Go_runs=0, actual_Native_runs=0, actual_SQL_runs=0, actual_dispatcher_runs=0, actual_model_provider_calls=0,
        Main_written=False, Canon_written=False, current_CanonicalPair_held=False, execution_grant=False,
        formal_case_accepted_delta=0, all_Source_guards_closed=True, retained_handles_count=0,
        original_failure_ordinals_preserved=[1042, 1044, 1045, 1047], new_root_ordinal_self_assigned=False,
        guard_ref=guard_ref, source_author_actual_peer_ref=author_audit)
    result = save('delta-authority-review.json', observation)
    print(json.dumps(dict(status='CHANGES_REQUIRED', controls_ref=result, blocker=findings[0], check_count=len(checks),
        guard_ref=guard_ref, actual_new_author_peer_ref=author_audit, all_Source_guards_closed=True,
        retained_handles_count=0, actual_Go_runs=0, actual_Native_runs=0, formal_case_accepted_delta=0), ensure_ascii=False), flush=True)

if __name__ == '__main__': main()
