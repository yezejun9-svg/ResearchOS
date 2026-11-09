from pathlib import Path
import json,hashlib,ast
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent;N=R/('execution/v2.4/receipts/W05/W05-99/integration_codex/desktop58-finite169-go3-r337-'+O.name)
def j(p):return json.loads(Path(p).read_bytes())
cp=j(R/'execution/v2.4/checkpoint.json');out=[]
def walk(x):
 if isinstance(x,dict):
  if set(x)=={'path','sha256','bytes'} and (x['sha256'].startswith('d753faf') or 'lease' in x['path'].lower()):out.append(x)
  else:
   for v in x.values():walk(v)
 elif isinstance(x,list):
  for v in x:walk(v)
walk(cp)
q=j(N/'root-construction.parameters.desktop58.json');s=j(N/'scope_registration.json');pipe=Path(q['metadata_pipeline_ref']['path']).read_text(encoding='utf-8');gate=Path(s['authorization_verifier_ref']['path']).read_text(encoding='utf-8')
print(json.dumps({'closure_refs_from_actual_cp':out,'rootalloc':j(N/'root-allocation.actual.json'),'pipeline_functions':[x.name for x in ast.parse(pipe).body if isinstance(x,ast.FunctionDef)],'gate_functions':[x.name for x in ast.parse(gate).body if isinstance(x,ast.FunctionDef)]},ensure_ascii=False))

