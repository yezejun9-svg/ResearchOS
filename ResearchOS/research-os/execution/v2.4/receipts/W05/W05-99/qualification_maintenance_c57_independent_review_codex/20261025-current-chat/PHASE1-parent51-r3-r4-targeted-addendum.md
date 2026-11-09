# 父51 r3/r4 定向静态补充复核

结论：**STATIC_FIX_CONFIRMED_PENDING_PHASE2**。r3 已闭合 r2 的 Domain.dispatch_row→Host→journal BeforeHash 接线缺口；r4 仅将租约 fixture 的两个调用参数改成已规范化 guard.root/source，与现有两条生产路径一致，未削弱 outer native lease 的生命周期断言。此结论只覆盖本次定向修复；不等于 combined57 接受，也不代表已独立执行候选测试。

## 固定输入与证据

- R3 SOURCEFREEZE：73dd30e430f8c2114b05327df1f4ae28105468f3465c4bbf499c367207b32f5b。
- R3 INCREMENT：d369d5f1fa7e1bced52f0a67b9ac3178a053a406e54c874748c2ba99704b5ca4；DELTA：91a739fec5da60714640ac8167d288a5d21a47d252c17ab5925aeaed7556eab5。
- R4 SOURCEFREEZE：fdb59f3f6385b77b97c58d9fe55d0abb5ed0b2115ffdfedd21f523a6176bdba2。
- R4 INCREMENT：695d80430c5b0bcf15c62525b166709518206b60ef0120361b95a29226ab15c0；DELTA：46ea18918f91d11eb7c9ea041c5e1a7ef4bc2b26f7de6c8ccf75fa6d67b624f7。
- 079 将六份增量控制文件、r3三份变更源码、r4一份变更源码、24份作者recipe/raw/exit引用固定到 C51-r3-r4-static-snapshot，并逐项核验摘要。重新核对全部51文件与 r4 freeze 一致；r2→r3 仅3文件改变，r3→r4 仅1文件改变。其余依赖使用此前固定的 r2 / C51 快照。

## r3 摘要接线已静态闭合

Domain r2 实现仍是365df3d753599fa417da91e4a561d0eaed3fc1c62c11061994fb0f23b3ba6a55。531–534行 beforeHash 使用键 dispatch_row，值为 typed BeforeDispatchRow；614–616行 JournalHashes 返回该摘要。Host 未改动的 qualificationJournalRaw 305–310 行将它写入 JournalPlan.BeforeHash。

r3 journal_windows.go SHA cf1701681f40f27af2f1766faa78d00ee3bcee0c0ea68512f3dbd8c044bd2708，在81行新增同一键 dispatch_row，值取 FullPlan.before_dispatch_row。其余before输入不变。因此原先两端输入结构不一致的问题已修复；并未删除 Domain 绑定或跳过 mismatch 检查。

新增 Host 测试 TestQualificationJournalFullPlanDispatchRowRoundTrip（22–97行）使用真实 domain.HistoricalQualificationPlan 类型，经 JSON 填入 typed dispatch row / cell，再调用真实 qualificationJournalRaw→StartQualification→OpenOwnInspection，要求读回 BEGIN。虽然 plan 数据是合成 fixture、没有运行原始数据库 preflight，但它使用真实 Domain JournalHashes 方法和真实 Host/journal 连接，能直接命中本次曾遗漏字段的接线回归。不是在测试中手工算一对相同且错误的 BeforeHash。

journal 的 TestQualificationJournalFullPlanHashesFailClosed 同时在117行增加 before_dispatch_row 篡改，保持原摘要后要求 StartQualification 拒绝。正反两条源码路径都针对原缺口。

作者061 recipe 的 regex 为 ^(TestQualificationJournal.*|TestQualificationMaintenanceFrozenSubjectAndExternalPlan)$，覆盖新增 Host 测试及 journal hash 测试。其独立核验的 raw 记录两个包 ok、native exit0；新增 Host 测试无 Skip 分支。这里只确认作者证据与代码命中关系，不将其计为 reviewer 执行结果。

## r4 路径修正与生产一致，原断言保留

r4 仅修改 backup_source_lease_windows_test.go（SHA bb1c9b40e5c2c3a736c3b2d11edcbc7071e1d1719b51797ee786319f7ae09cd5）两行：

- 128行 acquirePreparedUpgradeRootLease 使用 guard.root、guard.source；
- 138行 guard.Check 使用同一规范化路径。

生产 checkedBackupSource 在32–47行调用 upgradePath，回写 opt.Source，再建立 root/source guard。prepared-local 在 backup_prepared_abandonment_upgrade.go 415–416行先运行 upgradePaths，再将 filepath.Dir(opt.Source)、opt.Source 送入 nested lease。prepared-handoff 在 backup_prepared_abandonment_handoff.go 180–184行先运行 preparedHandoffPaths（其127–130行规范化 source），再核对 sourceLease 并送入 nested lease。两者都使用已规范化路径。因此 fixture 改用 guard 中的同一规范化结果与真实调用契约一致，未改变生产 identity 检查。

fixture 保留以下检查：inner 初次 Check 成功；inner.Close 成功后 Check 必须失败；outer lease.Held 必须仍为true；guard.Check 继续执行真实 borrow.Check/native guards；os.Rename 原 source 仍必须失败（128–143行）。旧的 wrong-root/source 拒绝测试与其他 lease 测试没有改动。该 fixture 两个 subtest 名称共用同一个 nested helper，不能单凭它宣称两条完整升级流程已经独立运行通过；生产两条规范化链是本次静态核对所得。

作者 combined-065 与070原始失败保留：两者 native exit1，原因均为 UPGRADE_SOURCE_LEASE_IDENTITY。修复后071、073（另一临时路径环境）和074组合命令的原始 exit0均已核验；071/073 stdout 明列两个 subtest PASS。没有删除旧失败或把旧失败记作 reviewer 测试失败。

## 范围与诊断

078–080只读取固定文件、生成 own receipts 快照与核对作者证据；候选测试执行0，Boot6可变代码读取0，候选源码/原环境写入0。本次新增 reviewer native nonzero0，既有累计3保持；工具协议错误0。73项断言与旧报告/seal不变，本文件只追加定向闭环结论，映射既有 PLAN-08 / JRN-01/02 和 C-LD02 / TX-HOLD 的约束。

原 r2 接线阻断在上述新版本中静态闭合；原 r2 报告仍作为历史版本判断保留。下一步等待 Root 的 v11 + combined57 精确冻结及 Phase2 amendment。
