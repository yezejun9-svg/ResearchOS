"""C-only offline tool controller. Never executes candidate source or writes D:."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
MAIN = Path('D:/作品集/ResearchOS/research-os')
LOCK = MAIN / 'execution/toolchains/locked.json'
FILES = ['go.mod', 'validate.go', 'validate_test.go', 'README.md', 'tools/run-author.py']
arguments = argparse.ArgumentParser()
arguments.add_argument('--attempt', type=int, choices=[1, 2], default=1)
options = arguments.parse_args()
origin = 'cli-pure-scalar-missing-test-helper-20261104'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

lock = json.loads(LOCK.read_bytes())
go = lock['tools']['go']
python = lock['tools']['python']
if not Path(go['path']).is_absolute() or sha(go['path']) != go['sha256']:
    raise SystemExit('locked Go executable mismatch')
if Path(sys.executable).resolve() != Path(python['path']).resolve() or sha(python['path']) != python['sha256']:
    raise SystemExit('locked Python executable mismatch')

output = ROOT / 'evidence' / f'attempt-{options.attempt:02d}'
if options.attempt == 2:
    prior = ROOT / 'evidence/attempt-01'
    if 'undefined: assertRejected' not in (prior / 'go-test.stderr.txt').read_text(encoding='utf-8'):
        raise SystemExit('directed retry requires the preserved helper-compilation failure')
output.mkdir(parents=True, exist_ok=False)
private = ROOT / '.local/author-private'
paths = {
    'GOCACHE': private / 'go-cache',
    'GOPATH': private / 'gopath',
    'GOMODCACHE': private / 'gopath/pkg/mod',
    'GOTMPDIR': private / 'go-tmp',
    'TEMP': private / 'tmp',
    'TMP': private / 'tmp',
    'USERPROFILE': private / 'profile',
    'APPDATA': private / 'profile/AppData/Roaming',
    'LOCALAPPDATA': private / 'profile/AppData/Local',
}
for path in paths.values():
    path.mkdir(parents=True, exist_ok=True)
overrides = {key: str(value) for key, value in paths.items()}
overrides.update({
    'GOROOT': str(Path(go['path']).parent.parent),
    'GOPROXY': 'off', 'GOSUMDB': 'off', 'GOENV': 'off',
    'GOTOOLCHAIN': 'local', 'GOTELEMETRY': 'off', 'GOWORK': 'off',
    'GO111MODULE': 'on', 'CGO_ENABLED': '0', 'GOCACHEPROG': '',
    'GOFLAGS': '-mod=readonly', 'PYTHONDONTWRITEBYTECODE': '1',
})
environment = dict(os.environ, **overrides)
session = json.loads((ROOT.parent / 'SESSION.json').read_bytes())
put(output / 'inputs.json', {
    'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'cwd': str(ROOT), 'tools': {'go': go, 'python': python},
    'tool_lock_path': str(LOCK), 'tool_lock_sha256': sha(LOCK),
    'environment_overrides': overrides,
    'source_before_format_sha256': {name: sha(ROOT / name) for name in FILES},
    'session_sha256': sha(ROOT.parent / 'SESSION.json'),
    'baseline_checkpoint': session['baseline_checkpoint'],
    'baseline_failure_records': session['baseline_failure_records'],
    'measurement_mode': 'STANDALONE_DEVELOPMENT_ONLY',
    'attempt_index': options.attempt, 'failure_origin': origin,
    'previous_attempt': 'evidence/attempt-01' if options.attempt == 2 else None,
    'formal_increment': 0, 'researchos_d_source_or_state_writes': 0,
})
shutil.copyfile(Path(__file__), output / 'controller.py.txt')

results = []
failure = None
for name, argv in [
    ('go-version', [go['path'], 'version']),
    ('go-fmt', [go['path'], 'fmt', './...']),
    ('go-test', [go['path'], 'test', '-count=1', '-v', './...']),
]:
    put(output / (name + '.command.json'), {'argv': argv, 'cwd': str(ROOT), 'expected_exit': 0, 'environment_overrides': overrides})
    begin = time.monotonic()
    with (output / (name + '.stdout.txt')).open('wb') as stdout, (output / (name + '.stderr.txt')).open('wb') as stderr:
        try:
            process = subprocess.run(argv, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr, timeout=300)
            code = process.returncode
            cause = None
        except subprocess.TimeoutExpired:
            code, cause = 124, 'tool timeout'
        except OSError as error:
            code, cause = 125, type(error).__name__ + ': ' + str(error)
    result = {'name': name, 'exit_code': code, 'elapsed_seconds': round(time.monotonic() - begin, 3), 'terminal': True, 'cause': cause}
    results.append(result)
    put(output / (name + '.result.json'), result)
    print(json.dumps(result), flush=True)
    if code != 0:
        failure = result
        break

frozen = {name: sha(ROOT / name) for name in FILES}
put(output / 'source-manifest.json', {'files': [{'path': name, 'sha256': digest, 'bytes': (ROOT / name).stat().st_size} for name, digest in frozen.items()], 'frozen': failure is None})
for name in FILES:
    target = output / 'frozen-source' / (name + '.txt')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, target)
test_output = (output / 'go-test.stdout.txt').read_text(encoding='utf-8') if (output / 'go-test.stdout.txt').exists() else ''
passed = re.findall(r'^--- PASS: (Test[^\s(]+)', test_output, re.M)
failed = re.findall(r'^--- FAIL: (Test[^\s(]+)', test_output, re.M)
summary = {
    'status': 'FROZEN_STANDALONE_TESTS_PASSED_NOT_INTEGRATED' if failure is None else 'FAILED_OR_BLOCKED_FIRST_EVIDENCE_PRESERVED',
    'results': results, 'first_failure': failure,
    'failure_origin': origin, 'attempt_index': options.attempt,
    'previous_attempt': 'evidence/attempt-01' if options.attempt == 2 else None,
    'passed_test_functions': passed, 'failed_test_functions': failed,
    'passed_function_count': len(passed), 'source_sha256': frozen,
    'package': 'deliverygate', 'function_policy': 'fixed package candidate / Clamp / three named int32 inputs / one unnamed int32 result',
    'proof_scope': 'Structural AST/types and exact-byte SHA256 consistency only; not Clamp correctness, compilation/execution of submitted code, LIVE acceptance, or trusted benchmark isolation.',
    'researchos_applied': False, 'researchos_d_source_or_state_writes': 0,
    'formal_increment': 0, 'independent_acceptance': 'NOT_REQUESTED', 'counter_reset': False,
    'private_profile_and_go_paths': overrides,
    'limitations': ['An incorrect Clamp such as return 0 intentionally passes the structural policy.', 'A later integration must bind trusted inputs and consume the sealed bytes or reverify actual compiler input bytes.', 'No ordinary LIVE Goal gate, model, native host, server, database or registry was changed.'],
}
put(output / 'author-summary.json', summary)
put(output / 'diagnostics.json', {'first_failure': failure, 'failure_origin': origin, 'attempt_index': options.attempt, 'earlier_failures_preserved': True, 'previous_failure_ref': 'evidence/attempt-01/go-test.stderr.txt' if options.attempt == 2 else None, 'directed_fix': 'Added the missing assertRejected test helper; validator implementation unchanged.' if options.attempt == 2 else None, 'global_failure_counter': 'Parent-owned; not modified here.', 'read_diagnostics': [], 'no_d_write_commands': True})
evidence = {str(path.relative_to(output)).replace('\\', '/'): sha(path) for path in sorted(output.rglob('*')) if path.is_file()}
put(output / 'evidence-manifest.json', {'source_sha256': frozen, 'evidence_sha256': evidence})
print(json.dumps({'status': summary['status'], 'passed_function_count': len(passed), 'first_failure': failure, 'source_sha256': frozen}, ensure_ascii=False), flush=True)
raise SystemExit(0 if failure is None else 1)
