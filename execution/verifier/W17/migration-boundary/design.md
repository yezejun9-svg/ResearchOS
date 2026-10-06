# 本机控制面 schema 13 → 14 升级边界设计

结论：实现一个独立、明确命名的 `upgrade-local` 入口。它只在同机复制并升级控制面数据库，保留指向原受保护服务的不透明引用。普通 `create/export/restore` 的非 PROJECT 拒绝和 `Service.New` 的 `MIGRATION_PREBACKUP_REQUIRED` 原样保留。此文是只读设计评审，不是实现或实际升级通过证明。

## 事实与范围

- `backupIntegrity` 检查所有 Artifact 历史版本，对非 PROJECT 返回 `PROTECTED_BACKUP_REQUIRES_W17`；`CreateBackup` 在此处停止。
- `RestoreBackup` 先要求快照版本列表与 `SupportedMigrations` 精确相等，之后才有程序内 `Migration` callback。CLI 既无升级计划，也未设置该 callback。
- `Service.New` 从 migration 参数的所在目录 glob 全部版本，所以仅保留旧 exe 不足以锁住旧 schema；回退同时要保留对应 13 版 migration/contracts 根目录。
- `0014_remote_access.sql` 只新增五个 remote_* 表及两个 remote_audit 不可变触发器。冻结字节 SHA256：`687b01552260301a8f3f39e92422f16d0b2e310b38f77d1b025566f9a9cfa4d7`。不需要改写既有业务对象。
- W18 已接受 W18-G01/G02 与 A12 的受限原范围；其报告明确不含受保护备份。本次需对改动运行相应 W18 回归，不能沿用原回执自动授予新增能力。
- 原库两份 W11 qualification 和受保护引用的存在、schema13/PID66092、既有原生 rollback snapshot，由主 Agent 报告。本评审未打开 `.local/data`、原生 snapshot 或任何受保护文件，也未调用服务。

## 最小文件责任

1. **新增 `internal/domain/backup_upgrade.go`**：本机升级协调器、冻结 13→14 计划、受保护外部引用校验、迁移前后不变量核对。局部共享逻辑可抽入现有 backup 文件；不得复制/削弱整个恢复算法。
2. **有限修改 `internal/domain/backup.go`**：复用现有加密、MAC、快照、暂存/原子发布及恢复流程；通过私有内部策略给新增入口传递更窄的引用保留规则。公开 `CreateBackup` / `RestoreBackup` 默认路径不放宽。新的包用独立目的/格式标记，普通 create/export/restore 不能消费或声称导出了它。
3. **有限修改 `ops/backup/main.go`**：增加 `upgrade-local` 命令；输入旧库、独立密钥、全新快照目录、全新隔离目标、固定源/目标 release 根与 13→14 计划。CLI 不启动 HTTP/worker，不切换原库，不接受任意 SQL/callback、ignore/force 开关。
4. **新增 `internal/domain/backup_upgrade_test.go` 并补 CLI 测试**：真实文件 SQLite、真实新进程启动与负向断言。测试内部可注入合成描述校验 seam；CLI 正式分支只能使用具体 `FrozenProvider`，不得把任意 Provider/JSON 声明视为 LIVE。
5. **在既有 ops 恢复文档补一段本机操作说明**。若新增命令登记，交主 Agent 串行整合。

`backup_recovery.go` 中 source relocation、`backupFence`、acceptedTaskBinding 重算直接复用，不需要业务语义修改。`store.go`、`backup_migration.go`、0014 SQL 与 protected service 不改。不要为了复用而新增启动期绕过 guard 的参数。

## 新入口的精确流程

