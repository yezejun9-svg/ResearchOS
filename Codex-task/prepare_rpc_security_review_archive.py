import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
review=HERE/'product-v1-native-rpc-b1-security-review-rev3-20261105';correction=HERE/'product-v1-native-rpc-b2-test01-correction-review-20261105';src=HERE/'product-v1-native-rpc-runtime-author-20261105/rev3-test02-ready';assert sha(review/'REVIEW.json')=='49892fd268e3e7e424ce4287379befef09fd25cf1a3e173441bd178ab1b6a20a';assert sha(correction/'correction-report.json')=='09c74de499af091ce77b1b11cffa19985aef315a519afd247772d23479144781'
files=[review/n for n in ('REVIEW.json','REVIEW.md','ARCHIVE-SELECTION.json')]+list(src.glob('*.go'))+[p for p in correction.rglob('*') if p.is_file()]+[HERE/'product-v1-native-rpc-wiring-rev2-review-20261105/review-report.json',HERE/'product-v1-native-rpc-wiring-rev3-review-20261105/review-report.json']
p=HERE/'product-v1-rpc-interim-reviews-root-selection.json';assert not p.exists();p.write_bytes((json.dumps(dict(root=str(HERE),files=[dict(path=f.relative_to(HERE).as_posix(),sha256=sha(f)) for f in files]),indent=2)+'\n').encode('utf8'));print(json.dumps(dict(selection=str(p),sha256=sha(p),files=len(files))))
