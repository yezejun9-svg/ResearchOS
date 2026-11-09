from __future__ import annotations
import ast, ctypes, hashlib, importlib.util, json, ntpath
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
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def checked(ref):
    raw=Path(ref['path']).read_bytes();need(hashlib.sha256(raw).hexdigest()==ref['sha256'] and len(raw)==ref['bytes'],'EXACT_PIN');return raw
def save(name,value):
    p=Q/name
    with p.open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
    return pin(p)
def load(p,name):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def capture():
    size=AUDIT.stat().st_size;head=None;calls={};outputs={}
    with AUDIT.open('rb') as f:
        while f.tell()<size:
            off=f.tell();raw=f.readline()
            if not raw.endswith(b'\n'):break
            row=json.loads(raw);p=row.get('payload',{})
            if head is None:
                need(row['type']=='session_meta' and p['id']==THREAD and p['parent_thread_id']==ROOT_THREAD,'ACTUAL_SOURCE_PARENT');head=(off,raw,row)
            if row.get('type')!='response_item':continue
            cid=p.get('call_id');typ=p.get('type')
            if typ in ('custom_tool_call','function_call') and cid and 'task61_' in str(p.get('input',p.get('arguments',''))):calls[cid]=(off,raw,row)
            elif typ in ('custom_tool_call_output','function_call_output') and cid:outputs[cid]=(off,raw,row)
    pairs=[];failed=None
    for cid,first in calls.items():
        if cid not in outputs:continue
        last=outputs[cid];need(first[2]['ordinal']<last[2]['ordinal'],'ACTUAL_CALL_ORDER');lines=[head[1],first[1],last[1]]
        tag=cid.removeprefix('call_');rp=Q/('actual-Source-'+tag+'.raw.jsonl')
        with rp.open('xb') as f:f.write(b''.join(lines))
        binding=save('actual-Source-'+tag+'.binding.json',dict(schema='researchos.actual-source-tool-binding.v1',source_actor=ACTOR,source_thread_id=THREAD,source_parent_thread_id=ROOT_THREAD,source_audit_path=str(AUDIT),source_prefix_size_observed=size,source_line_offsets=[head[0],first[0],last[0]],source_line_bytes=[len(v) for v in lines],original_line_sha256=[hashlib.sha256(v).hexdigest() for v in lines],original_capture_ref=pin(rp),original_call_id=cid,actual_tool_name=first[2]['payload'].get('name')))
        pair=dict(raw_ref=pin(rp),binding_ref=binding);pairs.append(pair)
        args=str(first[2]['payload'].get('input',first[2]['payload'].get('arguments','')));out=str(last[2]['payload'].get('output'))
        if 'store("task61_construct_input"' in args and 'await tools.exec_command(a)' in args and '52671c' in out:
            need(failed is None,'UNIQUE_ORIGINAL1064');failed=pair
    need(failed is not None and pairs,'FULL_ORIGINAL1064_FOUND');return pairs,failed,head[2]['payload']
