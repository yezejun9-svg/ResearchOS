"""Issue a resource-review-only Scope and enumerate real local runtime inputs.

No programme execution, registration, qualification or acceptance is performed.
"""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import ast,hashlib,json,os,sys,types
R=Path(r'D:\作品集\ResearchOS\research-os');N=Path(__file__).resolve().parent
B=R/'execution/v2.4/receipts/W05/W05-99'
M=B/'fresh_main23_root_caller_registration_source_codex/main23root-20261009-03'
THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
t=ast.parse((N/'seal_continuation.live1013.root.py').read_bytes())
exec(compile(ast.Module(body=[v for v in t.body if isinstance(v,ast.FunctionDef) and v.name in ('pin','save','exact')],type_ignores=[]),'prior_root_helpers_only','exec'),globals())
hdfref=exact(M/'HDF.json','6ea62e31e8a8b50ac1685bee9e19b639e7df1417a1a18421fc755a0bd4b0525b',13200)
mfref=exact(M/'MF.json','6ede7ac360b4f71f086872a8e1ee2e7097187dd16dd6618ddc17c8ea0d296872',9259)
callerref=exact(M/'main23_root.source.py','c72ba84cde5cbbc6cc55cd25322d2faa49b34981f5fd88ce7b746275d2af336b',56282)
contractref=exact(M/'root-calling-contract.source.json','469dac4375965d83dafea44c59e2e37cf8c7dd65e81a532f29bb099f706a87a5',18436)
calling=json.loads(Path(contractref['path']).read_bytes());buildercontractref=calling['builder_contract_ref']
assert pin(Path(buildercontractref['path']))['sha256']==buildercontractref['sha256']
contract=json.loads(Path(buildercontractref['path']).read_bytes())
def load(ref,name):
    assert pin(Path(ref['path']))['sha256']==ref['sha256'] and Path(ref['path']).stat().st_size==ref['bytes']
    m=types.ModuleType(name);m.__file__=ref['path'];sys.modules[name]=m
    exec(compile(Path(ref['path']).read_bytes(),m.__file__,'exec'),m.__dict__)
    return m
caller=load(callerref,'root_main23_resource_probe_caller')
guard=load(caller.GUARD_REF,'root_main23_resource_probe_guard')
tp=load(caller.TP_REF,'root_main23_resource_probe_tp')
job=load(contract['owned_job_ref'],'root_main23_resource_probe_owned')
builder=load(contract['builder_ref'],'root_main23_resource_probe_builder')
base=load(contract['base_helper_ref'],'root_main23_resource_probe_leaf_base')
resourcepaths=list(job.runtime_resource_paths())
for module in tuple(sys.modules.values()):
    for key in ('__file__','__cached__'):
        value=getattr(module,key,None)
        if value and Path(value).is_file():resourcepaths.append(value)
resourcepaths+=[sys.executable,contract['go_ref']['path'],callerref['path'],caller.GUARD_REF['path'],caller.TP_REF['path'],contract['owned_job_ref']['path'],contract['builder_ref']['path'],contract['base_helper_ref']['path']]
by_path={}
for p in resourcepaths:
    r=pin(Path(p));key=caller.canonical(r['path'])
    assert key not in by_path or by_path[key]==r
    by_path[key]=r
resources=[by_path[k] for k in sorted(by_path)]
held=guard.SourceReadGuard(per_file_cap=512*1024*1024,total_cap=1024*1024*1024)
cleanup=None
try:
    held.acquire(resources)
    assert all(pin(Path(ref['path']))==ref for ref in resources)
finally:
    cleanup=held.close()
assert cleanup['closed'] and cleanup['retained_handles_count']==0 and not cleanup['errors']
guardref=save('main23.v3.runtime-resource-probe.guard.closed.root.json',cleanup)
now=datetime.now(timezone.utc)
scope= dict(schema='researchos.root-main23-runtime-qualification-scope.v2',issued_by='codex:/root',root_thread_id=THREAD,
    slice_id='MAIN23_RUNTIME_RESOURCE_QUALIFICATION',formal_acceptance=False,execution_grant=False,
    source_hdf_ref=hdfref,source_mf_ref=mfref,caller_ref=callerref,builder_contract_ref=buildercontractref,
    created_utc=now.isoformat(),lease_expires_at=(now+timedelta(hours=24)).isoformat())
scoperef=save('main23.v3.runtime-qualification.scope.actual.root.json',scope)
manifestref=save('main23.v3.runtime-resources.proposed.root.json',dict(schema='researchos.root-main23-runtime-resources-proposed.v1',issued_by='codex:/root',root_thread_id=THREAD,qualification_scope_ref=scoperef,
    source_hdf_ref=hdfref,source_mf_ref=mfref,caller_ref=callerref,builder_contract_ref=buildercontractref,
    python_ref=pin(Path(sys.executable)),go_ref=contract['go_ref'],resource_refs=resources,probe_guard_ref=guardref,
    source_guard_closed=True,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_queries=0,
    actual_dispatcher_runs=0,actual_model_requests=0,Canonical_written=False,
    status='REAL_LOCAL_RESOURCE_OBSERVATION_PENDING_INDEPENDENT_REVIEW',qualification=None,formal_acceptance=False))
print(json.dumps(dict(schema='researchos.root-main23-resource-scope-issuance.v1',issued_by='codex:/root',root_thread_id=THREAD,
    scope_ref=scoperef,proposed_resources_ref=manifestref,source_hdf_ref=hdfref,source_mf_ref=mfref,caller_ref=callerref,
    builder_contract_ref=buildercontractref,resource_count=len(resources),probe_guard_ref=guardref,
    Source_resource_review_only=True,execution_grant=False,programme_qualification=False,Canon_written=False),ensure_ascii=False),flush=True)
