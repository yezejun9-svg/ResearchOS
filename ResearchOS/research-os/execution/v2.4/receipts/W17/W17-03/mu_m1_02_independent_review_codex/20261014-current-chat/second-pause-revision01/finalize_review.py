from review_tools import E,W,A,S,HEAD,TREE,BASE,read,write,pin,guards
import datetime,decimal,hashlib,json,pathlib

scope=read(S);m=read(A/'source-manifest.json')
assert sorted(scope['allowed_source_files'])==sorted(x['path'] for x in m['source_files'])
write(E/'final-source-guard.json',guards())
assets=pathlib.Path('C:/Users/yqyyds/.codex/researchos-build-worktrees/mu-m1-wire-20261014/.local/m1-01')
runtime=[(assets/'node.exe','5f364598aa3017130b22908ff7c3db0fd05bd42d39fd65b79fd6bd3f73c73da6'),(assets/'mu-worker.mjs','34cb78ca809dc8269eb6c3c7f4ebbdb983a672ed10ceacfc934da9b2b3fbd0cd'),(pathlib.Path('D:/作品集/ResearchOS/research-os/.local/mu-m1-core-20261014/runtime-verifier.exe'),'e7bb47ab866cd887499d3cea995a1465643eee9ab4ecadce2e430bccd41500a2')]
pins=[]
for p,h in runtime:
    v=pin(p);assert v['sha256']==h;pins.append(v)
write(E/'runtime-inputs.json',dict(classification='PUBLIC_FROZEN_RUNTIME_INPUTS_READ_ONLY',inputs=pins))

