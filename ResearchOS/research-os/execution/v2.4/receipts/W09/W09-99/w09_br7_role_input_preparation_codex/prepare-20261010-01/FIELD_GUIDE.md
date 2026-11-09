# BR7 五角色输入合同

本包对当前 Main `formal_profile_w09.py`（SHA `1e04865beef37fdbffa06d649d072721d7b6eb0ef5e525d87bb867da414e4087`）与 BR7 `w09_root_bridge.source.py`（SHA `16b9f425efcbe2f7f9155cd7be54c3fe4faf10e327a2800ce6edb89d13fa1668`）做静态合同检查。没有调用 Main 角色门、`_native` 或 BR7 stage。模板中的 null 必须等待对应实际产物或事件产生后填入；模板本身不是合格 registry、审计记录或执行授权。

## 最小输入与五类 proof

`role-registry-input.template.json` 是 BR7 `role_registry_input_ref` 指向文档的最小结构：`run_id`、`roles`、`provenance`、`route_execution_refs`。roles 阶段生成的 registry 才增加 `schema=researchos.w09.execution-role-registry.v1` 与 `writer_actor=codex:/root`。不要把本指南字段加入生成的 registry；Main 对 registry、proof、role_policy 均使用 exact-field 校验。

| role | actor_id | origin_kind | raw_ref.locator |
|---|---|---|---|
| SOURCE_AUTHOR | `/root/full_w09_source_review` | ROOT_SCOPE_REGISTRATION | `{"json_pointer":"/source_actor"}` |
| EXECUTOR | `codex:/root` | ACTUAL_MODE_DECISION | `{"json_pointer":"/producer_id"}` |
| EVIDENCE_ASSEMBLER | `codex:/root` | ROOT_OWNER_REGISTRATION | `{"json_pointer":"/selected_worker_id"}` |
| VERIFIER | `/root/backup_regression_resources` | ACTUAL_MODE_DECISION | `{"json_pointer":"/reviewer_id"}` |
| ROOT_OBSERVER | `codex:/root` | ROOT_SCOPE_REGISTRATION | `{"json_pointer":"/issued_by"}` |

每个 proof 恰有 `role, actor_id, origin_kind, raw_ref, actual_audit_ref`。raw_ref 恰有 `path, sha256, locator`，不加 bytes；actual_audit_ref 恰有 `path, sha256, bytes`。raw_ref 解引用结果必须逐字相等于 actor_id。

`roles.source_authors` 是数组，至少包含 BR7 backend `/root/full_w09_source_review`；BR7 拒绝把 canonical `codex:/root/full_w09_source_review` 放进去代替它。已有 Root 收到的真实 agent_message.author 已核对为上述两个 backend 值。现有 capture 包装中的 `codex:` actor 标签不能代替原消息 actor。最小模板只登记当前 BR7 作者；若实际登记更多作者，每位都要额外 SOURCE_AUTHOR proof。Verifier 不得与任何作者、executor、assembler 或 root_observer 忽略大小写后相同。

SOURCE_AUTHOR 与 ROOT_OBSERVER 的 raw origin 使用新 BR7 consumers Scope（也可用满足同一合同的真实 Root Scope），要求 issued_by=`codex:/root`，schema 匹配 `researchos\.w09[-.][a-z0-9.-]*scope\.v1`。BR7 新 Scope 的 source_actor 必须为当前 backend。EVIDENCE_ASSEMBLER 使用新 assembly owner：owner_id 为 Root 或 executor、selected_worker_id 为 assembler、lease_status=ACTIVE；其真实 scope_ref 指向 issued_by=Root 且 slice_id=W09_FULL_FORMAL_ASSEMBLY 的 Scope。context.created_at 不晚于 owner.lease_expires_at。

EXECUTOR 与 VERIFIER 可共同引用已发布 Mode01；schema 必须 `researchos.w09-mode-decision.v2`、decision=QUALIFIED、reviewer_role=INDEPENDENT_NON_AUTHOR。Mode01 的 producer/reviewer 分别是 Root/Backup。六个实际 Mode 的完整 pins 位于 `known-role-evidence.json`，没有重新签发 Mode。

## actual-role-audit 的精确结构与原件

`actual-role-audits.template.json` 是以五个 role 为键的准备容器；Root 应将每个填完的子对象分别保存为实际审计文档，不能把这个外层容器直接传给 Main。每个实际文档恰有：

