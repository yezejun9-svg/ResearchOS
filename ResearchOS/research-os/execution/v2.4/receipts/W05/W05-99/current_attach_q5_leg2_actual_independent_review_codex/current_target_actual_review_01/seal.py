import sys
sys.dont_write_bytecode=True
import json,hashlib,datetime
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 p=Path(p).resolve();r=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(r).hexdigest(),'bytes':len(r)}
def read(p):return json.loads(Path(p).read_bytes())
def save(n,obj):
 with (O/n).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
report=read(O/'report.json');sup=read(O/'supplement.report.json')
assert report['issue_count']==0 and sup['status']=='SUPPLEMENT_PASSED'
for n in ('source-guard.cleanup.actual.json','supplement.source-guard.cleanup.actual.json'):
 g=read(O/n);assert g['closed'] and not g['errors'] and g['retained_handles_count']==0
hdf={'schema':'researchos.independent-limited-actual-review.v1','reviewer':'current_target_actual_review','author_of_target':False,'status':'ACCEPTED_LIMITED_ACTUAL_PASSED_FAILED_ORIGINALS_AND_CLOSURE','created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'target_choice':pin(O/'originals/A9/source.integration.choice.json'),'target_closed':pin(O/'originals/A9/validation.closed.json'),'root_failure_origin':pin(O/'originals/A9/failure-origin.871.json'),'report':pin(O/'report.json'),'report_text':pin(O/'report.md'),'supplement':pin(O/'supplement.report.json'),'own_source_guard':pin(O/'source-guard.cleanup.actual.json'),'supplement_guard':pin(O/'supplement.source-guard.cleanup.actual.json'),'Root_actual_outer_exit':1,'Root_actual_python_exit':1,'Root_actual_native_exit':1,'target_suite_pass':False,'Source_count':58,'parent_count':54,'test_terminals':{'pass':152,'fail':5,'skip':0},'nested_children':6,'nested_test_terminals':{'pass':10,'fail':0,'skip':0},'native_child_pid_exit_individually_measured':False,'descendant_closure_source':'Root unnamed exclusive Job actual cleanup; no individual native child exit invented','formal_acceptance':False,'Main_adoption':False,'full_domain_accepted':False,'formal42_accepted':False,'parent22_accepted':False,'native_migration_accepted':False,'original_paid_business_accepted':False,'ordinary_historical20_upgrade':'BLOCKED','new_test_model_native_execution':False,'canonical_write':False,'Source_write':False,'new_failure_count':0,'role_model_policy':'Architecture/security/independent acceptance prefers gpt-6-astra high per project AGENTS; actual model identifier is not exposed to this agent and is not asserted.','postseal_exclusions':['MF.json','postseal.json','seal.original-tool-io.json']}
save('HDF.json',hdf)
exclude={'MF.json','postseal.json','seal.original-tool-io.json'}
members=[pin(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name not in exclude]
mf=save('MF.json',{'schema':'researchos.independent-evidence-manifest.v1','members':members,'excluded_seal_envelopes':sorted(exclude),'formal_acceptance':False})
for ref in members:assert pin(ref['path'])==ref
post=save('postseal.json',{'schema':'researchos.independent-evidence-postseal.v1','status':'PASS','manifest':mf,'handoff':pin(O/'HDF.json'),'verified_members':len(members),'all_exact_sha256_bytes':True,'no_product_acceptance':True,'excluded_self_and_tool_return':['postseal.json','seal.original-tool-io.json']})
print(json.dumps({'HDF':pin(O/'HDF.json'),'MF':mf,'postseal':post,'status':hdf['status']},ensure_ascii=False))
