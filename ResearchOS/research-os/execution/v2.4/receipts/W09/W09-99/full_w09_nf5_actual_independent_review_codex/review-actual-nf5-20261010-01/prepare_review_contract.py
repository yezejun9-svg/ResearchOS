import ast,hashlib,json,sys,traceback,types
from pathlib import Path
Q=Path(__file__).resolve().parent
def main():
    path=Q/'review_actual_nf5.py';raw=path.read_bytes();tree=ast.parse(raw);compile(tree,str(path),'exec')
    namespace={'__file__':str(path),'__name__':'Source_only_nf5_reviewer'}
    exec(compile(tree,str(path),'exec'),namespace)
    checks=[]
    def check(name,fn):fn();checks.append(dict(name=name,status='PASS',execution_scope='SOURCE_ONLY_NO_NATIVE'))
    def rejects(fn):
        try:fn()
        except ValueError:return
        raise AssertionError('expected exact rejection')
    uint=namespace['uint'];decode=namespace['decode'];job=namespace['job']
    check('uint64-above-JS-safe-keeps-exact',lambda:assert_equal(uint(134360591449948294,64,'FILETIME'),134360591449948294))
    check('bool-is-not-PID',lambda:rejects(lambda:uint(True,32,'PID')))
    check('float-is-not-FILETIME',lambda:rejects(lambda:uint(float(134360591449948294),64,'FILETIME')))
    check('string-is-not-uint64',lambda:rejects(lambda:uint('134360591449948294',64,'FILETIME')))
    check('uint64-overflow-rejected',lambda:rejects(lambda:uint(1<<64,64,'FILETIME')))
    check('duplicate-JSON-key-rejected',lambda:rejects(lambda:decode(b'{"x":0,"x":1}')))
    check('nonfinite-JSON-rejected',lambda:rejects(lambda:decode(b'{"x":NaN}')))
    shape=json.loads((Q/'actual-input-shapes.json').read_bytes());real=shape['G02_invocation_observations'][-1]['row']['record']
    check('already-closed-G02-job-numeric-observation',lambda:assert_equal(job(real)['creation_time_100ns_decimal'],'134360591449948294'))
    clone=json.loads(json.dumps(real));clone['creation_time_100ns_decimal']='134360591449948288'
    check('changed-FILETIME-decimal-rejected',lambda:rejects(lambda:job(clone)))
    clone=json.loads(json.dumps(real));clone['result']['job_cleanup']['active_processes_last_observed']=1
    check('active-descendant-rejected',lambda:rejects(lambda:job(clone)))
    clone=json.loads(json.dumps(real));clone['individual_child_numeric_exit']=0
    check('invented-descendant-zero-rejected',lambda:rejects(lambda:job(clone)))
    previous=Path('D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W09/W09-99/full_w09_nf5_independent_source_review_codex/review-nf5-20261010-01')
    def pin(p):
        b=Path(p).read_bytes();return dict(path=str(p),sha256=hashlib.sha256(b).hexdigest(),bytes=len(b))
    contract=dict(schema='researchos.w09-nf5-actual-independent-review-calling-contract.v1',status='PREPARED_WAITING_FOR_ROOT_FOUR_FINAL_ACTUAL_INPUTS',
        reviewer='codex:/root/backup_regression_resources',source_author='codex:/root/attach_restore_independent_review',executor='codex:/root',
        reviewer_program_ref=pin(path),prior_Source_review_refs=dict(hdf=pin(previous/'producer/HDF.json'),mf=pin(previous/'producer/MF.json'),decision=pin(previous/'producer/decision.json')),
        reused_Source_checks=27,reused_Source_resource_closure=4154,old_Source_checks_repeated=False,
        input_schema='researchos.w09-nf5-four-actual-review-input.v1',input_exact_fields=['schema','source_review_ref','groups'],
        exact_group_keys=['W09-G01','W09-G02','A06','C19'],group_exact_fields=['prepare_ref','producer_closed_ref','prepare_Root_capture_ref','prepare_Root_observation_ref','run_initial_Root_capture_ref','run_completed_Root_capture_ref'],
        all_refs=dict(exact_fields=['path','sha256','bytes'],sha256='bare lowercase 64hex',bytes='nonnegative exact int, bool forbidden',paths='verified regular absolute path; repo-relative pinned raw refs normalized physically; no private credential or liveCanon/audit reads'),
        future_actual_inputs=None,Source_only_controls_ref=pin(Q/'source-preparation-controls.json')if(Q/'source-preparation-controls.json').exists()else None,
        actual_review_required=['all four exact original run IDs/selector rosters; C19 two tests/five IDs',
            'same Root request/registered distinct generation and original finite lease; no borrowed scope',
            'original report+ToolRun+two streams+all owned graph+Source21 SHA and Go lock',
            'actual Go package/test run and unique terminal PASS/clock interval',
            'HTTP/SQLite/file business facts replayed from existing readonly Main consumer',
            'Go-list and Python exclusive Job actual0/descendant idle0/handles closed; known uint64 FILETIME preserved as int and decimal string',
            '3905 Source inputs held by original input guard plus actual private compiler exports/gomods closure',
            'prepare and producer guards closed0 with actual serialized originals',
            'Root original header+tool call+returned output from immutable captures; running session→same completion; no live audit handle',
            'FIXTURE actual HTTP recorder+owned temp states; G02 actual Windows branch+junction command+owned output',
            'all formal accepted deltas0; no new Native/Go/model/dispatcher/TP/Main/Canon call'],
        Mode_policy=dict(final_Mode_issued=False,qualification='Backup independent actual facts only',finalization='MODE_FINALIZATION_REQUIRES_TRUE_FULL_REVIEWER',
            code_refs=['formal_profile_w09.py:329 VERIFIER proof reads one actual Mode /reviewer_id','formal_profile_w09.py:410-424 final acceptance/owner/issuance require registry verifier','w09_evidence_closure.py:565-592 local Mode verifies producer != reviewer and matching independent receipt'],
            Root_current_contract_final_Verifier='/root/full_w09_source_review',no_impersonation=True),
        future_argv=['C:/Users/yqyyds/AppData/Local/Python/pythoncore-3.14-64/python.exe','-I','-S','-B','-X','utf8',str(path),'<Root-four-completed-input.path>','<sha256>','<bytes>'],
        execution_grant=False,formal_acceptance=False,formal_case_accepted_delta=0,new_Native_runs=0,new_Go_runs=0,new_model_requests=0,Main_written=False,Canon_written=False)
    with(Q/'source-preparation-controls.json').open('xb')as f:f.write((json.dumps(dict(schema='researchos.nf5-reviewer-source-controls.v1',checks=checks,passed=len(checks),failed=0,old_checks_repeated=False,Native_called=False,formal_acceptance=False),ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    contract['Source_only_controls_ref']=pin(Q/'source-preparation-controls.json')
    with(Q/'input-contract.json').open('xb')as f:f.write((json.dumps(contract,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    print(json.dumps(dict(status=contract['status'],input_contract_ref=pin(Q/'input-contract.json'),review_program_ref=pin(path),Source_controls=len(checks),Native_called=False,formal_acceptance=False),ensure_ascii=False));return 0
def assert_equal(a,b):
    if a!=b:raise AssertionError((a,b))
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
