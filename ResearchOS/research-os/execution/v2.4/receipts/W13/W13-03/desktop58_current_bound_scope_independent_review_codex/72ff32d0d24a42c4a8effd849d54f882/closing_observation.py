from pathlib import Path
import json,hashlib,re
O=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os');N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-'+O.name)
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
p=N/'tool-observations.fourth-full-scope.closed.original.json';d=json.loads(p.read_bytes());sref=dict(ref(N/'scope_registration.json'),path=(N/'scope_registration.json').relative_to(R).as_posix());C=[]
def ck(n,v):C.append({'check':n,'passed':bool(v)})
ck('actual Root saved scope_ref exactREL3key',d['actual_scope_ref']==sref and d['scope_ref_root_relative_from_first_creation'] is True)
ck('scope before execution full original actor/UID',d['actor']=='codex:/root' and d['run_uuid']==O.name and d['formal_increment']==0 and d['source_acceptance'] is False and d['candidate_execution'] is False and d['canonical_write'] is False)
rows=d['scope_build'];ck('scope original2streams',len(rows)==2 and rows[0]['result']['session_id']==45714 and rows[0]['result']['chunk_id']=='b0ae79' and rows[-1]['input']['session_id']==45714)
terminal=rows[-1]['result'];markers=re.findall(r'ACTUAL_[A-Z_]*EXIT[=:]\s*(-?\d+)',terminal['output'])
ck('actual40ea7c terminal0/Python0',terminal['chunk_id']=='40ea7c' and terminal['exit_code']==0 and markers==['0'] and d['scope_build_terminal_actual_outer_python_exit']==[0,0])
ck('all toolreturned statuses present arezero',all(x['result'].get('exit_code') in (None,0) for x in rows))
out={'schema':'researchos.desktop58-bound-scope-actual-observation-review.v1','checks':C,'failed':[x for x in C if not x['passed']],'scope_ref':sref,'actual_tool_observation_ref':ref(p),'scope_build_actual_results':[x['result'] for x in rows],'source_ref_protocol':'Actual Root saved exact scope_ref is ROOT-relative; future prepare/grant must keep identical dictionary. No actual registration/grant implied.','new_failure_count':0}
with (O/'closed-observation.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'checks':len(C),'failed':out['failed'],'observation_ref':ref(p),'report_ref':ref(O/'closed-observation.json')},ensure_ascii=False))
