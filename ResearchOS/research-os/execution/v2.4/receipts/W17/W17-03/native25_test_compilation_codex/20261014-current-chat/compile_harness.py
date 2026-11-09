"""Build the fixed, independently reviewed Native25 test binary; do not run it."""
import hashlib,json,subprocess,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
R=Path('D:/作品集/ResearchOS/research-os');B=R/'execution/v2.4/receipts/W05/W05-99';O=Path(__file__).parent
T=R/'.local/worktrees/schema24-to25-native-20261014';S=R/'.local/native25-test-compilation-20261014'
GO=R/'.local/tools/go1.27.1/go/bin/go.exe'
def pin(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value):
 p=O/name
 with p.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
 return pin(p)
def load(p,sha):
 assert pin(p)['sha256']==sha
 m=types.ModuleType('root_compile_'+p.stem);m.__file__=str(p);sys.modules[m.__name__]=m;exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);return m
def git(*args):return subprocess.check_output(['git',*args],cwd=T,text=True,encoding='utf8').strip()
assert git('rev-parse','HEAD')=='f80955594bdd0373ae1c961cd02ab6be96f2c196' and git('status','--porcelain')==''
review=R/'execution/v2.4/receipts/W17/W17-03/schema24_to25_independent_review_codex/20261014-current-chat/revision01/FINAL-report.json'
assert pin(review)['sha256']=='fa7c3041458c8c68968debbe8e5c6936f55c508a21c477c5eb54cf39f5b5b7d0'
assert pin(GO)['sha256']=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
gp=B/'source_read_guard_revision_v2_codex/d6d10c192b1940ed9c11a957411aecd9/source_read_guard.py'
hp=B/'integration_codex/independent-cli-list-scopes-r308/windows_owned_process.py'
guardmod=load(gp,'e75ae31b45cf9bbe82b3930173a068e66f012dfa0468a2ed36cfd9e359115b85')
helper=load(hp,'6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad')
S.mkdir(exist_ok=False)
for n in ['temp','profile','programs']:(S/n).mkdir()
env={'SystemRoot':'C:\\Windows','WINDIR':'C:\\Windows','ComSpec':'C:\\Windows\\System32\\cmd.exe','PATH':str(GO.parent)+';C:\\Windows\\System32;C:\\Program Files\\Git\\cmd','PATHEXT':'.COM;.EXE;.BAT;.CMD','USERPROFILE':str(S/'profile'),'LOCALAPPDATA':str(S/'profile'),'APPDATA':str(S/'profile'),'TEMP':str(S/'temp'),'TMP':str(S/'temp'),'GOROOT':str(GO.parent.parent),'GOPATH':str(R/'.local/tools/gopath'),'GOCACHE':str(R/'.local/go-cache/mu-m1-core-20261014'),'GOTMPDIR':str(S/'temp'),'GOENV':'off','GOTOOLCHAIN':'local','GOPROXY':'off','GOSUMDB':'off','GOWORK':'off','CGO_ENABLED':'0','GOFLAGS':'-mod=readonly -p=1','GOMAXPROCS':'2'}
invocations=[];guards=[];result_summary={'state':'IN_PROGRESS','native_harness_executed':False,'signatures_created':0,'product_db_writes':0,'formal_increment':0}
def acquire(label,refs):
 g=guardmod.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024);g.acquire(list({r['path'].casefold():r for r in refs}.values()));guards.append((label,g));return g
def invoke(label,argv,wall=300):
 out=O/(label+'.stdout.raw');err=O/(label+'.stderr.raw');result=None;error=None
 try:
  with out.open('xb') as stdout,err.open('xb') as stderr:result=helper.run_owned(argv,str(T),env,stdout,stderr,wall,creation_flags=0x08000000)
 except BaseException as exc:error=repr(exc)
 receipt=save(label+'.invocation.json',{'argv':argv,'cwd':str(T),'public_environment':env,'result':result,'exception':error,'actual_native_exit':result.get('actual_exit') if result else None,'stdout_ref':pin(out),'stderr_ref':pin(err),'external_model_provider_requests':0,'production_db_writes':0});invocations.append(receipt)
 assert error is None and result['actual_exit']==0 and result['error'] is None and not result['timed_out']
 j=result['job_cleanup'];assert not j['errors'] and j['active_processes_last_observed']==0 and all(j[k] for k in ['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed'])
 print(json.dumps({'stage':label,'actual_native_exit':result['actual_exit'],'receipt':receipt}),flush=True)
 return receipt
