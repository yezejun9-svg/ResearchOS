from pathlib import Path
import json,hashlib,subprocess
R=Path(r'D:\作品集\ResearchOS\research-os');E=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 x=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(x).hexdigest(),'bytes':len(x)}
for p in [Path(r'C:\Users\yqyyds\AGENTS.md'),R.parent/'AGENTS.md',R/'AGENTS.md']:
 if p.is_file():print('RULES',str(p),p.read_text(encoding='utf-8-sig'))
cp=read(R/'execution/v2.4/checkpoint.json');ow=read(R/'execution/v2.4/path_ownership.json')
print('CHECKPOINT',json.dumps({k:cp.get(k)for k in ['revision','updated_at','current_step_id','next_command']},ensure_ascii=False))
print('COUNTERS',len(cp.get('failure_counters',[])),'OWNERSHIP_REV',ow.get('revision'))
print('LATEST_WIP',json.dumps({k:v for k,v in cp.get('work_in_progress',{}).items()if any(s in k for s in ['cp52','source43','process_binding','react','frontend'])},ensure_ascii=False))
print('OWNERS',json.dumps({k:v for k,v in ow.get('special_paths',{}).items()if any(s in k for s in ['source43','process_binding','react','frontend'])},ensure_ascii=False))
def git(cwd,*a):
 r=subprocess.run(['git','-c','maintenance.auto=false','-c','gc.auto=0',*a],cwd=cwd,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 print('GIT',str(cwd),a,'EXIT',r.returncode);print(r.stdout.decode('utf8','replace'));print(r.stderr.decode('utf8','replace'))
git(R,'rev-parse','HEAD','HEAD^{tree}');git(R,'status','--porcelain=v1','--untracked-files=no');git(R,'diff','--cached','--name-only')
print('PROTECTED_REFS',json.dumps([ref(R/p)for p in ['execution/project_identity.json','.git/config','execution/v2.4/step_state.json']],ensure_ascii=False))
W=R/'.local/worktrees/source43-b-stop-finalpath-20261015'
if W.is_dir():
 git(W,'rev-parse','HEAD','HEAD^{tree}');git(W,'status','--porcelain=v1');git(W,'diff','--name-only','4f4023c956f84d65743f39ce77d6c8899a21ada1','HEAD')
for d in ['source43_b_stop_finalpath_codex','original_backup_process_binding_codex']:
 p=R/'execution/v2.4/receipts/W05/W05-99'/d/'20261015-current-chat'
 print('RECEIPTS',d,'EXISTS',p.exists(),'FILES',[x.name for x in p.iterdir()if x.is_file()]if p.exists()else[])
 for n in ['FINAL-manifest.json','FINAL.md','RESOURCE-BINDING.md']:
  q=p/n
  if q.is_file():
   print('FROZEN',ref(q))
   if n.endswith('.md'):print(q.read_text(encoding='utf-8-sig'))
p=Path(r'C:\Users\yqyyds\.codex\memories\MEMORY.md')
if p.is_file():
 r=subprocess.run(['rg','-n','ResearchOS|VALIDATED_FILE|React|frontend',str(p)],stdout=subprocess.PIPE,stderr=subprocess.PIPE);print('MEMORY_SEARCH_EXIT',r.returncode);print(r.stdout.decode('utf8','replace'))
