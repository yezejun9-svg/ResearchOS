import pathlib,json,hashlib,subprocess,datetime,collections,re,os
E=pathlib.Path(__file__).parent;ROOT=pathlib.Path('D:/作品集/ResearchOS/research-os')
S=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/coding-any-combined-build-20261014')
P=pathlib.Path('C:/Users/yqyyds/.codex/researchos-resource-cache/normal-coding-any-a7ec7ebf-20261014');OLD=P.parent/'normal-status-combined-5ddc0abb-20261014'
F=ROOT/'execution/v2.4/receipts/W05/W05-99/coding_any_desktop_build_codex/20261014-current-chat'
C='a7ec7ebf2d53848ea163b6115667b3e3761a6bd2';TREE='5b54aa0b8b94cb8012413efd401dc417671b06de';MU='8dfebe36508ac0c2508735bb866756dab9283e74'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def save(n,o):(E/n).write_text(json.dumps(o,ensure_ascii=True,indent=2),encoding='utf8')
def record(p):
 p=pathlib.Path(p);data=p.read_bytes();return {'path':str(p),'sha256':sha(data),'bytes':len(data)}
def git(*a):return subprocess.check_output(['git','-C',str(S),*a]).decode().strip()
assert record(F/'FINAL-manifest.json')['sha256']=='544657c2e5b8f121289ac5de133ae010d432653561806c12bca8bf601cca3d98'
assert record(F/'composition.json')['sha256']=='04ccb8ef06485aa521136a38da7dd800aef45bcddaac0d744a41120b2a019a71'
M=read(F/'FINAL-manifest.json');CMP=read(F/'composition.json');D=read(P/'apps/desktop/resources/client-wire/descriptor.json');RAW=pathlib.Path(M['build']['raw_receipts'])
checked={};errors=[]
def references(o):
 if isinstance(o,dict):
  if all(k in o for k in ['path','sha256','bytes']) and pathlib.Path(o['path']).is_absolute():
   key=o['path']
   if key not in checked:checked[key]=record(key)
   if checked[key]['sha256']!=o['sha256'] or checked[key]['bytes']!=o['bytes']:errors.append({'expected':o,'actual':checked[key]})
  for v in o.values():references(v)
 elif isinstance(o,list):
  for v in o:references(v)
for o in [M,CMP,D]:references(o)
archive=read(RAW/'compiler-work-archive.json');references(archive)
invocations={}
for name,row in M['build']['invocations'].items():
 inv=read(row['receipt']['path']);references(inv)
 assert inv['actualargv']==row['actualargv'] and inv['cwd']==row['cwd'] and inv.get('native_exit',inv.get('exit'))==row['native_exit']==0,name
 rawrows={}
 for stream in ['stdout','stderr']:
  v=inv[stream];path=pathlib.Path(v['path']) if isinstance(v,dict) else RAW/v
  rawrows[stream]=record(path)
 invocations[name]={'receipt':record(row['receipt']['path']),'actualargv':inv['actualargv'],'cwd':inv['cwd'],'native_exit':inv.get('native_exit',inv.get('exit')),'raw':rawrows}
assert not errors
assert git('rev-parse','HEAD')==C and git('rev-parse','HEAD^{tree}')==TREE and git('status','--porcelain')==''
delta=git('diff','--name-only',CMP['base_commit'],C).splitlines();assert sorted(delta)==sorted(CMP['changed_paths_exact'])
files=[]
for row in CMP['package_files']:
 p=P/row['path'];assert p.resolve().is_relative_to(P.resolve());r=record(p);assert r['sha256']==row['sha256'] and r['bytes']==row['bytes']
 if row['component']!='NEW_INSTALLATION_MANIFEST_FRESH_VERIFIER':assert record(row['source'])['sha256']==r['sha256']
 if 'EQUAL_OLD' in row['component'] or row['component'].startswith('REUSED_'):assert record(OLD/row['path'])['sha256']==r['sha256']
 if row['path'].startswith(('apps/desktop/main/','apps/desktop/preload/','internal/api/contracts/','migrations/','spec/')):assert record(S/row['path'])['sha256']==r['sha256']
 files.append(r|{'relative_path':row['path'],'component':row['component'],'source':row['source'],'source_commit':row['source_commit']})
