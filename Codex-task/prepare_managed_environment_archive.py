import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;source=HERE/'product-v1-managed-environment-author'
manifest=source/'EVIDENCE_MANIFEST.json';assert hashlib.sha256(manifest.read_bytes()).hexdigest()=='5c4671b9fced75938e8c4115bfbf664d69377fb5bcf2914901f6b6820b721a64'
entries=json.loads(manifest.read_bytes())['files'];entries.append(dict(path=manifest.name,sha256=hashlib.sha256(manifest.read_bytes()).hexdigest()))
dest=source/'ARCHIVE_FILES.json';assert not dest.exists();dest.write_bytes((json.dumps(dict(root=str(source),files=entries),ensure_ascii=False,indent=2)+'\n').encode('utf8'))
print(hashlib.sha256(dest.read_bytes()).hexdigest())
