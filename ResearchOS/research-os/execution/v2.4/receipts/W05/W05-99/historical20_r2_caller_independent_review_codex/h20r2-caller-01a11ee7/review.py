from pathlib import Path
import ast, copy, hashlib, importlib.util, json, re
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=B/'historical20_r2_caller_independent_review_codex/h20r2-caller-01a11ee7'
checks=[];inputs={}
def check(name, value):
 checks.append({'name':name,'pass':bool(value)})
def save(name,obj):
 with (O/name).open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def read(ref):
 actual=pin(ref['path']);check('pin:'+actual['path'],actual['sha256']==ref['sha256'].removeprefix('sha256:') and actual['bytes']==ref['bytes']);inputs[actual['path']]=actual;return Path(actual['path']).read_bytes()
def obj(ref):return json.loads(read(ref))
def direct(p):return obj(pin(p))
def members(m):return list(m['members'].values()) if isinstance(m['members'],dict) else m['members']
h=direct(O/'inputs/HDF.json');mf=direct(O/'inputs/MF.json')
for row in direct(O/'initial-pins.json'):read(row['original'])
for ref in members(mf):read(ref)
check('MF 9 members',mf['member_count']==len(members(mf))==9)
diff=direct(O/'packet/001/exact-replacements.json');choice=direct(O/'packet/005/source.integration.choice.json')
for ref in direct(O/'packet/002/input-pins.json'):read(ref)
prior=direct(B/'history20_five_parent_caller_independent_review_codex/h20v-20261009-source-review/HDF.json')
check('prior independent accepted',prior['status']=='SOURCE_APPROVED_FOR_ROOT_FRESH_SPARSE_AND_NARROW_VALIDATION' and prior['STOP'] and prior['FINAL'])
for ref in members(obj(prior['manifest_ref'])):read(ref)
read(prior['candidate_handoff_ref']);oldmf=obj(prior['candidate_manifest_ref'])
for ref in members(oldmf):read(ref)
inverse=[]
for i,row in enumerate(diff['callers']):
 old=read(row['base_ref']);new=read(row['new_ref']);check('prior review binds caller '+str(i),row['base_ref']==prior['prepare_ref' if i==0 else 'validate_ref'])
 changed=old
 for rep in row['replacements']:
  a=rep['old'].encode();b=rep['new'].encode();check('old occurrence '+str(i)+rep['old'],changed.count(a)==rep['count']);changed=changed.replace(a,b)
 check('full forward '+str(i),changed==new)
 inverse_bytes=new
 for rep in reversed(row['replacements']):
  a=rep['old'].encode();b=rep['new'].encode();check('new occurrence '+str(i)+rep['new'],inverse_bytes.count(b)==rep['count']);inverse_bytes=inverse_bytes.replace(b,a)
 check('full byte inverse '+str(i),inverse_bytes==old)
 oldtree=ast.parse(old);newtree=ast.parse(new);check('AST inverse '+str(i),ast.dump(ast.parse(inverse_bytes))==ast.dump(oldtree))
 for fn in [n for n in oldtree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))]:
  other=next(n for n in newtree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==fn.name);check('unchanged function '+str(i)+fn.name,ast.dump(fn)==ast.dump(other))
 a=[ast.dump(n.finalbody) if False else [ast.dump(x) for x in n.finalbody] for n in ast.walk(oldtree) if isinstance(n,ast.Try) and n.finalbody]
 b=[[ast.dump(x) for x in n.finalbody] for n in ast.walk(newtree) if isinstance(n,ast.Try) and n.finalbody];check('all finally preserved '+str(i),a==b)
 inverse.append({'caller':row['name'],'full_forward':changed==new,'full_inverse':inverse_bytes==old,'replacements':row['replacements']})
oldchoice=obj(diff['exact_prior_choice_ref']);check('prior choice binds',diff['exact_prior_choice_ref']==prior['choice_ref'])
restored=copy.deepcopy(choice);changed_fields=[]
for k in choice:
 if choice[k]!=oldchoice.get(k):changed_fields.append(k)
check('only declared choice changes',set(changed_fields)=={'source_components','fresh_worktree','fresh_isolation_output','fresh_validation_output','fresh_environment'})
check('other five components unchanged',choice['source_components'][:-1]==oldchoice['source_components'][:-1])
check('only H20R2 component replacement',choice['source_components'][-1]==diff['new_h20_component'] and oldchoice['source_components'][-1]==diff['prior_h20_component'])
restored['source_components'][-1]=oldchoice['source_components'][-1]
fresh={}
for k in ('fresh_worktree','fresh_isolation_output','fresh_validation_output','fresh_environment'):
 fresh[k]={'path':choice[k],'absent':not Path(choice[k]).exists()};check(k+' absent',fresh[k]['absent']);restored[k]=oldchoice[k]
