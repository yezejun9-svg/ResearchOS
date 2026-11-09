import json,hashlib
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
qpath=R/'execution/v2.4/receipts/W05/W05-99/cli43_successful_execution_independent_review_codex/6f07498ca19a49c7866b9e528d401aa0/qualification.json'
q=json.loads(qpath.read_bytes());ins=json.loads((O/'inspection.json').read_bytes())
removed={r['path'].lower():r for r in ins['removed_runtime_rows'] if r['path'].lower().startswith('c:')}
hits=[];inputs=[]
def visit(v,pointer,case):
    if isinstance(v,dict):
        for k,x in v.items():
            if isinstance(x,str) and x.removeprefix('\\\\?\\').lower() in removed:
                hits.append({'case':case,'pointer':pointer+'/'+k,'actual_record':v,'omitted_ref':removed[x.removeprefix('\\\\?\\').lower()]})
            elif isinstance(x,(dict,list)):visit(x,pointer+'/'+k,case)
    elif isinstance(v,list):
        for i,x in enumerate(v):visit(x,pointer+'/'+str(i),case)
for c in q['case_facts']:
    r=c['invocation_ref'];p=Path(r['path']);b=p.read_bytes();actual={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};inputs.append(actual)
    if actual['sha256']!=r['sha256'] or actual['bytes']!=r['bytes']:raise RuntimeError('Pinned historical invocation changed')
    visit(json.loads(b),'',c['case_id'])
v={'historical_qualification_ref':{'path':str(qpath),'sha256':hashlib.sha256(qpath.read_bytes()).hexdigest(),'bytes':len(qpath.read_bytes())},'historical_invocation_refs':inputs,'missing_observed_records':hits,'not_new_runtime_observation':True}
with (O/'observed-resource-comparison.json').open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps({'hits':len(hits),'paths':sorted(set(x['omitted_ref']['path'] for x in hits)),'first':hits[:1]},ensure_ascii=False))
