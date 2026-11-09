import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

out = Path(__file__).resolve().parent
if sys.flags.optimize != 0 or len(sys.argv) != 3:
    raise RuntimeError('Expected unoptimized Root execution with exact independent review path and SHA')
argv = [sys.executable, '-I', str(out / 'register.py'), '--review', sys.argv[1], '--review-sha', sys.argv[2]]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out / 'stdout.raw').open('xb') as stdout, (out / 'stderr.raw').open('xb') as stderr:
    child = subprocess.run(argv, cwd=Path.cwd(), stdout=stdout, stderr=stderr)
record = {'argv': argv, 'cwd': str(Path.cwd()), 'started_at': started,
    'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_exit': child.returncode,
    'stdout_sha256': hashlib.sha256((out / 'stdout.raw').read_bytes()).hexdigest(),
    'stderr_sha256': hashlib.sha256((out / 'stderr.raw').read_bytes()).hexdigest()}
with (out / 'invocation.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'actual_exit': child.returncode, 'stdout': (out / 'stdout.raw').read_text(encoding='utf-8'),
    'stderr': (out / 'stderr.raw').read_text(encoding='utf-8', errors='replace')[-3000:]}, ensure_ascii=True))
sys.exit(child.returncode)
