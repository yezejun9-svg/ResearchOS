import datetime,json
from preserve_desktop_main_ecc28 import verify
from preserve_main_baseline import read,ref,R,N
cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json')
assert cp['revision']==556 and ow['revision']==342 and len(cp['failure_counters'])==2251
p=N/'continuation-cp556/RESUME.current.json';assert ref(p)['sha256']=='3e41af83383c094e221b744b208ce2a77146818c02b67b7deb3c27e4b503e42b'
r=read(p);assert r['head']=='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419'and r['active_source_cards']==[] and r['accepted_formal_cases']==0
preserved=verify();refs=[]
for x in [r['Desktop_Main_integration_adoption_ref'],r['Desktop_Main_preservation_gate_ref']]:
 from pathlib import Path
 a=ref(Path(x['path']));assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
value={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checkpoint':556,'ownership':342,'mixed_records':2251,'previous_goal_turn':'PROGRESS_CP554_TO_CP556','previous_actual_progress':['Seven-file Main fast-forward','Independent pre/post integration review','Preservation evidence and validated selector'],'preserved':preserved,'verified_current_refs':refs,'next_branch':'Audit actual CLI/Desktop delivery implementation and frozen contract before source scope','C57_admin_session':'USER_PREPARING_NOT_VERIFIED','formal_increment':0}
o=N/'CP556-live-continuation-verification.json'
with o.open('x',encoding='utf8')as s:json.dump(value,s,ensure_ascii=False,indent=2);s.write('\n')
print(json.dumps({'ref':ref(o),'Main':r['head'],'dirty_preserved':20,'verified_refs':len(preserved['verified_refs']),'prior_turn':'PROGRESS','formal':0},ensure_ascii=False))
