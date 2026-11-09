import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
def pin(path):
    raw=Path(path).read_bytes();return {'path':str(Path(path)),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def put(name,value):
    with (OUT/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())
    return pin(OUT/name)
intake=json.loads((OUT/'input-intake.json').read_bytes())
rechecked=[]
for record in intake['inputs']:
    actual=pin(record['ref']['path']);same=actual['sha256']==record['ref']['sha256'] and actual['bytes']==record['ref']['bytes']
    rechecked.append({'ref':record['ref'],'matches':same})
assert all(r['matches'] for r in rechecked)
put('final-input-recheck.json',{'inputs':rechecked,'unique_inputs':len(rechecked),'drift':0})
review=json.loads((OUT/'review.json').read_bytes())
assert review['decision']=='PASS_COMPONENT_EVIDENCE_WITH_GOAL_BLOCKED' and not review['failed_checks']
members=[pin(p) for p in sorted(OUT.rglob('*')) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
mf=put('manifest.json',{'schema':'researchos.independent-component-review-manifest.v1','actor_id':'codex:/root/command_queue_impl','members':members,'member_count':len(members),'input_refs':[r['ref'] for r in rechecked],'excludes_self_and_handoff_to_avoid_hash_cycle':True})
hdf=put('handoff.json',{'schema':'researchos.actual-cli-bootstrap-component-review-handoff.v1','actor_id':'codex:/root/command_queue_impl','decision':review['decision'],'manifest_ref':mf,'review_ref':pin(OUT/'review.json'),'report_ref':pin(OUT/'REVIEW.md'),'evidence_checks_ref':pin(OUT/'evidence-checks.json'),'original_tool_io_ref':pin(OUT/'original-review-tool-io.json'),'source_handoff_ref':review['source_handoff_ref'],'verified_checks':38,'input_count':40,'input_drift':0,'actual_init_accepted_as_component':True,'actual_GUI_binding_accepted_as_component':True,'all3jobs_cleanup_confirmed_from_original_records':True,'goal_native_exit':3,'goal_reason':'HOST_REJECTED:RESOURCE_BLOCKED','root_outer_exit':1,'root_python_exit':1,'failure719_recounted':False,'new_tool_failures':0,'bootstrap_accepted':False,'runtime_qualification':False,'formal_acceptance':False,'execution_grant_issued':False,'reviewer_native_GUI_SQL_provider_calls':0,'Main_canonical_writes':0,'stopped':True})
print(json.dumps({'handoff_ref':hdf,'manifest_ref':mf,'review_ref':pin(OUT/'review.json'),'members':len(members),'decision':review['decision'],'checks':38,'inputs':40,'drift':0,'new_failures':0}))
