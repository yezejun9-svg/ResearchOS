# M1-02 pause activation admission 独立架构决策复核

结论：`CONDITIONAL_ARCHITECTURE_APPROVAL_REQUIRED_GATES`。同一 Run 的封存暂停点激活可以成为一项范围更窄的新能力；这需要 Root 明确补充施工合同。**不接受仅将 `"resume"` 改成 `"pause-activation"` 来通过当前失败测试。** 当前实现、原生续跑及 M1-02 均未在本复核获接受。

复核为只读，未修改 Source、运行测试、访问产品数据库、调用 API/模型或控制进程。基线与实际字节见 `review-inputs.json`；作者工作树存在未提交实现，复核只对应该快照。作者保留的 `attempt-004-native.log` 明确报 `GATE_FAILED: runtime has no native resume proof`，native exit 对应 FAIL；本复核没有重跑，不能把作者此前暂停证明提升为独立续跑证明。

## 实际合同与分支

`runtime_admission.go:258-381` 中只有 `operation == "resume"` 的特殊检查：`supports_resume != true` 即拒绝。其余共同检查包括运行器 AVAILABLE/current revision、项目、请求 capabilities、精确资格与批准、当前 profile/binding、独立 acceptance/observation/receipt、能力在 plan 与 observation 中、当前 purpose/credential/expiry 快照。旧无资格 fixture 在 294-300 行有 legacy 路径；新能力必须拒绝由它获得执行权限。

`runtime_dispatch.go:130-165` 校验旧 manifest 的 Task/runtime/executor/epoch/context/input/contract、当前 executor grant，重新做 admission，然后逐字段比较 profile、technical identity、资格、permission、credential、expiry 与 capabilities，并检查 context/dependencies。它还有 `qualification_bootstrap` 旁路；新暂停激活不得利用 bootstrap 取得恢复权。该函数自身对 action 没有额外分支，换名会确实避开上面的 resume flag 检查，并非行为等价重构。

`qualifyRuntime` 227-242 行明确要求独立 resume proof，并且当前 S1 对 supports_resume=true 返回未实现；成功资格写 false/null。这是真实能力边界。`HOST_PAUSE_CAPABILITY` 是当前 Host 在实际 init ACK 后写入的进程/输入绑定证据，**它不是独立恢复资格证明，也不能独自把 RuntimeRegistration 提升为支持通用恢复**。新能力可组合已接受 M1-01 的固定构建、当前完整 runtime 资格和该次暂停证据，但完成前仍是候选能力。

已授权 proposal 的 R1/R2 要求所有现有 admission/session/model/tool gates，CP469 只扩展 effect cutoff；作者也确认找不到既有文本允许忽略 supports_resume。因此本意见是建议 Root 授权一个明确的替代证明类别，不声称原合同已经允许。规范 `03_DATA_CONTRACTS.md:159` 不允许运行中重解释旧 receipt；`07_OPERATIONS_AND_EVOLUTION.md:57` 要求恢复前核对当前 context/input，不得把重建宣传为原生会话恢复。

## 实现需要满足的两阶段 gate

