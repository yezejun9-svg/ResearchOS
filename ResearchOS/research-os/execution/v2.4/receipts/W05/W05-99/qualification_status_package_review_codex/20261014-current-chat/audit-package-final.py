import pathlib,json,hashlib,subprocess,datetime,copy,base64,collections,re
E=pathlib.Path(__file__).resolve().parent/'verified-audit'
E.mkdir(exist_ok=False)
ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os');S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-repair-20261014')
P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-status-combined-5ddc0abb-20261014');OLD=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-attach-combined-c465d135-20261014')
F=ROOT/'execution/v2.4/receipts/W05/W05-99/qualification_status_desktop_build_codex/20261014-current-chat';MP=F/'FINAL-manifest.json'
C='5ddc0abb8c6d95e9ca071a4eb41a7e12b8559456';T='bfade6fd49897f53e2ec629c71691405be2f2fbe';B='c465d1356480d6e6a90da84656724f9fc02b31c7';MAIN='454492f78fc0536966c8c8343d4bdd2fd99250b7';CORE='b955c8665281193d5cbf90a146f936c9212c7940';MU='8dfebe36508ac0c2508735bb866756dab9283e74'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(name,value):
 with (E/name).open('x',encoding='utf8') as stream:json.dump(value,stream,ensure_ascii=True,indent=2)
def record(p):
 p=pathlib.Path(p);raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args]).decode('utf8').strip()
assert record(MP)['sha256']=='2eacc362c5ee59c8ae1273007f93b4086378b715df1549eeff55e73fbe678703'
M=read(MP);CMP=read(F/'composition.json');D=read(P/'apps/desktop/resources/client-wire/descriptor.json');RAW=pathlib.Path(M['build']['raw_receipts'])
checked={};reference_errors=[]
def references(obj):
 if isinstance(obj,dict):
  if all(k in obj for k in ('path','bytes','sha256')) and pathlib.Path(obj['path']).is_absolute():
   p=pathlib.Path(obj['path']);key=str(p)
   if key not in checked:
    try:checked[key]=record(p)
    except Exception as error:checked[key]={'path':key,'error':str(error)}
   actual=checked[key]
   if actual.get('bytes')!=obj['bytes'] or actual.get('sha256')!=obj['sha256']:reference_errors.append({'expected':obj,'actual':actual})
  for value in obj.values():references(value)
 elif isinstance(obj,list):
  for value in obj:references(value)
for obj in [M,CMP,D]:references(obj)
for value in M['build']['invocations'].values():references(read(value['receipt']['path']))
archive=read(RAW/'compiler-work-archive.json');references(archive)
assert git(S,'rev-parse','HEAD')==C and git(S,'rev-parse','HEAD^{tree}')==T and git(S,'status','--porcelain=v1')==''
assert git(ROOT,'rev-parse','HEAD')==MAIN and git(ROOT,'rev-parse','HEAD^{tree}')==T
assert git(S,'rev-parse',B+'^{tree}')==git(S,'rev-parse',CORE+'^{tree}')=='00d44e133662227b115eb3b16bef3d4edcc35630'
delta=git(S,'diff','--name-only',B,C).splitlines();assert sorted(delta)==sorted(CMP['changed_paths_exact'])
assert all(p.startswith(('apps/desktop/main/lib/desktop-management.js','apps/web/src/workbench.jsx','tests/ui/desktop/')) for p in delta)
files=[]
for row in CMP['package_files']:
 target=(P/row['path']).resolve();assert target.is_relative_to(P.resolve());actual=record(target)
 item={**row,'actual':actual,'matches_composition':actual['sha256']==row['sha256'] and actual['bytes']==row['bytes']}
 if row['component']=='NEW_INSTALLATION_MANIFEST_REUSED_VERIFIER':item['generator_ref_only']=record(row['source'])
 else:item['matches_source']=record(row['source'])['sha256']==actual['sha256']
 if 'EQUAL_OLD' in row['component'] or row['component'].startswith('REUSED_'):item['matches_old']=record(OLD/row['path'])['sha256']==actual['sha256']
 if row['path'].startswith(('apps/desktop/main/','apps/desktop/preload/','internal/api/contracts/','migrations/','spec/')):item['matches_candidate']=record(S/row['path'])['sha256']==actual['sha256']
 if row['component']=='NEW_BOUND_REACT':
  independent=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-status-independent-review-20261014/web-dist')/pathlib.Path(row['path']).relative_to('apps/web/dist');item['matches_independent_source_build']=record(independent)['sha256']==actual['sha256']
 files.append(item)
