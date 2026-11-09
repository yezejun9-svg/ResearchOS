# v7 SDDL 恢复补充：原目标兼容性与 API 能力边界

结论：**不能把“无 AI 全拒”变成已完成的最终合同，也没有依据把 AI 差异忽略。** 历史采用目标确有无 AI 分支。可继续验证一个有限的同 handle 原生完整 SD 写入候选；本轮没有证明其成功，也没有证明 Windows 必然无法精确恢复。

**原目标历史事实。** 已重新验证 file-ancestor-metadata.json SHA256 f4c58e80940d0dc81ce9c0bac70a1131030238c27cfe7e9347e749ac33d71cc5。其 67 个记录中 PUBLIC_PRODUCT_TARGET 22 个：16 个 C 缓存包文件有 AI，6 个 D repo 文件没有 AI（record 51/55/56/60/63/66），包含实际 repo main.js 与 desktop-management.js；共享 electron.exe 也在该历史 inventory，但不能因此推定它是允许撤执行权的 fence target。C home 祖先 record2 为 P 无 AI。以上是 20261015 历史 metadata，不是当前 native identity/ACL 证明。对所有 target 加无 AI 拒绝会阻断至少 repo main.js 的历史分支，不能静默报告完整能力。逐条路径、control 与 SDDL digest 见 HISTORICAL-v7-sddl-contract-extract.json。

**既有合同。** design-review.md SHA256 3965106935192d75a8bff39d5c21edd3d98e63417f1ed19067c8a36d2e2f290c 的37行要求保留 owner/group/DACL/可读 SACL、保护/继承控制位及 binary SD；39行虽使用“按字节/语义保留”，同时要求全 SD 保真、ACE 次序与继承传播可解释；98行要求 exact preimage/installed 比对恢复。采用文件 boot-proposal-adopted-limits.json SHA256 5933670aa546382834ad4309d7d2debc7ed0f065ed82ddc4df6b2b5848a22e6b 未授权忽略 AI。因此“等价权限足够恢复”不是本轮可以自行解释出的豁免；原始取证保留与当前 same-handle 精确校验都不能改写。

**最小实现候选与限制。**

- SetSecurityInfo 可以用于目前已见的现代继承模型 PAI installed，但它的参数传 O/G SID 与 DACL，不直接传入完整 SD control；不能把内存 SetSecurityDescriptorControl 清 AI 当作已对文件清 AI。恢复原无 AI 描述符是否可行，需要另一原生写入路径的实际结果。
- 可在现有 boot_windows.go 内有限验证 **NtSetSecurityObject(同一 retained handle, 精确 SECURITY_INFORMATION mask, 保存的完整 self-relative SD)**。微软 [ZwSetSecurityObject](https://learn.microsoft.com/en-us/windows-hardware/drivers/ddi/ntifs/nf-ntifs-zwsetsecurityobject) 文档明确允许 absolute/self-relative SD，并明确 user mode 使用 Nt 名称；DACL 写要求 WRITE_DAC，实际 owner/group 变更再要求 WRITE_OWNER。这给出同 handle 完整 SD 的候选，不要求新服务、账户或架构。官方页面没有承诺 AI/control 位可逐位还原，所以“该调用可以精确清 AI”仍是假设，必须由作者 own fixture 证实。不能直接将 SetSecurityInfo 的 PROTECTED/UNPROTECTED 标志复制过去后假定语义相同；原 control、ACE flags 和实际读回才是判断依据。原 owner eligibility 仍适用，NTSTATUS 必须完整保留并正确失败。
- 有限验证应覆盖已需要支持的 legacy 无 AI 与 modern AI 原始 SD，两类都保留原始 O/G、ACE 类型/SID/mask/order、P/AI 与 ACE inheritance flags；装围栏后恢复时完整同 handle 读回相等，reopen 再验证，父链与兄弟对象不变。若 Nt 路径只适用于无 AI，而现有路径能精确恢复 AI，可将选择绑定到冻结原 descriptor 类别；不得根据失败结果临时更换比较规则。上述是已有恢复断言的实现判据，不新增永久清单，本 reviewer 未运行这些测试。
- 不使用 SetKernelObjectSecurity 文件对象捷径：微软明确不建议用于文件系统。SetFileSecurityW 虽接受完整 descriptor，但[官方页](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-setfilesecurityw)已标 obsolete，且是 path-based，不满足当前 mutation same-handle 要求。BACKUP_SECURITY_INFORMATION 引入整个 SD 的额外权限/组件，不是仅修 AI 的无条件替换。[SECURITY_INFORMATION](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-information)。
- 如果这个有限候选仍无法保真，明确报告 **已采用 legacy 分支的原生精确恢复能力未实现**，保留 pre-mutation 阻断以防先写后不可恢复；这不是“缺一个普通资源”的完成状态。由 Root 决定如何处理合同/范围，不可归零失败、把该分支藏进永久 unsupported 或预先改原 ACL。若候选成功，也只是对应 owned fixture 证据，异 SID/实际密集 ACE/真实重启还须原有分层资格。

本补充澄清上一 advisory 的“无 AI 拒绝”仅是未证明恢复能力时的临时安全门禁，不是最终 supported-set 改写。旧报告及 seal 均保留。041–045 全是只读历史/文档检查，新 reviewer native非零0、tool diagnostics0，累计 native非零仍2；73断言与 combined57 phase2 状态不变。搜索发现中的社区 Q&A 未用于最终 API 结论，技术依据仅上述微软主文档。

