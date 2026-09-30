# R2 same-authority mechanism independent review

结论：`NEEDS_FIX`。源提交 `c645ce3674483ac2f01a42d560a8ae136b9e76f8`，证据提交 `818659ad70bbffa388c13d9b1dff7be963792540`。两个作者机制测试的 PASS 可作为限定证据保留，但以下两个 P1 未关闭，不能据此接纳 actual-control 发布链。作者已确认两项；修复将另出增量报告，本报告不追改为 PASS。

## P1 findings

- `R2-READY-RETRY-PROJECTION`：`release_engine_windows.go:203` 在 `Ready` 前把真实子进程写成 `CANARY`。`Ready` 失败后仍保留该 phase；`release_host/control_windows.go:131` 的 execute 重试允许直接进入 `WriteFixtureReceipt` 和 `FIXTURE_PROJECT`。当前共同 receipt 只要求准确进程仍 Alive，没有 private startup readiness，因此初次 READY 失败但子进程仍存活时可产生成功回执并投影。回滚也在 Ready 前记录 `ROLLED_BACK`。应先持久化准确进程 identity 与未知结果 fence，Ready 成功后才进入已接受 phase；新回执和旧回执重读的共同边界均应验证 actual driver private READY。回归需证明 Ready 失败且 Alive=true 不会 receipt/project，不重发 Start，正常路径仍成立。本次为静态可达性结论，未运行原生故障注入。
- `R2-ACTUAL-PROFILE-GATE`：`apps/control/drain_windows.go:181` 对五种 FIXTURE 私有动作只验证 capability、quiesce 和当前进程 snapshot，随后进入 `Service.HandleReleaseFixture`。`releaseAdmissionInputs:303` 未区分 actual control 和旧计算器 profile，也未校验 actual profile/generation helper。同一个通用 domain 入口被快照机制测试用旧计算器 proof 成功调用。通常 stable EXE hash 不同可间接拒绝现成计算器 admission，但不等于实际模式具有显式关闭门；missing candidate 返回 NOT_FOUND 也没有覆盖该门。实际 control 私有 effect 入口须显式 unavailable，直至可信 exact-control/profile/generation helper 集成；不妨碍隔离 domain 计算器快照机制测试。

## Verified bounded evidence

独立读取了全部 13 个 source 文件差异、两项完整测试、共同 receipt/engine/journal、control drain/启动和 backup recovery 依赖。重新计算 13 个 source、4 个 evidence、20 个 migration 共 37 项 SHA256 全匹配；Go executable SHA256 匹配。作者 worktree clean，implementation `f05126d` 到 `c645ce3` 只修改两份测试：WAIT_TIMEOUT 类型比较和 ProjectProfile 查询；没有修生产逻辑来隐藏失败。source 到 evidence 只有 5 份收据文件。SQL 0001..0020 和 contracts 相对基线 `352828d` 无改动。

最终 raw 恰有 `TestPersistentActualControlHostClosedQualification`、`TestReleaseCutoverEncryptedSnapshotMechanism` 两个 top-level PASS，没有 FAIL。前次 compile error 和 SQL no rows FAIL 原始输出完整保留；更早零测试 compile 只作诊断。作者 manifest 报告 final exit 0；审查者未重放 Go 或业务测试。

实际新建 persistent host PID 82224，actual control PID 7864 / created 1790798797737591100 / image `1f4b104b810d6929761df3da69f7b4523d555084cc63807a586346a7a5007f67`。已有证据支持独立 host journal、control 独占 authority-root lease、私有 missing-candidate 拒绝、正常私有停止、准确原始 handle exit 与 lease 释放。所谓 restart 只指停止后重开 journal 和 fresh driver 不得制造 stop capability；没有第二个 live host takeover。

cutover 证据来自隔离数据库和合法旧计算器 proof。新加密 manifest `af9ddd3e2af207c0097639910188b626c54808527abb773746286c5ced26c35e` 与 pre-intent backup `82d095afde021ba3c74cb04be712bdb2edc96066b4a92895724d87a8de33538c` 不同。seal 后的 ProjectProfile 在还原目录保留相同 body；DISPATCHED 非重放状态保留，凭据全部撤销，外部 protected references 经原 CanaryStore 验证，authority 未复制 protected payload，原 failed DB 字节不变。重复 dispatch/cutover 和 closed lease restore 被拒绝。静态实现还验证 purpose、operation/epoch/admission、实际 DB/root、加密 manifest/schema/inventory，并在独立 stage 完成还原再发布。真实 rollback 已连接 drain→checkpoint→准确正常 exit→原 root lease→新 root restore，但本次没有完整实际 control rollback 证据。

## Scope retained

`ACTUAL_CONTROL_BEHAVIOR_PROOF=UNAVAILABLE`；不同 hash actual-control switch、Owner intent 后项目/任务连续性、实际 rollback、live host restart/lost-ACK 全链均未验证。这里的计算器快照机制 PASS 不构成 actual control 业务增益，也不是 formal W16/C20/A16 接受。没有触碰实际用户 DB/PID/provider、旧 S2、I2 SOURCE、SCM/LIVE；没有自动放开 authority。所有 reviewer 写入仅在本 verifier 目录，未改作者源代码、合同、SQL 或主 ledger。
