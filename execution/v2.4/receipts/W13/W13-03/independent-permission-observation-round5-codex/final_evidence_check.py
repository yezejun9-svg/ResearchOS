import datetime, hashlib, json, pathlib, runpy, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[6]
RAW = pathlib.Path(__file__).resolve().parent
RECEIPTS = ROOT / 'execution/v2.4/receipts/W13/W13-03'
checks = []

def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def ref(path):
    return {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path)}

def check(name, okay):
    checks.append({'id': name, 'pass': bool(okay)})
    if not okay:
        raise AssertionError(name)

head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
check('FROZEN_HEAD', head == '5e0b2eb9a08e21d2c67fcf7eac6006ccc616fcff')
namespace = runpy.run_path(str(ROOT/'tests/ui/w1303/check.py'), run_name='independent_final_source_read')
current = namespace['source_hashes']()
report_path = RECEIPTS/'registered-20261005T194002Z-f1118cda/report.json'
report = read(report_path)
check('SOURCE_FINGERPRINT_CURRENT_EXACT', current == report['source_hashes'])
check('SOURCE_DRIFT_EMPTY', report['source_drift'] == [])
check('CARD_REMAINS_PARTIAL_UNACCEPTED', report['status'] == 'PARTIAL' and report['card_accepted'] is False and report['formal_cases_accepted'] == [])
check('BLOCKERS_PRESERVED', {(b['gate'], b['status']) for b in report['blockers']} == {('SCREEN_READER','BLOCKED_OS_FOREGROUND'),('WORKSPACE_INDEPENDENT_REVIEW','BLOCKED_PLATFORM_POLICY')})
check('ZERO_PROVIDER_CALLS', report['provider_calls'] == 0)
verified_refs = []
stage_summaries = []
for stage in report['stages']:
    name = stage['stage']
    check(name+'_FRESH_PASS', stage['status'] == 'PASS' and stage['reused'] is False and stage['exit_code'] == 0)
    check(name+'_NONEMPTY_ALL_CHECKS_PASS', bool(stage['checks']) and all(c['status'] == 'PASS' for c in stage['checks']))
    for evidence in stage['evidence']:
        check(name+'_HASH_'+evidence['path'], sha(ROOT/evidence['path']) == evidence['sha256'])
        verified_refs.append(evidence)
    stage_summaries.append({'stage': name, 'status': stage['status'], 'reused': stage['reused'], 'checks': len(stage['checks'])})
check('SIX_FRESH_STAGES', len(stage_summaries) == 6)
check('632_PASS_ASSERTIONS', len(report['assertion_rows']) == 632 and all(row['status'] == 'PASS' for row in report['assertion_rows']))
for b in report['blockers']:
    check('BLOCKER_HASH_'+b['gate'], sha(ROOT/b['evidence']) == b['sha256'])

permission = []
for decision in ['allow_once','deny']:
    path = RECEIPTS/'permission-20261005T194132Z-7328d7a3'/decision/'permission.json'
    record = read(path)
    check(decision+'_CHECKS_PASS', record['status'] == 'PASS' and len(record['checks']) == 17 and all(c['status'] == 'PASS' for c in record['checks']))
    codes = [r.get('error_code') for r in record['closed_request_probe_replies']]
    check(decision+'_DIRECT_CLOSED_REJECTION', codes == ['STALE_REVISION'])
    for shot in record['screenshots']:
        check(decision+'_SCREENSHOT_HASH_'+shot['file'], sha(path.parent/shot['file']) == shot['sha256'])
        verified_refs.append(ref(path.parent/shot['file']))
    permission.append({'decision': record['decision'], 'evidence': ref(path), 'checks': len(record['checks']), 'run_state': record['run_before_file_assertion']['status'], 'replay_error_codes': codes, 'fallback_exercised_in_actual_gui': False})
check('DENY_CANCEL_REQUESTED_IS_NONTERMINAL_OBSERVATION', permission[1]['run_state'] == 'CANCEL_REQUESTED')

old_summaries = []
for name, expected_hash in [('registered-20261005T193205Z-1fc0aadf/report.json','2a28e2922ac1e04181a29cd3fdef0a161162c25ef53ca6347574c9ac37d5d8de'),('registered-20261005T193701Z-4e153612/report.json',None)]:
    path = RECEIPTS/name
    record = read(path)
    check('OLD_FAIL_PRESERVED_'+name, record['status'] == 'FAIL')
    if expected_hash:
        check('OLD_HASH_UNCHANGED_'+name, sha(path) == expected_hash)
    for stage in record['stages']:
        for evidence in stage['evidence']:
            check('OLD_RAW_HASH_'+evidence['path'], sha(ROOT/evidence['path']) == evidence['sha256'])
    old_summaries.append({'evidence':ref(path),'status':record['status'],'permission_checks':len(next(s for s in record['stages'] if s['stage']=='permission')['checks'])})

for name in ['cache-test-result.json','cache-input-expansion-result.json']:
    result = read(RAW/name)
    check(name+'_SOURCE_MATCH', result['checker_sha256'] == current['tests/ui/w1303/check.py'] and result['permission_driver_sha256'] == current['tests/ui/w1303/permission.cjs'])
probe = read(RAW/'permission-probe-unit-result.json')
check('SIMULATED_PROBE_SOURCE_MATCH', probe['driver_sha256'] == current['tests/ui/w1303/permission.cjs'])
check('CLOSURE_NO_SOURCE_DRIFT', namespace['source_hashes']() == current)
result = {'status':'PASS','head':head,'source_fingerprint':current,'report':ref(report_path),'stages':stage_summaries,'permission':permission,'old_failed_reports':old_summaries,'verified_evidence':verified_refs,'checks':checks,'check_count':len(checks),'reviewer_new_gui_runs':0,'reviewer_new_workspace_probes':0,'provider_calls':0,'finished_at':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(RAW/'final-evidence-check-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','checks':len(checks),'verified_evidence_refs':len(verified_refs),'final_report':ref(report_path),'source_inputs':len(current)},ensure_ascii=False))
