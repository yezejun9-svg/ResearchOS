"""Frozen W11 fixture assertions. This command never calls a live provider."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = json.loads((ROOT / 'tests/jev/expected.json').read_text(encoding='utf-8'))
GROUPS = {
    'W11-G01': [name for name in EXPECTED if name != 'TestW11C20RubricOnly'],
    'C07': ['TestW11HardGates', 'TestW11ManualDecisionHardGate'],
    'C08': ['TestW11HostAndFallback', 'TestW11QualificationClosed', 'TestW11ImportedProvenance'],
    'C20': ['TestW11C20RubricOnly'],
}


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def main(command_key='test.jev.fixture'):
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fixture'], default='fixture')
    args = parser.parse_args()
    task, check, case = (os.getenv(k, '') for k in ['RESEARCHOS_TASK_ID', 'RESEARCHOS_CHECK_ID', 'RESEARCHOS_CASE_ID'])
    w11 = task == 'W11' and ((check == 'W11-G01' and not case) or (not check and case in ('C07', 'C08')))
    w16_c20 = task == 'W16' and not check and case == 'C20'
    if not (w11 or w16_c20):
        parser.error('exact W11-G01 / C07 / C08 or W16/C20 selector required; live/protected gates are separate')
    selector = check or case
    go = os.getenv('RESEARCHOS_GO') or str(ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not Path(go).is_file():
        parser.error('RESEARCHOS_GO must name the pinned Go executable')
    names = GROUPS[selector]
    expected = [a for name in names for a in EXPECTED[name]]
    if not expected or len(expected) != len(set(expected)):
        raise RuntimeError('nonzero, unique frozen assertion inventory required')
    run_id = str(uuid.uuid4())
    out = ROOT / ('execution/receipts/W16/c20-private/jev' if w16_c20 else 'execution/receipts/W11/fixture') / run_id
    out.mkdir(parents=True)
    env = dict(os.environ)
    # Credentials are neither needed nor propagated to fixture subprocesses.
    for key in list(env):
        if 'JEV' in key.upper() or 'TYPESAFE' in key.upper():
            del env[key]
    command = [go, 'test', './adapters/decision', './internal/domain', '-v', '-count=1', '-timeout=2m', '-run', '^(' + '|'.join(names) + ')$']
    patterns = ['adapters/decision/*.go', 'internal/domain/*.go', 'internal/canonical/*.go', 'internal/store/*.go',
                'spec/v2.0/contracts/*.json', 'migrations/sqlite/*.sql', 'go.mod', 'go.sum',
                'execution/commands.json', 'tests/jev/expected.json', 'ops/ci/jev.py']
    manifest = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
    before = {
        'schema': 'GLOBAL_EVIDENCE_V1_CANDIDATE', 'task_id': task, 'check_id': check, 'case_id': case, 'run_id': run_id,
        'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'environment_mode': 'FIXTURE',
        'os': platform.platform(), 'architecture': platform.machine(), 'executor_identity': os.getenv('RESEARCHOS_EXECUTOR_ID', 'codex:/root/resources'),
        'verifier_identity': None, 'code_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, encoding='utf-8').strip(),
        'dirty': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True, encoding='utf-8'),
        'command_key': command_key, 'registered_command_revision': digest(ROOT / 'execution/commands.json'),
        'argv': command, 'cwd': str(ROOT), 'environment_names': sorted(env), 'version_manifest': manifest,
        'go_version': subprocess.check_output([go, 'version'], cwd=ROOT, text=True).strip(),
        'expected_assertion_ids': sorted(expected), 'implementation_model': 'gpt-6-astra', 'reasoning_effort': 'high',
        'runtime_model': {'provider': 'LOOPBACK_FIXTURE', 'model': 'jev-1.13.0', 'real_provider_called': False},
        'scope': 'W16 C20 Jev rubric-only fixture interface' if w16_c20 else 'W11 typed adapter, authenticated host invocation, C07 hard gates, C08 fallback and W11 interface portion of C20',
        'excluded': ['real provider', 'LIVE qualification', 'automatic authority', 'full C20 acceptance'] if w16_c20 else ['A08 LIVE_SERVICE', 'W11-G02', 'W11-G03', 'W11-G04 protected identity isolation', 'W16 full C20'],
        'rubric': 'spec/v2.0/contracts/acceptance.json C07/C08; tests/jev/expected.json exact assertion inventory',
        'automatic_authority': 'NONE', 'qualification_maximum_mode': 'ADVISORY',
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
    for number, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        if not line.startswith('W11_ASSERTION '):
            continue
        try:
            row = json.loads(line[len('W11_ASSERTION '):])
            if not all(k in row for k in ['assertion_id', 'expected', 'actual', 'status', 'evidence']):
                malformed = True
            row['raw_evidence'] = {'path': 'stdout.txt', 'line': number, 'sha256': digest(out / 'stdout.txt')}
            rows.append(row)
        except ValueError:
            malformed = True
    ids = [r.get('assertion_id') for r in rows]
    drift = [p for p, h in manifest.items() if not (ROOT / p).is_file() or digest(ROOT / p) != h]
    passed = code == 0 and not malformed and not drift and len(ids) == len(expected) and set(ids) == set(expected) and all(r['status'] == 'PASS' and r['expected'] == r['actual'] for r in rows)
    report = {'task_id': task, 'check_id': check, 'case_id': case, 'run_id': run_id, 'status': 'PASS' if passed else 'FAIL',
              'executor_status': 'EXECUTION_REPORTED', 'exit_code': code, 'assertions': rows,
              'assertion_ids': ids, 'expected_assertion_ids': sorted(expected), 'missing': sorted(set(expected) - set(ids)),
              'malformed': malformed, 'source_drift': drift, 'environment_mode': 'FIXTURE',
              'raw_evidence_hashes': {p.name: digest(p) for p in out.iterdir() if p.is_file()},
              'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'independent_acceptance': 'NOT_REQUESTED', 'global_evidence': 'CANDIDATE_PENDING_INDEPENDENT_VERIFIER',
              'scope': before['scope'], 'excluded': before['excluded'], 'automatic_authority': 'NONE'}
    save(out / 'report.json', report)
    print(json.dumps({'status': report['status'], 'assertions': len(rows), 'assertion_ids': ids, 'scope': before['scope'], 'receipt': str(out / 'report.json')}))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
