import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;D=HERE/'product-v1-native-rpc-runtime-author-20261105/test03-passed';CONTROL=HERE/'product-v1-owned-verification-20261104'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in D.rglob('*') if p.is_file()]+[CONTROL/'scopes/product-v1-native-rpc-b1-tests-03.json'];assert len(files)<25
assert sha(CONTROL/'scopes/product-v1-native-rpc-b1-tests-03.json')=='e50b37b15a620ff7464fc4fa92f6837a667f880d126e930e3d3c743d9598179a'
p=HERE/'product-v1-rpc-b1-test03-root-selection.json';assert not p.exists();p.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=f.relative_to(HERE).as_posix(),sha256=sha(f)) for f in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(p),sha256=sha(p),files=len(files))))
