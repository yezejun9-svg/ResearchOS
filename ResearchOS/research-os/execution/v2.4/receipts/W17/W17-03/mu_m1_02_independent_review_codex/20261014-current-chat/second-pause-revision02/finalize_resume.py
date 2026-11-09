from review_tools import E,W,A,S,HEAD,TREE,BASE,read,write,pin,guards
import datetime,json,pathlib

ver=read(E/'resume-verification.json')
source=guards()
assert source==ver['source']
assert len(ver['attempts'])==4
assert all(x['exit']==0 for x in ver['attempts'])
top=[];all_results=[]
for attempt in ver['attempts']:
    command=read(pathlib.Path(attempt['command']['path']))
    assert all(x['action']=='pass' for x in command['test_results'])
    top.extend(attempt['top_level_results']);all_results.extend(command['test_results'])
assert len(top)==25
assert len([x for x in all_results if x['test'].startswith('TestReviewPauseEffectPurpose/')])==16
assert len([x for x in all_results if x['test'].startswith('TestReviewLocalLaunchMalformedHistoricalHold/')])==14
write(E/'final-source-guard.json',source)
write(E/'diagnostic-history-resume.json',dict(classification='READ_ONLY_REVIEWER_DIAGNOSTICS_NOT_PRODUCT_OR_GO_TEST_FAILURES',entries=[dict(operation='Read optional parent AGENTS.md',result='File absent; repository AGENTS.md read successfully in same call'),dict(operation='rg wildcard passed as Windows positional path',occurrences=2,result='Invalid path; corrected to directory plus -g, no source/evidence modification')]))
report=dict(schema='researchos.core-r2-independent-review.v2',verdict='LIMITED_SOURCE_ACCEPTANCE',finding_disposition={'M1-02-R2':'RESOLVED_AT_PINNED_CANDIDATE'},reviewer_agent='codex:/root/core_r2_review_resume',reviewer_role='INDEPENDENT_REVIEWER_NOT_BUILDER',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),source=dict(head=HEAD,tree=TREE,base=BASE,exact_files=2,clean=True,scope=pin(S)),author=dict(manifest=pin(A/'source-manifest.json'),ledger=pin(A/'attempt-ledger.json'),attempts=7,passed=6,failed=1,failure_classification='COMPILE_FAILURE_RETAINED'),independent_verification=dict(reused_prior_independent_attempts=['01-domain-regressions','02-native-regressions'],fresh_attempts=['03-independent-native-probes','04-independent-domain-probes'],total_attempts=4,failed_attempts=0,skipped_tests=0,top_level_pass=len(top),domain_original_top_level=13,native_regression_top_level=8,native_additional_top_level=2,independent_domain_top_level=2,purpose_subcases=16,malformed_hold_subcases=14,verified_pins=89,budget_trajectories=4,budget_rows_per_trajectory=6,revocation_paths=4,verification_ref=pin(E/'resume-verification.json')),retained_history=dict(author_revision01=dict(attempts=23,passed=11,failed=11,skipped=1),review_revision01=dict(attempts=5,failed=2),earlier_author=dict(attempts=18,failed=7),earlier_review=dict(attempts=5,failed=2),note='Separate historical cohorts; do not sum overlapping lower bounds. All original files retained.'),findings=[],scope_limits=['Acceptance only covers exact2 R2 change above exact9 base at pinned HEAD/tree; no Main merge or release approval.','Real Windows Host, canonical DB, AppContainer, broker and verifier were exercised with synthetic loopback model responses; no live external model qualification.','CANCEL uses native HTTP; Owner uses Service.RevokePrincipal; Goal/lease and malformed budget are synthetic isolated canonical DB fault injections.','Purpose and malformed historical-hold cases are domain fixtures, not native user trajectories.','Runtime inputs reused at frozen hashes; broader Bridge compatibility remains separately scoped.','No actual Desktop interaction, product data/private keys, shared-state updates or formal case acceptance.'],formal_increment=0,formal_accepted_cases='0/42',all_parent_tasks_open=22)
write(E/'report.json',report)
(E/'report.md').write_text('''# CoreR2 exact2 独立审查

结论：**LIMITED_SOURCE_ACCEPTANCE**。冻结候选内的 M1-02-R2 已解决，本轮未发现需阻止此范围源码接受的问题。接受仅覆盖 exact9 基础上的 exact2 心跳修订；没有合入 Main，没有批准发布或产品正式验收。正式仍为 **0/42，22 个父任务全部 open**。

`internal/domain/runtime_coordinator_windows.go:535` 在已有 dispatchGate 事务内读取当前 run/epoch 的 pause intent，再交给原 pause purpose 门禁。`RunAdmitted:695` 的周期心跳传入 heartbeat-current，15 秒周期未变。当前暂停仍需匹配 task/run/runtime/epoch/dispatch/manifest/process、状态见证、有效 Owner、Goal、session/queue/control，并经过原 lease 与 admission 校验。普通调用没有 purpose，BLOCKED 的严格拒绝仍保留；没有借历史 activation 放宽执行或启动。

## 独立验证

本审查恢复时，前位独立 reviewer 的 01 与 02 均已完成，未发现遗留 go/host/domain 测试进程。已核对原命令、日志哈希及前后 source guards，复用其独立结果；它们不是作者测试。新增 03 与 04 使用独立编号及 attempt-ledger-resume.json，原 attempt-ledger.json 未改写。

- 01：13 个原 domain 顶层用例 PASS，覆盖预算接管、终态释放、四 epoch、重放及既有暂停门禁。
- 02：8 个 Host 原生顶层用例 PASS，含四个撤销子例。第二轮模型与工具分别在途等待 17000ms，heartbeat_at 实际推进；同 Run/attempt 恢复至 epoch3，两个 activation、四条命令及四条消费回执各一次。模型路径实际 Host 工具 1 次；工具路径 2 次，并断言文件确已写入第二轮内容。
- 03：上一轮失败的 17 秒 overlay 逐字节未变，SHA-256 `f2dc0aa0a0b72a1aaac2371a225107656f66bfca7a0afd557f6b0f24dc19a800`。本次实际执行 PASS，PAUSED_CONFIRMED 后恢复到 epoch3。相同命令内的完整 successor rollback 用例亦 PASS：真实首次暂停后，仅向隔离 DB 注入 receipt 有效而 reservation_id 错误的 RELEASE，Scan 明确拒绝，Run/Task/账本、pause intents/receipts、carry、activation、dispatch 前后完全一致。
- 04：16 个独立 purpose 子例和 14 个错误历史 hold 子例全部 PASS。复用上一轮修正后的独立夹具字节，未改候选源码。

四条原生两轮轨迹的最终预算账本另经独立 Python 解码：每轨迹六行，每 epoch 一条 RESERVE 与一条 RELEASE，reservation_id、project/run/request/event/policy、零金额币种和 receipt hash 均精确匹配，时间可解析。原生恢复的四条命令与四条消费回执也再次核对。见 resume-verification.json，包含 89 个输入引用的实际哈希复核。

四类撤销均先跨过第二次暂停的心跳，再撤销当前权限，Bridge 被取消，epoch3 activation 为 0，已消费队列保持 2，Host 工具调用保持 1。CANCEL 是真实 HTTP；Owner 调用真实 Service.RevokePrincipal；Goal 与 lease 使用隔离 canonical DB 合成故障。后两类不能称作完整用户撤销路径。

## 历史与边界

本 revision02 独立测试共 4 次命令、25 个顶层 PASS、0 个非零退出、0 skip。作者 revision02 的 7 次尝试保持 6 PASS/1 编译失败；旧作者 23 次 11 PASS/11 FAIL/1 SKIP、旧 reviewer 5 次/2 FAIL，以及更早作者 18/7、reviewer 5/2 均未改写，不能重置或重复累加。只读诊断中的路径错误单独记录，不混作产品失败。

这里运行了真实 Windows Host、canonical DB、AppContainer、broker 和 verifier，模型为本机 synthetic 回应。未调用外部模型，未操作实际 Desktop、产品数据或私钥，未修改 Main/共享状态。purpose/历史 hold 为 domain fixture；预算及 Goal/lease 为原生前置流程加隔离 DB 故障注入。宽泛 Bridge 兼容、真实模型和正式用例仍需各自证据。本结论不扩大为全部 runtime 或产品通过。

候选 HEAD `8f50cb57ff821554aef17e9a9bd5208935489d50`，tree `361ead86ee812d5e040fe1d2cde2a92297eb639f`，base `36b2634bfebe6201a14b7661f2dce32b7f1a5098`。exact2 为 coordinator 与 Host test。scope SHA-256 `b070cfa31d8336ef9c029d4cb410b214ccf0f30750b1dcbdbbce6a8d6d8c7d64`。最终 guard clean；runtime 资产及 overlay 哈希与冻结输入一致。
''',encoding='utf-8')
members=[]
for p in sorted(E.rglob('*')):
    if p.is_file() and p.name!='evidence-manifest.json' and '__pycache__' not in p.parts:
        item=pin(p);item['path']=p.relative_to(E).as_posix();members.append(item)
write(E/'evidence-manifest.json',dict(schema='researchos.core-r2-independent-evidence.v2',verdict='LIMITED_SOURCE_ACCEPTANCE',source=source,files=members,formal_increment=0))
print(json.dumps(dict(report=pin(E/'report.md'),report_json=pin(E/'report.json'),manifest=pin(E/'evidence-manifest.json'),members=len(members)),ensure_ascii=True))
