from pathlib import Path
import json,os,subprocess,datetime
OUT=Path(__file__).resolve().parent; ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-runtime-qualification-repair-v2-20261012'
baseline=json.loads((OUT/'host.invocation.json').read_text(encoding='utf-8'))
env=dict(os.environ); env.update(baseline['environment'])
argv=baseline['argv'].copy()
argv[argv.index('-run')+1]='^TestReviewer(VerifierRevokedBeforeAcceptance|UnknownPolicyDriftBeforeAcceptance|ServiceRootRevokedBeforeAcceptanceConfirmed)$'
argv[2:2]=['-overlay='+str(OUT/'reviewer-original-overlay.json')]
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(argv,cwd=WT,env=env,capture_output=True,timeout=300)
(OUT/'counterexamples.stdout').write_bytes(r.stdout);(OUT/'counterexamples.stderr').write_bytes(r.stderr)
(OUT/'counterexamples.invocation.json').write_text(json.dumps({'argv':argv,'cwd':str(WT),'started':start,'ended':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit_code':r.returncode,'environment':baseline['environment'],'real_model_calls':0},indent=2)+'\n',encoding='utf-8')
events=[]
for line in r.stdout.splitlines():
    try: events.append(json.loads(line))
    except ValueError: pass
terminal=[{k:e[k] for k in ['Action','Package','Test','Elapsed'] if k in e} for e in events if e.get('Action') in ['pass','fail','skip']]
(OUT/'counterexamples.summary.json').write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'exit':r.returncode,'terminal':terminal}))
if r.returncode: print(r.stderr.decode('utf-8',errors='replace'));print(r.stdout.decode('utf-8',errors='replace'))
raise SystemExit(r.returncode)
