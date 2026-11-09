"""Owner evidence for synthetic native protected-body checks; not formal G04."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[3]


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    if platform.system() != 'Windows':
        raise SystemExit('Windows native canary execution required')
    go = Path(os.environ.get('RESEARCHOS_GO', ROOT / '.local/tools/go1.27.1/go/bin/go.exe'))
    if not go.is_file():
        raise SystemExit('RESEARCHOS_GO must point to the pinned Go 1.27.1 executable')
    version = subprocess.check_output([str(go), 'version'], text=True).strip()
    if not version.startswith('go version go1.27.1 '):
        raise SystemExit('pinned Go 1.27.1 required')
    inventory = json.loads((ROOT / 'tests/jev/protected/expected.json').read_text(encoding='utf-8'))
    expected = [item for items in inventory.values() for item in items]
    if len(expected) != 41 or len(set(expected)) != 41:
        raise SystemExit('exact frozen 41-assertion inventory required')
    run_id = str(uuid.uuid4())
    out = ROOT / 'execution/receipts/W11/protected' / run_id
    out.mkdir(parents=True)
    env = {k: v for k, v in os.environ.items() if 'JEV' not in k.upper() and 'TYPESAFE' not in k.upper()}
    command = [str(go), 'test', './tests/jev/protected', './internal/domain', '-v', '-count=1', '-timeout=2m', '-run', '^(' + '|'.join(inventory) + ')$']
    patterns = ['adapters/protectedstore/*.go', 'adapters/runtime/*.go', 'adapters/decision/*.go',
                'internal/domain/*.go', 'internal/canonical/*.go', 'internal/store/*.go',
                'ops/experiment_sandbox/*.go', 'tests/jev/protected/*', 'go.mod', 'go.sum',
                'spec/v2.0/contracts/*.json', 'migrations/sqlite/*.sql']
    manifest = {p.relative_to(ROOT).as_posix(): digest(p) for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
    before = {
        'schema': 'W11_PROTECTED_CANARY_EVIDENCE_V1', 'task_id': 'W11', 'run_id': run_id,
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
        'scope': 'CANARY_ONLY', 'environment_mode': 'FIXTURE_NATIVE_WINDOWS',
        'formal_G04': 'BLOCKED', 'formal_A08': 'BLOCKED', 'formal_holdout_accessed': False,
        'real_provider_called': False, 'automatic_authority': 'NONE', 'maximum_mode': 'ADVISORY',
        'executor_identity': 'codex:/root/resources', 'verifier_identity': None,
        'os': platform.platform(), 'architecture': platform.machine(), 'go_version': version,
        'implementation_model': 'gpt-6-astra', 'reasoning_effort': 'high',
        'argv': command, 'cwd': str(ROOT), 'version_manifest': manifest,
        'expected_assertion_ids': sorted(expected),
    }
    save(out / 'before.json', before)
    try:
        result = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=140)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, code = error.stdout or b'', error.stderr or b'', 124
    (out / 'stdout.txt').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    rows, malformed = [], False
    prefix = 'W11_PROTECTED_ASSERTION '
    for line_number, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if not line.startswith(prefix):
            continue
        try:
            row = json.loads(line[len(prefix):])
            if not isinstance(row, dict) or not all(key in row for key in ['assertion_id', 'expected', 'actual', 'status', 'evidence', 'scope', 'formal_isolation']):
                malformed = True
                continue
            row['raw_evidence'] = {'path': 'stdout.txt', 'line': line_number, 'sha256': digest(out / 'stdout.txt')}
            rows.append(row)
        except (ValueError, TypeError):
            malformed = True
    ids = [r['assertion_id'] for r in rows]
    drift = [p for p, h in manifest.items() if not (ROOT / p).is_file() or digest(ROOT / p) != h]
    passed = code == 0 and not malformed and not drift and len(ids) == len(expected) and set(ids) == set(expected) and all(r['status'] == 'PASS' and r['expected'] == r['actual'] and r['scope'] == 'CANARY_ONLY' and r['formal_isolation'] == 'BLOCKED' for r in rows)
    report = {
        'schema': before['schema'], 'task_id': 'W11', 'run_id': run_id,
        'status': 'PASS' if passed else 'FAIL', 'executor_status': 'EXECUTION_REPORTED',
        'independent_acceptance': 'PENDING', 'formal_G04': 'BLOCKED', 'formal_A08': 'BLOCKED',
        'scope': 'CANARY_ONLY', 'automatic_authority': 'NONE', 'maximum_mode': 'ADVISORY',
        'exit_code': code, 'assertions': rows, 'assertion_count': len(rows),
        'expected_assertion_ids': sorted(expected), 'missing': sorted(set(expected) - set(ids)),
        'malformed': malformed, 'source_drift': drift,
        'raw_evidence_hashes': {p.name: digest(p) for p in out.iterdir() if p.is_file()},
        'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    save(out / 'report.json', report)
    print(json.dumps({'status': report['status'], 'assertions': len(rows), 'receipt': str(out / 'report.json')}))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
