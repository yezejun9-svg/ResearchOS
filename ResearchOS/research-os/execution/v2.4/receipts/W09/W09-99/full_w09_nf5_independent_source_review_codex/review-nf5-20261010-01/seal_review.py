"""Task100 seal non-author Source decisions; never run an adoption/native stage."""
import ast,hashlib,json,ntpath,sys,traceback,types
from pathlib import Path
from datetime import datetime,timezone
Q=Path(__file__).resolve().parent
ACTOR='codex:/root/backup_regression_resources'
BACKEND='/root/backup_regression_resources'
AUTHOR='codex:/root/attach_restore_independent_review'
THREAD='01a11cee-bf59-7a01-be0e-9f799f9b1084'
ROOT_THREAD='01a11007-5233-7ca1-b71f-9e9e5ce84c98'
AUDIT=Path('C:/Users/yqyyds/.codex/sessions/2026/10/09/rollout-2026-10-09T03-12-51-01a11cee-bf59-7a01-be0e-9f799f9b1084.jsonl')
def need(ok,code):
    if not ok:raise AssertionError(code)
def pin(p):
    p=Path(p);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def raw_new(p,raw):
    with Path(p).open('xb')as f:f.write(raw)
    return pin(p)
def write(name,obj):return raw_new(Q/name,(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def doc(name):return json.loads((Q/name).read_bytes())
def capture():
    home=Q/'actual-reviewer-host';home.mkdir()
    with AUDIT.open('rb')as f:
        header=f.readline();h=json.loads(header)
        need(h['type']=='session_meta'and h['payload']['id']==THREAD and h['payload']['agent_path']==BACKEND and h['payload']['parent_thread_id']==ROOT_THREAD,'ACTUAL_NONAUTHOR_SESSION')
        f.seek(0,2);prefix=f.tell();start=max(len(header),prefix-16*1024*1024);f.seek(start)
        if start!=len(header):f.readline()
        scan=f.tell();calls={};pairs=[];original={}
        while f.tell()<prefix:
            at=f.tell();raw=f.readline()
            if not raw or at+len(raw)>prefix:break
            row=json.loads(raw);v=row.get('payload')
            if row.get('type')!='response_item'or type(v)is not dict:continue
            kind=v.get('type')
            if kind in ('custom_tool_call','function_call'):
                src=v.get('input',v.get('arguments',''))
                if type(src)is str and 'task100_'in src:calls[v['call_id']]=(at,raw,row,src)
            elif kind in ('custom_tool_call_output','function_call_output')and v.get('call_id')in calls:
                ca,cr,call,src=calls.pop(v['call_id']);cid=v['call_id']
                rawref=raw_new(home/(cid+'.raw.jsonl'),header+cr+raw)
                br=write('actual-reviewer-host/'+cid+'.binding.json',dict(schema='researchos.Source-author-actual-tool-binding.v1',Source_author=ACTOR,actual_agent_path=BACKEND,Source_author_thread=THREAD,actual_parent_thread=ROOT_THREAD,source_audit_path=str(AUDIT),source_prefix_bytes=prefix,source_line_offsets=[0,ca,at],source_line_bytes=[len(header),len(cr),len(raw)],source_line_sha256=[hashlib.sha256(x).hexdigest()for x in (header,cr,raw)],original_capture_ref=rawref,actual_call_id=cid,actual_tool_name=call['payload'].get('name'),actual_tool_type=call['payload']['type'],tool_call_utc=call['timestamp'],tool_output_utc=row['timestamp'],capture_is_raw_original_bytes=True,Root_issuer=False,execution_grant=False,formal_acceptance=False))
                pair=dict(raw_ref=rawref,binding_ref=br,call_id=cid);pairs.append(pair)
                if 'store("task100_review_run_input",v)'in src and '3650ab'in raw.decode('utf-8'):original['start']=pair
                if 'store("task100_review_poll2_input",v)'in src and '0a6f02'in raw.decode('utf-8'):original['terminal']=pair
    need(len(pairs)>=16 and set(original)=={'start','terminal'},'ACTUAL_TASK100_SOURCE_HOST_PAIRS')
    origin=write('original1147.failure-origin.json',dict(schema='researchos.original-failure-origin.v1',original_ordinal=1147,
        capture_kind='ACTUAL_SUCCESSFUL_PROCESS_WITH_SEMANTIC_SOURCE_CHECKER_FAILURE',actual_start_chunk_id='3650ab',actual_terminal_chunk_id='0a6f02',actual_start_host_binding_ref=original['start']['binding_ref'],actual_start_raw_ref=original['start']['raw_ref'],actual_host_binding_ref=original['terminal']['binding_ref'],actual_raw_ref=original['terminal']['raw_ref'],full_original_IO_ref=pin(Q/'original1147.actual-tool-IO.values.json'),failed_checker_script_ref=pin(Q/'review_source.py'),original_result_ref=pin(Q/'finite-review.json'),actual_outer_exit=0,actual_Python_exit=0,ROOT_PYTHON_EXIT_marker=0,semantic_failed=1,Go_exit=None,Native_exit=None,SQL_exit=None,model_exit=None,TP_exit=None,dispatcher_exit=None,source_guard_ref=pin(Q/'SourceGuard.closed.json'),guard_actual_closed=True,guard_retained_handles=0,original_4154_resource_closure_replayed=False,
        reason='The checker traversed a whole prepare If including its else/run branch. This was a checker semantic error, not a product Source defect or nonzero process exit.',corrected_delta_ref=pin(Q/'prepare-body-delta.json'),failure_count_reset=False,automatic_retry=False))
    audit=write('reviewer-source-audit.json',dict(schema='researchos.w09-nf5-independent-source-audit.v1',actor_id=ACTOR,actual_backend=BACKEND,actual_thread=THREAD,actual_parent_thread=ROOT_THREAD,source_audit_path=str(AUDIT),finite_scan_start_offset=scan,source_prefix_bytes=prefix,completed_pair_count=len(pairs),completed_tool_pairs=pairs,original1147_ref=origin,pending_final_sealer_calls_not_fabricated=sorted(calls),final_sealer_and_Final_delivery_obligation='Root captures this actual complete tool return and subsequent backend Final after they occur; no future Root peer, lease, Scope, qualification or return is prefilled.',Root_issuer=False,execution_grant=False))
    return audit,origin
def main():
    x=doc('input-shapes.json');n=json.loads(Path(x['producer_hdf_ref']['path']).read_bytes());s=json.loads(Path(x['registrar_hdf_ref']['path']).read_bytes())
    nc=json.loads(Path(n['calling_contract_ref']['path']).read_bytes());sc=json.loads(Path(s['contract_ref']['path']).read_bytes())
    choice=json.loads(Path(n['source_choice_ref']['path']).read_bytes());original=doc('finite-review.json');delta=doc('prepare-body-delta.json')
    fullguard=doc('SourceGuard.closed.json');dguard=doc('prepare-delta.SourceGuard.closed.json')
    need(original['passed']==26 and original['failed']==1 and delta['passed']is True and original['old_controls_rerun']is False,'ORIGINAL_26_AND_NARROW_ONE_CHECKER_CORRECTION')
    for guard in (fullguard,dguard):need(guard['closed']is True and guard['retained_handles_count']==0 and guard['verification']=='PASSED'and not guard['errors'],'ALL_REAL_GUARDS_CLOSED')
    need(len(fullguard['entries'])==4154 and doc('exact-inverses.json')['all_exact']is True,'REAL_4154_INPUT_CLOSURE_AND_EXACT_INVERSE')
    need(not doc('actual-tool-IO.values.json')['missing_in_memory_pairs'],'COMPLETE_STORED_TOOL_VALUES')
    audit,origin=capture()
    report='''NF5 Producer 与 ScopeCaller02 的独立 Source 审查通过，仅供 Root 后续按真实输入注册；不授执行或正式接受。

当前 Source21 及3905编译输入锁定 retrieval_test.go 的1254f8c7...版本；真正C19分支保留两项Main测试、五个C19 ID。四个新RunID属于fullw09-20261010-05，当前scratch/receipt/output均未创建。NF4→NF5五文件及Registrar两文件逐项恢复原UTF-8字节与原SHA；旧Source、旧69/112/20/98/35/36以及作者21/13控制不重跑。

NF5实际未来Go list使用-test/-deps/-compiled/-export/-json，3905稳定输入包含8个真实Go工具exe；19个go.mod、353包名及51个Main目录名单保留。RootOwnedPython→当前Main runner→innerOwnedGo的编译输入、exports/generated和launcher permit在最终Job闲置并关闭之前持有；原已返回observation先保存，输出hash错误不会将已知退出丢为NULL。prepare真分支不调用产品；run是一轮list及一轮test，不自动重试。

真实C盘 .researchos/w09-native-v5父目录、Root资源回执b85a...、项目Owner标记与原Root工具三行a5cd...已有限读取验证；资源回执execution_grant=false、RootScope_issued=false，不能替代新的四Scope发行。真实Task97平台metadata+Final已核为Attach后端作者，NF5与Registrar HDF均在原Final中；不合成或重标作者。

ScopeCaller仍先检查Root身份、原正式Source交付、非作者两个独立decision、current4动态CAS、旧Main profile/CM40实际adoption回执、有限四lease及新generation。完整四档案与旧诊断前缀保留，counter整数/连续/NULL门没有降低；旧三Scope仍要求closed且原owner/worker/ref不变。activate过滤CP/OW的SourceReadGuard并在TP持有时只用缓存原字节model，不在回调重新打开CP/OW；Root唯一写Canon。Source级资源调查不替未来Rootscope/lease/完整实际父返回。

本次27个唯一检查中最初26通过、1项检查器把prepare的else/run误计；original1147真实outer/Python0/0、semantic_failed1、其余NULL已保存，不是产品失败。只补正确branch.body检查并通过，4154资源闭包和26通过项未重跑。4154份公开资源包括3905编译refs和165个实际加载Python/Windows资源，主guard及delta guard全部closed/retained0；不持live四Canon。

下一步Root按两个review合同分别绑定producer与registrar三件套及本次真实backend Final，重捕当前四Canon和连续pending，发行新的有限NATIVE_SCOPES generation，再串行prepare/run四selector。固定Windows绝对ref三参数与Python -I -S -B -X utf8必须保持；每步完整原Root工具返回/Job/guards需另行对账。未来正式consumer/Rootverify进程TEMP/TMP必须共同设实际C父，先于tempfile缓存；Bridge02的两阻断仍须单独修复，本审查不接受该Bridge或新Native mode。
'''
    reportref=raw_new(Q/'report.md',report.encode('utf-8'))
    resource=write('runtime-resource-qualification.json',dict(schema='researchos.w09-nf5-independent-runtime-resource-qualification.v1',status='SOURCE_RUNTIME_RESOURCE_CLOSURE_VERIFIED_PENDING_ROOT_BINDING',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,producer_source_handoff_ref=x['producer_hdf_ref'],producer_source_manifest_ref=n['manifest_ref'],registrar_source_handoff_ref=x['registrar_hdf_ref'],registrar_source_manifest_ref=s['manifest_ref'],public_resource_manifest_ref=pin(Q/'public-resource-manifest.json'),source_guard_ref=pin(Q/'SourceGuard.closed.json'),delta_source_guard_ref=pin(Q/'prepare-delta.SourceGuard.closed.json'),reviewer_source_audit_ref=audit,source_author_actual_audit_ref=original['SourceAuthor_actual_audit_ref'],actual_compile_Source_refs=3905,actual_held_public_resources=4154,actual_loaded_runtime_refs=165,all_guards_closed=True,current_live_Canon_held=False,actual_Go_runs=0,actual_Native_runs=0,actual_SQL_runs=0,actual_TP_calls=0,actual_model_provider_calls=0,Source_runtime_stage_calls=0,Root_runtime_binding_ref=None,Root_scope_ref=None,Root_lease=None,future_actual_list_generated_exports_refs=None,future_actual_Go_and_descendant_DLL_inventory=None,formal_acceptance=False,execution_grant=False))
    boundary=write('calling-contract.review.json',dict(schema='researchos.w09-nf5-independent-reviewed-calling-contract.v1',producer_contract_ref=n['calling_contract_ref'],registrar_contract_ref=s['contract_ref'],producer_future_argv=nc['future_argv'],registrar_future_CLI=sc['CLI'],review_decisions_must_bind_separate_local_HDF_MF=True,Source_author=AUTHOR,reviewer=ACTOR,Root_issuer_executor='codex:/root',Root_current4='Dynamic completed Root original observation; no Source current4 grant.',source_author_actual_audit_ref=original['SourceAuthor_actual_audit_ref'],Root_must_capture_this_real_Final=True,finite_scopes_required=4,producer_generation=n['generation'],Native_roots_status='NOT_CREATED_NOT_RUN',Root_parent_resource_only=True,formal_consumer_TEMP_TMP=sc['formal_consumer_actual_TEMP_TMP'],runtime_resource_qualification_ref=resource,formal_acceptance=False,execution_grant=False,Root_future_Request=None,Root_future_Scope=None))
    decisions={}
    for name in ('producer','registrar'):
        home=Q/name;home.mkdir()
        if name=='producer':
            d=dict(schema=nc['review_schema'],decision=nc['review_decision'],actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,source_handoff_ref=x['producer_hdf_ref'],source_manifest_ref=n['manifest_ref'],calling_contract_ref=n['calling_contract_ref'],**nc['bound_source_refs'],selectors=choice['selectors'],source21=choice['common']['source21'])
        else:
            d=dict(schema=sc['review_schema'],decision=sc['review_decision'],actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_author_id=AUTHOR,source_handoff_ref=x['registrar_hdf_ref'],source_manifest_ref=s['manifest_ref'],caller_ref=s['caller_ref'],core_ref=s['core_ref'],contract_ref=s['contract_ref'])
        d.update(created_utc=datetime.now(timezone.utc).isoformat(),findings=[],actual_executed=False,formal_acceptance=False,parent_acceptance=False,execution_grant=False,formal_case_accepted_delta=0,actual_root_stage_calls=0,original_checks_ref=pin(Q/'finite-review.json'),checker_delta_ref=pin(Q/'prepare-body-delta.json'),unique_checks_passed=27,original1147_ref=origin,runtime_resource_qualification_ref=resource,report_ref=reportref,reviewer_source_audit_ref=audit,source_author_actual_audit_ref=original['SourceAuthor_actual_audit_ref'],Root_future_Scope=None,Root_future_runtime_binding=None,STOP=True)
        dr=write(name+'/decision.json',d)
        ctx=write(name+'/review-context.json',dict(schema='researchos.w09-nf5-independent-source-context.v1',component=name,report_ref=reportref,Source_guard_ref=pin(Q/'SourceGuard.closed.json'),delta_guard_ref=pin(Q/'prepare-delta.SourceGuard.closed.json'),runtime_resource_qualification_ref=resource,calling_contract_review_ref=boundary,original1147_ref=origin,reviewer_source_audit_ref=audit,source_only=True,formal_acceptance=False,execution_grant=False))
        mr=write(name+'/MF.json',dict(schema='researchos.source-manifest.v1',members=[dr,ctx]))
        hr=write(name+'/HDF.json',dict(schema='researchos.w09-nf5-independent-source-review-handoff.v1',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_thread_id=THREAD,Root_thread_id=ROOT_THREAD,source_author_id=AUTHOR,status='ACCEPTED_SOURCE_ONLY',manifest_ref=mr,source_decision_ref=dr,runtime_resource_qualification_ref=resource,report_ref=reportref,reviewer_source_audit_ref=audit,original1147_ref=origin,formal_acceptance=False,execution_grant=False,Root_future_Scope=None,STOP=True))
        decisions[name]=dict(hdf_ref=hr,mf_ref=mr,decision_ref=dr,decision=d['decision'])
    compiled=[]
    for f in sorted(Q.glob('*.py')):
        ast.parse(f.read_bytes());compile(f.read_bytes(),str(f),'exec');compiled.append(pin(f))
    static=write('static-final-boundary.json',dict(schema='researchos.w09-nf5-independent-static-boundary.v1',compiled_Source_refs=compiled,subject_Source_written=False,Main_written=False,Canon_written=False,live_Canon_held=False,source_actor=ACTOR,subject_author=AUTHOR,Source_independence=True,actual_stage_calls=[],old_passed_checks_rerun=False,old_4154_closure_rerun=False,original1147_preserved=True,FILETIME_representation='No new product PID/FILETIME observations; future OwnedJob uses Python exact int/decimal str.',formal_acceptance=False,execution_grant=False))
    # Hold only newly assembled review files. Do not replay the 4154-resource closure.
    gr=x['choice_guard_ref'];raw=Path(gr['path']).read_bytes();need(pin(gr['path'])==gr,'GUARD_SOURCE_PIN')
    gm=types.ModuleType('task100_final_review_package_guard');exec(compile(raw,gr['path'],'exec'),gm.__dict__)
    refs=[gr]+[pin(f)for f in sorted(Q.rglob('*'))if f.is_file()]
    guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=1024*1024*1024)
    try:guard.acquire(refs)
    finally:closed=guard.close();closedref=write('final-review-package-guard.closed.json',closed)
    need(closed['closed']is True and closed['verification']=='PASSED'and closed['retained_handles_count']==0 and not closed['errors'],'FINAL_SOURCE_PACKAGE_GUARD_CLOSED')
    members=[pin(f)for f in sorted(Q.rglob('*'))if f.is_file()and f not in (Q/'HDF.json',Q/'MF.json')]
    mf=write('MF.json',dict(schema='researchos.source-manifest.v1',actor_id=ACTOR,members=members,exclusions=['Top MF/HDF self digests','Final sealer return and later peer Final occur after sealing; Root captures originals separately.'],immutable_after_publish=True,formal_acceptance=False,execution_grant=False))
    hdf=write('HDF.json',dict(schema='researchos.w09-nf5-independent-combined-source-review-handoff.v1',status='ACCEPTED_SOURCE_ONLY',actor_id=ACTOR,actor_role='INDEPENDENT_NON_AUTHOR',source_thread_id=THREAD,Root_thread_id=ROOT_THREAD,source_author_id=AUTHOR,manifest_ref=mf,producer=decisions['producer'],registrar=decisions['registrar'],runtime_resource_qualification_ref=resource,report_ref=reportref,reviewer_source_audit_ref=audit,complete_tool_IO_ref=pin(Q/'actual-tool-IO.values.json'),original1147_ref=origin,original_main_guard_ref=pin(Q/'SourceGuard.closed.json'),checker_delta_guard_ref=pin(Q/'prepare-delta.SourceGuard.closed.json'),final_package_guard_ref=closedref,calling_contract_review_ref=boundary,static_boundary_ref=static,unique_checks_passed=27,original_check_attempt='26 PASS / 1 checker semantic error, then one narrow corrected check PASS; original1147 retained.',all_Source_guards_closed_zero=True,Native_NOT_CREATED_NOT_RUN=True,Root_stages_called=[],formal_acceptance=False,execution_grant=False,future_Root_binding=None,STOP=True))
    print(json.dumps(dict(schema='researchos.w09-nf5-independent-source-review-delivery.v1',operation='SOURCE_REVIEW_WITNESS',component='W09_NF5_PRODUCER_AND_SCOPE_CALLER_SOURCE',decision='ACCEPTED_SOURCE_ONLY',reviewer_actor=ACTOR,reviewer_backend=BACKEND,Root_thread_id=ROOT_THREAD,hdf_ref=hdf,mf_ref=mf,producer=decisions['producer'],registrar=decisions['registrar'],runtime_resource_qualification_ref=resource,source_guard_ref=closedref,original1147_ref=origin,formal_acceptance=False,execution_grant=False,actual_root_stage_calls=0,STOP=True),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
