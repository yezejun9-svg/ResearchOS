# Core 第二次暂停 exact9 独立审查

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
