import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent
def pin(p):
 b=Path(p).read_bytes();return {'path':str(Path(p)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,obj):
 with (O/n).open('xb') as f:f.write((json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(O/n)
r=json.loads((O/'review.json').read_bytes());inputs=json.loads((O/'input-intake.json').read_bytes())['refs']
for ref in inputs:
 a=pin(ref['path']);assert a['sha256']==ref['sha256'] and a['bytes']==ref['bytes']
members=[pin(p) for p in sorted(O.iterdir()) if p.is_file() and p.name not in ('manifest.json','handoff.json')]
m=put('manifest.json',{'schema':'researchos.independent-component-review-manifest.v1','members':members,'member_count':len(members),'input_refs':inputs,'input_drift':0,'excludes_self_and_handoff':True})
h=put('handoff.json',{'schema':'researchos.staged-runtime-actual-component-review-handoff.v1','actor_id':'codex:/root/command_queue_impl','decision':r['decision'],'manifest_ref':m,'review_ref':pin(O/'review.json'),'evidence_checks_ref':pin(O/'evidence-checks.json'),'business_observations_ref':pin(O/'actual-business-observations.json'),'source_author':'codex:/root','verified_checks':56,'unique_input_count':54,'input_drift':0,'actual_owned_jobs':4,'all_owned_jobs_confirmed_closed':True,'source_guard_entries':17,'reviewer_SQL_mode':'mode=ro;query_only','private_host_state_credential_token_vault_read':False,'reviewer_native_provider_calls':0,'Main_canonical_writes':0,'new_tool_failures':0,'runtime_qualification':False,'formal_acceptance':False,'formal_acceptance_count':0,'execution_grant_issued':False,'stopped':True})
print(json.dumps({'handoff':h,'manifest':m,'review':pin(O/'review.json'),'members':len(members)},ensure_ascii=True))

