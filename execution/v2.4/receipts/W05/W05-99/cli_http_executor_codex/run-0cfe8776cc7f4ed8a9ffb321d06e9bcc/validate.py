from pathlib import Path
import datetime,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[7]
HERE=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
GO=MAIN/'.local/tools/go1.27.1/go/bin/go.exe'
ENV=dict(os.environ,GOROOT=str(GO.parent.parent),GOTOOLCHAIN='local',GOENV='off',GOPATH=str(MAIN/'.local/gopath'),GOCACHE=str(MAIN/'.local/gocache'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_WRITER_LEASE_TTL='60s',RESEARCHOS_NODE='C:/nvm4w/nodejs/node.exe',RESEARCHOS_MU_BUNDLE=str(MAIN/'.local/w0599-queue-integration/mu-worker.mjs'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(name,v):(HERE/name).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run(name,args,timeout=360):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();q=subprocess.run(args,cwd=ROOT,env=ENV,capture_output=True,timeout=timeout)
 (HERE/(name+'.stdout.raw')).write_bytes(q.stdout);(HERE/(name+'.stderr.raw')).write_bytes(q.stderr)
 dump(name+'.invocation.json',dict(argv=args,cwd=str(ROOT),actual_exit=q.returncode,started_at=start,ended_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),stdout_sha256=sha(HERE/(name+'.stdout.raw')),stderr_sha256=sha(HERE/(name+'.stderr.raw')),measurement_mode='FIXTURE'))
 print(name,q.returncode,flush=True);return q
assert sha(GO)=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
assert sha(Path(ENV['RESEARCHOS_NODE']))=='5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'
assert sha(Path(ENV['RESEARCHOS_MU_BUNDLE']))=='adfe7f456975bd986e58845f23a865a8f6eec5c45973fa2f14d298795aae8a38'
dump('fixed-environment.json',{k:ENV[k] for k in ['GOROOT','GOTOOLCHAIN','GOENV','GOPATH','GOCACHE','GOPROXY','GOSUMDB','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE','RESEARCHOS_WRITER_LEASE_TTL']})
assert run('gofmt',[str(GO.parent/'gofmt.exe'),'-w','apps/cli/cli_v2.go','apps/cli/cli_http_status_test.go']).returncode==0
assert run('go-env',[str(GO),'env','-json','GOROOT','GOTOOLCHAIN','GOENV','GOPATH','GOCACHE','GOMODCACHE','GOVERSION']).returncode==0
listed=run('go-list',[str(GO),'list','-deps','-test','-json','./apps/cli']);assert listed.returncode==0
text=listed.stdout.decode('utf-8');dec=json.JSONDecoder();off=0;paths=set()
while off<len(text):
 while off<len(text) and text[off].isspace():off+=1
 if off==len(text):break
 obj,off=dec.raw_decode(text,off);directory=Path(obj.get('Dir',''))
 if directory.is_dir():
  paths.update(x for x in directory.glob('*.go') if x.is_file())
  for field in ['EmbedFiles','SFiles','CFiles','CXXFiles','MFiles','HFiles','FFiles','SysoFiles','SwigFiles','SwigCXXFiles']:
   paths.update(directory/f for f in obj.get(field,[]))
paths.update(Path(ENV[k]) for k in ['RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE'])
paths.update(ROOT/p for p in ['go.mod','go.sum','apps/cli/main.go','apps/cli/cli_stream.go','apps/cli/cli_stream_test.go','apps/cli/cli_doctor.go','apps/cli/cli_doctor_test.go','tests/runtime/cli_contract/v2verbs.go'])
paths.add(Path(__file__).resolve());before={str(p):sha(p) for p in sorted(paths) if p.is_file()};dump('source-before.json',before)
focused=run('focused',[str(GO),'test','-count=1','-json','-run','^TestW05HTTP','./apps/cli'])
binary=HERE/'researchos-http.exe';built=run('build',[str(GO),'build','-o',str(binary),'./apps/cli'])
full=None
if focused.returncode==0 and built.returncode==0:
 ENV['RESEARCHOS_DOCTOR_TEST_BINARY']=str(binary)
 full=run('full-cli',[str(GO),'test','-count=1','-json','./apps/cli'])
after={str(p):sha(p) for p in sorted(paths) if p.is_file()};dump('source-after.json',after)
def counts(raw):
 rows=[json.loads(line) for line in raw.splitlines() if line.startswith(b'{')];return {key:sum(x.get('Action')==key and bool(x.get('Test')) for x in rows) for key in ['pass','fail','skip']}|{'top_pass':sum(x.get('Action')=='pass' and bool(x.get('Test')) and '/' not in x['Test'] for x in rows)}
summary=dict(source_count=len(before),source_drift=before!=after,focused_exit=focused.returncode,focused=counts(focused.stdout),build_exit=built.returncode,binary_sha256=sha(binary) if binary.exists() else None,full_cli_exit=full.returncode if full else None,full_cli=counts(full.stdout) if full else None,formal_increment=0,mode='FIXTURE')
dump('summary.json',summary);print(json.dumps(summary),flush=True)
