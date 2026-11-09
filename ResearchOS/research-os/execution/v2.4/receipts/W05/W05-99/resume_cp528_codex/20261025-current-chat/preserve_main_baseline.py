"""Read-only preservation gate for the scoped Desktop continuation."""
import hashlib,json,subprocess
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');N=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def git(cwd,*args):return subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0',*args],cwd=cwd)
def verify():
 assert git(R,'rev-parse','HEAD').decode().strip()=='7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e'
 assert not git(R,'diff','--cached','--name-only')
 base=read(N/'React-Main-integration-baseline.json');assert git(R,'diff','--name-only','-z').decode().strip(chr(0)).split(chr(0))==base['dirty_paths']
 shared={'execution/v2.4/checkpoint.json','execution/v2.4/path_ownership.json','execution/v2.4/HANDOFF_RESUME_PACK.md'}
 for x in base['dirty_files']:
  if x['relative_path']in shared:continue
  p=R/x['relative_path'];assert p.is_file()==x['exists']
  if x['exists']:assert ref(p)['sha256']==x['sha256']
 refs=[]
 for x in base['protected_source']+base['original_dist_refs']+read(N/'React-Main-integration-result.json')['staged_build_refs']:
  p=Path(x['path']);a=ref(p if p.is_absolute()else R/p);assert a['sha256']==x['sha256']and a['bytes']==x['bytes'];refs.append(a)
 for name,sha in [('execution/project_identity.json','03f06a2b72ae85b3445d724058b10c8b13bcdb98f31feaf195e10b2e88fb26ec'),('.git/config','1ab6dec2977cfa8cd134b3f8f10faa732a4400a6c7de77ccc6ad336387c9a540'),('execution/v2.4/step_state.json','168c55121a874be36522e7ac5c7286cd7f90af0b7c06d1b73e444c19aa57307e')]:
  a=ref(R/name);assert a['sha256']==sha;refs.append(a)
 W=R/'.local/worktrees/qualification-maintenance-c57-20261025'
 assert git(W,'rev-parse','HEAD').decode().strip()=='03aa4d687dfaa541d9b18d4c766805307a537d1d'
 assert not git(W,'status','--porcelain=v1','--untracked-files=all')
 return {'Main':'7d1e3ff288f91254c7304dd32f6e5bb4b66b8f1e','C57_frozen':'03aa4d687dfaa541d9b18d4c766805307a537d1d','dirty_path_count':len(base['dirty_paths']),'protected':len(base['protected_source']),'old_assets':len(base['original_dist_refs']),'new_assets':len(read(N/'React-Main-integration-result.json')['staged_build_refs']),'verified_refs':refs}
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False))
