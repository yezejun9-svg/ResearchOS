from __future__ import annotations
import ctypes, hashlib, importlib.util, json, ntpath, sys
from datetime import datetime, timezone
from pathlib import Path
Q=Path(__file__).resolve().parent
ACTOR='codex:/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def need(v,c):
    if not v:raise ValueError(c)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def pin(p):
    p=Path(p);r=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(r).hexdigest(),bytes=len(r))
def checked(ref):
    r=Path(ref['path']).read_bytes();need(hashlib.sha256(r).hexdigest()==ref['sha256'] and len(r)==ref['bytes'],'PIN');return r
def save(name,value):
    p=Q/name;need(not p.exists(),'NEW_MEMBER_ONLY');p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return pin(p)
def load(p,name):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def captures():
    size=AUDIT.stat().st_size;header=None;calls={};outputs={}
    with AUDIT.open('rb') as f:
        while f.tell()<size:
            off=f.tell();raw=f.readline()
            if not raw.endswith(b'\n'):break
            row=json.loads(raw);p=row.get('payload',{})
            if header is None:
                need(row.get('type')=='session_meta' and p.get('id')==THREAD and p.get('parent_thread_id')==ROOT_THREAD,'REVIEW_REAL_IDENTITY');header=(off,raw,row)
            if row.get('type')!='response_item':continue
            cid=p.get('call_id');typ=p.get('type')
            if typ in ('custom_tool_call','function_call') and cid and 'task54_' in str(p.get('arguments',p.get('input',''))):calls[cid]=(off,raw,row)
            elif typ in ('custom_tool_call_output','function_call_output') and cid:outputs[cid]=(off,raw,row)
    rows=[];failed=None
    for cid,first in calls.items():
        if cid not in outputs:continue
        last=outputs[cid];need(first[2]['ordinal']<last[2]['ordinal'],'REAL_CALL_ORDER')
        lines=[header[1],first[1],last[1]];raw=b''.join(lines);tag=cid.removeprefix('call_')
        rp=Q/('actual-review-tool-'+tag+'.raw.jsonl');bp=Q/('actual-review-tool-'+tag+'.binding.json')
        if rp.exists():need(rp.read_bytes()==raw and bp.exists(),'EXISTING_RAW_UNCHANGED');binding=read(bp);need(binding['original_capture_ref']==pin(rp),'EXISTING_BINDING')
        else:
            need(not bp.exists(),'NEW_RAW_AND_BINDING');rp.write_bytes(raw)
            binding=dict(source_actor=ACTOR,source_thread_id=THREAD,source_parent_thread_id=ROOT_THREAD,source_audit_path=str(AUDIT),source_prefix_size_observed=size,source_line_offsets=[header[0],first[0],last[0]],source_line_bytes=[len(v) for v in lines],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in lines],original_capture_ref=pin(rp),original_call_id=cid,actual_tool_name=first[2]['payload'].get('name'))
            save(bp.name,binding)
        row=dict(binding_ref=pin(bp),raw_ref=pin(rp),actual_tool_name=first[2]['payload'].get('name'))
        rows.append(row)
        args=str(first[2]['payload'].get('arguments',first[2]['payload'].get('input','')))
        out=str(last[2]['payload'].get('output'))
        if 'store("task54_review_prepare_input"' in args and 'await tools.exec_command(a)' in args and '8a177d' in out:
            need(failed is None,'ONE_1056_TOOLPAIR');failed=row
    need(failed is not None and rows,'REAL_ORIGINAL1056_FOUND');return rows,failed
