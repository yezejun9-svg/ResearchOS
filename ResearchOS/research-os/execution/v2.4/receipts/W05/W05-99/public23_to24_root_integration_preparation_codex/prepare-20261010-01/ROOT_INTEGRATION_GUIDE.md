# Main23 → Main24 Root 合成与真实 binding 配方

状态：METADATA_ONLY_PENDING_ROOT_REVIEW。作者 codex:/root/attach_restore_independent_review。本包不采纳 Source、不签发接受、不执行产品命令。Root 是 Main/Canon 唯一写入方。

## 先决结论

四个 handoff targets 是相对 Q revision 的增量，不是从当前 Main23 到 Main24 的完整补丁。当前只读观察中，PRA4 六文件有三个已存在但没有一个与候选完全同字节，Native v2 二十文件有一个已存在且不同，Q 十二文件有五个已存在且不同。不得把这些差异当作可覆盖许可；每个目标都要在 Root 实际写前核对现存字节，合并已有工作。

composition-map.json 保存每层 HDF/MF、完整候选 SHA/bytes、原声明 base/previous pins、当前 Main 的观察 pins，以及条件合成后的 40 个最终路径。它是路径和来源清单，不是已合成目录，也不证明 Native v2 已被 Root 采纳。

## 精确合成顺序

1. 保留真正 Main23：实际 binary c6eaec594aba4ef3585314e24edbae2139395529d336c0e489e2fd200f0c90ee，18390528 bytes，以及该构建的 frozen_main。保留 case2fe607 的 candidate23 原库、backup23、raw stdout/result 与单独 key 路径。不要先改 Main23 release 目录再将它充作 --source-root。
2. PRA4：prepared_run_abandonment_source_v4_codex/f1cd47ca0f9544bfbe94b51a80d7c492 六文件，先提供 store 字段/调用、runtime coordinator、migration guard、prepared-run implementation/tests 与编号 0024 SQL。
3. Native authority：原 schema24 合同引用 f6373acf36474d869fa8a64f3c490864；现存 b1599aaf259c435db5a0a5313ab0ea65 是 v2 public-anchor/inventory 修订，本包把它列作条件候选，Root 必须用其已有真实独立复核与采纳事实确定有效版本。不得因旧合同引用而回退新版 authority。Native overlay 的 prepared_run_abandonment.go 覆盖 PRA4 同名文件；PRA4 的 v4 test 文件仍保留。完整 Native 二十文件名单在 composition-map.json，涵盖 apps/control、domain authority、recoveryauthority、两个 supervisor 入口。它与 schema24 原库入口有互相引用，全部合成后才能 build，不能在中间层把缺符号当作产品回归。
4. Q：prepared_abandonment_schema_upgrade_revision_codex/6b0cb88050554e688314092dbebc6ba6 十二文件。在完整已确认前提上采用其最终 revision 字节，原 e841 包是 lineage，无需先覆盖旧 tests 再覆盖一次 revision。Q 保留普通 <=23 行为，增加固定 schema24 backup 检查及 upgrade-local 固定计划与平台入口。
5. Handoff：public23_to24_handoff_source_codex/handoff-20261010-01 的四个 integration targets 最后应用，见下表。其 candidate-root 包含十一份 Q 同字节副本，仅作来源，不要用这些副本再次覆盖 Root 后续合并。
6. Root 在新候选完成 gofmt/build/相关新边界检验与独立复核；本包没有执行这些操作。格式化后文件 hash 可改变，Root 应生成实际新输入清单，不能继续声称候选原始 SHA 就是格式化后 Main SHA。

## 四个增量 targets

| repo path | 操作 | 必须匹配的基底 SHA | handoff SHA / bytes |
|---|---|---|---|
| internal/domain/backup.go | 替换 Q 对应文件 | 97fe9760039a24798a7f9633b438e679e515b1c14c89d6f67b67925e2d1fb8c8 | 8856ce51405acf5f16c9d72754507033616575eb6b4c424f133e431b869636eb / 25345 |
| ops/backup/main.go | 在指定 Main 基底上加入入口 | e17a7b0e5e96e2a000b7be85b60184cef871e5e87c6a94d0448ddf7edde57903 | 3b362964eb7eda92bcfaee65870ddd0b26e4ba05a8c8f8ecba506ad983d6bd2f / 7307 |
| internal/domain/backup_prepared_abandonment_handoff.go | 新增；现存时须先判定来源 | null | 658e096d0f43bbee11e63a1d2be9ba01589dd4867932e134462536e02cfa1102 / 18373 |
| internal/domain/backup_prepared_abandonment_handoff_test.go | 新增；现存时须先判定来源 | null | bfcb35a97dfb513d19b90995e759d5836e9cdd361c380faaa39188148edb0a04 / 4665 |

上表新入口 SHA 以 integration-targets.json/composition-map.json 的完整机器值为准；封存脚本会核对表值。两替换目标有额外 Root 改动时采用受审增量合并，不能强制文件替换。

