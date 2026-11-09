import hashlib,json,os,subprocess
from pathlib import Path
from datetime import datetime,timezone
root=Path('D:/作品集/ResearchOS/research-os')
out=root/'execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/deliverygate-integration'
scope=json.loads((out/'scope.json').read_bytes());wt=Path(scope['worktree'])
target=out/'checks-01';assert not target.exists();target.mkdir()
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
lock=json.loads((root/'execution/toolchains/locked.json').read_bytes())['tools']['go'];go=Path(lock['path']);assert sha(go)==lock['sha256']
for path,digest in scope['files'].items():assert sha(wt/path)==digest
private=wt/'.local/deliverygate-checks-01';private.mkdir()
for name in ['gocache','gopath','tmp','profile','appdata','localappdata']:(private/name).mkdir()
env={key:value for key,value in os.environ.items() if key.upper() in {'SYSTEMROOT','WINDIR','PATH','PATHEXT','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA'}}
env.update({'GOTOOLCHAIN':'local','GOENV':'off','GOTELEMETRY':'off','GOPROXY':'off','GOSUMDB':'off','CGO_ENABLED':'0','GOCACHE':str(private/'gocache'),'GOPATH':str(private/'gopath'),'GOTMPDIR':str(private/'tmp'),'TEMP':str(private/'tmp'),'TMP':str(private/'tmp'),'USERPROFILE':str(private/'profile'),'APPDATA':str(private/'appdata'),'LOCALAPPDATA':str(private/'localappdata')})
argv=[str(go),'test','-mod=readonly','-count=1','-json','./internal/deliverygate']
(target/'invocation.json').write_text(json.dumps({'argv':argv,'cwd':str(wt),'env':env,'source':scope['files'],'go_sha256':sha(go),'scope':'DEVELOPMENT_COMPONENT_ONLY'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
start=datetime.now(timezone.utc).isoformat()
run=subprocess.run(argv,cwd=wt,env=env,capture_output=True,timeout=180)
(target/'stdout.jsonl').write_bytes(run.stdout);(target/'stderr.txt').write_bytes(run.stderr)
events=[json.loads(line) for line in run.stdout.decode('utf-8').splitlines() if line.startswith('{')]
passed=[e['Test'] for e in events if e.get('Action')=='pass' and e.get('Test')]
failed=[e.get('Test',e.get('Package')) for e in events if e.get('Action')=='fail']
for path,digest in scope['files'].items():assert sha(wt/path)==digest
result={'started_at':start,'ended_at':datetime.now(timezone.utc).isoformat(),'exit_code':run.returncode,'top_level_passed':len([name for name in passed if '/' not in name]),'subtests_passed':len([name for name in passed if '/' in name]),'failed':failed,'source_unchanged':True,'formal_increment':0,'native_core_or_model_started':False}
(target/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result));assert run.returncode==0 and not failed
