from pathlib import Path
import json,subprocess,os,datetime,sys
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-desktop-parent-image-observation-repair-20261012'
AUTHOR=OUT.parents[1]/'product_parent_image_observation_repair_codex/20261012-current-chat'
inv=json.loads((AUTHOR/'attempt08-frozen-observation.invocation.json').read_text(encoding='utf-8'))
label=sys.argv[1];env=dict(os.environ);env.update(inv['environment'])
for k in ['TEMP','TMP','GOTMPDIR','GOCACHE']:
 p=OUT/'cache'/k;p.mkdir(parents=True,exist_ok=True);env[k]=str(p)
env['RESEARCHOS_CONTROL_EXE']=str(ROOT/'.local/builds/product-parent-image-observation-repair-20261012/control.exe')
env['RESEARCHOS_RUNTIME_VERIFIER_EXE']=str(ROOT/'.local/builds/product-parent-image-observation-repair-20261012/runtime-verifier.exe')
args=inv['argv']
if label=='causal':
 args=args[:];i=args.index('./ops/supervisor');args[i:i]=['-overlay',str(OUT/'overlay.json')];args[args.index('-run')+1]='^TestReviewerParentImage'
start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(args,cwd=WT,env=env,capture_output=True,timeout=360)
(OUT/(label+'.stdout')).write_bytes(r.stdout);(OUT/(label+'.stderr')).write_bytes(r.stderr)
(OUT/(label+'.invocation.json')).write_text(json.dumps(dict(argv=args,cwd=str(WT),started_at=start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment={k:v for k,v in env.items() if k.startswith(('GO','RESEARCHOS_')) or k in ['TEMP','TMP']},exit_code=r.returncode,actual_model_calls=0),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
events=[]
for line in r.stdout.splitlines():
 try:events.append(json.loads(line))
 except ValueError:pass
terminal=[x for x in events if x.get('Action') in ['pass','fail','skip']]
(OUT/(label+'.summary.json')).write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(exit_code=r.returncode,parent_passes=sum(x['Action']=='pass' and 'Test'in x and '/'not in x['Test'] for x in terminal),subtest_passes=sum(x['Action']=='pass' and '/'in x.get('Test','') for x in terminal),failures=[x for x in terminal if x['Action']=='fail'],skips=[x for x in terminal if x['Action']=='skip'])))
if r.returncode:print(r.stderr.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode());print(r.stdout[-16000:].decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode())
raise SystemExit(r.returncode)
