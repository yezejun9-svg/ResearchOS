"""Root-only finite registration, single-target adoption, and consumed closure.

Registration and closure are separate invocations from Main adoption. No product
process, model, Go, SQL, automatic retry, or automatic inverse is invoked here.
"""
from pathlib import Path
from datetime import datetime, timezone, timedelta
from ctypes import wintypes
import copy
import ctypes
import hashlib
import json
import os
import sys
import types
import uuid

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
TARGET = R / 'ops/ci/retrieval.py'
CANON = [R / 'execution/v2.4' / name for name in
         ('checkpoint.json', 'path_ownership.json', 'step_state.json', 'commands.json')]
ROOT = 'codex:/root'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
BEFORE = '9d94366591e1620c62abd27c34a8e513499cf10f8fdeaf741fe2e5a20b63e0c2'
AFTER = 'b85fb90d9927a2427ee29a5ff756b8e7d18b0639e9a3910a7621991bc3788f11'
GUARD = R / 'execution/v2.4/receipts/W05/W05-99/source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
TP = R / 'execution/v2.4/receipts/W05/W05-99/mu_sdk_controller_revision_v5_codex/e5953a6723c44426a05b5bb540186cdc/canonical_transactions.py'
AUDIT_RUNTIME = R / 'execution/v2.4/receipts/W09/W09-99/full_w09_main_native_producer_source_codex/fullw09-20261010-03/full_w09_runtime.source.py'
IMPORT_PINS = [(GUARD, 'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85'),
               (TP, '094e1a97fb00d01412b4e71e2d740b800accfce00e607c6853cb634280b12ba9'),
               (AUDIT_RUNTIME, '1709bc96848fb52fe4ddde8591fe063576515aaabdc63d35630b1023a82ccc08')]

def require(ok, message):
    if not ok:
        raise ValueError(message)

def pin(path, raw=None):
    path = Path(path)
    raw = path.read_bytes() if raw is None else raw
    return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))

def same_ref(a, b):
    return Path(a['path']) == Path(b['path']) and a['sha256'] == b['sha256'] and a['bytes'] == b['bytes']

def load_ref(ref):
    raw = Path(ref['path']).read_bytes()
    require(same_ref(pin(ref['path'], raw), ref), 'EXACT_INPUT_PIN')
    return json.loads(raw)

def save(path, value, raw=False):
    path = Path(path)
    data = value if raw else (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return pin(path, data)

def imported(path, digest, name):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'IMPORT_SHA')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module

def refs_in(value):
    if isinstance(value, dict):
        if set(value) == {'path', 'sha256', 'bytes'}:
            yield value
        else:
            for child in value.values():
                yield from refs_in(child)
    elif isinstance(value, list):
        for child in value:
            yield from refs_in(child)

def unique(refs):
    result = {}
    for ref in refs:
        require(Path(ref['path']).is_absolute(), 'ABSOLUTE_REF')
        key = os.path.normcase(os.path.normpath(ref['path']))
        require(key not in result or same_ref(result[key], ref), 'CONFLICTING_PIN')
        result[key] = ref
    return list(result.values())

def guarded(refs, out, action):
    guard = imported(*IMPORT_PINS[0], 'root_c19_adoption_guard').SourceReadGuard(
        per_file_cap=64 * 1024 * 1024, total_cap=512 * 1024 * 1024)
    try:
        guard.acquire(unique(refs))
        result = action()
    finally:
        closed = guard.close()
        closed_ref = save(out, closed)
    require(closed['closed'] and not closed['errors'] and closed['retained_handles_count'] == 0,
            'ALL_INPUT_HANDLES_CLOSED')
    return result, closed_ref

