"""Independent frozen C20 package audit. Read-only; no test/native execution."""
import base64
import hashlib
import io
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
RUN = '5402da3d-e835-42d6-8b5f-168b941158dc'
PREFIX = 'execution/receipts/W16/'+RUN+'/'
SOURCE = '7e789b291814828556edd0a1e722d1992205b9f4'
ARCHIVE = '891fa45'
checks = []

def check(value,name):
    if not value:
        raise AssertionError(name)
    checks.append(name)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canon(v):
    def inspect(x):
        if isinstance(x,float):
            raise ValueError('native JCS required for floats')
        if isinstance(x,dict):
            for k,v in x.items():
                if any(ord(c)>65535 for c in k):
                    raise ValueError('native JCS required for non-BMP keys')
                inspect(v)
        if isinstance(x,list):
            for v in x:inspect(v)
    inspect(v)
    return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def seal(v):
    return 'sha256:'+sha(canon({k:w for k,w in v.items() if k!='receipt_hash'}))

def blobs(commit,names):
    names=list(dict.fromkeys(names))
    result=subprocess.check_output(['git','cat-file','--batch'],input=''.join(commit+':'+p.replace('\\','/')+'\n' for p in names).encode(),cwd=ROOT)
    stream=io.BytesIO(result); values={}
    for name in names:
        header=stream.readline().split()
        check(len(header)==3 and header[1]==b'blob','frozen-blob:'+name)
        values[name]=stream.read(int(header[2]))
        check(stream.read(1)==b'\n','blob-framing:'+name)
    return values

raw=blobs(ARCHIVE,[PREFIX+n for n in ['receipt.json','artifacts.json','environment-before.json','C20.json','executor-plan.json','dispatcher-results.json']])
def load(path):return json.loads(raw[path])
receipt=load(PREFIX+'receipt.json');manifest=load(PREFIX+'artifacts.json');env=load(PREFIX+'environment-before.json');case=load(PREFIX+'C20.json')
check(receipt['receipt_hash']==seal(receipt)=='sha256:251e1744e1dea003985d00766acfc9a663c93433201faee734c69c3069013ec4','canonical-executor-receipt')
check(receipt['code_revision']==SOURCE and receipt['run_id']==RUN and receipt['task_id']=='W16','executor-version-identity')
check(receipt['status']=='EXECUTION_REPORTED' and receipt['verifier_identity'] is None and receipt['owned_acceptance_status']=='PENDING_INDEPENDENT_VERIFIER','executor-no-self-acceptance')
check(sha(raw[PREFIX+'artifacts.json'])==receipt['artifact_manifest_hash'],'artifact-manifest-hash')
check(len(manifest['files'])==len({f['path'] for f in manifest['files']})==63,'exact-artifact-inventory')
raw.update(blobs(ARCHIVE,[f['path'] for f in manifest['files'] if f['path'] not in raw]))
for entry in manifest['files']:
    check(sha(raw[entry['path']])==entry['sha256'],'archive-artifact-hash:'+entry['path'])
    check(sha((ROOT/entry['path']).read_bytes())==entry['sha256'],'working-artifact-unchanged:'+entry['path'])
source_paths=env['source_sha256']
check(len(source_paths)==345 and set(source_paths)==set(receipt['verified_source_paths']),'source-inventory-345')
check(env['git_head']==SOURCE and env['tracked_source_clean'] and env['tracked_status_porcelain']=='','clean-source-preflight')
additional=['spec/v2.0/contracts/acceptance.json','spec/v2.0/contracts/tasks.json','spec/v2.0/PACKAGE_MANIFEST.json','execution/project_identity.json','execution/route.json']
source=blobs(SOURCE,list(source_paths)+additional)
for name,want in source_paths.items():
    check(sha(source[name])==want,'source-preflight-hash:'+name)
    check(sha((ROOT/name).read_bytes())==want,'current-source-unchanged:'+name)
