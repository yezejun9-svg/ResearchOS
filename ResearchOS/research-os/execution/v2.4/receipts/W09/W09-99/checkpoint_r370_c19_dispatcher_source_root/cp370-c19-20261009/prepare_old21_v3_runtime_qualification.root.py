"""Observe old21 runtime resources and issue a resource-review-only scope."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import ast, hashlib, json, os, sys, types

R = Path(r'D:\作品集\ResearchOS\research-os')
N = Path(__file__).resolve().parent
B = R / 'execution/v2.4/receipts/W05/W05-99'
M = B / 'schema21_root_caller_registration_source_codex/s21root-20261010-03'
THREAD = '01a11007-5233-7ca1-b71f-9e9e5ce84c98'
tree = ast.parse((N / 'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x, ast.FunctionDef)
    and x.name in {'pin', 'save', 'exact'}], type_ignores=[]),
    'Root_pin_helpers_only', 'exec'), globals())
hdf = exact(M / 'HDF.json', '37d0152dd58020f7c1be76d1a66b6fa2363de8782668998ad89080c84257a45b', 12041)
mf = exact(M / 'MF.json', 'e91b682efa8220d95ec9c54a4e6348a6f1a5736e133bb662475836384a46e176', 11639)
caller_ref = exact(M / 'old21_root.source.py', 'b538b9b543ac0d45140834d52b0a209dc47546ac7c007ec9aaeda9e8602a1b06', 65191)
calling_ref = exact(M / 'root-calling-contract.source.json', '98982899cea28ab19521b2e260c9df06e37f91bcc30579eb1daf6c9009915279', 38413)
calling = json.loads(Path(calling_ref['path']).read_bytes())
builder_contract_ref = calling['builder_contract_ref']
exact(Path(builder_contract_ref['path']), builder_contract_ref['sha256'], builder_contract_ref['bytes'])
contract = json.loads(Path(builder_contract_ref['path']).read_bytes())

def load(ref, name):
    exact(Path(ref['path']), ref['sha256'], ref['bytes'])
    module = types.ModuleType(name)
    module.__file__ = ref['path']
    sys.modules[name] = module
    exec(compile(Path(ref['path']).read_bytes(), module.__file__, 'exec'), module.__dict__)
    return module

caller = load(caller_ref, 'root_old21_resource_probe_caller')
guard = load(caller.GUARD_REF, 'root_old21_resource_probe_guard')
load(caller.TP_REF, 'root_old21_resource_probe_tp')
job = load(contract['owned_job_ref'], 'root_old21_resource_probe_owned')
load(contract['builder_ref'], 'root_old21_resource_probe_builder')
load(contract['base_helper_ref'], 'root_old21_resource_probe_leaf_base')
paths = list(job.runtime_resource_paths())
for module in tuple(sys.modules.values()):
    for key in ('__file__', '__cached__'):
        value = getattr(module, key, None)
        if value and Path(value).is_file():
            paths.append(value)
paths += [sys.executable, contract['go_ref']['path'], caller_ref['path'],
    caller.GUARD_REF['path'], caller.TP_REF['path'], contract['owned_job_ref']['path'],
    contract['builder_ref']['path'], contract['base_helper_ref']['path'],
    calling_ref['path'], builder_contract_ref['path'], contract['input_manifest_ref']['path']]
resources_by_path = {}
for path in paths:
    ref = pin(Path(path))
    key = caller.canonical(ref['path'])
    assert key not in resources_by_path or resources_by_path[key] == ref
    resources_by_path[key] = ref
resources = [resources_by_path[key] for key in sorted(resources_by_path)]
held = guard.SourceReadGuard(per_file_cap=512 * 1024 * 1024, total_cap=1024 * 1024 * 1024)
try:
    held.acquire(resources)
    assert all(pin(Path(ref['path'])) == ref for ref in resources)
finally:
    cleanup = held.close()
assert cleanup['closed'] and cleanup['retained_handles_count'] == 0 and not cleanup['errors']
guard_ref = save('old21.v3.runtime-resource-probe.guard.closed.root.json', cleanup)
now = datetime.now(timezone.utc)
scope_ref = save('old21.v3.runtime-qualification.scope.actual.root.json', dict(
    schema='researchos.root-old21-runtime-qualification-scope.v2', issued_by='codex:/root',
    root_thread_id=THREAD, slice_id='OLD21_RUNTIME_RESOURCE_QUALIFICATION',
    formal_acceptance=False, execution_grant=False, source_hdf_ref=hdf, source_mf_ref=mf,
    caller_ref=caller_ref, builder_contract_ref=builder_contract_ref,
    created_utc=now.isoformat(), lease_expires_at=(now + timedelta(hours=24)).isoformat()))
manifest_ref = save('old21.v3.runtime-manifest.actual.root.json', dict(
    schema='researchos.root-old21-runtime-manifest.v1', issued_by='codex:/root', root_thread_id=THREAD,
    source_author=calling['source_author'], builder_source_author=calling['builder_source_author'],
    resource_refs=resources, source_hdf_ref=hdf, source_mf_ref=mf, caller_ref=caller_ref,
    builder_contract_ref=builder_contract_ref, qualification_scope_ref=scope_ref,
    formal_acceptance=False, execution_grant=False, python_ref=pin(Path(sys.executable)),
    go_ref=contract['go_ref'], probe_guard_ref=guard_ref,
    actual_Go_Native_SQL_model_TP_calls=0, Canonical_written=False))
print(json.dumps(dict(scope_ref=scope_ref, runtime_manifest_ref=manifest_ref, resource_count=len(resources),
    probe_guard_ref=guard_ref, execution_grant=False, programme_qualification=False,
    Canon_written=False), ensure_ascii=False), flush=True)
