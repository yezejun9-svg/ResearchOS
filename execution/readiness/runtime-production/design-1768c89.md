# Runtime production 最小施工设计

状态：`DESIGN_READY_NOT_IMPLEMENTED`。本文件是施工输入，不是产品验收回执。设计基线 `1768c89`，最终源码核对 HEAD `0d8f692469727049a5c35a4d90922ffb41134e14`。期间 W15 的 skills/source-conflict 修改已进入共享文件；后续施工须保留这些修改。此次只创建本目录指定的 JSON/Markdown，不运行模型、worker、服务、测试或迁移，不变更产品源码。

结论：两个连续切片足够补齐接口与协调机制。S1 先修复资格任务的完整执行/独立接受路径并实现冻结的 `qualifyRuntime`；S2 再把同一 authority DB 的 READY claim 接到有权限边界的 worker、生命周期回执、预算与恢复。不能仅删掉现有 FIXTURE 检查，也不能把 W16 `fixtureHost` 接到 LIVE。真实 Codex 工具资格仍受 `RQ-W05-CLI-POLICY-001` 阻塞；本设计不产生 A04、W05 G02、W06 G03 通过结论。

## 1. 当前缺口与可复用点

| 源码锚点 | 现状 | 最小变化 |
| --- | --- | --- |
| `internal/domain/runtime.go:21` | `BeginRuntimeQualification` 直接为 dependency-free DRAFT 建 Run，未冻结合同/依赖，Task 仍 DRAFT | 复用提交和 claim 的事务内校验；资格私有标记只豁免“已有资格”一项 |
| `internal/domain/orchestration.go:94,235,298` | 已有冻结合同、上下文、冲突、并发、重试上限、依赖快照与 Run 原子 claim；343 行固定 fixture | 抽取共同 claim 校验与 `currentRuntimeAdmission`，保留 fixture 路径 |
| `internal/domain/acceptance.go:10,162,239` | 短事务快照、事务外验证、最终重查已经正确；103 行固定 fixture，251 行生成 fixture evidence | 增加有绑定的资格接受及普通已获资格运行接受；mode 由可信快照决定 |
| `internal/domain/runtime.go:102,150,337` | 可信本地 observation、epoch/lease、seal/report 可复用；scope 将大多数 runtime 操作视为 Run | observation 增加可信 dispatch 来源绑定；`qualifyRuntime` 明确按 RuntimeRegistration 作用域 |
| `internal/domain/resources.go:161` | replacement 强制 fixture；已有 same-Run 交接 | 替换为共同当前资格/权限检查；保留停止、effect 已对账、版本条件 |
| `internal/domain/durability.go:41,111,201,234` | effect 的 PREPARED/STARTED/UNKNOWN、预算和 checkpoint epoch 已存在 | 抽出事务内 helper；bridge 实际接入，不造第二套账；resume 补资格检查 |
| `apps/control/main.go`、`ops/runtime/main.go` | 分别是 HTTP host 与单个已准入 Run worker | 在 control 内增加唯一协调循环；worker 仍不选择 Task/Goal |
| `adapters/runtime/runtime_windows.go:121,467,520` | intent journal、Job、lease watchdog、reconcile 可复用；同用户进程及继承环境不构成任务权限边界 | 接入 W10 AppContainer，取消生产 child 的宿主凭据/代理环境继承 |
| `ops/experiment_sandbox/sandbox_windows.go:78` | 已实际使用零 capability AppContainer、Job、专属 staging ACL | 提取可复用异步进程边界，保留 Run 包装与 W10/W16 fixture 行为 |

冻结依据：`spec/v2.0/02_TECHNICAL_DESIGN.md`、同目录 WBS 中 W05/W06/W12/W19，以及 `contracts` 中 RuntimeRegistration、QualifyRuntimeRequest、qualifyRuntime。冻结文件保持逐字节不变。心跳 15 秒、租约 90 秒；启动前持久化意图；PID 必须结合创建时间和 worker/Job 身份；UNKNOWN 不自动重试；独立接受不得自签。

## 2. 唯一 authority 与最少持久化

复用现有 Task/Run、`orchestration_contracts`、`orchestration_run_dependencies`、`runtime_observations`、artifact/upload/use、effect/budget、资源路由、idempotency、outbox。建议只加三张私有表，不扩张冻结公开 schema；migration 编号由主 Agent 串行分配，开发仅新建临时 fixture DB。

