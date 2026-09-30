from pathlib import Path
import hashlib,json,subprocess
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[3]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
data=[]
for label in ['a','b']:
 base=OUT/('fixture-probe/data-'+label)
 for path in sorted(base.rglob('*')):
  if path.is_file():data.append({'path':path.relative_to(OUT).as_posix(),'sha256':sha(path),'bytes':path.stat().st_size})
 assert (base/'researchos.sqlite').is_file()
put(OUT/'fixture-probe/preserved-data-before-cleanup.json',{'note':'Stop preserved both disposable data directories; removed after hashing as no longer needed test working data.','files':data})
args=['powershell.exe','-NoProfile','-File',str(OUT/'cleanup_owned.ps1')]
with (OUT/'cleanup.stdout.log').open('wb') as stdout,(OUT/'cleanup.stderr.log').open('wb') as stderr:r=subprocess.run(args,stdout=stdout,stderr=stderr,timeout=60)
put(OUT/'cleanup-command.json',{'argv':args,'exit_code':r.returncode});assert r.returncode==0
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file() and p.name!='index.json' and not p.relative_to(OUT).parts[0].startswith('fix-')]
put(OUT/'index.json',{'source_revision':'14bf6d633ca58b4e2bf8b911719ac93e23f53239','verdict':'NEEDS_FIX_R1_SOURCE_AND_PROCESS_IDENTITY','files':files})
for row in files:assert sha(OUT/row['path'])==row['sha256']
print(json.dumps({'review_sha256':sha(OUT/'review.json'),'index_sha256':sha(OUT/'index.json'),'files':len(files),'cleanup_exit':r.returncode}))
