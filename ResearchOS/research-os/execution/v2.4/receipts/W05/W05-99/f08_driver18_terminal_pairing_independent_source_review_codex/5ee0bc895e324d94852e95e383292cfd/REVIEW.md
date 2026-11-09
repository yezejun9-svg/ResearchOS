## Review Summary

**Verdict: APPROVE — READY_SOURCE_PREPARATION_ONLY**

R02-T01 的窄范围源码合同已闭合。实际 Root capture/sealer、注册、grant、native 编译和用例仍 OPEN。

### Critical Issues

无。

### Important Issues

无新增静态缺陷。

### Suggestions

Root 后续实际 capture producer 必须用原 transport event 绑定输入/响应，并由独审 command producer 保证实际 shell cmd 对应声明的 launcher argv。Reader 验证 ref 与字段的一致性，不能独立证明外部事件真实性。该具体实现仍属于 A05 OPEN。

### What's Done Well

authority_adapter.v3.proposed.py:388–416 增加 initial exec_command 与 terminal write_stdin 的原始 action/input/response 配对。terminal input 的真实 session 必须等于初始 session，response_ref 必须逐项等于当前完成回执；未知 tool、非空 chars、错误 session 或缺实际 ref 均拒绝。NULL 原生退出码保持不变，不为同步完成补造 session。

### Verification Story

- Tests reviewed：8 个 T01–T08 控制均 NOT_RUN。
- Build verified：否。仅 source IO/Python AST，未 import/execute candidate、helper、Go、SQL 或网络。
- Security checked：完整新增函数 body 与原 input/result/data-flow 静态核对。
- 新包 16 成员、33 原 inputs 与 manifest 共 50 unique refs 重哈希，0 mismatch、0 drift。
- authority 仅 outer_completion 单插入；binding 仅 gate 文件名/SHA 两常量。两源完整正逆字节吻合，其他函数 AST 保持。
- controller v4 的 75d3…/21592 实际 pin 无变化；R01/R03、caps、30 calls、partial17、I16/I18 边界复用已冻结独审。
- 新增失败 0。旧 REQUEST 未改。source acceptance、actual CAS/grant、正式接受增量均为 0；I17/full18/SQL24 继续 OPEN。