actual=[]
for p in P.rglob('*'):
 assert not p.is_symlink() and not p.is_junction(),str(p)
 if p.is_file():actual.append(p.relative_to(P).as_posix())
assert len(actual)==58 and sorted(actual)==sorted(r['path'] for r in CMP['package_files'])
assert M['package']['members']==CMP['package_files']
assert len(D['exact_module_source_inventory'])==14 and len(D['compiled_React_asset_inventory'])==3
for row in D['exact_module_source_inventory']:assert record(P/'apps/desktop'/row['path'])['sha256']==row['sha256']==record(S/'apps/desktop'/row['path'])['sha256']
for row in D['compiled_React_asset_inventory']:assert record(P/'apps/web/dist'/row['path'])['sha256']==row['sha256']
input_reports={};input_sets={}
for label,prefix,count in [('validator','',6444),('core','core-',6049)]:
 before=read(RAW/(prefix+'inputs.before.json'));after=read(RAW/(prefix+'inputs.after.json'));assert len(before)==count
 index={str(pathlib.Path(r['path']).resolve()).lower():r for r in before};assert len(index)==count
 for row in before:
  now=record(row['path']);assert now['sha256']==row['sha256'] and now['bytes']==row['bytes'],row['path']
 assert [{k:r[k] for k in ['path','sha256','bytes']} for r in after]==before and all(r['sha256']==r['current_sha256'] for r in after)
 digest=sha(json.dumps(before,sort_keys=True,separators=(',',':')).encode())
 assert digest==M['build']['input_digest' if label=='validator' else 'core_input_digest']
 input_reports[label]={'count':count,'digest':digest,'all_current_hashes_match':True,'before_after_consistent':True};input_sets[label]=index
assert input_reports['validator']['digest']==D['build_input_digest']==CMP['bound_full_input_digest']
# Independently decode concatenated go-list JSON and ensure every concrete source
# and embedded input belongs to the matching frozen inventory.
closure={}
for label,name in [('validator','go-list.stdout'),('core','core-go-list.stdout')]:
 text=(RAW/name).read_text(encoding='utf8');dec=json.JSONDecoder();offset=0;packages=[];paths=set();missing=[]
 while offset<len(text):
  while offset<len(text) and text[offset].isspace():offset+=1
  if offset==len(text):break
  obj,offset=dec.raw_decode(text,offset);packages.append(obj)
  for field in ['GoFiles','CompiledGoFiles','CgoFiles','CFiles','CXXFiles','HFiles','SFiles','SysoFiles','EmbedFiles']:
   for member in obj.get(field,[]):
    p=pathlib.Path(member);p=p if p.is_absolute() else pathlib.Path(obj['Dir'])/p
    if p.exists():
     norm=str(p.resolve()).lower();paths.add(norm)
     if norm not in input_sets[label]:missing.append({'package':obj.get('ImportPath'),'field':field,'path':str(p)})
 assert not missing,missing[:10]
 closure[label]={'packages':len(packages),'concrete_source_embed_paths':len(paths),'all_in_frozen_input_inventory':True}
versions=[]
for label,path in [('control','apps/desktop/resources/control/researchos-control.exe'),('runtime-verifier','apps/desktop/resources/control/runtime-verifier.exe'),('validator','apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')]:
 argv=[D['go_tool_ref']['path'],'version','-m',str(P/path)];p=subprocess.run(argv,cwd=E,capture_output=True);(E/(label+'-version-m.stdout.raw')).write_bytes(p.stdout);(E/(label+'-version-m.stderr.raw')).write_bytes(p.stderr)
 text=p.stdout.decode();assert p.returncode==0 and 'vcs.revision='+C in text and 'vcs.modified=false' in text
 if label=='validator':assert D['build_input_digest'] in text
 item={'argv':argv,'native_exit':p.returncode,'binary':record(P/path),'vcs_revision':C,'vcs_modified':False};save(label+'-version-m.process.json',item);versions.append(item)