def proofs(config):
    source = load_ref(config['source_handoff_ref'])
    contract = load_ref(config['calling_contract_ref'])
    review = load_ref(config['review_decision_ref'])
    reviewer = config['reviewer_actor']
    require(reviewer not in (ROOT, source['source_author']), 'INDEPENDENT_NONAUTHOR_REVIEWER')
    require(source['source_author'] == 'codex:/root/full_w09_source_review', 'SOURCE_AUTHOR')
    require(same_ref(source['calling_contract_ref'], config['calling_contract_ref']), 'CALLING_CONTRACT')
    require(contract['sourcecandidate_ref']['sha256'] == AFTER, 'CANDIDATE_SHA')
    for keys, value in config['review_acceptance_requirements']:
        item = review
        for key in keys:
            item = item[key]
        require(item == value, 'ACTUAL_REVIEW_ACCEPTANCE:' + '/'.join(keys))
    require(any(same_ref(ref, contract['sourcecandidate_ref']) for ref in refs_in(review)), 'REVIEW_EXACT_CANDIDATE')
    runtime = imported(*IMPORT_PINS[2], 'root_c19_actual_peer')
    runtime.actual_audit(config['author_witness_ref'], source['source_author'], source['decision_ref']['sha256'])
    runtime.actual_audit(config['review_witness_ref'], reviewer, config['review_witness_binding_sha256'])
    for hdf_ref in (config['source_handoff_ref'], config['review_handoff_ref']):
        hdf = load_ref(hdf_ref)
        manifest_ref = hdf.get('manifest_ref', hdf.get('MF_ref'))
        if manifest_ref is not None:
            require(any(same_ref(manifest_ref, x) for x in
                        (config['source_manifest_ref'], config['review_manifest_ref'])), 'MANIFEST_CHAIN')
    for ref in config['closed_review_guard_refs']:
        closed = load_ref(ref)
        require(closed['closed'] and not closed['errors'] and closed['retained_handles_count'] == 0,
                'SOURCE_REVIEW_GUARDS_CLOSED')
    return source, contract

def proof_refs(config):
    names = ('source_handoff_ref', 'source_manifest_ref', 'calling_contract_ref',
             'author_witness_ref', 'review_handoff_ref', 'review_manifest_ref',
             'review_decision_ref', 'review_witness_ref')
    refs = [config[name] for name in names] + config['closed_review_guard_refs']
    for name in ('source_manifest_ref', 'review_manifest_ref'):
        refs += load_ref(config[name])['members']
    for name in ('author_witness_ref', 'review_witness_ref'):
        refs.append(load_ref(config[name])['original_capture_ref'])
    refs += [pin(p) for p, digest in IMPORT_PINS]
    refs += [pin(Path(__file__).resolve()), pin(Path(sys.executable))]
    return unique(refs)

def authority(request, cp, ow):
    scope = load_ref(request['scope_ref'])
    require(scope['issued_by'] == ROOT and scope['root_thread_id'] == THREAD, 'ROOT_SCOPE')
    require(scope['write_targets'] == [str(TARGET)] and scope['execution_limit'] == 1, 'SINGLE_TARGET_ONCE')
    require(datetime.fromisoformat(scope['lease_issued_at']) <= datetime.now(timezone.utc)
            < datetime.fromisoformat(scope['lease_expires_at']), 'FINITE_CURRENT_LEASE')
    key = request['owner_key']
    owner = ow['card_path_bindings']['W09-99']['subtasks'][key]
    workers = [x for x in cp['workers'] if x.get('slice_id') == key]
    require(len(workers) == 1 and owner['owner'] == workers[0]['owner'] == ROOT, 'ROOT_OWNER_WORKER')
    require(same_ref(owner['scope_ref'], request['scope_ref'])
            and same_ref(workers[0]['scope_ref'], request['scope_ref']), 'EXACT_OWNER_WORKER_SCOPE')
    require(owner['state'] == workers[0]['state'] == 'ROOT_REGISTERED_SINGLE_TARGET_MAIN_ADOPTION'
            and owner['lease_id'] == workers[0]['lease_id'] == scope['lease_id'], 'UNCONSUMED_BOUND_LEASE')
    require(ow['active_integrator']['id'] == ROOT and ow['card_path_bindings']['W09-99']['owner'] == ROOT,
            'CURRENT_ROOT_INTEGRATOR')

