"""Seal only this new Main-root producer Source package after pure controls."""
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')

def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value,text=False):
    raw=value.encode() if text else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(raw)
    return pin(N/name)

assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
c=load(N/'source.choice.json');contract=load(N/'root-calling-contract.json')
controls=load(N/'source-controls.revision2.json');inputs=load(N/'source-input-pins.original.json')
assert controls['status']=='PASS' and controls['new_check_count']==107
assert controls['original_inputs_unchanged']==inputs['count']==4000
assert controls['real_producer_runs']==0 and controls['future_authority_documents_only_in_memory'] is True
assert len(c['source21'])==21 and len(c['main_seven_after_refs'])==7
assert all(pin(N/name)==contract['bound_source_refs'][field] for field,name in contract['source_file_bindings'].items())
for name in ('source-preparation.guard.cleanup.actual.json','source-controls.guard.cleanup.actual.json','source-controls.revision2.guard.cleanup.actual.json'):
    closed=load(N/name)
    assert closed['closed'] is True and not closed['errors'] and closed['retained_handles_count']==0
failure=load(N/'failure952.original-tool-io.json')
assert failure['root_assigned_ordinal']==952 and failure['outer_exit']==1 and failure['complete_original_pair'] is True
assert all(failure[k] is None for k in ('SourcePython_exit','Go_exit','Native_exit','Model_exit'))
for name in ('preparation.original-tool-io.json','final-bind.original-tool-io.json','final-controls-completion.original-tool-io.json'):
    result=load(N/name)['saved_tool_record']['result']
    assert result['exit_code']==0 and 'SourcePythonExit=0' in result['output']
gp=c['guard_ref'];assert pin(gp['path'])==gp
gm=types.ModuleType('main_c19_seal_guard');gm.__file__=gp['path']
exec(compile(Path(gp['path']).read_bytes(),gp['path'],'exec'),gm.__dict__)
refs={r['path'].casefold():r for r in inputs['refs']}
for p in N.iterdir():
    assert p.is_file()
    ref=pin(p);key=ref['path'].casefold();assert key not in refs or refs[key]==ref;refs[key]=ref
forbidden={r['path'].casefold() for r in c['main_seven_after_refs']}|{str(R/'execution/v2.4'/f'{n}.json').casefold() for n in ('checkpoint','path_ownership','step_state','commands')}
assert not forbidden.intersection(refs)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    for ref in refs.values():assert pin(ref['path'])==ref
    assert all(not Path(c[k]).exists() for k in ('receipt_root','scratch_root','output_root'))
    save('final-source-proof.json',dict(schema='researchos.w09-main-c19-producer-final-source-proof.v1',
        status='SOURCE_ONLY_COMPLETE',source_controls_ref=pin(N/'source-controls.revision2.json'),new_controls=107,
        historical_104_counted_as_new=False,original_inputs_unchanged=4000,guarded_refs=len(refs),
        Source_guard_excludes_Root_seven_targets_and_Canon=True,Source21=c['source21'],
        Source21_actual_Main_current_qualification='NOT_PERFORMED_IN_THIS_SOURCE_TASK; mandatory before future prepare',
        expected_Main_seven_after_refs=c['main_seven_after_refs'],future_paths={k:c[k] for k in ('receipt_root','scratch_root','output_root')},
        all_future_outputs_absent=True,actual_Main_preparation=False,actual_Main_native_producer=False,
        actual_dispatcher=False,worktree_created=False,Main_Source_written=False,Canon_written=False,
        Git_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0))
finally:
    cleanup=guard.close();save('source-seal.guard.cleanup.actual.json',cleanup)
assert cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0
save('failure-origins.json',dict(new_original_failures=[dict(ordinal=952,original_io_ref=pin(N/'failure952.original-tool-io.json'),
    outer_exit=1,SourcePython_exit=None,Go_exit=None,Native_exit=None,Model_exit=None)],root_reported_next_live=953,
    counter_reset=False,Source_controls_success_does_not_supersede_original_failure=True))
