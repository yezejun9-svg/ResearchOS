"""Finite Source-only checks. Authority fixtures remain in memory and grant nothing."""
import ast, copy, hashlib, json, os, sys, types
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent;R=Path('D:/作品集/ResearchOS/research-os')
def main():
    m=types.ModuleType('bounded_full_w09_source');m.__file__=str(N/'full_w09_runtime.source.py')
    exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
    rows=[]
    def check(name,ok,detail=None):
        if not ok:raise AssertionError(name)
        rows.append(dict(name=name,status='PASS',detail=detail))
    def rejected(name,fn,code=None):
        try:fn()
        except (ValueError,KeyError,FileNotFoundError,TypeError) as exc:
            check(name,code is None or code in str(exc),dict(type=type(exc).__name__,error=str(exc)));return
        raise AssertionError(name+' ACCEPTED')
    choice=json.loads((N/'source.choice.json').read_bytes());contract=json.loads((N/'root-calling-contract.json').read_bytes())
    check('three_distinct_run_ids',len({c['run_id'] for c in choice['selectors'].values()})==3)
    check('fixed_three_selectors',set(choice['selectors'])=={'W09-G01','W09-G02','A06'})
    for key in choice['selectors']:
        c=m.choice(key);env=m.build_environment(c)
        check(key+'_exact_selector_environment',env['RESEARCHOS_CHECK_ID']==c['selector']['check_id'] and env['RESEARCHOS_CASE_ID']==c['selector']['case_id']
            and env['RESEARCHOS_RETRIEVAL_MODE']==('live' if key=='W09-G02' else 'fixture'))
        check(key+'_two_packages',c['packages']==['./adapters/retrieval','./internal/domain'] and c['list_argv_suffix'][-2:]==c['packages']
            and c['go_test_argv_suffix'][-2:]==c['packages'])
        check(key+'_full_frozen_regex',c['go_test_argv_suffix'][4]=='^(?:'+'|'.join(c['selected_tests'])+')$')
        check(key+'_fresh_one_shot_paths',all(not Path(c[n]).exists() for n in ('receipt_root','scratch_root','output_root')))
        check(key+'_mode_count',c['required_independent_modes']==(2 if key=='A06' else 1))
    g=m.choice('W09-G01');check('G01_five_tests_eight_ids',len(g['selected_tests'])==5 and len(g['expected_native_ids'])==8
        and g['selected_tests'][:2]==['TestW09C19ExplicitOriginAndUnknown','TestW09C19ChainInvalidation'])
    for key in ('W09-G02','A06'):
        c=m.choice(key);check(key+'_eight_tests_seven_ids',len(c['selected_tests'])==8 and len(c['expected_native_ids'])==7)
    rejected('standalone_C19_forbidden',lambda:m.choice('C19'),'THREE_SELECTORS_ONLY')
    rejected('unknown_selector_forbidden',lambda:m.choice('W09-G03'),'THREE_SELECTORS_ONLY')
    rejected('missing_selector_args_stop_before_process',lambda:m.stage('run',[]),'SELECTOR_AND_THREE')
    rejected('duplicate_JSON_keys',lambda:m.decode('{"a":1,"a":2}'),'DUPLICATE_JSON_KEY')
    rejected('nonfinite_JSON',lambda:m.decode('{"a":NaN}'),'NONFINITE_JSON')
    rejected('bool_ref_size',lambda:m.read_ref(dict(path=str(N/'source.choice.json'),sha256='0'*64,bytes=True)),'TYPED_REF')
    rejected('foreign_or_missing_request',lambda:m.validate_authority(dict(path=str(N/'not-issued-root-request.json'),sha256='0'*64,bytes=0),m.choice('W09-G01')))
    good=dict(owned_child_pid=42,creation_time_100ns=0xffffffffffffffff,actual_exit=0,error=None,timed_out=False,
        job_cleanup=dict(errors=[],active_processes_last_observed=0,**{k:True for k in ('unnamed_exclusive_job','kill_on_job_close_configured','assigned_before_resume','primary_exit_confirmed','job_idle_confirmed','handles_closed')}))
    check('exact_uint64_FILETIME_preserved',m.job_closed(good))
    for name,field,value in [('boolean_PID','owned_child_pid',True),('zero_PID','owned_child_pid',0),('float_FILETIME','creation_time_100ns',1.0),
        ('boolean_FILETIME','creation_time_100ns',True),('overflow_FILETIME','creation_time_100ns',2**64)]:
        bad=copy.deepcopy(good);bad[field]=value;check(name+'_rejects',m.job_closed(bad) is False)
    for field,value in [('active_processes_last_observed',True),('handles_closed',False),('errors',['close failed'])]:
        bad=copy.deepcopy(good);bad['job_cleanup'][field]=value;check('cleanup_'+field+'_rejects',m.job_closed(bad) is False)
    # Full authority shape and mutation checks: mock bytes only; no Canon or scope writes.
    original={name:getattr(m,name) for name in ('read_ref','pin','package_refs','actual_audit')}
    c=m.choice('W09-G01');memory={}
    def fixture(name,obj):
        raw=(json.dumps(obj,ensure_ascii=False)+'\n').encode();ref=dict(path=str(N/('IN_MEMORY_ONLY_'+name)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));memory[ref['path']]=raw;return ref
    href=fixture('HDF',{});mref=fixture('MF',{})
    bound={k:m.pin(N/v) for k,v in contract['source_file_bindings'].items()};cr=m.pin(N/'root-calling-contract.json')
    dr=fixture('review-decision',dict(schema=contract['review_schema'],decision=contract['review_decision'],actor_role='INDEPENDENT_NON_AUTHOR',
        actor_id='codex:/root/independent_test_peer',source_handoff_ref=href,source_manifest_ref=mref,calling_contract_ref=cr,**bound,
        selectors=choice['selectors'],source21=c['source21'],actual_executed=False,formal_case_accepted_delta=0))
    rh=fixture('review-HDF',dict(actor_id='codex:/root/independent_test_peer',source_decision_ref=dr,manifest_ref=None))
    rm=fixture('review-MF',dict(members=[dr]))
    rh=fixture('review-HDF',dict(actor_id='codex:/root/independent_test_peer',source_decision_ref=dr,manifest_ref=rm))
    aa=fixture('author-audit',{});ra=fixture('review-audit',{});sa=fixture('Root-scope-audit',{})
    now=datetime.now(timezone.utc)
    scope=dict(schema=contract['scope_schema'],status='ROOT_AUTHORIZED_SINGLE_SELECTOR_NATIVE',issued_by=m.ROOT_ACTOR,executor=m.ROOT_ACTOR,
        source_handoff_ref=href,source_manifest_ref=mref,**bound,source_review_handoff_ref=rh,source_review_manifest_ref=rm,source_review_decision_ref=dr,
        source_author_audit_ref=aa,source_review_audit_ref=ra,lease_id='a'*32,lease_issued_at=(now-timedelta(minutes=1)).isoformat(),
        lease_expires_at=(now+timedelta(minutes=5)).isoformat(),maximum_go_test_runs=1,maximum_go_list_runs=1,
        **{key:c[key] for key in ('selector_key','selector','mode','native_scope','packages','source_root','run_id','receipt_root','scratch_root','output_root',
            'selected_tests','expected_native_ids','source21','list_timeout_seconds','producer_timeout_seconds','inner_Go_timeout_seconds')},
        **{key:False for key in m.BOOL_FALSE},**{key:0 for key in m.ZERO})
    sr=fixture('scope',scope)
    owner=dict(owner=m.ROOT_ACTOR,current_source_writer=None,state='ROOT_REGISTERED_PENDING_SELECTOR_NATIVE',scope_ref=sr,source_handoff_ref=href,
        source_manifest_ref=mref,source_review_handoff_ref=rh,source_review_manifest_ref=rm,source_root=str(R),selector=c['selector_key'],run_id=c['run_id'],
        receipt_root=c['receipt_root'],scratch_root=c['scratch_root'],output_root=c['output_root'],lease_id=scope['lease_id'],lease_issued_at=scope['lease_issued_at'],
        lease_expires_at=scope['lease_expires_at'],formal_case_accepted_delta=0,parent_acceptance=False)
    worker=dict(step_id='W09-99',slice_id=m.SLICE+'_'+c['selector_key'],owner=m.ROOT_ACTOR,state=owner['state'],scope_ref=sr,source_handoff_ref=href,
        source_review_handoff_ref=rh,run_id=c['run_id'],lease_id=scope['lease_id'])
    docs=[dict(revision=372,project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',head=c['expected_git_head'],workers=[worker],
        work_in_progress=dict(w09_native_producer_scopes={c['selector_key']:sr})),
        dict(revision=176,active_integrator=dict(id=m.ROOT_ACTOR),shared_integrator='qoder-desktop:/root/platform_owner',
        card_path_bindings={'W09-99':dict(owner=m.ROOT_ACTOR,subtasks={m.OWNER_KEY+'_'+c['selector_key']:owner})}),{},{}]
    canon=[]
    for p,doc in zip(m.CANON,docs):
        raw=json.dumps(doc).encode();ref=dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw));memory[str(p)]=raw;canon.append(ref)
    vr=fixture('canonical-vector',dict(schema='researchos.w09-three-selector-native-canonical-vector.v1',checkpoint_revision=372,ownership_revision=176,refs=canon))
    q=dict(schema=contract['request_schema'],issued_by=m.ROOT_ACTOR,selector=c['selector_key'],scope_ref=sr,canonical_vector_ref=vr,calling_contract_ref=cr,scope_audit_ref=sa)
    qr=fixture('request',q);auditcalls=[]
    def memory_read(ref):
        if ref['path'] in memory:
            raw=memory[ref['path']];m.require(m.raw_pin(Path(ref['path']),raw)==ref,'CONTROL_MEMORY_PIN');return raw
        return original['read_ref'](ref)
    m.read_ref=memory_read;m.package_refs=lambda:(href,mref,[href,mref])
    m.actual_audit=lambda ref,actor,binding:(auditcalls.append((actor,binding)) or [ref])
    try:
        result=m.validate_authority(qr,c)
        check('in_memory_authority_shape_positive_NO_GRANT',len(auditcalls)==3 and result[1]==scope)
        for name,key,value,code in [('non_Root_executor','executor',m.AUTHOR,'ROOT_SCOPE'),('boolean_zero_budget','formal_case_accepted_delta',False,'SCOPE_BOUNDARY'),
            ('extra_Native_run','maximum_go_test_runs',2,'FINITE_EXECUTION_BUDGET'),('foreign_mode','mode','LIVE_WINDOWS','EXACT_SCOPE_mode'),
            ('foreign_output','output_root',str(N/'wrong'),'EXACT_SCOPE_output_root'),('stale_lease','lease_expires_at',(now-timedelta(seconds=1)).isoformat(),'CURRENT_FINITE_LEASE')]:
            bad=copy.deepcopy(scope);bad[key]=value;br=fixture('bad-scope-'+name,bad);bq=dict(q,scope_ref=br);bqr=fixture('bad-request-'+name,bq)
            rejected('authority_'+name,lambda:m.validate_authority(bqr,c),code)
        bad=copy.deepcopy(json.loads(memory[dr['path']]));bad['actor_id']=m.AUTHOR;bdr=fixture('author-self-review',bad)
        badh=fixture('self-review-HDF',dict(actor_id=m.AUTHOR,source_decision_ref=bdr,manifest_ref=None));badm=fixture('self-review-MF',dict(members=[bdr]));badh=fixture('self-review-HDF',dict(actor_id=m.AUTHOR,source_decision_ref=bdr,manifest_ref=badm))
        bad=copy.deepcopy(scope);bad.update(source_review_handoff_ref=badh,source_review_manifest_ref=badm,source_review_decision_ref=bdr)
        br=fixture('scope-self-review',bad);bqr=fixture('request-self-review',dict(q,scope_ref=br))
        rejected('author_cannot_approve_source',lambda:m.validate_authority(bqr,c),'INDEPENDENT_SOURCE_DECISION')
    finally:
        for name,value in original.items():setattr(m,name,value)
    # Resource cleanup always continues after archive and first close failures.
    class Guard:
        def __init__(self,fail=False):self.closed=False;self.fail=fail
        def close(self):
            self.closed=True
            if self.fail:raise OSError('CONTROL_CLOSE_FAILURE')
            return dict(closed=True,errors=[],retained_handles_count=0)
    g1,g2=Guard(),Guard(True);closed=m.close_stage_resources('prepare',False,c,N,Path(c['output_root']),[('one',g1),('two',g2)])
    check('close_failure_does_not_skip_other_guards',g1.closed and g2.closed and closed['all_guards_closed'] is False and bool(closed['errors']))
    for filename in ('full_w09_runtime.source.py','full_w09_launcher.source.py','prepare_full_w09.source.py','run_full_w09.source.py'):
        ast.parse((N/filename).read_bytes());check(filename+'_AST',True)
    check('runtime_no_constant_351',(N/'full_w09_runtime.source.py').read_text().find('351')==-1)
    bp=json.loads((N/'compiler-source-blueprint.json').read_bytes());m.verify_directories(bp)
    check('two_test_variants_required',len(bp['required_test_packages'])==6 and bp['actual_package_count'] is None)
    check('Main21_current',all(m.pin(ref['path'])==ref for ref in c['source21']))
    check('source_guard_closed',m.guard_cleanup_ok(json.loads((N/'source-build-guard.closed.json').read_bytes())))
    check('no_authority_or_native_paths_created',all(not Path(c[k]).exists() for c in choice['selectors'].values() for k in ('receipt_root','scratch_root','output_root')))
    m.save(N,'source-controls.json',dict(schema='researchos.w09-three-selector-bounded-source-controls.v1',actor_id=m.AUTHOR,
        controls=rows,status='PASS_SOURCE_ONLY',authority_fixture='IN_MEMORY_ONLY_MOCKED_AUDIT_NOT_AUTHORITY',
        actual_Go_runs=0,actual_Native_runs=0,actual_dispatcher_runs=0,actual_SQL_runs=0,actual_model_calls=0,
        Canon_read_in_controls=False,Canon_written=False,Main_written=False,execution_grant=False,formal_case_accepted_delta=0))
    print(json.dumps(dict(status='PASS_SOURCE_ONLY',checks=len(rows),Source_scope='three-selector caller controls only; no Native or formal qualification')))
if __name__=='__main__':main()
