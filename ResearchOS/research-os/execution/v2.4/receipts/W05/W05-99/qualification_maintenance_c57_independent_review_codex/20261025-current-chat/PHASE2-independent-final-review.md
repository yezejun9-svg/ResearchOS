# C57 独立阶段2复核完成记录

结论：最终 `03aa4d687dfaa541d9b18d4c766805307a537d1d` 的本轮 Source/自有夹具复核未发现仍未关闭的 Source P1/P2 阻断。既有业务 token 特权缺口已在 v12 的共用准入路径修正并独立补测。**这不是 73 项全部 native/actual PASS，也不是 formal 接受；Root 决定最终 Source adoption，formal 增量0。**

最终 tree `81059bc4cdba04716fcd2607496485bbbf22bc80`；相对旧 `08d63ed86356a93fe5715732cfeae0624c5cb6c9` 仅 boot_windows.go 与 boot_windows_test.go 两文件变化。独立逐一对照57个 git blob 和40个 inherited pins，运行前后无漂移。旧2文件在 PHASE2-old08d63-preserved-delta2 保留，原运行结果原样保存。工作目录名仍为 source-08d63ed86356，版本以 recipe 中的 commit/tree 和核验manifest为准。

## 独立执行与计数

选作最终证据的10组：native exit 全0；通过事件 172，跳过事件 3，失败事件0；跨组去重后通过测试名（含子测试）120，顶层通过测试名64。这些计数包含 C/D 重复覆盖及父/子事件，不能换算为73条合同断言或正式用例。完整计数在 PHASE2-test-summary.json。

| 组 | Source版本 | pass events | skip events | 主要证据 |
|---|---|---:|---:|---|
| 095-phase2-core-c-owned-cache | 08d63 | 36 | 0 | 七包lease/入口/journal/store/backup/CLI |
| 096-phase2-domain-c-owned-cache | 08d63 | 24 | 0 | 五upgrade guard、历史私有事务、typed dispatch/immutable classifier |
| 103-independent-domain-census | 08d63 | 1 | 0 | 独立87表逐表census |
| 114-independent-native-hold | 08d63 | 3 | 0 | 8证据文件/4自有祖先/GC/copy/SQL返回时序 |
| 116-independent-sql-cuts | 08d63 | 1 | 0 | 9表真实SQL失败切点、第二writer、typed hex87表census |
| 120-independent-journal-prefixes | 08d63 | 10 | 0 | 9种前缀/terminal状态及只读证据保持 |
| 128-independent-concurrent-borrow | 08d63 | 1 | 0 | 32并发borrow只有1成功 |
| 133-v12-boot-c | 03aa4d | 44 | 1 | 最终Boot C密集继承/原生ACL/特权/真实token |
| 134-v12-boot-d | 03aa4d | 43 | 2 | 最终Boot D ACL/noAI/特权/真实token |
| 135-v12-host-wiring | 03aa4d | 9 | 0 | 最终Host与CLI依赖接线 |

C最终仅 child helper TestPEExecutionProbe 顶层跳过；它在真实PE测试子进程中使用。D除同一helper，还因自然目录只有8条ACE而跳过需至少200条ACE的自然继承dense分支；D显式208ACE及exact no-AI native回读恢复已执行。C自然父208ACE、file106 inherited ACE的原生往返已执行。D实际PE路径见134 raw；098虽标D但实际C，已纠正分类，未覆盖或删除原记录。

## 关键断言及证据强度

- 116用独立 `typeof + hex(CAST AS BLOB)` 编码文本/BLOB及整数，REAL用26位表示，逐表稳定排序；成功只改变9表，其余78表完整内容不变。domain_versions +5、domain_objects +3、uploaded_content +1等精确delta成立。每个目标表在真实writer命中TEMP触发器的ABORT后，同一事务Rollback返回，全87表无差异；被拒重复写入也无差异。103较早版本用quote编码，116提供保留NUL的加强编码。
- 114从实际三帧native构造器取得holds，调用私有validated closure；8个raw/MODEL/input文件的写/删除/改名，以及4个自有祖先改名，在SQL Commit/Rollback返回前与返回后Close前全部失败。每阶段强制2次GC；复制closure保持共享owner；Close后8文件可写、copy Check拒绝。此SQL正证是fixture marker事务，实际planned writes另由116验证；两者结合Source接线，不能冒充完整public Host业务操作。
- 116真实第二SQLite连接在reservation期间报locked/busy，原事务Rollback后同一写入成功。096还独立执行candidate阻塞driver的取消Rollback与Commit错误返回测试。128真实32 goroutine借用竞争只1成功，outer原值/副本Close拒绝，独立native lease竞争失败，释放后可重新获得。
- 120构造empty operation、plan-only、partial plan/BEGIN、错sequence/hash、NOT_APPLIED、DB_COMMITTED_OBSERVED、DURABLE；未知/非终态阻止ordinary，NOT_APPLIED仍阻止；DURABLE按合同放行。所有inspection不改证据，不创建DB。每个文件系统Sync指令处的实际掉电/进程kill未运行，durability写入顺序为Source验证。
- v12 boot_windows.go:856–903先读取真实TokenPrivileges，按present LUID拒绝SeTakeOwnershipPrivilege/SeRestorePrivilege/SeBackupPrivilege，与enabled/disabled无关，然后生成digest。计数/长度用uint64边界检查；lookup/读取失败拒绝。实际共用producer/current/post/Check/MarkCDurable路径与独立管理restore边界见token-privilege-static/v12-static-review.md。133/134执行6个disabled/enabled合成LUID反例、安全LUID和截断反例，确认live token bytes未改变；实际安全producer与既存Explorer读取都PASS、没有Skip。未创建/启用实际危险特权token。

## 旧组复用及未证明分支

08d63到03aa4d仅Boot实现与测试2文件变化；其余55个scope文件、40pins、整个git diff中的其他源/测试依赖逐字节未变。lease/upgrade/journal/store/internal planned writer及5个独立补充文件原结果据此复用；Boot全部C/D与Host/CLI依赖边缘已在03aa4d重跑。旧Boot结果保留，不拿来证明v12特权修复。

不同SID/elevated恢复管理员、真实foreign-owner恢复、特权可读SACL、实际在线backup/restore/credential、完整部署supported-set/ancestor策略、真实FullRestart及原业务执行均为各自P/R/A分支UNAVAILABLE。测试名含ReadableSACL的用例是构造native SD缓冲区，不是成功读到真实privileged SACL。现有native capture有SACL不可读时的明确未取得语义，不能当已读取。未改OS祖先、账号、原ACL/DB/Core/STOP或Main。

完整 public Host preflight→current quiescence→maintenance commit→MarkCDurable→disarm 正链受上述真实边界前提限制，没有通过伪造q、公开bool、B online ticket或直接rawhandle补足。73项逐项Source/fixture/native与缺口见PHASE2-final-coverage73.json；部分条目为Source已验证、内部native已验证、public/actual未执行，不能整体记PASS。

## 失败与历史限制

reviewer累计原生非零9：此前Phase1为3；Phase2新增6分别为模块zip缺失、两次缓存复制准备、一次未捕获到独立文件的错误路径rg、一次无匹配rg、一次错误lease测试路径读取。候选断言失败0；所有实际候选测试raw/recipe完整。121还出现native0但stderr缺路径的读取诊断，单独列示。094/094b和089等原记录完整保留；原作者失败/格式化恢复前缺diff/native unknown等不被重置或消除。原始历史Wait缺失、exit124、raw3/ACK2/queue_empty=false、money UNKNOWN不改写。

本封存仅报告独立证据，不改任务卡、Main或formal状态。
