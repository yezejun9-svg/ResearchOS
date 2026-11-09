"""Serve the existing local model on the persisted numeric-loopback endpoint."""
import datetime,hashlib,json,os,socket,subprocess,time,urllib.request
from pathlib import Path
E=Path(__file__).parent;R=Path('D:/作品集/ResearchOS/research-os')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def ref(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def new(p,v):
 with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
exe=Path('C:/Users/yqyyds/AppData/Local/Programs/Ollama/ollama.exe');assert ref(exe)['sha256']=='4e91d8fb44e0909ab69feec21c3699ae82843b56ce631b37491255c2dc6b0792'
models=Path('C:/Users/yqyyds/.ollama/models');assert (models/'manifests/registry.ollama.ai/library/qwen3/4b-instruct').is_file()
with socket.socket() as s:s.bind(('127.0.0.1',11435))
env={k:os.environ[k] for k in ['SystemRoot','WINDIR','USERPROFILE','LOCALAPPDATA','APPDATA','TEMP','TMP','PATH'] if k in os.environ};env.update(OLLAMA_HOST='127.0.0.1:11435',OLLAMA_MODELS=str(models))
argv=[str(exe),'serve'];new(E/'01-invocation.json',{'at':now(),'argv':argv,'cwd':str(R),'environment_allowlist':env,'executable':ref(exe),'new_model_pulls':0,'model_completion_requests':0,'default_configuration_writes':0,'owned_process_handle':True,'formal_increment':0})
with (E/'server.stdout.raw').open('xb') as out,(E/'server.stderr.raw').open('xb') as err:
 p=subprocess.Popen(argv,cwd=R,env=env,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
 new(E/'02-process-started.json',{'at':now(),'pid':p.pid,'owned_process_handle':True,'executable':ref(exe),'bind':'127.0.0.1:11435','model_completion_requests':0,'formal_increment':0})
 ready=False
 for _ in range(50):
  if p.poll() is not None:break
  try:
   with socket.create_connection(('127.0.0.1',11435),timeout=0.2):ready=True
   break
  except OSError:time.sleep(0.2)
 metadata=[]
 if ready:
  opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  for endpoint in ['version','tags']:
   url='http://127.0.0.1:11435/api/'+endpoint
   with opener.open(url,timeout=10) as response:raw=response.read();status=response.status
   path=E/(endpoint+'.response.raw.json');path.write_bytes(raw);metadata.append({'url':url,'status':status,'ref':ref(path)})
  tags=json.loads((E/'tags.response.raw.json').read_bytes());selected=[m for m in tags['models'] if m['name']=='qwen3:4b-instruct'];assert len(selected)==1 and selected[0]['digest']=='0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0'
 new(E/'03-resource-ready.json',{'at':now(),'pid':p.pid,'ready':ready,'metadata_requests':metadata,'selected_model':'qwen3:4b-instruct','model_completion_requests':0,'new_pulls':0,'formal_increment':0})
 print(json.dumps({'event':'RESOURCE_READY' if ready else 'RESOURCE_NOT_READY','pid':p.pid,'owned_handle_retained':True,'metadata_only':True}),flush=True)
 started=time.monotonic();code=p.wait();new(E/'04-process-wait.json',{'at':now(),'pid':p.pid,'native_exit':code,'elapsed_seconds':time.monotonic()-started,'observer_signal_or_kill':False,'formal_increment':0})
 print(json.dumps({'event':'RESOURCE_EXITED','pid':p.pid,'native_exit':code}),flush=True)
