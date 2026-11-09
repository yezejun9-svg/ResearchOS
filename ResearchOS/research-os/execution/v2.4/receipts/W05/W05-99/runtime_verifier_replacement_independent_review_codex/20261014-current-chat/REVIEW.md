# 独立 Source 复核：CHANGES_REQUIRED

候选 `c5ea30829800a75badc07cfc25b01c0822e787c9` / tree `6d1dd6b5475de3435539c5d457affa3370696b95`，base `c8b7adab9f0c15eb33f235f8d0d9eb205794e376`。exact8、scope、source.patch、architecture、作者 FINAL-manifest 与其 41 项 source/receipt/tool/binary 引用均独立核对。649 个当前 sparse 工作树 tracked build inputs 共 7,789,812 bytes 已设前后 source guard。未改 Source/Main/checkpoint；以下复核在 reviewer 自有临时隔离 fixtures 中完成。

## 必修问题

### F1 [P2] 不应以墙钟字符串决定事务合法性与先后

位置：`internal/host/runtime_verifier_replacement_journal_windows.go:198`、`:486`（相关 `:489-502`）。

`replacementReadJournal` 直接比较 `event.At < last.At`。RFC3339Nano 会去掉末尾零，因此真实递增的 `2026-10-14T02:00:00.1Z` → `.11Z` → `.12Z`，字符串顺序却会把第二条判成倒退。独立 probe 使用三个可由 Go 的正常格式化器产生且严格递增的时间、重算有效 event hashes/previous chain，startup gate 与 recover inspect 均返回 `event time regressed`。原追加路径先将事件持久化，再 readJournal 验证，因此正常运行一旦跨到该格式边界，会留下 read/recover 都拒绝的 immutable 日志。

另一个 probe 模拟第一条已提交事务发生后系统时钟向后校正，再正常执行已授权的反向事务：两个 commit 都成功 APPLIED，但 startup gate 按 terminal.At 排序后返回 `latest replacement registration drift`，导致正常产品无法启动。此 probe 没有修改机器时钟；只在自有 fixture 的第一条已提交事件链中写入一组有效未来审计时间并重算哈希，模拟其真实可能的历史，然后通过原实现完成第二条事务。

建议用持久化 predecessor/head digest 或等效确定的因果顺序绑定整个 operation 历史，并用事件 sequence/previous/hash 验证内部链；At 只作审计。仅将字符串改为 time.Parse 仍不能解决系统墙钟回退的跨事务排序问题。不得用删除/覆写旧事件修复，也不应允许提交成功后才发现所产生的历史无法正常启动。

### F2 [P2] 同时脱离 lineage 与 grant 的既有 child 被 all-child census 漏掉

位置：`internal/host/runtime_verifier_replacement_windows.go:364`、`:387`。

`belongs` 只依据现存 root/parent 与从现存 grant 推导的 child ID。独立 fixture 具有 project-a/project-b 两个已注册 child；把 project-b child 的 root 与 parent 均改为 foreign，再删除其 grant，原 auth_principals child 行仍存在。此时该 child 被 `if !belongs { continue }` 忽略，preflight 实际返回 PREFLIGHT、NOT_APPLIED、四项 census 全 0。这违反 exact scope 要求的全部既有 child lineage/grants 漂移拒绝，也超过注释“detached or reparented service child cannot disappear”的实际能力。

建议在归属过滤前校验保留的 `local-verifier-<derived-id>` 命名空间中现有 child 的 lineage/grants 完整性；对缺失或非法归属 fail closed，不能把无法归属的 reserved child 静默跳过。可在本次新 host 实现/测试文件内修复，不需改 domain schema 或扩大生产业务权限。需补“只删 grant”“只删 lineage”“两者同时移除/改走”和多个 child 的负例；保持合法其他 service-root 的边界可解释。

## 新鲜独立执行证据

- `01-independent-focused`: 真正 `go test ./internal/host ./apps/control -run ^TestRuntimeVerifierReplacement -count=1 -json`，native exit 0；11 个 top-level PASS，含子测试 68 PASS、1 SKIP。保留 foreign-owner 的 WRITE_OWNER 限制，未将其记作通过。
- 以上包含 8 个实际 Windows 子进程 kill 边界（每个 child native exit 1）、11 次实际编译后的 control CLI 调用、原 mismatch 拒绝、reverse、readonly WAL 观察、全局 census、ACL/reparse/hardlink、实际 ReplaceFile race UNKNOWN、startup gate before store.Open。
- `02-independent-adversarial`: reviewer 自有 Go overlay 追加测试，不写候选源码；3 个 top-level FAIL，native exit 1。两个时间 probe 对应 F1，一个 grantless detached child probe 对应 F2。日志 SHA256 `52781625cc4e2a1ab2220b1bdce3b6dfb91ec23c564d1924db30b92c98a08fa7`。probe 与 overlay 均在本证据目录。
- 所有实际 argv、cwd、完整 allowlist env、数值 exit、开始结束时间、stdout 日志 digest 均在对应 JSON 与 append-only attempt-ledger.jsonl。GOPROXY/GOSUMDB=off；没有模型/网络 provider 配置传入测试进程。
- 初始只读诊断失误保存在 reviewer-diagnostics.json：PowerShell 未引号的 HEAD^{tree} 解释问题、可选作者报告文件名误猜，以及首次 evidence mkdir 缺 parent。没有重置或隐藏这些失败。

## 已确认设计与剩余边界

main() 新早分支真实位于正常 flag/DB/Host/监听器之前；正常启动 gate 在相同 DataRootLease 后、store.Open 前。原 ensureRuntimeVerifier 未修改。安装注册采用精确 old bytes hash 与 canonical record/installation hash 分离；真正 ReplaceFile 实际 backup 核对、当前记录读回、私有不可变事件、recover 不重放、反向新事务均有新鲜 fixture 证据。只读连接使用 mode=ro/query_only 与 BEGIN/ROLLBACK；没有新增 migration/credential/provider/HTTP/Native3/renderer 入口。

包装注意（非本次独立确认的运行时缺陷）：`replacementRead` 对 exe 也强制 current-SID owner/protected single-ACE；这比原 LoadRuntimeVerifierInstallation 的文件字节合同更严格。Root 后续实际新包必须显式满足并独立读回该 ACL，不能从 manifest 的 ACL 合格推断 exe 合格。本轮未读取产品 DataRoot 或实际安装包 ACL，因此不宣称当前产品包已经满足。

作者已冻结的 SUMMARY 保留了 7 个 legacy Mu synthetic leaf 失败（此前拿到的资产 build metadata 不匹配），其后补充修复证据不在本次冻结作者 manifest 内；本报告不提前把它们转成 PASS。foreign-owner native token 边界仍有明确 SKIP。现有 8 个 crash 点是实际进程终止证明，不覆盖机器断电/存储硬件持久性，也未证明任意 partial temp/orphan 都可自动恢复；歧义保留 UNKNOWN。

## 接受范围与下一步

结论 CHANGES_REQUIRED；本次不接受 Source、不授权产品注册替换、不增加任何 formal case。Root 可将 F1/F2 交回独立 builder，在已登记 exact8 内修复并保留旧失败，再冻结新 commit/tree/source/evidence。独立 reviewer 将对新候选重跑本次 3 项 probes 与受影响的 focused/CLI/crash/history 回归，并核对已冻结旧证据未改。包组合、实际原 DataRoot preflight/commit、正常重开和新 qualification 仍属于后续 Root 的单独产品执行证据。