identity=json.loads(source['execution/project_identity.json'])
check(receipt['project_id']==identity['project_id'] and receipt['input_manifest_hash']==identity['spec_manifest_sha256']==sha(source['spec/v2.0/PACKAGE_MANIFEST.json']),'permanent-project-spec-identity')
contracts=json.loads(source['spec/v2.0/contracts/acceptance.json'])
contract=next(c for c in contracts['cases'] if c['id']=='C20')
check(contract['mode']=='FIXTURE' and contract['final_owner_task']=='W16','frozen-C20-fixture-owner')
registry=json.loads(source['execution/commands.json'])['commands']
expected={
    'test.evolution':['C20-PRIVATE-MISSING','C20-PRIVATE-TAMPER','C20-PRIVATE-REVOKED','C20-PRIVATE-GRANT-REMOVED','C20-PRIVATE-REMOTE-DENIED','C20-01','C20-02','C20-03'],
    'test.jev.fixture':json.loads(source['tests/jev/expected.json'])['TestW11C20RubricOnly'],
    'acceptance.audit':['C20-AUDIT-INTEGRITY','C20-AUDIT-VERSIONS','C20-AUDIT-NO-GAIN','C20-AUDIT-PROTECTED-RAW'],
}
check(set(expected)==set(contract['command_keys']),'three-frozen-required-keys')
allrows={};invocations={};runs=[];children={}
for result in receipt['verification_results']:
    ref=result['actual_invocation_reference'];inv=load(ref);key=inv['command_key'];invocations[key]=inv
    check(key in expected and inv['status']==result['status']==result['actual_dispatch_status']=='PASS','dispatcher-success:'+key)
    check(inv['exit_code']==inv['child_exit_code']==result['exit_code']==0,'dispatcher-exits:'+key)
    check(inv['code_revision']==SOURCE and inv['selectors']=={'task_id':'W16','check_id':'','case_id':'C20'},'dispatcher-exact-source-selector:'+key)
    check(inv['registered_command_revision']==sha(source['execution/commands.json']) and inv['toolchain_revision']==sha(source['execution/toolchains/locked.json']) and inv['dispatcher_sha256']==sha(source['execution/command_dispatcher/dispatch.py']),'dispatcher-registered-inputs:'+key)
    check(inv['argv'][1:]==registry[key]['argv'] and registry[key]['state']=='BOUND','registered-argv:'+key)
    check(inv['assertion_ids']==result['assertion_ids'] and len(inv['assertion_ids'])==len(expected[key]) and set(inv['assertion_ids'])==set(expected[key]),'exact-command-assertions:'+key)
    for version in inv['input_versions']:check(version['sha256']==sha(source[version['path']]),'registered-script-hash:'+key)
    for stream in ['stdout','stderr']:check(sha(raw[inv[stream]['path']])==inv[stream]['sha256'],'dispatcher-stream-hash:'+key+':'+stream)
    output=json.loads(raw[inv['stdout']['path']]);path=Path(output['receipt']).resolve()
    check(path.is_relative_to((ROOT/'execution/receipts/W16').resolve()),'child-receipt-boundary:'+key)
    report_path=path.relative_to(ROOT).as_posix();report=load(report_path);directory=path.parent.relative_to(ROOT).as_posix()+'/'
    children[key]=(directory,report,report_path)
    check(output['status']==report['status']=='PASS' and report['exit_code']==0 and output['assertions']==len(expected[key]),'child-success:'+key)
    check(output['assertion_ids']==report['assertion_ids']==inv['assertion_ids'],'child-assertion-chain:'+key)
    child_hashes=report.get('hashes',report.get('raw_evidence_hashes',{}))
    for name,want in child_hashes.items():check(sha(raw[directory+name])==want.removeprefix('sha256:'),'child-file-hash:'+key+':'+name)
    if key!='acceptance.audit':
        before=load(directory+'before.json');lines=raw[directory+'stdout.txt'].decode().splitlines()
        if key=='test.evolution':
            check(before['version_manifest']['code_commit']==SOURCE and before['run_receipt']['task_id']=='W16' and before['run_receipt']['case_id']=='C20','evolution-child-version')
            hashes=before['version_manifest']['files']
            check(report['scope']=='W16_G02_FIXTURE_ONLY' and report['independent_acceptance']=='NONE' and report['formal_A16']=='PARTIAL_FIXTURE_ONLY','evolution-scope-retained')
            check(sum(l.startswith('--- PASS: ') for l in lines)==6 and not any('--- FAIL:' in l or '--- SKIP:' in l for l in lines),'six-evolution-tests-passed')
            check(report['objective_gain_test_exit_code']==0,'objective-gain-unit-command-zero')
        else:
            check(before['code_revision']==SOURCE and before['task_id']=='W16' and before['case_id']=='C20','jev-child-version')
            hashes=before['version_manifest']
            check(before['runtime_model']['provider']=='LOOPBACK_FIXTURE' and before['runtime_model']['real_provider_called'] is False and before['automatic_authority']=='NONE','jev-fixture-no-provider-authority')
            check(before['implementation_model']=='gpt-6-sol' and 'C20' in before['rubric'],'jev-corrected-metadata')
            check(sum(l.startswith('=== RUN   ') for l in lines)==sum(l.startswith('--- PASS: ') for l in lines)==1 and not any('--- FAIL:' in l or '--- SKIP:' in l for l in lines),'one-jev-test-passed')
        missing=[p.replace('\\','/') for p in hashes if p.replace('\\','/') not in source]
        if missing:source.update(blobs(SOURCE,missing))
        for name,want in hashes.items():check(sha(source[name.replace('\\','/')])==want.removeprefix('sha256:'),'child-source-hash:'+key+':'+name)
        for row in report['assertions']:
            loc=row.get('raw',row.get('raw_evidence'));check(loc['path']=='stdout.txt' and type(loc['line']) is int and 1<=loc['line']<=len(lines),'assertion-location:'+key)
            line=lines[loc['line']-1];check(line.startswith('W16_ASSERTION ' if key=='test.evolution' else 'W11_ASSERTION '),'assertion-prefix:'+key)
            decoded=json.loads(line.split(' ',1)[1]);check(decoded=={k:v for k,v in row.items() if k not in ['raw','raw_evidence']},'assertion-raw-line:'+key+':'+row['assertion_id'])
    else:
        check(report['source_revision']==SOURCE and report['independent_acceptance']=='NONE' and report['scope']=='C20_EXISTING_FIXTURE_EVIDENCE_ONLY','audit-scope-version')
        for name,want in report['audited_input_hashes'].items():check(sha(raw[name.replace('\\','/')])==want.removeprefix('sha256:'),'audited-exact-input:'+name)
    for row in report['assertions']:
        check(row['status']=='PASS' and row['expected']==row['actual'],'raw-row-passed:'+key+':'+row['assertion_id'])
        check((ref,row['assertion_id']) not in allrows,'unique-command-assertion')
        allrows[(ref,row['assertion_id'])]=row
    runs.append({'command_key':key,'invocation_id':inv['invocation_id'],'assertions':len(inv['assertion_ids']),'child_report':report_path,'started_at':inv['started_at'],'ended_at':inv['ended_at']})
