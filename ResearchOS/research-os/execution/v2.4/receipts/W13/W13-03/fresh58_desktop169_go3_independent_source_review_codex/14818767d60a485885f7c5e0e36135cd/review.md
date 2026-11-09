## Review Summary

**Verdict:** REQUEST CHANGES

**Overview:** 原169个Node用例、Go3选择器及独占目录语义均保留；纯源码准备有两项 Important 未闭合。实际 Root authority、资源、预算和资格仍是 OPEN。

### Critical Issues

无已确认 Critical；这不构成执行资格。

### Important Issues

- **D169-R01 — response lifecycle 可提前关闭后被接受。** [legacy_http_observer.proposed.cjs:60](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_desktop169_go3_controller_preparation_codex/52998fc9c4d64166b10aa02e6eca11e4/legacy_http_observer.proposed.cjs:60) 无论 `finished` 是否为真都 `active--`；[fixture_evaluator.proposed.py:28](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_desktop169_go3_controller_preparation_codex/52998fc9c4d64166b10aa02e6eca11e4/fixture_evaluator.proposed.py:28) 只校 final active/errors 与彼此独立的聚合数。真实 `request-received → body-complete → close(finished:false) → exit0` 可以满足这些谓词而得到 `qualified:true`。修复应逐 observer PID/request id 关联 body end、finish、close，拒绝缺失/重复/陌生 id 与不完整关闭；允许合法 GET/SSE 的事件次序。该路径为源码推演，未执行伪造fixture或候选。
- **D169-R02 — helper 收尾时间未计入 remaining。** [desktop_controller.v2.proposed.py:100](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_desktop169_go3_controller_preparation_codex/52998fc9c4d64166b10aa02e6eca11e4/desktop_controller.v2.proposed.py:100) 仅减5秒；[windows_debug_job_tree.future_images.final.proposed.py:663](D:/作品集/ResearchOS/research-os/execution/v2.4/receipts/W13/W13-03/fresh58_desktop169_go3_controller_preparation_codex/52998fc9c4d64166b10aa02e6eca11e4/windows_debug_job_tree.future_images.final.proposed.py:663) 的成功证据收尾另有25秒。launcher只要求 outer > inner+5。最后一轮正常进程可耗尽 process预算后仍合法进入25秒收尾，使整体超预算并可能被 outer kill 截断证据。尾部超时会拒绝资格，未发现 late success 被接受。应在启动前扣除成功收尾/失败清理/证据IO预算，或给新helper同一个Root绝对deadline，并校验完整outer阶段预算。原9c/6a不改。

### Suggestions

- `actual_native_top_commands` 在 helper 实际创建进程前增加；可改名为 requested operations，或另记有真实 PID/creation 的启动数，保留 NULL exit。

### What's Done Well

- 原 JS 只有一处目录分配改写，逆向还原完整原字节；原 mkdir、wx、copy 和断言保留。20个目录、15条启动路径、16次CREATE（unreaped同路径两次）与5条不启动路径明确区分。
- 新futureimage路径只在暂停的真实CREATE事件授权：精确 path/UUID/case/ordinal，hFile与当前path句柄身份及SHA一致。事件错误必须先终止ownedJob成功才能Continue；失败不Continue。此结论仅为代码路径，Windows行为待实际验证。
- Go3 raw PASS与完整owned debug tree先检查，Node169仍逐叶原断言；9个builder内部操作与176个top-level调用分别记账。两项offscreenElectron保持真实原fixture，visible installed GUI为0。

### Verification Story

- Tests reviewed: yes。原162源码、7回归正文、Go3原选择器和future controls；所有新target验证NOT_RUN。
- Build verified: no。只做pureIO/hash/inverse/AST parse，没有导入或运行candidate、Node、Go、DLL、Job、网络或canonical。
- Security checked: source only。Rootverifier/catalog/grant/tuple/当前58 CLI2资格与预算NULL；准备包当前在分配前拒绝。
- 30个MF成员+MF及10个额外冻结输入，共41个实际pin均0drift；四份wholeinverse成立。controller9个定义、helper19个定义AST与源码bytes不变。没有读取或推广未来Root目录。
- 本审查新增两个metadata失败058eb9/b27bd3（各outer/Python1/1，targetnativeNULL），原始input/result封存，未重跑失败输入。首条roster误报已撤去；实际字段leaves/regressions/go_units与consumer一致。原作者1622f8/ef37a8仍只保留原次数。
