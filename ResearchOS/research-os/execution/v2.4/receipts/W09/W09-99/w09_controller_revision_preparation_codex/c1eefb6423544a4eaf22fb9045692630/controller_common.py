"""Receipt-only controller support. No product/native execution at import."""
import base64, hashlib, json, os, re, stat, sys, time, types
from pathlib import Path
PREP=Path(__file__).resolve().parent
BASE='2cdb0d43d5a600eef13c8f1735946a9adf52d079'
CANDIDATE='cd0d818baa703fbc59a6f7c8187d467d41570094'
FLAGS=['-I','-S','-X','utf8']
class Stop(RuntimeError): pass
def raw_json(data):
 def pairs(items):
  obj={}
  for k,v in items:
   if k in obj: raise Stop('Duplicate JSON key: '+k)
   obj[k]=v
  return obj
 return json.loads(data,object_pairs_hook=pairs,parse_constant=lambda s: (_ for _ in ()).throw(Stop('Nonfinite JSON')))
def no_alias(p, exists=True):
 p=Path(p)
 if not p.is_absolute() or '..' in p.parts or Path(os.path.abspath(p))!=p: raise Stop('Noncanonical absolute path')
 for a in [*reversed(p.parents),p]:
  try:s=a.lstat()
  except FileNotFoundError:
   if a==p and not exists:continue
   raise
  if stat.S_ISLNK(s.st_mode) or getattr(s,'st_file_attributes',0)&0x400:raise Stop('Reparse/symlink path refused: '+str(a))
 if exists and p.resolve()!=p:raise Stop('Resolved alias')
 return p

def file_ref(p):
 p=no_alias(p);s=p.stat()
 if not stat.S_ISREG(s.st_mode):raise Stop('Regular file required')
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 after=p.stat()
 if (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise Stop('Read drift')
 return {'path':str(p),'sha256':h.hexdigest(),'bytes':s.st_size}
def verify(row):
 actual=file_ref(row['path'])
 if any(actual[k]!=row[k] for k in ['path','sha256','bytes']):raise Stop('Pin mismatch '+row['path'])
 return actual

def write_json(path,obj):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);no_alias(p,False)
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
 return file_ref(p)
def write_bytes(path,data):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);no_alias(p,False)
 with p.open('xb') as f:f.write(data)
 return file_ref(p)
def trusted_module(path,expected):
 raw=verified_raw(expected)
 if str(path)!=expected['path']:raise Stop('Helper path mismatch')
 mod=types.ModuleType(Path(path).stem);mod.__file__=str(path)
 exec(compile(raw,str(path),'exec'),mod.__dict__)
 return mod