try:
 product={}
 roots=['apps/control','internal','adapters','evaluation','ops','migrations/sqlite','spec/v2.0/contracts']
 for rel in roots:
  root=T/rel;assert root.is_dir()
  for p in root.rglob('*'):
   assert not p.is_symlink()
   if p.is_file():product[str(p.resolve())]=pin(p)
 for rel in ['go.mod','go.sum','execution/toolchains/locked.json']:product[str((T/rel).resolve())]=pin(T/rel)
 runtime=[pin(p) for p in helper.runtime_resource_paths()]
 toolrefs=[pin(p) for p in (GO.parent.parent/'pkg/tool/windows_amd64').iterdir() if p.is_file()]
 acquire('product_and_runtime',[*product.values(),*runtime,*toolrefs,pin(GO),pin(GO.parent.parent/'VERSION'),pin(gp),pin(hp),pin(Path(__file__)),pin(review)])
 invoke('compiler-input-list',[str(GO),'list','-test','-deps','-compiled','-json','./internal/domain'])
 raw=(O/'compiler-input-list.stdout.raw').read_text(encoding='utf8');decoder=json.JSONDecoder();pos=0;packages=[];inputs={};embeds=[];modulefiles={}
 fields=['GoFiles','CgoFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles']
 while pos<len(raw):
  while pos<len(raw) and raw[pos].isspace():pos+=1
  if pos==len(raw):break
  pkg,pos=decoder.raw_decode(raw,pos);assert not pkg.get('Error') and not pkg.get('DepsErrors');packages.append(pkg.get('ImportPath'))
  if not pkg.get('Dir'):continue
  directory=Path(pkg['Dir'])
  for field in fields:
   for name in pkg.get(field,[]):
    p=Path(name);p=p if p.is_absolute() else directory/p;ref=pin(p);inputs[ref['path']]=ref
    if field.endswith('EmbedFiles'):embeds.append({'package':pkg['ImportPath'],'field':field,'ref':ref})
  mod=pkg.get('Module',{})
  for module in [mod,mod.get('Replace',{})]:
   if module.get('GoMod'):
    ref=pin(module['GoMod']);modulefiles[ref['path']]=ref
 inputs.update(modulefiles)
 inventory=save('actual-test-compiler-input-inventory.json',{'package_count':len(packages),'packages':packages,'build_input_count':len(inputs),'build_inputs':list(inputs.values()),'actual_embed_files':embeds,'product_inventory_count':len(product),'product_inventory':list(product.values()),'compiler_tool_refs':toolrefs,'GoRef':pin(GO),'selected_module_files_pinned':True,'module_files':list(modulefiles.values()),'includes_actual_test_and_embed_inputs':True,'build_tag':'','GOWORK':'off','CGO_ENABLED':'0','Main_adopted':False,'formal_acceptance':False})
 acquire('selected_compiler_inputs',[*inputs.values(),pin(O/'actual-test-compiler-input-inventory.json')])
 binary=S/'programs/native-pause-migration-harness.test.exe'
 invocation=invoke('test-binary-compile',[str(GO),'test','-c','-trimpath','-buildvcs=true','-o',str(binary),'./internal/domain'],600)
 assert git('rev-parse','HEAD')=='f80955594bdd0373ae1c961cd02ab6be96f2c196' and git('status','--porcelain')==''
 result_summary.update(state='FIXED_SOURCE_TEST_BINARY_BUILT_NATIVE_NOT_RUN',source_head=git('rev-parse','HEAD'),source_tree=git('rev-parse','HEAD^{tree}'),test_program_ref=pin(binary),compiler_inventory_ref=inventory,build_invocation_ref=invocation,runtime_resources=runtime,compiler_input_count=len(inputs),product_input_count=len(product),source_review_ref=pin(review))
except BaseException as exc:
 result_summary.update(state='FAILED_BUILD_NO_NATIVE_EXECUTION',error_type=type(exc).__name__,error=str(exc));raise
finally:
 cleanup=[]
 for name,g in reversed(guards):
  value=g.close();ref=save(name+'.guard-cleanup.json',value);cleanup.append({'name':name,'ref':ref,'closed':value['closed'],'errors':value['errors']})
 result_summary.update(invocations=invocations,cleanup=cleanup,all_guards_closed=all(x['closed'] and not x['errors'] for x in cleanup));save('compilation.closed.json',result_summary)
 print(json.dumps({'state':result_summary['state'],'all_guards_closed':result_summary['all_guards_closed']}),flush=True)