1. **首次准备：旧 epoch e。** 使用专用内部 helper，固定用途且不接收客户端可选 operation 字符串。要求 schema25 实际安装、非 legacy fixture/非 qualification bootstrap、完整共同 `currentDispatchAdmission` 通过；要求 exact PAUSED_CONFIRMED intent、当前 pause revision/checkpoint hash、真实 RESUME request key/hash、当前 Owner/远端设备/grants、原 Task/Goal/Run 的允许状态、原 active_run_id、runtime/session/input/context/dependency 仍一致。重载原 `HOST_PAUSE_CAPABILITY` 并核验正文 hash、协议、generation、dispatch/manifest/process identity/epoch、init ACK 和 original_input_hash，不能只校验 hash 长度或只读旧布尔值。
2. **首次准备的原生与事务证据。** 验证 exact durable sealed checkpoint 字节/hash/size、原 Artifact/use/principal、seal/journal receipt、SDK session/queue cut/ledger/watermarks、同一旧进程的可信 NATIVE_STOPPED + children_stopped/streams_drained/cleanup_complete、效果已对账且 UNKNOWN 成本不被清零。CANCEL/restore_fenced 优先，queue generation/e/dispatch 仍精确。写锁与 state/revision CAS 一次性原子完成 e+1、carry/new-use、immutable activation、新 manifest、queue fence 和 request-consumed receipt；所有失败整事务回滚，保留历史。**此时 activation 尚未插入，不能把一个“找不到 activation 就成功”的后继 gate 当作首次证明。**
3. **新 epoch e+1 的 launch/recovery。** 专用 required gate 必须在 schema/activation/intent/receipt 缺失或矛盾时明确拒绝。绑定 same project/Task/Run、previous_epoch=e、epoch=e+1、pause/request、旧 checkpoint 与原 use/new carry-use principal、SDK session/original input、旧/新 dispatch/manifest/generation；重查当前 Owner、公共 admission、session/Goal/CANCEL/restore fence 和当前队列绑定。只在具备完整证据时触发 resumePause；不得 prompt(original)、新建 Run 或把恢复失败退回普通 claim。
4. **提交后恢复。** PREPARED 且无 worker/identity/journal/effect/任何已尝试启动证据时，才可在同一 successor epoch 更换 lease；继续要求完整 required gate 和当前授权，不再次递增 epoch/carry/建 activation。STARTED/UNKNOWN/不明进程不盲重启。实际 restore/init ACK 前不能写 RESUMED；model/tool 累计与消息消费保持单调。

现有 `pauseActivationGate` 610-628 行在 schema 未安装或 activation 不存在时返回 nil，这是普通 dispatch 的“没有暂停激活则不适用”兼容逻辑。它只核对一部分 intent/dispatch/fresh actor，**不能不变地作为上述 required gate**。可保留该可选 gate 服务普通路径，另加“必须存在”的内部 helper；也可以由明确调用方保证 presence 后复用，但必须有负面测试证明缺失绝不落入普通执行。首次准备、RunAdmitted、prepared lease recovery 必须都使用各自完整 gate，不能仅修首个失败调用。

## 原字段与接口意见

- 保留 `RuntimeRegistration.supports_resume=false`、`resume_evidence_ref=null`、原 qualification_ids、profile/technical/config/credential 与 runtime capabilities，不写伪造独立证明，不修改历史 observation/receipt/hash。普通 `resume`、`ResumeCheckpoint`、资格写入与未支持的旧运行器继续按原合同拒绝。
- 保留 Run id、attempt/progress、原 SDK snapshot binding/session/header/cwd/inputHash；只有外层 successor lease_epoch=e+1，新进程 identity 与 lease 正常更新。原 checkpoint epoch 不能就地改写；新 activation 引用旧证明。
- 需要更正的是**策略表述与窄路径可调用条件**，不是把字段值强行改 true：Root 应明确记录“通用 runtime resume 未资格；只有已封存暂停点且具备 exact activation 的能力获准候选施工”。不能把现有 false 在全局重新解释为 true，也不能把 Host pause ACK 写成独立恢复资格。
- 当前不新增公共 schema/enum/API，不扩大已授权 exact16。若选择修改 `runtime_admission.go` 或资格模型，须 Root 先追加确切文件/合同授权；单独 helper 可落在已授权 pause 源文件，但仍须策略授权。最终独立实现复核和原生端到端通过后，才能接受这项新能力；LIVE 与普通 Main/package/schema24 升级另行验证。

## 必要验证（本复核未执行）

普通 resume 在 supports_resume=false 时继续拒绝；原缺资格/撤销/过期/profile/input/purpose/permission/context/dependency 的拒绝保持。新 action 不带 schema25、exact capability、sealed use、STOPPED、activation 或合法 current Owner 必拒；错 generation/input/process/epoch/hash/use principal、legacy fixture/bootstrap、取消/restore fence、重复请求/两路竞争均不得产生额外 epoch/进程/效果。成功用例必须经真实 Host/API/coordinator/AppContainer，证明同 Run e→e+1、原 SDK session、旧 tool/effect 不重做、消息只消费一次。prepared crash recovery 与 STARTED 不明拒绝独立覆盖；保留 attempt-004 及全部失败计数。

正式增量 0，22 个父任务保持 OPEN，0/42 正式接受。该决策不是实现接受，也不是作者自验。
