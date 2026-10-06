import hashlib,json,pathlib,subprocess,re,os,threading,http.server
from datetime import datetime,timezone
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/codex-w0599-doctor'
PREFIX='execution/v2.4/receipts/W05/W05-99/doctor_executor_codex/'
HAND=WT/PREFIX/'handoff-1f508d6818b94172a0ec51a1e403e90a'
COMMIT='f1c57664f438bccb07d2f7f6a9071ce55164f506'
def sha(b):return hashlib.sha256(b).hexdigest()
def ref(p):return {'path':str(p),'sha256':sha(p.read_bytes())}
def save(name,d):
 raw=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode()
 with (OUT/name).open('xb') as f:f.write(raw)
 return ref(OUT/name)
def git(*args):return subprocess.run(['git','-C',str(WT),*args],capture_output=True,check=True).stdout
candidate=json.loads((HAND/'candidate.json').read_bytes())
assert sha((HAND/'candidate.json').read_bytes())=='a61c95bf7ceb992f72068608bab68aea002381351886a25feda39d23d07c7be5'
assert sha((HAND/'manifest.json').read_bytes())=='3eaa644fa1f9e93d08fe3f2823be79f64a1e2b986babd8c44708a0ebaed12452'
manifest=json.loads((HAND/'manifest.json').read_bytes())
for r in manifest['files']:assert sha((WT/r['path']).read_bytes())==r['sha256'],r['path']
sources={r['path']:r['sha256'] for r in candidate['source_paths']}
blobs=[]
for name in git('diff-tree','--no-commit-id','--name-only','-r',COMMIT).decode().splitlines():
 assert name in sources or name.startswith(PREFIX),name
 b=git('show',COMMIT+':'+name);assert b==(WT/name).read_bytes(),name
 if name in sources:assert sha(b)==sources[name]
 blobs.append({'path':name,'sha256':sha(b),'bytes':len(b)})
for name,r in candidate['protected'].items():assert git('show',candidate['base_commit']+':'+name)==(WT/name).read_bytes() and sha((WT/name).read_bytes())==r['sha256']
old=git('show',candidate['base_commit']+':tests/runtime/cli_contract/v2verbs.go').decode()
new=(WT/'tests/runtime/cli_contract/v2verbs.go').read_text()
old=old.replace('\r\n','\n')
start=new.index('\t\tif method == "host.status" {',new.index('case "malformed":'))
end=new.index('\t\t// The published envelope',start)
assert new[:start]+new[end:]==old
assert len(new[start:end].splitlines())==12
source_before=json.loads((WT/candidate['source_before_ref']['path']).read_bytes())
source_after=json.loads((WT/candidate['source_after_ref']['path']).read_bytes())
assert source_before==source_after and len(source_before)==5961
for name,h in source_before.items():assert sha(pathlib.Path(name).read_bytes())==h,name
run=WT/PREFIX/'0994dfb7b5ca4a1d81ef82ad54ab2f63'
dec=json.JSONDecoder();text=(run/'go-list.stdout').read_text();required=set();packages=0
while text.strip():
 obj,n=dec.raw_decode(text.lstrip());text=text.lstrip()[n:];packages+=1;d=pathlib.Path(obj.get('Dir',''))
 if d.is_dir():
  required.update(str(p) for p in d.glob('*.go') if p.is_file())
  for field in ['EmbedFiles','SFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SysoFiles','SwigFiles','SwigCXXFiles']:
   required.update(str(d/f) for f in obj.get(field,[]))
assert required.issubset(source_before),sorted(required-set(source_before))
invocations=[]
for p in (WT/PREFIX).glob('**/*.invocation.json'):
 d=json.loads(p.read_bytes());stem=p.name[:-len('.invocation.json')]
 for stream in ['stdout','stderr']:
  raw=(p.parent/(stem+'.'+stream)).read_bytes();assert sha(raw)==d[stream+'_sha256'],str(p)
 raw=(p.parent/(stem+'.stdout')).read_text(errors='replace')
 passes=re.findall(r'^\s*--- PASS: ([^ ]+)',raw,re.M);fails=re.findall(r'^\s*--- FAIL: ([^ ]+)',raw,re.M);skips=re.findall(r'^\s*--- SKIP: ([^ ]+)',raw,re.M)
 invocations.append({'ref':ref(p),'exit':d['exit'],'passes':len(passes),'top_passes':sum('/' not in x for x in passes),'fails':len(fails),'skips':len(skips),'stdout_ref':ref(p.parent/(stem+'.stdout')),'stderr_ref':ref(p.parent/(stem+'.stderr'))})
