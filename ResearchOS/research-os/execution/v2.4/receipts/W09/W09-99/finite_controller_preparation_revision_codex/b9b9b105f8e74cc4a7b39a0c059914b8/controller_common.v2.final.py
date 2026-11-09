"""Receipt-only controller support. No product/native execution at import."""
import base64, contextlib, hashlib, json, os, re, stat, sys, time, types
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
 verify(expected)
 if str(path)!=expected['path']:raise Stop('Helper path mismatch')
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected['sha256'] or len(raw)!=expected['bytes']:raise Stop('Helper drift before raw compile')
 mod=types.ModuleType(Path(path).stem);mod.__file__=str(path)
 sys.modules['w09_receipt_'+Path(path).stem]=mod
 exec(compile(raw,str(path),'exec'),mod.__dict__)
 return mod

def existing_ref(path):
 return file_ref(path) if path is not None and Path(path).is_file() else None

AUTHORIZATION_PATHS=[]
def read_bound(ref):
 verify(ref);raw=Path(ref['path']).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=ref['sha256'] or len(raw)!=ref['bytes']:raise Stop('Read-after-pin drift')
 if ref['path'] not in AUTHORIZATION_PATHS:AUTHORIZATION_PATHS.append(ref['path'])
 return raw_json(raw)

def exact(value,keys,label):
 if type(value) is not dict or set(value)!=set(keys):raise Stop('Exact shape required: '+label)

def pointer(value,p):
 if type(p) is not str or not p.startswith('/'):raise Stop('Explicit JSON pointer required')
 for token in p[1:].split('/'):
  token=token.replace('~1','/').replace('~0','~')
  value=value[int(token)] if isinstance(value,list) else value[token]
 return value

