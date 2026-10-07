from pathlib import Path
import os,sys,json,hashlib,uuid,subprocess,datetime,re
W=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip());N=Path(__file__).resolve().parent
B=N/'build-0413a23c684743899fd5498ce5219f9b';G=Path('D:/作品集/ResearchOS/research-os/.local/tools/go1.27.1/go/bin/go.exe')
scope=json.loads((N/'cli_implementation_scope.json').read_text(encoding='utf-8'));group=sys.argv[1]
allowed=scope['new_test_groups']+[s[1:-1] for s in scope['approved_exact_regression_selectors']]
assert group in allowed,group
run=N/('run-'+uuid.uuid4().hex);run.mkdir();evidence=run/'cases';evidence.mkdir()
ENV=os.environ.copy();ENV.update({'GOTOOLCHAIN':'local','GOENV':'off','GOROOT':str(G.parent.parent),'GOPATH':'D:/作品集/ResearchOS/research-os/.local/gopath','GOCACHE':str(W/'.local/cli-r303/cache'),'GOTMPDIR':str(W/'.local/cli-r303/gotmp'),'GOPROXY':'off','GOSUMDB':'off','RESEARCHOS_GO':str(G),'RESEARCHOS_CLI_PROTOCOL_BINARY':str(B/'researchos-cli.exe'),'RESEARCHOS_CLI_PROTOCOL_EVIDENCE_DIR':str(evidence)})
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=json.loads((B/'inputs.after.json').read_text(encoding='utf-8'));before=[dict(x,sha256=sha(x['path']),bytes=Path(x['path']).stat().st_size) for x in old]
assert old==before,'BUILD_INPUT_DRIFT'
extra=[{'path':str(p),'sha256':sha(p)} for p in [G,B/'cli.test.exe',B/'researchos-cli.exe',Path(__file__),N/'finite-inventory-r305.json']]
(run/'inputs.before.json').write_text(json.dumps({'compile_inputs':before,'execution_inputs':extra},indent=2),encoding='utf-8')
argv=[str(G),'tool','test2json','-t','-p','researchos.local/research-os/apps/cli',str(B/'cli.test.exe'),'-test.v','-test.timeout=480s','-test.failfast','-test.run=^'+group+'$']
start=datetime.datetime.now(datetime.timezone.utc).isoformat();out=run/'stdout.jsonl';err=run/'stderr.txt'
with out.open('wb') as o,err.open('wb') as e:
 p=subprocess.Popen(argv,cwd=W/'apps/cli',env=ENV,stdout=o,stderr=e)
 try:code=p.wait(timeout=510);timeout=False
 except subprocess.TimeoutExpired:p.kill();code=p.wait();timeout=True
end=datetime.datetime.now(datetime.timezone.utc).isoformat()
after=[dict(x,sha256=sha(x['path']),bytes=Path(x['path']).stat().st_size) for x in old];(run/'inputs.after.json').write_text(json.dumps(after,indent=2),encoding='utf-8')
rows=[]
for line in out.read_text(encoding='utf-8',errors='replace').splitlines():
 try:rows.append(json.loads(line))
 except json.JSONDecodeError:pass
counts={s:sum(x.get('Action')==s and bool(x.get('Test')) for x in rows) for s in ['pass','fail','skip']}
result={'actualargv':argv,'cwd':str(W/'apps/cli'),'started_at':start,'ended_at':end,'exit_code':code,'timeout':timeout,'event_counts_including_parent':counts,'leaf_events':[{'test':x['Test'],'action':x['Action']} for x in rows if x.get('Test') and x.get('Action') in ['pass','fail','skip'] and not any(y.get('Test','').startswith(x['Test']+'/') for y in rows)],'input_count':len(before),'source_drift':before!=after,'stdout_ref':{'path':str(out.relative_to(W)),'sha256':sha(out)},'stderr_ref':{'path':str(err.relative_to(W)),'sha256':sha(err)},'SDK_MODEL_EXTERNAL_PAID_CALLS':0,'formal_acceptance':False}
(run/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('RESULT',run,'EXIT',code,'COUNTS',counts,'DRIFT',before!=after,flush=True)
for row in rows:
 text=row.get('Output','')
 if 'FAIL' in text or 'fatal' in text.lower() or 'expected' in text.lower() or '--- SKIP' in text:print(text.rstrip(),flush=True)
sys.exit(code or (1 if before!=after else 0))
