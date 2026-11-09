import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path.cwd().resolve()
out = Path(__file__).resolve().parent
authorization = out / 'provider_g1_esm_execution_scope.json'
authorization_sha = hashlib.sha256(authorization.read_bytes()).hexdigest()
assert authorization_sha == 'b10055069ae7581c0075e8d8ab78d9d1e1d9c22f06936d828899f997055588d2'
cp_path = root / 'execution/v2.4/checkpoint.json'
cp = json.loads(cp_path.read_bytes())
assert cp['revision'] == 300 and len(cp['failure_counters']) == 316
runner = root / 'execution/v2.4/receipts/W05/W05-99/provider_whole9_g1_esm_repair_preparation_codex/788ce69c409b472799ee1389b778f9da/run_g1.py'
assert hashlib.sha256(runner.read_bytes()).hexdigest() == '6562febe8fd5fab1be63405c4511b4cf31faafbcf007a36b05b0d1c30792e42d'
if sys.flags.optimize != 0:
    raise RuntimeError('Optimized Python prohibited')
argv = [sys.executable, '-I', str(runner), '--execute', '--actor', 'codex:/root',
    '--authorization', str(authorization), '--authorization-sha', authorization_sha, '--counter-state', str(cp_path)]
env = {k: v for k, v in os.environ.items() if k.upper() not in {'NODE_COMPILE_CACHE', 'NODE_V8_COVERAGE', 'NODE_DEBUG', 'NODE_DEBUG_NATIVE', 'PYTHONOPTIMIZE', 'PYTHONPATH'}}
env['NODE_DISABLE_COMPILE_CACHE'] = '1'
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
with (out / 'g1.outer.stdout.raw').open('xb') as stdout, (out / 'g1.outer.stderr.raw').open('xb') as stderr:
    child = subprocess.run(argv, cwd=root, env=env, stdout=stdout, stderr=stderr)
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