def register(config_path):
    config_ref = pin(config_path)
    config = load_ref(config_ref)
    require(config['root_actor'] == ROOT and config['root_thread_id'] == THREAD, 'ROOT_CONFIG')
    require(len(config['review_acceptance_requirements']) > 0, 'NONEMPTY_REAL_REVIEW_GATE')
    expected = config['expected_current4']
    require(all(same_ref(pin(p), ref) for p, ref in zip(CANON, expected)), 'CURRENT_FOUR_CAS')
    request_id = uuid.uuid4().hex
    out = N / ('c19-order-Main-adoption-' + request_id)
    out.mkdir(exist_ok=False)
    journal = out / 'registration-journal'
    journal.mkdir()
    def prepare():
        source, contract = proofs(config)
        require(same_ref(pin(TARGET), contract['before_main_ref']), 'BEFORE_MAIN')
        now = datetime.now(timezone.utc)
        scope = dict(schema='researchos.root-single-target-Main-adoption-scope.v1', issued_by=ROOT,
            root_thread_id=THREAD, request_id=request_id, parent='W09', step_id='W09-99',
            write_targets=[str(TARGET)], output_root=str(out), execution_limit=1,
            lease_id=uuid.uuid4().hex, lease_issued_at=now.isoformat(),
            lease_expires_at=(now + timedelta(minutes=20)).isoformat(),
            sourcecandidate_ref=contract['sourcecandidate_ref'], before_main_ref=contract['before_main_ref'],
            independent_review_ref=config['review_decision_ref'], before_canonical_refs=expected,
            product_execution_permitted=False, formal_acceptance=False)
        scope_ref = save(out / 'scope.root.json', scope)
        key = 'C19_MAIN_ORDER_ADOPTION_' + request_id
        def transform(cp, ow):
            require(cp['revision'] == config['expected_cp_revision'] and ow['revision'] == config['expected_ow_revision'],
                    'CANON_REVISIONS')
            require(ow['active_integrator']['id'] == ROOT and ow['card_path_bindings']['W09-99']['owner'] == ROOT,
                    'ROOT_CURRENT_OWNER')
            require(key not in ow['card_path_bindings']['W09-99']['subtasks']
                    and not any(x.get('slice_id') == key for x in cp['workers']), 'NEW_SCOPE_KEY')
            owner = dict(owner=ROOT, current_source_writer=ROOT,
                state='ROOT_REGISTERED_SINGLE_TARGET_MAIN_ADOPTION', scope_ref=scope_ref,
                lease_id=scope['lease_id'], lease_issued_at=scope['lease_issued_at'],
                lease_expires_at=scope['lease_expires_at'], source_paths=[str(TARGET)], formal_acceptance=False)
            worker = dict(owner, step_id='W09-99', slice_id=key)
            cp['workers'].append(worker)
            cp['work_in_progress']['c19_order_Main_adoption_scope_ref'] = scope_ref
            ow['card_path_bindings']['W09-99']['subtasks'][key] = owner
            cp['expected_previous_revision'] = cp['revision']
            cp['revision'] += 1
            ow['revision'] += 1
            for value in (cp, ow):
                value['updated_at'] = now.isoformat()
                value['updated_by'] = ROOT
            return cp, ow
        tp = imported(*IMPORT_PINS[1], 'root_c19_adoption_canon')
        committed = tp.update_pair(expected[:2], transform, journal, 'activate')
        current = [committed['checkpoint_ref'], committed['ownership_ref'], *expected[2:]]
        request = dict(config, schema='researchos.w09-c19-main-order-actual-adoption-request.v1',
            request_id=request_id, scope_ref=scope_ref, owner_key=key,
            target_path=str(TARGET), before_main_ref=contract['before_main_ref'],
            sourcecandidate_ref=contract['sourcecandidate_ref'], before_source_ref=contract['before_source_ref'],
            current_canonical_refs=current, registration_result=committed,
            original_byte_archive_path=str(out / 'Main.before.raw'), config_ref=config_ref)
        return save(out / 'adoption.actual.request.root.json', request)
    request_ref, guard_ref = guarded(proof_refs(config) + [config_ref, *expected[2:], pin(TARGET)],
                                    out / 'registration-source-guard.closed.json', prepare)
    print(json.dumps(dict(request_ref=request_ref, registration_guard_closed_ref=guard_ref,
                          Main_written=False, formal_acceptance=False), ensure_ascii=False))

