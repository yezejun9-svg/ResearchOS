from pathlib import Path
import subprocess,json,os,sys,datetime,re
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[6]
AUTHOR=OUT.parents[1]/'product_coding_profile_core_codex/20261012-current-chat'
WT=ROOT/'.local/worktrees/w05-product-coding-profile-core-20261012'
def native(s):return re.sub(r'\\u([0-9a-fA-F]{4})',lambda m:chr(int(m[1],16)),s)
label=sys.argv[1]
original='attempt36-frozen-native-lifecycle' if label=='native' else 'attempt37-frozen-regression'
inv=json.loads((AUTHOR/(original+'.invocation.json')).read_text(encoding='utf-8'))
env=dict(os.environ);env.update({k:native(v) for k,v in inv['environment'].items()})
for key in ['TEMP','TMP','GOTMPDIR','GOCACHE']:
 p=OUT/'cache'/key;p.mkdir(parents=True,exist_ok=True);env[key]=str(p)
env['RESEARCHOS_CONTROL_EXE']=str(ROOT/'.local/builds/product-coding-profile-core-20261012/control.exe')
env['RESEARCHOS_RUNTIME_VERIFIER_EXE']=str(ROOT/'.local/builds/product-coding-profile-core-20261012/runtime-verifier.exe')
args=[native(x) for x in inv['argv']]
if label=='additional':
 args=[args[0],'test','-mod=readonly','-count=1','-json','-timeout=180s','-overlay',str(OUT/'overlay.json'),'./internal/domain','-run','^TestReviewerCoding']
start=datetime.datetime.now(datetime.timezone.utc).isoformat()
r=subprocess.run(args,cwd=WT,env=env,capture_output=True,timeout=420)
(OUT/(label+'.stdout')).write_bytes(r.stdout);(OUT/(label+'.stderr')).write_bytes(r.stderr)
(OUT/(label+'.invocation.json')).write_text(json.dumps(dict(argv=args,cwd=str(WT),started_at=start,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),environment={k:v for k,v in env.items() if k.startswith(('GO','RESEARCHOS_')) or k in ['TEMP','TMP']},exit_code=r.returncode,actual_model_calls=0),indent=2)+'\n',encoding='utf-8')
events=[]
for line in r.stdout.splitlines():
 try:events.append(json.loads(line))
 except ValueError:pass
terminal=[e for e in events if e.get('Action') in ['pass','fail','skip']]
(OUT/(label+'.summary.json')).write_text(json.dumps(terminal,indent=2)+'\n',encoding='utf-8')
summary=dict(exit_code=r.returncode,parent_passes=sum(e.get('Action')=='pass' and 'Test' in e and '/' not in e['Test'] for e in terminal),subtest_passes=sum(e.get('Action')=='pass' and '/' in e.get('Test','') for e in terminal),failures=[e for e in terminal if e.get('Action')=='fail'],skips=[e for e in terminal if e.get('Action')=='skip'])
print(json.dumps(summary))
if r.returncode:print(r.stderr.decode('utf-8',errors='replace').encode('ascii',errors='backslashreplace').decode('ascii'));print(r.stdout.decode('utf-8',errors='replace')[-12000:].encode('ascii',errors='backslashreplace').decode('ascii'))
raise SystemExit(r.returncode)
