import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;OLD=N.parent/'register-20261010-01';W=N.parent.parent
NF=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-05'
RESOURCE=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
controls=doc(N/'delta-controls.json');closed=doc(N/'source-guard.closed.json')
assert controls['passed']==13 and controls['failed']==0 and closed['closed'] and not closed['errors'] and closed['retained_handles_count']==0
contract=doc(N/'root-calling-contract.source.json')
for k,name in {'caller_ref':'register_w09_adoption.source.py','core_ref':'adoption_core.source.py'}.items():assert contract['source_bindings'][k]==ref(N/name)
assert contract['input_pins_ref']==ref(N/'input-pins.json')
members=[ref(p) for p in sorted(N.iterdir(),key=lambda p:p.name.casefold()) if p.is_file() and p.name not in ('MF.json','HDF.json','postseal-tool-io.json')]
put(N/'MF.json',dict(schema='researchos.w09-nf4-registration-source-manifest.v1',members=members))
h=dict(schema='researchos.w09-nf4-registration-source-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 source_thread_id='01a11e0c-eef6-7363-a5b1-da61d6ae7f4c',status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',
 manifest_ref=ref(N/'MF.json'),caller_ref=ref(N/'register_w09_adoption.source.py'),core_ref=ref(N/'adoption_core.source.py'),
 contract_ref=ref(N/'root-calling-contract.source.json'),input_pins_ref=ref(N/'input-pins.json'),source_delta_ref=ref(N/'source-delta.json'),
 source_guard_ref=ref(N/'source-guard.closed.json'),finite_controls_ref=ref(N/'delta-controls.json'),
 new_finite_controls=dict(passed=13,failed=0,synthetic_Source_only=True),
 prior_successful_partial_source_refs=contract['prior_successful_partial_source_refs'],
 prior_successful_controls_ref=ref(OLD/'delta-controls.json'),prior_partial_has_HDF_or_MF=False,prior_controls_rerun=False,
 producer_source_hdf_ref=ref(NF/'HDF.json'),producer_source_mf_ref=ref(NF/'MF.json'),
 resource_hdf_ref=ref(RESOURCE/'HDF.json'),resource_mf_ref=ref(RESOURCE/'MF.json'),resource_report_ref=ref(RESOURCE/'resource-report.json'),
 resource_parent_ref=contract['resource_parent_ref'],resource_owner_ref=contract['resource_owner_ref'],resource_audit_ref=contract['resource_audit_ref'],
 generation=contract['generation'],selectors=contract['selectors'],old_closed_scope_refs_preserved=True,
 shared_TP_gate_reused=True,complete_Source_and_Canon_byte_inverse=True,dynamic_current4=True,
 Main_profile_CM40_read_only=True,actual_executed=False,actual_TP_calls=0,actual_Go_runs=0,actual_Native_runs=0,
 actual_dispatcher_runs=0,actual_SQL_runs=0,actual_model_provider_calls=0,Main_written=False,Canon_written=False,
 current_CanonicalPair_held=False,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,
 execution_grant=False,future_Root_scope=None,future_Root_request=None,future_registration=None,
 earlier_mechanical_diagnostics_refs=[ref(OLD/'original-diagnostics.json'),ref(NF.parent/'fullw09-20261010-04/original-diagnostics.json')],
 new_original_failures=[],
 formal_consumer_TEMP_TMP=contract['formal_consumer_actual_TEMP_TMP'],
 next_gate='Independent non-author Source/runtime review; Root real current4 request, complete pending counter suffix, actual audits, resource reobservation, four finite new-generation leases, and shared TP registration.',
 interface_schema_note=contract['interface_schema_note'])
put(N/'HDF.json',h)
print(json.dumps(dict(HDF=ref(N/'HDF.json'),MF=ref(N/'MF.json'),caller=h['caller_ref'],core=h['core_ref'],contract=h['contract_ref'],members=len(members)),ensure_ascii=False))

