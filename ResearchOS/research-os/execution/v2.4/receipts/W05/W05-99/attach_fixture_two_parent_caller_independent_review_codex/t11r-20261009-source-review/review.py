import sys
sys.dont_write_bytecode=True
import pathlib,json,hashlib,ast,re,difflib
N=pathlib.Path(__file__).resolve().parent
R=N.parents[6]
B=N.parents[1]
A=B/'integration_codex'/'attach-fixture-current-two-parent-root-source-t11-1a11e7f5205729390aaee9f47b28ce6'
def pin(p):
 p=pathlib.Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def load(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def text(p):return pathlib.Path(p).read_text(encoding='utf-8')
def js(name,obj):
 with (N/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=True,indent=2);f.write('\n')
checks=[];refs={}
def ck(name,v):checks.append(dict(name=name,passed=bool(v)))
def verify(r):
 actual=pin(r['path']);ck('hash '+actual['path'],actual['sha256']==r['sha256'].removeprefix('sha256:') and actual['bytes']==r['bytes']);refs[actual['path']]=actual;return actual
expected={
'HDF.json':('51402abda88b6b159027cf356c6f7fd6f48aa580a0f30eeb8e95e94761c00726',3964),
'MF.json':('9a24553517872485673da57962078f351f3ceb6bfa78c75a221e147c911d52ba',10297),
'prepare_attach_fixture_two_parent.actual_owned.py':('4694aa929b27da960e23511be26da59a016e4a9b4f7296667335ebe6edca6020',7263),
'validate_attach_fixture_two_parent.actual_owned.py':('05c9c83463c8abd58d7ca4f92c56a8ed96e5a3a0a1cd22036613043f41ba3229',17560),
'source.integration.choice.json':('44afd8c086194419cc2f6f12ba01916adb2f8846345c7989e3fe071d046f79fc',19864)}
for name,(sha,size) in expected.items():verify(dict(path=str(A/name),sha256=sha,bytes=size))
manifest=load(A/'MF.json');ck('27 members',len(manifest['members'])==27)
for rel,r in manifest['members'].items():
 ck('manifest path '+rel,pathlib.Path(r['path']).resolve()==(A/rel).resolve());verify(r)
sourceguard=load(A/'sourceguard.initial.json')
for ref in sourceguard['refs']:verify(ref)
initial=list(refs.values());js('guard.initial.json',initial)
for i,ref in enumerate(initial):
 p=pathlib.Path(ref['path']);dest=N/'inputs'/str(i).zfill(4)/p.name;dest.parent.mkdir(parents=True,exist_ok=True)
 with dest.open('xb') as f:f.write(p.read_bytes())
rep=load(A/'source-replacements.json')
for label,file in [('prepare','prepare_attach_fixture_two_parent.actual_owned.py'),('validate','validate_attach_fixture_two_parent.actual_owned.py')]:
 base=text(A/'base'/(label+'.py'));candidate=text(A/file)
 tree=ast.parse(candidate);oldtree=ast.parse(base)
 inverse=candidate
 for item in reversed(rep[label]):
  ck(label+' unique inverse',inverse.count(item['new'])==1);inverse=inverse.replace(item['new'],item['old'],1)
 ck(label+' exact inverse',inverse.encode()==(A/'base'/(label+'.py')).read_bytes())
 with (N/(label+'.inverse.py')).open('xb') as f:f.write(inverse.encode())
 forward=base
 for item in rep[label]:
  ck(label+' unique forward',forward.count(item['old'])==1);forward=forward.replace(item['old'],item['new'],1)
 ck(label+' exact reconstruction',forward==candidate)
 patch=''.join(difflib.unified_diff(base.splitlines(True),candidate.splitlines(True),fromfile='base/'+label,tofile='candidate/'+label))
 ck(label+' patch exact',(A/(label+'.patch')).read_bytes()==patch.encode())
 funcs={x.name:x for x in tree.body if isinstance(x,ast.FunctionDef)}
 oldfuncs={x.name:x for x in oldtree.body if isinstance(x,ast.FunctionDef)}
 for name in funcs:
  if name=='closed':continue
  ck(label+' unchanged safety function '+name,ast.dump(funcs[name])==ast.dump(oldfuncs[name]))
 toptry=[x for x in tree.body if isinstance(x,ast.Try)]
 oldtry=[x for x in oldtree.body if isinstance(x,ast.Try)]
 ck(label+' finally unchanged',ast.dump(ast.Module(body=toptry[-1].finalbody,type_ignores=[]))==ast.dump(ast.Module(body=oldtry[-1].finalbody,type_ignores=[])))
p=text(A/'prepare_attach_fixture_two_parent.actual_owned.py');v=text(A/'validate_attach_fixture_two_parent.actual_owned.py')
basep=text(A/'base/prepare.py');basev=text(A/'base/validate.py')
ck('compiler inventory exact',v[v.index(' success("tagged-compiler-input-list"'):v.index(' binary=scratch/')]==basev[basev.index(' success("tagged-compiler-input-list"'):basev.index(' binary=scratch/')])
ck('five guard finally',all(x in v for x in ['(binary_guard,"binary")','(compiler_guard,"compiler")','(candidate_guard,"candidate")','(runtime_guard,"runtime")','(input_guard,"input")']))
ck('official t2j exact pin','dead8050fd4e0e0471407380898fe9642b9107048e0ad119cb652821dfe58f7c' in v)
ck('main dirty/staged policy exact','assert len(tracked_lines)==13 and sum(line.startswith(" D ") for line in tracked_lines)==11' in p and 'assert not (O/"staged-status.stdout.raw").read_bytes().strip()' in p)
ck('five owned Git invocations',p.count('=invoke(')==5)
ck('explicit prepare args','assert len(sys.argv)==4' in p and 'sys.argv[1],int(sys.argv[2]),int(sys.argv[3])' in p)
ck('explicit validate args','assert len(sys.argv)==8' in v and 'sys.argv[3],int(sys.argv[4]),int(sys.argv[5])' in v and '"sha256":sys.argv[6],"bytes":int(sys.argv[7])' in v)
ck('no hidden fixed checkpoint',all(x not in p+v for x in ['==361','==362','==363','27b6680899a8ba49b0f76fa6c7c917a80edecd0bcf68059de4dfc8da91088845']))
ck('exact CP SHA and size both drivers',all('pin(canonical[0])["sha256"]==checkpoint_sha and pin(canonical[0])["bytes"]==checkpoint_bytes' in s for s in [p,v]))
ck('fail closed fresh output paths',all('assert not O.exists();O.mkdir()' in s for s in [p,v]) and 'assert not T.exists()' in p)
choice=load(A/'source.integration.choice.json');oldchoice=load(A/'base/choice.json')
ck('old four source components exact',choice['source_components'][:-1]==oldchoice['source_components'])
ck('AF sole added component',len(choice['source_components'])==5 and choice['source_components'][-1]['component']=='AF')
af=choice['source_components'][-1]
ck('accepted AF source pin',af['source_handoff']['sha256']=='e28f505265ff2dc2e0b95e8060dd535c888fd8665fc0e70fd2c60389c2798947')
ck('accepted independent AF pin',af['independent_handoff']['sha256']=='d69d12f0519944ccfebf462857cc8788f94071a5c3a930e008a9abda25ee8e8b')
for f,ref in zip(['prepare.py','validate.py','choice.json'],choice['base_driver_refs']):
 verify(ref);ck('base copy exact '+f,(A/'base'/f).read_bytes()==pathlib.Path(ref['path']).read_bytes())
baseactual=load(choice['base_current49'])
formatted=load(baseactual['formatted_source_ref']['path'])
P=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
sources={pathlib.Path(x['path']).resolve().relative_to(P).as_posix():verify(x) for x in formatted}
ck('base49 count',len(sources)==49)
parents=set(baseactual['exact_25_parent_names'])
af_changed=[]
for component in choice['source_components']:
 for key in ['source_handoff','source_manifest','independent_handoff','independent_manifest']:verify(component[key])
 for key in ['source_manifest','independent_manifest']:
  members=load(component[key]['path'])['members'];members=list(members.values()) if isinstance(members,dict) else members
  for ref in members:verify(ref)
 manifest2=load(component['source_manifest']['path'])['members']
 values=list(manifest2.values()) if isinstance(manifest2,dict) else manifest2
 root=(B/component['candidate_namespace']/'candidate-root').resolve()
 for ref in values:
  path=pathlib.Path(ref['path']).resolve()
  if not path.is_relative_to(root):continue
  rel=path.relative_to(root).as_posix()
  if component['component']=='AF':af_changed.append(rel)
  sources[rel]=pin(path)
  if rel.endswith('_test.go'):parents.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',text(path),re.M))
ck('58 composed members',len(sources)==58)
ck('AF only1 test overwrite',af_changed==['internal/domain/client_protocol_attach_contract_windows_test.go'])
ck('composed declared exact',sources==load(A/'composition.source-members.json'))
selected={'TestClientAttachSettledAcquisitionCompletesAndReplays','TestClientAttachPreservesStaleAndBindingGates'}
ck('54 preserved parents',len(parents)==54 and parents==set(choice['source_preserved_parent_names']))
ck('exact two selected',set(choice['exact_parent_names'])==selected)
ck('52 nonselected',len(parents-selected)==52)
allnames=set()
for rel,ref in sources.items():
 if rel.endswith('_test.go'):allnames.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',text(ref['path']),re.M))
ck('132 declarations',len(allnames)==132 and allnames==set(choice['all_source_file_declared_parent_names']))
ck('anchored exact selector','selector="^("+("|".join(sorted(new_tests)))+")$"' in v)
ck('all started finish without failure skip','starts==set(actions) and new_tests.issubset(starts) and all(action=="pass" for action in actions.values())' in v)
ck('other52 not claimed','nonselected_parents_executed_or_newly_accepted=False' in v)
ck('history20 blocked',choice['ordinary_history20_full_release_program_rehearsal_authority']=='BLOCKED' and 'ordinary_history20_full_release_program_rehearsal_authority="BLOCKED"' in v)
# Execute only the already inspected pure Source-composition statements, never the actual entrypoint.
tree=ast.parse(v)
scope=dict(Path=pathlib.Path,hashlib=hashlib,json=json,re=re,R=R,B=B,P=P,A=pathlib.Path(choice['base_current49']).parent,choice=choice,sources={},input_refs=[])
functions=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in ('pin','verify','members','unique')]
exec(compile(ast.Module(body=functions,type_ignores=[]),'<reviewed-pure-source-functions>','exec'),scope)
start=v.index('assert pin(A/"validation.closed.json")');end=v.index('\ncanonical=[',start)
exec(compile(v[start:end],'<reviewed-source-composition-only>','exec'),scope)
ck('exact candidate Source block composition',scope['sources']==sources and scope['new_tests']==selected and scope['preserved_parent_sources']==parents)
ck('full Source context preflight count',len(scope['input_refs'])==784)
contract=load(A/'execution-contract.json');pathstatus={}
for field in ['worktree','isolation_output','target_output','scratch']:
 path=pathlib.Path(contract[field]);pathstatus[field]=dict(path=str(path),exists=path.exists());ck('fresh '+field,not path.exists())
