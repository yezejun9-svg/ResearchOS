from pathlib import Path
import json,subprocess,os,datetime,sys
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6];WT=ROOT/'.local/worktrees/w05-product-coding-client-20261012';BUILD=WT/'.local/coding-client-bound-final3'
node=Path('C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe');label=sys.argv[1]
script={'counterexamples':'counterexamples.mjs','boundary':'bound-coding-boundary.test.mjs','dom':'status-refresh-dom.mjs'}[label]
env=dict(os.environ);temp=OUT/'test-temp';temp.mkdir(exist_ok=True);env['TEMP']=env['TMP']=str(temp)
env['RESEARCHOS_SHARED_ROOT']=str(ROOT);env['RESEARCHOS_UI_SOURCE']=str(BUILD/'apps/web/src/workbench.jsx');env['RESEARCHOS_BOUND_APP']=str(BUILD/'apps/desktop')
args=[str(node)]+(['--test'] if label=='boundary' else [])+[str(OUT/script)]
start=datetime.datetime.now(datetime.timezone.utc).isoformat();r=subprocess.run(args,cwd=OUT,env=env,capture_output=True,timeout=120)
(OUT/(label+'.stdout')).write_bytes(r.stdout);(OUT/(label+'.stderr')).write_bytes(r.stderr)
(OUT/(label+'.invocation.json')).write_text(json.dumps(dict(argv=args,cwd=str(OUT),started_at=start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),exit_code=r.returncode,actual_model_calls=0,actual_tool_calls=0),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(r.stdout.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode());print(r.stderr.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode());raise SystemExit(r.returncode)
