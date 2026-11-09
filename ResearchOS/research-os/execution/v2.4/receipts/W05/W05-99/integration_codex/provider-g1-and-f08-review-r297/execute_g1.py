import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path.cwd().resolve()
out = Path(__file__).resolve().parent
authorization = out / 'provider_g1_execution_scope.json'
authorization_sha = hashlib.sha256(authorization.read_bytes()).hexdigest()
assert authorization_sha == '19554590a73f93cf0105d6ce45ae2358a8e89ec0424b85d2d287dd937b9fbb3b'
cp_path = root / 'execution/v2.4/checkpoint.json'
cp = json.loads(cp_path.read_bytes())
assert cp['revision'] == 297 and len(cp['failure_counters']) == 302
runner = root / 'execution/v2.4/receipts/W05/W05-99/provider_whole9_g1_preparation_codex/093a934167674f6ca02e0a09dc5d5010/run_g1.py'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == 'e0ab68f17a54db81e2a0173430f52a4d3e1c73578f6b87b48563ce652be8ce23'
argv = [sys.executable, str(runner), '--execute', '--actor', 'codex:/root',
    '--authorization', str(authorization), '--authorization-sha', authorization_sha, '--counter-state', str(cp_path)]
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out / 'g1.outer.stdout.raw').open('xb') as stdout, (out / 'g1.outer.stderr.raw').open('xb') as stderr:
    child = subprocess.run(argv, cwd=root, stdout=stdout, stderr=stderr)
record = {'actor': 'codex:/root', 'argv': argv, 'cwd': str(root), 'started_at': started,
    'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'actual_exit': child.returncode,
    'stdout_sha256': hashlib.sha256((out / 'g1.outer.stdout.raw').read_bytes()).hexdigest(),
    'stderr_sha256': hashlib.sha256((out / 'g1.outer.stderr.raw').read_bytes()).hexdigest(),
    'same_failure_chain_retained': True, 'automatic_retry': False}
with (out / 'g1.outer.invocation.json').open('x', encoding='utf-8') as stream:
    json.dump(record, stream, ensure_ascii=False, indent=2); stream.write('\n')
print(json.dumps({'actual_exit': child.returncode, 'invocation': str(out / 'g1.outer.invocation.json'),
    'stderr_tail': (out / 'g1.outer.stderr.raw').read_text(encoding='utf-8', errors='replace')[-2400:]}, ensure_ascii=True))
sys.exit(child.returncode)
