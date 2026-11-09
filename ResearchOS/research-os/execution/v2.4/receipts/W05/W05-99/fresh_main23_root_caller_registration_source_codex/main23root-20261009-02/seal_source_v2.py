import sys
sys.dont_write_bytecode=True
import ast
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import stat
import traceback

Q=Path(__file__).resolve().parent
AUTHOR='codex:/root/backup_regression_resources'
PRIOR_AUTHOR='codex:/root/native_temp_independent_review'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'

def pin(path):
    path=Path(path).resolve(strict=True);raw=path.read_bytes()
    return {'path':str(path),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
def save(name,value,raw=False):
    path=Q/name;data=value if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode('utf-8')
    with path.open('xb') as stream:assert stream.write(data)==len(data)
    return pin(path)
def doc(name):return json.loads((Q/name).read_text(encoding='utf-8'))
def functions(raw):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(raw).body if isinstance(x,ast.FunctionDef)}

def main():
    final_ref=pin(Q/'main23_root.source.py')
    assert (final_ref['sha256'],final_ref['bytes'])==('2a79993d3060d548d1a7d2a6c80400a549ec4cb81640ff36f56e73a475549fca',56259)
    initial=doc('input-discovery.json');basis=initial['roots']
    # Prove the entire final candidate's inverse, preserving mixed line endings.
    delta=doc('observed-tool-name.exact-inverse.json');final=(Q/'main23_root.source.py').read_bytes()
    offset=delta['offset'];new=delta['new_utf8'].encode('utf-8');old=delta['old_utf8'].encode('utf-8')
    assert final[offset:offset+len(new)]==new
    intermediate=final[:offset]+old+final[offset+len(new):]
    assert intermediate==(Q/'pre-observed-tool-name.caller.py').read_bytes()
    inverse=intermediate.decode('utf-8')
    for change in reversed(doc('exact-inverse.json')['patches']):
        start=change['start'];end=start+len(change['after'])
        assert inverse[start:end]==change['after']
        inverse=inverse[:start]+change['before']+inverse[end:]
    base=(Q/'inputs/base-main23_root.source.py').read_bytes()
    assert inverse.encode('utf-8')==base
    old_functions,new_functions=functions(base),functions(final)
    unchanged=[k for k in old_functions if old_functions[k]==new_functions[k]]
    modified=[k for k in old_functions if old_functions[k]!=new_functions[k]]
    assert set(old_functions)<=set(new_functions) and old_functions['projection']==new_functions['projection']
    original22=doc('source-controls.current-final.json');targeted45=doc('source-controls.v2.current-final.json')
    assert len(original22['controls'])==22 and all(x['pass'] and x.get('result',True) is not False for x in original22['controls'])
    assert len(targeted45['controls'])==45 and all(x['status']=='PASS' for x in targeted45['controls'])
    assert targeted45['caller_ref']==final_ref and targeted45['actual_future_qualification_ref'] is None
    static_ref=save('static-verification.final.json',{
        'schema':'researchos.main23-caller-v2-final-static-verification.v1','source_author':AUTHOR,
        'AST_and_Python_compile':'PASS_SOURCE_ONLY','full_final_to_v1_original_byte_inverse_equal':True,
        'unchanged_original_functions':unchanged,'changed_original_functions':modified,
        'new_functions':sorted(set(new_functions)-set(old_functions)),
        'TP_projection_AST_unchanged':True,'original22_names_and_assertions_preserved':doc('static-verification.json')['original_22_assertions_preserved'],
        'original22_current_candidate_pass':22,'targeted45_current_candidate_pass':45,
        'runtime_Source_changes':['strict actual Root capture and structured complete refs','actual independent runtime review chain before native loader'],
        'authority':'NONE','production_Main_Canon_writes':0,'Native_Go_SQLite_dispatcher_model':None})
    # Capture sources are original owned-thread bytes, not generated future Root evidence.
    capture_indexes=[doc('actual-source-hostpairs.index.json'),doc('actual-source-hostpairs-continuation.index.json')]
    captures={x['label']:x for index in capture_indexes for x in index['pairs']}
    identity=doc('actual-source-hostpairs/input-read.binding.json')['header_public_identity']
    assert identity['id']=='01a11cee-bf59-7a01-be0e-9f799f9b1084'
    assert identity['parent_thread_id']==ROOT_THREAD and identity['agent_path']=='/root/backup_regression_resources'
    failure_specs=[(1031,'eb048f','construct_source.py','inverse count assumed unique substring'),
        (1032,'2ae9b6','construct_source_revision.py','AST breadth-first ordering differed after synthetic fixture nesting'),
        (1037,'e8d701','extract_source_hostpairs.py','stored fulfilled.value already was actual host dictionary'),
        (1038,'d93af2','extract_source_hostpairs_revision.py','qualified tool name did not match observed bare exec')]
    failure_refs=[]
    for ordinal,chunk,script,reason in failure_specs:
        label='original'+str(ordinal);item=captures[label]
        assert item['actual_outer_exit']==item['actual_Python_exit']==1
        origin=save('failure-origin.'+str(ordinal)+'.json',{
            'schema':'researchos.original-source-tool-failure.v1','root_allocated_original_ordinal':ordinal,
            'actual_call_chunk_id':chunk,'source_author':AUTHOR,'source_thread_id':identity['id'],
            'parent_root_thread_id':ROOT_THREAD,'actual_agent_path':identity['agent_path'],
            'original_script_ref':pin(Q/script),'complete_original_dictionary_IO_ref':pin(Q/('original-'+chunk+'.full-tool-pair.json')),
            'actual_source_raw_hostpair_ref':item['raw_ref'],'actual_source_hostpair_binding_ref':item['binding_ref'],
            'origin_selector':'original response_item tool output / chunk_id='+chunk,
            'actual_outer_exit':1,'actual_python_exit':1,'actual_native_exit':None,'actual_dispatcher_exit':None,
            'actual_model_exit':None,'actual_go_exit':None,'actual_sqlite_exit':None,
            'diagnosis':reason,'candidate_Main_Canon_writes_in_original_failed_invocation':0,
            'counter_reset':False,'automatic_retry':False,'original_script_and_IO_unchanged':True,
            'subsequent_revision_is_new_input_not_original_retry':True,'authority':'NONE'})
        failure_refs.append({'ordinal':ordinal,'origin_ref':origin,'raw_hostpair_ref':item['raw_ref'],
            'capture_binding_ref':item['binding_ref'],'original_dictionary_IO_ref':pin(Q/('original-'+chunk+'.full-tool-pair.json'))})
    # Archive observations as Source inputs; live Canon refs never become held Source dependencies.
    references=initial['Source_inputs']+[x['snapshot_ref'] for x in initial['current_creation_baseline']]
    inputs_ref=save('source-inputs.json',{
        'schema':'researchos.main23-root-caller-v2-source-inputs.v1','source_author':AUTHOR,
        'previous_caller_author':PRIOR_AUTHOR,'builder_source_author_unchanged':PRIOR_AUTHOR,
        'references':references,'creation_baseline':initial['current_creation_baseline'],
        'live_creation_Canon_read_handles_closed':True,'future_current_before_refs':None,
        'Root_may_legally_advance_Canon':'Source snapshots remain historical371/175/39; fresh current4 is a mandatory later Root input',
        'authority':'NONE'})
    contract=doc('inputs/base-root-calling-contract.source.json')
    contract.update(schema='researchos.main23-root-calling-contract.v2',source_author=AUTHOR,
        previous_caller_author=PRIOR_AUTHOR,builder_source_author=PRIOR_AUTHOR,caller_ref=final_ref,registrar_ref=final_ref,source_inputs_ref=inputs_ref)
    contract['source_review_decision']['source_author']=AUTHOR
    contract['source_review_decision']['review_author']='actual independent peer, neither Root nor caller/builder Source author; backend Root delivery identity must agree'
    contract['future_binding_policy']='Creation baseline is actual CP371/OW175/CM39, archived in source-inputs. All future Root qualifications, requests, grants and current4 remain null. Independently review this new Source and its actual runtime closure, then Root must refresh actual current4 and issue a same-thread scope. The public22 product trial failed PUBLIC_RESTORE_SCHEMA_MISMATCH and is not accepted. Actual public371 registration lineage is separate from product PASS. CP372/OW176 is only valid if a fresh current before really is371/175.'
    contract['actual_source_author_identity']=identity
    contract['capture_binding']={
        'schema':'researchos.root-actual-tool-capture-binding.v1','root_thread_id':ROOT_THREAD,
        'source_audit_path':'C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl',
        'fields':['issued_by=codex:/root','operation','original_capture_ref','original_call_id','original_line_sha256[3]',
            'source_line_bytes[3]','source_line_offsets[3] with first0','source_prefix_size_observed positive int',
            'tool_call_timestamp','tool_result_timestamp','peer_delivery_binding_ref for SOURCE_REVIEW_WITNESS'],
        'raw_rows':'Exactly three LF-terminated original records: session_meta ordinal0 + actual call + matching returned output. Each selected line must match original fixed Root log at its exact integer offset. First/last ordinals and actual timestamps remain exact.',
        'call':'custom_tool_call/function_call; matching nonempty call_id; explicit exec/functions.exec or exec_command/functions.exec_command. Wrapper exec must request tools.exec_command and carry MAIN23_CAPTURE_OPERATION:<exact operation>. Unknown tool names are rejected.',
        'returned_source':'Decode one actual returned exec host dictionary with chunk_id, integer exit_code0, string output. Decode exactly one complete typed researchos.root-main23-capture-result.v2 from host output; arbitrary SHA strings never qualify.',
        'typed_result_fields':['schema','issued_by=codex:/root','observer_actor=codex:/root','root_thread_id',
            'operation','source=tools.exec_command','formal_acceptance=false','observed_refs exact complete triples','peer_actor exact or null'],
        'operations':{'SOURCE_REVIEW_WITNESS':'review HDF/MF/decision, plus actual peer delivery proof',
            'POSTREVIEW_CURRENT_FOUR':'ordered actual checkpoint/ownership/step_state/commands',
            'ACTIVATION_FACTS_CURRENT_FOUR':'facts plus actual current4',
            'RUNTIME_QUALIFICATION_ISSUANCE':'payload+qualification scope+review HDF/MF/decision+peer binding'},
        'Root_probe_requirement':'Run a Root-owned finite public reader with locked Python through tools.exec_command; print the complete typed result JSON after checking all observed refs. Preserve this actual outer request/return, original source offsets and stdout; a standalone invented JSON or body containing hashes is rejected.'}
    contract['actual_peer_delivery']={
        'binding_schema':'researchos.root-actual-peer-capture-binding.v2','same_root_thread':ROOT_THREAD,
        'raw_rows':'Original session_meta, inter_agent_communication_metadata and next backend response_item agent_message. Communication trigger_turn is bool, next ordinal and timestamps match, metadata.client_authored is false.',
        'identity':'Actual agent_message author == qualified peer; recipient /root; nonempty actual message id. Actor is codex:/root/[a-z0-9_]+, not Root or either Source author.',
        'message_schema':'researchos.main23-peer-review-delivery.v2',
        'message_fields':['review_author','root_thread_id','operation','verdict=ACCEPTED_SOURCE_ONLY',
            'formal_acceptance=false','execution_grant=false','review_refs exact HDF/MF/decision triples'],
        'binding_fields':['all original capture line/source pins','peer_actor','message_id','received_at'],
        'order':'Actual peer delivery must precede Root observation/issuance. Root observes peer delivery; Root does not issue independent acceptance.'}
    contract['runtime_qualification']={
        'schema':'researchos.root-main23-qualified-runtime.v2',
        'fields':['issued_by=codex:/root','root_thread_id','status=QUALIFIED_FOR_MAIN23_BUILD','independent_non_author=true',
            'formal_programme_qualification=false','review_author','source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref',
            'qualification_scope_ref','python_ref','go_ref','resource_refs','review_hdf_ref','review_mf_ref','review_decision_ref',
            'review_hostpair_binding_ref','created_utc','payload_ref','root_issuance_binding_ref'],
        'payload_schema':'researchos.root-main23-runtime-qualification-payload.v2',
        'payload_rule':'Every field except wrapper schema/payload_ref/root_issuance_binding_ref equals payload exactly; Root captures payload before wrapping the final qualification, avoiding a circular hash.',
        'scope_schema':'researchos.root-main23-runtime-qualification-scope.v2',
        'scope_fields':['issued_by=codex:/root','root_thread_id','slice_id=MAIN23_RUNTIME_RESOURCE_QUALIFICATION',
            'formal_acceptance=false','execution_grant=false','source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref',
            'created_utc','lease_expires_at still live'],
        'review_hdf_schema':'researchos.main23-runtime-independent-review-hdf.v2',
        'review_decision_schema':'researchos.main23-runtime-independent-review-decision.v2',
        'review_common_fields':['review_author actual peer','source_author='+AUTHOR,'builder_source_author='+PRIOR_AUTHOR,
            'root_thread_id','source_hdf_ref','source_mf_ref','caller_ref','builder_contract_ref','qualification_scope_ref','python_ref','go_ref'],
        'review_hdf_additional_fields':['manifest_ref','decision_ref','reviewed_utc'],
        'review_decision_additional_fields':['independent_non_author=true','verdict=RUNTIME_CLOSURE_ACCEPTED',
            'formal_acceptance=false','execution_grant=false','resource_refs exactly equals qualification'],
        'review_MF_rule':'All members checked by exact path/SHA/bytes, including decision; HDF/MF/decision/source/caller pins match precisely.',
        'time_order':'scope.created <= review.reviewed <= actual peer receipt <= actual Root call <= actual Root output <= qualification.created',
        'authority':'Independent reviewer must supply actual closure evidence and backend formal delivery. Two Root JSONs claiming the same reviewer are insufficient. No qualification is created by this Source.',
        'existing_runtime_gate':'Locked Python/Go, loaded Python/native closure and actual module resources remain required; strict provenance is checked before native Job module loading. Same existing SourceReadGuard lifetime and child Job/cleanup rules remain.'}
    contract['future_bindings']={k:None for k in contract['future_bindings']}
    contract['public22']='Actual product trial failed PUBLIC_RESTORE_SCHEMA_MISMATCH; separate end22 slice remains unaccepted'
    contract_ref=save('root-calling-contract.source.json',contract)
    report='''本包只准备 Main23 Root caller/registrar Source v2；authority=NONE，待新非作者独立审查。

作者为 codex:/root/backup_regression_resources，实际线程与 Root parent 见 actual-source-hostpairs/input-read.binding.json。
旧 v1 与独立 builder 作者仍为 codex:/root/native_temp_independent_review；没有改写旧身份或借用其资格。

P1-ROOT-CAPTURE：原 SHA 子串检查改成完整三行实际审计来源、call_id、精确操作及实际返回宿主结构验证。
三个字段 path/sha256/bytes 必须完整且全部匹配，缺项、重复项、SHA 字符串、仿造工具返回或不匹配原日志均拒绝。
实际审计工具名 exec 已按原始 Source 日志确认；别名兼容有限，wrapper 必须请求 tools.exec_command。
Source review witness 另绑定真实 backend peer→Root 原始交付，Root 只观察，不能用 Root JSON 自称 peer。

P1-RUNTIME-CLOSURE：Root 两个 JSON 的相同 reviewer 字符串不足以资格闭合。
新增实际独立 HDF/MF/decision、caller/Source/builder pins、Root 同线程资格 scope、peer 原始交付及 Root 发行实际返回绑定。
资格 payload 与外层 wrapper 分两步建立，避免未来回执哈希循环。
保持 locked Python/Go、当前已加载 Python/native 资源完整闭合、原 SourceReadGuard、Root OwnedJob 与所有 cleanup 条件。

原 22 个控件及实质断言保留；历史 pre371 predicate 使用明确合成 fixture，released-runtime 使用原 builder 的真实作者。
最终候选运行结果：原22通过；新增45纯 Source provenance 控件通过，合成目录已清除。
实际 Root 控件原始三行、完整 request/result 及 offset/hash/bytes 见两个 actual-source-hostpairs*.index.json。
这些控件不构成真实 Root 资格、登记、Go/native/model 产品执行或正式验收。

完整最终 Source→中间候选→旧 v1 原始 bytes 逆恢复验证通过，mixed CRLF/LF 保留；TP projection AST 不变。
caller.final.diff、controls.diff、observed-tool-name.exact-inverse.json 与 static-verification.final.json 给出精确差分与静态边界。
原1031/1032/1037/1038失败脚本与 IO 原件保留，不重跑同输入、不重置失败数；每项 actual outer/Python=1/1，其余未执行=NULL。

创建时 Canon 实际371/175/39，4完整快照已保留且读句柄已关闭。
当前 Source 依赖仅持历史快照，不锁住 live CP/OW；Root 合法后续事务无需被解释成 Source 写入。
public22 实际 trial 已在 PUBLIC_RESTORE_SCHEMA_MISMATCH 停止，不能因为4子进程退出0宣称产品PASS。
Root 之后必须新非作者 Source 审查、真实资源 closure 审查、真实 peer 原交付、同线程 Root scope/发行及 fresh current4。
未来 qualification/request/registration/grant 均为NULL；Main/Canon/旧包/T* 写入0；本作者不自批准正式接受。
封存后 STOP。
'''
    report_ref=save('source-report.md',report.encode('utf-8'),True)
    mapping_ref=save('finding-to-change.mapping.json',{
        'schema':'researchos.main23-v2-p1-mapping.v1','prior_rejection_ref':pin(Q/'inputs/review-source-findings.json'),
        'findings':[
            {'id':'ROOT_CAPTURE_SOURCE_BINDING','changed_functions':['validate_root_capture','own_review','future_request','register'],
                'added_functions':['structured_documents','exact_ref_set','original_capture_rows','validate_peer_delivery'],
                'scope':'only actual provenance and complete structured refs; no grant or acceptance threshold lowering'},
            {'id':'RUNTIME_CLOSURE_NONAUTHOR_QUALIFICATION','changed_functions':['runtime_closure'],
                'added_functions':['runtime_review_chain'],'scope':'actual exact independent Source/resources/scope/peer/Root issuance chain before native loader'}],
        'author_split':['CALLER_AUTHOR current backup','BUILDER_AUTHOR original Native'],
        'unchanged_original_functions':unchanged,'original22_preserved':True,'extra45_source_controls':True,'authority':'NONE'})
    facts_ref=save('source-facts.json',{
        'schema':'researchos.main23-root-caller-source-facts.v2','source_author':AUTHOR,'actual_source_header_identity':identity,
        'caller_ref':final_ref,'contract_ref':contract_ref,'source_inputs_ref':inputs_ref,
        'creation_baseline_revisions':{'checkpoint':371,'path_ownership':175,'step_state':None,'commands':39},
        'original_controls_passed':22,'new_pure_controls_passed':45,'Sourcecontrols_authority':'SYNTHETIC_NONE',
        'failure_origins':failure_refs,'Source_guard_initial_ref':pin(Q/'input-source-guard.closed.json'),
        'actual_future_qualification_ref':None,'actual_request_ref':None,'actual_registration_ref':None,'actual_grant_ref':None,
        'Main_Canon_oldSource_T_writes':0,'Native_Go_SQLite_dispatcher_model':None,
        'public22_status':'FAIL_PUBLIC_RESTORE_SCHEMA_MISMATCH_NOT_ACCEPTED','authority':'NONE','formal_acceptance':False})
    # Finite immutable Source guard: never acquire live Canon handles here.
    spec=importlib.util.spec_from_file_location('main23_v2_guard_bootstrap',Q/'read_inputs.py')
    lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
    guard=lib.Guard();closed=False
    try:
        paths=sorted(p for p in Q.rglob('*') if p.is_file())
        for path in paths:
            raw,ref=guard.read(path,pin(path))
            if path.suffix=='.py':ast.parse(raw);compile(raw,str(path),'exec')
        for ref in initial['Source_inputs']:guard.read(ref['path'],ref)
        closure=guard.close();closed=True
        closure.update(authority='NONE',live_Canon_handles=0,source_author=AUTHOR,
            candidate_ref=final_ref,all_current_Source_files_ast_compile_checked=True)
        guard_ref=save('finite-source-guard.final.closed.json',closure)
    finally:
        if not closed:
            for stream,_,_ in guard.held:stream.close()
    members=sorted((pin(p) for p in Q.rglob('*') if p.is_file()),key=lambda x:x['path'])
    mf_ref=save('MF.json',{'schema':'researchos.immutable-source-manifest.v1','source_author':AUTHOR,
        'authority':'NONE','members':members,'excluded_postseal_files':['source-seal.actual-tool-pair.json','source-seal.actual-source-hostpair.jsonl','source-seal.actual-source-hostpair.binding.json','source-seal.closed-summary.json','capture_source_seal_io.py'],
        'excluded_postseal_reason':'Self-referential seal hostpair and close summary follow immutable member pins; they do not alter members.'})
    hdf_ref=save('HDF.json',{'schema':'researchos.main23-root-caller-registration-source-hdf.v2',
        'status':'SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING','source_author':AUTHOR,
        'source_thread_id':identity['id'],'parent_root_thread_id':ROOT_THREAD,'actual_agent_path':identity['agent_path'],
        'previous_caller_author':PRIOR_AUTHOR,'builder_source_author':PRIOR_AUTHOR,
        'manifest_ref':mf_ref,'caller_ref':final_ref,'registrar_ref':final_ref,'contract_ref':contract_ref,
        'source_inputs_ref':inputs_ref,'report_ref':report_ref,'facts_ref':facts_ref,'mapping_ref':mapping_ref,
        'static_verification_ref':static_ref,'Source_guard_ref':guard_ref,
        'base_hdf_ref':basis['base_HDF']['ref'],'base_mf_ref':basis['base_MF']['ref'],
        'rejected_review_hdf_ref':basis['review_HDF']['ref'],'rejected_review_mf_ref':basis['review_MF']['ref'],
        'original22_current_result_ref':pin(Q/'source-controls.current-final.json'),
        'new45_current_result_ref':pin(Q/'source-controls.v2.current-final.json'),
        'actual_source_hostpairs_index_refs':[pin(Q/'actual-source-hostpairs.index.json'),pin(Q/'actual-source-hostpairs-continuation.index.json')],
        'original_failures_preserved':failure_refs,'created_utc':datetime.now(timezone.utc).isoformat(),
        'current_creation_Canon_revisions':{'checkpoint':371,'path_ownership':175,'commands':39},
        'live_Canon_held_handles':0,'actual_future_qualification_ref':None,'actual_request_ref':None,
        'actual_registration_ref':None,'actual_grant_ref':None,'Source_only':True,'authority':'NONE',
        'formal_acceptance':False,'parent_acceptance':False,'Native_Go_SQLite_dispatcher_model':None,
        'production_Main_Canon_oldSource_T_writes':0,'author_STOP_after_seal':True})
    for ref in members+[mf_ref,hdf_ref]:
        assert pin(ref['path'])==ref
        path=Path(ref['path']);path.chmod(path.stat().st_mode & ~stat.S_IWRITE)
    print(json.dumps({'HDF_ref':hdf_ref,'MF_ref':mf_ref,'member_count':len(members),'caller_ref':final_ref,
        'contract_ref':contract_ref,'guard_ref':guard_ref,'report_ref':report_ref,
        'failure_origins':failure_refs,'Source_controls':{'original':22,'targeted':45},
        'retained_handles':0,'actual_future_qualification_ref':None,'actual_registration':False,
        'authority':'NONE','STOP':True},ensure_ascii=False))

if __name__=='__main__':
    code=0
    try:main()
    except BaseException:traceback.print_exc();code=1
    print('ROOT_PYTHON_EXIT='+str(code));raise SystemExit(code)
