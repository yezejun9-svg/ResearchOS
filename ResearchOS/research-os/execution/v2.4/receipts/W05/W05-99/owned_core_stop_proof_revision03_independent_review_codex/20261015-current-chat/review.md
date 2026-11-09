# STOP-r3 独立 Source 审查

结论：**NEEDS_CHANGES**。候选 `2816daacdb2c08ae8ee1d62c91bcd3f571d40737`，tree `67fc84be0238b724f7d0ec41eb4c8b688b0269f3`；核对 Main4f 起全部 19 路径及 rejected f5 起 7 路径。仅有一项 P2 实质缺陷；未修改 Source/Main/共享状态。

## STOP-R3-F01 / prior STOP-R2-F03 — 初始 owner/DACL 未作授权判断

`ops/supervisor/owned_core_handle_windows.go:111–128` 只要求 owner SID 有效、DACL 非空，随后保存 SDDL；`verifyOwnedImageFile` 只与初始值比较。无 trusted-owner 判断，也无外部主体写入/控制 ACE 拒绝。

独立 Go overlay 在真实 Windows 上复制当前测试程序，启动该映像的 parent 与 child。分别把映像祖先设为 `D:P(A;OICI;FA;;;WD)`、最终映像设为 Everyone 完全控制，两个样本均通过 `ObserveOwnedCoreReadOnly`、`OpenOwnedCoreRetained` 和 `verifyRetained`。这证明初始不安全 ACL 被接受。信号数为 0。v2 原始输出与 overlay 血缘见 review.json 的 finding.evidence。

三个边界分别处理：owner 只做有效性检查是源码证据，本轮未创建 foreign-owner/user；直接与继承的外部写 ACE 接受是动态证据；祖先 `FILE_SHARE_WRITE` 在保留期间确实允许另开 `GENERIC_WRITE` 目录句柄。现有正常测试的最终映像写共享拒绝、祖先重命名拒绝均通过，因此不宣称已完成命名空间替换或 hostile race。目录写共享需满足卡片的 deny-write 要求，或提供同等强度的原生保护证明，不能仅凭保存 SDDL 认定授权。

最小修复范围为 `ops/supervisor/owned_core_handle_windows.go` 和 `ops/supervisor/owned_core_handle_windows_test.go`：明确可信 owner 与 ACE 策略，正确处理继承、inherit-only、直接权限和安装/系统所有者；对每级 Core/parent 映像路径检查并保留约束。保留同一句柄 hash/ID、nonreparse、hardlink 与逆序关闭。增加真实 copied parent/child 的安全 ACL 正例、Everyone/Users 直接和继承写权限负例、owner 策略边界及相关目录原语测试。

## 其他修复与覆盖

F01 支持修复：本轮自己编译 fixture 和两类 grant 程序。正常流程 `STOPPED_LEASE_VERIFIED`，一次原生终止、exit `1381191507`、postflight 87 表 35 行且 census 一致。worker 缺 `native_exit_code`、verifier 缺 `native_wait_result` 均在 preflight 变为 `STOP_UNAVAILABLE`，没有生成 STOP grant、没有 attempt/intent。28 个数值存在性/范围测试通过；七类 proof 保持严格，每类独立解码。fixture 历史回执仍是明确标注的 synthetic，不作为原产品 native Wait 证明。

F02 源码修复受支持：caller context 与更早 deadline 传至 retained native 层，intent 前后及 prewait 后都有检查。聚焦取消、较早 deadline、prewait 取消与持久消费 journal 测试通过。源码可组合说明 consumed attempt 不重试；**完整 live Commit 在自身 intent flush 后取消/到期未被确定性执行**，保留为覆盖限制，不冒充已执行全路径，也未发现新取消源码缺陷。后续最小 cut 是完整 Commit 的确定性测试接缝、零信号/UNKNOWN 与另进程 replay，不能添加生产授权开关。

COV01：六种 synthetic journal image 经真实 CLI 重入/重复；third grant 仅 claim 点；preflight reset 拒绝覆盖四个正常 claimed 点。torn/orphan 的 reset、各点并发乘积未全做，r3 无新增 concurrent CLI case。它们不是实际杀死 grant-aware CLI 或断电试验。COV02：真实 Core/parent 的 hardlink、reparse、rename、write-sharing、wrong parent 测试本轮通过；wrong expected SID 不等于外部用户进程；F03 的初始 ACL 仍阻塞。COV03 保留 F02 集成限制。COV04：作者 six danger cuts 真实 CLI 为 `STALE_PLAN`、零信号，但因完整 census 先变，不能声称每个 deeper SafetySnapshot 分支都动态走到。COV05：三类 malformed compiled grant 与两类 CLI flags 有真实拒绝；数据文件快照只涵盖可读文件，`coordinator.lock` 不可读已列明，不是所有文件 open 的全局追踪。

## 证据与诊断

作者 583 个引用的大小和 SHA256 全部核对通过。80 条新 nonzero 与原始 before/after/raw 对照，71 为预期拒绝、9 为保留诊断；旧 63 条不重复累计。作者首轮 malformed-grant harness 读取活跃锁失败未抹去。

独立审查自己的首次 ACL 祖先试验因不继承 ACE 造成 child launch AccessDenied；修正为 OICI 后才得到两个有效失败断言。第一次 cleanup 因 Windows PowerShell 无 BOM 的中文路径解码失败；v2 使用 BOM 后仅删除经边界核对的自身临时目录。首次报告脚本生成发生嵌套引号 SyntaxError，随后 logger 记录缺失脚本 exit 2，改用直接文件 patch 写入。初始 read-only discovery 与部分 own-E 脚本写入没有独立 logger 包装、首次复合 Git 读取掩盖子命令退出码等实际 gap 均列于 diagnostic-ledger.json，没有宣称零缺口。

Root 另行确认作者 12:21:24 的 scope bootstrap read-before-logger，是两个 reset 后 Git read gaps 之外的单独事件；本报告作为 Root 消息补充登记，由 Root 下一 CP 落账，作者冻结文件不变，也不把此审计遗漏列为 Source 缺陷。

最终 formal 增量 **0**。本结论不接受 Main、原始 actual Core、当前 data root、provider/model、W05 父任务或正式用例；boot recovery 不在本卡。
