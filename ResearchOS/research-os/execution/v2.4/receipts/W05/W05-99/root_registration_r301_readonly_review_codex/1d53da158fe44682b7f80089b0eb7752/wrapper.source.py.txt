import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
runner = OUT / 'register.py'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == 'f179bed41e2988a990e7c531a1300e79ec937f4b309b080f204b9f77a893fe94'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
argv = [sys.executable, '-I', str(runner)]
env = {key: value for key, value in os.environ.items() if key.upper() not in {'PYTHONOPTIMIZE', 'PYTHONPATH'}}
with (OUT / 'stdout.raw').open('xb') as stdout, (OUT / 'stderr.raw').open('xb') as stderr:
    child = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
record = {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'started_at': started,
    'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_exit': child.returncode,
    'runner_sha256': hashlib.sha256(runner.read_bytes()).hexdigest(),
    'stdout_sha256': hashlib.sha256((OUT / 'stdout.raw').read_bytes()).hexdigest(),
    'stderr_sha256': hashlib.sha256((OUT / 'stderr.raw').read_bytes()).hexdigest(),
    'automatic_retry': False, 'counter_reset': False}
with (OUT / 'invocation.json').open('xb') as stream:
    stream.write((json.dumps(record, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8'))
print(json.dumps({'actual_exit': child.returncode, 'invocation': str(OUT / 'invocation.json'),
    'stderr_tail_display_only': (OUT / 'stderr.raw').read_bytes().decode('utf-8', errors='replace')[-1800:],
    'stdout_display': (OUT / 'stdout.raw').read_bytes().decode('utf-8', errors='replace')}, ensure_ascii=True))
sys.exit(child.returncode)
