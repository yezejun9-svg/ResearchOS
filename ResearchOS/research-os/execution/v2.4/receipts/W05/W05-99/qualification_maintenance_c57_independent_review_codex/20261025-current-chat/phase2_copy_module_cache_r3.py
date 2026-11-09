import pathlib,json,re,shutil,hashlib
B=pathlib.Path(__file__).parent
v=json.loads((B/'PHASE2-exact-snapshot-verification.json').read_text(encoding='utf-8'));S=pathlib.Path(v['snapshot']);C=S.parent
origin=pathlib.Path(r'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod');dest=C/'gomodcache'
mods=re.findall(r'^\s*([a-z][^\s]+)\s+(v[^\s]+)',(S/'go.mod').read_text(),re.M)
records=[]
for mod,version in mods:
 src=origin/(mod+'@'+version);out=dest/(mod+'@'+version)
 assert src.is_dir(),str(src)
 h=hashlib.sha256();count=size=copied=0
 for path in sorted(src.rglob('*')):
  relative=path.relative_to(src);target=out/relative
  if path.is_dir():target.mkdir(parents=True,exist_ok=True);continue
  assert path.is_file(),str(path)
  data=path.read_bytes();digest=hashlib.sha256(data).digest()
  if target.exists():assert hashlib.sha256(target.read_bytes()).digest()==digest,'owned cached content differs: '+str(relative)
  else:
   target.parent.mkdir(parents=True,exist_ok=True)
   with target.open('xb') as f:f.write(data)
   copied+=1
  h.update(str(relative).replace('\\','/').encode()+b'\0'+digest);count+=1;size+=len(data)
 meta=origin/'cache/download'/mod/'@v';target=dest/'cache/download'/mod/'@v';target.mkdir(parents=True,exist_ok=True)
 for path in meta.glob(version+'.*'):
  if path.is_file() and path.suffix not in ['.lock','.zip']:
   output=target/path.name
   if not output.exists():shutil.copyfile(path,output)
 records.append({'module':mod,'version':version,'files':count,'bytes':size,'copied':copied,'framed_tree_sha256':h.hexdigest()})
print(json.dumps(records,indent=2))
with (B/'PHASE2-owned-module-cache-copy.json').open('x',encoding='utf-8') as f:json.dump({'source':str(origin),'target':str(dest),'modules':records},f,indent=2)
jobs=B/'PHASE2-jobs'
for old,new in [('089-phase2-core-c','095-phase2-core-c-owned-cache'),('090-phase2-domain-c','096-phase2-domain-c-owned-cache'),('091-phase2-boot-c','097-phase2-boot-c-owned-cache'),('092-phase2-boot-d','098-phase2-boot-d-owned-cache')]:
 job=json.loads((jobs/(old+'.json')).read_text(encoding='utf-8'));job['tag']=new;job['env']['GOPROXY']='off'
 (jobs/(new+'.json')).write_text(json.dumps(job,ensure_ascii=False,indent=2),encoding='utf-8')
