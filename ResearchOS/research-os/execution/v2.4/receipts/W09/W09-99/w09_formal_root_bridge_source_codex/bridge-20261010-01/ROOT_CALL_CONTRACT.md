# W09 Root bridge Source

状态：可审查 Source；未授权、未运行任何 runtime stage。作者只写本命名空间；Main、Canon、产品文件未写入。当前 G02/A06 缺成功 Native 资格，所有依赖 Native 的阶段必须拒绝。

调用形式（未来由 Root 使用 locked Python；每一步用新的 request、Current4、限时 grant 和唯一 output_directory）：

    <locked-python> -I -S -B -X utf8 w09_root_bridge.source.py <stage> --request <absolute-json> --sha256 <sha256> --bytes <bytes>

共同 request：
- schema=researchos.w09-root-bridge-request.v1；actor_id=codex:/root；Root_thread_id=01a11007-5233-7ca1-b71f-9e9e5ce84c98。
- stage、created_at、expires_at、output_directory（W09-99 内全新目录）。
- current4：checkpoint、path_ownership、step_state、commands 四个实际绝对 path/sha256/bytes，严格依次；commands 只接受 CM40 的既有 pin。
- bridge_source_ref：本次 source 文件精确三键 ref。
- source_review_ref：实际独立 Source reviewer 出具的 decision=ACCEPTED_SOURCE_ONLY、formal_acceptance=false、source_ref=bridge_source_ref、reviewer_id 非作者/Root；source_review_audit 用 Main actual-role-audit 与原始 peer 三行证明实际作者，不能用 JSON issuer 字段代替。
- grant_ref 与 grant_audit：Root 真工具原件所绑定的 grant。grant schema 可由 Root 命名，必须 issued_by=codex:/root、stage 与 request 相同。request_body_sha256 是本程序 encoded(request 去掉 grant_ref/grant_audit 两字段) 的 SHA256；先生成 request body，再生成 grant 和实际 Root 工具回执，最后填入两个 ref，避免循环 hash。
- 审计 proof 的 actual_audit_ref 必须符合既有 Main researchos.w09.actual-role-audit.v1，原始 public 三行固定在 Main root_original_events 边界；proof actor 字符串与实际 backend 字面相等。
- 正式 context/review/issuance 及 Main vector refs 用 repo-relative forward slash path/sha256 两键；Root authority、current4、role/index refs 用相应 Main 规定的三键，不能混用。

阶段：
1. seed：context_input_ref 提供实际 run_id、六个 Native/tool/mode refs、固定 spec refs、environment、components 与其余不可推断事实。程序从实际 retrieval.py SOURCES 和两个 Go 目录构造完整 source_files/source_coverage，再用 Main _vector 验证，输出 context-seed.json。绝不把后续会改变的 CP/OW 塞进 stable vector。
2. propose：context_seed_ref、lease_expires_at；调用 Main _native 核验六个 route 的真实 report/raw/owned/Go events/mode，三 Native 失败或未闭合立即停止；产生四 consumer Scope 与 assembly Scope、各自 owner/worker；只产生 proposal，不登记。
3. activate：proposal_ref；检查 Source绑定、Current4、有限 lease、CAS；用既有 TP 注册 CP/OW 的独立 subtask/worker，仅 Root 以后调用。保留 SS、CM、既有失败计数、旧 owner。永不写 ACCEPTED。
4. consume：proposal_ref、context_seed_ref、isolated_environment（TEMP/TMP/USERPROFILE/LOCALAPPDATA/APPDATA 现存 repo 内隔离目录）。复查 Main Native closure，冻结读集合与实际 runtime modules，只执行四个 exact dispatcher argv，各携六个真实 env。OwnedJob 120秒/自身5秒清理；记录 true exit/cleanup 后再读/hash stream，任一步失败即停。C19 两个 receipt refs 原样保留，无 Native producer 重跑。
5. roles：proposal_ref、role_registry_input_ref；该输入包含 run_id、五角色、provenance、六个 route_execution_refs。每个实际审计调用 Main _role_audit，产生 execution-roles.proposed.json；Root 发布到固定 execution/v2.4/root_delivery_captures/W09/W09-99/execution-roles.json。角色中 Verifier 必须是真 backend /root/full_w09_source_review，作者列表包含本 Source 作者和实际其余作者。新四route 使用本次 Scope/owner，旧C19保留原 Scope/owner及历史有效lease。
6. publish-registration：publication_ref 指向 roles/capture 阶段 result、expected_previous_registry_ref（首次为 null）；只接受 Root 已发布的精确固定文件字节，TP 登记对应 CP slot。capture 分支还要求真实 original/capture 已发布且字节相同。不会静默覆盖固定文件。该阶段本身不发行正式接受。
7. assemble：proposal_ref、context_seed_ref（更新到真实 role registry pin 的 stable vector）、consumer_result_ref、plan_ref（固定外部 v2.4 execution.plan.json）、package_manifest_ref、code_revision、dirty、refusal_evidence_refs。Main _role_registry/_dispatches 验证六条链，程序构造 C19/A06 各四个 GLOBAL 文件、完整 context；保留历史 Native start/consumer end，不新造 C19 运行时间。A06-02 refusal 必須真实 raw refs。输出只供独立 Verifier 审查。
8. capture：只有真实正式 review 和正常 backend Final 已存在后运行，输入 context_ref/review_ref（均两键）、original_offsets 三个真实字节偏移、previous_index_ref（首次null）。从固定 Root 日志读原始 header/meta/adjacent Final，逐字核 actor、时间、内容完整 SHA，无 alias 或时间修正。输出 original/capture/index 待 Root 发布字节与 issuance；然后 publish-registration，才可 check。不能先预测 event/time。
9. check：prospective_owner_ref、context_ref/review_ref/issuance_ref、plan_ref。prospective owner 必须已得到当前 Root grant 明确批准，包含正确 evidence roots。调用 Main _registered_roots、verify_owner、recheck_inputs；结果是审查通过的纯检查，不登记 SS，不发行 owner。
10. derive：只有 Root 在真实审查/捕获/预检查之后实际登记 canonical SS，输入 plan_ref；调用 Main derive_formal_cases 固定 live SS，再 recheck_inputs。观察 W09 owner VALID_ACCEPTED、owned accepted_case_ids=[A06,C19]；保留其他 owner 的完整结果。CLI 只有全 index integrity PASS 才0。

Root 发布 roles、original、capture、index 是单独可审查步骤；本桥只校验实际发布字节再登记，不能将 proposal 当已发布。已有 index 需 Root 对 previous pin 做 CAS 合并。不得自动替换 Canon 或生成临时 SS 来让 derive 接受。

Source 验证仅 AST/纯函数有限控制；没有 Main 模块执行、dispatcher/Native/Go/SQL/model/TP/verify_owner/derive 调用。source-controls.json 对应当时中间 Source pin；final delta 控制对应最终 Source，旧失败/控制原件均保留。尚待独立 Source review 与 Root 真实运行。

机械诊断保留 original1123（不存在上级 AGENTS，outer1/PythonNULL）、1124（不存在 spec/v2.4，整体outer0/componentNULL）、1127（作者AST控制脚本 Dict.values()，outer1/Python1）、1129（.NET读 Root 日志共享拒绝及closed reader，整体outer0/componentNULL）。以上无产品调用；没有把整体outer0当内部成功。

