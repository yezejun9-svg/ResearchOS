import json,subprocess,hashlib
from pathlib import Path
R=Path("D:/作品集/ResearchOS/research-os");N=Path(__file__).parent
s=json.loads((N/'continuation-cp530/react-workbench-redesign-source-scope.json').read_text(encoding='utf8'))
git=['git','-c','maintenance.auto=false','-c','gc.auto=0']
dirty=subprocess.check_output(git+['diff','--name-only','-z'],cwd=R).decode('utf8').strip(chr(0)).split(chr(0))
overlap=sorted(set(dirty)&set(s['source_allowlist']))
baseline_delta=[]
for rel in s['source_allowlist']:
 p=R/rel
 if p.is_file():
  q=subprocess.run(git+['show',s['base_commit']+':'+rel],cwd=R,capture_output=True)
  if q.returncode==0 and hashlib.sha256(q.stdout).hexdigest()!=hashlib.sha256(p.read_bytes()).hexdigest():baseline_delta.append(rel)
out={'main_dirty_paths':dirty,'react_dirty_overlap':overlap,'react_baseline_vs_commit_delta':baseline_delta,'scope_baseline_hashes_verified':True}
for x in s['baseline_source']:
 p=Path(x['path']);p=p if p.is_absolute()else R/p
 assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
with (N/'React-original-change-overlap-verification.json').open('x',encoding='utf8')as f:json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps(out,ensure_ascii=False,indent=2))
