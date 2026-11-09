独立窄审结论：REQUEST_CHANGES_WITH_PARTIAL_FIXES。仅复核 v2 对 CTRL-R01、CTRL-R03、CTRL-R04 的修复；R01、R03 在此源码范围内通过，R04 仅部分修复，尚不能关闭。没有重新审查旧版整链，也不签 READY_SOURCE_ONLY。

新 controller 原文为 9dfad55126c68bc02a3a16c45b0d487c3af363182d45914fb409850c63309487，17140 bytes。作者提供的正向diff逐字生成新版本，逆向diff逐字恢复旧版本。AST差异恰为 pinned、close_canonical_lease、launch_reviewed_phase 三函数变化和新增 cleanup_confirmed；其他顶层内容未变，hooks、phase_worker、job_probe_worker 三文件原文字节未变。

R01 / SOURCE PASS_IN_SCOPE

93-108 行新增 cleanup_confirmed gate。复用上一轮独立内存filesystem、原始active UUID和活子树反例，active_processes=1 / job_idle=false / handles_closed=false 的结果现在写 retained-unconfirmed receipt，并保留checkpoint和ownership完整原文字节及active UUID。没有native result、缺少cleanup、单独未确认exit/idle/handles/zero-active及cleanup errors均保留lease。合法成功和已确认终结的失败进程可以关闭lease。此结论仅关闭“未确认清理仍释放lease”问题；R02 canonical事务/CAS仍OPEN。

R03 / SOURCE PASS_IN_SCOPE

25-30 行现在一次读取raw，对同一buffer验证path/sha256/bytes并返回这个buffer。复用上次两遍读取返回不同内容的ChangingPath，v2只读取一次，返回内容与pin一致；错误hash被拒绝。module仍消费pinned返回的已检查buffer。此结论不扩大为所有文件路径、动态依赖和启动加载闭包已经审查通过。

R04 / PARTIAL_FIX_WITH_REMAINING_FINDING

146-153 行的新gate先于184行环境原文intent；旧未知extra-key反例被拒绝，合法八键范围输入可通过，NUL值和错误Windows根被拒绝。这修复了任意未知变量进入intent/进程的原始路径。

残留反例是 v2 allowlist 额外允许 ComSpec 与 PATHEXT，而已固定v8 runner.cli_environment只投影SystemRoot、WINDIR、PATH、USERPROFILE、LOCALAPPDATA、APPDATA、TEMP、TMP八键。独立用虚构公共值分别加入ComSpec和PATHEXT，gate仍通过；两份环境在v8 basis中的投影与不含额外键时完全相同。随后controller仍把完整public_env写intent、交observer和CreateProcess。实际消费环境有未被phase basis约束的字段，原R04不能全部关闭。

最小修复是把controller环境闭集收敛到v8 basis覆盖的八键，或对新增键采用正式且同步的basis/observer契约扩展并重新审查。Root已说明将采用下一immutable revision的八键方案；本审查不修改v2或预先接受尚未封存的代码。

验证范围

共19项独立pure AST/内存检查，17项符合预期，两项允许ComSpec/PATHEXT的应拒绝反例被接受。控件明确复用上一轮自己的输入，不执行作者的5项cleanup控件。没有导入候选模块，没有执行真实launch/controller/native WinAPI、SQL、模型或provider，也没有写canonical/Main。Source反例属于审查发现，不是工具失败；本轮新增工具失败为0。

CTRL-R02、CTRL-R05、CTRL-R06、真实Host资格路径、真实OS callback和全生命周期证明继续OPEN，不在本窄审中重跑或升级。Root告知的起点为CP342/168/681；本包不修改或重计这些数，也不改变旧31项审查包。新包decision不能满足observer整链READY gate，formal_acceptance=false、execution_ready=false。

