"""Finite Source delta controls: stubs are not Root or Native evidence."""
import ast,copy,hashlib,json,types
from pathlib import Path
N=Path(__file__).resolve().parent
OLD=N.parent/'fullw09-20261010-03'
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def doc(p):return json.loads(p.read_bytes())
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def mod(p):
 m=types.ModuleType(p.stem);m.__file__=str(p);exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
checks=[]
def check(name,ok):assert ok,name;checks.append(name)
runtime=mod(N/'full_w09_runtime.source.py')
choice=doc(N/'source.choice.json');contract=doc(N/'root-calling-contract.json');delta=doc(N/'source-delta.json')
for key in ('W09-G01','W09-G02','A06','C19'):
 c=runtime.choice(key)
 check('choice-'+key,c['generation']=='fullw09-20261010-04' and c['selector_key']==key)
 e=runtime.build_environment(c)
 check('private-cache-'+key,e['GOCACHE']==str(Path(c['scratch_root'])/'gocache') and e['GOPROXY']=='off' and e['GOENV']=='off')
 check('future-paths-absent-'+key,all(not Path(c[k]).exists() for k in ('scratch_root','receipt_root','output_root')))
try:runtime.choice('BAD')
except ValueError:check('reject-fifth-selector',True)
else:raise AssertionError('fifth selector admitted')
trees={n:ast.parse((N/n).read_bytes()) for n in ('full_w09_runtime.source.py','runtime-overrides.source.py')}
for function in ('choice','validate_authority','read_inputs','validate_packet'):
 def node(tree):return next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==function)
 check('runtime-overrides-identical-'+function,ast.dump(node(trees['full_w09_runtime.source.py']))==ast.dump(node(trees['runtime-overrides.source.py'])))
v=next(n for n in trees['full_w09_runtime.source.py'].body if isinstance(n,ast.FunctionDef) and n.name=='validate_packet')
routing=[n for n in v.body if isinstance(n,ast.If) and any(isinstance(x,ast.Attribute) and x.attr in ('verify_c19','verify_a06') for x in ast.walk(n))]
for selector,want in {'W09-G01':['C19','A06'],'W09-G02':['A06'],'A06':['A06'],'C19':['C19']}.items():
 calls=[];closure=types.SimpleNamespace(verify_c19=lambda _:calls.append('C19'),verify_a06=lambda _:calls.append('A06'))
 exec(compile(ast.Module(body=routing,type_ignores=[]),'<Source routing controls>','exec'),dict(c={'selector_key':selector},closure=closure,owned={}))
 check('owned-closure-'+selector,calls==want)
for name in ('full_w09_runtime.source.py','runtime-overrides.source.py','full_w09_launcher.source.py','prepare_full_w09.source.py','run_full_w09.source.py'):
 text=(N/name).read_text(encoding='utf-8')
 for e in reversed([e for e in delta['text_edits'] if e['file']==name]):text=text.replace(e['after'],e['before'])
 check('exact-inverse-'+name,text.encode('utf-8')==(OLD/name).read_bytes())
 # All text sources are parsed, not invoked.
 ast.parse((N/name).read_bytes())
check('Source21-current-test-only',sum(a!=b for a,b in zip(delta['source21_before'],delta['source21_after']))==1)
bp=doc(N/'compiler-source-blueprint.json');oldbp=doc(OLD/'compiler-source-blueprint.json')
restored=copy.deepcopy(bp);restored['stable_input_refs']=oldbp['stable_input_refs']
check('blueprint-other-fields-exact',restored==oldbp)
check('actual-package-count-not-invented',bp['source_only'] is True and bp['actual_package_count'] is None)
check('C19-one-package-two-tests-five-IDs',len(choice['selectors']['C19']['selected_tests'])==2 and len(choice['selectors']['C19']['expected_native_ids'])==5 and choice['selectors']['C19']['packages']==['./internal/domain'])
check('four-run-IDs-new',len({v['run_id'] for v in choice['selectors'].values()})==4 and not {v['run_id'] for v in choice['selectors'].values()} & {v['run_id'] for v in doc(OLD/'source.choice.json')['selectors'].values()})
check('generation-field-bound','generation' in contract['scope_required_fields'] and contract['generation']==choice['common']['generation'])
check('source-pins-consistent',all(ref(N/name)==contract['bound_source_refs'][k] for k,name in contract['source_file_bindings'].items()))
check('old-scratch-formula-absent',all("str(R/'.local'/('w09-full-'" not in (N/name).read_text(encoding='utf-8') for name in trees))
check('fresh-cache-runtime-preserved',"FRESH_PRIVATE_GOCACHE" in (N/'full_w09_runtime.source.py').read_text(encoding='utf-8'))
put(N/'delta-controls.json',dict(schema='researchos.nf4-source-delta-controls.v1',status='PASS',passed=len(checks),failed=0,
 checks=checks,synthetic_Source_only=True,actual_Root_authority=False,actual_Native_runs=0,actual_Go_runs=0,
 actual_Canon_calls=0,old_controls_rerun=False))
print(json.dumps(dict(status='NF4_DELTA_CONTROLS_PASS',passed=len(checks),report_ref=ref(N/'delta-controls.json')),ensure_ascii=False))

