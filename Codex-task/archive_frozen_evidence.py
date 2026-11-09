import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--source', required=True)
p.add_argument('--target', required=True)
p.add_argument('--anchor', required=True)
p.add_argument('--anchor-sha', required=True)
p.add_argument('--include-dir', action='append', default=[])
a = p.parse_args()
source = Path(a.source).resolve()
target = Path(a.target).resolve()
allowed = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts').resolve()
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
assert target.is_relative_to(allowed)
assert sha(source / a.anchor) == a.anchor_sha
assert not target.exists(), 'Inspect uncertain prior archive before retrying'
files = [f for f in source.iterdir() if f.is_file()]
for rel in a.include_dir:
    tree = (source / rel).resolve()
    assert tree.is_relative_to(source) and tree.is_dir()
    for f in tree.rglob('*'):
        assert not f.is_symlink() and not f.is_junction(), str(f)
        if f.is_file(): files.append(f)
files = sorted(set(files))
assert sum(f.stat().st_size for f in files) < 16 * 1024 * 1024
assert all(not f.is_symlink() and not f.is_junction() for f in files)
target.mkdir()
entries = []
for f in files:
    rel = f.relative_to(source)
    dest = target / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(f.read_bytes())
    assert sha(dest) == sha(f)
    entries.append(dict(path=rel.as_posix(), sha256=sha(dest), bytes=dest.stat().st_size))
manifest = dict(source_root=str(source), anchor=a.anchor, anchor_sha256=a.anchor_sha,
                formal_increment=0, entries=entries)
(target / 'ROOT_ARCHIVE.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(dict(files=len(entries), bytes=sum(x['bytes'] for x in entries), anchor_sha256=sha(target / a.anchor))))
