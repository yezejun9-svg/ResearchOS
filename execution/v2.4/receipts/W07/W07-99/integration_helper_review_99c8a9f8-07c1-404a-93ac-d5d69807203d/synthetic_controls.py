"""Independent helper controls. SYNTHETIC ONLY; never invoke register/main."""
import hashlib
import json
import os
from pathlib import Path
import types

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
CANDIDATE = REPO / '.local/worktrees/codex-w0599-command-queue/execution/v2.4/receipts/W05/W05-99/historical_fixture_executor_codex/w07-root-registration-candidate-a0c4f30a-50d2-42d5-924b-24131c5763e7/issue_reviewed_current.py'
EXPECTED = 'b65d2a363c513e0bbdec8659f96a0f19f3fe140a39d28f39e5590170b62bb250'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def must(v, message):
    if not v: raise AssertionError(message)
raw = CANDIDATE.read_bytes()
must(hashlib.sha256(raw).hexdigest() == EXPECTED, 'candidate hash')
m = types.ModuleType('synthetic_only_reviewed_helper')
m.__file__ = str(CANDIDATE)
exec(compile(raw, str(CANDIDATE), 'exec'), m.__dict__)
main_before = {p: sha(REPO / p) for p in m.CANONICAL}
results = []
def check(name, fn):
    detail = fn()
    results.append({'control': name, 'result': 'PASS', 'detail': detail})
    print(json.dumps(results[-1], ensure_ascii=False), flush=True)
def refusal(fn, code):
    try: fn()
    except Exception as exc:
        must(code in str(exc), str(exc))
        return {'exception': type(exc).__name__, 'error': str(exc)}
    raise AssertionError('missing refusal ' + code)
def fixture(name):
    repo = HERE / 'SYNTHETIC_NOT_PRODUCT' / name
    repo.mkdir(parents=True)
    out = repo / 'synthetic-transaction'
    entries = []
    for n, relative in enumerate(m.CANONICAL):
        path = repo / relative
        original = m.encoded({'SYNTHETIC': True, 'generation': 'original', 'file': n, 'history': ['old'], 'failures': 116})
        desired = m.encoded({'SYNTHETIC': True, 'generation': 'desired', 'file': n, 'history': ['old', 'new'], 'failures': 116})
        m.immutable_bytes(path, original)
        op = out / 'canonical-bytes' / (str(n) + '.original')
        dp = out / 'canonical-bytes' / (str(n) + '.desired')
        m.immutable_bytes(op, original); m.immutable_bytes(dp, desired)
        entries.append({'path': relative, 'original_sha256': m.digest(original), 'desired_sha256': m.digest(desired), 'original_ref': m.ref(repo, op), 'desired_ref': m.ref(repo, dp)})
    journal = {'schema': 'researchos.root-registration-pending.v1', 'actor': m.ACTOR, 'project_id': m.PROJECT_ID, 'repo': str(repo), 'status': 'PENDING_NOT_ACCEPTED', 'files': entries}
    m.save(out / 'pending-journal.json', journal)
    return repo, out, journal
def put_desired(repo, out, journal, indices):
    for n in indices:
        e = journal['files'][n]
        m.cas_replace(repo / e['path'], e['original_sha256'], (repo / e['desired_ref']['path']).read_bytes(), out)
def recover_control():
    details = []
    for count in range(4):
        repo, out, j = fixture('crash-after-' + str(count))
        put_desired(repo, out, j, range(count))
        before_journal = sha(out / 'pending-journal.json')
        r = m.recover_files(repo, out, j, {'SYNTHETIC': True})
        must(r['status'] == 'RESTORED_ORIGINAL', r)
        must(sha(out / 'pending-journal.json') == before_journal, 'journal changed')
        must(all(sha(repo / e['path']) == e['original_sha256'] for e in j['files']), 'raw restore')
        details.append({'after_writes': count, 'status': r['status'], 'actions': [x['action'] for x in r['files']]})
    return details
check('strict_duplicate_json', lambda: refusal(lambda: m.strict('{"a":1,"a":2}'), 'DUPLICATE_JSON_KEY'))
check('strict_nan', lambda: refusal(lambda: m.strict('{"a":NaN}'), 'NONFINITE_JSON'))
check('strict_overflow', lambda: refusal(lambda: m.strict('{"a":1e999}'), 'NONFINITE_JSON'))
check('partial_0_1_2_3_writes_exact_restore', recover_control)
def stale():
    repo, out, j = fixture('stale-cas')
    e = j['files'][0]; p = repo / e['path']
    foreign = m.encoded({'SYNTHETIC': True, 'foreign': True})
    p.write_bytes(foreign)
    r = refusal(lambda: m.cas_replace(p, e['original_sha256'], b'{}', out), 'CANONICAL_CAS')
    must(p.read_bytes() == foreign, 'foreign clobbered')
    return r
