import pathlib,subprocess,os,json,hashlib,datetime,uuid,sys
sys.stdout.reconfigure(encoding='utf-8')
HERE=pathlib.Path(__file__).resolve().parent
ROOT=HERE.parents[6]
MAIN=pathlib.Path('D:/作品集/ResearchOS/research-os')
GO=MAIN/'.local/tools/go1.27.1/go/bin/go.exe'
ENV=os.environ.copy(); ENV.update(GOTOOLCHAIN='local',GOENV='off',GOROOT=str(GO.parents[1]),GOCACHE=str(MAIN/'.local/gocache'),GOPATH=str(MAIN/'.local/gopath'))
SOURCE=['migrations/sqlite/0023_host_model_configuration.sql','internal/domain/client_configuration.go','internal/domain/client_configuration_test.go','internal/domain/client_command_identity.go','internal/domain/client_command_identity_test.go']
def sha(b):return hashlib.sha256(b).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def vector():
 names=subprocess.check_output(['git','ls-files'],cwd=ROOT).decode('utf-8').splitlines()
 names=sorted(set([n for n in names if n.endswith(('.go','.sql')) or n in ('go.mod','go.sum','execution/toolchains/locked.json') or n.startswith('internal/api/contracts/')]+SOURCE))
 return [{'path':n,'sha256':sha((ROOT/n).read_bytes()),'bytes':(ROOT/n).stat().st_size} for n in names]
run=HERE/('run-'+uuid.uuid4().hex);run.mkdir();save(run/'source.before.json',vector())
for n in SOURCE:
 p=run/'source_snapshot'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/n).read_bytes())
args=[str(GO)]+sys.argv[1:]
save(run/'invocation.json',{'argv':args,'cwd':str(ROOT),'environment':{k:ENV[k] for k in ['GOTOOLCHAIN','GOENV','GOROOT','GOCACHE','GOPATH']},'go_sha256':sha(GO.read_bytes()),'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'network_requests':0,'credential_reads':0})
with (run/'stdout.raw').open('wb') as out,(run/'stderr.raw').open('wb') as err:
 result=subprocess.run(args,cwd=ROOT,env=ENV,stdout=out,stderr=err)
save(run/'source.after.json',vector());save(run/'result.json',{'exit_code':result.returncode,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stdout_sha256':sha((run/'stdout.raw').read_bytes()),'stderr_sha256':sha((run/'stderr.raw').read_bytes()),'source_drift':(run/'source.before.json').read_bytes()!=(run/'source.after.json').read_bytes()})
print(str(run)); print('exit',result.returncode);print((run/'stderr.raw').read_text('utf-8',errors='replace')[-6000:]);print((run/'stdout.raw').read_text('utf-8',errors='replace')[-10000:])
