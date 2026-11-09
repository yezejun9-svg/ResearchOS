"""Remove only the explicit task-owned temporary root after proof retention."""
import json
from pathlib import Path
import shutil

tmp = Path(r'D:\作品集\ResearchOS\research-os\.local\react-workbench-redesign-20261025-tmp')
allowed_parent = Path(r'D:\作品集\ResearchOS\research-os\.local').resolve()
target = tmp.resolve()
if target.parent != allowed_parent or target.name != 'react-workbench-redesign-20261025-tmp':
    raise RuntimeError('resolved cleanup target is outside the explicit task-owned root')
if not target.is_dir():
    raise RuntimeError('task-owned temp root is missing')
shutil.rmtree(target)
out = Path(__file__).parent / 'TEMP-CLEANUP.json'
out.write_text(json.dumps({'schema': 'researchos.source14-temp-cleanup.v1', 'removed_root': str(target),
                           'contained_only_task_own_temp': True, 'preview_dist_and_receipts_retained': True}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'removed_root': str(target)}, ensure_ascii=False))
