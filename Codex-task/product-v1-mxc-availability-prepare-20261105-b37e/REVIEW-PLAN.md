# MXC 无模型可用性检查：准备包，禁止直接执行

本包只准备下一步 Root 独立审查材料。没有运行 Codex、cmd、模型、probe、App、setup 或安装器；没有修改已存在分析目录或 D:。创建了空的 C-owned empty-cwd，并确认 attempt-01 不存在。scope.template.json 明确 PREPARATION_ONLY_NOT_AUTHORIZED；不是已有批准回执，也不是 f13 CLI 可接受的 scope。

检查目标只有：已安装的 Codex 能否显式选择 MXC，启动固定 Windows cmd.exe，输出 MXC_OK，并被外层 Job 完整回收。内置 :workspace 仅用于这个无数据 echo 检查，不替换产品 :root deny/:minimal read/source read profile。即使成功，也不证明 split-read 边界、产品执行资格、所有网络隔离或用户模型上下文符合限制。

Root 报告的只读 OS 事实是 Windows 11 25H2 build 26200.9711，超过文档列出的 26200.9278；仍不能单独证明 MXC capability。官方说明要求系统能力预先存在，显式 mode 在资源/政策不支持时失败；候选不应触发 fallback、安装或管理员 setup。[Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)

## Exact argv 与输入 pin

机器可读 exact-argv.json 为唯一参数顺序。CreateProcessW 的 applicationName 必须是该绝对 codex.exe；使用 Windows 标准 argv 转义，不通过 PowerShell/shell 字符串启动。内层 cmd 为查到 SystemRoot 后固定的 C:\Windows\System32\cmd.exe：

    <pinned codex.exe> -c windows.sandbox=mxc sandbox --include-managed-config --permission-profile :workspace -- C:\Windows\System32\cmd.exe /d /c echo MXC_OK

无 stdin prompt、exec 子命令、login、模型任务、项目路径参数、网络命令、脚本、额外命令或命令串分隔符。cmd /d 禁止 cmd AutoRun；这并不证明 Codex 原生初始化不存在其他受平台配置控制的行为。

pins.json 记录本次只读复核的四个实际文件：Codex 0.166.0 的 native exe、cmd.exe、f13 owned_run.py、其固定 Python。第三方输入保持原路径，不能只复制 codex.exe 脱离当前完整安装目录。它们在最终 Root scope 创建、执行前、结束确认后都需检查；不一致则停止，不更新 pin 后自动继续。

## 环境与 f13 复用

f13 完整 SHA：f13f630d21548bf8bbb9f1bdaf08b78adc41546d32f00216c05f6ae3664a218c。

读取源码后发现 f13.child_env 强制替代 USERPROFILE/HOME/APPDATA/LOCALAPPDATA/TEMP/TMP，execute()还创建新 profile；不能直接执行 f13 CLI。为遵守本次 normalNativeenv，本准备包选择父线程允许的“直接 exactargv 计划”，没有交付未经审查的 runnable wrapper。

