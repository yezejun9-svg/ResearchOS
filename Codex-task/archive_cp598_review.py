import hashlib
import json
from pathlib import Path

source = Path(__file__).resolve().parent / 'cp597-continuation/w14-native-create-clients-independent-review-01'
target = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp597-20261104/clients/reviews/freeze-01')
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
assert sha(source / 'source-review.json') == '8215291ba3e98de8774132c042a4bc4228945fdf61a3fa516e9c554af31fc102'
assert not target.exists(), 'Check any uncertain previous archive before retrying'
files = [p for p in source.iterdir() if p.is_file()]
files += [p for p in (source / 'isolated-frozen-node').rglob('*') if p.is_file()]
assert sum(p.stat().st_size for p in files) < 8 * 1024 * 1024
assert all(not p.is_symlink() and not p.is_junction() for p in files)
target.mkdir()
manifest = []
for path in files:
    rel = path.relative_to(source)
    dest = target / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(path.read_bytes())
    assert sha(dest) == sha(path)
    manifest.append({'path': str(rel), 'sha256': sha(dest), 'bytes': dest.stat().st_size})
(target / 'ROOT_ARCHIVE.json').write_text(json.dumps({
    'status': 'FROZEN_V1_REQUIRES_CHANGES_PRESERVED', 'source_root': str(source),
    'excluded': ['gocache', 'tmp'], 'formal_increment': 0, 'entries': manifest,
}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'files': len(files), 'bytes': sum(p.stat().st_size for p in files),
                  'review_sha256': sha(target / 'source-review.json'), 'formal_increment': 0}))
