# Lawful restore projection / RECOVERY_QUALIFICATION 最小接入建议

状态：**READ_ONLY_DESIGN_ADVICE；不是 PASS，不授权运行或激活**。基线 `6c8f33aae15d8b3b4e7a2326fd809304aa25b4a8`，34 个读取文件均与该 HEAD 字节一致，见 `sourcehash.json`。未运行 native/private/provider、旧 helper、blocked CLI、activation 或测试；仅新增本目录两份建议证据。当前 control-generation 作者尚未 freeze；下述恢复 proof 必须依赖其最终契约，不在此另造 generation 规则。

结论：第一片可实现“真实恢复证据绑定 + 显式恢复 fence + 只读对账”，在缺少新授权时返回 `BLOCKED_RECOVERY_AUTHORIZATION`。完整补记接入既有 `release_host`、既有 peer/HMAC 私有通道与同一个 control DB writer。正常 START_CANARY 的收益门、成功观察窗、独立身份要求全部保留；不创建第二启动器或公开 API。

## 1. 现有调用链与事实边界

| 位置 | 当前行为及接入意义 |
|---|---|
| `evolution_release_cutover_windows.go:19,80` | QUIESCED 后要求 journal `DRAIN_UNKNOWN` 与 SQL `DISPATCHED`，冻结真实 authority DB 的 cutover；purpose 绑定 operation、root、database、epoch、admission。它不同于早先 admission backup。 |
| `release_host/control_windows.go:87`、`release_engine_windows.go:219` | 私有 host `rollback` 调 `RollbackFixture`：drain、准确 PID stop/exit、Compatible、last-good image 校验、Start、Ready，最后 journal `ROLLED_BACK`。回滚不递增 epoch。 |
| `control_fixture_windows.go:384` | Compatible 持有原 root 独占 lease，调用 Restore 回调；把 journal.Data 指到恢复目标并清 PID，然后才继续启动 last-good。 |
| `evolution_release_cutover_windows.go:95` | RestoreEvolutionCutover 校验 lease、固定 locator/purpose、外部保护引用、backup manifest hash，调用 `restoreBackupPolicy`，只返回 destination 字符串；未把 restore-report hash/after inventory 持久绑定到 host journal。 |
| `backup.go:516,628,637,656,676` | 解密验证、migration/schema/contract/inventory、beforeRecovery、source relocation、backupFence、接受关系重算、afterRecovery、after inventory、checkpoint、报告落盘和发布新目录；返回 `RESTORED_RECONCILIATION_REQUIRED`。 |
| `backup_recovery.go:backupFence` | 未完成 Run/外部 effect 保持 reconciliation fence，吊销全部 `auth_credentials`；不删除 `auth_principals/auth_grants`，不修复 evolution release projection。 |
| `evolution_release_channel_windows.go:66` | 当前投影仅接收 live CANARY、当前 PID/image/epoch、DISPATCHED、EVALUATING、旧 host root 与当前角色检查；恢复后 root 改变或 journal 已 ROLLED_BACK 都会拒绝。 |
| `release_receipt_windows.go:55,100` | 不可变 canary receipt 在 domain 投影前落盘；重读要求它等于当前 journal sequence/hash 且 candidate 仍 alive/ready，不能用于已结束 canary 的历史复核。 |

术语须分开：外部 `release.journal` 的 phase 是 CANARY/ROLLED_BACK 等；OBSERVED/PROJECTED 是 SQL0019 的 operation 状态。现有外部 journal 不持久记录“domain PROJECTED ACK”。不能把 journal CANARY 当作 domain 已成功投影，也不能把旧 SQL PROJECTED 当作当前 OS 存活。

已有 `same-authority-c645ce3/handoff.md` 与独立 `fix-20958cb/review.md` 只支持 cutover/恢复机制片段：恢复后 DISPATCHED 存在、凭据吊销、保护引用可解析、失败 DB 保留。它们明确未完成 actual-control 全链 rollback；本建议不扩大这些结论。