后续 Root 小 controller 的最小接入契约：
1. 固定 Python 下以 -I -S -X utf8 运行；先验证自身、已登记 scope、review receipt、f13 和两个原生 exe 的 SHA 与路径。不得从 PATH 找 executable。
2. 仅加载固定且校验后的 f13，复用 Kernel/run_owned 所提供的 suspended CreateProcess、Job assign-before-resume、无 breakaway、KILL_ON_JOB_CLOSE、原 handle 跟踪及主动清理。不能修改 f13 原文件；不能调用它的 execute/validate_plan 环境路径。
3. 若使用 f13.run_owned，在被隔离加载的模块实例中注入经 Root 审查的 child_env 回调，仅返回执行进程原生环境的副本。这个改动发生于控制器自身内存，不修改 OS或文件；需纳入新 controller pin/review。回调不增加 CODEX_HOME，不改任何 HOME/PROFILE/TEMP 路径，不写 env 快照，不打印 env 值，也不读取凭据文件。graceful=none，事件句柄=0。
4. CWD 固定为本包 empty-cwd；执行前检查普通目录、实际路径/所有祖先无 reparse、当前授权用户所有、目录仍为空。任何文件出现即停止，不清空或删除后重试。
5. attempt-01 必须不存在；exclusive mkdir消费一次调用预算，再以 exclusive写入 CONSUMED（在 CreateProcess 前）。失败/未知都保留 consumed 目录；不存在自动重试或新 attempt生成逻辑。
6. stdin=NUL；stdout/stderr写 C-owned attempt内独占创建的普通文件，不能使用继承 pipe。输出上限每流1MiB；监督期限45秒，cleanup最多5秒，外层总上限60秒；Job活动进程<=16、总内存<=2048MiB。监督开始前完成所有哈希，resume后先进行有界handle/Job轮询，先清理Job再读取输出。
7. 从 f13取得 stop_proved、root signaled、job active zero、exit code、timeout和error事实。仅在已确认停止后封存raw并读回有限stdout、核验输入未漂移。stdout只能是 MXC_OK 加 LF或CRLF，exit=0且无错误，方可记 MXC_ECHO_STARTUP_OBSERVED_ONLY。
8. 结果任何状态都写 resource_ready=false、product_can_submit=false、automatic_retry=false、formal_increment=0、product_increment=0、maximum_model_tasks=0。未确认停止时不得hash/read可能仍在写的raw；保留 UNKNOWN，无第二次调用。

所述第3项是需要独立审查的接入点，不能视为f13既有审查自动覆盖。Root须将实际controller pin和review receipt纳入新registered scope；本模板中的controller=null不构成可执行方案。Root 若已有满足上述条件的已审查 controller，可复用其确切版本并补pin，无需新建控制器。

## 本地副作用与未证明事项

已发生的准备副作用只是在本准备目录写入 JSON/Markdown，并创建空 empty-cwd。预计 Root 后续执行的明确副作用：
- 外层创建/消费 attempt-01；写 CONSUMED、stdout.raw、stderr.raw、RESULT和hash证据。
- 创建有限时 Windows Job、Codex进程及其沙箱cmd/必要子进程；退出/超时关闭或终止整个Job。
- cmd echo 自身只输出常量，不读用户文件、不写文件、不主动使用网络。
- --include-managed-config 让 Codex 按其原生流程处理平台配置；外层不读取、复制或输出这些私有配置/认证内容。normal env原样传给原生CLI，不代表其变量值可公开。

未授权副作用：saved config写入、OS组件安装、sandbox setup、UAC/提升、创建用户/组、防火墙或ACL/登录权利更改、更新依赖、打开App、模型调用、D:写入。发现需要它们时停止并报告，不能替换为unelevated或自动修复。

文档支持显式MXC使用预存能力和失败关闭，但本次没有源码级证明 sandbox子命令所有初始化分支的本地state/log/cache/telemetry行为；不能声称“整个CLI绝不网络/绝不触碰任何本地状态”。这里只限定传入的cmd没有网络/文件动作。是否有原生运行时额外state/log写入，需Root在最终执行审查中如实处理；不能以准备包暗授广泛写入许可，也不能设置临时认证HOME来回避这个未知。若审核要求绝对排除任何saved-config变化，且证据不足，保持待审而不是默认执行。

raw输出可能包含原生诊断/路径等信息，只放本地受限receipts，不在root工具回显整段；只发布exit、token匹配、bounded failure类别、停止证据及必要脱敏文本。不得查看 .sandbox-secrets 或其他认证文件，亦不采集用户真实项目。

## 结果解释与后续

成功只说明这一次固定echo命令的MXC启动可用；内置 :workspace可读面不是产品profile，不能增加既有task成功计数、修改历史FAILED、标READY或放行模型任务。实际customprofile本地负向/正向边界probes必须另审。

失败分为显式不兼容/政策禁止、输出不匹配、非零退出、超时/输出上限、cleanup未确认；不自动安装、不自动fallback、不重复probe。原Task1已提交消费；此前thread/start失败不能重置任何Task/model预算。

本包待 Root 独立审查、确定执行控制器、生成实际registered scope及批准后才可能执行；准备者不运行、不登记D:。

