# W16 current-control 独立审查

结论：`PASS_IN_SCOPE_PERSISTED_SYNTHETIC_RECOMPUTATION`。本次未发现阻断该受限结论的新问题。原预审 B0→G0 authority/readset 缺口已在固定源码中修正，并从原快照独立重算通过。此结论仅接受新合成夹具的持久化证据、数据变化规则和结果推导；不签 full formal A16、SCM、LIVE、W18、G2 或正常发布授权。

`historical currentAtSEAL` 不等于 `now-current`。保存的 SEAL 回复声明 current=true；执行进程随后停止。审查没有启动服务、探测旧 PID 或重演原生执行，无法独立重验原 OS 执行事件真实性，标记 `UNVERIFIED`。当前 owner 资格标记 `UNVERIFIED_STOPPED`，不得映射成 PASS。

## 固定边界与来源

- 作者 WT：`.local/worktrees/control-business-proof`，源码 `36956330065ef7dc9e91005850ee19e1dea69a48`，证据 HEAD `5c6d274a91f9f13d11e880a037133d1246f31811`，审查时 clean。
- 实际执行 HEAD 为 `34f9c0dd21ce44d3ba9a61ab519195fd9dfff63d` 且 dirty；没有以后提交替换执行时 HEAD。before/after 3830 文件库存逐项相等；20 个新增源码与 4 个薄通道文件的执行库存、提交 blob、当前文件三方 hash 相等。实际构建库存 206 文件均匹配当前字节。
- 作者 manifest 实际覆盖 26 个文件，全部复核匹配。这里采用实际枚举数，不把任务描述中的约数视为清单数量。
- 独立读取限定于指定 NEW Canary（OpenCanary/Describe/Read）、B0/G0/G1 内存快照及零长度 WAL 的原 DB 内存读副本。未写 private store、未导出 private raw/labels、未启动服务/原生 producer/provider、未调用旧 private helper。所有写入均在本审查目录。

## 独立重算

`readonly_review_test.go` 由 Go overlay 注入固定作者包；只运行 `TestIndependentCurrentPersistedReview`。最后一轮 `readonly-test-04.log` PASS，结果见 `readonly-result.json`。

| 核查项 | 独立结果 |
| --- | --- |
| 最终 private proof | `sha256:52e11691cd7d336868d285bcf403afc5ae26e88d8e8008d4959cfbd209491a9c`，Describe/Read 校验通过 |
| B0/G0/G1 | 每段 4 个有序 chunks；各 chunk、整段 hash、size、session/stage 与数据库 generation 重算匹配 |
| 原 DB | hash `sha256:fa7fb345d40b2b2b9e755c1a39c2c23f8e979b80ff2d676a3c256976fab2b6a8`；generation 等于 G1；审查前后文件 hash 不变 |
| B0→G0 | 369 项具名变化；重算 whitelist 通过；delta `sha256:0abfcbdafe2d166a19a6aaf85834f054270fa12d65e9d8fbfe64c45e1d8e2ebf` |
| G0→G1 | 221 项具名变化；schema、事件/版本与 whitelist 重算通过；delta `sha256:84592a1315e754374d982940e4df1d194bf7d61357b1d6f8d6eeb9bce37f1ae9` |
| authority | 9 张表纳入核对；准备期仅新增当前 executor/task/run 的单一 auth_grants；G0→G1 全部相同；历史 verifier 角色与 authority-root 分离检查通过 |
| EVALUATE | RESERVED、RECORDED 各 1；完整 session/G0/plan/owner/run/epoch journal binding 重算通过 |
| public/private 回执 | 各 2 对，共 8 个 native receipts；纯 CheckControl 重算均 required_passed=true、gain=false；private summary hash 与持久化结果相同 |
| Run/Acceptance/Experiment | execution Receipt、Acceptance Receipt hash 重算；保存对象与原 G1 完全一致；paired metric 与 NO_IMPROVEMENT 重新计算一致 |
| ObserveRuntime | ended=`2026-09-30T21:50:42.630847Z`，等于 8 回执中最大 Finished；recorded_at=`2026-09-30T21:50:44.1763406Z`；session/G0/execution 绑定匹配 |
| EXE/CODE | 实际 image、上传 CODE bytes、protected owner、构建记录均为 `sha256:203fe4d5208de7c571392b345ec580e007ec3713799a8d2042e921393dcae14c` |
| 正常晋升门 | candidate=REJECTED，Experiment=NO_IMPROVEMENT，host 保存状态 STABLE，normal_release_authorized=false |

源码核对 `apps/control/current_control_windows.go:16`：继承的 peer/MAC 通道进入实际 service，检查 listener、持有的 data-root lease、PID/creation/image 与 STABLE snapshot；仅接受 SAMPLE/REGISTER/FREEZE/EVALUATE/SEAL。`internal/domain/evolution_control_current.go:167` 每阶段复核 owner/source，SAMPLE 在 244 行使用固定 recipe 重建并要求字节相等。独立审查校验了构建输入与最终 bytes；没有再运行该重建或原 OS 执行，历史重建执行真实性属于保存证据范围。

准备期 `evolution_control_preparation.go:14/51/69/95` 限定新 Experiment 默认预算、已有 Goal 单次追加 task、精确 authority grant、ContextBundle ImpactLink/version vector 与零 UPPER_BOUND ledger。G0→G1 的 `evolution_control_delta.go:215` 校验所有表变化及具体对象关系。`evolution_control_current_execution.go` 在任何 holdout/public 执行之前提交 reservation；`evolution_control_current_completed.go:11` 从 durable result 返回 SEALED_EXISTING_RESULT，不调用执行路径。ACK 丢失后的未知执行仍拒绝自动重跑；这次保存的完成后重复请求只返回既有结果。没有故障注入 ACK 丢失场景，不能扩大为所有崩溃恢复路径验证。

五个正常 release 动作原门仍关闭，thin channel 没有赋予 release authority。无 gain 的普通门拒绝为预期结果，不是正收益或发布成功。ShutdownFixture 因零成本 RESERVE 未结清而拒绝 drain；保存日志中的定向停止仅是清理，不计 drain/cutover PASS。

## 限制与审查过程

同用户 Canary ACL 不是独立 OS/SCM 身份。独立读取证明保存数据自洽及其符合固定验证规则，不能排除拥有同用户权限的人修改全部证据。B0 前人工创建的合成资料也不构成真实研究/业务价值证明。01–04 仅有部分终端摘录，缺原 DB/完整库存，保持不可重算，不以后续成功追认。

审查脚手架前两次失败分别为未初始化 Contracts 的 nil 引用和错写 authority 表名 `auth_run_grants`；修正为实际 `auth_grants` 后第三次通过，第四次新增 EXE/CODE 与完整 journal binding 断言通过。原日志保留，未把脚手架失败计为产品失败，也未隐藏重试。审查没有重跑作者 native matrix、早期 attempts 或已停止的平台流程。

交付：`public-binding-audit.json`（全部公共 hash 与执行库存绑定）、`readonly-result.json`（仅安全聚合）、overlay 源码及 4 次原始审查日志。父任务仍需按集成后的 source closure 判断复用；本报告不替父任务签最终产品接受。
