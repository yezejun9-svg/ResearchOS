import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;D=HERE/'product-v1-native-rpc-runtime-author-20261105/final-rev6';R=HERE/'product-v1-native-rpc-b1-security-binding-rev6-20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'ARCHIVE.json')=='1c57e9129d6dd0201ae5ac2e5f7dbb1190272cae9f5f55a03ae2c40d08f59cce' and sha(R/'REVIEW.json')=='a05ee1625d175e5250c662b968fc7a02c3f334de892a9dbe6e227e9442361998'
dirs=[D,R,HERE/'product-v1-native-rpc-b1-security-review-rev4-20261105',HERE/'product-v1-native-rpc-b1-security-review-rev5-20261105'];files=[p for d in dirs for p in d.rglob('*') if p.is_file()];assert len(files)<100
p=HERE/'product-v1-rpc-runtime-final-root-selection.json';assert not p.exists();p.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=f.relative_to(HERE).as_posix(),sha256=sha(f)) for f in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(p),sha256=sha(p),files=len(files))))
