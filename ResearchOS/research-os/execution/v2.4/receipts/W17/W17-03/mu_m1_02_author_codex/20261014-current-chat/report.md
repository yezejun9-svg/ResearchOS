# M1-02 作者交付，等待独立实现复核

隔离组合已实现 canonical PAUSE、durable checkpoint seal、同一 Run 的原生 SDK 续跑和队列恢复。源码冻结为 `ff5ac2047566a52388188b84f267217d8582c571`，tree `e5792b72e0380af65fa1cc5f8b122399c1366d9b`，精确 17 文件；schema25 的 9 个依赖和 M1-01 未改。Root 是唯一集成者。本报告不是独立接受，正式增量 0。

最终真实 Host / HTTP / coordinator / AppContainer 三用例全部通过（attempt-017，51.035s）：暂停后续跑、暂停后取消、提交后的 PREPARED lease 丢失恢复。续跑保持 Run id 和 attempt，epoch 1→2，原生 stop/drain/cleanup 成立，typed seal ACK 后恰有一个 turn.paused；实际 Host write 仅一次。暂停队列 CONSUMED/SDK_ACCEPTED/ENQUEUED 为 1/2/1，最终四条各消费一次。模型为本地 synthetic；两条续跑用例各 6 次模型调用（含资格 1 次），取消用例 3 次，无真实 provider 调用。

事务回滚用例在 activation INSERT 注入失败，证明 epoch/activation/carry 全部回滚。prepared 恢复用例在最后 Task 写入撤销 requester，让新进程启动前拒绝并失去内存 lease；重新确认当前权限后，在同一个 epoch=2 更换 lease，activation/carry 仍各一条。这是提交后未启动故障注入，不宣传为整应用 OS crash。STARTED、worker/identity/journal 已存在及取消/restore/foreign fence 的禁止重启另有边界夹具。

最终 domain pause + 真实 pinned Mu queue/cancel/Goal 排序回归通过（attempt-018，33.295s）；此前 ordinary controls、checkpoint rebuild、schema25、队列备份回归通过（attempt-014，21.320s）。所有 18 次执行日志完整保留；7 次失败调用中含 1 次编译失败、6 次测试失败，详见 attempt-ledger。没有删除失败或重置计数。

旧 coordinator 回归中两项未通过：`TestRuntimeCoordinatorCheckpointResume`、`TestRuntimeCoordinatorCheckpointCrashRecovery`。根因为冻结 M1-01 对旧 inline checkpoint 无条件采用 V1 file checkpoint；在冻结 M1-01 worktree 已直接复现第一项同样失败。其余该轮原生 qualification、typed broker、purpose revoke、heartbeat、effect crash、controller crash 回归通过。详见 legacy-checkpoint-compatibility.md；Root 已另行登记兼容债，不在本次 exact17 内修改。

实现入口：runtime_pause.go 保存当前 Owner 授权、CAS/full-row witness、effects cut 和严格 Task 生命周期例外；runtime_pause_windows.go 处理 captured bytes、seal ACK、confirmed native stop、窄 sealed activation gate、原子 successor 和无启动证据的 lease 恢复。窄 gate 重新验证初始化能力回执、原 dispatch/process/input、原 sealed bytes/use、STOPPED/typed ACK、SDK metadata、旧/新 use principal、immutable activation/request/carry、当前 session/Goal/Owner/cancel/queue。新 manifest 带必须存在 activation 的 marker；缺 schema/activation 不得退回普通执行。普通 supports_resume=false/null 与公共状态图保持原契约。

边界：未做生产 DB、API/provider、GUI 操作；未发布普通 Main/package，未执行真实 schema24 升级。SENDING/UNKNOWN 若原回执恢复仍无法确认则阻塞，不盲重发。所有成功证据为 NATIVE_SYNTHETIC 或 fixture/source，不能替代 LIVE、独立实现复核、22 父任务或 42 正式用例接受。

审查定位：`source-manifest.json`、`source.patch`、`attempt-ledger.json`、`report.json`。最终 native 证据目录：`D:\作品集\ResearchOS\research-os\.local\mu-m1-core-20261014\native-attempt-017`。report.json SHA-256 `56e709f7ae1af2c60dfe62fb3f517789989a63b63f0f3cfa61b753e6f9bca8ef`。