def main():
    result=read(Q/'construction-result.json');inputs=read(Q/'source-inputs.json');controls=read(Q/'finite-M4-source-controls.json')
    need(controls['count']==37 and all(x['status'] in ('PASS_SOURCE_ONLY','PASS_EXPECTED_REJECTION') for x in controls['controls']),'FINITE_NEW_CONTROLS')
    inv=read(Q/'exact-inverse.json');need(inv['full_original_byte_inverse'] and inv['old_byte_sha256']==inv['inverse_sha256'],'FULL_INVERSE')
    pairs,failed,identity=capture()
    index=save('actual-Source-tool-capture-index.json',dict(schema='researchos.main23-M4-actual-source-tool-index.v1',source_actor=ACTOR,source_thread_id=THREAD,actual_pairs=pairs,original1064_pair=failed,sealing_tool_return_requires_external_postseal_capture=True,execution_grant=False,formal_acceptance=False))
    failure=save('failure-origin.1064.json',dict(schema='researchos.failure-origin.v1',original_ordinal=1064,assigned_by='codex:/root',chunk_id='52671c',actual_outer_exit=1,actual_python_exit=1,ROOT_PYTHON_EXIT_marker_observed=True,Go_exit=None,Native_exit=None,SQL_exit=None,TP_exit=None,dispatcher_exit=None,model_exit=None,complete_original_IO_ref=pin(Q/'failure-52671c.complete-original-IO.json'),raw_hostpair_ref=failed['raw_ref'],binding_ref=failed['binding_ref'],failed_script_ref=pin(Q/'construct_M4_source.py'),failure_guard_serialized_close_ref=None,failed_attempt_Finally_close_source_present=True,failed_attempt_close_observation_not_serialized=True,candidate_created_in_failed_attempt=False,revision_script_ref=pin(Q/'construct_M4_source_revision.py'),revision_exit=0,old_failed_input_retried=False,failure_counter_reset=False))
    caller=result['caller_ref'];tree=ast.parse(checked(caller))
    static=save('static-verification.json',dict(schema='researchos.main23-M4-minimum-static-verification.v1',caller_ref=caller,inverse_ref=result['inverse_ref'],new_logic_functions=inv['changed_top_level_functions'],unchanged_function_names=inv['unchanged_function_names'],Root_tool_structured_documents_unchanged=inv['Root_tool_structured_documents_byte_unchanged'],relative_N_unchanged=inv['relative_N_unchanged'],function_lines={n.name:dict(start=n.lineno,end=n.end_lineno) for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))},new_finite_controls=37,old_controls_reused_not_rerun=inputs['old_source_controls_reused_not_rerun'],Task58_CHANGES_REQUIRED_retained=True,actual_source_actor=ACTOR,actual_Source_identity=identity,Main_Canon_oldSource_writes=0,Root_qualification_Scope_lease_grant_created=False))
    constructor=load(Q/'construct_M4_source_revision.py','seal_Source_guard_no_main');guard=constructor.Guard();closed=False;refs={}
    for ref in [*inputs['references'],pin(Q/'construction-result.json'),*result.values()]:
        if isinstance(ref,dict) and set(ref)=={'path','sha256','bytes'}:refs[ntpath.normcase(ntpath.normpath(ref['path']))]=ref
    for p in Q.iterdir():
        if p.is_file():refs[ntpath.normcase(ntpath.normpath(str(p)))]=pin(p)
    try:
        for ref in refs.values():guard.read(ref['path'],ref)
        closure=guard.close();closed=True
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
    need(closure['all_handles_closed'] is True and closure['retained_handles']==0 and closure['live_Canon_handles']==0,'ALL_SOURCE_GUARDS_CLOSED')
    guardref=save('finite-Source-guard.final.closed.json',closure)
    files=sorted(p for p in Q.iterdir() if p.is_file());mf=save('MF.json',dict(schema='researchos.main23-root-caller-M4-source-manifest.v1',source_author=ACTOR,members=[pin(p) for p in files],excluded=['MF.json','HDF.json','A later external sealing tool return capture, available only after sealing'],all_Source_guards_closed=True,live_Canon_handles=0,authority='NONE'))
    now=datetime.now(timezone.utc).isoformat()
    hdf=save('HDF.json',dict(schema='researchos.main23-root-caller-registration-source-hdf.v4',status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING',source_author=ACTOR,source_thread_id=THREAD,parent_root_thread_id=ROOT_THREAD,actual_agent_path='/root/backup_regression_resources',actual_Source_identity=identity,builder_source_author='codex:/root/native_temp_independent_review',manifest_ref=mf,caller_ref=caller,registrar_ref=caller,contract_ref=result['contract_ref'],source_inputs_ref=result['source_inputs_ref'],base_hdf_ref=result['base_hdf_ref'],base_mf_ref=result['base_mf_ref'],Task58_hdf_ref=result['Task58_hdf_ref'],Task58_mf_ref=result['Task58_mf_ref'],Task58_decision_ref=result['Task58_decision_ref'],inverse_ref=result['inverse_ref'],static_verification_ref=static,report_ref=pin(Q/'Source-report.md'),Source_guard_ref=guardref,finite37_controls_ref=pin(Q/'finite-M4-source-controls.json'),finite_controls_guard_ref=pin(Q/'finite-M4-controls.guard.closed.json'),construction_guard_ref=pin(Q/'construction-input.guard.closed.json'),actual_Source_tool_index_ref=index,original1064_ref=failure,original1064_complete_IO_ref=pin(Q/'failure-52671c.complete-original-IO.json'),original1064_raw_hostpair_ref=failed['raw_ref'],original1064_binding_ref=failed['binding_ref'],old_controls_reused_not_rerun=inputs['old_source_controls_reused_not_rerun'],created_utc=now,Source_only=True,authority='NONE',independent_acceptance=False,all_Source_guards_closed=True,retained_handles=0,live_Canon_held_handles=0,future_qualification_ref=None,future_Scope_ref=None,future_lease_ref=None,future_request_ref=None,future_Root_grant_ref=None,Main_Canon_oldSource_T_writes=0,Go_runs=0,Native_jobs=0,SQL_runs=0,TP_runs=0,dispatcher_runs=0,model_calls=0,private_credential_key_owner_reads=0,formal_acceptance=False,parent_acceptance=False,author_STOP_after_seal=True))
    need(read(Q/'HDF.json')['manifest_ref']==pin(Q/'MF.json'),'HDF_MF_EXACT')
    for ref in read(Q/'MF.json')['members']:checked(ref)
    api=ctypes.WinDLL('kernel32',use_last_error=True);api.GetFileAttributesW.argtypes=[ctypes.c_wchar_p];api.GetFileAttributesW.restype=ctypes.c_uint32;api.SetFileAttributesW.argtypes=[ctypes.c_wchar_p,ctypes.c_uint32];api.SetFileAttributesW.restype=ctypes.c_int
    for p in Q.iterdir():
        if p.is_file():
            flags=api.GetFileAttributesW(str(p));need(flags!=0xffffffff and api.SetFileAttributesW(str(p),flags|1)!=0,'IMMUTABLE_SOURCE_MEMBERS')
    print(json.dumps(dict(status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING',HDF_ref=hdf,MF_ref=mf,caller_ref=caller,contract_ref=result['contract_ref'],inverse_ref=result['inverse_ref'],controls_ref=pin(Q/'finite-M4-source-controls.json'),Source_guard_ref=guardref,original1064_ref=failure,original1064_raw_ref=failed['raw_ref'],original1064_binding_ref=failed['binding_ref'],original1064_complete_IO_ref=pin(Q/'failure-52671c.complete-original-IO.json'),member_count=len(files),guards_closed=True,retained_handles=0,authority='NONE',STOP=True),ensure_ascii=False),flush=True)
if __name__=='__main__':
    try:main()
    except BaseException:print('ROOT_PYTHON_EXIT=1',flush=True);raise
    print('ROOT_PYTHON_EXIT=0',flush=True)

