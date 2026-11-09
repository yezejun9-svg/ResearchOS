"""Independent bounded metadata/hash/AST reader; no candidate import or native child."""
import ast,hashlib,json,pathlib
P=pathlib.Path(__file__).resolve().parent
S=P.parents[1]/'desktop_exact15_integration_preparation_codex/f5ac31fcc8884b43ba7d25fc4fc75735'
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def read(n):return json.loads((S/n).read_bytes())
def save(n,v):
 with (P/n).open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
m=read('manifest.json');checked=[]
for r in m['entries']:
 p=pathlib.Path(r['path'])
 if not p.is_relative_to(S):raise RuntimeError('Source manifest escapes known preparation namespace')
 a=ref(p);checked.append({'expected':r,'actual':a,'match':a==r})
 if a!=r:raise RuntimeError('Immutable source preparation mismatch: '+str(p))
scope=read('scope.final.v2.proposed.json');exact=read('exact15.json');comp=read('composition-current.json');pro=read('protected-public-paths.planned.json')
save('input-audit.before.json',{'manifest_ref':ref(S/'manifest.json'),'actual_count':len(checked),'declared_count':m['count'],'mismatch_count':sum(not r['match'] for r in checked),'checks':checked})
snaps=[]
for name in ['integrate_desktop15.py','launch_desktop15.py','scope.final.v2.proposed.json','exact15.json','composition-current.json','implementation-conditions.json']:
 b=(S/name).read_bytes();q=P/('snapshot.'+name)
 with q.open('xb') as f:f.write(b)
 snaps.append({'original':ref(S/name),'snapshot':ref(q)})
asts={}
for name in ['integrate_desktop15.py','launch_desktop15.py']:
 body=(S/name).read_text(encoding='utf-8');tree=ast.parse(body,filename=str(S/name))
 asts[name]={'ref':ref(S/name),'AST_ONLY':True,'imported_or_executed':False,'functions':[{ 'name':n.name,'start':n.lineno,'end':n.end_lineno} for n in ast.walk(tree) if isinstance(n,ast.FunctionDef)]}
save('source-snapshots-and-AST.json',{'snapshots':snaps,'AST':asts,'product_or_helper_execution':False})
overview={'exact_type':type(exact).__name__,'exact_count':len(exact),'exact_first_row':exact[0] if isinstance(exact,list) and exact else None,'composition':comp,'protected_type':type(pro).__name__,'protected_count':len(pro),'protected_first_last':pro[:3]+pro[-3:] if isinstance(pro,list) else list(pro)[:5],'git_raw_paths':[r['path'] for r in m['entries'] if '/git/' in r['path'].replace(chr(92),'/') and ('tree' in r['path'] or 'patch' in r['path'])],'profile_guard_shape':type(read('profile-guards.current.json')).__name__,'inputs_shapes':{n:type(read(n)).__name__ for n in ['inputs.before.json','inputs.after.json']}}
save('bounded-overview.json',overview)
print(json.dumps({'manifest_count':len(checked),'mismatch':0,'exact_count':len(exact),'exact_first_row':overview['exact_first_row'],'protected_count':len(pro),'protected_type':overview['protected_type'],'git_raw_paths':overview['git_raw_paths'],'AST':asts},ensure_ascii=False))
