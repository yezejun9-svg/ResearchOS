from pathlib import Path
import subprocess, hashlib, json
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
REV='2f30646a57c0c18a022c2080ec3aeb2e9d9d559e'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def sha(b):return hashlib.sha256(b).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
paths=['ops/experiment_sandbox/'+n for n in ['async_windows.go','async_windows_test.go','sandbox_windows.go']]
replace={};rows=[]
for name in paths:
 raw=git('show',REV+':'+name);dest=OUT/'source'/Path(name).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw)
 replace[str(ROOT/name)]=str(dest);rows.append({'path':name,'git_revision':REV,'sha256':sha(raw),'overlay':str(dest)})
others=[]
for name in git('ls-tree','-r','--name-only',REV,'ops/experiment_sandbox').decode().splitlines():
 if name in paths:continue
 raw=git('show',REV+':'+name);current=(ROOT/name).read_bytes();assert raw.replace(b'\r\n',b'\n')==current.replace(b'\r\n',b'\n');others.append({'path':name,'git_sha256':sha(raw),'working_sha256':sha(current)})
author=[]
for name in git('ls-tree','-r','--name-only','2b8d6e0','execution/receipts/W06/runtime-s2').decode().splitlines():
 raw=git('show','2b8d6e0:'+name);dest=OUT/'author-evidence'/Path(name).parent.name/Path(name).name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);author.append({'path':name,'sha256':sha(raw),'copy':str(dest)})
put(OUT/'source-audit.json',{'source_revision':REV,'main_head':git('rev-parse','HEAD').decode().strip(),'changed_paths':rows,'unchanged_package_paths':others,'author_evidence':author,'git_status_before':git('status','--short').decode()})
replace[str(ROOT/'ops/experiment_sandbox/independent_s2_test.go')]=str(OUT/'independent_s2_test.go')
put(OUT/'overlay.json',{'Replace':replace})
print(json.dumps({'source_files':len(rows),'unchanged_package_files':len(others),'author_evidence_files':len(author)}))
