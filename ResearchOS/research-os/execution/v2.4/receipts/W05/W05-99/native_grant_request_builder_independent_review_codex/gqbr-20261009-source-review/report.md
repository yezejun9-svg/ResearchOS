# GQB 独立 Source 审查

结论：SOURCE_ACCEPTED_FOR_ROOT_INERT_REQUEST_GENERATION。此次只接受固定 C12 请求生成器 Source。Root 后续可以针对已经存在的 grant snapshot ref3，用精确完整选择标志生成固定 Q12 请求；仍须独立审查实际请求，再以单独动作调用已审查的归档 helper。此次没有运行 compose、main、write_request、helper、原生 API、Go、SQL、私钥读取或模型调用。

固定输入为 builder 732694a07b89813c39e794e21f7edb1bc3ee7a335a0d8a0b8cf1c503fcd002cc / 24509；helper 96a7195080dc99a6b669336c7563a51cc1ba60b4f3584b6f4b7a6330a05d0771 / 23941；C12 config 38a1305ed39835194678d0e9a6f06acec1b74b1f2ba1071bc1769841c57c2256 / 1106152，CaseID t12cl149d6f49321。候选 HDF/MF 与 14 个成员完整核验。共 153 个独立检查、25 个输入 pin 通过；四个 canonical 文件与 checkpoint364 prepared refs 一致，审查前后不变。

16 个复制纯函数和 9 个常量与新 helper AST/值一致；从 config_ref 到 snapshot evidence closure 的 metadata block AST 一致。源码不存在 helper import/exec/compile/invocation、进程启动、签名、批准或归档动作。仅有一个 rb 输入读取点与一个 xb 请求写入点。输入读取严格验证整数/cap，调用 expected bytes + 1，先比长度再 SHA；复核读取仍通过同一个有界函数。真实 Source 被解析但没有作为模块运行，仅白名单纯函数 AST 被提取到独立命名空间运行，文件读取全部为 fake stream。

独立边界覆盖零字节、精确、短读、多一字节、虚拟超大、错误哈希、bool/float/负数/超 cap、cap 短读、读取异常关闭、重复 JSON、NaN 和 uint64 无精度损失。独立选择使用两个 synthetic 密文，共 61 个唯一条目，证明条数随 manifest 密文列表变化，并非固定 60。source inventory 为 28，target 为 29，包含 next_v24_sessions.sql；再加 backup manifest、rehearsal 和全部 manifest 声明的 encrypted-backup-payload。migration-sql 必须与 target 0024 完全相同，但仅选择 target inventory 一份。缺失/重复/错哈希/错路径/未支持角色/别名冲突/清单缺漏及近似标志均拒绝。原 payload 和所有 path/sha/bytes 引用不变，不读取 KeyFile、数据库或递归 private metadata。

请求 schema 精确为 researchos.native-grant-public-pin-archive-request.v1，七个顶层字段 Schema、HelperSource、Config、Snapshot、Payload、OutputDirectory、Entries；Entries 仅 role/path/sha256/bytes。Root 参数为已有 SNAPSHOT_PATH、sha256: 前缀 SHA、十进制 bytes、--select-full-current-grant-public-pins。固定 Q12/grant-public-pin-archive.request.json 使用 xb，已有文件拒绝。固定 future archive 必须不存在，且位于 receipts 并与 controller、harness、build、program、TEMP 分离；builder 不创建归档目录。现状读取确认 Q12 已存在、请求与 archive 均未出现。

此生成器验证已有 snapshot/config/payload/ready/observation 绑定和归档前生命周期，没有授予新权限，也没有续期、重签或改写原 grant/snapshot。snapshot 中的 held-job observation 是已有证据；本次 Source 审查不把它当作当前活跃进程或 grant 时效的证明。独立请求生成不能代替归档 helper 的真实 SourceReadGuard、原始密文/SQL/JSON 读取和原样复制结果。Root 必须在释放 fixture/TEMP 前拿到实际 FULL_TEMP_PIN_CLOSURE manifest：57 inventory + backup/rehearsal + 全部 ciphertext，原始与归档 refs 的 SHA/bytes 相符且 guard 关闭。签名、API 批准及后续迁移仍分别执行，九 cases、formal42、真实 Owner、完整20→24均保持 OPEN。

本审查是 pin 前后观察，没有取得 OS SourceReadGuard 或 canonical 句柄；无保留句柄。所有写入仅在本次独立审查目录。作者 45 个 source controls 的结果仅作为输入核验，未重跑其会写候选目录的控制脚本。

真实机械失败保留：918 为一次 Get-Content 批次误猜 builder-controls.final.json 与 RESOURCE_MANIFEST.json，chunk7217ff outer1，Python/native NULL。通过真实成员清单继续读取。920 为独立审查器第一轮仅 literal_eval 导致 CAP BinOp 未收集，chunk a6df1a outer1/明确 REVIEW_PYTHON_EXIT=1/native NULL；原脚本另存 review-first-attempt.py 和完整原IO。确定性检查 CAP 表达式后显式赋固定整数，重跑同一审查范围 chunk5ad739 outer0/明确 REVIEW_PYTHON_EXIT=0。未修改候选或把失败改写为成功。当前全局 next921 由 Root 通知。

STOP/FINAL。Root 保留全部实际执行和 canonical 更新职责。

