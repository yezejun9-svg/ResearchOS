from pathlib import Path
import json,hashlib,subprocess,os,datetime
ROOT=Path('D:/作品集/ResearchOS/research-os'); WT=ROOT/'.local/worktrees/codex-w0599-cli-http'; OUT=Path(__file__).resolve().parent
P='execution/v2.4/receipts/W05/W05-99/cli_http_executor_codex/run-0cfe8776cc7f4ed8a9ffb321d06e9bcc'; D=WT/P; C='b7249b1b1dbd3625a1d8f6b7af845dbfbd20ad8b'
def sh(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=json.loads((D/'manifest.json').read_bytes()); hand=json.loads((D/'handoff.json').read_bytes()); before=json.loads((D/'source-before.json').read_bytes()); after=json.loads((D/'source-after.json').read_bytes())
changed=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',C],cwd=WT).decode().splitlines(); blobrows=[]
for p in changed:
 b=subprocess.check_output(['git','show',C+':'+p],cwd=WT); blobrows.append({'path':p,'sha256':hashlib.sha256(b).hexdigest(),'same_worktree':b==(WT/p).read_bytes()})
manifestchecks=[{'path':x['path'],'expected':x['sha256'],'actual':sh(WT/x['path'])} for x in manifest['entries']]
current={p:sh(Path(p)) for p in before}; counts={}; invocations={}
for name in ['focused','full-cli','build','go-list','go-env','gofmt']:
 inv=json.loads((D/(name+'.invocation.json')).read_bytes()); invocations[name]={'actual_exit':inv['actual_exit'],'stdout_matches':sh(D/(name+'.stdout.raw'))==inv['stdout_sha256'],'stderr_matches':sh(D/(name+'.stderr.raw'))==inv['stderr_sha256']}
 if name in ['focused','full-cli']:
  rows=[json.loads(l) for l in (D/(name+'.stdout.raw')).read_bytes().splitlines() if l.startswith(b'{')]; counts[name]={k:sum(x.get('Action')==k and bool(x.get('Test')) for x in rows) for k in ['pass','fail','skip']};counts[name]['top_pass']=sum(x.get('Action')=='pass' and bool(x.get('Test')) and '/' not in x['Test'] for x in rows)
env=os.environ.copy();env.update(json.loads((D/'fixed-environment.json').read_bytes()));go=Path(env['GOROOT'])/'bin/go.exe'; argv=[str(go),'test','-count=1','-json','-run','^TestW05HTTP','./apps/cli'];start=datetime.datetime.now(datetime.timezone.utc).isoformat();p=subprocess.run(argv,cwd=WT,env=env,capture_output=True,timeout=90)
(OUT/'focused.stdout.raw').write_bytes(p.stdout);(OUT/'focused.stderr.raw').write_bytes(p.stderr)
dump('focused.invocation.json',{'argv':argv,'cwd':str(WT),'started_at':start,'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_exit':p.returncode,'stdout_sha256':sh(OUT/'focused.stdout.raw'),'stderr_sha256':sh(OUT/'focused.stderr.raw'),'mode':'FIXTURE','network':'local httptest only; GOPROXY/GOSUMDB off'})
rows=[json.loads(l) for l in p.stdout.splitlines() if l.startswith(b'{')]; own={k:sum(x.get('Action')==k and bool(x.get('Test')) for x in rows) for k in ['pass','fail','skip']}
final={path:sh(Path(path)) for path in before}; readrefs=[{'path':str(x),'sha256':sh(x)} for x in [ROOT/'AGENTS.md',D/'handoff.json',D/'manifest.json',D/'validate.py',WT/'apps/cli/cli_v2.go',WT/'apps/cli/cli_http_status_test.go']]
audit={'candidate':C,'changed_count':len(changed),'blob_checks':blobrows,'manifest_count':len(manifestchecks),'manifest_checks':manifestchecks,'manifest_plus_self_exact':set(changed)=={x['path'] for x in manifestchecks}|{P+'/manifest.json'},'closure_count':len(before),'before_after_same':before==after,'current_before_same':before==current,'current_after_replay_same':before==final,'counts_from_raw':counts,'invocations':invocations,'independent_focused':own,'independent_exit':p.returncode,'actual_reads':readrefs,'go_sha256':sh(go),'protected':[{**x,'actual':sh(WT/x['path'])} for x in hand['protected_refs']]}
dump('audit.json',audit)
assert len(changed)==33 and len(before)==5963 and before==after==current==final
assert all(x['same_worktree'] for x in blobrows) and all(x['expected']==x['actual'] for x in manifestchecks) and audit['manifest_plus_self_exact']
assert all(x['actual_exit']==0 and x['stdout_matches'] and x['stderr_matches'] for x in invocations.values())
assert counts['focused']=={'pass':39,'fail':0,'skip':0,'top_pass':4} and counts['full-cli']=={'pass':182,'fail':0,'skip':0,'top_pass':51}
assert p.returncode==0 and own=={'pass':39,'fail':0,'skip':0}
print(json.dumps({'audit_sha256':sh(OUT/'audit.json'),'independent':own,'blobs':len(changed),'closure':len(before)}))

