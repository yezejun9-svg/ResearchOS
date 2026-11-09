# 每用户 Electron 宿主方案：独立设计审查

结论：`DESIGN_CONDITIONALLY_ACCEPTABLE_NOT_IMPLEMENTED`。建议采用同一安装产品的 Electron 主进程作为唯一管理宿主，CLI 只启动/发现它并使用既有 Native3 凭据和客户端协议。该路线比新增管理服务更贴近当前代码。Root 的 exact14 文件范围基本足够，但必须覆盖下面的阻断设计要求；仅增加 single-instance 锁不够。本报告未执行 native、测试、安装或源代码修改，Main 与新 candidate 均实读为 ecc28。源写授权仍由 Root 另登记。

## 源码依据与必须补齐的设计

| 必须解决的事项 | 当前代码依据 | 第一阶段完成条件 |
|---|---|---|
| 单例宿主与窗口分离 | `main.js:367` boot 同时注册 IPC、启动管理链并创建 BrowserWindow；没有 single-instance 分支 | 在任何 Core 启动前确定稳定 userData 并取得锁；仅赢家运行一次 host boot。窗口创建/聚焦单独、幂等；CLI 模式不创建主窗口，Desktop 请求复用赢家。second-instance 在 STARTING 时排队，不二次注册 IPC 或调用 start。 |
| 同一正常数据根、安装身份及版本 | main 默认 REPO/.local；CLI `main.go:19`、`cli_contract.go:121,134` 路径依赖 cwd；Core discovery 当前只有 URL/PID/data_dir/host_id | 安装根、数据根、Electron userData、CLI config、discovery 均由同一产品布局解析为规范绝对路径。默认布局遵循蓝图204；显式 owned 测试根仅用于新候选。绑定安装 ID、产品/build/protocol/schema、宿主与 Core PID/creation/image、data root；第二发行件/版本冲突拒绝。锁只决定进程唯一，不证明该宿主可信或兼容。 |
| CLI 路径与首次凭据不能漏接 | `cli_native.go:34` 独立重读 env-or-relative discovery；`cli_verbs.go:189-199` 只在已有 cfg.ProjectID/WorkspaceRef 时更新凭据；首次 interactive无凭据即拒绝 | `cli_native.go` 必须统一布局解析，不应标“仅首用凭据确需才改”。首用 `init` 保留 native选择/确认；裸 interactive 的无项目/无凭据状态必须有明确引导或同用户 bootstrap，不能只启动宿主就宣称可用。已有项目的 credential renewal 不重复目录选择。doctor原有只读、不续凭据/资格的语义应保持，若改变须明确测试和文档。 |
| 单例转交不等于 READY；后台日志不能污染CLI | management.start有独立READY握手；CLI面向用户stdout为JSONL | CLI 启动固定安装 Electron→有限等待可信宿主记录与当前 Core/native可用→再运行Go CLI；不能把第二Electron退出0或健康HTTP200当成功。启动失败/超时/冲突返回可诊断非零，不自动重试或把失败变fresh数据；后台stdout/stderr应受控分流，保留Go CLI stdin、stdout、Ctrl+C语义。CLI退出只退出该客户端，不能杀共享宿主。 |
| 统一退出与活动任务边界 | `main.js:411-423` close直接shutdown；`runtime_drain_windows.go:65-108,132` 检查busy/unresolved并拒绝，不主动cancel；管理shutdown等待同一child退出 | 所有受控退出走一个串行safeExit（窗口、tray、before-quit）；重复退出幂等，确认期间拒绝第二启动/变更。阶段1可在busy时拒绝退出并保持可操作界面，不得假称已暂停/取消/settle。若提供“退出并停止”，必须先经现有授权协议停止相关任务并等待真实settle，再请求SHUTDOWN及同一进程退出。不能用app.exit、终止进程或读一次UI状态绕过。 |
| orphan/Core 外部进程不能被收养 | management.start:421-427在旧PID活或HTTP可达时EXTERNAL_HOST_PRESENT；currentHost:335-347绑定本child；Go管理verifyParent绑定原OS父进程；`apps/control/main.go:340` EOF只记录断链保留Core | 保留foreign/orphan拒绝；正常同宿主后续Desktop只复用赢家，不再次management.start。宿主崩溃后旧Core不能伪装owned，不能凭同版本/同SID接管。孤儿恢复为明确未解决分支；不自动杀进程/删discovery/破数据锁。正常有序退出后，旧PID已退出且数据保留时应允许重开同一data root。 |
| 运行路径、验证器和闭包必须真实可安装 | Go `LoadRuntimeVerifierInstallation`与JS installedResources要求绝对真实路径、hash与空arguments；`http-wire.js:25-52`验证全部main/preload模块清单；Core仍依赖cwd下contracts/migrations | 新 builder在最终owned输出位置生成独立产品布局和安装绑定，包含CLI/Electron/Core/worker/validator/verifier、必要contracts/migrations/web与许可。重建client-wire descriptor及validator相关闭包；只拷旧descriptor会因main/lib新增文件失败。控制cwd明确，不能依赖用户当前目录或源码仓库。 |