def validate_grant(path,expected_sha):
 if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True or not sys.dont_write_bytecode:raise Stop('Require -I -S -X utf8 and disabled bytecode writes')
 grant_ref=file_ref(path)
 if grant_ref['sha256']!=expected_sha:raise Stop('Exact grant hash required')
 g=read_bound(grant_ref)
 if g.get('schema')!='researchos.w09.finite-controller-root-grant.v2' or g.get('actor')!='codex:/root' or g.get('authorized') is not True or g.get('actual_registration_completed') is not True or g.get('status')!='ROOT_REGISTERED_EXECUTION_AUTHORIZED':raise Stop('Future Root grant missing')
 required=['scope_ref','spec_ref','controller_review_ref','registration_review_ref','registration_audit_ref','registration_intent_ref','registration_invocation_ref','registration_manifest_ref','registration_register_ref','registration_wrapper_ref','canonical_original_refs','canonical_desired_refs','canonical_copy_refs','resource_catalog_ref','runtime_catalog_ref','source_catalog_ref','source_compile_basis','combined_source_closure_ref']
 if any(g.get(k) is None for k in required):raise Stop('Unbound future authority/source/resource field')
 s=read_bound(g['spec_ref']);scope=read_bound(g['scope_ref']);review=read_bound(g['controller_review_ref'])
 if s['authorized'] is not False or s['status']!='PREPARATION_ONLY_NOT_RUN':raise Stop('Preparation cannot self-authorize')
 if scope.get('schema')!='researchos.w09.finite-root-scope.v2' or scope.get('actor')!='codex:/root' or scope.get('status')!='ROOT_SCOPE_REGISTERED' or scope.get('spec_ref')!=g['spec_ref']:raise Stop('Root scope identity')
 if review.get('schema')!='researchos.w09.finite-controller-independent-review.v2' or review.get('decision')!='READY_FOR_ROOT_FINITE_PREPARATION_AND_EXECUTION_WITH_EXPLICIT_INPUTS' or review.get('requested_changes')!=[] or review.get('actual_execution') is not False or review.get('scope_ref')!=g['scope_ref'] or review.get('spec_ref')!=g['spec_ref'] or review.get('controller_refs')!=s['controller_refs'] or review.get('reviewer') in (None,'codex:/root','codex:/root/command_queue_impl','codex:/root/sources_parent_impl'):raise Stop('Exact nonauthor controller/scope review required')
 if g.get('repository')!=scope.get('repository') or g.get('repository')!='D:\\作品集\\ResearchOS\\research-os':raise Stop('Exact public repository required')
 if g['source_commit']!=CANDIDATE or g['base_commit']!=BASE or scope.get('source_commit')!=CANDIDATE or scope.get('base_commit')!=BASE:raise Stop('Pinned candidate/base required; combined source needs separate revision')
 if g['source_compile_basis']!='FROZEN_CD0_ON_2CDB_NOT_CURRENT_MAIN' or scope.get('source_compile_basis')!=g['source_compile_basis']:raise Stop('Explicit compile basis required')
 # The explicitly pinned closure is the source export plan, NOT a claim of generated compiler evidence.
 basis=read_bound(g['combined_source_closure_ref'])
 if basis.get('source_commit')!=CANDIDATE or basis.get('current_combined_Main') is not False or basis.get('source_catalog_ref')!=g['source_catalog_ref'] or basis.get('actual_compilation_closure') is not None or scope.get('combined_source_closure_ref')!=g['combined_source_closure_ref']:raise Stop('Source closure basis substitution')
 for key in ['caps','controller_refs','source_catalog_ref']:
  if g.get(key)!=s.get(key) or scope.get(key)!=s.get(key):raise Stop('Frozen spec field differs: '+key)
 if scope.get('controller_review_actor')!=review['reviewer']:raise Stop('Reviewer actor binding')
 before=scope.get('expected_before');after=scope.get('expected_after')
 if not isinstance(before,list) or not isinstance(after,list) or len(before)!=3 or len(after)!=3 or any(type(n) is not int or n<0 for n in before+after) or after[0]!=before[0]+1 or after[1]!=before[1]+1 or after[2]<before[2]:raise Stop('Explicit future registration tuple required')
 manifest=read_bound(g['registration_manifest_ref']);members=manifest.get('members')
 if not isinstance(members,list) or manifest.get('member_count')!=len(members):raise Stop('Sealed registration manifest shape')
 if len(members)>4096:raise Stop('Registration manifest cap')
 bypath={}
 for pin in members:
  if Path(pin['path']) in {Path(g['repository'])/'execution/v2.4'/n for n in ['checkpoint.json','path_ownership.json','step_state.json','commands.json']}:raise Stop('Only immutable canonical copies permitted, not live files')
  if pin['path'].casefold() in bypath:raise Stop('Duplicate registration manifest path')
  read_bound_file(pin);bypath[pin['path'].casefold()]=pin
 def sealed(pin):
  if bypath.get(pin['path'].casefold())!=pin:raise Stop('Required registration object not sealed')
 for key in ['registration_audit_ref','registration_intent_ref','registration_invocation_ref','registration_register_ref','registration_wrapper_ref']:
  sealed(g[key])
 audit=read_bound(g['registration_audit_ref']);intent=read_bound(g['registration_intent_ref']);inv=read_bound(g['registration_invocation_ref']);rr=read_bound(g['registration_review_ref'])
 # A future Root adapter must preserve and expose the ACTUAL source documents; this is a contract, not a guessed current receipt shape.
 if audit.get('schema')!='researchos.w09.actual-registration-evidence.v2' or audit.get('actor')!='codex:/root' or audit.get('completed') is not True or audit.get('expected_before')!=before or audit.get('actual_after')!=after or audit.get('scope_ref')!=g['scope_ref'] or audit.get('controller_review_ref')!=g['controller_review_ref'] or audit.get('intent_ref')!=g['registration_intent_ref'] or audit.get('actual_invocation_ref')!=g['registration_invocation_ref']:raise Stop('Actual Root registration evidence mismatch')
 if rr.get('schema')!='researchos.root-registration-source-review.v1' or rr.get('decision')!='REGISTRATION_DRAFT_REVIEWED_FOR_ROOT_EXECUTION' or rr.get('requested_changes')!=[] or rr.get('actual_registration_executed') is not False or rr.get('expected_before')!=before or rr.get('expected_after')!=after or rr.get('register_sha256')!=g['registration_register_ref']['sha256'] or rr.get('wrapper_sha256')!=g['registration_wrapper_ref']['sha256'] or rr.get('reviewer') in (None,'codex:/root'):raise Stop('Independent actual registration draft review mismatch')
 contract=scope.get('actual_invocation_contract')
 exact(contract,['argv_pointer','exact_argv','native_exit_pointer','outer_exit_pointer'],'actual invocation contract')
 if pointer(inv,contract['argv_pointer'])!=contract['exact_argv'] or pointer(inv,contract['native_exit_pointer'])!=0 or type(pointer(inv,contract['native_exit_pointer'])) is not int or pointer(inv,contract['outer_exit_pointer'])!=0 or type(pointer(inv,contract['outer_exit_pointer'])) is not int:raise Stop('Actual registered invocation argv/native/outer evidence')
 if g['registration_wrapper_ref']['path'] not in contract['exact_argv'] and g['registration_register_ref']['path'] not in contract['exact_argv']:raise Stop('Registration invocation not original reviewed controller')
 originals=g['canonical_original_refs'];desired=g['canonical_desired_refs'];copies=g['canonical_copy_refs']
 labels=['checkpoint.json','path_ownership.json','step_state.json','commands.json']
 if any(type(v) is not list or len(v)!=4 for v in [originals,desired,copies]):raise Stop('Four ordered canonical snapshots required')
 if intent.get('schema')!='researchos.w09.registration-intent-binding.v2' or intent.get('original_refs')!=originals or intent.get('desired_refs')!=desired or intent.get('scope_ref')!=g['scope_ref'] or intent.get('expected_before')!=before or intent.get('expected_after')!=after or audit.get('canonical_copy_refs')!=copies:raise Stop('Intent/original/desired relationship missing')
 original_docs=[];copy_docs=[]
 for i,label in enumerate(labels):
  for pin in [originals[i],desired[i],copies[i]]:sealed(pin)
  if copies[i].get('canonical_name')!=label or originals[i].get('canonical_name')!=label or desired[i].get('canonical_name')!=label:raise Stop('Ordered canonical role mismatch')
  if (copies[i]['sha256'],copies[i]['bytes'])!=(desired[i]['sha256'],desired[i]['bytes']):raise Stop('Actual canonical copy not intended committed bytes')
  original_docs.append(read_bound(originals[i]));copy_docs.append(read_bound(copies[i]))
 if [original_docs[0]['revision'],original_docs[1]['revision'],len(original_docs[0]['failure_counters'])]!=before or [copy_docs[0]['revision'],copy_docs[1]['revision'],len(copy_docs[0]['failure_counters'])]!=after:raise Stop('Canonical actual counter tuple')
 if copy_docs[0]['failure_counters'][:before[2]]!=original_docs[0]['failure_counters'] or any((originals[i]['sha256'],originals[i]['bytes'])!=(copies[i]['sha256'],copies[i]['bytes']) for i in [2,3]):raise Stop('Failure prefix/ST/CM changed')
 wip=copy_docs[0]['work_in_progress'];binding=scope.get('checkpoint_binding_keys')
 exact(binding,['scope','review'],'checkpoint binding keys')
 if wip.get(binding['scope'])!=g['scope_ref'] or wip.get(binding['review'])!=g['controller_review_ref']:raise Stop('Actual canonical grant references absent')
 for ref in s['controller_refs']+[s['source_review_ref'],s['roster_ref']]:read_bound_file(ref)
 if file_ref(Path(__file__)) not in s['controller_refs']:raise Stop('Current common source not pinned')
 catalog=read_bound(g['source_catalog_ref'])
 if catalog['source_commit']!=CANDIDATE or catalog['base_commit']!=BASE or catalog['file_count']!=len(catalog['files']):raise Stop('Exact public source catalog')
 resources=read_bound(g['resource_catalog_ref']);runtime=read_bound(g['runtime_catalog_ref'])
 if resources.get('complete_public_input_inventory') is not True or not resources.get('files') or g.get('resource_files')!=resources['files'] or scope.get('resource_catalog_ref')!=g['resource_catalog_ref'] or scope.get('runtime_catalog_ref')!=g['runtime_catalog_ref']:raise Stop('Future resource inventory missing')
 if runtime.get('point_in_time_only') is not True or runtime.get('full_python_lifecycle_claim') is not False or not runtime.get('files'):raise Stop('Honest explicit runtime inventory required')
 for pin in resources['files']+runtime['files']:read_bound_file(pin)
 resources_by_path={r['path'].casefold():r for r in resources['files']}
 if len(resources_by_path)!=len(resources['files']) or len(resources_by_path)>200000:raise Stop('Resource duplicates/cap')
 if any(resources_by_path.get(r['path'].casefold())!=r for r in runtime['files']):raise Stop('Runtime outside approved public inventory')
 for name in ['python','go','git','cmd']:
  if g['tools'][name]!=s[name+'_ref']:raise Stop('Locked tool substitution')
 for pin in list(g['tools'].values())+g['go_tool_images']+g['git_images']:
  if resources_by_path.get(pin['path'].casefold())!=pin:raise Stop('Unapproved actual executable')
 if g['tools']['git'] not in g['git_images'] or not g['go_tool_images']:raise Stop('Explicit Git shim and Go child-image closure required')
 if g['normal_helper_ref']!=s['normal_helper_ref'] or g['debug_helper_ref']!=s['debug_helper_ref']:raise Stop('Debug/helper substitution')
 if str(Path(sys.executable).resolve())!=g['tools']['python']['path']:raise Stop('Actual interpreter mismatch')
 for pin in runtime_source_snapshot(resources['files']):read_bound_file(pin)
 if g['goroot']!=str(Path(g['tools']['go']['path']).parent.parent):raise Stop('GOROOT mismatch')
 for root in [Path(g['goroot']),Path(g['module_cache'])]:
  if {str(p).casefold() for p in walk_files(root)}!={r['path'].casefold() for r in resources['files'] if Path(r['path']).is_relative_to(root)}:raise Stop('Incomplete Go source/module resource closure')
 if set(g['resources'])!={'symlink','junction'} or any(type(v) is not bool for v in g['resources'].values()) or scope.get('resources')!=g['resources']:raise Stop('Exact OS-dependent grant')
 if scope.get('os_hold_policy')!={'not_granted':'HOLD','granted_unexpected_failure':'STOP'}:raise Stop('Unexpected resource failures cannot be HOLD')
 if not re.fullmatch('[0-9a-f]{32}',g['run_nonce']):raise Stop('Nonce missing')
 parent=no_alias(g['output_parent'])
 if str(parent)!=scope.get('output_parent') or str(parent)!=s['future_output_parent']:raise Stop('Output boundary')
 out=parent/('run-'+g['run_nonce'])
 if g['output_root']!=str(out):raise Stop('Unique direct output leaf')
 g['_authorization_paths']=list(AUTHORIZATION_PATHS);g['_grant_ref']=grant_ref;g['_scope']=scope
 return g,s,out

