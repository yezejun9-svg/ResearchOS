"""New frozen-source QA only. No old DB, caller registration or resource start."""
from pathlib import Path
import datetime,hashlib,json,os,re,shutil,subprocess,sys,time

ROOT=Path(__file__).resolve().parent
MAIN=Path('D:/作品集/ResearchOS/research-os')
CANDIDATE=MAIN/'.local/worktrees/coding-delivery-binding-20261104'
PINFILE=ROOT/'FINAL-PINS.json'
RUN=ROOT/'run-01'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(name,value):
 path=RUN/name
 with path.open('x',encoding='utf-8',newline='\n') as stream:json.dump(value,stream,indent=2,ensure_ascii=False);stream.write('\n')
pins=json.loads(PINFILE.read_bytes())
assert pins['status']=='ROOT_NOTIFIED_FINAL_FREEZE'
assert pins['base_head']=='b84b065739d64a61407ca815651880b6c06ae36a'
assert len(pins['source_sha256'])==4
def source_match():return all(sha(CANDIDATE/name)==digest for name,digest in pins['source_sha256'].items())
assert source_match()
lock=MAIN/'execution/toolchains/locked.json'
tools=json.loads(lock.read_bytes())['tools']
assert tools['go']['sha256']=='d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490'
assert tools['python']['sha256']=='cce21c0e8710e304273e98ac4b2b0f5aceb639acbcd2343cbaa5c4e81619c45b'
for name in ('go','python'):assert sha(tools[name]['path'])==tools[name]['sha256']
assert Path(sys.executable).resolve()==Path(tools['python']['path']).resolve()
RUN.mkdir(parents=True,exist_ok=False)
shutil.copyfile(Path(__file__),RUN/'controller.py.txt')
shutil.copyfile(PINFILE,RUN/'freeze-inputs.json')
for name in pins['source_sha256']:
 target=RUN/'frozen-source'/(name+'.txt');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(CANDIDATE/name,target)
private=RUN/'private'
overrides={}
for name,relative in {'GOCACHE':'go-cache','GOPATH':'gopath','GOMODCACHE':'gopath/pkg/mod','GOTMPDIR':'go-tmp','TEMP':'tmp','TMP':'tmp','USERPROFILE':'profile','APPDATA':'profile/AppData/Roaming','LOCALAPPDATA':'profile/AppData/Local'}.items():
 path=private/relative;path.mkdir(parents=True,exist_ok=True);overrides[name]=str(path)
