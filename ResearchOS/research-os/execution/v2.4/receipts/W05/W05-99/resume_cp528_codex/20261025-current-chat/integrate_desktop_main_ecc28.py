import datetime,json,subprocess
from preserve_main_baseline import verify as before,read,ref,git,R,N
from preserve_desktop_main_ecc28 import verify as after
from verify_cp554_main_preflight import BASE,CANDIDATE,TREE,FILES

def new(p,v):
 with p.open('x',encoding='utf8')as s:json.dump(v,s,ensure_ascii=False,indent=2);s.write('\n')
cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json')
assert cp['revision']==555 and ow['revision']==341 and len(cp['failure_counters'])==2250
scope=read(N/'continuation-cp555/Desktop-Main-integration-scope.json')
assert scope['candidate']==CANDIDATE and scope['base']==BASE and scope['allowed_paths']==FILES and scope['operation']=='LOCAL_FAST_FORWARD_ONLY'
assert ref(N/'integrate_desktop_main_ecc28.py')==scope['runner_ref']
assert ref(N/'preserve_desktop_main_ecc28.py')==scope['post_gate_ref']
for x in scope['bound_evidence']:
 p=__import__('pathlib').Path(x['path']);a=ref(p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes']
prior=before();assert git(R,'branch','--show-current').decode().strip()=='main'
assert git(R,'rev-parse',CANDIDATE+'^').decode().strip()==BASE
assert sorted(git(R,'diff','--name-only',BASE,CANDIDATE).decode().splitlines())==FILES
for f in FILES:
 if f!='apps/desktop/main/main.js':assert not(R/f).exists()
 else:assert(R/f).read_bytes()==git(R,'show',BASE+':'+f)
O=N/'desktop-main-integration-01';O.mkdir()
new(O/'preservation.before.json',prior)
argv=['git','-c','maintenance.auto=false','-c','gc.auto=0','merge','--ff-only','--no-edit',CANDIDATE]
new(O/'git-command.json',{'argv':argv,'cwd':str(R),'at':datetime.datetime.now(datetime.timezone.utc).isoformat()})
r=subprocess.run(argv,cwd=R,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
(O/'git.stdout.raw').write_bytes(r.stdout);(O/'git.stderr.raw').write_bytes(r.stderr)
new(O/'git-result.json',{'native_exit':r.returncode,'stdout':ref(O/'git.stdout.raw'),'stderr':ref(O/'git.stderr.raw')})
if r.returncode:raise SystemExit(r.returncode)
current=after();new(O/'preservation.after.json',current)
new(O/'result.json',{'status':'EXACT_SEVEN_PATH_FAST_FORWARD_INTEGRATED_PENDING_INDEPENDENT_POST_REVIEW','Main':CANDIDATE,'tree':TREE,'previous_Main':BASE,'git_native_exit':0,'original_dirty_preserved':20,'protected_refs':48,'candidate_file_refs':7,'original_data_action':False,'C57_merge':False,'source_or_native_retest':False,'formal_increment':0,'scope_ref':ref(N/'continuation-cp555/Desktop-Main-integration-scope.json'),'before_ref':ref(O/'preservation.before.json'),'after_ref':ref(O/'preservation.after.json')})
print(json.dumps({'result':ref(O/'result.json'),'Main':CANDIDATE,'tree':TREE,'git_native_exit':0,'formal_increment':0},ensure_ascii=False))
