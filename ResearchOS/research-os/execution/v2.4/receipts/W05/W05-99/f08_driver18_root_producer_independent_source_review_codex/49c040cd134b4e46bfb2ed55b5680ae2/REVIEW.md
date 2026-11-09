## Review Summary

**Verdict: REQUEST CHANGES**

候选已实现当前 draft/lease、双层 Job、两次 all4 CAS 和完整 prepare gate 的具体流程。以下 3 个 Important 问题必须在 Root 实际运行前修正；源准备和实际 A01–A07 资格仍分开。

### Critical Issues

- 本次未列 Critical。

### Important Issues

- **R01 — 原证据树在拒绝前被追加。** [producer:332](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:332) 先创建 leaf 和 producer-request；[leaf:49](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:49) 只限制在通用 RECEIPTS 内。传入 existing prepare/launcher root 的新子目录会先追加文件，然后完整 manifest 验证才拒绝。[grant:255](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:255) 的 preflight 也没有排除原 phase trees。必须在任何 mkdir/write 之前完成 action-specific scope/Root ownership 和不重叠检查；同时保护 work 与四个 phase 输出树，不能靠拒绝后的 manifest 错误补救。

- **R02 — 接受的路径表示与固定 consumer 不兼容。** [resource_catalog:108](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:108) / :115 使用 same_ref，然后原样输出；但 frozen utility:164、controller:85/107 要逐字 pin/dict equality。forward-slash REF 或 equivalent offline REF 会先通过 producer，随后 runtime/prepare 失败。[prepare_scope:129](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:129) 原样保留 forward-slash work_root，也冲突于 prepared.json 的 Windows str(Path) 与 authority:450/controller:138。应在 scope SHA/独审前统一新输出的 Windows 参照表示或提前拒绝；python 要等于实际选定 pin，offline ref 要逐字等于 catalog row；不得改冻结 consumer 或原输入。

- **R03 — 原工具事件来源尚未硬校验。** [capture_action:289](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:289) 只要求非空 locator、复制裸 input/response refs；[seal_outer:304](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:304) 接受裸 action refs，既未消费 Root capture MF/实际配对复核，也未验证 grant 内容。字段/session 一致不能证明 terminal response 来自该 write_stdin 事件。应先验证 current grant，并要求 Root 原 capture manifest/配对复核与 exact raw/event/identity 绑定；缺该实际来源时 FATAL_OPEN。不能用 actor 字符串或 candidate 自造签名补证。

### Suggestions

- [reviewed:148](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_preparation_codex/fe7a07dcb98a4f2aacb2f73d4ff60780/driver18_root_producer.proposed.py:148) 修复后可把长行拆成对应合同的小检查，降低后续审查遗漏风险；无需新框架或改 consumer。

### What's Done Well

- 注册复核增加 exact producer_ref，并绑定当前 scope/draft/MF、四份 originals/desired 与 phase lease，覆盖两个 bootstrap 后的实际 engine。
- CAS 顺序保留两次 immediate all4 和 final source guard 后的 all4；旧失败全前缀及无关 canonical 字段通过 inverse 保护。
- Inner 与 wrapper 使用两个实际 owned Job 调用，原 raw 和 nullable native 先保存再判定成功；完整 prepare 与 18 NOT_STARTED roster 委托固定 gate 核验。

### Verification Story

- 先读 11 条 future-negative-controls；它们全是 NOT_RUN 描述，尚非可运行或通过的 fixture。本回执新增 10 个具体逻辑反例，全部 NOT_RUN。
- 12 manifest 成员、32 冻结输入、MF 与外部 postseal annex 精确 SHA/bytes 一致。原 MF 只包含 12 成员；annex 没有伪装成原 MF 成员。
- Producer 34 函数 / 357 行、authority/binder/controller 全文及 helper 关键函数已静审。b80509 的返回中段被工具截断，a11cd7 明确补读缺失正文；原结果保持不改。
- 仅 Python AST / 公共只读 IO；无候选 import/运行、Job/Go/SQL/driver/HTTP/Node/SDK/model、live canonical 读取或写入。没有构建、Go AST、真实 prepare 或测试通过的声明。
- 冻结 controller/launcher 与 I16/I18 源字节保持；原 32/600/750/3300/3600/cleanup5 和 partial17/30 calls 不改，I17 OPEN；CLI331 资格未被当作 F08 权威。
- 实际 tuple/catalog/bound reviews/grant/proof 仍 OPEN，source_acceptance=false，formal_increment=0。新失败 origins 0；作者 outer0/nativeNULL 原事实保留。

具体字段、行号、最小修复和反例见 review.json、coverage.json、counterexamples.NOT_RUN.json。