| 表 | 主键与关键字段 | 约束 |
| --- | --- | --- |
| `runtime_bindings` | `(project,runtime)`；immutable profile Artifact ref/hash、technical fingerprint、owner authorization/credential reference revision、allowed routes、sandbox profile | 绑定建成后不原地换技术身份；凭据只存引用；更新技术配置必须新 profile 和重新资格 |
| `runtime_qualification_runs` | `(project,task)` unique，run unique；frozen plan/profile/hash、contract/input/context hashes、bootstrap author/root、requested capability set、validity bound、一次执行 marker | 只有 trusted local bootstrap 可写；不能凭 task_type 字符串获得；不另存可调度状态 |
| `runtime_dispatches` | `(project,run,epoch)`；unique dispatch key、immutable manifest hash、profile/build/input/contract/context hashes、worker instance、可信 journal locator、CAS state、observation sequence/hash | 状态 PREPARED/STARTED/OBSERVED/UNKNOWN 描述一次启动；不是第二 Task 队列；一次 key 只启动一次 |

每个 authority data root 只允许一个 control coordinator：启动时对规范化 data directory 的锁文件取得 OS 独占句柄，持有至进程退出，失败则拒绝启动协调循环。SQLite 单连接不能替代跨进程锁。worker 仍保有自身 journal 独占锁。来自 API 的路径、UUID、runtime metadata 不能直接变成本地可执行路径。

profile Artifact 冻结：程序/build hash、适配器及其版本、backend/model 的预期与可验证身份、Windows/platform profile、AppContainer capability/ACL/environment/egress profile、命令/输出合同、凭据引用 revision、允许工具/route、最大有效期及 resume 要求。实际 observed identity/capabilities 必须在 host 证据中出现。`Spec.Model` 只是配置；无法观测到的 model/backend 不能宣称已证明，也不能授予依赖该能力的资格。

避免资格自失效：资格 Task 的输入引用 immutable profile Artifact，不把“待更新为 AVAILABLE 的 RuntimeRegistration 当前 revision”放进 effective input 链。私有绑定记录当时 runtime ref 的历史和技术 fingerprint；qualification 验证技术 fingerprint，status/health/qualification_ids 的生命周期变更不改变技术身份。变更 binary/model/backend/adapter/platform/permissions/credential revision 会失效；不能借此排除真正影响行为的配置。

## 3. S1：窄资格引导与 qualifyRuntime

`BeginRuntimeQualification` 继续是 trusted local 入口，没有新增 public owner bypass endpoint。它只能执行 host 预先批准的 frozen qualification plan；用户填一个同名普通 Task 不够。owner 必须当前有效且有项目授权，executor 有当前有效 EXECUTOR 角色，profile 必须已登记、权限边界可实现、runtime 非 REVOKED/UNAVAILABLE。

一个短事务完成以下步骤：

1. 校验 exact DRAFT Task、ACTIVE Goal、current inputs/context/policy、无冲突、资源约束、no-progress、attempt/project/global concurrency、没有未对账前次运行，以及 plan 中的必要独立检查。
2. 走共同 submit helper：冻结合同，生成依赖快照，DRAFT → READY。资格任务仍要求 dependency-free，但持久化空依赖向量，不能省略表记录。
3. 写一次性 `runtime_qualification_runs` marker，走共同 claim helper，只豁免“已具备资格”的检查；创建 Run/lease/grant、dispatch intent/预算状态，READY → RUNNING，保存事件，提交。
4. 提交成功后 bridge 才能启动；失败则整个事务回滚。不能直接 DRAFT → RUNNING；现有 transition 不允许，且 DRAFT 也不能通过 `BeginEffect`。

bootstrap 的豁免只在该 exact Task/Run/epoch/profile/plan 上有效，无普通任务继承、无任意命令/工具授权、无资格期间 normal claim、无跨项目使用、无自授权凭据。未授权的真实 Codex 仍不启动。

资格运行产物按真实 provenance sealing/report；fixture 原生程序测试保持 FIXTURE。完成后独立 Verifier 使用现有 accept 接口，`acceptanceSnapshot` 在资格 marker 分支校验 exact frozen plan/profile、可信 host observation、完整原始 bytes/hash、current epoch、停止且队列清空、effect 全部对账和必要能力检查。保留当前短事务/事务外检查/最终快照重查。Verifier root 必须区别于 executor 和资格发起/证据作者 root，角色与 project grant 在最终事务重新检查；同一个 OS 用户的两个 Agent 并不自动形成受保护的独立性。

