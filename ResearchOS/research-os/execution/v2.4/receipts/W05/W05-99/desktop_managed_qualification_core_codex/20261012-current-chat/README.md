# Desktop 私有受管资格 Core：Source 候选

状态：SOURCE_FIXTURE_PENDING_INDEPENDENT_REVIEW。作者不签发自身接受，不更新 Main、Canon、父任务或正式接受数。

Candidate `63dec0f43b7a30d36e68a9826dc36e633936318f`，base `dfefe326dd7f4ae528caaf311ae388f40b8f0841`。独立 sparse worktree `.local/worktrees/w05-desktop-managed-qualification-core-20261012`，12 个 Source 文件，提交后 clean。范围依据 CP412/OW201 与 CP413/OW202 amendment；未改 UI/CLI、frozen V2/Native3、旧 Core 候选或旧回执。

## 交付行为

采用原 control 进程内接线，保持单一 coordinator 和 data-root lease。`--desktop-management-stdio` 使用 Desktop main 持有的继承 stdin/stdout 管道；Core 从 Windows 读取真实父进程 PID、创建时刻、镜像摘要和 OS 身份，每帧复验。READY 的 CreatedNS 为十进制字符串，避免 JavaScript / canonical JSON 整数精度损失。完整 consumer/producer 合同见 `private-protocol.md`。

PREPARE 只离线准备与登记原数据库短期确认，不执行模型。确认冻结 Host、Owner/root、session revision/writer、模型配置、plan/profile、request ID、issued_at/expires_at（最多 60 秒）、单次无工具调用和 600 秒 mu_turn purpose。CONFIRM 的 Begin 事务重复全部绑定及时间检查，原子提交 Run claim 和一次性消费；所有 claim gates 后再次检查期限，过期整体回滚。重复 key、未知 JSON 字段、非法 Unicode、尾随对象和超长帧均拒绝。

CONFIRM 在唯一 scan mutex 下围住所有路由的普通调度和 session execution intake，直至原 Run、独立 verifier、服务端 acceptance 和 purpose 授权结束。全局 active Run / unresolved effect / unresolved dispatch 拒绝开始。消费后崩溃时从原 Run/effect/dispatch 与既有 idempotency 恢复围栏，绝不重放。结算后的 UNKNOWN/null 成本记录保持原样；未将 UNKNOWN 当零，也未改预算门禁。实际模型 effect 已发出后管理管道断开，原 Host context 继续结算，结果可由 STATUS 从原数据库重建。

私有协议不交付 Owner/verifier token 或 Key，不生成新的请求文件/管理业务数据库。旧 startup request 文件 consumer 仍要求既有确认，增加严格 JSON、绝对 regular/no-redirection 文件、protected current-user-only DACL 检查，不能通过自造文件绕过确认。未新增 HTTP/Native3 方法或任何 release fixture 状态。

## 最终验证

- `attempt08-frozen-build.txt`：control 与 verifier 实际构建；两者 `vcs.revision=63dec0f4...` 且 `vcs.modified=false`，Go 1.27.1。
- `attempt09-frozen-domain.txt`：28 parent + 73 subtest PASS，0 skip。覆盖 Begin 内过期/未来/超长 TTL、Owner/root/Host/session/config/plan 变更、未登记、撤销、重复消费、claim-crash/UNKNOWN 保留、真实 native fixture 中其他 READY task 不派发、离线准备、旧 qualification/root-liveness/UNKNOWN 与有界模型 checker 回归。
- `attempt10-frozen-host-private.txt`：7 parent + 12 subtest PASS，0 skip。真实编译 control 经继承管道和 Native3 Owner bootstrap，两代保持同 Host/Owner，原能力 orderly shutdown 后实际 exit=0；第二 coordinator 被原 lease 拒绝。实际 Host/Mu AppContainer/独立 verifier 使用纯合成 SSE 完成 PREPARE→CONFIRM→acceptance→purpose→normal session.send。重复 CONFIRM 拒绝；管理通道在原 effect 已发出时丢失仍结算一次。根撤销的 before_acceptance / before_qualify / before_purpose / after_purpose 四种反例保留旧 receipt/UNKNOWN，拒绝新 authority。
- `attempt11-frozen-verifier.txt`：2 parent + 9 subtest PASS，0 skip。原 verifier 独立私有帧与网络目标拒绝门禁。

最终 Host 文件中合成模型调用共 8 次：正常 private flow 2，lost-reply flow 2，root revocation 4×1。Domain 的明确 Mu fixture 也仅使用测试自己创建的 httptest loopback 服务。全部 real/local Ollama/paid/external model calls=0，protected_holdout=false；未访问 Root 的 11435 或旧 11434。所有测试 DB 是隔离夹具，不产生产品 LIVE qualification 或正式接受。

## 保留的失败与限制

`attempt02` 的 ACL 文本相等检查误拒绝 Windows 等效描述符；已改成 protected DACL / 单一 current-SID allow ACE 的结构核验，`attempt03` 和最终测试通过。`attempt04` 首轮真实管道因 CreatedNS unsafe integer 失败；已改 decimal string，后续通过。原记录全部保留。`attempt07` 正则选中了没有给 Mu bundle 的额外旧测试，12 条 skip 不计通过；最终 `attempt09` 使用明确资源与对应测试范围，无 skip。

首轮失败留下 fresh 0 模型、0 业务 control fixture PID 61540，按唯一候选镜像和完整唯一 Temp discovery argv 定点清理，记录在 `attempt04-orphan-fixture-cleanup.txt`。当时未保留创建时刻，因此此清理不属于严格进程身份或正常 shutdown 证明。生产代码没有 force-kill 路径；最终真实 control 两代退出均来自原私有 SHUTDOWN，测试也加入 finally 的原能力 graceful cleanup。最终核对本候选 control 无遗留活动进程。

删除该失败夹具临时目录 `C:\Users\yqyyds\AppData\Local\Temp\TestDesktopManagementActualControlLifecycle360862440` 的 PowerShell LiteralPath 递归清理被自动审批审查拒绝（blocked by policy），未执行，也未换通道绕过。该目录暂留、不是正式证据。

SHUTDOWN 复用现有真实 QuiesceForRelease，不豁免 UNKNOWN ledger / 未结算资源。因此存在该类历史时仍会拒绝安全退出；此边界保持 OPEN，不声称解决旧 paid UNKNOWN。in-place 资格流程本身不需要退出或重启。管理 link 失效不接管/重建外部 host；后续已管理进程生命周期可用 STATUS 读取原记录，不能自动再次 CONFIRM。

默认 Desktop main 还需由其独立作者接入本协议，经非作者 Source 审查通过后 Root 再整合和开展真实本地模型资格。这份候选只提供生产 Core 入口、可信 producer/consumer 和 Source+Fixture 证据。
