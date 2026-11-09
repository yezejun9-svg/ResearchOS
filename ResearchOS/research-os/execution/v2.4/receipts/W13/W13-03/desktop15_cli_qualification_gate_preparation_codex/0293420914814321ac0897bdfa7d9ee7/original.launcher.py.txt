"""PREPARATION ONLY. Future sole-Root, independently reviewed, once-only launcher."""
import sys
sys.dont_write_bytecode=True
import argparse,datetime,hashlib,json,os,time,traceback,types
from pathlib import Path

ROOT=Path('D:/作品集/ResearchOS/research-os')
PARENT=ROOT/'execution/v2.4/receipts/W13/W13-03/desktop_exact15_integration_executor_codex'
DEADLINE=None
HASHED=0

def require(v,m):
 if not v:raise RuntimeError(m)

def safe(value,repo=False):
 p=Path(value)
 require(p.is_absolute() and '..' not in p.parts and p.resolve()==p.absolute(),'Absolute no-alias path required')
 if repo:require(p.is_relative_to(ROOT) and p!=ROOT,'Own repository boundary')
 for q in [p,*p.parents]:
  if os.path.lexists(q):require(not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400),'Reparse ancestor')
 return p

def raw(path):
 global HASHED
 p=safe(path);require(p.stat().st_size<=256*1024*1024,'Per-file256MiB')
 chunks=[]
 with p.open('rb') as f:
  while True:
   require(DEADLINE is not None and time.monotonic()<DEADLINE,'Outer evidence observation deadline')
   b=f.read(1024*1024)
   if not b:break
   HASHED+=len(b);require(HASHED<=32*1024**3,'Outer32GiB read bound');chunks.append(b)
 return b''.join(chunks)

def pin(path):
 p=safe(path);b=raw(p);return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}

def verify(ref):
 require(isinstance(ref,dict) and {'path','sha256','bytes'}<=set(ref),'Reference shape')
 b=raw(ref['path']);require(type(ref['bytes']) is int and len(b)==ref['bytes'] and hashlib.sha256(b).hexdigest()==ref['sha256'],'Immutable pin mismatch');return b

def parse(b):
 def pairs(items):
  out={}
  for k,v in items:
   require(k not in out,'Duplicate JSON key');out[k]=v
  return out
 def bad(v):raise ValueError('Nonfinite JSON '+v)
 return json.loads(b.decode('utf-8','strict'),object_pairs_hook=pairs,parse_constant=bad)

def save(out,name,value):
 with (out/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))