`requestSingleInstanceLock` / `second-instance` 的官方语义支持单例转交，但不提供该应用的业务就绪确认；Windows 注销/重启不会保证触发 before-quit/will-quit。以上生命周期设计参考实际锁定版本 [Electron v37.10.3 app 文档](https://raw.githubusercontent.com/electron/electron/v37.10.3/docs/api/app.md)。因此本阶段受控退出不能被提升为睡眠、重启、故障恢复或8小时资格。转交参数只允许有限的显示/CLI启动意图与非秘密兼容信息，不能承载任意命令、token、路径执行或新增管理操作；参数属于输入，不能成为身份授权证明。

## 建议第一阶段行为

正常流程应是：首次CLI从安装入口解析唯一产品布局→启动无主窗口的Electron宿主→原private stdio链启动owned Core→等待真实READY→通过既有native取得凭据→Go CLI创建非空项目/session并写入正常数据。随后打开Desktop，只显示同宿主窗口；CLI与Desktop检查同一个host ID和Core PID/creation/image，并通过现有session控制权规则交接，不能同时写同一session。关闭后再次打开窗口仍使用同Core；明确退出并确认Core停止之后，下一次启动允许复用非空data root、项目/session身份和历史；新Core PID是正常重启，不应要求跨退出仍同PID。

无窗口宿主也必须有用户可见的打开/诊断/安全退出入口。阶段1可有tray管理入口，但不能默认将窗口close解释为“任务继续运行”：持久门未通过时，窗口close可尝试安全退出，busy则保留窗口并说明原因；用户显式隐藏窗口与继续任务不是已被本阶段接受的后台资格。CLI调用结束不应自动触发共享Core退出；如需idle退出策略，必须另外证明无活CLI/工作/待结算状态，不能靠超时猜测。

验证范围建议（后续由Root登记执行）：

1. 同时启动两次、CLI先/GUI先、STARTING期间第二次、已ready第二次：只能一个管理宿主/一个Core；第二客户端能收到就绪或失败结果。
2. 第一次创建非空项目/session→第二窗口/CLI读取同一身份→安全退出→已有数据重新打开；证明不是fresh-state launcher换名。多项目运行的CLI配置应保留已有选择/冲突语义，不能通过重置全局config令第二端“成功”。
3. 冲突安装ID/build/data root、篡改validator/verifier、活动foreign/orphan、损坏discovery：明确拒绝，无第二Core、无旧数据修改或自动清理。
4. busy/unresolved拒绝退出、重复退出、Core非零退出、确认超时：不得声称shutdown成功；JSONL不混宿主日志。原先单次empty smoke不能替代这些增量。

以上首先进行源码、构建与可控temp/mock验证；其后Root单独注册owned native范围。测试通过也只接受这段正常生命周期，不签发W13/W20/A15或C57恢复。

## CLI 包、安装绑定与其他架构

CLI发行包包含Electron可以接受：合同要求独立可用的CLI和必要运行时，并未限制宿主实现语言或包体积；用户不应被要求另装Desktop、Node或手动服务。但“独立包”不能默认形成第二套安装宿主。建议CLI包与Desktop包都是同一基础运行时/安装ID的不同入口，安装到同一canonical产品位置并共享data root；已存在相同兼容安装则明确复用，冲突拒绝。若要独立安装路径共用宿主，需补可信安装发现与版本仲裁，不宜本阶段临时用环境变量或先发现先连接解决。

verifier绑定应在最终安装位置校验实际exe hash后生成绝对路径清单，并在发行manifest中分别记录可重现包hash与安装绑定hash；安装换路径/升级则生成新的合法绑定并重新验证，不改旧封存开发清单。安装清单的source_commit是构建来源，不是独立OS身份或C57隔离证明。当前代码没有要求读取该清单必须提权；per-user安装可做，但不能从“加载成功”推导正式受保护验证资格。若新builder只是最终owned位置的可运行布局而非installer，应如实命名，不宣称安装/升级/卸载已经交付。

已有 `ops/supervisor/release_host` 明确是same-user disposable R2 fixture；其ControlFixtureDriver依赖fixture authority/canary、release journal和私有drain，不是可直接替换的普通用户管理服务。直接采用它会扩大边界并重做私有管理集成。未来独立Go supervisor可减少CLI运行时，但需要迁移父进程权属、同用户认证与特权确认UI桥，超过本阶段最小范围；当前优先复用Electron宿主更合理。

建议 exact14 原范围保留；cli_native.go纳入必改条件。若CLI启动路径能集中在hostDiscovery等已有共享入口，则无需预先扩大到main.go/resources.go；实现审查须证明所有实际host-bound入口覆盖，并保持help/version/只读doctor的明确行为。本报告不批准具体源代码、共享登记或native运行，仅提供Root登记scope所需的独立设计边界。
