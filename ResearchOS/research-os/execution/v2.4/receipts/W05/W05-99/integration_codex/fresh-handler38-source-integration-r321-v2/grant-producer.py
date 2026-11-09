"""Root metadata-only once grant; execute only after actual reviewed CP321 seal."""
import sys
sys.dont_write_bytecode = True
import hashlib
import json
import os
from pathlib import Path
import traceback

ROOT = Path.cwd().resolve()
REG = Path(__file__).resolve().parent
EXPECTED = [321, 149, 422]
CANON = ['execution/v2.4/' + n + '.json' for n in ['checkpoint', 'path_ownership', 'step_state', 'commands']]

def check(ok, message):
    if not ok:
        raise RuntimeError(message)

def safe(p, exists=True):
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    check('..' not in p.parts and p.is_relative_to(ROOT) and p != ROOT, 'Repository boundary')
    check(p.resolve(strict=exists) == p.absolute(), 'Path alias')
    for ancestor in [p] + list(p.parents):
        if os.path.lexists(ancestor):
            st = os.lstat(ancestor)
            check(not ancestor.is_symlink() and not getattr(st, 'st_file_attributes', 0) & 0x400, 'Reparse path')
    return p

def ref(p, expected=None):
    p = safe(p)
    raw = p.read_bytes()
    item = {'path': p.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    check(expected is None or item['sha256'] == expected, 'Hash mismatch')
    return item

def verify(item):
    actual = ref(item['path'], item['sha256'])
    check(actual['bytes'] == item['bytes'], 'Size mismatch')
    return safe(item['path']).read_bytes()

def save(directory, name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (directory / name).open('xb') as stream:
        stream.write(raw)
    return ref(directory / name)

check(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize, 'Python flags')
scope_ref = ref(REG / 'scope_registration.json', '254642660280442df4352e355d0e01f6c0fc8bab8bc7337554d6bbc26a223f90')
scope = json.loads(verify(scope_ref))
operation = scope['operation_uuid']
check(len(operation) == 32 and all(c in '0123456789abcdef' for c in operation), 'Operation UUID')
auth_parent = safe(ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_root_grant_codex', False)
auth_parent.mkdir(exist_ok=True)
auth = safe(auth_parent / operation, False)
auth.mkdir(exist_ok=False)
failure = None
try:
    lock_ref = ref(ROOT / 'execution/toolchains/locked.json', '0958d3f313e8d09d471521787a2b8b9480a17a91d6e4aa722393741dcbd8e663')
    tools = json.loads(verify(lock_ref))['tools']
    check(Path(sys.executable).resolve() == Path(tools['python']['path']).resolve(), 'Actual Python identity')
    check(hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == tools['python']['sha256'], 'Actual Python bytes')
    canonical = []
    docs = []
    for name in CANON:
        p = safe(name)
        raw = p.read_bytes()
        docs.append(json.loads(raw))
        target = auth / (p.stem + '.actual321.json')
        with target.open('xb') as stream:
            stream.write(raw)
        canonical.append({'canonical_path': name, 'ref': ref(target)})
    cp, ow = docs[:2]
    check([cp['revision'], ow['revision'], len(cp['failure_counters'])] == EXPECTED, 'Actual registration tuple')
    check(cp['head'] == scope['base_commit'] and cp['project_id'] == 'aede0678-7308-43dc-b9f2-cfe3d90cfdfb', 'Identity and base')
    prepared_ref = ref(REG / 'prepared_refs.json')
    prepared = json.loads(verify(prepared_ref))
    pins = prepared['pins']
    check(pins['scope'] == scope_ref, 'Actual scope ref')
    review_ref = pins['integration_controller_review']
    review = json.loads(verify(review_ref))
    check(review['schema'] == 'researchos.exact38-integration-controller-review.v1' and review['reviewer'] == 'codex:/root/w05_merge_review', 'Controller reviewer')
    check(review['decision'] == 'READY_FOR_ROOT_EXACT38_FAST_FORWARD_ONCE' and review['requested_changes'] == [] and review['actual_integration_executed'] is False, 'Controller review decision')
    check(review['controller_sha256'] == scope['controller_ref']['sha256'] and review['scope_sha256'] == scope_ref['sha256'], 'Exact reviewed controller/scope')
    check(cp['work_in_progress']['handler38_source_integration_scope_ref'] == scope_ref and cp['work_in_progress']['handler38_source_integration_controller_review_ref'] == review_ref, 'Canonical authority refs')
    registration = {key: ref(REG / filename) for key, filename in {
        'manifest': 'manifest.json', 'audit': 'registration-audit.json', 'invocation': 'invocation.json',
        'intent': 'canonical-write.intent.json', 'verified': 'canonical-write.verified.json'}.items()}
    manifest = json.loads(verify(registration['manifest']))
    check(manifest['count'] == len(manifest['entries']), 'Registration manifest count')
    listed = {}
    for item in manifest['entries']:
        p = safe(item['path'])
        check(p.is_relative_to(REG), 'Registration manifest boundary')
        verify(item)
        listed[p] = item
    for key in ['audit', 'invocation', 'intent', 'verified']:
        check(listed.get(safe(registration[key]['path'])) == registration[key], 'Unsealed registration evidence')
    audit, inv, intent, done = [json.loads(verify(registration[key])) for key in ['audit', 'invocation', 'intent', 'verified']]
    check(audit['actual_registration_exit'] == inv['actual_exit'] == 0 and audit['after'] == EXPECTED, 'Actual registration completion')
    check(audit['before'] == [320, 148, 417] and [done['checkpoint'], done['ownership'], done['failure_origins']] == EXPECTED, 'Registration transition')
    check(audit['invocation_ref'] == registration['invocation'] and audit['intent_ref'] == registration['intent'] and audit['verified_ref'] == registration['verified'], 'Actual closed refs')
    for item, copy in zip(intent['metadata'], canonical[:2]):
        check(verify(item['desired_ref']) == verify(copy['ref']), 'Canonical desired copy')
    for item, copy in zip(intent['unchanged'], canonical[2:]):
        check(item['sha256'] == copy['ref']['sha256'], 'Unchanged canonical copy')
    for item in canonical:
        check(safe(item['canonical_path']).read_bytes() == verify(item['ref']), 'Canonical changed during preflight')
    execution_parent = safe(ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_executor_codex', False)
    parent_existed = execution_parent.exists()
    execution_parent.mkdir(exist_ok=True)
    safe(execution_parent)
    execution_out = safe(scope['new_output_root'], False)
    check(execution_out.parent == execution_parent and execution_out.name == operation and not os.path.lexists(execution_out), 'Fresh exclusive execution leaf')
    parent_receipt = save(auth, 'execution-parent.preflight.json', {
        'fixed_parent': str(execution_parent), 'parent_existed': parent_existed,
        'parent_created_by_Root_if_absent': not parent_existed, 'ancestors_alias_reparse_rejected': True,
        'execution_leaf': str(execution_out), 'leaf_exists': False, 'source_writes': 0, 'product_executions': 0})
    grant = save(auth, 'grant.json', {
        'schema': 'researchos.exact38-source-integration-grant.v1', 'actor': 'codex:/root',
        'status': 'ROOT_REGISTERED_EXECUTION_AUTHORIZED', 'actual_registration_completed': True,
        'scope_ref': scope_ref, 'controller_review_ref': review_ref, 'source_chain': scope['source_chain'],
        'operation_uuid': operation, 'automatic_retry': False, 'canonical_copies': canonical,
        'registration_refs': registration, 'parent_preflight_ref': parent_receipt,
        'grant_producer_ref': ref(Path(__file__)), 'formal_increment': 0})
    print(json.dumps({'grant_ref': grant, 'parent_preflight_ref': parent_receipt}, ensure_ascii=True))
except BaseException as exc:
    failure = {'schema': 'researchos.root-grant-preflight-failure.v1', 'actor': 'codex:/root',
        'error': repr(exc), 'traceback': traceback.format_exc(), 'actual_native_product_exit': None,
        'source_writes': 0, 'FF_attempts': 0, 'automatic_retry': False, 'counter_reset': False}
    save(auth, 'failure.origin.json', failure)
    raise
finally:
    entries = [ref(p) for p in sorted(auth.iterdir()) if p.is_file()]
    save(auth, 'manifest.json', {'entries': entries, 'self_excluded': True,
        'preflight_complete': failure is None, 'product_executions': 0})
