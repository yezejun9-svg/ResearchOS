import datetime, hashlib, json, os, pathlib, subprocess, sys

base=pathlib.Path(__file__).resolve().parent
repo=pathlib.Path(r'D:\作品集\ResearchOS\research-os')
cwd=repo/'.local/worktrees/verifier-replacement-20261014'
label=sys.argv[1]
argv=sys.argv[2:]
env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','PATH','TEMP','TMP','USERPROFILE','APPDATA','LOCALAPPDATA','COMSPEC','PATHEXT','PROGRAMFILES','PROGRAMFILES(X86)','PROGRAMDATA','PROCESSOR_ARCHITECTURE','NUMBER_OF_PROCESSORS','HOMEDRIVE','HOMEPATH'}}
env.update(GOCACHE=str(repo/'.local/go-cache/verifier-replacement-20261014'),GOMODCACHE=str(repo/'.local/tools/gopath/pkg/mod'),GOTOOLCHAIN='local',GOPROXY='off',GOSUMDB='off')
temp=repo/'.local/tmp/verifier-replacement-20261014'
temp.mkdir(parents=True,exist_ok=True)
env.update(TEMP=str(temp),TMP=str(temp))
record={'label':label,'argv':argv,'cwd':str(cwd),'environment':env,'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
path=base/(label+'.log')
with path.open('xb') as log:
    result=subprocess.run(argv,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
record.update(exit_code=result.returncode,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),log_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
(base/(label+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:record[k] for k in ['label','exit_code','log_sha256','bytes']},ensure_ascii=False))
print(path.read_text(encoding='utf-8',errors='replace')[-12000:])
sys.exit(result.returncode)
