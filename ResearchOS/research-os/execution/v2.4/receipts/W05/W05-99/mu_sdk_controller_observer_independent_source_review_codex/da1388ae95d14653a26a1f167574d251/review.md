独立结论：REQUEST_CHANGES。旧版 controller ddcf5458... 与 observer b062be8b... 的 Source 组合存在6项问题，不能签 READY_SOURCE_ONLY，也不能把本报告用作Root grant。没有执行候选模块、原生Job/WinAPI、产品SQL、SDK或provider，没有修改Main/canonical。

范围与证据

逐项核验Root controller封包及observer封包，共28个输入记录；读取时没有漂移。审查包括controller、owned_job_hooks、phase_worker、job_probe_worker、observer、v8runner和固定windows_owned_process依赖。只编译变换后的AST/code object，没有执行native-sensitive候选模块。31项独立检查中，7项用于controller/worker/hook，24项用于observer；原作者52项控件仅作为包内原文保留，没有重跑或当作独立证据。

独立controls.json复现了清理失败释放lease、canonical覆盖并发字段、pin双读以及环境投影遗漏；observer-controls.json进一步证明替换argv/cwd和增加未绑定环境变量仍通过相应guard。所有反例只用合成内存filesystem、frame/locals、code object和虚构公共字符串，不代表真实Windows运行结果，也没有触及实际canonical文件。

必须修复

CTRL-R01 / P1：controller.py 92-108、233。在实际exit/Job idle/handles尚未确认时，assert_native_closed会拒绝，但finally仍关闭canonical lease。反例active_processes=1、job_idle=false、handles_closed=false后，active UUID仍被清空且ownership记FAILED_EXECUTION_CLOSED。下一次activate允许active为空，因而旧子树未确认停止时可再次接纳trial。应保留active UUID和明确未确认清理状态，只在真实终结证据满足后释放。

CTRL-R02 / P1：controller.py 85-87、104-105。读取并比较raw之后的两次replace不是原子CAS。内存调度器在ownership更新时插入checkpoint revision350和新字段，后续checkpoint被写回revision342和旧字段。需要覆盖读取、校验与整组变更的真实独占writer/CAS路径，或把canonical写入交回Root已有的串行事务接口。准备write-intent有助于部分写入恢复，但不能阻止此竞态。

CTRL-R03 / P1：controller.py 25-33。pinned先用pin(path)读取校验，又用path.read_bytes返回另一份raw；module实际编译第二份。独立变更reader返回的第二份与被审查hash不一致却被接受。应一次读取并检查、返回相同buffer，解析与执行均消费这个已检查buffer。

CTRL-R04 / P2：controller.py 130、161、193、217，以及observer.py 125-155、319-325。public_environment完整写原文intent并传CreateProcess，basis只保留八项allowlist和两个CLI路径。独立额外变量不改变basis，observer的frame检查也只比较两份自报的完整map，仍接受。必须在任何写出/加载/创建前验证公共环境闭集，并让basis、intent、实际进程和observer消费同一受约束map。本次只使用虚构dummy值，没有读取真实环境或凭据。

CTRL-R05 / P2：owned_job_hooks.py 18-29及controller.py 165-217。before_resume在run_owned主线程同步执行，下一次deadline检查发生在callback返回之后；controller也在observer返回后才检查deadline。callback或文件操作停滞时，没有独立owner在固定deadline终止Job，heartbeat线程仍可刷新。应由实际受控watchdog/owner覆盖callback和执行阶段，保留终止与错误原文。本项为静态控制流结论，未运行超时实验。

CTRL-R06 / P1：observer.py 158-168、294-331，controller.py 160-164、190-217。observer验证了正确run_owned代码位置、PID/handles、flags/deadline/env，但未核对实际frame.argv/cwd。foreign argv和foreign cwd两项独立替身均被接受。四Source review还未绑定phase_worker或Python；controller临时记录worker pin，不代表后续实际CreateProcess消费同一被审查字节。应将worker、执行依赖和确切argv/cwd纳入review/context，并在真实callback以及进程创建/加载边界验证，不得由self-reported intent代替。

已验证的正向边界

hook的确切字符串变换落在AssignProcessToJobObject成功之后、第一次ResumeThread之前，固定base字节与期望pin一致。phase_worker源码确在同一Python进程内依次调用precheck和phase，期间检查input原文及runner pin。observer能拒绝已resume、未assigned、错callback行、错PID/creation/Job、额外Job子进程、breakaway、退出进程、Root或作者自签、REQUEST_CHANGES和formal_acceptance=true。

observer明确标注program actor、独立源码作者、Root实际执行者，以及admission-only/full_lifecycle_cleanup_verified=false；没有冒充另一个Agent亲自观察完整native生命周期。这些边界应保留。其声明的同步callback来源仍待真实开发probe验证，不能由合成frame控件升级为实际Job证据。

保留OPEN

真实Host资格prepare/admit/dispatch、资格请求纳入当前300秒/3请求范围、所有Host/worker子树的终结、actual callback/OS原文、以及新的被审查Source全部仍OPEN。v8 runner已有的独立审查不替代本次controller/observer执行闭包审查。Root提供的CP341/168/679与observed680/681是本次任务起点信息；本包不更新这些数，不把包内旧错误复计。此次独立review没有新增工具失败。

修复应生成新的immutable Source revision；此包和输入旧版本保持可复查。正式签名文件decision为REQUEST_CHANGES，formal_acceptance=false。

