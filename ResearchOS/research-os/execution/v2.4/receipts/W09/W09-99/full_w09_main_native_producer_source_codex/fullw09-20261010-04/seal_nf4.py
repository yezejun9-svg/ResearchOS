import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent
OLD=N.parent/'fullw09-20261010-03'
W=N.parent.parent
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
controls=doc(N/'delta-controls.json');guard=doc(N/'source-guard.closed.json')
assert controls['passed']==35 and controls['failed']==0 and guard['closed'] and not guard['errors'] and guard['retained_handles_count']==0
contract=doc(N/'root-calling-contract.json');choice=doc(N/'source.choice.json')
for k,name in contract['source_file_bindings'].items():assert ref(N/name)==contract['bound_source_refs'][k]
assert choice['common']['compiler_blueprint_ref']==ref(N/'compiler-source-blueprint.json')
for x in choice['common']['source21']:assert ref(Path(x['path']))==x
resource=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01/resource-survey.json'
assert ref(resource)['sha256']=='83aad04144c52d79bab636a30164074f35b9bce3d7237367d282f4e1e1cc6484'
members=[ref(p) for p in sorted(N.iterdir(),key=lambda p:p.name.casefold()) if p.is_file() and p.name not in ('MF.json','HDF.json','postseal-tool-io.json')]
put(N/'MF.json',dict(schema='researchos.w09-four-selector-producer-source-manifest.v1',members=members))
h=dict(schema='researchos.w09-four-selector-producer-source-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 source_thread_id='01a11e0c-eef6-7363-a5b1-da61d6ae7f4c',status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',
 manifest_ref=ref(N/'MF.json'),calling_contract_ref=ref(N/'root-calling-contract.json'),
 source_choice_ref=ref(N/'source.choice.json'),runtime_ref=ref(N/'full_w09_runtime.source.py'),
 overrides_ref=ref(N/'runtime-overrides.source.py'),launcher_ref=ref(N/'full_w09_launcher.source.py'),
 prepare_caller_ref=ref(N/'prepare_full_w09.source.py'),producer_caller_ref=ref(N/'run_full_w09.source.py'),
 compiler_blueprint_ref=ref(N/'compiler-source-blueprint.json'),source_delta_ref=ref(N/'source-delta.json'),
 source_guard_ref=ref(N/'source-guard.closed.json'),finite_controls_ref=ref(N/'delta-controls.json'),
 new_finite_controls=dict(passed=35,failed=0,synthetic_Source_only=True),
 prior_source_hdf_ref=ref(OLD/'HDF.json'),prior_source_mf_ref=ref(OLD/'MF.json'),
 resource_survey_ref=ref(resource),generation=choice['common']['generation'],source21=choice['common']['source21'],
 selectors=choice['selectors'],original_diagnostics=doc(N/'original-diagnostics.json'),
 old_controls_69_112_20_98_rerun=False,actual_executed=False,actual_Go_runs=0,actual_Native_runs=0,
 actual_dispatcher_runs=0,actual_SQL_runs=0,actual_model_provider_calls=0,Main_written=False,Canon_written=False,
 current_CanonicalPair_held=False,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,
 execution_grant=False,future_Root_scope=None,future_Root_request=None,future_registration=None,future_ModeProof=None,
 next_gate='Independent non-author Source review; Root separately prepares physical fixed C scratch parent; fresh generation four scopes and real current4 request/lease before execution.',
 root_only_scope_registration='Prepared separately in w09_nf4_root_registration_source_codex/register-20261010-01; Source does not issue scopes.')
put(N/'HDF.json',h)
print(json.dumps(dict(HDF=ref(N/'HDF.json'),MF=ref(N/'MF.json'),runtime=h['runtime_ref'],contract=h['calling_contract_ref'],members=len(members)),ensure_ascii=False))

