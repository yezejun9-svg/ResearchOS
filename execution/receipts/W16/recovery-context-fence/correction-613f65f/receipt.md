# W16 recovery context correction

状态：IMPLEMENTED_DELTA；等待独立审查，不签接受回执。修正 source commit：`9253b997a9d79239c0767967aa2e482098d3e73a`，base：`a86a7330a1f739ebeaf1438a1021144eb24146ef`。

原 source `613f65f95f60311a0d938d7c30b1aa1b90c2fb8e` 的独立结论仍是 NEEDS_WORK；原 evidence `a86a7330a1f739ebeaf1438a1021144eb24146ef` 与原 raw 不覆盖、不重新标为通过。输入报告是 canonical `execution/verifier/W16/recovery-context-fence/613f65f/review.md`，SHA256 `97cc88894b779904247e3e5f617c3d70090b926f682e6fe35eba1283c1deb94b`。

## 修正及范围

P1-01：journal 在 `State()` 出口与 `Append()` 保存入口统一深复制。覆盖 `RestoreContext`、`AdmissionBundle`、`Cutover` 指针，以及 `Frozen`、`Cutover.Migrations`、`Cutover.Purpose` 可变集合。显式 typed clone 保持 nil/空集合区别和 RawMessage 原字节；JSON roundtrip 会压缩 RawMessage，故未用它替换原字节。十二个边界子测试分别修改返回值及原入参，并验证内存状态与重载后的磁盘状态；恢复 context replacement 仍被拒绝。旧 journal 字节/hash 检查仍通过。

调用点静态检查覆盖 supervisor driver、engine、host、receipt 与 domain release adapter 的 State/Append 使用。业务写入均经 Append；`load` 从 JSON 分配独立值，外部输入由 Append 复制后保存；未按 caller 添加绕过或分散的防御条件。未来 ReleaseState 或其嵌套对象新增可变字段时仍须扩展 typed clone。此检查不声称新增并发线程安全。

P1-02：保留旧 `ManifestSHA256` 语义摘要。新的 typed context 另存 manifest 固定 locator、Windows file identity 与实际原始字节 SHA256。原始字节从验证 file ID 的同一文件 handle 读取，与原备份认证流程返回的 BackupManifest 比对；恢复前、恢复 hooks、恢复后、Validate/Bind/revisit 均再次检查实际文件身份/字节。Validate 还核对 purpose、migrations 与 context/state 绑定。重新编码的等义 JSON、`{}`、缺文件及同字节新 file ID 都被拒绝。缺少这组新字段的旧 typed context 会关闭式拒绝，不自动补造证据。

P2-03：新的 `EnsureRestoreDirectory` 先检查已有 ancestor 的 canonical path/native identity，再逐层 Mkdir 并核对新目录；journal 打开及 recovery 目录创建共用它。`ObserveRestorePath` 显式拒绝 reparse-point component，并继续检查 handle 解析后的最终路径。普通缺失目录创建和 file ancestor 拒绝已执行。动态 symlink alias 检查仍因权限不足 SKIP；本次没有提权、尝试其他 alias 创建办法或把 package exit 0 说成此项 PASS。静态顺序修正不声称抵御同用户恶意并发替换目录。

## 本次执行

1. Affected selector：`^TestW16RecoveryContext(Correction.*|FenceEncryptedCopy|TamperMissingAndIdentity|JournalBlockedBeforeStart|LegacyJournalBytes|JournalImmutableFence|CallbackFailureAndLegacy)$`，packages 为 domain、supervisor、release_host，实际 exit 0；10 个 top-level PASS，45 个含子测试 PASS 事件，1 个子测试 SKIP，0 fail。release_host 仅编译，无选中测试。
2. 原 review 检查源码逐字节复制到本目录的 `review-*.go.txt`，通过 `overlay.json` 在新 worktree 原样执行 `^TestIndependentRecoveryContext`，实际 exit 0；StateAlias 与 ManifestBytes 两个 top-level PASS（含子测试共 4 个 PASS 事件），WriteBeforePathTrust 仍 SKIP，0 fail。这是实现者复验原审查输入，不冒充新的独立审查。

两组原始输出分别为 `affected.raw.jsonl`、`review-reproduction.raw.jsonl`；实际退出码另存 `*.exit.txt`，完整命令/环境/时间/统计/输入 hash 见 `commands.json`。source 在这两组执行之后未再改变，先冻结 source commit，再单独提交证据。原始 Windows CRLF 字节保留；证据空白检查使用 `git -c core.whitespace=cr-at-eol diff --cached --check`。

本次没有重跑原 NonIdle/StrictDelta 全矩阵，也没有重跑旧 native/private/helper/CLI/provider/activation/SOURCE/S2。没有操作 protected PID 79136、live PID 32736、schema13 或实际服务。只执行新增修正与受影响的公开 synthetic storage/journal 检查；路径 SKIP 单列。

`BLOCKED_RECOVERY_AUTHORIZATION`、idle-only、原 Data/PID=0/RECOVERING、无 Start、无 projection/gain/generation/qualification 的边界保持。actual release actions 仍关闭。非空来源目录重定位正向分支、实际控制进程恢复、当前 recovery actor/proof 均不在本次验收范围。
