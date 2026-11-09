import ast,json
from pathlib import Path
B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_binding_revision_codex/c97e11df194d431cb901934bf01e6c94")
h=json.loads((B/'handoff.json').read_bytes());src=Path(h['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8');t=ast.parse(src)
for n in t.body:
 if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='PUBLIC_SCHEMAS' for x in n.targets):s=ast.literal_eval(n.value)
for g,n in [('domain','Id'),('domain','AcceptanceContract'),('domain','ProjectBinding'),('domain','StopPolicy'),('persistence','ProjectBinding'),('client','RunStateEventPayload'),('client','ToolResultEventPayload'),('client','UsageEventPayload'),('client','MessageEventPayload')]:print(g+':'+n+' '+json.dumps(s[g][n],ensure_ascii=False))
for n in t.body:
 if isinstance(n,ast.FunctionDef) and n.name in ['verify_live_originals','verify_capture_bundle','_integer','_native_exit','_nonempty']:print('\n'+ast.get_source_segment(src,n))
for name in ['source-controls.actual.json','source-controls.actual.v2.json']:
 d=json.loads((B/name).read_bytes());print(name+' '+json.dumps({'count':d['control_count'],'matched':d['matched_count'],'mismatches':[x for x in d['results'] if not x['matched']]}))
inv=json.loads((B/'source.inverse.actual.json').read_bytes());print('inverse '+json.dumps([{k:v for k,v in x.items() if k!='ndiff'} for x in inv['entries']],ensure_ascii=False))

