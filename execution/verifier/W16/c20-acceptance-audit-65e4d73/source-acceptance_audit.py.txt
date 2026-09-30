"""Audit existing C20 fixture receipts; never grants independent acceptance."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid

ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read(path):
    return json.loads(path.read_bytes())


def bounded(base, path):
    result = (base / path).resolve()
    require(result.is_relative_to(base.resolve()) and result.is_file(), 'evidence path outside expected directory or missing')
    return result


def check_hashes(base, hashes):
    require(bool(hashes), 'empty evidence inventory')
    for name, expected in hashes.items():
        require(digest(bounded(base, name)) == 'sha256:' + expected.removeprefix('sha256:'), 'evidence hash mismatch')


def audit_invocation(path, key, head):
    path = bounded(ROOT / 'execution/invocations', path)
    invocation = read(path)
    require(invocation['command_key'] == key and invocation['selectors'] == {'task_id': 'W16', 'check_id': '', 'case_id': 'C20'}, 'wrong C20 invocation')
    require(invocation['status'] == 'PASS' and invocation['exit_code'] == 0 and invocation['assertion_ids'], 'upstream command did not pass')
    require(invocation['code_revision'] == head and invocation['registered_command_revision'] == digest(ROOT / 'execution/commands.json').removeprefix('sha256:'), 'stale command or source revision')
    for stream in ('stdout', 'stderr'):
        item = invocation[stream]
        require(digest(bounded(ROOT / 'execution/invocations', ROOT / item['path'])) == 'sha256:' + item['sha256'], 'invocation stream changed')
    output = read(ROOT / invocation['stdout']['path'])
    report_path = bounded(ROOT / 'execution/receipts', output['receipt'])
    report = read(report_path)
    require(report['status'] == 'PASS' and report['exit_code'] == 0, 'upstream child did not pass')
    check_hashes(report_path.parent, report.get('hashes', report.get('raw_evidence_hashes', {})))
    rows = report['assertions']
    require(len(rows) == len(invocation['assertion_ids']) and {r['assertion_id'] for r in rows} == set(invocation['assertion_ids']), 'assertion inventory mismatch')
    raw_lines = (report_path.parent / 'stdout.txt').read_text(encoding='utf-8').splitlines()
    for row in rows:
        require(row['status'] == 'PASS' and row['expected'] == row['actual'], 'failed upstream assertion')
        line = raw_lines[row.get('raw', row.get('raw_evidence'))['line'] - 1]
        recorded = json.loads(line.split(' ', 1)[1])
        require(recorded == {k: v for k, v in row.items() if k not in ('raw', 'raw_evidence')}, 'assertion not bound to actual output')
    before = read(report_path.parent / 'before.json')
    if key == 'test.evolution':
        check_hashes(ROOT, before['version_manifest']['files'])
        require(before['version_manifest']['code_commit'] == head, 'stale evolution source')
    else:
        check_hashes(ROOT, before['version_manifest'])
        require(before['code_revision'] == head, 'stale Jev source')
    return report_path.parent, report, invocation


def main():
    require(os.getenv('RESEARCHOS_TASK_ID') == 'W16' and os.getenv('RESEARCHOS_CASE_ID') == 'C20' and not os.getenv('RESEARCHOS_CHECK_ID'), 'only exact W16 C20 is implemented')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT).decode().strip()
    evidence = {}
    for key, variable in [('test.evolution', 'RESEARCHOS_C20_EVOLUTION_RECEIPT'), ('test.jev.fixture', 'RESEARCHOS_C20_JEV_RECEIPT')]:
        evidence[key] = audit_invocation(Path(os.environ[variable]), key, head)
    directory, report, invocation = evidence['test.evolution']
    def one(suffix):
        paths = list(directory.glob('*-' + suffix + '.json'))
        require(len(paths) == 1, 'missing or duplicate C20 artifact')
        return read(paths[0])
    benefit, conclusion, locator, rejected = (one(s) for s in ('C20-private-benefit', 'C20-conclusion', 'C20-protected-locator', 'C20-promotion-rejection'))
    require(rejected['status'] == 'REJECTED', 'promotion was not rejected')
    require(benefit['frozen_case_count'] >= 2 and benefit['baseline_correct'] == benefit['candidate_correct'] and benefit['outcome_gain'] is False and benefit['new_score'] > benefit['old_score'] and benefit['new_rubric'] != benefit['old_rubric'], 'score-only benefit was misstated')
    require(conclusion['quality_improved'] is False and conclusion['project_closed'] is False and conclusion['experiment_outcome'] == benefit['experiment_outcome'] == 'NO_IMPROVEMENT' and conclusion['real_world_gain'] == 'NOT_ESTABLISHED', 'final quality or project closure claim changed')
    require(conclusion['private_proof_hash'] == benefit['private_proof_sha256'] == locator['dual_rubric_raw_proof_sha256'] and locator['reopened_and_recomputed'] is True, 'private proof binding changed')
    protected = Path(locator['protected_store']).resolve()
    require(protected.is_relative_to((ROOT.parent / 'verifier-evidence/W16/c20').resolve()), 'private evidence must remain outside repository')
    blobs = {digest(p): p for p in protected.glob('*.bin')}
    require(len(blobs) == 3 and all(locator[k] in blobs for k in ('input_sha256', 'label_sha256', 'dual_rubric_raw_proof_sha256')), 'protected raw evidence missing or changed')
    for path in blobs.values():
        descriptor = read(path.with_suffix('.json'))
        require(descriptor['hash'] == digest(path) and descriptor['size'] == path.stat().st_size and descriptor['measurement_mode'] == 'FIXTURE' and descriptor['project'] == rejected['project_id'], 'protected descriptor binding changed')
    out = ROOT / 'execution/receipts/W16/c20-audit' / str(uuid.uuid4())
    out.mkdir(parents=True)
    ids = ['C20-AUDIT-INTEGRITY', 'C20-AUDIT-VERSIONS', 'C20-AUDIT-NO-GAIN', 'C20-AUDIT-PROTECTED-RAW']
    rows = [{'assertion_id': i, 'expected': True, 'actual': True, 'status': 'PASS'} for i in ids]
    result = {'status': 'PASS', 'exit_code': 0, 'scope': 'C20_EXISTING_FIXTURE_EVIDENCE_ONLY', 'assertion_ids': ids, 'assertions': rows,
              'source_revision': head, 'independent_acceptance': 'NONE', 'ended_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'upstream_invocations': {k: v[2]['invocation_id'] for k, v in evidence.items()},
              'hashes': {}, 'private_proof_sha256': locator['dual_rubric_raw_proof_sha256'],
              'limits': ['Integrity and public conclusion audit; independent verifier must re-evaluate the protected objective proof.', 'No LIVE evaluation, promotion or whole W16 acceptance.']}
    (out / 'report.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': 'PASS', 'assertions': len(ids), 'assertion_ids': ids, 'scope': result['scope'], 'receipt': str(out / 'report.json')}))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'FAIL', 'assertions': 0, 'assertion_ids': [], 'error_type': type(error).__name__}))
        raise SystemExit(1)