`schema, actor_id, role, Root_thread_id, source_audit_path, source_line_offsets, original_line_sha256, source_prefix_size_observed, original_capture_ref, binding_sha256`。

固定值：schema=`researchos.w09.actual-role-audit.v1`；Root_thread_id=`01a11007-5233-7ca1-b71f-9e9e5ce84c98`；source_audit_path 必须逐字等于 `C:/Users/yqyyds/.codex/sessions/2026/10/06/rollout-2026-10-06T15-04-37-01a11007-5233-7ca1-b71f-9e9e5ce84c98.jsonl`，使用该正斜杠字符串。现有 `researchos.w09-native-producer.actual-audit.v1` capture 包装不能直接作为 Main 的 actual_audit_ref；应保留它，另写正确 schema 的角色适配文档，真实 offsets/digests 不变。

original_capture_ref 恰有 path/sha256/bytes，其内容必须是从 Root 原始日志逐字复制的三条 LF 结尾记录：session_meta header、原始 call/metadata、原始 result/message。不可解析后重序列化、改身份或补 ordinal。header.ordinal=0，payload.id 为上述 Root thread；call/result.ordinal 为正整数且后者更大。

Root actor 的 call/result 必须是真实匹配 call_id 的工具调用与结果。peer actor 的前一条必须 inter_agent_communication_metadata，下一条必须 agent_message；两条同 timestamp，ordinal 恰差1；author 精确匹配 proof.actor_id，recipient=/root，client_authored=false，content 为唯一 input_text。原件记录没有满足这些字段时不能伪造。

source_line_offsets 是严格递增的三个非负整数；original_line_sha256 是三个实际行 SHA；source_prefix_size_observed 是实际观察到的整数前缀界限，覆盖三行全部字节。Main 将 seek 原始 Root 日志并比较每行字节和摘要；复制件不是原始日志校验的替代品。本次只读核对了两个已经发生的 peer 交付及其原始范围。

## origin_allowed_binding：这是选择规则，不是新增 JSON 字段

Main 允许选择的 binding_sha256 集合为：proof.raw_ref.sha256；origin 中已有的 source_hdf_ref、source_mf_ref、source_review_ref、scope_ref、independent_review_ref 的 sha256；以及 origin.report_sha256。所选值须为 SHA256，且逐字出现在原始 call 与 result 两行拼接文本中。

| proof | 当前可用或未来应观察的 binding |
|---|---|
| SOURCE_AUTHOR | 已发生 BR7 作者交付中的 HDF `1da577805839fb3f96f20bb5282020d7f909e466278aa1df3713f758d977d06c`；新 Scope.source_hdf_ref 必须指向这一真实 HDF。不能声称作者交付观察了未来 Scope。 |
| VERIFIER | 已发生六 Mode 交付中的 Mode01 自身 SHA `c7ca8206145c1c6bd0f85bcfbd878b398e5fdb4c45a9baa9817d0c8a046d614e`，已从原消息核对；原包装选用的另一个 HDF SHA 不自动属于 Mode origin 的允许集合。 |
| EXECUTOR | 未来 Root 真实只读观察 Mode01 的原工具 pair，绑定 Mode01 自身 SHA；actor 必须 Root。 |
| EVIDENCE_ASSEMBLER | 未来 Root 真实只读观察新 assembly owner 或它引用的 assembly Scope 的 SHA。 |
| ROOT_OBSERVER | 未来 Root 真实只读观察新 consumers Scope 的 SHA。 |

同一个真实 Root pair 可以承载多项它确实观察并输出的 artifact hash，但每个 proof 仍有自己的 role、origin 和 binding。读取或显示这些公共证据只形成观察记录，不增加执行权限。本包没有填写任何未来 Root pair 的 offsets、digests、prefix 或原件 pin。

## 路径与保护边界

Main proof.raw_ref、proof.actual_audit_ref、六 route 的 scope_ref/owner_ref，全部使用 repo 相对 POSIX 路径并位于 `execution/v2.4/receipts/W09/`。不要传绝对 Windows 路径或反斜杠。owner 文档内部的 scope_ref.path 可以是实际绝对 Windows 路径或 repo 相对路径，但解析后的文件、SHA、bytes 必须与注册的 Scope 相同。

