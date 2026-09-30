# 实际 control 发布资格的最小后续方案

这是只读设计建议，不是门接受、不授权实际发布、不修改合同或状态账本。输入为已独立审查的 control profile `104b83f`、R2 fix `20958cb` 及本次整合源码；开始时 main 为 `8fb31a5`，源码取证时为 `b894f78645987e98ada37d6aaf98efef067d262e` 且 tracked clean；收尾发现其他工作流正在修改安装/发布文件，未触碰。没有重跑私有 helper、native control、S2 或故障脚本。

结论：可以把笼统的 `ACTUAL_CONTROL_BEHAVIOR_PROOF_UNAVAILABLE` 拆成具体、可实现的绑定门，但目前不能删除这些门后宣布实际发布可用。最小后续有两条独立路径：真实行为改善支持正常收益晋升；预注册的独立恢复演练支持回滚机制资格。已有无增益证据属于第一条路径的正确拒绝结果，不是第二条路径的执行证据。

## 1. 无增益结论的覆盖范围

| 原要求 | 已有结论可支持什么 | 仍欠什么 |
| --- | --- | --- |
| C20-01 / C20-03 | 同一个实际 control 构建的 public/private 均无改善，正常请求拒绝候选并保持 stable；不能虚构收益 | C20 完整用例的双 rubric、旧产物不变而分数上涨场景及两套原始结果不能由本次替代 |
| A16-03 | 冻结样本、外部判定和零改善不晋升的 fixture 子结论 | LIVE_WINDOWS 独立身份、当前实际 authority、实际 stable 进程与业务连续性 |
| C09 | 支持不可绕过强制门的局部机制 | “局部指标改善但必需功能回归”完整输入，以及 stable 接受新无关任务；同构建 2/2 对 2/2 不是该场景 |
| W16 development_done | 规格允许拒绝改进候选后取得机制资格 | tasks.json 仍要求 A16 全部必需证据；正确拒绝不能单独完成 W16 |
| W16-G01 / W18-G02 | 无增益没有改变前置条件 | W18 已接受且 A12 当前恢复资格有效；真实导出、干净目标恢复、hash/inventory 核对及恢复后继续任务 |
| A16-01 / 02 / 04、W16-G03 | 现有 R2 代码和测试提供有限机制证据 | 独立 Windows 控制身份、真实 canary 到上一接受版本 hash 的实际回滚、状态/必要数据恢复、候选冻结、不循环晋升、稳定业务连续 |

依据：`spec/v2.0/08_AGENT_EXECUTION_GOAL.md:34`；`contracts/tasks.json:1917,1963-1978`；`06_ACCEPTANCE_TESTS.md:845-847,1734-1765`。成功发布仍需至少一个真实周期和至少 6 小时观察，最长 24 小时未满足要求不扩大；负向故障分支可立即触发，但不能替代成功观察窗。无需为了再证明已确认的无增益而重复旧测试。

## 2. 正常发布资格应如何接入

### 2.1 冻结的构建与输入

1. 新建可信的实际 control 注册配置，保持旧 fixture host 不可变。`RegisterEvolutionControlFixture` 明确传入 `releaseMechanism=false`；正常 `START_CANARY` 对有收益的 control profile 仍返回 503。这两个限制应由一个具有更强前置条件的新注册/admission 分支接替，不应原地改旧 host 事实。
2. 两个 EXE 都必须是 `apps/control` 的真实 Windows amd64 构建，绑定各自源 commit、完整 source inventory、Go 工具链、模块依赖、嵌入 SQL/contract 字节与输出 SHA256。稳定 EXE 必须等于 host 当前接受版本及实际 PID 的 image hash；候选必须等于计划和受保护 artifact 的字节 hash。执行前再次核对磁盘 image 与 PID/creation-time/image/root lease，不能仅检查编译元信息。
3. 先冻结 public/private 样本、标签、协议、投影策略和回归政策，再评价两个 EXE。候选改动仍限于已允许的三个 research 业务文件；如果另需扩大范围，应明确重新评审范围，不能把 evaluator、sandbox、release 或 schema 改动藏入业务收益。
4. 当前 public/private baseline 都是 2/2，现行规则要求两侧 gain，因此这套已饱和样本不能产生正收益。需要先确认真实既存缺陷，再预注册能检验该缺陷的新 profile/样本和独立 holdout。不得改坏 stable、降低标签标准或选过结果后更换样本制造收益。相同输入上真实差异仍为零时，接受“实验有效、候选拒绝”的结果。

