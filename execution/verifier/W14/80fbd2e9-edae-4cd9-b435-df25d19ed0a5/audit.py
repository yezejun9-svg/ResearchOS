"""Public evidence audit only; does not rerun the product or external providers."""
from pathlib import Path
import hashlib,json,subprocess
from datetime import datetime,timezone
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[3]
BASE=ROOT/'execution/receipts/W14'/OUT.name
PRIOR=ROOT/'execution/verifier/W14/fixture-f84f17a'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def canonical(v):
    def validate(x):
        assert not isinstance(x,float), 'float requires full JCS'
        if isinstance(x,int):assert abs(x)<=9007199254740991
        if isinstance(x,dict):
            assert all(all(ord(c)<65536 for c in k) for k in x)
            for y in x.values():validate(y)
        if isinstance(x,list):
            for y in x:validate(y)
    validate(v)
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def jhash(v):return 'sha256:'+hashlib.sha256(canonical(v)).hexdigest()
hashes={}
def check(p,h):
    p=Path(p).resolve();assert p.is_relative_to(ROOT)
    got=sha(p);assert got==h.removeprefix('sha256:'),str(p)
    hashes[str(p.relative_to(ROOT)).replace('\\','/')]=got
r=read(BASE/'receipt.json');manifest=read(BASE/'artifacts.json');env=read(BASE/'environment-before.json')
assert r['receipt_hash']=='sha256:be5ad39e567eef5af12f2b6a2911b563470fa45bf6b9be001fb2f3e8b0ab3b40'
assert r['receipt_hash']==jhash({k:v for k,v in r.items() if k!='receipt_hash'})
check(BASE/'artifacts.json',r['artifact_manifest_hash'])
assert len(manifest['files'])==len({x['path'] for x in manifest['files']})==44
for item in manifest['files']:check(ROOT/item['path'],item['sha256'])
assert len(env['source_sha256'])==261
current_drift=[]
for name,h in env['source_sha256'].items():
    raw=subprocess.run(['git','show',r['code_revision']+':'+name],cwd=ROOT,check=True,capture_output=True).stdout
    assert hashlib.sha256(raw).hexdigest()==h,name
    if sha(ROOT/name)!=h:current_drift.append(name)
assert len(r['verification_results'])==1
c=r['verification_results'][0];inv=read(ROOT/c['actual_invocation_reference'])
assert inv['selectors']=={'task_id':'W14','check_id':'W14-G01','case_id':''}
assert c['mode']=='FIXTURE' and inv['code_revision']==r['code_revision']
assert c['status']==c['actual_dispatch_status']==inv['status']=='PASS'
assert c['exit_code']==inv['exit_code']==0
for k in ['command_key','registered_command_revision','started_at','ended_at']:assert c[k]==inv[k]
for k in ['stdout','stderr']:check(ROOT/inv[k]['path'],inv[k]['sha256'])
stdout=read(ROOT/inv['stdout']['path']);p=Path(stdout['receipt']).parent;report=read(p/'report.json')
assert report['scope']=='FIXTURE_SYNTHETIC' and report['status']=='PASS'
assert report['head']==r['code_revision'] and report['temporary_database_removed']
for name,h in report['files'].items():check(p/name,h)
contract=read(ROOT/'evaluation/project_cycle/fixture_contract.json')
check(ROOT/'evaluation/project_cycle/fixture_contract.json',report['fixture_contract_sha256'])
rows=[];phases={}
for phase in ['vertical','resume','missing-source']:
    chunk=[json.loads(x) for x in (p/(phase+'.jsonl')).read_text('utf-8').splitlines()]
    rows+=chunk;phases[phase]=chunk
assertions=[x for x in rows if x['record_type']=='assertion'];byid={x['assertion_id']:x for x in assertions}
assert len(assertions)==len(byid)==32
assert set(byid)==set(contract['required_assertions'])==set(inv['assertion_ids'])==set(c['assertion_ids'])
assert all(x['actual']==x['expected'] and x['status']=='PASS' and x['scope']=='FIXTURE_SYNTHETIC' for x in assertions)
assert {x['assertion_id']:x for x in report['assertions']}==byid
http=[x for x in rows if x['record_type']=='http'];assert len(http)==report['http_count']==96
assert sum(400<=x['status']<500 for x in http)==report['rejected_http_count']==7
checkpoint=read(p/'checkpoint.json');resume_hashes=[]
for name in ['STATE','GOAL','PROGRESS','CYCLE','RELEASE','NOTIFICATIONS']:
    row=byid['W14-NEW-SESSION-'+name+'_HASH']
    assert jhash(row['evidence'])==row['actual']==checkpoint[name.lower()+'_hash']
    resume_hashes.append(name)