ck('contract worktree paths',contract['worktree'].replace('\\','/') in p and contract['worktree'].replace('\\','/') in v)
ck('contract output paths',contract['isolation_output'].replace('\\','/') in p and contract['isolation_output'].replace('\\','/') in v and contract['target_output'].replace('\\','/') in v and contract['scratch'].replace('\\','/') in v)
ck('all independent MF members input guarded','input_refs.extend(verify(ref) for ref in members(item["independent_manifest"]))' in v)
js('path-status.json',pathstatus)
js('source-composition-reviewed.json',dict(sources=sources,preserved_parents=sorted(parents),selected=sorted(selected),nonselected=sorted(parents-selected),declarations=sorted(allnames),pure_composition_input_count=len(scope['input_refs']),actual_entrypoint_executed=False))
final=[pin(x['path']) for x in initial];ck('full guarded input closure',initial==final)
js('guard.final.json',dict(unchanged=initial==final,before=initial,after=final))
js('checks.json',checks)
out=dict(status='SOURCE_ACCEPTED_PENDING_ROOT_ACTUAL' if all(x['passed'] for x in checks) else 'REQUEST_CHANGES',checks=len(checks),failed=[x for x in checks if not x['passed']],source_guard_count=len(sourceguard['refs']),guarded_unique_count=len(initial),source_members=58,preserved_parents=54,selected_parents=2,nonselected_parents=52,all_source_declarations=132,Git_Go_SQL_native_model_actual=False,formal_acceptance=False)
js('result.json',out);print(json.dumps(out))

