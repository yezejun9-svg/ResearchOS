import sys
sys.dont_write_bytecode=True
import os,json,hashlib,datetime,types,traceback,re,sqlite3,base64
from pathlib import Path
from collections import Counter
if sys.flags.optimize:raise RuntimeError('Optimized mode forbidden')
R=Path(r'D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/codex-w0599-session-list-proof-r312'
OUT=Path(__file__).resolve().parent
WORK=W/'.local/closedcopy-907592b8'
NAMES=['NullContext','OwnedContext','ContextNotResultFilter','ExactReplayAfterCommit','ChangedPayloadConflict','ChangedSIDConflict','CrossProjectContext','ForeignPrincipalContext','ForeignPrincipalNullList','UnknownContext','ProjectGrantDenied','CrossProjectCursor','CrossPrincipalCursor','MalformedRequest']
SCOPE=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/session-list-closedcopy-exact1-r312/scope_registration.json'
HELPER=R/'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'
PLAN=R/'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json'
LOCK=R/'execution/toolchains/locked.json'
STATE={'phase':'PREPARE','guard':[],'results':[],'invocations':[]}
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def row(p):
 p=Path(p).absolute();return {'path':str(p),'resolved':str(p.resolve()),'sha256':digest(p),'bytes':p.stat().st_size}
def load(p):return json.loads(Path(p).read_bytes())
def save(n,v):
 p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return row(p)
def require(v,m):
 if not v:raise RuntimeError(m)
def vector(paths):return [row(p) for p in sorted(set(Path(p).absolute() for p in paths),key=str)]
def check(frozen,n):
 obs=[];errors=[]
 for e in frozen:
  try:
   a=row(e['path']);obs.append(a)
   if a!=e:errors.append({'before':e,'after':a})
  except Exception as x:errors.append({'before':e,'error':repr(x)})
 save(n,{'at':now(),'files':obs,'errors':errors});require(not errors,'Input drift: '+n)
def runtime_paths():
 # Pure URI conversion primes lazy imports before the first inventory.
 WORK.absolute().as_uri()
 paths={Path(x) for x in helper.runtime_resource_paths()}
 for module in list(sys.modules.values()):
  for attr in ['__file__','__cached__']:
   x=getattr(module,attr,None)
   if isinstance(x,str) and Path(x).is_file():paths.add(Path(x).absolute())
 return paths

def run(name,argv,cwd=W,timeout=600):
 STATE['phase']=name;d=OUT/'processes'/('%03d-'%len(STATE['invocations'])+name);d.mkdir(parents=True)
 result=None;err=None;inv={'name':name,'argv':[str(x) for x in argv],'cwd':str(cwd),'environment':ENV,'started_at':now()}
 try:
  with (d/'stdout.raw').open('xb') as so,(d/'stderr.raw').open('xb') as se:
   result=helper.run_owned(inv['argv'],str(cwd),ENV,so,se,timeout)
 except BaseException as x:err=repr(x)
 finally:
  inv.update(ended_at=now(),result=result,actual_exit=result.get('actual_exit') if result else None,wrapper_error=err)
  save(str((d/'invocation.json').relative_to(OUT)),inv);STATE['invocations'].append({'name':name,'ref':row(d/'invocation.json'),'actual_exit':inv['actual_exit']})
 c=result.get('job_cleanup',{}) if result else {}
 require(result is not None and err is None and result.get('error') is None and result.get('actual_exit')==0 and result.get('timed_out') is False and result.get('resumed') is True and all(c.get(k) is True for k in ['kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed']) and c.get('errors')==[], 'First unexpected owned process: '+name)
 return d

def stream_json(s):
 dec=json.JSONDecoder();out=[];s=s.lstrip()
 while s:
  obj,i=dec.raw_decode(s);out.append(obj);s=s[i:].lstrip()
 return out

def main():
 global helper,ENV
 require(digest(SCOPE)=='31b4e0abaea4355d908050859062206b1a1292407177462acc123313ef8b1f2c','Scope SHA')
 require(digest(HELPER)=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad','Helper SHA')
 require(digest(PLAN)=='598adac08e7c638bda6b783a78dc8541847b8e48054e196dd6da6eb728319bc2','Publicplan SHA')
 require(not WORK.exists(),'Work already exists; no automatic retry')
 WORK.mkdir();[(WORK/x).mkdir() for x in ['cache','gotmp','temp']]
 helper=types.ModuleType('owned_helper');helper.__file__=str(HELPER);exec(compile(HELPER.read_bytes(),str(HELPER),'exec'),helper.__dict__)
 tools=load(LOCK)['tools']
 for key in ['python','go','git']:require(digest(tools[key]['path'])==tools[key]['sha256'],'Locked '+key)
 require(Path(sys.executable).resolve()==Path(tools['python']['path']).resolve(),'Python identity')
 go=Path(tools['go']['path']);git=Path(tools['git']['path']);goroot=go.parent.parent
 ENV={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
 ENV.update(PATH=str(go.parent)+';'+str(git.parent)+';C:/Windows/System32',GOROOT=str(goroot),GOPATH=str(R/'.local/gopath'),GOMODCACHE=str(R/'.local/gopath/pkg/mod'),GOCACHE=str(WORK/'cache'),GOTMPDIR=str(WORK/'gotmp'),TEMP=str(WORK/'temp'),TMP=str(WORK/'temp'),GOTOOLCHAIN='local',GOENV='off',GOWORK='off',GOPROXY='off',GOSUMDB='off',CGO_ENABLED='0',GOOS='windows',GOARCH='amd64',GOAMD64='v1',GOEXPERIMENT='',GODEBUG='',GOFLAGS='-buildvcs=false -p=2',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,RESEARCHOS_GO=str(go),RESEARCHOS_SESSION_LIST_EVIDENCE=str(OUT/'cases'))
 assertions=OUT/'root_assertions.original.py';exec(compile(assertions.read_bytes(),str(assertions),'exec'),globals())
 save('authorized-inputs.json',{'scope':row(SCOPE),'helper':row(HELPER),'plan':row(PLAN),'driver':row(Path(__file__)),'unchanged_root_assertions':row(assertions),'cases':NAMES,'calls_maximum':224,'SDK_MODEL_Node_external_paid_private':0,'source_ready':False})
 head=run('git-head',[git,'rev-parse','HEAD'],timeout=60);require((head/'stdout.raw').read_text().strip()=='534857db99fa5e694987f877af74c322eaa2a0b3','Wrongbase')
 status=run('git-source-status',[git,'status','--porcelain=v1','--untracked-files=no'],timeout=60);require((status/'stdout.raw').read_text().strip()=='M internal/api/v2_sessions_test.go','Wrongdirtyscope')
 source=W/'internal/api/v2_sessions_test.go';domain=W/'internal/domain/client_protocol_sessions.go'
 require(digest(domain)=='7fb40c79ba73d4605431e6f8b5aec5730fc32de5b4a7e8537cdfc603b6862ce3','Protected domain')
 fmt=run('gofmt',[go.parent/'gofmt.exe','-w',source],timeout=60)
 original=(OUT/'source.before.go').read_bytes();after=source.read_bytes();marker=b'// Only the host binding port';n=14633
 require(hashlib.sha256(after[after.index(marker):after.index(marker)+n]).hexdigest()=='c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1','Protected originalbody')
 before_append=original.index(b'func (f *sessionListFixture) closeEvidence(');newappend=after.index(b'// readonlyCopyOpen is only')
 require(after[:newappend].replace(b'\t"net/url"\n',b'',1)==original[:before_append],'Outsideownedprefix')
 require(after[after.index(b'func TestSessionListHTTPOriginalContextIdentity'):]==original[original.index(b'func TestSessionListHTTPOriginalContextIdentity'):],'Original14bodychanged')
 save('source.freeze.json',{'test':row(source),'domain':row(domain),'originalbody_sha256':'c8451df67e00833e54d95219693301916f20a45dbda236196a14f9956c2688b1','outside_append_and_import_unchanged':True})
 tracked=run('git-input-list',[git,'ls-files','-z'],timeout=60);paths=set()
 for rel in (tracked/'stdout.raw').read_bytes().decode().split('\0'):
  if rel and (rel in ['go.mod','go.sum','VERSION','AGENTS.md','execution/project_identity.json'] or rel.startswith(('adapters/','internal/','migrations/','spec/','apps/','tests/','contracts/','bootstrap/','evaluation/','ops/'))):
   p=W/rel
   if p.is_file():paths.add(p)
 plan=load(PLAN);require(len(plan['git_resources'])==518,'Catalogcount')
 require(all((W/x['path']).is_file() for x in plan['git_resources']),'PubliccatalogmissingbeforeGo')
 for e in plan['external_tools_modules_stdlib']:
  p=Path(e['path']);require(p.is_file() and digest(p)==e['sha256'] and p.stat().st_size==e['bytes'],'Publicresourcepin '+str(p));paths.add(p)
 for directory in [goroot/'src',goroot/'pkg/tool',goroot/'lib']:paths.update(p for p in directory.rglob('*') if p.is_file())
 paths.update([Path(__file__),OUT/'launch.py',SCOPE,HELPER,PLAN,LOCK,assertions,OUT/'root_assertions.origin.json',source,domain,go,go.parent/'gofmt.exe',git,Path(sys.executable)])
 paths.update(runtime_paths());initial=vector(paths);STATE['guard']=initial;save('inputs.before_Go.json',initial)
 run('go-version',[go,'version'],timeout=60)
 listed=run('go-list',[go,'list','-deps','-test','-compiled','-json','./internal/api'])
 check(initial,'inputs.after_Go_list.json')
 generated=[]
 for p in stream_json((listed/'stdout.raw').read_text(encoding='utf-8')):
  require(not p.get('Error') and not p.get('DepsErrors'),'Grapherror')
  for field in ['GoFiles','CgoFiles','CompiledGoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','EmbedFiles','TestGoFiles','XTestGoFiles','TestEmbedFiles','XTestEmbedFiles']:
   for name in p.get(field,[]):
    file=Path(name);file=file if file.is_absolute() else Path(p['Dir'])/file
    if file.is_file():paths.add(file)
    else:require(field=='CompiledGoFiles' and file.resolve().is_relative_to(WORK.resolve()),'Missinggraphinput '+str(file));generated.append(str(file))
  if p.get('Module',{}).get('GoMod'):paths.add(Path(p['Module']['GoMod']))
 save('generated.advertised.json',generated);before=vector(paths);STATE['guard']=before;save('inputs.before_compile.json',before)
 exe=WORK/'session-list-closedcopy.test.exe';build=run('compile',[go,'test','-c','-work','-x','-o',exe,'./internal/api'])
 check(before,'inputs.after_compile.json');raw=(build/'stderr.raw').read_text(encoding='utf-8');ws=re.findall(r'^WORK=(.+)$',raw,re.M);require(len(ws)==1,'UniqueWORK');work=Path(ws[0].strip());require(work.resolve().is_relative_to((WORK/'gotmp').resolve()),'WORKoutsideowned')
 artifacts={p for p in work.rglob('*') if p.is_file()};archives=set();mains=[];gen=[]
 for p in sorted(artifacts):
  if p.suffix=='.go' or p.name.startswith('importcfg'):
   copy=OUT/'compiler-generated'/p.relative_to(work);copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(p.read_bytes());paths.add(copy);gen.append({'original':row(p),'copy':row(copy)})
   if p.name=='_testmain.go':mains.append(p)
   if p.name.startswith('importcfg'):
    for line in p.read_text().splitlines():
     if line.startswith('packagefile '):archives.add(Path(line.split('=',1)[1].replace('$WORK',str(work))))
 require(len(mains)==1 and 'TestSessionListHTTPOriginalContextIdentity' in mains[0].read_text(),'Missingtestmain')
 save('compiled.WORK.json',vector(artifacts));save('compiled.archives.json',vector(archives));save('compiled.generated.json',gen)
 run('exe-buildinfo',[go,'version','-m',exe],timeout=60)
 paths.update(artifacts);paths.update(archives);paths.add(exe);paths.update(runtime_paths());frozen=vector(paths);STATE['guard']=frozen;save('inputs.before_first_case.json',frozen);save('testexe.json',row(exe))
 print(json.dumps({'stage':'COMPILED','input_count':len(frozen),'exe':row(exe)},ensure_ascii=True),flush=True)
 total=0
 for i,name in enumerate(NAMES):
  check(frozen,'case-%02d.inputs.before.json'%i)
  proc=run('case-%02d-%s'%(i,name),[exe,'-test.run','^TestSessionListHTTPOriginalContextIdentity$/^'+name+'$','-test.v','-test.count=1','-test.failfast','-test.timeout=150s'],W/'internal/api',180)
  check(frozen,'case-%02d.inputs.after_native.json'%i)
  text=(proc/'stdout.raw').read_text(encoding='utf-8');require('--- FAIL:' not in text and '--- SKIP:' not in text,'FailorSkip');require(re.findall(r'^\s*--- PASS: (\S+/\S+)',text,re.M)==['TestSessionListHTTPOriginalContextIdentity/'+name],'Exactleaf')
  directory=OUT/'cases'/('TestSessionListHTTPOriginalContextIdentity__'+name)
  dbcheck=check_closed(directory);wirecheck=check_wire(directory,name)
  for f in ['closed-original.sidecars.json','closed-copy.before.sidecars.json','closed-copy.after.sidecars.json']:
   facts=load(directory/f);require(set(facts)=={'-wal','-shm'} and all(x['exists'] is False and x['error'] is None for x in facts.values()),'Sidecarsnotabsent '+f)
  require(load(directory/'closed-proof.json')['closed_copy_sidecars_absent'] is True,'Missingclosedsidecarproof')
  check(frozen,'case-%02d.inputs.after_proofs.json'%i)
  runtime=runtime_paths();frozenpaths={str(Path(x['path']).resolve()) for x in frozen};require(all(str(p.resolve()) in frozenpaths for p in runtime),'NewunboundPythonruntime')
  total+=wirecheck['HTTP_calls_including_setup'];require(total<=224,'HTTPcap')
  result={'name':name,'actual_native_exit':0,'process':row(proc/'invocation.json'),'DB':dbcheck,'wire':wirecheck,'status':'AUTHOR_EXECUTION_REPORTED_NOT_ACCEPTED'};save('case-%02d.result.json'%i,result);STATE['results'].append(result)
  print(json.dumps({'case':name,'PASS':True,'HTTP_total':total},ensure_ascii=True),flush=True)
 check(frozen,'inputs.after_all_cases.json');check(initial,'original_resources.final.json')
 save('execution_report.json',{'status':'AUTHOR_EXECUTION_REPORTED','cases':STATE['results'],'PASS_leaves':len(STATE['results']),'SKIP':0,'HTTP_total':total,'SDK_MODEL_Node_external_paid_private':0,'source_acceptance':False,'source_ready':False,'formal_increment':0,'original_closedcopy_failure_preserved':True,'input_count':len(frozen)})

if __name__=='__main__':
 with (OUT/'started.json').open('x',encoding='utf-8') as f:json.dump({'at':now(),'actor':'codex:/root/command_queue_impl'},f)
 try:main()
 except BaseException as x:
  save('failure_origin.json',{'actual_driver_exit':1,'actual_product_exit':'See specific invocation, never inferred','at':now(),'phase':STATE['phase'],'error':repr(x),'traceback':traceback.format_exc(),'invocations':STATE['invocations'],'completed':STATE['results'],'not_run':[x for x in NAMES if x not in [r['name'] for r in STATE['results']]],'automatic_retry':False,'counter_reset':False})
  if STATE['guard']:
   try:check(STATE['guard'],'inputs.after_failure.json')
   except BaseException as y:save('after_failure_check_error.json',{'error':repr(y)})
  print(traceback.format_exc(),flush=True);sys.exit(1)