actual_members=sorted(p.relative_to(P).as_posix() for p in P.rglob('*') if p.is_file());expected_members=sorted(r['path'] for r in files)
assert len(actual_members)==58 and actual_members==expected_members
assert M['package']['members']==CMP['package_files']
assert all(all(v for k,v in item.items() if k.startswith('matches_')) for item in files)
assert len(D['exact_module_source_inventory'])==14 and len(D['compiled_React_asset_inventory'])==3
for row in D['exact_module_source_inventory']:
 assert record(P/'apps/desktop'/row['path'])['sha256']==row['sha256']==record(S/'apps/desktop'/row['path'])['sha256']
for row in D['compiled_React_asset_inventory']:
 assert record(P/'apps/web/dist'/row['path'])['sha256']==row['sha256']
before=read(RAW/'inputs.before.json');after=read(RAW/'inputs.after.json');input_bad=[]
for row in before:
 actual=record(row['path'])
 if actual['sha256']!=row['sha256'] or actual['bytes']!=row['bytes']:input_bad.append({'expected':row,'actual':actual})
bound=sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())
assert len(before)==6444 and not input_bad
assert bound==D['build_input_digest']==CMP['bound_full_input_digest']==M['build']['input_digest']
assert [{k:row[k] for k in ['path','sha256','bytes']} for row in after]==before
assert all(row['sha256']==row['current_sha256'] for row in after)
assert D['binary_sha256']==record(P/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')['sha256']==CMP['validator_sha256']
assert not reference_errors
versions=[]
for name,relative,commit in [('control','apps/desktop/resources/control/researchos-control.exe',CORE),('runtime-verifier','apps/desktop/resources/control/runtime-verifier.exe',CORE),('validator','apps/desktop/resources/client-wire/researchos-client-wire-validator.exe',C)]:
 argv=[D['go_tool_ref']['path'],'version','-m',str(P/relative)];proc=subprocess.run(argv,cwd=E,capture_output=True)
 (E/(name+'-version-m.stdout.raw')).write_bytes(proc.stdout);(E/(name+'-version-m.stderr.raw')).write_bytes(proc.stderr)
 item={'argv':argv,'cwd':str(E),'native_exit':proc.returncode,'binary':record(P/relative),'expected_source_commit':commit};save(name+'-version-m.process.json',item)
 text=proc.stdout.decode('utf8');assert proc.returncode==0 and 'vcs.revision='+commit in text and 'vcs.modified=false' in text
 if name=='validator':assert bound in text
 versions.append(item)
installer=read(P/'apps/desktop/resources/control/runtime-verifier-installation.json');verifier=P/'apps/desktop/resources/control/runtime-verifier.exe'
assert pathlib.Path(installer['executable']).resolve()==verifier.resolve() and pathlib.Path(installer['executable']).is_absolute()
assert installer['executable_hash']=='sha256:'+record(verifier)['sha256'] and installer['source_commit']==CORE and installer['arguments']==[]
for path,row in M['package']['mu_reuse'].items():assert row['source_commit']==MU and record(P/path)['sha256']==row['sha256']==record(OLD/path)['sha256']
inv=read(RAW/'package-cases.invocation.json');log=pathlib.Path(inv['stdout']['path']).read_text(encoding='utf8');assert inv['native_exit']==0 and inv['counts']['tests']==inv['counts']['pass']==214 and inv['counts']['fail']==0 and inv['counts']['skipped']==0
# Native Node summary is retained raw; wrappers cannot replace its counts.
counts={k:int(v) for k,v in re.findall(r'^.*? (tests|pass|fail|cancelled|skipped|todo) (\d+)\s*$',log,re.M)}
assert counts=={'tests':214,'pass':214,'fail':0,'cancelled':0,'skipped':0,'todo':0}
summary={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'author_manifest':record(MP),'source':{'candidate':C,'candidate_tree':T,'main':MAIN,'main_tree':T,'clean_candidate':True,'exact_changed_paths':delta,'old_core':CORE,'old_core_base_same_tree':True,'mu':MU},'package_root':str(P),'package_member_count':len(actual_members),'package_members':files,'component_counts':dict(collections.Counter(r['component'] for r in files)),'bound_input_count':len(before),'bound_input_digest':bound,'inputs_current_match':True,'before_after_consistent':True,'input_scope_note':'Complete declared bound build snapshot; 6444 is not the count of files individually passed to compile.exe. Raw -work/-x and archive inputs are separately checked.','references_checked':len(checked),'reference_errors':reference_errors,'reference_files':list(checked.values()),'module_count':14,'react_count':3,'versions':versions,'installer':installer,'builder_package_cases':{'native_exit':inv['native_exit'],'counts':inv['counts'],'invocation':record(RAW/'package-cases.invocation.json'),'stdout':record(inv['stdout']['path'])},'not_executed':['Desktop','Core/control','runtime-verifier','real database','API','model'],'writes_outside_review':0}
save('package-audit.json',summary)
print(json.dumps({'members':len(actual_members),'inputs':len(before),'digest':bound,'references_checked':len(checked),'version_m_exit':[r['native_exit'] for r in versions],'components':summary['component_counts']},ensure_ascii=True))
