import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path.cwd().resolve()
OUT = Path(__file__).resolve().parent
SCOPE = ROOT / 'execution/v2.4/receipts/W05/W05-99/integration_codex/independent-cli-list-scopes-r308/list_independent_scope.json'
RUNNER = SCOPE.parent / 'list_replay.py'
assert sys.flags.optimize == 0
assert hashlib.sha256(SCOPE.read_bytes()).hexdigest() == '5fbd2bee9fc3e08456bc643dc42747ebd4441d9d1f0ca7fc150dc18ac49cd48f'
assert hashlib.sha256(RUNNER.read_bytes()).hexdigest() == '764a62d357527f8503840ece15409a7a83d1c85d293680db35d6322cf2c61b5c'
lock = json.loads((ROOT / 'execution/toolchains/locked.json').read_bytes())['tools']
assert Path(sys.executable).resolve() == Path(lock['python']['path']).resolve()
assert hashlib.sha256(Path(sys.executable).read_bytes()).hexdigest() == lock['python']['sha256']
argv = [sys.executable, '-X', 'utf8', '-I', str(RUNNER), str(SCOPE), '5fbd2bee9fc3e08456bc643dc42747ebd4441d9d1f0ca7fc150dc18ac49cd48f']
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
env = {key: value for key, value in os.environ.items() if key.upper() not in {'PYTHONOPTIMIZE', 'PYTHONPATH'}}
with (OUT / 'stdout.raw').open('xb') as stdout, (OUT / 'stderr.raw').open('xb') as stderr:
    child = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=stdout, stderr=stderr)
    with (OUT / 'started.json').open('xb') as stream:
        stream.write((json.dumps({'argv': argv, 'cwd': str(ROOT), 'owned_runner_pid': child.pid, 'started_at': started,
            'scope_sha256': hashlib.sha256(SCOPE.read_bytes()).hexdigest(), 'runner_sha256': hashlib.sha256(RUNNER.read_bytes()).hexdigest(),
            'Source_acceptance': False, 'paid_calls': 0}, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
    code = child.wait()
record = {'actor': 'codex:/root', 'argv': argv, 'cwd': str(ROOT), 'owned_runner_pid': child.pid,
    'actual_exit': code, 'started_at': started, 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'stdout_sha256': hashlib.sha256((OUT / 'stdout.raw').read_bytes()).hexdigest(),
    'stderr_sha256': hashlib.sha256((OUT / 'stderr.raw').read_bytes()).hexdigest(), 'automatic_retry': False,
    'counter_reset': False, 'source_acceptance': False, 'formal_increment': 0}
with (OUT / 'invocation.json').open('xb') as stream:
    stream.write((json.dumps(record, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))
print(json.dumps({'actual_exit': code, 'stdout_display': (OUT / 'stdout.raw').read_text(encoding='utf-8'),
    'stderr_tail_display_only': (OUT / 'stderr.raw').read_text(encoding='utf-8')[-3500:]}, ensure_ascii=True))
sys.exit(code)
