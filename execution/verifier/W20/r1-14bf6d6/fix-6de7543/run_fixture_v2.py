from pathlib import Path
import subprocess,sys,json
OUT=Path(__file__).resolve().parent
source=(OUT/'fixture_review.py').read_text(encoding='utf-8')
source=source.replace('import subprocess,urllib.request,socket,json,hashlib','import subprocess,urllib.request,socket,json,hashlib,http.client,time')
source=source.replace("PROBE=OUT/'fixture-probe'", "PROBE=OUT/'fixture-probe-v2'")
old='''def health(port):
 try:
  with urllib.request.urlopen('http://127.0.0.1:'+str(port)+'/healthz',timeout=2) as r:return r.status
 except Exception:return None'''
new='''health_records=[]
def health(port):
 start=time.monotonic();connection=http.client.HTTPConnection('127.0.0.1',port,timeout=5)
 row={'port':port,'transport':'direct http.client, no proxy'}
 try:
  connection.request('GET','/healthz');response=connection.getresponse();row.update(status=response.status,body=response.read().decode('utf-8'));return response.status
 except Exception as error:
  row.update(status=None,error_type=type(error).__name__,error=str(error));return None
 finally:
  connection.close();row['elapsed_seconds']=time.monotonic()-start;health_records.append(row);put(PROBE/'health-transcripts.json',health_records)'''
assert old in source;source=source.replace(old,new)
needle="  check(label+'-both-alive',health(ports['a'])==200 and health(ports['b'])==200,started)"
replacement="""  for name in ['a','b']:
   ps('live-'+label+'-'+name,PRIOR/'fixture_process_identity.ps1','-ProcessIdToInspect',started[name])
   snapshot=decode((PROBE/('live-'+label+'-'+name+'.stdout.log')).read_bytes());check(label+'-native-alive-'+name,snapshot['alive'] is True,snapshot)
  check(label+'-both-alive',health(ports['a'])==200 and health(ports['b'])==200,started)"""
assert needle in source;source=source.replace(needle,replacement)
script=OUT/'fixture_review_v2.py';script.write_text(source,encoding='utf-8')
args=[sys.executable,'-X','utf8',str(script)]
with (OUT/'fixture-v2.stdout.log').open('wb') as stdout,(OUT/'fixture-v2.stderr.log').open('wb') as stderr:r=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=120)
(OUT/'fixture-v2-command.json').write_text(json.dumps({'argv':args,'exit_code':r.returncode,'change':'Direct loopback HTTP, 5s timeout, every HTTP result recorded and native liveness captured after each refusal. Original first-attempt failure is retained unchanged.'},indent=2)+'\n',encoding='utf-8')
print((OUT/'fixture-v2.stdout.log').read_text());print((OUT/'fixture-v2.stderr.log').read_text());print('exit_code='+str(r.returncode))
