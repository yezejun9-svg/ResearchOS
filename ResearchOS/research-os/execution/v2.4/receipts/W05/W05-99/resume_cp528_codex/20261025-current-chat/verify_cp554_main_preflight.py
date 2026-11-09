import datetime, hashlib, json
from pathlib import Path
from preserve_main_baseline import verify, read, ref, git, R, N

CANDIDATE='ecc28dd3c91a0f68dcddb41b53325aa7f0e81419'
BASE='7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e'
TREE='1d44a02c9483fc529b08ffe81895ec443920bdd1'
FILES=['apps/desktop/build-development.py','apps/desktop/launch-development.mjs','apps/desktop/main/main.js','docs/installation/desktop-development.md','tests/ui/desktop/development-bundle.test.py','tests/ui/desktop/development-launcher.test.mjs','tests/ui/desktop/development-smoke.test.mjs']
W=R/'.local/worktrees/desktop-main7d-native-20261025'
def run():
 cp=read(R/'execution/v2.4/checkpoint.json'); ow=read(R/'execution/v2.4/path_ownership.json')
 assert cp['revision']==554 and ow['revision']==340 and len(cp['failure_counters'])==2244
 preserved=verify()
 assert ref(N/'continuation-cp554/RESUME.current.json')['sha256']=='4fd4af092b65a46f396da098e7099967f5567c451c2dfe1fbc3619196e543130'
 assert git(W,'rev-parse','HEAD').decode().strip()==CANDIDATE
 assert git(W,'rev-parse','HEAD^').decode().strip()==BASE
 assert git(W,'rev-parse','HEAD^{tree}').decode().strip()==TREE
 assert not git(W,'status','--porcelain=v1','--untracked-files=all')
 assert sorted(git(R,'diff','--name-only',BASE,CANDIDATE).decode().splitlines())==FILES
 rows=[]
 for f in FILES:
  blob=git(R,'show',CANDIDATE+':'+f); sha=hashlib.sha256(blob).hexdigest()
  assert ref(W/f)['sha256']==sha
  main=R/f; tracked=bool(git(R,'ls-files','--',f).strip())
  if f=='apps/desktop/main/main.js':
   assert tracked and main.read_bytes()==git(R,'show',BASE+':'+f)
  else: assert not tracked and not main.exists()
  rows.append({'path':f,'action':'M' if tracked else 'A','candidate_sha256':sha,'candidate_bytes':len(blob),'main_before_ref':ref(main) if tracked else None,'main_collision':False})
 result={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'prior_goal_turn':'PROGRESS_CP550_TO_CP554','prior_progress':['Seven-file complete Desktop development implementation','Independent source/build review','One actual owned native React/Core test and independent evidence acceptance'],'checkpoint_revision':554,'ownership_revision':340,'mixed_records':2244,'Main_branch':git(R,'branch','--show-current').decode().strip(),'Main_before':BASE,'candidate':CANDIDATE,'candidate_tree':TREE,'candidate_is_direct_child':True,'files':rows,'preserved':preserved,'C57_admin_status':'USER_PREPARING_NOT_VERIFIED','formal_increment':0}
 out=N/'CP554-live-Main-integration-preflight.json'
 with out.open('x',encoding='utf8')as s:json.dump(result,s,ensure_ascii=False,indent=2);s.write('\n')
 print(json.dumps({'result':ref(out),'Main_branch':result['Main_branch'],'seven_paths_collision_free':True,'original_dirty':20,'preserved_refs':len(preserved['verified_refs']),'formal':0},ensure_ascii=False))
if __name__=='__main__':run()
