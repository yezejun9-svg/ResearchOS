## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** v3 静态闭合旧 c34 的三个具体缺口，并且已有与冻结 binder/gate 兼容的 stage/draft/native 正向布局。完整复审仍发现 1 项 Important：首次 stage 不能保证所选 parent 是新目录，仍可修改旧封存树。

### Critical Issues

无。

### Important Issues

- [driver18_root_producer.v3.proposed.py:135](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_revision_preparation_codex/a40358cbf99d4ade84977634d74a7d21/driver18_root_producer.v3.proposed.py:135) **R01-V3-FRESH_PARENT**：`registration_layout:88–95` 只要求 UUID-named parent 已存在；stage preallocation 只要求三个计划子目录不存在。一个含旧 manifest/成果的 namespace 也满足这些条件。若 stage input、当前 producer 和 GATE/BINDER 位于外部，旧 parent 不会自动进入 REF 保护集，`metadata=False` 后会向旧树创建 stage child。
  最小修复：在首次 stage-code 的 preallocation 分支、任何 mkdir/request/source 写入之前要求 parent 为空；bootstrap 输入和源放在 parent 外。不要对后续 registration_layout 统一要求为空，后续 stage/draft/native 合法内容已存在。保留三 child fresh/casefold/reparse、所有 REF parent 保护与 no-retry。同步明确 required-input-contract 的初始输入位置。

### Suggestions

无额外要求。

### What's Done Well

- 旧 **R01-REV**：新 schema-bound producer_layout 明确 stage/draft/native 为同 namespace 的严格直接子目录；draft 在创建叶目录和 canonical copies 前核全部真实 scope/stage/controller review；native 分配保护完整当前 dref/regref/sref/index/MF/Reader/code refs。冻结消费者保持原边界。
- 旧 **R02-REV**：resource REF 对照 resolve 后的实际字符串及完整 pin，不再把 Windows Path case-insensitive equality 当作字面路径证明。
- 旧 **R03-REV**：真实 initial raw cmd/cwd 与 terminal input/session 现在位于共同 closure，capture_action、seal_outer、seal_prepare 均调用。真实原事件、capture MF、独立 pairing review 和 grant 仍是硬门。
- 10 个逆 hunk 唯一恢复 v2 原字节；32 个既有函数 AST 保持一致。

### Verification Story

- Tests reviewed: 先审 author 18 个 future controls 与 positive-path example，均为 NOT_RUN。独立拆解九个 source-flow 阶段，并验证直接严格 sibling 路径代数；未创建示例目录、输入、授权或结果。
- Build verified: **no**。只读源码、Python AST 与 metadata IO；没有 import/execute candidate、native、Job、Go、SQL、network、model、CAS 或 Git probe。
- Security checked: 静态 namespace、old input、resource literal、original event/raw command、review/grant/lease/CAS 边界。实际 Root tuple/catalog/reviews/capture/prepare proof 仍 OPEN。
- 21 个 author members、9 个既有 inputs、complete MF 共 31 frozen refs SHA/bytes 无漂移；旧 c34 REQUEST 与来源原样保留。新增失败 origins 0。
- 本轮不能授 Root 运行资格、source acceptance、I17/full18/callback/SQL24 或正式用例接受。

STOPPED：只写本 UUID 的 review metadata；作者、Main/canonical 与旧 sealed 文件未写入。

