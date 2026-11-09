# Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** W09 六正式绑定仍有两父门的合法正向路径错误；正式证据和运行模式的执行绑定尚不完整。源码确实使用真实生产域、本地文件和 SQLite 操作，不能仅凭旧 roster 或改 ID 接受正式用例。

### Critical Issues

- W09-BIND-R01 · D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/w09_formal_binding_source_preparation_codex/e1275d3270ca43288293e798aa5eea34/w09_formal_router.proposed.py:9 — G01/G02 合法成功路径不可达。adapter在正式ID转换前要求 expected⊆observed；真实底层从不产生 W09-G01 或 W09-G02。完整底层 PASS 也必进入 SOURCE_REPORT_NOT_EXACT_OR_INCOMPLETE。 修复：分别冻结 native roster 与 formal projection。先要求原报告 source selector/status/exit、selected_tests/passed_tests、expected_assertion_ids 和 observed 完整有序或 multiset一致、无重复、raw证据当前，再按明确行为映射输出父门ID；不得在底层伪造父ID、删减原4/5断言或只检查非空/子集。

### Important Issues

- W09-BIND-R02 · D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/w09_formal_binding_source_preparation_codex/e1275d3270ca43288293e798aa5eea34/w09_formal_router.proposed.py:63 — 正式证据闭包没有实现。router仅确认report/raw路径非空，不保存逐条REF/hash；旧report的source_sha256是产品源文件hash，不能代替本次输入快照。C19主测试仅输出数量/一个origin ID，没有完整27条关系图/各snapshot hash；A06只输出检查后的布尔常量，不保留原API输入输出/根身份/文件与权限版本/hash/缓存命中记录。临时夹具测试结束后被t.TempDir清理。原dispatcher仅封自身stdout/stderr且 scope 为CONSTRUCTION_CHECK_NOT_PRODUCT_ACCEPTANCE，无法自动补 GLOBAL_EVIDENCE_V1。 修复：保留原断言，在测试临时资源清理前导出本次owned证据：C19完整records+root关系与snapshot refs/hash；A06实际A/B根与junction身份、每步文件/权限/索引版本、API请求响应及查询/缓存/fallback记录。adapter保存/核实际child stdout/stderr、source report和导出文件的path/SHA/bytes及每断言expected/actual/raw locator；绑定v2.4 acceptance/plan hash，同时如实保留legacy v2.0 fixture contract/provenance。Root生产run_receipt/command_receipt并由独立Verifier签acceptance_receipt；这些未完成前保持formal OPEN。
- W09-BIND-R03 · D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W05/W05-99/w09_formal_binding_source_preparation_codex/e1275d3270ca43288293e798aa5eea34/w09_formal_router.proposed.py:66 — 运行模式当前由selector硬编码，G01/G02未验证source.scope。A06一边mode=FIXTURE、一边保留LIVE_WINDOWS_LOCAL并只标reclassification_required；没有已审核的分类结果被执行入口消费。G02底层确实调用生产域和真实本地文件/SQLite、Windowsjunction，但使用合成t.TempDir/fixture身份与进程内httptest recorder；不能仅靠mode字符串、dispatcher的platform先决条件或Go PASS声称真实Windows11 x64 qualification。当前尚无实际Windows资源观察，这是明确OPEN，不是实际失败。 修复：冻结每路source scope与运行模式映射，并以已审source-scope记录绑定A06的t.TempDir测试输入/路径界限，保持产品内实际OBSERVED/LIVE snapshot语义而不改数据种类。G02要求本次真实Windows11 x64环境/locked nativeGo target、实际本机授权根/句柄或junction/文件读改删fallback原观察及输入hash；缺失返回BLOCKED/OPEN而不凭selector出LIVE PASS。允许生成受控本机测试文件，无需读取用户私有文件或增加外部服务。独立资格仍由Root真实运行后签发。

### Suggestions

- D:/作品集/ResearchOS/research-os/ops/ci/retrieval.py:100 — 正式版本采集仍从PATH运行git。下一最小版本可消费已锁Git绝对path并记其actualargv/hash；保留原上游handler的锁工具拒绝PATH fallback语义。未在本轮执行Git。

### What's Done Well

- 十个允许tuple由router精确拒绝cross-product，旧W09-01/W08-01/02/W17-01入口和child输出/真实exit保留。
- C19实际生产域测试保留4转载、2独立来源、20SIMULATED和同字节未知源；未知/相似文字未被计为独立OBSERVED。
- A06实际调用生产Handler/SQLite/本地根验证，修改删除移动撤权与Windowsjunction负例和FTS失败回退有具体断言；临时根用于FIXTURE的来源可定位。
- 作者明确未修改active registry、formal delta=0、mode discrepancy及实际G02 qualification未运行；原83faae失败保留。