report='''# W09 C19 Main-root producer Source

本包实现新的两阶段 caller。固定 cwd/source_root 为 Main；prepare 仅创建专属 receipt、profile、TEMP 和 GOCACHE，run 依次调用一次 owned go list -export 和一次 owned Python producer。producer 保留原六份审查 Source 与两项 Go 父测试，产生固定新 run 的五项 C19 assertion，Source21、owned/raw 绝对路径均必须属于 Main。本轮没有执行这些实际阶段。

launcher 只给加载的 retrieval runner 注入局部 UUID 对象，恰好允许一次 uuid4，既不改 stdlib uuid 全局状态，也不修改 Main 文件。launcher、permit/started/closed、环境、argv 和 run/output 绑定都是后续 mode 独审的强制输入。不能借用旧候选 packet 或旧 mode review。

实际 prepare 的前置条件为：Main 七目标实际 adoption 及非作者实际独审、当前21项源码与commands精确匹配、本包新的独立 Source 接受、Root 新 scope、CP>367/OW>171 的 owner/worker 登记和四文档 vector。scope 不包含 vector 引用；登记后 request 绑定二者，避免循环 hash。prepare/run 必须使用同一 request/vector。

固定 toolchain；351包 roster 和3905稳定 compiler refs 只从旧 metadata 建立有限清单，不把历史 Native 结果当作新结果。19项 Module GoMod、稳定 Main/GOROOT/module Source 在 go list 前持锁；实际新生成 export/cache/compiler 输入在 Go test 前持锁。使用全新私有 GOCACHE，禁网络模块下载。超时为 list240 / producer420 / innerGo180。

任一步失败停止，不自动重跑。每个 Job 保留原始 stdout/stderr 和原始结果对象；FILETIME 同时保留 Python 整数与十进制字符串，未观察到的各子进程数值退出码为 null。ordinary failure 尽力逐个关闭所有 guard，只在 Job 已确认 idle 后保存部分 packet；进程丢失保留 intent 和现有证据供 Root 明确核对。prepare-ready 和 producer-closed 只在必要 guard/Job/archive 完整闭合后发布。

最终107项新纯 Source 控制通过，4000项既有输入 pin 不变，准备、初轮控制、最终控制、封存四次 Source guard 均 closed、retained=0。内存 fake helper 的 nonzero/timeout/unknown/unclosed 行是控制输入，不是真实 Native 执行。初轮104控制为此前未封存版本结果，未与最终107累加。完整字节逆操作及未封存绑定修订全文均保留。

本任务未读/持锁 Root 七目标与 Canon，未写 Main/Canon，未执行 Git/Go/SQL/API/model/dispatcher/worktree/实际 producer。Source21 的当前 Main 资格由未来实际 gate 验证。一次只读工具错误已独立保存完整原始 pair：ordinal952，outer1，Python/Go/Native/Model均null；当前Root下一序号953。后续正确Source调用0没有覆盖原失败。

状态为 SOURCE_READY_PENDING_INDEPENDENT_REVIEW。本包不授权执行，不接受 formal C19，不改变 W09 parent；formal_case_accepted_delta=0。后续依次需要本包独立 Source 审查、Root新登记与actual授权、实际Main producer及模式独审、两条真实router/dispatcher消费与正式资格审查。
'''
save('REPORT.md',report,True)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
manifest=save('MF.json',dict(schema='researchos.w09-main-c19-producer-source-manifest.v1',members=members,member_count=len(members)))
fields={'report_ref':'REPORT.md','root_calling_contract_ref':'root-calling-contract.json',
    'prepare_caller_ref':'prepare_main_c19.actual_owned.py','producer_caller_ref':'run_main_c19.actual_owned.py',
    'launcher_ref':'main_c19_launcher.source.py','runtime_ref':'main_c19_runtime.source.py','choice_ref':'source.choice.json',
    'compiler_blueprint_ref':'compiler-source-blueprint.json','caller_complete_byte_inverse_ref':'caller.complete-byte-inverse.json',
    'source_controls_ref':'source-controls.revision2.json','source_input_pins_ref':'source-input-pins.original.json',
    'final_source_proof_ref':'final-source-proof.json','failure_origins_ref':'failure-origins.json'}
h=dict(schema='researchos.w09-main-c19-producer-source-handoff.v1',actor_id=c['actor_id'],
    status='SOURCE_READY_PENDING_INDEPENDENT_REVIEW',manifest_ref=manifest,**{k:pin(N/v) for k,v in fields.items()},
    fixed_paths={k:c[k] for k in ('source_root','run_id','receipt_root','scratch_root','output_root')},
    source21=c['source21'],main_seven_after_refs=c['main_seven_after_refs'],selected_tests=c['selected_tests'],expected_native_ids=c['expected_native_ids'],
    new_source_controls=107,original_inputs_unchanged=4000,all_source_guards_closed=True,
    guard_cleanup_refs=[pin(N/v) for v in ('source-preparation.guard.cleanup.actual.json','source-controls.guard.cleanup.actual.json',
        'source-controls.revision2.guard.cleanup.actual.json','source-seal.guard.cleanup.actual.json')],
    source_stage_actual_exits=dict(preparation=0,final_binding=0,final_controls=0),
    original_tool_failure_952_ref=pin(N/'failure952.original-tool-io.json'),root_reported_next_live=953,
    actual_Main_preparation=False,actual_Main_native_producer=False,actual_dispatcher=False,actual_executed=False,
    Main_Source_written=False,Canon_written=False,Git_Go_SQL_API_model_calls=0,execution_grant=False,
    formal_acceptance=False,parent_acceptance=False,formal_case_accepted_delta=0,
    required_next=['Independent Source review of this exact package','Independent actual Main7 adoption proof',
        'Root fresh native scope owner worker current vector and actual grant','Actual Main producer',
        'Independent actual mode review including launcher','Two actual C19 consumers and formal qualification'])
href=save('HDF.json',h)
for ref in members:assert pin(ref['path'])==ref
assert h['manifest_ref']==pin(N/'MF.json')
print(json.dumps(dict(status=h['status'],HDF=href,MF=manifest,contract=h['root_calling_contract_ref'],
    prepare=h['prepare_caller_ref'],run=h['producer_caller_ref'],runtime=h['runtime_ref'],launcher=h['launcher_ref'],
    new_controls=107,original_inputs_unchanged=4000,actual=False)))
