独立整链 Source 结论：REQUEST_CHANGES。controller v3 与已通过窄审的 observer v2 已修复多项旧问题，但仍有3项源码缺口，不能签 READY_SOURCE_ONLY。没有执行候选入口、真实Windows API、SQL、SDK或provider，也没有写Main/canonical。

范围与结果

固定controller273523f5.../17627，canonical transaction094e1a97.../6877，watchdog0c859dfc.../2705，observer7077b2b7.../31072，runner仍为v8的5b112a08.../90096。Root六个源码文件仅做compile检查；新两依赖literal path/hash/bytes均与实际固定文件相符。26项输入出口复核前读取无漂移，controller正向/逆向diff逐字互还；只改activate/close/launch，pinned与cleanup_confirmed保持v2已审查字节结构，三个旧依赖原文字节未变。

复用observer v2已封39项独立检查，不重跑。此轮新增21项纯AST/内存检查：18项符合预期，3个应拒绝/清理反例揭示2项问题；再有1项静态文件加载边界问题。两个canonical反例属于同一部分close问题，不重复计数。所有WinAPI名称仅是Python内存替身接口，没有真实OS调用；watchdog用确定性的线程/event/clock替身，不是真实超时实验。

V3-R01 / P2 / CTRL-R02残留

canonical_transactions.py 77-99 与controller.py 63-78、100-111。share0同时持有两现存文件确实覆盖了read/compare/write/verify，旧read-check→replace竞态在源码结构上消除。旧expected bytes、第二文件取锁失败、transform失败均正确阻止写入。

但close按checkpoint→ownership写入。独立内存故障在第二个文件写入时报错，此时checkpoint active UUID已清空、ownership仍ACTIVE，failed.partial原文存在且句柄关闭。下一次显式activate使用当前pins时只检查checkpoint active为空，未检查旧ownership活跃状态或未完成事务，可以覆盖原ownership并接纳新UUID。本控件不是候选自动retry；它证明了reconciliation-required原文没有成为下次admission的硬门槛。应增加持久未完成事务门槛或成对lease状态检查，阻止未协调部分close后重新admit。

V3-R02 / P2 / CTRL-R05清理残留

job_deadline_watchdog.py 33-43 与controller.py 180-183、242-259。源码已把独立timer放到callback工作前，正常计时模型能按实际更紧deadline请求TerminateJobObject；终止失败、CloseHandle失败和join后仍存活的线程也能标记未确认，controller会把这些错误计入native result并保留lease。这些正向边界已确认。

新反例是DuplicateHandle后Thread对象已赋值，但Thread.start()异常。stop_and_close随后直接join未启动线程，再次抛RuntimeError，CloseHandle步骤未执行。controller finally在这个调用处退出，后续phase-launch.invocation封存也被跳过。应追踪成功启动状态，隔离start/join/close异常并确保安全清理分支执行；controller即使watchdog清理抛错，也应继续保留原始native result、第一失败及未确认lease。

V3-R03 / P1 / CTRL-R06残留

controller.py 175-179、207-230，observer v2 validate_launch_inputs及phase_worker入口。新的六ref/context和observer v2已能绑定实际argv、cwd、worker/Python pin及八键环境；但这是观察时的文件字节绑定。

observer把worker_raw编译后丢弃code object，返回argv与pins；实际Python仍在Resume后打开worker文件路径。最后一次observer pin/compile与实际打开之间，controller没有对worker文件保持禁止写入/删除的所有权，也没有让进程消费那个已验证buffer。文件在这个区间改变时，PID/Job/argv/cwd都可保持正确，最终代码却可能不同。该缺口需真正文件不可变性或稳定执行buffer协议，不能靠再补一次hash或self-reported intent关闭。此项仅作静态消费序列与内存timeline分析，没有实际改动/执行worker。

旧六项的当前状态

CTRL-R01保留未确认清理lease的gate和CTRL-R03单次verified buffer读取保持通过；CTRL-R04由v3八键gate与observer v2 exact basis环境共同闭合。CTRL-R02的并发锁窗口修复，但部分close的reconciliation admission仍有缺口。CTRL-R05正常callback时限路径补上，但线程启动失败的清理仍有缺口。CTRL-R06的argv/cwd/source tuple修复，实际文件加载不可变性仍未闭合。

真实Job、sharing ownership、watchdog及callback探针仍是OPEN；Host资格admission、所有子树归属和停止、当前phase seed/完整Python运行时选择也未由本Source审查证明。未评审随后通知的SDK v9提案，不能将v8结论迁移到v9。

失败与权限

本轮新增工具失败为0。之前observer窄审的失败682及Root其他任务后来通报的计数不在此包复计；没有读取或修改canonical计数。原始工具I/O、Source snapshots、21项独立控件、3项finding及输入出口pins均随包封存。

正式schema保持researchos.mu-sdk-controller-observer-independent-source-review.v2，但decision=REQUEST_CHANGES；Root当前phase seed没有提供一个已选定的Python binary pin，本拒绝报告保留python_binary_ref=null，不能被误用于启动。formal_acceptance=false、execution_ready=false。新版本修复后必须重新绑定相关Source refs并独立复核。

