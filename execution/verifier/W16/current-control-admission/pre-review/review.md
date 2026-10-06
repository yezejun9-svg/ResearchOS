# W16 current-control admission：独立只读预审

**结论：NEEDS_WORK；1 个 P1 阻断。源码未冻结，不签最终接受。**

审查作者 worktree `D:/作品集/ResearchOS/research-os/.local/worktrees/control-business-proof` 的当前未提交实现，以及薄通道提交 `f85cf066888d90042d8c1378a95ed29814be07e9`。收尾时作者已将该通道 cherry-pick 为 `34f9c0dd21ce44d3ba9a61ab519195fd9dfff63d`，四个通道文件与已审查版本逐字节一致；domain 实现仍未提交、未冻结，不能称为已运行。具体源码 SHA256、引用行及 Git 状态在 `source-audit.json`，不把 dirty HEAD 当作实现身份。

## 阻断问题

### P1-01：B0→G0 没有具名变化白名单，既有 authority/Issuer/grants 可被重新基线化

位置：`internal/domain/evolution_control_freeze.go` 的 `freezeCurrentControl`（约 162–188 行）及 `controlBusinessReadsetUnchanged`（207 行起）。

触发：SAMPLE 完成后，在 FREEZE 前，修改已有 `auth_principals`、`auth_grants`、`auth_credentials`、`orchestration_identity` 或 `remote_devices` 的行；让最后使用的 owner/verifier/executor/release 在 G0 仍有效且满足当前独立性检查。也可以修改该阶段未被挑选的业务对象或历史版本。

现有校验只比较 `domain_objects` 中 ProjectProfile、ProjectState、少数 policy、SourceCursor 及指定 ResearchCycle，并忽略 ProjectState 的事件计数/修订元数据。随后 `controlRowDifferences` 虽计算全部差异，却逐项无条件赋予 `B0_TO_G0_EXPLICIT_REGISTRATION_AND_PROVISIONING_AUDIT`。没有对这些差异调用白名单校验，也没有把 B0 的既有身份/Issuer/grants 与 G0 精确比较。`deriveNames` 和 `independentVerifier` 读取的是变化后的身份，不能替代跨代绑定。

影响：B0 原始快照与 G0 执行/验收 authority 可以来自不同身份授权状态，却被封装为同一 current-control 证据链。G0→G1 的精确行检查只能锁住已经变化的 G0，无法补回 B0→G0 的连续性。现有测试只证明 G0→G1 的 grant 变化会拒绝，没有覆盖这一前置窗口。

最低修正：在接受 FREEZE 前实施独立的 B0→G0 具名差异校验。默认禁止所有既有 authority/Issuer/grants/credential 行变化或删除；必要的新增 principal、run grant 和业务准备行必须绑定本 session 的明确身份、project、candidate、task、run 及精确字段，并验证版本/事件/引用关系。若 B0 采样前即可完成身份准备，优先把这些准备移到 B0 前，让 authority 表整段保持不变。不要把一个统一 reason 字符串当成允许变化的依据。修正后只需对该窗口的公共合成数据做针对性检查，无需读取私有 LIVE 数据或重跑旧 helper。

## 已确认的静态边界

