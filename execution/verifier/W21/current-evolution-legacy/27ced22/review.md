# W21 R04 legacy evolution 只读版本核查

结论：**C10 / C12 / C20 当前完整覆盖均为 PARTIAL**。本次完成了要求的只读审查，未发现可据此宣称产品失败的新运行结果；也没有把历史 PASS 自动提升为当前 PASS。没有执行测试、原生子进程、provider、私有重算 helper 或读取私有 payload。

固定产品版本为 `27ced22e73da7631d65bdd6e1844de24dd198065`。C10/C12 历史接受源是 `1768c89ca8a4f2ba4f79240f281c92f3c4683367`，正式回执 `163c0536-0805-4932-81df-d765a88fe57d`；C20 历史接受源是 `7e789b291814828556edd0a1e722d1992205b9f4`，正式回执 `5402da3d-e835-42d6-8b5f-168b941158dc`。这三个历史 PASS 及原冻结预期保持原样。

## 精确 legacy selectors

以下仅记录既有选择器，没有执行。完整 prerequisites、命令归属和断言 ID 见 `selectors.json`，原始已执行 argv 与公共回执见 `historical-commands.json`。

| case / 分支 | 包 | 精确 selector / 命令 |
|---|---|---|
| C10 | `./internal/domain` | `^(TestW16C10)$` |
| C12 | `./internal/domain` | `^(TestW16C12)$` |
| C20 native/private | `./internal/domain` | `^(TestW16C20\|TestW16C20PrivateProofMissing\|TestW16C20PrivateProofTampered\|TestW16C20PrivateVerifierRevoked\|TestW16C20PrivateVerifierGrantRemoved\|TestW16C20PrivateRemoteVerifier)$` |
| C20 Jev 双 rubric 接口 | `./internal/domain` | `^(TestW11C20RubricOnly)$` |
| C20 objective 辅助检查 | `./ops/supervisor` | `^TestObjectiveHoldoutGain$` |
| C20 既有证据审计 | Python | `acceptance.audit` → `ops/ci/acceptance_audit.py` |

C10 的 `test.orchestration` 在 W16/C10 路由直接委派给 `evolution_main`，与 `test.evolution` 使用同一个 TestW16C10，不能误算为另一组覆盖。C20 的 objective 辅助检查不产生 W16 case 断言；Python audit 会访问外部 protected blob 完整性，不能把它当成这次可直接执行的公共检查。

`evoSetupMode` 会编译真实 candidate/stable EXE，`run` 进入 ExecuteEvolutionFixture 与 AppContainer。C12 继续执行退化 canary、加密备份隔离恢复和原 stable 健康检查。C20 native 分支会生成、读回并重算 protected input/labels/proof，再执行丢失、篡改、撤销身份、撤销 grant 与 remote verifier 负向路径。本轮明确停留在源码与公共回执核查。

## 版本差异与真实调用边界

对 99 个明确选取的直接/相关调用文件逐一核对当前字节与目标 Git blob 相等，并与两个历史接受版本比较。该集合包含共享 auth/context/acceptance/experiment/budget、evolution、backup、supervisor、相关测试和 runner；不是已证明的传递依赖闭包。

| 历史 case | 已有文件改变 | 已有文件未变 | 接受后新增 |
|---|---:|---:|---:|
| C10 / C12 | 22 | 21 | 56 |
| C20 | 17 | 35 | 47 |

逐文件旧/current SHA-256、是否曾在原清单中及新增状态见 `source-deltas.json`。`source-current.json` 是当前限定清单，`source-locations.json` 提供关键函数的真实行号与当前函数块 hash。新增数量包含相关测试，不能当作产品行为数量。

关键分支：`evolutionRecordValid` 在 `controlHost(h)` 时进入 `controlRecordValid`，legacy 则重新验证 Pair、private holdout 和实际收益。`ExecuteEvolutionFixture` 在 regression 执行后把公开收益与 holdout gain 共同用于 improved；`actSystemCandidate` 对无 gain 置 REJECTED，control profile 的正向 release 另有关闭门。legacy C12 的 `runEvolutionCanary` 才执行退化指标、ROLLBACK_STARTED、备份恢复、原 stable health 和 slot 还原。新 control 的拒绝结果不能替换这条退化链。

369 current-control 集成清单 24 项中，当前 23 项字节一致；`ops/supervisor/release_host/control_windows.go` 已随 recovery 修复由 `Restore` 改为 `RestoreWithContext` / `RestoreEvolutionCutoverContext`。这说明集成 source closure 存在明确后续变化，不能把原集成清单描述成当前全量一致；该修改也不是当前 C12 完整回退的运行证据。

## 原断言到最新证据

`assertion-map.json` 覆盖 9 项冻结断言，保留原 expected、历史命令/公共 report/raw 定位、最新可复用范围和缺口。公共 invocation、stdout/stderr、report 与匹配 assertion 已核对；未追踪 protected locator。

| 冻结断言 | 最新已有证据可支持的范围 | 当前缺口 |
|---|---|---|
| C10-01 | current-control 准备期部分 authority 表漂移拒绝 | legacy 四类 native 篡改与 baseline/labels/权限/stable 不变的完整矩阵 |
| C10-02 | 当前 R08 self/child/alias 独立性断言；Go test 不得持有 control authority | evolution 伪造回执、自发布完整矩阵 |
| C10-03 | 未找到指定最新证据中的完整对应链 | 独立规则提案、旧评测、新样例与禁止同事务自批 |
| C12-01 | control 无收益拒绝 | 实际退化触发阈值、回退旧 hash 和 stable health |
| C12-02 | control REJECTED | 退化 FROZEN、晋升及重复 canary 拒绝 |
| C12-03 | control 持久化身份/变化绑定 | 退化实际值/阈值、旧新 hash、恢复回执和恢复资格条件 |
| C20-01 | control public/private gain=false、REJECTED | legacy rubric-only/private proof 全矩阵 |
| C20-02 | control snapshot/owner/plan/version 绑定 | 同样本旧/新 rubric 原始分数、输入/结果/模型版本与不可跨尺度增量 |
| C20-03 | control NO_IMPROVEMENT，零收益未改写 | 完整当前 legacy 规则研究结论链 |

## current-control 复用限度

复用 `execution/verifier/W16/current-control-admission/3695633/` 中的公共 review、`readonly-result.json`、`readonly-test-04.log` 和 public-binding audit；相关 hash 与原 manifest 一致。本次没有重新打开 Canary、B0/G0/G1 或原 DB。它们记录的是此前独立重算通过，不能写成本轮再次完成私有重算。

该证据范围仍为 `SYNTHETIC_FIXTURE_PERSISTED_RECOMPUTATION_ONLY`。public/private 各 2 pair 的 `gain=false`、`required_passed=true`、NO_IMPROVEMENT 与 REJECTED 可以复用；它没有构造完整 C20 的同题旧/新 rubric 比较，所以不能替代 C20-02 或整个 C20。`historical currentAtSEAL` 不等于 now-current；owner 仍为 `UNVERIFIED_STOPPED`，历史 native 事件真实性仍为 `UNVERIFIED`。原 drain 被拒绝、定向停止属于清理，也不算 C12 rollback、cutover 或正常发布成功。

本轮不修改产品源码、canonical 状态、原证据或正式 case 接受状态。没有为使结论通过而执行旧流程。后续若需要补全 R04，必须在明确 native/private 前提后另行决定具体边界；本报告仅给出准确 selector 与未闭合范围，不构成执行授权。