def adopt(request_path):
    request_ref = pin(request_path)
    request = load_ref(request_ref)
    out = request_path.parent
    require(request['root_actor'] == ROOT and request['root_thread_id'] == THREAD, 'ROOT_REQUEST')
    current = request['current_canonical_refs']
    registration_closed_ref = pin(out / 'registration-source-guard.closed.json')
    def validate():
        source, contract = proofs(request)
        registration_closed = load_ref(registration_closed_ref)
        require(registration_closed['closed'] and not registration_closed['errors']
                and registration_closed['retained_handles_count'] == 0, 'REGISTRATION_GUARD_CLOSED')
        cp, ow = (load_ref(ref) for ref in current[:2])
        authority(request, cp, ow)
        before = Path(request['before_source_ref']['path']).read_bytes()
        after = Path(request['sourcecandidate_ref']['path']).read_bytes()
        old = b'selected = GROUPS[check] if check else list(TESTS)'
        new = b'selected = GROUPS[check] if check else [name for name in CASES[case] if name in TESTS]'
        require(before.count(old) == 1 and after.count(new) == 1 and before.replace(old, new, 1) == after,
                'EXACT_ONE_EXPRESSION_AND_COMPLETE_INVERSE')
        require(pin(TARGET, before)['sha256'] == BEFORE and len(before) == 14509,
                'WHOLE_BEFORE_BYTES')
        require(pin(TARGET, after)['sha256'] == AFTER and len(after) == 14545,
                'WHOLE_CANDIDATE_BYTES')
        return before, after
    (before, after), guard_ref = guarded(proof_refs(request) + [request_ref, request['scope_ref'], registration_closed_ref, *current],
                                        out / 'adoption-source-guard.closed.json', validate)
    # All read guards above have closed0 before acquiring the exclusive Main file.
    scope = load_ref(request['scope_ref'])
    require(datetime.now(timezone.utc) < datetime.fromisoformat(scope['lease_expires_at']), 'LEASE_BEFORE_WRITE')
    for path in (TARGET, *TARGET.parents):
        require(not path.is_symlink() and not path.is_junction(), 'NO_REPARSE_PATH')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    H, D, B = ctypes.c_void_p, wintypes.DWORD, wintypes.BOOL
    def bind(name, args, result):
        fn = getattr(kernel, name)
        fn.argtypes, fn.restype = args, result
        return fn
    create = bind('CreateFileW', [wintypes.LPCWSTR, D, D, H, D, D, H], H)
    close = bind('CloseHandle', [H], B)
    size = bind('GetFileSizeEx', [H, ctypes.POINTER(ctypes.c_longlong)], B)
    seek = bind('SetFilePointerEx', [H, ctypes.c_longlong, H, D], B)
    read = bind('ReadFile', [H, H, D, ctypes.POINTER(D), H], B)
    write = bind('WriteFile', [H, H, D, ctypes.POINTER(D), H], B)
    end, flush = bind('SetEndOfFile', [H], B), bind('FlushFileBuffers', [H], B)
    final = bind('GetFinalPathNameByHandleW', [H, wintypes.LPWSTR, D, D], D)
    handle = None
    written = False
    close_error = None
    def checked(ok):
        if not ok:
            raise ctypes.WinError(ctypes.get_last_error())
    def owned_read():
        length = ctypes.c_longlong()
        checked(size(handle, ctypes.byref(length)))
        require(0 < length.value < 128 * 1024, 'TARGET_BOUNDED_SIZE')
        checked(seek(handle, 0, None, 0))
        buf, got = ctypes.create_string_buffer(length.value), D()
        checked(read(handle, buf, length.value, ctypes.byref(got), None))
        require(got.value == length.value, 'TARGET_COMPLETE_READ')
        return buf.raw[:got.value]
    try:
        handle = create(str(TARGET), 0x80000000 | 0x40000000, 0, None, 3, 0x80, None)
        require(bool(handle) and handle != ctypes.c_void_p(-1).value, 'TARGET_EXCLUSIVE_OPEN')
        name = ctypes.create_unicode_buffer(32768)
        count = final(handle, name, len(name), 0)
        require(0 < count < len(name) and Path(name.value.removeprefix('\\\\?\\')) == TARGET,
                'TARGET_EXACT_PHYSICAL_PATH')
        original = owned_read()
        require(original == before and same_ref(pin(TARGET, original), request['before_main_ref']),
                'MAIN_CAS_WHILE_EXCLUSIVE')
        before_ref = save(out / 'Main.before.raw', original, True)
        after_ref = save(out / 'Main.after.proposed.raw', after, True)
        save(out / 'intent.root.json', dict(request_ref=request_ref, original_archive_ref=before_ref,
            proposed_archive_ref=after_ref, input_guard_closed_ref=guard_ref, scope_ref=request['scope_ref'],
            mandatory_share_mode=0, automatic_inverse=False, automatic_retry=False))
        checked(seek(handle, 0, None, 0))
        buf, done = ctypes.create_string_buffer(after), D()
        checked(write(handle, buf, len(after), ctypes.byref(done), None))
        require(done.value == len(after), 'COMPLETE_TARGET_WRITE')
        checked(end(handle))
        checked(flush(handle))
        written = True
        require(owned_read() == after, 'EXCLUSIVE_TARGET_READBACK')
        save(out / 'committed.while-owned.json', dict(actual_Main_ref=pin(TARGET, after),
            original_archive_ref=before_ref, proposed_archive_ref=after_ref,
            actual_write_complete=True, actual_readback_while_exclusive=True,
            Canon_written=False, formal_acceptance=False))
    except BaseException as exc:
        partial = None
        if handle and handle != ctypes.c_void_p(-1).value:
            try:
                partial = save(out / 'Main.failed.partial.raw', owned_read(), True)
            except BaseException as observation:
                partial = dict(observation_error=repr(observation))
        save(out / 'adoption.failed.root.json', dict(error=repr(exc), written=written,
            partial_ref=partial, automatic_inverse=False, automatic_retry=False))
        raise
    finally:
        if handle and handle != ctypes.c_void_p(-1).value and not close(handle):
            close_error = ctypes.get_last_error()
        save(out / 'target-handle.closed.json', dict(target_handle_closed=close_error is None,
            CloseHandle_error=close_error, actual_write_complete=written))
    require(close_error is None and same_ref(pin(TARGET), dict(request['sourcecandidate_ref'], path=str(TARGET))),
            'CLOSED_CURRENT_MAIN')
    require(all(same_ref(pin(p), ref) for p, ref in zip(CANON, current)), 'CANON_UNCHANGED')
    result_ref = save(out / 'adoption.closed.root.json', dict(
        schema='researchos.w09-c19-main-order-actual-adoption.v1', actor_id=ROOT,
        root_thread_id=THREAD, created_utc=datetime.now(timezone.utc).isoformat(), request_ref=request_ref,
        scope_ref=request['scope_ref'], actual_Main_ref=pin(TARGET), before_archive_ref=before_ref,
        candidate_archive_ref=after_ref, source_guard_closed_ref=guard_ref,
        all_handles_closed=True, Canon_unchanged=True, four_fresh_Native_and_six_consumers_required=True,
        formal_acceptance=False, formal_case_accepted_delta=0))
    print(json.dumps(dict(adoption_closed_ref=result_ref, actual_Main_ref=pin(TARGET),
        all_handles_closed=True, Canon_unchanged=True, formal_acceptance=False), ensure_ascii=False))