check(set(invocations)==set(expected) and len(runs)==3,'all-three-commands-executed')
audit=children['acceptance.audit'][1]
check(audit['upstream_invocations']=={k:invocations[k]['invocation_id'] for k in ['test.evolution','test.jev.fixture']},'audit-binds-these-two-runs')

# Recompute the public native baseline/candidate outcomes and signed record hashes.
public_count=0;native_count=0
def native_result(v,build):
    global native_count
    r=v['receipt'];request=v['request']
    ordered={'phase':request['phase'],'cases':[{k:c[k] for k in ['id','operation','a','b','text']} for c in request['cases']],'protected_paths':request['protected_paths']}
    check(v['build_hash']==build and v['input_hash']=='sha256:'+sha(json.dumps(ordered,ensure_ascii=False,separators=(',',':')).encode()),'public-native-build-input')
    check(v['raw_hash']=='sha256:'+sha(v['raw'].encode()) and base64.b64decode(r['stdout'])==v['raw'].encode(),'public-native-raw-stdout')
    check(not v.get('error') and r['exit_code']==0 and not r['timed_out'] and r['children_stopped'] and r['pid']>0 and r['appcontainer_sid'] and r['capabilities']==[],'public-native-success-lifecycle')
    rows=json.loads(v['raw']);check([x['id'] for x in rows]==['existing-add','negative-input','instruction-injection','optional-product'],'public-suite-case-order')
    values=['1' if x['value']==want else '0' for x,want in zip(rows,[15,-6,16,21])]
    native_count+=1
    return {'values':values,'required_passed':all(x=='1' for x in values[:3]),'correct':values.count('1'),'rows':rows}
