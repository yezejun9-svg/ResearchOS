"""Read frozen C20 source/registry and prior Jev logs; execute no tests."""
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
MAIN = '7e789b2'
AUTHOR = 'ee535ea913c9fd34675b1f268111674e75ab65a1'
RAW = 'fe52d68'

def git(commit,path):
    return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

checks = {}
def check(name,value):
    checks[name] = bool(value)

main = subprocess.check_output(['git','rev-parse',MAIN],cwd=ROOT).decode().strip()
paths = ['internal/domain/decision_c20_test.go','internal/domain/evolution_test.go','ops/ci/jev.py','tests/jev/expected.json','execution/commands.json','ops/ci/evolution.py','ops/ci/acceptance_audit.py','execution/receipts/W16/c20-formal/run.py']
sources = {p:sha(git(main,p)) for p in paths}
check('author_jev_source_equal_main',all(git(main,p)==git(AUTHOR,p) for p in paths[:4]))
check('registry_and_fixture_status_equal_reviewed_commit',all(git(main,p)==git('166b9e4',p) for p in ['execution/commands.json','ops/ci/evolution.py']))
check('acceptance_audit_equal_reviewed_commit',git(main,'ops/ci/acceptance_audit.py')==git('51eb8e8','ops/ci/acceptance_audit.py'))
check('formal_runner_equal_reviewed_commit',git(main,'execution/receipts/W16/c20-formal/run.py')==git('7954533','execution/receipts/W16/c20-formal/run.py'))
registry = json.loads(git(main,'execution/commands.json'))['commands']
keys = ['test.jev.fixture','test.evolution','acceptance.audit']
check('all_required_keys_bound_for_w16_c20',all(registry[k]['state']=='BOUND' and 'W16' in registry[k]['selectors']['task_id'] and 'C20' in registry[k]['selectors']['case_id'] for k in keys))
check('audit_requires_explicit_receipts',set(registry['acceptance.audit']['required_env'])=={'RESEARCHOS_C20_EVOLUTION_RECEIPT','RESEARCHOS_C20_JEV_RECEIPT'})
check('audit_registry_exact_selector',registry['acceptance.audit']['selectors']=={'task_id':['W16'],'check_id':[],'case_id':['C20']})
expected = json.loads(git(main,'tests/jev/expected.json'))['TestW11C20RubricOnly']
logs = []
for run in ['884115f2-7865-4912-bc01-fddf8076620f','0aede6d6-4773-4f35-a1d3-750c1e7bb82c']:
    prefix='execution/receipts/W16/c20-private/jev/'+run+'/'
    b=json.loads(git(RAW,prefix+'before.json'));r=json.loads(git(RAW,prefix+'report.json'))
    raw=git(RAW,prefix+'stdout.txt'); lines=raw.decode().splitlines()
    hashes={p:sha(git(RAW,prefix+p)) for p in ['before.json','report.json','stdout.txt','stderr.txt']}
    raw_match=all('sha256:'+hashes[p]==h for p,h in r['raw_evidence_hashes'].items())
    manifest_matches=all('sha256:'+sha(git(b['code_revision'],p))==h for p,h in b['version_manifest'].items())
    line_match=all(json.loads(lines[a['raw_evidence']['line']-1].split(' ',1)[1])=={k:v for k,v in a.items() if k!='raw_evidence'} for a in r['assertions'])
    check(run+':raw_hashes',raw_match)
    check(run+':source_manifest',manifest_matches)
    check(run+':assertion_lines',line_match)
    logs.append({'run':run,'source':b['code_revision'],'status':r['status'],'exit_code':r['exit_code'],'assertion_count':len(r['assertions']),'source_hash_count':len(b['version_manifest']),'raw_sha256':hashes,'dirty':b['dirty'],'test_run_count':sum(x.startswith('=== RUN   ') for x in lines),'test_pass_count':sum(x.startswith('--- PASS: ') for x in lines),'test_fail_count':sum(x.startswith('--- FAIL: ') for x in lines)})
    if r['status']=='PASS':
        check('successful_jev_exact_inventory',set(r['assertion_ids'])==set(expected) and len(r['assertion_ids'])==len(expected)==3)
        check('successful_source_dirty_only_raw_directory',b['dirty'].strip()=='?? execution/receipts/W16/c20-private/jev/')
check('failed_readiness_run_preserved',logs[0]['status']=='FAIL' and logs[0]['assertion_count']==0 and logs[0]['test_fail_count']==1)
check('successful_retry_has_one_real_test',logs[1]['status']=='PASS' and logs[1]['test_run_count']==logs[1]['test_pass_count']==1 and logs[1]['test_fail_count']==0)
result={'verdict':'PASS_READONLY_C20_SOURCE_AND_PRIOR_JEV_RAW' if all(checks.values()) else 'NEEDS_REVIEW','main_commit':main,'author_source':AUTHOR,'raw_commit':subprocess.check_output(['git','rev-parse',RAW],cwd=ROOT).decode().strip(),'checks':checks,'source_sha256':sources,'prior_runs':logs,'new_tests_executed':False,'formal_C20':'PENDING_SAME_HEAD_THREE_COMMAND_EXECUTION_AND_INDEPENDENT_REVIEW'}
(OUT/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'verdict':result['verdict'],'checks':len(checks),'failed':[k for k,v in checks.items() if not v],'main':main}))
