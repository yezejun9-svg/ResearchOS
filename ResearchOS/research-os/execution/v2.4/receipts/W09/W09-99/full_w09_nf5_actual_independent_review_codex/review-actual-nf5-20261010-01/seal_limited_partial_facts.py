import hashlib,json,os,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
R=Q.parents[6]
S=Q.parent.parent/'checkpoint_r370_c19_dispatcher_source_root/cp370-c19-20261009'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
ACTOR='codex:/root/backup_regression_resources'
def pin(p):
    raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,obj):
    p=Q/name
    with p.open('xb')as f:f.write(obj if type(obj)is bytes else(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def docs(v):
    if type(v)in(dict,list):
        yield v
        for x in(v.values()if type(v)is dict else v):yield from docs(x)
    elif type(v)is str:
        for t in dict.fromkeys((v,*v.splitlines())):
            try:p=json.loads(t)
            except(ValueError,TypeError):continue
            if p!=v:yield from docs(p)
def capture(chunk,name):
    calls={};matches=[];header=None
    with AUDIT.open('rb')as f:
        size=os.fstat(f.fileno()).st_size;offset=0
        while offset<size:
            line=f.readline();row=json.loads(line);p=row.get('payload',{})
            if offset==0:header=(offset,line,row)
            if type(p)is dict and p.get('type')in('custom_tool_call','function_call'):calls[p.get('call_id')]=(offset,line,row)
            if type(p)is dict and p.get('type')in('custom_tool_call_output','function_call_output'):
                if any(type(x)is dict and x.get('chunk_id')==chunk and'output'in x for x in docs(p)):
                    call=calls.get(p.get('call_id'))
                    if call is not None:matches.append((call,(offset,line,row)))
            offset+=len(line)
    assert len(matches)==1 and header[2]['payload']['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
    call,result=matches[0];rows=[header,call,result];raw=write(name+'.actual.raw.jsonl',b''.join(x[1]for x in rows))
    return dict(original_capture_ref=raw,source_audit_path=str(AUDIT),source_prefix_size_observed=size,source_line_offsets=[x[0]for x in rows],source_line_bytes=[len(x[1])for x in rows],original_line_sha256=[hashlib.sha256(x[1]).hexdigest()for x in rows],original_call_id=call[2]['payload']['call_id'],actual_chunk_id=chunk,actor=ACTOR,backend_author='/root/backup_regression_resources',source_thread_id=header[2]['payload']['id'],Root_parent_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98')
def main():
    bad=capture('138dad','original1173')
    bad.update(schema='researchos.original-failure-actual-source-binding.v1',original_ordinal=1173,actual_outer_exit=0,actual_Python_exit=0,semantic_failed=1,actual_Go_exit=None,actual_Native_exit=None,actual_SQL_exit=None,actual_model_exit=None,actual_TP_exit=None,actual_dispatcher_exit=None,full_tool_IO_ref=pin(Q/'original1173.full-tool-IO.json'),failed_script_ref=pin(Q/'seal_original1172.py'),failure='Copied numeric ordinal1168 instead of actual1172; process succeeded, emitted metadata was wrong',failure_count_reset=False)
    b1173=write('original1173.binding.json',bad)
    correction=json.loads((Q/'original1172.binding.json').read_bytes());assert correction['original_ordinal']==1168 and correction['actual_chunk_id']=='993be3'
    correction.update(original_ordinal=1172,metadata_correction_of_ref=pin(Q/'original1172.binding.json'),metadata_error_origin_ref=b1173,corrected_only=['original_ordinal'],old_bytes_preserved=True)
    corr=write('original1172.corrected.binding.json',correction)
    control=capture('12e4d9','observed-Root-argv-delta');control.update(schema='researchos.source-control-actual-host-binding.v1',actual_outer_exit=0,actual_Python_exit=0,controls_ref=pin(Q/'observed-Root-argv-delta.controls.json'),guard_ref=pin(Q/'observed-Root-argv-delta.guard.closed.json'),Native_exit=None,Go_exit=None,SQL_exit=None,TP_exit=None,model_exit=None)
    cref=write('observed-Root-argv-delta.actual.binding.json',control)
    bundle=S/'nf5-four-closed-actual-input02.root.json';assert pin(bundle)['sha256']=='2e4e45e9cc2e57aef0e431dd1a98d1308112837e2745b4683189fe6f5b2b8dcf'
    packet=json.loads(bundle.read_bytes());groups={}
    for name,row in packet['groups'].items():
        closedpath=Path(row['producer_closed_ref']['path']);assert pin(closedpath)==dict(row['producer_closed_ref'],path=str(closedpath))
        closed=json.loads(closedpath.read_bytes());observed=closed['invocation_observations'][-1]
        groups[name]=dict(input_refs=row,producer_actual_exit=observed['record']['result']['actual_exit'],producer_invocation_ref=observed['ref'],Root_outer_exit_observed=1 if name=='C19'else 0,Root_Python_exit_observed=1 if name=='C19'else 0,formal_case_accepted_delta=0)
        if name=='C19':groups[name].update(fact_status='REFUSED_EXACT_NATIVE_ARGV',producer_actual_exit=0,Root_original_failure_ordinal=1156,Root_failure_binding_ref=pin(S/'original1156.actual-root.binding.json'),reason='Actual C19 Main report and ToolRun test alternation order differs from frozen NF5 exact argv.',qualified=False,Mode_issued=False)
        elif name=='W09-G01':groups[name].update(fact_status='VERIFIED_NATIVE_OWNED_COMPILER_PREFIX_ONLY',verified_prefix_ref=pin(Q/'original1168.binding.json'),verified_prefix_guard_ref=pin(Q/'actual-review-v5-guard.closed.json'),not_completed=['Rootprepare session matrix binding','Rootrun full binding','Mode predicate facts','launcher tail'],qualified=False,Mode_issued=False)
        else:groups[name].update(fact_status='ROOT_EXIT_ZERO_OBSERVED_INDEPENDENT_REVIEW_NOT_REACHED',independent_business_gates='NOT_CHECKED_BY_THIS_REVIEW',qualified=False,Mode_issued=False)
    guardrefs=[pin(Q/'preparation.Sourceguard.closed.json'),pin(Q/'actual-review-v5-guard.closed.json'),pin(Q/'actual-review-v7-guard.closed.json'),pin(Q/'observed-Root-argv-delta.guard.closed.json')]
    for ref in guardrefs:
        g=json.loads(Path(ref['path']).read_bytes());assert g['closed']is True and g['retained_handles_count']==0 and not g['errors']and g['failure']is None
    decision=dict(schema='researchos.w09-nf5-actual-limited-independent-facts.v1',reviewer=ACTOR,source_author='codex:/root/attach_restore_independent_review',actual_executor='codex:/root',decision='LIMITED_PARTIAL_FACTS_C19_REFUSED_OTHER_REVIEW_GATES_NOT_COMPLETED',input_ref=pin(bundle),groups=groups,overall_qualified=False,Main_formal_consumption_qualified=False,Mode_finalization='MODE_FINALIZATION_REQUIRES_TRUE_FULL_REVIEWER',Mode_issued=False,formal_acceptance=False,formal_case_accepted_delta=0,Source_adoption=False,Root_execution_grant=False,new_Native_runs=0,new_Go_runs=0,new_SQL_calls=0,new_model_requests=0,new_TP_calls=0,Main_written=False,Canon_written=False,guards_closed_refs=guardrefs,continuation='Stop historical review; review new Main C19 ordering candidate. Future adoption requires four fresh Native and six current CM40 consumers.',original1172_correction_ref=corr,original1173_ref=b1173,new_controls_actual_ref=cref,unexecuted_reviewer_revision=pin(Q/'construct_session_matrix_revision.py'))
    dref=write('decision.json',decision)
    report='Independent facts only. Root G01/G02/A06 exits are observed as 0. C19 producer is 0, Root reporter is 1 and EXACT_NATIVE_ARGV is refused.\nG01 native/owned/compiler prefix is preserved by original1168; uncompleted Root/Mode/launcher checks remain NOT_CHECKED. G02/A06 independent business review was not reached.\nNo Mode, formal acceptance, Source adoption or runtime grant is issued. Main and Canon were not modified. All actually acquired review guards are closed with zero retained handles.\nOld failures and wrong1172 metadata are preserved; new correction links actual1172 and original1173 semantic error without resetting counters.\n'
    reportref=write('report.md',report.encode('utf-8'))
    members=[pin(p)for p in sorted(Q.iterdir(),key=lambda p:p.name)if p.is_file()and p.name not in('HDF.json','MF.json')]
    mf=write('MF.json',dict(schema='researchos.independent-readonly-review-manifest.v1',actor=ACTOR,members=members,member_count=len(members),excluded_self=['HDF.json','MF.json'],execution_authority=False))
    hdf=write('HDF.json',dict(schema='researchos.independent-readonly-review-HDF.v1',reviewer=ACTOR,Root_parent_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',source_thread_id='01a11cee-bf59-7a01-be0e-9f799f9b1084',manifest_ref=mf,decision_ref=dref,report_ref=reportref,input_ref=pin(bundle),actual_control_host_ref=cref,source_guard_refs=guardrefs,formal_acceptance=False,execution_authority=False,Mode_issued=False))
    print(json.dumps(dict(HDF=hdf,MF=mf,decision=dref,original1172_corrected_binding=corr,original1173_binding=b1173,original1173_raw_ref=bad['original_capture_ref'],original1173_fullIO=bad['full_tool_IO_ref']),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
