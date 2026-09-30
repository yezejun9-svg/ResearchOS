#!/usr/bin/env python3
"""Run W15-G01/A09 with strict selectors and retain raw fixture evidence."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_PATH = ROOT / 'tests/skills/expected.json'


def digest(path: Path) -> str:
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['fixture'])
    args = parser.parse_args()
    task, check, case = (os.getenv(k, '') for k in ('RESEARCHOS_TASK_ID', 'RESEARCHOS_CHECK_ID', 'RESEARCHOS_CASE_ID'))
    if task != 'W15' or (check, case) not in (('W15-G01', ''), ('', 'A09')) or args.mode not in (None, 'fixture'):
        parser.error('W15 requires exactly W15-G01 or A09 in fixture mode; W15-G02 remains BLOCKED')
    expected_map = json.loads(EXPECTED_PATH.read_text(encoding='utf-8'))
    selected = list(expected_map)
    expected = [a for name in selected for a in expected_map[name]]
    if not expected or len(expected) != len(set(expected)):
        raise RuntimeError('nonempty, unique frozen assertion inventory required')
    go = Path(os.getenv('RESEARCHOS_GO') or ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not go.is_file():
        parser.error('RESEARCHOS_GO must identify the pinned Go executable')
    run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
    out = ROOT / 'execution/receipts/W15/fixture' / run_id
    out.mkdir(parents=True, exist_ok=False)
    command = [str(go), 'test', '-json', '-count=1', '-timeout=3m', '-run', '^(?:' + '|'.join(selected) + ')$', './internal/domain']
    patterns = ('internal/domain/*.go', 'internal/store/*.go', 'adapters/knowledge/*.go',
                'evaluation/skills/*.go', 'migrations/sqlite/*.sql', 'spec/v2.0/contracts/*.json',
                'tests/skills/*', 'go.mod', 'go.sum', 'contracts/operation_coverage.json')
    sources = {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p)
               for pattern in patterns for p in ROOT.glob(pattern) if p.is_file()}
    before = {
        'schema': 'GLOBAL_EVIDENCE_V1_CANDIDATE', 'task_id': task, 'check_id': check or None,
        'case_id': case or None, 'run_id': run_id, 'started_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'environment_mode': 'FIXTURE', 'executor_identity': os.getenv('RESEARCHOS_EXECUTOR_ID', 'codex:/root/skills_lifecycle'),
        'verifier_identity': None, 'command_key': 'test.skills', 'registry_state': 'BOUND',
        'command_registry_proposal': 'tests/skills/command_registry_proposal.json',
        'command_registry_revision': digest(ROOT / 'execution/commands.json'), 'argv': command, 'cwd': str(ROOT),
        'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'git_status_porcelain': subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True),
        'source_hashes': sources, 'go_tool': {'path': str(go), 'sha256': digest(go)},
        'go_version': subprocess.check_output([str(go), 'version'], cwd=ROOT, text=True).strip(),
        'os': platform.platform(), 'python': platform.python_version(),
        'environment_names': sorted(k for k in os.environ if k.startswith('RESEARCHOS_')),
        'expected_assertion_ids': expected,
        'scope': 'Product HTTP handlers, loopback read, SQLite and synthetic inputs; W15-G02/live and host installation NOT_RUN',
        'construction_acceptance': 'PENDING_INDEPENDENT_VERIFIER',
        'implementation_model': 'gpt-6-sol', 'reasoning_effort': 'high',
    }
    save(out / 'before.json', before)
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=190)
        stdout, stderr, code = result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code = exc.stdout or b'', exc.stderr or b'', 124
    (out / 'stdout.jsonl').write_bytes(stdout)
    (out / 'stderr.txt').write_bytes(stderr)
    events, rows, malformed = [], [], False
    for line_number, line in enumerate(stdout.decode('utf-8', errors='replace').splitlines(), 1):
        try:
            event = json.loads(line)
            events.append(event)
            if event.get('Test') in selected and event.get('Action') == 'output':
                output = event.get('Output', '')
                if output.startswith('W15_ASSERTION '):
                    row = json.loads(output[len('W15_ASSERTION '):])
                    if not all(k in row for k in ('assertion_id', 'expected', 'actual', 'status', 'evidence')):
                        malformed = True
                    row['raw_evidence'] = {'path': 'stdout.jsonl', 'line': line_number, 'sha256': digest(out / 'stdout.jsonl')}
                    rows.append(row)
        except (ValueError, TypeError):
            malformed = True
    ids = [r.get('assertion_id') for r in rows]
    test_passed = all(any(e.get('Action') == 'pass' and e.get('Test') == name for e in events) for name in selected)
    drift = [p for p, h in sources.items() if digest(ROOT / p) != h]
    passed = (code == 0 and test_passed and not malformed and not drift and ids == expected
              and all(r['status'] == 'PASS' and r['expected'] == r['actual'] for r in rows))
    report = {'task_id': task, 'check_id': check or None, 'case_id': case or None, 'run_id': run_id,
              'status': 'PASS' if passed else 'FAIL', 'executor_status': 'EXECUTION_REPORTED',
              'environment_mode': 'FIXTURE', 'exit_code': code, 'assertion_count': len(rows),
              'assertion_ids': ids, 'expected_assertion_ids': expected,
              'missing_assertion_ids': sorted(set(expected) - set(ids)), 'malformed': malformed,
              'source_drift': drift, 'assertions': rows, 'test_passed': test_passed,
              'raw_evidence_hashes': {name: digest(out / name) for name in ('before.json', 'stdout.jsonl', 'stderr.txt')},
              'construction_acceptance': 'PENDING_INDEPENDENT_VERIFIER',
              'product_live_qualification': 'BLOCKED_W15_G02_W14_REAL_INPUT_W05_POLICY',
              'ended_at': dt.datetime.now(dt.timezone.utc).isoformat()}
    save(out / 'report.json', report)
    print(json.dumps({'status': report['status'], 'assertions': len(rows), 'assertion_ids': ids, 'receipt': str(out / 'report.json')}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
