# W09 SS 单行追加 helper 非作者 Source 审查

结论：CHANGES_REQUIRED_BEFORE_ROOT_SS_APPEND。审查对象仅为 bf391cd9531988a02b4fbd0f7b43d80f33ae719e0f7bf7e39b0f1f1040d034df / 6820 bytes；不建议 Root 执行这一版本。

两个阻断点：

1. SourceGuard 未持有 Main precheck 的全部非SS依赖、owner evidence和 actual_audit 返回的原始capture。一次 recheck 后还有归档与intent写入窗口；文件可以在替换SS前漂移。refs合并还会重新pin文件，未严格保留输入expected hash。最小修正是按物理身份去重、冲突拒绝，保留expected SHA，完整纳入非SS依赖并持有至提交回执；guard取得后重核批准/audit/precheck。只精确排除将被原子替换的SS。audit_ranges和inventory仍须正确复核，不能锁住整个活跃审计日志来阻止合法追加。
2. 原 atomic_state/writer_lock AST 虽被正确提取，却绑定了本地较弱的 path_in。它会解析link并允许指向仓库内另一文件，使原子替换可能落在该解析目标，同时回执仍宣称only_SS_written；而原path_in拒绝symlink/junction/drive/traversal。最小修正是一并复用原path_in及Refusal/need、exclusive、sha和PureWindowsPath依赖，保持原共享锁路径。

已有正确边界：固定原Source hash；提取FunctionDef保留contextmanager装饰器；指定Backup真实approval audit及exact owner/precheck ref比较；锁内current4与full SS CAS；拒绝既有W09-99；deepcopy追加一行并验证完整逆操作；原始SS/desired/intent先xb+fsync；没有自动回滚；committed明确postcommit derivation pending。以上仅为Source判断。

补充：原行内容保留是JSON语义层面，raw原文已归档。建议使用strict JSON解码并禁止NaN，避免重复键折叠。intent最好直接记录原始归档ref，当前before_ref指向会变动的canonical SS。helper异常只有finally清理；Root外层必须保留原始异常与当前SS真相，不能让清理错误覆盖首次失败，也不能在postderive失败时自动写回original。

本轮只做AST/字节与源码阅读，未导入或运行待审helper、register CLI、formal review、Native/Go/SQL；未读取或修改活动SS/Canon。无需重跑已成功的正式复核；修订后只复核新Source差异和相关metadata边界。
