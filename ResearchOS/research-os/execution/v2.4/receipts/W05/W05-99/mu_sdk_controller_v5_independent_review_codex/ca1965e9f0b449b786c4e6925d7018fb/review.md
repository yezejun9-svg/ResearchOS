C5 Controller 独立 Source 审查

结论：REQUEST_CHANGES，2 个 P1：C5-R01（当前作者可自签独立 review）与 C5-R02（reconcile 接受未绑定真实来源的 cleanup 字典，并接受未来时间）。不发 whole Source READY，不把本轮纯内存控制当成实际 Windows 生命周期证明。

C4 原问题的直接分支已经修复。结果为 None、仍有 active child、cleanup errors、active count 为 bool/float 时，Source guard 和 watchdog 均不 close，记录进入 RETAINED_UNCONFIRMED，强引用由当前 PID 的 sys-anchored owner 保留。outer finally 遇到中断的 NATIVE_INVOKED 也只 retain。PRE_NATIVE 能证明从未调用 native，允许清理；正常确认 cleanup 先在 Guard 内加载 canonical transaction，再关闭 Source guard。Guard/duplicate 清理失败时保留对象。owner 跨 PID 调用被拒绝；本机制只在该 PID 存活期间有效。

C5-R01：C5 handoff 的作者是 codex:/root/live_resource_lookup，但 controller 的 review actor 拒绝名单仍仅 Root/w05；O3 的拒绝名单同样没有当前 controller 作者。独立构造了其他全部字段和六 refs 合法的 review，两处实际 AST gate 都接受该作者。应在当前 tuple 的实际准入边界绑定所有 Source 作者，拒绝任一作者自行签发 independent review；不能只沿用上一版的作者名单。

C5-R02：reconcile 接受任意 callable，只检查返回值的 run_uuid、owner_pid、observed_monotonic>=retained 和 cleanup 字典形状。独立控制在 now=100、retained=100 时传入 observed=1000000，函数仍关闭 guard/watchdog 并删除 owner 记录。另一个完全未被审查或绑定到 retained Job 的 callable，只要返回同样的字典便能释放；附加 foreign producer/Job 标记也被忽略。这不是要求当前 schema 凭空支持某个字段，而是说明真实 cleanup 来源与 Job 身份根本没有进入强制条件。需要将已审、精确 pin、受 Source 保护的 producer 与 retained Job/child 身份绑定，并使用有限且落在本次 fresh call 开始至返回之间的时间；任何来源、身份或观测缺口都必须继续 retain。实际 Root 常驻进程和 producer 的未来 wiring 可以保持 LIVE_INTEGRATION_OPEN，但 Source 的释放接口本身必须先具备这些强制条件。

新增 26 项独立纯控制中 23 符合，3 个反例归上述 2 个 finding。控制只编译选定 AST 方法、finally 块和判断式，PID/时钟/RLock/sys/Guard/watchdog/transaction 都使用独立内存替身，没有真实线程、WinAPI 或 native 调用；callback 的形状阳性仅验证解析路径，不表示获得了实际 cleanup 证据。作者 20 项控制未执行、未当成独审。

C4 到 C5 的完整正逆 diff 均独立应用并精确恢复，五个 helper 字节不变；仅 cleanup_confirmed、close_canonical_lease、inner/outer launch 改动，并新增 resident owner/reconcile 支持。O3/v9 的原独审、Guard v2 的 31+28 控制及实际私有目标 probe 原封结果复用，未重跑 39/8/31/28 或任何 native probe。本轮 50 条输入记录无漂移，0 新增工具失败。作者 699-701 在 Source 包中是开发失败摘要，本审查不把该摘要冒充完整原 IO，也不重新计数。

六个 Source/Python refs 均非 NULL、按当前 C5/O3/v9/固定 Python 精确绑定。Main/canonical/SQL/provider 未触碰。实际 Root resident caller、fresh cleanup producer、完整 Controller/Host 生命周期、资格与正式 SDK trial 仍 OPEN。
