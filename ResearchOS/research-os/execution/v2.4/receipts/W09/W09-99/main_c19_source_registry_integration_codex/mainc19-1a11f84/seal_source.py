import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def save(name,value):
    raw=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(raw)
    return pin(N/name)

change=json.loads((N/'change-set.json').read_bytes())
controls=json.loads((N/'source-controls.json').read_bytes())
original=json.loads((N/'source-input-pins.original.json').read_bytes())
assert controls['status']=='PASS' and controls['check_count']==471
assert controls['original_inputs_unchanged']==original['count']==140
assert not (N/'actual-adoption').exists()
assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
gp=change['guard_ref'];assert pin(gp['path'])==gp
gm=types.ModuleType('w09_main_source_seal_guard');gm.__file__=gp['path']
exec(compile(Path(gp['path']).read_bytes(),gp['path'],'exec'),gm.__dict__)
refs={r['path'].casefold():r for r in original['refs']}
for p in N.iterdir():
    assert p.is_file()
    ref=pin(p);key=ref['path'].casefold()
    assert key not in refs or refs[key]==ref
    refs[key]=ref
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    for ref in original['refs']:assert pin(ref['path'])==ref
    before_status=[]
    for i,row in enumerate(change['targets']):
        p=Path(row['target'])
        if row['before_ref'] is None:assert not p.exists()
        else:assert pin(p)==row['before_ref']
        before_status.append(dict(target=str(p),still_before=True,exists=row['before_ref'] is not None))
    save('final-source-proof.json',dict(status='SOURCE_ONLY_COMPLETE',source_input_count=140,
        all_original_inputs_unchanged=True,seven_targets_still_before=before_status,
        no_actual_adoption_output=True,controls_ref=pin(N/'source-controls.json'),
        source21_count=21,other15_current_exact=True,actual_adoption=False,
        actual_Win32_transaction=False,product_Git_Go_SQL_API_model_calls=0))
finally:
    cleanup=guard.close()
    save('source-seal.guard.cleanup.actual.json',cleanup)
    assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0

save('failure-origins.json',dict(new_original_failures=[],no_product_rerun=True,
    prior_mapping_diagnostics_not_recounted=[942,943],consumer_review_prior_failure_not_recounted=[946],
    root_reported_next_at_last_message=947))