directory=children['test.evolution'][0]
for name in raw:
    if not(name.startswith(directory) and name.endswith('-REGRESSION.json')):continue
    d=load(name);e=d['execution'];a=d['acceptance'];p=e['pair']
    check(e['receipt_hash']==seal(e) and a['receipt_hash']==seal(a),'public-record-receipt-hashes')
    check(a['verdict']=='PASS' and a['run_id']==e['run_id'] and e['state']=='RECORDED','public-record-accepted-regression')
    b=native_result(p['baseline'],e['baseline_hash']);c=native_result(p['candidate'],e['candidate_hash'])
    check(b==p['baseline_result'] and c==p['candidate_result'],'public-native-outcomes-recomputed')
    gain=b['required_passed'] and c['required_passed'] and c['correct']>b['correct']
    check(gain==p['improved']==e['improved']==False and p['baseline']['input_hash']==p['candidate']['input_hash'] and p['stable_preserved'],'public-no-gain-same-input')
    public_count+=1
check(public_count==6 and native_count==12,'six-public-native-pairs')

# Bind the final public rejection, objective aggregate and independently read private proof.
name=next(p for p in raw if p.startswith(directory) and p.endswith('-C20-promotion-rejection.json'));prefix=name.removesuffix('-C20-promotion-rejection.json')
rejected=load(name);record=load(prefix+'-REGRESSION.json');locator=load(prefix+'-C20-protected-locator.json');benefit=load(prefix+'-C20-private-benefit.json');conclusion=load(prefix+'-C20-conclusion.json')
check(rejected['status']=='REJECTED' and rejected['id']==record['candidate']['id']==record['execution']['candidate_id'],'same-candidate-promotion-rejected')
check(rejected['regression_acceptance_id']==record['acceptance']['id'] and rejected['experiment_id']==record['experiment']['id'] and record['experiment']['outcome']=='NO_IMPROVEMENT','rejection-exact-acceptance-experiment')
check(all(rejected[k]==record['candidate'][k] for k in ['project_id','stable_artifact_ref','candidate_artifact_ref']),'rejection-project-builds')
private=json.loads((OUT/'private-audit-report.json').read_bytes())
check(all(private['checks'].values()) and private['aggregate']=={'cases':2,'baseline_correct':2,'candidate_correct':2,'outcomes_equal':True,'scores_increased':True,'objective_gain':False},'independent-protected-objective-recomputation')
check(private['protected_hashes']['dual_rubric_raw_proof_sha256']==locator['dual_rubric_raw_proof_sha256']==audit['private_proof_sha256']==record['execution']['holdout_proof_hash']==conclusion['private_proof_hash']==benefit['private_proof_sha256'],'single-private-proof-chain')
check(benefit['old_score']==10 and benefit['new_score']==100 and benefit['outcome_gain'] is False and benefit['baseline_correct']==benefit['candidate_correct']==2,'benefit-score-only-zero-gain')
check(conclusion['quality_improved'] is False and conclusion['project_closed'] is False and conclusion['real_world_gain']=='NOT_ESTABLISHED' and conclusion['experiment_outcome']=='NO_IMPROVEMENT','no-false-quality-or-closure-claim')

