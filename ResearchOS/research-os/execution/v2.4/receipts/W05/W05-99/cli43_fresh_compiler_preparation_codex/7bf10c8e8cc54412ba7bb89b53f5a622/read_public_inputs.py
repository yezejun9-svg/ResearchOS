"""Bounded read-only Git/source inventory; never invokes product/compiler/helper."""
import hashlib,json,os,re,subprocess,time
from pathlib import Path
ROOT=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).resolve().parent
OLD=ROOT/'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f'
GIT=Path('C:/Program Files/Git/cmd/git.exe');COMMIT='a510dbef4a7e08fb5c428df44c39b133f3ffa856'
def digest(b):return hashlib.sha256(b).hexdigest()
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':digest(b),'bytes':len(b)}
def raw(n,b):
 with (N/n).open('xb') as f:f.write(b)
 return ref(N/n)
def save(n,d):return raw(n,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
if ref(GIT)['sha256']!='da240fe9bc24895b3e04150a4990b8a6ff329ecabcd8f19684c2cc310da5ef3f':raise RuntimeError('Git pin')
env={k:v for k,v in os.environ.items() if k.upper() in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT']}
env.update(GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
def git(label,args,data=None):
 argv=[str(GIT),'-C',str(ROOT),*args];started=time.time()
 if data is not None:raw(label+'.stdin.raw',data)
 p=subprocess.run(argv,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=45)
 sr=raw(label+'.stdout.raw',p.stdout);er=raw(label+'.stderr.raw',p.stderr)
 save(label+'.invocation.json',{'argv':argv,'cwd':str(ROOT),'environment':env,'started_at_unix':started,'ended_at_unix':time.time(),'actual_native_exit':p.returncode,'stdout_ref':sr,'stderr_ref':er,'readonly':True,'automatic_retry':False})
 if p.returncode:raise RuntimeError('First read-only Git failure '+label)
 if len(p.stdout)>64*1024*1024:raise RuntimeError('Read output cap')
 return p.stdout
oldbefore=[ref(OLD/n) for n in ['runner.v2.py','public_compiler_export_plan.v2.json','preparation_tools.v2.json','finite_selectors.json','prepared_execution_spec.v2.json','manifest.v2.json']]
head=git('git-head',['rev-parse','HEAD']).decode().strip()
if head!=COMMIT:raise RuntimeError('CurrentMain43 HEAD differs')
tree={}
for line in git('git-tree',['ls-tree','-r','-z',COMMIT]).split(b'\0'):
 if not line:continue
 h,p=line.split(b'\t',1);mode,kind,blob=h.decode('ascii').split();name=p.decode('utf-8','strict')
 if name in tree:raise RuntimeError('Duplicate tree path')
 tree[name]={'mode':mode,'kind':kind,'git_blob':blob}
oldplan=json.loads((OLD/'public_compiler_export_plan.v2.json').read_bytes())
oldnames={r['path'] for r in oldplan['git_resources']}
go={p for p in tree if p.endswith('.go') and not p.startswith(('execution/','.local/'))}
selected=go|{p for p in tree if p.startswith(('migrations/sqlite/','spec/v2.0/contracts/'))}|{'go.mod','go.sum'}|oldnames
for p in selected:
 if p not in tree or tree[p]['mode']!='100644' or tree[p]['kind']!='blob':raise RuntimeError('Public source missing/mode '+p)
 if any(x in p.lower() for x in ['privateholdout','private_holdout','/secrets/','/vault/']):raise RuntimeError('Private-data path excluded '+p)
names=sorted(selected);batch=git('git-public-blobs',['cat-file','--batch'],''.join(tree[p]['git_blob']+'\n' for p in names).encode('ascii'))
pos=0;rows=[];bodies={}
for p in names:
 end=batch.index(b'\n',pos);oid,kind,n=batch[pos:end].decode('ascii').split();n=int(n);pos=end+1;body=batch[pos:pos+n];pos+=n
 if oid!=tree[p]['git_blob'] or kind!='blob' or len(body)!=n or batch[pos:pos+1]!=b'\n':raise RuntimeError('Batch framing')
 pos+=1;rows.append({'path':p,**tree[p],'sha256':digest(body),'bytes':n});bodies[p]=body
if pos!=len(batch):raise RuntimeError('Batch trailing')
embeds=[]
for p in sorted(go):
 for line in bodies[p].decode('utf-8','strict').splitlines():
  if line.lstrip().startswith('//go:embed '):embeds.append({'file':p,'directive':line.strip(),'future_actual_go_list_embed_gate':True})
save('public-source-catalog.proposed.json',{'schema':'researchos.cli43.public-source-catalog.v1','commit':COMMIT,'files':rows,'file_count':len(rows),'all_platform_Go_count':len(go),'old_paths_used_as_public_name_hints_only':len(oldnames),'old_blobs_and_hashes_reused':False,'embed_directives':embeds,'runtime_graph_NOT_RUN':True,'runtime_missing_input_policy':'FAIL_BEFORE_COMPILE; no on-demand unregistered filesystem widening'})
for p in ['apps/cli/cli_sessions_test.go','apps/cli/cli_stream_test.go','internal/api/v2_sessions_test.go']:
 raw(p.replace('/','__')+'.original',bodies[p])
roster=json.loads((OLD/'finite_selectors.json').read_bytes())
changes=git('git-old-cli-to-main43',['diff','--name-only','b98738ac093ea55bb8700cfa724ddd9e6b2a1251',COMMIT,'--','apps/cli','internal','adapters','migrations','spec/v2.0/contracts']).decode().splitlines()
save('roster-impact.json',{'current_commit':COMMIT,'previous_candidate':'b98738ac093ea55bb8700cfa724ddd9e6b2a1251','changed_paths':changes,'previous_roster':roster,'proposed_now':['TestCLIProtocolInteractiveAuthority/real-existing-open-readonly','TestCLIProtocolInteractiveAuthority/real-existing-self-send'],'now_count':2,'future47_separate_decision_required':True,'current49_not_automatically_authorized':True,'reason':'Main43 adds handler/list closed-copy composition; current CLI8 product/test blobs are same as b987, but domain/API graph changed. First address two held real API leaves and then independently decide necessary remaining current regressions.','current_results':None})
after=[ref(Path(p['path'])) for p in oldbefore]
if after!=oldbefore:raise RuntimeError('Old input prefix drift')
save('read-inputs.audit.json',{'head':head,'catalog_count':len(rows),'old_before':oldbefore,'old_after':after,'drift':[],'Git_readonly_calls':4,'candidate_Go_SQL_Node_HTTP_DLL_Model':0,'new_failure_origins':[]})
print(json.dumps({'catalog_count':len(rows),'all_platform_Go':len(go),'embed_directives':embeds,'changed_paths':changes,'old_prefix_drift':0},ensure_ascii=False))
