"""Seal Source only; no Root scope, TP, Main, Canon, or Native execution."""
import hashlib,json
from pathlib import Path
N=Path(__file__).resolve().parent;W=N.parent.parent
NF=W/'full_w09_main_native_producer_source_codex/fullw09-20261010-04'
OLD=W/'w09_profile_nf3_root_adoption_source_codex/adopt-20261010-02'
RESOURCE=W/'full_w09_current_resource_readonly_codex/new-current-resource-readonly-20261010-01'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):
 with p.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
controls=doc(N/'delta-controls.json');assert controls['passed']==36 and controls['failed']==0
guards=[]
for name in ('source-guard.closed.json','source-guard-corrected.closed.json','source-guard-corrected-v2.closed.json'):
 obj=doc(N/name);assert obj['closed'] and not obj['errors'] and obj['retained_handles_count']==0
 guards.append(ref(N/name))
contract=doc(N/'root-calling-contract.source.json');assert contract['input_pins_ref']==ref(N/'input-pins.json')
for k,name in (('caller_ref','register_w09_adoption.source.py'),('core_ref','adoption_core.source.py')):
 assert contract['source_bindings'][k]==ref(N/name)
assert ref(RESOURCE/'HDF.json')['sha256']=='39002754b0cadffac4741a56a38f95d53ff88f8bac03dd39d38c47828bf6d1b4'
assert ref(RESOURCE/'MF.json')['sha256']=='ef1c2cfbceeadfc2d5fd43c68d506a5f05ee0617246da5f29c53fdf41432a752'
assert ref(RESOURCE/'resource-report.json')['sha256']=='f5f274d449c6ba68d6de66cdb300eea5225caf105273d2ecc0a33f92623de81a'
members=[ref(p) for p in sorted(N.iterdir(),key=lambda p:p.name.casefold()) if p.is_file() and p.name not in ('MF.json','HDF.json','postseal-tool-io.json')]
put(N/'MF.json',dict(schema='researchos.w09-nf4-registration-source-manifest.v1',members=members))
h=dict(schema='researchos.w09-nf4-registration-source-handoff.v1',actor_id='codex:/root/attach_restore_independent_review',
 source_thread_id='01a11e0c-eef6-7363-a5b1-da61d6ae7f4c',status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',
 manifest_ref=ref(N/'MF.json'),caller_ref=ref(N/'register_w09_adoption.source.py'),core_ref=ref(N/'adoption_core.source.py'),
 contract_ref=ref(N/'root-calling-contract.source.json'),input_pins_ref=ref(N/'input-pins.json'),
 source_delta_ref=ref(N/'source-delta.json'),source_guard_refs=guards,
 finite_controls_ref=ref(N/'delta-controls.json'),new_finite_controls=dict(passed=36,failed=0,synthetic_Source_only=True),
 producer_source_hdf_ref=ref(NF/'HDF.json'),producer_source_mf_ref=ref(NF/'MF.json'),
 prior_source_hdf_ref=ref(OLD/'HDF.json'),prior_source_mf_ref=ref(OLD/'MF.json'),
 resource_hdf_ref=ref(RESOURCE/'HDF.json'),resource_mf_ref=ref(RESOURCE/'MF.json'),resource_report_ref=ref(RESOURCE/'resource-report.json'),
 original_diagnostics=doc(N/'original-diagnostics.json'),generation=contract['generation'],selectors=contract['selectors'],
 old_closed_scope_refs_preserved=True,shared_TP_gate_reused=True,complete_Source_and_Canon_byte_inverse=True,
 dynamic_current4=True,Main_profile_CM40_read_only=True,
 scratch_parent='Root separate physical C resource preparation required; no directory creation performed by Source.',
 formal_consumer_TEMP='Future true consumer/verify_owner/derive process must use the controlled shared C parent as actual TEMP/TMP; this Source does not call consumers.',
 old_controls_69_112_20_98_rerun=False,actual_executed=False,actual_TP_calls=0,actual_Go_runs=0,actual_Native_runs=0,
 actual_dispatcher_runs=0,actual_SQL_runs=0,actual_model_provider_calls=0,Main_written=False,Canon_written=False,
 current_CanonicalPair_held=False,formal_case_accepted_delta=0,formal_acceptance=False,parent_acceptance=False,
 execution_grant=False,future_Root_scope=None,future_Root_request=None,future_registration=None,
 next_gate='Independent non-author review of NF4 runtime and this registrar; Root actual resource preparation, current4, complete pending diagnostics, real audits, and fresh finite four-selector leases.')
put(N/'HDF.json',h)
print(json.dumps(dict(HDF=ref(N/'HDF.json'),MF=ref(N/'MF.json'),caller=h['caller_ref'],core=h['core_ref'],contract=h['contract_ref'],members=len(members)),ensure_ascii=False))

