import review_runner as r
import json, pathlib, hashlib, re
def read(p): return json.loads(pathlib.Path(p).read_text(encoding='utf-8-sig'))
def counts(p):
    rows=[json.loads(x) for x in pathlib.Path(p).read_text(encoding='utf-8-sig').splitlines() if x.startswith('{')]
    result={a:sum(x.get('Action')==a and bool(x.get('Test')) for x in rows) for a in ['run','pass','fail','skip']}
    result.update(top_level_pass=sum(x.get('Action')=='pass' and bool(x.get('Test')) and '/' not in x['Test'] for x in rows),subtest_pass=sum(x.get('Action')=='pass' and '/' in x.get('Test','') for x in rows),package_pass=sum(x.get('Action')=='pass' and not x.get('Test') for x in rows))
    result['tests']=[{'test':x['Test'],'action':x['Action']} for x in rows if x.get('Test') and x['Action'] in ('pass','fail','skip')]
    return result
results={k:counts(p) for k,p in [('source_focused',r.SOURCE/'final-targeted.raw.jsonl'),('independent_focused',r.E/'candidate-focused.raw'),('base_regressions',r.E/'base-regressions.raw'),('candidate_regressions',r.E/'candidate-regressions.raw')]}
r.save('test-counts.json',results)
before=read(r.E/'initial-guards.json');after=read(r.E/'final-guards.json')
guard={'main_head_unchanged':before['main']['head']==after['main']['head'],'main_status_unchanged':before['main']['status']==after['main']['status'],'main_index_empty':not after['main']['index'],'main_dirty_file_hash_changes':{p:{'before':h,'after':after['main']['dirty_hashes'].get(p)} for p,h in before['main']['dirty_hashes'].items() if h!=after['main']['dirty_hashes'].get(p)},'candidate_unchanged':before['candidate']==after['candidate'],'base_unchanged':before['base']==after['base'],'bundle_unchanged':before['bundle']==after['bundle']}
manifest=read(r.SOURCE/'source-manifest.json')
guard['candidate_file_hashes_unchanged']=all(r.sha(r.CAND/x['path'])==x['sha256'] for x in manifest['changed_files'])
guard['source_evidence_hashes_unchanged']=all(r.sha(r.SOURCE/x['path'])==x['sha256'] for x in manifest['receipt_files'])
r.save('guard-comparison.json',guard)
findings=[
 {'id':'F01','priority':'P1','kind':'production_regression','path':'internal/runtimepolicy/qualification_projection.go','line_start':158,'line_end':163,'title':'Preserve native-offline qualification admission','finding':'Prepare unconditionally requests model_config before backend scoping; any runtime_qualification with a legitimate native-offline profile now fails preparation. This is an existing supported qualification path, not malformed Mu authority.','proof':'Same exact Go argv and environment: TestRuntimeCoordinatorNativeQualification passes base4f and fails candidate525 with GATE_FAILED: qualification projection: projection source config missing at runtime_coordinator_windows_test.go:115.','fix':'Keep native-offline qualification without projection compatible; apply strict complete eligibility and contradictory tuple rejection to Mu projection only; add focused native-offline regression and ordinary native-offline no-marker check.'},
 {'id':'F02','priority':'P2','kind':'invalid_negative_control','path':'adapters/runtime/qualification_projection_windows_test.go','line_start':82,'line_end':90,'title':'Use a valid decoded positive control for adapter tampering','finding':'json.Unmarshal into map[string]any converts q.max_calls, source max_calls and epoch into float64. Effective rejects the unmodified clone in eligible/exactNumber before reaching most marker binding comparisons. Thus nil-error assertions may pass even if project/task/ref/hash comparisons are removed. The original direct-map positive test does not validate the cloned input used by the matrix.','proof':'Source inspection: json.Unmarshal at :85; exactNumber accepts only json.Number/int/int64; eligible checks qualification max_calls before binding-field comparison. Independent native adapter test passes, but does not repair this proof gap. External E probe compilation was rejected by Go internal-package scope; this is preserved as a failed diagnostic and is not dynamic confirmation.','fix':'Decode every clone with UseNumber and first assert the unchanged clone passes validateBridgeProgram. Then mutate exactly one field per case and require the intended rejection, including task_type/profile_ref/null/unknown fields.'},
 {'id':'F03','priority':'P2','kind':'acceptance_evidence_gap','path':'internal/domain/runtime_qualification_projection_windows_test.go','line_start':12,'line_end':44,'title':'Complete required consumer and legacy coverage','finding':'A04 requires each marker/authority cut at all production consumers. Current stage/pretransport loop covers 15 marker fields; brokerEffect tests only old tools and second call; drain has no marker matrix; adapter matrix has F02. No marker-null test exists. Normal/legacy proof uses 8/1 staging plus request validator, not original 8/4 at host and verifier; the ordinary session integration fails before the normal turn on both revisions. A09 ordinary snapshot acceptance and A10 altered projection rejection remain unproven.','proof':'Review of all seven added/changed test files and raw 72-node run; matching baseline failure provides attribution only and cannot count as a passing normal-turn chain.','fix':'Add bounded positive/negative controls across host pre-prepare, pre-transport, adapter, verifier and drain, including null/partial marker and permission/bootstrap cases; add valid ordinary/legacy 8/4 host/verifier snapshots without broad unrelated package reruns.'}
]
cuts={
 'A01':'PARTIAL: correct pure derivation/source ownership by inspection and test; recursive unchanged-config assertion is weaker than stated claim',
 'A02':'PARTIAL: pure/stage 8/1 pass; ordinary full session has same pre-dispatch failure on exact base and candidate; host/verifier 8/4 positive proof missing',
 'A03':'PARTIAL: legacy absence pure/stage 8/1 pass; complete host/verifier original-config compatibility not dynamically established',
 'A04':'NOT_ACCEPTED: incomplete all-consumer matrix and invalid adapter cloned positive control (F02/F03)',
 'A05':'NOT_ACCEPTED: Mu marker actual-Task/max2 tests pass, but native-offline qualification regresses (F01)',
 'A06':'PARTIAL: old worker config rejected by StartBridge before native launch; bundle and no-marker checks pass; marker field matrix invalid',
 'A07':'PASS_BOUNDED_FIXTURE: frozen worker executes one local-fixture MODEL with wire tools0; source8/4 effective1/0 unchanged provider identity',
 'A08':'PASS_BOUNDED_SUBSET: old tools/second MODEL rejected before effect append; tampered marker at direct brokerModel rejects before provider; complete matrix remains missing',
 'A09':'PARTIAL: projected snapshot passes independent verifier; copied marker/old tools/source mismatch/excess count rejected; ordinary snapshot control missing',
 'A10':'PARTIAL: confirmed local completion and UNKNOWN ledger preservation pass; existing closure/effect gaps and old tools rejected; projection-tamper matrix missing',
 'A11':'PASS_BOUNDED: shared domain/adapter/policy canonical golden with json.Number, nested arrays, Unicode and empty tools; owned JSON deep copy by inspection',
 'A12':'PASS_BOUNDED_FIXTURE: hostile tool_calls causes exactly one provider request and zero TOOL effects; no terminal/B assertion'}
