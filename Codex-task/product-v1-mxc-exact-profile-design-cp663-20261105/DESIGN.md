# CP663：MXC 精确请求权限的无模型验证设计

状态：DESIGN_ONLY；模型放行 BLOCKED。未创建可执行 scope、helper、fixture、listener 或注册记录，未运行 CLI/Echo/探针/模型。输出仅为 C 设计文件。旧 MXC Echo 2/2 和旧 confirmed FAILED Task 均不可重放。

## 已核实的边界

当前 Host 的 arguments(cwd, source) 请求 researchos-readonly：root deny、minimal read、唯一 source workspace read、network false；没有 cwd write。Host 在启动前创建 cwd/marker 不等于授予 Native child 写权限。PermissionOverrides 被复制但没有用于 arguments；当前也未显式传 windows.sandbox。Host capabilities 目前只用 installed/config-controlled/logged-in 决定 can_submit，尽管 enforcement_verified=false；这些不是权限证据。来源：本报告 SOURCE-PINS.json 指向的实际 Main 源文件，读取时基线 CP663。

两个必须分开的事实：
- 显式 windows.sandbox="mxc" 的受管不允许值会拒绝；[Windows resolver](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/config/windows_sandbox_config.rs#L78)。
- named permission profile 不同：若 selected 不在 managed allowlist，resolver 可告警并选择 required fallback；不能假设 fallback 更窄。[profile selector](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/core/src/config/mod.rs#L4858)。sandbox -P 只是写同一个 default_permissions override，并没有额外 exact-match 保证。[sandbox loader](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/debug_sandbox.rs#L653)。

因此：新 probe 可安全地只触碰合成资源，观察当次有限操作；即使全部符合预期，也不能据此将下一次模型线程 actual_mode_permission_verified 置 true。TTL 仅是过期上限，不能防止启动时重新解析为不同 profile。

## 建议的一次有界诊断结构（尚未授权执行）

以后单独批准时，用新 purpose/diagnostic origin，例如 mxc-exact-requested-profile-qualification；新 attempt 1、Native invocation budget 1、model 0。记录其关联旧 echo 结果，但绝不把它归为旧 echo attempt 3 或重置 2/2。总体 Native 本地调用计量另累计。

原 f13 controller 的完整进程 Job 保持不变：controller → 已 pin 的审计 wrapper → 一次 Codex sandbox → 唯一 helper；不增加第二个 Codex command，不另起不受控对照 CLI。35s soft、45s execution、5s cleanup、Root overall <=60s、16 process、2048 MiB、1MiB/stream ingest、64KiB durable prefix 可沿用为新的独立预算。stdout/stderr 仍边接收边持久化；任何 incomplete/UNKNOWN 保留消费记录、禁止重发。

只设计三个 Host-owned、同级但不互相包含的 canonical 路径：
- S/source：allow.txt（随机合成内容）、write-existing.txt（可牺牲合成文件）、固定自包含 qualification-helper.exe；
- W/cwd：Host marker 与 write-existing.txt；作为 command cwd，不列入 workspace_roots；
- D/denied-sibling：denied.txt（不同的合成内容）。

S/W/D 位于新 C 用户工作目录下，避开 Windows、Program Files、ProgramData、TEMP 默认特殊路径和真实项目，不含真实 userdata/auth/config。无 junction/symlink/reparse；检查父路径、文件对象身份、普通文件、链接数，保留 pre/post 哈希。D 必须在 S 之外且不落入任何已知 minimal 读根。不存在真实秘密文件作为否定测试。

可信 Host controller 先直接用文件 API 证明这些合成目标存在、正常用户确有读写能力；对牺牲文件写入并还原，再取 baseline。不能通过只读属性、额外 ACL、共享锁或故意缺失文件制造“拒绝”结果。probe 运行时关闭目标文件的控制端句柄，尤其不能持有阻止写入的 share-mode 锁。只对 helper/binary pin 可另持防替换句柄，并确认该保护不覆盖被测试文件。

## helper 如何在原权限下启动

优先一个新编译、独立审阅、固定 SHA 的自包含无模型 Windows helper，预先放在 S 内。它凭既有 source-read grant 被读取/执行，仅依赖 Windows 系统 DLL，不读取相邻配置、不使用插件、不产生子进程、不初始化产品服务、不产生 Go test 缓存、不写日志到磁盘；输出只走继承 stdout/stderr。它的布局不是新增文件权限规则。可以由 Core 代码库单独的极小命令构建；不要把具有产品启动副作用的 Core 主入口直接拿来运行测试。

用户目录下现有 Python.exe 不属于 MXC 的 minimal 平台读取根，脚本和标准库还可能需要额外文件；不能只因它在旧外层 controller 可执行，就认定在目标 sandbox 内可执行。不得增加 Python 安装目录、helper 所在外部目录、cwd-write 或 tmp-write grant 来使测试通过。若坚持 Python，必须把固定 interpreter 及全部所需依赖作为合成 S 的预置测试数据，经新的源审查后直接启动，禁 bytecode/site/env 注入；成本及污染风险更高，本方案不推荐。helper 无法在既有授权范围内启动就记录 BOOTSTRAP_BLOCKED，不修宽 profile。

此判断依据 [MXC platform_read_roots](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/src/windows.rs#L110)：平台读取根是 Windows、ProgramFiles、ProgramFilesX86、ProgramData。不要把 minimal 称作“只读两个项目文件”。

## 精确 argv 构造规格

以下是 argv 规格，不是命令行、scope 或可执行脚本；<S>、<W>、<NONCE>、<PORT4> 等必须由未来 Host 注册步骤绑定，不能现在直接运行。所有项均用数组传递，禁止 shell 拼接。TOML 路径使用与现有 Go strconv.Quote 一致的转义。target helper 使用反斜杠 canonical Windows 绝对路径。

    CODEX_PINNED_EXE
    -c windows.sandbox="mxc"
    -c default_permissions="researchos-readonly"
    -c permissions.researchos-readonly.filesystem={":root"="deny",":minimal"="read",":workspace_roots"={"."="read"}}
    -c permissions.researchos-readonly.workspace_roots={"<S>"=true}
    -c permissions.researchos-readonly.network.enabled=false
    -c project_root_markers=[".researchos-codex-root"]
    -c approval_policy="never"
    -c features.hooks=false
    -c features.plugins=false
    -c features.remote_plugin=false
    -c features.skill_mcp_dependency_install=false
    -c features.apps=false
    -c notify=[]
    -c web_search="disabled"
    sandbox
    --include-managed-config
    --permission-profile researchos-readonly
    -C <W>
    --
    <S>\qualification-helper.exe
    --plan-v1 <BASE64_OF_PINNED_SYNTHETIC_PLAN>

Plan 内容只含合成路径、nonce、已批准 loopback endpoint 和有界 case 列表；不包含 allow.txt 的预期内容或完整 hash，避免 helper 不读文件也输出预期答案。helper 报实际读取 hash，由 Host 独立比较。Plan/argv/hash 在 launch 前冻结，helper 不接受任意命令、URL、路径递归或自定义代码。不要添加 --sandbox-state-readable-root、--add-dir、setup、prefer_mxc、fallback、unsafe、ignore-rules。

公开 Windows parser 支持 -P、-C 和 include-managed-config；没有 sandbox 的 --ignore-user-config。[CLI types](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/lib.rs#L137)。exec 的该 flag 是另一入口的选项：[exec CLI](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/exec/src/cli.rs#L39)。因此以上可比较 exact REQUESTED permission map，却不能宣称完整 exec config loader 等价。

## 一次 helper 内的操作与判定

所有调用有单独短期限、逐 case START/RESULT/END 序号，末尾 complete bitmap；异常不中途伪造剩余 PASS。

| case | 实际操作 | 成功条件 |
|---|---|---|
| source read | 打开 S/allow.txt，最多64KiB，读取实际字节并 hash | 与 Host baseline hash 一致 |
| sibling read | 对已存在 D/denied.txt 发真实 GENERIC_READ/open/read | 明确原生拒绝，不能以不存在/共享冲突/异常当通过；若读到任何字节立即 FAIL，不输出内容 |
| source existing write | 对牺牲 S/write-existing.txt 请求写访问；如获准仅写固定短 sentinel | 请求被原生拒绝且 post hash 不变；一旦获得写权限即 FAIL，即使未成功写字节 |
| source create | S 下预先确认不存在的固定新文件 CREATE_NEW | 原生拒绝且 post 不存在；已存在/父目录错误不是 PASS |
| cwd existing write/create | 对 W 同样两项 | 同上；没有给 W 加权限 |
| network | 下述拥有正控的 loopback TCP connect | 原生 policy/access-denied、无 probe 连接被接受，正控保持可达 |

Win32 error 5 / WSAEACCES 10013 等按原始码记录；未知码、FILE_NOT_FOUND、PATH_NOT_FOUND、sharing violation、ECONNREFUSED 或 timeout 只能 UNKNOWN/OBSERVED_UNREACHABLE，不自动解释成 sandbox enforcement。source 读失败使整个资格失败，不能只报告否定测试通过。若误允许写，保留新文件/变更供 post audit，不在同一轮偷偷回滚抹掉失败。

## 有意义且无外网的 network case

controller 在原 f13 Job 内以自身线程建立 127.0.0.1 的随机 owned listener；需要 IPv6 覆盖时同时建立 ::1 listener，均不监听 0.0.0.0、不访问 DNS/互联网。controller 用自己文件/网络 API 做 nonce 标记的正向 round-trip，记录就绪、真实 bound port 和 precontrol。listener 的 handle 不继承给 helper；只继承标准流。

helper 对指定 IP/port 各一次有界 connect，成功连接即 FAIL（即使后续 handshake 失败）。listener 记录 accept 时间/标记；控制正向连接与 probe 采用不同 nonce。probe 后同 listener 做 postcontrol 并正常关闭。前后控制或 listener 记录不完整则 UNKNOWN；端口没监听造成的失败不得当成 network deny。

这只观察指定本机 TCP tuple；不证明所有协议/IPv4/IPv6/DNS/远程 egress。若当前 managed profile 引入代理，MXC 可以有 loopback 例外；不能扩大预期或移走 listener 使结果好看。按 [policy builder](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/src/policy.rs#L208)，disabled network 与 proxied network 的 loopback 行为不同，必须保留实际观察。额外 ingress 测试如需另行设计，不能顺便增加本轮动作。

## Native context、配置及可信 seal

当前产品 Environment("") 继承 PATH 和 HTTP_PROXY/HTTPS_PROXY/ALL_PROXY/NO_PROXY，旧 echo wrapper 则丢弃这些变量。因此不能把旧 echo 的 environment 当作产品环境身份。未来 Host 应冻结并共用明确 environment policy，记录不可逆摘要/存在性而非可能带认证的 proxy 原值，额外 env 策略变化须独立审查。不得为得到 PASS 临时清掉 managed 代理或变更 Native home。

include-managed-config 可能让 Native 进行 cloud config/auth bootstrap；sandbox 的 network=false 不约束外层 Native 的该过程。[cloud loader](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/cli/src/debug_sandbox/cloud_config.rs#L11)。本设计不读私有配置/凭据，也不承诺 Native 自身无认证读取/网络。正常 Native context、managed requirements、AGENTS/rules、hooks/MCP PLATFORM_POLICY 限制继续单列；probe 不是模型上下文只含合成文件的证明。

可信接收必须来自 Host-owned collector 对自己创建的原 process/Job/stdio handles 的观察，经现有 authenticated Host authority / canonical sealed RuntimeProfile/artifact 机制产生；renderer、请求 JSON、用户指定 receipt 路径、孤立“PASS”文件或自报 hash 一律不能创建可信状态。独立审查报告是审核证据，不自动成为运行权限。不要新增另一个自建凭据/数据库体系。

seal 至少绑定：schema/probe revision，Host build/authority generation，原 process creation identity+Job，Codex canonical identity/version/hash，完整 requested argv/map digest，helper/code/fixture baseline digest，source/cwd canonical identities，environment policy revision，OS build/architecture，managed effective-profile provenance（若未知必须显式 UNKNOWN），起止时间、原始流hash/complete bitmap、全部 case、post-readback、Job-zero receipt、独立授权scope与consume。

seal 的 TTL、binary 不变、登录状态均不是 effective-policy 证明。native policy、configuration revision、Host restart、workspace/cwd身份、环境、OS更新或代码变化即失效；无法得到可信 managed/config revision 时，不得标为跨启动可复用 VERIFIED。synthetic source 的证据也不得直接覆盖另一个真实 source identity。

## 同次 Native、模型 turn 前的 barrier：候选存在，完整证明仍阻断

现有 exec --json 是单向运行协议；Host 没有一个在 Native 完成有效权限解析后、模型 turn 前核对完整 policy 并回 ACK 的接口。stderr warning 过滤或看到 thread.started 后 kill 都存在先启动模型的竞态，不是预放行 barrier。

官方 app-server 的 experimental thread/start.permissions 为命名 profile 字符串；不是完整权限对象。[thread API](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/thread.rs#L92)。activePermissionProfile 只包含 id/extends，公开 profile list 仅 id/description/allowed；legacy sandbox 不能还原 split-read 图。[permission types](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/app-server-protocol/src/protocol/v2/permissions.rs#L378)。仅比较名称不足以证明相同实际 grants。schema 默认还过滤实验字段，不能把未经协商字段当成保证。

定向核对已确认：thread/start 的 active ID 来自实际线程 config_snapshot，显式权限更新还有拒绝 managed fallback warning 的路径。如果能证明固定命名图唯一、所有扩张已排除或准确纳入契约、实际 ID 能识别所有 fallback、后续 turn 不重配，则不一定需要完整图 API。但是当前发现两个明确反例：普通配置跨层递归合并会保留 Host inline table 未列出的额外 grant；Native 追加 helper/memory read roots 时也可保留原 ID。详见同目录 BARRIER-ANALYSIS.md，包括正向调用链、反例和候选条件。故当前 exact 权限放行仍 BLOCKED，而非断言 app-server 永远不可行。不得以 broad config/read 读取秘密补链；手写 receipt、不同进程查询、probe+TTL 均不能替代同次屏障。此刻不调用这些接口、不安装升级其他 Harness。

## 最小落实顺序与阻断

1. Slice A：Host fixed MXC + 统一 fail-closed capability/admission/scan/pre-resume 门及 sealed profile revision；Unknown 保持 can_submit=false。不得通过构造 Descriptor(true) 或导入 review JSON 假装 exact enforcement。
2. 另行源码准备/审查上面的 tiny helper、collector、合成布局和新一次诊断预算；本文件不创建这些产物，不批准执行。
3. 只在 Root 独立登记后执行一次新无模型资格；可能得到 OBSERVED_CASES_MATCH_REQUEST，而不是 universal isolation 或模型许可。原 echo 和旧 Task 不动。
4. Slice B 的模型放行仍阻断于 same-launch effective-profile barrier。若 pinned Native 无可靠路径，按 Root 指示保留该门并转其他产品功能，不放宽权限或消耗新的真实 Task。
5. 只有另行建立/审查 barrier 后，才谈新 synthetic readonly Task：新授权/RequestID/Task/至多一Run，旧FAILED不重发；正常 DOM submit前实际caps+LOGGED_IN/chatgpt+精确seal绑定，prompt只列固定合成文件名，答案canary只从文件读取；UNKNOWN不重交。此处是后置条件，未授权模型执行。

固有局限：有限OS调用仅证明当次具体对象/操作；hard-link、volume alias 和 Native上下文仍需保持限制。[MXC公开局限](https://github.com/openai/codex/blob/rust-v0.166.0/codex-rs/mxc-sandbox/README.md#limits-and-windows-validation)。公开 tag 与已装0.166 binary版本/hash关联不是可复现构建证明。无真实 run 时所有 case 均 NOT_RUN。

formal_increment=0；product_increment=0；model_invocations=0；native_invocations=0；execution_scope_created=false。