## 2. 精确缺口与危害

1. **恢复目的地缺少独立派生上下文。** 原 `evolution_hosts` 不可改，当前投影却只认旧 `host/data`。应创建绑定 oldRoot → restoredRoot 的恢复证据，不改旧 host registration。仅路径字符串或 restore-report 文件存在不够：文件在子进程启动后可被修改，须在启动前由持锁 host 固定报告 bytes hash、backup manifest、before/after inventory 和根身份。
2. **恢复副本表面仍 STABLE。** cutover 时 slot=STABLE、candidate=EVALUATING、op=DISPATCHED；恢复保留这些值是合法历史，却不代表当前可再次发布。需要恢复范围内的显式 `RECOVERING` fence，不删除/重建 operation、不重送 switch。
3. **没有历史 receipt 校验入口及回滚 receipt。** 当前 `ReadFixtureReceipt` 应继续严格检查 live CANARY。新增历史读取器必须对照完整 hash 链中的精确 sequence/hash/operation/epoch/image/PID/creation time，而不是伪造一个当前 CANARY snapshot。历史 alive 只表示原观察时 alive；当前健康证据来自恢复后的 last-good PID。
4. **旧权限记录会随备份复原。** `releaseActorsCurrent` 使用 `evolutionCurrentPrincipal`，只查主体、角色与 grant（含 remote 约束），不会认证已吊销 token，也不知道快照后发生的撤权。它是必要交叉校验，不是新的恢复授权来源。
5. **不可直接套用旧 fixture rollback。** `evolution_execution.go:539` 依赖当前 SQL CANARY 并执行 `epoch=epoch+1`，还涉及 Invoke/effect 流；R2 host rollback 保持 epoch。必须使用准确 journal epoch 的 CAS，不能调用旧 helper 修复状态。
6. **恢复报告不是完整 DB generation。** `backupInventory` 主要是指定表计数及 domain object revision digest，不覆盖全部授权/operation 行。补充 read-set/generation 必须引用正在冻结的 current-control 契约，并显式覆盖 operation、slot、candidate、保护 proof、授权与恢复差异；不能把 inventory hash 冒充完整 authority generation。

## 3. 第一片：先完成安全对账与 fence，授权不足继续 BLOCKED

在 `RestoreEvolutionCutover` 构造专用 backupPolicy 时，利用现有 `beforeRecovery/afterRecovery` 回调，保持通用 backup/upgrade 行为不变：

- beforeRecovery 保存被验证 cutover 的 operation、slot、candidate、不可变 host/proof/授权源 generation 摘要；可复用 `upgradeRows/upgradeExtra` 的确定性比较手法，但不要直接调用仅接受目标版本 14/20 且有迁移专属表假设的 `upgradeRecoveryInvariantForTarget`。
- afterRecovery 先复核只发生恢复允许差异：凭据 revoked、Run/effect fence、sources relocation、对应审计事件。对当前 operation 做精确 CAS：仅将原 `STABLE` slot 改为 `RECOVERING`，其 active/stable hash、candidate 与原 snapshot epoch 暂不改变；START operation 和 SystemCandidate 保持原状。此动作表示禁止新发布，不表示候选已 CANARY 或已回滚。
- 把这项派生差异纳入新的 typed `RestoreContext`（不是覆盖旧 manifest）：origin/current root identity、database locator、original host registration hash、operation/admission、cutover manifest hash、原 slot epoch、host epoch、restore report raw hash、before/after inventory、允许差异清单、恢复时间、current-generation 契约版本。host 在启动 last-good 前以 O_EXCL+fsync 保存不可变 context，并将 digest/locator 绑定进 journal。
- 回调返回类型由 string 扩展为内部 typed restore result（destination + context），`ControlFixtureDriver.Compatible` 只接收已验证结果。失败不发布可用资格，不动 failed root；若 context 已创建而 ACK/journal append 不明，读取固定 operation 的结果并核对，不能再造一个新恢复目录。

