"""Build only NF4 Source. No Native, Root Scope, or canonical operation."""
import ast,copy,hashlib,json,re,types,uuid
from pathlib import Path
N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
OLD=N.parent/'fullw09-20261010-03'
AUTHOR='codex:/root/attach_restore_independent_review'
SESSION='01a11e0c-eef6-7363-a5b1-da61d6ae7f4c'
GEN='fullw09-20261010-04'
SCRATCH=Path('C:/Users/yqyyds/AppData/Local/ResearchOS/w09-native-v4')
def ref(p):
 b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def write(p,b):
 with p.open('xb') as f:f.write(b)
def load(p):return json.loads(p.read_bytes())
base=load(OLD/'source.choice.json')
main=R/'internal/domain/retrieval_test.go'
assert ref(main)['sha256']=='1254f8c7524638cac6bee492fe7d4daf685722250779f86e36e97b0e7a9f1141' and ref(main)['bytes']==32352
names=['full_w09_runtime.source.py','runtime-overrides.source.py','full_w09_launcher.source.py','prepare_full_w09.source.py','run_full_w09.source.py','source.choice.json','compiler-source-blueprint.json','root-calling-contract.json']
pins=[ref(OLD/n) for n in names]+[ref(OLD/'HDF.json'),ref(OLD/'MF.json')]+[ref(Path(x['path'])) for x in base['common']['source21']]
gr=base['common']['guard_ref'];raw=Path(gr['path']).read_bytes();assert hashlib.sha256(raw).hexdigest()==gr['sha256']
gm=types.ModuleType('nf4_guard');gm.__file__=gr['path'];exec(compile(raw,gr['path'],'exec'),gm.__dict__)
g=gm.SourceReadGuard(total_cap=256*1024*1024);g.acquire(pins)
edits=[]
def transform(name,changes):
 original=(OLD/name).read_bytes();text=original.decode('utf-8')
 for before,after in changes:
  count=text.count(before);assert count>0,(name,before)
  text=text.replace(before,after);edits.append(dict(file=name,before=before,after=after,count=count))
 candidate=text.encode('utf-8')
 # Exact inverse of all text replacements, in reverse application order.
 restored=text
 for e in reversed([e for e in edits if e['file']==name]):restored=restored.replace(e['after'],e['before'])
 assert restored.encode('utf-8')==original,('EXACT_TEXT_INVERSE',name)
 write(N/name,candidate)
