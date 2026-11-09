Task90 独立 Source 结论：REQUEST_CHANGES_SOURCE_ONLY。存在 1 个必须修复的证据保存问题 PUBLIC21-OBSERVATION-001；本审查不签发执行 grant、Root issuer、组件通过或正式 acceptance。

PUBLIC21-OBSERVATION-001（P2）：public21_runner.py 第 173 行把 observation、actual_exit、ended_at_unix_ns 与 stdout/stderr observed_ref 放进同一次 invocation.update 调用。Python 会先求值所有参数，后执行 update。若子进程已返回，但其中任一输出文件的读取或哈希抛出 OSError，update 根本不执行：invocation 中的已知 actual_exit 和完整 OwnedJob cleanup 仍为初始 null。第 194 行的失败记录因此也把 last_child_exit 记为 null。已经取得的真实执行与清理证据丢失，违反 contract 的停止分支必须保留实际 stdout/stderr/call results、实际退出码或确实未知的 NULL 的要求。

独立反例只从当前固定 SHA256 源码提取第 173 行的原始 AST 语句，以内存中的 synthetic job 返回值分别注入 stdout 和 stderr 读取失败。两种情况均确认实际已提供的 synthetic actual_exit=0 与 closed cleanup 未写入 invocation。该 0 仅是数据流反例输入，不是 native 成功。没有调用 run_registered_case、创建 Root scope、执行 SQL、运行 Go 或启动 native；作者已有 56 项控制未重跑。这两项是新增未覆盖异常路径的纯 Source 控制，预期注入异常已捕获，不属于新的实际机械失败。

建议最小修复：在任何输出文件读取、哈希或 receipt 写入之前，将 run_owned 返回的完整 observation、实际退出码和结束时间独立保存到 invocation；后续分别处理 stdout/stderr pins 和 result receipt 的失败，并在返回状态中保留已知 Job 结果、清理事实及具体 artifact failure。不要把实际已知退出码降为 null，也不要因此自动重跑同一输入。修订后仅补验这些新异常分支，不重跑已有 56 项作者控制。

其它已验证边界：
- HDF/MF 与全部 78 个 manifest 成员 pin 匹配；交付目录实际为 80 文件，仅 MF 自身与引用 MF 的 HDF 按声明排除。
- 真实 Root-bound old21 programme qualification 的 SHA256 为 8b5d6565586e51be741fa25b2f79cf41c55d0f8733c43d0f6a60f2ebca738a70，5911 bytes；两程序、source commit/tree 与 contract 一致，programme qualification 不含 execution grant。
- 实际 frozen SQL 文件编号恰为 1..21，next_v24_sessions.sql 是独立非编号 addon；真实 domain.New 在同一事务应用编号迁移、addon 与 installClientSessionFence。没有伪造 ledger 或 Source 创建数据库。
- 固定 Control argv 只有 --bootstrap-owner --credential-file；cwd 为 frozen_source，RESEARCHOS_DATA_DIR 指向新的 source21。该公开管理分支在 HTTP server 路径前 return；私有 Owner 文件由程序生成，15 分钟生命周期，Windows DACL 由系统 API 设置，runner 不读取/复制/哈希该文件内容。
- 仅有一个 run_owned 调用，90 秒有限期限；复用的固定 OwnedJob 实现先 suspended 创建、assign-before-resume，finally 处理进程及所有持有句柄。成功门验证 actual_exit=0、PID/精确 FILETIME、primary exited、Job idle、零 active、handles closed 和无 cleanup error，之后才进入数据库 oracle。
- 数据库 oracle 使用既有固定 helper 的 ro+immutable+query_only，拒绝非空 sidecar，先设置只读并持有 SourceReadGuard，再校验 ledger/schema/table hashes/integrity/foreign keys 和前后 DB bytes；不输出原始行。
- 新 PUBLIC21_BOOTSTRAP_ONLY、动态 current4/owner/有限 lease、独立 Source review、真实 Root issuance/peer capture 和完整 Python/SQLite/native 资源 qualification 仍是未来独立 Root caller 的前提。leaf 的 7-key/6-key JSON binding 只检查结构和 pins，不形成身份或授权。所有 future refs 仍为 null。
- 作者 29 组实际 host 三行记录逐组核验 call/output IDs、真实 author/parent 身份、行长度与 SHA256，并与其引用原始文件的指定 offsets 逐字节比较。未生成或推断尚未返回的 final sealer 原始输出。
- 作者三份 Source guard 闭合记录分别包含 62、7、139 条输入；均 closed=true、retained_handles_count=0、errors=[]、verification=PASSED。

本 Reviewer 对 146 个固定输入持有真实 SourceReadGuard，结束时全部关闭且 SHA256/bytes 无漂移。输入保护包括交付包、programme/native 程序 pins、真实 SQL、共享 helpers 和补充源码。小于等于 2 MiB 的公开输入另有复制索引；较大程序/build.closed 以原路径精确 pin 核验，没有重复复制。只写指定的新 review namespace，未写 Source/Main/canonical；原失败计数未重置，新增实际机械失败为 0。

实际审查工具 b9de9c：outer=0、ROOT_PYTHON_EXIT=0。该结果证明审查脚本及反例检查完成，不表示被审查 Source 已通过。20→24、backup/restore、W05-99 A04/C11/C15、22 parents/42 formal gates 均未获得新验收。修订 Source 后重新独立复核；本轮封包后 STOP。

