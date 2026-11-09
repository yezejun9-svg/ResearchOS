import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;D=HERE/'product-v1-native-rpc-final-combined-audit-20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'REVIEW.json')=='9ce81df395a42fec202d9f53ec3c8a40f3a5588156c646e10f0c08500f2abb45'
r=json.loads((D/'ARCHIVE-SELECTION.json').read_bytes());files={D/n for n in ('REVIEW.json','REVIEW.md','ARCHIVE-SELECTION.json')}
for row in r['evidence']+r['review_files']+list(r['candidate_manifests'].values()):
 p=Path(row['path']);p=p if p.is_absolute() else HERE/p;assert p.resolve().is_relative_to(HERE) and sha(p)==row['sha256'];files.add(p)
p=HERE/'product-v1-rpc-combined-audit-root-selection.json';assert not p.exists();p.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=f.relative_to(HERE).as_posix(),sha256=sha(f)) for f in sorted(files)]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(p),sha256=sha(p),files=len(files))))
