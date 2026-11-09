# ONLINE backup Source resource map

状态：`EXISTING_PRODUCTION_INTERFACE_IDENTIFIED_NOT_LIVE_QUALIFIED`。本轮只读 Main `4f4023c956f84d65743f39ce77d6c8899a21ada1` 的 Source，未连接当前数据库、Host API、私钥、provider，也未生成备份或运行夹具。formal 增量 0。

`internal/domain/backup.go:362` 的 `Service.CreateBackup` 和 `backup_workspace.go:88` 的 `CreateBackupWithWorkspaces` 已是真实生产接口。`ops/backup/main.go:195-214` 的 `backup create` 打开现有数据库，按活动 WorkspaceBinding 数量选择普通或含工作区分支；此入口本身没有先 AcquireDataRootLease。这使它成为 Core 在线持有产品根租约时的候选备份路径，不能仅因没有独占根租约就断言没有备份能力。

数据库快照在 `backup.go:380` 通过 `VACUUM INTO` 写到新 staging。之后的 integrity/schema/runtime/inventory/queue/sealed-content 导出均针对生成的快照连接。上传内容和所有 Artifact 历史版本在快照中验证 hash；stage 的 SQLite 被关闭后加密，manifest/MAC 校验后发布到原本不存在的 destination。这里描述已读源码接线，不代替 SQLite 一致性语义的独立资格验证或真实恢复证明。

含工作区分支有额外前提：`ops/backup/main.go:210` 调用 `Host.New`。该构造函数会创建/设置 Host 私有目录权限、调用 NewCurrentMu、打开 vault/root registry/selection store/Host state。它不能当作只读状态查询。`Host.SnapshotWorkspace` 还要求当前 bound principal、非撤销 pinned root、原始文件身份、无 reparse/递归路径和逐文件稳定性，并在文件/目录/字节上限外拒绝而不跳过。因此目前不能声称此命令已适配当前根的所有实际工作区或不会发生正常初始化副作用。

`backup_command_queue.go` 保存四类客户端队列表及绑定关系，校验主体、Run/epoch、请求/receipt/idempotency/process identity 和内容 hash。已读校验没有简单地要求每条队列都终态；不能把原 UNKNOWN 自动当成“不准备份”，也不能从静态检查推导当前根一定通过。原 UNKNOWN/ACK/cost 等应按快照原样保留。

候选备份格式明确标注 key 与包分开存储、恢复后 credentials 需要 fresh provisioning。它不是将全部 Host 私有文件原样恢复的承诺。未来 boot arm 所需“可用”必须包含确实可恢复、同主体历史可追溯，以及凭证/RootBinding 再建立的具体可行步骤。

进入当前根操作前最小资格切面为：在隔离 schema24 根内，一个真实进程继续持有产品 DataRootLease；另一个真实编译的 backup CLI 对同一根执行 create；分别覆盖没有工作区与有已绑定小型工作区、UNKNOWN Run/effect/queue/history 的样本。验证源逻辑全表不变集合、快照时间点、密文/MAC、restore 后原历史与内容，以及 root lease 未被抢占、没有 worker/model/provider 调用。Host 构造的所有原根初始化/文件权限变化须明确观测和许可，不能把副作用藏在“读备份”描述内。

这项资格测试尚未执行。实际活动工作区数量、资源上限适用性、现有可用加密恢复 key、当前根的正常 Host 初始化条件和真实 restore 可用性均没有在本 Source 卡中探测。它们是明确待核对的资源，不是永久无解的结论，也不要求先对当前根盲跑命令。

Root 可在两张现有 Source 修复卡之外的独立测试资格范围内，安排上述少量 fresh fixtures；通过后仍须单独接受实际备份计划，再进入原始根。此 map 不授予 SourceC、backup CLI 当前根执行、启动围栏或用户 Restart 权限。
