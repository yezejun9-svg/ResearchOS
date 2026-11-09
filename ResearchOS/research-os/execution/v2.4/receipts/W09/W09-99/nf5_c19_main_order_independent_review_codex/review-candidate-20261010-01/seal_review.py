import hashlib,json,os,sys,traceback
from pathlib import Path
Q=Path(__file__).resolve().parent
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
        for text in dict.fromkeys((v,*v.splitlines())):
            try:p=json.loads(text)
            except(ValueError,TypeError):continue
            if p!=v:yield from docs(p)
def main():
    calls={};matches=[];header=None
    with AUDIT.open('rb')as f:
        size=os.fstat(f.fileno()).st_size;offset=0
        while offset<size:
            line=f.readline();row=json.loads(line);payload=row.get('payload',{})
            if offset==0:header=(offset,line,row)
            if type(payload)is dict and payload.get('type')in('custom_tool_call','function_call'):calls[payload.get('call_id')]=(offset,line,row)
            if type(payload)is dict and payload.get('type')in('custom_tool_call_output','function_call_output'):
                if any(type(d)is dict and d.get('chunk_id')=='8a685f'and'output'in d for d in docs(payload)):
                    call=calls.get(payload.get('call_id'))
                    if call is not None:matches.append((call,(offset,line,row)))
            offset+=len(line)
    assert len(matches)==1 and header[2]['payload']['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
    call,result=matches[0];rows=[header,call,result];raw=write('actual-review.raw.jsonl',b''.join(x[1]for x in rows))
    binding=write('actual-review.binding.json',dict(schema='researchos.independent-source-review-actual-host-binding.v1',actor=ACTOR,backend_author='/root/backup_regression_resources',source_thread_id=header[2]['payload']['id'],Root_parent_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',source_audit_path=str(AUDIT),source_prefix_size_observed=size,source_line_offsets=[x[0]for x in rows],source_line_bytes=[len(x[1])for x in rows],original_line_sha256=[hashlib.sha256(x[1]).hexdigest()for x in rows],original_capture_ref=raw,actual_call_id=call[2]['payload']['call_id'],actual_chunk_id='8a685f',actual_outer_exit=0,actual_Python_exit=0,actual_Go_exit=None,actual_Native_exit=None,actual_SQL_exit=None,actual_model_exit=None,actual_TP_exit=None,actual_dispatcher_exit=None,controls_source_ref=pin(Q/'review_candidate.py'),full_tool_IO_ref=pin(Q/'complete-tool-IO.reencoded.json'),Source_only=True,execution_grant=False,formal_acceptance=False))
    d=json.loads((Q/'decision.unsealed.json').read_bytes());assert d['decision']=='ACCEPTED_SOURCE_ONLY'and d['checks_passed']==8 and d['execution_grant']is False
    g=json.loads(Path(d['guard_ref']['path']).read_bytes());assert g['closed']is True and g['retained_handles_count']==0 and g['failure']is None and not g['errors']
    d.update(actual_reviewer_host_ref=binding,Root_post_delivery_capture_ref=None,review_bound_to_this_actual_Source=True,Root_adoption_requires_actual_new_request_and_authority=True)
    decision=write('decision.json',d)
    report=write('report.md',('ACCEPTED_SOURCE_ONLY. Independent reviewer Backup differs from candidate author Full and Root executor.\nEight new candidate checks passed; all '+str(len(g['entries']))+' held input resources closed with zero retained handles. Previous 18 advisory properties and six author publication checks were not rerun.\nThe complete candidate changes only the case-only selected expression at retrieval.py:178; full inverse equals the original Main bytes. C19 order becomes ExplicitOriginAndUnknown then ChainInvalidation, exactly the frozen two tests and five assertion IDs. All other bytes, gates, thresholds and check branches remain unchanged.\nThe adoption contract requires real Root peer observation, a fresh request/owner/lease, an exclusive target with exact before SHA/bytes, complete original-byte archive and finally closure. It is a Source contract; no adoption executable or live authority was issued.\nAny adoption changes Source21: four previous Native reports become historical. Root must publish and independently review the fresh Source generation, qualify fresh resources/scopes, run four fresh Native selectors and all six current CM40 routes. No current Source21, runtime, Mode or formal qualification is granted by this review.\n').encode('utf-8'))
    members=[pin(p)for p in sorted(Q.iterdir(),key=lambda p:p.name)if p.is_file()and p.name not in('HDF.json','MF.json')]
    mf=write('MF.json',dict(schema='researchos.w09-c19-main-order-independent-source-review-manifest.v1',reviewer=ACTOR,members=members,member_count=len(members),excluded_self=['MF.json','HDF.json'],execution_grant=False,formal_acceptance=False))
    hdf=write('HDF.json',dict(schema='researchos.w09-c19-main-order-independent-source-review-HDF.v1',decision='ACCEPTED_SOURCE_ONLY',reviewer=ACTOR,reviewer_backend='/root/backup_regression_resources',reviewer_thread_id='01a11cee-bf59-7a01-be0e-9f799f9b1084',Root_parent_thread_id='01a11007-5233-7ca1-b71f-9e9e5ce84c98',source_author='codex:/root/full_w09_source_review',source_hdf_ref=d['candidate_HDF_ref'],source_mf_ref=d['candidate_MF_ref'],contract_ref=d['candidate_contract_ref'],candidate_ref=d['candidate_ref'],manifest_ref=mf,decision_ref=decision,report_ref=report,guard_ref=d['guard_ref'],actual_reviewer_host_ref=binding,checks_passed=8,Source21_qualification=False,runtime_qualification=False,Mode_qualification=False,RootScope_lease_or_qualification_issued=False,formal_acceptance=False,execution_grant=False,Main_adopted=False))
    print(json.dumps(dict(HDF=hdf,MF=mf,decision=decision,actual_review_host_ref=binding,Source_only=True,execution_grant=False,formal_acceptance=False),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
