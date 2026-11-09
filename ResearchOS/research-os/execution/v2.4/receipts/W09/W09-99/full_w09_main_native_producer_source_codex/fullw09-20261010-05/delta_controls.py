"""Only NF5 physical-C/resource/generation deltas; NF4 controls are not rerun."""
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent;OLD=N.parent/'fullw09-20261010-04'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def module(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
m=module(N/'full_w09_runtime.source.py');choice=doc(N/'source.choice.json');old=doc(OLD/'source.choice.json')
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
c=m.choice('C19');refs=m.validate_scratch_parent(c)
check('actual-Root-resource-and-physical-C-owner-verified',len(refs)==4)
check('resource-parent-not-execution-grant',doc(Path(c['resource_parent_ref']['path']))['execution_grant'] is False)
trees={name:ast.parse((N/name).read_bytes()) for name in ('full_w09_runtime.source.py','runtime-overrides.source.py')}
for name in ('validate_scratch_parent','validate_authority'):
 nodes=[next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name==name) for t in trees.values()]
 check('runtime-override-'+name,ast.dump(nodes[0])==ast.dump(nodes[1]))
function=next(n for n in trees['full_w09_runtime.source.py'].body if isinstance(n,ast.FunctionDef) and n.name=='validate_authority')
call=next(n for n in function.body if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and any(isinstance(a,ast.Constant) and a.value=='FIXED_PRIVATE_PATHS' for a in n.value.args))
for key in choice['selectors']:
 item=m.choice(key)
 exec(compile(ast.Module(body=[call],type_ignores=[]),'<fixed physical path delta>','exec'),dict(c=item,R=m.R,N=m.N,Path=Path,re=m.re,require=m.require))
 check('new-physical-formula-'+key,Path(item['scratch_root']).parent.resolve(strict=True)==Path('C:/Users/yqyyds/.researchos/w09-native-v5'))
 bad=copy.deepcopy(item);bad['scratch_root']=old['selectors'][key]['scratch_root']
 try:exec(compile(ast.Module(body=[call],type_ignores=[]),'<reject old alias formula>','exec'),dict(c=bad,R=m.R,N=m.N,Path=Path,re=m.re,require=m.require))
 except ValueError:check('old-aliased-scratch-rejected-'+key,True)
 else:raise AssertionError('old scratch admitted')
check('source21-byte-pins-unchanged',choice['common']['source21']==old['common']['source21'])
check('compiler-blueprint-byte-exact',(N/'compiler-source-blueprint.json').read_bytes()==(OLD/'compiler-source-blueprint.json').read_bytes())
check('fresh-IDs-disjoint',not {v['run_id'] for v in choice['selectors'].values()} & {v['run_id'] for v in old['selectors'].values()})
check('resource-scope-three-exact-bindings',all(k in doc(N/'root-calling-contract.json')['scope_required_fields'] for k in ('resource_parent_ref','resource_owner_ref','resource_audit_ref')))
for row in doc(N/'source-delta.json')['source_edits']:
 text=(N/row['file']).read_bytes().decode()
 if row['appended']:
  assert text.endswith(row['appended']);text=text[:-len(row['appended'])]
 for e in reversed(row['replacements']):text=text.replace(e['after'],e['before'])
 check('exact-Source-inverse-'+row['file'],text.encode()==Path(row['base_ref']['path']).read_bytes())
report=dict(schema='researchos.nf5-source-delta-controls.v1',status='PASS',passed=len(checks),failed=0,checks=checks,
 resource_actual_readonly_refs=refs,actual_Native_runs=0,actual_Go_runs=0,actual_Canon_calls=0,
 RootScope_issued=False,old_NF4_controls_rerun=False,new_path_clause_controls_synthetic=True)
(N/'delta-controls.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='NF5_DELTA_PASS',passed=len(checks),report_ref=ref(N/'delta-controls.json')),ensure_ascii=False))

