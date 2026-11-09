from pathlib import Path
import hashlib,json,re,sys

def audit(event,args):
    if event.startswith(('subprocess.','socket.')) or event in {'os.system','os.fork','os.posix_spawn','os.spawn'}:
        raise RuntimeError('READBACK_FORBIDS_PROCESS_OR_NETWORK:'+event)
sys.addaudithook(audit)
OUT=Path(__file__).parent
REPORT=OUT/'source-review.json'
EXPECTED='e85f39c0ba2fae6cf7d068f893635b6fa836cd7db1f4312720dd16ba48665103'
memo={};checks=[]
def observed(path):
    path=Path(path)
    key=str(path)
    if key not in memo:
        b=path.read_bytes()
        memo[key]=dict(path=key,sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
    return memo[key]
def verify(path,expected,expected_bytes=None,kind='declared evidence'):
    value=observed(path)
    row=dict(value,expected=expected,kind=kind,match=value['sha256']==expected and (expected_bytes is None or value['bytes']==expected_bytes))
    assert row['match'],str(path)
    checks.append(row)
    return value
def readj(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
verify(REPORT,EXPECTED,24477,'immutable final report')
r=readj(REPORT)
assert r['decision']=='APPROVE_CLIENT_WIRING_ONLY_NOT_NATIVE_OR_W14_ACCEPTANCE'
assert r['formal_increment']==0 and r['pending_blockers']==[] and len(r['source_sha256'])==8
assert not r['native_execution_authorized'] and not r['formal_pass_issued']
for name,entry in r['artifacts'].items():verify(entry['path'],entry['sha256'],entry['bytes'],'report artifact:'+name)
for name in ('author_manifest_final','author_manifest_final_D','original_freeze02_manifest','rejected_v1_report'):
    entry=r[name];verify(entry['path'],entry['sha256'],entry['bytes'],name)
for name in ('pin-verification.json','post-review-pin-verification.json'):
    data=readj(OUT/name)
    for entry in data['rows']:
        verify(entry['path'],entry['expected'],entry['bytes'],'previous pin record:'+name)
    if name=='pin-verification.json':
        for entry in data['node_staging']:
            verify(OUT/'isolated-frozen-node'/entry['path'],entry['sha256'],kind='isolated frozen Node dependency')
go=readj(OUT/'go-independent-checks.json')
assert go['test_exit']==0 and go['vet_exit']==0
go_log=(OUT/'go-independent-tests.log').read_text(encoding='utf-8-sig')
run_names=re.findall(r'^=== RUN   (.+)$',go_log,re.M)
assert len(run_names)==47 and sum('/' not in name for name in run_names)==7
assert len(re.findall(r'^\s*--- PASS:',go_log,re.M))==47
assert not re.search(r'^\s*--- FAIL:|^FAIL(?:\s|$)',go_log,re.M)
node=readj(OUT/'node-independent-checks.json')
assert node['checks']==54 and node['passed']==54 and node['failed']==0 and all(x['passed'] for x in node['results'])
author_node=readj(OUT/'node-author-fixture.log')
assert author_node['status']=='PASS' and author_node['checks']==29
raw={
    'Go47':dict(observed(OUT/'go-independent-tests.log'),exit_code=0,terminal='8588f9',top_tests=7,subcases=40),
    'vet':dict(observed(OUT/'go-independent-vet.log'),exit_code=0,terminal='8588f9'),
    'Node54_log':dict(observed(OUT/'node-independent.log'),exit_code=0,terminal='28ac1c'),
    'Node54_results':dict(observed(OUT/'node-independent-checks.json'),checks=54,passed=54,failed=0),
    'author_Node29_independent_rerun':dict(observed(OUT/'node-author-fixture.log'),exit_code=0,terminal='f2b3f7',checks=29),
}
result=dict(schema='researchos.client-review-post-freeze-readback/1',
    status='ALL_DECLARED_IMMUTABLE_EVIDENCE_MATCHED',readback_verified=True,
    report=observed(REPORT),decision=r['decision'],formal_increment=0,pending_blockers=[],
    checks=len(checks),unique_files_hashed=len(memo),rows=checks,
    source_sha256=r['source_sha256'],unchanged_source_sha256=r['unchanged_source_sha256'],
    raw_test_evidence=raw,tests_rerun=False,freeze_rerun=False,
    real_native=0,real_HTTP=0,model=0,old_DB_access=0,old_probe_replay=0,
    archive_root=str(OUT),required_subdirectories=['isolated-frozen-node/apps/desktop/main/lib','isolated-frozen-node/tests/ui'],
    archive_exclusions=['tmp (disposable compiler temporary directory, if present)'],
    archive_note='Keep all review02 root evidence files plus the two explicit isolated-frozen-node subtrees. Existing review01 and author freeze01/freeze02 archives remain immutable.')
target=OUT/'post-freeze-readback.json'
with target.open('x',encoding='utf-8',newline='') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(dict(status=result['status'],checks=len(checks),unique_files_hashed=len(memo),readback=observed(target),raw_test_evidence=raw),ensure_ascii=True))
