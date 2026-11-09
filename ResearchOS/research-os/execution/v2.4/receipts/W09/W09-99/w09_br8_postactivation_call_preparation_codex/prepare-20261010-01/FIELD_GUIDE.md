# BR8 activate 后的 Root 请求配方

本包只给出 metadata 配方。未调用任何 Root stage、Main 函数、dispatcher、Native、Go、SQL、TP 或模型；未写 registry / Main / Canon。模板中所有未发生的输出、授权、时间、动态 current4、实际身份观测均为 null。已填的 Source pin、固定协议字符串和 A06-02 引用来自现存文件，不代表本轮执行。

有一个不能靠补字段解决的后续缺口：formal review v3 要求 input bundle 在自身 resource_refs 中携带自己的最终 SHA/bytes，构成自引用。见 OPEN_BOUNDARIES.json。consume 到 assemble 的配方可以独立准备；不要据此宣布现存 v3 已能接收可构造的完整实际审查 bundle。

## 共用请求与授权顺序

common-request.template.json 是实际 researchos.w09-root-bridge-request.v1 的非可执行模板。将每个 extras 文件的键平铺合并进共用请求；不要把 extras 当成名为 extras 的嵌套字段。

Root 必须使用当前阶段的真实 actor_id=codex:/root 和固定 Root_thread_id=01a11007-5233-7ca1-b71f-9e9e5ce84c98，并提供自己实际签发的有限时间、输出目录、grant 与原始 audit。这些不是本作者可以代填的事实。stage 值分别为 consume、roles、publish-registration、seed、assemble。

四个 Source 引用必须逐字段等于已审查文档中的原始对象，包括路径拼写：bridge_source_ref、consumer_launcher_ref、source_hdf_ref、source_mf_ref。模板保留其反斜杠原始路径。source_review_ref 指向现存 ACCEPTED_SOURCE_ONLY 文档；source_review_audit 仍需实际 Root 收到该独立 Source FINAL 的证据，不能拿 Source 作者自己的 audit 代替。

current4 依次为 checkpoint / path_ownership / step_state / commands 的绝对路径精确三字段 pin。每个实际 stage 前重新取值。activate 和 publish-registration 变更 CP/OW 后，旧 current4 不能继续作为当前授权。历史 proposal 保留原 current4 及四份原始档案，不能重写成新值；BR8 允许使用有档案证明的历史 CP/OW，但 SS/CM 仍须与新请求完全一致，CM 必须是固定 CM40。

每个请求先补齐所有字段，包括 role_protection_refs，然后按 BR8 encoded 的 UTF-8、ensure_ascii=False、indent=2、末尾 LF 规则计算去掉顶层 grant_ref / grant_audit 后的 request_body_sha256。Root 的真实 grant 必须绑定它，再补入 grant_ref / grant_audit。获得 grant 后再添加或更改 extras 会破坏绑定。

共用资源字段 bridge_temp_parent、resource_parent_ref、resource_audit_ref、resource_owner_sha256 必须严格取 BR8 源码固定 RESOURCE_* 值。bridge_temp_parent 及进程 TEMP/TMP 都要求 C:\Users\yqyyds\.researchos\w09-native-v5。不要把其 C 路径资源 marker 伪装成普通 repository ref；BR8 为这个固定 marker 保留专用处理。不要持有完整活动 Root 日志，只使用已绑定的有限 audit ranges。后续每个输出目录须为 W09/W09-99 下全新绝对路径。

## 1. consume

extras/consume.template.json 的字段：
- proposal_ref：原 BR8 propose 的 result.json 三字段 pin；这是完整 proposal，不是工具 stdout 包装对象。
- context_seed_ref：该 proposal.context_seed_ref 的原始三字段引用。
- c19_policy：RUN_CURRENT_CM40。
- isolated_environment：TEMP、TMP、USERPROFILE、LOCALAPPDATA、APPDATA 五个实际目录；前两个必须等于固定 PUBLIC_TEMP，其余是现存独立环境目录。

BR8 先重验原 Scope/Owner/worker 注册及有限 lease，再按已有 context.registered_commands 的顺序执行六条已登记 consumer route。四份 NF6 Native 报告和六份 Mode 沿用；consumer 验证这些报告，不重新生产 Native。六条实际 route 必须为 G01、G02、C19 两条、A06 两条，不得把 source 中的四条 NEW 列表用于 RUN_CURRENT_CM40。

工具 stdout 的 result_ref 指向 consumers result.json；它具有 schema=researchos.w09-bridge-consumers.v1、registered_commands 和 processes。该文件的三字段 pin 才是后面 assemble 与 Backup review 的 consumer_result_ref。每条新的 receipt_ref 是 repository-relative POSIX 两字段引用，由实际 dispatcher stdout 解出的 receipt.json 生成；不取 0.stdout.raw、0.process.json、0.complete.json 或任意汇总副本代替。首次非零/超时/Job 未闭合即停止，保留实测退出与失败文件。