try:
 common=[
 ("('W09-G01','W09-G02','A06')","('W09-G01','W09-G02','A06','C19')"),
 ("{'W09-G01','W09-G02','A06'}","{'W09-G01','W09-G02','A06','C19'}"),
 ('THREE_SELECTORS_ONLY','FOUR_SELECTORS_ONLY'),('EXACT_THREE_CHOICES','EXACT_FOUR_CHOICES'),
 ('three-selector','four-selector'),('THREE_SELECTOR','FOUR_SELECTOR'),
 ("'source21')","'source21','generation')"),
 ("cp['work_in_progress']['w09_native_producer_scopes'][c['selector_key']]","cp['work_in_progress']['w09_native_producer_scope_generations'][c['generation']][c['selector_key']]"),
 ("owner=dict(owner=ROOT_ACTOR,","owner=dict(generation=c['generation'],owner=ROOT_ACTOR,"),
 ("worker=dict(step_id='W09-99',","worker=dict(generation=c['generation'],step_id='W09-99',"),
 ("str(R/'.local'/('w09-full-'+c['selector_key']+'-'+c['run_id']))","str(Path('C:/Users/yqyyds/AppData/Local/ResearchOS/w09-native-v4')/(c['selector_key']+'-'+c['run_id']))"),
 ("require(c['source_root']==str(R)","require(c['generation']=='fullw09-20261010-04' and c['source_root']==str(R)"),
 ("bp['required_packages']==c['packages']","bp['required_packages']==['./adapters/retrieval','./internal/domain'] and set(c['packages']).issubset(bp['required_packages'])"),
 ("if c['selector_key']=='W09-G01':closure.verify_c19(owned)","if c['selector_key'] in ('W09-G01','C19'):closure.verify_c19(owned)"),
 ("    closure.verify_a06(owned)","    if c['selector_key'] in ('W09-G01','W09-G02','A06'):closure.verify_a06(owned)")]
 transform('full_w09_runtime.source.py',common+[
 ("AUTHOR='codex:/root/w09_formal_profile_source_impl'","AUTHOR='"+AUTHOR+"'"),
 ("OWNER_KEY='full_w09_main_native_producer'","OWNER_KEY='full_w09_main_native_producer_fullw09-20261010-04'"),
 ("SLICE='FULL_W09_MAIN_NATIVE_PRODUCER'","SLICE='FULL_W09_MAIN_NATIVE_PRODUCER_fullw09-20261010-04'")])
 transform('runtime-overrides.source.py',common)
 runtime=ref(N/'full_w09_runtime.source.py')
 oldsha=ref(OLD/'full_w09_runtime.source.py')['sha256']
 for name in ('prepare_full_w09.source.py','run_full_w09.source.py'):
  transform(name,[(oldsha,runtime['sha256'])])
 transform('full_w09_launcher.source.py',[(oldsha,runtime['sha256']),('three-selector','four-selector')])
 bp=load(OLD/'compiler-source-blueprint.json')
 oldstable=copy.deepcopy(bp['stable_input_refs'])
 for x in bp['stable_input_refs']:
  if x['path']==str(main):x.update(ref(main))
 assert sum(a!=b for a,b in zip(oldstable,bp['stable_input_refs']))==1
 put(N/'compiler-source-blueprint.json',bp)
 choice=copy.deepcopy(base)
 choice['schema']=choice['schema'].replace('three-selector','four-selector');choice['actor_id']=AUTHOR
 choice['common']['generation']=GEN
 choice['common']['source21']=[ref(Path(x['path'])) for x in base['common']['source21']]
 assert sum(a!=b for a,b in zip(base['common']['source21'],choice['common']['source21']))==1
 choice['common']['compiler_blueprint_ref']=ref(N/'compiler-source-blueprint.json')
 # Compile only actual top-level data assignments from Main, never its entrypoint.
 tree=ast.parse((R/'ops/ci/retrieval.py').read_bytes())
 assignments=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('TESTS','GROUPS','CASES') for t in n.targets)]
 env={};exec(compile(ast.Module(body=assignments,type_ignores=[]),'<Main selector data>','exec'),env)
 tests=env['CASES']['C19'];ids=[i for t in tests for i in env['TESTS'][t][1]]
 packages=sorted({env['TESTS'][t][0] for t in tests})
 c19=copy.deepcopy(choice['selectors']['W09-G01'])
 c19.update(selector=dict(task_id='W09',check_id='',case_id='C19'),selector_key='C19',selected_tests=tests,
  expected_native_ids=ids,packages=packages,go_test_argv_suffix=['test','-count=1','-json','-run','^(?:'+'|'.join(tests)+')$',*packages],
  assertion_owner={i:t for t in tests for i in env['TESTS'][t][1]},required_independent_modes=2)
 choice['selectors']['C19']=c19
 for key,item in choice['selectors'].items():
  run=uuid.uuid4().hex;item.update(run_id=run,receipt_root=str(N/('actual-'+key+'-'+run)),
    scratch_root=str(SCRATCH/(key+'-'+run)),output_root=str(R/'execution/receipts/W09/retrieval'/('run-'+run)))
  assert all(not Path(item[k]).exists() for k in ('receipt_root','scratch_root','output_root'))
 put(N/'source.choice.json',choice)
 contract=load(OLD/'root-calling-contract.json')
 def rebase(x):
  if isinstance(x,str):return x.replace(str(OLD),str(N)).replace('three-selector','four-selector').replace('THREE_SELECTOR','FOUR_SELECTOR').replace('codex:/root/w09_formal_profile_source_impl',AUTHOR).replace('01a12011-7d41-7991-a01c-de2d71701ff7',SESSION)
  if isinstance(x,list):return [rebase(v) for v in x]
  if isinstance(x,dict):return {k:rebase(v) for k,v in x.items()}
  return x
 contract=rebase(contract);contract['scope_required_fields'].append('generation')
 contract['bound_source_refs']={k:ref(N/name) for k,name in contract['source_file_bindings'].items()}
 contract['canonical_registration']=dict(checkpoint_wip='w09_native_producer_scope_generations[generation][selector_key]',
 ownership_subtask='full_w09_main_native_producer_'+GEN+'_<selector_key>',worker_slice='FULL_W09_MAIN_NATIVE_PRODUCER_'+GEN+'_<selector_key>')
 contract['no_standalone_C19']=False;contract['generation']=GEN
 contract['scratch_policy']=dict(exact_parent=str(SCRATCH),exact_leaf='<selector>-<runid>',project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',
  physical_local_path=True,no_reparse_or_alias=True,Root_must_create_parent_separately=True,fresh_empty_GOCACHE_each_run=True,
  reuse_only_existing_locked_GOROOT_and_GOPATH_pkgmod=True,old_cache_delete_or_move=False)
 put(N/'root-calling-contract.json',contract)
 for name in names:
  if name.endswith('.py'):ast.parse((N/name).read_bytes())
 put(N/'source-delta.json',dict(base_refs=[ref(OLD/name) for name in names],text_edits=edits,exact_text_inverse=True,
  source21_before=base['common']['source21'],source21_after=choice['common']['source21'],
  blueprint_before_ref=ref(OLD/'compiler-source-blueprint.json'),compiler_stable_ref_changed_count=1,
  current_Main_C19_data=dict(selected_tests=tests,expected_native_ids=ids,packages=packages),
  Main_written=False,Canon_written=False,actual_Native_runs=0,actual_Go_runs=0,actual_scope_registration=False))
finally:
 closed=g.close();put(N/'source-guard.closed.json',closed)
 assert closed['closed'] and closed['retained_handles_count']==0 and not closed['errors']
print(json.dumps(dict(status='NF4_SOURCE_BUILT_PENDING_DELTA_CONTROLS',runtime_ref=runtime,contract_ref=ref(N/'root-calling-contract.json')),ensure_ascii=False))

