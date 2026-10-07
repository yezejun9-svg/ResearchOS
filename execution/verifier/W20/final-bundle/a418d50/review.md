# a418d50 最终开发包独立复核

结论：`PASS_BOUNDED_DEVELOPMENT_FIXTURE_ONLY`。既有 `tests/release/check.py --run-fixture` 仅执行一次，真实 OS exit=0，28 项检查 PASS。没有重跑旧 native/private/provider、完整 42 例或被阻止的分支。此结论不接受 A15、W20 全阶段、W21-G01/G02 或完整产品交付。

## 精确包与执行

- 源码：`a418d503f29646f62010905f9dc9338630aa0108`。
- 两份 ZIP：`.local/researchos-development-a418d50-a.zip` 与 `-b.zip`，均为 43,197,438 bytes，SHA-256 `dc90caedd5287bcd718c76bc8e0e2189cf3b33c92a547b6d9fe71d3564f8a193`。
- 514 个 ZIP entries、513 个 manifest 文件逐字节相同且哈希/大小全部匹配；release manifest SHA-256 `9ca7d9630aecdb1c3a323717792b9a712a3b0a8bf212f2ddd5a4c1678e159d61`。
- 独立执行：`2026-09-30T22:53:38.095905+00:00` 至 `22:54:01.863417+00:00`。完整 argv/cwd 在 `command.json`，先保存 stdout/stderr 和真实退出码，再解析报告。
- 460 个观察源文件与 source commit 匹配；源码、检查脚本、工具、两个 ZIP、manifest、SBOM 的 before/after 全部相同。该清单用于本次包/检查绑定，不声称整个产品传递依赖闭包。

28 项覆盖 ZIP 唯一/排序/路径安全、精确 allowlist、每文件 hash、schema20 有界升级声明、未授权 activation/未绑定命令、篡改/缺合同/额外文件/路径逃逸拒绝，以及两套全新临时 loopback 实例的启动、健康、实例身份、错误 PID/创建时间停止拒绝、正确停止和数据保留。最后未绑定 `release.reproduce` 仍返回非零 NOT_IMPLEMENTED。脚本自己建立和清理临时目录；未操作原实例、旧数据或原 PID。

原始 stdout SHA-256 `802beffc7cd0be6ea55c98ff5f15abd7c31c3078d82f1415164ffce60580dfcd`，stderr 为空。`exit.json` 保留真实 exit=0；`check-result.json` 保留全部 28 个原检查 ID。根双构建 exit=0/0 为已保存作者记录；本复核重新检查双 ZIP 和清单，未另行构建。

## C05 与新文档事实

C05 的 12 个 source 文件在包 source commit 上精确保持，9 份公开 raw 与 root integration 清单相同；独立 review hash 为 `84f6c7532d14e22923be37b45c3442fae07b6d3dad416661cff5b6560e5bc5a0`。复用原 C05 8 断言和最终 matrix 21 子测试，不再执行 C05。原 aggregate FAIL、null==null 稳定 Release 限制、work-only predicate 仅源码隔离依据、五项旧 R02 PASS 的 11 文件漂移限制均保留，不签完整 C05/W08/来源 LIVE 资格。

`docs/handoff/current-construction.md` 和 `release/outcome_report.json` 的 34/6/1/1 历史 case、7/15 WBS、费用/真实 Outcome 为 null、Jev FAILED/ADVISORY/NONE、真实冻结/手机/隔夜/干净 Windows 未接受等表述，与记录一致。Outcome 已打入 ZIP 且字节相同；handoff 文档是源码侧入口，不在既有包 allowlist 内。两者引用的完整施工证据位于外部源码 checkout，不承诺 ZIP 内具有这些路径。

包内 `control.exe` SHA-256 为 `b667c45bef91508df9c02f16ad91138762bcb0cbf30a481c998e71cc8194c8eb`；它不是旧 current-control 审查所绑定的 `203fe4d5208de7c571392b345ec580e007ec3713799a8d2042e921393dcae14c`。旧 `historical currentAtSEAL`、持久化合成复算和 NO_GAIN 不转移为新二进制的 now-current proof。当前 owner 仍 UNVERIFIED_STOPPED，正常发布、恢复新代授权和不同 build 切换回滚仍未接受。

## 保留缺口

许可证两缺口、clean Windows A15、真实独立服务身份、原有权威数据 activation、W18 完整当前恢复资格、物理设备/休眠/隔夜及完整当前 42 例均未清除。未用新 fixture 通过覆盖 UI 的五次 FAIL、R03 fixture 失败、R05 未知退出码或其他历史失败。本审查没有修改 canonical/spec/既有证据。

W21 预备索引原 8 个输出及其 manifest 保持字节不变；只新增 `final-supplement.json` 与独立 supplement manifest，记录 C05 和本包的最终定位，不重新制作 42/22 索引。
