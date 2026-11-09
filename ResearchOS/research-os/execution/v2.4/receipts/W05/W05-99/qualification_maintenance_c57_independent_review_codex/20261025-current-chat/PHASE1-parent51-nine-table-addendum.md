# 父 51 九表完整行分类补查

结论：原 P1 保持，并确认同一完整 after-image 失效机制还影响 **domain_objects.immutable 的精确值**。共两处需修复，归于原 DB-02 / DB-05 / JRN-01 / JRN-02；不增加 73 项永久断言。本补查继续使用 C51-static-snapshot，不读取父作者正在修改的源码，不运行 candidate tests。

## 新确认：immutable 非 1 值被统统当作 0

- domain qualification_failure_maintenance_windows.go 1165–1166：非 EventEnvelope 仅要求 `immutable == 1` 为 false，而不是 `immutable == 0`。
- store qualification_maintenance_windows.go 303–309：相关五对象的 domain_objects 整行从 residual census 排除。
- 固定 base migration 0002_domain.sql 第 3 行：immutable 为 INTEGER NOT NULL DEFAULT 0，无 CHECK 值域约束。第 39 行触发器只阻止 OLD.immutable=1 的 UPDATE。后续 schema24 trigger 只涉及具有 prepared-abandonment 行的 Run/Task，不覆盖 ImpactLink。
- 因此合法提交后对本次 ImpactLink 执行 `UPDATE domain_objects SET immutable=2 WHERE project=? AND kind='ImpactLink' AND id=?` 的值变化，既不会被该 schema 的 immutable trigger 拒绝，也不会被当前 exact checker 判为不同；protected/residual 不变，APPLIED 分支仅检查 schema hash，仍可能 APPLIED。使用 -1 也有相同判断问题。这是静态推导，未执行该 SQL。
- 修复要求：比较精确整数（EventEnvelope=1，其他四对象=0），并针对 0→2 / 0→-1 回归为 UNKNOWN，保持合法 0/1 的正常 APPLIED。若整体改成 typed expected-row census，应同时覆盖这一项。

## 对原 dispatch 发现的触发条件澄清

固定 base migration 0017_runtime_dispatch.sql 15–17 行确实为 project/run/epoch/dispatch_key/manifest/manifest_hash/prepared_at 设置 BEFORE UPDATE trigger。因此，**普通 SQL 直接改 manifest 或 prepared_at 会先被 trigger 拒绝**，不能将这种测试的报错当作 classifier 已经覆盖了这些列。首报告描述了分类器本身的漏验，这些例子不应被表述为普通 UPDATE 即可完成的反例。

worker、journal_locator、identity 没有这一 frozen-column trigger 保护。它们在 residual 被整行排除，也未进入 exact checker 的 SELECT，因此仍构成可用普通 SQL 构造的同类误判路径。该发现无需删 trigger 或改变 schema，P1 结论不变。全部 15 列仍应有可审计的 expected after-image 绑定，不能以当前存在部分 trigger 代替完整分类契约。

## 九表逐列覆盖核对

固定 base commit：085b4711afe0c1288448b174eef24ecd5af0551b。读取其 migrations 0002 / 0003 / 0005 / 0017 / next_v24_sessions，保存到 C51-frozen-base-schema；另读取 0024 检查后续触发器条件。067–071 保留原始命令与输出。以下“覆盖”表示列名和值的静态对照，不代表已执行类型变异、约束破坏、crash cuts 或真实数据库接受。

| 被排除表 | 原始列数量 | WHERE / exact 对照 | 补查结果 |
|---|---:|---|---|
| uploaded_content | 7 | storage_key/project/principal 定位；bytes/content_hash/sealed/expires_at 精确读取比较（1234–1247） | 未发现其他漏列；sealed 必须=1，proof bytes 用 bytes.Equal。 |
| domain_versions | 6 | project/kind/id/revision 定位；revision/body/content_hash 对照（1119–1167） | 未发现其他漏列；content_hash null/value 分开判断。 |
| domain_objects | 7 | project/kind/id 定位；revision/body/content_hash/immutable 对照（1119–1167） | immutable 只比较是否等于1，漏 exact 0，见上。 |
| domain_refs | 9 | project/kind/id/revision 定位；field/target_project/target_kind/target_id/target_revision 全量排序列表（1001–1018、1171–1233） | 没有遗漏列；集合长度/内容参与判断，额外 ref 不会因 SELECT 一条而消失。 |
| runtime_observations | 6 | project/run/epoch/receipt_hash 定位；body/observed_at 对照（1249–1259） | 未发现其他漏列。 |
| runtime_dispatches | 15 | project/run/epoch 定位；七字段 SELECT（1261–1275） | 漏 manifest/worker/journal_locator/identity/prepared_at 共5列，其中 worker/journal_locator/identity 无 frozen UPDATE trigger 保护。 |
| outbox | 5 | project/sequence/id 定位；body/acknowledged 对照（1277–1288） | 未发现其他漏列；acknowledged 必须=0。 |
| event_state_snapshots | 4 | project/event_id 定位；body/revision 对照（1290–1305） | 未发现其他漏列。 |
| idempotency | 9 | principal/project/operation/key/request_hash 定位；body/status/headers/created_at 对照（1307–1320） | 未发现其他漏列；body 对 canonical marker bytes 比较，status=200，headers={}。 |

typed full-row / cell 编码仍是原 census 契约的一部分；本表不会把 Go Scan 后的值比较认证为 SQLite storage-class 完整测试。修复后仍需由新冻结版本的 Phase2 验证对应完整 SQL 像及0delta语义。

## 追加诊断

067、069、070、071 native exit 0。068 中四次 git show 输出成功；末尾 git grep 对 next_v24_sessions 的九表模式无匹配，故整个捕获的 native exit 为 1。保留该原始 nonzero，不覆写、不将其计作测试失败。reviewer 历史 native nonzero 原累计 2，本次新增 1，累计 **3**；工具协议错误仍 0；candidate tests 仍未运行。

上一报告与 seal 原样保留：b25628c14a9f8b47ce1f62d133482fb0f439e8490461ec8a8f5710026d08e085 / 89ce92686cc716ca2bd0d1d867e341bad85b9a4a3992d3d3961a6ba272ee9fbb。追加 seal 绑定本文件、冻结 base schema、067–071、原报告与原 seal；不能用旧快照的审查结果替代修复后候选的接受。
