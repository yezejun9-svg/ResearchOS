# 父 51 冻结快照静态复核

结论：**发现 1 个 P1 阻断，不能据本次复核签署父 51 / combined57 接受**。发现归入既有 DB-02、DB-05、JRN-01/02 的完整 after-image / recovery 断言，73 项断言不增不减。本轮只读固定源码与测试源码，没有执行 candidate tests，没有修改候选源码、原环境、ACL、数据库、服务或接受状态。

## 输入与固定范围

- C51-PRESEAL.json SHA256：cd99649c24552dbd6394ba97daf04bb835da16170cd02c4ef0808684614b29fb。
- Root verification-r3 SHA256：10c1d90502d081512e708962023a7424b466cb51575628703908f36cc9d9f8bb。
- 独立复制 51 个文件到 C51-static-snapshot；逐项 bytes/SHA256 匹配，并在复制完成时重读全部 51 个源文件，仍相同。055 保存完整命令、raw 与 native exit。
- 下列行号均针对该固定快照。Boot6 未冻结，本轮不复读其实现；ReadBoundaryPlan / OpenCurrentQuiescence / Check / MarkCDurable 的安全保证仍是待 combined57 独立验证的接口假设。
- 这是对指定重点的静态审查，不将作者测试源码、作者预封存或 Root 引用核验当作独立运行证据。

## P1：恢复分类器漏验被排除 dispatch 行的不变字段

位置：

- internal/store/qualification_maintenance_windows.go:313–314：residual census 按 project/run/epoch 排除整条 runtime_dispatches 记录。
- internal/domain/qualification_failure_maintenance_windows.go:1261–1275：exact checker 只读 state、observation_sequence、observation_hash、dispatch_key、manifest_hash、updated_at、reason。
- 同文件 1337–1375：full census 在非 before-image 分支只使用 SchemaSHA256；protected census 不含九个允许表，residual 已跳过该行，最后 exact checker 即决定 APPLIED。
- internal/host/qualification_failure_maintenance_windows.go:437–441、524–567：同 plan replay 采用该 APPLIED 结论；recover 可据此补 DB_COMMITTED_OBSERVED / DURABLE 并调用 MarkCDurable。

触发：从合法提交后的数据库开始，仅改本 operation 的 runtime_dispatches.manifest 原文，保留 manifest_hash 与以上七个字段。该列确实存在，固定测试源码 97–98 行有实际 INSERT；历史核验也在 domain 1429 行读取 dispatch["manifest"]。同理 worker、identity、journal_locator、prepared_at 等未被本次操作许可修改的列没有在 exact checker 内比较。

静态路径推导：整库 SHA 改变不妨碍 APPLIED 分支；schema 未改变，protected 不变，residual 跳过该行，七字段 exact 仍相同，因此不会得到 UNKNOWN。即便所有合法 C 写入都准确，恢复边界也无法区分此额外漂移。这违反完整 after-image 分类要求，可能让不匹配的状态获得 DURABLE。这里未执行构造或变异测试。

建议在现有授权文件内修复：对 dispatch 行逐列构造完整 expected after-image（来自冻结 before-image，只替换 state、observation_sequence、observation_hash、reason、updated_at），或仅从 residual 编码排除这五个允许变更的 cell，保留其余原始列的类型与值。不要只追加少数目前想到的列。增加 manifest / worker / identity / journal_locator / prepared_at 单列漂移应为 UNKNOWN 的针对性回归，并保留正常 APPLIED 与同 plan 0delta 情形。现有 TestHistoricalQualificationRecoveryClassificationNineTables 在 785–790 行仅增加 unrelated outbox 行，尚未覆盖本缺口。

## 其余重点的静态观察