随后只读生成 reconciliation plan：对照恢复 DB、历史 receipt、完整 journal 与 restore context；列出需补记的 START/ROLLBACK 行和预期 revision。当前 actor/proof generation 不足时返回 BLOCKED，保持 RECOVERING、旧 credentials revoked、未知 effects 不重发。这一片无需声称业务授权可用，也无需开放实际 release action。

## 4. 完整合法补记的内部接入

### 4.1 host 观察与私有边界

在 `release_host/control_windows.go` 的既有 `rollback` 分支中：成功完成 mechanical RollbackFixture 后，取得 typed rollback observation 并发到同一 `d.Private`。如果 journal 已是本 operation 的 ROLLED_BACK，重试只做 observation/projection，不再次调用 RollbackFixture、Restore 或 Start。`status` 维持只读，不暗中修复 DB。host 重启后原 inherited capability 不在时仍 BLOCKED，不能从 journal 伪造 key/PID 接管；接管协议属于独立范围。

新增内部消息例如 `FIXTURE_RECOVERY_PROJECT`，在 `ReleasePrivateMessage` 放 typed recovery payload。它必须经过 `apps/control/drain_windows.go` 当前统一 qualification gate、准确 peer/PID/creation/image/root/epoch 检查和同一 writer。不得将新 kind 放在当前五动作拒绝列表之外绕过 gate。existing `handleQualifiedFrame` 是复用位置；未获得 recovery-purpose 资格时该消息仍明确拒绝。

typed rollback observation 至少绑定：purpose/protocol、source START operation/admission、历史 canary receipt raw hash 与其 journal sequence/hash、当前 ROLLED_BACK journal anchor、candidate/last-good/active image、frozen digest、RestoreContext hash、当前 root/DB generation、当前 last-good PID/creation/image、private readiness、回滚原因及观察时间。当前 READY token 应是实际启动的 `operation + "-rollback"`；旧 `receiptReady` 固定传 `s.Operation`，不能直接复制到 rollback receipt 中。

新增 history reader 只读已验证 journal 链中的历史行，不依赖当前 live canary；它验证历史事实，不执行任何 side effect。新增 rollback receipt 采用 O_EXCL+fsync、exact bytes digest、重复同 bytes 幂等。当前 observation 与历史证据类型不能互相冒用。

### 4.2 先补 START 事实，再独立 ROLLBACK operation

在 `evolution_release_channel_windows.go` 内部路由到新 domain helper，例如 `projectRecoveryPrivate`。它是新的恢复语义，现有 `projectReleasePrivate` 不放宽 live-CANARY 条件。先校验 RestoreContext lineage 和新授权，随后一个 DB 事务按以下顺序完成，外部观察不到中间状态：

1. load 精确 project/candidate/START operation，复核 immutable identity、expected_epoch/admission/effect_key、candidate plan、历史 receipt digest。DISPATCHED → OBSERVED 只写真实历史 receipt；已 OBSERVED 只接受相同 digest；已 PROJECTED 还须验证对应 domain revision/补记记录，而非只看 status。
2. 将真实“曾有 CANARY”的观察写为追加式恢复审计（记录原 observed time 和本次 recovered time），并生成对应 SystemCandidate 新 revision，但**不把其当前 status 改成 CANARY**。新 revision 仍 EVALUATING，表示历史观察已补记。START 的 OBSERVED → PROJECTED 引用这个真实恢复投影 revision；这是历史事实投影而非当前进程声明。若已有匹配 PROJECTED，复用该 revision，不再 bump。
3. 创建独立 action=ROLLBACK 行，确定性 identity 建议 hash(project,candidate,START operation,host epoch,RestoreContext hash,action)，effect_key 同样确定。SQL0019 要求新行 PREPARED，顺序推进 PREPARED → DISPATCHED → OBSERVED；这几步是**消费已经完成的外部事实**，helper 内不得 dispatch。其 admission_hash 绑定新的恢复授权 bundle；receipt_digest 绑定 rollback observation，不能覆盖 START receipt。
4. 精确 CAS slot：恢复 fence `RECOVERING + 原 snapshot epoch + 原 image hash` → `STABLE + 当前 journal.Epoch + exact last-good hash + candidate=NULL`。如允许已完成部分恢复的形态，逐一枚举，不能宽泛接受任意 CANARY/STABLE。epoch 取实际 journal，不执行 arithmetic increment。
5. candidate → ROLLED_BACK，填真实冻结原因、必要的受保护/可解析恢复报告引用；revision bump 后令 ROLLBACK → PROJECTED。通过现有 put/event/evolutionJournal 写入一致审计，事务提交。SystemCandidate 合同里的 `rollback_verified_receipt_id` 只有在已生成相应合法 receipt 对象时才能填写；不得塞一个原始 hash 假装 AcceptanceReceipt。

