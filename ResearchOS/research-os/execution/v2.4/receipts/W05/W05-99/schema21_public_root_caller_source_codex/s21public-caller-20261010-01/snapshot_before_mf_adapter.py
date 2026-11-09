import hashlib, json
from pathlib import Path
N=Path(__file__).resolve().parent
p=N/'public21_root.source.py';raw=p.read_bytes()
guard=json.loads((N/'source-controls.guard.closed.json').read_bytes())
original=next(x for x in guard['held_refs'] if Path(x['path'])==p)
try:
    assert len(raw)==original['bytes'] and hashlib.sha256(raw).hexdigest()==original['sha256']
    with (N/'public21_root.before-mf-adapter.source.txt').open('xb') as f:f.write(raw)
except BaseException:
    print('ROOT_PYTHON_EXIT=1',flush=True);raise
else:print('ROOT_PYTHON_EXIT=0',flush=True)