check('entire choice semantic inverse',restored==oldchoice)
base=direct(choice['base_current49']);check('historical base facts retained',base['source_count']==49 and base['pass_count']==61 and base['fail_count']==6)
basepath=R/'.local/worktrees/codex-w0599-typed-q3-83b95f35e9bd4f81ad0c6682895a6ac1'
sources={Path(ref['path']).relative_to(basepath).as_posix():ref for ref in obj(base['formatted_source_ref'])};check('base49',len(sources)==49)
parents=set(base['exact_25_parent_names']);t11=obj(choice['actual_T11_overlay_ref'])['sources'];h20paths=set(choice['h20_candidate_paths'])
for component in choice['source_components']:
 sm=obj(component['source_manifest']);ih=obj(component['independent_handoff']);im=obj(component['independent_manifest']);obj(component['source_handoff'])
 for ref in members(sm)+members(im):read(ref)
 if component['component']=='H20R2':
  check('exact T11 58 composition',sources==t11 and len(sources)==58);check('R2 independent accepted',ih['status']=='SOURCE_ACCEPTED_PENDING_FRESH_ROOT_CALLER_AND_RUNTIME');check('R2 independent binds Source',ih['candidate_manifest_ref']==component['source_manifest'] and ih['candidate_handoff_ref']==component['source_handoff'])
 candidate=B/component['candidate_namespace']/'candidate-root';actualpaths=[]
 for ref in members(sm):
  p=Path(ref['path'])
  if p.is_relative_to(candidate):
   rel=p.relative_to(candidate).as_posix();actualpaths.append(rel);sources[rel]=ref
   if rel.endswith('_test.go'):parents.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',read(ref).decode('utf-8'),re.M))
 if component['component']=='H20R2':
  check('exact five H20 paths',set(actualpaths)==h20paths);testref=sources['internal/domain/backup_history20_upgrade_test.go'];check('R2 test accepted exact pin',testref==ih['test_ref'] and testref['sha256']=='914792b2e903f15026ea0a6d0652e1db5401076dc24fc9132bebaad3fa930f2f')
check('61 exact raw Source',len(sources)==choice['expected_source_count']==61)
check('non H20 unchanged from T11',all(sources[k]==v for k,v in t11.items() if k not in h20paths))
for ref in sources.values():read(ref)
selected=set(choice['exact_parent_names']);check('preserved parents59 and nonselected54',parents==set(choice['source_preserved_parent_names']) and len(parents)==59 and len(parents-selected)==54)
declared=set()
for k,ref in sources.items():
 if k.endswith('_test.go'):declared.update(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',read(ref).decode('utf-8'),re.M))
check('all declared parents preserved',declared==set(choice['all_source_file_declared_parent_names']))
test=read(testref).decode();testparents=set(re.findall(r'^func (Test[A-Za-z0-9_]+)\(',test,re.M));check('five exact parents derived',testparents==selected and len(selected)==5)
leaves=set(re.findall(r'"(migration-hash|extra-numbered-migration|foreign-table|session-addon)"',test));expected=selected|{'TestHistory20RejectsReleaseAndSourceDrift/'+x for x in leaves};check('nine terminals derived',len(leaves)==4 and len(expected)==9 and expected==set(choice['expected_terminal_names']))
prepare=read(diff['callers'][0]['new_ref']).decode();validate=read(diff['callers'][1]['new_ref']).decode()
check('prepare dynamic CP pins',all(s in prepare for s in ('len(sys.argv)==4','sys.argv[1],int(sys.argv[2]),int(sys.argv[3])','==checkpoint_sha','==checkpoint_bytes','==checkpoint_revision')))
check('validator dynamic CP isolation pins',all(s in validate for s in ('len(sys.argv)==8','sys.argv[3],int(sys.argv[4]),int(sys.argv[5])','sys.argv[6]','int(sys.argv[7])','==checkpoint_sha','==checkpoint_bytes','==checkpoint_revision')))
pt=ast.parse(prepare);vt=ast.parse(validate)
calls=lambda tree,name:[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id==name and n.args and isinstance(n.args[0],ast.Constant)]
pc=calls(pt,'invoke');vc=calls(vt,'success')+calls(vt,'invoke');check('six owned Git calls',len(pc)==6);check('four owned validation calls',len(vc)==4)
check('source-only ops CLI scope',all('./ops/backup' not in ast.unparse(n) for n in vc) and './internal/domain' in validate and 'ops/backup/main.go' in validate)
check('strict actual nine terminal gate',all(s in validate for s in ('starts==set(actions)==set(choice["expected_terminal_names"])','len(actions)==9','all(action=="pass" for action in actions.values())','events[-1]["Action"]=="pass"','name not in starts','name in starts and name not in actions')))
canonical={}
for name in ('checkpoint','path_ownership','step_state','commands'):
 p=R/'execution/v2.4'/(name+'.json');ref=pin(p);read(ref);canonical[name]=ref
cp=json.loads(Path(canonical['checkpoint']['path']).read_bytes());check('live CP364',cp['revision']==364)
G=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py';check('guard exact',pin(G)['sha256']=='e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85')
s=importlib.util.spec_from_file_location('guard',G);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);g=m.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
try:
 g.acquire(list(inputs.values()))
 for ref in inputs.values():check('guard buffer exact:'+ref['path'],hashlib.sha256(g.get_buffer(ref['path'])).hexdigest()==ref['sha256'])
finally:cleanup=g.close()
check('OS handles released',cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0)
save('guard.final.json',cleanup);save('input-pins.json',list(inputs.values()));save('checks.json',checks)
save('independent-diff.json',{'inverse':inverse,'choice_changed_fields':changed_fields,'choice_full_inverse':restored==oldchoice,'fresh_paths':fresh,'prior_independent_handoff':pin(B/'history20_five_parent_caller_independent_review_codex/h20v-20261009-source-review/HDF.json')})
save('composition.json',{'source_count':len(sources),'sources':sources,'preserved_parent_count':len(parents),'declared_parent_count':len(declared),'selected_parent_names':sorted(selected),'expected_terminal_names':sorted(expected),'owned_prepare_labels':[n.args[0].value for n in pc],'owned_validation_labels':[n.args[0].value for n in vc]})
save('canonical.observed.json',{'revision':cp['revision'],'refs':canonical,'failure_counters':cp['failure_counters'],'canonical_mutated':False})
print(json.dumps({'checks':len(checks),'failed':[x for x in checks if not x['pass']],'inputs':len(inputs),'source_count':len(sources),'CP_revision':cp['revision'],'guard_closed':cleanup['closed'],'actual_Git_Go_SQL_native_API':False},ensure_ascii=False))
