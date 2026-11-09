# CP486 建议：R2周期心跳最小修复

建议修订仅允许以下 **2个文件**，都在原exact9内：

1. `internal/domain/runtime_coordinator_windows.go`
2. `internal/host/runtime_pause_windows_test.go`

基线为 HEAD `36b2634bfebe6201a14b7661f2dce32b7f1a5098`、tree `bea72c5cdbb341e4d67bd91331803ec6e8013e3b`。这是独立修订建议，不是实施或接受；本轮不改源码/Main/共享状态、不新增测试运行。

依据为冻结 `second-pause-revision01/report.md`，SHA-256 `71399c37bf175148c1ba8dc16cf83b8f41ffdae46e14781aa97cfce0b5e64713`；该审查manifest SHA-256 `91b8abb4112916426c0aefe095815c29bcaa35a1f63f44c09278c8f75b1f23a6`。原生复现显示第二次PAUSE返回200后保持原模型响应在途17秒，进程跨过真实15秒心跳即被取消，最终RECONCILING/UNKNOWN。

## 生产边界

缺口在coordinator第682行：周期调用没有purpose；第540行严格拒绝BLOCKED；第686–687行取消进程。pauseCheckpoint自己的同步heartbeat有purpose，无法替代等待在途effect期间的周期维护。

周期调用必须显式标记为 **Host周期维护心跳**。在与dispatch授权相同的事务及写锁内，读取当前Task、Run和当前epoch的pause intent，构造完整绑定的现有heartbeat purpose，再执行原dispatch/admission和`pauseDispatchPurposeGate`。可以在coordinator内增加专用入口或内部purpose分派；无需修改既有pause gate的允许条件。

必须避免先在独立查询中判断“当前不是暂停”，再走无purpose通用gate：PAUSE可能在两步之间提交，仍会导致合法暂停被误取消。当前暂停身份的选择与检查应在同一gate事务内完成。不得通过捕获BLOCKED错误后直接忽略、盲目续租，或弱化错误处理来规避竞态。

允许维护的暂停状态仅为当前精确绑定的PAUSE_REQUESTED、CHECKPOINT_SEALED；完整检查继续由现有gate负责：Task.active_run、当前epoch、pause_id及witness、dispatch_key、manifest_hash、process identity、session/generation、queue fence、PAUSE control、现有activation证明、当前Owner/Goal/executor/lease及admission。purpose只能由Host构造，不信任worker自报pause_id或历史Bridge快照。若借助Bridge字段，仍必须在gate事务内与canonical当前intent核对；Bridge尚未收到PAUSE不得造成合法canonical暂停被误判。

未暂停时保留普通心跳语义；没有当前合法intent的BLOCKED不能续命。PAUSED_CONFIRMED、RECONCILING、CANCELLED、错误绑定、撤销权限或Goal终止仍必须拒绝并走现有取消路径。普通dispatch、RunAdmitted/BeforeResume、legacy checkpoint、permission和effect准入不能从维护purpose继承权限。checkpoint显式传入的pause_id仍需精确匹配，不得被“自动选择当前intent”静默替换。

不改`runtime_pause_windows.go`、budget、permission、worker/Bridge协议、15秒心跳周期或90秒lease，也不扩普通supports_resume。若作者证明两个文件无法满足同事务选择，应先报告具体依赖再登记扩范围；不能为凑文件数牺牲上述边界。

## 精确测试要求

**A. 二轮模型暂停跨周期心跳。** 保留原审查的实际HTTP/AppContainer触发方式：同一Run首次恢复到epoch2后，保持既有模型响应在途，发送第二次PAUSE。在响应仍被测试端持有且Task仍BLOCKED期间，等待至少一次真实周期heartbeat成功，记录Run heartbeat_at在PAUSE提交后前进或成功heartbeat HTTP回执。等待上限必须跨15秒；仅延时但未记录成功维护不能算通过。此时不得新增模型请求、工具执行或queue consumption。再释放原响应，确认PAUSED_CONFIRMED、stopped/drained，显式RESUME至epoch3并settle；Run/attempt不变、两activation、队列各一次消费、预算各epoch RESERVE/RELEASE准确对应。

**B. 同一Run的两轮工具在途/发布前复核。** 一个实际原生流程覆盖epoch1和epoch2各一次工具阻塞，不能把原epoch1工具用例重复执行两遍当成两轮恢复。每轮均在Host工具已经准入、物理写入尚未发生的位置持有执行；通过普通HTTP PAUSE使Task成为BLOCKED，跨真实周期心跳并记录维护成功，再放行实际Host执行及物理发布回调Revalidate。用两次可区分的合法写入或明确预期内容/哈希证明每个原effect只发布一次；第二轮不得重放第一轮写入。两次确认暂停后分别显式恢复，最终同一Run/attempt为epoch3，工具总数和内容按固定synthetic脚本精确断言，queue逐key一次消费。保留每轮pause/stop、effect、workspace结果与最终预算ledger证据。

**C. 维护不延续失效权限。** 至少在原生暂停等待期间验证CANCEL以及Owner撤销两个分支：下一维护检查必须拒绝，原进程被停止/清理，不发生被持有工具的物理写入、额外模型调用或新继任epoch。继续执行既有Goal停止、缺intent、旧epoch、错pause/dispatch/identity/session、通用BLOCKED和effect cutoff反例；这些已有domain用例可原样运行，无须修改其文件。不得用通过A/B替代这些反例。

**D. 回归与竞态。** 原5个native用例和原13个domain用例保持通过、0 skip；正常未暂停的周期心跳也必须继续通过。应在测试中控制PAUSE提交与维护检查的交错，或明确通过同事务代码结构加针对性交错探针证明不会走“外部读无intent→PAUSE提交→通用gate误取消”路径。不得调整心跳间隔来让等待用例避开心跳。

独立完整预算successor回滚证据已经在revision01补齐，可原封保留；本次不需要重做预算实现。所有新运行记录实际argv/cwd/allowlist环境、数字exit、原始输出和前后source guard。失败与skip追加计数，原作者23/11/1skip、早期作者18/7、早期审查5/2、revision01审查5/2不得重置或重复累加。

这些要求仅决定下一候选的可审查性。需要新鲜独立复核后才能接受Source；正式增量仍0/42，22个父任务保持open。