overrides.update(GOROOT=str(Path(tools['go']['path']).parent.parent),GOPROXY='off',GOSUMDB='off',GOENV='off',GOTOOLCHAIN='local',GOTELEMETRY='off',GOWORK='off',GOFLAGS='-mod=readonly',GO111MODULE='on',CGO_ENABLED='0',GOCACHEPROG='',PYTHONDONTWRITEBYTECODE='1')
env=dict(os.environ,**overrides)
put('inputs.json',{'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'freeze_pins':pins,'tools':{name:tools[name] for name in ('go','python')},'tool_lock_sha256':sha(lock),'environment_overrides':overrides,'test_scope':'Original frozen binding tests + additional C Go overlay; new SQLite t.TempDir only, no old DB or native/model/Core/API.','author_attempt04_vet':'UNKNOWN_PRESERVED_NO_REPLAY','formal_increment':0})

# The dependency store on D is read-only: copy public download metadata and the
# selected existing zip archives to an owned C module cache before offline Go.
source_cache=MAIN/'.local/tools/gopath/pkg/mod/cache/download'
target_cache=Path(overrides['GOMODCACHE'])/'cache/download'
target_cache.mkdir(parents=True,exist_ok=True)
copied=[]
for path in sorted(source_cache.rglob('*')):
 if not path.is_file() or path.suffix in ('.zip','.lock','.partial','.tmp'):continue
 relative=path.relative_to(source_cache);target=target_cache/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
 copied.append({'path':str(relative).replace('\\','/'),'bytes':target.stat().st_size,'sha256':sha(target)})
modules=[]
for line in (CANDIDATE/'go.mod').read_text(encoding='utf-8').splitlines():
 found=re.fullmatch(r'\s*(?:require\s+)?([^\s()]+)\s+(v[^\s]+)(?:\s+//.*)?\s*',line)
 if found:modules.append(found.groups())
def escape(value):return ''.join('!'+char.lower() if char.isupper() else char for char in value)
for module,version in modules:
 relative=Path(escape(module))/ '@v' /(escape(version)+'.zip')
 source=source_cache/relative;target=target_cache/relative
 if source.is_file():
  target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
  copied.append({'path':str(relative).replace('\\','/'),'bytes':target.stat().st_size,'sha256':sha(target)})
 else:
  unpacked=MAIN/'.local/tools/gopath/pkg/mod'/(escape(module)+'@'+escape(version))
  if not unpacked.is_dir():raise RuntimeError('OFFLINE_PUBLIC_DEPENDENCY_MISSING '+module+' '+version)
  shutil.copytree(unpacked,Path(overrides['GOMODCACHE'])/(escape(module)+'@'+escape(version)))
  copied.append({'unpacked_module':module,'version':version,'source':str(unpacked),'reason':'source zip absent; complete existing public source copy'})
put('offline-dependency-copy.json',{'source_read_only':str(source_cache),'target':str(target_cache),'copied':copied,'network':False})
print(json.dumps({'phase':'private_offline_dependencies_prepared','selected_modules':len(modules),'files_copied':len(copied)}),flush=True)

overlay_source=ROOT/'independent_relationship_test.go'
shutil.copyfile(overlay_source,RUN/'independent_relationship_test.go.txt')
overlay=RUN/'overlay.json'
virtual=CANDIDATE/'internal/domain/coding_delivery_binding_independent_review_test.go'
put('overlay.json',{'Replace':{str(virtual):str(overlay_source)}})
put('overlay-input.json',{'path':str(overlay_source),'sha256':sha(overlay_source),'virtual_package_file':str(virtual),'physical_candidate_write':False})
go=tools['go']['path']
commands=[
 ('original-tests',[go,'test','-mod=readonly','-count=1','-timeout=120s','-json','-vet=off','-run','^TestCodingDeliveryBinding','./internal/domain']),
 ('independent-tests',[go,'test','-mod=readonly','-count=1','-timeout=120s','-json','-vet=off','-overlay',str(overlay),'-run','^TestReviewCodingDeliveryBinding','./internal/domain']),
 ('independent-vet',[go,'vet','-mod=readonly','./internal/domain']),
]
results=[]
for name,argv in commands:
 assert source_match(),'FROZEN_SOURCE_DRIFT_BEFORE_'+name
 put(name+'.command.json',{'argv':argv,'cwd':str(CANDIDATE),'environment_overrides':overrides,'source_sha256':pins['source_sha256']})
 start=time.monotonic()
 with (RUN/(name+'.stdout.txt')).open('wb') as out,(RUN/(name+'.stderr.txt')).open('wb') as err:
  try:
   process=subprocess.Popen(argv,cwd=CANDIDATE,env=env,stdout=out,stderr=err)
   put(name+'.started.json',{'pid':process.pid,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'argv':argv})
   try:code=process.wait(timeout=420);cause=None
   except subprocess.TimeoutExpired:process.kill();code=process.wait();cause='REVIEW_TOOL_TIMEOUT_AFTER_420_SECONDS'
  except OSError as error:code=125;cause=repr(error)
 result={'name':name,'exit_code':code,'cause':cause,'elapsed_seconds':round(time.monotonic()-start,3),'terminal':True,'source_unchanged':source_match()}
 if name.endswith('tests'):
  events=[]
  for line in (RUN/(name+'.stdout.txt')).read_text(encoding='utf-8').splitlines():
   try:events.append(json.loads(line))
   except ValueError:pass
  run_names={item['Test'] for item in events if item.get('Action')=='run' and 'Test' in item}
  pass_names={item['Test'] for item in events if item.get('Action')=='pass' and 'Test' in item}
  result.update(run_test_count=len(run_names),pass_test_count=len(pass_names),run_pass_rosters_equal=run_names==pass_names,top_level_passed=len([n for n in pass_names if '/' not in n]),subtests_passed=len([n for n in pass_names if '/' in n]),failed=[item.get('Test',item.get('Package')) for item in events if item.get('Action')=='fail'],skipped=[item.get('Test') for item in events if item.get('Action')=='skip'],package_terminal_pass=any(item.get('Action')=='pass' and 'Test' not in item for item in events))
  if code==0 and (not run_names or run_names!=pass_names or result['skipped'] or not result['package_terminal_pass']):result['review_roster_error']='Cannot grant test success without actual complete run/pass roster.'
 put(name+'.result.json',result);results.append(result);print(json.dumps(result),flush=True)
first_failure=next((r for r in results if r['exit_code']!=0 or r.get('review_roster_error') or not r['source_unchanged']),None)
put('result.json',{'status':'FOUNDATION_QA_PASSED_NOT_PRODUCT_ACCEPTANCE' if first_failure is None else 'INDEPENDENT_QA_FAILURE_PRESERVED','results':results,'first_failure':first_failure,'frozen_source_unchanged':source_match(),'author_attempt04_vet':'UNKNOWN_PRESERVED','formal_increment':0,'old_database_connections':0,'native_model_provider_runs':0,'D_source_writes':0,'counter_reset':False})
raise SystemExit(0 if first_failure is None else 1)
