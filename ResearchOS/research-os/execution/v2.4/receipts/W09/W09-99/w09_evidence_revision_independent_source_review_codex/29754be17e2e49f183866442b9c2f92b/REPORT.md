## Review Summary

**Verdict:** REQUEST CHANGES

v4 补充了原 Go stdout 重建、逐 ID 的独有导出引用和 SQL snapshot 阶段。当前源码仍有合法路径不可达、mode 独审顺序循环及 witness 读取边界缺口；不可采用为正式 Source 或用例资格。

### Critical Issues

无已确认的 Critical。候选未执行。

### Important Issues

- **R01** `w09_formal_router.v4.proposed.py:165,241` 与 `w09_evidence_closure.py:96,110,208`：每意见新增一个 structured binding，使前缀匹配数从20变40；旧20计数必拒绝合法 C19/G01。binding又被opaque过滤，20bindings无法进入消费者。仅把完整的 `simulated-opinion-00..19` body归为opaque并计20，binding须解析及核run/owner/ordinal/IDs/pin。
- **R02** router `278,305–316`、runner `138,151`、closure `355–386`：独审receipt的本次run/report SHA需运行后才能确定，Env却须启动前固定SHA；每次路由又生成新run。分离native report producer与只读closure consumer，消费同一个已封原run，缺review保持NOT_RUN。
- **R03** closure `404–421`：host/junction witness直接 `root / item.path` 读取，丢掉旧Root-relative resolve边界；junction只核前三个argv。读前核exact REF/规范Root内路径/本run有限allowlist并拒alias/reparse；完整绑定 `cmd.exe /c mklink /J root target`。
- **R04** closure `208–220,247–340`、Go tests `242–247,263–264,320–348`：A06 context/bundle冻结断言仍缺对应原call result/error索引，C19 simulation artifact IDs未联结原HTTP artifacts/evidence req/resp。保原断言，追加真实原结果与有限逐ID raw refs，missing locator保持NOT_RUN。
- **I01** 恢复链：f72e/a26/report原byte恢复通过；earliest72ad/dc4原bytes未恢复，04前置apply_patch完整wrapper缺失且保持NULL。不能称全历史immutable。Root如无法恢复，应把初始seal标为不可采用历史，并在新Source UUID中冻结已核当前6候选及原始恢复/overwrite链，禁止重写原NS或推算原exit。

### Suggestions

两处owned parser共享明确的有限标签分类规则，避免body与structured event重名再次破坏合法路径。

### What's Done Well

- 原业务断言保留；新增Go map switch与实际 `Object` alias兼容。
- stdout与report逐record相等、assertion ID实际唯一event路径及pins已补。
- 五个A06 SQL阶段有真实snapshot rows；HTTP和文件继续封原始bytes，未导出Authorization。
- 两次overwrite实际sealer input/result分别保留，未按三个被覆盖文件重计。

### Verification Story

- 当前Source36、finalization7、origin annex3、旧v3 Source13成员实际hash正确；3个Main basis无漂移。
- 六组whole forward/inverse、五组v3→v4整字节对比正确；仅Python AST，未import、compile或执行候选；Go语法/build未验证。
- G01/G02及C19/A06两命令完整roster/投影静态复核；全部实际NOT_RUN。
- 原rg581/582、overwrite583/584各一次保留；本审新工具失败0。fixed第四cut48→580保持，未读写canonical。
- Source接受、whole-suite资格、正式case接受、provider调用均0。

此报告与 `review.json`、`audit.json` 及原工具I/O一起封存。Source请求修正，并非实际执行或验收。
