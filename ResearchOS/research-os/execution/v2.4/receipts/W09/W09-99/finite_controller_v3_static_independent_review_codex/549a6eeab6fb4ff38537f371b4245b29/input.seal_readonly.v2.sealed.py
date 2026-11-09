import sys
sys.dont_write_bytecode=True
import argparse, contextlib, hashlib, io, json, os, re, stat, time, types
from pathlib import Path
# Hash actual source bytes BEFORE compile; no importlib loader and no pyc read for controller modules.
_common_path=Path(__file__).resolve().parent/'controller_common.v2.sealed.py'
_common_raw=_common_path.read_bytes()
if hashlib.sha256(_common_raw).hexdigest()!='35e86c1b3bcbd6b070c0c46df21f9a4e42e8a5c4aacf6b30c3fb5cf46fef64d9':raise RuntimeError('Pinned common source mismatch before import')
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


VECTOR_BINDINGS={}

def exact_pin_map(pins):
 result={}
 for pin in pins:
  if not isinstance(pin,dict) or set(pin)!={'path','sha256','bytes'}:raise Stop('Nonexact ledger pin')
  if not isinstance(pin['path'],str) or not re.fullmatch('[0-9a-f]{64}',pin['sha256']) or type(pin['bytes']) is not int or pin['bytes']<0:raise Stop('Malformed exact ledger pin')
  key=pin['path'].casefold()
  if key in result:raise Stop('Duplicate/colliding ledger membership')
  result[key]=pin
 return result

class PrefixProof:
 def __init__(self,directory):
  self.directory=directory;self.revision=0;self.rows={};self.vectors=[];self.last_end=None
 def add(self,group,pins):
  # Match Ledger.add, including deduplication and empty additions advancing revision.
  new=[]
  for pin in pins:
   if set(pin)!={'path','sha256','bytes'}:raise Stop('Unexpected addition pin fields')
   verify(pin);key=pin['path'].casefold()
   if key in self.rows:
    if self.rows[key]['ref']!=pin:raise Stop('Addition collides with immutable prefix')
   else:self.rows[key]={'ref':pin,'group':group};new.append(pin)
  self.revision+=1
  actual=raw_json((self.directory/('%04d-add.json'%self.revision)).read_bytes())
  expected={'revision':self.revision,'group':group,'new_files':new,'total':len(self.rows)}
  if actual!=expected or type(actual.get('revision')) is not int or type(actual.get('total')) is not int:raise Stop('Exact producer addition/prefix mismatch')
 def vector(self,name):
  p=self.directory/(name+'.json');key=str(p)
  if key in VECTOR_BINDINGS:raise Stop('Duplicate vector stage')
  VECTOR_BINDINGS[key]={'revision':self.revision,'members':[row['ref'] for row in self.rows.values()]}
  v=check_vector(p)
  if self.last_end is not None and v['started_at_unix']<self.last_end:raise Stop('Vector observation order regressed')
  self.last_end=v['ended_at_unix'];self.vectors.append(p.name)
 def finish(self,final):
  expected_files={('%04d-add.json'%i) for i in range(1,self.revision+1)}|set(self.vectors)
  if {p.name for p in self.directory.iterdir()}!=expected_files:raise Stop('Missing/extra prefix or vector file')
  rows=raw_json(final.read_bytes())
  if rows!=list(self.rows.values()):raise Stop('Final ordered membership/group differs from exact prefix')
  exact_pin_map([r['ref'] for r in rows])

def check_vector(path,expected_count=None):
 p=Path(path);bound=VECTOR_BINDINGS.get(str(p))
 if bound is None:raise Stop('Vector has no producer-specific prefix binding')
 v=raw_json(p.read_bytes())
 if set(v)!={'revision','file_count','started_at_unix','ended_at_unix','drift'}:raise Stop('Vector shape')
 members=exact_pin_map(bound['members'])
 if v['drift']!=[] or type(v['revision']) is not int or v['revision']!=bound['revision'] or type(v['file_count']) is not int or v['file_count']!=len(members):raise Stop('Stage vector revision/cardinality does not match exact prefix')
 if expected_count is not None and v['file_count']!=expected_count:raise Stop('Input vector count mismatch')
 start,end=v['started_at_unix'],v['ended_at_unix']
 if type(start) not in (int,float) or type(end) not in (int,float) or not (0<start<=end<float('inf')):raise Stop('Vector timestamps invalid')
 return v

