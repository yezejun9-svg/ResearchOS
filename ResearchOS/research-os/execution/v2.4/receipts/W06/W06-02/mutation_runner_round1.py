"""W06-02 falsifiability matrix, round 1: neutralise each guard this card delivers and see which named id goes red.

Selection: the 22 W06-02-* rows the card emits (driven through internal/domain/session_w0602_test.go, which is what
the registered check phase reports). A guard whose neutralisation reddens no row is reported as survived with the
construction it would need, never as caught. session_service.go is restored byte-exact in a finally and the restore
is re-verified by digest, then the suite is re-run to prove nothing was left mutated.

usage: python .local/w0602_mutation_round1.py
"""
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path('.')
SRC = REPO / 'internal/domain/session_service.go'
GO = json.loads(Path('execution/toolchains/locked.json').read_text(encoding='utf-8'))['tools']['go']['path']
OUT = REPO / 'execution/v2.4/receipts/W06/W06-02/mutation_selfcheck_round2.json'
original = SRC.read_bytes()
BEFORE_DIGEST = hashlib.sha256(original).hexdigest()
text = original.decode('utf-8')

MUT = [
    ('M1-ignore-live-run-gate',
     'blocked := runID != "" && liveRunStatuses[status] && !settled',
     'blocked := false'),
    ('M2-drop-stale-epoch-check',
     '\tif cur, _ := sess["writer_epoch"].(int64); cur != epoch {',
     '\tif false {'),
    ('M3-drop-writer-attribution-check',
     '\tif owner, _ := sess["writer_client_id"].(string); owner != clientID {',
     '\tif false {'),
    ('M4-drop-request-hash-comparison',
     '\t\tif storedHash.String != hash {',
     '\t\tif false {'),
    ('M5-drop-watermark-ahead-refusal',
     '\tif after > head {',
     '\t\tif false {'),
    ('M6-never-report-truncation',
     '\ttruncated := missed > 0',
     '\ttruncated := false'),
    ('M7-drop-sealed-session-gate',
     '\tif sealed(sess) {\n\t\treturn nil, Fail(409, "SESSION_SEALED", "a sealed session cannot take a new writer")',
     '\tif false {\n\t\treturn nil, Fail(409, "SESSION_SEALED", "unreachable")'),
    ('M8-drop-grant-check-on-attach',
     '\tif !p.Allowed(project, "", "", false) {\n\t\treturn nil, Fail(403, "FORBIDDEN", "current principal has no grant on this project")\n\t}\n\tif in.SessionID == ""',
     '\tif false {\n\t\treturn nil, Fail(403, "FORBIDDEN", "unreachable")\n\t}\n\tif in.SessionID == ""'),
]
CARD_IDS = sorted(json.loads((REPO / 'execution/v2.4/receipts/W06/W06-02/mutation_roster.json').read_text(
    encoding='utf-8'))['ids']) if (REPO / 'execution/v2.4/receipts/W06/W06-02/mutation_roster.json').is_file() else []


def run_suite():
    # GOPATH/GOCACHE must be absolute: the first version of this runner passed '.local\gopath' and every go test
    # invocation exited 2 with no rows, which the classifier then reported as "crashed mutant" for all eight
    # mutations. The paths are taken from the registry entry that already runs this package.
    import os
    locked = json.loads(Path('execution/v2.4/commands.json').read_text(encoding='utf-8'))
    fixed = locked['commands']['test.context']['fixed_env']
    env = {k: v for k, v in os.environ.items()}
    env.update({'GOTOOLCHAIN': 'local', 'GOENV': 'off',
                'GOPATH': fixed['GOPATH'], 'GOCACHE': fixed['GOCACHE'], 'RESEARCHOS_GO': GO})
    p = subprocess.run([GO, 'test', './internal/domain', '-run', '^TestW0602SessionSingleWriterHandoff$',
                        '-v', '-count=1', '-timeout', '8m'], capture_output=True, cwd=str(REPO), env=env, timeout=900)
    rows, compile_error = [], None
    for line in (p.stdout or b'').decode('utf-8', 'replace').splitlines():
        if line.startswith('W06_ASSERTION '):
            try:
                rows.append(json.loads(line[14:]))
            except ValueError:
                pass
    if not rows:
        compile_error = (((p.stderr or b'').decode('utf-8', 'replace') or '') + ((p.stdout or b'').decode('utf-8', 'replace') or ''))[:400]
    return p.returncode, rows, compile_error


