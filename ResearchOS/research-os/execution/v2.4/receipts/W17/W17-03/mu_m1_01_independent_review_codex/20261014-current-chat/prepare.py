import hashlib,json,pathlib,subprocess,tarfile,io,datetime
ROOT=pathlib.Path(__file__).parent
SRC=ROOT.parent/'mu-m1-wire-20261014'
SNAP=ROOT/'source'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(SRC),*a]).decode().strip()
def save(n,o):(ROOT/n).write_text(json.dumps(o,ensure_ascii=False,indent=2),encoding='utf8')
assert git('rev-parse','HEAD')=='c6f39e84fd0efa046a9651bb5542a4f3c6b4344b'
assert not git('status','--porcelain')
base='c465d1356480d6e6a90da84656724f9fc02b31c7'
m=json.loads((SRC/'.local/m1-01/manifest.json').read_text(encoding='utf-8-sig'))
assert sha(SRC/'.local/m1-01/manifest.json')=='23928d5d2beecff9ba4bca3c2b3a90754377cf6e1112da3713bf83b8ddcca67f'
for f in m['source8']:assert sha(SRC/f['path'])==f['sha256']
assert sorted(git('diff','--name-only',base,'HEAD').splitlines())==sorted(f['path'] for f in m['source8'])
for name,f in m['files'].items():
 p=SRC/'.local/m1-01'/name
 assert sha(p)==f['sha256'] and p.stat().st_size==f['bytes'],name
assert sha(SRC/'.local/m1-01/report.json')==m['report_sha256']
paths=['adapters','internal','ops','go.mod','go.sum','migrations','contracts','bootstrap','spec']
data=subprocess.check_output(['git','-C',str(SRC),'archive','HEAD',*paths])
SNAP.mkdir(exist_ok=False)
with tarfile.open(fileobj=io.BytesIO(data)) as archive:
 for member in archive.getmembers():
  assert member.isfile() or member.isdir(),member.name
  assert (SNAP/member.name).resolve().is_relative_to(SNAP.resolve())
 archive.extractall(SNAP,filter='data')
# Read-only Git metadata pointer lets the unchanged builder discover the canonical
# dependency/census root. No Git write command is run from this source snapshot.
(SNAP/'.git').write_bytes((SRC/'.git').read_bytes())
files=[]
for p in SNAP.rglob('*'):
 if p.is_file():files.append({'path':p.relative_to(SNAP).as_posix(),'sha256':sha(p),'bytes':p.stat().st_size})
for f in m['source8']:assert sha(SNAP/f['path'])==f['sha256']
save('source-before.json',{'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':git('rev-parse','HEAD'),'tree':git('rev-parse','HEAD^{tree}'),'base':base,'source8':m['source8'],'author_members_verified':len(m['files']),'snapshot_files':files,'archive_sha256':hashlib.sha256(data).hexdigest(),'snapshot_bytes':sum(f['bytes'] for f in files)})
print(json.dumps({'files':len(files),'bytes':sum(f['bytes'] for f in files),'author_members':len(m['files'])}))
