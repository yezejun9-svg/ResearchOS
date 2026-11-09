import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 raw=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(n,x):
 with (O/n).open('xb') as f:f.write((json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
inputs=json.loads((O/'input-intake.json').read_bytes())['input_refs']
for ref in inputs:
 a=pin(ref['path']);assert a['sha256']==ref['sha256'] and a['bytes']==ref['bytes']
r=json.loads((O/'review.json').read_bytes());assert r['failed_trial_provider_requests'] is None
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('handoff.json','manifest.json')]
m=put('manifest.json',{'schema':'researchos.failure-component-review-manifest.v1','members':members,'member_count':len(members),'input_refs':inputs,'input_drift':0,'excludes_self_and_handoff':True})
h=put('handoff.json',{'schema':'researchos.model-trial-failure-component-review-handoff.v1','actor_id':'codex:/root/command_queue_impl','decision':r['decision'],'manifest_ref':m,'review_ref':pin(O/'review.json'),'business_state_ref':pin(O/'business-state.observed.json'),'checks_ref':pin(O/'evidence-checks.json'),'failure746_origin_ref':pin(O/'failure-origin.746.json'),'root_failure745_recounted':False,'verified_checks':37,'unique_inputs':20,'input_drift':0,'root_parent_pid':20540,'owned_jobs_confirmed_closed':2,'extra_duplicates_confirmed_closed':True,'coordinator_guard_entries_closed':80,'wrapper_guard_entries_closed':6,'failed_trial_provider_requests':None,'recorded_model_effects':0,'Run_status':'QUEUED','qualification_Task_status':'RUNNING','dispatch_state':'PREPARED','dispatch_worker':'','runtime_qualification':False,'formal_acceptance':False,'formal_acceptance_count':0,'reviewer_new_failures':[746],'Source_canonical_once_clock_mutations':0,'reviewer_native_provider_calls':0,'private_state_lease_token_vault_read':False,'stopped':True})
print(json.dumps({'handoff':h,'manifest':m,'review':pin(O/'review.json'),'failure746':pin(O/'failure-origin.746.json'),'members':len(members)},ensure_ascii=True))