## 2. role builder 与 roles

role-builder-request.template.json 恰好八个字段，schema=researchos.w09-role-input-builder-request.v1。Root 的新 preparation_id 为真实未用过的 32 位小写 hex。proposal_ref 与 context_seed_ref 必须是上述原始组合；builder 明确验证 proposal.context_seed_ref==请求 context_seed_ref，因此不能提前换成登记 registry 后的新 seed。

另三个 audit 输入分别证明实际 Root 观察：
- scope_observation_audit_ref：consumers Scope，绑定其实际 scope pin。
- assembly_owner_observation_audit_ref：assembly Owner，绑定其实际 owner pin。
- mode01_observation_audit_ref：既有 Mode01 的实际 Root 观察，绑定 Mode01 pin；不要求重跑 Native。

已有 Source 作者和 Verifier 两个真实 peer 证据由固定 builder inputs 引入。不要重写 actor/backend 身份，或把 Root 自己的普通文本冒充 peer FINAL。builder 写到新的 w09_br8_role_inputs_root/<preparation_id> 及 root_original_events/.../roles-<preparation_id>；它不发布固定 registry。

builder stdout.result_ref 指向 builder result.json：
- role_registry_input_ref：提供给 roles。
- role_protection_refs_ref：先读取这个文档，取其中 role_protection_refs 数组，原样平铺放进 roles 请求；不是只放该文件的 ref，也不是把整个包装对象当数组。
- context_policy_template_ref：后续重建新 seed 的 schema 模板。
- registered_ref3 和 registry_ref2 仍为 null；builder 不产生这两个事实。

extras/roles.template.json 除 proposal_ref、RUN_CURRENT_CM40 外，提供上述 role_registry_input_ref 与完整 role_protection_refs。后者覆盖五组原始三行副本、五份 actual-role-audit、原始 provenance 文件以及 consumers/assembly 的 Scope/Owner。它们必须在请求 grant hash 之前进入请求，确保普通递归 dependency scan 能 hold 到实际文件。actual-role-audit 本体精确十字段；不要沿用旧文案中的十一字段说法。

roles 验证原始 audits 和基本 route 数量，输出 publication proposal；它没有执行完整 _role_registry / _dispatches / _global，也没有签发正式接受。

## 3. Root 逐字节发布与 publish-registration

roles 工具 stdout.result_ref 指向 publication proposal result.json：
- publication.fixed_path 固定为 execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json。
- publication.payload_ref 指向同次 roles 输出目录里的 execution-roles.proposed.json。

Root 先审查提案，再把 payload_ref 指定文件的原始字节发布到 fixed_path。不能重新 json.dumps registry、重新排序、换编码或改换行。若目标已存在，必须核查是否等同及 Root 处理权限，不能默默覆盖。payload file 的路径不同于固定文件路径，虽然原始字节 SHA/bytes 应相等。

extras/publish-registration.template.json：
- publication_ref = roles 的整个 publication proposal result.json 三字段 pin，不是 payload_ref。
- expected_previous_registry_ref = 该调用前实际 checkpoint.work_in_progress.w09_execution_role_registry_ref；只有实际槽位不存在时才是 null。本模板的 null 不表示已经观察到不存在。

publish-registration 只核对固定文件字节已等于 payload，再由现有 TP CAS 登记 slot；它本身不复制 registry 文件。其 result.json 只有 checkpoint_ref、ownership_ref、transaction_journal。不要查找并不存在的 result.registered_ref3。

实际成功之后，从新 checkpoint_ref 对应文档读取 work_in_progress.w09_execution_role_registry_ref，核对实际固定文件，得到 registered_ref3。其 path 必须是上述固定 repository-relative POSIX 路径，且对象精确为 path / sha256 / bytes。registry_ref2 是从它只投影 path / sha256。这两个都是后续真实派生值，模板仍为 null。

## 4. 新建带 role policy 的 context input，再调用 seed

不要改原 seed、proposal、既有 builder result 或 policy template。Root 新建一个 context input：
1. 从原 seed 的内容复制；保留 run_id、acceptance_baseline_ref、NF6 Native refs、六个 Mode refs、environment、components、spec/lock/tool/input 版本事实。
2. registered_commands 使用同次 consume result 的六条实际完整行，保留其 Native/Mode 引用。
3. role_policy 精确为 schema=researchos.w09.execution-role-policy.v1 与 registry_ref=registered_ref3。
4. version_vector.input_files 中按固定 registry path 去重替换/追加 registry_ref2；不能把三字段对象塞入 _vector 的两字段列表。不能把 CP/OW 加进 context input_files。
5. global_evidence_refs 可清为空对象，由 assemble 从真实 facts 生成八份文档；不要先填未来 GLOBAL refs。

