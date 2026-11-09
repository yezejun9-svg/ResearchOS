# Original verifier startup / pre-Job semantic audit — CP511

结论：**NOT_PROVABLE_NO_NEW_OPERATIONAL_CLASS**。保持既有“精确协议错误分支未向 verifier 发送 Job”的窄源码推断，但本轮不注册 NEVER_JOB_AUTHORIZED_V1、不将其替代 native closure、不授权 STOP 或任何 actual 动作。formal_increment=0，待独立语义复核；本文件不是自签接受。

原 verifier SHA256 为 f255f4d49c5b217462bb38a8ec2292e9d62889d8506488569ff3638237708a43，源码提交 4f4023c956f84d65743f39ce77d6c8899a21ada1；原请求 bc269e772ada7e1bce54439fd080550c，run f3dcb996b2e43cf52cba874be7abfc70。CP511 scope SHA256 为 6c0dbca2b0606c124739e66c163f4c87aefa9f14cefae598d35595718445fa41。

## 覆盖与证据层

原始 link 包为 332，当前 selected map 为 333（额外 unsafe）；2145 个 selected files，2052 个 Go files 均匹配历史输入向量。原 binary 的 602 个 initializer-related symbols 是原始二进制数据。当前 selected map 是 reconstruction；7 个 HFiles 不在历史向量，不把它们声称为历史已采集数据。

selected-init-coverage.json 映射原始 AST 的全部 4696 条，并补录 717 条零值声明，共 5413 行；每行保留 file/hash/line/targets/group/residual。selected-file-coverage.json 覆盖全部 selected files，包括没有 initializer 的文件。完整枚举不等于完整语义闭包，没有将 5413 行标为 PASS。

分析 helper 排除 140 个未直接调用的 function-literal bodies，保留立即调用的 literal、调用参数及 target counts。finite-eager-target-inventory.json 保存 683 个 package/target-expression 对。被传入的 callback 仍可能由 callee 同步执行：FIPS CAST 在 Enabled 时明确调用 f()，所以“未在外层直接调用”不证明未执行。

| 分组 | 行数 | 结论边界 |
|---|---:|---|
| 无 eager-call 语法 | 2878 | 可能依赖其他已初始化全局值；非 transitive proof |
| errors.New | 649 | body 构造 errorString；runtime allocator 边界仍在 |
| 标准库 | 670 | 关键边界已查，全部闭包未完成 |
| Windows lazy/eager | 537 | descriptor 与 Find/Call 分开 |
| 其他第三方 | 153 | 有限 target 清单，未 blanket PASS |
| jsonschema | 7 | 嵌入输入闭包，不是 compiler 全语义证明 |
| libc/memory/math | 226 | 含真实 native 初始化 |
| SQLite | 260 | 表注册、数值转换与 mutex init 分开 |
| 其余项目 initializer | 27 | schema/regexp/lazy DLL 等 |
| 其余 pdfcpu | 6 | 显式字体/配置入口未被 initializer 调用 |

## 关键语义链

**main gate。** main_windows.go:16-41 先检查 argv、stdin/stdout pipe，Handshake 后等待完整 Job，协议与 nonce 合法后才进入 Verify；client.go:22-38 的 HTTP client/transport 构造位于该门之后。门前 main 的可见操作是继承 pipe IO、Getpid/GetFileType。保持 CP509 已接受的精确 Host 协议错误分支无短 verifier token/Job transfer 的窄推断；这不说明同 SID 进程没有 ambient 权限，也不说明进程已结束。

**实际存在启动副作用。** runtime.main（proc.go:153-346）在应用 main 前启动 sysmon、GC 并执行 init tasks；proc.go:374 init 启动 forcegchelper。runtime.osinit（os_windows.go:469-493）涉及可选系统调用、异常处理、高精度 timer、系统目录/路径能力和 SetProcessPriorityBoost。net.init 调用 poll.InitWSA；其 OnceFunc callback 调用 WSAStartup。故 literal “没有任何外部效果/后台活动”不成立。这些事实不等于发生了产品 DB 写入或模型/HTTP 请求。

**DLL lazy 与实际解析。** x/sys/windows.NewLazySystemDLL/NewProc 先生成 descriptor；Find/Call 才进入 Load。go-isatty init 明确 Find GetFileInformationByHandleEx 与 NtQueryObject；go-runewidth handleEnv 在相关可选环境变量缺失时执行 console codepage probe。前者用 kernel32.dll/ntdll.dll，后者 syscall.NewLazyDLL 参数为 kernel32。仅描述实际源码边界，不猜测恶意 DLL；历史向量不包含当时 OS DLL 实现，本轮未做当前 OS 探针。

**modernc/sqlite。** 988 个 __ccgo_fp 位点将函数指针写入生成的表；sqlite.go:13896 helper 取 interface data 指针，不调用目标函数。ccgo 数值 helpers body 为数值转换；unsafe.Add/字段布局仍是 unsafe 边界。mutex.go init 使用 NewTLS、Xmalloc、SQLITE_CONFIG_MUTEX、Xfree/Close；该 config 分支复制 mutex methods。根 sqlite init 调用 sql.Register/defaultDriver；database/sql/sql.go:54-64 存储 driver。PatchIssue199 body 是 nop，vtab.SetRegisterFunc 储存 callback。libc 同时快照环境、建立 std handle wrappers、注册 Windows callback、分配 native memory；memory.mmap 最终使用 VirtualAlloc。没有将注册当作数据库 Open，也没有将整个分配器/OS 链标为 inert。

