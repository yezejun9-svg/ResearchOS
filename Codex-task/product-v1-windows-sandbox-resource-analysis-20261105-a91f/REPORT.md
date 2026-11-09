# Windows 原生沙箱资源诊断（只读分析；未实施）
日期：2026-11-05。范围：当前 installed Codex 0.166.0、公开包文件、ResearchOS 源码/D03、已产生的公共回执、OpenAI 官方文档。未运行 Codex/ResearchOS CLI 或 App、模型、sandbox probe、installer/setup/UAC；未修改 D:、认证、配置、系统策略或失败计数。此报告和伴随 evidence.json 是本次唯一新产物。

## 结论与现状
当前实际运行选择的 unelevated restricted-token 路径无法实现既定 split filesystem read 限制，并拒绝无沙箱执行。应将这个具体适配器/权限组合阻止提交，而不是放松 :root deny 或改成普遍 read-only。更强候选是显式 MXC，其次为已获管理员初始化的 elevated；两者在此设备的可用性、有效策略、精确配置兼容性均未证实。安装新版或管理员初始化目前都不是已证明必需的动作。

原始事实：
- package.json=0.166.0；平台包=0.166.0-win32-x64；codex-package.json target=x86_64-pc-windows-msvc，entrypoint=bin/codex.exe。
- 已安装二进制 SHA256：9d563ee4e0441ff9d59d612013e0460ddf8e5709735c2d9f6b98b7ef8ca4eb42；本次只读取并哈希，没有执行。
- project 3c2851162463a31281fc21678e12636a；task 449cdce6ba09adefcbaa57e95e2e9411；run d15274806ec0f89e26077c195ef93e59，epoch 1。
- events sequence 7/8：Failed to create session / thread/start，AGENTS.md loading 的 fs sandbox preparation 阶段失败；原文关键句为 “windows unelevated restricted-token sandbox cannot enforce split filesystem read restrictions directly; refusing to run unsandboxed”。
- final-task FAILED；cli_thread_id=null；assistant_text=""；retryable=false。单次 DOM submit=1；internal_model_api_calls=NOT_MEASURED。进程开始/公共 RUNNING 不证明模型线程或推理已发生；也不能把内部 API calls 未测量改写成测得 0。
- 原 result 的 formal_increment=0、product_increment=0、REAL_READ_RESULT_NOT_CONFIRMED 和原任务/Run引用全部保留。

