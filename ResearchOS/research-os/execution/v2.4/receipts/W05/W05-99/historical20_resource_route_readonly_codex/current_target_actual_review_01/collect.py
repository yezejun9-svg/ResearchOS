import sys
sys.dont_write_bytecode=True
import subprocess,json,hashlib,re
from pathlib import Path
R=Path('D:/作品集/ResearchOS/research-os');T=R/'.local/worktrees/codex-w0599-current-attach-q5-leg2-1791509207371';O=Path(__file__).resolve().parent
COMMIT='3225a31fd25969c6a5e071a2fc686cb4a835e162';io=[];pins=[]
def pin(p):
 p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
def save(n,v):
 p=O/n;p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode())
 return pin(p)
def git(label,args):
 p=subprocess.run(['git','-C',str(R),*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
 out=O/'git-raw'/(label+'.stdout.raw');err=O/'git-raw'/(label+'.stderr.raw');out.parent.mkdir(exist_ok=True)
 out.write_bytes(p.stdout);err.write_bytes(p.stderr)
 io.append(dict(argv=['git','-C',str(R),*args],actual_exit=p.returncode,stdout_ref=pin(out),stderr_ref=pin(err)))
 if p.returncode!=0:save('git-original-io.json',io);raise RuntimeError('git read failed: '+label)
 return p.stdout
identity=pin(R/'execution/project_identity.json');head=git('head-before',['rev-parse','HEAD']).decode().strip()
root=git('repo-root',['rev-parse','--show-toplevel']).decode().strip();tree=git('tree-id',['rev-parse',COMMIT+'^{tree}']).decode().strip()
rawtree=git('full-tree',['ls-tree','-r','-z','--full-tree',COMMIT]);entries=[]
for line in rawtree.split(b'\0'):
 if not line:continue
 metadata,path=line.split(b'\t',1);mode,typ,oid=metadata.decode().split();entries.append(dict(mode=mode,type=typ,oid=oid,path=path.decode('utf-8')))
save('full-tree.index.json',entries)
selection=[]
for e in entries:
 p=e['path']
 if e['type']!='blob':continue
 if p in ('go.mod','go.sum','AGENTS.md','VERSION','execution/toolchains/locked.json') or (p.startswith(('apps/','cmd/','internal/','adapters/','evaluation/','ops/')) and p.endswith('.go') and '/node_modules/' not in p) or p.startswith('migrations/sqlite/') or (p.startswith('spec/v2.0/contracts/') and p.endswith('.json')):
  selection.append(e)
batch_input=b''.join((e['oid']+'\n').encode() for e in selection)
p=subprocess.run(['git','-C',str(R),'cat-file','--batch'],input=batch_input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
bp=O/'git-raw/cat-file-batch.stdin.raw';bp.write_bytes(batch_input)
bo=O/'git-raw/cat-file-batch.stdout.raw';bo.write_bytes(p.stdout)
be=O/'git-raw/cat-file-batch.stderr.raw';be.write_bytes(p.stderr)
io.append(dict(argv=['git','-C',str(R),'cat-file','--batch'],actual_exit=p.returncode,stdin_ref=pin(bp),stdout_ref=pin(bo),stderr_ref=pin(be)))
assert p.returncode==0
pos=0;entrypoints=[];embeds=[];imports=set()
for e in selection:
 end=p.stdout.index(b'\n',pos);header=p.stdout[pos:end].decode().split();size=int(header[2]);body=p.stdout[end+1:end+1+size];pos=end+1+size+1
 assert header[0]==e['oid'] and header[1]=='blob' and hashlib.sha1(b'blob '+str(size).encode()+b'\0'+body).hexdigest()==e['oid']
 dest=O/'historical-source'/e['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(body);pins.append(dict(tree_entry=e,source_copy=pin(dest)))
 if e['path'].endswith('.go'):
  text=body.decode('utf-8')
  if re.search(r'^func main\(',text,re.M):entrypoints.append(e['path'])
  for n,l in enumerate(text.splitlines(),1):
   if '//go:embed' in l:embeds.append(dict(path=e['path'],line=n,directive=l.strip()))
  for block in re.findall(r'(?m)^import\s+(?:\((.*?)\)|([^\n]+))',text,re.S):
   imports.update(re.findall(r'"([^"\n]+)"',' '.join(block)))
assert pos==len(p.stdout)
current=[]
for base in ('apps','cmd','internal/recoveryauthority','internal/domain','migrations/sqlite'):
 d=T/base
 if not d.is_dir():continue
 for f in sorted(d.rglob('*')):
  if not f.is_file():continue
  rel=f.relative_to(T).as_posix()
  if '/node_modules/' in rel:continue
  select=(f.suffix=='.go' and (rel.startswith(('cmd/','internal/recoveryauthority/')) or f.name.startswith(('backup_','store','migration')) or rel.startswith('apps/control/'))) or rel.startswith('migrations/sqlite/')
  if select:
   dest=O/'current-source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes());current.append(dict(original=pin(f),copy=pin(dest)))
for rel in ('go.mod','go.sum','execution/toolchains/locked.json'):
 f=T/rel
 if f.is_file():
  dest=O/'current-source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes());current.append(dict(original=pin(f),copy=pin(dest)))
head_after=git('head-after',['rev-parse','HEAD']).decode().strip();assert head==head_after=='adc460c2138528f163f7fdab5e8d81dde157b7fb' and identity==pin(R/'execution/project_identity.json')
save('git-original-io.json',io);save('historical-source.pins.json',pins);save('current-source.pins.json',current)
summary={'commit':COMMIT,'tree':tree,'head':head,'identity':identity,'repo_root':root,'tree_entries':len(entries),'selected_historical_files':len(selection),'current_files':len(current),'entrypoints':entrypoints,'embeds':embeds,'imports':sorted(imports),'matching_historical_DDL_blobs':[e for e in entries if e['oid']=='9efc768f8f4cfb6ac31e1f88a78ad095877328af'],'migrations':[e for e in entries if e['path'].startswith('migrations/sqlite/')],'compile_executed':False,'product_execution':False,'model_calls':0,'SQL_execution':False,'private_keys_read':False,'Main_canonical_Source_writes':False}
save('resource-inventory.json',summary)
print(json.dumps(summary,ensure_ascii=False))