1. **预检与冻结**：旧程序/旧 migration+contracts 根、目标 release 根、计划字节及其哈希、源 DB migration 列表和 schema_hash 都绑定到计划。只接受恰好 `[1..13] → [1..14]` 与上面的 0014 哈希；拒绝缺号/重复号/额外未来版本/已有14/错 schema。新程序本身不隐式假定 cwd 就是版本根。记录独立目标，禁止源路径、目标路径、密钥目录之间的重叠、别名与已存在目标。
2. **源库停写窗口**：由主 Agent 串行暂停原产品写入/worker，保留旧程序与匹配根和回退 snapshot。新 CLI 不杀任意进程、不自改进程配置。源库在整个 clone→验证→切换窗口不得继续接收业务写入，否则恢复副本可能丢失后续写入；发现逻辑快照漂移即停止切换。仅执行标准一致性 snapshot 操作，不对源库迁移。
3. **生成受限加密快照**：复用 `VACUUM INTO`、完整性/引用/receipt 检查、AES-GCM+MAC、单独 key、临时目录和原子发布。保存全量 control-plane DB 与 PROJECT 内容；保留所有对象及历史行中的外部引用。禁止读取、复制、重新生成 private service 内容。专用包不输出通用 portable JSON 或明文 protected 清单；其元数据/票据仍留在加密 DB 内，公开报告只给数量和摘要。用途标记类似 `SAME_HOST_CONTROL_PLANE_UPGRADE`，明确依赖原服务，不能跨机/服务丢失恢复。
4. **校验唯一允许的受保护引用类别**：扫描所有 Artifact 历史版本，不只 current。PROJECT 仍执行原有 sealed bytes/hash 检查。非 PROJECT 仅允许已登记的 LIVE、VERIFIER_ONLY、有效 opaque ticket、且与具体 FrozenProvider 的 Describe 返回的 ticket/hash/size/media/mode 完全匹配；未知种类、FIXTURE、未绑定引用一律拒绝。检查历史及 current 引用 ID/revision/内容摘要，禁止重登记从而生成新 ID。对该 ticket 必须不存在 host `uploaded_content` 内容行；不调用 Provider.Read。验证 Ready/Boundary 的既有独立身份约束，服务缺失/变更/失败即退出。检查现有 qualification 与服务固定终态绑定，但不重写结果、不授予自动权限。
5. **隔离恢复后迁移**：验证专用包 MAC/文件 hashes、源 schema/list、冻结 contracts、库存与历史一致性后，在全新且未发布的 stage 执行现有 relocation 与 fence。之后由受检计划的内部 callback 在单一事务中执行冻结0014字节并记 migration14；这是恢复内的受限迁移，不是绕过启动 guard 的原库 SQL。源版本比较仍是13精确相等，目标版本检查另设为14，不能用宽松“子集兼容”替代默认逻辑。
6. **发布前验后**：迁移后所有既有 schema 对象不变，恰好多出0014五表两trigger，以及 restore fence 自身已定义的表/trigger；不得把带 fence 的 schema 与无 fence 的全新14库直接全量等号比较。五个新表为空。全部 qualification、Artifact（含受保护历史）、refs、receipt、费用账本、游标等 ID/history 内容哈希不变。允许的业务差异仅现有 W18 明列的 fencing：旧 credentials revoked、活动 Run 新revision/过期lease、未完成 effect UNKNOWN、追加审计、source roots relocation；旧历史行不删除或改写。重算 acceptedTaskBinding，复验所有 PROJECT bytes/hash 与受保护外部描述；不自动恢复任务、不派发外部动作。
7. **发布与验证**：关闭 stage 连接、checkpoint/sync、写带计划/源快照/目标版本/允许差异/零外部派发的报告，然后原子发布到新目标。新产品 exe 用 target release 根和新DB实际启动，通过 `New` 的正常检查（已为14，无新迁移）及健康/读 API。CLI 不自动切换或删除原库；主 Agent 在独立复核后串行指向新目标，保留旧实例回退材料。只能运行一个可写权威实例。
8. **失败回退**：所有失败只丢弃本次创建的未发布 stage，源库、稳定加密快照和受保护服务保持不变；中断留下的独立材料可审查，但不得覆盖继续。迁移失败与拒绝目标必须有真实负向测试。切换前可直接用旧 exe + 13 根重新打开原库；切换后若有新增业务写入，不能把旧快照称为无损回退，需要另行明确恢复点。禁止自动删除 remote_* 表作回退。

## 外部保护引用证明的边界

现有 FrozenProvider.Describe 通过 aggregate 验证 SCM identity、进程/pipe 归属、installed binary hash 和已完成终态描述，Read 永远拒绝。broker 每次 aggregate 重读的是 canary 文件；COMPLETED frozen batch 不是每次重新读回 hash。因此上述过程只能证明 **既有外部引用与当前受认证服务终态描述一致**，不能证明私有 batch/envelopes/raw results 已重新逐字节校验或已备份。包和报告均应保存 `protected_payloads_included=false`、`protected_payloads_revalidated=false`、`recovery_dependency=ORIGINAL_PROTECTED_SERVICE`。不扩 A12/C22，不修改管道词汇、不部署新 service、不重跑30次正式评价。

## 最小验收

- 原 `CreateBackup/export/RestoreBackup` 对含非 PROJECT 历史版本仍拒绝，`New` 在 populated13+14根仍返回 MIGRATION_PREBACKUP_REQUIRED，原13所有数据不变。
- 独立合成夹具具有两份 qualification、受保护 Artifact current/history/ref、公开 sealed内容、receipt、费用/游标、未完成 effects；upgrade-local 后除明列fence差异外全量历史指纹一致，qualification保持原FAILED/ADVISORY、自动权限NONE；Provider.Read调用次数为0，外部派发为0。
- provider缺失/模式或SID边界错/描述任一字段错/未知ticket/受保护票据存在uploaded_content/旧根与计划不匹配/SQL hash错/多余迁移/失败SQL/中断/占用及别名目标，均拒绝且原库与稳定包不变。
- 在独立Windows目录通过真实CLI：迁移前13拒绝、upgrade-local产生14、新进程正常启动读取同ID/history；旧程序+旧根仍能读原13；旧credentials失效、active effects不能盲重放，必须fresh observation才按W12续接。
- 针对实际共用变动跑现有W18 backup negatives、CLI、alias/identity以及fencing回归，补W11保护API/qualification拒绝路径；只因这些改动重跑，不重跑正式provider30次评价。
- 真实`.local/data`操作前提供 candidate commit、定向测试/CLI回执、源/目标/快照计划与零private-body声明，独立复核后由主Agent执行。此文不授权本评审者操作原库或服务。
