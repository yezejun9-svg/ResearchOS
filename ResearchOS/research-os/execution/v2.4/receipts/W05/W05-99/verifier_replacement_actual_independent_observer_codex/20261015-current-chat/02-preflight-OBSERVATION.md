# 实际 preflight 独立观察与 plan 核对

plan `8ba3ed5d6a1cc467b2e8539d3c90ff710c3038b913aea8937e3e20989393cefe` 的全部绑定与实际观察一致。Root preflight native exit 0，状态 PREFLIGHT/NOT_APPLIED；本 observer 未执行 commit/recover，也不签发接受。原 schema 未迁移，formal 增量 0。

相对 `01-baseline`，88 表的完整类型化行摘要、完整 schema 摘要、schema 24、四项 global census、Owner/Host/service root/ALL reserved children 语义及 lineage、公开 host state、原注册 bytes、主 DB 和 WAL raw hashes 全部保持。当前相关 Core/Desktop/verifier PID 快照为空，现存 coordinator.lock 可独占只读打开；只读观察结束后全部 native handle 已关闭并再次独占只读打开复验。观察者在原生 deny-write handles 下使用 mode=ro/query_only/BEGIN/ROLLBACK，自身读取前后所有允许文件字节和全树元数据一致。

实际 preflight 后只有 `researchos.sqlite-shm` 在公开文件比较中变化：SHA256 从 `c35020473aed1b4642cd726cad727b63fff2824ad68cedd7ffb73c7cbd890479` 变为 `b295c557a95e745c5ed44fd567e712adae5be65fb11f2534d98cce37c141b783`，mtime_ns 从 `1791920316533129300` 变为 `1792056490703372700`；size 32768、native file identity 保持。未保存旧 SHM 原始字节，因此无法给出逐偏移差异，也不把具体 readmark 字段或更新机制当作已证事实。

原冻结 ARCHITECTURE.md SHA256 `66b0023d91a53827cbccbf5cbc58010224d69969c17a59e1365cd4f4d11c13cc` 第 74 行明确要求 SQLite WAL/SHM 文件系统行为单列观察，不能由逻辑只读推断所有辅助文件不变。Root 追加 CP493 scope amendment SHA256 `36118c237961a1d5bea414c1ede5934316869d07deaa0f16a207312cad1a3edb`，按该原有架构区分业务不变性与 SHM 实测差异。原 CP492 scope 和第一次严格 public_files 比较失败完整保留，没有把 SHM 记作字节未变。

plan 核对覆盖：当前原生 SID→principal_ref、Host ID、唯一 Owner、service root 和所有 reserved child；DataRoot/host/DB 原生 volume/index；schema/census；state raw hash；从实际 readonly DB 重算的 lineage hash；old raw bytes 与 baseline 精确一致；old/new record canonical hash 和 installation hash；新 manifest/exe path/hash/Source4f；plan 的新注册 bytes 按冻结 Go struct 字段顺序独立重建后逐字节相同。安装字段精确只改变 executable/executable_hash/source_commit，其余注册权威字段不变。

history_sequence=1，前驱 operation/plan/terminal 摘要为空，与实际 journal 尚不存在一致；没有 rollback_of。plan、新 manifest、新 verifier exe 的真实 ACL 均为 current-SID owner/protected single allow ACE，flags=0、mask=0x001f01ff；native identities 验证单硬链接且全部父路径无 reparse。原数据公开 host/state/registration ACL 亦独立读回。

保留两次 observer 审核失败：第一次严格 public_files 比较发现真实 SHM 差异；第二次 review helper 误用 `/` 索引 Windows 相对路径，产生 KeyError 后修正。两份失败脚本版本和 failure receipts 均保留。最终结论是“plan 绑定匹配，SHM 差异单列观察”，不是产品验收或执行 commit 的替代授权。
