import json
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r335-1c4ea6999d4d4437a0202c4e81ce581b';O=Path(__file__).parent;q=json.loads((N/'root-construction.parameters.desktop58.json').read_bytes())
def load(r):
 p=Path(r['path']);return json.loads((p if p.is_absolute() else R/p).read_bytes())
v={'qkeys':list(q),'scalar':{k:x for k,x in q.items() if not isinstance(x,(list,dict))},'public_environment':q['public_environment'],'main_git':q['main_git'],'metadata_shape':type(json.loads((N/'metadata-code-refs.json').read_bytes())).__name__,'scope':load(q['scope_template_ref']),'code_source_refs':{k:q[k] for k in ['builder_source_ref','metadata_pipeline_ref']},'full_finite_input_shape':{'type':type(load(q['full_finite_inputs_ref'])).__name__,'len':len(load(q['full_finite_inputs_ref']))}}
with (O/'inspection.json').open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
print(json.dumps(v,ensure_ascii=False))