def close_registration(request_path):
    request_ref = pin(request_path)
    request = load_ref(request_ref)
    out = request_path.parent
    result_ref = pin(out / 'adoption.closed.root.json')
    result = load_ref(result_ref)
    require(result['all_handles_closed'] and result['actual_Main_ref']['sha256'] == AFTER, 'REAL_CLOSED_ADOPTION')
    current = request['current_canonical_refs']
    journal = out / 'closure-journal'
    journal.mkdir(exist_ok=False)
    def transform(cp, ow):
        authority(request, cp, ow)
        owner = ow['card_path_bindings']['W09-99']['subtasks'][request['owner_key']]
        worker = next(x for x in cp['workers'] if x.get('slice_id') == request['owner_key'])
        now = datetime.now(timezone.utc).isoformat()
        for record in (owner, worker):
            record.update(state='CLOSED_ACTUAL_SINGLE_TARGET_MAIN_ADOPTION', current_source_writer=None,
                one_shot_consumed=True, future_execution_permitted=False, closed_at=now,
                actual_adoption_ref=result_ref)
        cp['work_in_progress']['c19_order_Main_adoption_closed_ref'] = result_ref
        cp['expected_previous_revision'] = cp['revision']
        cp['revision'] += 1
        ow['revision'] += 1
        for value in (cp, ow):
            value['updated_at'], value['updated_by'] = now, ROOT
        return cp, ow
    def commit():
        return imported(*IMPORT_PINS[1], 'root_c19_adoption_close').update_pair(current[:2], transform, journal, 'close')
    committed, guard_ref = guarded([request_ref, request['scope_ref'], result_ref, *current[2:],
                                    pin(TARGET), *[pin(p) for p, d in IMPORT_PINS]],
                                   out / 'closure-source-guard.closed.json', commit)
    receipt = save(out / 'registration.closed.root.json', dict(committed=committed,
        source_guard_closed_ref=guard_ref, scope_consumed=True, future_execution_permitted=False,
        formal_acceptance=False))
    print(json.dumps(dict(registration_closed_ref=receipt, **committed), ensure_ascii=False))

if __name__ == '__main__':
    operation, input_path = sys.argv[1:]
    require(operation in ('register', 'adopt', 'close'), 'EXACT_ROOT_OPERATION')
    {'register': register, 'adopt': adopt, 'close': close_registration}[operation](Path(input_path))
