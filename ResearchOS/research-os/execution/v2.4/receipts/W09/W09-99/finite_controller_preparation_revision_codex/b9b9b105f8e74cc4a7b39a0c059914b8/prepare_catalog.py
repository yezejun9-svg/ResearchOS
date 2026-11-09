"""Preparation metadata only: bounded read-only Git; no candidate imports."""
import hashlib,json,pathlib,subprocess,time
P=pathlib.Path(__file__).resolve().parent
R=pathlib.Path('D:/作品集/ResearchOS/research-os')
G='C:/Program Files/Git/cmd/git.exe'
C='cd0d818baa703fbc59a6f7c8187d467d41570094'
SEED=R/'execution/v2.4/receipts/W05/W05-99/cli_exact8_execution_preparation_codex/7d5925dba96b4c04baa2b6e6e33d164f/public_compiler_export_plan.v2.json'
def put(name,b):
 with (P/name).open('xb') as f:f.write(b)
def save(name,x):put(name,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def ref(p):
 b=p.read_bytes();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def git(label,args,data=None):
 argv=[G,*args];start=time.time();q=subprocess.run(argv,cwd=R,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
 put(label+'.stdout.raw',q.stdout);put(label+'.stderr.raw',q.stderr)
 if data is not None:put(label+'.stdin.raw',data)
 save(label+'.invocation.json',{'argv':argv,'cwd':str(R),'actual_native_exit':q.returncode,'started':start,'ended':time.time(),'read_only':True})
 if q.returncode:raise RuntimeError('First unexpected read-only Git failure: '+label)
 return q.stdout
seed=json.loads(SEED.read_bytes())
tree=git('git-public-tree',['ls-tree','-r','-z',C,'--','internal','adapters','ops','evaluation','migrations','spec','go.mod','go.sum'])
entries={}
for part in tree.split(b'\0'):
 if not part:continue
 head,path=part.split(b'\t',1);mode,kind,oid=head.decode().split();path=path.decode('utf-8','strict')
 entries[path]={'path':path,'mode':mode,'type':kind,'git_blob':oid}
names={r['path'] for r in seed['git_resources'] if r['path'] in entries}
names|={p for p in entries if p.endswith('.go') and p.startswith(('internal/','adapters/','ops/','evaluation/'))}
names|={p for p in entries if p.startswith('migrations/sqlite/') and p.endswith('.sql')}
names|={'go.mod','go.sum'}
rows=[entries[p] for p in sorted(names)]
if len(rows)>4096 or any(r['mode']!='100644' or r['type']!='blob' for r in rows):raise RuntimeError('Public source catalog mode/count')
batch=''.join(r['git_blob']+'\n' for r in rows).encode('ascii')
raw=git('git-public-blobs',['cat-file','--batch'],batch);pos=0;embeds=[]
for row in rows:
 end=raw.index(b'\n',pos);oid,kind,size=raw[pos:end].decode('ascii').split();size=int(size);pos=end+1
 body=raw[pos:pos+size];pos+=size
 if oid!=row['git_blob'] or kind!='blob' or raw[pos:pos+1]!=b'\n' or len(body)!=size:raise RuntimeError('Git batch framing')
 pos+=1;row.update(sha256=hashlib.sha256(body).hexdigest(),bytes=size)
 if row['path'].endswith('.go'):
  for n,line in enumerate(body.decode('utf-8','strict').splitlines(),1):
   if line.strip().startswith('//go:embed '):embeds.append({'path':row['path'],'line':n,'directive':line.strip()})
if pos!=len(raw):raise RuntimeError('Trailing Git output')
save('public-source-catalog.json',{'schema':'researchos.w09.public-source-catalog.v2','source_commit':C,'base_commit':'2cdb0d43d5a600eef13c8f1735946a9adf52d079','seed_ref':ref(SEED),'selection':'Existing approved public catalog reconciled to exact candidate plus public Go sources in internal/adapters/ops/evaluation and numbered/additive migration SQL. No holdout data, vault, or untracked input. Compilation closure remains NOT_RUN.','files':rows,'file_count':len(rows),'embed_directives':embeds,'omitted_seed_paths':[r['path'] for r in seed['git_resources'] if r['path'] not in entries],'combined_Main_source_commit':None,'actual_compilation_closure':None})
print(json.dumps({'file_count':len(rows),'ops_evaluation':[r['path'] for r in rows if r['path'].startswith(('ops/','evaluation/'))],'embed_directives':embeds,'catalog_ref':ref(P/'public-source-catalog.json')},ensure_ascii=False))
