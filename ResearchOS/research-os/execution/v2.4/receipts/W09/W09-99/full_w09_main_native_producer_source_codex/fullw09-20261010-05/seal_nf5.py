import copy,hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;OLD=N.parent/'fullw09-20261010-04'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
choice=doc(N/'source.choice.json');contract=doc(N/'root-calling-contract.json');controls=doc(N/'delta-controls.json')
assert controls['passed']==21 and controls['failed']==0
closed=doc(N/'source-guard.closed.json');assert closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
for key,name in contract['source_file_bindings'].items():assert ref(N/name)==contract['bound_source_refs'][key]
for r in choice['common']['source21']:assert ref(Path(r['path']))==r
members=[ref(p) for p in sorted(N.iterdir(),key=lambda p:p.name.casefold()) if p.is_file() and p.name not in ('HDF.json','MF.json','postseal-tool-io.json')]
put(N/'MF.json',dict(schema='researchos.w09-four-selector-producer-source-manifest.v1',members=members))
h=copy.deepcopy(doc(OLD/'HDF.json'))
for field,name in {'manifest_ref':'MF.json','calling_contract_ref':'root-calling-contract.json','source_choice_ref':'source.choice.json',
 'runtime_ref':'full_w09_runtime.source.py','overrides_ref':'runtime-overrides.source.py','launcher_ref':'full_w09_launcher.source.py',
 'prepare_caller_ref':'prepare_full_w09.source.py','producer_caller_ref':'run_full_w09.source.py','compiler_blueprint_ref':'compiler-source-blueprint.json',
 'source_delta_ref':'source-delta.json','source_guard_ref':'source-guard.closed.json','finite_controls_ref':'delta-controls.json'}.items():h[field]=ref(N/name)
h.update(generation=choice['common']['generation'],selectors=choice['selectors'],source21=choice['common']['source21'],
 prior_source_hdf_ref=ref(OLD/'HDF.json'),prior_source_mf_ref=ref(OLD/'MF.json'),
 reused_prior_controls_ref=ref(OLD/'delta-controls.json'),old_NF4_controls_rerun=False,
 new_finite_controls=dict(passed=21,failed=0,physical_resource_observation=True,synthetic_path_clause_checks=True),
 original_diagnostics=[],resource_parent_ref=choice['common']['resource_parent_ref'],
 resource_owner_ref=choice['common']['resource_owner_ref'],resource_audit_ref=choice['common']['resource_audit_ref'],
 resource_only_is_execution_grant=False,exact_physical_C_parent='C:\\Users\\yqyyds\\.researchos\\w09-native-v5',
 root_only_scope_registration='New registrar Source register-20261010-02; source does not issue scopes.',
 next_gate='Independent non-author runtime/Source review; new Root generation four scopes, exact current4, fresh leases, actual provenance, and runtime physical resource reobservation before execution.')
put(N/'HDF.json',h)
print(json.dumps(dict(HDF=ref(N/'HDF.json'),MF=ref(N/'MF.json'),runtime=h['runtime_ref'],contract=h['calling_contract_ref'],members=len(members)),ensure_ascii=False))