### 2.2 当前 generation 与外部 Verifier

现有 `evolution_control_projection.go:57,187` 将完整源 DB 的逻辑 hash 写入 `AuthorityGeneration`，并绑定原 snapshot 字节 hash。它证明取样时的来源，不是对现运行 authority 的持续租约。评估过程中 TaskRun、Artifact、Acceptance 等合法写入也会改变完整 DB；直接要求最初 hash 永远相等会拒绝正常流程，忽略全部这些表又会放过权限/候选/证明变化。

最小可审查方案是明确三段：

- **G0（取样）**：从持有当前 data-root lease 的 authority 获取一致 snapshot，保存完整逻辑 hash、源字节 hash、业务 read-set/版本、slot epoch、root identity、稳定 image、冻结 profile 和当前权限摘要。运行可在隔离投影完成，原 authority 继续写入时必须记录随后影响本次决定的变更。
- **G1（资格封签）**：当前独立 Verifier 重新解析公私原始结果，按当前主体/角色/issuer 交集及 grant 验证权限。完整枚举 G0 后本次评估、产物、验收和候选状态写入的允许变化；业务 read-set、冻结样本、稳定 image/slot、候选源和必需政策应相同。其他变化或权限撤销一律重新评估或拒绝。给出完整当前 generation G1 与 G0→G1 的清单 hash；不能只加 `current=true` 字段。
- **G2（切换）**：封签后由 owner 协调 ingress/worker drain，最终一致 snapshot 必须包含已 DISPATCHED intent。G1→G2 只允许该 operation 已知、确定的 intent/cutover 元数据变更。备份和已验证恢复结果绑定 G2、数据清单与所需私有引用；未知/未确认外部效果阻断。直到 old PID 退出并由新 PID 取得根租约，切换 fence 不解除。延期、重新取样或重新封签均产生新证据，不得静默续期。

如果实现选择在 G1 前先完全 quiesce，必须另外提供狭窄、类型化且单次的 proof/intent 写入口；现有 quiesce 对私有写动作的限制不能通过重新打开普通写请求规避。外部 Verifier 必须独立于候选作者和发布执行者，凭据/密钥或受保护的认证 receipt 存储不能给候选写权限。104b83f 私有重算只是历史 receipt 复核，临时 authority DB 已删除，不能当当前 grant 的证据。

### 2.3 admission 的具体落点

保留 `releaseAdmissionInputs` 现有 `improved && required_passed && holdout.gain` 要求。扩展真实 control admission 所需类型和其 canonical digest，至少绑定：purpose/profile/protocol；G0/G1/最终 cutover generation 与 lineage；authority root/epoch；两个构建及源 inventory；public/private suite/policy/proof hash；当前 Verifier principal/授权版本及 proof；当前 W18 恢复资格；backup/restore inventory；无未知效果证明；operation、nonce、到期时间。可复用已有字段，但缺失内容必须由受保护的类型化包承载，不能只往未验真的自由文本填 hash。

同时更新并核对 seal、`FIXTURE_CURRENT`、dispatch、切换前检查和恢复检查对同一 canonical bundle 的验证。host 应从当前独立服务重新取得验证结果，而不是因为 candidate DB 声称 acceptance PASS 就相信。`ReleaseAdmission` 当前只有两 image hash、execution/verifier/holdout/backup hash、epoch、布尔值和 expiry，尚不含上述 generation/来源链；`releaseAdmissionInputs` 还限定 `R2_NATIVE_FIXTURE / os_service_qualified=false`，不能把它的返回值标成 OS 资格。

## 3. 故意故障能否验证真实 rollback

可以执行预注册、作用域受限的故障恢复演练；依据是 A16 明确允许负向故障分支，并要求 canary_then_rollback。它不等于普通候选收益晋升。最小新增协议应有独立 purpose（例如 `RECOVERY_QUALIFICATION`）、可信 host 签发的 QualificationIntent、固定两个 EXE/source hash、已实测备份、精确隔离 authority、预定故障点、最大持续时间和外部判据。正常 `START_CANARY` 和 `PROMOTE` 仍不得把 `improved=false` 当通过。

同行为而 hash 不同的两构建可验证 image 切换和状态恢复的机械事实，但必须准确报告“无收益”。更有意义的恢复演练是：先通过隔离回归和权限边界检查，在受限 authority 启动真实 candidate，取得真实 readiness/canary 观察，再由独立 host 在预定点终止候选或注入受控故障；由独立恢复控制面停止/确认退出、恢复数据、启动上个接受 image，继续一个无关的受限任务，核对业务状态并冻结失败 hash。禁止对 stable 先人为退化来造“收益”。

