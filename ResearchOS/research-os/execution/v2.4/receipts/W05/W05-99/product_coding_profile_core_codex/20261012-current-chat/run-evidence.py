import datetime,json,os,pathlib,subprocess,sys
out=pathlib.Path(__file__).resolve().parent
repo=out.parents[6]
wt=repo/'.local/worktrees/w05-product-coding-profile-core-20261012'
base=repo/'execution/v2.4/receipts/W05/W05-99/desktop_managed_qualification_core_repair_v2_codex/20261012-current-chat'
baseline=json.loads((base/'attempt11-frozen-host.invocation.json').read_text(encoding='utf-8'))
env=dict(os.environ);env.update(baseline['environment'])
for key in ['GOTMPDIR','TEMP','TMP']:
 p=out/'cache'/key;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
go=str(repo/'.local/tools/go1.27.1/go/bin/go.exe')
phase,prefix=sys.argv[1:3]
if phase=='format':
 paths=subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard'],cwd=wt,text=True).splitlines()
 argv=[str(pathlib.Path(go).with_name('gofmt.exe')),'-w',*[p for p in paths if p.endswith('.go')]]
elif phase in ['build-verifier','build-control']:
 build=repo/'.local/builds/product-coding-profile-core-20261012';build.mkdir(parents=True,exist_ok=True);target='runtime-verifier' if phase=='build-verifier' else 'control';argv=[go,'build','-mod=readonly','-o',str(build/(target+'.exe')),'./apps/'+target]
else:argv=[go,'test','-mod=readonly','-count=1','-json','-timeout=300s',*sys.argv[3:]]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(argv,cwd=wt,env=env,capture_output=True,timeout=420)
(out/(prefix+'.stdout')).write_bytes(r.stdout);(out/(prefix+'.stderr')).write_bytes(r.stderr)
(out/(prefix+'.invocation.json')).write_text(json.dumps(dict(argv=argv,cwd=str(wt),started=start,ended=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=r.returncode,environment={k:v for k,v in env.items() if k in baseline['environment'] or k in ['W14_GO_TOOLCHAIN','W10_EVIDENCE_DIR']},real_model_calls=0),indent=2),encoding='utf-8')
events=[]
for line in r.stdout.splitlines():
 try:events.append(json.loads(line))
 except ValueError:pass
terminal=[e for e in events if e.get('Action') in ['pass','fail','skip']]
(out/(prefix+'.summary.json')).write_text(json.dumps(terminal,indent=2),encoding='utf-8')
print(json.dumps(dict(exit=r.returncode,passes=sum(e.get('Action')=='pass' and 'Test' in e for e in terminal),fails=[e for e in terminal if e.get('Action')=='fail'],skips=[e for e in terminal if e.get('Action')=='skip'])))
if r.returncode: print(r.stderr.decode('utf-8',errors='replace'));print(r.stdout.decode('utf-8',errors='replace')[-12000:])
sys.exit(r.returncode)


