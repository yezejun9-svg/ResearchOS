"""Last static pin/metadata pass, no candidate import or execution."""
import ast,hashlib,json,pathlib,difflib
P=pathlib.Path(__file__).resolve().parent
def get(n):return (P/n).read_text(encoding='utf-8')
def put(n,v):
 with (P/n).open('xb') as f:f.write(v.encode() if isinstance(v,str) else v)
def save(n,v):put(n,json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
old=get('controller_common.v2.final.py');new=old.replace("  if bypath.get(pin['path'].casefold())!=pin:raise Stop('Required registration object not sealed')", "  bound=bypath.get(pin['path'].casefold())\n  if bound is None or any(bound[k]!=pin[k] for k in ['path','sha256','bytes']):raise Stop('Required registration object not sealed')")
oldwrite="p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);no_alias(p,False)"
new=new.replace(oldwrite,"p=Path(path);make_owned_parents(p.parent);no_alias(p,False)")
insert='''def make_owned_parents(parent):
 parent=Path(parent)
 if not parent.is_absolute() or '..' in parent.parts:raise Stop('Absolute bounded receipt parent required')
 missing=[];current=parent
 while not current.exists():
  missing.append(current);current=current.parent
 no_alias(current)
 for directory in reversed(missing):
  no_alias(directory.parent);directory.mkdir(exist_ok=False);no_alias(directory)

'''
new=new.replace('def write_json(path,obj):',insert+'def write_json(path,obj):')
put('controller_common.v2.sealed.py',new);cp=ref(P/'controller_common.v2.sealed.py')
selected=['controller_common.v2.sealed.py']
for name in ['controller','launch','case_worker','seal_readonly']:
 text=get(name+'.v2.final.py').replace("/'controller_common.v2.final.py'","/'controller_common.v2.sealed.py'").replace(ref(P/'controller_common.v2.final.py')['sha256'],cp['sha256'])
 n=name+'.v2.sealed.py';put(n,text);selected.append(n)
selected+=['windows_debug_job_tree.py','windows_owned_process.py']
s=json.loads((P/'spec.v2.final.json').read_bytes());s['preparation_revision']='v2-sealed-PREPARATION_ONLY';s['controller_refs']=[ref(P/n) for n in selected]
for key,name in [('controller_ref','controller'),('launcher_ref','launch'),('case_worker_ref','case_worker'),('sealer_ref','seal_readonly')]:s[key]=ref(P/(name+'.v2.sealed.py'))
save('spec.v2.sealed.json',s)
for stem in ['root-scope.UNREGISTERED','root-grant.UNAUTHORIZED']:
 doc=json.loads((P/(stem+'.v2.final.template.json')).read_bytes());doc['spec_ref']=ref(P/'spec.v2.sealed.json');doc['controller_refs']=s['controller_refs'];save(stem+'.v2.sealed.template.json',doc)
rows=[]
for n in selected:
 tree=ast.parse(get(n),filename=str(P/n));rows.append({'ref':ref(P/n),'AST_PARSE':'PASS','imported':False,'executed':False})
save('ast-audit.sealed.json',{'schema':'researchos.w09.static-ast-only.v2','files':rows,'actual_AST_modules':len(rows),'actual_candidate_or_helper_imports':0,'actual_native_product_calls':0})
put('common-last-static-guards.diff',''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='controller_common.v2.final.py',tofile='controller_common.v2.sealed.py')))
print(json.dumps({'spec':ref(P/'spec.v2.sealed.json'),'selected':s['controller_refs'],'authorized':False},ensure_ascii=False))
