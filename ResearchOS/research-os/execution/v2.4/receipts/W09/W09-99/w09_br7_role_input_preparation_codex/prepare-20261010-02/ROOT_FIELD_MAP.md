# Root role input builder

这是元数据 builder Source，需 Root 审源后另行运行。源码 import 无执行入口动作；本轮只运行新增纯 schema/补充引用控制。它不调用 Main/BR7 stage，不创建 grant，不验证或改写 Canon，不发布固定 execution-roles.json，也不声明任何角色已被 Main 接受。

## 输入

将 builder-request.template.json 的 null 填为真实值。请求恰有八项字段：schema、actor_id、preparation_id、proposal_ref、context_seed_ref、scope_observation_audit_ref、assembly_owner_observation_audit_ref、mode01_observation_audit_ref。schema 固定 researchos.w09-role-input-builder-request.v1，actor_id 固定 codex:/root；preparation_id 为新的32位小写hex。五项动态 ref 都是 path/sha256/bytes 三键。

| 字段 | 实际文件及约束 |
|---|---|
| proposal_ref | BR7 propose 输出的 proposal result.json；generation=bridge-20261010-07，RUN_CURRENT_CM40，source_ref 精确绑定已封 BR7。 |
| context_seed_ref | proposal.context_seed_ref 指向的同一份实际 context-seed.json；不是 seed stage 外层 result.json。run_id 从该文件读取，executor 为 Root，六路完整且 Main profile pin 为当前1e048...。 |
| scope_observation_audit_ref | Root 已真实读取/观察 proposal.documents.consumers.scope_ref 所指 Scope，原 call/result 明文包含 Scope 自身 SHA。 |
| assembly_owner_observation_audit_ref | Root 已真实读取/观察 proposal.documents.assembly.owner_ref 所指 owner，原 call/result 明文包含 owner 自身 SHA。 |
| mode01_observation_audit_ref | Root 已真实读取/观察固定 Mode01 c7ca8206...，原 call/result 明文包含 Mode01 自身 SHA。 |

三个 Root audit 可以来自同一真实 call/result，只要原件确实包含所选三个 hash；各自 ref 仍必须是实际存在的审计文档。不要仅回显已知 hash 冒充读取。未就绪时保留请求模板的 null；builder 运行时会在写输出之前拒绝 null，不据此宣布整个 Goal 阻塞。

audit 包装必须是已使用的 researchos.w09-native-producer.actual-audit.v1 九字段结构，或带 role 的 researchos.w09.actual-role-audit.v1 十字段结构。字段集合为 schema/actor_id/Root_thread_id/source_audit_path/source_line_offsets/original_line_sha256/source_prefix_size_observed/original_capture_ref/binding_sha256（角色结构另有 role）。Root 包装 actor_id 必须为 codex:/root。允许来源日志同一绝对 Windows 路径的正/反斜杠拼写，输出适配器统一使用 Main 要求的固定正斜杠字符串。

计数勘误：前一份已封 FIELD_GUIDE.md 与任务里的“11字段”文字应为10字段；其实际模板键集合一直正确。本builder遵循Main真正的10键 exact tuple，不增加第11键。已发生纯控制记录中保留含 eleven 的原始测试标签，以保留原输出摘要；实际断言集合为上述10键，正确计数以本合同为准。

audit 包装本身必须位于 repo；original_capture_ref 仅这一字段可引用 repo 外的真实本地绝对 copied3LF 文件（例如 cap.RawCopied3LF）。它必须是已校验 pin 的普通本地文件；UNC、junction、symlink、reparse、路径穿越和错误大小/hash 被拒绝。外部 copied3LF 会被 SourceReadGuard 持有，再原字节复制到 RootOriginPrefix。不会把外部路径交给 Main，也不会持有整份持续追加的 Root log。

## 固定复用与输出字段

source-inputs.json 的 SHA 固定在 builder 中。它固定复用已封6257...模板、BR7 Source/HDF、当前 Main、SourceGuard、Mode01和两个真实 peer capture。SourceAuthor 使用真实 /root/full_w09_source_review 的交付并绑定 BR7 HDF1da...；Verifier 使用真实 /root/backup_regression_resources 的交付并绑定原消息实际包含的 Mode01自身 SHA。不会修改原消息 actor，也不会使用包装中的 canonical 标签替代它。

运行时从 proposal 读取 consumers Scope/owner 与 assembly Scope/owner；不写这些文件，不检查或伪造其 Canon 注册状态。后续 BR7 registered/Main 仍负责真实注册、lease 和正式接受门。builder 拒绝错误 source_actor、source pin、scope 类型、缺路由与不一致 owner链，但这些元数据检查不签发执行权。

通过全部原件范围验证后，输出到唯一目录：

- `execution/v2.4/receipts/W09/W09-99/w09_br7_role_inputs_root/{preparation_id}/`
- `execution/v2.4/root_original_events/W09/W09-99/roles-{preparation_id}/`

两者任一已存在就拒绝；不覆盖、不清理既有目录。失败保留输出与关闭记录，Root 留存真实工具结果后决定下一次独立准备，不自动重试。

五份 raw 三行文件逐字复制 header/call/result；SourceAuthor/Verifier 是真实 metadata+agent_message，Root三角色是真实工具pair。所有原件再次对 Root 固定日志的真实 offsets 逐行比较，保留原 SHA、offsets、prefix。只生成 Main 精确10字段 role audit 适配器；不制造新事件，不为 builder 自身生成角色审计或 grant。

| 输出 | 后续用途 |
|---|---|
| role-registry-input.json | BR7 roles 请求的 role_registry_input_ref，四字段 run_id/roles/provenance/route_execution_refs。 |
| 五份 *.actual-role-audit.json | Main 所需10字段适配器；实际 actor 采用 backend /root 值或 codex:/root。 |
| role-protection-refs.json | 将其中 role_protection_refs 数组直接合并到未来 roles 请求，再建立请求 hash/grant；只传此文件的 ref 不会递归持有里面的 copied3LF。 |
| context-role-policy.template.json | 后续合并片段。固定 registry 路径已填，sha256/bytes 继续 null，等实际 roles payload 发布并登记后填。 |
| result.json | 上述实际产物 pins；registered_ref3 与 registry_ref2 保持 null，明确尚未发布或登记。 |
| source-guard.closed.json | 实际运行的 guard observation 与 cleanup_errors；必须 closed/0/无错误后才能报告 builder 成功。 |

六 route_execution_refs 全部来自 proposal 新 consumers Scope/owner，采用 Main 的 repo POSIX 三键 refs。proof.raw_ref 仅 path/sha256/locator 三键，actual_audit_ref 三键；原件路径位于固定 RootOriginPrefix。Scope/owner 内部已有绝对 Windows refs 不重写。

Root 以后将 roles 产生的 payload 精确发布到 `execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json`，再按既有 BR7 publish-registration 合同登记。context.role_policy.registry_ref 的 path/sha256/bytes 要逐字等于真实 CP slot；vector.input_files 使用同一 registry 的 path/sha256 两键项，保留原有列表。该步骤与新的 Main角色/route校验均不由本builder执行。

## argv

root-calling-contract.source.json 给出精确 argv_template。仅 --request 后的真实请求绝对路径、--sha256后的实际摘要、--bytes后的实际十进制字节数待 Root 填写。使用锁定 Python 的 -I -S -B -X utf8，显式 cwd 为 D:/作品集/ResearchOS/research-os。没有 execute/activate 或 Root stage 参数。
