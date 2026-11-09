from pathlib import Path
import subprocess,json,os,sys,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-desktop-managed-qualification-client-repair-v2-20261012'
BUILD=WT/'.local/managed-client-repair-v2-bound-final'
env=os.environ.copy();(OUT/'test-temp').mkdir(exist_ok=True)
env['TEMP']=env['TMP']=str(OUT/'test-temp')
env['RESEARCHOS_DESKTOP_WIRE_ROOT']=str(BUILD/'apps/desktop')
label=sys.argv[1]
env['RESEARCHOS_DESKTOP_CASE_RECEIPT']=str(OUT/(label+'-http'))
node='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe'
if label=='boundary':args=[node,'--test',str(OUT/'bound-boundary.test.mjs')]
elif label=='ui-v5-regression':args=[node,'--test','--test-name-pattern=model-config/|prebuilder/default-configure|prebuilder/scoped-configure|prebuilder/partial-scope|revision/ack-before-concurrent-get',str(WT/'tests/ui/desktop/http-wire-boundary.test.mjs')]
else:args=[node,str(OUT/(label+'.mjs'))]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
result=subprocess.run(args,cwd=WT,env=env,capture_output=True,timeout=240)
(OUT/(label+'.stdout')).write_bytes(result.stdout);(OUT/(label+'.stderr')).write_bytes(result.stderr)
(OUT/(label+'.invocation.json')).write_text(json.dumps(dict(argv=args,cwd=str(WT),environment={k:v for k,v in env.items() if k.startswith('RESEARCHOS_') or k in ['TEMP','TMP']},started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=result.returncode,model_calls=0,external_calls=0),indent=2)+'\n',encoding='utf-8')
print(result.stdout.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii')[-2500:]);print(result.stderr.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii')[-1000:])
raise SystemExit(result.returncode)