# Reconcile frozen contract statements and every GLOBAL evidence mapping.
check(case['global_evidence_id']=='GLOBAL_EVIDENCE_V1' and case['run_receipt']['case_id']=='C20' and case['run_receipt']['run_id']==RUN and case['run_receipt']['environment_mode']=='FIXTURE','global-case-identity-mode')
check(case['run_receipt']['executor_identity']=='codex:/root' and case['run_receipt']['independent_verifier_identity']=='codex:/root/evolution_verifier','global-independent-role-binding')
check([a['assertion_id'] for a in case['assertion_results']]==[a['id'] for a in contract['assertions']],'exact-three-formal-assertions')
check(sorted(x['command_key'] for x in case['command_receipt'])==sorted(contract['command_keys']),'global-complete-command-set')
for entry in case['command_receipt']:
    ref=entry['reference'];check(sha(raw[ref])==entry['sha256'],'global-invocation-hash')
    inv=load(ref)
    for k in ['command_key','argv','cwd','environment_names','exit_code','stdout','stderr','registered_command_revision','code_revision']:check(entry[k]==inv[k],'global-command-field:'+k)
for frozen,actual in zip(contract['assertions'],case['assertion_results']):
    check(frozen['expected']==actual['expected'] and actual['status']=='PASS' and actual['actual'],'global-frozen-assertion:'+frozen['id'])
    for row in actual['actual']:
        check({k:v for k,v in row.items() if k!='invocation_reference'}==allrows[(row['invocation_reference'],row['assertion_id'])],'global-exact-supporting-row:'+frozen['id'])
    for item in actual['raw_evidence']:check(sha(raw[item['path']])==item['sha256'],'global-raw-reference-hash')
check(len(case['supplemental_assertions'])==len(allrows)==15,'global-supplemental-inventory')
for row in case['supplemental_assertions']:check({k:v for k,v in row.items() if k!='invocation_reference'}==allrows[(row['invocation_reference'],row['assertion_id'])],'global-supplemental-raw-row')
v=case['version_manifest'];check(all(v.get(k)==value for k,value in env.items()),'global-preflight-version-manifest')
refs=v['input_snapshots']+v['policy_versions']+v['lock_files']
missing=[x['path'] for x in refs if x['path'] not in source]
if missing:source.update(blobs(SOURCE,missing))
for item in refs:check(sha(source[item['path']])==item['sha256'],'global-version-ref:'+item['path'])
check(v['task_gates_sha256']==sha(source['spec/v2.0/contracts/tasks.json']),'global-task-contract-version')
check(sha(raw[PREFIX+'C20.json'])==receipt['owned_acceptance_evidence']['C20']['sha256'],'global-case-receipt-hash')
summary={'status':'PASS','task_id':'W16','run_id':RUN,'source_revision':SOURCE,'archive_commit':subprocess.check_output(['git','rev-parse',ARCHIVE],cwd=ROOT).decode().strip(),'executor_receipt_jcs_hash':receipt['receipt_hash'],'manifest_files':63,'frozen_source_files':345,'checks_passed':len(checks),'private_checks_passed':len(private['checks']),'registered_runs':runs,'public_native_records_recomputed':public_count,'public_native_invocations_recomputed':native_count,'protected_native_invocations_recomputed':4,'private_cases':2,'formal_assertion_ids':[a['id'] for a in contract['assertions']],'supplemental_rows':15,'new_native_test_runs':0,'accepted_case':'C20','accepted_mode':'FIXTURE','whole_W16_accepted':False,'A16_accepted':False,'LIVE_qualified':False}
(OUT/'global-audit-report.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
(OUT/'global-audit-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary))
