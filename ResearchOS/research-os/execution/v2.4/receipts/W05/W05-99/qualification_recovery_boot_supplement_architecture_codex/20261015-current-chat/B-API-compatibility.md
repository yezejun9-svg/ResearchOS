# B75 与 C+boot 的精确兼容边界

证据：G04-B75-full-source.raw（git show candidate75），G03 B-author-report；不是B独立接受。B75基于f48fca0e4013bda19913a34d91da0cd23157a08b，tree ba3f9d4c101df39ab17856158d5fc72a9f0600ce。Root须先采用独立B审查结论再冻结C施工基线。

| 真实B75位置 | 现状 | C最小接线 |
|---|---|---|
| :668 validatedQualificationFailureTx(tx *sql.Tx, project,taskID,runID string,epoch int64) -> qualificationFailureClosure | 私有Service方法；无D production调用 | 保持签名/私有返回type。只在该方法内以严格kind+namespace分支调用新的私有historical validator；不得导出“通过”bool或通用SQL入口。 |
| :676–700 | 查询host:qualification-failure-closure，恰好1 marker；ONLINE_FIRST_GATE_TOOL_DENIAL | C使用host:qualification-failure-maintenance + operationID；精确检查两个namespace中subject歧义/重复后拒绝，不能宽OR后随便取一条。原online解析逻辑独立保留。 |
| :707–717 | SCHEDULER作者与currentAuthorityRoot到OWNER | C作者当前未撤销OWNER，run_id=null；historical branch重验原Owner/Host/root，不假装在线Scheduler作者。 |
| :754–762 | proof kind在线，包含真实rejection_digest及BEFORE_PREPARE_EFFECT_TX rejection | C不能制造typed online denial/rejection digest。独立HOST_TOOL_EFFECT_NOT_DISPATCHED版本化历史重构及raw/source绑定；boot proof只作current-quiescence premise。 |
| :758 | B full plan digest = Digest(Bytes({core,proof})) | C FullPlan为既定PlanCore+exact proof bytes+planned rows，request_hash=plan_file_sha256；两种canonicalization不能互换。历史分支分别重算C所有hash。 |
| :765–774 | 原生native、online broker accepted/completed2、pending0、第三帧rejected | C不能制造B drain ticket、broker join或ACK3；原3/2和raw queue_empty=false保留；独立历史分类须验证所有C premises。 |
| :788–803 | effect1、rejected0、CONFIRMED model且ledger UNKNOWN/null money | C完整effect/queue/cursor/control census仍要求无额外UNKNOWN；CONFIRMED模型与UNKNOWN金额保持原账，不变成0。 |
| :805–819 | artifact/link/event/outbox/snapshot/outcome hash组成私有closure | C分支验证自身五version delta、封存MANIFEST/profile、marker、全census/outcome，成功才构造同private closure；D只消费接受后的结果。 |

不得从boot helper调用online denial构造器或用fixture ticket跨入C。historical validator放在已列internal/domain/qualification_failure_maintenance_windows.go，runtime_qualification_failure_windows.go只做私有分流与共同不变量；其测试加在既有同名windows_test和C维护test，范围不增加。没有接受B时这些都是提案，不是实施。B独立审查如改变API/语义，Root按具体变更复核兼容点；禁止忽略新审查结论硬套本稿。

