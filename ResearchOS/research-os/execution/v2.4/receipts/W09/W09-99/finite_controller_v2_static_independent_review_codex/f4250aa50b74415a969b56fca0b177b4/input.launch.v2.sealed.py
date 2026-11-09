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

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--grant',required=True);ap.add_argument('--grant-sha256',required=True);a=ap.parse_args()
 g,s,out=validate_grant(a.grant,a.grant_sha256)
 if file_ref(__file__)!=s['launcher_ref']:raise Stop('Launcher exact pin')
 outer=out.with_name(out.name+'-outer')
 if out.exists() or outer.exists():raise Stop('Prior output exists; no reuse/retry')
 outer.mkdir();cause=FirstCause();helper=None;result=None;ledger=Ledger(outer/'vectors');argv=[g['tools']['python']['path'],*FLAGS,s['controller_ref']['path'],'--grant',str(Path(a.grant)),'--grant-sha256',a.grant_sha256]
 env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
 started=time.time();write_json(outer/'invocation.started.json',{'actualargv':argv,'cwd':str(PREP),'env':env,'grant_ref':g['_grant_ref'],'started_at_unix':started,'actual_native_exit':None,'timeout_seconds':15000,'cleanup_observation_seconds':5})
 try:
  ledger.add(g['_authorization_paths']+[r['path'] for r in g['resource_files']],'actual-authorization-public-inputs');ledger.check('before')
  write_json(outer/'runtime.source.before.json',runtime_source_snapshot(g['resource_files']))
  helper=trusted_module(g['normal_helper_ref']['path'],g['normal_helper_ref'])
  write_json(outer/'runtime.before.json',runtime_snapshot(helper,g['resource_files']))
  with (outer/'stdout.raw').open('xb') as so,(outer/'stderr.raw').open('xb') as se:result=helper.run_owned(argv,str(PREP),env,so,se,15000)
  require_job(result)
 except BaseException as e:cause.record(e,'outer-controller')
 finally:
  cause.attempt('outer-after-inputs',lambda:ledger.check('after'))
  cause.attempt('outer-runtime-source-after',lambda:write_json(outer/'runtime.source.after.json',runtime_source_snapshot(g['resource_files'])))
  if helper:cause.attempt('outer-runtime-after',lambda:write_json(outer/'runtime.after.json',runtime_snapshot(helper,g['resource_files'])))
  cause.attempt('outer-input-vector',lambda:write_json(outer/'inputs.final.json',ledger.export()))
  record={'actualargv':argv,'cwd':str(PREP),'started_at_unix':started,'ended_at_unix':time.time(),'owned_result':result,'actual_native_controller_exit':None if result is None else result.get('actual_exit'),'stdout_ref':existing_ref(outer/'stdout.raw'),'stderr_ref':existing_ref(outer/'stderr.raw'),'first_error':cause.primary,'secondary_errors':cause.secondary,'source_acceptance':False}
  write_json(outer/'completion.json',record)
  if cause.primary:write_json(outer/'failure.origin.json',{'first_error':cause.primary,'secondary_errors':cause.secondary,'actual_native_exit':record['actual_native_controller_exit'],'counter_reset':False})
 cause.raise_if_any()
if __name__=='__main__':
 try:main()
 except BaseException as e:
  # Pre-authority/pre-output failures remain on actual stderr for the Root-owned caller.
  print(json.dumps({'schema':'researchos.w09.entry-failure.v2','error_type':type(e).__name__,'message':str(e),'actual_child_native_exit':None,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
  raise

