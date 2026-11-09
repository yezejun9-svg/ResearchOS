"""Future sole-Root outer launcher; PREPARATION ONLY, no execution on import."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json,os,types
from pathlib import Path
def require(v,m):
 if not v:raise RuntimeError(m)
def load(path,sha):
 p=Path(path);b=p.read_bytes();require(hashlib.sha256(b).hexdigest()==sha,'Input pin');return json.loads(b)
def verify(r):
 b=Path(r['path']).read_bytes();require(len(b)==r['bytes'] and hashlib.sha256(b).hexdigest()==r['sha256'],'Immutable ref');return b
def main():
 require(sys.flags.isolated and sys.flags.no_site and sys.flags.utf8_mode and not sys.flags.optimize,'PinnedPython -I -S -X utf8')
 ap=argparse.ArgumentParser()
 for n in ['scope','scope-sha256','grant','grant-sha256']:ap.add_argument('--'+n,required=True)
 a=ap.parse_args();s=load(a.scope,a.scope_sha256);g=load(a.grant,a.grant_sha256)
 require(s['authorized'] is True and g['authorized'] is True and g['actual_registration_completed'] is True and s['owner']==g['actor']=='codex:/root','No actual Root grant')
 require(s['launcher_ref']['path']==str(Path(__file__).resolve()),'Launcher identity');verify(s['launcher_ref']);verify(s['controller_ref'])
 lock=json.loads(verify(s['toolchain_lock_ref']));python=lock['tools']['python']
 require(str(Path(sys.executable).absolute())==str(Path(python['path']).absolute()) and hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest()==python['sha256'],'Python identity')
 out=Path(s['new_output_root']);parent=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/desktop_exact15_integration_executor_codex')
 require(out.parent==parent and out.name==s['operation_uuid'] and len(out.name)==32 and all(c in '0123456789abcdef' for c in out.name),'Exclusive output identity')
 for q in [parent,*parent.parents]:
  require(q.exists() and not q.is_symlink() and not(getattr(q.lstat(),'st_file_attributes',0)&0x400),'Output parent alias')
 outer=out.with_name(out.name+'-outer');require(not out.exists() and not outer.exists(),'No retry/resume');outer.mkdir()
 def save(n,value):
  with (outer/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
 hr=s['owned_process_helper_ref'];require(hr['sha256']=='6a4fa13d7a69bd6dc33b10a667253906193bf105f8370db9f6665cd76837b3ad','Owned helper pin')
 helper=types.ModuleType('desktop15_owned_outer');helper.__file__=hr['path'];exec(compile(verify(hr),hr['path'],'exec'),helper.__dict__)
 argv=[python['path'],'-I','-S','-X','utf8',s['controller_ref']['path'],'--scope',str(Path(a.scope).absolute()),'--scope-sha256',a.scope_sha256,'--grant',str(Path(a.grant).absolute()),'--grant-sha256',a.grant_sha256]
 env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']};save('started.json',{'actualargv':argv,'cwd':str(Path(__file__).parent),'environment':env,'timeout_seconds':1200,'cleanup_seconds':5,'scope_SHA':a.scope_sha256,'grant_SHA':a.grant_sha256,'acceptance':False})
 with (outer/'stdout.raw').open('xb') as so,(outer/'stderr.raw').open('xb') as se:result=helper.run_owned(argv,str(Path(__file__).parent),env,so,se,1200)
 save('completed.json',{'owned_result':result,'actual_native_controller_exit':result.get('actual_exit'),'automatic_retry':False,'source_acceptance':False})
 c=result.get('job_cleanup',{});require(result.get('actual_exit')==0 and result.get('error') is None and result.get('timed_out') is False and result.get('resumed') is True and result.get('creation_time_100ns') and c.get('active_processes_last_observed')==0 and c.get('errors')==[] and all(c.get(k) is True for k in ['unnamed_exclusive_job','assigned_before_resume','kill_on_job_close_configured','primary_exit_confirmed','job_idle_confirmed','handles_closed']),'Outer lifecycle incomplete; no retry/reset')
if __name__=='__main__':main()
