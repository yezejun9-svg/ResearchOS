import datetime,json,os,pathlib,subprocess,sys
OUT=pathlib.Path(__file__).resolve().parent
SRC=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/qualification-read-lane-20261012')
NODE='C:/Users/yqyyds/AppData/Local/nvm/v24.9.0/node.exe'
which=sys.argv[1]
env=os.environ.copy();env['RESEARCHOS_DESKTOP_WIRE_ROOT']=str(SRC/'.local/qualification-build-output-v2-02/apps/desktop');env['RESEARCHOS_DESKTOP_CASE_RECEIPT']=str(OUT/(which+'-raw'));env['TEMP']=str(OUT/'temp');env['TMP']=env['TEMP']
pathlib.Path(env['TEMP']).mkdir(exist_ok=True)
args=[NODE,'--test','--test-concurrency=1']
if which=='author-targeted':args+=['--test-name-pattern=qualification-lane',str(SRC/'tests/ui/desktop/http-wire-boundary.test.mjs')]
elif which=='supplemental':args+=[str(OUT/'supplemental.mjs')]
elif which=='management':args+=[str(SRC/'tests/ui/desktop/desktop-management-boundary.test.mjs')]
else:raise ValueError(which)
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
p=subprocess.run(args,cwd=OUT,env=env,capture_output=True,timeout=180)
(OUT/(which+'.stdout.raw')).write_bytes(p.stdout);(OUT/(which+'.stderr.raw')).write_bytes(p.stderr)
(OUT/(which+'.invocation.json')).write_text(json.dumps({'argv':args,'cwd':str(OUT),'start':start,'end':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exit':p.returncode,'explicit_environment':{k:env[k] for k in ['RESEARCHOS_DESKTOP_WIRE_ROOT','RESEARCHOS_DESKTOP_CASE_RECEIPT','TEMP','TMP']}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(p.stdout.decode('utf-8',errors='replace'));print(p.stderr.decode('utf-8',errors='replace'));print('EXIT',p.returncode)
