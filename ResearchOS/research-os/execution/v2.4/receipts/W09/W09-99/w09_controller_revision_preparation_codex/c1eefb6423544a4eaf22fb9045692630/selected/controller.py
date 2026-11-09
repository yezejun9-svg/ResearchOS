"""W09 finite PREPARATION template. Requires a later sealed Root grant.
No import runs product/native/SQL. Parent source cd0 remains immutable.
"""
import sys
sys.dont_write_bytecode=True
import argparse, hashlib, io, json, os, re, tarfile, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from controller_common import *

def json_stream(raw):
 text=raw.decode('utf-8','strict');dec=json.JSONDecoder();pos=0;result=[]
 while pos<len(text):
  while pos<len(text) and text[pos].isspace():pos+=1
  if pos==len(text):break
  obj,end=dec.raw_decode(text,pos);result.append(obj);pos=end
  if len(result)>4096:raise Stop('Go package graph bound')
 return result

def test_facts(raw,selected,expected):
 text=raw.decode('utf-8','strict');runs=re.findall(r'^=== RUN\s+([^\s]+)',text,re.M)
 ends=re.findall(r'^\s*--- (PASS|FAIL|SKIP): ([^\s]+) \([^\n]+\)$',text,re.M)
 passed=[name for status,name in ends if status=='PASS']
 bad=[{'status':status,'test':name} for status,name in ends if status!='PASS']
 ancestry=['/'.join(selected.split('/')[:i]) for i in range(1,len(selected.split('/')))]
 if selected not in runs or selected not in passed or bad:raise Stop('Selected actual test did not PASS without skip/failure')
 if runs!=expected['run_records'] or passed!=expected['pass_records']:raise Stop('Frozen expanded event inventory differs')
 leaves=[name for name in runs if not any(other.startswith(name+'/') for other in runs)]
 if leaves!=expected['leaf_records']:raise Stop('Frozen leaf inventory differs')
 if len(set(runs))!=len(runs) or len(set(passed))!=len(passed) or not re.search(r'^PASS\r?$',text,re.M):raise Stop('Duplicate events or missing process PASS')
 return {'selected':selected,'actual_run_records':runs,'actual_pass_records':passed,'actual_leaf_records':leaves,'skip_fail':bad,'scenario_rows_qualified':1,'parents_not_counted_as_separate_scenarios':ancestry}

