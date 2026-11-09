import hashlib
import json
from pathlib import Path
import subprocess
import sys

p = Path(sys.argv[1])
v = json.loads(p.read_text(encoding='utf-8-sig'))
def ref(q):
    x = q.read_bytes()
    return {'path': str(q), 'sha256': hashlib.sha256(x).hexdigest(), 'bytes': len(x)}
for suffix in ['.stdout.raw', '.stderr.raw', '.result.json']:
    assert not p.with_name(p.stem + suffix).exists()
r = subprocess.run(v['argv'], cwd=v['cwd'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
out, err, result = [p.with_name(p.stem + suffix) for suffix in ['.stdout.raw', '.stderr.raw', '.result.json']]
out.write_bytes(r.stdout)
err.write_bytes(r.stderr)
result.write_text(json.dumps({'recipe': ref(p), 'native_exit': r.returncode, 'stdout': ref(out), 'stderr': ref(err)}, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
print(json.dumps({'native_exit': r.returncode, 'result': ref(result)}, ensure_ascii=False))
sys.stdout.flush()
sys.stdout.buffer.write(r.stdout)
sys.stderr.buffer.write(r.stderr)
raise SystemExit(r.returncode)
