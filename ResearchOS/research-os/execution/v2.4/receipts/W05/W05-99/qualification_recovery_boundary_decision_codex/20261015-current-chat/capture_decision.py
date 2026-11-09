import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.stdin.reconfigure(encoding='utf8')
sys.stdout.reconfigure(encoding='utf8')
request = json.load(sys.stdin)
base = Path(__file__).resolve().parent
label = request['label']
if not label or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label):
    raise SystemExit('invalid label')
env = {k: os.environ[k] for k in ('SystemRoot', 'WINDIR', 'TEMP', 'TMP', 'PATH', 'PATHEXT', 'COMSPEC') if k in os.environ}
env.update({'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'})
argv = [sys.executable, '-X', 'utf8', '-c', request['script']]
recipe = {'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'cwd': str(Path.cwd()), 'argv': argv, 'environment_exact': env, 'mode': 'READONLY_RECOVERY_BOUNDARY_DECISION'}
(base / (label + '.recipe.json')).open('x', encoding='utf8').write(json.dumps(recipe, ensure_ascii=False, indent=2) + '\n')
r = subprocess.run(argv, env=env, capture_output=True)
refs = []
for suffix, data in (('stdout.raw', r.stdout), ('stderr.raw', r.stderr)):
    p = base / (label + '.' + suffix)
    p.open('xb').write(data)
    refs.append({'path': p.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
(base / (label + '.result.json')).open('x', encoding='utf8').write(json.dumps({'native_exit': r.returncode, 'raw': refs}, indent=2) + '\n')
print(r.stdout.decode('utf8', errors='backslashreplace'))
if r.stderr:
    print(r.stderr.decode('utf8', errors='backslashreplace'))
print('native_exit=' + str(r.returncode))
sys.exit(r.returncode)
