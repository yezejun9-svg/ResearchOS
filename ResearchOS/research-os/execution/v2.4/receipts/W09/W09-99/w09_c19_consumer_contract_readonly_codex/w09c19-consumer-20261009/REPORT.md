# W09 C19 producer 后续 consumer 契约（独立只读）

结论：可以先在原隔离 candidate 上验证两个 consumer，再由 Root/W02 登记正式入口。component PASS 不算正式接受。后续仅变更 canonical/commands 不要求重跑已经完整关闭的 producer；原 producer vector 必须保留为其运行时历史证据，不能继续称为 CURRENT。

本次只追踪原三份 Python v6 Source 与已接受 r2 calling contract，复用先前 Source 审查。46 项静态检查、16 个输入 pin 通过；没有执行 producer、consumer、Git、Go、SQL 或模型，没有修改 Main/canonical。结构化参数见 consumer-contract.json，真实 run 相关占位符必须由实际已审查产物填入。

## 1. 最小入口、同 run 与输出

两个入口顺序沿用已固定 next-task 契约：
1. test.research.fixture / W09 / 空 check / C19。
2. test.retrieval / W09 / 空 check / C19。

每个最小 argv 是 [locked Python, -B, -X, utf8, <candidate>/ops/ci/w09_formal_router.py, <key>]，cwd 必须是原 candidate 根目录。router 的 ROOT 是 cwd，而 producer ROOT 来自脚本位置。必须让 sibling w09_evidence_closure import 可达；最小 argv 没有照抄 producer 的 -I。若采用 -I 隔离 wrapper，须另行明确固定的 sibling import 路径并审查该 wrapper。

两次均提供 W09/空 check/C19，以及六个环境字段：
- RESEARCHOS_W09_NATIVE_REPORT_REF / SHA256。
- RESEARCHOS_W09_TOOL_RUN_REF / SHA256。
- RESEARCHOS_W09_MODE_DECISION_REF / SHA256。

这些 REF 必须是 candidate 根下的规范相对路径（正斜杠、无 ..、无绝对路径、无 reparse/alias）。两次报告、tool-run 及 SHA 必须完全相同，mode decision 则分别绑定各自完整 route。允许两条 decision 引用同一份非作者独立 review，因为 review 的 schema 不要求 route 字段。decision/review 必须源于本次原始 native 审查，不可预填 QUALIFIED。

TEMP/TMP 应与 producer 的 .local/w09c19-producer-env-1a11f08/temp 相同。FIXTURE 检查实际比较导出 state root_path 与 consumer 的 tempfile.gettempdir()；换临时目录可能产生 FIXTURE_INPUT_NOT_ACTUAL。decision 与其 independent_review_ref 的文件也须在 candidate 根内，且 review 不得位于 producer run 子树。若独立审查原件保存在外层审查目录，只能按授权把原字节复制到 candidate 的独立审查命名空间，保留非作者身份与原始 provenance，不能重写为 Root 自审。

