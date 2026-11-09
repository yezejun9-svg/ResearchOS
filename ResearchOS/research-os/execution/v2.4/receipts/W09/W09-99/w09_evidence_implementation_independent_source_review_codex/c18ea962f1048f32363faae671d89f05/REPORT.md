## Review Summary

**Verdict:** REQUEST CHANGES

v3 已加入真实文件、HTTP 和 SQLite 证据导出，并修复 G01/G02 的 native→formal 投影。还存在三处证据对应关系缺口；本次没有执行候选或产品，所有实际用例仍为 NOT_RUN，正式接受增量为 0。

### Critical Issues

无。

### Important Issues

- **W09-V3-R02-LOCATOR** — w09_formal_router.v3.proposed.py:125、194、208。报告断言没有从已 pin 的 Go stdout 重建；owned_export_ref 只核哈希和测试目录，没有等于当前 assertion-ID 的实际事件路径。C19-01..04 同属一个测试，后面三个引用都误指 C19-01 时仍满足现有谓词。修复：保留事件的实际路径和 pin，要求断言引用逐项等于该事件；从原 stdout 重建 W09_ASSERTION 和 pass roster，与报告逐字对应，并核冻结 expected 与真实 invocation。最小反例为同目录交叉断言引用、改报告但保原 stdout、缺失/重复/外来事件；这些控制尚未运行。
- **W09-V3-R02-CASE-CLOSURE** — w09_formal_router.v3.proposed.py:216、233、246、255。C19 只要求六条来源行，没有验证两 ROOT 和四 DERIVED 同源，以及图、Artifact、文件路径和原始字节的连接。A06 只要求至少一条 HTTP exchange，未要求已导出的修改、移动、删除、撤销等关键状态。删掉 state-a06-revoked 并相应更新成员清单，现有条件仍成立。修复：建立有限、按断言对应的证据索引；校验完整 C19 来源边和 7+20 个输入，A06 七阶段状态及真实 search/412/context/materialization/revoke 请求响应、权限/root/index/dedupe/snapshot 值。逐项删证据及换来源/输入的控制必须拒绝。
- **W09-V3-R03-MODE-WITNESS** — w09_formal_router.v3.proposed.py:269、284、300、307。mode 只绑定 route、标签和 router hash；producer_id 可以缺失，reviewer 只是非空字符串。locked_go_sha256 只检查非空，host/junction refs 只核文件哈希，因此历史或无关文件也能满足这些条件。修复：定义并消费真实 Root/独立复核合同，绑定本次 execution/intent/source closure 与明确身份；验证 host/junction 记录内容和真实 raw witness，并使 locked Go 与实际 invocation、锁定 catalog 一致。FIXTURE 要对应真实 t.TempDir 和 httptest 证据，不能只依赖声明字符串。若 junction 合同需原始命令输出，retrieval_test.proposed.go:464 的成功 CombinedOutput 当前被丢弃，需要在该实际分支导出。缺资源继续 NOT_RUN。

### Suggestions

- w09_formal_router.v3.proposed.py:163：先将 http-request/http-response/file-body 视为不透明字节；合法 JSON 文件体目前会误入 file 事件校验并被要求有 exists 字段。当前冻结文件均为文本，本边界未执行。
- retrieval.proposed.py:37：version_manifest 未含新增 helper 和改过的 domain_test.go。未来源集成时补 pin，或显式依赖包含两文件的 Root 完整 source closure。
- report.json:6：显式 prior_source_basis 路径不存在，需改为真实已封 prior reference，并提供 SHA/bytes。本次没有重试或迁移搜索；未声称完成 v2→v3 全源码比较。

### What's Done Well

导出发生在临时目录清理前，使用独占创建保存原始字节。HTTP 不泄漏 Authorization token，delivery 字段保留 in-process 属性。SQLite 读取真实 grant/index/origin，未知 cache scalar 保持 NULL。三份 Main 差异精确逆向还原原文件，原业务操作及失败断言保留。

### Verification Story

- Tests reviewed: yes。先核测试/helper、冻结行为，再读 runner/router。13 个 MF 成员和 4 个 basis 全字节匹配。
- Main whole inverse: domain_test 1 hunk、retrieval_test 20 hunks、runner 4 hunks，全部精确相等。
- Python AST: runner/router/generator 解析成功；候选从未导入或执行。Go parser/gofmt/compile/test 和 SQL 均未运行，不能宣称 build PASS。
- Security checked: yes。检查 raw/ref/member 所有权、权限状态、模式证据和敏感头边界；具体缺口见三项 Important。
- 一次只读元数据失败：作者显式 prior handoff 路径不存在，aa0295 outer/Python 1/1，原 input/result/trace 独立封存，不重试、不重置计数。其他本轮 metadata reader 成功。作者既有失败不重计。
- 产品/模型/网络/Git/CAS/canonical/source 修改均为 0。固定第三 cut 43→575 保持；新增 origin 留给 Root 后续登记。

完整候选 ref、字段级定位、未执行反例、SQL 依据和范围在 review.json；原工具返回在 raw-tool-observations.json。本结论只适用于源码准备，不能授予实际执行或正式接受。
