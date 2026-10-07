from pathlib import Path
import subprocess,urllib.request,socket,json,hashlib,http.client,time
OUT=Path(__file__).resolve().parent;PRIOR=OUT.parent;ROOT=OUT/'fixture-release';PROBE=OUT/'fixture-probe-v2';PROBE.mkdir(exist_ok=True)
commands=[];checks=[];identities={};original={};started={};stopped=set();ports={}
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
def ps(label,script,*args):
 argv=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(script),*map(str,args)]
 with (PROBE/(label+'.stdout.log')).open('wb') as stdout,(PROBE/(label+'.stderr.log')).open('wb') as stderr:r=subprocess.run(argv,stdout=stdout,stderr=stderr,timeout=45)
 row={'label':label,'argv':argv,'exit_code':r.returncode};commands.append(row);put(PROBE/'commands.json',commands);return row
def check(id,condition,actual):checks.append({'id':id,'status':'PASS' if condition else 'FAIL','actual':actual});put(PROBE/'assertions.json',checks);assert condition,(id,actual)
def freeport():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
health_records=[]
def health(port):
 start=time.monotonic();connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
 row={'port':port,'transport':'direct http.client, no proxy'}
 try:
  connection.request('GET','/healthz');response=connection.getresponse();row.update(status=response.status,body=response.read().decode('utf-8'));return response.status
 except Exception as error:
  row.update(status=None,error_type=type(error).__name__,error=str(error));return None
 finally:
  connection.close();row['elapsed_seconds']=time.monotonic()-start;health_records.append(row);put(PROBE/'health-transcripts.json',health_records)
def decode(raw):
 try:return json.loads(raw.decode('utf-8-sig'))
 except UnicodeDecodeError:return json.loads(raw.decode('mbcs'))
def identity_file(name):return PROBE/('data-'+name)/'fixture-control.pid'
try:
 for name in ['a','b']:
  data=PROBE/('data-'+name);ports[name]=freeport();r=ps('start-'+name,ROOT/'scripts/start.ps1','-DataDir',data,'-Listen','127.0.0.1:'+str(ports[name]),'-Fresh')
  check('start-'+name,r['exit_code']==0,r);original[name]=identity_file(name).read_bytes();identities[name]=decode(original[name]);started[name]=identities[name]['pid']
  ps('identity-'+name,PRIOR/'fixture_process_identity.ps1','-ProcessIdToInspect',started[name]);check('health-'+name,health(ports[name])==200,ports[name])
  check('bound-record-'+name,identities[name]['schema']=='researchos.fixture-process.v1' and identities[name]['data_dir']==str(data) and identities[name]['release_root']==str(ROOT) and identities[name]['created_utc_ticks']>0,identities[name])
 first=identities['a'];second=identities['b']
 cases={
  'wrong-pid':dict(first,pid=second['pid']),
  'wrong-creation':dict(first,created_utc_ticks=first['created_utc_ticks']+1),
  'copied-identity-wrong-data-binding':dict(second,data_dir=first['data_dir']),
  'wrong-instance':dict(first,instance='0'*32),
  'wrong-release-root':dict(first,release_root=str(OUT/'other-release')),
 }
 for label,value in cases.items():
  target=identity_file('a');target.write_text(json.dumps(value),encoding='utf-8-sig');before=hashlib.sha256(target.read_bytes()).hexdigest();r=ps(label,ROOT/'scripts/stop.ps1','-DataDir',target.parent)
  check(label+'-refused-preserving-record',r['exit_code']!=0 and target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()==before,r)
  for name in ['a','b']:
   ps('live-'+label+'-'+name,PRIOR/'fixture_process_identity.ps1','-ProcessIdToInspect',started[name])
   snapshot=decode((PROBE/('live-'+label+'-'+name+'.stdout.log')).read_bytes());check(label+'-native-alive-'+name,snapshot['alive'] is True,snapshot)
  check(label+'-both-alive',health(ports['a'])==200 and health(ports['b'])==200,started)
 # Valid stop must affect exactly A, preserving its data and B's liveness.
 identity_file('a').write_bytes(original['a']);r=ps('valid-stop-a',ROOT/'scripts/stop.ps1','-DataDir',identity_file('a').parent);check('valid-stop-a',r['exit_code']==0 and not identity_file('a').exists() and health(ports['a']) is None and health(ports['b'])==200,r);stopped.add('a')
 check('stop-preserves-data-a',(identity_file('a').parent/'researchos.sqlite').is_file(),True)
 identity_file('a').write_bytes(original['a']);r=ps('stale-stopped-identity',ROOT/'scripts/stop.ps1','-DataDir',identity_file('a').parent);check('stale-identity-refused-and-retained',r['exit_code']!=0 and identity_file('a').read_bytes()==original['a'] and health(ports['b'])==200,r)
 identity_file('a').unlink()
finally:
 for name in list(started):
  if name not in stopped:
   identity_file(name).write_bytes(original[name]);r=ps('cleanup-valid-stop-'+name,ROOT/'scripts/stop.ps1','-DataDir',identity_file(name).parent)
   check('cleanup-stop-'+name,r['exit_code']==0 and not identity_file(name).exists(),r);stopped.add(name)
  ps('identity-cleanup-'+name,PRIOR/'fixture_process_identity.ps1','-ProcessIdToInspect',started[name]);raw=(PROBE/('identity-cleanup-'+name+'.stdout.log')).read_bytes();check('process-finally-stopped-'+name,decode(raw)['alive'] is False,started[name])
  check('data-finally-preserved-'+name,(identity_file(name).parent/'researchos.sqlite').is_file(),True)
 put(PROBE/'result.json',{'scope':'new owned disposable credential-free fixtures only','ports':ports,'pids':started,'identities':identities,'checks':len(checks),'all_pass':all(x['status']=='PASS' for x in checks)})
print(json.dumps({'assertions':len(checks),'pids':started,'all_pass':all(x['status']=='PASS' for x in checks)},indent=2))
