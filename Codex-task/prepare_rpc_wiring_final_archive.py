import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;D=HERE/'product-v1-native-rpc-wiring-final-20261105'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(D/'MANIFEST.json')=='6e4219f609d2690043401b4ac55bf00af9fd1e6e03c0b7269655e12d465cd1fd'
files=[p for p in D.rglob('*') if p.is_file()];assert len(files)<150
for p in files:assert p.suffix.lower() not in ('.exe','.dll','.db','.sqlite') and not p.is_symlink()
sel=HERE/'product-v1-rpc-wiring-final-root-selection.json';assert not sel.exists();sel.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=p.relative_to(HERE).as_posix(),sha256=sha(p)) for p in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(sel),sha256=sha(sel),files=len(files))))