## 不可缺的版本、migration 和 store 保护

- migrations/sqlite/0024_prepared_run_abandonment.sql 与 internal/domain/contracts/prepared_run_abandonment.sql 必须完全相同：1c606771104c3b9abaaedaadb55d8e8c16d5f91f3398fa283ec9886b935f9098，2933 bytes。前者来自 PRA4，后者来自 Q。
- internal/domain/backup_migration.go 的 checkMigrationInventory 上界必须从 23 扩到固定 24，连续整数 1..24 检验不能去掉。PRA4 候选 df01995719bffd1551cf59d2654ce4eb49dd4cfb1a689110f3107f544e254d92，4163 bytes。
- store 保护属于 internal/domain/store.go 和上述 domain guard；internal/store/sqlite.go 不是此补丁目标。store.go 在普通 migration 前调用 CheckMigrationSafety；有业务数据的 schema23 用 target24 正常启动仍须报 MIGRATION_PREBACKUP_REQUIRED。不能通过直接启动执行 0024。
- next_v24_sessions.sql 是既有 additive session SQL，文件名含 v24 不等于已应用编号 migration24；保留原固定 hash 与 session/fence 检查。
- backup_host_configuration.go 的 <=23 既有路径保留；exact24 必须同时满足完整 inventory 与 SQL24 的 proof table/autoindexes/six triggers。不能仅改最大版本数字。
- backup_upgrade.go 仍保留旧计划，新增固定 schema23-to24-prepared-abandonment-v1 分支。旧 upgrade-local 的运行程序==SourceProgram 规则保持；真实双程序 handoff 使用新增 upgrade-prepared-backup，其运行程序必须==TargetProgram，并与 source 程序 hash 不同。
- runtime_coordinator_windows.go、prepared_run_abandonment.go 和 authority 文件构成编译依赖与后续授权边界。isolated handoff 不授予原库 migration/abandonment 权限；新 receipt prepared-abandonment-public-backup-handoff.json 不能伪装成旧 prepared-abandonment-rehearsal.json。

## 真实 Main23 binding 字段

binding-field-map.json 给出 case.closed.json 的准确 JSON pointers；binding.actual-source.template.json 只填本轮直接读到并核验的旧实际输入，target_program_sha256 保持 null，当前不可作为可执行 binding。

case.closed.json SHA 2fe607aa52fe6beceaa45e2791d56f8d9d2825e074fbd4ea3ed0bcb6444bd70a，793194 bytes。backup23 位于 calls[1]，argv[0] 是 c6ea Main23，argv[1] 是 create，--db 指向 candidate23/researchos.sqlite，--out 指向同 case 的 backup23。actual_exit=0。

manifest SHA 11b1e013b987540c4b83840ba4b7c9f575611971c30e5f83255f9c027ebdc70e，2304 bytes，id=1b8bea2d695f74c53a937ff2dcd5080c，migrations=1..23，purpose 缺省。stdout SHA 378226d5998f57f1bc7017176c80c0193115fb83bbbab0756fdb7999a87e0c4d，2305 bytes。两文件 JSON 内容一致，但 stdout 多一个换行；不能互换 raw pins。

producer_observation 指向原 raw/backup23.result.json：68d61be9f4a7cc6118897ae464eccd9ca3eeda907a6aa24811e8e06ab8572499，3703 bytes；不要使用 before.json 的 null exit，也不要把 case 摘要或本配方当作 producer 原始执行证明。Source 只验证该 observation 文件字节，Root 仍负责结合真实主机 call/result、binary 资格与非作者实际复核确认来源。

binding 内所有摘要需加 sha256:，包级 HDF/MF refs 使用裸 hex；填完真实 target hash 后再计算整份 binding 文件摘要。不得先固定 binding hash 再编辑内容。target hash、target release、实际 handoff destination、backup24/restore24 返回与接受状态均等待未来真实观察。

## 后续独立工作与保留证据

Root 的最小新增边界是：在已确认 compose 来源上构建实际 Main24；为既有 Main23 backup 填入正确 target pin 与经复核 observation；新目标执行 isolated 23→24 handoff；随后由匹配 Main24 做普通 backup24 与 restore24 并独立复核。这不是对未执行结果的承诺。无需重跑成功 Main20→21→22→23、旧 Source controls 或 W09 Native。

source-root 必须冻结并含精确 1..23 migration/contracts/additive inventory；target-root 含对应精确 1..24。key 只传现存独立路径，本文没有读取 key 内容。现存 candidate23 必须与旧 backup rows 一致，否则 handoff 正确拒绝，不得编辑旧 backup 或弱化 snapshot 检查。

本轮诊断 original1237/1238/1239 各保留真实 session header、call、result 三行和成功前缀。1237 outer0/Python null；1238 outer1/Python null；1239 outer0/Python1。第三条发生在 metadata 已写之后的审计捕获解析：原函数结果前置截断提示，不能对整段作单 JSON 解析；追加捕获按原始记录分行解析，只补缺失记录，不重跑合成/binding 生成。

