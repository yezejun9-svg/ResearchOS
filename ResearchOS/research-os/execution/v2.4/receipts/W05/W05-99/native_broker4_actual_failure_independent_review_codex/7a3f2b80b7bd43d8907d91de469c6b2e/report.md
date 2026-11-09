# Native T10 实际失败与夹具存续独立审查

结论：`FAILED_EXECUTION_CLOSURE_CONFIRMED_FIXTURE_LOST_NO_SQL_OR_SPECIFIC_RELEASE`。41/41 项只读事实检查通过，89 个现存公开输入接受 SourceReadGuard 保护；20 处历史 guard 记录与本次 guard 均已验证关闭。这里的“通过”仅指审查事实一致，不表示 Native 正向、Owner、九用例、原 trial、业务或正式验收通过。

## 实际失败

- Native failure ordinal 892 对应一次运行。Go PID 42244，FILETIME 134359866411023123，actual exit 1，elapsed 1200.9577792 秒；outer Python PID 79092，FILETIME 134359866284665514，actual exit 1，elapsed 1213.3352557 秒。
- 两层 owned job 均已 idle，active processes 0，primary exit confirmed，handles closed，无清理错误；`timed_out=false`，`termination_requested=false`。这是约 20 分钟后的自然失败退出。没有证据支持“30 分钟硬杀”。
- 真实 Go stdout 的两处 `Root review window ended context deadline exceeded` 分别位于 grant 等待（626）及 cleanup 等待（468），属于同一 attempt。
- 固定 Go source 第 405 行建立 20 分钟 context；cleanup 第 465 行写出 retained marker 后，第 468 行复用已过期 context 等待 explicit release。第 252–253 行 ctx done 触发 t.Fatal。随后原有 TempDir cleanup 执行，故 ready marker 不能证明当前夹具仍活着。
- Controller helper timeout 为 1260 秒，Go timeout 为 25 分钟；本次都没有触发。

## 签名和夹具

Grant 仅签名一次并成功结束 owned signer job；issued 2026-10-09T02:38:36.7336808Z，expires 2026-10-09T02:42:36.7336808Z。未发现 grant approval publication 或 native apply。先前 initial release 签名及发布已完成，但不是本夹具的 explicit release。

历史 root file ID 为 `ee413c31:00040000:00118352`，database ID 为 `ee413c31:00040000:00118353`，它们与公开 grant binding 一致。本轮仅 stat 精确公开路径：source.sqlite、WAL、SHM、其 003 目录、TestNativeMigrationAuthorityHarness3100897094 父目录，以及 rehearsal Snapshot/Destination/SourceRoot/TargetRoot 均已不存在。没有重新打开 DB 或测得当前 File ID；没有 stat 或读取 fixture 私钥文件。

公开 before.rows.json 的 87 张表 digest 仍在，但不能替代失败后的完整 SQL 读取。旧 fixture 已无法作为 SQL 检查或 explicit release 的对象；本轮两项均未接受。后续新用例应保有独立 cleanup 生命周期，使 actual whole SQL 检查和明确 release 能完成。任何另存副本都必须有自己的身份与来源，不能被描述为旧 original fixture。

## 证据与边界

review.json 给出逐项检查；input-pins.json 给出原始公开输入 SHA-256/bytes；historical-owned-jobs.json 保留 exact FILETIME 十进制字符串；fixture-current-state.json 保留当前路径状态；guard-closure.json 与 historical-source-guard-closure-summary.json 保留关闭证据；canonical-short-pins.json 保留审查前后稳定的短 pin。

Root 原始 terminal IO 已逐字节复制为 original-root-terminal-tool-io.json，原文件 SHA-256 42600e84cbebe3619dc120dd51de487acdf8e0813a25f8a1a53e6d04f24a5096，860 bytes，chunk 338949，actual outer exit 1。本审查的 Python 工具回执 chunk 3b676c，exit 0；script 与 wrapper 各输出一次 ROOT_PYTHON_EXIT=0，均已原样保留。

本轮未发起 API/native/Git/Go/model/SQL；未修改 canonical/main、原 trial 或他人文件；没有新本地执行失败。global/original-trial provider requests 无本轮权威来源，保持 unknown。旧预终态 ACTIVE 记录仍为历史证据，不代表当前 live 状态。所有审查动作已停止；仅在新的明确任务下继续。

