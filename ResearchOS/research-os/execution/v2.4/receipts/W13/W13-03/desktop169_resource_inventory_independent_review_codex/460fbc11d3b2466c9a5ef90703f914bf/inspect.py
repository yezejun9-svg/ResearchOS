from pathlib import Path
import json,hashlib,collections
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;P=R/'execution/v2.4/receipts/W13/W13-03';W=R/'.local/worktrees/codex-w1303-desktop-http-r311';REF=[]
def ref(p):
 b=p.read_bytes();r={'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};REF.append(r);return r
def doc(p):ref(p);return json.loads(p.read_bytes())
old=W/'execution/v2.4/receipts/W13/W13-03/desktop_http_exact15_executor_codex/revision-r317-a7f44ed9b4ae4225bd072adcf708e24b/final-audit-2d44db33d4874f8bb806b44137292e08/handoff.json';h=doc(old)
facts={}
for k in ['full_inputs_ref','module_ref','build_ref','archive_entries_ref']:
 p=W/h[k]['path'];v=doc(p);facts[k]={'ref':ref(p),'type':type(v).__name__,'len':len(v),'keys':list(v) if isinstance(v,dict) else None,'first':v[:1] if isinstance(v,list) else {x:v[x] for x in v if not isinstance(v[x],(list,dict))}}
s=doc(R/'execution/v2.4/receipts/W05/W05-99/integration_codex/cli58-fresh-held2-r334-v2-0e298790cd484ec9ba319a379e7e34ed/scope_registration.json')
for k in ['compiler_resources_ref','runtime_resources_ref']:
 r=s[k];p=Path(r['path']);p=p if p.is_absolute() else R/p;v=doc(p);facts[k]={'ref':ref(p),'keys':list(v),'scalar':{x:y for x,y in v.items() if not isinstance(y,(dict,list))},'files_count':len(v['files']),'first':v['files'][:1]}
facts['input_refs']=REF
with (O/'inspection.json').open('xb') as f:f.write((json.dumps(facts,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(facts,ensure_ascii=False))
