from pathlib import Path
import subprocess,urllib.request,socket,time,json
OUT=Path(__file__).resolve().parent;ROOT=OUT/'fixture-release';PROBE=OUT/'fixture-probe';PROBE.mkdir(exist_ok=True)
records=[]
def ps(label,script,*args):
 argv=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),*map(str,args)]
 with (PROBE/(label+'.stdout.log')).open('wb') as stdout,(PROBE/(label+'.stderr.log')).open('wb') as stderr:result=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=45)
 row={'label':label,'argv':argv,'exit_code':result.returncode};records.append(row);return row
def health(port):
 try:
  with urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/healthz',timeout=2) as response:return {'status':response.status,'body':response.read().decode()}
 except Exception as exc:return {'status':None,'error':str(exc)}
def freeport():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
a=PROBE/'data-a';b=PROBE/'data-b';ports={name:freeport() for name in ['a','b']};pids={};observed={}
try:
 for name,data in [('a',a),('b',b)]:
  result=ps('start-'+name,ROOT/'scripts/start.ps1','-DataDir',data,'-Listen','127.0.0.1:'+str(ports[name]),'-Fresh');assert result['exit_code']==0
  pids[name]=int((data/'fixture-control.pid').read_text(encoding='utf-8-sig').strip());assert pids[name] not in [32736,79136]
  ps('identity-'+name,OUT/'fixture_process_identity.ps1','-ProcessIdToInspect',pids[name]);observed['before_'+name]=health(ports[name]);assert observed['before_'+name]['status']==200
 assert pids['a']!=pids['b']
 # Model a stale/wrong local PID record using only these two owned fixtures.
 (a/'fixture-control.pid').write_text(str(pids['b'])+'\n',encoding='ascii')
 observed['stop_a_with_b_pid']=ps('stop-a-with-b-pid',ROOT/'scripts/stop.ps1','-DataDir',a)
 observed['after_a']=health(ports['a']);observed['after_b']=health(ports['b'])
 ps('identity-after-a',OUT/'fixture_process_identity.ps1','-ProcessIdToInspect',pids['a']);ps('identity-after-b',OUT/'fixture_process_identity.ps1','-ProcessIdToInspect',pids['b'])
 observed['cross_data_process_killed']=observed['stop_a_with_b_pid']['exit_code']==0 and observed['after_a']['status']==200 and observed['after_b']['status'] is None
finally:
 for name,data in [('a',a),('b',b)]:
  if name in pids:
   (data/'fixture-control.pid').write_text(str(pids[name])+'\n',encoding='ascii')
   ps('cleanup-stop-'+name,ROOT/'scripts/stop.ps1','-DataDir',data)
   observed['cleanup_'+name]=health(ports[name]);ps('identity-cleanup-'+name,OUT/'fixture_process_identity.ps1','-ProcessIdToInspect',pids[name])
 (PROBE/'commands.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
 (PROBE/'result.json').write_text(json.dumps({'scope':'two newly created owned credential-free fixtures only','ports':ports,'pids':pids,'observed':observed},indent=2)+'\n',encoding='utf-8')
print(json.dumps({'pids':pids,'ports':ports,'cross_data_process_killed':observed.get('cross_data_process_killed'),'before':{x:observed.get('before_'+x) for x in ['a','b']},'after':{x:observed.get('after_'+x) for x in ['a','b']},'cleanup':{x:observed.get('cleanup_'+x) for x in ['a','b']}},indent=2))
