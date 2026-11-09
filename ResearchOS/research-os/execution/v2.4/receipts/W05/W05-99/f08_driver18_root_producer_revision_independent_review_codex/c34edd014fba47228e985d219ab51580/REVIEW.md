## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** v2 加入了预分配保护、严格资源 REF 和外部原始 capture 闭合，但新的通用目录规则与冻结 binder/gate 不兼容。仍有 1 项 Critical 和 2 项 Important，实际 A01–A07 全部 OPEN。

### Critical Issues

- [driver18_root_producer.v2.proposed.py:74](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_revision_preparation_codex/dcfcd2f9a20e4962af5fa8278efa1ab0/driver18_root_producer.v2.proposed.py:74) **R01-REV**：所有 metadata output 必须为 `executor/<UUID>`，而冻结 gate 要求 registration namespace 的自身名称含完整 run UUID，冻结 binder 又要求 draft 是其严格子目录。这些条件没有共同合法 draft 输出。namespace 等于 output 时，源码先写四份 canonical copies，再由 binder 拒绝。stage-code 的另一个 fresh sibling output 也无法同时满足 gate 对 register/wrapper code 的同 namespace 边界。
  最小修复：stage-code/draft 使用当前 Root registration namespace 下相互独立的 fresh 子叶；stage 前的 namespace/run UUID 仅是 metadata 输出绑定。保留冻结消费者，并让 staged-code、draft、native-registration 保持彼此不重叠。内部 `run_registration` 分配前保护当前 dref/regref/index/MF 和全部 Reader refs，其当前 `[s]` 保护集缺少这些输入。补充真实合法路径正例和精确新字段契约。

### Important Issues

- [driver18_root_producer.v2.proposed.py:108](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_revision_preparation_codex/dcfcd2f9a20e4962af5fa8278efa1ab0/driver18_root_producer.v2.proposed.py:108) **R02-REV**：`pin(safe(row.path))` 保留调用方大小写；Windows Path equality 忽略大小写，因此 `resolve()==p` 不能证明字符串表示相同。正确 SHA/bytes 的大小写别名仍可生成 catalog，而后续 `runtime:174` 的 resolved pin 或冻结 module observation 字面字典比较会拒绝。最小修复：在 catalog 输出前使用与实际消费者一致的 code/tool/loaded-resource pin 表示，拒绝不兼容别名；不重写旧证据或放宽消费者。

- [driver18_root_producer.v2.proposed.py:426](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/f08_driver18_root_producer_revision_preparation_codex/dcfcd2f9a20e4962af5fa8278efa1ab0/driver18_root_producer.v2.proposed.py:426) **R03-REV**：直接 `seal_outer` / `seal_prepare` 经过共同 capture 闭包，却没有执行 `capture_action:410–412` 对 initial raw cmd/cwd 的真实 launcher 字节检查。冻结 outer gate 只验证非空 cmd 等于从同一 raw input 复制的 `tool_command`。最小修复：把现有 exact literal cmd/cwd 谓词放入 `original_capture_closure`，使三个入口都在成功写入前验证真实 dispatch。独立配对复核与原事件 MF 仍必须真实提供。

### Suggestions

无额外建议；本轮只要求上述具体修正。

### What's Done Well

- 已验证 grant 和真实 prepared proof 后才创建 preflight/auth，并同时检查两个新目录；unknown action 在通用目录分配前拒绝。
- 原 capture bundle/MF、原 raw/action refs、独立非作者 pair review 和 nullable native 字段现已强制保留。
- 17 个逆 hunk 唯一恢复原源码；24 个原函数 AST 保持一致。冻结 consumer、CAS/origin prefix、partial17、I16/I18 和 I17 OPEN 边界保留。

### Verification Story

- Tests reviewed: 先审 13 个 author future controls，均为 NOT_RUN 描述。独立提出 8 个具体 NOT_RUN 正反条件；未运行候选或 filesystem alias fixture。
- Build verified: **no**。仅 Python AST parse / 纯 IO；没有 import/execute producer、binder、gate、helper、Go、SQL、Job、CAS 或网络。
- Security checked: 静态 namespace、原事件/dispatch、REF、review、grant、lease、CAS 边界。真实当前 Root tuple/catalog/reviews/prepared proof 尚缺。
- 17 个完整 MF 成员、13 个旧输入、完整 MF 和一个冻结 utility 共 32 文件 SHA/bytes 实际无漂移；旧 review 的 2 个路径字典差异未重报为字节漂移。新增 failure origins 0。
- 实际 A01–A07、I17、full18、完整 callbacks、SQL24、source acceptance、正式用例接受均未因本审查升级。

STOPPED：仅本 UUID 的 metadata receipt 写入；所有 Main/canonical、作者包和旧 sealed review 未改。

