import hashlib,json,pathlib,subprocess,time,re
P=pathlib.Path(__file__).resolve().parent;R=pathlib.Path('D:/作品集/ResearchOS/research-os');G='C:/Program Files/Git/cmd/git.exe';C='cd0d818baa703fbc59a6f7c8187d467d41570094'
def put(n,b):
 with (P/n).open('xb') as f:f.write(b)
def save(n,x):put(n,(json.dumps(x,ensure_ascii=False,indent=2)+'\n').encode())
def git(n,args,data=None):
 argv=[G,*args];t=time.time();r=subprocess.run(argv,cwd=R,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
 put(n+'.stdout.raw',r.stdout);put(n+'.stderr.raw',r.stderr)
 if data is not None:put(n+'.stdin.raw',data)
 save(n+'.invocation.json',{'argv':argv,'cwd':str(R),'actual_native_exit':r.returncode,'started':t,'ended':time.time(),'read_only':True})
 if r.returncode:raise RuntimeError('Read-only Git first failure')
 return r.stdout
c=json.loads((P/'public-source-catalog.json').read_bytes());rows=[]
for part in git('git-control-tree',['ls-tree','-r','-z',C,'--','apps/control']).split(b'\0'):
 if not part:continue
 h,p=part.split(b'\t',1);m,k,o=h.decode().split();p=p.decode('utf-8')
 if p.endswith('.go'):
  if m!='100644' or k!='blob':raise RuntimeError('Nonregular public control source')
  rows.append({'path':p,'mode':m,'type':k,'git_blob':o})
raw=git('git-control-blobs',['cat-file','--batch'],''.join(x['git_blob']+'\n' for x in rows).encode());pos=0
for x in rows:
 e=raw.index(b'\n',pos);o,k,n=raw[pos:e].decode().split();n=int(n);b=raw[e+1:e+1+n];pos=e+2+n
 if o!=x['git_blob'] or k!='blob' or raw[pos-1:pos]!=b'\n':raise RuntimeError('Bad Git batch')
 x.update(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
 if b'//go:embed' in b:raise RuntimeError('Additional embed requires explicit catalog revision')
c['files']=sorted(c['files']+rows,key=lambda x:x['path']);c['file_count']=len(c['files']);c['supplement_reason']='Explicit public apps/control package source referenced by source text; no generator executed.'
allraw=(P/'git-public-blobs.stdout.raw').read_bytes()+raw
dirs={str(pathlib.PurePosixPath(x['path']).parent) for x in c['files'] if x['path'].endswith('.go')}
imports=sorted({x.decode() for x in re.findall(rb'\x22researchos.local/research-os/([^\x22]+)\x22',allraw)})
missing=[x for x in imports if x not in dirs]
embeds=[];names={x['path'] for x in c['files']}
for x in c['embed_directives']:
 target=str(pathlib.PurePosixPath(x['path']).parent/x['directive'].split(' ',1)[1])
 embeds.append({**x,'resolved_catalog_path':target,'present':target in names})
if missing or not all(x['present'] for x in embeds):raise RuntimeError('Public lexical import/embed coverage gap')
c['lexical_import_audit']={'local_imports':imports,'missing_directories':missing,'not_a_Go_compilation_claim':True};c['embed_directives']=embeds
save('public-source-catalog.v2.json',c)
print(json.dumps({'files':len(c['files']),'added':len(rows),'missing_local_package_dirs':missing,'embed_count':len(embeds),'actual_Go_calls':0}))
