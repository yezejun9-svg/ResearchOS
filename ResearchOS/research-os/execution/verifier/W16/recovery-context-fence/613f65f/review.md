# W16 recovery context/fence 第一片：独立审查

**NEEDS_WORK：两个已复现的阻断缺陷，另有一个静态路径写入顺序问题。不签 bounded first-slice PASS。**

冻结源码 `613f65f95f60311a0d938d7c30b1aa1b90c2fb8e`，证据提交 `a86a7330a1f739ebeaf1438a1021144eb24146ef`。作者 worktree 在审查前后均 clean。9 个源码文件的实际字节 SHA256 与 Git blob 均匹配 sourcehash；作者最终 raw SHA256 为 `7df071c0e665140093239f421c6431befd3d039800c069585c615a3cfbc05430`，独立解析确认 8 个 top-level、31 个含 subtest 的 PASS 事件，0 fail；release_host 仅编译、没有选中测试。

## 阻断发现

### P1-01：RestoreContext 指针别名绕过 journal 的不可变检查

- 源码：`ops/supervisor/release_journal_windows.go:167` 的 `State()`、218 行起的 `Append()`、248 行起的 `restoreContextTransition()`。
- 触发：context 已绑定后，`next := j.State()`，然后修改 `next.RestoreContext.ContextSHA256` 并调用 `j.Append(next)`。`State()` 返回浅拷贝，`Append()` 保存的也仍是调用方传入指针，修改已经提前改变 `j.last.State.RestoreContext`。transition 比较两边看到同一份新值，因而通过。直接修改原先传给 Append 的指针也有同类问题。
- 实际证据：`TestIndependentRecoveryContextStateAlias` 同时观察到尚未 Append 时 committed 内存引用已改变，以及 Append 返回 nil 接受替换。这是公共合成 journal，无进程、无恢复、无真实 context 数据。
- 影响：当前进程可以越过新片声称的 immutable binding，并追加与旧磁盘 context 不一致的新条目；重载时的严格 transition 可使该 journal 无法再打开。不能把只读 State 调用者当作内部持久状态的 owner。作者原测试在修改前主动复制了 `*RestoreContext`，恰好未覆盖这个别名入口。
- 最低修正：State 对外返回独立副本，Append/其他保存入口先复制输入；覆盖 RestoreContext，并同样处理影响绑定的 Cutover、AdmissionBundle 和嵌套 slice/RawMessage 等引用字段。保持旧 JSON 字段序与 nil/omitempty 编码不变。补对读取返回值、Append 原输入的修改测试；不要只加强比较条件。

### P1-02：typed context 的 manifest 绑定没有覆盖实际 manifest 文件

- 源码：`internal/domain/evolution_release_recovery_windows.go:47,137` 与 `ops/supervisor/release_journal_windows.go:358` 的 `ValidateReleaseRestoreResult()`。
- 触发：公共合成恢复成功后，修改 `Cutover.Directory/manifest.json` 的实际文件，然后在不改 result/state 的条件下再次 Validate。
- 实际证据：`TestIndependentRecoveryContextManifestBytes/reencoded` 给原 manifest 增加 JSON 空白，`/invalid` 将文件改为 `{}`；两次 `ValidateReleaseRestoreResult` 都返回 nil。报告/DB/native identity 仍保持原值。
- 原因：创建时 `ManifestSHA256` 沿用对已解析 BackupManifest 重编码的历史语义摘要；typed context 只保存该摘要。Validate 只比较 context/result/state 三处登记值，实际读取和重新 hash 的文件只有 source DB、destination DB、restore report，没有 source manifest。作者“manifest tamper”测试修改的是 state 字段，而非持久文件。
- 影响：当前 validator 无法证明 typed restore 所引用的实际 manifest 仍存在且未变；连无效文件也被宣布绑定有效。该发现不表示恢复数据被重新执行或 release 已获授权，Start fence 仍有效。
- 最低修正：保留历史 canonical `ManifestSHA256` 合同，另给新的 typed context 增加 manifest 的固定 locator/native identity 和原始字节 hash；从实际读到并验证过的同一文件捕获，在 restore 前后以及 Validate/Bind/revisit 时核对。不要通过改变旧 canonical digest 算法破坏旧 journal/backup 兼容。

## 静态路径问题

### P2-03：校验 recovery 目录身份前先执行 MkdirAll

位置：`internal/domain/evolution_release_recovery_windows.go:62–66`。如果 `release-state/recoveries` 已是指向其他目录的父级 alias/junction，`os.MkdirAll(directory)` 会先经该 alias 创建 operation 子目录，随后 `ObserveRestorePath(directory,true)` 才拒绝。虽然此处尚未写入 DB/context，仍违反“写入前确定目标归属”的边界。

