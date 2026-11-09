import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
dirs=['product-v1-native-qualification-producer-author-20261105','product-v1-native-qualification-producer-author-20261105-rev2','product-v1-native-qualification-b3-security-review-rev2-20261105','product-v1-native-qualification-wrapper-rev2-review-20261105'];files=[p for d in dirs for p in (HERE/d).rglob('*') if p.is_file()]
files += [HERE/'register_product_v1_go_check.py',HERE/'register_product_v1_go_check_v2.py',HERE/'derive_go_check_v2.py'];assert len(files)<120
p=HERE/'product-v1-qualification-blocked-root-selection.json';assert not p.exists();p.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=f.relative_to(HERE).as_posix(),sha256=sha(f)) for f in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(p),sha256=sha(p),files=len(files))))
