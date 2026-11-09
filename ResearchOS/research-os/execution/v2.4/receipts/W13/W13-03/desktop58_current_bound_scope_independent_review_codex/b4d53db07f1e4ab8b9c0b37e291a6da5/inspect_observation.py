from pathlib import Path
import json
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-'+O.name)
x=json.loads((N/'tool-observations.sixth-construction.closed.original.json').read_bytes())
def shape(v):
 if isinstance(v,dict):return {'keys':list(v),'scalars':{k:z for k,z in v.items() if not isinstance(z,(dict,list)) and len(str(z))<200}}
 return type(v).__name__
print(json.dumps({'keys':list(x),'topscalars':{k:v for k,v in x.items() if not isinstance(v,(dict,list))},'records':[shape(v) for v in x.get('records',[])]},ensure_ascii=False))
p=R/'execution/v2.4/receipts/W13/W13-03/desktop58_old_failed_lease_closure_cas_codex/5e2a75ea3da546b28b20975cc6a4d18f/manifest.closed.json'
m=json.loads(p.read_bytes());print(json.dumps({'closed_manifest_shape':shape(m),'first_row':next((v[:1] for v in m.values() if isinstance(v,list)),[])},ensure_ascii=False))

