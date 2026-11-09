"""Root launch entry, NOT_AUTHORIZED until exact sealed grant. No work at import."""
import sys
sys.dont_write_bytecode=True
import argparse, json, os, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from controller_common import *
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--grant',required=True);ap.add_argument('--grant-sha256',required=True);a=ap.parse_args()
 g,s,out=validate_grant(a.grant,a.grant_sha256)
 outer=out.with_name(out.name+'-outer')
 if out.exists() or outer.exists():raise Stop('Exclusive run namespace already used')
 outer.mkdir();helper=trusted_module(g['normal_helper_ref']['path'],g['normal_helper_ref'])
 argv=[g['tools']['python']['path'],*FLAGS,s['controller_ref']['path'],'--grant',str(Path(a.grant)),'--grant-sha256',a.grant_sha256]
 env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT','NUMBER_OF_PROCESSORS','PROCESSOR_ARCHITECTURE'}}
 started=time.time();write_json(outer/'invocation.started.json',{'actualargv':argv,'cwd':str(PREP),'env':env,'grant_ref':file_ref(a.grant),'started_at_unix':started,'timeout_seconds':15000,'cleanup_observation_seconds':5})
 with (outer/'stdout.raw').open('xb') as so,(outer/'stderr.raw').open('xb') as se:
  result=helper.run_owned(argv,str(PREP),env,so,se,15000)
 write_json(outer/'completion.json',{'actualargv':argv,'cwd':str(PREP),'started_at_unix':started,'ended_at_unix':time.time(),'owned_result':result,'actual_native_controller_exit':result.get('actual_exit'),'stdout_ref':file_ref(outer/'stdout.raw'),'stderr_ref':file_ref(outer/'stderr.raw'),'source_acceptance':False})
 require_job(result)
 print(json.dumps({'controller_exit':result['actual_exit'],'result_path':str(out/'result.json'),'source_acceptance':False}))
if __name__=='__main__':main()