assert D['binary_sha256']==record(P/'apps/desktop/resources/client-wire/researchos-client-wire-validator.exe')['sha256']
installer=read(P/'apps/desktop/resources/control/runtime-verifier-installation.json');verifier=P/'apps/desktop/resources/control/runtime-verifier.exe'
assert pathlib.Path(installer['executable']).is_absolute() and pathlib.Path(installer['executable']).resolve()==verifier.resolve()
assert installer['executable_hash']=='sha256:'+record(verifier)['sha256'] and installer['source_commit']==C and installer['arguments']==[]
for path,row in M['package']['mu_reuse'].items():assert row['source_commit']==MU and record(P/path)['sha256']==row['sha256']==record(OLD/path)['sha256']
mu=read(P/'apps/desktop/resources/control/runtime/mu-worker.mjs.build.json');assert mu['mu_commit']==MU
numbers=sorted(int(p.name[:4]) for p in (P/'migrations/sqlite').glob('*.sql') if re.match(r'^\d{4}_',p.name));assert numbers==list(range(1,25))
oldreview=ROOT/'execution/v2.4/receipts/W05/W05-99/qualification_status_desktop_package_review_codex/20261014-current-chat/FINAL-report.json'
if not oldreview.exists():oldreview=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/status-package-independent-review-20261014/FINAL-report.json')
assert record(oldreview)['sha256']=='063724b8449cb356ab62d0792b6b8b7e04e381e0b15a6ba3d82f385d51f4fe4b'
inv=read(RAW/'package-cases.invocation.json');log=pathlib.Path(inv['stdout']['path']).read_text(encoding='utf8');counts={k:int(v) for k,v in re.findall(r'^.*? (tests|pass|fail|cancelled|skipped|todo) (\d+)\s*$',log,re.M)}
assert inv['native_exit']==0 and counts=={'tests':214,'pass':214,'fail':0,'cancelled':0,'skipped':0,'todo':0}
failed=read(RAW/'validator-suite.invocation.json');corrected=read(RAW/'validator-suite-corrected.invocation.json');references(failed);references(corrected)
failure_raw=pathlib.Path(failed['stdout']['path']).read_text(encoding='utf8');corrected_raw=pathlib.Path(corrected['stdout']['path']).read_text(encoding='utf8')
assert failed['native_exit']==1 and corrected['native_exit']==0 and failed['actualargv']==corrected['actualargv']
assert '../../../tests/contracts/fixtures/client_protocol_v2_fixtures.json' in failure_raw and 'cannot find' in failure_raw
assert corrected['cwd']==str(S/'apps/desktop/validator') and re.findall(r'^--- PASS: (\S+)',corrected_raw,re.M) and '--- FAIL:' not in corrected_raw and corrected_raw.endswith('PASS\n')
summary={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'author_manifest':record(F/'FINAL-manifest.json'),'source':{'commit':C,'tree':TREE,'clean':True,'exact_changes':delta},'package_root':str(P),'package_member_count':58,'package_members':files,'component_counts':dict(collections.Counter(r['component'] for r in files)),'inputs':input_reports,'go_list_closure':closure,'reference_count':len(checked),'references':list(checked.values()),'reference_errors':errors,'build_invocations':invocations,'fresh_go_versions':versions,'module_count':14,'react_count':3,'installer':installer,'mu_commit':MU,'old_package_review':record(oldreview),'numbered_migrations':numbers,'author_package_test_counts':counts,'preserved_setup_failure':{'failed':record(RAW/'validator-suite.invocation.json'),'corrected':record(RAW/'validator-suite-corrected.invocation.json'),'native_exits':[1,0],'reason':'Same validator.test executable initially ran in source root and could not find relative fixture; corrected cwd apps/desktop/validator passed. Original failure retained.'},'limits':'No Desktop/Core/verifier activation; fresh validator synthetic execution only. Bound snapshots include tests/tools beyond production compile; go-list closure separately verified.'}
save('package-audit.json',summary)
print(json.dumps({'members':58,'inputs':input_reports,'closure':closure,'references':len(checked),'versions':3,'package_tests':counts}))