class Controller:
 def __init__(self,g,s,out):
  self.g,self.s,self.out=g,s,out;self.serial=0;self.tests=0;self.ledger=Ledger(out/'vectors')
  self.normal=trusted_module(g['normal_helper_ref']['path'],g['normal_helper_ref'])
  self.debug=trusted_module(g['debug_helper_ref']['path'],g['debug_helper_ref'])
  self.environment={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
  for var in ('GOCACHE','GOTMPDIR','GOPATH'):(out/var.lower()).mkdir()
  self.goroot=no_alias(g['goroot']);self.modcache=no_alias(g['module_cache'])
  (out/'testtmp').mkdir()
  self.environment.update(TMP=str(out/'testtmp'),TEMP=str(out/'testtmp'),PATH=str(Path(g['tools']['cmd']['path']).parent),GOROOT=str(self.goroot),GOTOOLCHAIN='local',GOENV='off',GOWORK='off',GOPROXY='off',GOSUMDB='off',CGO_ENABLED='0',GOFLAGS='-mod=readonly -buildvcs=false -p=1',GOCACHE=str(out/'gocache'),GOTMPDIR=str(out/'gotmpdir'),GOPATH=str(out/'gopath'),GOMODCACHE=str(self.modcache),GOMAXPROCS='2')
  self.tree=out/'source';self.tool_images=[g['tools']['go']]+g['go_tool_images']
  self.ledger.add([r['path'] for r in g['resource_files']],'root-pinned-public-resource-universe')
  self.ledger.add([r['path'] for r in g['controller_refs']]+[r['path'] for r in g['_authorization_input_refs']],'controller-spec-actual-authority')
  write_json(out/'runtime.before.json',runtime_snapshot(self.debug,g['resource_files']))
 def run(self,label,argv,cwd,timeout,process_cap,images,env=None):
  self.serial+=1
  if self.serial>128:raise Stop('Total native invocation cap')
  self.ledger.check('%03d-%s-before'%(self.serial,label))
  d=self.out/'native'/('%03d-%s'%(self.serial,label));d.mkdir(parents=True)
  started=time.time();result=None
  try:
   primary=file_ref(argv[0]);pins=[{'path':r['path'],'sha256':r['sha256'],'bytes':r['bytes']} for r in images]
   if label.startswith('case-'):
    worker=self.s['case_worker_ref'];python=self.g['tools']['python']
    request=write_json(d/'case-request.json',{'schema':'researchos.w09.owned-case-request.v1','authorized_by_controller':True,'root_grant_ref':self.g['_grant_ref'],'spec_ref':self.g['spec_ref'],'source_commit':CANDIDATE,'self_ref':worker,'python_ref':python,'debug_helper_ref':self.g['debug_helper_ref'],'argv':argv,'cwd':str(cwd),'env':env,'output_dir':str(d),'timeout':120,'process_cap':process_cap,'images':pins,'allowed_module_files':[r['ref'] for r in self.ledger.rows.values()],'expected_image':{'sha256':primary['sha256'],'bytes':primary['bytes']}})
    wrapperargv=[python['path'],*FLAGS,worker['path'],'--request',request['path'],'--sha256',request['sha256']]
    with (d/'wrapper.stdout.raw').open('xb') as so,(d/'wrapper.stderr.raw').open('xb') as se:
     wrapper=self.normal.run_owned(wrapperargv,str(PREP),self.environment,so,se,150)
    write_json(d/'wrapper.json',{'actualargv':wrapperargv,'cwd':str(PREP),'owned_result':wrapper,'request_ref':request,'stdout_ref':file_ref(d/'wrapper.stdout.raw'),'stderr_ref':file_ref(d/'wrapper.stderr.raw')})
    require_job(wrapper)
    result=raw_json((d/'case-owned.json').read_bytes())
   else:
    with (d/'stdout.raw').open('xb') as so,(d/'stderr.raw').open('xb') as se:
     result=self.debug.run_owned(argv,str(cwd),self.environment if env is None else env,so,se,timeout,{'sha256':primary['sha256'],'bytes':primary['bytes']},pins,[r['ref'] for r in self.ledger.rows.values()],process_cap,creation_flags=0x08000000)
   rawlimit=512*1024*1024 if label=='git-export' else 64*1024*1024
   if any((d/name).stat().st_size>rawlimit for name in ['stdout.raw','stderr.raw']):raise Stop('Native raw bound exceeded')
   invocation={'actualargv':argv,'cwd':str(cwd),'environment':self.environment if env is None else env,'started_at_unix':started,'ended_at_unix':time.time(),'actual_native_exit':None if result is None else result.get('actual_exit'),'owned_result':result,'stdout_ref':file_ref(d/'stdout.raw'),'stderr_ref':file_ref(d/'stderr.raw')}
   write_json(d/'invocation.json',invocation)
   require_job(result,True)
   module_paths=[]
   for item in result['debug_capture']['modules']:
    p=item['path_from_actual_file_handle']
    slash=chr(92)
    if p.startswith(slash*2+'?'+slash+'UNC'+slash):p=slash*2+p[8:]
    elif p.startswith(slash*2+'?'+slash):p=p[4:]
    pin=file_ref(p)
    if pin['sha256']!=item['before']['sha256'] or pin['bytes']!=item['before']['bytes'] or item['before']!=item['after']:raise Stop('Actual module differs from held file')
    module_paths.append(p)
   self.ledger.add(module_paths,'actual-loaded-images-'+label)
   return d,result
  finally:self.ledger.check('%03d-%s-after'%(self.serial,label))
 def export_source(self):
  git=self.g['tools']['git'];root=no_alias(self.g['repository'])
  d,_=self.run('git-parent',[git['path'],'rev-parse',CANDIDATE+'^'],root,30,4,[git])
  if (d/'stdout.raw').read_text(encoding='ascii').strip()!=BASE:raise Stop('Candidate parent differs')
  d,_=self.run('git-four-diff',[git['path'],'diff-tree','--no-commit-id','--name-only','-r',CANDIDATE],root,30,4,[git])
  if set((d/'stdout.raw').read_text(encoding='utf-8').splitlines())!=set(self.s['exact4_paths']):raise Stop('Candidate not exact4')
  include=['internal','adapters','migrations','spec','go.mod','go.sum']
  d,_=self.run('git-export',[git['path'],'archive','--format=tar',CANDIDATE,*include],root,90,4,[git])
  tar=d/'stdout.raw'
  if tar.stat().st_size>512*1024*1024:raise Stop('Git export bound')
  self.tree.mkdir();members=[]
  with tarfile.open(tar,'r:') as archive:
   for member in archive:
    parts=Path(member.name).parts
    if Path(member.name).is_absolute() or '..' in parts or any(':' in p or p.rstrip(' .')!=p for p in parts):raise Stop('Unsafe archive path')
    target=self.tree.joinpath(*parts)
    if not target.is_relative_to(self.tree):raise Stop('Archive escape')
    if member.isdir():target.mkdir(parents=True,exist_ok=True);continue
    if not member.isfile() or member.size>64*1024*1024 or len(members)>=100000:raise Stop('Nonregular/oversized export')
    body=archive.extractfile(member).read();members.append(write_bytes(target,body))
  for pin in self.s['exact4_pins']:
   if file_ref(self.tree/pin['path'])['sha256']!=pin['sha256']:raise Stop('Exported candidate test mismatch')
  write_json(self.out/'source-export.json',{'candidate':CANDIDATE,'architecture_base':BASE,'tar_ref':file_ref(tar),'paths':include,'files':members,'not_combined_Main':True})
  self.ledger.add([r['path'] for r in members],'fixed-Git-export')
 def build(self):
  go=self.g['tools']['go']['path'];self.ledger.check('pre-build-complete')
  d,_=self.run('go-version',[go,'version'],self.tree,30,1,self.tool_images)
  if (d/'stdout.raw').read_text(encoding='utf-8').strip()!='go version go1.27.1 windows/amd64':raise Stop('Go version')
  d,_=self.run('go-env',[go,'env','-json','GOROOT','GOVERSION','GOENV','GOTOOLCHAIN','GOMOD','GOMODCACHE','GOCACHE','GOTMPDIR','CGO_ENABLED','GOWORK'],self.tree,30,1,self.tool_images)
  actual=raw_json((d/'stdout.raw').read_bytes())
  for key in ['GOROOT','GOENV','GOTOOLCHAIN','GOMODCACHE','GOCACHE','GOTMPDIR','CGO_ENABLED','GOWORK']:
   if actual.get(key)!=self.environment[key]:raise Stop('Go actual env mismatch '+key)
  if no_alias(actual['GOMOD'])!=self.tree/'go.mod':raise Stop('Go module outside fixed export')
  self.executables={}
  for label,pkg in [('domain','./internal/domain'),('adapter','./adapters/retrieval')]:
   d,_=self.run('list-'+label,[go,'list','-deps','-test','-compiled','-json','-mod=readonly','-work','-x',pkg],self.tree,180,2048,self.tool_images)
   graph=json_stream((d/'stdout.raw').read_bytes());discovered=[]
   for package in graph:
    if package.get('Error') or package.get('DepsErrors') or package.get('Incomplete'):raise Stop('Incomplete package graph')
    if not package.get('Dir'):continue
    directory=no_alias(package['Dir'])
    if directory.is_relative_to(self.tree):discovered.extend(directory.glob('*.go'))
    for key in ['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles']:
     for name in package.get(key,[]):
      p=Path(name);p=p if p.is_absolute() else directory/p
      if not any(p.is_relative_to(root) for root in [self.tree,self.modcache,self.goroot,self.out/'gotmpdir',self.out/'gocache']):raise Stop('Go package input outside closed resource roots')
      if p.exists():discovered.append(p)
      else:raise Stop('Listed package input absent '+str(p))
    if package.get('Module',{}).get('GoMod'):discovered.append(Path(package['Module']['GoMod']))
   stable=[]
   for path in discovered:
    path=no_alias(path)
    if path.is_relative_to(self.out/'gotmpdir') or path.is_relative_to(self.out/'gocache'):continue
    if str(path).casefold() not in self.ledger.rows:raise Stop('Unbound actual Go input '+str(path))
    stable.append(path)
   self.ledger.add(stable,'actual-go-list-'+label)
   write_json(self.out/('graph-'+label+'.json'),graph)
   exe=self.out/(label+'.test.exe')
   self.run('compile-'+label,[go,'test','-c','-p=1','-mod=readonly','-work','-x','-o',str(exe),pkg],self.tree,600,2048,self.tool_images)
   self.executables[label]=file_ref(exe)
   self.ledger.add([exe],'compiled-test-image-'+label)
   self.run('buildinfo-'+label,[go,'version','-m',str(exe)],self.tree,30,1,self.tool_images)
  # All generated WORK, importcfg, archives and cache bytes become immutable after the last compile.
  generated=walk_files(self.out/'gotmpdir')+walk_files(self.out/'gocache')+[Path(x['path']) for x in self.executables.values()]
  self.ledger.add(generated,'final-WORK-generated-importcfg-archives-exes')
  write_json(self.out/'compiled-executables.json',self.executables)
  write_json(self.out/'compiled-inputs.frozen.json',self.ledger.export())
  self.ledger.check('compile-complete')
 def check_membership(self):
  for root in [self.tree,self.goroot,self.modcache,self.out/'gotmpdir',self.out/'gocache']:
   current={str(x).casefold() for x in walk_files(root)}
   frozen={k for k,v in self.ledger.rows.items() if Path(v['ref']['path']).is_relative_to(root)}
   if current!=frozen:raise Stop('Frozen directory membership differs '+str(root))
 def resources(self):
  self.resource={'symlink':'HOLD_NOT_GRANTED','junction':'HOLD_NOT_GRANTED'}
  self.link=None
  if self.g['resources']['symlink'] is True:
   root=self.out/'symlink-prerequisite';root.mkdir();a=root/'A';b=root/'B';a.mkdir();b.mkdir()
   try:
    os.symlink(str(b),str(a/'outside'),target_is_directory=True)
    s=(a/'outside').lstat()
    if not stat.S_ISLNK(s.st_mode):raise Stop('Actual symlink branch mode mismatch')
    self.resource['symlink']='AVAILABLE'
   except OSError as e:
    write_json(root/'failure.json',{'actual_native_exit':None,'exception_type':type(e).__name__,'message':str(e),'qualification':'STOP_UNEXPECTED_RESOURCE_FAILURE'})
    raise
  if self.g['resources']['junction'] is True:
   root=self.out/'junction-resource';root.mkdir();a=root/'A';b=root/'B';a.mkdir();b.mkdir()
   for p in [a/'same.txt',b/'same.txt']:write_bytes(p,b'owned-public-marker')
   link=a/'outside'
   if any(c in str(root) for c in '"%&|<>^!\r\n'):raise Stop('Unsafe cmd resource path')
   cmd=self.g['tools']['cmd'];command='mklink /J "'+str(link)+'" "'+str(b)+'"'
   d,result=self.run('junction-resource',[cmd['path'],'/D','/V:OFF','/S','/C',command],root,15,1,[cmd])
   s=link.lstat()
   if not getattr(s,'st_file_attributes',0)&0x400 or link.resolve()!=b.resolve():raise Stop('Wrong actual junction/target')
   self.resource['junction']='AVAILABLE';self.link=root
  write_json(self.out/'resource-status.json',self.resource)
 def cases(self):
  result=[]
  for row in self.s['roster']:
   label=row['id'];selected=row['selector'];required=row['requires_resource']
   if required and any(self.resource[k]!='AVAILABLE' for k in required):
    result.append({'id':label,'selector':selected,'state':'NOT_RUN_RESOURCE_HOLD','requirements':required,'actual_native_exit':None});continue
   self.check_membership()
   self.tests+=1
   if self.tests>49:raise Stop('Test invocation budget')
   package='adapter' if row['file'].startswith('adapters/') else 'domain'
   cwd=self.tree/('adapters/retrieval' if package=='adapter' else 'internal/domain')
   casedir=self.out/'cases'/label;casedir.mkdir(parents=True)
   evidence=casedir/'evidence';evidence.mkdir()
   env=dict(self.environment);env['RESEARCHOS_W09_CAUSAL_EVIDENCE']=str(evidence)
   if self.link:env['RESEARCHOS_W09_CAUSAL_LINK_RESOURCE']=str(self.link)
   images=[self.executables[package]]
   if not row['new'] and required and 'junction' in required:images.append(self.g['tools']['cmd'])
   d,owned=self.run('case-'+label,[self.executables[package]['path'],'-test.run',row['test_run'],'-test.v','-test.count=1','-test.failfast','-test.timeout=120s'],cwd,150,2 if not row['new'] and required else 1,images,env)
   self.check_membership()
   facts=test_facts((d/'stdout.raw').read_bytes(),selected,row['expected_records'])
   dbproofs=[]
   if row['new'] and package=='domain':
    case=evidence/selected.replace('/','__');db=case/'closed.sqlite';proof=case/'closed-proof.json'
    dbproofs=check_closed_evidence(case,row)
   state={'id':label,'selector':selected,'state':'PASS_OBSERVED_PENDING_REVIEW','actual_native_exit':owned['actual_exit'],'facts':facts,'invocation_ref':file_ref(d/'invocation.json'),'stdout_ref':file_ref(d/'stdout.raw'),'stderr_ref':file_ref(d/'stderr.raw'),'closed_copy_refs':dbproofs,'original_regression_closed_DB_missing_by_design':not row['new'] and package=='domain','measurement':'FIXTURE_OR_INJECTED','not_formal':True}
   write_json(casedir/'result.json',state);result.append(state)
   write_json(self.out/('progress-%02d.json'%len(result)),result)
  return result

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--grant',required=True);ap.add_argument('--grant-sha256',required=True);a=ap.parse_args()
 g,s,out=validate_grant(a.grant,a.grant_sha256)
 if out.exists():raise Stop('Output already exists; never resume/retry an old run')
 out.mkdir();write_json(out/'started.json',{'grant_ref':file_ref(a.grant),'source':CANDIDATE,'base':BASE,'authorized':True,'started_at_unix':time.time()})
 controller=None;error=None;results=None
 try:
  controller=Controller(g,s,out);controller.export_source();controller.build();controller.resources();results=controller.cases()
 except BaseException as e:
  error={'type':type(e).__name__,'message':str(e)}
  raise
 finally:
  summary={'source':CANDIDATE,'base':BASE,'source_acceptance':False,'formal_increment':0,'first_error':error,'results':results,'actual_test_invocations':0 if controller is None else controller.tests,'counter_reset':False,'stage':'INCOMPLETE' if error else ('FINITE_EXECUTION_COMPLETE_WITH_HOLDS' if results and any(x['state']=='NOT_RUN_RESOURCE_HOLD' for x in results) else 'FINITE_EXECUTION_COMPLETE_PENDING_REVIEW')}
  if controller:
   try:
    controller.ledger.check('final');write_json(out/'inputs.final.json',controller.ledger.export());write_json(out/'runtime.after.json',runtime_snapshot(controller.debug,g['resource_files']))
   except BaseException as e:
    summary['finalization_error']=type(e).__name__+': '+str(e);summary['stage']='INCOMPLETE';error=error or summary['finalization_error']
  write_json(out/'result.json',summary)
  if error and sys.exc_info()[0] is None:raise Stop('Finalization incomplete')
if __name__=='__main__':main()
