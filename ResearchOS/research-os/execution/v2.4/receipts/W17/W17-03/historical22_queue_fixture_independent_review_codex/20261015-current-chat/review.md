# Historical22 fixture 独立 Source 审查

结论：**LIMITED_SOURCE_ACCEPTED**。候选 `6802628826dcc4b79a16ced20a8e26f7e5494a1b` 相对 `2a2d939c5f1e86156c4f5fe55e07b3a5d4fd4b02` 只修改 `internal/domain/backup_configuration_upgrade_test.go`。限定接受历史夹具来源替换；没有发现阻断该 exact1 Source 接受的缺陷。

新鲜执行 `ActiveQueueRecovery`、`Frozen22ProgramLock`、`NativeCLI` 三项均 PASS，零 skip。四个负向运行分别缺记录、错记录 pin、错 DB pin、错行快照 pin，均 native1 且出现对应拒绝原因；这些 FAIL 原样保留，不能写成“全部命令成功”。独立只读检查实际 SQLite 快照及输入执行 22 个命名断言；现有八个丢表/历史连续性负向分支均对应非空表，不会因空夹具跳过。Go 本身未输出总断言数，不虚构总数。

已逐项核对冻结范围及作者最终引用链、502 个归档/源码文件、5922 个先前编译输入（495 个路径映射到重建根）、29 个本机程序/发布输入以及 helper/编译程序 hash。重建根唯一额外文件是 `active_queue_fixture_child_test.go`。历史 Git tree `458e375ec2be0b989bb9b9e3d487f969e3c62966` 仍缺失；该证据证明选定 502 文件归档的字节来源，不证明完整 Git tree checkout。

helper 经 `goalCommand` 解码、事务及实际旧版 `ClientService.Execute` 完成 1 次 goal.start、7 次 session.send、1 次 session.control；Run 经旧版公开任务 claim 路径生成，effect 经 Prepare/Begin/Observe API 进入 UNKNOWN。六个中间队列状态由 `appendClientReceipt + UPDATE` 合成；跨进程工作区由 Project/WorkspaceBinding 当前对象路径及 content_hash 重绑定。两者均是明确的夹具处理，不是 SDK/provider 真实阶段执行，也不是一般产品路径变更迁移的证明。没有注入 schema23 identities。

原库用 mode=ro 检查，schema min/max/count 为 1/22/22，identities 表不存在。七相位合成后，公开 CANCEL 将 ENQUEUED 改为 DROPPED，将 SENDING/SDK_ACCEPTED 改为 DROP_REQUESTED；所以最终旧库是 CONSUMED1/DROPPED2/DROP_REQUESTED3/UNKNOWN1。迁移后仍有七条相同 generation/sequence 队列记录，其中 UNKNOWN4；控制请求 RECONCILING1；Run 同 epoch、token 更换、lease 过期且 revision+1；effect 保留原三条历史并追加 UNKNOWN fence；idempotency 与 runtime_dispatches 保持逐行类型和值，零 dispatch；新 identities 表为空。原 DB/helper/record 字节不变。

环境 pin 的信任来自本次冻结范围，不来自任意调用者自填 hash。该 exact1 测试消费外部记录、DB、稳定工作区和旧/新程序；纯净 CI 环境尚无可移植性证明。后续集成必须提供本回执验证过的 artifact 集及相同受控 env，并保留缺资源明确失败。该条件不扩大成本轮 Main、打包或正式接受。

失败历史保持完整：作者 18 次尝试中 7 次失败、旧 T3 三项失败均保留。本审查第一次把最终队列误设为七种状态各一条，纠正前的检查失败已保留；原探索查询的路径/编码诊断也保留。整体 Main 守卫首次失败是 Root 同期 CP499→CP500 更新 HANDOFF/checkpoint/path_ownership 三文件，已用 Root before.raw 字节及回执归因；原 FAIL 不覆盖，其余17个脏文件、HEAD、空 index、Source/helper/DB 均不变。

本次临时目录 `.local/builds/historical22-independent-review-20261015` 的精确 PowerShell 清理被自动批准审查以 `blocked by policy` 拒绝，命令未执行，目录保留；未更换工具绕过。所有实际测试 argv/cwd/allowlist env/native exit/raw logs 与快照均在此回执目录，`evidence-manifest.json` 冻结文件 hash。

没有 Main 集成、原实际数据库迁移、package 接受、模型/provider 调用、stop/signature、旧 UNKNOWN Run 重放或正式增量。正式仍为 0/42，22 个父任务仍 OPEN。
