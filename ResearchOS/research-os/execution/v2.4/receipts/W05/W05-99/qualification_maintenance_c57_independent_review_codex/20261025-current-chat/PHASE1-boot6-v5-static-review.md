# Boot6 v5 六文件独立静态复核（PHASE1）

结论：NEEDS_WORK。发现 3 项 P1 源码问题；本报告不构成 Source acceptance、native qualification 或 combined57 phase2。既有 73 项断言不改、不新增永久验收清单。

复核对象为 final-v5-six-source-manifest.json（SHA256 175b24b640edf7d8a7924db527c93400125299278632e58d8f73ffeceb31a3d0）所列的准确六文件。主文件 internal/recoveryboundary/boot_windows.go SHA256 74362237c5b3d8da423070ccee580a1a6d20546e10d3eba60f3894d4e673ae3c。031 已复制并验证独立快照，032–036 为静态读取。所有行号指向该快照。没有运行候选 Go 测试、操作原环境 ACL/进程/注册表、创建账号或重启。没有读取新的 mutable 父模块依赖。

## 需要修复的源码问题

1. **P1 — arm 前未证明能恢复异 SID 的原 owner。** boot_windows.go:1014–1028 的 preflightManagementRestore 只验证 READ/WRITE_DAC/WRITE_OWNER handle 及原始 identity；1388–1400 只验证 management elevation/user。1809–1816 随即开始写 APPLYING 并将 owner 转给 manager，1965–1967 却通过同一 setTargetDescriptor 把 owner 恢复为原 BusinessSID。在原 owner 不属于管理 token 可指定 owner 的 SID 且 SeRestorePrivilege 未启用时，WRITE_OWNER 可以允许接管为管理自身，却不允许归还异 SID；因此当前预检可以通过并装上围栏，直到 disarm 才失败。1062 的 manager WRITE_OWNER grant 不能补足该条件。应在任何 mutation 前核对每个原 owner 的实际可恢复性，并在实际 mutation token 中验证所需恢复权限；资源不可用应在 APPLYING 前失败。285–323 的测试只构造描述符，213–283/397–490 的同 SID fixture 不能覆盖此问题。API 依据见 Microsoft SetNamedSecurityInfoW psidOwner 条件及 SetSecurityInfo owner eligibility：[owner requirement](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setnamedsecurityinfow)、[same-handle API](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-setsecurityinfo)。这是预检缺失的源码问题；生产 distinct SID/privilege 资源尚未证明是另一项限制。

2. **P1 — 目录 ACL 检查不能证明记录文件受保护。** boot_windows.go:340–418 的 readRecord 在 checkManagedChain 后直接 os.ReadFile(plan/pre/post/event/full-restart)，479–495 只核对目录；582–600 也直接读取 pre/post。1403–1439 虽对 acceptance 文件调用 openNative，但未验证所取 SecurityDescriptor 的 owner/DACL；readFullRestartEvidence 同样没有文件 ACL 检查。合法管理目录可以含有显式授予业务用户 WRITE_DATA/WRITE_DAC 或业务 owner 的子文件；具备通常的 SeChangeNotifyPrivilege 的业务用户可按已知路径访问该文件，不受父目录遍历拒绝保护。事件 SHA 链和见证字段均可重算，不能替代文件的写保护。攻击者/错误 staging 可在目录检查通过时改变 pre/post/event 或 FullRestart completion 记录。应逐个验证实际读取 handle 的 owner/DACL、非 reparse/单链接身份，并从被验证的对象取得内容；写新记录时确保有效文件权限，不能只依赖目录检查。checkManagedDescriptor 也未要求可继承 manager ACE，进一步说明父目录通过并不能推出子文件策略。API 依据：[Bypass traverse checking](https://learn.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/bypass-traverse-checking)。这是记录认证路径的源码缺口，并非缺少真实 FullRestart 资源。

3. **P1 — disabled-but-enableable group 被当成无权组，不能支持不可撤销的祖先围栏。** boot_windows.go:624–638 仅把当前 SE_GROUP_ENABLED 且非 DENY_ONLY 的 SID 放进 EffectiveSIDs，999–1000 对其余 trustee 一律跳过。若业务 token 内存在普通 disabled（不是 DENY_ONLY）组，祖先 DACL 给该组 WRITE_DAC、WRITE_OWNER 或 FILE_DELETE_CHILD，目前可以通过检查；业务进程随后以 TOKEN_ADJUST_GROUPS 启用自己 token 的该组即可改变/替换祖先。反复查询 Explorer 的当前 enabled map 也不能阻止另一个业务进程启用它自己的组。应保留完整 group attributes，明确区分不可启用的 DENY_ONLY 与可启用的 disabled group；对后者拒绝危险祖先授予，或提供等价的不可启用证明。权限摘要同样不能把二者都无声丢弃。不要将此项修复成忽略 BA/DENY_ONLY 的 blanket allow。API 依据：[AdjustTokenGroups](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-adjusttokengroups) 明确允许启用已有组，但禁止启用 DENY_ONLY 组。这是条件明确的源码漏洞；本轮没有声称当前机器实际 token 含有此类组。

## 已落代码的修正与限制

- WTSQueryUserToken 路径已移除；现有系统 Explorer 使用 PROCESS_QUERY_LIMITED_INFORMATION + TOKEN_QUERY，匹配 BusinessSID，并记录 PID、创建时间、session、logon SID 与镜像 identity。跨重启不要求相同 session/logon/PID；当前 post witness 仍绑定具体进程来源。此项为静态确认，不是跨账户 native probe 成功。
- OS ancestor 检查过滤 INHERIT_ONLY 与 DENY_ONLY 对 allow map 的贡献，保留危险有效 ACE 检查。D root 的保留样例及其测试使用 SYSTEM owner；本轮不宣称任意其他 OS owner/ACL 组合均已支持。
- target owner 转移、精确业务 deny、manager restore rights grant、arm 前祖先检查、同 mutation handle identity/SD 比较及读回均在冻结代码中。它们没有消除上述第 1 项 owner eligibility 问题；同 handle 也不等于与其他特权管理者并发修改的原子 CAS。
- CurrentQuiescence 的 owner 私有、值复制共用 owner，Check/Close 用同一 mutex；Close 先置 closed，汇总 CloseHandle 错误并清空 holds。原 os.NewFile finalizer 问题已去除。本轮没有作外部 SQL transaction 整体 lifetime 的正式结论。
- 作者 v6/v6b 的 own TEMP fixture WRITE_OWNER 失败及其补跑，不在本报告转换为 source/native acceptance，也不计作 reviewer 失败。生产 distinct management/business SID、实际跨账户 TOKEN_QUERY、完整恢复能力及真实 FullRestart 仍需对应 native 证据。
- 既有 73 项断言仍为 prepared；不更改历史计数、报告和 seal。本轮 reviewer 新 native 非零 0、tool diagnostics 0；此前 reviewer native 非零累计 2 保持，作者和 Root 的失败各自保留。

证据索引、准确六文件、旧成果不可变校验和本轮原始回执 SHA256 见同目录 PHASE1-boot6-v5-static-review-seal.json。网页发现结果与三份官方 API 内容已追加保存在 WEB-boot6-*.json；仅上述 Microsoft 主来源用于技术判断。