def read_bound_file(ref):
 pin=verify(ref)
 if pin['path'] not in AUTHORIZATION_PATHS:AUTHORIZATION_PATHS.append(pin['path'])
 return pin

def runtime_source_snapshot(allowed):
 permitted={x['path'].casefold():x for x in allowed};paths={str(Path(sys.executable).resolve())}
 for mod in list(sys.modules.values()):
  for attr in ['__file__','__cached__']:
   p=getattr(mod,attr,None)
   if p and Path(p).is_file():paths.add(str(Path(p).resolve()))
 rows=[]
 for p in sorted(paths,key=str.casefold):
  if p.casefold() not in permitted:raise Stop('Unapproved actual Python source/pyc '+p)
  rows.append(verify(permitted[p.casefold()]))
 return rows

def fault(e):return {'type':type(e).__name__,'message':str(e)}

class FirstCause:
 def __init__(self):self.primary=None;self.secondary=[]
 def record(self,e,phase):
  item={'phase':phase,**fault(e)}
  if self.primary is None:self.primary=item
  else:self.secondary.append(item)
 def attempt(self,phase,fn):
  try:return fn()
  except BaseException as e:self.record(e,phase);return None
 def raise_if_any(self):
  if self.primary:raise Stop(self.primary['phase']+': '+self.primary['type']+': '+self.primary['message'])


def require_job(result,debug=False):
 c=result.get('job_cleanup',{})
 keys=['unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','job_idle_confirmed','primary_exit_confirmed','handles_closed']
 if result.get('actual_exit')!=0 or result.get('error') or result.get('timed_out') or not result.get('creation_time_100ns') or not result.get('resumed') or c.get('errors') or any(c.get(k) is not True for k in keys) or c.get('active_processes_last_observed')!=0:raise Stop('Owned child did not complete cleanly')
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