| 范围 | 源码结论 | 仍需冻结后证据 |
| --- | --- | --- |
| 同一实际服务与私有通道 | 薄通道 `currentControl` 检查 held DataRootLease、实际 listener、ready coordinator、STABLE snapshot、当前 PID/creation/image hash/data root；五阶段走同一 inherited peer/MAC 通道。domain 保存同一 lease 实例并重新观察进程/文件身份。 | 合并后实际服务 owner、listener、source/image hash 与五阶段回执一一绑定。当前没有运行证据。 |
| B0→G0 | 只有有限业务 readset 固定及全量差异记录。 | P1-01 必须修正。 |
| G0→G1 | `validateCurrentRows` 重验 owner 与独立 verifier；`validateNamedDelta` 固定 schema，默认拒绝未知表变化/删除，限定单 candidate/task/run 及允许字段，并检查版本、事件和引用。authority 表不在允许集合。 | 仅补修正范围内的具名准备/生命周期正例和拒绝例。静态审查不证明所有实际准备步骤均能通过。 |
| rebuild/EXE/CODE | SAMPLE 读取批准根中的 source inventory，固定 Go recipe 和离线环境，核对 pinned go.exe hash/version，独立 rebuild 后逐字节比较 CODE；实际自身映像必须为同 hash 的 apps/control。后续阶段再核源码与 owner。 | exact source inventory、工具链、recipe、rebuild hash、CODE hash、实际服务 EXE hash 同一冻结记录；未执行编译。 |
| 私有 B0/G0 | online backup 直接进入内存，原始字节分块进入 CanaryStore；读取时校验 purpose/stage/session/顺序/hash。public snapshot artifact 只有显式投影后的 ordinary research bundle。当前新路径不把原始 DB 写入 ordinary temp 或 uploaded_content。 | 公共合成 sentinel 与文件/产物清单即可验证；不需要打开真实私有 payload。 |
| EVALUATE/ACK | 进程内 `a.evaluating` 在业务 I/O 前单次置位且失败不清除；完成后重复调用只返回已有 observation ref。普通 execution 另有 SQLite 唯一 RESERVED 行。Private 通道连接后只发送一次，无业务自动重发。会话随实际进程消失而不可恢复，现有 host 行阻止在同 project 重新 SAMPLE。 | 不能把进程内 latch 称为持久化 EVALUATE reservation：holdout 发生在普通 execution RESERVED 之前。最终需明确此阶段失联只作 UNKNOWN/检查，不换 session 重跑；只使用允许的合成检查。 |
| ObserveRuntime | 调用前 `controlRecordValid` 重算 public/private 证明；`CheckControl` 逐 RunReceipt 检查 PID/creation/image、exit=0、stopped/drained/cleanup 等。写入 observation 绑定 session、G0、execution、public/native 与 holdout proof hashes，因此不是未经检查的调用者 bool。 | 当前 observation 的 ended 用 `Now()`，没有复制原始 RunReceipt 的完成时间，亦未直接带 streams_drained/cleanup_complete。应明确这是验证后聚合观察时间；若契约要求实际终止时间，需从已校验 receipt 聚合并分别记 recorded_at。若 Run 已有 runtime_dispatches 行，普通 ObserveRuntime 会拒绝，需真实流程证明选定 Run 路径，而不是绕过 coordinator gate。 |
| 无 gain 与 release | SEAL 仅接受 REJECTED、原独立 verifier 的 acceptance、COMPLETED experiment 和 improved=false，proof 显式 normal_release_authorized=false/os_service_qualified=false。五个 FIXTURE_SEAL/CURRENT/DISPATCH/CUTOVER/PROJECT 动作在 drain gate 继续返回 ACTUAL_CONTROL_BEHAVIOR_PROOF_UNAVAILABLE。 | 后续结果只可标 current same-user fixture nongain proof，不代表 normal 晋升、G2 cutover 或 SCM/LIVE 资格。 |

## 下一次独立 delta 的输入

作者修正 P1-01 并冻结合并源码后，提供 exact source commit/inventory、实际 recipe/build/CODE/EXE 绑定以及准许范围内的五阶段原始回执。将每一阶段的 session、owner、B0/G0/G1 hash 与最终无 gain 接受链逐项对账；保留所有失败/UNKNOWN。不要以本预审替代源码冻结或执行接受。

本次只读取本项目源码、Git 和公开合同身份文件，仅写本目录。没有运行测试、编译、服务或 CLI，没有连接旧 PID，没有访问私有 LIVE 数据，没有调用旧 private helper、耗尽的 SOURCE 测试或平台已停止的 S2 审查，也没有修改作者源码、canonical、SQL 或 contracts。
