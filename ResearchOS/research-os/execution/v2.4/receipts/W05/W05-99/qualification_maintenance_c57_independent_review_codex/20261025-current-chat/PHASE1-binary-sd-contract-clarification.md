# Binary SD 合同澄清与 v7 字节差异定位（只读）

结论：核对的已采用设计明确要求**保存完整原生 binary preimage、owner/group/control、ACE 与继承保真，并精确比对恢复**；未找到“NtQuery 返回的整段 self-relative buffer 必须逐字节相同”的独立原文条款。因此不能凭一个未明文定义的 buffer memcmp 自动裁定永久不可实现，也不能把 full/exact 降为 SDDL 字符串相等。本例不需要靠这一解释分歧作决定：作者 raw 的四条 native ACE flags 实际变化，且当前快照没有 binary preimage 存储/消费，均尚未满足原有要求。

## 原文与采用链

以下行号指向原文件，已复制进 BINARY-contract-snapshot 并核验 SHA：

- BOOT-C-ARCHITECTURE.md（39e1d66f…）61行：“撤除需要同operation exact before/installed security descriptor、全目标readback和最终C classification；只还原自己确实写入且仍匹配的descriptor”；63行要求“受保护离线恢复清单、原始descriptor、全部native identity”。
- actual-deployment-plan-reviewable.md（960b47d3…）8行：“每个target的读回完全匹配expected installed descriptor”；14行：“目标current descriptor==installed逐一恢复original并readback”。
- 独立 design-review.md（39651069…）37行：“保存原 owner/group/DACL/SACL可读部分/保护与继承控制位及 binary SD”；39行：“须按字节/语义保留”以及“全 SD 保真、ACE 次序、最终有效权限和兄弟对象不受新增继承影响均需 native 验证”；98行：“按 exact preimage/installed 比对恢复”。
- design-review.json（3107fdba…）272–278行 required_artifacts 明列：“full original binary SD and owner/group/control flags”、“per-object before/installed/restore SD delta and native ID”、“restore current==installed CAS and pending-C fence retention”。
- boot-proposal-adopted-limits.json（5933670a…）2–5行通过 FINAL-manifest SHA97a51cd5…引用该独立设计；21行要求 preserve dense deny preimages，146行要求 dense-ACE-preserving deployment and restoration，153行要求 authorized exact shared ACL delta/readback。没有加入 query-buffer-byteequal，也没有准许删 control/ACE flags 或用 SDDL 代替 binary 保存。

以上原文所能确认的是保存与完整恢复义务。39行“字节/语义”不是忽略原生字段变化的豁免。是否将可能仅有布局/填充变化的 buffer 视为等价，需要明确字段级证明与 Root 对合同的判断，本咨询不新增或放宽阈值。

## 本例的差异是字段变化

独立只读解析作者 v7-binary-02.stdout（SHA d74238d47b06c12e68beaf65608be2fadcf2a5cdc98dae074a1e74a9faad93cc）中的完整 hex，结果保存在 BINARY-native-ace-diff.json：

| 项目 | before / after |
|---|---|
| 长度、SD revision、control | 均172B、revision1、0x8004 |
| owner/group/SACL/DACL offsets | 均20/48/0/76 |
| DACL revision/size/count | 均2/96B/4 |
| 唯一4处差异，零起始 byte offsets | 85、109、129、149 |
| 每处字段 | 对应 ACE_HEADER.AceFlags，0x00 → 0x10（INHERITED_ACE） |

四条 ACE 的其他字节及所有其他 buffer 字节相同。不是 padding、component offset 或布局差异。作者日志所示 GetSecurityInfo SDDL 前后均含 ID，不能据此否认原始 NtQuery before 没有该标志。微软 [ACE_HEADER](https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-ace_header) 将 AceFlags 定义为实际 ACE 控制字段，INHERITED_ACE 表示继承来源。因此本结果未证明继承保真，v7-binary-02 的测试退出0不等于这个断言通过。

## 当前源码中的保存/恢复缺口

本轮只读 mutable 快照 contract.go SHA13e0374f13ec9135709f4caa8cfe40dfd4f40a9aa320b812eff1c1619d33930d：26–40行只保存 SecurityDescriptor string / InstalledSD string，没有原生 binary preimage。boot_windows.go SHAcaa5bba5263564ee0c51609fc1b44cec974cc59ec9680cf0e5d1eb1dd7ca707a：125–129行 GetSecurityInfo → sd.String；1734–1735行将 desiredSD 字符串重建 descriptor；1801–1806行只比较高层 SDDL。这条路径不能满足“保存 full original binary SD”，也解释了为什么 SDDL 一致不能证明原生继承位保真。这里定位的是咨询时快照，不能推断后续作者修改状态。

Root 已明确要求在原6内保存/绑定/消费 NtQuery 同 handle 真实 binary preimage，展示 SDDL 从保存 raw 派生，恢复使用原 binary，Installed 计划也绑定确定 native 表示，并核对恢复后完整字段与 bytes；无 AI 原 ACE flags0→围栏→恢复0必须成立。本咨询不代写或运行修复，不把这些要求改为新的永久断言。保存内容的 query mask/可读组件边界须明示，不能以 O/G/D 查询声称已保存未读取的 SACL。

是否继续 sourcefreeze 由 Root 决定；本报告没有签署 Source/native/combined57 接受。原始 binary_equal=false、原作者退出码、所有失败/历史报告保持；本轮 reviewer 047–050只读原文/解析、051封存，新 native非零0、tool diagnostics0，累计 reviewer native非零2，73断言不变。后续真实修复留待 exact57 phase2。

