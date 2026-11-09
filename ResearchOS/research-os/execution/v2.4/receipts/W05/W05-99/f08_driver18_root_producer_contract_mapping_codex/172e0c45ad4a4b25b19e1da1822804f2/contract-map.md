# F08 Root A01–A07 producer 映射

结论：MAPPING_READY_ACTUAL_PRODUCTION_OPEN。已有 v3 authority / binder 与 v4 controller 的静态契约可用于编写 Root producer；本回执不生成资源资格、scope、lease、CAS、grant 或实际工具调用。A01–A07 的实际完成仍为 OPEN / NOT_RUN。

这次仅按目录 catalog 读取 r330 已有公共脚本和回执。28 个已有哈希的输入将做封存前再核对；已读的 intent/audit 两份 JSON 单独作 late-pin，保持“最初未记 raw hash”的边界。未追读 live canonical，未重哈希大树，未执行候选或 helper。

| 门 | consumer 位置 | 可复用的 r330 函数 | 最小新增内容 |
|---|---|---|---|
| A01 | authority.scope:194–210；controller:82–135、146–167 | v7 verify:64、runtime:105 | driver 专用有限 files/python/go/GOROOT/compiler_images/offline_modcache_copies；真实 Python/OS loaded inputs。CLI 大资源目录的 ref 不能直接改标签成为资格。 |
| A02 | binder.build_scope:44、draft:69；authority.scope:159、lease:216、registration:235–281 | v7 canonical_expected:182、origins:193、prepared:254 | 明确当前 phase/UUID/before/after/cut/source guard/metadata timeout；两条 CP WIP 和专用 OW lease。使用已有 driver binder，不再编写 CLI scope builder。 |
| A03 | binder:72–79；authority:260–268、289–321 | v7 registration_review:276 | 每阶段完整 bound scope 独审；当前 draft/MF/4 originals/4 desired/lease/代码四 SHA 的独立注册复核；先冻结 preaudit/prepared_refs，再 review，避免循环。 |
| A04 | authority.registration:224–372、job:144–157 | v7 register:288、run_registration:313、seal:335 | 新 request 和完整 argv/cwd/env/timeout；独立 wrapper 实际 Job；intent/audit/verified 绑定 current_scope/draft/request；最终 bundle 和 members/files manifest。 |
| A05 | authority.verify_authority:508；outer_completion:374–433 | v7 grant:353；root-launch-once.v2:44–74；completion-reader:36–74 | driver phase grant 与 Git -C ROOT 原 argv；Root 原 exec_command / terminal write_stdin 的 input+response+真实事件 locator；单次实际授权，禁止目录/exit0 标签造证。 |
| A06 | controller:93–136；authority.prepared_evidence:435–506 | completion-reader 的 raw/firstcause/new-manifest 收口方式 | 完整实际 prepare files、固定 18 NOT_STARTED roster、真实 launcher Job/raw、external Root launcher-pair 与 proof。保持原 inner/launcher manifest 原字节。 |
| A07 | controller:154–279 | 保留已审 v4 controller、fbf9 launcher、原测试 | 真实新工具链、3 graphs、4 builds、3 buildinfo、17 tests、I16 两额外阶段的独立闭包复核。总 30 calls，上限 32；I17 继续 OPEN。 |

## 精确注册接口

REGISTER child argv 共 16 项：`[PY,-I,-S,-X,utf8,REGISTER,--registration-draft,DRAFT.path,--draft-sha256,DRAFT.sha256,--registration-review,REVIEW.path,--review-sha256,REVIEW.sha256,--output-root,REGOUT]`。

WRAPPER argv：`[PY,-I,-S,-X,utf8,WRAPPER,--request,REQUEST.path,--request-sha256,REQUEST.sha256]`。两者 cwd 都是 `D:/作品集/ResearchOS/research-os`，env 使用 scope 的公开环境，timeout 使用 explicit registration_timeout_seconds；request/raw/result 必须来自该实际调用。wrapper.result 需自身真实 owned Job，不能复制 inner.result。