这两种 action 相互独立，但在同一恢复补记事务里有明确先后关系；不是先制造 current CANARY 再回滚。两个 PROJECTED revision 分别指向真实创建的恢复版本；终态 trigger 触发后，不得为了重试再次更新 ROLLED_BACK。重复请求先验证同一 immutable receipt/context/operation 和当前 final slot，再直接返回原结果。任一不同 digest、跨项目/candidate、旧 epoch、root/manifest/proof 漂移、未知 chain 断点一律冲突，整事务回滚。

SQL0019 现有 action/status 足够承载这条“确曾 CANARY 然后真实回滚”的路径；不改旧 migration、不开 trigger 后门。若从未到 CANARY（启动失败），不能消费不存在的 canary receipt。先保持 BLOCKED；后续以独立 typed failed-launch observation 与明确状态语义补充，不能把它伪装为上述成功历史。

## 5. 新恢复 actor / proof 的实际来源和当前限制

已有可信本机入口是 `apps/control/main.go:67` 持有 data-root lease 后的 `adminCredential`（`:101`），下接 `Service.ProvisionPrincipal` / `IssueCredential`。它只允许 INSERT 新主体和新 token，输出新私有文件；不是修改 revoked=0 的复活通道。**仅重新签发给快照旧 ID 仍不证明当前 grant**。新角色/grant 定义必须由当前可信本机管理员从未被回卷的当前授权依据明确提供，并绑定新 RestoreContext/generation；没有该依据则不发恢复资格。

该 CLI 无法在 restored control 已持有 lease 时另开 DB 写入。未来可在已授权维护窗口、control 启动前通过现有管理入口 provision；或由同一个已持锁 authority writer 复用该受信任内部 primitive，并承接明确验证过的本机请求。不能为了方便启动第二 DB writer、泄露管理员 token 给 candidate，或在 Restore 自动凭旧表 provision。此轮不执行任何 credential CLI。

独立 Verifier 可复用现有 `acceptance.go:prepareTaskAcceptance/acceptanceSnapshot` 的 token 认证、角色/grant/独立性入口，以及 `evolution_holdout.go:evolutionHoldoutVerifierCurrent` 的冻结身份交叉检查；但当前这些函数**没有签发 recovery-generation proof 的现成协议**。应等 current-control generation 契约 freeze 后，增加内部 `RecoveryAuthorization` 验证 adapter，输入受保护的新证明，而不是返回 nil 的 verifier。该证明绑定当前 actor/issuer 交集与授权版本、新目的根和 generation、不可变历史 receipt、context、purpose/expiry，并限制为一次本 operation 的补记/冻结；不能授权 PROMOTE 或下一次 START_CANARY。

原 `releaseActorsCurrent` 保留为原 host/作者/历史验收关系的检查，但不能要求修改 immutable host 来替换 release_principal，也不能把旧 verifier ID 的 grant 自动授给新主体。新增 reconciliation actor 是独立主体，授权 proof 明确把它映射到这一份恢复上下文；只有合法新授权可允许它补记旧 operation。历史 admission 可以已过期，因为只读/补记既成事实不重放原 effect；新的 reconciliation authorization 仍必须当前有效，不能续期旧 admission。