pids={phase:next(x['pid'] for x in chunk if x['record_type']=='transport') for phase,chunk in phases.items()}
assert len(set(pids.values()))==3 and pids['vertical']==checkpoint['first_process_pid']
nextstep=byid['W14-NEW-SESSION-NEXT-STEP']['evidence'];assert nextstep['pid']==pids['resume'] and nextstep['prior_pid']==pids['vertical']
assert nextstep['background_resupplied']==0 and nextstep['follow_up']['status']=='DRAFT'
assert byid['W14-NEW-SESSION-GOAL_HASH']['evidence']['status']=='ACTIVE'
acceptance=byid['W14-INDEPENDENT-SERVICE-ACCEPTANCE']['evidence']
assert acceptance['receipt_hash']==jhash({k:v for k,v in acceptance.items() if k!='receipt_hash'})
assert acceptance['verifier_principal_id'] not in acceptance['executor_principal_ids']
assert acceptance['measurement_mode']=='FIXTURE' and acceptance['independence_basis']=='DETERMINISTIC_SERVICE'
assert acceptance['id']==checkpoint['acceptance_id']
experiment=byid['W14-LEGAL-NO-IMPROVEMENT']['evidence'];assert experiment['status']=='COMPLETED' and experiment['outcome']=='NO_IMPROVEMENT'
assert experiment['acceptance_id']==acceptance['id']
assert byid['W14-NEGATIVE-CYCLE-COMPLETE']['actual']=='COMPLETE'
assert byid['W14-MISSING-SOURCE-HONEST-PARTIAL']['actual']=='PARTIAL'

prior=read(PRIOR/'review.json');index=read(PRIOR/'evidence-index.json')
assert prior['verdict']=='PASS_IN_SCOPE' and prior['scope']=='FIXTURE_SYNTHETIC_ONLY'
assert len(index['files'])==25
for item in index['files']:
    check(PRIOR/item['path'],item['sha256']);assert (PRIOR/item['path']).stat().st_size==item['bytes']
prior_checks=read(PRIOR/'independent-checks.json')
assert len(prior_checks)==434 and all(x['status']=='PASS' for x in prior_checks)
source_diff=subprocess.run(['git','diff',prior['source_commit'],r['code_revision'],'--','tests/e2e_cycle/_fixture/cycle_test.go','evaluation/project_cycle/fixture_contract.json'],cwd=ROOT,check=True,capture_output=True).stdout
assert source_diff==b''
selector_diff=subprocess.run(['git','diff',prior['source_commit'],r['code_revision'],'--','tests/e2e_cycle/run_fixture.py'],cwd=ROOT,check=True,capture_output=True).stdout.decode()
(OUT/'runner-integration.diff').write_text(selector_diff,encoding='utf-8')
result={'status':'PASS','reviewed_at':datetime.now(timezone.utc).isoformat(),'executor_receipt_jcs_hash':r['receipt_hash'],
 'manifest_files_verified':44,'frozen_source_hashes_verified':261,'current_source_drift':current_drift,
 'assertions':32,'product_http_requests':96,'http_negative_responses':7,'additional_trusted_service_rejection':1,
 'phase_pids':pids,'resume_object_hashes_recomputed':resume_hashes,'independent_acceptance_receipt_jcs':acceptance['receipt_hash'],
 'previous_independent_index_files_verified':25,'previous_independent_audit_checks':434,
 'fixture_source_and_contract_changed_since_independent_rerun':False,
 'integration_delta':'Runner gains strictG01 selector and stdout assertion IDs/receipt path; W17 auth and migration integration is exercised by current32-assertion product flow but is not security-qualified here.',
 'new_product_or_provider_runs':0,'stage_accepted':False,'owned_A13_accepted':False,'hashes':hashes}
(OUT/'audit-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='hashes'},ensure_ascii=False))