原始 evidence 取 producer packet index 的 original_report_ref、original_tool_run_ref，转换成相对同一 candidate 的路径。报告所在目录为 execution/receipts/W09/retrieval/run-<原32位run_id>/，原 go-test.stdout.jsonl、go-test.stderr.txt、owned/*.raw 完整保留。native-packet 归档复制件用于保全，不能直接替换 original refs。owned_export_ref 等字段包含原绝对路径，随意搬到 Main 会破坏绑定。

两次各要求实际 exit 0，JSON status PASS，assertions=3，assertion_ids 精确 C19-01/02/03，native_assertion_ids 精确 C19-01..05，formal_acceptance=PENDING_INDEPENDENT_VERIFIER，mode_evidence.mode=FIXTURE 且 formal_authority=false。source_pins 为原 stdout、stderr、report 三个精确 pin；native_tool_run_ref 必须为同一次 producer；owned_export_member_count 对应该报告完整原始 owned 集合。封存每次 consumer 的实际 argv、cwd、允许环境、stdout/stderr 原字节及 SHA/bytes、native exit、Job/guard closure，不能只保存解析后的 PASS。

producer 的真实 selected 顺序是 ChainInvalidation 然后 ExplicitOriginAndUnknown。router 对名单排序比较，但 verify_native 用报告原 selected 顺序重建 Go argv，因此无需也不得改报告顺序。C19 consumer 分支只读取现有文件，不调用 producer/Go；PRESERVED 旧分支的子进程不属于这两次 C19 路径。

## 2. 独立 mode 资格必须在消费前完成

closure.py:551–597 要求两条 decision 分别为 researchos.w09-mode-decision.v2，mode FIXTURE、decision QUALIFIED、input_origin OWNED_TEMP_DIR，并绑定原 run/report/stdout/source_sha256/go。producer_id 与 reviewer_id 非空且不同，reviewer_role=INDEPENDENT_NON_AUTHOR。

其 typed independent_review_ref 必须固定 path/sha256/bytes，文件 schema=researchos.w09-independent-mode-review.v1；actor_id 等于 decision.reviewer_id，actor_role 为 INDEPENDENT_NON_AUTHOR，producer/run/report/source/go/原 OS 与 OS release 均一致，decision QUALIFIED。字段来源见 mode-receipt-required-fields.json；该文件只是字段契约，不是已签发 decision。

## 3. Main 采用与 commands 登记

直接在隔离 candidate 调 router，可先作为 component 验证。它不读取 commands.json，也不要求 Main 已采用三份 Python；但 Root 必须另有具体 consumer 资源/输出授权，不能把 producer-only scope 自动扩成 consumer scope。未登记的直接调用不产生 v2.4 正式 dispatcher 路由资格。

观察到当前 registry revision 39：test.research.fixture 仍指向 Go tests/research/check，只支持 W08-01/02；test.retrieval 仍指向 tests/evidence/check/main.py，只支持 W09-01。两个 key 均未接纳 C19，也没有透传六个 evidence 环境字段。

正式调用沿用 next-task 中的 dispatcher argv：
- locked Python execution/command_dispatcher/dispatch.py test.research.fixture --task-id W09 --case-id C19 --spec v2.4。
- 随后同命令改为 test.retrieval。

Root/W02 登记至少要具体处理：
- 两个 key 的 executable_tool/argv/cwd，让上述精确 tuple 实际落到已审查 router 与原 candidate ROOT；将 W09/C19 纳入 selectors，同时保留旧 W08/W09-01 行为。dispatcher selector 是逐字段校验，最终完整 tuple 仍由 router 拒绝不支持的组合。
- 把六个 evidence 环境字段加入 allowed_env，保留 TEMP/TMP；required_env 是整 key 全局要求，直接把六项全加为 required_env 会破坏不消费这些证据的旧分支，应由 C19 router 分支检查。清空 check selector，不从非受控继承环境带入其他 check。
- 若 test.research.fixture 全 key 改为 Python router，其 PRESERVED W08 分支要求 RESEARCHOS_GO，必须用 tool_env 绑定 locked Go；不能只换 executable_tool 而漏掉旧分支依赖。
- 固定入口、sibling module、dispatcher、锁工具、原 21 项 Source 和实际 packet/decision/review 输入，登记 output/Job/guard 资源。dispatcher 只在 argv 中记录可识别文件，不能代替完整 consumer 输入冻结。

现有 registry 每个 key 只有一个 argv/cwd，没有 route-specific cwd。因此若 Root dispatcher 从 Main 发起、C19 留在 candidate，而旧 W08/W09-01 要继续在 Main，须具体审查分支 wrapper/路由设计；不能仅全局改 cwd 后宣称旧分支不变。本次只给契约，没有编写或批准该注册实现。

代码没有“必须 Main adopt 才能消费”的条件，硬条件是当前 consumer ROOT 下的 21 项 Source、tool lock 和 Go 与报告版本相符，且原 owned 绝对引用成立。六份候选源已部署至 candidate 足以做 component；Main 正式采用是 Root 后续集成动作。若坚持把 formal ROOT 改为 Main，不能凭复制报告绕过路径与当前 Source 检查，需要先证明完整迁移仍满足原字节契约，否则在新根产生新的 producer 证据。

## 4. canonical 冻结与是否重跑 producer

准备前完成 scope/worker/owner/活跃 parent 注册，然后生成 CP3+VECTOR3。prepare 与 producer 必须用同一 vector；两者之间或 producer 持有 guard 时，四份 canonical 不能变。否则 r2 会在当前字节/vector/ready 检查失败，不能改 ready 或封存 vector 冒充原调用。

producer 已完整 closed、Job/guard 全关闭并经独立审查后，允许另行登记 consumer scope/commands，并生成新 consumer 的当前输入快照。旧 producer vector 保留为其真实运行时 pin，不再是新阶段 CURRENT。router/closure 不读取 checkpoint/commands/vector；producer SOURCES 的精确 21 项也不包含四份 canonical。因此仅后续 registry/canonical 更新，不使原 native 业务证据失效，不要求重 producer。

仍需冻结同一个 candidate、21 项 Source、locked Go/Go lock、原报告/raw/owned、同 run review/两个 decisions 和两个 consumer caller/registry。任何这些源码或工具字节变化、原 run 数据损坏、实际 ROOT/owned 路径不再满足契约，不能归为“仅登记更新”；先判断能否保留原输入精确复现，不能通过编辑原报告/decision 消除差异。两次正式 consumer 也宜在同一已登记 registry 快照内顺序完成，避免把两次不同路由状态拼为一个接受链。

## 5. 完成计数边界

native producer 的 5 个 ID，是 C19-01..05 的原业务证明。每个 formal route 输出 3 个冻结 C19 ID；两个 route 共用一例，不是 6 个新的正式用例。代码明确 producer formal_case_accepted_delta=0，consumer 仍 PENDING_INDEPENDENT_VERIFIER。只有完成规定的两次正式入口及独立接受后，才可把 C19 作为一项正式用例处理；本回执新增正式接受数为 0。

这不等于 W09-99 ACCEPTED。G01 还涉及 A06 fixture，G02 是另一个真实 Windows/local 资格，A06 有独立完整断言与 ContextBundle/materialization 连接；42 必选用例和其他 owner 边界未改变。

证据定位：router.py:15–17、21–30、89–129、132–271、280–356；closure.py:34–67、70–177、551–597；retrieval.py:15–48、127–250；dispatcher.py:94–148、177–205、229–250；r2 calling contract 与 prior next-task 的 review_sequence/formal_commands_after_binding。全部对应已 pin 的原始文件，未以新执行替代阅读。

