import hashlib,json,subprocess
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
s=read(N/'continuation-cp536/React-Main-integration-scope.json');ui=read(N/'continuation-cp534/react-workbench-redesign-source14-scope.json');git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
g=lambda *a:subprocess.check_output(git+list(a),cwd=R)
assert g('rev-parse','HEAD').decode().strip()==s['expected_Main_HEAD'];assert not g('diff','--cached','--name-only')
dirty=g('diff','--name-only','-z').decode().strip(chr(0)).split(chr(0));assert len(dirty)==20 and not set(dirty)&set(s['allowed_source_paths'])
protected=read(N/'selector-live-verification.json')['protected_source']
for x in protected:assert ref(Path(x['path']))['sha256']==x['sha256']
known=set()
for x in ui['baseline_source']:
 p=Path(x['path']);p=p if p.is_absolute()else R/p;known.add(p.resolve());assert ref(p)['sha256']==x['sha256']
for rel in s['allowed_source_paths']:
 p=R/rel
 if p.resolve()not in known:assert not p.exists(),str(p)
assert not Path(s['build_output_root']).exists()
original=Path(s['production_dist_preservation']);dist=[]
if original.is_dir():
 for p in subprocess.check_output(['rg','--files','--hidden','--no-ignore',str(original)],cwd=R).decode('utf8').splitlines():dist.append(ref(Path(p)))
out={'schema':'researchos.React-Main-integration-baseline.v1','Main_HEAD':s['expected_Main_HEAD'],'Main_branch':g('symbolic-ref','--short','HEAD').decode().strip(),'target_commit':s['target_commit'],'target_tree':s['target_tree'],'dirty_paths':dirty,'dirty_files':[{'relative_path':p,'exists':(R/p).is_file(),**(ref(R/p)if(R/p).is_file()else{})}for p in dirty],'protected_source':protected,'original_dist_exists':original.exists(),'original_dist_refs':dist,'source_inputs':ui['baseline_source'],'integration_scope':ref(N/'continuation-cp536/React-Main-integration-scope.json'),'staging_output':s['build_output'],'formal_increment':0}
with(N/'React-Main-integration-baseline.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({'Main_HEAD':out['Main_HEAD'],'branch':out['Main_branch'],'dirty_count':len(dirty),'original_dist_files':len(dist),'no_overlap':True,'protected':len(protected),'target':s['target_commit']},ensure_ascii=False))
for p in [N/'003-revalidate-frontend-paths.py']:
 if p.exists():
  lines=p.read_text(encoding='utf8').splitlines()
  print('PRIOR SELECTOR COMMAND LINES '+chr(10).join(x for x in lines if 'task_packet'in x or 'select_cmd'in x))
