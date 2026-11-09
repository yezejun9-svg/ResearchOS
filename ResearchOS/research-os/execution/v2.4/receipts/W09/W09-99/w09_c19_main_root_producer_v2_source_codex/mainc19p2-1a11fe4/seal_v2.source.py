"""Seal the cleanup successor only after exact Source controls and guard closure."""
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
OLD=R/'execution/v2.4/receipts/W09/W09-99/w09_c19_main_root_producer_source_codex/mainc19p-1a11fbc'
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes();return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value,text=False):
    raw=value.encode() if text else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(raw)
    return pin(N/name)

assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
c=load(N/'source.choice.json');contract=load(N/'root-calling-contract.json')
controls=load(N/'source-controls.revision2.json');inputs=load(N/'source-input-pins.original.json');origin=load(N/'fix-origin.json')
assert controls['status']=='PASS' and controls['new_check_count']==113 and controls['original_inputs_unchanged']==inputs['count']==4047
assert origin['decision']=='REQUEST_CHANGES' and pin(origin['handoff_ref']['path'])==origin['handoff_ref']
assert all(pin(N/name)==contract['bound_source_refs'][field] for field,name in contract['source_file_bindings'].items())
guard_names=['source-preparation.guard.cleanup.actual.json','source-controls.guard.cleanup.actual.json','source-controls.revision2.guard.cleanup.actual.json']
for name in guard_names:
    q=load(N/name);assert q['closed'] is True and not q['errors'] and q['retained_handles_count']==0
for name in ('preparation.original-tool-io.json','refinement.original-tool-io.json','final-controls.original-tool-io.json'):
    q=load(N/name)['saved_tool_record']['result'];assert q['exit_code']==0 and 'SourcePythonExit=0' in q['output']
refs={r['path'].casefold():r for r in inputs['refs']}
for p in N.iterdir():
    assert p.is_file()
    ref=pin(p);key=ref['path'].casefold();assert key not in refs or refs[key]==ref;refs[key]=ref
forbidden={r['path'].casefold() for r in c['main_seven_after_refs']}|{str(R/'execution/v2.4'/f'{n}.json').casefold() for n in ('checkpoint','path_ownership','step_state','commands')}
assert not forbidden.intersection(refs)
gp=c['guard_ref'];assert pin(gp['path'])==gp
gm=types.ModuleType('cleanup_v2_seal_guard');gm.__file__=gp['path'];exec(compile(Path(gp['path']).read_bytes(),gp['path'],'exec'),gm.__dict__)
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    for ref in refs.values():assert pin(ref['path'])==ref
    assert all(not Path(c[k]).exists() for k in ('receipt_root','scratch_root','output_root'))
    save('final-source-proof.json',dict(schema='researchos.w09-main-c19-producer-v2-final-source-proof.v1',status='SOURCE_ONLY_COMPLETE',
        source_controls_ref=pin(N/'source-controls.revision2.json'),new_controls=113,original_inputs_unchanged=4047,
        predecessor_Source_and_REQUEST_CHANGES_exact=True,Source_guard_excludes_Root_seven_and_Canon=True,
        future_fixed_paths={k:c[k] for k in ('source_root','run_id','receipt_root','scratch_root','output_root')},
        future_outputs_absent=True,actual_executed=False,Main_Canon_read_or_written=False,
        Git_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0))
finally:
    cleanup=guard.close();save('source-seal.guard.cleanup.actual.json',cleanup)
assert cleanup['closed'] is True and not cleanup['errors'] and cleanup['retained_handles_count']==0
guard_names.append('source-seal.guard.cleanup.actual.json')
save('failure-origins.json',dict(new_original_failures=[],retained_original_failure952_ref=origin['retained_original_failure952_ref'],
    root_reported_next_live=954,Root_reported_953_belongs_to_other_review=True,counter_reset=False,
    expected_memory_faults_are_not_original_tool_failures=True))