接受所得 `AcceptanceReceipt` 的 subject 为该 `runtime_qualification` Task，verdict PASS，mode 必须与实际证据一致。使用一种由服务端快照确定 mode 的 observed-artifact helper，保留 `serverArtifact` 既有 FIXTURE 调用者，避免把 W15 等旁路全部改为 LIVE。`AcceptanceReceipt.qualification_ids` 原有 W11/Jev 语义不变；确定性验证仍为空。Goal LIVE 接受不在本切片范围，不能由 Task 接受推导 Goal 已完成。

实现既有 `POST /v1/projects/{project_id}/runtimes/{object_id}/qualify`：保留冻结 body、条件更新、幂等和公开错误码。事务内验证：

- 当前 Verifier role/project grant、authority root 独立；expected Runtime revision 与 Idempotency-Key；runtime 非 REVOKED/UNAVAILABLE；profile 技术身份 exact/current。
- `qualification_ids` 非空且去重，每项必须是同项目的 PASS `AcceptanceReceipt`，指向已独立接受、具有私有 marker 的 exact qualification Task/Run；普通 Task receipt、W11 `Qualification`、跨项目 ID、自签、历史失效 input、未对账 effect 均拒绝。
- 必要能力覆盖必须由 frozen plan 定义，不能由请求挑一组容易通过的 receipts；原始 host evidence 与合同、输入、实际 observed backend/model/adapter/platform/权限/build 一致。没有真正 LIVE 证据不能为 LIVE runtime 授予资格。
- `receipt_artifact_ref` 是已密封、同一 runtime/profile/资格 Task 的可信证据；不是任意报告。`supports_resume=true` 必须有独立 exact resume proof；无 proof 则拒绝，false 不暗示 checkpoint/native resume 能力。
- 服务端按冻结 plan/策略和 evidence 时间计算有效期；不接受调用方自报无限期。资格 receipt 的签发者 principal 被撤销、失去相关 role/grant、profile 改变、evidence 失效或过期立即阻断后续使用。签发时 HTTP token TTL 到期与 principal 撤销不同，正常 token 轮换不会自动撤销资格。
- 全通过才写 Runtime AVAILABLE/qualification_ids/supports_resume/receipt ref 和事件。状态变更不能清洗技术差异。

`RuntimeRegistration.qualification_ids` 在 `store.refs`、visibility/workbench graph 和 runtime route request 中按明确 owner kind/operation 映射 `AcceptanceReceipt`。不要全局改 `idTargets["qualification_ids"]`；W11 `Qualification` 仍沿用原解析。嵌套 graph helper 必须传播可信的实体 kind/操作上下文，不能根据调用者可伪造的 `adapter` 字段判别。`runtimeScope` 对 qualifyRuntime 特判 RuntimeRegistration，否则误用 currentRun。

共同 `currentRuntimeAdmission(tx, project, task, runtime, requestedCapabilities, operation)` 返回受验证的 profile/mode/qualification/permission/evidence/expiry snapshot。S1 实现并测试这个检查函数，普通 LIVE claim 开关仍关；S2 将 claim、dispatch、accept、resume、replacement 接到它。S1 独立验收通过才开展 S2。

## 4. S2：一次 READY 到独立 accept 的运行

control 内协调器只扫描现有 DB READY Task；没有新业务队列。它在 OS 锁下使用当前 Scheduler 服务身份及项目授权，按既有合同策略选择已批准 runtime/executor，然后调用共同 claim。不得创建替代 Goal/Task 掩盖失败。

```text
READY
  claim transaction: existing gates + currentRuntimeAdmission
    -> Run/lease + dependency snapshot + required cost admission + dispatch PREPARED
    -> Task RUNNING + events -> COMMIT
  trusted bridge: recheck current epoch/admission; create owned staging; validate hashes
    -> durable worker intent -> AppContainer + Job + suspended process
    -> durable PID/creation-time/worker/job/profile binding -> resume process
  bounded protocol: heartbeat/checkpoint/proposed effect/output
    -> authoritative heartbeats + immutable sealed artifacts + effect ledger
  process exited + streams drained + Job children stopped + effect reconciliation
    -> host observation -> seal/report -> Run SETTLED -> Task EXECUTION_REPORTED
  current independent Verifier: snapshot -> checks outside TX -> revalidate + accept
    -> AcceptanceReceipt + Task ACCEPTED (Goal acceptance remains separate)
```

