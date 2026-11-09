import ast,collections,difflib,hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;B=Path("D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/a04_formal_profile_source_binding_revision_codex/c97e11df194d431cb901934bf01e6c94")
h=json.loads((B/'handoff.json').read_bytes());src=Path(h['source_pins']['execution/v2.4/formal_profile_w05.py']['path']).read_text(encoding='utf-8');t=ast.parse(src)
constants={}
for n in t.body:
 if isinstance(n,ast.Assign):
  for target in n.targets:
   if isinstance(target,ast.Name):
    try: constants[target.id]=ast.literal_eval(n.value)
    except (ValueError,TypeError):pass
schemas=constants['PUBLIC_SCHEMAS']; raw={g:json.loads((B/('public.'+g+'.schema.original.json')).read_bytes()) for g in schemas}
keywords=collections.Counter();annotations=[]
def visit(node,path):
 if not isinstance(node,dict):return
 for k,v in node.items():
  keywords[k]+=1
  if k in ['readOnly','writeOnly','deprecated','default','examples']:annotations.append({'path':path+'/'+k,'value':v})
  if k=='properties':
   for prop,sub in v.items():visit(sub,path+'/properties/'+prop)
  elif isinstance(v,dict):visit(v,path+'/'+k)
  elif isinstance(v,list):
   for i,sub in enumerate(v):
    if isinstance(sub,dict):visit(sub,path+'/'+k+'/'+str(i))
for g,defs in schemas.items():
 for n in defs:visit(raw[g]['$defs'][n],g+':'+n)
print('DEFINITION_NAMES '+json.dumps({k:list(v) for k,v in schemas.items()}))
print('KEYWORDS '+json.dumps(dict(keywords)));print('REMOVED_NON_DESCRIPTION_ANNOTATIONS '+json.dumps(annotations,ensure_ascii=False))
for g,n in [('domain','Task'),('persistence','Task'),('domain','Run'),('domain','Artifact'),('client','SessionEvent')]:
 print('\nRAW_SCHEMA '+g+':'+n);print(json.dumps(raw[g]['$defs'][n],ensure_ascii=False,indent=2))
print('\nROOT_CONSTANTS '+json.dumps({k:v for k,v in constants.items() if k!='PUBLIC_SCHEMAS'},ensure_ascii=False))
for name in ['verify_live_originals','verify_capture_bundle','_integer','_native_exit','_nonempty']:
 n=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name)
 print('\nFUNC '+name);print(ast.get_source_segment(src,n))
for name in ['source-controls.actual.json','source-controls.actual.v2.json','source.inverse.actual.json','original-tool-io.json']:
 d=json.loads((B/name).read_bytes());print('\nDOC_SHAPE '+name+' '+json.dumps(list(d) if isinstance(d,dict) else {'type':'list','count':len(d),'first_keys':list(d[0]) if d else None}))
 if name.startswith('source-controls'):print(json.dumps(d,ensure_ascii=False))

