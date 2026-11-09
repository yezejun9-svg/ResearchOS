"""Remove only task-created credentials/data and obsolete build assets."""
import hashlib
import json
from pathlib import Path
import re
import shutil

REPO = Path(r'D:\作品集\ResearchOS\research-os\.local\worktrees\react-workbench-redesign-20261025')
TMP = Path(r'D:\作品集\ResearchOS\research-os\.local\react-workbench-redesign-20261025-tmp')
OUT = Path(__file__).parent
dist = (REPO / 'apps/web/dist').resolve()
assets = (dist / 'assets').resolve()
assert assets.is_relative_to(dist) and assets.is_dir()
assert TMP.resolve().is_relative_to(Path(r'D:\作品集\ResearchOS\research-os\.local').resolve())

index = (dist / 'index.html').read_text(encoding='utf-8')
keep = set(re.findall(r'/assets/(index-[A-Za-z0-9_-]+\.(?:css|js))', index))
if len(keep) != 2 or not all((assets / name).is_file() for name in keep):
    raise RuntimeError(f'unexpected active asset references: {keep}')
removed = []
for file in assets.iterdir():
    if file.name in keep:
        continue
    if not file.is_file() or not re.fullmatch(r'index-[A-Za-z0-9_-]+\.(?:css|js)', file.name) or not file.resolve().is_relative_to(assets):
        raise RuntimeError(f'unexpected asset: {file}')
    file.unlink()
    removed.append(str(file))
for run in ('01', '02', '03'):
    data = (TMP / f'real-isolated-{run}-data').resolve()
    credentials = (TMP / f'real-isolated-{run}-owner.json').resolve()
    if not data.is_relative_to(TMP.resolve()) or not credentials.is_relative_to(TMP.resolve()):
        raise RuntimeError('cleanup path escaped task temp')
    if data.exists():
        shutil.rmtree(data)
        removed.append(str(data))
    if credentials.exists():
        credentials.unlink()
        removed.append(str(credentials))
active = {str(file.relative_to(dist)).replace('\\', '/'): hashlib.sha256(file.read_bytes()).hexdigest()
          for file in sorted(dist.rglob('*')) if file.is_file()}
report = {'schema': 'researchos.source13-task-owned-cleanup.v1', 'removed': removed,
          'active_dist_sha256': active, 'preview_source_remains': str(dist), 'credentials_removed': True}
(OUT / 'CLEANUP.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'removed_count': len(removed), 'active_assets': sorted(keep)}, ensure_ascii=False))
