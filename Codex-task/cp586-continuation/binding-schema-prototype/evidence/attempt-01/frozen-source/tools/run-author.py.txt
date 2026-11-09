"""C-only build + fresh integrity fixtures. No product/database/native gate is used."""
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
OUT = ROOT / 'evidence/attempt-01'

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path, value):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

lock = json.loads(LOCK.read_bytes())
for key in ('go', 'python'):
    tool = lock['tools'][key]
    if not Path(tool['path']).is_absolute() or sha(tool['path']) != tool['sha256']:
        raise SystemExit('locked tool drift: ' + key)
if Path(sys.executable).resolve() != Path(lock['tools']['python']['path']).resolve():
    raise SystemExit('wrong Python')
OUT.mkdir(parents=True, exist_ok=False)
private = ROOT / '.local/author-private'
locations = {name: private / path for name, path in {
    'GOCACHE': 'go-cache', 'GOPATH': 'gopath', 'GOMODCACHE': 'gopath/pkg/mod',
    'GOTMPDIR': 'go-tmp', 'TEMP': 'tmp', 'TMP': 'tmp', 'USERPROFILE': 'profile',
    'APPDATA': 'profile/AppData/Roaming', 'LOCALAPPDATA': 'profile/AppData/Local',
}.items()}
for path in locations.values(): path.mkdir(parents=True, exist_ok=True)
overrides = {name: str(path) for name, path in locations.items()}
overrides.update(GOROOT=str(Path(lock['tools']['go']['path']).parent.parent), GOPROXY='off', GOSUMDB='off',
                 GOENV='off', GOTOOLCHAIN='local', GOTELEMETRY='off', GOWORK='off', GOFLAGS='-mod=readonly',
                 GO111MODULE='on', CGO_ENABLED='0', GOCACHEPROG='', PYTHONDONTWRITEBYTECODE='1')
environment = dict(os.environ, **overrides)
helper = ROOT / '.local/canonicalhash.exe'
go, python = lock['tools']['go']['path'], lock['tools']['python']['path']
put(OUT / 'inputs.json', {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'cwd': str(ROOT), 'tools': {name: lock['tools'][name] for name in ('go', 'python')},
    'tool_lock_sha256': sha(LOCK), 'environment_overrides': overrides,
    'root_decisions': str(ROOT / 'DECISIONS.md'), 'root_decisions_sha256': sha(ROOT / 'DECISIONS.md'),
    'scope': 'C-only schema/canonical/fresh fake SQLite integrity; no product schema version or migration assignment',
    'native_model_old_database_D_writes': 0, 'formal_increment': 0})
shutil.copyfile(Path(__file__), OUT / 'controller.py.txt')
commands = [
    ('prepare-canonical', [python, '-B', '-X', 'utf8', 'tools/prepare-canonical.py']),
    ('render-ddl', [python, '-B', '-X', 'utf8', 'tools/render-ddl.py']),
    ('go-fmt-helper', [go, 'fmt', './cmd/...']),
    ('go-test-vectors', [go, 'test', '-count=1', '-v', './...']),
    ('go-build-helper', [go, 'build', '-o', str(helper), './cmd/canonicalhash']),
    ('python-fresh-fixtures', [python, '-B', '-X', 'utf8', '-m', 'unittest', '-v', 'test_bindings']),
]
results = []
first_failure = None
for name, argv in commands:
    if name == 'python-fresh-fixtures':
        put(ROOT / '.local/canonical-helper.json', {'path': str(helper), 'sha256': sha(helper)})
    put(OUT / (name + '.command.json'), {'argv': argv, 'cwd': str(ROOT), 'environment_overrides': overrides, 'expected_exit': 0})
    start = time.monotonic()
    with (OUT / (name + '.stdout.txt')).open('wb') as stdout, (OUT / (name + '.stderr.txt')).open('wb') as stderr:
        try:
            process = subprocess.run(argv, cwd=ROOT, env=environment, stdout=stdout, stderr=stderr, timeout=300)
            code, cause = process.returncode, None
        except subprocess.TimeoutExpired:
            code, cause = 124, 'tool timeout'
        except OSError as error:
            code, cause = 125, repr(error)
    result = {'name': name, 'exit_code': code, 'cause': cause, 'elapsed_seconds': round(time.monotonic() - start, 3), 'terminal': True}
    put(OUT / (name + '.result.json'), result)
    results.append(result)
    print(json.dumps(result), flush=True)
    if code != 0:
        first_failure = result
        break
