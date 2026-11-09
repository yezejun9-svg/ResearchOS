# A21 actual caller 独立 Source Review

结论：REQUEST_CHANGES。3项P1和2项P2；禁止据此包开始actual。没有自修作者Source。严格反例、精确63源列表和源码行号见findings.json与counterexamples.json。

P1 A21CALL-01，validate_root_actual.py:84：已绑定的H20 61加A21五overlay为63项（3替换、2新增），但原断言要求每一项都是internal/domain或ops/backup下的.go。完整predicate对精确清单返回False：20项被拒，包括apps/control、internal/recoveryauthority、ops/supervisor、numbered SQL与两份domain内SQL。因此这个包会在建候选/编译前确定性失败。必须保留完整已审63项，建立精确允许名单和逐路径相对安全校验，不能删掉这些依赖来满足错误断言。

P1 A21CALL-02，validate_root_actual.py:271：typed-child-evidence仅被检查初始不存在并作为env字符串传入。后续无读取、校验、pin、inventory、归档/export或closed绑定。独立控制执行原event gate AST片段，提供13个synthetic run/pass及包pass，在不提供任何typed child材料时照样通过。该控制不执行实际测试，也不证明未来测试会PASS；它证明success gate不要求typed64/PID/FILETIME、后代argv/raw stdout/stderr与闭合证据。必须在成功前校验并封存实际有界typed corpus、来源和闭合。

P1 A21CALL-03，validate_root_actual.py:292与prepare finally：独立纯内存FakeGuard执行原finally片段，第一个cleanup返回error时assert中断，prepare余下1个、validate余下4个guard均不调用close。另一FakeHelper执行原invoke函数，仅返回带error和未闭合job的虚构结果，原invoke在jobs.append之前assert；jobs仍为空而closed的all(jobs)为True。准备阶段先写ready，验证阶段先写PASS，再finally清guard，且验证不要求prepare cleanup refs。需每个guard均尝试并记录；异常与失败job也进入闭合审计；NOT_OBSERVED不能变为closed；最终ready/success需在cleanup证据通过后签发，并由stage2精确绑定。

P2 A21CALL-04，validate_root_actual.py:105及prepare同类比较：原CP JSON revision==int(arg)允许true、366.0、0，已用原predicate纯内存逐例证实；OW只有SHA/bytes锁定，没有positive-int结构校验。需对CP/OW执行type-int且>0（排除bool），CP再与显式动态revision比较；保持同一四ref vector。

P2 A21CALL-05，validate_root_actual.py:17及compiler list：FIELDS包含test/embed Source，但没有Export或Module.GoMod，go list未请求-export；编译使用共享GOCACHE/GOPATH。当前inventory支持source/embed清单，不能声称完整冻结compiler export/module/cache闭包。需补确切依赖清单与守卫，或采用审过的隔离cache方案，并让声明与持有范围一致。

已通过的基础事实：H20 actual与A21 v2 Source独审状态和exact refs匹配；63源组合数量成立；原9父4漂移叶=13未来run的roster、H20公有fixture经UpgradeLocal产plain21、无New24/截ledger、disk/return Recovery测试均保留。程序字节仍fixture，非真实维护21/22程序。新worktree/env/isolation/validation output均是固定且不存在的命名空间。实际参数合同为prepare10参数、validate12参数（后2个为isolation.ready SHA/bytes）；四Canon SHA/bytes向量相同，checkpoint revision显式。prepare实际计划在HEAD前后用Git核对，validate只绑定已封ready中的head，没有独立再次查询当前HEAD；本轮没有Git调用。

外部调用Source使用二进制stdout/stderr句柄和已pin的Windows Owned helper，并保留实际结果与raw refs；descendant test binary exit=NULL没有伪造。它们不能抵消上述闭合与证据缺口。source_guard本身acquire异常会尝试关闭自己，问题是caller多个guard的finally短路。

独立修正后的50项检查完成、132个精确输入在真实SourceReadGuard下稳定，全部guard已闭合、retained=0。原event/finally/invoke/revision片段的counterexamples只使用纯内存synthetic objects；未运行完整caller、任何Git/Go/compiler/SQL/native产品/CLI/model。当前四Canon未读锁写；Main、旧Source、作者包、SQL和candidate不改。正式accepted delta=0，Native、public late failure、真实21/22来源、全链及Owner/cutover仍OPEN。

机械失败947=e6dd3e：独审初次把拒绝数量预写18，仅按前缀计数，漏两份domain SQL；原完整predicate实际拒20。保留原review.py、完整review-failed.original-tool-io.json及原cleanup。修正版只改独审数量条件/说明及新cleanup名，58caf0 outer/Python0；原call outer/Python1、Native/modelNULL未清除。本轮没有产品失败或重跑。原作者945保持partial envelope：chunk/outer NULL不捏造。

STOP / FINAL。作者修订后需要新的独立Source结论。