native=read(E/'native/TestProductMuSecondPauseResumeNative/canonical-evidence.json')
run=native['final_run'];prefix='runtime-local-launch/'+run['id']+'/'
rows=[json.loads(x['body']) for x in native['budget_ledger']]
rows=[x for x in rows if x['provider_request_id'].startswith(prefix)]
assert len(rows)==6
checks=[]
for epoch in range(1,4):
    request=prefix+str(epoch);hold,=[x for x in rows if x['provider_request_id']==request and x['operation']=='RESERVE'];release,=[x for x in rows if x['provider_request_id']==request and x['operation']=='RELEASE']
    assert hold['run_id']==release['run_id']==run['id'] and hold['project_id']==release['project_id']==run['project_id']
    assert hold['provider_event_id']==request and release['provider_event_id']==request+'/released'
    assert hold['reservation_id'] is None and release['reservation_id']==hold['id']
    assert hold['policy_id']==release['policy_id'] and hold['money']==release['money']
    assert decimal.Decimal(hold['money']['amount'])==0 and hold['cost_basis']=='UPPER_BOUND' and release['cost_basis']=='ACTUAL'
    for x in [hold,release]:
        digest='sha256:'+hashlib.sha256(json.dumps({k:v for k,v in x.items() if k!='receipt_hash'},sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
        assert x['receipt_hash']==digest
        assert datetime.datetime.fromisoformat(x['occurred_at'].replace('Z','+00:00')).tzinfo is not None
    checks.append(dict(epoch=epoch,hold_id=hold['id'],release_id=release['id'],hold_receipt=hold['receipt_hash'],release_receipt=release['receipt_hash'],reservation_exact=True,zero_same_currency=True,timestamps_parse=True))
write(E/'native-budget-verification.json',dict(source=pin(E/'native/TestProductMuSecondPauseResumeNative/canonical-evidence.json'),run=run['id'],epoch=run['lease_epoch'],checks=checks))
rollback=read(E/'native/TestReviewMuBudgetFailureRollsBackNativeSuccessor/canonical-evidence.json')
assert rollback['same_state'] is True and rollback['before']==rollback['after']
bad=read(E/'native/TestReviewMuSecondPauseAcrossHeartbeatNative/after-second-pause.json')
assert bad['http_status']==200 and bad['pause_state']=='RECONCILING'
bridge=read(E/'native/TestReviewMuSecondPauseAcrossHeartbeatNative/bridge.json')
assert bridge['cancelled'] is True and bridge['state']=='FAILED'
ledger=read(E/'attempt-ledger.json')
assert len(ledger['attempts'])==5 and ledger['failed_attempt_count']==2
finding={'id':'M1-02-R2','priority':'P2','title':'暂停等待跨周期心跳时被通用 BLOCKED 门禁取消','file':'internal/domain/runtime_coordinator_windows.go','line_start':680,'line_end':687,'related_lines':[540,817],'trigger':'第二轮 PAUSE 返回200后让原已准入模型响应继续在途17秒，跨过真实15秒周期心跳；未撤销Owner/Goal/lease、未发生外部模型错误。','observed':{'pause_state':bad['pause_state'],'dispatch':'UNKNOWN/protocol not reconciled','bridge_state':bridge['state'],'bridge_cancelled':bridge['cancelled'],'bridge_reason':bridge['reason'],'model_calls':bad['synthetic_model_calls'],'host_tool_calls':bad['actual_host_tool_calls'],'native_started':bridge['started'],'native_ended':bridge['ended']},'cause':'周期心跳仍调用无purpose heartbeat；它经过新通用 gate，在 Task BLOCKED且currentPause=nil 时拒绝，心跳循环随后cancel并取消Bridge。只有checkpoint同步heartbeat有新purpose。','remediation':'周期暂停维护心跳必须通过当前真实pause_id/epoch/dispatch/process/session/generation的专用目的和原完整门禁，允许PAUSE_REQUESTED/CHECKPOINT_SEALED的必要维护；不能放宽通用执行gate，取消/撤销/错误phase仍拒绝。','evidence':['03-independent-native-probes/command.json','03-independent-native-probes/stdout.jsonl','native/TestReviewMuSecondPauseAcrossHeartbeatNative/after-second-pause.json','native/TestReviewMuSecondPauseAcrossHeartbeatNative/bridge.json'],'proof_boundary':'状态为真实AppContainer/API/DB实测，具体门禁因果为冻结源码追踪；模型仅synthetic。'}
report={'schema':'researchos.mu-second-pause-independent-review.v1','verdict':'NEEDS_CHANGES','source':{'head':HEAD,'tree':TREE,'base':BASE,'exact_files':9,'clean':True,'scope':pin(S)},'author':{'source_manifest':pin(A/'source-manifest.json'),'ledger':pin(A/'attempt-ledger.json'),'attempt_count':23,'pass_count':11,'failed_count':11,'skip_count':1,'cp483_native_failure_lower_bound':3,'lower_bound_already_included_attempts':['02','03','04']},'independent_attempt_ledger':ledger,'findings':[finding],'verification':{'original_domain_top_level_pass':13,'original_native_top_level_pass':5,'independent_native_rollback_pass':True,'independent_effect_purpose_subcases_pass':16,'independent_malformed_hold_subcases_pass':14,'native_budget_rows_verified':6,'native_epochs':[1,2,3],'native_model_calls':native['synthetic_model_calls'],'native_tool_calls':native['actual_host_tool_calls'],'same_Run_attempt':True,'commands_consumed_once':4,'production_source_modified':False},'failure_classification':{'03-independent-native-probes':'product R2, one native fail; budget native-setup rollback test passes in same invocation','04-independent-domain-probes':'review fixture construction missing required checkpoint columns; source code not implicated; old overlay/output retained; corrected v2 passes in05'},'retained_prior_history':{'original_author':{'attempts':18,'failures':7},'original_independent_review':{'attempts':5,'failures':2}},'coverage_limits':['Author forged-release fixture only covered Run epoch and ledger; this review separately adds native setup + synthetic malformed ledger full successor transaction rollback.','Tool publication original native test covers PAUSE in epoch1 then resume, not two complete tool-in-flight pause cycles; second-cycle model path is proven. Next candidate should add the scope-required two-cycle tool variant.','Independent purpose probes are domain fixtures, not native negative trajectories.','Budget time verification proves nonempty/parseable real captured times and unchanged replay rows; no claim that arbitrary malformed nonempty historical timestamps are independently rejected.','No real external model, actual Desktop/product DB/private credentials, Main merge or formal acceptance.','Legacy Bridge compatibility remains separate frozen work; no all-runtime-regressions-pass claim.'],'formal_increment':0,'formal_accepted_cases':'0/42','all_parent_tasks_open':22}
write(E/'report.json',report)
(E/'report.md').write_text('''# Core 第二次暂停 exact9 独立审查

结论：**NEEDS_CHANGES**。exact9 的普通两轮暂停恢复已跑通，但新增原生边界复现表明：暂停等待跨过周期心跳会被取消。正式接受仍为0/42，22个父任务保持open；本审查没有修改源码、Main或共享状态。

## M1-02-R2 / P2：周期心跳取消正常等待中的暂停

位置：`internal/domain/runtime_coordinator_windows.go:680-687`；相关严格门禁在540行，heartbeat入口在817行。

周期循环的 `c.heartbeat(..., locator, "")` 没有传入新的暂停维护目的。Task在PAUSE请求后成为BLOCKED，通用gate拒绝，循环随即cancel并取消Bridge。只有pauseCheckpoint里的同步heartbeat获得了专用purpose；在途模型或工具稍慢时尚未到达那个调用点。

独立复现保持真实同一Run的epoch2模型响应在途，发送普通HTTP第二次PAUSE并收到200，再等待17秒后释放响应。没有撤销Owner/Goal/lease，也没有真实外部模型调用。结果：pause intent为RECONCILING，epoch2 dispatch为UNKNOWN / protocol not reconciled，Bridge为FAILED、cancelled=true、reason=`coordinator control channel closed`。模型共4次、Host工具1次。Bridge实际started/ended与完整DB行在原始证据中保留。

测试只通过Go overlay更换审查目录内的测试副本，未改生产源码或心跳间隔。`03-independent-native-probes/command.json`记录完整argv/cwd/环境/exit；该目录保存原始stdout。具体DB/Bridge证据在 `native/TestReviewMuSecondPauseAcrossHeartbeatNative/`。运行状态为原生实测，门禁原因由冻结源码追踪。

最小修订仍在已授权coordinator/pause与测试文件内：让周期心跳仅在精确当前暂停身份下走现有的暂停维护purpose，保持完整Owner/Goal/lease/manifest/session/queue校验。不能给普通执行、启动、任意BLOCKED或历史activation开通用例外。补原生“等待跨15秒心跳仍能确认暂停并恢复”的模型/工具用例，并证明取消与撤销仍能终止。

## 本轮通过的独立验证

- 13个原domain顶层用例通过，含W12预算接管、终态释放、四epoch及同epoch重放、10个错误RELEASE绑定反例和既有pause边界；0 skip。
- 5个原Host原生用例通过：首次恢复、取消、未启动lease恢复、第二次暂停恢复、PAUSE后Host工具实际发布复核。两轮模型路径保持同一Run/attempt、epoch1→2→3、四条命令各一次消费、模型6次和工具1次。
- 对两轮原生最终账本的6行再次独立解码和校验：每epoch一个RESERVE及一个绑定原reservation_id的RELEASE，project/run/request/event/policy/零金额币种和receipt hash均匹配，时间可解析。见 `native-budget-verification.json`。
- 独立native setup + canonical故障注入：在真实首次暂停后，仅向隔离测试DB插入receipt有效但reservation_id错误的RELEASE，使用真实c.Scan恢复入口。错误明确返回，Run/Task/BudgetLedgerEntry、pause intents/receipts、carry、activation、dispatch在事务前后完全一致。补齐作者局部预算夹具没有证明的完整successor rollback。见 `native/TestReviewMuBudgetFailureRollsBackNativeSuccessor/canonical-evidence.json`；这是原生前置流程加合成故障注入，不声称用户数据发生过该故障。
- 独立16个purpose夹具覆盖原PREPARED开始、STARTED/CONFIRMED观察、continue/finish、UNKNOWN/新key/错hash/旧epoch/变化sequence/封存后effect拒绝；14个历史hold反例覆盖规范epoch、空time/id、receipt及账目绑定。这些是domain fixture证据，不升级为原生负例。

## 失败历史和证据边界

本轮独立5次命令、2次非零：03含实际R2失败和rollback通过；04是审查夹具把CHECKPOINT_SEALED构造为缺少必填列，被存储CHECK正确拒绝，原overlay与原始失败保留；修正审查夹具v2后05的16项purpose全部通过。不得把04算成产品缺陷，也不得删除它。

作者23次为11PASS/11FAIL/1SKIP，CP483原生失败下限3已映射其中02-04，不能重复累加。早期作者18/7和独立审查5/2保持原值。源manifest、全部作者日志/exit/native引用共105次哈希核验一致。

工具发布原用例仅覆盖epoch1暂停后的真实工具发布；第二轮model-in-flight已证明，但范围要求的“两轮tool-in-flight”尚未单独完成。下一候选须补这一条，不能把first-pause工具用例写成第二轮工具证据。原生预算时间校验不等于证明任意非空非法历史时间都被拒绝。普通supports_resume=false和历史activation门禁未放宽；更广的Bridge兼容、真实模型、实际Desktop与正式验收仍不在本次通过范围。

源码HEAD `36b2634bfebe6201a14b7661f2dce32b7f1a5098`，tree `bea72c5cdbb341e4d67bd91331803ec6e8013e3b`，base `ff5ac2047566a52388188b84f267217d8582c571`。scope SHA-256 `1f418aac77ee33a0f75d91defd9466dcd961c9e0ca869319d653f7f8d6adb957`。运行前后固定guard均clean；模块、编译缓存和公开runtime资产复用，没有新worktree或全量checkout。
''',encoding='utf-8')
members=[]
for p in sorted(E.rglob('*')):
    if p.is_file() and p.name!='evidence-manifest.json' and '__pycache__' not in p.parts:
        x=pin(p);x['path']=p.relative_to(E).as_posix();members.append(x)
write(E/'evidence-manifest.json',dict(schema='researchos.mu-second-pause-independent-evidence.v1',verdict='NEEDS_CHANGES',files=members,formal_increment=0))
print(json.dumps(dict(report=pin(E/'report.md'),manifest=pin(E/'evidence-manifest.json'),members=len(members)),ensure_ascii=True))
