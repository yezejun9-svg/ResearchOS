from pathlib import Path
import json,hashlib,ast
R=Path('D:/作品集/ResearchOS/research-os');O=Path(__file__).parent
Q=R/'execution/v2.4/receipts/W05/W05-99/cli58_successful_execution_independent_review_codex/83c89c410a1744b8b77d121fd44e5c5e/qualification.json'
def read(p):return json.loads(Path(p).read_bytes())
def pin(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
q=read(Q);e=q['evidence_refs'];result=read(e['result_ref']['path']);root=read(e['root_completion_ref']['path']);req=read(root['closure_request_ref']['path']);case_details=[]
for fact in q['case_facts']:
 inv=read(fact['invocation_ref']['path']);verified=read(fact['verified_ref']['path']);case_details.append({'fact':fact,'invocation':inv,'verified_shape':{k:({'keys':list(v)} if isinstance(v,dict) else {'length':len(v)} if isinstance(v,list) else v) for k,v in verified.items()}})
g=R/'execution/v2.4/receipts/W13/W13-03/desktop58_cli_root_closure_adapter_revision_preparation_codex/156343f1960f409cbfb1b13af160735f/authorization_adapter.v3.cli_root.proposed.py';tree=ast.parse(g.read_bytes());functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['validate_cli2','sealed_cli_root_closure','sealed_manifest','member']]
deref=[]
for f in functions:
 for n in ast.walk(f):
  if isinstance(n,ast.Subscript):deref.append({'function':f.name,'line':n.lineno,'expression':ast.unparse(n)})
out={'qualification_ref':pin(Q),'qualification_keys':list(q),'evidence_refs':e,'case_details':case_details,'result':result,'root_completion_keys':list(root),'root_request_keys':list(req),'gate_ref':pin(g),'gate_dereferences':deref}
with (O/'inspection.json').open('xb') as f:f.write((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
print(json.dumps({'qualification_keys':list(q),'case_details':case_details,'result':result,'root_completion_keys':list(root),'gate_dereference_count':len(deref)},ensure_ascii=False))