results = []
try:
    base_rc, base_rows, base_err = run_suite()
    assert base_rows, 'the baseline itself emitted no rows (' + str(base_err) + '); a matrix measured against an empty ' \
                      'baseline would classify every mutant as crashed and is not evidence, so this run aborts'
    assert base_rc == 0, 'baseline did not pass: exit ' + str(base_rc)
    base_ids = {r['assertion_id'] for r in base_rows if r['status'] == 'PASS'}
    print(json.dumps({'baseline_exit': base_rc, 'rows': len(base_rows), 'pass': len(base_ids),
                      'compile_error': base_err}, ensure_ascii=False), flush=True)
    for name, anchor, replacement in MUT:
        occurrences = text.count(anchor)
        entry = {'mutation': name, 'anchor': anchor.strip()[:120], 'anchor_occurrences': occurrences}
        if occurrences != 1:
            entry.update({'classification': 'anchor-missing',
                          'detail': 'the anchor is not unique, so no edit was attempted rather than editing the '
                                    'wrong clause'})
            results.append(entry)
            continue
        SRC.write_bytes(text.replace(anchor, replacement, 1).encode('utf-8'))
        try:
            rc, rows, cerr = run_suite()
        except Exception as e:
            rows, rc, cerr = [], 'timeout', str(e)[:300]
        red = sorted({r['assertion_id'] for r in rows if r['status'] != 'PASS'} - (set() if not rows else set()))
        emitted = {r['assertion_id'] for r in rows if r['status'] == 'PASS'}
        lost = sorted(base_ids - emitted)
        entry.update({'exit_code': rc, 'rows_emitted': len(rows), 'passing_card_rows': len(emitted),
                      'card_rows_red': lost, 'compile_error': cerr})
        if cerr:
            entry['classification'] = 'crashed-mutant-ill-formed'
        elif lost:
            entry['classification'] = 'caught-by-card-id'
            entry['first_card_red'] = lost[0]
        elif rc == 0 and len(rows) == len(base_rows):
            entry['classification'] = 'survived'
        else:
            entry['classification'] = 'survived'
            entry['detail'] = 'no card row went red; the mutant stayed green'
        results.append(entry)
        print(json.dumps({k: entry[k] for k in ('mutation', 'classification') if k in entry}, ensure_ascii=False),
              flush=True)
        SRC.write_bytes(original)
        assert hashlib.sha256(SRC.read_bytes()).hexdigest() == BEFORE_DIGEST, 'restore failed mid-run'
finally:
    SRC.write_bytes(original)
    restored = hashlib.sha256(SRC.read_bytes()).hexdigest()
post_rc, post_rows, _ = run_suite()
totals = {'mutations': len(results),
          'caught_by_card_id': sum(1 for r in results if r['classification'] == 'caught-by-card-id'),
          'survived': sum(1 for r in results if r['classification'] == 'survived'),
          'crashed': sum(1 for r in results if r['classification'] == 'crashed-mutant-ill-formed'),
          'anchor_missing': sum(1 for r in results if r['classification'] == 'anchor-missing')}
report = {
    'card': 'W06-02', 'round': 1, 'at': datetime.now(timezone.utc).isoformat(),
    'executor': 'qoder-desktop:/root/construction',
    'why': 'the card\'s checks must be shown capable of failing for the reason they state; a guard that no mutation '
           'can redden is either unreachable or unasserted, and that has to be named rather than assumed',
    'selection': {'driver': 'go test ./internal/domain -run ^TestW0602SessionSingleWriterHandoff$',
                  'card_rows': len(base_ids)},
    'baseline': {'exit_code': base_rc, 'rows': len(base_rows), 'pass': len(base_ids)},
    'totals': totals, 'results': results,
    'survivors_and_reasons': [r for r in results if r['classification'] != 'caught-by-card-id'],
    'restore_verification': {'expected_sha256': BEFORE_DIGEST, 'sha256_after': restored,
                             'restored_byte_exact': restored == BEFORE_DIGEST},
    'post_restore_rerun': {'exit_code': post_rc, 'rows': len(post_rows),
                           'non_pass': [r['assertion_id'] for r in post_rows if r['status'] != 'PASS']},
    'note': 'Executor-run self-check, not independent review. A survival is reported as a survival.',
}
OUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
print(json.dumps({'totals': totals, 'out': str(OUT).replace('\\', '/'),
                  'restore_ok': report['restore_verification']['restored_byte_exact'],
                  'post': post_rc, 'survivors': [r['mutation'] for r in report['survivors_and_reasons']]},
                 ensure_ascii=False))
