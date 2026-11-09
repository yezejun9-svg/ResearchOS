"""Finite Source controls: synthetic authority objects grant no actual scope."""
import ast,builtins,copy,hashlib,json,sys,types
from datetime import datetime,timedelta,timezone
from pathlib import Path
sys.dont_write_bytecode=True
N=Path(__file__).resolve().parent
def main():
    m=types.ModuleType('public22_recheck_controls');m.__file__=str(N/'public22_recheck_root.source.py')
    exec(compile(Path(m.__file__).read_bytes(),m.__file__,'exec'),m.__dict__)
    rows=[]
    def check(name,ok,detail=None):
        if not ok:raise AssertionError(name)
        rows.append(dict(name=name,status='PASS',detail=detail))
    def rejected(name,fn,code=None):
        try:fn()
        except (ValueError,KeyError,TypeError,FileNotFoundError) as exc:
            check(name,code is None or code in str(exc),dict(type=type(exc).__name__,error=str(exc)));return
        raise AssertionError(name+' ACCEPTED')
    i=m.inputs();original=m.original_evidence(i)
    check('actual_old_metadata_and_original_Root_audit',len(original['state']['calls'])==4)
    check('original1025_failed_unchanged',original['state']['status']=='STOPPED_AT_FIRST_FAILURE' and original['assignment']['ordinal']==1025)
    check('fixed_original_request_exact',original['requirements']['request_ref']==i['case_request_ref'])
    check('nine_evidence_refs_exact',len(i['evidence'])==9 and i['evidence']==original['requirements']['evidence'])
    check('six_baseline_readonly_members',len(original['baseline']['references'])==6)
    runtime=m.doc(i['runtime_resources_ref'])
    for ref in runtime['resource_refs']:m.checked(ref)
    check('reviewable_SQLite_resource_manifest_pinned',any(m.same(ref,runtime['sqlite_extension_ref']) for ref in runtime['resource_refs']))
    for label,ref in [('leaf',i['leaf_runner_ref']),('TP',m.TP_REF),('SourceGuard',m.GUARD_REF)]:m.checked(ref);check(label+'_exact_pin',True)
    ref=i['case_request_ref'];check('slash_spelling_preserves_physical_ref',m.same(ref,dict(ref,path=Path(ref['path']).as_posix())))
    check('nested_JSON_full_ref_positive',m.contains_ref({'output':json.dumps({'ref':ref})},ref))
    check('truncated_outer_JSON_nested_complete_ref',m.contains_ref('{"old":'+json.dumps(ref)+',"truncated":',ref))
    check('SHA_substring_alone_is_not_ref',not m.contains_ref(ref['sha256'],ref))
    check('wrong_path_same_SHA_rejected',not m.contains_ref(dict(ref,path=str(N/'wrong')),ref))
    check('wrong_bytes_same_SHA_rejected',not m.contains_ref(dict(ref,bytes=ref['bytes']+1),ref))
    check('bool_bytes_rejected',not m.contains_ref(dict(ref,bytes=True),ref))
    for field,value in [('owned_child_pid',True),('owned_child_pid',0),('creation_time_100ns',True),('creation_time_100ns',1.5),('creation_time_100ns',2**64),('actual_exit',False)]:
        bad=copy.deepcopy(original['state']['calls'][0]['observation']);bad[field]=value
        rejected('native_'+field+'_'+str(value),lambda:m.native_observation(bad))
    observation=copy.deepcopy(original['state']['calls'][0]['observation']);observation['creation_time_100ns']=str(observation['creation_time_100ns'])
    check('decimal_FILETIME_preserved',m.native_observation(observation)==observation['creation_time_100ns'])
    now=datetime.now(timezone.utc);q=dict(lease_id='a'*32,lease_issued_at=(now-timedelta(minutes=1)).isoformat(),lease_expires_at=(now+timedelta(minutes=5)).isoformat())
    m.lease(q);check('finite_live_lease_shape',True)
    rejected('expired_lease',lambda:m.lease(dict(q,lease_expires_at=(now-timedelta(seconds=1)).isoformat())),'LIVE_READONLY_LEASE')
    rejected('naive_lease',lambda:m.lease(dict(q,lease_issued_at='2026-10-09T00:00:00')),'TIMEZONE_REQUIRED')
    rejected('unbounded_lease',lambda:m.lease(dict(q,lease_expires_at=(now+timedelta(days=1)).isoformat())),'LIVE_READONLY_LEASE')
    rejected('product_run_mode_absent',lambda:m.main(['run',ref['path'],ref['sha256'],str(ref['bytes'])]),'READONLY_CALLER_MODES_ONLY')
    rejected('leaf_case_request_not_Root_envelope',lambda:m.root_request(i['case_request_ref']))
    # No registration files or actual canonical reads: TP projection is pure.
    fake=lambda name:dict(path=str(N/('IN_MEMORY_ONLY_'+name)),sha256=hashlib.sha256(name.encode()).hexdigest(),bytes=len(name))
    sr,oref,wref,fref=[fake(name) for name in ('scope','owner','worker','facts')]
    owner=dict(scope_ref=sr,selected_worker_id=m.ROOT);worker=dict(scope_ref=sr,selected_owner_ref=oref,worker_id=m.ROOT,slice_id=m.SLICE)
    basecp=dict(revision=400,project_id='aede0678-7308-43dc-b9f2-cfe3d90cfdfb',workers=[dict(slice_id='OTHER',unchanged=True)],
        work_in_progress=dict(root_next_failure_ordinal_live=1041,existing='preserve'),failure_counters=[dict(ordinal=1025,status='FAILED_RETAINED')])
    baseow=dict(revision=209,card_path_bindings={'W05-99':dict(subtasks={'OTHER':dict(unchanged=True)})})
    oldopen=builtins.open;oldchecked=m.checked;oldpin=m.pin
    deny=lambda *a,**k:(_ for _ in ()).throw(AssertionError('IO_FORBIDDEN_IN_TP_CALLBACK'))
    try:
        builtins.open=deny;m.checked=deny;m.pin=deny
        aftercp,afterow=m.projection(basecp,baseow,sr,oref,wref,fref,owner,worker,'2026-10-10T00:00:00+00:00')
    finally:builtins.open=oldopen;m.checked=oldchecked;m.pin=oldpin
    check('TP_projection_performs_no_IO',True)
    check('rebase_400_209_to_401_210',aftercp['revision']==401 and afterow['revision']==210)
    check('other_worker_and_owner_preserved',aftercp['workers'][0]==basecp['workers'][0] and afterow['card_path_bindings']['W05-99']['subtasks']['OTHER']==baseow['card_path_bindings']['W05-99']['subtasks']['OTHER'])
    check('original_failure_counter_never_reset_or_appended',aftercp['failure_counters']==basecp['failure_counters'] and aftercp['work_in_progress']['root_next_failure_ordinal_live']==1041)
    rejected('second_registration_rejected',lambda:m.projection(aftercp,afterow,sr,oref,wref,fref,owner,worker,'later'),'READONLY_SLICE_ALREADY_REGISTERED')
    # Inverse semantic validation plus original raw archive byte restoration.
    restored_cp=copy.deepcopy(aftercp);restored_ow=copy.deepcopy(afterow)
    for key in ('workers','work_in_progress','revision','expected_previous_revision','updated_at','updated_by'):
        if key in basecp:restored_cp[key]=basecp[key]
        else:restored_cp.pop(key,None)
    del restored_ow['card_path_bindings']['W05-99']['subtasks'][m.KEY]
    for key in ('revision','updated_at','updated_by'):
        if key in baseow:restored_ow[key]=baseow[key]
        else:restored_ow.pop(key,None)
    check('full_projection_inverse',restored_cp==basecp and restored_ow==baseow)
    byte_examples=[]
    for value,restored in [(basecp,restored_cp),(baseow,restored_ow)]:
        raw=(json.dumps(value,ensure_ascii=False,indent=3)+'\n').replace('\n','\r\n').encode()
        archive=bytes(raw);check('raw_archive_inverse_'+str(len(byte_examples)),json.loads(archive)==restored and archive==raw)
        byte_examples.append(dict(before_sha256=hashlib.sha256(raw).hexdigest(),restored_sha256=hashlib.sha256(archive).hexdigest(),bytes=len(raw)))
    # Leaf callback denies before first artifact read, before requiring a mocked live scope.
    oldlive,oldchecked=m.live,m.checked;read_calls=[]
    scope=dict(leaf_contract_ref=i['leaf_contract_ref'],case_request_ref=i['case_request_ref'],evidence=i['evidence'])
    m.live=lambda _: (scope,None,None,None);m.checked=lambda r:read_calls.append(r) or b''
    try:
        cap=m.ExistingObservationScope({},None,[])
        rejected('released_capability_before_any_IO',lambda:cap.require_existing_observation(i['leaf_contract_ref'],i['case_request_ref'],i['evidence'],m.LEAF_AUTHOR),'LIVE_CAPABILITY_ONCE_HELD')
        check('released_capability_zero_artifact_reads',not read_calls)
        cap=m.ExistingObservationScope({},object(),[i['leaf_contract_ref'],i['case_request_ref'],*i['evidence'].values()])
        rejected('wrong_Source_author_before_any_IO',lambda:cap.require_existing_observation(i['leaf_contract_ref'],i['case_request_ref'],i['evidence'],m.AUTHOR),'LIVE_ORIGINAL_LEAF_BINDING')
        check('wrong_author_zero_artifact_reads',not read_calls)
        cap.require_existing_observation(i['leaf_contract_ref'],i['case_request_ref'],i['evidence'],m.LEAF_AUTHOR)
        check('synthetic_capability_once_after_all_resources_bound',cap.used and len(read_calls)==11)
        rejected('capability_replay_rejected',lambda:cap.require_existing_observation(i['leaf_contract_ref'],i['case_request_ref'],i['evidence'],m.LEAF_AUTHOR),'LIVE_CAPABILITY_ONCE_HELD')
        cap=m.ExistingObservationScope({},object(),[])
        rejected('missing_held_resources_rejected',lambda:cap.require_existing_observation(i['leaf_contract_ref'],i['case_request_ref'],i['evidence'],m.LEAF_AUTHOR),'REQUIRED_ARTIFACTS_ALREADY_HELD')
        m.live=lambda _:(_ for _ in ()).throw(ValueError('CONTROL_REVOKED_REGISTRATION'))
        cap=m.ExistingObservationScope({},object(),[])
        rejected('revoked_registration_stops_callback',lambda:cap.require_existing_observation(i['leaf_contract_ref'],i['case_request_ref'],i['evidence'],m.LEAF_AUTHOR),'CONTROL_REVOKED')
    finally:m.live,m.checked=oldlive,oldchecked
    class Guard:
        def close(self):return dict(closed=True,retained_handles_count=0,errors=[])
    oldsave=m.save;m.save=lambda *a,**k:(_ for _ in ()).throw(OSError('CONTROL_SAVE_FAILURE'))
    try:
        closed=m.close_guard(Guard(),N,'never-created',True)
        check('cleanup_save_failure_retains_successful_close',closed['cleanup']['closed'] and closed['errors'][0]['phase']=='guard-cleanup-save')
        primary=ValueError('ORIGINAL_PRIMARY');failure=m.SourceFailure('CONTROL',primary,closed['errors'])
        check('cleanup_never_masks_original_exception',failure.primary_exception is primary and len(failure.secondary_errors)==1)
    finally:m.save=oldsave
    # Real old Root audit is the positive case; tampering with self-consistent pins fails physical provenance.
    ar=original['requirements']['original_actual_capture_binding_ref'];binding=m.doc(ar);raw=m.checked(binding['original_capture_ref']);lines=raw.splitlines(keepends=True)
    prior=m.doc(original['requirements']['original_caller_record_ref'])['root_request_ref']
    for name,toolname in [('qualified_exec_supported','functions.exec'),('wrong_exec_name','exec_command')]:
        changed=[json.loads(x) for x in lines];changed[1]['payload']['name']=toolname
        crafted=[(json.dumps(v,ensure_ascii=False)+'\n').encode() for v in changed];fake_raw=b''.join(crafted)
        fakecap=fake('capture'+name);fakebinding=fake('binding'+name);b=copy.deepcopy(binding)
        b.update(original_capture_ref=fakecap,source_line_bytes=[len(x) for x in crafted],original_line_sha256=[hashlib.sha256(x).hexdigest() for x in crafted])
        oldchecked=m.checked;m.checked=lambda ref,b=b: m.encoded(b) if ref==fakebinding else fake_raw if ref==fakecap else oldchecked(ref)
        try:rejected(name,lambda:m.audit(fakebinding,m.ROOT,[prior,i['case_request_ref']]),'ORIGINAL_ROOT_BYTES' if name=='qualified_exec_supported' else 'ROOT_EXEC_CALL_AND_OUTPUT')
        finally:m.checked=oldchecked
    tree=ast.parse(Path(m.__file__).read_bytes())
    check('no_product_process_invocations',not any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr in ('run_owned','Popen','run_registered_case') for x in ast.walk(tree)))
    check('exact_readonly_leaf_entry',any(isinstance(x,ast.Call) and isinstance(x.func,ast.Attribute) and x.func.attr=='recheck_existing_public22' for x in ast.walk(tree)))
    check('TP_guard_explicitly_excludes_pair','refs_unique(refs,CANON[:2])' in Path(m.__file__).read_text())
    check('Source_has_no_issued_scope',not any((N/name).exists() for name in ('scope.root.json','owner.root.json','worker.root.json','facts.root.json')))
    result=m.save(N,'source-controls.json',dict(status='PASS_SOURCE_ONLY',controls=rows,byte_inverse_examples=byte_examples,
        synthetic_authority_controls=True,real_old_artifact_metadata_and_audit_checked=True,SQL_queries=0,new_native_children=0,
        actual_TP_transactions=0,current_Canon_read=False,original1025_result='FAILED_RETAINED',execution_grant=False,formal_acceptance=False))
    print(json.dumps(dict(status='PASS_SOURCE_ONLY',checks=len(rows),result_ref=result,SQL_queries=0,new_native_children=0),ensure_ascii=False))
if __name__=='__main__':main()
