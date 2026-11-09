# Trusted Host v2 独立修复复审

结论：**PASS_SOURCE_FIX_SCOPE_WITH_OPEN_RUNTIME_GATES**。原审查 R1–R4 及 S1 的 prepare 重复创建窗口已在这版固定 Source 中关闭；无新增源码阻断。保留一项非阻断工具 schema 一致性建议和执行前的 Root/native gate。本结论不代表 runtime qualification、provider acceptance 或正式用例新增 PASS。

Source：mu_sdk_trusted_qualification_host_source_revision_codex/797a5659dec64d55a16915d1aea6e46c。
Source manifest：a86da829b9ac3e54140815bbc599d7e19735e838efa50c22d63ae71aea5ed653 / 11882 bytes。
原独审：mu_sdk_trusted_host_independent_source_review_codex/a23894ca628e4e2c85ead05c283d73aa。本次复用其未变 API/资格链路分析，只审差异及组合契约。

| 原发现 | 新证据 | 结论 |
|---|---|---|
| R1 GO 验证后重读 | execute.go:81–86 从单次 raw 计算长度和 hash；117–119 readPinnedObject 解码同一已验证 raw；122–132 四个支持记录全部经此入口。 | CLOSED_SOURCE |
| R2 profile/Node/bundle 重读 | main.go:121–130 单次读后验 hash并返回raw，140–142存入seed非JSON字段；prepare.go:81–83 直接消费 ProfileRaw/NodeRaw/BundleRaw，97从这些raw产生hash。 | CLOSED_SOURCE |
| R3 Workspace 无共同布局 | main.go:139 要求 dataRoot 在 repo/.local、workspace 精确等于 dataRoot/workspace、vault 与dataRoot双向不包含；原 verifyEvidenceWorkspace 保留 canonical/non-reparse 与仅evidence.txt。符合 observer v2:279–286 和 v9:996–1000。 | CLOSED_SOURCE |
| R4 工具策略不一致 | prepare.go:107及profile模板均1/4096/4096/write_paths=[]；v9:932–934改为[]；Main Empty() 返回[]any，runtimeToolPaths接受数组。 | CLOSED_SOURCE_WITH_V9 |
| S1 prepare 租约外存在检查 | prepare.go:21 openEnvironment成功持有lease后，24检查state，28写PREPARE_CLAIMED；defer close确保检查与持久化在同一租约内。 | CLOSED_FOR_PREPARE |

R1 的 GO 顶层字段校验保留：schema、project、draft goal、runtime、qualification task/run/epoch、profile hash、started UTC、Host ID/PID/URL、provider计数3/1/2、READY/discovery/coordinator路径及coordinator pin。RootGrant、OnceMarker、OuterJobContract、HostJobProbe 的语义检查函数与旧版逐文本一致，校验入口改为消费同一验证buffer。前三个只做完整性对照的文件仍经 verifyPin。顶层authority路径来自Root stdin；其受控创建及冻结仍属于Root职责。

R2 对prepare封存输入的修复成立；未来执行仍会通过路径读取Node/bundle，原本的runtime路径生命周期问题仍为OPEN，并未因本次同buffer修复自动关闭。

🟡 **A1 / 非阻断：read schema 的 maximum 仍为65536。** prepare.go:91向模型宣称limit最大65536，实际policy为4096；Main runtime_tools_windows.go:316–320使用policy作为默认limit并拒绝大于policy的值，因此不会越过4096读取边界，但模型按schema生成4097–65536会遭拒绝，可能浪费这次有界试验。建议下次新Source把schema maximum同步4096；本次不修改已冻结Source。

原S1中对admit/execute的状态读取建议并未在本版展开；本次关闭的是已确认的prepare重复创建窗口。Root仍应串行执行prepare/admit/execute并禁止失败后的自动重试。

验证：新manifest的42引用逐项匹配；原独审41个输入引用重新核对；共67个独立路径快照。四个变更文件的正反向diff均按实际Source重新生成核对，hostapi.go及seed/GO模板不变。9项源码定位检查和3项独立期望模型负例通过。期望模型仅说明pin改变被拒绝的规则，未执行或模拟真实Go运行，不作native证据。

作者早期消息给出的revision diff hash/bytes已过时；本审查实际消费正式manifest中的revision.old-to-new.diff：34e82ccaa52716ea9f1e8cdf6b8e33e54279f4342bd5dde28802af9e97acda07 / 9982 bytes。本次没有pin不匹配失败，使用正式manifest实核字节。

## Root 新版编译证据

已读取并核对Root提供的compile.closed.json、compile.invocation.json、before、intent及stdout/stderr原文。named-file argv精确指向本版四个Go文件，actual_native_exit=0、timeout=false、异常为空；记录的owned Job为assigned-before-resume、active=0、idle/primary-exit/handles-closed=true、errors=[]，冻结Source/Main/canonical检查均为true。

编译输出binary当前SHA-256 f21e64d17ec997823c55c9bb540455f0be36cce2f6571a32864c25a3ba1111ba / 32090624 bytes，与closed记录匹配。审查者仅核对记录和当前binary身份，未重新观察过去的OS执行，未执行binary。详见compile-evidence-review.json及build-evidence/。

Source原HANDOFF中的“新版未编译”为作者封存时状态，Root后续编译证据作为本次追加事实，不回写原HANDOFF。TargetHost仍0、provider仍0，不计入22用例或正式资格。

## 下一步必要的实际验证

1. Root完成路径guard非作者源码审查后，用无provider负例验证所有Source/Python/Node/bundle在指定期间受真实句柄保护；写入/替换被阻止，partial-acquire/启动失败/正常退出均释放句柄，无遗留锁。
2. 实际隔离Host prepare/admit-only/READY流程确认原DRAFT目标保留、真实Run/PREPARED dispatch、HTTP/native discovery与Host身份绑定，且GO前provider=0；先核对实际profile为1/4096/[]和正确profile_ref hash语义。
3. Root controller证明Host、CLI、Mu整棵Job树和统一300秒deadline；取消、stdin EOF、启动异常、超时均应核对实际树终止及handles关闭，不能以any-Job或JSON自述代替。
4. 仅在Root实际授权及所有gate闭合后，执行一次qualification+两次ordinary的真实链路，按原生Run/LOG/DETERMINISTIC_SERVICE acceptance/qualification及provider账本对账。源码和编译通过都不授权本审查者发起调用。

本回执只写自己的审查目录，未改Main、候选Source、canonical或既有回执。没有新增只读失败。旧审查4条locator错误仅按Root映射683/684/685/686引用，不重新计数、不改旧封存。

