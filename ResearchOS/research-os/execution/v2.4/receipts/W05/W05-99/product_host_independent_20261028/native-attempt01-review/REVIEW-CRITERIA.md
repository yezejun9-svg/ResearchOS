# CP564 owned native attempt01 独立复核判据

执行 owner 为 Root；本 reviewer 不启动或操作产品进程，只读取封存原始回执。scope SHA256 `e4eb2b6dd6734abf76bfe7b9a13b95489adae9cbb9139bc2cb5a9e1172d2014d`，build04/commit448af，隔离数据根和回执根以 scope 为准。

只有实际完成且输入未漂移的支路可接受。没有 outer exit、真实阶段回执或 OS 观察的阶段保持未完成；controller 声明不得替代这些原件。失败时保留状态，不自动重启、关机、结束进程或清理。

核对项目：

- scope、wrapper、driver、builder marker、工具和 before/after 绑定；只读原件副本必须保留原始 hash。
- version/help/doctor 的退出码、JSONL、隔离根；doctor 未就绪应明确 NOT_FOUND，不能称健康检查通过。
- 第一 GUI 真实 parent/Core/witness/native host.status；重复 GUI 与并行 CLI 不能产生第二 host。
- 精确 PID/image/creation 限制的原生目录选择；Unicode owned workspace/project、无凭据离线配置、session.create/open/get 四类身份贯通。
- GUI 正常关闭经既有 safeExit，观测确切 parent/Core 均退出、witness退役；同非空数据 GUI 重开，再经 CLI 冷启动，保留 project/session/workspace/model。
- 三轮 host identity 应变化、installation/data 应保持；必须核对原始 typed response 与进程观察，不能只计断言数。
- 截图只能证明所见 UI，不能替代真实 API/OS 结果。零 provider 计数只约束此运行监听范围，且源码禁止 provider/probe/send。
- 正式增量恒为0。busy、STARTING竞争、installer、clean Windows、升级/回滚/卸载、C57、真实模型调用和全部父任务/用例仍在本范围之外。

原 source/build 接受、所有历史失败、两条拒绝清理命令和既有报告均不修改。
