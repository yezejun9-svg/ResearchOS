from pathlib import Path
import subprocess,json,os,sys,datetime
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v3-20261012'
env=os.environ.copy()
env['RESEARCHOS_DESKTOP_WIRE_ROOT']=str(ROOT/'.local/worktrees/w05-normal-model-ui-repair-v2-20261012/.local/w05-ui-repair-validator-final3/apps/desktop')
env['RESEARCHOS_DESKTOP_CASE_RECEIPT']=str(OUT/'baseline-http')
label=sys.argv[1]
node='C:/nvm4w/nodejs/node.exe'
if label=='boundary':
    args=[node,'--test','--test-name-pattern=model-config/|prebuilder/default-configure|prebuilder/scoped-configure|prebuilder/partial-scope|revision/ack-before-concurrent-get|lifecycle/phase-raw-binding',str(WT/'tests/ui/desktop/http-wire-boundary.test.mjs')]
elif label=='baseline-dom':args=[node,str(OUT/'baseline-dom.mjs')]
else:args=[node,str(OUT/'host-race-dom.mjs')]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
result=subprocess.run(args,cwd=WT,env=env,capture_output=True,timeout=180)
(OUT/(label+'.stdout')).write_bytes(result.stdout)
(OUT/(label+'.stderr')).write_bytes(result.stderr)
(OUT/(label+'.invocation.json')).write_text(json.dumps(dict(argv=args,cwd=str(WT),started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=result.returncode,model_calls=0,external_calls=0,current_v3_full_build_binding=False),indent=2)+'\n',encoding='utf-8')
print(result.stdout.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii')[-3500:])
print(result.stderr.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii')[-2000:])
raise SystemExit(result.returncode)