def verified_raw(row):
 if not isinstance(row,dict) or set(row)!={'path','sha256','bytes'}:raise Stop('Exact file ref required')
 p=no_alias(row['path']);before=p.stat();raw=p.read_bytes();after=p.stat()
 if (before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise Stop('Pinned read drift')
 if str(p)!=row['path'] or type(row['bytes']) is not int or len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise Stop('Consumed raw pin mismatch')
 return raw

def root_authority(g,spec,grant_ref):
 # Proposed Root capsule. Its real producer/CAS adapter is an explicit OPEN prerequisite.
 binding=spec.get('root_binding')
 if not isinstance(binding,dict):raise Stop('UNBOUND: actual Root binding absent')
 consumed=[grant_ref,g['spec_ref']]
 def read(ref):
  raw=verified_raw(ref);consumed.append(ref);return raw_json(raw)
 def eq(a,b,label):
  if a!=b:raise Stop('Root authority mismatch: '+label)
 def pointer(obj,keys):
  if not isinstance(keys,list) or not keys:raise Stop('Explicit canonical field path required')
  for key in keys:obj=obj[key]
  return obj
 before=binding['before'];after=binding['after']
 if any(not isinstance(x,list) or len(x)!=3 or any(type(n) is not int or n<0 for n in x) for x in (before,after)):raise Stop('Explicit Root transition required')
 if after[0]!=before[0]+1 or after[1]!=before[1]+1 or after[2]<before[2]:raise Stop('Nonforward Root transition')
 capsule=read(g['registration_evidence_ref'])
 eq(capsule['schema'],'researchos.w09.root-registration-capsule.v1','capsule schema')
 eq(capsule['actor'],'codex:/root','registration actor')
 eq(capsule['before'],before,'before tuple');eq(capsule['after'],after,'after tuple')
 eq(capsule['registration_namespace'],binding['registration_namespace'],'registration namespace')
 root=no_alias(binding['registration_namespace'])
 for ref in [g['registration_evidence_ref'],capsule['manifest_ref'],capsule['audit_ref'],capsule['invocation_ref'],capsule['request_ref'],capsule['intent_ref']]:
  if not Path(ref['path']).is_relative_to(root):raise Stop('Foreign registration receipt')
 manifest=read(capsule['manifest_ref']);members=manifest['members']
 if not members or len({r['path'].casefold() for r in members})!=len(members):raise Stop('Registration manifest duplicate/empty')
 for ref in members:
  verified_raw(ref);consumed.append(ref)
 for key in ['audit_ref','invocation_ref','request_ref','intent_ref','registration_review_ref']:
  if capsule[key] not in members:raise Stop('Unsealed mandatory registration input '+key)
 audit=read(capsule['audit_ref']);invocation=read(capsule['invocation_ref']);request=read(capsule['request_ref']);intent=read(capsule['intent_ref'])
 eq(audit['status'],'REGISTRATION_COMPLETED','registration completion')
 eq(audit['actual_registration_executed'],True,'actual registration')
 eq(audit['before'],before,'audit before');eq(audit['after'],after,'audit after')
 eq(audit['intent_ref'],capsule['intent_ref'],'intent');eq(audit['invocation_ref'],capsule['invocation_ref'],'invocation')
 eq(invocation['request_ref'],capsule['request_ref'],'actual request')
 eq(invocation['actualargv'],request['argv'],'actual argv');eq(invocation['cwd'],request['cwd'],'actual cwd')
 if not request['argv'] or request['argv'][0]!=g['tools']['python']['path']:raise Stop('Registration Python substitution')
 require_job(invocation['owned_result'])
 if type(invocation['actual_native_exit']) is not int or invocation['actual_native_exit']!=0:raise Stop('Registration native completion absent')
 rr=read(capsule['registration_review_ref'])
 eq(rr['schema'],'researchos.w09.root-registration-review.v1','registration review schema')
 eq(rr['reviewer'],'codex:/root/w05_merge_review','registration nonauthor')
 eq(rr['decision'],'REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION','registration review decision')
 eq(rr['requested_changes'],[],'registration changes');eq(rr['actual_registration_executed'],False,'review timing')
 eq(rr['before'],before,'review before');eq(rr['after'],after,'review after')
 eq(rr['request_ref'],capsule['request_ref'],'reviewed actual request')
 for key in ['register_ref','wrapper_ref','prepared_ref']:
  eq(rr[key],request[key],'reviewed registration code');verified_raw(request[key]);consumed.append(request[key])
 if request['register_ref']['path'] not in request['argv'] and request['wrapper_ref']['path'] not in request['argv']:raise Stop('Reviewed code absent from actual registration argv')
 canonical=capsule['canonical_copies']
 if [r['role'] for r in canonical]!=['checkpoint','ownership','step_state','commands']:raise Stop('Ordered four canonical copies required')
 if len({r['original_path'].casefold() for r in canonical})!=4:raise Stop('Canonical original path collision')
 eq(canonical,intent['canonical_copies'],'intent desired/original pairs');eq(audit['canonical_copies'],canonical,'actual installed canonical pairs')
 documents=[]
 for item in canonical:
  for key in ['before_ref','after_ref']:
   if item[key] not in members:raise Stop('Unsealed canonical bytes')
  prior=read(item['before_ref']);current=read(item['after_ref']);documents.append((prior,current))
  if item['role'] in ('step_state','commands') and item['before_ref']['sha256']!=item['after_ref']['sha256']:raise Stop('Unrelated canonical bytes changed')
 fields=binding['canonical_fields']
 cp0,cp=documents[0];ow0,ow=documents[1]
 eq(pointer(cp0,fields['checkpoint_revision']),before[0],'original checkpoint');eq(pointer(cp,fields['checkpoint_revision']),after[0],'current checkpoint')
 eq(pointer(ow0,fields['ownership_revision']),before[1],'original ownership');eq(pointer(ow,fields['ownership_revision']),after[1],'current ownership')
 f0=pointer(cp0,fields['failure_origins']);f1=pointer(cp,fields['failure_origins'])
 if not isinstance(f0,list) or not isinstance(f1,list) or len(f0)!=before[2] or len(f1)!=after[2] or f1[:len(f0)]!=f0:raise Stop('Failure prefix/cut changed')
 eq(f1[len(f0):],binding['new_failure_origins'],'fixed new failure cut')
 eq(pointer(cp,fields['scope_ref']),g['spec_ref'],'current checkpoint scope')
 eq(pointer(cp,fields['review_ref']),g['controller_review_ref'],'current checkpoint nonauthor review')
 lease=pointer(ow,fields['lease'])
 eq(lease,{'owner':'codex:/root','status':'EXECUTION_AUTHORIZED_ONCE','scope_ref':g['spec_ref'],'run_nonce':g['run_nonce'],'source_commit':CANDIDATE},'current Root lease')
 payload={k:g[k] for k in ['source_commit','base_commit','run_nonce','output_parent','output_root','spec_ref','controller_refs','tools','normal_helper_ref','debug_helper_ref','caps','resources','resource_files','runtime_catalog_ref','goroot','module_cache','go_tool_images','repository']}
 review=read(g['controller_review_ref'])
 eq(str(no_alias(g['controller_review_ref']['path'])),str(no_alias(binding['controller_review_path'])),'predeclared review path')
 eq(review['schema'],'researchos.w09.finite-controller-bound-review.v1','controller review schema')
 eq(review['reviewer'],'codex:/root/w05_merge_review','controller nonauthor')
 eq(review['decision'],'READY_FOR_ROOT_W09_FINITE_ONCE','controller review decision')
 eq(review['requested_changes'],[],'controller review changes');eq(review['execution_binding'],payload,'full bound inputs')
 eq(review['scope_ref'],g['spec_ref'],'full reviewed spec')
 issuance=read(g['root_issuance_ref'])
 eq(issuance['schema'],'researchos.w09.root-once-issuance.v1','issuance schema');eq(issuance['actor'],'codex:/root','issuer')
 eq(issuance['actual_registration_completed'],True,'actual Root registration')
 eq(issuance['execution_binding'],payload,'issued inputs');eq(issuance['registration_evidence_ref'],g['registration_evidence_ref'],'issued registration')
 eq(issuance['controller_review_ref'],g['controller_review_ref'],'issued nonauthor review')
 eq(g['authority_refs'],[g['registration_evidence_ref'],g['root_issuance_ref']],'authority refs')
 eq(g['independent_review_refs'],[g['controller_review_ref'],capsule['registration_review_ref']],'review refs')
 return list({r['path']:r for r in consumed}.values())

def validate_grant(path,expected_sha):
 if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True:raise Stop('Require pinnedPython -I -S -X utf8')
 actual=file_ref(path)
 if actual['sha256']!=expected_sha:raise Stop('Root grant digest mismatch')
 g=raw_json(verified_raw(actual))
 if g.get('authorized') is not True or g.get('schema')!='researchos.w09.finite-controller-root-grant.v1':raise Stop('No actual Root execution grant')
 if g['source_commit']!=CANDIDATE or g['base_commit']!=BASE:raise Stop('Architecture/source substitution')
 if not re.fullmatch('[0-9a-f]{32}',g['run_nonce']):raise Stop('Exclusive run nonce required')
 if not g['authority_refs'] or not g['independent_review_refs']:raise Stop('Actual authority/review refs required')
 for row in g['authority_refs']+g['independent_review_refs']+g['controller_refs']+[g['spec_ref']]:verify(row)
 spec=raw_json(verified_raw(g['spec_ref']))
 if spec['authorized'] is not False:raise Stop('Specification cannot manufacture authority')
 if g['caps']!=spec['caps']:raise Stop('Cap substitution')
 if g['controller_refs']!=spec['controller_refs']:raise Stop('Controller substitution')
 roles=['common_ref','controller_ref','case_worker_ref','launcher_ref','sealer_ref','normal_helper_ref','debug_helper_ref']
 if g['controller_refs']!=[spec[k] for k in roles] or len({r['path'].casefold() for r in g['controller_refs']})!=7:raise Stop('Exact reviewed mechanism closure required')
 if g['normal_helper_ref']!=spec['normal_helper_ref'] or g['debug_helper_ref']!=spec['debug_helper_ref']:raise Stop('Helper role substitution')
 if file_ref(Path(__file__).resolve())!=spec['common_ref']:raise Stop('Actual common module differs')
 main=file_ref(Path(sys.modules['__main__'].__file__).resolve())
 if main not in [spec[k] for k in ['controller_ref','case_worker_ref','launcher_ref','sealer_ref']]:raise Stop('Actual entry mechanism differs')
 if set(g['tools'])!={'python','go','git','cmd'}:raise Stop('Exact tool roles required')
 for name,row in g['tools'].items():verify(row)
 if str(Path(sys.executable).resolve())!=g['tools']['python']['path']:raise Stop('Actual Python path mismatch')
 if g['tools']['python']!=spec['python_ref'] or g['tools']['go']!=spec['go_ref'] or g['tools']['git']!=spec['git_ref']:raise Stop('Locked tool mismatch')
 parent=no_alias(g['output_parent'])
 if parent!=Path(spec['future_output_parent']):raise Stop('Output parent substitution')
 out=parent/('run-'+g['run_nonce'])
 if g['output_root']!=str(out):raise Stop('Output namespace not direct nonce child')
 for row in g['resource_files']:verify(row)
 if len(g['resource_files'])>200000:raise Stop('Resource inventory cap')
 if g['goroot']!=str(Path(g['tools']['go']['path']).parent.parent):raise Stop('GOROOT not pinned tool root')
 for image in g['go_tool_images']:
  verify(image)
  if not Path(image['path']).is_relative_to(Path(g['goroot'])/'pkg/tool/windows_amd64'):raise Stop('Foreign Go tool image')
 if set(g['resources'])!={'symlink','junction'} or any(type(v) is not bool for v in g['resources'].values()):raise Stop('Explicit resource grants required')
 if g['resources']['junction'] and g['tools']['cmd']!=spec['cmd_ref']:raise Stop('Unpinned cmd resource')
 for pin in list(g['tools'].values())+g['go_tool_images']+[g['normal_helper_ref'],g['debug_helper_ref']]:
  if pin not in g['resource_files'] and pin not in g['controller_refs']:raise Stop('Unbound actual tool/helper')
 for root in [Path(g['goroot']),Path(g['module_cache'])]:
  actual_members={str(x).casefold() for x in walk_files(root)}
  expected_members={x['path'].casefold() for x in g['resource_files'] if Path(x['path']).is_relative_to(root)}
  if actual_members!=expected_members:raise Stop('Incomplete fixed source resource root inventory')
 if g['runtime_catalog_ref'] not in g['resource_files']:raise Stop('Runtime catalog not pinned')
 g['_authorization_input_refs']=root_authority(g,spec,actual)
 g['_grant_ref']=actual
 return g,spec,out

def require_job(result,debug=False):
 c=result.get('job_cleanup',{})
 keys=['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']
 if type(result.get('actual_exit')) is not int or result.get('actual_exit')!=0 or result.get('error') or result.get('timed_out') or not result.get('creation_time_100ns') or not result.get('resumed') or c.get('errors') or any(c.get(k) is not True for k in keys) or c.get('active_processes_last_observed')!=0:raise Stop('Owned child did not complete cleanly')
 if debug and (result.get('debug_capture',{}).get('complete') is not True or c.get('explicit_owned_handles_remaining')!=0):raise Stop('Actual debug-module/process/handle closure incomplete')

class Ledger:
 def __init__(self,path):self.path=Path(path);self.rows={};self.revision=0
 def add(self,paths,group):
  new=[]
  for p in paths:
   row=file_ref(p);key=row['path'].casefold()
   if key in self.rows:
    if self.rows[key]['ref']!=row:raise Stop('Frozen input drift '+row['path'])
   else:self.rows[key]={'ref':row,'group':group};new.append(row)
  self.revision+=1
  write_json(self.path/('%04d-add.json'%self.revision),{'revision':self.revision,'group':group,'new_files':new,'total':len(self.rows)})
 def check(self,label):
  before=time.time();bad=[]
  for row in self.rows.values():
   try:verify(row['ref'])
   except BaseException as e:bad.append({'ref':row['ref'],'error':type(e).__name__+': '+str(e)})
  write_json(self.path/(label+'.json'),{'revision':self.revision,'file_count':len(self.rows),'started_at_unix':before,'ended_at_unix':time.time(),'drift':bad})
  if bad:raise Stop('Frozen input recheck failed')
 def export(self):return list(self.rows.values())

def walk_files(root,cap=200000):
 root=no_alias(root);found=[]
 for current,dirs,files in os.walk(root,followlinks=False):
  no_alias(current)
  for d in dirs:no_alias(Path(current)/d)
  for name in files:
   p=no_alias(Path(current)/name)
   if not p.is_file():raise Stop('Nonregular inventory entry')
   found.append(p)
   if len(found)>cap:raise Stop('File inventory exhausted')
 return sorted(found,key=lambda p:str(p).casefold())

def runtime_snapshot(helper,allowed):
 # This is an actual point-in-time observation, not transient Python load attestation.
 paths={str(Path(sys.executable).resolve())}
 for mod in list(sys.modules.values()):
  for attr in ['__file__','__cached__']:
   value=getattr(mod,attr,None)
   if value and Path(value).is_file():paths.add(str(Path(value).resolve()))
 paths.update(helper.runtime_resource_paths())
 permitted={x['path'].casefold():x for x in allowed}
 rows=[]
 for p in sorted(paths,key=str.casefold):
  if p.casefold() not in permitted:raise Stop('Unbound actual Python/OS resource '+p)
  rows.append(verify(permitted[p.casefold()]))
 return rows

TABLES=('domain_objects','domain_versions','outbox','evidence_origins')
def check_closed_evidence(case,row):
 # File-only read. Never opens SQLite, original or copy.
 case=no_alias(case);db=case/'closed.sqlite';proof=case/'closed-proof.json'
 before=file_ref(db);e=raw_json(proof.read_bytes())
 if e.get('sha256')!='sha256:'+before['sha256'] or e.get('bytes')!=before['bytes']:raise Stop('Closed copy hash differs')
 if e.get('original_close_observed') is not True or e.get('checkpoint_busy')!=0 or e.get('original_and_copy_sidecars_absent') is not True or e.get('copy_not_opened_as_database') is not True or e.get('case_failed') is not False:raise Stop('Closed copy lifecycle assertion absent')
 for suffix in ('-wal','-shm'):
  if Path(str(db)+suffix).exists():raise Stop('Closed copy sidecar present')
 refs=[before,file_ref(proof)]
 for name in row['expected_evidence_json']:
  path=case/name;value=raw_json(path.read_bytes());refs.append(file_ref(path))
  if name==row.get('four_table_evidence_file'):
   counts=value['counts']
   for table in TABLES:
    n=counts[table];ms=counts[table+'_row_multiset'];rows=ms['rows'];cols=ms['columns']
    if type(n) is not int or n<0 or n!=len(rows) or rows!=sorted(rows) or not cols or len(cols)!=len(set(cols)):raise Stop('Four-table row multiset shape')
    for encoded in rows:
     values=raw_json(encoded)
     if not isinstance(values,list) or len(values)!=len(cols):raise Stop('Four-table encoded column cardinality')
 # Explicitly SQL driver-value JSON, not SQLite typeof/implicit-rowid/full-database equivalence.
 if file_ref(db)!=before:raise Stop('Closed copy changed during file-only seal')
 return refs
