# Main24 逐文件增量整合建议

状态：METADATA_ONLY_PENDING_ROOT_REVIEW。Root已指定 Native v2 b1599aaf259c435db5a0a5313ab0ea65。本包不修改Main/Canon、不执行Go/build/runtime/Native/SQL，不重放Source controls。

本轮40目标：{'APPLY_PINNED_INCREMENT': 10, 'ADD_ONLY_IF_STILL_ABSENT': 30}。10个已有文件均与其Source链声明的原始Main基底同字节，因此本轮没有额外Main侧分叉需要三方解冲突。30个新路径须在Root写入时再次确认不存在。这个结论只适用于observed_at快照，不能覆盖稍后编辑。

每个已有文件提供三种证据：当前ref、最终组合Source ref、祖先基底的HDF/MF指针；并有可逐字节审查的edit JSON及unified patch。edit JSON记录旧范围/旧hash、新文本/hash，以及保留区间，纯内存重建与目标Source同字节。它是未执行的建议，不能作为已合并或已通过运行测试的证据。

Root执行时先重核当前全文件hash，再核每个旧片段hash；按old_start_byte倒序应用增量，保留其他字节。若当前hash改变，不得强行应用或直接覆盖，应先保留新Main全文并重新计算三方差异。新文件若已出现则停止ADD，判断来源。Root实际gofmt后另行记录真实新hash。

先前指南中store保护的表述需精确理解：internal/domain/store.go的CheckMigrationSafety调用在当前Main已存在，本次该文件实际只新增authority字段；版本上界调整属于backup_migration.go。

## 已有文件

| 路径 | 变更位置（当前行） | 增量与保留内容 |
|---|---|---|
| internal/domain/store.go | 25(insert) | 仅增加 preparedAbandonmentAuthority 私有字段；现存 CheckMigrationSafety 调用保持原样。 |
| internal/domain/runtime_coordinator_windows.go | 941(insert), 973+1 | 恢复路径在锁内识别已 abandonment，Recover 查询排除有 proof 的 dispatch；保留其余恢复处理。 |
| internal/domain/backup_migration.go | 61+1 | 固定 inventory 上界23改24；连续版本及 populated DB prebackup 拒绝保持。 |
| apps/control/main.go | 34(insert) | 在原 fixture/正常启动分派前增加 maintenance 分派；保留原启动路径。 |
| internal/domain/backup.go | 60(insert), 527+1, 530+1, 581+1, 633+1, 694(insert) | 组合 Q workspace policy 与 handoff ordinary-public policy 四处检查及固定分支；旧加密、MAC、普通 workspace/protected-ref 检查保持。 |
| internal/domain/backup_configuration_upgrade_test.go | 21+1, 867+1, 873+1, 876+1 | 旧schema23 tests使用固定 release23 fixture；保留原期望版本及断言。 |
| internal/domain/backup_host_configuration.go | 82+1, 88(insert) | 固定24上界加 exact24 proof-schema 检查；其余<=23路径保持。 |
| internal/domain/backup_upgrade.go | 246(insert) | 添加固定 PreparedAbandonment 计划分派；原 configuration/queue/旧版本分支保持。 |
| internal/domain/backup_upgrade_test.go | 735+1, 762+1, 768+1, 771+1 | 仅version14 fixture Resume调用采用历史helper；其他版本仍用原ResumeCheckpoint。 |
| ops/backup/main.go | 28+1, 42(insert), 70+1, 76(insert) | 增加命令、两个binding flags与API分派；保留旧create/export/restore/upgrade-local。 |

## 新文件

| 路径 | 最终来源层 | 操作 |
|---|---|---|
| internal/domain/prepared_run_abandonment.go | Native-v2-candidate | ADD only if absent |
| internal/domain/prepared_run_abandonment_windows_test.go | PRA4 | ADD only if absent |
| migrations/sqlite/0024_prepared_run_abandonment.sql | PRA4 | ADD only if absent |
| apps/control/prepared_recovery_other.go | Native-v2-candidate | ADD only if absent |
| apps/control/prepared_recovery_windows.go | Native-v2-candidate | ADD only if absent |
| internal/domain/prepared_abandonment_authority.go | Native-v2-candidate | ADD only if absent |
| internal/domain/prepared_abandonment_authority_test.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/authority_test.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/enrollment_windows.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/history.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/history_test.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/migration.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/migration_windows.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/native_other.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/native_windows.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/native_windows_test.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/root_windows.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/transport_windows.go | Native-v2-candidate | ADD only if absent |
| internal/recoveryauthority/types.go | Native-v2-candidate | ADD only if absent |
| ops/supervisor/recovery_enrollment/main_windows.go | Native-v2-candidate | ADD only if absent |
| ops/supervisor/recovery_root/main_windows.go | Native-v2-candidate | ADD only if absent |
| internal/domain/backup_historical14_resume_test.go | Q-schema24-revision | ADD only if absent |
| internal/domain/backup_prepared_abandonment_upgrade.go | Q-schema24-revision | ADD only if absent |
| internal/domain/backup_prepared_abandonment_upgrade_other.go | Q-schema24-revision | ADD only if absent |
| internal/domain/backup_prepared_abandonment_upgrade_test.go | Q-schema24-revision | ADD only if absent |
| internal/domain/backup_prepared_abandonment_upgrade_windows.go | Q-schema24-revision | ADD only if absent |
| internal/domain/backup_prepared_abandonment_upgrade_windows_test.go | Q-schema24-revision | ADD only if absent |
| internal/domain/contracts/prepared_run_abandonment.sql | Q-schema24-revision | ADD only if absent |
| internal/domain/backup_prepared_abandonment_handoff.go | Public-handoff | ADD only if absent |
| internal/domain/backup_prepared_abandonment_handoff_test.go | Public-handoff | ADD only if absent |

完整SHA、bytes、逐路径base证据、差异范围及建议文件ref见file-merge-map.json。Source的四层合成顺序和实际Main23 binding来源沿用已封存配方，不在此重跑。

没有读取密钥、数据库或活动Canon。所有输入句柄已关闭；所有产物位于本包新namespace。