source_paths = [path for path in ROOT.rglob('*') if path.is_file() and '.local' not in path.relative_to(ROOT).parts and 'evidence' not in path.relative_to(ROOT).parts and '__pycache__' not in path.relative_to(ROOT).parts]
frozen = {str(path.relative_to(ROOT)).replace('\\', '/'): sha(path) for path in sorted(source_paths)}
canonical = ROOT / 'canonical/jcs.go'
if canonical.exists() and sha(canonical) != '7aad384f03ced5d4033145d5bf2953909be72c658642bbfc1b7795fd037f4d8d':
    raise SystemExit('copied canonical source changed')
put(OUT / 'source-manifest.json', {'frozen': first_failure is None, 'files': [{'path': name, 'sha256': digest, 'bytes': (ROOT / name).stat().st_size} for name, digest in frozen.items()]})
for name in frozen:
    target = OUT / 'frozen-source' / (name + '.txt')
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / name, target)
python_log = (OUT / 'python-fresh-fixtures.stderr.txt').read_text(encoding='utf-8') if (OUT / 'python-fresh-fixtures.stderr.txt').exists() else ''
count = re.search(r'^Ran (\d+) tests? in ', python_log, re.M)
go_log = (OUT / 'go-test-vectors.stdout.txt').read_text(encoding='utf-8') if (OUT / 'go-test-vectors.stdout.txt').exists() else ''
summary = {'status': 'FROZEN_SCHEMA_INTEGRITY_FIXTURE_NOT_AUTHORIZATION' if first_failure is None else 'AUTHOR_FAILURE_PRESERVED',
    'results': results, 'first_failure': first_failure, 'source_sha256': frozen,
    'python_test_count': int(count.group(1)) if count else None,
    'go_passed_test_functions': re.findall(r'^--- PASS: (Test[^\s(]+)', go_log, re.M),
    'canonical_source_sha256': sha(canonical) if canonical.exists() else None,
    'helper_sha256': sha(helper) if helper.exists() else None,
    'original_open_semantics_and_probe_preserved': True,
    'not_connected': ['Native approval consumption', 'real Owner/root/Host/refs/profile/suite/lineage', 'source witness/checker', 'Task/Goal factories and pending audit', 'Goal503 exception', 'production migration/backup restore'],
    'classification': 'SCHEMA_PROTOTYPE / INTEGRITY_FIXTURE_ONLY', 'formal_increment': 0,
    'D_writes': 0, 'old_database_connections': 0, 'counter_reset': False}
put(OUT / 'author-summary.json', summary)
put(OUT / 'diagnostics.json', {'first_failure': first_failure, 'previous_probe': '../sqlite-prerequisite-probe-01.json',
    'semantic_resolution': '../../DECISIONS.md', 'original_open_semantics_preserved': True, 'global_counter': 'Not modified; parent-owned.'})
evidence = {str(path.relative_to(OUT)).replace('\\', '/'): sha(path) for path in sorted(OUT.rglob('*')) if path.is_file()}
put(OUT / 'evidence-manifest.json', {'source_sha256': frozen, 'evidence_sha256': evidence})
print(json.dumps({'status': summary['status'], 'python_test_count': summary['python_test_count'], 'first_failure': first_failure, 'source_manifest_sha256': sha(OUT / 'source-manifest.json')}, ensure_ascii=False), flush=True)
raise SystemExit(0 if first_failure is None else 1)
