from pathlib import Path
import json,subprocess,hashlib,tarfile,io,datetime
R=Path.cwd();N=Path(__file__).resolve().parent;W=R/'.local/independent-handler38-a639cfcf';a=json.loads((N/'resource_amendment.byte-exact.json').read_bytes());git=json.loads((R/'execution/toolchains/locked.json').read_bytes())['tools']['git']['path'];commit=a['candidate']
def save(n,o):(N/n).write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def run(label,args):
 start=datetime.datetime.now(datetime.timezone.utc).isoformat();q=subprocess.run([git,*args],cwd=R,capture_output=True);(N/(label+'.stdout.raw')).write_bytes(q.stdout);(N/(label+'.stderr.raw')).write_bytes(q.stderr);save(label+'.invocation.json',{'argv':[git,*args],'cwd':str(R),'started_at':start,'exit':q.returncode});assert q.returncode==0;return q.stdout
assert W.is_dir() and (W/'.git').is_file();assert [p.relative_to(W).as_posix() for p in W.rglob('*') if p.is_file()]==['.git']
tracked=run('candidate-inventory',['ls-tree','-rz',commit]);entries={}
for row in tracked.split(b'\0'):
 if row:
  meta,path=row.split(b'\t',1);entries[path.decode('utf8')]=meta.decode().split()[2]
pathspecs=a['preparation_correction']['next_pathspecs'];assert len(pathspecs)==15
for p in pathspecs:assert any(x==p or x.startswith(p+'/') for x in entries)
archive=run('public-source-archive',['archive','--format=tar',commit,*pathspecs]);rows=[]
with tarfile.open(fileobj=io.BytesIO(archive),mode='r:') as t:
 for item in t:
  if item.isdir():continue
  assert item.isfile(),'no link export'
  p=(W/item.name).resolve();assert p.is_relative_to(W.resolve()) and not p.exists();raw=t.extractfile(item).read();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);rows.append({'path':item.name,'git_blob':entries[item.name],'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
for i,row in enumerate(a['exact_additional_public_compile_files']):
 assert entries[row['path']]==row['git_blob'];raw=run('public-compile-'+str(i),['cat-file','blob',row['git_blob']]);assert hashlib.sha256(raw).hexdigest()==row['sha256'] and len(raw)==row['bytes'];p=W/row['path'];assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);rows.append({k:row[k] for k in ['path','git_blob','sha256','bytes']})
save('export_manifest.json',{'candidate':commit,'files':rows,'compile_only_additions':12,'archive_pathspecs':pathspecs,'private_data':0,'original_failures_preserved':True});print(json.dumps({'checkout':str(W),'exported_files':len(rows),'total_bytes':sum(x['bytes'] for x in rows),'exit':0},ensure_ascii=True))
