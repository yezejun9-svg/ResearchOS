# Root 手动逐阶段 concrete approval helpers

状态：SOURCE_PREPARED_PENDING_INDEPENDENT_REVIEW。作者不自批；此包未执行任何 helper main，未生成 approval、签署或发布。

T10 原因已经对应原始 invocation、stdout 与 Go Source：native PID 42244 / FILETIME 134359866411023123，exit 1，elapsed 1200.9577792000491，timed_out=false，termination_requested=false。主测试 20 分钟 context 已过期，cleanup 复用同一 context，在 retained.ready 写出后再次立即失败，TempDir 随后清理。原数据库已不存在，本包不生成 T10 全库检查或释放成功记录。grant 的四分钟期限与这个二十分钟生命周期是两个独立限制；脚本不会刷新任何期限。

root_concrete_approval_helper.py 的单次 request 显式选择 sign、publish 或 release-fixture。phase 只支持 release、grant、fixture-retained，case 严格限定当前已审查的 positive-replay。输入以 path/SHA256/bytes 精确绑定。没有 phase loop、自动 sign/publish、预签 future grant、重试或 TTL 延長，也不调用 controller API。现有 API 仍负责当前 owned Job 与真实 native file identity 的最终验证；helper 成功只代表具体 approval 文件已生成，不代表 API 已消费或 native 已成功。

Config/HarnessConfig、FrozenInputs 全集、实际 tagged compiler inventory、compile invocation/native exit0/Job closure、snapshot/public evidence、ready/current phase、payload、explicit fresh CaseID 和 binary namespace 都验证。release Source 根据原 harness 的七目录、可选 vendor、go.mod/go.sum/locked.json 与可选 go.work 清点全量集合，不固定未来599数量。issuer public key 与 root-adoption public key 分开验证；key-provision.closed 只读 public metadata，绝不 follow private_resource_ref、读取密钥内容或保存该 metadata 副本。

sign 只允许未消费的本阶段 payload；publish 额外要求固定 signing receipt、真实 native exit0、精确 PID/FILETIME、全部 Job closed flag、source guard closed、此前 sign approval 的完整一致性和 signed payload 的原始字节一致。grant 显式绑定已发布 signed release、source/target programs、owner/project、native IDs、原 fixture hashes、rehearsal/options/backup 与所有声明的 RawPin。期限在昂贵读取之前、验证期间、最终写入之前复核，原值保持不变。

release-fixture 必须读取已完成的 Root whole-SQL inspection receipt，完整核对 config/snapshot、事务/数据版本/原文件稳定性、native IDs、typed-row hash、两个 reader guard。Root 明确选择 migrated 或 unchanged-failed；前者要求完整 after rows/迁移版本/新空证明表与全部 invariants，后者要求 schema23 和全部 before rows 精确保持。此 helper 不执行 SQL、不伪造独立检查；数据库消失或生命周期 terminal 会拒绝。

public_evidence_archive.py 仅允许显式枚举的 typed-row-digests 与 fixture-summary，两类都是结构限制后的原字节复制。它不会跟随 JSON 内路径或引用，不复制 SQLite/WAL、DPAPI、fixture key、raw rows、任意 stdout/stderr 或通用 JSON。更广类型目前不支持，不应将这个有意窄的归档器称为全目录归档。

验证：Python AST、27 项纯 Source 控制与原文件前后 pin。控制包括严格 JSON 类型、重复成员/NaN、实际旧 signer receipt 结构、Job/guard 异常、signed payload 字节错配、grant 绝对期限边界/未来签发/TTL延长、T10 terminal、raw-row拒绝。归档 signer receipt 字段检查不是新 native 验证；历史时刻的 TTL 正控制只用于纯函数，未改变系统时钟。最终入口还需非作者 Source 审查和未来 Root fresh case 实际使用。

provenance：四份既有 Root helper 文本在 base 中保留 exact bytes；controller/API/harness 仅通过原路径 pin 引用。新实现为新的独立模块，未改旧文件，因此不存在旧文件反向补丁；provenance.json 将原判据逐项映射至新函数，并明确旧固定 Case/pin 替换为 Root 请求参数。SourceGuard 为前后精确只读 pin；真正调用 approval helper 时另外启用原 deny-write SourceReadGuard 并要求关闭成功。

本任务机械读取错误893：同一 PowerShell 调用对两个 null 字段调用 GetType，两条诊断属于一个origin；外层exit0，Python/native均null。原始完整输入输出见 failure-origin.893.json。未重置失败计数。无新增 native actual；894/之后 Root 的其他失败不在本包重复计数。