## 官方资源路径（当前文档，不是该安装的运行证明）
Windows guide documents MXC as preferred on compatible Windows 11 devices; introduced builds are 24H2 26100.9278 / 25H2 26200.9278. It needs no admin setup, extra accounts or local firewall rules. Explicit MXC fails on incompatibility/policy denial. Managed networking requires effective allow_local_binding=true; loopback is reachable. Elevated uses lower-privilege sandbox accounts, ACLs, firewall and local-policy changes; setup requires administrator approval. Unelevated cannot enforce denied reads. Deny-read globs snapshot existing matches per process. [Windows sandbox](https://learn.chatgpt.com/docs/windows/windows-sandbox)

The documented non-model MXC command test exists in CLI 0.162.0+. Elevated provisioning must use an administrator-trusted installation, correct target identity and Codex home; setup reads that user's configuration and persists the elevated selection. Installing CLI does not grant workspace access. [Windows deployment](https://learn.chatgpt.com/docs/enterprise/windows-deployment)

The configuration reference supports windows.sandbox=mxc|elevated|unelevated. features.prefer_mxc allows legacy fallback; explicit mxc is the fail-closed candidate. Managed windows.allow_mxc=false prohibits MXC, allowed_sandbox_implementations constrains legacy modes, and require_mxc rejects other modes but does not select MXC. project_doc_max_bytes caps AGENTS instruction bytes; untrusted projects skip project .codex config/hooks/rules. features.hooks disables lifecycle hooks; sandbox network controls do not cover apps/MCP/hosted tools. [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)

这些官方页面由 developers.openai.com 旧路径重定向至 learn.chatgpt.com，读取于本日期。它们是滚动文档。版本 >=0.162.0 的明确声明支持把 0.166.0 纳入候选范围，但本机 npm 公开包没有 Rust 实现或 schema 文件可离线证明所有字段的精确行为；vendor 的两个 bin 文件存在不证明任何 OS 沙箱已经初始化。

## 可审查的最小后续方案（仅提案，全部未执行）
1. 保持完整既有 Host-fixed argv、只读授权 source、owned cwd、approval_policy=never、network.enabled=false、受控环境和 managed requirements。仅为候选模式加入单个 Host-fixed TOML override：
   - 首选候选：-c windows.sandbox="mxc"
   - 备选候选：-c windows.sandbox="elevated"（仅在明确已初始化且获准时）。
   不使用自动 fallback preference 作为 readiness 证明；不使用 --sandbox read-only、unsafe/full access 或 :root read 替代既定 profile。上面不是当前执行指令，也不是已经完成的代码变更。
2. 在任何模型运行前，先审查是否能通过现有公共/管理员提供的受限元数据确认 OS build、MXC capability、有效 managed mode、或既有 elevated provisioning 的对应用户/版本/策略状态。仅选择 mode 不能证明资源存在。明确禁止把首次运行触发的自动 setup 当作只读检查。
3. 若以后单独授权非模型诊断，可按官方示例考察显式 MXC command startup；官方 :workspace 示例不是本产品精确权限测试，不可用它替代 split-read profile 验证。对本产品应先冻结精确 argv/permission profile、单独 C-owned 无敏感 fixture 和所有潜在写入清单，再审查执行。当前 no-probes 限制下未运行任何这类命令。
4. 若明确需要 elevated 初始化，官方模板（未执行）为：
   codex sandbox setup --elevated --user '<target-Windows-identity>' --codex-home '<approved-existing-Codex-home>'
   这是 OS/用户配置变更审批项，不是普通只读 preflight。应由用户/IT决定实际 identity/home，不从私有区域读取或猜测，不要求用户交出凭据。现有 C:/nvm4w 安装能被当前用户读取，不足以证明可被管理员安全信任；在提升前还须由管理员确认其完整安装目录不可由低权限方篡改。
5. setup 的已知变更类别：创建/维护 sandbox 用户及组；ACL/文件权限；防火墙；sandbox 用户的本地登录权利/策略；用户 Codex home 下 setup 状态/诊断及配置选择。精确账户名、规则名、ACL目标、文件清单、重复初始化行为和回滚粒度未由当前本地公开包证实，因此本报告不提供“无副作用”或“精确已审计安装器”的承诺。若必须升级 OS/安装缺失 MXC capability，也需要另行明确授权和具体方案；不能从文档推荐直接推断需安装。

上面提案的依赖关系：公开元数据检查 → 明确 mode/resource 支持 → 精确非模型权限验证 → 上下文边界审查 → 另行批准且只提交一次新的测试。没有一步自动允许模型重试。本次此前那一次任务的授权/计数不会被“启动失败”重置。

## 能否只读确认已经初始化？
可以只读检查“存在”的迹象，但本次授权范围内不能完整确认可用性：
- 已完成：公开包版本、manifest、native binary inventory/hash；公开事件中实际选中 unelevated。
- 未执行但可单独定义的受限元数据检查：OS build；系统宣告 MXC capability；仅目标 Codex sandbox 的用户/组、ACL、防火墙、登录权限摘要。应避免整机用户/网络配置枚举与敏感内容输出。
- 既有 setup 文件在 CODEX_HOME 内。本次禁止读取私有认证/配置区域，所以没有读取 setup 标记、sandbox log 或 secrets；标记存在也不能证明当前策略、ACL和运行身份一致。
- 官方 /status、/debug-config 和 sandbox 命令测试需要 CLI/session/命令执行；不是当前允许的静态检查。完整 debug-config 还可能暴露无关配置，不能为方便而收集。
- 只读 metadata 能排除明显不兼容；不能证明 precise source-read/elsewhere-deny、network-off 或 Job descendant cancellation。后者需要受控真实验证，且单次 echo startup 仍不足以验收全部边界。
因此 current resource readiness=UNKNOWN；observed unelevated + requested profile compatibility=UNSUPPORTED。不要把 UNKNOWN 写成 NOT_INSTALLED，也不要写成 READY。

## 模型上下文是独立门槛
--ignore-user-config skips only CODEX_HOME/config.toml; authentication still uses CODEX_HOME. --ephemeral prevents session rollout persistence, not every runtime/config/log write. [CLI reference](https://learn.chatgpt.com/docs/developer-commands?surface=cli)

Codex normally collects global AGENTS.override.md/AGENTS.md plus project guidance; combined instruction size is capped by project_doc_max_bytes. [AGENTS instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md)

本地 D03 明确是 PLATFORM_POLICY，不是 “全部 hooks/MCP/context 均移除” 证明。实际错误发生在加载 AGENTS 阶段，更表明 thread 初始化会处理 prompt 两个文件以外的上下文路径。当前 executionInput 还带 source_workspace、process_working_directory 绝对路径；这些路径可包含 Windows 用户名。更强 Windows sandbox 不会自动消除 Host 构造的路径元数据、平台系统/开发者指令、managed instructions、工具/skills说明或账户上下文。

后续可研究的抑制候选：Host-fixed -c project_doc_max_bytes=0、project_doc_fallback_filenames=[]、保持 owned project marker、关闭 hooks/plugins/apps/remote plugins，并单独考虑 memories、skills/MCP来源。0 值是否阻止所有 global/project 文件读取、managed constraints 如何影响它、是否还有其他注入渠道，在 installed 0.166.0 上尚未证实。空 fallback list 也不禁用标准 AGENTS 文件；不可宣传成绝对两文件隔离。不要为绕过平台策略而读/复制凭据、另设临时认证 HOME 或删除规则。

在父线程最新“不得传真实项目/凭据/额外个人信息”约束下，未来只用无敏感固定 fixture还不够：需具体审查目录命名/传输路径元数据及剩余 native context。现 D03 的公开声明不能替代这一新增范围门槛。如果无法有证据证明符合，停止模型路径并列为独立 blocker，不擅自扩大授权。

## 产品能力失败分类建议（不实施）
源码证据：
- adapters/runtime/codex_driver_windows.go:47 固定参数；:root deny、:minimal read、source workspace read、network disabled。读取到的当前 arguments 没有显式 ownedcwd write 条目；Host 创建 cwd 是进程准备行为，不能据此宣称 tool 权限内 cwd 可写。应在后续冻结调用时逐项核对，禁止推断或暗加权限。
- 同文件 :412 对非零 exit 统一给 CODEX_EXECUTOR_EXIT；不能仅凭任意 stderr 的 "sandbox" 字样确定强分类。
- internal/domain/runtime_harness_windows.go:75 capabilities 的 ready 仅由 Present/ConfigurationControlled/LOGGED_IN 决定；UnavailableReason 只附加 reason_codes，未影响 ready；workspace_read_scope/execution/cancellation仍 UNVERIFIED。
- :387 对失败统一 HARNESS_UNAVAILABLE；:770 scanHarness只有相同三项门槛；:967 launch只检查 config/hash。
- :1115 已有 sealed researchos.codex-result.v1 artifact 的 failure/execution_state/thread_id；现有 NativeRun、runtime_dispatches、project outbox 和 result artifact 是唯一持久业务证据链，不需要新数据库。

建议新增有界原因（名称为提案）：WINDOWS_SANDBOX_PROFILE_UNSUPPORTED；phase=SANDBOX_PREPARATION；effective_mode=unelevated；retryable=false。匹配须限制到已固定版本/hash/backend/profile，并要求可信原生运行诊断中的精确拒绝文本、启动失败阶段、无 thread identity/assistant 输出和已确认 cleanup。若记录不全、已有 thread 或 cleanup 未确认，保留既有 UNKNOWN 优先级，不将其降级为“安全未运行”。不从 prompt/tool 任意文本触发 classification。

分类写回现有 canonical result/dispatch/Run lifecycle，再由 capabilities 和 task failure投影，不增加可与 canonical state 分叉的独立缓存DB。历史此Run保持 FAILED 和原引用；补充原因须通过正式支持的可追溯路径，不能改原 receipt/assistant result/成功统计。成功执行/边界验证仍保持 UNVERIFIED，直到独立有效验证。

can_submit、Submit admission、scanHarness、最终 launch gate必须一致阻止被证实不支持的 mode/profile；当前 reason_codes 仅展示而未 gate 的问题也要处理。阻止项绑定 mode/profile/CLI hash/backend及适当运行环境证据，不永久封禁所有 Windows/Codex，也不凭新版本或换模式自动转 READY。证据改变后先回到 UNKNOWN/待资格验证。旧 terminal/task 不重排队，refresh/restart/登录/点击检查均不自动重试。

推荐 UI 文案：“当前 Windows 沙箱不能执行此只读范围；任务在模型线程创建前启动失败。请先完成受支持沙箱的兼容性确认。” 保留原Task/Run与原错误详情；无需 UI 暴露私有配置或原始认证信息。

## 审批和阻塞
当前没有发起安装、配置/策略写入、管理员/UAC、CLI/probe 或模型任务；没有工具拒绝/等待批准动作。本次分析已完成。
待解决：本机 MXC兼容与managed政策未知；elevated既有初始化未知；精确profile下OS边界未验证；额外上下文/路径元数据限制尚未得到满足证明。只有确实需要 OS安装/提升/setup/政策变更时，才提交对应最小具体变更及副作用供用户批准；本报告不请求对不明资源的泛化管理员授权。

## MXC static preflight 的精确边界（父线程补充）
已知官方资料支持“系统能力必须预先存在 + 显式模式不可用则报错”，没有给出安装 Microsoft Execution Containers 的 Codex 命令。不能把 Windows Sandbox 的 Containers-DisposableClientVM、Hyper-V、WSL 或 Docker 任选一个当作 MXC 先决条件；本报告未发现这种官方映射。

可另行批准的只读 OS build 信息命令示例（未执行）：
Get-ItemProperty -LiteralPath 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' |
  Select-Object DisplayVersion,CurrentBuildNumber,UBR

它仅读取公开版本数字，不读用户配置、不创建进程沙箱、不改系统。不能单凭通过版本阈值证明此设备已获得 MXC，亦不能判定有效管理策略。没有查到官方精确 MXC public file/export/optional-feature 检查契约；因此不建议凭名称猜测 Get-WindowsOptionalFeature 参数或将某 DLL存在当成 READY。不得直接运行本示例，当前委派仍为不probe。

官方命令级候选（原样展示；没有执行）：
codex -c windows.sandbox=mxc sandbox --include-managed-config --permission-profile :workspace -- cmd.exe /d /c echo MXC_OK

该例不发模型请求，但会启动沙箱命令，可能产生常规运行状态/日志，且 :workspace 不是 ResearchOS split-read profile。因此它既不是零副作用静态检查，也不是现任务授权下可自动运行的动作。若 root 后续审查，必须换为经版本核验的固定安全 profile/fixtures后再作独立非模型验证计划。全局Task1预算已消费；不能以“没有thread”为理由补发模型Task。

显式 -c windows.sandbox="mxc" 是 Host/source mode选择变更，仍须 root 独立source lease/review。它不授权系统组件安装或管理员提升。文档“无需管理员setup”不等于对安装二进制所有启动分支的完整无副作用保证；没有实际命令/源审计前，未知事项保持未知。若显式MXC失败，不回退unelevated、不安装组件、不提权、不发送第二模型任务。