Root writer 沿用 v7 register 的顺序：初始 all4 CAS → Git/source guards → immutable intent → CP exclusive temp / source guard / immediate all4 CAS / replace / verify → OW 同样步骤 → final all4 → unchanged reads / final source guard → final all4 → verified。失败保留 first cause；无重置、回滚、同输入自动重试。

`intent/audit/verified` 都必须有 `current_scope_ref,registration_draft_ref,requested_ref`。post audit 还需 `wrapper_invocation_ref,draft_manifest_ref`。preaudit 与 post audit 是两个原件；preexecution draft manifest 不纳入未来 request/review/postaudit 的哈希。最终注册 manifest 必须使用 `members` 或 `files`；现有 CLI `entries` 不符合 reader。

## 工具原件配对

launcher argv 共 11 项：`[PY,-I,-S,-X,utf8,LAUNCHER,PHASE,SCOPE.path,SCOPE.sha256,GRANT.path,GRANT.sha256]`。原始 exec_command `cmd` 和 `workdir`、terminal write_stdin `session_id/chars`、全部响应对象先原样保存，再封闭格式 action。

action 仅 9 个键：`schema,actor,tool_name,input_ref,response_ref,initial_action_ref,command_identity,request_event_locator,response_event_locator`。command_identity 精确包含 `launcher_ref,argv,cwd,phase,scope_ref,grant_ref,run_uuid`。terminal response_ref 必须逐 ref 等于当前 completion.tool_result_ref；initial 与 terminal 的真实 request locator 不同，session 相同。

现有 r330 `root-launch.tool-observations.json` 只有 initial/polls/final 响应，没有原始 request/input/action/event-locator。Root 应在未来实际调用时捕获；不能从 session 或目录重建输入。当前 adapter 只支持真实 async exec_command→write_stdin，不支持伪造同步响应的 session。Root command producer 还要接受独审，证明 shell cmd 确实执行声明的固定 launcher argv/cwd。

outer `actual_native_launcher_exit` 在当前 driver consumer 中明确必须为 NULL。任何实际独立采样 native bridge 保留在原始记录中，不能改写原件。Python caller、launcher child、controller、工具 outer 各自退出只按真实来源填写。

## prepare → execute

prepare 和 execute 共用 UUID、work/prepare roots、fixed/catalog refs，使用不同 phase lease、scope/grant、当前注册 tuple/cut、注册目录和复核。prepare output 必须是真实全量拷贝；1899 fork、1899 pristine old module、offline files、8 overlays 与 actual work tree 完整集合和字节一致。

原 prepare result 必须为 `native_calls=0`、I01–I18 全部 `NOT_STARTED/actual_exit:null/qualified:false`，`first_cause:null,secondary:[]`。真实 launcher request/owned Job/raw/completed、inner/launcher 的原始完整 files manifest 均合格后，Root 在第三个新 namespace 封 launcher pair 和 proof，不向两份原始输出树添加任何文件。

随后单独绑定并独审 execute scope，以实际 prepared ref 和 proof 重新注册、guard、grant。原 v4 controller 执行 PARTIAL_17_EXPLICIT：I01–I16、I18。I16 维持三个独立进程、pristine old driver 拒绝、closed bytes 不变及原 cause/count/x 断言；I18 保留原完整 body。I17 raw-DDL/callback 等另支路仍 OPEN。

## 原件与边界

r330 terminal response 的 exit_code=1、原 PythonNativeExit=1 继续是 CLI 历史失败事实；本次只读引用不再计一个 origin，不成为 driver18 资格。固定 cut、历史失败、canonical 和旧候选都未改。

driver caps 保持 `32 / 600 / 750 / 3300 / 3600 / cleanup5`，image64、compiler_processes2048、job_active16、fixture_HTTP0、SDK/Node/model/paid0。Root metadata 的注册 timeout 必须显式提供，不能误称属于 controller 32 native calls。

详细字段、schema、argv、Job 原始结果、manifest 和最小 5 组实现见 `contract-map.json`。这份 map 已可交 Root 实施和独审；实际 authority/准备/编译/测试、SQL24 安装、完整 callbacks 与正式验收不由它授予。

Verification：仅公共只读 IO / Python AST；无候选 import、构建、目标测试、网络或 canonical 操作。新 failure origins 0；旧原件及失败前缀未改。