check('stale_CAS_preserves_foreign_bytes', stale)
def foreign_recovery():
    repo, out, j = fixture('foreign-during-recovery'); put_desired(repo, out, j, range(3))
    p = repo / j['files'][1]['path']; foreign = b'{"SYNTHETIC":"foreign"}\n'; p.write_bytes(foreign)
    r = m.recover_files(repo, out, j, {'SYNTHETIC': True})
    must(r['status'] == 'PARTIAL_REGISTRATION' and p.read_bytes() == foreign, r)
    must(r['files'][1]['action'] == 'FOREIGN_CHANGE_NOT_TOUCHED', r)
    must(all(sha(repo / j['files'][i]['path']) == j['files'][i]['original_sha256'] for i in (0,2)), 'other own writes not restored')
    return r
check('foreign_change_partial_recovery', foreign_recovery)
def missing():
    repo, out, j = fixture('missing-target'); put_desired(repo, out, j, (0,1))
    p = repo / j['files'][0]['path']; p.unlink()
    r = m.recover_files(repo, out, j, {'SYNTHETIC': True})
    must(r['status'] == 'PARTIAL_REGISTRATION' and not p.exists(), r)
    return r
check('missing_target_not_recreated', missing)
def corrupt():
    repo, out, j = fixture('corrupt-archive'); put_desired(repo, out, j, range(3))
    before = m.observed_canonical(repo)
    (repo / j['files'][0]['original_ref']['path']).write_bytes(b'{"SYNTHETIC":"tamper"}')
    r = refusal(lambda: m.recover_files(repo, out, j, {'SYNTHETIC': True}), 'JOURNAL_BACKUP_HASH')
    must(m.observed_canonical(repo) == before, 'writes before journal validated')
    return r
check('corrupt_archive_no_recovery_writes', corrupt)
def replace_failure():
    repo, out, j = fixture('os-replace-refusal'); put_desired(repo, out, j, range(3))
    before = m.observed_canonical(repo)
    real_replace = os.replace
    def fail(*args, **kwargs): raise PermissionError('SYNTHETIC injected replace refusal')
    try:
        os.replace = fail
        r = m.recover_files(repo, out, j, {'SYNTHETIC': True})
    finally: os.replace = real_replace
    must(r['status'] == 'PARTIAL_REGISTRATION' and all(x['action']=='RECOVERY_FAILED' for x in r['files']), r)
    must(m.observed_canonical(repo) == before, 'replacement failure changed target')
    return {'status': r['status'], 'actions': [x['action'] for x in r['files']]}
check('replacement_failure_remains_partial', replace_failure)
def completed():
    repo, out, j = fixture('completed-guard'); put_desired(repo, out, j, range(3))
    marker = out / 'completion-marker-bytes.json'; m.save(marker, {'SYNTHETIC': True})
    os.link(marker, out / 'completed.json')
    before = m.observed_canonical(repo)
    r = refusal(lambda: m.recover_files(repo, out, j, {'SYNTHETIC': True}), 'ALREADY_COMPLETED')
    must(m.observed_canonical(repo) == before, 'completed rollback')
    try: os.link(marker, out / 'completed.json')
    except FileExistsError: pass
    else: raise AssertionError('completion marker replaced')
    must(sha(marker) == sha(out / 'completed.json'), 'marker bytes changed')
    return r
check('completed_marker_no_overwrite_no_rollback', completed)
def origin():
    repo, out, j = fixture('failure-origin')
    p = m.error_origin(out, 'SYNTHETIC', RuntimeError('SYNTHETIC failure'), 'SYNTHETIC trace', 'SYNTHETIC')
    h = sha(p)
    r = m.recover_files(repo, out, j, m.ref(repo, p))
    must(sha(p) == h and r['failure_origin_ref']['sha256'] == h, 'origin lost')
    v = m.strict(p.read_bytes()); must(v['counter_reset'] is False and 'append' in v['counter_recording'], 'counter semantics')
    try: m.save(p, {})
    except FileExistsError: pass
    else: raise AssertionError('immutable receipt overwritten')
    return {'origin_sha256': h, 'status': r['status'], 'counter_reset': False}
check('immutable_failure_origin_and_reconciliation', origin)
main_after = {p: sha(REPO / p) for p in m.CANONICAL}
must(main_before == main_after, 'actual main canonical drift during synthetic controls')
must(sha(CANDIDATE) == EXPECTED, 'candidate drift')
result = {'schema':'researchos.independent-synthetic-helper-controls.v1','classification':'SYNTHETIC_NOT_PRODUCT_NOT_ACCEPTANCE','source_sha256':EXPECTED,'status':'PASS','controls':results,'count':len(results),'real_canonical_before':main_before,'real_canonical_after':main_after,'actual_register_or_main_called':False}
with (HERE / 'controls-result.json').open('x', encoding='utf-8') as f: json.dump(result, f, ensure_ascii=False, indent=2); f.write('\n')
print(json.dumps({'status':'PASS','control_count':len(results),'result_sha256':sha(HERE / 'controls-result.json')}))
