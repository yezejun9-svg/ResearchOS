# 父51 r2 定向静态闭环复核

结论：**P1_BLOCKED_STATIC_INTEGRATION**。原两个 APPLIED 误判机制在 r2 的分类器实现中已得到静态修复；但新加 before_dispatch_row 没有同步到 journal 的 BeforeHash 重建，合法 Host commit 会在写 BEGIN 之前被拒绝。因此当前不能给整个 r2 标记 STATIC_FIX_CONFIRMED_PENDING_PHASE2。仍是 Phase1 只读审查，未运行 candidate tests、未签接受，73 项断言不变。

## 输入固定

- C51-R2-SOURCEFREEZE.json：f76ac75feffbbe174c6268f505512a49447296953868f7d914889663c008525a。
- C51-R2-FINAL.json：5a2738da447227dc52af4c44514e560d1850e3f138a2d48ac4034eed511b102c。
- C51-R2-DELTA.patch：2553a14ec3394abf6936736e9c532273165ad93e50e5c6315c58346d610fb758。
- Domain 实现：365df3d753599fa417da91e4a561d0eaed3fc1c62c11061994fb0f23b3ba6a55；Domain tests：e1e4091cdc9867cd1f0421b97f73f92d9d0544b82bf78867bb64d9d621f71c50。
- 两个新文件与控制文件独立复制到 C51-r2-static-snapshot。074 在复制后重验全部51 live文件与r2 freeze一致；其余49文件的 hash 与上一固定快照完全相同。后续只读固定快照，不追随正在修订的源码。

## P1：Domain / journal 的 BeforeHash 输入不一致

r2 Domain 531–534 行在 beforeHash 中加入 dispatch_row。614–616 行 JournalHashes 返回该摘要；未改动的 Host qualification_failure_maintenance_windows.go 305–310 行把它写入 JournalPlan.BeforeHash。

未改动的 qualificationmaintenancejournal/journal_windows.go 79–85 行，重建 before 对象时只有 census/run/state/dispatch/protected/residual，没有 dispatch_row。445–446 行 StartQualification 会在创建 namespace/plan/BEGIN 之前调用此校验并返回 qualification before hash mismatch。readQualification 也使用同一 full-plan 校验。该结果由两个 hash 输入结构的差异可直接确认，无需执行候选代码。

影响：正常 preflight 输出的 r2 FullPlan 不能经过真正 Host→JournalPlan→StartQualification 流程；分类器单包测试通过无法证明 commit/recovery 可达。此项属于既有 PLAN-03/PLAN-08、JRN-01/02 的多层摘要绑定与 journal 完整性，不新增永久断言。

修复要求：同步 journal 的 before 重建，使用相同字段键 dispatch_row 对应 FullPlan 的 before_dispatch_row；不能通过删除 Domain 的 raw-row 绑定或跳过 mismatch 来消除报错。增加来自真实 Domain plan + Host qualificationJournalRaw 的 StartQualification / inspection readback 组合回归，避免测试自行拼一份同时遗漏该字段的 journal fixture。

## 原两处缺口的修复检查

1. Dispatch 全行：r2 539–555 声明全部15列；563–584 在同一 transaction 内读取值，再读取每列 typeof + CAST AS BLOB。1323–1345 从 BeforeDispatchRow 复制 expected，只替换 state、observation_sequence、observation_hash、updated_at、reason 五个许可字段及其对应 cells；其余10列连同类型/字节均参与 reflect.DeepEqual。此前漏验的 worker / identity / journal_locator / manifest / prepared_at 不再被省略。
2. immutable：1223–1228 按 EventEnvelope=1、其他四对象=0 比较精确整数，2/-1 不再与0混同。未扩张数据库写入范围。

绑定检查：BeforeDispatchRow 在 buildHistoricalQualificationPlan 627–630 从当前 transaction 重读；存入完整 plan 后，Apply 路径已有重建整个 plan 的 hash 相等要求。beforeHash 明确绑定此行，外部 full-plan bytes digest 也绑定字段。当前阻断是 journal 重建未同步，而非分类器忽略新字段。

类型与序列化：Cells 中 Type 明确保留 SQLite storage class，Data 为 []byte、JSON 编码为 base64，避免只扫描成 string 时丢掉 TEXT/BLOB 区别。固定 schema 的15列均 NOT NULL；SQL NULL 在第一轮 string/int64 Scan 失败，不能作为成功 APPLIED 值。缺失/零值 cells 与正常实读 cells 不同；5个写入字段的 expected 类型分别设为 text / integer。固定数组按值复制后只替换对应 cell，不修改原计划其余切片。JSON往返与空串字段的稳定性有作者测试覆盖，但未在本轮独立运行。未发现这个定向读取范围内另一项可确认的新分类通过缺口。

## 作者测试实质性

074/075读取新增测试源码，076独立复制并校验 FINAL 所列16份作者recipe/raw/native-exit文件。最新058 recipe仅为：
go test -count=1 ./internal/domain -run ^(TestHistoricalQualificationRecoveryClassificationNineTables|TestHistoricalQualificationPlannedWriter.*)$

作者058 native exit=0，stdout为 package ok；这是作者执行证据，不计作独立测试通过。

- tests 789–800：实际计划 JSON marshal/unmarshal 后仍要求 APPLIED。
- 803–823：分别 UPDATE worker/identity/journal_locator，要求 UNKNOWN，再还原要求 APPLIED。SQL错误会 t.Fatal，没有把 trigger拒绝当作分类器拒绝。
- 825–844：将同字节 worker 改为 BLOB，先查询 typeof(worker)==blob，再使用往返后的 plan 要求 UNKNOWN；还原后 APPLIED。
- 846–870：Artifact immutable 0→2，先要求 RowsAffected==1，再读回2，然后要求 UNKNOWN；还原0后 APPLIED。若 Artifact trigger 拒绝 SQL，测试会直接失败，不能产生伪通过。
- 以上仍不经过 qualificationJournalRaw / StartQualification，解释了为什么新 journal 接线阻断没有被这条作者命令发现。

## 诊断与结论边界

073–076及本次seal捕获均仅执行只读或 own receipts 快照/封存操作；新增 native 非零0、工具错误0。既有 reviewer native 非零累计3保持。旧主报告、九表补查及seals保持原字节。Boot6 mutable实现未读取。

下一版需在原授权51范围内修复 journal binding，生成新精确冻结哈希。届时复核这一接线点；最终 combined57 的实际测试和接受仍由 Root freeze amendment 启动。
