"""Task105 seal the minimal Caller02 Source revision, no Root runtime stage."""
import ast,copy,hashlib,json,sys,traceback,types
from pathlib import Path
Q=Path(__file__).resolve().parent
ACTOR='codex:/root/backup_regression_resources'
BACKEND='/root/backup_regression_resources'
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
def write(name,v):return raw_new(Q/name,(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf-8'))
def doc(name):return json.loads((Q/name).read_bytes())
def capture():
    home=Q/'actual-source-author-host';home.mkdir()
    with AUDIT.open('rb')as f:
        header=f.readline();h=json.loads(header)
        need(h['type']=='session_meta'and h['payload']['id']==THREAD and h['payload']['agent_path']==BACKEND and h['payload']['parent_thread_id']==ROOT_THREAD,'TRUE_SOURCE_AUTHOR_HEADER')
        f.seek(0,2);prefix=f.tell();start=max(len(header),prefix-16*1024*1024);f.seek(start)
        if start!=len(header):f.readline()
        scan=f.tell();calls={};pairs=[];construction=[]
        while f.tell()<prefix:
            at=f.tell();raw=f.readline()
            if not raw or at+len(raw)>prefix:break
            row=json.loads(raw);value=row.get('payload')
            if row.get('type')!='response_item'or type(value)is not dict:continue
            kind=value.get('type')
            if kind in ('custom_tool_call','function_call'):
                source=value.get('input',value.get('arguments',''))
                if type(source)is str and 'task105_'in source:calls[value['call_id']]=(at,raw,row,source)
            elif kind in ('custom_tool_call_output','function_call_output')and value.get('call_id')in calls:
                ca,cr,call,source=calls.pop(value['call_id']);cid=value['call_id']
                rr=raw_new(home/(cid+'.raw.jsonl'),header+cr+raw)
                br=write('actual-source-author-host/'+cid+'.binding.json',dict(schema='researchos.Source-author-actual-tool-binding.v1',Source_author=ACTOR,actual_agent_path=BACKEND,Source_author_thread=THREAD,actual_parent_thread=ROOT_THREAD,source_audit_path=str(AUDIT),source_prefix_bytes=prefix,source_line_offsets=[0,ca,at],source_line_bytes=[len(header),len(cr),len(raw)],source_line_sha256=[hashlib.sha256(x).hexdigest()for x in (header,cr,raw)],original_capture_ref=rr,actual_call_id=cid,actual_tool_name=call['payload'].get('name'),actual_tool_type=call['payload']['type'],tool_call_utc=call['timestamp'],tool_output_utc=row['timestamp'],capture_is_raw_original_bytes=True,Root_issuer=False,execution_grant=False,formal_acceptance=False))
                item=dict(raw_ref=rr,binding_ref=br,call_id=cid);pairs.append(item)
                if 'store("task105_construct_run_input",v)'in source and '837d94'in raw.decode('utf-8'):construction.append(item)
    need(len(pairs)>=6 and len(construction)==1,'REAL_SOURCE_CONSTRUCTION_PAIRS')
    return write('actual-source-author-host.index.json',dict(schema='researchos.public21-directory-revision-source-audit.v1',source_author=ACTOR,actual_backend=BACKEND,author_thread=THREAD,Root_parent_thread=ROOT_THREAD,source_audit_path=str(AUDIT),finite_scan_start_offset=scan,source_prefix_bytes=prefix,completed_tool_pairs=pairs,completed_pair_count=len(pairs),construction_host_pair=construction[0],actual_construction_outer_exit=0,actual_construction_Python_exit=0,pending_final_sealer_calls_not_fabricated=sorted(calls),postseal_external_capture_obligation='Root independently captures the actual final sealer return and this subsequent true backend Final after they occur; no future Root witness/runtime qualification/current4/lease/Scope is synthesized.',formal_acceptance=False,execution_grant=False))
def main():
    b=doc('Source-revision-build.json');controls=doc('directory-delta-controls.json');inverse=doc('directory-exact-inverse.json');closed=doc('directory-delta.SourceGuard.closed.json')
    need(controls['passed']==13 and controls['failed']==0 and inverse['exact_inverse']is True,'MINIMAL_13_CONTROLS_AND_EXACT_SOURCE_INVERSE')
    need(closed['closed']is True and closed['verification']=='PASSED'and closed['retained_handles_count']==0 and not closed['errors'],'ORIGINAL_DELTA_GUARD_CLOSED')
    need(not doc('actual-tool-IO.values.json')['missing_in_memory_pairs'],'COMPLETE_TRUE_TOOL_VALUES')
    for key in ('caller_ref','contract_ref','source_inputs_ref'):need(pin(b[key]['path'])==b[key],'CURRENT_SOURCE_OUTPUT_PIN')
    audit=capture()
    report='''Caller02 Source 修订已准备，待独立非作者审查与Root重新绑定；不签执行、正式接受或产品通过。

唯一业务修改是safe_directory的目录祖先身份比较：最初canonical(str(path))及文件ref strict原字节不变；对已有祖先改用ntpath.normcase(str(resolve(strict=True)))与ntpath.normcase(str(absolute()))，允许D:\\仅作为目录祖先观察，补充FILE_ATTRIBUTE_REPARSE_POINT 0x400拒绝。原symlink/junction、目录存在、新目录、ADS/UNC/设备/遍历和所有namespace门保留。

Caller01的完整原55236字节可由inverse中唯一safe_directory跨度逐字节恢复；其他全部函数和类AST一致，Leaf02、OC3、所有Schemas、Root/peer资格、finite lease、current4/TP、SQL/oracle/private Owner边界、OwnedJob、失效计数与捕获均未改。N仍自动由__file__解析新包，不在源代码加第二个路径引擎。新contract/currentcaller/source-inputs和HDF/MF指向当前Caller02，新Source审查/RuntimeScope/qualification/current4仍动态未知。

Root原1146与Full Task102真实三LF均按父线程、actor、原offset/hash和Root审计原始字节核实；1146的outer/Python1/1事实和旧失败计数不消除，不用Source修复宣称旧运行成功。原Caller01/58/SourceReview99及所有旧成果未写入，58/353/17/4154和旧产品构建均不重跑。

13项必要增量通过：实际existing integration_codex目录及全新未创建目录成功；UNC/extended/device/ADS/traversal拒绝；symlink/junction/reparse/解析alias用合成metadata反例拒绝，未创建OS链接或产品fixture；strict首句和完整byte/AST逆向保留。Sourceguard实际closed/retained0。没有prepare/propose/check/activate/execute、SQLconnection、Go/Native/dispatcher/model/TP/Rootissuer，也不持liveCanon。

下一步Full非作者绑定本新Caller02及新HDF/MF/contract审查，Root真实捕获Final后，以新Source资源、Scope/owner/有限lease/current4 CAS重新绑定并执行真正prepare。旧Caller01审查或old21 BUILD/Main23/public22资格不能代替本新Caller02或public21执行授权。完整实际Root返回仍需后置捕获和独立核对。
'''
    reportref=raw_new(Q/'report.md',report.encode('utf-8'))
    compiled=[]
    for p in sorted(Q.glob('*.py')):
        ast.parse(p.read_bytes());compile(p.read_bytes(),str(p),'exec');compiled.append(pin(p))
    static=write('static-boundary.json',dict(schema='researchos.public21-directory-root-static-boundary.v1',compiled_refs=compiled,changed_function='safe_directory',exact_inverse_ref=b['inverse_ref'],all_other_functions_classes_unchanged=True,Source_author=ACTOR,source_thread=THREAD,actual_Root_stages=[],Go_Native_SQL_model_TP_dispatcher_calls=0,Live_Canon_held=False,Source_self_acceptance=False,formal_acceptance=False,execution_grant=False,new_Original_failures=[],old_original1146_preserved=True))
    inputs=json.loads(Path(b['source_inputs_ref']['path']).read_bytes())
    guards=[r for r in inputs['references']if Path(r['path']).name=='source_read_guard.py']
    need(len(guards)==1,'ONE_EXISTING_PINNED_GUARD_HELPER')
    gr=guards[0];raw=Path(gr['path']).read_bytes();need(pin(gr['path'])=={**gr,'path':str(Path(gr['path']))},'PINNED_GUARD_HELPER')
    gm=types.ModuleType('task105_final_source_guard');exec(compile(raw,gr['path'],'exec'),gm.__dict__)
    # New package closure only; do not repeat old 58/353/17/4154 checks.
    refs=[gr,b['base_hdf_ref'],b['base_mf_ref']]+[pin(p)for p in sorted(Q.rglob('*'))if p.is_file()]
    guard=gm.SourceReadGuard(per_file_cap=128*1024*1024,total_cap=512*1024*1024)
    try:guard.acquire(refs)
    finally:finalclosed=guard.close();fullguard=write('Source-full-closure.guard.closed.json',finalclosed)
    need(finalclosed['closed']is True and finalclosed['verification']=='PASSED'and finalclosed['retained_handles_count']==0 and not finalclosed['errors'],'FINAL_REVIEW_SOURCE_GUARD_CLOSED')
    mf=write('MF.json',dict(schema='researchos.source-manifest.v1',source_author=ACTOR,members=[pin(p)for p in sorted(Q.rglob('*'))if p.is_file()and p not in (Q/'HDF.json',Q/'MF.json')],exclusions=['MF/HDF self digests','Final sealer return/peer Final occurs after sealing; Root captures original bytes separately.'],immutable_after_publish=True,formal_acceptance=False,execution_grant=False))
    h=json.loads(Path(b['base_hdf_ref']['path']).read_bytes())
    h.update(caller_ref=b['caller_ref'],registrar_ref=b['caller_ref'],contract_ref=b['contract_ref'],source_inputs_ref=b['source_inputs_ref'],manifest_ref=mf,source_controls_ref=b['new_controls_ref'],Source_controls_passed=13,new_unreached_or_delta_controls=13,original_prefix_successes_reused=0,source_author_audit_ref=audit,Source_full_closure_ref=fullguard,source_author=ACTOR,author_thread=THREAD,parent_Root_thread=ROOT_THREAD,base_Source_hdf_ref=b['base_hdf_ref'],base_Source_mf_ref=b['base_mf_ref'],base58_controls_reused_ref=b['reused_base_58_controls_ref'],old58_353_17_4154_replayed=False,directory_inverse_ref=b['inverse_ref'],directory_delta_guard_ref=b['new_guard_ref'],Root_original1146_and_Task102_witnesses=b['Root_finding_witnesses'],report_ref=reportref,static_boundary_ref=static,current_Source_revision='CALLER02_DIRECTORY_ROOT_ONLY',future_SourceReviewer_root_witness=None,future_RuntimeScope=None,future_runtime_qualification=None,future_RootScope=None,future_current4=None,future_actual_bootstrap=None,Source_self_acceptance=False,status='SOURCE_ONLY_PENDING_NONAUTHOR_REVIEW_AND_ROOT_BINDING',live_Canon_read_or_held=False,Root_Go_Native_SQL_TP_model_calls=0,formal_acceptance=False,parent_acceptance=False,execution_grant=False,STOP=True)
    hdf=write('HDF.json',h)
    print(json.dumps(dict(schema='researchos.public21-root-caller-source-delivery.v1',operation='SOURCE_PUBLICATION',source_author=ACTOR,author_backend=BACKEND,author_thread=THREAD,root_thread_id=ROOT_THREAD,status=h['status'],hdf_ref=hdf,mf_ref=mf,caller_ref=b['caller_ref'],contract_ref=b['contract_ref'],source_inputs_ref=b['source_inputs_ref'],exact_inverse_ref=b['inverse_ref'],source_guard_ref=fullguard,new_controls_passed=13,old58_353_17_4154_replayed=False,Source_self_acceptance=False,Root_stages_executed=[],formal_acceptance=False,execution_grant=False,STOP=True),ensure_ascii=False));return 0
if __name__=='__main__':
    rc=1
    try:rc=main()
    except BaseException:traceback.print_exc()
    print('ROOT_PYTHON_EXIT='+str(rc));sys.exit(rc)