**jsonschema。** draft.go:127 确实 NewCompiler/AssertFormat/MustCompile。newRoots 的默认 loader 是 FileLoader；defaultLoader.load 先检查缓存/loadMeta，后者优先 embed.FS。openMeta 接受 http/https 的 json-schema.org 前缀，不是 HTTP 下载。对精确 19 个 EmbedFiles 建立 resource path 的两种 scheme 映射，193 个 lexical $ref/$schema/$recursiveRef/$dynamicRef 全部映射到 embed，0 unmapped。draft04 没有自身 id，必须以 embed path 为资源 identity；015 的错误假设和失败保留，017 修正后才得出结论。资源闭包不代替完整 compiler/format callback 语义证明。

**pdfcpu。** 完整 selected initializer target census 没有调用 NewDefaultConfiguration、EnsureDefaultConfigAt 或 LoadUserFonts；这些显式函数在调用时会读/写配置或扫描字体。初始化主要为 error/literal/rectangle/regexp/IP-prefix 解析及 image callback 注册。已读取 NewRectangle/setupRegExpForPageSelection；RegisterFormat 只保存 callback。不能因为库中出现 os.MkdirAll 就判定初始化已写目录，也不能据此将全部 transitive callees 标为无效果。

完整 hash/行段在 relevant-source-refs.json；原始读取为 007/008/010/014/019/021 capture。finite-eager-target-inventory.json 是有限待核对清单，不是 SSA call graph。

## 同步 close 不能补上原 native closure

018 capture 的原始公开记录有 confirm 后 CONFIRM_REJECTED_CHECK_STATUS、后续 UNRESOLVED/VALIDATOR_TIMEOUT、worker 桥接状态及 protocol not reconciled 的历史 DB 观察；没有原 verifier 的 PID+creation+native Wait 结果。worker PID 69860 / exit 124 不能挪作 verifier 证据。DB reason 写在 Host defer 前，也不能证明 close 已返回。

精确 Go os/exec.Cmd.Wait（exec.go:936-972）调用 Process.Wait 后保存 state。Windows os.Process.wait（exec_windows.go:18-53）有 statusDone/statusReleased、WAIT_FAILED、非 WAIT_OBJECT_0、GetExitCodeProcess/GetProcessTimes 失败等提前返回。因此不是每一次 Wait 返回都意味着成功 native wait。Host close 丢弃 Wait error，waited 仅表示走过该调用路径。一般函数返回/UI 文本不能证明被忽略的 native error 不存在。

## 最小补证来源与不可追补边界

Root 追加要求的有限源码定位已完成（022-025，仅读文件，未调用产品）：

- internal/host/runtime_verifier_process_windows.go:104-112 的 cmd/identity/waited 属于局部 runtimeVerifierProcess；219-227 的 close 不返回或持久化 Wait 结果。没有找到公开 retained-native-handle / wait-result 读取接口。
- internal/host/runtime_qualification_windows.go:180-196 单次创建 process/defer close。189 的 EXPLICIT_QUALIFICATION_REQUEST Artifact 理论上包含 identity，但不含 Wait 结果；给定历史公开诊断 administration_provenance=[]。即便另有该 Artifact，也只可能补 identity。
- internal/domain/runtime_qualification_confirmation_windows.go:94-162 的 LocalQualificationStatus 返回 request/run/runtime 状态，无原 verifier identity+native completion。
- internal/host/desktop_management_windows.go:216-220,247-248 的 STATUS wrapper 先 IssueCredential，再 defer revoke。不能把它推荐为零写只读补证入口；本轮未调用。
- 以上是当前源码定位快照，不是原运行 Core 的内存或二进制 attestation。

唯一有界补件：证据所有者若能指出**已经存在**且绑定同一原 verifier 的 native handle / Wait-success / closure receipt，则单独核对 hash、PID+creation+image、请求/attempt 归属和成功结果。当前材料未提供，现成公开接口也不提供。若不存在，历史 successful Wait 事实不能从当前 PID absence、重启、下一次运行、添加 logger 或 init 分析追补。未来源码可为未来启动保存此类收据，不能倒填本次。

可实际采用本报告保留窄 Host-no-Job 诊断并保持 native-closure 缺口；Root 选择明确的恢复/范围决策，保留原失败计数和证据。本报告不提出新 broad 类，也不授权 termination、replacement、actual 重试或 Source 改动。

## 残余与验证

residual-matrix.json 明列 R1 有限 transitive/callback 闭包未完成；R2 runtime/native/OS trusted boundary 不完整；R3 七个 header provenance 缺口；R4 原 verifier closure 历史事实未捕获；R5 已存在公开 readback 路径不提供该事实。R4/R5 已足以阻止 native-closure 替代，不为强行得到可用类继续广搜。

capture_analysis.py 在执行前写 exact recipe/environment，保留 stdout/stderr/native exit。Go helper 只 parse 源文本，未 import/运行产品；构建禁用 module/network，缓存位于本收据目录，收尾删除临时 analysis cache/tmp/gopath。015 失败保留；022 rg 的不存在 apps/core 路径产生 native 2，而 outer 分析 native 0，二者在 ledger 分列，023/024 用存在的限定路径完成定位。工具展示截断不影响完整 raw。

无新 operational class 或 Source 改动，故没有新增产品或 class-tamper tests。验证限于 input/source hashes、覆盖完整性、资源映射和 artifact/manifest 一致性。没有 current DB/OS process probe/private pipe/key/GUI/API/model 操作，也未编辑共享 Source。
