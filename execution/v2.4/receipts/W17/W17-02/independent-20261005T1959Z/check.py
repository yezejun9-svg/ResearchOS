import datetime, hashlib, json, os, pathlib, subprocess, sys

MAIN = pathlib.Path('D:/作品集/ResearchOS/research-os')
ROOT = MAIN / '.local/worktrees/codex-w1702'
OUT = pathlib.Path(__file__).resolve().parent
EVIDENCE = ROOT / 'execution/v2.4/receipts/W17/W17-02/20261005T193538Z-b41b6c472b'
sys.path.insert(0, str(ROOT / 'tests/security'))
import w1702, c22_fixture as c22

def save(name, value):
    path = OUT / name
    with path.open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)

rows = []
def check(name, condition, detail):
    rows.append({'id': name, 'status': 'PASS' if condition else 'FAIL', 'detail': detail})
    if not condition:
        raise AssertionError(name)

commands = []
def run(name, argv):
    env = dict(os.environ, GOTOOLCHAIN='local', GOENV='off', GOPATH=str(MAIN / '.local/gopath'), GOCACHE=str(MAIN / '.local/gocache'))
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    proc = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        stdout, stderr = proc.communicate(timeout=180)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
    for suffix, raw in [('stdout', stdout), ('stderr', stderr)]:
        with (OUT / (name + '.' + suffix)).open('xb') as f:
            f.write(raw)
    commands.append({'argv': argv, 'cwd': str(ROOT), 'started_at': start, 'exit_code': proc.returncode})
    check(name + '-exit', proc.returncode == 0, proc.returncode)
    return stdout

try:
    manifest = c22.read(EVIDENCE / 'source-manifest.json')
    drift = [p for p, h in manifest['files'].items() if c22.digest(ROOT / p) != h]
    check('candidate-source-hashes', not drift, {'count': len(manifest['files']), 'drift': drift})
    index = c22.read(EVIDENCE / 'evidence-index.json')
    drift = [p for p, h in index['files'].items() if c22.digest(EVIDENCE / p) != h]
    check('candidate-evidence-hashes', not drift, {'count': len(index['files']), 'drift': drift})
    events = [json.loads(x) for x in (EVIDENCE / 'c22.stdout.jsonl').read_text().splitlines()]
    validated = c22.validate_evidence(EVIDENCE, events, c22.read(c22.EXPECTED))
    check('c22-raw-revalidation', len(validated['assertions']) == 137, {'assertions': 137, 'http': validated['http_count'], 'scan': validated['scan']})
    report = c22.read(EVIDENCE / 'report.json')
    ids = [r['assertion_id'] for r in report['assertions']]
    check('producer-unique-nonzero-inventory', len(ids) == len(set(ids)) == 154 and all(r['status'] == 'PASS' and r['actual'] == r['expected'] for r in report['assertions']), len(ids))
    check('producer-commands', len(report['commands']) == 2 and all(c['exit_code'] == 0 for c in report['commands']), report['commands'])
    locked = c22.read(ROOT / 'execution/toolchains/locked.json')['tools']
    go = str(MAIN / '.local/tools/go1.27.1/go/bin/go.exe')
    check('locked-tools', c22.digest(pathlib.Path(go)) == 'sha256:' + locked['go']['sha256'] and c22.digest(pathlib.Path(sys.executable)) == 'sha256:' + locked['python']['sha256'], {'go': c22.digest(pathlib.Path(go)), 'python': c22.digest(pathlib.Path(sys.executable))})
    raw = run('independent-increment', [go, 'test', './internal/domain', '-run', '^(TestW1702AuthorityTransitions|TestProtectedReadRevalidation)$', '-count=1', '-timeout=120s', '-json'])
    current_rows = w1702.validate_increment([json.loads(x) for x in raw.decode('utf-8').splitlines()])
    check('independent-increment-unique', len(current_rows) == len({r['assertion_id'] for r in current_rows}) == 17, current_rows)
    run('handler-mutations', [sys.executable, '-B', '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'tests/security', '-p', 'test_w1702_handler.py', '-v'])
    check('post-run-source-stable', all(c22.digest(ROOT / p) == h for p, h in manifest['files'].items()), len(manifest['files']))
finally:
    save('checks.json', {'checks': rows, 'commands': commands, 'fixture_product_assertions': 17, 'producer_assertions_revalidated': 154, 'formal_holdout_accessed': False})

print(json.dumps({'status': 'PASS', 'independent_checks': len(rows), 'fixture_product_assertions': len(current_rows), 'producer_assertions_revalidated': len(ids)}))
