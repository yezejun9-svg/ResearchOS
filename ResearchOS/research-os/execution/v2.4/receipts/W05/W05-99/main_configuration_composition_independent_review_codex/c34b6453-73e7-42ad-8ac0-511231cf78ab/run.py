from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,stat,shutil,traceback
sys.stdout.reconfigure(encoding='utf-8');O=Path(__file__).resolve().parent;R=O.parents[6];G=R/'.local/tools/go1.27.1/go';B=R/'.local/w0599-main-stream-integration-r268/mu-worker.mjs';N=Path('C:/nvm4w/nodejs/node.exe');HEAD='1b3cda2ee974916f864b9a0af988076d01ca65bd'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
E={k:v for k,v in os.environ.items() if not k.startswith(('GIT_','RESEARCHOS_'))};E.update(GIT_NO_REPLACE_OBJECTS='1',GOROOT=str(G),GOENV='off',GOTOOLCHAIN='local',GOPATH=str(R/'.local/gopath'),GOCACHE=str(R/'.local/independent-configuration-cache-9673a59f'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_GO=str(G/'bin/go.exe'),RESEARCHOS_NODE=str(N),RESEARCHOS_MU_BUNDLE=str(B),RESEARCHOS_QUEUE_WORKER_BUNDLE=str(B),RESEARCHOS_STREAM_SDK_ROOT=str(R/'third_party/mu'),RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR=str(O/'actual-fixtures'))
old=R/'execution/v2.4/receipts/W05/W05-99/host_configuration_upgrade_executor_codex/old22-build-40e94f3f6e53442fa07068089c0de64a';E.update(RESEARCHOS_CONFIGURATION_OLD_CONTROL=str(old/'old22-control.exe'),RESEARCHOS_CONFIGURATION_OLD_ROOT=str(old/'frozen_source'),RESEARCHOS_CONFIGURATION_TARGET_PROGRAM=str(O/'programs/main-backup23.exe'))
def run(n,a,cwd=R,timeout=600):
 start=now()
 with (O/(n+'.stdout.raw')).open('xb') as out,(O/(n+'.stderr.raw')).open('xb') as err:
  p=subprocess.run(a,cwd=cwd,env=E,stdout=out,stderr=err,timeout=timeout)
 save(n+'.invocation.json',{'argv':a,'cwd':str(cwd),'started_at':start,'finished_at':now(),'exit':p.returncode,'stdout_sha256':sha(O/(n+'.stdout.raw')),'stderr_sha256':sha(O/(n+'.stderr.raw'))});print(n,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(n+' actualexit '+str(p.returncode))
def main():
 scope=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/configuration-main-scope-r282/scope_registration.json';assert sha(scope)=='2a0e849c2745a5515d1ac338c78a12435cb1473c0063536a22d371da70752a41';doc=json.loads(scope.read_text(encoding='utf-8-sig'));(O/'scope.original.json').write_bytes(scope.read_bytes());assert all(sha(R/x['path'])==x['sha256'] for x in doc['exact_source16']);assert sha(B)=='2a8e70132a914affc6122c1f1db29cfa315b655c93d4200145852ebbc853d441'
 run('head-before',['git','--no-replace-objects','rev-parse','HEAD']);assert (O/'head-before.stdout.raw').read_text().strip()==HEAD
 run('status-before',['git','status','--short','--untracked-files=no']);save('environment.json',{k:v for k,v in E.items() if k.startswith(('GO','RESEARCHOS_','GIT_'))})
 run('go-list',[str(G/'bin/go.exe'),'list','-deps','-test','-json','./internal/domain','./apps/cli','./internal/api','./internal/host','./apps/control','./ops/backup'])
 raw=(O/'go-list.stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();pkgs=[]
 while raw.strip():
  raw=raw.lstrip();p,end=dec.raw_decode(raw);pkgs.append(p);raw=raw[end:]
 files=set()
 for p in pkgs:
  if not p.get('Dir'):continue
  d=Path(p['Dir']);files.update(x for x in d.glob('*.go') if x.is_file())
  for k in ['EmbedFiles','TestEmbedFiles','XTestEmbedFiles','SFiles','HFiles','SysoFiles','CFiles','CXXFiles']:
   for name in p.get(k,[]):files.add(d/name)
  if p.get('Module',{}).get('GoMod'):files.add(Path(p['Module']['GoMod']))
 def runtime_inventory():
  paths=set()
  for folder in ['internal','adapters','apps','tests/runtime','migrations','spec/v2.0/contracts']:
   paths.update(p for p in (R/folder).rglob('*') if p.is_file() and p.suffix in ['.go','.mjs','.json','.sql'])
  for folder in ['internal','adapters','tests']:
   for d in (R/folder).rglob('testdata'):paths.update(p for p in d.rglob('*') if p.is_file())
  for folder in ['packages','node_modules']:paths.update(p for p in (R/'third_party/mu'/folder).rglob('*') if p.is_file() and '.git' not in p.parts)
  return paths
 files.update(runtime_inventory());inventory=sorted(str(p) for p in runtime_inventory());save('inventory.before.json',inventory)
 vendor=json.loads((R/'third_party/mu.MANIFEST.json').read_text(encoding='utf-8'));assert vendor['files']==len(vendor['entries'])==5083
 for name,x in vendor['entries'].items():
  p=R/name;s=p.lstat();assert stat.S_ISREG(s.st_mode) and not (getattr(s,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT);assert s.st_size==x['size'] and sha(p)==x['sha256'];files.add(p)
 for name in ['go.mod','go.sum','third_party/mu/package.json','third_party/mu/package-lock.json','third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json','execution/toolchains/locked.json','evaluation/development/jev-v2/dataset.json']:files.add(R/name)
 lock=json.loads((R/'execution/toolchains/locked.json').read_text(encoding='utf-8-sig'));git=Path(lock['tools']['git']['path']);assert sha(git)==lock['tools']['git']['sha256'];files.add(git);files.add(Path(shutil.which('git')))
 files.update([G/'bin/go.exe',N,B,Path(__file__),Path(sys.executable),O/'environment.json',O/'scope.original.json']);files.update(p for p in (G/'pkg/tool').rglob('*') if p.is_file())
 ps=Path(shutil.which('powershell.exe'));files.add(ps);files.update(p for p in ps.parent.glob('*.dll') if p.is_file())
 for name in ['csc.exe','csc.exe.config','Microsoft.CSharp.dll','mscorlib.dll','System.dll','System.Core.dll']:
  p=Path(E['SYSTEMROOT'])/'Microsoft.NET/Framework64/v4.0.30319'/name
  if p.is_file():files.add(p)
 assert sha(old/'old22-control.exe')=='0cba028c2f8222bef5000a292b1d52346eb534f026f0ee34b4bf55e8a6f033e6';files.add(old/'old22-control.exe');files.update(p for p in (old/'frozen_source').rglob('*') if p.is_file())
 files=sorted(files)
 def vector():return {str(p):sha(p) for p in files}
 before=vector();save('inputs.before.json',before);print('inputs frozen '+str(len(before)),flush=True);(O/'programs').mkdir()
 for name,package in [('main-control23','./apps/control'),('main-backup23','./ops/backup')]:run('build-'+name,[str(G/'bin/go.exe'),'build','-o',str(O/'programs'/(name+'.exe')),package])
 cohorts=[('domain','internal/domain','^Test(ClientQueueFreshNumberedSchema|ClientQueueHistorical22NumberedSchema|ClientQueueBackup|ConfigurationUpgrade|BackupHostConfiguration|ClientConfiguration|ClientCommandIdentity|QueueUpgrade)',300),('cli','apps/cli','.',480),('api','internal/api','.',300),('host','internal/host','^Test(W1802ProductionBackupCLIWorkspaceContinuation|NativePublishedBootstrapRebindsAndRenews|NativeWorkspaceChooseNeedsConfirmedHostSelection|NativeWindowsFolderChooserAPIsPresent|NativePipePublishedBootstrap|W03NativeHostUsesCurrentMuContracts)$',300)]
 for name,pkg,selector,timeout in cohorts:run('compile-'+name,[str(G/'bin/go.exe'),'test','-c','-o',str(O/'programs'/(name+'.test.exe')),'./'+pkg])
 aftercompile=vector();save('inputs.after_compile.json',aftercompile);assert before==aftercompile
 files+=list((O/'programs').glob('*.exe'));frozen=vector();save('test_inputs.before.json',frozen);save('programs.freeze.json',[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in (O/'programs').glob('*.exe')]);outcomes=[]
 for name,pkg,selector,timeout in cohorts:
  run('test-'+name,[str(G/'bin/go.exe'),'tool','test2json','-t','-p','researchos.local/research-os/'+pkg,str(O/'programs'/(name+'.test.exe')),'-test.v=test2json','-test.run='+selector,'-test.failfast','-test.timeout='+str(timeout)+'s'],R/pkg,timeout+120)
  count={'pass':0,'fail':0,'skip':0,'top_pass':0}
  for line in (O/('test-'+name+'.stdout.raw')).read_text(encoding='utf-8').splitlines():
   x=json.loads(line)
   if x.get('Test') and x.get('Action') in count:
    count[x['Action']]+=1
    if x['Action']=='pass' and '/' not in x['Test']:count['top_pass']+=1
  save('test-'+name+'.counts.json',count);assert count['pass']>0 and count['skip']==0;outcomes.append({'cohort':name,'counts':count});print(name+' counts '+json.dumps(count),flush=True)
  after=vector();save('inputs.after-'+name+'.json',after);assert frozen==after
 end=vector();save('inputs.current.json',end);assert frozen==end;invafter=sorted(str(p) for p in runtime_inventory());save('inventory.after.json',invafter);assert inventory==invafter
 run('head-after',['git','--no-replace-objects','rev-parse','HEAD']);run('status-after',['git','status','--short','--untracked-files=no']);save('result.json',{'status':'CURRENT_MAIN_SCOPED_COMPOSITION_PASS_NOT_FORMAL','head':HEAD,'before_inputs':len(before),'test_inputs':len(frozen),'stable':True,'sdk_files':5083,'bundle_sha256':sha(B),'tests':outcomes,'actual_provider_models':0,'paid':0,'provider_held_runs':0,'formal_increment':0})
try:main()
except Exception:
 save('failure.json',{'time':now(),'traceback':traceback.format_exc(),'stopped_no_retry':True});raise
