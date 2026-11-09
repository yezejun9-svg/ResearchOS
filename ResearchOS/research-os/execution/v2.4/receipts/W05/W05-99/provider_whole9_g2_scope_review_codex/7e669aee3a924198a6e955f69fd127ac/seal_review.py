from pathlib import Path
import json, hashlib, datetime

OUT = Path(__file__).resolve().parent
ROOT = Path('D:/作品集/ResearchOS/research-os')
INP = Path(json.loads((OUT/'locations.json').read_text(encoding='utf-8'))['input'])
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def put(name, obj):
    p = OUT/name
    with p.open('x', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
def ref(p, start=None, end=None):
    p=Path(p)
    r={'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size}
    if start is not None: r['locator']={'line_start':start,'line_end':end or start}
    return r
def src(name,start,end=None): return ref(INP/'snapshot/candidate/internal/domain'/name,start,end)

before=json.loads((OUT/'inputs.before.json').read_text(encoding='utf-8'))
after=[{'path':r['path'],'sha256':digest(Path(r['path'])),'bytes':Path(r['path']).stat().st_size} for r in before]
assert before==after, 'Input drift: no seal allowed'
put('inputs.after.json',after)
m=json.loads((INP/'manifest.json').read_text(encoding='utf-8'))
checks=[{'path':r['path'],'equal':digest(INP/r['path'])==r['sha256'] and (INP/r['path']).stat().st_size==r['bytes']} for r in m['files']]
assert len(checks)==52 and all(r['equal'] for r in checks)
git=json.loads((OUT/'candidate_git_binding.json').read_text(encoding='utf-8'))
assert len(git)==24 and all(r['equal'] and r['exit']==0 for r in git)
put('audit.json',{'manifest_listed':52,'including_manifest':53,'manifest_checks':checks,'before_after_count':len(before),'drift':[], 'candidate_git_files':24,'candidate_git_all_equal':True,'candidate':'6fb5263681c17f0e50920c354dc07ed440a23714','additional_immutable_git_input':ref(OUT/'budget_test.gitblob.txt'),'executed_tests':0,'sql_calls':0,'go_calls':0,'node_calls':0,'http_calls':0,'model_calls':0,'product_writes':0})

conditions=[
('B01','精确函数边界纠正','providerBrokerFixture 114–215；Preflight 552–596；Quarantine 598–635。coordinatorFixtureProgram 118–204。提案的 219/642/223 末行越入 held positive、Archived 或原 NativeQualification；不得据旧行段改到这些函数。仅相邻新增私有测试 helper 与必要 import。原签名、variadic flags、全部原断言和 held2 函数体原字节保留。'),
('B02','budget-before-context 同一真实构造链','callback 放在 Goal ACTIVATE 后、Task POST 前；通过原 owner GET/PUT 改 cap，再读取同一 Goal 返回当前 If-Match。此时不得已有 Task/context/Run，不重建已准入 Run。临时 token 必须恢复。旧入口传 nil，保持原操作顺序、profile callback 时点、参数与返回值。不得将 callback 返回其他 Goal 或伪造新版本作为成功。'),
('B03','原 boundaryHook 必须保留','链式保留原 PREPARED transport/hash/UA/session/path 核验及 atomic original，新增 dispatch/native/effect stage 记录使用并发安全结构，终止 child 后再取快照。不得覆盖原 hook 或用测试制造的事件替代原 producer。'),
('B04','逐案真实 typed fault 与 stage','errors.As(*Fault) 后严格比 Status/Code/Message；要求原 Task/Run/epoch/profile/dispatch 与实际 MODEL frame key。missing-plan 为 launch 前；其他 preflight 为启动后 route/budget，均 HTTP0/effect0。预算必须先证明 context 未过期并实际得到 budget exhausted。'),
('B05','账本字段与原 UNKNOWN 原因','按原 MODEL key/provider_event/reservation_id 关联真实 ledger；ACTUAL 是 cost_basis，不是 operation。不得以 operation=ACTUAL 的恒空查询代替检查。quarantine 保留原 RESERVE 且无 cost_basis ACTUAL，无 COMMIT/RECONCILE/RELEASE；actual_cost 未知不得填0。原 effect PREPARED→STARTED→UNKNOWN 与 original receipt.reason 精确核对，不能用 runtime_dispatches 的 protocol not reconciled reason 替代。preflight 不把其它资格预算行混为 MODEL 行。'),
('B06','bootstrap 非流边界','从原请求 manifest 与真实 bridge journal 确认 qualification_bootstrap 与 QueueRequired=false；四个 quarantine 原因仅适用 broker 非流支路。原 MODEL frame 未获 ordinary success ACK 不代表普通 Session auxiliary credit 或公共 MESSAGE 隔离。G2不关闭 LIVE、同Run TOOL history、普通流可见性。'),
('B07','有界 component controls','rollback-only 原 Tx 调用 dispatchGate/providerRoute/prepareEffectTx，明确 synthetic BridgeFrame；close Tx、确认无提交 rows 后才 native。四个 benign neighbor 与原 payload 分别定位 Feed/Finish、complete SSE、policy 层；不称 SDK成功或新资格。cause helper 须拒 nil/wrong status/code/message/key/reason。'),
('B08','执行仍待登记','Root 在任何 edits/execution 前登记 exact2 与有限 selectors；全部当前 future NOT_RUN。新编译闭包/现 provider bundle 来源及工具需完整实际核对，G1 未满足资源条件时只阻塞该 lane。失败保留原出口/DB并停止相关 lane，不自动重试/扩项，不运行 held2 或 broad64+12。')]
put('mandatory_conditions.json',[{'id':i,'title':t,'requirement':r} for i,t,r in conditions])

cases=json.loads((INP/'cause_matrix.json').read_text(encoding='utf-8'))['cases']
rows=[]
for c in cases:
    pre='Preflight' in c['selector']; mode=c['mode']
    if pre:
        file=INP/'snapshot/old-author-G2/native'/('TestProviderBindingPreflightRefusals_'+mode)/'preflight.json'
        if mode=='missing-qualification-plan': producers=[src('runtime_qualification.go',124,127),src('runtime_coordinator_windows.go',486,526)]
        elif mode=='insufficient-budget': producers=[src('runtime_coordinator_windows_test.go',146,171),src('context.go',192,193),src('durability.go',95,112),src('budget.go',366,376)]
        else: producers=[src('runtime_broker_windows.go',43,117),src('runtime_broker_windows.go',120,199)]
        stage={'native_started':0 if mode=='missing-qualification-plan' else 1,'http':0,'effect_prepared':0,'scoped_effect_rows':0}
    else:
        file=INP/'snapshot/old-author-G2/native'/('TestProviderBindingQuarantineBeforeSDK_'+mode)/'quarantine.json'
        producers=[src('runtime_model_windows.go',48,63),src('runtime_model_windows.go',160,189),src('durability.go',226,253)]
        if mode in ('selected-alias','escaped-tool'): producers.append(src('runtime_model_stream.go',842,912))
        if mode=='unsupported-detail': producers.append(src('runtime_model_verification.go',592,628))
        stage={'native_started':1,'http':1,'effect_prepared':1,'original_effect_chain':['PREPARED','STARTED','UNKNOWN'],'ordinary_success_ACK':0,'model_observation_rows':0}
    rows.append({'selector':c['selector'],'static_cause_verdict':'MATCHES_FROZEN_PRODUCER_WITH_B01_B08_CONDITIONS','future_execution':'NOT_RUN','expected_fault':c['expected_fault'],'unknown_reason':c.get('exact_unknown_receipt_reason'),'old_raw':ref(file),'old_evidence_limit':'STALE_INPUT 实际旧原因不是 budget exhausted' if mode=='insufficient-budget' else ('旧 raw 无 typed fault 三字段/stage/reservation 完整断言' if pre else '旧 raw 仅 UNKNOWN/HTTP计数，无原 UNKNOWN reason 与 reservation 完整证明'),'producer_refs':producers,'future_expected_not_observed':stage,'component_neighbor':c.get('positive_neighbor'),'root_registration_required':True})
put('whole11_review_matrix.json',rows)
put('future_selectors.json',{'status':'PROPOSED_NOT_AUTHORIZED_NOT_RUN','native_leaf_count':11,'native_selectors':[c['selector'] for c in cases],'helper_controls':{'typed_fault':'nil/wrong Status/Code/Message','effect_identity':'wrong original key/UNKNOWN reason','rollback_components':'original route/context validity; legal small budget reserve followed by rollback/no committed facts','quarantine_neighbors':'4 original and 4 benign payloads, prescribed evaluator layers'},'new_helper_test_names':'implementation author must freeze exact names/count and Root register before execution','optional_compatibility_selector':'^TestRuntimeCoordinatorNativeQualification$ only if Root explicitly adds this unchanged nil-callback regression; not included in 11','held_excluded':['TestProviderBindingActualSameRunToolHistory','TestProviderBindingAllOriginalStatesPortable'],'no_broad_inventory_rerun':True,'timeout_plan':'test150s/outer180s proposed; keep production60/90s; finalized argv requires Root registration','expected_total_loopback_HTTP':4,'expected_external_HTTP':0,'expected_paid':0})
put('tool_diagnostics.json',{'status':'READONLY_TOOL_DIAGNOSTICS_NOT_PRODUCT_FAILURES','recording_basis':'actual tool return outer exit; raw tool chunks retained by platform, not reconstructed full stdout','nonzero':[{'tool_chunk':'ed311b','actual_outer_exit':1,'cause':'last rg query had no matches for providerSSEPolicy/reasoning_details/reasoning alternative in runtime_model.go; preceding Git grep had located capBody','correction_chunk':'948f99','correction_outer_exit':0,'correct_location':'runtime_model_verification.go:592–628','product_test_executed':False}],'observed_zero_chunks':['f2411b','5a10fc','544097','166502','be9525','172667','948f99','52301f','08966c','96d3cf','eb06ef'],'unknown_outer_fields_not_invented':True,'counter_owner':'Root; this review does not mutate counters'})
put('review.json',{'status':'SOURCE_SCOPE_READY_WITH_MANDATORY_CONDITIONS','scope_only':True,'source_acceptance':'NO_SOURCE_READY','provider_or_formal_acceptance':False,'reviewer':'codex:/root/sources_parent_impl','proposal_author':'codex:/root/command_queue_impl','candidate':'6fb5263681c17f0e50920c354dc07ed440a23714','created_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'proposal':ref(INP/'scope_proposal.json'),'matrix':ref(INP/'cause_matrix.json'),'manifest':ref(INP/'manifest.json'),'basis':'whole11 historical public raw and 24 exact candidate Git sources; static-only independent scope review','conclusion':'exact2测试范围足够补足当前G2因果断言；必须采用B01–B08后由Root登记。旧budget PASS未触达预算耗尽；旧quarantine raw未证明精确原因。没有本轮测试或产品接受。','exact_paths':['internal/domain/runtime_provider_binding_windows_test.go','internal/domain/runtime_coordinator_windows_test.go'],'mandatory_conditions':ref(OUT/'mandatory_conditions.json'),'whole11':ref(OUT/'whole11_review_matrix.json'),'future_selectors':ref(OUT/'future_selectors.json'),'input_audit':ref(OUT/'audit.json'),'before':ref(OUT/'inputs.before.json'),'after':ref(OUT/'inputs.after.json'),'tool_diagnostics':ref(OUT/'tool_diagnostics.json'),'historical_events':ref(OUT/'historical_G2_events.json'),'remaining_gates':['Root exact2 registration and finite runner approval','G1 resource/source/bundle closure prerequisites','actual new compile/native11/components/closedDB evidence','independent nonauthor implementation review; ordinary streaming/history/LIVE excluded']})
put('handoff.json',{'status':'INDEPENDENT_SCOPE_REVIEW_ONLY','review':ref(OUT/'review.json'),'matrix':ref(OUT/'whole11_review_matrix.json'),'conditions':ref(OUT/'mandatory_conditions.json'),'input_count':53,'git_candidate_sources':24,'drift_count':0,'executed_test_count':0,'readonly_tool_nonzero_count':1,'no_source_or_acceptance_writes':True})
files=[{'path':p.relative_to(OUT).as_posix(),'sha256':digest(p),'bytes':p.stat().st_size} for p in sorted(OUT.rglob('*')) if p.is_file()]
put('manifest.json',{'algorithm':'sha256','self_excluded':True,'files_count':len(files),'files':files})
for name in ['review.json','handoff.json','whole11_review_matrix.json','mandatory_conditions.json','tool_diagnostics.json','manifest.json']:
    print(json.dumps(ref(OUT/name),ensure_ascii=False))
