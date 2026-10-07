# R2 two-P1 correction independent delta review

结论：`PASS_BOUNDED_CORRECTION_DELTA`。源 `20958cbd6d35c11c2d8822518a398f7d5e0d1c11`，证据 `533e8d1a288c6b4a4778e8356264617d9aba05b6`。两个 P1 在本次限定修复中关闭，没有发现阻碍 root 串行集成的新问题。原 `c645ce3` 的 `NEEDS_FIX` 报告保持原文与原 hash。本结论不打开 actual-control 发布资格，不构成阶段或正式验收。

## Findings closed

`R2-READY-RETRY-PROJECTION`：SwitchFixture 与 RollbackFixture 在 Start 后、Ready 前先把实际 PID/creation/image 写入已有 RECOVERING；Ready 成功才记录 CANARY/ROLLED_BACK。Ready 失败可保留真实已启动进程身份，而 Switch、host execute 和 Reconcile 对此未知状态均不重发 Start。新的状态顺序与现有 ControlFixtureDriver.Ready 的准确 process/root/epoch/image 绑定兼容；actual 成功子例也经过此分支。

共同 `receiptReady` 对没有 Ready 能力的 driver 返回错误。WriteFixtureReceipt 在产生任何新回执前调用它；已有回执的 readFixtureReceiptBytes 同样调用，覆盖 ReadFixtureReceipt、existing-file retry 和竞争创建后的重读。actual host 固定传入 ControlFixtureDriver，其 Ready 重验 inherited private HMAC 通道、准确进程、root/epoch/token、startup completion、lease 与 listener，之后 HTTP health 和 liveness 作为补充。旧 NativeFixtureDriver 明确使用 marker-fixture Alive readiness，不表示 actual control readiness。调用跟踪未发现 actual host 可通过请求 flag 选择旧 driver。control 的未来 qualified PROJECT 分支另加 startup/lease/listener 检查；该分支当前因显式关闭不可达。

`R2-ACTUAL-PROFILE-GATE`：真实 control 在完成 named-pipe peer/HMAC/root 基础验证后，对 FIXTURE_SEAL/CURRENT/DISPATCH/CUTOVER/PROJECT 五个动作统一返回 `ACTUAL_CONTROL_BEHAVIOR_PROOF_UNAVAILABLE`，在调用 domain 前结束。不存在 request/config flag 打开此分支；rg 确认 handleQualifiedFrame 只由该统一 handler 调用。原 READY/QUIESCE/RESUME/COMMIT_EXIT 仍走正常控制路径。通用 domain 快照机制可继续隔离验证，但无法借实际私有入口把旧计算器 proof 当 actual business proof。未来集成必须以可信 exact-build/current-profile/generation helper 替换明确关闭门，不能直接删掉门或改为 caller boolean。

## Evidence and verification

独立完整读取 8 个 changed source 文件的差异、新增测试、原始输出、handoff/manifest 与所有 receipt 调用点。31 个 hash（8 source、3 evidence、20 frozen SQL）全部匹配；pinned Go SHA256 为 `d3ccdb604eafa6031133aefe1a3db24f0bb7362b857bc2125ac4e4c178b4b490`，与前包冻结值一致。source 到 evidence 仅 4 份收据文件；contracts/SQL 无差异；作者 worktree clean。原 review.md SHA256 仍为 `0a230135bb02d68fe55f03267d1c2ac5788b1c41c33bca9293cd10842641d66f`。

作者两个限定命令在该 source 均报告首次 exit 0。targeted-gates.raw.txt 恰有 3 个 named PASS；normal-private-ready-receipt.raw.txt 有 TestActualControlDrain 父项与唯一 idle_same_root_switch_preserves_data 子例 PASS，没有 FAIL，未把父子计作两次独立业务检查。

- Ready 失败反例是 deterministic simulated process：保持 Alive=true，验证 RECOVERING identity、Start=1、不产生 usable receipt、不重放 switch/reconcile；历史 CANARY 形态的新旧回执都重验 Ready，失败不落新 receipt，成功分支可写。它未执行 native private-READY failure injection，也没有实际调用投影 DB；投影被阻断的结论另由 host 在共同 receipt gate 之后才调用 PROJECT 的控制流支撑。Rollback 的相同顺序经静态检查，未新增完整实际 rollback 测试。
- 五个发布动作经过真实 authenticated named pipe 并精确返回 unavailable；测试 server 与 peer 同一进程，service/DB 未设置，提前拒绝不会进入 domain。它不声称跨账户隔离。
- 实际 release_host PID 27112 启动 actual control PID 86388 / created 1790799234349346300 / image `894af9ad4e71a5d487acac88e595e316808854bab754809032bd9b6a84d2ee77`。seal 精确拒绝，stable identity 保持，第二 writer lease 被拒绝，正常停止释放 lease。
- 精确 actual idle 子例使用 synthetic admission 和同一 image：old PID 54332、新 PID 15972；Project `b6e0519656ad372f24a9f8c87452fd75` revision 1 和 profile hash `2606188aa9e044204300b05f11216af818398ee3486bd346158afd6b3ad56a0d` 经实际 HTTP GET 保留。新增 WriteFixtureReceipt/ReadFixtureReceipt 均经过 actual private READY 且回执 hash 相同。

审查者只读源码和原始证据、重算 hash，没有重跑 Go、native 服务、故障注入、CLI、旧 S2/adversarial、provider 或实际用户 DB。只在本 verifier 子目录写报告。

## Remaining scope

`ACTUAL_CONTROL_BEHAVIOR_PROOF=UNAVAILABLE`。不同 build 业务提升、actual cutover 与完整 encrypted rollback、live host takeover/lost-ACK、SCM/LIVE、正式 W16/C20/A16 仍未接受。cutover snapshot 保留 DISPATCHED/EVALUATING；后续合法 rollback projection 需由 durable host observation 派生，不能假设还原 DB 已处 CANARY，且需保留 credential revocation/reconciliation fences 并重新建立 current actor/proof/generation 资格。此处仅保留待验条件，没有扩展实施或执行。