full=next(x for x in invocations if x['ref']['path']==str(run/'full-cli.invocation.json'))
assert (full['exit'],full['passes'],full['top_passes'],full['fails'],full['skips'])==(0,143,47,0,0)
fullraw=(run/'full-cli.stdout').read_text()
assert '--- PASS: TestW05DoctorLocalHostIntegration' in fullraw
doctor_passes=re.findall(r'^\s*--- PASS: (TestW05Doctor[^ ]+)',fullraw,re.M)
assert len(doctor_passes)==35
exe=WT/candidate['binary_ref']['path'];assert sha(exe.read_bytes())==candidate['binary_ref']['sha256']
NATIVE=OUT/'SYNTHETIC 本机诊断';NATIVE.mkdir()
binary=NATIVE/'researchos-doctor.exe';binary.write_bytes(exe.read_bytes())
sentinel='INDEPENDENT-DOCTOR-SYNTHETIC-BEARER-ONLY'
observations=[];state={'mode':'valid'};calls=[]
class Handler(http.server.BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  calls.append({'method':'GET','path':self.path})
  self.send_response(200);self.end_headers();self.wfile.write(b'{"state":"READY"}')
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  calls.append({'method':'POST','path':self.path,'envelope':data,'auth_matches':self.headers.get('Authorization')=='Bearer '+sentinel})
  assert data['method']=='host.status' and data['payload']=={}
  assert all(data[k] is None for k in ['session_id','project_id','writer_epoch','expected_revision'])
  mode=state['mode']
  if mode.startswith('plain'):
   self.send_response(int(mode[5:]));self.end_headers();self.wfile.write(sentinel.encode());return
  if mode=='redirect':
   self.send_response(307);self.send_header('Location',base+'/must-not-follow');self.end_headers();return
  result={'host_instance_id':'synthetic-host','core_build_id':'synthetic-core','protocol_versions':['researchos-client/2'],'host_state':'READY','client_id':data['client_id'],'authenticated_principal_ref':'PRIVATE-PRINCIPAL','config_revision':0,'model_configurations':[],'credentials':[],'workspaces':[],'supported_methods':['host.status'],'operating_mode':'LOCAL_USER_HOST'}
  reply={'protocol_version':'researchos-client/2','command_id':data['command_id'],'method':'host.status','status':'COMPLETED','session_id':None,'revision':None,'error_code':None,'error':None,'result':result}
  if mode=='wrong-client':result['client_id']='wrong'
  if mode=='wrong-method':reply['method']='session.get'
  if mode=='pending':reply['status']='IN_PROGRESS'
  self.send_response(200);self.end_headers();self.wfile.write(json.dumps(reply).encode())
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);base='http://127.0.0.1:'+str(server.server_port)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
discovery=NATIVE/'discovery.json';discovery.write_text(json.dumps({'url':base,'pid':os.getpid(),'data_dir':str(NATIVE/'no-session')}))
config=NATIVE/'config.json';config.write_text('{"project_id":"stale","session_id":"stale","writer_epoch":99}')
oldconfig=config.read_bytes()
try:
 for mode,want in [('valid',0),('plain401',3),('plain403',3),('plain503',1),('wrong-client',1),('wrong-method',1),('pending',1),('redirect',1),('absent-credential',3)]:
  state['mode']=mode;calls.clear();env=dict(os.environ,RESEARCHOS_CLI_DISCOVERY=str(discovery),RESEARCHOS_CLI_CONFIG=str(config),RESEARCHOS_CLI_CLIENT_ID='independent-doctor',RESEARCHOS_CLI_CREDENTIAL='' if mode=='absent-credential' else sentinel)
  started=datetime.now(timezone.utc).isoformat();r=subprocess.run([str(binary),'doctor'],cwd=NATIVE,env=env,capture_output=True,timeout=15)
  (NATIVE/(mode+'.stdout')).write_bytes(r.stdout);(NATIVE/(mode+'.stderr')).write_bytes(r.stderr)
  assert r.returncode==want,(mode,r.returncode,r.stdout)
  assert len(r.stdout.strip().splitlines())==1 and sentinel.encode() not in r.stdout+r.stderr
  out=json.loads(r.stdout);assert out['exit_code']==want
  assert out['provider_verification']=='NOT_CHECKED' and out['provider_network_called'] is False and out['tool_qualification']=='NOT_EVALUATED'
  assert config.read_bytes()==oldconfig
  assert len(calls)==(1 if mode=='absent-credential' else 2),calls
  if mode=='valid':assert out['credentials_reporting']=='NOT_REPORTED_BY_HOST' and out['model_configurations_reporting']=='NOT_REPORTED_BY_HOST'
  observations.append({'mode':mode,'classification':'SYNTHETIC_LOCAL_NOT_PROVIDER','actualargv':[str(binary),'doctor'],'cwd':str(NATIVE),'started_at':started,'exit':r.returncode,'stdout_ref':ref(NATIVE/(mode+'.stdout')),'stderr_ref':ref(NATIVE/(mode+'.stderr')),'observed_requests':list(calls)})
finally:server.shutdown();server.server_close();thread.join()
native_ref=save('native_controls.json',{'binary_ref':ref(binary),'controls':observations,'pass':len(observations),'fail':0,'provider_calls':0,'real_private_state_read':False})
result={'schema':'researchos.w05.independent-doctor-source-audit.v1','reviewer_id':'codex:/root/w05_merge_review','candidate_commit':COMMIT,'candidate_ref':ref(HAND/'candidate.json'),'manifest_ref':ref(HAND/'manifest.json'),'commit_blobs':blobs,'source_paths':candidate['source_paths'],'manifest_entries':len(manifest['files']),'total_commit_blobs':len(blobs),'receipt_artifact_blobs':len(blobs)-4,'protected':candidate['protected'],'fixture_added_lines':12,'all_original_fixture_bytes_retained':True,'complete_source_count':len(source_before),'go_list_packages':packages,'required_compilation_inputs':len(required),'current_drift':0,'source_before_ref':ref(WT/candidate['source_before_ref']['path']),'invocations':invocations,'doctor_current_inclusive_pass':35,'full_cli_current':full,'native_ref':native_ref,'source_registry_canonical_changes':0,'formal_acceptance_delta':0}
audit=save('audit.json',result);print(json.dumps({'audit':audit,'native':native_ref,'blobs':len(blobs),'inputs':len(source_before),'native_controls':len(observations)}))