角色 audit 文档仍在上述 receipts/W09 前缀。它里面的 original_capture_ref.path 则必须是 repo 相对 POSIX，且在固定 `execution/v2.4/root_original_events/W09/W09-99/` 前缀下。现有两个真实 copied3LF 目前存于 S receipts 目录；Root 必须按原字节复制到这个固定 origin 前缀，再填目标路径。既有 SHA/bytes 不变；本包没有发布这个副本。

若外部 capture 工具返回 cap.RawCopied3LF，先保留并校验该真实传输原件。外部路径不能直接作为 Main original_capture_ref，也不能放入 BR7 一般请求 ref（physical 限制 repo/固定 plan）。Root 发布的 repo 内 copied3LF、角色 audit、raw origin、assembly Scope 应在角色 stage 执行期间受 SourceReadGuard 保护。BR7 对 role_registry_input_ref 只扫描文档内显式 refs，不递归展开 actual_audit_ref 指向文件中的 original_capture_ref；因此单有 audit ref 不足以预先持有 copied3LF。

`role-stage-protection.template.json` 提供可合并进未来 Root roles request 的 `role_protection_refs`：五个 copied3LF pin 加一个 assembly Scope pin。这是现有 request_dependency_refs/references 会读取的附加公共资源列表，不是新权限字段，不写入最终 registry。Root 可去重相同复制件。必须在请求 hash/grant 建立之前填好并纳入请求，不能签发后追加。不要把 live Root audit log 作为整文件静态 pin 或持有禁止追加的句柄；Main 按已记录有限 ranges 校验原始日志，snapshot 保留这些 ranges。

## 六 route、发布与 context

用户所说的六 route_scope_refs 在 Main 中正式字段名是 `route_execution_refs`；每行恰有 command_key/check_id/case_id/scope_ref/owner_ref，后两项均是三键 public provenance pin。六组合为：test.retrieval/W09-G01/空、test.retrieval/W09-G02/空、test.research.fixture/空/C19、test.retrieval/空/C19、test.retrieval/空/A06、test.security/空/A06。

RUN_CURRENT_CM40 时六行可指向同一份新 consumers Scope/owner。scope.issued_by=Root；owner.scope_ref 必须精确绑定该 Scope，owner_id=Root 或 executor，selected_worker_id=executor，lease_status=ACTIVE；每个 command_key 必须同时在 owner.routes 与 scope.routes 中。实际 dispatcher receipt.ended_at 必须不晚于 owner.lease_expires_at。Mode.producer_id 必须等于 roles.executor。保留旧 Native 证据和它们原始 Scope；新 consumer 的回执时段不能凭旧 Native Scope 的历史 lease 获得覆盖。assembly owner 不能拿来替代 consumers owner。

BR7 roles 只运行 Main _role_audit 并检查角色来源作者/Verifier与六行数量，尚不等价于完整 _role_registry 或 _route_execution_actor 通过。它返回 execution-roles.proposed.json 的精确 payload。Root 另行发布该 payload 原字节到固定 `execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json`；publish-registration 验证相同字节、持久依赖 snapshot 和 current4 CAS，再按 expected_previous_registry_ref 的真实旧值登记 CP.work_in_progress.w09_execution_role_registry_ref。该 slot 是 path/sha256/bytes 三键且 path 必须逐字为固定 POSIX 路径；不是外部 Scope 授权替代品。

`context-role-policy.template.json` 是待合并的片段，不是完整 context/vector。role_policy 恰有 schema=`researchos.w09.execution-role-policy.v1` 和 registry_ref；registry_ref 三键必须逐字等于已登记 CP slot。version_vector.input_files 添加同一 registry 的两键 path/sha256 项（不能携带 bytes），并保留已有输入。registry.run_id 必须等于 context.run_id；roles.executor 必须等于 context.executor_id。重新生成所需真实 context/request/snapshot，不覆盖旧 seed 或签发旧请求。BR7 seed 不允许把可变 CP/OW 放入 vector.input_files。

Main verify_owner 在 _role_registry 后检查 registry 位于 vector 的实际 pin 集合；_vector 本身允许其位于任一文件组，但本合同按角色输入语义放 input_files。roles 阶段成功、文件发布成功、CP slot 登记成功、完整 Main 验证是不同的事实，应按实际记录分别报告。本次只完成模板准备；动态输入尚未就绪不表示整个 Goal 阻塞。