### Frozen Binding Coverage

|入口|实际范围与结论|
|---|---|
|test.retrieval --task-id W09 --check-id W09-G01|C19来源独立/UNKNOWN/SIMULATED + A06失效/隔离/回退；UNREACHABLE_PARENT_ID; behavior source exists; evidence R02/R03 OPEN。来源：retrieval_test.go:40–174,177–368; local_test.go:11–45|
|test.retrieval --task-id W09 --check-id W09-G02|真实Windows本地检索/读改删撤权/越权/回退；UNREACHABLE_PARENT_ID; actual Windows observation/qualification NOT_RUN。来源：retrieval_test.go:177–526; local_test.go:11–81; dispatcher.py:101|
|test.research.fixture --task-id W09 --case-id C19|C19-01 四记录原链; C19-02 2/20; C19-03 UNKNOWN；Behavior source coverage present; complete graph/snapshot evidence absent。来源：retrieval_test.go:69–110 checks all4 origins and counts2/20/1/27; explicit relation rejection|
|test.retrieval --task-id W09 --case-id C19|same three frozen assertions; extra C19-04/05 retained as native scope；Do not infer second command receipt from first; actual command NOT_RUN。来源：retrieval_test.go:111–174 invalidation adds stricter native checks|
|test.retrieval --task-id W09 --case-id A06|A06-01 invalidated bodies/noCURRENT; A06-02 root escape0; A06-03 candidate failure+fallback/cache versioning；Real code/fixture source; raw input/result export and classification OPEN; source tests do not assert full cache identity matrix。来源：retrieval_test.go:197–315,318–368,395–490; retrieval.go:111–115,179–184; local_test.go:34–44|
|test.security --task-id W09 --case-id A06|same A06 assertion set; independent command receipt required；Do not claim W17 host security qualification or accept other cases; actual command NOT_RUN。来源：router lines41–46 exact W17 preserved vs W09 branch|

### Verification Story

- Tests reviewed: yes；先读原测试与冻结合同，再审路由器。本文是纯源码/IO/AST审查，未运行任何候选或产品测试。
- Build verified: no；只有 AST.parse，不等价 compile/native build PASS。
- Security checked: yes；精确 selector、真实根路径/权限/源 hash recheck 与证据边界经静审。G02 实际 Windows 资格仍 NOT_RUN。
- 作者 MF 5成员与15公共 source_refs 均实读重哈希，0漂移。作者83faae旧metadata失败仅引用，未重计。
- 本轮新增metadata失败0；产品、Git、Go、SDK、provider、CAS、canonical、正式接受均0。

### Smallest Follow-up Verification Set

- 合法六入口各自精确native roster→formal roster；四preserved tuple原argv/env/results不变。
- 缺一个native断言、删C19-04/05、重复/意外ID、未pass选中test、0assertions、错误selector、child nonzero均拒绝；不能用空/总量PASS。
- C19完整2original+4reposts+20simulated+1unknown数据/关系/快照hash；两个独立正式command receipts。
- A06本次TempDir A/B与junction实际路径/根identity、每种失效后的ContextBundle/current support与原API回执；actual cache project/permission/content/index版本变化；两正式command receipts。
- G02真实Windows11 x64/lockedGo/实际文件与junction/fallback观察；无资源只阻塞此路，不冒用G01/FIXTURE。
- 证据REF missing/foreign/outside namespace/hash drift/duplicate/raw locator错配/未署名mode decision与independent acceptance拒绝。

### Open Root Integration Boundary

- 新的不可变作者revision与独立源码复审
- 确定候选升级为正式owned source路径或Root显式允许immutable source路径；v2.4注册只由W02/Root CAS
- W09-01/W09-02/W03-99/W07-99依赖接受当前有效证明；不由本review改状态
- Root当前真实输入/资源/版本/失败counter及scope/producer冻结；不借W05/CLI2资格
- 六命令实际独立执行+GLOBAL_EVIDENCE_V1+独立Verifier accepts C19/A06 和两父门；本review formal0

当前 before/after tuple、失败cut、SourceRegistry、W05/CLI2资格均未修改或继承。本独审只提供可修复问题，不发任何实际 grant/qualification/acceptance。

