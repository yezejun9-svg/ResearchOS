# T7 failure, whole SQLite inspection and cleanup independent review

**Verdict: APPROVE — 仅接受失败执行、整库只读检查与关闭证据。**

**Decision: FAILED_EXECUTION_WHOLE_SQL_INSPECTION_AND_CLEANUP_COMPONENTS_ACCEPTED**

T7 的 native positive 仍然失败。此结论不接受 positive-replay、Owner、原业务断言、九类场景或 formal/product authority。authority=NONE，formal_acceptance=false。

## Critical Issues

本次失败证据和清理闭合范围内未发现 Critical 问题。

## Important Issues

- **T7-ENV-001（后续 native Source 修复项）：**固定 T7 `internal/domain/native_migration_authority_harness_windows_test.go:332` 只向 backup child 请求传递 SystemRoot/WINDIR；:348 的 broker 进程环境同样只有这两个变量。controller 和 Go harness 本身有隔离 TEMP/TMP，但没有传给 backup 子进程。实际 00-rehearsal.request.json 确认这个环境，:499–501 因 backup exit1 报错。对应 `backup_prepared_abandonment_upgrade.go:386` 调用 `os.MkdirTemp("", ".researchos-backup-stage-")`，实际 stderr 是 `mkdir C:\\Windows\\.researchos-backup-stage-2831620225: Access is denied.`。这些 Source 和实际请求/错误证据支持“隔离临时目录环境未传播导致 rehearsal 失败”的判断；没有额外复现，也不把修复后的成功视为既定事实。**建议：**新的不可变 harness Source 修订应显式传递已验证的隔离 TEMP/TMP（以及确有需要的公开 profile 路径），保留现有环境白名单、冻结程序指纹和生命周期控制；独立审阅并重新编译后，由 Root 运行新的 native case。本审查不修改旧 Source，不启动重试。

## Suggestions

- `early_failure_retained=false` 是 API 按 fixture_public_ref 文件名计算的分支标签。实际引用为 fixture.public.json，因此该标签为 false；06-fixture-retained.ready.json 的 test_failed=true 和实际 exit1 才表示测试结果。后续摘要应继续明确这一区别。

## What's Done Well

- 未把 rehearsal 的非零退出隐藏为 fixture 成功。原始 72-byte stderr、真实 Go FAIL:501、三个进程的 PID/creation time 和退出码全部保留。
- Root 先完成单一 SQLite 只读事务的全表/schema 检查，再通过绑定本次 snapshot 和 inspection 的具体 release approval 释放 fixture。
- 私有 stdin 使用匿名 pipe；receipt 记录写端已关闭、缓冲已清零、PrivateInputPersisted=false。审查仅复制公开收据，没有读取 private 文件。

## Verification Story

### 失败阶段及进程关闭

| 层级 | PID | Creation FILETIME | Actual exit | 关闭证据 |
| --- | ---: | ---: | ---: | --- |
| backup rehearsal | 5276 | 134359787476336016 | 1 | Primary exit、Job idle/active0、handles closed |
| Root Go harness | 28060 | 134359787460741284 | 1 | Primary exit、Job idle/active0、handles closed |
| Root server child | 97888 | 134359787335688469 | 1 | Primary exit、Job idle/active0、handles closed |

三个 Job 均 unnamed/exclusive、kill-on-close、assigned-before-resume，未超时，未使用 termination，也没有 cleanup errors。Go stdout 原字节报告 TestNativeMigrationAuthorityHarness FAIL，指向 :501；controller.closed 明确 harness_test_exit_zero=false、worker_still_alive=false，outer.closed 的 owned_outer_job_closed=true。

精确原始 Root 工具返回：inspect completion acae5a 为 outer0 / ROOT_PYTHON_EXIT=0；release completion 6d2bd2 为 outer0 / ROOT_PYTHON_EXIT=0；serve completion 7bd3e1 为 outer1 / ROOT_PYTHON_EXIT=1。原始请求与返回对象存于复制的 original-tool-io.json，保留工具原有截断。

### 整库检查

已静态审查 pinned API 的 mode=ro、query_only、BEGIN、枚举 sqlite_master 与所有表、按 SQLite storage class 编码每行及排序摘要、rollback 和 data_version 复查路径。Root 实际 inspection 记录：

- 87 张表、296 个 schema objects，schema_migrations 连续 1..23。
- data_version 2→2，primary/WAL 原字节复查未变；native root/database identity 一致。此观察允许既有 writer handles，不声称 DB 在整个生命周期不可变。
- 独立重算 87 张表的 typed-row 摘要为 `sha256:e455fd8f0bc4ce7a467f6e5e88c70c4e76523aa33477eb17b720208d4408f83f`，与 inspection、fixture.public 和 before.rows 一致；87 张表的 columns/row-digest multiset 全部等于 before。
- schema digest 与 fixture.public 一致。expected_baseline_available=false、expected_state_matches=false；仅 schema_migrations 的“应新增一条”比较为 false，符合尚未升级的实际阶段。
- 156 reader entries 和 1 database identity entry 均 verified/final_path_match/closed，无保留句柄或 errors。

本 reviewer 没有执行 SQL 或重新打开数据库。清理后只检查路径存在性：DB、WAL、SHM 与 fixture root 均不存在；数据库 pin 只作历史 inspection 证据，绝不标为当前可读取文件。schema receipt 记录 digest/count，typed-row receipt 记录类型化行摘要，不输出私有行值。

### 来源与 guard 闭合

初始去重 4,124 条引用中 4,123 条不可变文件指纹匹配，1 条 DB 明确标为历史收据。最终闭合资料去重 4,117 条：4,112 条文件指纹匹配、4 条 canonical 标为 server-close 时刻历史观察、1 条已删除 DB 为历史 pin；没有未解释的缺失或漂移。Root 本任务明确给出的 10 个 SHA256/bytes anchors 全部匹配。

13 份 guard observation 均闭合，包含 inspection 同一 reader/DB guard 的重复记录，并非 13 个独立 guard。server child/outer 各4086、controller4085、四次 API 各4086、snapshot4、release7、reader156 与 DB1 的逐项 verified/final_path_match/closed 均成立。没有从后续 CP360 推断早期 canonical 状态；server-close 的四个 canonical refs 保留为当时证据。

Tests reviewed: yes，先核对 native test 与失败调用链，再读固定 API/controller Source 和原始实际收据。Build verified: 未重新编译；固定程序和 compiler inventory 作为引用核验。Security checked: 静态公开输入、审批绑定、private pipe 与 guard/job 关闭范围；未执行 native、model、SQL、sign 或 private 读取。

Root failures 835（T7 actual failure）、836（rg literal glob/OS123）、837（CreateProcess206）原始证据保持完整；835 与旧失败前缀、FULL 1261/25/4 不 reset。本 reviewer 新增 mechanical failures=0。所有新写入都在独立 namespace，未改 canonical、Source、SQL 或任何旧包。FINAL STOP。

