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
runner = OUT / 'adjudicate.py'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == '0a3a440d3c82f75d3495e7b6e72b0e21d5ac76a9aab1d7281e15927774d59347'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
argv = [sys.executable, '-I', str(runner)]
env = {key: value for key, value in os.environ.items() if key.upper() not in {'PYTHONOPTIMIZE', 'PYTHONPATH'}}
with (OUT / 'outer.stdout.raw').open('xb') as stdout, (OUT / 'outer.stderr.raw').open('xb') as stderr:
    child = subprocess.run(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
raw = (json.dumps({'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'started_at': started,
    'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_exit': child.returncode,
    'runner_sha256': hashlib.sha256(runner.read_bytes()).hexdigest(),
    'stdout_sha256': hashlib.sha256((OUT / 'outer.stdout.raw').read_bytes()).hexdigest(),
    'stderr_sha256': hashlib.sha256((OUT / 'outer.stderr.raw').read_bytes()).hexdigest(),
    'original_G1_failure_preserved': True, 'new_product_test_execution': 0, 'automatic_retry': False},
    ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')
with (OUT / 'outer.invocation.json').open('xb') as stream:
    stream.write(raw)
print(json.dumps({'actual_exit': child.returncode, 'invocation': str(OUT / 'outer.invocation.json'),
    'stderr_tail_display_only': (OUT / 'outer.stderr.raw').read_bytes().decode('utf-8', errors='replace')[-1800:]}, ensure_ascii=True))
sys.exit(child.returncode)