## 6. RECOVERY_QUALIFICATION 与其他资格的隔离

| 路径 | 可证明的内容 | 不能替代 |
|---|---|---|
| 第一片 reconciliation + fence | manifest/journal/DB 来源一致，禁止重复 effect，授权缺失安全阻断 | 真实授权、actual rollback 执行、任何门 PASS |
| RECOVERY_QUALIFICATION | 预注册故障点下真实切换、last-good 恢复、必要状态一致、冻结及受限业务续行 | normal gain、成功发布、private holdout 独立性或 SCM |
| normal-gain admission | 独立同样本收益、必需回归、当前 generation、实际 actor/proof | 不能用 improved=false 演练结果替代 |
| 成功 canary | 至少真实周期 + 至少6小时，最长24小时未满足不扩大 | 不能用即时故障回滚代替观察窗 |
| SCM/LIVE 独立身份 | 真正独立 Windows 服务身份、ACL/恢复权限及当前 W18/A12 | 同用户 CanaryStore/HMAC capability 只属 fixture 机制 |

RECOVERY_QUALIFICATION 后续应采用独立 typed QualificationIntent/purpose，绑定固定两构建/source inventory、隔离 authority、最终 generation、真实备份/restore context、预定故障点、期限与独立核验人。它不能通过给当前 `ReleaseAdmission` 填假 improved/holdout.gain 获得普通 START_CANARY。复用单一 engine/process/drain 执行器，在未来的 purpose admission adapter 中区分资格；当前 `ReleaseAdmission` 和 journal validation 仍只有普通 fixture 假设，应明确拒绝未知 purpose，而非把新增字段当万能 bypass。generation 契约未 freeze 前不确定其序列化格式。

`releaseBackupGuard` 当前明确要求 CanaryStore/CANARY_ONLY/非独立身份/同用户可读，并依赖 ORIGINAL_CANARY_STORE；`RegisterEvolutionControlFixture` 与 actual gate 的限制不会因本建议消失。A16 原文允许即时负向故障，但正式资格仍要求有效 W18/A12、独立控制面、真实状态/数据回滚、冻结与业务连续。这里不写新 evidence PASS。

## 7. 最少文件改动建议与定向验证

第一片建议只触及 `evolution_release_cutover_windows.go`（专用回调、typed result/context）、`control_fixture_windows.go`（接 typed result 并在 Start 前固定 journal 绑定）、`release_journal_windows.go`（可选 context 引用及验证）、`release_drain_windows.go`（内部类型），以及新增一个 domain recovery helper 文件。不修改 generic backup.go/backup_upgrade*.go，也不改0015/0019。新增 journal 可选字段必须 omitempty 或版本化保留旧 bytes/hash 解释；不能让读取旧记录时重新序列化改变历史 hash。

完整补记再扩展 `release_receipt_windows.go`（history/rollback 类型校验）、`release_host/control_windows.go`（rollback完成后/重试的投影）、`evolution_release_channel_windows.go`（内部路由）、`apps/control/drain_windows.go`（新purpose门/同通道校验）。helper 可放新 `evolution_release_recovery_windows.go`，不复制旧 launcher。原 engine 的 Start/Stop/drain/epoch 算法本轮无需重做。

授权后只做对应定向测试：真实 cutover-derived DISPATCHED/EVALUATING 还原后 fence；相同历史重复请求不重复修订/事件；错误 digest/root/epoch/manifest/current auth 拒绝；revoked credential 与旧 grant-only 输入不能授权；事务每个崩溃点无半个最终投影；host ROLLED_BACK 重试的 Start/Stop/Restore 计数为0；epoch与journal逐字相等；无历史CANARY不能走canary补记；旧journal序列化兼容。后续独立资格实施才执行新预注册 actual演练；不重跑已完成 control-drain、旧无收益、S2 或旧 private helper。
