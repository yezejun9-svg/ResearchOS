"""Seal the Mainv2 package after new Source controls, with a real read guard."""
import hashlib
import json
from pathlib import Path
import types

N=Path(__file__).resolve().parent
R=Path('D:/作品集/ResearchOS/research-os')
OLD=R/'execution/v2.4/receipts/W09/W09-99/main_c19_source_registry_integration_codex/mainc19-1a11f84'
def pin(p):
    p=Path(p).resolve(strict=True);raw=p.read_bytes()
    return dict(path=str(p),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
def load(p):return json.loads(Path(p).read_bytes())
def save(name,value,raw=False):
    data=value.encode() if raw else (json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
    with (N/name).open('xb') as f:f.write(data)
    return pin(N/name)

assert not (N/'HDF.json').exists() and not (N/'MF.json').exists()
change=load(N/'change-set.json');controls=load(N/'source-controls.json');inputs=load(N/'source-input-pins.original.json')
assert controls['status']=='PASS' and controls['check_count']==113 and controls['original_inputs_unchanged']==inputs['count']==208
assert controls['old_471_historical_only'] and controls['virtual_Root_or_reviewer_files_written']==0
gp=change['guard_ref'];assert pin(gp['path'])==gp
gm=types.ModuleType('mainv2_seal_guard');gm.__file__=gp['path']
exec(compile(Path(gp['path']).read_bytes(),gp['path'],'exec'),gm.__dict__)
refs={r['path'].casefold():r for r in inputs['refs']}
for p in N.iterdir():
    assert p.is_file()
    ref=pin(p);key=ref['path'].casefold();assert key not in refs or refs[key]==ref;refs[key]=ref
guard=gm.SourceReadGuard(per_file_cap=256*1024*1024,total_cap=2*1024*1024*1024)
try:
    guard.acquire(list(refs.values()))
    for ref in refs.values():assert pin(ref['path'])==ref
    targets=[]
    for row in change['targets']:
        current=pin(row['target']) if Path(row['target']).is_file() else None
        assert current==row['before_ref'];targets.append(dict(target=row['target'],current_ref=current,still_before=True))
    assert not (N/'actual-adoption').exists()
    save('final-source-proof.json',dict(schema='researchos.main-c19-v2-final-source-proof.v1',status='SOURCE_ONLY_COMPLETE',
        source_controls_ref=pin(N/'source-controls.json'),new_v2_controls=113,historical_471_counted_as_v2=False,
        original_inputs_unchanged=208,seven_targets_still_before=targets,source21_unchanged=True,
        seven_after_target_refs=[r['after_target_ref'] for r in change['targets']],actual_adoption=False,
        Canon_written=False,actual_dispatcher=False,Git_Go_SQL_API_model_calls=0,formal_case_accepted_delta=0))
finally:
    cleanup=guard.close();save('source-seal.guard.cleanup.actual.json',cleanup)
assert cleanup['closed'] and not cleanup['errors'] and cleanup['retained_handles_count']==0
save('failure-origins.json',dict(new_original_failures=[],root_reported_next_live=951,counter_reset=False,
    old_finding_is_source_counterexample_not_new_tool_failure=True))
report='''# Mainv2 scope type contract — Source only

修复 CP367-V3-P1-CROSS-CALLER-INT-BOOL：七个布尔开关要求 is False；formal_case_accepted_delta 和 new_Go_SQL_API_model_calls 要求 type(value) is int 且 == 0。

本包仅修改 caller 固定 namespace 与上述谓词；完整字节 inverse 同时保留 caller 以及 change-set/contract 的原、新全文和 spans。七个最终目标 bytes、六个 sealed Source refs、commands.proposed.json、四个完整 before archive 及 commands 完整 inverse 均保持原样。旧 Source 包和其独审结论未修改。

本轮 113 个新纯 Source 控制 PASS，208 个旧输入 exact pin 不变。真实 Root registration facts_scope、validate_live_context、transform 与 Mainv2 完整 validate_scope 通过同一内存 scope/owner/worker/CP/OW/vector 串接；旧谓词 P1 被内存反例复现。计数的 false/true、0.0/-0.0、正负非零整数、字符串、null、缺失均被两端拒绝；非 boolean-false 开关与绑定/角色错误同样拒绝。未来 Root/reviewer 文档仅存在于内存，未落盘。旧 471 控制只是历史结果，不计为本包新通过。

准备、控制、封存各自使用真实 SourceReadGuard 并完整关闭；Main/commands/CP/OW/SS 未写入，七个目标仍为 before，未执行 adoption、dispatcher、Git、Go、SQL、API、model。actual-adoption 目录不存在。无新的原始工具失败。

Root 后续必须绑定本包新的 HDF/MF/contract/caller/change-set 和新的独立 Source 决策，再更新 registration facts/Root scope；旧 scope 或旧 Source reviewer 的接受不能直接作为本包的执行授权。当前 canon 仍是 CP366/OW170。

范围外后续：旧候选 native packet 的 assertion 和嵌套 raw pins 固化候选绝对路径，Source21 相同不能自动证明 Main 原样消费可用。此包不复制或重写旧 packet，不执行 Main producer 或正式消费者。formal_case_accepted_delta = 0，W09 parent acceptance 不变。
'''
save('REPORT.md',report,True)
members=[pin(p) for p in sorted(N.iterdir()) if p.is_file()]
assert all(Path(r['path']).parent==N for r in members)
manifest=save('MF.json',dict(schema='researchos.w09-main-c19-source-registry-manifest.v1',source_revision='v2',members=members,member_count=len(members)))
h=load(OLD/'HDF.json')
mapping={'manifest_ref':'MF.json','report_ref':'REPORT.md','caller_ref':'adopt_main_c19.source.py','change_set_ref':'change-set.json',
    'commands_proposed_ref':'commands.proposed.json','registry_full_byte_inverse_ref':'commands.complete-byte-inverse.json',
    'root_calling_contract_ref':'root-calling-contract.json','source_controls_ref':'source-controls.json','final_source_proof_ref':'final-source-proof.json',
    'source_input_pins_ref':'source-input-pins.original.json'}
for field,name in mapping.items():h[field]=pin(N/name)
h.update(source_revision='v2',source_controls=113,original_inputs_unchanged=208,
    guard_cleanup_refs=[pin(N/name) for name in ('source-preparation.guard.cleanup.actual.json','source-controls.guard.cleanup.actual.json','source-seal.guard.cleanup.actual.json')],
    caller_complete_byte_inverse_ref=pin(N/'caller.complete-byte-inverse.json'),metadata_complete_byte_inverse_ref=pin(N/'metadata.complete-byte-inverse.json'),
    fix_origin_ref=pin(N/'fix-origin.json'),previous_handoff_ref=pin(OLD/'HDF.json'),previous_manifest_ref=pin(OLD/'MF.json'),
    fixed_finding='CP367-V3-P1-CROSS-CALLER-INT-BOOL',old_471_historical_only=True,
    scope_boolean_false_fields=load(N/'root-calling-contract.json')['scope_boolean_false_fields'],
    scope_strict_integer_zero_fields=['formal_case_accepted_delta','new_Go_SQL_API_model_calls'],
    new_independent_Source_review_required=True,old_review_is_not_v2_execution_authority=True,
    registration_facts_and_scope_rebind_required=True,actual_registration=False)
href=save('HDF.json',h)
for ref in members:assert pin(ref['path'])==ref
assert h['manifest_ref']==manifest
print(json.dumps(dict(status='MAINV2_SOURCE_SEALED_PENDING_INDEPENDENT_REVIEW',HDF=href,MF=manifest,
    caller=h['caller_ref'],contract=h['root_calling_contract_ref'],change_set=h['change_set_ref'],new_v2_checks=113,
    original_inputs_unchanged=208,actual_adoption=False)))