两次资格检查间的撤回通过 launch 前检查、每次 effect/resume 检查及 worker 心跳撤销传播限制；最终接受再检查。不声称能够撤销已经提交给外部 provider 的操作。失效后不发新请求，停止 worker，仍保留并对账晚到结果与成本。

worker 从 trusted immutable manifest 启动，不读用户传入 shell 任意文本；平台命令模板、输出目录、broker routes 由绑定决定。保留 worker 单 Run 职责。control 持有 executor token/lease 与 provider secrets，任务 AppContainer 不拿 bearer token、authority DB 路径、Codex auth home、宿主 profile/代理环境。host bridge 代表已绑定 executor 调用现有 upload/seal/heartbeat/report；auth grants 不放大为 project owner。

### 真正的任务权限边界

复用 W10 sandbox：每次新 AppContainer SID，零 capabilities，专属只读 input/只写 output staging，最低必要继承句柄，Job kill-on-close、单进程与 256 MiB 限额，当前最大 5 分钟边界。提取异步 start/stream/wait/cancel 接口，保留旧 `Run` 包装用于 W10/W16。增加 `beforeResume` hook，把 PID/creation time/job/worker identity 写进可信 journal 后才 ResumeThread；当前 runtime adapter 在启动函数返回后才记 PID，不能保留这段空窗。

原始 sandbox 一次性返回 raw streams；生产 bridge 还需有界增量流、丢失检测、完整性 hash、进程终态和 cleanup receipt。child 数据只是候选输出，不能自称 trusted observation。adapter/model/权限能力证据由 host 采集，绑定 dispatch key、sequence、build hash 和原始协议摘要；通道关闭、stream 超限或截断均不能成功 settled。

零网络 native 程序是当前可以真实测试的 profile。需要 provider 的生产方案采用凭据只留 host 的 typed broker；AppContainer 经私有匿名管道请求批准的 route/capability，而非任意 URL/header/shell。host 校验 exact Run/epoch/profile/owner-purpose grant、能力、预算、request hash，再发出固定路由请求。这个 broker 是待实现的生产依赖；受冻结保护的 broker 79136 不调用、不重启、不复用实验会话。

本切片不得为使 Codex 跑通而增加 internetClient、复制 auth home、换 launcher/代理执行已拒动作、放宽审查或 Job 进程数。真实 Codex CLI 是否适配零网络/typed broker、实际 tool 能力、provider identity，均须独立授权的后续真实证据；机制 fixture 不能填补该缺口。

### 生命周期与 effect/budget

心跳每 15 秒，只有 DB 当前 Run/epoch/lease 成功续期后才给 worker renew，worker 用单调时钟执行 90 秒 watchdog；控制通道 EOF、失败 heartbeat、过期或 cancel 都停止。睡眠唤醒先检查实际 lease 与进程身份，不无条件续期。checkpoint 先验证并 seal，再 heartbeat 绑定；candidate 发来的文件路径不能越过 output root。

`settled` 必须同时满足进程真实退出、stdout/stderr/protocol 全部读完、Job 子进程停止、内部待执行命令队列为空、必要 artifacts 密封且 hash/size exact、当前 epoch、所有相关 effect 已完成对账。进程 exit 0 或 JSON `turn.completed` 单独不足。stop 先撤销新增 effect，发送取消并在截止后结束 Job；可信 stop receipt 才允许 acknowledge。reconcile 不是重发命令。

每个 proposed provider effect 使用稳定的 `(Run, logical effect key, request hash)`；同 key 不同 hash 拒绝，新 key 不能绕过已 UNKNOWN 的同一动作。先 `PrepareEffect`（持有资源写锁、current goal/context/epoch/policy、预算 reservation），再 `BeginEffect` 成功持久化 STARTED，最后 host 发请求；trusted receipt 驱动 `ObserveEffect` 与预算 SETTLE/UNKNOWN。遇到 blocked by policy 即资源阻塞，不重试。