report='''# W09 C19 Main source and registry adoption — Source only

七个业务目标的采用源码已封存，尚未执行；formal delta = 0。

- 六个 Main 源码精确引用原 sealed bytes：三文件当前存在、三文件当前不存在；加 commands.json 共四个 existing、三个 absent。
- 原 v7 report 的 Source21 已逐项核对：六个待采用 pin 完全一致，其余十五个 Main 文件当前一致。
- commands.proposed.json 只改 test.research.fixture 与 test.retrieval 两条 entry 的 executable_tool/argv/allowed_env/selectors/tool_env。全文件字节 inverse 保留所有其他字段与 entry。
- 六环境变量仅加到 allowed_env；required_env 仍为空。router 不加 -I；W08 保留旧程序并通过 locked tool_env 注入 RESEARCHOS_GO；W09-01 原程序、streams 与 exit 转发保持。
- Root caller 只允许七个固定业务路径和本包 actual-adoption 下六个固定回执文件；不复制 producer/report，不改 CP/OW/SS，不跑 dispatcher/Go/Git/SQL/API/Model。
- 采用时持有全部七目标的 Windows shareMode=0 文件句柄，并持有防止父目录改名的目录句柄。正常失败在同句柄下回滚 existing 原字节，仅把本次 CREATE_NEW 的三个新文件标记 delete-on-close。
- durable intent 保存全部 before/after 字节。进程强杀或断电不宣称跨七文件崩溃原子性；异常回滚/cleanup 不完整必须交 Root 明确恢复，不自动重跑。
- Root 先登记独立审查通过的 scope 到后继 CP/OW，再封四文件 vector，最后生成独立 request 引用 scope/vector，避免哈希循环。Source caller 必须绑定 future CP > 366、OW > 170，以及真实的 Source 独审和组件实际独审。
- 组件实际独审使用真实已封 HDF schema researchos.w09-c19-v7-consumer-independent-actual-handoff.v1 / decision ACTUAL_TWO_C19_COMPONENT_CONSUMERS_VERIFIED_PASS；仍 NOT_CURRENT_NOT_REGISTERED。

验证：471 个纯源码/内存控制通过；包含两 entry 的完整 inverse、有限路由矩阵、旧分支 AST 保持、每个 partial-write/open/create/journal 失败点的内存回滚、外来 CAS/新文件不覆盖、回滚设备错误诚实返回、未来 Root/source-review/owner/vector 负例。140 个原输入保持不变，两个 SourceReadGuard 均闭合、零保留句柄。没有执行真实 Windows 七目标事务，也没有产品调用。

后续仍 OPEN：独立 Source 审查；Root 显式采用授权/新 owner-vector；真实七目标采用；新的双路 dispatcher 回执与 CURRENT 适用性；生产 W09 formal profile 及 W09 其余父任务门。现有 C19 组件 PASS 不自动接受 W09-99 或 A06。
'''
with (N/'REPORT.md').open('xb') as f:f.write(report.encode())
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file() and p.name not in ('MF.json','HDF.json')]
mref=save('MF.json',dict(schema='researchos.w09-main-c19-source-registry-manifest.v1',members=members,member_count=len(members)))
href=save('HDF.json',dict(schema='researchos.w09-main-c19-source-registry-handoff.v1',
    actor_id='codex:/root/command_queue_impl',status='SOURCE_READY_PENDING_INDEPENDENT_SOURCE_REVIEW',
    manifest_ref=mref,report_ref=pin(N/'REPORT.md'),caller_ref=pin(N/'adopt_main_c19.source.py'),
    change_set_ref=pin(N/'change-set.json'),commands_proposed_ref=pin(N/'commands.proposed.json'),
    registry_full_byte_inverse_ref=pin(N/'commands.complete-byte-inverse.json'),
    root_calling_contract_ref=pin(N/'root-calling-contract.json'),source_controls_ref=pin(N/'source-controls.json'),
    final_source_proof_ref=pin(N/'final-source-proof.json'),source_input_pins_ref=pin(N/'source-input-pins.original.json'),
    guard_cleanup_refs=[pin(N/'source-preparation.guard.cleanup.actual.json'),pin(N/'source-seal.guard.cleanup.actual.json')],
    source21_report_ref=change['source21_report_ref'],source21_count=21,other15_current_exact=True,
    exact_business_targets=[r['target'] for r in change['targets']],business_target_count=7,
    main_existing_sources=3,main_absent_sources=3,registry_existing_targets=1,registry_changed_entries=2,
    producer_actual_review_handoff_ref=change['producer_actual_review_handoff_ref'],
    producer_actual_review_manifest_ref=change['producer_actual_review_manifest_ref'],
    component_actual_review_handoff_ref=change['component_actual_review_handoff_ref'],
    component_actual_review_manifest_ref=change['component_actual_review_manifest_ref'],
    consumer_closed_ref=change['original_consumer_closed_ref'],source_controls=471,original_inputs_unchanged=140,
    actual_Win32_adoption=False,actual_adoption=False,Main_written=False,registry_written=False,
    CP_OW_SS_written=False,producer_report_copied=False,formal_dispatcher_executed=False,
    product_Git_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0,parent_acceptance=False,
    crash_atomic=False,ordinary_failure_rollback_source=True,process_loss_requires_Root_reconciliation=True,
    new_original_failures=[],execution_grant=False,STOP=True,FINAL=True))
assert pin(N/'MF.json')==mref
for member in members:assert pin(member['path'])==member
print(json.dumps(dict(status='SOURCE_SEALED_STOP',handoff_ref=href,manifest_ref=mref,
    caller_ref=pin(N/'adopt_main_c19.source.py'),change_set_ref=pin(N/'change-set.json'),
    contract_ref=pin(N/'root-calling-contract.json'),controls=471,guard_closed=True),ensure_ascii=False))
