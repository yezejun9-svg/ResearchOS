import sys
sys.dont_write_bytecode=True
from pathlib import Path
import hashlib,json,re
Q=Path(__file__).parent
T=Path('D:/作品集/ResearchOS/research-os/.local/worktrees/codex-w0599-native-harness43-d74319468b584322b516e3b8b3aee4f2')
observed=json.loads((Q/'git-source-observation.json').read_text(encoding='utf-8'))
raw=observed['DDL_raw_stdout'].encode('utf-8')
blob=hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()
def pin(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
tree={}
for line in observed['migration_constructor_tree_raw_stdout'].splitlines():
 mode,typ,obj,path=line.split(None,3);tree[path]=obj
files=sorted((T/'migrations/sqlite').glob('[0-9][0-9][0-9][0-9]_*.sql'))[:20]
rows=[]
for n,p in enumerate(files,1):
 b=p.read_bytes();obj=hashlib.sha1(b'blob '+str(len(b)).encode('ascii')+b'\0'+b).hexdigest();path='migrations/sqlite/'+p.name
 rows.append({'version':n,'filename':p.name,'actual_source_ref':pin(p),'git_path':path,'commit':observed['commit'],'git_blob':tree.get(path),'actual_git_blob':obj,'matches_fixed_historical_Git_source':obj==tree.get(path)})
compatible=(blob==observed['DDL_git_blob'] and b'transcript_artifact_id' not in raw and len(rows)==20 and all(r['matches_fixed_historical_Git_source'] and int(r['filename'][:4])==r['version'] for r in rows))
out={'authority':'NONE','historical_commit':observed['commit'],'historical_DDL_git_blob':observed['DDL_git_blob'],'observed_DDL_git_blob':blob,'migration_prefix_matches_real_historical_source':compatible,'migration_sources':rows,'historical_constructor_Git_entries':[{'git_path':p,'git_blob':b,'commit':observed['commit']} for p,b in tree.items() if p.startswith('internal/domain/')]}
if compatible:
 p=Q/'resources/pretranscript-3225a31f.sql';p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(raw)
 out['historical_DDL_resource_ref']=pin(p)
with (Q/'migration-resources.json').open('x',encoding='utf-8') as f:f.write(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'prefix_matches_real_historical_source':compatible,'source_count':len(rows),'DDL_ref':out.get('historical_DDL_resource_ref'),'constructor_entries':out['historical_constructor_Git_entries'],'nonmatching_sources':[r['filename'] for r in rows if not r['matches_fixed_historical_Git_source']]},ensure_ascii=False))
