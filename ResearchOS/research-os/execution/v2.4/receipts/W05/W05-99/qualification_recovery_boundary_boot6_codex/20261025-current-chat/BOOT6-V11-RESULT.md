# C57 boot6 v11: inherited C fixture verification

## 结论

六个 boot6 文件中的生产实现未改动；本轮只修改 `internal/recoveryboundary/boot_windows_test.go` 的测试假设、清理 helper 和新增的自然继承 ACL 用例。C 盘自有夹具根、D 盘自有夹具根的完整 Windows 包测试均退出 0，Linux 交叉构建退出 0。旧 `combined-067-boot` 的退出 1 和 v10 封存继续保留。

`combined-067-boot` 的失败原因可重现为夹具基线差异：其 C 盘临时目录有 208 条 inherited ACE，测试曾硬编码“文件恰有四条、flags 为 0”，并让清理 helper 对 auto-inherited 原始描述符一律调用 NtSet。v11 在自有 C 盘根直接测试生产 `setTargetDescriptor`：临时父目录自然有 208 条 ACE，文件按 Windows 文件继承规则得到 106 条 inherited ACE；安装围栏并从保存的原生 preimage 恢复后，文件的 O/G/control、ACE 顺序和 flags、3,872 字节原生描述符均与原始记录一致。原始 SHA-256 为 `9670edefaf50d6f0353087f05cfff517a271def615cdba2a3ba23a555a9d0a28`，control 为 `0x8404`。

另一个显式构造并读回的 protected no-AI 夹具 control 为 `0x9004`，其原生描述符恢复后逐字节相同。显式 208-ACE 夹具的 7,628 字节原生恢复也通过。修订后的清理 helper 以保存的真实 native preimage 为输入：auto-inherited 分支与生产路径一致使用 `SetSecurityInfo`，no-AI 分支使用 `NtSetSecurityObject`，且清理后比较 SDDL、语义摘要和原生字节。脚本 `FILE_READ_DATA` 拒绝、真实 PE 执行拒绝和 SQLite/WAL 持续可用的 C 盘夹具测试通过。

## 本轮原始记录

| 记录 | 结果 |
| --- | --- |
| `v11-dev-c-natural-01.*` | 退出 0，但过严的“文件至少 200 ACE”条件跳过了测试；文件实际只继承父目录中适用于文件的 ACE。 |
| `v11-dev-c-natural-02.*` | 退出 1，新增测试对临时目录路径未规范化；随后只修正了该测试路径。 |
| `v11-dev-c-natural-03.*` | 自有 C 盘自然继承夹具生产围栏与原始恢复 PASS。 |
| `v11-dev-c-focused-04.*` | C 盘五个针对性原生夹具测试 PASS。 |
| `final-v11-c-inherited-windows-tests.*` | 完整 Windows 两包测试退出 0；仅 helper-process 专用 PE 用例计划性 skip。 |
| `final-v11-d-windows-tests.*` | 完整 Windows 两包测试退出 0；自然继承密集用例因 D 盘父目录 ACE 数不足而计划性 skip。 |
| `final-v11-linux-crossbuild.*` | Linux amd64 交叉构建退出 0。 |
| `final-v11-six-source-manifest.json` | 精确六文件 SHA-256、字节数和行数。 |
| `final-v11-six-new-files.diff` | 原始 Git 字节流拼接的六个新增文件完整补丁。 |
| `final-v11-diff-check.*` | `git apply --cached --check --whitespace=error` 只读检查退出 0，未暂存。 |

这属于源码和自有临时夹具证据。实际官方目标、不同 SID 的特权管理身份、可读取 SACL 的真实 OS 正例、真实 `FullRestart`、实际 C 交易和正式验收仍未执行；正式验收计数为零。没有改动原始 ACL、数据库、重启状态或 VPS。