report='''# Main C19 producer v2 — Source cleanup correction

修复 MAIN-C19-PRODUCER-01，绑定 v1 非作者 REQUEST_CHANGES 的完整 HDF/MF。旧 Source、952 原始失败、Main 七目标、Canon 和实际目录均未修改。新 run 为 9e912dfc1058454da08ae7f93f4de24d；全部 caller/module/launcher/choice/contract refs 已重绑。七目标与21项 Source roster、toolchain、351包蓝图、两项测试、240/420/180超时和 one-shot 约束不变；蓝图字节相同，只作有限编译输入清单。

receipt presence/pin/read/decode/closure 检查及 packet archive 各自捕获错误；逐 guard close 位于外层 guaranteed finally。每项 close、闭合状态判定、cleanup-save 分开隔离，保存失败不抹掉成功关闭的原始 observation。关闭后的 Job 状态取自已保护的观察，不再无保护重读 receipt。缺失、部分 JSON、不可读、pin 失败或不一致都不能证明 Job 已关闭。

invoke 保存 helper 原异常对象与异常链，stdout/stderr pin、invocation-save、progress 输出错误单独聚合。stage 同样保留 primary exception、invocation diagnostics、inspection/archive/close/save 分类；final-save/progress 失败不能遮蔽 primary。尚未创建实际目录时直接输出未保存诊断，不额外建目录；输出也失败时异常文本仍携带原错误与次级分类。私有 launcher 的 UUID 还原、观察、pin、closed-save 同样隔离并保留原 runner 异常。任何失败停止，不自动重跑，不覆盖部分原始文件。

113项最终新纯 Source 控制通过：重现旧 finally partial JSON 导致零关闭；新路径覆盖 missing/partial/unreadable/pin/presence、archive、首个/中间 close、异常 cleanup observation、cleanup-save、多重组合失败；五个 guard 关闭动作始终全部尝试。实际新 stage except/finally/postlude 的内存执行证明 primary identity/cause 保留、未知 Job 不被报 closed、final-save/progress 错误归入 secondary。invoke 精确原始 bytes/FILETIME、一调用无重试、launcher异常保全，以及未建目录的失败输出均验证。v1的107与v2初轮109只作历史，不累加为最终控制。

4047项原输入 pin 不变；准备、初轮控制、最终控制、封存的真实 Source guards 全部关闭，retained=0。Source工具均outer/Python0，无新增原始工具失败。952原始pair保持原引用；Root报告的953属于另一个独审，下一序号954，不重置。

本包仍为 SOURCE_READY_PENDING_INDEPENDENT_REVIEW，尚无Actual授权。未读取或持锁Root七目标/Canon，未执行Main producer、Go、Git、CLI、SQL、API、model、dispatcher。后续必须独立审查本v2，再由Root使用新的scope登记owner/worker及当前四文档vector；最低CP>367/OW>171不限定恰好CP368。实际producer和模式独审、两消费者及formal资格均待后续。formal_case_accepted_delta=0，W09 parent不变。
'''
save('REPORT.md',report,True)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
manifest=save('MF.json',dict(schema='researchos.w09-main-c19-producer-source-manifest.v1',source_revision='v2',members=members,member_count=len(members)))
h=load(OLD/'HDF.json')
mapping={'manifest_ref':'MF.json','report_ref':'REPORT.md','root_calling_contract_ref':'root-calling-contract.json',
    'prepare_caller_ref':'prepare_main_c19.actual_owned.py','producer_caller_ref':'run_main_c19.actual_owned.py',
    'launcher_ref':'main_c19_launcher.source.py','runtime_ref':'main_c19_runtime.source.py','choice_ref':'source.choice.json',
    'compiler_blueprint_ref':'compiler-source-blueprint.json','caller_complete_byte_inverse_ref':'complete-byte-inverse.json',
    'source_controls_ref':'source-controls.revision2.json','source_input_pins_ref':'source-input-pins.original.json',
    'final_source_proof_ref':'final-source-proof.json','failure_origins_ref':'failure-origins.json'}
for key,name in mapping.items():h[key]=pin(N/name)
h.update(source_revision='v2',fixed_finding='MAIN-C19-PRODUCER-01',fix_origin_ref=pin(N/'fix-origin.json'),
    predecessor_handoff_ref=origin['predecessor_handoff_ref'],predecessor_manifest_ref=origin['predecessor_manifest_ref'],
    REQUEST_CHANGES_handoff_ref=origin['handoff_ref'],REQUEST_CHANGES_manifest_ref=origin['manifest_ref'],
    fixed_paths={k:c[k] for k in ('source_root','run_id','receipt_root','scratch_root','output_root')},
    new_source_controls=113,original_inputs_unchanged=4047,guard_cleanup_refs=[pin(N/name) for name in guard_names],
    source_stage_actual_exits=dict(preparation=0,refinement=0,final_controls=0),new_original_failures=[],
    root_reported_next_live=954,new_independent_Source_review_required=True,old_107_controls_historical_only=True)
href=save('HDF.json',h)
for ref in members:assert pin(ref['path'])==ref
print(json.dumps(dict(status=h['status'],HDF=href,MF=manifest,contract=h['root_calling_contract_ref'],
    prepare=h['prepare_caller_ref'],run=h['producer_caller_ref'],runtime=h['runtime_ref'],launcher=h['launcher_ref'],
    run_id=c['run_id'],new_controls=113,original_inputs_unchanged=4047,actual=False)))
