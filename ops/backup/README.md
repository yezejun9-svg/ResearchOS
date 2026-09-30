# 本机备份与恢复

本入口是本机运维命令，不向 HTTP、执行器或候选暴露。需要已具备原数据库文件读取权限，恢复密钥必须独立保管。运行前使用当前版本固定 Go，并在仓库根目录执行。

```powershell
go run ./ops/backup keygen --key-file D:/private/researchos-recovery.key
go run ./ops/backup create --db D:/researchos/state.sqlite --out D:/backups/researchos-20260930 --key-file D:/private/researchos-recovery.key
go run ./ops/backup restore --backup D:/backups/researchos-20260930 --out D:/restored/researchos-20260930 --key-file D:/private/researchos-recovery.key
```

父目录由使用者选择；keygen 不创建密钥目录、不覆盖已有密钥。备份/恢复目标必须不存在。磁盘不足、密钥错误、缺文件、内容损坏、版本不兼容均返回非零，不清理旧备份或原实例。每个命令只清理自己新建的 staging 目录。突然断电遗留 `.researchos-backup-stage-*` 不会被视作有效备份；重新执行使用新 staging，不删除其他进程或旧失败目录。

`VACUUM INTO` 从 SQLite 获取事务一致快照，包含 WAL 已提交状态、版本、验收、来源、outbox、费用、幂等记录与封存 BLOB。产物文件和可移植 JSON 均从同一快照导出。清单列出 hash、数据库 migration 序列、实体版本摘要、开始时间和完成时间；备份点位于该窗口，完成后的写入不受本包覆盖。SQLite 说明：[VACUUM INTO consistency](https://www.sqlite.org/lang_vacuum.html)。

备份文件全部 AES-256-GCM 加密，清单 HMAC-SHA256。数据库含幂等响应中的短期租约，因此不能明文打包。密钥不写入包或日志；恢复必须获得独立密钥。外部 provider 密钥从未导出，数据库仅保留其引用；外部后端不可用时相应调用仍阻塞。`VERIFIER_ONLY` 等受限产物整包拒绝，待 W17 的受控备份身份与隔离资格，不以本包绕过。

恢复会撤销旧会话凭据、重定位本地来源根、重建封存来源文件。当前项目及历史验收 hash 不改写；活动 Run 改为 `RECONCILING`，旧租约过期。所有未完成外部动作（含备份时 PREPARED）进入 UNKNOWN，因为它们可能在备份点之后已执行。必须先对账再使用现有 W12 ResumeCheckpoint；数据库触发器要求恢复之后的新可信进程观察，旧快照观察不能解锁。恢复过程不启动 Worker，不调用外部服务，不发通知。内部 outbox 由原 event ID 去重；外部渠道恢复需要 provider 对账。

`restore-report.json` 记录前后计数、实体摘要、恢复耗时及预期差异。FTS 缓存随 SQLite 保留；外部 worker 工作区、物化上下文和检索进程缓存不属于权威数据，需从封存产物重建。源目录不会作为恢复实例的读取后备。

迁移流程：先 create、再向新隔离目录 restore 并演练候选迁移。`RestoreOptions.Migration` 仅在未发布隔离副本执行；失败丢弃该副本，稳定包保持不变。不可逆迁移拒绝自动晋升；不支持降级时使用匹配程序版本重新恢复旧包。现有应用自动迁移启动入口尚需 root 串行接入此预备份流程；本工具不宣称替换了那个入口。