最低修正：从已经可信且确认身份的 host/release-state 根逐级校验现有父目录，再创建缺失层级并核对新目录；不可先对整条尚未信任路径 MkdirAll。

补充公共临时目录 check `TestIndependentRecoveryContextWriteBeforePathTrust` 因 Windows 创建 symlink 权限不足而 **SKIP**，未到达 restore 调用，未复现越界目录创建。这里的结论来自源码顺序，不把 package exit 0 当作该检查 PASS；没有提权或尝试绕过权限。

## 其他已检查边界

| 要求 | 审查结果与限制 |
| --- | --- |
| 原根和目的根绑定 | RestoreContextPaths 按 operation 固定唯一 destination；lease 必须持有原 data root。source/dest DB 与 report 均有 native file ID 和实际文件 hash，替换同字节文件会失败。context 文件自身按原始字节 hash 读取；manifest 缺口见 P1-02。 |
| 不授予恢复启动权限 | actual-control host 选择 RestoreWithContext；typed callback 有错误直接返回，不回落旧 Restore。成功 Bind 后仍返回 BLOCKED_RECOVERY_AUTHORIZATION。Start 在映像查找/启动前检查 bound context 并拒绝。 |
| journal 状态 | Bind 保持 Data 为原根，PID/creation/image 清空、Phase=RECOVERING；validRestoreResult 不许 bound context 成为活动 slot。transition 在 Append/load 上存在，但内存 alias 使 Append 不可靠，见 P1-01。 |
| operation/epoch 连续性 | Rollback 在 Compatible 成功和失败后都刷新 actual driver 的 journal，先核同 operation/epoch，避免旧局部值覆盖新 context。正常串行 host 路线可见；并发安全未作额外宣称。 |
| 单次尝试与 ACK UNKNOWN | destination 名固定；attempt.json 使用 O_EXCL 并 fsync。已有 destination 或 attempt 返回 BLOCKED_RESTORE_OUTCOME_UNKNOWN。未绑定 context 不回收/重试，已绑定 context 只校验并保持授权关闭。未发现 typed→legacy fallback。 |
| 业务 fence | idle guard 拒绝活动 Run 与 PREPARED/STARTED/UNKNOWN effect；restore 前冻结完整表行，普通恢复只许 credential 撤销、retrieval root 移位和空 barrier 表；slot CAS 只把 STABLE 改成 RECOVERING，epoch/stable/active、DISPATCHED ledger、EVALUATING candidate 不变。 |
| 失败发布 | guard 失败发生在 generic restore 的 staging rename 前，临时副本被清理。restore 完成后 context/bind 失败可能留下 inactive fenced destination 与 attempt，此时拒绝第二次 restore；本片未声称自动修复这种 UNKNOWN。 |
| report actual bytes | 重新读取实际 restore-report 文件并验证 hash、解码后与实际返回值一致；Validate 再检查文件 identity/hash 与 before/after inventory。没有用新造 report 替代原始持久 bytes。 |
| 旧路径兼容 | RestoreContext 为尾部 omitempty 字段，nil 时旧 encoding/entryHash 保持；legacy synthetic Restore callback 仍保留。不是对 production typed 路径使用 legacy fallback 的许可。 |
| 边界未覆盖 | 原真实 cutover guards、当前 actor/proof、非空 retrieval root 的正向搬迁、实际 control child recovery、normal gain、current generation、SCM 或 W18 正式资格均不在此次接受范围。 |

## 独立执行记录

只通过 Go overlay 添加审查目录中的测试，没有修改作者源码。第一条命令精确选择两个新 top-level 测试（另含两个 manifest subtest），Go exit 1，四个 test fail 事件均为上述规范拒绝断言失败。raw SHA256：`1ab95ce05c42dbc54737b97578e7932516244297f91b6286f8f4d9792ea3d3e2`。原始日志、命令、overlay、测试源码与冻结核对分别保留为 `independent.raw.jsonl`、`independent-command.json`、`overlay.json`、`independent_*_windows_test.go`、`source-and-raw-binding.json`。

第二条仅路径顺序 check，test SKIP、package PASS/exit 0，详见 `path-independent.raw.jsonl` 与 `path-independent-command.json`。未重新运行作者 31 项矩阵，没有运行任何旧 native/private helper、旧 PID、真实 schema13、CLI、provider、activation、SOURCE 或 S2；临时 fixture 由 Go testing 清理。

修正后只需要复验这几个新增边界及受改动影响的 journal 兼容检查，再对冻结 delta 独立审查。本报告不能提升任何更广的 release/recovery 资格。