report={'schema':'researchos.qualification-projection-A-independent-review-result.v1','reviewer':'codex:/root/qualification_projection_review','model':'gpt-6-astra','reasoning_effort':'high','verdict':'NOT_ACCEPTED','candidate_commit':manifest['commit'],'candidate_tree':manifest['tree'],'base_commit':manifest['base'],'findings':findings,'cuts':cuts,'test_summary':{k:{a:b for a,b in v.items() if a!='tests'} for k,v in results.items()},'guards':guard,'source_scope':'15 exact allowlisted changed files: 8 production files, seven production consumers plus shared helper; seven changed test files','historical_capture_gaps':'Source SUPPLEMENT explicitly admits earlier raw outputs and initial overwritten patch missing. This independent rerun is fresh evidence only; missing original records stay missing. 102 is static assertion call sites, never dynamic assertion count.','normal_mu_baseline':'Both exact base and candidate fail TestRuntimeMuSessionToolAndIndependentAcceptance at :146 with MODEL_UNAVAILABLE legacy original frozen profile unavailable. Same argv/env (cwd differs only by exact revision worktree).','failed_probe':'adapter-numeric-positive-control native exit1: external receipt Go source cannot import candidate internal package; no workaround, overlay or source mutation attempted. Numeric-control finding is static reasoning.','actual_provider_calls':0,'actual_product_data_calls':0,'formal_increment':0,'formal_cases':'0/42 this scope; all22 parents remain open','main_package_actual_acceptance':False,'B_terminal_closure':'NOT_CLAIMED','C_old_run':'UNTOUCHED'}
r.save('review.json',report)
md='''# Qualification projection A independent review — NOT_ACCEPTED

Candidate `525a9c923a8761a9491070123de3c94aa5618d71`, tree `ee490d97969fb85e2bc2eeeda067188ebb07045b`, base `4f4023c956f84d65743f39ce77d6c8899a21ada1`.

发现一个新增生产回归、一个无效阴性对照和一组必须补齐的验收证据，不能签发 LIMITED_SOURCE_ACCEPTED。候选源码保持冻结。

## Findings

1. **F01 / P1 — native-offline 资格入口回归。** `internal/runtimepolicy/qualification_projection.go:158-163` 在区分 Mu backend 之前要求 model_config，并对任何 runtime_qualification 返回错误。现有 `TestRuntimeCoordinatorNativeQualification` 在 exact base PASS，在 candidate FAIL：`GATE_FAILED: qualification projection: projection source config missing`。两次使用同一 argv/env，完整 JSON、native exit、cwd 都已保存到 `base-regressions.*` 与 `candidate-regressions.*`。应只对 Mu 投影执行严格资格校验，保留没有 marker 的 native-offline 原流程，并添加对应回归。

2. **F02 / P2 — adapter 篡改矩阵的克隆本身无效。** `adapters/runtime/qualification_projection_windows_test.go:82-90` 使用 json.Unmarshal，将数字转成 float64。`exactNumber` 仅接受 json.Number/int/int64，因此未篡改 clone 在 qualification max_calls 判断就失败；大部分字段检查失效也可能保持测试绿色。需用 UseNumber 克隆，先证明未改 clone 通过，再逐字段篡改。E 内独立 probe 因 Go internal import 范围限制编译失败，已保留原始诊断；未绕过、未增加 Source overlay。此结论依据源码控制流，不冒称该 probe 已动态证实。

3. **F03 / P2 — 全 consumer 和 normal/legacy 验收覆盖不足。** A04 要求的完整字段/authority/null/partial 矩阵未覆盖 brokerEffect、drain 等各 consumer；adapter 另有 F02。normal/legacy 新测试仅覆盖 8/1 staging 与 request validator，未证明原始 8/4 host/verifier；普通 session 集成在 base/candidate 都于 :146 MODEL_UNAVAILABLE 失败。该同基线失败可排除该项新增回归，不能算普通链路通过。A09 ordinary snapshot 和 A10 altered projection 应补充有有效正对照的隔离测试。

## Independently observed evidence

- Author raw 与本次重跑均为 72 test nodes = 19 top-level + 53 subtests，另 3 package pass；零 skip/fail。102 仅是作者静态断言调用点统计，未视为动态断言数。
- frozen SDK worker + loopback fixture：原 profile8/4 保持，effective1/0；实际 wire 无 coding tools，一次 MODEL；host provider identity 仍绑定 original config。
- hostile tool_calls fixture：一次 provider 请求，零 TOOL effects；未认定 B 的终态关闭。
- marker 在真实 Task 类型验证之后、manifest hash/INSERT 之前建立；stage、adapter prelaunch、brokerEffect preprepare、brokerModel pretransport、verifier、drain 都调用同一 helper。全字段/hash/canonical/deepcopy 设计主体连通，不能抵消 F01 与覆盖缺口。
- focused build 原生退出 0；独立 build binary 在删除前记录 SHA/size。
- source manifest/input/receipt hash 全匹配；15 文件 diff 属 allowlist；canonical binary patch 与现有 patch 字节一致，reverse check 通过；22 个 formatter 外部路径 blob 各自等于 HEAD。
- base/candidate tracked clean；Main HEAD/index/20 项既有 dirty 状态保留。并发 Root 允许的共享 checkpoint/ownership/handoff 差异以 guard-comparison.json 为准，非本 reviewer 写入。

## Evidence boundaries

Source 早期 compile、错误、skip、原始被覆盖 patch 等 full raw 缺失仍然缺失，SUPPLEMENT 与 diagnostics 原样保留。本次复跑仅增加新证据，不能补称原始日志已捕获。完整命令 argv、cwd、allowlisted env、native exit 和 raw hash 见 *.command.json / diagnostic-ledger.jsonl；详细 A01-A12 状态见 review.json。

仅 Source/隔离 fixture 审查；无实际 provider/Ollama/产品数据调用，无 Source/Main/package/实际 DB 修复，无安装包修改、旧 Run 修复或 B 闭合声明。formal 增量0/42，22 父任务保持开放。
'''
(r.E/'review.md').write_text(md,encoding='utf-8')
binary=r.TEMP/'control-review.exe'
r.save('independent-build-artifact.json',{'path':str(binary),'sha256':r.sha(binary),'bytes':binary.stat().st_size,'disposition':'temporary verification build; authorized cleanup after hash capture'})
r.save('read-diagnostics.json',{'capture':'Read-only exploration diagnostics were emitted by exec tool; source historic raw gaps remain unchanged. No policy approval denial occurred.','items':[{'command':'Get-Content architecture receipt using candidate-relative path','native_exit':1,'reason':'receipt exists only in Main evidence tree; corrected to authoritative absolute read path'},{'command':'Get-Content continuation-cp501/before.raw; rg internal/domain/*test.go','native_exit':1,'reason':'actual filenames checkpoint.before.raw.json/ownership.before.raw.json/handoff.before.raw.md; PowerShell literal wildcard argument invalid for rg. Bounded path listing identified correct filenames.'}],'probe':'Compiler scope rejection is recorded separately; no alternate import bypass attempted.'})
print(json.dumps({'verdict':report['verdict'],'test_summary':report['test_summary'],'guard_differences':guard['main_dirty_file_hash_changes']},ensure_ascii=False))
