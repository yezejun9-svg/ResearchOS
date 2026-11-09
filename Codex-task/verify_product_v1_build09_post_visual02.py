import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=Path('D:/作品集/ResearchOS/research-os');bundle=ROOT/'.local/worktrees/product-v1-build-09-20261105/.local/desktop-v1-build-09'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
mf=bundle/'development-manifest.json';assert sha(mf)=='27659d100d38f8af8fca841f176feaf471fdc9d674fbd202ee9f4b12cad7d329';m=json.loads(mf.read_bytes());listed={r['path'] for r in m['files']};bad=[r['path'] for r in m['files'] if sha(bundle/r['path'])!=r['sha256']];extra=sorted({p.relative_to(bundle).as_posix() for p in bundle.rglob('*') if p.is_file()}-listed-{'development-manifest.json'});out=HERE/'product-v1-build09-post-visual02-root-readback.json';assert not out.exists();out.write_bytes((json.dumps(dict(manifest_sha256=sha(mf),listed_files=len(listed),mismatches=bad,unlisted_paths=extra),indent=2)+'\n').encode());assert not bad and not extra;print(json.dumps(dict(path=str(out),sha256=sha(out))))
