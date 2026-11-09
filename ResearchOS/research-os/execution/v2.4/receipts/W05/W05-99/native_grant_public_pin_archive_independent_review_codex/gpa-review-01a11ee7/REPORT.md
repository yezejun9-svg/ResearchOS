当前 GPA helper Source 结论：REQUEST_CHANGES。唯一阻断项是 GPA-R01；修正后可做有限 delta 复核，真实归档与最终验收仍单独成立。

GPA-R01（P2）：native_grant_public_pin_archive.py 第91–95行的 read_ref 先调用 Path.read_bytes()，再检查长度与 hash。run 在 SourceReadGuard.acquire 前通过此函数预读 request/config/harness/snapshot/payload/readiness/observation/guard Source。声明 bytes <=128MiB 不等于限制实际读取量，漂移大文件会在 Guard 拒绝前被无上限读入。应在新 immutable revision 使用至多 expected bytes +1 的读取，拒绝超长/短读/hash漂移，继续保留 Guard 的持柄复制和总量/单文件上限。此发现来自静态数据流，不是本轮发生了大文件读取或实际运行失败，也不增加 Root 机械失败计数。

已独立核对的范围
- 作者 HDF/MF/helper exact pins：原 28 个 MF 成员全部匹配；38 个原始 Source 输入全部通过短时 SourceReadGuard 并完整复制。
- helper INVENTORY 的29个不同相对文件与实际 N12 Source SHA/bytes逐项一致，也与 backup_upgrade/queue/configuration/prepared 四层生产常量逐项一致。preparedUpgradeRelease 接收23/24编号SQL，加四个JSON与next_v24_sessions.sql，因此正确计数为source28、target29，共57。旧27/28计数应被明确纠正，不能改旧Source掩盖。
- grant白名单仅57项inventory、backup manifest、rehearsal公共JSON和显式cipher .enc。source/target程序与五个fixture-evidence仅核元数据，不能选择归档；未知role拒绝，未递归跟随私钥、KeyFile、DB/WAL/SHM。
- migration-sql 与 target-inventory:...0024 只有完全一致的 path/SHA/bytes 才构成唯一声明alias。alias自身不能作为第二选项；target复制一次并在结果保留双role映射。其他重复路径/role拒绝；不同roots同字节仍保留不同原路径。
- 选项必须是payload原RawPin精确子集；非空部分选择保留精确missing_roles，缺项不能称FULL_TEMP_PIN_CLOSURE。cipher角色集合与backup manifest文件名集合强等；cipher仅按原raw bytes复制，不解密、不打印正文。
- SourceReadGuard 获取后再次比对已pin输入，复制直接来自get_buffer；写入xb独占、fsync与字节重读核验。finally关闭guard；仅closed/errors空/verification PASSED 后输出success manifest。
- 输出是Root receipt树下fresh目录，排除controller/harness-output/build/programs/TEMP，并拒绝与输入重叠；关闭controller或fixture-release请求会拒绝。复制不延长grant TTL、不签名、不自动批准或改写原grant。
- JSON严格拒绝重复key和非有限数；bytes拒绝bool/float；所归档JSON不重序列化，Python整数/原raw bytes保持FILETIME精度。

验证范围与待接输入
作者41项纯Source controls已读源码和结果，未重跑、未计为真实Win32/archive证明。本轮独立仅进行读取、SHA/bytes比较、AST结构和生产常量比对；helper未import或执行、archive入口未调用，Go/SQL/native/API/private/model调用0，Main/CP/旧Source写入0，新增机械失败0。作者915以及Root914与历史912/913均保留各自原归属，不重计。

Root曾表示会补一个Snapshot→惰性archiveRequest Source，但截至此包封存未收到其精确pin，因此该Source为NOT_REVIEWED，本回执不推断其实现或允许执行。新helper revision和builder应一并delta复核；builder若在guard前预读也应遵守相同有限读量。

修正Source仍不等于实际归档闭合。最终必须针对当前真实Snapshot/Config/Payload和Root明确Entries执行归档，独立重核Original→Archived映射、完整57项加backup/rehearsal/ciphers与guard关闭，再按Root流程释放fixture。本审查不签收原Owner、九用例、迁移authority或42项正式验收。