def bind_all_prefixes(root,g,s):
 VECTOR_BINDINGS.clear()
 pins=lambda paths:[file_ref(p) for p in paths]
 outerdir=root.with_name(root.name+'-outer')
 outer=PrefixProof(outerdir/'vectors')
 outer.add('actual-authorization-public-inputs',pins(g['_authorization_paths'])+g['resource_files'])
 outer.vector('before');outer.vector('after');outer.finish(outerdir/'inputs.final.json')
 c=PrefixProof(root/'vectors');serial=0
 c.add('consumed-immutable-Root-authorization-chain',pins(g['_authorization_paths']))
 c.add('root-pinned-public-resource-universe',g['resource_files'])
 c.add('controller-spec',g['controller_refs']+[g['spec_ref']])
 def stage(label):
  nonlocal serial
  serial+=1;d=root/'native'/('%03d-%s'%(serial,label))
  c.vector('%03d-%s-before'%(serial,label))
  if label.startswith('case-'):
   request=raw_json((d/'case-request.json').read_bytes())
   before=[row['ref'] for row in c.rows.values()]
   if request['allowed_module_files']!=before:raise Stop('Case allowed_module_files differ from exact before-prefix')
   exact_pin_map(request['allowed_module_files'])
   worker=PrefixProof(d/'worker-vectors')
   worker.add('worker-actual-inputs',pins(g['_authorization_paths'])+[file_ref(d/'case-request.json')]+before)
   worker.vector('before');worker.vector('after');worker.finish(d/'worker.inputs.final.json')
  inv=raw_json((d/'invocation.json').read_bytes());modules=[]
  for entry in inv['owned_result']['debug_capture']['modules']:
   p=entry['path_from_actual_file_handle'];slash=chr(92)
   if p.startswith(slash*2+'?'+slash+'UNC'+slash):p=slash*2+p[8:]
   elif p.startswith(slash*2+'?'+slash):p=p[4:]
   pin=file_ref(p)
   if pin['sha256']!=entry['before']['sha256'] or pin['bytes']!=entry['before']['bytes'] or entry['before']!=entry['after']:raise Stop('Held image/prefix pin differs')
   modules.append(pin)
  c.add('actual-loaded-images-'+label,modules)
  c.vector('%03d-%s-after'%(serial,label))
 stage('git-parent');stage('git-four-diff')
 c.add('exact-export-request',[file_ref(root/'git-export.stdin.raw')]);stage('git-export')
 exported=raw_json((root/'source-export.json').read_bytes())['files']
 c.add('fixed-Git-export',exported);c.vector('pre-build-complete')
 stage('go-version');stage('go-env')
 for label in ['domain','adapter']:
  stage('list-'+label)
  # The unchanged producer explicitly requires all stable list inputs already present.
  # Thus this group is an empty-new-files event, but still advances the revision.
  c.add('actual-go-list-'+label,[])
  stage('compile-'+label)
  c.add('compiled-test-image-'+label,[file_ref(root/(label+'.test.exe'))])
  stage('buildinfo-'+label)
 generated=walk_files(root/'gotmpdir')+walk_files(root/'gocache')+[root/'domain.test.exe',root/'adapter.test.exe']
 c.add('final-WORK-generated-importcfg-archives-exes',pins(generated))
 if c.revision!=21:raise Stop('Pinned compile producer revision differs')
 if raw_json((root/'compiled-inputs.frozen.json').read_bytes())!=list(c.rows.values()):raise Stop('Compile prefix membership differs')
 c.vector('compile-complete')
 if g['resources']['junction']:stage('junction-resource')
 for row in s['roster']:
  if all(g['resources'][key] for key in row['requires_resource']):stage('case-'+row['id'])
 c.vector('final');c.finish(root/'inputs.final.json')
 return {'stage_vectors':len(VECTOR_BINDINGS),'controller_final_revision':c.revision,'controller_final_members':len(c.rows),'membership_source':'EXACT_PINNED_PRODUCER_ADD_PREFIX','timestamp_role':'AUXILIARY_ORDER_ONLY','raw_vectors_contain_member_list':False}


