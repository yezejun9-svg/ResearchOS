独立审查结论：SOURCE_ACCEPTED_WITH_EXECUTION_GATES。LEGACY-ROLLBACK-001 的 Source 阻塞已修复；这不构成组件执行通过、ordinary 迁移通过或正式验收。

v2 仅修改 TestClientTranscriptIndexUpgradeRollsBackWithCallerTransaction：直接从 legacyTranscriptFixtureDatabase(t) 取得 schema-only db；同一个 db 执行 Begin 和回滚后的 QueryRow。事务内 installClientSessionFence(ctx, tx, false)、tx.QueryRow 的列存在断言、显式 Rollback、延迟 Rollback 和回滚后列不存在断言均保留。helper 在迁移前注册 db.Close 的 t.Cleanup。restored=false 的生产路径跳过 Run barrier seeding；空 session 表的安装操作不再依赖先复制 Project。此前“缺少 Project 导致 helper 提前返回、根本没有到达 Begin”的静态前置条件冲突已消除。运行时可达性仍待 Root 独立实测。

独立 Python 词法屏蔽与平衡括号检查重新计算了原始两文件的 12 个 Test 名称和 126 处断言调用，均完整保留；9 个无关测试体逐字节一致。该计数为静态源码验证，不是 Go AST 或编译结果。v2 的反向替换逐字节还原 v1 rollback 测试文件，另 3 个候选文件与 v1 完全相同。20 个真实编号 migration 的 Git blob 与固定历史来源匹配；旧 DDL 的 Git blob 为 9efc768f8f4cfb6ac31e1f88a78ad095877328af。

源 manifest 含 41 个成员。实际排除的是顶层 MF.json、自报后封包 postseal-tool-io.json 和 inputs/review/MF.json 副本。后两项已单独 pin：review MF 副本与旧独立审查原件 SHA256/字节数一致，postseal IO 的实际结果包含 outer=0 与 ROOT_PYTHON_EXIT=0。此处不把 basename 排除行为当作 manifest 内覆盖。

162 个输入通过真实 SourceReadGuard 锁定并独立核验；所有源、当前 canonical、Main、原包和旧审查包的受保护输入保持原始 SHA256/字节数。关闭报告 confirmed closed=true、retained_handles_count=0、errors=[]。本轮只写这个新审查 namespace，没有写候选源码、Main、T5/T6 或 canonical。

本审查保留机械错误 844：functions.exec 原始完整输入在 JavaScript 解析阶段失败，未进入 apply_patch/exec_command，未创建 Python/native 进程；actual outer、marked Python、native exit 均为 null。新入口仅修正脚本载体的反引号转义，实际审查 outer=0、ROOT_PYTHON_EXIT=0。未重置累计计数；Root 负责登记 844。

ordinary 保持 BLOCKED_HISTORICAL20_MATCHING_PROGRAM_BACKUP_RESTORE_UPGRADE。仍缺少匹配历史 20 的程序发布、真实 backup/restore 与获授权的升级链，不能使用组件或合成 fixture 替代。下一步只能由 Root 按独立执行门禁进行 fresh guarded compile/component 实测。本 Reviewer authority=NONE，formal_acceptance=false；交包后 STOP。