claim 的整体 admission 与 cost/effect reservation 必须在同一 DB 事务，不调用会再开启事务的 public method，以免单连接死锁。抽出 `prepareEffectTx`/预算 helper。`reserveFixtureDispatch` 的 0 USD 仅适用于已证明免费 fixture，不能拿来代表 LIVE。已知上界 reserve；未知成本记录 UNKNOWN，strict cap 拒绝，允许未知的明确策略可保留 UNKNOWN，但不宣称免费。区分本地无费用 launch 与真正 provider 请求，避免重复扣款；晚到实际费用归原 Run/epoch，即使超过估计也如实记账。

replacement/resume 复用同一 Run；先确认旧 process/children 停止、effect 对账、checkpoint 和输入版本有效，再校验新 runtime 当前资格及 owner-purpose grant，旋转 epoch 和 ResourceSession，保留路由历史。native resume 必须单独 proof；`ResumeCheckpoint` 的 fresh session 恢复保持 `native_resume=false`，不能冒充 CLI 原生续跑。recovery 所需能力也须在 frozen plan 明确。

## 5. 新进程恢复：宁可未完成，也不重发 UNKNOWN

| 崩溃点 | 新 control 的动作 | 允许重新执行吗 |
| --- | --- | --- |
| claim 事务未提交 | 没有 Run/dispatch，按正常 READY 处理 | 可按正常 claim；没有已提交启动事实 |
| PREPARED 已提交，尚无确定进程证据 | 查 worker journal、Job/PID 创建时间；无肯定未启动证明则 UNKNOWN | 不自动启动；不因缺 PID 推断没执行 |
| suspended 创建后、journal 写入前 | Job handle 关闭杀进程；核验现存身份/停止，保留 dispatch 未决 | 不据缺记录重新 launch |
| STARTED/provider 请求后、receipt 前 | 旧 effect STARTED → UNKNOWN；读取可信 provider 对账依据 | 不换 key、不换 runtime 重试；无证据则保持未决 |
| 已退出，artifact/receipt 尚未入 DB | 读取完整可信 journal/原始文件，校验 exact dispatch/epoch/hash | 只补录旧事实，不重跑 |
| seal/report 已提交，ACK 丢失 | 同键读回 seal/report/current Run，验证已有事实 | 幂等返回，不新建 Run |
| coordinator 重启仍有旧 worker | reacquire OS lock 后先执行只观察/停止的 reconcile，核验 PID+creation time+worker/Job | 只有显式 resume 合同满足后，同 Run 新 epoch |

现有 upload/seal 要有效 lease，故补录过期 epoch 需要新增 **仅 trusted local recovery-ingest**：从 host-owned journal locator 读取终态 bytes，在事务内验证 dispatch、原执行身份、旧 epoch、artifact manifest、effect 结果及当前冲突，幂等写入历史观察/回执。它不能续执行 lease、不能新命令、不能接受 HTTP 上载自称旧回执，不能影响新 epoch。若当前 Run 可安全完成，再由正常 report 核验 helper推进；否则保留 reconciliation-required。不要放松全局 lease 校验来补这条路径。

现有 `Reconcile` 的 “进程已不存在/children stopped” 只证明生命周期；它不能证明外部 effect 未发生。无法确认的状态明确为 UNKNOWN，旧 reservation/成本不清零。恢复流程不能 fork 新业务身份。

## 6. 文件边界与集成顺序

S1 owner 新建 `internal/domain/runtime_qualification.go`、`runtime_admission.go` 及相应 tests；串行修改 runtime.go/init/scope、orchestration.go 共同 submit/claim helper、acceptance.go、changes.go 的新 mode-aware helper、artifact_uses_proof.go 的 scoped provenance、store.go/context.go/workbench.go/http.go 的 typed relation。`contracts.go` operation ownership 仅加 qualifyRuntime；不覆盖 W15/W07 分支。新增三表 migration 可分 S1 两表、S2 dispatch 表，但编号由根 Agent 分配。冻结 OpenAPI/schema 不改。

S2 owner 新建 `internal/domain/runtime_coordinator.go`、`adapters/runtime/bridge_windows.go` 及 native fixture；修改 apps/control/main.go、ops/runtime/main.go、adapters/runtime/runtime_windows.go/process_windows.go、ops/experiment_sandbox/sandbox_windows.go 与平台 stub、durability.go、budget_scopes.go、resources.go。需要异步 sandbox 的新文件可放原 package，保持 W10/W16 API 兼容。共享 helpers/hooks 逐个串行整合，最多两个施工 worktree。`ops/supervisor/fixture_windows.go` 的 fixtureHost 不取得 LIVE 权限。

