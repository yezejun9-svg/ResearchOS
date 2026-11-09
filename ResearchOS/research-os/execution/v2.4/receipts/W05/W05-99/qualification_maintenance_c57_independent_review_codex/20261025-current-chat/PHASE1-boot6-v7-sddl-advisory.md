# Boot6 v7 SDDL 窄咨询（只读，不签接受）

结论：本次报错包含两个不同原因。v7-sddl-01 的 G 缺失属于读取字段不一致；v7-sddl-02 已修复 G，只剩 D:P → D:PAI，owner、group、ACE 顺序/掩码/flags 均相同。这一条原始输出没有显示实质访问权变更，却暴露了 installed 预期及原 SD 精确恢复合同需要分别处理。不能把 AI 删除后宣布恢复成功。

**固定输入。** 039 复制 mutable boot_windows.go（35b241e4e1e7447cb143e865ec75eae93328bb7fcb647ea70a25c710fa6e206c）及 boot_windows_test.go（d01f5f7f76f5ce8e92f8fd8a8e25f405aa0c5e6d519a4ff1d373122ad2e9a2b6），复制 v7 raw/recipe/nativeexit 并验证捕获前后相同。对应 raw sddl-01 SHA256 4482f01822edfca16c1b05c9bc6e8a4bc60e193ebc7702a6615f2c2c0bee00ba，sddl-02 SHA256 8f8909f8b8c2b871dfd6e4bc78d5935ad9fa5891d82525486e1caa29e67770a2。源码是咨询时的 mutable 快照，不能推定它与更早测试二进制完全相同。

**原因和最小修正。**

1. 统一目标身份 capture、mutation 前检查和 mutation 后读回的 SECURITY_INFORMATION 为 OWNER | GROUP | DACL（当前快照124、1777行已如此）。GROUP 未请求时，返回 descriptor 无法与包含 G 的完整计划直接比较；这不能解释成 group 实际被清空。[GetSecurityInfo](https://learn.microsoft.com/en-us/windows/win32/api/aclapi/nf-aclapi-getsecurityinfo) 明确按请求字段返回。没有 group 改动时不需要写 GROUP，但必须验证它保持原值。

2. denyDescriptor 的1271行只设 P，SetSecurityInfo 的1774行执行后系统返回 PAI。Microsoft 说明该 API 使用当前自动继承模型，并给转换后的描述符设置 AUTO_INHERITED；P 与 AI 是不同控制位，AI 也不等同于某条 ACE 的 INHERITED_ACE。[自动传播](https://learn.microsoft.com/en-us/windows/win32/secauthz/automatic-propagation-of-inheritable-aces)、[控制位](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-descriptor-control)。建议在编译 installed 计划时通过结构化 SD API 明确构造预期 P|AI，保留 O/G、DACL present/null 区别、ACE 类型/SID/mask/全部 flags/顺序；继续要求同 handle 精确读回。只允许设计已规定的围栏 deny、manager grant/owner 与继承转显式变换。不能对输入/输出 SDDL 字符串批量删 G、P、AI，不能在写入后把未知读回直接登记成新 InstalledSD。

3. **原 SD 恢复不能套用上述 installed 规范化。** 原始 descriptor 与 SHA 必须保持。若原始没有 AI，而当前 SetSecurityInfo 会将它转换为 AI，那么本轮证据未证明原 descriptor 可精确 round-trip；仅令比较忽略 AI 会改变既有契约。最小保守门禁是在 mutation 前拒绝尚未证明可精确恢复的 descriptor 类别，返回明确 unsupported-exact-restore，不改原环境。已含 AI 也不是自动通过，仍须逐项 owner/group/ACE/继承位及父链稳定性验证。若要支持无 AI 原始对象，应另证实际可用且符合同 handle 原生恢复契约的方法，或由 Root 明确处理语义恢复与精确恢复契约差异，不能由实现偷偷降级。owned fixture 可以在第一次 baseline 捕获前用相同 API 建立 native descriptor；这只验证该类别，不覆盖无 AI 原环境。不要改用 SetKernelObjectSecurity 规避：其[官方文档](https://learn.microsoft.com/en-us/windows/win32/api/securitybaseapi/nf-securitybaseapi-setkernelobjectsecurity)明确不应将其用于文件系统对象。

4. 当前仅在 owner 变化时请求 WRITE_OWNER（1761–1765）是合理的最小权限修正；不替代异 SID owner eligibility 和实际恢复权限门禁。此咨询不签署此前三 P1 的关闭。v7-focused-01 的4PASS 是作者回执；full-01/full-02/sddl-01/sddl-02 的exit1全部保留。此外 post-write readback mismatch 已发生 mutation，不能仍标为“fixture WRITE_DAC unavailable”并 SKIP（raw full-02）；应标失败并执行可审查清理/恢复。前置真实资源拒绝与写后不匹配须区分。

本轮没有运行候选测试、改源、操作原环境或创建新永久断言。固定73、旧静态3P1报告/seal保持原样；新 reviewer native非零0/tool diagnostics0，历史 reviewer native非零累计2。后续 exact57 phase2 尚未开始。依据只来自上述固定快照、作者既有 raw 与微软主来源；引用和哈希见 PHASE1-boot6-v7-sddl-advisory-seal.json。