def main():
 global DEADLINE
 DEADLINE=time.monotonic()+1200
 out=None;phase='ARGUMENTS_AND_FLAGS';first=None;secondary=[];result=None;phase_native=None;controller=None;helper=None;s=None;argv=None;env=None;runtime=None
 def failure(exc):return {'phase':phase,'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'actual_native_exit':phase_native}
 def attempt(label,fn):
  nonlocal first
  try:return fn()
  except BaseException as exc:
   detail={'phase':label,'type':type(exc).__name__,'message':str(exc),'traceback':traceback.format_exc(),'actual_native_exit':None}
   if first is None:first=detail
   else:secondary.append(detail)
   print(json.dumps({'first_error':first,'secondary_error':detail},ensure_ascii=False),file=sys.stderr)
 try:
  require(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize,'Pinned Python -I -S -X utf8')
  ap=argparse.ArgumentParser()
  for n in ['scope','scope-sha256','grant','grant-sha256']:ap.add_argument('--'+n,required=True)
  a=ap.parse_args();scopepath=safe(a.scope,True);grantpath=safe(a.grant,True)
  sb=raw(scopepath);gb=raw(grantpath)
  require(hashlib.sha256(sb).hexdigest()==a.scope_sha256 and hashlib.sha256(gb).hexdigest()==a.grant_sha256,'Scope/grant bytes')
  s=parse(sb);g=parse(gb)
  require(s['authorized'] is True and g['authorized'] is True and g['actual_registration_completed'] is True and s['owner']==g['actor']=='codex:/root','No actual Root grant')
  phase='SAFE_OWN_OUTPUT'
  target=safe(s['new_output_root'],True);safe(PARENT,True)
  require(target.parent==PARENT and target.name==s['operation_uuid'] and len(target.name)==32 and all(c in '0123456789abcdef' for c in target.name),'Exclusive UUID output identity')
  candidate=safe(target.with_name(target.name+'-outer'),True)
  require(not os.path.lexists(target) and not os.path.lexists(candidate),'No retry or existing output')
  candidate.mkdir(exist_ok=False);out=candidate
  save(out,'started.json',{'actual_launcher_argv':[sys.executable,*sys.orig_argv[1:]],'cwd':str(Path.cwd()),'phase':phase,'automatic_retry':False,'counter_reset':False,'actual_native_exit':None})
  phase='PIN_CONTROLLER_AND_PYTHON_SOURCES'
  require(s['launcher_ref']['path']==str(Path(__file__).resolve()),'Launcher exact identity');verify(s['launcher_ref'])
  source=verify(s['controller_ref']);lock=parse(verify(s['toolchain_lock_ref']));python=lock['tools']['python']
  require(safe(sys.executable)==safe(python['path']) and pin(sys.executable)['sha256']==python['sha256'],'Python identity')
  catalog=parse(verify(s['runtime_resources_ref']))
  expected={str(safe(x['path'])).casefold():x for x in catalog['files']}
  hr=s['owned_process_helper_ref']
  require(hr['sha256']=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad','Exact owned helper')
  for item in [s['launcher_ref'],s['controller_ref'],hr]:expected[str(safe(item['path'])).casefold()]=item
  Path(__file__).resolve().as_uri() # Prime standard-library URI dependency before the first point observation.
  def observe(name,with_dll):
   paths={sys.executable}
   for module in list(sys.modules.values()):
    for field in ['__file__','__cached__']:
     p=getattr(module,field,None)
     if p and Path(p).is_file():paths.add(p)
   if with_dll:paths.update(helper.runtime_resource_paths())
   rows=[]
   for p in sorted(paths):
    q=safe(p);r=expected.get(str(q).casefold());require(r is not None,'Unpinned outer Python/OS runtime '+str(q));verify(r);rows.append(pin(q))
   save(out,name+'.json',{'kind':'ACTUAL_POINT_IN_TIME_NOT_LIFECYCLE','with_loaded_OS_modules':with_dll,'files':rows})
  runtime=lambda name:observe(name,helper is not None)
  observe('runtime.source.before_import',False)
  controller=types.ModuleType('desktop15_authority_readonly');controller.__file__=s['controller_ref']['path'];sys.modules[controller.__name__]=controller
  exec(compile(source,controller.__file__,'exec'),controller.__dict__)
  controller.DEADLINE=DEADLINE;controller.BASE=s['expected_cli43_head']
  phase='ACTUAL_ROOT_AUTHORITY_BEFORE_CHILD'
  sref=pin(scopepath);sref['path']=g['scope_ref']['path']
  require(controller.bounded(g['scope_ref']['path'])==scopepath,'Grant exact scope path')
  require(isinstance(s['expected_cli43_head'],str) and len(s['expected_cli43_head'])==40,'Actual completed CLI43 required')
  copies=controller.grant_check(s,sref,g) # Pure read/hash. Never call execute or any Git/Go command here.
  immutable=[pin(scopepath),pin(grantpath),s['launcher_ref'],s['controller_ref'],s['toolchain_lock_ref'],s['runtime_resources_ref'],hr,*controller.READS.values()]
  for r in immutable:verify(r)
  save(out,'authority.verified.json',{'scope_ref':sref,'grant_ref':pin(grantpath),'canonical_copies':copies,'consumed_immutable_inputs':immutable,'actual_root_chain_checked_before_child':True,'product_acceptance':False})
  phase='PIN_AND_LOAD_OWNED_HELPER'
  observe('runtime.source.prehelper',False)
  helper=types.ModuleType('desktop15_owned_outer');helper.__file__=hr['path'];sys.modules[helper.__name__]=helper
  exec(compile(verify(hr),hr['path'],'exec'),helper.__dict__)
  runtime('runtime.before')
  save(out,'immutable-inputs.before.json',immutable)
  argv=[python['path'],'-I','-S','-X','utf8',s['controller_ref']['path'],'--scope',str(scopepath),'--scope-sha256',a.scope_sha256,'--grant',str(grantpath),'--grant-sha256',a.grant_sha256]
  env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']}
  timeout=min(1200,max(0,DEADLINE-time.monotonic()));require(timeout>0,'Outer deadline before child')
  save(out,'inner.started.json',{'argv':argv,'cwd':str(Path(__file__).parent),'environment':env,'timeout_seconds':timeout,'timeout_cap_seconds':1200,'cleanup_seconds':5,'automatic_retry':False,'counter_reset':False})
  phase='OWNED_CONTROLLER'
  with (out/'stdout.raw').open('xb') as so,(out/'stderr.raw').open('xb') as se:result=helper.run_owned(argv,str(Path(__file__).parent),env,so,se,timeout)
  phase='OWNED_RESULT_EVIDENCE';phase_native=None
  save(out,'owned-result.json',{'owned_result':result,'actual_native_controller_exit':result.get('actual_exit') if isinstance(result,dict) else None})
  phase='OWNED_CONTROLLER_RESULT';phase_native=result.get('actual_exit') if isinstance(result,dict) else None
  controller.job_ok(result)
  phase='POST_CHILD_INPUT_GUARDS';phase_native=None
  for r in immutable:verify(r)
  for item in copies:require(raw(ROOT/item['canonical_path'])==verify(item['ref']),'Canonical changed during exact integration')
  save(out,'immutable-inputs.after.json',immutable)
 except BaseException as exc:
  first=failure(exc)
  print(json.dumps({'first_error':first,'safe_output':str(out) if out else None,'last_child_observation':result,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
 finally:
  if out is not None:
   if runtime is not None:attempt('runtime.after',lambda:runtime('runtime.after'))
   attempt('invocation.final',lambda:save(out,'invocation.final.json',{'argv':argv,'environment':env,'owned_result':result,'actual_native_controller_exit':result.get('actual_exit') if isinstance(result,dict) else None,'current_phase_native_exit':None,'first_error':first,'secondary_errors':secondary,'source_acceptance':False,'automatic_retry':False,'counter_reset':False}))
   if first is None:attempt('completed',lambda:save(out,'completed.json',{'status':'OWNED_CONTROLLER_EXIT_ZERO_PENDING_EVIDENCE_REVIEW','owned_result':result,'actual_native_controller_exit':result.get('actual_exit') if isinstance(result,dict) else None,'source_acceptance':False,'formal_increment':0}))
   if first is not None:attempt('failure.origin',lambda:save(out,'failure.origin.json',{'first_error':first,'secondary_errors':secondary,'last_child_observation':result,'automatic_retry':False,'counter_reset':False}))
   def seal():
    entries=[pin(p) for p in sorted(out.iterdir()) if p.is_file()]
    save(out,'manifest.json',{'entries':entries,'count':len(entries),'excluded_only':str(out/'manifest.json')})
   attempt('manifest',seal)
   # Any finalization failure remains observable even if the filesystem cannot accept another receipt.
   if first is not None:print(json.dumps({'first_error':first,'secondary_errors':secondary,'last_child_observation':result,'actual_native_launcher_exit':None,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
 return 1 if first is not None else 0

if __name__=='__main__':raise SystemExit(main())
