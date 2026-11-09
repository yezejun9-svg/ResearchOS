import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');P=R/'execution/v2.4/receipts/W13/W13-03';D=P/'desktop58_failed_execution_root_closure_codex/4705959febf34a72a90e13e3ea2da9a4'
def read(p):return json.loads(p.read_bytes())
def path(r):
 p=Path(r['path']);return p if p.is_absolute() else R/p
r=read(D/'report.json');m=read(D/'manifest.json');t=read(path(r['failed_export_tree_ref']))
inv=next(x for x in r['all_closed_original_refs'] if x['path'].endswith('/build-current58.invocation.json'));i=read(path(inv));j=i['result'];d=j['debug_capture']
def shape(v):return {'type':type(v).__name__,'len':len(v) if hasattr(v,'__len__') else None,'keys':list(v) if isinstance(v,dict) else None}
out={'manifest':shape(m),'manifest_scalar':{k:v for k,v in m.items() if not isinstance(v,(dict,list))},'tree':shape(t),'tree_fields':{k:shape(v) for k,v in t.items()},'jobkeys':list(j),'debugkeys':list(d),'rejected':d['rejected_load_facts'],'firstevent':d['events'][0] if d['events'] else None,'firstmodule':d['modules'][0] if isinstance(d['modules'],list) and d['modules'] else None,'vector_shapes':[]}
for rr in r['all_closed_original_refs']:
 if rr['path'].endswith('initial.vector.json') or rr['path'].endswith('final.vector.json'):
  v=read(path(rr));out['vector_shapes'].append({'ref':rr,'shape':shape(v),'fields':{k:shape(a) for k,a in v.items()} if isinstance(v,dict) else None})
with (Path(__file__).parent/'actual-shapes.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(out,ensure_ascii=False))
