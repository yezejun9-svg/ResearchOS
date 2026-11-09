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
 verify(expected)
 if str(path)!=expected['path']:raise Stop('Helper path mismatch')
 mod=types.ModuleType(Path(path).stem);mod.__file__=str(path)
 exec(compile(Path(path).read_bytes(),str(path),'exec'),mod.__dict__)
 return mod

def validate_grant(path,expected_sha):
 if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True:raise Stop('Require pinnedPython -I -S -X utf8')
 actual=file_ref(path)
 if actual['sha256']!=expected_sha:raise Stop('Root grant digest mismatch')
 g=raw_json(Path(path).read_bytes())
 if g.get('authorized') is not True or g.get('schema')!='researchos.w09.finite-controller-root-grant.v1':raise Stop('No actual Root execution grant')
 if g['source_commit']!=CANDIDATE or g['base_commit']!=BASE:raise Stop('Architecture/source substitution')
 if not re.fullmatch('[0-9a-f]{32}',g['run_nonce']):raise Stop('Exclusive run nonce required')
 if not g['authority_refs'] or not g['independent_review_refs']:raise Stop('Actual authority/review refs required')
 for row in g['authority_refs']+g['independent_review_refs']+g['controller_refs']+[g['spec_ref']]:verify(row)
 spec=raw_json(Path(g['spec_ref']['path']).read_bytes())
 if spec['authorized'] is not False:raise Stop('Specification cannot manufacture authority')
 if g['caps']!=spec['caps']:raise Stop('Cap substitution')
 if g['controller_refs']!=spec['controller_refs']:raise Stop('Controller substitution')
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
 return g,spec,out

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
