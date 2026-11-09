import hashlib,json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-429e1734d9da4efba276680e78e2510b'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def doc(p):return json.loads(p.read_bytes())
def resolve(x):
 p=Path(x);return p if p.is_absolute() else R/p
def save(name,v):
 with (O/name).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
 return ref(O/name)
p=doc(N/'prepared_refs.json');a=doc(O/'audit.json');z=doc(O/'scope-ref-compatibility.json')
guards=[{'canonical_ref':r,'equal_original_copy':resolve(r['path']).read_bytes()==resolve(c['path']).read_bytes()} for r,c in zip(p['canonical_before'],a['copied_canonical_before_refs'])]
checks_ok=all(x['equal_original_copy'] for x in guards) and not z['failed']
request=[z['finding']]
if not checks_ok:request.append({'id':'R335-FINAL-SEAL-GUARD','severity':'BLOCKER','summary':'Supplement or final canonical snapshot guard failed; inspect recorded guards.'})
review={'schema':'researchos.root-registration-source-review.v1','reviewer':'codex:/root/w05_merge_review',
 'decision':'REQUEST_CHANGES','requested_changes':request,'actual_registration_executed':False,
 'expected_before':p['expected_before'],'expected_after':p['expected_after'],
 'register_sha256':ref(N/'register.py')['sha256'],'wrapper_sha256':ref(N/'run.py')['sha256'],
 'prepared_refs_sha256':ref(N/'prepared_refs.json')['sha256'],'audit_sha256':ref(N/'audit.json')['sha256'],
 'canonical_before':p['canonical_before'],'copied_canonical_before_refs':a['copied_canonical_before_refs'],
 'scope_ref':p['scope_ref'],'binding_ref':ref(N/'binding.json'),'sealer_ref':ref(N/'seal.py'),
 'draft_actual_prepare':{'reported_tool_initial':'06b98c','reported_session':88228,'reported_terminal':'b62d50','reported_outer_exit':0,'reported_python_exit':0,'status':'Actual prepare completed; this static incompatible-reference finding is not a failed prepare or product invocation.'},
 'audit_ref':ref(O/'audit.json'),'compatibility_supplement_ref':ref(O/'scope-ref-compatibility.json'),
 'tool_observations_ref':ref(O/'tool-observations.json'),'source_review_reused':a['scope_review_ref'],
 'check_summary':{'original_checks':len(a['checks']),'original_failed_predicates':a['failed'],'supplement_checks':len(z['checks']),'supplement_failed':z['failed'],'confirmed_blockers':1,'corrected_static_false_positives':1,'all_original_audit_bytes_preserved':True},
 'resource_reuse':{'verified_refs':a['resource_reuse']['verified_refs'],'exact_reused_fullscope_actualhash_refs':a['resource_reuse']['exact_reused_fullscope_actualhash_refs'],'new_metadata_refs_rehashed':len(a['resource_reuse']['extra_metadata_refs_rehashed']),'baseline_audit_ref':a['resource_reuse']['baseline_audit_ref'],'full_resource_tree_rehashed_this_registration_review':False},
 'actual_metadata_git_evidence':a['jobs'],'final_canonical_guards':guards,
 'failure_accounting':{'registered_before':532,'proposed_fixed_after':575,'fixed_origin_count':43,'historical_prefix_preserved':True,'later_pending_not_appended':True,'new_failure_count':0,'new_failure_origins':[],'static_finding_is_not_native_failure':True},
 'boundaries':{'candidate_import_or_execution':False,'registration_run_seal_grant_executed_by_reviewer':False,'native_Git_or_product_calls':0,'canonical_source_index_writes':0,'source_acceptance':False,'formal_increment':0,'runtime_observations_point_in_time_only':True,'Python_lifecycle_proof':False,'future_product_resources_and_execution_qualification':'OPEN'},
 'next_step':'Root new immutable allocation/input cycle only. Supply canonical ROOT-relative exact scope_ref from prepare onward and to grant. Preserve old prepared/desired/scope/cut/review bytes. Review new actual scope and CAS draft before Root run once; do not execute register independently before run.'}
rr=save('review.json',review)
hr=save('handoff.json',{'schema':'researchos.independent-review-handoff.v1','reviewer':review['reviewer'],'status':'STOPPED','decision':review['decision'],'review_ref':rr,'audit_ref':review['audit_ref'],'compatibility_supplement_ref':review['compatibility_supplement_ref'],'tool_observations_ref':review['tool_observations_ref'],'requested_change_ids':[x['id'] for x in request],'new_failure_count':0,'new_failure_origins':[],'actual_registration_executed':False,'source_acceptance':False,'formal_increment':0,'manifest_filename':'manifest.json'})
members=[ref(x) for x in sorted(O.iterdir()) if x.is_file() and x.name!='manifest.json']
mr=save('manifest.json',{'schema':'researchos.public-review-manifest.v1','entries':members,'count':len(members),'self_excluded':True})
print(json.dumps({'decision':review['decision'],'review_ref':rr,'manifest_ref':mr,'handoff_ref':hr,'supplement_ref':review['compatibility_supplement_ref'],'all_final_guards':checks_ok,'new_failure_count':0,'status':'STOPPED'},ensure_ascii=False))
