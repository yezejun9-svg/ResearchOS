import sys
sys.dont_write_bytecode=True
import argparse, contextlib, hashlib, io, json, os, re, stat, time, types
from pathlib import Path
# Hash actual source bytes BEFORE compile; no importlib loader and no pyc read for controller modules.
_common_path=Path(__file__).resolve().parent/'controller_common.v2.py'
_common_raw=_common_path.read_bytes()
if hashlib.sha256(_common_raw).hexdigest()!='d7c12331d66be452a807b172a1d7510ee307326b42c869d32edb9a5199889eb9':raise RuntimeError('Pinned common source mismatch before import')
if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True:raise RuntimeError('Pinned -I -S -X utf8 required')
_common=types.ModuleType('w09_common_v2');_common.__file__=str(_common_path);sys.modules[_common.__name__]=_common
exec(compile(_common_raw,str(_common_path),'exec'),_common.__dict__)
globals().update({k:v for k,v in _common.__dict__.items() if not k.startswith('__')})

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
  self.g,self.s,self.out=g,s,out;self.serial=0;self.tests=0;self.results=[];self.attempts=[];self.ledger=Ledger(out/'vectors')
  self.ledger.add(g['_authorization_paths'],'consumed-immutable-Root-authorization-chain')
  write_json(out/'runtime.source.before.json',runtime_source_snapshot(g['resource_files']))
  self.normal=trusted_module(g['normal_helper_ref']['path'],g['normal_helper_ref'])
  self.debug=trusted_module(g['debug_helper_ref']['path'],g['debug_helper_ref'])
  self.environment={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
  for var in ('GOCACHE','GOTMPDIR','GOPATH'):(out/var.lower()).mkdir()
  self.goroot=no_alias(g['goroot']);self.modcache=no_alias(g['module_cache'])
  (out/'testtmp').mkdir()
  self.environment.update(TMP=str(out/'testtmp'),TEMP=str(out/'testtmp'),PATH=str(Path(g['tools']['cmd']['path']).parent),GOROOT=str(self.goroot),GOTOOLCHAIN='local',GOENV='off',GOWORK='off',GOPROXY='off',GOSUMDB='off',CGO_ENABLED='0',GOOS='windows',GOARCH='amd64',GOAMD64='v1',GOEXPERIMENT='',GODEBUG='',GOFLAGS='-mod=readonly -buildvcs=false -p=1',GOCACHE=str(out/'gocache'),GOTMPDIR=str(out/'gotmpdir'),GOPATH=str(out/'gopath'),GOMODCACHE=str(self.modcache),GOMAXPROCS='2')
  self.tree=out/'source';self.tool_images=[g['tools']['go']]+g['go_tool_images']
  self.ledger.add([r['path'] for r in g['resource_files']],'root-pinned-public-resource-universe')
  self.ledger.add([r['path'] for r in g['controller_refs']]+[g['spec_ref']['path']],'controller-spec')
  write_json(out/'runtime.before.json',runtime_snapshot(self.debug,g['resource_files']))
 def run(self,label,argv,cwd,timeout,process_cap,images,env=None,stdin_path=None):
  self.serial+=1
  if self.serial>128:raise Stop('Total native invocation cap')
  d=self.out/'native'/('%03d-%s'%(self.serial,label));d.mkdir(parents=True)
  started=time.time();result=None;wrapper=None;request=None;cause=FirstCause();effective=self.environment if env is None else env
  item={'serial':self.serial,'label':label,'directory':str(d),'actualargv':argv,'cwd':str(cwd),'environment':effective,'started_at_unix':started,'actual_native_exit':None,'owned_result':None,'wrapper_ref':None,'first_error':None,'secondary_errors':[]}
  self.attempts.append(item)
  write_json(d/'invocation.started.json',item)
  try:
   self.ledger.check('%03d-%s-before'%(self.serial,label))
   primary=file_ref(argv[0]);pins=[{'path':r['path'],'sha256':r['sha256'],'bytes':r['bytes']} for r in images]
   if label.startswith('case-'):
    worker=self.s['case_worker_ref'];python=self.g['tools']['python']
    request=write_json(d/'case-request.json',{'schema':'researchos.w09.owned-case-request.v2','grant_ref':self.g['_grant_ref'],'source_commit':CANDIDATE,'self_ref':worker,'python_ref':python,'debug_helper_ref':self.g['debug_helper_ref'],'argv':argv,'cwd':str(cwd),'env':effective,'output_dir':str(d),'timeout':120,'process_cap':process_cap,'images':pins,'allowed_module_files':[r['ref'] for r in self.ledger.rows.values()],'expected_image':{'sha256':primary['sha256'],'bytes':primary['bytes']}})
    wrapperargv=[python['path'],*FLAGS,worker['path'],'--request',request['path'],'--sha256',request['sha256']]
    write_json(d/'wrapper.started.json',{'actualargv':wrapperargv,'request_ref':request,'actual_native_exit':None})
    try:
     with (d/'wrapper.stdout.raw').open('xb') as so,(d/'wrapper.stderr.raw').open('xb') as se:wrapper=self.normal.run_owned(wrapperargv,str(PREP),self.environment,so,se,150)
     require_job(wrapper)
    except BaseException as e:cause.record(e,'case-wrapper')
    finally:
     item['wrapper_ref']=write_json(d/'wrapper.json',{'actualargv':wrapperargv,'cwd':str(PREP),'owned_result':wrapper,'actual_native_exit':None if wrapper is None else wrapper.get('actual_exit'),'request_ref':request,'stdout_ref':existing_ref(d/'wrapper.stdout.raw'),'stderr_ref':existing_ref(d/'wrapper.stderr.raw'),'first_error':cause.primary})
    if (d/'case-owned.json').is_file():result=raw_json((d/'case-owned.json').read_bytes())
    cause.raise_if_any()
   else:
    import contextlib
    with (d/'stdout.raw').open('xb') as so,(d/'stderr.raw').open('xb') as se, (Path(stdin_path).open('rb') if stdin_path else contextlib.nullcontext(None)) as si:
     result=self.debug.run_owned(argv,str(cwd),effective,so,se,timeout,{'sha256':primary['sha256'],'bytes':primary['bytes']},pins,[r['ref'] for r in self.ledger.rows.values()],process_cap,stdin=si,creation_flags=0x08000000)
   require_job(result,True)
   rawlimit=512*1024*1024 if label=='git-export' else 64*1024*1024
   if any((d/name).stat().st_size>rawlimit for name in ['stdout.raw','stderr.raw']):raise Stop('Native raw bound exceeded')
   modules=[]
   for entry in result['debug_capture']['modules']:
    p=entry['path_from_actual_file_handle'];slash=chr(92)
    if p.startswith(slash*2+'?'+slash+'UNC'+slash):p=slash*2+p[8:]
    elif p.startswith(slash*2+'?'+slash):p=p[4:]
    pin=file_ref(p)
    if pin['sha256']!=entry['before']['sha256'] or pin['bytes']!=entry['before']['bytes'] or entry['before']!=entry['after']:raise Stop('Actual held module differs')
    modules.append(p)
   self.ledger.add(modules,'actual-loaded-images-'+label)
  except BaseException as e:
   if cause.primary is None:cause.record(e,'native-stage')
  finally:
   item.update(ended_at_unix=time.time(),actual_native_exit=None if result is None else result.get('actual_exit'),owned_result=result,stdout_ref=existing_ref(d/'stdout.raw'),stderr_ref=existing_ref(d/'stderr.raw'),stdin_ref=existing_ref(stdin_path) if stdin_path else None)
   cause.attempt('after-vector',lambda:self.ledger.check('%03d-%s-after'%(self.serial,label)))
   item.update(first_error=cause.primary,secondary_errors=cause.secondary)
   cause.attempt('save-native-invocation',lambda:write_json(d/'invocation.json',item))
   if cause.primary:cause.attempt('save-first-cause',lambda:write_json(d/'failure.origin.json',{'first_error':cause.primary,'secondary_errors':cause.secondary,'actual_native_exit':item['actual_native_exit'],'counter_reset':False}))
  cause.raise_if_any()
  return d,result

 def export_source(self):
  git=self.g['tools']['git'];root=no_alias(self.g['repository']);images=self.g['git_images']
  d,_=self.run('git-parent',[git['path'],'rev-parse',CANDIDATE+'^'],root,30,4,images)
  if (d/'stdout.raw').read_text(encoding='ascii').strip()!=BASE:raise Stop('Candidate parent differs')
  d,_=self.run('git-four-diff',[git['path'],'diff-tree','--no-commit-id','--name-only','-r',CANDIDATE],root,30,4,images)
  if set((d/'stdout.raw').read_text(encoding='utf-8').splitlines())!=set(self.s['exact4_paths']):raise Stop('Candidate not exact4')
  catalog=read_bound(self.g['source_catalog_ref']);rows=catalog['files']
  if len(rows)>4096 or len({x['path'].casefold() for x in rows})!=len(rows):raise Stop('Catalog duplicate/cap')
  # Query exact candidate:path, then independently verify Git blob AND SHA/size. No tree-wide extraction/private data.
  for row in rows:
   name=row['path'];parts=Path(name).parts
   if Path(name).is_absolute() or '..' in parts or any(':' in p or p.rstrip(' .')!=p for p in parts) or row['mode']!='100644' or row['type']!='blob':raise Stop('Catalog path/mode')
  request=write_bytes(self.out/'git-export.stdin.raw',''.join(CANDIDATE+':'+r['path']+'\n' for r in rows).encode('utf-8'))
  self.ledger.add([request['path']],'exact-export-request')
  d,_=self.run('git-export',[git['path'],'cat-file','--batch'],root,90,4,images,stdin_path=request['path'])
  raw=(d/'stdout.raw').read_bytes();pos=0;self.tree.mkdir();members=[]
  for row in rows:
   end=raw.index(b'\n',pos);oid,kind,n=raw[pos:end].decode('ascii','strict').split();n=int(n);pos=end+1
   body=raw[pos:pos+n];pos+=n
   if oid!=row['git_blob'] or kind!='blob' or n!=row['bytes'] or len(body)!=n or raw[pos:pos+1]!=b'\n' or hashlib.sha256(body).hexdigest()!=row['sha256']:raise Stop('Actual exported blob framing/hash differs')
   pos+=1;members.append(write_bytes(self.tree/row['path'],body))
  if pos!=len(raw):raise Stop('Unexpected extra export bytes')
  for pin in self.s['exact4_pins']:
   actual=file_ref(self.tree/pin['path'])
   if (actual['sha256'],actual['bytes'])!=(pin['sha256'],pin['bytes']):raise Stop('Exported candidate test differs')
  if {str(p.relative_to(self.tree)).replace(chr(92),'/') for p in walk_files(self.tree)}!={r['path'] for r in rows}:raise Stop('Complete export catalog differs BEFORE any Go')
  write_json(self.out/'source-export.json',{'candidate':CANDIDATE,'architecture_base':BASE,'catalog_ref':self.g['source_catalog_ref'],'stdin_ref':request,'raw_ref':file_ref(d/'stdout.raw'),'files':members,'complete_before_any_Go':True,'not_combined_Main':True})
  self.ledger.add([r['path'] for r in members],'fixed-Git-export')

 def resources(self):
  self.resource={'symlink':'HOLD_NOT_GRANTED','junction':'HOLD_NOT_GRANTED'};self.link=None
  # Only a frozen false resource grant produces HOLD. Every granted OS error is an unexpected failure.
  if self.g['resources']['symlink']:
   root=self.out/'symlink-prerequisite';root.mkdir();a=root/'A';b=root/'B';a.mkdir();b.mkdir()
   try:
    os.symlink(str(b),str(a/'outside'),target_is_directory=True)
    if not stat.S_ISLNK((a/'outside').lstat().st_mode) or (a/'outside').resolve()!=b.resolve():raise Stop('Wrong symlink identity')
    self.resource['symlink']='AVAILABLE'
   except BaseException as e:
    write_json(root/'failure.json',{'actual_native_exit':None,'type':type(e).__name__,'message':str(e),'winerror':getattr(e,'winerror',None),'errno':getattr(e,'errno',None),'classification':'UNEXPECTED_STOP_NOT_HOLD'});raise
  if self.g['resources']['junction']:
   root=self.out/'junction-resource';root.mkdir();a=root/'A';b=root/'B';a.mkdir();b.mkdir()
   for p in [a/'same.txt',b/'same.txt']:write_bytes(p,b'owned-public-marker')
   link=a/'outside'
   if any(c in str(root) for c in '"%&|<>^!\r\n'):raise Stop('Unsafe cmd resource path')
   cmd=self.g['tools']['cmd'];command='mklink /J "'+str(link)+'" "'+str(b)+'"'
   self.run('junction-resource',[cmd['path'],'/D','/V:OFF','/S','/C',command],root,15,1,[cmd])
   if not getattr(link.lstat(),'st_file_attributes',0)&0x400 or link.resolve()!=b.resolve():raise Stop('Wrong actual junction target')
   self.resource['junction']='AVAILABLE';self.link=root
  write_json(self.out/'resource-status.json',{'states':self.resource,'grant_ref':self.g['_grant_ref'],'granted':self.g['resources'],'hold_policy':'ONLY_EXPLICIT_FALSE_GRANT'})

 def build(self):
  go=self.g['tools']['go']['path'];self.ledger.check('pre-build-complete')
  d,_=self.run('go-version',[go,'version'],self.tree,30,1,self.tool_images)
  if (d/'stdout.raw').read_text(encoding='utf-8').strip()!='go version go1.27.1 windows/amd64':raise Stop('Go version')
  d,_=self.run('go-env',[go,'env','-json','GOROOT','GOVERSION','GOENV','GOTOOLCHAIN','GOMOD','GOMODCACHE','GOCACHE','GOTMPDIR','CGO_ENABLED','GOWORK','GOOS','GOARCH','GOAMD64','GOEXPERIMENT','GODEBUG'],self.tree,30,1,self.tool_images)
  actual=raw_json((d/'stdout.raw').read_bytes())
  for key in ['GOROOT','GOENV','GOTOOLCHAIN','GOMODCACHE','GOCACHE','GOTMPDIR','CGO_ENABLED','GOWORK','GOOS','GOARCH','GOAMD64','GOEXPERIMENT','GODEBUG']:
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
  generated_mains=[p for p in walk_files(self.out/'gotmpdir') if p.name=='_testmain.go']
  importcfgs=[p for p in walk_files(self.out/'gotmpdir') if p.name.startswith('importcfg')]
  archives={}
  for cfg in importcfgs:
   for line in cfg.read_text(encoding='utf-8',errors='strict').splitlines():
    if line.startswith('packagefile '):
     path=no_alias(line.split('=',1)[1]);pin=file_ref(path)
     if pin['path'].casefold() not in self.ledger.rows:raise Stop('Actual compiler archive outside final full vector')
     archives[pin['path']]=pin
  if len(generated_mains)<2 or not importcfgs or not archives:raise Stop('Actual generated compiler provenance incomplete')
  write_json(self.out/'compiler-derived.json',{'generated_testmain_refs':[file_ref(p) for p in generated_mains],'importcfg_refs':[file_ref(p) for p in importcfgs],'archive_refs':list(archives.values()),'testexe_refs':self.executables,'all_WORK_ref':file_ref(self.out/'compiled-inputs.frozen.json')})
  self.ledger.check('compile-complete')
 def check_membership(self):
  for root in [self.tree,self.goroot,self.modcache,self.out/'gotmpdir',self.out/'gocache']:
   current={str(x).casefold() for x in walk_files(root)}
   frozen={k for k,v in self.ledger.rows.items() if Path(v['ref']['path']).is_relative_to(root)}
   if current!=frozen:raise Stop('Frozen directory membership differs '+str(root))
 def cases(self):
  result=self.results
  for row in self.s['roster']:
   label=row['id'];selected=row['selector'];required=row['requires_resource']
   if required and any(self.resource[k]!='AVAILABLE' for k in required):
    result.append({'id':label,'selector':selected,'state':'NOT_RUN_RESOURCE_HOLD','requirements':required,'actual_native_exit':None});write_json(self.out/('progress-%02d.json'%len(result)),result);continue
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
 if file_ref(__file__)!=s['controller_ref']:raise Stop('Controller exact pin')
 if out.exists():raise Stop('Output exists; no resume/retry')
 out.mkdir();write_json(out/'started.json',{'grant_ref':g['_grant_ref'],'source':CANDIDATE,'base':BASE,'started_at_unix':time.time()})
 c=Controller.__new__(Controller);c.g=g;c.s=s;c.out=out;c.tests=0;c.serial=0;c.results=[];c.attempts=[];c.ledger=Ledger(out/'vectors');c.debug=None;cause=FirstCause()
 try:
  c.__init__(g,s,out);c.export_source();c.build();c.resources();c.cases()
 except BaseException as e:cause.record(e,'controller')
 finally:
  cause.attempt('final-vector',lambda:c.ledger.check('final'))
  cause.attempt('freeze-final-inputs',lambda:write_json(out/'inputs.final.json',c.ledger.export()))
  cause.attempt('runtime-source-after',lambda:write_json(out/'runtime.source.after.json',runtime_source_snapshot(g['resource_files'])))
  if c.debug:cause.attempt('runtime-after',lambda:write_json(out/'runtime.after.json',runtime_snapshot(c.debug,g['resource_files'])))
  completed={x['id'] for x in c.results}
  notrun=[{'id':x['id'],'selector':x['selector'],'state':'NOT_RUN_AFTER_STOP'} for x in s['roster'] if x['id'] not in completed]
  summary={'source':CANDIDATE,'base':BASE,'source_acceptance':False,'formal_increment':0,'first_error':cause.primary,'secondary_errors':cause.secondary,'results':c.results,'not_run':notrun,'actual_test_invocations':c.tests,'attempts':c.attempts,'counter_reset':False,'stage':'INCOMPLETE' if cause.primary or notrun else 'FINITE_EXECUTION_COMPLETE_PENDING_REVIEW','grant_ref':g['_grant_ref'],'python_inventory':'ACTUAL_POINT_IN_TIME_ONLY_NOT_LIFECYCLE'}
  write_json(out/'result.json',summary)
  if cause.primary:write_json(out/'failure.origin.json',{'first_error':cause.primary,'secondary_errors':cause.secondary,'counter_reset':False,'actual_native_exit':None,'native_details_in_each_attempt':True})
 cause.raise_if_any()
if __name__=='__main__':
 try:main()
 except BaseException as e:
  # Pre-authority/pre-output failures remain on actual stderr for the Root-owned caller.
  print(json.dumps({'schema':'researchos.w09.entry-failure.v2','error_type':type(e).__name__,'message':str(e),'actual_child_native_exit':None,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
  raise

