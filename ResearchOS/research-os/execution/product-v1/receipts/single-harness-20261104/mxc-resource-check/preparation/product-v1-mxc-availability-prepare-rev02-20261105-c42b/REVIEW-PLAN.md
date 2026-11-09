# MXC availability 准备 Rev02 — 未执行、未批准
本包替代 b37e direct-plan 草案。唯一可审查执行拓扑：原版 pinned f13 CLI → pinned Node mxc-echo.mjs → pinned Codex sandbox → pinned cmd echo。不修改 f13、Kernel 或其 execute入口，不替换 f13 child_env。父线程选择的 Node 子层显式环境恢复模式沿用 Native05。

文件：
- mxc-echo.mjs：无第三方依赖、无SDK、无模型/认证探针；只单次spawn。
- mxc.scope.template.json：内层模板，state为PREPARATION_ONLY_NOT_AUTHORIZED。
- f13.scope.template.json：外层模板，authorization为PREPARATION_ONLY_NOT_AUTHORIZED，内层scope哈希是待填占位。
- pins.json / MANIFEST.json：实际只读hash和准备物清单。

运行前必须由 Root 独立静审，再将内层模板复制为本目录mxc.scope.json，改为ROOT_REVIEWED_EXACT_COMMAND并固定哈希；将外层模板登记到原 f13 的 scopes 目录，绑定最终内层哈希、wrapper与所有inputs，authorization改为ROOT_REVIEWED_EXACT_COMMAND。准备者没有做这些步骤。f13仍使用原CLI --scope <registered path> --scope-sha256 <registered sha>；固定Python执行，禁止直接启动Node wrapper。

外层 purpose=build 仅因原f13支持fixture/build/gui枚举；实际argv完全不进行build。不得把此枚举解释成产品build授权。

## 固定命令与资源
完整命令在内层模板argv中，Codex与cmd都为绝对路径，shell=false：
    codex.exe -c windows.sandbox=mxc sandbox --include-managed-config --permission-profile :workspace -- C:/Windows/System32/cmd.exe /d /c echo MXC_OK

官方命令文档要求CLI>=0.162.0。实际installed=0.166.0，binary SHA9d563ee4…；cmd SHA15cd209c…；Node SHA5f364598…；f13 SHA f13f630d…。完整hash在pins.json。本机25H2 build26200.9711由Root只读观察，超过文档引入阈值，但不证明MXC已具备。[官方 Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)

外层 f13：45秒执行、5秒cleanup、无grace、<=16进程、Job总内存<=2048MiB、每流raw<=1MiB；Root外层必须保留总deadline<=60秒。内层：35秒观察deadline、每流1MiB阈值、64KiB精确byte prefix、全流SHA256。35秒后或输出超额仅记录pending状态并继续等待child.close，绝不自行kill、PID枚举/名称终止、process.exit、重试或自动fallback。f13是唯一硬终止边界；Node不会自证Job membership。

f13先创建唯一runs/mxc_availability_20261105_c42b并消费一次scope；Node再独占创建mxc子目录并写CONSUMED。其中cwd和tmp均新建；Codex cwd始终是空cwd目录，与脚本、scope、receipts隔离。现阶段所有run目录不存在，模板也未登记。任何attempt已存在即停止，不清空/重跑。

## 环境来源
只借鉴并裁剪已审 Native05 real-electron-flow.mjs 的makeEnvironment OS/native-profile字段，来源hash b1de184c9ac825f786e66ecb80f950bc875cd8b8ceb4847c7e45fc2b0800ee98。没有import或执行Native05。
- SystemRoot=C:/Windows，SystemDrive从该已验证drive-root路径派生；正常USERPROFILE/HOME/APPDATA/LOCALAPPDATA为当前用户已知路径。
- TEMP/TMP仅指向新建owned run tmp；固定PATH只含Codex安装bin、Node目录、System32、Windows。
- 不拷贝ambient env，不带API key/proxy/NODE_OPTIONS/CODEX_HOME/ResearchOS参数；不手动读取、复制或记录私有配置/认证。没有更改OS环境或savedconfig。HOME是正常profile，没有临时认证HOME。
- CLI自身仍按原生正常配置流程处理--include-managed-config。env值不写receipt，仅key名称。
- 这与初版“ambient env全部继承、TEMP不改”的草案不同，以父线程最新指令和本Rev02为准。

## 证据与结果边界
stdout/stderr不经公开工具原样回显。内层关闭后保留每流前64KiB的原始prefix.bin、全流SHA/总byte/截断标志；短错误完整保留，长错误保留hash-prefix，不能宣称长错误文本完整保留。原始prefix只存在本地C receipts，Root发布前应做必要脱敏。
超时/上限/stream错误记录不会转成功；spawn错误不重试。进程close后hash所有固定inputs并检查漂移。只有exit0、exact MXC_OK加LF/CRLF、无error/超时/超限/漂移才产生：
MXC_ECHO_CHILD_CLOSED_REQUIRES_ROOT_STOP_PROOF
这不是最终root清理证明。Root必须结合f13 RESULT中的job_assigned、stop_proved、root_signaled、job_active_zero、无errors、无timeout/input drift确认这一次可用性。cleanup不明时UNKNOWN且不读可能仍写入的raw、不重跑。

resource_ready=false、product_can_submit=false、formal_increment=0、product_increment=0始终固定。内置:workspace只验证无数据echo启动，不修改/替代ResearchOS产品的root deny/minimal read/source read，不证明split-read enforcement。customprofile本地验证须另审；不能放行模型重跑或改历史FAILED。原单次Task预算已消费，thread/start失败不重置。

## 已知副作用与剩余限制
准备阶段只有本C目录新文件及Node --check语法检查；没有启动wrapper/Codex/cmd/模型/探针/安装器/GUI，无D写入。
未来若批准：
- f13原入口创建owned attempt/profile/tmp和raw/result；Node创建mxc/cwd、tmp、CONSUMED、计划、prefix和结果。
- Windows Job和受控子进程；cmd echo只输出常量，不读用户项目/文件、不发网络命令。
- Codex sandbox启动可能按原生流程处理配置并产生本地缓存/诊断；不能声称整体CLI零写入或零网络。控制器不会手动查看private config，绝不写savedconfig。
- 未授权OS安装、setup、UAC、用户/组、ACL/firewall/策略更改、自动bootstrap、CLI认证命令、模型任务或付费fallback。显式MXC不兼容/被政策禁止就失败；不改mode或权限绕过。
- 既有f13 Job能否容纳MXC子进程亦须实测，不能通过allow-breakaway或脱离Job来“修好”。

纯准备验证：Node --check通过（只语法，无执行模块）；JSON模板解析、固定argv/budgets/env路径与pins检查。未运行任何可用性测试。需Root独立审查和最终scope注册后才可能执行。