def main():
    basis=read(Q/'verified-source-basis.index.json');members={Path(x['path']).name:x for x in basis['members']};h=json.loads(checked(basis['source_hdf_ref']))
    source_inputs=json.loads(checked(h['source_inputs_ref']));resources=json.loads(checked(source_inputs['runtime_resources_ref']));runtime=json.loads(checked(members['runtime-closure-control.json']))
    controls=read(Q/'independent-controls.json');static=read(Q/'static-and-host-evidence.json')
    need(controls['Source_checks']==65 if 'Source_checks' in controls else controls.get('total_Source_checks')==65,'65_CONTROL_COUNT')
    need(static['status']=='PASS_SOURCE_ONLY' and len(static['source_capture_original_pairs'])==18,'STATIC_ACTUAL_EVIDENCE')
    actual,failed=captures();capture_index=save('actual-review-tool-capture-index.json',dict(schema='researchos.independent-source-actual-tool-capture-index.v1',source_actor=ACTOR,source_thread_id=THREAD,source_parent_thread_id=ROOT_THREAD,actual_pairs=actual,original1056_pair=failed,postseal_actual_toolpair_requires_external_capture=True,SQL_queries=0,new_native_children=0))
    failure=save('failure-origin.1056.json',dict(schema='researchos.failure-origin.v1',original_ordinal=1056,assigned_by='codex:/root',chunk_id='8a177d',actual_outer_exit=1,actual_python_exit=1,python_exit_marker_observed=True,actual_Go_exit=None,actual_native_exit=None,actual_SQL_exit=None,actual_dispatcher_exit=None,actual_model_exit=None,actual_host_raw_ref=failed['raw_ref'],actual_host_binding_ref=failed['binding_ref'],complete_original_tool_IO_ref=pin(Q/'failure-8a177d.complete-original-IO.json'),failed_script_ref=pin(Q/'prepare_review_evidence.py'),revision_script_ref=pin(Q/'prepare_review_evidence_revision.py'),revision_actual_exit=0,original_failed_input_retried=False,Source_caller_problem=False,original1025_result='FAILED_RETAINED',failure_counter_reset=False))
    contract=json.loads(checked(h['calling_contract_ref']))
    calling=save('next-Root-calling-contract.json',dict(schema='researchos.public22-existing-independent-next-Root-calling-contract.v1',decision='ACCEPTED_SOURCE_ONLY',caller_ref=h['caller_ref'],source_hdf_ref=basis['source_hdf_ref'],source_mf_ref=basis['source_mf_ref'],Source_author=h['source_author'],reviewer_actor=ACTOR,actual_backend_peer_author='/root/backup_regression_resources',Root_actor='codex:/root',Root_thread=ROOT_THREAD,Root_source_audit_path=contract['audit_policy']['Root_source_audit_path'],source_contract_ref=h['calling_contract_ref'],registration_request_schema=contract['Root_registration_request_schema'],registration_required_fields=contract['Root_registration_request_required_fields'],actual_request_schema=contract['Root_actual_schema'],actual_required_fields=contract['Root_actual_required_fields'],activation_required_fields=contract['Root_activation_required_fields'],argv_template=contract['argv_template'],modes=contract['modes'],revision_policy=contract['revision_policy'],source_review_HDF_fields=contract['source_review_HDF_fields'],runtime_resources_ref=h['runtime_resources_ref'],future_Root_scope=None,future_lease=None,future_registration_request=None,future_actual_request=None,execution_grant=False,formal_acceptance=False,original1025_result='FAILED_RETAINED',original1043_result='FAILED_RETAINED',original1056_retained=True,new_native_children_expected_for_existing_observation=0))
    now=datetime.now(timezone.utc).isoformat()
    decision=save('decision.json',dict(schema='researchos.public22-existing-root-independent-source-decision.v1',decision='ACCEPTED_SOURCE_ONLY',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author=h['source_author'],source_hdf_ref=basis['source_hdf_ref'],source_mf_ref=basis['source_mf_ref'],caller_ref=h['caller_ref'],source_inputs_ref=h['source_inputs_ref'],calling_contract_ref=h['calling_contract_ref'],runtime_resources_ref=h['runtime_resources_ref'],readonly_only=True,original1025_result='FAILED_RETAINED',original1043_result='FAILED_RETAINED',execution_grant=False,formal_acceptance=False,parent_acceptance=False,reviewed_utc=now,review_controls_ref=pin(Q/'independent-controls.json'),static_and_host_evidence_ref=pin(Q/'static-and-host-evidence.json'),actual_tool_capture_index_ref=capture_index,next_Root_calling_contract_ref=calling,report_ref=pin(Q/'report.md'),new_review_mechanical_failure_ref=failure,Source_checks=65,SQL_queries=0,new_native_children=0,Go_runs=0,dispatcher_runs=0,model_calls=0,actual_registration=False,findings=[],limits=['Synthetic authority controls are Source only; future Root issuer/Scope/lease/request are not created or qualified.','No duplicate SQL query: prior accepted leaf readonly SQL diagnostic is referenced; Root future readonly run remains unobserved.']))
    allrefs={}
    for ref in [basis['source_hdf_ref'],basis['source_mf_ref'],*basis['members'],*source_inputs['source_resource_refs'],*resources['resource_refs'],*runtime['verified_resource_refs']]:
        key=ntpath.normcase(ntpath.normpath(ref['path']))
        if key in allrefs:need((allrefs[key]['sha256'],allrefs[key]['bytes'])==(ref['sha256'],ref['bytes']),'REF_CONFLICT')
        allrefs[key]=ref
    for p in Q.iterdir():
        if p.is_file():allrefs[ntpath.normcase(ntpath.normpath(str(p)))]=pin(p)
    guardlib=load(Q/'read_source_basis.py','final_independent_source_guard_only');guard=guardlib.Guard();closed=False
    try:
        for ref in allrefs.values():guard.read(ref['path'],ref)
        closure=guard.close();closed=True
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
    need(closure['all_handles_closed'] is True and closure['retained_handles']==0 and closure['live_Canon_handles']==0,'ALL_FINAL_GUARDS_CLOSED')
    guardref=save('final-source-and-review.guard.closed.json',closure)
    files=sorted(p for p in Q.iterdir() if p.is_file());mf=save('MF.json',dict(schema='researchos.independent-source-review-manifest.v1',actor_id=ACTOR,members=[pin(p) for p in files],excluded=['HDF.json','MF.json','Any later external postseal actual toolpair supplement'],reason='HDF references MF; the sealing process actual return is available only after sealing and must be externally captured.'))
    hdr=save('HDF.json',dict(schema='researchos.public22-existing-root-independent-source-review-handoff.v1',status='ACCEPTED_SOURCE_ONLY',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author=h['source_author'],reviewed_utc=now,manifest_ref=mf,source_decision_ref=decision,source_hdf_ref=basis['source_hdf_ref'],source_mf_ref=basis['source_mf_ref'],caller_ref=h['caller_ref'],calling_contract_ref=h['calling_contract_ref'],runtime_resources_ref=h['runtime_resources_ref'],review_controls_ref=pin(Q/'independent-controls.json'),final_guard_closed_ref=guardref,actual_tool_capture_index_ref=capture_index,report_ref=pin(Q/'report.md'),next_Root_calling_contract_ref=calling,original1056_ref=failure,original1056_actual_host_raw_ref=failed['raw_ref'],original1056_actual_host_binding_ref=failed['binding_ref'],original1056_complete_IO_ref=pin(Q/'failure-8a177d.complete-original-IO.json'),all_guards_closed=True,retained_handles=0,live_Canon_handles=0,Source_checks=65,SQL_queries=0,new_native_children=0,Go_runs=0,dispatcher_runs=0,model_calls=0,Main_Canon_oldcase_Source_writes=0,private_owner_credential_key_reads=0,actual_registration=False,original1025_result='FAILED_RETAINED',original1043_result='FAILED_RETAINED',execution_grant=False,formal_acceptance=False,parent_acceptance=False,STOP=True))
    need(read(Q/'HDF.json')['manifest_ref']==pin(Q/'MF.json'),'SEALED_MF_BINDING')
    for ref in read(Q/'MF.json')['members']:checked(ref)
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.GetFileAttributesW.argtypes=[ctypes.c_wchar_p];api.GetFileAttributesW.restype=ctypes.c_uint32;api.SetFileAttributesW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32];api.SetFileAttributesW.restype=ctypes.c_int
    for p in Q.iterdir():
        if p.is_file():
            attrs=api.GetFileAttributesW(str(p));need(attrs!=0xffffffff and api.SetFileAttributesW(str(p),attrs|1)!=0,'REVIEW_MEMBER_READONLY')
    print(json.dumps(dict(decision='ACCEPTED_SOURCE_ONLY',review_hdf_ref=hdr,review_mf_ref=mf,review_decision_ref=decision,report_ref=pin(Q/'report.md'),original1056_ref=failure,original1056_raw_ref=failed['raw_ref'],original1056_binding_ref=failed['binding_ref'],original1056_complete_IO_ref=pin(Q/'failure-8a177d.complete-original-IO.json'),members=len(files),guard_closed=True,retained_handles=0,execution_grant=False,formal_acceptance=False,STOP=True),ensure_ascii=False),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1',flush=True);raise
    print('ROOT_PYTHON_EXIT=0',flush=True)

