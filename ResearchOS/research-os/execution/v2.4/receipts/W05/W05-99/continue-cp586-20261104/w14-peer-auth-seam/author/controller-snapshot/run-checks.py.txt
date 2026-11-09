from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os/.local/worktrees/w14-peer-auth-seam-20261104')
RECEIPT = Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/continue-cp586-20261104/w14-peer-auth-seam/author')
LOCK = Path('D:/作品集/ResearchOS/research-os/execution/toolchains/locked.json')
attempt = sys.argv[1]
selection = sys.argv[2] if len(sys.argv) > 2 else 'all'
assert selection in ('all', 'api-only')
out = RECEIPT/attempt
out.mkdir(exist_ok=False)
lock = json.loads(LOCK.read_text(encoding='utf-8-sig'))
go = Path(lock['tools']['go']['path'])
assert hashlib.sha256(go.read_bytes()).hexdigest() == lock['tools']['go']['sha256']
git = Path(lock['tools']['git']['path'])
assert hashlib.sha256(git.read_bytes()).hexdigest() == lock['tools']['git']['sha256']
gofmt = go.with_name('gofmt.exe')
scope = json.loads((RECEIPT.parent/'scope.json').read_text(encoding='utf-8-sig'))
names = scope['production_paths'] + scope['test_paths']
profile = HERE/'runtime'
settings = {
    'GOCACHE': str(profile/'gocache'), 'GOPATH': str(profile/'gopath'),
    'GOMODCACHE': 'D:/作品集/ResearchOS/research-os/.local/tools/gopath/pkg/mod',
    'GOTMPDIR': str(profile/'tmp'), 'TMP': str(profile/'tmp'), 'TEMP': str(profile/'tmp'),
    'APPDATA': str(profile/'profile/roaming'), 'LOCALAPPDATA': str(profile/'profile/local'),
    'USERPROFILE': str(profile/'profile'),
    'GOPROXY': 'off', 'GOSUMDB': 'off', 'GOENV': 'off', 'GOTOOLCHAIN': 'local',
    'GOTELEMETRY': 'off', 'GOWORK': 'off', 'CGO_ENABLED': '0',
    'GOFLAGS': '-mod=readonly -p=1 -buildvcs=false', 'GOMAXPROCS': '2',
}
for key in ['GOCACHE','GOPATH','GOTMPDIR','APPDATA','LOCALAPPDATA','USERPROFILE']:
    Path(settings[key]).mkdir(parents=True, exist_ok=True)
env = os.environ.copy()
env = {k: v for k, v in env.items() if not k.upper().startswith(('RESEARCHOS_', 'MU_'))}
env.update(settings)

def save(name, value):
    with (out/name).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')

save('input.json', {
    'scope': scope['scope_id'], 'base': scope['base_head'], 'cwd': str(ROOT),
    'attempt': attempt, 'selection': selection, 'environment_overrides': settings,
    'toolchain': lock['tools']['go'],
    'gofmt_sha256': hashlib.sha256(gofmt.read_bytes()).hexdigest(),
    'source_before': {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names},
    'runtime_scope': 'injected/fresh development fixtures only; no native/product/model process',
})
commands = [
    ('format', [str(gofmt), '-w', *names]),
    ('host-focused', [str(go), 'test', './internal/host', '-run', '^(TestNativePeerCapability.*|TestHostBootEntropyFailurePrecedesMutableInitialization)$', '-count=1', '-timeout=60s', '-json']),
    ('domain-focused', [str(go), 'test', './internal/domain', '-run', '^TestCommandAuthContext', '-count=1', '-timeout=60s', '-json']),
    ('api-focused', [str(go), 'test', './internal/api', '-run', '^TestCommandAuthHTTP', '-count=1', '-timeout=60s', '-json']),
    ('compatibility', [str(go), 'test', './internal/domain', './internal/api', '-run', '^(TestClientTypedRejectionRollsBackBusinessWrites|TestAttachGrantFaultRollsBackEpochAndIdentity|TestAttachSnapshotFaultRollsBackHandoffAndJournal|TestW14SessionHTTPCreateSendEventsAndReplay|TestW14SessionHTTPAuthorityAndFrozenRequest|TestW14SessionWriterLeaseHandoff|TestAttachHTTPRawReplayAndDefaultLease)$', '-count=1', '-timeout=60s', '-json']),
    ('diff-check', [str(git), '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'diff', '--check']),
    ('scope-status', [str(git), '-c', 'gc.auto=0', '-c', 'maintenance.auto=false', 'status', '--short', '--untracked-files=all']),
]
rows = []
if selection == 'api-only':
    commands = [(name, [str(gofmt), '-w', 'internal/api/v2_auth_context_test.go'] if name == 'format' else argv)
                for name, argv in commands if name in ('format','api-focused','diff-check','scope-status')]
for name, argv in commands:
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    print(json.dumps({'phase': name, 'state': 'STARTED'}, ensure_ascii=False), flush=True)
    try:
        done = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=240, check=False)
        code, stdout, stderr = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        code, stdout, stderr = 124, exc.stdout or b'', exc.stderr or b''
    (out/(name+'.stdout.raw')).write_bytes(stdout)
    (out/(name+'.stderr.raw')).write_bytes(stderr)
    row = {'name': name, 'argv': argv, 'cwd': str(ROOT), 'started': started,
           'finished': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'exit_code': code,
           'stdout_sha256': hashlib.sha256(stdout).hexdigest(), 'stderr_sha256': hashlib.sha256(stderr).hexdigest()}
    save(name+'.command.json', row)
    rows.append(row)
    print(json.dumps({'phase': name, 'exit_code': code, 'stderr_preview': stderr.decode('utf-8', errors='replace')[:700]}, ensure_ascii=False), flush=True)
    if name == 'format' and code != 0:
        break
save('results.json', {'status': 'DEVELOPMENT_CHECKS_PASS' if all(x['exit_code']==0 for x in rows) else 'DEVELOPMENT_CHECKS_FAILED',
                      'commands': rows, 'formal_increment': 0, 'native_model_calls': 0,
                      'sources_after': {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}})
sys.exit(0 if all(x['exit_code']==0 for x in rows) else 1)