然后用新、独立真实授权的 seed stage，extras 仅 context_input_ref。seed 会生成新的 source coverage/source_files、created_at 并检验 vector。其 result.json.context_ref 是新 seed 三字段引用。该 seed 供 assemble 使用；原 proposal 和原 role-builder 绑定继续保持不变。registry.run_id 必须仍等于新 context.run_id。新 seed 和 context input 的文件路径/哈希/bytes 都只能在实际产生之后取得。

## 5. assemble 的完整 extras 与八份 GLOBAL 顺序

extras/assemble.template.json：
- proposal_ref：同一原 BR8 proposal。
- context_seed_ref：上一步新 seed，含已登记的 role_policy 与 registry 两字段 vector pin。
- consumer_result_ref：consume 的实际 result.json 三字段 pin。
- c19_policy：RUN_CURRENT_CM40。
- plan_ref：真实 frozen implementation execution.plan.json 三字段 pin。BR8 physical() 只对这一个固定外部 PLAN 文件开例外。
- code_revision：实际 Git HEAD 的完整 commit；dirty：实际 bool。不要用候选 Source 的作者声明代替。
- package_manifest_ref：新 context.version_vector.spec_files 中名为 PACKAGE_MANIFEST.json 的精确两字段 ref；Main 要求该对象本身属于 spec_files。
- refusal_evidence_refs：非空 path / sha256 / locator 数组，用于 A06-02。模板给出现存 NF6 A06-02 owned export 的 /actual 引用，已读取为 http_path_traversal_rejected=true、secret_marker_leaks=0；它是现存证据，不是新结果。仍须随当前请求保留 pin 校验。

BR8 实际调用顺序是：registered → native_inputs/_vector及六个_native → 替换为实际consumer行 → _role_registry → _dispatches → 写 C19 四文件 → 写 A06 四文件 → _global → snapshot/recheck_inputs → 写不可变 context.json。

四种文件的写入及 GLOBAL ref map 插入顺序严格为 run_receipt、version_manifest、command_receipt、assertion_results。Main _global 按 ref map.values() 取文档，再按同序解包；因此不要对这些 map 的键排序。总计八个 GLOBAL artifact，不是八个独立 Root stage。_dispatches 当前 Main 先产生六 route 的 outputs/facts，不依赖尚未生成的 GLOBAL。禁止先伪造八份 PASS 文件来绕过前置门。

C19/A06 每个 assertion 都必须从两条实际 route 找到相同 evidence；raw_evidence_refs 由既有 owned_export_ref 转成两字段 pin 加 /actual locator。A06-02 另外需要上述真实 refusal refs。run 起点取 Native start，终点取 dispatcher end；version_manifest 使用同一最终 context vector，command_receipt 使用 _dispatches 的实际输出结构。

assemble stdout.result_ref 指向 assembled-context result.json；其中 context_ref 才是最后不可变 context.json 的 repository-relative POSIX 两字段引用。不能拿 result_ref 当 formal context_ref，也不能把 seed 的三字段 context_ref 或任何绝对路径交给 Backup v3 的 context_ref 参数。八个 refs 位于实际 context.global_evidence_refs，均为两字段，未来值保持 null。

## 6. Backup 实际审查边界

修复 OPEN_BOUNDARIES 的 self-pin 问题并独立审查后，实际 review bundle 按 review-input.template.json 组装。root_publication_refs.scope/owner 必须来自 assembly 的 Scope/Owner，而非 consumers Scope/Owner；roles 必须等于最终 context.role_policy.registry_ref。consumer_result_ref 是 consume result.json 三字段；context_ref 是最终 assemble context.json 两字段。

其实际审查顺序为：hold 全部已声明资源 → consumer_closure/六个真实 Job → _vector → dispatcher stdout/receipt 当前CM40绑定 → _role_registry 与 assembly owner/scope绑定 → _dispatches → _global 八份文档 → _review_execution_cutoff → reader资源闭合 → 关闭 guards → 才写 independent-review.json。原 NF6 qualification 与六个 Mode 继续引用既有 pin，不重新签发。

当前 v3 的 self-pin 约束尚不能靠这些模板实现。不要实际运行一个明知缺少该 gate 的 bundle 来重演失败。后续审查成功也仍需 Backup 的真实普通 FINAL、Root 的真实三行捕获、固定 capture index 发布与登记、Root 观察 issuance 和独立 owner 流程。这里全部保留 null，不产生任何授权。

