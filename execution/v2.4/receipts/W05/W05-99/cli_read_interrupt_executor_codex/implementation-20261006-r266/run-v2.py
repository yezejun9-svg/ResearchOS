import datetime, hashlib, json, os, pathlib, subprocess, sys, uuid
R=pathlib.Path(r'D:/作品集/ResearchOS/research-os')
W=R/'.local/worktrees/codex-w0599-cli-read-interrupt'
D=R/'execution/v2.4/receipts/W05/W05-99/cli_read_interrupt_executor_codex/implementation-20261006-r266'
G=R/'.local/tools/go1.27.1/go'
E=os.environ.copy()
E.update(GOROOT=str(G),GOENV='off',GOTOOLCHAIN='local',GOPATH=str(R/'.local/gopath'),GOCACHE=str(R/'.local/gocache'),GOPROXY='off',GOSUMDB='off',RESEARCHOS_GO=str(G/'bin/go.exe'),RESEARCHOS_NODE='C:/nvm4w/nodejs/node.exe',RESEARCHOS_MU_BUNDLE=str(R/'.local/w0599-queue-integration/mu-worker.mjs'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,obj):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
paths=['apps/cli/cli_stream.go','apps/cli/cli_continuation.go','apps/cli/cli_read_interrupt_test.go']
def snapshot():return [{'path':p,'sha256':sha(W/p),'bytes':(W/p).stat().st_size} for p in paths]
def run(name,args,timeout=120):
 d=D/(name+'-'+uuid.uuid4().hex);d.mkdir()
 write(d/'source_before.json',snapshot()); started=datetime.datetime.now(datetime.timezone.utc).isoformat()
 completed=subprocess.run(args,cwd=W,env=E,capture_output=True,timeout=timeout)
 (d/'stdout.raw').write_bytes(completed.stdout);(d/'stderr.raw').write_bytes(completed.stderr)
 write(d/'source_after.json',snapshot())
 write(d/'invocation.json',{'actor':'codex:/root','scope_ref':'execution/v2.4/receipts/W05/W05-99/integration_codex/cli-read-interrupt-scope-r266/scope_registration.json','argv':args,'cwd':str(W),'started_at':started,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_exit':completed.returncode,'environment':{k:E[k] for k in ['GOROOT','GOENV','GOTOOLCHAIN','GOPATH','GOCACHE','GOPROXY','GOSUMDB','RESEARCHOS_GO','RESEARCHOS_NODE','RESEARCHOS_MU_BUNDLE']},'stdout_sha256':sha(d/'stdout.raw'),'stderr_sha256':sha(d/'stderr.raw')})
 counts={'pass':0,'fail':0,'skip':0}
 for line in completed.stdout.splitlines():
  try:row=json.loads(line)
  except:continue
  if row.get('Test') and row.get('Action') in counts:counts[row['Action']]+=1
 print(json.dumps({'directory':str(d.relative_to(R)).replace('\\','/'),'actual_exit':completed.returncode,'assertion_counts':counts,'source_drift':json.loads((d/'source_before.json').read_text(encoding='utf8'))!=json.loads((d/'source_after.json').read_text(encoding='utf8'))},ensure_ascii=False),flush=True)
 if completed.returncode:
  for line in completed.stdout.splitlines():
   try:row=json.loads(line)
   except:continue
   if row.get('Action')=='fail' or row.get('OutputType')=='error':print(json.dumps(row,ensure_ascii=False))
  print(completed.stderr.decode('utf8','replace')[-3000:])
 return completed.returncode
if sys.argv[1]=='format':sys.exit(run('gofmt',[str(G/'bin/gofmt.exe'),'-w']+paths))
if sys.argv[1]=='focused':sys.exit(run('focused',[str(G/'bin/go.exe'),'test','-json','-count=1','-timeout=60s','./apps/cli','-run','TestCLIRead'],90))
if sys.argv[1]=='full':sys.exit(run('full',[str(G/'bin/go.exe'),'test','-json','-count=1','-timeout=180s','./apps/cli'],220))
raise SystemExit('unsupported action')