| 既有范围 | 观察与边界 |
|---|---|
| Host early gates / PLAN-01..08 | host 334–365 严格解析输入与 full-plan digest / subject / source；373–409 先查 boundary、subject，再取 ordinary 或 exact-own lease；443–451 在维护 DB opener 前构造并检查 q。C_DURABLE replay 是独立只读分类路径，依赖上述 P1 修复。preflight 无 C BEGIN；首次 commit 在 502–512 重查后 StartQualification，再调用 apply。 |
| schema24 / 九表 / 五版本 | store 23–82 使用 mode=rw，不跑 migrations，核对 schema 1..24、87 tables、WAL/FULL/foreign_keys 与 quick_check。domain 835–889 的显式写入为上传内容、五种 domain object/version/ref、observation、dispatch、outbox、snapshot、marker；Task、ledger 无 put/update。protected 与 residual census 意图覆盖其余事实，但上述 dispatch 漏列使完整恢复证明不成立。 |
| 三摘要 / private proof | boundaryPlanSHA256 与 coreHash / fullPlan file SHA 分开；Core 含 boundary 引用，重建全 plan 的 Hash 必须一致（973–976）；私有 consumer 校验 owner/model/native binding（895–918）；journal full-plan 校验 core/before/after/subject/evidence（journal 52–115）。原 online proof 的 raw upload digest / core hash / request full digest 校验仍在 runtime_qualification_failure_windows.go 904、912 行，未见历史 variant 冒充其 schema。 |
| TX-HOLD | PlanHistoricalQualification 756 与 ApplyHistoricalQualification 949 使用 context.WithoutCancel(ctx)；清理函数 211–216 先同步 Rollback，再 hold.Close；apply 994–997 等 Commit 返回后才标 txFinished。Commit error 路径会在已返回的 Commit 后进入清理。preflight 791 与 apply 991 检查调用 ctx；部分既有内部 SQL helper 无 Context 参数，不能声称每条内部 SQL 都可及时响应取消，但最终 gate 与清理顺序存在。 |
| 对应 driver test | domain tests 381–471 的取消 rollback / commit_error 用阻塞 driver，在实际驱动尚未返回时尝试重命名 source，释放后再检查可改名；测试源码有针对性。本轮未跑，不记测试通过。 |
| lease copy/generation | data_root 18、28–51 共享私有 owner/state；259–268 匹配 owner/generation/root；272–313 区分 legacy 与 maintenance；316–333 拒绝带活跃 borrow 的 Close；384–422 拒绝 stale/kind/generation 不同的释放。 |
| five upgrades / shared namespace | backup source adapter 63–80 接受五类计划，先归一化并 native borrow，common upgradePaths 149–151 复核 source；prepared nested lease 28–48 只消费继承 guard，不关闭 outer owner。journal CheckOrdinary 546–550 检查双 namespace；exact-own 555–615 拒绝另一 namespace pending，并在拿 raw lease 后再次验证 permit。各入口的 gate 顺序已按 062/064/065 静态定位，仍需 Phase2 实际 setup 计数与 native 对抗。 |

上述观察不扩大为“全部无缺陷”或运行接受。原父 51 预封存应保留作为被审查版本；修复须生成新的精确 hash / 预封存，不能覆写本次快照或失败历史。最终 combined57 phase2 仍等待 Root 的精确 freeze amendment。

## 证据与诊断

052–054 为输入定位与预封存读取，055–065 为固定、检索、带行号源码阅读；均保留 recipe/stdout.raw/stderr.raw/result.json，native exit 均 0。本任务另有一次读取 reviewer 自身 read-wrapper 的只读命令，native exit 0；其原始 tool result 位于本 chat（chunk 7b73ce），无独立 stdout/stderr 文件，不把它补记为完整 raw 捕获。它不读取候选源码，不参与 P1 证据。

本任务新增 native 非零 0、工具协议错误 0；先前 reviewer native 非零累计 2 保持，不重置。没有执行测试，所以无测试失败/通过数。所有辅助脚本与快照都是本次复核的审计依据，保留在 own receipts。