def verify_runtime_pair(directory,prefix,resources):
 allowed={x['path'].casefold():x for x in resources}
 for tag in ['before','after']:
  for stem in [prefix+'.runtime.',prefix+'.runtime.source.'] if prefix else ['runtime.','runtime.source.']:
   rows=raw_json((directory/(stem+tag+'.json')).read_bytes())
   if not rows:raise Stop('Missing actual interpreter point-in-time observation')
   for pin in rows:
    if allowed.get(pin['path'].casefold())!=pin:raise Stop('Actual runtime source outside pinned catalog')
    verify(pin)

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--grant',required=True);ap.add_argument('--grant-sha256',required=True);ap.add_argument('--result-sha256',required=True);a=ap.parse_args()
 g,s,root=validate_grant(a.grant,a.grant_sha256)
 if file_ref(__file__)!=s['sealer_ref']:raise Stop('Sealer exact pin')
 root=no_alias(root);prefix_audit=bind_all_prefixes(root,g,s);resultref=file_ref(root/'result.json')
 if resultref['sha256']!=a.result_sha256:raise Stop('Explicit completed result required')
 result=raw_json((root/'result.json').read_bytes());outerdir=root.with_name(root.name+'-outer');outer=raw_json((outerdir/'completion.json').read_bytes())
 if outer.get('first_error') or outer.get('secondary_errors'):raise Stop('Faulted outer result')
 require_job(outer['owned_result'])
 if outer['actual_native_controller_exit']!=0 or outer['actualargv']!=[g['tools']['python']['path'],*FLAGS,s['controller_ref']['path'],'--grant',str(Path(a.grant)),'--grant-sha256',a.grant_sha256]:raise Stop('Outer invocation differs from exact grant')
 for key in ['stdout_ref','stderr_ref']:verify(outer[key])
 outerfinal=raw_json((outerdir/'inputs.final.json').read_bytes())
 for row in outerfinal:verify(row['ref'])
 check_vector(outerdir/'vectors/before.json',len(outerfinal));check_vector(outerdir/'vectors/after.json',len(outerfinal));verify_runtime_pair(outerdir,'',g['resource_files'])
 if result.get('stage')!='FINITE_EXECUTION_COMPLETE_PENDING_REVIEW' or result.get('first_error') or result.get('secondary_errors') or result.get('not_run') or result.get('source')!=CANDIDATE or result.get('base')!=BASE or result.get('grant_ref')!=g['_grant_ref']:raise Stop('Incomplete/faulted source execution')
 states=raw_json((root/'resource-status.json').read_bytes())
 if states.get('grant_ref')!=g['_grant_ref'] or states.get('granted')!=g['resources'] or states.get('states')!={k:'AVAILABLE' if v else 'HOLD_NOT_GRANTED' for k,v in g['resources'].items()}:raise Stop('OS HOLD provenance differs')
 rows=result['results'];roster=s['roster']
 if len(rows)!=49 or [x['id'] for x in rows]!=[x['id'] for x in roster] or [x['selector'] for x in rows]!=[x['selector'] for x in roster]:raise Stop('Fixed roster order/identity')
 eligible=[x for x in roster if all(g['resources'][k] for k in x['requires_resource'])]
 labels=['git-parent','git-four-diff','git-export','go-version','go-env','list-domain','compile-domain','buildinfo-domain','list-adapter','compile-adapter','buildinfo-adapter']+(['junction-resource'] if g['resources']['junction'] else [])+['case-'+x['id'] for x in eligible]
 git=g['tools']['git']['path'];go=g['tools']['go']['path'];tree=root/'source'
 expected_argv={
  'git-parent':[git,'rev-parse',CANDIDATE+'^'],
  'git-four-diff':[git,'diff-tree','--no-commit-id','--name-only','-r',CANDIDATE],
  'git-export':[git,'cat-file','--batch'],
  'go-version':[go,'version'],
  'go-env':[go,'env','-json','GOROOT','GOVERSION','GOENV','GOTOOLCHAIN','GOMOD','GOMODCACHE','GOCACHE','GOTMPDIR','CGO_ENABLED','GOWORK','GOOS','GOARCH','GOAMD64','GOEXPERIMENT','GODEBUG']}
 for label,pkg in [('domain','./internal/domain'),('adapter','./adapters/retrieval')]:
  expected_argv['list-'+label]=[go,'list','-deps','-test','-compiled','-json','-mod=readonly','-work','-x',pkg]
  expected_argv['compile-'+label]=[go,'test','-c','-p=1','-mod=readonly','-work','-x','-o',str(root/(label+'.test.exe')),pkg]
  expected_argv['buildinfo-'+label]=[go,'version','-m',str(root/(label+'.test.exe'))]
 if g['resources']['junction']:
  resource=root/'junction-resource';expected_argv['junction-resource']=[g['tools']['cmd']['path'],'/D','/V:OFF','/S','/C','mklink /J "'+str(resource/'A/outside')+'" "'+str(resource/'B')+'"']
 for row in eligible:
  package='adapter' if row['file'].startswith('adapters/') else 'domain'
  expected_argv['case-'+row['id']]=[str(root/(package+'.test.exe')),'-test.run',row['test_run'],'-test.v','-test.count=1','-test.failfast','-test.timeout=120s']
 attempts=result['attempts']
 if [x['label'] for x in attempts]!=labels or len(attempts)>128 or result['actual_test_invocations']!=len(eligible):raise Stop('Exact complete native stage inventory')
 actualdirs=sorted(x.name for x in (root/'native').iterdir())
 if actualdirs!=sorted('%03d-%s'%(i+1,label) for i,label in enumerate(labels)):raise Stop('Missing/extra native stage directory')
 for i,(item,label) in enumerate(zip(attempts,labels),1):
  d=root/'native'/('%03d-%s'%(i,label));inv=raw_json((d/'invocation.json').read_bytes());start=raw_json((d/'invocation.started.json').read_bytes())
  if inv!=item or inv['serial']!=i or inv.get('first_error') or inv.get('secondary_errors') or inv['actual_native_exit']!=0 or start['actualargv']!=inv['actualargv']:raise Stop('Incomplete actual native invocation')
  if inv['actualargv']!=expected_argv[label]:raise Stop('Actual native argv differs from fixed stage plan')
  require_job(inv['owned_result'],True)
  for key in ['stdout_ref','stderr_ref']:verify(inv[key])
  check_vector(root/'vectors'/('%03d-%s-before.json'%(i,label)));check_vector(root/'vectors'/('%03d-%s-after.json'%(i,label)))
  if label.startswith('case-'):
   verify(inv['wrapper_ref']);wrapper=raw_json(Path(inv['wrapper_ref']['path']).read_bytes());require_job(wrapper['owned_result'])
   if wrapper['first_error'] or wrapper['actual_native_exit']!=0:raise Stop('Faulted case wrapper')
   verify(wrapper['request_ref']);request=raw_json(Path(wrapper['request_ref']['path']).read_bytes())
   if wrapper['actualargv']!=[g['tools']['python']['path'],*FLAGS,s['case_worker_ref']['path'],'--request',wrapper['request_ref']['path'],'--sha256',wrapper['request_ref']['sha256']] or request['grant_ref']!=g['_grant_ref'] or request['argv']!=inv['actualargv'] or request['cwd']!=inv['cwd'] or request['env']!=inv['environment']:raise Stop('Wrapper/request/native binding')
   for key in ['stdout_ref','stderr_ref']:verify(wrapper[key])
   owned=raw_json((d/'case-owned.json').read_bytes());completion=raw_json((d/'worker.completion.json').read_bytes())
   if owned!=inv['owned_result'] or completion.get('first_error') or completion.get('secondary_errors') or completion.get('actual_native_exit')!=0:raise Stop('Worker final actual proof')
   frozen=raw_json((d/'worker.inputs.final.json').read_bytes())
   for r in frozen:verify(r['ref'])
   check_vector(d/'worker-vectors/before.json',len(frozen));check_vector(d/'worker-vectors/after.json',len(frozen));verify_runtime_pair(d,'worker',g['resource_files'])
 holds=[];passed=0;leafs=0
 for observed,planned in zip(rows,roster):
  unavailable=[k for k in planned['requires_resource'] if not g['resources'][k]]
  if unavailable:
   if observed.get('state')!='NOT_RUN_RESOURCE_HOLD' or observed.get('requirements')!=planned['requires_resource'] or observed.get('actual_native_exit') is not None:raise Stop('Illegal conditional HOLD')
   holds.append(observed);continue
  if observed.get('state')!='PASS_OBSERVED_PENDING_REVIEW' or observed.get('actual_native_exit')!=0:raise Stop('Expected eligible case is not observed PASS')
  for key in ['invocation_ref','stdout_ref','stderr_ref']:verify(observed[key])
  facts=test_facts(Path(observed['stdout_ref']['path']).read_bytes(),planned['selector'],planned['expected_records'])
  if facts!=observed['facts']:raise Stop('Raw Go event inventory')
  passed+=1;leafs+=len(facts['actual_leaf_records'])
  for pin in observed['closed_copy_refs']:verify(pin)
  if planned['new'] and planned['file'].startswith('internal/domain/'):
   if not observed['closed_copy_refs'] or check_closed_evidence(Path(observed['closed_copy_refs'][0]['path']).parent,planned)!=observed['closed_copy_refs']:raise Stop('Closed DB file-only proof')
 final=raw_json((root/'inputs.final.json').read_bytes())
 for row in final:verify(row['ref'])
 frozenpaths={x['ref']['path'] for x in final}
 if not set(g['_authorization_paths']).issubset(frozenpaths):raise Stop('Consumed actual authorization chain omitted from full vector')
 for name in ['pre-build-complete','compile-complete','final']:check_vector(root/'vectors'/(name+'.json'))
 addfiles=sorted((root/'vectors').glob('*-add.json'));merged={}
 for number,p in enumerate(addfiles,1):
  doc=raw_json(p.read_bytes())
  if doc['revision']!=number:raise Stop('Ledger addition sequence gap')
  for pin in doc['new_files']:
   if pin['path'].casefold() in merged:raise Stop('Duplicate ledger entry')
   verify(pin);merged[pin['path'].casefold()]=pin
  if doc['total']!=len(merged):raise Stop('Ledger total mismatch')
 if {r['ref']['path'].casefold():r['ref'] for r in final}!=merged:raise Stop('Complete ledger differs from append chain')
 verify_runtime_pair(root,'',g['resource_files'])
 for name in ['source-export.json','compiled-executables.json','compiled-inputs.frozen.json','graph-domain.json','graph-adapter.json','compiler-derived.json']:
  if not (root/name).is_file():raise Stop('Missing compiled provenance '+name)
 source_export=raw_json((root/'source-export.json').read_bytes());catalog=read_bound(g['source_catalog_ref'])
 if source_export.get('catalog_ref')!=g['source_catalog_ref'] or source_export.get('complete_before_any_Go') is not True or len(source_export['files'])!=catalog['file_count']:raise Stop('Public export proof')
 for pin,row in zip(source_export['files'],catalog['files']):
  if pin['path']!=str(root/'source'/row['path']) or (pin['sha256'],pin['bytes'])!=(row['sha256'],row['bytes']):raise Stop('Exported public input differs')
  verify(pin)
 derived=raw_json((root/'compiler-derived.json').read_bytes())
 if len(derived['generated_testmain_refs'])<2 or not derived['archive_refs'] or not derived['importcfg_refs']:raise Stop('Compiler generated/archive closure')
 for pin in derived['generated_testmain_refs']+derived['archive_refs']+derived['importcfg_refs']+list(derived['testexe_refs'].values()):
  verify(pin)
  if pin['path'] not in frozenpaths:raise Stop('Derived compiler input not frozen')
 for ownedroot in [root/'source',root/'gotmpdir',root/'gocache',Path(g['goroot']),Path(g['module_cache'])]:
  if {str(p) for p in walk_files(ownedroot)}!={p for p in frozenpaths if Path(p).is_relative_to(ownedroot)}:raise Stop('Complete actual compiled/input directory membership differs')
 work=walk_files(root/'gotmpdir');actual_mains=[file_ref(p) for p in work if p.name=='_testmain.go'];actual_cfgs=[file_ref(p) for p in work if p.name.startswith('importcfg')];actual_archives={}
 for pin in actual_cfgs:
  for line in Path(pin['path']).read_text(encoding='utf-8',errors='strict').splitlines():
   if line.startswith('packagefile '):
    p=no_alias(line.split('=',1)[1]);actual_archives[str(p)]=file_ref(p)
 if actual_mains!=derived['generated_testmain_refs'] or actual_cfgs!=derived['importcfg_refs'] or list(actual_archives.values())!=derived['archive_refs']:raise Stop('Actual generated/importcfg/archive multiset differs')
 for label in ['domain','adapter']:
  graph=raw_json((root/('graph-'+label+'.json')).read_bytes())
  if not graph or len(graph)>4096 or any(x.get('Error') or x.get('DepsErrors') or x.get('Incomplete') for x in graph):raise Stop('Actual full Go graph failed')
  for package in graph:
   if not package.get('Dir'):continue
   directory=no_alias(package['Dir'])
   for key in ['GoFiles','CgoFiles','CompiledGoFiles','TestGoFiles','XTestGoFiles','EmbedFiles','TestEmbedFiles','XTestEmbedFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SFiles','SwigFiles','SwigCXXFiles','SysoFiles']:
    for name in package.get(key,[]):
     p=Path(name);p=p if p.is_absolute() else directory/p
     if str(no_alias(p)) not in frozenpaths:raise Stop('Actual Go package input omitted from complete closure')
   if package.get('Module',{}).get('GoMod') and str(no_alias(package['Module']['GoMod'])) not in frozenpaths:raise Stop('Actual module metadata omitted')
 # All evidence is preserved. The new summary is included; only this manifest excludes itself.
 seal=root/'sealed-readonly-v2';seal.mkdir(exist_ok=False)
 write_json(seal/'summary.json',{'schema':'researchos.w09.finite-evidence-seal.v2','result_ref':resultref,'grant_ref':g['_grant_ref'],'spec_ref':g['spec_ref'],'scenario_rows':49,'actual_pass_rows':passed,'actual_leaf_records':leafs,'holds':holds,'source_acceptance':False,'formal_increment':0,'status':'EVIDENCE_ASSEMBLED_PENDING_NONAUTHOR_REVIEW','SQL_reads':0,'processes_started':0,'stage_prefix_audit':prefix_audit,'python_inventory':'ACTUAL_POINT_IN_TIME_ONLY','closed_DB_limitation':'29 new domain VACUUM copies; 21 selected four-table driver-value JSON and 8 business JSON; not fullDB/typeof/rowid equivalence; old six domain no export'})
 members=[];links=[]
 permitted_links={str(root/'symlink-prerequisite/A/outside'):root/'symlink-prerequisite/B',str(root/'junction-resource/A/outside'):root/'junction-resource/B'}
 for base in [root,outerdir]:
  for current,dirs,files in os.walk(base,followlinks=False):
   for name in list(dirs)+files:
    path=Path(current)/name;st=path.lstat()
    if stat.S_ISLNK(st.st_mode) or getattr(st,'st_file_attributes',0)&0x400:
     if str(path) not in permitted_links or path.resolve()!=permitted_links[str(path)].resolve():raise Stop('Unexpected evidence alias')
     links.append({'path':str(path),'resolved_target':str(path.resolve()),'file_attributes':getattr(st,'st_file_attributes',None),'mode':st.st_mode,'followed':False})
     if name in dirs:dirs.remove(name)
    elif path.is_file():members.append(file_ref(path))
 write_json(seal/'manifest.json',{'members':members,'member_count':len(members),'only_self_excluded':True,'owned_links_not_followed':links,'old_files_mutated':False})
if __name__=='__main__':
 try:main()
 except BaseException as e:
  # Pre-authority/pre-output failures remain on actual stderr for the Root-owned caller.
  print(json.dumps({'schema':'researchos.w09.entry-failure.v2','error_type':type(e).__name__,'message':str(e),'actual_child_native_exit':None,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
  raise

