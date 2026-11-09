import json,hashlib
from pathlib import Path
O=Path(__file__).parent
R=Path('D:/作品集/ResearchOS/research-os')
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def put(n,d):
 p=O/n
 with p.open('xb') as f:f.write((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
 return ref(p)
p=R/'execution/v2.4/receipts/W13/W13-03/desktop58_finite_executor_codex/72ff32d0d24a42c4a8effd849d54f882/build-current58.invocation.json'
events=json.loads(p.read_bytes())['result']['debug_capture']['events']
active={};seen=set();closed=[];issues=[]
for ordinal,e in enumerate(events):
 if e['code']==3:
  pid=e['pid']
  if pid in seen:issues.append(['duplicatePID',ordinal,pid])
  seen.add(pid);active[pid]=e['process_generation']
 elif e['code']==5:
  pid=e['pid']
  if pid not in active:issues.append(['orphanEXIT',ordinal,pid])
  else:closed.append({'pid':pid,'generation_from_create':active.pop(pid),'exit':e['actual_exit_event_code']})
checks={'unique_create_PIDs_802':len(seen)==802,'closed_802':len(closed)==802,'active_empty':not active,'no_orphans_or_reusedPID':not issues,'generation_sequence':sorted(x['generation_from_create'] for x in closed)==list(range(1,803))}
supp=put('audit.supplement.json',{'schema':'researchos.readonly-audit-supplement.v1','original_audit_ref':ref(O/'audit.json'),'invocation_ref':ref(p),'checks':checks,'all_passed':all(checks.values()),'closed_processes':closed,'correction':'EXIT records have no generation field. Unique PIDs and ordered CREATE/EXIT pairing establish correspondence; original false predicate retained. No native rerun.','new_failure_origins':[]})
rv=json.loads((O/'review.json').read_bytes());rv['decision']='FAILED_EXECUTION_EVIDENCE_CLOSED_QUALIFICATION_WITHHELD' if all(checks.values()) else 'REQUEST_CHANGES';rv['requested_changes']=[] if all(checks.values()) else [checks]
rv['reviewer']=rv['actor'];rv['audit_supplement_ref']=supp;rv['preserved_initial_review_ref']=ref(O/'review.json');rv['effective_checks']={'initial_total':6110,'initial_passed':6109,'superseded_incorrect_predicates':1,'supplemental_passed':sum(checks.values())}
r=put('review.final.json',rv)
h=put('handoff.final.json',{'schema':'researchos.independent-review-handoff.v1','review_ref':r,'audit_supplement_ref':supp,'decision':rv['decision'],'new_failure_origins':[],'new_failure_count':0,'status':'STOPPED','source_acceptance':False,'formal_increment':0})
entries=[ref(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='manifest.final.json']
m=put('manifest.final.json',{'schema':'researchos.public-review-manifest.v1','entries':entries,'count':len(entries),'self_excluded':True,'mutable_after_seal':False})
print(json.dumps({'review':r,'handoff':h,'manifest':m,'checks':checks},ensure_ascii=False))

