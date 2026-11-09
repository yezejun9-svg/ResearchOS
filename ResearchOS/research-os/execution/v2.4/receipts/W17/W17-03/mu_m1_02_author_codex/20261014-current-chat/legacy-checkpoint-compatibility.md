# 冻结 M1-01 的旧 checkpoint 兼容性定位

结论：共享生产 Bridge 的旧 checkpoint 协议路由被 M1-01 收窄，属于产品代码兼容回归；已通过真实 AppContainer 的旧 adapter 协议夹具复现。没有读取用户生产数据或观察实际安装中的旧 worker，因此不能声称某个已部署任务已经因此失败。M1-02 未改这份冻结依赖，也未改旧用例。

证据：冻结 M1-01 worktree `c6f39e84fd0efa046a9651bb5542a4f3c6b4344b` 上的 `attempt-016-frozen-m1-01-baseline.log`，`TestRuntimeCoordinatorCheckpointResume` 在接收旧 inline checkpoint 时报 `invalid bound pause checkpoint`。当前组合上的 `attempt-015-coordinator-regression.log` 同时保留 `TestRuntimeCoordinatorCheckpointResume` 与 `TestRuntimeCoordinatorCheckpointCrashRecovery` 两项失败；其它原生调度、effects crash 和 controller crash 回归通过。

直接位置：`adapters/runtime/bridge_windows.go:410-414` 对所有 `checkpoint` 帧无条件调用 `capturePauseCheckpoint`；`:1011-1012` 要求已发 `command.pause`、固定 `pause-checkpoint.json`、V1 metadata 和当前绑定。后续 `:416-421` 的 `turn.paused`、`:632-646` 的 ACK，以及 `:851-852` 的离线恢复也无条件要求 V1 typed seal。因此只在 capture 处补一个判断还不够。

这条路由属于共享生产代码。`internal/domain/runtime_model.go:51-54` 对非 Mu backend 保留普通 profile 路径；`runtime_dispatch.go` 的公共 AppContainer dispatch 和 `runtime_coordinator_windows.go` 的旧 inline `checkpoint()` 分支仍存在。`durability.go:263` 的 `ResumeCheckpoint` 仍公开支持 `native_resume=false` 的 checkpoint/context 重建；其结果不能升级成 Mu SDK 原生会话恢复。旧测试通过真实进程、公共上传/封存 API 和 canonical checkpoint artifact/use 覆盖这些代码，并非纯 mock 检查。

建议另立最小兼容卡，首先限定 `adapters/runtime/bridge_windows.go` 和对应 native bridge 协议测试文件；只有测试证明 Core 分支也需要修正时再扩范围。使用 Host 已冻结的 request/manifest 协商结果选择协议，覆盖 frame ingest、ACK、paused terminal 和 offline read 四处：明确协商 V1 的 worker 永远走 typed file checkpoint，不得因 metadata 缺失/错误转回 inline；非 Mu、未协商 V1 的旧 adapter 才可走原有有界 inline checkpoint/ACK 契约。未知协议值、Mu worker 未协商却发送 checkpoint、混合两种协议、V1 的空 turn.paused 或弱 ACK 均拒绝。

验收应包含原有两个失败用例恢复通过，并保留 M1-01/M1-02 的 V1 typed ACK、12 MiB payload vs 64 KiB frame、no-reparse、内容哈希、wrong epoch/binding 和 missing seal 拒绝。新增交叉负例必须证明 V1 无 fallback，旧 context rebuild 仍回报 native_resume=false。此文是定位建议，不是修复或接受。
