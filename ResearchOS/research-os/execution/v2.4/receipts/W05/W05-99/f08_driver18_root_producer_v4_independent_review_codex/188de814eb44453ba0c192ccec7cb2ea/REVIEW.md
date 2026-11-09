## Review Summary

**Verdict:** APPROVE — READY_SOURCE_PREPARATION_ONLY。

**Overview:** v4 仅闭合 R01-V3-FRESH_PARENT。首次 staging 会拒绝非空旧 namespace；合法新空 parent 与后续 draft/native 布局仍可行。实际 Root 授权与执行条件仍 OPEN。

### Critical Issues
无。

### Important Issues
无新增。上一项已在源码层闭合：preallocate:135 首查整个 parent 为空；entry:497 紧邻 leaf:498 再检查安全路径和完整空目录。旧 manifest、文件、隐藏项或其他子目录均在分配前拒绝。共享 registration_layout 未增加全局空目录条件。

### Suggestions
无。

### What's Done Well
两处检查只影响首次 stage-code；合同明确 bootstrap 输入与源留在 parent 外。两 hunk 完整逆变换恢复冻结 v3 原字节，40 个其他函数 AST 完全一致。

### Verification Story
- Tests reviewed: 4 条静态正/反例；全部 NOT_RUN，无目录或候选执行。
- Build verified: 否。仅 Python AST 解析与源码/字节核对。
- Security checked: 原 safe/reparse、REF、scope、raw capture 与 authority 条件保持。
- 12 个包成员、9 个原输入及 manifest 自身：22 个唯一 refs 无 SHA/bytes 漂移，原 input before/after 逐字节相等。
- A01–A07、实际 catalog/scope/review/capture/prepared、I17、完整18、callbacks 与 SQL24 仍 OPEN；正式验收增量0。

本轮 F08 复核新增失败0。先前临时定位的 516943 和 04c0fb 各保存一次原命令与工具响应、outer/native2/2，不重跑或重置。旧审查和 canonical 未改。

