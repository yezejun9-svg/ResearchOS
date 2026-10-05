"""Exact W11/W11-02 check: fixture negatives + pinned public readiness records.

Exit 2 means genuine resource BLOCKED, never PASS or independent acceptance.
The old test.jev.live selectors continue to use their existing handler.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = {
    'REPORT-NEVER-GRANTS', 'UNKNOWN-COST-NULL', 'LATENCY', 'SMOKE12',
    'MODEL-VOTE', 'DEVELOPMENT-AS-HOLDOUT', 'FAMILY-OVERLAP', 'HOLDOUT-TUNING',
    'FIXTURE-AS-LIVE', 'ARCHIVE-AS-NEW-LIVE', 'CROSS-PURPOSE', 'CROSS-LANGUAGE',
    'CROSS-PROVIDER', 'CROSS-MODEL', 'CROSS-RUBRIC', 'MISSING-KEY',
    'INSUFFICIENT-DEV', 'INCOMPLETE-CALLS', 'CRITICAL-ERROR', 'FALSE-ACCEPT-OVER-5',
    'DISAGREEMENT-OVER-5', 'ALL-ABSTAIN', 'COUNT-MISMATCH', 'OVERFLOW',
    'NEGATIVE-COST', 'DENOMINATORS', 'LABEL-COUNTS', 'EXACT-5-PERCENT',
    *('REUSE-' + n for n in ('license_unknown', 'platform_mismatch',
      'integration_unavailable', 'no_benefit', 'missing_evidence',
      'readme_injection', 'timeout', 'abstain', 'cross_scope_qualification')),
}
EXPECTED = {'W1102-' + item for item in EXPECTED}


def digest(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    with path.open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def main():
    selector = (os.getenv('RESEARCHOS_TASK_ID'), os.getenv('RESEARCHOS_CHECK_ID'),
                os.getenv('RESEARCHOS_CASE_ID', ''))
    if selector != ('W11', 'W11-02', '') or len(sys.argv) != 1:
        print('UNBOUND: exact W11/W11-02 selector with no case/arguments required', file=sys.stderr)
        return 1
    go = Path(os.getenv('RESEARCHOS_GO') or ROOT / '.local/tools/go1.27.1/go/bin/go.exe')
    if not go.is_file():
        print('pinned Go unavailable', file=sys.stderr)
        return 1
    out = ROOT / 'execution/v2.4/receipts/W11/W11-02/dispatched' / str(uuid.uuid4())
    out.mkdir(parents=True, exist_ok=False)
    sources = [*ROOT.glob('adapters/decision/*.go'),
               *ROOT.glob('adapters/protectedstore/*.go'),
               *ROOT.glob('adapters/protectedstore/*.json'),
               *ROOT.glob('evaluation/holdout/jev/*.go'),
               *ROOT.glob('internal/canonical/*.go'),
               ROOT/'tests/jev/w1102_probe/main.go', Path(__file__),
               ROOT/'go.mod', ROOT/'go.sum',
               ROOT/'execution/verifier/W11/frozen-live-ac9d6153/aggregate.stdout.json',
               *ROOT.glob('execution/v2.4/receipts/W11/W11-02/imported-service-readiness-20261005T195606Z/*')]
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in sources}
    env = {k: v for k, v in os.environ.items() if 'JEV' not in k.upper() and 'TYPESAFE' not in k.upper()}
    env.update(GOTOOLCHAIN='local', GOENV='off')
    commands = []

    def run(name, argv, timeout):
        started = dt.datetime.now(dt.timezone.utc).isoformat()
        try:
            result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, timeout=timeout)
            stdout, stderr, code = result.stdout, result.stderr, result.returncode
        except subprocess.TimeoutExpired as exc:
            stdout, stderr, code = exc.stdout or b'', exc.stderr or b'', 124
        (out/(name+'.stdout.log')).write_bytes(stdout)
        (out/(name+'.stderr.log')).write_bytes(stderr)
        commands.append(dict(name=name, argv=argv, cwd=str(ROOT), started_at=started,
                             exit_code=code, stdout_sha256=digest(out/(name+'.stdout.log')),
                             stderr_sha256=digest(out/(name+'.stderr.log'))))
        return code, stdout

    save(out/'before.json', dict(task_id='W11', check_id='W11-02',
        started_at=dt.datetime.now(dt.timezone.utc).isoformat(), source_hashes=hashes,
        source_revision=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
        source_dirty_status=subprocess.check_output(['git','status','--porcelain'], cwd=ROOT, text=True).splitlines(),
        expected_assertion_ids=sorted(EXPECTED), new_provider_calls=0,
        independent_acceptance='PENDING_INDEPENDENT_REVIEW'))
    code, version = run('go-version', [str(go), 'version'], 15)
    if code or version.decode().strip() != 'go version go1.27.1 windows/amd64':
        save(out/'commands.json', commands)
        print('pinned Go version mismatch', file=sys.stderr)
        return 1
    code, raw = run('negative-fixture', [str(go),'test','./adapters/decision','-v','-count=1',
                                       '-timeout=60s','-run','^TestW1102QualificationAudit$'], 90)
    rows = []
    malformed = False
    for line in raw.decode('utf-8', errors='replace').splitlines():
        if line.startswith('W11_ASSERTION '):
            try:
                row = json.loads(line[len('W11_ASSERTION '):])
                if not all(k in row for k in ('assertion_id','expected','actual','status','evidence')):
                    malformed = True
                rows.append(row)
            except ValueError:
                malformed = True
    ids = [r.get('assertion_id') for r in rows]
    fixture_ok = (code == 0 and not malformed and len(ids) == len(EXPECTED) and
                  set(ids) == EXPECTED and all(r['expected'] == r['actual'] and
                  r['status'] == 'PASS' for r in rows))
    probe = None
    probe_ok = False
    if fixture_ok:
        probe_code, raw = run('read-only-probe', [str(go),'run','./tests/jev/w1102_probe'], 120)
        try:
            probe = json.loads(raw)
            probe_ok = (probe_code == 0 and probe['schema'] == 'researchos.w1102-readiness.v1'
                        and probe['new_provider_calls'] == 0 and probe['formal_label_body_accessed'] is False
                        and probe['automatic_authority'] == 'NONE' and probe['status'] == 'BLOCKED'
                        and len(probe['archive']['key_reports']) == 2 and len(probe['reuse_selection']) == 2)
        except (ValueError, KeyError, TypeError):
            probe_ok = False
    drift = [p for p, sha in hashes.items() if digest(ROOT/p) != sha]
    good = fixture_ok and probe_ok and not drift
    save(out/'commands.json', commands)
    save(out/'report.json', dict(task_id='W11', check_id='W11-02', status='BLOCKED' if good else 'FAIL',
        fixture_status='PASS' if fixture_ok else 'FAIL', assertions=rows, assertion_count=len(rows),
        expected_assertion_count=len(EXPECTED), malformed=malformed, source_drift=drift,
        resource_probe=probe, resource_probe_valid=probe_ok,
        measurement_modes=['FIXTURE','RECORDED_LIVE_WINDOWS_READINESS_NOT_NEW_MEASUREMENT'],
        real_qualification='BLOCKED', automatic_authority='NONE',
        blocked_resources=['OS_SERVICE_CONTROL_PERMISSION','authorized_provider_for_new_purpose_run','independent_labeled_cases_per_requested_key'],
        independent_acceptance='PENDING_INDEPENDENT_REVIEW', ended_at=dt.datetime.now(dt.timezone.utc).isoformat()))
    save(out/'evidence-index.json', {'files': [{'path':p.name,'sha256':digest(p)} for p in sorted(out.iterdir()) if p.is_file()]})
    print(json.dumps(dict(status='BLOCKED' if good else 'FAIL', fixture_status='PASS' if fixture_ok else 'FAIL',
        assertion_count=len(rows), receipt=str(out/'report.json')), ensure_ascii=False))
    return 2 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
