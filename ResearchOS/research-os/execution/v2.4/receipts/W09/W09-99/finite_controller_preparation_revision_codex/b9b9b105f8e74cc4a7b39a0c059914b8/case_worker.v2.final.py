import sys
sys.dont_write_bytecode=True
import argparse, contextlib, hashlib, io, json, os, re, stat, time, types
from pathlib import Path
# Hash actual source bytes BEFORE compile; no importlib loader and no pyc read for controller modules.
_common_path=Path(__file__).resolve().parent/'controller_common.v2.final.py'
_common_raw=_common_path.read_bytes()
if hashlib.sha256(_common_raw).hexdigest()!='f9b673e52caf9ad3a781171e3681fee1cc1ef523e64d7dd979bbb28bbf41cc3d':raise RuntimeError('Pinned common source mismatch before import')
if not sys.flags.isolated or not sys.flags.no_site or sys._xoptions.get('utf8') is not True:raise RuntimeError('Pinned -I -S -X utf8 required')
_common=types.ModuleType('w09_common_v2');_common.__file__=str(_common_path);sys.modules[_common.__name__]=_common
exec(compile(_common_raw,str(_common_path),'exec'),_common.__dict__)
globals().update({k:v for k,v in _common.__dict__.items() if not k.startswith('__')})

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--request',required=True);ap.add_argument('--sha256',required=True);a=ap.parse_args()
 pin=file_ref(a.request)
 if pin['sha256']!=a.sha256:raise Stop('Case request changed')
 r=raw_json(Path(a.request).read_bytes())
 if r.get('schema')!='researchos.w09.owned-case-request.v2':raise Stop('Case request schema')
 g,s,out=validate_grant(r['grant_ref']['path'],r['grant_ref']['sha256'])
 if r['self_ref']!=s['case_worker_ref'] or file_ref(__file__)!=r['self_ref'] or r['python_ref']!=g['tools']['python'] or r['debug_helper_ref']!=g['debug_helper_ref']:raise Stop('Worker/actual grant pin')
 output=no_alias(r['output_dir'])
 if not output.is_relative_to(out/'native') or Path(a.request)!=output/'case-request.json':raise Stop('Case output boundary')
 if r['timeout']!=120 or r['process_cap'] not in (1,2):raise Stop('Case caps')
 argv=r['argv'];matches=[x for x in s['roster'] if argv[1:]==['-test.run',x['test_run'],'-test.v','-test.count=1','-test.failfast','-test.timeout=120s']]
 if len(matches)!=1:raise Stop('Exact finite selector required')
 planned=matches[0];package='adapter' if planned['file'].startswith('adapters/') else 'domain'
 if argv[0]!=str(out/(package+'.test.exe')):raise Stop('Foreign case executable')
 expected_cap=2 if not planned['new'] and 'junction' in planned['requires_resource'] else 1
 if r['process_cap']!=expected_cap:raise Stop('Case process bound')
 allowed={x['path'].casefold():x for x in r['allowed_module_files']}
 for image in r['images']:
  if allowed.get(image['path'].casefold())!=image:raise Stop('Case image not in frozen full vector')
  verify(image)
 if file_ref(argv[0])['sha256']!=r['expected_image']['sha256']:raise Stop('Actual case image')
 cause=FirstCause();debug=None;result=None;ledger=Ledger(output/'worker-vectors')
 write_json(output/'worker.started.json',{'request_ref':pin,'grant_ref':r['grant_ref'],'actualargv':argv,'actual_native_exit':None,'selector':planned['selector']})
 try:
  ledger.add(g['_authorization_paths']+[pin['path']]+[x['path'] for x in r['allowed_module_files']],'worker-actual-inputs');ledger.check('before')
  write_json(output/'worker.runtime.source.before.json',runtime_source_snapshot(g['resource_files']))
  debug=trusted_module(r['debug_helper_ref']['path'],r['debug_helper_ref'])
  write_json(output/'worker.runtime.before.json',runtime_snapshot(debug,g['resource_files']))
  with (output/'stdout.raw').open('xb') as so,(output/'stderr.raw').open('xb') as se:result=debug.run_owned(argv,r['cwd'],r['env'],so,se,120,r['expected_image'],r['images'],r['allowed_module_files'],r['process_cap'],creation_flags=0x08000000)
  require_job(result,True)
 except BaseException as e:cause.record(e,'debug-case')
 finally:
  cause.attempt('worker-after-inputs',lambda:ledger.check('after'))
  cause.attempt('worker-runtime-source-after',lambda:write_json(output/'worker.runtime.source.after.json',runtime_source_snapshot(g['resource_files'])))
  if debug:cause.attempt('worker-runtime-after',lambda:write_json(output/'worker.runtime.after.json',runtime_snapshot(debug,g['resource_files'])))
  cause.attempt('worker-input-vector',lambda:write_json(output/'worker.inputs.final.json',ledger.export()))
  write_json(output/'case-owned.json',result)
  write_json(output/'worker.completion.json',{'actual_native_exit':None if result is None else result.get('actual_exit'),'first_error':cause.primary,'secondary_errors':cause.secondary,'stdout_ref':existing_ref(output/'stdout.raw'),'stderr_ref':existing_ref(output/'stderr.raw'),'request_ref':pin,'point_in_time_python_only':True})
  if cause.primary:write_json(output/'worker.failure.origin.json',{'first_error':cause.primary,'secondary_errors':cause.secondary,'counter_reset':False})
 cause.raise_if_any()
if __name__=='__main__':
 try:main()
 except BaseException as e:
  # Pre-authority/pre-output failures remain on actual stderr for the Root-owned caller.
  print(json.dumps({'schema':'researchos.w09.entry-failure.v2','error_type':type(e).__name__,'message':str(e),'actual_child_native_exit':None,'counter_reset':False},ensure_ascii=False),file=sys.stderr)
  raise

