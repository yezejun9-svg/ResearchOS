from pathlib import Path
import subprocess, json, os, datetime, sys
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[6]
WT=ROOT/'.local/worktrees/w05-normal-model-ui-repair-v2-20261012'
env=os.environ.copy()
env['RESEARCHOS_DESKTOP_WIRE_ROOT']=str(WT/'.local/w05-ui-repair-validator-final3/apps/desktop')
env['RESEARCHOS_DESKTOP_CASE_RECEIPT']=str(OUT/'baseline-http')
node='C:/nvm4w/nodejs/node.exe'
label=sys.argv[1] if len(sys.argv)>1 else 'boundary'
if label=='boundary':
    args=[node,'--test','--test-name-pattern=model-config/|prebuilder/default-configure|prebuilder/scoped-configure|prebuilder/partial-scope|revision/ack-before-concurrent-get|lifecycle/phase-raw-binding',str(WT/'tests/ui/desktop/http-wire-boundary.test.mjs')]
elif label=='extra':
    args=[node,str(OUT/'reviewer-extra.mjs')]
else:
    args=[node,str(OUT/'reviewer-dom.mjs')]
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
result=subprocess.run(args,cwd=WT,env=env,capture_output=True,timeout=180)
(OUT/(label+'.stdout')).write_bytes(result.stdout)
(OUT/(label+'.stderr')).write_bytes(result.stderr)
(OUT/(label+'.invocation.json')).write_text(json.dumps(dict(argv=args,cwd=str(WT),started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=result.returncode,model_calls=0,external_calls=0),indent=2)+'\n',encoding='utf-8')
print(result.stdout.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii')[-5000:])
print(result.stderr.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii')[-3000:])
raise SystemExit(result.returncode)