## 7. 必须验证的行为

开发测试只在新建临时 DB、无密钥 staging 与原生测试程序执行；使用 frozen public HTTP route/schema/headers 验证可达性，不能只直接调用内部方法。runner 必须报告非零断言、具体命令/exit/raw receipts，selectors 无匹配视为失败。

| 验证组 | 最低断言 |
| --- | --- |
| S1 public qualification | exact accepted runtime qualification receipt 可通过；普通 Task/W11 ID/duplicate/cross-project/wrong profile/篡改 bytes/过期/撤销 verifier/同 root/旧 revision/缺 idempotency/假 resume 分别拒绝；reader 可见性按正确实体类型 |
| bootstrap | 无 marker 的同名 Task 无 bypass；冻结合同、空依赖快照、RUNNING、并发/预算均具备；不能给普通 LIVE claim 放行；失败整个事务回滚 |
| mode 与独立接受 | fixture 仍 FIXTURE；mode 从 host binding 获取；caller 写 LIVE 不产生 LIVE；最终重查期间撤销、输入/contract/profile/epoch 改动会拒绝；W11/W15既有语义无回归 |
| native permission | 真 AppContainer 下写 host gate/DB/凭据哨兵失败，input 只读/output 有界；网络、任意继承句柄、越界/reparse 输出、spawn child 被限制；raw receipts 证明边界，不依赖 child 自报 |
| complete mechanism | public submit/claim/heartbeat/seal/report/accept 的完整 normal fixture flow，经新协调器及可信 bridge；一次 native 执行、独立接受、exact artifact/hash、已有资源/预算表记录 |
| effect 与恢复 | crash 注入上述各窗口；新 process reopen 同一临时 DB，旧 effect UNKNOWN 不再发；kill-on-close/timeout/heartbeat expiry/睡眠唤醒处理；late cost 归旧 epoch，丢 ACK 幂等 |
| restart exclusion | 两 control 竞争同一 data root 只有一个持锁；same dispatch 不 launch 两次；PID reuse 不能误认进程；recovery-ingest 不允许 HTTP 伪造/启动/越 epoch |
| remaining LIVE gate | 无真实当前资格的 LIVE claim/replacement/resume/accept 明确失败；真实 Codex policy blocked 状态保持，A04/W05G02/W06G03 不 PASS |

新 coordinator 的 fixture end-to-end 证明控制机制；即使运行真实 native exe，也不自动成为生产模型 LIVE 资格。可为无 provider 的明确 offline profile 增加真实限定能力资格，但不得把这项结果换名为 Codex 工具资格。本设计不授权这次进行任何实际运行。

## 8. 两个连续施工切片与完成判据

**S1：qualification bootstrap + frozen qualifyRuntime。** 授权产品代码、临时 DB migration、public HTTP 与原生无密钥夹具测试；不激活主 `.local/data`，不启动真实模型、生产服务、protected broker、真实网络工具，不修改权限以绕过策略。完成：引导无死锁且不越权，accepted qualification receipt 绑定和 resolver 消歧成立，endpoint 冻结合同一致，所有负例拒绝，提交可独立审查的 source commit/raw receipts。由独立 Verifier 审查后才授权 S2 接入普通 LIVE 分支；接口完成不能写真实资格通过。

**S2：single coordinator + production boundary + lifecycle/effect/reconcile。** 在 S1 接受基础上施工唯一 control loop、manifest dispatch、W10 sandbox async bridge、heartbeat/seal/report、effect/cost、current-use/replacement/resume、旧终态可信导入。完成：新的协调机制经过完整 native fixture 运行、独立接受和重启断言；无第二队列、无未资格 LIVE 放行、无 UNKNOWN 重发、无凭据进入 child、无 host 写权限泄漏。独立 Verifier 对 source/native receipts 作结论；实际安装/启用服务、迁移既有 authority DB、真正 Codex 工具资格仍须单独满足现有授权和 policy，不属于此次设计或 fixture 通过的隐含结果。

持续冻结：`RQ-W05-CLI-POLICY-001` 两次拒绝不重试；主 schema14 activation 的 policy block 不触碰；protected broker 79136 保持 30 calls，不重启/不调用。没有任何 A04/W05G02/W06G03 状态更新。本次证据仅为源码阅读与设计文件的结构一致性检查。
