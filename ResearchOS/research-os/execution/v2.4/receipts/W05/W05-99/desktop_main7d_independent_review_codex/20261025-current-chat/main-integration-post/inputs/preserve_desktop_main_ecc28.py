"""Post-integration gate. Original Main7d preservation evidence stays immutable."""
import hashlib
from pathlib import Path
from preserve_main_baseline import read,ref,git,R,N
from verify_cp554_main_preflight import BASE,CANDIDATE,TREE,FILES,W

def verify():
 assert git(R,'rev-parse','HEAD').decode().strip()==CANDIDATE
 assert git(R,'rev-parse','HEAD^{tree}').decode().strip()==TREE
 assert git(R,'branch','--show-current').decode().strip()=='main'
 assert not git(R,'diff','--cached','--name-only')
 original=read(N/'React-Main-integration-baseline.json')
 assert git(R,'diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==original['dirty_paths']
 shared={'execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/HANDOFF_RESUME_PACK.md'}
 for x in original['dirty_files']:
  if x['relative_path']in shared:continue
  p=R/x['relative_path'];assert p.is_file()==x['exists']
  if x['exists']:assert ref(p)['sha256']==x['sha256']
 pre=read(N/'CP554-live-Main-integration-preflight.json');refs=[]
 for x in pre['preserved']['verified_refs']:
  a=ref(Path(x['path']));assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
 for x in pre['files']:
  a=ref(R/x['path']);assert a['sha256']==x['candidate_sha256']and a['bytes']==x['candidate_bytes']
  assert hashlib.sha256(git(R,'show','HEAD:'+x['path'])).hexdigest()==a['sha256'];refs.append(a)
 assert git(W,'rev-parse','HEAD').decode().strip()==CANDIDATE and not git(W,'status','--porcelain=v1','--untracked-files=all')
 C=R/'.local/worktrees/qualification-maintenance-c57-20261025'
 assert git(C,'rev-parse','HEAD').decode().strip()=='03aa4d687dfaa541d9b18d4c766805307a537d1d'
 assert not git(C,'status','--porcelain=v1','--untracked-files=all')
 return {'Main':CANDIDATE,'Main_tree':TREE,'Main_previous':BASE,'C57_frozen':'03aa4d687dfaa541d9b18d4c766805307a537d1d','dirty_path_count':20,'protected':9,'old_assets':33,'new_assets':3,'integrated_exact_paths':FILES,'verified_refs':refs}
