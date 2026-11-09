import sys
sys.dont_write_bytecode = True
import ast
import hashlib
import json
from pathlib import Path
import re
import uuid

assert sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
OLD = OUT.parent / 'fresh-handler38-source-integration-r321'
V2 = ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_preparation_codex/revision-v2-ed1a1dab301a40b293dd6a177980cfaf'

def ref(path, expected=None):
    p = Path(path)
    if not p.is_absolute():
        p = ROOT / p
    raw = p.read_bytes()
    item = {'path': str(p), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    assert expected is None or item['sha256'] == expected
    return item

def save(name, value):
    raw = (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
    with (OUT / name).open('xb') as stream:
        stream.write(raw)
    return ref(OUT / name)

def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after, 1)

def cut(text):
    updated, count = re.subn(r'(?<![A-Za-z0-9_])421(?![A-Za-z0-9_])', '422', text)
    assert count > 0
    assert set(re.findall(r'[0-9a-f]{64}', text)) == set(re.findall(r'[0-9a-f]{64}', updated))
    return updated

def script(name, text):
    ast.parse(text, filename=name)
    with (OUT / name).open('xb') as stream:
        stream.write(text.encode('utf-8'))
    return ref(OUT / name)

v2_handoff_ref = ref(V2 / 'handoff.json', '424f16f455f464ad899bb1d77de740d2fa6085ffe26aa1e41b15363ce6bb715b')
v2_manifest_ref = ref(V2 / 'manifest.json', 'd0f188833adec9b098f872c21134352f0ac4b67588b133472fe7d6abffecde7f')
mf = json.loads(Path(v2_manifest_ref['path']).read_bytes())
assert len(mf['entries']) == 20
for item in mf['entries']:
    assert ref(item['path'], item['sha256'])['bytes'] == item['bytes']
scope = json.loads(Path(ref(V2 / 'scope.v2.proposed.json', '5adcca6d046ba0ac173639fdd5055fc6f2eea0302bdc7c40f1ac4a38841c48df')['path']).read_bytes())
assert scope['expected_registration'] == [321, 149, 422]
assert scope['controller_ref'] == ref(V2 / 'integrate_exact38.v2.py', 'e2f98bded200afc15cf1afecbc73d0423dcc1ab0a16e5497ca4a1dd7e244d6ff')
operation = uuid.uuid4().hex
scope.update(status='ROOT_REGISTERED_EXACT38_INTEGRATION_ONCE', registration_checkpoint=321,
    registration_namespace=OUT.relative_to(ROOT).as_posix(), operation_uuid=operation,
    new_output_root=str(ROOT / 'execution/v2.4/receipts/W05/W05-99/main_exact38_integration_executor_codex' / operation),
    base_commit=scope['source_chain'][0], target_source_commit=scope['source_chain'][-1],
    max_source_FF_operations=1, source_paths_ref=scope['exact38_ref'],
    Go_compile=0, Go_test=0, SQL=0, HTTP=0, SDK_MODEL_external_paid=0,
    effective_only_after_actual_registration_seal_and_once_grant=True,
    maximum_owned_Git_invocations=56, query_timeout_seconds=60,
    fast_forward_timeout_seconds=180, owned_child_cleanup_wait_seconds=5,
    native_process_bounds='Fixed56 owned Git calls maximum, query60s/FF180s/cleanup5s. Root Python preflight/evidence IO remains outside native child bounds.',
    Main_integration_currently_authorized=False, preparation_manifest_ref=v2_manifest_ref,
    read_only_task_packet_handoff_ref=ref(ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/package-packet-and-zeroexit-lookups-r320/handoff.json', '1572419110be7501759a57a79c2496104d8d21b3c7293459b0368871d852e6ee'))
assert not Path(scope['new_output_root']).exists()
scope_ref = save('scope_registration.json', scope)
old_prepare = (OLD / 'prepare.py').read_text(encoding='utf-8')
prepared = cut(old_prepare)
prepared = once(prepared, "assert len(origins) == len({row['origin_key'] for row in origins}) == 4", "assert len(origins) == len({row['origin_key'] for row in origins}) == 5")
prepared = once(prepared, "chunk = original.get('tool_trace') or original['unique_original_invocation'].split('/')[-1]", "chunk = original.get('tool_trace') or original.get('tool_chunk') or original['unique_original_invocation'].split('/')[-1]")
prepared = once(prepared, "key = original.get('origin_key') or 'w05-root14-readonly-' + chunk", "key = original.get('origin_key') or ('w05-integration-static-map-audit-828f8b' if chunk == '828f8b' else 'w05-root14-readonly-' + chunk)")
prepared = once(prepared, "native = original.get('actual_python_auditor_exit') if chunk == '61f965' else None", "native = original.get('actual_python_auditor_exit') if chunk == '61f965' else original.get('actual_python_exit') if chunk == '828f8b' else None\n    assert 'actor' in original or chunk == '828f8b'")
prepared = once(prepared, "'actor': original['actor']", "'actor': original.get('actor', 'codex:/root/w05_merge_review')")
prepared = once(prepared, "assert len(prepared['origins']) == 4 and len(old_failures) == 417", "assert len(prepared['origins']) == 5 and len(old_failures) == 417")
prepared = once(prepared, "'new_actual_nonzero_origins': 4", "'new_actual_nonzero_origins': 5")
prepared = once(prepared, 'r321-four-readonly-diagnostics', 'r321-five-readonly-diagnostics')
prepared = once(prepared, 'All421 origins', 'All422 registered origins plus2pending aftercut')
prepared = once(prepared, "assert cp['failure_counters'][:417] == old_failures and len(cp['failure_counters']) == 422", "assert cp['failure_counters'][:417] == old_failures and len(cp['failure_counters']) == 422\nassert len(prepared['pending_origin_refs']) == 2\nfor item in prepared['pending_origin_refs']:\n    ref(item['path'], item['sha256'])\ncp['work_in_progress']['r321_cut_pending_actual_tool_origin_refs'] = prepared['pending_origin_refs']\ncp['work_in_progress']['observed_actual_tool_origin_lower_bound_after_r321_cut'] = 424")
prepared = once(prepared, "'verified_refs': [ref(path) for path in sorted(READS, key=str) if path not in CANON]", "'pending_origin_refs': pin_bundle['pending_origin_refs'],\n    'verified_refs': [ref(path) for path in sorted(READS, key=str) if path not in CANON]")
prep_ref = script('prepare.py', prepared)
old_grant = (OLD / 'grant-producer.py').read_text(encoding='utf-8')
grant = cut(old_grant)
grant = once(grant, 'b3412116292c8e30d7e29f546ac399ee9f25c4bf5f6f39c0bb62ed16142fa30b', scope_ref['sha256'])
grant_ref = script('grant-producer.py', grant)
audit = save('derivation-audit.json', {
    'state': 'FROZEN_V2_SCOPE_AND_UNEXECUTED_ROOT_METADATA_TEMPLATES_PENDING_INDEPENDENT_REVIEW',
    'original_prepare_ref': ref(OLD / 'prepare.py'), 'original_grant_producer_ref': ref(OLD / 'grant-producer.py'),
    'scope_ref': scope_ref, 'prepare_ref': prep_ref, 'grant_producer_ref': grant_ref,
    'controller_preparation_handoff_ref': v2_handoff_ref, 'controller_preparation_manifest_ref': v2_manifest_ref,
    'future_registration': [321, 149, 422], 'cut_count': 5, 'pending_after_cut': 2,
    'counter_reset': False, 'source_writes': 0, 'FF_executions': 0, 'formal_increment': 0})
print(json.dumps({'scope_ref': scope_ref, 'prepare_ref': prep_ref, 'grant_producer_ref': grant_ref, 'audit_ref': audit}, ensure_ascii=True))