启动失败、必需回归、验收/权限篡改是分别有拒绝/恢复判据的负例。启动前已失败的候选不能记录“曾 CANARY”；隔离门不通过的候选不能为了演练直接走普通发布。若尚未实现独立的资格 purpose 和隔离边界，就继续阻断，不可用合成 improved=true 或总是返回 nil 的 AdmissionVerifier 开始演练。此新增路径最多逐步补齐 A16 负向/恢复机制；仍须原规格要求的独立身份、有效 W18 和其他必需证据，才可能评价正式资格。

## 4. restored DISPATCHED/EVALUATING 的合法投影

当前实现仅支持 journal 当前 `CANARY` 且 live process receipt 完整时，将 domain `EVALUATING` 和 slot `STABLE` 投影成 `CANARY`（`evolution_release_channel_windows.go:66-152`）。恢复 snapshot 保留 `DISPATCHED/EVALUATING` 是合理的；journal 已 `ROLLED_BACK` 时复用该函数会被正确拒绝。恢复目的根改变还会触发 `projection authority root changed`，应验证 restore manifest 后建立派生恢复上下文，不能篡改不可变旧 host root。

需要两个事实清楚、可重试的投影分支：

1. **journal 仍 CANARY**：复核当前 PID/creation/image/private readiness、相同 operation/admission/epoch、候选与当前 actor，再沿现有路径投影。重复同 receipt 返回同结果；不同 receipt 不覆盖旧 digest。
2. **journal 已 ROLLED_BACK**：新增 typed rollback observation，引用 host 的不可变历史 canary（确实发生时）、cutover/restore manifest、失败 candidate hash、last-good image、恢复后 root/inventory、当前 stable PID/private readiness 和冻结记录。一次 domain 事务消费真实历史并投影最终 STABLE/ROLLED_BACK；不可先伪造“当前 live CANARY”来调用旧函数。

SQL 0019 已规定只能 `PREPARED→DISPATCHED→OBSERVED→PROJECTED`，或 `PREPARED→FAILED`，receipt 一旦写入不可替换且行不可删除。因此 restored START_CANARY 不能直接 DISPATCHED→FAILED/PROJECTED，也不能删行重建。已有真实历史 canary receipt 时，以它补齐 START_CANARY 的 OBSERVED/PROJECTED，再用 action=ROLLBACK 的独立 operation 保存 rollback 事实并完成最终投影。这个补记事务是对 host 已发生事实的恢复记录，绝不再次 start/stop/触发外部效果；effect key 和 admission 引用必须确定且幂等。

如果启动失败从未进入 CANARY，需要单独定义合法的 failed-launch observation 类型，将事实记录为失败启动/恢复，不冒充 canary receipt。若 host 缺少必要历史，就保持待核对状态。当前 epoch 必须与真实 journal 一致：现有 Rollback 不自动递增 epoch，投影不得凭空加一。若恢复吊销了所有凭据，必须经可信恢复 provisioning 建立具备当前权限的 reconciliation actor；不能复活旧 token 或跳过 `releaseActorsCurrent`。任何绑定/权限/历史不完整时继续阻断投影。

## 最小实施顺序与资源缺口

1. 先补类型化 generation lineage、实际 control registration/admission 和 current Verifier 绑定；给出“元数据合法变更可通过、业务/权限/源码漂移拒绝”的定向证据。
2. 补 restore-context 与 rollback/failed-launch 幂等投影；验证恢复后不会重复执行 effect，也不会违背 SQL 0019。仅运行本改动直接覆盖的测试，不重跑已禁 S2。
3. 先用新隔离 authority 走完整无增益→拒绝；正常晋升仍关闭。随后完成独立资格 purpose 才能执行预注册实际回滚演练。
4. 只有在有效 W18/A12、独立 Windows Supervisor/Verifier 身份与 ACL、真实可归因改进、新 profile 的公私收益和全部强制回归均具备时，再走正常收益发布；成功观察窗按原规格执行。

当前明确缺口：已审查 control profile 没有任何正收益样本，不能凭现有 2/2 结果构造真实改善；同用户 fixture 不能证明独立 OS 服务身份；已有历史私有 receipt 不能证明现时 authority/grant；有效 W18 恢复资格及成功观察窗不能由这份建议或代码补丁生成。上述缺口应按实际条件继续保留，不能用文字降门。
