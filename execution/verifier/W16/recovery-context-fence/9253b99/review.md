# W16 recovery-context-fence 定向独立复验

结论：`PASS_IN_SCOPE_DELTA`，限定于固定源码的公开合成 storage/journal 修正。原两个 P1 已关闭。P2 的创建前祖先校验顺序已静态修正；动态 symlink 路径测试仍 `SKIP_PERMISSION`，不算 PASS。原 `613f65f` 的 NEEDS_WORK 与全部原失败证据保持不变。

源码 `9253b997a9d79239c0767967aa2e482098d3e73a`，证据 `43f47837e622a9f8ea35af11d712fa05d68ce3c7`，WT `.local/worktrees/recovery-context-fence-fix` 在审查前后 clean。确认只有声明的 5 个改动文件，完整 9 文件库存的实际 SHA256 与 Git blob 全部匹配；11 个证据文件 hash 全部匹配。结果见 `source-and-raw-binding.json`。

## 问题关闭依据

| 原问题 | 修正与独立验证 | 状态 |
| --- | --- | --- |
| P1-01 journal pointer alias | `release_journal_windows.go:168/174/242` 在 State 出口和 Append 入口统一 clone；原 StateAlias 测试通过；6 类可变字段 × 2 边界共 12 子测试通过，重开 journal 后保存字节不受 caller mutation 影响 | CLOSED |
| P1-02 实际 manifest 未绑定 | `evolution_release_recovery_windows.go:43` 获取固定 locator/native file ID 与原始 hash；从同一核对 identity 的 handle 读取，和 authenticated manifest 比对；恢复 hooks 前后及结束再次检查；`release_journal_windows.go:456` Validate/Bind/revisit 重读实际文件 | CLOSED |
| P2-03 MkdirAll 早于路径校验 | `EnsureRestoreDirectory` 在任何 Mkdir 前找到并校验已有 ancestor，逐层建立并核对新目录；OpenReleaseJournal 与恢复目标创建共用；ObserveRestorePath 显式拒绝 reparse point，再核对 handle 最终路径 | STATIC_FIXED / DYNAMIC_ALIAS_UNVERIFIED |

clone 覆盖 `Frozen []string`、`Cutover *ReleaseCutover` 及其 `Purpose json.RawMessage`/`Migrations []int`、`AdmissionBundle *ReleaseAdmission`、`RestoreContext *ReleaseRestoreResult`。后两者没有可由 caller 原地修改的导出嵌套集合；RestoreContext 是轻量结果引用，不是带 inventories 的大 context 对象。nil/空 slice、nil pointer、RawMessage 原始空白保留的 DeepEqual 断言实际通过。旧无 context 的 journal 格式回执已核对，未改变旧序列化字段顺序或哈希语义。新 typed context 缺 manifest identity/raw hash 时关闭式拒绝，不补造历史证据。

实际 manifest 独立检查覆盖等义重编码、无效 JSON、缺文件、相同字节的新文件 identity，以及恢复 before/after hook 中的修改。原 ManifestBytes 规范性测试逐字节复用并通过；新的受影响检查确认 Validate、Bind 和 revisit 都拒绝。旧 `ManifestSHA256` 保留原语义摘要，新 `ManifestRawSHA256` 单独绑定实际文件，未混淆两种 hash。

`release_engine_windows.go:254` 在 Compatible 成功或失败后均先重读 journal，并要求 operation/epoch 与调用前一致，再使用当前状态处理后续分支。原 changed-operation 两分支结果在作者 raw 中通过；本次另写 `TestIndependentRecoveryEpochRefresh`，同 operation 仅改变 epoch，在 success/error 两分支独立通过，验证不会写回旧 epoch。

## 实际复验

`run_review.py` 只通过 overlay 运行原两 P1 检查、原路径检查、上述新 epoch 检查，以及新增 clone/manifest 受影响 checks。未重跑原 NonIdle/StrictDelta 全矩阵。

- 独立实际 exit 0；6 个 top-level PASS、28 个含子测试 PASS 事件、1 个 top-level SKIP、0 fail。
- `TestIndependentRecoveryContextWriteBeforePathTrust` 因 Windows 创建 symlink 权限不足而 SKIP。没有提权或改用其他 alias 绕过；作者 affected 中另一个 alias SKIP 也单列保留。
- 原始输出 `independent.raw.jsonl` SHA256：`7e8ed2fc959e26a69286dbb056c4bee5bd5c44fd03717a79784943d9436d760d`，stderr 为空。完整命令、时间、selector、统计见 `independent-command.json`。
- 作者 affected raw：10 top-level PASS、45 PASS 事件、1 SKIP、0 fail；原 review 重演 raw：2 top-level PASS、4 PASS 事件、1 SKIP、0 fail。这里只把它们作为已核 hash 的作者证据，不替代上面的独立执行。

所有测试使用本变化的公开合成临时 journal/加密备份数据及 stub callback；未启动 actual control/native process，未读取 private/live 数据或旧 helper，未运行 provider/activation/SOURCE/S2。测试临时目录由 Go 清理。只有本审查目录新增文件；未修改作者源码、原报告、canonical、合同、SQL 或规格。

本次不声称抵御同用户恶意并发替换路径；路径创建仍有同用户 TOCTOU 边界。保留 `BLOCKED_RECOVERY_AUTHORIZATION`、idle-only、原 Data/PID=0/RECOVERING、无 Start、无 projection/gain/generation/qualification 的限制。非空 source roots 正向重定位、真实控制进程恢复、current recovery actor/proof 与 full formal A16/W18 尚未接受；正常 release actions 仍关闭。
