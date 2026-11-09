import pathlib,json,hashlib,subprocess,os,datetime
M=pathlib.Path('D:/作品集/ResearchOS/research-os'); W=M/'.local/worktrees/codex-w0599-host-config'; R=M/'execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_source_review_codex/c4ca3130-f842-454f-96d9-39df9ea53644'; E=W/'execution/v2.4/receipts/W05/W05-99/host_configuration_foundation_executor_codex/implementation-1cc1b20e27534da8a78e7350fa533ea3'; F=E/'run-238574514fa345f89e5468d9c9be5237'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(n,v):(R/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def git(*args):return subprocess.check_output(['git','-c','core.quotepath=false',*args],cwd=W).decode('utf-8')
a={'candidate':git('rev-parse','HEAD').strip(),'status_before':git('status','--porcelain'),'manifest_errors':[],'closures':{}}
manifest=json.loads((E/'manifest.json').read_text())
for row in manifest['files']:
 p=W/row['path']; actual=sha(p)
 if actual!=row['sha256'] or p.stat().st_size!=row['bytes']:a['manifest_errors'].append(row['path'])
a['manifest_entries']=len(manifest['files']);a['commit_changes']=git('diff-tree','--no-commit-id','--name-status','-r','HEAD').splitlines()
for kind in ['source','compiled','tools']:
 before=json.loads((F/(kind+'.before.json')).read_text());after=json.loads((F/(kind+'.after.json')).read_text()); current=[]
 for row in before:
  p=pathlib.Path(row['path']);p=p if p.is_absolute() else W/p
  if sha(p)!=row['sha256']:current.append(row['path'])
 a['closures'][kind]={'count':len(before),'before_after_equal':before==after,'current_mismatches':current}
a['old_source_changes']=[r for r in a['commit_changes'] if not r.startswith('A\t')]
put('audit.before.json',a)
go=M/'.local/tools/go1.27.1/go/bin/go.exe';env=os.environ.copy();env.update(GOTOOLCHAIN='local',GOENV='off',GOROOT=str(go.parent.parent),GOPATH=str(M/'.local/gopath'),GOCACHE=str(M/'.local/gocache'),GOPROXY='off',GOSUMDB='off')
argv=[str(go),'test','-json','-count=1','-run','TestClient(Configuration|CommandIdentity)','./internal/domain'];inv={'argv':argv,'cwd':str(W),'env':{k:env[k] for k in ['GOTOOLCHAIN','GOENV','GOROOT','GOPATH','GOCACHE','GOPROXY','GOSUMDB']},'go_sha256':sha(go),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};put('focused.invocation.json',inv)
p=subprocess.run(argv,cwd=W,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE);(R/'focused.stdout.raw').write_bytes(p.stdout);(R/'focused.stderr.raw').write_bytes(p.stderr)
rows=[json.loads(x) for x in p.stdout.splitlines() if x.startswith(b'{')];result={'exit':p.returncode,'pass':sum(x.get('Action')=='pass' and 'Test'in x for x in rows),'fail':sum(x.get('Action')=='fail' and 'Test'in x for x in rows),'skip':sum(x.get('Action')=='skip' for x in rows),'ended_at':datetime.datetime.now(datetime.timezone.utc).isoformat()};put('focused.result.json',result);print(json.dumps({'audit':a['closures'],'manifest_entries':a['manifest_entries'],'manifest_errors':a['manifest_errors'],'commit_count':len(a['commit_changes']),'result':result},ensure_ascii=False))
