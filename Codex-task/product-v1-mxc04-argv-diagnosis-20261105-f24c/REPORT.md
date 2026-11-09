# MXC04 命令语法失败：只读诊断
结论：当前证据足以确认单次 MXC availability 检查以命令语法错误退出；不足以认定 MXC 不存在、不可用、绕过了沙箱，或确定 forward slash/COMSPEC/SDK serializer 中哪一个环节是根因。状态应保持 FAILED_COMMAND_SYNTAX_CAUSE_UNCONFIRMED / readiness UNKNOWN。没有重跑、创建新执行scope或修改准备/运行/产品配置。

## 实际证据
唯一已执行本地检查：mxc_availability_20261105_e91c。读取Root指定的C receipts：
- Codex child exit_code=1，stdout为0字节；spawn_error=null、timed_out=false、input_drift=false、observation_errors=[]。
- stderr恰好18字节：C3 FC C1 EE D3 EF B7 A8 B2 BB D5 FD C8 B7 A1 A3 0D 0A。
- GBK/CP936静态解码为“命令语法不正确。”加CRLF；不是UTF-8文本。SHA256=7830609d54ab060eb4d9b243eda3a59e38b0940058ed397f4cd26d89631cd86d。
- 完整stream EOF+child.close已观察；delivered=ingested=durable_prefix=18，未截断、未pause、未输出超限，所以本次错误不是诊断截断或文本解码丢失造成。
- f13 status=CHILD_NONZERO_STOPPED，job_total_processes=7、job_active_zero=true、stop_proved=true；无timeout/output_limit/errors、无TerminateJob/TerminateProcess操作，约1.238秒结束。
- 7个Job累计进程不提供每个镜像/角色或实际命令行；不能据此识别哪一个进程输出错误，更不能证明具体隔离边界。

实际argv（程序入口为已固定canonical Codex）：
["-c","windows.sandbox=mxc","sandbox","--include-managed-config","--permission-profile",":workspace","--","C:/Windows/System32/cmd.exe","/d","/c","echo","MXC_OK"]

wrapper第17行CMD为forward-slash absolute路径；第58行COMSPEC复用同一CMD；spawn第109行使用参数数组、shell=false、windowsHide=true、detached=false。这避免Node主动另起shell，但不能排除Codex/MXC随后将argv序列化为Windows command line。argv各字符串无空格、内嵌引号或shell运算符；固定echo命令也没有用户输入。

官方示例为裸cmd.exe，而本次改用同一镜像的固定绝对路径。二者路径身份相同不代表所有命令行解析语境的文本行为必然相同。[Windows sandbox说明](https://learn.chatgpt.com/docs/windows/windows-sandbox)

## 对应版本上游源码链路
只读访问OpenAI官方仓库rust-v0.166.0 tag，未下载/运行代码或编译。该tag Cargo version=0.166.0；它是对应版本源码参考，不是对installed binary可复现构建的证明。

1. CLI WindowsCommand把命令保存为Vec<String>；sandbox入口把global -c配置传入，再调用Windows sandbox函数。没有证据表明wrapper构造了额外shell文本。
   [CLI参数结构](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/lib.rs#L138)
   [CLI入口](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/main.rs#L1682)
2. debug_sandbox.rs 的WindowsMxc分支465–500将首项作为program、其余作为args交SandboxManager转换，再启动返回的MXC wrapper并传播退出状态；该代码路径本身未将cmd路径改成反斜杠。
   [debug sandbox实现](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/debug_sandbox.rs#L465)
3. mxc-sandbox/policy.rs 252–256以command.command调用cmdline_from_argv_for_context，context为WindowsCreateProcess，结果放入ExecutionRequest.script_code。因此确实存在SDK序列化边界，而不只是最外层Node argv。
   [MXC request构造](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/src/policy.rs#L253)
4. windows.rs 29–63先检查is_available并解码请求、构造policy，再调native::launch。native.rs 31–36调用BaseContainerRunner.spawn(request, logger, Inherit)并wait；它刻意不发布SDK完整diagnostic buffer。因而仅有本次18字节stderr不能还原SDK内部最终CreateProcess字符串或失败阶段。
   [MXC Windows入口](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/src/windows.rs#L29)
   [MXC native调用](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/src/native.rs#L15)
5. OpenAI tag的Cargo.toml429把mxc-sdk固定为Microsoft/mxc commit b21120168d70befe12356411423266bfef168446。实际serializer及BaseContainerRunner属于这一外部SDK。本次沿先前“仅OpenAI官方来源”限制未进一步读取Microsoft仓库，所以没有擅自声称其quote/normalization或COMSPEC行为已审计。
   [确切SDK依赖版本](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/Cargo.toml#L429)

## 假设、反证和限制
- 候选A：C:/Windows/System32/cmd.exe文本在SDK/Windows命令解析中被误解。可疑点为不同于文档cmd.exe；目前没有实际最终commandline或对照，不能定根因。
- 候选B：COMSPEC也采用forward slash，SDK若使用该变量启动内部cmd，错误可能发生在内层包装，未必是用户指定cmd参数。尚未读固定SDK源码证明它是否使用COMSPEC。
- 候选C：SDK将WindowsCreateProcess命令再包进cmd，或其quoting规则产生语法错误。OpenAI源码证明调用了serializer，但尚未证明serializer实现如何处理本例。
- 普通Node spawn失败未被观察到：spawn_error=null，进程实际退出；但这只覆盖Node→Codex一层，不覆盖内部后代的CreateProcess。
- 错误形式更像某个命令解析器的语法报告，属于合理推测；仅中文文本不提供签名化进程来源。没有“native MXC is unavailable”明示错误，也不能把这种缺少消息推断成MXC已经成功隔离。
- 无证据支持修改rootdeny、minimal/sourceRead、设置full access、关闭sandbox、改登录或管理员安装。这次失败不需要用模型任务来诊断。

## 最小后续提案：仅供Root选择，未准备执行
优先继续静态读取OpenAI固定的Microsoft/mxc commit中的cmdline_from_argv_for_context与BaseContainerRunner.spawn实现及相关单测，核对：
(1) WindowsCreateProcess context如何序列化cmd.exe；
(2) 是否识别forward/backslash basename、如何quote argv0和/c内容；
(3) 是否使用COMSPEC、是否再包一层cmd；
(4) error来源/进程exit传播。
此动作无Native调用；若当前来源范围不允许Microsoft官方依赖，先由Root明确这一只读来源范围。不读取本机私有sandbox/auth日志弥补缺口。

仅若静态证据仍不足且Root明确授权另一项必要本地诊断，再考虑“同一pinned cmd镜像，CMD常量文本改为C:\Windows\System32\cmd.exe、COMSPEC随同一常量一致”的单次、无模型、相同MXC/f13/limits/空cwd检查。这样改变一个source常量但影响argv和环境两处，不能把成功结果归因于其中单独一处。该方案不是已批准重试，不创建新scope、不自动执行；必须保留已消费MXC04及原产品Task预算/失败记录，不能冒充原run补发。也不建议先运行不带sandbox的echo对照来绕过既定安全边界。

当前Root可公开的准确状态：“一次无模型MXC启动检查以命令语法错误退出，进程已清理；具体参数解析原因尚未确认，资源可用性未判定。” formal/product仍0，不能READY或放行模型。

