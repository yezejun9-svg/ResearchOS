"""Seal completed Task98 Source review and original host records, no runtime stage."""
import ast, hashlib, json, ntpath, sys, traceback, types
from pathlib import Path
from datetime import datetime, timezone
Q=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
AUTHOR='codex:/root/backup_regression_resources'
BACKEND='/root/backup_regression_resources'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def need(ok,code):
    if not ok: raise AssertionError(code)
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def write(name,value):
    with (Q/name).open('xb') as f:f.write((json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n').encode('utf-8'))
    return pin(Q/name)
def raw_new(path,raw):
    with Path(path).open('xb') as f:f.write(raw)
    return pin(path)
def capture():
    outdir=Q/'actual-reviewer-host';outdir.mkdir()
    with AUDIT.open('rb') as f:
        first=f.readline();header=json.loads(first);identity=header['payload']
        need(header['type']=='session_meta' and identity['id']==THREAD and identity['agent_path']==BACKEND and identity['parent_thread_id']==ROOT_THREAD,'REAL_REVIEWER_HEADER')
        f.seek(0,2);prefix=f.tell()
        # Only a finite recent Source prefix, not an unbounded conversation replay.
        start=max(len(first),prefix-16*1024*1024);f.seek(start)
        if start!=len(first):f.readline()
        scan_start=f.tell();calls={};completed=[];original=[]
        while f.tell()<prefix:
            at=f.tell();raw=f.readline()
            if not raw or at+len(raw)>prefix:break
            row=json.loads(raw);value=row.get('payload')
            if row.get('type')!='response_item' or type(value)is not dict:continue
            kind=value.get('type')
            if kind in ('custom_tool_call','function_call'):
                source=value.get('input',value.get('arguments',''))
                if type(source)is str and 'task98_' in source:
                    need(type(value.get('call_id'))is str,'TRUE_CALL_ID')
                    calls[value['call_id']]=(at,raw,row,source)
            elif kind in ('custom_tool_call_output','function_call_output') and value.get('call_id') in calls:
                ca,cr,call,source=calls.pop(value['call_id']);cid=value['call_id']
                need(row['timestamp']>=call['timestamp'],'ACTUAL_RETURN_CAUSAL_ORDER')
                raw_ref=raw_new(outdir/(cid+'.raw.jsonl'),first+cr+raw)
                binding={'schema':'researchos.Source-author-actual-tool-binding.v1','Source_author':AUTHOR,'actual_agent_path':BACKEND,'Source_author_thread':THREAD,'actual_parent_thread':ROOT_THREAD,'source_audit_path':str(AUDIT),'source_prefix_bytes':prefix,'source_line_offsets':[0,ca,at],'source_line_bytes':[len(first),len(cr),len(raw)],'source_line_sha256':[hashlib.sha256(x).hexdigest() for x in (first,cr,raw)],'original_capture_ref':raw_ref,'actual_call_id':cid,'actual_tool_name':call['payload'].get('name'),'actual_tool_type':call['payload']['type'],'tool_call_utc':call['timestamp'],'tool_output_utc':row['timestamp'],'capture_is_raw_original_bytes':True,'Root_issuer':False,'formal_acceptance':False,'execution_grant':False}
                br=write('actual-reviewer-host/'+cid+'.binding.json',binding)
                pair={'raw_ref':raw_ref,'binding_ref':br,'call_id':cid,'actual_tool_name':binding['actual_tool_name']}
                completed.append(pair)
                if 'store("task98_review_run_input",v)' in source and 'c20c0e' in raw.decode('utf-8'):
                    original.append(pair)
    need(len(completed)>=8,'FINITE_REAL_SOURCE_PAIRS')
    need(len(original)==1,'EXACT_ORIGINAL1144_CALL_RETURN')
    write('original1144.failure-origin.json',{'schema':'researchos.original-failure-origin.v1','original_ordinal':1144,'actual_chunk_id':'c20c0e','capture_kind':'ACTUAL_PROCESS_TOOL_RESULT','actual_host_binding_ref':original[0]['binding_ref'],'actual_raw_ref':original[0]['raw_ref'],'full_original_IO_ref':pin(Q/'original1144.actual-tool-IO.values.json'),'failed_script_ref':pin(Q/'review_source.py'),'actual_outer_exit':1,'actual_Python_exit':1,'ROOT_PYTHON_EXIT_marker':1,'Go_exit':None,'Native_exit':None,'SQL_exit':None,'dispatcher_exit':None,'model_exit':None,'SourceGuard':'NOT_ACQUIRED','reason':'AST literal_eval encountered actual TRUSTED keys Name GUARD/TP/OWNED; original script/IO preserved. Later resolver allows exactly these three declared string constants.','original_failure_counter_not_reset':True,'Main_Canon_old_Source_writes':0,'runtime_stages_called':[]})
    return {'schema':'researchos.w09-bridge-reviewer-actual-source-audit.v1','reviewer_actor':AUTHOR,'actual_backend':BACKEND,'actual_thread':THREAD,'actual_parent_thread':ROOT_THREAD,'source_audit_path':str(AUDIT),'finite_scan_start_offset':scan_start,'source_prefix_bytes':prefix,'session_meta_ref':raw_new(outdir/'session-meta.raw.jsonl',first),'completed_tool_pairs':completed,'completed_pair_count':len(completed),'pending_final_sealer_calls_not_fabricated':sorted(calls),'pending_final_sealer_boundary':'Final sealer call+return does not yet exist as a completed pair. Root retains the eventual actual returned pair and this subsequent peer Final; neither is prefilled here.','Root_issuer':False,'execution_grant':False,'formal_acceptance':False}
def main():
    decision=json.loads((Q/'decision.json').read_bytes());controls=json.loads((Q/'finite-review-controls.json').read_bytes())
    prior=json.loads((Q/'source-guard.closed.json').read_bytes())
    need(decision['decision']=='CHANGES_REQUIRED' and len(decision['findings'])==2 and controls['passed']==24 and controls['failed']==0,'REAL_REVIEW_DECISION')
    need(prior['closed']is True and prior['retained_handles_count']==0 and prior['verification']=='PASSED' and not prior['errors'],'PRIOR_GUARD_CLOSED')
    io=json.loads((Q/'actual-tool-IO.values.json').read_bytes())
    need(not io['missing_in_memory_pairs'] and len(io['records'])==29,'COMPLETE_REAL_TOOL_VALUES')
    audit_ref=write('reviewer-source-audit.json',capture())
    compiled=[]
    for path in sorted(Q.glob('*.py')):
        raw=path.read_bytes();ast.parse(raw);compile(raw,str(path),'exec');compiled.append(pin(path))
    static_ref=write('static-review-boundary.json',{'schema':'researchos.w09-bridge-review-boundary.v1','AST_compile_refs':compiled,'independent_reviewer':AUTHOR,'subject_Source_author':'codex:/root/attach_restore_independent_review','independent_of_subject_Source_author':True,'Main_and_bridge_stages_executed':[],'Source_pure_predicate_checks':24,'old18_or_26_or_other_historical_controls_rerun':False,'Root_issuer_or_Scope_or_runtime_qualification_created':False,'product_Native_Go_SQL_dispatcher_model_TP':0,'Canon_Main_subject_Source_writes':0,'live_CP_OW_handles_held':False,'Native_fixture_NOT_CREATED_NOT_RUN':True,'existing_physical_C_parents_resource_only':True,'original1144_retained':True,'full_IO_representation':'Stored tool values are JSON re-encoded, separate raw host records preserve exact bytes.','formal_acceptance':False,'execution_grant':False})
    report='''Bridge02 独立审查结论：CHANGES_REQUIRED，仅 Source/runtime 接口审查，不签运行或正式接受。

BRIDGE-ROLE-001：Bridge canonical AUTHOR 进入 propose.source_actor，并必须进入 RoleRegistry.source_authors。Main 先要求 pinned origin.source_actor 与 proof.actor_id 相同，再要求真实 peer payload.author 与 proof.actor_id 相同。现有真实 Root 三行表明 Attach backend 是 /root/attach_restore_independent_review，canonical codex: 名不能替代。该旧 peer 仅证明真实身份，不是 Bridge95 资格。保持 canonical Source 元数据，角色来源用精确 backend 名与真实固定映射；不得改 Main/伪造或重标原记录。

BRIDGE-TEMP-002：consume 对 TEMP/TMP 使用 repo-only physical()；合法的真正 C 盘 .researchos/w09-native-v5 资源父目录因此被拒绝。Main verify_mode 的 FIXTURE 支路按当前 tempfile.gettempdir() 包含实际 state root；未来 C fixture 使用 R/.local 的 TEMP 也会拒绝。需受限公开父目录策略，并使运行 Bridge precheck/propose/assemble/check/derive 的 Python 与消费者 OwnedJob 使用同一真实 TEMP/TMP，先于 tempfile 缓存。AppData 候选 original1142 曾被观察为 alias；Native fixture/scratch 一律 NOT_CREATED/NOT_RUN，这里只核 C 盘资源父目录与纯 Windows 路径谓词。

十阶段均逐项记录在 decision.json。六 route/四 selector、current Source21/CM40、真正独立 mode 资格、Root scope/owner/有限 lease、Root current4 CAS、原返结果先于 output refs、真实 OwnedJob 终态、真正 RoleRegistry/capture、Main verify_owner 与实际 SS→derive 门均仍在。旧作者18控制及26guards不重跑；24项新有限 AST/纯谓词检查通过，无 Root 阶段、产品或 SQL 运行。

original1144 是本次审查脚本 literal_eval 对真实 Name key 的机械失败，outer/Python1/1、其他NULL，未 acquire guard；旧脚本与原完整IO/raw/binding保存，新 resolver 只允许 GUARD/TP/OWNED 三字面常量，完整 inverse 保留。成功复核 SourceGuard closed0/PASSED。Root 要先获得全新两P1最小 Source 修订与非作者复核，再做实际 scope/runtime 绑定；本包不给 Bridge02 启动资格。
'''
    report_ref=raw_new(Q/'report.md',report.encode('utf-8'))
    source_pins=json.loads((Q/'input-source-pins.json').read_bytes())
    guard_ref=next(ref for ref in source_pins['references'] if Path(ref['path']).name=='source_read_guard.py')
    raw=Path(guard_ref['path']).read_bytes();need(hashlib.sha256(raw).hexdigest()==guard_ref['sha256'] and len(raw)==guard_ref['bytes'],'GUARD_PIN')
    gm=types.ModuleType('task98_full_seal_guard');exec(compile(raw,guard_ref['path'],'exec'),gm.__dict__)
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
    refs=source_pins['references']+[pin(p) for p in sorted(Q.rglob('*')) if p.is_file()]
    unique={}
    for ref in refs:
        key=ntpath.normcase(ntpath.normpath(ref['path'].replace('/','\\')))
        if key in unique:need(unique[key]['sha256']==ref['sha256'] and unique[key]['bytes']==ref['bytes'],'FULL_SOURCE_PIN_CONFLICT')
        else:unique[key]=ref
    try:guard.acquire([unique[k] for k in sorted(unique)])
    finally:
        closed=guard.close();closed_ref=write('full-source-guard.closed.json',closed)
    need(closed['closed']is True and closed['retained_handles_count']==0 and closed['verification']=='PASSED' and not closed['errors'],'FULL_REVIEW_SOURCE_GUARD_CLOSED')
    members=[pin(p) for p in sorted(Q.rglob('*')) if p.is_file() and p.name not in ('HDF.json','MF.json')]
    mf_ref=write('MF.json',{'schema':'researchos.source-manifest.v1','reviewer_actor':AUTHOR,'members':members,'member_count':len(members),'exclusions':['MF.json self digest','HDF.json references finalized MF','Final sealer actual returned toolpair and peer delivery occur after sealing; Root independently captures originals.'],'immutable_after_publish':True,'execution_grant':False,'formal_acceptance':False})
    hdf_ref=write('HDF.json',{'schema':'researchos.w09-bridge-independent-source-review-handoff.v1','status':'CHANGES_REQUIRED_SOURCE_ONLY','reviewer_id':BACKEND,'reviewer_actor':AUTHOR,'actual_reviewer_thread':THREAD,'actual_parent_Root_thread':ROOT_THREAD,'subject_Source_author':decision['source_author'],'subject_source_ref':decision['source_ref'],'subject_hdf_ref':decision['source_hdf_ref'],'subject_mf_ref':decision['source_mf_ref'],'manifest_ref':mf_ref,'decision_ref':pin(Q/'decision.json'),'report_ref':report_ref,'source_pins_ref':pin(Q/'input-source-pins.json'),'controls_ref':pin(Q/'finite-review-controls.json'),'reviewer_source_audit_ref':audit_ref,'actual_tool_IO_ref':pin(Q/'actual-tool-IO.values.json'),'original1144_ref':pin(Q/'original1144.failure-origin.json'),'source_guard_ref':pin(Q/'source-guard.closed.json'),'full_source_guard_ref':closed_ref,'static_boundary_ref':static_ref,'passed_finite_controls':24,'findings':['BRIDGE-ROLE-001','BRIDGE-TEMP-002'],'actual_Native_fixture_status':'NOT_CREATED_NOT_RUN','all_Source_guards_closed_zero':True,'formal_acceptance':False,'execution_grant':False,'Root_Scope_or_runtime_qualification_ref':None,'STOP':True})
    print(json.dumps({'schema':'researchos.w09-bridge-source-review-delivery.v1','operation':'SOURCE_REVIEW_WITNESS','component':'W09_FORMAL_ROOT_BRIDGE_SOURCE','decision':'CHANGES_REQUIRED','reviewer_id':BACKEND,'reviewer_actor':AUTHOR,'source_author':decision['source_author'],'hdf_ref':hdf_ref,'mf_ref':mf_ref,'decision_ref':pin(Q/'decision.json'),'source_guard_ref':closed_ref,'original1144_ref':pin(Q/'original1144.failure-origin.json'),'actual_tool_IO_ref':pin(Q/'actual-tool-IO.values.json'),'passed_finite_controls':24,'formal_acceptance':False,'execution_grant':False,'runtime_stages_executed':[],'STOP':True},ensure_ascii=False));return 0
if __name__=='__main__':
    code=1
    try:code=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(code));sys.exit(code)
