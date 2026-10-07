"""Independent current MAIN composition. Run only after Root gives final HEAD/bundle."""
from pathlib import Path
import os,sys,json,hashlib,datetime,subprocess,re,stat
sys.stdout.reconfigure(encoding='utf-8')
O=Path(__file__).resolve().parent;R=O.parents[6]
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(n,x):
 with (O/n).open('x',encoding='utf-8')as f:json.dump(x,f,ensure_ascii=False,indent=2)
def require(x,message):
 if not x:raise RuntimeError(message)
def run(name,argv,env):
 start=now()
 with (O/(name+'.stdout.raw')).open('xb')as out,(O/(name+'.stderr.raw')).open('xb')as err:x=subprocess.run(argv,cwd=R,env=env,stdout=out,stderr=err)
 write(name+'.invocation.json',{'argv':argv,'cwd':str(R),'started_at':start,'ended_at':now(),'exit':x.returncode,'stdout_sha256':sha(O/(name+'.stdout.raw')),'stderr_sha256':sha(O/(name+'.stderr.raw'))});print(name,x.returncode,flush=True);return x.returncode

def main():
 require(len(sys.argv)==4,'Require actual Root final HEAD, current rebuilt bundle path, bundle SHA')
 expected_head,root_bundle,bundle_sha=sys.argv[1:];root_bundle=Path(root_bundle);require(root_bundle.is_file()and sha(root_bundle)==bundle_sha,'Root bundle bytes mismatch')
 env={k:v for k,v in os.environ.items()if not k.startswith('GIT_')};env['GIT_NO_REPLACE_OBJECTS']='1'
 go=R/'.local/tools/go1.27.1/go';node=Path('C:/nvm4w/nodejs/node.exe');bundle=R/'.local/independent-main-stream'/O.name/'mu-worker.mjs'
 env.update(GOROOT=str(go),GOTOOLCHAIN='local',GOENV='off',GOPATH=str(R/'.local/gopath'),GOCACHE=str(R/'.local/gocache'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_GO=str(go/'bin/go.exe'),RESEARCHOS_NODE=str(node),RESEARCHOS_MU_BUNDLE=str(bundle),RESEARCHOS_QUEUE_WORKER_BUNDLE=str(bundle),RESEARCHOS_STREAM_SDK_ROOT=str(R/'third_party/mu'),RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR=str(O/'actual-fixtures'))
 write('execution_input.json',{'expected_main_head':expected_head,'root_bundle':str(root_bundle),'root_bundle_sha256':bundle_sha,'mode':'PUBLIC_SYNTHETIC_FIXTURES_NO_PROVIDER_QUALIFICATION','run_at':now()})
 require(run('head-before',['git','--no-replace-objects','rev-parse','HEAD'],env)==0,'head command failed');require((O/'head-before.stdout.raw').read_text().strip()==expected_head,'MAIN changed before freeze')
 sources=json.loads((O/'expected_sources.json').read_text(encoding='utf-8'))
 require(all(sha(R/x['path'])==x['sha256']for x in sources['files']),'MAIN differs from independently reviewed20 sources')
 write('environment.json',{k:env[k]for k in ['GOROOT','GOTOOLCHAIN','GOENV','GOPATH','GOCACHE','GOPROXY','GOSUMDB','RESEARCHOS_GO','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE','RESEARCHOS_QUEUE_WORKER_BUNDLE','RESEARCHOS_STREAM_SDK_ROOT','RESEARCHOS_MODEL_STREAM_EVIDENCE_DIR']})
 require(run('go-list-before',[str(go/'bin/go.exe'),'list','-deps','-test','-json','./adapters/runtime','./internal/domain','./apps/cli','./tests/runtime/cli_contract'],env)==0,'go-list failed')
 raw=(O/'go-list-before.stdout.raw').read_text(encoding='utf-8');dec=json.JSONDecoder();packages=[]
 while raw.strip():
  raw=raw.lstrip();p,end=dec.raw_decode(raw);packages.append(p);raw=raw[end:]
 paths=set()
 for p in packages:
  if not p.get('Dir'):continue
  d=Path(p['Dir']);paths.update(x for x in d.glob('*.go')if x.is_file())
  for key in ['EmbedFiles','TestEmbedFiles','XTestEmbedFiles','SFiles','HFiles','SysoFiles','CFiles','CXXFiles']:
   for name in p.get(key,[]):
    q=d/name;require(q.is_file(),'compiler input missing '+str(q));paths.add(q)
  if p.get('Module',{}).get('GoMod'):paths.add(Path(p['Module']['GoMod']))
 for folder in ['internal','adapters','apps','tests/runtime','migrations','spec/v2.0/contracts']:
  paths.update(p for p in (R/folder).rglob('*')if p.is_file()and p.suffix in ['.go','.mjs','.json','.sql'])
 for folder in ['internal','adapters','tests']:
  for d in (R/folder).rglob('testdata'):paths.update(p for p in d.rglob('*')if p.is_file())
 vendor=json.loads((R/'third_party/mu.MANIFEST.json').read_text(encoding='utf-8'));require(vendor['files']==len(vendor['entries'])==5083,'fixed vendor count drift')
 for name,expect in vendor['entries'].items():
  q=R/name;info=q.lstat();require(stat.S_ISREG(info.st_mode)and not(getattr(info,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT),'vendor type drift');require(info.st_size==expect['size']and sha(q)==expect['sha256'],'vendor bytes drift '+name);paths.add(q)
 for folder in ['packages','node_modules']:paths.update(p for p in (R/'third_party/mu'/folder).rglob('*')if p.is_file()and '.git'not in p.parts)
 for n in ['go.mod','go.sum','third_party/mu/package.json','third_party/mu/package-lock.json','third_party/mu.MANIFEST.json','third_party/VENDORED_FROM.md','execution/v2.4/component_lock.json']:paths.add(R/n)
 paths.update([go/'bin/go.exe',node,root_bundle,Path(__file__),O/'expected_sources.json']);paths.update(p for p in (go/'pkg/tool').rglob('*')if p.is_file())
 receipt=R/'execution/v2.4/receipts/W05/W05-99/model_stream_executor_codex'
 for n in ['test-53a6e07436494837878a09393994fdce/failed-fixture.sqlite','test-f4a65b87734641c8a39d7060dd8b24fb/actual-fixtures/TestCLIModelStreamInterruptedPrefix/fixture.sqlite','test-18872d343fdd4a5fa788669ec6516cd9/actual-fixtures/actual-consumption-snapshot.json']:paths.add(receipt/n)
 paths=sorted(paths)
 def vector():return {('repo:'+p.relative_to(R).as_posix()if p.is_relative_to(R)else'absolute:'+p.as_posix()):sha(p) for p in paths}
 def inventory():
  names=set()
  for folder in ['internal','adapters','apps','tests/runtime','migrations','spec/v2.0/contracts']:
   names.update(str(p)for p in (R/folder).rglob('*')if p.is_file()and p.suffix in ['.go','.mjs','.json','.sql'])
  for p in packages:
   if p.get('Dir'):names.update(str(x)for x in Path(p['Dir']).glob('*.go')if x.is_file())
  for folder in ['packages','node_modules']:names.update(str(p)for p in (R/'third_party/mu'/folder).rglob('*')if p.is_file()and '.git'not in p.parts)
  return sorted(names)
 inventory_before=inventory();write('source_inventory_before.json',inventory_before)
 before=vector();write('source_before.json',before)
 require(run('actual-build',[str(node),'adapters/runtime/mu/build.mjs',str(bundle)],env)==0,'actual fixed vendor build failed')
 require(sha(bundle)==bundle_sha,'independently rebuilt MAIN bundle differs from Root supplied bundle')
 buildmeta=json.loads(Path(str(bundle)+'.build.json').read_text(encoding='utf-8'));write('actual-build-metadata.json',buildmeta);require(buildmeta['vendored_files_verified']==5083,'builder incomplete')
 paths.extend([bundle,Path(str(bundle)+'.build.json')]);test_before=vector();write('test_inputs_before.json',test_before)
 cmds=[('sdk',[str(node),'--test','--test-reporter=tap','adapters/runtime/mu/worker-stream.test.mjs','adapters/runtime/mu/worker-control.test.mjs']),('core',[str(go/'bin/go.exe'),'test','-count=1','-v','-timeout','480s','-run','^(TestModelStream|TestClient|TestRuntime(ClientQueue|Mu|Model|CoordinatorCheckpoint)|TestMu|TestBackupQueue|TestW18|TestW14Session)','./adapters/runtime','./internal/domain']),('cli',[str(go/'bin/go.exe'),'test','-count=1','-v','-timeout','480s','./apps/cli'])]
 outcomes=[]
 for name,argv in cmds:
  code=run(name,argv,env);text=(O/(name+'.stdout.raw')).read_text(encoding='utf-8');counts={k:len(re.findall(r'^\s*--- '+k+r':',text,re.M))for k in ['PASS','FAIL','SKIP']}if name!='sdk'else {k:int(re.search(r'^# '+k+r' (\d+)',text,re.M).group(1))for k in ['pass','fail','skipped']};outcomes.append({'name':name,'exit':code,'counts':counts})
 inventory_after=inventory();write('source_inventory_after.json',inventory_after)
 after=vector();write('source_after.json',after);run('head-after',['git','--no-replace-objects','rev-parse','HEAD'],env);run('status-after',['git','status','--short','--untracked-files=no'],env)
 result={'mode':'CURRENT_MAIN_FIXTURE_COMPOSITION_NOT_LIVE_NOT_FORMAL','expected_main_head':expected_head,'source_input_count':len(before),'test_input_count':len(test_before),'test_source_drift':test_before!=after,'source_inventory_drift':inventory_before!=inventory_after,'prebuild_source_drift':any(after.get(k)!=v for k,v in before.items()),'final_head_matches':(O/'head-after.stdout.raw').read_text().strip()==expected_head,'bundle_sha256':sha(bundle),'tests':outcomes}
 write('result.json',result);require(not result['source_inventory_drift']and not result['test_source_drift']and not result['prebuild_source_drift']and result['final_head_matches'],'composition changed');require(all(x['exit']==0 for x in outcomes),'actual test failure');require(all(x['counts'].get('PASS',x['counts'].get('pass',0))>0 and x['counts'].get('SKIP',x['counts'].get('skipped',0))==0 for x in outcomes),'empty or skipped cohort');print(json.dumps(result),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  import traceback
  write('failure.json',{'when':now(),'traceback':traceback.format_exc(),'no_retry':True});raise
