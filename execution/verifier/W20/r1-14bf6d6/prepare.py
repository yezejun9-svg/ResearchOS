from pathlib import Path,PurePosixPath
import subprocess,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent
SOURCE='14bf6d633ca58b4e2bf8b911719ac93e23f53239';EVIDENCE='f11cf5c0d8abc82d513bde752e76df8d0e16bc46'
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def digest(raw):return hashlib.sha256(raw).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf-8')
sources=[]
for name in git('diff-tree','--no-commit-id','--name-only','-r',SOURCE).decode().splitlines():
 raw=git('show',SOURCE+':'+name);dest=OUT/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);sources.append({'path':name,'sha256':digest(raw)})
evidence=[]
for name in git('ls-tree','-r','--name-only',EVIDENCE,'execution/receipts/W20/release-package/r1').decode().splitlines():
 raw=git('show',EVIDENCE+':'+name);dest=OUT/'author-evidence'/Path(name).name;dest.parent.mkdir(exist_ok=True);dest.write_bytes(raw);evidence.append({'path':name,'sha256':digest(raw),'bytes':len(raw)})
summary=json.loads((OUT/'author-evidence/summary.json').read_text(encoding='utf-8-sig'))
for name,wanted in summary['raw'].items():assert digest((OUT/'author-evidence'/name).read_bytes())==wanted
archive=OUT/'author-evidence/researchos-r1-windows-amd64.zip';assert digest(archive.read_bytes())==summary['archive_sha256']
rows=[];git_paths=set(git('ls-tree','-r','--name-only',SOURCE).decode().splitlines())
with zipfile.ZipFile(archive) as z:
 names=z.namelist();assert names==sorted(set(names));manifest=json.loads(z.read('release-manifest.json'));assert digest(z.read('release-manifest.json'))==summary['manifest_sha256'];assert manifest['source_commit']==SOURCE
 listed={r['path']:r for r in manifest['files']};assert set(names)==set(listed)|{'release-manifest.json'}
 assert all(not PurePosixPath(n).is_absolute() and '..' not in PurePosixPath(n).parts for n in names)
 for name,row in listed.items():
  raw=z.read(name);assert len(raw)==row['size'] and digest(raw)==row['sha256'];source_name=name
  if name.startswith('scripts/'):source_name='ops/release/'+name.removeprefix('scripts/')
  match=None
  if source_name in git_paths:
   blob=git('show',SOURCE+':'+source_name);assert raw.replace(b'\r\n',b'\n')==blob.replace(b'\r\n',b'\n'),name;match=True
  rows.append({'path':name,'sha256':row['sha256'],'source_git_path':source_name if match else None,'git_blob_LF_matches':match})
 put(OUT/'release-manifest.json',manifest)
 # An immutable release copy for independent owned fixture execution.
 release=OUT/'fixture-release';release.mkdir(exist_ok=True);z.extractall(release)
put(OUT/'source-audit.json',{'source_revision':SOURCE,'evidence_revision':EVIDENCE,'source_files':sources,'author_evidence_files':evidence,'zip_sha256':summary['archive_sha256'],'manifest_sha256':summary['manifest_sha256'],'manifest_files':len(rows),'source_git_matches':sum(bool(r['git_blob_LF_matches']) for r in rows),'files':rows,'main_head':git('rev-parse','HEAD').decode().strip(),'status_before':git('status','--short').decode()})
print(json.dumps({'manifest_files':len(rows),'source_git_matches':sum(bool(r['git_blob_LF_matches']) for r in rows),'archive_sha256':summary['archive_sha256']}))
